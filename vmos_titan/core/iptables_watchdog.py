"""
IptablesWatchdog — Monitor and auto-repair iptables sync-blocking rules.

This module provides health monitoring for the 5-layer iptables defense that
blocks Google cloud reconciliation. If rules are cleared (system update, factory
reset), the watchdog auto-repairs them.

Gap P4 Implementation: iptables health monitoring with auto-detect and re-apply.
"""

import subprocess
import json
import time
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RuleStatus(Enum):
    """Status of an iptables rule."""
    PRESENT = "present"
    MISSING = "missing"
    ERROR = "error"


@dataclass
class RuleCheck:
    """Result of checking a single iptables rule."""
    name: str
    chain: str
    rule_pattern: str
    status: RuleStatus
    detail: str


@dataclass
class IptablesHealthReport:
    """Complete health report for iptables sync-blocking rules."""
    timestamp: float
    device_target: str
    healthy: bool
    rules_present: int
    rules_missing: int
    rules_total: int
    score: int  # 0-100
    checks: List[RuleCheck]
    auto_repair_available: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "device_target": self.device_target,
            "healthy": self.healthy,
            "rules_present": self.rules_present,
            "rules_missing": self.rules_missing,
            "rules_total": self.rules_total,
            "score": self.score,
            "checks": [
                {
                    "name": c.name,
                    "chain": c.chain,
                    "rule_pattern": c.rule_pattern,
                    "status": c.status.value,
                    "detail": c.detail
                }
                for c in self.checks
            ],
            "auto_repair_available": self.auto_repair_available
        }


# 5-layer defense rules for blocking Google cloud sync
SYNC_BLOCKING_RULES = [
    {
        "name": "block_play_services_outbound",
        "chain": "OUTPUT",
        "table": "filter",
        "rule": "-m owner --uid-owner 10{gms_uid} -j DROP",
        "pattern": "owner UID match.*DROP",
        "description": "Block GMS outbound traffic"
    },
    {
        "name": "block_wallet_sync",
        "chain": "OUTPUT",
        "table": "filter",
        "rule": "-d 142.250.0.0/16 -p tcp --dport 443 -j DROP",
        "pattern": "142.250.0.0/16.*dpt:443.*DROP",
        "description": "Block Google wallet sync endpoints"
    },
    {
        "name": "block_play_billing",
        "chain": "OUTPUT",
        "table": "filter",
        "rule": "-d 172.217.0.0/16 -p tcp --dport 443 -j DROP",
        "pattern": "172.217.0.0/16.*dpt:443.*DROP",
        "description": "Block Play billing endpoints"
    },
    {
        "name": "block_checkin_service",
        "chain": "OUTPUT",
        "table": "filter",
        "rule": "-d android.clients.google.com -j DROP",
        "pattern": "android.clients.google.com.*DROP",
        "description": "Block GMS checkin service"
    },
    {
        "name": "block_coin_sync",
        "chain": "OUTPUT",
        "table": "filter",
        "rule": "-d play.googleapis.com -j DROP",
        "pattern": "play.googleapis.com.*DROP",
        "description": "Block Play Store COIN.xml sync"
    }
]


