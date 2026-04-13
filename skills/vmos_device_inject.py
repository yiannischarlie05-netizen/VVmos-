#!/usr/bin/env python3
"""
VMOS Device Full Injection — APP5B54EI0Z1EOEA
Builds all databases locally, pushes via chunked base64, uses native VMOS APIs.
NO UI automation — pure filesystem injection only.
"""
import asyncio
import base64
import hashlib
import json
import logging
import os
import random
import secrets
import sqlite3
import sys
import tempfile
import time
from typing import Dict, List, Tuple

sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/core")

os.environ["VMOS_CLOUD_AK"] = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
os.environ["VMOS_CLOUD_SK"] = "Q2SgcSwEfuwoedY0cijp6Mce"

from vmos_cloud_api import VMOSCloudClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("inject")

PAD = "APP5B54EI0Z1EOEA"
EMAIL = "epolusamuel682@gmail.com"
DISPLAY_NAME = "Epolu Samuel"
GAIA_ID = str(random.randint(100000000000000000, 999999999999999999))
ANDROID_ID = "c8a554af4d6387"

client = VMOSCloudClient(
    ak=os.environ["VMOS_CLOUD_AK"],
    sk=os.environ["VMOS_CLOUD_SK"],
)

# ═══════════════════════════════════════════════════════════════════════════════
# SHELL + FILE PUSH HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def sh(cmd: str, timeout: int = 30) -> str:
    """Execute shell command on device."""
    try:
        r = await client.sync_cmd(PAD, cmd, timeout_sec=timeout)
        if r.get("code") == 200:
            d = r.get("data")
            if isinstance(d, list) and d:
                o = d[0].get("errorMsg", "")
                return str(o).strip() if o else ""
        return ""
    except Exception as e:
        return f"[ERR:{e}]"


async def push_bytes(data: bytes, target_path: str, owner: str = "system:system",
                     mode: str = "660") -> bool:
    """Push file bytes to device via chunked base64."""
    b64 = base64.b64encode(data).decode("ascii")
    staging = f"/data/local/tmp/_titan_{hashlib.md5(target_path.encode()).hexdigest()[:8]}"
    b64_path = f"{staging}.b64"

    # Clean
    await sh(f"rm -f {b64_path} {staging}")
    await asyncio.sleep(1)

    # Push in chunks (VMOS has ~4KB command limit)
    CHUNK = 3000
    chunks = [b64[i:i+CHUNK] for i in range(0, len(b64), CHUNK)]
    log.info(f"  Pushing {len(data)} bytes ({len(chunks)} chunks) → {target_path}")

    for i, chunk in enumerate(chunks):
        ok = await sh(f"echo -n '{chunk}' >> {b64_path}")
        if "[ERR" in str(ok):
            log.error(f"  Chunk {i+1} failed: {ok}")
            return False
        # Rate limit — VMOS needs spacing
        if i % 5 == 4:
            await asyncio.sleep(2)

    # Decode
    await sh(f"base64 -d {b64_path} > {staging} 2>/dev/null")
    await asyncio.sleep(1)

    # Verify size
    sz = await sh(f"wc -c < {staging}")
    try:
        actual = int(sz.strip())
        if actual != len(data):
            log.warning(f"  Size mismatch: expected {len(data)}, got {actual}")
    except:
        pass

    # Move to target
    target_dir = os.path.dirname(target_path)
    await sh(f"mkdir -p {target_dir}")
    await sh(f"cp {staging} {target_path}")
    await sh(f"chown {owner} {target_path}")
    await sh(f"chmod {mode} {target_path}")
    await sh(f"restorecon {target_path} 2>/dev/null")
    await sh(f"rm -f {b64_path} {staging}")

    log.info(f"  ✓ Pushed {target_path}")
    return True


async def push_xml(xml: str, target_path: str, package: str) -> bool:
    """Push SharedPreferences XML to device with correct ownership."""
    # Discover app UID
    uid = await sh(f"stat -c %U /data/data/{package} 2>/dev/null")
    uid = uid.strip() if uid and "[ERR" not in uid else "system"
    owner = f"{uid}:{uid}"
    return await push_bytes(xml.encode("utf-8"), target_path, owner=owner, mode="660")


