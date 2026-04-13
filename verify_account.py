#!/usr/bin/env python3
"""
Verify account injection after restart
"""

import asyncio
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP5AU4BB1QQBHNA"
EMAIL = "harshaf019@gmail.com"
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

async def verify():
    global client
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    print(f"\n{'='*70}")
    print(f"VERIFYING ACCOUNT INJECTION AFTER RESTART")
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
    
    # Check dumpsys account
    print("\n[2] Checking dumpsys account...")
    dumpsys = await sh("dumpsys account", "dumpsys")
    if dumpsys:
        print(f"  dumpsys account output:")
        for line in dumpsys.split('\n')[:20]:
            print(f"    {line}")
        
        if EMAIL in dumpsys:
            print(f"\n  ✓ Account {EMAIL} FOUND in dumpsys!")
        else:
            print(f"\n  ✗ Account {EMAIL} NOT found in dumpsys")
    else:
        print(f"  dumpsys account: command failed")
    
    # Check databases
    print("\n[3] Checking databases...")
    ce_check = await sh("sqlite3 /data/system_ce/0/accounts_ce.db 'SELECT name FROM accounts;'", "check_ce")
    if ce_check:
        print(f"  accounts_ce.db accounts: {ce_check.strip()}")
        if EMAIL in ce_check:
            print(f"  ✓ Account found in accounts_ce.db")
        else:
            print(f"  ✗ Account not found in accounts_ce.db")
    else:
        print(f"  accounts_ce.db: sqlite3 command failed")
    
    de_check = await sh("sqlite3 /data/system_de/0/accounts_de.db 'SELECT name FROM accounts;'", "check_de")
    if de_check:
        print(f"  accounts_de.db accounts: {de_check.strip()}")
        if EMAIL in de_check:
            print(f"  ✓ Account found in accounts_de.db")
        else:
            print(f"  ✗ Account not found in accounts_de.db")
    else:
        print(f"  accounts_de.db: sqlite3 command failed")
    
    print(f"\n{'='*70}")
    print("VERIFICATION COMPLETE")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(verify())
