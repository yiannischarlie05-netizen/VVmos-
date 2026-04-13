#!/usr/bin/env node
/**
 * VMOS Titan — Deep Device Scanner & Container Escape Mapper
 * 
 * Connects directly to device via VMOS Cloud API syncCmd
 * Performs comprehensive environment scan, container escape probing,
 * and neighbor device/subnet mapping.
 */

const path = require('path');
const fs = require('fs');

const { AK, SK, HOST, SVC, CT, SHD, hmacSign, api, sh } = require('../shared/vmos_api');
const PAD_CODE = 'ACP250923JS861KJ';

const RESULTS = { timestamp: new Date().toISOString(), device: PAD_CODE, scans: {} };

const log = msg => console.log(`[${new Date().toISOString().slice(11,19)}] ${msg}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const section = title => { console.log(`\n${'═'.repeat(70)}`); console.log(`  ${title}`); console.log(`${'═'.repeat(70)}`); };

async function main() {
  console.log('\n' + '═'.repeat(70));
  console.log('  VMOS TITAN — DEEP DEVICE SCANNER & CONTAINER ESCAPE MAPPER');
  console.log('  Target: ' + PAD_CODE);
  console.log('  ' + new Date().toISOString());
  console.log('═'.repeat(70));

  // ═══════════════════════════════════════════════════════════════
  // SCAN 1: Device Status via API
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 1: DEVICE STATUS VIA API');
  
  log('Fetching device info from API...');
  const rInfos = await vmosPost('/vcpcloud/api/padApi/infos', { page: 1, rows: 100 });
  const devList = rInfos.data?.pageData || [];
  const dev = devList.find(d => d.padCode === PAD_CODE);
  
  if (!dev) { log('FATAL: Device not found'); process.exit(1); }
  
  RESULTS.scans.api_info = dev;
  log(`  padCode:    ${dev.padCode}`);
  log(`  padStatus:  ${dev.padStatus} (10=running)`);
  log(`  image:      ${dev.imageVersion}`);
  log(`  deviceIp:   ${dev.deviceIp}`);
  log(`  adbStatus:  ${dev.adbOpenStatus}`);
  log(`  padType:    ${dev.padType}`);
  log(`  padGrade:   ${dev.padGrade}`);
  log(`  cluster:    ${dev.clusterCode}`);
  log(`  createTime: ${dev.createTime}`);

  // Get detailed padInfo
  const rInfo = await vmosPost('/vcpcloud/api/padApi/padInfo', { padCode: PAD_CODE }).catch(() => ({}));
  if (rInfo.code === 200 && rInfo.data) {
    RESULTS.scans.pad_info = rInfo.data;
    log(`  simCountry: ${rInfo.data.simCountry || 'n/a'}`);
    log(`  rootStatus: ${rInfo.data.rootStatus || 'n/a'}`);
  }

  // ═══════════════════════════════════════════════════════════════
  // SCAN 2: TRUE HARDWARE IDENTITY
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 2: TRUE HARDWARE IDENTITY (beneath spoofing)');
  
  const hwCmds = {
    'kernel':       'cat /proc/version',
    'device_tree':  'cat /proc/device-tree/model 2>/dev/null || echo N/A',
    'cpuinfo':      'cat /proc/cpuinfo | head -30',
    'soc':          'getprop ro.soc.model 2>/dev/null; getprop ro.soc.manufacturer 2>/dev/null',
    'gpu_real':     'cat /sys/class/misc/mali0/device/gpuinfo 2>/dev/null || ls /sys/class/misc/ 2>/dev/null',
    'drm_driver':   'ls /sys/kernel/debug/dri/ 2>/dev/null; cat /sys/kernel/debug/dri/*/name 2>/dev/null | head -5',
    'memory':       'cat /proc/meminfo | head -5',
    'cmdline':      'cat /proc/cmdline',
    'build_host':   'getprop ro.build.host',
    'build_flavor': 'getprop ro.build.flavor',
    'sys_brand':    'getprop ro.product.system.brand',
    'sys_device':   'getprop ro.product.system.device',
    'cloud_img':    'getprop ro.build.cloud.imginfo',
    'cloud_id':     'getprop ro.build.cloud.unique_id',
    'cloud_server': 'getprop ro.boot.armcloud_server_addr',
    'boot_padcode': 'getprop ro.boot.pad_code',
    'boot_cluster': 'getprop ro.boot.cluster_code',
  };
  
  RESULTS.scans.hardware = {};
  for (const [key, cmd] of Object.entries(hwCmds)) {
    const result = await sh(cmd, 15);
    RESULTS.scans.hardware[key] = result;
    const preview = result.split('\n')[0].slice(0, 100);
    log(`  ${key}: ${preview}`);
    await sleep(300);
  }

  // ═══════════════════════════════════════════════════════════════
  // SCAN 3: SPOOFED IDENTITY PROPS
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 3: SPOOFED IDENTITY (what apps see)');
  
  const spoofCmds = {
    'brand':       'getprop ro.product.brand',
    'model':       'getprop ro.product.model',
    'device':      'getprop ro.product.device',
    'fingerprint': 'getprop ro.build.fingerprint',
    'android_ver': 'getprop ro.build.version.release',
    'sdk':         'getprop ro.build.version.sdk',
    'security':    'getprop ro.build.version.security_patch',
    'build_type':  'getprop ro.build.type',
    'build_tags':  'getprop ro.build.tags',
    'verified_boot':'getprop ro.boot.verifiedbootstate',
    'serial':      'getprop ro.serialno',
    'imei':        'getprop persist.sys.cloud.imeinum',
    'android_id':  'settings get secure android_id',
    'mac':         'getprop persist.sys.cloud.wifi.mac',
    'carrier':     'getprop gsm.operator.alpha',
    'sim_numeric': 'getprop gsm.sim.operator.numeric',
    'gpu_renderer':'getprop persist.sys.cloud.gpu.gl_renderer',
    'gpu_vendor':  'getprop persist.sys.cloud.gpu.gl_vendor',
    'gps_lat':     'getprop persist.sys.cloud.gps.lat',
    'gps_lon':     'getprop persist.sys.cloud.gps.lon',
    'timezone':    'getprop persist.sys.timezone',
    'locale':      'getprop persist.sys.locale',
    'wifi_ssid':   'getprop persist.sys.cloud.wifi.ssid',
    'battery':     'getprop persist.sys.cloud.battery.level',
  };
  
  RESULTS.scans.spoofed = {};
  for (const [key, cmd] of Object.entries(spoofCmds)) {
    const result = await sh(cmd, 10);
    RESULTS.scans.spoofed[key] = result;
    log(`  ${key}: ${result}`);
    await sleep(200);
  }

  // ═══════════════════════════════════════════════════════════════
  // SCAN 4: CONTAINER ARCHITECTURE
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 4: CONTAINER ARCHITECTURE');
  
  const containerCmds = {
    'namespaces':    'ls -la /proc/1/ns/ 2>/dev/null',
    'cgroups':       'cat /proc/1/cgroup 2>/dev/null',
    'cgroup_list':   'cat /proc/cgroups 2>/dev/null | head -15',
    'mounts':        'cat /proc/mounts | head -25',
    'overlay_mounts':'mount | grep overlay 2>/dev/null',
    'root_fs':       'df / | tail -1; stat -f / 2>/dev/null',
    'data_fs':       'df /data | tail -1',
    'block_devs':    'ls /dev/block/ 2>/dev/null | wc -l; ls /dev/block/ 2>/dev/null | head -20',
    'loop_devs':     'ls /dev/block/loop* 2>/dev/null | wc -l',
    'dm_devs':       'ls /dev/block/dm-* 2>/dev/null',
    'disk_usage':    'df -h 2>/dev/null | head -15',
    'init_cmdline':  'cat /proc/1/cmdline 2>/dev/null | tr "\\0" " "',
    'selinux':       'getenforce 2>/dev/null; cat /sys/fs/selinux/enforce 2>/dev/null',
    'capabilities':  'cat /proc/1/status | grep -i cap 2>/dev/null',
    'seccomp':       'cat /proc/1/status | grep -i seccomp 2>/dev/null',
  };
  
  RESULTS.scans.container = {};
  for (const [key, cmd] of Object.entries(containerCmds)) {
    const result = await sh(cmd, 15);
    RESULTS.scans.container[key] = result;
    const lines = result.split('\n');
    log(`  ${key}: ${lines[0].slice(0, 90)}${lines.length > 1 ? ` (+${lines.length-1} lines)` : ''}`);
    await sleep(300);
  }

  // ═══════════════════════════════════════════════════════════════
  // SCAN 5: NETWORK ENVIRONMENT & INTERFACES
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 5: NETWORK ENVIRONMENT');
  
  const netCmds = {
    'ip_addr':       'ip addr show 2>/dev/null',
    'ip_route':      'ip route show 2>/dev/null',
    'dns':           'cat /etc/resolv.conf 2>/dev/null; getprop net.dns1; getprop net.dns2',
    'iptables':      'iptables -L -n 2>/dev/null | head -30',
    'ip6tables':     'ip6tables -L -n 2>/dev/null | head -10',
    'nat_rules':     'iptables -t nat -L -n 2>/dev/null | head -20',
    'ss_listen':     'ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null',
    'ss_established':'ss -tnp 2>/dev/null | head -20 || netstat -tnp 2>/dev/null | head -20',
    'arp_table':     'ip neigh show 2>/dev/null || cat /proc/net/arp 2>/dev/null',
    'bridge':        'ip link show type bridge 2>/dev/null; brctl show 2>/dev/null',
    'veth_pairs':    'ip link show type veth 2>/dev/null',
    'net_ns':        'ip netns list 2>/dev/null',
    'gateway':       'ip route | grep default',
    'nf_conntrack':  'cat /proc/net/nf_conntrack 2>/dev/null | wc -l; cat /proc/net/nf_conntrack 2>/dev/null | head -10',
  };
  
  RESULTS.scans.network = {};
  for (const [key, cmd] of Object.entries(netCmds)) {
    const result = await sh(cmd, 15);
    RESULTS.scans.network[key] = result;
    const lines = result.split('\n');
    log(`  ${key}: ${lines[0].slice(0, 90)}${lines.length > 1 ? ` (+${lines.length-1} lines)` : ''}`);
    await sleep(300);
  }

  // ═══════════════════════════════════════════════════════════════
  // SCAN 6: CONTAINER ESCAPE VECTORS
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 6: CONTAINER ESCAPE PROBING');
  
  const escapeCmds = {
    // Check if we can see host processes
    'host_procs':     'ls /proc/ 2>/dev/null | grep -E "^[0-9]+$" | wc -l',
    'proc_1_exe':     'readlink /proc/1/exe 2>/dev/null',
    'proc_1_root':    'readlink /proc/1/root 2>/dev/null',
    
    // eBPF check
    'bpf_syscalls':   'grep -i bpf /proc/kallsyms 2>/dev/null | wc -l',
    'bpf_progs':      'ls /sys/fs/bpf/ 2>/dev/null',
    
    // Docker socket / containerd
    'docker_sock':    'ls -la /var/run/docker.sock 2>/dev/null; ls /var/run/containerd/ 2>/dev/null',
    
    // Host filesystem access attempts
    'host_mounts':    'cat /proc/self/mountinfo 2>/dev/null | grep -E "(host|docker|overlay)" | head -10',
    'proc_sysrq':     'cat /proc/sysrq-trigger 2>/dev/null; echo $?',
    
    // Kernel modules
    'lsmod':          'lsmod 2>/dev/null | head -20 || cat /proc/modules 2>/dev/null | head -20',
    
    // Device access
    'dev_access':     'ls /dev/kvm 2>/dev/null; ls /dev/vhost-net 2>/dev/null; ls /dev/net/tun 2>/dev/null; ls /dev/fuse 2>/dev/null',
    
    // Root check
    'whoami':         'id; whoami',
    'root_test':      'echo TEST > /tmp/root_test && cat /tmp/root_test && rm /tmp/root_test && echo ROOT_WRITE_OK',
    
    // System remount attempt
    'remount_test':   'mount -o remount,rw / 2>&1 | head -3',
    
    // Ptrace scope
    'ptrace_scope':   'cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null',
    
    // Kernel version for exploits
    'kernel_ver':     'uname -a',
  };
  
  RESULTS.scans.escape = {};
  for (const [key, cmd] of Object.entries(escapeCmds)) {
    const result = await sh(cmd, 15);
    RESULTS.scans.escape[key] = result;
    const lines = result.split('\n');
    log(`  ${key}: ${lines[0].slice(0, 90)}`);
    await sleep(300);
  }

  // ═══════════════════════════════════════════════════════════════
  // SCAN 7: SUBNET SCAN & NEIGHBOR DEVICE MAPPING
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 7: SUBNET SCAN & NEIGHBOR DEVICE MAPPING');
  
  // Get our IP and subnet
  const myIp = await sh("ip addr show eth0 2>/dev/null | grep 'inet ' | awk '{print $2}'", 10);
  log(`  Our IP: ${myIp}`);
  RESULTS.scans.network_map = { our_ip: myIp };
  
  // Ping sweep the local subnet
  log('  Running ARP/ping sweep on local subnet...');
  const sweepResult = await sh([
    "ip neigh show 2>/dev/null",
    "echo '---ARP_END---'",
    // Parallel ping sweep of /24
    "for i in $(seq 1 254); do (ping -c1 -W1 10.1.16.$i >/dev/null 2>&1 && echo \"ALIVE:10.1.16.$i\") & done; wait 2>/dev/null",
    "echo '---PING_END---'",
    "ip neigh show 2>/dev/null",
  ].join('; '), 60);
  RESULTS.scans.network_map.sweep = sweepResult;
  
  const aliveHosts = (sweepResult.match(/ALIVE:[\d.]+/g) || []).map(h => h.replace('ALIVE:', ''));
  log(`  Alive hosts found: ${aliveHosts.length}`);
  for (const h of aliveHosts.slice(0, 30)) log(`    ${h}`);
  
  // Scan other common subnets
  log('  Probing other subnets...');
  const subnetProbe = await sh([
    "for subnet in 10.1.0 10.1.1 10.1.2 10.1.8 10.1.32 10.1.64 172.16.0 172.16.52 172.22.132 192.168.1 192.168.50; do",
    "  (ping -c1 -W1 ${subnet}.1 >/dev/null 2>&1 && echo \"GW_ALIVE:${subnet}.1\") &",
    "  (ping -c1 -W1 ${subnet}.11 >/dev/null 2>&1 && echo \"HOST_ALIVE:${subnet}.11\") &",
    "done",
    "wait 2>/dev/null",
    "echo SUBNET_PROBE_DONE",
  ].join('\n'), 30);
  RESULTS.scans.network_map.subnet_probe = subnetProbe;
  
  const gwAlive = (subnetProbe.match(/GW_ALIVE:[\d.]+/g) || []).map(h => h.replace('GW_ALIVE:', ''));
  const hostAlive = (subnetProbe.match(/HOST_ALIVE:[\d.]+/g) || []).map(h => h.replace('HOST_ALIVE:', ''));
  log(`  Reachable gateways: ${gwAlive.join(', ') || 'none'}`);
  log(`  Reachable hosts: ${hostAlive.join(', ') || 'none'}`);

  // Port scan the gateway
  const gateway = await sh("ip route | grep default | awk '{print $3}'", 10);
  log(`  Gateway: ${gateway}`);
  if (gateway && gateway.match(/\d+\.\d+\.\d+\.\d+/)) {
    log(`  Port scanning gateway ${gateway}...`);
    const portScan = await sh([
      `for port in 22 53 80 443 2375 2376 5555 8080 8443 9090 10250 10255; do`,
      `  (echo >/dev/tcp/${gateway.trim()}/$port 2>/dev/null && echo "PORT_OPEN:$port") &`,
      `done`,
      `wait 2>/dev/null`,
      `echo PORT_SCAN_DONE`,
    ].join('\n'), 20);
    RESULTS.scans.network_map.gateway_ports = portScan;
    const openPorts = (portScan.match(/PORT_OPEN:\d+/g) || []).map(p => p.replace('PORT_OPEN:', ''));
    log(`  Gateway open ports: ${openPorts.join(', ') || 'none detected'}`);
  }

  // ═══════════════════════════════════════════════════════════════
  // SCAN 8: INSTALLED APPS & SERVICES
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 8: INSTALLED APPS & RUNNING SERVICES');
  
  const appCmds = {
    'packages_count':  'pm list packages 2>/dev/null | wc -l',
    'google_packages': 'pm list packages 2>/dev/null | grep google | head -20',
    'user_packages':   'pm list packages -3 2>/dev/null | head -20',
    'running_services':'dumpsys activity services 2>/dev/null | grep ServiceRecord | wc -l',
    'running_procs':   'ps -A 2>/dev/null | wc -l; ps -A 2>/dev/null | head -20',
    'top_procs':       'top -n1 -b 2>/dev/null | head -15',
    'accounts':        'dumpsys account 2>/dev/null | grep -E "Account {" | head -10',
    'sensors':         'dumpsys sensorservice 2>/dev/null | grep -E "^0x" | head -15',
    'battery_info':    'dumpsys battery 2>/dev/null',
    'connectivity':    'dumpsys connectivity 2>/dev/null | grep -E "(NetworkInfo|type|state)" | head -10',
  };
  
  RESULTS.scans.apps = {};
  for (const [key, cmd] of Object.entries(appCmds)) {
    const result = await sh(cmd, 20);
    RESULTS.scans.apps[key] = result;
    const lines = result.split('\n');
    log(`  ${key}: ${lines[0].slice(0, 90)}${lines.length > 1 ? ` (+${lines.length-1} lines)` : ''}`);
    await sleep(300);
  }

  // ═══════════════════════════════════════════════════════════════
  // SCAN 9: SENSITIVE DATA & FILES
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 9: SENSITIVE DATA & FILE SYSTEM');
  
  const dataCmds = {
    'data_dirs':       'ls /data/data/ 2>/dev/null | head -30',
    'data_size':       'du -sh /data/ 2>/dev/null | head -5',
    'sdcard':          'ls /sdcard/ 2>/dev/null',
    'downloads':       'ls /sdcard/Download/ 2>/dev/null',
    'accounts_db':     'ls -la /data/system_ce/0/accounts_ce.db* /data/system_de/0/accounts_de.db* 2>/dev/null',
    'wifi_configs':    'cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | head -20 || echo NO_WIFI_CONFIG',
    'keystore':        'ls /data/misc/keystore/ 2>/dev/null | head -10',
    'gms_data':        'ls /data/data/com.google.android.gms/databases/ 2>/dev/null | head -10',
    'chrome_data':     'ls /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null | head -10',
    'wallet_data':     'ls /data/data/com.google.android.apps.walletnfcrel/ 2>/dev/null',
    'tapandpay':       'ls /data/data/com.google.android.gms/databases/tapandpay* 2>/dev/null',
    'env_vars':        'env 2>/dev/null | head -30',
    'tmp_files':       'ls -la /data/local/tmp/ 2>/dev/null',
    'magisk':          'ls -la /data/adb/magisk/ 2>/dev/null; ls /sbin/su /system/bin/su /system/xbin/su 2>/dev/null',
  };
  
  RESULTS.scans.sensitive = {};
  for (const [key, cmd] of Object.entries(dataCmds)) {
    const result = await sh(cmd, 15);
    RESULTS.scans.sensitive[key] = result;
    const lines = result.split('\n');
    log(`  ${key}: ${lines[0].slice(0, 90)}${lines.length > 1 ? ` (+${lines.length-1} lines)` : ''}`);
    await sleep(300);
  }

  // ═══════════════════════════════════════════════════════════════
  // SCAN 10: TOOL INSTALLATION & ADVANCED PROBING
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 10: ADVANCED PROBING (busybox, proc)');
  
  // Check what tools are available
  const toolCheck = await sh([
    'echo "--- Available Tools ---"',
    'which busybox 2>/dev/null && busybox --list 2>/dev/null | head -20 || echo "no busybox"',
    'which curl wget nmap nc ncat socat 2>/dev/null',
    'which sqlite3 2>/dev/null',
    'which python3 python 2>/dev/null',
    'which toybox 2>/dev/null && toybox --help 2>/dev/null | head -5',
    'echo "--- /system/bin tools ---"',
    'ls /system/bin/ 2>/dev/null | wc -l',
    'echo "--- /system/xbin tools ---"',
    'ls /system/xbin/ 2>/dev/null | wc -l',
  ].join('\n'), 20);
  RESULTS.scans.tools = toolCheck;
  log('  Available tools:');
  for (const line of toolCheck.split('\n').slice(0, 15)) log(`    ${line}`);

  // Deep /proc exploration
  log('  Deep /proc exploration...');
  const procDeep = await sh([
    'echo "=== /proc/self/status ==="',
    'cat /proc/self/status 2>/dev/null | head -20',
    'echo "=== /proc/self/limits ==="', 
    'cat /proc/self/limits 2>/dev/null',
    'echo "=== /proc/net/tcp ==="',
    'cat /proc/net/tcp 2>/dev/null | head -15',
    'echo "=== /proc/net/udp ==="',
    'cat /proc/net/udp 2>/dev/null | head -10',
    'echo "=== /proc/net/unix ==="',
    'cat /proc/net/unix 2>/dev/null | wc -l',
    'echo "=== /proc/buddyinfo ==="',
    'cat /proc/buddyinfo 2>/dev/null',
  ].join('\n'), 20);
  RESULTS.scans.proc_deep = procDeep;
  for (const line of procDeep.split('\n').slice(0, 10)) log(`    ${line}`);

  // ═══════════════════════════════════════════════════════════════
  // SCAN 11: CROSS-DEVICE MAPPING (both pads)
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 11: CROSS-DEVICE MAPPING (all cloud devices)');
  
  log('  Querying all VMOS cloud instances...');
  const allDevices = devList.map(d => ({
    padCode: d.padCode,
    status: d.padStatus,
    ip: d.deviceIp,
    image: d.imageVersion,
    type: d.padType,
    grade: d.padGrade,
    cluster: d.clusterCode,
    adb: d.adbOpenStatus,
    created: d.createTime,
  }));
  RESULTS.scans.all_devices = allDevices;
  
  for (const d of allDevices) {
    log(`  Device: ${d.padCode}`);
    log(`    Status: ${d.status} | IP: ${d.ip} | Image: ${d.image}`);
    log(`    Cluster: ${d.cluster} | Type: ${d.type} | Grade: ${d.grade}`);
    
    // Try to reach other device from our device
    if (d.ip && d.padCode !== PAD_CODE) {
      log(`    Probing ${d.ip} from our container...`);
      const probe = await sh(`ping -c2 -W2 ${d.ip} 2>/dev/null && echo REACHABLE || echo UNREACHABLE; echo "---"; (echo >/dev/tcp/${d.ip}/5555 2>/dev/null && echo ADB_PORT_OPEN || echo ADB_CLOSED)`, 15);
      RESULTS.scans.cross_device_probe = probe;
      for (const line of probe.split('\n')) {
        if (line.trim()) log(`      ${line.trim()}`);
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // SCAN 12: SECURITY POSTURE
  // ═══════════════════════════════════════════════════════════════
  section('SCAN 12: SECURITY POSTURE ASSESSMENT');
  
  const secCmds = {
    'selinux_mode':     'getenforce 2>/dev/null',
    'selinux_policy':   'cat /sys/fs/selinux/policyvers 2>/dev/null',
    'selinux_contexts': 'ls -Z /system/bin/sh /data 2>/dev/null',
    'verity':           'getprop ro.boot.veritymode 2>/dev/null',
    'dm_verity':        'getprop ro.boot.vbmeta.device_state 2>/dev/null',
    'secureboot':       'getprop ro.boot.secureboot 2>/dev/null',
    'debuggable':       'getprop ro.debuggable',
    'usb_debug':        'getprop persist.sys.usb.config 2>/dev/null; settings get global adb_enabled 2>/dev/null',
    'crypto':           'getprop ro.crypto.state 2>/dev/null',
    'keymaster':        'getprop ro.hardware.keystore 2>/dev/null',
    'play_integrity':   'dumpsys package com.google.android.gms 2>/dev/null | grep -i "integrity\\|safetynet" | head -5',
  };
  
  RESULTS.scans.security = {};
  for (const [key, cmd] of Object.entries(secCmds)) {
    const result = await sh(cmd, 15);
    RESULTS.scans.security[key] = result;
    log(`  ${key}: ${result.split('\n')[0].slice(0, 80)}`);
    await sleep(200);
  }

  // ═══════════════════════════════════════════════════════════════
  // SAVE REPORT
  // ═══════════════════════════════════════════════════════════════
  section('SCAN COMPLETE — SAVING REPORT');
  
  const reportFile = `${path.join(__dirname, '..', 'reports')}/DEEP_SCAN_${PAD_CODE}_${Date.now()}.json`;
  fs.writeFileSync(reportFile, JSON.stringify(RESULTS, null, 2));
  log(`Report saved: ${reportFile}`);

  // ═══════════════════════════════════════════════════════════════
  // SUMMARY
  // ═══════════════════════════════════════════════════════════════
  section('EXECUTIVE SUMMARY');
  
  const hw = RESULTS.scans.hardware;
  const sp = RESULTS.scans.spoofed;
  const esc = RESULTS.scans.escape;
  
  console.log(`
  TARGET:      ${PAD_CODE}
  REAL HARDWARE:
    SoC:       ${(hw.soc || '').split('\n')[0] || 'unknown'}
    Board:     ${(hw.device_tree || '').split('\n')[0] || 'unknown'}
    GPU:       ${(hw.gpu_real || '').split('\n')[0] || 'unknown'}
    Kernel:    ${(hw.kernel || '').split('\n')[0].slice(0, 80) || 'unknown'}
    Cloud ID:  ${hw.cloud_id || 'unknown'}
    Server:    ${hw.cloud_server || 'unknown'}
    Cluster:   ${hw.boot_cluster || 'unknown'}
  
  SPOOFED AS:
    ${sp.brand} ${sp.model} (${sp.device})
    Android ${sp.android_ver} SDK ${sp.sdk}
    Fingerprint: ${(sp.fingerprint || '').slice(0, 60)}...
    IMEI: ${sp.imei || 'none'}
    Serial: ${sp.serial || 'none'}
    Carrier: ${sp.carrier} (${sp.sim_numeric})
    GPU: ${sp.gpu_renderer}
  
  CONTAINER:
    UID:       ${(esc.whoami || '').split('\n')[0]}
    Kernel:    ${(esc.kernel_ver || '').slice(0, 60)}
    SELinux:   ${RESULTS.scans.security?.selinux_mode || 'unknown'}
    Processes: ${esc.host_procs || 'unknown'}
    PID 1:     ${esc.proc_1_exe || 'unknown'}
    
  NETWORK:
    Our IP:    ${myIp}
    Gateway:   ${gateway}
    Alive hosts: ${aliveHosts.length}
    Devices:   ${allDevices.length} total in cloud
    
  SECURITY:
    Root:      ${(esc.whoami || '').includes('uid=0') ? 'YES (uid=0)' : 'NO'}
    Write:     ${(esc.root_test || '').includes('ROOT_WRITE_OK') ? 'YES' : 'NO'}
    Debuggable:${RESULTS.scans.security?.debuggable || 'unknown'}
    Verified:  ${sp.verified_boot || 'unknown'}
`);
  
  console.log('═'.repeat(70));
  console.log(`  Report: ${reportFile}`);
  console.log('═'.repeat(70));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
