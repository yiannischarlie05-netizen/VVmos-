#!/usr/bin/env python3
"""
Use VMOSFilePusher to extract, modify, and re-inject databases
"""

import asyncio
import sqlite3
import tempfile
import os
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
from vmos_titan.core.vmos_file_pusher import VMOSFilePusher

PAD = "APP5AU4BB1QQBHNA"
EMAIL = "harshaf019@gmail.com"
DISPLAY_NAME = "Isuru"
PASSWORD = "Isuru@Rome"
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE_URL = "https://api.vmoscloud.com"

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

async def pull_file_via_cat(path):
    """Pull file using cat with base64 encoding."""
    cmd = f"cat {path} | base64 -w 0"
    output = await sh(cmd, f"pull_{path}", timeout=60)
    if not output:
        return None
    
    # Clean output
    output = output.strip().replace('\n', '').replace('\r', '')
    try:
        return base64.b64decode(output)
    except:
        return None

async def inject_with_file_pusher():
    global client
    client = VMOSCloudClient(AK, SK, BASE_URL)
    pusher = VMOSFilePusher(client, PAD)
    
    print(f"\n{'='*70}")
    print(f"INJECTING USING VMOSFILEPUSHER")
    print(f"{'='*70}\n")
    
    # Stop services
    print("[1] Stopping Google services...")
    await sh("am force-stop com.google.android.gms && am force-stop com.android.vending && am force-stop com.android.chrome", "stop")
    await asyncio.sleep(10)
    print("  ✓ Services stopped")
    
    # Pull databases
    print("\n[2] Pulling databases from device...")
    ce_bytes = await pull_file_via_cat("/data/system_ce/0/accounts_ce.db")
    if not ce_bytes:
        print("  ✗ Failed to pull accounts_ce.db")
        return False
    print(f"  ✓ accounts_ce.db: {len(ce_bytes)} bytes")
    
    de_bytes = await pull_file_via_cat("/data/system_de/0/accounts_de.db")
    if not de_bytes:
        print("  ✗ Failed to pull accounts_de.db")
        return False
    print(f"  ✓ accounts_de.db: {len(de_bytes)} bytes")
    
    # Modify databases locally
    print("\n[3] Modifying databases locally...")
    
    # Modify accounts_ce.db
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, "wb") as f:
            f.write(ce_bytes)
        
        conn = sqlite3.connect(tmp_path)
        c = conn.cursor()
        
        # Clear existing data
        c.execute("DELETE FROM accounts")
        c.execute("DELETE FROM authtokens")
        c.execute("DELETE FROM extras")
        c.execute("DELETE FROM grants")
        c.execute("DELETE FROM shared_accounts")
        
        # Insert new account
        c.execute(
            "INSERT INTO accounts (name, type, password) VALUES (?, 'com.google', ?)",
            (EMAIL, PASSWORD)
        )
        account_id = c.lastrowid or 1
        
        # Insert extras
        c.execute(
            "INSERT INTO extras (accounts_id, key, value) VALUES (?, 'account_name', ?)",
            (account_id, DISPLAY_NAME)
        )
        c.execute(
            "INSERT INTO extras (accounts_id, key, value) VALUES (?, 'account_type', ?)",
            (account_id, "com.google")
        )
        
        conn.commit()
        conn.close()
        
        # Read modified database
        with open(tmp_path, "rb") as f:
            modified_ce = f.read()
        print(f"  ✓ Modified accounts_ce.db: {len(modified_ce)} bytes")
    finally:
        os.unlink(tmp_path)
    
    # Modify accounts_de.db
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, "wb") as f:
            f.write(de_bytes)
        
        conn = sqlite3.connect(tmp_path)
        c = conn.cursor()
        
        # Clear existing data
        c.execute("DELETE FROM accounts")
        c.execute("DELETE FROM ce_accounts")
        
        # Insert new account
        c.execute(
            "INSERT INTO accounts (name, type) VALUES (?, 'com.google')",
            (EMAIL,)
        )
        account_id = c.lastrowid or 1
        c.execute(
            "INSERT INTO ce_accounts (_id, ce_accounts_password) VALUES (?, '')",
            (account_id,)
        )
        
        conn.commit()
        conn.close()
        
        # Read modified database
        with open(tmp_path, "rb") as f:
            modified_de = f.read()
        print(f"  ✓ Modified accounts_de.db: {len(modified_de)} bytes")
    finally:
        os.unlink(tmp_path)
    
    # Push databases back
    print("\n[4] Pushing databases back using VMOSFilePusher...")
    
    ce_result = await pusher.push_file(
        modified_ce,
        "/data/system_ce/0/accounts_ce.db",
        owner="system:system",
        mode="660"
    )
    if ce_result.success:
        print(f"  ✓ accounts_ce.db pushed successfully")
    else:
        print(f"  ✗ accounts_ce.db push failed: {ce_result.error}")
        return False
    
    de_result = await pusher.push_file(
        modified_de,
        "/data/system_de/0/accounts_de.db",
        owner="system:system",
        mode="660"
    )
    if de_result.success:
        print(f"  ✓ accounts_de.db pushed successfully")
    else:
        print(f"  ✗ accounts_de.db push failed: {de_result.error}")
        return False
    
    print("\n[5] Skipping restart (user will restart manually)")
    print(f"\n{'='*70}")
    print("INJECTION COMPLETE")
    print(f"{'='*70}")
    print(f"Account: {EMAIL}")
    print(f"Display Name: {DISPLAY_NAME}")
    print(f"Next: Restart device manually in VMOS Cloud console")
    print(f"{'='*70}")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(inject_with_file_pusher())
    exit(0 if success else 1)