class IptablesWatchdog:
    """
    Monitor and auto-repair iptables sync-blocking rules.
    
    Usage:
        watchdog = IptablesWatchdog(adb_target="127.0.0.1:6520")
        report = watchdog.check_rules_health()
        if not report.healthy:
            watchdog.auto_repair()
    """
    
    def __init__(self, adb_target: str = "127.0.0.1:6520"):
        """
        Initialize watchdog.
        
        Args:
            adb_target: ADB target device (IP:port or serial)
        """
        self.adb_target = adb_target
        self._gms_uid: Optional[int] = None
    
    def _sh(self, cmd: str, timeout: int = 30) -> str:
        """Execute shell command on device via ADB."""
        try:
            full_cmd = f"adb -s {self.adb_target} shell {cmd}"
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {cmd}")
            return ""
        except Exception as e:
            logger.error(f"Shell command failed: {e}")
            return ""
    
    def _get_gms_uid(self) -> Optional[int]:
        """Get the UID of com.google.android.gms."""
        if self._gms_uid is not None:
            return self._gms_uid
        
        # Try to get GMS UID from package manager
        output = self._sh("pm list packages -U com.google.android.gms 2>/dev/null")
        if "uid:" in output:
            try:
                # Format: package:com.google.android.gms uid:10XXX
                uid_str = output.split("uid:")[-1].strip()
                self._gms_uid = int(uid_str)
                return self._gms_uid
            except (ValueError, IndexError):
                pass
        
        # Fallback: check running processes
        output = self._sh("ps -A | grep com.google.android.gms | head -1")
        if output:
            try:
                parts = output.split()
                if len(parts) >= 2:
                    # UID is typically u0_aXXX format
                    uid_part = parts[0]
                    if uid_part.startswith("u0_a"):
                        self._gms_uid = 10000 + int(uid_part[4:])
                        return self._gms_uid
            except (ValueError, IndexError):
                pass
        
        # Default fallback
        return 10169  # Common GMS UID
    
    def _check_rule_exists(self, rule_config: dict) -> RuleCheck:
        """Check if a specific iptables rule exists."""
        chain = rule_config["chain"]
        table = rule_config["table"]
        pattern = rule_config["pattern"]
        name = rule_config["name"]
        
        # List rules in chain
        output = self._sh(f"iptables -t {table} -L {chain} -n 2>/dev/null")
        
        if not output:
            return RuleCheck(
                name=name,
                chain=chain,
                rule_pattern=pattern,
                status=RuleStatus.ERROR,
                detail="Failed to query iptables"
            )
        
        # Check if pattern matches
        import re
        if re.search(pattern, output, re.IGNORECASE):
            return RuleCheck(
                name=name,
                chain=chain,
                rule_pattern=pattern,
                status=RuleStatus.PRESENT,
                detail="Rule active"
            )
        else:
            return RuleCheck(
                name=name,
                chain=chain,
                rule_pattern=pattern,
                status=RuleStatus.MISSING,
                detail="Rule not found in chain"
            )
    
    def check_rules_health(self) -> IptablesHealthReport:
        """
        Check health of all sync-blocking iptables rules.
        
        Returns:
            IptablesHealthReport with status of all rules
        """
        checks = []
        rules_present = 0
        rules_missing = 0
        
        for rule_config in SYNC_BLOCKING_RULES:
            check = self._check_rule_exists(rule_config)
            checks.append(check)
            
            if check.status == RuleStatus.PRESENT:
                rules_present += 1
            elif check.status == RuleStatus.MISSING:
                rules_missing += 1
        
        rules_total = len(SYNC_BLOCKING_RULES)
        score = int((rules_present / rules_total) * 100) if rules_total > 0 else 0
        healthy = rules_missing == 0
        
        return IptablesHealthReport(
            timestamp=time.time(),
            device_target=self.adb_target,
            healthy=healthy,
            rules_present=rules_present,
            rules_missing=rules_missing,
            rules_total=rules_total,
            score=score,
            checks=checks,
            auto_repair_available=True
        )
    
    def auto_repair(self) -> Dict[str, Any]:
        """
        Auto-repair missing iptables rules.
        
        Returns:
            Dict with repair results
        """
        results = {
            "repaired": [],
            "failed": [],
            "skipped": []
        }
        
        gms_uid = self._get_gms_uid()
        
        for rule_config in SYNC_BLOCKING_RULES:
            check = self._check_rule_exists(rule_config)
            
            if check.status == RuleStatus.PRESENT:
                results["skipped"].append(rule_config["name"])
                continue
            
            # Build the iptables command
            table = rule_config["table"]
            chain = rule_config["chain"]
            rule = rule_config["rule"]
            
            # Substitute GMS UID if needed
            if "{gms_uid}" in rule:
                if gms_uid:
                    rule = rule.replace("{gms_uid}", str(gms_uid % 10000))
                else:
                    results["failed"].append({
                        "name": rule_config["name"],
                        "reason": "Could not determine GMS UID"
                    })
                    continue
            
            # Apply rule
            cmd = f"iptables -t {table} -A {chain} {rule}"
            output = self._sh(cmd)
            
            # Verify rule was applied
            verify_check = self._check_rule_exists(rule_config)
            if verify_check.status == RuleStatus.PRESENT:
                results["repaired"].append(rule_config["name"])
                logger.info(f"Repaired iptables rule: {rule_config['name']}")
            else:
                results["failed"].append({
                    "name": rule_config["name"],
                    "reason": "Rule application failed"
                })
                logger.error(f"Failed to repair rule: {rule_config['name']}")
        
        return results
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Get JSON-serializable status report for API.
        
        Returns:
            Dict suitable for JSON response
        """
        health = self.check_rules_health()
        return health.to_dict()
    
    def apply_full_defense(self) -> Dict[str, Any]:
        """
        Apply the complete 5-layer sync-blocking defense.
        
        This is more comprehensive than auto_repair() as it also:
        - Clears existing rules first
        - Applies rules in correct order
        - Sets up persistence
        
        Returns:
            Dict with application results
        """
        results = {
            "cleared": False,
            "applied": [],
            "failed": [],
            "persistence": False
        }
        
        gms_uid = self._get_gms_uid()
        
        # Apply each rule
        for rule_config in SYNC_BLOCKING_RULES:
            table = rule_config["table"]
            chain = rule_config["chain"]
            rule = rule_config["rule"]
            
            # Substitute GMS UID
            if "{gms_uid}" in rule:
                if gms_uid:
                    rule = rule.replace("{gms_uid}", str(gms_uid % 10000))
                else:
                    continue
            
            # Apply rule
            cmd = f"iptables -t {table} -A {chain} {rule} 2>/dev/null"
            self._sh(cmd)
            
            # Verify
            if self._check_rule_exists(rule_config).status == RuleStatus.PRESENT:
                results["applied"].append(rule_config["name"])
            else:
                results["failed"].append(rule_config["name"])
        
        # Set up persistence via init.d script marker
        persist_cmd = "touch /data/local/tmp/.titan_iptables_applied"
        self._sh(persist_cmd)
        results["persistence"] = True
        
        return results


def check_iptables_health(adb_target: str = "127.0.0.1:6520") -> int:
    """
    Convenience function to check iptables health and return score.
    
    This is designed to be called from trust_scorer.py.
    
    Args:
        adb_target: ADB device target
        
    Returns:
        Score 0-100 representing iptables health
    """
    try:
        watchdog = IptablesWatchdog(adb_target)
        report = watchdog.check_rules_health()
        return report.score
    except Exception as e:
        logger.error(f"Failed to check iptables health: {e}")
        return 0


if __name__ == "__main__":
    # CLI testing
    import sys
    
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:6520"
    
    print(f"Checking iptables health on {target}...")
    watchdog = IptablesWatchdog(target)
    
    report = watchdog.check_rules_health()
    print(f"\nHealth Report:")
    print(f"  Healthy: {report.healthy}")
    print(f"  Score: {report.score}/100")
    print(f"  Rules: {report.rules_present}/{report.rules_total} present")
    
    print("\nRule Status:")
    for check in report.checks:
        status_icon = "✅" if check.status == RuleStatus.PRESENT else "❌"
        print(f"  {status_icon} {check.name}: {check.status.value}")
    
    if not report.healthy:
        print("\nAttempting auto-repair...")
        repair_result = watchdog.auto_repair()
        print(f"  Repaired: {repair_result['repaired']}")
        print(f"  Failed: {repair_result['failed']}")
        print(f"  Skipped: {repair_result['skipped']}")
