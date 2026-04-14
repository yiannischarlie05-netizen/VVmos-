"""
VMOSProductionClient — Production-Ready VMOS Cloud Client Wrapper

Wraps VMOSCloudClient with:
- Proper response parsing (handles list vs dict responses)
- Fixed SIM modification with correct parameters
- Working humanized touch via raw touch simulation
- Retry logic and error handling
- Convenience methods for common operations

This addresses gaps identified during live testing:
1. sync_cmd returns list[dict] with errorMsg field
2. modify_sim_by_country requires additional params
3. simulateClick endpoint returns 404 - use raw touch instead
4. apmt is available for Xposed hooks

Usage:
    client = VMOSProductionClient(ak="...", sk="...")
    
    # Execute shell command with proper parsing
    output = await client.shell("getprop ro.build.fingerprint")
    
    # Modify SIM with full parameters
    await client.set_sim_full(pad_code, mcc="310", mnc="260", operator="T-Mobile")
    
    # Humanized touch using raw touch with timing
    await client.tap(pad_code, x=540, y=960)
"""

import asyncio
import logging
import os
import random
import time
from typing import Any, Dict, List, Optional, Tuple

# Import base client
import sys
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

logger = logging.getLogger(__name__)


class VMOSProductionClient:
    """Production-ready VMOS Cloud client with gap fixes."""
    
    def __init__(self, ak: str = None, sk: str = None):
        """Initialize with credentials."""
        self.ak = ak or os.environ.get("VMOS_CLOUD_AK", "")
        self.sk = sk or os.environ.get("VMOS_CLOUD_SK", "")
        self._client = VMOSCloudClient(ak=self.ak, sk=self.sk)
        self._default_pad = None
    
    # ═══════════════════════════════════════════════════════════════════════
    # RESPONSE PARSING HELPERS
    # ═══════════════════════════════════════════════════════════════════════
    
    @staticmethod
    def _extract_output(result: dict) -> Tuple[bool, str]:
        """
        Extract command output from API response.
        
        Handles both formats:
        - {"code": 200, "data": {"errorMsg": "output"}}
        - {"code": 200, "data": [{"errorMsg": "output", ...}]}
        
        Returns:
            (success, output_string)
        """
        if result.get("code") != 200:
            return False, result.get("msg", "API error")
        
        data = result.get("data")
        
        if isinstance(data, list) and data:
            # List response - extract from first item
            item = data[0]
            if isinstance(item, dict):
                output = item.get("errorMsg") or item.get("result", "")
                if output is None:
                    output = ""
                return True, str(output).strip()
            return True, str(item).strip()
        
        elif isinstance(data, dict):
            # Dict response
            output = data.get("errorMsg") or data.get("result", "")
            if output is None:
                output = ""
            return True, str(output).strip()
        
        elif isinstance(data, str):
            return True, data.strip()
        
        return True, str(data) if data else ""
    
    # ═══════════════════════════════════════════════════════════════════════
    # SHELL COMMAND EXECUTION
    # ═══════════════════════════════════════════════════════════════════════
    
    async def shell(self, pad_code: str, command: str, 
                    timeout: int = 30) -> Tuple[bool, str]:
        """
        Execute shell command with proper output parsing.
        
        Args:
            pad_code: Instance pad code
            command: Shell command to run
            timeout: Command timeout in seconds
            
        Returns:
            (success, output) tuple
        """
        result = await self._client.sync_cmd(pad_code, command, timeout_sec=timeout)
        return self._extract_output(result)
    
    async def shell_async(self, pad_codes: List[str], command: str) -> dict:
        """Execute async shell command on multiple instances."""
        return await self._client.async_adb_cmd(pad_codes, command)
    
    async def getprop(self, pad_code: str, prop: str) -> str:
        """Get a system property value."""
        success, output = await self.shell(pad_code, f"getprop {prop}", timeout=15)
        return output if success else ""
    
    async def setprop(self, pad_code: str, prop: str, value: str) -> bool:
        """Set a system property value."""
        success, _ = await self.shell(pad_code, f"setprop {prop} {value}", timeout=15)
        return success
    
    # ═══════════════════════════════════════════════════════════════════════
    # DEVICE IDENTITY
    # ═══════════════════════════════════════════════════════════════════════
    
    async def set_properties(self, pad_code: str, props: Dict[str, str]) -> bool:
        """
        Set multiple device properties.
        
        Uses modify_instance_properties (which works) instead of 
        modify_android_props (which requires different params).
        """
        result = await self._client.modify_instance_properties([pad_code], props)
        return result.get("code") == 200
    
    async def set_device_identity(self, pad_code: str, 
                                  brand: str = "samsung",
                                  model: str = "SM-S928U",
                                  fingerprint: str = None) -> bool:
        """Set complete device identity."""
        props = {
            "ro.product.brand": brand,
            "ro.product.manufacturer": brand.title(),
            "ro.product.model": model,
            "ro.build.type": "user",
            "ro.debuggable": "0",
            "ro.secure": "1",
            "ro.boot.verifiedbootstate": "green",
        }
        
        if fingerprint:
            props["ro.build.fingerprint"] = fingerprint
        
        return await self.set_properties(pad_code, props)
    
    # ═══════════════════════════════════════════════════════════════════════
    # SIM/TELEPHONY (FIXED)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def set_sim_full(self, pad_code: str,
                           mcc: str = "310",
                           mnc: str = "260",
                           operator: str = "T-Mobile",
                           country_iso: str = "us",
                           phone_number: str = None) -> bool:
        """
        Set full SIM configuration via setprop commands.
        
        The modify_sim_by_country API has parameter issues, so we use
        direct property setting instead.
        """
        props = [
            f"gsm.sim.state READY",
            f"gsm.sim.operator.numeric {mcc}{mnc}",
            f"gsm.sim.operator.alpha {operator}",
            f"gsm.sim.operator.iso-country {country_iso}",
            f"gsm.operator.numeric {mcc}{mnc}",
            f"gsm.operator.alpha {operator}",
            f"gsm.operator.iso-country {country_iso}",
            f"gsm.network.type LTE",
            f"gsm.nitz.time {int(time.time() * 1000)}",
        ]
        
        if phone_number:
            props.append(f"gsm.sim.operator.phonenumber {phone_number}")
        
        for prop in props:
            cmd = f"setprop {prop}"
            await self.shell(pad_code, cmd, timeout=10)
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # GPS/LOCATION
    # ═══════════════════════════════════════════════════════════════════════
    
    async def set_gps(self, pad_code: str, lat: float, lng: float,
                      altitude: float = 50.0, accuracy: float = 10.0) -> bool:
        """Set GPS coordinates."""
        result = await self._client.set_gps(
            [pad_code], lat=lat, lng=lng, altitude=altitude
        )
        return result.get("code") == 200
    
    async def set_location_la(self, pad_code: str) -> bool:
        """Shortcut: Set location to Los Angeles."""
        return await self.set_gps(pad_code, 34.0522, -118.2437)
    
    async def set_location_nyc(self, pad_code: str) -> bool:
        """Shortcut: Set location to New York City."""
        return await self.set_gps(pad_code, 40.7128, -74.0060)
    
    # ═══════════════════════════════════════════════════════════════════════
    # TOUCH SIMULATION (FIXED - uses raw touch with timing)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def tap(self, pad_code: str, x: int, y: int,
                  width: int = 1080, height: int = 2400,
                  humanize: bool = True) -> bool:
        """
        Perform a tap at coordinates.
        
        Uses raw simulate_touch with press/release timing to simulate
        human-like tap since simulateClick endpoint returns 404.
        """
        # Add slight position jitter for humanization
        if humanize:
            x += random.randint(-3, 3)
            y += random.randint(-3, 3)
        
        # Press
        positions = [{"x": x, "y": y, "actionType": 0}]  # 0 = pressed
        result = await self._client.simulate_touch([pad_code], width, height, positions)
        
        if result.get("code") != 200:
            return False
        
        # Hold for human-like duration (50-150ms)
        if humanize:
            await asyncio.sleep(random.uniform(0.05, 0.15))
        else:
            await asyncio.sleep(0.05)
        
        # Release
        positions = [{"x": x, "y": y, "actionType": 1}]  # 1 = lifted
        result = await self._client.simulate_touch([pad_code], width, height, positions)
        
        return result.get("code") == 200
    
    async def swipe(self, pad_code: str,
                    start_x: int, start_y: int,
                    end_x: int, end_y: int,
                    width: int = 1080, height: int = 2400,
                    duration_ms: int = 300,
                    humanize: bool = True) -> bool:
        """
        Perform a swipe gesture.
        
        Generates intermediate touch points with timing for smooth swipe.
        """
        # Add jitter for humanization
        if humanize:
            start_x += random.randint(-5, 5)
            start_y += random.randint(-5, 5)
            end_x += random.randint(-5, 5)
            end_y += random.randint(-5, 5)
        
        # Number of intermediate points
        steps = max(10, duration_ms // 20)
        step_delay = duration_ms / 1000 / steps
        
        # Start press
        positions = [{"x": start_x, "y": start_y, "actionType": 0}]
        result = await self._client.simulate_touch([pad_code], width, height, positions)
        if result.get("code") != 200:
            return False
        
        await asyncio.sleep(step_delay)
        
        # Intermediate moves
        for i in range(1, steps):
            progress = i / steps
            # Ease-out curve for natural deceleration
            eased = 1 - (1 - progress) ** 2
            
            x = int(start_x + (end_x - start_x) * eased)
            y = int(start_y + (end_y - start_y) * eased)
            
            positions = [{"x": x, "y": y, "actionType": 2}]  # 2 = touching/moving
            await self._client.simulate_touch([pad_code], width, height, positions)
            await asyncio.sleep(step_delay)
        
        # End release
        positions = [{"x": end_x, "y": end_y, "actionType": 1}]
        result = await self._client.simulate_touch([pad_code], width, height, positions)
        
        return result.get("code") == 200
    
    async def scroll_up(self, pad_code: str, amount: int = 800) -> bool:
        """Scroll up by swiping from bottom to top."""
        return await self.swipe(pad_code, 540, 1600, 540, 1600 - amount)
    
    async def scroll_down(self, pad_code: str, amount: int = 800) -> bool:
        """Scroll down by swiping from top to bottom."""
        return await self.swipe(pad_code, 540, 800, 540, 800 + amount)
    
    # ═══════════════════════════════════════════════════════════════════════
    # ROOT & ADVANCED CAPABILITIES
    # ═══════════════════════════════════════════════════════════════════════
    
    async def enable_root(self, pad_code: str, package: str = "com.android.shell") -> bool:
        """Enable root access for a package."""
        result = await self._client.switch_root(
            [pad_code], enable=True, root_type=1, package_name=package
        )
        return result.get("code") == 200
    
    async def disable_root(self, pad_code: str, package: str = "com.android.shell") -> bool:
        """Disable root access for a package."""
        result = await self._client.switch_root(
            [pad_code], enable=False, root_type=1, package_name=package
        )
        return result.get("code") == 200
    
    async def is_rooted(self, pad_code: str) -> bool:
        """Check if device has root access."""
        success, output = await self.shell(pad_code, "id")
        return "uid=0" in output or "root" in output
    
    async def has_magisk(self, pad_code: str) -> bool:
        """Check if Magisk is installed."""
        success, output = await self.shell(
            pad_code, "ls /data/adb/magisk/busybox 2>/dev/null && echo 'found'"
        )
        return "found" in output
    
    async def has_lsposed(self, pad_code: str) -> bool:
        """Check if LSPosed is installed."""
        success, output = await self.shell(
            pad_code, 
            "ls /data/adb/lspd 2>/dev/null || ls /data/adb/modules/zygisk_lsposed 2>/dev/null"
        )
        return success and output and "No such file" not in output
    
    async def has_apmt(self, pad_code: str) -> bool:
        """Check if apmt (VMOS patch tool) is available."""
        success, output = await self.shell(pad_code, "which apmt")
        return success and output and "not found" not in output
    
    # ═══════════════════════════════════════════════════════════════════════
    # FRIDA INJECTION
    # ═══════════════════════════════════════════════════════════════════════
    
    async def install_frida(self, pad_code: str, version: str = "16.2.1") -> bool:
        """
        Install Frida server on the device.
        
        Downloads and installs frida-server for ARM64.
        """
        frida_url = f"https://github.com/frida/frida/releases/download/{version}/frida-server-{version}-android-arm64.xz"
        
        commands = [
            f"cd /data/local/tmp",
            f"curl -L -o frida.xz '{frida_url}'",
            f"xz -d frida.xz",
            f"mv frida frida-server",
            f"chmod 755 frida-server",
        ]
        
        for cmd in commands:
            success, output = await self.shell(pad_code, cmd, timeout=60)
            if not success:
                logger.error(f"Frida install failed at: {cmd}")
                return False
        
        return True
    
    async def start_frida(self, pad_code: str) -> bool:
        """Start Frida server in background."""
        # Kill any existing
        await self.shell(pad_code, "pkill -f frida-server", timeout=10)
        await asyncio.sleep(1)
        
        # Start new instance
        success, _ = await self.shell(
            pad_code, 
            "nohup /data/local/tmp/frida-server -l 0.0.0.0:27042 &",
            timeout=10
        )
        
        # Verify
        await asyncio.sleep(2)
        success, output = await self.shell(pad_code, "pgrep -f frida-server")
        return bool(output)
    
    async def stop_frida(self, pad_code: str) -> bool:
        """Stop Frida server."""
        success, _ = await self.shell(pad_code, "pkill -f frida-server")
        return success
    
    # ═══════════════════════════════════════════════════════════════════════
    # LSPOSED/XPOSED HOOKS VIA APMT
    # ═══════════════════════════════════════════════════════════════════════
    
    async def apmt_list_plugins(self, pad_code: str) -> List[str]:
        """List installed apmt plugins."""
        success, output = await self.shell(pad_code, "apmt list 2>/dev/null")
        if success and output:
            return [line.strip() for line in output.split('\n') if line.strip()]
        return []
    
    async def apmt_install_plugin(self, pad_code: str, 
                                  apk_path: str, 
                                  target_package: str) -> bool:
        """Install an apmt/Xposed plugin."""
        cmd = f"apmt install {apk_path} -t {target_package}"
        success, output = await self.shell(pad_code, cmd, timeout=30)
        return success and "success" in output.lower()
    
    async def apmt_remove_plugin(self, pad_code: str, plugin_name: str) -> bool:
        """Remove an apmt plugin."""
        cmd = f"apmt remove {plugin_name}"
        success, output = await self.shell(pad_code, cmd, timeout=15)
        return success
    
    # ═══════════════════════════════════════════════════════════════════════
    # INSTANCE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
    
    async def list_instances(self) -> List[Dict[str, Any]]:
        """List all cloud phone instances."""
        result = await self._client.cloud_phone_list(page=1, rows=100)
        if result.get("code") == 200:
            data = result.get("data", {})
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("rows", data.get("list", []))
        return []
    
    async def get_first_online_instance(self) -> Optional[str]:
        """Get the first online instance pad code."""
        instances = await self.list_instances()
        for inst in instances:
            if isinstance(inst, dict):
                status = inst.get("padStatus")
                if status in [1, 100, "1", "100", "online"]:
                    return inst.get("padCode")
        # Fallback to first instance
        if instances and isinstance(instances[0], dict):
            return instances[0].get("padCode")
        return None
    
    async def restart_instance(self, pad_code: str) -> bool:
        """Restart an instance."""
        result = await self._client.instance_restart([pad_code])
        return result.get("code") == 200
    
    async def reset_instance(self, pad_code: str) -> bool:
        """Factory reset an instance."""
        result = await self._client.instance_reset([pad_code])
        return result.get("code") == 200
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEALTH AUDIT
    # ═══════════════════════════════════════════════════════════════════════
    
    async def stealth_audit(self, pad_code: str) -> Dict[str, Any]:
        """
        Audit device stealth properties.
        
        Returns dict with pass/fail status for each check.
        """
        checks = {
            "ro.build.type": ("user", "Build type"),
            "ro.debuggable": ("0", "Debuggable"),
            "ro.secure": ("1", "Secure"),
            "ro.boot.verifiedbootstate": ("green", "Verified boot"),
            "ro.kernel.qemu": ("", "QEMU indicator"),
            "gsm.sim.state": ("READY", "SIM state"),
        }
        
        results = {}
        passed = 0
        total = len(checks)
        
        for prop, (expected, desc) in checks.items():
            value = await self.getprop(pad_code, prop)
            ok = (expected == "" and value == "") or (value == expected)
            
            results[prop] = {
                "value": value,
                "expected": expected,
                "passed": ok,
                "description": desc,
            }
            
            if ok:
                passed += 1
        
        return {
            "passed": passed,
            "total": total,
            "score": round(passed / total * 100),
            "checks": results,
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # FULL STEALTH SETUP
    # ═══════════════════════════════════════════════════════════════════════
    
    async def apply_stealth_patch(self, pad_code: str,
                                  preset: str = "samsung_s24",
                                  carrier: str = "tmobile_us",
                                  location: str = "la") -> Dict[str, Any]:
        """
        Apply full stealth patching.
        
        Combines property modification, SIM setup, GPS, and verification.
        """
        results = {"phases": [], "success": True}
        
        # Phase 1: Device identity
        try:
            if preset == "samsung_s24":
                ok = await self.set_device_identity(
                    pad_code, 
                    brand="samsung",
                    model="SM-S928U",
                    fingerprint="samsung/e1qsq/e1q:14/UP1A.231005.007/S928USQS2AXB1:user/release-keys"
                )
            elif preset == "pixel_8":
                ok = await self.set_device_identity(
                    pad_code,
                    brand="google",
                    model="Pixel 8",
                    fingerprint="google/shiba/shiba:14/AP2A.240805.005/12025142:user/release-keys"
                )
            else:
                ok = await self.set_device_identity(pad_code)
            
            results["phases"].append({"name": "device_identity", "success": ok})
            results["success"] &= ok
        except Exception as e:
            results["phases"].append({"name": "device_identity", "success": False, "error": str(e)})
            results["success"] = False
        
        # Phase 2: SIM configuration
        try:
            if carrier == "tmobile_us":
                ok = await self.set_sim_full(pad_code, "310", "260", "T-Mobile", "us")
            elif carrier == "att_us":
                ok = await self.set_sim_full(pad_code, "310", "410", "AT&T", "us")
            elif carrier == "verizon_us":
                ok = await self.set_sim_full(pad_code, "311", "480", "Verizon", "us")
            else:
                ok = await self.set_sim_full(pad_code)
            
            results["phases"].append({"name": "sim_config", "success": ok})
            results["success"] &= ok
        except Exception as e:
            results["phases"].append({"name": "sim_config", "success": False, "error": str(e)})
        
        # Phase 3: GPS location
        try:
            if location == "la":
                ok = await self.set_location_la(pad_code)
            elif location == "nyc":
                ok = await self.set_location_nyc(pad_code)
            else:
                ok = await self.set_gps(pad_code, 34.0522, -118.2437)
            
            results["phases"].append({"name": "gps_location", "success": ok})
            results["success"] &= ok
        except Exception as e:
            results["phases"].append({"name": "gps_location", "success": False, "error": str(e)})
        
        # Phase 4: Stealth audit
        try:
            audit = await self.stealth_audit(pad_code)
            results["audit"] = audit
            results["phases"].append({"name": "stealth_audit", "success": audit["passed"] >= 4})
        except Exception as e:
            results["phases"].append({"name": "stealth_audit", "success": False, "error": str(e)})
        
        return results


# Convenience function
async def get_production_client() -> VMOSProductionClient:
    """Get a production client with default credentials."""
    return VMOSProductionClient()
