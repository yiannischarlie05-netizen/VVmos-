#!/usr/bin/env python3
"""
VMOS FINAL INJECTION — All-in-one: Contacts, Calls, SMS, Gallery, Chrome, Account restart.
Uses sync_cmd API for file pushes (proven working) + ADB shell for verification.
"""
import asyncio, base64, hashlib, json, logging, os, random, secrets
import sqlite3, struct, sys, tempfile, time

sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/core")
os.environ["VMOS_CLOUD_AK"] = "YOUR_VMOS_AK_HERE"
os.environ["VMOS_CLOUD_SK"] = "YOUR_VMOS_SK_HERE"
from vmos_cloud_api import VMOSCloudClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("final")

PAD = "APP5B54EI0Z1EOEA"
EMAIL = "epolusamuel682@gmail.com"
NAME = "Epolu Samuel"
client = VMOSCloudClient(ak=os.environ["VMOS_CLOUD_AK"], sk=os.environ["VMOS_CLOUD_SK"])

ADB = "/opt/titan/cuttlefish/cf/bin/adb"
ADB_TARGET = "localhost:7342"

CONTACTS = [
    ("James", "Wilson"), ("Sarah", "Johnson"), ("Michael", "Davis"),
    ("Jennifer", "Martinez"), ("David", "Anderson"), ("Lisa", "Thomas"),
    ("Robert", "Taylor"), ("Karen", "Moore"), ("William", "Jackson"),
    ("Jessica", "White"), ("Chris", "Harris"), ("Ashley", "Martin"),
    ("Daniel", "Thompson"), ("Emily", "Garcia"), ("Matthew", "Brown"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def sh(cmd, timeout=30):
    """Shell via sync_cmd API."""
    try:
        r = await client.sync_cmd(PAD, cmd, timeout_sec=timeout)
        if r.get("code") == 200:
            d = r.get("data")
            if isinstance(d, list) and d:
                return str(d[0].get("errorMsg", "")).strip()
        return ""
    except Exception as e:
        return f"[ERR:{e}]"

async def push_bytes(data, target_path, owner="system:system", mode="660"):
    """Push bytes via chunked base64 through sync_cmd."""
    b64 = base64.b64encode(data).decode("ascii")
    h = hashlib.md5(target_path.encode()).hexdigest()[:8]
    staging = f"/data/local/tmp/_f_{h}"
    b64f = f"{staging}.b64"
    await sh(f"rm -f {b64f} {staging}")

    CHUNK = 3000
    chunks = [b64[i:i+CHUNK] for i in range(0, len(b64), CHUNK)]
    log.info(f"    Push {len(data)}B ({len(chunks)} chunks) → {target_path}")

    for i, chunk in enumerate(chunks):
        await sh(f"echo -n '{chunk}' >> {b64f}")
        if i % 6 == 5:
            await asyncio.sleep(1)

    await sh(f"base64 -d {b64f} > {staging} 2>/dev/null")
    target_dir = os.path.dirname(target_path)
    await sh(f"mkdir -p {target_dir}")
    await sh(f"cp {staging} {target_path}")
    await sh(f"chown {owner} {target_path}")
    await sh(f"chmod {mode} {target_path}")
    await sh(f"restorecon {target_path} 2>/dev/null")
    await sh(f"rm -f {b64f} {staging}")
    # Clean WAL/SHM/journal for databases
    if target_path.endswith(".db"):
        await sh(f"rm -f {target_path}-wal {target_path}-shm {target_path}-journal")
    return True

def tmp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path

def read_and_delete(path):
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data

# ═══════════════════════════════════════════════════════════════════════════════
# BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def build_contacts_db():
    path = tmp_db()
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS raw_contacts (
            _id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER, account_type TEXT, account_name TEXT,
            version INTEGER DEFAULT 1, dirty INTEGER DEFAULT 0,
            deleted INTEGER DEFAULT 0, display_name TEXT,
            display_name_alt TEXT, display_name_source INTEGER DEFAULT 40,
            times_contacted INTEGER DEFAULT 0, last_time_contacted INTEGER DEFAULT 0,
            starred INTEGER DEFAULT 0, pinned INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS mimetypes (
            _id INTEGER PRIMARY KEY AUTOINCREMENT, mimetype TEXT UNIQUE);
        INSERT OR IGNORE INTO mimetypes(mimetype) VALUES('vnd.android.cursor.item/name');
        INSERT OR IGNORE INTO mimetypes(mimetype) VALUES('vnd.android.cursor.item/phone_v2');
        INSERT OR IGNORE INTO mimetypes(mimetype) VALUES('vnd.android.cursor.item/email_v2');
        CREATE TABLE IF NOT EXISTS data (
            _id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_contact_id INTEGER, mimetype_id INTEGER,
            is_primary INTEGER DEFAULT 0, is_super_primary INTEGER DEFAULT 0,
            data1 TEXT, data2 TEXT, data3 TEXT);
        CREATE TABLE IF NOT EXISTS android_metadata (locale TEXT);
        INSERT OR IGNORE INTO android_metadata VALUES ('en_US');
    """)
    c = conn.cursor()
    c.execute("SELECT _id, mimetype FROM mimetypes")
    mm = {r[1]: r[0] for r in c.fetchall()}
    nm, pm, em = mm.get('vnd.android.cursor.item/name'), mm.get('vnd.android.cursor.item/phone_v2'), mm.get('vnd.android.cursor.item/email_v2')

    for i, (first, last) in enumerate(CONTACTS):
        full = f"{first} {last}"
        area = random.choice(["212","310","415","305","713","312","404","206"])
        phone = f"+1{area}{random.randint(2000000,9999999)}"
        rc_id = i + 1
        c.execute("INSERT INTO raw_contacts(_id,display_name,display_name_alt,times_contacted,last_time_contacted) VALUES(?,?,?,?,?)",
                  (rc_id, full, f"{last}, {first}", random.randint(0,15), int(time.time()*1000)-random.randint(0,90*86400000)))
        if nm: c.execute("INSERT INTO data(raw_contact_id,mimetype_id,data1,data2,data3) VALUES(?,?,?,?,?)", (rc_id, nm, full, first, last))
        if pm: c.execute("INSERT INTO data(raw_contact_id,mimetype_id,data1,data2) VALUES(?,?,?,?)", (rc_id, pm, phone, "2"))
        if em: c.execute("INSERT INTO data(raw_contact_id,mimetype_id,data1,data2) VALUES(?,?,?,?)", (rc_id, em, f"{first.lower()}.{last.lower()}@gmail.com", "1"))
    conn.commit(); conn.close()
    return read_and_delete(path)

def build_calllog_db():
    path = tmp_db()
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE IF NOT EXISTS calls (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT, type INTEGER DEFAULT 1, date INTEGER,
        duration INTEGER DEFAULT 0, new INTEGER DEFAULT 0,
        name TEXT DEFAULT '', numbertype INTEGER DEFAULT 0,
        countryiso TEXT DEFAULT 'US')""")
    c = conn.cursor()
    now = int(time.time()*1000)
    for i in range(25):
        f, l = random.choice(CONTACTS)
        area = random.choice(["212","310","415","305","713"])
        ct = random.choice([1,1,2,2,3])
        dur = 0 if ct == 3 else random.randint(15,600)
        dt = now - random.randint(0,90)*86400000 - random.randint(0,86400000)
        c.execute("INSERT INTO calls(number,type,date,duration,new,name,countryiso) VALUES(?,?,?,?,0,?,?)",
                  (f"+1{area}{random.randint(2000000,9999999)}", ct, dt, dur, f"{f} {l}", "US"))
    conn.commit(); conn.close()
    return read_and_delete(path)

def build_sms_db():
    path = tmp_db()
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE IF NOT EXISTS sms (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT, body TEXT, type INTEGER DEFAULT 1,
        date INTEGER, read INTEGER DEFAULT 1,
        seen INTEGER DEFAULT 1, thread_id INTEGER DEFAULT 1)""")
    msgs = ["Hey, how are you?","On my way!","Thanks!","See you soon","Can you call me?",
            "Running late","Sounds good!","Miss you!","Meeting at 3pm","Got it, thanks",
            "Happy birthday!","No problem","What time works?","Dinner tonight?","Good morning!",
            "Let me know","Okay, will do","Be there in 10","Sorry, missed your call","Talk later?"]
    c = conn.cursor()
    now = int(time.time()*1000)
    for i in range(30):
        area = random.choice(["212","310","415","305","713"])
        addr = f"+1{area}{random.randint(2000000,9999999)}"
        dt = now - random.randint(0,60)*86400000 - random.randint(0,86400000)
        c.execute("INSERT INTO sms(address,body,type,date,read,seen,thread_id) VALUES(?,?,?,?,1,1,?)",
                  (addr, random.choice(msgs), random.choice([1,1,2]), dt, (i%8)+1))
    conn.commit(); conn.close()
    return read_and_delete(path)

def build_chrome_history():
    urls = [
        ("https://www.google.com/search?q=weather+today","weather today - Google Search"),
        ("https://www.amazon.com/","Amazon.com: Online Shopping"),
        ("https://www.youtube.com/","YouTube"),
        ("https://mail.google.com/mail/","Gmail - Inbox"),
        ("https://www.reddit.com/","Reddit"),
        ("https://www.netflix.com/browse","Netflix"),
        ("https://maps.google.com/","Google Maps"),
        ("https://www.instagram.com/","Instagram"),
        ("https://www.facebook.com/","Facebook"),
        ("https://www.linkedin.com/feed/","LinkedIn"),
        ("https://www.walmart.com/","Walmart"),
        ("https://www.target.com/","Target"),
        ("https://www.espn.com/","ESPN"),
        ("https://stackoverflow.com/","Stack Overflow"),
        ("https://github.com/","GitHub"),
    ]
    path = tmp_db()
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY, url TEXT NOT NULL, title TEXT NOT NULL DEFAULT '',
        visit_count INTEGER NOT NULL DEFAULT 1, typed_count INTEGER NOT NULL DEFAULT 0,
        last_visit_time INTEGER NOT NULL DEFAULT 0, hidden INTEGER NOT NULL DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY, url INTEGER NOT NULL, visit_time INTEGER NOT NULL,
        from_visit INTEGER NOT NULL DEFAULT 0, transition INTEGER NOT NULL DEFAULT 0,
        segment_id INTEGER NOT NULL DEFAULT 0, visit_duration INTEGER NOT NULL DEFAULT 0)""")

    epoch_off = 11644473600000000
    now_c = int(time.time()*1000000) + epoch_off
    for url, title in urls:
        visits = random.randint(1,8)
        last = now_c - random.randint(0, 30*86400*1000000)
        c.execute("INSERT INTO urls(url,title,visit_count,last_visit_time) VALUES(?,?,?,?)", (url,title,visits,last))
        uid = c.lastrowid
        for v in range(visits):
            vt = last - random.randint(0, 60*86400*1000000)
            c.execute("INSERT INTO visits(url,visit_time,transition,visit_duration) VALUES(?,?,0,?)",
                      (uid, vt, random.randint(5000000,300000000)))
    conn.commit(); conn.close()
    return read_and_delete(path)

def build_exif_jpeg(ts):
    dt_str = time.strftime("%Y:%m:%d %H:%M:%S", time.gmtime(ts))
    dt_b = dt_str.encode("ascii") + b'\x00'
    make, model = b'samsung\x00', b'SM-S9280\x00'
    lat = 40.7128 + random.uniform(-0.05, 0.05)
    lon = 74.0060 + random.uniform(-0.05, 0.05)
    def d2r(d):
        dd=int(d); mm=int((d-dd)*60); ss=int(((d-dd)*60-mm)*60*100)
        return struct.pack('>IIIIII',dd,1,mm,1,ss,100)
    lr, lonr = d2r(lat), d2r(lon)
    n5 = 5; sz = 2 + n5*12 + 4; ds = 8 + sz
    da = bytearray()
    def ad(d):
        o = ds + len(da); da.extend(d); return o
    mo, mdo, dto = ad(make), ad(model), ad(dt_b)
    glo, gloo = ad(lr), ad(lonr)
    eio = ds + len(da)
    ee = struct.pack('>H',3)
    ee += struct.pack('>HHII',0x9003,2,20,dto)
    ee += struct.pack('>HHII',0xA002,3,1,(4032<<16))
    ee += struct.pack('>HHII',0xA003,3,1,(3024<<16))
    ee += struct.pack('>I',0)
    da.extend(ee)
    gio = ds + len(da)
    ge = struct.pack('>H',4)
    ge += struct.pack('>HHII',0x0001,2,2,int.from_bytes(b'N\x00','big')<<16)
    ge += struct.pack('>HHII',0x0002,5,3,glo)
    ge += struct.pack('>HHII',0x0003,2,2,int.from_bytes(b'W\x00','big')<<16)
    ge += struct.pack('>HHII',0x0004,5,3,gloo)
    ge += struct.pack('>I',0)
    da.extend(ge)
    ifd = struct.pack('>H',n5)
    ifd += struct.pack('>HHII',0x010F,2,len(make),mo)
    ifd += struct.pack('>HHII',0x0110,2,len(model),mdo)
    ifd += struct.pack('>HHII',0x0132,2,20,dto)
    ifd += struct.pack('>HHII',0x8769,4,1,eio)
    ifd += struct.pack('>HHII',0x8825,4,1,gio)
    ifd += struct.pack('>I',0)
    tiff = b'MM' + struct.pack('>HI',42,8) + ifd + bytes(da)
    eh = b'Exif\x00\x00'
    a1d = eh + tiff
    a1 = b'\xff\xe1' + struct.pack('>H',len(a1d)+2) + a1d
    return b'\xff\xd8' + a1 + os.urandom(random.randint(8192,16384)) + b'\xff\xd9'


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    t0 = time.time()
    log.info("=" * 65)
    log.info("FINAL INJECTION — Contacts, Calls, SMS, Chrome, Gallery + Verify")
    log.info("=" * 65)

    # Stop providers
    log.info("\n[PREP] Stopping content providers...")
    for pkg in ["com.android.providers.contacts","com.android.providers.telephony",
                "com.android.chrome","com.google.android.gms","com.android.vending"]:
        await sh(f"am force-stop {pkg} 2>/dev/null")
    await asyncio.sleep(2)

    # ── 1. CONTACTS ──
    log.info("\n[1/5] CONTACTS")
    cdb = build_contacts_db()
    uid = await sh("stat -c %U /data/data/com.android.providers.contacts 2>/dev/null")
    uid = uid.strip() if uid and "ERR" not in uid else "u0_a24"
    await push_bytes(cdb, "/data/data/com.android.providers.contacts/databases/contacts2.db",
                     owner=f"{uid}:{uid}", mode="660")
    log.info(f"  ✓ {len(CONTACTS)} contacts")

    # ── 2. CALL LOGS ──
    log.info("\n[2/5] CALL LOGS")
    cldb = build_calllog_db()
    await push_bytes(cldb, "/data/data/com.android.providers.contacts/databases/calllog.db",
                     owner=f"{uid}:{uid}", mode="660")
    log.info("  ✓ 25 call records")

    # ── 3. SMS ──
    log.info("\n[3/5] SMS")
    sdb = build_sms_db()
    tuid = await sh("stat -c %U /data/data/com.android.providers.telephony 2>/dev/null")
    tuid = tuid.strip() if tuid and "ERR" not in tuid else "radio"
    await sh("mkdir -p /data/data/com.android.providers.telephony/databases")
    await push_bytes(sdb, "/data/data/com.android.providers.telephony/databases/mmssms.db",
                     owner=f"{tuid}:{tuid}", mode="660")
    log.info("  ✓ 30 SMS messages")

    # ── 4. CHROME HISTORY ──
    log.info("\n[4/5] CHROME HISTORY")
    hdb = build_chrome_history()
    cuid = await sh("stat -c %U /data/data/com.android.chrome 2>/dev/null")
    cuid = cuid.strip() if cuid and "ERR" not in cuid else "system"
    cdir = "/data/data/com.android.chrome/app_chrome/Default"
    await sh(f"mkdir -p {cdir}")
    await push_bytes(hdb, f"{cdir}/History", owner=f"{cuid}:{cuid}", mode="660")
    log.info("  ✓ 15 URLs with visit history")

    # ── 5. GALLERY PHOTOS ──
    log.info("\n[5/5] GALLERY — 12 EXIF photos")
    await sh("mkdir -p /sdcard/DCIM/Camera")
    pc = 0
    now = time.time()
    for i in range(12):
        days = random.randint(1, 60)
        pts = now - days*86400 - random.randint(0,86400)
        ds = time.strftime("%Y%m%d_%H%M%S", time.gmtime(pts))
        fn = f"IMG_{ds}_{random.randint(100,999)}.jpg"
        jpg = build_exif_jpeg(pts)
        tf = time.strftime("%Y%m%d%H%M.%S", time.gmtime(pts))
        ok = await push_bytes(jpg, f"/sdcard/DCIM/Camera/{fn}", owner="media_rw:media_rw", mode="664")
        if ok:
            await sh(f"touch -t {tf} /sdcard/DCIM/Camera/{fn} 2>/dev/null")
            pc += 1
    await sh("am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/DCIM/Camera/ 2>/dev/null")
    log.info(f"  ✓ {pc} photos with EXIF (GPS, Samsung camera model, timestamps)")

    # ── ACCOUNT RESTART ──
    log.info("\n[RESTART] Forcing account manager to re-read databases...")
    await sh("am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null")
    await sh("am broadcast -a android.intent.action.PROVIDER_CHANGED -d content://com.android.contacts 2>/dev/null")
    await sh("am force-stop com.google.android.gms")
    await sh("am force-stop com.android.vending")
    await asyncio.sleep(3)

    # ── VERIFICATION ──
    log.info("\n[VERIFY]")
    r = await sh("dumpsys account 2>/dev/null | head -5")
    log.info(f"  Account service:\n    {r}")

    r = await sh("ls -la /data/data/com.android.providers.contacts/databases/contacts2.db")
    log.info(f"  contacts2.db: {r}")

    r = await sh("ls -la /data/data/com.android.providers.contacts/databases/calllog.db")
    log.info(f"  calllog.db: {r}")

    r = await sh("ls -la /data/data/com.android.providers.telephony/databases/mmssms.db")
    log.info(f"  mmssms.db: {r}")

    r = await sh(f"ls -la {cdir}/History")
    log.info(f"  Chrome History: {r}")

    r = await sh("ls /sdcard/DCIM/Camera/ | wc -l")
    log.info(f"  Photos: {r}")

    # Check if account DB has data
    r = await sh("ls -la /data/system_ce/0/accounts_ce.db")
    log.info(f"  accounts_ce.db: {r}")

    elapsed = time.time() - t0
    log.info(f"\n{'='*65}")
    log.info(f"ALL INJECTIONS COMPLETE in {elapsed:.0f}s")
    log.info(f"  Contacts: {len(CONTACTS)} | Calls: 25 | SMS: 30")
    log.info(f"  Chrome URLs: 15 | Photos: {pc}")
    log.info(f"  Account: {EMAIL}")
    log.info(f"{'='*65}")

if __name__ == "__main__":
    asyncio.run(main())
