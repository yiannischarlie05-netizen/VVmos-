#!/usr/bin/env node
/**
 * HYBRID CLONE: ADB stream keeps .220 alive + nc for fast data transfer
 * 
 * For each APK:
 *   1. Spawn nc listener on D1 (via adb shell, stays alive)
 *   2. Open ADB stream to .220 → run "cat APK | nc D1_IP PORT"
 *   3. Stream keeps .220 shell alive with WRTE/OKAY flow control
 *   4. Data flows through fast nc connection (.220 → D1)
 *   5. Pull from D1, install on D2
 * 
 * For small data files: use ADB stream directly (fast enough for <50KB)
 */
const net = require('net');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const https = require('https');
const crypto = require('crypto');

const D1_ADB_PORT = 8479;
const D1_SERIAL = 'localhost:8479';
const D2_SERIAL = 'localhost:7391';
const D2_PAD = 'ACP251008GUOEEHB';
const D1_IP = '10.0.96.174';
const SRC_IP = '10.0.26.220';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');
const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');

const A_CNXN = 0x4e584e43, A_OPEN = 0x4e45504f, A_OKAY = 0x59414b4f;
const A_WRTE = 0x45545257, A_CLSE = 0x45534c43;

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d) { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); return d; }

const APK_MAP = {
  'com.app.trademo': '/data/app/~~Wxk7-55Bxuh7YZnn2ZFEiA==/com.app.trademo-5zyYOz2-ozsLRT0GbiAuSQ==/base.apk',
  'com.trademo.massmo': '/data/app/~~gli6s-DGv126q_t3AWx8OQ==/com.trademo.massmo-tRUCK-pf3W1mqcevfNeVMA==/base.apk',
  'com.yandex.bank': '/data/app/~~0hnfvBzhxnhpDuHI9cY30Q==/com.yandex.bank-r0hzstC_hD8aKHipTzfq_g==/base.apk',
  'ru.cupis.wallet': '/data/app/~~MQOPHJiiE-OgQqw02fdHWg==/ru.cupis.wallet-mHfJ4Ua1GYiictw54IYJGg==/base.apk',
  'ru.apteka': '/data/app/~~j5AB5LSL4yAlPfSzN1o8xA==/ru.apteka-zQwY0yHDnh2Ik4ZrZAct9g==/base.apk',
  'ru.getpharma.eapteka': '/data/app/~~Lh7KkGdY9VtBm3AC5wEsLg==/ru.getpharma.eapteka-rWUoa051jyFeGAfMEClihw==/base.apk',
  'ru.vk.store': '/data/app/~~dI5E6u2aJsY99z-LqOyblA==/ru.vk.store-JU1LsGZ0NISX_7STXf6vsg==/base.apk',
  'ru.yandex.taxi': '/data/app/~~wK2mAP68gZwmyFPp6UeaOA==/ru.yandex.taxi-PKOPpTH5qtvKYkprFt340A==/base.apk',
  'ru.ozon.fintech.finance': '/data/app/~~-APX0nrW1si12r1V9idv3A==/ru.ozon.fintech.finance-MLh6s6UVrHHWWIXkWyddHA==/base.apk',
  'ru.ozon.app.android': '/data/app/~~VEvGmwbOcylt8Lcx2Qp9hg==/ru.ozon.app.android-QBTantiUD_bSeBU-eHSV1Q==/base.apk',
  'ru.yoo.money': '/data/app/~~Yf1SUfwhCxaEibOm-_Ctig==/ru.yoo.money-YqZiD1qUsxxsuETehWeIrA==/base.apk',
  'ru.rostel': '/data/app/~~PmomRTxq1p5ywefa9_lGnw==/ru.rostel-a12u2iLNxh0NxbBhsamL8w==/base.apk',
  'com.wildberries.ru': '/data/app/~~B6750jl6r8XGKnOM0-hRAQ==/com.wildberries.ru-lX42uzsZ4Zs675Qy80BYWQ==/base.apk',
};

