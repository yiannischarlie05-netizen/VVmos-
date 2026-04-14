#!/usr/bin/env python3
"""
Dialog IdeaBiz Location API — Single MSISDN Query

Official endpoint (docs.ideabiz.lk):
  GET https://ideabiz.lk/apicall/location/v1/queries/location?address={MSISDN}&requestedAccuracy=1000

Token via ideabiz_oauth.py (OAuth2 consumer_key/consumer_secret)
"""
import sys
import json
import requests

LOCATION_API_GET = "https://ideabiz.lk/apicall/location/v1/queries/location"
LOCATION_API_POST = "https://ideabiz.lk/apicall/location/v1/location/verify"

def normalize_msisdn(msisdn):
    msisdn = msisdn.strip().replace(" ", "").replace("-", "")
    if msisdn.startswith("tel:"): return msisdn
    if msisdn.startswith("+"): return f"tel:{msisdn}"
    if msisdn.startswith("94"): return f"tel:+{msisdn}"
    if msisdn.startswith("0"): return f"tel:+94{msisdn[1:]}"
    return f"tel:+{msisdn}"

def get_token():
    try:
        from ideabiz_oauth import IdeaBizAuth
        auth = IdeaBizAuth()
        t = auth.get_valid_token()
        if t: return f"Bearer {t}"
    except ImportError:
        pass
    return None

def get_location(msisdn, token=None):
    if not token:
        token = get_token()
    if not token:
        print("[!] No token. Configure IDEABIZ_CONSUMER_KEY/SECRET or run: python ideabiz_oauth.py --init")
        return
    if not token.startswith("Bearer"):
        token = f"Bearer {token}"

    normalized = normalize_msisdn(msisdn)
    headers = {"Authorization": token, "Accept": "application/json", "Content-Type": "application/json"}

    # Try official GET endpoint
    params = {"address": normalized, "requestedAccuracy": 1000}
    r = requests.get(LOCATION_API_GET, headers=headers, params=params, timeout=15)

    if r.status_code == 200:
        try:
            data = r.json()
            loc = data.get("terminalLocationList", {}).get("terminalLocation", {})
            curr = loc.get("currentLocation", {})
            if curr.get("latitude"):
                print(f"[✓] {msisdn} → lat={curr['latitude']}, lng={curr['longitude']}, acc={curr.get('accuracy','?')}m")
                return data
        except Exception:
            pass
        print(r.text)
    elif "900901" in r.text:
        print(f"[!] Subscription inactive (900901). Token is valid but subscription is still ON_HOLD.")
        print(f"[!] Contact support@ideabiz.lk to activate location v1 for DefaultApplication.")
    elif "900903" in r.text:
        print(f"[!] Token expired (900903). Run: python ideabiz_oauth.py --refresh")
    elif "900800" in r.text:
        print(f"[!] Rate limited (900800). Wait and retry.")
    else:
        print(f"[!] HTTP {r.status_code}: {r.text[:300]}")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dialog_location_query.py <MSISDN>")
        print("  Configure: export IDEABIZ_CONSUMER_KEY=xxx IDEABIZ_CONSUMER_SECRET=xxx")
        print("  Or: python ideabiz_oauth.py --init")
        sys.exit(1)
    get_location(sys.argv[1])