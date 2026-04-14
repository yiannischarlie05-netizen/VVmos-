#!/usr/bin/env python3
"""
Proper Google Account Injection — No-Password Cold Checkin Strategy
====================================================================
Based on genesis_fix2.py approach (most battle-tested in codebase).

Strategy:
  - Build accounts_ce.db with NO password, NO fake tokens
  - Build accounts_de.db with visibility entries for all Google apps
  - Nuke ALL cached GMS/GSF state → force cold checkin
  - Push databases + minimal SharedPrefs
  - Trigger CheckinService → GMS registers device
  - Device shows "Sign in" notification → user taps → real tokens

Target device: AC32010810392 (SM-S9280, Android 15)
Account: socarsocar100@gmail.com / Socar
"""

import asyncio
import base64
import hashlib
import os
import random
import secrets
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

PAD = 'AC32010810392'
EMAIL = 'socarsocar100@gmail.com'
DISPLAY_NAME = 'Socar'
GAIA_ID = str(random.randint(100000000000000000, 999999999999999999))
ANDROID_ID = '418a2e0b9807cad5'
DELAY = 3.5
CHUNK = 2048  # b64 chunk size for VMOS syncCmd

# UIDs (verified from device)
GMS_UID = 10036
GSF_UID = 10036
VENDING_UID = 10042
CHROME_UID = 10058


# ═══════════════════════════════════════════════════════════════════════
# DB BUILDERS (from genesis_fix2.py — proven)
# ═══════════════════════════════════════════════════════════════════════

def build_accounts_ce(email, password=None):
    """Build accounts_ce.db — password=None forces anonymous checkin."""
    gaia = GAIA_ID
    disp = DISPLAY_NAME
    parts = disp.split()
    birth = int((time.time() - 90 * 86400) * 1000)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        p = f.name
    try:
        conn = sqlite3.connect(p)
        c = conn.cursor()
        c.executescript("""
            CREATE TABLE android_metadata (locale TEXT);
            CREATE TABLE accounts (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, type TEXT NOT NULL,
                password TEXT, UNIQUE(name, type));
            CREATE TABLE authtokens (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                accounts_id INTEGER NOT NULL,
                type TEXT NOT NULL, authtoken TEXT,
                UNIQUE(accounts_id, type));
            CREATE TABLE extras (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                accounts_id INTEGER, key TEXT NOT NULL,
                value TEXT, UNIQUE(accounts_id, key));
            CREATE TABLE grants (
                accounts_id INTEGER NOT NULL,
                auth_token_type TEXT NOT NULL DEFAULT '',
                uid INTEGER NOT NULL,
                UNIQUE(accounts_id, auth_token_type, uid));
            CREATE TABLE shared_accounts (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, type TEXT NOT NULL,
                UNIQUE(name, type));
            PRAGMA user_version = 10;
        """)
        c.execute("INSERT INTO android_metadata VALUES ('en_US')")
        c.execute("INSERT INTO accounts (name, type, password) VALUES (?, 'com.google', ?)",
                  (email, password))
        aid = c.lastrowid

        for k, v in [
            ("google.services.gaia", gaia),
            ("GoogleUserId", gaia),
            ("is_child_account", "false"),
            ("given_name", parts[0] if parts else ""),
            ("family_name", parts[-1] if len(parts) > 1 else ""),
            ("display_name", disp),
            ("account_creation_time", str(birth)),
        ]:
            c.execute("INSERT INTO extras (accounts_id, key, value) VALUES (?,?,?)",
                      (aid, k, v))

        c.execute("INSERT INTO shared_accounts (name, type) VALUES (?, 'com.google')", (email,))

        # Grant access to key system UIDs
        for uid in (1000, GMS_UID, VENDING_UID, 10000, 10001):
            c.execute("INSERT OR IGNORE INTO grants (accounts_id, auth_token_type, uid) VALUES (?,'',?)",
                      (aid, uid))
            for tt in ("com.google", "SID", "LSID"):
                c.execute("INSERT OR IGNORE INTO grants (accounts_id, auth_token_type, uid) VALUES (?,?,?)",
                          (aid, tt, uid))

        conn.commit()
        conn.close()
        return Path(p).read_bytes()
    finally:
        Path(p).unlink(missing_ok=True)


