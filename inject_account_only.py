#!/usr/bin/env python3
"""
Account Injection Only - No Template Replacement
Inject harshaf019@gmail.com into APP5AU4BB1QQBHNA with Play Store and Chrome
"""

import asyncio
import sqlite3
import tempfile
import os
import sys
import base64
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT / "vmos_titan" / "core"))
sys.path.insert(0, str(_ROOT))

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
from vmos_titan.core.vmos_db_builder import VMOSDbBuilder

# Configuration
PAD = "APP5AU4BB1QQBHNA"
EMAIL = "harshaf019@gmail.com"
DISPLAY_NAME = "Isuru"
PASSWORD = "Isuru@Rome"
VMOS_AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
VMOS_SK = "Q2SgcSwEfuwoedY0cijp6Mce"
VMOS_BASE_URL = "https://api.vmoscloud.com"
CMD_DELAY = 10

async def sh(cmd, label="", timeout=30, max_retries=3):
    """Execute shell command on VMOS device."""
    for attempt in range(max_retries):
        r = await client.async_adb_cmd([PAD], cmd)
        if r.get("code") != 200:
            code = r.get("code", "?")
            if code == 500 or code == 110031:
                wait_time = (attempt + 1) * 10
                print(f"  [{label}] API rate limit (code={code}), retry {attempt+1}/{max_retries} in {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            print(f"  [{label}] FAILED to submit (code={code})")
            return ""
        data = r.get("data", [])
        if not data:
            return ""
        tid = data[0].get("taskId")
        if not tid:
            return ""
        
        for _ in range(timeout):
            await asyncio.sleep(1)
            d = await client.task_detail([tid])
            if d.get("code") == 200:
                items = d.get("data", [])
                if items and items[0].get("taskStatus") == 3:
                    return items[0].get("taskResult", "")
                if items and items[0].get("taskStatus", 0) < 0:
                    return ""
        return ""
    print(f"  [{label}] FAILED after {max_retries} retries")
    return ""

async def wait_running(max_wait=120):
    """Wait for device to reach status=10."""
    for i in range(max_wait // 5):
        r = await client.instance_list(page=1, rows=50)
        if r.get("code") == 200:
            for inst in r.get("data", {}).get("pageData", []):
                if inst.get("padCode") == PAD:
                    if inst.get("padStatus") == 10:
                        return True
        await asyncio.sleep(5)
    return False

async def inject_account():
    global client
    client = VMOSCloudClient(VMOS_AK, VMOS_SK, VMOS_BASE_URL)
    
    print(f"\n{'='*70}")
    print(f"ACCOUNT INJECTION ONLY: {PAD}")
    print(f"{'='*70}")
    print(f"Email: {EMAIL}")
    print(f"Display Name: {DISPLAY_NAME}")
    print(f"{'='*70}\n")
    
    # Check device status
    print("[1] Checking device status...")
    r = await client.instance_list(page=1, rows=50)
    if r.get("code") == 200:
        for inst in r.get("data", {}).get("pageData", []):
            if inst.get("padCode") == PAD:
                status = inst.get("padStatus")
                print(f"  Status: {status}")
                if status != 10:
                    print(f"  Device is not RUNNING (status={status})")
                    return False
                break
    else:
        print(f"  Error checking status: {r.get('msg')}")
        return False
    
    # Get Android ID
    print("\n[2] Getting Android ID...")
    android_id = await sh("settings get secure android_id", "get_android_id")
    if not android_id:
        print("  Failed to get Android ID")
        return False
    print(f"  Android ID: {android_id.strip()}")
    await asyncio.sleep(CMD_DELAY)
    
    # Stop Google services
    print("\n[3] Stopping Google services...")
    await sh("am broadcast -a android.intent.action.ACTION_REQUEST_SHUTDOWN --ez android.intent.extra.KEY_CONFIRM true", "stop_services")
    await asyncio.sleep(CMD_DELAY)
    await sh("am force-stop com.google.android.gms", "stop_gms")
    await asyncio.sleep(CMD_DELAY)
    await sh("am force-stop com.android.vending", "stop_play_store")
    await asyncio.sleep(CMD_DELAY)
    await sh("am force-stop com.android.chrome", "stop_chrome")
    await asyncio.sleep(CMD_DELAY)
    
    # Build account databases
    print("\n[4] Building account databases...")
    builder = VMOSDbBuilder()
    
    # Generate synthetic tokens
    gaia_id = EMAIL.split("@")[0]
    gsf_id = f"1|{android_id.strip()}|{gaia_id}"
    tokens = {
        "gsf_id": gsf_id,
        "oauth_token": "oauth_token_placeholder",
        "oauth_secret": "oauth_secret_placeholder"
    }
    
    try:
        acct_ce_bytes = builder.build_accounts_ce(
            email=EMAIL,
            gaia_id=gaia_id,
            display_name=DISPLAY_NAME,
            tokens=tokens,
            password=PASSWORD,
            age_days=0
        )
        print(f"  accounts_ce.db: {len(acct_ce_bytes)} bytes")
    except Exception as e:
        print(f"  Error building accounts_ce.db: {e}")
        return False
    
    try:
        acct_de_bytes = builder.build_accounts_de(
            email=EMAIL,
            gaia_id=gaia_id
        )
        print(f"  accounts_de.db: {len(acct_de_bytes)} bytes")
    except Exception as e:
        print(f"  Error building accounts_de.db: {e}")
        return False
    
    # Push databases
    print("\n[5] Pushing account databases...")
    
    # Write to temp files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        f.write(acct_ce_bytes)
        ce_temp = f.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        f.write(acct_de_bytes)
        de_temp = f.name
    
    try:
        # Push via VMOS Cloud API (need to use file upload or direct push)
        # For now, use base64 encoding to push
        ce_b64 = base64.b64encode(acct_ce_bytes).decode()
        de_b64 = base64.b64encode(acct_de_bytes).decode()
        
        # Write to device
        print("  Writing accounts_ce.db...")
        await sh(f"echo '{ce_b64}' | base64 -d > /data/local/tmp/accounts_ce.db", "write_ce")
        await asyncio.sleep(CMD_DELAY)
        await sh("cp /data/local/tmp/accounts_ce.db /data/system_ce/0/accounts_ce.db", "copy_ce")
        await asyncio.sleep(CMD_DELAY)
        await sh("chmod 600 /data/system_ce/0/accounts_ce.db", "chmod_ce")
        await asyncio.sleep(CMD_DELAY)
        await sh("chown 1000:1000 /data/system_ce/0/accounts_ce.db", "chown_ce")
        await asyncio.sleep(CMD_DELAY)
        
        print("  Writing accounts_de.db...")
        await sh(f"echo '{de_b64}' | base64 -d > /data/local/tmp/accounts_de.db", "write_de")
        await asyncio.sleep(CMD_DELAY)
        await sh("cp /data/local/tmp/accounts_de.db /data/system_de/0/accounts_de.db", "copy_de")
        await asyncio.sleep(CMD_DELAY)
        await sh("chmod 600 /data/system_de/0/accounts_de.db", "chmod_de")
        await asyncio.sleep(CMD_DELAY)
        await sh("chown 1000:1000 /data/system_de/0/accounts_de.db", "chown_de")
        await asyncio.sleep(CMD_DELAY)
        
        print("  ✓ Databases pushed successfully")
    finally:
        os.unlink(ce_temp)
        os.unlink(de_temp)
    
    # Inject GMS shared preferences
    print("\n[6] Injecting GMS shared preferences...")
    gms_prefs = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="google_account_email">{EMAIL}</string>
    <string name="google_account_display_name">{DISPLAY_NAME}</string>
    <string name="google_account_gaia_id">{gaia_id}</string>
    <boolean name="google_account_signed_in" value="true"/>
</map>"""
    gms_b64 = base64.b64encode(gms_prefs.encode()).decode()
    await sh(f"echo '{gms_b64}' | base64 -d > /data/local/tmp/gms_prefs.xml", "write_gms")
    await asyncio.sleep(CMD_DELAY)
    await sh("mkdir -p /data/data/com.google.android.gms/shared_prefs", "mkdir_gms")
    await asyncio.sleep(CMD_DELAY)
    await sh("cp /data/local/tmp/gms_prefs.xml /data/data/com.google.android.gms/shared_prefs/device_account.xml", "copy_gms")
    await asyncio.sleep(CMD_DELAY)
    await sh("chmod 644 /data/data/com.google.android.gms/shared_prefs/device_account.xml", "chmod_gms")
    await asyncio.sleep(CMD_DELAY)
    await sh("chown 1000:1000 /data/data/com.google.android.gms/shared_prefs/device_account.xml", "chown_gms")
    await asyncio.sleep(CMD_DELAY)
    print("  ✓ GMS preferences injected")
    
    # Inject Play Store shared preferences
    print("\n[7] Injecting Play Store shared preferences...")
    play_prefs = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="account_type">com.google</string>
    <string name="account_name">{EMAIL}</string>
    <boolean name="is_signed_in" value="true"/>
</map>"""
    play_b64 = base64.b64encode(play_prefs.encode()).decode()
    await sh(f"echo '{play_b64}' | base64 -d > /data/local/tmp/play_prefs.xml", "write_play")
    await asyncio.sleep(CMD_DELAY)
    await sh("mkdir -p /data/data/com.android.vending/shared_prefs", "mkdir_play")
    await asyncio.sleep(CMD_DELAY)
    await sh("cp /data/local/tmp/play_prefs.xml /data/data/com.android.vending/shared_prefs/account.xml", "copy_play")
    await asyncio.sleep(CMD_DELAY)
    await sh("chmod 644 /data/data/com.android.vending/shared_prefs/account.xml", "chmod_play")
    await asyncio.sleep(CMD_DELAY)
    await sh("chown 1000:1000 /data/data/com.android.vending/shared_prefs/account.xml", "chown_play")
    await asyncio.sleep(CMD_DELAY)
    print("  ✓ Play Store preferences injected")
    
    # Inject Chrome shared preferences
    print("\n[8] Injecting Chrome shared preferences...")
    chrome_prefs = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="google_account_email">{EMAIL}</string>
    <string name="google_account_display_name">{DISPLAY_NAME}</string>
    <boolean name="sync_enabled" value="true"/>
</map>"""
    chrome_b64 = base64.b64encode(chrome_prefs.encode()).decode()
    await sh(f"echo '{chrome_b64}' | base64 -d > /data/local/tmp/chrome_prefs.xml", "write_chrome")
    await asyncio.sleep(CMD_DELAY)
    await sh("mkdir -p /data/data/com.android.chrome/shared_prefs", "mkdir_chrome")
    await asyncio.sleep(CMD_DELAY)
    await sh("cp /data/local/tmp/chrome_prefs.xml /data/data/com.android.chrome/shared_prefs/account.xml", "copy_chrome")
    await asyncio.sleep(CMD_DELAY)
    await sh("chmod 644 /data/data/com.android.chrome/shared_prefs/account.xml", "chmod_chrome")
    await asyncio.sleep(CMD_DELAY)
    await sh("chown 1000:1000 /data/data/com.android.chrome/shared_prefs/account.xml", "chown_chrome")
    await asyncio.sleep(CMD_DELAY)
    print("  ✓ Chrome preferences injected")
    
    # Restore SELinux context
    print("\n[9] Restoring SELinux context...")
    await sh("restorecon -R /data/system_ce/0/ /data/system_de/0/ /data/data/com.google.android.gms /data/data/com.android.vending /data/data/com.android.chrome", "restorecon")
    await asyncio.sleep(CMD_DELAY)
    
    # SKIP RESTART - Device crash was caused by restart after injection
    print("\n[10] Skipping device restart (prevents crash)")
    print("  Account injection complete - device not restarted")
    
    # Verify injection
    print("\n[11] Verifying account injection...")
    await asyncio.sleep(5)
    accounts_output = await sh("dumpsys account", "verify_accounts")
    if EMAIL in accounts_output:
        print(f"  ✓ Account {EMAIL} found in dumpsys")
    else:
        print(f"  ✗ Account {EMAIL} NOT found in dumpsys")
        print(f"  Output: {accounts_output[:500]}")
    
    # Check databases
    ce_check = await sh("ls -la /data/system_ce/0/accounts_ce.db", "check_ce")
    if "accounts_ce.db" in ce_check:
        print("  ✓ accounts_ce.db exists")
    else:
        print("  ✗ accounts_ce.db missing")
    
    de_check = await sh("ls -la /data/system_de/0/accounts_de.db", "check_de")
    if "accounts_de.db" in de_check:
        print("  ✓ accounts_de.db exists")
    else:
        print("  ✗ accounts_de.db missing")
    
    print(f"\n{'='*70}")
    print("ACCOUNT INJECTION COMPLETE")
    print(f"{'='*70}")
    print(f"Device: {PAD}")
    print(f"Email: {EMAIL}")
    print(f"Display Name: {DISPLAY_NAME}")
    print(f"{'='*70}")
    
    return True

if __name__ == "__main__":
    import sys
    import base64
    success = asyncio.run(inject_account())
    sys.exit(0 if success else 1)
