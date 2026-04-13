#!/usr/bin/env python3
"""
OnePlus Device Connector & Shell Commander
Connects to OnePlus devices via ADB (USB or wireless) and runs shell commands.
"""

import subprocess
import sys
import time
import os
from typing import Tuple, Optional, List

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
                info = {}
                for part in parts[2:]:
                    if ':' in part:
                        k, v = part.split(':', 1)
                        info[k] = v
                devices.append({'id': device_id, 'status': status, 'info': info})
    return devices


def connect_wireless(ip: str, port: int = 5555) -> bool:
    """Connect to device via wireless ADB."""
    print(f"Connecting to {ip}:{port}...")
    result = subprocess.run(
        ["adb", "connect", f"{ip}:{port}"],
        capture_output=True, text=True
    )
    success = result.returncode == 0 and "connected" in result.stdout.lower()
    if success:
        print(f"✓ Connected to {ip}:{port}")
    else:
        print(f"✗ Failed: {result.stdout} {result.stderr}")
    return success


def identify_device(target: str) -> dict:
    """Get device identification info."""
    return {
        'model': adb_shell(target, "getprop ro.product.model"),
        'brand': adb_shell(target, "getprop ro.product.brand"),
        'device': adb_shell(target, "getprop ro.product.device"),
        'manufacturer': adb_shell(target, "getprop ro.product.manufacturer"),
        'android_version': adb_shell(target, "getprop ro.build.version.release"),
        'fingerprint': adb_shell(target, "getprop ro.build.fingerprint"),
        'serial': adb_shell(target, "getprop ro.serialno"),
    }


def run_shell_tests(target: str) -> dict:
    """Run comprehensive shell command tests."""
    results = {'target': target, 'tests': {}}
    
    print(f"\n{'='*60}")
    print("  RUNNING SHELL COMMAND TESTS")
    print(f"{'='*60}")
    
    # Basic tests
    tests = [
        ("echo", "echo 'Hello OnePlus'", "Basic echo test"),
        ("whoami", "whoami", "Current user"),
        ("id", "id", "User ID info"),
        ("pwd", "pwd", "Current directory"),
        ("uname", "uname -a", "Kernel info"),
    ]
    
    # Device info tests
    tests.extend([
        ("cpuinfo", "cat /proc/cpuinfo | head -5", "CPU information"),
        ("meminfo", "cat /proc/meminfo | head -3", "Memory info"),
        ("battery", "dumpsys battery | grep -E 'level|status|scale' | head -4", "Battery status"),
        ("storage", "df -h /data | tail -1", "Storage usage"),
    ])
    
    # Network tests
    tests.extend([
        ("wifi_ip", "ifconfig wlan0 2>/dev/null || ip addr show wlan0 2>/dev/null | grep 'inet ' | head -1", "WiFi IP"),
        ("network", "ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo 'Internet: OK' || echo 'Internet: FAIL'", "Internet connectivity"),
    ])
    
    # OnePlus specific
    tests.extend([
        ("oneplus_props", "getprop | grep -i oneplus | head -5", "OnePlus properties"),
        ("oxygen", "getprop ro.oxygen.version 2>/dev/null || echo 'Not OxygenOS'", "OxygenOS version"),
    ])
    
    for test_name, cmd, description in tests:
        print(f"\n📋 {description} ({test_name}):")
        output = adb_shell(target, cmd)
        results['tests'][test_name] = output
        if output:
            print(f"   {output[:100]}")
        else:
            print(f"   (no output)")
    
    return results


def interactive_shell(target: str):
    """Interactive shell mode."""
    print(f"\n{'='*60}")
    print("  INTERACTIVE SHELL MODE")
    print("  Type 'exit' or 'quit' to return to menu")
    print(f"{'='*60}\n")
    
    while True:
        try:
            cmd = input(f"{target}$ ").strip()
            if cmd.lower() in ('exit', 'quit', 'q'):
                break
            if not cmd:
                continue
            
            output = adb_shell(target, cmd, timeout=30)
            if output:
                print(output)
            else:
                print("(no output or command failed)")
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except EOFError:
            break


