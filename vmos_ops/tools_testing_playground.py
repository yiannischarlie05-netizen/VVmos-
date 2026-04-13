#!/usr/bin/env python3
"""
EXTREME ANDROID TOOLS TESTING PLAYGROUND
=========================================
Test suite for all tools mentioned in Titan-X arsenal on VMOS Pro devices.
Targets: OnePlus devices in VMOS Pro Cloud
Date: March 31, 2026
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import subprocess
import logging

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / "vmos_titan" / "core"))

from vmos_cloud_api import VMOSCloudClient
from adb_utils import adb_shell, ensure_adb_root, adb_with_retry
from json_logger import configure_all_loggers

# Configure logging
configure_all_loggers()
logger = logging.getLogger("tools_playground")

# ═══════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS & DETECTION METHODS
# ═══════════════════════════════════════════════════════════════════════

TOOL_MANIFEST = {
    "TIER_1_STATIC_ANALYSIS": {
        "JADX": {
            "category": "Decompilation",
            "priority": "P0_Essential",
            "detection": "Check for JADX binary availability",
            "command": "which jadx || jadx -version",
            "stealth": "N/A (offline)",
        },
        "Androguard": {
            "category": "Static Analysis",
            "priority": "P0_Essential",
            "detection": "Python import + version",
            "command": "python3 -c 'from androguard.misc import AnalyzeAPK; print(\"✓ Androguard available\")'",
            "stealth": "N/A (offline)",
        },
        "APKiD": {
            "category": "Protection Detection",
            "priority": "P0_Essential",
            "detection": "CLI tool check",
            "command": "apkid --version",
            "stealth": "N/A (offline)",
        },
        "APKLeaks": {
            "category": "Secret Extraction",
            "priority": "P0_Essential",
            "detection": "CLI tool availability",
            "command": "which apkleaks",
            "stealth": "N/A (offline)",
        },
        "semgrep": {
            "category": "Custom Patterns",
            "priority": "P1_Important",
            "detection": "Python package + rules",
            "command": "semgrep --version",
            "stealth": "N/A (offline)",
        },
        "MobSF": {
            "category": "Automated Scanning",
            "priority": "P1_Important",
            "detection": "Docker container / API endpoint",
            "command": "docker ps | grep -i mobsf || echo 'MobSF not running - can start'",
            "stealth": "N/A (controlled env)",
        },
    },
    "TIER_2_DYNAMIC_HOOKING": {
        "Frida": {
            "category": "Runtime Hooking",
            "priority": "P0_Essential",
            "detection": "Frida server on device + gadget",
            "command": "frida --version; adb shell 'ps aux | grep frida'",
            "stealth": "HIGH (kernel-space capable)",
            "validation": "frida -U --list-devices",
        },
        "Objection": {
            "category": "Interactive Frida",
            "priority": "P1_Important",
            "detection": "Objection CLI + Frida dependency",
            "command": "objection --version",
            "stealth": "HIGH (Frida-based)",
            "dependency": "Frida",
        },
        "Drozer": {
            "category": "Component Testing",
            "priority": "P1_Important",
            "detection": "Drozer agent APK + console",
            "command": "drozer --version || echo 'Install from GitHub'",
            "stealth": "MEDIUM (requires agent APK)",
        },
        "Xposed/LSPosed": {
            "category": "Method Hooking",
            "priority": "P2_Advanced",
            "detection": "apmt CLI + module framework",
            "command": "adb shell 'which apmt' || echo 'Not installed'",
            "stealth": "VERY HIGH (systemless)",
            "note": "VMOS-specific via apmt",
        },
        "KernelSU": {
            "category": "Kernel Root",
            "priority": "P2_Advanced",
            "detection": "ksu binary + module API",
            "command": "adb shell 'which ksu' || adb shell 'su -V 2>/dev/null'",
            "stealth": "ULTRA-HIGH (kernel-space)",
        },
    },
    "TIER_3_NETWORK_INTERCEPTION": {
        "mitmproxy": {
            "category": "HTTPS Interception",
            "priority": "P0_Essential",
            "detection": "Service running + CA cert installed",
            "command": "pgrep -f mitmproxy || echo 'Not running'",
            "stealth": "HIGH (system CA cert)",
        },
        "Wireshark/tshark": {
            "category": "Packet Capture",
            "priority": "P1_Important",
            "detection": "tshark CLI tool",
            "command": "tshark --version",
            "stealth": "HIGH (host-side)",
        },
        "Burp Suite": {
            "category": "Web Security",
            "priority": "P1_Important",
            "detection": "Burp binary + port listener",
            "command": "which burpsuite || echo 'Commercial tool'",
            "stealth": "HIGH (system CA cert)",
        },
        "Charles Proxy": {
            "category": "Traffic Monitoring",
            "priority": "P2_Advanced",
            "detection": "Charles daemon + CA cert",
            "command": "pgrep charles || echo 'Not installed'",
            "stealth": "HIGH (system CA cert)",
        },
    },
    "TIER_4_BINARY_PATCHING": {
        "apktool": {
            "category": "APK Disassembly",
            "priority": "P0_Essential",
            "detection": "apktool binary",
            "command": "apktool --version",
            "stealth": "HIGH (if re-applied obfuscation)",
        },
        "smali/baksmali": {
            "category": "Dalvik Assembly",
            "priority": "P1_Important",
            "detection": "smali/baksmali JARs",
            "command": "which smali && which baksmali || echo 'Check /opt/smali/'",
            "stealth": "HIGH",
        },
        "Frida Gadget": {
            "category": "Persistent Hooking",
            "priority": "P2_Advanced",
            "detection": "Gadget .so embedded in APK",
            "command": "echo 'Detectable via strings gadget.so'",
            "stealth": "VERY HIGH",
        },
        "apksigner": {
            "category": "APK Signing",
            "priority": "P0_Essential",
            "detection": "apksigner CLI tool",
            "command": "apksigner --version || which apksigner",
            "stealth": "N/A",
        },
    },
    "TIER_5_ROOT_HIDING_EVASION": {
        "Magisk": {
            "category": "Systemless Root",
            "priority": "P0_Essential",
            "detection": "magisk binary + DenyList",
            "command": "adb shell 'magisk --version' || echo 'Not installed'",
            "stealth": "VERY HIGH",
            "vmos_check": "adb shell 'ls /data/adb/magisk'",
        },
        "Play Integrity Fix": {
            "category": "Attestation Bypass",
            "priority": "P1_Important",
            "detection": "Magisk module status",
            "command": "adb shell 'ls /data/adb/modules/ | grep -i integrity'",
            "stealth": "VERY HIGH",
            "dependency": "Magisk",
        },
        "Shamiko": {
            "category": "Hide Replacement",
            "priority": "P2_Advanced",
            "detection": "KernelSU module list",
            "command": "adb shell 'ls /data/adb/modules/shamiko'",
            "stealth": "VERY HIGH",
        },
    },
    "TIER_6_ADVANCED_REVERSING": {
        "Ghidra": {
            "category": "Binary Analysis",
            "priority": "P1_Important",
            "detection": "Ghidra installation + JDK",
            "command": "ghidraRun -version 2>/dev/null || echo 'Not installed'",
            "stealth": "N/A (offline)",
        },
        "radare2": {
            "category": "Binary Framework",
            "priority": "P1_Important",
            "detection": "r2 CLI tool",
            "command": "r2 -version",
            "stealth": "N/A (offline)",
        },
        "angr": {
            "category": "Symbolic Execution",
            "priority": "P2_Advanced",
            "detection": "Python module + Z3/Z3.py",
            "command": "python3 -c 'import angr; print(\"angr available\")'",
            "stealth": "N/A (offline)",
        },
        "Triton": {
            "category": "Symbolic Execution",
            "priority": "P2_Advanced",
            "detection": "Triton library + Pin",
            "command": "python3 -c 'from triton import *; print(\"Triton available\")'",
            "stealth": "N/A (offline)",
        },
    },
    "TIER_7_CRYPTOGRAPHIC_ATTACKS": {
        "Fault Injection Lab": {
            "category": "DFA/Glitch Board",
            "priority": "P3_Extreme",
            "detection": "Hardware glitch board + serial",
            "command": "ls /dev/ttyUSB* | head -1",
            "stealth": "ZERO (hardware-level)",
            "hardware": "ChipWhisperer / PicoEMP",
        },
        "Cache Timing (aflush)": {
            "category": "Side-Channel",
            "priority": "P3_Extreme",
            "detection": "RDTSC capability on CPU",
            "command": "python3 -c 'import sys; print(\"avx\" in open(\"/proc/cpuinfo\").read())'",
            "stealth": "LOW (timing variance)",
        },
    },
    "TIER_8_PERSISTENCE": {
        "Bootloader Rootkit": {
            "category": "Permanent Persistence",
            "priority": "P3_Extreme",
            "detection": "JTAG port + flasher board",
            "command": "echo 'Requires physical hardware access'",
            "stealth": "ZERO (boots first)",
            "hardware": "CH341A / RPi GPIO",
        },
        "Kernel Module": {
            "category": "LKM Persistence",
            "priority": "P2_Advanced",
            "detection": "lsmod output + dmesg logs",
            "command": "adb shell 'lsmod | grep titan'",
            "stealth": "MEDIUM (dmesg logs)",
        },
        "SELinux Policy Inject": {
            "category": "Policy-Level Persistence",
            "priority": "P2_Advanced",
            "detection": "getenforce + policy audit",
            "command": "adb shell 'getenforce'",
            "stealth": "MEDIUM (policy diff)",
        },
    },
    "TIER_9_BEHAVIORAL_EVASION": {
        "LSTM Behavior Cloning": {
            "category": "AI Mimicry",
            "priority": "P2_Advanced",
            "detection": "ML model + behavior synthesis",
            "command": "python3 -c 'import torch; print(\"PyTorch available\")'",
            "stealth": "HIGH (statistical)",
        },
        "RNN Event Generator": {
            "category": "Temporal Synthesis",
            "priority": "P2_Advanced",
            "detection": "TensorFlow/PyTorch models",
            "command": "python3 -c 'import tensorflow; print(\"TensorFlow available\")'",
            "stealth": "HIGH",
        },
    },
    "TIER_10_CORELLIUM": {
        "Corellium Cloud": {
            "category": "Virtualized Testing",
            "priority": "P1_Important",
            "detection": "Corellium API + credentials",
            "command": "echo 'Check $CORELLIUM_TOKEN'",
            "stealth": "MAXIMUM (hypervisor-level)",
            "env_var": "CORELLIUM_TOKEN",
        },
    },
}

# ═══════════════════════════════════════════════════════════════════════
# VMOS CLOUD DEVICE DETECTION & QUERYING
# ═══════════════════════════════════════════════════════════════════════

class VMOSProDeviceDetector:
    """Detect and list available VMOS Pro devices (OnePlus focus)"""
    
    def __init__(self):
        self.client = VMOSCloudClient()
        self.devices = []
        
    async def list_devices(self) -> List[Dict]:
        """List all available VMOS Pro devices from cloud"""
        try:
            response = await self.client.instance_list()
            print(f"[✓] VMOS Cloud API Response: {len(response)} devices")
            self.devices = response
            return response
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
            return []
    
    async def find_oneplus_devices(self) -> List[Dict]:
        """Filter for OnePlus devices"""
        oneplus = []
        for device in self.devices:
            # Handle both dict and string responses
            if isinstance(device, dict):
                device_str = json.dumps(device).lower()
                device_name = device.get('alias', str(device))
            else:
                device_str = str(device).lower()
                device_name = str(device)
            
            if any(model in device_str for model in ["oneplus", "op", "ace", "note"]):
                oneplus.append(device)
                print(f"[✓] Found OnePlus: {device_name}")
        return oneplus
    
    async def get_device_specs(self, pad_code: str) -> Dict:
        """Get detailed specs for one device"""
        try:
            # Query device properties
            result = await self.client.instance_list()
            for dev in result:
                if dev.get("padCode") == pad_code:
                    return dev
        except Exception as e:
            logger.error(f"Failed to get device specs: {e}")
        return {}

# ═══════════════════════════════════════════════════════════════════════
# TOOL TESTING ENGINE
# ═══════════════════════════════════════════════════════════════════════

class ToolValidationEngine:
    """Test each tool for presence, functionality, and stealth level"""
    
    def __init__(self):
        self.results = {}
        self.report = []
        
    def test_local_tool(self, tool_name: str, command: str) -> Dict:
        """Test if tool is available on host"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            status = "✓ AVAILABLE" if result.returncode == 0 else "⚠ PARTIAL"
            output = result.stdout[:100] if result.stdout else result.stderr[:100]
            return {
                "status": status,
                "output": output,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"status": "⏱ TIMEOUT", "output": "Command took >5s"}
        except Exception as e:
            return {"status": "✗ NOT FOUND", "error": str(e)}
    
    async def test_on_device(self, device_id: str, tool_name: str, command: str) -> Dict:
        """Test if tool is available on VMOS device via ADB"""
        try:
            output = adb_shell(device_id, command, timeout=10)
            if "not found" in output.lower() or output.strip() == "":
                return {"status": "✗ NOT INSTALLED", "device": device_id}
            return {"status": "✓ AVAILABLE", "device": device_id, "output": output[:100]}
        except Exception as e:
            return {"status": "✗ ERROR", "device": device_id, "error": str(e)}
    
    def generate_report(self) -> str:
        """Generate comprehensive tool availability report"""
        report = []
        report.append("=" * 80)
        report.append("EXTREME ANDROID TOOLS TESTING REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)
        report.append("")
        
        for tier, tools in TOOL_MANIFEST.items():
            report.append(f"\n{tier}")
            report.append("-" * 60)
            
            for tool_name, tool_info in tools.items():
                category = tool_info.get("category", "")
                priority = tool_info.get("priority", "")
                stealth = tool_info.get("stealth", "N/A")
                status = self.results.get(tool_name, {}).get("status", "NOT TESTED")
                
                report.append(f"\n  [{status}] {tool_name:20} | {category:20} | {priority}")
                report.append(f"      Stealth: {stealth}")
                
                if tool_name in self.results:
                    result = self.results[tool_name]
                    if "output" in result:
                        report.append(f"      Output: {result['output'][:60]}")
                    if "error" in result:
                        report.append(f"      Error: {result['error'][:60]}")
        
        report.append("\n" + "=" * 80)
        report.append("SUMMARY BY TIER")
        report.append("=" * 80)
        
        tier_stats = {}
        for tool_name, result in self.results.items():
            status = result.get("status", "NOT TESTED")
            for tier, tools in TOOL_MANIFEST.items():
                if tool_name in tools:
                    if tier not in tier_stats:
                        tier_stats[tier] = {"available": 0, "total": 0}
                    tier_stats[tier]["total"] += 1
                    if "AVAILABLE" in status or "PARTIAL" in status:
                        tier_stats[tier]["available"] += 1
        
        for tier, stats in tier_stats.items():
            pct = (stats["available"] / stats["total"] * 100) if stats["total"] > 0 else 0
            report.append(f"{tier:30}: {stats['available']}/{stats['total']} ({pct:.0f}%)")
        
        return "\n".join(report)

# ═══════════════════════════════════════════════════════════════════════
# MAIN TESTING ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════

class PlaygroundOrchestrator:
    """Main test coordinator"""
    
    def __init__(self):
        self.detector = VMOSProDeviceDetector()
        self.validator = ToolValidationEngine()
        self.test_results = {}
        
    async def run_all_tests(self):
        """Execute complete testing suite"""
        
        print("\n" + "=" * 80)
        print("EXTREME TOOLS TESTING PLAYGROUND - INITIALIZATION")
        print("=" * 80)
        
        # Step 1: List available devices
        print("\n[1/5] Detecting VMOS Pro devices...")
        devices = await self.detector.list_devices()
        print(f"      Found {len(devices)} total devices")
        
        # Parse device responses (may be strings or dicts)
        parsed_devices = []
        for dev in devices:
            if isinstance(dev, dict):
                parsed_devices.append(dev)
            elif isinstance(dev, str):
                try:
                    parsed_devices.append(json.loads(dev))
                except:
                    parsed_devices.append({"raw": dev})
        
        self.detector.devices = parsed_devices
        
        oneplus_devices = await self.detector.find_oneplus_devices()
        if oneplus_devices:
            print(f"      {len(oneplus_devices)} OnePlus device(s) available")
            target_device = oneplus_devices[0]
            if isinstance(target_device, dict):
                target_pad = target_device.get("padCode")
                target_alias = target_device.get('alias', 'OnePlus')
            else:
                target_pad = str(target_device)
                target_alias = "Unknown"
            print(f"      → Target device: {target_alias} ({target_pad})")
        else:
            print("      ⚠ No OnePlus devices found, will test with any available device")
            target_device = parsed_devices[0] if parsed_devices else None
            if target_device and isinstance(target_device, dict):
                target_pad = target_device.get("padCode")
            else:
                target_pad = str(target_device) if target_device else None
        
        # Step 2: Test local tools (host)
        print("\n[2/5] Testing local tools on host...")
        for tier, tools in TOOL_MANIFEST.items():
            for tool_name, tool_info in tools.items():
                if tool_info.get("stealth") == "N/A (offline)" or "version" in tool_info.get("command", ""):
                    result = self.validator.test_local_tool(
                        tool_name,
                        tool_info["command"]
                    )
                    self.validator.results[tool_name] = result
                    status_icon = "✓" if "AVAILABLE" in result["status"] else "✗"
                    print(f"      {status_icon} {tool_name:20} {result['status']}")
        
        # Step 3: Test on VMOS device (if available)
        if target_pad:
            print(f"\n[3/5] Testing tools on device: {target_pad}...")
            try:
                ensure_adb_root(target_pad)
                
                # Test Frida
                result = await self.validator.test_on_device(
                    target_pad,
                    "Frida",
                    "ps aux | grep frida-server"
                )
                print(f"      Frida-server status: {result['status']}")
                
                # Test Magisk
                result = await self.validator.test_on_device(
                    target_pad,
                    "Magisk",
                    "ls /data/adb/magisk.db"
                )
                print(f"      Magisk status: {result['status']}")
                
                # Test Play Integrity Fix module
                result = await self.validator.test_on_device(
                    target_pad,
                    "Play Integrity Fix",
                    "ls /data/adb/modules/ | grep -i integrity"
                )
                print(f"      PI Fix module status: {result['status']}")
                
            except Exception as e:
                print(f"      ✗ Device testing error: {e}")
        
        # Step 4: Generate report
        print("\n[4/5] Generating comprehensive report...")
        report = self.validator.generate_report()
        
        # Step 5: Save report
        print("\n[5/5] Saving report...")
        report_path = Path("/root/vmos-titan-unified/TOOLS_TESTING_REPORT.md")
        report_path.write_text(report)
        print(f"      Report saved to: {report_path}")
        
        print("\n" + "=" * 80)
        print(report)
        print("=" * 80)

# ═══════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════

async def main():
    """Main entry point"""
    orchestrator = PlaygroundOrchestrator()
    await orchestrator.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[!] Testing interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
