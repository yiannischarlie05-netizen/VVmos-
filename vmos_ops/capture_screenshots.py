#!/usr/bin/env python3
"""
Screenshot capture while streaming from 20 live cameras
Captures frames periodically and saves to organized directory
"""
import subprocess, os, json, time, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import threading

WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
SCREENSHOT_DIR = os.path.join(WORK_DIR, 'live_screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Load the 20 cameras
CAMERAS_FILE = os.path.join(WORK_DIR, '20_cams_COMPLETE_20260401_012000.json')
if not os.path.exists(CAMERAS_FILE):
    # Try to find any complete file
    for f in os.listdir(WORK_DIR):
        if f.startswith('20_cams_COMPLETE') and f.endswith('.json'):
            CAMERAS_FILE = os.path.join(WORK_DIR, f)
            break

with open(CAMERAS_FILE) as f:
    data = json.load(f)
    cameras = data.get('streams', [])

print(f'[*] Loaded {len(cameras)} cameras for screenshot capture')
print(f'[*] Screenshots will be saved to: {SCREENSHOT_DIR}')
print(f'[*] Press Ctrl+C to stop\n')

def capture_screenshot(camera, timestamp=None):
    """Capture a single screenshot from camera"""
    ip = camera['ip']
    rtsp_url = camera.get('rtsp_url', f'rtsp://admin:@{ip}:554/Streaming/Channels/101')
    
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create subdir for this camera
    cam_dir = os.path.join(SCREENSHOT_DIR, ip.replace('.', '_'))
    os.makedirs(cam_dir, exist_ok=True)
    
    frame_file = os.path.join(cam_dir, f'screenshot_{timestamp}.jpg')
    
    try:
        r = subprocess.run(
            ['ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
             '-vframes', '1', '-f', 'image2', '-y', frame_file],
            capture_output=True, timeout=5, text=True
        )
        if r.returncode == 0 and os.path.exists(frame_file) and os.path.getsize(frame_file) > 1000:
            return frame_file
    except:
        pass
    return None

def continuous_capture(camera, interval=5, duration=None):
    """Continuously capture screenshots from a camera"""
    ip = camera['ip']
    count = 0
    start_time = time.time()
    
    while True:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result = capture_screenshot(camera, timestamp)
        
        if result:
            count += 1
            size = os.path.getsize(result)
            print(f'  [{ip}] Screenshot #{count}: {size:,}B')
        else:
            print(f'  [{ip}] Failed to capture')
        
        # Check if duration exceeded
        if duration and (time.time() - start_time) >= duration:
            break
            
        time.sleep(interval)
    
    return count

def capture_all_cameras(interval=5, duration=60):
    """Capture from all cameras simultaneously"""
    print(f'[*] Starting screenshot capture: {len(cameras)} cameras')
    print(f'[*] Interval: {interval}s | Duration: {duration}s\n')
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(continuous_capture, cam, interval, duration): cam for cam in cameras}
        
        for fut in as_completed(futures):
            cam = futures[fut]
            try:
                count = fut.result()
                results[cam['ip']] = count
            except Exception as e:
                print(f'  [{cam["ip"]}] Error: {e}')
    
    return results

# Main execution
if __name__ == '__main__':
    # Quick test - capture one screenshot from each camera first
    print('[*] TEST: Capturing initial screenshot from each camera...\n')
    
    test_results = []
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(capture_screenshot, cam): cam for cam in cameras}
        for fut in as_completed(futures):
            cam = futures[fut]
            try:
                result = fut.result()
                if result:
                    test_results.append((cam['ip'], result))
                    print(f'  [+] {cam["ip"]}: {result}')
                else:
                    print(f'  [-] {cam["ip"]}: Failed')
            except Exception as e:
                print(f'  [!] {cam["ip"]}: Error - {e}')
    
    print(f'\n[*] Test complete: {len(test_results)}/{len(cameras)} cameras responding')
    
    # Now do continuous capture
    print('\n[*] Starting continuous capture (5 second interval, 60 seconds)...\n')
    
    try:
        results = capture_all_cameras(interval=5, duration=60)
        
        print('\n' + '='*60)
        print('CAPTURE COMPLETE')
        print('='*60)
        
        total_screenshots = sum(results.values())
        print(f'Total screenshots captured: {total_screenshots}')
        print(f'\nPer-camera breakdown:')
        for ip, count in sorted(results.items()):
            print(f'  {ip}: {count} screenshots')
        
        print(f'\nScreenshots saved to: {SCREENSHOT_DIR}')
        
    except KeyboardInterrupt:
        print('\n\n[!] Capture interrupted by user')
        print(f'Screenshots saved to: {SCREENSHOT_DIR}')
