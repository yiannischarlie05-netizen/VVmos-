#!/usr/bin/env python3
"""
E2E Cloud Device Recon & Preparation
=====================================
Connects to VMOS Pro Cloud, selects a running device, performs deep
filesystem/app recon, maps Genesis injection paths, installs required
apps, and validates real-world E2E test readiness.
"""

import asyncio
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE_URL = "https://api.vmoscloud.com"

# Rate limit helper
async def rate_wait(seconds=3.5):
    await asyncio.sleep(seconds)


async def cmd(client, pad_code, command, label=""):
    """Execute shell command with rate limiting and error handling."""
    await rate_wait()
    try:
        resp = await client.sync_cmd(pad_code, command, timeout_sec=30)
        if resp.get("code") == 200:
            output = resp.get("data", {})
            if isinstance(output, dict):
                return output.get("cmdRet", output.get("result", str(output)))
            return str(output)
        else:
            return f"[ERROR code={resp.get('code')}] {resp.get('msg', '')}"
    except Exception as e:
        return f"[EXCEPTION] {e}"


async def main():
    client = VMOSCloudClient(AK, SK, BASE_URL)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: List all devices and select a running one
    # ═══════════════════════════════════════════════════════════════════
    print("=" * 80)
    print("PHASE 1: DEVICE DISCOVERY")
    print("=" * 80)

    resp = await client.instance_list(page=1, rows=100)
    if resp.get("code") != 200:
        print(f"FATAL: Cannot list devices: {resp}")
        return

    data = resp.get("data", {})
    instances = data.get("pageData", [])
    total = data.get("total", 0)

    print(f"Total devices: {total}")
    print(f"Returned: {len(instances)}")

    STATUS_MAP = {10: "RUNNING", 11: "BOOTING", 12: "RESETTING", 14: "STOPPED", 15: "BRICKED", 20: "STOPPED"}

    running_devices = []
    for inst in instances:
        pc = inst.get("padCode", "?")
        status = inst.get("padStatus", -1)
        sname = STATUS_MAP.get(status, f"UNKNOWN({status})")
        tmpl = inst.get("realPhoneTemplateId", "?")
        img = inst.get("imageVersion", "?")
        print(f"  [{sname:>10}] {pc}  template={tmpl}  image={img}")
        if status == 10:
            running_devices.append(inst)

    if not running_devices:
        print("\nNo RUNNING devices found. Cannot proceed.")
        return

    # Pick the first running device
    target = running_devices[0]
    PAD = target["padCode"]
    print(f"\n>>> SELECTED DEVICE: {PAD}")
    print(f"    Template: {target.get('realPhoneTemplateId', '?')}")
    print(f"    Image:    {target.get('imageVersion', '?')}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: Basic device info & root check
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 2: DEVICE BASELINE INFO")
    print("=" * 80)

    checks = {
        "whoami": "whoami",
        "id": "id",
        "Android version": "getprop ro.build.version.release",
        "SDK level": "getprop ro.build.version.sdk",
        "Device model": "getprop ro.product.model",
        "Brand": "getprop ro.product.brand",
        "Build fingerprint": "getprop ro.build.fingerprint",
        "Security patch": "getprop ro.build.version.security_patch",
        "SELinux": "getenforce",
        "Disk space": "df -h /data | tail -1",
        "Uptime": "uptime",
    }

    for label, c in checks.items():
        result = await cmd(client, PAD, c, label)
        print(f"  {label:>25}: {result.strip() if result else 'N/A'}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: Installed packages (key ones)
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 3: INSTALLED PACKAGE AUDIT")
    print("=" * 80)

    critical_packages = [
        "com.google.android.gms",           # Google Play Services
        "com.android.vending",              # Play Store
        "com.google.android.apps.walletnfcrel",  # Google Wallet/Pay
        "com.android.chrome",               # Chrome
        "com.google.android.gsf",           # Google Services Framework
        "com.google.android.apps.maps",     # Google Maps
        "com.google.android.youtube",       # YouTube
        "com.google.android.gm",            # Gmail
        "com.google.android.contacts",      # Google Contacts
        "com.google.android.calendar",      # Google Calendar
        "com.android.providers.contacts",   # Contacts provider
        "com.android.providers.telephony",  # Telephony provider
        "com.android.providers.media",      # Media provider
        "com.android.settings",             # Settings
    ]

    pm_list_raw = await cmd(client, PAD, "pm list packages 2>/dev/null | head -200")
    installed_packages = set()
    if pm_list_raw:
        for line in pm_list_raw.strip().split('\n'):
            if line.startswith('package:'):
                installed_packages.add(line.replace('package:', '').strip())

    print(f"  Total packages installed: {len(installed_packages)}")
    print(f"\n  Critical Package Status:")
    missing_packages = []
    for pkg in critical_packages:
        present = pkg in installed_packages
        status = "✓ INSTALLED" if present else "✗ MISSING"
        print(f"    {status:>14}  {pkg}")
        if not present:
            missing_packages.append(pkg)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: Genesis injection path mapping
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 4: GENESIS INJECTION PATH MAPPING")
    print("=" * 80)

    injection_paths = {
        # Wallet / Payment
        "tapandpay.db": "/data/data/com.google.android.gms/databases/tapandpay.db",
        "COIN.xml": "/data/data/com.google.android.gms/shared_prefs/COIN.xml",
        "GMS shared_prefs dir": "/data/data/com.google.android.gms/shared_prefs/",
        "GMS databases dir": "/data/data/com.google.android.gms/databases/",
        "Chrome Web Data": "/data/data/com.android.chrome/app_chrome/Default/Web Data",
        "Chrome Login Data": "/data/data/com.android.chrome/app_chrome/Default/Login Data",
        "Chrome Cookies": "/data/data/com.android.chrome/app_chrome/Default/Cookies",
        "Chrome History": "/data/data/com.android.chrome/app_chrome/Default/History",
        "Chrome Preferences": "/data/data/com.android.chrome/app_chrome/Default/Preferences",
        # Contacts / SMS / Calls  
        "Contacts DB": "/data/data/com.android.providers.contacts/databases/contacts2.db",
        "Call log DB": "/data/data/com.android.providers.contacts/databases/calllog.db",
        "SMS/MMS DB": "/data/data/com.android.providers.telephony/databases/mmssms.db",
        # Media
        "DCIM Camera": "/sdcard/DCIM/Camera/",
        "Pictures": "/sdcard/Pictures/",
        "Downloads": "/sdcard/Download/",
        # WiFi
        "WiFi config": "/data/misc/wifi/WifiConfigStore.xml",
        "wpa_supplicant": "/data/misc/wifi/wpa_supplicant.conf",
        # Accounts
        "accounts_ce.db": "/data/system_ce/0/accounts_ce.db",
        "accounts_de.db": "/data/system_de/0/accounts_de.db",
        # Settings
        "settings_secure.xml": "/data/system/users/0/settings_secure.xml",
        "settings_global.xml": "/data/system/users/0/settings_global.xml",
        "settings_system.xml": "/data/system/users/0/settings_system.xml",
        # Play Store / Vending
        "Vending prefs": "/data/data/com.android.vending/shared_prefs/",
        # System
        "Build.prop": "/system/build.prop",
        "Default.prop": "/default.prop",
        # Staging
        "tmpfs staging": "/dev/.sc/",
        "data local tmp": "/data/local/tmp/",
    }

    print(f"\n  Checking {len(injection_paths)} injection targets...")
    path_report = {}
    for name, path in injection_paths.items():
        if path.endswith('/'):
            result = await cmd(client, PAD, f"ls -la {path} 2>/dev/null | head -5")
        else:
            result = await cmd(client, PAD, f"ls -la {path} 2>/dev/null")

        exists = result and "No such file" not in result and "[ERROR" not in result and "[EXCEPTION" not in result and result.strip() != ""
        size_info = ""
        if exists and not path.endswith('/'):
            # Get file size
            size_result = await cmd(client, PAD, f"stat -c '%s' {path} 2>/dev/null")
            if size_result and size_result.strip().isdigit():
                size = int(size_result.strip())
                size_info = f" ({size} bytes)"

        status = "✓ EXISTS" if exists else "✗ MISSING"
        path_report[name] = {"path": path, "exists": exists}
        print(f"    {status:>12}  {name}: {path}{size_info}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 5: Deep filesystem recon
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 5: DEEP FILESYSTEM RECON")
    print("=" * 80)

    recon_commands = {
        "GMS databases": "ls /data/data/com.google.android.gms/databases/ 2>/dev/null | head -20",
        "GMS shared_prefs": "ls /data/data/com.google.android.gms/shared_prefs/ 2>/dev/null | head -20",
        "Chrome profile dir": "ls /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null | head -15",
        "Accounts in accounts_ce": "sqlite3 /data/system_ce/0/accounts_ce.db 'SELECT name, type FROM accounts;' 2>/dev/null",
        "Contacts count": "sqlite3 /data/data/com.android.providers.contacts/databases/contacts2.db 'SELECT COUNT(*) FROM raw_contacts;' 2>/dev/null",
        "Call log count": "sqlite3 /data/data/com.android.providers.contacts/databases/calllog.db 'SELECT COUNT(*) FROM calls;' 2>/dev/null",
        "SMS count": "sqlite3 /data/data/com.android.providers.telephony/databases/mmssms.db 'SELECT COUNT(*) FROM sms;' 2>/dev/null",
        "WiFi saved networks": "cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | grep -c 'SSID' || echo 0",
        "Android ID": "settings get secure android_id 2>/dev/null",
        "Google Ad ID": "cat /data/data/com.google.android.gms/shared_prefs/adid_settings.xml 2>/dev/null | grep -o 'value=\"[^\"]*\"' | head -1",
        "/dev/.sc exists": "ls -la /dev/.sc/ 2>/dev/null || echo 'NOT_CREATED'",
        "/data/local/tmp contents": "ls -la /data/local/tmp/ 2>/dev/null | head -10",
        "Magisk present": "ls /data/adb/magisk/ 2>/dev/null && echo MAGISK_FOUND || which su 2>/dev/null && echo SU_FOUND || echo NO_ROOT_MANAGER",
        "Frida server": "ls /data/local/tmp/frida* 2>/dev/null || echo NOT_INSTALLED",
        "iptables status": "iptables -L OUTPUT 2>/dev/null | head -5 || echo NO_IPTABLES",
        "SELinux mode": "cat /sys/fs/selinux/enforce 2>/dev/null",
        "Kernel version": "uname -r",
        "Mount points (data)": "mount | grep '/data ' | head -3",
        "Props count": "getprop | wc -l",
    }

    for label, c in recon_commands.items():
        result = await cmd(client, PAD, c, label)
        output = result.strip() if result else "N/A"
        if '\n' in output:
            print(f"\n  {label}:")
            for line in output.split('\n')[:10]:
                print(f"    {line}")
        else:
            print(f"  {label:>30}: {output}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 6: Create staging directory
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 6: STAGING DIRECTORY SETUP")
    print("=" * 80)

    staging_cmds = [
        ("Create /dev/.sc staging", "mkdir -p /dev/.sc && chmod 777 /dev/.sc && echo OK"),
        ("Create /data/local/tmp/genesis", "mkdir -p /data/local/tmp/genesis && chmod 777 /data/local/tmp/genesis && echo OK"),
        ("Verify staging", "ls -la /dev/.sc/ /data/local/tmp/genesis/ 2>/dev/null"),
    ]

    for label, c in staging_cmds:
        result = await cmd(client, PAD, c, label)
        print(f"  {label}: {result.strip() if result else 'FAILED'}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 7: Check and enable ADB
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 7: ADB STATUS")
    print("=" * 80)

    await rate_wait()
    try:
        adb_resp = await client.enable_adb([PAD], enable=True)
        print(f"  Enable ADB response: code={adb_resp.get('code')}")
    except Exception as e:
        print(f"  Enable ADB error: {e}")

    await rate_wait()
    try:
        adb_info = await client.get_adb_info(PAD)
        print(f"  ADB info: {json.dumps(adb_info.get('data', {}), indent=4)}")
    except Exception as e:
        print(f"  ADB info error: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 8: Device properties snapshot
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 8: KEY DEVICE PROPERTIES")
    print("=" * 80)

    key_props = [
        "ro.build.fingerprint",
        "ro.build.display.id",
        "ro.product.model",
        "ro.product.brand",
        "ro.product.device",
        "ro.product.manufacturer",
        "ro.product.name",
        "ro.hardware",
        "ro.serialno",
        "ro.build.version.release",
        "ro.build.version.sdk",
        "ro.build.version.security_patch",
        "ro.build.type",
        "ro.build.tags",
        "ro.boot.verifiedbootstate",
        "ro.boot.flash.locked",
        "ro.boot.vbmeta.device_state",
        "persist.sys.timezone",
        "persist.sys.language",
        "gsm.sim.operator.alpha",
        "gsm.operator.alpha",
        "ro.telephony.default_network",
    ]

    props_cmd = " && ".join([f"echo '{p}='$(getprop {p})" for p in key_props])
    props_result = await cmd(client, PAD, props_cmd)
    if props_result:
        for line in props_result.strip().split('\n'):
            if '=' in line:
                print(f"  {line}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 9: Check Google Play Services readiness
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 9: GOOGLE PLAY SERVICES READINESS")
    print("=" * 80)

    gms_checks = {
        "GMS version": "dumpsys package com.google.android.gms 2>/dev/null | grep versionName | head -1",
        "GMS PID": "pidof com.google.android.gms 2>/dev/null || echo NOT_RUNNING",
        "GMS persistent": "dumpsys package com.google.android.gms 2>/dev/null | grep 'flags=' | head -1",
        "Play Store version": "dumpsys package com.android.vending 2>/dev/null | grep versionName | head -1",
        "GSF ID": "sqlite3 /data/data/com.google.android.gsf/databases/gservices.db \"SELECT value FROM main WHERE name='android_id';\" 2>/dev/null || echo N/A",
        "GMS registered accounts": "sqlite3 /data/data/com.google.android.gms/databases/accounts.db 'SELECT name FROM accounts;' 2>/dev/null || echo NONE",
        "NFC capability": "pm list features 2>/dev/null | grep nfc || echo NO_NFC",
    }

    for label, c in gms_checks.items():
        result = await cmd(client, PAD, c, label)
        print(f"  {label:>30}: {result.strip() if result else 'N/A'}")

    # ═══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("E2E READINESS SUMMARY")
    print("=" * 80)

    existing_paths = sum(1 for v in path_report.values() if v["exists"])
    missing_paths = sum(1 for v in path_report.values() if not v["exists"])

    print(f"  Device:          {PAD}")
    print(f"  Packages:        {len(installed_packages)} installed ({len(missing_packages)} critical missing)")
    print(f"  Injection paths: {existing_paths} exist / {missing_paths} missing")
    print(f"  Missing critical packages: {', '.join(missing_packages) if missing_packages else 'NONE'}")
    missing_path_names = [k for k, v in path_report.items() if not v["exists"]]
    print(f"  Missing paths:   {', '.join(missing_path_names[:10]) if missing_path_names else 'NONE'}")

    # Save full report
    report = {
        "device": PAD,
        "template": target.get("realPhoneTemplateId"),
        "image": target.get("imageVersion"),
        "total_packages": len(installed_packages),
        "missing_critical_packages": missing_packages,
        "injection_paths": path_report,
        "missing_paths": missing_path_names,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    report_path = Path(__file__).parent / "e2e_cloud_recon_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\n  Full report saved: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
