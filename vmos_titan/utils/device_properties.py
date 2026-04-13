"""
VMOS Cloud Device Properties Reference & Injection Utilities
=============================================================
Complete property namespace reference from API catalog + helper functions
for generating sensor data files, boot time offsets, DRM spoofing, etc.

Usage:
    from vmos_titan.utils.device_properties import (
        generate_sensor_data, PROPERTY_CATALOG, inject_properties
    )
"""

from __future__ import annotations

import math
import random
import time
from typing import Any


# ═══════════════════════════════════════════════════════════════════════
# PROPERTY CATALOG — All known persist.sys.cloud.* and ro.sys.cloud.* props
# ═══════════════════════════════════════════════════════════════════════

PROPERTY_CATALOG = {
    # --- Hardware & OS Identity (ro.*) ---
    "identity": {
        "ro.product.model": "Device model name",
        "ro.product.brand": "Device brand",
        "ro.product.name": "Product name",
        "ro.product.device": "Device code name",
        "ro.product.manufacturer": "Manufacturer name",
        "ro.product.board": "Board/SoC name",
        "ro.hardware": "Hardware architecture",
        "ro.build.fingerprint": "Build fingerprint (full)",
        "ro.odm.build.fingerprint": "ODM partition fingerprint",
        "ro.product.build.fingerprint": "Product partition fingerprint",
        "ro.system.build.fingerprint": "System partition fingerprint",
        "ro.system_ext.build.fingerprint": "System ext fingerprint",
        "ro.vendor.build.fingerprint": "Vendor partition fingerprint",
        "ro.build.version.incremental": "Build incremental version",
        "ro.build.flavor": "Build flavor",
    },
    # --- Unique Identifiers ---
    "identifiers": {
        "ro.sys.cloud.android_id": "Android ID (advertising)",
        "persist.sys.cloud.imeinum": "IMEI number",
        "persist.sys.cloud.iccidnum": "SIM ICCID",
        "persist.sys.cloud.imsinum": "IMSI number",
        "persist.sys.cloud.drm.id": "Widevine DRM deviceUniqueId",
        "persist.sys.cloud.drm.puid": "Widevine provisioningUniqueId",
    },
    # --- GPU/Graphics ---
    "gpu": {
        "persist.sys.cloud.gpu.gl_vendor": "OpenGL vendor string",
        "persist.sys.cloud.gpu.gl_renderer": "OpenGL renderer string",
        "persist.sys.cloud.gpu.gl_version": "OpenGL ES version string",
    },
    # --- Network ---
    "network": {
        "persist.sys.cloud.wifi.ssid": "Wi-Fi SSID name",
        "persist.sys.cloud.wifi.mac": "Wi-Fi MAC address",
        "persist.sys.cloud.wifi.ip": "Wi-Fi assigned IP",
        "persist.sys.cloud.wifi.gateway": "Wi-Fi gateway",
        "persist.sys.cloud.wifi.dns1": "Primary DNS",
        "persist.sys.cloud.cellinfo": "Cell tower hex (type,mcc,mnc,tac,cellid,narfcn,pci)",
        "persist.sys.cloud.mobileinfo": "MCC/MNC",
        "persist.sys.cloud.phonenum": "Phone number (intl format)",
        "ro.sys.cloud.proxy.mode": "proxy or vpn",
        "ro.sys.cloud.proxy.type": "socks5 or http-relay",
        "ro.sys.cloud.proxy.data": "IP|port|user|pass|enable",
        "ro.sys.cloud.proxy.byPassPackageName1": "Bypass rule: package name",
        "ro.sys.cloud.proxy.byPassIpName1": "Bypass rule: IP",
        "ro.sys.cloud.proxy.byByPassDomain1": "Bypass rule: domain",
        "ro.boot.redroid_net_ndns": "Number of DNS servers",
        "ro.boot.redroid_net_dns1": "Primary DNS server",
        "ro.boot.redroid_net_dns2": "Secondary DNS server",
    },
    # --- GPS ---
    "gps": {
        "persist.sys.cloud.gps.lat": "Latitude",
        "persist.sys.cloud.gps.lon": "Longitude",
        "persist.sys.cloud.gps.speed": "Speed (m/s)",
        "persist.sys.cloud.gps.altitude": "Altitude (m)",
        "persist.sys.cloud.gps.bearing": "Bearing (degrees)",
    },
    # --- Battery ---
    "battery": {
        "persist.sys.cloud.battery.capacity": "Battery capacity (mAh)",
        "persist.sys.cloud.battery.level": "Initial charge level (%)",
    },
    # --- Environment ---
    "environment": {
        "persist.sys.timezone": "System timezone (e.g. America/New_York)",
        "persist.sys.locale": "Locale (e.g. en-US)",
        "persist.sys.cloud.pm.install_source": "App install source (com.android.vending)",
        "persist.sys.cloud.boottime.offset": "Boot time offset (seconds, for backdating)",
        "ro.sys.cloud.boot_id": "Kernel random boot ID",
        "ro.sys.cloud.rand_pics": "Number of gallery images at boot",
    },
    # --- Sensor ---
    "sensor": {
        "persist.sys.cloud.sensor.tpl_dp": "Path to sensor data file on device",
    },
}

