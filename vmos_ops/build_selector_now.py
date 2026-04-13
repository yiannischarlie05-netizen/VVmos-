#!/usr/bin/env python3
"""
Fast builder: classify all existing frames and build the selector immediately.
Used by spain_indoor_hunt to save the selector whenever needed.
"""

import os, json, shutil, time, cv2, numpy as np
from pathlib import Path


def classify_indoor(filepath):
    """Fast CV-based indoor/outdoor classification. Returns (is_indoor, score, details)."""
    try:
        img = cv2.imread(filepath)
        if img is None:
            return False, 0, "unreadable"

        h, w = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        brightness = np.mean(hsv[:, :, 2])
        saturation_mean = np.mean(hsv[:, :, 1])

        # Edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w)

        # Sky detection (top quarter)
        top_q = hsv[:h // 4, :, :]
        top_bright = np.mean(top_q[:, :, 2])
        top_sat = np.mean(top_q[:, :, 1])

        # Green vegetation
        green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
        green_pct = np.sum(green_mask > 0) / (h * w)

        # Blue sky
        blue_mask = cv2.inRange(hsv, np.array([100, 40, 100]), np.array([130, 255, 255]))
        blue_pct = np.sum(blue_mask > 0) / (h * w)

        # Warm colors (indoor lighting)
        warm_mask = cv2.inRange(hsv, np.array([10, 30, 100]), np.array([30, 200, 255]))
        warm_pct = np.sum(warm_mask > 0) / (h * w)

        # IR / night vision detection (grayscale camera)
        is_ir = saturation_mean < 30

        # Scoring
        indoor_score = 0
        outdoor_score = 0
        tags = []

        if brightness < 140:
            indoor_score += 1.5
            tags.append("dim")
        if edge_density > 0.08:
            indoor_score += 1
            tags.append("complex")
        if warm_pct > 0.05:
            indoor_score += 1
            tags.append("warm-light")
        if is_ir:
            indoor_score += 2
            tags.append("IR-nightvision")

        if top_bright > 200 and top_sat < 60:
            outdoor_score += 2
            tags.append("sky")
        if green_pct > 0.12:
            outdoor_score += 1.5
            tags.append("vegetation")
        if blue_pct > 0.08:
            outdoor_score += 1
            tags.append("blue-sky")
        if brightness > 180:
            outdoor_score += 0.5
            tags.append("bright")

        is_indoor = indoor_score > outdoor_score
        detail = f"in={indoor_score:.1f} out={outdoor_score:.1f} [{','.join(tags)}]"
        return is_indoor, indoor_score, detail

    except Exception as e:
        return False, 0, str(e)


def build_html_selector(indoor_cams, out_dir):
    """Build the interactive HTML selector."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🇪🇸🏠 Spain Indoor Cameras Live</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#111;color:#fff;padding:15px}
.header{text-align:center;margin-bottom:20px}
.header h1{font-size:2em;color:#ff6b6b;margin-bottom:5px}
.stats{display:flex;justify-content:center;gap:20px;margin:15px 0;flex-wrap:wrap}
.stat{background:#222;padding:8px 16px;border-radius:5px}
.stat strong{color:#4ecdc4}
.controls{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-bottom:15px}
button{background:#4ecdc4;color:#000;border:none;padding:10px 18px;border-radius:5px;cursor:pointer;font-weight:bold;font-size:0.95em}
button:active{background:#45b8af}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.card{background:#222;border-radius:8px;overflow:hidden;cursor:pointer;border:2px solid transparent;position:relative;transition:all 0.2s}
.card:hover{border-color:#4ecdc4;transform:translateY(-3px)}
.card.selected{border-color:#ff6b6b;box-shadow:0 0 12px rgba(255,107,107,0.5)}
.card input[type=checkbox]{position:absolute;top:8px;left:8px;width:18px;height:18px;z-index:5;cursor:pointer}
.card img{width:100%;height:160px;object-fit:cover;display:block}
.card .info{padding:8px 10px;font-size:0.85em}
.card .ip{color:#4ecdc4;font-weight:bold;word-break:break-all;font-size:0.9em}
.card .tags{color:#999;font-size:0.8em;margin-top:3px}
.card .vlc-btn{display:block;background:#ff6b6b;color:#fff;text-align:center;padding:6px;font-size:0.85em;text-decoration:none;font-weight:bold;border:none}
.card .vlc-btn:active{background:#ff5252}
.dl-btn{background:#ff6b6b;color:#fff}
.dl-btn:active{background:#ff5252}
#count{color:#ff6b6b}
.updated{font-size:0.9em;color:#999;margin-top:5px}
</style>
</head>
<body>
<div class="header">
<h1>🇪🇸🏠 Spain Home/Indoor Cameras LIVE</h1>
<p>Real-time indoor camera detection — tap to play in VLC</p>
<div class="stats">
<div class="stat">🏠 Indoor: <strong id="total">0</strong></div>
<div class="stat">✓ Selected: <strong id="count">0</strong></div>
</div>
<div class="updated">Last updated: <span id="updated">loading...</span></div>
</div>
<div class="controls">
<button onclick="selAll()">✓ Select All</button>
<button onclick="deselAll()">✗ Deselect All</button>
<button class="dl-btn" onclick="dlPlaylist()">⬇️ Download .m3u</button>
<button onclick="location.reload()">🔄 Refresh</button>
</div>
<div class="grid" id="grid"></div>
<script>
let cams=[],sel=new Set();
function load(){
    fetch('manifest.json?t='+Date.now()).then(r=>r.json()).then(d=>{
        cams=d.cameras||[];
        document.getElementById('total').textContent=cams.length;
        document.getElementById('updated').textContent=new Date(parseInt(d.timestamp)*1000).toLocaleString();
        render();
    }).catch(e=>console.log('Load error:',e));
}
function render(){
    const g=document.getElementById('grid');
    g.innerHTML='';
    cams.forEach((c,i)=>{
        const d=document.createElement('div');
        d.className='card'+(sel.has(i)?' selected':'');
        const rtsp=c.rtsp_urls&&c.rtsp_urls[0]?c.rtsp_urls[0]:'';
        d.innerHTML=`
            <input type="checkbox" ${sel.has(i)?'checked':''} onchange="tog(${i})" onclick="event.stopPropagation()">
            <img src="${c.screenshot_url||''}" alt="${c.ip}" loading="lazy" style="cursor:pointer">
            <div class="info">
                <div class="ip">${c.ip}</div>
                <div class="tags">${(c.size_bytes/1024/1024).toFixed(1)}MB · ${c.indoor_score.toFixed(1)}</div>
            </div>
            <a class="vlc-btn" href="vlc://${rtsp}" onclick="event.stopPropagation()">▶ Play in VLC</a>`;
        d.onclick=e=>{if(e.target.tagName==='IMG'){const a=d.querySelector('.vlc-btn');window.open(a.href);}};
        g.appendChild(d);
    });
}
function tog(i){sel.has(i)?sel.delete(i):sel.add(i);upd();}
function selAll(){cams.forEach((_,i)=>sel.add(i));upd();}
function deselAll(){sel.clear();upd();}
function upd(){
    document.getElementById('count').textContent=sel.size;
    document.querySelectorAll('.card').forEach((c,i)=>{
        c.classList.toggle('selected',sel.has(i));
        c.querySelector('input').checked=sel.has(i);
    });
}
function dlPlaylist(){
    if(!sel.size){alert('Select cameras first');return;}
    let m='#EXTM3U\\n# SPAIN INDOOR CAMERAS\\n';
    sel.forEach(i=>{
        const c=cams[i];
        if(c.rtsp_urls&&c.rtsp_urls[0])
            m+=`#EXTINF:-1,[🇪🇸 ${c.ip}]\\n${c.rtsp_urls[0]}\\n`;
    });
    const b=new Blob([m],{type:'audio/x-mpegurl'});
    const a=document.createElement('a');
    a.href=URL.createObjectURL(b);
    a.download=`spain_indoor_${sel.size}_${Date.now()}.m3u`;
    a.click();
}
load();
setInterval(load, 5000);  // Auto-refresh every 5s
</script>
</body>
</html>"""
    
    with open(os.path.join(out_dir, "screenshot_selector.html"), 'w') as f:
        f.write(html)


def build_selector(indoor_cams, out_dir):
    """Build manifest.json, cameras.m3u, and HTML selector from a list of indoor cameras."""
    os.makedirs(os.path.join(out_dir, "screenshots"), exist_ok=True)

    # Copy screenshots
    for cam in indoor_cams:
        src = cam["frame_path"]
        if os.path.exists(src):
            dst = os.path.join(out_dir, "screenshots", os.path.basename(src))
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            cam["screenshot_url"] = f"screenshots/{os.path.basename(src)}"

    # Manifest
    manifest = {
        "title": "Spain HOME/INDOOR Cameras Live",
        "timestamp": str(int(time.time())),
        "total": len(indoor_cams),
        "cameras": indoor_cams
    }
    with open(os.path.join(out_dir, "manifest.json"), 'w') as f:
        json.dump(manifest, f, indent=2)

    # M3U
    m3u = "#EXTM3U\n# SPAIN HOME/INDOOR CAMERAS\n"
    for cam in indoor_cams:
        m3u += f"#EXTINF:-1,[🏠 ES] {cam['ip']}\n"
        m3u += f"{cam['rtsp_urls'][0]}\n\n"
    with open(os.path.join(out_dir, "cameras.m3u"), 'w') as f:
        f.write(m3u)

    # HTML Selector
    build_html_selector(indoor_cams, out_dir)


def main():
    SCRIPT_DIR = "/root/vmos-titan-unified/vmos_titan/playground/cctv-tool"
    os.chdir(SCRIPT_DIR)
    
    FRAMES_DIR = os.path.join(SCRIPT_DIR, "spain_frames")
    OUT_DIR = os.path.join(SCRIPT_DIR, "spain_indoor_verify")
    
    print("[*] Building selector from existing frames...")
    indoor_cams = []
    
    # Classify all frames in spain_frames/
    frame_files = sorted([f for f in os.listdir(FRAMES_DIR) if f.endswith('.jpg')])
    print(f"[*] Found {len(frame_files)} frames to classify")
    
    for idx, frame_file in enumerate(frame_files):
        filepath = os.path.join(FRAMES_DIR, frame_file)
        is_indoor, score, detail = classify_indoor(filepath)
        
        if is_indoor:
            ip = frame_file.replace('.jpg', '').replace('_', '.')
            size_mb = os.path.getsize(filepath) / (1024*1024)
            
            cam = {
                "ip": ip,
                "frame_path": filepath,
                "indoor_score": float(score),
                "indoor_detail": detail,
                "size_bytes": os.path.getsize(filepath),
                "rtsp_urls": [f"rtsp://admin:12345@{ip}:554/Streaming/Channels/101"],
                "screenshot_url": ""
            }
            indoor_cams.append(cam)
            print(f"[+] {idx+1}/{len(frame_files)} | INDOOR: {ip} (score={score:.1f})")
        else:
            print(f"[-] {idx+1}/{len(frame_files)} | outdoor: {frame_file[:20]}...")
    
    print(f"\n[✓] Classified {len(indoor_cams)}/{len(frame_files)} as INDOOR")
    
    # Sort by score descending
    indoor_cams.sort(key=lambda x: x['indoor_score'], reverse=True)
    
    # Build selector
    build_selector(indoor_cams, OUT_DIR)
    
    print(f"[✓] Selector built to {OUT_DIR}")
    print(f"[✓] Files created:")
    print(f"    - manifest.json ({len(indoor_cams)} cameras)")
    print(f"    - cameras.m3u")
    print(f"    - screenshot_selector.html")
    print(f"    - screenshots/ ({len(indoor_cams)} images)")


if __name__ == '__main__':
    main()
