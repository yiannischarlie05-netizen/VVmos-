"""VMOS Cloud API - Timing Devices Module

Manages timing device instances for scheduled and recurring operations.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from vmos_titan.api.base import APIModule


@dataclass
class TimingDevice:
    """Timing device instance"""
    device_id: str
    name: str
    status: str
    created_at: datetime
    assigned_tasks: int


class TimingDevicesAPI(APIModule):
    """Timing device management"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "timing_devices"

    async def list_devices(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List timing devices
        
        Args:
            status: Filter by status ("available", "busy", "offline")
            limit: Maximum results
            
        Returns:
            List of timing devices
        """
        data = {"limit": limit}
        if status:
            data["status"] = status

        return await self._call(
            "get",
            "/timing-devices",
            data=data,
        )

    async def get_device(
        self,
        device_id: str,
    ) -> Dict[str, Any]:
        """Get device details
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device information
        """
        return await self._call(
            "get",
            f"/timing-devices/{device_id}",
        )

    async def create_device(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create new timing device
        
        Args:
            name: Device name
            config: Device configuration
            
        Returns:
            New device information
        """
        return await self._call(
            "post",
            "/timing-devices",
            data={
                "name": name,
                "config": config,
            },
        )

    async def delete_device(
        self,
        device_id: str,
    ) -> Dict[str, Any]:
        """Delete timing device
        
        Args:
            device_id: Device to delete
            
        Returns:
            Deletion status
        """
        return await self._call(
            "delete",
            f"/timing-devices/{device_id}",
        )

    async def assign_task(
        self,
        device_id: str,
        task_id: str,
    ) -> Dict[str, Any]:
        """Assign task to device
        
        Args:
            device_id: Device identifier
            task_id: Task to assign
            
        Returns:
            Assignment status
        """
        return await self._call(
            "post",
            f"/timing-devices/{device_id}/tasks",
            data={"task_id": task_id},
        )

    async def unassign_task(
        self,
        device_id: str,
        task_id: str,
    ) -> Dict[str, Any]:
        """Unassign task from device
        
        Args:
            device_id: Device identifier
            task_id: Task to unassign
            
        Returns:
            Unassignment status
        """
        return await self._call(
            "delete",
            f"/timing-devices/{device_id}/tasks/{task_id}",
        )

    async def get_assigned_tasks(
        self,
        device_id: str,
    ) -> Dict[str, Any]:
        """Get tasks assigned to device
        
        Args:
            device_id: Device identifier
            
        Returns:
            List of assigned tasks
        """
        return await self._call(
            "get",
            f"/timing-devices/{device_id}/tasks",
        )

    async def enable_device(
        self,
        device_id: str,
    ) -> Dict[str, Any]:
        """Enable timing device
        
        Args:
            device_id: Device to enable
            
        Returns:
            Status update
        """
        return await self._call(
            "post",
            f"/timing-devices/{device_id}/enable",
        )

    async def disable_device(
        self,
        device_id: str,
    ) -> Dict[str, Any]:
        """Disable timing device
        
        Args:
            device_id: Device to disable
            
        Returns:
            Status update
        """
        return await self._call(
            "post",
            f"/timing-devices/{device_id}/disable",
        )

    async def get_device_stats(
        self,
        device_id: str,
    ) -> Dict[str, Any]:
        """Get device statistics
        
        Args:
            device_id: Device identifier
            
        Returns:
            Performance statistics
        """
        return await self._call(
            "get",
            f"/timing-devices/{device_id}/stats",
        )

    async def reset_device(
        self,
        device_id: str,
    ) -> Dict[str, Any]:
        """Reset device to default state
        
        Args:
            device_id: Device to reset
            
        Returns:
            Reset status
        """
        return await self._call(
            "post",
            f"/timing-devices/{device_id}/reset",
        )

    async def get_queue_estimate(
        self,
        device_id: str,
    ) -> Dict[str, Any]:
        """Get estimated processing time
        
        Args:
            device_id: Device identifier
            
        Returns:
            Queue and processing estimates
        """
        return await self._call(
            "get",
            f"/timing-devices/{device_id}/queue-estimate",
        )

    async def update_device_config(
        self,
        device_id: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update device configuration
        
        Args:
            device_id: Device identifier
            config: New configuration
            
        Returns:
            Update status
        """
        return await self._call(
            "put",
            f"/timing-devices/{device_id}/config",
            data=config,
        )
