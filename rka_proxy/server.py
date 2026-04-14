"""
RKA Proxy Server — Remote Keybox Attestation Service

FastAPI server that forwards Play Integrity attestation challenges to a pool
of physical Android devices for real TEE signing. This achieves STRONG/DEVICE
attestation level required for 100% NFC payment acceptance.

Gap P0 Implementation: RKA proxy Docker service for STRONG attestation.

Architecture:
    Physical Device Fleet (N devices with real TEE)
           ↓ USB/ADB
    RKA Proxy Server (this service)
           ↓ HTTP API
    Titan Pipeline (requests attestation)
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local imports
from device_pool import DevicePool, PhysicalDevice, DeviceStatus

logger = logging.getLogger(__name__)

app = FastAPI(
    title="RKA Proxy — Remote Keybox Attestation",
    description="Forward Play Integrity challenges to physical devices for real TEE attestation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global device pool
device_pool: Optional[DevicePool] = None


class AttestationLevel(str, Enum):
    """Play Integrity attestation levels."""
    MEETS_BASIC_INTEGRITY = "MEETS_BASIC_INTEGRITY"
    MEETS_DEVICE_INTEGRITY = "MEETS_DEVICE_INTEGRITY"
    MEETS_STRONG_INTEGRITY = "MEETS_STRONG_INTEGRITY"


class AttestationRequest(BaseModel):
    """Request for attestation signing."""
    nonce: str = Field(..., description="Base64-encoded nonce from Play Integrity API")
    package_name: str = Field(default="com.google.android.apps.walletnfcrel", description="Package to attest")
    request_id: Optional[str] = Field(default=None, description="Optional request tracking ID")


class AttestationResponse(BaseModel):
    """Response with signed attestation token."""
    request_id: str
    success: bool
    token: Optional[str] = None
    attestation_level: Optional[AttestationLevel] = None
    device_id: Optional[str] = None
    latency_ms: int
    error: Optional[str] = None


class KeyboxSignRequest(BaseModel):
    """Request for keybox signing operation."""
    challenge: str = Field(..., description="Base64-encoded challenge to sign")
    key_alias: str = Field(default="attestation_key", description="Key alias in device keystore")


class KeyboxSignResponse(BaseModel):
    """Response with signed challenge."""
    request_id: str
    success: bool
    signature: Optional[str] = None
    certificate_chain: Optional[List[str]] = None
    device_id: Optional[str] = None
    latency_ms: int
    error: Optional[str] = None


class DeviceInfo(BaseModel):
    """Information about a physical device."""
    device_id: str
    model: str
    manufacturer: str
    android_version: str
    security_patch: str
    status: str
    attestation_level: str
    last_used: Optional[float]
    success_count: int
    failure_count: int


class HealthResponse(BaseModel):
    """Service health status."""
    status: str
    uptime_seconds: float
    devices_total: int
    devices_available: int
    devices_busy: int
    devices_offline: int
    total_requests: int
    successful_requests: int
    average_latency_ms: float


# Metrics
class ServiceMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        self.total_latency_ms = 0
    
    def record_request(self, success: bool, latency_ms: int):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        self.total_latency_ms += latency_ms
    
    @property
    def average_latency(self) -> float:
        if self.successful_requests == 0:
            return 0
        return self.total_latency_ms / self.successful_requests

metrics = ServiceMetrics()


@app.on_event("startup")
async def startup():
    """Initialize device pool on startup."""
    global device_pool
    device_pool = DevicePool()
    await device_pool.discover_devices()
    logger.info(f"RKA Proxy started with {device_pool.available_count} devices")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    global device_pool
    if device_pool:
        await device_pool.shutdown()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Get service health status."""
    if not device_pool:
        raise HTTPException(status_code=503, detail="Device pool not initialized")
    
    stats = device_pool.get_stats()
    
    return HealthResponse(
        status="healthy" if stats["available"] > 0 else "degraded",
        uptime_seconds=time.time() - metrics.start_time,
        devices_total=stats["total"],
        devices_available=stats["available"],
        devices_busy=stats["busy"],
        devices_offline=stats["offline"],
        total_requests=metrics.total_requests,
        successful_requests=metrics.successful_requests,
        average_latency_ms=metrics.average_latency,
    )


