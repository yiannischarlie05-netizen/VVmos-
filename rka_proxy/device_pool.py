"""
DevicePool — Manage pool of physical Android devices for attestation.

Handles device discovery, health monitoring, and load balancing across
multiple physical devices connected via USB/ADB.
"""

import asyncio
import subprocess
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class DeviceStatus(Enum):
    """Status of a physical device."""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class AttestationLevel(Enum):
    """Play Integrity attestation levels."""
    UNKNOWN = "unknown"
    BASIC = "MEETS_BASIC_INTEGRITY"
    DEVICE = "MEETS_DEVICE_INTEGRITY"
    STRONG = "MEETS_STRONG_INTEGRITY"


@dataclass
class AttestationResult:
    """Result of an attestation operation."""
    success: bool
    token: Optional[str] = None
    level: Optional[AttestationLevel] = None
    error: Optional[str] = None


@dataclass
class SigningResult:
    """Result of a keybox signing operation."""
    success: bool
    signature: Optional[str] = None
    cert_chain: Optional[List[str]] = None
    error: Optional[str] = None


@dataclass
class PhysicalDevice:
    """Represents a physical Android device for attestation."""
    device_id: str
    model: str = "Unknown"
    manufacturer: str = "Unknown"
    android_version: str = "Unknown"
    security_patch: str = "Unknown"
    status: DeviceStatus = DeviceStatus.OFFLINE
    attestation_level: Optional[AttestationLevel] = None
    last_used: Optional[float] = None
    success_count: int = 0
    failure_count: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    async def _adb(self, cmd: str, timeout: int = 30) -> str:
        """Execute ADB command on this device."""
        try:
            full_cmd = f"adb -s {self.device_id} {cmd}"
            proc = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            return stdout.decode().strip()
        except asyncio.TimeoutError:
            logger.warning(f"ADB command timed out on {self.device_id}: {cmd}")
            return ""
        except Exception as e:
            logger.error(f"ADB command failed on {self.device_id}: {e}")
            return ""
    
    async def refresh_info(self) -> bool:
        """Refresh device information."""
        try:
            # Check device is online
            state = await self._adb("get-state")
            if state != "device":
                self.status = DeviceStatus.OFFLINE
                return False
            
            # Get device info
            self.model = await self._adb("shell getprop ro.product.model") or "Unknown"
            self.manufacturer = await self._adb("shell getprop ro.product.manufacturer") or "Unknown"
            self.android_version = await self._adb("shell getprop ro.build.version.release") or "Unknown"
            self.security_patch = await self._adb("shell getprop ro.build.version.security_patch") or "Unknown"
            
            # Check attestation capability
            keystore_check = await self._adb("shell ls /system/etc/security/keystore2 2>/dev/null")
            if keystore_check:
                self.attestation_level = AttestationLevel.STRONG
            else:
                self.attestation_level = AttestationLevel.DEVICE
            
            self.status = DeviceStatus.AVAILABLE
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh device info for {self.device_id}: {e}")
            self.status = DeviceStatus.ERROR
            return False
    
    async def attest_integrity(self, nonce: str, package_name: str) -> AttestationResult:
        """
        Perform Play Integrity attestation using this device's TEE.
        
        This uses the device's hardware-backed attestation to sign the nonce.
        """
        async with self._lock:
            self.status = DeviceStatus.BUSY
            self.last_used = time.time()
            
            try:
                # Push attestation helper script to device
                attest_script = f'''
                am broadcast -a com.titan.rka.ATTEST \
                    --es nonce "{nonce}" \
                    --es package "{package_name}" \
                    -n com.titan.rka/.AttestationReceiver 2>/dev/null
                '''
                
                # For real implementation, this would:
                # 1. Use PlayIntegrityManager on device
                # 2. Get the integrity token
                # 3. Return signed token
                
                # Simplified: Use keystore attestation directly
                result = await self._adb(
                    f'shell "echo {nonce} | keystore2_cli sign --key attestation_key"',
                    timeout=15
                )
                
                if result and "error" not in result.lower():
                    self.success_count += 1
                    self.status = DeviceStatus.AVAILABLE
                    return AttestationResult(
                        success=True,
                        token=result,
                        level=self.attestation_level or AttestationLevel.DEVICE,
                    )
                else:
                    # Fallback: use direct Play Integrity API call
                    # This requires a helper app installed on device
                    pi_result = await self._adb(
                        f'shell am start -a android.intent.action.VIEW '
                        f'-d "integrity://attest?nonce={nonce}&pkg={package_name}" '
                        f'--activity-clear-task',
                        timeout=20
                    )
                    
                    # Read result from shared location
                    token = await self._adb(
                        'shell cat /data/local/tmp/.titan_attestation_token 2>/dev/null',
                        timeout=5
                    )
                    
                    if token:
                        self.success_count += 1
                        self.status = DeviceStatus.AVAILABLE
                        return AttestationResult(
                            success=True,
                            token=token,
                            level=self.attestation_level or AttestationLevel.DEVICE,
                        )
                    
                    self.failure_count += 1
                    self.status = DeviceStatus.AVAILABLE
                    return AttestationResult(
                        success=False,
                        error="Attestation failed - no token returned",
                    )
                    
            except Exception as e:
                self.failure_count += 1
                self.status = DeviceStatus.ERROR
                return AttestationResult(
                    success=False,
                    error=str(e),
                )
    
    async def sign_with_keybox(self, challenge: str, key_alias: str) -> SigningResult:
        """
        Sign a challenge using the device's hardware keybox.
        """
        async with self._lock:
            self.status = DeviceStatus.BUSY
            self.last_used = time.time()
            
            try:
                # Use Android Keystore to sign
                # This requires root or a helper app
                sign_cmd = f'''
                keystore2_cli sign \
                    --key {key_alias} \
                    --algorithm ECDSA_P256_SHA256 \
                    --input "{challenge}"
                '''
                
                result = await self._adb(f'shell "{sign_cmd}"', timeout=15)
                
                if result and "error" not in result.lower():
                    # Get certificate chain
                    cert_cmd = f'keystore2_cli get-cert --key {key_alias}'
                    certs = await self._adb(f'shell "{cert_cmd}"', timeout=10)
                    cert_chain = certs.split("-----END CERTIFICATE-----") if certs else []
                    cert_chain = [c.strip() + "-----END CERTIFICATE-----" 
                                  for c in cert_chain if c.strip()]
                    
                    self.success_count += 1
                    self.status = DeviceStatus.AVAILABLE
                    return SigningResult(
                        success=True,
                        signature=result,
                        cert_chain=cert_chain if cert_chain else None,
                    )
                else:
                    self.failure_count += 1
                    self.status = DeviceStatus.AVAILABLE
                    return SigningResult(
                        success=False,
                        error=result or "Signing failed",
                    )
                    
            except Exception as e:
                self.failure_count += 1
                self.status = DeviceStatus.ERROR
                return SigningResult(
                    success=False,
                    error=str(e),
                )


