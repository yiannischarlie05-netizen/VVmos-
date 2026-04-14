"""VMOS Cloud API - Email Module

Manages email verification services for device provisioning and account
setup operations.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from vmos_titan.api.base import APIModule


@dataclass
class EmailVerification:
    """Email verification record"""
    email: str
    verified: bool
    verified_at: Optional[datetime]
    verification_code: Optional[str]
    expires_at: Optional[datetime]


class EmailAPI(APIModule):
    """Email verification and management"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "email"

    async def request_verification(
        self,
        email: str,
    ) -> Dict[str, Any]:
        """Request email verification code
        
        Args:
            email: Email address to verify
            
        Returns:
            Verification request status
        """
        return await self._call(
            "post",
            "/email/verify/request",
            data={"email": email},
        )

    async def verify_email(
        self,
        email: str,
        code: str,
    ) -> Dict[str, Any]:
        """Verify email with code
        
        Args:
            email: Email address
            code: Verification code received
            
        Returns:
            Verification status
        """
        return await self._call(
            "post",
            "/email/verify",
            data={
                "email": email,
                "code": code,
            },
        )

    async def get_verification_status(
        self,
        email: str,
    ) -> Dict[str, Any]:
        """Get email verification status
        
        Args:
            email: Email address
            
        Returns:
            Verification status and metadata
        """
        return await self._call(
            "get",
            "/email/verify/status",
            data={"email": email},
        )

    async def resend_verification_code(
        self,
        email: str,
    ) -> Dict[str, Any]:
        """Resend verification code to email
        
        Args:
            email: Email address
            
        Returns:
            Resend status
        """
        return await self._call(
            "post",
            "/email/verify/resend",
            data={"email": email},
        )

    async def list_verified_emails(
        self,
    ) -> Dict[str, Any]:
        """List all verified emails
        
        Returns:
            List of verified email addresses
        """
        return await self._call(
            "get",
            "/email/verified",
        )

    async def remove_verified_email(
        self,
        email: str,
    ) -> Dict[str, Any]:
        """Remove verified email from account
        
        Args:
            email: Email to remove
            
        Returns:
            Removal status
        """
        return await self._call(
            "delete",
            "/email/verified",
            data={"email": email},
        )

    async def set_primary_email(
        self,
        email: str,
    ) -> Dict[str, Any]:
        """Set primary email address
        
        Args:
            email: Email to set as primary
            
        Returns:
            Update status
        """
        return await self._call(
            "post",
            "/email/primary",
            data={"email": email},
        )

    async def get_primary_email(
        self,
    ) -> Dict[str, Any]:
        """Get primary email address
        
        Returns:
            Primary email information
        """
        return await self._call(
            "get",
            "/email/primary",
        )

    async def send_recovery_email(
        self,
        email: str,
    ) -> Dict[str, Any]:
        """Send account recovery email
        
        Args:
            email: Email to send recovery to
            
        Returns:
            Send status
        """
        return await self._call(
            "post",
            "/email/recovery/send",
            data={"email": email},
        )

    async def verify_recovery_token(
        self,
        token: str,
    ) -> Dict[str, Any]:
        """Verify recovery token from email
        
        Args:
            token: Recovery token
            
        Returns:
            Token verification status
        """
        return await self._call(
            "post",
            "/email/recovery/verify",
            data={"token": token},
        )

    async def get_email_history(
        self,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get email verification history
        
        Args:
            limit: Maximum records to return
            
        Returns:
            Email history records
        """
        return await self._call(
            "get",
            "/email/history",
            data={"limit": limit},
        )

    async def configure_email_notifications(
        self,
        settings: Dict[str, bool],
    ) -> Dict[str, Any]:
        """Configure email notification preferences
        
        Args:
            settings: Notification type -> enabled mapping
            
        Returns:
            Configuration status
        """
        return await self._call(
            "post",
            "/email/notifications/config",
            data=settings,
        )

    async def get_email_notification_settings(
        self,
    ) -> Dict[str, Any]:
        """Get email notification settings
        
        Returns:
            Current notification preferences
        """
        return await self._call(
            "get",
            "/email/notifications/config",
        )

    async def validate_email_format(
        self,
        email: str,
    ) -> Dict[str, Any]:
        """Validate email format
        
        Args:
            email: Email to validate
            
        Returns:
            Validation result
        """
        return await self._call(
            "post",
            "/email/validate",
            data={"email": email},
        )
