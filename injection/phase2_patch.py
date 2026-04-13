#!/usr/bin/env python3
"""Phase 2+3: Anomaly Patching & Stealth Hardening for ACP250329ACQRPDV"""
import asyncio, os, sys
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
    print('=== PHASE 2: ANOMALY PATCHING - ACP250329ACQRPDV ===')
    
    # 1. SIM/Telephony - T-Mobile US
    print('\n[1] Setting SIM to T-Mobile US...')
    sim_cmds = (
        'setprop gsm.sim.state READY && '
        'setprop gsm.sim.operator.alpha T-Mobile && '
        'setprop gsm.sim.operator.numeric 310260 && '
        'setprop gsm.sim.operator.iso-country us && '
        'setprop gsm.network.type LTE && '
        'setprop gsm.operator.alpha T-Mobile && '
        'setprop gsm.operator.numeric 310260 && '
        'setprop gsm.operator.iso-country us && '
        'setprop gsm.current.phone-type 1 && '
        'echo SIM_OK'
    )
    await sh(sim_cmds, 'sim-telephony')
    await asyncio.sleep(5)
    
    # 2. Timezone to LA
    print('[2] Setting timezone to LA...')
    await sh(
        'setprop persist.sys.timezone America/Los_Angeles && '
        'service call alarm 3 s16 America/Los_Angeles && echo TZ_OK',
        'timezone'
    )
    await asyncio.sleep(5)
    
    # 3. Check for resetprop
    print('[3] Checking resetprop availability...')
    await sh(
        'which resetprop 2>/dev/null || '
        'ls /data/local/tmp/magisk64 2>/dev/null || '
        'ls /data/adb/magisk/busybox 2>/dev/null || '
        'echo NO_RESETPROP',
        'resetprop-check'
    )
    await asyncio.sleep(5)

    # 4. Verified boot state
    print('[4] Fixing verified boot state props...')
    await sh(
        'setprop ro.boot.verifiedbootstate green 2>/dev/null; '
        'setprop ro.boot.flash.locked 1 2>/dev/null; '
        'setprop ro.debuggable 0 2>/dev/null; '
        'setprop ro.secure 1 2>/dev/null; '
        'echo SETPROP_DONE',
        'vboot-setprop'
    )
    await asyncio.sleep(5)

    # 5. Proc sterilization - cmdline
    print('[5] Proc sterilization - cmdline...')
    await sh(
        'mkdir -p /dev/.sc 2>/dev/null; '
        'mount -t tmpfs tmpfs /dev/.sc 2>/dev/null; '
        'cat /proc/cmdline | '
        'sed "s/androidboot.verifiedbootstate=orange/androidboot.verifiedbootstate=green/g" | '
        'sed "s/storagemedia=emmc //g" | '
        'sed "s/androidboot.storagemedia=emmc //g" | '
        'sed "s/mac=[^ ]* //g" '
        '> /dev/.sc/cmdline && '
        'mount --bind /dev/.sc/cmdline /proc/cmdline && '
        'echo CMDLINE_OK || echo CMDLINE_FAIL',
        'proc-cmdline'
    )
    await asyncio.sleep(5)
    
    # 6. Proc cgroup
    print('[6] Proc cgroup...')
    await sh(
        'echo "0::/" > /dev/.sc/cgroup && '
        'mount --bind /dev/.sc/cgroup /proc/1/cgroup && '
        'echo CGROUP_OK || echo CGROUP_FAIL',
        'proc-cgroup'
    )
    await asyncio.sleep(5)
    
    # 7. Proc mounts filter
    print('[7] Proc mounts filter...')
    await sh(
        'cat /proc/mounts | grep -v "cloud\\|armcloud\\|vmos\\|/dev/.sc" '
        '> /dev/.sc/mounts && '
        'mount --bind /dev/.sc/mounts /proc/mounts && '
        'echo MOUNTS_OK || echo MOUNTS_FAIL',
        'proc-mounts'
    )
    await asyncio.sleep(5)
    
    # 8. Proc mountinfo filter
    print('[8] Proc mountinfo filter...')
    await sh(
        'cat /proc/self/mountinfo | grep -v "tmpfs /dev/.sc\\|cloud\\|armcloud" '
        '> /dev/.sc/mountinfo && '
        'mount --bind /dev/.sc/mountinfo /proc/self/mountinfo && '
        'echo MOUNTINFO_OK || echo MOUNTINFO_FAIL',
        'proc-mountinfo'
    )
    await asyncio.sleep(5)

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
    
    print('\n=== PHASE 2+3 COMPLETE ===')

if __name__ == '__main__':
    asyncio.run(main())
