#!/usr/bin/env python3
"""
Clone Restore v2.0 — Restore cloned neighbor data to our device
================================================================
Restores system data (accounts, GMS, GSF) and app data (WhatsApp,
Google Wallet, etc.) from a clone backup into our device.

APKs are pulled directly from the neighbor device via ADB relay,
then installed on our device. App data is restored from the clone backup
served over HTTP from VPS.

Identity is NEVER modified — only data/accounts/apps are restored.

Usage:
    python3 tools/clone_restore.py <clone_dir> [--neighbor-ip IP]
    
Example:
    python3 tools/clone_restore.py clone_backups/10_0_46_2_Infinix_X6531B
"""

import asyncio
import base64
import json
import os
import struct
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ─── Config ──────────────────────────────────────────────────────────
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
PAD = "AC32010810392"
API_URL = "https://api.vmoscloud.com"
OUR_IP = "10.0.21.62"
VPS_IP = "51.68.33.34"
SERVE_PORT = 18999
D = 3.5  # API rate delay

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots" / "clone_verify"

# App activities for launching/verifying
APP_ACTIVITIES = {
    "com.whatsapp": "com.whatsapp/.Main",
    "com.whatsapp.w4b": "com.whatsapp.w4b/.Main",
    "org.telegram.messenger": "org.telegram.messenger/.DefaultIcon",
    "com.google.android.apps.walletnfcrel": "com.google.android.apps.walletnfcrel/.home.HomeActivity",
    "com.instagram.android": "com.instagram.android/.activity.MainTabActivity",
    "com.instagram.barcelona": "com.instagram.barcelona/.activity.MainTabActivity",
    "com.bank.vr": "com.bank.vr/.ui.LauncherActivity",
    "com.airbnb.android": "com.airbnb.android/.activities.HomeActivity",
    "com.glovo": "com.glovo/.features.main.MainActivity",
}


# ─── ADB Wire Protocol (from device_cloner.py) ──────────────────────

def _le32(v): return struct.pack("<I", v)
def _adb_msg(cmd_id, arg0, arg1, payload=b""):
    hdr = struct.pack("<IIII", cmd_id, arg0, arg1, len(payload))
    ck = sum(payload) & 0xFFFFFFFF
    magic = cmd_id ^ 0xFFFFFFFF
    hdr += struct.pack("<II", ck, magic)
    return hdr + payload

def build_adb_cnxn():
    return _adb_msg(0x4e584e43, 0x01000001, 4096, b"host::\x00")

def build_adb_open(local_id, destination):
    return _adb_msg(0x4e45504f, local_id, 0, destination.encode() + b"\x00")


# ─── Bridge (proven API + ADB relay wrapper) ─────────────────────────