class DevicePool:
    """
    Manage a pool of physical Android devices for attestation.
    
    Provides device discovery, health monitoring, and load balancing.
    """
    
    def __init__(self):
        self._devices: Dict[str, PhysicalDevice] = {}
        self._lock = asyncio.Lock()
        self._health_task: Optional[asyncio.Task] = None
    
    @property
    def available_count(self) -> int:
        """Number of available devices."""
        return sum(1 for d in self._devices.values() 
                   if d.status == DeviceStatus.AVAILABLE)
    
    def get_stats(self) -> Dict[str, int]:
        """Get device pool statistics."""
        stats = {
            "total": len(self._devices),
            "available": 0,
            "busy": 0,
            "offline": 0,
            "error": 0,
        }
        for device in self._devices.values():
            if device.status == DeviceStatus.AVAILABLE:
                stats["available"] += 1
            elif device.status == DeviceStatus.BUSY:
                stats["busy"] += 1
            elif device.status == DeviceStatus.OFFLINE:
                stats["offline"] += 1
            else:
                stats["error"] += 1
        return stats
    
    def get_all_devices(self) -> List[PhysicalDevice]:
        """Get all devices in pool."""
        return list(self._devices.values())
    
    async def discover_devices(self) -> int:
        """
        Discover physical devices connected via ADB.
        
        Returns:
            Number of devices discovered
        """
        async with self._lock:
            try:
                # Get list of connected devices
                proc = await asyncio.create_subprocess_shell(
                    "adb devices -l",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                output = stdout.decode()
                
                # Parse device list
                discovered = 0
                for line in output.strip().split('\n')[1:]:  # Skip header
                    if not line.strip():
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "device":
                        device_id = parts[0]
                        
                        # Skip emulators (we want physical devices only)
                        if device_id.startswith("emulator-"):
                            continue
                        
                        if device_id not in self._devices:
                            device = PhysicalDevice(device_id=device_id)
                            self._devices[device_id] = device
                            logger.info(f"Discovered new device: {device_id}")
                        
                        # Refresh device info
                        await self._devices[device_id].refresh_info()
                        discovered += 1
                
                # Mark missing devices as offline
                online_ids = set()
                for line in output.strip().split('\n')[1:]:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "device":
                        online_ids.add(parts[0])
                
                for device_id, device in self._devices.items():
                    if device_id not in online_ids:
                        device.status = DeviceStatus.OFFLINE
                
                return discovered
                
            except Exception as e:
                logger.error(f"Device discovery failed: {e}")
                return 0
    
    async def acquire_device(self) -> Optional[PhysicalDevice]:
        """
        Acquire an available device for attestation.
        
        Uses round-robin selection with preference for devices with
        higher success rates.
        
        Returns:
            PhysicalDevice if available, None otherwise
        """
        async with self._lock:
            # Sort by success rate and last used time
            available = [
                d for d in self._devices.values()
                if d.status == DeviceStatus.AVAILABLE
            ]
            
            if not available:
                return None
            
            # Prefer devices with better success rates
            def score(d: PhysicalDevice) -> float:
                total = d.success_count + d.failure_count
                if total == 0:
                    return 0.5
                return d.success_count / total
            
            available.sort(key=score, reverse=True)
            
            # Take the best available device
            device = available[0]
            device.status = DeviceStatus.BUSY
            return device
    
    async def release_device(self, device: PhysicalDevice):
        """Release a device back to the pool."""
        async with self._lock:
            if device.device_id in self._devices:
                if device.status == DeviceStatus.BUSY:
                    device.status = DeviceStatus.AVAILABLE
    
    async def start_health_monitor(self, interval: int = 60):
        """Start background health monitoring."""
        async def monitor():
            while True:
                await asyncio.sleep(interval)
                await self.discover_devices()
        
        self._health_task = asyncio.create_task(monitor())
    
    async def shutdown(self):
        """Shutdown the device pool."""
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
