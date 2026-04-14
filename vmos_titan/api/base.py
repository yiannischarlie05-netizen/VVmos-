"""
APIModule — Base class for domain-specific API modules
Provides common patterns for all API domains (device, network, apps, etc.)
"""

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class APIModule(ABC):
    """
    Abstract base class for domain-specific API modules.
    
    Provides common patterns:
    - Access to SignedHTTPClient for making authenticated requests
    - Safety guard checking
    - Error handling and retry logic (delegated to client)
    - Request tracing
    """
    
    def __init__(self, client):
        """
        Initialize API module.
        
        Args:
            client: SignedHTTPClient instance for making requests
        """
        self.client = client
        self.config = client.config
    
    @abstractmethod
    def get_module_name(self) -> str:
        """Get human-readable module name."""
        pass
    
    async def _call(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        timeout_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute API call through SignedHTTPClient.
        
        Args:
            method: HTTP method (POST, GET, etc.)
            path: API endpoint path
            data: Request body
            timeout_sec: Request timeout
        
        Returns:
            Parsed API response
        
        Raises:
            VMOSAPIError and subclasses on error
        """
        return await self.client._execute_request(method, path, data, timeout_sec)
    
    def _check_guard(self, operation: str) -> None:
        """
        Check if operation is allowed by safety guards.
        
        Args:
            operation: Operation name (e.g., "restart", "replacePad")
        
        Raises:
            GuardViolationError if guard not set
            ForbiddenOperationError if operation is forbidden
        """
        from vmos_titan.core.exceptions import GuardViolationError, ForbiddenOperationError
        
        # Check if operation is forbidden
        if not self.config.is_operation_allowed(operation):
            reason = self.config.FORBIDDEN_OPS.get(operation)
            raise ForbiddenOperationError(
                message=f"Operation {operation} is forbidden",
                operation=operation,
                reason=reason,
            )
        
        # Check if operation requires guard
        if self.config.requires_guard(operation):
            guard_name = "VMOS_ALLOW_RESTART" if operation == "restart" else "VMOS_ALLOW_TEMPLATE_IMPORT_PAD"
            raise GuardViolationError(
                message=f"Operation {operation} requires safety guard",
                guard_name=guard_name,
            )
