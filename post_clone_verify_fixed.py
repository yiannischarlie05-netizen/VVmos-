#!/usr/bin/env python3
"""
Post-clone verification and account visibility fix.
The DBs are injected but AccountManagerService needs a kick.
"""
import asyncio
import os
import sys
import time

os.environ["VMOS_ALLOW_RESTART"] = "1"
sys.path.insert(0, ".")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
TARGET = "ABP63U6H37MV34I0"
BASE_URL = "https://api.vmoscloud.com"

async def cmd(client, sh, timeout=30, retries=3):
    for attempt in range(retries):
        try:
            r = await client.sync_cmd(TARGET, sh, timeout_sec=timeout)
            if r.get("code") == 200:
                data = r.get("data", [])
                if data and isinstance(data, list) and data[0]:
                    return (data[0].get("errorMsg") or "").strip()
                return ""
            elif r.get("code") in (110012, 110031):
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
            return None
        except Exception:
            if attempt < retries - 1:
                await asyncio.sleep(3)
    return None

async def main():
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
    
    print("=== POST-CLONE VERIFICATION ===", flush=True)
    
    # Check DB integrity first
    print("\n[1] DB INTEGRITY", flush=True)
    for db in ["/data/system_ce/0/accounts_ce.db", "/data/system_de/0/accounts_de.db"]:
        out = await cmd(client, f"sqlite3 {db} \"PRAGMA integrity_check\" 2>/dev/null")
        print(f"  {db.split('/')[-1]}: {out}", flush=True)
        out = await cmd(client, f"sqlite3 {db} \"SELECT name FROM accounts\" 2>/dev/null")
        print(f"    accounts: {out}", flush=True)
        await asyncio.sleep(2)
    
    # Check AccountManagerService state
    print("\n[2] ACCOUNT MANAGER", flush=True)
    out = await cmd(client, "dumpsys activity service AccountManagerService | head -20")
    if out:
        for line in out.split("\n")[:15]:
            print(f"    {line}", flush=True)
    await asyncio.sleep(3)
    
    # Broadcast account changes
    print("\n[3] BROADCAST ACCOUNT CHANGES", flush=True)
    broadcasts = [
        "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED",
        "am broadcast -a com.google.android.gms.auth.account.LOGIN_ACCOUNTS_CHANGED",
        "am broadcast -a com.google.android.gms.common.account.CHANGED",
    ]
    for bc in broadcasts:
        out = await cmd(client, bc, retries=1)
        print(f"  {bc}: {out if out else 'OK'}", flush=True)
        await asyncio.sleep(2)
    
    # Restart GMS services
    print("\n[4] RESTART GMS SERVICES", flush=True)
    services = [
        "com.google.android.gms",
        "com.google.android.gsf",
        "com.android.vending",
    ]
    for svc in services:
        out = await cmd(client, f"am force-stop {svc}", retries=1)
        await asyncio.sleep(1)
        out = await cmd(client, f"am startservice -a com.google.android.gms.INIT_SERVICE", retries=1)
        print(f"  {svc}: restarted", flush=True)
        await asyncio.sleep(3)
    
    # Wait and recheck
    print("\n[5] FINAL ACCOUNT CHECK", flush=True)
    await asyncio.sleep(10)
    out = await cmd(client, "dumpsys account 2>/dev/null | head -25")
    if out:
        for line in out.split("\n")[:25]:
            print(f"    {line}", flush=True)
    
    # Test Google account visibility
    print("\n[6] GOOGLE APPS TEST", flush=True)
    for pkg in ["com.google.android.gms", "com.android.vending", "com.google.android.gm"]:
        out = await cmd(client, f"dumpsys package {pkg} | grep -i account | head -5")
        print(f"  {pkg}: {out if out else 'no account refs'}", flush=True)
        await asyncio.sleep(2)
    
    # If still no accounts, try a soft restart
    out = await cmd(client, "dumpsys account | grep -c 'Account {'")
    acct_count = int(out.strip()) if out and out.strip().isdigit() else 0
    print(f"\n  Account count: {acct_count}", flush=True)
    
    if acct_count == 0:
        print("\n[7] SOFT RESTART (no reboot)", flush=True)
        # Stop system_server briefly
        out = await cmd(client, "kill -9 $(pidof system_server) 2>/dev/null && echo KILLED", retries=1)
        print(f"  system_server: {out}", flush=True)
        await asyncio.sleep(15)
        # Check again
        out = await cmd(client, "dumpsys account 2>/dev/null | head -10")
        if out:
            for line in out.split("\n")[:10]:
                print(f"    {line}", flush=True)
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
