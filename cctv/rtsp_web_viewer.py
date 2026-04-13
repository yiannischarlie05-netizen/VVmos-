#!/usr/bin/env python3
"""
TITAN RTSP WEB VIEWER — View live RTSP camera feeds in any web browser.
Continuously grabs JPEG snapshots from each camera via ffmpeg and serves
them as auto-refreshing images on an HTTP dashboard.
"""

import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE = Path(__file__).resolve().parent
SNAP_DIR = BASE / "web_snapshots"
RESULTS = BASE / "results"
SNAP_DIR.mkdir(exist_ok=True)

PORT = 7701
REFRESH_INTERVAL = 4  # seconds between frame grabs per camera
MAX_WORKERS = 12

# ── Load cameras from results ──
def load_cameras() -> list:
    cams = {}
    # Try live_streams.json first (most complete)
    for fname in ["live_streams.json", "rtsp_blitz_live.json"]:
        p = RESULTS / fname
        if p.exists():
            with open(p) as f:
                d = json.load(f)
            streams = d.get("streams", [])
            for s in streams:
                ip = s.get("ip", "")
                if ip and ip not in cams:
                    cams[ip] = s
    return list(cams.values())


CAMERAS = load_cameras()
CAM_STATUS = {}  # ip -> {last_ok, error, resolution}

# ══════════════════════════════════════════════════════════
# SNAPSHOT GRABBER
# ══════════════════════════════════════════════════════════

def grab_snapshot(cam: dict) -> bool:
    """Grab a single JPEG frame from an RTSP stream via ffmpeg."""
    ip = cam["ip"]
    url = cam.get("rtsp_url", "")
    if not url:
        return False
    safe = ip.replace(".", "_")
    out_path = SNAP_DIR / f"{safe}.jpg"
    tmp_path = SNAP_DIR / f"{safe}_tmp.jpg"

    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp",
             "-timeout", "4000000",
             "-i", url,
             "-frames:v", "1", "-update", "1",
             "-vf", "scale=640:-1",
             "-q:v", "4",
             str(tmp_path)],
            capture_output=True, timeout=10, text=True
        )
        if r.returncode == 0 and tmp_path.exists() and tmp_path.stat().st_size > 1000:
            # Atomic rename so HTTP server never serves partial file
            tmp_path.rename(out_path)
            # Parse resolution from ffmpeg stderr
            import re
            res = re.search(r"(\d{2,5})x(\d{2,5})", r.stderr)
            reso = f"{res.group(1)}x{res.group(2)}" if res else "?"
            CAM_STATUS[ip] = {"last_ok": time.time(), "error": None, "resolution": reso}
            return True
        else:
            if tmp_path.exists():
                tmp_path.unlink()
            CAM_STATUS[ip] = {"last_ok": CAM_STATUS.get(ip, {}).get("last_ok", 0),
                              "error": "ffmpeg failed", "resolution": "?"}
    except subprocess.TimeoutExpired:
        if tmp_path.exists():
            tmp_path.unlink()
        CAM_STATUS[ip] = {"last_ok": CAM_STATUS.get(ip, {}).get("last_ok", 0),
                          "error": "timeout", "resolution": "?"}
    except Exception as e:
        CAM_STATUS[ip] = {"last_ok": CAM_STATUS.get(ip, {}).get("last_ok", 0),
                          "error": str(e)[:50], "resolution": "?"}
    return False


def snapshot_loop():
    """Continuously grab snapshots from all cameras."""
    while True:
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            results = list(pool.map(grab_snapshot, CAMERAS))
        ok = sum(results)
        elapsed = time.time() - t0
        print(f"[SNAP] {ok}/{len(CAMERAS)} frames grabbed in {elapsed:.1f}s")
        # Wait before next round, minimum REFRESH_INTERVAL
        wait = max(0, REFRESH_INTERVAL - elapsed)
        time.sleep(wait)


# ══════════════════════════════════════════════════════════
# HTTP SERVER
# ══════════════════════════════════════════════════════════

class ViewerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/snap/"):
            # Serve snapshot image: /snap/1_2_3_4.jpg
            fname = self.path[6:]  # strip /snap/
            fpath = SNAP_DIR / fname
            if fpath.exists() and fpath.suffix == ".jpg":
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                self.wfile.write(fpath.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()

        elif self.path == "/api/cameras":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = []
            for c in CAMERAS:
                ip = c["ip"]
                st = CAM_STATUS.get(ip, {})
                data.append({
                    "ip": ip, "port": c.get("port", 554),
                    "rtsp_url": c.get("rtsp_url", ""),
                    "path": c.get("path", ""),
                    "user": c.get("user", ""),
                    "auth": c.get("auth", ""),
                    "resolution": st.get("resolution", c.get("resolution", "?")),
                    "online": (time.time() - st.get("last_ok", 0)) < 30,
                    "error": st.get("error"),
                    "snap_url": f"/snap/{ip.replace('.','_')}.jpg",
                })
            self.wfile.write(json.dumps(data).encode())

        elif self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(build_dashboard().encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass


def build_dashboard() -> str:
    ts = datetime.now().strftime('%H:%M:%S')
    online = sum(1 for ip in CAM_STATUS if (time.time() - CAM_STATUS[ip].get("last_ok", 0)) < 30)

    cam_grid = ""
    for i, c in enumerate(CAMERAS):
        ip = c["ip"]
        safe = ip.replace(".", "_")
        st = CAM_STATUS.get(ip, {})
        is_online = (time.time() - st.get("last_ok", 0)) < 30
        dot = "🟢" if is_online else "🔴"
        reso = st.get("resolution", c.get("resolution", "?"))
        auth = f'{c.get("user","")}:{c.get("password","")}' if c.get("user") else "OPEN"
        rtsp = c.get("rtsp_url", "")

        cam_grid += f'''
<div class="cam" id="cam-{safe}">
  <div class="cam-header">
    <span class="cam-num">#{i+1}</span>
    <span class="cam-status">{dot}</span>
    <span class="cam-ip">{ip}</span>
  </div>
  <div class="cam-img-wrap" onclick="openFull('{safe}')">
    <img src="/snap/{safe}.jpg?t={int(time.time())}" 
         class="cam-img" id="img-{safe}"
         onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
         onload="this.style.display='block';this.nextElementSibling.style.display='none'">
    <div class="cam-placeholder">Connecting...</div>
  </div>
  <div class="cam-info">
    <span>{reso}</span> | <span>:{c.get("port",554)}</span> | <span class="auth">{auth}</span>
  </div>
  <div class="cam-rtsp" onclick="navigator.clipboard.writeText('{rtsp}');this.style.color='#0f0'" title="Click to copy">{rtsp}</div>
</div>'''

    return f'''<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>TITAN LIVE CAMERA VIEWER — {len(CAMERAS)} Cameras</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a18; color: #eee; font-family: 'Segoe UI', 'Courier New', monospace; }}
.header {{
  background: linear-gradient(135deg, #1a0a2e, #0a1a2e);
  padding: 15px 20px;
  border-bottom: 2px solid #f00;
  display: flex; justify-content: space-between; align-items: center;
}}
.header h1 {{ color: #f00; font-size: 20px; }}
.stats {{ display: flex; gap: 15px; }}
.stat {{ background: #111; padding: 5px 12px; border-radius: 6px; font-size: 12px; border: 1px solid #222; }}
.stat b {{ color: #0f0; font-size: 16px; }}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 8px; padding: 10px;
}}
.cam {{
  background: #12122a;
  border: 1px solid #2a2a4a;
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.3s;
}}
.cam:hover {{ border-color: #0ff; }}
.cam-header {{
  display: flex; align-items: center; gap: 6px;
  padding: 6px 10px; background: #0d0d20;
}}
.cam-num {{ color: #0f0; font-weight: bold; font-size: 12px; }}
.cam-ip {{ color: #0ff; font-size: 12px; }}
.cam-status {{ font-size: 10px; }}
.cam-img-wrap {{
  position: relative; cursor: pointer;
  background: #000; min-height: 180px;
  display: flex; align-items: center; justify-content: center;
}}
.cam-img {{ width: 100%; display: block; }}
.cam-placeholder {{
  display: flex; align-items: center; justify-content: center;
  color: #333; font-size: 13px; height: 180px; width: 100%;
}}
.cam-info {{
  padding: 4px 10px; font-size: 11px; color: #888;
  border-top: 1px solid #1a1a2a;
}}
.auth {{ color: #ff0; }}
.cam-rtsp {{
  padding: 3px 10px 6px; font-size: 9px; color: #444;
  word-break: break-all; cursor: pointer;
}}
.cam-rtsp:hover {{ color: #0ff; }}
#fullscreen {{
  display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.95); z-index: 999;
  justify-content: center; align-items: center; cursor: pointer;
}}
#fullscreen img {{ max-width: 95%; max-height: 95%; border-radius: 8px; }}
.controls {{
  padding: 8px 20px; display: flex; gap: 10px; align-items: center;
}}
.controls button {{
  background: #1a1a3a; color: #0f0; border: 1px solid #333;
  padding: 6px 14px; border-radius: 5px; cursor: pointer; font-family: monospace;
}}
.controls button:hover {{ background: #2a2a4a; border-color: #0f0; }}
.controls select {{
  background: #1a1a3a; color: #eee; border: 1px solid #333;
  padding: 5px 10px; border-radius: 5px; font-family: monospace;
}}
</style>
</head>
<body>

<div class="header">
  <h1>TITAN LIVE CAMERA VIEWER</h1>
  <div class="stats">
    <div class="stat">Cameras: <b>{len(CAMERAS)}</b></div>
    <div class="stat">Online: <b>{online}</b></div>
    <div class="stat">Updated: <b>{ts}</b></div>
  </div>
</div>

<div class="controls">
  <button onclick="refreshAll()">Refresh All</button>
  <button onclick="toggleAutoRefresh()">Auto-Refresh: <span id="ar-status">ON</span></button>
  <select id="refreshRate" onchange="setRate(this.value)">
    <option value="3000">3s</option>
    <option value="5000" selected>5s</option>
    <option value="10000">10s</option>
    <option value="30000">30s</option>
  </select>
  <span style="color:#666;font-size:11px;margin-left:10px;">Click any camera to view fullscreen. Click RTSP URL to copy.</span>
</div>

<div class="grid" id="grid">{cam_grid}</div>

<div id="fullscreen" onclick="closeFull()">
  <img id="full-img" src="">
</div>

<script>
let autoRefresh = true;
let refreshRate = 5000;
let timer = null;

function refreshAll() {{
  document.querySelectorAll('.cam-img').forEach(img => {{
    const src = img.src.split('?')[0];
    img.src = src + '?t=' + Date.now();
  }});
}}

function toggleAutoRefresh() {{
  autoRefresh = !autoRefresh;
  document.getElementById('ar-status').textContent = autoRefresh ? 'ON' : 'OFF';
  if (autoRefresh) startTimer();
  else clearInterval(timer);
}}

function setRate(ms) {{
  refreshRate = parseInt(ms);
  if (autoRefresh) {{ clearInterval(timer); startTimer(); }}
}}

function startTimer() {{
  timer = setInterval(refreshAll, refreshRate);
}}

function openFull(safe) {{
  const img = document.getElementById('img-' + safe);
  const fs = document.getElementById('fullscreen');
  const fi = document.getElementById('full-img');
  fi.src = img.src;
  fs.style.display = 'flex';
}}

function closeFull() {{
  document.getElementById('fullscreen').style.display = 'none';
}}

document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') closeFull();
}});

// Start auto-refresh
startTimer();
refreshAll();
</script>

</body></html>'''


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=7701)
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--interval", type=int, default=4)
    args = p.parse_args()
    PORT = args.port
    MAX_WORKERS = args.workers
    REFRESH_INTERVAL = args.interval

    # Reload cameras
    CAMERAS = load_cameras()
    print(f"[INIT] Loaded {len(CAMERAS)} cameras from results")
    for i, c in enumerate(CAMERAS[:5]):
        print(f"  {i+1}. {c['ip']}:{c.get('port',554)} {c.get('path','?')}")
    if len(CAMERAS) > 5:
        print(f"  ... +{len(CAMERAS)-5} more")

    # Start snapshot grabber thread
    snap_thread = threading.Thread(target=snapshot_loop, daemon=True)
    snap_thread.start()
    print(f"[SNAP] Snapshot grabber started ({MAX_WORKERS} workers, {REFRESH_INTERVAL}s interval)")

    # Start HTTP server
    server = HTTPServer(('0.0.0.0', PORT), ViewerHandler)
    print(f"\n{'='*60}")
    print(f"  TITAN LIVE CAMERA VIEWER")
    print(f"  Open in browser: http://localhost:{PORT}")
    print(f"  {len(CAMERAS)} cameras | Auto-refreshing snapshots")
    print(f"{'='*60}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
