#!/usr/bin/env node
/**
 * Install apps on D2 using multiple strategies:
 * 1. Test D2 → .220 connectivity (direct ADB pull if reachable)
 * 2. Download APKs via D2's curl from internet
 * 3. Extract + push app data from .220 via raw ADB base64
 * 4. Set proxy
 */
const { execSync } = require('child_process');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, D2, CT, SHD } = require('../shared/vmos_api');
const D1_SERIAL = 'localhost:8479';
const D2_SERIAL = 'localhost:7391';
const D2_PAD = 'ACP251008GUOEEHB';
const SRC_IP = '10.0.26.220';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');

const APPS = {
  'com.yandex.bank': 'Yandex Bank',
  'ru.ozon.app.android': 'Ozon',
  'ru.ozon.fintech.finance': 'Ozon Fintech',
  'com.wildberries.ru': 'Wildberries',
  'ru.yandex.taxi': 'Yandex Go',
  'ru.yoo.money': 'YooMoney',
  'ru.cupis.wallet': 'Cupis Wallet',
  'ru.apteka': 'Apteka.ru',
  'ru.getpharma.eapteka': 'eApteka',
  'ru.rostel': 'Rostel',
  'ru.vk.store': 'RuStore',
  'com.app.trademo': 'Trademo',
  'com.trademo.massmo': 'Massmo',
};

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
function ensureDir(d) { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); }

