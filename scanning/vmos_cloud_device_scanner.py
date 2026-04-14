#!/usr/bin/env python3
"""
VMOS Cloud Device Scanner
Lists all cloud phone instances with detailed status information.

Usage:
    export VMOS_CLOUD_AK="your_access_key"
    export VMOS_CLOUD_SK="your_secret_key"
    python3 vmos_cloud_device_scanner.py
"""

import asyncio
import os
import sys
from typing import List, Dict, Any, Optional

# Add project path
sys.path.insert(0, "/home/debian/Downloads/vmos-titan-unified")

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
from vmos_titan.core.vmos_cloud_module import VMOSCloudBridge


def check_credentials() -> bool:
    """Check if VMOS Cloud API credentials are configured."""
    ak = os.environ.get("VMOS_CLOUD_AK") or os.environ.get("VMOS_API_KEY")
    sk = os.environ.get("VMOS_CLOUD_SK") or os.environ.get("VMOS_API_SECRET")
    return bool(ak and sk)


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_device_card(device: Dict[str, Any], index: int):
    """Print a formatted device info card."""
    status_map = {
        0: ("🔴 OFFLINE", "\033[91m"),
        1: ("🟢 ONLINE", "\033[92m"),
        10: ("🟡 BOOTING", "\033[93m"),
        14: ("🔵 RESTARTING", "\033[94m"),
        15: ("🟠 RESETTING", "\033[95m"),
        100: ("⚡ RUNNING", "\033[96m"),
    }
    
    status_code = device.get("status", 0)
    status_text, color = status_map.get(status_code, (f"❓ UNKNOWN({status_code})", "\033[90m"))
    reset_color = "\033[0m"
    
    pad_code = device.get("padCode", "N/A")
    device_name = device.get("deviceName", "Unknown")
    device_ip = device.get("deviceIp", "N/A")
    rom_version = device.get("romVersion", "N/A")
    android_version = device.get("androidVersion", "N/A")
    resolution = device.get("resolution", "N/A")
    device_level = device.get("deviceLevel", "N/A")
    
    print(f"\n┌─ Device #{index}: {pad_code}")
    print(f"│   Name:        {device_name}")
    print(f"│   Status:      {color}{status_text}{reset_color}")
    print(f"│   IP:          {device_ip}")
    print(f"│   Android:     {android_version} (ROM: {rom_version})")
    print(f"│   Resolution:  {resolution}")
    print(f"│   Tier:        {device_level}")
    print(f"└─────────────────────────────────────────────")


async def scan_with_client():
    """Scan using the httpx-based client."""
    print_header("VMOS Cloud Device Scanner v2.0")
    
    try:
        client = VMOSCloudClient()
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease set your API credentials:")
        print("  export VMOS_CLOUD_AK='your_access_key'")
        print("  export VMOS_CLOUD_SK='your_secret_secret'")
        print("\nOr:")
        print("  export VMOS_API_KEY='your_access_key'")
        print("  export VMOS_API_SECRET='your_secret_secret'")
        return
    
    print("\n🔍 Scanning VMOS Cloud instances...")
    print(f"   API Host: {client.base_url}")
    
    try:
        # Get instance list
        result = await client.cloud_phone_list(page=1, rows=100)
        
        if result.get("code") != 200:
            print(f"\n❌ API Error: {result.get('msg', 'Unknown error')}")
            return
        
        data = result.get("data", {})
        devices = data if isinstance(data, list) else data.get("rows", [])
        
        if not devices:
            print("\n⚠️  No devices found in your VMOS Cloud account.")
            return
        
        print(f"\n✅ Found {len(devices)} device(s):\n")
        
        # Count by status
        status_counts = {}
        online_devices = []
        
        for i, device in enumerate(devices, 1):
            print_device_card(device, i)
            status = device.get("status", 0)
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if status in [1, 100]:  # Online or Running
                online_devices.append(device)
        
        # Summary
        print_header("Summary")
        print(f"  Total Devices:    {len(devices)}")
        print(f"  Online/Running:   {len(online_devices)}")
        print(f"  Offline:          {status_counts.get(0, 0)}")
        print(f"  Booting:          {status_counts.get(10, 0)}")
        
        if online_devices:
            print(f"\n  Online Device Pad Codes:")
            for dev in online_devices:
                print(f"    - {dev.get('padCode')} ({dev.get('deviceName')})")
        
        # Detailed info for online devices
        if online_devices:
            print_header("Detailed Online Device Info")
            for device in online_devices[:3]:  # Limit to first 3
                pad_code = device.get("padCode")
                print(f"\n📱 {pad_code}:")
                
                # Get installed apps
                apps_result = await client.list_installed_apps_realtime(pad_code)
                if apps_result.get("code") == 200:
                    apps_data = apps_result.get("data", {})
                    apps = apps_data if isinstance(apps_data, list) else apps_data.get("list", [])
                    app_names = [a.get("packageName", "N/A") for a in apps[:5]]
                    print(f"   Top Apps: {', '.join(app_names)}")
                
                # Get properties
                props_result = await client.query_instance_properties(pad_code)
                if props_result.get("code") == 200:
                    props_data = props_result.get("data", {})
                    props = props_data if isinstance(props_data, dict) else {}
                    model = props.get("ro.product.model", "N/A")
                    brand = props.get("ro.product.brand", "N/A")
                    print(f"   Model: {brand} {model}")
        
    except Exception as e:
        print(f"\n❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()


async def quick_scan():
    """Quick scan using the bridge module."""
    print_header("Quick VMOS Cloud Scan")
    
    bridge = VMOSCloudBridge()
    
    if not bridge.config.is_configured():
        print("\n❌ API credentials not configured!")
        print("\nPlease set environment variables:")
        print("  export VMOS_CLOUD_AK='your_access_key'")
        print("  export VMOS_CLOUD_SK='your_secret_secret'")
        return
    
    print("\n🔍 Scanning...")
    instances = await bridge.list_instances()
    
    if not instances:
        print("\n⚠️  No instances found or API error.")
        return
    
    print(f"\n✅ Found {len(instances)} instance(s):\n")
    
    for i, inst in enumerate(instances, 1):
        status_icon = "🟢" if inst.status in ["1", "online", "100"] else "🔴"
        print(f"{status_icon} {i}. {inst.pad_code} | {inst.device_name} | {inst.status}")
        print(f"      IP: {inst.device_ip} | Android {inst.android_version}")


async def main():
    """Main entry point."""
    if not check_credentials():
        print_header("VMOS Cloud Device Scanner")
        print("\n❌ API credentials not configured!")
        print("\n📋 Required environment variables:")
        print("   VMOS_CLOUD_AK or VMOS_API_KEY  - Your VMOS Cloud access key")
        print("   VMOS_CLOUD_SK or VMOS_API_SECRET - Your VMOS Cloud secret key")
        print("\n💡 Example:")
        print("   export VMOS_CLOUD_AK='abc123def456'")
        print("   export VMOS_CLOUD_SK='xyz789uvw012'")
        print("   python3 vmos_cloud_device_scanner.py")
        print("\n📝 Get your API keys from: https://console.vmoscloud.com")
        return 1
    
    # Run comprehensive scan
    await scan_with_client()
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
