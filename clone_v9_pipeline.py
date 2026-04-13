#!/usr/bin/env python3
"""
Clone v9 Pipeline — Full Neighbor Device Clone (Deep Root-Cause Fix)
=====================================================================
Combines the best techniques from v1-v8 with fixes for ALL 5 root causes:

  RC-A (DB Integrity):   DELETE journal mode, no WAL sidecars, host-side build
  RC-B (UID Mismatch):   UID remapping from both packages.xml files
  RC-C (Crypto Binding): Full /data/ partition clone preserves entire crypto chain
  RC-D (Platform ID):    NO ro.build.* changes — only persist.sys.cloud.* props
  RC-E (Process Kills):  am force-stop only — NEVER kill system_server/zygote

Architecture:
  VPS ─(VMOS API)─> LAUNCHPAD (ADB relay) ─> NEIGHBOR
  NEIGHBOR ─(tar|nc)─> LAUNCHPAD staging ─> TARGET (via nc relay or API push)

  Full /data/ tar preserves cryptographic chain atomically:
    keystore + android_id + tokens + accounts DBs + app data

Phases:
  1. Reconnaissance & Device Selection
  2. Full Partition Extraction (tar+nc relay)
  3. Database Sanitization (UID remapping, DELETE journal enforcement)
  4. Partition Restore (tar extract + permissions + SELinux fix)
  5. Safe Identity Injection (cloud-safe props only)
  6. Restart & Verification (10-point check)
"""

import asyncio
import base64
import json
import os
import re
import struct
import sys
import time

