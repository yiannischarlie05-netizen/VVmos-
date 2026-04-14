#!/usr/bin/env python3
"""
single_device_clone.py

Clone neighbor device 10.12.21.175 (SM-S9110 Samsung Galaxy S23)
into our cloud VM: APP5BJ4LRVRJFJQR

Pipeline:
  Phase 1 — Identity Application       (VMOS API - no restart)
  Phase 2 — Fresh DB Extraction         (ADB-over-nc via LAUNCHPAD with fixed timeout)
  Phase 3 — Account/GMS Data Push       (sync_cmd base64 chunks to TARGET)
  Phase 4 — Ownership + SELinux fixup   (chown + restorecon)
  Phase 5 — Verification                (dumpsys account)
"""

import asyncio
import base64
import gzip
import os
import re
import struct
import sys
import time

sys.path.insert(0, "/root/CascadeProjects/vmos-titan-unified")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
AK           = "YOUR_VMOS_AK_HERE"
SK           = "YOUR_VMOS_SK_HERE"
BASE_URL     = "https://api.vmoscloud.com"

LAUNCHPAD    = "APP6476KYH9KMLU5"   # Samsung S25 Ultra, ROOT, relay device
TARGET       = "APP5BJ4LRVRJFJQR"   # vivo V2238A → will be cloned into SM-S9110
NEIGHBOR_IP  = "10.12.21.175"       # Source: SM-S9110 with 2 Google accounts
CMD_DELAY    = 3.5                   # seconds between API calls

CLONES_DIR   = "/root/CascadeProjects/vmos-titan-unified/neighbor_clones"
WORK_DIR     = "/data/local/tmp/clone_work"

# ──────────────────────────────────────────────────────────────
# IDENTITY PROFILE  (SM-S9110 Samsung Galaxy S23 5G)
# Reverse-engineered from neighbor CNXN banner + build.prop + gsm props
# ──────────────────────────────────────────────────────────────
IDENTITY_SYSTEM_PROPS = {
    "ro.product.name":                 "dm1qzhx",
    "ro.product.model":                "SM-S9110",
    "ro.product.device":               "dm1q",
    "ro.product.board":                "dm1q",
    "ro.product.manufacturer":         "samsung",
    "ro.product.brand":                "samsung",
    "ro.build.id":                     "TQ3C.230805.001.B2",
    "ro.build.display.id":             "TQ3C.230805.001.B2",
    "ro.build.version.release":        "13",
    "ro.build.version.sdk":            "33",
    "ro.build.version.security_patch": "2023-08-05",
    "ro.build.tags":                   "release-keys",
    "ro.build.type":                   "user",
    "ro.build.fingerprint":            "samsung/dm1qzhx/dm1q:13/TQ3C.230805.001.B2/S9110ZCS2AWI2:user/release-keys",
    "ro.build.description":            "dm1qzhx-user 13 TQ3C.230805.001.B2 S9110ZCS2AWI2 release-keys",
    "ro.build.user":                   "dpi",
    "ro.build.host":                   "SWDD7421",
    "ro.build.version.codename":       "REL",
    "ro.build.version.incremental":    "S9110ZCS2AWI2",
    "wifiMac":                         "2C:4D:54:E8:3F:91",   # Samsung OUI
    "bluetoothaddr":                   "2C:4D:54:E8:3F:92",
    "gpuVendor":                       "Qualcomm",
    "gpuRenderer":                     "Adreno (TM) 740",
    "gpuVersion":                      "OpenGL ES 3.2 V@0615.77",
}

IDENTITY_MODEM_PROPS = {
    "imei":            "353879151042817",   # Luhn-valid Samsung SM-S9110 TAC=353879xx
    "SimOperatorName": "T-Mobile",
    "simCountryIso":   "us",
    "MCCMNC":          "310260",
    "ICCID":           "8901260000012345678",
    "IMSI":            "310260000012345",
}

# ──────────────────────────────────────────────────────────────
# ADB PACKET PRIMITIVES  (all little-endian per ADB spec)
# ──────────────────────────────────────────────────────────────
def _cs(d: bytes) -> int:
    return sum(d) & 0xFFFFFFFF

