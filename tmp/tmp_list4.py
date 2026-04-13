import asyncio, os, sys, json
os.chdir("/root/vmos-titan-unified")
with open("/root/vmos-titan-unified/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()
sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/core")
from vmos_cloud_api import VMOSCloudClient

async def main():
    c = VMOSCloudClient()
    # Try various page sizes and filters
    for rows in [10, 50, 100]:
        r = await c.instance_list(page=1, rows=rows)
        data = r.get("data", {})
        items = data.get("list", [])
        print(f"rows={rows}: total={data.get('total')}, list_len={len(items)}")
        if items:
            for i in items:
                print(f"  {i.get('padCode')}: status={i.get('padStatus')}")
    
    # Also try the raw API to see full response
    print("\n--- Raw API response ---")
    r = await c._post("/vcpcloud/api/padApi/infos", {"page": 1, "rows": 100})
    print(json.dumps(r, indent=2, ensure_ascii=False)[:2000])

asyncio.run(main())
