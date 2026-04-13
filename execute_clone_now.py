#!/usr/bin/env python3
"""
Execute Clone NOW — Direct DB injection via Cloud API
=====================================================
Self-contained: builds DBs, pushes via base64/syncCmd, installs, verifies.
No VPS, no ADB bridge needed.

Source:  neighbor 10.12.21.175 (VMOS Cloud device, same platform)
Target:  ACP2507303B6HNRI (freshly reset)
Fix:     DELETE journal mode + system_data_file SELinux context
"""
import asyncio
import base64
import hashlib
import os
import sys
import time

os.environ['VMOS_ALLOW_RESTART'] = '1'
sys.path.insert(0, ".")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
from vmos_titan.core.vmos_db_builder import VMOSDbBuilder

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

TARGET = "ACP2507303B6HNRI"

ACCOUNTS = [
    {"email": "petersfaustina699@gmail.com", "display_name": "Peters Faustina"},
    {"email": "faustinapeters11@gmail.com", "display_name": "Faustina Peters"},
]

# DB targets — SELinux context matches VMOS Cloud native (system_data_file, NOT accounts_data_file)
DB_TARGETS = {
    "accounts_ce.db": {
        "path": "/data/system_ce/0/accounts_ce.db",
        "owner": "1000:1000",
        "perms": "660",
        "ctx": "u:object_r:system_data_file:s0",
    },
    "accounts_de.db": {
        "path": "/data/system_de/0/accounts_de.db",
        "owner": "1000:1000",
        "perms": "660",
        "ctx": "u:object_r:system_data_file:s0",
    },
}

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
TMP = "/data/local/tmp/clone"
API_DELAY = 3.0


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

async def cmd(client, pad, command, label="", retries=3, delay=3, timeout=30):
    """Execute sync_cmd with retry."""
    for attempt in range(retries):
        try:
            r = await client.sync_cmd(pad, command, timeout_sec=timeout)
            code = r.get("code", 0)
            if code == 200:
                data = r.get("data", [])
                if data and isinstance(data, list) and data[0]:
                    return (data[0].get("errorMsg") or "").strip()
                return ""
            elif code in (110012, 110031):
                if attempt < retries - 1:
                    await asyncio.sleep(delay if code == 110012 else 8)
                    continue
                return None
            else:
                return None
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    return None


async def push_bytes_b64(client, pad, data: bytes, remote_path: str, label: str = ""):
    """Push raw bytes to device via base64 chunks through syncCmd."""
    b64 = base64.b64encode(data).decode()
    chunk_size = 2500  # Safe for syncCmd
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

    # Clear target
    await cmd(client, pad, f"rm -f {remote_path}.b64 {remote_path}", label=f"clear_{label}")
    await asyncio.sleep(1)

    # Push chunks
    for ci, chunk in enumerate(chunks):
        op = ">>" if ci > 0 else ">"
        out = await cmd(client, pad, f'echo -n "{chunk}" {op} {remote_path}.b64',
                       label=f"chunk_{ci}", retries=2, timeout=10)
        await asyncio.sleep(0.5)

    # Decode
    out = await cmd(client, pad,
        f"base64 -d {remote_path}.b64 > {remote_path} && rm -f {remote_path}.b64 && "
        f"wc -c < {remote_path}",
        label=f"decode_{label}", timeout=15)
    await asyncio.sleep(1)

    return out


