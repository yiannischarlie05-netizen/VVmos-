#!/usr/bin/env python3
"""
VMOS Injection Phase 2 — Contacts, Calls, SMS, Gallery, Chrome History
Uses local SQLite builds + chunked base64 push (same as profile_injector.py).
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
import struct
import sys
import tempfile
import time

sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/core")
os.environ["VMOS_CLOUD_AK"] = "YOUR_VMOS_AK_HERE"
os.environ["VMOS_CLOUD_SK"] = "YOUR_VMOS_SK_HERE"
from vmos_cloud_api import VMOSCloudClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("inject2")

PAD = "APP5B54EI0Z1EOEA"
EMAIL = "epolusamuel682@gmail.com"
DISPLAY_NAME = "Epolu Samuel"
client = VMOSCloudClient(ak=os.environ["VMOS_CLOUD_AK"], sk=os.environ["VMOS_CLOUD_SK"])


async def sh(cmd, timeout=30):
    try:
        r = await client.sync_cmd(PAD, cmd, timeout_sec=timeout)
        if r.get("code") == 200:
            d = r.get("data")
            if isinstance(d, list) and d:
                return str(d[0].get("errorMsg", "")).strip()
        return ""
    except:
        return ""


async def push_bytes(data, target_path, owner="system:system", mode="660"):
    b64 = base64.b64encode(data).decode("ascii")
    staging = f"/data/local/tmp/_t_{hashlib.md5(target_path.encode()).hexdigest()[:8]}"
    b64_path = f"{staging}.b64"
    await sh(f"rm -f {b64_path} {staging}")
    await asyncio.sleep(0.5)

    CHUNK = 3000
    chunks = [b64[i:i+CHUNK] for i in range(0, len(b64), CHUNK)]
    log.info(f"  Pushing {len(data)}B ({len(chunks)} chunks) → {target_path}")

    for i, chunk in enumerate(chunks):
        await sh(f"echo -n '{chunk}' >> {b64_path}")
        if i % 5 == 4:
            await asyncio.sleep(1.5)

    await sh(f"base64 -d {b64_path} > {staging} 2>/dev/null")
    await asyncio.sleep(0.5)

    target_dir = os.path.dirname(target_path)
    await sh(f"mkdir -p {target_dir}")
    await sh(f"cp {staging} {target_path}")
    await sh(f"chown {owner} {target_path}")
    await sh(f"chmod {mode} {target_path}")
    await sh(f"restorecon {target_path} 2>/dev/null")
    await sh(f"rm -f {b64_path} {staging}")
    log.info(f"  ✓ {target_path}")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# CONTACTS — Build contacts2.db locally then push
# ═══════════════════════════════════════════════════════════════════════════════

CONTACT_NAMES = [
    ("James", "Wilson"), ("Sarah", "Johnson"), ("Michael", "Davis"),
    ("Jennifer", "Martinez"), ("David", "Anderson"), ("Lisa", "Thomas"),
    ("Robert", "Taylor"), ("Karen", "Moore"), ("William", "Jackson"),
    ("Jessica", "White"), ("Chris", "Harris"), ("Ashley", "Martin"),
    ("Daniel", "Thompson"), ("Emily", "Garcia"), ("Matthew", "Brown"),
]

def build_contacts_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS raw_contacts (
            _id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER, account_type TEXT, account_name TEXT,
            version INTEGER DEFAULT 1, dirty INTEGER DEFAULT 0,
            deleted INTEGER DEFAULT 0, display_name TEXT,
            display_name_alt TEXT, display_name_source INTEGER DEFAULT 40,
            sort_key TEXT, sort_key_alt TEXT,
            times_contacted INTEGER DEFAULT 0, last_time_contacted INTEGER DEFAULT 0,
            starred INTEGER DEFAULT 0, pinned INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS mimetypes (
            _id INTEGER PRIMARY KEY AUTOINCREMENT,
            mimetype TEXT UNIQUE);
        INSERT OR IGNORE INTO mimetypes(mimetype) VALUES('vnd.android.cursor.item/name');
        INSERT OR IGNORE INTO mimetypes(mimetype) VALUES('vnd.android.cursor.item/phone_v2');
        INSERT OR IGNORE INTO mimetypes(mimetype) VALUES('vnd.android.cursor.item/email_v2');
        CREATE TABLE IF NOT EXISTS data (
            _id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_contact_id INTEGER, mimetype_id INTEGER,
            is_primary INTEGER DEFAULT 0, is_super_primary INTEGER DEFAULT 0,
            data1 TEXT, data2 TEXT, data3 TEXT, data4 TEXT,
            data5 TEXT, data6 TEXT, data7 TEXT, data8 TEXT,
            data9 TEXT, data10 TEXT, data11 TEXT, data12 TEXT,
            data13 TEXT, data14 TEXT, data15 TEXT);
        CREATE TABLE IF NOT EXISTS android_metadata (locale TEXT);
        INSERT OR IGNORE INTO android_metadata VALUES ('en_US');
    """)

    c.execute("SELECT _id, mimetype FROM mimetypes")
    mime_map = {row[1]: row[0] for row in c.fetchall()}
    name_mid = mime_map.get('vnd.android.cursor.item/name')
    phone_mid = mime_map.get('vnd.android.cursor.item/phone_v2')
    email_mid = mime_map.get('vnd.android.cursor.item/email_v2')

    for i, (first, last) in enumerate(CONTACT_NAMES):
        full_name = f"{first} {last}"
        area = random.choice(["212", "310", "415", "305", "713", "312", "404", "206"])
        phone = f"+1{area}{random.randint(2000000, 9999999)}"
        email_addr = f"{first.lower()}.{last.lower()}@gmail.com"

        rc_id = i + 1
        c.execute("INSERT INTO raw_contacts(_id, display_name, display_name_alt, sort_key, sort_key_alt, times_contacted, last_time_contacted) VALUES (?,?,?,?,?,?,?)",
                  (rc_id, full_name, f"{last}, {first}", last.upper(), first.upper(),
                   random.randint(0, 20), int(time.time()*1000) - random.randint(0, 90*86400000)))

        if name_mid:
            c.execute("INSERT INTO data(raw_contact_id,mimetype_id,data1,data2,data3) VALUES(?,?,?,?,?)",
                      (rc_id, name_mid, full_name, first, last))
        if phone_mid:
            c.execute("INSERT INTO data(raw_contact_id,mimetype_id,data1,data2) VALUES(?,?,?,?)",
                      (rc_id, phone_mid, phone, "2"))
        if email_mid:
            c.execute("INSERT INTO data(raw_contact_id,mimetype_id,data1,data2) VALUES(?,?,?,?)",
                      (rc_id, email_mid, email_addr, "1"))

    conn.commit()
    conn.close()
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data, [f"{first} {last}" for first, last in CONTACT_NAMES]


