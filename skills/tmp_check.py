import asyncio
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

PAD = "APP5B54EI0Z1EOEA"

async def main():
    c = VMOSCloudClient()
    r = await c.instance_list(page=1, page_size=10)
    for inst in r.get("data", {}).get("list", []):
        if inst.get("padCode") == PAD:
            print(f"Device status: {inst.get('padStatus')}")
            return
    print("Device not found")

asyncio.run(main())