// ═══════════════════════════════════════════════════════════════
// ADB Protocol
// ═══════════════════════════════════════════════════════════════
function makeHeader(cmd,a0,a1,dl,dc){const h=Buffer.alloc(24);h.writeUInt32LE(cmd,0);h.writeUInt32LE(a0,4);h.writeUInt32LE(a1,8);h.writeUInt32LE(dl,12);h.writeUInt32LE(dc,16);h.writeUInt32LE((cmd^0xFFFFFFFF)>>>0,20);return h;}
function crc(d){let s=0;for(let i=0;i<d.length;i++)s+=d[i];return s>>>0;}
function makeCnxn(){const p=Buffer.from('host::\x00');return Buffer.concat([makeHeader(A_CNXN,0x01000000,256*1024,p.length,crc(p)),p]);}
function makeOpen(lid,svc){const p=Buffer.from(svc+'\x00');return Buffer.concat([makeHeader(A_OPEN,lid,0,p.length,crc(p)),p]);}
function makeOkay(lid,rid){return makeHeader(A_OKAY,lid,rid,0,0);}
function parsePackets(buf){const pkts=[];let o=0;while(o+24<=buf.length){const cmd=buf.readUInt32LE(o),a0=buf.readUInt32LE(o+4),a1=buf.readUInt32LE(o+8),dl=buf.readUInt32LE(o+12);if(o+24+dl>buf.length)break;pkts.push({cmd,arg0:a0,arg1:a1,data:buf.slice(o+24,o+24+dl)});o+=24+dl;}return{packets:pkts,remaining:buf.slice(o)};}

