#!/usr/bin/env python3
"""
Clone Restore v4 — HYBRID DB INJECTION
=======================================
Instead of replacing DBs wholesale (which crashes system_server on boot),
this approach:
  1. Takes the FRESH target device's own accounts_ce.db + accounts_de.db
  2. INSERTs source account data INTO them (preserving all metadata/structure)
  3. Pushes these hybrid DBs (not foreign files)
  4. Kills system_server (NOT full device restart) to reload

This preserves:
  - Target DB header, page sizes, internal structures
  - Correct UID mappings (auth_uid_for_type:com.google → 10036)
  - Correct journal mode (DELETE, matching target)
  - All SQLite internal metadata

Source: 10.12.21.175 (SM-S9110)
  - petersfaustina699@gmail.com + faustinapeters11@gmail.com
  - 84 auth tokens, 221 extras
"""
import asyncio
import os
import sys
import time

os.environ['VMOS_ALLOW_RESTART'] = '1'
sys.path.insert(0, ".")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

TARGET = "ACP2504309PQ0CDL"
VPS = "37.60.234.139:9999"
TMP = "/data/local/tmp/clone"

# Only 2 files needed — hybrid DBs built on VPS
FILES = [
    # (vps_filename, device_path, owner, selinux_context)
    ("hybrid_ce.db", "/data/system_ce/0/accounts_ce.db", "1000:1000", "u:object_r:accounts_data_file:s0"),
    ("hybrid_de.db", "/data/system_de/0/accounts_de.db", "1000:1000", "u:object_r:accounts_data_file:s0"),
]

# Expected MD5s for integrity verification
EXPECTED_MD5 = {
    "hybrid_ce.db": "52f07adec3c1810dba3118799c07d69b",
    "hybrid_de.db": "120ac42b4838ca196443e9c45222fc7e",
}


