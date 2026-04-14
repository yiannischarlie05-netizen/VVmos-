#!/usr/bin/env python3
import asyncio, sys
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

async def main():
    c = VMOSCloudClient(ak=AK, sk=SK, base_url='https://api.vmoscloud.com')
    
    print('=== Checking account DB files ===')
    out = await amd(c, 'ls -la /data/system_ce/0/accounts_ce.db /data/system_de/0/accounts_de.db 2>&1', w=10)
    print(out.strip())

    print('\n=== Checking dumpsys accounts ===')
    out2 = await amd(c, 'dumpsys account 2>/dev/null | head -30', w=10)
    print(out2.strip()[:500])

asyncio.run(main())