// ═══════════════════════════════════════════════════════════════
// API helpers
// ═══════════════════════════════════════════════════════════════
function sign(b){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z'),sd=xd.slice(0,8),CT='application/json;charset=UTF-8',SHD='content-type;host;x-content-sha256;x-date';const bh=crypto.createHash('sha256').update(b,'utf8').digest('hex');const can=`host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;const ch=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=`HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;let k=crypto.createHmac('sha256',SK).update(sd).digest();k=crypto.createHmac('sha256',k).update('armcloud-paas').digest();k=crypto.createHmac('sha256',k).update('request').digest();return{'content-type':CT,'x-date':xd,'x-host':HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256',k).update(sts).digest('hex')}`};}
function apiPost(ep,d,t){return new Promise(ok=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b);const req=https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(t||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}

// ═══════════════════════════════════════════════════════════════
// .220 ADB helpers
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

// ═══════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(60));
  console.log('  CLONE .220 → D2');
  console.log('═'.repeat(60));

  ensureDir(OUT);

  // Verify tunnels
  try {
    execSync(`adb -s ${D1_SERIAL} shell echo D1_OK`, { timeout: 5000 });
    execSync(`adb -s ${D2_SERIAL} shell echo D2_OK`, { timeout: 5000 });
    log('ADB tunnels OK');
  } catch (e) { log('ERROR: tunnel(s) down'); process.exit(1); }

  // Ensure cnxn.bin
  fs.writeFileSync('/tmp/adb_cnxn.bin',
    Buffer.from('434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex'));
  execSync(`adb -s ${D1_SERIAL} push /tmp/adb_cnxn.bin /sdcard/cnxn.bin 2>/dev/null`);

  // ════════════════════════════════════════════════════════════
  // STEP 0: Check D2 → .220 connectivity
  // ════════════════════════════════════════════════════════════
  log('\nSTEP 0: Network check...');

  // D2 IP and subnet
  let d2Ip = '';
  try {
    d2Ip = execSync(`adb -s ${D2_SERIAL} shell "ip route show | head -3"`, {
      timeout: 10000, encoding: 'utf8'
    }).trim();
    log(`  D2 routes: ${d2Ip}`);
  } catch (e) {}

  // D2 → .220 connectivity
  let d2Can220 = false;
  try {
    const r = execSync(`adb -s ${D2_SERIAL} shell "echo test | nc -w 3 ${SRC_IP} 5555 2>&1; echo EXIT_CODE=\\$?"`, {
      timeout: 15000, encoding: 'utf8'
    }).trim();
    d2Can220 = r.includes('EXIT_CODE=0');
    log(`  D2 → .220: ${d2Can220 ? '✓ REACHABLE' : '✗ unreachable'}`);
  } catch (e) { log('  D2 → .220: ✗ unreachable (timeout)'); }

  // ════════════════════════════════════════════════════════════
  // STEP 1: Install APKs on D2
  // ════════════════════════════════════════════════════════════
  log('\nSTEP 1: Installing APKs...');

  const installed = [];

  if (d2Can220) {
    // D2 can reach .220! Use D2 to pull APKs directly from .220 via raw ADB
    log('  Strategy: D2 pulls APKs directly from .220');

    // Get APK paths from .220
    const apkPaths = runOn220('pm list packages -f -3 2>/dev/null', 5);
    log(`  APK paths from .220:\n${apkPaths}`);

    // For each app, have D2 connect to .220:5555 and pull APK
    // D2 has nc and curl, so we can use raw ADB from D2
    for (const pkg of Object.keys(APPS)) {
      const pathMatch = apkPaths.match(new RegExp(`package:(.+?)=${pkg}`));
      if (!pathMatch) { log(`    ${pkg}: path not found`); continue; }
      const apkPath = pathMatch[1];

      // Build ADB packets for D2 to send to .220
      const catCmd = `cat "${apkPath}" 2>/dev/null | base64`;
      // This won't work for large files... skip for now
      log(`    ${pkg}: ${apkPath} (will try internet download)`);
    }
  }

  // Internet download strategy
  log('  Strategy: Download APKs from internet via D2 curl');

  // First verify curl works on D2 with a known URL
  const curlTest = await syncCmd(D2_PAD, 
    'curl -s -L -o /dev/null -w "code:%{http_code} size:%{size_download}" "https://www.google.com" --connect-timeout 10 --max-time 15', 20);
  log(`  D2 curl test: ${curlTest}`);

  // APK download sources - try multiple for each app
  const APK_SOURCES = {
    'ru.vk.store': [
      'https://static.rustore.ru/apk/RuStore.apk',
      'https://www.rustore.ru/download',
    ],
  };

  // For each app, try to install via syncCmd
  for (const [pkg, name] of Object.entries(APPS)) {
    // Check if already installed
    const check = await syncCmd(D2_PAD, `pm path ${pkg} 2>/dev/null`, 5);
    if (check.includes('package:')) {
      log(`  ✓ ${pkg} already installed`);
      installed.push(pkg);
      continue;
    }

    // Strategy A: Try RuStore download first (for ru.vk.store)
    if (pkg === 'ru.vk.store') {
      const dlResult = await syncCmd(D2_PAD, [
        'cd /data/local/tmp',
        'rm -f rustore.apk',
        'curl -s -L -o rustore.apk "https://static.rustore.ru/apk/RuStore.apk" --connect-timeout 15 --max-time 120',
        'ls -la rustore.apk 2>/dev/null',
        'pm install -r -g rustore.apk 2>&1',
        'rm -f rustore.apk',
      ].join('; '), 150);
      if (dlResult.includes('Success')) {
        log(`  ✓ ${pkg} installed via RuStore direct`);
        installed.push(pkg);
        continue;
      } else {
        log(`  ✗ ${pkg} RuStore: ${dlResult.slice(0, 80)}`);
      }
    }

    // Strategy B: Try APKPure API
    const apkPureResult = await syncCmd(D2_PAD, [
      'cd /data/local/tmp',
      `rm -f ${pkg}.apk`,
      // APKPure has a CDN; try the direct format
      `curl -s -L -o ${pkg}.apk "https://d.apkpure.net/b/APK/${pkg}?versionCode=latest" -H "User-Agent: APKPure/3.17" --connect-timeout 15 --max-time 180`,
      `SIZE=$(wc -c < ${pkg}.apk 2>/dev/null)`,
      `echo "DL_SIZE=$SIZE"`,
      `if [ "$SIZE" -gt 100000 ]; then pm install -r -g ${pkg}.apk 2>&1; else echo "too_small"; fi`,
      `rm -f ${pkg}.apk`,
    ].join('; '), 200);
    
    if (apkPureResult.includes('Success')) {
      log(`  ✓ ${pkg} installed via APKPure`);
      installed.push(pkg);
      continue;
    }
    
    // Strategy C: Try apkcombo
    const apkComboResult = await syncCmd(D2_PAD, [
      'cd /data/local/tmp',
      `rm -f ${pkg}.apk`,
      `curl -s -L -o ${pkg}.apk "https://apkcombo.com/api/download/apk/${pkg}" -H "User-Agent: Mozilla/5.0" --connect-timeout 15 --max-time 180`,
      `SIZE=$(wc -c < ${pkg}.apk 2>/dev/null)`,
      `echo "DL_SIZE=$SIZE"`,
      `if [ "$SIZE" -gt 100000 ]; then pm install -r -g ${pkg}.apk 2>&1; else echo "too_small"; fi`,
      `rm -f ${pkg}.apk`,
    ].join('; '), 200);
    
    if (apkComboResult.includes('Success')) {
      log(`  ✓ ${pkg} installed via APKCombo`);
      installed.push(pkg);
      continue;
    }

    log(`  ✗ ${pkg}: internet download failed (APKPure: ${apkPureResult.slice(0, 50)}, APKCombo: ${apkComboResult.slice(0, 50)})`);
  }

  // Strategy D: Install RuStore first, then use it to install other apps
  if (installed.includes('ru.vk.store') && installed.length < Object.keys(APPS).length) {
    log('\n  RuStore installed - other apps may need manual install via RuStore');
  }

  log(`\n  APKs installed: ${installed.length}/${Object.keys(APPS).length}`);
  const missing = Object.keys(APPS).filter(p => !installed.includes(p));
  if (missing.length > 0) {
    log(`  Missing: ${missing.join(', ')}`);
  }

  // ════════════════════════════════════════════════════════════
  // STEP 2: Extract app data from .220 (small files via base64)
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 2: Extracting app data from .220...');

  ensureDir(path.join(OUT, 'data'));
  let totalExtracted = 0;

  for (const pkg of Object.keys(APPS)) {
    const appDir = path.join(OUT, 'data', pkg);
    ensureDir(appDir);
    let fileCount = 0;

    // Get database list with sizes
    const dbListRaw = runOn220(`ls -la /data/data/${pkg}/databases/ 2>/dev/null`, 3);
    const dbFiles = dbListRaw.split('\n')
      .map(l => {
        const m = l.match(/\s(\d+)\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+(.+\.db)$/);
        return m ? { name: m[2], size: parseInt(m[1]) } : null;
      })
      .filter(Boolean)
      .filter(d => d.size > 0 && d.size < 3000);

    if (dbFiles.length > 0) {
      ensureDir(path.join(appDir, 'databases'));
      for (const db of dbFiles.slice(0, 5)) {
        const b64 = runOn220(`base64 "/data/data/${pkg}/databases/${db.name}" 2>/dev/null`, 5);
        if (b64.length > 10) {
          const clean = b64.replace(/[^A-Za-z0-9+/=\n]/g, '').replace(/\n/g, '');
          try {
            const buf = Buffer.from(clean, 'base64');
            if (buf.length > 10) {
              fs.writeFileSync(path.join(appDir, 'databases', db.name), buf);
              fileCount++;
            }
          } catch (e) {}
        }
      }
    }

    // Get shared_prefs list with sizes
    const prefListRaw = runOn220(`ls -la /data/data/${pkg}/shared_prefs/ 2>/dev/null`, 3);
    const prefFiles = prefListRaw.split('\n')
      .map(l => {
        const m = l.match(/\s(\d+)\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+(.+\.xml)$/);
        return m ? { name: m[2], size: parseInt(m[1]) } : null;
      })
      .filter(Boolean)
      .filter(p => p.size > 0 && p.size < 3000);

    if (prefFiles.length > 0) {
      ensureDir(path.join(appDir, 'shared_prefs'));
      for (const pref of prefFiles.slice(0, 10)) {
        const b64 = runOn220(`base64 "/data/data/${pkg}/shared_prefs/${pref.name}" 2>/dev/null`, 5);
        if (b64.length > 10) {
          const clean = b64.replace(/[^A-Za-z0-9+/=\n]/g, '').replace(/\n/g, '');
          try {
            const buf = Buffer.from(clean, 'base64');
            if (buf.length > 10) {
              fs.writeFileSync(path.join(appDir, 'shared_prefs', pref.name), buf);
              fileCount++;
            }
          } catch (e) {}
        }
      }
    }

    totalExtracted += fileCount;
    if (fileCount > 0) log(`  ${pkg}: ${fileCount} files`);
    else log(`  ${pkg}: no small extractable files`);
  }

  log(`  Total extracted: ${totalExtracted} files`);

  // Also extract account databases from .220
  log('\n  Extracting account databases...');
  for (const dbName of ['accounts_ce.db', 'accounts_de.db']) {
    const b64 = runOn220(`base64 /data/system_ce/0/${dbName} 2>/dev/null`, 5);
    if (b64.length > 10) {
      const clean = b64.replace(/[^A-Za-z0-9+/=\n]/g, '').replace(/\n/g, '');
      try {
        const buf = Buffer.from(clean, 'base64');
        ensureDir(path.join(OUT, 'accounts'));
        fs.writeFileSync(path.join(OUT, 'accounts', dbName), buf);
        log(`    ✓ ${dbName}: ${buf.length}B`);
      } catch (e) {}
    }
  }

  // ════════════════════════════════════════════════════════════
  // STEP 3: Push data to D2
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 3: Pushing data to D2...');

  let totalPushed = 0;
  const dataDir = path.join(OUT, 'data');

  for (const pkg of fs.readdirSync(dataDir)) {
    const pkgDir = path.join(dataDir, pkg);
    if (!fs.statSync(pkgDir).isDirectory()) continue;

    // Check if app is installed on D2
    try {
      const check = execSync(`adb -s ${D2_SERIAL} shell "pm path ${pkg}" 2>/dev/null`, {
        timeout: 5000, encoding: 'utf8'
      });
      if (!check.includes('package:')) continue;
    } catch (e) { continue; }

    // Stop app
    try { execSync(`adb -s ${D2_SERIAL} shell "am force-stop ${pkg}" 2>/dev/null`, { timeout: 5000 }); } catch (e) {}

    let pushed = 0;

    // Push databases
    const dbDir = path.join(pkgDir, 'databases');
    if (fs.existsSync(dbDir)) {
      execSync(`adb -s ${D2_SERIAL} shell "mkdir -p /data/data/${pkg}/databases" 2>/dev/null`, { timeout: 5000 });
      for (const f of fs.readdirSync(dbDir)) {
        const fp = path.join(dbDir, f);
        if (fs.statSync(fp).size < 10) continue;
        try {
          execSync(`adb -s ${D2_SERIAL} push "${fp}" "/data/data/${pkg}/databases/${f}" 2>/dev/null`, { timeout: 15000 });
          pushed++;
        } catch (e) {}
      }
    }

    // Push shared_prefs
    const prefsDir = path.join(pkgDir, 'shared_prefs');
    if (fs.existsSync(prefsDir)) {
      execSync(`adb -s ${D2_SERIAL} shell "mkdir -p /data/data/${pkg}/shared_prefs" 2>/dev/null`, { timeout: 5000 });
      for (const f of fs.readdirSync(prefsDir)) {
        const fp = path.join(prefsDir, f);
        if (fs.statSync(fp).size < 10) continue;
        try {
          execSync(`adb -s ${D2_SERIAL} push "${fp}" "/data/data/${pkg}/shared_prefs/${f}" 2>/dev/null`, { timeout: 15000 });
          pushed++;
        } catch (e) {}
      }
    }

    // Fix ownership
    if (pushed > 0) {
      try {
        const uid = execSync(`adb -s ${D2_SERIAL} shell "stat -c %u /data/data/${pkg}" 2>/dev/null`, {
          timeout: 5000, encoding: 'utf8'
        }).trim();
        if (/^\d+$/.test(uid)) {
          execSync(`adb -s ${D2_SERIAL} shell "chown -R ${uid}:${uid} /data/data/${pkg}/databases /data/data/${pkg}/shared_prefs" 2>/dev/null`, { timeout: 10000 });
        }
      } catch (e) {}
      totalPushed += pushed;
      log(`  ${pkg}: ${pushed} files pushed`);
    }
  }

  // Push account databases to D2
  for (const dbName of ['accounts_ce.db', 'accounts_de.db']) {
    const localDb = path.join(OUT, 'accounts', dbName);
    if (fs.existsSync(localDb) && fs.statSync(localDb).size > 100) {
      try {
        execSync(`adb -s ${D2_SERIAL} push "${localDb}" "/data/system_ce/0/${dbName}" 2>/dev/null`, { timeout: 15000 });
        log(`  ✓ Account ${dbName} pushed`);
        totalPushed++;
      } catch (e) { log(`  ✗ Account ${dbName} push failed`); }
    }
  }

  // Account refresh
  try {
    execSync(`adb -s ${D2_SERIAL} shell "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED" 2>/dev/null`, { timeout: 10000 });
  } catch (e) {}

  log(`  Total pushed: ${totalPushed} files`);

  // ════════════════════════════════════════════════════════════
  // STEP 4: Proxy
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 4: Setting proxy on D2...');

  // Get .220 proxy config
  const proxyInfo = runOn220([
    'getprop ro.sys.cloud.proxy.type',
    'echo "|"',
    'getprop ro.sys.cloud.proxy.mode',
    'echo "|"',
    'getprop ro.sys.cloud.proxy.data',
    'echo "|"',
    'settings get global http_proxy 2>/dev/null',
  ].join('; '), 5);
  log(`  .220 proxy config: ${proxyInfo}`);

  // Parse and apply proxy
  const parts = proxyInfo.split('|').map(s => s.trim());
  const proxyType = parts[0] || '';
  const proxyMode = parts[1] || '';
  const proxyData = parts[2] || '';
  const httpProxy = parts[3] || '';

  if (proxyData || httpProxy) {
    log(`  Proxy: type=${proxyType} mode=${proxyMode} data=${proxyData} http=${httpProxy}`);

    // Try setting via VMOS API
    if (proxyData) {
      try {
        const pd = JSON.parse(proxyData);
        const setResult = await apiPost('/vcpcloud/api/padApi/modifyProxy', {
          padCodes: [D2_PAD],
          proxyType: parseInt(proxyType) || 1,
          proxyMode: parseInt(proxyMode) || 1,
          proxyData: proxyData,
        });
        log(`  modifyProxy: code=${setResult.code} msg=${setResult.msg || 'ok'}`);
      } catch (e) {
        // Set via syncCmd as fallback
        if (httpProxy && httpProxy !== 'null') {
          await syncCmd(D2_PAD, `settings put global http_proxy "${httpProxy}"`, 10);
          log(`  Set http_proxy via settings: ${httpProxy}`);
        }
      }
    } else if (httpProxy && httpProxy !== 'null') {
      await syncCmd(D2_PAD, `settings put global http_proxy "${httpProxy}"`, 10);
      log(`  Set http_proxy: ${httpProxy}`);
    }
  } else {
    log('  No proxy found on .220');
  }

  // ════════════════════════════════════════════════════════════
  // SUMMARY
  // ════════════════════════════════════════════════════════════
  console.log('\n' + '═'.repeat(60));
  console.log('  CLONE SUMMARY');
  console.log(`  APKs installed: ${installed.length}/${Object.keys(APPS).length}`);
  if (missing.length > 0) console.log(`  Missing: ${missing.join(', ')}`);
  console.log(`  Data files extracted: ${totalExtracted}`);
  console.log(`  Data files pushed to D2: ${totalPushed}`);
  console.log('═'.repeat(60));
}

main().catch(e => console.error('FATAL:', e));
