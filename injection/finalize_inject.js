#!/usr/bin/env node
/**
 * Finalize account injection: move DBs from /sdcard to system paths,
 * fix permissions, restart framework, verify.
 */
const https = require('https');
const crypto = require('crypto');

const { AK, SK, HOST, D2, CT, SHD } = require('../shared/vmos_api');

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

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('═'.repeat(60));
  console.log('  FINALIZE ACCOUNT INJECTION INTO D2');
  console.log('═'.repeat(60));

  // Ensure root
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  await sleep(2000);

  const rootCheck = await syncCmd(D2, 'id', 10);
  log('Root: ' + rootCheck.split('\n')[0]);

  // Step 1: Backup existing DBs
  log('\n=== Step 1: Backup existing accounts DBs ===');
  await syncCmd(D2, 'cp /data/system_ce/0/accounts_ce.db /data/system_ce/0/accounts_ce.db.bak 2>/dev/null; cp /data/system_de/0/accounts_de.db /data/system_de/0/accounts_de.db.bak 2>/dev/null', 10);
  log('Backed up existing DBs');

  // Step 2: Check pushed files on /sdcard
  log('\n=== Step 2: Verify pushed files ===');
  const lsSdcard = await syncCmd(D2, 'ls -la /sdcard/fresh_accounts_*.db', 10);
  log(lsSdcard);

  // Step 3: Move fresh DBs into place
  log('\n=== Step 3: Install accounts DBs ===');

  // Copy CE db
  const cpCe = await syncCmd(D2, 'cp /sdcard/fresh_accounts_ce.db /data/system_ce/0/accounts_ce.db && chown system:system /data/system_ce/0/accounts_ce.db && chmod 600 /data/system_ce/0/accounts_ce.db && echo OK', 15);
  log('CE db: ' + cpCe);

  // Copy DE db
  const cpDe = await syncCmd(D2, 'cp /sdcard/fresh_accounts_de.db /data/system_de/0/accounts_de.db && chown system:system /data/system_de/0/accounts_de.db && chmod 600 /data/system_de/0/accounts_de.db && echo OK', 15);
  log('DE db: ' + cpDe);

  // Verify file integrity
  const verifyDb = await syncCmd(D2, 'ls -la /data/system_ce/0/accounts_ce.db /data/system_de/0/accounts_de.db; echo ---; md5sum /data/system_ce/0/accounts_ce.db /sdcard/fresh_accounts_ce.db', 10);
  log('Files: ' + verifyDb);

  // Step 4: Clean up /sdcard
  await syncCmd(D2, 'rm -f /sdcard/fresh_accounts_*.db /sdcard/backup_test.ab', 5);

  // Step 5: Restart framework to load new accounts
  log('\n=== Step 4: Restart Android framework ===');
  // Use stop/start instead of zygote restart for cleaner reboot
  await syncCmd(D2, 'stop; sleep 2; start', 30);
  log('Framework restarting, waiting 20s...');
  await sleep(20000);

  // Step 6: Verify accounts
  log('\n=== Step 5: Verify accounts on D2 ===');

  // Re-enable root after restart
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  await sleep(3000);

  const accVerify = await syncCmd(D2, 'dumpsys account 2>&1 | head -25', 15);
  log(accVerify);

  // Check DB contents
  const dbContents = await syncCmd(D2, 'strings /data/system_ce/0/accounts_ce.db | grep -E "OZON|yandex|passport" | head -5', 10);
  log('DB strings: ' + dbContents);

  // Step 7: Check identity is intact
  log('\n=== Step 6: Identity check ===');
  const identity = await syncCmd(D2, [
    'getprop persist.sys.cloud.imeinum',
    'getprop persist.sys.cloud.phonenum',
    'settings get secure android_id',
    'pm list packages -3 | wc -l',
  ].join('; echo ---; '), 15);
  log(identity);

  log('\n═══════════════════════════════════════');
  log('  COMPLETE');
  log('═══════════════════════════════════════');
}

main().catch(e => console.error('FATAL:', e));