# ═══════════════════════════════════════════════════════════════════════
# SENSOR TYPES — Supported sensor simulation types
# ═══════════════════════════════════════════════════════════════════════

SENSOR_TYPES = {
    # Motion
    "accelerometer": {"unit": "m/s²", "format": "x:y:z"},
    "gyroscope": {"unit": "rad/s", "format": "x:y:z"},
    "linear-acceleration": {"unit": "m/s²", "format": "x:y:z"},
    "gravity": {"unit": "m/s²", "format": "x:y:z"},
    "rotation-vector": {"unit": "quaternion", "format": "x:y:z:w"},
    "game-rotation-vector": {"unit": "quaternion", "format": "x:y:z:w"},
    # Environment
    "magnetic-field": {"unit": "µT", "format": "x:y:z"},
    "proximity": {"unit": "cm", "format": "value"},
    "light": {"unit": "lux", "format": "value"},
    "pressure": {"unit": "hPa", "format": "value"},
    "temperature": {"unit": "℃", "format": "value"},
    "humidity": {"unit": "%", "format": "value"},
    # Biometrics
    "step-counter": {"unit": "steps", "format": "value"},
    "step-detector": {"unit": "event", "format": "1"},
    "heart-rate": {"unit": "BPM", "format": "value"},
    # Foldable
    "hinge-angle0": {"unit": "degrees", "format": "value"},
    "hinge-angle1": {"unit": "degrees", "format": "value"},
    "hinge-angle2": {"unit": "degrees", "format": "value"},
}


# ═══════════════════════════════════════════════════════════════════════
# SENSOR DATA GENERATION
# ═══════════════════════════════════════════════════════════════════════

def generate_sensor_data(
    duration_sec: int = 300,
    delay_ms: int = 50,
    include_accelerometer: bool = True,
    include_gyroscope: bool = True,
    include_light: bool = True,
    include_proximity: bool = False,
    include_steps: bool = False,
    motion_profile: str = "idle",  # idle, walking, driving
) -> str:
    """Generate realistic sensor data file content for VMOS Cloud injection.
    
    Args:
        duration_sec: Duration of sensor data in seconds
        delay_ms: Delay between readings in milliseconds (50ms = 20Hz)
        include_accelerometer: Include accelerometer readings
        include_gyroscope: Include gyroscope readings  
        include_light: Include ambient light readings
        include_proximity: Include proximity sensor
        include_steps: Include step counter
        motion_profile: "idle" (phone on table), "walking", "driving"
        
    Returns:
        UTF-8 sensor data file content ready for device injection
    """
    lines = []
    steps_total = 0
    num_readings = (duration_sec * 1000) // delay_ms
    
    for i in range(num_readings):
        t = i * delay_ms / 1000.0  # time in seconds
        
        if include_accelerometer:
            if motion_profile == "idle":
                ax = random.gauss(0.01, 0.005)
                ay = random.gauss(0.02, 0.005)
                az = random.gauss(9.81, 0.01)
            elif motion_profile == "walking":
                phase = t * 1.8 * 2 * math.pi  # ~1.8 Hz step frequency
                ax = random.gauss(0.0, 0.3) + 0.5 * math.sin(phase)
                ay = random.gauss(0.0, 0.2) + 0.3 * math.cos(phase * 0.5)
                az = 9.81 + 1.2 * abs(math.sin(phase)) + random.gauss(0, 0.1)
            else:  # driving
                ax = random.gauss(0.0, 0.15) + 0.1 * math.sin(t * 0.3)
                ay = random.gauss(0.0, 0.1)
                az = 9.81 + random.gauss(0, 0.05)
            lines.append(f"accelerometer:{ax:.4f}:{ay:.4f}:{az:.4f}")
        
        if include_gyroscope:
            if motion_profile == "idle":
                gx = random.gauss(0.001, 0.0005)
                gy = random.gauss(0.002, 0.0005)
                gz = random.gauss(0.001, 0.0005)
            elif motion_profile == "walking":
                phase = t * 1.8 * 2 * math.pi
                gx = random.gauss(0.0, 0.05) + 0.1 * math.sin(phase)
                gy = random.gauss(0.0, 0.03)
                gz = random.gauss(0.0, 0.02)
            else:  # driving
                gx = random.gauss(0.0, 0.01)
                gy = random.gauss(0.0, 0.01) + 0.02 * math.sin(t * 0.1)
                gz = random.gauss(0.0, 0.005)
            lines.append(f"gyroscope:{gx:.6f}:{gy:.6f}:{gz:.6f}")
        
        if include_light:
            # Simulate indoor lighting with occasional changes
            base_lux = 350 + 50 * math.sin(t * 0.01)
            lux = max(0, base_lux + random.gauss(0, 10))
            if random.random() < 0.001:
                lux = random.choice([50, 200, 800, 10000])  # room change
            lines.append(f"light:{lux:.1f}")
        
        if include_proximity:
            prox = 5.0 if random.random() > 0.02 else 0.0  # far most of time
            lines.append(f"proximity:{prox:.1f}")
        
        if include_steps and motion_profile == "walking":
            if random.random() < (delay_ms / 555.0):  # ~1.8 steps/sec
                steps_total += 1
                lines.append(f"step-counter:{steps_total}")
                lines.append("step-detector:1")
        
        lines.append(f"delay:{delay_ms}")
    
    return "\n".join(lines) + "\n"


