"""
Device API Module — Device lifecycle and control operations
Covers: restart, reset, properties, ADB, screenshot, GPS, country, switchRoot
"""

from typing import Any, Dict, List, Optional
from .base import APIModule


class DeviceAPI(APIModule):
    """Device lifecycle and control operations."""
    
    def get_module_name(self) -> str:
        return "device"
    
    # ==================== Device Control ====================
    
    async def restart(self, pad_code: str) -> Dict[str, Any]:
        """
        Restart device (warm reboot).
        
        Requires: VMOS_ALLOW_RESTART=true
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response dict
        
        Raises:
            GuardViolationError if VMOS_ALLOW_RESTART not set
            ForbiddenOperationError if restarts are blocked
        """
        self._check_guard("restart")
        
        return await self._call(
            "POST",
            "/api/pad/restart",
            {"pad_code": pad_code},
        )
    
    async def reset(self, pad_code: str) -> Dict[str, Any]:
        """
        Reset device (full factory reset).
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/reset",
            {"pad_code": pad_code},
            timeout_sec=60.0,  # Reset may take longer
        )
    
    async def switch_root(self, pad_code: str, enable: bool) -> Dict[str, Any]:
        """
        Enable or disable root access on device.
        
        Args:
            pad_code: Device pad code
            enable: True to enable root, False to disable
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/switchRoot",
            {"pad_code": pad_code, "enable": enable},
        )
    
    # ==================== Properties ====================
    
    async def get_properties(self, pad_code: str) -> Dict[str, Any]:
        """
        Get device properties (ro.* system properties).
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with properties dictionary
        """
        return await self._call(
            "POST",
            "/api/pad/getPadProperty",
            {"pad_code": pad_code},
        )
    
    async def set_property(self, pad_code: str, key: str, value: str) -> Dict[str, Any]:
        """
        Set a single device property.
        
        Args:
            pad_code: Device pad code
            key: Property key (e.g., "ro.build.fingerprint")
            value: Property value
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/updatePadProperties",
            {"pad_code": pad_code, "properties": {key: value}},
        )
    
    async def set_properties_batch(
        self,
        pad_code: str,
        properties: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Set multiple device properties at once (safe, no restart).
        
        Args:
            pad_code: Device pad code
            properties: Dictionary of key-value pairs
        
        Returns:
            API response dict
        """
        if len(properties) > self.config.max_property_batch_size:
            from vmos_titan.core.exceptions import ParameterError
            raise ParameterError(
                message=f"Too many properties ({len(properties)} > {self.config.max_property_batch_size})",
                parameter="properties",
            )
        
        return await self._call(
            "POST",
            "/api/pad/updatePadProperties",
            {"pad_code": pad_code, "properties": properties},
        )
    
    # ==================== Screenshots & Interaction ====================
    
    async def screenshot(self, pad_code: str) -> Dict[str, Any]:
        """
        Capture device screenshot.
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with image data (base64 or URL)
        """
        return await self._call(
            "POST",
            "/api/pad/screenshot",
            {"pad_code": pad_code},
            timeout_sec=10.0,
        )
    
    async def preview(self, pad_code: str) -> Dict[str, Any]:
        """
        Get device preview (lightweight screenshot for monitoring).
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with preview image
        """
        return await self._call(
            "POST",
            "/api/pad/preview",
            {"pad_code": pad_code},
            timeout_sec=5.0,
        )
    
    # ==================== ADB Shell ====================
    
    async def adb_shell(self, pad_code: str, command: str) -> Dict[str, Any]:
        """
        Execute ADB shell command on device.
        
        Args:
            pad_code: Device pad code
            command: Shell command to execute
        
        Returns:
            API response with command output
        
        Raises:
            ParameterError if command too long
        """
        if len(command) > self.config.max_adb_command_length:
            from vmos_titan.core.exceptions import ParameterError
            raise ParameterError(
                message=f"Command too long ({len(command)} > {self.config.max_adb_command_length})",
                parameter="command",
            )
        
        return await self._call(
            "POST",
            "/api/pad/adbCmd",
            {"pad_code": pad_code, "command": command},
            timeout_sec=15.0,
        )
    
    # ==================== Location & Regional ====================
    
    async def set_gps(
        self,
        pad_code: str,
        latitude: float,
        longitude: float,
        accuracy: float = 10.0,
        altitude: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Set device GPS location.
        
        Args:
            pad_code: Device pad code
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            accuracy: GPS accuracy in meters (default 10)
            altitude: Altitude in meters (default 0)
        
        Returns:
            API response dict
        
        Raises:
            ParameterError if coordinates out of range
        """
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            from vmos_titan.core.exceptions import ParameterError
            raise ParameterError(
                message=f"Invalid coordinates: lat={latitude}, lng={longitude}",
                parameter="coordinates",
            )
        
        return await self._call(
            "POST",
            "/api/pad/gpsLocation",
            {
                "pad_code": pad_code,
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": accuracy,
                "altitude": altitude,
            },
        )
    
    async def set_country(self, pad_code: str, country_code: str) -> Dict[str, Any]:
        """
        Set device country and region settings.
        
        Args:
            pad_code: Device pad code
            country_code: ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "JP")
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/setCountry",
            {"pad_code": pad_code, "country_code": country_code},
        )
    
    async def set_timezone(self, pad_code: str, timezone: str) -> Dict[str, Any]:
        """
        Set device timezone.
        
        Args:
            pad_code: Device pad code
            timezone: Timezone identifier (e.g., "America/New_York", "Europe/London")
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/setTimezone",
            {"pad_code": pad_code, "timezone": timezone},
        )
    
    async def set_language(self, pad_code: str, language: str) -> Dict[str, Any]:
        """
        Set device language.
        
        Args:
            pad_code: Device pad code
            language: Language code (e.g., "en", "zh", "ja")
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/setLanguage",
            {"pad_code": pad_code, "language": language},
        )
    
    # ==================== Status & Info ====================
    
    async def get_status(self, pad_code: str) -> Dict[str, Any]:
        """
        Get device status.
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with device status
        """
        return await self._call(
            "POST",
            "/api/pad/getStatus",
            {"pad_code": pad_code},
            timeout_sec=5.0,
        )
    
    async def get_info(self, pad_code: str) -> Dict[str, Any]:
        """
        Get device information (model, version, etc).
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with device info
        """
        return await self._call(
            "POST",
            "/api/pad/getPadInfo",
            {"pad_code": pad_code},
        )
