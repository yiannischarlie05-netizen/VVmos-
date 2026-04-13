#!/usr/bin/env node
/**
 * Clone 10.0.26.220 → D2 — Phase 2+3
 * Pull full APKs via nc relay (with proper timeouts), install on D2 via adb
 * Then restore app data/accounts via syncCmd
 */

const { execSync } = require('child_process');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');
const D2_PAD = 'ACP251008GUOEEHB';
const D1_SERIAL = 'localhost:8479';
const D2_SERIAL = 'localhost:7391';
const D1_IP = '10.0.96.174';
const SRC_IP = '10.0.26.220';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');

// APK paths discovered in Phase 2A
const APK_MAP = {
  'com.yandex.bank': '/data/app/~~0hnfvBzhxnhpDuHI9cY30Q==/com.yandex.bank-r0hzstC_hD8aKHipTzfq_g==/base.apk',
  'ru.ozon.app.android': '/data/app/~~VEvGmwbOcylt8Lcx2Qp9hg==/ru.ozon.app.android-QBTantiUD_bSeBU-eHSV1Q==/base.apk',
  'ru.ozon.fintech.finance': '/data/app/~~-APX0nrW1si12r1V9idv3A==/ru.ozon.fintech.finance-MLh6s6UVrHHWWIXkWyddHA==/base.apk',
  'com.wildberries.ru': '/data/app/~~B6750jl6r8XGKnOM0-hRAQ==/com.wildberries.ru-lX42uzsZ4Zs675Qy80BYWQ==/base.apk',
  'ru.yandex.taxi': '/data/app/~~wK2mAP68gZwmyFPp6UeaOA==/ru.yandex.taxi-PKOPpTH5qtvKYkprFt340A==/base.apk',
  'ru.yoo.money': '/data/app/~~Yf1SUfwhCxaEibOm-_Ctig==/ru.yoo.money-YqZiD1qUsxxsuETehWeIrA==/base.apk',
  'ru.cupis.wallet': '/data/app/~~MQOPHJiiE-OgQqw02fdHWg==/ru.cupis.wallet-mHfJ4Ua1GYiictw54IYJGg==/base.apk',
  'ru.apteka': '/data/app/~~j5AB5LSL4yAlPfSzN1o8xA==/ru.apteka-zQwY0yHDnh2Ik4ZrZAct9g==/base.apk',
  'ru.getpharma.eapteka': '/data/app/~~Lh7KkGdY9VtBm3AC5wEsLg==/ru.getpharma.eapteka-rWUoa051jyFeGAfMEClihw==/base.apk',
  'ru.rostel': '/data/app/~~PmomRTxq1p5ywefa9_lGnw==/ru.rostel-a12u2iLNxh0NxbBhsamL8w==/base.apk',
  'ru.vk.store': '/data/app/~~dI5E6u2aJsY99z-LqOyblA==/ru.vk.store-JU1LsGZ0NISX_7STXf6vsg==/base.apk',
  'com.app.trademo': '/data/app/~~Wxk7-55Bxuh7YZnn2ZFEiA==/com.app.trademo-5zyYOz2-ozsLRT0GbiAuSQ==/base.apk',
  'com.trademo.massmo': '/data/app/~~gli6s-DGv126q_t3AWx8OQ==/com.trademo.massmo-tRUCK-pf3W1mqcevfNeVMA==/base.apk',
};

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d) { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); return d; }

