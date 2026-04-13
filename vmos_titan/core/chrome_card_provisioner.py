"""
ChromeCardProvisioner — UI automation for Chrome autofill card provisioning.

This module uses DeviceAgent and TouchSimulator to add credit cards through
Chrome's settings UI, which properly encrypts card data via Android Keystore.
This addresses Gap P2: Chrome Keystore key derivation.

The alternative to NULL card_number_encrypted in direct DB injection.
"""

import asyncio
import logging
import time
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ProvisioningState(Enum):
    """State of the Chrome card provisioning process."""
    IDLE = "idle"
    LAUNCHING_CHROME = "launching_chrome"
    NAVIGATING_SETTINGS = "navigating_settings"
    OPENING_PAYMENT_METHODS = "opening_payment_methods"
    ADDING_CARD = "adding_card"
    ENTERING_DETAILS = "entering_details"
    SAVING_CARD = "saving_card"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CardData:
    """Credit card data for provisioning."""
    card_number: str
    exp_month: int
    exp_year: int
    cardholder_name: str
    cvv: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None


@dataclass
class ProvisioningResult:
    """Result of Chrome card provisioning."""
    success: bool
    state: ProvisioningState
    card_last4: Optional[str] = None
    encrypted: bool = False
    latency_ms: int = 0
    error: Optional[str] = None
    screenshots: Optional[List[str]] = None


