"""VMOS Cloud API - Resources Module

Manages resource allocation, instance lists, batch operations, and
resource pooling for cloud devices.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from vmos_titan.api.base import APIModule


@dataclass
class ResourceInfo:
    """Resource information"""
    resource_id: str
    type_: str  # "cpu", "memory", "storage", "bandwidth"
    allocated: int
    available: int
    total: int
    utilization: float


class ResourcesAPI(APIModule):
    """Cloud resource management"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "resources"

    async def get_resource_info(
        self,
    ) -> Dict[str, Any]:
        """Get overall resource information
        
        Returns:
            Resource allocation summary
        """
        return await self._call(
            "get",
            "/resources",
        )

    async def get_device_resource_usage(
        self,
        pad_code: str,
    ) -> Dict[str, Any]:
        """Get resource usage for specific device
        
        Args:
            pad_code: Device identifier
            
        Returns:
            Device resource utilization
        """
        return await self._call(
            "get",
            f"/resources/device/{pad_code}",
        )

    async def list_all_devices(
        self,
        status: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List all cloud devices
        
        Args:
            status: Filter by status
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of all devices with metadata
        """
        data = {
            "limit": limit,
            "offset": offset,
        }
        if status:
            data["status"] = status

        return await self._call(
            "get",
            "/resources/devices",
            data=data,
        )

    async def get_device_metrics(
        self,
        pad_code: str,
    ) -> Dict[str, Any]:
        """Get device performance metrics
        
        Args:
            pad_code: Device identifier
            
        Returns:
            CPU, memory, network metrics
        """
        return await self._call(
            "get",
            f"/resources/metrics/{pad_code}",
        )

    async def batch_get_device_status(
        self,
        pad_codes: List[str],
    ) -> Dict[str, Any]:
        """Get status of multiple devices
        
        Args:
            pad_codes: Device identifiers
            
        Returns:
            Status for each device
        """
        return await self._call(
            "post",
            "/resources/batch/status",
            data={"pad_codes": pad_codes},
        )

    async def batch_device_operation(
        self,
        pad_codes: List[str],
        operation: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute operation on batch of devices
        
        Args:
            pad_codes: Devices to operate on
            operation: Operation name
            params: Operation parameters
            
        Returns:
            Batch operation status
        """
        data = {
            "pad_codes": pad_codes,
            "operation": operation,
        }
        if params:
            data["params"] = params

        return await self._call(
            "post",
            "/resources/batch/operation",
            data=data,
        )

    async def allocate_resource(
        self,
        resource_type: str,
        quantity: int,
    ) -> Dict[str, Any]:
        """Allocate additional resources
        
        Args:
            resource_type: Type of resource
            quantity: Amount to allocate
            
        Returns:
            Allocation confirmation
        """
        return await self._call(
            "post",
            "/resources/allocate",
            data={
                "type": resource_type,
                "quantity": quantity,
            },
        )

    async def deallocate_resource(
        self,
        resource_id: str,
    ) -> Dict[str, Any]:
        """Release allocated resources
        
        Args:
            resource_id: Resource to release
            
        Returns:
            Deallocation status
        """
        return await self._call(
            "post",
            "/resources/deallocate",
            data={"resource_id": resource_id},
        )

    async def get_quota(
        self,
    ) -> Dict[str, Any]:
        """Get account resource quota
        
        Returns:
            Quota limits by resource type
        """
        return await self._call(
            "get",
            "/resources/quota",
        )

    async def get_quota_usage(
        self,
    ) -> Dict[str, Any]:
        """Get quota usage
        
        Returns:
            Current usage against quota
        """
        return await self._call(
            "get",
            "/resources/quota/usage",
        )

    async def request_quota_increase(
        self,
        resource_type: str,
        requested_amount: int,
    ) -> Dict[str, Any]:
        """Request increase to quota
        
        Args:
            resource_type: Resource type
            requested_amount: Requested new limit
            
        Returns:
            Request status
        """
        return await self._call(
            "post",
            "/resources/quota/request",
            data={
                "type": resource_type,
                "amount": requested_amount,
            },
        )

    async def get_resource_history(
        self,
        time_window_days: int = 30,
    ) -> Dict[str, Any]:
        """Get resource usage history
        
        Args:
            time_window_days: Historical window
            
        Returns:
            Historical resource data
        """
        return await self._call(
            "get",
            "/resources/history",
            data={"days": time_window_days},
        )

    async def scale_device_resources(
        self,
        pad_code: str,
        cpu_cores: Optional[int] = None,
        memory_gb: Optional[int] = None,
        storage_gb: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Scale device resources
        
        Args:
            pad_code: Device to scale
            cpu_cores: New CPU count
            memory_gb: New memory amount
            storage_gb: New storage amount
            
        Returns:
            Scaling status
        """
        data = {"pad_code": pad_code}
        if cpu_cores is not None:
            data["cpu_cores"] = cpu_cores
        if memory_gb is not None:
            data["memory_gb"] = memory_gb
        if storage_gb is not None:
            data["storage_gb"] = storage_gb

        return await self._call(
            "post",
            "/resources/scale",
            data=data,
        )

    async def get_billing_info(
        self,
    ) -> Dict[str, Any]:
        """Get resource billing information
        
        Returns:
            Billing summary and charges
        """
        return await self._call(
            "get",
            "/resources/billing",
        )

    async def get_resource_recommendations(
        self,
    ) -> Dict[str, Any]:
        """Get resource optimization recommendations
        
        Returns:
            Recommended resource configuration
        """
        return await self._call(
            "get",
            "/resources/recommendations",
        )
