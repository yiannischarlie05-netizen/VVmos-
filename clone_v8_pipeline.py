#!/usr/bin/env python3
"""
Clone v8 Pipeline — Full Device Clone with Root Cause Fixes
============================================================
Pull-Modify-Push native DBs, Cloud API app install, VPS HTTP relay.

Target:    ABP63U6H37MV34I0 (10.10.80.2, Android 16 vcloud)
Launchpad: APP6476KYH9KMLU5 (10.12.11.186)
Neighbor:  10.12.21.175 (Samsung SM-S9110 identity)
VPS:       37.60.234.139 (THIS machine, HTTP :9999)

Root causes fixed:
  1. NO fingerprint change (was crashing platform)
  2. Correct GMS UID 10036 (was 1021)
  3. Pull-modify-push native DBs (was building wrong schema)
"""
import asyncio
import base64
import hashlib
import json
import os
import secrets
import sqlite3
import struct
import sys
import tempfile
import time
from pathlib import Path

os.environ["VMOS_ALLOW_RESTART"] = "1"
sys.path.insert(0, ".")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
from vmos_titan.core.vmos_db_builder import VMOSDbBuilder

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
TARGET = "ABP63U6H37MV34I0"
LAUNCHPAD = "APP6476KYH9KMLU5"
NEIGHBOR_IP = "10.12.21.175"
VPS_IP = "37.60.234.139"
VPS_HTTP_PORT = 9999
BASE_URL = "https://api.vmoscloud.com"
STAGING = "/data/local/tmp/clone8"
CMD_DELAY = 3.0

# Native GMS UID on VMOS Cloud
GMS_UID = 10036

# VPS served directory (http.server :9999 serves from here)
VPS_DIR = Path("/root/CascadeProjects/vmos-titan-unified/neighbor_clones/clone_dbs")

# Identity — ONLY cloud-safe props (NO ro.build.fingerprint!)
SAFE_IDENTITY = {
    "persist.sys.cloud.imeinum": "312671446307090",
    "persist.sys.cloud.imsinum": "234103772931327",
    "persist.sys.cloud.iccidnum": "89445046905698751410",
    "persist.sys.cloud.phonenum": "4453816683684",
    "persist.sys.cloud.drm.id": "iRz4b1B4ZeJRlMAz7YlNB7CfGHVCkewvha1U97EwEsM=",
    "persist.sys.cloud.gps.lat": "54.5585",
    "persist.sys.cloud.gps.lon": "-1.1476",
}

ACCOUNTS = [
    {"email": "petersfaustina699@gmail.com", "display_name": "Peters Faustina"},
    {"email": "faustinapeters11@gmail.com", "display_name": "Faustina Peters"},
]

# All 12 Google packages that need account visibility
VISIBILITY_PACKAGES = [
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
]

# Grant UIDs — system (1000) + GMS (10036)
GRANT_UIDS = [1000, GMS_UID]
GRANT_TYPES = ["", "com.google", "SID", "LSID"]

# ═══════════════════════════════════════════════════════════════
# ADB PROTOCOL HELPERS (for neighbor commands via launchpad)
# ═══════════════════════════════════════════════════════════════
def _pkt(c, a0, a1, d=b""):
    cs = sum(d) & 0xFFFFFFFF
    mg = struct.unpack("<I", c)[0] ^ 0xFFFFFFFF
    return struct.pack("<4sIIIII", c, a0, a1, len(d), cs, mg) + d

def adb_cnxn():
    return _pkt(b"CNXN", 0x01000001, 256 * 1024, b"host::\x00")

def adb_open(lid, svc):
    return _pkt(b"OPEN", lid, 0, svc.encode() + b"\x00")


# ═══════════════════════════════════════════════════════════════
# CLOUD API HELPERS
# ═══════════════════════════════════════════════════════════════

async def tgt(client, sh, timeout=30, retries=3):
    """Execute command on TARGET with retry."""
    for attempt in range(retries):
        try:
            r = await client.sync_cmd(TARGET, sh, timeout_sec=timeout)
            if r.get("code") == 200:
                data = r.get("data", [])
                if data and isinstance(data, list) and data[0]:
                    return (data[0].get("errorMsg") or "").strip()
                return ""
            elif r.get("code") in (110012, 110031):
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
            return None
        except Exception:
            if attempt < retries - 1:
                await asyncio.sleep(3)
    return None


