#!/usr/bin/env node
/**
 * FULL CLONE .220 → D2 via ADB protocol streaming
 * Chain: local TCP → D1 ADB → exec:nc .220 5555 → .220 ADB
 * With proper WRTE/OKAY flow control for large file transfers.
 */
const net = require('net');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const https = require('https');
const crypto = require('crypto');

const D1_ADB_PORT = 8479;
const D2_SERIAL = 'localhost:7391';
const D2_PAD = 'ACP251008GUOEEHB';
const SRC_IP = '10.0.26.220';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');
const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');

const A_CNXN = 0x4e584e43, A_OPEN = 0x4e45504f, A_OKAY = 0x59414b4f;
const A_WRTE = 0x45545257, A_CLSE = 0x45534c43, MAX_PAYLOAD = 4096;

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d) { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); return d; }

// APK map from .220 (extracted in Phase 2)
const APK_MAP = {
  'com.yandex.bank': '/data/app/~~qbvjjp3CJ0_zz6P7JhGSzQ==/com.yandex.bank-zXBRN9vL-EqP8kFRNdaAHA==/base.apk',
  'ru.ozon.app.android': '/data/app/~~M1-wjqDaS8xB9TjZH-g3RQ==/ru.ozon.app.android-8NR1VZZXXI8JCIFdYkCi_g==/base.apk',
  'ru.ozon.fintech.finance': '/data/app/~~6xBPvYT5FRh5UUyYd8JV_A==/ru.ozon.fintech.finance-1VX3l8TApHCeTQrCsEMkIQ==/base.apk',
  'com.wildberries.ru': '/data/app/~~iG_1S2RFAE9HUoxlS-GDig==/com.wildberries.ru-VoNFN4u9FcYZ4Lq46p7mlA==/base.apk',
  'ru.yandex.taxi': '/data/app/~~EyJe2VE6o8PVCYy4TlKKYQ==/ru.yandex.taxi-HjBBjFc7TJB3vUdY8YVROQ==/base.apk',
  'ru.yoo.money': '/data/app/~~4JHrFZfIFSd1BRd2g8Ue4Q==/ru.yoo.money-P_WMCpSwASwNPnZNVcCh8A==/base.apk',
  'ru.cupis.wallet': '/data/app/~~T8b3PBcXA4fHdaKqh3y-7Q==/ru.cupis.wallet-XywgBqMVjIjR3L6gfKi_0g==/base.apk',
  'ru.apteka': '/data/app/~~r0EjaSsF8mRSd-c8ISwWAQ==/ru.apteka-lbxbGdNBvFNpWu3ZwbPijQ==/base.apk',
  'ru.getpharma.eapteka': '/data/app/~~cJTkUNK_0HkfFRaH1e9q6w==/ru.getpharma.eapteka-1GjTSiIL2EeNxkT2XluF7g==/base.apk',
  'ru.rostel': '/data/app/~~PmomRTxq1p5ywefa9_lGnw==/ru.rostel-a12u2iLNxh0NxbBhsamL8w==/base.apk',
  'ru.vk.store': '/data/app/~~cTGe4mB1tLTqCqoVSjr87g==/ru.vk.store-oQ8HnxGjBUC3VjXy8tqWww==/base.apk',
  'com.app.trademo': '/data/app/~~Wxk7-55Bxuh7YZnn2ZFEiA==/com.app.trademo-5zyYOz2-ozsLRT0GbiAuSQ==/base.apk',
  'com.trademo.massmo': '/data/app/~~eBNkfgqD5VNxhkJkOJNwJQ==/com.trademo.massmo-lT2kkSblkSs1Gi-tW3wVog==/base.apk',
};

