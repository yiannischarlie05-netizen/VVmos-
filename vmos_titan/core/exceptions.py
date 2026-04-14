"""
Titan V11.3 — Structured Exception Hierarchy
All Titan-specific exceptions inherit from TitanError for unified
catch-all handling and structured error reporting.
"""

from typing import Optional


class TitanError(Exception):
    """Base exception for all Titan errors."""

    def __init__(self, message: str = "", code: str = "TITAN_ERROR") -> None:
        self.code = code
        super().__init__(message)


# ═══════════════════════════════════════════════════════════════════════
# ADB / Device Errors
# ═══════════════════════════════════════════════════════════════════════

class ADBConnectionError(TitanError):
    """ADB connection failed after retries."""

    def __init__(self, device_id: str, port: int = 0, attempts: int = 1) -> None:
        self.device_id = device_id
        self.port = port
        self.attempts = attempts
        super().__init__(
            f"ADB connection to {device_id}:{port} failed after {attempts} attempts",
            code="ADB_CONNECTION_ERROR",
        )


class ADBCommandError(TitanError):
    """An ADB shell command failed."""

    def __init__(self, command: str, output: str = "", device_id: str = "") -> None:
        self.command = command
        self.output = output
        self.device_id = device_id
        super().__init__(
            f"ADB command failed on {device_id}: {command[:80]}",
            code="ADB_COMMAND_ERROR",
        )


class DeviceOfflineError(TitanError):
    """Device is offline or not responding."""

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        super().__init__(f"Device {device_id} is offline", code="DEVICE_OFFLINE")


class DeviceNotFoundError(TitanError):
    """Requested device not found in DeviceManager."""

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        super().__init__(f"Device not found: {device_id}", code="DEVICE_NOT_FOUND")


# ═══════════════════════════════════════════════════════════════════════
# Patch / Stealth Errors
# ═══════════════════════════════════════════════════════════════════════

class PatchPhaseError(TitanError):
    """A specific anomaly patcher phase failed."""

    def __init__(self, phase: str, vector: str = "", reason: str = "") -> None:
        self.phase = phase
        self.vector = vector
        msg = f"Phase {phase}"
        if vector:
            msg += f" vector {vector}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, code="PATCH_PHASE_ERROR")


class PatchPersistenceError(TitanError):
    """Patch persistence (reboot survival) failed."""

    def __init__(self, reason: str = "") -> None:
        super().__init__(
            f"Patch persistence failed: {reason}" if reason else "Patch persistence failed",
            code="PATCH_PERSISTENCE_ERROR",
        )


class ResetpropError(TitanError):
    """resetprop binary not available or failed."""

    def __init__(self, reason: str = "") -> None:
        super().__init__(
            f"resetprop error: {reason}" if reason else "resetprop not available",
            code="RESETPROP_ERROR",
        )


# ═══════════════════════════════════════════════════════════════════════
# Profile / Injection Errors
# ═══════════════════════════════════════════════════════════════════════

class ProfileForgeError(TitanError):
    """Profile generation/forging failed."""

    def __init__(self, reason: str = "", profile_id: str = "") -> None:
        self.profile_id = profile_id
        super().__init__(
            f"Profile forge failed ({profile_id}): {reason}" if profile_id else f"Profile forge failed: {reason}",
            code="PROFILE_FORGE_ERROR",
        )


class InjectionError(TitanError):
    """Profile injection into device failed."""

    def __init__(self, target: str = "", reason: str = "", device_id: str = "") -> None:
        self.target = target
        self.device_id = device_id
        msg = f"Injection failed"
        if target:
            msg += f" ({target})"
        if device_id:
            msg += f" on {device_id}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, code="INJECTION_ERROR")


# ═══════════════════════════════════════════════════════════════════════
# Wallet / Payment Errors
# ═══════════════════════════════════════════════════════════════════════

class WalletProvisionError(TitanError):
    """Wallet provisioning failed."""

    def __init__(self, reason: str = "", card_last4: str = "") -> None:
        self.card_last4 = card_last4
        msg = "Wallet provisioning failed"
        if card_last4:
            msg += f" (card *{card_last4})"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, code="WALLET_PROVISION_ERROR")


# ═══════════════════════════════════════════════════════════════════════
# GApps / Bootstrap Errors
# ═══════════════════════════════════════════════════════════════════════

class GAppsBootstrapError(TitanError):
    """GApps installation/bootstrap failed."""

    def __init__(self, reason: str = "", package: str = "") -> None:
        self.package = package
        msg = "GApps bootstrap failed"
        if package:
            msg += f" ({package})"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, code="GAPPS_BOOTSTRAP_ERROR")


# ═══════════════════════════════════════════════════════════════════════
# Workflow / Pipeline Errors
# ═══════════════════════════════════════════════════════════════════════

class WorkflowError(TitanError):
    """Workflow engine stage failed."""

    def __init__(self, stage: str = "", reason: str = "") -> None:
        self.stage = stage
        super().__init__(
            f"Workflow stage '{stage}' failed: {reason}" if stage else f"Workflow failed: {reason}",
            code="WORKFLOW_ERROR",
        )


class ProvisionError(TitanError):
    """Full provisioning pipeline failed."""

    def __init__(self, step: str = "", reason: str = "", job_id: str = "") -> None:
        self.step = step
        self.job_id = job_id
        msg = "Provisioning failed"
        if step:
            msg += f" at step '{step}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, code="PROVISION_ERROR")


# ═══════════════════════════════════════════════════════════════════════
# VMOS Cloud API Errors (Phase 1 Refactoring)
# ═══════════════════════════════════════════════════════════════════════