# ═══════════════════════════════════════════════════════════════════════════════
# CALL LOGS — Build calllog.db
# ═══════════════════════════════════════════════════════════════════════════════

def build_calllog_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS calls (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT, type INTEGER DEFAULT 1,
        date INTEGER, duration INTEGER DEFAULT 0,
        new INTEGER DEFAULT 0, name TEXT DEFAULT '',
        numbertype INTEGER DEFAULT 0, numberlabel TEXT DEFAULT '',
        countryiso TEXT DEFAULT 'US', geocoded_location TEXT DEFAULT '',
        phone_account_component_name TEXT DEFAULT '',
        phone_account_id TEXT DEFAULT '')""")

    now_ms = int(time.time() * 1000)
    count = 0
    for i in range(25):
        name_pair = random.choice(CONTACT_NAMES)
        name = f"{name_pair[0]} {name_pair[1]}"
        area = random.choice(["212", "310", "415", "305", "713"])
        number = f"+1{area}{random.randint(2000000, 9999999)}"
        call_type = random.choice([1, 1, 2, 2, 3])  # in, in, out, out, missed
        duration = 0 if call_type == 3 else random.randint(15, 600)
        days_ago = random.randint(0, 90)
        date = now_ms - (days_ago * 86400000) - random.randint(0, 86400000)
        c.execute("INSERT INTO calls(number,type,date,duration,new,name,countryiso) VALUES(?,?,?,?,0,?,?)",
                  (number, call_type, date, duration, name, "US"))
        count += 1

    conn.commit()
    conn.close()
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data, count


# ═══════════════════════════════════════════════════════════════════════════════
# SMS — Build mmssms.db
# ═══════════════════════════════════════════════════════════════════════════════

SMS_TEMPLATES = [
    "Hey, how are you?", "On my way!", "Thanks!", "See you soon",
    "Can you call me?", "Running late", "Sounds good!", "Miss you!",
    "Meeting at 3pm", "Got it, thanks", "Happy birthday!", "No problem",
    "What time works?", "Just got home", "See you tomorrow!",
    "Dinner tonight?", "Good morning!", "Let me know", "Okay, will do",
    "Be there in 10", "Sorry, missed your call", "Talk later?",
]

def build_sms_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS sms (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT, body TEXT, type INTEGER DEFAULT 1,
        date INTEGER, read INTEGER DEFAULT 1,
        seen INTEGER DEFAULT 1, thread_id INTEGER DEFAULT 1)""")

    now_ms = int(time.time() * 1000)
    count = 0
    for i in range(30):
        area = random.choice(["212", "310", "415", "305", "713"])
        address = f"+1{area}{random.randint(2000000, 9999999)}"
        body = random.choice(SMS_TEMPLATES)
        msg_type = random.choice([1, 1, 2])  # 1=received, 2=sent
        days_ago = random.randint(0, 60)
        date = now_ms - (days_ago * 86400000) - random.randint(0, 86400000)
        thread_id = (i % 8) + 1
        c.execute("INSERT INTO sms(address,body,type,date,read,seen,thread_id) VALUES(?,?,?,?,1,1,?)",
                  (address, body, msg_type, date, thread_id))
        count += 1

    conn.commit()
    conn.close()
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data, count


