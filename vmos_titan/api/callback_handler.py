"""
VMOS Cloud Callback Handler — Webhook receiver for async operation results.

This module provides FastAPI endpoints to receive callbacks from VMOS Cloud
for async operations like ADB commands, file uploads, app installations, etc.

Callback Types:
- Async ADB command completion
- File upload completion  
- App install/uninstall/start/stop/restart
- One-key new device completion
- Instance image upgrade
- Instance status changes
- Instance restart/reset completion

Usage:
    from callback_handler import create_callback_app, CallbackEventQueue
    
    app = create_callback_app()
    queue = CallbackEventQueue()
    
    # In your pipeline code:
    event = await queue.wait_for_event("adb_command", task_id="12345", timeout=30)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Awaitable
from enum import Enum
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CallbackType(str, Enum):
    """Types of VMOS Cloud callbacks."""
    ADB_COMMAND = "adb_command"
    FILE_UPLOAD = "file_upload"
    APP_INSTALL = "app_install"
    APP_UNINSTALL = "app_uninstall"
    APP_START = "app_start"
    APP_STOP = "app_stop"
    APP_RESTART = "app_restart"
    USER_IMAGE_UPLOAD = "user_image_upload"
    ONE_KEY_NEW_DEVICE = "one_key_new_device"
    IMAGE_UPGRADE = "image_upgrade"
    INSTANCE_STATUS = "instance_status"
    INSTANCE_RESTART = "instance_restart"
    INSTANCE_RESET = "instance_reset"


class TaskStatus(int, Enum):
    """Task execution status codes."""
    PENDING = 0
    EXECUTING = 1
    SUCCESS = 2
    FAILED = 3
    TIMEOUT = 4
    CANCELLED = 5


@dataclass
class CallbackEvent:
    """Represents a callback event from VMOS Cloud."""
    callback_type: CallbackType
    task_id: str
    pad_code: str
    status: TaskStatus
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    error_msg: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "callback_type": self.callback_type.value,
            "task_id": self.task_id,
            "pad_code": self.pad_code,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "error_msg": self.error_msg,
        }


# Pydantic models for callback payloads

class AdbCommandCallback(BaseModel):
    """Async ADB command callback payload."""
    taskId: str = Field(..., description="Task ID")
    padCode: str = Field(..., description="Instance pad code")
    taskStatus: int = Field(..., description="0=pending, 1=executing, 2=success, 3=failed")
    errorMsg: Optional[str] = Field(None, description="Command output or error")
    executeTime: Optional[int] = Field(None, description="Execution time in ms")


class FileUploadCallback(BaseModel):
    """File upload callback payload."""
    taskId: str
    padCode: str
    taskStatus: int
    fileUrl: Optional[str] = None
    filePath: Optional[str] = None
    errorMsg: Optional[str] = None


class AppOperationCallback(BaseModel):
    """App install/uninstall/start/stop callback payload."""
    taskId: str
    padCode: str
    taskStatus: int
    pkgName: Optional[str] = None
    appName: Optional[str] = None
    errorMsg: Optional[str] = None


class OneKeyNewDeviceCallback(BaseModel):
    """One-key new device callback payload."""
    taskId: str
    padCode: str
    taskStatus: int
    newPadCode: Optional[str] = None
    countryCode: Optional[str] = None
    errorMsg: Optional[str] = None


class InstanceStatusCallback(BaseModel):
    """Instance status change callback payload."""
    padCode: str
    oldStatus: int
    newStatus: int
    timestamp: int
    reason: Optional[str] = None


class ImageUpgradeCallback(BaseModel):
    """Instance image upgrade callback payload."""
    taskId: str
    padCode: str
    taskStatus: int
    imageId: Optional[str] = None
    errorMsg: Optional[str] = None


class CallbackEventQueue:
    """
    Thread-safe event queue for callback processing.
    
    Allows pipeline code to wait for specific callback events.
    """
    
    def __init__(self, max_events: int = 10000):
        self._events: Dict[str, CallbackEvent] = {}
        self._waiters: Dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()
        self._max_events = max_events
        self._event_handlers: List[Callable[[CallbackEvent], Awaitable[None]]] = []
    
    async def put(self, event: CallbackEvent):
        """Add an event to the queue."""
        async with self._lock:
            # Create composite key
            key = f"{event.callback_type.value}:{event.task_id}"
            
            # Store event
            self._events[key] = event
            
            # Notify waiters
            if key in self._waiters:
                self._waiters[key].set()
            
            # Prune old events if needed
            if len(self._events) > self._max_events:
                # Remove oldest 10%
                to_remove = sorted(self._events.items(), 
                                   key=lambda x: x[1].timestamp)[:self._max_events // 10]
                for k, _ in to_remove:
                    del self._events[k]
        
        # Call registered handlers
        for handler in self._event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    async def wait_for_event(self, callback_type: CallbackType | str,
                             task_id: str, timeout: float = 60.0) -> Optional[CallbackEvent]:
        """
        Wait for a specific callback event.
        
        Args:
            callback_type: Type of callback to wait for.
            task_id: Task ID to match.
            timeout: Maximum wait time in seconds.
            
        Returns:
            CallbackEvent if received, None if timeout.
        """
        if isinstance(callback_type, str):
            callback_type = CallbackType(callback_type)
        
        key = f"{callback_type.value}:{task_id}"
        
        # Check if event already exists
        async with self._lock:
            if key in self._events:
                return self._events.pop(key)
            
            # Create waiter
            self._waiters[key] = asyncio.Event()
        
        try:
            # Wait for event
            await asyncio.wait_for(self._waiters[key].wait(), timeout=timeout)
            
            async with self._lock:
                return self._events.pop(key, None)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for callback: {key}")
            return None
        finally:
            async with self._lock:
                self._waiters.pop(key, None)
    
    def register_handler(self, handler: Callable[[CallbackEvent], Awaitable[None]]):
        """Register a handler function to be called for all events."""
        self._event_handlers.append(handler)
    
    def get_recent_events(self, count: int = 100) -> List[CallbackEvent]:
        """Get most recent events."""
        sorted_events = sorted(self._events.values(), 
                               key=lambda x: x.timestamp, reverse=True)
        return sorted_events[:count]


# Global event queue (can be overridden)
_event_queue: Optional[CallbackEventQueue] = None


def get_event_queue() -> CallbackEventQueue:
    """Get or create the global event queue."""
    global _event_queue
    if _event_queue is None:
        _event_queue = CallbackEventQueue()
    return _event_queue


def create_callback_app(event_queue: Optional[CallbackEventQueue] = None) -> FastAPI:
    """
    Create FastAPI application for receiving VMOS Cloud callbacks.
    
    Args:
        event_queue: Optional event queue to use. If None, uses global queue.
        
    Returns:
        FastAPI application instance.
    """
    app = FastAPI(
        title="VMOS Cloud Callback Handler",
        description="Webhook receiver for VMOS Cloud async operation callbacks",
        version="1.0.0",
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    queue = event_queue or get_event_queue()
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "pending_events": len(queue._events),
        }
    
    @app.get("/events")
    async def list_recent_events(count: int = 50):
        """List recent callback events."""
        events = queue.get_recent_events(count)
        return {"events": [e.to_dict() for e in events]}
    
    @app.post("/callback/adb")
    async def handle_adb_callback(payload: AdbCommandCallback, background_tasks: BackgroundTasks):
        """Handle async ADB command completion callback."""
        event = CallbackEvent(
            callback_type=CallbackType.ADB_COMMAND,
            task_id=payload.taskId,
            pad_code=payload.padCode,
            status=TaskStatus(payload.taskStatus),
            timestamp=time.time(),
            data={"output": payload.errorMsg, "execute_time_ms": payload.executeTime},
            error_msg=payload.errorMsg if payload.taskStatus == 3 else None,
        )
        
        background_tasks.add_task(queue.put, event)
        logger.info(f"ADB callback: task={payload.taskId} status={payload.taskStatus}")
        
        return {"code": 200, "msg": "success"}
    
    @app.post("/callback/file_upload")
    async def handle_file_upload_callback(payload: FileUploadCallback, background_tasks: BackgroundTasks):
        """Handle file upload completion callback."""
        event = CallbackEvent(
            callback_type=CallbackType.FILE_UPLOAD,
            task_id=payload.taskId,
            pad_code=payload.padCode,
            status=TaskStatus(payload.taskStatus),
            timestamp=time.time(),
            data={"file_url": payload.fileUrl, "file_path": payload.filePath},
            error_msg=payload.errorMsg,
        )
        
        background_tasks.add_task(queue.put, event)
        logger.info(f"File upload callback: task={payload.taskId} status={payload.taskStatus}")
        
        return {"code": 200, "msg": "success"}
    
    @app.post("/callback/app_install")
    async def handle_app_install_callback(payload: AppOperationCallback, background_tasks: BackgroundTasks):
        """Handle app installation callback."""
        event = CallbackEvent(
            callback_type=CallbackType.APP_INSTALL,
            task_id=payload.taskId,
            pad_code=payload.padCode,
            status=TaskStatus(payload.taskStatus),
            timestamp=time.time(),
            data={"pkg_name": payload.pkgName, "app_name": payload.appName},
            error_msg=payload.errorMsg,
        )
        
        background_tasks.add_task(queue.put, event)
        logger.info(f"App install callback: task={payload.taskId} pkg={payload.pkgName}")
        
        return {"code": 200, "msg": "success"}
    
    @app.post("/callback/app_uninstall")
    async def handle_app_uninstall_callback(payload: AppOperationCallback, background_tasks: BackgroundTasks):
        """Handle app uninstallation callback."""
        event = CallbackEvent(
            callback_type=CallbackType.APP_UNINSTALL,
            task_id=payload.taskId,
            pad_code=payload.padCode,
            status=TaskStatus(payload.taskStatus),
            timestamp=time.time(),
            data={"pkg_name": payload.pkgName},
            error_msg=payload.errorMsg,
        )
        
        background_tasks.add_task(queue.put, event)
        return {"code": 200, "msg": "success"}
    
    @app.post("/callback/app_start")
    async def handle_app_start_callback(payload: AppOperationCallback, background_tasks: BackgroundTasks):
        """Handle app start callback."""
        event = CallbackEvent(
            callback_type=CallbackType.APP_START,
            task_id=payload.taskId,
            pad_code=payload.padCode,
            status=TaskStatus(payload.taskStatus),
            timestamp=time.time(),
            data={"pkg_name": payload.pkgName},
            error_msg=payload.errorMsg,
        )
        
        background_tasks.add_task(queue.put, event)
        return {"code": 200, "msg": "success"}
    
    @app.post("/callback/app_stop")
    async def handle_app_stop_callback(payload: AppOperationCallback, background_tasks: BackgroundTasks):
        """Handle app stop callback."""
        event = CallbackEvent(
            callback_type=CallbackType.APP_STOP,
            task_id=payload.taskId,
            pad_code=payload.padCode,
            status=TaskStatus(payload.taskStatus),
            timestamp=time.time(),
            data={"pkg_name": payload.pkgName},
            error_msg=payload.errorMsg,
        )
        
        background_tasks.add_task(queue.put, event)
        return {"code": 200, "msg": "success"}
    
    @app.post("/callback/app_restart")
    async def handle_app_restart_callback(payload: AppOperationCallback, background_tasks: BackgroundTasks):
        """Handle app restart callback."""
        event = CallbackEvent(
            callback_type=CallbackType.APP_RESTART,
            task_id=payload.taskId,
            pad_code=payload.padCode,
            status=TaskStatus(payload.taskStatus),
            timestamp=time.time(),
            data={"pkg_name": payload.pkgName},
            error_msg=payload.errorMsg,
        )
        
        background_tasks.add_task(queue.put, event)
        return {"code": 200, "msg": "success"}
    
    @app.post("/callback/one_key_new_device")
    async def handle_one_key_new_device_callback(payload: OneKeyNewDeviceCallback, background_tasks: BackgroundTasks):
        """Handle one-key new device callback."""
        event = CallbackEvent(
            callback_type=CallbackType.ONE_KEY_NEW_DEVICE,
            task_id=payload.taskId,
            pad_code=payload.padCode,
            status=TaskStatus(payload.taskStatus),
            timestamp=time.time(),
            data={"new_pad_code": payload.newPadCode, "country_code": payload.countryCode},
            error_msg=payload.errorMsg,
        )
        
        background_tasks.add_task(queue.put, event)
        logger.info(f"One-key new device callback: task={payload.taskId} new_pad={payload.newPadCode}")
        
        return {"code": 200, "msg": "success"}
    
    @app.post("/callback/image_upgrade")
    async def handle_image_upgrade_callback(payload: ImageUpgradeCallback, background_tasks: BackgroundTasks):
        """Handle instance image upgrade callback."""
        event = CallbackEvent(
            callback_type=CallbackType.IMAGE_UPGRADE,
            task_id=payload.taskId,
            pad_code=payload.padCode,
            status=TaskStatus(payload.taskStatus),
            timestamp=time.time(),
            data={"image_id": payload.imageId},
            error_msg=payload.errorMsg,
        )
        
        background_tasks.add_task(queue.put, event)
        logger.info(f"Image upgrade callback: task={payload.taskId} status={payload.taskStatus}")
        
        return {"code": 200, "msg": "success"}
    
    @app.post("/callback/instance_status")
    async def handle_instance_status_callback(payload: InstanceStatusCallback, background_tasks: BackgroundTasks):
        """Handle instance status change callback."""
        event = CallbackEvent(
            callback_type=CallbackType.INSTANCE_STATUS,
            task_id=f"status_{payload.padCode}_{payload.timestamp}",
            pad_code=payload.padCode,
            status=TaskStatus.SUCCESS,  # Status change itself is always "successful"
            timestamp=time.time(),
            data={
                "old_status": payload.oldStatus,
                "new_status": payload.newStatus,
                "reason": payload.reason,
            },
        )
        
        background_tasks.add_task(queue.put, event)
        logger.info(f"Instance status callback: pad={payload.padCode} {payload.oldStatus} -> {payload.newStatus}")
        
        return {"code": 200, "msg": "success"}
    
    @app.post("/callback/instance_restart")
    async def handle_instance_restart_callback(payload: AppOperationCallback, background_tasks: BackgroundTasks):
        """Handle instance restart/reset task callback."""
        event = CallbackEvent(
            callback_type=CallbackType.INSTANCE_RESTART,
            task_id=payload.taskId,
            pad_code=payload.padCode,
            status=TaskStatus(payload.taskStatus),
            timestamp=time.time(),
            error_msg=payload.errorMsg,
        )
        
        background_tasks.add_task(queue.put, event)
        return {"code": 200, "msg": "success"}
    
    # Generic callback endpoint for unknown types
    @app.post("/callback/{callback_type}")
    async def handle_generic_callback(callback_type: str, request: Request, background_tasks: BackgroundTasks):
        """Handle any callback type not explicitly defined."""
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        
        logger.warning(f"Unknown callback type: {callback_type}, payload: {payload}")
        
        # Try to create event from common fields
        task_id = payload.get("taskId", payload.get("task_id", str(time.time())))
        pad_code = payload.get("padCode", payload.get("pad_code", "unknown"))
        status = payload.get("taskStatus", payload.get("status", 2))
        
        event = CallbackEvent(
            callback_type=CallbackType.ADB_COMMAND,  # Default type
            task_id=task_id,
            pad_code=pad_code,
            status=TaskStatus(status) if isinstance(status, int) else TaskStatus.SUCCESS,
            timestamp=time.time(),
            data=payload,
        )
        
        background_tasks.add_task(queue.put, event)
        return {"code": 200, "msg": "success"}
    
    return app


# Pipeline integration helpers

async def wait_for_adb_completion(task_id: str, timeout: float = 60.0) -> Optional[str]:
    """
    Wait for an async ADB command to complete.
    
    Args:
        task_id: Task ID from async_adb_cmd response.
        timeout: Maximum wait time.
        
    Returns:
        Command output if successful, None if failed/timeout.
    """
    queue = get_event_queue()
    event = await queue.wait_for_event(CallbackType.ADB_COMMAND, task_id, timeout)
    
    if event and event.status == TaskStatus.SUCCESS:
        return event.data.get("output", "")
    return None


async def wait_for_app_install(task_id: str, timeout: float = 120.0) -> bool:
    """
    Wait for an app installation to complete.
    
    Args:
        task_id: Task ID from install_app response.
        timeout: Maximum wait time (default 2 min for large APKs).
        
    Returns:
        True if installation successful.
    """
    queue = get_event_queue()
    event = await queue.wait_for_event(CallbackType.APP_INSTALL, task_id, timeout)
    
    return event is not None and event.status == TaskStatus.SUCCESS


async def wait_for_new_device(task_id: str, timeout: float = 180.0) -> Optional[str]:
    """
    Wait for one-key new device operation to complete.
    
    Args:
        task_id: Task ID from one_key_new_device response.
        timeout: Maximum wait time (default 3 min for device reset).
        
    Returns:
        New pad code if successful, None otherwise.
    """
    queue = get_event_queue()
    event = await queue.wait_for_event(CallbackType.ONE_KEY_NEW_DEVICE, task_id, timeout)
    
    if event and event.status == TaskStatus.SUCCESS:
        return event.data.get("new_pad_code")
    return None


if __name__ == "__main__":
    import uvicorn
    
    app = create_callback_app()
    uvicorn.run(app, host="0.0.0.0", port=8091)
