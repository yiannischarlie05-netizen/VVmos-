#!/usr/bin/env node
/**
 * Rebuild D2 after factory reset:
 * 1. Clone identity from .220
 * 2. Install 13 APKs
 * 3. Enable root
 * 4. Push accounts_ce.db + accounts_de.db
 * 5. Restart framework safely (setprop ctl.restart zygote)
 * 6. Verify
 */
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');
const D2_SERIAL = 'localhost:7391';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');

// .220 identity values (extracted previously)
const IDENTITY = {
  'persist.sys.cloud.imeinum': '895410082175508',
  'persist.sys.cloud.imsinum': '250990090080855',
  'persist.sys.cloud.iccidnum': '89701011747214753090',
  'persist.sys.cloud.phonenum': '79286458086',
  'persist.sys.cloud.macaddress': '14:7D:DA:67:40:69',
  'persist.sys.cloud.gps.lat': '45.42',
  'persist.sys.cloud.gps.lon': '36.77',
};
const ANDROID_ID = 'a4141eb091e166bf';

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
    const req = https.request({ hostname: HOST, path: ep, method: 'POST', headers: { ...h, 'content-length': buf.length }, timeout: (t || 120) * 1000 }, res => {
      let r = ''; res.on('data', c => r += c); res.on('end', () => { try { ok(JSON.parse(r)); } catch { ok({ code: -1 }); } });
    });
    req.on('timeout', () => { req.destroy(); ok({ code: -99 }); });
    req.on('error', e => ok({ code: -99, msg: e.message }));
    req.write(buf); req.end();
  });
}

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function waitForOnline(pad, maxSec) {
  const end = Date.now() + (maxSec || 120) * 1000;
  while (Date.now() < end) {
    const r = await syncCmd(pad, 'id', 10);
    if (!r.startsWith('[ERR')) return r;
    await sleep(10000);
  }
  return null;
}

