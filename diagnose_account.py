#!/usr/bin/env python3
"""
Diagnose why account not appearing after restart
"""

import asyncio
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP5AU4BB1QQBHNA"
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
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

async def diagnose():
    global client
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    print(f"\n{'='*70}")
    print(f"DIAGNOSING ACCOUNT INJECTION FAILURE")
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
                    print(f"  Device not running (status={status})")
                    return
                break
    
    await asyncio.sleep(CMD_DELAY)
    
    # Check if databases exist
    print("\n[2] Checking databases...")
    ce_check = await sh("ls -la /data/system_ce/0/accounts_ce.db", "check_ce")
    print(f"  accounts_ce.db: {ce_check.strip()}")
    await asyncio.sleep(CMD_DELAY)
    
    de_check = await sh("ls -la /data/system_de/0/accounts_de.db", "check_de")
    print(f"  accounts_de.db: {de_check.strip()}")
    await asyncio.sleep(CMD_DELAY)
    
    # Check file permissions
    print("\n[3] Checking file permissions...")
    ce_perms = await sh("stat -c '%a %U:%G' /data/system_ce/0/accounts_ce.db", "ce_perms")
    print(f"  accounts_ce.db permissions: {ce_perms.strip()}")
    await asyncio.sleep(CMD_DELAY)
    
    de_perms = await sh("stat -c '%a %U:%G' /data/system_de/0/accounts_de.db", "de_perms")
    print(f"  accounts_de.db permissions: {de_perms.strip()}")
    await asyncio.sleep(CMD_DELAY)
    
    # Check database integrity
    print("\n[4] Checking database integrity...")
    ce_integrity = await sh("sqlite3 /data/system_ce/0/accounts_ce.db '.schema'", "ce_schema")
    if ce_integrity:
        print(f"  accounts_ce.db schema: {ce_integrity[:200]}")
    else:
        print(f"  accounts_ce.db: sqlite3 command failed (may not be available)")
    await asyncio.sleep(CMD_DELAY)
    
    de_integrity = await sh("sqlite3 /data/system_de/0/accounts_de.db '.schema'", "de_schema")
    if de_integrity:
        print(f"  accounts_de.db schema: {de_integrity[:200]}")
    else:
        print(f"  accounts_de.db: sqlite3 command failed (may not be available)")
    await asyncio.sleep(CMD_DELAY)
    
    # Check account table content
    print("\n[5] Checking account table content...")
    ce_content = await sh("sqlite3 /data/system_ce/0/accounts_ce.db 'SELECT * FROM accounts;'", "ce_content")
    if ce_content:
        print(f"  accounts_ce.db accounts: {ce_content.strip()}")
    else:
        print(f"  accounts_ce.db: sqlite3 command failed")
    await asyncio.sleep(CMD_DELAY)
    
    de_content = await sh("sqlite3 /data/system_de/0/accounts_de.db 'SELECT * FROM accounts;'", "de_content")
    if de_content:
        print(f"  accounts_de.db accounts: {de_content.strip()}")
    else:
        print(f"  accounts_de.db: sqlite3 command failed")
    await asyncio.sleep(CMD_DELAY)
    
    # Check AccountManager logs
    print("\n[6] Checking AccountManager logs...")
    logs = await sh("logcat -d -s AccountManagerService:* 2>/dev/null | tail -50", "logs")
    if logs:
        print(f"  AccountManager logs (last 50 lines):")
        for line in logs.split('\n')[:20]:
            print(f"    {line}")
    else:
        print(f"  AccountManager logs: command failed")
    await asyncio.sleep(CMD_DELAY)
    
    # Check dumpsys account
    print("\n[7] Checking dumpsys account...")
    dumpsys = await sh("dumpsys account", "dumpsys")
    if dumpsys:
        print(f"  dumpsys account output:")
        for line in dumpsys.split('\n')[:15]:
            print(f"    {line}")
    else:
        print(f"  dumpsys account: command failed")
    
    print(f"\n{'='*70}")
    print("DIAGNOSIS COMPLETE")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(diagnose())
