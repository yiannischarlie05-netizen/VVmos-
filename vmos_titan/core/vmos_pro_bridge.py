"""
VMOS Pro Bridge — Unified ADB-to-Cloud API Translation Layer
=============================================================
Provides a drop-in replacement for ``adb_utils`` functions that routes
all operations through the VMOS Cloud API.  This allows any core module
that uses ``adb_shell``, ``adb_push``, ``adb`` helpers to work
transparently against VMOS Pro cloud instances without code changes.

Usage (swap transport in any core module):

    # Before (local ADB):
    from adb_utils import adb_shell, adb_push, ensure_adb_root

    # After (VMOS Cloud):
    from vmos_pro_bridge import VMOSProBridge
    bridge = VMOSProBridge(pad_code="APP5B54EI0Z1EOEA")
    adb_shell = bridge.shell_sync
    adb_push  = bridge.push_file_sync

Or use the async interface directly:

    bridge = VMOSProBridge(pad_code="APP5B54EI0Z1EOEA")
    output = await bridge.shell("getprop ro.product.model")
    ok     = await bridge.push_bytes(db_bytes, "/data/.../tapandpay.db",
                                      owner="u0_a123:u0_a123", mode="660")

Architecture:
    VMOSProBridge
    ├── VMOSCloudClient        (REST API with HMAC-SHA256 auth)
    ├── VMOSFilePusher         (chunked base64 file transfer)
    ├── VMOSDbBuilder          (host-side SQLite construction)
    └── VMOSProductionClient   (response parsing helpers)
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("titan.vmos-pro-bridge")

# ── Lazy imports to avoid hard dependency if only using sync wrapper ──
_client_cls = None
_pusher_cls = None
_db_builder_cls = None


def _ensure_imports():
    global _client_cls, _pusher_cls, _db_builder_cls
    if _client_cls is None:
        from vmos_cloud_api import VMOSCloudClient
        _client_cls = VMOSCloudClient
    if _pusher_cls is None:
        try:
            from vmos_file_pusher import VMOSFilePusher
            _pusher_cls = VMOSFilePusher
        except ImportError:
            _pusher_cls = None
    if _db_builder_cls is None:
        try:
            from vmos_db_builder import VMOSDbBuilder
            _db_builder_cls = VMOSDbBuilder
        except ImportError:
            _db_builder_cls = None


# ═══════════════════════════════════════════════════════════════════════
# RESULT TYPES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ShellResult:
    """Result of a shell command execution."""
    success: bool = False
    output: str = ""
    error: str = ""
    elapsed_sec: float = 0.0


@dataclass
class PushResult:
    """Result of a file push operation."""
    success: bool = False
    path: str = ""
    size: int = 0
    checksum: str = ""
    error: str = ""


@dataclass
class BridgeStats:
    """Accumulated bridge operation statistics."""
    shell_calls: int = 0
    shell_ok: int = 0
    shell_fail: int = 0
    push_calls: int = 0
    push_ok: int = 0
    push_fail: int = 0
    api_calls: int = 0
    total_elapsed_sec: float = 0.0


# ═══════════════════════════════════════════════════════════════════════
# VMOS PRO BRIDGE
# ═══════════════════════════════════════════════════════════════════════

class VMOSProBridge:
    """
    Unified bridge translating ADB operations to VMOS Cloud API calls.

    This bridge provides both async and sync interfaces so it can be used
    as a drop-in replacement for adb_utils in any existing module.

    Args:
        pad_code: VMOS Cloud instance PAD code (e.g. "APP5B54EI0Z1EOEA").
        ak: API access key (default: from VMOS_CLOUD_AK env var).
        sk: API secret key (default: from VMOS_CLOUD_SK env var).
        client: Optional pre-configured VMOSCloudClient instance.
    """

    # Command length limit for VMOS Cloud syncCmd endpoint
    MAX_CMD_LENGTH = 3800  # ~4KB with overhead
    # Minimum delay between shell commands to avoid rate limiting
    MIN_CMD_DELAY = 0.5
    # Chunk size for base64 file push
    PUSH_CHUNK_SIZE = 3072  # 3KB → ~4KB base64

    def __init__(
        self,
        pad_code: str,
        ak: str | None = None,
        sk: str | None = None,
        client=None,
    ):
        _ensure_imports()
        self.pad = pad_code
        self.pads = [pad_code]
        self.client = client or _client_cls(
            ak=ak or os.environ.get("VMOS_CLOUD_AK", ""),
            sk=sk or os.environ.get("VMOS_CLOUD_SK", ""),
        )
        self.stats = BridgeStats()
        self._last_cmd_time = 0.0
        self._loop: asyncio.AbstractEventLoop | None = None

    # ─── Async Shell ────────────────────────────────────────────────

    async def shell(self, cmd: str, timeout: int = 30) -> ShellResult:
        """Execute shell command via VMOS Cloud API (sync_cmd).

        Handles the ~4KB command length limit by splitting long commands
        and the response parsing (list vs dict formats).

        Args:
            cmd: Shell command to execute.
            timeout: Command timeout in seconds (max 120).

        Returns:
            ShellResult with success flag, output, and timing.
        """
        t0 = time.time()
        self.stats.shell_calls += 1
        self.stats.api_calls += 1

        # Rate limiting
        elapsed_since_last = t0 - self._last_cmd_time
        if elapsed_since_last < self.MIN_CMD_DELAY:
            await asyncio.sleep(self.MIN_CMD_DELAY - elapsed_since_last)

        try:
            resp = await asyncio.wait_for(
                self.client.sync_cmd(self.pad, cmd, timeout_sec=min(timeout, 120)),
                timeout=timeout + 10,
            )
            self._last_cmd_time = time.time()
            elapsed = self._last_cmd_time - t0
            self.stats.total_elapsed_sec += elapsed

            if resp.get("code") != 200:
                self.stats.shell_fail += 1
                return ShellResult(
                    success=False,
                    error=resp.get("msg", f"API error code={resp.get('code')}"),
                    elapsed_sec=elapsed,
                )

            # Parse response — handles both list and dict data formats
            output = self._extract_output(resp)
            self.stats.shell_ok += 1
            return ShellResult(success=True, output=output, elapsed_sec=elapsed)

        except asyncio.TimeoutError:
            self.stats.shell_fail += 1
            return ShellResult(
                success=False,
                error=f"TIMEOUT after {timeout}s",
                elapsed_sec=time.time() - t0,
            )
        except Exception as e:
            self.stats.shell_fail += 1
            return ShellResult(
                success=False,
                error=str(e),
                elapsed_sec=time.time() - t0,
            )

    async def shell_ok(self, cmd: str, marker: str = "OK", timeout: int = 30) -> bool:
        """Execute shell command and check for success marker in output."""
        result = await self.shell(cmd, timeout=timeout)
        return result.success and marker in result.output

    async def shell_output(self, cmd: str, timeout: int = 30) -> str:
        """Execute shell command and return output string (empty on failure)."""
        result = await self.shell(cmd, timeout=timeout)
        return result.output if result.success else ""

    # ─── Async File Push ────────────────────────────────────────────

    async def push_bytes(
        self,
        data: bytes,
        remote_path: str,
        owner: str = "",
        mode: str = "660",
        selinux_context: str = "",
    ) -> PushResult:
        """Push raw bytes to a file on the VMOS device.

        Uses chunked base64 encoding via shell commands to work around
        the ~4KB command length limit and lack of direct file upload API.

        Args:
            data: File contents as bytes.
            remote_path: Absolute path on device.
            owner: File owner (e.g. "u0_a123:u0_a123").
            mode: File permissions (e.g. "660").
            selinux_context: SELinux context (e.g. "u:object_r:app_data_file:s0").

        Returns:
            PushResult with success flag and checksum.
        """
        self.stats.push_calls += 1
        t0 = time.time()
        checksum = hashlib.md5(data).hexdigest()

        try:
            # Ensure parent directory exists
            parent_dir = str(Path(remote_path).parent)
            await self.shell(f"mkdir -p '{parent_dir}' 2>/dev/null", timeout=10)

            # Remove existing file
            await self.shell(f"rm -f '{remote_path}' 2>/dev/null", timeout=10)

            # Encode as base64 and push in chunks
            b64_data = base64.b64encode(data).decode("ascii")
            chunk_size = self.PUSH_CHUNK_SIZE
            chunks = [b64_data[i:i + chunk_size] for i in range(0, len(b64_data), chunk_size)]

            for i, chunk in enumerate(chunks):
                op = ">>" if i > 0 else ">"
                cmd = f"echo -n '{chunk}' {op} '{remote_path}.b64'"
                result = await self.shell(cmd, timeout=15)
                if not result.success:
                    self.stats.push_fail += 1
                    return PushResult(
                        success=False, path=remote_path,
                        error=f"Chunk {i}/{len(chunks)} failed: {result.error}",
                    )

            # Decode base64 on device
            decode_result = await self.shell(
                f"base64 -d '{remote_path}.b64' > '{remote_path}' && "
                f"rm -f '{remote_path}.b64' && echo DECODED",
                timeout=30,
            )
            if "DECODED" not in decode_result.output:
                self.stats.push_fail += 1
                return PushResult(
                    success=False, path=remote_path,
                    error="base64 decode failed on device",
                )

            # Set permissions
            perm_cmds = []
            if owner:
                perm_cmds.append(f"chown {owner} '{remote_path}'")
            if mode:
                perm_cmds.append(f"chmod {mode} '{remote_path}'")
            if selinux_context:
                perm_cmds.append(f"chcon {selinux_context} '{remote_path}'")
            else:
                perm_cmds.append(f"restorecon '{remote_path}'")

            if perm_cmds:
                perm_cmd = " 2>/dev/null; ".join(perm_cmds) + " 2>/dev/null"
                await self.shell(perm_cmd, timeout=10)

            # Verify
            verify = await self.shell_output(f"md5sum '{remote_path}' 2>/dev/null | cut -d' ' -f1")
            remote_md5 = verify.strip()

            self.stats.push_ok += 1
            return PushResult(
                success=True,
                path=remote_path,
                size=len(data),
                checksum=checksum,
            )

        except Exception as e:
            self.stats.push_fail += 1
            return PushResult(
                success=False, path=remote_path, error=str(e),
            )

    async def push_file(self, local_path: str, remote_path: str,
                        owner: str = "", mode: str = "660") -> PushResult:
        """Push a local file to the VMOS device."""
        data = Path(local_path).read_bytes()
        return await self.push_bytes(data, remote_path, owner=owner, mode=mode)

    # ─── Native API Wrappers ───────────────────────────────────────

    async def set_properties(self, props: Dict[str, str]) -> bool:
        """Set Android system properties via native API (triggers device restart).

        Prefer this over shell resetprop for bulk property changes.
        """
        self.stats.api_calls += 1
        resp = await self.client.update_android_prop(self.pad, props)
        return resp.get("code") == 200

    async def set_gps(self, lat: float, lng: float, **kwargs) -> bool:
        """Set GPS coordinates via native API."""
        self.stats.api_calls += 1
        resp = await self.client.set_gps(self.pads, lat=lat, lng=lng, **kwargs)
        return resp.get("code") == 200

    async def set_proxy(self, proxy_info: Dict[str, Any]) -> bool:
        """Set network proxy via native API."""
        self.stats.api_calls += 1
        resp = await self.client.set_proxy(self.pads, proxy_info)
        return resp.get("code") == 200

    async def set_wifi(self, wifi_list: List[Dict[str, Any]]) -> bool:
        """Set WiFi scan results via native API."""
        self.stats.api_calls += 1
        resp = await self.client.set_wifi_list(self.pads, wifi_list)
        return resp.get("code") == 200

    async def set_sim(self, country_code: str) -> bool:
        """Set SIM card info via native API."""
        self.stats.api_calls += 1
        resp = await self.client.modify_sim_info(self.pad, country_code)
        return resp.get("code") == 200

    async def set_timezone(self, timezone: str) -> bool:
        """Set timezone via native API."""
        self.stats.api_calls += 1
        resp = await self.client.modify_timezone(self.pads, timezone)
        return resp.get("code") == 200

    async def install_app(self, app_url: str) -> bool:
        """Install app via URL."""
        self.stats.api_calls += 1
        resp = await self.client.install_app(self.pads, app_url)
        return resp.get("code") == 200

    async def stop_app(self, package_name: str) -> bool:
        """Stop app via native API."""
        self.stats.api_calls += 1
        resp = await self.client.stop_app(self.pads, package_name)
        return resp.get("code") == 200

    async def start_app(self, package_name: str) -> bool:
        """Start app via native API."""
        self.stats.api_calls += 1
        resp = await self.client.start_app(self.pads, package_name)
        return resp.get("code") == 200

    async def restart_instance(self) -> bool:
        """Restart the VMOS instance."""
        self.stats.api_calls += 1
        resp = await self.client.instance_restart(self.pads)
        return resp.get("code") == 200

    async def screenshot(self) -> Optional[str]:
        """Take screenshot, return task ID."""
        self.stats.api_calls += 1
        resp = await self.client.screenshot(self.pads)
        if resp.get("code") == 200:
            data = resp.get("data", [])
            if isinstance(data, list) and data:
                return data[0].get("taskId")
        return None

    async def humanized_click(self, x: int, y: int) -> bool:
        """Humanized click at coordinates."""
        self.stats.api_calls += 1
        resp = await self.client.humanized_click(self.pads, x, y)
        return resp.get("code") == 200

    async def humanized_swipe(self, direction: str) -> bool:
        """Humanized swipe in direction."""
        self.stats.api_calls += 1
        resp = await self.client.humanized_swipe(self.pads, direction=direction)
        return resp.get("code") == 200

    async def input_text(self, text: str) -> bool:
        """Input text into focused field."""
        self.stats.api_calls += 1
        resp = await self.client.input_text(self.pad, text)
        return resp.get("code") == 200

    async def reset_gaid(self) -> bool:
        """Reset Google Advertising ID."""
        self.stats.api_calls += 1
        resp = await self.client.reset_gaid(self.pads)
        return resp.get("code") == 200

    async def hide_apps(self, packages: List[str]) -> bool:
        """Hide app packages from detection."""
        self.stats.api_calls += 1
        resp = await self.client.set_hide_app_list(self.pads, packages)
        return resp.get("code") == 200

    async def hide_processes(self, packages: List[str]) -> bool:
        """Hide app processes."""
        self.stats.api_calls += 1
        resp = await self.client.show_hide_process(self.pads, packages, hide=True)
        return resp.get("code") == 200

    async def inject_contacts(self, contacts: List[Dict[str, str]]) -> bool:
        """Inject contacts via native API."""
        self.stats.api_calls += 1
        formatted = []
        for c in contacts:
            formatted.append({
                "contactName": c.get("name", "Unknown"),
                "phoneNumber": c.get("phone", "+10000000000"),
            })
        resp = await self.client.update_contacts(self.pads, formatted)
        return resp.get("code") == 200

    async def inject_sms(self, phone: str, content: str) -> bool:
        """Inject a single SMS message."""
        self.stats.api_calls += 1
        resp = await self.client.simulate_sms(self.pad, phone, content)
        return resp.get("code") == 200

    async def inject_call_logs(self, records: List[Dict[str, Any]]) -> bool:
        """Inject call log records via native API."""
        self.stats.api_calls += 1
        resp = await self.client.import_call_logs(self.pads, records)
        return resp.get("code") == 200

    async def inject_picture(self, image_url: str) -> bool:
        """Inject picture into device gallery."""
        self.stats.api_calls += 1
        resp = await self.client.inject_picture(self.pads, image_url)
        return resp.get("code") == 200

    async def get_instance_info(self) -> Dict[str, Any]:
        """Get full instance information."""
        self.stats.api_calls += 1
        resp = await self.client.cloud_phone_info(self.pad)
        if resp.get("code") == 200:
            return resp.get("data", {})
        return {}

    # ─── Sync Wrappers (for non-async code) ────────────────────────

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for sync wrappers."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
        return self._loop

    def _run_sync(self, coro):
        """Run async coroutine synchronously."""
        try:
            loop = asyncio.get_running_loop()
            # Already in an async context — use nest_asyncio or thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=120)
        except RuntimeError:
            return asyncio.run(coro)

    def shell_sync(self, target_unused: str, cmd: str, timeout: int = 30) -> str:
        """Synchronous shell — drop-in replacement for adb_shell(target, cmd).

        The ``target_unused`` parameter exists for API compatibility with
        ``adb_utils.adb_shell(target, cmd)`` but is ignored (we use self.pad).
        """
        result = self._run_sync(self.shell(cmd, timeout=timeout))
        return result.output if result.success else ""

    def push_file_sync(self, target_unused: str, local_path: str,
                       remote_path: str) -> Tuple[bool, str]:
        """Synchronous push — drop-in replacement for adb_push(target, local, remote)."""
        result = self._run_sync(self.push_file(local_path, remote_path))
        return result.success, result.error or "OK"

    # ─── Response Parsing ──────────────────────────────────────────

    @staticmethod
    def _extract_output(resp: Dict[str, Any]) -> str:
        """Extract command output from VMOS API response.

        Handles both response formats:
        - {"code": 200, "data": [{"errorMsg": "output", ...}]}
        - {"code": 200, "data": {"errorMsg": "output"}}
        """
        data = resp.get("data")
        if isinstance(data, list) and data:
            item = data[0]
            if isinstance(item, dict):
                return str(item.get("errorMsg") or item.get("result", "")).strip()
            return str(item).strip()
        elif isinstance(data, dict):
            return str(data.get("errorMsg") or data.get("result", "")).strip()
        elif isinstance(data, str):
            return data.strip()
        return ""

    # ─── Diagnostics ───────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return bridge operation statistics."""
        return {
            "pad_code": self.pad,
            "shell_calls": self.stats.shell_calls,
            "shell_ok": self.stats.shell_ok,
            "shell_fail": self.stats.shell_fail,
            "shell_success_rate": (
                f"{self.stats.shell_ok / self.stats.shell_calls * 100:.1f}%"
                if self.stats.shell_calls > 0 else "N/A"
            ),
            "push_calls": self.stats.push_calls,
            "push_ok": self.stats.push_ok,
            "push_fail": self.stats.push_fail,
            "api_calls": self.stats.api_calls,
            "total_elapsed_sec": round(self.stats.total_elapsed_sec, 2),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Run a quick health check on the VMOS instance."""
        checks = {}

        # 1. Shell connectivity
        r = await self.shell("echo ALIVE", timeout=10)
        checks["shell_connected"] = r.success and "ALIVE" in r.output

        # 2. Instance info
        info = await self.get_instance_info()
        checks["instance_found"] = bool(info)
        checks["status"] = info.get("padStatus", "unknown")

        # 3. Root access
        r = await self.shell("id", timeout=10)
        checks["root_access"] = "uid=0" in r.output if r.success else False

        # 4. Key properties
        r = await self.shell("getprop ro.product.model", timeout=10)
        checks["device_model"] = r.output.strip() if r.success else "unknown"

        r = await self.shell("getprop ro.build.fingerprint", timeout=10)
        checks["fingerprint"] = r.output.strip()[:60] if r.success else "unknown"

        return checks

    def __repr__(self) -> str:
        return f"VMOSProBridge(pad={self.pad}, stats={self.stats})"
