#!/usr/bin/env python3
"""Boot device, verify state, install apps from neighbor, restore data, verify with screenshots."""
import asyncio, sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['VMOS_ALLOW_RESTART_PAD'] = 'AC32010810392'

PAD = 'AC32010810392'
NEIGHBOR = '10.0.46.2'
CLONE_DIR = os.path.join(os.path.dirname(__file__), '..', 'clone_backups', '10_0_46_2_Infinix_X6531B')

# Apps to install and restore
TARGET_APPS = {
    'com.whatsapp': 'WhatsApp',
    'com.whatsapp.w4b': 'WhatsApp Business',
    'com.google.android.apps.walletnfcrel': 'Google Wallet',
}

async def cmd(client, shell_cmd, timeout=25):
    """Execute shell cmd on device, return output string."""
    r = await client.sync_cmd(PAD, shell_cmd, timeout=timeout)
    if r.get('code') == 200 and r.get('data'):
        return r['data'].get('output', '')
    return ''

async def wait_for_boot(client, max_wait=300):
    """Wait for device to reach running state and respond to sync_cmd."""
    print(f'[BOOT] Waiting for device (max {max_wait}s)...')
    start = time.time()
    
    while time.time() - start < max_wait:
        await asyncio.sleep(5)
        elapsed = int(time.time() - start)
        
        # Check padStatus
        r = await client.instance_list(page=1, rows=5)
        devs = r.get('data', {}).get('pageData', [])
        st = None
        for d in devs:
            if d['padCode'] == PAD:
                st = d['padStatus']
                break
        
        if st == 14:
            print(f'[BOOT] [{elapsed}s] Status=14 STOPPED. Triggering restart...')
            await client.instance_restart([PAD])
            await asyncio.sleep(10)
            continue
        
        if st == 10:
            # Try sync_cmd
            try:
                r2 = await client.sync_cmd(PAD, 'echo ALIVE')
                if r2.get('code') == 200 and r2.get('data') and 'ALIVE' in r2['data'].get('output', ''):
                    print(f'[BOOT] [{elapsed}s] Device ALIVE and responsive!')
                    return True
                else:
                    print(f'[BOOT] [{elapsed}s] Status=10 but sync_cmd returned {r2.get("code")}')
            except Exception as e:
                print(f'[BOOT] [{elapsed}s] Status=10 but sync_cmd error: {e}')
        elif st == 11:
            if elapsed % 30 == 0:
                print(f'[BOOT] [{elapsed}s] Still booting (status=11)...')
        else:
            print(f'[BOOT] [{elapsed}s] Status={st}')
    
    print('[BOOT] TIMEOUT - device failed to boot')
    return False

async def check_accounts(client):
    """Check what accounts are loaded."""
    out = await cmd(client, 'dumpsys account 2>/dev/null | grep "Account {" | head -10')
    if out.strip():
        print(f'[ACCOUNTS] Found accounts:\n{out}')
        return True
    else:
        print('[ACCOUNTS] No accounts loaded')
        # Check if DB files exist 
        out2 = await cmd(client, 'ls -la /data/system_ce/0/accounts_ce.db /data/system_de/0/accounts_de.db 2>&1')
        print(f'[ACCOUNTS] DB files: {out2}')
        return False

