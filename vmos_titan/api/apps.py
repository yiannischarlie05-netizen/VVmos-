"""
Apps API Module — Application management on device
Covers: install, uninstall, start, stop, list, upload, keep-alive
"""

from typing import Any, Dict, List, Optional
from .base import APIModule


class AppsAPI(APIModule):
    """Application management operations."""
    
    def get_module_name(self) -> str:
        return "apps"
    
    # ==================== App Installation ====================
    
    async def install_app(
        self,
        pad_code: str,
        package_url: str,
        app_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Install application on device from URL.
        
        Args:
            pad_code: Device pad code
            package_url: URL to APK file
            app_name: Optional human-readable app name
        
        Returns:
            API response with install status
        """
        return await self._call(
            "POST",
            "/api/pad/installApp",
            {
                "pad_code": pad_code,
                "package_url": package_url,
                "app_name": app_name,
            },
            timeout_sec=60.0,  # Installation may take time
        )
    
    async def uninstall_app(self, pad_code: str, package_name: str) -> Dict[str, Any]:
        """
        Uninstall application from device.
        
        Args:
            pad_code: Device pad code
            package_name: Package name (e.g., "com.example.app")
        
        Returns:
            API response with uninstall status
        """
        return await self._call(
            "POST",
            "/api/pad/uninstallApp",
            {"pad_code": pad_code, "package_name": package_name},
        )
    
    # ==================== App Control ====================
    
    async def start_app(self, pad_code: str, package_name: str) -> Dict[str, Any]:
        """
        Start/launch application on device.
        
        Args:
            pad_code: Device pad code
            package_name: Package name to start
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/startApp",
            {"pad_code": pad_code, "package_name": package_name},
        )
    
    async def stop_app(self, pad_code: str, package_name: str) -> Dict[str, Any]:
        """
        Stop/force-stop application on device.
        
        Args:
            pad_code: Device pad code
            package_name: Package name to stop
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/stopApp",
            {"pad_code": pad_code, "package_name": package_name},
        )
    
    async def restart_app(self, pad_code: str, package_name: str) -> Dict[str, Any]:
        """
        Restart application (stop and start).
        
        Args:
            pad_code: Device pad code
            package_name: Package name to restart
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/restartApp",
            {"pad_code": pad_code, "package_name": package_name},
        )
    
    async def keep_alive_app(
        self,
        pad_code: str,
        package_name: str,
        keep_alive: bool = True,
    ) -> Dict[str, Any]:
        """
        Set app to keep-alive (prevent background kill).
        
        Args:
            pad_code: Device pad code
            package_name: Package name
            keep_alive: True to keep alive, False to allow kill
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/keepAliveApp",
            {
                "pad_code": pad_code,
                "package_name": package_name,
                "keep_alive": keep_alive,
            },
        )
    
    # ==================== App Information ====================
    
    async def list_apps(
        self,
        pad_code: str,
        system_apps: bool = False,
        running_only: bool = False,
    ) -> Dict[str, Any]:
        """
        List applications on device.
        
        Args:
            pad_code: Device pad code
            system_apps: Include system apps in list
            running_only: List only running apps
        
        Returns:
            API response with app list
        """
        return await self._call(
            "POST",
            "/api/pad/listApps",
            {
                "pad_code": pad_code,
                "system_apps": system_apps,
                "running_only": running_only,
            },
        )
    
    async def get_app_info(self, pad_code: str, package_name: str) -> Dict[str, Any]:
        """
        Get information about a specific app.
        
        Args:
            pad_code: Device pad code
            package_name: Package name
        
        Returns:
            API response with app info (version, size, permissions, etc)
        """
        return await self._call(
            "POST",
            "/api/pad/getAppInfo",
            {"pad_code": pad_code, "package_name": package_name},
        )
    
    async def is_app_installed(self, pad_code: str, package_name: str) -> Dict[str, Any]:
        """
        Check if app is installed on device.
        
        Args:
            pad_code: Device pad code
            package_name: Package name
        
        Returns:
            API response with installed status
        """
        return await self._call(
            "POST",
            "/api/pad/isAppInstalled",
            {"pad_code": pad_code, "package_name": package_name},
        )
    
    async def is_app_running(self, pad_code: str, package_name: str) -> Dict[str, Any]:
        """
        Check if app is currently running on device.
        
        Args:
            pad_code: Device pad code
            package_name: Package name
        
        Returns:
            API response with running status
        """
        return await self._call(
            "POST",
            "/api/pad/isAppRunning",
            {"pad_code": pad_code, "package_name": package_name},
        )
    
    # ==================== File Upload ====================
    
    async def upload_file(
        self,
        pad_code: str,
        remote_path: str,
        file_url: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Upload file to device.
        
        Args:
            pad_code: Device pad code
            remote_path: Destination path on device
            file_url: URL to download file from
            file_name: Optional filename
            file_size: Optional filesize in bytes
        
        Returns:
            API response with upload status
        
        Raises:
            ParameterError if file too large
        """
        if file_size and file_size > self.config.max_file_upload_mb * 1024 * 1024:
            from vmos_titan.core.exceptions import ParameterError
            raise ParameterError(
                message=f"File too large: {file_size / 1024 / 1024:.1f}MB > {self.config.max_file_upload_mb}MB",
                parameter="file_size",
            )
        
        return await self._call(
            "POST",
            "/api/pad/uploadFile",
            {
                "pad_code": pad_code,
                "remote_path": remote_path,
                "file_url": file_url,
                "file_name": file_name,
                "file_size": file_size,
            },
            timeout_sec=300.0,  # Large uploads may take time
        )
    
    # ==================== Permissions ====================
    
    async def grant_permission(
        self,
        pad_code: str,
        package_name: str,
        permission: str,
    ) -> Dict[str, Any]:
        """
        Grant permission to app on device.
        
        Args:
            pad_code: Device pad code
            package_name: Package name
            permission: Permission name (e.g., "android.permission.CAMERA")
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/grantPermission",
            {
                "pad_code": pad_code,
                "package_name": package_name,
                "permission": permission,
            },
        )
    
    async def revoke_permission(
        self,
        pad_code: str,
        package_name: str,
        permission: str,
    ) -> Dict[str, Any]:
        """
        Revoke permission from app on device.
        
        Args:
            pad_code: Device pad code
            package_name: Package name
            permission: Permission name
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/revokePermission",
            {
                "pad_code": pad_code,
                "package_name": package_name,
                "permission": permission,
            },
        )