def build_accounts_de(email):
    """Build accounts_de.db with visibility entries for all Google apps."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        p = f.name
    try:
        conn = sqlite3.connect(p)
        c = conn.cursor()
        c.executescript("""
            CREATE TABLE accounts (
                _id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                type TEXT NOT NULL, previous_name TEXT,
                last_password_entry_time_millis_epoch INTEGER DEFAULT 0,
                UNIQUE(name, type));
            CREATE TABLE grants (
                accounts_id INTEGER NOT NULL,
                auth_token_type TEXT NOT NULL DEFAULT '',
                uid INTEGER NOT NULL,
                UNIQUE(accounts_id, auth_token_type, uid));
            CREATE TABLE visibility (
                accounts_id INTEGER NOT NULL,
                _package TEXT NOT NULL, value INTEGER,
                UNIQUE(accounts_id, _package));
            CREATE TABLE authtokens (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                accounts_id INTEGER NOT NULL,
                type TEXT NOT NULL DEFAULT '', authtoken TEXT,
                UNIQUE(accounts_id, type));
            CREATE TABLE extras (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                accounts_id INTEGER NOT NULL,
                key TEXT NOT NULL DEFAULT '', value TEXT,
                UNIQUE(accounts_id, key));
            PRAGMA user_version = 3;
        """)
        c.execute("INSERT INTO accounts VALUES (1,?,'com.google',NULL,?)",
                  (email, int(time.time() * 1000)))

        # Visibility entries — all apps that need to see the account
        for pkg in (
            "com.google.android.gms",
            "com.android.vending",
            "com.google.android.gsf",
            "com.android.chrome",
            "com.google.android.youtube",
            "com.google.android.gm",
            "com.google.android.apps.walletnfcrel",
            "com.google.android.googlequicksearchbox",
            "com.google.android.apps.maps",
            "com.google.android.apps.photos",
            "com.google.android.calendar",
            "com.google.android.contacts",
            "com.google.android.apps.docs",
            "com.google.android.keep",
        ):
            c.execute("INSERT OR IGNORE INTO visibility VALUES (1,?,1)", (pkg,))

        conn.commit()
        conn.close()
        return Path(p).read_bytes()
    finally:
        Path(p).unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════════════════
# VMOS HELPERS
# ═══════════════════════════════════════════════════════════════════════

_client = None
_last_cmd = 0.0


async def get_client():
    global _client
    if _client is None:
        from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
        _client = VMOSCloudClient(
            ak='YOUR_VMOS_AK_HERE',
            sk='YOUR_VMOS_SK_HERE',
            base_url='https://api.vmoscloud.com'
        )
    return _client


async def cmd(shell_cmd, label='', timeout=30):
    """Execute shell command with rate limiting."""
    global _last_cmd
    elapsed = time.time() - _last_cmd
    if elapsed < DELAY:
        await asyncio.sleep(DELAY - elapsed)
    _last_cmd = time.time()

    c = await get_client()
    for attempt in range(3):
        try:
            r = await c.sync_cmd(PAD, shell_cmd, timeout_sec=timeout)
            if not isinstance(r, dict):
                await asyncio.sleep(5)
                continue
            code = r.get('code')
            if code == 200:
                data = r.get('data')
                if data is None:
                    return ''
                if isinstance(data, list) and data:
                    out = data[0].get('errorMsg', '') if isinstance(data[0], dict) else ''
                    if label and out and 'CHUNK' not in label:
                        print(f'  [{label}] {out.strip()[:200]}')
                    return out or ''
                return ''
            if code == 110012:
                print(f'  [{label}] timeout (attempt {attempt+1}/3)')
                await asyncio.sleep(8)
                continue
            return ''
        except Exception as e:
            print(f'  [{label}] error: {e}')
            await asyncio.sleep(5)
    return ''


async def push_bytes(data, target_path, owner='system:system', mode='660'):
    """Push file to device via base64 chunking."""
    b64 = base64.b64encode(data).decode()
    h = hashlib.md5(target_path.encode()).hexdigest()[:8]
    stg = f'/sdcard/.inj_{h}'
    b64f = f'{stg}.b64'
    name = target_path.split('/')[-1]
    chunks = [b64[i:i+CHUNK] for i in range(0, len(b64), CHUNK)]
    print(f'  Pushing {len(data)} bytes -> {name} ({len(chunks)} chunks)')

    await cmd(f'rm -f {b64f} {stg}')
    for i, ch in enumerate(chunks):
        safe = ch.replace("'", "'\\''")
        await cmd(f"echo -n '{safe}' >> {b64f}", f'CHUNK {i+1}/{len(chunks)}')
        if (i + 1) % 15 == 0:
            print(f'    chunk {i+1}/{len(chunks)}')

    await cmd(f'base64 -d {b64f} > {stg}')
    sz = await cmd(f'wc -c < {stg}')
    try:
        actual = int(sz.strip())
        if actual != len(data):
            print(f'    SIZE MISMATCH: {actual} vs {len(data)}')
            return False
    except (ValueError, AttributeError):
        pass

    d = os.path.dirname(target_path)
    await cmd(f'mkdir -p {d}')
    await cmd(f'cp {stg} {target_path}')
    await cmd(f'chown {owner} {target_path}')
    await cmd(f'chmod {mode} {target_path}')
    await cmd(f'restorecon {target_path}')
    await cmd(f'rm -f {b64f} {stg}')
    v = await cmd(f'ls -la {target_path}')
    ok = name in (v or '')
    print(f'    -> {"OK" if ok else "FAIL"}')
    return ok


# ═══════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════

async def main():
    t0 = time.time()
    print('=' * 65)
    print('  PROPER GOOGLE ACCOUNT INJECTION')
    print(f'  Target: {PAD}')
    print(f'  Account: {EMAIL}')
    print(f'  Display: {DISPLAY_NAME}')
    print('  Strategy: No-password + Cold Checkin (genesis_fix2 approach)')
    print('=' * 65)

    # ── Phase 1: Verify device ────────────────────────────────────────
    print('\n▸ PHASE 1: VERIFY DEVICE')
    root = await cmd('id -u', 'ROOT')
    if '0' not in (root or ''):
        print('  FAIL: not root')
        return
    print('  Root confirmed')

    # ── Phase 2: Build databases ──────────────────────────────────────
    print('\n▸ PHASE 2: BUILD DATABASES')
    print('  Building accounts_ce.db (NO password, NO tokens)')
    ce = build_accounts_ce(EMAIL, password=None)
    print(f'  accounts_ce.db: {len(ce)} bytes')

    de = build_accounts_de(EMAIL)
    print(f'  accounts_de.db: {len(de)} bytes')

    # ── Phase 3: Stop + Nuke cached state ─────────────────────────────
    print('\n▸ PHASE 3: STOP GOOGLE APPS + NUKE CACHED STATE')
    for pkg in ['com.android.vending', 'com.google.android.gms',
                'com.google.android.gsf', 'com.google.android.gm',
                'com.google.android.youtube', 'com.android.chrome',
                'com.google.android.apps.walletnfcrel']:
        await cmd(f'am force-stop {pkg}')
    print('  All Google apps stopped')

    # Remove old DBs
    print('  Removing old account databases...')
    await cmd('rm -f /data/system_ce/0/accounts_ce.db* /data/system_de/0/accounts_de.db*')

    # Nuke ALL cached auth/checkin/gsf state
    print('  Nuking GMS/GSF cached state (force cold checkin)...')
    await cmd('rm -rf /data/data/com.google.android.gsf/databases/*')
    await cmd('rm -rf /data/data/com.google.android.gsf/shared_prefs/*')
    await cmd('rm -f /data/data/com.google.android.gms/shared_prefs/CheckinService.xml')
    await cmd('rm -f /data/data/com.google.android.gms/shared_prefs/CheckinAccount.xml')
    await cmd('rm -f /data/data/com.google.android.gms/shared_prefs/GservicesSettings.xml')
    await cmd('rm -rf /data/data/com.google.android.gms/databases/auth*.db*')
    await cmd('rm -rf /data/data/com.android.vending/cache/*')
    await cmd('rm -rf /data/data/com.google.android.gms/cache/*')
    print('  All cached state cleared')

    # ── Phase 4: Push databases ───────────────────────────────────────
    print('\n▸ PHASE 4: PUSH DATABASES')
    ce_ok = await push_bytes(ce, '/data/system_ce/0/accounts_ce.db', '1000:1000', '600')
    de_ok = await push_bytes(de, '/data/system_de/0/accounts_de.db', '1000:1000', '600')

    if not ce_ok:
        print('  CRITICAL: accounts_ce.db push FAILED')
        return

    # Remove WAL/SHM/journal that might conflict
    await cmd('rm -f /data/system_ce/0/accounts_ce.db-wal /data/system_ce/0/accounts_ce.db-shm /data/system_ce/0/accounts_ce.db-journal')
    await cmd('rm -f /data/system_de/0/accounts_de.db-wal /data/system_de/0/accounts_de.db-shm /data/system_de/0/accounts_de.db-journal')

    # ── Phase 5: Push SharedPrefs ─────────────────────────────────────
    print('\n▸ PHASE 5: PUSH SharedPrefs')

    # CheckinAccount (just account binding, no auth data)
    checkin_xml = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="account_name">{EMAIL}</string>
    <string name="account_type">com.google</string>
    <boolean name="registered" value="true" />
</map>
"""
    await push_bytes(checkin_xml.encode(), '/data/data/com.google.android.gms/shared_prefs/CheckinAccount.xml',
                     f'{GMS_UID}:{GMS_UID}', '660')

    # finsky (Play Store signed-in state)
    finsky_xml = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="signed_in_account">{EMAIL}</string>
    <string name="first_account_name">{EMAIL}</string>
    <boolean name="logged_in" value="true" />
    <boolean name="setup_done" value="true" />
    <boolean name="setup_wizard_has_run" value="true" />
    <boolean name="tos_accepted" value="true" />
    <boolean name="auto_update_enabled" value="true" />