async def install_apps_from_neighbor(client):
    """Pull APKs from neighbor device and install on our device."""
    print('\n[APPS] Installing apps from neighbor...')
    
    # First check which apps are already installed
    out = await cmd(client, 'pm list packages 2>/dev/null')
    installed = set()
    for line in out.strip().split('\n'):
        if line.startswith('package:'):
            installed.add(line.split(':')[1])
    
    await asyncio.sleep(3)
    
    for pkg, name in TARGET_APPS.items():
        if pkg in installed:
            print(f'[APPS] {name} ({pkg}) already installed, skipping')
            continue
        
        print(f'[APPS] Installing {name} ({pkg})...')
        
        # Get APK path from neighbor using nc relay  
        apk_path_cmd = f'echo "pm path {pkg}" | nc -w 3 {NEIGHBOR} 5555 2>/dev/null | grep "package:" | head -1'
        # Actually, the neighbor is behind ADB - we need a different approach
        # Use the device_cloner approach: relay ADB commands via nc
        
        # Alternative: use install_app API with APK URL from APKMirror/APKPure
        # For now, try pulling from neighbor via shell relay
        relay_cmd = (
            f'rm -f /data/local/tmp/{pkg}.apk; '
            f'apk_path=$(echo "shell:pm path {pkg}" | nc -w 5 {NEIGHBOR} 5555 2>/dev/null | tr -d "\\r" | grep "package:" | cut -d: -f2 | head -1); '
            f'echo "APK_PATH=$apk_path"'
        )
        out = await cmd(client, relay_cmd)
        print(f'  Neighbor APK path: {out.strip()}')
        
        await asyncio.sleep(3)
    
    return True

async def install_apps_via_api(client):
    """Install apps via VMOS install_app API using public APK URLs."""
    print('\n[APPS] Installing apps via API...')
    
    # Check current installs
    out = await cmd(client, 'pm list packages 2>/dev/null')
    installed = set()
    for line in out.strip().split('\n'):
        if line.startswith('package:'):
            installed.add(line.split(':')[1])
    
    # APK URLs - using public CDN sources
    APK_URLS = {
        'com.whatsapp': 'https://scontent.whatsapp.net/v/t39.8562-34/513399015_588399560507606_6574543505082476641_n.apk/WhatsApp.apk',
        'com.whatsapp.w4b': None,  # Need to find URL
        'com.google.android.apps.walletnfcrel': None,  # Google Wallet
    }
    
    task_ids = []
    for pkg, name in TARGET_APPS.items():
        if pkg in installed:
            print(f'  {name} already installed')
            continue
        
        url = APK_URLS.get(pkg)
        if not url:
            print(f'  {name}: no APK URL, will try neighbor relay')
            continue
        
        print(f'  Installing {name} via API...')
        r = await client.install_app([PAD], url)
        print(f'  Result: {r}')
        if r.get('data') and isinstance(r['data'], list):
            for item in r['data']:
                if item.get('taskId'):
                    task_ids.append(item['taskId'])
        await asyncio.sleep(5)
    
    return task_ids

async def pull_apk_from_neighbor(client, pkg):
    """Pull APK from neighbor device to our device via nc relay."""
    print(f'[PULL] Pulling {pkg} from neighbor...')
    
    # Step 1: Get APK path on neighbor
    # The nc relay to ADB on neighbor needs special binary protocol
    # Instead, use our device to relay shell commands
    # Actually - the neighbor's ADB port was discovered via scanning, but
    # the nc-to-ADB approach requires proper ADB wire protocol
    
    # Simpler approach: use the fact that both devices share a /16 network
    # Set up a quick nc file transfer:
    # On neighbor (via our device relaying): cat APK | nc -l -p PORT
    # On our device: nc NEIGHBOR PORT > /data/local/tmp/pkg.apk
    
    # But we can only execute commands on OUR device, not directly on neighbor
    # The neighbor relay from device_cloner used ADB wire protocol over nc
    
    # Let's try the approach from clone_restore.py - serve files from VPS
    print(f'[PULL] Cannot directly pull from neighbor without ADB relay')
    print(f'[PULL] Will install via APK URL instead')
    return None