async def cmd(client, pad, command, timeout=30, label="", retries=3):
    """Execute sync_cmd with retry."""
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
                print(f"    [{label}] code={code}")
                return None
        except Exception as e:
            print(f"    [{label}] error: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(3)
    return None


async def wait_for_boot(client, pad, max_wait=120):
    """Wait for device to boot and respond."""
    t0 = time.time()
    for i in range(max_wait // 10):
        await asyncio.sleep(10)
        elapsed = int(time.time() - t0)
        out = await cmd(client, pad, "getprop sys.boot_completed", label="boot_check", retries=1)
        if out and "1" in out:
            print(f"    Boot complete at {elapsed}s")
            return True
        # Also check if commands work at all
        out = await cmd(client, pad, "echo ALIVE", label="alive_check", retries=1)
        if out and "ALIVE" in out:
            print(f"    Device responsive at {elapsed}s")
            return True
        print(f"    [{elapsed}s] Still booting...")
    return False


async def main():
    t0 = time.time()
    client = VMOSCloudClient(
        ak="BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi",
        sk="Q2SgcSwEfuwoedY0cijp6Mce",
        base_url="https://api.vmoscloud.com"
    )

    print("=" * 70)
    print("  CLONE RESTORE v4 — HYBRID DB INJECTION")
    print(f"  Target: {TARGET}")
    print("=" * 70)

    # ══════ PHASE 1: PRE-FLIGHT ══════
    print("\n╔══ PHASE 1: PRE-FLIGHT ══╗")
    out = await cmd(client, TARGET, "id", label="preflight")
    if out is None:
        print("  FATAL: Device unreachable")
        return
    print(f"  Root: {out[:80]}")
    await asyncio.sleep(3)

    out = await cmd(client, TARGET, "getprop ro.build.version.release && dumpsys account 2>/dev/null | head -5", label="state")
    print(f"  State: {out[:200] if out else 'N/A'}")
    await asyncio.sleep(3)

    # ══════ PHASE 2: DOWNLOAD HYBRID DBs ══════
    print("\n╔══ PHASE 2: DOWNLOAD HYBRID DBs ══╗")
    
    # Create work dir + launch downloads
    dl_script = f"rm -rf {TMP} && mkdir -p {TMP} && "
    for vps_name, _, _, _ in FILES:
        dl_script += f"curl -sf --connect-timeout 10 --max-time 60 http://{VPS}/{vps_name} -o {TMP}/{vps_name} && "
    dl_script += "echo ALL_DONE"
    
    out = await cmd(client, TARGET, dl_script, timeout=30, label="download")
    if not out or "ALL_DONE" not in out:
        # Try background download
        print("  Sync download failed, trying background...")
        bg_dl = f"rm -rf {TMP} && mkdir -p {TMP} && "
        for vps_name, _, _, _ in FILES:
            bg_dl += (f"nohup sh -c 'curl -sf --connect-timeout 10 --max-time 60 "
                      f"http://{VPS}/{vps_name} -o {TMP}/{vps_name} "
                      f"&& echo DONE_{vps_name} >> {TMP}/status.txt' >/dev/null 2>&1 & ")
        bg_dl += "echo LAUNCHED"
        await cmd(client, TARGET, bg_dl, label="bg_download")
        await asyncio.sleep(10)
        
        for poll in range(12):
            out = await cmd(client, TARGET, f"cat {TMP}/status.txt 2>/dev/null | wc -l", label="poll")
            try:
                done = int(out.strip()) if out else 0
            except:
                done = 0
            print(f"  Poll {poll+1}: {done}/{len(FILES)} done")
            if done >= len(FILES):
                break
            await asyncio.sleep(5)
    else:
        print("  All downloads completed synchronously")
    
    await asyncio.sleep(3)

    # Verify downloads with MD5
    print("\n  Verifying downloads...")
    for vps_name, _, _, _ in FILES:
        out = await cmd(client, TARGET, f"md5sum {TMP}/{vps_name}", label=f"md5_{vps_name}")
        device_md5 = out.split()[0] if out else "MISSING"
        expected = EXPECTED_MD5.get(vps_name, "???")
        match = "✓" if device_md5 == expected else "✗ MISMATCH"
        print(f"  {vps_name}: {device_md5} {match}")
        if device_md5 != expected:
            print(f"    Expected: {expected}")
            print("  FATAL: MD5 mismatch, aborting")
            return
        await asyncio.sleep(2)

    # ══════ PHASE 3: FREEZE GOOGLE SERVICES ══════
    print("\n╔══ PHASE 3: FREEZE GOOGLE SERVICES ══╗")
    
    # Stop all Google packages
    pkgs = [
        "com.google.android.gms",
        "com.google.android.gsf",
        "com.android.vending",
        "com.google.android.gm",
        "com.google.android.apps.docs",
        "com.google.android.apps.photos",
        "com.google.android.youtube",
        "com.google.process.gapps",
    ]
    stop_cmd = " && ".join([f"am force-stop {p} 2>/dev/null" for p in pkgs]) + " && echo STOPPED"
    out = await cmd(client, TARGET, stop_cmd, label="stop_gms")
    print(f"  Force-stop: {out[:50] if out else 'N/A'}")
    await asyncio.sleep(3)

    # Kill remaining processes
    kill_cmd = "killall -9 com.google.android.gms com.google.android.gsf com.google.process.gapps 2>/dev/null; echo KILLED"
    out = await cmd(client, TARGET, kill_cmd, label="kill_gms")
    print(f"  Kill: {out[:50] if out else 'N/A'}")
    await asyncio.sleep(3)

    # ══════ PHASE 4: CLEAN WAL/SHM + INSTALL HYBRID DBs ══════
    print("\n╔══ PHASE 4: INSTALL HYBRID DBs ══╗")

    # Clean ALL WAL/SHM/journal files first
    clean_cmd = (
        "rm -f /data/system_ce/0/accounts_ce.db-wal "
        "/data/system_ce/0/accounts_ce.db-shm "
        "/data/system_ce/0/accounts_ce.db-journal "
        "/data/system_de/0/accounts_de.db-wal "
        "/data/system_de/0/accounts_de.db-shm "
        "/data/system_de/0/accounts_de.db-journal "
        "&& echo CLEANED"
    )
    out = await cmd(client, TARGET, clean_cmd, label="clean_wal")
    print(f"  WAL cleanup: {out}")
    await asyncio.sleep(2)

    for vps_name, device_path, owner, ctx in FILES:
        print(f"\n  Installing {vps_name} → {device_path}")
        
        # Copy
        cp_cmd = f"cp {TMP}/{vps_name} {device_path} && echo CP_OK"
        out = await cmd(client, TARGET, cp_cmd, label=f"cp_{vps_name}")
        print(f"    Copy: {out}")
        await asyncio.sleep(1)

        # Ownership
        out = await cmd(client, TARGET, f"chown {owner} {device_path}", label=f"chown_{vps_name}")
        await asyncio.sleep(1)

        # Permissions
        out = await cmd(client, TARGET, f"chmod 660 {device_path}", label=f"chmod_{vps_name}")
        await asyncio.sleep(1)

        # SELinux
        out = await cmd(client, TARGET, f"chcon {ctx} {device_path}", label=f"chcon_{vps_name}")
        await asyncio.sleep(1)

        # Verify
        out = await cmd(client, TARGET, f"ls -laZ {device_path}", label=f"verify_{vps_name}")
        print(f"    Verified: {out}")
        await asyncio.sleep(2)

    # ══════ PHASE 5: RELOAD ACCOUNTS ══════
    print("\n╔══ PHASE 5: RELOAD ACCOUNTS ══╗")
    
    # Method: Kill system_server — it auto-restarts and re-reads DBs
    # This is SAFER than instance_restart which does a full VM reboot
    print("  Killing system_server to force DB reload...")
    out = await cmd(client, TARGET, 
        "PID=$(pidof system_server) && echo KILLING_PID=$PID && kill $PID",
        label="kill_ss")
    print(f"  {out}")
    
    # Wait for system_server to respawn and stabilize
    print("  Waiting for system_server to respawn...")
    await asyncio.sleep(15)
    
    # Check if device is responsive
    for i in range(10):
        out = await cmd(client, TARGET, "echo ALIVE", label="post_kill_check", retries=1)
        if out and "ALIVE" in out:
            print(f"  System_server recovered after {(i+1)*5}s")
            break
        await asyncio.sleep(5)
    else:
        print("  System_server may need more time...")
        await asyncio.sleep(20)
    
    await asyncio.sleep(5)

    # ══════ PHASE 6: VERIFICATION ══════
    print("\n" + "=" * 70)
    print("  VERIFICATION")
    print("=" * 70)

    # 6a: dumpsys account
    print("\n  [6a] dumpsys account...")
    out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -40", timeout=30, label="dumpsys")
    if out:
        for line in out.split("\n")[:35]:
            print(f"    {line}")
    await asyncio.sleep(3)

    # 6b: Check account count specifically
    print("\n  [6b] Account count...")
    out = await cmd(client, TARGET, 
        "dumpsys account 2>/dev/null | grep -c '@gmail.com'",
        label="count")
    print(f"    Gmail references: {out}")
    await asyncio.sleep(3)

    # 6c: DB files on device
    print("\n  [6c] DB files...")
    out = await cmd(client, TARGET, 
        "ls -la /data/system_ce/0/accounts_ce.db /data/system_de/0/accounts_de.db",
        label="files")
    print(f"    {out}")
    await asyncio.sleep(3)

    # 6d: WAL status
    print("\n  [6d] WAL/SHM status...")
    out = await cmd(client, TARGET,
        "ls /data/system_ce/0/accounts_ce.db-wal /data/system_de/0/accounts_de.db-wal 2>/dev/null || echo NO_WAL",
        label="wal")
    print(f"    {out}")
    await asyncio.sleep(3)

    # 6e: Logcat for account errors
    print("\n  [6e] Recent account logcat...")
    out = await cmd(client, TARGET,
        "logcat -d -t 50 2>/dev/null | grep -iE 'AccountManager|accounts_ce|accounts_de|SQLITE' | tail -15 || echo NO_LOGS",
        label="logcat")
    if out:
        for line in out.split("\n")[:12]:
            print(f"    {line}")
    await asyncio.sleep(3)

    # 6f: Check if system_server is healthy
    print("\n  [6f] System health...")
    out = await cmd(client, TARGET, "pidof system_server && uptime", label="health")
    print(f"    {out}")

    elapsed = time.time() - t0
    print(f"\n{'=' * 70}")
    print(f"  CLONE RESTORE v4 COMPLETE — {elapsed:.0f}s")
    print(f"  Target: {TARGET}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
