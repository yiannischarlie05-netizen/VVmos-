"""
TapAndPayGuardian — inotify-based wallet DB persistence daemon.
================================================================
Monitors tapandpay.db (Google Pay token database) and auto-restores
from backup when GMS cloud reconciliation attempts to delete injected
payment tokens.

Gap #3 from research report cross-reference:
- coin_xml_guardian.py protects COIN.xml (Play Store billing state)
- NO equivalent exists for tapandpay.db (Google Pay payment tokens)
- GMS periodically syncs to payments.google.com → unrecognized tokens deleted
- If iptables sync blocking (Layer 3/5) fails, tapandpay.db gets wiped
- This module provides last-line defense via filesystem monitoring

Covers BOTH tapandpay.db copy paths:
    /data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db
    /data/data/com.google.android.gms/databases/tapandpay.db

Also monitors WAL journal files (-wal, -journal, -shm) to prevent
partial-write corruption from cloud sync race conditions.

Pattern follows coin_xml_guardian.py: inotify preferred, polling fallback,
daemon script for boot persistence, threaded monitoring.
"""

from __future__ import annotations

import hashlib
import logging
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class GuardianState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class GuardianStatus:
    state: GuardianState
    monitored_paths: List[str]
    backup_dir: str
    backup_exists: bool
    token_count: int
    restore_count: int
    last_restore_time: Optional[float]
    uptime_seconds: float
    checksums: Dict[str, Optional[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "monitored_paths": self.monitored_paths,
            "backup_dir": self.backup_dir,
            "backup_exists": self.backup_exists,
            "token_count": self.token_count,
            "restore_count": self.restore_count,
            "last_restore_time": self.last_restore_time,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "checksums": self.checksums,
        }


# Both possible tapandpay.db locations
TAPANDPAY_PATHS = [
    "/data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db",
    "/data/data/com.google.android.gms/databases/tapandpay.db",
]

# WAL/journal companions to monitor
WAL_SUFFIXES = ["-wal", "-journal", "-shm"]

BACKUP_DIR = "/data/local/tmp/.titan/wallet_backup"
POLL_INTERVAL_S = 3
RESTORE_COOLDOWN_S = 5  # Prevent rapid-fire restores


class TapAndPayGuardian:
    """
    Monitor and auto-restore tapandpay.db to maintain wallet injection state.

    Uses inotifywait on the device to detect file modifications in real-time.
    When tapandpay.db is modified by GMS cloud reconciliation, restores from
    backup and re-applies ownership + permissions.

    Usage:
        guardian = TapAndPayGuardian(adb_target="127.0.0.1:6520")
        guardian.create_backup()   # After wallet_provisioner injection
        guardian.start()           # Begin monitoring
        ...
        guardian.stop()

    For VMOS Cloud devices:
        guardian = TapAndPayGuardian(
            adb_target="ACP250329ACQRPDV",
            use_vmos_api=True,
        )
    """

    def __init__(self, adb_target: str = "127.0.0.1:6520",
                 use_vmos_api: bool = False):
        self.adb_target = adb_target
        self.use_vmos_api = use_vmos_api
        self._state = GuardianState.STOPPED
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._restore_count = 0
        self._last_restore_time: Optional[float] = None
        self._start_time: Optional[float] = None
        self._active_paths: List[str] = []
        self._canonical_checksums: Dict[str, str] = {}
        self._on_restore_callback: Optional[Callable] = None
        self._vmos_client = None

    # ──────────────────────────────────────────────────────────────
    # Shell execution
    # ──────────────────────────────────────────────────────────────

    def _sh(self, cmd: str, timeout: int = 30) -> str:
        """Execute shell command on device."""
        if self.use_vmos_api:
            return self._sh_vmos(cmd, timeout)

        try:
            full_cmd = f"adb -s {self.adb_target} shell {cmd}"
            result = subprocess.run(
                full_cmd, shell=True,
                capture_output=True, text=True, timeout=timeout,
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {cmd[:80]}")
            return ""
        except Exception as e:
            logger.error(f"Shell command failed: {e}")
            return ""

    def _sh_vmos(self, cmd: str, timeout: int = 30) -> str:
        """Execute via VMOS Cloud API (sync wrapper)."""
        import asyncio

        async def _run():
            if self._vmos_client is None:
                from vmos_cloud_api import VMOSCloudClient
                self._vmos_client = VMOSCloudClient()
            result = await self._vmos_client.async_adb_cmd(
                [self.adb_target], cmd,
            )
            if isinstance(result, dict):
                return str(result.get("data", {}).get("result", ""))
            return str(result)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, _run()).result(timeout=timeout)
            return asyncio.run(_run())
        except Exception as e:
            logger.error(f"VMOS shell failed: {e}")
            return ""

    def _sh_async(self, cmd: str) -> subprocess.Popen:
        """Execute async shell command (local ADB only)."""
        full_cmd = f"adb -s {self.adb_target} shell {cmd}"
        return subprocess.Popen(
            full_cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )

    # ──────────────────────────────────────────────────────────────
    # File utilities
    # ──────────────────────────────────────────────────────────────

    def _get_checksum(self, path: str) -> Optional[str]:
        output = self._sh(f"sha256sum {path} 2>/dev/null")
        if output and " " in output:
            return output.split()[0]
        return None

    def _file_exists(self, path: str) -> bool:
        return bool(self._sh(f"[ -f {path} ] && echo yes"))

    def _get_app_uid(self, package: str) -> Optional[str]:
        output = self._sh(f"stat -c %u /data/data/{package} 2>/dev/null")
        return output if output and output.isdigit() else None

    def _get_token_count(self, db_path: str) -> int:
        output = self._sh(
            f"sqlite3 {db_path} 'SELECT COUNT(*) FROM tokens;' 2>/dev/null"
        )
        try:
            return int(output)
        except (ValueError, TypeError):
            return 0

    # ──────────────────────────────────────────────────────────────
    # Path discovery
    # ──────────────────────────────────────────────────────────────

    def _find_active_paths(self) -> List[str]:
        """Find which tapandpay.db paths actually exist."""
        active = []
        for path in TAPANDPAY_PATHS:
            if self._file_exists(path):
                active.append(path)
        return active

    def _backup_path_for(self, db_path: str) -> str:
        """Get backup file path for a given tapandpay.db location."""
        # Use sanitized path as filename
        safe_name = db_path.replace("/", "_").lstrip("_")
        return f"{BACKUP_DIR}/{safe_name}"

    # ──────────────────────────────────────────────────────────────
    # Backup operations
    # ──────────────────────────────────────────────────────────────

    def create_backup(self) -> bool:
        """
        Create backup of all tapandpay.db instances.

        Should be called AFTER wallet_provisioner.provision_card()
        completes and cards are visible in Google Pay.

        Returns:
            True if at least one backup was created.
        """
        self._active_paths = self._find_active_paths()
        if not self._active_paths:
            logger.error("No tapandpay.db found on device")
            return False

        self._sh(f"mkdir -p {BACKUP_DIR}")

        backed_up = 0
        for db_path in self._active_paths:
            backup = self._backup_path_for(db_path)

            # Force WAL checkpoint to merge journal into main DB
            self._sh(
                f"sqlite3 {db_path} 'PRAGMA wal_checkpoint(FULL);' 2>/dev/null"
            )

            # Copy main DB file
            self._sh(f"cp {db_path} {backup}")

            if self._file_exists(backup):
                checksum = self._get_checksum(backup)
                self._canonical_checksums[db_path] = checksum
                token_count = self._get_token_count(backup)
                logger.info(
                    f"Backup created: {backup} "
                    f"(checksum: {checksum}, tokens: {token_count})"
                )
                backed_up += 1
            else:
                logger.error(f"Failed to create backup for {db_path}")

        return backed_up > 0

    # ──────────────────────────────────────────────────────────────
    # Restore operations
    # ──────────────────────────────────────────────────────────────

    def restore_from_backup(self, db_path: Optional[str] = None) -> bool:
        """
        Restore tapandpay.db from backup.

        Handles: file copy → WAL removal → ownership → permissions →
                 SELinux context → force-stop wallet app.

        Args:
            db_path: Specific path to restore, or None for all.

        Returns:
            True if at least one restore succeeded.
        """
        # Cooldown to prevent rapid-fire restores
        if self._last_restore_time:
            elapsed = time.time() - self._last_restore_time
            if elapsed < RESTORE_COOLDOWN_S:
                logger.debug("Restore cooldown active, skipping")
                return False

        paths_to_restore = [db_path] if db_path else self._active_paths
        restored = 0

        for path in paths_to_restore:
            if not path:
                continue
            backup = self._backup_path_for(path)
            if not self._file_exists(backup):
                logger.warning(f"No backup for {path}")
                continue

            # Force-stop wallet before restoring
            if "walletnfcrel" in path:
                pkg = "com.google.android.apps.walletnfcrel"
            else:
                pkg = "com.google.android.gms"
            self._sh(f"am force-stop {pkg}")

            # Remove WAL/journal companions (prevent partial-write corruption)
            for suffix in WAL_SUFFIXES:
                self._sh(f"rm -f {path}{suffix}")

            # Restore from backup
            self._sh(f"cp {backup} {path}")

            # Fix ownership to match app UID
            uid = self._get_app_uid(pkg)
            if uid:
                self._sh(f"chown {uid}:{uid} {path}")

            # Fix permissions (SQLite DBs are 0660)
            self._sh(f"chmod 660 {path}")

            # Restore SELinux context
            self._sh(f"restorecon {path} 2>/dev/null")

            # Verify
            backup_cksum = self._get_checksum(backup)
            current_cksum = self._get_checksum(path)
            if backup_cksum and current_cksum and backup_cksum == current_cksum:
                restored += 1
                logger.info(f"tapandpay.db restored: {path}")
            else:
                logger.error(f"Restore verification failed for {path}")

        if restored > 0:
            self._restore_count += 1
            self._last_restore_time = time.time()

            if self._on_restore_callback:
                try:
                    self._on_restore_callback(self._restore_count)
                except Exception as e:
                    logger.warning(f"Restore callback error: {e}")

        return restored > 0

    # ──────────────────────────────────────────────────────────────
    # Monitor loops
    # ──────────────────────────────────────────────────────────────

    def _check_inotifywait(self) -> bool:
        return bool(self._sh("which inotifywait 2>/dev/null"))

    def _monitor_loop_inotify(self):
        """Monitor tapandpay.db via inotifywait (preferred)."""
        if not self._active_paths:
            self._active_paths = self._find_active_paths()
        if not self._active_paths:
            logger.error("No tapandpay.db found — cannot start monitor")
            self._state = GuardianState.ERROR
            return

        logger.info(f"inotify monitor started on {self._active_paths}")

        while not self._stop_event.is_set():
            for db_path in self._active_paths:
                db_dir = os.path.dirname(db_path)
                db_file = os.path.basename(db_path)

                try:
                    # Watch for modifications, deletions, moves
                    proc = self._sh_async(
                        f"inotifywait -q -t 5 "
                        f"-e modify,delete,move,moved_from "
                        f"{db_path} 2>/dev/null"
                    )

                    while not self._stop_event.is_set():
                        try:
                            proc.wait(timeout=1)
                            break  # Event fired or timeout
                        except subprocess.TimeoutExpired:
                            continue

                    if self._stop_event.is_set():
                        proc.terminate()
                        break

                    # Check if DB was tampered
                    current = self._get_checksum(db_path)
                    canonical = self._canonical_checksums.get(db_path)
                    if canonical and current != canonical:
                        token_count = self._get_token_count(db_path)
                        logger.warning(
                            f"tapandpay.db modification detected! "
                            f"tokens={token_count}, restoring backup"
                        )
                        self.restore_from_backup(db_path)

                except Exception as e:
                    logger.error(f"inotify error: {e}")
                    time.sleep(5)

            if not self._stop_event.is_set():
                time.sleep(0.5)

    def _monitor_loop_polling(self):
        """Fallback polling monitor (if inotifywait unavailable)."""
        if not self._active_paths:
            self._active_paths = self._find_active_paths()
        if not self._active_paths:
            logger.error("No tapandpay.db found — cannot start monitor")
            self._state = GuardianState.ERROR
            return

        logger.info(f"Polling monitor started on {self._active_paths}")

        while not self._stop_event.is_set():
            for db_path in self._active_paths:
                try:
                    current = self._get_checksum(db_path)
                    canonical = self._canonical_checksums.get(db_path)

                    if not current:
                        # File deleted entirely — restore
                        logger.warning(f"tapandpay.db DELETED: {db_path}")
                        self.restore_from_backup(db_path)
                    elif canonical and current != canonical:
                        token_count = self._get_token_count(db_path)
                        logger.warning(
                            f"tapandpay.db MODIFIED: {db_path} "
                            f"(tokens={token_count})"
                        )
                        self.restore_from_backup(db_path)
                except Exception as e:
                    logger.error(f"Poll error on {db_path}: {e}")

            self._stop_event.wait(POLL_INTERVAL_S)

    # ──────────────────────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────────────────────

    def start(self, on_restore: Optional[Callable] = None) -> bool:
        """
        Start the tapandpay.db guardian.

        Args:
            on_restore: Callback(restore_count) fired on each restore.

        Returns:
            True if monitoring started.
        """
        if self._state == GuardianState.RUNNING:
            logger.warning("Guardian already running")
            return True

        # Verify backups exist
        self._active_paths = self._find_active_paths()
        has_backup = False
        for path in self._active_paths:
            bp = self._backup_path_for(path)
            if self._file_exists(bp):
                has_backup = True
                # Re-read canonical checksums
                self._canonical_checksums[path] = self._get_checksum(bp)

        if not has_backup:
            logger.error(
                "No backups found. Call create_backup() after wallet injection."
            )
            return False

        self._on_restore_callback = on_restore
        self._stop_event.clear()
        self._start_time = time.time()

        if self.use_vmos_api:
            # VMOS API can't do async inotify — use polling
            monitor_fn = self._monitor_loop_polling
        elif self._check_inotifywait():
            monitor_fn = self._monitor_loop_inotify
        else:
            logger.warning("inotifywait unavailable, using polling fallback")
            monitor_fn = self._monitor_loop_polling

        self._monitor_thread = threading.Thread(
            target=monitor_fn, daemon=True, name="TapAndPayGuardian",
        )
        self._monitor_thread.start()
        self._state = GuardianState.RUNNING
        logger.info("tapandpay.db guardian started")
        return True

    def stop(self):
        """Stop the guardian."""
        if self._state != GuardianState.RUNNING:
            return
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None
        self._state = GuardianState.STOPPED
        logger.info("tapandpay.db guardian stopped")

    def get_status(self) -> GuardianStatus:
        """Get current guardian status."""
        paths = self._active_paths or self._find_active_paths()
        has_backup = any(
            self._file_exists(self._backup_path_for(p)) for p in paths
        )
        total_tokens = sum(self._get_token_count(p) for p in paths)
        checksums = {}
        for p in paths:
            checksums[p] = self._get_checksum(p)
        uptime = time.time() - self._start_time if self._start_time else 0.0

        return GuardianStatus(
            state=self._state,
            monitored_paths=paths,
            backup_dir=BACKUP_DIR,
            backup_exists=has_backup,
            token_count=total_tokens,
            restore_count=self._restore_count,
            last_restore_time=self._last_restore_time,
            uptime_seconds=uptime,
            checksums=checksums,
        )


# ──────────────────────────────────────────────────────────────────
# Boot-persistent daemon script
# ──────────────────────────────────────────────────────────────────

def install_guardian_daemon(adb_target: str = "127.0.0.1:6520") -> bool:
    """
    Install a shell-based tapandpay.db guardian for boot persistence.

    Creates /data/local/tmp/.titan/tapandpay_guardian.sh and
    optionally registers it in init.d.

    Args:
        adb_target: ADB target device.

    Returns:
        True if installed.
    """
    daemon_script = r'''#!/system/bin/sh
# tapandpay.db Guardian Daemon — Titan V13
# Monitors and restores tapandpay.db if modified by GMS cloud sync

WALLET_DB="/data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db"
GMS_DB="/data/data/com.google.android.gms/databases/tapandpay.db"
BACKUP_DIR="/data/local/tmp/.titan/wallet_backup"
LOG="/data/local/tmp/.titan/tapandpay_guardian.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG"
}

restore_db() {
    local db_path="$1"
    local safe_name=$(echo "$db_path" | tr '/' '_' | sed 's/^_//')
    local backup="$BACKUP_DIR/$safe_name"

    if [ ! -f "$backup" ]; then
        return 1
    fi

    # Determine package
    case "$db_path" in
        *walletnfcrel*) pkg="com.google.android.apps.walletnfcrel" ;;
        *) pkg="com.google.android.gms" ;;
    esac

    am force-stop "$pkg" 2>/dev/null

    # Remove WAL/journal
    rm -f "${db_path}-wal" "${db_path}-journal" "${db_path}-shm"

    # Restore
    cp "$backup" "$db_path"

    # Fix ownership
    uid=$(stat -c %u "/data/data/$pkg" 2>/dev/null)
    [ -n "$uid" ] && chown "$uid:$uid" "$db_path"
    chmod 660 "$db_path"
    restorecon "$db_path" 2>/dev/null

    log "RESTORED: $db_path (pkg=$pkg)"
}

check_db() {
    local db_path="$1"
    local safe_name=$(echo "$db_path" | tr '/' '_' | sed 's/^_//')
    local backup="$BACKUP_DIR/$safe_name"

    [ ! -f "$backup" ] && return

    if [ ! -f "$db_path" ]; then
        log "DELETED: $db_path — restoring"
        restore_db "$db_path"
        return
    fi

    BACKUP_HASH=$(sha256sum "$backup" 2>/dev/null | cut -d' ' -f1)
    CURRENT_HASH=$(sha256sum "$db_path" 2>/dev/null | cut -d' ' -f1)

    if [ "$BACKUP_HASH" != "$CURRENT_HASH" ]; then
        TOKENS=$(sqlite3 "$db_path" 'SELECT COUNT(*) FROM tokens;' 2>/dev/null)
        log "MODIFIED: $db_path (tokens=$TOKENS) — restoring"
        restore_db "$db_path"
    fi
}

log "Guardian started (PID $$)"

while true; do
    sleep 3
    check_db "$WALLET_DB"
    check_db "$GMS_DB"
done
'''

    try:
        full_cmd = f"adb -s {adb_target} shell"
        # Create directory and write script
        setup_cmds = [
            f"mkdir -p {BACKUP_DIR}",
            f"cat > {BACKUP_DIR}/../tapandpay_guardian.sh << 'EOFSCRIPT'\n{daemon_script}\nEOFSCRIPT",
            f"chmod 755 {BACKUP_DIR}/../tapandpay_guardian.sh",
        ]

        for cmd in setup_cmds:
            subprocess.run(
                f"adb -s {adb_target} shell \"{cmd}\"",
                shell=True, capture_output=True, text=True, timeout=10,
            )

        # Verify script exists
        result = subprocess.run(
            f"adb -s {adb_target} shell ls {BACKUP_DIR}/../tapandpay_guardian.sh",
            shell=True, capture_output=True, text=True, timeout=5,
        )
        if "tapandpay_guardian.sh" in result.stdout:
            logger.info("tapandpay.db guardian daemon installed")
            return True

        logger.error("Guardian daemon installation failed")
        return False

    except Exception as e:
        logger.error(f"Guardian daemon install error: {e}")
        return False