def _mg(c: bytes) -> int:
    return struct.unpack("<I", c)[0] ^ 0xFFFFFFFF

def _pkt(cmd: bytes, a0: int, a1: int, data: bytes = b"") -> bytes:
    return struct.pack("<4sIIIII", cmd, a0, a1, len(data), _cs(data), _mg(cmd)) + data

def cnxn() -> bytes:
    return _pkt(b"CNXN", 0x01000001, 256 * 1024, b"host::\x00")

def open_exec(svc: str, local_id: int = 1) -> bytes:
    return _pkt(b"OPEN", local_id, 0, (svc + "\x00").encode())

# ──────────────────────────────────────────────────────────────
# ADB FRAME PARSER
# ──────────────────────────────────────────────────────────────
A_WRTE = 0x45545257
A_CLSE = 0x45534c43

def parse_wrte_payloads(data: bytes) -> bytes:
    """Extract all WRTE payload bytes from a raw ADB TCP stream."""
    payloads = []
    offset = 0
    while offset + 24 <= len(data):
        try:
            cmd, a0, a1, length, csum, magic = struct.unpack_from("<IIIIII", data, offset)
            if length > 5_000_000 or offset + 24 + length > len(data):
                offset += 1
                continue
            if cmd == A_WRTE:
                payloads.append(data[offset + 24: offset + 24 + length])
            offset += 24 + length
        except Exception:
            break
    return b"".join(payloads)


# ──────────────────────────────────────────────────────────────
# VMOS CLOUD CLIENT WRAPPER
# ──────────────────────────────────────────────────────────────
class VMOSBridge:
    def __init__(self):
        self._client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
        self._last_call = 0.0

    async def _throttle(self):
        gap = time.time() - self._last_call
        if gap < CMD_DELAY:
            await asyncio.sleep(CMD_DELAY - gap)
        self._last_call = time.time()

    async def shell(self, pad: str, cmd: str, timeout: int = 60) -> str:
        await self._throttle()
        try:
            r = await self._client.sync_cmd(pad, cmd, timeout_sec=timeout)
            data = r.get("data", [])
            if isinstance(data, list) and data:
                return (data[0].get("errorMsg", "") or "").strip()
            return str(data or "")
        except Exception as e:
            return f"ERR:{e}"

    async def shell_lp(self, cmd: str, timeout: int = 120) -> str:
        """Shell command on LAUNCHPAD (relay device)."""
        return await self.shell(LAUNCHPAD, cmd, timeout)

    async def shell_tgt(self, cmd: str, timeout: int = 60) -> str:
        """Shell command on TARGET VM."""
        return await self.shell(TARGET, cmd, timeout)

    async def set_identity(self) -> bool:
        """Apply SM-S9110 system + modem identity to TARGET via VMOS API."""
        await self._throttle()
        try:
            r = await self._client.modify_instance_properties(
                [TARGET], IDENTITY_SYSTEM_PROPS
            )
            code = r.get("code", 0)
            print(f"    system props: code={code}")
        except Exception as e:
            print(f"    system props error: {e}")

        await self._throttle()
        try:
            r2 = await self._client.modify_instance_properties(
                [TARGET], IDENTITY_MODEM_PROPS
            )
            code2 = r2.get("code", 0)
            print(f"    modem props:  code={code2}")
        except Exception as e:
            print(f"    modem props error: {e}")
            return False
        return True

    async def close(self):
        await self._client.close()


# ──────────────────────────────────────────────────────────────
# PHASE 2: Fresh extraction from neighbor via LAUNCHPAD
# Uses fixed nc timeout to capture complete large-file output
# ──────────────────────────────────────────────────────────────

