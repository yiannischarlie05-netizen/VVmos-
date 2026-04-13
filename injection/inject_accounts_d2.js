#!/usr/bin/env node
/**
 * Inject accounts into D2 using root access.
 * Since sqlite3 is not available, we:
 * 1. Copy accounts_ce.db from .220 via D1 relay (D1 has root + can read .220's db)
 * 2. OR: Manually construct accounts_ce.db and push it
 * 3. OR: Use Android's `cmd account` or content provider to add accounts
 */
const net = require('net');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');
const D2_SERIAL = 'localhost:7391';
const SRC_IP = '10.0.26.220';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');

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
const sleep = ms => new Promise(r => setTimeout(r, ms));

// Chunked file injection via syncCmd
const CHUNK_SIZE = 3000;
async function injectFile(pad, b64Data, destPath) {
  const clean = b64Data.replace(/\s/g, '');
  const chunks = [];
  for (let i = 0; i < clean.length; i += CHUNK_SIZE) {
    chunks.push(clean.slice(i, i + CHUNK_SIZE));
  }
  if (chunks.length === 0) return false;

  if (chunks.length === 1) {
    const r = await syncCmd(pad, `printf '%s' '${chunks[0]}' | base64 -d > "${destPath}" && echo OK`, 30);
    return r.includes('OK');
  }

  const tmp = `/data/local/tmp/inject_${Date.now()}.b64`;
  let r = await syncCmd(pad, `printf '%s' '${chunks[0]}' > "${tmp}" && echo OK`, 15);
  if (!r.includes('OK')) return false;

  for (let i = 1; i < chunks.length; i++) {
    r = await syncCmd(pad, `printf '%s' '${chunks[i]}' >> "${tmp}" && echo OK`, 15);
    if (!r.includes('OK')) return false;
  }

  r = await syncCmd(pad, `base64 -d "${tmp}" > "${destPath}" && rm -f "${tmp}" && echo OK`, 30);
  return r.includes('OK');
}

