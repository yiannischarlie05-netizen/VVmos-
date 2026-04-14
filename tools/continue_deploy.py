#!/usr/bin/env python3
"""
Continuation deploy — picks up where the interrupted deploy left off.

Current state:
  - APKPure: installed
  - System apps (Chrome, GMS, GSF, Vending): present
  - Revolut: NOT installed (APK was on device but dir got cleaned)  
  - Telegram: NOT installed
  - GMS shared_prefs: 150 files restored
  - System data tar: was extracted (gms_databases, gsf_data, gms_accounts, telegram_session, chrome_data present)
  - But the clone dirs were cleaned, need to re-download what's missing

Plan:
  1. Re-download Revolut + Telegram APKs (fresh)
  2. Install both
  3. Re-download + extract system_data.tar for proper data placement
  4. Download + restore app data (data.tar.gz per app)
  5. Restart services + verify
"""

import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
PAD = "AC32010810392"
API = "https://api.vmoscloud.com"
URL = "http://YOUR_OLLAMA_HOST:18999"
TMP = "/data/local/tmp"
D = 3.5


async def cmd(client, sh, t=30):
    """Run shell command, return output string."""
    try:
        r = await client.sync_cmd(PAD, sh, timeout_sec=t)
        d = r.get("data", [])
        if d and isinstance(d, list):
            return d[0].get("errorMsg", "") or ""
        return ""
    except Exception as e:
        return f"ERR:{e}"


async def fire(client, sh):
    """Fire command, ignore response."""
    try:
        await client.sync_cmd(PAD, sh, timeout_sec=5)
    except:
        pass
    await asyncio.sleep(D)


async def wait_for_file(client, path, expected_size, label="file"):
    """Poll until file reaches expected size (within 1%)."""
    for i in range(120):  # 120 * 5s = 10min max
        await asyncio.sleep(5)
        out = await cmd(client, f"stat -c %s {path} 2>/dev/null || echo 0")
        sz = int(out.strip()) if out.strip().isdigit() else 0
        if i % 6 == 0:
            print(f"    {label}: {sz/1048576:.1f}MB / {expected_size/1048576:.1f}MB")
        if sz >= expected_size * 0.99:
            print(f"    {label}: COMPLETE ({sz/1048576:.1f}MB)")
            return sz
        time.sleep(D)
    print(f"    {label}: TIMEOUT")
    return 0


async def install_apk(client, apk_path, pkg_name):
    """Install APK and verify."""
    print(f"    Installing {pkg_name}...")
    await fire(client, f"pm install -r -d -g {apk_path}")
    # Wait for install to complete
    await asyncio.sleep(25)
    time.sleep(D)

    out = await cmd(client, f"pm list packages 2>/dev/null | grep -c {pkg_name}")
    if out.strip() == "1":
        print(f"    {pkg_name}: INSTALLED ✓")
        return True

    # Retry
    await asyncio.sleep(20)
    time.sleep(D)
    out = await cmd(client, f"pm list packages 2>/dev/null | grep -c {pkg_name}")
    if out.strip() == "1":
        print(f"    {pkg_name}: INSTALLED ✓ (retry)")
        return True

    print(f"    {pkg_name}: INSTALL FAILED ✗")
    return False


