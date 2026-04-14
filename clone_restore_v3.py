#!/usr/bin/env python3
"""
Clone Restore v3 — Correct DB cloning with UID migration.

Root causes fixed (from v1 + v2 failures):
  v1: phenotype.db WAL mode, GMS respawn, manual zygote kill -> device brick
  v2: accounts_de.db UID mismatch (10026 vs 10036) -> Accounts: 0 + IOERR_WRITE
      Stale fd corruption (cp over open inode), no journal file -> crash loop

v3 fixes:
  1. accounts_de.db pre-migrated on VPS (UID 10026->10036, cleaned debug_table/visibility)
  2. Use mv+cp instead of overwriting (avoids stale fd corruption from system_server)
  3. Create proper 0-byte journal files after DB install
  4. Apply identity + restart FIRST (separate cycle), then clone
  5. All DBs verified: DELETE journal mode, integrity_check=ok

Source: 10.12.21.175 (SM-S9110, petersfaustina699@ + faustinapeters11@)
Target: ATP6426IG8ABXYK9 (Android 16, root, factory-reset)
"""
import asyncio
import sys
import time

sys.path.insert(0, ".")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

TARGET = "ATP6426IG8ABXYK9"
VPS = "37.60.234.139:9999"
TMP = "/data/local/tmp/clone"

# SM-S9110 identity
IDENTITY_PROPS = {
    "ro.product.name": "dm1qzhx",
    "ro.product.model": "SM-S9110",
    "ro.product.device": "dm1q",
    "ro.product.board": "dm1q",
    "ro.product.manufacturer": "samsung",
    "ro.product.brand": "samsung",
    "ro.build.id": "TQ3C.230805.001.B2",
    "ro.build.display.id": "TQ3C.230805.001.B2",
    "ro.build.version.release": "13",
    "ro.build.version.sdk": "33",
    "ro.build.version.security_patch": "2023-08-05",
    "ro.build.tags": "release-keys",
    "ro.build.type": "user",
    "ro.build.fingerprint": "samsung/dm1qzhx/dm1q:13/TQ3C.230805.001.B2/S9110ZCS2AWI2:user/release-keys",
    "ro.build.description": "dm1qzhx-user 13 TQ3C.230805.001.B2 S9110ZCS2AWI2 release-keys",
    "wifiMac": "2C:4D:54:E8:3F:91",
    "bluetoothaddr": "2C:4D:54:E8:3F:92",
    "gpuVendor": "Qualcomm",
    "gpuRenderer": "Adreno (TM) 740",
    "gpuVersion": "OpenGL ES 3.2 V@0615.77",
}

MODEM_PROPS = {
    "imei": "353879151042817",
    "SimOperatorName": "T-Mobile",
    "simCountryIso": "us",
    "MCCMNC": "310260",
    "ICCID": "8901260000012345678",
    "IMSI": "310260000012345",
}

# DB files — accts_de uses MIGRATED version with fixed UIDs
FILES = [
    # (vps_name, device_path, owner, selinux, description)
    ("accts_ce.db", "/data/system_ce/0/accounts_ce.db",
     "1000:1000", "u:object_r:accounts_data_file:s0", "account credentials"),
    ("accts_de_migrated.db", "/data/system_de/0/accounts_de.db",
     "1000:1000", "u:object_r:accounts_data_file:s0", "account device-encrypted"),
    ("gsf_gservices2.db", "/data/data/com.google.android.gsf/databases/gservices.db",
     None, None, "GSF gservices config"),
    ("phenotype.db", "/data/data/com.google.android.gms/databases/phenotype.db",
     None, None, "GMS phenotype flags"),
]

GOOGLE_PACKAGES = [
    "com.google.android.gms",
    "com.google.android.gsf",
    "com.google.android.gsf.login",
    "com.google.process.gapps",
    "com.android.vending",
    "com.google.android.gm",
    "com.google.android.apps.maps",
    "com.google.android.youtube",
    "com.google.android.apps.docs",
]


