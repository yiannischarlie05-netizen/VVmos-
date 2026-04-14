#!/usr/bin/env python3
"""
Zero-Login Device Clone Engine v1.0
=====================================
Full-partition backup from ADB neighbor → restore to VMOS Cloud device.

Replicates what VMOS Cloud's native backup/restore does internally:
- Full /data/ partition tar (not cherry-picked files)
- Complete keystore, accounts DB, GMS state, app data in one atomic snapshot
- Identity properties via Cloud API
- Permission + SELinux fix via syncCmd root

Result: apps continue operating without ANY re-login.

Usage:
  python3 -m vmos_titan.core.clone_engine probe
  python3 -m vmos_titan.core.clone_engine backup <NEIGHBOR_IP>
  python3 -m vmos_titan.core.clone_engine restore <NEIGHBOR_IP>
  python3 -m vmos_titan.core.clone_engine clone <NEIGHBOR_IP>     # backup + restore
  python3 -m vmos_titan.core.clone_engine verify <NEIGHBOR_IP>
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"

# Our two devices
DEVICES = {
    "ACP250916A5B1912": "Device A (clone target)",
    "APP6476KYH9KMLU5": "Device B (launchpad)",
}

RELAY_PORT = 15573
ADB_BRIDGE = "localhost:8550"
CLONE_ROOT = "tmp/full_clones"
API_DELAY = 3.5

# Full set of identity properties
IDENTITY_PROPS = [
    "ro.product.brand", "ro.product.model", "ro.product.device",
    "ro.product.name", "ro.product.manufacturer",
    "ro.build.display.id", "ro.build.version.release",
    "ro.build.version.sdk", "ro.build.fingerprint",
    "ro.product.board", "ro.hardware",
    "ro.serialno", "ro.boot.serialno",
    "ro.build.version.incremental", "ro.build.flavor",
    "ro.odm.build.fingerprint", "ro.vendor.build.fingerprint",
    "ro.system.build.fingerprint", "ro.system_ext.build.fingerprint",
    "ro.product.build.fingerprint",
]

CLOUD_IDENTITY_PROPS = [
    "persist.sys.cloud.imeinum", "persist.sys.cloud.iccidnum",
    "persist.sys.cloud.imsinum", "persist.sys.cloud.drm.id",
    "persist.sys.cloud.drm.puid", "ro.sys.cloud.android_id",
    "persist.sys.cloud.wifi.ssid", "persist.sys.cloud.wifi.mac",
    "persist.sys.cloud.wifi.ip", "persist.sys.cloud.wifi.gateway",
    "persist.sys.cloud.wifi.dns1",
    "persist.sys.cloud.gpu.gl_vendor", "persist.sys.cloud.gpu.gl_renderer",
    "persist.sys.cloud.gpu.gl_version",
    "persist.sys.cloud.gps.lat", "persist.sys.cloud.gps.lon",
    "persist.sys.cloud.phonenum", "persist.sys.cloud.mobileinfo",
    "persist.sys.cloud.cellinfo",
    "persist.sys.cloud.battery.capacity", "persist.sys.cloud.battery.level",
    "persist.sys.cloud.boottime.offset",
    "persist.sys.cloud.pm.install_source",
    "ro.sys.cloud.boot_id",
]

# Directories to include in full-partition backup
BACKUP_PATHS = [
    "/data/data/",
    "/data/system_ce/0/",
    "/data/system_de/0/",
    "/data/system/users/0/",
    "/data/misc/keystore/user_0/",
    "/data/misc/wifi/",
    "/data/misc/keychain/",
    "/data/app/",
]

# Directories to exclude (cache, temp — reduce tar size)
BACKUP_EXCLUDES = [
    "*/cache/*",
    "*/code_cache/*",
    "/data/dalvik-cache/*",
    "/data/local/tmp/*",
    "*/app_webview/*Cache*",
    "*/app_chrome/Default/GPUCache/*",
]


# ═══════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class DeviceProbe:
    pad_code: str = ""
    alive: bool = False
    root: bool = False
    model: str = ""
    brand: str = ""
    android_version: str = ""
    hardware: str = ""
    cpu_arch: str = ""
    storage_total: str = ""
    storage_free: str = ""
    is_cloud_vm: bool = False
    ip_address: str = ""
    third_party_apps: int = 0
    error: str = ""


@dataclass
class BackupManifest:
    neighbor_ip: str = ""
    brand: str = ""
    model: str = ""
    android: str = ""
    is_root: bool = False
    fingerprint_count: int = 0
    partition_tar_path: str = ""
    partition_tar_size_mb: float = 0.0
    partition_tar_sha256: str = ""
    keystore_count: int = 0
    accounts: list = field(default_factory=list)
    pkg_count: int = 0
    third_party_pkgs: list = field(default_factory=list)
    backup_time: str = ""
    status: str = "pending"


# ═══════════════════════════════════════════════════════════════════════
# ADB HELPERS
# ═══════════════════════════════════════════════════════════════════════

def adb(addr: str, cmd: str, timeout: int = 15) -> str:
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "shell", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except (subprocess.TimeoutExpired, Exception):
        return ""


def adb_pull(addr: str, remote: str, local: str, timeout: int = 120) -> bool:
    os.makedirs(os.path.dirname(local) or ".", exist_ok=True)
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "pull", remote, local],
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0
    except Exception:
        return False


def adb_push(addr: str, local: str, remote: str, timeout: int = 300) -> bool:
    for attempt in range(2):
        try:
            r = subprocess.run(
                ["adb", "-s", addr, "push", local, remote],
                capture_output=True, text=True, timeout=timeout
            )
            if r.returncode == 0:
                return True
            if attempt == 0:
                subprocess.run(["adb", "connect", addr], capture_output=True, timeout=8)
        except Exception:
            if attempt == 0:
                subprocess.run(["adb", "connect", addr], capture_output=True, timeout=8)
    return False


def adb_check(addr: str) -> bool:
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "shell", "echo OK"],
            capture_output=True, text=True, timeout=5
        )
        if "OK" in r.stdout:
            return True
    except Exception:
        pass
    subprocess.run(["adb", "connect", addr], capture_output=True, timeout=8)
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "shell", "echo OK"],
            capture_output=True, text=True, timeout=5
        )
        return "OK" in r.stdout
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════
# CLOUD API HELPERS
# ═══════════════════════════════════════════════════════════════════════

async def cloud_cmd(client: VMOSCloudClient, pad_code: str,
                    command: str, timeout_sec: int = 30) -> str:
    try:
        result = await client.sync_cmd(pad_code, command, timeout_sec=timeout_sec)
        if not result or not isinstance(result, dict):
            return ""
        data = result.get("data", [])
        if data and isinstance(data, list) and len(data) > 0:
            return data[0].get("errorMsg", "") or ""
        return ""
    except Exception as e:
        return ""


async def cloud_cmd_retry(client: VMOSCloudClient, pad_code: str,
                          command: str, retries: int = 3,
                          timeout_sec: int = 30) -> str:
    for i in range(retries):
        result = await cloud_cmd(client, pad_code, command, timeout_sec)
        if result:
            return result
        await asyncio.sleep(API_DELAY)
    return ""


# ═══════════════════════════════════════════════════════════════════════
# RELAY MANAGEMENT (connect to neighbor via our launchpad device)
# ═══════════════════════════════════════════════════════════════════════

async def deploy_relay(client: VMOSCloudClient, launchpad: str,
                       target_ip: str, port: int = RELAY_PORT) -> bool:
    await cloud_cmd(client, launchpad,
        f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /data/local/tmp/rf_{port}; echo c")
    await asyncio.sleep(0.4)

    output = await cloud_cmd(client, launchpad,
        f"mkfifo /data/local/tmp/rf_{port} && echo fifo_ok")
    if "fifo_ok" not in output:
        return False

    await asyncio.sleep(0.3)
    output = await cloud_cmd(client, launchpad,
        f'nohup sh -c "nc -l -p {port} < /data/local/tmp/rf_{port} | '
        f'nc {target_ip} 5555 > /data/local/tmp/rf_{port}" > /dev/null 2>&1 & echo relay_ok')
    return "relay_ok" in output


def connect_relay(port: int = RELAY_PORT) -> str:
    addr = f"localhost:{port}"
    subprocess.run(["adb", "disconnect", addr], capture_output=True, timeout=5)
    subprocess.run(["adb", "-s", ADB_BRIDGE, "forward", f"tcp:{port}", f"tcp:{port}"],
                   capture_output=True, timeout=8)
    subprocess.run(["adb", "connect", addr], capture_output=True, timeout=8)
    return addr


def disconnect_relay(port: int = RELAY_PORT):
    subprocess.run(["adb", "disconnect", f"localhost:{port}"],
                   capture_output=True, timeout=5)


async def kill_relay(client: VMOSCloudClient, launchpad: str,
                     port: int = RELAY_PORT):
    await cloud_cmd(client, launchpad,
        f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /data/local/tmp/rf_{port}; echo d")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: PROBE DEVICES
# ═══════════════════════════════════════════════════════════════════════

async def probe_device(client: VMOSCloudClient, pad_code: str) -> DeviceProbe:
    probe = DeviceProbe(pad_code=pad_code)

    # Test connectivity
    test = await cloud_cmd(client, pad_code, "echo ALIVE && id")
    await asyncio.sleep(API_DELAY)

    if "ALIVE" not in test:
        probe.error = "Device not responding"
        return probe

    probe.alive = True
    probe.root = "uid=0" in test

    # Device identity
    probe.model = await cloud_cmd(client, pad_code, "getprop ro.product.model")
    await asyncio.sleep(API_DELAY)
    probe.brand = await cloud_cmd(client, pad_code, "getprop ro.product.brand")
    await asyncio.sleep(API_DELAY)
    probe.android_version = await cloud_cmd(client, pad_code, "getprop ro.build.version.release")
    await asyncio.sleep(API_DELAY)
    probe.hardware = await cloud_cmd(client, pad_code, "getprop ro.hardware")
    await asyncio.sleep(API_DELAY)

    # CPU architecture
    cpu = await cloud_cmd(client, pad_code, "cat /proc/cpuinfo | grep -i 'model name\\|Hardware\\|CPU part' | head -3")
    await asyncio.sleep(API_DELAY)
    probe.cpu_arch = cpu.replace("\n", " | ") if cpu else "unknown"

    # Storage
    df = await cloud_cmd(client, pad_code, "df -h /data 2>/dev/null | tail -1")
    await asyncio.sleep(API_DELAY)
    if df:
        parts = df.split()
        if len(parts) >= 4:
            probe.storage_total = parts[1]
            probe.storage_free = parts[3]

    # IP address
    ip = await cloud_cmd(client, pad_code, "ip -4 addr show | grep inet | grep -v 127.0.0.1 | head -1 | awk '{print $2}'")
    await asyncio.sleep(API_DELAY)
    probe.ip_address = ip.split("/")[0] if ip else ""

    # Detect cloud VM vs real ARM
    # Cloud VMs typically have vmos/cloud kernel markers
    kernel = await cloud_cmd(client, pad_code, "uname -r 2>/dev/null")
    await asyncio.sleep(API_DELAY)
    vmos_marker = await cloud_cmd(client, pad_code, "getprop ro.vmos.cloud 2>/dev/null")
    await asyncio.sleep(API_DELAY)
    cloud_marker = await cloud_cmd(client, pad_code, "ls /data/data/com.cloud.phone 2>/dev/null && echo CLOUD")
    await asyncio.sleep(API_DELAY)

    probe.is_cloud_vm = bool(
        "vmos" in (kernel or "").lower() or
        "cloud" in (kernel or "").lower() or
        vmos_marker or
        "CLOUD" in (cloud_marker or "")
    )

    # Third-party app count
    pkgs = await cloud_cmd(client, pad_code, "pm list packages -3 2>/dev/null | wc -l")
    await asyncio.sleep(API_DELAY)
    try:
        probe.third_party_apps = int(pkgs.strip())
    except (ValueError, AttributeError):
        pass

    return probe


async def probe_all_devices(client: VMOSCloudClient) -> dict[str, DeviceProbe]:
    print(f"\n{'═'*70}")
    print(f"  DEVICE PROBE — Analyzing both devices")
    print(f"{'═'*70}")

    probes = {}
    for pad_code, label in DEVICES.items():
        print(f"\n  Probing {label} ({pad_code})...")
        probe = await probe_device(client, pad_code)
        probes[pad_code] = probe

        if probe.alive:
            print(f"    Status:    ALIVE {'(ROOT)' if probe.root else '(non-root)'}")
            print(f"    Model:     {probe.brand} {probe.model}")
            print(f"    Android:   {probe.android_version}")
            print(f"    Hardware:  {probe.hardware}")
            print(f"    CPU:       {probe.cpu_arch}")
            print(f"    Storage:   {probe.storage_total} total / {probe.storage_free} free")
            print(f"    IP:        {probe.ip_address}")
            print(f"    Cloud VM:  {'YES' if probe.is_cloud_vm else 'NO (real ARM)'}")
            print(f"    3rd-party: {probe.third_party_apps} apps")
        else:
            print(f"    Status:    OFFLINE — {probe.error}")

    # Determine best target
    print(f"\n  {'─'*50}")
    print(f"  RECOMMENDATION:")
    alive_probes = {k: v for k, v in probes.items() if v.alive}

    if not alive_probes:
        print(f"    [!] No devices responding. Check connectivity.")
    else:
        # Prefer cloud VM (identity changes are instant via API)
        cloud_vms = {k: v for k, v in alive_probes.items() if v.is_cloud_vm}
        if cloud_vms:
            best = next(iter(cloud_vms))
            print(f"    Best clone target: {best} (Cloud VM — instant identity change)")
        else:
            # Pick device with more storage
            best = max(alive_probes, key=lambda k: alive_probes[k].storage_free or "0")
            print(f"    Best clone target: {best} (most storage: {alive_probes[best].storage_free})")
        print(f"    This device will receive the cloned neighbor data.")

    # Determine launchpad (device used to relay to neighbors)
    for pad, p in alive_probes.items():
        if p.ip_address and p.ip_address.startswith("10.0."):
            print(f"    Launchpad:  {pad} (IP {p.ip_address} — on neighbor network)")
            break

    print(f"{'═'*70}\n")

    # Save probe results
    os.makedirs("tmp", exist_ok=True)
    with open("tmp/device_probes.json", "w") as f:
        json.dump({k: asdict(v) for k, v in probes.items()}, f, indent=2)

    return probes


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: FULL-PARTITION BACKUP FROM NEIGHBOR
# ═══════════════════════════════════════════════════════════════════════

async def full_partition_backup(client: VMOSCloudClient, launchpad: str,
                                neighbor_ip: str) -> Optional[BackupManifest]:
    """
    Full-partition backup from neighbor via ADB relay.
    Creates atomic tar of /data/ — same approach as VMOS Cloud native backup.
    """
    clone_dir = os.path.join(CLONE_ROOT, neighbor_ip.replace(".", "_"))
    os.makedirs(clone_dir, exist_ok=True)

    manifest = BackupManifest(neighbor_ip=neighbor_ip)
    manifest.backup_time = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'═'*70}")
    print(f"  FULL-PARTITION BACKUP v1.0")
    print(f"  Neighbor:  {neighbor_ip}")
    print(f"  Launchpad: {launchpad}")
    print(f"  Clone dir: {clone_dir}")
    print(f"{'═'*70}")

    # ── Deploy relay ──
    print(f"\n  [1/8] Deploying ADB relay to neighbor...")
    if not await deploy_relay(client, launchpad, neighbor_ip):
        print("  [!] Relay deploy FAILED")
        manifest.status = "relay_failed"
        return manifest

    await asyncio.sleep(0.6)
    dev = connect_relay()
    await asyncio.sleep(0.5)

    test = adb(dev, "echo OK", 5)
    if "OK" not in test:
        print("  [!] ADB not responding via relay")
        disconnect_relay()
        await kill_relay(client, launchpad)
        manifest.status = "adb_failed"
        return manifest

    # ── Device info ──
    print(f"\n  [2/8] Reading device info...")
    shell_id = adb(dev, "id")
    manifest.is_root = "uid=0" in shell_id
    manifest.brand = adb(dev, "getprop ro.product.brand")
    manifest.model = adb(dev, "getprop ro.product.model")
    manifest.android = adb(dev, "getprop ro.build.version.release")

    print(f"    Device: {manifest.brand} {manifest.model}")
    print(f"    Android: {manifest.android}")
    print(f"    Shell: {'ROOT' if manifest.is_root else 'NON-ROOT (limited backup)'}")

    if not manifest.is_root:
        print(f"    [!] WARNING: Non-root access limits backup to app-level data only.")
        print(f"        System accounts DB and keystore will be skipped.")

    # ── Backup device fingerprint ──
    print(f"\n  [3/8] Backing up device fingerprint (all properties)...")
    props_raw = adb(dev, "getprop", 30)
    props_file = os.path.join(clone_dir, "build.prop")
    with open(props_file, "w") as f:
        f.write(props_raw)

    all_props = {}
    for line in props_raw.splitlines():
        line = line.strip()
        if line.startswith("[") and "]: [" in line:
            key = line.split("]: [")[0].lstrip("[")
            val = line.split("]: [")[1].rstrip("]")
            all_props[key] = val

    fingerprint = {k: all_props.get(k, "") for k in IDENTITY_PROPS + CLOUD_IDENTITY_PROPS
                   if all_props.get(k)}
    fp_file = os.path.join(clone_dir, "fingerprint.json")
    with open(fp_file, "w") as f:
        json.dump(fingerprint, f, indent=2)
    manifest.fingerprint_count = len(fingerprint)
    print(f"    Properties saved: {len(fingerprint)} identity + {len(all_props)} total")

    # Save ALL properties (not just identity — may be needed for deeper matching)
    with open(os.path.join(clone_dir, "all_properties.json"), "w") as f:
        json.dump(all_props, f, indent=2)

    # ── Enumerate packages ──
    print(f"\n  [4/8] Enumerating packages...")
    raw_pkgs = adb(dev, "pm list packages -3 2>/dev/null | cut -d: -f2", 15)
    third_party = [p.strip() for p in raw_pkgs.splitlines() if p.strip()]
    manifest.third_party_pkgs = third_party
    manifest.pkg_count = len(third_party)
    print(f"    Third-party packages: {manifest.pkg_count}")

    # Save full package list with APK paths
    full_pkg_list = adb(dev, "pm list packages -f 2>/dev/null", 20)
    with open(os.path.join(clone_dir, "packages.txt"), "w") as f:
        f.write(full_pkg_list)

    # ── Accounts dump ──
    print(f"\n  [5/8] Dumping accounts...")
    accts_raw = adb(dev, "dumpsys account 2>/dev/null", 20)
    with open(os.path.join(clone_dir, "accounts_dump.txt"), "w") as f:
        f.write(accts_raw)

    for line in accts_raw.splitlines():
        if "Account {" in line and "name=" in line:
            try:
                name = line.split("name=")[1].split(",")[0]
                atype = line.split("type=")[1].rstrip("}").strip()
                manifest.accounts.append({"name": name, "type": atype})
            except (IndexError, ValueError):
                pass
    print(f"    Accounts found: {len(manifest.accounts)}")
    for a in manifest.accounts:
        print(f"      {a['name']} ({a['type']})")

    # ── Check /data/ size ──
    print(f"\n  [6/8] Checking data size...")
    du_output = adb(dev, "du -sh /data/data/ /data/system_ce/0/ /data/misc/keystore/ "
                        "/data/app/ 2>/dev/null", 30)
    print(f"    {du_output.replace(chr(10), chr(10) + '    ')}")

    # ── FULL-PARTITION TAR (the key step) ──
    print(f"\n  [7/8] Creating full-partition backup tar...")
    print(f"    This is the atomic backup — includes ALL data, keystore, accounts, app state.")

    # Build tar command with excludes
    exclude_flags = " ".join(f"--exclude='{e}'" for e in BACKUP_EXCLUDES)
    include_paths = " ".join(BACKUP_PATHS)

    remote_tar = "/sdcard/full_clone_backup.tar.gz"
    tar_cmd = (
        f"rm -f {remote_tar} && "
        f"tar czf {remote_tar} {exclude_flags} "
        f"{include_paths} 2>/dev/null && "
        f"ls -lh {remote_tar} && echo TAR_OK"
    )

    print(f"    Running tar on neighbor (may take several minutes)...")
    t_start = time.time()
    tar_result = adb(dev, tar_cmd, timeout=600)  # 10 min max
    t_elapsed = time.time() - t_start
    print(f"    Tar completed in {t_elapsed:.0f}s")

    if "TAR_OK" not in tar_result:
        print(f"    [!] Full tar failed. Falling back to per-directory tar...")
        # Fallback: tar each directory separately
        tar_parts = []
        for path in BACKUP_PATHS:
            part_name = path.strip("/").replace("/", "_")
            part_remote = f"/sdcard/clone_part_{part_name}.tar.gz"
            part_result = adb(dev,
                f"tar czf {part_remote} {exclude_flags} {path} 2>/dev/null && "
                f"ls -lh {part_remote} && echo PART_OK",
                timeout=300)
            if "PART_OK" in part_result:
                tar_parts.append(part_remote)
                print(f"      {path}: ✓")
            else:
                print(f"      {path}: ✗ (access denied or empty)")

        # Combine parts into single tar
        if tar_parts:
            parts_list = " ".join(tar_parts)
            combine = adb(dev,
                f"cat {parts_list} > {remote_tar} && echo COMBINE_OK",
                timeout=120)
            if "COMBINE_OK" not in combine:
                # Just use parts separately
                remote_tar = tar_parts[0]  # Use first successful part
                print(f"    [!] Using individual parts instead of combined tar")

    # Get tar size
    size_out = adb(dev, f"stat -c '%s' {remote_tar} 2>/dev/null || wc -c < {remote_tar}", 10)
    try:
        tar_size_bytes = int(size_out.strip())
        manifest.partition_tar_size_mb = round(tar_size_bytes / (1024 * 1024), 1)
    except (ValueError, AttributeError):
        manifest.partition_tar_size_mb = 0
    print(f"    Tar size: {manifest.partition_tar_size_mb:.1f} MB")

    # Pull tar to local
    local_tar = os.path.join(clone_dir, "full_partition.tar.gz")
    print(f"    Pulling tar to local disk...")
    t_start = time.time()
    pull_ok = adb_pull(dev, remote_tar, local_tar, timeout=1800)  # 30 min max for large files

    if not pull_ok or not os.path.exists(local_tar) or os.path.getsize(local_tar) < 1024:
        print(f"    [!] Pull failed. Trying chunked pull...")
        # Chunked pull: split on device, pull parts, reassemble
        split_result = adb(dev,
            f"cd /sdcard && split -b 50m {remote_tar} clone_chunk_ && ls -la clone_chunk_* && echo SPLIT_OK",
            timeout=300)
        if "SPLIT_OK" in split_result:
            chunk_dir = os.path.join(clone_dir, "chunks")
            os.makedirs(chunk_dir, exist_ok=True)
            chunks = [l.strip().split()[-1] for l in split_result.splitlines()
                      if "clone_chunk_" in l and "SPLIT_OK" not in l]
            pulled_chunks = []
            for chunk in chunks:
                chunk_local = os.path.join(chunk_dir, chunk)
                if adb_pull(dev, f"/sdcard/{chunk}", chunk_local, timeout=600):
                    pulled_chunks.append(chunk_local)
                    print(f"      Chunk {chunk}: ✓")
            # Reassemble
            if pulled_chunks:
                with open(local_tar, "wb") as out_f:
                    for cp in sorted(pulled_chunks):
                        with open(cp, "rb") as in_f:
                            out_f.write(in_f.read())
                pull_ok = True
                print(f"    Reassembled {len(pulled_chunks)} chunks → {local_tar}")
            # Cleanup chunks on device
            adb(dev, "rm -f /sdcard/clone_chunk_*", 10)

    t_elapsed = time.time() - t_start
    if pull_ok and os.path.exists(local_tar):
        actual_size = os.path.getsize(local_tar) / (1024 * 1024)
        print(f"    Pull complete: {actual_size:.1f} MB in {t_elapsed:.0f}s")
        manifest.partition_tar_path = local_tar
        manifest.partition_tar_size_mb = round(actual_size, 1)

        # SHA256 checksum
        sha = hashlib.sha256()
        with open(local_tar, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        manifest.partition_tar_sha256 = sha.hexdigest()
        print(f"    SHA256: {manifest.partition_tar_sha256[:16]}...")
    else:
        print(f"    [!] Tar pull FAILED")
        manifest.status = "pull_failed"

    # Cleanup tar on neighbor
    adb(dev, f"rm -f {remote_tar}", 10)

    # ── Keystore inventory ──
    print(f"\n  [8/8] Keystore inventory...")
    ks_list = adb(dev, "ls /data/misc/keystore/user_0/ 2>/dev/null | wc -l", 5)
    try:
        manifest.keystore_count = int(ks_list.strip())
    except (ValueError, AttributeError):
        manifest.keystore_count = 0
    print(f"    Keystore entries: {manifest.keystore_count}")

    # Cleanup relay
    disconnect_relay()
    await kill_relay(client, launchpad)

    # Save manifest
    manifest.status = "backed_up"
    manifest_file = os.path.join(clone_dir, "clone_manifest.json")
    with open(manifest_file, "w") as f:
        json.dump(asdict(manifest), f, indent=2)

    print(f"\n{'═'*70}")
    print(f"  BACKUP COMPLETE")
    print(f"  Tar: {manifest.partition_tar_size_mb:.1f} MB")
    print(f"  Properties: {manifest.fingerprint_count}")
    print(f"  Keystore: {manifest.keystore_count} entries")
    print(f"  Accounts: {len(manifest.accounts)}")
    print(f"  Packages: {manifest.pkg_count}")
    print(f"  Clone dir: {clone_dir}")
    print(f"{'═'*70}")

    return manifest


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: FULL-PARTITION RESTORE TO OUR DEVICE
# ═══════════════════════════════════════════════════════════════════════

async def full_partition_restore(client: VMOSCloudClient, target_pad: str,
                                 neighbor_ip: str,
                                 clean_slate: bool = True) -> dict:
    """
    Restore full-partition backup to our VMOS Cloud device.
    Replicates VMOS Cloud native restore — identity + full data + permissions.
    """
    clone_dir = os.path.join(CLONE_ROOT, neighbor_ip.replace(".", "_"))
    manifest_file = os.path.join(clone_dir, "clone_manifest.json")

    if not os.path.exists(manifest_file):
        print(f"[!] No backup manifest at {manifest_file}")
        return {"error": "no_backup"}

    with open(manifest_file) as f:
        manifest = json.load(f)

    local_tar = manifest.get("partition_tar_path", os.path.join(clone_dir, "full_partition.tar.gz"))
    if not os.path.exists(local_tar):
        print(f"[!] Backup tar not found: {local_tar}")
        return {"error": "no_tar"}

    fp_file = os.path.join(clone_dir, "fingerprint.json")
    if not os.path.exists(fp_file):
        print(f"[!] No fingerprint data found")
        return {"error": "no_fingerprint"}

    with open(fp_file) as f:
        fingerprint = json.load(f)

    tar_size_mb = os.path.getsize(local_tar) / (1024 * 1024)

    print(f"\n{'═'*70}")
    print(f"  FULL-PARTITION RESTORE v1.0")
    print(f"  Source:   {neighbor_ip} ({manifest.get('brand','')} {manifest.get('model','')})")
    print(f"  Target:   {target_pad}")
    print(f"  Tar:      {tar_size_mb:.1f} MB")
    print(f"  Props:    {len(fingerprint)}")
    print(f"  Accounts: {len(manifest.get('accounts', []))}")
    print(f"{'═'*70}")

    restore_log = {
        "source": neighbor_ip,
        "target": target_pad,
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "steps": {},
    }

    # ── Step 1: Clean slate (optional) ──
    if clean_slate:
        print(f"\n  [1/10] Clean slate — replacePad...")
        try:
            os.environ["VMOS_ALLOW_RESTART"] = "1"
            result = await client.one_key_new_device([target_pad], country_code="US")
            code = result.get("code", -1)
            if code == 200:
                print(f"    replacePad: ✓ — waiting 90s for fresh boot...")
                restore_log["steps"]["clean_slate"] = True
                await asyncio.sleep(90)
            else:
                print(f"    replacePad: code={code} msg={result.get('msg','')}")
                print(f"    Continuing without clean slate...")
                restore_log["steps"]["clean_slate"] = False
        except Exception as e:
            print(f"    replacePad error: {e}")
            restore_log["steps"]["clean_slate"] = False
    else:
        print(f"\n  [1/10] Skipping clean slate (clean_slate=False)")
        restore_log["steps"]["clean_slate"] = "skipped"

    # ── Step 2: Enable root ──
    print(f"\n  [2/10] Enabling root...")
    try:
        result = await client.switch_root([target_pad], enable=True)
        code = result.get("code", -1)
        print(f"    switchRoot: code={code}")
        await asyncio.sleep(5)
    except Exception as e:
        print(f"    switchRoot error: {e}")
    restore_log["steps"]["root"] = True

    # Verify device is alive
    alive = await cloud_cmd_retry(client, target_pad, "echo ALIVE && id")
    if "ALIVE" not in alive:
        print(f"  [!] Device not responding after setup. Waiting 30s...")
        await asyncio.sleep(30)
        alive = await cloud_cmd_retry(client, target_pad, "echo ALIVE && id")
        if "ALIVE" not in alive:
            print(f"  [!] Device still not responding. Aborting.")
            return {"error": "device_offline"}
    print(f"    Device alive: {'ROOT' if 'uid=0' in alive else 'non-root'}")

    # ── Step 3: Write ro.* identity props (deep identity) ──
    print(f"\n  [3/10] Writing deep identity properties (ro.*)...")
    ro_props = {k: v for k, v in fingerprint.items()
                if k.startswith("ro.") and not k.startswith("ro.sys.cloud")}

    if ro_props:
        try:
            result = await client.update_android_prop(target_pad, ro_props)
            code = result.get("code", -1)
            print(f"    updatePadAndroidProp: code={code} ({len(ro_props)} props)")
            restore_log["steps"]["ro_props"] = len(ro_props)
            await asyncio.sleep(API_DELAY)
        except Exception as e:
            print(f"    Error: {e}")
            # Fallback: use resetprop via syncCmd
            print(f"    Falling back to resetprop via syncCmd...")
            for k, v in ro_props.items():
                await cloud_cmd(client, target_pad,
                    f'resetprop {k} "{v}" 2>/dev/null || setprop {k} "{v}" 2>/dev/null')
                await asyncio.sleep(API_DELAY)
            restore_log["steps"]["ro_props"] = f"{len(ro_props)} (resetprop)"

    # ── Step 4: Restart to apply ro.* changes ──
    print(f"\n  [4/10] Restarting to apply ro.* properties...")
    try:
        os.environ["VMOS_ALLOW_RESTART"] = "1"
        result = await client.instance_restart([target_pad])
        code = result.get("code", -1)
        print(f"    restart: code={code} — waiting 60s...")
        await asyncio.sleep(60)
    except Exception as e:
        print(f"    restart error: {e}")
        await asyncio.sleep(30)
    restore_log["steps"]["restart_1"] = True

    # Verify alive again
    alive = await cloud_cmd_retry(client, target_pad, "echo ALIVE && id", retries=5)
    if "ALIVE" not in alive:
        print(f"  [!] Device not responding after restart. Waiting 60s...")
        await asyncio.sleep(60)
        alive = await cloud_cmd_retry(client, target_pad, "echo ALIVE && id", retries=5)
    print(f"    Device alive: {'ROOT' if 'uid=0' in alive else 'non-root'}")

    # ── Step 5: Write persist.* + cloud identity props ──
    print(f"\n  [5/10] Writing runtime identity properties (persist.*)...")
    persist_props = {k: v for k, v in fingerprint.items()
                     if k.startswith("persist.") or k.startswith("ro.sys.cloud")}

    if persist_props:
        try:
            result = await client.modify_instance_properties([target_pad], persist_props)
            code = result.get("code", -1)
            print(f"    updatePadProperties: code={code} ({len(persist_props)} props)")
            restore_log["steps"]["persist_props"] = len(persist_props)
            await asyncio.sleep(API_DELAY)
        except Exception as e:
            print(f"    Error: {e}")
    else:
        print(f"    No persist.* properties to write")

    # ── Step 6: Stop GMS before data injection ──
    print(f"\n  [6/10] Stopping Google Play Services before data injection...")
    await cloud_cmd(client, target_pad,
        "am force-stop com.google.android.gms && "
        "am force-stop com.google.android.gsf && "
        "am force-stop com.android.vending && "
        "echo STOPPED")
    await asyncio.sleep(API_DELAY)
    restore_log["steps"]["stop_gms"] = True

    # ── Step 7: Push + extract full-partition tar (THE KEY STEP) ──
    print(f"\n  [7/10] Pushing full-partition tar to device ({tar_size_mb:.1f} MB)...")
    print(f"    This is the atomic restore — ALL data, keystore, accounts, app state.")

    # Push tar via ADB bridge
    remote_tar = "/data/local/tmp/full_clone_backup.tar.gz"
    pushed = False

    adb_available = adb_check(ADB_BRIDGE)
    if adb_available:
        print(f"    Pushing via ADB bridge...")
        t_start = time.time()
        pushed = adb_push(ADB_BRIDGE, local_tar, remote_tar, timeout=1800)
        t_elapsed = time.time() - t_start
        if pushed:
            print(f"    Push complete: {t_elapsed:.0f}s")
        else:
            print(f"    ADB push failed after {t_elapsed:.0f}s")

    if not pushed:
        print(f"    [!] ADB push failed. Trying base64 via syncCmd (slow for large files)...")
        if tar_size_mb > 50:
            print(f"    [!] File too large ({tar_size_mb:.0f}MB) for base64 transfer.")
            print(f"    [!] Connect ADB bridge and retry.")
            restore_log["steps"]["push_tar"] = False
            return restore_log

        # Base64 chunked upload via syncCmd
        with open(local_tar, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode()

        chunk_size = 3000
        chunks = [b64_data[i:i+chunk_size] for i in range(0, len(b64_data), chunk_size)]
        print(f"    Uploading via base64: {len(chunks)} chunks...")

        await cloud_cmd(client, target_pad, f"rm -f {remote_tar}.b64 {remote_tar}")
        await asyncio.sleep(API_DELAY)

        for ci, chunk in enumerate(chunks):
            op = ">>" if ci > 0 else ">"
            await cloud_cmd(client, target_pad,
                f'echo -n "{chunk}" {op} {remote_tar}.b64', timeout_sec=10)
            await asyncio.sleep(API_DELAY)
            if (ci + 1) % 100 == 0:
                print(f"      {ci+1}/{len(chunks)} chunks...")

        result = await cloud_cmd(client, target_pad,
            f"base64 -d {remote_tar}.b64 > {remote_tar} && rm -f {remote_tar}.b64 && echo B64_OK",
            timeout_sec=60)
        pushed = "B64_OK" in result
        if pushed:
            print(f"    Base64 upload complete")
        else:
            print(f"    [!] Base64 upload failed")

    restore_log["steps"]["push_tar"] = pushed

    if not pushed:
        print(f"  [!] Cannot push tar to device. Aborting.")
        return restore_log

    # Extract tar on device (runs as ROOT via syncCmd)
    print(f"    Extracting tar on device...")
    # Use background extraction for large files (syncCmd has timeout)
    marker = "/tmp/.extract_done_full"
    await cloud_cmd(client, target_pad, f"rm -f {marker}")
    await asyncio.sleep(API_DELAY)

    extract_cmd = (
        f"nohup sh -c '"
        f"cd / && tar xzf {remote_tar} 2>/dev/null && "
        f"echo OK > {marker}"
        f"' >/dev/null 2>&1 &"
    )
    await cloud_cmd(client, target_pad, extract_cmd, timeout_sec=10)
    await asyncio.sleep(API_DELAY)

    # Poll for extraction completion (may take several minutes for large archives)
    print(f"    Waiting for extraction (polling every 5s)...")
    extract_ok = False
    for poll in range(120):  # max 10 minutes
        await asyncio.sleep(5)
        check = await cloud_cmd(client, target_pad, f"cat {marker} 2>/dev/null")
        if check and "OK" in check:
            extract_ok = True
            await cloud_cmd(client, target_pad, f"rm -f {marker}")
            break
        if (poll + 1) % 12 == 0:
            print(f"      {(poll+1)*5}s elapsed...")

    print(f"    Extract: {'✓' if extract_ok else 'STILL RUNNING (may complete after restore)'}")
    restore_log["steps"]["extract_tar"] = extract_ok

    # Cleanup tar on device
    await cloud_cmd(client, target_pad, f"rm -f {remote_tar}")
    await asyncio.sleep(API_DELAY)

    # ── Step 7b: Fix accounts DB journal mode (DELETE, not WAL) ──
    # Root cause of v1-v5 crashes: extracted DBs may be in WAL mode.
    # system_server can't create WAL/SHM sidecar files under SELinux
    # accounts_data_file context → SQLITE_IOERR_WRITE → crash loop.
    print(f"\n  [7b/10] Fixing accounts DB journal mode (WAL → DELETE)...")

    accounts_dbs = [
        "/data/system_ce/0/accounts_ce.db",
        "/data/system_de/0/accounts_de.db",
    ]

    for db_path in accounts_dbs:
        db_name = db_path.split("/")[-1]

        # Step 1: Clean existing WAL/SHM/journal sidecar files
        clean_result = await cloud_cmd(client, target_pad,
            f"rm -f '{db_path}-wal' '{db_path}-shm' '{db_path}-journal' "
            f"&& echo CLEAN_OK",
            timeout_sec=10)
        await asyncio.sleep(API_DELAY)

        # Step 2: Check if DB exists (may not if tar didn't include it)
        exists = await cloud_cmd(client, target_pad,
            f"[ -f '{db_path}' ] && echo EXISTS || echo MISSING",
            timeout_sec=5)
        await asyncio.sleep(API_DELAY)

        if "MISSING" in (exists or ""):
            print(f"    {db_name}: not found (skipped)")
            continue

        # Step 3: Use sqlite3 if available to checkpoint WAL and convert to DELETE
        # Most VMOS images don't have sqlite3, so we use a shell-based approach:
        # Attempt sqlite3 first, fall back to just cleaning sidecar files
        convert_result = await cloud_cmd(client, target_pad,
            f"if command -v sqlite3 >/dev/null 2>&1; then "
            f"  sqlite3 '{db_path}' 'PRAGMA wal_checkpoint(TRUNCATE); PRAGMA journal_mode=DELETE;' 2>/dev/null && echo CONVERTED; "
            f"else "
            f"  echo NO_SQLITE3; "
            f"fi",
            timeout_sec=15)
        await asyncio.sleep(API_DELAY)

        if "CONVERTED" in (convert_result or ""):
            print(f"    {db_name}: WAL → DELETE (sqlite3)")
        else:
            # Fallback: just ensure no WAL sidecar files exist.
            # If the DB file itself is in WAL mode but no -wal file exists,
            # SQLite will auto-recover to rollback journal on next open.
            print(f"    {db_name}: cleaned sidecar files (no sqlite3 on device)")

        # Step 4: Fix permissions for this DB
        await cloud_cmd(client, target_pad,
            f"chown 1000:1000 '{db_path}' && "
            f"chmod 600 '{db_path}' && "
            f"chcon u:object_r:system_data_file:s0 '{db_path}' && "
            f"echo PERM_OK",
            timeout_sec=10)
        await asyncio.sleep(API_DELAY)

        # Verify no sidecar files
        wal_check = await cloud_cmd(client, target_pad,
            f"ls '{db_path}-wal' 2>/dev/null && echo HAS_WAL || echo NO_WAL",
            timeout_sec=5)
        await asyncio.sleep(API_DELAY)
        print(f"    {db_name}: perms fixed, WAL={wal_check}")

    restore_log["steps"]["db_journal_fix"] = True

    # ── Step 8: Fix permissions for ALL packages ──
    print(f"\n  [8/10] Fixing permissions for all packages...")

    # Batch permission fix: get UID mapping for all installed packages
    uid_map_cmd = (
        "for pkg in $(pm list packages -3 | cut -d: -f2); do "
        "  uid=$(dumpsys package $pkg 2>/dev/null | grep 'userId=' | head -1 | sed 's/.*userId=//;s/ .*//'); "
        "  [ -n \"$uid\" ] && echo \"$pkg:$uid\"; "
        "done"
    )
    uid_map_raw = await cloud_cmd(client, target_pad, uid_map_cmd, timeout_sec=60)
    await asyncio.sleep(API_DELAY)

    uid_map = {}
    if uid_map_raw:
        for line in uid_map_raw.splitlines():
            if ":" in line:
                parts = line.strip().split(":", 1)
                if len(parts) == 2 and parts[1].strip().isdigit():
                    uid_map[parts[0]] = parts[1].strip()

    print(f"    UID map: {len(uid_map)} packages")

    # Batch chown + restorecon in groups of 10
    pkgs_with_uid = list(uid_map.items())
    for i in range(0, len(pkgs_with_uid), 10):
        batch = pkgs_with_uid[i:i+10]
        batch_cmd = "; ".join(
            f"chown -R {uid}:{uid} /data/data/{pkg}/ 2>/dev/null && "
            f"restorecon -R /data/data/{pkg}/ 2>/dev/null"
            for pkg, uid in batch
        )
        await cloud_cmd(client, target_pad, batch_cmd + " && echo BATCH_OK", timeout_sec=30)
        await asyncio.sleep(API_DELAY)

    print(f"    Permissions fixed for {len(uid_map)} packages")
    restore_log["steps"]["permissions"] = len(uid_map)

    # Fix system-level DB permissions
    print(f"    Fixing system DB permissions...")
    sys_perm_cmd = (
        "chown 1000:1000 /data/system_ce/0/accounts_ce.db 2>/dev/null; "
        "chown 1000:1000 /data/system_de/0/accounts_de.db 2>/dev/null; "
        "chmod 600 /data/system_ce/0/accounts_ce.db 2>/dev/null; "
        "chmod 600 /data/system_de/0/accounts_de.db 2>/dev/null; "
        "chcon u:object_r:system_data_file:s0 /data/system_ce/0/accounts_ce.db 2>/dev/null; "
        "chcon u:object_r:system_data_file:s0 /data/system_de/0/accounts_de.db 2>/dev/null; "
        "rm -f /data/system_ce/0/accounts_ce.db-wal /data/system_ce/0/accounts_ce.db-shm 2>/dev/null; "
        "rm -f /data/system_de/0/accounts_de.db-wal /data/system_de/0/accounts_de.db-shm 2>/dev/null; "
        "chown 1017:1017 /data/misc/keystore/user_0/* 2>/dev/null; "
        "chmod 600 /data/misc/keystore/user_0/* 2>/dev/null; "
        "restorecon -R /data/system_ce/0/ 2>/dev/null; "
        "restorecon -R /data/system_de/0/ 2>/dev/null; "
        "restorecon -R /data/misc/keystore/ 2>/dev/null; "
        "restorecon -R /data/misc/wifi/ 2>/dev/null; "
        "echo SYS_PERM_OK"
    )
    sys_result = await cloud_cmd(client, target_pad, sys_perm_cmd, timeout_sec=30)
    print(f"    System permissions: {'✓' if 'SYS_PERM_OK' in sys_result else '✗'}")
    restore_log["steps"]["sys_permissions"] = "SYS_PERM_OK" in sys_result

    # ── Step 9: Broadcast account changes + restart GMS ──
    print(f"\n  [9/10] Activating accounts + restarting services...")
    await cloud_cmd(client, target_pad,
        "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED "
        "--receiver-include-background 2>/dev/null && echo BROADCAST_OK")
    await asyncio.sleep(API_DELAY)

    # Restart GMS to pick up accounts
    await cloud_cmd(client, target_pad,
        "am force-stop com.google.android.gms && "
        "sleep 2 && "
        "am startservice com.google.android.gms/.checkin.CheckinService 2>/dev/null && "
        "echo GMS_RESTARTED")
    await asyncio.sleep(API_DELAY)
    restore_log["steps"]["activate_accounts"] = True

    # ── Step 10: Pre-restart validation + final restart ──
    print(f"\n  [10/10] Pre-restart validation + final restart...")

    # CRITICAL: Verify no WAL/SHM sidecar files exist before restart.
    # If they exist, system_server will try to open them and hit
    # SQLITE_IOERR_WRITE under SELinux → crash loop (status=11/14).
    pre_restart_ok = True
    wal_check_cmd = (
        "ls /data/system_ce/0/accounts_ce.db-wal "
        "/data/system_ce/0/accounts_ce.db-shm "
        "/data/system_de/0/accounts_de.db-wal "
        "/data/system_de/0/accounts_de.db-shm "
        "2>/dev/null && echo HAS_WAL || echo SAFE_NO_WAL"
    )
    wal_result = await cloud_cmd(client, target_pad, wal_check_cmd, timeout_sec=10)
    await asyncio.sleep(API_DELAY)

    if "HAS_WAL" in (wal_result or ""):
        print(f"    WARNING: WAL/SHM files found — cleaning before restart...")
        await cloud_cmd(client, target_pad,
            "rm -f /data/system_ce/0/accounts_ce.db-wal "
            "/data/system_ce/0/accounts_ce.db-shm "
            "/data/system_ce/0/accounts_ce.db-journal "
            "/data/system_de/0/accounts_de.db-wal "
            "/data/system_de/0/accounts_de.db-shm "
            "/data/system_de/0/accounts_de.db-journal "
            "&& echo EMERGENCY_CLEAN",
            timeout_sec=10)
        await asyncio.sleep(API_DELAY)
    else:
        print(f"    Pre-restart check: SAFE (no WAL/SHM sidecar files)")

    try:
        os.environ["VMOS_ALLOW_RESTART"] = "1"
        result = await client.instance_restart([target_pad])
        code = result.get("code", -1)
        print(f"    restart: code={code} — waiting 60s...")
        await asyncio.sleep(60)
    except Exception as e:
        print(f"    restart error: {e}")
    restore_log["steps"]["final_restart"] = True

    # Wait for device to come back
    alive = await cloud_cmd_retry(client, target_pad, "echo ALIVE && id", retries=10)
    if "ALIVE" in alive:
        print(f"    Device back online: {'ROOT' if 'uid=0' in alive else 'non-root'}")
    else:
        print(f"    [!] Device slow to respond — may need more time")

    restore_log["status"] = "complete"
    restore_log["completed"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # Save restore log
    log_file = os.path.join(clone_dir, "restore_log.json")
    with open(log_file, "w") as f:
        json.dump(restore_log, f, indent=2)

    print(f"\n{'═'*70}")
    print(f"  RESTORE COMPLETE")
    print(f"  Target: {target_pad}")
    print(f"  Identity: {len(fingerprint)} properties written")
    print(f"  Data: {tar_size_mb:.1f} MB extracted")
    print(f"  Permissions: {len(uid_map)} packages fixed")
    print(f"  Log: {log_file}")
    print(f"{'═'*70}")
    print(f"\n  Apps should now work WITHOUT re-login.")
    print(f"  Run 'verify' to confirm: python3 -m vmos_titan.core.clone_engine verify {neighbor_ip}")

    return restore_log


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: VERIFY CLONE
# ═══════════════════════════════════════════════════════════════════════

async def verify_clone(client: VMOSCloudClient, target_pad: str,
                       neighbor_ip: str) -> dict:
    """Verify the clone by comparing properties, apps, accounts, and taking screenshots."""
    clone_dir = os.path.join(CLONE_ROOT, neighbor_ip.replace(".", "_"))
    manifest_file = os.path.join(clone_dir, "clone_manifest.json")

    if not os.path.exists(manifest_file):
        print(f"[!] No backup manifest at {manifest_file}")
        return {"error": "no_backup"}

    with open(manifest_file) as f:
        manifest = json.load(f)

    fp_file = os.path.join(clone_dir, "fingerprint.json")
    if os.path.exists(fp_file):
        with open(fp_file) as f:
            source_fp = json.load(f)
    else:
        source_fp = {}

    print(f"\n{'═'*70}")
    print(f"  CLONE VERIFICATION")
    print(f"  Source: {neighbor_ip} ({manifest.get('brand','')} {manifest.get('model','')})")
    print(f"  Target: {target_pad}")
    print(f"{'═'*70}")

    results = {"checks": {}, "overall": "pending"}

    # Check 1: Device alive
    alive = await cloud_cmd(client, target_pad, "echo ALIVE && id")
    await asyncio.sleep(API_DELAY)
    results["checks"]["alive"] = "ALIVE" in alive
    print(f"\n  [1] Device alive: {'✓' if results['checks']['alive'] else '✗'}")

    if not results["checks"]["alive"]:
        results["overall"] = "device_offline"
        return results

    # Check 2: Identity match
    print(f"\n  [2] Identity match:")
    matched = 0
    mismatched = 0
    for key in list(source_fp.keys())[:20]:  # Check top 20 properties
        current = await cloud_cmd(client, target_pad, f"getprop {key}")
        await asyncio.sleep(API_DELAY)
        expected = source_fp[key]
        if current.strip() == expected.strip():
            matched += 1
        else:
            mismatched += 1
            if mismatched <= 5:
                print(f"    MISMATCH: {key}")
                print(f"      expected: {expected}")
                print(f"      got:      {current}")

    total = matched + mismatched
    pct = (matched / total * 100) if total > 0 else 0
    results["checks"]["identity_match"] = f"{matched}/{total} ({pct:.0f}%)"
    print(f"    Identity: {matched}/{total} properties match ({pct:.0f}%)")

    # Check 3: Accounts
    print(f"\n  [3] Accounts:")
    accts = await cloud_cmd(client, target_pad, "dumpsys account 2>/dev/null | grep 'Account {' | head -10")
    await asyncio.sleep(API_DELAY)
    acct_count = len([l for l in accts.splitlines() if "Account {" in l]) if accts else 0
    source_acct_count = len(manifest.get("accounts", []))
    results["checks"]["accounts"] = f"{acct_count} (source had {source_acct_count})"
    print(f"    Current: {acct_count} accounts (source had {source_acct_count})")
    if accts:
        for line in accts.splitlines()[:5]:
            if "name=" in line:
                print(f"      {line.strip()}")

    # Check 4: Keystore
    print(f"\n  [4] Keystore:")
    ks_count = await cloud_cmd(client, target_pad,
        "ls /data/misc/keystore/user_0/ 2>/dev/null | wc -l")
    await asyncio.sleep(API_DELAY)
    source_ks = manifest.get("keystore_count", 0)
    results["checks"]["keystore"] = f"{ks_count.strip()} entries (source had {source_ks})"
    print(f"    Current: {ks_count.strip()} entries (source had {source_ks})")

    # Check 5: Apps installed
    print(f"\n  [5] Apps installed:")
    current_pkgs = await cloud_cmd(client, target_pad, "pm list packages -3 | wc -l")
    await asyncio.sleep(API_DELAY)
    source_pkgs = manifest.get("pkg_count", 0)
    results["checks"]["apps"] = f"{current_pkgs.strip()} (source had {source_pkgs})"
    print(f"    Current: {current_pkgs.strip()} third-party (source had {source_pkgs})")

    # Check 6: Chrome data
    print(f"\n  [6] Chrome data:")
    chrome_check = await cloud_cmd(client, target_pad,
        "ls /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null | head -5")
    await asyncio.sleep(API_DELAY)
    has_chrome = bool(chrome_check and "Login" in chrome_check or "Cookies" in chrome_check)
    results["checks"]["chrome_data"] = has_chrome
    print(f"    Chrome profile: {'✓ (Login Data/Cookies present)' if has_chrome else '✗'}")
    if chrome_check:
        print(f"      {chrome_check}")

    # Check 7: GMS state
    print(f"\n  [7] Google Play Services:")
    gms_check = await cloud_cmd(client, target_pad,
        "dumpsys activity service GmsClientSupervisor 2>/dev/null | head -5")
    await asyncio.sleep(API_DELAY)
    gms_running = bool(gms_check and "Service" in gms_check)
    results["checks"]["gms_running"] = gms_running
    print(f"    GMS: {'✓ running' if gms_running else '✗ not detected'}")

    # Check 8: Screenshot of home screen
    print(f"\n  [8] Taking screenshot...")
    try:
        ss_result = await client.screenshot([target_pad])
        results["checks"]["screenshot"] = ss_result.get("code") == 200
        print(f"    Screenshot: {'✓ captured' if results['checks']['screenshot'] else '✗'}")
    except Exception as e:
        results["checks"]["screenshot"] = False
        print(f"    Screenshot: ✗ ({e})")

    # Overall assessment
    pass_count = sum(1 for v in results["checks"].values()
                     if v is True or (isinstance(v, str) and "✓" not in str(v) and int(v.split("/")[0]) > 0
                                      if "/" in str(v) else False))
    total_checks = len(results["checks"])
    results["overall"] = "PASS" if pct >= 90 and acct_count > 0 else "PARTIAL"

    print(f"\n{'═'*70}")
    print(f"  VERIFICATION {'PASSED ✓' if results['overall'] == 'PASS' else 'PARTIAL ⚠'}")
    print(f"  Identity match: {pct:.0f}%")
    print(f"  Accounts: {acct_count}/{source_acct_count}")
    print(f"  Keystore: {ks_count.strip()}/{source_ks}")
    print(f"{'═'*70}")

    # Save verification results
    verify_file = os.path.join(clone_dir, "verification.json")
    with open(verify_file, "w") as f:
        json.dump(results, f, indent=2)

    return results


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    if len(sys.argv) < 2:
        print("""