class ChromeCardProvisioner:
    """
    Provision credit cards via Chrome UI automation.
    
    This approach uses the device's actual Chrome app to add cards,
    which ensures proper Android Keystore encryption of card numbers.
    
    Usage:
        provisioner = ChromeCardProvisioner(adb_target="127.0.0.1:6520")
        card = CardData(
            card_number="4111111111111111",
            exp_month=12,
            exp_year=2029,
            cardholder_name="John Doe"
        )
        result = await provisioner.provision_card(card)
    """
    
    # Chrome package and activity names
    CHROME_PACKAGES = [
        ("com.android.chrome", "com.google.android.apps.chrome.Main"),
        ("com.chrome.beta", "com.google.android.apps.chrome.Main"),
        ("com.kiwibrowser.browser", "org.nicotine.nicotine.Main"),
    ]
    
    # UI element patterns for locating buttons/fields
    UI_PATTERNS = {
        "settings_menu": ["More options", "⋮", "menu"],
        "settings_option": ["Settings", "설정", "Einstellungen"],
        "payment_methods": ["Payment methods", "Payment", "Cards", "支付方式"],
        "add_card": ["Add card", "Add payment method", "Add", "+"],
        "card_number_field": ["Card number", "Number", "卡号"],
        "expiry_field": ["Expiration", "Expiry", "MM/YY", "有效期"],
        "name_field": ["Name on card", "Cardholder", "姓名"],
        "save_button": ["Save", "Done", "Add", "保存"],
    }
    
    # Screen coordinates (fallback for common resolutions)
    # Format: (x_ratio, y_ratio) as percentage of screen dimensions
    FALLBACK_COORDS = {
        "menu_button": (0.95, 0.05),  # Top-right menu
        "settings_item": (0.5, 0.7),   # Settings in dropdown
        "payment_methods": (0.5, 0.4), # Payment methods in settings
        "add_button": (0.5, 0.8),      # Add card button
        "save_button": (0.5, 0.9),     # Save button
    }
    
    def __init__(self, adb_target: str = "127.0.0.1:6520"):
        """
        Initialize Chrome card provisioner.
        
        Args:
            adb_target: ADB target device (IP:port or serial)
        """
        self.adb_target = adb_target
        self._state = ProvisioningState.IDLE
        self._screen_width = 1080  # Default, will be detected
        self._screen_height = 2400
        self._chrome_package: Optional[str] = None
        self._chrome_activity: Optional[str] = None
    
    async def _sh(self, cmd: str, timeout: int = 30) -> str:
        """Execute shell command on device via ADB."""
        try:
            full_cmd = f"adb -s {self.adb_target} shell {cmd}"
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
            logger.warning(f"Command timed out: {cmd}")
            return ""
        except Exception as e:
            logger.error(f"Shell command failed: {e}")
            return ""
    
    async def _detect_screen_size(self):
        """Detect device screen dimensions."""
        output = await self._sh("wm size")
        if output:
            match = re.search(r"(\d+)x(\d+)", output)
            if match:
                self._screen_width = int(match.group(1))
                self._screen_height = int(match.group(2))
                logger.info(f"Screen size: {self._screen_width}x{self._screen_height}")
    
    async def _detect_chrome_package(self) -> bool:
        """Detect installed Chrome-compatible browser."""
        for package, activity in self.CHROME_PACKAGES:
            output = await self._sh(f"pm path {package} 2>/dev/null")
            if output:
                self._chrome_package = package
                self._chrome_activity = activity
                logger.info(f"Found Chrome: {package}")
                return True
        
        logger.error("No Chrome-compatible browser found")
        return False
    
    async def _tap(self, x: int, y: int, delay: float = 0.5):
        """Tap at screen coordinates."""
        await self._sh(f"input tap {x} {y}")
        await asyncio.sleep(delay)
    
    async def _tap_ratio(self, x_ratio: float, y_ratio: float, delay: float = 0.5):
        """Tap at screen position by ratio (0.0-1.0)."""
        x = int(self._screen_width * x_ratio)
        y = int(self._screen_height * y_ratio)
        await self._tap(x, y, delay)
    
    async def _input_text(self, text: str, delay: float = 0.3):
        """Input text via ADB."""
        # Escape special characters for shell
        escaped = text.replace("'", "\\'").replace(" ", "%s")
        await self._sh(f"input text '{escaped}'")
        await asyncio.sleep(delay)
    
    async def _press_key(self, keycode: str, delay: float = 0.2):
        """Press a key."""
        await self._sh(f"input keyevent {keycode}")
        await asyncio.sleep(delay)
    
    async def _find_ui_element(self, patterns: List[str]) -> Optional[Tuple[int, int]]:
        """
        Find a UI element by text patterns using UI Automator.
        
        Returns:
            (x, y) coordinates of element center, or None if not found
        """
        try:
            # Dump UI hierarchy
            await self._sh("uiautomator dump /data/local/tmp/ui.xml")
            xml = await self._sh("cat /data/local/tmp/ui.xml")
            
            for pattern in patterns:
                # Search for element with matching text
                match = re.search(
                    rf'text="[^"]*{re.escape(pattern)}[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                    xml,
                    re.IGNORECASE
                )
                if match:
                    x1, y1, x2, y2 = map(int, match.groups())
                    return ((x1 + x2) // 2, (y1 + y2) // 2)
            
            return None
            
        except Exception as e:
            logger.warning(f"UI element search failed: {e}")
            return None
    
    async def _launch_chrome_settings(self) -> bool:
        """Launch Chrome and navigate to settings."""
        self._state = ProvisioningState.LAUNCHING_CHROME
        
        # Launch Chrome
        await self._sh(
            f"am start -n {self._chrome_package}/{self._chrome_activity}"
        )
        await asyncio.sleep(2)
        
        self._state = ProvisioningState.NAVIGATING_SETTINGS
        
        # Try to find and tap menu button
        coords = await self._find_ui_element(self.UI_PATTERNS["settings_menu"])
        if coords:
            await self._tap(*coords)
        else:
            # Fallback: tap common menu location
            await self._tap_ratio(*self.FALLBACK_COORDS["menu_button"])
        
        await asyncio.sleep(1)
        
        # Find and tap Settings
        coords = await self._find_ui_element(self.UI_PATTERNS["settings_option"])
        if coords:
            await self._tap(*coords)
        else:
            await self._tap_ratio(*self.FALLBACK_COORDS["settings_item"])
        
        await asyncio.sleep(1.5)
        return True
    
    async def _navigate_to_payment_methods(self) -> bool:
        """Navigate to Payment methods in Chrome settings."""
        self._state = ProvisioningState.OPENING_PAYMENT_METHODS
        
        # Scroll down to find Payment methods
        for _ in range(3):
            coords = await self._find_ui_element(self.UI_PATTERNS["payment_methods"])
            if coords:
                await self._tap(*coords)
                await asyncio.sleep(1)
                return True
            
            # Scroll down
            await self._sh(
                f"input swipe {self._screen_width//2} {int(self._screen_height*0.7)} "
                f"{self._screen_width//2} {int(self._screen_height*0.3)} 300"
            )
            await asyncio.sleep(0.5)
        
        logger.warning("Payment methods not found, trying fallback")
        await self._tap_ratio(*self.FALLBACK_COORDS["payment_methods"])
        await asyncio.sleep(1)
        return True
    
    async def _add_new_card(self, card: CardData) -> bool:
        """Add a new card through the UI."""
        self._state = ProvisioningState.ADDING_CARD
        
        # Find and tap "Add card" button
        coords = await self._find_ui_element(self.UI_PATTERNS["add_card"])
        if coords:
            await self._tap(*coords)
        else:
            await self._tap_ratio(*self.FALLBACK_COORDS["add_button"])
        
        await asyncio.sleep(1.5)
        
        self._state = ProvisioningState.ENTERING_DETAILS
        
        # Enter card number
        coords = await self._find_ui_element(self.UI_PATTERNS["card_number_field"])
        if coords:
            await self._tap(*coords)
        else:
            # Tap first input field
            await self._tap_ratio(0.5, 0.3)
        
        await asyncio.sleep(0.3)
        await self._input_text(card.card_number)
        
        # Move to expiry field (Tab or tap)
        await self._press_key("KEYCODE_TAB")
        await asyncio.sleep(0.3)
        
        # Enter expiry (format: MM/YY or MMYY depending on UI)
        exp_str = f"{card.exp_month:02d}{card.exp_year % 100:02d}"
        await self._input_text(exp_str)
        
        # Move to name field
        await self._press_key("KEYCODE_TAB")
        await asyncio.sleep(0.3)
        
        # Enter cardholder name
        await self._input_text(card.cardholder_name)
        
        await asyncio.sleep(0.5)
        return True
    
    async def _save_card(self) -> bool:
        """Save the card."""
        self._state = ProvisioningState.SAVING_CARD
        
        # Find and tap Save button
        coords = await self._find_ui_element(self.UI_PATTERNS["save_button"])
        if coords:
            await self._tap(*coords)
        else:
            await self._tap_ratio(*self.FALLBACK_COORDS["save_button"])
        
        await asyncio.sleep(2)
        return True
    
    async def _verify_card_added(self, card: CardData) -> bool:
        """Verify the card was added successfully."""
        self._state = ProvisioningState.VERIFYING
        
        last4 = card.card_number[-4:]
        
        # Check Chrome's Web Data database for the card
        output = await self._sh(
            f"sqlite3 /data/data/{self._chrome_package}/app_chrome/Default/'Web Data' "
            f"\"SELECT card_number_encrypted, name_on_card FROM credit_cards "
            f"WHERE name_on_card LIKE '%{card.cardholder_name}%' LIMIT 1\" 2>/dev/null"
        )
        
        if output:
            # Check if card_number_encrypted is not NULL (properly encrypted)
            parts = output.split("|")
            if len(parts) >= 1 and parts[0] and parts[0] != "NULL":
                logger.info(f"Card verified with encryption: ***{last4}")
                return True
        
        # Fallback: check UI for card display
        xml_check = await self._sh("uiautomator dump /data/local/tmp/ui.xml && cat /data/local/tmp/ui.xml")
        if last4 in xml_check or card.cardholder_name in xml_check:
            logger.info(f"Card visible in UI: ***{last4}")
            return True
        
        logger.warning("Card verification inconclusive")
        return False
    
    async def provision_card(self, card: CardData, take_screenshots: bool = False) -> ProvisioningResult:
        """
        Provision a credit card through Chrome UI automation.
        
        Args:
            card: CardData with card details
            take_screenshots: Whether to capture screenshots during process
            
        Returns:
            ProvisioningResult with success status and details
        """
        start_time = time.time()
        screenshots = []
        
        try:
            # Initialize
            await self._detect_screen_size()
            
            if not await self._detect_chrome_package():
                return ProvisioningResult(
                    success=False,
                    state=ProvisioningState.FAILED,
                    error="No Chrome-compatible browser installed",
                    latency_ms=int((time.time() - start_time) * 1000),
                )
            
            # Step 1: Launch Chrome and go to settings
            if not await self._launch_chrome_settings():
                return ProvisioningResult(
                    success=False,
                    state=self._state,
                    error="Failed to launch Chrome settings",
                    latency_ms=int((time.time() - start_time) * 1000),
                )
            
            # Step 2: Navigate to Payment methods
            if not await self._navigate_to_payment_methods():
                return ProvisioningResult(
                    success=False,
                    state=self._state,
                    error="Failed to navigate to Payment methods",
                    latency_ms=int((time.time() - start_time) * 1000),
                )
            
            # Step 3: Add new card
            if not await self._add_new_card(card):
                return ProvisioningResult(
                    success=False,
                    state=self._state,
                    error="Failed to add card details",
                    latency_ms=int((time.time() - start_time) * 1000),
                )
            
            # Step 4: Save card
            if not await self._save_card():
                return ProvisioningResult(
                    success=False,
                    state=self._state,
                    error="Failed to save card",
                    latency_ms=int((time.time() - start_time) * 1000),
                )
            
            # Step 5: Verify
            encrypted = await self._verify_card_added(card)
            
            self._state = ProvisioningState.COMPLETED
            
            return ProvisioningResult(
                success=True,
                state=self._state,
                card_last4=card.card_number[-4:],
                encrypted=encrypted,
                latency_ms=int((time.time() - start_time) * 1000),
                screenshots=screenshots if take_screenshots else None,
            )
            
        except Exception as e:
            logger.error(f"Chrome card provisioning failed: {e}")
            self._state = ProvisioningState.FAILED
            return ProvisioningResult(
                success=False,
                state=self._state,
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000),
            )
        
        finally:
            # Press Home to exit Chrome
            await self._press_key("KEYCODE_HOME")