// ═══════════════════════════════════════════════════════════════
// VMOS Cloud API
// ═══════════════════════════════════════════════════════════════
function sign(b){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z'),sd=xd.slice(0,8),CT='application/json;charset=UTF-8',SHD='content-type;host;x-content-sha256;x-date';const bh=crypto.createHash('sha256').update(b,'utf8').digest('hex');const can=`host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;const ch=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=`HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;let k=crypto.createHmac('sha256',SK).update(sd).digest();k=crypto.createHmac('sha256',k).update('armcloud-paas').digest();k=crypto.createHmac('sha256',k).update('request').digest();return{'content-type':CT,'x-date':xd,'x-host':HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256',k).update(sts).digest('hex')}`};}

function apiPost(ep,d,t){return new Promise(ok=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b);const req=https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(t||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}

// ═══════════════════════════════════════════════════════════════
// ADB helpers
// ═══════════════════════════════════════════════════════════════
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

// Run shell command on .220 (returns first ~4KB output)
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

// Pull file from .220 to D1 via nc, then adb pull to local
function relayPull(remoteFile, localFile, port, timeoutSec) {
  timeoutSec = timeoutSec || 120;
  const cmd = `cat "${remoteFile}" | nc -w ${timeoutSec} ${D1_IP} ${port}`;
  const open = buildOpen(cmd);
  fs.writeFileSync('/tmp/adb_open_relay.bin', open);
  execSync(`adb -s ${D1_SERIAL} push /tmp/adb_open_relay.bin /sdcard/open_relay.bin 2>/dev/null`, { timeout: 10000 });

  const script = [
    '#!/system/bin/sh',
    `rm -f /sdcard/recv_${port}.bin`,
    `nc -l -p ${port} -w ${timeoutSec} > /sdcard/recv_${port}.bin &`,
    'LPID=$!',
    'sleep 1',
    `(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_relay.bin; sleep ${timeoutSec}) | nc -w ${timeoutSec + 5} ${SRC_IP} 5555 > /dev/null 2>&1 &`,
    'SPID=$!',
    'wait $LPID 2>/dev/null',
    'kill $SPID 2>/dev/null',
    'sleep 1',
    `wc -c < /sdcard/recv_${port}.bin 2>/dev/null`,
  ].join('\n');
  fs.writeFileSync(`/tmp/d1_relay_${port}.sh`, script);
  execSync(`adb -s ${D1_SERIAL} push /tmp/d1_relay_${port}.sh /sdcard/relay.sh 2>/dev/null`, { timeout: 10000 });

  try {
    const sizeStr = execSync(`adb -s ${D1_SERIAL} shell sh /sdcard/relay.sh`, {
      timeout: (timeoutSec + 20) * 1000, encoding: 'utf8'
    }).trim();
    const size = parseInt(sizeStr) || 0;
    if (size > 0) {
      execSync(`adb -s ${D1_SERIAL} pull /sdcard/recv_${port}.bin "${localFile}" 2>/dev/null`, { timeout: 120000 });
      // Clean up on D1
      execSync(`adb -s ${D1_SERIAL} shell rm -f /sdcard/recv_${port}.bin 2>/dev/null`, { timeout: 5000 });
      return size;
    }
    return 0;
  } catch (e) { return -1; }
}

// ═══════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(60));
  console.log('  CLONE 10.0.26.220 → D2 — Full APKs + Data');
  console.log('═'.repeat(60));

  ensureDir(path.join(OUT, 'apks'));

  // Verify both tunnels
  try {
    execSync(`adb -s ${D1_SERIAL} shell echo D1_OK`, { timeout: 5000, encoding: 'utf8' });
    execSync(`adb -s ${D2_SERIAL} shell echo D2_OK`, { timeout: 5000, encoding: 'utf8' });
    log('Both D1 and D2 tunnels verified');
  } catch (e) {
    log('ERROR: ADB tunnel(s) not connected');
    process.exit(1);
  }

  // Ensure cnxn.bin exists on D1
  const cnxn = Buffer.from('434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex');
  fs.writeFileSync('/tmp/adb_cnxn.bin', cnxn);
  execSync(`adb -s ${D1_SERIAL} push /tmp/adb_cnxn.bin /sdcard/cnxn.bin 2>/dev/null`);

  // ── Step 1: Get APK sizes ──
  log('\nStep 1: Getting APK sizes from .220...');
  const apkSizes = {};
  for (const [pkg, apkPath] of Object.entries(APK_MAP)) {
    const out = runOn220(`stat -c %s "${apkPath}" 2>/dev/null`, 3);
    const size = parseInt(out.trim()) || 0;
    apkSizes[pkg] = size;
    log(`  ${pkg}: ${(size / 1024 / 1024).toFixed(1)} MB`);
    await sleep(300);
  }

  const totalMB = Object.values(apkSizes).reduce((a, b) => a + b, 0) / 1024 / 1024;
  log(`  Total: ${totalMB.toFixed(0)} MB across ${Object.keys(apkSizes).length} APKs`);

  // ── Step 2: Pull full APKs via nc relay ──
  log('\nStep 2: Pulling full APKs (.220 → D1 → local)...');
  let port = 33500;
  const pulled = [];

  for (const [pkg, apkPath] of Object.entries(APK_MAP)) {
    const sizeMB = (apkSizes[pkg] || 0) / 1024 / 1024;
    if (sizeMB < 0.001) {
      log(`  ${pkg}: 0 bytes, skipping`);
      continue;
    }

    // Timeout: ~1 min per 20MB + 30s buffer
    const timeout = Math.max(60, Math.ceil(sizeMB / 20) * 60 + 30);
    const localFile = path.join(OUT, 'apks', `${pkg}.apk`);

    // Skip if already pulled correctly
    if (fs.existsSync(localFile) && Math.abs(fs.statSync(localFile).size - apkSizes[pkg]) < 1024) {
      log(`  ${pkg}: already pulled (${sizeMB.toFixed(1)}MB) ✓`);
      pulled.push(pkg);
      continue;
    }

    log(`  ${pkg}: pulling ${sizeMB.toFixed(1)}MB (timeout ${timeout}s)...`);
    const got = relayPull(apkPath, localFile, port, timeout);
    
    if (got > 0 && Math.abs(got - apkSizes[pkg]) < 1024) {
      log(`  ✓ ${pkg}: ${(got / 1024 / 1024).toFixed(1)}MB`);
      pulled.push(pkg);
    } else {
      log(`  ✗ ${pkg}: got ${got} bytes, expected ${apkSizes[pkg]}`);
    }
    port++;
    await sleep(500);
  }
  log(`  Pulled: ${pulled.length}/${Object.keys(APK_MAP).length}`);

  // ── Step 3: Install APKs on D2 via adb install ──
  log('\nStep 3: Installing APKs on D2 via adb...');
  const installed = [];

  for (const pkg of pulled) {
    const apkFile = path.join(OUT, 'apks', `${pkg}.apk`);
    const size = fs.statSync(apkFile).size;
    log(`  Installing ${pkg} (${(size / 1024 / 1024).toFixed(1)}MB)...`);

    try {
      const result = execSync(
        `adb -s ${D2_SERIAL} install -r -g "${apkFile}" 2>&1`,
        { timeout: 120000, encoding: 'utf8' }
      );
      if (result.includes('Success')) {
        log(`  ✓ ${pkg}`);
        installed.push(pkg);
      } else {
        log(`  ✗ ${pkg}: ${result.trim().slice(0, 80)}`);
      }
    } catch (e) {
      log(`  ✗ ${pkg}: ${(e.stdout || e.message).slice(0, 80)}`);
    }
    await sleep(500);
  }
  log(`  Installed: ${installed.length}/${pulled.length}`);

  // ── Step 4: Restore app data from previous extraction ──
  log('\nStep 4: Restoring app data...');
  const dataDir = path.join(OUT, 'data');

  if (fs.existsSync(dataDir)) {
    for (const pkg of fs.readdirSync(dataDir)) {
      const pkgDir = path.join(dataDir, pkg);
      if (!fs.statSync(pkgDir).isDirectory()) continue;

      // Stop the app
      await syncCmd(D2_PAD, `am force-stop ${pkg} 2>/dev/null`, 5);

      let restoredCount = 0;

      // Restore databases
      const dbDir = path.join(pkgDir, 'databases');
      if (fs.existsSync(dbDir)) {
        for (const db of fs.readdirSync(dbDir)) {
          const localFile = path.join(dbDir, db);
          if (fs.statSync(localFile).size < 10) continue;
          try {
            execSync(`adb -s ${D2_SERIAL} shell mkdir -p /data/data/${pkg}/databases 2>/dev/null`, { timeout: 5000 });
            execSync(`adb -s ${D2_SERIAL} push "${localFile}" /data/data/${pkg}/databases/${db} 2>/dev/null`, { timeout: 30000 });
            restoredCount++;
          } catch (e) { /* skip */ }
        }
      }

      // Restore shared_prefs
      const prefsDir = path.join(pkgDir, 'shared_prefs');
      if (fs.existsSync(prefsDir)) {
        for (const pref of fs.readdirSync(prefsDir)) {
          const localFile = path.join(prefsDir, pref);
          if (fs.statSync(localFile).size < 10) continue;
          try {
            execSync(`adb -s ${D2_SERIAL} shell mkdir -p /data/data/${pkg}/shared_prefs 2>/dev/null`, { timeout: 5000 });
            execSync(`adb -s ${D2_SERIAL} push "${localFile}" /data/data/${pkg}/shared_prefs/${pref} 2>/dev/null`, { timeout: 30000 });
            restoredCount++;
          } catch (e) { /* skip */ }
        }
      }

      // Fix ownership
      if (restoredCount > 0) {
        try {
          const uid = execSync(`adb -s ${D2_SERIAL} shell stat -c %u /data/data/${pkg} 2>/dev/null`, {
            timeout: 5000, encoding: 'utf8'
          }).trim();
          if (uid.match(/^\d+$/)) {
            execSync(`adb -s ${D2_SERIAL} shell chown -R ${uid}:${uid} /data/data/${pkg}/databases /data/data/${pkg}/shared_prefs 2>/dev/null`, { timeout: 10000 });
          }
        } catch (e) { /* skip */ }
      }

      if (restoredCount > 0) log(`  ${pkg}: ${restoredCount} files restored`);
    }
  }

  // Restore account databases if they were extracted
  const acctCE = path.join(OUT, 'accounts', 'accounts_ce.db');
  const acctDE = path.join(OUT, 'accounts', 'accounts_de.db');
  for (const [file, target] of [[acctCE, '/data/system_ce/0/accounts_ce.db'], [acctDE, '/data/system_de/0/accounts_de.db']]) {
    if (fs.existsSync(file) && fs.statSync(file).size > 100) {
      try {
        execSync(`adb -s ${D2_SERIAL} push "${file}" ${target} 2>/dev/null`, { timeout: 30000 });
        execSync(`adb -s ${D2_SERIAL} shell "chown system:system ${target}; chmod 600 ${target}" 2>/dev/null`, { timeout: 5000 });
        log(`  ✓ ${path.basename(file)} restored`);
      } catch (e) { log(`  ✗ ${path.basename(file)}: ${e.message.slice(0, 60)}`); }
    }
  }

  // Trigger account refresh
  try {
    execSync(`adb -s ${D2_SERIAL} shell am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null`, { timeout: 10000 });
    log('  Account refresh broadcast sent');
  } catch (e) { /* ignore */ }

  // ── Step 5: Proxy ──
  log('\nStep 5: Setting up proxy on D2...');
  const existing = await apiPost('/vcpcloud/api/padApi/queryProxyList', { page: 1, rows: 10 });
  const proxies = existing?.data?.records || [];
  const ruProxy = proxies.find(p => p.proxyCountry === 'RU');
  
  if (ruProxy) {
    log(`  Found Russian proxy: ${ruProxy.proxyHost}:${ruProxy.proxyPort}`);
    const r = await apiPost('/vcpcloud/api/padApi/setProxy', {
      padCodes: [D2_PAD], proxyType: 'proxy', proxyName: 'socks5',
      proxyIp: ruProxy.proxyHost, proxyPort: ruProxy.proxyPort,
      proxyUser: ruProxy.username || '', proxyPassword: ruProxy.password || '',
    });
    log(`  setProxy: code=${r.code}`);
  } else if (proxies.length > 0) {
    const p = proxies[0];
    log(`  No Russian proxy. Using: ${p.proxyHost}:${p.proxyPort} (${p.proxyCountry})`);
    const r = await apiPost('/vcpcloud/api/padApi/setProxy', {
      padCodes: [D2_PAD], proxyType: 'proxy', proxyName: p.proxyName || 'socks5',
      proxyIp: p.proxyHost, proxyPort: p.proxyPort,
      proxyUser: p.username || '', proxyPassword: p.password || '',
    });
    log(`  setProxy: code=${r.code}`);
    log('  → Buy Russian proxy: POST /vcpcloud/api/padApi/createProxyOrder { countryId: 1 }');
  } else {
    log('  No proxies in account. Buy one first.');
  }

  // ── Summary ──
  console.log('\n' + '═'.repeat(60));
  console.log('  CLONE COMPLETE');
  console.log(`  APKs installed: ${installed.length}/${Object.keys(APK_MAP).length}`);
  console.log(`  Data dir: ${OUT}`);
  console.log('═'.repeat(60));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
