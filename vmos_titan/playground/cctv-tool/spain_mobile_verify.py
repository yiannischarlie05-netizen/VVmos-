import os
import glob
import json
import base64
import time
import shutil

# Paths
SPAIN_FRAMES_DIR = "spain_frames"
OUT_DIR = "spain_mobile_verify"
IMG_DIR = os.path.join(OUT_DIR, "screenshots")
MANIFEST_FILE = os.path.join(OUT_DIR, "manifest.json")
GALLERY_FILE = os.path.join(OUT_DIR, "gallery.html")
M3U_FILE = os.path.join(OUT_DIR, "cameras.m3u")
SELECTOR_FILE = os.path.join(OUT_DIR, "screenshot_selector.html")

def main():
    print("🚀 Building Spain Mobile Verification Toolkit...")
    
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    
    # 1. Find all frames
    frames = glob.glob(os.path.join(SPAIN_FRAMES_DIR, "*.jpg"))
    print(f"[*] Found {len(frames)} raw frame files in {SPAIN_FRAMES_DIR}/")
    
    cameras = []
    
    for frame_path in frames:
        # Check size to ensure valid frame
        size_bytes = os.path.getsize(frame_path)
        if size_bytes < 5000:  # Skip tiny/broken frames (<5KB)
            continue
            
        filename = os.path.basename(frame_path)
        # Format: 109_227_132_113.jpg
        name_parts = filename.replace('.jpg', '').split('_')
        ip = '.'.join(name_parts)
        
        # Copy file to output dir for web serving
        dst_frame = os.path.join(IMG_DIR, filename)
        shutil.copy2(frame_path, dst_frame)
        
        rtsp_url = f"rtsp://admin:12345@{ip}:554/Streaming/Channels/101"
        
        cameras.append({
            "ip": ip,
            "scene": "spain_camera",  # Default scene since it's not pre-classified
            "priority": False,
            "size_bytes": size_bytes,
            "frame_path": dst_frame,
            "screenshot_url": f"screenshots/{filename}",
            "rtsp_urls": [rtsp_url],
            "http_urls": [
                f"http://{ip}/",
                f"http://{ip}:8000/",
                f"http://{ip}:8080/"
            ],
            "status": "valid",
            "protocol": "rtsp",
            "port": 554
        })
    
    # Sort largely by file size descending (biggest = most detail usually)
    cameras.sort(key=lambda x: x['size_bytes'], reverse=True)
    
    print(f"[+] Processed {len(cameras)} valid cameras (>5KB frames)")
    
    # 2. Generate JSON Manifest
    manifest = {
        "title": "Spain Camera Hunt Results",
        "timestamp": str(time.time()),
        "total": len(cameras),
        "priority_count": 0,
        "cameras": cameras
    }
    
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"[+] Wrote {MANIFEST_FILE}")
    
    # 3. Generate Basic M3U File (All cameras)
    m3u_content = "#EXTM3U\n# SPAIN CAMERA HUNT - VLC PLAYLIST\n"
    for cam in cameras:
        m3u_content += f"#EXTINF:-1,[ES] src - {cam['ip']}\n"
        m3u_content += f"{cam['rtsp_urls'][0]}\n\n"
        
    with open(M3U_FILE, 'w') as f:
        f.write(m3u_content)
    print(f"[+] Wrote {M3U_FILE}")
    
    # 4. Generate Interactive Selector HTML
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🇪🇸 Spain Camera Screenshot Selector</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #1a1a1a; color: #fff; padding: 20px; line-height: 1.6; }
        .header { max-width: 1400px; margin: 0 auto 30px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; color: #ffca28; }
        .stats { display: flex; justify-content: center; gap: 30px; font-size: 1.1em; margin-bottom: 20px; }
        .stat { background: #2a2a2a; padding: 10px 20px; border-radius: 5px; }
        .stat strong { color: #4ecdc4; }
        .controls { max-width: 1400px; margin: 0 auto 20px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; justify-content: center; }
        button { background: #4ecdc4; color: #000; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 1em; transition: all 0.3s; }
        button:hover { background: #45b8af; transform: scale(1.05); }
        .grid { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; padding: 20px 0; }
        .camera-card { background: #2a2a2a; border-radius: 8px; overflow: hidden; transition: all 0.3s; cursor: pointer; border: 2px solid transparent; position: relative; }
        .camera-card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(78, 205, 196, 0.2); border-color: #4ecdc4; }
        .camera-card.selected { border-color: #ff6b6b; box-shadow: 0 0 15px rgba(255, 107, 107, 0.5); }
        .checkbox-overlay { position: absolute; top: 10px; left: 10px; z-index: 10; }
        .checkbox-overlay input[type="checkbox"] { width: 20px; height: 20px; cursor: pointer; }
        .screenshot { width: 100%; height: 180px; object-fit: cover; display: block; }
        .info { padding: 12px; background: #1a1a1a; }
        .info-title { font-weight: bold; color: #4ecdc4; margin-bottom: 5px; font-size: 0.9em; word-break: break-all; }
        .info-meta { display: flex; justify-content: space-between; font-size: 0.85em; color: #999; }
        .badge { display: inline-block; background: #ffca28; color: #000; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; margin-right: 5px; }
        .selected-count { background: #ff6b6b; color: #fff; padding: 10px 20px; border-radius: 5px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🇪🇸 Spain Live Cameras Selector</h1>
        <p>Live streams acquired from the ongoing Masscan hunt</p>
        <div class="stats">
            <div class="stat">Total Valid Cameras: <strong id="total-count">0</strong></div>
            <div class="stat">Selected: <strong><span id="selected-count">0</span></strong></div>
        </div>
    </div>
    
    <div class="controls">
        <button onclick="selectAll()">✓ Select All</button>
        <button onclick="deselectAll()">✗ Deselect All</button>
        <button onclick="downloadPlaylist()" class="selected-count">⬇️ Download Selected (.m3u)</button>
    </div>
    
    <div class="grid" id="grid"></div>

    <script>
        let allCameras = [];
        let selectedCameras = new Set();
        
        fetch('manifest.json')
            .then(r => r.json())
            .then(data => {
                allCameras = data.cameras || [];
                document.getElementById('total-count').textContent = allCameras.length;
                renderGrid();
            })
            .catch(e => console.error('Error loading manifest:', e));
        
        function renderGrid() {
            const grid = document.getElementById('grid');
            grid.innerHTML = '';
            
            allCameras.forEach((cam, idx) => {
                const card = document.createElement('div');
                card.className = 'camera-card';
                if (selectedCameras.has(idx)) card.classList.add('selected');
                
                const imgUrl = cam.screenshot_url ? cam.screenshot_url : 'data:image/svg+xml,...';
                
                card.innerHTML = `
                    <div class="checkbox-overlay">
                        <input type="checkbox" ${selectedCameras.has(idx) ? 'checked' : ''} 
                               onchange="toggleSelect(${idx})">
                    </div>
                    <img src="${imgUrl}" alt="${cam.ip}" class="screenshot" loading="lazy">
                    <div class="info">
                        <div class="info-title">${cam.ip}</div>
                        <div class="info-meta">
                            <span class="badge">🇪🇸 Spain</span>
                            <span>${(cam.size_bytes / 1024).toFixed(0)}KB</span>
                        </div>
                    </div>
                `;
                
                card.onclick = (e) => {
                    if (e.target.tagName !== 'INPUT') {
                        const checkbox = card.querySelector('input[type="checkbox"]');
                        checkbox.checked = !checkbox.checked;
                        toggleSelect(idx);
                    }
                };
                
                grid.appendChild(card);
            });
        }
        
        function toggleSelect(idx) {
            if (selectedCameras.has(idx)) selectedCameras.delete(idx);
            else selectedCameras.add(idx);
            updateUI();
        }
        
        function selectAll() {
            allCameras.forEach((_, idx) => selectedCameras.add(idx));
            updateUI();
        }
        
        function deselectAll() {
            selectedCameras.clear();
            updateUI();
        }
        
        function updateUI() {
            document.getElementById('selected-count').textContent = selectedCameras.size;
            document.querySelectorAll('.camera-card').forEach((card, idx) => {
                if (selectedCameras.has(idx)) {
                    card.classList.add('selected');
                    card.querySelector('input[type="checkbox"]').checked = true;
                } else {
                    card.classList.remove('selected');
                    card.querySelector('input[type="checkbox"]').checked = false;
                }
            });
        }
        
        function downloadPlaylist() {
            if (selectedCameras.size === 0) {
                alert('Please select at least one camera');
                return;
            }
            
            let m3u = '#EXTM3U\\n# SPAIN CAMERA HUNT - CUSTOM SELECTION\\n';
            m3u += `# Generated: ${new Date().toLocaleString()}\\n`;
            m3u += `# Selected: ${selectedCameras.size} cameras\\n\\n`;
            
            document.querySelectorAll('.camera-card.selected').forEach((card, i) => {
                const idx = Array.from(document.querySelectorAll('.camera-card')).indexOf(card);
                if (selectedCameras.has(idx)) {
                    const cam = allCameras[idx];
                    if (cam.rtsp_urls && cam.rtsp_urls[0]) {
                        m3u += `#EXTINF:-1,[ES] Spain - ${cam.ip}\\n${cam.rtsp_urls[0]}\\n\\n`;
                    }
                }
            });
            
            const blob = new Blob([m3u], { type: 'audio/x-mpegurl' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `spain_cameras_selected_${selectedCameras.size}.m3u`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        }
    </script>
</body>
</html>
"""
    with open(SELECTOR_FILE, 'w') as f:
        f.write(html_template)
    print(f"[+] Wrote {SELECTOR_FILE}")
    print("[✓] All done! Ready to serve.")

if __name__ == "__main__":
    main()
