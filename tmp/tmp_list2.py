import asyncio, os, sys
os.chdir("/root/vmos-titan-unified")

# Load .env manually
with open("/root/vmos-titan-unified/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/core")
sys.path.insert(0, "/root/vmos-titan-unified/core")
sys.path.insert(0, "/root/vmos-titan-unified/server")

from vmos_cloud_api import VMOSCloudClient

async def main():
    c = VMOSCloudClient()
    print(f"AK: {os.environ.get('VMOS_CLOUD_AK', 'NOT SET')[:8]}...")
    r = await c.instance_list(page=1, page_size=50)
    print(f"API response code: {r.get('code')}")
    print(f"API msg: {r.get('msg')}")
    devices = r.get("data", {}).get("list", [])
    print(f"Total devices: {len(devices)}")
    for inst in devices:
        pc = inst.get("padCode", "")
        st = inst.get("padStatus", "?")
        name = inst.get("padName", "")
        print(f"  {pc}: status={st} name={name}")

asyncio.run(main())
