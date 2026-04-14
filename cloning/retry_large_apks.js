#!/usr/bin/env node
/**
 * Retry the 5 large APKs that failed due to adb pull timeout.
 * Uses hybrid nc relay + longer adb pull timeout (600s).
 */
const net = require('net');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const D1_ADB_PORT = 8479;
const D1_SERIAL = 'localhost:8479';
const D2_SERIAL = 'localhost:7391';
const SRC_IP = '10.0.26.220';
const D1_IP = '10.0.96.174';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data', 'apks');

const A_CNXN=0x4e584e43,A_OPEN=0x4e45504f,A_OKAY=0x59414b4f,A_WRTE=0x45545257,A_CLSE=0x45534c43;
function makeHeader(cmd,a0,a1,dl,dc){const h=Buffer.alloc(24);h.writeUInt32LE(cmd,0);h.writeUInt32LE(a0,4);h.writeUInt32LE(a1,8);h.writeUInt32LE(dl,12);h.writeUInt32LE(dc,16);h.writeUInt32LE((cmd^0xFFFFFFFF)>>>0,20);return h;}
function crc(d){let s=0;for(let i=0;i<d.length;i++)s+=d[i];return s>>>0;}
function makeCnxn(){const p=Buffer.from('host::\x00');return Buffer.concat([makeHeader(A_CNXN,0x01000000,256*1024,p.length,crc(p)),p]);}
function makeOpen(lid,svc){const p=Buffer.from(svc+'\x00');return Buffer.concat([makeHeader(A_OPEN,lid,0,p.length,crc(p)),p]);}
function makeOkay(lid,rid){return makeHeader(A_OKAY,lid,rid,0,0);}
function parsePackets(buf){const pkts=[];let o=0;while(o+24<=buf.length){const cmd=buf.readUInt32LE(o),a0=buf.readUInt32LE(o+4),a1=buf.readUInt32LE(o+8),dl=buf.readUInt32LE(o+12);if(o+24+dl>buf.length)break;pkts.push({cmd,arg0:a0,arg1:a1,data:buf.slice(o+24,o+24+dl)});o+=24+dl;}return{packets:pkts,remaining:buf.slice(o)};}

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

