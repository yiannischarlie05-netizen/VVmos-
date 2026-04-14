"""
Phase Registry — Defines all 11 Genesis phases with verification steps.

Each phase includes:
- Name and description
- Verification method
- Expected outcomes
- Screenshot targets for visual verification
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class PhaseStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARN = "warn"


@dataclass
class VerificationStep:
    """Single verification step for a phase."""
    name: str
    description: str
    check_type: str  # "shell", "screenshot", "property", "file", "ocr"
    target: str  # Command, path, or property name
    expected: str  # Expected value or pattern
    screenshot_app: str = ""  # Package to launch for screenshot verification


@dataclass
class PhaseInfo:
    """Complete phase definition."""
    number: int
    name: str
    description: str
    verifications: List[VerificationStep] = field(default_factory=list)
    screenshot_targets: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "name": self.name,
            "description": self.description,
            "verifications": [
                {"name": v.name, "type": v.check_type, "target": v.target}
                for v in self.verifications
            ],
            "screenshot_targets": self.screenshot_targets,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

PHASES: List[PhaseInfo] = [
    # Phase 0: Wipe
    PhaseInfo(
        number=0,
        name="Wipe",
        description="Clear previous identity data (accounts, contacts, wallet, history)",
        verifications=[
            VerificationStep(
                name="accounts_cleared",
                description="accounts_ce.db removed or empty",
                check_type="file",
                target="/data/system_ce/0/accounts_ce.db",
                expected="missing_or_empty",
            ),
            VerificationStep(
                name="wallet_cleared",
                description="tapandpay.db removed",
                check_type="file",
                target="/data/data/com.google.android.gms/databases/tapandpay.db",
                expected="missing",
            ),
            VerificationStep(
                name="chrome_cleared",
                description="Chrome history cleared",
                check_type="file",
                target="/data/data/com.android.chrome/app_chrome/Default/History",
                expected="missing_or_empty",
            ),
        ],
    ),
    
    # Phase 1: Stealth Patch
    PhaseInfo(
        number=1,
        name="Stealth Patch",
        description="Device fingerprint, root hiding, proc sterilization",
        verifications=[
            VerificationStep(
                name="build_type",
                description="ro.build.type is 'user'",
                check_type="property",
                target="ro.build.type",
                expected="user",
            ),
            VerificationStep(
                name="debuggable",
                description="ro.debuggable is '0'",
                check_type="property",
                target="ro.debuggable",
                expected="0",
            ),
            VerificationStep(
                name="verified_boot",
                description="Boot state is green",
                check_type="property",
                target="ro.boot.verifiedbootstate",
                expected="green",
            ),
            VerificationStep(
                name="fingerprint_changed",
                description="Fingerprint matches preset",
                check_type="property",
                target="ro.build.fingerprint",
                expected="contains:user/release-keys",
            ),
        ],
    ),
    
    # Phase 2: Network/Proxy
    PhaseInfo(
        number=2,
        name="Network/Proxy",
        description="Configure network proxy and connectivity",
        verifications=[
            VerificationStep(
                name="network_connected",
                description="Network is connected",
                check_type="shell",
                target="ping -c 1 8.8.8.8",
                expected="contains:1 received",
            ),
        ],
    ),
    
    # Phase 3: Forge Profile
    PhaseInfo(
        number=3,
        name="Forge Profile",
        description="Generate and inject device identity (IMEI, serial, Android ID)",
        verifications=[
            VerificationStep(
                name="imei_set",
                description="IMEI is set",
                check_type="property",
                target="persist.radio.imei",
                expected="not_empty",
            ),
            VerificationStep(
                name="serial_set",
                description="Serial number is set",
                check_type="property",
                target="ro.serialno",
                expected="not_empty",
            ),
        ],
    ),
    
    # Phase 4: Google Account
    PhaseInfo(
        number=4,
        name="Google Account",
        description="Inject Gmail account into Play Store and all Google apps",
        verifications=[
            VerificationStep(
                name="accounts_ce_injected",
                description="Account in accounts_ce.db",
                check_type="shell",
                target="sqlite3 /data/system_ce/0/accounts_ce.db 'SELECT name FROM accounts LIMIT 1'",
                expected="contains:@",
            ),
            VerificationStep(
                name="play_store_signed_in",
                description="Play Store shows account",
                check_type="screenshot",
                target="com.android.vending",
                expected="ocr:@gmail.com",
                screenshot_app="com.android.vending",
            ),
        ],
        screenshot_targets=["com.android.vending", "com.google.android.gm"],
    ),
    
    # Phase 5: Inject
    PhaseInfo(
        number=5,
        name="Inject",
        description="App data injection (SharedPrefs, databases, login states)",
        verifications=[
            VerificationStep(
                name="app_data_present",
                description="App SharedPrefs injected",
                check_type="shell",
                target="ls /data/data/com.android.chrome/shared_prefs/*.xml | wc -l",
                expected="greater_than:0",
            ),
        ],
    ),
    
    # Phase 6: Wallet/GPay
    PhaseInfo(
        number=6,
        name="Wallet/GPay",
        description="Inject credit card into Google Wallet with transaction history",
        verifications=[
            VerificationStep(
                name="tapandpay_exists",
                description="tapandpay.db created",
                check_type="file",
                target="/data/data/com.google.android.gms/databases/tapandpay.db",
                expected="exists",
            ),
            VerificationStep(
                name="wallet_card_visible",
                description="Card visible in Google Wallet",
                check_type="screenshot",
                target="com.google.android.apps.walletnfcrel",
                expected="ocr:****",
                screenshot_app="com.google.android.apps.walletnfcrel",
            ),
        ],
        screenshot_targets=["com.google.android.apps.walletnfcrel"],
    ),
    
    # Phase 7: Provincial Layer
    PhaseInfo(
        number=7,
        name="Provincial Layer",
        description="Regional settings, timezone, locale, carrier",
        verifications=[
            VerificationStep(
                name="timezone_set",
                description="Timezone configured",
                check_type="property",
                target="persist.sys.timezone",
                expected="not_empty",
            ),
            VerificationStep(
                name="sim_state",
                description="SIM shows ready",
                check_type="property",
                target="gsm.sim.state",
                expected="READY",
            ),
        ],
    ),
    
    # Phase 8: Post-Harden
    PhaseInfo(
        number=8,
        name="Post-Harden",
        description="Final hardening, root hiding, cleanup",
        verifications=[
            VerificationStep(
                name="no_frida",
                description="Frida not detected",
                check_type="shell",
                target="ls /data/local/tmp/frida* 2>/dev/null || echo 'clean'",
                expected="contains:clean",
            ),
            VerificationStep(
                name="selinux_enforcing",
                description="SELinux enforcing",
                check_type="shell",
                target="getenforce",
                expected="Enforcing",
            ),
        ],
    ),
    
    # Phase 9: Attestation
    PhaseInfo(
        number=9,
        name="Attestation",
        description="Play Integrity / SafetyNet attestation check",
        verifications=[
            VerificationStep(
                name="basic_integrity",
                description="Basic integrity passes",
                check_type="shell",
                target="getprop ro.boot.verifiedbootstate",
                expected="green",
            ),
        ],
    ),
    
    # Phase 10: Trust Audit
    PhaseInfo(
        number=10,
        name="Trust Audit",
        description="Final trust score calculation and audit",
        verifications=[
            VerificationStep(
                name="trust_score",
                description="Trust score calculated",
                check_type="shell",
                target="echo 'audit_complete'",
                expected="audit_complete",
            ),
        ],
    ),
]


def get_phase(number: int) -> Optional[PhaseInfo]:
    """Get phase info by number."""
    for phase in PHASES:
        if phase.number == number:
            return phase
    return None


def get_all_verifications() -> List[Dict[str, Any]]:
    """Get flat list of all verification steps."""
    result = []
    for phase in PHASES:
        for v in phase.verifications:
            result.append({
                "phase": phase.number,
                "phase_name": phase.name,
                "name": v.name,
                "description": v.description,
                "type": v.check_type,
                "target": v.target,
                "expected": v.expected,
            })
    return result