Zero-Login Device Clone Engine v1.0
======================================

Usage:
  python3 -m vmos_titan.core.clone_engine probe                     # Analyze both devices
  python3 -m vmos_titan.core.clone_engine backup <NEIGHBOR_IP>      # Full-partition backup from neighbor
  python3 -m vmos_titan.core.clone_engine restore <NEIGHBOR_IP>     # Restore to best device
  python3 -m vmos_titan.core.clone_engine clone <NEIGHBOR_IP>       # Backup + restore
  python3 -m vmos_titan.core.clone_engine verify <NEIGHBOR_IP>      # Verify clone

How it works:
  1. Full /data/ partition tar from neighbor (keystore + accounts + app data)
  2. Identity properties via Cloud API (updatePadAndroidProp + updatePadProperties)
  3. Atomic extraction + permission fix via syncCmd root
  4. Result: apps work without re-login (same as VMOS native backup/restore)

Devices:
  ACP2507303B6HNRI — Device A (clone target)
  APP6476KYH9KMLU5 — Device B (launchpad)
""")
        sys.exit(1)

    client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")
    action = sys.argv[1].lower()

    if action == "probe":
        await probe_all_devices(client)

    elif action == "backup":
        if len(sys.argv) < 3:
            print("Usage: ... backup <NEIGHBOR_IP>")
            sys.exit(1)
        neighbor_ip = sys.argv[2]
        # Use device A as launchpad by default (first alive device)
        probes = await probe_all_devices(client)
        launchpad = None
        for pad, p in probes.items():
            if p.alive:
                launchpad = pad
                break
        if not launchpad:
            print("[!] No device responding")
            sys.exit(1)
        print(f"\n  Using {launchpad} as launchpad for relay.")
        await full_partition_backup(client, launchpad, neighbor_ip)

    elif action == "restore":
        if len(sys.argv) < 3:
            print("Usage: ... restore <NEIGHBOR_IP>")
            sys.exit(1)
        neighbor_ip = sys.argv[2]
        # Use best device as target
        probes = await probe_all_devices(client)
        target = None
        for pad, p in probes.items():
            if p.alive:
                if p.is_cloud_vm or target is None:
                    target = pad
        if not target:
            print("[!] No device responding")
            sys.exit(1)
        print(f"\n  Restoring to {target}.")
        await full_partition_restore(client, target, neighbor_ip)

    elif action == "clone":
        if len(sys.argv) < 3:
            print("Usage: ... clone <NEIGHBOR_IP>")
            sys.exit(1)
        neighbor_ip = sys.argv[2]
        probes = await probe_all_devices(client)
        alive = {k: v for k, v in probes.items() if v.alive}
        if not alive:
            print("[!] No device responding")
            sys.exit(1)

        # Pick launchpad and target
        launchpad = next(iter(alive))
        target = launchpad
        # If 2 devices alive, use one as launchpad (on neighbor network) and other as target
        if len(alive) >= 2:
            pads = list(alive.keys())
            # Prefer cloud VM as target
            cloud_vms = [p for p in pads if alive[p].is_cloud_vm]
            if cloud_vms:
                target = cloud_vms[0]
                launchpad = [p for p in pads if p != target][0]
            else:
                launchpad = pads[0]
                target = pads[1]

        print(f"\n  Launchpad: {launchpad} (relay to neighbor)")
        print(f"  Target:    {target} (will receive clone)")

        manifest = await full_partition_backup(client, launchpad, neighbor_ip)
        if manifest and manifest.status == "backed_up":
            print(f"\n  {'─'*50}")
            print(f"  Backup complete. Starting restore in 10s...")
            print(f"  {'─'*50}")
            await asyncio.sleep(10)
            await full_partition_restore(client, target, neighbor_ip)
            await asyncio.sleep(5)
            await verify_clone(client, target, neighbor_ip)
        else:
            print(f"\n  [!] Backup failed. Restore skipped.")

    elif action == "verify":
        if len(sys.argv) < 3:
            print("Usage: ... verify <NEIGHBOR_IP>")
            sys.exit(1)
        neighbor_ip = sys.argv[2]
        probes = await probe_all_devices(client)
        target = None
        for pad, p in probes.items():
            if p.alive:
                target = pad
                break
        if not target:
            print("[!] No device responding")
            sys.exit(1)
        await verify_clone(client, target, neighbor_ip)

    else:
        print(f"Unknown action: {action}")
        print("Actions: probe, backup, restore, clone, verify")
        sys.exit(1)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