async def restore_app_data(client):
    """Extract appdata.tar.gz and restore per-app data."""
    print('\n[RESTORE] Restoring app data from tarball...')
    
    # Check if tarball exists
    out = await cmd(client, 'ls -la /data/local/tmp/appdata.tar.gz 2>&1')
    print(f'  Tarball: {out.strip()}')
    if 'No such file' in out:
        print('  ERROR: appdata.tar.gz not found on device!')
        return False
    
    await asyncio.sleep(3)
    
    # Extract tarball
    print('  Extracting tarball (this may take a while)...')
    out = await cmd(client, 'cd /data/local/tmp && tar xzf appdata.tar.gz 2>&1; echo RC=$?', timeout=60)
    print(f'  Extract result: {out.strip()[-200:]}')
    
    await asyncio.sleep(3)
    
    # List extracted contents
    out = await cmd(client, 'ls /data/local/tmp/data/data/ 2>/dev/null')
    print(f'  Extracted app dirs: {out.strip()}')
    
    await asyncio.sleep(3)
    
    # For each target app, restore data
    for pkg, name in TARGET_APPS.items():
        print(f'\n  Restoring data for {name} ({pkg})...')
        
        # Check if app is installed
        out = await cmd(client, f'pm path {pkg} 2>/dev/null')
        if not out.strip():
            print(f'    SKIP: {name} not installed')
            continue
        
        await asyncio.sleep(3)
        
        # Get app UID
        out = await cmd(client, f'stat -c %u /data/data/{pkg} 2>/dev/null')
        uid = out.strip()
        if not uid:
            print(f'    SKIP: Cannot determine UID for {pkg}')
            continue
        
        await asyncio.sleep(3)
        
        # Force stop the app first
        await cmd(client, f'am force-stop {pkg}')
        await asyncio.sleep(2)
        
        # Check if we have backup data for this app
        src = f'/data/local/tmp/data/data/{pkg}'
        out = await cmd(client, f'ls {src}/ 2>/dev/null')
        if not out.strip():
            print(f'    SKIP: No backup data for {pkg}')
            continue
        
        print(f'    App UID: {uid}')
        print(f'    Backup contents: {out.strip()[:200]}')
        
        await asyncio.sleep(3)
        
        # Restore directories: shared_prefs, databases, files
        for subdir in ['shared_prefs', 'databases', 'files', 'cache', 'app_webview']:
            out = await cmd(client, f'ls {src}/{subdir}/ 2>/dev/null | head -5')
            if out.strip():
                # Copy data
                await cmd(client, f'cp -r {src}/{subdir} /data/data/{pkg}/ 2>/dev/null; chown -R {uid}:{uid} /data/data/{pkg}/{subdir} 2>/dev/null; echo OK')
                print(f'    Restored {subdir}')
                await asyncio.sleep(3)
        
        # Set correct permissions
        await cmd(client, f'chmod -R 750 /data/data/{pkg} 2>/dev/null; restorecon -R /data/data/{pkg} 2>/dev/null')
        print(f'    Permissions fixed for {pkg}')
        await asyncio.sleep(3)
    
    return True

async def take_screenshots(client):
    """Take screenshots of each app to verify."""
    print('\n[VERIFY] Taking verification screenshots...')
    
    os.makedirs('screenshots/clone_verify', exist_ok=True)
    ts = time.strftime('%Y%m%d_%H%M%S')
    
    APP_ACTIVITIES = {
        'com.whatsapp': 'com.whatsapp/.Main',
        'com.whatsapp.w4b': 'com.whatsapp.w4b/.Main',
        'com.google.android.apps.walletnfcrel': 'com.google.android.apps.walletnfcrel/.home.HomeActivity',
    }
    
    for pkg, name in TARGET_APPS.items():
        # Check if installed
        out = await cmd(client, f'pm path {pkg} 2>/dev/null')
        if not out.strip():
            print(f'  SKIP {name}: not installed')
            continue
        
        # Launch app
        activity = APP_ACTIVITIES.get(pkg, '')
        if activity:
            await cmd(client, f'am start -n {activity} 2>/dev/null')
        else:
            await cmd(client, f'monkey -p {pkg} -c android.intent.category.LAUNCHER 1 2>/dev/null')
        
        await asyncio.sleep(5)
        
        # Take screenshot via API
        try:
            r = await client.capture_screenshot(PAD)
            if r.get('code') == 200 and r.get('data'):
                url = r['data'] if isinstance(r['data'], str) else r['data'].get('url', '')
                if url:
                    print(f'  {name}: screenshot URL = {url[:100]}')
                else:
                    print(f'  {name}: screenshot taken (no URL in response)')
            else:
                print(f'  {name}: screenshot response = {r}')
        except Exception as e:
            # Fallback: screencap on device
            out = await cmd(client, f'screencap -p /sdcard/{pkg}_{ts}.png 2>&1; ls -la /sdcard/{pkg}_{ts}.png 2>&1')
            print(f'  {name}: screencap result = {out.strip()[:200]}')
        
        await asyncio.sleep(3)
        
        # Go back to home
        await cmd(client, 'input keyevent KEYCODE_HOME')
        await asyncio.sleep(2)
    
    # Also take a screenshot of the home screen
    try:
        r = await client.capture_screenshot(PAD)
        print(f'  Home screen: {r.get("code")}')
    except Exception as e:
        print(f'  Home screenshot error: {e}')
    
    return True

