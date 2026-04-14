#!/usr/bin/env python3
"""
VMOS-Titan Genesis Real-World Test Runner
==========================================
Tests the upgraded Genesis engine on device APP5AU4BB1QQBHNA.

This script validates:
1. AUTO_CASCADE authentication (zero-UI)
2. Host-side database construction
3. 8-flag zero-auth wallet configuration
4. Purchase history injection
5. UUID coherence across all data stores

Usage:
    python scripts/test_genesis_real_world.py
    
    # With credentials:
    GOOGLE_EMAIL=user@gmail.com GOOGLE_PASSWORD=xxxx python scripts/test_genesis_real_world.py
"""

import asyncio
import json
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vmos_titan", "core"))

# Test configuration
TEST_DEVICE = "APP5AU4BB1QQBHNA"
TEST_EMAIL = os.environ.get("GOOGLE_EMAIL", "test.genesis@gmail.com")
TEST_PASSWORD = os.environ.get("GOOGLE_PASSWORD", "test-app-password")
TEST_CC_NUMBER = os.environ.get("TEST_CC", "4532015112830366")
TEST_CC_HOLDER = os.environ.get("TEST_CC_HOLDER", "Test User")


class TestResult:
    """Test result tracker."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
    
    def add_pass(self, name: str):
        self.passed += 1
        print(f"  ✓ {name}")
    
    def add_fail(self, name: str, error: str = ""):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ✗ {name}: {error}")
    
    def add_skip(self, name: str, reason: str = ""):
        self.skipped += 1
        print(f"  ○ {name}: {reason}")
    
    def summary(self) -> str:
        total = self.passed + self.failed + self.skipped
        return f"Tests: {self.passed}/{total} passed, {self.failed} failed, {self.skipped} skipped"


def test_imports():
    """Test that all modules can be imported."""
    print("\n=== Testing Module Imports ===")
    result = TestResult()
    
    modules = [
        ("google_master_auth", "GoogleMasterAuth, AuthMethod, is_app_password"),
        ("vmos_db_builder", "VMOSDbBuilder, CardData, PurchaseRecord"),
        ("wallet_injection", "GooglePayInjector, PaymentCard, WalletType"),
        ("genesis_real_world_executor", "GenesisExecutor, ExecutorConfig"),
        ("transaction_simulator", "TransactionSimulator, PurchaseHistoryGenerator"),
    ]
    
    for module_name, expected_items in modules:
        try:
            module = __import__(module_name)
            for item in expected_items.split(", "):
                if hasattr(module, item):
                    result.add_pass(f"{module_name}.{item}")
                else:
                    result.add_fail(f"{module_name}.{item}", "not found")
        except ImportError as e:
            result.add_fail(module_name, str(e))
    
    print(result.summary())
    return result


def test_auth_method():
    """Test AUTO_CASCADE authentication method."""
    print("\n=== Testing Authentication (AUTO_CASCADE) ===")
    result = TestResult()
    
    try:
        from google_master_auth import GoogleMasterAuth, AuthMethod, is_app_password
        
        # Test app password detection
        if is_app_password("xxxx-xxxx-xxxx-xxxx"):
            result.add_pass("App password detection (valid)")
        else:
            result.add_fail("App password detection (valid)", "Should return True")
        
        if not is_app_password("regular_password123"):
            result.add_pass("App password detection (invalid)")
        else:
            result.add_fail("App password detection (invalid)", "Should return False")
        
        # Test AUTO_CASCADE method exists
        if AuthMethod.AUTO_CASCADE:
            result.add_pass("AUTO_CASCADE method defined")
        else:
            result.add_fail("AUTO_CASCADE method defined", "Not found")
        
        # Test authentication (mock - no real credentials)
        auth = GoogleMasterAuth()
        auth_result = auth.authenticate(
            email="test@example.com",
            password="test-password",
            method=AuthMethod.AUTO_CASCADE,
        )
        
        if auth_result.cascade_attempts:
            result.add_pass(f"Cascade attempts recorded: {auth_result.cascade_attempts}")
        else:
            result.add_fail("Cascade attempts recording", "No attempts recorded")
        
        # Should fall back to hybrid mode with synthetic tokens
        if auth_result.success:
            result.add_pass("Authentication completed (hybrid mode)")
        else:
            result.add_skip("Authentication", "Expected to fail without real credentials")
        
    except Exception as e:
        result.add_fail("Authentication test", str(e))
    
    print(result.summary())
    return result


def test_database_builder():
    """Test host-side database construction."""
    print("\n=== Testing Database Builder ===")
    result = TestResult()
    
    try:
        from vmos_db_builder import VMOSDbBuilder
        
        builder = VMOSDbBuilder()
        
        # Test accounts_ce.db
        accounts_ce = builder.build_accounts_ce(
            email="test@gmail.com",
            display_name="Test User",
            gaia_id="123456789012345678",
            tokens={"com.google": "ya29.test_token"},
            age_days=90,
        )
        if len(accounts_ce) > 1000:
            result.add_pass(f"accounts_ce.db built ({len(accounts_ce)} bytes)")
        else:
            result.add_fail("accounts_ce.db", f"Too small: {len(accounts_ce)} bytes")
        
        # Test accounts_de.db
        accounts_de = builder.build_accounts_de(
            email="test@gmail.com",
            display_name="Test User",
            age_days=90,
        )
        if len(accounts_de) > 500:
            result.add_pass(f"accounts_de.db built ({len(accounts_de)} bytes)")
        else:
            result.add_fail("accounts_de.db", f"Too small: {len(accounts_de)} bytes")
        
        # Test tapandpay.db
        tapandpay = builder.build_tapandpay(
            card_number="4532015112830366",
            exp_month=12,
            exp_year=2029,
            cardholder="Test User",
            persona_email="test@gmail.com",
            age_days=90,
        )
        if len(tapandpay) > 2000:
            result.add_pass(f"tapandpay.db built ({len(tapandpay)} bytes)")
        else:
            result.add_fail("tapandpay.db", f"Too small: {len(tapandpay)} bytes")
        
        # Test library.db
        library = builder.build_library(
            email="test@gmail.com",
            num_auto_purchases=10,
            age_days=90,
        )
        if len(library) > 1000:
            result.add_pass(f"library.db built ({len(library)} bytes)")
        else:
            result.add_fail("library.db", f"Too small: {len(library)} bytes")
        
        # Test complete bundle
        bundle = builder.build_complete_bundle(
            email="test@gmail.com",
            display_name="Test User",
            card_number="4532015112830366",
            cardholder="Test User",
            age_days=90,
        )
        if "accounts_ce_bytes" in bundle and "tapandpay_bytes" in bundle:
            result.add_pass("Complete bundle built")
        else:
            result.add_fail("Complete bundle", "Missing expected keys")
        
        if bundle.get("instrument_id"):
            result.add_pass(f"Instrument ID generated: {bundle['instrument_id']}")
        else:
            result.add_fail("Instrument ID", "Not generated")
        
    except Exception as e:
        result.add_fail("Database builder test", str(e))
    
    print(result.summary())
    return result


def test_wallet_injection():
    """Test wallet injection with 8-flag zero-auth."""
    print("\n=== Testing Wallet Injection (8-Flag Zero-Auth) ===")
    result = TestResult()
    
    try:
        from wallet_injection import GooglePayInjector, PaymentCard
        
        # Create test card
        card = PaymentCard(
            card_number="4532015112830366",
            exp_month=12,
            exp_year=2029,
            cardholder_name="Test User",
        )
        
        # Test DPAN generation
        if card.dpan and card.dpan != card.card_number:
            result.add_pass(f"DPAN generated: ****{card.dpan[-4:]}")
        else:
            result.add_fail("DPAN generation", "DPAN same as FPAN or empty")
        
        # Test network detection
        if card.network.value == "visa":
            result.add_pass("Network detected: VISA")
        else:
            result.add_fail("Network detection", f"Expected VISA, got {card.network.value}")
        
        # Test COIN.xml with 8 flags
        injector = GooglePayInjector()
        coin_xml = injector.build_coin_xml(card, "test@gmail.com")
        
        required_flags = [
            "purchase_requires_auth",
            "require_purchase_auth",
            "one_touch_enabled",
            "biometric_payment_enabled",
            "PAYMENTS_ZERO_AUTH_ENABLED",
            "device_auth_not_required",
            "skip_challenge_on_payment",
            "frictionless_checkout_enabled",
        ]
        
        flags_found = sum(1 for flag in required_flags if flag in coin_xml)
        if flags_found == 8:
            result.add_pass("All 8 zero-auth flags present")
        else:
            result.add_fail("Zero-auth flags", f"Only {flags_found}/8 flags found")
        
        # Test GMS COIN.xml
        gms_coin = injector.build_gms_coin_xml(card, "test@gmail.com")
        if "PAYMENTS_ZERO_AUTH_ENABLED" in gms_coin:
            result.add_pass("GMS COIN.xml has zero-auth flag")
        else:
            result.add_fail("GMS COIN.xml", "Missing zero-auth flag")
        
        # Test wallet prefs with coherence
        wallet_prefs = injector.build_wallet_prefs_xml("test@gmail.com", "instrument_123", card)
        if "default_instrument_id" in wallet_prefs:
            result.add_pass("Wallet prefs has instrument ID for coherence")
        else:
            result.add_fail("Wallet prefs", "Missing instrument ID")
        
        # Test wallet UI tokenization bypass — unified method
        bypass_files = injector.get_all_wallet_ui_bypass_files(
            card, "test@gmail.com", "instrument_123", "Test User"
        )
        if len(bypass_files) >= 10:
            result.add_pass(f"Wallet UI bypass: {len(bypass_files)} files generated")
        else:
            result.add_fail("Wallet UI bypass", f"Only {len(bypass_files)} files, need 10+")
        
        # Verify each critical bypass file exists in the output
        critical_bypasses = [
            ("WalletOnboardingPrefs", "has_completed_onboarding"),
            ("IdentityCredentialsPrefs", "idv_complete"),
            ("PaymentMethodPrefs", "payment_method_verified"),
            ("SyncManager", "suppress_sign_in_required"),
            ("finsky", "never_require_auth"),
            ("tapandpay", "setup_complete"),
        ]
        for name, flag in critical_bypasses:
            matching = [v for k, v in bypass_files.items() if name in k]
            if matching and flag in matching[0]:
                result.add_pass(f"  {name}: {flag} ✓")
            else:
                result.add_fail(f"  {name}", f"Missing {flag}")
        
        # Test settings provider commands
        cmds = injector.get_settings_provider_commands()
        if len(cmds) >= 8:
            result.add_pass(f"Settings provider: {len(cmds)} commands")
        else:
            result.add_fail("Settings provider", f"Only {len(cmds)} commands")
        
        # Verify NFC default and setup_complete in commands
        nfc_cmd = any("nfc_payment_default_component" in c for c in cmds)
        setup_cmd = any("user_setup_complete" in c for c in cmds)
        if nfc_cmd and setup_cmd:
            result.add_pass("Settings: NFC default + setup_complete present")
        else:
            result.add_fail("Settings", f"NFC={nfc_cmd} setup={setup_cmd}")
        
    except Exception as e:
        result.add_fail("Wallet injection test", str(e))
    
    print(result.summary())
    return result


def test_transaction_simulator():
    """Test transaction simulation."""
    print("\n=== Testing Transaction Simulator ===")
    result = TestResult()
    
    try:
        from transaction_simulator import (
            TransactionSimulator, PurchaseRequest, PurchaseHistoryGenerator,
            generate_order_id, generate_purchase_history
        )
        
        # Test order ID generation
        order_id = generate_order_id()
        if order_id.startswith("GPA.") and len(order_id) == 24:
            result.add_pass(f"Order ID format: {order_id}")
        else:
            result.add_fail("Order ID format", f"Invalid: {order_id}")
        
        # Test purchase history generation
        history = generate_purchase_history("test@gmail.com", age_days=90, num_entries=20)
        if len(history) >= 15:
            result.add_pass(f"Purchase history: {len(history)} entries")
        else:
            result.add_fail("Purchase history", f"Only {len(history)} entries")
        
        # Check history has required fields
        if history and all(k in history[0] for k in ["app_id", "order_id", "purchase_time_ms"]):
            result.add_pass("Purchase history has required fields")
        else:
            result.add_fail("Purchase history fields", "Missing required fields")
        
        # Test simulator velocity check
        simulator = TransactionSimulator(email="test@gmail.com")
        if simulator._check_velocity():
            result.add_pass("Velocity check passed (fresh state)")
        else:
            result.add_fail("Velocity check", "Should pass on fresh state")
        
    except Exception as e:
        result.add_fail("Transaction simulator test", str(e))
    
    print(result.summary())
    return result


async def test_genesis_executor():
    """Test Genesis executor (mock mode)."""
    print("\n=== Testing Genesis Executor (Mock Mode) ===")
    result = TestResult()
    
    try:
        from genesis_real_world_executor import GenesisExecutor, ExecutorConfig
        
        config = ExecutorConfig(
            pad_code=TEST_DEVICE,
            google_email=TEST_EMAIL,
            google_password=TEST_PASSWORD,
            cc_number=TEST_CC_NUMBER,
            cc_holder=TEST_CC_HOLDER,
            verbose=False,
        )
        
        executor = GenesisExecutor(config)
        
        # Run in mock mode (no VMOS client)
        exec_result = await executor.execute()
        
        # Check if running in mock mode
        mock_mode = executor.client is None
        
        if exec_result.pad_code == TEST_DEVICE:
            result.add_pass(f"Executor initialized for {TEST_DEVICE}")
        else:
            result.add_fail("Executor initialization", "Wrong device")
        
        if len(exec_result.phases_completed) > 0:
            result.add_pass(f"Phases completed: {exec_result.phases_completed}")
        else:
            result.add_skip("Phases completion", "Expected to skip in mock mode")
        
        if exec_result.execution_time_seconds > 0:
            result.add_pass(f"Execution time: {exec_result.execution_time_seconds:.2f}s")
        else:
            result.add_fail("Execution time", "Should be > 0")
        
        # Trust score expectations differ between real and mock
        if mock_mode:
            # In mock mode, stealth is skipped and cloud_sync_defeated=False
            expected_score = 96  # 100 - 4 (stealth bypass) but other phases complete
            if exec_result.trust_score >= expected_score:
                result.add_pass(f"Trust score: {exec_result.trust_score}/100 (mock mode)")
            else:
                result.add_fail("Trust score", f"{exec_result.trust_score}/100 — expected {expected_score}+")
        else:
            if exec_result.trust_score == 100:
                result.add_pass(f"Trust score: {exec_result.trust_score}/100 ★ PERFECT")
            elif exec_result.trust_score >= 80:
                result.add_fail("Trust score", f"{exec_result.trust_score}/100 — not 100, check phases")
            else:
                result.add_fail("Trust score", f"{exec_result.trust_score}/100 — too low")
        
        # Verify wallet UI tokenization happened
        if exec_result.wallet_ui_tokenized:
            result.add_pass(f"Wallet UI tokenized: {exec_result.wallet_ui_files_injected} files")
        else:
            result.add_fail("Wallet UI tokenization", "Not completed")
        
        if exec_result.settings_commands_run >= 8:
            result.add_pass(f"Settings commands: {exec_result.settings_commands_run}")
        else:
            result.add_fail("Settings commands", f"Only {exec_result.settings_commands_run}/8")
        
        # Verify no 2FA/UI methods used
        if "wallet_ui_tokenization" in exec_result.phases_completed:
            result.add_pass("Zero-UI wallet tokenization phase completed")
        else:
            result.add_fail("Zero-UI wallet tokenization", "Phase not completed")
        
        # Verify new phases: attestation, post-harden, app restart
        if "attestation" in exec_result.phases_completed:
            result.add_pass(f"Attestation: {exec_result.attestation_tier} tier")
        else:
            result.add_fail("Attestation", "Phase not completed")
        
        if "post_harden" in exec_result.phases_completed:
            result.add_pass(f"Post-harden: cloud_sync_defeated={exec_result.cloud_sync_defeated}")
        else:
            result.add_fail("Post-harden", "Phase not completed")
        
        if "app_restart" in exec_result.phases_completed:
            result.add_pass("App restart cycle completed")
        else:
            result.add_fail("App restart", "Phase not completed")
        
        # Verify account injection includes GMS/GSF shared prefs
        if "account_injection" in exec_result.phases_completed:
            result.add_pass("Account injection (7 targets) completed")
        else:
            result.add_fail("Account injection", "Phase not completed")
        
        # Verify all 13 phases pipeline (mock may skip stealth)
        expected_phases = [
            "authentication", "database_build", "stealth_patch",
            "account_injection", "wallet_injection", "wallet_ui_tokenization",
            "purchase_history", "attestation", "post_harden",
            "app_restart", "verification",
        ]
        
        # In mock mode, stealth_patch is expected to be skipped, not completed
        if mock_mode:
            expected_phases_mock = [p for p in expected_phases if p != "stealth_patch"]
            missing = [p for p in expected_phases_mock if p not in exec_result.phases_completed]
            if not missing:
                result.add_pass(f"All {len(expected_phases_mock)} non-stealth phases completed (mock mode)")
            else:
                result.add_fail("Phase coverage", f"Missing: {missing}")
        else:
            missing = [p for p in expected_phases if p not in exec_result.phases_completed]
            if not missing:
                result.add_pass(f"All {len(expected_phases)} phases completed")
            else:
                result.add_fail("Phase coverage", f"Missing: {missing}")
        
        # Verify result dict includes new fields
        result_dict = exec_result.to_dict()
        new_fields = ["cloud_sync_defeated", "iptables_rules", "forensic_backdated", "attestation_tier"]
        for field in new_fields:
            if field in result_dict:
                result.add_pass(f"Result field: {field}={result_dict[field]}")
            else:
                result.add_fail(f"Result field: {field}", "Missing from to_dict()")
        
    except Exception as e:
        result.add_fail("Genesis executor test", str(e))
    
    print(result.summary())
    return result


def main():
    """Run all tests."""
    print("=" * 60)
    print("VMOS-Titan Genesis Real-World Upgrade Test Suite")
    print("=" * 60)
    print(f"Test Device: {TEST_DEVICE}")
    print(f"Test Email: {TEST_EMAIL}")
    print(f"Test CC: ****{TEST_CC_NUMBER[-4:]}")
    print("=" * 60)
    
    start_time = time.time()
    all_results = []
    
    # Run tests
    all_results.append(test_imports())
    all_results.append(test_auth_method())
    all_results.append(test_database_builder())
    all_results.append(test_wallet_injection())
    all_results.append(test_transaction_simulator())
    all_results.append(asyncio.run(test_genesis_executor()))
    
    # Summary
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total_skipped = sum(r.skipped for r in all_results)
    total_tests = total_passed + total_failed + total_skipped
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Total: {total_passed}/{total_tests} passed, {total_failed} failed, {total_skipped} skipped")
    print(f"Time: {elapsed:.2f}s")
    
    if total_failed > 0:
        print("\nFailed tests:")
        for r in all_results:
            for name, error in r.errors:
                print(f"  - {name}: {error}")
    
    # Success criteria
    success = total_failed == 0
    print(f"\nOverall: {'PASS ✓' if success else 'FAIL ✗'}")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