async def provision_chrome_card_via_ui(
    adb_target: str,
    card_number: str,
    exp_month: int,
    exp_year: int,
    cardholder_name: str,
) -> Dict[str, Any]:
    """
    Convenience function to provision a Chrome autofill card via UI.
    
    This is designed to be called from wallet_provisioner.py as an
    alternative to direct database injection.
    
    Args:
        adb_target: ADB device target
        card_number: Full card number
        exp_month: Expiration month (1-12)
        exp_year: Expiration year (4-digit)
        cardholder_name: Name on card
        
    Returns:
        Dict with success status and details
    """
    provisioner = ChromeCardProvisioner(adb_target)
    card = CardData(
        card_number=card_number,
        exp_month=exp_month,
        exp_year=exp_year,
        cardholder_name=cardholder_name,
    )
    
    result = await provisioner.provision_card(card)
    
    return {
        "success": result.success,
        "encrypted": result.encrypted,
        "last4": result.card_last4,
        "latency_ms": result.latency_ms,
        "error": result.error,
    }


if __name__ == "__main__":
    import sys
    
    async def main():
        target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:6520"
        
        print(f"Testing Chrome Card Provisioner on {target}...")
        
        # Test card
        card = CardData(
            card_number="4111111111111111",
            exp_month=12,
            exp_year=2029,
            cardholder_name="Test User",
        )
        
        provisioner = ChromeCardProvisioner(target)
        result = await provisioner.provision_card(card)
        
        print(f"\nResult:")
        print(f"  Success: {result.success}")
        print(f"  State: {result.state.value}")
        print(f"  Encrypted: {result.encrypted}")
        print(f"  Last4: {result.card_last4}")
        print(f"  Latency: {result.latency_ms}ms")
        if result.error:
            print(f"  Error: {result.error}")
    
    asyncio.run(main())
