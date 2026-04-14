"""VMOS Cloud API - Cloud Phones Module

Manages cloud phone instance lifecycle including creation, deletion,
SKU management, and image provisioning.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from vmos_titan.api.base import APIModule


@dataclass
class CloudPhoneInstance:
    """Cloud phone instance information"""
    pad_code: str
    sku: str  # SKU identifier
    status: str
    created_at: datetime
    region: str
    image_id: str
    billing_status: str
    expiry_at: Optional[datetime]


class CloudPhonesAPI(APIModule):
    """Cloud phone instance management"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "cloud_phones"

    async def list_instances(
        self,
        sku: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List cloud phone instances
        
        Args:
            sku: Filter by SKU type
            status: Filter by status ("running", "stopped", "provisioning")
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of cloud phone instances
        """
        data = {
            "limit": limit,
            "offset": offset,
        }
        if sku:
            data["sku"] = sku
        if status:
            data["status"] = status

        return await self._call(
            "get",
            "/cloud-phones",
            data=data,
        )

    async def get_instance_details(
        self,
        pad_code: str,
    ) -> Dict[str, Any]:
        """Get detailed instance information
        
        Args:
            pad_code: Instance identifier
            
        Returns:
            Detailed instance information
        """
        return await self._call(
            "get",
            f"/cloud-phones/{pad_code}",
        )

    async def create_instance(
        self,
        sku: str,
        image_id: Optional[str] = None,
        region: Optional[str] = None,
        duration_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create new cloud phone instance
        
        Args:
            sku: SKU type to provision
            image_id: Custom image ID (None = default)
            region: Region for instance
            duration_days: Rental duration in days
            
        Returns:
            New instance information
        """
        data = {"sku": sku}
        if image_id:
            data["image_id"] = image_id
        if region:
            data["region"] = region
        if duration_days:
            data["duration_days"] = duration_days

        return await self._call(
            "post",
            "/cloud-phones",
            data=data,
        )

    async def delete_instance(
        self,
        pad_code: str,
    ) -> Dict[str, Any]:
        """Delete cloud phone instance
        
        Args:
            pad_code: Instance to delete
            
        Returns:
            Deletion status
        """
        return await self._call(
            "delete",
            f"/cloud-phones/{pad_code}",
        )

    async def list_skus(
        self,
    ) -> Dict[str, Any]:
        """List available SKU types
        
        Returns:
            Available SKUs with pricing and specs
        """
        return await self._call(
            "get",
            "/cloud-phones/skus",
        )

    async def get_sku_details(
        self,
        sku: str,
    ) -> Dict[str, Any]:
        """Get detailed SKU information
        
        Args:
            sku: SKU identifier
            
        Returns:
            SKU specifications and pricing
        """
        return await self._call(
            "get",
            f"/cloud-phones/skus/{sku}",
        )

    async def list_images(
        self,
        sku: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List available provisioning images
        
        Args:
            sku: Filter by SKU type
            
        Returns:
            Available images with version info
        """
        data = {}
        if sku:
            data["sku"] = sku

        return await self._call(
            "get",
            "/cloud-phones/images",
            data=data,
        )

    async def create_custom_image(
        self,
        name: str,
        base_image_id: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create custom provisioning image
        
        Args:
            name: Image name
            base_image_id: Base image to customize
            config: Image configuration
            
        Returns:
            New image information
        """
        return await self._call(
            "post",
            "/cloud-phones/images",
            data={
                "name": name,
                "base_image_id": base_image_id,
                "config": config,
            },
        )

    async def delete_image(
        self,
        image_id: str,
    ) -> Dict[str, Any]:
        """Delete custom image
        
        Args:
            image_id: Image to delete
            
        Returns:
            Deletion status
        """
        return await self._call(
            "delete",
            f"/cloud-phones/images/{image_id}",
        )

    async def upgrade_instance_sku(
        self,
        pad_code: str,
        new_sku: str,
    ) -> Dict[str, Any]:
        """Upgrade instance to different SKU
        
        Args:
            pad_code: Instance to upgrade
            new_sku: Target SKU type
            
        Returns:
            Upgrade status
        """
        return await self._call(
            "post",
            f"/cloud-phones/{pad_code}/upgrade",
            data={"sku": new_sku},
        )

    async def reimage_instance(
        self,
        pad_code: str,
        image_id: str,
    ) -> Dict[str, Any]:
        """Reimage instance with different image
        
        Args:
            pad_code: Instance to reimage
            image_id: Target image
            
        Returns:
            Reimage operation status
        """
        return await self._call(
            "post",
            f"/cloud-phones/{pad_code}/reimage",
            data={"image_id": image_id},
        )

    async def get_billing_info(
        self,
        pad_code: str,
    ) -> Dict[str, Any]:
        """Get instance billing information
        
        Args:
            pad_code: Instance identifier
            
        Returns:
            Billing details and charges
        """
        return await self._call(
            "get",
            f"/cloud-phones/{pad_code}/billing",
        )

    async def extend_rental(
        self,
        pad_code: str,
        days: int,
    ) -> Dict[str, Any]:
        """Extend instance rental period
        
        Args:
            pad_code: Instance to extend
            days: Additional days
            
        Returns:
            New expiry information
        """
        return await self._call(
            "post",
            f"/cloud-phones/{pad_code}/extend",
            data={"days": days},
        )
