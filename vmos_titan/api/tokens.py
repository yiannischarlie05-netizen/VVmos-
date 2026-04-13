"""VMOS Cloud API - Tokens Module

Manages STS (Security Token Service) tokens and credential lifecycle
for secure API operations.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from vmos_titan.api.base import APIModule


@dataclass
class TokenInfo:
    """STS token information"""
    token: str
    token_type: str  # "access", "refresh", "session"
    expires_at: datetime
    scope: str
    issued_at: datetime


class TokensAPI(APIModule):
    """STS token lifecycle management"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "tokens"

    async def request_token(
        self,
        service: str = "vmos-cloud",
        duration_sec: int = 3600,
    ) -> Dict[str, Any]:
        """Request new STS token
        
        Args:
            service: Service name for token scope
            duration_sec: Token validity duration in seconds
            
        Returns:
            Token information with expiry
        """
        return await self._call(
            "post",
            "/sts/tokens",
            data={
                "service": service,
                "duration": duration_sec,
            },
        )

    async def get_token_status(
        self,
        token: str,
    ) -> Dict[str, Any]:
        """Get token status and remaining validity
        
        Args:
            token: Token string
            
        Returns:
            Token status information
        """
        return await self._call(
            "get",
            "/sts/tokens/status",
            data={"token": token},
        )

    async def refresh_token(
        self,
        refresh_token: str,
        duration_sec: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Refresh token using refresh token
        
        Args:
            refresh_token: Refresh token from previous request
            duration_sec: New token validity duration
            
        Returns:
            New token information
        """
        data = {"refresh_token": refresh_token}
        if duration_sec:
            data["duration"] = duration_sec

        return await self._call(
            "post",
            "/sts/tokens/refresh",
            data=data,
        )

    async def revoke_token(
        self,
        token: str,
    ) -> Dict[str, Any]:
        """Revoke token for security
        
        Args:
            token: Token to revoke
            
        Returns:
            Revocation status
        """
        return await self._call(
            "post",
            "/sts/tokens/revoke",
            data={"token": token},
        )

    async def list_active_tokens(
        self,
    ) -> Dict[str, Any]:
        """List all active tokens for account
        
        Returns:
            List of active tokens with metadata
        """
        return await self._call(
            "get",
            "/sts/tokens/active",
        )

    async def revoke_all_tokens(
        self,
    ) -> Dict[str, Any]:
        """Revoke all active tokens
        
        Returns:
            Revocation status
        """
        return await self._call(
            "post",
            "/sts/tokens/revoke-all",
        )

    async def get_token_permissions(
        self,
        token: str,
    ) -> Dict[str, Any]:
        """Get permissions granted by token
        
        Args:
            token: Token to check
            
        Returns:
            Permissions dictionary
        """
        return await self._call(
            "get",
            "/sts/tokens/permissions",
            data={"token": token},
        )

    async def create_scoped_token(
        self,
        permissions: list[str],
        duration_sec: int = 3600,
        pad_codes: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """Create token with limited scope
        
        Args:
            permissions: List of permission strings
            duration_sec: Token validity duration
            pad_codes: Limit to specific devices (None = all)
            
        Returns:
            Scoped token information
        """
        data = {
            "permissions": permissions,
            "duration": duration_sec,
        }
        if pad_codes:
            data["pad_codes"] = pad_codes

        return await self._call(
            "post",
            "/sts/tokens/scoped",
            data=data,
        )

    async def validate_token(
        self,
        token: str,
    ) -> Dict[str, Any]:
        """Validate token authenticity and status
        
        Args:
            token: Token to validate
            
        Returns:
            Validation result with token claims
        """
        return await self._call(
            "post",
            "/sts/tokens/validate",
            data={"token": token},
        )

    async def exchange_token(
        self,
        token: str,
        new_service: str,
    ) -> Dict[str, Any]:
        """Exchange token for service-specific token
        
        Args:
            token: Current token
            new_service: Target service name
            
        Returns:
            New service-specific token
        """
        return await self._call(
            "post",
            "/sts/tokens/exchange",
            data={
                "token": token,
                "service": new_service,
            },
        )

    async def get_token_history(
        self,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get token request history
        
        Args:
            limit: Maximum records to return
            
        Returns:
            Token history with timestamps and status
        """
        return await self._call(
            "get",
            "/sts/tokens/history",
            data={"limit": limit},
        )
