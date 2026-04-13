#!/usr/bin/env python3
import os, asyncio, json
from pathlib import Path
from vmos_cloud_api import VMOSCloudClient

AK=os.getenv('VMOS_CLOUD_AK','BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi')
SK=os.getenv('VMOS_CLOUD_SK','Q2SgcSwEfuwoedY0cijp6Mce')
PAD=os.getenv('VMOS_PAD_CODE','ACP251008GUOEEHB')
assert AK and SK and PAD
client=VMOSCloudClient(ak=AK, sk=SK)

async def run_cmd(pad, cmd, timeout=20):
    r = await client.sync_cmd(pad, cmd, timeout_sec=timeout)
    return r

async def get_neighbors(pad):
    r = await run_cmd(pad, 'ip neigh show')
    raw = r.get('data',[{}])[0].get('errorMsg','')
    addrs=[]
    for line in raw.splitlines():
        parts=line.split()
        if len(parts)>=1 and parts[0].count('.')==3:
            addrs.append(parts[0])
    return list(dict.fromkeys(addrs))

async def scan_neighbor(pad, ip):
    ports=[22,80,443,5555,8888,8000,8080]
    result=[]
    for p in ports:
        c = f"(echo > /dev/tcp/{ip}/{p}) >/dev/null 2>&1 && echo OPEN || echo CLOSED"
        r = await run_cmd(pad,c,timeout=10)
        out = r.get('data',[{}])[0].get('errorMsg','').strip()
        result.append({'port':p,'status':out})
    return result

async def probe_escape(pad):
    tests=[
        'id',
        'cat /proc/self/cgroup',
        'readlink /proc/1/root',
        'cat /proc/1/mounts | head -n 20',
        'getenforce 2>/dev/null || echo no-selinux',
        'cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null || echo no-yama',
    ]
    out=[]
    for t in tests:
        r = await run_cmd(pad,t,timeout=15)
        out.append({'test':t,'out':r.get('data',[{}])[0].get('errorMsg','')})
    return out

async def main():
    res={'pad':PAD,'adb':None,'probe':None,'neighbors':[]}
    try:
        res['adb']=await client.get_adb_info(PAD,enable=True)
    except Exception as e:
        res['adb']={'error':str(e)}
    res['probe']=await probe_escape(PAD)
    neighbors=await get_neighbors(PAD)
    for n in neighbors:
        if n.startswith('10.9.43.'):
            res['neighbors'].append({'ip':n,'scan':await scan_neighbor(PAD,n)})
    with open('scan_results.json','w') as f:
        json.dump(res,f,indent=2)
    print('done')

if __name__ == '__main__':
    asyncio.run(main())
