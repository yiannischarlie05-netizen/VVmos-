#!/usr/bin/env python3
"""
Dialog IdeaBiz Location API — Batch MSISDN Query

Usage: python dialog_location_batch.py 94771234567 94771234568 ...
       or: cat numbers.txt | xargs python dialog_location_batch.py

Official endpoint (docs.ideabiz.lk):
  GET https://ideabiz.lk/apicall/location/v1/queries/location?address={MSISDN}&requestedAccuracy=1000

Note: Subscription must be in UNBLOCKED/ACTIVE state (not ON_HOLD).
      Contact IdeaBiz support to activate: support@ideabiz.lk
"""
import sys
import time
import json
import requests

LOCATION_API_GET = "https://ideabiz.lk/apicall/location/v1/queries/location"


def normalize_msisdn(msisdn):
    msisdn = msisdn.strip().replace(" ", "").replace("-", "")
    if msisdn.startswith("tel:"):
        return msisdn
    if msisdn.startswith("+"):
        return f"tel:{msisdn}"
    if msisdn.startswith("94"):
        return f"tel:+{msisdn}"
    if msisdn.startswith("0"):
        return f"tel:+94{msisdn[1:]}"
    return f"tel:+{msisdn}"


def get_token():
    try:
        from ideabiz_oauth import IdeaBizAuth
        auth = IdeaBizAuth()
        t = auth.get_valid_token()
        if t:
            return f"Bearer {t}"
    except Exception as e:
        print(f"[!] OAuth error: {e}")
    return None


def get_location_batch(msisdns, token=None, delay=1.5):
    if not token:
        token = get_token()
    if not token:
        print("[!] No token. Configure IDEABIZ_CONSUMER_KEY/SECRET.")
        return {}
    if not token.startswith("Bearer"):
        token = f"Bearer {token}"

    headers = {
        "Authorization": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    results = {}
    for msisdn in msisdns:
        normalized = normalize_msisdn(msisdn)
        params = {"address": normalized, "requestedAccuracy": 1000}
        try:
            r = requests.get(LOCATION_API_GET, headers=headers, params=params, timeout=15)
            if r.status_code == 200:
                try:
                    data = r.json()
                    loc = data.get("terminalLocationList", {}).get("terminalLocation", {})
                    curr = loc.get("currentLocation", {})
                    if curr.get("latitude"):
                        result = {
                            "lat": curr["latitude"],
                            "lng": curr["longitude"],
                            "accuracy": curr.get("accuracy", "?"),
                            "timestamp": curr.get("timestamp", ""),
                            "status": "ok",
                        }
                        print(f"[+] {msisdn} → lat={result['lat']}, lng={result['lng']}, acc={result['accuracy']}m")
                        results[msisdn] = result
                        continue
                except Exception:
                    pass
                print(f"[?] {msisdn} → HTTP 200 but unexpected response: {r.text[:200]}")
            elif "900901" in r.text:
                print(f"[!] {msisdn} → Subscription not active (900901). Contact IdeaBiz support.")
                results[msisdn] = {"status": "subscription_inactive"}
            elif "900903" in r.text:
                print(f"[!] {msisdn} → Token expired (900903). Refreshing...")
                token = get_token()
                if token and not token.startswith("Bearer"):
                    token = f"Bearer {token}"
                headers["Authorization"] = token or headers["Authorization"]
                results[msisdn] = {"status": "token_expired"}
            elif "900800" in r.text:
                print(f"[!] {msisdn} → Rate limited (900800). Increasing delay.")
                delay = delay * 2
                results[msisdn] = {"status": "rate_limited"}
            else:
                print(f"[!] {msisdn} → HTTP {r.status_code}: {r.text[:200]}")
                results[msisdn] = {"status": f"http_{r.status_code}"}
        except Exception as e:
            print(f"[!] {msisdn} → Error: {e}")
            results[msisdn] = {"status": "error", "error": str(e)}

        time.sleep(delay)

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dialog_location_batch.py <MSISDN> [MSISDN2] ...")
        print("  Example: python dialog_location_batch.py 94771234567 94779876543")
        sys.exit(1)
    msisdns = sys.argv[1:]
    print(f"[*] Querying {len(msisdns)} number(s)...")
    results = get_location_batch(msisdns)
    print("\n[*] Summary:")
    print(json.dumps(results, indent=2))