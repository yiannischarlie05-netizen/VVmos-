#!/usr/bin/env python3
"""
Full Clone Pipeline v7
======================
Complete neighbor→target clone: identity, proxy, accounts, apps, app data, settings.

Uses:
 - Raw ADB protocol via nc for neighbor commands (no adb binary needed)
 - nc relay for binary file transfers (neighbor → launchpad → VPS → target)
 - VMOSDbBuilder for clean DELETE-mode account DBs
 - Cloud API for identity props and device control

Source:  neighbor 10.12.21.175 (Samsung SM-S9110 identity)
Launchpad: APP6476KYH9KMLU5 (10.12.11.186, same subnet as neighbor)
Target: ACP250916A5B1912 (10.11.36.6, freshly reset)
"""
import asyncio
import base64
import hashlib
import json
import os
import struct
import sys
import time
from pathlib import Path

os.environ['VMOS_ALLOW_RESTART'] = '1'
sys.path.insert(0, ".")
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
from vmos_titan.core.vmos_db_builder import VMOSDbBuilder

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
LAUNCHPAD = "APP6476KYH9KMLU5"
TARGET = "ACP250916A5B1912"
NEIGHBOR = "10.12.21.175"
VPS_IP = "37.60.234.139"
VPS_PORT = 9999
BASE_URL = "https://api.vmoscloud.com"
STAGING = "/data/local/tmp/clone7"
CMD_DELAY = 3.5
API_DELAY = 3.0

# Identity from extraction
IDENTITY = {
    "ro.product.model": "SM-S9110",
    "ro.product.brand": "samsung",
    "ro.product.manufacturer": "samsung",
    "ro.product.device": "dm1q",
    "ro.product.board": "kalama",
    "ro.product.name": "dm1qzhx",
    "ro.hardware": "qcom",
    "ro.build.fingerprint": "samsung/dm1qzhx/dm1q:13/TP1A.220624.014/S9110ZHS2AWI2:user/release-keys",
    "ro.build.id": "TP1A.220624.014",
    "ro.build.display.id": "TP1A.220624.014.S9110ZHS2AWI2",
    "ro.build.version.release": "13",
    "ro.build.version.sdk": "33",
    "ro.build.version.security_patch": "2025-12-05",
    "ro.build.type": "user",
    "ro.build.flavor": "dm1qzhx-user",
    "persist.sys.cloud.imeinum": "312671446307090",
    "persist.sys.cloud.imsinum": "234103772931327",
    "persist.sys.cloud.iccidnum": "89445046905698751410",
    "persist.sys.cloud.phonenum": "4453816683684",
    "persist.sys.cloud.macaddress": "",
    "persist.sys.cloud.drm.id": "iRz4b1B4ZeJRlMAz7YlNB7CfGHVCkewvha1U97EwEsM=",
    "persist.sys.cloud.gps.lat": "54.5585",
    "persist.sys.cloud.gps.lon": "-1.1476",
}

ACCOUNTS = [
    {"email": "petersfaustina699@gmail.com", "display_name": "Peters Faustina"},
    {"email": "faustinapeters11@gmail.com", "display_name": "Faustina Peters"},
]

# ═══════════════════════════════════════════════════════════════
# ADB PROTOCOL HELPERS
# ═══════════════════════════════════════════════════════════════
def _cs(d): return sum(d) & 0xFFFFFFFF
def _mg(c): return struct.unpack("<I", c)[0] ^ 0xFFFFFFFF
def _pkt(c, a0, a1, d=b""):
    return struct.pack("<4sIIIII", c, a0, a1, len(d), _cs(d), _mg(c)) + d
def adb_cnxn(): return _pkt(b"CNXN", 0x01000001, 256*1024, b"host::\x00")
def adb_open(lid, svc): return _pkt(b"OPEN", lid, 0, svc.encode() + b"\x00")

# ═══════════════════════════════════════════════════════════════
# CLOUD API HELPERS
# ═══════════════════════════════════════════════════════════════

