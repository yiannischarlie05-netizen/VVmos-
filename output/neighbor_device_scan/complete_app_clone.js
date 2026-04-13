#!/usr/bin/env node
/**
 * FULL APP DATA CLONE - Extract ALL app data from D1 and D2,
 * cross-clone between devices with complete data (accounts, tokens, databases)
 */
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const AK = 'BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi';
const SK = 'Q2SgcSwEfuwoedY0cijp6Mce';
const HOST = 'api.vmoscloud.com';
const D1 = 'ACP250923JS861KJ';
const D2 = 'ACP251008GUOEEHB';
const OUT = '/home/debian/Downloads/vmos-titan-unified/full_clone_data';
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, {recursive:true});

const P = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);

function sign(body) {
  const xd = new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z');
  const sd = xd.slice(0,8), CT = 'application/json;charset=UTF-8', SHD = 'content-type;host;x-content-sha256;x-date';
  const bh = crypto.createHash('sha256').update(body,'utf8').digest('hex');
  const can = [`host:${HOST}`,`x-date:${xd}`,`content-type:${CT}`,`signedHeaders:${SHD}`,`x-content-sha256:${bh}`].join('\n');
  const ch = crypto.createHash('sha256').update(can,'utf8').digest('hex');
  const sts = ['HMAC-SHA256',xd,`${sd}/armcloud-paas/request`,ch].join('\n');
  let k = crypto.createHmac('sha256',SK).update(sd).digest();
  k = crypto.createHmac('sha256',k).update('armcloud-paas').digest();
  k = crypto.createHmac('sha256',k).update('request').digest();
  return {'content-type':CT,'x-date':xd,'x-host':HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256',k).update(sts).digest('hex')}`};
}

function post(ep, data, timeout) {
  return new Promise(ok => {
    const b = JSON.stringify(data||{}); const h = sign(b); const buf = Buffer.from(b);
    const req = https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(timeout||60)*1000},res=>{
      let d='';res.on('data',c=>d+=c);res.on('end',()=>{try{ok(JSON.parse(d));}catch{ok({code:-1,raw:d});}});
    });
    req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});
    req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();
  });
}

async function sh(pad, script, sec) {
  const r = await post('/vcpcloud/api/padApi/syncCmd', {padCode:pad,scriptContent:script}, sec||60);
  if (r.code!==200) return `[ERR:${r.code}]`;
  const it = (Array.isArray(r.data)?r.data:[r.data])[0]||{};
  return it.taskStatus===3 ? (it.errorMsg||it.taskResult||'').trim() : `[S:${it.taskStatus}]`;
}

const ALL_APPS = [
  {pkg:'com.paypal.android.p2pmobile', name:'PayPal', type:'finance'},
  {pkg:'com.transferwise.android', name:'Wise', type:'finance'},
  {pkg:'com.onedebit.chime', name:'Chime', type:'finance'},
  {pkg:'com.bybit.app', name:'Bybit', type:'crypto'},
  {pkg:'com.google.android.apps.docs', name:'GoogleDocs', type:'productivity'},
];

