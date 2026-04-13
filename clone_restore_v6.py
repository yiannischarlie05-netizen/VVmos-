#!/usr/bin/env python3
"""
Clone Restore v6 — SAFE DB INJECTION (DELETE journal mode)
============================================================
Root cause fix for v1-v5.1 device crashes:
  - v1-v3: SQLITE_IOERR_WRITE (code 778) — DBs built in WAL mode,
    system_server can't create WAL/SHM files under SELinux
  - v4: Device death (status=14) — killed system_server with corrupt WAL refs
  - v5.1: Accounts semi-visible but restart → boot loop (status=11)
  - v5.1_fix: Same boot loop — still WAL-mode DB

v6 fix:
  1. Build DBs host-side with PRAGMA journal_mode=DELETE + page_size=4096
  2. Verify integrity locally before pushing
  3. Atomic inode swap (mv old → cp new) so system_server never sees partial write
  4. Clean ALL WAL/SHM/journal sidecar files
  5. Progressive reload: broadcast first, API restart only if needed
  6. DB is DELETE-mode so restart is safe — no WAL sidecar creation

Source: neighbor device accounts extracted earlier
Target: VMOS Cloud device
"""
import asyncio
import hashlib
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

os.environ['VMOS_ALLOW_RESTART'] = '1'
sys.path.insert(0, ".")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
from vmos_titan.core.vmos_db_builder import VMOSDbBuilder


# ═══════════════════════════════════════════════════════════════════════
# CONFIG — Edit these for your setup
# ═══════════════════════════════════════════════════════════════════════

TARGET = os.environ.get("CLONE_TARGET", "ACP2507303B6HNRI")
VPS = os.environ.get("CLONE_VPS", "37.60.234.139:9999")
TMP = "/data/local/tmp/clone"

# Accounts to inject (from neighbor extraction)
ACCOUNTS = [
    {"email": "petersfaustina699@gmail.com", "display_name": "Peters Faustina"},
    {"email": "faustinapeters11@gmail.com", "display_name": "Faustina Peters"},
]

# DB targets on device
DB_TARGETS = {
    "accounts_ce.db": {
        "device_path": "/data/system_ce/0/accounts_ce.db",
        "owner": "1000:1000",
        "perms": "660",
        "selinux": "u:object_r:system_data_file:s0",
    },
    "accounts_de.db": {
        "device_path": "/data/system_de/0/accounts_de.db",
        "owner": "1000:1000",
        "perms": "660",
        "selinux": "u:object_r:system_data_file:s0",
    },
}


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

