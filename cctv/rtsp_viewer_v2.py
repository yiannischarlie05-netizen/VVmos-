#!/usr/bin/env python3
"""
TITAN RTSP WEB VIEWER v2 — Fully dynamic SPA dashboard.
- Grabs JPEG snapshots via ffmpeg (threaded)
- Dashboard is a single-page app that fetches /api/cameras JSON
- Auto-reloads camera list from disk (picks up yolo_rooms.json etc.)
- Serves on 0.0.0.0 for external access
"""

import json, subprocess, threading, time, re as _re
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE = Path(__file__).resolve().parent
SNAP_DIR = BASE / "web_snapshots"
RESULTS = BASE / "results"
SNAP_DIR.mkdir(exist_ok=True)

PORT = 7701
REFRESH_INTERVAL = 5
MAX_WORKERS = 14

CAMERAS = []
CAM_STATUS = {}


def load_cameras() -> list:
    cams = {}
    for fname in ["yolo_rooms.json", "live_streams.json", "rtsp_blitz_live.json"]:
        p = RESULTS / fname
        if not p.exists():
            continue
        try:
            with open(p) as f:
                d = json.load(f)
            streams = d.get("streams", []) if isinstance(d, dict) else d
            for s in streams:
                ip = s.get("ip", "")
                if ip and ip not in cams:
                    cams[ip] = s
        except Exception:
            pass
    return list(cams.values())


def grab_snapshot(cam: dict) -> bool:
    ip = cam["ip"]
    url = cam.get("rtsp_url", "")
    if not url:
        return False
    safe = ip.replace(".", "_")
    out = SNAP_DIR / f"{safe}.jpg"
    tmp = SNAP_DIR / f"{safe}_tmp.jpg"
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp", "-timeout", "5000000",
             "-i", url, "-frames:v", "1", "-update", "1",
             "-vf", "scale=640:-1", "-q:v", "4", str(tmp)],
            capture_output=True, timeout=10, text=True)
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 800:
            tmp.rename(out)
            m = _re.search(r"(\d{2,5})x(\d{2,5})", r.stderr)
            reso = f"{m.group(1)}x{m.group(2)}" if m else "?"
            CAM_STATUS[ip] = {"last_ok": time.time(), "error": None, "resolution": reso}
            return True
        if tmp.exists():
            tmp.unlink()
    except subprocess.TimeoutExpired:
        if tmp.exists(): tmp.unlink()
    except Exception:
        pass
    CAM_STATUS.setdefault(ip, {})
    CAM_STATUS[ip]["error"] = "fail"
    return False


def snap_loop():
    while True:
        if not CAMERAS:
            time.sleep(2); continue
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            res = list(pool.map(grab_snapshot, list(CAMERAS)))
        ok = sum(res)
        print(f"[SNAP] {ok}/{len(CAMERAS)} frames in {time.time()-t0:.1f}s")
        time.sleep(max(0, REFRESH_INTERVAL - (time.time() - t0)))


def reload_loop():
    global CAMERAS
    while True:
        time.sleep(10)
        new = load_cameras()
        if len(new) != len(CAMERAS):
            CAMERAS.clear()
            CAMERAS.extend(new)
            print(f"[RELOAD] {len(CAMERAS)} cameras")


