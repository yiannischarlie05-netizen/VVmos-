#!/usr/bin/env python3
"""
Intel Store — Persistent in-memory + JSON file store for all collected intelligence.
Keeps per-target records. Auto-saves to disk every write.
"""

import os
import json
import time
import threading
from typing import Dict, Optional, Any

STORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intel_store.json")

_lock = threading.Lock()
_store: Dict[str, dict] = {}


def _load():
    global _store
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r") as f:
                _store = json.load(f)
        except Exception:
            _store = {}


def _save():
    try:
        with open(STORE_FILE, "w") as f:
            json.dump(_store, f, indent=2, default=str)
    except Exception:
        pass


def record(target_id: str, category: str, data: dict):
    """Record intelligence under a target. Categories: gps, ip_geo, device, phone_osint, hlr, tier1"""
    with _lock:
        if target_id not in _store:
            _store[target_id] = {"created": time.time(), "intel": {}}
        _store[target_id]["intel"][category] = {
            "ts": time.time(),
            "data": data,
        }
        _store[target_id]["updated"] = time.time()
        _save()


def get(target_id: str) -> Optional[dict]:
    """Get all intel for a target."""
    with _lock:
        return _store.get(target_id)


def get_all() -> Dict[str, dict]:
    with _lock:
        return dict(_store)


def list_targets() -> list:
    with _lock:
        result = []
        for tid, v in _store.items():
            cats = list(v.get("intel", {}).keys())
            result.append({"target_id": tid, "categories": cats, "updated": v.get("updated")})
        return result


# Load on import
_load()
