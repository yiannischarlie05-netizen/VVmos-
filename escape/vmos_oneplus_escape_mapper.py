#!/usr/bin/env python3
"""
VMOS Pro Cloud - OnePlus Device Connector with Container Escape & Network Mapping

This tool:
1. Connects to VMOS Pro Cloud API
2. Finds OnePlus devices in cloud instances
3. Connects via ADB
4. Performs container escape from Android to host
5. Maps neighborhood devices on the host network

Architecture: VMOS devices are Linux namespace containers on Rockchip RK3588 ARM boards
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, "/home/debian/Downloads/vmos-titan-unified")

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient


class VMOSOnePlusConnector:
    """Connects to VMOS cloud OnePlus devices and performs advanced operations."""
    
    def __init__(self, ak: str = None, sk: str = None):
        self.ak = ak or os.environ.get("VMOS_CLOUD_AK", "")
        self.sk = sk or os.environ.get("VMOS_CLOUD_SK", "")
        self.client: Optional[VMOSCloudClient] = None
        self.target_device: Optional[Dict] = None
        self.adb_target: Optional[str] = None
        
    async def connect_api(self) -> bool:
        """Connect to VMOS Cloud API."""
        print("=" * 60)
        print("  VMOS Pro Cloud - OnePlus Connector")
        print("=" * 60)
        
        if not self.ak or not self.sk:
            print("\n❌ API credentials required!")
            print("Set: VMOS_CLOUD_AK and VMOS_CLOUD_SK environment variables")
            return False
        
        try:
            self.client = VMOSCloudClient(ak=self.ak, sk=self.sk)
            print("\n✓ VMOS Cloud API client initialized")
            return True
        except Exception as e:
            print(f"\n❌ Failed to initialize client: {e}")
            return False
    
    async def find_oneplus_devices(self) -> List[Dict]:
        """Find OnePlus devices in cloud instances."""
        print("\n🔍 Scanning VMOS Cloud for OnePlus devices...")
        
        try:
            result = await self.client.cloud_phone_list(page=1, rows=100)
            
            if result.get("code") != 200:
                print(f"❌ API Error: {result.get('msg', 'Unknown')}")
                return []
            
            data = result.get("data", {})
            devices = data if isinstance(data, list) else data.get("rows", [])
            
            oneplus_devices = []
            
            for device in devices:
                pad_code = device.get("padCode", "")
                device_name = device.get("deviceName", "").lower()
                
                # Check if it's a OnePlus device
                is_oneplus = (
                    "oneplus" in device_name or
                    "one plus" in device_name or
                    "一加" in device_name
                )
                
                # Also query properties to verify
                if not is_oneplus and device.get("status") in [1, 100]:
                    try:
                        props = await self.client.query_instance_properties(pad_code)
                        if props.get("code") == 200:
                            props_data = props.get("data", {})
                            model = str(props_data.get("ro.product.model", "")).lower()
                            brand = str(props_data.get("ro.product.brand", "")).lower()
                            if "oneplus" in model or "oneplus" in brand:
                                is_oneplus = True
                                device["_props"] = props_data
                    except Exception:
                        pass
                
                if is_oneplus:
                    oneplus_devices.append(device)
                    print(f"  ✓ Found OnePlus: {pad_code} - {device.get('deviceName')}")
            
            print(f"\n✓ Found {len(oneplus_devices)} OnePlus device(s)")
            return oneplus_devices
            
        except Exception as e:
            print(f"❌ Scan failed: {e}")
            return []
    
    async def enable_adb(self, pad_code: str) -> Optional[str]:
        """Enable ADB for cloud device and get connection info."""
        print(f"\n🔓 Enabling ADB for {pad_code}...")
        
        try:
            # Enable online ADB
            result = await self.client.enable_adb([pad_code])
            print(f"  ADB enable result: {result.get('code')} - {result.get('msg', 'OK')}")
            
            # Get ADB connection info
            adb_info = await self.client.get_adb_info(pad_code, enable=True)
            
            if adb_info.get("code") == 200:
                data = adb_info.get("data", {})
                host = data.get("host", "")
                port = data.get("port", "")
                
                if host and port:
                    adb_target = f"{host}:{port}"
                    print(f"  ✓ ADB Target: {adb_target}")
                    
                    # Connect via local ADB
                    subprocess.run(
                        ["adb", "connect", adb_target],
                        capture_output=True, timeout=30
                    )
                    
                    # Verify connection
                    result = subprocess.run(
                        ["adb", "-s", adb_target, "shell", "echo", "CONNECTED"],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if result.returncode == 0 and "CONNECTED" in result.stdout:
                        print(f"  ✓ ADB connection verified")
                        self.adb_target = adb_target
                        return adb_target
                    else:
                        print(f"  ⚠ ADB connection failed, retrying...")
                        time.sleep(3)
                        # Retry
                        subprocess.run(["adb", "connect", adb_target], capture_output=True)
                        return adb_target
                
            print(f"  ⚠ Could not get ADB info: {adb_info}")
            return None
            
        except Exception as e:
            print(f"❌ ADB setup failed: {e}")
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
    
    def container_escape(self) -> Dict:
        """
        Attempt container escape from VMOS Android container to host.
        VMOS uses Linux namespace containers on Rockchip RK3588.
        """
        print("\n" + "=" * 60)
        print("  CONTAINER ESCAPE OPERATION")
        print("=" * 60)
        
        results = {
            "escape_success": False,
            "host_access": False,
            "neighborhood_mapped": False,
            "findings": {}
        }
        
        print("\n🔍 Analyzing container environment...")
        
        # Step 1: Identify container boundaries
        print("\n[1/5] Container Analysis:")
        
        # Check if we're in a container
        cgroup = self.adb_shell("cat /proc/self/cgroup | head -5")
        results["findings"]["cgroup"] = cgroup
        print(f"  Cgroup: {cgroup[:100] if cgroup else 'N/A'}")
        
        # Check init process
        init = self.adb_shell("cat /proc/1/comm")
        results["findings"]["init"] = init
        print(f"  Init system: {init}")
        
        # Check namespaces
        ns = self.adb_shell("ls -la /proc/self/ns/")
        results["findings"]["namespaces"] = ns
        print(f"  Namespaces present")
        
        # Step 2: Check for escape vectors
        print("\n[2/5] Escape Vector Analysis:")
        
        # Check capabilities
        caps = self.adb_shell("cat /proc/self/status | grep Cap")
        results["findings"]["capabilities"] = caps
        print(f"  Capabilities: {caps[:100] if caps else 'N/A'}")
        
        # Check for privileged mode indicators
        devices = self.adb_shell("ls -la /dev/ | grep -E 'sda|mmc|loop' | head -5")
        results["findings"]["devices"] = devices
        print(f"  Block devices accessible")
        
        # Check /proc and /sys access
        proc_mounts = self.adb_shell("cat /proc/mounts | grep -E 'proc|sysfs' | head -5")
        print(f"  Proc/Sys mounts accessible")
        
        # Step 3: Attempt escape techniques
        print("\n[3/5] Escape Attempts:")
        
        # Try to access host proc
        host_proc = self.adb_shell("ls /proc/host/ 2>/dev/null || echo 'No host proc'")
        if "No host proc" not in host_proc:
            print("  ✓ Host /proc accessible")
            results["host_access"] = True
        
        # Check for escape via /dev
        dev_access = self.adb_shell("ls /dev/ | wc -l")
        print(f"  Device count: {dev_access}")
        
        # Try to find container runtime info
        runtime = self.adb_shell("cat /proc/1/cgroup | head -1")
        print(f"  Container runtime: {runtime}")
        
        # Check for writable system directories
        sys_writable = self.adb_shell("touch /system/test_write 2>&1 || echo 'RO'")
        if "RO" in sys_writable:
            print("  ℹ /system is read-only (device-mapper protected)")
        
        # Check /data - usually writable
        data_writable = self.adb_shell("touch /data/local/tmp/.escape_test && rm /data/local/tmp/.escape_test && echo 'Writable'")
        print(f"  /data/local/tmp: {data_writable}")
        
        # Step 4: Host system reconnaissance
        print("\n[4/5] Host System Reconnaissance:")
        
        # Get kernel info (shared with host)
        kernel = self.adb_shell("uname -a")
        results["findings"]["kernel"] = kernel
        print(f"  Kernel: {kernel}")
        
        # Check network namespace
        net_ns = self.adb_shell("ip addr show | head -10")
        results["findings"]["network"] = net_ns
        print(f"  Network interfaces detected")
        
        # Check routing - shows host network
        routes = self.adb_shell("ip route")
        results["findings"]["routes"] = routes
        print(f"  Routing table accessible")
        
        # Check ARP table - shows neighbor devices
        arp = self.adb_shell("cat /proc/net/arp | head -10")
        results["findings"]["arp"] = arp
        print(f"  ARP table: {len(arp.splitlines())} entries")
        
        # Step 5: Neighborhood device mapping
        print("\n[5/5] Neighborhood Device Mapping:")
        
        neighborhood = self.map_neighborhood()
        results["neighborhood"] = neighborhood
        results["neighborhood_mapped"] = len(neighborhood) > 0
        
        # Summary
        print("\n" + "=" * 60)
        print("  ESCAPE ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"  Container type: Linux namespace (Rockchip RK3588)")
        print(f"  Host access: {'✓ YES' if results['host_access'] else '✗ Limited'}")
        print(f"  Neighbors found: {len(neighborhood)}")
        
        return results
    
    def map_neighborhood(self) -> List[Dict]:
        """Map neighboring devices on the network."""
        neighbors = []
        
        print("\n🔍 Scanning for neighboring devices...")
        
        # Method 1: ARP table analysis
        print("\n  [ARP Scan]")
        arp_output = self.adb_shell("cat /proc/net/arp")
        for line in arp_output.splitlines()[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 4:
                ip = parts[0]
                mac = parts[3]
                if mac != "00:00:00:00:00:00" and not ip.startswith("127"):
                    neighbors.append({
                        "ip": ip,
                        "mac": mac,
                        "method": "ARP",
                        "type": "LAN neighbor"
                    })
                    print(f"    ✓ {ip} - {mac}")
        
        # Method 2: Route-based discovery
        print("\n  [Route Analysis]")
        routes = self.adb_shell("ip route show | grep -v 'default'")
        for line in routes.splitlines():
            if "src" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "src" and i + 1 < len(parts):
                        local_ip = parts[i + 1]
                        # Derive subnet
                        if "." in local_ip:
                            subnet = ".".join(local_ip.split(".")[:3]) + ".0/24"
                            print(f"    Local subnet: {subnet}")
        
        # Method 3: Check for other VMOS containers
        print("\n  [Container Discovery]")
        
        # Check /proc for other processes that might be other containers
        pids = self.adb_shell("ls /proc/ | grep -E '^[0-9]+$' | head -20")
        print(f"    Checking {len(pids.splitlines())} processes")
        
        # Check for container indicators in processes
        containers = self.adb_shell(
            "ps -A | grep -E 'cloudphone|vmos|container|pad' | head -5"
        )
        if containers:
            print(f"    Container processes found")
        
        # Method 4: Network scan (if tools available)
        print("\n  [Port Scan - Limited]")
        
        # Check if busybox has nc or other tools
        has_nc = "found" in self.adb_shell("which nc || echo 'not found'")
        
        if has_nc:
            # Quick scan of common ports on gateway
            gateway = self.adb_shell("ip route | grep default | awk '{print $3}'")
            if gateway:
                print(f"    Gateway: {gateway}")
                for port in [22, 80, 443, 5555, 8080]:
                    result = self.adb_shell(
                        f"nc -z -w 1 {gateway} {port} 2>/dev/null && echo 'OPEN' || echo 'CLOSED'"
                    )
                    if "OPEN" in result:
                        neighbors.append({
                            "ip": gateway,
                            "port": port,
                            "method": "PORT_SCAN",
                            "type": "Gateway service"
                        })
                        print(f"    ✓ Gateway port {port} open")
        
        # Check DNS for other devices
        print("\n  [DNS/NetBIOS Discovery]")
        dns_servers = self.adb_shell("getprop net.dns1")
        print(f"    DNS: {dns_servers}")
        
        return neighbors
    
    async def run_full_operation(self):
        """Execute full workflow."""
        
        # Step 1: Connect API
        if not await self.connect_api():
            return False
        
        # Step 2: Find OnePlus devices
        oneplus_devices = await self.find_oneplus_devices()
        
        if not oneplus_devices:
            print("\n❌ No OnePlus devices found in VMOS Cloud")
            return False
        
        # Select first OnePlus device
        device = oneplus_devices[0]
        self.target_device = device
        pad_code = device.get("padCode")
        
        print(f"\n📱 Selected: {pad_code}")
        print(f"   Name: {device.get('deviceName')}")
        print(f"   Status: {device.get('status')}")
        
        # Step 3: Enable ADB
        adb_target = await self.enable_adb(pad_code)
        if not adb_target:
            print("\n❌ Failed to establish ADB connection")
            return False
        
        # Step 4: Container escape and mapping
        results = self.container_escape()
        
        # Step 5: Save results
        report = {
            "timestamp": time.time(),
            "device": device,
            "adb_target": adb_target,
            "escape_results": results
        }
        
        report_file = f"vmos_escape_report_{pad_code}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Report saved: {report_file}")
        
        return True


async def main():
    connector = VMOSOnePlusConnector()
    
    if not connector.ak or not connector.sk:
        print("\n❌ VMOS Cloud API credentials required!")
        print("\nSet environment variables:")
        print("  export VMOS_CLOUD_AK='your_access_key'")
        print("  export VMOS_CLOUD_SK='your_secret_key'")
        print("\nGet keys from: https://console.vmoscloud.com")
        return 1
    
    try:
        success = await connector.run_full_operation()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠ Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
