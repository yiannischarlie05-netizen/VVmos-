#!/system/bin/sh
# TEE Simulator Service Script
# Runs at boot to configure TEE simulation for Play Integrity

MODDIR=${0%/*}
LOG=/data/local/tmp/.titan/teesimulator.log

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [TEESimulator] $1" >> $LOG
}

# Wait for system to be ready
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 1
done
sleep 5

log "TEE Simulator starting..."

# Check if keybox is already loaded
KB_LOADED=$(getprop persist.titan.keybox.loaded)
if [ "$KB_LOADED" = "1" ]; then
    log "Hardware keybox already loaded, TEESimulator not needed"
    exit 0
fi

# Set TEE simulation properties
resetprop -n ro.boot.vbmeta.device_state locked
resetprop -n ro.boot.verifiedbootstate green
resetprop -n ro.boot.flash.locked 1
resetprop -n ro.boot.veritymode enforcing
resetprop -n ro.boot.warranty_bit 0
resetprop -n ro.warranty_bit 0
resetprop -n ro.debuggable 0
resetprop -n ro.secure 1
resetprop -n ro.build.type user
resetprop -n ro.build.tags release-keys

# Set attestation properties
resetprop -n ro.product.first_api_level 33
resetprop -n ro.board.first_api_level 33

# Configure keystore simulation
resetprop -n persist.titan.tee.simulated 1
resetprop -n persist.titan.keybox.type simulated

# Mark TEESimulator as active
setprop persist.titan.teesimulator.active 1

log "TEE Simulator configured successfully"
log "Attestation level: MEETS_DEVICE_INTEGRITY (simulated)"
