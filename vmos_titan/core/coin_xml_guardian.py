"""
CoinXmlGuardian — inotify-based file watcher for COIN.xml persistence.

This module monitors the Play Store's COIN.xml SharedPreferences file and
auto-restores it from backup if cloud reconciliation attempts to overwrite
the injected billing state.

Gap P1 Implementation: FileObserver for COIN.xml persistence to eliminate
reconciliation risk when iptables rules fail or are temporarily cleared.
"""

import subprocess
import hashlib
import time
import logging
import threading
import os
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class GuardianState(Enum):
    """State of the COIN.xml guardian."""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class GuardianStatus:
    """Status report for the guardian."""
    state: GuardianState
    coin_xml_path: str
    backup_path: str
    backup_exists: bool
    backup_checksum: Optional[str]
    current_checksum: Optional[str]
    restore_count: int
    last_restore_time: Optional[float]
    uptime_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "coin_xml_path": self.coin_xml_path,
            "backup_path": self.backup_path,
            "backup_exists": self.backup_exists,
            "backup_checksum": self.backup_checksum,
            "current_checksum": self.current_checksum,
            "restore_count": self.restore_count,
            "last_restore_time": self.last_restore_time,
            "uptime_seconds": self.uptime_seconds
        }


# COIN.xml paths for Play Store billing state
COIN_XML_PATHS = [
    "/data/data/com.android.vending/shared_prefs/COIN.xml",
    "/data/user/0/com.android.vending/shared_prefs/COIN.xml",
]

BACKUP_PATH = "/data/local/tmp/.titan/coin_backup.xml"
BACKUP_DIR = "/data/local/tmp/.titan"


