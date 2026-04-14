#!/bin/bash
# verify_accounts_and_logins.sh - Comprehensive account and login verification

set -e

DEVICE_ID="$1"
if [ -z "$DEVICE_ID" ]; then
    echo "Usage: $0 <device-id-or-serial>"
    exit 1
fi

echo "════════════════════════════════════════════════════════════════"
echo "ACCOUNT & LOGIN VERIFICATION — Device: $DEVICE_ID"
echo "════════════════════════════════════════════════════════════════"

# [1] System Accounts
echo ""
echo "[1] System Accounts in AccountManager:"
echo "────────────────────────────────────────"
adb -s "$DEVICE_ID" shell "dumpsys account 2>/dev/null | grep -A 20 'Accounts:'" || echo "⚠ Cannot access dumpsys account"

# [2] Account Databases
echo ""
echo "[2] System Account Databases:"
echo "────────────────────────────────────────"
adb -s "$DEVICE_ID" shell "ls -la /data/system_ce/0/accounts*.db 2>/dev/null || echo '⚠ No CE accounts DB'"
adb -s "$DEVICE_ID" shell "ls -la /data/system_de/0/accounts*.db 2>/dev/null || echo '⚠ No DE accounts DB'"

# [3] GMS Accounts
echo ""
echo "[3] GMS Account Registration:"
echo "────────────────────────────────────────"
adb -s "$DEVICE_ID" shell "dumpsys account 2>/dev/null | grep -i 'com.google' | head -5" || echo "⚠ No GMS accounts found"

# [4] Chrome Saved Logins
echo ""
echo "[4] Chrome Saved Logins:"
echo "────────────────────────────────────────"
adb -s "$DEVICE_ID" shell "find /data/data/com.android.chrome/app_chrome -name 'Login*' -ls 2>/dev/null || echo '⚠ No Chrome login data'"

# [5] Chrome Cookies Check
echo ""
echo "[5] Chrome Authentication Cookies:"
echo "────────────────────────────────────────"
adb -s "$DEVICE_ID" shell "find /data/data/com.android.chrome -name 'Cookies*' -ls 2>/dev/null || echo '⚠ No Chrome cookies'"

# [6] Telegram Account Status
echo ""
echo "[6] Telegram Session Status:"
echo "────────────────────────────────────────"
if adb -s "$DEVICE_ID" shell "pm list packages -3 | grep -q telegram"; then
    echo "✓ Telegram installed"
    adb -s "$DEVICE_ID" shell "ls -la /data/data/org.telegram.messenger.web/files/ 2>/dev/null | grep -E 'tgnet|cache' || echo '⚠ No session files'"
else
    echo "✗ Telegram NOT installed"
fi

# [7] GMS Services Check
echo ""
echo "[7] GMS Services Status:"
echo "────────────────────────────────────────"
adb -s "$DEVICE_ID" shell "pm list packages | grep -E 'gms|gsf|vending'" || echo "⚠ GMS packages not found"

# [8] Revolut Account Check
echo ""
echo "[8] Revolut App & Databases:"
echo "────────────────────────────────────────"
if adb -s "$DEVICE_ID" shell "pm list packages | grep -q revolut"; then
    echo "✓ Revolut installed"
    adb -s "$DEVICE_ID" shell "ls -la /data/data/com.revolut.revolut/databases/ 2>/dev/null | grep -E 'accounts|android-devices|aqueduct' || echo '⚠ No Revolut DBs'"
else
    echo "✗ Revolut NOT installed"
fi

# [9] Device Identity Check
echo ""
echo "[9] Device Identity Properties:"
echo "────────────────────────────────────────"
echo "Android ID:"
adb -s "$DEVICE_ID" shell "getprop ro.android_id"
echo "Build Fingerprint:"
adb -s "$DEVICE_ID" shell "getprop ro.build.fingerprint"
echo "IMEI:"
adb -s "$DEVICE_ID" shell "getprop ro.gsm.imei"

# [10] Overall Status
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "SUMMARY:"
echo "────────────────────────────────────────"

accounts_count=$(adb -s "$DEVICE_ID" shell "dumpsys account 2>/dev/null | grep -c 'account {' || echo '0'")
echo "Total registered accounts: $accounts_count"

if [ "$accounts_count" -gt 0 ]; then
    echo "✓ ACCOUNTS ACTIVE - Injection appears successful"
else
    echo "✗ NO ACCOUNTS - Injection may have failed or not yet complete"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
