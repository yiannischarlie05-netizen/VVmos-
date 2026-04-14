#!/usr/bin/env python3
"""Phase 4: Google Account Injection for ACP250329ACQRPDV

Builds accounts_ce.db and accounts_de.db host-side, pushes via turbo pusher,
then injects GMS/Chrome/Play Store shared preferences.
"""
import asyncio, sys, time, uuid, secrets
sys.path.insert(0, 'vmos_titan/core')
sys.path.insert(0, 'core')
sys.path.insert(0, 'server')

from vmos_cloud_api import VMOSCloudClient
from vmos_db_builder import VMOSDbBuilder
from vmos_turbo_pusher import VMOSTurboPusher, BatchFile

PAD = 'ACP250329ACQRPDV'
EMAIL = 'epolusamuel682@gmail.com'
DISPLAY_NAME = 'Samuel Epolu'
GAIA_ID = '117892456301834567'  # synthetic but realistic 18-digit
AGE_DAYS = 120  # 4 months of account age

async def sh(cmd, label='', timeout=30):
    """Execute shell command on VMOS device."""
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
    print('=== PHASE 4: GOOGLE ACCOUNT INJECTION ===')
    print(f'    Email: {EMAIL}')
    print(f'    Device: {PAD}')
    
    # Step 1: Build databases host-side
    print('\n[1] Building databases host-side...')
    builder = VMOSDbBuilder()
    
    # Build accounts_ce.db with synthetic tokens (no real OAuth for now)
    synth_tokens = {
        'com.google': f'ya29.{secrets.token_urlsafe(100)}',
        'oauth2:https://www.googleapis.com/auth/userinfo.email': f'ya29.{secrets.token_urlsafe(80)}',
        'oauth2:https://www.googleapis.com/auth/userinfo.profile': f'ya29.{secrets.token_urlsafe(80)}',
        'oauth2:https://www.googleapis.com/auth/plus.me': f'ya29.{secrets.token_urlsafe(80)}',
    }
    
    accts_ce_bytes = builder.build_accounts_ce(
        email=EMAIL,
        display_name=DISPLAY_NAME,
        gaia_id=GAIA_ID,
        tokens=synth_tokens,
        age_days=AGE_DAYS,
    )
    print(f'  accounts_ce.db: {len(accts_ce_bytes)} bytes')
    
    accts_de_bytes = builder.build_accounts_de(
        email=EMAIL,
        display_name=DISPLAY_NAME,
        gaia_id=GAIA_ID,
        age_days=AGE_DAYS,
    )
    print(f'  accounts_de.db: {len(accts_de_bytes)} bytes')
    
    # Step 2: Stop account services before injection
    print('\n[2] Stopping account services...')
    await sh(
        'am force-stop com.google.android.gms; '
        'am force-stop com.google.android.gms.setup; '
        'am force-stop com.google.android.gsf; '
        'am force-stop com.android.vending; '
        'echo STOP_OK',
        'stop-services'
    )
    await asyncio.sleep(5)
    
    # Step 3: Create directories
    print('\n[3] Creating directories...')
    await sh(
        'mkdir -p /data/system_ce/0 /data/system_de/0 2>/dev/null; '
        'rm -f /data/system_ce/0/accounts_ce.db* /data/system_de/0/accounts_de.db* 2>/dev/null; '
        'echo DIR_OK',
        'create-dirs'
    )
    await asyncio.sleep(5)
    
    # Step 4: Push databases via turbo pusher
    print('\n[4] Pushing databases via turbo pusher...')
    client = VMOSCloudClient()
    pusher = VMOSTurboPusher(client, PAD)
    
    # Push accounts_ce.db
    ce_result = await pusher.push_file(
        accts_ce_bytes,
        '/data/system_ce/0/accounts_ce.db',
        owner='system:system',
        mode='660'
    )
    print(f'  accounts_ce.db push: {"OK" if ce_result.success else "FAILED"} '
          f'({ce_result.chunks_sent} chunks, {ce_result.elapsed_sec:.1f}s)')
    if not ce_result.success:
        print(f'  ERROR: {ce_result.error}')
    
    await asyncio.sleep(3)
    
    # Push accounts_de.db
    de_result = await pusher.push_file(
        accts_de_bytes,
        '/data/system_de/0/accounts_de.db',
        owner='system:system',
        mode='660'
    )
    print(f'  accounts_de.db push: {"OK" if de_result.success else "FAILED"} '
          f'({de_result.chunks_sent} chunks, {de_result.elapsed_sec:.1f}s)')
    if not de_result.success:
        print(f'  ERROR: {de_result.error}')
    
    await asyncio.sleep(5)
    
    # Step 5: Set ownership and SELinux on DB files
    print('\n[5] Setting ownership and SELinux contexts...')
    await sh(
        'chown 1000:1000 /data/system_ce/0/accounts_ce.db 2>/dev/null; '
        'chown 1000:1000 /data/system_de/0/accounts_de.db 2>/dev/null; '
        'chmod 660 /data/system_ce/0/accounts_ce.db 2>/dev/null; '
        'chmod 660 /data/system_de/0/accounts_de.db 2>/dev/null; '
        'restorecon -R /data/system_ce/0/ /data/system_de/0/ 2>/dev/null; '
        'echo PERM_OK',
        'set-perms'
    )
    await asyncio.sleep(5)
    
    # Step 6: Inject GMS shared preferences
    print('\n[6] Injecting GMS shared preferences...')
    now_ms = int(time.time() * 1000)
    android_id = '3fa9f06d9b7be9f8'  # from Phase 1 scan
    gsf_id = secrets.token_hex(8)
    
    # GMS device_registration
    gms_prefs = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="android_id">{android_id}</string>
    <long name="registration_timestamp" value="{now_ms - AGE_DAYS * 86400000}" />
    <string name="registered_account">{EMAIL}</string>
    <boolean name="device_registered" value="true" />