class CoinXmlGuardian:
    """
    Monitor and auto-restore COIN.xml to maintain zero-auth billing state.
    
    Uses inotifywait on the device to detect file modifications in real-time.
    When COIN.xml is modified by cloud sync, restores from backup immediately.
    
    Usage:
        guardian = CoinXmlGuardian(adb_target="127.0.0.1:6520")
        guardian.create_backup()  # After initial COIN.xml injection
        guardian.start()          # Begin monitoring
        ...
        guardian.stop()           # Stop monitoring
    """
    
    def __init__(self, adb_target: str = "127.0.0.1:6520"):
        """
        Initialize guardian.
        
        Args:
            adb_target: ADB target device (IP:port or serial)
        """
        self.adb_target = adb_target
        self._state = GuardianState.STOPPED
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._restore_count = 0
        self._last_restore_time: Optional[float] = None
        self._start_time: Optional[float] = None
        self._coin_xml_path: Optional[str] = None
        self._on_restore_callback: Optional[Callable] = None
    
    def _sh(self, cmd: str, timeout: int = 30) -> str:
        """Execute shell command on device via ADB."""
        try:
            full_cmd = f"adb -s {self.adb_target} shell {cmd}"
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {cmd}")
            return ""
        except Exception as e:
            logger.error(f"Shell command failed: {e}")
            return ""
    
    def _sh_async(self, cmd: str) -> subprocess.Popen:
        """Execute async shell command on device via ADB."""
        full_cmd = f"adb -s {self.adb_target} shell {cmd}"
        return subprocess.Popen(
            full_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    def _find_coin_xml_path(self) -> Optional[str]:
        """Find the actual COIN.xml path on device."""
        for path in COIN_XML_PATHS:
            if self._sh(f"ls {path} 2>/dev/null"):
                return path
        return None
    
    def _get_file_checksum(self, path: str) -> Optional[str]:
        """Get SHA256 checksum of a file on device."""
        output = self._sh(f"sha256sum {path} 2>/dev/null")
        if output:
            return output.split()[0]
        return None
    
    def _get_vending_uid(self) -> Optional[str]:
        """Get the UID of com.android.vending (Play Store)."""
        output = self._sh("stat -c %u /data/data/com.android.vending 2>/dev/null")
        return output if output else None
    
    def create_backup(self) -> bool:
        """
        Create backup of current COIN.xml.
        
        Should be called after successful wallet injection to capture
        the canonical zero-auth billing state.
        
        Returns:
            True if backup created successfully
        """
        self._coin_xml_path = self._find_coin_xml_path()
        if not self._coin_xml_path:
            logger.error("COIN.xml not found on device")
            return False
        
        # Create backup directory
        self._sh(f"mkdir -p {BACKUP_DIR}")
        
        # Copy COIN.xml to backup location
        result = self._sh(f"cp {self._coin_xml_path} {BACKUP_PATH}")
        
        # Verify backup exists
        if self._sh(f"ls {BACKUP_PATH} 2>/dev/null"):
            checksum = self._get_file_checksum(BACKUP_PATH)
            logger.info(f"COIN.xml backup created: {BACKUP_PATH} (checksum: {checksum})")
            return True
        
        logger.error("Failed to create COIN.xml backup")
        return False
    
    def restore_from_backup(self) -> bool:
        """
        Restore COIN.xml from backup.
        
        Returns:
            True if restore successful
        """
        if not self._coin_xml_path:
            self._coin_xml_path = self._find_coin_xml_path()
            if not self._coin_xml_path:
                logger.error("Cannot restore: COIN.xml path unknown")
                return False
        
        # Check backup exists
        if not self._sh(f"ls {BACKUP_PATH} 2>/dev/null"):
            logger.error("Cannot restore: backup does not exist")
            return False
        
        # Get vending UID for ownership fix
        vending_uid = self._get_vending_uid()
        
        # Restore from backup
        self._sh(f"cp {BACKUP_PATH} {self._coin_xml_path}")
        
        # Fix ownership
        if vending_uid:
            self._sh(f"chown {vending_uid}:{vending_uid} {self._coin_xml_path}")
        
        # Fix permissions (SharedPrefs are typically 0660)
        self._sh(f"chmod 660 {self._coin_xml_path}")
        
        # Restore SELinux context
        self._sh(f"restorecon {self._coin_xml_path} 2>/dev/null")
        
        # Verify restore
        backup_checksum = self._get_file_checksum(BACKUP_PATH)
        current_checksum = self._get_file_checksum(self._coin_xml_path)
        
        if backup_checksum and current_checksum and backup_checksum == current_checksum:
            self._restore_count += 1
            self._last_restore_time = time.time()
            logger.info(f"COIN.xml restored from backup (restore #{self._restore_count})")
            
            if self._on_restore_callback:
                try:
                    self._on_restore_callback(self._restore_count)
                except Exception as e:
                    logger.warning(f"Restore callback failed: {e}")
            
            return True
        
        logger.error("COIN.xml restore verification failed")
        return False
    
    def _check_inotifywait_available(self) -> bool:
        """Check if inotifywait is available on device."""
        output = self._sh("which inotifywait 2>/dev/null")
        return bool(output)
    
    def _monitor_loop_inotify(self):
        """Monitor loop using inotifywait (preferred method)."""
        if not self._coin_xml_path:
            self._coin_xml_path = self._find_coin_xml_path()
        
        if not self._coin_xml_path:
            logger.error("Cannot start monitor: COIN.xml not found")
            self._state = GuardianState.ERROR
            return
        
        # Get initial checksum
        canonical_checksum = self._get_file_checksum(BACKUP_PATH)
        if not canonical_checksum:
            logger.error("Cannot start monitor: backup checksum unavailable")
            self._state = GuardianState.ERROR
            return
        
        logger.info(f"Starting inotify monitor on {self._coin_xml_path}")
        
        # Monitor using inotifywait in a loop
        watch_dir = os.path.dirname(self._coin_xml_path)
        watch_file = os.path.basename(self._coin_xml_path)
        
        while not self._stop_event.is_set():
            try:
                # Use inotifywait to watch for modifications
                proc = self._sh_async(
                    f"inotifywait -q -e modify,delete,move {self._coin_xml_path} 2>/dev/null"
                )
                
                # Wait for event or stop signal
                while not self._stop_event.is_set():
                    try:
                        proc.wait(timeout=1)
                        # Process exited, meaning event occurred
                        break
                    except subprocess.TimeoutExpired:
                        continue
                
                if self._stop_event.is_set():
                    proc.terminate()
                    break
                
                # Event detected - check if COIN.xml was modified
                current_checksum = self._get_file_checksum(self._coin_xml_path)
                
                if current_checksum != canonical_checksum:
                    logger.warning("COIN.xml modification detected - restoring from backup")
                    self.restore_from_backup()
                
                # Small delay to prevent rapid fire
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"inotify monitor error: {e}")
                time.sleep(5)  # Back off on error
    
    def _monitor_loop_polling(self):
        """Fallback monitor loop using polling (if inotifywait unavailable)."""
        if not self._coin_xml_path:
            self._coin_xml_path = self._find_coin_xml_path()
        
        if not self._coin_xml_path:
            logger.error("Cannot start monitor: COIN.xml not found")
            self._state = GuardianState.ERROR
            return
        
        canonical_checksum = self._get_file_checksum(BACKUP_PATH)
        if not canonical_checksum:
            logger.error("Cannot start monitor: backup checksum unavailable")
            self._state = GuardianState.ERROR
            return
        
        logger.info(f"Starting polling monitor on {self._coin_xml_path}")
        
        while not self._stop_event.is_set():
            try:
                current_checksum = self._get_file_checksum(self._coin_xml_path)
                
                if current_checksum and current_checksum != canonical_checksum:
                    logger.warning("COIN.xml modification detected - restoring from backup")
                    self.restore_from_backup()
                
                # Poll every 2 seconds
                self._stop_event.wait(2)
                
            except Exception as e:
                logger.error(f"Polling monitor error: {e}")
                time.sleep(5)
    
    def start(self, on_restore: Optional[Callable] = None) -> bool:
        """
        Start the guardian monitoring.
        
        Args:
            on_restore: Optional callback called on each restore (receives count)
            
        Returns:
            True if started successfully
        """
        if self._state == GuardianState.RUNNING:
            logger.warning("Guardian already running")
            return True
        
        # Verify backup exists
        if not self._sh(f"ls {BACKUP_PATH} 2>/dev/null"):
            logger.error("Cannot start: no backup exists. Call create_backup() first.")
            return False
        
        self._on_restore_callback = on_restore
        self._stop_event.clear()
        self._start_time = time.time()
        
        # Choose monitor method based on inotifywait availability
        if self._check_inotifywait_available():
            monitor_func = self._monitor_loop_inotify
        else:
            logger.warning("inotifywait not available, falling back to polling")
            monitor_func = self._monitor_loop_polling
        
        self._monitor_thread = threading.Thread(
            target=monitor_func,
            daemon=True,
            name="CoinXmlGuardian"
        )
        self._monitor_thread.start()
        self._state = GuardianState.RUNNING
        
        logger.info("COIN.xml guardian started")
        return True
    
    def stop(self):
        """Stop the guardian monitoring."""
        if self._state != GuardianState.RUNNING:
            return
        
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None
        
        self._state = GuardianState.STOPPED
        logger.info("COIN.xml guardian stopped")
    
    def get_status(self) -> GuardianStatus:
        """Get current guardian status."""
        backup_exists = bool(self._sh(f"ls {BACKUP_PATH} 2>/dev/null"))
        backup_checksum = self._get_file_checksum(BACKUP_PATH) if backup_exists else None
        
        coin_path = self._coin_xml_path or self._find_coin_xml_path() or COIN_XML_PATHS[0]
        current_checksum = self._get_file_checksum(coin_path)
        
        uptime = time.time() - self._start_time if self._start_time else 0
        
        return GuardianStatus(
            state=self._state,
            coin_xml_path=coin_path,
            backup_path=BACKUP_PATH,
            backup_exists=backup_exists,
            backup_checksum=backup_checksum,
            current_checksum=current_checksum,
            restore_count=self._restore_count,
            last_restore_time=self._last_restore_time,
            uptime_seconds=uptime
        )


