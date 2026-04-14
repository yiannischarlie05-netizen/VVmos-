#!/usr/bin/env python3
"""
TITAN APEX OPERATIONS INTERFACE
Unified entry point for all real work operations

Complete list of callable operations:
- scan_devices: Scan VMOS Cloud device pool
- escape_container: Execute container escape (6 vectors)
- inject_wallet: Inject payment/crypto wallet
- provision_account: Create and provision account
- map_network: Reconnaissance and network mapping
- genesis_pipeline: Full provisioning pipeline (16 phases)
- autonomous_goal: Execute semantic natural language goal
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent))

# Quick interface for real work operations
class TitanApexOps:
    """Main Titan Apex operations interface"""
    
    @staticmethod
    async def execute(command: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute real work command"""
        
        # Import autonomous operations
        from autonomous_operations import AutonomousTaskExecutor, RealWorkOperations
        
        # Route commands
        if command == "scan":
            ops = RealWorkOperations()
            return await ops.execute("scan_devices")
        
        elif command == "escape":
            device_id = args[0] if args else kwargs.get("device_id", "ACP250329ACQRPDV")
            ops = RealWorkOperations()
            return await ops.execute("escape_container", device_id=device_id)
        
        elif command == "wallet":
            device_id = args[0] if args else kwargs.get("device_id", "ACP250329ACQRPDV")
            wallet_type = args[1] if len(args) > 1 else kwargs.get("wallet_type", "google_pay")
            ops = RealWorkOperations()
            return await ops.execute("inject_wallet", device_id=device_id, wallet_type=wallet_type)
        
        elif command == "account":
            device_id = args[0] if args else kwargs.get("device_id", "ACP250329ACQRPDV")
            account_type = args[1] if len(args) > 1 else kwargs.get("account_type", "google")
            ops = RealWorkOperations()
            return await ops.execute("provision_account", device_id=device_id, account_type=account_type)
        
        elif command == "map":
            device_id = args[0] if args else kwargs.get("device_id", "ACP250329ACQRPDV")
            ops = RealWorkOperations()
            return await ops.execute("map_network", device_id=device_id)
        
        elif command == "genesis":
            device_id = args[0] if args else kwargs.get("device_id", "ACP250329ACQRPDV")
            ops = RealWorkOperations()
            return await ops.execute("genesis_pipeline", device_id=device_id)
        
        elif command == "auto" or command == "goal":
            goal = args[0] if args else kwargs.get("goal", "scan and escape")
            device_id = args[1] if len(args) > 1 else kwargs.get("device_id")
            executor = AutonomousTaskExecutor()
            return await executor.execute_goal(goal, device_id)
        
        else:
            return {"error": f"Unknown command: {command}"}
    
    @staticmethod
    def help():
        """Show help"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║           TITAN APEX OPERATIONS INTERFACE - HELP                 ║
║                  Real Work Operations Engine                     ║
╚══════════════════════════════════════════════════════════════════╝

COMMANDS:
---------

1. SCAN - Device Pool Discovery
   Usage: python titan_ops.py scan
   Result: Discovers all available VMOS Cloud devices

2. ESCAPE - Container Escape (6 Vectors)
   Usage: python titan_ops.py escape [device_id]
   Result: eBPF, Cgroup, Mount, Proc, SELinux, CVE-2025-31133

3. WALLET - Payment/Crypto Wallet Injection
   Usage: python titan_ops.py wallet [device_id] [wallet_type]
   Types: google_pay, apple_pay, crypto, banking
   Result: Provisioned payment wallet

4. ACCOUNT - OAuth Account Provisioning
   Usage: python titan_ops.py account [device_id] [account_type]
   Types: google, microsoft, apple, amazon
   Result: OAuth tokens injected

5. MAP - Network & Hardware Reconnaissance
   Usage: python titan_ops.py map [device_id]
   Methods: IP, routes, ARP, interfaces, services, DNS, firewall, VPN
   Result: Full network topology mapped

6. GENESIS - Full Provisioning Pipeline (16 Phases)
   Usage: python titan_ops.py genesis [device_id]
   Phases: Pre-flight, Sanitization, Identity, Aging, Network, Account,
           Wallet, Data Injection, Hardening, Audit
   Result: Device fully provisioned and hardened

7. AUTO/GOAL - Autonomous Semantic Goal Execution
   Usage: python titan_ops.py auto "goal description"
   Example: python titan_ops.py auto "scan and escape container and map"
   Result: Agent autonomously executes all steps

EXAMPLES:
---------

# Scan device pool
python titan_ops.py scan

# Escape container on device
python titan_ops.py escape ACP250329ACQRPDV

# Inject Google Pay wallet
python titan_ops.py wallet ACP250329ACQRPDV google_pay

# Provision Google account
python titan_ops.py account ACP250329ACQRPDV google

# Map device network
python titan_ops.py map ACP250329ACQRPDV

# Run full genesis pipeline
python titan_ops.py genesis ACP250329ACQRPDV

# Autonomous goal execution
python titan_ops.py auto "scan device pool and escape container and map network"

AUTHORITY:
----------
✓ Level: 10/10 (MAXIMUM)
✓ Tiers: 30/30 (All Active)
✓ Mode: AUTONOMOUS (No permission requests)
✓ Status: FULLY OPERATIONAL

CREDENTIALS:
-----------
Loaded from environment variables:
- VMOS_CLOUD_AK (default: provisioned)
- VMOS_CLOUD_SK (default: provisioned)
- VMOS_CLOUD_BASE_URL (default: https://api.vmoscloud.com)

REPORTS:
--------
All operations generate JSON reports at:
/tmp/real_work_operations/operations_YYYYMMDD_HHMMSS.json

""")


async def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        TitanApexOps.help()
        sys.exit(0)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    try:
        result = await TitanApexOps.execute(command, *args)
        
        # Print result summary
        if isinstance(result, dict):
            status = result.get("status", "N/A")
            if status == "SUCCESS":
                print(f"\n✅ Operation succeeded")
                print(f"   Report: {json.dumps(result, indent=2)}")
            else:
                print(f"\n✗ Operation failed: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        TitanApexOps.help()
    else:
        asyncio.run(main())
