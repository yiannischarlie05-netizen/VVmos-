#!/usr/bin/env node
/**
 * Clone .220 → D2: Final approach
 * 1. Install APKs on D2 via curl download + pm install (using D2's own internet)
 * 2. Extract small data files from .220 via raw ADB + base64
 * 3. Push data to D2 via ADB tunnel
 * 4. Set proxy
 */
const { execSync } = require('child_process');
const https = require('https');
const http = require('http');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');
const D1_SERIAL = 'localhost:8479';
const D2_SERIAL = 'localhost:7391';
const D2_PAD = 'ACP251008GUOEEHB';
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
// VMOS API
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

function extractSmallFile220(remotePath) {
  const out = runOn220(`base64 "${remotePath}" 2>/dev/null`, 5);
  if (out.length < 10) return null;
  const clean = out.replace(/[^A-Za-z0-9+/=\n]/g, '').replace(/\n/g, '');
  try { return Buffer.from(clean, 'base64'); } catch (e) { return null; }
}

// ═══════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(60));
  console.log('  CLONE .220 → D2: Install + Data + Proxy');
  console.log('═'.repeat(60));

  ensureDir(OUT);
  ensureDir(path.join(OUT, 'data'));

  // Verify tunnels
  try {
    execSync(`adb -s ${D1_SERIAL} shell echo D1_OK`, { timeout: 5000, encoding: 'utf8' });
    execSync(`adb -s ${D2_SERIAL} shell echo D2_OK`, { timeout: 5000, encoding: 'utf8' });
    log('D1 + D2 tunnels OK');
  } catch (e) { log('ERROR: tunnel(s) down'); process.exit(1); }

  // Ensure cnxn.bin
  fs.writeFileSync('/tmp/adb_cnxn.bin',
    Buffer.from('434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex'));
  execSync(`adb -s ${D1_SERIAL} push /tmp/adb_cnxn.bin /sdcard/cnxn.bin 2>/dev/null`);

  // ════════════════════════════════════════════════════════════
  // STEP 1: Install APKs on D2 using D2's own curl + pm install
  // Download from APKPure via curl on D2 itself
  // ════════════════════════════════════════════════════════════
  log('\nSTEP 1: Installing APKs on D2...');

  // Get app versions from .220 first
  log('  Getting app versions from .220...');
  const versionInfo = runOn220('pm list packages --show-versioncode -3 2>/dev/null', 5);
  log(`  Versions:\n${versionInfo.slice(0, 500)}`);

  const installed = [];
  for (const pkg of APPS) {
    log(`\n  [${pkg}]`);

    // Check if already installed on D2
    const check = await syncCmd(D2_PAD, `pm list packages ${pkg} 2>/dev/null`, 5);
    if (check.includes(pkg)) {
      log(`    Already installed on D2`);
      installed.push(pkg);
      continue;
    }

    // Try download + install via curl on D2
    // APKPure download URL format
    const downloadCmd = [
      `cd /data/local/tmp`,
      `rm -f ${pkg}.apk`,
      // Try APKPure direct download
      `curl -L -o ${pkg}.apk "https://d.apkpure.net/b/APK/${pkg}?version=latest" -H "User-Agent: Mozilla/5.0" --connect-timeout 15 --max-time 300 -s -w "%{http_code}" 2>/dev/null`,
    ].join('; ');

    const dlResult = await syncCmd(D2_PAD, downloadCmd, 60);
    log(`    Download: ${dlResult.slice(0, 60)}`);

    // Check file size
    const sizeCheck = await syncCmd(D2_PAD, `ls -la /data/local/tmp/${pkg}.apk 2>/dev/null`, 5);
    log(`    File: ${sizeCheck.slice(0, 80)}`);

    // Try install
    if (sizeCheck.includes(pkg)) {
      const installResult = await syncCmd(D2_PAD,
        `pm install -r -g "/data/local/tmp/${pkg}.apk" 2>&1; rm -f "/data/local/tmp/${pkg}.apk"`, 30);
      if (installResult.includes('Success')) {
        log(`    ✓ Installed`);
        installed.push(pkg);
      } else {
        log(`    ✗ Install: ${installResult.slice(0, 80)}`);
      }
    }

    await sleep(1000);
  }

  // If APKPure didn't work, try alternative: RuStore or direct ADB install
  const notInstalled = APPS.filter(p => !installed.includes(p));
  if (notInstalled.length > 0) {
    log(`\n  ${notInstalled.length} apps not installed. Trying ADB install from local APKs...`);

    // For each missing app, try to install via adb from local machine
    // First check if we have any valid APKs locally (from earlier attempts)
    for (const pkg of notInstalled) {
      const localApk = path.join(OUT, 'apks', `${pkg}.apk`);
      if (fs.existsSync(localApk) && fs.statSync(localApk).size > 50000) {
        log(`    Installing ${pkg} from local APK...`);
        try {
          const r = execSync(`adb -s ${D2_SERIAL} install -r -g "${localApk}" 2>&1`, {
            timeout: 120000, encoding: 'utf8'
          });
          if (r.includes('Success')) {
            log(`    ✓ ${pkg}`);
            installed.push(pkg);
          } else {
            log(`    ✗ ${r.trim().slice(0, 80)}`);
          }
        } catch (e) { log(`    ✗ ${(e.stdout || e.message).slice(0, 80)}`); }
      }
    }
  }

  log(`\n  === Installed: ${installed.length}/${APPS.length} ===`);

  // ════════════════════════════════════════════════════════════
  // STEP 2: Extract & push app data from .220
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 2: Extracting + pushing app data...');

  for (const pkg of APPS) {
    const appDir = ensureDir(path.join(OUT, 'data', pkg));
    let extractedFiles = 0;

    // List databases on .220
    const dbList = runOn220(`ls -la /data/data/${pkg}/databases/ 2>/dev/null`, 3);
    const dbs = dbList.split('\n')
      .filter(l => l.trim().endsWith('.db'))
      .map(l => {
        const parts = l.trim().split(/\s+/);
        return { name: parts[parts.length - 1], size: parseInt(parts[4]) || 0 };
      })
      .filter(d => d.size > 0 && d.size < 3500);

    if (dbs.length > 0) {
      ensureDir(path.join(appDir, 'databases'));
      for (const db of dbs.slice(0, 5)) {
        const data = extractSmallFile220(`/data/data/${pkg}/databases/${db.name}`);
        if (data && data.length > 10) {
          const localFile = path.join(appDir, 'databases', db.name);
          fs.writeFileSync(localFile, data);
          // Push to D2
          try {
            execSync(`adb -s ${D2_SERIAL} shell "mkdir -p /data/data/${pkg}/databases" 2>/dev/null`, { timeout: 5000 });
            execSync(`adb -s ${D2_SERIAL} push "${localFile}" "/data/data/${pkg}/databases/${db.name}" 2>/dev/null`, { timeout: 15000 });
            extractedFiles++;
          } catch (e) {}
        }
        await sleep(300);
      }
    }

    // List shared_prefs
    const prefList = runOn220(`ls -la /data/data/${pkg}/shared_prefs/ 2>/dev/null`, 3);
    const prefs = prefList.split('\n')
      .filter(l => l.trim().endsWith('.xml'))
      .map(l => {
        const parts = l.trim().split(/\s+/);
        return { name: parts[parts.length - 1], size: parseInt(parts[4]) || 0 };
      })
      .filter(p => p.size > 0 && p.size < 3500);

    if (prefs.length > 0) {
      ensureDir(path.join(appDir, 'shared_prefs'));
      for (const pref of prefs.slice(0, 10)) {
        const data = extractSmallFile220(`/data/data/${pkg}/shared_prefs/${pref.name}`);
        if (data && data.length > 10) {
          const localFile = path.join(appDir, 'shared_prefs', pref.name);
          fs.writeFileSync(localFile, data);
          try {
            execSync(`adb -s ${D2_SERIAL} shell "mkdir -p /data/data/${pkg}/shared_prefs" 2>/dev/null`, { timeout: 5000 });
            execSync(`adb -s ${D2_SERIAL} push "${localFile}" "/data/data/${pkg}/shared_prefs/${pref.name}" 2>/dev/null`, { timeout: 15000 });
            extractedFiles++;
          } catch (e) {}
        }
        await sleep(300);
      }
    }

    // Fix ownership on D2
    if (extractedFiles > 0) {
      try {
        const uid = execSync(`adb -s ${D2_SERIAL} shell "stat -c %u /data/data/${pkg}" 2>/dev/null`, {
          timeout: 5000, encoding: 'utf8'
        }).trim();
        if (uid.match(/^\d+$/)) {
          execSync(`adb -s ${D2_SERIAL} shell "chown -R ${uid}:${uid} /data/data/${pkg}/databases /data/data/${pkg}/shared_prefs" 2>/dev/null`, { timeout: 10000 });
        }
      } catch (e) {}
      log(`  ${pkg}: ${extractedFiles} files`);
    } else {
      log(`  ${pkg}: no small extractable files`);
    }
  }

  // Account DB + refresh
  try {
    execSync(`adb -s ${D2_SERIAL} shell "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED" 2>/dev/null`, { timeout: 10000 });
    log('  Account refresh broadcast sent');
  } catch (e) {}

  // ════════════════════════════════════════════════════════════
  // STEP 3: Proxy
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 3: Setting up proxy...');
  const existing = await apiPost('/vcpcloud/api/padApi/queryProxyList', { page: 1, rows: 10 });
  const proxies = existing?.data?.records || [];

  if (proxies.length > 0) {
    const p = proxies[0];
    log(`  Assigning proxy: ${p.proxyHost}:${p.proxyPort} (${p.proxyCountry})`);
    const r = await apiPost('/vcpcloud/api/padApi/setProxy', {
      padCodes: [D2_PAD], proxyType: 'proxy',
      proxyName: p.proxyName || 'socks5',
      proxyIp: p.proxyHost, proxyPort: p.proxyPort,
      proxyUser: p.username || '', proxyPassword: p.password || '',
    });
    log(`  setProxy: code=${r.code}, msg=${r.msg}`);
  } else {
    log('  No proxies available in account');
  }

  // ════════════════════════════════════════════════════════════
  // SUMMARY
  // ════════════════════════════════════════════════════════════
  console.log('\n' + '═'.repeat(60));
  console.log('  CLONE SUMMARY');
  console.log(`  Apps installed: ${installed.length}/${APPS.length}`);
  console.log(`  Not installed: ${APPS.filter(p => !installed.includes(p)).join(', ') || 'none'}`);

  // Count data files
  let totalData = 0;
  for (const pkg of APPS) {
    const d = path.join(OUT, 'data', pkg);
    if (fs.existsSync(d)) {
      const walk = dir => { for (const f of fs.readdirSync(dir)) { const fp = path.join(dir, f); if (fs.statSync(fp).isDirectory()) walk(fp); else totalData++; } };
      walk(d);
    }
  }
  console.log(`  Data files pushed: ${totalData}`);
  console.log('═'.repeat(60));
}

main().catch(e => console.error('FATAL:', e));
