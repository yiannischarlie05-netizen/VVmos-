#!/usr/bin/env python3
"""Full account injection + device restart + verify"""
import asyncio, sys, os, base64, httpx, time
sys.path.insert(0, '/home/debian/Downloads/vmos-titan-unified')
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = 'YOUR_VMOS_AK_HERE'
SK = 'YOUR_VMOS_SK_HERE'
PAD = 'AC32010810392'

async def amd(c, cmd, w=10):
    r = await c.async_adb_cmd([PAD], cmd)
    if not r or not r.get('data'): return ''
    t = r['data'][0].get('taskId')
    if not t: return ''
    await asyncio.sleep(w)
    r2 = await c.task_detail([t])
    if not r2 or not r2.get('data'): return ''
    d = r2['data'][0]
    return d.get('taskResult','') or d.get('errorMsg','')

async def take_screenshot(c, label):
    os.makedirs('screenshots', exist_ok=True)
    r = await c.screenshot([PAD])
    url = r['data'][0]['accessUrl']
    async with httpx.AsyncClient(verify=False, timeout=30) as hc:
        resp = await hc.get(url)
        if resp.status_code == 200:
            path = f'screenshots/{label}_{int(time.time())}.jpg'
            with open(path, 'wb') as f:
                f.write(resp.content)
            print(f'  Saved: {path} ({len(resp.content)} bytes)')
            return path

async def wait_running(c, max_wait=120):
    for i in range(max_wait // 5):
        r = await c.instance_list(page=1, rows=50)
        if r.get('code') == 200:
            for inst in r.get('data', {}).get('pageData', []):
                if inst.get('padCode') == PAD and inst.get('padStatus') == 10:
                    return True
        await asyncio.sleep(5)
    return False

async def main():
    os.environ['VMOS_ALLOW_RESTART'] = '1'
    c = VMOSCloudClient(ak=AK, sk=SK, base_url='https://api.vmoscloud.com')
    
    # Check DB content
    print('=== Checking accounts_ce.db content ===')
    out = await amd(c, 'sqlite3 /data/system_ce/0/accounts_ce.db "SELECT name, type FROM accounts LIMIT 5;" 2>/dev/null', w=10)
    print(f'accounts_ce content: {(out or "").strip()}')
    
    # Also check accounts_de.db
    out = await amd(c, 'sqlite3 /data/system_de/0/accounts_de.db "SELECT name, type FROM accounts LIMIT 5;" 2>/dev/null', w=10)
    print(f'accounts_de content: {(out or "").strip()}')
    
    # Restart device to reload account manager
    print('\n=== Restarting device to reload accounts ===')
    r = await c.instance_restart([PAD])
    print(f'Restart: {r}')
    
    print('Waiting for device to come back online...')
    await asyncio.sleep(30)
    running = await wait_running(c, max_wait=180)
    print(f'Device running: {running}')
    
    if not running:
        print('Device not running yet, waiting 30 more seconds...')
        await asyncio.sleep(30)
    
    # Verify accounts after restart
    print('\n=== Verifying accounts after restart ===')
    await asyncio.sleep(15)  # Let Android boot completely
    
    out = await amd(c, 'dumpsys account 2>/dev/null | head -20', w=12)
    print(out.strip()[:400])
    
    # Take screenshot of home screen after restart
    print('\n=== Taking post-restart screenshots ===')
    await asyncio.sleep(5)
    await take_screenshot(c, 'post_restart_home')
    
    # Launch Google Wallet
    out = await amd(c, 'monkey -p com.google.android.apps.walletnfcrel -c android.intent.category.LAUNCHER 1 2>&1', w=5)
    print('Wallet launch:', out.strip()[:100])
    await asyncio.sleep(8)
    await take_screenshot(c, 'wallet_post_restart')
    
    # Launch WhatsApp
    await amd(c, 'monkey -p com.whatsapp -c android.intent.category.LAUNCHER 1 2>&1', w=5)
    await asyncio.sleep(6)
    await take_screenshot(c, 'whatsapp_post_restart')

asyncio.run(main())
