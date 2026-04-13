"""
Refactored VMOSCloudClient — Unified facade for VMOS Cloud API
Orchestrates domain-specific API modules with 100% backward compatibility
"""

from typing import Any, Dict, Optional
import logging

from vmos_titan.core.config import APIConfig, get_default_config
from vmos_titan.core.signed_http_client import SignedHTTPClient
from vmos_titan.api.device import DeviceAPI
from vmos_titan.api.network import NetworkAPI
from vmos_titan.api.apps import AppsAPI
from vmos_titan.api.interaction import InteractionAPI
from vmos_titan.api.properties import PropertiesAPI
from vmos_titan.api.tasks import TasksAPI
from vmos_titan.api.tokens import TokensAPI
from vmos_titan.api.cloud_phones import CloudPhonesAPI
from vmos_titan.api.timing_devices import TimingDevicesAPI
from vmos_titan.api.storage import StorageAPI
from vmos_titan.api.email import EmailAPI
from vmos_titan.api.proxy_dynamic import ProxyDynamicAPI
from vmos_titan.api.proxy_static import ProxyStaticAPI
from vmos_titan.api.automation_tasks import AutomationTasksAPI
from vmos_titan.api.resources import ResourcesAPI

logger = logging.getLogger(__name__)


class VMOSCloudClient:
    """
    Unified VMOS Cloud API client using modular domain-specific API classes.
    
    This client provides:
    - Clean modular architecture (device, network, apps, interaction modules)
    - Type-safe operations with comprehensive error handling
    - Safety guards for dangerous operations (restart, reset, etc.)
    - Circuit breaker with exponential backoff resilience
    - Request tracing and structured logging
    - 100% backward compatibility with existing code
    
    Usage:
        # Using modular API
        async with VMOSCloudClient() as client:
            # Device operations
            await client.devices.restart(pad_code)
            await client.devices.set_gps(pad_code, 37.7749, -122.4194)
            
            # Network operations
            await client.network.set_smart_ip(pad_code, "US", "San Francisco")
            
            # App management
            await client.apps.start_app(pad_code, "com.google.android.apps.maps")
            
            # User interaction
            await client.interaction.touch(pad_code, 100, 200)
    """
    
    def __init__(
        self,
        config: Optional[APIConfig] = None,
        name: str = "vmos-cloud-client",
    ):
        """
        Initialize VMOSCloudClient.
        
        Args:
            config: APIConfig instance (if None, uses environment variables)
            name: Client name for logging and tracing
        """
        self.config = config or get_default_config()
        self.name = name
        
        # Create base HTTP client
        self._client = SignedHTTPClient(self.config, name=name)
        
        # Lazy-loaded domain modules
        self._devices: Optional[DeviceAPI] = None
        self._network: Optional[NetworkAPI] = None
        self._apps: Optional[AppsAPI] = None
        self._interaction: Optional[InteractionAPI] = None
        self._properties: Optional[PropertiesAPI] = None
        self._tasks: Optional[TasksAPI] = None
        self._tokens: Optional[TokensAPI] = None
        self._cloud_phones: Optional[CloudPhonesAPI] = None
        self._timing_devices: Optional[TimingDevicesAPI] = None
        self._storage: Optional[StorageAPI] = None
        self._email: Optional[EmailAPI] = None
        self._proxy_dynamic: Optional[ProxyDynamicAPI] = None
        self._proxy_static: Optional[ProxyStaticAPI] = None
        self._automation_tasks: Optional[AutomationTasksAPI] = None
        self._resources: Optional[ResourcesAPI] = None
    
    # ==================== Module Properties (Lazy Loading) ====================
    
    @property
    def devices(self) -> DeviceAPI:
        """Get device API module."""
        if self._devices is None:
            self._devices = DeviceAPI(self._client)
        return self._devices
    
    @property
    def device(self) -> DeviceAPI:
        """Alias for devices module."""
        return self.devices
    
    @property
    def network(self) -> NetworkAPI:
        """Get network API module."""
        if self._network is None:
            self._network = NetworkAPI(self._client)
        return self._network
    
    @property
    def apps(self) -> AppsAPI:
        """Get apps API module."""
        if self._apps is None:
            self._apps = AppsAPI(self._client)
        return self._apps
    
    @property
    def interaction(self) -> InteractionAPI:
        """Get interaction API module."""
        if self._interaction is None:
            self._interaction = InteractionAPI(self._client)
        return self._interaction
    
    @property
    def properties(self) -> PropertiesAPI:
        """Get properties API module."""
        if self._properties is None:
            self._properties = PropertiesAPI(self._client)
        return self._properties
    
    @property
    def tasks(self) -> TasksAPI:
        """Get tasks API module."""
        if self._tasks is None:
            self._tasks = TasksAPI(self._client)
        return self._tasks
    
    @property
    def tokens(self) -> TokensAPI:
        """Get tokens API module."""
        if self._tokens is None:
            self._tokens = TokensAPI(self._client)
        return self._tokens
    
    @property
    def cloud_phones(self) -> CloudPhonesAPI:
        """Get cloud phones API module."""
        if self._cloud_phones is None:
            self._cloud_phones = CloudPhonesAPI(self._client)
        return self._cloud_phones
    
    @property
    def timing_devices(self) -> TimingDevicesAPI:
        """Get timing devices API module."""
        if self._timing_devices is None:
            self._timing_devices = TimingDevicesAPI(self._client)
        return self._timing_devices
    
    @property
    def storage(self) -> StorageAPI:
        """Get storage API module."""
        if self._storage is None:
            self._storage = StorageAPI(self._client)
        return self._storage
    
    @property
    def email(self) -> EmailAPI:
        """Get email API module."""
        if self._email is None:
            self._email = EmailAPI(self._client)
        return self._email
    
    @property
    def proxy_dynamic(self) -> ProxyDynamicAPI:
        """Get dynamic proxy API module."""
        if self._proxy_dynamic is None:
            self._proxy_dynamic = ProxyDynamicAPI(self._client)
        return self._proxy_dynamic
    
    @property
    def proxy_static(self) -> ProxyStaticAPI:
        """Get static proxy API module."""
        if self._proxy_static is None:
            self._proxy_static = ProxyStaticAPI(self._client)
        return self._proxy_static
    
    @property
    def automation_tasks(self) -> AutomationTasksAPI:
        """Get automation tasks API module."""
        if self._automation_tasks is None:
            self._automation_tasks = AutomationTasksAPI(self._client)
        return self._automation_tasks
    
    @property
    def resources(self) -> ResourcesAPI:
        """Get resources API module."""
        if self._resources is None:
            self._resources = ResourcesAPI(self._client)
        return self._resources
    
    # ==================== Context Manager ====================
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
    
    async def close(self):
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.close()
    
    # ==================== Legacy API (Backward Compatibility) ====================
    
    async def restart(self, pad_code: str) -> Dict[str, Any]:
        """Legacy method - use client.devices.restart() instead."""
        logger.warning("Using legacy restart() method, prefer devices.restart()")
        return await self.devices.restart(pad_code)
    
    async def reset(self, pad_code: str) -> Dict[str, Any]:
        """Legacy method - use client.devices.reset() instead."""
        logger.warning("Using legacy reset() method, prefer devices.reset()")
        return await self.devices.reset(pad_code)
    
    async def get_status(self, pad_code: str) -> Dict[str, Any]:
        """Legacy method - use client.devices.get_status() instead."""
        logger.warning("Using legacy get_status() method, prefer devices.get_status()")
        return await self.devices.get_status(pad_code)
    
    async def screenshot(self, pad_code: str) -> Dict[str, Any]:
        """Legacy method - use client.devices.screenshot() instead."""
        logger.warning("Using legacy screenshot() method, prefer devices.screenshot()")
        return await self.devices.screenshot(pad_code)
    
    async def adb_shell(self, pad_code: str, command: str) -> Dict[str, Any]:
        """Legacy method - use client.devices.adb_shell() instead."""
        logger.warning("Using legacy adb_shell() method, prefer devices.adb_shell()")
        return await self.devices.adb_shell(pad_code, command)
    
    async def set_smart_ip(
        self,
        pad_code: str,
        country: str,
        city: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Legacy method - use client.network.set_smart_ip() instead."""
        logger.warning("Using legacy set_smart_ip() method, prefer network.set_smart_ip()")
        return await self.network.set_smart_ip(pad_code, country, city, **kwargs)
    
    async def check_ip(self, pad_code: str) -> Dict[str, Any]:
        """Legacy method - use client.network.check_ip() instead."""
        logger.warning("Using legacy check_ip() method, prefer network.check_ip()")
        return await self.network.check_ip(pad_code)
    
    async def start_app(self, pad_code: str, package_name: str) -> Dict[str, Any]:
        """Legacy method - use client.apps.start_app() instead."""
        logger.warning("Using legacy start_app() method, prefer apps.start_app()")
        return await self.apps.start_app(pad_code, package_name)
    
    async def stop_app(self, pad_code: str, package_name: str) -> Dict[str, Any]:
        """Legacy method - use client.apps.stop_app() instead."""
        logger.warning("Using legacy stop_app() method, prefer apps.stop_app()")
        return await self.apps.stop_app(pad_code, package_name)
    
    async def touch(self, pad_code: str, x: int, y: int) -> Dict[str, Any]:
        """Legacy method - use client.interaction.touch() instead."""
        logger.warning("Using legacy touch() method, prefer interaction.touch()")
        return await self.interaction.touch(pad_code, x, y)
    
    # ==================== Statistics & Monitoring ====================
    
    def get_config(self) -> APIConfig:
        """Get current APIConfig."""
        return self.config
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "name": self.name,
            "config": {
                "endpoint": self.config.endpoint,
                "allow_restart": self.config.allow_restart,
                "allow_template_import_pad": self.config.allow_template_import_pad,
            },
            "http_client": self._client.get_stats(),
        }


# ==================== Factory Functions ====================

def get_client(
    ak: Optional[str] = None,
    sk: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> VMOSCloudClient:
    """
    Create VMOS Cloud API client with optional credential override.
    
    Args:
        ak: Access key (if None, uses environment variable)
        sk: Secret key (if None, uses environment variable)
        endpoint: API endpoint (if None, uses environment variable)
    
    Returns:
        VMOSCloudClient instance
    
    Example:
        client = get_client()
        async with client as c:
            await c.devices.restart("PAD_CODE")
    """
    config = APIConfig.from_env()
    
    if ak:
        config.access_key = ak
    if sk:
        config.secret_key = sk
    if endpoint:
        config.endpoint = endpoint
    
    return VMOSCloudClient(config)


def get_default_client() -> VMOSCloudClient:
    """
    Get default VMOS Cloud API client using environment configuration.
    
    Returns:
        VMOSCloudClient instance configured from environment
    
    Example:
        client = get_default_client()
        async with client as c:
            await c.devices.restart("PAD_CODE")
    """
    return VMOSCloudClient(config=get_default_config())
