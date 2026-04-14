#!/usr/bin/env python3
"""
Bundle & Deploy Tool v2 — Individual file download approach.

Serves each file separately over HTTP. No giant tar.gz that corrupts APKs.
Downloads APKs individually via curl, restores data per-app.

Usage:
    python3 tools/bundle_and_deploy.py bundle    # Prepare serve directory
    python3 tools/bundle_and_deploy.py serve      # Start HTTP server
    python3 tools/bundle_and_deploy.py deploy     # Download + install on device
    python3 tools/bundle_and_deploy.py full       # All steps
"""

import asyncio
import hashlib
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import tarfile
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ─── Config ──────────────────────────────────────────────────────────────
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
PAD = "AC32010810392"
API = "https://api.vmoscloud.com"
CLONE_DIR = "tmp/device_clones/10_0_76_1"
BUNDLE_DIR = "tmp/deploy_bundle"
SERVE_PORT = 18999
TMP_DIR = "/data/local/tmp"
RATE_DELAY = 3.5

# System apps — don't try to install, just restore data
SYSTEM_PKGS = {
    "com.android.vending", "com.android.chrome",
    "com.google.android.gms", "com.google.android.gsf",
    "com.google.android.gms.policy_sidecar_aps",
    "com.google.android.apps.restore",
}

# ─── Helpers ─────────────────────────────────────────────────────────────

def get_public_ip():
    try:
        r = subprocess.run(["curl", "-4", "-s", "--max-time", "5", "ifconfig.me"],
                           capture_output=True, text=True, timeout=8)
        ip = r.stdout.strip()
        if ip and "." in ip:
            return ip
    except Exception:
        pass
    try:
        r = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip().split()[0]
    except Exception:
        return "127.0.0.1"


def file_size_str(size):
    if size > 1048576:
        return f"{size / 1048576:.1f}MB"
    return f"{size / 1024:.0f}KB"


async def cmd(client, shell_cmd, timeout_sec=30):
    """Run shell command on device, return output string."""
    try:
        r = await client.sync_cmd(PAD, shell_cmd, timeout_sec=timeout_sec)
        if not r or not isinstance(r, dict):
            return ""
        data = r.get("data", [])
        if data and isinstance(data, list) and len(data) > 0:
            return data[0].get("errorMsg", "") or ""
        return ""
    except Exception as e:
        return f"ERROR: {e}"


async def fire(client, shell_cmd):
    """Fire a command and don't care about the response (fire-and-forget via API)."""
    try:
        await client.sync_cmd(PAD, shell_cmd, timeout_sec=5)
    except Exception:
        pass
    await asyncio.sleep(RATE_DELAY)


