#!/usr/bin/env python3
"""
Screenshot capture - handles both HTTP and RTSP cameras
"""
import subprocess, os, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
SCREENSHOT_DIR = os.path.join(WORK_DIR, 'live_screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Load cameras
CAMERAS_FILE = os.path.join(WORK_DIR, '20_cams_COMPLETE_20260401_012000.json')
with open(CAMERAS_FILE) as f:
    data = json.load(f)
    cameras = data.get('streams', [])

print(f'[*] Loaded {len(cameras)} cameras')
print(f'[*] Screenshots: {SCREENSHOT_DIR}')

def capture_screenshot(camera):
    """Capture using appropriate method"""
    ip = camera['ip']
    method = camera.get('method', 'rtsp')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    cam_dir = os.path.join(SCREENSHOT_DIR, ip.replace('.', '_'))
    os.makedirs(cam_dir, exist_ok=True)
    
    frame_file = os.path.join(cam_dir, f'shot_{timestamp}.jpg')
    
    if method == 'http':
        # Try HTTP/ISAPI snapshot
        urls = [
            f'http://{ip}:80/ISAPI/Streaming/channels/101/picture',
            f'http://{ip}:8000/ISAPI/Streaming/channels/101/picture',
            f'http://{ip}:80/cgi-bin/snapshot.cgi?user=admin&pwd=',
        ]
        for url in urls:
            try:
                r = subprocess.run(['curl', '-s', '--max-time', '4', '-o', frame_file, url],
                    capture_output=True, timeout=5)
                if r.returncode == 0 and os.path.exists(frame_file) and os.path.getsize(frame_file) > 3000:
                    return frame_file, os.path.getsize(frame_file)
            except:
                pass
    
    # Try RTSP as fallback
    rtsp_url = camera.get('rtsp_url', f'rtsp://admin:@{ip}:554/Streaming/Channels/101')
    try:
        r = subprocess.run(
            ['ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
             '-vframes', '1', '-f', 'image2', '-y', frame_file],
            capture_output=True, timeout=5, text=True
        )
        if r.returncode == 0 and os.path.exists(frame_file) and os.path.getsize(frame_file) > 1000:
            return frame_file, os.path.getsize(frame_file)
    except:
        pass
    
    return None, 0

def capture_continuous(camera, count=10, interval=3):
    """Capture multiple screenshots from one camera"""
    ip = camera['ip']
    successful = 0
    total_size = 0
    
    for i in range(count):
        result, size = capture_screenshot(camera)
        if result:
            successful += 1
            total_size += size
            print(f'  [{ip}] Shot #{successful}: {size:,}B')
        else:
            print(f'  [{ip}] Shot failed')
        
        if i < count - 1:
            time.sleep(interval)
    
    return successful, total_size

# Test all cameras first
print('\n[*] Testing all cameras...\n')
working_cams = []

with ThreadPoolExecutor(max_workers=20) as pool:
    futures = {pool.submit(capture_screenshot, cam): cam for cam in cameras}
    for fut in as_completed(futures):
        cam = futures[fut]
        try:
            result, size = fut.result()
            if result:
                working_cams.append(cam)
                print(f'[+] {cam["ip"]}: Working ({size:,}B)')
            else:
                print(f'[-] {cam["ip"]}: Failed')
        except:
            print(f'[!] {cam["ip"]}: Error')

print(f'\n[*] {len(working_cams)}/{len(cameras)} cameras responding')

# Capture multiple shots from working cameras
if working_cams:
    print(f'\n[*] Capturing 10 shots each from {len(working_cams)} cameras...\n')
    
    all_results = {}
    with ThreadPoolExecutor(max_workers=len(working_cams)) as pool:
        futures = {pool.submit(capture_continuous, cam, 10, 3): cam for cam in working_cams}
        for fut in as_completed(futures):
            cam = futures[fut]
            try:
                count, total = fut.result()
                all_results[cam['ip']] = (count, total)
            except:
                pass
    
    print('\n' + '='*60)
    print('SCREENSHOT CAPTURE COMPLETE')
    print('='*60)
    total_shots = sum(r[0] for r in all_results.values())
    total_bytes = sum(r[1] for r in all_results.values())
    print(f'Total: {total_shots} screenshots, {total_bytes:,} bytes')
    print(f'\nBreakdown:')
    for ip, (count, size) in sorted(all_results.items()):
        print(f'  {ip}: {count} shots, {size:,}B')
    print(f'\nSaved to: {SCREENSHOT_DIR}')
else:
    print('[!] No working cameras found')
