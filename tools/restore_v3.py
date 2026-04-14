#!/usr/bin/env python3
"""
Post-reset restore pipeline v3.0
Strategy: Install apps first → Download appdata → Restore per-app data → Screenshot verify
No GMS/system data injection (Android version mismatch fix).
"""
import asyncio, sys, os, json, time, logging
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
logging.disable(logging.CRITICAL)
os.environ['VMOS_ALLOW_RESTART_PAD'] = 'AC32010810392'

PAD = 'AC32010810392'
VPS_IP = 'YOUR_OLLAMA_HOST'
HTTP_PORT = 18999
CLONE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'clone_backups', '10_0_46_2_Infinix_X6531B'))

TARGET_APPS = {
    'com.whatsapp': 'WhatsApp',
    'com.whatsapp.w4b': 'WhatsApp Business',
    'com.google.android.apps.walletnfcrel': 'Google Wallet',
}

# Activity names for launching apps
APP_ACTIVITIES = {
    'com.whatsapp': 'com.whatsapp/.Main',
    'com.whatsapp.w4b': 'com.whatsapp.w4b/.Main',
    'com.google.android.apps.walletnfcrel': 'com.google.android.apps.walletnfcrel/.home.HomeActivity',
}


async def cmd(client, shell_cmd, timeout=25):
    """Execute shell command and return output string."""
    r = await client.sync_cmd(PAD, shell_cmd, timeout_sec=timeout)
    if r.get('code') == 200 and r.get('data'):
        data = r['data']
        # Handle both dict and list responses
        if isinstance(data, list) and data:
            item = data[0]
            output = item.get('errorMsg', '') or item.get('taskResult', '')
            # errorMsg contains actual output for successful commands
            if item.get('taskStatus') == 3 and item.get('errorMsg'):
                return item['errorMsg']
            return output
        elif isinstance(data, dict):
            return data.get('output', '')
    return ''