def install_guardian_daemon(adb_target: str = "127.0.0.1:6520") -> bool:
    """
    Install guardian daemon script for boot persistence.
    
    Creates a script in /data/local/tmp that can be started via init.d
    or manually to maintain COIN.xml persistence across reboots.
    
    Args:
        adb_target: ADB device target
        
    Returns:
        True if installed successfully
    """
    daemon_script = '''#!/system/bin/sh
# COIN.xml Guardian Daemon - Titan V13
# Monitors and restores COIN.xml if modified by cloud sync

COIN_XML="/data/data/com.android.vending/shared_prefs/COIN.xml"
BACKUP="/data/local/tmp/.titan/coin_backup.xml"
LOG="/data/local/tmp/.titan/guardian.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> $LOG
}

# Check if backup exists
if [ ! -f "$BACKUP" ]; then
    log "ERROR: No backup found at $BACKUP"
    exit 1
fi

CANONICAL_HASH=$(sha256sum $BACKUP | cut -d' ' -f1)
log "Guardian started. Canonical hash: $CANONICAL_HASH"

# Get vending UID
VENDING_UID=$(stat -c %u /data/data/com.android.vending 2>/dev/null)

while true; do
    sleep 2
    
    if [ ! -f "$COIN_XML" ]; then
        log "COIN.xml missing - restoring"
        cp $BACKUP $COIN_XML
        [ -n "$VENDING_UID" ] && chown $VENDING_UID:$VENDING_UID $COIN_XML
        chmod 660 $COIN_XML
        continue
    fi
    
    CURRENT_HASH=$(sha256sum $COIN_XML | cut -d' ' -f1)
    
    if [ "$CURRENT_HASH" != "$CANONICAL_HASH" ]; then
        log "COIN.xml modified (hash: $CURRENT_HASH) - restoring"
        cp $BACKUP $COIN_XML
        [ -n "$VENDING_UID" ] && chown $VENDING_UID:$VENDING_UID $COIN_XML
        chmod 660 $COIN_XML
    fi
done
'''
    
    try:
        # Create daemon directory
        subprocess.run(
            f"adb -s {adb_target} shell mkdir -p /data/local/tmp/.titan",
            shell=True, check=True
        )
        
        # Write daemon script
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(daemon_script)
            temp_path = f.name
        
        subprocess.run(
            f"adb -s {adb_target} push {temp_path} /data/local/tmp/.titan/coin_guardian.sh",
            shell=True, check=True
        )
        
        os.unlink(temp_path)
        
        # Make executable
        subprocess.run(
            f"adb -s {adb_target} shell chmod 755 /data/local/tmp/.titan/coin_guardian.sh",
            shell=True, check=True
        )
        
        logger.info("Guardian daemon installed at /data/local/tmp/.titan/coin_guardian.sh")
        return True
        
    except Exception as e:
        logger.error(f"Failed to install guardian daemon: {e}")
        return False


