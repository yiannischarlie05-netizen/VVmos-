#!/usr/bin/env python3
"""
TITAN CCTV v2 — RECORDING + CONTINUOUS MONITORING ENGINE
Handles continuous recording, re-verification, alerts, and stream archival.

Usage:
    python cctv_recorder.py record --input results/scan_*.json --duration 60
    python cctv_recorder.py monitor --input results/scan_*.json --interval 300
    python cctv_recorder.py snapshot --input results/scan_*.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from titan_cctv import probe_rtsp, yolo_detect, FRAME_DIR, RESULTS_DIR

BASE_DIR = Path(__file__).resolve().parent
RECORDINGS_DIR = BASE_DIR / "recordings"
SNAPSHOTS_DIR = BASE_DIR / "snapshots"
ALERTS_DIR = BASE_DIR / "alerts"

for d in (RECORDINGS_DIR, SNAPSHOTS_DIR, ALERTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

_shutdown = threading.Event()


def _signal_handler(sig, frame):
    print("\n[!] Shutdown requested …")
    _shutdown.set()

signal.signal(signal.SIGINT, _signal_handler)


def load_cameras_from_results(pattern: str) -> list[dict]:
    """Load cameras from scan result JSON files."""
    cameras = []
    files = sorted(glob.glob(pattern))
    for f in files:
        try:
            with open(f) as fp:
                data = json.load(fp)
            for cam in data.get("cameras", []):
                if cam.get("rtsp_url"):
                    cameras.append(cam)
        except Exception as e:
            print(f"  [!] Error loading {f}: {e}")
    # dedupe by IP
    seen = set()
    deduped = []
    for c in cameras:
        ip = c.get("ip")
        if ip and ip not in seen:
            seen.add(ip)
            deduped.append(c)
    return deduped


# ════════════════════════════════════════════════════════════
#  RECORD — continuous video capture via ffmpeg
# ════════════════════════════════════════════════════════════

def record_stream(cam: dict, duration: int = 60, segment: int = 0) -> dict:
    """Record a single camera stream for `duration` seconds."""
    ip = cam.get("ip", "unknown")
    rtsp = cam.get("rtsp_url")
    if not rtsp:
        return {"ip": ip, "error": "no_rtsp_url"}

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_ip = ip.replace(".", "_")
    out_dir = RECORDINGS_DIR / safe_ip
    out_dir.mkdir(parents=True, exist_ok=True)

    if segment > 0:
        # segment recording into multiple files
        out_pattern = str(out_dir / f"rec_{safe_ip}_{ts}_%03d.mp4")
        cmd = [
            "ffmpeg", "-rtsp_transport", "tcp", "-i", rtsp,
            "-c", "copy", "-t", str(duration),
            "-f", "segment", "-segment_time", str(segment),
            "-reset_timestamps", "1", "-y", out_pattern,
        ]
    else:
        out_file = str(out_dir / f"rec_{safe_ip}_{ts}.mp4")
        cmd = [
            "ffmpeg", "-rtsp_transport", "tcp", "-i", rtsp,
            "-c", "copy", "-t", str(duration), "-y", out_file,
        ]

    try:
        r = subprocess.run(cmd, capture_output=True, timeout=duration + 30, text=True)
        # find output files
        files = sorted(out_dir.glob(f"rec_{safe_ip}_{ts}*"))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        return {
            "ip": ip,
            "status": "recorded",
            "files": [str(f) for f in files],
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "duration_s": duration,
        }
    except subprocess.TimeoutExpired:
        return {"ip": ip, "status": "timeout"}
    except Exception as e:
        return {"ip": ip, "status": "error", "error": str(e)}


def batch_record(cameras: list[dict], duration: int = 60, workers: int = 8,
                 segment: int = 0) -> list[dict]:
    """Record multiple cameras in parallel."""
    print(f"\n[RECORD] Recording {len(cameras)} cameras for {duration}s (workers={workers})")
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {
            pool.submit(record_stream, cam, duration, segment): cam
            for cam in cameras
        }
        for fut in as_completed(futs):
            if _shutdown.is_set():
                break
            try:
                r = fut.result()
                results.append(r)
                status = r.get("status", "?")
                size = r.get("total_size_mb", 0)
                print(f"  [{len(results):>3}/{len(cameras)}] {r['ip']:>16}  "
                      f"status={status}  size={size}MB")
            except Exception:
                pass
    return results


# ════════════════════════════════════════════════════════════
#  SNAPSHOT — grab single frame + YOLO from all cameras
# ════════════════════════════════════════════════════════════

def snapshot_camera(cam: dict) -> dict:
    """Grab a fresh frame + run YOLO on a known camera."""
    ip = cam.get("ip", "unknown")
    rtsp = cam.get("rtsp_url")
    if not rtsp:
        return {"ip": ip, "error": "no_rtsp_url"}

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_ip = ip.replace(".", "_")
    snap_file = str(SNAPSHOTS_DIR / f"snap_{safe_ip}_{ts}.jpg")

    try:
        r = subprocess.run(
            ["ffmpeg", "-rtsp_transport", "tcp", "-i", rtsp,
             "-vframes", "1", "-f", "image2", "-y", snap_file],
            capture_output=True, timeout=10, text=True,
        )
        if r.returncode == 0 and os.path.isfile(snap_file) and os.path.getsize(snap_file) > 1000:
            det = yolo_detect(snap_file)
            return {
                "ip": ip,
                "status": "live",
                "snapshot": snap_file,
                "frame_size": os.path.getsize(snap_file),
                "yolo": det,
                "timestamp": datetime.now().isoformat(),
            }
        return {"ip": ip, "status": "dead", "timestamp": datetime.now().isoformat()}
    except (subprocess.TimeoutExpired, Exception):
        return {"ip": ip, "status": "dead", "timestamp": datetime.now().isoformat()}


def batch_snapshot(cameras: list[dict], workers: int = 30) -> list[dict]:
    """Take snapshots of all cameras and run YOLO."""
    print(f"\n[SNAPSHOT] Capturing {len(cameras)} cameras …")
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(snapshot_camera, cam): cam for cam in cameras}
        for fut in as_completed(futs):
            if _shutdown.is_set():
                break
            try:
                r = fut.result()
                results.append(r)
                st = r.get("status", "?")
                room = r.get("yolo", {}).get("room_type", "?")
                print(f"  [{len(results):>3}/{len(cameras)}] {r['ip']:>16}  "
                      f"status={st}  room={room}")
            except Exception:
                pass

    live = [r for r in results if r.get("status") == "live"]
    dead = [r for r in results if r.get("status") != "live"]
    print(f"\n  Live: {len(live)} | Dead: {len(dead)}")
    return results


# ════════════════════════════════════════════════════════════
#  MONITOR — continuous re-verification loop
# ════════════════════════════════════════════════════════════

def monitor_loop(cameras: list[dict], interval: int = 300, workers: int = 20,
                 alert_on: list[str] | None = None):
    """Periodically re-verify cameras and generate alerts on room-type match."""
    alert_rooms = set(alert_on or [])
    cycle = 0
    print(f"\n[MONITOR] Starting continuous monitoring")
    print(f"  Cameras: {len(cameras)} | Interval: {interval}s | Alert rooms: {alert_rooms or 'none'}")

    while not _shutdown.is_set():
        cycle += 1
        print(f"\n{'='*60}")
        print(f"  [CYCLE {cycle}] {datetime.now().isoformat()}")
        print(f"{'='*60}")

        results = batch_snapshot(cameras, workers=workers)
        live = [r for r in results if r.get("status") == "live"]

        # check alerts
        if alert_rooms:
            for r in live:
                room = r.get("yolo", {}).get("room_type", "unknown")
                if room in alert_rooms:
                    _generate_alert(r, cycle)

        # save cycle report
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            "cycle": cycle,
            "timestamp": datetime.now().isoformat(),
            "total": len(cameras),
            "live": len(live),
            "dead": len(results) - len(live),
            "cameras": results,
        }
        report_file = RESULTS_DIR / f"monitor_cycle_{cycle}_{ts}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  Report saved: {report_file}")

        # wait
        print(f"  Next cycle in {interval}s … (Ctrl+C to stop)")
        _shutdown.wait(timeout=interval)

    print("\n[MONITOR] Stopped.")


def _generate_alert(cam_result: dict, cycle: int):
    """Save an alert when a matching room type is detected."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ip = cam_result.get("ip", "unknown")
    room = cam_result.get("yolo", {}).get("room_type", "unknown")
    alert = {
        "timestamp": datetime.now().isoformat(),
        "cycle": cycle,
        "ip": ip,
        "room_type": room,
        "objects": cam_result.get("yolo", {}).get("unique_objects", []),
        "snapshot": cam_result.get("snapshot"),
    }
    alert_file = ALERTS_DIR / f"alert_{room}_{ip.replace('.','_')}_{ts}.json"
    with open(alert_file, "w") as f:
        json.dump(alert, f, indent=2)
    print(f"  🚨 ALERT: {room} detected on {ip} → {alert_file.name}")


