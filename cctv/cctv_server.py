#!/usr/bin/env python3
"""
TITAN CCTV v2 — LIVE DASHBOARD SERVER
Flask + SocketIO backend serving real-time scan results, YOLO frames, and control API.

Run:
    python cctv_server.py                    # starts on 0.0.0.0:7700
    python cctv_server.py --port 8888
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# local imports
from cctv_config import (
    GLOBAL_CIDRS,
    REGIONS,
    ROOM_CLASSIFICATION,
    YOLO_CLASSES,
    list_available_countries,
    list_available_regions,
)
from titan_cctv import (
    generate_ips,
    get_cidrs_for_countries,
    get_cidrs_for_region,
    masscan_scan,
    probe_rtsp,
    run_scan,
    scan_ip,
    yolo_detect,
    FRAME_DIR,
    RESULTS_DIR,
)

# ════════════════════════════════════════════════════════════
#  APP SETUP
# ════════════════════════════════════════════════════════════

app = Flask(
    __name__,
    static_folder=str(Path(__file__).parent / "static"),
    template_folder=str(Path(__file__).parent / "templates"),
)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# In-memory state
STATE = {
    "cameras": [],          # list[dict] – discovered cameras
    "scan_active": False,
    "scan_progress": {},
    "stats": {
        "total_scanned": 0,
        "live_found": 0,
        "yolo_processed": 0,
        "rooms": defaultdict(int),
    },
    "history": [],          # past scan reports
}

SCAN_THREAD: threading.Thread | None = None


# ════════════════════════════════════════════════════════════
#  ROUTES — pages
# ════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/frames/<path:filename>")
def serve_frame(filename):
    return send_from_directory(str(FRAME_DIR), filename)


# ════════════════════════════════════════════════════════════
#  API — REST endpoints
# ════════════════════════════════════════════════════════════

@app.route("/api/countries")
def api_countries():
    return jsonify(list_available_countries())


@app.route("/api/regions")
def api_regions():
    data = {}
    for r in list_available_regions():
        data[r] = REGIONS[r]
    return jsonify(data)


@app.route("/api/cameras")
def api_cameras():
    return jsonify(STATE["cameras"])


@app.route("/api/stats")
def api_stats():
    s = STATE["stats"].copy()
    s["rooms"] = dict(s["rooms"])
    s["scan_active"] = STATE["scan_active"]
    s["camera_count"] = len(STATE["cameras"])
    return jsonify(s)


@app.route("/api/history")
def api_history():
    # return list of past result files
    files = sorted(RESULTS_DIR.glob("scan_*.json"), reverse=True)[:20]
    history = []
    for f in files:
        try:
            with open(f) as fp:
                d = json.load(fp)
            history.append({
                "file": f.name,
                "timestamp": d.get("timestamp"),
                "target": d.get("target"),
                "live_streams": d.get("live_streams", 0),
            })
        except Exception:
            pass
    return jsonify(history)


@app.route("/api/scan/start", methods=["POST"])
def api_scan_start():
    if STATE["scan_active"]:
        return jsonify({"error": "Scan already running"}), 409
    data = request.get_json(force=True) or {}
    threading.Thread(target=_run_scan_bg, args=(data,), daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/api/scan/stop", methods=["POST"])
def api_scan_stop():
    STATE["scan_active"] = False
    return jsonify({"status": "stopping"})


@app.route("/api/probe", methods=["POST"])
def api_probe():
    data = request.get_json(force=True) or {}
    ip = data.get("ip")
    if not ip:
        return jsonify({"error": "ip required"}), 400
    hit = probe_rtsp(ip)
    if hit:
        det = yolo_detect(hit["frame_file"])
        hit["yolo"] = det
        # encode frame as base64 for the UI
        try:
            with open(hit["frame_file"], "rb") as f:
                hit["frame_b64"] = base64.b64encode(f.read()).decode()
        except Exception:
            pass
        return jsonify(hit)
    return jsonify({"error": "no_stream", "ip": ip}), 404


@app.route("/api/yolo", methods=["POST"])
def api_yolo():
    data = request.get_json(force=True) or {}
    image_path = data.get("image")
    if not image_path:
        return jsonify({"error": "image path required"}), 400
    det = yolo_detect(image_path, conf=data.get("conf", 0.35))
    return jsonify(det)


# ════════════════════════════════════════════════════════════
#  BACKGROUND SCAN — with live SocketIO updates
# ════════════════════════════════════════════════════════════

def _run_scan_bg(params: dict):
    """Run a scan in background, emitting progress via SocketIO."""
    STATE["scan_active"] = True
    STATE["cameras"] = []
    STATE["stats"] = {
        "total_scanned": 0, "live_found": 0, "yolo_processed": 0,
        "rooms": defaultdict(int),
    }
    socketio.emit("scan_status", {"status": "started", "params": params})

    countries = params.get("countries")
    region = params.get("region")
    cidrs_raw = params.get("cidrs")
    max_cams = int(params.get("max_cams", 50))
    run_yolo = params.get("yolo", True)
    workers = int(params.get("workers", 80))

    # resolve CIDRs
    cidrs = []
    label = "custom"
    if cidrs_raw:
        cidrs = [c.strip() for c in cidrs_raw.split(",")]
        label = "custom_cidrs"
    elif region:
        cidrs = get_cidrs_for_region(region)
        label = region
    elif countries:
        if isinstance(countries, str):
            countries = [c.strip() for c in countries.split(",")]
        if countries == ["all"]:
            countries = list(GLOBAL_CIDRS.keys())
        cidrs = get_cidrs_for_countries(countries)
        label = "+".join(countries[:3])

    if not cidrs:
        socketio.emit("scan_status", {"status": "error", "message": "No CIDRs resolved"})
        STATE["scan_active"] = False
        return

    socketio.emit("scan_status", {"status": "phase1", "message": f"Generating IPs from {len(cidrs)} CIDRs"})

    ips = generate_ips(cidrs, count=int(params.get("ips", 2000)))
    STATE["stats"]["total_scanned"] = len(ips)
    socketio.emit("scan_status", {"status": "phase2", "ips": len(ips)})

    # probe
    from concurrent.futures import ThreadPoolExecutor, as_completed

    streams = []
    probed = 0
    socketio.emit("scan_status", {"status": "phase3", "message": f"Probing {len(ips)} IPs"})

    with ThreadPoolExecutor(max_workers=min(workers, 60)) as pool:
        futs = {pool.submit(probe_rtsp, ip): ip for ip in ips}
        for fut in as_completed(futs):
            if not STATE["scan_active"]:
                for f in futs:
                    f.cancel()
                break
            probed += 1
            try:
                hit = fut.result()
                if hit:
                    # YOLO detection
                    if run_yolo:
                        det = yolo_detect(hit["frame_file"])
                        hit["yolo"] = det
                        STATE["stats"]["yolo_processed"] += 1
                        room = det.get("room_type", "unknown")
                        STATE["stats"]["rooms"][room] += 1

                    # encode frame
                    try:
                        with open(hit["frame_file"], "rb") as f:
                            hit["frame_b64"] = base64.b64encode(f.read()).decode()
                    except Exception:
                        pass

                    streams.append(hit)
                    STATE["cameras"].append(hit)
                    STATE["stats"]["live_found"] = len(streams)

                    socketio.emit("camera_found", {
                        "camera": _safe_cam(hit),
                        "total": len(streams),
                        "probed": probed,
                    })

                    if len(streams) >= max_cams:
                        for f in futs:
                            f.cancel()
                        break
            except Exception:
                pass
            if probed % 50 == 0:
                socketio.emit("scan_progress", {"probed": probed, "found": len(streams), "total": len(ips)})

    # save results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "scan_id": f"titan_cctv_{ts}",
        "timestamp": datetime.now().isoformat(),
        "target": label,
        "cidrs_used": len(cidrs),
        "ips_scanned": len(ips),
        "live_streams": len(streams),
        "yolo_enabled": run_yolo,
        "room_classification": dict(STATE["stats"]["rooms"]),
        "cameras": [_safe_cam(c) for c in streams],
    }
    out_file = RESULTS_DIR / f"scan_{label.replace(' ', '_')}_{ts}.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    STATE["scan_active"] = False
    socketio.emit("scan_status", {
        "status": "complete",
        "live_streams": len(streams),
        "file": str(out_file),
        "rooms": dict(STATE["stats"]["rooms"]),
    })


def _safe_cam(cam: dict) -> dict:
    """Strip binary data for JSON serialization."""
    c = cam.copy()
    c.pop("frame_b64", None)  # defer to /frames/ endpoint
    return {k: v for k, v in c.items() if not isinstance(v, bytes)}


# ════════════════════════════════════════════════════════════
#  SOCKETIO EVENTS
# ════════════════════════════════════════════════════════════

@socketio.on("connect")
def on_connect():
    emit("state", {
        "cameras": len(STATE["cameras"]),
        "scan_active": STATE["scan_active"],
        "stats": {k: (dict(v) if isinstance(v, defaultdict) else v)
                  for k, v in STATE["stats"].items()},
    })


@socketio.on("request_cameras")
def on_request_cameras():
    emit("cameras_list", [_safe_cam(c) for c in STATE["cameras"]])


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=7700)
    args = p.parse_args()

    # ensure template dir exists
    tpl = Path(__file__).parent / "templates"
    tpl.mkdir(exist_ok=True)
    static = Path(__file__).parent / "static"
    static.mkdir(exist_ok=True)

    print(f"\n  TITAN CCTV v2 — Dashboard Server")
    print(f"  http://{args.host}:{args.port}")
    print(f"  Ctrl+C to stop\n")
    socketio.run(app, host=args.host, port=args.port, debug=False, allow_unsafe_werkzeug=True)
