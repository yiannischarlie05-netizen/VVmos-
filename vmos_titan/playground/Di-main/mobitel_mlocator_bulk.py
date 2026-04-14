#!/usr/bin/env python3
"""Mobitel mLocator bulk location query.
Note: mlocator.mobitel.lk currently returns 503 (backend down).
Credentials loaded from config.json if present.
"""
import requests
import base64
import sys
import json
import os

API_URL = "https://mlocator.mobitel.lk/api/v3/track"

# Load credentials from config.json
_config_path = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(_config_path) as _f:
        _cfg = json.load(_f)
    USERNAME = _cfg.get("mobitel_username", "enterprise_admin_01")
    PASSWORD = _cfg.get("mobitel_password", "")
    SESSION_TOKEN = _cfg.get("mobitel_session_token", "")
except Exception:
    USERNAME = "enterprise_admin_01"
    PASSWORD = ""
    SESSION_TOKEN = ""


def track_bulk(msisdns):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode(),
        "Content-Type": "application/json",
    }
    if SESSION_TOKEN:
        headers["X-Session-Token"] = SESSION_TOKEN
    payload = {"subscriber_list": msisdns, "tracking_mode": "realtime", "interval": 30}
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=12)
        if r.status_code == 503:
            print("[!] Mobitel mLocator backend is DOWN (503). Service temporarily unavailable.")
            return None
        if r.status_code == 401:
            print("[!] Mobitel authentication failed (401). Credentials may need updating.")
            return None
        print(f"[+] {r.status_code}: {r.text}")
        return r.json() if r.text else None
    except requests.exceptions.ConnectionError as e:
        print(f"[!] Connection failed: {e}")
        return None
    except requests.exceptions.Timeout:
        print("[!] Request timed out.")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mobitel_mlocator_bulk.py 94771234567 94771234568 ...")
        sys.exit(1)
    track_bulk(sys.argv[1:])