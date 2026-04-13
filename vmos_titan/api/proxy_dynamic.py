"""VMOS Cloud API - Dynamic Proxy Module

Manages dynamic proxy fleet operations for rotating IP addresses
and geo-location spoofing.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from vmos_titan.api.base import APIModule


@dataclass
class DynamicProxy:
    """Dynamic proxy configuration"""
    proxy_id: str
    status: str
    rotation_interval: int
    location: str
    ip_pool_size: int
    created_at: datetime


class ProxyDynamicAPI(APIModule):
    """Dynamic proxy fleet management"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "proxy_dynamic"

    async def list_proxies(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List dynamic proxies
        
        Args:
            status: Filter by status ("active", "inactive", "rotating")
            limit: Maximum results
            
        Returns:
            List of dynamic proxies
        """
        data = {"limit": limit}
        if status:
            data["status"] = status

        return await self._call(
            "get",
            "/proxies/dynamic",
            data=data,
        )

    async def get_proxy(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Get dynamic proxy details
        
        Args:
            proxy_id: Proxy identifier
            
        Returns:
            Proxy configuration and status
        """
        return await self._call(
            "get",
            f"/proxies/dynamic/{proxy_id}",
        )

    async def create_proxy(
        self,
        name: str,
        rotation_interval: int = 300,
        location: Optional[str] = None,
        protocol: str = "https",
    ) -> Dict[str, Any]:
        """Create dynamic proxy pool
        
        Args:
            name: Proxy pool name
            rotation_interval: IP rotation interval (seconds)
            location: Geographic location for IPs
            protocol: Proxy protocol ("http", "https", "socks5")
            
        Returns:
            New proxy configuration
        """
        data = {
            "name": name,
            "rotation_interval": rotation_interval,
            "protocol": protocol,
        }
        if location:
            data["location"] = location

        return await self._call(
            "post",
            "/proxies/dynamic",
            data=data,
        )

    async def delete_proxy(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Delete dynamic proxy
        
        Args:
            proxy_id: Proxy to delete
            
        Returns:
            Deletion status
        """
        return await self._call(
            "delete",
            f"/proxies/dynamic/{proxy_id}",
        )

    async def get_proxy_ips(
        self,
        proxy_id: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get IPs in proxy pool
        
        Args:
            proxy_id: Proxy identifier
            limit: Maximum IPs to return
            
        Returns:
            List of available IPs
        """
        return await self._call(
            "get",
            f"/proxies/dynamic/{proxy_id}/ips",
            data={"limit": limit},
        )

    async def get_current_ip(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Get currently active IP
        
        Args:
            proxy_id: Proxy identifier
            
        Returns:
            Current IP and metadata
        """
        return await self._call(
            "get",
            f"/proxies/dynamic/{proxy_id}/current-ip",
        )

    async def rotate_ip(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Force IP rotation
        
        Args:
            proxy_id: Proxy to rotate
            
        Returns:
            New IP information
        """
        return await self._call(
            "post",
            f"/proxies/dynamic/{proxy_id}/rotate",
        )

    async def set_rotation_interval(
        self,
        proxy_id: str,
        interval_sec: int,
    ) -> Dict[str, Any]:
        """Set IP rotation interval
        
        Args:
            proxy_id: Proxy identifier
            interval_sec: New rotation interval
            
        Returns:
            Update status
        """
        return await self._call(
            "put",
            f"/proxies/dynamic/{proxy_id}/rotation-interval",
            data={"interval": interval_sec},
        )

    async def get_rotation_stats(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Get rotation statistics
        
        Args:
            proxy_id: Proxy identifier
            
        Returns:
            Rotation stats and history
        """
        return await self._call(
            "get",
            f"/proxies/dynamic/{proxy_id}/stats",
        )

    async def enable_proxy(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Enable dynamic proxy
        
        Args:
            proxy_id: Proxy to enable
            
        Returns:
            Status update
        """
        return await self._call(
            "post",
            f"/proxies/dynamic/{proxy_id}/enable",
        )

    async def disable_proxy(
        self,
        proxy_id: str,
    ) -> Dict[str, Any]:
        """Disable dynamic proxy
        
        Args:
            proxy_id: Proxy to disable
            
        Returns:
            Status update
        """
        return await self._call(
            "post",
            f"/proxies/dynamic/{proxy_id}/disable",
        )

    async def update_proxy_config(
        self,
        proxy_id: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update proxy configuration
        
        Args:
            proxy_id: Proxy identifier
            config: New configuration
            
        Returns:
            Update status
        """
        return await self._call(
            "put",
            f"/proxies/dynamic/{proxy_id}",
            data=config,
        )

    async def get_available_locations(
        self,
    ) -> Dict[str, Any]:
        """Get available geographic locations
        
        Returns:
            List of location options
        """
        return await self._call(
            "get",
            "/proxies/dynamic/locations",
        )

    async def change_proxy_location(
        self,
        proxy_id: str,
        location: str,
    ) -> Dict[str, Any]:
        """Change proxy location
        
        Args:
            proxy_id: Proxy identifier
            location: New location
            
        Returns:
            Location change status
        """
        return await self._call(
            "put",
            f"/proxies/dynamic/{proxy_id}/location",
            data={"location": location},
        )
