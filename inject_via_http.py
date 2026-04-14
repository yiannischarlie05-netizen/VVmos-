#!/usr/bin/env python3
"""
Inject accounts via HTTP download from VPS.
DBs already built & served at http://37.60.234.139:9999/clone_dbs/
No base64 corruption — target curls directly from VPS.
"""
import asyncio
import os
import sys
import time

os.environ['VMOS_ALLOW_RESTART'] = '1'
sys.path.insert(0, ".")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

TARGET = "ACP250916A5B1912"
VPS = "37.60.234.139"
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
STAGING = "/data/local/tmp/clone7"
API_DELAY = 3.0


async def cmd(client, sh, timeout=30, retries=3):
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
        except:
            if attempt < retries - 1:
                await asyncio.sleep(3)
    return None


async def main():
    t0 = time.time()
    client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")

    print("=" * 70, flush=True)
    print("  INJECT via HTTP DOWNLOAD (no base64 corruption)", flush=True)
    print("=" * 70, flush=True)

    # Verify target alive
    out = await cmd(client, "id")
    print(f"Target: {out}", flush=True)
    if not out or "root" not in (out or ""):
        print("  Not root, enabling...", flush=True)
        try:
            await client.switch_root([TARGET], enable=True)
            await asyncio.sleep(8)
        except:
            pass
        out = await cmd(client, "id")
        print(f"  After root: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    # Create staging
    await cmd(client, f"mkdir -p {STAGING}")
    await asyncio.sleep(2)

    # Test VPS connectivity
    print("\n[0] TESTING VPS CONNECTIVITY...", flush=True)
    out = await cmd(client,
        f"curl -s -o /dev/null -w '%{{http_code}}' http://{VPS}:9999/clone_dbs/accounts_ce.db --max-time 5",
        timeout=15)
    print(f"  VPS HTTP test: {out}", flush=True)
    if out != "200":
        print("  FATAL: Target cannot reach VPS!", flush=True)
        await client.close()
        return
    await asyncio.sleep(API_DELAY)

    # Download DBs from VPS
    print("\n[1] DOWNLOADING DBs FROM VPS...", flush=True)
    db_ok = True
    expected = {"accounts_ce.db": ("53248", "18a57b5b360ba24a92e9f975187f0c26"),
                "accounts_de.db": ("49152", "2d666840b7265f82ab7ce217c33d6888")}

    for db_name, (exp_size, exp_md5) in expected.items():
        out = await cmd(client,
            f"curl -s -o {STAGING}/{db_name} http://{VPS}:9999/clone_dbs/{db_name} && "
            f"wc -c < {STAGING}/{db_name}",
            timeout=30)
        size = (out or "").strip()
        print(f"  {db_name}: size={size} (expected {exp_size})", flush=True)
        await asyncio.sleep(2)

        out = await cmd(client,
            f"md5sum {STAGING}/{db_name} 2>/dev/null | cut -d' ' -f1",
            timeout=15)
        md5 = (out or "").strip()
        ok = md5 == exp_md5
        print(f"  {db_name}: md5={md5} {'OK' if ok else 'MISMATCH!'}", flush=True)
        if not ok:
            db_ok = False
        await asyncio.sleep(API_DELAY)

    if not db_ok:
        print("  FATAL: DB integrity check failed!", flush=True)
        await client.close()
        return

    # Freeze services
    print("\n[2] FREEZING SERVICES...", flush=True)
    for p in ["com.google.android.gms", "com.google.android.gsf",
              "com.android.vending", "com.google.android.gm"]:
        await cmd(client, f"am force-stop {p} 2>/dev/null", retries=1)
        await asyncio.sleep(0.5)
    await cmd(client, "killall -9 com.google.android.gms com.google.android.gsf 2>/dev/null")
    await asyncio.sleep(3)

    # Atomic inode swap
    print("\n[3] ATOMIC DB SWAP + PERMISSIONS...", flush=True)
    DB_MAP = {
        "accounts_ce.db": "/data/system_ce/0/accounts_ce.db",
        "accounts_de.db": "/data/system_de/0/accounts_de.db",
    }
    for db_name, dev_path in DB_MAP.items():
        # Clean sidecars
        await cmd(client, f"rm -f '{dev_path}-wal' '{dev_path}-shm' '{dev_path}-journal'")
        await asyncio.sleep(0.5)
        # Move old (new inode)
        await cmd(client, f"mv '{dev_path}' '{dev_path}.old' 2>/dev/null")
        await asyncio.sleep(0.5)
        # Copy new
        out = await cmd(client, f"cp '{STAGING}/{db_name}' '{dev_path}' && echo CP_OK")
        print(f"  {db_name}: {out}", flush=True)
        await asyncio.sleep(0.5)
        # Fix perms + SELinux
        await cmd(client,
            f"chown 1000:1000 '{dev_path}' && chmod 660 '{dev_path}' && "
            f"chcon u:object_r:system_data_file:s0 '{dev_path}'")
        await asyncio.sleep(0.5)
        # Verify
        out = await cmd(client, f"ls -laZ '{dev_path}'")
        print(f"  Verify: {out}", flush=True)
        await asyncio.sleep(1)

    # Cleanup old
    for dev_path in DB_MAP.values():
        await cmd(client, f"rm -f '{dev_path}.old'")

    # Restart
    print("\n[4] RESTART + VERIFY...", flush=True)
    out = await cmd(client,
        "ls /data/system_ce/0/accounts_ce.db-wal 2>/dev/null && echo HAS_WAL || echo SAFE")
    print(f"  WAL check: {out}", flush=True)

    try:
        r = await client.instance_restart([TARGET])
        print(f"  Restart: code={r.get('code')}", flush=True)
    except Exception as e:
        print(f"  Restart error: {e}", flush=True)

    print("  Waiting for reboot...", flush=True)
    await asyncio.sleep(40)

    alive = False
    for i in range(15):
        out = await cmd(client, "echo ALIVE", retries=1, timeout=10)
        if out and "ALIVE" in out:
            print(f"  ALIVE after {i * 8 + 40}s", flush=True)
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
                        print(f"  [{i * 8 + 40}s] status={s}", flush=True)
        except:
            pass
        await asyncio.sleep(8)

    if not alive:
        print("  Target not responding", flush=True)
        await client.close()
        return

    await asyncio.sleep(5)

    # Verification
    print(f"\n{'=' * 70}", flush=True)
    print("  VERIFICATION", flush=True)
    print(f"{'=' * 70}", flush=True)

    out = await cmd(client, "dumpsys account 2>/dev/null | head -20")
    if out:
        for line in out.split("\n")[:20]:
            print(f"    {line}", flush=True)
    await asyncio.sleep(API_DELAY)

    out = await cmd(client, "getprop ro.product.model && getprop ro.product.brand")
    print(f"\n  Identity: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    for db in ["/data/system_ce/0/accounts_ce.db", "/data/system_de/0/accounts_de.db"]:
        out = await cmd(client, f"ls -laZ {db}")
        print(f"  {db.split('/')[-1]}: {out}", flush=True)
        out = await cmd(client, f"ls {db}-wal 2>/dev/null && echo HAS_WAL || echo NO_WAL")
        print(f"    sidecar: {out}", flush=True)
        await asyncio.sleep(1)

    out = await cmd(client, "pidof system_server && uptime")
    print(f"\n  System: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    out = await cmd(client,
        "logcat -d -t 50 2>/dev/null | grep -iE 'SQLite.*Error|IOERR|AccountManager.*crash' | tail -5")
    if out and out.strip():
        print(f"  Logcat errors: {out}", flush=True)
    else:
        print(f"  Logcat: CLEAN (no SQLite errors)", flush=True)

    elapsed = time.time() - t0
    print(f"\n{'=' * 70}", flush=True)
    print(f"  DONE — {elapsed:.0f}s", flush=True)
    print(f"{'=' * 70}", flush=True)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