async function main() {
  console.log('═'.repeat(60));
  console.log('  INJECT ACCOUNTS + DATA INTO D2');
  console.log('═'.repeat(60));

  // Ensure root
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D1, D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  await sleep(2000);

  // ══════════════════════════════════════════════
  // STEP 1: Get accounts_ce.db from D1 (which has root + sqlite3-like tools)
  // ══════════════════════════════════════════════
  log('=== STEP 1: Extract D1 accounts_ce.db for structure reference ===');
  
  // Check if D1 has sqlite3
  const hasSqlite = await syncCmd(D1, 'which sqlite3 2>/dev/null; ls /system/xbin/sqlite3 /system/bin/sqlite3 2>/dev/null', 10);
  log('D1 sqlite3: ' + hasSqlite);

  // Extract D1's accounts_ce.db 
  const d1AccB64 = await syncCmd(D1, 'base64 /data/system_ce/0/accounts_ce.db 2>/dev/null', 30);
  if (d1AccB64.length > 100) {
    const d1AccFile = path.join(OUT, 'app_data', 'd1_accounts_ce.db');
    fs.writeFileSync(d1AccFile, Buffer.from(d1AccB64.replace(/\s/g, ''), 'base64'));
    log('D1 accounts_ce.db: ' + fs.statSync(d1AccFile).size + ' bytes');
    
    // Read it locally with sqlite3
    try {
      const schema = execSync(`sqlite3 "${d1AccFile}" ".schema accounts"`, { encoding: 'utf8', timeout: 5000 });
      log('Schema: ' + schema.slice(0, 300));
      
      const rows = execSync(`sqlite3 "${d1AccFile}" "SELECT * FROM accounts;"`, { encoding: 'utf8', timeout: 5000 });
      log('D1 accounts: ' + rows);
    } catch (e) {
      log('Local sqlite3: ' + (e.message || '').slice(0, 100));
    }
  }

  // ══════════════════════════════════════════════
  // STEP 2: Create a fresh accounts_ce.db with .220's accounts
  // ══════════════════════════════════════════════
  log('\n=== STEP 2: Create accounts_ce.db with .220 accounts ===');
  
  // First get D2's current db to preserve structure
  const d2AccB64 = await syncCmd(D2, 'base64 /data/system_ce/0/accounts_ce.db 2>/dev/null', 30);
  const d2AccFile = path.join(OUT, 'app_data', 'd2_accounts_ce.db');
  
  if (d2AccB64.length > 100 && !d2AccB64.includes('inaccessible')) {
    fs.writeFileSync(d2AccFile, Buffer.from(d2AccB64.replace(/\s/g, ''), 'base64'));
    log('D2 accounts_ce.db downloaded: ' + fs.statSync(d2AccFile).size + ' bytes');
  } else {
    // D2 might not have the file yet, use D1's as template
    log('D2 accounts_ce.db not found, using D1 as template');
    const d1File = path.join(OUT, 'app_data', 'd1_accounts_ce.db');
    if (fs.existsSync(d1File)) {
      fs.copyFileSync(d1File, d2AccFile);
    }
  }

  // Modify locally with sqlite3 if available
  try {
    // Clear existing accounts and insert .220's
    execSync(`sqlite3 "${d2AccFile}" "DELETE FROM accounts;"`, { timeout: 5000 });
    execSync(`sqlite3 "${d2AccFile}" "DELETE FROM authtokens;"`, { timeout: 5000 });
    execSync(`sqlite3 "${d2AccFile}" "DELETE FROM extras;"`, { timeout: 5000 });
    execSync(`sqlite3 "${d2AccFile}" "DELETE FROM grants;"`, { timeout: 5000 });
    
    // Insert .220 accounts
    execSync(`sqlite3 "${d2AccFile}" "INSERT INTO accounts (_id, name, type, previous_name) VALUES (1, 'OZON ID', 'ru.ozon.id.authorized.account', '');"`, { timeout: 5000 });
    execSync(`sqlite3 "${d2AccFile}" "INSERT INTO accounts (_id, name, type, previous_name) VALUES (2, 'Максим Сирож #2042295278 ﹫', 'com.yandex.passport', '');"`, { timeout: 5000 });
    
    // Verify
    const verify = execSync(`sqlite3 "${d2AccFile}" "SELECT * FROM accounts;"`, { encoding: 'utf8', timeout: 5000 });
    log('Modified db accounts: ' + verify);
    
    log('DB file size: ' + fs.statSync(d2AccFile).size + ' bytes');
  } catch (e) {
    log('sqlite3 modify error: ' + (e.message || '').slice(0, 200));
    // If no local sqlite3, try installing it
    try {
      execSync('which sqlite3', { timeout: 3000 });
    } catch {
      log('No local sqlite3 either. Will try alternative injection.');
    }
  }

  // ══════════════════════════════════════════════
  // STEP 3: Push accounts_ce.db to D2
  // ══════════════════════════════════════════════
  log('\n=== STEP 3: Push accounts_ce.db to D2 ===');
  
  if (fs.existsSync(d2AccFile) && fs.statSync(d2AccFile).size > 1000) {
    const b64 = fs.readFileSync(d2AccFile).toString('base64');
    log('Pushing ' + b64.length + ' base64 chars...');
    
    // Stop account-related services first
    await syncCmd(D2, 'am force-stop com.yandex.bank; am force-stop ru.ozon.fintech.finance; am force-stop ru.ozon.app.android', 10);
    
    const pushed = await injectFile(D2, b64, '/data/system_ce/0/accounts_ce.db');
    if (pushed) {
      log('✓ accounts_ce.db pushed');
      
      // Fix ownership and permissions
      await syncCmd(D2, 'chown system:system /data/system_ce/0/accounts_ce.db; chmod 600 /data/system_ce/0/accounts_ce.db', 10);
      
      // Also need accounts_de.db in /data/system_de/0/
      log('Checking accounts_de.db...');
      const d1DeB64 = await syncCmd(D1, 'base64 /data/system_de/0/accounts_de.db 2>/dev/null', 30);
      if (d1DeB64.length > 100) {
        const deFile = path.join(OUT, 'app_data', 'd2_accounts_de.db');
        fs.writeFileSync(deFile, Buffer.from(d1DeB64.replace(/\s/g, ''), 'base64'));
        
        // Modify DE database similarly
        try {
          execSync(`sqlite3 "${deFile}" "DELETE FROM accounts;"`, { timeout: 5000 });
          execSync(`sqlite3 "${deFile}" "INSERT INTO accounts (_id, name, type, previous_name) VALUES (1, 'OZON ID', 'ru.ozon.id.authorized.account', '');"`, { timeout: 5000 });
          execSync(`sqlite3 "${deFile}" "INSERT INTO accounts (_id, name, type, previous_name) VALUES (2, 'Максим Сирож #2042295278 ﹫', 'com.yandex.passport', '');"`, { timeout: 5000 });
        } catch (e) {
          log('DE db modify: ' + (e.message || '').slice(0, 100));
        }

        const deB64 = fs.readFileSync(deFile).toString('base64');
        const dePushed = await injectFile(D2, deB64, '/data/system_de/0/accounts_de.db');
        if (dePushed) {
          await syncCmd(D2, 'chown system:system /data/system_de/0/accounts_de.db; chmod 600 /data/system_de/0/accounts_de.db', 10);
          log('✓ accounts_de.db pushed');
        }
      }
      
      // Restart the system to pick up new accounts
      log('Restarting Android framework on D2...');
      // Kill system_server to force restart
      await syncCmd(D2, 'setprop ctl.restart zygote', 15);
      log('Waiting 15s for restart...');
      await sleep(15000);
      
    } else {
      log('✗ Failed to push accounts_ce.db');
      
      // Alternative: Push via ADB directly
      log('Trying ADB push...');
      try {
        const tmpLocal = '/tmp/d2_accounts_ce.db';
        fs.copyFileSync(d2AccFile, tmpLocal);
        execSync(`adb -s ${D2_SERIAL} push "${tmpLocal}" /sdcard/accounts_ce.db`, { timeout: 30000 });
        await syncCmd(D2, 'cp /sdcard/accounts_ce.db /data/system_ce/0/accounts_ce.db; chown system:system /data/system_ce/0/accounts_ce.db; chmod 600 /data/system_ce/0/accounts_ce.db; rm /sdcard/accounts_ce.db', 15);
        log('✓ accounts_ce.db pushed via ADB');
      } catch (e) {
        log('ADB push failed: ' + (e.message || '').slice(0, 100));
      }
    }
  }

  // ══════════════════════════════════════════════
  // STEP 4: Verify accounts on D2 after restart
  // ══════════════════════════════════════════════
  log('\n=== STEP 4: Verify D2 accounts ===');
  await sleep(5000);
  const d2VerifyAcc = await syncCmd(D2, 'dumpsys account 2>&1 | head -20', 15);
  log(d2VerifyAcc);

  // Check if accounts_ce.db has our entries
  const d2VerifyDb = await syncCmd(D2, 'ls -la /data/system_ce/0/accounts_ce.db; hexdump -C /data/system_ce/0/accounts_ce.db | grep -i "ozon\\|yandex" | head -5', 15);
  log('DB check: ' + d2VerifyDb);

  log('\n═══════════════════════════════════════');
  log('  COMPLETE');
  log('═══════════════════════════════════════');
}

main().catch(e => console.error('FATAL:', e));
