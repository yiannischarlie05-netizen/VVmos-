#!/usr/bin/env python3
"""
VMOS Device Poll & Escape - Waits for device to be ready
"""

import asyncio
import json
import subprocess
import sys
import time

sys.path.insert(0, "/home/debian/Downloads/vmos-titan-unified")

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
DEVICE = "ACP251008GUOEEHB"


async def poll_device_ready(client, max_attempts=20):
    """Poll until device is online."""
    print("  Polling for device ready...")
    for i in range(max_attempts):
        info = await client.cloud_phone_info(DEVICE)
        if info.get("code") == 200:
            data = info.get("data", {})
            status = data.get("status")
            print(f"    Attempt {i+1}: status={status}")
            if status == 100:  # Running
                return True
        await asyncio.sleep(5)
    return False


async def main():
    print("=" * 60)
    print(f"  VMOS Escape Analysis - {DEVICE}")
    print("=" * 60)
    
    client = VMOSCloudClient(ak=AK, sk=SK)
    
    # Ensure device is running
    print("\n[1] Ensuring device is online...")
    info = await client.cloud_phone_info(DEVICE)
    status = info.get("data", {}).get("status") if info.get("code") == 200 else None
    
    if status != 100:
        print(f"  Device not running (status={status}), starting...")
        await client.instance_restart([DEVICE])
        ready = await poll_device_ready(client)
        if not ready:
            print("  ✗ Device failed to come online")
            return
    
    print("  ✓ Device online!")
    
    # Get ADB info
    print("\n[2] Getting ADB connection...")
    adb_info = await client.get_adb_info(DEVICE, enable=True)
    
    if adb_info.get("code") != 200:
        print(f"  ✗ ADB info failed: {adb_info}")
        return
    
    data = adb_info.get("data", {})
    host = data.get("host", "")
    port = data.get("port", "")
    
    if not host:
        print("  ⚠ No host in ADB info, trying direct IP from device info...")
        # Try to use device IP
        if info.get("code") == 200:
            host = info["data"].get("deviceIp", "")
            port = "5555"
    
    if not host:
        print("  ✗ Cannot determine ADB host")
        return
    
    target = f"{host}:{port}"
    print(f"  ADB Target: {target}")
    
    # Connect ADB
    print("\n[3] Connecting ADB...")
    subprocess.run(["adb", "connect", target], capture_output=True)
    await asyncio.sleep(3)
    
    # Test connection
    test = subprocess.run(
        ["adb", "-s", target, "shell", "echo", "READY"],
        capture_output=True, text=True, timeout=10
    )
    
    if "READY" not in test.stdout:
        print(f"  ✗ ADB not responding")
        print(f"    stdout: {test.stdout}")
        print(f"    stderr: {test.stderr}")
        return
    
    print("  ✓ ADB connected and responsive!")
    
    # Container escape analysis
    print("\n" + "=" * 60)
    print("  CONTAINER ESCAPE ANALYSIS")
    print("=" * 60)
    
    findings = {}
    
    # Define all tests
    tests = [
        # Filesystem
        ("FS-01", "proc_root", "ls -la /proc/"),
        ("FS-02", "system_perms", "ls -ld /system"),
        ("FS-03", "data_perms", "ls -ld /data"),
        ("FS-04", "root_dir", "ls -la / | head -15"),
        ("FS-05", "dev_block", "ls /dev/block/ | head -10"),
        ("FS-06", "mnt_namespace", "ls -la /proc/self/ns/mnt"),
        ("FS-07", "cgroup", "cat /proc/self/cgroup"),
        
        # Network
        ("NET-01", "net_namespace", "ls -la /proc/self/ns/net"),
        ("NET-02", "interfaces", "ifconfig -a 2>/dev/null | head -20"),
        ("NET-03", "ip_addr", "ip addr show"),
        ("NET-04", "routes", "ip route show"),
        ("NET-05", "arp", "cat /proc/net/arp"),
        ("NET-06", "tcp_conns", "cat /proc/net/tcp | wc -l"),
        ("NET-07", "dns", "cat /etc/resolv.conf"),
        
        # Processes
        ("PROC-01", "pid_namespace", "ls -la /proc/self/ns/pid"),
        ("PROC-02", "init", "cat /proc/1/comm"),
        ("PROC-03", "ps_all", "ps -A | head -15"),
        ("PROC-04", "pid_count", "ls /proc/ | grep -E '^[0-9]+$' | wc -l"),
        
        # Privileges
        ("PRIV-01", "whoami", "whoami"),
        ("PRIV-02", "id", "id"),
        ("PRIV-03", "caps", "cat /proc/self/status | grep -i cap"),
        ("PRIV-04", "selinux", "getenforce 2>/dev/null || echo 'N/A'"),
        
        # Device info
        ("INFO-01", "kernel", "uname -a"),
        ("INFO-02", "model", "getprop ro.product.model"),
        ("INFO-03", "brand", "getprop ro.product.brand"),
        ("INFO-04", "android", "getprop ro.build.version.release"),
        ("INFO-05", "fingerprint", "getprop ro.build.fingerprint"),
        ("INFO-06", "board", "getprop ro.product.board"),
        
        # Escape vectors
        ("ESC-01", "system_rw", "touch /system/.test 2>&1 && rm /system/.test && echo 'RW' || echo 'RO'"),
        ("ESC-02", "data_rw", "touch /data/local/tmp/.test && rm /data/local/tmp/.test && echo 'RW'"),
        ("ESC-03", "proc_host", "ls /proc/host/ 2>/dev/null || echo 'NO_HOST'"),
        ("ESC-04", "sys_kernel", "ls /sys/kernel/ 2>/dev/null | head -5"),
    ]
    
    print(f"\nRunning {len(tests)} escape tests...\n")
    
    for code, name, cmd in tests:
        result = subprocess.run(
            ["adb", "-s", target, "shell", cmd],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        findings[name] = {
            "cmd": cmd,
            "output": output[:500],
            "error": error[:200] if error else None,
            "status": "success" if result.returncode == 0 else "failed"
        }
        
        status_icon = "✓" if output and result.returncode == 0 else "✗"
        display = output[:50].replace('\n', ' ')
        print(f"{status_icon} [{code}] {name}: {display}")
    
    # Network discovery
    print("\n" + "-" * 60)
    print("  NETWORK DISCOVERY")
    print("-" * 60)
    
    # Get gateway
    gw_result = subprocess.run(
        ["adb", "-s", target, "shell", "ip route | grep default | awk '{print $3}' | head -1"],
        capture_output=True, text=True, timeout=10
    )
    gateway = gw_result.stdout.strip()
    print(f"\nGateway: {gateway}")
    
    if gateway:
        # ARP scan
        arp_result = subprocess.run(
            ["adb", "-s", target, "shell", "cat /proc/net/arp"],
            capture_output=True, text=True, timeout=10
        )
        arp_lines = arp_result.stdout.strip().split('\n')
        print(f"\nARP Table ({len(arp_lines)-1} entries):")
        neighbors = []
        for line in arp_lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 4:
                ip, mac = parts[0], parts[3]
                if mac != "00:00:00:00:00:00":
                    neighbors.append({"ip": ip, "mac": mac})
                    print(f"  {ip} -> {mac}")
        
        findings["neighbors"] = neighbors
        
        # Port scan
        print(f"\nPort scanning {gateway}...")
        open_ports = []
        for port in [22, 80, 443, 5555, 8080, 9090]:
            port_result = subprocess.run(
                ["adb", "-s", target, "shell", f"timeout 2 nc -z {gateway} {port} 2>/dev/null && echo 'OPEN' || echo 'CLOSED'"],
                capture_output=True, text=True, timeout=5
            )
            status = port_result.stdout.strip()
            if status == "OPEN":
                open_ports.append(port)
                print(f"  ✓ {port}/tcp OPEN")
            else:
                print(f"  ✗ {port}/tcp closed")
        
        findings["gateway_ports"] = open_ports
    
    # Summary analysis
    print("\n" + "=" * 60)
    print("  ESCAPE ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Check key indicators
    system_rw = findings.get("system_rw", {}).get("output", "")
    data_rw = findings.get("data_rw", {}).get("output", "")
    proc_host = findings.get("proc_host", {}).get("output", "")
    
    print(f"\nContainer Type: Linux namespace (VMOS Cloud)")
    print(f"/system: {'WRITABLE' if 'RW' in system_rw else 'Read-only'}")
    print(f"/data: {'Writable' if 'RW' in data_rw else 'Unknown'}")
    print(f"Host /proc: {'Accessible' if 'NO_HOST' not in proc_host else 'Isolated'}")
    print(f"Neighbors found: {len(findings.get('neighbors', []))}")
    print(f"Gateway open ports: {findings.get('gateway_ports', [])}")
    
    # Save report
    report_file = f"vmos_escape_final_{DEVICE}_{int(time.time())}.json"
    with open(report_file, "w") as f:
        json.dump({
            "device": DEVICE,
            "adb_target": target,
            "findings": findings,
            "summary": {
                "total_tests": len(tests),
                "neighbors": len(findings.get("neighbors", [])),
                "gateway_ports": findings.get("gateway_ports", []),
                "system_writable": "RW" in system_rw
            },
            "timestamp": time.time()
        }, f, indent=2)
    
    print(f"\n📄 Complete report: {report_file}")
    print("\n✅ Escape analysis complete!")


if __name__ == "__main__":
    asyncio.run(main())