// ═══════════════════════════════════════════════════════════════
// ADB Protocol helpers
// ═══════════════════════════════════════════════════════════════
function makeHeader(cmd, arg0, arg1, dl, dc) {
  const h = Buffer.alloc(24);
  h.writeUInt32LE(cmd,0); h.writeUInt32LE(arg0,4); h.writeUInt32LE(arg1,8);
  h.writeUInt32LE(dl,12); h.writeUInt32LE(dc,16); h.writeUInt32LE((cmd^0xFFFFFFFF)>>>0,20);
  return h;
}
function crc(d){let s=0;for(let i=0;i<d.length;i++)s+=d[i];return s>>>0;}
function makeCnxn(){const p=Buffer.from('host::\x00');return Buffer.concat([makeHeader(A_CNXN,0x01000000,MAX_PAYLOAD,p.length,crc(p)),p]);}
function makeOpen(lid,svc){const p=Buffer.from(svc+'\x00');return Buffer.concat([makeHeader(A_OPEN,lid,0,p.length,crc(p)),p]);}
function makeOkay(lid,rid){return makeHeader(A_OKAY,lid,rid,0,0);}
function parsePackets(buf){const pkts=[];let o=0;while(o+24<=buf.length){const cmd=buf.readUInt32LE(o),a0=buf.readUInt32LE(o+4),a1=buf.readUInt32LE(o+8),dl=buf.readUInt32LE(o+12);if(o+24+dl>buf.length)break;pkts.push({cmd,arg0:a0,arg1:a1,data:buf.slice(o+24,o+24+dl)});o+=24+dl;}return{packets:pkts,remaining:buf.slice(o)};}

