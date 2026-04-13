#!/bin/bash
# TEESimulator Remote Installation Script
# Installs TEESimulator module on a target device via ADB

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TEESIM_DIR="$PROJECT_DIR/teesimulator"

usage() {
    echo "Usage: $0 <adb_target>"
    echo ""
    echo "Arguments:"
    echo "  adb_target    ADB device target (e.g., 127.0.0.1:6520 or device serial)"
    echo ""
    echo "Example:"
    echo "  $0 127.0.0.1:6520"
    exit 1
}

if [ -z "$1" ]; then
    usage
fi

ADB_TARGET="$1"

echo "=== TEESimulator Installation ==="
echo "Target: $ADB_TARGET"
echo ""

# Check ADB connection
echo "[1/5] Checking ADB connection..."
if ! adb -s "$ADB_TARGET" get-state >/dev/null 2>&1; then
    echo "ERROR: Cannot connect to device $ADB_TARGET"
    exit 1
fi
echo "      Connected"

# Check root access
echo "[2/5] Checking root access..."
ROOT_CHECK=$(adb -s "$ADB_TARGET" shell "id -u" 2>/dev/null | tr -d '\r')
if [ "$ROOT_CHECK" != "0" ]; then
    echo "WARNING: Not running as root, some features may not work"
fi

# Create remote directory
echo "[3/5] Creating remote directory..."
adb -s "$ADB_TARGET" shell "mkdir -p /data/local/tmp/teesimulator"
adb -s "$ADB_TARGET" shell "mkdir -p /data/local/tmp/.titan"

# Push module files
echo "[4/5] Pushing module files..."
adb -s "$ADB_TARGET" push "$TEESIM_DIR/module.prop" /data/local/tmp/teesimulator/
adb -s "$ADB_TARGET" push "$TEESIM_DIR/service.sh" /data/local/tmp/teesimulator/
adb -s "$ADB_TARGET" push "$TEESIM_DIR/install.sh" /data/local/tmp/teesimulator/
adb -s "$ADB_TARGET" push "$TEESIM_DIR/uninstall.sh" /data/local/tmp/teesimulator/

# Make scripts executable
adb -s "$ADB_TARGET" shell "chmod 755 /data/local/tmp/teesimulator/*.sh"

# Run installation
echo "[5/5] Running installation script..."
adb -s "$ADB_TARGET" shell "sh /data/local/tmp/teesimulator/install.sh"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Verify installation:"
echo "  adb -s $ADB_TARGET shell getprop persist.titan.teesimulator.installed"
echo ""
echo "Check if active (after reboot):"
echo "  adb -s $ADB_TARGET shell getprop persist.titan.teesimulator.active"