</map>'''
    
    await sh(
        f'mkdir -p /data/data/com.google.android.gms/shared_prefs 2>/dev/null; '
        f'cat > /data/data/com.google.android.gms/shared_prefs/device_registration.xml << \'XMLEOF\'\n{gms_prefs}\nXMLEOF\n'
        f'echo GMS_REG_OK',
        'gms-registration'
    )
    await asyncio.sleep(5)
    
    # GSF gservices
    gsf_prefs = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="android_id">{gsf_id}</string>
    <long name="digest" value="{now_ms - AGE_DAYS * 86400000}" />
</map>'''
    
    await sh(
        f'mkdir -p /data/data/com.google.android.gsf/shared_prefs 2>/dev/null; '
        f'cat > /data/data/com.google.android.gsf/shared_prefs/gservices.xml << \'XMLEOF\'\n{gsf_prefs}\nXMLEOF\n'
        f'echo GSF_OK',
        'gsf-prefs'
    )
    await asyncio.sleep(5)
    
    # GMS CheckinService (for GSF alignment)
    checkin_prefs = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="deviceId">{gsf_id}</string>
    <long name="lastCheckinTime" value="{now_ms}" />
    <string name="digest">1-{secrets.token_hex(20)}</string>
</map>'''
    
    await sh(
        f'cat > /data/data/com.google.android.gms/shared_prefs/CheckinService.xml << \'XMLEOF\'\n{checkin_prefs}\nXMLEOF\n'
        f'echo CHECKIN_OK',
        'gms-checkin'
    )
    await asyncio.sleep(5)
    
    # Step 7: Play Store prefs
    print('\n[7] Injecting Play Store prefs...')
    finsky_prefs = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="signed_in_account">{EMAIL}</string>
    <boolean name="setup_complete" value="true" />
    <boolean name="tos_accepted" value="true" />
    <long name="last_sync_time" value="{now_ms}" />
</map>'''
    
    await sh(
        f'mkdir -p /data/data/com.android.vending/shared_prefs 2>/dev/null; '
        f'cat > /data/data/com.android.vending/shared_prefs/finsky.xml << \'XMLEOF\'\n{finsky_prefs}\nXMLEOF\n'
        f'echo FINSKY_OK',
        'play-store'
    )
    await asyncio.sleep(5)
    
    # Step 8: Chrome account prefs
    print('\n[8] Injecting Chrome account prefs...')
    await sh(
        f'mkdir -p /data/data/com.android.chrome/shared_prefs 2>/dev/null; '
        f'cat > /data/data/com.android.chrome/shared_prefs/AccountSync.xml << \'XMLEOF\'\n'
        f'<?xml version=\'1.0\' encoding=\'utf-8\' standalone=\'yes\' ?>\n'
        f'<map>\n'
        f'    <string name="signed_in_account">{EMAIL}</string>\n'
        f'    <boolean name="sync_enabled" value="true" />\n'
        f'</map>\nXMLEOF\n'
        f'echo CHROME_OK',
        'chrome-prefs'
    )
    await asyncio.sleep(5)
    
    # Step 9: Fix ownership on all injected prefs
    print('\n[9] Fixing ownership on all prefs...')
    await sh(
        'gms_uid=$(stat -c %u /data/data/com.google.android.gms 2>/dev/null || echo 10007); '
        'gsf_uid=$(stat -c %u /data/data/com.google.android.gsf 2>/dev/null || echo 10006); '
        'vend_uid=$(stat -c %u /data/data/com.android.vending 2>/dev/null || echo 10026); '
        'chrome_uid=$(stat -c %u /data/data/com.android.chrome 2>/dev/null || echo 10057); '
        'chown -R $gms_uid:$gms_uid /data/data/com.google.android.gms/shared_prefs/ 2>/dev/null; '
        'chown -R $gsf_uid:$gsf_uid /data/data/com.google.android.gsf/shared_prefs/ 2>/dev/null; '
        'chown -R $vend_uid:$vend_uid /data/data/com.android.vending/shared_prefs/ 2>/dev/null; '
        'chown -R $chrome_uid:$chrome_uid /data/data/com.android.chrome/shared_prefs/ 2>/dev/null; '
        'restorecon -R /data/data/com.google.android.gms /data/data/com.google.android.gsf '
        '/data/data/com.android.vending /data/data/com.android.chrome 2>/dev/null; '
        'echo CHOWN_OK',
        'fix-ownership'
    )
    await asyncio.sleep(5)
    
    # Step 10: Verification
    print('\n=== VERIFICATION ===')
    await sh('dumpsys account 2>/dev/null | head -30', 'verify-accounts')
    await asyncio.sleep(4)
    await sh('sqlite3 /data/system_ce/0/accounts_ce.db "SELECT name,type FROM accounts" 2>/dev/null || echo NO_SQLITE3', 'verify-db')
    await asyncio.sleep(4)
    await sh('ls -la /data/system_ce/0/accounts_ce.db /data/system_de/0/accounts_de.db 2>/dev/null', 'verify-files')
    await asyncio.sleep(4)
    await sh('cat /data/data/com.google.android.gms/shared_prefs/device_registration.xml 2>/dev/null | head -5', 'verify-gms')
    
    print('\n=== PHASE 4 COMPLETE ===')

if __name__ == '__main__':
    asyncio.run(main())
