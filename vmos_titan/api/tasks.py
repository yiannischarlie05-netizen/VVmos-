"""VMOS Cloud API - Tasks Module

Handles async task management, polling, and status monitoring for
long-running operations on cloud devices.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from vmos_titan.api.base import APIModule


@dataclass
class TaskInfo:
    """Task status information"""
    task_id: str
    operation: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float  # 0.0-1.0
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TasksAPI(APIModule):
    """Async task monitoring and management"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "tasks"

    async def get_task(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Get task status and details
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status information
        """
        return await self._call(
            "get",
            f"/tasks/{task_id}",
        )

    async def list_tasks(
        self,
        pad_code: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List tasks with filtering
        
        Args:
            pad_code: Filter by device (None = all)
            status: Filter by status ("pending", "running", "completed", "failed")
            limit: Maximum tasks to return
            offset: Pagination offset
            
        Returns:
            List of tasks with metadata
        """
        data = {
            "limit": limit,
            "offset": offset,
        }
        if pad_code:
            data["pad_code"] = pad_code
        if status:
            data["status"] = status

        return await self._call(
            "get",
            "/tasks",
            data=data,
        )

    async def get_task_result(
        self,
        task_id: str,
        timeout_sec: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Wait for task completion and get result
        
        Args:
            task_id: Task identifier
            timeout_sec: Max seconds to wait (None = indefinite)
            
        Returns:
            Task result
        """
        data = {}
        if timeout_sec:
            data["timeout"] = timeout_sec

        return await self._call(
            "get",
            f"/tasks/{task_id}/result",
            data=data,
        )

    async def poll_task(
        self,
        task_id: str,
        interval_sec: float = 1.0,
        max_polls: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Poll task for completion
        
        Args:
            task_id: Task identifier
            interval_sec: Poll interval in seconds
            max_polls: Maximum polls (None = unlimited)
            
        Returns:
            Final task status
        """
        return await self._call(
            "post",
            f"/tasks/{task_id}/poll",
            data={
                "interval": interval_sec,
                "max_polls": max_polls,
            },
        )

    async def cancel_task(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Cancel running task
        
        Args:
            task_id: Task identifier
            
        Returns:
            Cancellation status
        """
        return await self._call(
            "post",
            f"/tasks/{task_id}/cancel",
        )

    async def get_task_progress(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Get detailed task progress
        
        Args:
            task_id: Task identifier
            
        Returns:
            Progress information (percentage, ETA, current operation)
        """
        return await self._call(
            "get",
            f"/tasks/{task_id}/progress",
        )

    async def list_device_tasks(
        self,
        pad_code: str,
    ) -> Dict[str, Any]:
        """List all tasks for specific device
        
        Args:
            pad_code: Device identifier
            
        Returns:
            List of device tasks
        """
        return await self._call(
            "get",
            f"/device/{pad_code}/tasks",
        )

    async def retry_task(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Retry failed task
        
        Args:
            task_id: Task identifier
            
        Returns:
            New task information
        """
        return await self._call(
            "post",
            f"/tasks/{task_id}/retry",
        )

    async def get_task_log(
        self,
        task_id: str,
        lines: int = 100,
    ) -> Dict[str, Any]:
        """Get task execution log
        
        Args:
            task_id: Task identifier
            lines: Number of log lines to retrieve
            
        Returns:
            Task log entries
        """
        return await self._call(
            "get",
            f"/tasks/{task_id}/log",
            data={"lines": lines},
        )

    async def clear_task_history(
        self,
        pad_code: Optional[str] = None,
        older_than_days: int = 30,
    ) -> Dict[str, Any]:
        """Clear old task history
        
        Args:
            pad_code: Clear tasks for specific device (None = all)
            older_than_days: Delete tasks older than this many days
            
        Returns:
            Cleanup status
        """
        return await self._call(
            "post",
            "/tasks/cleanup",
            data={
                "pad_code": pad_code,
                "older_than_days": older_than_days,
            },
        )

    async def get_task_queue_status(
        self,
        pad_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get task queue status
        
        Args:
            pad_code: Queue status for specific device (None = global)
            
        Returns:
            Queue information (pending, active, completed)
        """
        path = f"/device/{pad_code}/task-queue" if pad_code else "/task-queue"
        return await self._call(
            "get",
            path,
        )
