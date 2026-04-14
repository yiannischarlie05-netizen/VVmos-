#!/usr/bin/env python3
"""
OnePlus Device Connector & Shell Tester
Connects to OnePlus devices via ADB and runs diagnostic commands.
"""

import subprocess
import sys
import time
from typing import Tuple, Optional

sys.path.insert(0, "/home/debian/Downloads/vmos-titan-unified")

from vmos_titan.core.adb_utils import (
    adb, adb_shell, ensure_adb_root, 
    is_device_connected, reconnect_device
)


def list_devices() -> list:
    """List all connected ADB devices."""
    result = subprocess.run(
        ["adb", "devices", "-l"],
        capture_output=True, text=True
    )
    devices = []
    for line in result.stdout.strip().split('\n')[1:]:
        if line.strip() and not line.startswith('*'):
            parts = line.split()
            if len(parts) >= 2:
                device_id = parts[0]
                status = parts[1]
                # Parse additional info
                info = {}
                for part in parts[2:]:
                    if ':' in part:
                        k, v = part.split(':', 1)
                        info[k] = v
                devices.append({
                    'id': device_id,
                    'status': status,
                    'info': info
                })
    return devices


def find_oneplus_device(devices: list) -> Optional[str]:
    """Find OnePlus device from device list."""
    for dev in devices:
        dev_id = dev['id']
        info = dev['info']
        # Check device properties for OnePlus
        model = adb_shell(dev_id, "getprop ro.product.model")
        brand = adb_shell(dev_id, "getprop ro.product.brand")
        manufacturer = adb_shell(dev_id, "getprop ro.product.manufacturer")
        
        if 'oneplus' in model.lower() or 'oneplus' in brand.lower() or 'oneplus' in manufacturer.lower():
            return dev_id
        
        # Also check USB device info
        if 'OnePlus' in str(info) or 'oneplus' in str(info).lower():
            return dev_id
    
    return None


def test_oneplus_device(target: str) -> dict:
    """Run diagnostic tests on OnePlus device."""
    results = {
        'target': target,
        'connected': False,
        'root': False,
        'tests': {}
    }
    
    # Check connection
    if not is_device_connected(target):
        print(f"Device {target} not connected, attempting reconnect...")
        if not reconnect_device(target):
            results['error'] = "Failed to connect to device"
            return results
    
    results['connected'] = True
    print(f"✓ Connected to {target}")
    
    # Test 1: Basic shell
    print("\n--- Test 1: Basic Shell Commands ---")
    ok, out = adb(target, "shell echo 'TEST_OK'")
    results['tests']['echo'] = {'ok': ok, 'output': out}
    print(f"  Echo test: {'✓ PASS' if ok and 'TEST_OK' in out else '✗ FAIL'}")
    
    # Test 2: Device properties
    print("\n--- Test 2: Device Properties ---")
    props = {
        'ro.product.model': adb_shell(target, "getprop ro.product.model"),
        'ro.product.brand': adb_shell(target, "getprop ro.product.brand"),
        'ro.product.device': adb_shell(target, "getprop ro.product.device"),
        'ro.build.version.release': adb_shell(target, "getprop ro.build.version.release"),
        'ro.build.fingerprint': adb_shell(target, "getprop ro.build.fingerprint"),
    }
    results['tests']['properties'] = props
    for k, v in props.items():
        print(f"  {k}: {v}")
    
    # Test 3: Root access
    print("\n--- Test 3: Root Access ---")
    root_ok = ensure_adb_root(target)
    results['root'] = root_ok
    print(f"  Root: {'✓ AVAILABLE' if root_ok else '✗ NOT AVAILABLE'}")
    
    # Test 4: System commands (if root)
    if root_ok:
        print("\n--- Test 4: System Commands (Root) ---")
        cmds = [
            ("whoami", "whoami"),
            ("id", "id"),
            ("ls /data", "ls -la /data/ | head -5"),
            ("cpuinfo", "cat /proc/cpuinfo | head -3"),
            ("meminfo", "cat /proc/meminfo | head -3"),
        ]
        for name, cmd in cmds:
            out = adb_shell(target, cmd)
            results['tests'][name] = out
            print(f"  {name}: {out[:50] if out else 'N/A'}")
    
    # Test 5: Package manager
    print("\n--- Test 5: Package Manager ---")
    out = adb_shell(target, "pm list packages | grep -i oneplus | head -3")
    results['tests']['oneplus_packages'] = out
    print(f"  OnePlus packages: {out if out else 'None found'}")
    
    # Test 6: Battery status
    print("\n--- Test 6: Battery Status ---")
    out = adb_shell(target, "dumpsys battery | grep -E 'level|status|temp' | head -5")
    results['tests']['battery'] = out
    print(f"  Battery: {out if out else 'N/A'}")
    
    # Test 7: Network
    print("\n--- Test 7: Network ---")
    out = adb_shell(target, "ifconfig | grep -A2 'wlan0\\|eth0' | head -6")
    results['tests']['network'] = out
    print(f"  Network: {out[:100] if out else 'N/A'}")
    
    return results


def main():
    print("=" * 60)
    print("  OnePlus Device Connector & Tester")
    print("=" * 60)
    
    # List devices
    print("\n🔍 Scanning for devices...")
    devices = list_devices()
    
    if not devices:
        print("\n❌ No devices found!")
        print("\nMake sure:")
        print("  1. USB debugging is enabled on the OnePlus device")
        print("  2. Device is connected via USB")
        print("  3. ADB is installed: sudo apt install android-tools-adb")
        print("\nOr for wireless ADB:")
        print("  adb connect <device_ip>:5555")
        return 1
    
    print(f"\n📱 Found {len(devices)} device(s):")
    for i, dev in enumerate(devices, 1):
        print(f"  {i}. {dev['id']} - {dev['status']}")
    
    # Find OnePlus device
    oneplus_target = find_oneplus_device(devices)
    
    if not oneplus_target:
        print("\n⚠️  No OnePlus device detected by model/brand.")
        print("Available devices:")
        for dev in devices:
            print(f"  - {dev['id']}")
        
        # Ask user to select
        if len(devices) == 1:
            oneplus_target = devices[0]['id']
            print(f"\nUsing only available device: {oneplus_target}")
        else:
            try:
                choice = input("\nEnter device ID to test (or 'all' to test all): ").strip()
                if choice.lower() == 'all':
                    oneplus_targets = [d['id'] for d in devices]
                else:
                    oneplus_targets = [choice]
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.")
                return 1
    else:
        oneplus_targets = [oneplus_target]
    
    # Run tests
    all_results = []
    for target in oneplus_targets:
        print(f"\n{'='*60}")
        print(f"Testing device: {target}")
        print(f"{'='*60}")
        
        results = test_oneplus_device(target)
        all_results.append(results)
        
        # Summary
        print(f"\n{'='*60}")
        print("  TEST SUMMARY")
        print(f"{'='*60}")
        print(f"  Connected: {'✓' if results['connected'] else '✗'}")
        print(f"  Root Access: {'✓' if results['root'] else '✗'}")
        print(f"  Tests Passed: {sum(1 for t in results['tests'].values() if t)}/{len(results['tests'])}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
