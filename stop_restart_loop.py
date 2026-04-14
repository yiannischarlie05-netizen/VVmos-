#!/usr/bin/env python3
"""
Check and stop device APP5AU4BB1QQBHNA if stuck in restart loop
"""

import asyncio
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP5AU4BB1QQBHNA"
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE_URL = "https://api.vmoscloud.com"

async def check_and_stop_device():
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    print(f"\n{'='*70}")
    print(f"CHECKING DEVICE STATUS: {PAD}")
    print(f"{'='*70}")
    
    # Check current status
    print("\n[1] Checking current status...")
    try:
        list_resp = await client.instance_list(page=1, rows=100)
        if list_resp.get("code") == 200:
            instances = list_resp.get("data", {}).get("pageData", [])
            for inst in instances:
                if inst.get("padCode") == PAD:
                    status_code = inst.get("padStatus")
                    status_map = {
                        10: "RUNNING",
                        11: "RESTARTING (STUCK)",
                        14: "ABNORMAL",
                        20: "STOPPED"
                    }
                    status_str = status_map.get(status_code, f"UNKNOWN({status_code})")
                    print(f"  Status: {status_str} (code={status_code})")
                    
                    if status_code == 11:
                        print("\n  Device is STUCK in restart loop!")
                        print("  Attempting to stop device...")
                        
                        # Try to stop device
                        stop_resp = await client.instance_restart([PAD])
                        print(f"  Restart response: code={stop_resp.get('code')}, msg={stop_resp.get('msg')}")
                        
                        # Wait and check again
                        print("  Waiting 10 seconds...")
                        await asyncio.sleep(10)
                        
                        list_resp2 = await client.instance_list(page=1, rows=100)
                        if list_resp2.get("code") == 200:
                            instances2 = list_resp2.get("data", {}).get("pageData", [])
                            for inst2 in instances2:
                                if inst2.get("padCode") == PAD:
                                    status_code2 = inst2.get("padStatus")
                                    print(f"  Status after restart: {status_code2}")
                                    if status_code2 == 11:
                                        print("\n  Device still stuck. Trying factory reset...")
                                        reset_resp = await client.one_key_new_device([PAD])
                                        print(f"  Reset response: code={reset_resp.get('code')}, msg={reset_resp.get('msg')}")
                                    break
                    break
    except Exception as e:
        print(f"  Exception: {e}")

if __name__ == "__main__":
    asyncio.run(check_and_stop_device())
