"""
Genesis Unified — Single entrypoint for all device provisioning pipelines
==========================================================================

Consolidates 4 competing Genesis implementations into ONE unified interface:
  - vmos_genesis_v3.py (1,423 LOC) → VMOS Cloud with real OAuth tokens (PRIMARY)
  - vmos_genesis_engine.py (1,829 LOC) → Original VMOS API version (ALIASED)
  - unified_genesis_engine.py (1,639 LOC) → Local ADB + VMOS hybrid (LEGACY)
  - vmos_nexus_runner.py (755 LOC) → 4-phase simplified runner (TESTING)

This module provides a single factory function that automatically selects the
best implementation based on target device type.

USAGE:
```python
from genesis_unified import GenesisFactory

# VMOS Cloud device (recommended)
engine = GenesisFactory.create_vmos_cloud(ak="...", sk="...")
await engine.run_pipeline(config, pad_code="ACP250329...", on_update=callback)

# Local Cuttlefish device with ADB
engine = GenesisFactory.create_local_adb(adb_target="192.168.1.10:5555")
await engine.run_pipeline(config, job_id="myjob", on_update=callback)

# Simple 4-phase runner for testing
engine = GenesisFactory.create_simple(pad_code="ACP250329...")
await engine.run_pipeline_simple(config)
```

CONSOLIDATION PLAN:
- Phase 1: Import vmos_genesis_v3.py as primary VMOS engine
- Phase 2: Create aliases for vmos_genesis_engine.py (subsumed by V3)
- Phase 3: Keep unified_genesis_engine.py as LOCAL variant only
- Phase 4: vmos_nexus_runner.py becomes internal test harness
- Phase 5: DEPRECATE direct imports of individual engines
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable, Dict, Any
from dataclasses import dataclass
import logging

# Import the 4 genesis implementations
try:
    from vmos_genesis_v3 import VMOSGenesisV3, PipelineConfigV3
except ImportError:
    VMOSGenesisV3 = None
    PipelineConfigV3 = None

try:
    from vmos_genesis_engine import VMOSGenesisEngine, PipelineConfig as VMOSPipelineConfig
except ImportError:
    VMOSGenesisEngine = None
    VMOSPipelineConfig = None

try:
    from unified_genesis_engine import UnifiedGenesisEngine
except ImportError:
    UnifiedGenesisEngine = None

try:
    from vmos_nexus_runner import VMOSNexusRunner, NexusConfig
except ImportError:
    VMOSNexusRunner = None
    NexusConfig = None

logger = logging.getLogger("genesis.unified")


class GenesisFactory:
    """
    Factory for creating Genesis engine instances with automatic backend selection.
    
    RECOMMENDATION: Use create_vmos_cloud() for production (V3 Nexus with real tokens).
    """

    @staticmethod
    def create_vmos_cloud(
        ak: str,
        sk: str,
        region: str = "default",
        use_real_auth: bool = True,
    ) -> "GenesisVMOSCloud":
        """
        Create a VMOS Cloud Genesis engine (V3 Nexus — RECOMMENDED FOR PRODUCTION).
        
        Args:
            ak: VMOS Cloud API Access Key
            sk: VMOS Cloud API Secret Key
            region: VMOS region (default: "default")
            use_real_auth: Use real gpsoauth tokens vs synthetic (default: True)
            
        Returns:
            GenesisVMOSCloud instance
            
        Raises:
            ImportError: If vmos_genesis_v3 module not found
        """
        if VMOSGenesisV3 is None:
            raise ImportError(
                "vmos_genesis_v3 module not found. Install dependencies."
            )
        
        engine = VMOSGenesisV3(
            cloud_ak=ak,
            cloud_sk=sk,
            use_real_auth=use_real_auth,
        )
        return GenesisVMOSCloud(engine)

    @staticmethod
    def create_vmos_legacy(
        ak: str,
        sk: str,
    ) -> "GenesisVMOSCloud":
        """
        Create a VMOS Genesis engine using legacy implementation.
        (Subsumed by create_vmos_cloud() — provided for compatibility only)
        
        Args:
            ak: VMOS Cloud API Access Key
            sk: VMOS Cloud API Secret Key
            
        Returns:
            GenesisVMOSCloud instance wrapping legacy engine
            
        Raises:
            ImportError: If vmos_genesis_engine module not found
        """
        if VMOSGenesisEngine is None:
            raise ImportError(
                "vmos_genesis_engine module not found. Install dependencies."
            )
        
        engine = VMOSGenesisEngine(ak, sk)
        return GenesisVMOSCloud(engine)

    @staticmethod
    def create_local_adb(
        adb_target: str,
    ) -> "GenesisLocal":
        """
        Create a local ADB-based Genesis engine (for Cuttlefish, physical devices).
        
        Args:
            adb_target: ADB target (device serial or "host:port")
            
        Returns:
            GenesisLocal instance
            
        Raises:
            ImportError: If unified_genesis_engine module not found
        """
        if UnifiedGenesisEngine is None:
            raise ImportError(
                "unified_genesis_engine module not found. Install dependencies."
            )
        
        engine = UnifiedGenesisEngine(adb_target=adb_target)
        return GenesisLocal(engine)

    @staticmethod
    def create_simple(
        pad_code: str,
        ak: str,
        sk: str,
    ) -> "GenesisSimple":
        """
        Create a simplified 4-phase Genesis runner (testing/debugging only).
        
        Args:
            pad_code: VMOS pad code
            ak: VMOS Cloud API Access Key
            sk: VMOS Cloud API Secret Key
            
        Returns:
            GenesisSimple instance
            
        Raises:
            ImportError: If vmos_nexus_runner module not found
        """
        if VMOSNexusRunner is None:
            raise ImportError(
                "vmos_nexus_runner module not found. Install dependencies."
            )
        
        engine = VMOSNexusRunner(pad_code, ak, sk)
        return GenesisSimple(engine)


class GenesisVMOSCloud:
    """
    Unified interface for VMOS Cloud Genesis pipelines (V3 Nexus primary).
    
    Supports both real (V3 with gpsoauth) and legacy (original API) implementations.
    """

    def __init__(self, engine):
        """
        Initialize with either VMOSGenesisV3 or VMOSGenesisEngine.
        
        Args:
            engine: Genesis engine instance
        """
        self.engine = engine
        self.is_v3 = isinstance(engine, VMOSGenesisV3) if VMOSGenesisV3 else False

    async def run_pipeline(
        self,
        pad_code: str,
        config: Dict[str, Any],
        job_id: Optional[str] = None,
        on_update: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full Genesis pipeline on VMOS Cloud device.
        
        11 phases (V3 Nexus):
          0. Wipe/Stealth Detection Bypass
          1. Stealth Patch (26 vectors, 103+ checks)
          2. Network/Proxy Setup
          3. Device Profile Forge
          4. Google Account (real OAuth via gpsoauth if V3)
          5. ADB Injection (contacts, calls, SMS, WiFi, Chrome)
          6. Wallet (tapandpay.db, COIN.xml 8-flag zero-auth)
          7. Purchase History (library.db, Coherence Bridge)
          8. Post-Harden (iptables, AppOps, forensic dating)
          9. Attestation (keybox, Play Integrity simulator)
          10. Trust Audit (14-check scoring, ≥95 A+ target)
        
        Args:
            pad_code: VMOS pad code (device identifier)
            config: Pipeline configuration dictionary with:
              - name, email, phone, dob, ssn
              - street, city, state, zip, country
              - cc_number, cc_exp_month, cc_exp_year
              - use_real_auth (bool) — Use real gpsoauth tokens
              - age_days (int) — Device profile age in days
              - country (str) — Device country code
            job_id: Optional job UUID for tracking
            on_update: Optional callback(phase, status, message, percentage)
            
        Returns:
            Pipeline result dict with:
              - success: bool
              - phases: list of phase results
              - trust_score: int (0-100)
              - error: Optional error message
        """
        if self.is_v3:
            # V3 Nexus with real OAuth tokens
            return await self.engine.run_pipeline(
                config,
                pad_code=pad_code,
                job_id=job_id,
                on_update=on_update,
            )
        else:
            # Legacy engine (original VMOS API)
            return await self.engine.run_pipeline(
                config,
                job_id=job_id,
                on_update=on_update,
            )

    async def get_device_status(self, pad_code: str) -> Dict[str, Any]:
        """Get current VMOS device status and properties."""
        if hasattr(self.engine, "get_device_status"):
            return await self.engine.get_device_status(pad_code)
        return {"status": "unknown"}

    async def cancel_pipeline(self, job_id: str) -> bool:
        """Cancel an in-progress pipeline job."""
        if hasattr(self.engine, "cancel_job"):
            return await self.engine.cancel_job(job_id)
        return False


