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

PAD = "APP5B54EI0Z1EOEA"

async def main():
    c = VMOSCloudClient()
    
    # Try reboot command via async_adb_cmd (device might still accept it even at s14)
    print("[1] Trying adb reboot...")
    r = await c.async_adb_cmd([PAD], "reboot")
    print(f"  Result: {json.dumps(r, indent=2, ensure_ascii=False)[:500]}")
    
    await asyncio.sleep(30)
    
    # Check status
    r = await c._post("/vcpcloud/api/padApi/infos", {"page": 1, "rows": 10})
    for inst in r.get("data", {}).get("pageData", []):
        if inst.get("padCode") == PAD:
            print(f"  Status after reboot: {inst.get('padStatus')}")
    
    # If still 14, we need to do a full reset
    # But reset wipes ALL data - ask user first
    print("\n[2] If still stuck at 14, a full reset may be needed.")
    print("    instance_reset() wipes ALL data on the device.")
    
    # Actually, let's try restarting one more time with a delay
    print("\n[3] Attempting restart one more time...")
    r = await c.instance_restart([PAD])
    print(f"  Restart: {r.get('code')}")
    
    for i in range(30):
        await asyncio.sleep(10)
        r = await c._post("/vcpcloud/api/padApi/infos", {"page": 1, "rows": 10})
        for inst in r.get("data", {}).get("pageData", []):
            if inst.get("padCode") == PAD:
                st = inst.get("padStatus")
                if i % 3 == 0 or st != 14:
                    print(f"  [{(i+1)*10}s] status={st}")
                if st == 10:
                    print("  RECOVERED!")
                    return
                if st == 11:
                    print("  CRITICAL: status=11 — device may be bricked")
                    return
    
    print("  Still stuck. Reset required.")

asyncio.run(main())
