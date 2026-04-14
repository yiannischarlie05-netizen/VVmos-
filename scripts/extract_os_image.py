#!/usr/bin/env python3
"""
VMOS Android 15 OS Image Extractor v1.0
========================================
Extracts the full Android 15 OS image from a VMOS Pro Cloud device
by dumping loop-backed partition images and packaging them for
re-deployment as a clone container.

Architecture discovered via probing:
  mountinfo shows dm-N labels → actually loop devices (major=7):
    loop3840 → / (system)        ~2.3GB ext4 ro
    loop3841 → /system_ext       ~254MB ext4 ro
    loop3842 → /product          ~489MB ext4 ro
    loop3843 → /vendor           ~161MB ext4 ro
    loop3844 → /odm              ~1.8MB ext4 ro
    loop3845 → /data             ~57GB  f2fs rw
    loop3846 → /cache            ~400MB ext4 rw

Extraction method:
  1. Parse /proc/self/mountinfo to discover current loop device mapping
  2. dd | gzip each system partition → /data/local/tmp/
  3. Selective tar of /data (accounts, GMS, apps, shared_prefs)
  4. Upload all to VPS via curl PUT
  5. Generate clone manifest (JSON) with partition map + device identity

Upload requires the upload server (scripts/upload_server.py) running on the VPS:
  python3 scripts/upload_server.py 19000  # start upload receiver on VPS port 19000

Usage:
  python3 scripts/extract_os_image.py --pad APP6476KYH9KMLU5 --vps YOUR_OLLAMA_HOST:19000
  python3 scripts/extract_os_image.py --pad APP6476KYH9KMLU5 --local-only  # dump without upload
  python3 scripts/extract_os_image.py --pad APP6476KYH9KMLU5 --partitions system,vendor
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK = os.environ.get("VMOS_AK", "YOUR_VMOS_AK_HERE")
SK = os.environ.get("VMOS_SK", "YOUR_VMOS_SK_HERE")
BASE_URL = "https://api.vmoscloud.com"

CMD_DELAY = 3.5          # seconds between API calls
POLL_INTERVAL = 10       # seconds between progress polls
STAGING_DIR = "/data/local/tmp/os_extract"
MAX_CHUNK_MB = 200       # split large files into chunks for upload

# Partition mount mapping — default for VMOS Android 15 on RK3588S
DEFAULT_PARTITIONS = {
    "system":     {"mount": "/",            "fs": "ext4", "mode": "ro"},
    "system_ext": {"mount": "/system_ext",  "fs": "ext4", "mode": "ro"},
    "product":    {"mount": "/product",     "fs": "ext4", "mode": "ro"},
    "vendor":     {"mount": "/vendor",      "fs": "ext4", "mode": "ro"},
    "odm":        {"mount": "/odm",         "fs": "ext4", "mode": "ro"},
    "cache":      {"mount": "/cache",       "fs": "ext4", "mode": "rw"},
}

# Critical data paths to include in data tar (selective — not full 57GB)
DATA_PATHS = [
    "/data/system/",
    "/data/system_ce/0/",
    "/data/system_de/0/",
    "/data/misc/",
    "/data/data/com.google.android.gms/",
    "/data/data/com.google.android.gsf/",
    "/data/data/com.android.providers.contacts/",
    "/data/data/com.android.providers.telephony/",
    "/data/data/com.android.providers.settings/",
    "/data/data/com.google.android.apps.walletnfcrel/",
    "/data/data/com.android.chrome/",
    "/data/data/com.android.vending/",
    "/data/local/oicq/",
    "/data/property/",
    "/data/misc_ce/0/",
    "/data/misc_de/0/",
    "/data/user_de/0/",
]


# ═══════════════════════════════════════════════════════════════════════
# API HELPER
# ═══════════════════════════════════════════════════════════════════════

class ExtractorBridge:
    """Cloud API bridge for extraction operations."""

    def __init__(self, pad_code: str):
        self.pad = pad_code
        self.client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
        self._last_cmd = 0.0
        self._cmd_count = 0

    async def _throttle(self):
        elapsed = time.time() - self._last_cmd
        if elapsed < CMD_DELAY:
            await asyncio.sleep(CMD_DELAY - elapsed)

    async def cmd(self, command: str, timeout: int = 30) -> str:
        """Execute shell via sync_cmd, return stdout."""
        await self._throttle()
        self._last_cmd = time.time()
        self._cmd_count += 1
        try:
            r = await asyncio.wait_for(
                self.client.sync_cmd(self.pad, command, timeout_sec=timeout),
                timeout=timeout + 15,
            )
            data = r.get("data", [])
            if isinstance(data, list) and data:
                return (data[0].get("errorMsg", "") or "").strip()
            elif isinstance(data, dict):
                return (data.get("errorMsg", "") or "").strip()
            return ""
        except asyncio.TimeoutError:
            return "ERR:api_timeout"
        except Exception as e:
            return f"ERR:{e}"

    async def fire(self, command: str):
        """Fire async command (non-blocking)."""
        await self._throttle()
        self._last_cmd = time.time()
        self._cmd_count += 1
        try:
            await self.client.async_adb_cmd([self.pad], command)
        except Exception:
            pass

    @property
    def api_calls(self) -> int:
        return self._cmd_count


# ═══════════════════════════════════════════════════════════════════════
# DISCOVERY
# ═══════════════════════════════════════════════════════════════════════

async def discover_partition_map(bridge: ExtractorBridge) -> dict:
    """Parse /proc/self/mountinfo to discover loop device → partition mapping."""
    print("[1/6] Discovering partition map...")

    raw = await bridge.cmd("cat /proc/self/mountinfo | head -60")
    if not raw or "ERR" in raw:
        print(f"  ✗ Failed to read mountinfo: {raw[:100]}")
        return {}

    partitions = {}
    for line in raw.split("\n"):
        parts = line.split()
        if len(parts) < 10:
            continue
        mount_point = parts[4]
        # Find the device after the " - " separator
        try:
            sep_idx = parts.index("-")
            fs_type = parts[sep_idx + 1]
            device = parts[sep_idx + 2]
        except (ValueError, IndexError):
            continue

        # Match dm-N labels (which are actually loop devices) or direct loop mounts
        dm_match = re.match(r"/dev/block/dm-(\d+)", device)
        loop_match = re.match(r"/dev/block/loop(\d+)", device)

        if dm_match:
            dm_num = int(dm_match.group(1))
            dev_major_minor = parts[2]  # e.g., "7:3840"
            major, minor = dev_major_minor.split(":")
            # major 7 = loop devices
            if major == "7":
                loop_dev = f"loop{minor}"
            else:
                loop_dev = f"dm-{dm_num}"
        elif loop_match:
            loop_dev = f"loop{loop_match.group(1)}"
            dev_major_minor = parts[2]
        else:
            continue

        for name, info in DEFAULT_PARTITIONS.items():
            if info["mount"] == mount_point:
                partitions[name] = {
                    "mount": mount_point,
                    "dm_label": f"dm-{dm_num}",
                    "actual_device": f"/dev/block/{loop_dev}",
                    "loop_dev": loop_dev,
                    "major_minor": dev_major_minor,
                    "fs_type": fs_type,
                    "mode": info["mode"],
                }
                break

    # Get sizes from /proc/partitions
    await asyncio.sleep(CMD_DELAY)
    size_raw = await bridge.cmd("cat /proc/partitions | grep loop")
    if size_raw and "ERR" not in size_raw:
        for line in size_raw.split("\n"):
            parts = line.split()
            if len(parts) >= 4:
                dev_name = parts[3]
                size_kb = int(parts[2])
                for name, info in partitions.items():
                    if info["loop_dev"] == dev_name:
                        info["size_kb"] = size_kb
                        info["size_mb"] = round(size_kb / 1024, 1)
                        break

    # Also find data partition
    data_raw = await bridge.cmd("cat /proc/self/mountinfo | grep ' /data '")
    if data_raw and "ERR" not in data_raw:
        for line in data_raw.split("\n"):
            parts = line.split()
            if len(parts) < 10 or parts[4] != "/data":
                continue
            dev_mm = parts[2]
            major, minor = dev_mm.split(":")
            try:
                sep_idx = parts.index("-")
                fs_type = parts[sep_idx + 1]
            except (ValueError, IndexError):
                fs_type = "f2fs"
            loop_dev = f"loop{minor}" if major == "7" else f"dm-{minor}"
            partitions["data"] = {
                "mount": "/data",
                "actual_device": f"/dev/block/{loop_dev}",
                "loop_dev": loop_dev,
                "major_minor": dev_mm,
                "fs_type": fs_type,
                "mode": "rw",
            }
            break

    # Get data size
    if "data" in partitions:
        dsize = await bridge.cmd(f"cat /proc/partitions | grep {partitions['data']['loop_dev']}")
        if dsize and "ERR" not in dsize:
            parts = dsize.split()
            if len(parts) >= 3:
                try:
                    partitions["data"]["size_kb"] = int(parts[2])
                    partitions["data"]["size_mb"] = round(int(parts[2]) / 1024, 1)
                except (ValueError, IndexError):
                    pass

    print(f"  ✓ Discovered {len(partitions)} partitions:")
    for name, info in partitions.items():
        sz = info.get("size_mb", "?")
        print(f"    {name:15s} → {info['actual_device']:30s} {sz}MB ({info['fs_type']}, {info['mode']})")

    return partitions


# ═══════════════════════════════════════════════════════════════════════
# IDENTITY EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

async def extract_identity(bridge: ExtractorBridge) -> dict:
    """Extract device identity properties for the clone manifest."""
    print("\n[2/6] Extracting device identity...")

    compound = (
        "echo MODEL:$(getprop ro.product.model); "
        "echo BRAND:$(getprop ro.product.brand); "
        "echo MANUF:$(getprop ro.product.manufacturer); "
        "echo DEVICE:$(getprop ro.product.device); "
        "echo BOARD:$(getprop ro.product.board); "
        "echo FP:$(getprop ro.build.fingerprint); "
        "echo ANDROID:$(getprop ro.build.version.release); "
        "echo SDK:$(getprop ro.build.version.sdk); "
        "echo SECURITY:$(getprop ro.build.version.security_patch); "
        "echo SERIAL:$(getprop ro.serialno); "
        "echo IMGINFO:$(getprop ro.build.cloud.imginfo); "
        "echo BUILD:$(getprop ro.build.display.id)"
    )
    raw = await bridge.cmd(compound)
    props = {}
    for line in (raw or "").split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            props[key.strip()] = val.strip()

    # Get container version
    version = await bridge.cmd("cat /data/local/oicq/version 2>/dev/null")
    props["CONTAINER_VERSION"] = version.strip() if version else ""

    print(f"  ✓ {props.get('BRAND', '?')} {props.get('MODEL', '?')} | "
          f"Android {props.get('ANDROID', '?')} | "
          f"Image: {props.get('IMGINFO', '?')}")

    return props


# ═══════════════════════════════════════════════════════════════════════
# PARTITION EXTRACTION (dd | gzip)
# ═══════════════════════════════════════════════════════════════════════

async def extract_partition(bridge: ExtractorBridge, name: str, info: dict) -> dict:
    """Extract a single partition image via dd | gzip."""
    device = info["actual_device"]
    size_mb = info.get("size_mb", 0)
    dest = f"{STAGING_DIR}/{name}.img.gz"

    print(f"\n  [{name}] Dumping {device} ({size_mb}MB)...")

    # Ensure staging dir
    await bridge.cmd(f"mkdir -p {STAGING_DIR}")

    # For small partitions (<50MB), sync_cmd with generous timeout
    if size_mb < 50:
        await bridge.cmd(
            f"dd if={device} bs=512K 2>/dev/null | gzip > {dest}",
            timeout=120,
        )
        # Get file size separately for reliable parsing
        size_str = await bridge.cmd(f"stat -c %s {dest} 2>/dev/null || wc -c < {dest} 2>/dev/null")
        try:
            compressed_bytes = int(size_str.strip().split()[0])
        except (ValueError, AttributeError, IndexError):
            compressed_bytes = 0
        if compressed_bytes > 0:
            print(f"  [{name}] ✓ Compressed: {compressed_bytes:,} bytes")
            return {"status": "ok", "file": dest, "compressed_bytes": compressed_bytes}
        else:
            print(f"  [{name}] ✗ dd failed or empty output")
            return {"status": "error", "error": "empty output"}

    # For larger partitions, use async background + polling
    print(f"  [{name}] Starting background dd (may take several minutes)...")

    # Fire background dd
    await bridge.fire(
        f"nohup sh -c 'dd if={device} bs=1M 2>/dev/null | gzip > {dest} && "
        f"echo DONE > {dest}.status' > /dev/null 2>&1 &"
    )

    # Poll for completion
    start_time = time.time()
    timeout_sec = max(300, size_mb * 2)  # ~2 seconds per MB max
    last_size = 0

    while time.time() - start_time < timeout_sec:
        await asyncio.sleep(POLL_INTERVAL)

        # Check status file
        status = await bridge.cmd(f"cat {dest}.status 2>/dev/null")
        if status and "DONE" in status:
            # Get final size
            size_str = await bridge.cmd(f"wc -c < {dest} 2>/dev/null")
            try:
                compressed_bytes = int(size_str.strip())
            except (ValueError, AttributeError):
                compressed_bytes = 0
            elapsed = int(time.time() - start_time)
            print(f"  [{name}] ✓ Complete in {elapsed}s: {compressed_bytes:,} bytes compressed")
            await bridge.cmd(f"rm -f {dest}.status")
            return {"status": "ok", "file": dest, "compressed_bytes": compressed_bytes}

        # Check progress (file size growing)
        size_str = await bridge.cmd(f"wc -c < {dest} 2>/dev/null")
        try:
            current_size = int(size_str.strip())
        except (ValueError, AttributeError):
            current_size = 0

        if current_size > last_size:
            elapsed = int(time.time() - start_time)
            pct = min(99, int((current_size / (size_mb * 1024 * 1024 * 0.4)) * 100))
            print(f"  [{name}] ... {current_size:,} bytes ({pct}%) [{elapsed}s]")
            last_size = current_size
        elif current_size == last_size and current_size > 0:
            # May be done but status file not written
            await asyncio.sleep(5)
            status2 = await bridge.cmd(f"cat {dest}.status 2>/dev/null; ls -la {dest}")
            if "DONE" in status2:
                compressed_bytes = current_size
                print(f"  [{name}] ✓ Complete: {compressed_bytes:,} bytes")
                await bridge.cmd(f"rm -f {dest}.status")
                return {"status": "ok", "file": dest, "compressed_bytes": compressed_bytes}

    # Timeout — check what we got
    size_str = await bridge.cmd(f"wc -c < {dest} 2>/dev/null")
    try:
        final_size = int(size_str.strip())
    except (ValueError, AttributeError):
        final_size = 0

    if final_size > 0:
        print(f"  [{name}] ⚠ Timeout but got {final_size:,} bytes (may be incomplete)")
        return {"status": "partial", "file": dest, "compressed_bytes": final_size}

    print(f"  [{name}] ✗ Timeout with no data")
    return {"status": "error", "error": "timeout"}


# ═══════════════════════════════════════════════════════════════════════
# DATA EXTRACTION (selective tar)
# ═══════════════════════════════════════════════════════════════════════

async def extract_data_selective(bridge: ExtractorBridge) -> dict:
    """Extract critical /data paths via selective tar."""
    print("\n[4/6] Extracting critical /data paths (selective tar)...")

    # Build tar command with existing paths only
    check_cmd = " ".join(
        f"[ -d '{p}' ] && echo EXISTS:{p};"
        for p in DATA_PATHS
    )
    raw = await bridge.cmd(check_cmd)
    existing = [
        line.split(":", 1)[1]
        for line in (raw or "").split("\n")
        if line.startswith("EXISTS:")
    ]

    if not existing:
        print("  ✗ No data paths found")
        return {"status": "error", "error": "no data paths"}

    print(f"  Found {len(existing)} data directories to archive")

    dest = f"{STAGING_DIR}/data_selective.tar.gz"
    paths_str = " ".join(existing)

    # Fire background tar
    await bridge.fire(
        f"nohup sh -c 'tar czf {dest} {paths_str} 2>/dev/null && "
        f"echo DONE > {dest}.status' > /dev/null 2>&1 &"
    )

    # Poll for completion (data tar can be large)
    start_time = time.time()
    timeout_sec = 600  # 10 minutes max
    last_size = 0

    while time.time() - start_time < timeout_sec:
        await asyncio.sleep(POLL_INTERVAL)

        status = await bridge.cmd(f"cat {dest}.status 2>/dev/null")
        if status and "DONE" in status:
            size_str = await bridge.cmd(f"wc -c < {dest} 2>/dev/null")
            try:
                size = int(size_str.strip())
            except (ValueError, AttributeError):
                size = 0
            elapsed = int(time.time() - start_time)
            print(f"  ✓ Data archive complete in {elapsed}s: {size:,} bytes")
            await bridge.cmd(f"rm -f {dest}.status")
            return {"status": "ok", "file": dest, "compressed_bytes": size}

        size_str = await bridge.cmd(f"wc -c < {dest} 2>/dev/null")
        try:
            current = int(size_str.strip())
        except (ValueError, AttributeError):
            current = 0
        if current > last_size:
            elapsed = int(time.time() - start_time)
            print(f"  ... {current:,} bytes [{elapsed}s]")
            last_size = current

    size_str = await bridge.cmd(f"wc -c < {dest} 2>/dev/null")
    try:
        final = int(size_str.strip())
    except (ValueError, AttributeError):
        final = 0
    if final > 0:
        return {"status": "partial", "file": dest, "compressed_bytes": final}
    return {"status": "error", "error": "timeout"}


# ═══════════════════════════════════════════════════════════════════════
# UPLOAD TO VPS
# ═══════════════════════════════════════════════════════════════════════

async def upload_file(bridge: ExtractorBridge, device_path: str,
                      vps_url: str, filename: str) -> bool:
    """Upload file from device to VPS via curl -T (streaming PUT)."""
    print(f"  Uploading {filename}...")

    # Check file size first
    size_str = await bridge.cmd(f"wc -c < {device_path} 2>/dev/null")
    try:
        size = int(size_str.strip())
    except (ValueError, AttributeError):
        print(f"  ✗ File not found: {device_path}")
        return False

    if size == 0:
        print(f"  ✗ File is empty: {device_path}")
        return False

    # Use curl -T for streaming PUT (no memory buffering, works for any size)
    result_file = f"{device_path}.upload_result"
    await bridge.cmd(
        f'nohup sh -c "curl -s -T {device_path} \'{vps_url}/{filename}\' '
        f'> {result_file} 2>&1 && echo UPLOAD_DONE >> {result_file}" '
        f'> /dev/null 2>&1 & echo FIRED'
    )

    # Poll for completion — scale timeout with file size
    max_wait = max(120, size // (2 * 1024 * 1024))  # ~2MB/s minimum
    for attempt in range(max_wait):
        await asyncio.sleep(5)
        result = await bridge.cmd(f"cat {result_file} 2>/dev/null")
        if result and "UPLOAD_DONE" in result:
            print(f"  ✓ Uploaded {filename} ({size:,} bytes)")
            await bridge.cmd(f"rm -f {result_file}")
            return True
        if result and "Error" in result.split("\n")[0] and "UPLOAD_DONE" not in result:
            print(f"  ✗ Upload failed: {result[:200]}")
            break
        if attempt % 12 == 11:  # every ~60s
            print(f"    ... uploading ({attempt * 5}s)")

    await bridge.cmd(f"rm -f {result_file}")
    return False


# ═══════════════════════════════════════════════════════════════════════
# MANIFEST GENERATION
# ═══════════════════════════════════════════════════════════════════════

def generate_manifest(identity: dict, partitions: dict,
                      extraction_results: dict, data_result: dict) -> dict:
    """Generate clone manifest JSON for reconstruction."""
    manifest = {
        "version": "1.0",
        "type": "vmos_android15_clone",
        "created_at": datetime.now().isoformat(),
        "source_device": {
            "pad_code": identity.get("_pad_code", ""),
            "model": identity.get("MODEL", ""),
            "brand": identity.get("BRAND", ""),
            "fingerprint": identity.get("FP", ""),
            "android_version": identity.get("ANDROID", ""),
            "sdk_version": identity.get("SDK", ""),
            "security_patch": identity.get("SECURITY", ""),
            "container_version": identity.get("CONTAINER_VERSION", ""),
            "image_id": identity.get("IMGINFO", ""),
        },
        "partitions": {},
        "data_archive": data_result,
        "reconstruction": {
            "method": "vmos_edge_create_instance",
            "notes": [
                "System partitions are raw ext4 images (gzip compressed)",
                "Data archive is selective tar.gz of critical paths",
                "To reconstruct: gunzip each .img.gz → losetup + mount",
                "Or: create VMOS Edge instance + restore data overlay",
                "Alternative: use local_backup/local_restore API with S3 config",
            ],
            "commands": {
                "decompress": "gunzip {name}.img.gz",
                "mount_readonly": "mount -o ro,loop {name}.img /mnt/{name}",
                "create_edge_instance": (
                    "POST /container_api/v1/create "
                    '{"user_name": "clone", "image_repository": "<image_id>"}'
                ),
                "restore_data": (
                    "tar xzf data_selective.tar.gz -C /data/ "
                    "# After mounting new instance data partition"
                ),
            },
        },
    }

    for name, info in partitions.items():
        if name in extraction_results:
            result = extraction_results[name]
            manifest["partitions"][name] = {
                **info,
                "extraction": result,
            }

    return manifest


# ═══════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════

async def run_extraction(pad_code: str, vps_addr: str | None = None,
                         partition_filter: list[str] | None = None,
                         skip_data: bool = False,
                         local_only: bool = False):
    """Full OS image extraction pipeline."""
    print("=" * 60)
    print("  VMOS Android 15 OS Image Extractor v1.0")
    print(f"  Target: {pad_code}")
    print(f"  VPS: {vps_addr or 'local-only'}")
    print("=" * 60)

    bridge = ExtractorBridge(pad_code)

    # ── Phase 1: Discover partitions ──
    partitions = await discover_partition_map(bridge)
    if not partitions:
        print("✗ Failed to discover partition map. Device may be offline.")
        return

    # ── Phase 2: Extract identity ──
    identity = await extract_identity(bridge)
    identity["_pad_code"] = pad_code

    # ── Phase 3: Extract system partitions ──
    print("\n[3/6] Extracting system partition images...")
    await bridge.cmd(f"mkdir -p {STAGING_DIR}")

    # Filter partitions if specified
    extract_names = partition_filter or [
        n for n in partitions if n != "data"
    ]

    extraction_results = {}
    for name in extract_names:
        if name not in partitions:
            print(f"  ⚠ Partition '{name}' not found, skipping")
            continue
        result = await extract_partition(bridge, name, partitions[name])
        extraction_results[name] = result

    # ── Phase 4: Extract data (selective) ──
    data_result = {"status": "skipped"}
    if not skip_data:
        data_result = await extract_data_selective(bridge)

    # ── Phase 5: Upload to VPS ──
    if vps_addr and not local_only:
        print(f"\n[5/6] Uploading to VPS ({vps_addr})...")
        vps_url = f"http://{vps_addr}"

        for name, result in extraction_results.items():
            if result.get("status") in ("ok", "partial") and result.get("file"):
                await upload_file(bridge, result["file"], vps_url, f"{name}.img.gz")

        if data_result.get("status") in ("ok", "partial") and data_result.get("file"):
            await upload_file(bridge, data_result["file"], vps_url, "data_selective.tar.gz")
    else:
        print(f"\n[5/6] Skipping upload (local-only mode)")
        print(f"  Images staged at: {STAGING_DIR}/")

    # ── Phase 6: Generate manifest ──
    print("\n[6/6] Generating clone manifest...")
    manifest = generate_manifest(identity, partitions, extraction_results, data_result)

    # Save manifest to device
    manifest_json = json.dumps(manifest, indent=2, default=str)
    # Write via echo (split for long content)
    await bridge.cmd(f"echo '{json.dumps(manifest, default=str)}' > {STAGING_DIR}/manifest.json")

    # Upload manifest
    if vps_addr and not local_only:
        await upload_file(bridge, f"{STAGING_DIR}/manifest.json", f"http://{vps_addr}", "manifest.json")

    # ── Summary ──
    print("\n" + "=" * 60)
    print("  EXTRACTION COMPLETE")
    print("=" * 60)
    total_bytes = sum(
        r.get("compressed_bytes", 0)
        for r in extraction_results.values()
        if isinstance(r, dict)
    )
    if isinstance(data_result, dict):
        total_bytes += data_result.get("compressed_bytes", 0)

    print(f"  API calls: {bridge.api_calls}")
    print(f"  Total extracted: {total_bytes:,} bytes ({total_bytes/1024/1024:.1f}MB)")
    print(f"  Partitions: {len(extraction_results)}")
    for name, r in extraction_results.items():
        status = r.get("status", "?")
        size = r.get("compressed_bytes", 0)
        print(f"    {name:15s}: {status:8s} ({size:,} bytes)")
    if isinstance(data_result, dict) and data_result.get("status") != "skipped":
        print(f"    {'data':15s}: {data_result.get('status', '?'):8s} "
              f"({data_result.get('compressed_bytes', 0):,} bytes)")

    print(f"\n  Manifest: {STAGING_DIR}/manifest.json")
    print(f"  Staged files: {STAGING_DIR}/")

    # Print manifest excerpt
    print("\n  Clone manifest (key info):")
    print(f"    Model: {manifest['source_device']['model']}")
    print(f"    Android: {manifest['source_device']['android_version']}")
    print(f"    Image: {manifest['source_device']['image_id']}")
    print(f"    Container: {manifest['source_device']['container_version']}")

    return manifest


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Extract Android 15 OS image from VMOS Pro Cloud device"
    )
    parser.add_argument("--pad", required=True, help="Device PAD code")
    parser.add_argument("--vps", default=None, help="VPS address:port for upload")
    parser.add_argument("--local-only", action="store_true",
                        help="Stage on device only, don't upload")
    parser.add_argument("--partitions", default=None,
                        help="Comma-separated list of partitions to extract")
    parser.add_argument("--skip-data", action="store_true",
                        help="Skip /data selective extraction")
    args = parser.parse_args()

    partition_filter = None
    if args.partitions:
        partition_filter = [p.strip() for p in args.partitions.split(",")]

    asyncio.run(run_extraction(
        pad_code=args.pad,
        vps_addr=args.vps,
        partition_filter=partition_filter,
        skip_data=args.skip_data,
        local_only=args.local_only,
    ))


if __name__ == "__main__":
    main()
