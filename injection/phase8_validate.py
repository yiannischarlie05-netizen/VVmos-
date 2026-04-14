#!/usr/bin/env python3
"""Phase 8: Final Validation & Trust Score Audit for ACP250329ACQRPDV

Runs comprehensive 14-check trust audit + 13-check wallet verification.
"""
import asyncio, sys
sys.path.insert(0, 'vmos_titan/core')
sys.path.insert(0, 'core')
sys.path.insert(0, 'server')

from vmos_cloud_api import VMOSCloudClient

PAD = 'ACP250329ACQRPDV'

async def sh(cmd, label='', timeout=30):
    client = VMOSCloudClient()
    r = await client.async_adb_cmd([PAD], cmd)
    tid = None
    if r.get('code') == 200:
        data = r.get('data', [])
        if data:
            tid = data[0].get('taskId')
    if not tid:
        code = r.get('code', '?')
        if code == 110031:
            print(f'  [{label}] Rate limited, waiting 30s...')
            await asyncio.sleep(30)
            return await sh(cmd, label, timeout)
        print(f'  [{label}] CMD_ERROR:{code}')
        return f'CMD_ERROR:{code}'
    for i in range(timeout):
        await asyncio.sleep(1)
        d = await client.task_detail([tid])
        if d.get('code') == 200:
            items = d.get('data', [])
            if items and items[0].get('taskStatus') == 3:
                result = items[0].get('taskResult', '') or ''
                return result
            if items and items[0].get('taskStatus', 0) < 0:
                return 'TASK_FAILED'
    return 'TIMEOUT'


async def check(cmd, label, check_fn):
    """Run check and evaluate pass/fail."""
    result = await sh(cmd, label)
    passed, detail = check_fn(result.strip() if result else '')
    status = '✅ PASS' if passed else '❌ FAIL'
    score = 1 if passed else 0
    print(f'  {status}  {label}: {detail}')
    return score


