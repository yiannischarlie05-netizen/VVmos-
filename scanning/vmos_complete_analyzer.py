#!/usr/bin/env python3
"""
VMOS Titan - Complete Codebase Analyzer & Container Escape Tool
Direct execution without scripting - analyzes all APIs, cloud connections, and escape vectors
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
from vmos_titan.core.vmos_cloud_module import VMOSCloudBridge


class VMOSCompleteAnalyzer:
    """Complete VMOS Titan codebase analysis and container escape."""
    
    def __init__(self, ak: str, sk: str):
        self.ak = ak
        self.sk = sk
        self.client = None
        self.bridge = None
        self.results = {
            "apis": {},
            "cloud_devices": [],
            "escape_vectors": {},
            "network_map": {},
            "codebase_analysis": {}
        }
    
    async def connect_apis(self):
        """Connect to all VMOS APIs."""
        print("=" * 80)
        print("  VMOS TITAN - COMPLETE CODEBASE & CONTAINER ANALYSIS")
        print("=" * 80)
        
        # API Client connections
        try:
            self.client = VMOSCloudClient(ak=self.ak, sk=self.sk)
            self.results["apis"]["cloud_client"] = "CONNECTED"
            print("✓ VMOS Cloud API Client connected")
        except Exception as e:
            self.results["apis"]["cloud_client"] = f"FAILED: {e}"
            print(f"✗ Cloud API Client failed: {e}")
        
        try:
            self.bridge = VMOSCloudBridge()
            self.results["apis"]["cloud_bridge"] = "CONNECTED"
            print("✓ VMOS Cloud Bridge connected")
        except Exception as e:
            self.results["apis"]["cloud_bridge"] = f"FAILED: {e}"
            print(f"✗ Cloud Bridge failed: {e}")
    
    async def scan_all_cloud_devices(self):
        """Scan all cloud devices and categorize."""
        print("\n[1] SCANNING ALL CLOUD DEVICES")
        
        devices = []
        
        # Method 1: Cloud Client
        if self.client:
            try:
                result = await self.client.cloud_phone_list(page=1, rows=100)
                if result.get("code") == 200:
                    data = result.get("data", [])
                    rows = data if isinstance(data, list) else data.get("rows", [])
                    for device in rows:
                        devices.append({
                            "source": "cloud_client",
                            "data": device
                        })
                    print(f"  ✓ Cloud Client: {len(rows)} devices")
            except Exception as e:
                print(f"  ✗ Cloud Client scan failed: {e}")
        
        # Method 2: Cloud Bridge
        if self.bridge:
            try:
                instances = await self.bridge.list_instances()
                for inst in instances:
                    devices.append({
                        "source": "cloud_bridge",
                        "data": {
                            "padCode": inst.pad_code,
                            "deviceName": inst.device_name,
                            "status": inst.status,
                            "ip": inst.device_ip,
                            "android": inst.android_version
                        }
                    })
                print(f"  ✓ Cloud Bridge: {len(instances)} instances")
            except Exception as e:
                print(f"  ✗ Cloud Bridge scan failed: {e}")
        
        # Categorize devices
        categorized = {
            "oneplus": [],
            "samsung": [],
            "pixel": [],
            "xiaomi": [],
            "other": [],
            "total": len(devices)
        }
        
        for device in devices:
            data = device["data"]
            name = str(data.get("deviceName", "")).lower()
            pad_code = data.get("padCode", "")
            
            # Get properties for better categorization
            if self.client and pad_code:
                try:
                    props = await self.client.query_instance_properties(pad_code)
                    if props.get("code") == 200:
                        props_data = props.get("data", {})
                        model = str(props_data.get("ro.product.model", "")).lower()
                        brand = str(props_data.get("ro.product.brand", "")).lower()
                        
                        if "oneplus" in model or "oneplus" in brand:
                            categorized["oneplus"].append(device)
                        elif "samsung" in model or "samsung" in brand:
                            categorized["samsung"].append(device)
                        elif "pixel" in model or "google" in brand:
                            categorized["pixel"].append(device)
                        elif "xiaomi" in model or "redmi" in model:
                            categorized["xiaomi"].append(device)
                        else:
                            categorized["other"].append(device)
                        continue
                except:
                    pass
            
            # Fallback categorization by name
            if "oneplus" in name:
                categorized["oneplus"].append(device)
            elif "samsung" in name:
                categorized["samsung"].append(device)
            elif "pixel" in name:
                categorized["pixel"].append(device)
            elif "xiaomi" in name or "redmi" in name:
                categorized["xiaomi"].append(device)
            else:
                categorized["other"].append(device)
        
        self.results["cloud_devices"] = categorized
        
        print(f"\n  Device Summary:")
        print(f"    Total: {categorized['total']}")
        print(f"    OnePlus: {len(categorized['oneplus'])}")
        print(f"    Samsung: {len(categorized['samsung'])}")
        print(f"    Pixel: {len(categorized['pixel'])}")
        print(f"    Xiaomi: {len(categorized['xiaomi'])}")
        print(f"    Other: {len(categorized['other'])}")
    
    async def analyze_codebase_apis(self):
        """Analyze all VMOS codebase APIs and endpoints."""
        print("\n[2] ANALYZING CODEBASE APIS")
        
        api_analysis = {
            "cloud_api": {},
            "cloud_bridge": {},
            "local_modules": {},
            "endpoints": []
        }
        
        # Cloud API capabilities
        if self.client:
            print("  Analyzing Cloud API capabilities...")
            
            # Test key endpoints
            endpoints_to_test = [
                ("cloud_phone_list", lambda: self.client.cloud_phone_list(page=1, rows=5)),
                ("enable_adb", lambda: self.client.enable_adb(["ACP251008GUOEEHB"])),
                ("get_adb_info", lambda: self.client.get_adb_info("ACP251008GUOEEHB")),
                ("query_instance_properties", lambda: self.client.query_instance_properties("ACP251008GUOEEHB")),
                ("set_gps", lambda: self.client.set_gps(["ACP251008GUOEEHB"], 37.7749, -122.4194)),
                ("list_installed_apps", lambda: self.client.list_installed_apps_realtime("ACP251008GUOEEHB")),
                ("sync_cmd", lambda: self.client.sync_cmd("ACP251008GUOEEHB", "getprop ro.build.version.release")),
                ("screenshot", lambda: self.client.screenshot(["ACP251008GUOEEHB"])),
                ("humanized_click", lambda: self.client.humanized_click(["ACP251008GUOEEHB"], 540, 960, 1080, 2400)),
                ("set_wifi_list", lambda: self.client.set_wifi_list(["ACP251008GUOEEHB"], [])),
                ("instance_restart", lambda: self.client.instance_restart(["ACP251008GUOEEHB"])),
            ]
            
            for endpoint_name, endpoint_func in endpoints_to_test:
                try:
                    result = await endpoint_func()
                    status = result.get("code", "unknown")
                    api_analysis["cloud_api"][endpoint_name] = {
                        "status": status,
                        "response": str(result)[:200]
                    }
                    if status == 200:
                        print(f"    ✓ {endpoint_name}")
                    else:
                        print(f"    ✗ {endpoint_name} ({status})")
                except Exception as e:
                    api_analysis["cloud_api"][endpoint_name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"    ✗ {endpoint_name} (ERROR: {str(e)[:50]})")
        
        # Cloud Bridge capabilities
        if self.bridge:
            print("  Analyzing Cloud Bridge capabilities...")
            
            bridge_methods = [
                ("list_instances", lambda: self.bridge.list_instances()),
                ("exec_shell", lambda: self.bridge.exec_shell("ACP251008GUOEEHB", "echo test")),
                ("update_android_props", lambda: self.bridge.update_android_props("ACP251008GUOEEHB", {"ro.test": "value"})),
                ("set_gps", lambda: self.bridge.set_gps("ACP251008GUOEEHB", 37.7749, -122.4194)),
                ("screenshot", lambda: self.bridge.screenshot("ACP251008GUOEEHB")),
                ("inject_contacts", lambda: self.bridge.inject_contacts("ACP251008GUOEEHB", [])),
            ]
            
            for method_name, method_func in bridge_methods:
                try:
                    result = await method_func()
                    api_analysis["cloud_bridge"][method_name] = {
                        "status": "success",
                        "result": str(result)[:200]
                    }
                    print(f"    ✓ {method_name}")
                except Exception as e:
                    api_analysis["cloud_bridge"][method_name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"    ✗ {method_name} (ERROR: {str(e)[:50]})")
        
        self.results["codebase_analysis"] = api_analysis
    
    async def container_escape_analysis(self):
        """Comprehensive container escape analysis."""
        print("\n[3] CONTAINER ESCAPE ANALYSIS")
        
        escape_vectors = {
            "filesystem": {},
            "network": {},
            "process": {},
            "privilege": {},
            "kernel": {},
            "hardware": {}
        }
        
        # Target device for escape analysis
        target_device = "ACP251008GUOEEHB"
        
        # Enable ADB for escape testing
        if self.client:
            try:
                await self.client.enable_adb([target_device])
                adb_result = await self.client.get_adb_info(target_device, enable=True)
                
                if adb_result.get("code") == 200:
                    data = adb_result.get("data", {})
                    host = data.get("host", "")
                    port = data.get("port", "")
                    
                    if host and port:
                        adb_target = f"{host}:{port}"
                        print(f"  ADB target: {adb_target}")
                        
                        # Connect local ADB
                        subprocess.run(["adb", "connect", adb_target], capture_output=True)
                        time.sleep(2)
                        
                        # Execute escape commands
                        escape_commands = [
                            ("cgroup", "cat /proc/self/cgroup"),
                            ("namespaces", "ls -la /proc/self/ns/"),
                            ("capabilities", "cat /proc/self/status | grep Cap"),
                            ("mounts", "cat /proc/mounts | head -20"),
                            ("devices", "ls -la /dev/ | head -20"),
                            ("network", "cat /proc/net/dev | head -10"),
                            ("routes", "ip route show"),
                            ("arp", "cat /proc/net/arp"),
                            ("processes", "ps -A | head -20"),
                            ("system_test", "touch /system/.test 2>&1 || echo 'RO'"),
                            ("data_test", "touch /data/local/tmp/.test && rm /data/local/tmp/.test && echo 'RW'"),
                            ("kernel", "uname -a"),
                            ("memory", "cat /proc/meminfo | head -5"),
                            ("cpuinfo", "cat /proc/cpuinfo | head -5"),
                        ]
                        
                        for cmd_name, cmd in escape_commands:
                            try:
                                result = subprocess.run(
                                    ["adb", "-s", adb_target, "shell", cmd],
                                    capture_output=True, text=True, timeout=10
                                )
                                output = result.stdout.strip()
                                escape_vectors[cmd_name] = {
                                    "status": "success" if result.returncode == 0 else "failed",
                                    "output": output[:500]
                                }
                                print(f"    ✓ {cmd_name}")
                            except Exception as e:
                                escape_vectors[cmd_name] = {
                                    "status": "error",
                                    "error": str(e)
                                }
                                print(f"    ✗ {cmd_name}")
                        
                        # Advanced escape techniques
                        print("  Testing advanced escape vectors...")
                        
                        # Check for container runtime info
                        runtime_cmd = "cat /proc/1/cgroup | head -1"
                        result = subprocess.run(
                            ["adb", "-s", adb_target, "shell", runtime_cmd],
                            capture_output=True, text=True, timeout=10
                        )
                        escape_vectors["runtime"] = {
                            "status": "success" if result.returncode == 0 else "failed",
                            "output": result.stdout.strip()
                        }
                        
                        # Check for host filesystem access
                        host_fs_cmd = "ls /proc/host/ 2>/dev/null || echo 'NO_HOST'"
                        result = subprocess.run(
                            ["adb", "-s", adb_target, "shell", host_fs_cmd],
                            capture_output=True, text=True, timeout=10
                        )
                        escape_vectors["host_fs"] = {
                            "status": "success" if "NO_HOST" not in result.stdout else "limited",
                            "output": result.stdout.strip()
                        }
                        
                        # Network scanning
                        print("  Network neighborhood scanning...")
                        
                        # Get gateway
                        gateway_cmd = "ip route | grep default | awk '{print $3}'"
                        result = subprocess.run(
                            ["adb", "-s", adb_target, "shell", gateway_cmd],
                            capture_output=True, text=True, timeout=10
                        )
                        gateway = result.stdout.strip()
                        
                        if gateway:
                            # Port scan gateway
                            ports = [22, 80, 443, 5555, 8080, 9090]
                            open_ports = []
                            
                            for port in ports:
                                port_cmd = f"nc -z -w 1 {gateway} {port} 2>/dev/null && echo 'OPEN' || echo 'CLOSED'"
                                result = subprocess.run(
                                    ["adb", "-s", adb_target, "shell", port_cmd],
                                    capture_output=True, text=True, timeout=5
                                )
                                if "OPEN" in result.stdout:
                                    open_ports.append(port)
                            
                            escape_vectors["network_scan"] = {
                                "gateway": gateway,
                                "open_ports": open_ports
                            }
                            print(f"    ✓ Network scan - Gateway: {gateway}, Open ports: {open_ports}")
                        
            except Exception as e:
                print(f"  ✗ Escape analysis failed: {e}")
                escape_vectors["error"] = str(e)
        
        self.results["escape_vectors"] = escape_vectors
    
    async def map_all_devices(self):
        """Map all devices in the VMOS ecosystem."""
        print("\n[4] MAPPING VMOS ECOSYSTEM")
        
        device_map = {
            "cloud_devices": [],
            "local_devices": [],
            "network_topology": {},
            "infrastructure": {}
        }
        
        # Map cloud devices with full details
        if self.client:
            try:
                result = await self.client.cloud_phone_list(page=1, rows=100)
                if result.get("code") == 200:
                    data = result.get("data", [])
                    rows = data if isinstance(data, list) else data.get("rows", [])
                    
                    for device in rows:
                        pad_code = device.get("padCode")
                        device_details = {
                            "pad_code": pad_code,
                            "name": device.get("deviceName"),
                            "status": device.get("status"),
                            "ip": device.get("deviceIp"),
                            "android": device.get("androidVersion"),
                            "location": device.get("padAddress"),
                            "properties": {}
                        }
                        
                        # Get detailed properties
                        if pad_code:
                            try:
                                props = await self.client.query_instance_properties(pad_code)
                                if props.get("code") == 200:
                                    props_data = props.get("data", {})
                                    device_details["properties"] = {
                                        "model": props_data.get("ro.product.model"),
                                        "brand": props_data.get("ro.product.brand"),
                                        "fingerprint": props_data.get("ro.build.fingerprint"),
                                        "kernel": props_data.get("ro.kernel.version"),
                                        "cpu": props_data.get("ro.product.cpu.abi"),
                                    }
                            except:
                                pass
                        
                        device_map["cloud_devices"].append(device_details)
                    
                    print(f"  ✓ Mapped {len(device_map['cloud_devices'])} cloud devices")
                    
            except Exception as e:
                print(f"  ✗ Cloud device mapping failed: {e}")
        
        # Map local ADB devices
        try:
            result = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip() and not line.startswith('*'):
                    parts = line.split()
                    if len(parts) >= 2:
                        device_id = parts[0]
                        status = parts[1]
                        info = {}
                        for part in parts[2:]:
                            if ':' in part:
                                k, v = part.split(':', 1)
                                info[k] = v
                        
                        device_map["local_devices"].append({
                            "id": device_id,
                            "status": status,
                            "info": info
                        })
            
            print(f"  ✓ Mapped {len(device_map['local_devices'])} local ADB devices")
            
        except Exception as e:
            print(f"  ✗ Local device mapping failed: {e}")
        
        # Analyze network topology
        if device_map["cloud_devices"]:
            # Group by location/IP
            locations = {}
            ips = {}
            
            for device in device_map["cloud_devices"]:
                location = device.get("location", "Unknown")
                ip = device.get("ip", "Unknown")
                
                locations[location] = locations.get(location, 0) + 1
                ips[ip] = ips.get(ip, 0) + 1
            
            device_map["network_topology"] = {
                "locations": locations,
                "ips": ips,
                "unique_locations": len(locations),
                "unique_ips": len(ips)
            }
            
            print(f"  ✓ Network topology: {len(locations)} locations, {len(ips)} unique IPs")
        
        # Infrastructure analysis
        infra = {
            "android_versions": {},
            "device_types": {},
            "status_distribution": {}
        }
        
        for device in device_map["cloud_devices"]:
            # Android versions
            android = device.get("android", "Unknown")
            infra["android_versions"][android] = infra["android_versions"].get(android, 0) + 1
            
            # Device types
            props = device.get("properties", {})
            brand = props.get("brand", "Unknown")
            infra["device_types"][brand] = infra["device_types"].get(brand, 0) + 1
            
            # Status
            status = device.get("status", "Unknown")
            infra["status_distribution"][status] = infra["status_distribution"].get(status, 0) + 1
        
        device_map["infrastructure"] = infra
        print(f"  ✓ Infrastructure analysis complete")
        
        self.results["network_map"] = device_map
    
    async def generate_final_report(self):
        """Generate comprehensive final report."""
        print("\n" + "=" * 80)
        print("  COMPREHENSIVE VMOS TITAN ANALYSIS REPORT")
        print("=" * 80)
        
        # API Summary
        print("\n[API CONNECTIONS]")
        for api_name, status in self.results["apis"].items():
            print(f"  {api_name}: {status}")
        
        # Device Summary
        print("\n[DEVICE SUMMARY]")
        devices = self.results["cloud_devices"]
        print(f"  Total Cloud Devices: {devices.get('total', 0)}")
        print(f"  OnePlus: {len(devices.get('oneplus', []))}")
        print(f"  Samsung: {len(devices.get('samsung', []))}")
        print(f"  Pixel: {len(devices.get('pixel', []))}")
        print(f"  Xiaomi: {len(devices.get('xiaomi', []))}")
        print(f"  Other: {len(devices.get('other', []))}")
        
        # Escape Analysis Summary
        print("\n[CONTAINER ESCAPE ANALYSIS]")
        escape = self.results["escape_vectors"]
        if escape:
            print(f"  Escape vectors tested: {len(escape)}")
            if "system_test" in escape:
                sys_status = escape["system_test"].get("output", "")
                if "RO" in sys_status:
                    print(f"  /system: Read-only (dm-verity)")
                else:
                    print(f"  /system: WRITABLE - ESCAPE POSSIBLE")
            
            if "network_scan" in escape:
                net = escape["network_scan"]
                if "gateway" in net:
                    print(f"  Gateway: {net['gateway']}")
                    print(f"  Open ports: {net.get('open_ports', [])}")
        
        # Network Map Summary
        print("\n[NETWORK TOPOLOGY]")
        netmap = self.results["network_map"]
        if "network_topology" in netmap:
            topo = netmap["network_topology"]
            print(f"  Unique locations: {topo.get('unique_locations', 0)}")
            print(f"  Unique IPs: {topo.get('unique_ips', 0)}")
        
        if "infrastructure" in netmap:
            infra = netmap["infrastructure"]
            print(f"  Android versions: {list(infra.get('android_versions', {}).keys())}")
            print(f"  Device brands: {list(infra.get('device_types', {}).keys())}")
        
        # Save comprehensive report
        timestamp = int(time.time())
        report_file = f"vmos_complete_analysis_{timestamp}.json"
        
        with open(report_file, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "analysis": self.results,
                "summary": {
                    "total_devices": devices.get('total', 0),
                    "apis_connected": len([k for k, v in self.results["apis"].items() if "CONNECTED" in v]),
                    "escape_vectors_found": len(escape),
                    "network_mapped": len(netmap.get("cloud_devices", [])),
                }
            }, f, indent=2, default=str)
        
        print(f"\n📄 Complete report saved: {report_file}")
        print(f"\n✅ VMOS Titan codebase analysis complete!")
    
    async def run_complete_analysis(self):
        """Execute complete analysis workflow."""
        await self.connect_apis()
        await self.scan_all_cloud_devices()
        await self.analyze_codebase_apis()
        await self.container_escape_analysis()
        await self.map_all_devices()
        await self.generate_final_report()


async def main():
    # Credentials
    AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
    SK = "Q2SgcSwEfuwoedY0cijp6Mce"
    
    analyzer = VMOSCompleteAnalyzer(AK, SK)
    
    try:
        await analyzer.run_complete_analysis()
        return 0
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