def generate_boot_time_offset(days_ago: int = 90) -> int:
    """Generate boot time offset in seconds for device aging.
    
    Args:
        days_ago: How many days ago the device should appear to have booted
        
    Returns:
        Offset in seconds (negative to backdate)
    """
    base_offset = days_ago * 86400
    jitter = random.randint(-3600, 3600)  # ±1 hour jitter
    return base_offset + jitter


def build_aging_properties(days_ago: int = 90, gallery_pics: int = 250) -> dict[str, str]:
    """Build property dict for device aging (boottime offset + gallery pics).
    
    Args:
        days_ago: How old the device should appear  
        gallery_pics: Number of random gallery images to generate at boot
        
    Returns:
        Dict of properties to set via updatePadProperties
    """
    return {
        "persist.sys.cloud.boottime.offset": str(generate_boot_time_offset(days_ago)),
        "ro.sys.cloud.rand_pics": str(gallery_pics),
        "persist.sys.cloud.pm.install_source": "com.android.vending",
    }


def build_gpu_properties(brand: str = "samsung") -> dict[str, str]:
    """Build GPU/OpenGL properties matching a real device brand.
    
    Args:
        brand: Device brand (samsung, google, oneplus, xiaomi, oppo)
    """
    presets = {
        "samsung": {
            "persist.sys.cloud.gpu.gl_vendor": "Qualcomm",
            "persist.sys.cloud.gpu.gl_renderer": "Adreno (TM) 750",
            "persist.sys.cloud.gpu.gl_version": "OpenGL ES 3.2 V@0701.0 (GIT@3f2a37e81a, I70df4a8bd0, 1700112425) (Date:11/16/23)",
        },
        "google": {
            "persist.sys.cloud.gpu.gl_vendor": "ARM",
            "persist.sys.cloud.gpu.gl_renderer": "Mali-G715 Immortalis MC10",
            "persist.sys.cloud.gpu.gl_version": "OpenGL ES 3.2 v1.r44p0-01eac0.09a1ae7e14b3cb9bc tried2fe2",
        },
        "oneplus": {
            "persist.sys.cloud.gpu.gl_vendor": "Qualcomm",
            "persist.sys.cloud.gpu.gl_renderer": "Adreno (TM) 750",
            "persist.sys.cloud.gpu.gl_version": "OpenGL ES 3.2 V@0701.0",
        },
        "xiaomi": {
            "persist.sys.cloud.gpu.gl_vendor": "Qualcomm",
            "persist.sys.cloud.gpu.gl_renderer": "Adreno (TM) 740",
            "persist.sys.cloud.gpu.gl_version": "OpenGL ES 3.2 V@0615.0",
        },
        "oppo": {
            "persist.sys.cloud.gpu.gl_vendor": "Qualcomm",
            "persist.sys.cloud.gpu.gl_renderer": "Adreno (TM) 730",
            "persist.sys.cloud.gpu.gl_version": "OpenGL ES 3.2 V@0530.0",
        },
    }
    return presets.get(brand.lower(), presets["samsung"])


def build_battery_properties(capacity_mah: int = 5000, level_pct: int = 72) -> dict[str, str]:
    """Build battery emulation properties."""
    return {
        "persist.sys.cloud.battery.capacity": str(capacity_mah),
        "persist.sys.cloud.battery.level": str(level_pct),
    }


def build_drm_properties() -> dict[str, str]:
    """Build Widevine DRM spoofing properties with random UUIDs."""
    import uuid
    return {
        "persist.sys.cloud.drm.id": str(uuid.uuid4()),
        "persist.sys.cloud.drm.puid": str(uuid.uuid4()),
    }
