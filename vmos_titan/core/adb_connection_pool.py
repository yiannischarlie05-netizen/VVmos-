"""
Titan V13.0 — ADB Connection Pooling with Health Checks
Maintains persistent ADB connections with automatic reconnection and health monitoring.
"""

import logging
import shlex
import subprocess
import threading
import time
import os
from typing import Dict, List, Optional, Tuple

from .exponential_backoff import ExponentialBackoff
from .metrics import get_metrics
from .exceptions import ADBConnectionError

logger = logging.getLogger("titan.adb-connection-pool")


class ADBConnection:
    """Represents a persistent ADB connection with health checking."""
    
    def __init__(self, target: str, max_usage: int = 1000):
        self.target = target
        self.created_at = time.time()
        self.last_used = time.time()
        self.command_count = 0
        self.max_usage = max_usage
        self.is_connected = False
        self.consecutive_failures = 0
        self._lock = threading.Lock()
        self._backoff = ExponentialBackoff(
            initial_delay=1.0,
            max_delay=30.0,
            max_retries=3,
        )
        self._connect()
        # Record initial connection attempt metric
        try:
            metrics = get_metrics()
            # no-op here; metrics updated in execute/_connect flows
        except Exception:
            pass
    
    def _connect(self) -> bool:
        """Establish ADB connection with retry logic."""
        for attempt in range(3):
            try:
                result = subprocess.run(
                    ["adb", "connect", self.target],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self.is_connected = result.returncode == 0 and "connected" in result.stdout.lower()
                if self.is_connected:
                    logger.debug(f"Connected to {self.target}")
                    self.consecutive_failures = 0
                    try:
                        get_metrics().record_adb_reconnect()
                    except Exception:
                        pass
                    return True
                else:
                    logger.warning(f"Failed to connect to {self.target}: {result.stdout}")
            except Exception as e:
                logger.error(f"Connection error for {self.target}: {e}")
            
            if attempt < 2:
                delay = self._backoff.get_delay(attempt)
                time.sleep(delay)
        
        self.is_connected = False
        return False
    
    def health_check(self) -> bool:
        """Verify connection is alive with a simple echo test."""
        if not self.is_connected:
            return False
        
        try:
            result = subprocess.run(
                ["adb", "-s", self.target, "shell", "echo", "ping"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            healthy = result.returncode == 0 and "ping" in result.stdout
            if not healthy:
                logger.debug(f"Health check failed for {self.target}")
                self.consecutive_failures += 1
            else:
                self.consecutive_failures = 0
            return healthy
        except Exception as e:
            logger.debug(f"Health check error for {self.target}: {e}")
            self.consecutive_failures += 1
            return False
    
    def execute(self, cmd: str, timeout: int = 15, shell: bool = False) -> Tuple[bool, str]:
        """Execute command on connected device with automatic reconnection.
        
        Args:
            cmd: Command to execute (string or list)
            timeout: Command timeout in seconds
            shell: If True, run command through shell (allows pipes, redirects)
        
        Returns:
            (success, output_or_error)
        """
        with self._lock:
            # Check if we need to reconnect
            if not self.is_connected or self.consecutive_failures >= 3:
                logger.info(f"Reconnecting to {self.target}...")
                self._connect()
            
            # Check if connection exceeded max usage
            if self.command_count >= self.max_usage:
                logger.info(f"Connection {self.target} exceeded max usage, reconnecting...")
                self.disconnect()
                self._connect()
                self.command_count = 0
            
            if not self.is_connected:
                return False, "not_connected"
            
            try:
                if shell:
                    # Use shell=True for complex commands with pipes/redirections
                    full_cmd = f"adb -s {self.target} shell {cmd}"
                    result = subprocess.run(
                        full_cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        shell=True,
                    )
                else:
                    # Safe command execution with proper argument handling
                    if isinstance(cmd, str):
                        cmd_parts = shlex.split(cmd)
                    else:
                        cmd_parts = cmd
                    
                    result = subprocess.run(
                        ["adb", "-s", self.target, "shell"] + cmd_parts,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                    )
                
                self.last_used = time.time()
                self.command_count += 1
                
                # Track failures for reconnection logic
                success = result.returncode == 0
                if success:
                    self.consecutive_failures = 0
                else:
                    self.consecutive_failures += 1

                # Record metrics for adb command
                try:
                    get_metrics().record_adb_command(success=success)
                except Exception:
                    pass

                return success, result.stdout.strip()
                
            except subprocess.TimeoutExpired:
                logger.warning(f"Command timeout on {self.target}")
                self.consecutive_failures += 1
                return False, "timeout"
            except Exception as e:
                logger.error(f"Command error on {self.target}: {e}")
                self.consecutive_failures += 1
                return False, str(e)
    
    def execute_batch(self, commands: List[str], timeout: int = 15) -> List[Tuple[bool, str]]:
        """Execute multiple commands efficiently."""
        results = []
        for cmd in commands:
            results.append(self.execute(cmd, timeout))
        return results
    
    def disconnect(self):
        """Disconnect from device."""
        try:
            subprocess.run(
                ["adb", "disconnect", self.target],
                capture_output=True,
                timeout=5,
            )
            self.is_connected = False
            logger.debug(f"Disconnected from {self.target}")
        except Exception as e:
            logger.error(f"Disconnect error for {self.target}: {e}")
    
    def is_stale(self, max_age: int = 3600) -> bool:
        """Check if connection is stale (unused for too long)."""
        return time.time() - self.last_used > max_age
    
    def is_unhealthy(self, max_failures: int = 5) -> bool:
        """Check if connection has too many consecutive failures."""
        return self.consecutive_failures >= max_failures
    
    def get_stats(self) -> Dict:
        """Get connection statistics."""
        return {
            "target": self.target,
            "connected": self.is_connected,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "command_count": self.command_count,
            "max_usage": self.max_usage,
            "consecutive_failures": self.consecutive_failures,
            "uptime_seconds": time.time() - self.created_at,
        }


class ADBConnectionPool:
    """Pool of persistent ADB connections with health monitoring."""
    
    def __init__(self, max_connections: int = 16, max_age: int = 3600,
                 health_check_interval: int = 60, max_failures: int = 5):
        """
        Initialize connection pool.
        
        Args:
            max_connections: Maximum concurrent connections
            max_age: Maximum connection age in seconds
            health_check_interval: Seconds between health checks
            max_failures: Maximum consecutive failures before reconnecting
        """
        self.max_connections = max_connections
        self.max_age = max_age
        self.health_check_interval = health_check_interval
        self.max_failures = max_failures
        self._connections: Dict[str, ADBConnection] = {}
        self._lock = threading.RLock()
        self._cond = threading.Condition(self._lock)
        self._cleanup_thread = None
        self._health_check_thread = None
        self._watchdog_thread = None
        self._running = False
        self._last_health_check = 0
        # load env overrides
        try:
            self.max_connections = int(os.getenv("ADB_POOL_MAX_CONNECTIONS", str(self.max_connections)))
            self.health_check_interval = int(os.getenv("ADB_POOL_HEALTH_INTERVAL", str(self.health_check_interval)))
            self._cleanup_interval = int(os.getenv("ADB_POOL_CLEANUP_INTERVAL", "300"))
        except Exception:
            self._cleanup_interval = 300
    
    def start(self):
        """Start cleanup and health check threads."""
        if self._running:
            return
        
        self._running = True
        
        # Cleanup thread for stale connections
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="adb-pool-cleanup",
        )
        self._cleanup_thread.start()
        
        # Health check thread
        self._health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True,
            name="adb-pool-health",
        )
        self._health_check_thread.start()

        # Watchdog thread to attempt reconnections and evict hung connections
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
            name="adb-pool-watchdog",
        )
        self._watchdog_thread.start()
        
        logger.info(f"ADB connection pool started (max={self.max_connections})")
    
    def stop(self):
        """Stop threads and close all connections."""
        self._running = False
        
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5)
        if self._watchdog_thread:
            self._watchdog_thread.join(timeout=5)
        
        with self._lock:
            for conn in list(self._connections.values()):
                conn.disconnect()
            self._connections.clear()
        
        logger.info("ADB connection pool stopped")
    
    def get_connection(self, target: str, validate: bool = True) -> Optional[ADBConnection]:
        """Get or create connection to target with optional validation.
        
        Args:
            target: ADB target (e.g., "127.0.0.1:5555")
            validate: If True, run health check before returning connection
        
        Returns:
            ADBConnection or None if connection failed
        """
        with self._lock:
            # Return existing connection if available and healthy
            if target in self._connections:
                conn = self._connections[target]
                
                # Validate connection health if requested
                if validate and not conn.health_check():
                    logger.info(f"Connection to {target} unhealthy, reconnecting...")
                    conn._connect()
                
                if conn.is_connected:
                    return conn
                else:
                    # Remove dead connection
                    del self._connections[target]
            
            # Create new connection if under limit
            if len(self._connections) < self.max_connections:
                conn = ADBConnection(target)
                if conn.is_connected:
                    self._connections[target] = conn
                    # notify waiters
                    try:
                        self._cond.notify_all()
                    except Exception:
                        pass
                    return conn
                else:
                    logger.warning(f"Failed to create connection to {target}")
                    return None

            # Pool full: try waiting for a free slot for a short period
            wait_timeout = int(os.getenv("ADB_POOL_WAIT_TIMEOUT", "10"))
            start = time.time()
            while len(self._connections) >= self.max_connections:
                remaining = start + wait_timeout - time.time()
                if remaining <= 0:
                    logger.warning(f"Connection pool full ({self.max_connections}), timeout waiting for slot")
                    return None
                # Wait on condition variable
                self._cond.wait(timeout=remaining)

            # Retry creation after wait
            conn = ADBConnection(target)
            if conn.is_connected:
                self._connections[target] = conn
                try:
                    self._cond.notify_all()
                except Exception:
                    pass
                return conn
            logger.warning(f"Failed to create connection to {target} after wait")
            return None
    
    def execute(self, target: str, cmd: str, timeout: int = 15,
                shell: bool = False) -> Tuple[bool, str]:
        """Execute command on pooled connection.
        
        Args:
            target: ADB target
            cmd: Command to execute
            timeout: Command timeout
            shell: Use shell for complex commands
        
        Returns:
            (success, output_or_error)
        """
        conn = self.get_connection(target)
        if not conn:
            return False, "no_connection"
        
        return conn.execute(cmd, timeout, shell=shell)
    
    def execute_batch(self, target: str, commands: List[str],
                      timeout: int = 15) -> List[Tuple[bool, str]]:
        """Execute multiple commands on pooled connection."""
        conn = self.get_connection(target)
        if not conn:
            return [(False, "no_connection")] * len(commands)
        
        return conn.execute_batch(commands, timeout)
    
    def release_connection(self, target: str):
        """Release connection back to pool (no-op, connections are reused)."""
        pass
    
    def remove_connection(self, target: str):
        """Remove a connection from the pool (e.g., on device disconnect)."""
        with self._lock:
            if target in self._connections:
                conn = self._connections.pop(target)
                conn.disconnect()
                logger.info(f"Removed connection: {target}")
                try:
                    self._cond.notify_all()
                except Exception:
                    pass
    
    def _cleanup_loop(self):
        """Periodically clean up stale and unhealthy connections."""
        while self._running:
            try:
                time.sleep(self._cleanup_interval)
                self._cleanup_stale_connections()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def _cleanup_stale_connections(self):
        """Remove stale and unhealthy connections."""
        with self._lock:
            to_remove = []
            
            for target, conn in self._connections.items():
                # Remove stale connections
                if conn.is_stale(self.max_age):
                    to_remove.append((target, "stale"))
                # Remove unhealthy connections
                elif conn.is_unhealthy(self.max_failures):
                    to_remove.append((target, "unhealthy"))
            
            for target, reason in to_remove:
                conn = self._connections.pop(target)
                conn.disconnect()
                logger.info(f"Cleaned up {reason} connection: {target}")
    
    def _health_check_loop(self):
        """Periodically run health checks on all connections."""
        while self._running:
            try:
                time.sleep(self.health_check_interval)
                self._run_health_checks()
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    def _run_health_checks(self):
        """Run health checks on all connections."""
        with self._lock:
            connections = list(self._connections.items())
        
        # Run health checks outside the lock to avoid blocking
        unhealthy = []
        for target, conn in connections:
            if not conn.health_check():
                # Attempt to reconnect once before eviction
                try:
                    logger.info(f"Attempting reconnect for unhealthy connection: {target}")
                    reconnected = conn._connect()
                    if not reconnected:
                        unhealthy.append(target)
                except Exception:
                    unhealthy.append(target)

        # Remove unhealthy connections and notify waiters
        if unhealthy:
            with self._lock:
                for target in unhealthy:
                    if target in self._connections:
                        conn = self._connections.pop(target)
                        conn.disconnect()
                        logger.warning(f"Removed unhealthy connection: {target}")
                try:
                    self._cond.notify_all()
                except Exception:
                    pass
        
        self._last_health_check = time.time()
    
    def get_stats(self) -> Dict:
        """Get pool statistics."""
        with self._lock:
            stats = {
                "total_connections": len(self._connections),
                "max_connections": self.max_connections,
                "last_health_check": self._last_health_check,
                "connections": {},
            }
            
            for target, conn in self._connections.items():
                stats["connections"][target] = conn.get_stats()
            
            return stats