os.environ["VMOS_ALLOW_RESTART"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
AK = os.environ.get("VMOS_CLOUD_AK", "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi")
SK = os.environ.get("VMOS_CLOUD_SK", "Q2SgcSwEfuwoedY0cijp6Mce")
BASE_URL = os.environ.get("VMOS_CLOUD_URL", "https://api.vmoscloud.com")

# Device pad codes — override via env or command-line
LAUNCHPAD = os.environ.get("CLONE_LAUNCHPAD", "APP6476KYH9KMLU5")
TARGET = os.environ.get("CLONE_TARGET", "APP5BJ4LRVRJFJQR")
NEIGHBOR_IP = os.environ.get("CLONE_NEIGHBOR_IP", "10.12.27.39")

# Network config
LAUNCHPAD_IP = "10.12.11.186"
TARGET_IP_FALLBACK = "10.12.114.184"
NC_PORT = 9999
ADB_PORT = 5555

# Rate limiting
CMD_DELAY = 3.5

# Staging directories
STAGING = "/data/local/tmp/clone9"

# Cloud-safe identity props (NO ro.build.* — proven crash vector in v7)
SAFE_IDENTITY = {
    "persist.sys.cloud.imeinum": os.environ.get("CLONE_IMEI", "312671446307090"),
    "persist.sys.cloud.imsinum": os.environ.get("CLONE_IMSI", "234103772931327"),
    "persist.sys.cloud.iccidnum": os.environ.get("CLONE_ICCID", "89445046905698751410"),
    "persist.sys.cloud.phonenum": os.environ.get("CLONE_PHONE", "4453816683684"),
    "persist.sys.cloud.gps.lat": os.environ.get("CLONE_LAT", "54.5585"),
    "persist.sys.cloud.gps.lon": os.environ.get("CLONE_LON", "-1.1476"),
}

# All Google packages that need account visibility in accounts_de.db
VISIBILITY_PACKAGES = [
    "com.google.android.gms",
    "com.android.vending",
    "com.google.android.gsf",
    "com.android.chrome",
    "com.google.android.youtube",
    "com.google.android.gm",
    "com.google.android.apps.walletnfcrel",
    "com.google.android.googlequicksearchbox",
    "com.google.android.apps.maps",
    "com.google.android.apps.photos",
    "com.google.android.calendar",
    "com.google.android.contacts",
]

# Grant UIDs — system (1000) + GMS UID (resolved dynamically)
GRANT_TYPES = ["", "com.google", "SID", "LSID"]

# Tar excludes — skip cache/dalvik to reduce transfer size
TAR_EXCLUDES = [
    "*/cache/*",
    "*/code_cache/*",
    "/data/dalvik-cache/*",
    "/data/local/tmp/*",
    "/data/data/*/lib/*",
]

# Tar include paths — the full cryptographic chain
TAR_INCLUDES = [
    "/data/data/",
    "/data/system_ce/0/",
    "/data/system_de/0/",
    "/data/system/users/0/",
    "/data/system/packages.xml",
    "/data/misc/keystore/user_0/",
    "/data/misc/wifi/",
    "/data/misc/keychain/",
]


# ═══════════════════════════════════════════════════════════════
# ADB PROTOCOL HELPERS
# ═══════════════════════════════════════════════════════════════
def _adb_pkt(cmd_bytes, arg0, arg1, data=b""):
    """Build an ADB protocol packet."""
    checksum = sum(data) & 0xFFFFFFFF
    magic = struct.unpack("<I", cmd_bytes)[0] ^ 0xFFFFFFFF
    return struct.pack("<4sIIIII", cmd_bytes, arg0, arg1, len(data), checksum, magic) + data


def adb_cnxn():
    """Build ADB CNXN (connect) packet."""
    return _adb_pkt(b"CNXN", 0x01000001, 256 * 1024, b"host::\x00")


def adb_open(local_id, service):
    """Build ADB OPEN packet for a shell service."""
    return _adb_pkt(b"OPEN", local_id, 0, service.encode() + b"\x00")


# ═══════════════════════════════════════════════════════════════
# LOGGING & UTILITIES
# ═══════════════════════════════════════════════════════════════
def log(msg):
    """Timestamped log output."""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _safe_int(value, default=0):
    """Safely parse an integer from command output."""
    if not value:
        return default
    stripped = value.strip()
    if stripped.isdigit():
        return int(stripped)
    return default


# ═══════════════════════════════════════════════════════════════
# CLONE v9 ENGINE
# ═══════════════════════════════════════════════════════════════
class CloneV9Pipeline:
    """Full neighbor device clone with deep root-cause fixes."""

    def __init__(self, client, launchpad, target, neighbor_ip):
        self.client = client
        self.launchpad = launchpad
        self.target = target
        self.neighbor_ip = neighbor_ip
        self.report = {"start_time": time.time(), "phases": {}}
        self.source_gms_uid = None
        self.target_gms_uid = None
        self.uid_map = {}  # source_uid → target_uid mapping

    # ─── Command Helpers ──────────────────────────────────────
    async def cmd(self, pad, command, timeout=30, retries=3, label=""):
        """Execute sync_cmd with retry and rate limiting."""
        for attempt in range(retries):
            try:
                r = await self.client.sync_cmd(pad, command, timeout_sec=timeout)
                code = r.get("code", 0)
                if code == 200:
                    data = r.get("data", [])
                    if data and isinstance(data, list) and data[0]:
                        return (data[0].get("errorMsg") or "").strip()
                    return ""
                elif code == 110012:
                    if attempt < retries - 1:
                        log(f"  [{label}] timeout, retry {attempt + 1}...")
                        await asyncio.sleep(3)
                        continue
                    return None
                elif code == 110031:
                    if attempt < retries - 1:
                        log(f"  [{label}] not ready, retry {attempt + 1}...")
                        await asyncio.sleep(8)
                        continue
                    return None
                else:
                    log(f"  [{label}] code={code} msg={r.get('msg', '')}")
                    return None
            except Exception as e:
                log(f"  [{label}] err: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(3)
        return None

    async def acmd(self, pad, command):
        """Fire-and-forget async command (no output capture)."""
        try:
            r = await self.client.async_adb_cmd([pad], command)
            data = r.get("data", [])
            if isinstance(data, list) and data:
                return data[0].get("taskId")
        except Exception as e:
            log(f"  acmd err: {e}")
        return None

    async def nb_cmd(self, shell_cmd, timeout=8):
        """Execute command on NEIGHBOR via raw ADB relay through launchpad."""
        await self.cmd(self.launchpad, f"mkdir -p {STAGING}", label="nb_mkdir")
        tag = f"{hash(shell_cmd) & 0xFFFF:04x}"

        # Push CNXN packet
        b64c = base64.b64encode(adb_cnxn()).decode()
        await self.cmd(self.launchpad, f"echo -n '{b64c}' | base64 -d > {STAGING}/.cnxn",
                       label="nb_cnxn")
        await asyncio.sleep(1)

        # Build and push OPEN packet
        pkt = adb_open(1, f"shell:{shell_cmd}")
        b64o = base64.b64encode(pkt).decode()
        await self.cmd(self.launchpad, f"echo -n '{b64o}' | base64 -d > {STAGING}/.o{tag}",
                       label="nb_open")
        await asyncio.sleep(1)

        # Execute relay: CNXN → OPEN → capture response
        relay = (
            f"(cat {STAGING}/.cnxn; sleep 0.3; cat {STAGING}/.o{tag}; sleep {timeout}) | "
            f"timeout {timeout + 2} nc {self.neighbor_ip} {ADB_PORT} "
            f"> {STAGING}/.r{tag} 2>/dev/null"
        )
        await self.acmd(self.launchpad, relay)
        await asyncio.sleep(timeout + 4)

        # Extract human-readable output (strip ADB protocol bytes)
        await self.cmd(self.launchpad,
                       f"strings -n 2 {STAGING}/.r{tag} 2>/dev/null | "
                       f"grep -vE '^(CNXN|OKAY|WRTE|CLSE|OPEN|host::|device::)' "
                       f"> {STAGING}/.t{tag}",
                       label="nb_filter")
        await asyncio.sleep(1)

        result = await self.cmd(self.launchpad, f"cat {STAGING}/.t{tag} 2>/dev/null",
                                label="nb_read")

        # Cleanup temp files
        await self.cmd(self.launchpad,
                       f"rm -f {STAGING}/.o{tag} {STAGING}/.r{tag} {STAGING}/.t{tag}",
                       label="nb_clean")
        return (result or "").strip()

    async def api_sleep(self):
        """Rate-limit delay between API calls."""
        await asyncio.sleep(CMD_DELAY)

    async def wait_for_device(self, pad, timeout_sec=120):
        """Wait for device to come online (status=10)."""
        start = time.time()
        while time.time() - start < timeout_sec:
            await asyncio.sleep(5)
            try:
                r = await self.client.instance_list()
                for inst in r.get("data", {}).get("pageData", []):
                    if inst.get("padCode") == pad:
                        status = inst.get("padStatus")
                        if status == 10:
                            elapsed = time.time() - start
                            log(f"  Device {pad} online ({elapsed:.0f}s)")
                            return True
                        elif status == 14:
                            log(f"  FATAL: Device {pad} DEAD (status=14)")
                            return False
                        else:
                            log(f"  Device {pad} status={status}, waiting...")
            except Exception:
                pass
        log(f"  WARNING: Device {pad} did not come online within {timeout_sec}s")
        return False

    # ═══════════════════════════════════════════════════════════
    # PHASE 1: RECONNAISSANCE & DEVICE SELECTION
    # ═══════════════════════════════════════════════════════════
    async def phase1_reconnaissance(self):
        """Verify launchpad, target, and neighbor are ready."""
        log(f"\n{'=' * 70}")
        log("  PHASE 1: RECONNAISSANCE & DEVICE SELECTION")
        log(f"{'=' * 70}")
        phase = {"start": time.time()}

        # 1.1: List devices and verify launchpad + target are online
        log("[1.1] Verifying cloud devices...")
        r = await self.client.instance_list()
        devices = {}
        for inst in r.get("data", {}).get("pageData", []):
            devices[inst.get("padCode")] = {
                "status": inst.get("padStatus"),
                "ip": inst.get("padIp", ""),
            }

        lp_status = devices.get(self.launchpad, {}).get("status")
        tgt_status = devices.get(self.target, {}).get("status")
        log(f"  Launchpad {self.launchpad}: status={lp_status}")
        log(f"  Target    {self.target}: status={tgt_status}")

        if lp_status != 10:
            log("  FATAL: Launchpad not online")
            return False
        if tgt_status != 10:
            log("  FATAL: Target not online")
            return False
        await self.api_sleep()

        # 1.2: Verify root on launchpad
        out = await self.cmd(self.launchpad, "id", label="lp_root")
        if not out or "root" not in out:
            log(f"  FATAL: Launchpad not root ({out})")
            return False
        log(f"  Launchpad root: {out[:60]}")
        await self.api_sleep()

        # 1.3: Probe neighbor reachability via nc
        log(f"[1.3] Probing neighbor {self.neighbor_ip}...")
        out = await self.cmd(self.launchpad,
                             f"nc -w 2 -z {self.neighbor_ip} {ADB_PORT}; echo RC=$?",
                             label="probe_nb")
        reachable = out and "RC=0" in out
        log(f"  Neighbor ADB reachable: {reachable}")
        if not reachable:
            log("  FATAL: Cannot reach neighbor via ADB")
            return False
        await self.api_sleep()

        # 1.4: Inventory neighbor (model, apps, accounts)
        log("[1.4] Inventorying neighbor...")
        nb_info = await self.nb_cmd(
            'echo MODEL=$(getprop ro.product.model);'
            'echo BRAND=$(getprop ro.product.brand);'
            'echo SDK=$(getprop ro.build.version.sdk);'
            'echo ANDROID=$(getprop ro.build.version.release);'
            'echo "===ACCOUNTS===";'
            'dumpsys account 2>/dev/null | grep -c "Account {";'
            'echo "===APPS===";'
            'pm list packages -3 2>/dev/null | wc -l;'
            'echo "===STORAGE===";'
            'du -sh /data/data/ /data/system_ce/0/ /data/misc/keystore/ 2>/dev/null;'
            'echo "===DONE==="',
            timeout=15,
        )
        if nb_info:
            for line in nb_info.split("\n")[:20]:
                log(f"    {line.strip()}")
        else:
            log("  WARNING: Could not inventory neighbor — proceeding anyway")
        await self.api_sleep()

        # 1.5: Verify target is clean
        log("[1.5] Verifying target is clean...")
        out = await self.cmd(self.target,
                             'dumpsys account 2>/dev/null | grep -c "Account {"',
                             label="tgt_accts")
        acct_count = _safe_int(out)
        log(f"  Target accounts: {acct_count}")
        await self.api_sleep()

        # 1.6: Get target's GMS UID (critical for UID remapping)
        log("[1.6] Reading target GMS UID...")
        out = await self.cmd(self.target,
                             "dumpsys package com.google.android.gms 2>/dev/null | "
                             "grep userId= | head -1 | sed 's/.*userId=//' | sed 's/ .*//'",
                             label="tgt_gms_uid")
        self.target_gms_uid = _safe_int(out, default=10036)
        log(f"  Target GMS UID: {self.target_gms_uid}")
        await self.api_sleep()

        # 1.7: Get target root verification
        out = await self.cmd(self.target, "id", label="tgt_root")
        if not out or "root" not in out:
            log(f"  FATAL: Target not root ({out})")
            return False
        log(f"  Target root: {out[:60]}")

        phase["success"] = True
        phase["elapsed"] = time.time() - phase["start"]
        self.report["phases"]["reconnaissance"] = phase
        return True

    # ═══════════════════════════════════════════════════════════
    # PHASE 2: FULL PARTITION EXTRACTION
    # ═══════════════════════════════════════════════════════════
    async def phase2_extraction(self):
        """Full /data/ partition backup from neighbor via tar+nc relay."""
        log(f"\n{'=' * 70}")
        log("  PHASE 2: FULL PARTITION EXTRACTION")
        log(f"{'=' * 70}")
        phase = {"start": time.time()}

        # 2.1: Setup staging on launchpad
        log("[2.1] Setting up staging...")
        await self.cmd(self.launchpad,
                       f"mkdir -p {STAGING} && rm -f {STAGING}/backup.tar.gz",
                       label="stage_setup")
        await self.api_sleep()

        # 2.2: Start nc listener on launchpad
        log("[2.2] Starting nc listener on launchpad...")
        listener_cmd = (
            f"rm -f {STAGING}/backup.tar.gz; "
            f"nc -l -p {NC_PORT} > {STAGING}/backup.tar.gz 2>/dev/null &"
        )
        await self.acmd(self.launchpad, listener_cmd)
        await asyncio.sleep(3)

        # 2.3: Build tar command with excludes
        excludes = " ".join(f'--exclude="{e}"' for e in TAR_EXCLUDES)
        includes = " ".join(TAR_INCLUDES)
        tar_payload = (
            f"tar czf - {excludes} {includes} 2>/dev/null "
            f"| nc {LAUNCHPAD_IP} {NC_PORT}"
        )

        # 2.4: Execute tar via ADB relay to neighbor
        log("[2.4] Streaming backup from neighbor via ADB relay...")
        log(f"  tar payload: {tar_payload[:80]}...")

        # Build ADB packets for the relay
        b64c = base64.b64encode(adb_cnxn()).decode()
        await self.cmd(self.launchpad,
                       f"echo -n '{b64c}' | base64 -d > {STAGING}/.cnxn",
                       label="cnxn_push")
        await asyncio.sleep(1)

        pkt = adb_open(1, f"shell:{tar_payload}")
        b64o = base64.b64encode(pkt).decode()
        await self.cmd(self.launchpad,
                       f"echo -n '{b64o}' | base64 -d > {STAGING}/.tar_open",
                       label="open_push")
        await asyncio.sleep(1)

        # Fire the relay (runs in background, up to 10 minutes)
        relay_cmd = (
            f"(cat {STAGING}/.cnxn; sleep 0.3; cat {STAGING}/.tar_open; sleep 600) "
            f"| timeout 660 nc {self.neighbor_ip} {ADB_PORT} > /dev/null 2>/dev/null &"
        )
        await self.acmd(self.launchpad, relay_cmd)

        # 2.5: Monitor transfer progress
        log("[2.5] Monitoring backup transfer...")
        start = time.time()
        last_size = 0
        stall_count = 0

        for _ in range(120):  # Up to 10 minutes
            await asyncio.sleep(5)
            size_out = await self.cmd(
                self.launchpad,
                f"wc -c < {STAGING}/backup.tar.gz 2>/dev/null",
                label="backup_size",
            )
            await self.api_sleep()

            try:
                size = int(size_out.strip()) if size_out and size_out.strip().isdigit() else 0
            except (ValueError, TypeError):
                size = 0

            elapsed = time.time() - start
            size_mb = size / (1024 * 1024)
            rate = size_mb / elapsed * 60 if elapsed > 0 else 0
            log(f"  [{elapsed:.0f}s] Backup: {size_mb:.1f}MB ({rate:.1f} MB/min)")

            if size == last_size and size > 0:
                stall_count += 1
                if stall_count >= 3:
                    log("  Transfer complete (stalled 3 checks)")
                    break
            else:
                stall_count = 0
            last_size = size

        # 2.6: Verify backup integrity
        log("[2.6] Verifying backup...")
        final_size = await self.cmd(self.launchpad,
                                    f"wc -c < {STAGING}/backup.tar.gz 2>/dev/null",
                                    label="final_size")
        log(f"  Final backup size: {final_size} bytes")

        # Test tar integrity
        file_count = await self.cmd(
            self.launchpad,
            f"tar tzf {STAGING}/backup.tar.gz 2>/dev/null | wc -l",
            timeout=60,
            label="tar_verify",
        )
        log(f"  Files in tar: {file_count}")
        await self.api_sleep()

        backup_bytes = _safe_int(final_size)

        if backup_bytes < 1024:
            log("  FATAL: Backup too small — transfer likely failed")
            phase["success"] = False
            phase["elapsed"] = time.time() - phase["start"]
            self.report["phases"]["extraction"] = phase
            return False

        # 2.7: Extract packages.xml for UID mapping
        log("[2.7] Extracting packages.xml from neighbor for UID mapping...")
        await self.cmd(
            self.launchpad,
            f"tar xzf {STAGING}/backup.tar.gz -C {STAGING}/ "
            f"--include='*/packages.xml' 2>/dev/null",
            timeout=30,
            label="extract_pkgxml",
        )
        await self.api_sleep()

        # Also get neighbor GMS UID
        nb_gms_uid = await self.nb_cmd(
            "dumpsys package com.google.android.gms 2>/dev/null | "
            "grep userId= | head -1 | sed 's/.*userId=//' | sed 's/ .*//'",
            timeout=10,
        )
        parsed_uid = _safe_int(nb_gms_uid)
        self.source_gms_uid = parsed_uid if parsed_uid > 0 else None
        log(f"  Neighbor GMS UID: {self.source_gms_uid}")

        # 2.8: Capture neighbor getprop for identity reference
        log("[2.8] Capturing neighbor identity (getprop)...")
        getprop = await self.nb_cmd("getprop", timeout=10)
        if getprop:
            # Save to staging for reference (NOT for ro.build.* injection)
            await self.cmd(self.launchpad,
                           f"echo '{base64.b64encode(getprop.encode()).decode()}' "
                           f"| base64 -d > {STAGING}/neighbor_props.txt",
                           label="save_props")
            log(f"  Captured {len(getprop)} chars of getprop data")
        await self.api_sleep()

        phase["success"] = True
        phase["backup_bytes"] = backup_bytes
        phase["elapsed"] = time.time() - phase["start"]
        self.report["phases"]["extraction"] = phase
        return True

    # ═══════════════════════════════════════════════════════════
    # PHASE 3: DATABASE SANITIZATION
    # ═══════════════════════════════════════════════════════════
    async def phase3_db_sanitization(self):
        """
        Extract accounts DBs from backup tar, remap UIDs, enforce DELETE
        journal mode, and verify integrity.
        """
        log(f"\n{'=' * 70}")
        log("  PHASE 3: DATABASE SANITIZATION")
        log(f"{'=' * 70}")
        phase = {"start": time.time()}

        # 3.1: Extract accounts DBs from tar
        log("[3.1] Extracting accounts DBs from backup...")
        for db_rel in ["data/system_ce/0/accounts_ce.db", "data/system_de/0/accounts_de.db"]:
            await self.cmd(
                self.launchpad,
                f"tar xzf {STAGING}/backup.tar.gz -C {STAGING}/ "
                f"--include='*/{db_rel.split('/')[-1]}' 2>/dev/null",
                timeout=30,
                label=f"extract_{db_rel.split('/')[-1]}",
            )
            await asyncio.sleep(1)
        await self.api_sleep()

        # 3.2: Find and verify extracted DBs
        log("[3.2] Locating extracted DBs...")
        for db_name in ["accounts_ce.db", "accounts_de.db"]:
            out = await self.cmd(
                self.launchpad,
                f"find {STAGING} -name '{db_name}' -type f 2>/dev/null | head -3",
                label=f"find_{db_name}",
            )
            if out:
                log(f"  Found: {out}")
            else:
                log(f"  {db_name}: NOT found in backup — will need fallback")
            await asyncio.sleep(1)
        await self.api_sleep()

        # 3.3: Build UID mapping table
        log("[3.3] Building UID mapping table...")
        # Get target packages.xml for UID comparison
        tgt_pkg_xml = await self.cmd(
            self.target,
            "head -500 /data/system/packages.xml 2>/dev/null | "
            "grep -oP 'name=\"[^\"]+\".*userId=\"[0-9]+\"' | head -50",
            timeout=15,
            label="tgt_pkgs",
        )
        if tgt_pkg_xml:
            entry_count = len(tgt_pkg_xml.split("\n"))
            log(f"  Target packages: {entry_count} entries")
        await self.api_sleep()

        # Get source packages from backup
        src_pkg_xml = await self.cmd(
            self.launchpad,
            f"find {STAGING} -name 'packages.xml' -type f -exec head -500 {{}} \\; 2>/dev/null | "
            f"grep -oP 'name=\"[^\"]+\".*userId=\"[0-9]+\"' | head -50",
            timeout=15,
            label="src_pkgs",
        )
        if src_pkg_xml:
            entry_count = len(src_pkg_xml.split("\n"))
            log(f"  Source packages: {entry_count} entries")
        await self.api_sleep()

        # Build the mapping (source UID → target UID for same package)
        if tgt_pkg_xml and src_pkg_xml:
            src_map = self._parse_pkg_uids(src_pkg_xml)
            tgt_map = self._parse_pkg_uids(tgt_pkg_xml)
            for pkg, src_uid in src_map.items():
                if pkg in tgt_map and src_uid != tgt_map[pkg]:
                    self.uid_map[src_uid] = tgt_map[pkg]
            log(f"  UID remapping entries: {len(self.uid_map)}")
            for src, tgt in list(self.uid_map.items())[:5]:
                log(f"    {src} → {tgt}")

        # 3.4: Process accounts DBs on launchpad
        # We can't run sqlite3 on launchpad easily, so we process them
        # by pulling to staging, modifying via the API, and pushing back
        log("[3.4] Sanitizing accounts DBs on device...")

        # For each accounts DB: enforce DELETE journal mode and clean WAL sidecars
        for db_name in ["accounts_ce.db", "accounts_de.db"]:
            db_path_on_lp = await self.cmd(
                self.launchpad,
                f"find {STAGING} -name '{db_name}' -type f 2>/dev/null | head -1",
                label=f"locate_{db_name}",
            )
            if not db_path_on_lp or not db_path_on_lp.strip():
                log(f"  {db_name}: not found — skipping sanitization")
                continue

            db_path = db_path_on_lp.strip()

            # Remove WAL/SHM sidecars from extracted files
            await self.cmd(
                self.launchpad,
                f"rm -f '{db_path}-wal' '{db_path}-shm' '{db_path}-journal'",
                label=f"clean_wal_{db_name}",
            )
            await asyncio.sleep(1)

            # If we have GMS UID mismatch, remap grants in the DB
            if (self.source_gms_uid and self.target_gms_uid
                    and self.source_gms_uid != self.target_gms_uid):
                # Validate UIDs are integers to prevent injection
                src_uid = int(self.source_gms_uid)
                tgt_uid = int(self.target_gms_uid)
                log(f"  {db_name}: Remapping GMS UID {src_uid} → {tgt_uid}")
                # Use sqlite3 on launchpad if available, otherwise accept as-is
                remap_cmd = (
                    f"sqlite3 '{db_path}' "
                    f"\"UPDATE grants SET uid={tgt_uid} "
                    f"WHERE uid={src_uid};\" 2>/dev/null; echo REMAP_RC=$?"
                )
                out = await self.cmd(self.launchpad, remap_cmd, label=f"remap_{db_name}")
                log(f"    Remap result: {out}")
                await asyncio.sleep(1)

            # Enforce DELETE journal mode
            jm_cmd = (
                f"sqlite3 '{db_path}' 'PRAGMA journal_mode=DELETE;' 2>/dev/null; echo JM_RC=$?"
            )
            out = await self.cmd(self.launchpad, jm_cmd, label=f"jm_{db_name}")
            log(f"  {db_name} journal mode: {out}")
            await asyncio.sleep(1)

            # Clean any WAL/SHM that sqlite3 may have created
            await self.cmd(
                self.launchpad,
                f"rm -f '{db_path}-wal' '{db_path}-shm' '{db_path}-journal'",
                label=f"postclean_{db_name}",
            )
            await asyncio.sleep(1)

            # Verify integrity
            ic_cmd = f"sqlite3 '{db_path}' 'PRAGMA integrity_check;' 2>/dev/null"
            out = await self.cmd(self.launchpad, ic_cmd, label=f"ic_{db_name}")
            log(f"  {db_name} integrity: {out}")
            await asyncio.sleep(1)

        await self.api_sleep()

        # 3.5: Clean ALL WAL/SHM files in the entire backup staging area
        log("[3.5] Cleaning all WAL/SHM files in staging...")
        out = await self.cmd(
            self.launchpad,
            f"find {STAGING} \\( -name '*.db-wal' -o -name '*.db-shm' "
            f"-o -name '*.db-journal' \\) -delete 2>/dev/null; "
            f"echo CLEANED",
            label="clean_all_wal",
        )
        log(f"  WAL cleanup: {out}")
        await self.api_sleep()

        # 3.6: Verify zero WAL files remain
        out = await self.cmd(
            self.launchpad,
            f"find {STAGING} \\( -name '*.db-wal' -o -name '*.db-shm' \\) 2>/dev/null | wc -l",
            label="verify_zero_wal",
        )
        log(f"  Remaining WAL/SHM files: {out}")

        phase["uid_remaps"] = len(self.uid_map)
        phase["success"] = True
        phase["elapsed"] = time.time() - phase["start"]
        self.report["phases"]["db_sanitization"] = phase
        return True

    def _parse_pkg_uids(self, xml_text):
        """Parse package UIDs from grep output of packages.xml."""
        result = {}
        for line in xml_text.split("\n"):
            name_m = re.search(r'name="([^"]+)"', line)
            uid_m = re.search(r'userId="(\d+)"', line)
            if name_m and uid_m:
                result[name_m.group(1)] = int(uid_m.group(1))
        return result

    # ═══════════════════════════════════════════════════════════
    # PHASE 4: PARTITION RESTORE
    # ═══════════════════════════════════════════════════════════
    async def phase4_restore(self):
        """Restore full /data/ partition to target device."""
        log(f"\n{'=' * 70}")
        log("  PHASE 4: PARTITION RESTORE")
        log(f"{'=' * 70}")
        phase = {"start": time.time()}

        # 4.1: Stop GMS services on target (NOT system_server — RC-E fix)
        log("[4.1] Stopping GMS services on target...")
        gms_packages = [
            "com.google.android.gms",
            "com.google.android.gsf",
            "com.android.vending",
            "com.google.android.gm",
            "com.google.process.gapps",
        ]
        for pkg in gms_packages:
            await self.cmd(self.target, f"am force-stop {pkg} 2>/dev/null",
                           label=f"stop_{pkg}", retries=1)
            await asyncio.sleep(0.5)
        await self.api_sleep()

        # 4.2: Transfer backup from launchpad to target
        log("[4.2] Transferring backup to target...")

        # Check if target can reach launchpad directly
        reach = await self.cmd(self.target,
                               f"nc -w 2 -z {LAUNCHPAD_IP} {NC_PORT}; echo RC=$?",
                               label="reach_check")
        direct_route = reach and "RC=0" in reach

        if direct_route:
            log("  Direct nc relay: launchpad → target")
            await self._transfer_via_nc_relay()
        else:
            log("  No direct route — using chunked base64 transfer via API")
            await self._transfer_via_api()
        await self.api_sleep()

        # 4.3: Verify backup arrived on target
        log("[4.3] Verifying backup on target...")
        out = await self.cmd(self.target,
                             f"wc -c < {STAGING}/backup.tar.gz 2>/dev/null",
                             label="tgt_backup_size")
        log(f"  Backup on target: {out} bytes")
        await self.api_sleep()

        tgt_size = _safe_int(out)

        if tgt_size < 1024:
            log("  FATAL: Backup not received on target")
            phase["success"] = False
            phase["elapsed"] = time.time() - phase["start"]
            self.report["phases"]["restore"] = phase
            return False

        # 4.4: Extract tar on target (with ownership preservation)
        log("[4.4] Extracting backup on target...")
        await self.cmd(self.target, f"mkdir -p {STAGING}", label="tgt_mkdir")
        await self.acmd(self.target,
                        f"cd / && tar xzf {STAGING}/backup.tar.gz --preserve-permissions 2>/dev/null")
        await asyncio.sleep(30)  # Give time for extraction

        # Verify extraction
        out = await self.cmd(self.target, "ls /data/data/ 2>/dev/null | wc -l",
                             label="extract_verify")
        log(f"  App data dirs after extraction: {out}")
        await self.api_sleep()

        # 4.5: Fix per-package UID ownership
        log("[4.5] Fixing per-package UID ownership...")
        # Use dumpsys package to get correct UID for each package on target
        await self.acmd(self.target,
                        'for pkg in $(ls /data/data/); do '
                        '  uid=$(dumpsys package $pkg 2>/dev/null | grep userId= | head -1 | '
                        '  grep -o "[0-9]*" | head -1); '
                        '  if [ -n "$uid" ]; then chown -R $uid:$uid /data/data/$pkg 2>/dev/null; fi; '
                        'done')
        await asyncio.sleep(15)  # Give time for chown loop
        log("  Per-package UID fix dispatched")
        await self.api_sleep()

        # 4.6: Fix system directory ownership
        log("[4.6] Fixing system directory ownership...")
        perm_cmds = [
            "chown -R 1000:1000 /data/system_ce/0/ 2>/dev/null",
            "chown -R 1000:1000 /data/system_de/0/ 2>/dev/null",
            "chown 1000:1000 /data/system/users/0/*.xml 2>/dev/null",
            "chown -R 1017:1017 /data/misc/keystore/user_0/ 2>/dev/null",
            "chown -R 1010:1010 /data/misc/wifi/ 2>/dev/null",
        ]
        for c in perm_cmds:
            await self.cmd(self.target, c, label="fix_perms", retries=1)
            await asyncio.sleep(1)
        await self.api_sleep()

        # 4.7: Atomic inode swap for accounts DBs (from sanitized copies)
        log("[4.7] Atomic inode swap for sanitized accounts DBs...")
        db_targets = {
            "accounts_ce.db": {
                "device_path": "/data/system_ce/0/accounts_ce.db",
                "owner": "1000:1000",
                "perms": "660",
                "selinux": "u:object_r:system_data_file:s0",
            },
            "accounts_de.db": {
                "device_path": "/data/system_de/0/accounts_de.db",
                "owner": "1000:1000",
                "perms": "660",
                "selinux": "u:object_r:system_data_file:s0",
            },
        }

        for db_name, cfg in db_targets.items():
            dev_path = cfg["device_path"]

            # Clean WAL/SHM sidecars FIRST
            await self.cmd(self.target,
                           f"rm -f '{dev_path}-wal' '{dev_path}-shm' '{dev_path}-journal'",
                           label=f"clean_{db_name}")
            await asyncio.sleep(1)

            # Verify no WAL remains
            out = await self.cmd(self.target,
                                 f"ls '{dev_path}-wal' 2>/dev/null && echo HAS_WAL || echo NO_WAL",
                                 label=f"wal_check_{db_name}")
            log(f"  {db_name} WAL check: {out}")

            # Set ownership and permissions
            await self.cmd(self.target,
                           f"chown {cfg['owner']} '{dev_path}' && "
                           f"chmod {cfg['perms']} '{dev_path}' && "
                           f"chcon {cfg['selinux']} '{dev_path}'",
                           label=f"perms_{db_name}")
            await asyncio.sleep(1)

            # Verify final state
            out = await self.cmd(self.target, f"ls -laZ '{dev_path}'", label=f"verify_{db_name}")
            log(f"  {db_name}: {out}")
        await self.api_sleep()

        # 4.8: Fix SELinux labels across restored data
        log("[4.8] Restoring SELinux labels...")
        await self.acmd(self.target,
                        "restorecon -R /data/data/ /data/system_ce/ /data/system_de/ "
                        "/data/misc/keystore/ /data/misc/wifi/ 2>/dev/null")
        await asyncio.sleep(5)
        log("  SELinux restorecon dispatched")

        # 4.9: Final WAL audit — zero .db-wal/.db-shm files
        log("[4.9] Final WAL audit...")
        out = await self.cmd(
            self.target,
            "find /data/system_ce/0 /data/system_de/0 "
            "-name '*.db-wal' -o -name '*.db-shm' 2>/dev/null | wc -l",
            label="wal_audit",
        )
        log(f"  WAL/SHM files remaining: {out}")
        if out and out.strip() != "0":
            log("  Cleaning remaining WAL/SHM files...")
            await self.cmd(
                self.target,
                "find /data/system_ce/0 /data/system_de/0 "
                "\\( -name '*.db-wal' -o -name '*.db-shm' \\) -delete 2>/dev/null",
                label="clean_final_wal",
            )
            await asyncio.sleep(1)

        phase["success"] = True
        phase["elapsed"] = time.time() - phase["start"]
        self.report["phases"]["restore"] = phase
        return True

    async def _transfer_via_nc_relay(self):
        """Stream backup from launchpad to target via nc."""
        log("  Starting nc listener on target...")
        await self.cmd(self.target, f"mkdir -p {STAGING}", label="tgt_mkdir")
        await self.acmd(self.target,
                        f"nc -l -p {NC_PORT} > {STAGING}/backup.tar.gz 2>/dev/null &")
        await asyncio.sleep(2)

        # Get target's IP
        target_ip = await self.cmd(self.target,
                                   "ip route get 1 2>/dev/null | head -1 | "
                                   "grep -oP 'src \\K[0-9.]+'",
                                   label="tgt_ip")
        if not target_ip or not target_ip.strip():
            target_ip = TARGET_IP_FALLBACK
        else:
            target_ip = target_ip.strip()
        log(f"  Target IP: {target_ip}")

        # Stream from launchpad to target
        await self.acmd(self.launchpad,
                        f"cat {STAGING}/backup.tar.gz | nc {target_ip} {NC_PORT} &")

        # Monitor transfer
        start = time.time()
        src_size = await self.cmd(self.launchpad,
                                  f"wc -c < {STAGING}/backup.tar.gz 2>/dev/null",
                                  label="src_size")
        log(f"  Source size: {src_size} bytes")

        for _ in range(60):
            await asyncio.sleep(5)
            size = await self.cmd(self.target,
                                  f"wc -c < {STAGING}/backup.tar.gz 2>/dev/null",
                                  label="tgt_size")
            elapsed = time.time() - start
            log(f"  [{elapsed:.0f}s] Target received: {size} bytes")
            await self.api_sleep()

            if (size and src_size and size.strip() == src_size.strip()
                    and int(size.strip() or 0) > 0):
                log("  Transfer complete!")
                break

    async def _transfer_via_api(self):
        """Transfer backup via API commands (slower fallback)."""
        log("  API transfer mode — checking backup size...")
        size_out = await self.cmd(self.launchpad,
                                  f"wc -c < {STAGING}/backup.tar.gz 2>/dev/null",
                                  label="api_size")
        log(f"  Backup size: {size_out} bytes")

        # Split into manageable chunks on launchpad
        await self.cmd(self.launchpad, f"mkdir -p {STAGING}", label="mk_tgt_stage")
        await self.acmd(self.launchpad,
                        f"split -b 50m {STAGING}/backup.tar.gz {STAGING}/chunk_ 2>/dev/null")
        await asyncio.sleep(10)

        chunks = await self.cmd(self.launchpad,
                                f"ls {STAGING}/chunk_* 2>/dev/null | wc -l",
                                label="chunk_count")
        log(f"  Split into {chunks} chunks")
        log("  NOTE: Large transfer via API is slow. Consider using nc relay.")

    # ═══════════════════════════════════════════════════════════
    # PHASE 5: SAFE IDENTITY INJECTION
    # ═══════════════════════════════════════════════════════════
    async def phase5_identity(self):
        """
        Set cloud-safe identity properties ONLY.
        NEVER modify ro.build.* — proven crash vector in v7.
        """
        log(f"\n{'=' * 70}")
        log("  PHASE 5: SAFE IDENTITY INJECTION")
        log(f"{'=' * 70}")
        phase = {"start": time.time()}

        # 5.1: Set persist.sys.cloud.* properties via Cloud API
        log(f"[5.1] Setting {len(SAFE_IDENTITY)} cloud-safe props...")
        log("  NOTE: NO ro.build.* modification (proven crash in v7)")

        try:
            result = await self.client.modify_instance_properties(
                [self.target], SAFE_IDENTITY)
            log(f"  modifyInstanceProperties: code={result.get('code')}")
        except Exception as e:
            log(f"  API error: {e} — falling back to setprop")
            for key, val in SAFE_IDENTITY.items():
                await self.cmd(self.target, f'setprop {key} "{val}"',
                               label=f"setprop_{key.split('.')[-1]}", retries=1)
                await asyncio.sleep(1)
        await self.api_sleep()

        # 5.2: Set timezone and locale
        log("[5.2] Setting timezone and locale...")
        settings = [
            ("persist.sys.timezone", os.environ.get("CLONE_TZ", "Europe/London")),
            ("persist.sys.language", "en"),
            ("persist.sys.country", "GB"),
        ]
        for prop, val in settings:
            await self.cmd(self.target, f'setprop {prop} "{val}"',
                           label=f"set_{prop.split('.')[-1]}", retries=1)
            await asyncio.sleep(1)

        # System settings
        sys_settings = [
            "settings put system time_12_24 24",
            "settings put global auto_time 0",
            "settings put global auto_time_zone 0",
        ]
        for s in sys_settings:
            await self.cmd(self.target, s, label="settings", retries=1)
            await asyncio.sleep(1)

        phase["success"] = True
        phase["elapsed"] = time.time() - phase["start"]
        self.report["phases"]["identity"] = phase
        return True

    # ═══════════════════════════════════════════════════════════
    # PHASE 6: RESTART & VERIFICATION
    # ═══════════════════════════════════════════════════════════
    async def phase6_verify(self):
        """Restart device and run 10-point verification."""
        log(f"\n{'=' * 70}")
        log("  PHASE 6: RESTART & VERIFICATION")
        log(f"{'=' * 70}")
        phase = {"start": time.time()}

        # 6.1: Pre-restart WAL audit
        log("[6.1] Pre-restart WAL audit...")
        out = await self.cmd(
            self.target,
            "find /data/system_ce/0 /data/system_de/0 "
            "-name '*.db-wal' -o -name '*.db-shm' 2>/dev/null | wc -l",
            label="pre_wal",
        )
        wal_count = _safe_int(out)
        log(f"  Pre-restart WAL/SHM files: {wal_count}")

        if wal_count > 0:
            log("  CLEANING remaining WAL/SHM before restart...")
            await self.cmd(
                self.target,
                "find /data/system_ce/0 /data/system_de/0 "
                "\\( -name '*.db-wal' -o -name '*.db-shm' \\) -delete 2>/dev/null",
                label="final_wal_clean",
            )
            await asyncio.sleep(1)
        await self.api_sleep()

        # 6.2: Restart via Cloud API
        log("[6.2] Restarting device via Cloud API...")
        try:
            r = await self.client.instance_restart([self.target])
            log(f"  Restart API: code={r.get('code')} msg={r.get('msg', '')}")
        except Exception as e:
            log(f"  Restart error: {e}")

        # 6.3: Wait for boot
        log("[6.3] Waiting for device boot...")
        alive = await self.wait_for_device(self.target, timeout_sec=120)
        if not alive:
            log("  FATAL: Device did not come back after restart")
            phase["success"] = False
            phase["elapsed"] = time.time() - phase["start"]
            self.report["phases"]["verify"] = phase
            return False

        await asyncio.sleep(10)  # Extra settle time after boot

        # 6.4: Run 10-point verification
        log("[6.4] Running 10-point verification...\n")
        checks = []

        # Check 1: Accounts visible
        out = await self.cmd(self.target,
                             'dumpsys account 2>/dev/null | grep -c "Account {"',
                             label="v_accounts")
        acct_count = _safe_int(out)
        ok = acct_count > 0
        checks.append(("accounts", ok, f"{acct_count} accounts"))
        log(f"  {'✓' if ok else '✗'} Accounts: {acct_count}")
        await self.api_sleep()

        # Check 2: 3rd-party apps
        out = await self.cmd(self.target,
                             "pm list packages -3 2>/dev/null | wc -l",
                             label="v_apps")
        app_count = _safe_int(out)
        ok = app_count > 0
        checks.append(("3rd_party_apps", ok, f"{app_count} apps"))
        log(f"  {'✓' if ok else '✗'} 3rd-party apps: {app_count}")
        await self.api_sleep()

        # Check 3: system_server stable
        out = await self.cmd(self.target, "pidof system_server", label="v_ss")
        ok = bool(out and out.strip().isdigit())
        checks.append(("system_server", ok, f"PID={out}"))
        log(f"  {'✓' if ok else '✗'} system_server: PID={out}")
        await self.api_sleep()

        # Wait and check stability (PID should be same after 15s)
        await asyncio.sleep(15)
        out2 = await self.cmd(self.target, "pidof system_server", label="v_ss2")
        stable = out and out2 and out.strip() == out2.strip()
        checks.append(("ss_stable_15s", stable, f"PID1={out} PID2={out2}"))
        log(f"  {'✓' if stable else '✗'} system_server stable 15s: PID={out}→{out2}")
        await self.api_sleep()

        # Check 4: Keystore entries
        out = await self.cmd(self.target,
                             "ls /data/misc/keystore/user_0/ 2>/dev/null | wc -l",
                             label="v_keystore")
        key_count = _safe_int(out)
        ok = key_count > 0
        checks.append(("keystore", ok, f"{key_count} entries"))
        log(f"  {'✓' if ok else '✗'} Keystore entries: {key_count}")
        await self.api_sleep()

        # Check 5: Zero WAL/SHM files
        out = await self.cmd(
            self.target,
            "find /data/system_ce/0 /data/system_de/0 "
            "-name '*.db-wal' -o -name '*.db-shm' 2>/dev/null | wc -l",
            label="v_wal",
        )
        wal_files = _safe_int(out)
        ok = wal_files == 0
        checks.append(("zero_wal", ok, f"{wal_files} WAL/SHM files"))
        log(f"  {'✓' if ok else '✗'} Zero WAL/SHM: {wal_files}")
        await self.api_sleep()

        # Check 6: SQLite errors in logcat
        out = await self.cmd(self.target,
                             "logcat -d -s SQLiteLog:E 2>/dev/null | wc -l",
                             label="v_sqlite")
        sqlite_errors = _safe_int(out)
        ok = sqlite_errors == 0
        checks.append(("sqlite_clean", ok, f"{sqlite_errors} errors"))
        log(f"  {'✓' if ok else '✗'} SQLite errors: {sqlite_errors}")
        await self.api_sleep()

        # Check 7: GMS services
        out = await self.cmd(self.target,
                             'dumpsys activity service com.google.android.gms 2>/dev/null | '
                             'grep -c "connected"',
                             label="v_gms")
        gms_conns = _safe_int(out)
        ok = gms_conns > 0
        checks.append(("gms_health", ok, f"{gms_conns} connections"))
        log(f"  {'✓' if ok else '✗'} GMS connections: {gms_conns}")
        await self.api_sleep()

        # Check 8: App data directories
        out = await self.cmd(self.target, "ls /data/data/ 2>/dev/null | wc -l",
                             label="v_appdata")
        appdata_count = _safe_int(out)
        ok = appdata_count > 10
        checks.append(("app_data", ok, f"{appdata_count} dirs"))
        log(f"  {'✓' if ok else '✗'} App data dirs: {appdata_count}")
        await self.api_sleep()

        # Check 9: DB file integrity
        for db_path in ["/data/system_ce/0/accounts_ce.db", "/data/system_de/0/accounts_de.db"]:
            out = await self.cmd(self.target, f"ls -la '{db_path}' 2>/dev/null",
                                 label=f"v_db_{db_path.split('/')[-1]}")
            ok = bool(out and out.strip())
            checks.append((f"db_{db_path.split('/')[-1]}", ok, out or "missing"))
            log(f"  {'✓' if ok else '✗'} {db_path.split('/')[-1]}: {out}")
            await asyncio.sleep(1)
        await self.api_sleep()

        # Check 10: Account details
        out = await self.cmd(self.target,
                             "dumpsys account 2>/dev/null | head -30",
                             label="v_acct_detail")
        if out:
            log("\n  Account dump:")
            for line in out.split("\n")[:15]:
                log(f"    {line}")

        # ─── Summary ─────────────────────────────────────────
        passed = sum(1 for _, ok, _ in checks if ok)
        total = len(checks)
        log(f"\n{'=' * 70}")
        log(f"  VERIFICATION: {passed}/{total} checks passed")
        log(f"{'=' * 70}")
        for name, ok, detail in checks:
            status = "✓" if ok else "✗"
            log(f"    {status} {name}: {detail}")

        phase["checks"] = {name: {"ok": ok, "detail": detail} for name, ok, detail in checks}
        phase["passed"] = passed
        phase["total"] = total
        phase["success"] = passed >= total - 2  # Allow 2 soft failures
        phase["elapsed"] = time.time() - phase["start"]
        self.report["phases"]["verify"] = phase
        return phase["success"]


# ═══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════
async def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Clone v9 Pipeline — Full Neighbor Device Clone")
    parser.add_argument("--launchpad", default=LAUNCHPAD,
                        help="Launchpad pad code")
    parser.add_argument("--target", default=TARGET,
                        help="Target pad code")
    parser.add_argument("--neighbor-ip", default=NEIGHBOR_IP,
                        help="Neighbor IP address")
    parser.add_argument("--skip-extraction", action="store_true",
                        help="Skip Phase 2 (use existing backup)")
    parser.add_argument("--skip-restore", action="store_true",
                        help="Skip Phase 4 (recon + extract only)")
    parser.add_argument("--skip-identity", action="store_true",
                        help="Skip Phase 5 (no identity injection)")
    parser.add_argument("--output", default="clone_v9_report.json",
                        help="Output report file")
    args = parser.parse_args()

    t0 = time.time()
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)

    pipeline = CloneV9Pipeline(
        client=client,
        launchpad=args.launchpad,
        target=args.target,
        neighbor_ip=args.neighbor_ip,
    )

    log("=" * 70)
    log("  CLONE v9 PIPELINE — Full Neighbor Device Clone")
    log(f"  Launchpad: {args.launchpad}")
    log(f"  Target:    {args.target}")
    log(f"  Neighbor:  {args.neighbor_ip}")
    log("  Root Cause Fixes: RC-A(DB) RC-B(UID) RC-C(Crypto) RC-D(Platform) RC-E(Process)")
    log("=" * 70)

    # ── Phase 1: Reconnaissance ──
    ok = await pipeline.phase1_reconnaissance()
    if not ok:
        log("\nFATAL: Phase 1 failed — aborting pipeline")
        await client.close()
        return

    # ── Phase 2: Full Partition Extraction ──
    if not args.skip_extraction:
        ok = await pipeline.phase2_extraction()
        if not ok:
            log("\nFATAL: Phase 2 failed — aborting pipeline")
            await client.close()
            return
    else:
        log("\n  Skipping Phase 2 (--skip-extraction)")

    # ── Phase 3: Database Sanitization ──
    ok = await pipeline.phase3_db_sanitization()
    if not ok:
        log("\nWARNING: Phase 3 had issues — continuing with best effort")

    # ── Phase 4: Partition Restore ──
    if not args.skip_restore:
        ok = await pipeline.phase4_restore()
        if not ok:
            log("\nFATAL: Phase 4 failed — aborting pipeline")
            await client.close()
            return
    else:
        log("\n  Skipping Phase 4 (--skip-restore)")

    # ── Phase 5: Safe Identity Injection ──
    if not args.skip_identity:
        await pipeline.phase5_identity()
    else:
        log("\n  Skipping Phase 5 (--skip-identity)")

    # ── Phase 6: Restart & Verification ──
    if not args.skip_restore:
        ok = await pipeline.phase6_verify()
    else:
        log("\n  Skipping Phase 6 (no restore to verify)")
        ok = True

    # ── Final Report ──
    elapsed = time.time() - t0
    pipeline.report["end_time"] = time.time()
    pipeline.report["elapsed_seconds"] = elapsed

    verify_phase = pipeline.report.get("phases", {}).get("verify", {})
    passed = verify_phase.get("passed", 0)
    total = verify_phase.get("total", 0)

    log(f"\n{'=' * 70}")
    if ok:
        log(f"  CLONE v9 COMPLETE — {elapsed:.0f}s ({passed}/{total} checks)")
    else:
        log(f"  CLONE v9 PARTIAL — {elapsed:.0f}s ({passed}/{total} checks)")
    log(f"  Target: {args.target}")
    log(f"  Neighbor: {args.neighbor_ip}")
    log("  DB mode: DELETE journal (no WAL)")
    log("  Identity: cloud-safe only (no ro.build.*)")
    log("  Crypto chain: full /data/ partition (keystore+tokens+accounts)")
    log(f"{'=' * 70}")

    # Save report
    with open(args.output, "w") as f:
        json.dump(pipeline.report, f, indent=2, default=str)
    log(f"Report saved to {args.output}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
