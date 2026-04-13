#!/usr/bin/env python3
"""
Reset & Clone — Full Pipeline
==============================
1. Reset target device (ACP2507303B6HNRI) to factory
2. Wait for it to boot
3. Full-partition backup from neighbor 10.12.21.175 via launchpad
4. Restore to freshly reset target (with v6 DB journal fix)
5. Verify clone

Uses the fixed clone_engine with DELETE journal mode DB handling.
"""
import asyncio
import os
import sys
import time

os.environ['VMOS_ALLOW_RESTART'] = '1'
sys.path.insert(0, ".")

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
from vmos_titan.core.clone_engine import (
    full_partition_backup, full_partition_restore, verify_clone,
    cloud_cmd, cloud_cmd_retry, probe_device, API_DELAY,
)

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"

TARGET = "ACP2507303B6HNRI"       # Device to reset and clone into
LAUNCHPAD = "APP6476KYH9KMLU5"    # Device used as relay to neighbor
NEIGHBOR_IP = "10.12.21.175"      # Neighbor device (SM-S9110)


async def wait_for_device(client, pad_code, max_wait=180):
    """Wait for device to come online after reset."""
    print(f"\n  Waiting for {pad_code} to come online (max {max_wait}s)...")
    t0 = time.time()

    for i in range(max_wait // 10):
        await asyncio.sleep(10)
        elapsed = int(time.time() - t0)

        # Check instance status
        try:
            r = await client.instance_list()
            for d in r.get('data', {}).get('pageData', []):
                if d.get('padCode') == pad_code:
                    status = d.get('padStatus')
                    if status == 10:  # Running
                        # Try command
                        out = await cloud_cmd(client, pad_code, "echo ALIVE && id")
                        if "ALIVE" in out:
                            print(f"    [{elapsed}s] Device ALIVE — {out[:80]}")
                            return True
                    elif status == 14:
                        print(f"    [{elapsed}s] status=14 (dead/off)")
                    elif status == 11:
                        print(f"    [{elapsed}s] status=11 (restarting)")
                    else:
                        print(f"    [{elapsed}s] status={status}")
        except Exception as e:
            print(f"    [{elapsed}s] poll error: {e}")

    print(f"    Device did not come back within {max_wait}s")
    return False


async def main():
    t0 = time.time()
    client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")

    print("=" * 70)
    print("  RESET & CLONE PIPELINE")
    print(f"  Target:    {TARGET} (will be RESET then receive clone)")
    print(f"  Launchpad: {LAUNCHPAD} (relay to neighbor)")
    print(f"  Neighbor:  {NEIGHBOR_IP}")
    print("=" * 70)

    # ══════ PHASE 1: RESET TARGET DEVICE ══════
    print(f"\n{'─'*70}")
    print(f"  PHASE 1: RESET TARGET DEVICE ({TARGET})")
    print(f"{'─'*70}")

    # Pre-reset check
    out = await cloud_cmd(client, TARGET, "echo ALIVE")
    if "ALIVE" in out:
        print(f"  Device is responsive. Proceeding with reset...")
    else:
        print(f"  Device not responding ({out}). Attempting reset anyway...")
    await asyncio.sleep(2)

    # Execute reset
    print(f"  Calling instance_reset({TARGET})...")
    try:
        r = await client.instance_reset([TARGET])
        code = r.get("code", -1)
        msg = r.get("msg", "")
        print(f"  Reset API: code={code} msg={msg}")
    except Exception as e:
        print(f"  Reset error: {e}")
        print(f"  Trying one_key_new_device as fallback...")
        try:
            os.environ['VMOS_DISABLE_TEMPLATE_IMPORT'] = '0'
            os.environ['VMOS_ALLOW_TEMPLATE_IMPORT_PAD'] = TARGET
            r = await client.one_key_new_device([TARGET])
            code = r.get("code", -1)
            print(f"  one_key_new_device: code={code}")
        except Exception as e2:
            print(f"  Fallback also failed: {e2}")
            return

    # Wait for device to come back after reset
    alive = await wait_for_device(client, TARGET, max_wait=180)
    if not alive:
        print("  FATAL: Device did not come back after reset")
        return

    # Give it a few more seconds to stabilize
    print("  Waiting 15s for system stabilization...")
    await asyncio.sleep(15)

    # Verify clean state
    out = await cloud_cmd(client, TARGET,
        "dumpsys account 2>/dev/null | grep 'Accounts:' | head -1")
    print(f"  Post-reset account state: {out}")
    await asyncio.sleep(API_DELAY)

    # ══════ PHASE 2: VERIFY LAUNCHPAD ══════
    print(f"\n{'─'*70}")
    print(f"  PHASE 2: VERIFY LAUNCHPAD ({LAUNCHPAD})")
    print(f"{'─'*70}")

    out = await cloud_cmd(client, LAUNCHPAD, "echo ALIVE && id")
    if "ALIVE" not in out:
        print(f"  FATAL: Launchpad not responding: {out}")
        return
    print(f"  Launchpad alive: {out[:80]}")
    await asyncio.sleep(API_DELAY)

    # Verify neighbor is reachable
    out = await cloud_cmd(client, LAUNCHPAD,
        f"(echo test | nc -w 3 {NEIGHBOR_IP} 5555 >/dev/null 2>&1 && echo OPEN) || echo CLOSED")
    print(f"  Neighbor {NEIGHBOR_IP}:5555 = {out}")
    if "OPEN" not in (out or ""):
        print(f"  FATAL: Neighbor not reachable from launchpad")
        return
    await asyncio.sleep(API_DELAY)

    # ══════ PHASE 3: FULL-PARTITION CLONE ══════
    print(f"\n{'─'*70}")
    print(f"  PHASE 3: FULL-PARTITION BACKUP FROM {NEIGHBOR_IP}")
    print(f"{'─'*70}")

    manifest = await full_partition_backup(client, LAUNCHPAD, NEIGHBOR_IP)
    if not manifest or manifest.status != "backed_up":
        print(f"  FATAL: Backup failed. Status: {manifest.status if manifest else 'None'}")
        return

    print(f"\n  Backup complete: {manifest.partition_tar_size_mb:.1f}MB")
    print(f"  Accounts: {manifest.accounts}")
    print(f"  Third-party apps: {len(manifest.third_party_pkgs)}")

    # ══════ PHASE 4: RESTORE TO TARGET ══════
    print(f"\n{'─'*70}")
    print(f"  PHASE 4: RESTORE TO {TARGET}")
    print(f"{'─'*70}")

    print("  Waiting 10s before restore...")
    await asyncio.sleep(10)

    await full_partition_restore(client, TARGET, NEIGHBOR_IP)

    # ══════ PHASE 5: VERIFY ══════
    print(f"\n{'─'*70}")
    print(f"  PHASE 5: VERIFY CLONE")
    print(f"{'─'*70}")

    await asyncio.sleep(5)
    results = await verify_clone(client, TARGET, NEIGHBOR_IP)

    # ══════ SUMMARY ══════
    elapsed = time.time() - t0
    print(f"\n{'=' * 70}")
    print(f"  RESET & CLONE COMPLETE — {elapsed:.0f}s")
    print(f"  Target: {TARGET}")
    print(f"  Source: {NEIGHBOR_IP}")
    if results:
        print(f"  Verification: {results.get('overall', 'N/A')}")
    print(f"{'=' * 70}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