@app.get("/devices", response_model=List[DeviceInfo])
async def list_devices():
    """List all physical devices in the pool."""
    if not device_pool:
        raise HTTPException(status_code=503, detail="Device pool not initialized")
    
    devices = device_pool.get_all_devices()
    return [
        DeviceInfo(
            device_id=d.device_id,
            model=d.model,
            manufacturer=d.manufacturer,
            android_version=d.android_version,
            security_patch=d.security_patch,
            status=d.status.value,
            attestation_level=d.attestation_level.value if d.attestation_level else "unknown",
            last_used=d.last_used,
            success_count=d.success_count,
            failure_count=d.failure_count,
        )
        for d in devices
    ]


@app.post("/devices/refresh")
async def refresh_devices():
    """Refresh device discovery."""
    if not device_pool:
        raise HTTPException(status_code=503, detail="Device pool not initialized")
    
    count = await device_pool.discover_devices()
    return {"discovered": count, "available": device_pool.available_count}


@app.post("/attestation/challenge", response_model=AttestationResponse)
async def attestation_challenge(request: AttestationRequest):
    """
    Forward Play Integrity challenge to a physical device for real TEE attestation.
    
    This is the main endpoint for achieving STRONG attestation level.
    """
    if not device_pool:
        raise HTTPException(status_code=503, detail="Device pool not initialized")
    
    request_id = request.request_id or str(uuid.uuid4())
    start_time = time.time()
    
    # Acquire a device from the pool
    device = await device_pool.acquire_device()
    if not device:
        return AttestationResponse(
            request_id=request_id,
            success=False,
            latency_ms=int((time.time() - start_time) * 1000),
            error="No devices available",
        )
    
    try:
        # Forward challenge to device
        result = await device.attest_integrity(
            nonce=request.nonce,
            package_name=request.package_name,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        metrics.record_request(result.success, latency_ms)
        
        return AttestationResponse(
            request_id=request_id,
            success=result.success,
            token=result.token,
            attestation_level=result.level if result.success else None,
            device_id=device.device_id,
            latency_ms=latency_ms,
            error=result.error if not result.success else None,
        )
        
    finally:
        # Release device back to pool
        await device_pool.release_device(device)


@app.post("/attestation/sign", response_model=KeyboxSignResponse)
async def keybox_sign(request: KeyboxSignRequest):
    """
    Sign a challenge using a physical device's hardware-backed keybox.
    
    Used for attestation operations that require direct keystore signing.
    """
    if not device_pool:
        raise HTTPException(status_code=503, detail="Device pool not initialized")
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    device = await device_pool.acquire_device()
    if not device:
        return KeyboxSignResponse(
            request_id=request_id,
            success=False,
            latency_ms=int((time.time() - start_time) * 1000),
            error="No devices available",
        )
    
    try:
        result = await device.sign_with_keybox(
            challenge=request.challenge,
            key_alias=request.key_alias,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        metrics.record_request(result.success, latency_ms)
        
        return KeyboxSignResponse(
            request_id=request_id,
            success=result.success,
            signature=result.signature,
            certificate_chain=result.cert_chain,
            device_id=device.device_id,
            latency_ms=latency_ms,
            error=result.error if not result.success else None,
        )
        
    finally:
        await device_pool.release_device(device)


@app.post("/attestation/batch")
async def attestation_batch(requests: List[AttestationRequest]):
    """
    Process multiple attestation requests in parallel.
    
    Useful for batch device provisioning.
    """
    if not device_pool:
        raise HTTPException(status_code=503, detail="Device pool not initialized")
    
    tasks = [attestation_challenge(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    responses = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            responses.append(AttestationResponse(
                request_id=requests[i].request_id or str(uuid.uuid4()),
                success=False,
                latency_ms=0,
                error=str(result),
            ))
        else:
            responses.append(result)
    
    return responses


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
