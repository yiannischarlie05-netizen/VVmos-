#!/usr/bin/env node
/**
 * Relay file from .220 → D1 → local using:
 *  - syncCmd on D1 for persistent nc listener
 *  - raw ADB to .220 for file push trigger
 *  - adb pull from D1 to local
 */
const { execSync } = require('child_process');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const { AK, SK, HOST, D1, CT, SHD } = require('../shared/vmos_api');
const D1_PAD = 'ACP250923JS861KJ';
const D1_SERIAL = 'localhost:8479';
const D1_IP = '10.0.96.174';
const SRC_IP = '10.0.26.220';

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

function sign(b){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z'),sd=xd.slice(0,8),CT='application/json;charset=UTF-8',SHD='content-type;host;x-content-sha256;x-date';const bh=crypto.createHash('sha256').update(b,'utf8').digest('hex');const can=`host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;const ch=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=`HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;let k=crypto.createHmac('sha256',SK).update(sd).digest();k=crypto.createHmac('sha256',k).update('armcloud-paas').digest();k=crypto.createHmac('sha256',k).update('request').digest();return{'content-type':CT,'x-date':xd,'x-host':HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256',k).update(sts).digest('hex')}`};}

function apiPost(ep,d,t){return new Promise(ok=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b);const req=https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(t||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}

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

// Send raw ADB command to .220 via D1's nc (one-shot, first ~4KB output)
function triggerOn220(cmd, waitSec) {
  waitSec = waitSec || 5;
  const open = buildOpen(cmd);
  fs.writeFileSync('/tmp/adb_open_relay.bin', open);
  execSync(`adb -s ${D1_SERIAL} push /tmp/adb_open_relay.bin /sdcard/open_relay.bin 2>/dev/null`);

  const script = [
    '#!/system/bin/sh',
    `(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_relay.bin; sleep ${waitSec}) | nc -w ${waitSec + 3} ${SRC_IP} 5555 2>/dev/null | strings`
  ].join('\n');
  fs.writeFileSync('/tmp/d1_trigger.sh', script);
  execSync(`adb -s ${D1_SERIAL} push /tmp/d1_trigger.sh /sdcard/trigger.sh 2>/dev/null`);

  try {
    return execSync(`adb -s ${D1_SERIAL} shell sh /sdcard/trigger.sh`, {
      timeout: (waitSec + 10) * 1000, encoding: 'utf8', maxBuffer: 5 * 1024 * 1024
    }).split('\n').filter(l => !l.match(/^(CNXN|OKAY|WRTE|CLSE|device::)/)).join('\n').trim();
  } catch (e) { return 'ERR:' + e.message.slice(0, 80); }
}

async function main() {
  // Ensure cnxn.bin on D1
  const cnxn = Buffer.from('434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex');
  fs.writeFileSync('/tmp/adb_cnxn.bin', cnxn);
  execSync(`adb -s ${D1_SERIAL} push /tmp/adb_cnxn.bin /sdcard/cnxn.bin 2>/dev/null`);

  // ── Test 1: Verify .220 → D1 connectivity ──
  log('Test 1: Basic .220 → D1 connectivity');

  // Start listener on D1 via syncCmd (persistent)
  log('  Starting nc listener on D1 via syncCmd...');
  // Use asyncCmd (non-blocking) - start listener in background
  const listenerResult = syncCmd(D1_PAD,
    'rm -f /sdcard/recv_test.bin; nc -l -p 33900 -w 30 > /sdcard/recv_test.bin; wc -c /sdcard/recv_test.bin',
    40);

  // Wait for listener to be ready
  await sleep(3000);

  // Trigger .220 to send test data
  log('  Triggering .220...');
  triggerOn220(`echo HELLO_TEST_$(date +%s) | nc -w 5 ${D1_IP} 33900`, 8);

  // Wait for transfer + check
  const lr = await listenerResult;
  log(`  Listener result: ${lr}`);

  // Check file on D1
  const check = await syncCmd(D1_PAD, 'cat /sdcard/recv_test.bin 2>/dev/null; echo "---"; wc -c /sdcard/recv_test.bin 2>/dev/null', 10);
  log(`  File content: ${check}`);

  if (!check.includes('HELLO_TEST')) {
    log('ERROR: .220 → D1 connectivity broken. Trying debug...');
    // Debug: check if listener was actually running
    const debug = await syncCmd(D1_PAD, 'netstat -tlnp 2>/dev/null | grep 33900; ps | grep nc', 10);
    log(`  Debug: ${debug}`);
    return;
  }

  // ── Test 2: Pull a small file ──
  log('\nTest 2: Pull /system/build.prop from .220');

  log('  Starting listener...');
  const lr2 = syncCmd(D1_PAD,
    'rm -f /sdcard/recv_prop.bin; nc -l -p 33901 -w 30 > /sdcard/recv_prop.bin; wc -c /sdcard/recv_prop.bin',
    40);
  await sleep(3000);

  log('  Triggering file transfer...');
  triggerOn220(`cat /system/build.prop | nc -w 15 ${D1_IP} 33901 2>/dev/null`, 20);

  const lr2r = await lr2;
  log(`  Listener: ${lr2r}`);

  const size2 = await syncCmd(D1_PAD, 'wc -c /sdcard/recv_prop.bin 2>/dev/null', 10);
  log(`  File size: ${size2}`);

  if (parseInt(size2) > 100) {
    // Pull to local
    try {
      execSync(`adb -s ${D1_SERIAL} pull /sdcard/recv_prop.bin /tmp/test_prop.txt 2>/dev/null`);
      const content = fs.readFileSync('/tmp/test_prop.txt', 'utf8');
      log(`  ✓ Got ${content.length} chars: ${content.slice(0, 100)}...`);
    } catch (e) { log(`  Pull failed: ${e.message.slice(0, 80)}`); }
  }

  // ── Test 3: Pull small APK ──
  log('\nTest 3: Pull com.app.trademo APK (8.3MB)');

  log('  Starting listener...');
  const lr3 = syncCmd(D1_PAD,
    'rm -f /sdcard/recv_apk.bin; nc -l -p 33902 -w 120 > /sdcard/recv_apk.bin; wc -c /sdcard/recv_apk.bin',
    150);
  await sleep(3000);

  log('  Triggering APK transfer...');
  triggerOn220(
    `cat "/data/app/~~Wxk7-55Bxuh7YZnn2ZFEiA==/com.app.trademo-5zyYOz2-ozsLRT0GbiAuSQ==/base.apk" | nc -w 60 ${D1_IP} 33902 2>/dev/null`,
    70
  );

  const lr3r = await lr3;
  log(`  Listener: ${lr3r}`);

  const size3 = await syncCmd(D1_PAD, 'wc -c /sdcard/recv_apk.bin 2>/dev/null', 10);
  log(`  APK size on D1: ${size3}`);
}

main().catch(e => console.error('FATAL:', e));