# ═══════════════════════════════════════════════════════════════════════════════
# CHROME HISTORY — Build History db
# ═══════════════════════════════════════════════════════════════════════════════

HISTORY_URLS = [
    ("https://www.google.com/search?q=weather+today", "weather today - Google Search"),
    ("https://www.amazon.com/", "Amazon.com: Online Shopping"),
    ("https://www.youtube.com/", "YouTube"),
    ("https://mail.google.com/mail/", "Gmail - Inbox"),
    ("https://www.reddit.com/", "Reddit - Pair programming"),
    ("https://www.netflix.com/browse", "Netflix"),
    ("https://maps.google.com/", "Google Maps"),
    ("https://news.google.com/", "Google News"),
    ("https://www.instagram.com/", "Instagram"),
    ("https://www.twitter.com/", "X (formerly Twitter)"),
    ("https://www.facebook.com/", "Facebook"),
    ("https://www.linkedin.com/feed/", "LinkedIn Feed"),
    ("https://www.walmart.com/", "Walmart.com"),
    ("https://www.target.com/", "Target: Expect More. Pay Less."),
    ("https://www.espn.com/", "ESPN - Scores, Stats"),
    ("https://www.cnn.com/", "CNN - Breaking News"),
    ("https://stackoverflow.com/", "Stack Overflow"),
    ("https://github.com/", "GitHub"),
    ("https://docs.google.com/", "Google Docs"),
    ("https://drive.google.com/", "Google Drive"),
]

