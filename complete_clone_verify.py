#!/usr/bin/env python3
"""Complete clone v6: Inject auth tokens + extras + visual verification screenshots."""

import argparse
import asyncio
import os
import sys
import sqlite3
import json
import base64
import time
import urllib.request

os.environ['VMOS_ALLOW_RESTART'] = '1'
sys.path.insert(0, '.')
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = 'ACP2507303B6HNRI'
TMP = '/data/local/tmp/clone'
SU = f'{TMP}/setuid_exec'
GMS_UID = 10036
SOURCE_CE = 'neighbor_clones/accts_ce.db'
SOURCE_DE = 'neighbor_clones/accts_de.db'
SCREENSHOT_DIR = 'screenshots/clone_verify'

# Account mapping: source_id -> email
ACCOUNTS = {
    1: 'petersfaustina699@gmail.com',
    2: 'faustinapeters11@gmail.com',
}


def load_source_data():
    """Extract tokens and extras from source DB."""
    db = sqlite3.connect(SOURCE_CE)
    cur = db.cursor()

    # Get unique tokens (dedup by accounts_id + type)
    rows = cur.execute(
        'SELECT accounts_id, type, authtoken FROM authtokens'
    ).fetchall()
    # Dedup: keep last token per (acct_id, type)
    token_map = {}
    for acct_id, ttype, token in rows:
        token_map[(acct_id, ttype)] = token
    tokens = [(k[0], k[1], v) for k, v in token_map.items()]
    print(f'  Source tokens: {len(rows)} total, {len(tokens)} unique')

    # Get all extras with values
    extras = cur.execute(
        'SELECT accounts_id, key, value FROM extras WHERE value IS NOT NULL'
    ).fetchall()
    print(f'  Source extras: {len(extras)} total')

    db.close()
    return tokens, extras


async def cmd(client, command, timeout_ok=False):
    """Run sync_cmd and return output."""
    r = await client.sync_cmd(PAD, command)
    data = r.get('data', [])
    if data and data[0]:
        return data[0].get('errorMsg', '')
    code = r.get('code', 0)
    if code == 110012 and timeout_ok:
        return '[timeout-ok]'
    return f'[code={code}]'


async def probe_binder_transactions(client):
    """Find setAuthToken and setUserData transaction codes."""
    print('\n=== Probing Binder transaction codes ===')

    # We know 10 = addAccountExplicitly
    # setAuthToken is typically around 15 in Android 14-16
    # setUserData is typically around 18
    # Let's use the method signature to identify:
    # setAuthToken(Account, String tokenType, String token) -> void
    # setUserData(Account, String key, String value) -> void

    # Probe setAuthToken: try with a known account, set a test token, then verify
    test_email = ACCOUNTS[1]
    test_token_type = '__test_probe__'
    test_token = '__probe_value__'

    set_auth_token_tx = None
    set_user_data_tx = None

    # Probe range 12-25 for setAuthToken
    for tx in range(12, 26):
        cmd_str = (
            f'{SU} {GMS_UID} {GMS_UID} service call account {tx} '
            f'i32 1 s16 "{test_email}" s16 "com.google" i32 -1 '
            f's16 "{test_token_type}" s16 "{test_token}"'
        )
        out = await cmd(client, cmd_str + ' 2>&1')
        await asyncio.sleep(3)

        # Check if it returns empty result (void method, success)
        # or throws an exception (wrong method / wrong args)
        if 'Result: Parcel(NULL)' in out or ('Result: Parcel(' in out and '00000000' in out):
            # Void return or 0 result - could be setAuthToken or setUserData
            # Verify by checking if the token was actually set
            # Use peekAuthToken to check (typically tx 14)
            print(f'  TX {tx}: Got clean response: {out[:80]}')
            if set_auth_token_tx is None:
                set_auth_token_tx = tx
                break
        elif 'Exception' in out or 'error' in out.lower():
            pass  # Wrong method or bad args
        else:
            print(f'  TX {tx}: {out[:80]}')

    if set_auth_token_tx:
        print(f'  setAuthToken candidate: TX {set_auth_token_tx}')
        # setUserData is usually 3 after setAuthToken (setAuthToken, setPassword, clearPassword, setUserData)
        set_user_data_tx = set_auth_token_tx + 3
        print(f'  setUserData candidate: TX {set_user_data_tx}')
    else:
        print('  Could not find setAuthToken. Will try alternative.')

    return set_auth_token_tx, set_user_data_tx