async def main():
    print('=' * 60)
    print('  FINAL VALIDATION - ACP250329ACQRPDV')
    print('  Genesis Pipeline Comprehensive Audit')
    print('=' * 60)
    
    total_score = 0
    max_score = 0
    
    # ── IDENTITY CHECKS ──────────────────────────────────
    print('\n── IDENTITY & STEALTH ──')
    
    # 1. Verified boot state
    max_score += 1
    total_score += await check(
        'cat /proc/cmdline | grep -o "verifiedbootstate=[a-z]*"',
        'Verified Boot State',
        lambda r: ('green' in r, r or 'NOT_FOUND')
    )
    await asyncio.sleep(4)
    
    # 2. Build type
    max_score += 1
    total_score += await check(
        'getprop ro.build.type',
        'Build Type',
        lambda r: (r == 'user', r)
    )
    await asyncio.sleep(4)
    
    # 3. Build tags
    max_score += 1
    total_score += await check(
        'getprop ro.build.tags',
        'Build Tags',
        lambda r: (r == 'release-keys', r)
    )
    await asyncio.sleep(4)
    
    # 4. SIM state
    max_score += 1
    total_score += await check(
        'getprop gsm.sim.state',
        'SIM State',
        lambda r: (r == 'READY', r)
    )
    await asyncio.sleep(4)
    
    # 5. Carrier
    max_score += 1
    total_score += await check(
        'getprop gsm.operator.alpha',
        'Carrier',
        lambda r: ('T-Mobile' in r, r or 'NOT_SET')
    )
    await asyncio.sleep(4)
    
    # 6. Timezone
    max_score += 1
    total_score += await check(
        'getprop persist.sys.timezone',
        'Timezone',
        lambda r: ('Los_Angeles' in r, r)
    )
    await asyncio.sleep(4)
    
    # 7. SELinux
    max_score += 1
    total_score += await check(
        'getenforce',
        'SELinux',
        lambda r: ('Enforcing' in r, r)
    )
    await asyncio.sleep(4)
    
    # ── ACCOUNT CHECKS ──────────────────────────────────
    print('\n── GOOGLE ACCOUNT ──')
    
    # 8. accounts_ce.db exists
    max_score += 1
    total_score += await check(
        'ls -la /data/system_ce/0/accounts_ce.db 2>/dev/null | wc -l',
        'accounts_ce.db Exists',
        lambda r: (r.strip() == '1', 'Present' if r.strip() == '1' else 'MISSING')
    )
    await asyncio.sleep(4)
    
    # 9. accounts_de.db exists
    max_score += 1
    total_score += await check(
        'ls -la /data/system_de/0/accounts_de.db 2>/dev/null | wc -l',
        'accounts_de.db Exists',
        lambda r: (r.strip() == '1', 'Present' if r.strip() == '1' else 'MISSING')
    )
    await asyncio.sleep(4)
    
    # 10. GMS device registration
    max_score += 1
    total_score += await check(
        'cat /data/data/com.google.android.gms/shared_prefs/device_registration.xml 2>/dev/null | grep -c "device_registered"',
        'GMS Device Registration',
        lambda r: (r.strip() == '1', 'Registered' if r.strip() == '1' else 'NOT_REGISTERED')
    )
    await asyncio.sleep(4)
    
    # ── WALLET CHECKS ──────────────────────────────────
    print('\n── WALLET & PAYMENT ──')
    
    # 11. tapandpay.db (wallet)
    max_score += 1
    total_score += await check(
        'ls /data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db 2>/dev/null && echo EXISTS || echo MISSING',
        'tapandpay.db (Wallet)',
        lambda r: ('EXISTS' in r, 'Present' if 'EXISTS' in r else 'MISSING')
    )
    await asyncio.sleep(4)
    
    # 12. tapandpay.db (GMS)
    max_score += 1
    total_score += await check(
        'ls /data/data/com.google.android.gms/databases/tapandpay.db 2>/dev/null && echo EXISTS || echo MISSING',
        'tapandpay.db (GMS)',
        lambda r: ('EXISTS' in r, 'Present' if 'EXISTS' in r else 'MISSING')
    )
    await asyncio.sleep(4)
    
    # 13. COIN.xml zero-auth flags
    max_score += 1
    total_score += await check(
        'cat /data/data/com.android.vending/shared_prefs/com.android.vending.billing.InAppBillingService.COIN.xml 2>/dev/null | grep -c "value=\\"true\\""',
        'COIN.xml Zero-Auth Flags',
        lambda r: (int(r.strip() or '0') >= 7, f'{r.strip()} true flags (need ≥7)')
    )
    await asyncio.sleep(4)
    
    # 14. NFC enabled
    max_score += 1
    total_score += await check(
        'settings get secure nfc_on',
        'NFC Enabled',
        lambda r: (r.strip() == '1', 'Enabled' if r.strip() == '1' else 'DISABLED')
    )
    await asyncio.sleep(4)
    
    # 15. Wallet setup complete
    max_score += 1
    total_score += await check(
        'cat /data/data/com.google.android.gms/shared_prefs/wallet_instrument_prefs.xml 2>/dev/null | grep -c "wallet_setup_complete"',
        'Wallet Setup Complete',
        lambda r: (r.strip() == '1', 'Complete' if r.strip() == '1' else 'NOT_SETUP')
    )
    await asyncio.sleep(4)
    
    # 16. Payment sync blocked
    max_score += 1
    total_score += await check(
        'iptables -L OUTPUT -n 2>/dev/null | grep -c "payments.google.com"',
        'Payment Sync Blocked',
        lambda r: (int(r.strip() or '0') >= 1, 'Blocked' if int(r.strip() or '0') >= 1 else 'NOT_BLOCKED')
    )
    await asyncio.sleep(4)
    
    # ── DATA AGING CHECKS ──────────────────────────────
    print('\n── DATA AGING & TRUST ──')
    
    # 17. Contacts
    max_score += 1
    total_score += await check(
        'content query --uri content://com.android.contacts/contacts --projection _id 2>/dev/null | wc -l',
        'Contacts Count',
        lambda r: (int(r.strip() or '0') >= 5, f'{r.strip()} contacts (need ≥5)')
    )
    await asyncio.sleep(4)
    
    # 18. Call logs
    max_score += 1
    total_score += await check(
        'content query --uri content://call_log/calls --projection _id 2>/dev/null | wc -l',
        'Call Log Count',
        lambda r: (int(r.strip() or '0') >= 10, f'{r.strip()} calls (need ≥10)')
    )
    await asyncio.sleep(4)
    
    # 19. SMS
    max_score += 1
    total_score += await check(
        'content query --uri content://sms --projection _id 2>/dev/null | wc -l',
        'SMS Count',
        lambda r: (int(r.strip() or '0') >= 5, f'{r.strip()} messages (need ≥5)')
    )
    await asyncio.sleep(4)
    
    # 20. WiFi networks
    max_score += 1
    total_score += await check(
        'cat /data/misc/apexdata/com.android.wifi/WifiConfigStore.xml 2>/dev/null | grep -c "SSID"',
        'WiFi Networks',
        lambda r: (int(r.strip() or '0') >= 5, f'{r.strip()} networks (need ≥5)')
    )
    await asyncio.sleep(4)
    
    # 21. UsageStats
    max_score += 1
    total_score += await check(
        'ls /data/system/usagestats/0/daily/ 2>/dev/null | wc -l',
        'UsageStats Files',
        lambda r: (int(r.strip() or '0') >= 5, f'{r.strip()} daily files (need ≥5)')
    )
    await asyncio.sleep(4)
    
    # 22. library.db
    max_score += 1
    total_score += await check(
        'ls /data/data/com.android.vending/databases/library.db 2>/dev/null && echo EXISTS || echo MISSING',
        'Play Store library.db',
        lambda r: ('EXISTS' in r, 'Present' if 'EXISTS' in r else 'MISSING')
    )
    await asyncio.sleep(4)
    
    # 23. File timestamps backdated
    max_score += 1
    total_score += await check(
        'stat -c %Y /data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db 2>/dev/null',
        'tapandpay.db Backdated',
        lambda r: (int(r.strip() or '0') < 1740000000, 
                   f'timestamp={r.strip()}' if r.strip() else 'MISSING')
    )
    await asyncio.sleep(4)
    
    # ── PROC STERILIZATION ──────────────────────────────
    print('\n── PROC STERILIZATION ──')
    
    # 24. No VMOS markers in cmdline
    max_score += 1
    total_score += await check(
        'cat /proc/cmdline 2>/dev/null | grep -ciE "vmos|armcloud|cuttlefish|vsoc"',
        'Cmdline Clean (no VM markers)',
        lambda r: (r.strip() == '0', 'Clean' if r.strip() == '0' else f'{r.strip()} markers found')
    )
    await asyncio.sleep(4)
    
    # 25. Frida ports blocked
    max_score += 1
    total_score += await check(
        'iptables -L INPUT -n 2>/dev/null | grep -c "27042"',
        'Frida Port Blocked',
        lambda r: (int(r.strip() or '0') >= 1, 'Blocked' if int(r.strip() or '0') >= 1 else 'OPEN')
    )
    await asyncio.sleep(4)
    
    # ── FINAL SCORE ──────────────────────────────────
    pct = (total_score / max_score * 100) if max_score > 0 else 0
    grade = 'A+' if pct >= 95 else 'A' if pct >= 90 else 'B' if pct >= 80 else 'C' if pct >= 70 else 'F'
    
    print('\n' + '=' * 60)
    print(f'  TRUST SCORE: {total_score}/{max_score} ({pct:.0f}%) — Grade: {grade}')
    print('=' * 60)
    
    if pct >= 85:
        print('  STATUS: READY FOR OPERATIONS')
        print('  Recommended: Klarna ($300-600), Affirm ($200-500),')
        print('               Afterpay ($300-600), Play Store zero-auth')
    elif pct >= 70:
        print('  STATUS: MARGINAL — some checks need fixing')
        print('  Recommended: Afterpay only ($150-300), Sezzle ($150-350)')
    else:
        print('  STATUS: NOT READY — significant gaps')
    
    print()

if __name__ == '__main__':
    asyncio.run(main())
