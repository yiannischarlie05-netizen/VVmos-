"""
Network API Module — Network, connectivity, and location spoofing
Covers: smartIP, WiFi, proxy, checkIP, timezone, language
"""

from typing import Any, Dict, List, Optional
from .base import APIModule


class NetworkAPI(APIModule):
    """Network connectivity and location spoofing operations."""
    
    def get_module_name(self) -> str:
        return "network"
    
    # ==================== Smart IP / Location Spoofing ====================
    
    async def set_smart_ip(
        self,
        pad_code: str,
        country: str,
        city: Optional[str] = None,
        autonomous_system: Optional[str] = None,
        ip_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Set device smart IP (location spoofing).
        
        Args:
            pad_code: Device pad code
            country: Country code (e.g., "US", "GB", "JP")
            city: Optional city name
            autonomous_system: Optional AS name (e.g., "AWS", "Google Cloud")
            ip_provider: Optional IP provider name
        
        Returns:
            API response with smart IP configuration
        """
        return await self._call(
            "POST",
            "/api/pad/smartIp",
            {
                "pad_code": pad_code,
                "country": country,
                "city": city,
                "autonomous_system": autonomous_system,
                "ip_provider": ip_provider,
            },
        )
    
    async def get_smart_ip(self, pad_code: str) -> Dict[str, Any]:
        """
        Get current smart IP configuration.
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with smart IP config
        """
        return await self._call(
            "POST",
            "/api/pad/getSmartIp",
            {"pad_code": pad_code},
        )
    
    async def check_ip(self, pad_code: str) -> Dict[str, Any]:
        """
        Check device's public IP address.
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with IP information (IP, country, city, ISP, etc)
        """
        return await self._call(
            "POST",
            "/api/pad/checkIP",
            {"pad_code": pad_code},
        )
    
    # ==================== WiFi Configuration ====================
    
    async def set_wifi_list(
        self,
        pad_code: str,
        networks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Set WiFi network list (for WiFi scan spoofing).
        
        Each network dict should contain:
            - ssid: Network name
            - bssid: MAC address (optional)
            - signal_strength: dBm value (optional)
            - security: Security type (OPEN, WEP, WPA, WPA2, WPA3)
        
        Args:
            pad_code: Device pad code
            networks: List of WiFi network dicts
        
        Returns:
            API response dict
        
        Raises:
            ParameterError if too many networks
        """
        if len(networks) > 50:  # Reasonable limit
            from vmos_titan.core.exceptions import ParameterError
            raise ParameterError(
                message=f"Too many WiFi networks: {len(networks)} > 50",
                parameter="networks",
            )
        
        return await self._call(
            "POST",
            "/api/pad/setWifiList",
            {"pad_code": pad_code, "networks": networks},
        )
    
    async def get_wifi_list(self, pad_code: str) -> Dict[str, Any]:
        """
        Get current WiFi network list.
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with WiFi networks
        """
        return await self._call(
            "POST",
            "/api/pad/getWifiList",
            {"pad_code": pad_code},
        )
    
    # ==================== Proxy Configuration ====================
    
    async def set_proxy(
        self,
        pad_code: str,
        host: str,
        port: int,
        proxy_type: str = "http",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Set device HTTP/SOCKS proxy.
        
        Args:
            pad_code: Device pad code
            host: Proxy host
            port: Proxy port
            proxy_type: "http", "socks4", or "socks5"
            username: Optional proxy username
            password: Optional proxy password
        
        Returns:
            API response dict
        
        Raises:
            ParameterError if port invalid
        """
        if not 1 <= port <= 65535:
            from vmos_titan.core.exceptions import ParameterError
            raise ParameterError(
                message=f"Invalid port: {port}",
                parameter="port",
            )
        
        return await self._call(
            "POST",
            "/api/pad/setProxy",
            {
                "pad_code": pad_code,
                "host": host,
                "port": port,
                "proxy_type": proxy_type,
                "username": username,
                "password": password,
            },
        )
    
    async def clear_proxy(self, pad_code: str) -> Dict[str, Any]:
        """
        Clear device proxy settings.
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/clearProxy",
            {"pad_code": pad_code},
        )
    
    # ==================== Mobile Carrier Simulation ====================
    
    async def set_carrier(
        self,
        pad_code: str,
        carrier_name: str,
        operator_code: Optional[str] = None,
        country_code: str = "US",
    ) -> Dict[str, Any]:
        """
        Set device mobile carrier.
        
        Args:
            pad_code: Device pad code
            carrier_name: Carrier name (e.g., "Verizon", "AT&T", "T-Mobile", "O2")
            operator_code: Optional operator code (MCC-MNC)
            country_code: ISO country code
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/setCarrier",
            {
                "pad_code": pad_code,
                "carrier_name": carrier_name,
                "operator_code": operator_code,
                "country_code": country_code,
            },
        )
    
    async def set_imei(self, pad_code: str, imei: str) -> Dict[str, Any]:
        """
        Set device IMEI.
        
        Args:
            pad_code: Device pad code
            imei: Valid IMEI (15 digits, Luhn validated)
        
        Returns:
            API response dict
        
        Raises:
            ParameterError if IMEI invalid
        """
        # Basic validation: 15 digits
        if not (len(imei) == 15 and imei.isdigit()):
            from vmos_titan.core.exceptions import ParameterError
            raise ParameterError(
                message=f"Invalid IMEI: must be 15 digits, got {len(imei)}",
                parameter="imei",
            )
        
        return await self._call(
            "POST",
            "/api/pad/setImei",
            {"pad_code": pad_code, "imei": imei},
        )
    
    # ==================== DNS & Network Parameters ====================
    
    async def set_dns(
        self,
        pad_code: str,
        dns1: str,
        dns2: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Set device DNS servers.
        
        Args:
            pad_code: Device pad code
            dns1: Primary DNS server IP
            dns2: Optional secondary DNS server IP
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/setDns",
            {
                "pad_code": pad_code,
                "dns1": dns1,
                "dns2": dns2,
            },
        )
    
    async def set_mac_address(self, pad_code: str, mac: str) -> Dict[str, Any]:
        """
        Set device MAC address.
        
        Args:
            pad_code: Device pad code
            mac: MAC address (format: AA:BB:CC:DD:EE:FF)
        
        Returns:
            API response dict
        
        Raises:
            ParameterError if MAC address invalid
        """
        # Basic validation
        parts = mac.split(":")
        if len(parts) != 6 or not all(len(p) == 2 and all(c in "0123456789ABCDEFabcdef" for c in p) for p in parts):
            from vmos_titan.core.exceptions import ParameterError
            raise ParameterError(
                message=f"Invalid MAC address: {mac}",
                parameter="mac",
            )
        
        return await self._call(
            "POST",
            "/api/pad/setMacAddress",
            {"pad_code": pad_code, "mac": mac},
        )
    
    # ==================== Cellular & Connection Info ====================
    
    async def get_cellular_info(self, pad_code: str) -> Dict[str, Any]:
        """
        Get device cellular information.
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with cellular info (carrier, IMEI, signal strength, etc)
        """
        return await self._call(
            "POST",
            "/api/pad/getCellularInfo",
            {"pad_code": pad_code},
        )
    
    async def get_network_info(self, pad_code: str) -> Dict[str, Any]:
        """
        Get device network information.
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with network info (IP, gateway, DNS, WiFi, etc)
        """
        return await self._call(
            "POST",
            "/api/pad/getNetworkInfo",
            {"pad_code": pad_code},
        )
