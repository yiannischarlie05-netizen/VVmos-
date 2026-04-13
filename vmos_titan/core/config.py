"""
VMOS Cloud API Configuration
Centralized configuration, safety guards, and operational settings for VMOS Cloud API client.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum


class DeviceStatus(Enum):
    """Device status codes from VMOS Cloud API."""
    RUNNING = 10
    BOOTING = 11
    RESETTING = 12
    STOPPED = 14
    BRICKED = 15


class ErrorCode(Enum):
    """VMOS Cloud API error codes."""
    RATE_LIMIT = 110031
    TIMEOUT = 110101
    FILE_TRANSFER = 110201
    AUTH_FAIL = 111001
    PARAM_ERROR = 1104
    NOT_FOUND = 1105
    INVALID_STATE = 1106
    OPERATION_FAILED = 1107


class RetryStrategy(Enum):
    """Retry strategy types."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    NONE = "none"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration for API resilience."""
    enabled: bool = True
    failure_threshold: int = 5  # Failures before opening circuit
    success_threshold: int = 2  # Successes before closing circuit
    timeout: float = 60.0  # Seconds before half-open
    exponential_base: float = 2.0  # Backoff multiplier


@dataclass
class RetryConfig:
    """Retry configuration for failed requests."""
    max_retries: int = 3
    initial_delay: float = 3.0  # seconds
    max_delay: float = 30.0  # seconds
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    rate_limit_backoff: float = 5.0  # Additional backoff for rate limits


@dataclass
class APIConfig:
    """
    Central configuration for VMOS Cloud API client.
    Controls operational modes, safety guards, and resilience settings.
    """
    
    # ==================== Credentials ====================
    access_key: Optional[str] = field(default=None)
    secret_key: Optional[str] = field(default=None)
    endpoint: str = "https://api.vmoscloud.com"
    
    # ==================== Safety Guards ====================
    # These environment-based guards control dangerous operations
    allow_restart: bool = field(default_factory=lambda: os.getenv("VMOS_ALLOW_RESTART", "false").lower() == "true")
    allow_template_import_pad: bool = field(default_factory=lambda: os.getenv("VMOS_ALLOW_TEMPLATE_IMPORT_PAD", "false").lower() == "true")
    
    # Additional safety guards
    max_concurrent_devices: int = 100
    max_file_upload_mb: int = 500
    max_batch_operations: int = 50
    
    # ==================== Resilience ====================
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    circuit_breaker_config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    request_timeout: float = 30.0  # seconds
    connection_pool_size: int = 20
    
    # ==================== Operational Settings ====================
    enable_request_tracing: bool = True
    enable_metrics: bool = True
    enable_debug_logging: bool = field(default_factory=lambda: os.getenv("VMOS_DEBUG", "false").lower() == "true")
    
    # Rate limiting settings (3-5s spacing per docs + backoff on 110031)
    min_request_interval: float = 3.0  # minimum seconds between requests
    max_requests_per_minute: int = 15  # typical rate limit
    
    # Device operation constraints
    max_property_batch_size: int = 50
    max_screenshot_batch: int = 10
    max_adb_command_length: int = 4096
    
    # ==================== Forbidden Operations ====================
    # These operations are NEVER safe and should not be called
    FORBIDDEN_OPS: Dict[str, str] = field(default_factory=lambda: {
        "replacePad": "Causes device reboot and state loss",
        "updatePadAndroidProp": "Causes device reboot, creates permanent Status 11 brick",
        "pm_disable_user_gesture": "Disables rtcgesture permanently, causes Status 11 brick",
        "chmod_sysblock": "Cascading device crashes, permanent damage",
        "mount_tmpfs_system": "Destroys package manager, unrecoverable",
    })
    
    # ==================== Safe Operations ====================
    # These operations are safe and don't trigger restarts
    SAFE_OPS: Dict[str, str] = field(default_factory=lambda: {
        "updatePadProperties": "Safe property update, no restart",
        "write_to_dev_sc": "Write to /dev/.sc persistent tmpfs overlay",
    })
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create APIConfig from environment variables."""
        return cls(
            access_key=os.getenv("VMOS_ACCESS_KEY"),
            secret_key=os.getenv("VMOS_SECRET_KEY"),
            endpoint=os.getenv("VMOS_ENDPOINT", "https://api.vmoscloud.com"),
            allow_restart=os.getenv("VMOS_ALLOW_RESTART", "false").lower() == "true",
            allow_template_import_pad=os.getenv("VMOS_ALLOW_TEMPLATE_IMPORT_PAD", "false").lower() == "true",
            enable_debug_logging=os.getenv("VMOS_DEBUG", "false").lower() == "true",
        )
    
    def validate(self) -> bool:
        """Validate configuration integrity."""
        if not self.access_key or not self.secret_key:
            return False
        if self.max_concurrent_devices <= 0:
            return False
        if self.request_timeout <= 0:
            return False
        return True
    
    def get_effective_timeout(self, operation: str) -> float:
        """Get timeout for specific operation, accounting for retries."""
        # Operations that might take longer
        if operation in ("uploadFile", "downloadFile", "restoreBackup"):
            return self.request_timeout * 3
        if operation in ("replacePad", "reset"):
            return self.request_timeout * 10
        return self.request_timeout
    
    def is_operation_allowed(self, operation: str) -> bool:
        """Check if operation is allowed (not in FORBIDDEN list)."""
        return operation not in self.FORBIDDEN_OPS
    
    def requires_guard(self, operation: str) -> bool:
        """Check if operation requires environment guard."""
        if operation == "restart":
            return not self.allow_restart
        if operation == "replacePad":
            return not self.allow_template_import_pad
        return False


# Global default config instance
_default_config: Optional[APIConfig] = None


def get_default_config() -> APIConfig:
    """Get or create the default API configuration."""
    global _default_config
    if _default_config is None:
        _default_config = APIConfig.from_env()
    return _default_config


def set_default_config(config: APIConfig) -> None:
    """Set the default API configuration."""
    global _default_config
    _default_config = config
