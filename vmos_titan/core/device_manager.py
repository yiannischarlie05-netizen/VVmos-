"""
Titan V13.0 — Device Manager (VMOS Cloud-Only Backend)
DEPRECATED: Cuttlefish/KVM support removed. Use VMOS Cloud API directly.
"""

import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .adb_utils import adb_shell

logger = logging.getLogger("titan.device-manager")

TITAN_DATA = Path(os.environ.get("TITAN_DATA", "/opt/titan/data"))
DEVICES_DIR = TITAN_DATA / "devices"


# ═══════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class CreateDeviceRequest:
    """DEPRECATED: Use VMOS Cloud API directly."""
    model: str = "samsung_s25_ultra"
    country: str = "US"
    carrier: str = "tmobile_us"
    phone_number: str = ""
    android_version: str = "14"


@dataclass
class DeviceInstance:
    """DEPRECATED: VMOS device representation."""
    id: str = ""
    adb_target: str = "127.0.0.1:6520"
    config: Dict[str, Any] = field(default_factory=dict)
    state: str = "deprecated"
    created_at: str = ""
    error: str = "DEPRECATED: Use VMOS Cloud API"

    def to_dict(self) -> dict:
        return {"id": self.id, "adb_target": self.adb_target, "state": self.state}


# ═══════════════════════════════════════════════════════════════════════
# SHELL HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _run(cmd: str, timeout: int = 60, env: Dict[str, str] = None) -> Dict[str, Any]:
    try:
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, env=run_env)
        return {"ok": r.returncode == 0, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "timeout"}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e)}


def _adb(target: str, cmd: str, timeout: int = 15) -> Dict[str, Any]:
    return _run(f"adb -s {target} {cmd}", timeout=timeout)


def _adb_shell(target: str, cmd: str, timeout: int = 15) -> str:
    return adb_shell(target, cmd, timeout=timeout)


# ═══════════════════════════════════════════════════════════════════════
# DEVICE MANAGER (DEPRECATED STUB)
# ═══════════════════════════════════════════════════════════════════════

class DeviceManager:
    """DEPRECATED: Cuttlefish/KVM removed. Use VMOS Cloud API directly."""

    def __init__(self):
        DEVICES_DIR.mkdir(parents=True, exist_ok=True)
        self._devices: Dict[str, DeviceInstance] = {}
        logger.warning("DeviceManager is DEPRECATED - Use VMOS Cloud API directly")

    def get_device(self, device_id: str) -> Optional[DeviceInstance]:
        """Get device by ID (deprecated)."""
        return None

    def list_devices(self) -> List[DeviceInstance]:
        """List all devices (deprecated)."""
        return []

    async def create_device(self, req: CreateDeviceRequest) -> Optional[DeviceInstance]:
        """DEPRECATED: Use VMOS Cloud API to create devices."""
        raise NotImplementedError("Cuttlefish removed - Use VMOS Cloud API")

    async def destroy_device(self, device_id: str) -> bool:
        """DEPRECATED: Use VMOS Cloud API to destroy devices."""
        raise NotImplementedError("Cuttlefish removed - Use VMOS Cloud API")

    async def patch_device(self, device_id: str) -> bool:
        """DEPRECATED: Use VMOS Cloud API workflow."""
        raise NotImplementedError("Cuttlefish removed - Use VMOS Cloud API")

    async def factory_reset_device(self, device_id: str) -> Dict[str, Any]:
        """DEPRECATED: Factory reset not available."""
        raise NotImplementedError("Cuttlefish removed - Use VMOS Cloud API")

    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device info via ADB (still works for any ADB target)."""
        return None

    async def screenshot(self, device_id: str) -> Optional[bytes]:
        """DEPRECATED: Screenshot not available."""
        return None