# Global connection pool
_pool: Optional[ADBConnectionPool] = None


def get_pool(max_connections: int = 16, max_age: int = 3600) -> ADBConnectionPool:
    """Get or create global connection pool.
    
    Args:
        max_connections: Maximum concurrent connections (only used on first call)
        max_age: Maximum connection age in seconds (only used on first call)
    """
    global _pool
    if _pool is None:
        _pool = ADBConnectionPool(
            max_connections=max_connections,
            max_age=max_age,
            health_check_interval=60,
            max_failures=5,
        )
        _pool.start()
    return _pool


def execute_pooled(target: str, cmd: str, timeout: int = 15,
                   shell: bool = False) -> Tuple[bool, str]:
    """Execute command using pooled connection.
    
    Args:
        target: ADB target (e.g., "127.0.0.1:5555")
        cmd: Command to execute
        timeout: Command timeout in seconds
        shell: Use shell for complex commands with pipes/redirections
    
    Returns:
        (success, output_or_error)
    """
    pool = get_pool()
    return pool.execute(target, cmd, timeout, shell=shell)


def execute_pooled_batch(target: str, commands: List[str],
                         timeout: int = 15) -> List[Tuple[bool, str]]:
    """Execute multiple commands using pooled connection.
    
    Args:
        target: ADB target
        commands: List of commands to execute
        timeout: Command timeout in seconds
    
    Returns:
        List of (success, output_or_error) tuples
    """
    pool = get_pool()
    return pool.execute_batch(target, commands, timeout)


def get_connection_stats() -> Dict:
    """Get connection pool statistics."""
    pool = get_pool()
    return pool.get_stats()


def remove_connection(target: str):
    """Remove a connection from the pool (e.g., on device disconnect)."""
    pool = get_pool()
    pool.remove_connection(target)
