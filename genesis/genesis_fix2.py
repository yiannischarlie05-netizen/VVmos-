#!/usr/bin/env python3
"""
Genesis Ultra v3.5 — Fix #2: No-Password Checkin
==================================================
Root cause: GMS reads stored password → sends to Google → BadAuthentication
→ Entire checkin pipeline stalls → device never registers → Play Store broken

Fix: Push account WITHOUT password and WITHOUT tokens.
- GMS CheckinService registers device using CTS fingerprint (no auth needed)
- Account appears in AccountManager (signed in state)
- GMS will show "Sign in to your Google Account" notification
  → User taps notification → proper WebView sign-in → real tokens obtained
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

# Setup
_env = Path(__file__).parent / ".env"
if _env.exists():
    for ln in _env.read_text().splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(Path(__file__).parent / "vmos_titan" / "core"))
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "server"))

PAD = "APP5B54EI0Z1EOEA"
EMAIL = "epolusamuel682@gmail.com"
PASSWORD = "gA3EFqhAQJOBZ"
DELAY = 3.5
CHUNK = 2048


# ── VMOS Cmd ──────────────────────────────────────────────────────────────────

class V:
    def __init__(self):
        from vmos_cloud_api import VMOSCloudClient
        self.c = VMOSCloudClient()
        self._t = 0.0
        self.n = 0

    async def sh(self, cmd, label="", timeout=30):
        elapsed = time.time() - self._t
        if elapsed < DELAY:
            await asyncio.sleep(DELAY - elapsed)
        self._t = time.time()
        self.n += 1
        for attempt in range(3):
            try:
                r = await self.c.sync_cmd(PAD, cmd, timeout_sec=timeout)
                if not isinstance(r, dict):
                    await asyncio.sleep(5)
                    continue
                code = r.get("code")
                if code == 200:
                    data = r.get("data")
                    if data is None:
                        return ""
                    if isinstance(data, list) and data:
                        raw = data[0].get("errorMsg") if isinstance(data[0], dict) else None
                        out = raw if raw is not None else ""
                        if label and out.strip():
                            print(f"  [{label}] {out.strip()[:200]}")
                        return out
                    return ""
                if code == 110012:
                    print(f"  [{label}] timeout (attempt {attempt+1}/3)")
                    await asyncio.sleep(8)
                    continue
                return ""
            except Exception as e:
                print(f"  [{label}] error: {e}")
                await asyncio.sleep(5)
        return ""

    async def push(self, data, target, owner="system:system", mode="660"):
        b64 = base64.b64encode(data).decode()
        h = hashlib.md5(target.encode()).hexdigest()[:8]
        stg = f"/sdcard/.fx2_{h}"
        b64f = f"{stg}.b64"
        name = target.split("/")[-1]
        chunks = [b64[i:i+CHUNK] for i in range(0, len(b64), CHUNK)]
        print(f"  Pushing {len(data)} bytes → {name} ({len(chunks)} chunks)")

        await self.sh(f"rm -f {b64f} {stg}")
        for i, ch in enumerate(chunks):
            safe = ch.replace("'", "'\\''")
            await self.sh(f"echo -n '{safe}' >> {b64f}")
            if (i+1) % 15 == 0:
                print(f"    chunk {i+1}/{len(chunks)}")

        await self.sh(f"base64 -d {b64f} > {stg}")
        sz = await self.sh(f"wc -c < {stg}")
        try:
            actual = int(sz.strip())
            if actual != len(data):
                print(f"    SIZE MISMATCH: {actual} vs {len(data)}")
                return False
        except (ValueError, AttributeError):
            pass

        d = os.path.dirname(target)
        await self.sh(f"mkdir -p {d}")
        await self.sh(f"cp {stg} {target}")
        await self.sh(f"chown {owner} {target}")
        await self.sh(f"chmod {mode} {target}")
        await self.sh(f"restorecon {target}")
        await self.sh(f"rm -f {b64f} {stg}")
        v = await self.sh(f"ls -la {target}")
        ok = name in v
        print(f"    → {'OK' if ok else 'FAIL'}")
        return ok


# ── DB Builders ───────────────────────────────────────────────────────────────

def build_ce(email, password=None):
    """accounts_ce.db — password=None means GMS does anonymous checkin."""
    gaia = str(random.randint(10**17, 10**18 - 1))
    disp = email.split("@")[0].replace(".", " ").title()
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
            c.execute("INSERT INTO extras (accounts_id, key, value) VALUES (?,?,?)", (aid, k, v))

        c.execute("INSERT INTO shared_accounts (name, type) VALUES (?, 'com.google')", (email,))
        for uid in (1000, 10036, 10042, 10000, 10001):
            c.execute("INSERT OR IGNORE INTO grants (accounts_id, auth_token_type, uid) VALUES (?,'',?)", (aid, uid))
            for tt in ("com.google", "SID", "LSID"):
                c.execute("INSERT OR IGNORE INTO grants (accounts_id, auth_token_type, uid) VALUES (?,?,?)", (aid, tt, uid))

        conn.commit()
        conn.close()
        return Path(p).read_bytes()
    finally:
        Path(p).unlink(missing_ok=True)


def build_de(email):
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
        for pkg in ("com.google.android.gms", "com.android.vending",
                     "com.google.android.gsf", "com.android.chrome",
                     "com.google.android.youtube", "com.google.android.gm",
                     "com.google.android.apps.walletnfcrel",
                     "com.google.android.googlequicksearchbox"):
            c.execute("INSERT INTO visibility VALUES (1,?,1)", (pkg,))
        conn.commit()
        conn.close()
        return Path(p).read_bytes()
    finally:
        Path(p).unlink(missing_ok=True)


# ── Main Pipeline ─────────────────────────────────────────────────────────────

async def main():
    v = V()
    t0 = time.time()

    print("=" * 65)
    print("  GENESIS ULTRA v3.5 — FIX #2")
    print(f"  Target: {PAD}")
    print(f"  Account: {EMAIL}")
    print("  Strategy: No-password + GSF Cold Checkin")
    print("=" * 65)

    # ── Phase 1: Verify ──────────────────────────────────────────────
    print("\n▸ PHASE 1: VERIFY DEVICE")
    root = await v.sh("id -u", "ROOT")
    if "0" not in root:
        print("  FAIL: not root")
        return False
    print("  Root confirmed")

    fp = await v.sh("getprop ro.build.fingerprint", "FP")
    print(f"  Fingerprint: {fp.strip()}")

    # ── Phase 2: Try gpsoauth (one more attempt with password) ───────
    print("\n▸ PHASE 2: gpsoauth ATTEMPT")
    real_tokens = None
    try:
        import gpsoauth
        aid = await v.sh("settings get secure android_id")
        aid = aid.strip() or "c8a554af4d6387"
        print(f"  Trying gpsoauth with android_id={aid}...")

        master = gpsoauth.perform_master_login(
            email=EMAIL, password=PASSWORD,
            android_id=aid, service="ac2dm",
            device_country="us", operator_country="us",
            lang="en_US", sdk_version=34,
            client_sig="38918a453d07199354f8b19af05ec6562ced5788",
        )
        if "Token" in master:
            mt = master["Token"]
            print(f"  Master token acquired!")
            real_tokens = {"com.google": mt}
            for scope in [
                "oauth2:https://www.googleapis.com/auth/plus.me",
                "oauth2:https://www.googleapis.com/auth/userinfo.email",
                "oauth2:https://www.googleapis.com/auth/userinfo.profile",
                "oauth2:https://www.googleapis.com/auth/android",
                "oauth2:https://www.googleapis.com/auth/drive",
                "oauth2:https://www.googleapis.com/auth/youtube",
            ]:
                try:
                    r = gpsoauth.perform_oauth(
                        email=EMAIL, master_token=mt, android_id=aid,
                        service=scope, app="com.google.android.gms",
                        client_sig="38918a453d07199354f8b19af05ec6562ced5788",
                    )
                    if "Auth" in r:
                        real_tokens[scope] = r["Auth"]
                except Exception:
                    pass
            print(f"  Got {len(real_tokens)} real tokens!")
        else:
            err = master.get("Error", "Unknown")
            print(f"  gpsoauth failed: {err}")
            if err == "BadAuthentication":
                print("  → Password rejected by Google servers")
                print("  → If 2FA enabled, create App Password at:")
                print("    https://myaccount.google.com/apppasswords")
    except ImportError:
        print("  gpsoauth not installed")
    except Exception as e:
        print(f"  gpsoauth error: {e}")

    # ── Phase 3: Build databases ─────────────────────────────────────
    print("\n▸ PHASE 3: BUILD DATABASES")
    if real_tokens:
        # Build with real tokens, no password needed
        print("  Using REAL tokens (no password stored)")
        ce = build_ce(EMAIL, password=None)
        # Need to add tokens separately
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            tp = f.name
        Path(tp).write_bytes(ce)
        conn = sqlite3.connect(tp)
        c = conn.cursor()
        for scope, tok in real_tokens.items():
            c.execute("INSERT OR REPLACE INTO authtokens (accounts_id, type, authtoken) VALUES (1,?,?)",
                      (scope, tok))
        conn.commit()
        conn.close()
        ce = Path(tp).read_bytes()
        Path(tp).unlink(missing_ok=True)
        print(f"  accounts_ce.db: {len(ce)} bytes (REAL tokens: {len(real_tokens)})")
    else:
        # Build WITHOUT password — forces anonymous checkin
        # GMS will show sign-in notification
        print("  Using NO password, NO tokens (anonymous checkin)")
        ce = build_ce(EMAIL, password=None)
        print(f"  accounts_ce.db: {len(ce)} bytes (no auth data)")

    de = build_de(EMAIL)
    print(f"  accounts_de.db: {len(de)} bytes")

    # ── Phase 4: Stop + Clean ────────────────────────────────────────
    print("\n▸ PHASE 4: STOP GOOGLE APPS + CLEAN STATE")
    for pkg in ["com.android.vending", "com.google.android.gms",
                "com.google.android.gsf", "com.google.android.gm",
                "com.google.android.youtube"]:
        await v.sh(f"am force-stop {pkg}")
    print("  All Google apps stopped")

    # Remove old DBs
    print("  Removing old databases...")
    await v.sh("rm -f /data/system_ce/0/accounts_ce.db*")
    await v.sh("rm -f /data/system_de/0/accounts_de.db*")

    # Nuke ALL cached auth/checkin/gsf state
    print("  Nuking cached GSF/GMS state (GSF Cold Checkin)...")
    await v.sh("rm -rf /data/data/com.google.android.gsf/databases/*")
    await v.sh("rm -rf /data/data/com.google.android.gsf/shared_prefs/*")
    await v.sh("rm -f /data/data/com.google.android.gms/shared_prefs/CheckinService.xml")
    await v.sh("rm -f /data/data/com.google.android.gms/shared_prefs/CheckinAccount.xml")
    await v.sh("rm -f /data/data/com.google.android.gms/shared_prefs/GservicesSettings.xml")
    await v.sh("rm -rf /data/data/com.google.android.gms/databases/auth*.db*")
    await v.sh("rm -rf /data/data/com.android.vending/cache/*")
    await v.sh("rm -rf /data/data/com.google.android.gms/cache/*")
    print("  All cached state cleared")

    # ── Phase 5: Push databases ──────────────────────────────────────
    print("\n▸ PHASE 5: PUSH DATABASES")
    ce_ok = await v.push(ce, "/data/system_ce/0/accounts_ce.db", "1000:1000", "600")
    de_ok = await v.push(de, "/data/system_de/0/accounts_de.db", "1000:1000", "600")

    if not ce_ok:
        print("  CRITICAL: accounts_ce.db push failed!")
        return False

    # ── Phase 6: Push minimal SharedPrefs ────────────────────────────
    print("\n▸ PHASE 6: PUSH SharedPrefs")

    # CheckinAccount (just account binding, no auth data)
    ca = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="account_name">{EMAIL}</string>
    <string name="account_type">com.google</string>
    <boolean name="registered" value="true" />
</map>
"""
    await v.push(ca.encode(), "/data/data/com.google.android.gms/shared_prefs/CheckinAccount.xml",
                 "10036:10036", "660")

    # finsky (Play Store signed-in state)
    fi = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
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
    await v.push(fi.encode(), "/data/data/com.android.vending/shared_prefs/finsky.xml",
                 "10042:10042", "660")

    # ── Phase 7: Trigger GMS Cold Checkin ────────────────────────────
    print("\n▸ PHASE 7: TRIGGER GMS COLD CHECKIN")

    await v.sh("am force-stop com.google.android.gms")
    await v.sh("am force-stop com.google.android.gsf")
    await asyncio.sleep(3)

    # Start CheckinService
    r = await v.sh("am startservice -n com.google.android.gms/.checkin.CheckinService", "CHECKIN")

    # Broadcasts
    await v.sh("am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED", "BCAST")
    await v.sh("am broadcast -a com.google.android.gms.INITIALIZE", "INIT")
    print("  Checkin triggered")

    # ── Phase 8: Wait + Monitor ──────────────────────────────────────
    print("\n▸ PHASE 8: WAIT FOR CHECKIN (90s)")
    checkin_ok = False
    for i in range(6):
        await asyncio.sleep(15)
        elapsed = (i + 1) * 15
        print(f"  [{elapsed}s] Checking...")

        # Check if CheckinService.xml has android_id
        ck = await v.sh("cat /data/data/com.google.android.gms/shared_prefs/CheckinService.xml 2>/dev/null | grep android_id")
        if "android_id" in ck and 'value=""' not in ck and 'value="0"' not in ck:
            print(f"  CHECKIN SUCCESS at {elapsed}s!")
            print(f"  {ck.strip()[:120]}")
            checkin_ok = True
            break

        # Check GSF databases
        gsf = await v.sh("ls /data/data/com.google.android.gsf/databases/ 2>&1 | head -5")
        if "gservices" in gsf:
            print(f"  GSF DB appeared at {elapsed}s!")
            checkin_ok = True
            break

        # Check logcat for clues
        if elapsed == 30:
            log = await v.sh("logcat -d -t 100 2>/dev/null | grep -iE 'checkin|BadAuth|credential' | tail -5", timeout=60)
            if log.strip():
                for line in log.strip().split("\n")[:3]:
                    print(f"    LOG: {line.strip()[:120]}")

    # ── Phase 9: Final Audit ─────────────────────────────────────────
    print("\n▸ PHASE 9: FINAL AUDIT")

    # Account visible
    acct = await v.sh("dumpsys account 2>/dev/null | head -15", "ACCT")
    acct_ok = EMAIL in acct
    print(f"  Account visible: {'PASS' if acct_ok else 'FAIL'}")

    # Checkin
    ck = await v.sh("cat /data/data/com.google.android.gms/shared_prefs/CheckinService.xml 2>/dev/null")
    has_aid = "android_id" in ck and 'value=""' not in ck and 'value="0"' not in ck
    has_time = "lastCheckinSuccessTime" in ck and 'value="0"' not in ck
    print(f"  GMS android_id: {'PASS' if has_aid else 'FAIL'}")
    print(f"  GMS checkin time: {'PASS' if has_time else 'FAIL'}")

    # GSF
    gsf = await v.sh("ls /data/data/com.google.android.gsf/databases/ 2>&1")
    gsf_ok = "gservices" in gsf
    print(f"  GSF registration: {'PASS' if gsf_ok else 'FAIL'}")

    # Auth errors
    auth = await v.sh("logcat -d -t 300 2>/dev/null | grep -c BadAuthentication", timeout=60)
    try:
        bad_count = int(auth.strip())
    except (ValueError, AttributeError):
        bad_count = -1
    print(f"  BadAuth errors: {bad_count}")

    # Check for sign-in notification
    notif = await v.sh("dumpsys notification 2>/dev/null | grep -iE 'sign.in|google.account' | head -3", timeout=60)
    has_notif = "sign" in notif.lower() or "google" in notif.lower()
    print(f"  Sign-in notification: {'YES' if has_notif else 'not detected'}")

    # Launch Play Store
    await v.sh("am start -n com.android.vending/com.android.vending.AssetBrowserActivity", "PLAY")

    # Score
    score = sum([acct_ok, has_aid or checkin_ok, gsf_ok, bad_count == 0])
    elapsed_total = time.time() - t0

    print(f"\n{'='*65}")
    print(f"  RESULTS — Score: {score}/4 | Elapsed: {elapsed_total:.0f}s | API calls: {v.n}")
    print(f"  Auth: {'REAL TOKENS' if real_tokens else 'NO-PASSWORD (anonymous)'}")
    print(f"  Account: {'PASS' if acct_ok else 'FAIL'}")
    print(f"  Checkin: {'PASS' if (has_aid or checkin_ok) else 'FAIL'}")
    print(f"  GSF: {'PASS' if gsf_ok else 'FAIL'}")
    print(f"  No Bad Auth: {'PASS' if bad_count == 0 else f'FAIL ({bad_count} errors)'}")

    if score >= 3:
        print("\n  STATUS: OPERATIONAL READY")
        print("  Play Store should work. Try downloading an app.")
    elif score >= 2:
        print("\n  STATUS: PARTIAL — may need more time or UI sign-in")
        if has_notif:
            print("  → A 'Sign in' notification appeared!")
            print("  → Tap it via VMOS Cloud console to complete sign-in")
        else:
            print("  → Wait 2-3 minutes for GMS to complete processing")
            print("  → Or try: Settings → Accounts → Google → sign in")
    else:
        print("\n  STATUS: NEEDS MANUAL SIGN-IN")
        print("  → Open Settings → Accounts → Add Account → Google")
        print("  → Or create App Password: https://myaccount.google.com/apppasswords")
        print("  → Re-run with App Password for automated injection")

    print(f"{'='*65}")
    return score >= 2


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
