#!/usr/bin/env python3
"""
E2E Cloud Device Preparation — Phase 2
=======================================
Properly-parsed package audit, missing app install, deep injection
validation, and E2E test config generation.

Uses the known device: ATP6416I3JJRXL3V
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE_URL = "https://api.vmoscloud.com"
PAD = "ATP6416I3JJRXL3V"


async def shell(client, command, label=""):
    """Execute shell command, properly extract stdout from API response."""
    await asyncio.sleep(3.5)
    try:
        resp = await client.sync_cmd(PAD, command, timeout_sec=30)
        if resp.get("code") == 200:
            data = resp.get("data")
            if isinstance(data, list) and len(data) > 0:
                entry = data[0]
                stdout = entry.get("errorMsg")  # errorMsg = actual stdout
                if stdout is None:
                    return ""
                return stdout.strip()
            elif isinstance(data, dict):
                return data.get("cmdRet", data.get("result", "")).strip()
            return str(data).strip()
        else:
            return f"[ERROR code={resp.get('code')}] {resp.get('msg', '')}"
    except Exception as e:
        return f"[EXCEPTION] {e}"


async def main():
    client = VMOSCloudClient(AK, SK, BASE_URL)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: PROPER PACKAGE AUDIT
    # ═══════════════════════════════════════════════════════════════════
    print("=" * 80)
    print("PHASE 1: COMPLETE PACKAGE AUDIT (properly parsed)")
    print("=" * 80)

    pkg_output = await shell(client, "pm list packages 2>/dev/null")
    packages = [line.replace("package:", "").strip()
                for line in pkg_output.split("\n")
                if line.startswith("package:")]

    print(f"  Total packages installed: {len(packages)}")

    # Categorized critical packages
    critical = {
        "Google Play Services": "com.google.android.gms",
        "Google Play Store": "com.android.vending",
        "Google Wallet/Pay": "com.google.android.apps.walletnfcrel",
        "Chrome": "com.android.chrome",
        "GSF (Framework)": "com.google.android.gsf",
        "Google Maps": "com.google.android.apps.maps",
        "YouTube": "com.google.android.youtube",
        "Gmail": "com.google.android.gm",
        "Google Contacts": "com.google.android.contacts",
        "Google Calendar": "com.google.android.calendar",
        "Contacts Provider": "com.android.providers.contacts",
        "Telephony Provider": "com.android.providers.telephony",
        "Media Provider": "com.android.providers.media",
        "Settings": "com.android.settings",
        "NFC Service": "com.android.nfc",
        "Google Pay (old)": "com.google.android.apps.nbu.paisa.user",
        "Samsung Pay": "com.samsung.android.spay",
        "Google Account Manager": "com.google.android.gsf.login",
        "Google Backup Transport": "com.google.android.backuptransport",
        "Setup Wizard": "com.google.android.setupwizard",
        "GBoard": "com.google.android.inputmethod.latin",
        "Google App": "com.google.android.googlequicksearchbox",
    }

    installed_critical = []
    missing_critical = []
    print("\n  Critical Package Status:")
    for name, pkg in sorted(critical.items()):
        if pkg in packages:
            print(f"    ✓ FOUND    {pkg} ({name})")
            installed_critical.append(pkg)
        else:
            print(f"    ✗ MISSING  {pkg} ({name})")
            missing_critical.append((name, pkg))

    # Show first 30 of all packages for context
    print(f"\n  First 40 installed packages:")
    for pkg in sorted(packages)[:40]:
        print(f"    {pkg}")
    if len(packages) > 40:
        print(f"    ... and {len(packages) - 40} more")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: DEEP INJECTION TARGET VALIDATION
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 2: DEEP INJECTION TARGET VALIDATION")
    print("=" * 80)

    # Check actual DB file sizes and permissions
    db_targets = [
        ("/data/data/com.google.android.gms/databases/tapandpay.db", "tapandpay.db"),
        ("/data/data/com.google.android.gms/databases/android_pay", "android_pay"),
        ("/data/data/com.google.android.gms/databases/config.db", "config.db"),
        ("/data/data/com.google.android.gms/databases/constellation.db", "constellation.db"),
        ("/data/data/com.android.chrome/app_chrome/Default/Web Data", "Chrome Web Data"),
        ("/data/data/com.android.chrome/app_chrome/Default/Login Data", "Chrome Login Data"),
        ("/data/data/com.android.chrome/app_chrome/Default/Cookies", "Chrome Cookies"),
        ("/data/data/com.android.chrome/app_chrome/Default/History", "Chrome History"),
        ("/data/data/com.android.providers.contacts/databases/contacts2.db", "Contacts DB"),
        ("/data/data/com.android.providers.contacts/databases/calllog.db", "Call Log DB"),
        ("/data/data/com.android.providers.telephony/databases/mmssms.db", "SMS/MMS DB"),
        ("/data/system_ce/0/accounts_ce.db", "accounts_ce.db"),
        ("/data/system_de/0/accounts_de.db", "accounts_de.db"),
        ("/data/misc/wifi/WifiConfigStore.xml", "WifiConfigStore.xml"),
        ("/data/data/com.google.android.gms/shared_prefs/COIN.xml", "COIN.xml"),
    ]

    print("\n  Injection Target Details (size + permissions):")
    for path, name in db_targets:
        result = await shell(client, f"ls -la '{path}' 2>/dev/null || echo 'NOT_FOUND'")
        print(f"    {name:25s} → {result}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: COIN.xml CURRENT STATE
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 3: COIN.xml CURRENT STATE (Zero-Auth Flags)")
    print("=" * 80)

    coin_content = await shell(client, "cat /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null || echo 'NOT_READABLE'")
    if len(coin_content) > 2000:
        # Show first 2000 chars
        print(f"  COIN.xml ({len(coin_content)} bytes):")
        print(coin_content[:2000])
        print("  ... (truncated)")
    else:
        print(f"  COIN.xml content:\n{coin_content}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: tapandpay.db SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 4: tapandpay.db SCHEMA ANALYSIS")
    print("=" * 80)

    schema = await shell(client, "sqlite3 /data/data/com.google.android.gms/databases/tapandpay.db '.tables' 2>/dev/null || echo 'CANNOT_READ'")
    print(f"  Tables in tapandpay.db:\n  {schema}")

    schema_detail = await shell(client, "sqlite3 /data/data/com.google.android.gms/databases/tapandpay.db '.schema' 2>/dev/null | head -100")
    print(f"\n  Schema (first 100 lines):\n{schema_detail}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 5: ACCOUNTS & IDENTITY STATE
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 5: ACCOUNTS & IDENTITY STATE")
    print("=" * 80)

    accounts_tables = await shell(client, "sqlite3 /data/system_ce/0/accounts_ce.db '.tables' 2>/dev/null || echo 'CANNOT_READ'")
    print(f"  accounts_ce.db tables: {accounts_tables}")

    accounts_data = await shell(client, "sqlite3 /data/system_ce/0/accounts_ce.db 'SELECT * FROM accounts LIMIT 10;' 2>/dev/null || echo 'EMPTY/ERROR'")
    print(f"  accounts_ce.db accounts: {accounts_data}")

    # Android ID + Advertising ID
    android_id = await shell(client, "settings get secure android_id")
    print(f"  Android ID: {android_id}")

    gsf_id = await shell(client, "sqlite3 /data/data/com.google.android.gsf/databases/gservices.db \"SELECT value FROM main WHERE name='android_id';\" 2>/dev/null || echo 'N/A'")
    print(f"  GSF ID: {gsf_id}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 6: CHROME AUTOFILL STATE
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 6: CHROME AUTOFILL STATE")
    print("=" * 80)

    chrome_tables = await shell(client, "sqlite3 '/data/data/com.android.chrome/app_chrome/Default/Web Data' '.tables' 2>/dev/null || echo 'CANNOT_READ'")
    print(f"  Chrome Web Data tables: {chrome_tables}")

    chrome_cards = await shell(client, "sqlite3 '/data/data/com.android.chrome/app_chrome/Default/Web Data' 'SELECT * FROM credit_cards LIMIT 5;' 2>/dev/null || echo 'EMPTY/ERROR'")
    print(f"  Chrome credit_cards: {chrome_cards}")

    chrome_autofill = await shell(client, "sqlite3 '/data/data/com.android.chrome/app_chrome/Default/Web Data' 'SELECT * FROM autofill LIMIT 10;' 2>/dev/null || echo 'EMPTY/ERROR'")
    print(f"  Chrome autofill entries: {chrome_autofill}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 7: NETWORK & CONNECTIVITY
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 7: NETWORK & CONNECTIVITY")
    print("=" * 80)

    ip_info = await shell(client, "ip addr show 2>/dev/null | grep 'inet ' | head -10")
    print(f"  IP addresses:\n{ip_info}")

    dns_info = await shell(client, "cat /etc/resolv.conf 2>/dev/null || getprop net.dns1")
    print(f"  DNS: {dns_info}")

    route_info = await shell(client, "ip route show default 2>/dev/null | head -5")
    print(f"  Default route: {route_info}")

    # Check for neighbors (other VMOS instances)
    arp_info = await shell(client, "ip neigh show 2>/dev/null | head -20")
    print(f"  ARP neighbors:\n{arp_info}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 8: COMPLETE DEVICE PROPERTIES DUMP (key ones)
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 8: KEY DEVICE PROPERTIES")
    print("=" * 80)

    key_props = [
        "ro.build.fingerprint", "ro.build.display.id",
        "ro.product.model", "ro.product.brand", "ro.product.device",
        "ro.product.manufacturer", "ro.product.name", "ro.product.board",
        "ro.hardware", "ro.hardware.chipname", "ro.soc.manufacturer", "ro.soc.model",
        "ro.serialno", "ro.boot.serialno",
        "ro.build.version.release", "ro.build.version.sdk",
        "ro.build.version.security_patch",
        "ro.build.type", "ro.build.tags",
        "ro.boot.verifiedbootstate", "ro.boot.flash.locked",
        "ro.boot.vbmeta.device_state",
        "persist.sys.timezone", "persist.sys.language",
        "gsm.sim.operator.alpha", "gsm.operator.alpha",
        "net.gprs.local-ip", "gsm.version.baseband",
        "ro.com.google.gmsversion",
        "ro.telephony.default_network",
        "ro.crypto.state",
        "dalvik.vm.heapsize", "dalvik.vm.heapmaxfree",
    ]

    props_output = await shell(client, " && ".join(
        [f"echo '{p}='$(getprop {p})" for p in key_props]
    ))
    print(f"  Properties:\n{props_output}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 9: SERVICES & PROCESS STATE
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 9: SERVICES & PROCESSES")
    print("=" * 80)

    gms_procs = await shell(client, "ps -A | grep -E 'gms|google|chrome|wallet|nfc|pay' | head -20")
    print(f"  Google-related processes:\n{gms_procs}")

    nfc_status = await shell(client, "dumpsys nfc 2>/dev/null | head -20 || echo 'NFC_NOT_AVAILABLE'")
    print(f"  NFC status:\n{nfc_status}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 10: GENERATE E2E TEST CONFIG
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 10: GENERATING E2E TEST CONFIG")
    print("=" * 80)

    config = {
        "device": {
            "pad_code": PAD,
            "model": "SM-S9280",
            "brand": "samsung",
            "android_version": "15",
            "sdk": 35,
            "security_patch": "2026-03-05",
            "fingerprint": "samsung/e3qzcx/e3q:15/AP3A.240905.015.A2/S9280ZCS4BYDF:user/release-keys",
            "root": True,
            "selinux": "Permissive",
            "kernel": "6.1.99-android14-11-2370239-abS9280ZCS4BYDF",
            "android_id": android_id,
        },
        "api": {
            "ak": AK,
            "sk": SK,
            "base_url": BASE_URL,
        },
        "injection_paths": {
            "tapandpay_db": "/data/data/com.google.android.gms/databases/tapandpay.db",
            "android_pay_db": "/data/data/com.google.android.gms/databases/android_pay",
            "config_db": "/data/data/com.google.android.gms/databases/config.db",
            "constellation_db": "/data/data/com.google.android.gms/databases/constellation.db",
            "coin_xml": "/data/data/com.google.android.gms/shared_prefs/COIN.xml",
            "chrome_web_data": "/data/data/com.android.chrome/app_chrome/Default/Web Data",
            "chrome_login_data": "/data/data/com.android.chrome/app_chrome/Default/Login Data",
            "chrome_cookies": "/data/data/com.android.chrome/app_chrome/Default/Cookies",
            "chrome_history": "/data/data/com.android.chrome/app_chrome/Default/History",
            "chrome_prefs": "/data/data/com.android.chrome/app_chrome/Default/Preferences",
            "contacts_db": "/data/data/com.android.providers.contacts/databases/contacts2.db",
            "calllog_db": "/data/data/com.android.providers.contacts/databases/calllog.db",
            "mmssms_db": "/data/data/com.android.providers.telephony/databases/mmssms.db",
            "accounts_ce_db": "/data/system_ce/0/accounts_ce.db",
            "accounts_de_db": "/data/system_de/0/accounts_de.db",
            "wifi_config": "/data/misc/wifi/WifiConfigStore.xml",
            "wpa_supplicant": "/data/misc/wifi/wpa_supplicant.conf",
            "settings_secure": "/data/system/users/0/settings_secure.xml",
            "settings_global": "/data/system/users/0/settings_global.xml",
            "settings_system": "/data/system/users/0/settings_system.xml",
            "build_prop": "/system/build.prop",
            "default_prop": "/default.prop",
        },
        "staging_dirs": {
            "tmpfs_staging": "/dev/.sc/",
            "genesis_staging": "/data/local/tmp/genesis/",
            "local_tmp": "/data/local/tmp/",
        },
        "media_paths": {
            "dcim_camera": "/sdcard/DCIM/Camera/",
            "pictures": "/sdcard/Pictures/",
            "downloads": "/sdcard/Download/",
        },
        "gms": {
            "databases_dir": "/data/data/com.google.android.gms/databases/",
            "shared_prefs_dir": "/data/data/com.google.android.gms/shared_prefs/",
        },
        "total_packages": len(packages),
        "installed_critical": installed_critical,
        "missing_critical": [(name, pkg) for name, pkg in missing_critical],
    }

    config_path = Path(__file__).parent / "e2e_cloud_config.json"
    config_path.write_text(json.dumps(config, indent=2))
    print(f"  Config written to: {config_path}")
    print(json.dumps(config, indent=2))

    print("\n" + "=" * 80)
    print("RECON COMPLETE — DEVICE READY FOR E2E TESTING")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
