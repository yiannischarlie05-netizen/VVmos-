#!/usr/bin/env python3
"""Deep environment scan of APP5BJ4LRVRJFJQR for Genesis pipeline readiness."""
import asyncio, json, time
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP5BJ4LRVRJFJQR"
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE = "https://api.vmoscloud.com"
DELAY = 3.6

results = {}

async def sh(c, cmd, timeout=30):
    r = await c.sync_cmd(pad_code=PAD, command=cmd, timeout_sec=timeout)
    d = r.get("data", [])
    if isinstance(d, list) and d:
        return d[0].get("errorMsg", "").strip()
    return str(d)

async def scan(c, label, cmd, timeout=30):
    await asyncio.sleep(DELAY)
    try:
        out = await sh(c, cmd, timeout)
        results[label] = out
        print(f"[✓] {label}: {out[:200]}")
    except Exception as e:
        results[label] = f"ERROR: {e}"
        print(f"[✗] {label}: {e}")

async def api_call(c, label, func, **kwargs):
    await asyncio.sleep(DELAY)
    try:
        r = await func(**kwargs)
        results[label] = r
        print(f"[API] {label}: code={r.get('code')} data_keys={list(r.get('data',{}).keys()) if isinstance(r.get('data'),dict) else type(r.get('data')).__name__}")
    except Exception as e:
        results[label] = f"ERROR: {e}"
        print(f"[✗] {label}: {e}")