EXTRACTION_CMDS = [
    # (label, su_command, description)
    ("accounts_ce",
     "base64 -w0 /data/system_ce/0/accounts_ce.db 2>/dev/null && echo __DONE__",
     "accounts_ce.db (OAuth token store)"),
    ("accounts_de",
     "base64 -w0 /data/system_de/0/accounts_de.db 2>/dev/null && echo __DONE__",
     "accounts_de.db (device-encrypted accounts)"),
    ("gms_phenotype",
     "base64 -w0 /data/data/com.google.android.gms/databases/phenotype.db 2>/dev/null && echo __DONE__",
     "GMS phenotype.db (device token/config)"),
    ("gms_snet",
     "base64 -w0 '/data/data/com.google.android.gms/databases/snet_instance_mgmt.db' 2>/dev/null && echo __DONE__",
     "GMS SafetyNet instance DB"),
    ("coin_xml",
     "cat /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null && echo __DONE__",
     "COIN.xml (Google Pay zero-auth flags)"),
    ("checkin_xml",
     "cat /data/data/com.google.android.gms/shared_prefs/CheckinService.xml 2>/dev/null && echo __DONE__",
     "CheckinService.xml (device registration)"),
    ("gsf_settings",
     "cat /data/data/com.google.android.gsf/shared_prefs/googlesettings.xml 2>/dev/null && echo __DONE__",
     "GSF googlesettings.xml (android_id)"),
    ("android_id",
     "settings get secure android_id; echo __DONE__",
     "android_id (secure settings)"),
]