DASHBOARD = rb'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>TITAN LIVE CAMERAS</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#080812;color:#ddd;font-family:system-ui,'Segoe UI',monospace}
.hdr{background:linear-gradient(135deg,#1a0a2e,#0a1628);padding:10px 16px;border-bottom:2px solid #e00;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100}
.hdr h1{color:#e00;font-size:17px;white-space:nowrap}
.sts{display:flex;gap:10px}
.st{background:#0a0a1a;padding:3px 9px;border-radius:5px;font-size:11px;border:1px solid #222}
.st b{color:#0f0;font-size:14px}
.bar{padding:6px 16px;display:flex;gap:6px;flex-wrap:wrap;background:#0a0a14;border-bottom:1px solid #181828}
.fb{background:#181828;color:#777;border:1px solid #222;padding:2px 9px;border-radius:10px;cursor:pointer;font-size:10px;font-family:monospace}
.fb.a{color:#0f0;border-color:#0f0;background:#0a1a0a}
.ctrl{padding:5px 16px;display:flex;gap:6px;align-items:center;background:#0a0a14}
.ctrl button,.ctrl select{background:#181830;color:#0f0;border:1px solid #333;padding:4px 10px;border-radius:4px;cursor:pointer;font-family:monospace;font-size:11px}
.ctrl button:hover{background:#282848;border-color:#0f0}
.ctrl span{color:#444;font-size:10px}
.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:5px;padding:6px}
.c{background:#10102a;border:1px solid #252548;border-radius:7px;overflow:hidden;transition:border-color .2s}
.c:hover{border-color:#0ff}
.c.on{border-color:#1a3a1a}
.ch{display:flex;align-items:center;gap:4px;padding:4px 7px;background:#0c0c1e;font-size:11px}
.cn{color:#0f0;font-weight:bold;font-size:10px}
.ci{color:#0ff;font-size:10px}
.tg{margin-left:auto;display:flex;gap:2px}
.tg span{padding:1px 4px;border-radius:3px;font-size:8px;font-weight:bold}
.tg .bed{background:#3a1818;color:#f88}
.tg .couch{background:#18283a;color:#8cf}
.tg .chair{background:#2a2a18;color:#cc8}
.tg .tv{background:#182a2a;color:#8cc}
.tg .person{background:#2a182a;color:#c8c}
.cw{position:relative;background:#000;min-height:160px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.cw img{width:100%;display:block;transition:opacity .3s}
.cw .ph{color:#222;font-size:11px;position:absolute;pointer-events:none}
.cf{padding:3px 7px;font-size:9px;color:#555;border-top:1px solid #151530;display:flex;justify-content:space-between}
.cu{padding:2px 7px 4px;font-size:7px;color:#2a2a4a;word-break:break-all;cursor:pointer}
.cu:hover{color:#0ff}
#fs{display:none;position:fixed;inset:0;background:rgba(0,0,0,.96);z-index:999;justify-content:center;align-items:center;cursor:pointer}
#fs img{max-width:96%;max-height:96%;border-radius:6px}
.empty{text-align:center;padding:60px;color:#333;font-size:14px}
</style></head><body>
<div class="hdr"><h1>TITAN LIVE CAMERAS</h1>
<div class="sts"><div class="st">Total: <b id="t">0</b></div><div class="st">Online: <b id="o">0</b></div><div class="st">Rooms: <b id="r">0</b></div><div class="st" id="tm">--</div></div></div>
<div class="ctrl">
<button onclick="rx()">&#8635; Refresh</button>
<button onclick="ta()">Auto: <span id="ar">ON</span></button>
<select onchange="sr(this.value)"><option value=3000>3s</option><option value=5000 selected>5s</option><option value=10000>10s</option><option value=30000>30s</option></select>
<span>Click image=fullscreen | Click URL=copy</span></div>
<div class="bar" id="fb"></div>
<div class="g" id="g"></div>
<div id="fs" onclick="cf()"><img id="fi"></div>
<script>
let D=[],au=1,rt=5000,ti,fl='all';
async function ld(){try{const r=await fetch('/api/cameras');D=await r.json();up();bf();rn()}catch(e){}}
function up(){
document.getElementById('t').textContent=D.length;
document.getElementById('o').textContent=D.filter(c=>c.online).length;
document.getElementById('r').textContent=D.filter(c=>c.yolo_tags&&c.yolo_tags.length).length;
document.getElementById('tm').textContent=new Date().toLocaleTimeString()}
function bf(){const s=new Set();D.forEach(c=>(c.yolo_tags||[]).forEach(t=>s.add(t)));
let h='<div class="fb'+(fl==='all'?' a':'')+'" onclick="sf(\'all\',this)">ALL ('+D.length+')</div>';
h+='<div class="fb'+(fl==='online'?' a':'')+'" onclick="sf(\'online\',this)">ONLINE ('+D.filter(c=>c.online).length+')</div>';
h+='<div class="fb'+(fl==='rooms'?' a':'')+'" onclick="sf(\'rooms\',this)">ROOMS ('+D.filter(c=>c.yolo_tags&&c.yolo_tags.length).length+')</div>';
s.forEach(t=>{const n=D.filter(c=>(c.yolo_tags||[]).includes(t)).length;
h+='<div class="fb'+(fl===t?' a':'')+'" onclick="sf(\''+t+'\',this)">'+t.toUpperCase()+' ('+n+')</div>'});
document.getElementById('fb').innerHTML=h}
function sf(f,el){fl=f;document.querySelectorAll('.fb').forEach(b=>b.classList.remove('a'));if(el)el.classList.add('a');rn()}
function rn(){const g=document.getElementById('g');let f=D;
if(fl==='online')f=D.filter(c=>c.online);
else if(fl==='rooms')f=D.filter(c=>c.yolo_tags&&c.yolo_tags.length);
else if(fl!=='all')f=D.filter(c=>(c.yolo_tags||[]).includes(fl));
if(!f.length){g.innerHTML='<div class="empty">No cameras matching filter "'+fl+'"</div>';return}
let h='';f.forEach((c,i)=>{const s=c.ip.replace(/\./g,'_'),on=c.online,
tags=(c.yolo_tags||[]).map(t=>'<span class="'+t+'">'+t+'</span>').join(''),
au=c.user?c.user+':***':'OPEN';
h+='<div class="c'+(on?' on':'')+'" id="c-'+s+'"><div class="ch"><span class="cn">#'+(i+1)+'</span>'
+'<span>'+(on?'\u{1F7E2}':'\u{1F534}')+'</span><span class="ci">'+c.ip+':'+( c.port||554)+'</span>'
+'<div class="tg">'+tags+'</div></div>'
+'<div class="cw" onclick="of(\''+s+'\')"><img src="/snap/'+s+'.jpg?t='+Date.now()+'" loading="lazy" '
+'onerror="this.style.opacity=0.1" onload="this.style.opacity=1"><span class="ph">\u23F3</span></div>'
+'<div class="cf"><span>'+(c.resolution||'?')+'</span><span>'+au+'</span><span>'+(c.room||'')+'</span></div>'
+'<div class="cu" onclick="event.stopPropagation();navigator.clipboard.writeText(\''+( c.rtsp_url||'')+'\');this.style.color=\'#0f0\'">'+(c.rtsp_url||'')+'</div></div>'});
g.innerHTML=h})
function rx(){document.querySelectorAll('.cw img').forEach(i=>{const s=i.src.split('?')[0];i.src=s+'?t='+Date.now()});ld()}
function ta(){au=!au;document.getElementById('ar').textContent=au?'ON':'OFF';au?st():clearInterval(ti)}
function sr(v){rt=+v;if(au){clearInterval(ti);st()}}
function st(){ti=setInterval(rx,rt)}
function of(s){const i=document.querySelector('#c-'+s+' img');if(i){document.getElementById('fi').src=i.src;document.getElementById('fs').style.display='flex'}}
function cf(){document.getElementById('fs').style.display='none'}
document.addEventListener('keydown',e=>{if(e.key==='Escape')cf()});
ld();st();
</script></body></html>'''


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        if p.startswith("/snap/"):
            fn = p[6:]
            if not _re.match(r'^[\d_]+\.jpg$', fn):
                self.send_response(404); self.end_headers(); return
            fp = SNAP_DIR / fn
            if fp.exists():
                data = fp.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache, no-store")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404); self.end_headers()
        elif p.startswith("/api/cameras"):
            out = []
            for c in CAMERAS:
                ip = c["ip"]
                st = CAM_STATUS.get(ip, {})
                out.append({
                    "ip": ip, "port": c.get("port", 554),
                    "rtsp_url": c.get("rtsp_url", ""),
                    "user": c.get("user", ""),
                    "resolution": st.get("resolution", c.get("resolution", "?")),
                    "online": (time.time() - st.get("last_ok", 0)) < 45,
                    "error": st.get("error"),
                    "yolo_tags": c.get("yolo_tags", []),
                    "room": c.get("room", ""),
                })
            payload = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(payload)
        elif p in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(DASHBOARD)))
            self.end_headers()
            self.wfile.write(DASHBOARD)
        else:
            self.send_response(404); self.end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7701)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--interval", type=int, default=5)
    args = ap.parse_args()
    PORT, MAX_WORKERS, REFRESH_INTERVAL = args.port, args.workers, args.interval

    CAMERAS.extend(load_cameras())
    print(f"[INIT] {len(CAMERAS)} cameras loaded")
    for c in CAMERAS[:3]:
        print(f"  - {c['ip']}:{c.get('port',554)} {c.get('path','')}")
    if len(CAMERAS) > 3:
        print(f"  ... +{len(CAMERAS)-3} more")

    threading.Thread(target=snap_loop, daemon=True).start()
    threading.Thread(target=reload_loop, daemon=True).start()
    print(f"[SNAP] {MAX_WORKERS} workers, {REFRESH_INTERVAL}s interval")

    srv = HTTPServer(('0.0.0.0', PORT), H)
    print(f"\n  TITAN LIVE CAMERAS — http://0.0.0.0:{PORT}\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("Done.")
