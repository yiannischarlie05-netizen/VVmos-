#!/usr/bin/env python3
"""
Clone Restore & Verify — Push cloned data to our device + screenshot verification.

Restores app data from clone_backups/ into our device WITHOUT touching device identity.
Then launches each app and takes screenshots to verify login state.

Usage:
    python3 tools/clone_restore_verify.py restore <clone_dir>    # Restore data
    python3 tools/clone_restore_verify.py verify <clone_dir>     # Screenshot verify
    python3 tools/clone_restore_verify.py full <clone_dir>       # Restore + verify
"""

import asyncio
import json
import os
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ─── Config ──────────────────────────────────────────────────────────
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
PAD = "AC32010810392"
API = "https://api.vmoscloud.com"
VPS_IP = "YOUR_OLLAMA_HOST"
SERVE_PORT = 18999
D = 3.5  # rate delay

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots" / "clone_verify"

# Apps that need APK install (not pre-installed on device)
INSTALL_URLS = {
    "com.whatsapp": "https://scontent.whatsapp.net/v/t61.25985-34/468578037_1321167802199498_1459539500771498587_n.apk/WhatsApp.apk?ccb=1",
    "com.whatsapp.w4b": None,  # Will need to find URL or use API upload
    "org.telegram.messenger": "https://telegram.org/dl/android/apk",
}

# App launch activities
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

# ─── Helpers ─────────────────────────────────────────────────────────

async def cmd(client, shell_cmd, timeout_sec=30):
    try:
        r = await client.sync_cmd(PAD, shell_cmd, timeout_sec=timeout_sec)
        if not r or not isinstance(r, dict):
            return ""
        data = r.get("data", [])
        if data and isinstance(data, list) and len(data) > 0:
            return (data[0].get("errorMsg", "") or "").strip()
        return ""
    except Exception as e:
        return f"ERR:{e}"


async def fire(client, shell_cmd):
    try:
        await client.async_adb_cmd([PAD], shell_cmd)
    except Exception:
        pass
    await asyncio.sleep(D)


