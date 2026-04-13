#!/usr/bin/env python3
"""Real-time frame monitor - watch hunt_frames and display new captures instantly"""
import os, time, sys, subprocess, glob
from datetime import datetime
import json

FRAME_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool/hunt_frames'

def get_frame_list():
    return sorted(set(glob.glob(os.path.join(FRAME_DIR, 'frame_*.jpg'))))

def display_frame_info(frame_path):
    """Extract and display frame info"""
    fname = os.path.basename(frame_path)
    ip = fname.replace('frame_', '').replace('.jpg', '').replace('_', '.')
    size = os.path.getsize(frame_path) / 1024
    mtime = datetime.fromtimestamp(os.path.getmtime(frame_path)).strftime('%H:%M:%S')
    return f'{mtime} | {ip:>16} | {size:>8.1f}KB | {fname}'

def wait_for_yolo():
    """Check if YOLO has classified this frame"""
    import json
    try:
        with open('/tmp/hunt_yolo_results.json') as f:
            data = json.load(f)
            return data
    except:
        return {}

print(f'REAL-TIME FRAME MONITOR')
print(f'Watching: {FRAME_DIR}')
print(f'Started: {datetime.now().strftime("%H:%M:%S")}\n')

seen = set()
idx = 0

while True:
    frames = get_frame_list()
    new_frames = [f for f in frames if f not in seen]
    
    if new_frames:
        for f in new_frames:
            idx += 1
            print(f'\n[{idx}] NEW FRAME CAPTURED:')
            print(f'    {display_frame_info(f)}')
            seen.add(f)
    
    # Check if hunt_indoor process is still running
    result = subprocess.run(['pgrep', '-f', 'hunt_indoor.py'], capture_output=True)
    if result.returncode != 0:
        break
    
    time.sleep(5)

print(f'\n[MONITOR] Scan process ended')
print(f'Total frames: {len(frames)}')