async def poll_file(client, path, timeout_sec=300, interval=5):
    """Poll until a file exists on device, return its size."""
    for _ in range(timeout_sec // interval):
        await asyncio.sleep(interval)
        out = await cmd(client, f'stat -c %s {path} 2>/dev/null || echo 0')
        sz = out.strip()
        if sz.isdigit() and int(sz) > 0:
            return int(sz)
    return 0


# ═══════════════════════════════════════════════════════════════════
#  STEP 1: BUNDLE — Prepare individual files for HTTP serving
# ═══════════════════════════════════════════════════════════════════

def create_bundle():
    """Copy all files into flat serve directory + create manifest."""
    print("\n══════════════════════════════════════════════════")
    print("  STEP 1: PREPARING FILES FOR HTTP SERVING")
    print("══════════════════════════════════════════════════\n")

    serve_dir = os.path.join(BUNDLE_DIR, "files")
    os.makedirs(serve_dir, exist_ok=True)

    manifest = {"files": [], "apps": {}, "system_data": {}}

    # ── 1a: Copy APKs individually (NO compression — preserves integrity) ──
    apps_dir = os.path.join(CLONE_DIR, "apps")
    if os.path.isdir(apps_dir):
        for pkg in sorted(os.listdir(apps_dir)):
            pkg_dir = os.path.join(apps_dir, pkg)
            if not os.path.isdir(pkg_dir):
                continue

            app_info = {}

            # Copy APK
            apk_src = os.path.join(pkg_dir, "base.apk")
            if os.path.isfile(apk_src) and os.path.getsize(apk_src) > 10240:
                apk_name = f"{pkg}.apk"
                apk_dst = os.path.join(serve_dir, apk_name)
                shutil.copy2(apk_src, apk_dst)
                size = os.path.getsize(apk_dst)
                app_info["apk"] = apk_name
                app_info["apk_size"] = size
                manifest["files"].append({"name": apk_name, "size": size, "type": "apk"})
                print(f"  [APK] {pkg}: {file_size_str(size)}")

            # Copy data.tar.gz
            data_src = os.path.join(pkg_dir, "data.tar.gz")
            if os.path.isfile(data_src) and os.path.getsize(data_src) > 100:
                data_name = f"{pkg}_data.tar.gz"
                data_dst = os.path.join(serve_dir, data_name)
                shutil.copy2(data_src, data_dst)
                size = os.path.getsize(data_dst)
                app_info["data"] = data_name
                app_info["data_size"] = size
                manifest["files"].append({"name": data_name, "size": size, "type": "data"})
                print(f"  [DAT] {pkg}: {file_size_str(size)}")

            if app_info:
                manifest["apps"][pkg] = app_info

    # ── 1b: Create system_data.tar — single archive for small files ──
    #   (gms_shared_prefs, gms_databases, gsf_data, gms_accounts,
    #    telegram_session, chrome_data)
    sys_tar_path = os.path.join(serve_dir, "system_data.tar")
    sys_file_count = 0

    with tarfile.open(sys_tar_path, "w") as tar:  # uncompressed for reliability
        for dirname in ["gms_shared_prefs", "gms_databases", "gsf_data",
                        "gms_accounts", "telegram_session", "chrome_data"]:
            src = os.path.join(CLONE_DIR, dirname)
            if not os.path.isdir(src):
                continue
            for root, dirs, files in os.walk(src):
                for f in files:
                    fpath = os.path.join(root, f)
                    arcname = os.path.relpath(fpath, CLONE_DIR)
                    tar.add(fpath, arcname=arcname)
                    sys_file_count += 1
            manifest["system_data"][dirname] = True

    sys_size = os.path.getsize(sys_tar_path)
    manifest["files"].append({"name": "system_data.tar", "size": sys_size, "type": "system"})
    print(f"\n  [SYS] system_data.tar: {file_size_str(sys_size)} ({sys_file_count} files)")

    # ── 1c: Write manifest ──
    manifest_path = os.path.join(serve_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    total = sum(e["size"] for e in manifest["files"])
    print(f"\n  ✓ {len(manifest['files'])} files prepared ({file_size_str(total)} total)")
    print(f"  ✓ {len(manifest['apps'])} apps ({sum(1 for a in manifest['apps'].values() if 'apk' in a)} APKs)")
    print(f"  ✓ Serve dir: {os.path.abspath(serve_dir)}")

    return manifest


# ═══════════════════════════════════════════════════════════════════
#  STEP 2: HTTP SERVER
# ═══════════════════════════════════════════════════════════════════

def start_http_server():
    """Start HTTP server serving individual files."""
    print("\n══════════════════════════════════════════════════")
    print("  STEP 2: STARTING HTTP SERVER")
    print("══════════════════════════════════════════════════\n")

    serve_dir = os.path.abspath(os.path.join(BUNDLE_DIR, "files"))
    ip = get_public_ip()
    base_url = f"http://{ip}:{SERVE_PORT}"

    # Kill existing server on this port
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        if s.connect_ex(("0.0.0.0", SERVE_PORT)) == 0:
            os.system(f"fuser -k {SERVE_PORT}/tcp 2>/dev/null")
            time.sleep(1)
        s.close()
    except Exception:
        pass

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=serve_dir, **kw)
        def log_message(self, fmt, *args):
            print(f"  [HTTP] {args[0]}")

    class ReuseTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
    
    server = ReuseTCPServer(("0.0.0.0", SERVE_PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # List files being served
    files = sorted(os.listdir(serve_dir))
    print(f"  ✓ Serving {len(files)} files at {base_url}/")
    for f in files:
        sz = os.path.getsize(os.path.join(serve_dir, f))
        print(f"    {base_url}/{f}  ({file_size_str(sz)})")

    return server, base_url


# ═══════════════════════════════════════════════════════════════════
#  STEP 3: DEPLOY — Download each file + install + restore
# ═══════════════════════════════════════════════════════════════════

async def deploy_to_device(base_url):
    """Download files individually to device, install APKs, restore data."""
    print("\n══════════════════════════════════════════════════")
    print("  STEP 3: DEPLOYING TO DEVICE")
    print("══════════════════════════════════════════════════\n")

    client = VMOSCloudClient(ak=AK, sk=SK, base_url=API)

    # ── 3a: Clean device tmp ──
    print("  [3a] Cleaning device...")
    await cmd(client, f"rm -rf {TMP_DIR}/clone_* {TMP_DIR}/*.apk {TMP_DIR}/*.tar* {TMP_DIR}/dl_* {TMP_DIR}/extract* 2>/dev/null; echo OK")
    await asyncio.sleep(RATE_DELAY)
    await cmd(client, f"mkdir -p {TMP_DIR}/clone_apks {TMP_DIR}/clone_data")
    await asyncio.sleep(RATE_DELAY)

    # ── 3b: Download manifest ──
    print("  [3b] Downloading manifest...")
    await cmd(client, f'curl -s -o {TMP_DIR}/manifest.json "{base_url}/manifest.json"')
    await asyncio.sleep(RATE_DELAY)
    mcheck = await cmd(client, f"cat {TMP_DIR}/manifest.json 2>/dev/null | head -3")
    if '"files"' not in mcheck:
        print(f"    ✗ Manifest download failed: {mcheck[:100]}")
        return False
    print("    ✓ Manifest OK")

    # Read local manifest for the plan
    manifest_path = os.path.join(BUNDLE_DIR, "files", "manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)

    # ── 3c: Download + install APKs one by one ──
    print("\n  [3c] Installing APKs...")
    installed = []
    failed = []

    for pkg, info in sorted(manifest["apps"].items()):
        if "apk" not in info:
            continue

        apk_name = info["apk"]
        expected_size = info["apk_size"]
        apk_path = f"{TMP_DIR}/clone_apks/{apk_name}"

        is_system = pkg in SYSTEM_PKGS
        if is_system:
            print(f"    {pkg}: system (skip install)")
            installed.append(pkg)
            continue

        # Download APK — fire curl in background, poll for file
        print(f"    {pkg}: downloading {file_size_str(expected_size)}...", end=" ", flush=True)
        await fire(client, f'curl -s -o {apk_path} {base_url}/{apk_name} &')
        
        # Poll until file appears with expected size
        dl_size = await poll_file(client, apk_path, timeout_sec=300)
        
        if dl_size == 0 or abs(dl_size - expected_size) > expected_size * 0.01:
            print(f"FAILED (got {dl_size})")
            failed.append(pkg)
            continue
        print(f"OK ({file_size_str(dl_size)})", end=" ", flush=True)

        # Install APK — fire in background, wait then check
        await fire(client, f'pm install -r -d -g {apk_path} &')
        
        # Wait for install to complete
        print("installing...", end=" ", flush=True)
        await asyncio.sleep(20)

        await asyncio.sleep(RATE_DELAY)
        check = await cmd(client, f'pm list packages 2>/dev/null | grep -c {pkg}')
        if check.strip() == "1":
            print("✓ installed")
            installed.append(pkg)
        else:
            # Try one more time after another wait
            await asyncio.sleep(15)
            check = await cmd(client, f'pm list packages 2>/dev/null | grep -c {pkg}')
            if check.strip() == "1":
                print("✓ installed")
                installed.append(pkg)
            else:
                print("✗ install failed")
                failed.append(pkg)

        # Clean APK
        await cmd(client, f'rm -f {apk_path}')
        await asyncio.sleep(RATE_DELAY)

    print(f"\n    Installed: {len(installed)}, Failed: {len(failed)}")
    if failed:
        print(f"    Failed pkgs: {', '.join(failed)}")

    # ── 3d: Download system_data.tar and extract ──
    print("\n  [3d] Downloading system data...")
    sys_path = f"{TMP_DIR}/clone_data/system_data.tar"

    await fire(client, f'curl -s -o {sys_path} {base_url}/system_data.tar &')
    dl_size = await poll_file(client, sys_path, timeout_sec=300, interval=5)

    if dl_size == 0:
        print("    ✗ System data download failed")
    else:
        print(f"    ✓ Downloaded system_data.tar ({file_size_str(dl_size)})")
        await asyncio.sleep(RATE_DELAY)

        # Extract system_data.tar
        print("    Extracting...")
        await fire(client, f'cd {TMP_DIR}/clone_data && tar xf system_data.tar &')
        await asyncio.sleep(15)  # give tar time to finish

        ls = await cmd(client, f"ls {TMP_DIR}/clone_data/ 2>/dev/null")
        print(f"    Contents: {ls.strip()}")

    # ── 3e: Restore app data ──
    print("\n  [3e] Restoring app data...")
    data_restored = 0

    for pkg, info in sorted(manifest["apps"].items()):
        if "data" not in info:
            continue
        if pkg not in installed and pkg not in SYSTEM_PKGS:
            print(f"    {pkg}: skipped (not installed)")
            continue

        data_name = info["data"]
        data_path = f"{TMP_DIR}/clone_data/{data_name}"
        expected_size = info["data_size"]

        # Download data archive
        print(f"    {pkg}: downloading data ({file_size_str(expected_size)})...", end=" ", flush=True)
        await fire(client, f'curl -s -o {data_path} {base_url}/{data_name} &')
        dl_size = await poll_file(client, data_path, timeout_sec=180, interval=5)
        await asyncio.sleep(RATE_DELAY)

        if dl_size == 0:
            print("download failed")
            continue
        print(f"OK ({file_size_str(dl_size)})", end=" ", flush=True)

        # Force-stop app, extract data into /data/data/pkg/
        await cmd(client, f"am force-stop {pkg} 2>/dev/null")
        await asyncio.sleep(RATE_DELAY)

        restore_cmd = (
            f'cd /data/data/{pkg}/ && '
            f'tar xzf {data_path} 2>/dev/null; '
            f'PKG_UID=$(dumpsys package {pkg} 2>/dev/null | grep userId= | head -1 | sed "s/.*userId=//;s/ .*//"); '
            f'[ -n "$PKG_UID" ] && chown -R $PKG_UID:$PKG_UID /data/data/{pkg}/ 2>/dev/null; '
            f'echo done'
        )
        out = await cmd(client, restore_cmd, timeout_sec=30)
        if "done" in out:
            print("✓ restored")
            data_restored += 1
        else:
            print("✗ restore failed")

        # Cleanup data archive
        await cmd(client, f'rm -f {data_path}')
        await asyncio.sleep(RATE_DELAY)

    print(f"\n    Data restored: {data_restored} apps")

    # ── 3f: Restore system data (GMS prefs, databases, accounts, etc.) ──
    print("\n  [3f] Restoring system data...")
    clone_dir = f"{TMP_DIR}/clone_data"

    # GMS shared_prefs
    await cmd(client, "am force-stop com.google.android.gms 2>/dev/null")
    await asyncio.sleep(RATE_DELAY)

    gms_prefs_script = f"""
GMS_UID=$(dumpsys package com.google.android.gms 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
GMS_DIR="/data/data/com.google.android.gms/shared_prefs"
mkdir -p "$GMS_DIR"
COUNT=0
for f in {clone_dir}/gms_shared_prefs/*.xml; do
    [ -f "$f" ] || continue
    cp "$f" "$GMS_DIR/" && COUNT=$((COUNT+1))
done
[ -n "$GMS_UID" ] && chown -R "$GMS_UID:$GMS_UID" "$GMS_DIR"
echo "PREFS_OK $COUNT"
"""
    out = await cmd(client, gms_prefs_script.replace("\n", " "), timeout_sec=30)
    print(f"    GMS shared_prefs: {out.strip()}")
    await asyncio.sleep(RATE_DELAY)

    # GMS databases
    gms_db_script = f"""
GMS_UID=$(dumpsys package com.google.android.gms 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
GMS_DB="/data/data/com.google.android.gms/databases"
mkdir -p "$GMS_DB"
COUNT=0
for f in {clone_dir}/gms_databases/*; do
    [ -f "$f" ] || continue
    cp "$f" "$GMS_DB/" && COUNT=$((COUNT+1))
done
[ -n "$GMS_UID" ] && chown -R "$GMS_UID:$GMS_UID" "$GMS_DB"
echo "DB_OK $COUNT"
"""
    out = await cmd(client, gms_db_script.replace("\n", " "), timeout_sec=30)
    print(f"    GMS databases: {out.strip()}")
    await asyncio.sleep(RATE_DELAY)

    # GSF data
    gsf_script = f"""
GSF_UID=$(dumpsys package com.google.android.gsf 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
am force-stop com.google.android.gsf 2>/dev/null
mkdir -p /data/data/com.google.android.gsf/databases /data/data/com.google.android.gsf/shared_prefs
for f in {clone_dir}/gsf_data/*.db {clone_dir}/gsf_data/*.db-journal; do [ -f "$f" ] && cp "$f" /data/data/com.google.android.gsf/databases/; done
for f in {clone_dir}/gsf_data/*.xml; do [ -f "$f" ] && cp "$f" /data/data/com.google.android.gsf/shared_prefs/; done
[ -n "$GSF_UID" ] && chown -R "$GSF_UID:$GSF_UID" /data/data/com.google.android.gsf/
echo "GSF_OK"
"""
    out = await cmd(client, gsf_script.replace("\n", " "), timeout_sec=30)
    print(f"    GSF data: {out.strip()}")
    await asyncio.sleep(RATE_DELAY)

    # System accounts
    acct_script = f"""
DONE=0
if [ -f {clone_dir}/gms_accounts/data_system_ce_0_accounts_ce.db ]; then
    cp {clone_dir}/gms_accounts/data_system_ce_0_accounts_ce.db /data/system_ce/0/accounts_ce.db 2>/dev/null
    chown 1000:1000 /data/system_ce/0/accounts_ce.db && chmod 600 /data/system_ce/0/accounts_ce.db && DONE=$((DONE+1))
fi
if [ -f {clone_dir}/gms_accounts/data_system_de_0_accounts_de.db ]; then
    cp {clone_dir}/gms_accounts/data_system_de_0_accounts_de.db /data/system_de/0/accounts_de.db 2>/dev/null
    chown 1000:1000 /data/system_de/0/accounts_de.db && chmod 600 /data/system_de/0/accounts_de.db && DONE=$((DONE+1))
fi
echo "ACCT_OK $DONE"
"""
    out = await cmd(client, acct_script.replace("\n", " "), timeout_sec=30)
    print(f"    Accounts DB: {out.strip()}")
    await asyncio.sleep(RATE_DELAY)

    # Telegram session
    tg_script = f"""
TG_PKG=""
for p in org.telegram.messenger.web org.telegram.messenger; do pm list packages 2>/dev/null | grep -q "$p" && TG_PKG="$p" && break; done
if [ -n "$TG_PKG" ] && [ -d {clone_dir}/telegram_session ]; then
    TG_UID=$(dumpsys package "$TG_PKG" 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
    am force-stop "$TG_PKG" 2>/dev/null
    TG_F="/data/data/$TG_PKG/files"
    mkdir -p "$TG_F"
    [ -f {clone_dir}/telegram_session/tgnet.dat ] && cp {clone_dir}/telegram_session/tgnet.dat "$TG_F/"
    [ -f {clone_dir}/telegram_session/cache4.db ] && cp {clone_dir}/telegram_session/cache4.db "$TG_F/"
    for n in 1 2 3; do
        if [ -d {clone_dir}/telegram_session/account$n ]; then
            mkdir -p "$TG_F/account$n"
            cp {clone_dir}/telegram_session/account$n/* "$TG_F/account$n/" 2>/dev/null
        fi
    done
    [ -n "$TG_UID" ] && chown -R "$TG_UID:$TG_UID" "$TG_F"
    echo "TG_OK $TG_PKG"
else
    echo "TG_SKIP"
fi
"""
    out = await cmd(client, tg_script.replace("\n", " "), timeout_sec=30)
    print(f"    Telegram session: {out.strip()}")
    await asyncio.sleep(RATE_DELAY)

    # Chrome data
    chrome_script = f"""
CHROME_UID=$(dumpsys package com.android.chrome 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
am force-stop com.android.chrome 2>/dev/null
CD="/data/data/com.android.chrome/app_chrome/Default"
mkdir -p "$CD"
[ -f {clone_dir}/chrome_data/Login_Data.db ] && cp {clone_dir}/chrome_data/Login_Data.db "$CD/Login Data"
[ -f {clone_dir}/chrome_data/Cookies.db ] && cp {clone_dir}/chrome_data/Cookies.db "$CD/Cookies"
[ -f {clone_dir}/chrome_data/History.db ] && cp {clone_dir}/chrome_data/History.db "$CD/History"
[ -f {clone_dir}/chrome_data/Web_Data.db ] && cp {clone_dir}/chrome_data/Web_Data.db "$CD/Web Data"
[ -n "$CHROME_UID" ] && chown -R "$CHROME_UID:$CHROME_UID" /data/data/com.android.chrome/
echo "CHROME_OK"
"""
    out = await cmd(client, chrome_script.replace("\n", " "), timeout_sec=30)
    print(f"    Chrome data: {out.strip()}")
    await asyncio.sleep(RATE_DELAY)

    # ── 3g: Restart services + broadcast ──
    print("\n  [3g] Restarting services...")
    await cmd(client, "am force-stop com.google.android.gms; am force-stop com.google.android.gsf")
    await asyncio.sleep(RATE_DELAY)
    await cmd(client, "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null")
    await asyncio.sleep(RATE_DELAY)
    await cmd(client, "am startservice com.google.android.gms/.chimera.GmsIntentOperationService 2>/dev/null || true")
    await asyncio.sleep(RATE_DELAY)

    # ── 3h: Final verification ──
    print("\n  [3h] VERIFICATION:")

    # Check packages
    pkg_check = await cmd(client, "pm list packages 2>/dev/null")
    await asyncio.sleep(RATE_DELAY)
    for pkg in manifest["apps"]:
        if pkg in pkg_check:
            print(f"    ✓ {pkg}")
        else:
            print(f"    ✗ {pkg} (NOT INSTALLED)")

    # Check accounts
    accts = await cmd(client, 'dumpsys account 2>/dev/null | grep -E "Account \\{|name=" | head -10')
    await asyncio.sleep(RATE_DELAY)
    print(f"\n    Accounts:\n    {accts.strip() if accts.strip() else '(none)'}")

    # GMS prefs count
    prefs = await cmd(client, "ls /data/data/com.google.android.gms/shared_prefs/*.xml 2>/dev/null | wc -l")
    print(f"    GMS shared_prefs: {prefs.strip()} files")

    # Cleanup
    await cmd(client, f"rm -rf {TMP_DIR}/clone_data {TMP_DIR}/clone_apks {TMP_DIR}/manifest.json {TMP_DIR}/dl_* {TMP_DIR}/ext_* {TMP_DIR}/restore_*")

    print("\n  ✓ DEPLOYMENT COMPLETE")
    return True


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    server = None

    if mode in ("bundle", "full"):
        create_bundle()

    if mode in ("serve", "full"):
        server, base_url = start_http_server()

    if mode in ("deploy", "full"):
        if mode == "deploy":
            server, base_url = start_http_server()
        await deploy_to_device(base_url)

    if mode == "serve":
        print(f"\n  Server running. Press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            if server:
                server.shutdown()

    print("\n  Done.")


if __name__ == "__main__":
    asyncio.run(main())
