#!/bin/bash
# Clone all .220 APKs to D1 — one at a time with D1 restart between pairs
set -e
cd /home/debian/Downloads/vmos-titan-unified

IP="10.0.26.220"
D1_IP="10.0.96.174"
D1_PAD="ACP250923JS861KJ"

# APK list (pkg:path)
APKS=(
  "ru.cupis.wallet:/data/app/~~MQOPHJiiE-OgQqw02fdHWg==/ru.cupis.wallet-mHfJ4Ua1GYiictw54IYJGg==/base.apk"
  "ru.apteka:/data/app/~~j5AB5LSL4yAlPfSzN1o8xA==/ru.apteka-zQwY0yHDnh2Ik4ZrZAct9g==/base.apk"
  "ru.getpharma.eapteka:/data/app/~~Lh7KkGdY9VtBm3AC5wEsLg==/ru.getpharma.eapteka-rWUoa051jyFeGAfMEClihw==/base.apk"
  "ru.vk.store:/data/app/~~dI5E6u2aJsY99z-LqOyblA==/ru.vk.store-JU1LsGZ0NISX_7STXf6vsg==/base.apk"
  "ru.yandex.taxi:/data/app/~~wK2mAP68gZwmyFPp6UeaOA==/ru.yandex.taxi-PKOPpTH5qtvKYkprFt340A==/base.apk"
  "ru.ozon.fintech.finance:/data/app/~~-APX0nrW1si12r1V9idv3A==/ru.ozon.fintech.finance-MLh6s6UVrHHWWIXkWyddHA==/base.apk"
  "ru.ozon.app.android:/data/app/~~VEvGmwbOcylt8Lcx2Qp9hg==/ru.ozon.app.android-QBTantiUD_bSeBU-eHSV1Q==/base.apk"
  "ru.yoo.money:/data/app/~~Yf1SUfwhCxaEibOm-_Ctig==/ru.yoo.money-YqZiD1qUsxxsuETehWeIrA==/base.apk"
  "ru.rostel:/data/app/~~PmomRTxq1p5ywefa9_lGnw==/ru.rostel-a12u2iLNxh0NxbBhsamL8w==/base.apk"
  "com.wildberries.ru:/data/app/~~B6750jl6r8XGKnOM0-hRAQ==/com.wildberries.ru-lX42uzsZ4Zs675Qy80BYWQ==/base.apk"
)

restart_d1() {
  echo ">>> Restarting D1..."
  python3 -c "
import asyncio, sys; sys.path.insert(0,'vmos_titan/core')
from vmos_cloud_api import VMOSCloudClient
async def r():
    c=VMOSCloudClient(ak='BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi',sk='Q2SgcSwEfuwoedY0cijp6Mce')
    await c.instance_restart(['$D1_PAD'])
    await asyncio.sleep(45)
    await c.switch_root(['$D1_PAD'],enable=True,root_type=1,package_name='com.android.shell')
    await asyncio.sleep(3)
    r2=await c.sync_cmd('$D1_PAD','echo ALIVE')
    d=r2.get('data',[])
    print(d[0].get('errorMsg','').strip() if isinstance(d,list) and d else 'DEAD')
asyncio.run(r())
" 2>&1 | grep -v "HTTP Request"
}

transfer_and_install() {
  local PKG="$1"
  local APK_PATH="$2"
  local PORT="$3"
  
  echo "  Transferring $PKG (port $PORT)..."
  timeout 180 python3 -c "
import asyncio,sys,time,base64,logging
logging.basicConfig(level=logging.WARNING)
sys.path.insert(0,'.')
from neighbor_backup_restore import D1Bridge,build_adb_open
async def xfer():
    bridge=D1Bridge()
    IP='$IP';D1_IP='$D1_IP';port=$PORT
    pkg='$PKG';apk_path='$APK_PATH'
    dest=f'/data/local/tmp/{pkg}.apk'
    ip_key=IP.replace('.','_')
    # Clean
    await bridge.cmd(f'pkill -f \"nc.*{port}\" 2>/dev/null; rm -f {dest}')
    # Stage OPEN
    await bridge._ensure_cnxn(IP)
    shell_cmd=f'cat {apk_path} | nc -w 10 {D1_IP} {port}'
    pkt=build_adb_open(1,f'shell:{shell_cmd}')
    b64=base64.b64encode(pkt).decode()
    await bridge.cmd(f\"echo -n '{b64}' | base64 -d > /sdcard/.xo\")
    # Listener
    await bridge._throttle();bridge._last_cmd=time.time()
    try: await bridge.client.async_adb_cmd([bridge.pad],f'nc -l -p {port} > {dest}')
    except: pass
    await asyncio.sleep(2)
    # Relay
    relay=f'(cat /sdcard/.cnxn_{ip_key}; sleep 0.3; cat /sdcard/.xo; sleep 60) | timeout 65 nc {IP} 5555 > /dev/null 2>&1'
    await bridge._throttle();bridge._last_cmd=time.time()
    try: await bridge.client.async_adb_cmd([bridge.pad],relay)
    except: pass
    # Wait
    await asyncio.sleep(70)
    # Check
    s=await bridge.cmd(f'wc -c < {dest} 2>/dev/null || echo 0')
    try: size=int(s.strip())
    except: size=0
    print(f'SIZE={size}')
    # Install
    if size>100000:
        await bridge._throttle();bridge._last_cmd=time.time()
        try: await bridge.client.async_adb_cmd([bridge.pad],f'pm install -r -d {dest} && rm -f {dest}')
        except: pass
        await asyncio.sleep(15)
    await bridge.cmd(f'rm -f /sdcard/.xo')
asyncio.run(xfer())
" 2>&1 | grep -E "^SIZE=|ERROR"
}

# Main loop
echo "============================================="
echo "CLONE .220 → D1: ${#APKS[@]} APKs remaining"
echo "============================================="

COUNT=0
for ENTRY in "${APKS[@]}"; do
  PKG="${ENTRY%%:*}"
  APK_PATH="${ENTRY#*:}"
  PORT=$((19900 + COUNT))
  
  # Restart D1 every 2 APKs
  if [ $((COUNT % 2)) -eq 0 ]; then
    restart_d1
  fi
  
  COUNT=$((COUNT + 1))
  echo "[$COUNT/${#APKS[@]}] $PKG"
  transfer_and_install "$PKG" "$APK_PATH" "$PORT"
  echo ""
done

# Final restart and check
restart_d1
echo ""
echo "=== FINAL PACKAGE LIST ==="
python3 -c "
import asyncio,sys; sys.path.insert(0,'vmos_titan/core')
from vmos_cloud_api import VMOSCloudClient
async def check():
    c=VMOSCloudClient(ak='BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi',sk='Q2SgcSwEfuwoedY0cijp6Mce')
    r=await c.sync_cmd('$D1_PAD','pm list packages -3 2>/dev/null | sort')
    d=r.get('data',[])
    print(d[0].get('errorMsg','').strip() if isinstance(d,list) and d else 'FAIL')
asyncio.run(check())
" 2>&1 | grep -v "HTTP Request"

echo ""
echo "DONE"
