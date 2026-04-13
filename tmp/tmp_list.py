import asyncio
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

async def main():
    c = VMOSCloudClient()
    r = await c.instance_list(page=1, page_size=50)
    devices = r.get("data", {}).get("list", [])
    print(f"Total devices: {len(devices)}")
    for inst in devices:
        pc = inst.get("padCode", "")
        st = inst.get("padStatus", "?")
        print(f"  {pc}: status={st}")

asyncio.run(main())
