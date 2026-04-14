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

async def sh(client, cmd, timeout=30):
    r = await client.async_adb_cmd([PAD], cmd)
    tid = r.get("data", [{}])[0].get("taskId") if r.get("code") == 200 else None
    if not tid: return ""
    for _ in range(timeout):
        await asyncio.sleep(1)
        d = await client.task_detail([tid])
        if d.get("code") == 200:
            items = d.get("data", [])
            if items and items[0].get("taskStatus") == 3:
                return items[0].get("taskResult", "")
            if items and items[0].get("taskStatus", 0) < 0:
                return ""
    return ""

async def main():
    c = VMOSCloudClient()
    
    # Step 1: Restart the device
    print("[1] Restarting device (status=14 → 10)...")
    r = await c.instance_restart([PAD])
    print(f"  Restart: code={r.get('code')}")
    
    # Step 2: Wait for recovery
    for i in range(24):
        await asyncio.sleep(5)
        r = await c._post("/vcpcloud/api/padApi/infos", {"page": 1, "rows": 10})
        for inst in r.get("data", {}).get("pageData", []):
            if inst.get("padCode") == PAD:
                st = inst.get("padStatus")
                print(f"  [{(i+1)*5}s] status={st}")
                if st == 10:
                    print("  RUNNING!")
                    
                    # Step 3: Wait for boot & check accounts
                    await asyncio.sleep(10)
                    out = await sh(c, "dumpsys account 2>/dev/null | grep -E 'Accounts:|com.google|Account.*epolu' | head -10")
                    print(f"\n[2] Account check after restart:\n{out}")
                    
                    await asyncio.sleep(5)
                    out = await sh(c, "dumpsys account 2>/dev/null | head -25")
                    print(f"\n[3] Full account dump:\n{out}")
                    
                    # Check if stealth patches survived restart
                    await asyncio.sleep(5)
                    out = await sh(c, """echo "vboot=$(getprop ro.boot.verifiedbootstate)" && echo "build=$(getprop ro.build.type)" && echo "nfc=$(settings get secure nfc_on)" && echo "cmdline_vmos=$(cat /proc/cmdline | grep -ci vmos)"  """)
                    print(f"\n[4] Stealth check:\n{out}")
                    return
    print("Device did not recover within 120s")

asyncio.run(main())
