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
    
    # Try stopping first, then starting
    print("[1] Stopping device...")
    r = await c._post("/vcpcloud/api/padApi/stop", {"padCodes": [PAD]})
    print(f"  Stop: {r.get('code')} {r.get('msg')}")
    
    await asyncio.sleep(10)
    
    # Check status
    r = await c._post("/vcpcloud/api/padApi/infos", {"page": 1, "rows": 10})
    for inst in r.get("data", {}).get("pageData", []):
        if inst.get("padCode") == PAD:
            print(f"  Status after stop: {inst.get('padStatus')}")
    
    print("[2] Starting device...")
    r = await c._post("/vcpcloud/api/padApi/start", {"padCodes": [PAD]})
    print(f"  Start: {r.get('code')} {r.get('msg')}")
    
    # Wait for running
    for i in range(40):
        await asyncio.sleep(5)
        r = await c._post("/vcpcloud/api/padApi/infos", {"page": 1, "rows": 10})
        for inst in r.get("data", {}).get("pageData", []):
            if inst.get("padCode") == PAD:
                st = inst.get("padStatus")
                if i % 3 == 0:
                    print(f"  [{(i+1)*5}s] status={st}")
                if st == 10:
                    print(f"  RUNNING at {(i+1)*5}s!")
                    return
    
    print("  Still not running after 200s")

asyncio.run(main())
