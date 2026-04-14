#!/usr/bin/env node
/**
 * Probe xu_daemon HTTP API on D1 (port 8779) and .220 (port 19090)
 * to understand auth and find a way to execute root commands.
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
  console.log('═'.repeat(60));
  console.log('  XU_DAEMON API PROBING');
  console.log('═'.repeat(60));

  // Step 1: Probe D1's xu_daemon HTTP port (8779)
  log('=== D1: Probing local xu_daemon on port 8779 ===');
  
  // GET /
  const d1get = await syncCmd(D1, 'curl -s -w "\\nHTTP_CODE:%{http_code}" http://127.0.0.1:8779/ 2>&1', 10);
  log('GET /: ' + d1get.slice(0, 300));

  // GET with various paths
  const d1paths = await syncCmd(D1, 'for p in /api /cmd /exec /shell /sync /health /status /v1 /rpc; do echo "PATH:$p"; curl -s -w " HTTP:%{http_code}\\n" http://127.0.0.1:8779$p 2>&1 | head -2; done', 20);
  log('Paths:\n' + d1paths);

  // POST with JSON
  const d1post = await syncCmd(D1, 'curl -s -X POST -H "Content-Type: application/json" -d \'{"cmd":"id"}\' http://127.0.0.1:8779/ 2>&1 | head -5', 10);
  log('POST /: ' + d1post.slice(0, 300));

  // Step 2: Get the 401 response body from .220 port 19090
  log('\n=== .220: Probing xu_daemon on port 19090 ===');

  const r401 = await adbExec220('curl -s -v http://127.0.0.1:19090/ 2>&1', 10);
  log('GET / verbose:\n' + r401.slice(0, 500));

  // Try various paths
  const paths220 = await adbExec220('for p in / /api /cmd /exec /shell /sync /health /status /v1 /rpc /api/v1/cmd /syncCmd; do echo "PATH:$p $(curl -s -o /dev/null -w %{http_code} http://127.0.0.1:19090$p 2>&1)"; done', 20);
  log('Paths:\n' + paths220);

  // Try POST with various bodies
  log('\nPOST attempts...');
  const post1 = await adbExec220('curl -s -X POST -H "Content-Type: application/json" -d \'{"scriptContent":"id"}\' http://127.0.0.1:19090/ 2>&1', 10);
  log('POST /: ' + post1.slice(0, 300));

  const post2 = await adbExec220('curl -s -X POST -H "Content-Type: application/json" -d \'{"scriptContent":"id"}\' http://127.0.0.1:19090/syncCmd 2>&1', 10);
  log('POST /syncCmd: ' + post2.slice(0, 300));

  const post3 = await adbExec220('curl -s -X POST -H "Content-Type: application/json" -d \'{"scriptContent":"id"}\' http://127.0.0.1:19090/api/v1/cmd 2>&1', 10);
  log('POST /api/v1/cmd: ' + post3.slice(0, 300));

  // Step 3: Try the same auth headers from D1 on .220
  log('\n=== .220: Try with VMOS-style auth ===');
  // D1 has port 8779 - check what auth it accepts
  const d1noAuth = await syncCmd(D1, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8779/ 2>&1', 10);
  log('D1 port 8779 no-auth code: ' + d1noAuth);

  // Check if .220 has the same port as D1 (8779)
  const check8779 = await adbExec220('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8779/ 2>&1', 10);
  log('.220 port 8779: ' + check8779);

  // Step 4: Check all .220 ports with more detail
  log('\n=== .220: Detailed port scan ===');
  const portScan = await adbExec220('for p in 19090 52220 52253 57891; do echo "PORT:$p"; timeout 2 curl -s -v http://127.0.0.1:$p/ 2>&1 | head -8; echo "---"; done', 30);
  log(portScan);
}

main().catch(e => console.error('FATAL:', e));