function adbExec220(cmd, sec) {
  return new Promise(resolve => {
    let trid=null,srid=null,sc=false,done=false,res=Buffer.alloc(0),buf=Buffer.alloc(0),tb=Buffer.alloc(0);
    const sock=net.createConnection(D1_ADB_PORT,'127.0.0.1',()=>sock.write(makeCnxn()));
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

const FAILED = [
  ['ru.yandex.taxi', '/data/app/~~wK2mAP68gZwmyFPp6UeaOA==/ru.yandex.taxi-PKOPpTH5qtvKYkprFt340A==/base.apk', 110],
  ['ru.ozon.app.android', '/data/app/~~VEvGmwbOcylt8Lcx2Qp9hg==/ru.ozon.app.android-QBTantiUD_bSeBU-eHSV1Q==/base.apk', 172],
  ['ru.rostel', '/data/app/~~PmomRTxq1p5ywefa9_lGnw==/ru.rostel-a12u2iLNxh0NxbBhsamL8w==/base.apk', 204],
  ['ru.yoo.money', '/data/app/~~Yf1SUfwhCxaEibOm-_Ctig==/ru.yoo.money-YqZiD1qUsxxsuETehWeIrA==/base.apk', 302],
  ['com.wildberries.ru', '/data/app/~~B6750jl6r8XGKnOM0-hRAQ==/com.wildberries.ru-lX42uzsZ4Zs675Qy80BYWQ==/base.apk', 393],
];

async function main() {
  log('Retrying 5 large APKs with longer timeouts...');

  for (const [pkg, apkPath, sizeMB] of FAILED) {
    const port = 36000 + FAILED.indexOf([pkg, apkPath, sizeMB]);
    const usePort = 36000 + FAILED.findIndex(f => f[0] === pkg);
    const recvFile = `/sdcard/recv_large_${pkg.replace(/\./g,'_')}.bin`;
    const localApk = path.join(OUT, `${pkg}.apk`);

    log(`\n[${pkg}] ${sizeMB} MB`);

    // Check if already installed on D2
    try {
      const check = execSync(`adb -s ${D2_SERIAL} shell "pm path ${pkg}" 2>/dev/null`, {
        timeout: 5000, encoding: 'utf8'
      });
      if (check.includes('package:')) { log('  Already installed'); continue; }
    } catch(e) {}

    // Kill any old nc
    try { execSync(`adb -s ${D1_SERIAL} shell "killall nc 2>/dev/null"`, { timeout: 3000 }); } catch(e) {}
    await sleep(1000);

    // Spawn listener on D1
    const listener = spawn('adb', ['-s', D1_SERIAL, 'shell',
      `rm -f ${recvFile}; nc -l -p ${usePort} -w 600 > ${recvFile}; echo RECV_DONE; wc -c ${recvFile}`
    ], { stdio: ['pipe', 'pipe', 'pipe'] });
    let lout = '';
    listener.stdout.on('data', d => lout += d.toString());
    listener.on('close', () => {});

    await sleep(2000);

    // Stream from .220
    log('  Pulling from .220 via nc...');
    const startTime = Date.now();
    const stream = adbExec220(`cat "${apkPath}" | nc -w 600 ${D1_IP} ${usePort} 2>/dev/null; echo NC_EXIT=$?`, 660);

    // Wait for listener to finish
    await new Promise(resolve => {
      const done = () => { clearTimeout(timer); resolve(); };
      listener.on('close', done);
      const timer = setTimeout(() => { listener.kill(); done(); }, 660000);
    });

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    log(`  Listener done in ${elapsed}s: ${lout.trim().slice(-60)}`);

    // Check received file
    let recvSize = 0;
    try {
      const s = execSync(`adb -s ${D1_SERIAL} shell "wc -c ${recvFile}"`, { timeout: 10000, encoding: 'utf8' }).trim();
      const m = s.match(/^(\d+)/);
      recvSize = m ? parseInt(m[1]) : 0;
    } catch(e) {}

    if (recvSize < 50000) { log(`  ✗ Only ${recvSize} bytes`); continue; }
    log(`  D1 has ${(recvSize/1024/1024).toFixed(1)} MB`);

    // Pull from D1 with 600s timeout
    log('  Pulling from D1 to local (long timeout)...');
    try {
      execSync(`adb -s ${D1_SERIAL} pull "${recvFile}" "${localApk}"`, { timeout: 600000 });
      const localSize = fs.statSync(localApk).size;
      log(`  Local: ${(localSize/1024/1024).toFixed(1)} MB`);
    } catch(e) { log(`  ✗ Pull failed: ${e.message.slice(0, 80)}`); continue; }

    // Install on D2 with 600s timeout
    log('  Installing on D2...');
    try {
      const r = execSync(`adb -s ${D2_SERIAL} install -r -g "${localApk}" 2>&1`, {
        timeout: 600000, encoding: 'utf8'
      });
      if (r.includes('Success')) {
        log(`  ✓ Installed!`);
      } else {
        log(`  ✗ Install: ${r.trim().slice(0, 80)}`);
      }
    } catch(e) { log(`  ✗ Install err: ${(e.stdout||e.message).slice(0, 80)}`); }

    // Cleanup D1
    try { execSync(`adb -s ${D1_SERIAL} shell "rm -f ${recvFile}" 2>/dev/null`, { timeout: 5000 }); } catch(e) {}
  }

  log('\nDone. Checking final install status...');
  for (const [pkg] of FAILED) {
    try {
      const check = execSync(`adb -s ${D2_SERIAL} shell "pm path ${pkg}" 2>/dev/null`, {
        timeout: 5000, encoding: 'utf8'
      });
      log(`  ${pkg}: ${check.includes('package:') ? '✓' : '✗'}`);
    } catch(e) { log(`  ${pkg}: ✗`); }
  }
}

main().catch(e => console.error('FATAL:', e));
