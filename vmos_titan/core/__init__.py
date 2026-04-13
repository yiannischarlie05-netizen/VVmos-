# Titan V13.0 — Core modules
"""
Core package exports for cleaner imports.
Usage:
    from core import AnomalyPatcher, ProfileInjector, AndroidProfileForge
    from vmos_titan.core.exceptions import TitanError, ADBConnectionError
    from vmos_titan.core.models import PatchPhase, JobStatus, DeviceState
    from vmos_titan.core.vmos_cloud_module import VMOSCloudBridge, VMOSDeviceModifier
    from vmos_titan.core.genesis_v3_optimized import GenesisV3OrchestrationOptimized
    from vmos_titan.core.turbo_pusher import VMOSTurboPusher
    from vmos_titan.core.osint_enricher import OsintEnricher
    from vmos_titan.core.stochastic_aging_engine import StochasticAgingEngine
    from vmos_titan.core.threeids_prewarmer import ThreeDSPrewarmer
"""

from vmos_titan.core.exceptions import (
    ADBCommandError,
    ADBConnectionError,
    DeviceNotFoundError,
    DeviceOfflineError,
    GAppsBootstrapError,
    InjectionError,
    PatchPhaseError,
    ProfileForgeError,
    ResetpropError,
    TitanError,
    WalletProvisionError,
)
from vmos_titan.core.vmos_cloud_module import (
    VMOSCloudBridge,
    VMOSConfig,
    VMOSDeviceModifier,
    VMOSInstance,
    VMOSResponse,
)
from vmos_titan.core.vmos_pro_bridge import VMOSProBridge

# Genesis V3 Optimized Modules
from vmos_titan.core.genesis_v3_optimized import GenesisV3OrchestrationOptimized
from vmos_titan.core.turbo_pusher import VMOSTurboPusher
from vmos_titan.core.osint_enricher import OsintEnricher
from vmos_titan.core.threeids_prewarmer import ThreeDSPrewarmer
from vmos_titan.core.vmos_pro_stealth_hardener import VMOSProStealthHardener
from vmos_titan.core.google_master_auth import GoogleMasterAuth, AuthMethod
from vmos_titan.core.vmos_db_builder import VMOSDbBuilder
from vmos_titan.core.tee_simulator import TEESimulator, AttestationMode, SecurityLevel
from vmos_titan.core.ucp_accessibility import UCPAccessibilityService
from vmos_titan.core.genesis_factory import (
    GenesisFactory,
    EngineType,
    GenesisCapability,
    create_genesis_engine,
    create_production_engine,
)
from vmos_titan.core.neighbor_data_importer import (
    NeighborDataImporter,
    import_neighbor_backup,
    NeighborDeviceData,
)

# Production Framework (NEW)
from vmos_titan.core.production_framework import (
    ProductionContext,
    RetryStrategy,
    RetryConfig,
    CircuitBreaker,
    RateLimiter,
    HealthMonitor,
    TelemetryCollector,
    VMOS_RATE_LIMITER,
    TELEMETRY,
)

# Genesis Production Engine (NEW - Unified 16-phase pipeline)
from vmos_titan.core.genesis_production_engine import (
    GenesisProductionEngine,
    GenesisConfig,
    GenesisResult,
    GenesisPhase,
    PHASE_DEFINITIONS,
)

# ML Evasion Engine (NEW - genesis-ml-evasion agent)
from vmos_titan.core.ml_evasion_engine import (
    BehavioralSynthesizer,
    FingerprintMorpher,
    RiskScoreManipulator,
    TouchEvent,
    DeviceFingerprint,
)

# Persistence Engine (NEW - genesis-persistence-engine agent)
from vmos_titan.core.persistence_engine import (
    PersistenceEngine,
    PersistenceVector,
    PersistenceResult,
    PersistenceStatus,
)

# Exfiltration Engine (NEW - genesis-exfiltration-worker agent)
from vmos_titan.core.exfiltration_engine import (
    ExfiltrationEngine,
    ExfilChannel,
    ExfilResult,
    DataCategory,
)

__all__ = [
    # Exceptions
    "ADBCommandError",
    "ADBConnectionError",
    "DeviceNotFoundError",
    "DeviceOfflineError",
    "GAppsBootstrapError",
    "InjectionError",
    "PatchPhaseError",
    "ProfileForgeError",
    "ResetpropError",
    "TitanError",
    "WalletProvisionError",
    # VMOS Cloud
    "VMOSCloudBridge",
    "VMOSConfig",
    "VMOSDeviceModifier",
    "VMOSInstance",
    "VMOSProBridge",
    "VMOSResponse",
    # Genesis V3 Core
    "GenesisV3OrchestrationOptimized",
    "VMOSTurboPusher",
    "OsintEnricher",
    "ThreeDSPrewarmer",
    "VMOSProStealthHardener",
    "GoogleMasterAuth",
    "AuthMethod",
    "VMOSDbBuilder",
    # 2026 Compliance Modules
    "TEESimulator",
    "AttestationMode",
    "SecurityLevel",
    "UCPAccessibilityService",
    # Genesis Factory
    "GenesisFactory",
    "EngineType",
    "GenesisCapability",
    "create_genesis_engine",
    "create_production_engine",
    # Neighbor Data Import
    "NeighborDataImporter",
    "import_neighbor_backup",
    "NeighborDeviceData",
    # Production Framework (NEW)
    "ProductionContext",
    "RetryStrategy",
    "RetryConfig",
    "CircuitBreaker",
    "RateLimiter",
    "HealthMonitor",
    "TelemetryCollector",
    "VMOS_RATE_LIMITER",
    "TELEMETRY",
    # Genesis Production Engine (NEW)
    "GenesisProductionEngine",
    "GenesisConfig",
    "GenesisResult",
    "GenesisPhase",
    "PHASE_DEFINITIONS",
    # ML Evasion Engine (NEW)
    "BehavioralSynthesizer",
    "FingerprintMorpher",
    "RiskScoreManipulator",
    "TouchEvent",
    "DeviceFingerprint",
    # Persistence Engine (NEW)
    "PersistenceEngine",
    "PersistenceVector",
    "PersistenceResult",
    "PersistenceStatus",
    # Exfiltration Engine (NEW)
    "ExfiltrationEngine",
    "ExfilChannel",
    "ExfilResult",
    "DataCategory",
]
