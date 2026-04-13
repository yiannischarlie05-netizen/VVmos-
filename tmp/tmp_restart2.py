import asyncio, os, sys
os.chdir("/root/vmos-titan-unified")
with open("/root/vmos-titan-unified/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()
sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/core")
from vmos_cloud_api import VMOSCloudClient

PAD = "APP5B54EI0Z1EOEA"

async def main():
    c = VMOSCloudClient()
    
    # Try instance_restart again (proper API endpoint)
    print("[1] Attempting restart via API...")
    r = await c.instance_restart([PAD])
    print(f"  Restart response: code={r.get('code')} msg={r.get('msg')}")
    if r.get("data"):
        for d in r["data"]:
            print(f"  taskId={d.get('taskId')}, taskStatus={d.get('taskStatus')}, vmStatus={d.get('vmStatus')}")
    
    # Wait longer this time (up to 5 min)
    print("[2] Waiting for recovery (up to 5 min)...")
    for i in range(60):
        await asyncio.sleep(5)
        r = await c._post("/vcpcloud/api/padApi/infos", {"page": 1, "rows": 10})
        for inst in r.get("data", {}).get("pageData", []):
            if inst.get("padCode") == PAD:
                st = inst.get("padStatus")
                if i % 6 == 0 or st == 10:
                    print(f"  [{(i+1)*5}s] status={st}")
                if st == 10:
                    print(f"  RECOVERED at {(i+1)*5}s!")
                    return
                if st == 11:
                    print(f"  BRICKED (status=11) — DO NOT restart again!")
                    return
    print("  Did not recover within 5 minutes — may need reset")

asyncio.run(main())
