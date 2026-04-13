#!/usr/bin/env python3
"""
VMOS Device Activator & Deep Container Escape
Restarts device if needed, then performs deep escape analysis
"""

import asyncio
import json
import subprocess
import sys
import time

sys.path.insert(0, "/home/debian/Downloads/vmos-titan-unified")

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
DEVICE = "ACP251008GUOEEHB"


async def main():
    print("=" * 60)
    print("  VMOS Device Activator & Deep Escape")
    print(f"  Target: {DEVICE}")
    print("=" * 60)
    
    client = VMOSCloudClient(ak=AK, sk=SK)
    
    # Check device status
    print("\n[1] Checking device status...")
    info = await client.cloud_phone_info(DEVICE)
    status = info.get("data", {}).get("status") if info.get("code") == 200 else None
    print(f"  Status: {status}")
    
    # Restart if not running
    if status != 100:
        print(f"\n[2] Device not running (status={status}), restarting...")
        restart = await client.instance_restart([DEVICE])
        print(f"  Restart: {restart.get('code')} - {restart.get('msg', 'OK')}")
        print("  Waiting 30 seconds for boot...")
        await asyncio.sleep(30)
    
    # Enable ADB
    print("\n[3] Enabling ADB...")
    enable = await client.enable_adb([DEVICE])
    print(f"  Enable: {enable.get('code')}")
    
    # Get ADB info
    adb_info = await client.get_adb_info(DEVICE, enable=True)
    print(f"  ADB Info: {adb_info.get('code')}")
    
    if adb_info.get("code") == 200:
        data = adb_info.get("data", {})
        host = data.get("host", "")
        port = data.get("port", "")
        print(f"  Host: {host}:{port}")
        
        if host and port:
            target = f"{host}:{port}"
            
            # Connect ADB
            print(f"\n[4] Connecting ADB to {target}...")
            subprocess.run(["adb", "connect", target], capture_output=True)
            time.sleep(3)
            
            # Test connection
            test = subprocess.run(
                ["adb", "-s", target, "shell", "echo", "CONNECTED"],
                capture_output=True, text=True, timeout=10
            )
            
            if "CONNECTED" in test.stdout:
                print("  ✓ ADB Connected!")
                
                # Deep escape analysis
                print("\n" + "=" * 60)
                print("  DEEP CONTAINER ESCAPE ANALYSIS")
                print("=" * 60)
                
                findings = {}
                
                # 1. Filesystem checks
                print("\n[FS] Filesystem Escape Vectors:")
                cmds = [
                    ("proc_self", "ls -la /proc/self/"),
                    ("root_dir", "ls -la / | head -20"),
                    ("system_rw", "touch /system/.test 2>&1; rm -f /system/.test 2>&1; echo $?"),
                    ("data_rw", "touch /data/local/tmp/.test && rm /data/local/tmp/.test && echo 'RW_OK'"),
                    ("dev_block", "ls -la /dev/block/ | head -10"),
                    ("proc_1", "ls -la /proc/1/ | head -10"),
                    ("sys_class", "ls /sys/class/ | head -10"),
                    ("mnt_ns", "ls -la /proc/self/ns/mnt"),
                    ("net_ns", "ls -la /proc/self/ns/net"),
                    ("pid_ns", "ls -la /proc/self/ns/pid"),
                ]
                
                for name, cmd in cmds:
                    result = subprocess.run(
                        ["adb", "-s", target, "shell", cmd],
                        capture_output=True, text=True, timeout=15
                    )
                    output = result.stdout.strip()
                    findings[name] = output[:200]
                    status = "✓" if output else "✗"
                    print(f"  {status} {name}: {output[:60] if output else 'N/A'}")
                
                # 2. Network analysis
                print("\n[NET] Network Analysis:")
                net_cmds = [
                    ("ifconfig", "ifconfig -a | head -20"),
                    ("ip_addr", "ip addr show"),
                    ("ip_route", "ip route show"),
                    ("arp_table", "cat /proc/net/arp"),
                    ("net_dev", "cat /proc/net/dev"),
                    ("tcp_conns", "cat /proc/net/tcp | head -10"),
                    ("resolv", "cat /etc/resolv.conf"),
                    ("hosts", "cat /etc/hosts"),
                ]
                
                for name, cmd in net_cmds:
                    result = subprocess.run(
                        ["adb", "-s", target, "shell", cmd],
                        capture_output=True, text=True, timeout=10
                    )
                    output = result.stdout.strip()
                    findings[name] = output[:300]
                    status = "✓" if output else "✗"
                    print(f"  {status} {name}: {output[:60] if output else 'N/A'}")
                
                # 3. Process analysis
                print("\n[PROC] Process Analysis:")
                proc_cmds = [
                    ("ps_all", "ps -A | head -20"),
                    ("init_comm", "cat /proc/1/comm"),
                    ("init_cmdline", "cat /proc/1/cmdline"),
                    ("our_pid", "echo $$"),
                    ("pids_visible", "ls /proc/ | grep -E '^[0-9]+$' | wc -l"),
                    ("other_containers", "ps -A | grep -E 'cloudphone|vmos|pad' | head -5"),
                ]
                
                for name, cmd in proc_cmds:
                    result = subprocess.run(
                        ["adb", "-s", target, "shell", cmd],
                        capture_output=True, text=True, timeout=10
                    )
                    output = result.stdout.strip()
                    findings[name] = output[:200]
                    status = "✓" if output else "✗"
                    print(f"  {status} {name}: {output[:60] if output else 'N/A'}")
                
                # 4. Privilege analysis
                print("\n[PRIV] Privilege Analysis:")
                priv_cmds = [
                    ("whoami", "whoami"),
                    ("id", "id"),
                    ("groups", "groups"),
                    ("caps", "cat /proc/self/status | grep Cap"),
                    ("selinux", "getenforce"),
                    ("is_root", "id -u"),
                ]
                
                for name, cmd in priv_cmds:
                    result = subprocess.run(
                        ["adb", "-s", target, "shell", cmd],
                        capture_output=True, text=True, timeout=10
                    )
                    output = result.stdout.strip()
                    findings[name] = output[:100]
                    status = "✓" if output else "✗"
                    print(f"  {status} {name}: {output[:60] if output else 'N/A'}")
                
                # 5. Host discovery
                print("\n[HOST] Host Discovery:")
                
                # Get gateway
                gw_result = subprocess.run(
                    ["adb", "-s", target, "shell", "ip route | grep default | awk '{print $3}'"],
                    capture_output=True, text=True, timeout=10
                )
                gateway = gw_result.stdout.strip()
                print(f"  Gateway: {gateway}")
                
                if gateway:
                    # Ping gateway
                    ping_gw = subprocess.run(
                        ["adb", "-s", target, "shell", f"ping -c 1 -W 2 {gateway} >/dev/null 2>&1 && echo 'ALIVE' || echo 'TIMEOUT'"],
                        capture_output=True, text=True, timeout=5
                    )
                    print(f"  Gateway ping: {ping_gw.stdout.strip()}")
                    
                    # Port scan gateway
                    print(f"  Port scanning {gateway}...")
                    for port in [22, 80, 443, 5555, 8080]:
                        port_result = subprocess.run(
                            ["adb", "-s", target, "shell", f"nc -z -w 1 {gateway} {port} 2>/dev/null && echo 'OPEN' || echo 'CLOSED'"],
                            capture_output=True, text=True, timeout=5
                        )
                        status = port_result.stdout.strip()
                        icon = "✓" if status == "OPEN" else "✗"
                        print(f"    {icon} {port}/tcp: {status}")
                
                # 6. Device info
                print("\n[INFO] Device Properties:")
                info_cmds = [
                    ("kernel", "uname -a"),
                    ("android_ver", "getprop ro.build.version.release"),
                    ("model", "getprop ro.product.model"),
                    ("brand", "getprop ro.product.brand"),
                    ("fingerprint", "getprop ro.build.fingerprint"),
                    ("hardware", "getprop ro.hardware"),
                    ("board", "getprop ro.product.board"),
                    ("device", "getprop ro.product.device"),
                ]
                
                for name, cmd in info_cmds:
                    result = subprocess.run(
                        ["adb", "-s", target, "shell", cmd],
                        capture_output=True, text=True, timeout=10
                    )
                    output = result.stdout.strip()
                    findings[name] = output
                    status = "✓" if output else "✗"
                    print(f"  {status} {name}: {output[:60] if output else 'N/A'}")
                
                # Save report
                report_file = f"vmos_deep_escape_{DEVICE}_{int(time.time())}.json"
                with open(report_file, "w") as f:
                    json.dump({
                        "device": DEVICE,
                        "target": target,
                        "findings": findings,
                        "timestamp": time.time()
                    }, f, indent=2)
                
                print(f"\n📄 Report saved: {report_file}")
                print("\n✅ Deep escape analysis complete!")
                
            else:
                print(f"  ✗ ADB connection failed")
                print(f"    Output: {test.stdout}")
                print(f"    Error: {test.stderr}")
    else:
        print(f"\n✗ Could not get ADB info")


if __name__ == "__main__":
    asyncio.run(main())
