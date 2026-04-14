"""VMOS Cloud API - Static Proxy Module

Manages static residential proxy configurations for stable connection
patterns and location persistence.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from vmos_titan.api.base import APIModule


@dataclass
class StaticProxy:
    """Static proxy configuration"""
    proxy_id: str
    host: str
    port: int
    protocol: str
    location: str
    status: str
    created_at: datetime
    bandwidth_mbps: int


class ProxyStaticAPI(APIModule):
    """Static residential proxy management"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "proxy_static"

    async def list_proxies(
        self,
        protocol: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List static proxies
        
        Args:
            protocol: Filter by protocol ("http", "https", "socks5")
            location: Filter by location
            limit: Maximum results
            
        Returns:
            List of static proxies
        """
        data = {"limit": limit}
        if protocol:
            data["protocol"] = protocol
        if location:
            data["location"] = location

        return await self._call(
            "get",
            "/proxies/static",
            data=data,
        )

    async def get_proxy(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Get static proxy details
        
        Args:
            proxy_id: Proxy identifier
            
        Returns:
            Proxy configuration and credentials
        """
        return await self._call(
            "get",
            f"/proxies/static/{proxy_id}",
        )

    async def create_proxy(
        self,
        name: str,
        location: str,
        protocol: str = "https",
        bandwidth_mbps: int = 100,
    ) -> Dict[str, Any]:
        """Create static proxy
        
        Args:
            name: Proxy name
            location: Geographic location
            protocol: Proxy protocol
            bandwidth_mbps: Bandwidth allocation
            
        Returns:
            New proxy configuration
        """
        return await self._call(
            "post",
            "/proxies/static",
            data={
                "name": name,
                "location": location,
                "protocol": protocol,
                "bandwidth_mbps": bandwidth_mbps,
            },
        )

    async def delete_proxy(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Delete static proxy
        
        Args:
            proxy_id: Proxy to delete
            
        Returns:
            Deletion status
        """
        return await self._call(
            "delete",
            f"/proxies/static/{proxy_id}",
        )

    async def get_proxy_credentials(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Get proxy username and password
        
        Args:
            proxy_id: Proxy identifier
            
        Returns:
            Authentication credentials
        """
        return await self._call(
            "get",
            f"/proxies/static/{proxy_id}/credentials",
        )

    async def regenerate_credentials(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Regenerate proxy credentials
        
        Args:
            proxy_id: Proxy identifier
            
        Returns:
            New credentials
        """
        return await self._call(
            "post",
            f"/proxies/static/{proxy_id}/regenerate-credentials",
        )

    async def get_proxy_stats(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Get proxy usage statistics
        
        Args:
            proxy_id: Proxy identifier
            
        Returns:
            Usage and performance statistics
        """
        return await self._call(
            "get",
            f"/proxies/static/{proxy_id}/stats",
        )

    async def enable_proxy(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Enable static proxy
        
        Args:
            proxy_id: Proxy to enable
            
        Returns:
            Status update
        """
        return await self._call(
            "post",
            f"/proxies/static/{proxy_id}/enable",
        )

    async def disable_proxy(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Disable static proxy
        
        Args:
            proxy_id: Proxy to disable
            
        Returns:
            Status update
        """
        return await self._call(
            "post",
            f"/proxies/static/{proxy_id}/disable",
        )

    async def get_whitelist(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Get IP whitelist for proxy
        
        Args:
            proxy_id: Proxy identifier
            
        Returns:
            Whitelisted IPs
        """
        return await self._call(
            "get",
            f"/proxies/static/{proxy_id}/whitelist",
        )

    async def add_to_whitelist(
        self,
        proxy_id: str,
        ip_address: str,
    ) -> Dict[str, Any]:
        """Add IP to whitelist
        
        Args:
            proxy_id: Proxy identifier
            ip_address: IP to whitelist
            
        Returns:
            Update status
        """
        return await self._call(
            "post",
            f"/proxies/static/{proxy_id}/whitelist",
            data={"ip": ip_address},
        )

    async def remove_from_whitelist(
        self,
        proxy_id: str,
        ip_address: str,
    ) -> Dict[str, Any]:
        """Remove IP from whitelist
        
        Args:
            proxy_id: Proxy identifier
            ip_address: IP to remove
            
        Returns:
            Update status
        """
        return await self._call(
            "delete",
            f"/proxies/static/{proxy_id}/whitelist",
            data={"ip": ip_address},
        )

    async def update_bandwidth(
        self,
        proxy_id: str,
        bandwidth_mbps: int,
    ) -> Dict[str, Any]:
        """Update proxy bandwidth allocation
        
        Args:
            proxy_id: Proxy identifier
            bandwidth_mbps: New bandwidth limit
            
        Returns:
            Update status
        """
        return await self._call(
            "put",
            f"/proxies/static/{proxy_id}/bandwidth",
            data={"bandwidth_mbps": bandwidth_mbps},
        )

    async def get_available_locations(
        self,
    ) -> Dict[str, Any]:
        """Get available proxy locations
        
        Returns:
            List of location options with pricing
        """
        return await self._call(
            "get",
            "/proxies/static/locations",
        )

    async def test_proxy_connection(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Test proxy connectivity
        
        Args:
            proxy_id: Proxy to test
            
        Returns:
            Connection test result
        """
        return await self._call(
            "post",
            f"/proxies/static/{proxy_id}/test",
        )