async def lp(client, sh, timeout=30, retries=3):
    """Execute command on LAUNCHPAD with retry."""
    for attempt in range(retries):
        try:
            r = await client.sync_cmd(LAUNCHPAD, sh, timeout_sec=timeout)
            if r.get("code") == 200:
                data = r.get("data", [])
                if data and isinstance(data, list) and data[0]:
                    return (data[0].get("errorMsg") or "").strip()
                return ""
            elif r.get("code") in (110012, 110031):
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                    continue
            return None
        except Exception:
            if attempt < retries - 1:
                await asyncio.sleep(2)
    return None


async def lp_fire(client, sh):
    """Fire-and-forget on launchpad."""
    try:
        await client.async_adb_cmd([LAUNCHPAD], sh)
    except Exception:
        pass


async def nb_cmd(client, shell_cmd, timeout=8):
    """Execute command on NEIGHBOR via raw ADB over nc relay through launchpad."""
    await lp(client, f"mkdir -p {STAGING}")
    tag = f"{hash(shell_cmd) & 0xFFFF:04x}"

    b64c = base64.b64encode(adb_cnxn()).decode()
    await lp(client, f"echo -n '{b64c}' | base64 -d > {STAGING}/.cnxn")
    await asyncio.sleep(1)

    pkt = adb_open(1, f"shell:{shell_cmd}")
    b64o = base64.b64encode(pkt).decode()
    await lp(client, f"echo -n '{b64o}' | base64 -d > {STAGING}/.o{tag}")
    await asyncio.sleep(1)

    relay = (
        f"(cat {STAGING}/.cnxn; sleep 0.3; cat {STAGING}/.o{tag}; sleep {timeout}) | "
        f"timeout {timeout + 2} nc {NEIGHBOR_IP} 5555 > {STAGING}/.r{tag} 2>/dev/null"
    )
    await lp_fire(client, relay)
    await asyncio.sleep(timeout + 4)

    await lp(client,
        f"strings -n 2 {STAGING}/.r{tag} 2>/dev/null | "
        f"grep -vE '^(CNXN|OKAY|WRTE|CLSE|OPEN|host::|device::)' > {STAGING}/.t{tag}")
    await asyncio.sleep(1)

    result = await lp(client, f"cat {STAGING}/.t{tag} 2>/dev/null")
    await lp(client, f"rm -f {STAGING}/.o{tag} {STAGING}/.r{tag} {STAGING}/.t{tag}")
    return (result or "").strip()


# ═══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════