class VMOSAPIError(TitanError):
    """Base exception for all VMOS Cloud API errors."""

    def __init__(self, message: str = "", error_code: Optional[int] = None,
                 http_status: Optional[int] = None, request_id: Optional[str] = None) -> None:
        self.error_code = error_code
        self.http_status = http_status
        self.request_id = request_id
        super().__init__(message, code="VMOS_API_ERROR")


class RateLimitError(VMOSAPIError):
    """Rate limit exceeded (error code 110031). Exponential backoff: 3→5→10→30s."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[float] = None, 
                 error_code: int = 110031, http_status: int = 429, **kwargs) -> None:
        self.retry_after = retry_after or 3.0
        super().__init__(message, error_code=error_code, http_status=http_status, **kwargs)


class TimeoutError(VMOSAPIError):
    """Request timeout (error code 110101). Safe to retry, max 30s wait."""

    def __init__(self, message: str = "Request timeout", error_code: int = 110101, 
                 http_status: int = 504, **kwargs) -> None:
        super().__init__(message, error_code=error_code, http_status=http_status, **kwargs)


class FileTransferError(VMOSAPIError):
    """File transfer failed (error code 110201). May retry chunks."""

    def __init__(self, message: str = "File transfer failed", chunk_index: Optional[int] = None,
                 error_code: int = 110201, http_status: int = 503, **kwargs) -> None:
        self.chunk_index = chunk_index
        super().__init__(message, error_code=error_code, http_status=http_status, **kwargs)


class AuthenticationError(VMOSAPIError):
    """Authentication/authorization failed (error code 111001). Requires credential refresh."""

    def __init__(self, message: str = "Authentication failed", error_code: int = 111001,
                 http_status: int = 401, **kwargs) -> None:
        super().__init__(message, error_code=error_code, http_status=http_status, **kwargs)


class ParameterError(VMOSAPIError):
    """Invalid parameters (error code 1104). Request validation failed."""

    def __init__(self, message: str = "Invalid parameters", parameter: Optional[str] = None,
                 error_code: int = 1104, http_status: int = 400, **kwargs) -> None:
        self.parameter = parameter
        super().__init__(message, error_code=error_code, http_status=http_status, **kwargs)


class NotFoundError(VMOSAPIError):
    """Resource not found (error code 1105). Device/pad/resource doesn't exist."""

    def __init__(self, message: str = "Resource not found", resource_id: Optional[str] = None,
                 error_code: int = 1105, http_status: int = 404, **kwargs) -> None:
        self.resource_id = resource_id
        super().__init__(message, error_code=error_code, http_status=http_status, **kwargs)


class InvalidStateError(VMOSAPIError):
    """Invalid device/operation state (error code 1106). Device in wrong state."""

    def __init__(self, message: str = "Invalid state", current_state: Optional[str] = None,
                 required_state: Optional[str] = None, error_code: int = 1106,
                 http_status: int = 409, **kwargs) -> None:
        self.current_state = current_state
        self.required_state = required_state
        super().__init__(message, error_code=error_code, http_status=http_status, **kwargs)


class OperationFailedError(VMOSAPIError):
    """Operation failed on device (error code 1107). Generic device-level failure."""

    def __init__(self, message: str = "Operation failed", operation: Optional[str] = None,
                 error_code: int = 1107, http_status: int = 500, **kwargs) -> None:
        self.operation = operation
        super().__init__(message, error_code=error_code, http_status=http_status, **kwargs)


class CircuitBreakerOpenError(VMOSAPIError):
    """Circuit breaker open. Too many failures in quick succession."""

    def __init__(self, message: str = "Circuit breaker is open - service temporarily unavailable", **kwargs) -> None:
        super().__init__(message, error_code=None, http_status=503, **kwargs)


class ForbiddenOperationError(VMOSAPIError):
    """Operation is forbidden for safety reasons."""

    def __init__(self, message: str = "Operation is forbidden", operation: Optional[str] = None,
                 reason: Optional[str] = None, **kwargs) -> None:
        self.operation = operation
        self.reason = reason
        full_msg = message
        if reason:
            full_msg = f"{message}: {reason}"
        super().__init__(full_msg, error_code=None, http_status=403, **kwargs)


class GuardViolationError(VMOSAPIError):
    """Safety guard violation. Environment variable check failed."""

    def __init__(self, message: str = "Safety guard violation", guard_name: Optional[str] = None, **kwargs) -> None:
        self.guard_name = guard_name
        full_msg = message
        if guard_name:
            full_msg = f"{message}: set {guard_name}=true to enable"
        super().__init__(full_msg, error_code=None, http_status=403, **kwargs)


class ConnectionError(VMOSAPIError):
    """Connection/network error. Network unreachable or connection refused."""

    def __init__(self, message: str = "Connection error", **kwargs) -> None:
        super().__init__(message, error_code=None, http_status=None, **kwargs)


def map_error_code_to_exception(
    error_code: int,
    message: str,
    http_status: Optional[int] = None,
    **kwargs
) -> VMOSAPIError:
    """
    Map VMOS error code to appropriate exception type.
    
    Args:
        error_code: VMOS or HTTP error code
        message: Error message
        http_status: HTTP status code if available
        **kwargs: Additional exception parameters (request_id, etc.)
    
    Returns:
        Appropriate VMOSAPIError subclass instance
    """
    error_map = {
        110031: RateLimitError,
        110101: TimeoutError,
        110201: FileTransferError,
        111001: AuthenticationError,
        1104: ParameterError,
        1105: NotFoundError,
        1106: InvalidStateError,
        1107: OperationFailedError,
    }
    
    exception_class = error_map.get(error_code, VMOSAPIError)
    return exception_class(
        message=message,
        error_code=error_code,
        http_status=http_status,
        **kwargs
    )
