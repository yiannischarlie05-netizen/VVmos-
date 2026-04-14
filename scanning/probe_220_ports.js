#!/usr/bin/env node
/**
 * Probe .220's local ports to find xu_daemon command interface.
 * Also check D1's own xu_daemon to understand the protocol.
 */
const net = require('net');
const https = require('https');
const crypto = require('crypto');

const { AK, SK, HOST, D1, CT, SHD } = require('../shared/vmos_api');
const SRC_IP = '10.0.26.220';

// --- VMOS API helpers ---
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

// --- ADB stream to .220 ---
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
  console.log('  PROBING .220 LOCAL PORTS + XU_DAEMON');
  console.log('═'.repeat(60));

  // PART 1: Understand xu_daemon on D1 first
  log('=== D1: xu_daemon analysis ===');
  
  const d1xu = await syncCmd(D1, 'ps -A | grep xu_daemon; echo ---; ls -la /proc/$(pidof xu_daemon)/fd/ 2>/dev/null | head -20; echo ---; cat /proc/$(pidof xu_daemon)/cmdline 2>/dev/null | tr "\\0" " "; echo', 20);
  log('D1 xu_daemon:\n' + d1xu);

  const d1ports = await syncCmd(D1, 'ss -tlnp 2>/dev/null | grep -v "^State"', 15);
  log('\nD1 listening ports:\n' + d1ports);

  // Check xu_daemon's open files and sockets
  const d1fds = await syncCmd(D1, 'ls -la /proc/$(pidof xu_daemon)/fd/ 2>/dev/null | grep socket | head -10; echo ---; cat /proc/$(pidof xu_daemon)/net/tcp 2>/dev/null | head -10', 20);
  log('\nD1 xu_daemon sockets:\n' + d1fds);

  // PART 2: Probe .220's ports
  log('\n=== .220: Port probing ===');
  const ports = [19090, 36351, 52220, 52253, 57891];

  for (const port of ports) {
    log(`\nProbing port ${port}...`);
    
    // Try HTTP GET
    const httpGet = await adbExec220(`echo -e "GET / HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n" | nc -w 3 127.0.0.1 ${port} 2>&1 | head -5`, 10);
    log(`  HTTP GET: ${httpGet.slice(0, 150)}`);
    
    // Try sending a JSON command (like syncCmd might use)
    const jsonCmd = await adbExec220(`echo '{"cmd":"exec","script":"id"}' | nc -w 3 127.0.0.1 ${port} 2>&1 | head -5`, 10);
    log(`  JSON cmd: ${jsonCmd.slice(0, 150)}`);
  }

  // PART 3: Check xu_daemon binary for clues
  log('\n=== .220: xu_daemon binary analysis ===');
  const xuBin = await adbExec220('file /system/bin/xu_daemon 2>/dev/null; echo ---; strings /system/bin/xu_daemon 2>/dev/null | grep -iE "port|listen|socket|cmd|exec|root|http|json|grpc" | sort -u | head -30', 20);
  log(xuBin);

  // PART 4: Check xu_daemon environment and config  
  log('\n=== .220: xu_daemon config ===');
  const xuEnv = await adbExec220('cat /proc/$(pidof xu_daemon)/environ 2>/dev/null | tr "\\0" "\\n" | head -20; echo ---; cat /proc/$(pidof xu_daemon)/cmdline 2>/dev/null | tr "\\0" " "; echo ---; ls /data/local/tmp/ 2>/dev/null', 15);
  log(xuEnv);

  // PART 5: Check process with port binding
  log('\n=== .220: Which process owns which port ===');
  const portOwners = await adbExec220('ss -tlnp 2>/dev/null', 10);
  log(portOwners);

  // PART 6: Try nsenter as root to PID 300 (xu_daemon)
  log('\n=== .220: nsenter to xu_daemon PID ===');
  const nsXu = await adbExec220('nsenter -t 300 -m -- id 2>&1; echo EXIT=$?', 10);
  log(nsXu);
}

main().catch(e => console.error('FATAL:', e));