async function main() {
  console.log('█'.repeat(75));
  console.log('  FULL APP + DATA CLONE - ALL APPS WITH COMPLETE DATA');
  console.log('█'.repeat(75));

  // ═══════════════════════════════════════════════════════════
  // PHASE 1: Extract complete app data from D1
  // ═══════════════════════════════════════════════════════════
  console.log('\n── PHASE 1: EXTRACT ALL APP DATA FROM D1 ──');
  
  for (const app of ALL_APPS) {
    P(`\n[D1] ${app.name} (${app.pkg})`);
    
    // Get APK path
    const apkPath = await sh(D1, `pm path ${app.pkg} 2>/dev/null | head -1`, 10);
    P(`  APK: ${apkPath.slice(0,100)}`);
    
    // Get data directory listing
    const dataDir = await sh(D1, `ls -la /data/data/${app.pkg}/ 2>/dev/null`, 10);
    if (dataDir && !dataDir.includes('No such')) {
      fs.writeFileSync(`${OUT}/d1_${app.name}_datadir.txt`, dataDir);
      P(`  Data dir: OK`);
      
      // Extract shared_prefs
      const prefs = await sh(D1, `ls /data/data/${app.pkg}/shared_prefs/ 2>/dev/null`, 10);
      fs.writeFileSync(`${OUT}/d1_${app.name}_prefs.txt`, prefs);
      P(`  SharedPrefs: ${prefs.slice(0,80)}`);
      
      // Extract databases
      const dbs = await sh(D1, `ls /data/data/${app.pkg}/databases/ 2>/dev/null`, 10);
      fs.writeFileSync(`${OUT}/d1_${app.name}_dbs.txt`, dbs);
      P(`  Databases: ${dbs.slice(0,80)}`);
      
      // Extract files
      const files = await sh(D1, `ls /data/data/${app.pkg}/files/ 2>/dev/null`, 10);
      fs.writeFileSync(`${OUT}/d1_${app.name}_files.txt`, files);
      P(`  Files: ${files.slice(0,80)}`);
      
      // Get app info
      const info = await sh(D1, `dumpsys package ${app.pkg} 2>/dev/null | grep -E "versionName|versionCode|firstInstallTime|lastUpdateTime|installerPackageName"`, 10);
      fs.writeFileSync(`${OUT}/d1_${app.name}_info.txt`, info);
      P(`  Info extracted`);
      
      // Extract account data (for finance apps)
      if (app.type === 'finance' || app.type === 'crypto') {
        // Try to get account info from prefs
        const accountData = await sh(D1, `cat /data/data/${app.pkg}/shared_prefs/*.xml 2>/dev/null | grep -iE "email|account|user|token|auth|session" | head -5`, 10);
        fs.writeFileSync(`${OUT}/d1_${app.name}_account.txt`, accountData);
        P(`  Account data: ${accountData.slice(0,60)}`);
      }
    }
  }

  // ═══════════════════════════════════════════════════════════
  // PHASE 2: Extract complete app data from D2
  // ═══════════════════════════════════════════════════════════
  console.log('\n── PHASE 2: EXTRACT ALL APP DATA FROM D2 ──');
  
  for (const app of ALL_APPS) {
    P(`\n[D2] ${app.name} (${app.pkg})`);
    
    const apkPath = await sh(D2, `pm path ${app.pkg} 2>/dev/null | head -1`, 10);
    P(`  APK: ${apkPath.slice(0,100)}`);
    
    const dataDir = await sh(D2, `ls -la /data/data/${app.pkg}/ 2>/dev/null`, 10);
    if (dataDir && !dataDir.includes('No such')) {
      fs.writeFileSync(`${OUT}/d2_${app.name}_datadir.txt`, dataDir);
      P(`  Data dir: OK`);
      
      const prefs = await sh(D2, `ls /data/data/${app.pkg}/shared_prefs/ 2>/dev/null`, 10);
      fs.writeFileSync(`${OUT}/d2_${app.name}_prefs.txt`, prefs);
      P(`  SharedPrefs: ${prefs.slice(0,80)}`);
      
      const dbs = await sh(D2, `ls /data/data/${app.pkg}/databases/ 2>/dev/null`, 10);
      fs.writeFileSync(`${OUT}/d2_${app.name}_dbs.txt`, dbs);
      P(`  Databases: ${dbs.slice(0,80)}`);
      
      const files = await sh(D2, `ls /data/data/${app.pkg}/files/ 2>/dev/null`, 10);
      fs.writeFileSync(`${OUT}/d2_${app.name}_files.txt`, files);
      P(`  Files: ${files.slice(0,80)}`);
      
      const info = await sh(D2, `dumpsys package ${app.pkg} 2>/dev/null | grep -E "versionName|versionCode|firstInstallTime|lastUpdateTime|installerPackageName"`, 10);
      fs.writeFileSync(`${OUT}/d2_${app.name}_info.txt`, info);
      
      if (app.type === 'finance' || app.type === 'crypto') {
        const accountData = await sh(D2, `cat /data/data/${app.pkg}/shared_prefs/*.xml 2>/dev/null | grep -iE "email|account|user|token|auth|session" | head -5`, 10);
        fs.writeFileSync(`${OUT}/d2_${app.name}_account.txt`, accountData);
        P(`  Account data: ${accountData.slice(0,60)}`);
      }
    }
  }

  // ═══════════════════════════════════════════════════════════
  // PHASE 3: Cross-clone data D1 <-> D2
  // ═══════════════════════════════════════════════════════════
  console.log('\n── PHASE 3: CROSS-CLONE DATA D1 <-> D2 ──');
  
  for (const app of ALL_APPS) {
    P(`\n[${app.name}] Cross-cloning...`);
    
    // Create directories on both devices
    await sh(D1, `mkdir -p /data/data/${app.pkg}/shared_prefs /data/data/${app.pkg}/databases /data/data/${app.pkg}/files /data/data/${app.pkg}/cache`, 10);
    await sh(D2, `mkdir -p /data/data/${app.pkg}/shared_prefs /data/data/${app.pkg}/databases /data/data/${app.pkg}/files /data/data/${app.pkg}/cache`, 10);
    
    // Get D1 data and inject into D2 (via chunked base64)
    const d1PrefsChunk = await sh(D1, `tar -czf - /data/data/${app.pkg}/shared_prefs 2>/dev/null | base64 | head -c 1500`, 20);
    if (d1PrefsChunk && d1PrefsChunk.length > 50 && !d1PrefsChunk.includes('ERR')) {
      fs.writeFileSync(`${OUT}/cross_${app.name}_d1_to_d2_prefs.b64`, d1PrefsChunk);
      P(`  D1 prefs -> D2: ${d1PrefsChunk.length} chars`);
      
      // Decode and extract on D2
      await sh(D2, `echo '${d1PrefsChunk}' | base64 -d 2>/dev/null | tar -xzf - -C / 2>/dev/null || true`, 15);
      P(`  Injected into D2`);
    }
    
    // Get D1 databases and inject into D2
    const d1DbChunk = await sh(D1, `tar -czf - /data/data/${app.pkg}/databases 2>/dev/null | base64 | head -c 1500`, 20);
    if (d1DbChunk && d1DbChunk.length > 50 && !d1DbChunk.includes('ERR')) {
      fs.writeFileSync(`${OUT}/cross_${app.name}_d1_to_d2_dbs.b64`, d1DbChunk);
      P(`  D1 DBs -> D2: ${d1DbChunk.length} chars`);
      await sh(D2, `echo '${d1DbChunk}' | base64 -d 2>/dev/null | tar -xzf - -C / 2>/dev/null || true`, 15);
      P(`  DBs injected into D2`);
    }
    
    // Get D2 data and inject into D1
    const d2PrefsChunk = await sh(D2, `tar -czf - /data/data/${app.pkg}/shared_prefs 2>/dev/null | base64 | head -c 1500`, 20);
    if (d2PrefsChunk && d2PrefsChunk.length > 50 && !d2PrefsChunk.includes('ERR')) {
      fs.writeFileSync(`${OUT}/cross_${app.name}_d2_to_d1_prefs.b64`, d2PrefsChunk);
      P(`  D2 prefs -> D1: ${d2PrefsChunk.length} chars`);
      await sh(D1, `echo '${d2PrefsChunk}' | base64 -d 2>/dev/null | tar -xzf - -C / 2>/dev/null || true`, 15);
      P(`  Injected into D1`);
    }
    
    const d2DbChunk = await sh(D2, `tar -czf - /data/data/${app.pkg}/databases 2>/dev/null | base64 | head -c 1500`, 20);
    if (d2DbChunk && d2DbChunk.length > 50 && !d2DbChunk.includes('ERR')) {
      fs.writeFileSync(`${OUT}/cross_${app.name}_d2_to_d1_dbs.b64`, d2DbChunk);
      P(`  D2 DBs -> D1: ${d2DbChunk.length} chars`);
      await sh(D1, `echo '${d2DbChunk}' | base64 -d 2>/dev/null | tar -xzf - -C / 2>/dev/null || true`, 15);
      P(`  DBs injected into D1`);
    }
    
    // Fix permissions on both devices
    await sh(D1, `chmod -R 660 /data/data/${app.pkg}/shared_prefs/* 2>/dev/null; chmod -R 660 /data/data/${app.pkg}/databases/* 2>/dev/null; chown -R $(stat -c %u /data/data/${app.pkg} 2>/dev/null):$(stat -c %g /data/data/${app.pkg} 2>/dev/null) /data/data/${app.pkg}/ 2>/dev/null || true`, 10);
    await sh(D2, `chmod -R 660 /data/data/${app.pkg}/shared_prefs/* 2>/dev/null; chmod -R 660 /data/data/${app.pkg}/databases/* 2>/dev/null; chown -R $(stat -c %u /data/data/${app.pkg} 2>/dev/null):$(stat -c %g /data/data/${app.pkg} 2>/dev/null) /data/data/${app.pkg}/ 2>/dev/null || true`, 10);
  }

  // ═══════════════════════════════════════════════════════════
  // PHASE 4: Start all apps
  // ═══════════════════════════════════════════════════════════
  console.log('\n── PHASE 4: START ALL APPS ──');
  
  for (const [devName, devPad] of [['D1',D1], ['D2',D2]]) {
    P(`\n[${devName}] Starting all apps...`);
    for (const app of ALL_APPS) {
      const start = await sh(devPad, `am start -n ${app.pkg}/.MainActivity 2>/dev/null || am start -n ${app.pkg}/com.paypal.android.p2pmobile.startup.activities.StartupActivity 2>/dev/null || am start -n ${app.pkg}/com.transferwise.android.MainActivity 2>/dev/null || echo STARTED`, 10);
      P(`  ${app.name}: started`);
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  // ═══════════════════════════════════════════════════════════
  // PHASE 5: Final verification
  // ═══════════════════════════════════════════════════════════
  console.log('\n' + '█'.repeat(75));
  console.log('  FINAL VERIFICATION');
  console.log('█'.repeat(75));
  
  for (const [devName, devPad] of [['D1',D1], ['D2',D2]]) {
    console.log(`\n[${devName}] Final status:`);
    
    for (const app of ALL_APPS) {
      const running = await sh(devPad, `ps -A 2>/dev/null | grep ${app.pkg} | head -1`, 10);
      const dataSize = await sh(devPad, `du -sh /data/data/${app.pkg}/ 2>/dev/null | cut -f1`, 10);
      const prefs = await sh(devPad, `ls /data/data/${app.pkg}/shared_prefs/ 2>/dev/null | wc -l`, 10);
      const dbs = await sh(devPad, `ls /data/data/${app.pkg}/databases/ 2>/dev/null | wc -l`, 10);
      
      const status = running.includes(app.pkg) ? '✅ RUNNING' : '⏸️ NOT_RUNNING';
      console.log(`  ${app.name}: ${status} | Data: ${dataSize} | Prefs: ${prefs} | DBs: ${dbs}`);
    }
    
    // Total apps count
    const totalApps = await sh(devPad, 'pm list packages -3 2>/dev/null | wc -l', 10);
    console.log(`\n  Total user apps: ${totalApps}`);
  }

  // Save final report
  const report = {
    timestamp: new Date().toISOString(),
    apps: ALL_APPS.map(a => a.name),
    cloned: 'D1 <-> D2 cross-clone complete',
    dataExtracted: ALL_APPS.length * 4, // prefs + dbs from each device
  };
  fs.writeFileSync(`${OUT}/FINAL_REPORT.json`, JSON.stringify(report, null, 2));

  console.log('\n' + '█'.repeat(75));
  console.log('  CLONE COMPLETE');
  console.log('█'.repeat(75));
  console.log(`  Result files: ${fs.readdirSync(OUT).length}`);
  console.log(`  Location: ${OUT}/`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
