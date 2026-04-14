"""
Interaction API Module — User input simulation and device interaction
Covers: touch, text input, SMS, calls, audio, ADB, broadcast
"""

from typing import Any, Dict, Optional
from .base import APIModule


class InteractionAPI(APIModule):
    """User input and device interaction operations."""
    
    def get_module_name(self) -> str:
        return "interaction"
    
    # ==================== Touch & Input ====================
    
    async def touch(
        self,
        pad_code: str,
        x: int,
        y: int,
        duration_ms: int = 100,
    ) -> Dict[str, Any]:
        """
        Simulate touch input on device screen.
        
        Args:
            pad_code: Device pad code
            x: X coordinate
            y: Y coordinate
            duration_ms: Touch duration in milliseconds
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/touch",
            {
                "pad_code": pad_code,
                "x": x,
                "y": y,
                "duration_ms": duration_ms,
            },
        )
    
    async def swipe(
        self,
        pad_code: str,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_ms: int = 500,
    ) -> Dict[str, Any]:
        """
        Simulate swipe input on device screen.
        
        Args:
            pad_code: Device pad code
            x1: Start X coordinate
            y1: Start Y coordinate
            x2: End X coordinate
            y2: End Y coordinate
            duration_ms: Swipe duration in milliseconds
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/swipe",
            {
                "pad_code": pad_code,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "duration_ms": duration_ms,
            },
        )
    
    async def text_input(self, pad_code: str, text: str) -> Dict[str, Any]:
        """
        Send text input to device.
        
        Args:
            pad_code: Device pad code
            text: Text to input
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/textInput",
            {"pad_code": pad_code, "text": text},
        )
    
    # ==================== Keyboard ====================
    
    async def key_press(self, pad_code: str, key_code: int) -> Dict[str, Any]:
        """
        Simulate key press on device.
        
        Args:
            pad_code: Device pad code
            key_code: Android key code (e.g., 4=BACK, 3=HOME, 26=POWER)
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/keyPress",
            {"pad_code": pad_code, "key_code": key_code},
        )
    
    async def key_event(
        self,
        pad_code: str,
        key_code: int,
        action: str = "press",
    ) -> Dict[str, Any]:
        """
        Send key event to device.
        
        Args:
            pad_code: Device pad code
            key_code: Android key code
            action: "press", "up", or "down"
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/keyEvent",
            {
                "pad_code": pad_code,
                "key_code": key_code,
                "action": action,
            },
        )
    
    # ==================== SMS & Calls ====================
    
    async def send_sms(self, pad_code: str, phone: str, message: str) -> Dict[str, Any]:
        """
        Send SMS message on device.
        
        Args:
            pad_code: Device pad code
            phone: Phone number
            message: SMS message text
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/sendSms",
            {
                "pad_code": pad_code,
                "phone": phone,
                "message": message,
            },
        )
    
    async def receive_sms(
        self,
        pad_code: str,
        phone: str,
        message: str,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Simulate receiving SMS message on device.
        
        Args:
            pad_code: Device pad code
            phone: Sender phone number
            message: SMS message text
            timestamp: Optional message timestamp
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/receiveSms",
            {
                "pad_code": pad_code,
                "phone": phone,
                "message": message,
                "timestamp": timestamp,
            },
        )
    
    async def make_call(self, pad_code: str, phone: str) -> Dict[str, Any]:
        """
        Simulate making phone call on device.
        
        Args:
            pad_code: Device pad code
            phone: Phone number to call
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/makeCall",
            {"pad_code": pad_code, "phone": phone},
        )
    
    async def receive_call(
        self,
        pad_code: str,
        phone: str,
        caller_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Simulate receiving phone call on device.
        
        Args:
            pad_code: Device pad code
            phone: Caller phone number
            caller_name: Optional caller display name
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/receiveCall",
            {
                "pad_code": pad_code,
                "phone": phone,
                "caller_name": caller_name,
            },
        )
    
    # ==================== Audio ====================
    
    async def play_audio(
        self,
        pad_code: str,
        audio_url: str,
        duration_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Play audio on device.
        
        Args:
            pad_code: Device pad code
            audio_url: URL to audio file
            duration_ms: Audio duration in milliseconds
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/playAudio",
            {
                "pad_code": pad_code,
                "audio_url": audio_url,
                "duration_ms": duration_ms,
            },
        )
    
    # ==================== Broadcast & System Events ====================
    
    async def send_broadcast(
        self,
        pad_code: str,
        action: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send system broadcast on device.
        
        Args:
            pad_code: Device pad code
            action: Broadcast action (e.g., "android.intent.action.BOOT_COMPLETED")
            data: Optional broadcast data dict
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/sendBroadcast",
            {
                "pad_code": pad_code,
                "action": action,
                "data": data or {},
            },
        )
    
    # ==================== Screen & Display ====================
    
    async def set_screen_state(
        self,
        pad_code: str,
        on: bool,
    ) -> Dict[str, Any]:
        """
        Turn device screen on or off.
        
        Args:
            pad_code: Device pad code
            on: True to turn on, False to turn off
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/setScreenState",
            {"pad_code": pad_code, "on": on},
        )
    
    async def set_screen_brightness(
        self,
        pad_code: str,
        brightness: int,
    ) -> Dict[str, Any]:
        """
        Set device screen brightness.
        
        Args:
            pad_code: Device pad code
            brightness: Brightness level (0-255)
        
        Returns:
            API response dict
        
        Raises:
            ParameterError if brightness out of range
        """
        if not 0 <= brightness <= 255:
            from vmos_titan.core.exceptions import ParameterError
            raise ParameterError(
                message=f"Brightness out of range: {brightness} (0-255)",
                parameter="brightness",
            )
        
        return await self._call(
            "POST",
            "/api/pad/setScreenBrightness",
            {"pad_code": pad_code, "brightness": brightness},
        )
    
    async def set_orientation(
        self,
        pad_code: str,
        orientation: str,
    ) -> Dict[str, Any]:
        """
        Set device screen orientation.
        
        Args:
            pad_code: Device pad code
            orientation: "portrait", "landscape", or "auto"
        
        Returns:
            API response dict
        """
        if orientation not in ("portrait", "landscape", "auto"):
            from vmos_titan.core.exceptions import ParameterError
            raise ParameterError(
                message=f"Invalid orientation: {orientation}",
                parameter="orientation",
            )
        
        return await self._call(
            "POST",
            "/api/pad/setOrientation",
            {"pad_code": pad_code, "orientation": orientation},
        )
    
    # ==================== Clipboard ====================
    
    async def get_clipboard(self, pad_code: str) -> Dict[str, Any]:
        """
        Get device clipboard content.
        
        Args:
            pad_code: Device pad code
        
        Returns:
            API response with clipboard text
        """
        return await self._call(
            "POST",
            "/api/pad/getClipboard",
            {"pad_code": pad_code},
        )
    
    async def set_clipboard(self, pad_code: str, text: str) -> Dict[str, Any]:
        """
        Set device clipboard content.
        
        Args:
            pad_code: Device pad code
            text: Text to set on clipboard
        
        Returns:
            API response dict
        """
        return await self._call(
            "POST",
            "/api/pad/setClipboard",
            {"pad_code": pad_code, "text": text},
        )