async def poll_file(client, path, expected_min=0, timeout_sec=300, interval=8):
    for _ in range(timeout_sec // interval):
        await asyncio.sleep(interval)
        out = await cmd(client, f'stat -c %s {path} 2>/dev/null || echo 0')
        sz = out.strip()
        if sz.isdigit() and int(sz) > expected_min:
            return int(sz)
    return 0


def start_http_server(serve_dir):
    """Start HTTP server to serve files to device."""
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

    class Handler(BaseHTTPRequestHandler):
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
    return server


# ═══════════════════════════════════════════════════════════════════
#  RESTORE — Push clone data to device
# ═══════════════════════════════════════════════════════════════════

async def restore_clone(clone_dir: Path):
    """Restore cloned app data + system data to our device.
    
    DOES NOT change device identity — only restores app data,
    shared_prefs, databases, accounts, and system-level Google data.
    """
    print("\n" + "=" * 60)
    print("  CLONE RESTORE — DATA ONLY (identity untouched)")
    print("=" * 60)

    client = VMOSCloudClient(ak=AK, sk=SK, base_url=API)

    # Load identity metadata for reference
    identity_file = clone_dir / "identity.json"
    if identity_file.exists():
        meta = json.load(open(identity_file))
        model = meta.get("identity", {}).get("model", "?")
        brand = meta.get("identity", {}).get("brand", "?")
        accts = meta.get("accounts", [])
        hv_apps = meta.get("high_value_apps", [])
        print(f"  Source: {brand} {model}")
        print(f"  Account: {accts}")
        print(f"  High-value apps: {', '.join(hv_apps)}")
    else:
        print("  ⚠ No identity.json found")
        hv_apps = []

    # ── Step 1: Create tar of clone data for upload ──
    print(f"\n  [1/6] Preparing data tars...")

    serve_dir = BASE_DIR / "tmp" / "clone_serve"
    serve_dir.mkdir(parents=True, exist_ok=True)

    # Copy the appdata.tar.gz and sysdata.tar.gz to serve dir
    appdata_tar = clone_dir / "appdata.tar.gz"
    sysdata_tar = clone_dir / "sysdata.tar.gz"

    if appdata_tar.exists():
        shutil.copy2(str(appdata_tar), str(serve_dir / "appdata.tar.gz"))
        print(f"    appdata.tar.gz: {appdata_tar.stat().st_size / 1048576:.1f}MB")

    if sysdata_tar.exists():
        shutil.copy2(str(sysdata_tar), str(serve_dir / "sysdata.tar.gz"))
        print(f"    sysdata.tar.gz: {sysdata_tar.stat().st_size / 1048576:.1f}MB")

    # Start HTTP server
    server = start_http_server(serve_dir)
    base_url = f"http://{VPS_IP}:{SERVE_PORT}"
    print(f"    Serving at {base_url}/")

    # ── Step 2: Install required apps ──
    print(f"\n  [2/6] Checking/installing apps...")

    # Check what's installed
    await asyncio.sleep(D)
    installed_raw = await cmd(client, "pm list packages 2>/dev/null")
    installed = set(installed_raw.split("\n")) if installed_raw else set()
    installed = {p.replace("package:", "").strip() for p in installed if p.startswith("package:")}

    apps_dir = clone_dir / "apps" / "data" / "data"
    cloned_apps = [d.name for d in apps_dir.iterdir() if d.is_dir()] if apps_dir.exists() else []

    for pkg in cloned_apps:
        if pkg in installed:
            print(f"    ✓ {pkg} already installed")
        else:
            print(f"    ○ {pkg} NOT installed — will restore data after install")

    # Try to install WhatsApp if not present
    if "com.whatsapp" not in installed:
        print(f"\n    Installing WhatsApp...")
        await cmd(client, f'curl -L -s -o /data/local/tmp/whatsapp.apk "https://scontent.whatsapp.net/v/t61.25985-34/468578037_1321167802199498_1459539500771498587_n.apk/WhatsApp.apk" 2>&1 &')
        await asyncio.sleep(D)
        # Also try direct APK URL
        await fire(client, 'nohup curl -L -s -o /data/local/tmp/whatsapp.apk "https://whatsapp.com/android" > /dev/null 2>&1 &')
        sz = await poll_file(client, "/data/local/tmp/whatsapp.apk", expected_min=10000000, timeout_sec=120)
        if sz > 10000000:
            print(f"    Downloaded WhatsApp: {sz/1048576:.1f}MB")
            await asyncio.sleep(D)
            out = await cmd(client, "pm install -r -d -g /data/local/tmp/whatsapp.apk 2>&1", timeout_sec=60)
            print(f"    Install: {out[:200]}")
        else:
            print(f"    ⚠ WhatsApp download failed (will still restore data for when installed)")

    # ── Step 3: Download and extract appdata on device ──
    print(f"\n  [3/6] Downloading app data to device...")

    await cmd(client, "mkdir -p /data/local/tmp/clone_restore")
    await asyncio.sleep(D)

    if appdata_tar.exists():
        await fire(client, f'nohup curl -s -o /data/local/tmp/clone_restore/appdata.tar.gz {base_url}/appdata.tar.gz > /dev/null 2>&1 &')
        expected = appdata_tar.stat().st_size
        sz = await poll_file(client, "/data/local/tmp/clone_restore/appdata.tar.gz",
                             expected_min=expected - 1000, timeout_sec=300)
        if sz > 0:
            print(f"    ✓ Downloaded appdata.tar.gz ({sz/1048576:.1f}MB)")
        else:
            print(f"    ✗ Download failed")
            return False
    else:
        print(f"    ⚠ No appdata.tar.gz")

    await asyncio.sleep(D)

    # Extract on device
    print(f"    Extracting...")
    await fire(client, 'nohup tar xzf /data/local/tmp/clone_restore/appdata.tar.gz -C /data/local/tmp/clone_restore/ > /dev/null 2>&1 &')
    await asyncio.sleep(20)  # tar needs time for 52MB
    out = await cmd(client, "ls /data/local/tmp/clone_restore/data/data/ 2>/dev/null")
    print(f"    Extracted dirs: {out}")

    # ── Step 4: Restore app data ──
    print(f"\n  [4/6] Restoring app data...")

    for pkg in cloned_apps:
        src = f"/data/local/tmp/clone_restore/data/data/{pkg}"
        dst = f"/data/data/{pkg}"

        # Force-stop app first
        await cmd(client, f"am force-stop {pkg} 2>/dev/null")
        await asyncio.sleep(D)

        # Check if source dir exists on device
        check = await cmd(client, f"[ -d {src} ] && echo YES || echo NO")
        if "YES" not in (check or ""):
            print(f"    ⚠ {pkg}: no extracted data on device")
            continue

        # Restore shared_prefs, databases, files, no_backup
        restore_script = f"""
mkdir -p {dst}/shared_prefs {dst}/databases {dst}/files {dst}/no_backup 2>/dev/null
[ -d {src}/shared_prefs ] && cp -a {src}/shared_prefs/* {dst}/shared_prefs/ 2>/dev/null
[ -d {src}/databases ] && cp -a {src}/databases/* {dst}/databases/ 2>/dev/null
[ -d {src}/files ] && cp -a {src}/files/* {dst}/files/ 2>/dev/null
[ -d {src}/no_backup ] && cp -a {src}/no_backup/* {dst}/no_backup/ 2>/dev/null
PKG_UID=$(dumpsys package {pkg} 2>/dev/null | grep userId= | head -1 | sed 's/.*userId=//;s/ .*//')
[ -n "$PKG_UID" ] && chown -R $PKG_UID:$PKG_UID {dst}/ 2>/dev/null
echo "RESTORE_OK:$PKG_UID"
"""
        out = await cmd(client, restore_script.replace("\n", " "), timeout_sec=30)
        if "RESTORE_OK" in (out or ""):
            uid = out.split("RESTORE_OK:")[1].strip() if "RESTORE_OK:" in out else "?"
            print(f"    ✓ {pkg}: data restored (uid={uid})")
        else:
            print(f"    ✗ {pkg}: restore failed ({out[:100]})")
        await asyncio.sleep(D)

    # ── Step 5: Restore system data (GMS, GSF, accounts) ──
    print(f"\n  [5/6] Restoring system data...")

    if sysdata_tar.exists():
        await fire(client, f'nohup curl -s -o /data/local/tmp/clone_restore/sysdata.tar.gz {base_url}/sysdata.tar.gz > /dev/null 2>&1 &')
        expected_sys = sysdata_tar.stat().st_size
        sz = await poll_file(client, "/data/local/tmp/clone_restore/sysdata.tar.gz",
                             expected_min=expected_sys - 500, timeout_sec=120)
        if sz > 0:
            print(f"    ✓ Downloaded sysdata.tar.gz ({sz/1048576:.1f}MB)")
        else:
            print(f"    ✗ sysdata download failed")

        await asyncio.sleep(D)
        # Extract system data
        await fire(client, 'nohup tar xzf /data/local/tmp/clone_restore/sysdata.tar.gz -C /data/local/tmp/clone_restore/ > /dev/null 2>&1 &')
        await asyncio.sleep(10)

    # GMS shared_prefs
    gms_restore = """
am force-stop com.google.android.gms 2>/dev/null
GMS_UID=$(dumpsys package com.google.android.gms 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
SRC=/data/local/tmp/clone_restore/data/data/com.google.android.gms
DST=/data/data/com.google.android.gms
COUNT=0
if [ -d $SRC/shared_prefs ]; then
    mkdir -p $DST/shared_prefs
    for f in $SRC/shared_prefs/*; do [ -f "$f" ] && cp "$f" $DST/shared_prefs/ && COUNT=$((COUNT+1)); done
fi
if [ -d $SRC/databases ]; then
    mkdir -p $DST/databases
    for f in $SRC/databases/*; do [ -f "$f" ] && cp "$f" $DST/databases/ && COUNT=$((COUNT+1)); done
fi
[ -n "$GMS_UID" ] && chown -R "$GMS_UID:$GMS_UID" $DST/ 2>/dev/null
echo "GMS_OK:$COUNT"
"""
    out = await cmd(client, gms_restore.replace("\n", " "), timeout_sec=30)
    print(f"    GMS data: {out}")
    await asyncio.sleep(D)

    # GSF data
    gsf_restore = """
am force-stop com.google.android.gsf 2>/dev/null
GSF_UID=$(dumpsys package com.google.android.gsf 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
SRC=/data/local/tmp/clone_restore/data/data/com.google.android.gsf
DST=/data/data/com.google.android.gsf
COUNT=0
if [ -d $SRC/databases ]; then
    mkdir -p $DST/databases
    for f in $SRC/databases/*; do [ -f "$f" ] && cp "$f" $DST/databases/ && COUNT=$((COUNT+1)); done
fi
if [ -d $SRC/shared_prefs ]; then
    mkdir -p $DST/shared_prefs
    for f in $SRC/shared_prefs/*; do [ -f "$f" ] && cp "$f" $DST/shared_prefs/ && COUNT=$((COUNT+1)); done
fi
[ -n "$GSF_UID" ] && chown -R "$GSF_UID:$GSF_UID" $DST/ 2>/dev/null
echo "GSF_OK:$COUNT"
"""
    out = await cmd(client, gsf_restore.replace("\n", " "), timeout_sec=30)
    print(f"    GSF data: {out}")
    await asyncio.sleep(D)

    # System accounts (accounts_ce.db)
    acct_restore = """
SRC=/data/local/tmp/clone_restore/data/system_ce/0
if [ -f $SRC/accounts_ce.db ]; then
    cp $SRC/accounts_ce.db /data/system_ce/0/accounts_ce.db 2>/dev/null
    chown 1000:1000 /data/system_ce/0/accounts_ce.db 2>/dev/null
    chmod 600 /data/system_ce/0/accounts_ce.db 2>/dev/null
    echo "ACCT_OK"
else
    echo "ACCT_NOFILE"
fi
"""
    out = await cmd(client, acct_restore.replace("\n", " "), timeout_sec=30)
    print(f"    Accounts DB: {out}")
    await asyncio.sleep(D)

    # ── Step 6: Restart services + broadcast ──
    print(f"\n  [6/6] Restarting services...")
    await cmd(client, "am force-stop com.google.android.gms; am force-stop com.google.android.gsf")
    await asyncio.sleep(D)
    await cmd(client, "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null")
    await asyncio.sleep(D)
    await cmd(client, "am startservice com.google.android.gms/.chimera.GmsIntentOperationService 2>/dev/null || true")
    await asyncio.sleep(D)

    # Verify accounts
    out = await cmd(client, 'dumpsys account 2>/dev/null | grep "Account {" | head -10')
    print(f"\n    Accounts now: {out if out else '(checking...)'}")
    await asyncio.sleep(D)

    # Verify GMS prefs
    out = await cmd(client, "ls /data/data/com.google.android.gms/shared_prefs/*.xml 2>/dev/null | wc -l")
    print(f"    GMS prefs: {out} files")

    # Cleanup
    await cmd(client, "rm -rf /data/local/tmp/clone_restore")

    server.shutdown()
    print(f"\n  ✓ RESTORE COMPLETE — identity untouched, data restored")
    return True


# ═══════════════════════════════════════════════════════════════════
#  VERIFY — Screenshot each app to confirm login state
# ═══════════════════════════════════════════════════════════════════

async def verify_screenshots(clone_dir: Path):
    """Launch each app and take screenshots to verify login state."""
    print("\n" + "=" * 60)
    print("  SCREENSHOT VERIFICATION")
    print("=" * 60)

    client = VMOSCloudClient(ak=AK, sk=SK, base_url=API)

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    verify_dir = SCREENSHOTS_DIR / ts
    verify_dir.mkdir(parents=True, exist_ok=True)

    # Get installed packages
    await asyncio.sleep(D)
    installed_raw = await cmd(client, "pm list packages 2>/dev/null")
    installed = {p.replace("package:", "").strip() for p in (installed_raw or "").split("\n") if p.startswith("package:")}

    # Load identity for reference
    identity_file = clone_dir / "identity.json"
    hv_apps = []
    if identity_file.exists():
        meta = json.load(open(identity_file))
        hv_apps = meta.get("high_value_apps", [])

    # List of apps to screenshot (all from clone + some system)
    apps_to_check = []
    for pkg in hv_apps:
        if pkg in installed:
            apps_to_check.append(pkg)

    # Always check Google Wallet
    if "com.google.android.apps.walletnfcrel" in installed:
        if "com.google.android.apps.walletnfcrel" not in apps_to_check:
            apps_to_check.append("com.google.android.apps.walletnfcrel")

    print(f"  Apps to verify: {len(apps_to_check)}")
    for pkg in apps_to_check:
        print(f"    • {pkg}")

    screenshots = []

    # ── First: Home screen screenshot ──
    print(f"\n  [home] Taking home screen...")
    await cmd(client, "input keyevent KEYCODE_HOME")
    await asyncio.sleep(3)
    await asyncio.sleep(D)

    sc = await take_screenshot(client, verify_dir, "00_home_screen")
    if sc:
        screenshots.append(sc)

    # ── Screenshot each app ──
    for i, pkg in enumerate(apps_to_check):
        activity = APP_ACTIVITIES.get(pkg)

        print(f"\n  [{i+1}/{len(apps_to_check)}] {pkg}")

        # Force stop first to get fresh launch
        await cmd(client, f"am force-stop {pkg} 2>/dev/null")
        await asyncio.sleep(D)

        # Launch app
        if activity:
            await cmd(client, f"am start -n {activity} 2>/dev/null")
        else:
            # Generic launch via monkey
            await cmd(client, f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1 2>/dev/null")
        
        # Wait for app to load
        await asyncio.sleep(8)
        await asyncio.sleep(D)

        # Screenshot 1: initial screen
        safe_name = pkg.replace(".", "_")
        sc = await take_screenshot(client, verify_dir, f"{i+1:02d}_{safe_name}_screen1")
        if sc:
            screenshots.append(sc)

        # For Google Wallet, navigate deeper
        if pkg == "com.google.android.apps.walletnfcrel":
            # Wait more for Wallet to fully load
            await asyncio.sleep(5)
            sc2 = await take_screenshot(client, verify_dir, f"{i+1:02d}_{safe_name}_screen2_loaded")
            if sc2:
                screenshots.append(sc2)

            # Try scrolling down to see payment methods
            await cmd(client, "input swipe 540 1500 540 500 500")
            await asyncio.sleep(3)
            await asyncio.sleep(D)
            sc3 = await take_screenshot(client, verify_dir, f"{i+1:02d}_{safe_name}_screen3_scrolled")
            if sc3:
                screenshots.append(sc3)

        # For WhatsApp, take a second screenshot after potential loading
        if "whatsapp" in pkg:
            await asyncio.sleep(5)
            sc2 = await take_screenshot(client, verify_dir, f"{i+1:02d}_{safe_name}_screen2_loaded")
            if sc2:
                screenshots.append(sc2)

        # Go back to home
        await cmd(client, "input keyevent KEYCODE_HOME")
        await asyncio.sleep(2)
        await asyncio.sleep(D)

    # ── Check Google Pay payment instruments specifically ──
    print(f"\n  [wallet] Checking Google Pay instruments...")
    await asyncio.sleep(D)

    # Check tapandpay database
    wallet_check = """
echo "===TAP_AND_PAY==="
ls -la /data/data/com.google.android.apps.walletnfcrel/databases/ 2>/dev/null
echo "===WALLET_PREFS==="
ls /data/data/com.google.android.apps.walletnfcrel/shared_prefs/ 2>/dev/null
echo "===WALLET_FILES==="
ls /data/data/com.google.android.apps.walletnfcrel/files/ 2>/dev/null | head -20
echo "===GMS_WALLET==="
ls /data/data/com.google.android.gms/databases/ 2>/dev/null | grep -i wallet
echo "===ACCOUNTS_CHECK==="
dumpsys account 2>/dev/null | grep -E "Account \\{|name=" | head -10
echo "===END==="
"""
    out = await cmd(client, wallet_check.replace("\n", " "), timeout_sec=30)
    print(f"    {out[:500]}")

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"  VERIFICATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Screenshots: {len(screenshots)} saved to {verify_dir}/")
    for sc in screenshots:
        print(f"    • {sc}")

    # Save verification report
    report = {
        "timestamp": datetime.now().isoformat(),
        "clone_source": str(clone_dir),
        "apps_verified": apps_to_check,
        "screenshots": screenshots,
        "screenshot_dir": str(verify_dir),
    }
    with open(verify_dir / "verification_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return screenshots


async def take_screenshot(client, output_dir: Path, name: str) -> str | None:
    """Take screenshot on device, pull to VPS."""
    device_path = f"/sdcard/{name}.png"

    await cmd(client, f"screencap -p {device_path}")
    await asyncio.sleep(D)

    # Check file exists
    out = await cmd(client, f"stat -c %s {device_path} 2>/dev/null || echo 0")
    try:
        sz = int(out.strip())
    except ValueError:
        sz = 0

    if sz < 1000:
        print(f"    ✗ Screenshot failed: {name}")
        return None

    # Pull via base64 chunks (screenshots are typically 100-500KB)
    local_path = output_dir / f"{name}.png"
    await _pull_file_b64(client, device_path, local_path, sz)

    # Cleanup device
    await cmd(client, f"rm -f {device_path}")

    if local_path.exists() and local_path.stat().st_size > 1000:
        print(f"    ✓ {name}.png ({local_path.stat().st_size / 1024:.0f}KB)")
        return f"{name}.png"
    else:
        print(f"    ✗ Pull failed: {name}")
        return None


async def _pull_file_b64(client, device_path: str, local_path: Path, total_size: int):
    """Pull file from device via chunked base64 reads."""
    # Use on-device base64 + chunked read to work around 2000-byte sync_cmd limit
    # Base64 expands by 4/3, so ~1400 raw bytes → ~1867 base64 chars (fits in 2000)
    CHUNK = 1350
    parts = []
    offset = 0

    while offset < total_size:
        remaining = total_size - offset
        read_size = min(CHUNK, remaining)
        b64 = await cmd(client,
            f"dd if={device_path} bs=1 skip={offset} count={read_size} 2>/dev/null | base64 | tr -d '\\n'")

        if not b64 or b64.startswith("ERR"):
            break
        parts.append(b64)
        offset += read_size

    if parts:
        import base64 as b64mod
        raw = b""
        for p in parts:
            try:
                padded = p + "=" * (-len(p) % 4)
                raw += b64mod.b64decode(padded)
            except Exception:
                pass

        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(raw)


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return

    mode = sys.argv[1]
    clone_path = Path(sys.argv[2])

    # Support relative path
    if not clone_path.is_absolute():
        clone_path = BASE_DIR / clone_path

    if not clone_path.exists():
        print(f"  ✗ Clone directory not found: {clone_path}")
        return

    if mode in ("restore", "full"):
        ok = await restore_clone(clone_path)
        if not ok:
            print("  ✗ Restore failed")
            return

    if mode in ("verify", "full"):
        # Give services time to settle after restore
        if mode == "full":
            print("\n  Waiting 15s for services to settle...")
            await asyncio.sleep(15)
        await verify_screenshots(clone_path)

    print("\n  Done.")


if __name__ == "__main__":
    asyncio.run(main())
