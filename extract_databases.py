#!/usr/bin/env python3
"""
Extract original accounts_ce.db and accounts_de.db from device as template
"""

import asyncio
import base64
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP5AU4BB1QQBHNA"
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

async def extract_databases():
    global client
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    print(f"\n{'='*70}")
    print(f"EXTRACTING ORIGINAL DATABASES FROM DEVICE")
    print(f"{'='*70}\n")
    
    # First, backup the current (injected) databases
    print("[1] Backing up current (injected) databases...")
    ce_b64 = await sh("base64 /data/system_ce/0/accounts_ce.db", "backup_ce")
    if ce_b64:
        with open("/tmp/accounts_ce_injected.b64", "w") as f:
            f.write(ce_b64)
        print(f"  ✓ accounts_ce.db backed up to /tmp/accounts_ce_injected.b64 ({len(ce_b64)} chars)")
    await asyncio.sleep(CMD_DELAY)
    
    de_b64 = await sh("base64 /data/system_de/0/accounts_de.db", "backup_de")
    if de_b64:
        with open("/tmp/accounts_de_injected.b64", "w") as f:
            f.write(de_b64)
        print(f"  ✓ accounts_de.db backed up to /tmp/accounts_de_injected.b64 ({len(de_b64)} chars)")
    await asyncio.sleep(CMD_DELAY)
    
    # Now, reset device to get clean databases
    print("\n[2] Resetting device to get clean databases...")
    print("  Manual reset required - please reset device in VMOS Cloud console")
    print("  Then re-run this script to extract clean databases")
    
    print(f"\n{'='*70}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(extract_databases())
