#!/usr/bin/env node
/**
 * Install Russian apps on D2 + extract & restore data from .220
 * Strategy: 
 *  - APKs: syncCmd on D2 to download via curl from APK mirrors
 *  - Data: raw ADB + base64 from .220, then adb push to D2
 */
const { execSync } = require('child_process');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');
const D1_SERIAL = 'localhost:8479';
const D2_SERIAL = 'localhost:7391';
const D2_PAD = 'ACP251008GUOEEHB';
const D1_IP = '10.0.96.174';
const SRC_IP = '10.0.26.220';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');

const APPS = [
  'com.yandex.bank', 'ru.ozon.app.android', 'ru.ozon.fintech.finance',
  'com.wildberries.ru', 'ru.yandex.taxi', 'ru.yoo.money', 'ru.cupis.wallet',
  'ru.apteka', 'ru.getpharma.eapteka', 'ru.rostel', 'ru.vk.store',
  'com.app.trademo', 'com.trademo.massmo'
];

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d) { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); return d; }

// ═══════════════════════════════════════════════════════════════
// VMOS Cloud API
// ═══════════════════════════════════════════════════════════════
function sign(b){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z'),sd=xd.slice(0,8),CT='application/json;charset=UTF-8',SHD='content-type;host;x-content-sha256;x-date';const bh=crypto.createHash('sha256').update(b,'utf8').digest('hex');const can=`host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;const ch=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=`HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;let k=crypto.createHmac('sha256',SK).update(sd).digest();k=crypto.createHmac('sha256',k).update('armcloud-paas').digest();k=crypto.createHmac('sha256',k).update('request').digest();return{'content-type':CT,'x-date':xd,'x-host':HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256',k).update(sts).digest('hex')}`};}

function apiPost(ep,d,t){return new Promise(ok=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b);const req=https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(t||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}

// ═══════════════════════════════════════════════════════════════
// ADB helpers for .220
// ═══════════════════════════════════════════════════════════════
function buildOpen(cmd) {
  const p = Buffer.from('shell:' + cmd + '\x00');
  const h = Buffer.alloc(24);
  h.writeUInt32LE(0x4e45504f, 0); h.writeUInt32LE(1, 4); h.writeUInt32LE(0, 8);
  h.writeUInt32LE(p.length, 12);
  let c = 0; for (const b of p) c += b;
  h.writeUInt32LE(c >>> 0, 16);
  h.writeUInt32LE((0x4e45504f ^ 0xFFFFFFFF) >>> 0, 20);
  return Buffer.concat([h, p]);
}

// Run on .220 via D1 raw ADB — returns first ~4KB text
function runOn220(cmd, waitSec) {
  waitSec = waitSec || 3;
  const open = buildOpen(cmd);
  fs.writeFileSync('/tmp/adb_open_tmp.bin', open);
  execSync(`adb -s ${D1_SERIAL} push /tmp/adb_open_tmp.bin /sdcard/open_tmp.bin 2>/dev/null`, { timeout: 10000 });

  const script = `(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_tmp.bin; sleep ${waitSec}) | nc -w ${waitSec + 2} ${SRC_IP} 5555 2>/dev/null | strings`;
  fs.writeFileSync('/tmp/d1_run.sh', script);
  execSync(`adb -s ${D1_SERIAL} push /tmp/d1_run.sh /sdcard/run.sh 2>/dev/null`, { timeout: 10000 });

  try {
    const raw = execSync(`adb -s ${D1_SERIAL} shell sh /sdcard/run.sh`, {
      timeout: (waitSec + 10) * 1000, encoding: 'utf8', maxBuffer: 5 * 1024 * 1024
    });
    return raw.split('\n').filter(l => !l.match(/^(CNXN|OKAY|WRTE|CLSE|device::)/)).join('\n').trim();
  } catch (e) { return ''; }
}

// Extract small file from .220 via base64 (< ~3KB files)
function extractFile220(remotePath) {
  const out = runOn220(`base64 "${remotePath}" 2>/dev/null`, 5);
  if (out.length < 10) return null;
  // Clean base64 — remove any non-base64 chars
  const clean = out.replace(/[^A-Za-z0-9+/=\n]/g, '').replace(/\n/g, '');
  try {
    return Buffer.from(clean, 'base64');
  } catch (e) { return null; }
}

// ═══════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(60));
  console.log('  Install Apps on D2 + Restore Data from .220');
  console.log('═'.repeat(60));

  ensureDir(OUT);
  ensureDir(path.join(OUT, 'data'));

  // Ensure cnxn.bin on D1
  fs.writeFileSync('/tmp/adb_cnxn.bin',
    Buffer.from('434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex'));
  execSync(`adb -s ${D1_SERIAL} push /tmp/adb_cnxn.bin /sdcard/cnxn.bin 2>/dev/null`);

  // ════════════════════════════════════════════════════════════
  // STEP 1: Install APKs on D2 using syncCmd + pm install from .220
  // Strategy: Have D2 pull APKs from .220 directly if possible,
  // or use installApp API
  // ════════════════════════════════════════════════════════════
  log('\nSTEP 1: Installing APKs on D2...');

  // First try: VMOS installApp API with a test
  log('  Testing installApp API...');
  const testInstall = await apiPost('/vcpcloud/api/padApi/installApp', {
    padCodes: [D2_PAD],
    appUrl: 'https://apk.support/apk-downloader?package=com.yandex.bank'
  });
  log(`  installApp response: ${JSON.stringify(testInstall).slice(0, 150)}`);

  // Check if D2 has curl/wget
  const curlCheck = await syncCmd(D2_PAD, 'which curl wget 2>/dev/null; curl --version 2>/dev/null | head -1', 10);
  log(`  D2 tools: ${curlCheck.slice(0, 100)}`);

  // Check D2 network — can it reach the internet?
  const netCheck = await syncCmd(D2_PAD, 'ping -c 1 -W 3 8.8.8.8 2>&1 | tail -1', 10);
  log(`  D2 network: ${netCheck.slice(0, 80)}`);

  // Check if D2 can reach .220 directly
  const d2to220 = await syncCmd(D2_PAD, `nc -w 3 ${SRC_IP} 5555 < /dev/null 2>&1; echo EXIT=$?`, 10);
  log(`  D2 → .220 connectivity: ${d2to220.slice(0, 80)}`);

  // Alternative: use pm install from D2 if it has APK download capability
  // Or: use D2 syncCmd to install from Google Play (if logged in)
  
  // Let's try installing apps via the installApp API with apkpure URLs
  // APKPure direct download URLs format: https://d.apkpure.com/b/APK/PACKAGE
  log('\n  Installing apps via VMOS installApp API...');
  
  for (const pkg of APPS) {
    // Try installApp API
    const r = await apiPost('/vcpcloud/api/padApi/installApp', {
      padCodes: [D2_PAD],
      appUrl: `https://d.apkpure.net/b/APK/${pkg}?version=latest`,
    });
    
    if (r.code === 200) {
      log(`  ✓ ${pkg}: task submitted (taskId: ${JSON.stringify(r.data).slice(0, 50)})`);
    } else {
      log(`  ✗ ${pkg}: ${r.msg || r.code}`);
    }
    await sleep(1000);
  }

  // Wait for installs to complete
  log('\n  Waiting 30s for installs...');
  await sleep(30000);

  // Check what got installed on D2
  const installed = await syncCmd(D2_PAD, 'pm list packages -3 2>/dev/null | sort', 15);
  log(`  D2 installed packages:\n${installed}`);

  // ════════════════════════════════════════════════════════════
  // STEP 2: Extract app data from .220 (databases + shared_prefs)
  // Only small files that fit in ~4KB raw ADB output
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 2: Extracting app data from .220...');

  for (const pkg of APPS) {
    const appDir = ensureDir(path.join(OUT, 'data', pkg));

    // List databases
    const dbList = runOn220(`ls /data/data/${pkg}/databases/ 2>/dev/null`, 3);
    const dbs = dbList.split('\n').filter(l => l.trim() && l.trim().endsWith('.db'));

    if (dbs.length > 0) {
      ensureDir(path.join(appDir, 'databases'));
      for (const db of dbs.slice(0, 5)) {
        const dbName = db.trim();
        // Get size first
        const sizeOut = runOn220(`wc -c /data/data/${pkg}/databases/${dbName} 2>/dev/null`, 3);
        const sizeMatch = sizeOut.match(/(\d+)/);
        const size = sizeMatch ? parseInt(sizeMatch[1]) : 0;

        if (size > 0 && size < 3000) {
          // Small enough for one-shot base64
          const data = extractFile220(`/data/data/${pkg}/databases/${dbName}`);
          if (data) {
            fs.writeFileSync(path.join(appDir, 'databases', dbName), data);
            log(`    ✓ ${pkg}/db/${dbName}: ${data.length}B`);
          }
        } else if (size >= 3000) {
          log(`    ⚠ ${pkg}/db/${dbName}: ${size}B (too large for one-shot, skipping)`);
        }
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
        const sizeOut = runOn220(`wc -c /data/data/${pkg}/shared_prefs/${prefName} 2>/dev/null`, 3);
        const sizeMatch = sizeOut.match(/(\d+)/);
        const size = sizeMatch ? parseInt(sizeMatch[1]) : 0;

        if (size > 0 && size < 3000) {
          const data = extractFile220(`/data/data/${pkg}/shared_prefs/${prefName}`);
          if (data) {
            fs.writeFileSync(path.join(appDir, 'shared_prefs', prefName), data);
            log(`    ✓ ${pkg}/prefs/${prefName}: ${data.length}B`);
          }
        } else if (size >= 3000) {
          log(`    ⚠ ${pkg}/prefs/${prefName}: ${size}B (too large)`);
        }
        await sleep(300);
      }
    }
    log(`  ${pkg}: done`);
  }

  // ════════════════════════════════════════════════════════════
  // STEP 3: Push extracted data to D2 via ADB
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 3: Pushing data to D2 via ADB...');

  const dataDir = path.join(OUT, 'data');
  for (const pkg of fs.readdirSync(dataDir)) {
    const pkgDir = path.join(dataDir, pkg);
    if (!fs.statSync(pkgDir).isDirectory()) continue;

    let pushed = 0;

    // Stop app first
    try { execSync(`adb -s ${D2_SERIAL} shell am force-stop ${pkg} 2>/dev/null`, { timeout: 5000 }); } catch (e) {}

    // Push databases
    const dbDir = path.join(pkgDir, 'databases');
    if (fs.existsSync(dbDir)) {
      try { execSync(`adb -s ${D2_SERIAL} shell mkdir -p /data/data/${pkg}/databases 2>/dev/null`, { timeout: 5000 }); } catch (e) {}
      for (const db of fs.readdirSync(dbDir)) {
        const f = path.join(dbDir, db);
        if (fs.statSync(f).size < 10) continue;
        try {
          execSync(`adb -s ${D2_SERIAL} push "${f}" "/data/data/${pkg}/databases/${db}" 2>/dev/null`, { timeout: 15000 });
          pushed++;
        } catch (e) {}
      }
    }

    // Push shared_prefs
    const prefsDir = path.join(pkgDir, 'shared_prefs');
    if (fs.existsSync(prefsDir)) {
      try { execSync(`adb -s ${D2_SERIAL} shell mkdir -p /data/data/${pkg}/shared_prefs 2>/dev/null`, { timeout: 5000 }); } catch (e) {}
      for (const pref of fs.readdirSync(prefsDir)) {
        const f = path.join(prefsDir, pref);
        if (fs.statSync(f).size < 10) continue;
        try {
          execSync(`adb -s ${D2_SERIAL} push "${f}" "/data/data/${pkg}/shared_prefs/${pref}" 2>/dev/null`, { timeout: 15000 });
          pushed++;
        } catch (e) {}
      }
    }

    // Fix ownership
    if (pushed > 0) {
      try {
        const uid = execSync(`adb -s ${D2_SERIAL} shell "stat -c %u /data/data/${pkg} 2>/dev/null"`, {
          timeout: 5000, encoding: 'utf8'
        }).trim();
        if (uid.match(/^\d+$/)) {
          execSync(`adb -s ${D2_SERIAL} shell "chown -R ${uid}:${uid} /data/data/${pkg}/databases /data/data/${pkg}/shared_prefs 2>/dev/null"`, { timeout: 10000 });
        }
      } catch (e) {}
      log(`  ${pkg}: ${pushed} files pushed`);
    }
  }

  // Account refresh
  try {
    execSync(`adb -s ${D2_SERIAL} shell "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED" 2>/dev/null`, { timeout: 10000 });
    log('  Account refresh sent');
  } catch (e) {}

  // ════════════════════════════════════════════════════════════
  // STEP 4: Proxy
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 4: Setting up proxy...');
  const existing = await apiPost('/vcpcloud/api/padApi/queryProxyList', { page: 1, rows: 10 });
  const proxies = existing?.data?.records || [];
  
  if (proxies.length > 0) {
    const p = proxies[0];
    log(`  Using proxy: ${p.proxyHost}:${p.proxyPort} (${p.proxyCountry})`);
    const r = await apiPost('/vcpcloud/api/padApi/setProxy', {
      padCodes: [D2_PAD], proxyType: 'proxy',
      proxyName: p.proxyName || 'socks5',
      proxyIp: p.proxyHost, proxyPort: p.proxyPort,
      proxyUser: p.username || '', proxyPassword: p.password || '',
    });
    log(`  setProxy: code=${r.code}`);
  } else {
    log('  No proxies available');
  }

  console.log('\n' + '═'.repeat(60));
  console.log('  DONE');
  console.log('═'.repeat(60));
}

main().catch(e => console.error('FATAL:', e));
