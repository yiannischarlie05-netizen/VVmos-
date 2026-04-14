#!/usr/bin/env python3
"""
IdeaBiz Subscription Status Checker & Poller

Checks if the location/DeviceLocation API subscriptions have been approved by
the IdeaBiz admin team (ON_HOLD → UNBLOCKED).

Usage:
  python subscription_checker.py         # Check once
  python subscription_checker.py --poll  # Poll every 5 minutes until active

Contact IdeaBiz to activate: support@ideabiz.lk
  - Mention: DefaultApplication (id=45956)
  - APIs: location v1, DeviceLocation v1
"""
import sys
import time
import json
import requests

STORE_URL = "https://ideabiz.lk"
APP_NAME = "DefaultApplication"


def check_subscriptions(username="lucifer25", password="Chilaw@123"):
    s = requests.Session()

    # Login
    resp = s.post(
        f"{STORE_URL}/store/site/blocks/user/login/ajax/login.jag",
        data={"action": "login", "username": username, "password": password},
        timeout=15,
        verify=False,
    )
    if "error" not in resp.text or '"error" : false' not in resp.text:
        try:
            d = resp.json()
            if d.get("error") is True:
                print(f"[!] Login failed: {d.get('message')}")
                return None
        except Exception:
            print(f"[!] Login response: {resp.text[:200]}")
            return None

    # Get subscriptions
    resp = s.post(
        f"{STORE_URL}/store/site/blocks/subscription/subscription-list/ajax/subscription-list.jag",
        data={"action": "getSubscriptionByApplication", "app": APP_NAME},
        timeout=15,
        verify=False,
    )
    try:
        data = resp.json()
    except Exception:
        print(f"[!] Bad response: {resp.text[:200]}")
        return None

    if data.get("error"):
        print(f"[!] Error: {data.get('message')}")
        return None

    return data.get("apis", [])


def print_status(apis):
    all_active = True
    for api in apis:
        name = api.get("apiName", "?")
        version = api.get("apiVersion", "?")
        sub_status = api.get("subStatus", "?")
        operators = api.get("operators", "?")

        if sub_status in ("ON_HOLD", "PENDING"):
            icon = "⏳"
            all_active = False
        elif sub_status == "UNBLOCKED":
            icon = "✅"
        else:
            icon = "❓"
            all_active = False

        print(f"  {icon} {name} v{version}: {sub_status} (operators: {operators})")

    return all_active


def check_token_works(username="lucifer25", password="Chilaw@123"):
    """Try to generate a token and hit the Location API."""
    try:
        import base64
        import importlib

        # Read config.json
        try:
            with open("config.json") as f:
                cfg = json.load(f)
            ck = cfg.get("auth_consumerKey", "")
            cs = cfg.get("auth_consumerSecret", "")
        except Exception:
            print("[!] config.json not found")
            return False

        client_creds = base64.b64encode(f"{ck}:{cs}".encode()).decode()
        import warnings
        warnings.filterwarnings("ignore")

        resp = requests.post(
            "https://ideabiz.lk/apicall/token",
            headers={"Authorization": f"Basic {client_creds}"},
            data={"grant_type": "client_credentials"},
            timeout=15,
            verify=False,
        )
        token_data = resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            print(f"[!] Token generation failed: {resp.text[:200]}")
            return False

        # Try Location API
        resp = requests.get(
            "https://ideabiz.lk/apicall/location/v1/queries/location",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            params={"address": "tel:+94771234567", "requestedAccuracy": 1000},
            timeout=15,
            verify=False,
        )

        if resp.status_code == 200:
            print(f"[✓] Location API WORKING! Response: {resp.text[:300]}")
            return True
        elif "900901" in resp.text:
            print(f"[✗] Location API subscription still inactive (sub status: ON_HOLD)")
            return False
        elif "900904" in resp.text:
            print(f"[✗] Token inactive (900904)")
            return False
        else:
            print(f"[?] HTTP {resp.status_code}: {resp.text[:200]}")
            return False

    except Exception as e:
        print(f"[!] Error: {e}")
        return False


def main():
    poll = "--poll" in sys.argv
    quiet = "--quiet" in sys.argv

    if not quiet:
        print("=" * 60)
        print("  IdeaBiz Subscription Status Checker")
        print("=" * 60)
        print(f"  Account: lucifer25")
        print(f"  Application: {APP_NAME} (id=45956)")
        print()

    import warnings
    warnings.filterwarnings("ignore")

    while True:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking subscription status...")
        apis = check_subscriptions()

        if apis is None:
            print("[!] Could not retrieve subscription status")
        elif not apis:
            print("[!] No subscriptions found")
        else:
            all_active = print_status(apis)

            if all_active:
                print("\n[✓] ALL SUBSCRIPTIONS ACTIVE!")
                print("[*] Testing Location API with live token...")
                if check_token_works():
                    print("\n[✓] SYSTEM READY — Location API fully operational")
                    break
                else:
                    print("[!] Subscriptions active but API test failed. Retrying...")
            else:
                print("\n[!] Subscriptions still ON_HOLD.")
                print("[!] To activate, contact IdeaBiz:")
                print("    Email: support@ideabiz.lk or info@ideabiz.lk")
                print("    Phone: +94 11 480 6666 (Dialog)")
                print("    Subject: 'API Subscription Activation - lucifer25 DefaultApplication'")
                print("    Body: 'Please approve location v1 and DeviceLocation v1 subscriptions")
                print("           for application DefaultApplication (id=45956) under account lucifer25.'")

        if not poll:
            break

        print(f"\n[*] Polling again in 5 minutes... (Ctrl+C to stop)")
        try:
            time.sleep(300)
        except KeyboardInterrupt:
            print("\n[*] Stopped.")
            break


if __name__ == "__main__":
    main()
