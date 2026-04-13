#!/usr/bin/env python3
"""
Device Recovery Script for APP61F5ERZYHYJH9
Attempts to recover a device stuck in restart (status=11)
"""

import asyncio
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP61F5ERZYHYJH9"
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE_URL = "https://api.vmoscloud.com"

async def recover_device():
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    print(f"\n{'='*70}")
    print(f"DEVICE RECOVERY: {PAD}")
    print(f"{'='*70}")
    
    # Check current status
    print("\n[1] Checking current device status...")
    try:
        list_resp = await client.instance_list(page=1, rows=100)
        if list_resp.get("code") == 200:
            instances = list_resp.get("data", {}).get("list", [])
            for inst in instances:
                if inst.get("padCode") == PAD:
                    status_code = inst.get("status")
                    status_map = {
                        10: "RUNNING",
                        11: "RESTARTING (STUCK)",
                        14: "ABNORMAL",
                        20: "STOPPED"
                    }
                    status_str = status_map.get(status_code, f"UNKNOWN({status_code})")
                    print(f"  Current Status: {status_str} (code={status_code})")
                    print(f"  Template: {inst.get('realPhoneTemplateId')}")
                    print(f"  Image: {inst.get('imageVersion')}")
                    break
    except Exception as e:
        print(f"  Error checking status: {e}")
        return False
    
    # Try method 1: Force restart again
    print("\n[2] Attempting force restart...")
    try:
        restart_resp = await client.instance_restart([PAD])
        print(f"  Response: code={restart_resp.get('code')}, msg={restart_resp.get('msg')}")
        if restart_resp.get("code") == 200:
            print("  Restart command sent successfully")
            print("  Waiting 30 seconds for device to come back online...")
            await asyncio.sleep(30)
        else:
            print("  Restart command failed")
    except Exception as e:
        print(f"  Error during restart: {e}")
    
    # Check if device recovered
    print("\n[3] Checking if device recovered...")
    try:
        list_resp = await client.instance_list(page=1, rows=100)
        if list_resp.get("code") == 200:
            instances = list_resp.get("data", {}).get("list", [])
            for inst in instances:
                if inst.get("padCode") == PAD:
                    status_code = inst.get("status")
                    if status_code == 10:
                        print("  ✓ Device recovered! Status: RUNNING")
                        return True
                    else:
                        print(f"  Device still stuck: status={status_code}")
                        break
    except Exception as e:
        print(f"  Error checking status: {e}")
    
    # Try method 2: One-key new device (reset to factory)
    print("\n[4] Attempting one-key new device (factory reset)...")
    print("  WARNING: This will clear all data including injected account!")
    try:
        reset_resp = await client.one_key_new_device([PAD])
        print(f"  Response: code={reset_resp.get('code')}, msg={reset_resp.get('msg')}")
        if reset_resp.get("code") == 200:
            print("  Reset command sent successfully")
            print("  Waiting 60 seconds for device to reset...")
            await asyncio.sleep(60)
        else:
            print("  Reset command failed")
    except Exception as e:
        print(f"  Error during reset: {e}")
    
    # Check if device recovered after reset
    print("\n[5] Checking if device recovered after reset...")
    try:
        list_resp = await client.instance_list(page=1, rows=100)
        if list_resp.get("code") == 200:
            instances = list_resp.get("data", {}).get("list", [])
            for inst in instances:
                if inst.get("padCode") == PAD:
                    status_code = inst.get("status")
                    if status_code == 10:
                        print("  ✓ Device recovered after reset! Status: RUNNING")
                        print("  NOTE: All data was cleared, need to re-run pipeline")
                        return True
                    else:
                        print(f"  Device still stuck: status={status_code}")
                        break
    except Exception as e:
        print(f"  Error checking status: {e}")
    
    print("\n" + "="*70)
    print("RECOVERY FAILED")
    print("="*70)
    print("Device could not be recovered automatically.")
    print("Please check the device in VMOS Cloud console.")
    return False

if __name__ == "__main__":
    result = asyncio.run(recover_device())
    if result:
        print("\n✓ Device recovered successfully")
    else:
        print("\n✗ Device recovery failed")