def build_prefs_xml(data: Dict) -> str:
    """Build Android SharedPreferences XML."""
    lines = ["<?xml version='1.0' encoding='utf-8' standalone='yes' ?>", "<map>"]
    for key, value in data.items():
        if isinstance(value, bool):
            lines.append(f'    <boolean name="{key}" value="{str(value).lower()}" />')
        elif isinstance(value, int):
            lines.append(f'    <long name="{key}" value="{value}" />')
        else:
            v = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            lines.append(f'    <string name="{key}">{v}</string>')
    lines.append("</map>")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ACCOUNTS_CE.DB — Credential-encrypted account store
# ═══════════════════════════════════════════════════════════════════════════════

def build_accounts_ce_db() -> bytes:
    """Build accounts_ce.db with Google account + auth tokens."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    c = conn.cursor()

    # Exact Android 14+ CE schema (user_version=10)
    c.execute("CREATE TABLE IF NOT EXISTS android_metadata (locale TEXT)")
    c.execute("INSERT OR IGNORE INTO android_metadata VALUES ('en_US')")

    c.execute("""CREATE TABLE IF NOT EXISTS accounts (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, type TEXT NOT NULL, password TEXT,
        UNIQUE(name,type))""")

    c.execute("""CREATE TABLE IF NOT EXISTS authtokens (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        accounts_id INTEGER NOT NULL, type TEXT NOT NULL, authtoken TEXT,
        UNIQUE(accounts_id,type))""")

    c.execute("""CREATE TABLE IF NOT EXISTS extras (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        accounts_id INTEGER, key TEXT NOT NULL, value TEXT,
        UNIQUE(accounts_id,key))""")

    c.execute("""CREATE TABLE IF NOT EXISTS grants (
        accounts_id INTEGER NOT NULL, auth_token_type TEXT NOT NULL DEFAULT '',
        uid INTEGER NOT NULL, UNIQUE(accounts_id,auth_token_type,uid))""")

    c.execute("""CREATE TABLE IF NOT EXISTS shared_accounts (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, type TEXT NOT NULL, UNIQUE(name,type))""")

    c.execute("PRAGMA user_version = 10")

    # Insert account
    c.execute("INSERT INTO accounts (name, type, password) VALUES (?, 'com.google', '')", (EMAIL,))
    acct_id = c.lastrowid

    # Auth tokens — full scope matrix
    auth_token = f"ya29.{secrets.token_urlsafe(120)}"
    token_types = [
        ("com.google", auth_token),
        ("oauth2:https://www.googleapis.com/auth/plus.me", f"ya29.{secrets.token_urlsafe(80)}"),
        ("oauth2:https://www.googleapis.com/auth/userinfo.email", f"ya29.{secrets.token_urlsafe(80)}"),
        ("oauth2:https://www.googleapis.com/auth/userinfo.profile", f"ya29.{secrets.token_urlsafe(80)}"),
        ("oauth2:https://www.googleapis.com/auth/drive", f"ya29.{secrets.token_urlsafe(80)}"),
        ("oauth2:https://www.googleapis.com/auth/youtube", f"ya29.{secrets.token_urlsafe(80)}"),
        ("oauth2:https://www.googleapis.com/auth/calendar", f"ya29.{secrets.token_urlsafe(80)}"),
        ("oauth2:https://www.googleapis.com/auth/contacts", f"ya29.{secrets.token_urlsafe(80)}"),
        ("oauth2:https://www.googleapis.com/auth/gmail.readonly", f"ya29.{secrets.token_urlsafe(80)}"),
        ("SID", secrets.token_hex(60)),
        ("LSID", secrets.token_hex(60)),
        ("oauth2:https://www.googleapis.com/auth/android", f"ya29.{secrets.token_urlsafe(80)}"),
    ]
    for tt, tv in token_types:
        c.execute("INSERT INTO authtokens (accounts_id,type,authtoken) VALUES (?,?,?)", (acct_id, tt, tv))

    # Extras
    first = DISPLAY_NAME.split()[0] if DISPLAY_NAME else ""
    last = DISPLAY_NAME.split()[-1] if DISPLAY_NAME and len(DISPLAY_NAME.split()) > 1 else ""
    extras = [
        ("google.services.gaia", GAIA_ID),
        ("is_child_account", "false"),
        ("GoogleUserId", GAIA_ID),
        ("given_name", first),
        ("family_name", last),
        ("display_name", DISPLAY_NAME),
    ]
    for ek, ev in extras:
        c.execute("INSERT INTO extras (accounts_id,key,value) VALUES (?,?,?)", (acct_id, ek, ev))

    conn.commit()
    conn.close()
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ACCOUNTS_DE.DB — Device-encrypted account store
# ═══════════════════════════════════════════════════════════════════════════════

def build_accounts_de_db() -> bytes:
    """Build accounts_de.db."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS accounts (
        _id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL,
        previous_name TEXT, last_password_entry_time_millis_epoch INTEGER DEFAULT 0,
        UNIQUE(name,type))""")

    c.execute("""CREATE TABLE IF NOT EXISTS grants (
        accounts_id INTEGER NOT NULL, auth_token_type TEXT NOT NULL DEFAULT '',
        uid INTEGER NOT NULL, UNIQUE(accounts_id,auth_token_type,uid))""")

    c.execute("""CREATE TABLE IF NOT EXISTS visibility (
        accounts_id INTEGER NOT NULL, _package TEXT NOT NULL,
        value INTEGER, UNIQUE(accounts_id,_package))""")

    c.execute("""CREATE TABLE IF NOT EXISTS authtokens (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        accounts_id INTEGER NOT NULL, type TEXT NOT NULL DEFAULT '', authtoken TEXT,
        UNIQUE(accounts_id,type))""")

    c.execute("""CREATE TABLE IF NOT EXISTS extras (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        accounts_id INTEGER NOT NULL, key TEXT NOT NULL DEFAULT '', value TEXT,
        UNIQUE(accounts_id,key))""")

    c.execute("""CREATE TABLE IF NOT EXISTS shared_accounts (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, type TEXT NOT NULL, UNIQUE(name,type))""")

    c.execute("""CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY NOT NULL, value TEXT)""")

    c.execute("PRAGMA user_version = 3")

    c.execute("INSERT INTO accounts (name,type,last_password_entry_time_millis_epoch) VALUES (?,'com.google',?)",
              (EMAIL, int(time.time() * 1000)))

    conn.commit()
    conn.close()
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN INJECTION SEQUENCE
# ═══════════════════════════════════════════════════════════════════════════════

async def inject_all():
    start = time.time()
    log.info("=" * 70)
    log.info(f"VMOS FULL INJECTION — {PAD}")
    log.info(f"Email: {EMAIL} | Name: {DISPLAY_NAME}")
    log.info("=" * 70)

    # ─── PHASE 1: STOP GOOGLE APPS ───
    log.info("\n[PHASE 1] Stopping Google apps...")
    for pkg in ["com.google.android.gms", "com.android.vending", "com.android.chrome",
                "com.google.android.apps.walletnfcrel"]:
        await sh(f"am force-stop {pkg} 2>/dev/null")
    await asyncio.sleep(2)

    # ─── PHASE 2: INJECT ACCOUNTS_CE.DB ───
    log.info("\n[PHASE 2] Building + pushing accounts_ce.db...")
    ce_bytes = build_accounts_ce_db()
    log.info(f"  Built accounts_ce.db: {len(ce_bytes)} bytes")

    # Backup original
    await sh("cp /data/system_ce/0/accounts_ce.db /data/system_ce/0/accounts_ce.db.bak 2>/dev/null")
    ok = await push_bytes(ce_bytes, "/data/system_ce/0/accounts_ce.db",
                          owner="system:system", mode="600")
    # Remove WAL/SHM
    await sh("rm -f /data/system_ce/0/accounts_ce.db-wal /data/system_ce/0/accounts_ce.db-shm /data/system_ce/0/accounts_ce.db-journal")
    log.info(f"  accounts_ce.db: {'✓' if ok else '✗'}")

    # ─── PHASE 3: INJECT ACCOUNTS_DE.DB ───
    log.info("\n[PHASE 3] Building + pushing accounts_de.db...")
    de_bytes = build_accounts_de_db()
    await sh("cp /data/system_de/0/accounts_de.db /data/system_de/0/accounts_de.db.bak 2>/dev/null")
    ok2 = await push_bytes(de_bytes, "/data/system_de/0/accounts_de.db",
                           owner="system:system", mode="600")
    await sh("rm -f /data/system_de/0/accounts_de.db-wal /data/system_de/0/accounts_de.db-shm /data/system_de/0/accounts_de.db-journal")
    log.info(f"  accounts_de.db: {'✓' if ok2 else '✗'}")

    # ─── PHASE 4: GMS SHARED PREFS ───
    log.info("\n[PHASE 4] Injecting GMS shared preferences...")
    checkin_ts = str(int(time.time() * 1000))
    device_id = str(random.randint(10**15, 10**16 - 1))

    # CheckinService.xml
    checkin_xml = build_prefs_xml({
        "lastCheckin": checkin_ts,
        "deviceId": device_id,
        "digest": secrets.token_hex(20),
        "versionInfo": "15.0",
    })
    await push_xml(checkin_xml, "/data/data/com.google.android.gms/shared_prefs/CheckinService.xml",
                   "com.google.android.gms")

    # GservicesSettings.xml
    gservices_xml = build_prefs_xml({
        "android_id": ANDROID_ID,
        "checkin_device_id": device_id,
        "gms:version": "24.26.32",
    })
    await push_xml(gservices_xml, "/data/data/com.google.android.gms/shared_prefs/GservicesSettings.xml",
                   "com.google.android.gms")

    # GSF googlesettings.xml
    gsf_xml = build_prefs_xml({
        "android_id": ANDROID_ID,
        "checkin_device_id": device_id,
        "digest": secrets.token_hex(20),
    })
    await push_xml(gsf_xml, "/data/data/com.google.android.gsf/shared_prefs/googlesettings.xml",
                   "com.google.android.gsf")
    log.info("  ✓ GMS + GSF shared prefs injected")

    # ─── PHASE 5: PLAY STORE BINDING ───
    log.info("\n[PHASE 5] Binding Play Store account...")
    finsky_xml = build_prefs_xml({
        "setup_done": True,
        "setup_wizard_has_run": True,
        "account": EMAIL,
        "first_account_name": EMAIL,
        "tos_accepted": True,
        "auto_update_enabled": True,
        "content_filters": "0",
        "logged_in": True,
        "gls_logged_in": True,
    })
    await push_xml(finsky_xml, "/data/data/com.android.vending/shared_prefs/finsky.xml",
                   "com.android.vending")
    log.info("  ✓ Play Store bound to " + EMAIL)

    # ─── PHASE 6: CONTACTS via VMOS API ───
    log.info("\n[PHASE 6] Injecting contacts via VMOS API...")
    contacts = []
    names = [
        ("James", "Wilson"), ("Sarah", "Johnson"), ("Michael", "Davis"),
        ("Jennifer", "Martinez"), ("David", "Anderson"), ("Lisa", "Thomas"),
        ("Robert", "Taylor"), ("Karen", "Moore"), ("William", "Jackson"),
        ("Jessica", "White"), ("Chris", "Harris"), ("Ashley", "Martin"),
        ("Daniel", "Thompson"), ("Emily", "Garcia"), ("Matthew", "Brown"),
    ]
    for first, last in names:
        area = random.choice(["212", "310", "415", "305", "713", "312"])
        phone = f"+1{area}{random.randint(2000000, 9999999)}"
        contacts.append({"contactName": f"{first} {last}", "phone": phone})

    r = await client.update_contacts([PAD], contacts)
    log.info(f"  Contacts API: code={r.get('code')} ({len(contacts)} contacts)")

    # ─── PHASE 7: CALL LOGS via VMOS API ───
    log.info("\n[PHASE 7] Injecting call logs via VMOS API...")
    call_records = []
    now_ms = int(time.time() * 1000)
    for i in range(20):
        contact = random.choice(contacts)
        call_type = random.choice([1, 2, 3])  # 1=incoming, 2=outgoing, 3=missed
        duration = 0 if call_type == 3 else random.randint(10, 300)
        days_ago = random.randint(0, 90)
        ts = now_ms - (days_ago * 86400000) - random.randint(0, 86400000)
        call_records.append({
            "phone": contact["phone"],
            "name": contact["contactName"],
            "callType": call_type,
            "duration": duration,
            "date": ts,
        })

    r = await client.import_call_logs([PAD], call_records)
    log.info(f"  Call logs API: code={r.get('code')} ({len(call_records)} records)")

    # ─── PHASE 8: SMS via VMOS API ───
    log.info("\n[PHASE 8] Injecting SMS via VMOS API...")
    sms_templates = [
        "Hey, how are you?", "On my way!", "Thanks!", "See you soon",
        "Can you call me?", "Running late", "Sounds good!", "Miss you!",
        "Meeting at 3pm", "Got it, thanks", "Happy birthday!", "No problem",
    ]
    sms_count = 0
    for i in range(15):
        contact = random.choice(contacts)
        msg = random.choice(sms_templates)
        r = await client.simulate_sms(PAD, contact["phone"], msg)
        if r.get("code") == 200:
            sms_count += 1
        await asyncio.sleep(1)  # Rate limit
    log.info(f"  SMS injected: {sms_count}/15")

    # ─── PHASE 9: GALLERY via VMOS API ───
    log.info("\n[PHASE 9] Injecting gallery photos...")
    # Create DCIM directory and placeholder images with timestamps
    await sh("mkdir -p /sdcard/DCIM/Camera")
    photo_count = 0
    for i in range(10):
        days_ago = random.randint(1, 60)
        dt_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time() - days_ago * 86400))
        touch_str = time.strftime("%Y%m%d%H%M.%S", time.localtime(time.time() - days_ago * 86400))
        fname = f"IMG_{dt_str}.jpg"

        # Create a minimal valid JPEG (1x1 white pixel)
        r = await sh(
            f"echo '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////2wBDAf//////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AKwA=' | base64 -d > /sdcard/DCIM/Camera/{fname} 2>/dev/null && touch -t {touch_str} /sdcard/DCIM/Camera/{fname} && echo OK"
        )
        if "OK" in str(r):
            photo_count += 1

    # Trigger media scan
    await sh("am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/DCIM/Camera/ 2>/dev/null")
    log.info(f"  Gallery photos: {photo_count}/10")

    # ─── PHASE 10: CHROME HISTORY + SIGN-IN ───
    log.info("\n[PHASE 10] Injecting Chrome sign-in + history...")
    # Chrome Preferences JSON
    chrome_prefs = {
        "account_info": [{
            "account_id": GAIA_ID,
            "email": EMAIL,
            "full_name": DISPLAY_NAME,
            "given_name": DISPLAY_NAME.split()[0],
            "gaia": GAIA_ID,
            "locale": "en",
            "is_child_account": False,
        }],
        "signin": {"allowed": True, "allowed_on_next_startup": True},
        "google": {"services": {"signin": {"allowed": True}}},
        "sync": {"has_setup_completed": True, "requested": True},
        "profile": {"name": DISPLAY_NAME},
    }
    prefs_dir = "/data/data/com.android.chrome/app_chrome/Default"
    await sh(f"mkdir -p {prefs_dir}")
    prefs_bytes = json.dumps(chrome_prefs, indent=2).encode("utf-8")
    uid = await sh("stat -c %U /data/data/com.android.chrome 2>/dev/null")
    uid = uid.strip() if uid and "[ERR" not in uid else "system"
    await push_bytes(prefs_bytes, f"{prefs_dir}/Preferences", owner=f"{uid}:{uid}", mode="660")
    log.info("  ✓ Chrome sign-in state injected")

    # ─── PHASE 11: RESTART SYSTEM TO PICK UP ACCOUNT ───
    log.info("\n[PHASE 11] Restarting account manager to detect injected account...")
    # Kill system services that cache account state
    await sh("am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null")
    await sh("am broadcast -a android.accounts.AccountManager.LOGIN_ACCOUNTS_CHANGED_ACTION 2>/dev/null")
    # Force GMS to re-read account databases
    await sh("am force-stop com.google.android.gms")
    await sh("am force-stop com.android.vending")
    await asyncio.sleep(2)

    # ─── PHASE 12: VERIFY ───
    log.info("\n[PHASE 12] Verifying injection...")
    # Check account shows up
    acct_check = await sh("dumpsys account 2>/dev/null | head -10")
    log.info(f"  Account service: {acct_check[:200]}")

    # Check contacts count
    contact_check = await sh("content query --uri content://com.android.contacts/contacts --projection _id 2>/dev/null | wc -l")
    log.info(f"  Contacts count: {contact_check}")

    # Check DCIM
    photo_check = await sh("ls /sdcard/DCIM/Camera/ 2>/dev/null | wc -l")
    log.info(f"  Photos count: {photo_check}")

    elapsed = time.time() - start
    log.info(f"\n{'=' * 70}")
    log.info(f"INJECTION COMPLETE in {elapsed:.1f}s")
    log.info(f"  Account: {EMAIL}")
    log.info(f"  Contacts: {len(contacts)}")
    log.info(f"  Call logs: {len(call_records)}")
    log.info(f"  SMS: {sms_count}")
    log.info(f"  Photos: {photo_count}")
    log.info(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(inject_all())