class RestoreBridge:
    def __init__(self):
        self.client = VMOSCloudClient(ak=AK, sk=SK, base_url=API_URL)
        self._last_cmd = 0.0
        self._cmd_count = 0
        self._cnxn_staged = {}

    async def _throttle(self):
        elapsed = time.time() - self._last_cmd
        if elapsed < D:
            await asyncio.sleep(D - elapsed)

    async def cmd(self, command, timeout=30):
        """Execute shell on our device, return stdout."""
        await self._throttle()
        self._last_cmd = time.time()
        self._cmd_count += 1
        try:
            r = await asyncio.wait_for(
                self.client.sync_cmd(PAD, command, timeout_sec=timeout),
                timeout=timeout + 15,
            )
            data = r.get("data", [])
            if isinstance(data, list) and data:
                return (data[0].get("errorMsg", "") or "").strip()
            elif isinstance(data, dict):
                return (data.get("errorMsg", "") or "").strip()
            return ""
        except asyncio.TimeoutError:
            return "ERR:timeout"
        except Exception as e:
            return f"ERR:{e}"

    async def fire(self, command):
        """Fire async command (no output wait)."""
        await self._throttle()
        self._last_cmd = time.time()
        self._cmd_count += 1
        try:
            await self.client.async_adb_cmd([PAD], command)
        except Exception:
            pass

    async def _ensure_cnxn(self, ip):
        key = ip.replace(".", "_")
        if key not in self._cnxn_staged:
            b64 = base64.b64encode(build_adb_cnxn()).decode()
            await self.cmd(f"echo -n '{b64}' | base64 -d > /sdcard/.cnxn_{key}")
            self._cnxn_staged[key] = True

    async def neighbor_cmd(self, ip, shell_cmd, timeout=8):
        """Execute shell command on neighbor via ADB relay."""
        ip_key = ip.replace(".", "_")
        tag = f"{hash(shell_cmd) & 0xFFFF:04x}"

        await self._ensure_cnxn(ip)

        open_pkt = build_adb_open(1, f"shell:{shell_cmd}")
        b64_open = base64.b64encode(open_pkt).decode()
        await self.cmd(f"echo -n '{b64_open}' | base64 -d > /sdcard/.o{tag}")

        relay_cmd = (
            f"(cat /sdcard/.cnxn_{ip_key}; sleep 0.3; cat /sdcard/.o{tag}; sleep {timeout}) | "
            f"timeout {timeout + 2} nc {ip} 5555 > /sdcard/.r{tag} 2>/dev/null"
        )
        await self.fire(relay_cmd)
        await asyncio.sleep(timeout + 4)

        info = await self.cmd(
            f"strings -n 3 /sdcard/.r{tag} | "
            f"grep -v -E '^(CNXN|OKAY|WRTE|CLSE|OPEN)' | "
            f"grep -v -e '^host::' -e '^device::' "
            f"> /sdcard/.t{tag} 2>/dev/null; "
            f"echo TOTAL:$(wc -l < /sdcard/.t{tag} 2>/dev/null)"
        )

        total_lines = 0
        for line in (info or "").split("\n"):
            if line.startswith("TOTAL:"):
                try: total_lines = int(line.split(":")[1].strip())
                except (ValueError, IndexError): pass

        if total_lines == 0:
            await self.cmd(f"rm -f /sdcard/.o{tag} /sdcard/.r{tag} /sdcard/.t{tag}")
            return ""

        CHUNK = 30
        chunks = []
        for start in range(0, total_lines, CHUNK):
            if start == 0:
                chunk = await self.cmd(f"head -{CHUNK} /sdcard/.t{tag}")
            else:
                chunk = await self.cmd(f"tail -n +{start + 1} /sdcard/.t{tag} | head -{CHUNK}")
            if chunk:
                chunks.append(chunk)

        await self.cmd(f"rm -f /sdcard/.o{tag} /sdcard/.r{tag} /sdcard/.t{tag}")
        return "\n".join(chunks).strip()

    async def pull_from_neighbor(self, ip, remote_path, device_dest, timeout=90):
        """Pull file from neighbor → our device via nc relay. Returns bytes received."""
        port = 19870 + (hash(remote_path) & 0xFF)
        ip_key = ip.replace(".", "_")

        await self.cmd(f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f {device_dest} /sdcard/.xfer_open")
        await self._ensure_cnxn(ip)

        shell_cmd = f"cat {remote_path} | nc -w 10 {OUR_IP} {port}"
        open_pkt = build_adb_open(1, f"shell:{shell_cmd}")
        b64_open = base64.b64encode(open_pkt).decode()
        await self.cmd(f"echo -n '{b64_open}' | base64 -d > /sdcard/.xfer_open")

        await self.fire(f"nc -l -p {port} > {device_dest}")
        await asyncio.sleep(2)

        relay_cmd = (
            f"(cat /sdcard/.cnxn_{ip_key}; sleep 0.3; cat /sdcard/.xfer_open; "
            f"sleep {timeout}) | "
            f"timeout {timeout + 5} nc {ip} 5555 > /dev/null 2>&1"
        )
        await self.fire(relay_cmd)

        # FIXED WAIT during transfer — NO syncCmd
        await asyncio.sleep(timeout + 5)

        size_str = await self.cmd(f"wc -c < {device_dest} 2>/dev/null || echo 0")
        try: size = int(size_str.strip())
        except ValueError: size = 0

        await self.cmd(f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /sdcard/.xfer_open")
        return size

    async def screenshot(self):
        """Take screenshot via API, return task result."""
        await self._throttle()
        self._last_cmd = time.time()
        self._cmd_count += 1
        r = await self.client.screenshot([PAD])
        return r

    async def get_screenshot_url(self):
        """Get preview image URL."""
        await self._throttle()
        self._last_cmd = time.time()
        self._cmd_count += 1
        r = await self.client.get_preview_image([PAD])
        return r


# ─── HTTP Server ─────────────────────────────────────────────────────

def start_http_server(serve_dir):
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        if s.connect_ex(("0.0.0.0", SERVE_PORT)) == 0:
            os.system(f"fuser -k {SERVE_PORT}/tcp 2>/dev/null")
            time.sleep(1)
        s.close()
    except Exception:
        pass

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(serve_dir), **kw)
        def log_message(self, fmt, *args):
            pass

    from socketserver import TCPServer
    class ReuseTCPServer(TCPServer):
        allow_reuse_address = True

    server = ReuseTCPServer(("0.0.0.0", SERVE_PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"    HTTP server on :{SERVE_PORT}")
    return server


# ═══════════════════════════════════════════════════════════════════
#  PHASE 1: System Data Restore (accounts, GMS, GSF)
# ═══════════════════════════════════════════════════════════════════

async def restore_system_data(bridge: RestoreBridge, clone_dir: Path, serve_dir: Path):
    """Restore accounts_ce.db, GMS prefs/databases, GSF databases."""
    print("\n  ┌─────────────────────────────────────┐")
    print("  │  PHASE 1: SYSTEM DATA RESTORE       │")
    print("  └─────────────────────────────────────┘")

    sysdata_tar = clone_dir / "sysdata.tar.gz"
    if not sysdata_tar.exists():
        print("    ✗ No sysdata.tar.gz — skipping system restore")
        return False

    # Copy to serve dir
    shutil.copy2(str(sysdata_tar), str(serve_dir / "sysdata.tar.gz"))
    url = f"http://{VPS_IP}:{SERVE_PORT}/sysdata.tar.gz"
    expected = sysdata_tar.stat().st_size
    print(f"    sysdata.tar.gz: {expected/1024:.0f}KB → serving at {url}")

    # Download to device (1.8MB — fire curl, wait 30s)
    print("    Downloading to device (fire + 30s wait)...")
    await bridge.fire(f"nohup curl -s -o /data/local/tmp/sysdata.tar.gz {url} > /dev/null 2>&1 &")
    await asyncio.sleep(30)  # fixed wait for 1.8MB

    sz_str = await bridge.cmd("stat -c %s /data/local/tmp/sysdata.tar.gz 2>/dev/null || echo 0")
    try:
        sz = int(sz_str.strip())
    except (ValueError, IndexError):
        sz = 0

    if sz < expected - 500:
        # Give it more time
        print(f"    Still downloading ({sz}/{expected})... waiting 30s more")
        await asyncio.sleep(30)
        sz_str = await bridge.cmd("stat -c %s /data/local/tmp/sysdata.tar.gz 2>/dev/null || echo 0")
        try: sz = int(sz_str.strip())
        except ValueError: sz = 0

    if sz < expected - 500:
        print(f"    ✗ Download incomplete ({sz}/{expected})")
        return False

    print(f"    ✓ Downloaded ({sz/1024:.0f}KB)")

    # Extract (fire + fixed wait for ~1.8MB compressed)
    await bridge.fire("nohup tar xzf /data/local/tmp/sysdata.tar.gz -C /data/local/tmp/ > /dev/null 2>&1 &")
    print("    Extracting (waiting 15s)...")
    await asyncio.sleep(15)
    out = await bridge.cmd("ls /data/local/tmp/data/data/ 2>/dev/null | head -5 && echo DONE")
    print(f"    Extracted: {out[:100]}")

    # Force-stop GMS/GSF before restore
    await bridge.cmd("am force-stop com.google.android.gms; am force-stop com.google.android.gsf")

    # Restore GMS shared_prefs + databases
    gms_cmd = (
        "SRC=/data/local/tmp/data/data/com.google.android.gms; "
        "DST=/data/data/com.google.android.gms; "
        "GMS_UID=$(dumpsys package com.google.android.gms 2>/dev/null | grep 'userId=' | head -1 | sed 's/.*userId=//;s/ .*//'); "
        "P=0; D=0; "
        "mkdir -p $DST/shared_prefs $DST/databases 2>/dev/null; "
        "[ -d $SRC/shared_prefs ] && cp -f $SRC/shared_prefs/* $DST/shared_prefs/ 2>/dev/null && P=$(ls $SRC/shared_prefs/ 2>/dev/null | wc -l); "
        "[ -d $SRC/databases ] && cp -f $SRC/databases/* $DST/databases/ 2>/dev/null && D=$(ls $SRC/databases/ 2>/dev/null | wc -l); "
        "[ -n \"$GMS_UID\" ] && chown -R $GMS_UID:$GMS_UID $DST/ 2>/dev/null; "
        "echo GMS_OK prefs=$P dbs=$D uid=$GMS_UID"
    )
    out = await bridge.cmd(gms_cmd, timeout=30)
    print(f"    GMS: {out}")

    # Restore GSF databases + prefs
    gsf_cmd = (
        "am force-stop com.google.android.gsf 2>/dev/null; "
        "SRC=/data/local/tmp/data/data/com.google.android.gsf; "
        "DST=/data/data/com.google.android.gsf; "
        "GSF_UID=$(dumpsys package com.google.android.gsf 2>/dev/null | grep 'userId=' | head -1 | sed 's/.*userId=//;s/ .*//'); "
        "D=0; "
        "mkdir -p $DST/databases $DST/shared_prefs 2>/dev/null; "
        "[ -d $SRC/databases ] && cp -f $SRC/databases/* $DST/databases/ 2>/dev/null && D=$(ls $SRC/databases/ 2>/dev/null | wc -l); "
        "[ -d $SRC/shared_prefs ] && cp -f $SRC/shared_prefs/* $DST/shared_prefs/ 2>/dev/null; "
        "[ -n \"$GSF_UID\" ] && chown -R $GSF_UID:$GSF_UID $DST/ 2>/dev/null; "
        "echo GSF_OK dbs=$D uid=$GSF_UID"
    )
    out = await bridge.cmd(gsf_cmd, timeout=30)
    print(f"    GSF: {out}")

    # Restore accounts_ce.db
    acct_cmd = (
        "SRC=/data/local/tmp/data/system_ce/0; "
        "DST=/data/system_ce/0; "
        "[ -f $SRC/accounts_ce.db ] && "
        "cp -f $SRC/accounts_ce.db $DST/accounts_ce.db 2>/dev/null && "
        "chown 1000:1000 $DST/accounts_ce.db 2>/dev/null && "
        "chmod 600 $DST/accounts_ce.db 2>/dev/null && "
        "echo ACCT_OK || echo ACCT_NOFILE"
    )
    out = await bridge.cmd(acct_cmd, timeout=15)
    print(f"    Accounts DB: {out}")

    # Broadcast account changes + restart GMS
    await bridge.cmd("am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null; "
                     "am startservice com.google.android.gms/.chimera.GmsIntentOperationService 2>/dev/null")

    # Verify
    await asyncio.sleep(5)
    out = await bridge.cmd('dumpsys account 2>/dev/null | grep "Account {" | head -5')
    print(f"    Accounts after restore: {out if out else '(none visible yet)'}")

    # Cleanup
    await bridge.cmd("rm -rf /data/local/tmp/sysdata.tar.gz /data/local/tmp/data")
    return True


# ═══════════════════════════════════════════════════════════════════
#  PHASE 2: Pull APKs from Neighbor + Install
# ═══════════════════════════════════════════════════════════════════

async def install_apps_from_neighbor(bridge: RestoreBridge, neighbor_ip: str, packages: list):
    """Pull APKs from neighbor and install on our device."""
    print("\n  ┌─────────────────────────────────────┐")
    print("  │  PHASE 2: APK PULL + INSTALL        │")
    print("  └─────────────────────────────────────┘")

    # Check what's already installed
    installed_raw = await bridge.cmd("pm list packages 2>/dev/null")
    installed = {p.replace("package:", "").strip() for p in (installed_raw or "").split("\n") if p.startswith("package:")}

    for pkg in packages:
        if pkg in installed:
            print(f"    ✓ {pkg}: already installed")
            continue

        print(f"\n    [{pkg}] Getting APK path from neighbor...")

        # Get APK path from neighbor
        apk_info = await bridge.neighbor_cmd(neighbor_ip, f"pm path {pkg} 2>/dev/null")
        apk_path = None
        for line in (apk_info or "").split("\n"):
            if line.startswith("package:"):
                p = line.replace("package:", "").strip()
                if p.endswith(".apk"):
                    apk_path = p
                    break

        if not apk_path:
            print(f"    ✗ {pkg}: APK path not found on neighbor")
            continue

        print(f"    APK path: {apk_path}")

        # Get APK size from neighbor
        size_info = await bridge.neighbor_cmd(neighbor_ip, f"stat -c %s {apk_path} 2>/dev/null")
        try:
            apk_size = int(size_info.strip())
        except (ValueError, AttributeError):
            apk_size = 0
        print(f"    APK size: {apk_size/1048576:.1f}MB")

        if apk_size < 10000:
            print(f"    ✗ APK too small or not found")
            continue

        # Calculate transfer timeout (1 MB/s minimum, 90s minimum)
        timeout = max(90, (apk_size // 1048576) * 3 + 60)

        # Pull APK from neighbor → our device
        dest = f"/data/local/tmp/{pkg}.apk"
        print(f"    Pulling APK ({timeout}s timeout)...")
        pulled = await bridge.pull_from_neighbor(neighbor_ip, apk_path, dest, timeout=timeout)

        if pulled < apk_size * 0.9:
            print(f"    ✗ Pull incomplete: {pulled}/{apk_size}")
            # Try shorter path (some split APKs)
            continue

        print(f"    ✓ Pulled {pulled/1048576:.1f}MB")

        # Install
        print(f"    Installing...")
        out = await bridge.cmd(f"pm install -r -d -g {dest} 2>&1", timeout=60)
        if "Success" in (out or ""):
            print(f"    ✓ Installed {pkg}")
        else:
            print(f"    Install result: {out[:200]}")

        # Cleanup APK
        await bridge.cmd(f"rm -f {dest}")

    print(f"\n    APK install phase complete")


# ═══════════════════════════════════════════════════════════════════
#  PHASE 3: App Data Restore
# ═══════════════════════════════════════════════════════════════════

async def restore_app_data(bridge: RestoreBridge, clone_dir: Path, serve_dir: Path):
    """Restore app databases, shared_prefs, files for each cloned app."""
    print("\n  ┌─────────────────────────────────────┐")
    print("  │  PHASE 3: APP DATA RESTORE          │")
    print("  └─────────────────────────────────────┘")

    appdata_tar = clone_dir / "appdata.tar.gz"
    if not appdata_tar.exists():
        print("    ✗ No appdata.tar.gz — skipping")
        return False

    shutil.copy2(str(appdata_tar), str(serve_dir / "appdata.tar.gz"))
    url = f"http://{VPS_IP}:{SERVE_PORT}/appdata.tar.gz"
    expected = appdata_tar.stat().st_size
    print(f"    appdata.tar.gz: {expected/1048576:.1f}MB → serving")

    # Download to device — fire curl, fixed wait, then check
    await bridge.fire(f"nohup curl -s -o /data/local/tmp/appdata.tar.gz {url} > /dev/null 2>&1 &")
    print("    Downloading to device (fixed wait ~120s for 52MB)...")
    await asyncio.sleep(120)  # fixed wait — no polling during download

    sz_str = await bridge.cmd("stat -c %s /data/local/tmp/appdata.tar.gz 2>/dev/null || echo 0")
    try: sz = int(sz_str.strip())
    except ValueError: sz = 0

    if sz < expected * 0.9:
        # Give it more time
        print(f"    Still downloading ({sz}/{expected})... waiting 60s more")
        await asyncio.sleep(60)
        sz_str = await bridge.cmd("stat -c %s /data/local/tmp/appdata.tar.gz 2>/dev/null || echo 0")
        try: sz = int(sz_str.strip())
        except ValueError: sz = 0

    if sz < expected * 0.9:
        print(f"    ✗ Download incomplete ({sz}/{expected})")
        return False

    print(f"    ✓ Downloaded ({sz/1048576:.1f}MB)")

    # Extract
    await bridge.fire("nohup tar xzf /data/local/tmp/appdata.tar.gz -C /data/local/tmp/ > /dev/null 2>&1 &")
    # Wait for extraction (52MB compressed)
    print("    Extracting...")
    await asyncio.sleep(25)
    out = await bridge.cmd("ls /data/local/tmp/data/data/ 2>/dev/null")
    print(f"    Extracted: {out}")

    apps_dir = clone_dir / "apps" / "data" / "data"
    cloned_apps = [d.name for d in apps_dir.iterdir() if d.is_dir()] if apps_dir.exists() else []

    for pkg in cloned_apps:
        # Force stop app
        await bridge.cmd(f"am force-stop {pkg} 2>/dev/null")

        # Check app is installed (data restore only works if app exists)
        check = await bridge.cmd(f"pm path {pkg} 2>/dev/null")
        if "package:" not in (check or ""):
            print(f"    ⚠ {pkg}: NOT installed — skipping data restore")
            continue

        src = f"/data/local/tmp/data/data/{pkg}"
        dst = f"/data/data/{pkg}"

        restore_cmd = (
            f"[ -d {src} ] || {{ echo NOSRC; exit 0; }}; "
            f"mkdir -p {dst}/shared_prefs {dst}/databases {dst}/files {dst}/no_backup 2>/dev/null; "
            f"P=0; D=0; F=0; "
            f"[ -d {src}/shared_prefs ] && cp -f {src}/shared_prefs/* {dst}/shared_prefs/ 2>/dev/null && P=$(ls {src}/shared_prefs/ 2>/dev/null | wc -l); "
            f"[ -d {src}/databases ] && cp -f {src}/databases/* {dst}/databases/ 2>/dev/null && D=$(ls {src}/databases/ 2>/dev/null | wc -l); "
            f"[ -d {src}/files ] && cp -a {src}/files/* {dst}/files/ 2>/dev/null && F=$(ls {src}/files/ 2>/dev/null | wc -l); "
            f"[ -d {src}/no_backup ] && cp -a {src}/no_backup/* {dst}/no_backup/ 2>/dev/null; "
            f"PKG_UID=$(dumpsys package {pkg} 2>/dev/null | grep userId= | head -1 | sed 's/.*userId=//;s/ .*//'); "
            f"[ -n \"$PKG_UID\" ] && chown -R $PKG_UID:$PKG_UID {dst}/ 2>/dev/null; "
            f"echo OK:{pkg} prefs=$P dbs=$D files=$F uid=$PKG_UID"
        )
        out = await bridge.cmd(restore_cmd, timeout=30)
        if "OK:" in (out or ""):
            print(f"    ✓ {out}")
        elif "NOSRC" in (out or ""):
            print(f"    ⚠ {pkg}: no source data on device")
        else:
            print(f"    ✗ {pkg}: {out[:150]}")

    # Cleanup
    await bridge.cmd("rm -rf /data/local/tmp/appdata.tar.gz /data/local/tmp/data")
    return True


# ═══════════════════════════════════════════════════════════════════
#  PHASE 4: Screenshot Verification
# ═══════════════════════════════════════════════════════════════════

async def verify_with_screenshots(bridge: RestoreBridge, clone_dir: Path):
    """Launch each restored app and take screenshots to verify."""
    print("\n  ┌─────────────────────────────────────┐")
    print("  │  PHASE 4: SCREENSHOT VERIFICATION   │")
    print("  └─────────────────────────────────────┘")

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    verify_dir = SCREENSHOTS_DIR / ts
    verify_dir.mkdir(parents=True, exist_ok=True)

    # Load identity for list of apps
    identity_file = clone_dir / "identity.json"
    hv_apps = []
    if identity_file.exists():
        meta = json.load(open(identity_file))
        hv_apps = meta.get("high_value_apps", [])

    # Check installed
    installed_raw = await bridge.cmd("pm list packages 2>/dev/null")
    installed = {p.replace("package:", "").strip() for p in (installed_raw or "").split("\n") if p.startswith("package:")}

    apps_to_check = [pkg for pkg in hv_apps if pkg in installed]
    # Also add wallet if available
    if "com.google.android.apps.walletnfcrel" in installed and "com.google.android.apps.walletnfcrel" not in apps_to_check:
        apps_to_check.append("com.google.android.apps.walletnfcrel")

    print(f"    Verifying {len(apps_to_check)} apps...")
    screenshots = []

    # Home screen
    await bridge.cmd("input keyevent KEYCODE_HOME")
    await asyncio.sleep(3)
    sc = await _take_and_save(bridge, verify_dir, "00_home")
    if sc: screenshots.append(sc)

    for i, pkg in enumerate(apps_to_check):
        label = pkg.split(".")[-1][:12]
        print(f"\n    [{i+1}/{len(apps_to_check)}] {pkg}")

        await bridge.cmd(f"am force-stop {pkg} 2>/dev/null")

        activity = APP_ACTIVITIES.get(pkg)
        if activity:
            await bridge.cmd(f"am start -n {activity} 2>/dev/null")
        else:
            await bridge.cmd(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1 2>/dev/null")

        await asyncio.sleep(8)

        sc = await _take_and_save(bridge, verify_dir, f"{i+1:02d}_{label}_main")
        if sc: screenshots.append(sc)

        # For Wallet: scroll and take more shots
        if "walletnfcrel" in pkg:
            await asyncio.sleep(3)
            sc2 = await _take_and_save(bridge, verify_dir, f"{i+1:02d}_{label}_loaded")
            if sc2: screenshots.append(sc2)
            await bridge.cmd("input swipe 540 1500 540 500 500")
            await asyncio.sleep(3)
            sc3 = await _take_and_save(bridge, verify_dir, f"{i+1:02d}_{label}_scrolled")
            if sc3: screenshots.append(sc3)

        # For WhatsApp: wait for loading
        if "whatsapp" in pkg:
            await asyncio.sleep(5)
            sc2 = await _take_and_save(bridge, verify_dir, f"{i+1:02d}_{label}_loaded")
            if sc2: screenshots.append(sc2)

        await bridge.cmd("input keyevent KEYCODE_HOME")
        await asyncio.sleep(2)

    # Additional Wallet analysis
    print("\n    [wallet-check] Analyzing Google Pay data...")
    wallet_info = await bridge.cmd(
        "echo '===WALLET_DB===' && "
        "ls -la /data/data/com.google.android.apps.walletnfcrel/databases/ 2>/dev/null && "
        "echo '===WALLET_PREFS===' && "
        "ls /data/data/com.google.android.apps.walletnfcrel/shared_prefs/ 2>/dev/null && "
        "echo '===GMS_WALLET_DB===' && "
        "ls /data/data/com.google.android.gms/databases/ 2>/dev/null | grep -i -E 'wallet|pay|tap' && "
        "echo '===ACCTS===' && "
        "dumpsys account 2>/dev/null | grep -E 'Account \\{' | head -5"
    )
    print(f"    {wallet_info[:600]}")

    # Summary
    print(f"\n  ┌─────────────────────────────────────┐")
    print(f"  │  VERIFICATION COMPLETE               │")
    print(f"  └─────────────────────────────────────┘")
    print(f"    Screenshots: {len(screenshots)} saved to {verify_dir}/")
    for sc in screenshots:
        print(f"      • {sc}")

    report = {
        "timestamp": datetime.now().isoformat(),
        "clone_source": str(clone_dir),
        "apps_verified": apps_to_check,
        "screenshots": screenshots,
        "wallet_info": wallet_info[:500] if wallet_info else "",
    }
    report_path = verify_dir / "verification_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"    Report: {report_path}")

    return screenshots


async def _take_and_save(bridge: RestoreBridge, output_dir: Path, name: str):
    """Take screenshot on device, pull via base64, save locally."""
    device_path = f"/sdcard/{name}.png"
    await bridge.cmd(f"screencap -p {device_path}")

    sz_str = await bridge.cmd(f"stat -c %s {device_path} 2>/dev/null || echo 0")
    try: sz = int(sz_str.strip())
    except ValueError: sz = 0

    if sz < 1000:
        print(f"      ✗ screencap failed: {name}")
        return None

    # For faster pull: use gzip + base64 (compress 500KB PNG → ~50KB gzip)
    await bridge.cmd(f"gzip -c {device_path} > {device_path}.gz")
    gz_str = await bridge.cmd(f"stat -c %s {device_path}.gz 2>/dev/null || echo 0")
    try: gz_sz = int(gz_str.strip())
    except ValueError: gz_sz = 0

    target = f"{device_path}.gz" if gz_sz > 100 else device_path
    target_sz = gz_sz if gz_sz > 100 else sz
    is_gzipped = gz_sz > 100

    # Pull via chunked base64
    CHUNK = 1350  # raw bytes per chunk → ~1800 base64 chars → fits 2000 limit
    parts = []
    offset = 0

    while offset < target_sz:
        remaining = target_sz - offset
        read_size = min(CHUNK, remaining)
        b64 = await bridge.cmd(
            f"dd if={target} bs=1 skip={offset} count={read_size} 2>/dev/null | base64 | tr -d '\\n'"
        )
        if not b64 or b64.startswith("ERR"):
            break
        parts.append(b64)
        offset += read_size

    # Assemble
    import base64 as b64mod
    import gzip as gzmod
    raw = b""
    for p in parts:
        try:
            padded = p + "=" * (-len(p) % 4)
            raw += b64mod.b64decode(padded)
        except Exception:
            pass

    if is_gzipped and raw:
        try:
            raw = gzmod.decompress(raw)
        except Exception:
            pass

    local_path = output_dir / f"{name}.png"
    if raw and len(raw) > 1000:
        with open(local_path, "wb") as f:
            f.write(raw)
        print(f"      ✓ {name}.png ({len(raw)/1024:.0f}KB)")
        # Cleanup device
        await bridge.cmd(f"rm -f {device_path} {device_path}.gz")
        return f"{name}.png"
    else:
        print(f"      ✗ Pull failed: {name}")
        await bridge.cmd(f"rm -f {device_path} {device_path}.gz")
        return None


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    clone_path = Path(sys.argv[1])
    if not clone_path.is_absolute():
        clone_path = BASE_DIR / clone_path

    # Parse --neighbor-ip option
    neighbor_ip = None
    for i, arg in enumerate(sys.argv):
        if arg == "--neighbor-ip" and i + 1 < len(sys.argv):
            neighbor_ip = sys.argv[i + 1]

    # Auto-detect neighbor IP from clone dir name
    if not neighbor_ip:
        dir_name = clone_path.name
        parts = dir_name.split("_")
        if len(parts) >= 4 and all(p.isdigit() for p in parts[:4]):
            neighbor_ip = ".".join(parts[:4])

    if not clone_path.exists():
        print(f"  ✗ Clone directory not found: {clone_path}")
        return

    # Load identity
    identity_file = clone_path / "identity.json"
    if identity_file.exists():
        meta = json.load(open(identity_file))
        model = meta.get("identity", {}).get("model", "?")
        brand = meta.get("identity", {}).get("brand", "?")
        accts = meta.get("accounts", [])
        hv = meta.get("high_value_apps", [])
        print(f"\n  Clone source: {brand} {model} ({neighbor_ip})")
        print(f"  Account: {accts}")
        print(f"  High-value apps: {len(hv)}")
    else:
        hv = []

    print(f"\n  ═══════════════════════════════════════")
    print(f"  CLONE RESTORE — Identity untouched")
    print(f"  ═══════════════════════════════════════")

    bridge = RestoreBridge()

    # Setup HTTP serve directory
    serve_dir = BASE_DIR / "tmp" / "clone_serve"
    serve_dir.mkdir(parents=True, exist_ok=True)
    server = start_http_server(serve_dir)

    try:
        # Phase 1: System data
        await restore_system_data(bridge, clone_path, serve_dir)

        # Phase 2: APK install from neighbor
        apps_dir = clone_path / "apps" / "data" / "data"
        cloned_pkgs = [d.name for d in apps_dir.iterdir() if d.is_dir()] if apps_dir.exists() else []
        if neighbor_ip and cloned_pkgs:
            await install_apps_from_neighbor(bridge, neighbor_ip, cloned_pkgs)
        else:
            print("\n  ⚠ No neighbor IP — skipping APK install from neighbor")

        # Phase 3: App data restore
        await restore_app_data(bridge, clone_path, serve_dir)

        # Phase 4: Screenshots
        await verify_with_screenshots(bridge, clone_path)

    finally:
        server.shutdown()
        # Cleanup serve dir
        shutil.rmtree(str(serve_dir), ignore_errors=True)

    print(f"\n  Total API calls: {bridge._cmd_count}")
    print(f"  Done.")


if __name__ == "__main__":
    asyncio.run(main())
