#!/usr/bin/env python3
"""
Check all devices in the account to find if APP61F5ERZYHYJH9 still exists
"""

import asyncio
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE_URL = "https://api.vmoscloud.com"

async def list_all_devices():
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    print(f"\n{'='*70}")
    print(f"LISTING ALL DEVICES IN ACCOUNT")
    print(f"{'='*70}")
    
    # List all instances
    print("\nFetching all instances...")
    try:
        list_resp = await client.instance_list(page=1, rows=100)
        if list_resp.get("code") == 200:
            data = list_resp.get("data", {})
            total = data.get("total", 0)
            instances = data.get("pageData", [])  # Correct key is pageData, not list
            
            print(f"\nTotal devices in account: {total}")
            print(f"Devices in list: {len(instances)}")
            print(f"\n{'='*70}")
            
            for i, inst in enumerate(instances, 1):
                pad_code = inst.get("padCode", "N/A")
                status = inst.get("padStatus", "N/A")  # Correct key is padStatus
                status_map = {
                    10: "RUNNING",
                    11: "RESTARTING",
                    14: "ABNORMAL",
                    20: "STOPPED"
                }
                status_str = status_map.get(status, f"UNKNOWN({status})")
                template = inst.get("realPhoneTemplateId", "N/A")
                image = inst.get("imageVersion", "N/A")
                
                print(f"\n[{i}] Device: {pad_code}")
                print(f"    Status: {status_str} (code={status})")
                print(f"    Template: {template}")
                print(f"    Image: {image}")
                
                if pad_code == "APP61F5ERZYHYJH9":
                    print(f"    *** TARGET DEVICE FOUND ***")
            
            # Check if APP61F5ERZYHYJH9 exists
            target_found = any(inst.get("padCode") == "APP61F5ERZYHYJH9" for inst in instances)
            
            print(f"\n{'='*70}")
            if target_found:
                print("✓ Device APP61F5ERZYHYJH9 EXISTS in account")
            else:
                print("✗ Device APP61F5ERZYHYJH9 NOT FOUND in account")
                print("   The device may have been deleted or the ID is incorrect")
                print(f"\nCurrent devices in account ({len(instances)}):")
                for inst in instances:
                    print(f"   - {inst.get('padCode', 'N/A')} (status={inst.get('status', 'N/A')})")
            print(f"{'='*70}")
            
        else:
            print(f"Error: code={list_resp.get('code')}, msg={list_resp.get('msg')}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(list_all_devices())
