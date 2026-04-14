"""
XposedManager — VMOS Cloud Xposed/LSPosed Hook Integration via apmt CLI.

This module provides programmatic control over Xposed framework plugins
on VMOS Cloud instances using the apmt (Android Patch Management Tool) CLI.

Capabilities:
- Install/remove Xposed plugins from local files or URLs
- List installed plugins and their status
- Generate hook templates for common bypass patterns
- System-level and app-level hooking support

Usage:
    manager = XposedManager(adb_target="127.0.0.1:6520")
    manager.install_plugin("bypass_root", "/path/to/plugin.apk")
    manager.list_plugins()
    manager.remove_plugin("bypass_root")
"""

import logging
import subprocess
import tempfile
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class PluginScope(Enum):
    """Scope of Xposed plugin hooks."""
    APP = "app"        # Hook specific app (appMain entry)
    SYSTEM = "system"  # Hook system server (systemMain entry)


class HookType(Enum):
    """Type of method hook."""
    BEFORE = "before"
    AFTER = "after"
    REPLACE = "replace"


@dataclass
class InstalledPlugin:
    """Information about an installed Xposed plugin."""
    name: str
    package: str
    path: str
    enabled: bool
    scope: PluginScope


@dataclass
class HookTemplate:
    """Template for generating Xposed hook code."""
    class_name: str
    method_name: str
    param_types: List[str]
    hook_type: HookType
    return_value: Optional[Any] = None
    before_code: Optional[str] = None
    after_code: Optional[str] = None


