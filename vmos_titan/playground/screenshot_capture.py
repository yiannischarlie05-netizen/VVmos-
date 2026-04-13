"""
Screenshot Capture — Capture and manage device screenshots via VMOS Cloud API.

Provides:
- Screenshot capture via API
- Base64 encoding for web display
- Screenshot diffing for before/after comparison
- App launching before capture
"""

import asyncio
import base64
import hashlib
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Screenshot:
    """Captured screenshot data."""
    pad_code: str
    timestamp: float
    base64_data: str = ""
    url: str = ""
    width: int = 0
    height: int = 0
    hash: str = ""
    
    def to_dict(self) -> dict:
        return {
            "pad_code": self.pad_code,
            "timestamp": self.timestamp,
            "has_data": bool(self.base64_data),
            "url": self.url,
            "width": self.width,
            "height": self.height,
            "hash": self.hash,
        }


class ScreenshotCapture:
    """Capture and manage device screenshots."""
    
    def __init__(self, client, pad_code: str):
        """
        Initialize screenshot capture.
        
        Args:
            client: VMOSCloudClient or VMOSProductionClient instance
            pad_code: Device pad code
        """
        self.client = client
        self.pad_code = pad_code
        self._cache: Dict[str, Screenshot] = {}
    
    async def capture(self, label: str = "") -> Screenshot:
        """
        Capture current screen.
        
        Args:
            label: Optional label for caching
            
        Returns:
            Screenshot object with base64 data or URL
        """
        ts = time.time()
        screenshot = Screenshot(pad_code=self.pad_code, timestamp=ts)
        
        try:
            # Try get_preview_image first (returns URL)
            result = await self.client.get_preview_image([self.pad_code])
            
            if result.get("code") == 200:
                data = result.get("data", [])
                if isinstance(data, list) and data:
                    item = data[0]
                    if isinstance(item, dict):
                        screenshot.url = item.get("imageUrl", item.get("url", ""))
            
            # Fallback to screenshot API (task-based)
            if not screenshot.url:
                result = await self.client.screenshot([self.pad_code])
                if result.get("code") == 200:
                    data = result.get("data", [])
                    if isinstance(data, list) and data:
                        task_id = data[0].get("taskId")
                        if task_id:
                            # Wait for task completion
                            screenshot.url = await self._wait_for_screenshot_task(task_id)
            
            # Generate hash for diffing
            if screenshot.url or screenshot.base64_data:
                content = screenshot.url or screenshot.base64_data
                screenshot.hash = hashlib.md5(content.encode()).hexdigest()[:12]
            
            # Cache if labeled
            if label:
                self._cache[label] = screenshot
            
            logger.info(f"Screenshot captured: {screenshot.hash or 'no_data'}")
            
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
        
        return screenshot
    
    async def _wait_for_screenshot_task(self, task_id: int, timeout: int = 30) -> str:
        """Wait for screenshot task to complete and return URL."""
        for _ in range(timeout):
            try:
                result = await self.client.task_detail([task_id])
                if result.get("code") == 200:
                    data = result.get("data", [])
                    if isinstance(data, list) and data:
                        item = data[0]
                        status = item.get("taskStatus")
                        if status == 3:  # Completed
                            return item.get("taskResult", "")
                        elif status in (-1, -2, -3):  # Failed
                            return ""
            except Exception:
                pass
            await asyncio.sleep(1)
        return ""
    
    async def capture_app(self, package: str, activity: str = "", 
                          wait_sec: float = 2.0) -> Screenshot:
        """
        Launch app and capture screenshot.
        
        Args:
            package: App package name
            activity: Optional activity to launch
            wait_sec: Seconds to wait after launch
            
        Returns:
            Screenshot of app
        """
        # Launch app
        if activity:
            cmd = f"am start -n {package}/{activity}"
        else:
            cmd = f"monkey -p {package} -c android.intent.category.LAUNCHER 1"
        
        try:
            if hasattr(self.client, 'shell'):
                await self.client.shell(self.pad_code, cmd)
            elif hasattr(self.client, 'sync_cmd'):
                await self.client.sync_cmd(self.pad_code, cmd, timeout_sec=15)
            else:
                await self.client.async_adb_cmd([self.pad_code], cmd)
        except Exception as e:
            logger.warning(f"App launch failed: {e}")
        
        # Wait for app to render
        await asyncio.sleep(wait_sec)
        
        # Capture
        return await self.capture(label=package)
    
    async def capture_google_wallet(self) -> Screenshot:
        """Capture Google Wallet/Pay app."""
        return await self.capture_app(
            "com.google.android.apps.walletnfcrel",
            "com.google.android.apps.walletnfcrel.home.HomeActivity"
        )
    
    async def capture_play_store(self) -> Screenshot:
        """Capture Play Store app."""
        return await self.capture_app(
            "com.android.vending",
            "com.android.vending.AssetBrowserActivity"
        )
    
    async def capture_gmail(self) -> Screenshot:
        """Capture Gmail app."""
        return await self.capture_app("com.google.android.gm")
    
    async def capture_settings(self) -> Screenshot:
        """Capture Settings app (for device info verification)."""
        return await self.capture_app(
            "com.android.settings",
            "com.android.settings.Settings"
        )
    
    def get_cached(self, label: str) -> Optional[Screenshot]:
        """Get cached screenshot by label."""
        return self._cache.get(label)
    
    def diff(self, label1: str, label2: str) -> bool:
        """
        Check if two cached screenshots differ.
        
        Returns:
            True if screenshots are different
        """
        s1 = self._cache.get(label1)
        s2 = self._cache.get(label2)
        
        if not s1 or not s2:
            return True
        
        return s1.hash != s2.hash
    
    async def capture_before_after(self, action_coro, 
                                   wait_after: float = 2.0) -> Tuple[Screenshot, Screenshot]:
        """
        Capture before and after an action.
        
        Args:
            action_coro: Coroutine to execute between captures
            wait_after: Seconds to wait after action
            
        Returns:
            (before, after) screenshot tuple
        """
        before = await self.capture(label="before")
        
        await action_coro
        await asyncio.sleep(wait_after)
        
        after = await self.capture(label="after")
        
        return before, after
    
    def clear_cache(self):
        """Clear screenshot cache."""
        self._cache.clear()