async function main() {
  console.log('═'.repeat(60));
  console.log('  REBUILD D2 — FULL PIPELINE');
  console.log('═'.repeat(60));

  // ══════════════════════════════════════════════
  // PHASE 1: Enable root + verify
  // ══════════════════════════════════════════════
  log('▶ PHASE 1: Enable root');
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  await sleep(3000);
  const rootCheck = await syncCmd(D2, 'id', 10);
  log('Root: ' + rootCheck.split('\n')[0]);

  // ══════════════════════════════════════════════
  // PHASE 2: Clone .220 identity
  // ══════════════════════════════════════════════
  log('\n▶ PHASE 2: Clone .220 identity');
  
  // Set cloud properties via API
  const modemProps = {
    modemPropertiesList: [
      { propertiesName: 'imei', propertiesValue: IDENTITY['persist.sys.cloud.imeinum'] },
      { propertiesName: 'phonenum', propertiesValue: IDENTITY['persist.sys.cloud.phonenum'] },
      { propertiesName: 'IMSI', propertiesValue: IDENTITY['persist.sys.cloud.imsinum'] },
      { propertiesName: 'ICCID', propertiesValue: IDENTITY['persist.sys.cloud.iccidnum'] },
    ],
  };
  const modR = await apiPost('/vcpcloud/api/padApi/updatePadProperties', { padCodes: [D2], ...modemProps });
  log('Modem props update: ' + (modR.code === 200 ? 'OK' : JSON.stringify(modR).slice(0, 100)));

  // Set props via shell
  for (const [key, val] of Object.entries(IDENTITY)) {
    await syncCmd(D2, `setprop ${key} "${val}"`, 5);
  }
  await syncCmd(D2, `settings put secure android_id ${ANDROID_ID}`, 5);
  
  // Set GPS
  const gpsR = await apiPost('/vcpcloud/api/padApi/updatePadProperties', {
    padCodes: [D2],
    locationPropertiesList: [
      { propertiesName: 'longitude', propertiesValue: IDENTITY['persist.sys.cloud.gps.lon'] },
      { propertiesName: 'latitude', propertiesValue: IDENTITY['persist.sys.cloud.gps.lat'] },
    ],
  });
  log('GPS update: ' + (gpsR.code === 200 ? 'OK' : gpsR.msg));

  // Verify identity
  const idCheck = await syncCmd(D2, 'getprop persist.sys.cloud.imeinum; getprop persist.sys.cloud.phonenum; settings get secure android_id', 10);
  log('Identity: ' + idCheck.replace(/\n/g, ' | '));

  // ══════════════════════════════════════════════
  // PHASE 3: Install 13 APKs
  // ══════════════════════════════════════════════
  log('\n▶ PHASE 3: Install APKs');
  
  // Check what's already installed
  const installed = await syncCmd(D2, 'pm list packages -3 2>/dev/null', 15);
  const installedPkgs = new Set((installed || '').split('\n').map(l => l.replace('package:', '').trim()).filter(Boolean));
  log('Currently installed: ' + installedPkgs.size);
  
  // Find APK files from previous extraction
  const apkDir = path.join(OUT, 'apks');
  if (!fs.existsSync(apkDir)) {
    // Try looking in other places
    const altDirs = [
      path.join(OUT, 'ACP250923JS861KJ'),
      OUT,
      '/tmp/apks',
    ];
    for (const d of altDirs) {
      if (fs.existsSync(d)) {
        const files = fs.readdirSync(d).filter(f => f.endsWith('.apk'));
        if (files.length > 0) {
          log('Found APKs in: ' + d);
          break;
        }
      }
    }
  }
  
  // Install APKs via VMOS installApp API (using previously cached URLs)
  // The APKs were originally pulled from .220 - we need to install them again.
  // Check if we have them locally and can push via ADB, or use the installApp API
  
  const missingApps = APPS.filter(p => !installedPkgs.has(p));
  log('Missing apps: ' + missingApps.length + '/' + APPS.length);
  
  if (missingApps.length > 0) {
    // Try ADB push from local extracted APKs
    let apkFiles = [];
    const searchDirs = [OUT, path.join(OUT, 'apks'), '/tmp'];
    for (const dir of searchDirs) {
      if (fs.existsSync(dir)) {
        try {
          const files = fs.readdirSync(dir).filter(f => f.endsWith('.apk'));
          apkFiles = files.map(f => path.join(dir, f));
          if (apkFiles.length > 0) break;
        } catch {}
      }
    }
    
    if (apkFiles.length > 0) {
      log('Found ' + apkFiles.length + ' local APK files, installing via ADB...');
      // Reconnect ADB to D2
      try {
        execSync('adb disconnect localhost:7391 2>/dev/null; sleep 1; adb connect localhost:7391', { timeout: 10000 });
        await sleep(3000);
        
        for (const apk of apkFiles) {
          const pkg = path.basename(apk, '.apk');
          if (installedPkgs.has(pkg)) continue;
          try {
            log('  Installing ' + path.basename(apk) + '...');
            execSync(`adb -s ${D2_SERIAL} install -r "${apk}"`, { timeout: 120000 });
            log('    ✓ ' + path.basename(apk));
          } catch (e) {
            log('    ✗ ' + (e.message || '').slice(0, 80));
          }
        }
      } catch (e) {
        log('ADB install failed: ' + (e.message || '').slice(0, 100));
      }
    } else {
      // No local APKs - need to use installApp API with app store URLs
      // or pull from .220 again. For now, try D1 relay approach.
      log('No local APK files found. Will try to install from D1 relay...');
      
      // List APKs on D1 that came from .220
      const d1Apks = await syncCmd('ACP250923JS861KJ', 'ls /sdcard/Download/*.apk 2>/dev/null; ls /data/local/tmp/*.apk 2>/dev/null', 10);
      log('D1 APKs: ' + d1Apks);
    }
  }

  // Verify installed apps
  const finalInstalled = await syncCmd(D2, 'pm list packages -3 2>/dev/null | wc -l', 10);
  log('Total 3rd party apps: ' + finalInstalled);

  // ══════════════════════════════════════════════
  // PHASE 4: Push accounts DBs
  // ══════════════════════════════════════════════
  log('\n▶ PHASE 4: Push accounts DBs');
  
  const ceDb = path.join(OUT, 'app_data', 'fresh_accounts_ce.db');
  const deDb = path.join(OUT, 'app_data', 'fresh_accounts_de.db');
  
  if (fs.existsSync(ceDb) && fs.existsSync(deDb)) {
    // Reconnect ADB
    try { execSync('adb connect localhost:7391 2>/dev/null', { timeout: 10000 }); } catch {}
    await sleep(2000);
    
    // Push via ADB to /sdcard
    try {
      execSync(`adb -s ${D2_SERIAL} push "${ceDb}" /sdcard/fresh_accounts_ce.db`, { timeout: 30000 });
      execSync(`adb -s ${D2_SERIAL} push "${deDb}" /sdcard/fresh_accounts_de.db`, { timeout: 30000 });
      log('Pushed DBs to /sdcard');
    } catch (e) {
      log('ADB push failed: ' + (e.message || '').slice(0, 100));
      // Fallback: use base64 via syncCmd
      log('Using base64 fallback...');
      const ceB64 = fs.readFileSync(ceDb).toString('base64');
      const chunks = [];
      for (let i = 0; i < ceB64.length; i += 3000) chunks.push(ceB64.slice(i, i + 3000));
      
      let ok = true;
      await syncCmd(D2, `printf '%s' '${chunks[0]}' > /sdcard/ce.b64`, 10);
      for (let i = 1; i < chunks.length; i++) {
        const r = await syncCmd(D2, `printf '%s' '${chunks[i]}' >> /sdcard/ce.b64`, 10);
        if (r.startsWith('[ERR')) { ok = false; break; }
      }
      if (ok) {
        await syncCmd(D2, 'base64 -d /sdcard/ce.b64 > /sdcard/fresh_accounts_ce.db && rm /sdcard/ce.b64', 15);
      }
      
      // Same for DE
      const deB64 = fs.readFileSync(deDb).toString('base64');
      await syncCmd(D2, `printf '%s' '${deB64}' | base64 -d > /sdcard/fresh_accounts_de.db`, 15);
      log('Pushed via base64');
    }
    
    // Install DBs with root
    const installCe = await syncCmd(D2, 'cp /sdcard/fresh_accounts_ce.db /data/system_ce/0/accounts_ce.db && chown system:system /data/system_ce/0/accounts_ce.db && chmod 600 /data/system_ce/0/accounts_ce.db && echo OK', 15);
    log('CE db install: ' + installCe);
    
    const installDe = await syncCmd(D2, 'cp /sdcard/fresh_accounts_de.db /data/system_de/0/accounts_de.db && chown system:system /data/system_de/0/accounts_de.db && chmod 600 /data/system_de/0/accounts_de.db && echo OK', 15);
    log('DE db install: ' + installDe);
    
    // Cleanup
    await syncCmd(D2, 'rm -f /sdcard/fresh_accounts_*.db', 5);
  } else {
    log('ERROR: accounts DB files not found at ' + ceDb);
  }

  // ══════════════════════════════════════════════
  // PHASE 5: Restart framework SAFELY
  // ══════════════════════════════════════════════
  log('\n▶ PHASE 5: Restart framework (safe method)');
  // Use API restart instead of shell stop/start to avoid bricking
  const restartR = await apiPost('/vcpcloud/api/padApi/restart', { padCodes: [D2] });
  log('API restart: ' + (restartR.code === 200 ? 'OK' : JSON.stringify(restartR).slice(0, 200)));
  
  log('Waiting for D2 to come back online...');
  const online = await waitForOnline(D2, 180);
  if (!online) {
    log('ERROR: D2 did not come back online after restart');
    return;
  }
  log('D2 online: ' + online);

  // Re-enable root
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  await sleep(3000);

  // ══════════════════════════════════════════════
  // PHASE 6: Verify everything
  // ══════════════════════════════════════════════
  log('\n▶ PHASE 6: Verification');
  
  const verify = await syncCmd(D2, [
    'echo "=== ROOT ==="', 'id',
    'echo "=== IDENTITY ==="',
    'getprop persist.sys.cloud.imeinum',
    'getprop persist.sys.cloud.phonenum',
    'getprop persist.sys.cloud.imsinum',
    'settings get secure android_id',
    'echo "=== ACCOUNTS ==="',
    'dumpsys account 2>&1 | head -15',
    'echo "=== APPS ==="',
    'pm list packages -3 2>/dev/null | wc -l',
    'echo "=== DB CHECK ==="',
    'ls -la /data/system_ce/0/accounts_ce.db /data/system_de/0/accounts_de.db 2>/dev/null',
    'strings /data/system_ce/0/accounts_ce.db 2>/dev/null | grep -iE "ozon|yandex" | head -3',
  ].join('; '), 30);
  log(verify);

  log('\n═══════════════════════════════════════');
  log('  REBUILD COMPLETE');
  log('═══════════════════════════════════════');
}

main().catch(e => console.error('FATAL:', e));
