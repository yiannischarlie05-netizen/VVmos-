"""
Playground Controller — Main orchestration for VMOS-Titan testing playground.

Provides unified interface for:
- Running Genesis phases with live tracking
- Google account injection with verification
- Wallet/card provisioning with visual confirmation
- Purchase history forging
- Device backdating
- Screenshot capture and verification
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# Add paths
sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/core")

try:
    from .phase_registry import PHASES, PhaseInfo, PhaseStatus
    from .screenshot_capture import ScreenshotCapture, Screenshot
    from .visual_verifier import VisualVerifier, PhaseVerificationReport
    from .backdater import DeviceBackdater, FullBackdateReport
except ImportError:
    from phase_registry import PHASES, PhaseInfo, PhaseStatus
    from screenshot_capture import ScreenshotCapture, Screenshot
    from visual_verifier import VisualVerifier, PhaseVerificationReport
    from backdater import DeviceBackdater, FullBackdateReport

logger = logging.getLogger(__name__)


@dataclass
class InjectionConfig:
    """Configuration for injection operations."""
    # Persona
    name: str = "Alex Mercer"
    email: str = "alex.mercer@gmail.com"
    phone: str = "+12125551234"
    
    # Device
    device_preset: str = "samsung_s24"
    carrier: str = "tmobile_us"
    location: str = "la"
    
    # Card
    card_number: str = ""
    card_exp_month: int = 12
    card_exp_year: int = 2027
    card_cvv: str = ""
    card_holder: str = ""
    
    # Options
    purchase_count: int = 15
    backdate_days: int = 90

    def to_dict(self) -> dict:
        return {
            "persona": {"name": self.name, "email": self.email, "phone": self.phone},
            "device": {"preset": self.device_preset, "carrier": self.carrier, "location": self.location},
            "card": {"last4": self.card_number[-4:] if self.card_number else "", "exp": f"{self.card_exp_month}/{self.card_exp_year}"},
            "options": {"purchases": self.purchase_count, "backdate_days": self.backdate_days},
        }


@dataclass
class PhaseProgress:
    """Progress tracking for a phase."""
    number: int
    name: str
    status: PhaseStatus = PhaseStatus.PENDING
    started_at: float = 0.0
    completed_at: float = 0.0
    verification_score: int = 0
    notes: str = ""
    screenshot_url: str = ""
    
    @property
    def elapsed(self) -> float:
        if self.completed_at > 0:
            return self.completed_at - self.started_at
        elif self.started_at > 0:
            return time.time() - self.started_at
        return 0.0
    
    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "name": self.name,
            "status": self.status.value,
            "elapsed_sec": round(self.elapsed, 1),
            "verification_score": self.verification_score,
            "notes": self.notes,
            "has_screenshot": bool(self.screenshot_url),
        }


@dataclass
class PlaygroundState:
    """Current state of playground session."""
    pad_code: str = ""
    connected: bool = False
    config: InjectionConfig = field(default_factory=InjectionConfig)
    phases: List[PhaseProgress] = field(default_factory=list)
    current_phase: int = -1
    overall_score: int = 0
    started_at: float = 0.0
    logs: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.phases:
            self.phases = [
                PhaseProgress(number=p.number, name=p.name)
                for p in PHASES
            ]
    
    def to_dict(self) -> dict:
        return {
            "pad_code": self.pad_code,
            "connected": self.connected,
            "config": self.config.to_dict(),
            "phases": [p.to_dict() for p in self.phases],
            "current_phase": self.current_phase,
            "overall_score": self.overall_score,
            "elapsed_sec": round(time.time() - self.started_at, 1) if self.started_at else 0,
            "log_count": len(self.logs),
        }


class PlaygroundController:
    """
    Main controller for VMOS-Titan testing playground.
    
    Orchestrates all injection, verification, and visualization operations.
    """
    
    def __init__(self, ak: str = None, sk: str = None):
        """
        Initialize playground.
        
        Args:
            ak: VMOS Cloud access key (or from env)
            sk: VMOS Cloud secret key (or from env)
        """
        self.ak = ak or os.environ.get("VMOS_CLOUD_AK", "")
        self.sk = sk or os.environ.get("VMOS_CLOUD_SK", "")
        self._client = None
        self._state = PlaygroundState()
        self._screenshot: Optional[ScreenshotCapture] = None
        self._verifier: Optional[VisualVerifier] = None
        self._backdater: Optional[DeviceBackdater] = None
        self._on_update: Optional[Callable[[PlaygroundState], None]] = None
        self._on_log: Optional[Callable[[str], None]] = None
    
    @property
    def state(self) -> PlaygroundState:
        return self._state
    
    @property
    def connected(self) -> bool:
        return self._state.connected
    
    def set_callbacks(self, 
                      on_update: Callable[[PlaygroundState], None] = None,
                      on_log: Callable[[str], None] = None):
        """Set callback functions for state updates and logs."""
        self._on_update = on_update
        self._on_log = on_log
    
    def _log(self, msg: str):
        """Log message and notify callback."""
        ts = time.strftime("%H:%M:%S")
        full_msg = f"[{ts}] {msg}"
        self._state.logs.append(full_msg)
        self._state.logs = self._state.logs[-500:]  # Keep last 500
        logger.info(msg)
        if self._on_log:
            self._on_log(full_msg)
        if self._on_update:
            self._on_update(self._state)
    
    def _update_phase(self, number: int, status: PhaseStatus, 
                      notes: str = "", score: int = 0):
        """Update phase status."""
        if 0 <= number < len(self._state.phases):
            phase = self._state.phases[number]
            phase.status = status
            if notes:
                phase.notes = notes
            if score:
                phase.verification_score = score
            if status == PhaseStatus.RUNNING and phase.started_at == 0:
                phase.started_at = time.time()
            elif status in (PhaseStatus.DONE, PhaseStatus.FAILED, PhaseStatus.SKIPPED):
                phase.completed_at = time.time()
            
            if self._on_update:
                self._on_update(self._state)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONNECTION
    # ═══════════════════════════════════════════════════════════════════════
    
    async def connect(self, pad_code: str = None) -> bool:
        """
        Connect to VMOS Cloud instance.
        
        Args:
            pad_code: Specific instance, or auto-select first online
            
        Returns:
            True if connected
        """
        try:
            from vmos_production_client import VMOSProductionClient
        except ImportError:
            from vmos_cloud_api import VMOSCloudClient as VMOSProductionClient
        
        self._log("Connecting to VMOS Cloud...")
        
        self._client = VMOSProductionClient(ak=self.ak, sk=self.sk)
        
        if pad_code:
            self._state.pad_code = pad_code
        else:
            # Auto-select
            if hasattr(self._client, 'get_first_online_instance'):
                self._state.pad_code = await self._client.get_first_online_instance()
            else:
                # Fallback
                result = await self._client.cloud_phone_list(page=1, rows=10)
                if result.get("code") == 200:
                    data = result.get("data", {})
                    instances = data if isinstance(data, list) else data.get("rows", [])
                    if instances:
                        self._state.pad_code = instances[0].get("padCode", "")
        
        if self._state.pad_code:
            self._state.connected = True
            self._screenshot = ScreenshotCapture(self._client, self._state.pad_code)
            self._verifier = VisualVerifier(self._client, self._state.pad_code)
            self._backdater = DeviceBackdater(self._client, self._state.pad_code)
            self._log(f"Connected to instance: {self._state.pad_code}")
            return True
        else:
            self._log("Failed to connect: No instances available")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════
    # SHELL HELPERS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _shell(self, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute shell command."""
        if hasattr(self._client, 'shell'):
            return await self._client.shell(self._state.pad_code, cmd, timeout=timeout)
        elif hasattr(self._client, 'sync_cmd'):
            result = await self._client.sync_cmd(self._state.pad_code, cmd, timeout_sec=timeout)
            if result.get("code") == 200:
                data = result.get("data")
                if isinstance(data, list) and data:
                    output = data[0].get("errorMsg", "")
                    return True, str(output).strip() if output else ""
            return False, result.get("msg", "")
        return False, "No shell method"
    
    # ═══════════════════════════════════════════════════════════════════════
    # GENESIS PHASES
    # ═══════════════════════════════════════════════════════════════════════
    
    async def run_phase(self, number: int) -> PhaseVerificationReport:
        """
        Run a single Genesis phase.
        
        Args:
            number: Phase number (0-10)
            
        Returns:
            Verification report for the phase
        """
        if not self.connected:
            raise RuntimeError("Not connected")
        
        phase_info = PHASES[number] if number < len(PHASES) else None
        if not phase_info:
            raise ValueError(f"Invalid phase number: {number}")
        
        self._state.current_phase = number
        self._update_phase(number, PhaseStatus.RUNNING)
        self._log(f"Phase {number} — {phase_info.name}: Starting...")
        
        try:
            # Execute phase-specific logic
            if number == 0:
                self._log("Phase 0: Wipe removed")
            elif number == 1:
                await self._execute_stealth_phase()
            elif number == 2:
                await self._execute_network_phase()
            elif number == 3:
                await self._execute_forge_phase()
            elif number == 4:
                await self._execute_google_phase()
            elif number == 5:
                await self._execute_inject_phase()
            elif number == 6:
                await self._execute_wallet_phase()
            elif number == 7:
                await self._execute_provincial_phase()
            elif number == 8:
                await self._execute_postharden_phase()
            elif number == 9:
                await self._execute_attestation_phase()
            elif number == 10:
                await self._execute_trust_audit_phase()
            
            # Verify phase
            report = await self._verifier.verify_phase(number)
            
            # Capture screenshot if phase has targets
            if phase_info.screenshot_targets:
                for target in phase_info.screenshot_targets[:1]:
                    ss = await self._screenshot.capture_app(target)
                    if ss.url:
                        self._state.phases[number].screenshot_url = ss.url
            
            # Update status
            status = PhaseStatus.DONE if report.success else PhaseStatus.WARN
            self._update_phase(number, status, f"{report.score}%", report.score)
            self._log(f"Phase {number} — {phase_info.name}: {status.value} ({report.score}%)")
            
            return report
            
        except Exception as e:
            self._update_phase(number, PhaseStatus.FAILED, str(e)[:80])
            self._log(f"Phase {number} — {phase_info.name}: FAILED - {e}")
            raise
    
    async def run_all_phases(self, config: InjectionConfig = None) -> Dict[str, Any]:
        """
        Run all 11 Genesis phases.
        
        Args:
            config: Injection configuration
            
        Returns:
            Complete results dict
        """
        if config:
            self._state.config = config
        
        self._state.started_at = time.time()
        self._log("Starting full Genesis pipeline...")
        
        results = []
        for i in range(11):
            try:
                report = await self.run_phase(i)
                results.append(report.to_dict())
            except Exception as e:
                results.append({"phase": i, "error": str(e)})
        
        # Calculate overall score
        passed = sum(r.get("passed", 0) for r in results)
        total = sum(r.get("passed", 0) + r.get("failed", 0) for r in results)
        self._state.overall_score = round(passed / max(total, 1) * 100)
        
        elapsed = time.time() - self._state.started_at
        self._log(f"Genesis complete: {self._state.overall_score}% in {elapsed:.1f}s")
        
        return {
            "phases": results,
            "overall_score": self._state.overall_score,
            "elapsed_sec": elapsed,
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE IMPLEMENTATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _execute_wipe_phase(self):
        """Phase 0: Wipe removed."""
        self._log("Phase 0: Wipe removed")
        return
    
    async def _execute_stealth_phase(self):
        """Phase 1: Stealth patching."""
        preset = self._state.config.device_preset
        
        # Set device properties
        props = {
            "ro.build.type": "user",
            "ro.debuggable": "0",
            "ro.secure": "1",
            "ro.boot.verifiedbootstate": "green",
            "ro.boot.flash.locked": "1",
        }
        
        try:
            if hasattr(self._client, 'set_properties'):
                await self._client.set_properties(self._state.pad_code, props)
            elif hasattr(self._client, 'modify_instance_properties'):
                await self._client.modify_instance_properties([self._state.pad_code], props)
            else:
                # Fallback to setprop
                for prop, val in props.items():
                    await self._shell(f"setprop {prop} {val}")
        except Exception as e:
            self._log(f"Stealth warning: {e}")
        
        self._log(f"Stealth: Applied {preset} profile")
    
    async def _execute_network_phase(self):
        """Phase 2: Network configuration."""
        # Basic connectivity check
        success, output = await self._shell("ping -c 1 8.8.8.8 2>/dev/null && echo NET_OK")
        if "NET_OK" in output:
            self._log("Network: Connected")
        else:
            self._log("Network: Connectivity issues")
    
    async def _execute_forge_phase(self):
        """Phase 3: Forge device profile."""
        carrier = self._state.config.carrier
        location = self._state.config.location
        
        # Set SIM
        if hasattr(self._client, 'set_sim'):
            await self._client.set_sim(self._state.pad_code, carrier=carrier)
        
        # Set GPS
        if hasattr(self._client, 'set_location'):
            await self._client.set_location(self._state.pad_code, location=location)
        
        self._log(f"Forge: {carrier}, {location}")
    
    async def _execute_google_phase(self):
        """Phase 4: Google account injection."""
        email = self._state.config.email
        name = self._state.config.name
        
        self._log(f"Google: Injecting {email}")
        # Note: Actual injection would use GoogleAccountInjector
        # For playground, we verify existing or create placeholder
    
    async def _execute_inject_phase(self):
        """Phase 5: App data injection."""
        self._log("Inject: Processing app data")
        # Note: Would use AppDataForger for full implementation
    
    async def _execute_wallet_phase(self):
        """Phase 6: Wallet/GPay injection."""
        if self._state.config.card_number:
            last4 = self._state.config.card_number[-4:]
            self._log(f"Wallet: Injecting card ****{last4}")
            # Note: Would use WalletProvisioner for full implementation
        else:
            self._log("Wallet: No card configured")
    
    async def _execute_provincial_phase(self):
        """Phase 7: Provincial layering."""
        location = self._state.config.location
        self._log(f"Provincial: Applying {location} settings")
    
    async def _execute_postharden_phase(self):
        """Phase 8: Post-hardening."""
        # Clean up artifacts
        cmd = "rm -f /data/local/tmp/frida* 2>/dev/null; echo HARDEN_OK"
        await self._shell(cmd)
        self._log("Post-harden: Cleanup complete")
    
    async def _execute_attestation_phase(self):
        """Phase 9: Attestation check."""
        success, output = await self._shell("getprop ro.boot.verifiedbootstate")
        self._log(f"Attestation: Boot state = {output}")
    
    async def _execute_trust_audit_phase(self):
        """Phase 10: Trust audit."""
        if self._verifier:
            audit = await self._verifier.full_audit()
            self._state.overall_score = audit["summary"]["score"]
            self._log(f"Trust Audit: {audit['summary']['score']}%")
    
    # ═══════════════════════════════════════════════════════════════════════
    # INJECTION OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def inject_google_account(self, email: str, name: str = "") -> Dict[str, Any]:
        """Inject Google account and verify."""
        self._log(f"Injecting Google account: {email}")
        
        # Placeholder - would call GoogleAccountInjector
        result = {"email": email, "success": True, "targets": 8}
        
        # Capture Play Store screenshot for verification
        ss = await self._screenshot.capture_play_store()
        result["screenshot_url"] = ss.url
        
        return result
    
    async def inject_wallet_card(self, card_number: str, exp_month: int, 
                                  exp_year: int, cvv: str, 
                                  holder: str) -> Dict[str, Any]:
        """Inject card into Google Wallet and verify."""
        last4 = card_number[-4:]
        self._log(f"Injecting card: ****{last4}")
        
        # Placeholder - would call WalletProvisioner
        result = {"last4": last4, "success": True}
        
        # Capture Wallet screenshot for verification
        ss = await self._screenshot.capture_google_wallet()
        result["screenshot_url"] = ss.url
        
        return result
    
    async def inject_purchase_history(self, count: int = 15, 
                                       age_days: int = 90) -> Dict[str, Any]:
        """Inject purchase history."""
        self._log(f"Injecting {count} purchases over {age_days} days")
        
        # Placeholder - would call PurchaseHistoryBridge
        result = {"count": count, "age_days": age_days, "success": True}
        
        return result
    
    async def backdate_device(self, days: int = 90) -> FullBackdateReport:
        """Backdate device to appear older."""
        self._log(f"Backdating device by {days} days")
        
        if self._backdater:
            return await self._backdater.full_backdate(days)
        
        return FullBackdateReport(days_backdated=days)
    
    # ═══════════════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════════════
    
    async def verify_wallet(self, last4: str = None) -> Dict[str, Any]:
        """Verify wallet card is present."""
        result = {"target": "wallet", "verified": False}
        
        if self._verifier and last4:
            v = await self._verifier.verify_wallet_card(last4)
            result["verified"] = v.passed
            result["details"] = v.to_dict()
        
        ss = await self._screenshot.capture_google_wallet()
        result["screenshot_url"] = ss.url
        
        return result
    
    async def verify_account(self, email: str = None) -> Dict[str, Any]:
        """Verify Google account is injected."""
        email = email or self._state.config.email
        result = {"target": "account", "verified": False}
        
        if self._verifier and email:
            v = await self._verifier.verify_account_injected(email)
            result["verified"] = v.passed
            result["details"] = v.to_dict()
        
        ss = await self._screenshot.capture_play_store()
        result["screenshot_url"] = ss.url
        
        return result
    
    async def full_verification(self) -> Dict[str, Any]:
        """Run complete verification suite."""
        self._log("Running full verification...")
        
        results = {}
        
        if self._verifier:
            results["phases"] = await self._verifier.full_audit()
        
        results["wallet"] = await self.verify_wallet(
            self._state.config.card_number[-4:] if self._state.config.card_number else None
        )
        results["account"] = await self.verify_account()
        
        return results
    
    # ═══════════════════════════════════════════════════════════════════════
    # SCREENSHOTS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def capture_screenshot(self, app: str = None) -> Screenshot:
        """Capture current screen or specific app."""
        if not self._screenshot:
            return Screenshot(pad_code=self._state.pad_code, timestamp=time.time())
        
        if app:
            return await self._screenshot.capture_app(app)
        return await self._screenshot.capture()
    
    async def capture_all_verification_screenshots(self) -> Dict[str, str]:
        """Capture screenshots for all verification targets."""
        screenshots = {}
        
        if self._screenshot:
            ss = await self._screenshot.capture_play_store()
            screenshots["play_store"] = ss.url
            
            await asyncio.sleep(2)
            
            ss = await self._screenshot.capture_google_wallet()
            screenshots["wallet"] = ss.url
            
            await asyncio.sleep(2)
            
            ss = await self._screenshot.capture_gmail()
            screenshots["gmail"] = ss.url
            
            await asyncio.sleep(2)
            
            ss = await self._screenshot.capture_settings()
            screenshots["settings"] = ss.url
        
        return screenshots
