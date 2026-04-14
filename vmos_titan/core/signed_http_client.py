"""
VMOS Cloud SignedHTTPClient — Base class for HMAC-SHA256 authenticated requests
Handles: HMAC signing, connection pooling, retry logic, error handling, request tracing
"""

import asyncio
import binascii
import datetime
import hashlib
import hmac
import json
import logging
import uuid
import time
from typing import Any, Optional, Dict, Tuple
from dataclasses import dataclass

import httpx

from .config import APIConfig, CircuitBreakerConfig, RetryConfig
from .exceptions import (
    VMOSAPIError, RateLimitError, TimeoutError as VMOSTimeoutError,
    FileTransferError, AuthenticationError, ParameterError,
    NotFoundError, InvalidStateError, OperationFailedError,
    ConnectionError as VMOSConnectionError, map_error_code_to_exception
)
from .circuit_breaker import CircuitBreaker, VMOSBackoffStrategy

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    method: str
    path: str
    attempt: int
    max_attempts: int
    http_status: Optional[int] = None
    api_code: Optional[int] = None
    api_msg: Optional[str] = None
    duration_ms: float = 0.0
    retrying: bool = False
    error: Optional[str] = None
    request_id: Optional[str] = None


class SignedHTTPClient:
    """
    Base HTTP client with HMAC-SHA256 signing, connection pooling, and resilience.
    
    Handles:
    - HMAC-SHA256 request signing per VMOS Cloud API spec
    - Connection pooling for performance
    - Exponential backoff with circuit breaker
    - Structured logging and metrics
    - Request tracing via x-request-id
    """
    
    # VMOS Cloud API signing constants
    _SERVICE = "armcloud-paas"
    _CONTENT_TYPE = "application/json;charset=UTF-8"
    _SIGNED_HEADERS = "content-type;host;x-content-sha256;x-date"
    _ALGORITHM = "HMAC-SHA256"
    
    # Retryable HTTP status codes
    _RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}
    
    # VMOS API error codes that should be retried
    _RETRYABLE_API_CODES = {110031, 2020, 500}
    
    def __init__(
        self,
        config: APIConfig,
        name: str = "vmos-api-client",
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        """
        Initialize SignedHTTPClient.
        
        Args:
            config: APIConfig instance with credentials and settings
            name: Client name (for logging and circuit breaker)
            circuit_breaker: Optional pre-configured CircuitBreaker
        """
        if not config.validate():
            raise ValueError("Invalid APIConfig: missing access_key or secret_key")
        
        self.config = config
        self.name = name
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            name=name,
            failure_threshold=config.circuit_breaker_config.failure_threshold,
            recovery_timeout=int(config.circuit_breaker_config.timeout),
        )
        
        # Connection pooling setup
        limits = httpx.Limits(
            max_connections=config.connection_pool_size,
            max_keepalive_connections=config.connection_pool_size // 2,
        )
        timeout = httpx.Timeout(
            config.request_timeout,
            connect=10.0,
        )
        self._client = httpx.AsyncClient(limits=limits, timeout=timeout)
        self._request_count = 0
    
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
            await self._client.aclose()
            self._client = None
    
    # ==================== HMAC-SHA256 Signing ====================
    
    @staticmethod
    def _sha256_hex(data: bytes) -> str:
        """Compute SHA256 hex digest."""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def _hmac_sha256(key: bytes, msg: str) -> bytes:
        """Compute HMAC-SHA256."""
        return hmac.new(key, msg.encode(), hashlib.sha256).digest()
    
    def _compute_signature(self, body_json: str, x_date: str) -> str:
        """
        Compute HMAC-SHA256 signature per VMOS Cloud API spec (v13.0).
        
        Args:
            body_json: JSON request body
            x_date: ISO 8601 timestamp (e.g., "20260410T141412Z")
        
        Returns:
            Hexadecimal signature string
        """
        x_content_sha256 = self._sha256_hex(body_json.encode())
        short_x_date = x_date[:8]  # YYYYMMDD
        host = self.config.endpoint.replace("https://", "").replace("http://", "")
        
        # Build canonical request
        canonical = (
            f"host:{host}\n"
            f"x-date:{x_date}\n"
            f"content-type:{self._CONTENT_TYPE}\n"
            f"signedHeaders:{self._SIGNED_HEADERS}\n"
            f"x-content-sha256:{x_content_sha256}"
        )
        
        credential_scope = f"{short_x_date}/{self._SERVICE}/request"
        hash_canonical = self._sha256_hex(canonical.encode())
        
        # Build string to sign
        string_to_sign = (
            f"{self._ALGORITHM}\n"
            f"{x_date}\n"
            f"{credential_scope}\n"
            f"{hash_canonical}"
        )
        
        # Derive signing key (3-level HMAC chain)
        k_date = self._hmac_sha256(self.config.secret_key.encode(), short_x_date)
        k_service = hmac.new(k_date, self._SERVICE.encode(), hashlib.sha256).digest()
        signing_key = hmac.new(k_service, b"request", hashlib.sha256).digest()
        
        # Compute final signature
        signature_bytes = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).digest()
        return binascii.hexlify(signature_bytes).decode()
    
    def _build_headers(self, body_json: str) -> Dict[str, str]:
        """
        Build signed request headers.
        
        Args:
            body_json: JSON request body
        
        Returns:
            Dictionary of HTTP headers with HMAC-SHA256 signature
        """
        x_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        host = self.config.endpoint.replace("https://", "").replace("http://", "")
        signature = self._compute_signature(body_json, x_date)
        
        return {
            "content-type": self._CONTENT_TYPE,
            "x-date": x_date,
            "x-host": host,
            "x-request-id": str(uuid.uuid4()),
            "authorization": (
                f"HMAC-SHA256 Credential={self.config.access_key}, "
                f"SignedHeaders={self._SIGNED_HEADERS}, "
                f"Signature={signature}"
            ),
        }
    
    # ==================== Request Execution ====================
    
    def _should_retry_response(
        self,
        response: Dict[str, Any],
        path: str,
        http_status: int = 200,
    ) -> bool:
        """
        Determine if response should be retried.
        
        Args:
            response: Parsed API response dict
            path: API endpoint path
            http_status: HTTP status code
        
        Returns:
            True if request should be retried
        """
        # Retry on transient HTTP errors
        if http_status in self._RETRYABLE_HTTP_STATUS:
            return True
        
        if not isinstance(response, dict):
            return False
        
        code = int(response.get("code", 0) or 0)
        msg = str(response.get("msg", "")).lower()
        
        # VMOS API error codes indicating transient failures
        if code in self._RETRYABLE_API_CODES:
            return True
        
        # Special handling for specific endpoints
        if code == 200 and response.get("data") is None:
            # Device offline or similar transient state
            if path.endswith(("/syncCmd", "/getStatus")):
                return True
        
        return False
    
    async def _execute_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        timeout_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute signed HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method (POST, GET, etc.)
            path: API endpoint path (e.g., "/api/pad/restart")
            data: Request body data (will be JSON encoded)
            timeout_sec: Request timeout in seconds
        
        Returns:
            Parsed API response dict
        
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            RateLimitError: On rate limit (110031)
            AuthenticationError: On auth failure (111001)
            And other VMOSAPIError subclasses
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_attempt():
            raise VMOSAPIError(
                message="Circuit breaker is OPEN - service temporarily unavailable",
                error_code=None,
                http_status=503,
            )
        
        body_json = json.dumps(data or {}, separators=(",", ":"), ensure_ascii=False)
        headers = self._build_headers(body_json)
        url = f"{self.config.endpoint.rstrip('/')}{path}"
        request_timeout = timeout_sec or self.config.request_timeout
        request_timeout = min(max(request_timeout, 5.0), 120.0)
        
        # Determine max attempts based on operation type
        max_attempts = self.config.retry_config.max_retries
        
        for attempt in range(max_attempts):
            self._request_count += 1
            start_time = time.time()
            
            try:
                # Make HTTP request
                response = await self._client.post(
                    url,
                    content=body_json,
                    headers=headers,
                    timeout=request_timeout,
                )
                
                duration_ms = (time.time() - start_time) * 1000
                parsed = response.json() if response.text else {}
                http_status = response.status_code
                api_code = parsed.get("code")
                api_msg = parsed.get("msg")
                request_id = headers.get("x-request-id")
                
                # Log metrics
                self._log_metrics(
                    method, path, attempt + 1, max_attempts,
                    http_status, api_code, api_msg, duration_ms,
                    request_id=request_id
                )
                
                # Check for retryable responses
                if self._should_retry_response(parsed, path, http_status):
                    if attempt < max_attempts - 1:
                        backoff = VMOSBackoffStrategy.get_backoff(
                            attempt,
                            error_code=api_code,
                            initial=self.config.retry_config.initial_delay,
                            base=self.config.retry_config.strategy.value if hasattr(self.config.retry_config.strategy, 'value') else 2.0,
                        )
                        await VMOSBackoffStrategy.wait_async(attempt, api_code)
                        self.circuit_breaker.record_failure(None, api_code)
                        continue
                
                # Success
                if api_code == 200 or http_status in (200, 201, 204):
                    self.circuit_breaker.record_success()
                    return parsed
                
                # API error - map to exception
                error = map_error_code_to_exception(
                    api_code or http_status,
                    api_msg or f"API returned code {api_code}",
                    http_status,
                    request_id=request_id,
                )
                self.circuit_breaker.record_failure(error, api_code)
                raise error
            
            except (httpx.TimeoutException, asyncio.TimeoutError) as e:
                duration_ms = (time.time() - start_time) * 1000
                self._log_metrics(
                    method, path, attempt + 1, max_attempts,
                    None, 110101, "Timeout", duration_ms,
                    retrying=(attempt < max_attempts - 1),
                    error=str(e),
                    request_id=headers.get("x-request-id")
                )
                
                if attempt < max_attempts - 1:
                    await VMOSBackoffStrategy.wait_async(attempt, 110101)
                    self.circuit_breaker.record_failure(e, 110101)
                    continue
                
                error = VMOSTimeoutError(f"Request timeout (attempt {attempt + 1})")
                self.circuit_breaker.record_failure(error, 110101)
                raise error
            
            except (httpx.RequestError, httpx.ConnectError) as e:
                duration_ms = (time.time() - start_time) * 1000
                self._log_metrics(
                    method, path, attempt + 1, max_attempts,
                    None, None, None, duration_ms,
                    retrying=(attempt < max_attempts - 1),
                    error=f"Connection error: {e}",
                    request_id=headers.get("x-request-id")
                )
                
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    self.circuit_breaker.record_failure(e, None)
                    continue
                
                error = VMOSConnectionError(f"Connection error: {e}")
                self.circuit_breaker.record_failure(error, None)
                raise error
            
            except VMOSAPIError as e:
                # Already mapped - just re-raise
                raise
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self._log_metrics(
                    method, path, attempt + 1, max_attempts,
                    None, None, None, duration_ms,
                    error=f"Unexpected error: {e}",
                    request_id=headers.get("x-request-id")
                )
                raise
        
        # All retries exhausted
        raise VMOSAPIError(message=f"Request failed after {max_attempts} attempts")
    
    def _log_metrics(
        self,
        method: str,
        path: str,
        attempt: int,
        max_attempts: int,
        http_status: Optional[int],
        api_code: Optional[int],
        api_msg: Optional[str],
        duration_ms: float,
        retrying: bool = False,
        error: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log structured metrics for request."""
        if not self.config.enable_metrics:
            return
        
        log_data = {
            "event": "vmos_api_request",
            "client": self.name,
            "method": method,
            "path": path,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "duration_ms": round(duration_ms, 2),
        }
        
        if request_id:
            log_data["request_id"] = request_id
        if http_status is not None:
            log_data["http_status"] = http_status
        if api_code is not None:
            log_data["api_code"] = api_code
        if api_msg:
            log_data["api_msg"] = api_msg[:200]
        if error:
            log_data["error"] = error[:200]
        if retrying:
            log_data["retrying"] = True
        
        msg = json.dumps(log_data)
        
        if error or retrying or (api_code and api_code != 200):
            logger.warning(msg)
        else:
            logger.debug(msg)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "name": self.name,
            "total_requests": self._request_count,
            "circuit_breaker": self.circuit_breaker.get_status(),
        }
