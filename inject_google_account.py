#!/usr/bin/env python3
"""Inject Google account via AccountManager content provider"""
import asyncio, sys
sys.path.insert(0, '/home/debian/Downloads/vmos-titan-unified')
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = 'BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi'
SK = 'Q2SgcSwEfuwoedY0cijp6Mce'
PAD = 'AC32010810392'
EMAIL = 'socarsocar100@gmail.com'

async def amd(c, cmd, w=10):
    r = await c.async_adb_cmd([PAD], cmd)
    if not r or not r.get('data'): return ''
    t = r['data'][0].get('taskId')
    if not t: return ''
    await asyncio.sleep(w)
    r2 = await c.task_detail([t])
    if not r2 or not r2.get('data'): return ''
    d = r2['data'][0]
    return d.get('taskResult','') or d.get('errorMsg','') or ''

async def main():
    c = VMOSCloudClient(ak=AK, sk=SK, base_url='https://api.vmoscloud.com')
    
    # Step 1: Check current accounts
    print('=== Current accounts ===')
    out = await amd(c, 'dumpsys account 2>/dev/null | head -15', w=10)
    print((out or '').strip()[:300])
    
    # Step 2: Force stop GMS to allow DB modification
    print('\n=== Force-stopping GMS ===')
    await amd(c, 'am force-stop com.google.android.gms', w=5)
    await amd(c, 'am force-stop com.android.vending', w=5)
    
    # Step 3: Try content insert AccountManager approach
    print('\n=== Content insert approach ===')
    out = await amd(c, f"content insert --uri content://com.android.account/accounts --bind name:s:{EMAIL} --bind type:s:com.google 2>&1; echo CMD_DONE", w=12)
    print('Content insert:', (out or '').strip()[:200])
    
    # Step 4: Try via SQLite directly on accounts_ce.db
    print('\n=== Direct SQLite insert ===')
    # First check if table exists
    out = await amd(c, 'sqlite3 /data/system_ce/0/accounts_ce.db ".tables" 2>/dev/null', w=10)
    print('Tables:', (out or '').strip())
    
    if out and 'accounts' in out:
        # Insert account
        out = await amd(c, f"sqlite3 /data/system_ce/0/accounts_ce.db \"INSERT OR IGNORE INTO accounts (name, type) VALUES ('{EMAIL}', 'com.google');\" 2>/dev/null && echo INSERT_OK", w=10)
        print('SQLite insert:', (out or '').strip())
    
    # Step 5: Broadcast account change
    print('\n=== Broadcasting account change ===')
    out = await amd(c, 'am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null; echo DONE', w=8)
    print('Broadcast:', (out or '').strip()[:100])
    
    # Step 6: Check result
    await asyncio.sleep(5)
    out = await amd(c, 'dumpsys account 2>/dev/null | grep -E "Account|socar|gmail" | head -10', w=10)
    print('\n=== Account check ===')
    print((out or '').strip()[:300])

asyncio.run(main())