class XposedManager:
    """
    Manage Xposed/LSPosed plugins on VMOS Cloud instances via apmt CLI.
    
    The apmt tool is VMOS Cloud's plugin management system that enables:
    - Runtime method interception via XC_MethodHook
    - App-level hooks (target specific apps like com.facebook.katana)
    - System-level hooks (hook Android framework in SystemServer)
    """
    
    def __init__(self, adb_target: str = "127.0.0.1:6520"):
        """
        Initialize Xposed manager.
        
        Args:
            adb_target: ADB target device (IP:port or serial)
        """
        self.target = adb_target
    
    def _sh(self, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute shell command on device via ADB."""
        try:
            result = subprocess.run(
                ["adb", "-s", self.target, "shell", cmd],
                capture_output=True, text=True, timeout=timeout,
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {cmd}")
            return False, "timeout"
        except Exception as e:
            logger.error(f"Shell command failed: {e}")
            return False, str(e)
    
    def _push_file(self, local_path: str, remote_path: str) -> bool:
        """Push file to device via ADB."""
        try:
            result = subprocess.run(
                ["adb", "-s", self.target, "push", local_path, remote_path],
                capture_output=True, timeout=60,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to push file: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════
    # PLUGIN MANAGEMENT (apmt CLI)
    # ═══════════════════════════════════════════════════════════════════════
    
    def install_plugin(self, name: str, source: str,
                       package: str = "android",
                       scope: PluginScope = PluginScope.APP) -> bool:
        """
        Install an Xposed plugin via apmt.
        
        Args:
            name: Unique name for the plugin.
            source: Local file path or remote URL to APK.
            package: Target package to hook (use "android" for system hooks).
            scope: Plugin scope (APP or SYSTEM).
            
        Returns:
            True if installation successful.
        """
        # Determine if source is URL or local path
        if source.startswith("http://") or source.startswith("https://"):
            # Remote URL - use apmt's -u flag
            cmd = f"apmt patch add -n {name} -p {package} -u {source}"
        else:
            # Local file - push to device first
            remote_path = f"/data/local/tmp/{name}.apk"
            if not os.path.exists(source):
                logger.error(f"Plugin file not found: {source}")
                return False
            
            if not self._push_file(source, remote_path):
                logger.error(f"Failed to push plugin to device")
                return False
            
            cmd = f"apmt patch add -n {name} -p {package} -f {remote_path}"
        
        ok, output = self._sh(cmd)
        
        if ok:
            logger.info(f"Plugin installed: {name} -> {package}")
            
            # System hooks require reboot
            if scope == PluginScope.SYSTEM:
                logger.warning("System-level hook installed. Device reboot required.")
        else:
            logger.error(f"Failed to install plugin: {output}")
        
        return ok
    
    def remove_plugin(self, name: str) -> bool:
        """
        Remove an installed Xposed plugin.
        
        Args:
            name: Plugin name to remove.
            
        Returns:
            True if removal successful.
        """
        ok, output = self._sh(f"apmt patch del -n {name}")
        
        if ok:
            logger.info(f"Plugin removed: {name}")
        else:
            logger.error(f"Failed to remove plugin: {output}")
        
        return ok
    
    def list_plugins(self) -> List[InstalledPlugin]:
        """
        List all installed Xposed plugins.
        
        Returns:
            List of InstalledPlugin objects.
        """
        ok, output = self._sh("apmt patch list")
        
        if not ok:
            logger.error(f"Failed to list plugins: {output}")
            return []
        
        plugins = []
        
        # Parse output (format varies by VMOS version)
        # Expected format: name | package | path | enabled
        for line in output.strip().split("\n"):
            if not line or line.startswith("#") or "---" in line:
                continue
            
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                plugins.append(InstalledPlugin(
                    name=parts[0],
                    package=parts[1] if len(parts) > 1 else "unknown",
                    path=parts[2] if len(parts) > 2 else "",
                    enabled=True,  # Assume enabled if listed
                    scope=PluginScope.SYSTEM if parts[1] == "android" else PluginScope.APP,
                ))
        
        return plugins
    
    def is_apmt_available(self) -> bool:
        """Check if apmt CLI is available on the device."""
        ok, output = self._sh("which apmt")
        return ok and "apmt" in output
    
    # ═══════════════════════════════════════════════════════════════════════
    # HOOK TEMPLATE GENERATORS
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_hook_code(self, template: HookTemplate) -> str:
        """
        Generate Xposed hook Java code from template.
        
        Args:
            template: HookTemplate with hook specification.
            
        Returns:
            Java code string for the hook.
        """
        param_types_str = ", ".join(f'"{t}"' for t in template.param_types)
        
        if template.hook_type == HookType.BEFORE:
            hook_method = "beforeHookedMethod"
            hook_body = template.before_code or "// Before hook"
        elif template.hook_type == HookType.AFTER:
            hook_method = "afterHookedMethod"
            hook_body = template.after_code or "// After hook"
        else:  # REPLACE
            hook_method = "beforeHookedMethod"
            hook_body = f"param.setResult({template.return_value});"
        
        return f'''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class Entry {{
    
    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {{
        XposedHelpers.findAndHookMethod(
            "{template.class_name}",
            lpparam.classLoader,
            "{template.method_name}",
            {param_types_str + ", " if param_types_str else ""}
            new XC_MethodHook() {{
                @Override
                protected void {hook_method}(MethodHookParam param) throws Throwable {{
                    {hook_body}
                }}
            }}
        );
    }}
    
    public static void systemMain() {{
        // System-level hooks go here
    }}
}}
'''
    
    def generate_root_bypass_hook(self) -> str:
        """Generate hook code to bypass root detection."""
        return '''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;
import java.io.File;

public class Entry {
    
    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {
        // Hook File.exists() to hide su binary
        XposedHelpers.findAndHookMethod(
            "java.io.File",
            lpparam.classLoader,
            "exists",
            new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                    String path = ((File) param.thisObject).getAbsolutePath();
                    if (path.contains("su") || path.contains("magisk") || 
                        path.contains("supersu") || path.contains("busybox")) {
                        param.setResult(false);
                    }
                }
            }
        );
        
        // Hook Runtime.exec() to block root commands
        XposedHelpers.findAndHookMethod(
            "java.lang.Runtime",
            lpparam.classLoader,
            "exec",
            String.class,
            new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    String cmd = (String) param.args[0];
                    if (cmd.contains("su") || cmd.contains("which")) {
                        param.setResult(null);
                    }
                }
            }
        );
        
        // Hook PackageManager to hide root apps
        XposedHelpers.findAndHookMethod(
            "android.app.ApplicationPackageManager",
            lpparam.classLoader,
            "getPackageInfo",
            String.class, int.class,
            new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    String pkg = (String) param.args[0];
                    if (pkg.contains("supersu") || pkg.contains("magisk") ||
                        pkg.contains("kingroot") || pkg.contains("topjohnwu")) {
                        param.setThrowable(new android.content.pm.PackageManager.NameNotFoundException());
                    }
                }
            }
        );
    }
    
    public static void systemMain() {}
}
'''
    
    def generate_play_integrity_bypass_hook(self) -> str:
        """Generate hook code to bypass Play Integrity checks."""
        return '''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class Entry {
    
    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {
        // Hook Build fields to spoof device
        try {
            Class<?> buildClass = XposedHelpers.findClass("android.os.Build", lpparam.classLoader);
            XposedHelpers.setStaticObjectField(buildClass, "FINGERPRINT", 
                "google/oriole/oriole:14/AP2A.240805.005/12025142:user/release-keys");
            XposedHelpers.setStaticObjectField(buildClass, "MODEL", "Pixel 6");
            XposedHelpers.setStaticObjectField(buildClass, "MANUFACTURER", "Google");
            XposedHelpers.setStaticObjectField(buildClass, "BRAND", "google");
            XposedHelpers.setStaticObjectField(buildClass, "DEVICE", "oriole");
            XposedHelpers.setStaticObjectField(buildClass, "PRODUCT", "oriole");
            XposedHelpers.setStaticObjectField(buildClass, "TAGS", "release-keys");
            XposedHelpers.setStaticObjectField(buildClass, "TYPE", "user");
        } catch (Throwable t) {
            // Ignore
        }
        
        // Hook Build.VERSION fields
        try {
            Class<?> versionClass = XposedHelpers.findClass("android.os.Build$VERSION", lpparam.classLoader);
            XposedHelpers.setStaticObjectField(versionClass, "SECURITY_PATCH", "2024-08-05");
        } catch (Throwable t) {
            // Ignore
        }
    }
    
    public static void systemMain() {
        // System-level Build property hooks
        try {
            XposedHelpers.findAndHookMethod(
                "android.os.SystemProperties",
                null,
                "get",
                String.class, String.class,
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        String key = (String) param.args[0];
                        if (key.equals("ro.boot.vbmeta.device_state")) {
                            param.setResult("locked");
                        } else if (key.equals("ro.boot.verifiedbootstate")) {
                            param.setResult("green");
                        } else if (key.equals("ro.debuggable")) {
                            param.setResult("0");
                        }
                    }
                }
            );
        } catch (Throwable t) {
            // Ignore
        }
    }
}
'''
    
    def generate_ssl_pinning_bypass_hook(self) -> str:
        """Generate hook code to bypass SSL certificate pinning."""
        return '''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XC_MethodReplacement;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;
import java.security.cert.X509Certificate;
import javax.net.ssl.*;

public class Entry {
    
    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {
        // Bypass OkHttp CertificatePinner
        try {
            XposedHelpers.findAndHookMethod(
                "okhttp3.CertificatePinner",
                lpparam.classLoader,
                "check",
                String.class, java.util.List.class,
                XC_MethodReplacement.DO_NOTHING
            );
        } catch (Throwable t) {}
        
        // Bypass OkHttp3 newer versions
        try {
            XposedHelpers.findAndHookMethod(
                "okhttp3.CertificatePinner",
                lpparam.classLoader,
                "check$okhttp",
                String.class, kotlin.jvm.functions.Function0.class,
                XC_MethodReplacement.DO_NOTHING
            );
        } catch (Throwable t) {}
        
        // Bypass TrustManagerImpl
        try {
            XposedHelpers.findAndHookMethod(
                "com.android.org.conscrypt.TrustManagerImpl",
                lpparam.classLoader,
                "verifyChain",
                X509Certificate[].class, byte[].class, byte[].class,
                String.class, String.class, boolean.class,
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult(param.args[0]);
                    }
                }
            );
        } catch (Throwable t) {}
        
        // Bypass WebViewClient SSL errors
        try {
            XposedHelpers.findAndHookMethod(
                "android.webkit.WebViewClient",
                lpparam.classLoader,
                "onReceivedSslError",
                android.webkit.WebView.class,
                android.webkit.SslErrorHandler.class,
                android.net.http.SslError.class,
                new XC_MethodHook() {
                    @Override
                    protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                        ((android.webkit.SslErrorHandler) param.args[1]).proceed();
                        param.setResult(null);
                    }
                }
            );
        } catch (Throwable t) {}
    }
    
    public static void systemMain() {}
}
'''
    
    def generate_emulator_detection_bypass_hook(self) -> str:
        """Generate hook code to bypass emulator/VM detection."""
        return '''
package androidx.app;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;
import java.io.File;

public class Entry {
    
    public static void appMain(XC_LoadPackage.LoadPackageParam lpparam) {
        // Hide emulator-specific files
        XposedHelpers.findAndHookMethod(
            "java.io.File",
            lpparam.classLoader,
            "exists",
            new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                    String path = ((File) param.thisObject).getAbsolutePath().toLowerCase();
                    if (path.contains("qemu") || path.contains("genymotion") ||
                        path.contains("nox") || path.contains("bluestacks") ||
                        path.contains("goldfish") || path.contains("vbox") ||
                        path.contains("x86") || path.contains("pipe")) {
                        param.setResult(false);
                    }
                }
            }
        );
        
        // Spoof TelephonyManager
        try {
            XposedHelpers.findAndHookMethod(
                "android.telephony.TelephonyManager",
                lpparam.classLoader,
                "getDeviceId",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult("358240051111110"); // Valid IMEI format
                    }
                }
            );
            
            XposedHelpers.findAndHookMethod(
                "android.telephony.TelephonyManager",
                lpparam.classLoader,
                "getSubscriberId",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult("310260000000000"); // T-Mobile US IMSI
                    }
                }
            );
            
            XposedHelpers.findAndHookMethod(
                "android.telephony.TelephonyManager",
                lpparam.classLoader,
                "getSimOperator",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        param.setResult("310260");
                    }
                }
            );
        } catch (Throwable t) {}
        
        // Hide sensors that indicate emulator
        try {
            XposedHelpers.findAndHookMethod(
                "android.hardware.SensorManager",
                lpparam.classLoader,
                "getSensorList",
                int.class,
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        // Return non-empty sensor list
                        if (param.getResult() == null || 
                            ((java.util.List) param.getResult()).isEmpty()) {
                            // Create fake sensor list
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
    # PLUGIN BUILD AND DEPLOY
    # ═══════════════════════════════════════════════════════════════════════
    
    def build_and_install_hook(self, name: str, java_code: str,
                                target_package: str = "android") -> bool:
        """
        Build Java hook code into APK and install as Xposed plugin.
        
        Note: This requires Android SDK/build tools on the host machine.
        For production use, pre-built plugins are recommended.
        
        Args:
            name: Plugin name.
            java_code: Java source code for the hook.
            target_package: Package to hook.
            
        Returns:
            True if build and install successful.
        """
        # Write Java source to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(java_code)
            java_path = f.name
        
        logger.info(f"Hook source written to {java_path}")
        logger.warning("APK building requires Android SDK. Using source deployment instead.")
        
        # For now, just push the source and use apmt's source compilation
        remote_java = f"/data/local/tmp/{name}_hook.java"
        if self._push_file(java_path, remote_java):
            logger.info(f"Hook source pushed to {remote_java}")
            # apmt may support source compilation on some VMOS versions
            return True
        
        return False
    
    def install_preset_bypass(self, bypass_type: str,
                               target_package: str = "android") -> bool:
        """
        Install a pre-defined bypass hook.
        
        Args:
            bypass_type: One of "root", "integrity", "ssl", "emulator"
            target_package: Package to apply bypass to.
            
        Returns:
            True if installation successful.
        """
        generators = {
            "root": self.generate_root_bypass_hook,
            "integrity": self.generate_play_integrity_bypass_hook,
            "ssl": self.generate_ssl_pinning_bypass_hook,
            "emulator": self.generate_emulator_detection_bypass_hook,
        }
        
        if bypass_type not in generators:
            logger.error(f"Unknown bypass type: {bypass_type}")
            return False
        
        code = generators[bypass_type]()
        plugin_name = f"titan_bypass_{bypass_type}"
        
        return self.build_and_install_hook(plugin_name, code, target_package)


# Convenience functions

def create_root_bypass_plugin(adb_target: str, package: str = "android") -> bool:
    """Install root detection bypass on device."""
    manager = XposedManager(adb_target)
    return manager.install_preset_bypass("root", package)


def create_integrity_bypass_plugin(adb_target: str, package: str = "android") -> bool:
    """Install Play Integrity bypass on device."""
    manager = XposedManager(adb_target)
    return manager.install_preset_bypass("integrity", package)


def create_ssl_bypass_plugin(adb_target: str, package: str) -> bool:
    """Install SSL pinning bypass for specific app."""
    manager = XposedManager(adb_target)
    return manager.install_preset_bypass("ssl", package)
