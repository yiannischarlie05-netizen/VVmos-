"""
Titan V13.0 — Devices Router (VMOS Cloud)
/api/devices/* — Device management via VMOS Cloud API
"""

import asyncio
import io
import logging
import subprocess
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger("titan.devices")

import sys
import os
# Ensure workspace core/ is in path before system /opt/titan/core/
workspace_core = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../core')
if workspace_core not in sys.path:
    sys.path.insert(0, workspace_core)

from device_manager import DeviceManager, CreateDeviceRequest
from anomaly_patcher import AnomalyPatcher
from device_presets import COUNTRY_DEFAULTS

router = APIRouter(prefix="/api/devices", tags=["devices"])

# Shared device manager singleton — set by main app
dm: DeviceManager = None


def init(device_manager: DeviceManager):
    global dm
    dm = device_manager


class CreateDeviceBody(BaseModel):
    model: str = "samsung_s25_ultra"
    country: str = "US"
    carrier: str = "tmobile_us"
    location: str = "nyc"
    phone_number: str = ""
    android_version: str = "14"
    auto_patch: bool = False


class InputBody(BaseModel):
    type: str = "tap"
    x: float = 0.0
    y: float = 0.0
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    duration: int = 300
    keycode: str = ""
    text: str = ""


@router.get("")
async def list_devices():
    devices = dm.list_devices()
    return {"devices": [d.to_dict() for d in devices]}


# ═══════════════════════════════════════════════════════════════════════
# VMOS CLOUD DEVICES
# ═══════════════════════════════════════════════════════════════════════

@router.get("/vmos")
async def get_vmos_devices():
    """Get VMOS Cloud devices."""
    return {"status": "use_vmos_cloud_api", "message": "Use /api/vmos/* endpoints"}


@router.post("/{device_id}/reconnect")
async def reconnect_device(device_id: str):
    """Verify ADB connectivity for a device."""
    from device_manager import _run
    dev = dm.get_device(device_id)
    if not dev:
        raise HTTPException(404, f"Device {device_id} not found")

    # Ensure ADB is connected
    _run(f"adb connect {dev.adb_target}", timeout=5)
    r = _run(f"adb -s {dev.adb_target} shell echo ok", timeout=8)
    if r.get("ok") and "ok" in r.get("stdout", ""):
        return {"status": "connected", "device_id": device_id}
    else:
        raise HTTPException(503, f"Cannot connect to {dev.adb_target}")


@router.post("/factory-reset")
async def factory_reset():
    """DEPRECATED: Factory reset not available with VMOS Cloud."""
    raise HTTPException(410, "Factory reset removed - Use VMOS Cloud API to recreate devices")


class UpdateDeviceConfigBody(BaseModel):
    model: str = ""
    country: str = ""
    carrier: str = ""
    location: str = ""


@router.post("/config")
async def update_config(body: UpdateDeviceConfigBody):
    """DEPRECATED: Device config managed via VMOS Cloud API."""
    raise HTTPException(410, "Device configuration removed - Use VMOS Cloud API")


@router.get("/{device_id}")
async def get_device(device_id: str):
    dev = dm.get_device(device_id)
    if not dev:
        raise HTTPException(404, "Device not found")
    return dev.to_dict()


@router.get("/{device_id}/info")
async def get_device_info(device_id: str):
    info = dm.get_device_info(device_id)
    if not info:
        raise HTTPException(404, "Device not found or not ready")
    return info


@router.post("")
async def create_device(body: CreateDeviceBody):
    """DEPRECATED: Use VMOS Cloud API to create devices."""
    raise HTTPException(410, "Device creation removed - Use POST /api/vmos/cloud/instances")


@router.delete("/{device_id}")
async def destroy_device(device_id: str):
    """DEPRECATED: Use VMOS Cloud API to destroy devices."""
    raise HTTPException(410, "Device destruction removed - Use DELETE /api/vmos/cloud/instances/{id}")


@router.post("/{device_id}/restart")
async def restart_device(device_id: str):
    """DEPRECATED: Device restart managed via VMOS Cloud API."""
    raise HTTPException(410, "Device restart removed - Use VMOS Cloud API")


@router.get("/{device_id}/screenshot")
async def device_screenshot(device_id: str):
    """DEPRECATED: Screenshot via direct ADB to VMOS device."""
    raise HTTPException(410, "Screenshot endpoint removed - Use ADB directly")


@router.post("/{device_id}/input")
async def device_input(device_id: str, body: InputBody):
    """Send touch/key input to device via ADB."""
    dev = dm.get_device(device_id)
    if not dev:
        raise HTTPException(404, "Device not found")

    from device_manager import _adb
    t = dev.adb_target

    # Get screen resolution for coordinate mapping
    info = _adb(t, 'shell "wm size"')
    width, height = 1080, 2400
    if info["ok"] and "x" in info["stdout"]:
        try:
            parts = info["stdout"].split(":")[-1].strip().split("x")
            width, height = int(parts[0]), int(parts[1])
        except Exception as e:
            logger.debug(f"Screen resolution parse failed: {e}")

    if body.type == "tap":
        px, py = int(body.x * width), int(body.y * height)
        try:
            subprocess.run(
                ["adb", "-s", t, "shell", "input", "tap", str(px), str(py)],
                capture_output=True, timeout=10
            )
            return {"ok": True, "action": "tap", "px": px, "py": py}
        except Exception as e:
            logger.error(f"Tap failed: {e}")
            return {"ok": False, "error": str(e)}

    elif body.type == "swipe":
        px1, py1 = int(body.x1 * width), int(body.y1 * height)
        px2, py2 = int(body.x2 * width), int(body.y2 * height)
        dur = max(100, min(body.duration, 2000))
        try:
            subprocess.run(
                ["adb", "-s", t, "shell", "input", "swipe", str(px1), str(py1), str(px2), str(py2), str(dur)],
                capture_output=True, timeout=10
            )
            return {"ok": True, "action": "swipe"}
        except Exception as e:
            logger.error(f"Swipe failed: {e}")
            return {"ok": False, "error": str(e)}

    elif body.type == "key":
        try:
            subprocess.run(
                ["adb", "-s", t, "shell", "input", "keyevent", body.keycode],
                capture_output=True, timeout=10
            )
            return {"ok": True, "action": "key", "keycode": body.keycode}
        except Exception as e:
            logger.error(f"Key event failed: {e}")
            return {"ok": False, "error": str(e)}

    elif body.type == "text":
        try:
            subprocess.run(
                ["adb", "-s", t, "shell", "input", "text", body.text],
                capture_output=True, timeout=10
            )
            return {"ok": True, "action": "text", "length": len(body.text)}
        except Exception as e:
            logger.error(f"Text input failed: {e}")
            return {"ok": False, "error": str(e)}

    return {"ok": False, "error": "unknown input type"}