async def cmd(client, pad, command, timeout=30, label="", retries=3):
    """Execute sync_cmd with retry and rate-limit handling."""
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
                    print(f"      [{label}] timeout, retry {attempt+1}...")
                    await asyncio.sleep(2)
                    continue
                return "TIMEOUT"
            elif code == 110031:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return f"NOT_READY:{code}"
            else:
                return f"ERR:{code}:{r.get('msg','')}"
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(3)
                continue
            return f"EXC:{e}"
    return "TIMEOUT"


async def bg_cmd(client, pad, command, poll_cmd, done_marker="DONE",
                 timeout=120, poll_interval=5, label=""):
    """Run background command, poll for completion."""
    bg = f"nohup sh -c '{command}; echo {done_marker}' > /data/local/tmp/_bg.log 2>&1 &"
    await client.sync_cmd(pad, bg, timeout_sec=8)
    start = time.time()
    while time.time() - start < timeout:
        await asyncio.sleep(poll_interval)
        r = await cmd(client, pad, poll_cmd, label=label, timeout=8)
        if done_marker in str(r):
            return r
    return "BG_TIMEOUT"


async def main():
    client = VMOSCloudClient(
        ak="YOUR_VMOS_AK_HERE",
        sk="YOUR_VMOS_SK_HERE",
        base_url="https://api.vmoscloud.com",
    )

    start = time.time()
    print("=" * 72)
    print("  CLONE RESTORE v3 — UID-MIGRATED DB CLONING")
    print(f"  Target: {TARGET} | Source: 10.12.21.175 (SM-S9110)")
    print("=" * 72)

    # ══════════════════════════════════════════════════════════════════
    # PHASE 1: APPLY IDENTITY + RESTART (separate cycle)
    # ══════════════════════════════════════════════════════════════════
    print("\n╔══ PHASE 1: APPLY IDENTITY + RESTART ══╗")

    # Pre-flight check
    r = await cmd(client, TARGET, "id", label="id")
    print(f"  Root check: {r.split()[0] if r else 'FAIL'}")
    if "uid=0" not in str(r):
        print("  FATAL: not root")
        return
    await asyncio.sleep(3)

    # Apply identity props
    print("  Applying system properties...")
    r = await client.modify_instance_properties([TARGET], IDENTITY_PROPS)
    print(f"  System props: code={r.get('code')}")
    await asyncio.sleep(3)

    print("  Applying modem properties...")
    r = await client.modify_instance_properties([TARGET], MODEM_PROPS)
    print(f"  Modem props: code={r.get('code')}")
    await asyncio.sleep(3)

    # Restart to apply identity (separate from DB clone cycle)
    print("  Restarting to apply identity...")
    r = await client.instance_restart([TARGET])
    print(f"  Restart: code={r.get('code')}")

    # Wait for boot
    for i in range(30):
        await asyncio.sleep(5)
        r = await cmd(client, TARGET, "getprop sys.boot_completed", label="boot", retries=1)
        if r == "1":
            print(f"  Boot complete at {i*5}s")
            break
    else:
        # Longer wait with status check
        for i in range(30):
            await asyncio.sleep(10)
            rl = await client.instance_list()
            for inst in rl.get("data", {}).get("pageData", []):
                if inst.get("padCode") == TARGET:
                    status = inst.get("padStatus")
                    if status == 10:
                        print(f"  Device online (status=10)")
                        await asyncio.sleep(10)  # Extra wait for boot
                        break
            else:
                continue
            break
        else:
            print("  FATAL: device didn't boot after identity restart")
            return

    await asyncio.sleep(5)

    # Verify identity applied
    r = await cmd(client, TARGET, "getprop ro.product.model", label="model")
    print(f"  Identity after restart: {r}")
    if "SM-S9110" not in str(r):
        print("  WARNING: Identity may not have applied, continuing anyway")

    # ══════════════════════════════════════════════════════════════════
    # PHASE 2: DOWNLOAD DBs
    # ══════════════════════════════════════════════════════════════════
    print("\n╔══ PHASE 2: DOWNLOAD DBs ══╗")
    await asyncio.sleep(3)

    r = await cmd(client, TARGET, f"mkdir -p {TMP}", label="mkdir")

    # Download all 4 DBs via background curl
    dl_cmds = []
    for vps_name, _, _, _, desc in FILES:
        dl_cmds.append(f"curl -sS -o {TMP}/{vps_name} http://{VPS}/{vps_name}")
    dl_all = " && ".join(dl_cmds)

    result = await bg_cmd(
        client, TARGET, dl_all,
        f"cat /data/local/tmp/_bg.log",
        done_marker="DONE",
        timeout=120,
        poll_interval=5,
        label="download",
    )
    print(f"  Download result: {result.splitlines()[-1] if result else 'UNKNOWN'}")

    await asyncio.sleep(3)

    # Verify downloads with md5
    for vps_name, _, _, _, desc in FILES:
        r = await cmd(client, TARGET,
                      f"ls -la {TMP}/{vps_name} && md5sum {TMP}/{vps_name}",
                      label=f"verify_{vps_name}")
        lines = r.strip().split("\n") if r else []
        for line in lines:
            print(f"  {desc}: {line.strip()}")
        await asyncio.sleep(3)

    # ══════════════════════════════════════════════════════════════════
    # PHASE 3: DEEP FREEZE GOOGLE SERVICES
    # ══════════════════════════════════════════════════════════════════
    print("\n╔══ PHASE 3: FREEZE GOOGLE SERVICES ══╗")

    # Force stop all Google packages
    print("  Step 3a: Force-stopping Google packages...")
    for pkg in GOOGLE_PACKAGES:
        await cmd(client, TARGET, f"am force-stop {pkg}", label=f"stop_{pkg}", retries=1)
        await asyncio.sleep(1)

    await asyncio.sleep(3)

    # Kill remaining Google processes
    print("  Step 3b: Killing remaining Google processes...")
    r = await cmd(client, TARGET,
                  "ps -A | grep -E 'google|gms|gsf|gapps|vending' | awk '{print $2}' | xargs -r kill -9 2>/dev/null; echo KILLED",
                  label="kill")
    await asyncio.sleep(3)

    # Disable GMS to prevent auto-restart
    print("  Step 3c: Disabling GMS auto-restart...")
    for comp in ["com.google.android.gms/.chimera.GmsIntentOperationService",
                 "com.google.android.gms/.update.SystemUpdateService",
                 "com.google.android.gms/.persistent.GmsPersistentProcess"]:
        await cmd(client, TARGET, f"pm disable {comp} 2>/dev/null", label="disable", retries=1)
        await asyncio.sleep(1)

    await asyncio.sleep(3)

    # Verify freeze
    r = await cmd(client, TARGET,
                  "ps -A | grep -cE 'google|gms|gsf|gapps|vending' || echo 0",
                  label="verify_freeze")
    print(f"  Google processes remaining: {r}")

    # ══════════════════════════════════════════════════════════════════
    # PHASE 4: PREPARE + REPLACE DBs (mv+cp method)
    # ══════════════════════════════════════════════════════════════════
    print("\n╔══ PHASE 4: INSTALL DATABASES ══╗")

    # Get UIDs for GMS/GSF data dirs
    r = await cmd(client, TARGET,
                  "stat -c '%u:%g' /data/data/com.google.android.gms",
                  label="gms_uid")
    gms_uid = r.strip() if r and ":" in r else "10036:10036"
    print(f"  GMS uid: {gms_uid}")
    await asyncio.sleep(3)

    r = await cmd(client, TARGET,
                  "stat -c '%u:%g' /data/data/com.google.android.gsf",
                  label="gsf_uid")
    gsf_uid = r.strip() if r and ":" in r else "10036:10036"
    print(f"  GSF uid: {gsf_uid}")
    await asyncio.sleep(3)

    for vps_name, dev_path, owner, selinux, desc in FILES:
        print(f"\n  Installing {desc}: {vps_name} → {dev_path}")

        # Determine owner
        if owner:
            use_owner = owner
        elif "gms" in dev_path:
            use_owner = gms_uid
        elif "gsf" in dev_path:
            use_owner = gsf_uid
        else:
            use_owner = "1000:1000"

        # Step 1: Clean ALL stale WAL/SHM/journal files
        r = await cmd(client, TARGET,
                      f"rm -f {dev_path}-wal {dev_path}-shm {dev_path}-journal",
                      label=f"clean_{desc}")
        await asyncio.sleep(2)

        # Step 2: Move old DB away (avoids stale fd corruption)
        # Using mv creates a new inode for the destination, while system_server
        # still holds fd to the old inode (now at .old path). After restart,
        # system_server opens the new file cleanly.
        r = await cmd(client, TARGET,
                      f"mv {dev_path} {dev_path}.old 2>/dev/null; echo MV_OK",
                      label=f"mv_{desc}")
        await asyncio.sleep(2)

        # Step 3: Copy new DB to destination (new inode)
        r = await cmd(client, TARGET,
                      f"cp {TMP}/{vps_name} {dev_path} && echo CP_OK",
                      label=f"cp_{desc}")
        print(f"    Copy: {r}")
        await asyncio.sleep(2)

        # Step 4: Set ownership
        r = await cmd(client, TARGET,
                      f"chown {use_owner} {dev_path}",
                      label=f"chown_{desc}")
        await asyncio.sleep(2)

        # Step 5: Set permissions (660)
        r = await cmd(client, TARGET,
                      f"chmod 660 {dev_path}",
                      label=f"chmod_{desc}")
        await asyncio.sleep(2)

        # Step 6: Set SELinux context
        if selinux:
            r = await cmd(client, TARGET,
                          f"chcon {selinux} {dev_path}",
                          label=f"chcon_{desc}")
        else:
            r = await cmd(client, TARGET,
                          f"restorecon {dev_path}",
                          label=f"restorecon_{desc}")
        await asyncio.sleep(2)

        # Step 7: Create empty journal file (system_server expects it)
        # Only for accounts DBs in system_ce/system_de directories
        if "system_ce" in dev_path or "system_de" in dev_path:
            journal_owner = use_owner
            r = await cmd(client, TARGET,
                          f"touch {dev_path}-journal && chown {journal_owner} {dev_path}-journal && chmod 600 {dev_path}-journal",
                          label=f"journal_{desc}")
            print(f"    Journal: created")
        await asyncio.sleep(2)

        # Step 8: Verify
        r = await cmd(client, TARGET,
                      f"ls -laZ {dev_path}",
                      label=f"verify_{desc}")
        print(f"    Verified: {r}")

        # Step 9: WAL paranoia check
        r = await cmd(client, TARGET,
                      f"ls {dev_path}-wal 2>/dev/null && echo HAS_WAL || echo NO_WAL",
                      label=f"wal_{desc}")
        print(f"    WAL check: {r}")
        await asyncio.sleep(2)

    # ══════════════════════════════════════════════════════════════════
    # PHASE 5: RE-ENABLE + RESTART
    # ══════════════════════════════════════════════════════════════════
    print("\n╔══ PHASE 5: RE-ENABLE + RESTART ══╗")

    # Re-enable GMS components
    print("  Re-enabling GMS components...")
    for comp in ["com.google.android.gms/.chimera.GmsIntentOperationService",
                 "com.google.android.gms/.update.SystemUpdateService",
                 "com.google.android.gms/.persistent.GmsPersistentProcess"]:
        await cmd(client, TARGET, f"pm enable {comp} 2>/dev/null", label="enable", retries=1)
        await asyncio.sleep(1)

    await asyncio.sleep(3)

    # Restart via API (safe method)
    print("  Restarting device via API...")
    r = await client.instance_restart([TARGET])
    print(f"  Restart: code={r.get('code')} err={r.get('data',[{}])[0].get('errMsg') if r.get('data') else None}")

    # ══════════════════════════════════════════════════════════════════
    # PHASE 6: WAIT FOR BOOT
    # ══════════════════════════════════════════════════════════════════
    print("\n╔══ PHASE 6: WAIT FOR BOOT ══╗")

    booted = False
    for i in range(60):
        await asyncio.sleep(5)
        r = await cmd(client, TARGET, "getprop sys.boot_completed", label="boot", retries=1)
        if r == "1":
            print(f"  Boot complete at {i*5}s")
            booted = True
            break
        # Also check instance status
        if i > 0 and i % 6 == 0:
            rl = await client.instance_list()
            for inst in rl.get("data", {}).get("pageData", []):
                if inst.get("padCode") == TARGET:
                    status = inst.get("padStatus")
                    print(f"  [{i*5}s] status={status}")
                    if status in (14, 15):
                        print("  FATAL: Device stopped/bricked")
                        return

    if not booted:
        # Final check
        rl = await client.instance_list()
        for inst in rl.get("data", {}).get("pageData", []):
            if inst.get("padCode") == TARGET:
                status = inst.get("padStatus")
                if status == 10:
                    print(f"  Device online but boot_completed not reporting (status={status})")
                    booted = True
                    await asyncio.sleep(15)
                else:
                    print(f"  FATAL: Device status={status}")
                    return

    if not booted:
        print("  FATAL: Device didn't boot in 300s")
        return

    await asyncio.sleep(10)  # Extra settle time

    # ══════════════════════════════════════════════════════════════════
    # PHASE 7: VERIFICATION
    # ══════════════════════════════════════════════════════════════════
    print("\n╔══ PHASE 7: VERIFICATION ══╗")

    # Identity
    print("\n  [7a] Identity...")
    r = await cmd(client, TARGET, "getprop ro.product.model && getprop ro.product.brand", label="identity")
    print(f"    Model+Brand: {r}")
    await asyncio.sleep(3)

    # DB files
    print("\n  [7b] DB files on device...")
    for vps_name, dev_path, _, _, desc in FILES:
        r = await cmd(client, TARGET, f"ls -la {dev_path}", label=f"ls_{desc}")
        print(f"    {desc}: {r}")
        await asyncio.sleep(3)

    # Journal files
    print("\n  [7c] Journal files...")
    for vps_name, dev_path, _, _, desc in FILES:
        r = await cmd(client, TARGET, f"ls -la {dev_path}-journal {dev_path}-wal {dev_path}-shm 2>&1", label=f"journal_{desc}")
        print(f"    {desc}: {r}")
        await asyncio.sleep(3)

    # dumpsys account — THE KEY TEST
    print("\n  [7d] dumpsys account...")
    r = await cmd(client, TARGET, "dumpsys account 2>&1 | head -20", label="dumpsys", timeout=15)
    print(f"    {r}")
    await asyncio.sleep(3)

    # Content provider
    print("\n  [7e] Content provider account query...")
    r = await cmd(client, TARGET,
                  "content query --uri content://com.android.contacts/raw_contacts --projection account_name 2>&1 | head -5",
                  label="content_acct", timeout=10)
    print(f"    {r}")
    await asyncio.sleep(3)

    # WAL status
    print("\n  [7f] WAL/SHM file status...")
    for vps_name, dev_path, _, _, desc in FILES:
        r = await cmd(client, TARGET,
                      f"ls {dev_path}-wal {dev_path}-shm 2>/dev/null && echo HAS_WAL || echo clean",
                      label=f"wal_{desc}")
        print(f"    {desc}: {r}")
        await asyncio.sleep(3)

    elapsed = int(time.time() - start)
    print(f"\n{'='*72}")
    print(f"  CLONE RESTORE v3 COMPLETE — {elapsed}s")
    print(f"  Target: {TARGET}")
    print(f"  Source: SM-S9110 / petersfaustina699@ + faustinapeters11@")
    print(f"{'='*72}")


if __name__ == "__main__":
    asyncio.run(main())
