"""
Frida Discoverer — Dynamic discovery of app internals for injection.

When standard API methods fail, uses Frida or shell exploration to:
- Find database paths
- Discover SharedPrefs locations
- Trace method calls
- Hook and intercept data
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredPath:
    """A discovered app path."""
    path: str
    path_type: str  # "database", "shared_prefs", "file", "directory"
    files: List[str] = field(default_factory=list)
    size_bytes: int = 0


@dataclass 
class DiscoveryResult:
    """Result of app discovery."""
    package: str
    paths: List[DiscoveredPath] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "paths": [{"path": p.path, "type": p.path_type, "files": p.files[:10]} for p in self.paths],
            "methods": self.methods[:20],
            "errors": self.errors,
        }


class FridaDiscoverer:
    """Dynamically discover app internals via Frida or shell."""
    
    # Common paths to search
    APP_PATHS = [
        "/data/data/{pkg}/shared_prefs",
        "/data/data/{pkg}/databases", 
        "/data/data/{pkg}/files",
        "/data/data/{pkg}/cache",
        "/data/data/{pkg}/app_webview",
        "/data/data/{pkg}/app_chrome",
    ]
    
    # Known wallet/payment paths
    WALLET_PATHS = [
        "/data/data/com.google.android.gms/databases/tapandpay.db",
        "/data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db",
        "/data/data/com.google.android.gms/shared_prefs/COIN.xml",
        "/data/data/com.google.android.gms/shared_prefs/wallet_instrument_prefs.xml",
    ]
    
    # Known account paths
    ACCOUNT_PATHS = [
        "/data/system_ce/0/accounts_ce.db",
        "/data/system_de/0/accounts_de.db",
        "/data/data/com.google.android.gms/shared_prefs/CheckinService.xml",
        "/data/data/com.android.vending/shared_prefs/finsky.xml",
    ]
    
    def __init__(self, client, pad_code: str):
        self.client = client
        self.pad_code = pad_code
    
    async def _shell(self, cmd: str, timeout: int = 15) -> Tuple[bool, str]:
        """Execute shell command."""
        try:
            if hasattr(self.client, 'shell'):
                return await self.client.shell(self.pad_code, cmd, timeout=timeout)
            elif hasattr(self.client, 'sync_cmd'):
                result = await self.client.sync_cmd(self.pad_code, cmd, timeout_sec=timeout)
                if result.get("code") == 200:
                    data = result.get("data")
                    if isinstance(data, list) and data:
                        output = data[0].get("errorMsg", "")
                        return True, str(output).strip() if output else ""
                return False, result.get("msg", "")
            return False, "No shell"
        except Exception as e:
            return False, str(e)
    
    async def discover_package(self, package: str) -> DiscoveryResult:
        """
        Discover all data paths for a package.
        
        Args:
            package: App package name
            
        Returns:
            DiscoveryResult with paths and files
        """
        result = DiscoveryResult(package=package)
        
        for path_template in self.APP_PATHS:
            path = path_template.format(pkg=package)
            
            # Check if path exists and list contents
            cmd = f"ls -la {path} 2>/dev/null"
            success, output = await self._shell(cmd)
            
            if success and output and "No such file" not in output:
                files = []
                for line in output.split('\n'):
                    parts = line.split()
                    if len(parts) >= 9:
                        filename = ' '.join(parts[8:])
                        if filename not in ('.', '..'):
                            files.append(filename)
                
                path_type = "shared_prefs" if "shared_prefs" in path else \
                           "database" if "databases" in path else "directory"
                
                result.paths.append(DiscoveredPath(
                    path=path,
                    path_type=path_type,
                    files=files,
                ))
        
        logger.info(f"Discovered {len(result.paths)} paths for {package}")
        return result
    
    async def discover_wallet_paths(self) -> DiscoveryResult:
        """Find Google Wallet/Pay database paths."""
        result = DiscoveryResult(package="wallet")
        
        for path in self.WALLET_PATHS:
            cmd = f"ls -la {path} 2>/dev/null"
            success, output = await self._shell(cmd)
            
            if success and output and "No such file" not in output:
                result.paths.append(DiscoveredPath(
                    path=path,
                    path_type="database" if ".db" in path else "shared_prefs",
                ))
        
        # Search for tapandpay.db anywhere
        if not result.paths:
            cmd = "find /data -name 'tapandpay.db' 2>/dev/null | head -5"
            success, output = await self._shell(cmd, timeout=30)
            if success and output:
                for path in output.split('\n'):
                    if path.strip():
                        result.paths.append(DiscoveredPath(
                            path=path.strip(),
                            path_type="database",
                        ))
        
        return result
    
    async def discover_account_paths(self) -> DiscoveryResult:
        """Find Google account database paths."""
        result = DiscoveryResult(package="accounts")
        
        for path in self.ACCOUNT_PATHS:
            cmd = f"ls -la {path} 2>/dev/null"
            success, output = await self._shell(cmd)
            
            if success and output and "No such file" not in output:
                result.paths.append(DiscoveredPath(
                    path=path,
                    path_type="database" if ".db" in path else "shared_prefs",
                ))
        
        return result
    
    async def check_frida_available(self) -> bool:
        """Check if Frida server is available."""
        cmd = "ls /data/local/tmp/frida-server 2>/dev/null"
        success, output = await self._shell(cmd)
        return success and output and "No such file" not in output
    
    async def install_frida(self, version: str = "16.2.1") -> bool:
        """
        Install Frida server.
        
        Note: Requires downloading the actual binary externally.
        This creates a placeholder script.
        """
        script = '''#!/system/bin/sh
# Frida server placeholder
# Download actual binary from:
# https://github.com/frida/frida/releases
echo "Frida placeholder - replace with actual binary"
'''
        cmd = f"echo '{script}' > /data/local/tmp/frida-server && chmod 755 /data/local/tmp/frida-server"
        success, _ = await self._shell(cmd)
        return success
    
    async def trace_method(self, package: str, method_pattern: str) -> List[str]:
        """
        Trace method calls matching pattern.
        
        Note: Requires actual Frida binary for full functionality.
        This uses logcat as fallback.
        """
        # Use logcat to trace app activity
        cmd = f"logcat -d -s {package} 2>/dev/null | grep -i '{method_pattern}' | head -20"
        success, output = await self._shell(cmd, timeout=30)
        
        if success and output:
            return output.split('\n')
        return []
    
    async def dump_database_schema(self, db_path: str) -> Dict[str, List[str]]:
        """Dump database schema."""
        schema = {}
        
        # Get table names
        cmd = f"sqlite3 {db_path} '.tables' 2>/dev/null"
        success, output = await self._shell(cmd)
        
        if success and output:
            tables = output.split()
            for table in tables[:10]:  # Limit to 10 tables
                # Get columns
                cmd = f"sqlite3 {db_path} 'PRAGMA table_info({table})' 2>/dev/null"
                success, cols = await self._shell(cmd)
                if success and cols:
                    schema[table] = [line.split('|')[1] for line in cols.split('\n') if '|' in line]
        
        return schema
    
    async def find_injection_points(self, package: str) -> Dict[str, Any]:
        """
        Find potential injection points for an app.
        
        Returns paths and methods that could be used for data injection.
        """
        result = {
            "package": package,
            "shared_prefs": [],
            "databases": [],
            "injection_methods": [],
        }
        
        # Discover paths
        discovery = await self.discover_package(package)
        
        for path in discovery.paths:
            if path.path_type == "shared_prefs":
                for f in path.files:
                    if f.endswith('.xml'):
                        result["shared_prefs"].append(f"{path.path}/{f}")
            elif path.path_type == "database":
                for f in path.files:
                    if f.endswith('.db'):
                        db_path = f"{path.path}/{f}"
                        schema = await self.dump_database_schema(db_path)
                        result["databases"].append({
                            "path": db_path,
                            "tables": list(schema.keys()),
                        })
        
        # Suggest injection methods
        if result["shared_prefs"]:
            result["injection_methods"].append("adb_push_xml")
        if result["databases"]:
            result["injection_methods"].append("sqlite3_insert")
        
        return result