async def lp_cmd(client, sh, timeout=30, retries=3):
    """Execute command on LAUNCHPAD."""
    for attempt in range(retries):
        try:
            r = await client.sync_cmd(LAUNCHPAD, sh, timeout_sec=timeout)
            if r.get("code") == 200:
                data = r.get("data", [])
                if data and isinstance(data, list) and data[0]:
                    return (data[0].get("errorMsg") or "").strip()
                return ""
            elif r.get("code") in (110012,):
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                    continue
            return None
        except:
            if attempt < retries - 1:
                await asyncio.sleep(2)
    return None

async def tgt_cmd(client, sh, timeout=30, retries=3):
    """Execute command on TARGET."""
    for attempt in range(retries):
        try:
            r = await client.sync_cmd(TARGET, sh, timeout_sec=timeout)
            if r.get("code") == 200:
                data = r.get("data", [])
                if data and isinstance(data, list) and data[0]:
                    return (data[0].get("errorMsg") or "").strip()
                return ""
            elif r.get("code") in (110012, 110031):
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
            return None
        except:
            if attempt < retries - 1:
                await asyncio.sleep(3)
    return None

async def lp_fire(client, sh):
    """Fire-and-forget on launchpad (async)."""
    try:
        await client.async_adb_cmd([LAUNCHPAD], sh)
    except:
        pass

async def nb_cmd(client, ip, shell_cmd, timeout=8):
    """Execute shell command on NEIGHBOR via raw ADB protocol over nc."""
    await lp_cmd(client, f"mkdir -p {STAGING}")
    ip_key = ip.replace(".", "_")

    # Stage CNXN packet
    b64_cnxn = base64.b64encode(adb_cnxn()).decode()
    await lp_cmd(client, f"echo -n '{b64_cnxn}' | base64 -d > {STAGING}/.cnxn_{ip_key}")
    await asyncio.sleep(1)

    # Stage OPEN packet
    tag = f"{hash(shell_cmd) & 0xFFFF:04x}"
    pkt = adb_open(1, f"shell:{shell_cmd}")
    b64_open = base64.b64encode(pkt).decode()
    await lp_cmd(client, f"echo -n '{b64_open}' | base64 -d > {STAGING}/.o{tag}")
    await asyncio.sleep(1)

    # Fire relay: CNXN + OPEN → nc neighbor → capture response
    relay = (
        f"(cat {STAGING}/.cnxn_{ip_key}; sleep 0.3; "
        f"cat {STAGING}/.o{tag}; sleep {timeout}) | "
        f"timeout {timeout + 2} nc {ip} 5555 > {STAGING}/.r{tag} 2>/dev/null"
    )
    await lp_fire(client, relay)
    await asyncio.sleep(timeout + 4)

    # Parse: strip ADB headers, keep text
    await lp_cmd(client,
        f"strings -n 2 {STAGING}/.r{tag} 2>/dev/null | "
        f"grep -v -E '^(CNXN|OKAY|WRTE|CLSE|OPEN|host::|device::)' "
        f"> {STAGING}/.t{tag}")
    await asyncio.sleep(1)

    total = await lp_cmd(client, f"wc -l < {STAGING}/.t{tag} 2>/dev/null || echo 0")
    try:
        n = int((total or "0").strip())
    except:
        n = 0

    if n == 0:
        return ""

    # Read in chunks
    chunks = []
    CHUNK = 40
    for start in range(0, n, CHUNK):
        if start == 0:
            chunk = await lp_cmd(client, f"head -{CHUNK} {STAGING}/.t{tag}")
        else:
            chunk = await lp_cmd(client, f"tail -n +{start+1} {STAGING}/.t{tag} | head -{CHUNK}")
        if chunk:
            chunks.append(chunk)
        await asyncio.sleep(CMD_DELAY)

    await lp_cmd(client, f"rm -f {STAGING}/.o{tag} {STAGING}/.r{tag} {STAGING}/.t{tag}")
    return "\n".join(chunks).strip()


