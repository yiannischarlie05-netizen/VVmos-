import asyncio, os, sys
os.chdir("/root/vmos-titan-unified")
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
    # Use correct parameter: rows (not page_size)
    r = await c.instance_list(page=1, rows=50)
    print(f"API code={r.get('code')} msg={r.get('msg')}")
    data = r.get("data", {})
    total = data.get("total", 0)
    print(f"Total in account: {total}")
    devices = data.get("list", [])
    print(f"Devices on page: {len(devices)}")
    for inst in devices:
        pc = inst.get("padCode", "")
        st = inst.get("padStatus", "?")
        name = inst.get("padName", "")
        print(f"  {pc}: status={st} name={name}")

asyncio.run(main())
