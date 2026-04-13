#!/system/bin/sh
# TEE Simulator Uninstallation Script

MODDIR=/data/adb/modules/teesimulator
LOG=/data/local/tmp/.titan/teesimulator_install.log

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [Uninstall] $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [Uninstall] $1" >> $LOG
}

log "TEESimulator uninstallation starting..."

# Remove module directory
if [ -d "$MODDIR" ]; then
    rm -rf "$MODDIR"
    log "Removed module directory"
fi

# Remove init.d script if exists
if [ -f /system/etc/init.d/99-teesimulator ]; then
    rm -f /system/etc/init.d/99-teesimulator
    log "Removed init.d script"
fi

# Clear properties
setprop persist.titan.teesimulator.installed 0
setprop persist.titan.teesimulator.active 0

log "TEESimulator uninstallation complete"
log "Reboot required to fully remove TEE simulation"

exit 0
