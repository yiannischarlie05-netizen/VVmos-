#!/usr/bin/env python3
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
    
    print('=== DB Schema Check ===')
    out = await amd(c, 'sqlite3 /data/system_ce/0/accounts_ce.db ".tables" 2>/dev/null || echo NO_DB', w=10)
    print('CE tables:', (out or '').strip())
    
    out = await amd(c, 'sqlite3 /data/system_ce/0/accounts_ce.db ".schema" 2>/dev/null | head -20', w=10)
    print('CE schema:', (out or '').strip()[:400])
    
    print('\n=== Package state ===')
    out = await amd(c, 'pm list packages | grep -E "whatsapp|wallet|gms|vending"', w=8)
    print((out or '').strip())
    
    print('\n=== Device boots OK? ===')
    out = await amd(c, 'echo ALIVE && getprop ro.product.model', w=8)
    print((out or '').strip())

asyncio.run(main())