</map>
"""
    await push_bytes(finsky_xml.encode(), '/data/data/com.android.vending/shared_prefs/finsky.xml',
                     f'{VENDING_UID}:{VENDING_UID}', '660')

    # ── Phase 6: SELinux restore ──────────────────────────────────────
    print('\n▸ PHASE 6: RESTORECON')
    await cmd('restorecon -R /data/system_ce/0/ /data/system_de/0/ '
              '/data/data/com.google.android.gms/shared_prefs '
              '/data/data/com.android.vending/shared_prefs', 'RESTORECON')

    # ── Phase 7: Trigger GMS Cold Checkin ─────────────────────────────
    print('\n▸ PHASE 7: TRIGGER GMS COLD CHECKIN')
    await cmd('am force-stop com.google.android.gms')
    await cmd('am force-stop com.google.android.gsf')
    await asyncio.sleep(3)

    # Start CheckinService
    out = await cmd('am startservice -n com.google.android.gms/.checkin.CheckinService', 'CHECKIN')
    print(f'  CheckinService: {(out or "").strip()[:150]}')

    # Login accounts changed broadcast
    await cmd('am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED', 'BCAST1')
    await cmd('am broadcast -a com.google.android.gms.INITIALIZE', 'BCAST2')
    print('  Checkin triggered')

    # ── Phase 8: Wait for checkin ─────────────────────────────────────
    print('\n▸ PHASE 8: WAIT FOR CHECKIN (120s)')
    checkin_ok = False
    for i in range(8):
        await asyncio.sleep(15)
        elapsed = (i + 1) * 15
        print(f'  [{elapsed}s] Checking...')

        # Check if CheckinService.xml appeared with android_id
        ck = await cmd('cat /data/data/com.google.android.gms/shared_prefs/CheckinService.xml 2>/dev/null | grep android_id')
        if 'android_id' in (ck or '') and 'value=""' not in (ck or '') and 'value="0"' not in (ck or ''):
            print(f'  CHECKIN SUCCESS at {elapsed}s!')
            print(f'  {(ck or "").strip()[:150]}')
            checkin_ok = True
            break

        # Check GSF databases
        gsf = await cmd('ls /data/data/com.google.android.gsf/databases/ 2>&1 | head -5')
        if 'gservices' in (gsf or ''):
            print(f'  GSF DB appeared at {elapsed}s!')
            checkin_ok = True
            break

    # ── Phase 9: Final Audit ──────────────────────────────────────────
    print('\n▸ PHASE 9: FINAL AUDIT')

    # Account visible
    acct = await cmd('dumpsys account 2>/dev/null | head -20', 'ACCT')
    acct_ok = EMAIL in (acct or '')
    print(f'  Account visible: {"PASS" if acct_ok else "FAIL"}')

    # Checkin state
    ck = await cmd('cat /data/data/com.google.android.gms/shared_prefs/CheckinService.xml 2>/dev/null')
    has_aid = 'android_id' in (ck or '') and 'value=""' not in (ck or '')
    print(f'  GMS checkin: {"PASS" if has_aid else "WAITING"}')

    # GSF state
    gsf = await cmd('ls /data/data/com.google.android.gsf/databases/ 2>&1')
    gsf_ok = 'gservices' in (gsf or '')
    print(f'  GSF registration: {"PASS" if gsf_ok else "WAITING"}')

    # Sign-in notification
    notif = await cmd('dumpsys notification 2>/dev/null | grep -iE "sign.in|google.account|add.*account" | head -5', timeout=60)
    has_notif = bool(notif and ('sign' in notif.lower() or 'google' in notif.lower() or 'account' in notif.lower()))
    print(f'  Sign-in notification: {"YES" if has_notif else "not detected yet"}')

    # Score
    score = sum([acct_ok, has_aid or checkin_ok, gsf_ok])
    elapsed_total = time.time() - t0

    print(f'\n{"="*65}')
    print(f'  RESULT — Score: {score}/3 | Elapsed: {elapsed_total:.0f}s')
    if acct_ok:
        print(f'  ✓ Account {EMAIL} is registered in AccountManager')
    if checkin_ok or has_aid:
        print(f'  ✓ GMS CheckinService completed')
    if has_notif:
        print(f'  ✓ "Sign in" notification appeared — tap to authenticate')
    else:
        print(f'  → Sign-in notification may appear shortly')
        print(f'  → Or open Settings > Accounts > Add account > Google')
    print(f'{"="*65}')


if __name__ == '__main__':
    asyncio.run(main())