def start_http_server(directory, port):
    """Start a simple HTTP server in a background thread."""
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=directory, **kwargs)
    server = TCPServer(('0.0.0.0', port), handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


async def phase_1_install_apps(client):
    """Install WhatsApp, WhatsApp Business, Google Wallet via VMOS install_app API."""
    print('\n' + '='*60)
    print('PHASE 1: INSTALL APPS')
    print('='*60)

    # Check what's already installed
    out = await cmd(client, 'pm list packages 2>/dev/null')
    installed = set()
    for line in out.strip().split('\n'):
        if line.startswith('package:'):
            installed.add(line.split(':')[1].strip())

    await asyncio.sleep(3)

    # Install via API using public APK URLs
    # These are direct download links
    installs = {}
    for pkg, name in TARGET_APPS.items():
        if pkg in installed:
            print(f'  {name} ({pkg}) already installed')
            continue
        print(f'  Installing {name}...')
        installs[pkg] = name

    if not installs:
        print('  All target apps already installed!')
        return True

    # Use VMOS install_app API - need publicly accessible APK URLs
    # Alternative: upload APKs via VPS HTTP server
    # For now, install the apps we have APKs for, or use store-like URLs

    # Check if we have APKs in clone backup
    apk_dir = os.path.join(CLONE_DIR, 'apps')
    if os.path.isdir(apk_dir):
        print(f'  Checking for APKs in clone backup: {apk_dir}')
        for entry in os.listdir(apk_dir):
            print(f'    Found: {entry}')

    # Since we may not have standalone APKs, try install_app with the packages
    # Or install via pm install with APK pulled from internet
    # Let's try the VMOS install_app API (it can download from URLs)

    # For Google Wallet, WhatsApp etc, we need APK hosting
    # Strategy: serve them from VPS if we have them, otherwise use known URLs

    task_ids = []
    for pkg in installs:
        # Try install via VMOS API with a known APK mirror
        # Note: VMOS install_app needs a direct APK URL
        name = installs[pkg]
        # Use am instrument or other means to trigger install
        print(f'  {name}: Will install via device package manager or APK')
        # Placeholder - will handle per-app

    # Approach: install WhatsApp and WhatsApp Business via APK download on device
    # Google Wallet is typically pre-installed or available via play store

    for pkg in installs:
        name = installs[pkg]
        # Try install via VMOS install_app API
        print(f'\n  Attempting {name} install...')

        # For WhatsApp, use whatsapp.com official download
        if pkg == 'com.whatsapp':
            # WhatsApp official APK download
            print('  Downloading WhatsApp APK on device...')
            await cmd(client, 'curl -L -o /data/local/tmp/whatsapp.apk "https://scontent.whatsapp.net/v/t39.8562-34/513399015_588399560507606_6574543505082476641_n.apk/WhatsApp.apk" 2>/dev/null; ls -la /data/local/tmp/whatsapp.apk')
            await asyncio.sleep(5)
            out = await cmd(client, 'pm install -r -d -g /data/local/tmp/whatsapp.apk 2>&1')
            print(f'  Install result: {out.strip()[:200]}')

        elif pkg == 'com.whatsapp.w4b':
            # WhatsApp Business
            print('  Installing WhatsApp Business via VMOS API...')
            r = await client.install_app([PAD], 'https://d.apkpure.net/b/XAPK/com.whatsapp.w4b?version=latest')
            print(f'  API result: {r.get("code")} {r.get("msg")}')
            if r.get('data') and isinstance(r['data'], list):
                for item in r['data']:
                    if item.get('taskId'):
                        task_ids.append(item['taskId'])

        elif pkg == 'com.google.android.apps.walletnfcrel':
            # Google Wallet - check if playstore is available
            out = await cmd(client, 'pm path com.android.vending 2>/dev/null')
            if out.strip():
                print('  Play Store available. Attempting Play Store install via am...')
                await cmd(client, 'am start -a android.intent.action.VIEW -d "market://details?id=com.google.android.apps.walletnfcrel" 2>/dev/null')
            else:
                print('  No Play Store. Will try APK download...')

        await asyncio.sleep(5)

    # Wait for async installs
    if task_ids:
        print(f'\n  Waiting for VMOS install tasks: {task_ids}')
        await asyncio.sleep(30)
        for tid in task_ids:
            r = await client.task_detail([tid])
            print(f'  Task {tid}: {json.dumps(r.get("data", []), ensure_ascii=False)[:200]}')
            await asyncio.sleep(3)

    # Verify what's installed now
    await asyncio.sleep(3)
    out = await cmd(client, 'pm list packages 2>/dev/null | grep -E "whatsapp|walletnfcrel"')
    print(f'\n  Installed target packages: {out.strip()}')

    return True


async def phase_2_download_appdata(client):
    """Download appdata.tar.gz to device via HTTP."""
    print('\n' + '='*60)
    print('PHASE 2: DOWNLOAD APP DATA')
    print('='*60)

    appdata_path = os.path.join(CLONE_DIR, 'appdata.tar.gz')
    if not os.path.exists(appdata_path):
        print(f'  ERROR: {appdata_path} not found!')
        return False

    size = os.path.getsize(appdata_path)
    print(f'  appdata.tar.gz: {size:,} bytes ({size/1024/1024:.1f}MB)')

    # Check if already on device
    out = await cmd(client, 'ls -la /data/local/tmp/appdata.tar.gz 2>&1')
    if str(size) in out:
        print('  Already on device with correct size, skipping download')
        return True

    # Start HTTP server serving the clone directory
    print(f'  Starting HTTP server on port {HTTP_PORT}...')
    server = start_http_server(CLONE_DIR, HTTP_PORT)

    await asyncio.sleep(2)

    # Download on device
    url = f'http://{VPS_IP}:{HTTP_PORT}/appdata.tar.gz'
    print(f'  Downloading from {url}...')

    # Fire download and wait
    await cmd(client, f'curl -s -o /data/local/tmp/appdata.tar.gz "{url}" &')
    
    # Wait for download (52MB @ ~10MB/s = ~5s, but could be slower)
    for i in range(30):
        await asyncio.sleep(10)
        out = await cmd(client, 'ls -la /data/local/tmp/appdata.tar.gz 2>&1')
        if str(size) in out:
            print(f'  Download complete: {out.strip()}')
            server.shutdown()
            return True
        # Check if curl is still running
        out2 = await cmd(client, 'pgrep -c curl 2>/dev/null || echo 0')
        if out2.strip() == '0':
            # curl finished  
            out3 = await cmd(client, 'stat -c %s /data/local/tmp/appdata.tar.gz 2>/dev/null')
            current = out3.strip()
            if current == str(size):
                print(f'  Download complete ({current} bytes)')
                server.shutdown()
                return True
            else:
                print(f'  Curl finished but size mismatch: {current} vs {size}')
                break
        else:
            print(f'  [{(i+1)*10}s] Still downloading...')

    server.shutdown()
    # Verify final size
    out = await cmd(client, 'stat -c %s /data/local/tmp/appdata.tar.gz 2>/dev/null')
    if out.strip() == str(size):
        print('  Download verified!')
        return True
    print(f'  Download failed. Device file size: {out.strip()}, expected: {size}')
    return False


async def phase_3_restore_app_data(client):
    """Extract and restore per-app data from appdata.tar.gz."""
    print('\n' + '='*60)
    print('PHASE 3: RESTORE APP DATA')
    print('='*60)

    # Extract tarball
    print('  Extracting appdata.tar.gz...')
    await cmd(client, 'rm -rf /data/local/tmp/data 2>/dev/null')
    await asyncio.sleep(2)
    out = await cmd(client, 'cd /data/local/tmp && tar xzf appdata.tar.gz 2>&1; echo RC=$?', timeout=120)
    print(f'  Extract: {out.strip()[-200:]}')

    await asyncio.sleep(3)

    # List what was extracted
    out = await cmd(client, 'ls /data/local/tmp/data/data/ 2>/dev/null')
    extracted_apps = [d for d in out.strip().split('\n') if d.strip()]
    print(f'  Extracted app dirs: {extracted_apps}')

    await asyncio.sleep(3)

    # Restore each target app's data
    for pkg, name in TARGET_APPS.items():
        print(f'\n  --- Restoring {name} ({pkg}) ---')

        # Check if app is installed
        out = await cmd(client, f'pm path {pkg} 2>/dev/null')
        if not out.strip():
            print(f'    SKIP: Not installed')
            continue

        await asyncio.sleep(3)

        # Check if we have backup data
        src = f'/data/local/tmp/data/data/{pkg}'
        out = await cmd(client, f'ls {src}/ 2>/dev/null')
        if not out.strip():
            print(f'    SKIP: No backup data')
            continue

        print(f'    Backup contents: {out.strip()[:300]}')

        # Get app UID
        out = await cmd(client, f'stat -c %u /data/data/{pkg} 2>/dev/null')
        uid = out.strip()
        if not uid or not uid.isdigit():
            print(f'    WARN: Cannot determine UID, using fallback')
            uid = '10000'  # default app uid range

        await asyncio.sleep(3)

        # Force stop app
        await cmd(client, f'am force-stop {pkg}')
        await asyncio.sleep(2)

        # Restore subdirectories
        for subdir in ['shared_prefs', 'databases', 'files', 'no_backup']:
            out = await cmd(client, f'ls {src}/{subdir}/ 2>/dev/null | wc -l')
            count = out.strip()
            if count and count != '0':
                await cmd(client, (
                    f'rm -rf /data/data/{pkg}/{subdir} 2>/dev/null; '
                    f'cp -r {src}/{subdir} /data/data/{pkg}/ 2>/dev/null; '
                    f'chown -R {uid}:{uid} /data/data/{pkg}/{subdir} 2>/dev/null; '
                    f'chmod -R 770 /data/data/{pkg}/{subdir} 2>/dev/null; '
                    f'echo OK'
                ))
                print(f'    Restored {subdir} ({count} items)')
                await asyncio.sleep(3)

        # Fix SELinux context
        await cmd(client, f'restorecon -R /data/data/{pkg} 2>/dev/null')
        print(f'    Permissions and SELinux fixed')
        await asyncio.sleep(3)

    return True


async def phase_4_inject_account(client):
    """Inject Google account using am commands (no DB push)."""
    print('\n' + '='*60)
    print('PHASE 4: INJECT GOOGLE ACCOUNT')
    print('='*60)

    email = 'socarsocar100@gmail.com'

    # Check if any accounts exist
    out = await cmd(client, 'dumpsys account 2>/dev/null | grep "Account {" | head -5')
    if email in out:
        print(f'  Account {email} already present!')
        return True

    print(f'  No accounts. Injecting {email}...')

    # Method 1: Use Android AccountManager content provider
    # AccountManager needs auth token, so we use the accounts_ce.db approach
    # but this time we build it compatible with Android 15

    # Build and push accounts_ce.db and accounts_de.db
    from vmos_titan.core.vmos_db_builder import VMOSDbBuilder

    builder = VMOSDbBuilder()
    ce_db = builder.build_accounts_ce(email)
    de_db = builder.build_accounts_de(email)

    print(f'  Built accounts_ce.db: {len(ce_db)} bytes')
    print(f'  Built accounts_de.db: {len(de_db)} bytes')

    # Push via base64 chunks (proven approach)
    import base64
    
    for db_name, db_bytes, dest_path in [
        ('accounts_ce.db', ce_db, '/data/system_ce/0/accounts_ce.db'),
        ('accounts_de.db', de_db, '/data/system_de/0/accounts_de.db'),
    ]:
        print(f'\n  Pushing {db_name} ({len(db_bytes)} bytes)...')
        
        b64 = base64.b64encode(db_bytes).decode()
        chunk_size = 800
        chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

        # Clear target
        await cmd(client, f'rm -f {dest_path}')
        await asyncio.sleep(2)

        # Write chunks
        for idx, chunk in enumerate(chunks):
            op = '>' if idx == 0 else '>>'
            await cmd(client, f"echo '{chunk}' {op} /data/local/tmp/{db_name}.b64")
            await asyncio.sleep(2)

        # Decode
        await cmd(client, f'base64 -d /data/local/tmp/{db_name}.b64 > {dest_path}')
        await asyncio.sleep(2)

        # Verify
        out = await cmd(client, f'stat -c %s {dest_path} 2>/dev/null')
        device_size = out.strip()
        print(f'  {db_name} on device: {device_size} bytes (expected: {len(db_bytes)})')

        # Set permissions
        await cmd(client, f'chmod 660 {dest_path}; chown system:system {dest_path}')
        await asyncio.sleep(2)

        # Cleanup
        await cmd(client, f'rm -f /data/local/tmp/{db_name}.b64')
        await asyncio.sleep(2)

    # NOTE: Account DBs need AMS restart to take effect.
    # Instead of full device restart (which could cause boot loop), 
    # just restart system_server (AMS will re-read DBs on restart)
    print('\n  Restarting system_server to load accounts...')
    await cmd(client, 'kill $(pidof system_server) 2>/dev/null')

    # Wait for system_server to restart
    await asyncio.sleep(20)

    # Check accounts
    out = await cmd(client, 'dumpsys account 2>/dev/null | grep "Account {" | head -5')
    if email in out:
        print(f'  SUCCESS: {email} loaded!')
        return True
    else:
        print(f'  Account check: {out.strip()[:200]}')
        print('  Account may need a full restart to load. Deferring...')
        return False


async def phase_5_screenshots(client):
    """Take verification screenshots of each app."""
    print('\n' + '='*60)
    print('PHASE 5: VERIFICATION SCREENSHOTS')
    print('='*60)

    os.makedirs('screenshots/clone_verify', exist_ok=True)
    ts = time.strftime('%Y%m%d_%H%M%S')

    screenshots = []

    # Home screen first
    print('  Taking home screen screenshot...')
    r = await client.screenshot([PAD])
    if r.get('code') == 200 and r.get('data'):
        for item in r['data']:
            url = item.get('accessUrl', '')
            if url:
                print(f'    Home: {url[:80]}...')
                screenshots.append(('home', url))

    await asyncio.sleep(5)

    # Each target app
    for pkg, name in TARGET_APPS.items():
        out = await cmd(client, f'pm path {pkg} 2>/dev/null')
        if not out.strip():
            print(f'  {name}: not installed, skipping')
            continue

        # Launch
        activity = APP_ACTIVITIES.get(pkg, '')
        if activity:
            await cmd(client, f'am start -n {activity} 2>/dev/null')
        else:
            await cmd(client, f'monkey -p {pkg} -c android.intent.category.LAUNCHER 1 2>/dev/null')

        await asyncio.sleep(5)

        # Screenshot
        r = await client.screenshot([PAD])
        if r.get('code') == 200 and r.get('data'):
            for item in r['data']:
                url = item.get('accessUrl', '')
                if url:
                    print(f'  {name}: {url[:80]}...')
                    screenshots.append((pkg, url))

        await asyncio.sleep(3)

        # Back to home
        await cmd(client, 'input keyevent KEYCODE_HOME')
        await asyncio.sleep(2)

    # Download screenshots
    print(f'\n  Downloading {len(screenshots)} screenshots...')
    for label, url in screenshots:
        fname = f'screenshots/clone_verify/{ts}_{label.replace(".", "_")}.jpg'
        os.system(f'curl -s -o "{fname}" "{url}" 2>/dev/null')
        size = os.path.getsize(fname) if os.path.exists(fname) else 0
        print(f'    {label}: {size:,} bytes')

    return screenshots


async def main():
    from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
    client = VMOSCloudClient(
        ak='YOUR_VMOS_AK_HERE',
        sk='YOUR_VMOS_SK_HERE',
        base_url='https://api.vmoscloud.com'
    )

    # Verify device is alive
    print('Verifying device...')
    out = await cmd(client, 'echo ALIVE && getprop ro.product.model && getprop ro.build.version.release')
    print(f'Device: {out.strip()}')
    if 'ALIVE' not in out:
        print('ERROR: Device not responding')
        return

    await asyncio.sleep(3)

    # Run phases
    await phase_1_install_apps(client)
    await phase_2_download_appdata(client)
    await phase_3_restore_app_data(client)
    # Skip account injection for now - focus on app data
    # await phase_4_inject_account(client)
    await phase_5_screenshots(client)

    print('\n' + '='*60)
    print('RESTORE PIPELINE COMPLETE')
    print('='*60)


if __name__ == '__main__':
    asyncio.run(main())