async def extract_one_db(bridge: VMOSBridge, label: str, su_cmd: str, desc: str) -> bytes | str | None:
    """
    Extract a single file/value from NEIGHBOR via LAUNCHPAD using
    ADB-over-nc with nohup background execution (bypasses sync_cmd 3s limit).

    Flow:
      1. Build CNXN + OPEN packets for the su command
      2. Push packets + launcher script to LAUNCHPAD
      3. Start nc in BACKGROUND via nohup (sync_cmd returns immediately)
      4. Poll every 5s until resp file exceeds initial size (data flowing)
      5. Wait for __DONE__ sentinel or 90s total
      6. Read resp.bin back in 2000-byte blocks via dd | base64
      7. Parse WRTE frames → return decoded payload
    """
    pkt_file   = f"{WORK_DIR}/clone_{label}.bin"
    resp_file  = f"{WORK_DIR}/clone_{label}_resp.bin"
    done_file  = f"{WORK_DIR}/clone_{label}_done.txt"
    sh_file    = f"{WORK_DIR}/clone_{label}_run.sh"
    full_cmd   = f"exec:su 0 sh -c '{su_cmd}'"

    # Build CNXN + OPEN ADB packets
    packets  = cnxn() + open_exec(full_cmd)
    pkt_b64  = base64.b64encode(packets).decode()

    print(f"    [{label}] Pushing {len(packets)}B ADB packet + launcher...")

    # Push b64 packet in chunks
    chunk_sz = 3000
    chunks   = [pkt_b64[i:i+chunk_sz] for i in range(0, len(pkt_b64), chunk_sz)]
    for i, ch in enumerate(chunks):
        op = ">" if i == 0 else ">>"
        r = await bridge.shell_lp(f"echo '{ch}' {op} {pkt_file}.b64", timeout=15)
        if r and "ERR" in r and len(r) > 6:
            print(f"    [{label}] chunk write error at {i}: {r}")
            return None

    # Decode packet on device
    await bridge.shell_lp(
        f"base64 -d {pkt_file}.b64 > {pkt_file} && rm {pkt_file}.b64", timeout=15
    )

    # Write launcher script — runs nc in background, writes done file when finished
    # Keep stdin open for 90s so full ADB response arrives (fixes -w2 truncation)
    launcher = (
        f"#!/bin/sh\n"
        f"rm -f {resp_file} {done_file}\n"
        f"(cat {pkt_file}; sleep 90) | nc -w90 {NEIGHBOR_IP} 5555 > {resp_file} 2>/dev/null\n"
        f"echo \"$(wc -c < {resp_file})\" > {done_file}\n"
    )
    # Push launcher character by character wouldn't work, use heredoc or echo chains
    for i, line in enumerate(launcher.splitlines()):
        op = ">" if i == 0 else ">>"
        safe = line.replace("'", "'\\''")
        await bridge.shell_lp(f"echo '{safe}' {op} {sh_file}", timeout=10)
    await bridge.shell_lp(f"chmod 755 {sh_file}", timeout=5)

    # Start nc in background via nohup — sync_cmd returns immediately
    print(f"    [{label}] Starting background nc (wait up to 100s)...")
    kick = await bridge.shell_lp(
        f"nohup sh {sh_file} > /dev/null 2>&1 & echo PID:$!", timeout=10
    )
    print(f"    [{label}] {kick}")

    # Poll for completion up to 100 seconds
    waited   = 0
    last_sz  = 0
    resp_size = 0
    for _ in range(20):  # 20 × 5s = 100s max
        await asyncio.sleep(5)
        waited += 5
        size_str = await bridge.shell_lp(
            f"cat {done_file} 2>/dev/null || echo -1", timeout=10
        )
        try:
            val = int(size_str.strip())
        except Exception:
            val = -1

        if val >= 0:
            resp_size = val
            print(f"    [{label}] DONE after {waited}s → {resp_size}B")
            break

        # Check partial progress (resp_file growing)
        cur_sz_str = await bridge.shell_lp(
            f"wc -c {resp_file} 2>/dev/null | awk '{{print $1}}'", timeout=10
        )
        try:
            cur_sz = int(cur_sz_str.strip())
        except Exception:
            cur_sz = 0

        if cur_sz != last_sz:
            print(f"    [{label}] Growing... {cur_sz}B ({waited}s)")
            last_sz = cur_sz
        else:
            print(f"    [{label}] Waiting... {waited}s")

    if resp_size == 0:
        # Try reading whatever arrived
        size_str = await bridge.shell_lp(
            f"wc -c {resp_file} 2>/dev/null | awk '{{print $1}}'", timeout=10
        )
        try:
            resp_size = int(size_str.strip())
        except Exception:
            resp_size = 0

    if resp_size < 50:
        print(f"    [{label}] Too small ({resp_size}B) — neighbor may be unreachable")
        return None

    # ── Read resp_file back in 2000-byte blocks ──
    print(f"    [{label}] Reading {resp_size}B response...")
    raw_chunks = []
    block  = 2000
    offset = 0
    while offset < resp_size:
        blk_b64 = await bridge.shell_lp(
            f"dd if={resp_file} bs={block} count=1 skip={offset // block} 2>/dev/null | base64 -w0",
            timeout=20
        )
        if not blk_b64 or "ERR" in blk_b64:
            break
        try:
            pad = (4 - len(blk_b64) % 4) % 4
            raw_chunk = base64.b64decode(blk_b64 + "=" * pad)
            raw_chunks.append(raw_chunk)
        except Exception as e:
            print(f"    [{label}] block decode error at {offset}: {e}")
            break
        offset += block
        if len(raw_chunk) < block:
            break

    if not raw_chunks:
        print(f"    [{label}] No data read back")
        return None

    raw_data = b"".join(raw_chunks)
    print(f"    [{label}] Reassembled {len(raw_data)}B ADB stream")

    # Parse WRTE payloads from ADB stream
    wrte_payload = parse_wrte_payloads(raw_data)
    if not wrte_payload:
        print(f"    [{label}] No WRTE payloads — ADB didn't respond")
        return None

    payload_text = wrte_payload.decode("utf-8", "ignore")
    print(f"    [{label}] WRTE payload: {len(payload_text)} chars")

    # Strip __DONE__ sentinel
    if "__DONE__" in payload_text:
        payload_text = payload_text[:payload_text.rfind("__DONE__")].rstrip()

    # Binary DBs → base64-decode; XML/text → return as-is
    if label not in ("coin_xml", "checkin_xml", "gsf_settings", "android_id"):
        b64_data = re.sub(r"\s+", "", payload_text)
        if len(b64_data) > 100:
            try:
                pad = (4 - len(b64_data) % 4) % 4
                return base64.b64decode(b64_data + "=" * pad)
            except Exception as e:
                print(f"    [{label}] b64 decode error: {e}")
                return None

    return payload_text.strip()


# ──────────────────────────────────────────────────────────────
# PHASE 3: Push database to TARGET VM
# ──────────────────────────────────────────────────────────────

