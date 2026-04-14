#!/usr/bin/env python3
"""
Try direct shell commands on known devices D1 and D2
"""

import asyncio
import os
import sys

# Add vmos_titan to path
sys.path.insert(0, '/home/debian/Downloads/vmos-titan-unified')

# Load .env file manually BEFORE importing VMOSCloudClient
def load_env():
    env_path = '/home/debian/Downloads/vmos-titan-unified/.env'
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

# Set VMOS_CLOUD_AK and VMOS_CLOUD_SK BEFORE importing
os.environ['VMOS_CLOUD_AK'] = os.environ.get('VMOS_AK', '')
os.environ['VMOS_CLOUD_SK'] = os.environ.get('VMOS_SK', '')

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

async def main():
    client = VMOSCloudClient()
    
    pad_code = 'APP5AU4BB1QQBHNA'
    
    print('═' * 70)
    print(f'  200 EXPERIMENTS: {pad_code}')
    print('═' * 70)
    
    commands = [
        # System Information (1-20)
        'uname -a',
        'id',
        'whoami',
        'hostname',
        'cat /proc/version',
        'cat /proc/cpuinfo | head -10',
        'cat /proc/meminfo | head -10',
        'free -h',
        'uptime',
        'date',
        'getprop ro.build.version.release',
        'getprop ro.build.version.sdk',
        'getprop ro.product.model',
        'getprop ro.product.brand',
        'getprop ro.product.manufacturer',
        'getprop ro.build.fingerprint',
        'getprop ro.build.date',
        'getprop ro.build.id',
        'getprop ro.build.type',
        'getprop ro.build.tags',
        
        # Network Tests (21-40)
        'ip addr show',
        'ip route show',
        'ip link show',
        'cat /proc/net/route',
        'cat /proc/net/arp',
        'cat /proc/net/tcp',
        'cat /proc/net/udp',
        'netstat -an 2>/dev/null | head -20',
        'ping -c 1 8.8.8.8 2>/dev/null || echo "ping failed"',
        'nslookup google.com 2>/dev/null || echo "nslookup failed"',
        'cat /etc/resolv.conf',
        'cat /etc/hosts',
        'iptables -L -n 2>/dev/null | head -20',
        'iptables -t nat -L -n 2>/dev/null | head -20',
        'ip6tables -L -n 2>/dev/null | head -10',
        'cat /proc/sys/net/ipv4/ip_forward',
        'cat /proc/sys/net/ipv4/conf/all/accept_source_route',
        'cat /proc/sys/net/ipv4/ip_local_port_range',
        'ss -tulpn 2>/dev/null | head -20',
        
        # File System (41-60)
        'df -h',
        'mount',
        'cat /proc/mounts | head -30',
        'ls -la /',
        'ls -la /system/',
        'ls -la /vendor/',
        'ls -la /product/',
        'ls -la /data/',
        'ls -la /sdcard/',
        'ls -la /storage/',
        'ls -la /dev/',
        'ls -la /proc/',
        'ls -la /sys/',
        'ls -la /tmp/',
        'ls -la /cache/',
        'ls -la /apex/',
        'ls -la /odm/',
        'ls -la /oem/',
        'ls -la /metadata/',
        'ls -la /debug_ramdisk/',
        
        # Block Devices (61-80)
        'cat /proc/partitions',
        'ls -la /dev/block/',
        'ls -la /dev/block/by-name/',
        'ls -la /dev/block/dm-*',
        'ls -la /dev/block/mmcblk0*',
        'cat /proc/devices | head -20',
        'lsblk 2>/dev/null || echo "lsblk not available"',
        'dmsetup ls 2>/dev/null || echo "dmsetup not available"',
        'fdisk -l 2>/dev/null | head -20',
        'cat /proc/diskstats | head -20',
        'ls -la /dev/sd* 2>/dev/null',
        'ls -la /dev/nvme* 2>/dev/null',
        'cat /sys/block/*/size',
        'cat /sys/block/*/queue/rotational',
        'cat /sys/block/*/queue/scheduler',
        'ls -la /dev/loop* | head -20',
        'losetup -a 2>/dev/null | head -10',
        'cat /proc/swaps',
        'swapon -s',
        'free -m',
        
        # Process Analysis (81-100)
        'ps aux',
        'ps -ef',
        'top -n 1 2>/dev/null | head -20',
        'cat /proc/1/status',
        'cat /proc/1/cmdline',
        'cat /proc/1/environ | tr "\\0" "\\n" | head -20',
        'cat /proc/1/cgroup',
        'cat /proc/1/mounts',
        'cat /proc/1/limits',
        'cat /proc/1/status | grep -E "(Uid|Gid|Cap)"',
        'ls -la /proc/1/root/',
        'cat /proc/1/stack 2>/dev/null | head -20',
        'cat /proc/1/maps 2>/dev/null | head -20',
        'cat /proc/1/fd 2>/dev/null | head -20',
        'cat /proc/self/status',
        'cat /proc/self/cmdline',
        'cat /proc/self/cgroup',
        'ls -la /proc/self/fd/ 2>/dev/null | head -20',
        'pgrep -l init',
        'pgrep -l zygote',
        'pgrep -l system_server',
        'cat /proc/sys/kernel/pid_max',
        
        # Security (101-120)
        'cat /proc/self/status | grep -E "(Uid|Gid)"',
        'getenforce',
        'selinuxenabled 2>/dev/null || echo "selinuxenabled not available"',
        'cat /sys/fs/selinux/enforce',
        'cat /sys/fs/selinux/status',
        'cat /proc/self/attr/current',
        'cat /proc/self/attr/exec',
        'cat /proc/self/attr/fscreate',
        'ls -la /data/misc/keystore/',
        'ls -la /data/misc/gatekeeper/',
        'ls -la /data/misc/vboot/',
        'getprop ro.boot.verifiedbootstate',
        'getprop ro.boot.vbmeta.device',
        'cat /proc/sys/kernel/random/entropy_avail',
        'cat /proc/sys/kernel/random/poolsize',
        'cat /proc/sys/kernel/random/uuid',
        'ls -la /data/adb/',
        'cat /data/adb/adb_keys 2>/dev/null',
        'cat /data/misc/adb/adb_keys 2>/dev/null',
        'getprop ro.debuggable',
        'getprop ro.secure',
        
        # Container/Namespaces (121-140)
        'which nsenter',
        'nsenter -t 1 -m -- hostname',
        'nsenter -t 1 -m -- ls -la /',
        'nsenter -t 1 -m -- cat /proc/1/cgroup',
        'nsenter -t 1 -m -- cat /proc/1/cmdline',
        'nsenter -t 1 -m -- ip addr show',
        'nsenter -t 1 -m -- mount | head -20',
        'nsenter -t 1 -m -- ps aux | head -20',
        'nsenter -t 1 -m -p -- cat /etc/passwd',
        'nsenter -t 1 -m -p -- cat /etc/shadow 2>/dev/null || echo "shadow not accessible"',
        'nsenter -t 1 -m -p -- ls -la /var/lib/',
        'nsenter -t 1 -m -p -- ls -la /var/log/',
        'nsenter -t 1 -m -p -- cat /var/log/syslog 2>/dev/null | head -20',
        'nsenter -t 1 -m -p -- docker ps 2>/dev/null || echo "no docker"',
        'nsenter -t 1 -m -p -- systemctl list-units 2>/dev/null | head -20',
        'nsenter -t 1 -m -p -- service --status-all 2>/dev/null | head -20',
        'nsenter -t 1 -m -p -- crontab -l 2>/dev/null',
        'nsenter -t 1 -m -p -- cat /etc/crontab 2>/dev/null',
        'nsenter -t 1 -m -p -- ls -la /etc/systemd/',
        'nsenter -t 1 -m -p -- journalctl -n 20 2>/dev/null || echo "no journalctl"',
        
        # Android Specific (141-160)
        'pm list packages',
        'pm list packages -3',
        'pm list packages -s',
        'pm list features',
        'pm list permissions',
        'pm list users',
        'pm list instrumentation',
        'dumpsys battery',
        'dumpsys wifi',
        'dumpsys connectivity',
        'dumpsys telephony',
        'dumpsys location',
        'dumpsys package',
        'getprop',
        'settings list global',
        'settings list secure',
        'settings list system',
        'am stack list',
        'am dumpheap',
        'am kill-all',
        
        # Hardware (161-180)
        'cat /proc/cpuinfo',
        'cat /proc/meminfo',
        'cat /proc/interrupts',
        'cat /proc/devices',
        'cat /proc/ioports',
        'cat /proc/iomem',
        'lspci 2>/dev/null || echo "lspci not available"',
        'lsusb 2>/dev/null | head -20',
        'lsmod 2>/dev/null || echo "lsmod not available"',
        'cat /proc/modules',
        'dmesg | head -30',
        'cat /var/log/kern.log 2>/dev/null | head -20',
        'cat /proc/kallsyms | head -30',
        'cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq',
        'cat /sys/class/thermal/thermal_zone*/temp',
        'cat /sys/class/hwmon/hwmon*/temp*_input',
        'cat /proc/loadavg',
        'cat /proc/uptime',
        'cat /proc/stat | head -10',
        
        # VMOS Cloud Specific (181-200)
        'getprop ro.build.cloud.imginfo',
        'getprop ro.build.cloud.unique_id',
        'cat /proc/cmdline',
        'env',
        'cat /system/build.prop',
        'cat /vendor/build.prop',
        'cat /product/build.prop 2>/dev/null',
        'ls -la /data/.titan/',
        'ls -la /data/local/tmp/',
        'cat /data/local/tmp/.titan/* 2>/dev/null',
        'cat /proc/self/status | head -30',
        'cat /proc/self/mounts',
        'ls -la /dev/block/by-name/',
        'cat /proc/partitions',
        'ls -la /data/data/',
        'du -sh /data/',
        'du -sh /system/',
        'du -sh /vendor/',
        'ls -la /sdcard/Download/',
        'ls -la /sdcard/DCIM/',
        'ls -la /sdcard/Pictures/',
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f'\n▶ [{i}/200] {cmd}')
        result = await client.sync_cmd(pad_code, cmd, timeout_sec=30)
        
        if isinstance(result, dict):
            code = result.get('code', -1)
            msg = result.get('msg', '')
            data = result.get('data', '')
            
            if code == 200:
                print(f"✓ Success")
                if data and len(str(data)) < 500:
                    print(data)
                else:
                    print(f"(Output too long or empty)")
            else:
                print(f"✗ Failed (code: {code}): {msg}")
        else:
            print(f"✗ Unexpected response: {type(result)}")

if __name__ == '__main__':
    asyncio.run(main())
