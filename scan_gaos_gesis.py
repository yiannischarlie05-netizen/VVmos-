#!/usr/bin/env python3
"""
Comprehensive Device Scan for GAOS (Google Accounts) and GESIS (Genesis)
Scans device APP61F5ERZYHYJH9 for:
- Google accounts (accounts_ce.db, accounts_de.db)
- Genesis-related files and configurations
- Injected data and wallet databases
"""

import asyncio
import json
import time
from datetime import datetime
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP61F5ERZYHYJH9"
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE_URL = "https://api.vmoscloud.com"

async def scan_device():
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    results = {
        "scan_time": datetime.utcnow().isoformat(),
        "device_id": PAD,
        "gaos": {},  # Google Accounts
        "gesis": {},  # Genesis
        "system": {},
        "wallet": {},
        "apps": {}
    }
    
    print(f"\n{'='*70}")
    print(f"COMPREHENSIVE DEVICE SCAN: {PAD}")
    print(f"{'='*70}")
    
    # Check device status
    print("\n[1] Device Status")
    device_accessible = False
    
    try:
        status_resp = await client.cloud_phone_info(PAD)
        if status_resp.get("code") == 200:
            status_data = status_resp.get("data", {})
            status_code = status_data.get("status")
            status_map = {
                10: "RUNNING",
                11: "RESTARTING",
                20: "STOPPED"
            }
            status_str = status_map.get(status_code, f"UNKNOWN({status_code})")
            print(f"  API Status: {status_str}")
            results["system"]["status"] = status_str
            results["system"]["status_code"] = status_code
            results["system"]["full_status"] = status_data
        else:
            print(f"  cloud_phone_info Error: {status_resp.get('msg')}")
            # Fallback to instance_list
            print("  Trying instance_list as fallback...")
            list_resp = await client.instance_list(page=1, rows=100)
            if list_resp.get("code") == 200:
                instances = list_resp.get("data", {}).get("list", [])
                for inst in instances:
                    if inst.get("padCode") == PAD:
                        status_code = inst.get("status")
                        status_map = {
                            10: "RUNNING",
                            11: "RESTARTING",
                            20: "STOPPED"
                        }
                        status_str = status_map.get(status_code, f"UNKNOWN({status_code})")
                        print(f"  Status (from list): {status_str}")
                        results["system"]["status"] = status_str
                        results["system"]["status_code"] = status_code
                        results["system"]["full_status"] = inst
                        break
            else:
                results["system"]["error"] = list_resp.get("msg")
    except Exception as e:
        print(f"  Exception checking status: {e}")
        results["system"]["exception"] = str(e)
    
    # Try to execute a simple command to check if device is actually accessible
    print("\n  Testing device accessibility...")
    try:
        test_resp = await client.sync_cmd(PAD, "echo 'device_online'", timeout_sec=10)
        if test_resp.get("code") == 200:
            output = test_resp.get("data", {}).get("taskStatus", "")
            if "device_online" in output:
                print("  Device is ACCESSIBLE via sync_cmd")
                device_accessible = True
                results["system"]["accessible"] = True
            else:
                print(f"  Device responded but unexpected output: {output}")
                results["system"]["accessible"] = False
        else:
            print(f"  sync_cmd failed: code={test_resp.get('code')}, msg={test_resp.get('msg')}")
            results["system"]["accessible"] = False
    except Exception as e:
        print(f"  Exception testing accessibility: {e}")
        results["system"]["accessible"] = False
    
    if not device_accessible:
        print("\n  Device is not accessible. Cannot proceed with scan.")
        return results
    
    # Scan Google Accounts (GAOS)
    print("\n[2] Google Accounts (GAOS)")
    
    # Check accounts_ce.db
    print("  Checking accounts_ce.db...")
    try:
        cmd = "ls -la /data/system_ce/0/accounts_ce.db"
        resp = await client.async_adb_cmd([PAD], cmd)
        if resp.get("code") == 0:
            output = resp.get("data", {}).get(PAD, {}).get("output", "")
            print(f"    {output.strip()}")
            results["gaos"]["accounts_ce_exists"] = "accounts_ce.db" in output
        else:
            print(f"    Error: {resp.get('msg')}")
    except Exception as e:
        print(f"    Exception: {e}")
    
    # Check accounts_de.db
    print("  Checking accounts_de.db...")
    try:
        cmd = "ls -la /data/system_de/0/accounts_de.db"
        resp = await client.async_adb_cmd([PAD], cmd)
        if resp.get("code") == 0:
            output = resp.get("data", {}).get(PAD, {}).get("output", "")
            print(f"    {output.strip()}")
            results["gaos"]["accounts_de_exists"] = "accounts_de.db" in output
        else:
            print(f"    Error: {resp.get('msg')}")
    except Exception as e:
        print(f"    Exception: {e}")
    
    # Query accounts via dumpsys
    print("  Querying accounts via dumpsys...")
    try:
        cmd = "dumpsys account"
        resp = await client.async_adb_cmd([PAD], cmd)
        if resp.get("code") == 0:
            output = resp.get("data", {}).get(PAD, {}).get("output", "")
            lines = output.strip().split('\n')
            account_lines = [l for l in lines if 'Accounts:' in l or '@' in l or 'com.google' in l]
            for line in account_lines[:20]:
                print(f"    {line}")
            results["gaos"]["dumpsys_output"] = account_lines
            results["gaos"]["account_count"] = len([l for l in lines if '@' in l])
        else:
            print(f"    Error: {resp.get('msg')}")
    except Exception as e:
        print(f"    Exception: {e}")
    
    # Scan Genesis (GESIS)
    print("\n[3] Genesis (GESIS)")
    
    # Check for Genesis-related files
    genesis_paths = [
        "/data/data/com.google.android.gms/databases/",
        "/data/data/com.android.vending/databases/",
        "/data/data/com.google.android.gm/databases/",
        "/data/user_de/0/com.google.android.gms/",
        "/sdcard/genesis/",
        "/sdcard/titan/"
    ]
    
    for path in genesis_paths:
        print(f"  Checking {path}...")
        try:
            cmd = f"ls -la {path}"
            resp = await client.async_adb_cmd([PAD], cmd)
            if resp.get("code") == 0:
                output = resp.get("data", {}).get(PAD, {}).get("output", "")
                if output.strip():
                    print(f"    Found: {len(output.splitlines())} entries")
                    results["gesis"][path] = "exists"
                else:
                    results["gesis"][path] = "empty"
            else:
                results["gesis"][path] = f"error: {resp.get('msg')}"
        except Exception as e:
            results["gesis"][path] = f"exception: {e}"
    
    # Scan Wallet Databases
    print("\n[4] Wallet Databases")
    
    wallet_paths = [
        "/data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db",
        "/data/data/com.google.android.apps.walletnfcrel/databases/library.db",
        "/data/data/com.android.vending/databases/library.db",
    ]
    
    for path in wallet_paths:
        print(f"  Checking {path}...")
        try:
            cmd = f"ls -la {path}"
            resp = await client.async_adb_cmd([PAD], cmd)
            if resp.get("code") == 0:
                output = resp.get("data", {}).get(PAD, {}).get("output", "")
                if "tapandpay.db" in output or "library.db" in output:
                    print(f"    Found: {output.strip()}")
                    results["wallet"][path] = "exists"
                else:
                    results["wallet"][path] = "not_found"
            else:
                results["wallet"][path] = f"error: {resp.get('msg')}"
        except Exception as e:
            results["wallet"][path] = f"exception: {e}"
    
    # Scan Apps
    print("\n[5] Apps")
    
    target_apps = [
        "com.google.android.gm",  # Gmail
        "com.google.android.apps.walletnfcrel",  # Google Wallet
        "com.android.vending",  # Play Store
        "com.google.android.gms",  # GMS
        "com.android.chrome",  # Chrome
    ]
    
    for app in target_apps:
        print(f"  Checking {app}...")
        try:
            cmd = f"pm list packages | grep {app}"
            resp = await client.async_adb_cmd([PAD], cmd)
            if resp.get("code") == 0:
                output = resp.get("data", {}).get(PAD, {}).get("output", "")
                if app in output:
                    print(f"    Installed")
                    results["apps"][app] = "installed"
                else:
                    print(f"    Not installed")
                    results["apps"][app] = "not_installed"
            else:
                results["apps"][app] = f"error: {resp.get('msg')}"
        except Exception as e:
            results["apps"][app] = f"exception: {e}"
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/tmp/gaos_gesis_scan_{PAD}_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Scan complete. Results saved to: {output_file}")
    print(f"{'='*70}")
    
    return results

if __name__ == "__main__":
    asyncio.run(scan_device())
