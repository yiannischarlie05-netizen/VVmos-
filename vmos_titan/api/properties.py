"""VMOS Cloud API - Properties Module

Handles device property read/write operations including batch operations
and property schema validation.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from vmos_titan.api.base import APIModule


@dataclass
class PropertyValue:
    """Single property with metadata"""
    key: str
    value: Any
    type_: str  # "string", "int", "float", "bool"
    readonly: bool = False


class PropertiesAPI(APIModule):
    """Device property management operations"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "properties"

    async def get_property(
        self,
        pad_code: str,
        property_key: str,
    ) -> Dict[str, Any]:
        """Get single device property
        
        Args:
            pad_code: Device identifier
            property_key: Property key (e.g., "ro.serialno", "ro.build.version.release")
            
        Returns:
            Dictionary with property value and metadata
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/properties/{property_key}",
        )

    async def get_properties(
        self,
        pad_code: str,
        property_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get multiple device properties
        
        Args:
            pad_code: Device identifier
            property_keys: List of specific keys to get (None = all)
            
        Returns:
            Dictionary mapping property keys to values
        """
        if property_keys:
            return await self._call(
                "post",
                f"/device/{pad_code}/properties/batch",
                data={"keys": property_keys},
            )
        else:
            return await self._call(
                "get",
                f"/device/{pad_code}/properties",
            )

    async def set_property(
        self,
        pad_code: str,
        property_key: str,
        value: Any,
    ) -> Dict[str, Any]:
        """Set single device property
        
        Args:
            pad_code: Device identifier
            property_key: Property key
            value: New value
            
        Returns:
            Status response
        """
        return await self._call(
            "put",
            f"/device/{pad_code}/properties/{property_key}",
            data={"value": value},
        )

    async def set_properties(
        self,
        pad_code: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Set multiple device properties (batch)
        
        Args:
            pad_code: Device identifier
            properties: Dictionary of key->value pairs
            
        Returns:
            Dictionary mapping keys to update status
        """
        return await self._call(
            "post",
            f"/device/{pad_code}/properties/batch-set",
            data={"properties": properties},
        )

    async def get_ro_properties(
        self,
        pad_code: str,
    ) -> Dict[str, str]:
        """Get all read-only (ro.*) properties
        
        Args:
            pad_code: Device identifier
            
        Returns:
            Dictionary of ro.* properties
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/properties/ro",
        )

    async def get_system_properties(
        self,
        pad_code: str,
    ) -> Dict[str, str]:
        """Get system build properties
        
        Args:
            pad_code: Device identifier
            
        Returns:
            System property dictionary
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/properties/system",
        )

    async def reset_properties(
        self,
        pad_code: str,
        property_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Reset properties to defaults
        
        Args:
            pad_code: Device identifier
            property_keys: Specific keys to reset (None = all)
            
        Returns:
            Reset status
        """
        data = {}
        if property_keys:
            data["keys"] = property_keys

        return await self._call(
            "post",
            f"/device/{pad_code}/properties/reset",
            data=data,
        )

    async def validate_properties(
        self,
        pad_code: str,
        properties: Dict[str, Any],
    ) -> Dict[str, bool]:
        """Validate properties before setting
        
        Args:
            pad_code: Device identifier
            properties: Properties to validate
            
        Returns:
            Dictionary mapping property keys to validation result
        """
        return await self._call(
            "post",
            f"/device/{pad_code}/properties/validate",
            data={"properties": properties},
        )

    async def export_properties(
        self,
        pad_code: str,
        format_: str = "json",
    ) -> Dict[str, Any]:
        """Export properties to file
        
        Args:
            pad_code: Device identifier
            format_: Export format ("json", "yaml", "properties")
            
        Returns:
            Exported properties data
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/properties/export",
            data={"format": format_},
        )

    async def import_properties(
        self,
        pad_code: str,
        properties_data: Dict[str, Any],
        format_: str = "json",
    ) -> Dict[str, Any]:
        """Import properties from file/data
        
        Args:
            pad_code: Device identifier
            properties_data: Properties to import
            format_: Data format ("json", "yaml", "properties")
            
        Returns:
            Import status
        """
        return await self._call(
            "post",
            f"/device/{pad_code}/properties/import",
            data={
                "properties": properties_data,
                "format": format_,
            },
        )

    async def get_property_schema(
        self,
        pad_code: str,
    ) -> Dict[str, Any]:
        """Get property schema/metadata for device
        
        Args:
            pad_code: Device identifier
            
        Returns:
            Property schema with types and constraints
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/properties/schema",
        )
