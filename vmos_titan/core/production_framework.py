"""
Production Framework — Unified Error Handling, Rate Limiting, and Telemetry
============================================================================
Central infrastructure for production-grade VMOS-Titan operations.

Components:
1. RetryStrategy - Exponential backoff with jitter
2. CircuitBreaker - Failure threshold management
3. RateLimiter - VMOS Cloud API compliant (3.5s intervals)
4. HealthMonitor - Phase-level metrics
5. TelemetryCollector - Structured logging

Usage:
    from vmos_titan.core.production_framework import (
        ProductionContext, RetryStrategy, CircuitBreaker, RateLimiter
    )
    
    async with ProductionContext("genesis_pipeline") as ctx:
        result = await ctx.execute_with_retry(
            phase_function,
            retry_strategy=RetryStrategy.EXPONENTIAL,
            circuit_breaker=True
        )
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger("titan.production")


# ═══════════════════════════════════════════════════════════════════════════
# RETRY STRATEGY
# ═══════════════════════════════════════════════════════════════════════════

class RetryStrategy(Enum):
    """Retry strategies for failed operations."""
    NONE = auto()
    LINEAR = auto()
    EXPONENTIAL = auto()
    FIBONACCI = auto()


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_attempts: int = 5
    base_delay_sec: float = 1.0
    max_delay_sec: float = 60.0
    jitter_factor: float = 0.2
    retryable_exceptions: tuple = (Exception,)
    non_retryable_exceptions: tuple = ()

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        if self.strategy == RetryStrategy.NONE:
            return 0
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay_sec * attempt
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay_sec * (2 ** (attempt - 1))
        elif self.strategy == RetryStrategy.FIBONACCI:
            delay = self.base_delay_sec * self._fib(attempt)
        else:
            delay = self.base_delay_sec

        # Apply jitter
        jitter = delay * self.jitter_factor * random.uniform(-1, 1)
        delay = max(0, delay + jitter)
        
        return min(delay, self.max_delay_sec)

    @staticmethod
    def _fib(n: int) -> int:
        """Calculate nth Fibonacci number."""
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b


async def retry_async(
    func: Callable,
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> Any:
    """Execute async function with retry logic."""
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except config.non_retryable_exceptions as e:
            logger.error(f"Non-retryable error: {e}")
            raise
        except config.retryable_exceptions as e:
            last_exception = e
            if attempt < config.max_attempts:
                delay = config.calculate_delay(attempt)
                logger.warning(f"Attempt {attempt}/{config.max_attempts} failed: {e}. "
                             f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {config.max_attempts} attempts failed: {e}")
    
    raise last_exception


def retry_sync(
    func: Callable,
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> Any:
    """Execute sync function with retry logic."""
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except config.non_retryable_exceptions as e:
            logger.error(f"Non-retryable error: {e}")
            raise
        except config.retryable_exceptions as e:
            last_exception = e
            if attempt < config.max_attempts:
                delay = config.calculate_delay(attempt)
                logger.warning(f"Attempt {attempt}/{config.max_attempts} failed: {e}. "
                             f"Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {config.max_attempts} attempts failed: {e}")
    
    raise last_exception


# ═══════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════════════════════

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for preventing cascade failures.
    
    Usage:
        cb = CircuitBreaker(name="vmos_api", failure_threshold=5)
        
        async with cb.protect():
            result = await vmos_api_call()
    """
    name: str
    failure_threshold: int = 5
    recovery_timeout_sec: float = 30.0
    half_open_max_calls: int = 3
    
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0, init=False)
    _half_open_calls: int = field(default=0, init=False)

    @property
    def state(self) -> CircuitState:
        """Get current state, checking for recovery."""
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout_sec:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
        return self._state

    def record_success(self):
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info(f"Circuit '{self.name}' recovered to CLOSED")
        elif self._state == CircuitState.CLOSED:
            self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self, error: Exception):
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit '{self.name}' re-opened after half-open failure")
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit '{self.name}' opened after {self._failure_count} failures")

    @asynccontextmanager
    async def protect(self):
        """Context manager for circuit-protected operations."""
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(f"Circuit '{self.name}' is OPEN")
        
        try:
            yield
            self.record_success()
        except Exception as e:
            self.record_failure(e)
            raise


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class RateLimiter:
    """
    Rate limiter for VMOS Cloud API compliance.
    
    VMOS Cloud requires minimum 3-3.5 seconds between API calls.
    This limiter enforces that constraint globally.
    
    Usage:
        limiter = RateLimiter(min_interval_sec=3.5)
        
        async with limiter.acquire():
            await vmos_api_call()
    """
    min_interval_sec: float = 3.5
    burst_capacity: int = 3
    
    _last_call_time: float = field(default=0, init=False)
    _burst_tokens: int = field(default=3, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    async def acquire(self):
        """Acquire permission to make an API call."""
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_call_time
            
            # Replenish burst tokens
            tokens_to_add = int(elapsed / self.min_interval_sec)
            self._burst_tokens = min(self.burst_capacity, self._burst_tokens + tokens_to_add)
            
            if self._burst_tokens > 0:
                self._burst_tokens -= 1
                self._last_call_time = now
                return
            
            # Must wait
            wait_time = self.min_interval_sec - elapsed
            if wait_time > 0:
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            
            self._last_call_time = time.time()

    @asynccontextmanager
    async def limit(self):
        """Context manager for rate-limited operations."""
        await self.acquire()
        yield


# Global rate limiter for VMOS Cloud API
VMOS_RATE_LIMITER = RateLimiter(min_interval_sec=3.5, burst_capacity=3)


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH MONITOR
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PhaseMetrics:
    """Metrics for a single phase execution."""
    phase_name: str
    started_at: float = 0
    completed_at: float = 0
    success: bool = False
    error: Optional[str] = None
    retry_count: int = 0
    sub_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_sec(self) -> float:
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return 0


class HealthMonitor:
    """
    Monitor health of pipeline execution.
    
    Tracks:
    - Phase completion status
    - Timing metrics
    - Error rates
    - Resource utilization
    """
    
    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self.phases: Dict[str, PhaseMetrics] = {}
        self.started_at = time.time()
        self.completed_at: Optional[float] = None
        self._current_phase: Optional[str] = None

    def start_phase(self, phase_name: str) -> PhaseMetrics:
        """Start tracking a phase."""
        metrics = PhaseMetrics(phase_name=phase_name, started_at=time.time())
        self.phases[phase_name] = metrics
        self._current_phase = phase_name
        logger.info(f"[{self.pipeline_name}] Starting phase: {phase_name}")
        return metrics

    def complete_phase(self, phase_name: str, success: bool = True, 
                      error: Optional[str] = None, **sub_metrics):
        """Complete a phase."""
        if phase_name in self.phases:
            metrics = self.phases[phase_name]
            metrics.completed_at = time.time()
            metrics.success = success
            metrics.error = error
            metrics.sub_metrics.update(sub_metrics)
            
            status = "✓" if success else "✗"
            logger.info(f"[{self.pipeline_name}] Phase {phase_name} {status} "
                       f"({metrics.duration_sec:.1f}s)")
        
        if self._current_phase == phase_name:
            self._current_phase = None

    def finalize(self) -> Dict[str, Any]:
        """Finalize monitoring and return summary."""
        self.completed_at = time.time()
        
        total_phases = len(self.phases)
        successful = sum(1 for p in self.phases.values() if p.success)
        failed = total_phases - successful
        
        summary = {
            "pipeline": self.pipeline_name,
            "started_at": datetime.fromtimestamp(self.started_at).isoformat(),
            "completed_at": datetime.fromtimestamp(self.completed_at).isoformat(),
            "total_duration_sec": self.completed_at - self.started_at,
            "phases_total": total_phases,
            "phases_successful": successful,
            "phases_failed": failed,
            "success_rate": successful / total_phases if total_phases > 0 else 0,
            "phases": {
                name: {
                    "success": m.success,
                    "duration_sec": m.duration_sec,
                    "error": m.error,
                    "retries": m.retry_count,
                    **m.sub_metrics
                }
                for name, m in self.phases.items()
            }
        }
        
        return summary


# ═══════════════════════════════════════════════════════════════════════════
# TELEMETRY COLLECTOR
# ═══════════════════════════════════════════════════════════════════════════

class TelemetryCollector:
    """
    Structured telemetry collection for production monitoring.
    
    Outputs JSON-formatted logs suitable for:
    - ELK stack
    - CloudWatch Logs
    - Datadog
    - Custom dashboards
    """
    
    def __init__(self, service_name: str = "vmos-titan"):
        self.service_name = service_name
        self._events: List[Dict[str, Any]] = []

    def emit(self, event_type: str, **data):
        """Emit a telemetry event."""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "event_type": event_type,
            **data
        }
        self._events.append(event)
        
        # Also log as JSON for structured logging
        logger.info(json.dumps(event))

    def emit_phase_start(self, phase: str, device_id: str = ""):
        """Emit phase start event."""
        self.emit("phase_start", phase=phase, device_id=device_id)

    def emit_phase_complete(self, phase: str, success: bool, duration_sec: float,
                           device_id: str = "", **metrics):
        """Emit phase completion event."""
        self.emit("phase_complete", phase=phase, success=success,
                 duration_sec=duration_sec, device_id=device_id, **metrics)

    def emit_error(self, error_type: str, message: str, phase: str = "",
                  device_id: str = "", recoverable: bool = True):
        """Emit error event."""
        self.emit("error", error_type=error_type, message=message,
                 phase=phase, device_id=device_id, recoverable=recoverable)

    def emit_metric(self, metric_name: str, value: float, unit: str = "",
                   device_id: str = "", **tags):
        """Emit a metric value."""
        self.emit("metric", metric_name=metric_name, value=value,
                 unit=unit, device_id=device_id, tags=tags)

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all collected events."""
        return self._events.copy()

    def flush(self) -> List[Dict[str, Any]]:
        """Flush and return all events."""
        events = self._events.copy()
        self._events.clear()
        return events


# Global telemetry collector
TELEMETRY = TelemetryCollector()


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCTION CONTEXT
# ═══════════════════════════════════════════════════════════════════════════

class ProductionContext:
    """
    Unified production context for pipeline execution.
    
    Combines:
    - Retry logic
    - Circuit breaker
    - Rate limiting
    - Health monitoring
    - Telemetry
    
    Usage:
        async with ProductionContext("genesis_pipeline", device_id="ACP...") as ctx:
            await ctx.execute_phase("stealth_patch", stealth_patch_func)
            await ctx.execute_phase("wallet_inject", wallet_inject_func)
            
            summary = ctx.get_summary()
    """
    
    def __init__(self, pipeline_name: str, device_id: str = "",
                 enable_circuit_breaker: bool = True,
                 enable_rate_limiting: bool = True):
        self.pipeline_name = pipeline_name
        self.device_id = device_id
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_rate_limiting = enable_rate_limiting
        
        self.health = HealthMonitor(pipeline_name)
        self.telemetry = TELEMETRY
        self.circuit_breaker = CircuitBreaker(name=pipeline_name) if enable_circuit_breaker else None
        self.rate_limiter = VMOS_RATE_LIMITER if enable_rate_limiting else None
        
        self._retry_config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            max_attempts=3,
            base_delay_sec=2.0,
            max_delay_sec=30.0
        )

    async def __aenter__(self):
        self.telemetry.emit("pipeline_start", pipeline=self.pipeline_name,
                          device_id=self.device_id)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        summary = self.health.finalize()
        self.telemetry.emit("pipeline_complete", pipeline=self.pipeline_name,
                          device_id=self.device_id, success=exc_type is None,
                          **summary)
        return False

    async def execute_phase(
        self,
        phase_name: str,
        func: Callable,
        *args,
        retry: bool = True,
        critical: bool = False,
        **kwargs
    ) -> Any:
        """
        Execute a pipeline phase with full production infrastructure.
        
        Args:
            phase_name: Name of the phase
            func: Async function to execute
            *args: Arguments to pass to func
            retry: Enable retry logic
            critical: If True, failures abort the pipeline
            **kwargs: Keyword arguments to pass to func
        
        Returns:
            Result of func
        """
        metrics = self.health.start_phase(phase_name)
        self.telemetry.emit_phase_start(phase_name, device_id=self.device_id)
        
        try:
            # Rate limiting
            if self.rate_limiter:
                await self.rate_limiter.acquire()
            
            # Circuit breaker
            if self.circuit_breaker:
                if self.circuit_breaker.state == CircuitState.OPEN:
                    raise CircuitBreakerOpenError(f"Circuit open for {self.pipeline_name}")
            
            # Execute with optional retry
            if retry:
                result = await retry_async(func, self._retry_config, *args, **kwargs)
                metrics.retry_count = 0  # TODO: Track actual retries
            else:
                result = await func(*args, **kwargs)
            
            # Record success
            if self.circuit_breaker:
                self.circuit_breaker.record_success()
            
            self.health.complete_phase(phase_name, success=True)
            self.telemetry.emit_phase_complete(
                phase_name, success=True, duration_sec=metrics.duration_sec,
                device_id=self.device_id
            )
            
            return result
            
        except Exception as e:
            # Record failure
            if self.circuit_breaker:
                self.circuit_breaker.record_failure(e)
            
            self.health.complete_phase(phase_name, success=False, error=str(e))
            self.telemetry.emit_error(
                error_type=type(e).__name__,
                message=str(e),
                phase=phase_name,
                device_id=self.device_id,
                recoverable=not critical
            )
            
            if critical:
                raise
            
            logger.warning(f"Phase {phase_name} failed (non-critical): {e}")
            return None

    def get_summary(self) -> Dict[str, Any]:
        """Get current execution summary."""
        return self.health.finalize()


# ═══════════════════════════════════════════════════════════════════════════
# VMOS CLOUD API WRAPPER
# ═══════════════════════════════════════════════════════════════════════════

class VMOSCloudAPIWrapper:
    """
    Production-grade wrapper for VMOS Cloud API calls.
    
    Features:
    - Automatic rate limiting (3.5s intervals)
    - Retry on transient errors
    - Circuit breaker for cascading failure prevention
    - Structured telemetry
    
    Usage:
        api = VMOSCloudAPIWrapper(client)
        result = await api.sync_cmd(pad_code, "getprop ro.product.model")
    """
    
    # VMOS Cloud error codes
    ERROR_RATE_LIMIT = 110031
    ERROR_TIMEOUT = 110012
    ERROR_AUTH_FAIL = 111001
    ERROR_FILE_TRANSFER = 110201
    
    RETRYABLE_ERRORS = {ERROR_RATE_LIMIT, ERROR_TIMEOUT, ERROR_FILE_TRANSFER}
    
    def __init__(self, client: Any, enable_circuit_breaker: bool = True):
        self.client = client
        self.rate_limiter = VMOS_RATE_LIMITER
        self.circuit_breaker = CircuitBreaker(
            name="vmos_cloud_api",
            failure_threshold=5,
            recovery_timeout_sec=60.0
        ) if enable_circuit_breaker else None
        
        self._retry_config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            max_attempts=5,
            base_delay_sec=3.5,
            max_delay_sec=60.0
        )

    async def _execute(self, method_name: str, *args, **kwargs) -> Any:
        """Execute API method with production infrastructure."""
        await self.rate_limiter.acquire()
        
        if self.circuit_breaker:
            if self.circuit_breaker.state == CircuitState.OPEN:
                raise CircuitBreakerOpenError("VMOS Cloud API circuit is open")
        
        try:
            method = getattr(self.client, method_name)
            result = await method(*args, **kwargs)
            
            # Check for error codes in result
            if isinstance(result, dict):
                code = result.get("code", 0)
                if code in self.RETRYABLE_ERRORS:
                    raise VMOSCloudRetryableError(f"Error {code}: {result.get('msg', '')}")
            
            if self.circuit_breaker:
                self.circuit_breaker.record_success()
            
            return result
            
        except Exception as e:
            if self.circuit_breaker:
                self.circuit_breaker.record_failure(e)
            raise

    async def sync_cmd(self, pad_code: str, cmd: str, timeout: int = 30) -> str:
        """Execute sync command with retry."""
        async def _do():
            return await self._execute("sync_cmd", pad_code, cmd, timeout=timeout)
        
        return await retry_async(_do, self._retry_config)

    async def async_cmd(self, pad_codes: List[str], cmd: str) -> Dict:
        """Execute async command with retry."""
        async def _do():
            return await self._execute("async_adb_cmd", pad_codes, cmd)
        
        return await retry_async(_do, self._retry_config)

    async def upload_file(self, pad_code: str, local_path: str, 
                         remote_path: str) -> bool:
        """Upload file with retry."""
        async def _do():
            return await self._execute("upload_file_v3", pad_code, 
                                      local_path, remote_path)
        
        return await retry_async(_do, self._retry_config)


class VMOSCloudRetryableError(Exception):
    """Retryable VMOS Cloud API error."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Retry
    "RetryStrategy",
    "RetryConfig",
    "retry_async",
    "retry_sync",
    
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    
    # Rate Limiting
    "RateLimiter",
    "VMOS_RATE_LIMITER",
    
    # Monitoring
    "HealthMonitor",
    "PhaseMetrics",
    "TelemetryCollector",
    "TELEMETRY",
    
    # Production Context
    "ProductionContext",
    
    # VMOS Cloud Wrapper
    "VMOSCloudAPIWrapper",
    "VMOSCloudRetryableError",
]