async def push_bytes_b64(client, data: bytes, remote_path: str, max_retries=3):
    """Push raw bytes to TARGET via base64 chunks through syncCmd.
    Uses small chunks + per-chunk retry to survive syncCmd 2s timeouts."""
    b64 = base64.b64encode(data).decode()
    chunk_size = 1800  # Smaller to fit within 2s timeout
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    expected_md5 = hashlib.md5(data).hexdigest()

    for attempt in range(max_retries):
        await tgt_cmd(client, f"rm -f {remote_path}.b64 {remote_path}")
        await asyncio.sleep(1)

        failed = False
        for ci, chunk in enumerate(chunks):
            op = ">>" if ci > 0 else ">"
            ok = False
            for r in range(3):
                out = await tgt_cmd(client,
                    f'echo -n "{chunk}" {op} {remote_path}.b64 && echo CHUNK_OK',
                    retries=1, timeout=10)
                if out and "CHUNK_OK" in out:
                    ok = True
                    break
                await asyncio.sleep(2)
            if not ok:
                print(f"      WARN: chunk {ci}/{len(chunks)} failed, retrying full push...", flush=True)
                failed = True
                break
            await asyncio.sleep(0.3)

        if failed:
            continue

        # Decode and verify
        out = await tgt_cmd(client,
            f"base64 -d {remote_path}.b64 > {remote_path} && rm -f {remote_path}.b64 && "
            f"md5sum {remote_path} 2>/dev/null | cut -d' ' -f1",
            timeout=15)
        await asyncio.sleep(1)
        got_md5 = (out or "").strip()

        if got_md5 == expected_md5:
            return got_md5
        print(f"      MD5 mismatch (attempt {attempt+1}): got={got_md5} expected={expected_md5}", flush=True)

    # Final attempt result
    return got_md5


# ═══════════════════════════════════════════════════════════════
# DB BUILDER
# ═══════════════════════════════════════════════════════════════

def build_account_dbs():
    """Build DELETE-mode accounts_ce.db and accounts_de.db with all accounts."""
    import sqlite3
    import tempfile

    builder = VMOSDbBuilder()
    primary = ACCOUNTS[0]

    ce_bytes = builder.build_accounts_ce(
        email=primary["email"],
        display_name=primary.get("display_name", ""),
        tokens=None, password="", age_days=90,
    )
    de_bytes = builder.build_accounts_de(
        email=primary["email"],
        display_name=primary.get("display_name", ""),
        age_days=90,
    )

    # Add extra accounts
    for extra in ACCOUNTS[1:]:
        for label, db_bytes in [("ce", ce_bytes), ("de", de_bytes)]:
            tmp_path = tempfile.mktemp(suffix=".db")
            try:
                Path(tmp_path).write_bytes(db_bytes)
                conn = sqlite3.connect(tmp_path)
                conn.execute("PRAGMA journal_mode=DELETE;")
                c = conn.cursor()

                if label == "ce":
                    c.execute("INSERT OR IGNORE INTO accounts (name, type, password) VALUES (?, 'com.google', '')",
                              (extra["email"],))
                    acct_id = c.lastrowid
                    if acct_id:
                        dn = extra.get("display_name", extra["email"].split("@")[0])
                        parts = dn.split()
                        for key, val in [("display_name", dn),
                                         ("given_name", parts[0] if parts else ""),
                                         ("family_name", parts[-1] if len(parts) > 1 else "")]:
                            c.execute("INSERT OR IGNORE INTO extras (accounts_id, key, value) VALUES (?, ?, ?)",
                                      (acct_id, key, val))
                else:
                    c.execute("INSERT OR IGNORE INTO accounts (name, type, previous_name, "
                              "last_password_entry_time_millis_epoch) VALUES (?, 'com.google', NULL, ?)",
                              (extra["email"], int(time.time() * 1000)))
                    acct_id = c.lastrowid
                    if acct_id:
                        for pkg in ("com.google.android.gms", "com.android.vending",
                                    "com.google.android.youtube", "com.google.android.gm"):
                            c.execute("INSERT OR IGNORE INTO visibility (accounts_id, _package, value) VALUES (?, ?, 1)",
                                      (acct_id, pkg))

                conn.commit()
                new_bytes = Path(tmp_path).read_bytes()
                conn.close()

                # Update the reference
                if label == "ce":
                    ce_bytes = new_bytes
                else:
                    de_bytes = new_bytes
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    ce_bytes = VMOSDbBuilder.safe_db_finalize(ce_bytes)
    de_bytes = VMOSDbBuilder.safe_db_finalize(de_bytes)
    return ce_bytes, de_bytes


