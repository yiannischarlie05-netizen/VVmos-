"""VMOS Cloud API - Storage Module

Manages device storage operations including backup, restore, encryption,
and data transfer.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from vmos_titan.api.base import APIModule


@dataclass
class BackupInfo:
    """Backup information"""
    backup_id: str
    pad_code: str
    created_at: datetime
    size_bytes: int
    status: str  # "pending", "backing_up", "completed", "failed"
    encryption: bool


class StorageAPI(APIModule):
    """Device storage and backup operations"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "storage"

    async def get_storage_info(
        self,
        pad_code: str,
    ) -> Dict[str, Any]:
        """Get device storage information
        
        Args:
            pad_code: Device identifier
            
        Returns:
            Storage capacity and usage info
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/storage",
        )

    async def create_backup(
        self,
        pad_code: str,
        include_apps: bool = True,
        include_data: bool = True,
        compression: bool = True,
    ) -> Dict[str, Any]:
        """Create device backup
        
        Args:
            pad_code: Device to backup
            include_apps: Backup installed apps
            include_data: Backup app data and files
            compression: Compress backup data
            
        Returns:
            Backup task information
        """
        return await self._call(
            "post",
            f"/device/{pad_code}/backups",
            data={
                "include_apps": include_apps,
                "include_data": include_data,
                "compression": compression,
            },
        )

    async def list_backups(
        self,
        pad_code: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List device backups
        
        Args:
            pad_code: Device identifier
            limit: Maximum results
            
        Returns:
            List of backup information
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/backups",
            data={"limit": limit},
        )

    async def get_backup_status(
        self,
        pad_code: str,
        backup_id: str,
    ) -> Dict[str, Any]:
        """Get backup status
        
        Args:
            pad_code: Device identifier
            backup_id: Backup identifier
            
        Returns:
            Backup status and progress
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/backups/{backup_id}",
        )

    async def restore_backup(
        self,
        pad_code: str,
        backup_id: str,
    ) -> Dict[str, Any]:
        """Restore device from backup
        
        Args:
            pad_code: Device to restore to
            backup_id: Backup to restore
            
        Returns:
            Restore operation status
        """
        return await self._call(
            "post",
            f"/device/{pad_code}/backups/{backup_id}/restore",
        )

    async def delete_backup(
        self,
        pad_code: str,
        backup_id: str,
    ) -> Dict[str, Any]:
        """Delete backup
        
        Args:
            pad_code: Device identifier
            backup_id: Backup to delete
            
        Returns:
            Deletion status
        """
        return await self._call(
            "delete",
            f"/device/{pad_code}/backups/{backup_id}",
        )

    async def download_backup(
        self,
        pad_code: str,
        backup_id: str,
    ) -> Dict[str, Any]:
        """Download backup file
        
        Args:
            pad_code: Device identifier
            backup_id: Backup to download
            
        Returns:
            Download URL and metadata
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/backups/{backup_id}/download",
        )

    async def upload_backup(
        self,
        pad_code: str,
        backup_file_url: str,
    ) -> Dict[str, Any]:
        """Upload backup file for restoration
        
        Args:
            pad_code: Device to restore to
            backup_file_url: URL of backup file
            
        Returns:
            Upload and import status
        """
        return await self._call(
            "post",
            f"/device/{pad_code}/backups/upload",
            data={"file_url": backup_file_url},
        )

    async def encrypt_backup(
        self,
        pad_code: str,
        backup_id: str,
        password: str,
    ) -> Dict[str, Any]:
        """Encrypt existing backup with password
        
        Args:
            pad_code: Device identifier
            backup_id: Backup to encrypt
            password: Encryption password
            
        Returns:
            Encryption status
        """
        return await self._call(
            "post",
            f"/device/{pad_code}/backups/{backup_id}/encrypt",
            data={"password": password},
        )

    async def schedule_backup(
        self,
        pad_code: str,
        schedule: str,  # "daily", "weekly", "monthly"
        time_utc: str = "02:00",
    ) -> Dict[str, Any]:
        """Schedule automatic backups
        
        Args:
            pad_code: Device identifier
            schedule: Backup frequency
            time_utc: Time in UTC (HH:MM)
            
        Returns:
            Schedule information
        """
        return await self._call(
            "post",
            f"/device/{pad_code}/backups/schedule",
            data={
                "schedule": schedule,
                "time_utc": time_utc,
            },
        )

    async def get_backup_schedule(
        self,
        pad_code: str,
    ) -> Dict[str, Any]:
        """Get backup schedule for device
        
        Args:
            pad_code: Device identifier
            
        Returns:
            Schedule information
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/backups/schedule",
        )

    async def clear_device_storage(
        self,
        pad_code: str,
        target_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Clear device storage
        
        Args:
            pad_code: Device identifier
            target_path: Path to clear (None = all)
            
        Returns:
            Cleared space information
        """
        data = {}
        if target_path:
            data["path"] = target_path

        return await self._call(
            "post",
            f"/device/{pad_code}/storage/clear",
            data=data,
        )

    async def get_storage_quota(
        self,
        pad_code: str,
    ) -> Dict[str, Any]:
        """Get storage quota information
        
        Args:
            pad_code: Device identifier
            
        Returns:
            Quota and usage details
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/storage/quota",
        )

    async def increase_storage(
        self,
        pad_code: str,
        size_gb: int,
    ) -> Dict[str, Any]:
        """Increase device storage quota
        
        Args:
            pad_code: Device identifier
            size_gb: Additional storage in GB
            
        Returns:
            New quota information
        """
        return await self._call(
            "post",
            f"/device/{pad_code}/storage/increase",
            data={"size_gb": size_gb},
        )