def quick_commands_menu(target: str):
    """Quick commands menu."""
    commands = {
        '1': ('Show running apps', "ps -A | grep -v 'S sleeping' | head -10"),
        '2': ('Show top processes', "top -n 1 | head -15"),
        '3': ('List installed packages', "pm list packages | head -10"),
        '4': ('Show device properties', "getprop | grep -E 'ro\\.(product|build)\\.' | head -10"),
        '5': ('Show screen info', "wm size && wm density"),
        '6': ('Battery stats', "dumpsys battery"),
        '7': ('Memory usage', "cat /proc/meminfo"),
        '8': ('Storage info', "df -h"),
        '9': ('Network interfaces', "ifconfig -a | head -20"),
        '10': ('Reboot device', "reboot"),
    }
    
    while True:
        print(f"\n{'='*60}")
        print("  QUICK COMMANDS MENU")
        print(f"{'='*60}")
        for key, (desc, _) in commands.items():
            print(f"  {key}. {desc}")
        print("  0. Back to main menu")
        
        choice = input("\nSelect command: ").strip()
        if choice == '0':
            break
        
        if choice in commands:
            desc, cmd = commands[choice]
            print(f"\n▶ Running: {desc}")
            print(f"  Command: {cmd}")
            output = adb_shell(target, cmd, timeout=30)
            if output:
                print(f"\n{output}")
            else:
                print("(no output)")
            input("\nPress Enter to continue...")


def main():
    print("=" * 60)
    print("  OnePlus Device Connector & Shell Commander")
    print("=" * 60)
    
    target = None
    
    # Check for existing connection
    devices = list_devices()
    
    if devices:
        print(f"\n📱 Found {len(devices)} connected device(s):")
        for i, dev in enumerate(devices, 1):
            print(f"  {i}. {dev['id']} [{dev['status']}]")
        
        if len(devices) == 1:
            target = devices[0]['id']
            print(f"\n✓ Auto-selected: {target}")
        else:
            choice = input("\nSelect device (number) or enter IP:port: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(devices):
                target = devices[int(choice)-1]['id']
            elif ':' in choice:
                ip, port = choice.split(':')
                if connect_wireless(ip, int(port)):
                    target = f"{ip}:{port}"
            else:
                target = choice
    else:
        print("\n⚠️  No devices connected.")
        print("\nConnection options:")
        print("  1. Connect via IP (wireless ADB)")
        print("  2. Wait and retry")
        print("  3. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            ip = input("Enter device IP: ").strip()
            port = input("Enter port [5555]: ").strip() or "5555"
            if connect_wireless(ip, int(port)):
                target = f"{ip}:{port}"
        elif choice == '2':
            print("Waiting for device... (Ctrl+C to cancel)")
            for _ in range(30):
                time.sleep(2)
                devices = list_devices()
                if devices:
                    target = devices[0]['id']
                    print(f"✓ Device connected: {target}")
                    break
            if not target:
                print("No device found after 60 seconds.")
                return 1
        else:
            return 0
    
    if not target:
        print("No target selected.")
        return 1
    
    # Verify connection
    print(f"\n🔌 Verifying connection to {target}...")
    if not is_device_connected(target):
        print("✗ Cannot connect to device.")
        return 1
    
    print("✓ Connection verified")
    
    # Identify device
    print("\n📋 Device Information:")
    info = identify_device(target)
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    is_oneplus = 'oneplus' in str(info).lower()
    if is_oneplus:
        print("\n✓ OnePlus device detected!")
    
    # Enable root if possible
    print("\n🔓 Checking root access...")
    root_ok = ensure_adb_root(target)
    if root_ok:
        print("✓ Root access enabled")
    else:
        print("⚠ Root not available (limited to user commands)")
    
    # Main menu
    while True:
        print(f"\n{'='*60}")
        print("  MAIN MENU")
        print(f"  Target: {target}")
        print(f"{'='*60}")
        print("  1. Run comprehensive tests")
        print("  2. Interactive shell")
        print("  3. Quick commands menu")
        print("  4. Show device info")
        print("  5. Check connection status")
        print("  6. Reconnect device")
        print("  0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            run_shell_tests(target)
        elif choice == '2':
            interactive_shell(target)
        elif choice == '3':
            quick_commands_menu(target)
        elif choice == '4':
            info = identify_device(target)
            for key, value in info.items():
                print(f"  {key}: {value}")
        elif choice == '5':
            connected = is_device_connected(target)
            print(f"  Connection status: {'✓ Connected' if connected else '✗ Disconnected'}")
        elif choice == '6':
            reconnect_device(target)
        elif choice == '0':
            print("Goodbye!")
            break
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