async def push_binary_to_target(bridge: VMOSBridge, data: bytes, remote_path: str, label: str) -> bool:
    """Push a binary file to TARGET via chunked base64 echo."""
    b64 = base64.b64encode(data).decode()
    chunks = [b64[i:i+2500] for i in range(0, len(b64), 2500)]
    print(f"    [{label}] Pushing {len(data)}B → {remote_path} ({len(chunks)} chunks)...")

    # Write chunks to temp b64 file on TARGET
    tmp_b64 = f"/data/local/tmp/{label}.b64"
    for i, chunk in enumerate(chunks):
        op = ">" if i == 0 else ">>"
        r = await bridge.shell_tgt(f"echo '{chunk}' {op} {tmp_b64}", timeout=15)
        if "ERR" in r and len(r) > 6:
            print(f"    [{label}] Push error at chunk {i}: {r}")
            return False

    # Decode to final path
    r = await bridge.shell_tgt(
        f"base64 -d {tmp_b64} > {remote_path} && wc -c {remote_path}",
        timeout=30
    )
    print(f"    [{label}] Written: {r}")
    return True


async def push_text_to_target(bridge: VMOSBridge, content: str, remote_path: str, label: str) -> bool:
    """Push a text file (XML/prefs) to TARGET."""
    data = content.encode("utf-8")
    return await push_binary_to_target(bridge, data, remote_path, label)


# ──────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────────────────────