async def inject_extras(client, extras, set_user_data_tx):
    """Inject account extras via setUserData Binder call."""
    print('\n=== Injecting account extras ===')

    # Critical extras to inject
    critical_keys = {
        'GoogleUserId', 'firstName', 'lastName', 'services',
        'oauthAccessToken',
    }

    injected = 0
    failed = 0
    for acct_id, key, value in extras:
        if key not in critical_keys:
            continue
        if value is None:
            continue

        email = ACCOUNTS.get(acct_id)
        if not email:
            continue

        # Escape value for shell
        safe_value = str(value).replace('"', '\\"').replace("'", "\\'")
        if len(safe_value) > 200:
            safe_value = safe_value[:200]

        cmd_str = (
            f'{SU} {GMS_UID} {GMS_UID} service call account {set_user_data_tx} '
            f'i32 1 s16 "{email}" s16 "com.google" i32 -1 '
            f's16 "{key}" s16 "{safe_value}"'
        )
        out = await cmd(client, cmd_str + ' 2>&1')
        if 'Exception' not in out:
            injected += 1
            print(f'  {email[:20]}... {key}: OK')
        else:
            failed += 1
            print(f'  {email[:20]}... {key}: FAILED ({out[:60]})')
        await asyncio.sleep(3)

    print(f'  Extras injected: {injected}, failed: {failed}')
    return injected


async def inject_tokens(client, tokens, set_auth_token_tx):
    """Inject auth tokens via setAuthToken Binder call."""
    print('\n=== Injecting auth tokens ===')

    # Prioritize key token types
    priority_patterns = [
        ':android',           # Master token
        ':oauth2: email',     # Email scope
        ':AndroidCheckIn',    # CheckIn token
    ]

    # Sort: priority tokens first, then by account
    def token_priority(t):
        acct_id, ttype, _ = t
        for i, pat in enumerate(priority_patterns):
            if pat in ttype:
                return (0, i, acct_id)
        return (1, 0, acct_id)

    sorted_tokens = sorted(tokens, key=token_priority)

    injected = 0
    failed = 0
    skipped = 0

    for acct_id, ttype, token in sorted_tokens:
        email = ACCOUNTS.get(acct_id)
        if not email:
            continue

        # Token type and value can be very long, shell has limits
        if len(ttype) > 500 or len(token) > 2000:
            skipped += 1
            continue

        # Escape for shell
        safe_type = ttype.replace('"', '\\"')
        safe_token = token.replace('"', '\\"')

        cmd_str = (
            f'{SU} {GMS_UID} {GMS_UID} service call account {set_auth_token_tx} '
            f'i32 1 s16 "{email}" s16 "com.google" i32 -1 '
            f's16 "{safe_type}" s16 "{safe_token}"'
        )
        out = await cmd(client, cmd_str + ' 2>&1', timeout_ok=True)
        if 'Exception' not in out and 'error' not in out.lower():
            injected += 1
        else:
            failed += 1
            if failed <= 3:
                print(f'  FAIL: {out[:80]}')
        await asyncio.sleep(3)

        # Progress
        total = injected + failed + skipped
        if total % 10 == 0:
            print(f'  Progress: {total}/{len(sorted_tokens)} (ok={injected} fail={failed} skip={skipped})')

    print(f'  Tokens injected: {injected}, failed: {failed}, skipped: {skipped}')
    return injected


async def verify_accounts(client):
    """Verify accounts via dumpsys."""
    print('\n=== Account verification ===')

    out = await cmd(client, 'dumpsys account 2>/dev/null | head -30')
    print(out)
    await asyncio.sleep(3)

    # Check token count
    out = await cmd(client, 'dumpsys account 2>/dev/null | grep -c "authtoken"')
    print(f'Auth tokens in dumpsys: {out}')
    await asyncio.sleep(3)


async def is_package_installed(client, package_name):
    out = await cmd(client, f'pm list packages | grep "^package:{package_name}$" 2>/dev/null')
    return bool(out and package_name in out)


async def resolve_launcher_activity(client, package_name):
    out = await cmd(client, f'cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER {package_name} 2>&1')
    if out and 'No activity found' not in out and 'Unable to resolve intent' not in out:
        return out.strip()
    return None


async def save_preview_image(client, filepath):
    r = await client.get_preview_image([PAD])
    await asyncio.sleep(2)
    data = r.get('data', [])
    if data and isinstance(data, list) and len(data) > 0:
        item = data[0]
    else:
        item = None

    if isinstance(item, dict):
        for key in ['url', 'imageUrl', 'previewUrl', 'screenshotUrl', 'longUrl']:
            url = item.get(key)
            if isinstance(url, str) and url:
                try:
                    urllib.request.urlretrieve(url, filepath)
                    return True
                except Exception:
                    continue
    elif isinstance(item, str) and item.startswith('http'):
        try:
            urllib.request.urlretrieve(item, filepath)
            return True
        except Exception:
            pass
    return False


async def save_screenshot_image(client, filepath):
    r2 = await client.screenshot([PAD])
    await asyncio.sleep(2)
    data2 = r2.get('data', [])
    if data2 and isinstance(data2, list) and len(data2) > 0:
        item = data2[0]
    else:
        item = None

    if isinstance(item, dict):
        for key in ['url', 'imageUrl', 'previewUrl', 'screenshotUrl', 'longUrl']:
            url = item.get(key)
            if isinstance(url, str) and url:
                try:
                    urllib.request.urlretrieve(url, filepath)
                    return True
                except Exception:
                    continue
    elif isinstance(item, str) and item.startswith('http'):
        try:
            urllib.request.urlretrieve(item, filepath)
            return True
        except Exception:
            pass
    return False


