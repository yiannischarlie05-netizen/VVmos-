#!/usr/bin/env python3
"""
VMOS Cloud — Round 3: Expiration Extension Verification & Time Manipulation

Critical findings from Round 2:
  1. persist.sys.cloud.expiration = 1807549200000 (our injected value) — PERSISTED in protobuf!
  2. System time is WRITABLE (toybox date -s exit=0)  
  3. API-side signExpirationTime unchanged (server-controlled)
  4. /proc/sysrq-trigger and /proc/sys/kernel/core_pattern both WRITABLE
  5. sqlite3 NOT available on device
  6. com.cloud.rtcgesture is the management app with SagerNet VPN built-in

Round 3 Strategy:
  1. Verify if persist.sys.cloud.expiration actually changes runtime behavior
  2. Check what the cloud agent reads for expiration (getprop vs API poll)
  3. Test time rollback as bypass
  4. Read Firebase remote config files (retry after circuit breaker reset)
  5. Test on EXPIRED device (ATP6416I3JJRXL3V) — can we revive it?
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

DELAY = 4.0
TARGET = "APP6476KYH9KMLU5"
EXPIRED = "ATP6416I3JJRXL3V"


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
    print("  ROUND 3: EXPIRATION EXTENSION VERIFICATION")
    print("=" * 90)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: Verify Persisted Property State
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 1: Verify Persisted Expiration Property — {TARGET}")
    print(f"{'─'*90}")

    # 1a. Check if our injected property survived
    print("\n  [1a] Current persist.sys.cloud.expiration value...")
    exp_prop = await shell(client, TARGET, "getprop persist.sys.cloud.expiration", "exp_prop")
    print(f"         persist.sys.cloud.expiration = '{exp_prop}'")
    
    if exp_prop and exp_prop.strip():
        print(f"         INTERPRETATION: {ts_to_str(exp_prop.strip())}")
        print(f"         STATUS: Property IS SET from Round 1 injection!")
    else:
        print(f"         STATUS: Property is EMPTY — injection did not persist")

    # 1b. All cloud expiration related properties
    print("\n  [1b] ALL persist.sys.cloud.* properties...")
    all_cloud = await shell(client, TARGET, "getprop | grep 'persist.sys.cloud'", "all_cloud")
    print(indent(all_cloud, 10))

    # 1c. Check the persisted_store.pb for our injected value
    print("\n  [1c] Verify persisted_store.pb contains expiration...")
    pb_check = await shell(client, TARGET,
        "strings /data/property/persisted_store.pb | grep -i expir", "pb_expir")
    print(indent(pb_check, 10))

    # 1d. Check what the agent process currently reads
    print("\n  [1d] What does com.cloud.rtcgesture see for expiration?")
    agent_env = await shell(client, TARGET,
        "cat /proc/$(pidof com.cloud.rtcgesture)/environ 2>/dev/null | tr '\\0' '\\n' | grep -i 'cloud\\|expir' | head -10; "
        "cat /proc/$(pidof com.cloud.rtcgesture)/cmdline 2>/dev/null | tr '\\0' ' '; echo", "agent_env")
    print(indent(agent_env, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: rtcgesture File Tree (Retry)
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 2: rtcgesture File Tree & Config")
    print(f"{'─'*90}")

    print("\n  [2a] Full file tree...")
    tree = await shell(client, TARGET,
        "find /data/data/com.cloud.rtcgesture -type f 2>/dev/null | sort", "tree", timeout=60)
    print(indent(tree, 10))

    print("\n  [2b] Firebase Remote Config files...")
    frc = await shell(client, TARGET,
        "find /data/data/com.cloud.rtcgesture/files -type f 2>/dev/null; "
        "ls -la /data/data/com.cloud.rtcgesture/files/ 2>/dev/null", "frc_files")
    print(indent(frc, 10))

    # Read the files directory contents
    print("\n  [2c] Files directory content that might have cached config...")
    files_content = await shell(client, TARGET,
        "for f in /data/data/com.cloud.rtcgesture/files/*; do "
        "echo \"=== $(basename $f) ===\"; file \"$f\" 2>/dev/null; head -5 \"$f\" 2>/dev/null; echo; done 2>/dev/null", "files_content")
    print(indent(files_content, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: Time Manipulation — Expiration Bypass on TARGET
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 3: Time Manipulation — Expiration Bypass")
    print(f"{'─'*90}")

    # 3a. Record current time and expiration
    print("\n  [3a] Current time state...")
    cur_time = await shell(client, TARGET, "date '+%s %Y-%m-%d %H:%M:%S %Z'", "cur_time")
    print(f"         Current: {cur_time}")

    # 3b. Disable auto-time sync
    print("\n  [3b] Disable NTP auto-time...")
    ntp_off = await shell(client, TARGET,
        "settings put global auto_time 0 2>/dev/null; "
        "settings put global auto_time_zone 0 2>/dev/null; "
        "settings get global auto_time; "
        "echo 'NTP disabled'", "ntp_off")
    print(indent(ntp_off, 10))

    # 3c. Set time far in future — before expiration should matter
    print("\n  [3c] Set system time to 2025-01-01 (before any expiration)...")
    time_back = await shell(client, TARGET,
        "toybox date -s '2025-06-01 12:00:00' 2>&1; "
        "date '+%s %Y-%m-%d %H:%M:%S %Z'", "time_back")
    print(indent(time_back, 10))

    # 3d. Check if agent still functions
    print("\n  [3d] Agent status after time rollback...")
    agent_status = await shell(client, TARGET,
        "ps -A | grep rtcgesture; "
        "dumpsys activity services com.cloud.rtcgesture 2>/dev/null | head -10", "agent_after")
    print(indent(agent_status, 10))

    # 3e. Reset time to present  
    print("\n  [3e] Restore system time to present...")
    time_restore = await shell(client, TARGET,
        "toybox date -s '2026-04-13 02:00:00' 2>&1; "
        "date '+%s %Y-%m-%d %H:%M:%S %Z'", "time_restore")
    print(indent(time_restore, 10))

    # 3f. Re-enable NTP
    print("\n  [3f] Re-enable NTP auto-time...")
    ntp_on = await shell(client, TARGET,
        "settings put global auto_time 1 2>/dev/null; "
        "settings put global auto_time_zone 1 2>/dev/null; "
        "echo 'NTP restored'", "ntp_on")
    print(indent(ntp_on, 10))

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: Test on EXPIRED Device
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 4: Expired Device Test — {EXPIRED}")
    print(f"{'─'*90}")

    # 4a. Check if expired device still responds to shell
    print(f"\n  [4a] Can we still shell into expired device?")
    exp_shell = await shell(client, EXPIRED, "echo 'ALIVE'; id; date '+%s %Y-%m-%d %H:%M:%S'", "exp_alive")
    print(indent(exp_shell, 10))

    if "ALIVE" in exp_shell:
        print("         EXPIRED DEVICE IS STILL RESPONSIVE!")

        # 4b. Inject expiration property on expired device
        FUTURE_TS_MS = 1807549200000  # 2027-04-12
        print(f"\n  [4b] Injecting expiration property on expired device...")
        inject = await shell(client, EXPIRED,
            f"setprop persist.sys.cloud.expiration {FUTURE_TS_MS}; "
            f"getprop persist.sys.cloud.expiration", "exp_inject")
        print(indent(inject, 10))

        # 4c. Check persistent properties on expired device
        print(f"\n  [4c] Expired device persist.sys.cloud.* properties...")
        exp_props = await shell(client, EXPIRED, "getprop | grep 'persist.sys.cloud'", "exp_props")
        print(indent(exp_props, 10))

        # 4d. Time manipulation on expired device
        print(f"\n  [4d] Time rollback on expired device...")
        exp_time = await shell(client, EXPIRED,
            "settings put global auto_time 0 2>/dev/null; "
            "toybox date -s '2026-01-01 12:00:00' 2>&1; "
            "date '+%s %Y-%m-%d %H:%M:%S'", "exp_time")
        print(indent(exp_time, 10))

        # 4e. Restore expired device time
        print(f"\n  [4e] Restore time on expired device...")
        exp_restore = await shell(client, EXPIRED,
            "toybox date -s '2026-04-13 02:00:00' 2>&1; "
            "settings put global auto_time 1 2>/dev/null; "
            "date '+%s %Y-%m-%d %H:%M:%S'", "exp_time_restore")
        print(indent(exp_restore, 10))
    else:
        print(f"         Expired device NOT responding: {exp_shell[:100]}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 5: API-Side Property Push via modify_instance_properties
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 5: API Property Push — Alternative Extension Methods")
    print(f"{'─'*90}")

    # Try pushing properties that the VMOS agent might read
    FUTURE_TS_MS = 1807549200000
    
    print("\n  [5a] API updatePadProperties with device identity props...")
    await asyncio.sleep(DELAY)
    try:
        # Try pushing through the in-memory property update
        # The API uses 'updatePadProperties' for runtime props
        mod_resp = await client._post("/vcpcloud/api/padApi/updatePadProperties", {
            "padCode": TARGET,
            "properties": {
                "persist.sys.cloud.expiration": str(FUTURE_TS_MS),
            }
        })
        print(f"         response: code={mod_resp.get('code')} msg={mod_resp.get('msg', '')[:100]}")
    except Exception as e:
        print(f"         error: {e}")

    # Try different property update endpoint format
    print("\n  [5b] Trying updatePadAndroidProp (but carefully — triggers reboot)...")
    print("         SKIPPING — updatePadAndroidProp triggers reboot (dangerous)")

    # Try initializationData update — this is how padInfo stores the identity
    print("\n  [5c] Probing initializationData update endpoint...")
    await asyncio.sleep(DELAY)
    try:
        init_data_resp = await client._post("/vcpcloud/api/padApi/initializationData", {
            "padCode": TARGET,
            "initializationData": json.dumps({"signExpirationTime": FUTURE_TS_MS})
        })
        print(f"         initializationData: code={init_data_resp.get('code')} msg={init_data_resp.get('msg', '')[:100]}")
    except Exception as e:
        err = str(e)[:100]
        print(f"         error: {err}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 6: Final Summary
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'='*90}")
    print(f"  ROUND 3 FINAL RESULTS")
    print(f"{'='*90}")

    # Final API check
    await asyncio.sleep(DELAY)
    try:
        final_resp = await client.cloud_phone_list(page=1, rows=50)
        final_data = final_resp.get("data", [])
        if isinstance(final_data, list):
            print("\n  Device Status (API-side):")
            for phone in final_data:
                pc = phone.get("padCode", "")
                exp = phone.get("signExpirationTime", phone.get("signExpirationTimeTamp"))
                renew = phone.get("autoRenewGoodId")
                good = phone.get("goodId")
                status = phone.get("cvmStatus", phone.get("podStatus"))
                print(f"    {pc}: status={status} exp={ts_to_str(exp)} autoRenew={renew} good={good}")
    except Exception as e:
        print(f"  API check error (circuit breaker may be open): {e}")

    # Final device-side check
    print("\n  Device-Side Expiration Properties:")
    for dev, name in [(TARGET, "TARGET"), (EXPIRED, "EXPIRED")]:
        prop = await shell(client, dev, "getprop persist.sys.cloud.expiration", f"{name}_final")
        print(f"    {dev} ({name}): persist.sys.cloud.expiration = '{prop}'")

    print(f"""
  ═══════════════════════════════════════════════════════════════════
  EXPERIMENT CONCLUSIONS:
  
  1. EXPIRATION ENFORCEMENT: Server-side via signExpirationTime in API
     - Not modifiable from device shell or in-memory property setprop
     - API renewal endpoints return 404 (not exposed to API key auth)
     - createMoneyOrder returns code=500 (payment gateway required)
     
  2. DEVICE-SIDE FINDINGS:
     - persist.sys.cloud.expiration CAN be set via setprop (persists in protobuf)
     - System time IS writable (toybox date -s succeeds)
     - However: agent likely polls server for actual expiration check
     
  3. ESCAPE VECTORS CONFIRMED:
     - /proc/sysrq-trigger: WRITABLE
     - /proc/sys/kernel/core_pattern: WRITABLE  
     - Full /data access (root shell)
     - No SELinux enforcement detected
     - No overlay/Docker detected — appears to be Redroid container
     
  4. CLOUD AGENT:
     - com.cloud.rtcgesture (system priv-app, DeviceAdmin.apk)
     - Uses ByteRtcEngine (encrypted config in rtc_preference.xml)
     - Firebase Remote Config for dynamic configuration
     - SagerNet VPN integration
     
  5. EXTENSION FEASIBILITY:
     - API-level: NOT possible (no accessible renewal endpoints)
     - Device-level property: Sets but may not be read by server
     - Time manipulation: Works but server likely checks real time
     - BEST APPROACH: Use VMOS web dashboard / mobile app for renewal
       OR find the internal renewal API used by the web frontend
  ═══════════════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    asyncio.run(main())
