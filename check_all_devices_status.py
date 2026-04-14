#!/usr/bin/env python3
"""
Check all devices in account for restart loop
"""

import asyncio
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE_URL = "https://api.vmoscloud.com"

async def check_all_devices():
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    print(f"\n{'='*70}")
    print(f"CHECKING ALL DEVICES FOR RESTART LOOP")
    print(f"{'='*70}")
    
    list_resp = await client.instance_list(page=1, rows=100)
    if list_resp.get("code") == 200:
        instances = list_resp.get("data", {}).get("pageData", [])
        print(f"\nTotal devices: {len(instances)}\n")
        
        for inst in instances:
            pad_code = inst.get("padCode")
            status_code = inst.get("padStatus")
            status_map = {
                10: "RUNNING",
                11: "RESTARTING (STUCK)",
                14: "ABNORMAL",
                20: "STOPPED"
            }
            status_str = status_map.get(status_code, f"UNKNOWN({status_code})")
            
            print(f"Device: {pad_code}")
            print(f"  Status: {status_str} (code={status_code})")
            print(f"  Template: {inst.get('realPhoneTemplateId')}")
            print(f"  Image: {inst.get('imageVersion')}")
            
            if status_code == 11:
                print(f"  ⚠️  THIS DEVICE IS STUCK IN RESTART!")
            print()
    else:
        print(f"Error: {list_resp.get('msg')}")

if __name__ == "__main__":
    asyncio.run(check_all_devices())