class GenesisLocal:
    """
    Unified interface for local ADB-based Genesis pipelines.
    
    For Cuttlefish VMs, physical Android devices, or local test targets.
    """

    def __init__(self, engine):
        """
        Initialize with UnifiedGenesisEngine.
        
        Args:
            engine: UnifiedGenesisEngine instance
        """
        self.engine = engine

    async def run_pipeline(
        self,
        config: Dict[str, Any],
        job_id: Optional[str] = None,
        on_update: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full Genesis pipeline on local ADB target.
        
        Same 11 phases as VMOS Cloud, adapted for ADB communication.
        
        Args:
            config: Pipeline configuration dictionary
            job_id: Optional job UUID
            on_update: Optional callback(phase, status, message, percentage)
            
        Returns:
            Pipeline result dict
        """
        return await self.engine.run_pipeline(
            config,
            job_id=job_id,
            on_update=on_update,
        )

    async def get_device_status(self) -> Dict[str, Any]:
        """Get current ADB device status."""
        if hasattr(self.engine, "get_device_status"):
            return await self.engine.get_device_status()
        return {"status": "unknown"}


class GenesisSimple:
    """
    Simplified 4-phase Genesis runner for testing and debugging.
    
    Lightweight alternative to full 11-phase pipeline.
    Phases:
      1. Stealth Patch
      4. Google Account + Wallet
      10. Trust Audit
    """

    def __init__(self, engine):
        """
        Initialize with VMOSNexusRunner.
        
        Args:
            engine: VMOSNexusRunner instance
        """
        self.engine = engine

    async def run_pipeline_simple(
        self,
        config: Dict[str, Any],
        on_update: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute simplified 4-phase pipeline.
        
        Args:
            config: Pipeline configuration dictionary
            on_update: Optional callback
            
        Returns:
            Pipeline result dict
        """
        if hasattr(self.engine, "run_pipeline"):
            return await self.engine.run_pipeline(config, on_update=on_update)
        elif hasattr(self.engine, "run_simple_pipeline"):
            return await self.engine.run_simple_pipeline(config, on_update=on_update)
        else:
            raise NotImplementedError("Engine does not support pipeline execution")


# ── DEPRECATION ALIASES ────────────────────────────────────────────────────

# For backwards compatibility: direct imports of individual engines should
# eventually be replaced with GenesisFactory.create_*()

def create_vmos_genesis_v3(ak: str, sk: str, **kwargs):
    """
    DEPRECATED: Use GenesisFactory.create_vmos_cloud() instead.
    
    Creates a V3 Nexus engine directly.
    """
    logger.warning(
        "create_vmos_genesis_v3() is deprecated. Use GenesisFactory.create_vmos_cloud()"
    )
    if VMOSGenesisEngineV3 is None:
        raise ImportError("vmos_genesis_v3 not available")
    return VMOSGenesisEngineV3(cloud_ak=ak, cloud_sk=sk, **kwargs)


def create_vmos_genesis_engine(ak: str, sk: str, **kwargs):
    """
    DEPRECATED: Use GenesisFactory.create_vmos_cloud() instead.
    
    Creates a legacy engine directly.
    """
    logger.warning(
        "create_vmos_genesis_engine() is deprecated. Use GenesisFactory.create_vmos_cloud()"
    )
    if VMOSGenesisEngine is None:
        raise ImportError("vmos_genesis_engine not available")
    return VMOSGenesisEngine(ak, sk, **kwargs)


if __name__ == "__main__":
    # Example usage
    print("Genesis Unified Factory")
    print("-" * 50)
    print("Available creators:")
    print("  - GenesisFactory.create_vmos_cloud() [PRIMARY]")
    print("  - GenesisFactory.create_local_adb()")
    print("  - GenesisFactory.create_simple()")
    print("-" * 50)
    print("Consolidation status: 4 engines → 1 unified interface")