def start_guardian_daemon(adb_target: str = "127.0.0.1:6520") -> bool:
    """
    Start the guardian daemon in background on device.
    
    Args:
        adb_target: ADB device target
        
    Returns:
        True if started successfully
    """
    try:
        # Kill any existing daemon
        subprocess.run(
            f"adb -s {adb_target} shell 'pkill -f coin_guardian.sh' 2>/dev/null",
            shell=True
        )
        
        # Start daemon in background
        subprocess.run(
            f"adb -s {adb_target} shell 'nohup /data/local/tmp/.titan/coin_guardian.sh > /dev/null 2>&1 &'",
            shell=True, check=True
        )
        
        # Verify running
        time.sleep(1)
        output = subprocess.run(
            f"adb -s {adb_target} shell 'pgrep -f coin_guardian.sh'",
            shell=True, capture_output=True, text=True
        )
        
        if output.stdout.strip():
            logger.info(f"Guardian daemon started (PID: {output.stdout.strip()})")
            return True
        
        logger.warning("Guardian daemon may not have started")
        return False
        
    except Exception as e:
        logger.error(f"Failed to start guardian daemon: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:6520"
    
    print(f"Testing COIN.xml Guardian on {target}...")
    guardian = CoinXmlGuardian(target)
    
    # Create backup
    print("\n1. Creating backup...")
    if guardian.create_backup():
        print("   Backup created successfully")
    else:
        print("   Failed to create backup")
        sys.exit(1)
    
    # Get status
    print("\n2. Guardian status:")
    status = guardian.get_status()
    print(f"   State: {status.state.value}")
    print(f"   Backup exists: {status.backup_exists}")
    print(f"   Backup checksum: {status.backup_checksum}")
    print(f"   Current checksum: {status.current_checksum}")
    
    # Start monitoring
    print("\n3. Starting guardian...")
    if guardian.start(on_restore=lambda c: print(f"   Restored! (count: {c})")):
        print("   Guardian running")
    else:
        print("   Failed to start guardian")
    
    # Wait a bit
    print("\n4. Monitoring for 10 seconds...")
    time.sleep(10)
    
    # Stop
    print("\n5. Stopping guardian...")
    guardian.stop()
    print("   Guardian stopped")
    
    # Final status
    print("\n6. Final status:")
    status = guardian.get_status()
    print(f"   Restore count: {status.restore_count}")
    print(f"   Uptime: {status.uptime_seconds:.1f}s")