def build_dbs():
    """Build DELETE-mode accounts DBs with safe finalization."""
    import sqlite3
    import tempfile
    from pathlib import Path

    builder = VMOSDbBuilder()
    primary = ACCOUNTS[0]

    # Build accounts_ce.db
    ce_bytes = builder.build_accounts_ce(
        email=primary["email"],
        display_name=primary.get("display_name", ""),
        tokens=None,
        password="",
        age_days=90,
    )

    # Build accounts_de.db
    de_bytes = builder.build_accounts_de(
        email=primary["email"],
        display_name=primary.get("display_name", ""),
        age_days=90,
    )

    # Add additional accounts
    for extra in ACCOUNTS[1:]:
        for label, db_bytes_ref in [("ce", [ce_bytes]), ("de", [de_bytes])]:
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                Path(tmp_path).write_bytes(db_bytes_ref[0])
                conn = sqlite3.connect(tmp_path)
                conn.execute("PRAGMA journal_mode=DELETE;")
                c = conn.cursor()

                if label == "ce":
                    c.execute(
                        "INSERT OR IGNORE INTO accounts (name, type, password) VALUES (?, 'com.google', '')",
                        (extra["email"],),
                    )
                    acct_id = c.lastrowid
                    if acct_id:
                        dn = extra.get("display_name", extra["email"].split("@")[0])
                        parts = dn.split()
                        for key, val in [("display_name", dn),
                                         ("given_name", parts[0] if parts else ""),
                                         ("family_name", parts[-1] if len(parts) > 1 else "")]:
                            c.execute(
                                "INSERT OR IGNORE INTO extras (accounts_id, key, value) VALUES (?, ?, ?)",
                                (acct_id, key, val),
                            )
                else:
                    c.execute(
                        "INSERT OR IGNORE INTO accounts (name, type, previous_name, "
                        "last_password_entry_time_millis_epoch) VALUES (?, 'com.google', NULL, ?)",
                        (extra["email"], int(time.time() * 1000)),
                    )
                    acct_id = c.lastrowid
                    if acct_id:
                        for pkg in ("com.google.android.gms", "com.android.vending",
                                    "com.google.android.youtube", "com.google.android.gm"):
                            c.execute(
                                "INSERT OR IGNORE INTO visibility (accounts_id, _package, value) VALUES (?, ?, 1)",
                                (acct_id, pkg),
                            )

                conn.commit()
                conn.close()
                db_bytes_ref[0] = Path(tmp_path).read_bytes()
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        ce_bytes = [ce_bytes] if not isinstance(ce_bytes, list) else ce_bytes
        de_bytes = [de_bytes] if not isinstance(de_bytes, list) else de_bytes
        # unwrap
        if isinstance(ce_bytes, list): ce_bytes = ce_bytes[0]
        if isinstance(de_bytes, list): de_bytes = de_bytes[0]

    # Final safety pass
    ce_bytes = VMOSDbBuilder.safe_db_finalize(ce_bytes)
    de_bytes = VMOSDbBuilder.safe_db_finalize(de_bytes)

    return ce_bytes, de_bytes


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    t0 = time.time()
    client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")

    print("=" * 70, flush=True)
    print("  EXECUTE CLONE — DIRECT DB INJECTION (v6 method)", flush=True)
    print(f"  Target:   {TARGET}", flush=True)
    print(f"  Accounts: {', '.join(a['email'] for a in ACCOUNTS)}", flush=True)
    print(f"  Fix:      journal_mode=DELETE, page_size=4096, system_data_file SELinux", flush=True)
    print("=" * 70, flush=True)

    # ══════ PHASE 1: PRE-FLIGHT ══════
    print("\n[PHASE 1] PRE-FLIGHT CHECK", flush=True)

    out = await cmd(client, TARGET, "id", label="id")
    if not out or "root" not in (out or ""):
        print(f"  No root: {out}", flush=True)
        print("  Enabling root...", flush=True)
        try:
            await client.switch_root([TARGET], enable=True)
            await asyncio.sleep(10)
        except:
            pass
        out = await cmd(client, TARGET, "id", label="id2")
    print(f"  ID: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | grep -E 'Accounts:|@' | head -3", label="accts")
    print(f"  Current accounts: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    # Read native SELinux context of accounts DB
    out = await cmd(client, TARGET, "ls -laZ /data/system_ce/0/accounts_ce.db", label="ctx")
    print(f"  Native DB context: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    # ══════ PHASE 2: BUILD DBs ══════
    print("\n[PHASE 2] BUILD DBs HOST-SIDE (DELETE journal mode)", flush=True)

    ce_bytes, de_bytes = build_dbs()
    ce_md5 = hashlib.md5(ce_bytes).hexdigest()
    de_md5 = hashlib.md5(de_bytes).hexdigest()
    print(f"  accounts_ce.db: {len(ce_bytes)} bytes, md5={ce_md5}", flush=True)
    print(f"  accounts_de.db: {len(de_bytes)} bytes, md5={de_md5}", flush=True)

    # Verify locally
    import sqlite3, tempfile
    from pathlib import Path
    for label, data in [("ce", ce_bytes), ("de", de_bytes)]:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            Path(tmp.name).write_bytes(data)
            conn = sqlite3.connect(tmp.name)
            jm = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            ic = conn.execute("PRAGMA integrity_check;").fetchone()[0]
            rows = conn.execute("SELECT name FROM accounts").fetchall()
            conn.close()
            Path(tmp.name).unlink()
            print(f"  {label}: journal={jm} integrity={ic} accounts={[r[0] for r in rows]}", flush=True)

    # ══════ PHASE 3: PUSH DBs VIA BASE64 ══════
    print("\n[PHASE 3] PUSH DBs TO DEVICE (base64 via syncCmd)", flush=True)

    await cmd(client, TARGET, f"mkdir -p {TMP}", label="mkdir")
    await asyncio.sleep(1)

    for db_name, db_data, expected_md5 in [
        ("accounts_ce.db", ce_bytes, ce_md5),
        ("accounts_de.db", de_bytes, de_md5),
    ]:
        remote = f"{TMP}/{db_name}"
        print(f"\n  Pushing {db_name} ({len(db_data)} bytes)...", flush=True)

        out = await push_bytes_b64(client, TARGET, db_data, remote, label=db_name)
        print(f"    Size on device: {out}", flush=True)
        await asyncio.sleep(2)

        # Verify MD5
        out = await cmd(client, TARGET, f"md5sum {remote} 2>/dev/null | cut -d' ' -f1", label=f"md5_{db_name}")
        ok = (out or "").strip() == expected_md5
        print(f"    MD5: {out} {'OK' if ok else 'MISMATCH!'}", flush=True)
        if not ok:
            print(f"    Expected: {expected_md5}", flush=True)
            print(f"    FATAL: DB integrity compromised during transfer", flush=True)
            return
        await asyncio.sleep(API_DELAY)

    # ══════ PHASE 4: FREEZE SERVICES ══════
    print("\n[PHASE 4] FREEZE GOOGLE SERVICES", flush=True)

    pkgs = ["com.google.android.gms", "com.google.android.gsf",
            "com.android.vending", "com.google.android.gm"]
    for p in pkgs:
        await cmd(client, TARGET, f"am force-stop {p} 2>/dev/null", label=f"stop_{p}", retries=1)
        await asyncio.sleep(0.5)

    await cmd(client, TARGET,
        "killall -9 com.google.android.gms com.google.android.gsf 2>/dev/null; echo K",
        label="kill")
    await asyncio.sleep(3)

    # ══════ PHASE 5: ATOMIC INODE SWAP ══════
    print("\n[PHASE 5] INSTALL DBs (atomic inode swap + perm fix)", flush=True)

    for db_name, cfg in DB_TARGETS.items():
        dev_path = cfg["path"]
        owner = cfg["owner"]
        perms = cfg["perms"]
        ctx = cfg["ctx"]

        print(f"\n  {db_name} → {dev_path}", flush=True)

        # Clean ALL sidecar files
        await cmd(client, TARGET,
            f"rm -f '{dev_path}-wal' '{dev_path}-shm' '{dev_path}-journal'",
            label=f"clean_{db_name}")
        await asyncio.sleep(1)

        # Move old DB (new inode avoids fd conflict)
        await cmd(client, TARGET, f"mv '{dev_path}' '{dev_path}.old' 2>/dev/null; echo mv_ok",
                  label=f"mv_{db_name}")
        await asyncio.sleep(1)

        # Copy new DB (creates fresh inode)
        out = await cmd(client, TARGET,
            f"cp '{TMP}/{db_name}' '{dev_path}' && echo CP_OK",
            label=f"cp_{db_name}")
        print(f"    Copy: {out}", flush=True)
        await asyncio.sleep(1)

        # Fix ownership, perms, SELinux
        await cmd(client, TARGET,
            f"chown {owner} '{dev_path}' && chmod {perms} '{dev_path}' && chcon {ctx} '{dev_path}'",
            label=f"perm_{db_name}")
        await asyncio.sleep(1)

        # Verify
        out = await cmd(client, TARGET, f"ls -laZ '{dev_path}'", label=f"verify_{db_name}")
        print(f"    Verify: {out}", flush=True)

        # Confirm no WAL sidecar
        out = await cmd(client, TARGET,
            f"ls '{dev_path}-wal' 2>/dev/null && echo HAS_WAL || echo NO_WAL",
            label=f"wal_{db_name}")
        print(f"    WAL: {out}", flush=True)
        await asyncio.sleep(1)

    # Remove old backups
    for db_name, cfg in DB_TARGETS.items():
        await cmd(client, TARGET, f"rm -f '{cfg['path']}.old'", label=f"rm_old_{db_name}")

    # ══════ PHASE 6: PROGRESSIVE RELOAD ══════
    print("\n[PHASE 6] PROGRESSIVE RELOAD", flush=True)

    # Step A: Broadcast only
    print("\n  [6a] Broadcasting LOGIN_ACCOUNTS_CHANGED...", flush=True)
    await cmd(client, TARGET,
        "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED "
        "--receiver-include-background 2>&1",
        label="broadcast")
    await asyncio.sleep(5)

    out = await cmd(client, TARGET,
        "dumpsys account 2>/dev/null | grep -c '@gmail.com'", label="check_6a")
    gmail_refs = 0
    try:
        gmail_refs = int((out or "0").strip())
    except (ValueError, TypeError):
        pass
    print(f"    Gmail refs after broadcast: {gmail_refs}", flush=True)

    if gmail_refs == 0:
        # Step B: Restart GMS
        print("\n  [6b] Restarting GMS...", flush=True)
        await cmd(client, TARGET,
            "am force-stop com.google.android.gms && sleep 2 && "
            "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED "
            "--receiver-include-background",
            label="gms_restart")
        await asyncio.sleep(8)

        out = await cmd(client, TARGET,
            "dumpsys account 2>/dev/null | grep -c '@gmail.com'", label="check_6b")
        try:
            gmail_refs = int((out or "0").strip())
        except (ValueError, TypeError):
            pass
        print(f"    Gmail refs after GMS restart: {gmail_refs}", flush=True)

    if gmail_refs == 0:
        # Step C: Full device restart (SAFE — DBs are DELETE mode)
        print("\n  [6c] Full restart (safe — DELETE mode DBs)...", flush=True)

        # Pre-restart: confirm no WAL
        out = await cmd(client, TARGET,
            "ls /data/system_ce/0/accounts_ce.db-wal 2>/dev/null && echo HAS_WAL || echo SAFE",
            label="pre_restart")
        print(f"    Pre-restart check: {out}", flush=True)

        try:
            r = await client.instance_restart([TARGET])
            print(f"    Restart: code={r.get('code')}", flush=True)
        except Exception as e:
            print(f"    Restart err: {e}", flush=True)

        print("    Waiting for reboot...", flush=True)
        await asyncio.sleep(35)

        alive = False
        for i in range(20):
            out = await cmd(client, TARGET, "echo ALIVE", label="boot", retries=1, timeout=10)
            if out and "ALIVE" in out:
                print(f"    Device ALIVE after {i*8+35}s", flush=True)
                alive = True
                break

            # Check status
            try:
                r = await client.instance_list()
                for d in r.get('data', {}).get('pageData', []):
                    if d.get('padCode') == TARGET:
                        s = d.get('padStatus')
                        if s == 14:
                            print(f"    DEVICE DEAD (status=14) — this should NOT happen with DELETE DBs", flush=True)
                            elapsed = time.time() - t0
                            print(f"\n{'='*70}\n  CLONE FAILED — {elapsed:.0f}s\n{'='*70}", flush=True)
                            await client.close()
                            return
                        elif s != 10:
                            print(f"    [{i*8+35}s] status={s}", flush=True)
            except:
                pass
            await asyncio.sleep(8)

        if not alive:
            print("    Device not responding after restart", flush=True)
            elapsed = time.time() - t0
            print(f"\n{'='*70}\n  CLONE INCOMPLETE — {elapsed:.0f}s\n{'='*70}", flush=True)
            await client.close()
            return

        await asyncio.sleep(5)

        out = await cmd(client, TARGET,
            "dumpsys account 2>/dev/null | grep -c '@gmail.com'", label="check_6c")
        try:
            gmail_refs = int((out or "0").strip())
        except (ValueError, TypeError):
            pass
        print(f"    Gmail refs after restart: {gmail_refs}", flush=True)

    # ══════ PHASE 7: VERIFICATION ══════
    print(f"\n{'='*70}", flush=True)
    print("  [PHASE 7] VERIFICATION", flush=True)
    print(f"{'='*70}", flush=True)

    # Full account dump
    out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -25", label="final_dump")
    if out:
        for line in (out or "").split("\n")[:20]:
            print(f"    {line}", flush=True)
    await asyncio.sleep(API_DELAY)

    # DB file state
    print("\n  DB files:", flush=True)
    for db_name, cfg in DB_TARGETS.items():
        out = await cmd(client, TARGET, f"ls -laZ '{cfg['path']}'", label=f"file_{db_name}")
        print(f"    {db_name}: {out}", flush=True)
        await asyncio.sleep(1)
        out = await cmd(client, TARGET,
            f"ls '{cfg['path']}-wal' '{cfg['path']}-shm' 2>/dev/null || echo NO_SIDECAR",
            label=f"sidecar_{db_name}")
        print(f"    sidecar: {out}", flush=True)
        await asyncio.sleep(1)

    # System health
    out = await cmd(client, TARGET, "pidof system_server && uptime", label="health")
    print(f"\n  System health: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    # Account logcat
    out = await cmd(client, TARGET,
        "logcat -d -t 50 2>/dev/null | grep -iE 'AccountManager|SQLite.*Error|IOERR' | tail -5",
        label="logcat")
    if out and out.strip():
        print(f"\n  Account logcat:", flush=True)
        for line in (out or "").split("\n")[:5]:
            print(f"    {line}", flush=True)
    else:
        print(f"\n  Account logcat: CLEAN (no errors)", flush=True)

    # ══════ RESULT ══════
    elapsed = time.time() - t0
    success = gmail_refs >= len(ACCOUNTS)

    print(f"\n{'='*70}", flush=True)
    if success:
        print(f"  CLONE SUCCESS — {elapsed:.0f}s", flush=True)
        print(f"  Accounts: {gmail_refs} gmail references", flush=True)
    else:
        print(f"  CLONE PARTIAL — {elapsed:.0f}s", flush=True)
        print(f"  Gmail refs: {gmail_refs} (expected >= {len(ACCOUNTS)})", flush=True)
    print(f"  Target: {TARGET}", flush=True)
    print(f"  Journal: DELETE | SELinux: system_data_file | Page: 4096", flush=True)
    print(f"{'='*70}", flush=True)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