async def main():
    t0 = time.time()
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)

    print("=" * 70, flush=True)
    print("  CLONE v8 PIPELINE", flush=True)
    print(f"  Target:    {TARGET} (Android 16 vcloud)", flush=True)
    print(f"  Neighbor:  {NEIGHBOR_IP} (Samsung SM-S9110)", flush=True)
    print(f"  Accounts:  {', '.join(a['email'] for a in ACCOUNTS)}", flush=True)
    print(f"  GMS UID:   {GMS_UID}", flush=True)
    print("=" * 70, flush=True)

    # ══════════════════════════════════════════════════════════
    # PHASE 1: PULL NATIVE DBs FROM TARGET
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 1] PULL NATIVE DBs FROM TARGET", flush=True)

    await tgt(client, f"mkdir -p {STAGING}")
    await asyncio.sleep(2)

    VPS_DIR.mkdir(parents=True, exist_ok=True)

    # Start nc listeners on VPS for DB pull
    import subprocess
    import threading

    for db_name, dev_path in [
        ("native_ce.db", "/data/system_ce/0/accounts_ce.db"),
        ("native_de.db", "/data/system_de/0/accounts_de.db"),
    ]:
        local_path = VPS_DIR / db_name
        local_path.unlink(missing_ok=True)

        port = 19200 if "ce" in db_name else 19201

        # Start nc listener on VPS
        def listen(p, lp):
            try:
                subprocess.run(
                    f"timeout 30 nc -l -p {p} > {lp}",
                    shell=True, timeout=35
                )
            except Exception:
                pass

        t = threading.Thread(target=listen, args=(port, str(local_path)), daemon=True)
        t.start()
        await asyncio.sleep(1)

        # Tell target to send DB to VPS (async — nc takes >2s)
        try:
            await client.async_adb_cmd([TARGET],
                f"cat {dev_path} | nc -w 5 {VPS_IP} {port}")
        except Exception:
            pass
        print(f"  {db_name}: sent async nc command", flush=True)
        await asyncio.sleep(8)  # Wait for transfer

        # Verify
        t.join(timeout=10)
        if local_path.exists():
            sz = local_path.stat().st_size
            print(f"  {db_name}: received {sz} bytes", flush=True)
            if sz == 0:
                print(f"  WARN: empty file — trying curl fallback", flush=True)
                # Fallback: use base64 via syncCmd for small file
                out = await tgt(client,
                    f"base64 {dev_path} 2>/dev/null | head -200",
                    timeout=15)
                if out:
                    try:
                        data = base64.b64decode(out)
                        local_path.write_bytes(data)
                        print(f"  {db_name}: b64 fallback got {len(data)} bytes", flush=True)
                    except Exception as e:
                        print(f"  {db_name}: b64 fallback failed: {e}", flush=True)
        else:
            print(f"  {db_name}: FAILED to receive", flush=True)
        await asyncio.sleep(CMD_DELAY)

    # Verify DBs are valid SQLite
    for db_name in ["native_ce.db", "native_de.db"]:
        local_path = VPS_DIR / db_name
        if local_path.exists() and local_path.stat().st_size > 0:
            try:
                conn = sqlite3.connect(str(local_path))
                uv = conn.execute("PRAGMA user_version").fetchone()[0]
                jm = conn.execute("PRAGMA journal_mode").fetchone()[0]
                tables = [t[0] for t in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                rows = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
                conn.close()
                print(f"  {db_name}: user_version={uv} journal={jm} "
                      f"tables={tables} accounts={rows}", flush=True)
            except Exception as e:
                print(f"  {db_name}: INVALID SQLite: {e}", flush=True)
        else:
            print(f"  {db_name}: missing or empty — will use builder fallback", flush=True)

    # ══════════════════════════════════════════════════════════
    # PHASE 2: MODIFY NATIVE DBs (add accounts + correct UIDs)
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 2] MODIFY NATIVE DBs", flush=True)

    for db_label, db_file in [("ce", "native_ce.db"), ("de", "native_de.db")]:
        local_path = VPS_DIR / db_file
        output_path = VPS_DIR / f"accounts_{db_label}.db"

        if not local_path.exists() or local_path.stat().st_size == 0:
            # Fallback: build from scratch using VMOSDbBuilder
            print(f"  {db_label}: no native DB — building from scratch", flush=True)
            builder = VMOSDbBuilder()
            primary = ACCOUNTS[0]
            if db_label == "ce":
                data = builder.build_accounts_ce(
                    email=primary["email"],
                    display_name=primary["display_name"],
                )
            else:
                data = builder.build_accounts_de(
                    email=primary["email"],
                    display_name=primary["display_name"],
                )
            output_path.write_bytes(data)
        else:
            # Copy native → output for modification
            import shutil
            shutil.copy2(str(local_path), str(output_path))

        # Now modify the DB
        conn = sqlite3.connect(str(output_path))
        conn.execute("PRAGMA journal_mode=DELETE;")
        c = conn.cursor()

        # Get current user_version (preserve it!)
        uv = c.execute("PRAGMA user_version").fetchone()[0]
        print(f"  {db_label}: user_version={uv}", flush=True)

        # Ensure tables exist (in case native DB is minimal)
        if db_label == "ce":
            c.executescript("""
                CREATE TABLE IF NOT EXISTS android_metadata (locale TEXT);
                CREATE TABLE IF NOT EXISTS accounts (
                    _id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, type TEXT NOT NULL, password TEXT,
                    UNIQUE(name, type)
                );
                CREATE TABLE IF NOT EXISTS authtokens (
                    _id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accounts_id INTEGER NOT NULL, type TEXT NOT NULL, authtoken TEXT,
                    UNIQUE(accounts_id, type)
                );
                CREATE TABLE IF NOT EXISTS extras (
                    _id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accounts_id INTEGER, key TEXT NOT NULL, value TEXT,
                    UNIQUE(accounts_id, key)
                );
                CREATE TABLE IF NOT EXISTS grants (
                    accounts_id INTEGER NOT NULL,
                    auth_token_type TEXT NOT NULL DEFAULT '',
                    uid INTEGER NOT NULL,
                    UNIQUE(accounts_id, auth_token_type, uid)
                );
                CREATE TABLE IF NOT EXISTS shared_accounts (
                    _id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, type TEXT NOT NULL,
                    UNIQUE(name, type)
                );
            """)
            c.execute("INSERT OR REPLACE INTO android_metadata (locale) VALUES ('en_US')")
        else:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS accounts (
                    _id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL, type TEXT NOT NULL,
                    previous_name TEXT,
                    last_password_entry_time_millis_epoch INTEGER DEFAULT 0,
                    UNIQUE(name, type)
                );
                CREATE TABLE IF NOT EXISTS grants (
                    accounts_id INTEGER NOT NULL,
                    auth_token_type TEXT NOT NULL DEFAULT '',
                    uid INTEGER NOT NULL,
                    UNIQUE(accounts_id, auth_token_type, uid)
                );
                CREATE TABLE IF NOT EXISTS visibility (
                    accounts_id INTEGER NOT NULL,
                    _package TEXT NOT NULL,
                    value INTEGER,
                    UNIQUE(accounts_id, _package)
                );
                CREATE TABLE IF NOT EXISTS authtokens (
                    _id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accounts_id INTEGER NOT NULL,
                    type TEXT NOT NULL DEFAULT '',
                    authtoken TEXT,
                    UNIQUE(accounts_id, type)
                );
                CREATE TABLE IF NOT EXISTS extras (
                    _id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accounts_id INTEGER NOT NULL,
                    key TEXT NOT NULL DEFAULT '',
                    value TEXT,
                    UNIQUE(accounts_id, key)
                );
            """)

        # Insert accounts
        for acct in ACCOUNTS:
            email = acct["email"]
            dn = acct["display_name"]
            parts = dn.split()
            gaia_id = str(secrets.randbits(64))

            if db_label == "ce":
                # CE: password=NULL (not empty string!)
                c.execute(
                    "INSERT OR IGNORE INTO accounts (name, type, password) "
                    "VALUES (?, 'com.google', NULL)", (email,))
                c.execute("SELECT _id FROM accounts WHERE name=? AND type='com.google'", (email,))
                aid = c.fetchone()[0]

                # Extras
                for key, val in [
                    ("google.services.gaia", gaia_id),
                    ("GoogleUserId", gaia_id),
                    ("is_child_account", "false"),
                    ("given_name", parts[0] if parts else ""),
                    ("family_name", parts[-1] if len(parts) > 1 else ""),
                    ("display_name", dn),
                    ("account_creation_time", str(int(time.time() * 1000))),
                ]:
                    c.execute(
                        "INSERT OR REPLACE INTO extras (accounts_id, key, value) "
                        "VALUES (?, ?, ?)", (aid, key, val))

                # Grants with CORRECT UIDs
                for uid in GRANT_UIDS:
                    for gt in GRANT_TYPES:
                        c.execute(
                            "INSERT OR IGNORE INTO grants "
                            "(accounts_id, auth_token_type, uid) VALUES (?, ?, ?)",
                            (aid, gt, uid))

                # Shared accounts
                c.execute(
                    "INSERT OR IGNORE INTO shared_accounts (name, type) "
                    "VALUES (?, 'com.google')", (email,))

            else:  # DE
                c.execute(
                    "INSERT OR IGNORE INTO accounts "
                    "(name, type, previous_name, last_password_entry_time_millis_epoch) "
                    "VALUES (?, 'com.google', NULL, ?)",
                    (email, int(time.time() * 1000)))
                c.execute("SELECT _id FROM accounts WHERE name=? AND type='com.google'", (email,))
                aid = c.fetchone()[0]

                # Visibility — ALL 12 Google packages
                for pkg in VISIBILITY_PACKAGES:
                    c.execute(
                        "INSERT OR IGNORE INTO visibility "
                        "(accounts_id, _package, value) VALUES (?, ?, 1)",
                        (aid, pkg))

                # Grants with CORRECT UIDs
                for uid in GRANT_UIDS:
                    for gt in GRANT_TYPES:
                        c.execute(
                            "INSERT OR IGNORE INTO grants "
                            "(accounts_id, auth_token_type, uid) VALUES (?, ?, ?)",
                            (aid, gt, uid))

        # Restore user_version
        if uv > 0:
            c.execute(f"PRAGMA user_version = {uv}")

        conn.commit()

        # Verify
        rows = c.execute("SELECT name FROM accounts").fetchall()
        grant_count = c.execute("SELECT COUNT(*) FROM grants").fetchone()[0]
        final_uv = c.execute("PRAGMA user_version").fetchone()[0]
        conn.close()

        # Finalize (ensure DELETE mode, no WAL)
        data = output_path.read_bytes()
        data = VMOSDbBuilder.safe_db_finalize(data)
        output_path.write_bytes(data)

        print(f"  {db_label}: accounts={[r[0] for r in rows]} grants={grant_count} "
              f"uv={final_uv} size={len(data)}", flush=True)

    # ══════════════════════════════════════════════════════════
    # PHASE 3: PUSH MODIFIED DBs → TARGET via VPS HTTP
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 3] PUSH DBs TO TARGET", flush=True)

    DB_MAP = {
        "accounts_ce.db": "/data/system_ce/0/accounts_ce.db",
        "accounts_de.db": "/data/system_de/0/accounts_de.db",
    }

    for db_name, dev_path in DB_MAP.items():
        local = VPS_DIR / db_name
        if not local.exists():
            print(f"  SKIP {db_name}: not found", flush=True)
            continue

        expected_md5 = hashlib.md5(local.read_bytes()).hexdigest()
        url = f"http://{VPS_IP}:{VPS_HTTP_PORT}/clone_dbs/{db_name}"

        # Download on target (fire-and-forget, then verify separately)
        try:
            await client.async_adb_cmd([TARGET],
                f"curl -s -o {STAGING}/{db_name} {url}")
        except Exception:
            pass
        await asyncio.sleep(8)  # Wait for download

        # Verify size
        out = await tgt(client, f"wc -c < {STAGING}/{db_name} 2>/dev/null")
        print(f"  {db_name}: size={out}", flush=True)
        await asyncio.sleep(CMD_DELAY)

        # Verify md5
        out = await tgt(client, f"md5sum {STAGING}/{db_name} 2>/dev/null | cut -d' ' -f1")
        got_md5 = (out or "").strip()
        ok = got_md5 == expected_md5
        print(f"  {db_name}: md5={got_md5} {'✓' if ok else 'MISMATCH!'} "
              f"(expected {expected_md5})", flush=True)

        if not ok:
            # Retry once
            print(f"  Retrying download...", flush=True)
            try:
                await client.async_adb_cmd([TARGET],
                    f"curl -s -o {STAGING}/{db_name} {url}")
            except Exception:
                pass
            await asyncio.sleep(8)
            out = await tgt(client, f"md5sum {STAGING}/{db_name} 2>/dev/null | cut -d' ' -f1")
            got_md5 = (out or "").strip()
            ok = got_md5 == expected_md5
            print(f"  {db_name}: retry md5={got_md5} {'✓' if ok else 'MISMATCH!'}", flush=True)
            if not ok:
                print(f"  FATAL: {db_name} integrity check failed!", flush=True)
                await client.close()
                return
        await asyncio.sleep(CMD_DELAY)

    # Freeze services before swap
    print("  Freezing services...", flush=True)
    for pkg in ["com.google.android.gms", "com.google.android.gsf",
                "com.android.vending", "com.google.android.gm"]:
        await tgt(client, f"am force-stop {pkg} 2>/dev/null", retries=1)
        await asyncio.sleep(0.5)
    await tgt(client, "killall -9 com.google.android.gms com.google.android.gsf 2>/dev/null")
    await asyncio.sleep(3)

    # Atomic inode swap
    print("  Atomic swap...", flush=True)
    for db_name, dev_path in DB_MAP.items():
        # Clean sidecars
        await tgt(client, f"rm -f '{dev_path}-wal' '{dev_path}-shm' '{dev_path}-journal'")
        await asyncio.sleep(0.5)
        # Move old
        await tgt(client, f"mv '{dev_path}' '{dev_path}.old' 2>/dev/null")
        await asyncio.sleep(0.5)
        # Copy new
        out = await tgt(client, f"cp '{STAGING}/{db_name}' '{dev_path}' && echo OK")
        print(f"    {db_name}: cp={out}", flush=True)
        await asyncio.sleep(0.5)
        # Fix perms + SELinux
        await tgt(client,
            f"chown 1000:1000 '{dev_path}' && chmod 660 '{dev_path}' && "
            f"chcon u:object_r:system_data_file:s0 '{dev_path}'")
        await asyncio.sleep(0.5)
        # Verify
        out = await tgt(client, f"ls -laZ '{dev_path}'")
        print(f"    verify: {out}", flush=True)
        await asyncio.sleep(1)

    # Cleanup
    for dev_path in DB_MAP.values():
        await tgt(client, f"rm -f '{dev_path}.old'")

    # ══════════════════════════════════════════════════════════
    # PHASE 4: CLOUD-SAFE IDENTITY (IMEI/SIM only)
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 4] CLOUD-SAFE IDENTITY", flush=True)
    print(f"  Setting {len(SAFE_IDENTITY)} persist.sys.cloud.* props (NO fingerprint!)", flush=True)

    try:
        result = await client.modify_instance_properties([TARGET], SAFE_IDENTITY)
        print(f"  modifyInstanceProperties: code={result.get('code')}", flush=True)
    except Exception as e:
        print(f"  API error: {e} — falling back to setprop", flush=True)
        for k, v in SAFE_IDENTITY.items():
            await tgt(client, f'setprop {k} "{v}" 2>/dev/null')
            await asyncio.sleep(1)
    await asyncio.sleep(CMD_DELAY)

    # ══════════════════════════════════════════════════════════
    # PHASE 5: INSTALL 3RD PARTY APPS
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 5] INSTALL 3RD PARTY APPS", flush=True)

    # Get APK paths from neighbor
    APP_LIST = ["org.crape.rotationcontrol", "com.pawoints.curiouscat",
                "com.requapp.requ", "com.google.android.gm",
                "com.heypiggy.heypiggy", "com.apkpure.aegon"]

    apk_info = {}
    for pkg in APP_LIST:
        out = await nb_cmd(client, f"pm path {pkg} 2>/dev/null", timeout=8)
        if out:
            paths = [l.replace("package:", "").strip()
                     for l in out.split("\n") if "package:" in l]
            if paths:
                apk_info[pkg] = paths[0]  # Take base APK
                print(f"  {pkg}: {paths[0]}", flush=True)
        await asyncio.sleep(CMD_DELAY)

    # Transfer APKs: neighbor → launchpad → VPS → install on target
    installed = 0
    lp_ip = "10.12.11.186"
    apk_dir = VPS_DIR.parent / "apks"
    apk_dir.mkdir(parents=True, exist_ok=True)

    for pkg, apk_path in apk_info.items():
        port = 19300 + (hash(pkg) & 0xFF)
        local_apk = apk_dir / f"{pkg}.apk"
        local_apk.unlink(missing_ok=True)

        # Listen on VPS for APK
        def listen_apk(p, lp):
            try:
                subprocess.run(f"timeout 60 nc -l -p {p} > {lp}", shell=True, timeout=65)
            except Exception:
                pass

        t = threading.Thread(target=listen_apk, args=(port, str(local_apk)), daemon=True)
        t.start()
        await asyncio.sleep(1)

        # Start listener on launchpad that forwards to VPS
        await lp(client, f"pkill -f 'nc.*{port}' 2>/dev/null")
        await asyncio.sleep(1)

        # Neighbor → VPS directly (neighbor can reach VPS)
        await nb_cmd(client,
            f"cat {apk_path} | nc -w 15 {VPS_IP} {port}",
            timeout=30)
        await asyncio.sleep(5)
        t.join(timeout=15)

        if local_apk.exists() and local_apk.stat().st_size > 1000:
            apk_size = local_apk.stat().st_size
            print(f"  {pkg}: {apk_size / 1024:.0f}KB received", flush=True)

            # Move to served directory
            served = VPS_DIR.parent / f"{pkg}.apk"
            import shutil
            shutil.copy2(str(local_apk), str(served))

            # Try Cloud API install_app first
            app_url = f"http://{VPS_IP}:{VPS_HTTP_PORT}/{pkg}.apk"
            try:
                r = await client.install_app([TARGET], app_url)
                api_code = r.get("code")
                print(f"    install_app API: code={api_code}", flush=True)
                if api_code == 200:
                    installed += 1
                    await asyncio.sleep(10)  # Wait for install
                    continue
            except Exception as e:
                print(f"    install_app API failed: {e}", flush=True)

            # Fallback: curl + pm install
            out = await tgt(client,
                f"curl -s -o {STAGING}/{pkg}.apk {app_url} && "
                f"pm install -r -d -g {STAGING}/{pkg}.apk 2>&1",
                timeout=60)
            if out and "Success" in out:
                print(f"    ✓ {pkg} installed (pm)", flush=True)
                installed += 1
            else:
                print(f"    ✗ {pkg}: {(out or '')[:80]}", flush=True)
            await tgt(client, f"rm -f {STAGING}/{pkg}.apk")
        else:
            apk_size = local_apk.stat().st_size if local_apk.exists() else 0
            print(f"  ✗ {pkg}: transfer failed ({apk_size}B)", flush=True)

        await asyncio.sleep(CMD_DELAY)

    print(f"  Installed: {installed}/{len(apk_info)}", flush=True)

    # ══════════════════════════════════════════════════════════
    # PHASE 6: INJECT APP SIGN-IN STATE
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 6] INJECT APP SIGN-IN STATE", flush=True)
    primary = ACCOUNTS[0]
    email = primary["email"]
    dn = primary["display_name"]
    android_id = "b091558a075000c4"  # From neighbor
    gaia_id = str(secrets.randbits(64))
    checkin_ts = str(int(time.time() * 1000))
    device_id = str(secrets.randbits(52))

    def mk_xml(data):
        lines = ["<?xml version='1.0' encoding='utf-8' standalone='yes' ?>", "<map>"]
        for k, v in data.items():
            sv = str(v)
            if sv.lower() in ("true", "false"):
                lines.append(f'    <boolean name="{k}" value="{sv.lower()}" />')
            elif sv.isdigit() and len(sv) < 18:
                lines.append(f'    <long name="{k}" value="{sv}" />')
            else:
                lines.append(f'    <string name="{k}">{sv}</string>')
        lines.append("</map>")
        return "\n".join(lines)

    prefs = [
        ("/data/data/com.google.android.gms/shared_prefs/CheckinService.xml",
         "com.google.android.gms",
         {"lastCheckin": checkin_ts, "deviceId": device_id,
          "digest": secrets.token_hex(20), "versionInfo": "16.0"}),
        ("/data/data/com.google.android.gms/shared_prefs/GservicesSettings.xml",
         "com.google.android.gms",
         {"android_id": android_id, "checkin_device_id": device_id}),
        ("/data/data/com.android.vending/shared_prefs/finsky.xml",
         "com.android.vending",
         {"tos_accepted": "true", "setup_wizard_complete": "true",
          "account": email, "first_account_name": email}),
        ("/data/data/com.google.android.gm/shared_prefs/Gmail.xml",
         "com.google.android.gm",
         {"account_name": email, "notifications_enabled": "true"}),
    ]

    for remote_path, pkg, data in prefs:
        xml = mk_xml(data)
        # Write XML via echo commands
        prefs_dir = os.path.dirname(remote_path)
        await tgt(client, f"mkdir -p '{prefs_dir}'")
        await asyncio.sleep(0.5)

        # Escape for shell
        safe_xml = xml.replace("'", "'\\''")
        out = await tgt(client,
            f"echo '{safe_xml}' > '{remote_path}' && echo XML_OK",
            timeout=15)
        if out and "XML_OK" in out:
            # Fix ownership
            await tgt(client,
                f"chown $(stat -c %u /data/data/{pkg} 2>/dev/null || echo 1000):"
                f"$(stat -c %g /data/data/{pkg} 2>/dev/null || echo 1000) "
                f"'{remote_path}' && chmod 660 '{remote_path}'")
            print(f"  ✓ {os.path.basename(remote_path)}", flush=True)
        else:
            print(f"  ✗ {os.path.basename(remote_path)}: {out}", flush=True)
        await asyncio.sleep(CMD_DELAY)

    # ══════════════════════════════════════════════════════════
    # PHASE 7: SETTINGS + TIMEZONE
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 7] SETTINGS + TIMEZONE", flush=True)

    settings = [
        "settings put system time_12_24 24",
        "settings put global auto_time 0",
        "settings put global auto_time_zone 0",
        "setprop persist.sys.timezone Europe/London",
        "settings put secure default_input_method com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME",
    ]
    for s in settings:
        out = await tgt(client, s, retries=1)
        label = s.split()[-1] if len(s.split()) > 3 else s
        print(f"  {label}: {out if out else 'OK'}", flush=True)
        await asyncio.sleep(1)

    # ══════════════════════════════════════════════════════════
    # PHASE 8: RESTART + VERIFY
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 8] RESTART + VERIFY", flush=True)

    # Pre-restart WAL check
    out = await tgt(client,
        "ls /data/system_ce/0/accounts_ce.db-wal 2>/dev/null && echo HAS_WAL || echo SAFE")
    print(f"  WAL check: {out}", flush=True)

    # Restart
    try:
        r = await client.instance_restart([TARGET])
        print(f"  Restart: code={r.get('code')}", flush=True)
    except Exception as e:
        print(f"  Restart error: {e}", flush=True)

    print("  Waiting for reboot...", flush=True)
    await asyncio.sleep(45)

    alive = False
    for i in range(20):
        out = await tgt(client, "echo ALIVE", retries=1, timeout=10)
        if out and "ALIVE" in out:
            print(f"  ALIVE after {i * 8 + 45}s", flush=True)
            alive = True
            break
        try:
            r = await client.instance_list()
            for d in r.get("data", {}).get("pageData", []):
                if d.get("padCode") == TARGET:
                    s = d.get("padStatus")
                    if s == 14:
                        print(f"  CRASH status=14!", flush=True)
                        await client.close()
                        return
                    if s != 10:
                        print(f"  [{i * 8 + 45}s] status={s}", flush=True)
        except Exception:
            pass
        await asyncio.sleep(8)

    if not alive:
        print("  Target not responding!", flush=True)
        await client.close()
        return

    await asyncio.sleep(8)

    # ═══ VERIFICATION ═══
    print(f"\n{'=' * 70}", flush=True)
    print("  VERIFICATION", flush=True)
    print(f"{'=' * 70}", flush=True)

    # Accounts
    out = await tgt(client,
        "dumpsys account 2>/dev/null | head -20")
    if out:
        for line in out.split("\n")[:20]:
            print(f"    {line}", flush=True)
    await asyncio.sleep(CMD_DELAY)

    # Identity
    out = await tgt(client, "getprop ro.product.model")
    print(f"\n  Model: {out}", flush=True)
    out = await tgt(client, "getprop persist.sys.cloud.imeinum")
    print(f"  IMEI: {out}", flush=True)
    await asyncio.sleep(CMD_DELAY)

    # Apps
    out = await tgt(client, "pm list packages -3 2>/dev/null | wc -l")
    print(f"  3rd party apps: {out}", flush=True)
    await asyncio.sleep(CMD_DELAY)

    # DB health
    for db in ["/data/system_ce/0/accounts_ce.db", "/data/system_de/0/accounts_de.db"]:
        out = await tgt(client, f"ls -laZ {db}")
        print(f"  {db.split('/')[-1]}: {out}", flush=True)
        out = await tgt(client, f"ls {db}-wal 2>/dev/null && echo HAS_WAL || echo NO_WAL")
        print(f"    sidecar: {out}", flush=True)
        await asyncio.sleep(1)

    # System health
    out = await tgt(client, "pidof system_server")
    print(f"\n  system_server PID: {out}", flush=True)
    out = await tgt(client, "uptime")
    print(f"  uptime: {out}", flush=True)
    await asyncio.sleep(CMD_DELAY)

    # SQLite errors
    out = await tgt(client,
        "logcat -d -t 50 2>/dev/null | grep -iE 'SQLite.*Error|IOERR' | tail -5")
    if out and out.strip():
        print(f"  SQLite errors: {out}", flush=True)
    else:
        print(f"  SQLite: CLEAN", flush=True)

    # Timezone
    out = await tgt(client, "getprop persist.sys.timezone")
    print(f"  Timezone: {out}", flush=True)

    elapsed = time.time() - t0
    print(f"\n{'=' * 70}", flush=True)
    print(f"  CLONE v8 COMPLETE — {elapsed:.0f}s", flush=True)
    print(f"  Target: {TARGET}", flush=True)
    print(f"  Identity: IMEI={SAFE_IDENTITY['persist.sys.cloud.imeinum']}", flush=True)
    print(f"  Accounts: {', '.join(a['email'] for a in ACCOUNTS)}", flush=True)
    print(f"  GMS UID: {GMS_UID} (correct)", flush=True)
    print(f"  DB mode: Pull-Modify-Push native + DELETE journal", flush=True)
    print(f"{'=' * 70}", flush=True)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
