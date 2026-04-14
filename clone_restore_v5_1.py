#!/usr/bin/env python3
"""
Clone Restore v5.1 — MICRO DB INJECTION
========================================
Root cause analysis from v1-v4:
  - v1-v3: Hybrid/full DBs (84 tokens, 221 extras) → system_server crash on restart
  - v4: Same hybrid, kill system_server → device death (status=14)

v5.1 hypothesis: The auth tokens/extras are crashing GMS.
  SOLUTION: Inject ONLY account names — ZERO tokens, ZERO extras.
  - micro_ce.db: 40KB (identical to fresh, + 2 account rows)
  - micro_de.db: 64KB (identical to fresh, + 2 accounts + visibility)

Source: 10.12.21.175 (SM-S9110)
  - petersfaustina699@gmail.com + faustinapeters11@gmail.com
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

FILES = [
    ("micro_ce.db", "/data/system_ce/0/accounts_ce.db", "1000:1000", "u:object_r:accounts_data_file:s0"),
    ("micro_de.db", "/data/system_de/0/accounts_de.db", "1000:1000", "u:object_r:accounts_data_file:s0"),
]

EXPECTED_MD5 = {
    "micro_ce.db": "bba12b2df1a164405ed355988bdb95c7",
    "micro_de.db": "d24df7ea1505720cf148a444a78f8e5b",
}


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
                print(f"    [{label}] code={code}")
                return None
        except Exception as e:
            print(f"    [{label}] err: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    return None


async def main():
    t0 = time.time()
    client = VMOSCloudClient(
        ak="YOUR_VMOS_AK_HERE",
        sk="YOUR_VMOS_SK_HERE",
        base_url="https://api.vmoscloud.com"
    )

    print("=" * 70)
    print("  CLONE RESTORE v5.1 — MICRO DB INJECTION")
    print(f"  Target: {TARGET}")
    print("  Micro DBs: accounts only, ZERO tokens/extras")
    print("=" * 70)

    # ══════ PHASE 1: PRE-FLIGHT ══════
    print("\n╔══ PHASE 1: PRE-FLIGHT ══╗")
    out = await cmd(client, TARGET, "id", label="id")
    if not out or "root" not in out:
        print(f"  FATAL: No root ({out})")
        return
    print(f"  Root: {out[:80]}")
    await asyncio.sleep(3)

    out = await cmd(client, TARGET,
        "getprop ro.build.version.release && dumpsys account 2>/dev/null | head -5",
        label="state")
    print(f"  State:\n    {out[:300] if out else 'N/A'}")
    await asyncio.sleep(3)

    # Capture system_server PID for reference
    out = await cmd(client, TARGET, "pidof system_server", label="ss_pid")
    ss_pid = out.strip() if out else "?"
    print(f"  system_server PID: {ss_pid}")
    await asyncio.sleep(3)

    # ══════ PHASE 2: DOWNLOAD MICRO DBs ══════
    print("\n╔══ PHASE 2: DOWNLOAD MICRO DBs ══╗")
    
    # Background download (proven to work in v4)
    bg_cmd = f"mkdir -p {TMP} && "
    for vps_name, _, _, _ in FILES:
        bg_cmd += (f"nohup sh -c 'curl -sf --connect-timeout 15 --max-time 60 "
                   f"http://{VPS}/{vps_name} -o {TMP}/{vps_name} "
                   f"&& echo DONE_{vps_name} >> {TMP}/status.txt' >/dev/null 2>&1 & ")
    bg_cmd += "echo LAUNCHED"
    
    out = await cmd(client, TARGET, bg_cmd, label="launch_dl")
    print(f"  {out}")
    await asyncio.sleep(8)
    
    # Poll for completion
    for poll in range(15):
        out = await cmd(client, TARGET, f"cat {TMP}/status.txt 2>/dev/null | wc -l", label="poll")
        try:
            done = int(out.strip()) if out else 0
        except:
            done = 0
        if done >= len(FILES):
            print(f"  Downloads complete ({poll+1} polls)")
            break
        print(f"  Poll {poll+1}: {done}/{len(FILES)}")
        await asyncio.sleep(5)
    else:
        print("  Download may have failed, checking files directly...")
    await asyncio.sleep(3)

    # Verify MD5
    print("\n  Verifying downloads...")
    all_ok = True
    for vps_name, _, _, _ in FILES:
        out = await cmd(client, TARGET, f"md5sum {TMP}/{vps_name} 2>/dev/null", label=f"md5_{vps_name}")
        if out:
            device_md5 = out.split()[0]
            expected = EXPECTED_MD5.get(vps_name, "")
            ok = "✓" if device_md5 == expected else "✗"
            print(f"  {vps_name}: {device_md5} {ok}")
            if device_md5 != expected:
                all_ok = False
        else:
            print(f"  {vps_name}: DOWNLOAD FAILED")
            all_ok = False
        await asyncio.sleep(2)

    if not all_ok:
        print("  FATAL: MD5 mismatch or download failure")
        return

    # Check file sizes (should match fresh DBs exactly)
    out = await cmd(client, TARGET, f"ls -la {TMP}/micro_ce.db {TMP}/micro_de.db", label="sizes")
    print(f"  Sizes: {out}")
    await asyncio.sleep(3)

    # ══════ PHASE 3: FREEZE GOOGLE SERVICES ══════
    print("\n╔══ PHASE 3: FREEZE GOOGLE SERVICES ══╗")
    
    pkgs = ["com.google.android.gms", "com.google.android.gsf", "com.android.vending"]
    for p in pkgs:
        out = await cmd(client, TARGET, f"am force-stop {p} 2>/dev/null && echo STOPPED_{p}", label=f"stop_{p}")
        print(f"  {out}")
        await asyncio.sleep(2)
    
    out = await cmd(client, TARGET,
        "killall -9 com.google.android.gms com.google.android.gsf 2>/dev/null; echo KILL_DONE",
        label="kill_gms")
    print(f"  Kill: {out}")
    await asyncio.sleep(3)

    # ══════ PHASE 4: INSTALL MICRO DBs ══════  
    print("\n╔══ PHASE 4: INSTALL MICRO DBs ══╗")

    # Clean WAL/SHM
    out = await cmd(client, TARGET,
        f"rm -f {'/data/system_ce/0/accounts_ce.db'}-wal "
        f"{'/data/system_ce/0/accounts_ce.db'}-shm "
        f"{'/data/system_ce/0/accounts_ce.db'}-journal "
        f"{'/data/system_de/0/accounts_de.db'}-wal "
        f"{'/data/system_de/0/accounts_de.db'}-shm "
        f"{'/data/system_de/0/accounts_de.db'}-journal "
        f"&& echo CLEANED",
        label="clean")
    print(f"  WAL cleanup: {out}")
    await asyncio.sleep(2)

    for vps_name, dest, owner, ctx in FILES:
        print(f"\n  Installing {vps_name} → {dest}")
        out = await cmd(client, TARGET,
            f"cp {TMP}/{vps_name} {dest} && "
            f"chown {owner} {dest} && "
            f"chmod 660 {dest} && "
            f"chcon {ctx} {dest} && "
            f"ls -laZ {dest}",
            label=f"install_{vps_name}")
        print(f"    {out}")
        await asyncio.sleep(3)

    # ══════ PHASE 5: PROGRESSIVE RELOAD ══════
    print("\n╔══ PHASE 5: PROGRESSIVE RELOAD ══╗")
    
    # Step 5A: Broadcast only (safest, likely won't show accounts)
    print("\n  [5a] Broadcasting account change...")
    out = await cmd(client, TARGET,
        "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>&1",
        label="broadcast")
    print(f"  {out}")
    await asyncio.sleep(5)

    out = await cmd(client, TARGET,
        "dumpsys account 2>/dev/null | grep -E 'Accounts:|@gmail' | head -5",
        label="check_5a")
    print(f"  After broadcast: {out}")
    await asyncio.sleep(3)

    # Step 5B: Restart GMS only
    print("\n  [5b] Restarting GMS...")
    out = await cmd(client, TARGET,
        "am force-stop com.google.android.gms && "
        "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED && "
        "sleep 1 && "
        "am startservice -n com.google.android.gms/.chimera.PersistentApiService 2>&1",
        label="restart_gms")
    print(f"  {out}")
    await asyncio.sleep(8)

    out = await cmd(client, TARGET,
        "dumpsys account 2>/dev/null | grep -E 'Accounts:|@gmail' | head -5",
        label="check_5b")
    print(f"  After GMS restart: {out}")
    await asyncio.sleep(3)

    # Check if accounts appeared without full restart
    out = await cmd(client, TARGET,
        "dumpsys account 2>/dev/null | grep -c '@gmail.com'",
        label="count_5b")
    gmail_refs = int(out.strip()) if out and out.strip().isdigit() else 0
    
    if gmail_refs > 0:
        print(f"\n  *** ACCOUNTS APPEARED WITHOUT RESTART ({gmail_refs} refs) ***")
    else:
        # Step 5C: VMOS instance_restart (proper API path)
        print(f"\n  [5c] Accounts not visible yet ({gmail_refs} refs)")
        print("  Using VMOS instance_restart API (proper restart flow)...")
        
        # Capture pre-restart diagnostics
        out = await cmd(client, TARGET,
            "logcat -d -t 20 2>/dev/null | grep -iE 'Account|SQLite' | tail -10",
            label="pre_logcat")
        if out:
            print(f"  Pre-restart logcat:\n    {out[:500]}")
        await asyncio.sleep(3)

        try:
            r = await client.instance_restart([TARGET])
            print(f"  Restart API response: code={r.get('code')} msg={r.get('msg')}")
        except Exception as e:
            print(f"  Restart error: {e}")
            # Fallback: try kill system_server
            print("  Fallback: kill system_server")
            out = await cmd(client, TARGET,
                "kill $(pidof system_server) 2>&1; echo KILLED",
                label="kill_ss")
            print(f"  {out}")
        
        # Wait for device to come back
        print("\n  Waiting for device to reboot...")
        await asyncio.sleep(30)
        
        alive = False
        for i in range(20):
            # Check instance status first
            try:
                r = await client.instance_list()
                for d in r.get('data', {}).get('pageData', []):
                    if d.get('padCode') == TARGET:
                        s = d.get('padStatus')
                        if s == 14:
                            print(f"  [{(i+1)*8}s] DEVICE DEAD (status=14)")
                            print("  *** MICRO DBs ALSO CRASH THE DEVICE ***")
                            print("  CONCLUSION: VMOS does NOT support DB-level account injection")
                            
                            elapsed = time.time() - t0
                            print(f"\n{'=' * 70}")
                            print(f"  v5.1 FAILED — {elapsed:.0f}s")
                            print(f"{'=' * 70}")
                            return
                        elif s == 10:
                            # Device is running, try to send a command
                            pass
                        else:
                            print(f"  [{(i+1)*8}s] status={s}")
                            await asyncio.sleep(8)
                            continue
            except:
                pass
            
            out = await cmd(client, TARGET, "echo ALIVE", label="boot", retries=1)
            if out and "ALIVE" in out:
                print(f"  Device ALIVE after {(i+1)*8 + 30}s")
                alive = True
                break
            await asyncio.sleep(8)
        
        if not alive:
            print("  Device did not come back. Checking final status...")
            try:
                r = await client.instance_list()
                for d in r.get('data', {}).get('pageData', []):
                    if d.get('padCode') == TARGET:
                        print(f"  Final status: {d.get('padStatus')}")
            except:
                pass
            return
        
        await asyncio.sleep(10)

    # ══════ PHASE 6: FINAL VERIFICATION ══════
    print("\n" + "=" * 70)
    print("  PHASE 6: FINAL VERIFICATION")
    print("=" * 70)

    # Full dumpsys account
    out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -40", label="final_dump")
    if out:
        for line in out.split("\n")[:35]:
            print(f"    {line}")
    await asyncio.sleep(3)

    # Gmail reference count
    out = await cmd(client, TARGET,
        "dumpsys account 2>/dev/null | grep -c '@gmail.com'",
        label="final_count")
    print(f"\n  Gmail references: {out}")
    await asyncio.sleep(3)

    # DB integrity check
    out = await cmd(client, TARGET,
        f"ls -laZ {'/data/system_ce/0/accounts_ce.db'} {'/data/system_de/0/accounts_de.db'}",
        label="final_files")
    print(f"  DB files: {out}")
    await asyncio.sleep(3)

    # System health
    out = await cmd(client, TARGET, "pidof system_server && uptime", label="health")
    print(f"  System health: {out}")
    await asyncio.sleep(3)

    # Post-restart logcat for account-related messages
    out = await cmd(client, TARGET,
        "logcat -d -t 100 2>/dev/null | grep -iE 'AccountManager|account.*service|GoogleLogin' | tail -15",
        label="post_logcat")
    if out:
        print(f"\n  Account logcat:")
        for line in out.split("\n")[:12]:
            print(f"    {line}")

    elapsed = time.time() - t0
    print(f"\n{'=' * 70}")
    print(f"  CLONE RESTORE v5.1 COMPLETE — {elapsed:.0f}s")
    print(f"  Target: {TARGET}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
