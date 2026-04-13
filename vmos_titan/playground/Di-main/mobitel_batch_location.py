#!/usr/bin/env python3
"""Mobitel batch location via mlocator.mobitel.lk (official endpoint).
Note: mlocator.mobitel.lk currently returns 503 (backend down).
Credentials loaded from config.json if present.
"""
import requests
import base64
import sys
import json
import os

API_URL = "https://mlocator.mobitel.lk/api/v3/track"

_config_path = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(_config_path) as _f:
        _cfg = json.load(_f)
    USERNAME = _cfg.get("mobitel_username", "")
    PASSWORD = _cfg.get("mobitel_password", "")
    SESSION_TOKEN = _cfg.get("mobitel_session_token", "")
except Exception:
    USERNAME = ""
    PASSWORD = ""
    SESSION_TOKEN = ""


def batch_track(msisdn_list):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode(),
        "Content-Type": "application/json",
    }
    if SESSION_TOKEN:
        headers["X-Session-Token"] = SESSION_TOKEN
    payload = {"subscriber_list": msisdn_list, "tracking_mode": "realtime", "interval": 30}
    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code == 503:
            print("[!] Mobitel mLocator backend is DOWN (503). Service temporarily unavailable.")
            return None
        if resp.status_code == 200:
            print("[+] Batch location results:")
            print(resp.text)
            return resp.json()
        print(f"[!] Error {resp.status_code}: {resp.text}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"[!] Connection failed: {e}")
        return None
    except requests.exceptions.Timeout:
        print("[!] Timeout.")
        return None


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["94773123456", "94771234567"]
    batch_track(targets)