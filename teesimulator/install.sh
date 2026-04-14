#!/system/bin/sh
# TEE Simulator Installation Script
# Installs TEESimulator module on device without Magisk Manager

MODDIR=/data/adb/modules/teesimulator
TMPDIR=/data/local/tmp/teesimulator
LOG=/data/local/tmp/.titan/teesimulator_install.log

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [Install] $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [Install] $1" >> $LOG
}

error() {
    log "ERROR: $1"
    exit 1
}

# Check root
if [ "$(id -u)" != "0" ]; then
    error "This script must be run as root"
fi

# Create log directory
mkdir -p /data/local/tmp/.titan

log "TEESimulator installation starting..."

# Check if Magisk is installed
if [ -d /data/adb/magisk ]; then
    log "Magisk detected, installing as Magisk module"
    INSTALL_TYPE="magisk"
elif [ -d /data/adb/ksu ]; then
    log "KernelSU detected, installing as KSU module"
    INSTALL_TYPE="ksu"
else
    log "No root manager detected, installing standalone"
    INSTALL_TYPE="standalone"
fi

# Create module directory
log "Creating module directory..."
mkdir -p $MODDIR
mkdir -p $MODDIR/system/lib64

# Copy module files
log "Copying module files..."
cp $TMPDIR/module.prop $MODDIR/
cp $TMPDIR/service.sh $MODDIR/
chmod 755 $MODDIR/service.sh

# Create post-fs-data script for early boot
cat > $MODDIR/post-fs-data.sh << 'EOF'
#!/system/bin/sh
# Early boot script - runs before zygote
MODDIR=${0%/*}

# Set critical boot properties early
resetprop -n ro.boot.vbmeta.device_state locked
resetprop -n ro.boot.verifiedbootstate green
resetprop -n ro.boot.flash.locked 1
EOF
chmod 755 $MODDIR/post-fs-data.sh

# Create system.prop for persistent properties
cat > $MODDIR/system.prop << 'EOF'
# TEESimulator system properties
ro.boot.vbmeta.device_state=locked
ro.boot.verifiedbootstate=green
ro.boot.flash.locked=1
ro.boot.veritymode=enforcing
ro.boot.warranty_bit=0
ro.warranty_bit=0
ro.debuggable=0
ro.secure=1
ro.build.type=user
ro.build.tags=release-keys
EOF

# For standalone installation, also set properties immediately
if [ "$INSTALL_TYPE" = "standalone" ]; then
    log "Setting properties for standalone mode..."
    
    # Check if resetprop is available
    if command -v resetprop >/dev/null 2>&1; then
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
        log "Properties set via resetprop"
    else
        log "WARNING: resetprop not available, properties will be set on next boot"
    fi
    
    # Create init.d script for boot persistence
    if [ -d /system/etc/init.d ]; then
        cp $MODDIR/service.sh /system/etc/init.d/99-teesimulator
        chmod 755 /system/etc/init.d/99-teesimulator
        log "Installed init.d script"
    fi
fi

# Mark installation complete
setprop persist.titan.teesimulator.installed 1
setprop persist.titan.teesimulator.version "1.0.0"

log "TEESimulator installation complete!"
log "Installation type: $INSTALL_TYPE"
log "Module directory: $MODDIR"

if [ "$INSTALL_TYPE" != "standalone" ]; then
    log "Please reboot to activate the module"
else
    log "Properties have been applied (reboot recommended)"
fi

exit 0