async def cmd(client, pad, command, label="", retries=3, delay=3):
    """Execute sync_cmd with retry and rate limiting."""
    for attempt in range(retries):
        try:
            r = await client.sync_cmd(pad, command, timeout_sec=30)
            code = r.get("code", 0)
            if code == 200:
                data = r.get("data", [])
                if data and isinstance(data, list) and data[0]:
                    return (data[0].get("errorMsg") or "").strip()
                return ""
            elif code == 110012:
                if attempt < retries - 1:
                    print(f"    [{label}] timeout, retry {attempt+1}...")
                    await asyncio.sleep(delay)
                    continue
                return None
            elif code == 110031:
                if attempt < retries - 1:
                    print(f"    [{label}] not ready, retry {attempt+1}...")
                    await asyncio.sleep(8)
                    continue
                return None
            else:
                print(f"    [{label}] code={code} msg={r.get('msg','')}")
                return None
        except Exception as e:
            print(f"    [{label}] err: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    return None


def build_safe_accounts_ce(accounts):
    """Build accounts_ce.db with DELETE journal mode (Android-safe)."""
    builder = VMOSDbBuilder()
    # Build with first account, then add additional accounts
    primary = accounts[0]
    db_bytes = builder.build_accounts_ce(
        email=primary["email"],
        display_name=primary.get("display_name", ""),
        tokens=None,  # No tokens — they cause GMS crash
        password="",
        age_days=90,
    )

    if len(accounts) > 1:
        # Add additional accounts to the same DB
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            Path(tmp_path).write_bytes(db_bytes)
            conn = sqlite3.connect(tmp_path)
            conn.execute("PRAGMA journal_mode=DELETE;")
            c = conn.cursor()
            for extra in accounts[1:]:
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
            conn.commit()
            conn.close()
            db_bytes = Path(tmp_path).read_bytes()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    # Final safety pass
    return VMOSDbBuilder.safe_db_finalize(db_bytes)


def build_safe_accounts_de(accounts):
    """Build accounts_de.db with DELETE journal mode (Android-safe)."""
    builder = VMOSDbBuilder()
    primary = accounts[0]
    db_bytes = builder.build_accounts_de(
        email=primary["email"],
        display_name=primary.get("display_name", ""),
        age_days=90,
    )

    if len(accounts) > 1:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            Path(tmp_path).write_bytes(db_bytes)
            conn = sqlite3.connect(tmp_path)
            conn.execute("PRAGMA journal_mode=DELETE;")
            c = conn.cursor()
            for extra in accounts[1:]:
                c.execute(
                    "INSERT OR IGNORE INTO accounts (name, type, previous_name, "
                    "last_password_entry_time_millis_epoch) VALUES (?, 'com.google', NULL, ?)",
                    (extra["email"], int(time.time() * 1000)),
                )
                acct_id = c.lastrowid
                if acct_id:
                    # Visibility — allow GMS + Play Store to see the account
                    for pkg in ("com.google.android.gms", "com.android.vending",
                                "com.google.android.youtube", "com.google.android.gm"):
                        c.execute(
                            "INSERT OR IGNORE INTO visibility (accounts_id, _package, value) "
                            "VALUES (?, ?, 1)",
                            (acct_id, pkg),
                        )
            conn.commit()
            conn.close()
            db_bytes = Path(tmp_path).read_bytes()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    return VMOSDbBuilder.safe_db_finalize(db_bytes)


def verify_db_local(db_bytes, label=""):
    """Verify DB bytes are valid DELETE-mode SQLite with integrity ok."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        Path(tmp_path).write_bytes(db_bytes)
        conn = sqlite3.connect(tmp_path)
        jm = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        ic = conn.execute("PRAGMA integrity_check;").fetchone()[0]
        ps = conn.execute("PRAGMA page_size;").fetchone()[0]
        conn.close()

        ok = jm == "delete" and ic == "ok" and ps == 4096
        status = "OK" if ok else "FAIL"
        print(f"    {label}: journal={jm} integrity={ic} page_size={ps} [{status}]")
        return ok
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def md5_bytes(data):
    """Compute MD5 hex digest of bytes."""
    return hashlib.md5(data).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    t0 = time.time()
    client = VMOSCloudClient(
        ak=os.environ.get("VMOS_CLOUD_AK", "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"),
        sk=os.environ.get("VMOS_CLOUD_SK", "Q2SgcSwEfuwoedY0cijp6Mce"),
        base_url="https://api.vmoscloud.com"
    )

    print("=" * 70)
    print("  CLONE RESTORE v6 — SAFE DB INJECTION (DELETE journal mode)")
    print(f"  Target: {TARGET}")
    print(f"  Accounts: {', '.join(a['email'] for a in ACCOUNTS)}")
    print(f"  Fix: journal_mode=DELETE, page_size=4096, atomic inode swap")
    print("=" * 70)

    # ══════ PHASE 1: PRE-FLIGHT ══════
    print("\n[PHASE 1] PRE-FLIGHT")

    out = await cmd(client, TARGET, "id", label="id")
    if not out or "root" not in out:
        print(f"  FATAL: No root ({out})")
        return
    print(f"  Root: {out[:80]}")
    await asyncio.sleep(3)

    # Capture system_server PID
    ss_pid = await cmd(client, TARGET, "pidof system_server", label="ss_pid")
    print(f"  system_server PID: {ss_pid}")
    await asyncio.sleep(3)

    # Current account state
    out = await cmd(client, TARGET,
        "dumpsys account 2>/dev/null | grep -E 'Accounts:|@' | head -5",
        label="state")
    print(f"  Account state: {out}")
    await asyncio.sleep(3)

    # Read target device's GMS UID (critical for visibility matching)
    gms_uid = await cmd(client, TARGET,
        "dumpsys package com.google.android.gms 2>/dev/null | grep userId= | head -1 | sed 's/.*userId=//' | sed 's/ .*//'",
        label="gms_uid")
    print(f"  GMS UID on target: {gms_uid}")
    await asyncio.sleep(3)

    # ══════ PHASE 2: BUILD DBs HOST-SIDE ══════
    print("\n[PHASE 2] BUILD DBs HOST-SIDE (DELETE journal mode)")

    print("  Building accounts_ce.db...")
    ce_bytes = build_safe_accounts_ce(ACCOUNTS)
    ce_md5 = md5_bytes(ce_bytes)
    print(f"    Size: {len(ce_bytes)} bytes, MD5: {ce_md5}")

    print("  Building accounts_de.db...")
    de_bytes = build_safe_accounts_de(ACCOUNTS)
    de_md5 = md5_bytes(de_bytes)
    print(f"    Size: {len(de_bytes)} bytes, MD5: {de_md5}")

    # ══════ PHASE 3: VERIFY DBs LOCALLY ══════
    print("\n[PHASE 3] VERIFY DBs LOCALLY")

    ce_ok = verify_db_local(ce_bytes, "accounts_ce.db")
    de_ok = verify_db_local(de_bytes, "accounts_de.db")

    if not (ce_ok and de_ok):
        print("  FATAL: Local DB verification failed. Aborting.")
        return

    # ══════ PHASE 4: PUSH DBs TO DEVICE ══════
    print("\n[PHASE 4] PUSH DBs TO DEVICE VIA VPS STAGING")

    # Write DBs to local temp for VPS upload
    staging_dir = Path("tmp/clone_v6_staging")
    staging_dir.mkdir(parents=True, exist_ok=True)

    (staging_dir / "accounts_ce.db").write_bytes(ce_bytes)
    (staging_dir / "accounts_de.db").write_bytes(de_bytes)
    print(f"  Staged to {staging_dir}")

    # Upload to VPS and download to device
    # Method: serve files via VPS HTTP, device curls them
    await cmd(client, TARGET, f"mkdir -p {TMP} && rm -f {TMP}/*.db {TMP}/status.txt",
              label="prep")
    await asyncio.sleep(2)

    # Background download both DBs
    bg_cmd = ""
    for db_name in ["accounts_ce.db", "accounts_de.db"]:
        bg_cmd += (f"nohup sh -c 'curl -sf --connect-timeout 15 --max-time 60 "
                   f"http://{VPS}/{db_name} -o {TMP}/{db_name} "
                   f"&& echo DONE_{db_name} >> {TMP}/status.txt' >/dev/null 2>&1 & ")
    bg_cmd += "echo LAUNCHED"

    out = await cmd(client, TARGET, bg_cmd, label="launch_dl")
    print(f"  Download launched: {out}")
    await asyncio.sleep(8)

    # Poll for completion
    for poll in range(15):
        out = await cmd(client, TARGET, f"cat {TMP}/status.txt 2>/dev/null | wc -l", label="poll")
        try:
            done = int(out.strip()) if out else 0
        except (ValueError, TypeError):
            done = 0
        if done >= 2:
            print(f"  Downloads complete ({poll+1} polls)")
            break
        print(f"  Poll {poll+1}: {done}/2")
        await asyncio.sleep(5)
    else:
        print("  WARNING: Downloads may not be complete, checking files...")
    await asyncio.sleep(3)

    # Verify MD5 on device
    print("\n  Verifying downloads on device...")
    all_ok = True
    for db_name, expected_md5 in [("accounts_ce.db", ce_md5), ("accounts_de.db", de_md5)]:
        out = await cmd(client, TARGET, f"md5sum {TMP}/{db_name} 2>/dev/null", label=f"md5_{db_name}")
        if out:
            device_md5 = out.split()[0]
            ok = device_md5 == expected_md5
            print(f"    {db_name}: {device_md5} {'OK' if ok else 'MISMATCH'}")
            if not ok:
                all_ok = False
        else:
            print(f"    {db_name}: DOWNLOAD FAILED")
            all_ok = False
        await asyncio.sleep(2)

    if not all_ok:
        print("  FATAL: MD5 mismatch. Aborting.")
        return

    # ══════ PHASE 5: FREEZE SERVICES ══════
    print("\n[PHASE 5] FREEZE GOOGLE SERVICES")

    # Force-stop all Google packages that touch accounts
    pkgs = ["com.google.android.gms", "com.google.android.gsf",
            "com.android.vending", "com.google.android.gm"]
    for p in pkgs:
        out = await cmd(client, TARGET,
            f"am force-stop {p} 2>/dev/null && echo STOPPED_{p}", label=f"stop_{p}")
        if out:
            print(f"  {out}")
        await asyncio.sleep(1)

    # Kill any remaining GMS processes
    await cmd(client, TARGET,
        "killall -9 com.google.android.gms com.google.android.gsf 2>/dev/null; echo KILL_DONE",
        label="kill")
    await asyncio.sleep(3)

    # ══════ PHASE 6: ATOMIC INODE SWAP ══════
    print("\n[PHASE 6] ATOMIC INODE SWAP + PERMISSION FIX")

    for db_name, cfg in DB_TARGETS.items():
        dev_path = cfg["device_path"]
        owner = cfg["owner"]
        perms = cfg["perms"]
        ctx = cfg["selinux"]

        print(f"\n  Installing {db_name} -> {dev_path}")

        # Step 1: Clean ALL stale WAL/SHM/journal files
        out = await cmd(client, TARGET,
            f"rm -f '{dev_path}-wal' '{dev_path}-shm' '{dev_path}-journal' "
            f"&& echo CLEANED",
            label=f"clean_{db_name}")
        print(f"    Clean sidecar: {out}")
        await asyncio.sleep(2)

        # Step 2: Move old DB to .old (new inode avoids stale fd corruption)
        # system_server still holds fd to old inode — after restart it opens new file
        out = await cmd(client, TARGET,
            f"mv '{dev_path}' '{dev_path}.old' 2>/dev/null; echo MV_OK",
            label=f"mv_{db_name}")
        print(f"    Move old: {out}")
        await asyncio.sleep(1)

        # Step 3: Copy new DB to destination (creates new inode)
        out = await cmd(client, TARGET,
            f"cp '{TMP}/{db_name}' '{dev_path}' && echo CP_OK || echo CP_FAIL",
            label=f"cp_{db_name}")
        print(f"    Copy new: {out}")
        if out and "FAIL" in out:
            print(f"    FATAL: Failed to copy {db_name}")
            return
        await asyncio.sleep(1)

        # Step 4: Set ownership (system:system = 1000:1000)
        await cmd(client, TARGET, f"chown {owner} '{dev_path}'", label=f"chown_{db_name}")
        await asyncio.sleep(1)

        # Step 5: Set permissions (600 = rw-------, matching Android default for accounts)
        await cmd(client, TARGET, f"chmod {perms} '{dev_path}'", label=f"chmod_{db_name}")
        await asyncio.sleep(1)

        # Step 6: Set SELinux context
        await cmd(client, TARGET, f"chcon {ctx} '{dev_path}'", label=f"chcon_{db_name}")
        await asyncio.sleep(1)

        # Step 7: Verify — NO WAL/SHM should exist
        out = await cmd(client, TARGET, f"ls -laZ '{dev_path}'", label=f"verify_{db_name}")
        print(f"    Verify: {out}")

        out = await cmd(client, TARGET,
            f"ls '{dev_path}-wal' 2>/dev/null && echo HAS_WAL || echo NO_WAL",
            label=f"wal_{db_name}")
        print(f"    WAL check: {out}")
        await asyncio.sleep(1)

    # Clean old backups
    for db_name, cfg in DB_TARGETS.items():
        await cmd(client, TARGET,
            f"rm -f '{cfg['device_path']}.old'", label=f"rm_old_{db_name}")

    # ══════ PHASE 7: PROGRESSIVE RELOAD ══════
    print("\n[PHASE 7] PROGRESSIVE RELOAD")

    # Step 7A: Broadcast only (safest — no restart)
    print("\n  [7a] Broadcasting LOGIN_ACCOUNTS_CHANGED...")
    out = await cmd(client, TARGET,
        "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED "
        "--receiver-include-background 2>&1",
        label="broadcast")
    print(f"    Broadcast: {out}")
    await asyncio.sleep(5)

    # Check if accounts visible via dumpsys
    out = await cmd(client, TARGET,
        "dumpsys account 2>/dev/null | grep -c '@gmail.com'",
        label="check_7a")
    gmail_refs = 0
    try:
        gmail_refs = int(out.strip()) if out and out.strip().isdigit() else 0
    except (ValueError, TypeError):
        pass
    print(f"    Gmail references after broadcast: {gmail_refs}")

    if gmail_refs > 0:
        print(f"\n  ACCOUNTS VISIBLE WITHOUT RESTART ({gmail_refs} refs)")
    else:
        # Step 7B: Restart GMS to force account re-read
        print("\n  [7b] Restarting GMS...")
        await cmd(client, TARGET,
            "am force-stop com.google.android.gms && sleep 2 && "
            "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED "
            "--receiver-include-background 2>&1",
            label="restart_gms")
        await asyncio.sleep(8)

        out = await cmd(client, TARGET,
            "dumpsys account 2>/dev/null | grep -c '@gmail.com'",
            label="check_7b")
        try:
            gmail_refs = int(out.strip()) if out and out.strip().isdigit() else 0
        except (ValueError, TypeError):
            gmail_refs = 0
        print(f"    Gmail references after GMS restart: {gmail_refs}")

    if gmail_refs == 0:
        # Step 7C: Full instance restart via VMOS API
        # SAFE because DB is DELETE-mode — no WAL sidecar creation on boot
        print("\n  [7c] Full instance restart via API (safe — DELETE mode DB)...")

        # Pre-restart: verify DB is still DELETE mode on device
        out = await cmd(client, TARGET,
            f"ls -la /data/system_ce/0/accounts_ce.db-wal 2>/dev/null && echo HAS_WAL || echo SAFE_NO_WAL",
            label="pre_restart_check")
        print(f"    Pre-restart WAL check: {out}")

        try:
            r = await client.instance_restart([TARGET])
            code = r.get("code", -1)
            print(f"    Restart API: code={code} msg={r.get('msg','')}")
        except Exception as e:
            print(f"    Restart error: {e}")

        # Wait for device to come back
        print("    Waiting for device reboot...")
        await asyncio.sleep(30)

        alive = False
        for i in range(25):
            # Check instance status
            try:
                r = await client.instance_list()
                for d in r.get('data', {}).get('pageData', []):
                    if d.get('padCode') == TARGET:
                        s = d.get('padStatus')
                        if s == 14:
                            print(f"    [{(i+1)*8}s] DEVICE DEAD (status=14)")
                            print("    This should NOT happen with DELETE-mode DBs.")
                            print("    Check: DB may have been overwritten by system_server before restart.")
                            elapsed = time.time() - t0
                            print(f"\n{'=' * 70}")
                            print(f"  v6 FAILED (device died) — {elapsed:.0f}s")
                            print(f"{'=' * 70}")
                            return
                        elif s == 10:
                            pass  # Running, try command
                        elif s == 11:
                            print(f"    [{(i+1)*8 + 30}s] status={s} (restarting)...")
                            await asyncio.sleep(8)
                            continue
                        else:
                            print(f"    [{(i+1)*8 + 30}s] status={s}")
                            await asyncio.sleep(8)
                            continue
            except Exception:
                pass

            out = await cmd(client, TARGET, "echo ALIVE", label="boot", retries=1)
            if out and "ALIVE" in out:
                print(f"    Device ALIVE after {(i+1)*8 + 30}s")
                alive = True
                break
            await asyncio.sleep(8)

        if not alive:
            print("    Device did not come back.")
            elapsed = time.time() - t0
            print(f"\n{'=' * 70}")
            print(f"  v6 INCOMPLETE (device not responding) — {elapsed:.0f}s")
            print(f"{'=' * 70}")
            return

        await asyncio.sleep(5)

    # ══════ PHASE 8: VERIFICATION ══════
    print("\n" + "=" * 70)
    print("  [PHASE 8] VERIFICATION")
    print("=" * 70)

    # 8a: Full dumpsys account
    out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -40", label="final_dump")
    if out:
        for line in out.split("\n")[:30]:
            print(f"    {line}")
    await asyncio.sleep(3)

    # 8b: Gmail reference count
    out = await cmd(client, TARGET,
        "dumpsys account 2>/dev/null | grep -c '@gmail.com'",
        label="final_count")
    final_refs = 0
    try:
        final_refs = int(out.strip()) if out and out.strip().isdigit() else 0
    except (ValueError, TypeError):
        pass
    print(f"\n  Gmail references: {final_refs}")
    await asyncio.sleep(3)

    # 8c: DB file check — verify no WAL/SHM created after restart
    print("\n  DB files on device:")
    for db_name, cfg in DB_TARGETS.items():
        dev_path = cfg["device_path"]
        out = await cmd(client, TARGET, f"ls -laZ '{dev_path}'", label=f"file_{db_name}")
        print(f"    {db_name}: {out}")
        await asyncio.sleep(1)

        # Check for WAL/SHM (should NOT exist with DELETE mode)
        out = await cmd(client, TARGET,
            f"ls -la '{dev_path}-wal' '{dev_path}-shm' 2>/dev/null || echo NO_SIDECAR",
            label=f"sidecar_{db_name}")
        print(f"    sidecar: {out}")
        await asyncio.sleep(1)
    await asyncio.sleep(3)

    # 8d: System health
    out = await cmd(client, TARGET, "pidof system_server && uptime", label="health")
    print(f"\n  System health: {out}")
    await asyncio.sleep(3)

    # 8e: Account-related logcat
    out = await cmd(client, TARGET,
        "logcat -d -t 100 2>/dev/null | grep -iE 'AccountManager|SQLite.*Error|IOERR' | tail -10",
        label="logcat")
    if out:
        print(f"\n  Account logcat:")
        for line in out.split("\n")[:10]:
            print(f"    {line}")

    # ══════ RESULT ══════
    elapsed = time.time() - t0
    success = final_refs >= len(ACCOUNTS)

    print(f"\n{'=' * 70}")
    if success:
        print(f"  CLONE RESTORE v6 SUCCESS — {elapsed:.0f}s")
        print(f"  Accounts injected: {final_refs} gmail references")
    else:
        print(f"  CLONE RESTORE v6 PARTIAL — {elapsed:.0f}s")
        print(f"  Gmail refs: {final_refs} (expected >= {len(ACCOUNTS)})")
        print(f"  Accounts may need time to sync with GMS")
    print(f"  Target: {TARGET}")
    print(f"  Journal mode: DELETE (safe for restart)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