async def main():
    from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
    client = VMOSCloudClient(
        ak='YOUR_VMOS_AK_HERE',
        sk='YOUR_VMOS_SK_HERE',
        base_url='https://api.vmoscloud.com'
    )
    client._log_requests = False
    
    # Phase 1: Boot device
    print('='*60)
    print('PHASE 1: BOOT DEVICE')
    print('='*60)
    
    # Check current status
    r = await client.instance_list(page=1, rows=5)
    devs = r.get('data', {}).get('pageData', [])
    current_status = None
    for d in devs:
        if d['padCode'] == PAD:
            current_status = d['padStatus']
            break
    
    print(f'Current padStatus: {current_status}')
    
    if current_status == 14:
        print('Device is stopped. Starting...')
        await client.instance_restart([PAD])
        await asyncio.sleep(5)
    
    if current_status != 10:
        ok = await wait_for_boot(client, max_wait=300)
        if not ok:
            print('FATAL: Cannot boot device')
            return
    
    # Additional wait for services to stabilize  
    print('[BOOT] Waiting 15s for services to stabilize...')
    await asyncio.sleep(15)
    
    # Verify device is responsive
    for retry in range(5):
        out = await cmd(client, 'echo ALIVE && getprop ro.product.model')
        if 'ALIVE' in out:
            print(f'[BOOT] Device confirmed alive: {out.strip()}')
            break
        print(f'[BOOT] Retry {retry+1}/5...')
        await asyncio.sleep(5)
    else:
        print('FATAL: Device not responding after boot')
        return
    
    await asyncio.sleep(3)
    
    # Phase 2: Check accounts
    print('\n' + '='*60)
    print('PHASE 2: CHECK ACCOUNTS')
    print('='*60)
    has_accounts = await check_accounts(client)
    
    await asyncio.sleep(3)
    
    # Phase 3: Install apps
    print('\n' + '='*60)
    print('PHASE 3: INSTALL APPS')
    print('='*60)
    
    # Check what's installed
    out = await cmd(client, 'pm list packages 2>/dev/null | grep -E "whatsapp|walletnfcrel"')
    print(f'Currently installed targets: {out.strip()}')
    
    await asyncio.sleep(3)
    
    # Try installing via API
    tasks = await install_apps_via_api(client)
    
    if tasks:
        print(f'  Waiting for installs (tasks: {tasks})...')
        await asyncio.sleep(30)
        for tid in tasks:
            r = await client.task_detail([tid])
            print(f'  Task {tid}: {r.get("data", [{}])[0].get("taskStatus") if r.get("data") else "?"}')
            await asyncio.sleep(3)
    
    await asyncio.sleep(3)
    
    # Phase 4: Restore app data
    print('\n' + '='*60)
    print('PHASE 4: RESTORE APP DATA')
    print('='*60)
    await restore_app_data(client)
    
    # Phase 5: Verification screenshots
    print('\n' + '='*60)
    print('PHASE 5: VERIFICATION SCREENSHOTS')
    print('='*60)
    await take_screenshots(client)
    
    print('\n' + '='*60)
    print('RESTORE COMPLETE')
    print('='*60)

if __name__ == '__main__':
    asyncio.run(main())