async def main():
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=API)

    print("=" * 60)
    print("  CONTINUATION DEPLOY")
    print("=" * 60)

    # ── Step 0: Prep directories ──
    print("\n[0] Preparing directories...")
    await cmd(client, f"mkdir -p {TMP}/apks {TMP}/data")
    time.sleep(D)

    # ── Step 1: Download + Install Revolut ──
    print("\n[1] Revolut APK")
    revolut_apk = f"{TMP}/apks/revolut.apk"
    await fire(client, f"nohup curl -s -o {revolut_apk} {URL}/com.revolut.revolut.apk >/dev/null 2>&1 &")
    sz = await wait_for_file(client, revolut_apk, 46727168, "Revolut")
    if sz > 0:
        await install_apk(client, revolut_apk, "com.revolut.revolut")
    else:
        print("    Revolut download failed, skipping")

    # ── Step 2: Download + Install Telegram ──
    print("\n[2] Telegram APK")
    telegram_apk = f"{TMP}/apks/telegram.apk"
    await fire(client, f"nohup curl -s -o {telegram_apk} {URL}/org.telegram.messenger.web.apk >/dev/null 2>&1 &")
    sz = await wait_for_file(client, telegram_apk, 43909120, "Telegram")
    if sz > 0:
        await install_apk(client, telegram_apk, "org.telegram.messenger.web")
    else:
        print("    Telegram download failed, skipping")

    # ── Step 3: Download system_data.tar ──
    print("\n[3] System data")
    sys_tar = f"{TMP}/data/system_data.tar"
    await fire(client, f"nohup curl -s -o {sys_tar} {URL}/system_data.tar >/dev/null 2>&1 &")
    sz = await wait_for_file(client, sys_tar, 13660160, "system_data.tar")
    if sz > 0:
        print("    Extracting...")
        await fire(client, f"cd {TMP}/data && tar xf system_data.tar")
        await asyncio.sleep(10)
        time.sleep(D)
        out = await cmd(client, f"ls {TMP}/data/")
        print(f"    Contents: {out.strip()}")
    time.sleep(D)

    # ── Step 4: Restore GMS shared_prefs ──
    print("\n[4] GMS shared_prefs")
    script = f"""
GMS_UID=$(dumpsys package com.google.android.gms 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
am force-stop com.google.android.gms 2>/dev/null
GMS_DIR="/data/data/com.google.android.gms/shared_prefs"
mkdir -p "$GMS_DIR"
COUNT=0
for f in {TMP}/data/gms_shared_prefs/*.xml; do
    [ -f "$f" ] || continue
    cp "$f" "$GMS_DIR/" && COUNT=$((COUNT+1))
done
[ -n "$GMS_UID" ] && chown -R "$GMS_UID:$GMS_UID" "$GMS_DIR"
echo "PREFS_OK $COUNT"
"""
    out = await cmd(client, script.replace("\n", " "), t=30)
    print(f"    Result: {out.strip()}")
    time.sleep(D)

    # ── Step 5: Restore GMS databases ──
    print("\n[5] GMS databases")
    script = f"""
GMS_UID=$(dumpsys package com.google.android.gms 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
GMS_DB="/data/data/com.google.android.gms/databases"
mkdir -p "$GMS_DB"
COUNT=0
for f in {TMP}/data/gms_databases/*; do
    [ -f "$f" ] || continue
    cp "$f" "$GMS_DB/" && COUNT=$((COUNT+1))
done
[ -n "$GMS_UID" ] && chown -R "$GMS_UID:$GMS_UID" "$GMS_DB"
echo "DB_OK $COUNT"
"""
    out = await cmd(client, script.replace("\n", " "), t=30)
    print(f"    Result: {out.strip()}")
    time.sleep(D)

    # ── Step 6: Restore GSF data ──
    print("\n[6] GSF data")
    script = f"""
GSF_UID=$(dumpsys package com.google.android.gsf 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
am force-stop com.google.android.gsf 2>/dev/null
mkdir -p /data/data/com.google.android.gsf/databases /data/data/com.google.android.gsf/shared_prefs
for f in {TMP}/data/gsf_data/*.db {TMP}/data/gsf_data/*.db-journal; do [ -f "$f" ] && cp "$f" /data/data/com.google.android.gsf/databases/; done
for f in {TMP}/data/gsf_data/*.xml; do [ -f "$f" ] && cp "$f" /data/data/com.google.android.gsf/shared_prefs/; done
[ -n "$GSF_UID" ] && chown -R "$GSF_UID:$GSF_UID" /data/data/com.google.android.gsf/
echo "GSF_OK"
"""
    out = await cmd(client, script.replace("\n", " "), t=30)
    print(f"    Result: {out.strip()}")
    time.sleep(D)

    # ── Step 7: Restore account databases ──
    print("\n[7] Account databases")
    script = f"""
DONE=0
if [ -f {TMP}/data/gms_accounts/data_system_ce_0_accounts_ce.db ]; then
    cp {TMP}/data/gms_accounts/data_system_ce_0_accounts_ce.db /data/system_ce/0/accounts_ce.db 2>/dev/null
    chown 1000:1000 /data/system_ce/0/accounts_ce.db && chmod 600 /data/system_ce/0/accounts_ce.db && DONE=$((DONE+1))
fi
if [ -f {TMP}/data/gms_accounts/data_system_de_0_accounts_de.db ]; then
    cp {TMP}/data/gms_accounts/data_system_de_0_accounts_de.db /data/system_de/0/accounts_de.db 2>/dev/null
    chown 1000:1000 /data/system_de/0/accounts_de.db && chmod 600 /data/system_de/0/accounts_de.db && DONE=$((DONE+1))
fi
echo "ACCT_OK $DONE"
"""
    out = await cmd(client, script.replace("\n", " "), t=30)
    print(f"    Result: {out.strip()}")
    time.sleep(D)

    # ── Step 8: Restore Telegram session ──
    print("\n[8] Telegram session")
    script = f"""
TG_PKG=""
for p in org.telegram.messenger.web org.telegram.messenger; do pm list packages 2>/dev/null | grep -q "$p" && TG_PKG="$p" && break; done
if [ -n "$TG_PKG" ] && [ -d {TMP}/data/telegram_session ]; then
    TG_UID=$(dumpsys package "$TG_PKG" 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
    am force-stop "$TG_PKG" 2>/dev/null
    TG_F="/data/data/$TG_PKG/files"
    mkdir -p "$TG_F"
    [ -f {TMP}/data/telegram_session/tgnet.dat ] && cp {TMP}/data/telegram_session/tgnet.dat "$TG_F/"
    [ -f {TMP}/data/telegram_session/cache4.db ] && cp {TMP}/data/telegram_session/cache4.db "$TG_F/"
    for n in 1 2 3; do
        if [ -d {TMP}/data/telegram_session/account$n ]; then
            mkdir -p "$TG_F/account$n"
            cp {TMP}/data/telegram_session/account$n/* "$TG_F/account$n/" 2>/dev/null
        fi
    done
    [ -n "$TG_UID" ] && chown -R "$TG_UID:$TG_UID" "$TG_F"
    echo "TG_OK $TG_PKG"
else
    echo "TG_SKIP"
fi
"""
    out = await cmd(client, script.replace("\n", " "), t=30)
    print(f"    Result: {out.strip()}")
    time.sleep(D)

    # ── Step 9: Restore Chrome data ──
    print("\n[9] Chrome data")
    script = f"""
CHROME_UID=$(dumpsys package com.android.chrome 2>/dev/null | grep "userId=" | head -1 | sed 's/.*userId=//;s/ .*//')
am force-stop com.android.chrome 2>/dev/null
CD="/data/data/com.android.chrome/app_chrome/Default"
mkdir -p "$CD"
[ -f {TMP}/data/chrome_data/Login_Data.db ] && cp {TMP}/data/chrome_data/Login_Data.db "$CD/Login Data"
[ -f {TMP}/data/chrome_data/Cookies.db ] && cp {TMP}/data/chrome_data/Cookies.db "$CD/Cookies"
[ -f {TMP}/data/chrome_data/History.db ] && cp {TMP}/data/chrome_data/History.db "$CD/History"
[ -f {TMP}/data/chrome_data/Web_Data.db ] && cp {TMP}/data/chrome_data/Web_Data.db "$CD/Web Data"
[ -n "$CHROME_UID" ] && chown -R "$CHROME_UID:$CHROME_UID" /data/data/com.android.chrome/
echo "CHROME_OK"
"""
    out = await cmd(client, script.replace("\n", " "), t=30)
    print(f"    Result: {out.strip()}")
    time.sleep(D)

    # ── Step 10: Download + restore app data ──
    print("\n[10] App data restoration")
    # Read manifest
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "tmp", "deploy_bundle", "files", "manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)

    for pkg, info in sorted(manifest["apps"].items()):
        if "data" not in info:
            continue

        # Check if package is installed
        time.sleep(D)
        chk = await cmd(client, f"pm list packages 2>/dev/null | grep -c {pkg}")
        if chk.strip() != "1":
            print(f"    {pkg}: not installed, skip data")
            continue

        data_name = info["data"]
        expected_size = info["data_size"]
        data_path = f"{TMP}/data/{data_name}"

        print(f"    {pkg}: downloading data ({expected_size/1048576:.1f}MB)...", end=" ", flush=True)
        await fire(client, f"nohup curl -s -o {data_path} {URL}/{data_name} >/dev/null 2>&1 &")
        sz = await wait_for_file(client, data_path, expected_size, pkg)

        if sz == 0:
            print(f"    {pkg}: data download failed")
            continue

        time.sleep(D)
        # Force stop, extract, fix ownership
        await cmd(client, f"am force-stop {pkg} 2>/dev/null")
        time.sleep(D)

        restore = (
            f'mkdir -p /data/data/{pkg} && '
            f'cd /data/data/{pkg}/ && '
            f'tar xzf {data_path} 2>/dev/null; '
            f'PKG_UID=$(dumpsys package {pkg} 2>/dev/null | grep userId= | head -1 | sed "s/.*userId=//;s/ .*//"); '
            f'[ -n "$PKG_UID" ] && chown -R $PKG_UID:$PKG_UID /data/data/{pkg}/ 2>/dev/null; '
            f'echo RESTORED'
        )
        out = await cmd(client, restore, t=30)
        if "RESTORED" in out:
            print(f"    {pkg}: data restored ✓")
        else:
            print(f"    {pkg}: data restore failed: {out[:100]}")

        # Cleanup
        await cmd(client, f"rm -f {data_path}")
        time.sleep(D)

    # ── Step 11: Restart services ──
    print("\n[11] Restarting services...")
    await cmd(client, "am force-stop com.google.android.gms; am force-stop com.google.android.gsf")
    time.sleep(D)
    await cmd(client, "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null")
    time.sleep(D)
    await cmd(client, "am startservice com.google.android.gms/.chimera.GmsIntentOperationService 2>/dev/null || true")
    time.sleep(D)

    # ── Step 12: Verification ──
    print("\n" + "=" * 60)
    print("  VERIFICATION")
    print("=" * 60)

    # Packages
    time.sleep(D)
    pkgs = await cmd(client, 'pm list packages 2>/dev/null | grep -E "revolut|telegram|apkpure|chrome|vending|gms|gsf"')
    print(f"\n  Packages:\n{pkgs.strip()}")

    # Accounts
    time.sleep(D)
    accts = await cmd(client, 'dumpsys account 2>/dev/null | grep -E "Account \\{|name=" | head -10')
    print(f"\n  Accounts:\n  {accts.strip() if accts.strip() else '(none)'}")

    # GMS prefs
    time.sleep(D)
    prefs = await cmd(client, "ls /data/data/com.google.android.gms/shared_prefs/*.xml 2>/dev/null | wc -l")
    print(f"\n  GMS prefs: {prefs.strip()} files")

    # GMS dbs
    time.sleep(D)
    dbs = await cmd(client, "ls /data/data/com.google.android.gms/databases/ 2>/dev/null | wc -l")
    print(f"  GMS databases: {dbs.strip()} files")

    # Cleanup
    await cmd(client, f"rm -rf {TMP}/apks {TMP}/data")

    print("\n  ✓ CONTINUATION DEPLOY COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
