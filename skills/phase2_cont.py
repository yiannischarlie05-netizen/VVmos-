#!/usr/bin/env python3
"""Phase 2+3 continuation: Steps 9-16 + verification"""
import asyncio, sys
sys.path.insert(0, 'vmos_titan/core')
sys.path.insert(0, 'core')
sys.path.insert(0, 'server')
from vmos_cloud_api import VMOSCloudClient

PAD = 'ACP250329ACQRPDV'

async def sh(cmd, label='', timeout=30):
    client = VMOSCloudClient()
    r = await client.async_adb_cmd([PAD], cmd)
    tid = None
    if r.get('code') == 200:
        data = r.get('data', [])
        if data:
            tid = data[0].get('taskId')
    if not tid:
        code = r.get('code', '?')
        if code == 110031:
            print(f'  [{label}] Rate limited, waiting 30s...')
            await asyncio.sleep(30)
            return await sh(cmd, label, timeout)
        print(f'  [{label}] CMD_ERROR:{code} - {r.get("msg","")}')
        return f'CMD_ERROR:{code}'
    for i in range(timeout):
        await asyncio.sleep(1)
        d = await client.task_detail([tid])
        if d.get('code') == 200:
            items = d.get('data', [])
            if items and items[0].get('taskStatus') == 3:
                result = items[0].get('taskResult', '') or ''
                if label:
                    print(f'  [{label}] OK: {result.strip()[:120]}')
                return result
            if items and items[0].get('taskStatus', 0) < 0:
                if label:
                    print(f'  [{label}] FAILED')
                return 'TASK_FAILED'
    if label:
        print(f'  [{label}] TIMEOUT')
    return 'TIMEOUT'

async def main():
    print('=== CONTINUING PHASE 2+3 (Steps 9-16) ===')

    # 9. Port blocking
    print('[9] Blocking detection ports...')
    await sh(
        'iptables -A INPUT -p tcp --dport 27042 -j DROP 2>/dev/null; '
        'iptables -A INPUT -p tcp --dport 27043 -j DROP 2>/dev/null; '
        'iptables -A OUTPUT -p tcp --dport 27042 -j DROP 2>/dev/null; '
        'iptables -A INPUT -p tcp --dport 5555 -j DROP 2>/dev/null; '
        'ip6tables -P INPUT DROP 2>/dev/null; '
        'ip6tables -P OUTPUT DROP 2>/dev/null; '
        'ip6tables -P FORWARD DROP 2>/dev/null; '
        'echo FW_OK',
        'iptables'
    )
    await asyncio.sleep(5)
    
    # 10. NFC config
    print('[10] Configuring NFC...')
    await sh(
        'settings put secure nfc_on 1; '
        'settings put secure nfc_payment_foreground 1; '
        'settings put secure nfc_payment_default_component '
        'com.google.android.apps.walletnfcrel/.service.HceDelegateService; '
        'echo NFC_OK',
        'nfc'
    )
    await asyncio.sleep(5)
    
    # 11. SELinux 
    print('[11] SELinux cleanup...')
    await sh('rmmod selinux_leak_fix 2>/dev/null; getenforce', 'selinux')
    await asyncio.sleep(5)
    
    # 12. Battery realism
    print('[12] Battery realism...')
    await sh(
        'setprop persist.sys.cloud.battery.level 73 && '
        'setprop persist.sys.cloud.battery.capacity 4500 && '
        'echo BATT_OK',
        'battery'
    )
    await asyncio.sleep(5)

    # 13. WiFi props
    print('[13] WiFi props...')
    await sh(
        'setprop persist.sys.cloud.wifi.ssid NETGEAR5G-Home && '
        'setprop persist.sys.cloud.wifi.mac 5c:6a:80:3e:a2:f7 && '
        'setprop persist.sys.cloud.wifi.ip 192.168.1.147 && '
        'setprop persist.sys.cloud.wifi.gateway 192.168.1.1 && '
        'setprop persist.sys.cloud.wifi.dns1 8.8.8.8 && '
        'echo WIFI_OK',
        'wifi'
    )
    await asyncio.sleep(5)

    # 14. Locale 
    print('[14] Locale...')
    await sh(
        'setprop persist.sys.language en && '
        'setprop persist.sys.country US && '
        'setprop persist.sys.locale en-US && '
        'echo LOCALE_OK',
        'locale'
    )
    await asyncio.sleep(5)

    # 15. Su hiding
    print('[15] Su hiding...')
    await sh(
        'for p in /system/bin/su /system/xbin/su /sbin/su /vendor/bin/su; do '
        '[ -f "$p" ] && chmod 000 "$p" && mount --bind /dev/null "$p" 2>/dev/null; '
        'done; echo SU_HIDE_OK',
        'su-hide'
    )
    await asyncio.sleep(5)
    
    # 16. Process cloaking
    print('[16] Process cloaking...')
    await sh(
        'for pid in $(ls /proc/ 2>/dev/null | grep -E "^[0-9]+$" | head -100); do '
        'cmdline=$(cat /proc/$pid/cmdline 2>/dev/null | tr "\\0" " "); '
        'echo "$cmdline" | grep -qiE "frida|xposed|substrate|magisk" && '
        'kill -9 $pid 2>/dev/null; '
        'done; echo PROC_CLOAK_OK',
        'proc-cloak'
    )
    await asyncio.sleep(5)

    # VERIFICATION
    print('\n=== VERIFICATION ===')
    await sh('cat /proc/cmdline | head -c 200', 'verify-cmdline')
    await asyncio.sleep(4)
    await sh(
        'getprop gsm.sim.state; getprop gsm.operator.alpha; getprop gsm.operator.numeric',
        'verify-sim'
    )
    await asyncio.sleep(4)
    await sh('getprop persist.sys.timezone', 'verify-tz')
    await asyncio.sleep(4)
    await sh('settings get secure nfc_on', 'verify-nfc')
    await asyncio.sleep(4)
    await sh('getenforce', 'verify-selinux')
    await asyncio.sleep(4)
    await sh('getprop persist.sys.cloud.battery.level', 'verify-battery')
    await asyncio.sleep(4)
    await sh('getprop persist.sys.cloud.wifi.ssid', 'verify-wifi')
    
    print('\n=== PHASE 2+3 FULLY COMPLETE ===')

if __name__ == '__main__':
    asyncio.run(main())
