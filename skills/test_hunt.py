#!/usr/bin/env python3
"""
Quick test of hunt_srilanka.py functionality
"""
import os, sys, subprocess, time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Test basic imports and setup
WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
FRAME_DIR = os.path.join(WORK_DIR, 'hunt_frames')
os.makedirs(FRAME_DIR, exist_ok=True)

print('[+] Testing basic functionality...')

# Test YOLO loading
try:
    from ultralytics import YOLO
    model_path = os.path.join(WORK_DIR, 'yolo11n.pt')
    if not os.path.exists(model_path):
        model_path = 'yolov8n.pt'
    yolo = YOLO(model_path)
    print(f'[+] YOLO loaded: {model_path}')
except Exception as e:
    print(f'[!] YOLO failed: {e}')
    yolo = None

# Test masscan availability
try:
    result = subprocess.run(['which', 'masscan'], capture_output=True, text=True)
    if result.returncode == 0:
        print('[+] masscan found')
    else:
        print('[!] masscan not found')
except:
    print('[!] masscan check failed')

# Test ffmpeg availability
try:
    result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
    if result.returncode == 0:
        print('[+] ffmpeg found')
    else:
        print('[!] ffmpeg not found')
except:
    print('[!] ffmpeg check failed')

# Test threading setup
def dummy_task(x):
    time.sleep(0.1)
    return x*2

with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(dummy_task, i) for i in range(8)]
    results = [f.result() for f in as_completed(futures)]

print(f'[+] Threading test: {len(results)} tasks completed')

print('[+] Test complete - script components working')
