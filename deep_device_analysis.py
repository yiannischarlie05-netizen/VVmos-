#!/usr/bin/env python3
"""
Deep Device Analysis for APP5AU4BB1QQBHNA
Comprehensive environment analysis and gap identification
"""

import asyncio
import json
from datetime import datetime
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP5AU4BB1QQBHNA"
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE_URL = "https://api.vmoscloud.com"

async def run_command(client, cmd, description):
    """Run a command and return result with description."""
    try:
        resp = await client.sync_cmd(PAD, cmd, timeout_sec=15)
        if resp.get("code") == 200:
            data = resp.get("data", {})
            # Handle both dict and list responses
            if isinstance(data, dict):
                output = data.get("taskStatus", "")
            elif isinstance(data, list):
                output = str(data) if data else ""
            else:
                output = str(data)
            return {"status": "success", "output": output, "description": description}
        else:
            return {"status": "error", "code": resp.get("code"), "msg": resp.get("msg"), "description": description}
    except Exception as e:
        return {"status": "exception", "error": str(e), "description": description}

async def analyze_device():
    client = VMOSCloudClient(AK, SK, BASE_URL)
    
    results = {
        "scan_time": datetime.utcnow().isoformat(),
        "device_id": PAD,
        "summary": {},
        "device_info": {},
        "system_properties": {},
        "installed_apps": {},
        "google_accounts": {},
        "filesystem": {},
        "capabilities": {},
        "genesis_readiness": {},
        "gaps": []
    }
    
    print(f"\n{'='*70}")
    print(f"DEEP DEVICE ANALYSIS: {PAD}")
    print(f"{'='*70}")
    
    # 1. Device Info
    print("\n[1] Device Information")
    try:
        info_resp = await client.cloud_phone_info(PAD)
        if info_resp.get("code") == 200:
            info = info_resp.get("data", {})
            results["device_info"] = info
            print(f"  Status: {info.get('status')} ({info.get('padStatus')})")
            print(f"  Template: {info.get('realPhoneTemplateId')}")
            print(f"  Image: {info.get('imageVersion')}")
            print(f"  Type: {info.get('padType')}")
            print(f"  Grade: {info.get('padGrade')}")
            print(f"  Screen: {info.get('screenLayoutCode')}")
            results["summary"]["device_status"] = info.get('padStatus')
        else:
            print(f"  Error: {info_resp.get('msg')}")
            results["gaps"].append("Cannot retrieve device info")
    except Exception as e:
        print(f"  Exception: {e}")
        results["gaps"].append(f"Device info exception: {e}")
    
    # 2. System Properties
    print("\n[2] System Properties")
    props_to_check = [
        ("ro.product.model", "Device Model"),
        ("ro.product.brand", "Device Brand"),
        ("ro.product.manufacturer", "Manufacturer"),
        ("ro.build.version.release", "Android Version"),
        ("ro.build.version.sdk", "SDK Version"),
        ("ro.build.fingerprint", "Build Fingerprint"),
        ("ro.build.type", "Build Type"),
        ("ro.build.tags", "Build Tags"),
        ("ro.hardware", "Hardware"),
        ("ro.serialno", "Serial Number"),
        ("ro.bootmode", "Boot Mode"),
        ("ro.debuggable", "Debuggable"),
        ("ro.secure", "Secure"),
        ("persist.sys.adb.tcp.port", "ADB Port"),
        ("net.hostname", "Hostname"),
    ]
    
    for prop, desc in props_to_check:
        result = await run_command(client, f"getprop {prop}", desc)
        results["system_properties"][prop] = result
        if result["status"] == "success":
            output = result["output"].strip()
            print(f"  {desc}: {output}")
        else:
            print(f"  {desc}: FAILED")
            results["gaps"].append(f"Cannot read property: {prop}")
    
    # 3. Android ID
    print("\n[3] Android ID")
    result = await run_command(client, "settings get secure android_id", "Android ID")
    results["system_properties"]["android_id"] = result
    if result["status"] == "success":
        print(f"  Android ID: {result['output'].strip()}")
    else:
        print(f"  Android ID: FAILED")
        results["gaps"].append("Cannot read Android ID")
    
    # 4. Installed Apps
    print("\n[4] Installed Apps")
    result = await run_command(client, "pm list packages -3", "Third-party apps")
    results["installed_apps"]["third_party"] = result
    if result["status"] == "success":
        apps = result["output"].strip().split('\n')
        print(f"  Third-party apps: {len(apps)}")
        for app in apps[:10]:
            print(f"    {app}")
        if len(apps) > 10:
            print(f"    ... and {len(apps) - 10} more")
    else:
        print(f"  Third-party apps: FAILED")
        results["gaps"].append("Cannot list third-party apps")
    
    # Check specific apps
    target_apps = [
        ("com.google.android.gm", "Gmail"),
        ("com.google.android.apps.walletnfcrel", "Google Wallet"),
        ("com.android.vending", "Play Store"),
        ("com.google.android.gms", "Google Play Services"),
        ("com.android.chrome", "Chrome"),
        ("com.google.android.youtube", "YouTube"),
        ("com.google.android.apps.maps", "Maps"),
    ]
    
    for pkg, name in target_apps:
        result = await run_command(client, f"pm list packages {pkg}", name)
        results["installed_apps"][pkg] = result
        if result["status"] == "success" and pkg in result["output"]:
            print(f"  ✓ {name}: Installed")
        else:
            print(f"  ✗ {name}: Not Installed")
            results["gaps"].append(f"Missing app: {name}")
    
    # 5. Google Accounts
    print("\n[5] Google Accounts")
    result = await run_command(client, "dumpsys account", "Accounts")
    results["google_accounts"]["dumpsys"] = result
    if result["status"] == "success":
        output = result["output"]
        account_lines = [l for l in output.split('\n') if '@' in l or 'Accounts:' in l]
        print(f"  Account lines found: {len(account_lines)}")
        for line in account_lines[:5]:
            print(f"    {line}")
        if len(account_lines) > 5:
            print(f"    ... and {len(account_lines) - 5} more")
        
        # Check accounts_ce.db
        result2 = await run_command(client, "ls -la /data/system_ce/0/accounts_ce.db", "accounts_ce.db")
        results["google_accounts"]["accounts_ce"] = result2
        if result2["status"] == "success" and "accounts_ce.db" in result2["output"]:
            print(f"  ✓ accounts_ce.db exists")
        else:
            print(f"  ✗ accounts_ce.db missing")
            results["gaps"].append("accounts_ce.db missing")
    else:
        print(f"  Accounts: FAILED")
        results["gaps"].append("Cannot check accounts")
    
    # 6. File System Structure
    print("\n[6] File System Structure")
    paths_to_check = [
        ("/data/system_ce/0/", "System CE"),
        ("/data/system_de/0/", "System DE"),
        ("/data/data/com.google.android.gms/", "GMS Data"),
        ("/data/data/com.android.vending/", "Play Store Data"),
        ("/data/data/com.android.chrome/", "Chrome Data"),
        ("/sdcard/", "SD Card"),
        ("/data/user_de/0/", "User DE"),
    ]
    
    for path, desc in paths_to_check:
        result = await run_command(client, f"ls -la {path}", desc)
        results["filesystem"][path] = result
        if result["status"] == "success":
            lines = result["output"].strip().split('\n')
            print(f"  {desc}: {len(lines)} entries")
        else:
            print(f"  {desc}: FAILED")
            results["gaps"].append(f"Cannot access path: {path}")
    
    # 7. Capabilities
    print("\n[7] System Capabilities")
    
    # Check root access
    result = await run_command(client, "su -c 'id'", "Root access")
    results["capabilities"]["root"] = result
    if result["status"] == "success" and "uid=0" in result["output"]:
        print(f"  ✓ Root access: Available")
    else:
        print(f"  ✗ Root access: Not available")
        results["gaps"].append("No root access")
    
    # Check ADB
    result = await run_command(client, "echo 'adb_test'", "ADB shell")
    results["capabilities"]["adb"] = result
    if result["status"] == "success":
        print(f"  ✓ ADB shell: Working")
    else:
        print(f"  ✗ ADB shell: Failed")
        results["gaps"].append("ADB shell not working")
    
    # Check SELinux
    result = await run_command(client, "getenforce", "SELinux")
    results["capabilities"]["selinux"] = result
    if result["status"] == "success":
        print(f"  SELinux: {result['output'].strip()}")
    else:
        print(f"  SELinux: FAILED")
        results["gaps"].append("Cannot check SELinux")
    
    # Check NFC
    result = await run_command(client, "service call iservicemanager 3 i32 9", "NFC service")
    results["capabilities"]["nfc"] = result
    if result["status"] == "success":
        print(f"  NFC: Available")
    else:
        print(f"  NFC: Not available or check failed")
    
    # 8. Genesis Readiness
    print("\n[8] Genesis Readiness")
    
    genesis_checks = {
        "accounts_ce": "/data/system_ce/0/accounts_ce.db",
        "accounts_de": "/data/system_de/0/accounts_de.db",
        "gms_prefs": "/data/data/com.google.android.gms/shared_prefs/",
        "play_store": "/data/data/com.android.vending/",
        "chrome": "/data/data/com.android.chrome/",
        "tapandpay": "/data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db",
        "library": "/data/data/com.android.vending/databases/library.db",
    }
    
    for check_name, path in genesis_checks.items():
        result = await run_command(client, f"ls -la {path}", check_name)
        results["genesis_readiness"][check_name] = result
        if result["status"] == "success" and (path.split('/')[-1] in result["output"] or "total" in result["output"]):
            print(f"  ✓ {check_name}: Ready")
        else:
            print(f"  ✗ {check_name}: Missing")
            results["gaps"].append(f"Genesis requirement missing: {check_name}")
    
    # 9. Network Info
    print("\n[9] Network Information")
    result = await run_command(client, "ip addr show", "Network interfaces")
    results["network"] = result
    if result["status"] == "success":
        print(f"  Network interfaces retrieved")
    else:
        print(f"  Network: FAILED")
    
    # 10. Storage Info
    print("\n[10] Storage Information")
    result = await run_command(client, "df -h", "Disk usage")
    results["storage"] = result
    if result["status"] == "success":
        print(f"  Storage info retrieved")
    else:
        print(f"  Storage: FAILED")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/tmp/device_analysis_APP5AU4BB1QQBHNA_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print(f"\n{'='*70}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*70}")
    print(f"Device ID: {PAD}")
    print(f"Status: {results['summary'].get('device_status', 'UNKNOWN')}")
    print(f"Gaps identified: {len(results['gaps'])}")
    print(f"\nTop gaps:")
    for i, gap in enumerate(results['gaps'][:10], 1):
        print(f"  {i}. {gap}")
    if len(results['gaps']) > 10:
        print(f"  ... and {len(results['gaps']) - 10} more")
    print(f"\nDetailed report saved to: {output_file}")
    print(f"{'='*70}")
    
    return results

if __name__ == "__main__":
    asyncio.run(analyze_device())
