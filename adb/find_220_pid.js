#!/usr/bin/env node
const https = require('https');
const crypto = require('crypto');

const { AK, SK, HOST, D1, CT, SHD } = require('../shared/vmos_api');

function sign(b) {
  const xd = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  const sd = xd.slice(0, 8), CT = 'application/json;charset=UTF-8', SHD = 'content-type;host;x-content-sha256;x-date';
  const bh = crypto.createHash('sha256').update(b, 'utf8').digest('hex');
  const can = `host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;
  const ch = crypto.createHash('sha256').update(can, 'utf8').digest('hex');
  const sts = `HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;
  let k = crypto.createHmac('sha256', SK).update(sd).digest();
  k = crypto.createHmac('sha256', k).update('armcloud-paas').digest();
  k = crypto.createHmac('sha256', k).update('request').digest();
  return { 'content-type': CT, 'x-date': xd, 'x-host': HOST, 'authorization': `HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256', k).update(sts).digest('hex')}` };
}
function apiPost(ep, d, t) {
  return new Promise(ok => {
    const b = JSON.stringify(d || {}); const h = sign(b); const buf = Buffer.from(b);
    const req = https.request({ hostname: HOST, path: ep, method: 'POST', headers: { ...h, 'content-length': buf.length }, timeout: (t || 60) * 1000 }, res => {
      let r = ''; res.on('data', c => r += c); res.on('end', () => { try { ok(JSON.parse(r)); } catch { ok({ code: -1 }); } });
    });
    req.on('timeout', () => { req.destroy(); ok({ code: -99 }); });
    req.on('error', e => ok({ code: -99, msg: e.message }));
    req.write(buf); req.end();
  });
}

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);

async function main() {
  // Known PIDs with persistent_properties from probe
  const pids = [1, 10, 11, 162, 174, 176, 177, 178, 180, 203, 204, 205, 206, 1028, 1046, 1133, 1137, 1379, 1545, 1566];

  log('Searching ' + pids.length + ' PIDs for .220 phone (79286458086)...');

  // Search in batches of 5
  for (let i = 0; i < pids.length; i += 5) {
    const batch = pids.slice(i, i + 5);
    const cmd = batch.map(p =>
      `strings /proc/${p}/root/data/property/persistent_properties 2>/dev/null | grep -q 79286458086 && echo MATCH:${p}`
    ).join('; ');

    const r = await syncCmd(D1, 'nsenter -t 1 -m -u -i -n -p -- sh -c "' + cmd + '"', 30);
    if (r.includes('MATCH:')) {
      log('FOUND! ' + r);
    } else {
      log('Batch ' + batch.join(',') + ': no match');
    }
  }

  // Also search by IP address pattern
  log('\nSearching by IP 10.0.26.220...');
  for (let i = 0; i < pids.length; i += 5) {
    const batch = pids.slice(i, i + 5);
    const cmd = batch.map(p =>
      `cat /proc/${p}/root/data/property/persistent_properties 2>/dev/null | strings | grep -q "10.0.26" && echo IPMATCH:${p}`
    ).join('; ');

    const r = await syncCmd(D1, 'nsenter -t 1 -m -u -i -n -p -- sh -c "' + cmd + '"', 30);
    if (r.includes('IPMATCH:')) {
      log('FOUND by IP! ' + r);
    }
  }

  // Search by IMEI
  log('\nSearching by IMEI 895410082175508...');
  for (let i = 0; i < pids.length; i += 5) {
    const batch = pids.slice(i, i + 5);
    const cmd = batch.map(p =>
      `strings /proc/${p}/root/data/property/persistent_properties 2>/dev/null | grep -q 895410082175508 && echo IMEIMATCH:${p}`
    ).join('; ');

    const r = await syncCmd(D1, 'nsenter -t 1 -m -u -i -n -p -- sh -c "' + cmd + '"', 30);
    if (r.includes('IMEIMATCH:')) {
      log('FOUND by IMEI! ' + r);
    }
  }

  // Also try: list what's in /data on each PID to identify .220 by its installed apps
  log('\nChecking installed apps on each container...');
  for (const pid of pids) {
    const r = await syncCmd(D1,
      'nsenter -t 1 -m -u -i -n -p -- sh -c "ls /proc/' + pid + '/root/data/data/ 2>/dev/null | grep -c yandex; echo PKG_COUNT=$(ls /proc/' + pid + '/root/data/data/ 2>/dev/null | wc -l)"',
      15);
    if (r.includes('PKG_COUNT=') && !r.startsWith('0')) {
      const yandex = r.split('\n')[0];
      log(`  PID ${pid}: yandex=${yandex} ${r.split('\n').slice(1).join(' ')}`);
    }
  }

  // Also check network config of each init process
  log('\nChecking IPs per container PID...');
  const initPids = [1, 10, 11];
  for (const pid of pids) {
    const r = await syncCmd(D1,
      'nsenter -t 1 -m -u -i -n -p -- cat /proc/' + pid + '/net/fib_trie 2>/dev/null | grep -oE "10\\.0\\.[0-9]+\\.[0-9]+" | sort -u | head -5',
      10);
    if (r.length > 5 && r.includes('10.0.')) {
      log(`  PID ${pid}: ${r.replace(/\n/g, ', ')}`);
    }
  }
}

main().catch(e => console.error('FATAL:', e));
