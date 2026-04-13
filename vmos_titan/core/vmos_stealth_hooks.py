"""
VMOSStealthHooks — Pre-built apmt Xposed Hook Templates for VMOS Pro
=====================================================================
Provides ready-to-deploy Xposed hook templates addressing the hardware
identity leaks that CANNOT be fixed via property modification alone.

Gap #5 from research report cross-reference:
- xposed_manager.py has generic hook infrastructure but NO pre-built
  templates for VMOS-specific hardware identity leaks
- vmos_anomaly_patcher.py sets ro.* properties for GPU (build.prop level)
  but GL_RENDERER is returned by hardware Mali-G715 driver at runtime
- NetworkInterface.getNetworkInterfaces() exposes eth0@if10 veth pair
- TelephonyManager returns container-default SIM state
- /sys/block/ enumeration shows 703 loop + 64 NBD devices

Pre-built hook templates:

Hook 1: GPU Identity (CRITICAL — Mali-G715 → Adreno 830)
    - Target: android.opengl.GLES20.glGetString()
    - Also: javax.microedition.khronos.opengles.GL10.glGetString()
    - Why: Banking apps + Play Integrity call glGetString(GL_RENDERER)
           which returns real GPU from hardware driver, NOT from build.prop
    - Fix: Zygisk-level hook is ideal but apmt can hook Java GL wrapper

Hook 2: Network Interface Filtering (eth0@if10 → hidden)
    - Target: java.net.NetworkInterface.getNetworkInterfaces()
    - Why: RASP scans for eth0 (container indicator) — phones use wlan0
    - Fix: Filter enumeration result to remove eth0, keep wlan0

Hook 3: SIM State Spoofing
    - Target: android.telephony.TelephonyManager methods
    - Why: SIM_STATE_ABSENT on containers → instant detection
    - Fix: Return SIM_STATE_READY + carrier info

Hook 4: Block Device Filtering (/sys/block/ loop devices)
    - Target: java.io.File.listFiles() when path = /sys/block/
    - Why: 703 loop + 64 NBD devices vs 3-5 on physical phone
    - Fix: Filter to return only sda/sdb/mmcblk0

Hook 5: Process Maps Filtering (/proc/self/maps)
    - Target: java.io.FileInputStream constructor for /proc/self/maps
    - Why: Klarna RootBeer scans loaded library paths for magisk/frida
    - Fix: Redirect reads to clean reference file

VMOS apmt entry class: androidx.app.Entry (NOT IXposedHookLoadPackage)
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class HookDeployResult:
    """Result of deploying a hook template."""
    name: str
    success: bool
    target_package: str
    scope: str  # "app" or "system"
    details: str = ""
    error: str = ""


# ═══════════════════════════════════════════════════════════════════════
# Pre-built Java hook source code
# ═══════════════════════════════════════════════════════════════════════

# Hook 1: GPU GL_RENDERER interception
GPU_HOOK_SOURCE = '''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class Entry {

    // Spoofed GPU values — must match build.prop ro.hardware.chipname
    private static final String SPOOF_RENDERER = "Adreno (TM) 830";
    private static final String SPOOF_VENDOR = "Qualcomm";
    private static final String SPOOF_VERSION = "OpenGL ES 3.2 V@0752.0 (GIT@1514975b31, Iea98bc0bde, 1719251092) (Date:06/24/24)";

    // GL constants
    private static final int GL_VENDOR = 0x1F00;
    private static final int GL_RENDERER = 0x1F01;
    private static final int GL_VERSION = 0x1F02;

    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {
        // Hook GLES20.glGetString (modern API)
        try {
            XposedHelpers.findAndHookMethod(
                "android.opengl.GLES20",
                lpparam.classLoader,
                "glGetString",
                int.class,
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        int name = (int) param.args[0];
                        if (name == GL_RENDERER) {
                            param.setResult(SPOOF_RENDERER);
                        } else if (name == GL_VENDOR) {
                            param.setResult(SPOOF_VENDOR);
                        } else if (name == GL_VERSION) {
                            param.setResult(SPOOF_VERSION);
                        }
                    }
                }
            );
        } catch (Throwable t) {
            // GLES20 may not be loaded in all apps
        }

        // Hook GLES30.glGetString (ES 3.0+)
        try {
            XposedHelpers.findAndHookMethod(
                "android.opengl.GLES30",
                lpparam.classLoader,
                "glGetString",
                int.class,
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        int name = (int) param.args[0];
                        if (name == GL_RENDERER) {
                            param.setResult(SPOOF_RENDERER);
                        } else if (name == GL_VENDOR) {
                            param.setResult(SPOOF_VENDOR);
                        } else if (name == GL_VERSION) {
                            param.setResult(SPOOF_VERSION);
                        }
                    }
                }
            );
        } catch (Throwable t) {}

        // Hook legacy GL10.glGetString (KitKat compatibility)
        try {
            XposedHelpers.findAndHookMethod(
                "javax.microedition.khronos.opengles.GL10",
                lpparam.classLoader,
                "glGetString",
                int.class,
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        int name = (int) param.args[0];
                        if (name == GL_RENDERER) {
                            param.setResult(SPOOF_RENDERER);
                        } else if (name == GL_VENDOR) {
                            param.setResult(SPOOF_VENDOR);
                        }
                    }
                }
            );
        } catch (Throwable t) {}
    }

    public static void systemMain() {
        // GPU hooks are app-level only
    }
}
'''

# Hook 2: Network interface filtering
NETWORK_HOOK_SOURCE = '''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;
import java.net.NetworkInterface;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.List;

public class Entry {

    // Container interfaces to hide
    private static final String[] HIDDEN_INTERFACES = {
        "eth0", "eth1", "docker0", "br-", "veth", "cni0",
        "flannel", "calico", "tunl0"
    };

    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {
        // Hook NetworkInterface.getNetworkInterfaces()
        try {
            XposedHelpers.findAndHookMethod(
                "java.net.NetworkInterface",
                lpparam.classLoader,
                "getNetworkInterfaces",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        Enumeration<NetworkInterface> original =
                            (Enumeration<NetworkInterface>) param.getResult();
                        if (original == null) return;

                        List<NetworkInterface> filtered = new ArrayList<>();
                        while (original.hasMoreElements()) {
                            NetworkInterface ni = original.nextElement();
                            String name = ni.getName();
                            boolean hide = false;
                            for (String prefix : HIDDEN_INTERFACES) {
                                if (name.startsWith(prefix)) {
                                    hide = true;
                                    break;
                                }
                            }
                            if (!hide) {
                                filtered.add(ni);
                            }
                        }
                        param.setResult(Collections.enumeration(filtered));
                    }
                }
            );
        } catch (Throwable t) {}
    }

    public static void systemMain() {}
}
'''

# Hook 3: SIM state spoofing
SIM_HOOK_SOURCE = '''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class Entry {

    // SIM_STATE_READY = 5
    private static final int SIM_STATE_READY = 5;

    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {
        String telephonyClass = "android.telephony.TelephonyManager";

        // Hook getSimState()
        try {
            XposedHelpers.findAndHookMethod(
                telephonyClass, lpparam.classLoader,
                "getSimState",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult(SIM_STATE_READY);
                    }
                }
            );
        } catch (Throwable t) {}

        // Hook getSimState(int slotIndex)
        try {
            XposedHelpers.findAndHookMethod(
                telephonyClass, lpparam.classLoader,
                "getSimState",
                int.class,
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult(SIM_STATE_READY);
                    }
                }
            );
        } catch (Throwable t) {}

        // Hook getNetworkOperatorName()
        try {
            XposedHelpers.findAndHookMethod(
                telephonyClass, lpparam.classLoader,
                "getNetworkOperatorName",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult("T-Mobile");
                    }
                }
            );
        } catch (Throwable t) {}

        // Hook getNetworkOperator() — MCC+MNC
        try {
            XposedHelpers.findAndHookMethod(
                telephonyClass, lpparam.classLoader,
                "getNetworkOperator",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult("310260");  // T-Mobile US
                    }
                }
            );
        } catch (Throwable t) {}

        // Hook getSimOperatorName()
        try {
            XposedHelpers.findAndHookMethod(
                telephonyClass, lpparam.classLoader,
                "getSimOperatorName",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult("T-Mobile");
                    }
                }
            );
        } catch (Throwable t) {}

        // Hook getPhoneType()
        try {
            XposedHelpers.findAndHookMethod(
                telephonyClass, lpparam.classLoader,
                "getPhoneType",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult(1);  // PHONE_TYPE_GSM
                    }
                }
            );
        } catch (Throwable t) {}
    }

    public static void systemMain() {}
}
'''

# Hook 4: Block device filtering (/sys/block/)
BLOCK_DEVICE_HOOK_SOURCE = '''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;
import java.io.File;
import java.util.ArrayList;

public class Entry {

    // Only show devices that a physical phone would have
    private static final String[] ALLOWED_BLOCKS = {
        "sda", "sdb", "sdc", "sdd", "sde",
        "mmcblk0", "mmcblk1", "dm-0", "dm-1"
    };

    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {
        // Hook File.listFiles() to filter /sys/block/ contents
        try {
            XposedHelpers.findAndHookMethod(
                "java.io.File",
                lpparam.classLoader,
                "listFiles",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        File self = (File) param.thisObject;
                        if (!self.getAbsolutePath().equals("/sys/block")) return;

                        File[] original = (File[]) param.getResult();
                        if (original == null) return;

                        ArrayList<File> filtered = new ArrayList<>();
                        for (File f : original) {
                            String name = f.getName();
                            for (String allowed : ALLOWED_BLOCKS) {
                                if (name.equals(allowed)) {
                                    filtered.add(f);
                                    break;
                                }
                            }
                        }
                        param.setResult(filtered.toArray(new File[0]));
                    }
                }
            );
        } catch (Throwable t) {}

        // Also hook File.list() for the same path
        try {
            XposedHelpers.findAndHookMethod(
                "java.io.File",
                lpparam.classLoader,
                "list",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        File self = (File) param.thisObject;
                        if (!self.getAbsolutePath().equals("/sys/block")) return;

                        param.setResult(ALLOWED_BLOCKS);
                    }
                }
            );
        } catch (Throwable t) {}
    }

    public static void systemMain() {}
}
'''

# Hook 5: /proc/self/maps filtering
PROC_MAPS_HOOK_SOURCE = '''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

public class Entry {

    private static final String[] FILTER_PATTERNS = {
        "magisk", "frida", "xposed", "substrate", "cydia",
        "riru", "zygisk", "lsposed", "edxposed", "titan"
    };

    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {
        // Hook FileInputStream constructor for /proc/self/maps
        try {
            XposedHelpers.findAndHookConstructor(
                "java.io.FileInputStream",
                lpparam.classLoader,
                File.class,
                new XC_MethodHook() {
                    @Override
                    protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                        File file = (File) param.args[0];
                        String path = file.getAbsolutePath();

                        if (path.contains("/proc/self/maps") ||
                            path.contains("/proc/" + android.os.Process.myPid() + "/maps")) {

                            // Read original, filter, redirect to clean version
                            StringBuilder clean = new StringBuilder();
                            try (BufferedReader reader = new BufferedReader(
                                    new InputStreamReader(new FileInputStream(file)))) {
                                String line;
                                while ((line = reader.readLine()) != null) {
                                    boolean skip = false;
                                    String lower = line.toLowerCase();
                                    for (String pattern : FILTER_PATTERNS) {
                                        if (lower.contains(pattern)) {
                                            skip = true;
                                            break;
                                        }
                                    }
                                    if (!skip) {
                                        clean.append(line).append("\\n");
                                    }
                                }
                            }

                            // Write filtered content to temp file
                            File tempFile = File.createTempFile("maps", null);
                            tempFile.deleteOnExit();
                            java.io.FileOutputStream fos = new java.io.FileOutputStream(tempFile);
                            fos.write(clean.toString().getBytes(StandardCharsets.UTF_8));
                            fos.close();

                            // Redirect to clean file
                            param.args[0] = tempFile;
                        }
                    }
                }
            );
        } catch (Throwable t) {}
    }

    public static void systemMain() {}
}
'''

# Combined all-in-one hook for maximum coverage
COMBINED_STEALTH_HOOK_SOURCE = '''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;
import java.io.File;
import java.net.NetworkInterface;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.List;

/**
 * Combined VMOS stealth hook — covers GPU, network, SIM, block devices,
 * and root detection in a single apmt plugin for reduced overhead.
 */
public class Entry {

    // GPU spoof values
    private static final String GPU_RENDERER = "Adreno (TM) 830";
    private static final String GPU_VENDOR = "Qualcomm";
    private static final int GL_VENDOR = 0x1F00;
    private static final int GL_RENDERER = 0x1F01;

    // SIM
    private static final int SIM_STATE_READY = 5;

    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {
        hookGPU(lpparam);
        hookNetwork(lpparam);
        hookSIM(lpparam);
        hookBlockDevices(lpparam);
        hookRootDetection(lpparam);
    }

    private static void hookGPU(XC_LoadPackage.LoadPackageParam lpparam) {
        try {
            XposedHelpers.findAndHookMethod("android.opengl.GLES20",
                lpparam.classLoader, "glGetString", int.class,
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        int name = (int) param.args[0];
                        if (name == GL_RENDERER) param.setResult(GPU_RENDERER);
                        else if (name == GL_VENDOR) param.setResult(GPU_VENDOR);
                    }
                }
            );
        } catch (Throwable t) {}
    }

    private static void hookNetwork(XC_LoadPackage.LoadPackageParam lpparam) {
        try {
            XposedHelpers.findAndHookMethod("java.net.NetworkInterface",
                lpparam.classLoader, "getNetworkInterfaces",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        Enumeration<NetworkInterface> orig =
                            (Enumeration<NetworkInterface>) param.getResult();
                        if (orig == null) return;
                        List<NetworkInterface> filtered = new ArrayList<>();
                        while (orig.hasMoreElements()) {
                            NetworkInterface ni = orig.nextElement();
                            if (!ni.getName().startsWith("eth") &&
                                !ni.getName().startsWith("veth") &&
                                !ni.getName().startsWith("docker") &&
                                !ni.getName().startsWith("br-")) {
                                filtered.add(ni);
                            }
                        }
                        param.setResult(Collections.enumeration(filtered));
                    }
                }
            );
        } catch (Throwable t) {}
    }

    private static void hookSIM(XC_LoadPackage.LoadPackageParam lpparam) {
        try {
            XposedHelpers.findAndHookMethod("android.telephony.TelephonyManager",
                lpparam.classLoader, "getSimState",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult(SIM_STATE_READY);
                    }
                }
            );
        } catch (Throwable t) {}
        try {
            XposedHelpers.findAndHookMethod("android.telephony.TelephonyManager",
                lpparam.classLoader, "getNetworkOperatorName",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult("T-Mobile");
                    }
                }
            );
        } catch (Throwable t) {}
    }

    private static void hookBlockDevices(XC_LoadPackage.LoadPackageParam lpparam) {
        final String[] allowed = {"sda","sdb","sdc","mmcblk0","dm-0","dm-1"};
        try {
            XposedHelpers.findAndHookMethod("java.io.File",
                lpparam.classLoader, "list",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        File self = (File) param.thisObject;
                        if ("/sys/block".equals(self.getAbsolutePath())) {
                            param.setResult(allowed);
                        }
                    }
                }
            );
        } catch (Throwable t) {}
    }

    private static void hookRootDetection(XC_LoadPackage.LoadPackageParam lpparam) {
        try {
            XposedHelpers.findAndHookMethod("java.io.File",
                lpparam.classLoader, "exists",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        String path = ((File) param.thisObject).getAbsolutePath();
                        if (path.contains("/su") || path.contains("magisk") ||
                            path.contains("supersu") || path.contains("busybox") ||
                            path.contains("Superuser")) {
                            param.setResult(false);
                        }
                    }
                }
            );
        } catch (Throwable t) {}
    }

    public static void systemMain() {}
}
'''


# ═══════════════════════════════════════════════════════════════════════
# Hook Deployer Class
# ═══════════════════════════════════════════════════════════════════════

HOOK_REGISTRY: Dict[str, str] = {
    "gpu_spoof": GPU_HOOK_SOURCE,
    "network_filter": NETWORK_HOOK_SOURCE,
    "sim_spoof": SIM_HOOK_SOURCE,
    "block_device_filter": BLOCK_DEVICE_HOOK_SOURCE,
    "proc_maps_filter": PROC_MAPS_HOOK_SOURCE,
    "combined_stealth": COMBINED_STEALTH_HOOK_SOURCE,
}


class VMOSStealthHookDeployer:
    """
    Deploy pre-built Xposed stealth hooks to VMOS Pro instances.

    Works with the xposed_manager.py apmt CLI interface to install
    hooks that address hardware-level identity leaks on VMOS containers.

    Usage:
        deployer = VMOSStealthHookDeployer(adb_target="127.0.0.1:6520")

        # Deploy individual hooks
        result = deployer.deploy_hook("gpu_spoof", "com.google.android.gms")

        # Deploy combined stealth hook to all target apps
        results = deployer.deploy_all_stealth(target_packages=[
            "com.google.android.gms",
            "com.google.android.apps.walletnfcrel",
            "com.android.chrome",
        ])
    """

    def __init__(self, adb_target: str = "127.0.0.1:6520"):
        self.adb_target = adb_target
        self._xposed_mgr = None

    def _get_manager(self):
        """Lazy-load XposedManager."""
        if self._xposed_mgr is None:
            from xposed_manager import XposedManager
            self._xposed_mgr = XposedManager(adb_target=self.adb_target)
        return self._xposed_mgr

    def _sh(self, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                ["adb", "-s", self.adb_target, "shell", cmd],
                capture_output=True, text=True, timeout=timeout,
            )
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def check_apmt_available(self) -> bool:
        """Check if apmt CLI is available on the device."""
        mgr = self._get_manager()
        return mgr.is_apmt_available()

    def deploy_hook(self, hook_name: str,
                    target_package: str) -> HookDeployResult:
        """
        Deploy a single pre-built hook to a target package.

        Args:
            hook_name: One of: gpu_spoof, network_filter, sim_spoof,
                       block_device_filter, proc_maps_filter, combined_stealth
            target_package: Android package to hook (e.g., "com.google.android.gms")

        Returns:
            HookDeployResult with deployment status.
        """
        if hook_name not in HOOK_REGISTRY:
            return HookDeployResult(
                name=hook_name, success=False,
                target_package=target_package, scope="app",
                error=f"Unknown hook: {hook_name}. Available: {list(HOOK_REGISTRY.keys())}",
            )

        source_code = HOOK_REGISTRY[hook_name]

        # Write Java source to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".java", prefix=f"titan_{hook_name}_",
            delete=False,
        ) as f:
            f.write(source_code)
            local_path = f.name

        try:
            # Push to device
            remote_path = f"/data/local/tmp/titan_{hook_name}.java"
            subprocess.run(
                ["adb", "-s", self.adb_target, "push", local_path, remote_path],
                capture_output=True, timeout=30,
            )

            # Install via apmt
            plugin_name = f"titan-{hook_name}"
            ok, output = self._sh(
                f"apmt patch add -n {plugin_name} -p {target_package} -f {remote_path}"
            )

            if ok:
                logger.info(f"Hook deployed: {hook_name} → {target_package}")
                return HookDeployResult(
                    name=hook_name, success=True,
                    target_package=target_package, scope="app",
                    details=f"Installed as {plugin_name}",
                )
            else:
                return HookDeployResult(
                    name=hook_name, success=False,
                    target_package=target_package, scope="app",
                    error=output,
                )
        finally:
            os.unlink(local_path)

    def deploy_all_stealth(self, target_packages: Optional[List[str]] = None,
                            use_combined: bool = True) -> List[HookDeployResult]:
        """
        Deploy full stealth hook suite to target packages.

        Args:
            target_packages: List of packages to hook. Defaults to
                             GMS + Wallet + Chrome.
            use_combined: If True, deploy single combined hook per package
                          (recommended for VMOS performance).
                          If False, deploy individual hooks separately.

        Returns:
            List of HookDeployResult for each deployment.
        """
        if target_packages is None:
            target_packages = [
                "com.google.android.gms",
                "com.google.android.apps.walletnfcrel",
                "com.android.chrome",
            ]

        results = []

        if use_combined:
            # Single combined hook per package (less overhead)
            for pkg in target_packages:
                result = self.deploy_hook("combined_stealth", pkg)
                results.append(result)
        else:
            # Individual hooks for granular control
            hooks = ["gpu_spoof", "network_filter", "sim_spoof",
                     "block_device_filter", "proc_maps_filter"]
            for pkg in target_packages:
                for hook in hooks:
                    result = self.deploy_hook(hook, pkg)
                    results.append(result)

        return results

    def list_deployed_hooks(self) -> List[str]:
        """List all titan-prefixed hooks installed via apmt."""
        mgr = self._get_manager()
        plugins = mgr.list_plugins()
        return [p.name for p in plugins if p.name.startswith("titan-")]

    def remove_all_hooks(self) -> int:
        """Remove all titan stealth hooks. Returns count removed."""
        mgr = self._get_manager()
        hooks = self.list_deployed_hooks()
        removed = 0
        for name in hooks:
            if mgr.remove_plugin(name):
                removed += 1
        return removed

    def get_hook_source(self, hook_name: str) -> Optional[str]:
        """Get the Java source code for a hook template."""
        return HOOK_REGISTRY.get(hook_name)