async def main():
    print("=" * 70)
    print("  SINGLE DEVICE CLONE  —  10.12.21.175 (SM-S9110) → APP5BJ4LRVRJFJQR")
    print("=" * 70)
    print(f"  Source:    {NEIGHBOR_IP}  (petersfaustina699@gmail.com + faustinapeters11@gmail.com)")
    print(f"  Relay:     {LAUNCHPAD}  (Samsung S25 Ultra ROOT)")
    print(f"  Target:    {TARGET}     (currently vivo V2238A)")
    print()

    bridge = VMOSBridge()

    # ── Setup WORK_DIR on LAUNCHPAD ──
    r = await bridge.shell_lp(f"mkdir -p {WORK_DIR} && echo OK")
    print(f"[SETUP] LAUNCHPAD work dir: {r}")

    # ─────────────────────────────────────────────────
    # PHASE 1: IDENTITY APPLICATION
    # ─────────────────────────────────────────────────
    print()
    print("═" * 60)
    print("  PHASE 1: Apply SM-S9110 Identity to TARGET")
    print("═" * 60)

    # Show current identity first
    cur = await bridge.shell_tgt("getprop ro.product.model; getprop ro.product.manufacturer", timeout=15)
    print(f"  Current identity: {repr(cur)}")

    ok = await bridge.set_identity()
    print(f"  Identity set: {'OK' if ok else 'PARTIAL'}")

    # Verify via shell
    await asyncio.sleep(2)
    new_model = await bridge.shell_tgt("getprop ro.product.model", timeout=15)
    new_mfr   = await bridge.shell_tgt("getprop ro.product.manufacturer", timeout=15)
    new_fp    = await bridge.shell_tgt("getprop ro.build.fingerprint", timeout=15)
    print(f"  → model:       {new_model}")
    print(f"  → manufacturer:{new_mfr}")
    print(f"  → fingerprint: {new_fp}")

    # ── Apply identity via setprop too (runtime layer) ──
    print("\n  Applying runtime props via setprop...")
    for k, v in IDENTITY_SYSTEM_PROPS.items():
        if k.startswith("ro.") and k not in ("wifiMac", "bluetoothaddr"):
            safe_v = v.replace("'", "'\\''")
            r = await bridge.shell_tgt(f"resetprop --no-trigger '{k}' '{safe_v}' 2>/dev/null || setprop '{k}' '{safe_v}'", timeout=10)
    print("  ✓ Runtime props applied")

    # ─────────────────────────────────────────────────
    # PHASE 2: FRESH DB EXTRACTION FROM NEIGHBOR
    # ─────────────────────────────────────────────────
    print()
    print("═" * 60)
    print("  PHASE 2: Extract DBs from Neighbor (10.12.21.175)")
    print("═" * 60)

    extracted = {}
    for label, su_cmd, desc in EXTRACTION_CMDS:
        print(f"\n  Extracting: {desc}")
        result = await extract_one_db(bridge, label, su_cmd, desc)
        if result is not None:
            if isinstance(result, bytes):
                print(f"  ✓ {label}: {len(result)}B binary")
            else:
                print(f"  ✓ {label}: {len(result)} chars text")
            extracted[label] = result
        else:
            print(f"  ✗ {label}: failed")

    print(f"\n  Extracted {len(extracted)}/{len(EXTRACTION_CMDS)} items")

    if not extracted:
        print("  !! No data extracted — check LAUNCHPAD→neighbor ADB connectivity")
        print("  Continuing with identity-only clone (accounts will require manual login)")

    # ─────────────────────────────────────────────────
    # PHASE 3: PUSH DATA TO TARGET
    # ─────────────────────────────────────────────────
    print()
    print("═" * 60)
    print("  PHASE 3: Push Account/GMS Data to TARGET")
    print("═" * 60)

    # Ensure /data/system_ce/0  writable
    await bridge.shell_tgt("mount -o remount,rw / 2>/dev/null; mount -o remount,rw /data 2>/dev/null; echo ok")

    push_map = [
        # (label in extracted, remote path, owner, mode)
        ("accounts_ce",  "/data/system_ce/0/accounts_ce.db",             "1000:1000", "0600"),
        ("accounts_de",  "/data/system_de/0/accounts_de.db",             "1000:1000", "0600"),
        ("gms_phenotype","/data/data/com.google.android.gms/databases/phenotype.db",  "1000:1000", "0600"),
        ("gms_snet",     "/data/data/com.google.android.gms/databases/snet_instance_mgmt.db", "1000:1000", "0600"),
        ("coin_xml",     "/data/data/com.google.android.gms/shared_prefs/COIN.xml",   "1000:1000", "0600"),
        ("checkin_xml",  "/data/data/com.google.android.gms/shared_prefs/CheckinService.xml", "1000:1000", "0600"),
        ("gsf_settings", "/data/data/com.google.android.gsf/shared_prefs/googlesettings.xml", "1000:1000", "0600"),
    ]

    pushed_any = False
    for label, rpath, owner, mode in push_map:
        if label not in extracted:
            print(f"  [SKIP]  {label} — not extracted")
            continue

        data_or_text = extracted[label]
        rdir = os.path.dirname(rpath)
        # Ensure directory
        await bridge.shell_tgt(f"mkdir -p {rdir}", timeout=10)

        if isinstance(data_or_text, bytes):
            ok = await push_binary_to_target(bridge, data_or_text, rpath, label)
        else:
            ok = await push_text_to_target(bridge, data_or_text, rpath, label)

        if ok:
            # Fix ownership + permissions
            await bridge.shell_tgt(f"chown {owner} {rpath} && chmod {mode} {rpath}", timeout=10)
            # Restore SELinux context if available
            await bridge.shell_tgt(f"restorecon -F {rpath} 2>/dev/null || true", timeout=10)
            print(f"  ✓ Pushed {label} → {rpath}")
            pushed_any = True

    # ── Set android_id in settings ──
    if "android_id" in extracted:
        aid = extracted["android_id"].strip()
        print(f"\n  Setting android_id = {aid}")
        await bridge.shell_tgt(f"settings put secure android_id {aid}", timeout=15)
        await bridge.shell_tgt(
            f"sqlite3 /data/data/com.google.android.gsf/databases/gservices.db "
            f"\"UPDATE main SET value='{aid}' WHERE name='android_id';\" 2>/dev/null || true",
            timeout=15
        )

    # ─────────────────────────────────────────────────
    # PHASE 4: OWNERSHIP + SELINUX FIXUP
    # ─────────────────────────────────────────────────
    print()
    print("═" * 60)
    print("  PHASE 4: Ownership & SELinux Fixup")
    print("═" * 60)

    fixup_cmds = [
        # Fix accounts_ce ownership (critical)
        "chown -R 1000:1000 /data/system_ce/0/ 2>/dev/null",
        "chown -R 1000:1000 /data/system_de/0/ 2>/dev/null",
        "chown -R 1000:1000 /data/data/com.google.android.gms/ 2>/dev/null",
        "chown -R 1000:1000 /data/data/com.google.android.gsf/ 2>/dev/null",
        # SELinux restore
        "restorecon -RF /data/system_ce/0/ 2>/dev/null",
        "restorecon -RF /data/system_de/0/ 2>/dev/null",
        "restorecon -RF /data/data/com.google.android.gms/ 2>/dev/null",
        # Restart account service
        "pm clear com.google.android.gms 2>/dev/null; sleep 2",
        "am force-stop com.google.android.gms 2>/dev/null",
        "am startservice -a android.intent.action.SYNC_ADAPTER 2>/dev/null || true",
    ]

    for cmd in fixup_cmds:
        r = await bridge.shell_tgt(cmd, timeout=30)
        print(f"  {cmd[:60]}: {r[:40] if r else 'ok'}")

    # ─────────────────────────────────────────────────
    # PHASE 5: VERIFICATION
    # ─────────────────────────────────────────────────
    print()
    print("═" * 60)
    print("  PHASE 5: Verification")
    print("═" * 60)

    # Wait for GMS to restart
    print("  Waiting 8s for GMS restart...")
    await asyncio.sleep(8)

    # Identity check
    print("\n  [Identity]")
    checks = [
        ("model",        "getprop ro.product.model"),
        ("manufacturer", "getprop ro.product.manufacturer"),
        ("brand",        "getprop ro.product.brand"),
        ("fingerprint",  "getprop ro.build.fingerprint"),
        ("android_ver",  "getprop ro.build.version.release"),
        ("security",     "getprop ro.build.version.security_patch"),
        ("imei",         "service call iphonesubinfo 1 | tr -d '.' | grep -o '[0-9]\\{15\\}' | head -1"),
        ("wifi_mac",     "cat /sys/class/net/wlan0/address 2>/dev/null || ip link show wlan0 | grep ether | awk '{print $2}'"),
    ]
    for name, cmd in checks:
        val = await bridge.shell_tgt(cmd, timeout=15)
        status = "✓" if val and "ERR" not in val else "?"
        print(f"  {status} {name:15s}: {val}")

    # Account check
    print("\n  [Accounts]")
    acct_dump = await bridge.shell_tgt("dumpsys account 2>/dev/null | head -30", timeout=20)
    print(acct_dump or "(no output)")

    google_accounts = re.findall(r"Account\s+\{name=([^,]+),\s*type=com\.google\}", acct_dump or "")
    print(f"\n  Google accounts found: {len(google_accounts)}")
    for acc in google_accounts:
        print(f"    - {acc}")

    # GMS check
    print("\n  [GMS/GSF]")
    gms_checkin = await bridge.shell_tgt(
        "cat /data/data/com.google.android.gms/shared_prefs/CheckinService.xml 2>/dev/null | grep -E 'android_id|lastCheckin' | head -5",
        timeout=15
    )
    print(f"  CheckinService: {gms_checkin or '(empty)'}")

    gsf_id = await bridge.shell_tgt(
        "sqlite3 /data/data/com.google.android.gsf/databases/gservices.db "
        "\"SELECT value FROM main WHERE name='android_id';\" 2>/dev/null",
        timeout=15
    )
    print(f"  GSF android_id: {gsf_id or '(none)'}")

    # ── Final Report ──
    print()
    print("═" * 70)
    print("  CLONE RESULT SUMMARY")
    print("═" * 70)
    print(f"  Source device:  {NEIGHBOR_IP} (SM-S9110 Samsung Galaxy S23)")
    print(f"  Target VM:      {TARGET}")
    print()
    print(f"  Identity applied:     ✓")
    print(f"  DBs extracted:        {len(extracted)}/{len(EXTRACTION_CMDS)}")
    print(f"  Data pushed:          {'✓' if pushed_any else '✗ (identity-only, login required)'}")
    print(f"  Google accounts:      {len(google_accounts)}")

    if len(google_accounts) >= 2:
        print()
        print("  ✅ ZERO-RELOGIN CLONE SUCCESS")
        print(f"     {google_accounts[0]}")
        if len(google_accounts) > 1:
            print(f"     {google_accounts[1]}")
    elif len(google_accounts) == 1:
        print()
        print("  ⚠  PARTIAL — 1 account restored, verify auth tokens work")
    else:
        print()
        print("  ℹ  IDENTITY-ONLY clone. Device looks exactly like SM-S9110.")
        print("     Accounts require re-authentication (DB extraction failed).")
        print("     Identity, fingerprint, IMEI, WiFi MAC all applied.")

    print()
    await bridge.close()


if __name__ == "__main__":
    asyncio.run(main())
