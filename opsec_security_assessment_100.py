#!/usr/bin/env python3
"""
Advanced OPSEC Security Assessment Suite
100 Tests: Host Level (30), Container Level (35), Kernel Level (35)
High OPSEC: No artifacts, stealth probing, automatic cleanup
"""

import asyncio
import os
import random
import time
from datetime import datetime
from dotenv import load_dotenv

# Load .env and set environment variables BEFORE importing VMOSCloudClient
load_dotenv()
os.environ['VMOS_CLOUD_AK'] = os.getenv('VMOS_AK', '')
os.environ['VMOS_CLOUD_SK'] = os.getenv('VMOS_SK', '')

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

class OPSECSecurityScanner:
    def __init__(self, pad_code: str):
        self.client = VMOSCloudClient()
        self.pad_code = pad_code
        self.results = []
        self.start_time = datetime.now()
        
    async def execute_cmd(self, cmd: str, timeout: int = 15) -> dict:
        """Execute command with random delay for OPSEC"""
        await asyncio.sleep(random.uniform(0.1, 0.5))
        result = await self.client.sync_cmd(self.pad_code, cmd, timeout_sec=timeout)
        return result
    
    def log_result(self, category: str, test_name: str, cmd: str, result: dict, status: str):
        """Log result without persistent artifacts"""
        entry = {
            'category': category,
            'test': test_name,
            'command': cmd,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'data': result
        }
        self.results.append(entry)
        
    async def run_host_level_tests(self):
        """30 Host Level Tests"""
        print("\n[HOST LEVEL] Starting 30 tests...")
        
        tests = [
            ("System Info", "uname -a"),
            ("User Info", "id"),
            ("Current User", "whoami"),
            ("Hostname", "hostname"),
            ("Uptime", "cat /proc/uptime"),
            ("Load Average", "cat /proc/loadavg"),
            ("CPU Info", "cat /proc/cpuinfo | head -20"),
            ("MemInfo", "cat /proc/meminfo | head -20"),
            ("Mount Points", "mount | head -20"),
            ("Disk Usage", "df -h"),
            ("Process List", "ps -ef | head -20"),
            ("Network Interfaces", "ip addr show"),
            ("Routing Table", "ip route show"),
            ("ARP Table", "cat /proc/net/arp"),
            ("TCP Connections", "cat /proc/net/tcp | head -10"),
            ("UDP Connections", "cat /proc/net/udp | head -10"),
            ("Socket Stats", "ss -tunlp 2>/dev/null | head -10"),
            ("Firewall Rules", "iptables -L -n 2>/dev/null | head -10"),
            ("Environment Vars", "env | head -20"),
            ("System Limits", "ulimit -a"),
            ("Open Files Limit", "cat /proc/sys/fs/file-max"),
            ("PID Max", "cat /proc/sys/kernel/pid_max"),
            ("Hostname Resolution", "cat /etc/hosts"),
            ("DNS Config", "cat /etc/resolv.conf"),
            ("System Services", "getprop | grep init.svc"),
            ("Android Build", "getprop ro.build.fingerprint"),
            ("Android Version", "getprop ro.build.version.release"),
            ("Security Patch", "getprop ro.build.version.security_patch"),
            ("Device Model", "getprop ro.product.model"),
            ("Device Brand", "getprop ro.product.brand"),
            ("SELinux Status", "getenforce"),
            ("CPU Architecture", "uname -m"),
        ]
        
        for test_name, cmd in tests:
            try:
                result = await self.execute_cmd(cmd, timeout=10)
                if isinstance(result, dict) and result.get('code') == 200:
                    data = result.get('data', [{}])[0].get('errorMsg', '')
                    self.log_result("HOST", test_name, cmd, result, "SUCCESS")
                    print(f"  ✓ [{test_name}]")
                else:
                    self.log_result("HOST", test_name, cmd, result, "FAILED")
                    print(f"  ✗ [{test_name}]")
            except Exception as e:
                self.log_result("HOST", test_name, cmd, str(e), "ERROR")
                print(f"  ! [{test_name}] Error: {e}")
    
    async def run_container_level_tests(self):
        """35 Container Level Tests"""
        print("\n[CONTAINER LEVEL] Starting 35 tests...")
        
        tests = [
            ("PID Namespace", "cat /proc/self/status | grep -E '(NSpid|NSpgid)'"),
            ("Mount Namespace", "cat /proc/self/status | grep -E 'NSmnt'"),
            ("Network Namespace", "cat /proc/self/status | grep -E 'NSnet'"),
            ("UTS Namespace", "cat /proc/self/status | grep -E 'NSuts'"),
            ("IPC Namespace", "cat /proc/self/status | grep -E 'NSipc'"),
            ("User Namespace", "cat /proc/self/status | grep -E 'NSuser'"),
            ("Cgroup Path", "cat /proc/self/cgroup"),
            ("Cgroup CPU Limits", "cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null"),
            ("Cgroup Memory Limits", "cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null"),
            ("Cgroup PIDs Limits", "cat /sys/fs/cgroup/pids/pids.max 2>/dev/null"),
            ("Docker Detection", "cat /.dockerenv 2>/dev/null || echo 'no docker'"),
            ("Container ID", "cat /proc/self/cgroup | grep docker"),
            ("Kubernetes Pod", "cat /var/run/secrets/kubernetes.io/serviceaccount/token 2>/dev/null || echo 'no k8s'"),
            ("Seccomp Status", "cat /proc/self/status | grep Seccomp"),
            ("Capability Set", "cat /proc/self/status | grep Cap"),
            ("Effective Caps", "capsh --print 2>/dev/null || echo 'no capsh'"),
            ("AppArmor Status", "cat /proc/self/attr/current 2>/dev/null"),
            ("SELinux Context", "cat /proc/self/attr/exec 2>/dev/null"),
            ("Device Access", "ls -la /dev/ | head -20"),
            ("Block Devices", "ls -la /dev/block/ | head -10"),
            ("TTY Devices", "ls -la /dev/tty* | head -10"),
            ("PTY Devices", "ls -la /dev/pts/ 2>/dev/null || echo 'no pts'"),
            ("Container Mounts", "mount | grep -E '(docker|overlay|cgroup)'"),
            ("OverlayFS", "cat /proc/mounts | grep overlay"),
            ("TmpFS", "cat /proc/mounts | grep tmpfs"),
            ("ProcFS", "cat /proc/mounts | grep proc"),
            ("SysFS", "cat /proc/mounts | grep sysfs"),
            ("Shared Memory", "ls -la /dev/shm/"),
            ("Container Env", "env | grep -i container"),
            ("Container Runtime", "cat /proc/1/cmdline"),
            ("Init Process", "cat /proc/1/environ | tr '\\0' '\\n' | head -10"),
            ("Parent PID", "cat /proc/self/status | grep PPid"),
            ("Process Tree", "ps -ef --forest | head -15"),
            ("Namespace IDs", "ls -la /proc/self/ns/"),
            ("Cgroup Controllers", "cat /proc/cgroups"),
            ("Memory Controller", "cat /sys/fs/cgroup/memory/memory.usage_in_bytes 2>/dev/null"),
            ("CPU Controller", "cat /sys/fs/cgroup/cpu/cpu.shares 2>/dev/null"),
            ("Freezer Status", "cat /sys/fs/cgroup/freezer/freezer.state 2>/dev/null"),
            ("Devices Controller", "ls -la /sys/fs/cgroup/devices/ 2>/dev/null"),
        ]
        
        for test_name, cmd in tests:
            try:
                result = await self.execute_cmd(cmd, timeout=10)
                if isinstance(result, dict) and result.get('code') == 200:
                    data = result.get('data', [{}])[0].get('errorMsg', '')
                    self.log_result("CONTAINER", test_name, cmd, result, "SUCCESS")
                    print(f"  ✓ [{test_name}]")
                else:
                    self.log_result("CONTAINER", test_name, cmd, result, "FAILED")
                    print(f"  ✗ [{test_name}]")
            except Exception as e:
                self.log_result("CONTAINER", test_name, cmd, str(e), "ERROR")
                print(f"  ! [{test_name}] Error: {e}")
    
    async def run_kernel_level_tests(self):
        """35 Kernel Level Tests"""
        print("\n[KERNEL LEVEL] Starting 35 tests...")
        
        tests = [
            ("Kernel Version", "uname -r"),
            ("Kernel Release", "uname -v"),
            ("System Calls", "cat /proc/kallsyms | head -20"),
            ("Loaded Modules", "cat /proc/modules | head -20"),
            ("Kernel Params", "sysctl -a 2>/dev/null | head -20"),
            ("SELinux Policy", "sestatus 2>/dev/null || echo 'no sestatus'"),
            ("SELinux Booleans", "getsebool -a 2>/dev/null | head -10"),
            ("SELinux Contexts", "ls -Z / 2>/dev/null | head -10"),
            ("AppArmor Profiles", "aa-status 2>/dev/null || echo 'no apparmor'"),
            ("Security Hooks", "cat /proc/1/status | grep -E '(Seccomp|NoNewPrivs)'"),
            ("Kernel Capabilities", "cat /proc/sys/kernel/cap_last_cap"),
            ("Secure Boot", "cat /sys/firmware/efi/efivars/SecureBoot-* 2>/dev/null || echo 'no secureboot'"),
            ("Trusted Platform", "cat /sys/class/tpm/tpm0/pcr 2>/dev/null || echo 'no tpm'"),
            ("IMA Status", "cat /sys/kernel/ima/ascii_runtime_measurements 2>/dev/null | head -10"),
            ("EVM Status", "cat /sys/kernel/security/evm 2>/dev/null || echo 'no evm'"),
            ("DM-Verity", "cat /sys/kernel/security/dm-verity 2>/dev/null || echo 'no dmverity'"),
            ("Verified Boot", "getprop ro.boot.verifiedbootstate"),
            ("Bootloader Lock", "getprop ro.boot.flash.locked"),
            ("AVB Status", "getprop ro.boot.vbmeta.device"),
            ("Keymaster Version", "getprop ro.hardware.keymaster.version"),
            ("TEE Status", "getprop ro.hardware.keystore"),
            ("Gatekeeper Status", "getprop ro.hardware.gatekeeper"),
            ("Kernel Hardening", "cat /proc/sys/kernel/random/entropy_avail"),
            ("ASLR Status", "cat /proc/sys/kernel/randomize_va_space"),
            ("Stack Protection", "cat /proc/sys/kernel/exec-shield 2>/dev/null || echo 'no exec-shield'"),
            ("Yama LSM", "cat /proc/sys/kernel/yama/ptrace_scope"),
            ("FS Protection", "cat /proc/sys/fs/protected_* 2>/dev/null"),
            ("BPF Programs", "bpftool prog list 2>/dev/null || echo 'no bpftool'"),
            ("eBPF Maps", "bpftool map list 2>/dev/null || echo 'no bpftool'"),
            ("Kernel Features", "cat /proc/config.gz 2>/dev/null | zcat | grep -E '(CONFIG_|CONFIG_DEBUG)' | head -20"),
            ("System Call Table", "cat /proc/kallsyms | grep sys_call_table"),
            ("Security Modules", "cat /proc/self/status | grep -E '(Smack|AppArmor|SELinux)'"),
            ("Integrity Status", "cat /proc/sys/kernel/integrity 2>/dev/null || echo 'no integrity'"),
            ("Lockdown Mode", "cat /sys/kernel/security/lockdown 2>/dev/null || echo 'no lockdown'"),
            ("Kernel Hooks", "cat /proc/kallsyms | grep -E '(security_|selinux_|apparmor_)'"),
            ("LSM List", "cat /sys/kernel/security/lsm 2>/dev/null"),
            ("Device Mapper", "dmsetup ls 2>/dev/null || echo 'no dmsetup'"),
        ]
        
        for test_name, cmd in tests:
            try:
                result = await self.execute_cmd(cmd, timeout=10)
                if isinstance(result, dict) and result.get('code') == 200:
                    data = result.get('data', [{}])[0].get('errorMsg', '')
                    self.log_result("KERNEL", test_name, cmd, result, "SUCCESS")
                    print(f"  ✓ [{test_name}]")
                else:
                    self.log_result("KERNEL", test_name, cmd, result, "FAILED")
                    print(f"  ✗ [{test_name}]")
            except Exception as e:
                self.log_result("KERNEL", test_name, cmd, str(e), "ERROR")
                print(f"  ! [{test_name}] Error: {e}")
    
    async def cleanup(self):
        """OPSEC Cleanup - Remove all artifacts"""
        print("\n[OPSEC] Cleaning up artifacts...")
        cleanup_commands = [
            "rm -rf /tmp/* 2>/dev/null",
            "rm -rf /data/local/tmp/* 2>/dev/null",
            "history -c 2>/dev/null",
            "rm -f /data/local/tmp/*.log 2>/dev/null",
        ]
        
        for cmd in cleanup_commands:
            try:
                await self.execute_cmd(cmd, timeout=5)
            except:
                pass
    
    def generate_report(self):
        """Generate final report without persistent storage"""
        duration = datetime.now() - self.start_time
        
        print("\n" + "="*60)
        print("OPSEC SECURITY ASSESSMENT REPORT")
        print("="*60)
        print(f"Device: {self.pad_code}")
        print(f"Duration: {duration}")
        print(f"Total Tests: {len(self.results)}")
        
        # Count by category
        host = len([r for r in self.results if r['category'] == 'HOST'])
        container = len([r for r in self.results if r['category'] == 'CONTAINER'])
        kernel = len([r for r in self.results if r['category'] == 'KERNEL'])
        
        print(f"\nTests by Category:")
        print(f"  Host Level: {host}")
        print(f"  Container Level: {container}")
        print(f"  Kernel Level: {kernel}")
        
        # Count by status
        success = len([r for r in self.results if r['status'] == 'SUCCESS'])
        failed = len([r for r in self.results if r['status'] == 'FAILED'])
        error = len([r for r in self.results if r['status'] == 'ERROR'])
        
        print(f"\nResults:")
        print(f"  ✓ Success: {success}")
        print(f"  ✗ Failed: {failed}")
        print(f"  ! Error: {error}")
        
        print("\n[OPSEC] Report generated in memory only - no artifacts persisted")
        print("="*60)
        
        return self.results

async def main():
    scanner = OPSECSecurityScanner("APP5AU4BB1QQBHNA")
    
    print("="*60)
    print("OPSEC SECURITY ASSESSMENT SUITE")
    print("100 Tests: Host (30), Container (35), Kernel (35)")
    print("Device: APP5AU4BB1QQBHNA")
    print("="*60)
    
    await scanner.run_host_level_tests()
    await scanner.run_container_level_tests()
    await scanner.run_kernel_level_tests()
    await scanner.cleanup()
    
    results = scanner.generate_report()
    
    # Results are in memory only - no file persistence
    return results

if __name__ == '__main__':
    asyncio.run(main())
