#!/usr/bin/env python3
"""
Use existing device databases as template - modify only account data
"""

import asyncio
import sqlite3
import tempfile
import os
import base64
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP5AU4BB1QQBHNA"
EMAIL = "harshaf019@gmail.com"
DISPLAY_NAME = "Isuru"
PASSWORD = "Isuru@Rome"
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE_URL = "https://api.vmoscloud.com"
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

async def use_existing_db_template():
    global client
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    print(f"\n{'='*70}")
    print(f"USING EXISTING DATABASE TEMPLATE")
    print(f"{'='*70}\n")
    
    # Modify databases directly on device (no extraction needed)
    print("\n[2] Modifying databases directly on device...")
    
    # First, stop services
    print("  Stopping Google services...")
    await sh("am force-stop com.google.android.gms && am force-stop com.android.vending && am force-stop com.android.chrome", "stop")
    await asyncio.sleep(CMD_DELAY)
    
    # Backup current databases
    print("  Backing up current databases...")
    await sh("cp /data/system_ce/0/accounts_ce.db /data/local/tmp/accounts_ce_backup.db", "backup_ce")
    await asyncio.sleep(CMD_DELAY)
    await sh("cp /data/system_de/0/accounts_de.db /data/local/tmp/accounts_de_backup.db", "backup_de")
    await asyncio.sleep(CMD_DELAY)
    print("  ✓ Backups created")
    
    # Modify accounts_ce.db using sqlite3 on device
    print("  Modifying accounts_ce.db...")
    # Delete existing accounts and insert new one
    await sh("sqlite3 /data/system_ce/0/accounts_ce.db 'DELETE FROM accounts;'", "del_accounts")
    await asyncio.sleep(CMD_DELAY)
    await sh("sqlite3 /data/system_ce/0/accounts_ce.db 'DELETE FROM authtokens;'", "del_tokens")
    await asyncio.sleep(CMD_DELAY)
    await sh("sqlite3 /data/system_ce/0/accounts_ce.db 'DELETE FROM extras;'", "del_extras")
    await asyncio.sleep(CMD_DELAY)
    await sh("sqlite3 /data/system_ce/0/accounts_ce.db 'DELETE FROM grants;'", "del_grants")
    await asyncio.sleep(CMD_DELAY)
    await sh("sqlite3 /data/system_ce/0/accounts_ce.db 'DELETE FROM shared_accounts;'", "del_shared")
    await asyncio.sleep(CMD_DELAY)
    
    await sh(f"sqlite3 /data/system_ce/0/accounts_ce.db \"INSERT INTO accounts (name, type, password) VALUES ('{EMAIL}', 'com.google', '{PASSWORD}');\"", "insert_account")
    await asyncio.sleep(CMD_DELAY)
    
    await sh(f"sqlite3 /data/system_ce/0/accounts_ce.db \"INSERT INTO extras (accounts_id, key, value) VALUES (1, 'account_name', '{DISPLAY_NAME}');\"", "insert_name")
    await asyncio.sleep(CMD_DELAY)
    
    await sh("sqlite3 /data/system_ce/0/accounts_ce.db \"INSERT INTO extras (accounts_id, key, value) VALUES (1, 'account_type', 'com.google');\"", "insert_type")
    await asyncio.sleep(CMD_DELAY)
    print("  ✓ accounts_ce.db modified")
    
    # Modify accounts_de.db
    print("  Modifying accounts_de.db...")
    await sh("sqlite3 /data/system_de/0/accounts_de.db 'DELETE FROM accounts;'", "del_de_accounts")
    await asyncio.sleep(CMD_DELAY)
    await sh("sqlite3 /data/system_de/0/accounts_de.db 'DELETE FROM ce_accounts;'", "del_ce_accounts")
    await asyncio.sleep(CMD_DELAY)
    
    await sh(f"sqlite3 /data/system_de/0/accounts_de.db \"INSERT INTO accounts (name, type) VALUES ('{EMAIL}', 'com.google');\"", "insert_de_account")
    await asyncio.sleep(CMD_DELAY)
    await sh("sqlite3 /data/system_de/0/accounts_de.db \"INSERT INTO ce_accounts (_id, ce_accounts_password) VALUES (1, '');\"", "insert_ce_account")
    await asyncio.sleep(CMD_DELAY)
    print("  ✓ accounts_de.db modified")
    
    # Keep system permissions
    print("\n[3] Setting system-compatible permissions...")
    await sh("chown system:system /data/system_ce/0/accounts_ce.db && chmod 660 /data/system_ce/0/accounts_ce.db", "perms_ce")
    await asyncio.sleep(CMD_DELAY)
    await sh("chown system:system /data/system_de/0/accounts_de.db && chmod 660 /data/system_de/0/accounts_de.db", "perms_de")
    await asyncio.sleep(CMD_DELAY)
    
    print("\n[4] Skipping restart (user will restart manually)")
    print(f"\n{'='*70}")
    print("INJECTION COMPLETE")
    print(f"{'='*70}")
    print(f"Account: {EMAIL}")
    print(f"Display Name: {DISPLAY_NAME}")
    print(f"Next: Restart device manually in VMOS Cloud console")
    print(f"{'='*70}")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(use_existing_db_template())
    exit(0 if success else 1)