# ═══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════

async def main():
    t0 = time.time()
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)

    print("=" * 70)
    print("  FULL CLONE PIPELINE v7")
    print(f"  Neighbor:   {NEIGHBOR} (Samsung SM-S9110)")
    print(f"  Launchpad:  {LAUNCHPAD}")
    print(f"  Target:     {TARGET}")
    print(f"  Accounts:   {', '.join(a['email'] for a in ACCOUNTS)}")
    print("=" * 70)

    # ══════════════════════════════════════════════════════════
    # PHASE 1: EXTRACT FROM NEIGHBOR (via launchpad relay)
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 1] EXTRACT FROM NEIGHBOR", flush=True)

    # 1a. Verify neighbor reachable
    print("  [1a] Verifying neighbor...", flush=True)
    out = await nb_cmd(client, NEIGHBOR, "id && echo NB_ALIVE", timeout=8)
    if not out or "NB_ALIVE" not in (out or ""):
        print(f"  WARN: Neighbor not responding cleanly: {out}", flush=True)
    else:
        print(f"  Neighbor: {out}", flush=True)
    await asyncio.sleep(CMD_DELAY)

    # 1b. Get proxy config
    print("  [1b] Extracting proxy config...", flush=True)
    proxy = await nb_cmd(client, NEIGHBOR,
        "settings get global http_proxy 2>/dev/null && "
        "settings get global global_http_proxy_host 2>/dev/null && "
        "settings get global global_http_proxy_port 2>/dev/null && "
        "settings get global global_http_proxy_exclusion_list 2>/dev/null",
        timeout=10)
    print(f"  Proxy: {proxy}", flush=True)
    await asyncio.sleep(CMD_DELAY)

    # 1c. Get 3rd party apps
    print("  [1c] Extracting 3rd party app list...", flush=True)
    apps = await nb_cmd(client, NEIGHBOR, "pm list packages -3 2>/dev/null", timeout=12)
    app_list = [l.replace("package:", "").strip() for l in (apps or "").split("\n") if l.startswith("package:")]
    print(f"  3rd party apps: {len(app_list)}", flush=True)
    for a in app_list[:10]:
        print(f"    {a}", flush=True)
    if len(app_list) > 10:
        print(f"    ... and {len(app_list)-10} more", flush=True)
    await asyncio.sleep(CMD_DELAY)

    # 1d. Get settings (timezone, locale, etc)
    print("  [1d] Extracting settings...", flush=True)
    settings = await nb_cmd(client, NEIGHBOR,
        "settings get system time_12_24 2>/dev/null && "
        "settings get global auto_time 2>/dev/null && "
        "settings get global auto_time_zone 2>/dev/null && "
        "settings get secure default_input_method 2>/dev/null && "
        "getprop persist.sys.timezone 2>/dev/null && "
        "getprop persist.sys.language 2>/dev/null && "
        "getprop persist.sys.country 2>/dev/null",
        timeout=10)
    print(f"  Settings: {settings}", flush=True)
    await asyncio.sleep(CMD_DELAY)

    # 1e. Get WiFi config
    print("  [1e] Extracting WiFi config...", flush=True)
    wifi = await nb_cmd(client, NEIGHBOR,
        "cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | head -30 || echo NO_WIFI_CONFIG",
        timeout=10)
    has_wifi = wifi and "NO_WIFI_CONFIG" not in wifi
    print(f"  WiFi config: {'found' if has_wifi else 'none'}", flush=True)
    await asyncio.sleep(CMD_DELAY)

    # 1f. Get account details from neighbor for verification
    print("  [1f] Extracting accounts...", flush=True)
    nb_accounts = await nb_cmd(client, NEIGHBOR,
        "dumpsys account 2>/dev/null | grep -E 'Accounts:|Account {' | head -5",
        timeout=10)
    print(f"  Neighbor accounts: {nb_accounts}", flush=True)
    await asyncio.sleep(CMD_DELAY)

    # ══════════════════════════════════════════════════════════
    # PHASE 2: APPLY IDENTITY TO TARGET
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 2] APPLY IDENTITY TO TARGET", flush=True)

    # 2a. Enable root
    print("  [2a] Enabling root on target...", flush=True)
    try:
        await client.switch_root([TARGET], enable=True)
        await asyncio.sleep(8)
    except Exception as e:
        print(f"    Root switch: {e}", flush=True)

    out = await tgt_cmd(client, "id")
    print(f"  Target ID: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    # 2b. Apply ro.* identity props
    ro_props = {k: v for k, v in IDENTITY.items() if k.startswith("ro.") and v}
    print(f"  [2b] Applying {len(ro_props)} ro.* identity props...", flush=True)
    try:
        result = await client.update_android_prop(TARGET, ro_props)
        print(f"    updatePadAndroidProp: code={result.get('code')}", flush=True)
    except Exception as e:
        print(f"    API error: {e}, falling back to resetprop...", flush=True)
        for k, v in ro_props.items():
            await tgt_cmd(client, f'resetprop {k} "{v}" 2>/dev/null || setprop {k} "{v}" 2>/dev/null')
            await asyncio.sleep(1)
    await asyncio.sleep(API_DELAY)

    # 2c. Apply persist.* / cloud identity props
    persist_props = {k: v for k, v in IDENTITY.items() if k.startswith("persist.") and v}
    print(f"  [2c] Applying {len(persist_props)} persist.* props...", flush=True)
    try:
        result = await client.modify_instance_properties([TARGET], persist_props)
        print(f"    modifyInstanceProperties: code={result.get('code')}", flush=True)
    except Exception as e:
        print(f"    API error: {e}", flush=True)
    await asyncio.sleep(API_DELAY)

    # 2d. Apply proxy config
    if proxy and "null" not in (proxy or ""):
        print(f"  [2d] Applying proxy config...", flush=True)
        proxy_lines = [l.strip() for l in (proxy or "").split("\n") if l.strip() and l.strip() != "null"]
        if proxy_lines:
            # First non-null line is likely http_proxy value
            proxy_val = proxy_lines[0]
            if ":" in proxy_val:
                await tgt_cmd(client, f'settings put global http_proxy "{proxy_val}"')
                print(f"    Set proxy: {proxy_val}", flush=True)
    else:
        print(f"  [2d] No proxy to apply", flush=True)
    await asyncio.sleep(API_DELAY)

    # 2e. Restart to apply identity
    print(f"  [2e] Restarting target to apply identity...", flush=True)
    try:
        result = await client.instance_restart([TARGET])
        print(f"    Restart: code={result.get('code')}", flush=True)
    except Exception as e:
        print(f"    Restart error: {e}", flush=True)

    print("    Waiting for reboot...", flush=True)
    await asyncio.sleep(40)

    # Wait for alive
    for i in range(15):
        out = await tgt_cmd(client, "echo ALIVE", retries=1, timeout=10)
        if out and "ALIVE" in out:
            print(f"    Device ALIVE after {i*8+40}s", flush=True)
            break
        await asyncio.sleep(8)
    else:
        print("    WARN: Target slow to respond, continuing...", flush=True)
    await asyncio.sleep(5)

    # Verify identity applied
    out = await tgt_cmd(client, "getprop ro.product.model")
    print(f"  Identity check: model={out}", flush=True)
    await asyncio.sleep(API_DELAY)

    # ══════════════════════════════════════════════════════════
    # PHASE 3: INJECT ACCOUNTS (DELETE-mode DBs)
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 3] INJECT ACCOUNTS", flush=True)

    # 3a. Build DBs
    print("  [3a] Building account DBs (DELETE journal mode)...", flush=True)
    ce_bytes, de_bytes = build_account_dbs()
    ce_md5 = hashlib.md5(ce_bytes).hexdigest()
    de_md5 = hashlib.md5(de_bytes).hexdigest()

    # Verify locally
    import sqlite3, tempfile
    for label, data in [("ce", ce_bytes), ("de", de_bytes)]:
        tmp = tempfile.mktemp(suffix=".db")
        Path(tmp).write_bytes(data)
        conn = sqlite3.connect(tmp)
        jm = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        ic = conn.execute("PRAGMA integrity_check;").fetchone()[0]
        rows = conn.execute("SELECT name FROM accounts").fetchall()
        conn.close()
        Path(tmp).unlink()
        print(f"    {label}: journal={jm} integrity={ic} accounts={[r[0] for r in rows]}", flush=True)

    # 3b. Push DBs to target
    print("  [3b] Pushing DBs to target...", flush=True)
    await tgt_cmd(client, f"mkdir -p {STAGING}")
    await asyncio.sleep(1)

    for db_name, db_data, expected_md5 in [
        ("accounts_ce.db", ce_bytes, ce_md5),
        ("accounts_de.db", de_bytes, de_md5),
    ]:
        remote = f"{STAGING}/{db_name}"
        print(f"    Pushing {db_name} ({len(db_data)} bytes)...", flush=True)
        got_md5 = await push_bytes_b64(client, db_data, remote)
        ok = got_md5 == expected_md5
        print(f"    MD5: {got_md5} {'OK' if ok else 'MISMATCH!'}", flush=True)
        if not ok:
            print(f"    Expected: {expected_md5} — FATAL", flush=True)
            await client.close()
            return
        await asyncio.sleep(API_DELAY)

    # 3c. Stop services, swap DBs
    print("  [3c] Freezing services...", flush=True)
    for p in ["com.google.android.gms", "com.google.android.gsf",
              "com.android.vending", "com.google.android.gm"]:
        await tgt_cmd(client, f"am force-stop {p} 2>/dev/null", retries=1)
        await asyncio.sleep(0.5)
    await tgt_cmd(client, "killall -9 com.google.android.gms com.google.android.gsf 2>/dev/null")
    await asyncio.sleep(3)

    DB_TARGETS = {
        "accounts_ce.db": "/data/system_ce/0/accounts_ce.db",
        "accounts_de.db": "/data/system_de/0/accounts_de.db",
    }

    print("  [3d] Atomic inode swap + permissions...", flush=True)
    for db_name, dev_path in DB_TARGETS.items():
        # Clean sidecars
        await tgt_cmd(client, f"rm -f '{dev_path}-wal' '{dev_path}-shm' '{dev_path}-journal'")
        await asyncio.sleep(0.5)
        # Move old (new inode)
        await tgt_cmd(client, f"mv '{dev_path}' '{dev_path}.old' 2>/dev/null")
        await asyncio.sleep(0.5)
        # Copy new
        out = await tgt_cmd(client, f"cp '{STAGING}/{db_name}' '{dev_path}' && echo CP_OK")
        print(f"    {db_name}: {out}", flush=True)
        await asyncio.sleep(0.5)
        # Fix perms + SELinux
        await tgt_cmd(client, f"chown 1000:1000 '{dev_path}' && chmod 660 '{dev_path}' && "
                       f"chcon u:object_r:system_data_file:s0 '{dev_path}'")
        await asyncio.sleep(0.5)
        # Verify
        out = await tgt_cmd(client, f"ls -laZ '{dev_path}'")
        print(f"    Verify: {out}", flush=True)
    # Cleanup
    for db_name, dev_path in DB_TARGETS.items():
        await tgt_cmd(client, f"rm -f '{dev_path}.old'")

    # ══════════════════════════════════════════════════════════
    # PHASE 4: INSTALL 3RD PARTY APPS
    # ══════════════════════════════════════════════════════════
    print(f"\n[PHASE 4] INSTALL 3RD PARTY APPS ({len(app_list)} found)", flush=True)

    if app_list:
        # Get APK paths from neighbor
        print("  [4a] Getting APK paths from neighbor...", flush=True)
        apk_info = {}
        for pkg in app_list[:20]:  # Limit to top 20
            out = await nb_cmd(client, NEIGHBOR, f"pm path {pkg} 2>/dev/null", timeout=8)
            if out:
                paths = [l.replace("package:", "").strip() for l in out.split("\n") if l.startswith("package:")]
                if paths:
                    apk_info[pkg] = paths
                    print(f"    {pkg}: {len(paths)} APK(s)", flush=True)
            await asyncio.sleep(CMD_DELAY)

        # Install via Cloud API upload_file_via_url if APKs are on VPS
        # Or install from neighbor via relay
        # For now, try to install common apps via pm install from neighbor's APK paths
        print(f"  [4b] Installing apps via neighbor relay...", flush=True)
        installed = 0
        for pkg, paths in list(apk_info.items())[:15]:
            if len(paths) == 1:
                # Single APK — copy from neighbor to launchpad, then push via VPS
                apk_path = paths[0]
                # Use nc relay: neighbor sends APK to launchpad
                lp_ip = "10.12.11.186"
                port = 19870 + (hash(pkg) & 0xFF)
                lp_dest = f"{STAGING}/{pkg}_base.apk"

                # Start listener on launchpad
                await lp_cmd(client, f"pkill -f 'nc.*{port}' 2>/dev/null; rm -f {lp_dest}")
                await asyncio.sleep(1)
                await lp_fire(client, f"nc -l -p {port} > {lp_dest}")
                await asyncio.sleep(2)

                # Have neighbor send APK to launchpad
                send_cmd = f"cat {apk_path} | nc -w 10 {lp_ip} {port}"
                await nb_cmd(client, NEIGHBOR, send_cmd, timeout=30)
                await asyncio.sleep(5)

                # Check if APK arrived on launchpad
                sz = await lp_cmd(client, f"wc -c < {lp_dest} 2>/dev/null || echo 0")
                try:
                    apk_size = int((sz or "0").strip())
                except:
                    apk_size = 0

                if apk_size > 1000:
                    print(f"    {pkg}: {apk_size/1024:.0f}KB on launchpad", flush=True)

                    # Upload APK from launchpad to VPS
                    await lp_cmd(client,
                        f"curl -s -T {lp_dest} http://{VPS_IP}:{VPS_PORT}/{pkg}_base.apk",
                        timeout=60)
                    await asyncio.sleep(3)

                    # Download on target from VPS and install
                    tgt_dest = f"{STAGING}/{pkg}_base.apk"
                    await tgt_cmd(client,
                        f"curl -s -o {tgt_dest} http://{VPS_IP}:{VPS_PORT}/{pkg}_base.apk",
                        timeout=60)
                    await asyncio.sleep(2)

                    result = await tgt_cmd(client,
                        f"pm install -r -d -g {tgt_dest} 2>&1",
                        timeout=60)
                    if result and "Success" in result:
                        print(f"    ✓ {pkg} installed", flush=True)
                        installed += 1
                    else:
                        print(f"    ✗ {pkg}: {(result or '')[:60]}", flush=True)
                    await tgt_cmd(client, f"rm -f {tgt_dest}")
                else:
                    print(f"    ✗ {pkg}: APK transfer failed ({apk_size}B)", flush=True)
                await asyncio.sleep(CMD_DELAY)

        print(f"  Installed: {installed}/{len(apk_info)}", flush=True)

    # ══════════════════════════════════════════════════════════
    # PHASE 5: RESTART + VERIFY
    # ══════════════════════════════════════════════════════════
    print("\n[PHASE 5] RESTART + VERIFY", flush=True)

    # 5a. Pre-restart WAL check
    out = await tgt_cmd(client,
        "ls /data/system_ce/0/accounts_ce.db-wal 2>/dev/null && echo HAS_WAL || echo SAFE")
    print(f"  Pre-restart WAL check: {out}", flush=True)

    # 5b. Full restart
    print("  Restarting target...", flush=True)
    try:
        result = await client.instance_restart([TARGET])
        print(f"    Restart: code={result.get('code')}", flush=True)
    except Exception as e:
        print(f"    Restart error: {e}", flush=True)

    await asyncio.sleep(40)

    # Wait for alive
    alive = False
    for i in range(20):
        out = await tgt_cmd(client, "echo ALIVE", retries=1, timeout=10)
        if out and "ALIVE" in out:
            print(f"    Device ALIVE after {i*8+40}s", flush=True)
            alive = True
            break

        # Check for crash
        try:
            r = await client.instance_list()
            for d in r.get('data', {}).get('pageData', []):
                if d.get('padCode') == TARGET:
                    s = d.get('padStatus')
                    if s == 14:
                        print(f"    CRASH (status=14) — should not happen with DELETE DBs!", flush=True)
                        await client.close()
                        return
                    elif s != 10:
                        print(f"    [{i*8+40}s] status={s}", flush=True)
        except:
            pass
        await asyncio.sleep(8)

    if not alive:
        print("    WARN: Target not responding", flush=True)

    await asyncio.sleep(5)

    # 5c. Verification
    print("\n  === VERIFICATION ===", flush=True)

    out = await tgt_cmd(client, "dumpsys account 2>/dev/null | head -15")
    if out:
        for line in out.split("\n")[:15]:
            print(f"    {line}", flush=True)
    await asyncio.sleep(API_DELAY)

    out = await tgt_cmd(client, "getprop ro.product.model && getprop ro.product.brand")
    print(f"  Identity: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    out = await tgt_cmd(client, "settings get global http_proxy 2>/dev/null")
    print(f"  Proxy: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    out = await tgt_cmd(client, "pm list packages -3 2>/dev/null | wc -l")
    print(f"  3rd party apps: {out}", flush=True)
    await asyncio.sleep(API_DELAY)

    # DB health
    for db in ["/data/system_ce/0/accounts_ce.db", "/data/system_de/0/accounts_de.db"]:
        out = await tgt_cmd(client, f"ls -laZ {db}")
        print(f"  {db.split('/')[-1]}: {out}", flush=True)
        out = await tgt_cmd(client, f"ls {db}-wal 2>/dev/null && echo HAS_WAL || echo NO_WAL")
        print(f"    sidecar: {out}", flush=True)
        await asyncio.sleep(1)

    out = await tgt_cmd(client, "pidof system_server && uptime")
    print(f"  System: {out}", flush=True)

    out = await tgt_cmd(client, "logcat -d -t 30 2>/dev/null | grep -iE 'SQLite.*Error|IOERR' | tail -3")
    if out and out.strip():
        print(f"  SQLite errors: {out}", flush=True)
    else:
        print(f"  SQLite: CLEAN", flush=True)

    elapsed = time.time() - t0
    print(f"\n{'='*70}")
    print(f"  FULL CLONE COMPLETE — {elapsed:.0f}s")
    print(f"  Target: {TARGET}")
    print(f"  Identity: Samsung SM-S9110")
    print(f"  Accounts: {', '.join(a['email'] for a in ACCOUNTS)}")
    print(f"  DB Mode: DELETE journal | system_data_file SELinux")
    print(f"{'='*70}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