async def main():
    c = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE)
    t0 = time.time()

    print("=" * 80)
    print(f"DEEP ENVIRONMENT SCAN — {PAD}")
    print("=" * 80)

    # ── PHASE 1: DEVICE IDENTITY & STATUS ──
    print("\n━━━ PHASE 1: DEVICE IDENTITY & STATUS ━━━")
    await api_call(c, "api_instance_list", c.instance_list, page=1, rows=50)
    
    # Find our device in the list
    il = results.get("api_instance_list", {})
    if isinstance(il, dict) and il.get("code") == 200:
        devices = il.get("data", {}).get("records", [])
        our_dev = next((d for d in devices if d.get("padCode") == PAD), None)
        if our_dev:
            print(f"    → Found device: template={our_dev.get('templateId')}, status={our_dev.get('status')}, "
                  f"model={our_dev.get('model')}, android={our_dev.get('androidVersion')}")
            results["device_meta"] = our_dev

    await api_call(c, "api_adb_info", c.get_adb_info, pad_code=PAD)

    # ── PHASE 2: SYSTEM IDENTITY ──
    print("\n━━━ PHASE 2: SYSTEM IDENTITY (ro.* properties) ━━━")
    await scan(c, "fingerprint", "getprop ro.build.fingerprint")
    await scan(c, "model", "getprop ro.product.model")
    await scan(c, "brand", "getprop ro.product.brand")
    await scan(c, "device", "getprop ro.product.device")
    await scan(c, "manufacturer", "getprop ro.product.manufacturer")
    await scan(c, "android_version", "getprop ro.build.version.release")
    await scan(c, "sdk_level", "getprop ro.build.version.sdk")
    await scan(c, "security_patch", "getprop ro.build.version.security_patch")
    await scan(c, "build_type", "getprop ro.build.type")
    await scan(c, "build_tags", "getprop ro.build.tags")
    await scan(c, "hardware", "getprop ro.hardware")
    await scan(c, "board", "getprop ro.product.board")
    await scan(c, "bootstate", "getprop ro.boot.verifiedbootstate")
    await scan(c, "flash_locked", "getprop ro.boot.flash.locked")
    await scan(c, "first_api_level", "getprop ro.product.first_api_level")
    await scan(c, "serial", "getprop ro.serialno")
    await scan(c, "boot_serialno", "getprop ro.boot.serialno")
    await scan(c, "android_id", "settings get secure android_id")

    # ── PHASE 3: ROOT & SECURITY POSTURE ──
    print("\n━━━ PHASE 3: ROOT & SECURITY POSTURE ━━━")
    await scan(c, "whoami", "id")
    await scan(c, "selinux", "getenforce")
    await scan(c, "su_binary", "which su 2>/dev/null && su --version 2>/dev/null || echo NO_SU")
    await scan(c, "magisk", "ls -la /data/adb/magisk/ 2>/dev/null && magisk --version 2>/dev/null || echo NO_MAGISK")
    await scan(c, "kernelsu", "ls /data/adb/ksu/ 2>/dev/null || echo NO_KSU")
    await scan(c, "superuser_app", "pm list packages 2>/dev/null | grep -iE 'supersu|magisk|ksu|superuser' || echo NONE")
    await scan(c, "frida_check", "ls /data/local/tmp/frida* 2>/dev/null; ps -A 2>/dev/null | grep frida || echo NO_FRIDA")
    await scan(c, "lsposed_check", "ls /data/adb/lspd/ 2>/dev/null; pm list packages 2>/dev/null | grep lsposed || echo NO_LSPOSED")

    # ── PHASE 4: KERNEL & CONTAINER DETECTION ──
    print("\n━━━ PHASE 4: KERNEL & CONTAINER DETECTION ━━━")
    await scan(c, "kernel", "uname -a")
    await scan(c, "proc_version", "cat /proc/version 2>/dev/null | head -1")
    await scan(c, "cgroup", "cat /proc/1/cgroup 2>/dev/null | head -5")
    await scan(c, "mountinfo_veth", "ip link show 2>/dev/null | head -10")
    await scan(c, "vmos_leaks", "getprop ro.boot.pad_code 2>/dev/null; ls /proc/device-tree/model 2>/dev/null; cat /proc/device-tree/model 2>/dev/null")
    await scan(c, "xu_daemon", "ps -A 2>/dev/null | grep -E 'xu_daemon|xudaemon|vmos' | head -5 || echo NONE")
    await scan(c, "container_markers", "ls /.dockerenv 2>/dev/null; cat /proc/1/environ 2>/dev/null | tr '\\0' '\\n' | grep -i container 2>/dev/null || echo NO_CONTAINER_ENV")
    await scan(c, "mount_points", "mount 2>/dev/null | head -30")
    await scan(c, "namespace_info", "ls -la /proc/self/ns/ 2>/dev/null")

    # ── PHASE 5: GMS / GOOGLE PLAY SERVICES ──
    print("\n━━━ PHASE 5: GMS & GOOGLE PLAY SERVICES ━━━")
    await scan(c, "gms_version", "dumpsys package com.google.android.gms 2>/dev/null | grep -E 'versionName|versionCode' | head -2")
    await scan(c, "gms_data", "ls -la /data/data/com.google.android.gms/ 2>/dev/null | head -10")
    await scan(c, "gms_databases", "ls -la /data/data/com.google.android.gms/databases/ 2>/dev/null")
    await scan(c, "gms_shared_prefs", "ls -la /data/data/com.google.android.gms/shared_prefs/ 2>/dev/null | head -20")
    await scan(c, "gms_process", "ps -A 2>/dev/null | grep com.google.android.gms | head -5")
    await scan(c, "play_store", "pm list packages 2>/dev/null | grep com.android.vending")
    await scan(c, "play_store_version", "dumpsys package com.android.vending 2>/dev/null | grep versionName | head -1")
    await scan(c, "accounts", "dumpsys account 2>/dev/null | head -30")

    # ── PHASE 6: WALLET / PAYMENT PATHS ──
    print("\n━━━ PHASE 6: WALLET & PAYMENT PATHS (Genesis Phase 3) ━━━")
    await scan(c, "tapandpay_db", "ls -la /data/data/com.google.android.gms/databases/tapandpay* 2>/dev/null || echo NOT_FOUND")
    await scan(c, "coin_xml", "ls -la /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null && cat /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null | head -20 || echo NOT_FOUND")
    await scan(c, "google_pay_app", "pm list packages 2>/dev/null | grep -E 'com.google.android.apps.walletnfcrel|com.google.android.apps.nbu' || echo NOT_INSTALLED")
    await scan(c, "nfc_status", "dumpsys nfc 2>/dev/null | head -20")
    await scan(c, "nfc_service", "service list 2>/dev/null | grep -i nfc | head -5")
    await scan(c, "chrome_data", "ls -la /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null | head -15 || echo NOT_FOUND")
    await scan(c, "chrome_web_data", "ls -la /data/data/com.android.chrome/app_chrome/Default/Web\\ Data 2>/dev/null || echo NOT_FOUND")
    await scan(c, "chrome_login_data", "ls -la /data/data/com.android.chrome/app_chrome/Default/Login\\ Data 2>/dev/null || echo NOT_FOUND")
    await scan(c, "chrome_cookies", "ls -la /data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null || echo NOT_FOUND")

    # ── PHASE 7: SQLITE3 & TOOLS AVAILABILITY ──
    print("\n━━━ PHASE 7: TOOLS AVAILABILITY ━━━")
    await scan(c, "sqlite3", "which sqlite3 2>/dev/null && sqlite3 --version 2>/dev/null || echo NO_SQLITE3")
    await scan(c, "busybox", "which busybox 2>/dev/null && busybox --help 2>/dev/null | head -1 || echo NO_BUSYBOX")
    await scan(c, "nc_available", "which nc 2>/dev/null && nc --help 2>&1 | head -1 || echo NO_NC")
    await scan(c, "curl_available", "which curl 2>/dev/null && curl --version 2>/dev/null | head -1 || echo NO_CURL")
    await scan(c, "wget_available", "which wget 2>/dev/null || echo NO_WGET")
    await scan(c, "xxd_available", "which xxd 2>/dev/null || echo NO_XXD")
    await scan(c, "iptables", "which iptables 2>/dev/null && iptables -L -n 2>/dev/null | head -10 || echo NO_IPTABLES")
    await scan(c, "content_cmd", "which content 2>/dev/null || echo NO_CONTENT")
    await scan(c, "settings_cmd", "which settings 2>/dev/null || echo NO_SETTINGS")
    await scan(c, "pm_cmd", "pm list packages 2>/dev/null | wc -l")
    await scan(c, "dumpsys_available", "which dumpsys 2>/dev/null || echo NO_DUMPSYS")

    # ── PHASE 8: NETWORK ENVIRONMENT ──
    print("\n━━━ PHASE 8: NETWORK ENVIRONMENT ━━━")
    await scan(c, "ip_addr", "ip addr show 2>/dev/null | grep -E 'inet |link/' | head -10")
    await scan(c, "default_route", "ip route show 2>/dev/null | head -5")
    await scan(c, "dns", "cat /etc/resolv.conf 2>/dev/null 2>/dev/null; getprop net.dns1; getprop net.dns2")
    await scan(c, "connectivity", "ping -c 1 -W 3 8.8.8.8 2>/dev/null && echo INTERNET_OK || echo NO_INTERNET")
    await scan(c, "arp_neighbors", "ip neigh show 2>/dev/null | head -20")
    await scan(c, "listening_ports", "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null | head -15")

    # ── PHASE 9: FILESYSTEM & STAGING DIRS ──
    print("\n━━━ PHASE 9: FILESYSTEM & STAGING DIRS ━━━")
    await scan(c, "disk_space", "df -h 2>/dev/null | head -10")
    await scan(c, "data_free", "df -h /data 2>/dev/null")
    await scan(c, "sdcard", "ls -la /sdcard/ 2>/dev/null | head -10")
    await scan(c, "tmp_writable", "touch /data/local/tmp/.genesis_test && echo WRITABLE && rm /data/local/tmp/.genesis_test || echo NOT_WRITABLE")
    await scan(c, "dev_sc_mount", "mount 2>/dev/null | grep '/dev/.sc' || echo NOT_MOUNTED")
    await scan(c, "dev_sc_test", "mkdir -p /dev/.sc 2>/dev/null && mount -t tmpfs tmpfs /dev/.sc 2>/dev/null && touch /dev/.sc/.test && echo TMPFS_OK && rm /dev/.sc/.test || echo TMPFS_FAIL")
    await scan(c, "system_rw", "touch /system/.test_rw 2>/dev/null && echo SYSTEM_RW && rm /system/.test_rw || echo SYSTEM_RO")
    await scan(c, "vendor_rw", "touch /vendor/.test_rw 2>/dev/null && echo VENDOR_RW && rm /vendor/.test_rw || echo VENDOR_RO")

    # ── PHASE 10: INSTALLED APPS INVENTORY ──
    print("\n━━━ PHASE 10: INSTALLED APPS INVENTORY ━━━")
    await scan(c, "all_packages_count", "pm list packages 2>/dev/null | wc -l")
    await scan(c, "system_packages", "pm list packages -s 2>/dev/null | wc -l")
    await scan(c, "third_party", "pm list packages -3 2>/dev/null")
    await scan(c, "google_apps", "pm list packages 2>/dev/null | grep google | sort")
    await scan(c, "payment_apps", "pm list packages 2>/dev/null | grep -iE 'pay|wallet|bank|venmo|cash|stripe|klarna|affirm|afterpay' || echo NONE")
    await scan(c, "security_apps", "pm list packages 2>/dev/null | grep -iE 'security|antivirus|lookout|norton|avast|avg|eset|kaspersky|detect' || echo NONE")

    # ── PHASE 11: DEVICE AGE MARKERS ──
    print("\n━━━ PHASE 11: DEVICE AGE MARKERS (Genesis Phase 6) ━━━")
    await scan(c, "boot_time", "cat /proc/stat 2>/dev/null | grep btime; uptime")
    await scan(c, "first_install", "stat -c '%w %n' /data/data/com.google.android.gms 2>/dev/null || stat /data/data/com.google.android.gms 2>/dev/null | head -5")
    await scan(c, "settings_secure_age", "stat /data/system/users/0/settings_secure.xml 2>/dev/null | head -5")
    await scan(c, "usage_stats", "ls -la /data/system/usagestats/0/ 2>/dev/null")
    await scan(c, "wifi_networks", "cat /data/misc/apexdata/com.android.wifi/WifiConfigStore.xml 2>/dev/null | grep -c 'ConfigKey' || cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | grep -c 'ConfigKey' || echo 0")
    await scan(c, "contacts_count", "content query --uri content://contacts/phones 2>/dev/null | wc -l || echo 0")
    await scan(c, "call_log_count", "content query --uri content://call_log/calls 2>/dev/null | wc -l || echo 0")

    # ── PHASE 12: CRITICAL GENESIS PATHS VERIFICATION ──
    print("\n━━━ PHASE 12: CRITICAL GENESIS INJECTION PATHS ━━━")
    await scan(c, "gms_owner", "stat -c '%U:%G %a %n' /data/data/com.google.android.gms 2>/dev/null || ls -la /data/data/ | grep com.google.android.gms")
    await scan(c, "gms_db_owner", "stat -c '%U:%G %a %n' /data/data/com.google.android.gms/databases/ 2>/dev/null || ls -la /data/data/com.google.android.gms/ | grep databases")
    await scan(c, "chrome_owner", "stat -c '%U:%G %a %n' /data/data/com.android.chrome 2>/dev/null || ls -la /data/data/ | grep com.android.chrome")
    await scan(c, "accounts_db", "find /data/system_ce /data/system_de -name 'accounts*' -type f 2>/dev/null")
    await scan(c, "accounts_ce_db", "ls -la /data/system_ce/0/accounts_ce.db 2>/dev/null || echo NOT_FOUND")
    await scan(c, "settings_global", "ls -la /data/system/users/0/settings_global.xml 2>/dev/null")
    await scan(c, "keystore_dir", "ls -la /data/misc/keystore/ 2>/dev/null | head -10")
    await scan(c, "gms_billing", "ls -la /data/data/com.google.android.gms/databases/*billing* 2>/dev/null || echo NO_BILLING_DB")

    # ── PHASE 13: PLAY INTEGRITY / ATTESTATION ──
    print("\n━━━ PHASE 13: PLAY INTEGRITY & ATTESTATION ━━━")
    await scan(c, "verified_boot", "getprop ro.boot.verifiedbootstate")
    await scan(c, "vbmeta_state", "getprop ro.boot.vbmeta.device_state")
    await scan(c, "dm_verity", "getprop ro.boot.veritymode")
    await scan(c, "keymaster_hal", "ls /vendor/lib64/hw/*keymaster* /vendor/lib/hw/*keymaster* 2>/dev/null; getprop ro.hardware.keystore 2>/dev/null")
    await scan(c, "gatekeeper", "ls /vendor/lib64/hw/*gatekeeper* 2>/dev/null")
    await scan(c, "tee_os", "getprop ro.hardware.chipname 2>/dev/null; getprop ro.soc.manufacturer 2>/dev/null; getprop ro.soc.model 2>/dev/null")

    elapsed = time.time() - t0
    print(f"\n{'=' * 80}")
    print(f"SCAN COMPLETE — {len(results)} data points in {elapsed:.1f}s")
    print(f"{'=' * 80}")

    # ── GENESIS READINESS ASSESSMENT ──
    print("\n" + "█" * 80)
    print("    GENESIS PIPELINE READINESS ASSESSMENT")
    print("█" * 80)

    checks = {
        "root_access": results.get("whoami", "").startswith("uid=0"),
        "selinux_permissive": "Permissive" in results.get("selinux", ""),
        "gms_present": "com.google.android.gms" in results.get("gms_process", ""),
        "play_store": "vending" in results.get("play_store", ""),
        "chrome_present": "NOT_FOUND" not in results.get("chrome_data", "NOT_FOUND"),
        "nfc_available": results.get("nfc_service", "") and "NOT" not in results.get("nfc_service", "NOT"),
        "internet": "INTERNET_OK" in results.get("connectivity", ""),
        "staging_writable": "WRITABLE" in results.get("tmp_writable", ""),
        "sqlite3_available": "NO_SQLITE3" not in results.get("sqlite3", "NO_SQLITE3"),
        "tapandpay_exists": "NOT_FOUND" not in results.get("tapandpay_db", "NOT_FOUND"),
        "coin_xml_exists": "NOT_FOUND" not in results.get("coin_xml", "NOT_FOUND"),
        "content_provider": "NO_CONTENT" not in results.get("content_cmd", "NO_CONTENT"),
        "accounts_ce": "NOT_FOUND" not in results.get("accounts_ce_db", "NOT_FOUND"),
        "tmpfs_staging": "TMPFS_OK" in results.get("dev_sc_test", ""),
    }

    critical = ["root_access", "selinux_permissive", "gms_present", "staging_writable", "content_provider"]
    important = ["play_store", "chrome_present", "internet", "accounts_ce"]
    nice = ["nfc_available", "sqlite3_available", "tapandpay_exists", "coin_xml_exists", "tmpfs_staging"]

    score = 0
    max_score = 0

    print("\n[CRITICAL REQUIREMENTS]")
    for k in critical:
        v = checks.get(k, False)
        w = 20
        max_score += w
        score += w if v else 0
        print(f"  {'✅' if v else '❌'} {k}: {'PASS' if v else 'FAIL'} (weight: {w})")

    print("\n[IMPORTANT REQUIREMENTS]")
    for k in important:
        v = checks.get(k, False)
        w = 10
        max_score += w
        score += w if v else 0
        print(f"  {'✅' if v else '⚠️'} {k}: {'PASS' if v else 'MISSING'} (weight: {w})")

    print("\n[NICE-TO-HAVE]")
    for k in nice:
        v = checks.get(k, False)
        w = 4
        max_score += w
        score += w if v else 0
        print(f"  {'✅' if v else '⚠️'} {k}: {'PASS' if v else 'MISSING'} (weight: {w})")

    pct = (score / max_score * 100) if max_score else 0
    print(f"\n{'─' * 40}")
    print(f"GENESIS READINESS SCORE: {score}/{max_score} ({pct:.0f}%)")
    
    if pct >= 80:
        print("VERDICT: ✅ READY FOR GENESIS PIPELINE")
    elif pct >= 60:
        print("VERDICT: ⚠️ PARTIALLY READY — some modules will need workarounds")
    elif pct >= 40:
        print("VERDICT: 🔧 NEEDS PREPARATION — install missing tools, configure environment")
    else:
        print("VERDICT: ❌ NOT READY — major requirements missing")

    # Save full results
    with open(f"deep_scan_{PAD}.json", "w") as f:
        serializable = {}
        for k, v in results.items():
            if isinstance(v, (str, int, float, bool, list)):
                serializable[k] = v
            elif isinstance(v, dict):
                serializable[k] = v
            else:
                serializable[k] = str(v)
        json.dump(serializable, f, indent=2, default=str)
    print(f"\nFull results saved to deep_scan_{PAD}.json")

asyncio.run(main())
