"""VMOS Cloud API - Automation Tasks Module

Manages TikTok and other social media automation tasks with scheduling
and performance tracking.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from vmos_titan.api.base import APIModule


@dataclass
class AutomationTask:
    """Automation task configuration"""
    task_id: str
    type_: str  # "tiktok_view", "tiktok_like", etc.
    status: str  # "scheduled", "running", "completed", "failed"
    created_at: datetime
    scheduled_start: Optional[datetime]
    completed_at: Optional[datetime]
    performance_metrics: Dict[str, Any]


class AutomationTasksAPI(APIModule):
    """Social media automation task management"""
    
    def get_module_name(self) -> str:
        """Get module name."""
        return "automation_tasks"

    async def list_tasks(
        self,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List automation tasks
        
        Args:
            task_type: Filter by task type
            status: Filter by status
            limit: Maximum results
            
        Returns:
            List of automation tasks
        """
        data = {"limit": limit}
        if task_type:
            data["type"] = task_type
        if status:
            data["status"] = status

        return await self._call(
            "get",
            "/automation/tasks",
            data=data,
        )

    async def get_task(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Get automation task details
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task configuration and status
        """
        return await self._call(
            "get",
            f"/automation/tasks/{task_id}",
        )

    async def create_tiktok_view_task(
        self,
        pad_code: str,
        video_urls: List[str],
        view_duration_sec: int = 30,
        schedule_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create TikTok video view task
        
        Args:
            pad_code: Device to use
            video_urls: List of TikTok video URLs
            view_duration_sec: Duration to view each video
            schedule_time: When to run task (None = immediate)
            
        Returns:
            Task information
        """
        data = {
            "pad_code": pad_code,
            "type": "tiktok_view",
            "video_urls": video_urls,
            "view_duration": view_duration_sec,
        }
        if schedule_time:
            data["schedule_time"] = schedule_time

        return await self._call(
            "post",
            "/automation/tasks",
            data=data,
        )

    async def create_tiktok_like_task(
        self,
        pad_code: str,
        video_urls: List[str],
        schedule_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create TikTok like task
        
        Args:
            pad_code: Device to use
            video_urls: Videos to like
            schedule_time: When to run task
            
        Returns:
            Task information
        """
        data = {
            "pad_code": pad_code,
            "type": "tiktok_like",
            "video_urls": video_urls,
        }
        if schedule_time:
            data["schedule_time"] = schedule_time

        return await self._call(
            "post",
            "/automation/tasks",
            data=data,
        )

    async def create_tiktok_follow_task(
        self,
        pad_code: str,
        creator_usernames: List[str],
        schedule_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create TikTok follow task
        
        Args:
            pad_code: Device to use
            creator_usernames: Creators to follow
            schedule_time: When to run task
            
        Returns:
            Task information
        """
        data = {
            "pad_code": pad_code,
            "type": "tiktok_follow",
            "usernames": creator_usernames,
        }
        if schedule_time:
            data["schedule_time"] = schedule_time

        return await self._call(
            "post",
            "/automation/tasks",
            data=data,
        )

    async def create_tiktok_comment_task(
        self,
        pad_code: str,
        video_urls: List[str],
        comments: List[str],
        schedule_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create TikTok comment task
        
        Args:
            pad_code: Device to use
            video_urls: Videos to comment on
            comments: Comments to post
            schedule_time: When to run task
            
        Returns:
            Task information
        """
        data = {
            "pad_code": pad_code,
            "type": "tiktok_comment",
            "video_urls": video_urls,
            "comments": comments,
        }
        if schedule_time:
            data["schedule_time"] = schedule_time

        return await self._call(
            "post",
            "/automation/tasks",
            data=data,
        )

    async def get_task_results(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Get task execution results
        
        Args:
            task_id: Task identifier
            
        Returns:
            Results and performance metrics
        """
        return await self._call(
            "get",
            f"/automation/tasks/{task_id}/results",
        )

    async def cancel_task(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Cancel automation task
        
        Args:
            task_id: Task to cancel
            
        Returns:
            Cancellation status
        """
        return await self._call(
            "post",
            f"/automation/tasks/{task_id}/cancel",
        )

    async def pause_task(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Pause automation task
        
        Args:
            task_id: Task to pause
            
        Returns:
            Pause status
        """
        return await self._call(
            "post",
            f"/automation/tasks/{task_id}/pause",
        )

    async def resume_task(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Resume paused task
        
        Args:
            task_id: Task to resume
            
        Returns:
            Resume status
        """
        return await self._call(
            "post",
            f"/automation/tasks/{task_id}/resume",
        )

    async def delete_task(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Delete automation task
        
        Args:
            task_id: Task to delete
            
        Returns:
            Deletion status
        """
        return await self._call(
            "delete",
            f"/automation/tasks/{task_id}",
        )

    async def get_task_log(
        self,
        task_id: str,
        lines: int = 100,
    ) -> Dict[str, Any]:
        """Get task execution log
        
        Args:
            task_id: Task identifier
            lines: Number of log lines
            
        Returns:
            Task log entries
        """
        return await self._call(
            "get",
            f"/automation/tasks/{task_id}/log",
            data={"lines": lines},
        )

    async def schedule_recurring_task(
        self,
        task_type: str,
        pad_code: str,
        config: Dict[str, Any],
        interval: str,  # "daily", "weekly", "hourly"
        start_time: str,
    ) -> Dict[str, Any]:
        """Create recurring automation task
        
        Args:
            task_type: Type of task
            pad_code: Device to use
            config: Task configuration
            interval: Recurrence interval
            start_time: Start time for schedule
            
        Returns:
            Scheduled task information
        """
        return await self._call(
            "post",
            "/automation/tasks/recurring",
            data={
                "type": task_type,
                "pad_code": pad_code,
                "config": config,
                "interval": interval,
                "start_time": start_time,
            },
        )

    async def get_automation_stats(
        self,
        time_window_days: int = 7,
    ) -> Dict[str, Any]:
        """Get automation statistics
        
        Args:
            time_window_days: Days to include in stats
            
        Returns:
            Statistics and summary data
        """
        return await self._call(
            "get",
            "/automation/stats",
            data={"days": time_window_days},
        )