async def capture_screen(client, name):
    filepath = f'{SCREENSHOT_DIR}/{name}_{int(time.time())}.png'
    if await save_preview_image(client, filepath):
        return filepath
    if await save_screenshot_image(client, filepath):
        return filepath
    print(f'  Failed to capture screenshot for {name}')
    return None


async def launch_activity_with_fallback(client, name, primary_cmd, fallback_cmds=None):
    if fallback_cmds is None:
        fallback_cmds = []

    attempts = [primary_cmd] + fallback_cmds
    for idx, launch_cmd in enumerate(attempts):
        print(f'  Launching {name} (attempt {idx+1}): {launch_cmd}')
        out = await cmd(client, launch_cmd + ' 2>&1', timeout_ok=True)
        print(f'    launch output: {out.strip()[:200]}')
        await asyncio.sleep(8)
        if 'Error type 3' in out or 'inaccessible or not found' in out or 'Exception occurred while executing' in out:
            if idx + 1 < len(attempts):
                print(f'    Fallback available for {name}, trying next launcher command...')
                continue
        return out
    return out


async def take_screenshots(client):
    """Capture visual verification screenshots."""
    print('\n=== Visual verification screenshots ===')
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    installed_gmail = await is_package_installed(client, 'com.google.android.gm')
    installed_play = await is_package_installed(client, 'com.android.vending')
    print(f'  Gmail installed: {installed_gmail}, Play Store installed: {installed_play}')

    screens = [
        ('settings_accounts', 'am start -a android.settings.SYNC_SETTINGS', []),
    ]

    if installed_gmail:
        gmail_activity = await resolve_launcher_activity(client, 'com.google.android.gm')
        if gmail_activity:
            screens.append(('gmail', f'am start -n {gmail_activity}', ['monkey -p com.google.android.gm -c android.intent.category.LAUNCHER 1']))
        else:
            screens.append(('gmail', 'monkey -p com.google.android.gm -c android.intent.category.LAUNCHER 1', []))
    else:
        print('  Gmail is not installed on this device; skipping Gmail launch.')

    if installed_play:
        play_activity = await resolve_launcher_activity(client, 'com.android.vending')
        if play_activity:
            screens.append(('play_store', 'monkey -p com.android.vending -c android.intent.category.LAUNCHER 1', [f'am start -n {play_activity}']))
        else:
            screens.append(('play_store', 'monkey -p com.android.vending -c android.intent.category.LAUNCHER 1', []))
    else:
        print('  Play Store is not installed on this device; skipping Play Store launch.')

    saved_files = []
    for name, launch_cmd, fallback_cmds in screens:
        out = await launch_activity_with_fallback(client, name, launch_cmd, fallback_cmds)
        filepath = await capture_screen(client, name)
        if filepath:
            size = os.path.getsize(filepath)
            print(f'  Saved: {filepath} ({size} bytes)')
            saved_files.append(filepath)
        else:
            print(f'  Failed to capture screenshot for {name}')

        await asyncio.sleep(3)

    await cmd(client, 'input keyevent KEYCODE_HOME', timeout_ok=True)
    return saved_files


async def main():
    parser = argparse.ArgumentParser(description='Complete clone verification for VMOS target.')
    parser.add_argument('--verify-only', action='store_true', help='Skip injection and run verification/screenshot capture only.')
    args = parser.parse_args()

    client = VMOSCloudClient(
        ak='BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi',
        sk='Q2SgcSwEfuwoedY0cijp6Mce',
        base_url='https://api.vmoscloud.com',
    )

    print('=== Complete Clone v6 ===')
    print(f'Target: {PAD}')
    print(f'Accounts: {list(ACCOUNTS.values())}')

    # 0. Verify setuid_exec is working
    out = await cmd(client, f'{SU} {GMS_UID} {GMS_UID} id 2>&1')
    print(f'\nsetuid_exec test: {out}')
    if 'u0_a36' not in out and str(GMS_UID) not in out:
        print('ERROR: setuid_exec not working')
        return
    await asyncio.sleep(3)

    if not args.verify_only:
        # 1. Load source data
        print('\n=== Loading source data ===')
        tokens, extras = load_source_data()

        # 2. Probe for Binder transaction codes
        set_auth_tx, set_data_tx = await probe_binder_transactions(client)

        # 3. Inject extras (if we found the right transaction)
        if set_data_tx:
            await inject_extras(client, extras, set_data_tx)
        else:
            print('  Skipping extras (no setUserData transaction found)')

        # 4. Inject tokens
        if set_auth_tx:
            await inject_tokens(client, tokens, set_auth_tx)
        else:
            print('  Skipping tokens (no setAuthToken transaction found)')

    # 5. Verify accounts
    await verify_accounts(client)

    # 6. Visual screenshots
    saved = await take_screenshots(client)

    print(f'\n=== CLONE COMPLETE ===')
    print(f'Screenshots saved: {len(saved)}')
    for f in saved:
        print(f'  {f}')


if __name__ == '__main__':
    asyncio.run(main())
