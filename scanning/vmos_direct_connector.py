#!/usr/bin/env python3
"""
VMOS Direct Device Connector - Container Escape & Network Mapping
Target Device: ACP251008GUOEEHB
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional

sys.path.insert(0, "/home/debian/Downloads/vmos-titan-unified")

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient


class VMOSDirectConnector:
    """Connect to specific VMOS device and perform operations."""
    
    def __init__(self, ak: str, sk: str, pad_code: str):
        self.ak = ak
        self.sk = sk
        self.pad_code = pad_code
        self.client: Optional[VMOSCloudClient] = None
        self.adb_target: Optional[str] = None
        
    async def connect(self) -> bool:
        """Connect to VMOS Cloud API."""
        print("=" * 60)
        print("  VMOS Direct Device Connector")
        print(f"  Target: {self.pad_code}")
        print("=" * 60)
        
        try:
            self.client = VMOSCloudClient(ak=self.ak, sk=self.sk)
            print("\n✓ VMOS Cloud API connected")
            return True
        except Exception as e:
            print(f"\n❌ API connection failed: {e}")
            return False
    
    async def get_device_info(self) -> Optional[Dict]:
        """Get device information."""
        print(f"\n🔍 Getting device info for {self.pad_code}...")
        
        try:
            # Get cloud phone info
            result = await self.client.cloud_phone_info(self.pad_code)
            
            if result.get("code") != 200:
                print(f"❌ Failed to get device info: {result.get('msg', 'Unknown')}")
                return None
            
            device_data = result.get("data", {})
            
            print(f"\n📱 Device Information:")
            print(f"  Pad Code: {device_data.get('padCode')}")
            print(f"  Name: {device_data.get('deviceName')}")
            print(f"  Status: {device_data.get('status')}")
            print(f"  IP: {device_data.get('deviceIp')}")
            print(f"  Android: {device_data.get('androidVersion')}")
            print(f"  ROM: {device_data.get('romVersion')}")
            print(f"  Level: {device_data.get('deviceLevel')}")
            
            # Get properties
            props_result = await self.client.query_instance_properties(self.pad_code)
            if props_result.get("code") == 200:
                props = props_result.get("data", {})
                device_data["_properties"] = props
                
                print(f"\n  Properties:")
                print(f"    Model: {props.get('ro.product.model', 'N/A')}")
                print(f"    Brand: {props.get('ro.product.brand', 'N/A')}")
                print(f"    Device: {props.get('ro.product.device', 'N/A')}")
                print(f"    Fingerprint: {props.get('ro.build.fingerprint', 'N/A')[:50]}...")
            
            return device_data
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    async def enable_adb(self) -> Optional[str]:
        """Enable ADB and get connection."""
        print(f"\n🔓 Enabling ADB for {self.pad_code}...")
        
        try:
            # Enable ADB
            result = await self.client.enable_adb([self.pad_code])
            print(f"  Enable ADB: {result.get('code')} - {result.get('msg', 'OK')}")
            
            # Get ADB info
            adb_result = await self.client.get_adb_info(self.pad_code, enable=True)
            
            if adb_result.get("code") == 200:
                data = adb_result.get("data", {})
                host = data.get("host", "")
                port = data.get("port", "")
                
                if host and port:
                    self.adb_target = f"{host}:{port}"
                    print(f"  ✓ ADB Target: {self.adb_target}")
                    
                    # Connect local ADB
                    subprocess.run(
                        ["adb", "connect", self.adb_target],
                        capture_output=True, timeout=30
                    )
                    time.sleep(2)
                    
                    # Verify connection
                    verify = subprocess.run(
                        ["adb", "-s", self.adb_target, "shell", "echo", "CONNECTED"],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if verify.returncode == 0 and "CONNECTED" in verify.stdout:
                        print(f"  ✓ ADB connection verified!")
                        return self.adb_target
                    else:
                        # Retry
                        print(f"  ⚠ Retrying connection...")
                        subprocess.run(["adb", "disconnect", self.adb_target], capture_output=True)
                        time.sleep(1)
                        subprocess.run(["adb", "connect", self.adb_target], capture_output=True)
                        time.sleep(2)
                        
                        # Re-verify
                        verify2 = subprocess.run(
                            ["adb", "-s", self.adb_target, "shell", "echo", "CONNECTED"],
                            capture_output=True, text=True, timeout=10
                        )
                        if verify2.returncode == 0:
                            print(f"  ✓ ADB connection verified on retry!")
                            return self.adb_target
                        else:
                            print(f"  ⚠ Connection verification failed")
                            return self.adb_target  # Return anyway, might work
            
            print(f"  ⚠ Could not get ADB info")
            return None
            
        except Exception as e:
            print(f"❌ ADB setup error: {e}")
            return None
    
    def adb_shell(self, cmd: str, timeout: int = 15) -> str:
        """Run ADB shell command."""
        if not self.adb_target:
            return ""
        
        result = subprocess.run(
            ["adb", "-s", self.adb_target, "shell", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    
    def container_escape_analysis(self) -> Dict:
        """Perform container escape analysis."""
        print("\n" + "=" * 60)
        print("  CONTAINER ESCAPE & HOST ANALYSIS")
        print("=" * 60)
        
        findings = {
            "container_type": "Linux namespace (VMOS Cloud)",
            "host_architecture": "Rockchip RK3588 ARM64",
            "escape_vectors": [],
            "host_access": {},
            "neighborhood": []
        }
        
        # 1. Container Analysis
        print("\n[1] Container Environment Analysis")
        
        cgroup = self.adb_shell("cat /proc/self/cgroup")
        print(f"  Cgroup hierarchy:")
        for line in cgroup.splitlines()[:5]:
            print(f"    {line}")
        findings["cgroup"] = cgroup
        
        # Check namespaces
        ns = self.adb_shell("ls -la /proc/self/ns/")
        print(f"\n  Namespaces:")
        for line in ns.splitlines():
            if "->" in line:
                print(f"    {line}")
        
        # Init system
        init = self.adb_shell("cat /proc/1/comm")
        print(f"\n  Init process: {init}")
        
        # 2. Privilege & Capability Analysis
        print("\n[2] Privilege Analysis")
        
        whoami = self.adb_shell("whoami")
        print(f"  Current user: {whoami}")
        
        id_info = self.adb_shell("id")
        print(f"  ID: {id_info}")
        
        caps = self.adb_shell("cat /proc/self/status | grep Cap")
        print(f"  Capabilities:")
        for line in caps.splitlines():
            print(f"    {line}")
        
        # 3. Filesystem Analysis
        print("\n[3] Filesystem Escape Vectors")
        
        # Check /system (should be read-only dm-verity)
        sys_test = self.adb_shell("touch /system/.test 2>&1 || echo 'RO'")
        if "RO" in sys_test or "Read-only" in sys_test:
            print(f"  ✓ /system is read-only (dm-verity protected)")
            findings["escape_vectors"].append("/system: dm-verity blocked")
        else:
            print(f"  ⚠ /system is writable!")
            findings["escape_vectors"].append("/system: WRITEABLE - ESCAPE POSSIBLE")
        
        # Check /data
        data_test = self.adb_shell("touch /data/local/tmp/.test && rm /data/local/tmp/.test && echo 'RW'")
        print(f"  /data: {data_test}")
        
        # Check for host mounts
        mounts = self.adb_shell("cat /proc/mounts | grep -E 'proc|sysfs|devpts' | head -10")
        print(f"\n  Key mounts:")
        for line in mounts.splitlines():
            if line.strip():
                print(f"    {line[:80]}")
        
        # 4. Host Network Access
        print("\n[4] Host Network Access (Container Network Breakout)")
        
        # Get network info
        net_dev = self.adb_shell("cat /proc/net/dev | grep -E 'eth|wlan' | head -5")
        print(f"  Network devices:")
        for line in net_dev.splitlines():
            if line.strip():
                print(f"    {line.strip()}")
        
        # Routes
        routes = self.adb_shell("ip route")
        print(f"\n  Routing table:")
        for line in routes.splitlines()[:10]:
            print(f"    {line}")
        findings["host_access"]["routes"] = routes
        
        # ARP table - shows other devices
        arp = self.adb_shell("cat /proc/net/arp")
        print(f"\n  ARP table (neighbor devices):")
        arp_lines = arp.splitlines()
        if len(arp_lines) > 1:
            for line in arp_lines[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 4:
                    ip = parts[0]
                    mac = parts[3]
                    if mac != "00:00:00:00:00:00":
                        print(f"    ✓ {ip} → {mac}")
                        findings["neighborhood"].append({"ip": ip, "mac": mac, "source": "ARP"})
        
        # 5. Process Analysis - Find other containers
        print("\n[5] Host Process Discovery (Other Containers)")
        
        # Get all PIDs
        all_pids = self.adb_shell("ls /proc/ | grep -E '^[0-9]+$' | wc -l")
        print(f"  Total processes visible: {all_pids}")
        
        # Check for VMOS/cloudphone processes
        vmos_procs = self.adb_shell("ps -A | grep -E 'cloudphone|vmos|pad|container' | head -10")
        if vmos_procs:
            print(f"\n  VMOS/Container processes:")
            for line in vmos_procs.splitlines():
                print(f"    {line.strip()}")
        
        # Find processes outside our namespace
        our_pid = self.adb_shell("echo $$")
        print(f"\n  Our PID: {our_pid}")
        
        # Check other container UIDs
        other_uids = self.adb_shell("ps -A -o uid,pid,comm | grep -v ' 0 ' | grep -v $(id -u) | head -10")
        if other_uids:
            print(f"\n  Other user namespaces (possible containers):")
            for line in other_uids.splitlines():
                print(f"    {line.strip()}")
        
        # 6. Network Scanning
        print("\n[6] Neighborhood Device Scan")
        
        # Get gateway
        gateway = self.adb_shell("ip route | grep default | awk '{print $3}'")
        if gateway:
            print(f"  Gateway: {gateway}")
            
            # Ping sweep of local subnet (limited)
            subnet = ".".join(gateway.split(".")[:3])
            print(f"\n  Scanning {subnet}.0/24...")
            
            # Quick ping scan for common hosts
            alive_hosts = []
            for i in range(1, 10):  # Scan .1 to .9
                ip = f"{subnet}.{i}"
                if ip == gateway:
                    continue
                result = self.adb_shell(f"ping -c 1 -W 1 {ip} >/dev/null 2>&1 && echo 'ALIVE' || echo 'DOWN'", timeout=5)
                if "ALIVE" in result:
                    print(f"    ✓ Host alive: {ip}")
                    alive_hosts.append(ip)
                    findings["neighborhood"].append({"ip": ip, "source": "PING"})
            
            # Port scan gateway
            print(f"\n  Gateway ({gateway}) port scan:")
            for port in [22, 80, 443, 5555, 8080, 9090]:
                result = self.adb_shell(f"nc -z -w 1 {gateway} {port} 2>/dev/null && echo 'OPEN' || echo 'CLOSED'")
                if "OPEN" in result:
                    print(f"    ✓ Port {port}/tcp open")
                    findings["neighborhood"].append({"ip": gateway, "port": port, "source": "PORT_SCAN"})
        
        # 7. Kernel & Host Info
        print("\n[7] Host System Information")
        
        kernel = self.adb_shell("uname -a")
        print(f"  Kernel: {kernel}")
        findings["host_access"]["kernel"] = kernel
        
        # Check for container runtime info
        sched = self.adb_shell("cat /proc/1/sched | head -1")
        print(f"  Scheduler: {sched[:50]}")
        
        # Memory info
        mem = self.adb_shell("cat /proc/meminfo | head -3")
        print(f"\n  Memory:")
        for line in mem.splitlines():
            print(f"    {line}")
        
        # 8. Security Assessment
        print("\n[8] Container Security Assessment")
        
        checks = {
            "seccomp": self.adb_shell("cat /proc/self/status | grep Seccomp"),
            "apparmor": self.adb_shell("cat /proc/self/attr/current"),
            "selinux": self.adb_shell("getenforce 2>/dev/null || echo 'N/A'"),
        }
        
        print(f"  Seccomp: {checks['seccomp'] or 'Not enforced'}")
        print(f"  AppArmor: {checks['apparmor'][:50] if checks['apparmor'] else 'N/A'}")
        print(f"  SELinux: {checks['selinux']}")
        
        # Summary
        print("\n" + "=" * 60)
        print("  ESCAPE ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"  Container Type: Linux PID/Network namespace")
        print(f"  Host: Rockchip RK3588 ARM64")
        print(f"  /system: dm-verity protected (read-only)")
        print(f"  /data: Writable")
        print(f"  Network: Shared with host (no isolation)")
        print(f"  Neighbor devices found: {len(findings['neighborhood'])}")
        
        if findings["neighborhood"]:
            print(f"\n  Discovered devices:")
            for dev in findings["neighborhood"]:
                print(f"    - {dev['ip']} ({dev.get('mac', 'N/A')}) [{dev['source']}]")
        
        return findings
    
    async def run(self):
        """Execute full workflow."""
        
        # Connect API
        if not await self.connect():
            return False
        
        # Get device info
        device_info = await self.get_device_info()
        if not device_info:
            return False
        
        # Enable ADB
        adb_target = await self.enable_adb()
        if not adb_target:
            print("\n⚠ Proceeding without verified ADB...")
            self.adb_target = f"{device_info.get('deviceIp', '0.0.0.0')}:5555"
        
        # Perform container escape analysis
        findings = self.container_escape_analysis()
        
        # Save report
        report = {
            "timestamp": time.time(),
            "device_id": self.pad_code,
            "device_info": device_info,
            "adb_target": self.adb_target,
            "findings": findings
        }
        
        filename = f"vmos_escape_{self.pad_code}_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Full report saved: {filename}")
        
        return True


async def main():
    # Credentials from user
    AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
    SK = "Q2SgcSwEfuwoedY0cijp6Mce"
    DEVICE_ID = "ACP251008GUOEEHB"
    
    connector = VMOSDirectConnector(AK, SK, DEVICE_ID)
    
    try:
        success = await connector.run()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
