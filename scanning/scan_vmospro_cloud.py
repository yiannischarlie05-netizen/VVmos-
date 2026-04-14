import asyncio
from vmos_titan.core.vmos_cloud_module import VMOSCloudBridge

async def main():
    bridge = VMOSCloudBridge()
    instances = await bridge.list_instances()
    print(f"Found {len(instances)} VMOSPro cloud devices:")
    for inst in instances:
        print(f"- {inst.pad_code} | {inst.device_name} | {inst.status} | {inst.device_ip}")

if __name__ == "__main__":
    asyncio.run(main())