def build_chrome_history_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY, url TEXT NOT NULL,
        title TEXT NOT NULL DEFAULT '', visit_count INTEGER NOT NULL DEFAULT 1,
        typed_count INTEGER NOT NULL DEFAULT 0,
        last_visit_time INTEGER NOT NULL DEFAULT 0,
        hidden INTEGER NOT NULL DEFAULT 0)""")

    c.execute("""CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY, url INTEGER NOT NULL,
        visit_time INTEGER NOT NULL, from_visit INTEGER NOT NULL DEFAULT 0,
        transition INTEGER NOT NULL DEFAULT 0,
        segment_id INTEGER NOT NULL DEFAULT 0,
        visit_duration INTEGER NOT NULL DEFAULT 0)""")

    chrome_epoch_offset = 11644473600000000
    now_chrome = int(time.time() * 1000000) + chrome_epoch_offset
    count = 0

    for url, title in HISTORY_URLS:
        visits = random.randint(1, 12)
        last_visit = now_chrome - random.randint(0, 30 * 86400 * 1000000)
        c.execute("INSERT INTO urls(url,title,visit_count,last_visit_time) VALUES(?,?,?,?)",
                  (url, title, visits, last_visit))
        url_id = c.lastrowid
        for v in range(visits):
            vt = last_visit - random.randint(0, 60 * 86400 * 1000000)
            dur = random.randint(5000000, 300000000)
            c.execute("INSERT INTO visits(url,visit_time,transition,visit_duration) VALUES(?,?,0,?)",
                      (url_id, vt, dur))
        count += 1

    conn.commit()
    conn.close()
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data, count


# ═══════════════════════════════════════════════════════════════════════════════
# GALLERY — Build EXIF JPEGs (from profile_injector.py)
# ═══════════════════════════════════════════════════════════════════════════════

def build_exif_jpeg(timestamp):
    """Minimal valid JPEG with EXIF (GPS, camera model, datetime)."""
    dt_str = time.strftime("%Y:%m:%d %H:%M:%S", time.gmtime(timestamp))
    dt_bytes = dt_str.encode("ascii") + b'\x00'
    make = b'samsung\x00'
    model = b'SM-S9280\x00'
    lat = 40.7128 + random.uniform(-0.05, 0.05)
    lon = -74.0060 + random.uniform(-0.05, 0.05)
    lat_ref = b'N\x00'
    lon_ref = b'W\x00'
    lat, lon = abs(lat), abs(lon)

    def deg_to_rational(deg):
        d = int(deg); m = int((deg - d) * 60); s = int(((deg - d) * 60 - m) * 60 * 100)
        return struct.pack('>IIIIII', d, 1, m, 1, s, 100)

    lat_r = deg_to_rational(lat)
    lon_r = deg_to_rational(lon)

    ifd0_count = 5
    ifd0_size = 2 + ifd0_count * 12 + 4
    data_start = 8 + ifd0_size
    data_area = bytearray()

    def add_data(d):
        off = data_start + len(data_area); data_area.extend(d); return off

    make_off = add_data(make)
    model_off = add_data(model)
    dt_off = add_data(dt_bytes)
    gps_lat_off = add_data(lat_r)
    gps_lon_off = add_data(lon_r)

    exif_ifd_offset = data_start + len(data_area)
    exif_entries = struct.pack('>H', 3)
    exif_entries += struct.pack('>HHII', 0x9003, 2, 20, dt_off)
    exif_entries += struct.pack('>HHII', 0xA002, 3, 1, (4032 << 16))
    exif_entries += struct.pack('>HHII', 0xA003, 3, 1, (3024 << 16))
    exif_entries += struct.pack('>I', 0)
    data_area.extend(exif_entries)

    gps_ifd_offset = data_start + len(data_area)
    gps_entries = struct.pack('>H', 4)
    gps_entries += struct.pack('>HHII', 0x0001, 2, 2, int.from_bytes(lat_ref, 'big') << 16)
    gps_entries += struct.pack('>HHII', 0x0002, 5, 3, gps_lat_off)
    gps_entries += struct.pack('>HHII', 0x0003, 2, 2, int.from_bytes(lon_ref, 'big') << 16)
    gps_entries += struct.pack('>HHII', 0x0004, 5, 3, gps_lon_off)
    gps_entries += struct.pack('>I', 0)
    data_area.extend(gps_entries)

    ifd0 = struct.pack('>H', ifd0_count)
    ifd0 += struct.pack('>HHII', 0x010F, 2, len(make), make_off)
    ifd0 += struct.pack('>HHII', 0x0110, 2, len(model), model_off)
    ifd0 += struct.pack('>HHII', 0x0132, 2, 20, dt_off)
    ifd0 += struct.pack('>HHII', 0x8769, 4, 1, exif_ifd_offset)
    ifd0 += struct.pack('>HHII', 0x8825, 4, 1, gps_ifd_offset)
    ifd0 += struct.pack('>I', 0)

    tiff = b'MM' + struct.pack('>HI', 42, 8) + ifd0 + bytes(data_area)
    exif_header = b'Exif\x00\x00'
    app1_data = exif_header + tiff
    app1 = b'\xff\xe1' + struct.pack('>H', len(app1_data) + 2) + app1_data
    body = os.urandom(random.randint(8192, 16384))
    return b'\xff\xd8' + app1 + body + b'\xff\xd9'


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    start = time.time()
    log.info("=" * 70)
    log.info(f"PHASE 2 INJECTION — Contacts, Calls, SMS, Gallery, History")
    log.info("=" * 70)

    # Stop providers before modifying DBs
    log.info("\n[STOP] Force-stopping providers...")
    for pkg in ["com.android.providers.contacts", "com.android.providers.telephony",
                "com.android.chrome", "com.google.android.gms"]:
        await sh(f"am force-stop {pkg} 2>/dev/null")
    await asyncio.sleep(2)

    # ─── CONTACTS ───
    log.info("\n[1/5] CONTACTS — Building contacts2.db...")
    contacts_bytes, contact_names = build_contacts_db()
    uid = await sh("stat -c %U /data/data/com.android.providers.contacts 2>/dev/null")
    uid = uid.strip() if uid else "u0_a24"
    await push_bytes(contacts_bytes,
                     "/data/data/com.android.providers.contacts/databases/contacts2.db",
                     owner=f"{uid}:{uid}", mode="660")
    # Clean WAL
    await sh("rm -f /data/data/com.android.providers.contacts/databases/contacts2.db-wal "
             "/data/data/com.android.providers.contacts/databases/contacts2.db-shm "
             "/data/data/com.android.providers.contacts/databases/contacts2.db-journal")
    log.info(f"  ✓ {len(contact_names)} contacts injected")

    # ─── CALL LOGS ───
    log.info("\n[2/5] CALL LOGS — Building calllog.db...")
    calllog_bytes, call_count = build_calllog_db()
    await push_bytes(calllog_bytes,
                     "/data/data/com.android.providers.contacts/databases/calllog.db",
                     owner=f"{uid}:{uid}", mode="660")
    await sh("rm -f /data/data/com.android.providers.contacts/databases/calllog.db-wal "
             "/data/data/com.android.providers.contacts/databases/calllog.db-shm "
             "/data/data/com.android.providers.contacts/databases/calllog.db-journal")
    log.info(f"  ✓ {call_count} call log entries injected")

    # ─── SMS ───
    log.info("\n[3/5] SMS — Building mmssms.db...")
    sms_bytes, sms_count = build_sms_db()
    # Find telephony provider UID
    tel_uid = await sh("stat -c %U /data/data/com.android.providers.telephony 2>/dev/null")
    tel_uid = tel_uid.strip() if tel_uid else "radio"
    # Ensure dir exists
    await sh("mkdir -p /data/data/com.android.providers.telephony/databases")
    await push_bytes(sms_bytes,
                     "/data/data/com.android.providers.telephony/databases/mmssms.db",
                     owner=f"{tel_uid}:{tel_uid}", mode="660")
    await sh("rm -f /data/data/com.android.providers.telephony/databases/mmssms.db-wal "
             "/data/data/com.android.providers.telephony/databases/mmssms.db-shm "
             "/data/data/com.android.providers.telephony/databases/mmssms.db-journal")
    log.info(f"  ✓ {sms_count} SMS messages injected")

    # ─── CHROME HISTORY ───
    log.info("\n[4/5] CHROME HISTORY — Building History db...")
    history_bytes, hist_count = build_chrome_history_db()
    chrome_uid = await sh("stat -c %U /data/data/com.android.chrome 2>/dev/null")
    chrome_uid = chrome_uid.strip() if chrome_uid else "system"
    chrome_dir = "/data/data/com.android.chrome/app_chrome/Default"
    await sh(f"mkdir -p {chrome_dir}")
    await push_bytes(history_bytes, f"{chrome_dir}/History",
                     owner=f"{chrome_uid}:{chrome_uid}", mode="660")
    log.info(f"  ✓ {hist_count} history URLs injected")

    # ─── GALLERY ───
    log.info("\n[5/5] GALLERY — Generating EXIF JPEGs...")
    await sh("mkdir -p /sdcard/DCIM/Camera")
    photo_count = 0
    now = time.time()
    for i in range(12):
        days_back = random.randint(1, 60)
        photo_ts = now - (days_back * 86400) - random.randint(0, 86400)
        date_str = time.strftime("%Y%m%d_%H%M%S", time.gmtime(photo_ts))
        fname = f"IMG_{date_str}_{random.randint(100,999)}.jpg"
        jpeg_data = build_exif_jpeg(photo_ts)
        touch_fmt = time.strftime("%Y%m%d%H%M.%S", time.gmtime(photo_ts))

        ok = await push_bytes(jpeg_data, f"/sdcard/DCIM/Camera/{fname}",
                              owner="media_rw:media_rw", mode="664")
        if ok:
            await sh(f"touch -t {touch_fmt} /sdcard/DCIM/Camera/{fname} 2>/dev/null")
            photo_count += 1

    # Trigger media scan
    await sh("am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/DCIM/Camera/ 2>/dev/null")
    log.info(f"  ✓ {photo_count} photos with EXIF injected")

    # ─── RESTART + VERIFY ───
    log.info("\n[VERIFY] Restarting providers and verifying...")
    await sh("am broadcast -a android.intent.action.PROVIDER_CHANGED -d content://com.android.contacts 2>/dev/null")
    await sh("am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null")
    await sh("am force-stop com.google.android.gms")
    await asyncio.sleep(3)

    # Account check
    acct = await sh("dumpsys account 2>/dev/null | head -5")
    log.info(f"  Accounts: {acct}")

    # Contact count
    c_count = await sh("ls /data/data/com.android.providers.contacts/databases/ 2>/dev/null")
    log.info(f"  Contacts DBs: {c_count}")

    # SMS check
    s_check = await sh("ls -la /data/data/com.android.providers.telephony/databases/mmssms.db 2>/dev/null")
    log.info(f"  SMS DB: {s_check}")

    # Photos
    p_count = await sh("ls /sdcard/DCIM/Camera/ 2>/dev/null | wc -l")
    log.info(f"  Photos: {p_count}")

    # Chrome history
    h_check = await sh(f"ls -la {chrome_dir}/History 2>/dev/null")
    log.info(f"  Chrome History: {h_check}")

    elapsed = time.time() - start
    log.info(f"\n{'='*70}")
    log.info(f"PHASE 2 COMPLETE in {elapsed:.1f}s")
    log.info(f"  Contacts: {len(contact_names)}")
    log.info(f"  Call logs: {call_count}")
    log.info(f"  SMS: {sms_count}")
    log.info(f"  Photos: {photo_count}")
    log.info(f"  History URLs: {hist_count}")
    log.info(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