# ════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cctv_recorder",
                                description="Titan CCTV v2 — Recording + Monitoring")
    sub = p.add_subparsers(dest="command")

    rec = sub.add_parser("record", help="Record video from cameras")
    rec.add_argument("--input", required=True, help="Glob pattern for scan result JSONs")
    rec.add_argument("--duration", type=int, default=60, help="Seconds per recording")
    rec.add_argument("--segment", type=int, default=0, help="Segment interval (0=single file)")
    rec.add_argument("--workers", type=int, default=8)
    rec.add_argument("--max", type=int, default=0, help="Max cameras to record (0=all)")

    sn = sub.add_parser("snapshot", help="Snapshot all cameras + YOLO")
    sn.add_argument("--input", required=True)
    sn.add_argument("--workers", type=int, default=30)

    mon = sub.add_parser("monitor", help="Continuous monitoring loop")
    mon.add_argument("--input", required=True)
    mon.add_argument("--interval", type=int, default=300, help="Seconds between cycles")
    mon.add_argument("--workers", type=int, default=20)
    mon.add_argument("--alert-on", type=str, default="",
                     help="Comma-separated room types to alert on (e.g. bedroom,bathroom)")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cameras = load_cameras_from_results(args.input)
    if not cameras:
        print(f"[!] No cameras found matching: {args.input}")
        return
    print(f"[*] Loaded {len(cameras)} cameras from results")

    if args.command == "record":
        cams = cameras[:args.max] if args.max > 0 else cameras
        results = batch_record(cams, duration=args.duration,
                               workers=args.workers, segment=args.segment)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(RESULTS_DIR / f"recording_report_{ts}.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

    elif args.command == "snapshot":
        results = batch_snapshot(cameras, workers=args.workers)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(RESULTS_DIR / f"snapshot_report_{ts}.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

    elif args.command == "monitor":
        alert_on = [r.strip() for r in args.alert_on.split(",") if r.strip()] if args.alert_on else None
        monitor_loop(cameras, interval=args.interval,
                     workers=args.workers, alert_on=alert_on)


if __name__ == "__main__":
    main()
