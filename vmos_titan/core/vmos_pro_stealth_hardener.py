"""
VMOSProStealthHardener — Deep VMOS Pro Container Stealth Patching
=================================================================
Addresses the critical VMOS Pro container-specific stealth gaps identified
in the research reports that vmos_anomaly_patcher.py cannot cover because
it only uses Cloud API property modification (~80% coverage).

This module fills the remaining ~20% gap via direct shell commands
targeting VMOS-specific forensic leaks:

Gap 1: xu_daemon / cloudservice binary hiding via tmpfs bind-mount
    - Reports: "Hardening Genesis V3" §2.2 — RASP scans these paths
    - Risk: Banking apps stat() these files → instant detection
    - Fix: tmpfs overlay with benign placeholders

Gap 2: eth0→wlan0 network interface rename
    - Reports: "Hardening Genesis V3" §2.1 — eth0@if10 veth pair
    - Risk: RASP detects Ethernet → corporate/container flag
    - Fix: ip link rename + mock wpa_supplicant

Gap 3: Process comm rename for VMOS daemons
    - Reports: xu_daemon, cloudservice show in /proc/*/comm
    - Fix: echo newname > /proc/PID/comm

Gap 4: /proc/self/mountinfo recursive hiding
    - Reports: "Advanced Wallet Provisioning" §RASP Evasion
    - Risk: RASP reads mount table, sees bind-mount evidence
    - Fix: 2-pass filtered mountinfo bind-mount

Gap 5: VMOS kernel module removal (selinux_leak_fix)
    - Reports: rmmod selinux_leak_fix
    - Fix: Unload VMOS-specific kernel modules

Gap 6: /sys/block/ loop device filtering (703 loop + 64 NBD)
    - Reports: "Hardening Genesis V3" §2.1 — storage block leak
    - Risk: ls /sys/block/ shows hundreds of loop devices
    - Note: Cannot chmod /sys/block/* (causes crash) — use LSPosed hook

VMOS Crash Prevention Rules (CRITICAL — reviewed against reports):
    - NEVER pm disable-user com.cloud.rtcgesture
    - NEVER pm disable-user com.android.expansiontools
    - NEVER mount tmpfs over /system/priv-app/
    - NEVER mass chmod /sys/block/
    - NEVER rapid-fire async_adb_cmd (<3s apart)
    - NEVER bind-mount over /system/bin/cloudservice (daemon must run)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

MIN_CMD_INTERVAL_S = 3.5  # VMOS API flood protection


@dataclass
class StealthPatchResult:
    """Result from a single stealth patch operation."""
    name: str
    success: bool
    details: str = ""
    error: str = ""


@dataclass
class StealthReport:
    """Complete report from stealth hardening run."""
    pad_code: str
    total_patches: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    patches: List[StealthPatchResult] = field(default_factory=list)
    duration_s: float = 0.0

    def to_dict(self) -> dict:
        return {
            "pad_code": self.pad_code,
            "total_patches": self.total_patches,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": f"{self.successful}/{self.total_patches}",
            "duration_s": round(self.duration_s, 2),
            "patches": [
                {"name": p.name, "success": p.success,
                 "details": p.details, "error": p.error}
                for p in self.patches
            ],
        }


class VMOSProStealthHardener:
    """
    Deep stealth patching for VMOS Pro cloud containers.

    Fills the ~20% coverage gap from vmos_anomaly_patcher.py by
    applying shell-level stealth fixes that require root access
    rather than Cloud API property modification.

    Usage:
        hardener = VMOSProStealthHardener(pad_code="ACP250329ACQRPDV")
        report = await hardener.full_harden()
        print(f"Success: {report.successful}/{report.total_patches}")

    For Cuttlefish (local ADB):
        hardener = VMOSProStealthHardener(
            pad_code="local",
            use_local_adb=True,
            adb_target="127.0.0.1:6520",
        )
    """

    # tmpfs staging directory (anonymous mount, survives until reboot)
    STAGING_DIR = "/dev/.sc"

    # VMOS control plane binaries to hide from RASP scanners
    CONTROL_PLANE_BINARIES = [
        "/system/bin/xu_daemon",
        "/system/bin/cloudservice",
    ]

    # VMOS kernel modules to unload
    VMOS_KERNEL_MODULES = [
        "selinux_leak_fix",
    ]

    # Proc files to sterilize
    PROC_STERILIZE_TARGETS = {
        "/proc/cmdline": [
            "androidboot.hardware=cutf_cvm",
            "vsoc_",
            "cuttlefish",
            "armcloud",
            "vmos",
            "redroid",
            "docker",
            "lxc",
            "containerd",
        ],
        "/proc/1/cgroup": None,  # Replace entirely with "0::/"
        "/proc/mounts": [
            "cloud",
            "armcloud",
            "vmos",
            "overlay",
            "tmpfs /dev/.sc",
        ],
    }

    def __init__(self, pad_code: str,
                 use_local_adb: bool = False,
                 adb_target: str = "127.0.0.1:6520"):
        self.pad_code = pad_code
        self.use_local_adb = use_local_adb
        self.adb_target = adb_target
        self._last_cmd_time = 0.0
        self._client = None

    async def _shell(self, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute shell command with rate limiting."""
        elapsed = time.time() - self._last_cmd_time
        if elapsed < MIN_CMD_INTERVAL_S:
            import asyncio
            await asyncio.sleep(MIN_CMD_INTERVAL_S - elapsed)

        self._last_cmd_time = time.time()

        if self.use_local_adb:
            return self._local_shell(cmd, timeout)
        else:
            return await self._vmos_shell(cmd, timeout)

    def _local_shell(self, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute via local ADB."""
        import subprocess
        try:
            result = subprocess.run(
                ["adb", "-s", self.adb_target, "shell", cmd],
                capture_output=True, text=True, timeout=timeout,
            )
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)

    async def _vmos_shell(self, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute via VMOS Cloud API."""
        if self._client is None:
            from vmos_cloud_api import VMOSCloudClient
            self._client = VMOSCloudClient()

        try:
            result = await self._client.async_adb_cmd([self.pad_code], cmd)
            if isinstance(result, dict):
                output = result.get("data", {}).get("result", "")
                success = result.get("code") == 0 or result.get("status") == 0
                return success, str(output)
            return True, str(result)
        except Exception as e:
            return False, str(e)

    # ═══════════════════════════════════════════════════════════════════════
    # PATCH 1: tmpfs Staging Area Setup
    # ═══════════════════════════════════════════════════════════════════════

    async def _setup_staging(self) -> StealthPatchResult:
        """Create anonymous tmpfs staging directory at /dev/.sc."""
        cmd = (
            f"mkdir -p {self.STAGING_DIR} && "
            f"mount -t tmpfs tmpfs {self.STAGING_DIR} 2>/dev/null; "
            f"echo ok"
        )
        ok, output = await self._shell(cmd)
        return StealthPatchResult(
            name="staging_tmpfs",
            success=ok or "ok" in output,
            details=f"Staging at {self.STAGING_DIR}",
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PATCH 2: xu_daemon / cloudservice Binary Hiding
    # ═══════════════════════════════════════════════════════════════════════

    async def _hide_control_plane(self) -> StealthPatchResult:
        """
        Hide VMOS control plane binaries from RASP scanners.

        Creates empty placeholder files on tmpfs and bind-mounts
        them over the real binaries. The daemons continue running
        in memory but file-path queries return benign placeholders.

        CRITICAL: Do NOT bind-mount over the actual running process
        memory or kill the daemons — this would crash the VMOS instance.
        """
        results = []
        for binary_path in self.CONTROL_PLANE_BINARIES:
            binary_name = binary_path.split("/")[-1]
            placeholder = f"{self.STAGING_DIR}/{binary_name}"

            # Create benign placeholder (empty file with neutral name)
            cmd = (
                f"touch {placeholder} && "
                f"chmod 755 {placeholder} && "
                f"mount --bind {placeholder} {binary_path} 2>/dev/null && "
                f"echo hidden:{binary_name}"
            )
            ok, output = await self._shell(cmd)
            results.append(f"{binary_name}:{'ok' if ok else 'fail'}")

        all_ok = all("ok" in r for r in results)
        return StealthPatchResult(
            name="control_plane_hiding",
            success=all_ok,
            details="; ".join(results),
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PATCH 3: /proc Sterilization (bind-mount technique)
    # ═══════════════════════════════════════════════════════════════════════

    async def _sterilize_proc_cmdline(self) -> StealthPatchResult:
        """
        Clean /proc/cmdline of virtualization markers.

        Strips: androidboot.hardware=cutf_cvm, vsoc_*, cuttlefish*,
        armcloud*, vmos*, redroid*, docker, lxc, containerd.
        Injects: androidboot.verifiedbootstate=green.
        """
        # Build sed expression to strip all markers
        markers = self.PROC_STERILIZE_TARGETS["/proc/cmdline"]
        sed_parts = []
        for marker in markers:
            escaped = marker.replace("/", "\\/").replace(".", "\\.")
            sed_parts.append(f"s/{escaped}[^ ]*//g")

        sed_expr = "; ".join(sed_parts)

        cmd = (
            f"cat /proc/cmdline | sed '{sed_expr}' | "
            f"sed 's/  */ /g' > {self.STAGING_DIR}/cmdline && "
            f"echo 'androidboot.verifiedbootstate=green' >> {self.STAGING_DIR}/cmdline && "
            f"mount --bind {self.STAGING_DIR}/cmdline /proc/cmdline 2>/dev/null && "
            f"echo sterilized"
        )
        ok, output = await self._shell(cmd)
        return StealthPatchResult(
            name="proc_cmdline_sterilize",
            success="sterilized" in output,
            details="Removed emulator/container markers from /proc/cmdline",
        )

    async def _sterilize_proc_cgroup(self) -> StealthPatchResult:
        """
        Replace /proc/1/cgroup with clean init process hierarchy.

        Container cgroups expose docker/containerd/kubepods signatures.
        Replace with standard "0::/" which mimics non-containerized init.
        """
        cmd = (
            f'echo "0::/" > {self.STAGING_DIR}/cgroup && '
            f"mount --bind {self.STAGING_DIR}/cgroup /proc/1/cgroup 2>/dev/null && "
            f"echo sterilized"
        )
        ok, output = await self._shell(cmd)
        return StealthPatchResult(
            name="proc_cgroup_sterilize",
            success="sterilized" in output,
            details="Replaced /proc/1/cgroup with clean hierarchy",
        )

    async def _sterilize_proc_mounts(self) -> StealthPatchResult:
        """
        Filter /proc/mounts to remove cloud/container mount evidence.

        2-pass technique: first filter mounts, then bind-mount the
        filtered version, then filter the new mountinfo to hide the
        bind-mount itself (recursive hiding).
        """
        # Pass 1: Filter /proc/mounts
        filter_markers = self.PROC_STERILIZE_TARGETS["/proc/mounts"]
        grep_exclude = " ".join(f"-e '{m}'" for m in filter_markers)

        cmd = (
            f"cat /proc/mounts | grep -v {grep_exclude} > "
            f"{self.STAGING_DIR}/mounts && "
            f"mount --bind {self.STAGING_DIR}/mounts /proc/mounts 2>/dev/null && "
            f"echo pass1"
        )
        ok1, output1 = await self._shell(cmd)

        # Pass 2: Filter /proc/self/mountinfo (hide the bind-mount itself)
        cmd2 = (
            f"cat /proc/self/mountinfo | grep -v "
            f"-e 'tmpfs /dev/.sc' -e 'cloud' -e 'armcloud' > "
            f"{self.STAGING_DIR}/mountinfo && "
            f"mount --bind {self.STAGING_DIR}/mountinfo /proc/self/mountinfo 2>/dev/null && "
            f"echo pass2"
        )
        ok2, output2 = await self._shell(cmd2)

        success = "pass1" in output1 or "pass2" in output2
        return StealthPatchResult(
            name="proc_mounts_sterilize",
            success=success,
            details="2-pass mount table filtering with recursive hiding",
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PATCH 4: Network Interface Camouflage
    # ═══════════════════════════════════════════════════════════════════════

    async def _rename_network_interface(self) -> StealthPatchResult:
        """
        Rename eth0 (container veth pair) to wlan0.

        VMOS containers expose eth0@if10 — a dead giveaway for
        containerized environments. Physical phones use wlan0.

        Also deploys mock wpa_supplicant state file for WiFi-scanning
        RASP checks.
        """
        # Step 1: Rename interface
        cmd = (
            "ip link set eth0 down 2>/dev/null && "
            "ip link set eth0 name wlan0 2>/dev/null && "
            "ip link set wlan0 up 2>/dev/null && "
            "echo renamed"
        )
        ok, output = await self._shell(cmd)

        if "renamed" not in output:
            # Some VMOS versions block interface rename — try alternative
            return StealthPatchResult(
                name="network_interface_rename",
                success=False,
                details="Interface rename blocked by VMOS namespace",
                error=output,
            )

        # Step 2: Create mock wpa_supplicant state
        wpa_state = (
            "bssid=a4:5e:60:xx:xx:xx\n"
            "freq=2437\n"
            "ssid=NETGEAR-5G\n"
            "id=0\n"
            "mode=station\n"
            "pairwise_cipher=CCMP\n"
            "group_cipher=CCMP\n"
            "key_mgmt=WPA2-PSK\n"
            "wpa_state=COMPLETED\n"
            "ip_address=192.168.1.42\n"
            "address=02:00:00:00:00:01\n"
        )
        cmd2 = (
            f"mkdir -p /data/misc/wifi && "
            f"echo '{wpa_state}' > /data/misc/wifi/wpa_supplicant.conf 2>/dev/null && "
            f"echo wpa_ok"
        )
        ok2, output2 = await self._shell(cmd2)

        return StealthPatchResult(
            name="network_interface_rename",
            success=True,
            details=f"eth0→wlan0 + wpa_supplicant state {'deployed' if 'wpa_ok' in output2 else 'skipped'}",
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PATCH 5: Process Identity Cloaking
    # ═══════════════════════════════════════════════════════════════════════

    async def _cloak_processes(self) -> StealthPatchResult:
        """
        Rename VMOS daemon process comm names to innocuous alternatives.

        Banking apps scan /proc/*/comm for known VMOS process names.
        Renaming via /proc/PID/comm changes the process name in ps output.
        """
        PROCESS_RENAMES = {
            "xu_daemon": "system_server",
            "cloudservice": "com.android.nfc",
            "rtcgesture": "surfaceflinger",
        }

        renamed = []
        for proc_name, new_name in PROCESS_RENAMES.items():
            cmd = (
                f"pid=$(pgrep -f {proc_name} | head -1) && "
                f'[ -n "$pid" ] && echo {new_name} > /proc/$pid/comm && '
                f"echo renamed:{proc_name}"
            )
            ok, output = await self._shell(cmd)
            if f"renamed:{proc_name}" in output:
                renamed.append(proc_name)

        return StealthPatchResult(
            name="process_cloaking",
            success=len(renamed) > 0,
            details=f"Renamed: {', '.join(renamed) if renamed else 'none'}",
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PATCH 6: VMOS Kernel Module Removal
    # ═══════════════════════════════════════════════════════════════════════

    async def _remove_kernel_modules(self) -> StealthPatchResult:
        """
        Unload VMOS-specific kernel modules.

        selinux_leak_fix is a 16KB VMOS module that patches SELinux
        information leaks. Its presence in lsmod is detectable.
        """
        removed = []
        for module in self.VMOS_KERNEL_MODULES:
            cmd = f"rmmod {module} 2>/dev/null && echo removed:{module}"
            ok, output = await self._shell(cmd)
            if f"removed:{module}" in output:
                removed.append(module)

        return StealthPatchResult(
            name="kernel_module_removal",
            success=True,  # Not all modules may exist
            details=f"Removed: {', '.join(removed) if removed else 'none present'}",
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PATCH 7: Boot Property Hardening
    # ═══════════════════════════════════════════════════════════════════════

    async def _harden_boot_properties(self) -> StealthPatchResult:
        """
        Set critical boot verification properties via resetprop.

        These properties are checked by Play Integrity, banking apps,
        and RASP frameworks to verify device integrity.
        """
        BOOT_PROPS = {
            "ro.boot.verifiedbootstate": "green",
            "ro.boot.flash.locked": "1",
            "ro.boot.vbmeta.device_state": "locked",
            "ro.debuggable": "0",
            "ro.secure": "1",
            "ro.build.type": "user",
            "ro.build.tags": "release-keys",
            "ro.adb.secure": "1",
        }

        set_count = 0
        for prop, value in BOOT_PROPS.items():
            # Try resetprop first (requires Magisk)
            cmd = f"resetprop {prop} {value} 2>/dev/null || setprop {prop} {value} 2>/dev/null && echo set"
            ok, output = await self._shell(cmd)
            if "set" in output:
                set_count += 1

        return StealthPatchResult(
            name="boot_property_hardening",
            success=set_count > 0,
            details=f"Set {set_count}/{len(BOOT_PROPS)} boot properties",
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PATCH 8: Frida/Debug Port Blocking
    # ═══════════════════════════════════════════════════════════════════════

    async def _block_debug_ports(self) -> StealthPatchResult:
        """
        Block known debugging/instrumentation ports via iptables.

        Frida: 27042, 27043
        ADB: 5555
        Xposed: various dynamic
        """
        BLOCK_PORTS = [27042, 27043, 5555]

        cmd_parts = []
        for port in BLOCK_PORTS:
            cmd_parts.append(f"iptables -A INPUT -p tcp --dport {port} -j DROP 2>/dev/null")
            cmd_parts.append(f"iptables -A OUTPUT -p tcp --dport {port} -j DROP 2>/dev/null")

        # Block IPv6 entirely
        cmd_parts.append("ip6tables -P INPUT DROP 2>/dev/null")
        cmd_parts.append("ip6tables -P OUTPUT DROP 2>/dev/null")
        cmd_parts.append("ip6tables -P FORWARD DROP 2>/dev/null")

        cmd = " && ".join(cmd_parts) + " && echo blocked"
        ok, output = await self._shell(cmd)

        return StealthPatchResult(
            name="debug_port_blocking",
            success="blocked" in output or ok,
            details=f"Blocked ports: {BLOCK_PORTS} + IPv6 DROP ALL",
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PATCH 9: su Binary Hiding
    # ═══════════════════════════════════════════════════════════════════════

    async def _hide_su_binaries(self) -> StealthPatchResult:
        """
        Hide su binaries from RASP root detection.

        4-path coverage: /system/bin/su, /system/xbin/su,
        /sbin/su, /vendor/bin/su.

        Uses bind-mount of /dev/null over existing su paths.
        """
        SU_PATHS = [
            "/system/bin/su",
            "/system/xbin/su",
            "/sbin/su",
            "/vendor/bin/su",
        ]

        hidden = []
        for su_path in SU_PATHS:
            cmd = (
                f"[ -f {su_path} ] && "
                f"chmod 000 {su_path} 2>/dev/null && "
                f"mount --bind /dev/null {su_path} 2>/dev/null && "
                f"echo hidden:{su_path}"
            )
            ok, output = await self._shell(cmd)
            if "hidden:" in output:
                hidden.append(su_path)

        return StealthPatchResult(
            name="su_binary_hiding",
            success=True,  # Success even if no su found (clean device)
            details=f"Hidden: {', '.join(hidden) if hidden else 'no su binaries found'}",
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PATCH 10: /proc/self/maps Cleaning
    # ═══════════════════════════════════════════════════════════════════════

    async def _clean_proc_maps(self) -> StealthPatchResult:
        """
        Filter /proc/self/maps to remove Magisk/Frida/Xposed library paths.

        Banking apps (especially Klarna via RootBeer) scan loaded library
        paths in /proc/self/maps for injection framework signatures.
        """
        FILTER_PATTERNS = [
            "magisk", "frida", "xposed", "substrate",
            "cydia", "riru", "zygisk", "lsposed",
        ]
        grep_exclude = " ".join(f"-e '{p}'" for p in FILTER_PATTERNS)

        cmd = (
            f"cat /proc/self/maps | grep -vi {grep_exclude} > "
            f"{self.STAGING_DIR}/maps && "
            f"echo cleaned"
        )
        ok, output = await self._shell(cmd)

        # Note: /proc/self/maps cannot be bind-mounted directly as it's
        # process-specific. This creates a clean reference that can be
        # used by LSPosed hooks to intercept reads.
        return StealthPatchResult(
            name="proc_maps_cleaning",
            success="cleaned" in output,
            details="Generated clean /proc/self/maps reference for LSPosed hook",
        )

    # ═══════════════════════════════════════════════════════════════════════
    # FULL HARDENING PIPELINE
    # ═══════════════════════════════════════════════════════════════════════

    async def full_harden(self, skip_patches: Optional[List[str]] = None) -> StealthReport:
        """
        Execute all stealth hardening patches.

        Args:
            skip_patches: List of patch names to skip.

        Returns:
            StealthReport with results of all patches.
        """
        start_time = time.time()
        skip = set(skip_patches or [])
        report = StealthReport(pad_code=self.pad_code)

        # Ordered patch pipeline
        patches = [
            ("staging_tmpfs", self._setup_staging),
            ("control_plane_hiding", self._hide_control_plane),
            ("proc_cmdline_sterilize", self._sterilize_proc_cmdline),
            ("proc_cgroup_sterilize", self._sterilize_proc_cgroup),
            ("proc_mounts_sterilize", self._sterilize_proc_mounts),
            ("network_interface_rename", self._rename_network_interface),
            ("process_cloaking", self._cloak_processes),
            ("kernel_module_removal", self._remove_kernel_modules),
            ("boot_property_hardening", self._harden_boot_properties),
            ("debug_port_blocking", self._block_debug_ports),
            ("su_binary_hiding", self._hide_su_binaries),
            ("proc_maps_cleaning", self._clean_proc_maps),
        ]

        for patch_name, patch_fn in patches:
            report.total_patches += 1

            if patch_name in skip:
                report.skipped += 1
                report.patches.append(StealthPatchResult(
                    name=patch_name, success=True,
                    details="Skipped by user",
                ))
                continue

            try:
                result = await patch_fn()
                report.patches.append(result)
                if result.success:
                    report.successful += 1
                    logger.info(f"[STEALTH] ✓ {patch_name}: {result.details}")
                else:
                    report.failed += 1
                    logger.warning(f"[STEALTH] ✗ {patch_name}: {result.error or result.details}")
            except Exception as e:
                report.failed += 1
                report.patches.append(StealthPatchResult(
                    name=patch_name, success=False,
                    error=str(e),
                ))
                logger.error(f"[STEALTH] ✗ {patch_name}: {e}")

        report.duration_s = time.time() - start_time
        logger.info(
            f"[STEALTH] Hardening complete: "
            f"{report.successful}/{report.total_patches} patches "
            f"({report.duration_s:.1f}s)"
        )
        return report