// ═══════════════════════════════════════════════════════════════
// VMOS API
// ═══════════════════════════════════════════════════════════════
function sign(b){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z'),sd=xd.slice(0,8),CT='application/json;charset=UTF-8',SHD='content-type;host;x-content-sha256;x-date';const bh=crypto.createHash('sha256').update(b,'utf8').digest('hex');const can=`host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;const ch=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=`HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;let k=crypto.createHmac('sha256',SK).update(sd).digest();k=crypto.createHmac('sha256',k).update('armcloud-paas').digest();k=crypto.createHmac('sha256',k).update('request').digest();return{'content-type':CT,'x-date':xd,'x-host':HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256',k).update(sts).digest('hex')}`};}
function apiPost(ep,d,t){return new Promise(ok=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b);const req=https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(t||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}

// ═══════════════════════════════════════════════════════════════
// ADB Stream — execute command on .220 via D1 tunnel, return all output
// ═══════════════════════════════════════════════════════════════
function adbExec220(cmd, timeoutSec) {
  return new Promise((resolve, reject) => {
    const timeout = (timeoutSec || 30) * 1000;
    let localId = 1;
    let tunnelRemoteId = null;
    let srcRemoteId = null;
    let srcConnected = false;
    let result = Buffer.alloc(0);
    let done = false;
    let buf = Buffer.alloc(0);
    let tunnelBuf = Buffer.alloc(0);
    let timer;

    const sock = net.createConnection(D1_ADB_PORT, '127.0.0.1', () => {
      sock.write(makeCnxn());
    });

    function finish() {
      if (done) return;
      done = true;
      clearTimeout(timer);
      sock.destroy();
      resolve(result);
    }

    timer = setTimeout(finish, timeout);

    sock.on('data', chunk => {
      buf = Buffer.concat([buf, chunk]);
      const { packets, remaining } = parsePackets(buf);
      buf = remaining;

      for (const pkt of packets) {
        if (pkt.cmd === A_CNXN && !tunnelRemoteId) {
          // D1 connected, open nc tunnel
          sock.write(makeOpen(localId, `exec:nc ${SRC_IP} 5555`));
        } else if (pkt.cmd === A_OKAY && pkt.arg1 === localId && !tunnelRemoteId) {
          tunnelRemoteId = pkt.arg0;
          // Tunnel open, send CNXN to .220
          setTimeout(() => {
            const cnxn = makeCnxn();
            const wrte = Buffer.concat([
              makeHeader(A_WRTE, localId, tunnelRemoteId, cnxn.length, crc(cnxn)), cnxn
            ]);
            sock.write(wrte);
          }, 500);
        } else if (pkt.cmd === A_WRTE && pkt.arg1 === localId) {
          // Data from D1's nc tunnel = .220's ADB responses
          sock.write(makeOkay(localId, tunnelRemoteId));
          tunnelBuf = Buffer.concat([tunnelBuf, pkt.data]);
          
          // Parse .220's ADB packets
          const inner = parsePackets(tunnelBuf);
          tunnelBuf = inner.remaining;

          for (const ipkt of inner.packets) {
            if (ipkt.cmd === A_CNXN) {
              srcConnected = true;
              // Send OPEN for our command
              const openCmd = Buffer.from('shell:' + cmd + '\x00');
              const openPkt = Buffer.concat([
                makeHeader(A_OPEN, 100, 0, openCmd.length, crc(openCmd)), openCmd
              ]);
              const wrte = Buffer.concat([
                makeHeader(A_WRTE, localId, tunnelRemoteId, openPkt.length, crc(openPkt)), openPkt
              ]);
              sock.write(wrte);
            } else if (ipkt.cmd === A_OKAY && ipkt.arg1 === 100) {
              srcRemoteId = ipkt.arg0;
            } else if (ipkt.cmd === A_WRTE && ipkt.arg1 === 100) {
              result = Buffer.concat([result, ipkt.data]);
              // Send OKAY to .220
              const okay = makeOkay(100, srcRemoteId);
              const wrte = Buffer.concat([
                makeHeader(A_WRTE, localId, tunnelRemoteId, okay.length, crc(okay)), okay
              ]);
              sock.write(wrte);
            } else if (ipkt.cmd === A_CLSE) {
              finish();
            }
          }
        } else if (pkt.cmd === A_CLSE) {
          finish();
        }
      }
    });

    sock.on('error', () => finish());
    sock.on('close', () => finish());
  });
}

// ═══════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(60));
  console.log('  CLONE .220 → D2 via ADB Stream');
  console.log('═'.repeat(60));
  ensureDir(OUT);
  ensureDir(path.join(OUT, 'apks'));

  // Verify D2 ADB
  try {
    execSync(`adb -s ${D2_SERIAL} shell echo D2_OK`, { timeout: 5000 });
    log('D2 ADB OK');
  } catch (e) { log('D2 ADB down!'); process.exit(1); }

  // ════════════════════════════════════════════════════════════
  // STEP 1: Pull APKs from .220 via ADB stream
  // ════════════════════════════════════════════════════════════
  log('\nSTEP 1: Pulling APKs from .220...');

  // Quick connectivity test
  const testData = await adbExec220('echo STREAM_OK', 10);
  if (!testData.toString().includes('STREAM_OK')) {
    log('ERROR: .220 stream not working');
    process.exit(1);
  }
  log('  .220 stream verified');

  // Get APK sizes
  log('  Getting APK sizes...');
  const sizeData = await adbExec220(
    Object.values(APK_MAP).map(p => `stat -c "%s ${p}" "${p}" 2>/dev/null`).join('; '),
    15
  );
  const sizes = {};
  for (const line of sizeData.toString().split('\n')) {
    for (const [pkg, apkPath] of Object.entries(APK_MAP)) {
      if (line.includes(apkPath)) {
        const m = line.match(/^(\d+)/);
        if (m) sizes[pkg] = parseInt(m[1]);
      }
    }
  }
  for (const [pkg, size] of Object.entries(sizes)) {
    log(`    ${pkg}: ${(size / 1024 / 1024).toFixed(1)} MB`);
  }

  // Pull APKs — start with smallest first
  const sorted = Object.entries(APK_MAP).sort((a, b) => (sizes[a[0]] || 999999999) - (sizes[b[0]] || 999999999));
  const installed = [];

  for (const [pkg, apkPath] of sorted) {
    const sizeMB = ((sizes[pkg] || 0) / 1024 / 1024).toFixed(1);
    const localApk = path.join(OUT, 'apks', `${pkg}.apk`);
    const timeout = Math.max(30, Math.ceil((sizes[pkg] || 0) / 1024 / 1024 / 5) * 60 + 60);

    log(`\n  [${pkg}] ${sizeMB} MB (timeout ${timeout}s)...`);

    const startTime = Date.now();
    const apkData = await adbExec220(`cat "${apkPath}"`, timeout);
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    const gotMB = (apkData.length / 1024 / 1024).toFixed(1);

    if (apkData.length > 50000) {
      fs.writeFileSync(localApk, apkData);
      log(`    ✓ Got ${gotMB} MB in ${elapsed}s`);

      // Install on D2
      try {
        const r = execSync(`adb -s ${D2_SERIAL} install -r -g "${localApk}" 2>&1`, {
          timeout: 120000, encoding: 'utf8'
        });
        if (r.includes('Success')) {
          log(`    ✓ Installed on D2`);
          installed.push(pkg);
        } else {
          log(`    ✗ Install: ${r.trim().slice(0, 80)}`);
        }
      } catch (e) { log(`    ✗ Install err: ${(e.stdout || e.message).slice(0, 80)}`); }
    } else {
      log(`    ✗ Only ${apkData.length} bytes in ${elapsed}s`);
    }
  }

  log(`\n  APKs installed: ${installed.length}/${Object.keys(APK_MAP).length}`);

  // ════════════════════════════════════════════════════════════
  // STEP 2: Extract app data from .220
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 2: Extracting app data...');
  let totalData = 0;

  for (const pkg of Object.keys(APK_MAP)) {
    const appDir = ensureDir(path.join(OUT, 'data', pkg));

    // Get db + prefs lists
    const listing = await adbExec220(
      `ls -la /data/data/${pkg}/databases/ 2>/dev/null; echo "===PREFS==="; ls -la /data/data/${pkg}/shared_prefs/ 2>/dev/null`,
      10
    );
    const listStr = listing.toString();
    const [dbSection, prefSection] = listStr.split('===PREFS===');

    // Extract databases (< 50KB each — stream can handle this)
    const dbFiles = (dbSection || '').split('\n')
      .map(l => { const m = l.match(/\s(\d+)\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+(.+\.db)$/); return m ? {name:m[2],size:parseInt(m[1])} : null; })
      .filter(d => d && d.size > 0 && d.size < 50000);

    if (dbFiles.length > 0) {
      ensureDir(path.join(appDir, 'databases'));
      for (const db of dbFiles.slice(0, 5)) {
        const data = await adbExec220(`cat "/data/data/${pkg}/databases/${db.name}"`, 15);
        if (data.length > 10) {
          fs.writeFileSync(path.join(appDir, 'databases', db.name), data);
          totalData++;
        }
      }
    }

    // Extract shared_prefs (< 50KB each)
    const prefFiles = (prefSection || '').split('\n')
      .map(l => { const m = l.match(/\s(\d+)\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+(.+\.xml)$/); return m ? {name:m[2],size:parseInt(m[1])} : null; })
      .filter(p => p && p.size > 0 && p.size < 50000);

    if (prefFiles.length > 0) {
      ensureDir(path.join(appDir, 'shared_prefs'));
      for (const pref of prefFiles.slice(0, 10)) {
        const data = await adbExec220(`cat "/data/data/${pkg}/shared_prefs/${pref.name}"`, 15);
        if (data.length > 10) {
          fs.writeFileSync(path.join(appDir, 'shared_prefs', pref.name), data);
          totalData++;
        }
      }
    }

    if (dbFiles.length + prefFiles.length > 0) {
      log(`  ${pkg}: ${dbFiles.length} dbs, ${prefFiles.length} prefs`);
    }
  }

  // Account databases
  for (const dbName of ['accounts_ce.db', 'accounts_de.db']) {
    const data = await adbExec220(`cat /data/system_ce/0/${dbName}`, 15);
    if (data.length > 100) {
      ensureDir(path.join(OUT, 'accounts'));
      fs.writeFileSync(path.join(OUT, 'accounts', dbName), data);
      log(`  ✓ ${dbName}: ${data.length}B`);
      totalData++;
    }
  }

  log(`  Total data files: ${totalData}`);

  // ════════════════════════════════════════════════════════════
  // STEP 3: Push data to D2
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 3: Pushing data to D2...');
  let totalPushed = 0;

  for (const pkg of Object.keys(APK_MAP)) {
    const pkgDir = path.join(OUT, 'data', pkg);
    if (!fs.existsSync(pkgDir)) continue;

    // Check installed
    try {
      const check = execSync(`adb -s ${D2_SERIAL} shell "pm path ${pkg}" 2>/dev/null`, { timeout: 5000, encoding: 'utf8' });
      if (!check.includes('package:')) continue;
    } catch (e) { continue; }

    execSync(`adb -s ${D2_SERIAL} shell "am force-stop ${pkg}" 2>/dev/null`, { timeout: 5000 }).toString();
    let pushed = 0;

    for (const sub of ['databases', 'shared_prefs']) {
      const subDir = path.join(pkgDir, sub);
      if (!fs.existsSync(subDir)) continue;
      execSync(`adb -s ${D2_SERIAL} shell "mkdir -p /data/data/${pkg}/${sub}" 2>/dev/null`, { timeout: 5000 });
      for (const f of fs.readdirSync(subDir)) {
        const fp = path.join(subDir, f);
        if (fs.statSync(fp).size < 10) continue;
        try {
          execSync(`adb -s ${D2_SERIAL} push "${fp}" "/data/data/${pkg}/${sub}/${f}" 2>/dev/null`, { timeout: 30000 });
          pushed++;
        } catch (e) {}
      }
    }

    if (pushed > 0) {
      try {
        const uid = execSync(`adb -s ${D2_SERIAL} shell "stat -c %u /data/data/${pkg}" 2>/dev/null`, { timeout: 5000, encoding: 'utf8' }).trim();
        if (/^\d+$/.test(uid)) {
          execSync(`adb -s ${D2_SERIAL} shell "chown -R ${uid}:${uid} /data/data/${pkg}/databases /data/data/${pkg}/shared_prefs" 2>/dev/null`, { timeout: 10000 });
        }
      } catch (e) {}
      totalPushed += pushed;
      log(`  ${pkg}: ${pushed} files`);
    }
  }

  // Account DBs
  for (const dbName of ['accounts_ce.db', 'accounts_de.db']) {
    const f = path.join(OUT, 'accounts', dbName);
    if (fs.existsSync(f) && fs.statSync(f).size > 100) {
      try {
        execSync(`adb -s ${D2_SERIAL} push "${f}" "/data/system_ce/0/${dbName}" 2>/dev/null`, { timeout: 15000 });
        totalPushed++;
        log(`  ✓ ${dbName}`);
      } catch (e) {}
    }
  }

  execSync(`adb -s ${D2_SERIAL} shell "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED" 2>/dev/null`, { timeout: 10000 });
  log(`  Total pushed: ${totalPushed}`);

  // ════════════════════════════════════════════════════════════
  // STEP 4: Proxy
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 4: Proxy...');
  const proxyData = await adbExec220(
    'getprop ro.sys.cloud.proxy.type; echo "|"; getprop ro.sys.cloud.proxy.mode; echo "|"; getprop ro.sys.cloud.proxy.data; echo "|"; settings get global http_proxy 2>/dev/null',
    10
  );
  const proxyStr = proxyData.toString().trim();
  log(`  .220 proxy: ${proxyStr.slice(0, 200)}`);

  const pp = proxyStr.split('|').map(s => s.trim());
  if (pp[2] && pp[2] !== '') {
    const r = await apiPost('/vcpcloud/api/padApi/modifyProxy', {
      padCodes: [D2_PAD], proxyType: parseInt(pp[0]) || 1,
      proxyMode: parseInt(pp[1]) || 1, proxyData: pp[2],
    });
    log(`  modifyProxy: ${r.code} ${r.msg || ''}`);
  } else if (pp[3] && pp[3] !== 'null') {
    execSync(`adb -s ${D2_SERIAL} shell "settings put global http_proxy '${pp[3]}'" 2>/dev/null`, { timeout: 10000 });
    log(`  Set http_proxy: ${pp[3]}`);
  } else {
    log('  No proxy config found on .220');
  }

  // ════════════════════════════════════════════════════════════
  // SUMMARY
  // ════════════════════════════════════════════════════════════
  console.log('\n' + '═'.repeat(60));
  console.log('  CLONE COMPLETE');
  console.log(`  APKs installed: ${installed.length}/${Object.keys(APK_MAP).length}`);
  const missing = Object.keys(APK_MAP).filter(p => !installed.includes(p));
  if (missing.length > 0) console.log(`  Missing: ${missing.join(', ')}`);
  console.log(`  Data extracted: ${totalData} files`);
  console.log(`  Data pushed to D2: ${totalPushed} files`);
  console.log('═'.repeat(60));
}

main().catch(e => console.error('FATAL:', e));
