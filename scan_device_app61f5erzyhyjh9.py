#!/usr/bin/env python3
"""
Device Scan for APP61F5ERZYHYJH9
Scans the VMOS Cloud device to understand current state, installed apps, and system properties.
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# Configuration
DEVICE_ID = "APP61F5ERZYHYJH9"
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE_URL = "https://api.vmoscloud.com"

async def sh(client, pad, cmd, label="", timeout=30):
    """Execute shell command with proper polling."""
    r = await client.async_adb_cmd([pad], cmd)
    if r.get("code") != 200:
        print(f"  [{label}] FAILED to submit (code={r.get('code')})")
        return ""
    data = r.get("data", [])
    if not data:
        return ""
    task_id = data[0].get("taskId")
    if not task_id:
        return ""
    
    for _ in range(timeout):
        await asyncio.sleep(1)
        d = await client.task_detail([task_id])
        if d.get("code") == 200:
            items = d.get("data", [])
            if items and items[0].get("taskStatus") == 3:
                return items[0].get("taskResult", "")
            if items and items[0].get("taskStatus", 0) < 0:
                return ""
    return ""

async def scan_device():
    """Scan device to understand current state."""
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
    
    print("\n" + "="*70)
    print(f"DEVICE SCAN: {DEVICE_ID}")
    print("="*70)
    print(f"Started: {datetime.now().isoformat()}")
    print("="*70 + "\n")
    
    results = {
        "device_id": DEVICE_ID,
        "scan_time": datetime.now().isoformat(),
        "device_info": {},
        "installed_apps": [],
        "system_properties": {},
        "data_presence": {},
    }
    
    # Stage 1: Device Verification
    print("[STAGE 1] Device Verification")
    print("-" * 50)
    try:
        response = await client.instance_list()
        page_data = response.get("data", {}).get("pageData", [])
        
        device_found = False
        for device in page_data:
            if device.get("padCode") == DEVICE_ID:
                device_found = True
                status = device.get("padStatus", 0)
                print(f"✓ Device located: {DEVICE_ID}")
                print(f"  Status: {status} ({'RUNNING' if status == 10 else 'NOT RUNNING'})")
                print(f"  Grade: {device.get('padGrade', 'N/A')}")
                print(f"  Template: {device.get('realPhoneTemplateId', 'N/A')}")
                print(f"  IP: {device.get('deviceIp', 'N/A')}")
                
                results["device_info"] = {
                    "status": status,
                    "grade": device.get('padGrade'),
                    "template": device.get('realPhoneTemplateId'),
                    "ip": device.get('deviceIp'),
                }
                break
        
        if not device_found:
            print(f"✗ Device {DEVICE_ID} not found!")
            return None
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return None
    
    print("[STAGE 1] ✓ COMPLETE\n")
    
    # Stage 2: Critical Apps Check
    print("[STAGE 2] Critical Apps Check")
    print("-" * 50)
    critical_apps = {
        "com.google.android.gms": "Google Play Services",
        "com.android.vending": "Google Play Store",
        "com.google.android.apps.walletnfcrel": "Google Wallet",
        "com.google.android.gm": "Gmail",
        "com.android.chrome": "Chrome",
    }
    
    for pkg, name in critical_apps.items():
        cmd = f"pm path {pkg} 2>/dev/null"
        out = await sh(client, DEVICE_ID, cmd, f"check_{pkg}", timeout=15)
        if out and "package:" in out:
            print(f"  ✓ {name} ({pkg}) - INSTALLED")
            results["installed_apps"].append(pkg)
        else:
            print(f"  ✗ {name} ({pkg}) - NOT INSTALLED")
        await asyncio.sleep(2)
    
    print("[STAGE 2] ✓ COMPLETE\n")
    
    # Stage 3: System Properties
    print("[STAGE 3] System Properties")
    print("-" * 50)
    cmd = "getprop ro.product.model && getprop ro.product.brand && getprop ro.build.fingerprint && settings get secure android_id"
    out = await sh(client, DEVICE_ID, cmd, "props", timeout=30)
    if out:
        print("✓ System properties:")
        for line in out.strip().split("\n"):
            print(f"  {line}")
    else:
        print("  ⚠ Could not retrieve properties")
    
    print("[STAGE 3] ✓ COMPLETE\n")
    
    # Stage 4: Google Account Check
    print("[STAGE 4] Google Account Check")
    print("-" * 50)
    cmd = "dumpsys account 2>/dev/null"
    out = await sh(client, DEVICE_ID, cmd, "accounts", timeout=30)
    if out:
        print("✓ Account state:")
        for line in out.strip().split("\n")[:15]:
            print(f"  {line}")
    else:
        print("  ⚠ Could not retrieve account info")
    
    print("[STAGE 4] ✓ COMPLETE\n")
    
    # Save results
    report_file = f"/tmp/device_scan_{DEVICE_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print("="*70)
    print("SCAN COMPLETE")
    print(f"Report saved: {report_file}")
    print("="*70 + "\n")
    
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(scan_device())
        sys.exit(0 if results else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Scan failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