// ═══════════════════════════════════════════════════════════════
// VMOS API
// ═══════════════════════════════════════════════════════════════
function sign(b){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z'),sd=xd.slice(0,8),CT='application/json;charset=UTF-8',SHD='content-type;host;x-content-sha256;x-date';const bh=crypto.createHash('sha256').update(b,'utf8').digest('hex');const can=`host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;const ch=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=`HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;let k=crypto.createHmac('sha256',SK).update(sd).digest();k=crypto.createHmac('sha256',k).update('armcloud-paas').digest();k=crypto.createHmac('sha256',k).update('request').digest();return{'content-type':CT,'x-date':xd,'x-host':HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256',k).update(sts).digest('hex')}`};}
function apiPost(ep,d,t){return new Promise(ok=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b);const req=https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(t||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}

// ═══════════════════════════════════════════════════════════════
// ADB stream: run command on .220 via D1 tunnel with WRTE/OKAY
// Returns: {output: Buffer, exitClean: bool}
// ═══════════════════════════════════════════════════════════════
function adbExec220(cmd, timeoutSec) {
  return new Promise((resolve) => {
    const timeout = (timeoutSec || 30) * 1000;
    let tunnelRemoteId = null, srcRemoteId = null;
    let srcConnected = false, done = false;
    let result = Buffer.alloc(0);
    let buf = Buffer.alloc(0), tunnelBuf = Buffer.alloc(0);
    let timer;

    const sock = net.createConnection(D1_ADB_PORT, '127.0.0.1', () => sock.write(makeCnxn()));

    function finish() {
      if (done) return; done = true;
      clearTimeout(timer);
      try { sock.destroy(); } catch(e) {}
      resolve({ output: result, exitClean: true });
    }

    timer = setTimeout(finish, timeout);

    sock.on('data', chunk => {
      buf = Buffer.concat([buf, chunk]);
      const { packets, remaining } = parsePackets(buf);
      buf = remaining;

      for (const pkt of packets) {
        if (pkt.cmd === A_CNXN && !tunnelRemoteId) {
          sock.write(makeOpen(1, `exec:nc ${SRC_IP} 5555`));
        } else if (pkt.cmd === A_OKAY && pkt.arg1 === 1 && !tunnelRemoteId) {
          tunnelRemoteId = pkt.arg0;
          setTimeout(() => {
            const c = makeCnxn();
            sock.write(Buffer.concat([makeHeader(A_WRTE, 1, tunnelRemoteId, c.length, crc(c)), c]));
          }, 500);
        } else if (pkt.cmd === A_WRTE && pkt.arg1 === 1) {
          sock.write(makeOkay(1, tunnelRemoteId));
          tunnelBuf = Buffer.concat([tunnelBuf, pkt.data]);
          const inner = parsePackets(tunnelBuf);
          tunnelBuf = inner.remaining;
          for (const ip of inner.packets) {
            if (ip.cmd === A_CNXN && !srcConnected) {
              srcConnected = true;
              const p = Buffer.from('shell:' + cmd + '\x00');
              const op = Buffer.concat([makeHeader(A_OPEN, 100, 0, p.length, crc(p)), p]);
              sock.write(Buffer.concat([makeHeader(A_WRTE, 1, tunnelRemoteId, op.length, crc(op)), op]));
            } else if (ip.cmd === A_OKAY && ip.arg1 === 100) {
              srcRemoteId = ip.arg0;
            } else if (ip.cmd === A_WRTE && ip.arg1 === 100) {
              result = Buffer.concat([result, ip.data]);
              const ok = makeOkay(100, srcRemoteId);
              sock.write(Buffer.concat([makeHeader(A_WRTE, 1, tunnelRemoteId, ok.length, crc(ok)), ok]));
            } else if (ip.cmd === A_CLSE) {
              finish();
            }
          }
        } else if (pkt.cmd === A_CLSE) {
          finish();
        }
      }
    });
    sock.on('error', finish);
    sock.on('close', finish);
  });
}

// ═══════════════════════════════════════════════════════════════
// Hybrid APK pull: ADB stream for .220 session + nc for data
// ═══════════════════════════════════════════════════════════════
async function pullApk(pkg, apkPath, port, timeoutSec) {
  timeoutSec = timeoutSec || 300;
  const recvFile = `/sdcard/recv_${port}.bin`;

  // Kill any old nc on that port
  try { execSync(`adb -s ${D1_SERIAL} shell "killall nc 2>/dev/null"`, { timeout: 3000 }); } catch(e) {}

  // Step 1: Spawn nc listener on D1 (stays alive via spawn)
  return new Promise(async (resolve) => {
    let listenerDone = false, streamDone = false;
    let receivedSize = 0;

    const listener = spawn('adb', ['-s', D1_SERIAL, 'shell',
      `rm -f ${recvFile}; nc -l -p ${port} -w ${timeoutSec} > ${recvFile}; wc -c ${recvFile}`
    ], { stdio: ['pipe', 'pipe', 'pipe'] });

    let listenerOut = '';
    listener.stdout.on('data', d => listenerOut += d.toString());
    listener.on('close', () => { listenerDone = true; checkDone(); });

    // Wait for listener to be ready
    await sleep(2000);

    // Step 2: ADB stream to .220 — run cat APK | nc D1_IP PORT
    // The stream keeps the session alive with WRTE/OKAY
    const ncCmd = `cat "${apkPath}" | nc -w ${timeoutSec} ${D1_IP} ${port} 2>/dev/null; echo NC_EXIT=$?`;
    log(`    Streaming via nc (port ${port})...`);

    const streamResult = adbExec220(ncCmd, timeoutSec + 30);
    streamResult.then(r => {
      streamDone = true;
      log(`    .220 stream done: ${r.output.toString().trim().slice(0, 50)}`);
      checkDone();
    });

    // Overall timeout
    const overallTimer = setTimeout(() => {
      listener.kill();
      checkDone();
    }, (timeoutSec + 60) * 1000);

    function checkDone() {
      if (!listenerDone) return;
      clearTimeout(overallTimer);

      // Check received file on D1
      try {
        const sizeStr = execSync(`adb -s ${D1_SERIAL} shell "wc -c ${recvFile}"`, {
          timeout: 10000, encoding: 'utf8'
        }).trim();
        const m = sizeStr.match(/^(\d+)/);
        receivedSize = m ? parseInt(m[1]) : 0;
      } catch(e) { receivedSize = 0; }

      resolve(receivedSize);
    }
  });
}

// ═══════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(60));
  console.log('  HYBRID CLONE .220 → D2');
  console.log('═'.repeat(60));
  ensureDir(OUT); ensureDir(path.join(OUT, 'apks'));

  // Verify tunnels
  try {
    execSync(`adb -s ${D1_SERIAL} shell echo D1_OK`, { timeout: 5000 });
    execSync(`adb -s ${D2_SERIAL} shell echo D2_OK`, { timeout: 5000 });
    log('ADB tunnels OK');
  } catch(e) { log('Tunnel(s) down!'); process.exit(1); }

  // Quick ADB stream test
  const test = await adbExec220('echo HYBRID_OK', 10);
  if (!test.output.toString().includes('HYBRID_OK')) {
    log('.220 stream failed!'); process.exit(1);
  }
  log('.220 ADB stream verified');

  // ════════════════════════════════════════════════════════════
  // STEP 1: Pull + Install APKs
  // ════════════════════════════════════════════════════════════
  log('\nSTEP 1: Pull APKs from .220 & install on D2...');

  // Get sizes
  const sizeResult = await adbExec220(
    Object.entries(APK_MAP).map(([p,f]) => `stat -c "%s" "${f}" 2>/dev/null && echo "PKG:${p}"`).join('; '),
    20
  );
  const sizes = {};
  const lines = sizeResult.output.toString().split('\n');
  for (let i = 0; i < lines.length - 1; i++) {
    const numMatch = lines[i].match(/^(\d+)$/);
    const pkgMatch = lines[i+1] && lines[i+1].match(/^PKG:(.+)/);
    if (numMatch && pkgMatch) sizes[pkgMatch[1]] = parseInt(numMatch[1]);
  }

  // Sort by size (smallest first)
  const sorted = Object.entries(APK_MAP).sort((a, b) => (sizes[a[0]] || 999999999) - (sizes[b[0]] || 999999999));
  for (const [p] of sorted) {
    log(`  ${p}: ${((sizes[p]||0)/1024/1024).toFixed(1)} MB`);
  }

  const installed = [];
  let port = 35000;

  for (const [pkg, apkPath] of sorted) {
    const sizeMB = ((sizes[pkg] || 0) / 1024 / 1024).toFixed(1);
    const localApk = path.join(OUT, 'apks', `${pkg}.apk`);
    const timeout = Math.max(60, Math.ceil(parseFloat(sizeMB) / 10) * 60 + 60);

    log(`\n  [${pkg}] ${sizeMB} MB`);

    // Check if already installed on D2
    try {
      const check = execSync(`adb -s ${D2_SERIAL} shell "pm path ${pkg}" 2>/dev/null`, {
        timeout: 5000, encoding: 'utf8'
      });
      if (check.includes('package:')) {
        log(`    Already installed on D2`);
        installed.push(pkg);
        continue;
      }
    } catch(e) {}

    // Pull via hybrid nc relay
    const startTime = Date.now();
    const recvSize = await pullApk(pkg, apkPath, port, timeout);
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

    if (recvSize > 50000) {
      // Pull from D1 to local
      log(`    D1 received: ${(recvSize/1024/1024).toFixed(1)} MB in ${elapsed}s`);
      try {
        execSync(`adb -s ${D1_SERIAL} pull /sdcard/recv_${port}.bin "${localApk}" 2>/dev/null`, { timeout: 120000 });
        execSync(`adb -s ${D1_SERIAL} shell "rm -f /sdcard/recv_${port}.bin" 2>/dev/null`, { timeout: 5000 });

        // Install on D2
        const r = execSync(`adb -s ${D2_SERIAL} install -r -g "${localApk}" 2>&1`, {
          timeout: 180000, encoding: 'utf8'
        });
        if (r.includes('Success')) {
          log(`    ✓ Installed on D2`);
          installed.push(pkg);
        } else {
          log(`    ✗ Install: ${r.trim().slice(0, 80)}`);
        }
      } catch(e) { log(`    ✗ Pull/install err: ${(e.stdout||e.message).slice(0, 80)}`); }
    } else {
      log(`    ✗ Only ${recvSize} bytes received in ${elapsed}s`);
    }

    port++;
    // Clean up D1 storage
    try { execSync(`adb -s ${D1_SERIAL} shell "rm -f /sdcard/recv_${port-1}.bin" 2>/dev/null`, { timeout: 5000 }); } catch(e) {}
  }

  log(`\n  APKs installed: ${installed.length}/${Object.keys(APK_MAP).length}`);

  // ════════════════════════════════════════════════════════════
  // STEP 2: Extract + push app data
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 2: App data extraction + push...');
  let totalData = 0;

  for (const pkg of Object.keys(APK_MAP)) {
    const appDir = ensureDir(path.join(OUT, 'data', pkg));
    const listing = await adbExec220(
      `ls -la /data/data/${pkg}/databases/ 2>/dev/null; echo "===PREFS==="; ls -la /data/data/${pkg}/shared_prefs/ 2>/dev/null`,
      10
    );
    const listStr = listing.output.toString();
    const [dbSec, prefSec] = listStr.split('===PREFS===');

    for (const [section, subdir] of [[dbSec, 'databases'], [prefSec, 'shared_prefs']]) {
      const ext = subdir === 'databases' ? '.db' : '.xml';
      const files = (section || '').split('\n')
        .map(l => { const m = l.match(new RegExp(`\\s(\\d+)\\s+\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}\\s+(.+\\${ext})$`)); return m ? {name:m[2],size:parseInt(m[1])} : null; })
        .filter(f => f && f.size > 0 && f.size < 50000);

      if (files.length > 0) {
        ensureDir(path.join(appDir, subdir));
        for (const f of files.slice(0, subdir === 'databases' ? 5 : 10)) {
          const data = await adbExec220(`cat "/data/data/${pkg}/${subdir}/${f.name}"`, 15);
          if (data.output.length > 10) {
            fs.writeFileSync(path.join(appDir, subdir, f.name), data.output);
            totalData++;
          }
        }
      }
    }
  }

  // Account databases
  for (const db of ['accounts_ce.db', 'accounts_de.db']) {
    const data = await adbExec220(`cat /data/system_ce/0/${db}`, 15);
    if (data.output.length > 100) {
      ensureDir(path.join(OUT, 'accounts'));
      fs.writeFileSync(path.join(OUT, 'accounts', db), data.output);
      log(`  ✓ ${db}: ${data.output.length}B`);
      totalData++;
    }
  }
  log(`  Extracted: ${totalData} data files`);

  // Push to D2
  log('\n  Pushing to D2...');
  let totalPushed = 0;
  for (const pkg of Object.keys(APK_MAP)) {
    const pkgDir = path.join(OUT, 'data', pkg);
    if (!fs.existsSync(pkgDir)) continue;
    try {
      const check = execSync(`adb -s ${D2_SERIAL} shell "pm path ${pkg}" 2>/dev/null`, { timeout: 5000, encoding: 'utf8' });
      if (!check.includes('package:')) continue;
    } catch(e) { continue; }

    try { execSync(`adb -s ${D2_SERIAL} shell "am force-stop ${pkg}" 2>/dev/null`, { timeout: 5000 }); } catch(e) {}
    let pushed = 0;
    for (const sub of ['databases', 'shared_prefs']) {
      const sd = path.join(pkgDir, sub);
      if (!fs.existsSync(sd)) continue;
      execSync(`adb -s ${D2_SERIAL} shell "mkdir -p /data/data/${pkg}/${sub}" 2>/dev/null`, { timeout: 5000 });
      for (const f of fs.readdirSync(sd)) {
        if (fs.statSync(path.join(sd, f)).size < 10) continue;
        try {
          execSync(`adb -s ${D2_SERIAL} push "${path.join(sd, f)}" "/data/data/${pkg}/${sub}/${f}" 2>/dev/null`, { timeout: 30000 });
          pushed++;
        } catch(e) {}
      }
    }
    if (pushed > 0) {
      try {
        const uid = execSync(`adb -s ${D2_SERIAL} shell "stat -c %u /data/data/${pkg}" 2>/dev/null`, { timeout: 5000, encoding: 'utf8' }).trim();
        if (/^\d+$/.test(uid)) execSync(`adb -s ${D2_SERIAL} shell "chown -R ${uid}:${uid} /data/data/${pkg}/databases /data/data/${pkg}/shared_prefs" 2>/dev/null`, { timeout: 10000 });
      } catch(e) {}
      totalPushed += pushed;
      log(`  ${pkg}: ${pushed} files`);
    }
  }

  // Account DBs to D2
  for (const db of ['accounts_ce.db', 'accounts_de.db']) {
    const f = path.join(OUT, 'accounts', db);
    if (fs.existsSync(f) && fs.statSync(f).size > 100) {
      try { execSync(`adb -s ${D2_SERIAL} push "${f}" "/data/system_ce/0/${db}" 2>/dev/null`, { timeout: 15000 }); totalPushed++; log(`  ✓ ${db}`); } catch(e) {}
    }
  }
  try { execSync(`adb -s ${D2_SERIAL} shell "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED" 2>/dev/null`, { timeout: 10000 }); } catch(e) {}
  log(`  Total pushed: ${totalPushed}`);

  // ════════════════════════════════════════════════════════════
  // STEP 3: Proxy
  // ════════════════════════════════════════════════════════════
  log('\n\nSTEP 3: Proxy...');
  const pxData = await adbExec220('getprop ro.sys.cloud.proxy.type; echo "|"; getprop ro.sys.cloud.proxy.mode; echo "|"; getprop ro.sys.cloud.proxy.data; echo "|"; settings get global http_proxy 2>/dev/null', 10);
  const pxStr = pxData.output.toString().trim();
  log(`  .220 proxy: ${pxStr.slice(0, 200)}`);
  const pp = pxStr.split('|').map(s => s.trim());
  if (pp[2] && pp[2].length > 2) {
    const r = await apiPost('/vcpcloud/api/padApi/modifyProxy', { padCodes: [D2_PAD], proxyType: parseInt(pp[0])||1, proxyMode: parseInt(pp[1])||1, proxyData: pp[2] });
    log(`  modifyProxy: ${r.code} ${r.msg||''}`);
  } else if (pp[3] && pp[3] !== 'null') {
    try { execSync(`adb -s ${D2_SERIAL} shell "settings put global http_proxy '${pp[3]}'" 2>/dev/null`, { timeout: 10000 }); } catch(e) {}
    log(`  http_proxy: ${pp[3]}`);
  } else { log('  No proxy found'); }

  // ════════════════════════════════════════════════════════════
  console.log('\n' + '═'.repeat(60));
  console.log('  CLONE SUMMARY');
  console.log(`  APKs: ${installed.length}/${Object.keys(APK_MAP).length}`);
  const miss = Object.keys(APK_MAP).filter(p => !installed.includes(p));
  if (miss.length) console.log(`  Missing: ${miss.join(', ')}`);
  console.log(`  Data: ${totalData} extracted, ${totalPushed} pushed`);
  console.log('═'.repeat(60));
}

main().catch(e => console.error('FATAL:', e));
