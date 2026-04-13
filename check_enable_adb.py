#!/usr/bin/env python3
"""
Check and enable ADB for device APP5AU4BB1QQBHNA
"""

import asyncio
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP5AU4BB1QQBHNA"
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE_URL = "https://api.vmoscloud.com"

async def check_and_enable_adb():
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    print(f"\n{'='*70}")
    print(f"CHECKING ADB STATUS: {PAD}")
    print(f"{'='*70}")
    
    # Check current ADB status
    print("\n[1] Checking current ADB status...")
    try:
        adb_resp = await client.get_adb_info(PAD, enable=False)
        print(f"  Response: code={adb_resp.get('code')}, msg={adb_resp.get('msg')}")
        if adb_resp.get("code") == 200:
            data = adb_resp.get("data", {})
            print(f"  ADB enabled: {data.get('enable')}")
            print(f"  ADB info: {data}")
    except Exception as e:
        print(f"  Exception: {e}")
    
    # Try to enable ADB
    print("\n[2] Enabling ADB...")
    try:
        enable_resp = await client.enable_adb([PAD], enable=True)
        print(f"  Response: code={enable_resp.get('code')}, msg={enable_resp.get('msg')}")
        if enable_resp.get("code") == 200:
            print("  ADB enable command sent successfully")
            print("  Waiting 10 seconds for ADB to initialize...")
            await asyncio.sleep(10)
        else:
            print("  ADB enable command failed")
    except Exception as e:
        print(f"  Exception: {e}")
    
    # Check ADB status again
    print("\n[3] Checking ADB status after enable...")
    try:
        adb_resp = await client.get_adb_info(PAD, enable=False)
        print(f"  Response: code={adb_resp.get('code')}, msg={adb_resp.get('msg')}")
        if adb_resp.get("code") == 200:
            data = adb_resp.get("data", {})
            print(f"  ADB enabled: {data.get('enable')}")
            print(f"  ADB info: {data}")
    except Exception as e:
        print(f"  Exception: {e}")
    
    # Test ADB command
    print("\n[4] Testing ADB command...")
    try:
        test_resp = await client.sync_cmd(PAD, "echo 'adb_test'", timeout_sec=10)
        print(f"  Response: code={test_resp.get('code')}, msg={test_resp.get('msg')}")
        if test_resp.get("code") == 200:
            data = test_resp.get("data", {})
            if isinstance(data, dict):
                output = data.get("taskStatus", "")
            else:
                output = str(data)
            print(f"  Output: {output}")
            print("  ✓ ADB is working!")
        else:
            print("  ✗ ADB command failed")
    except Exception as e:
        print(f"  Exception: {e}")

if __name__ == "__main__":
    asyncio.run(check_and_enable_adb())
