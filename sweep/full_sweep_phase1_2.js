#!/usr/bin/env node
/**
 * FULL SWEEP — Phase 1: Direct ADB + Phase 2: API Endpoint Sweep
 * ==============================================================
 * Tests ALL 60+ API endpoints and gets direct ADB host:port
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const { execSync } = require('child_process');

const { AK, SK, HOST, SVC, D1, D2, CT, SHD, sh, P } = require('../shared/vmos_api');
const OUT = path.join(__dirname, '..', 'output', 'full_sweep_results');

if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });
const save = (f, d) => fs.writeFileSync(`${OUT}/${f}`, typeof d === 'string' ? d : JSON.stringify(d, null, 2));
const R = {};

function sign(body) {
  const xd = new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z');
  const sd = xd.slice(0,8);
  const bh = crypto.createHash('sha256').update(body,'utf8').digest('hex');
  const can = [`host:${HOST}`,`x-date:${xd}`,`content-type:${CT}`,`signedHeaders:${SHD}`,`x-content-sha256:${bh}`].join('\n');
  const ch = crypto.createHash('sha256').update(can,'utf8').digest('hex');
  const sts = ['HMAC-SHA256',xd,`${sd}/${SVC}/request`,ch].join('\n');
  let k = crypto.createHmac('sha256',SK).update(sd).digest();
  k = crypto.createHmac('sha256',k).update(SVC).digest();
  k = crypto.createHmac('sha256',k).update('request').digest();
  return {'content-type':CT,'x-date':xd,'x-host':HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${crypto.createHmac('sha256',k).update(sts).digest('hex')}`};
}

function post(ep, data, timeout) {
  return new Promise(ok => {
    const b = JSON.stringify(data||{}); const h = sign(b); const buf = Buffer.from(b);
    const req = https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(timeout||30)*1000},res=>{
      let d='';res.on('data',c=>d+=c);res.on('end',()=>{try{ok(JSON.parse(d));}catch{ok({code:-1,raw:d.slice(0,2000)});}});
    });
    req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});
    req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();
  });
}

function get(ep, params, timeout) {
  return new Promise(ok => {
    const qs = params ? '?' + Object.entries(params).map(([k,v])=>`${k}=${encodeURIComponent(v)}`).join('&') : '';
    const b = JSON.stringify(params||{}); const h = sign(b);
    const req = https.request({hostname:HOST,path:ep+qs,method:'GET',headers:h,timeout:(timeout||30)*1000},res=>{
      let d='';res.on('data',c=>d+=c);res.on('end',()=>{try{ok(JSON.parse(d));}catch{ok({code:-1,raw:d.slice(0,2000)});}});
    });
    req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});
    req.on('error',e=>ok({code:-99,msg:e.message}));req.end();
  });
}

// ══════════════════════════════════════════════════════════════════
// PHASE 1: DIRECT ADB CONNECTION
// ══════════════════════════════════════════════════════════════════
async function phase1() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 1: DIRECT ADB CONNECTION');
  console.log('█'.repeat(75));

  // 1a: Enable root first
  P('[1a] Enable root on both devices...');
  const rootGlobal = await post('/vcpcloud/api/padApi/switchRoot', {padCodes:[D1,D2],rootStatus:1,rootType:0});
  P(`  Root global: ${rootGlobal.code}`);
  const rootShell = await post('/vcpcloud/api/padApi/switchRoot', {padCodes:[D1,D2],rootStatus:1,rootType:1,packageName:'com.android.shell'});
  P(`  Root shell: ${rootShell.code}`);

  // 1b: Enable ADB via openOnlineAdb
  P('[1b] Enable ADB via openOnlineAdb...');
  const adbEnable = await post('/vcpcloud/api/padApi/openOnlineAdb', {padCodes:[D1,D2],open:1});
  save('adb_enable.json', adbEnable);
  R.adb_enable = adbEnable;
  P(`  ADB enable: code=${adbEnable.code} msg=${adbEnable.msg||''}`);

  // 1c: Get ADB connection info for D1
  P('[1c] Get ADB info for D1...');
  const adbD1 = await post('/vcpcloud/api/padApi/adb', {padCode:D1,enable:1});
  save('adb_d1.json', adbD1);
  R.adb_d1 = adbD1;
  P(`  D1 ADB: code=${adbD1.code} data=${JSON.stringify(adbD1.data||{}).slice(0,200)}`);

  // 1d: Get ADB connection info for D2
  P('[1d] Get ADB info for D2...');
  const adbD2 = await post('/vcpcloud/api/padApi/adb', {padCode:D2,enable:1});
  save('adb_d2.json', adbD2);
  R.adb_d2 = adbD2;
  P(`  D2 ADB: code=${adbD2.code} data=${JSON.stringify(adbD2.data||{}).slice(0,200)}`);

  // 1e: Batch ADB info
  P('[1e] Batch ADB info...');
  const batchAdb = await post('/vcpcloud/api/padApi/batchAdb', {padCodes:[D1,D2]});
  save('adb_batch.json', batchAdb);
  R.adb_batch = batchAdb;
  P(`  Batch: code=${batchAdb.code} data=${JSON.stringify(batchAdb.data||{}).slice(0,300)}`);

  // 1f: Try to connect ADB from local machine
  if (adbD1.code === 200 && adbD1.data) {
    const h = adbD1.data.host || adbD1.data.ip;
    const p = adbD1.data.port;
    if (h && p) {
      P(`[1f] ADB target D1: ${h}:${p}`);
      R.adb_d1_target = `${h}:${p}`;
      try {
        const r = execSync(`adb connect ${h}:${p} 2>&1`, {timeout:15000}).toString().trim();
        P(`  Connect: ${r}`);
        R.adb_d1_connect = r;
        // Test shell
        try {
          const s = execSync(`adb -s ${h}:${p} shell "id; getprop ro.product.model" 2>&1`, {timeout:10000}).toString().trim();
          P(`  Shell: ${s.slice(0,100)}`);
          R.adb_d1_shell = s;
        } catch(e) { P(`  Shell err: ${e.message.slice(0,80)}`); }
      } catch(e) { P(`  Connect err: ${e.message.slice(0,80)}`); }
    }
  }

  if (adbD2.code === 200 && adbD2.data) {
    const h = adbD2.data.host || adbD2.data.ip;
    const p = adbD2.data.port;
    if (h && p) {
      P(`[1f] ADB target D2: ${h}:${p}`);
      R.adb_d2_target = `${h}:${p}`;
      try {
        const r = execSync(`adb connect ${h}:${p} 2>&1`, {timeout:15000}).toString().trim();
        P(`  Connect: ${r}`);
        R.adb_d2_connect = r;
      } catch(e) { P(`  Connect err: ${e.message.slice(0,80)}`); }
    }
  }

  // 1g: Also check internal ADB port 5555 via syncCmd
  P('[1g] Check ADB port 5555 internal...');
  const adb5555 = await sh(D1, [
    'getprop service.adb.tcp.port',
    'getprop persist.adb.tcp.port',
    'ss -tlnp | grep 5555',
    'echo "==="',
    'setprop service.adb.tcp.port 5555 2>/dev/null; echo "SET"',
    'stop adbd 2>/dev/null; start adbd 2>/dev/null; echo "RESTARTED"',
    'ss -tlnp | grep 5555',
  ].join('; '), 15);
  save('adb_5555.txt', adb5555);
  R.adb_5555 = adb5555;
  P(`  ADB 5555: ${adb5555.slice(0,150)}`);

  // 1h: Get SDK token for direct access
  P('[1h] SDK tokens...');
  const tokenD1 = await post('/vcpcloud/api/padApi/stsTokenByPadCode', {padCode:D1});
  save('sdk_token_d1.json', tokenD1);
  R.sdk_token_d1 = tokenD1;
  P(`  D1 token: code=${tokenD1.code} data=${JSON.stringify(tokenD1.data||{}).slice(0,200)}`);
  
  const tokenD2 = await post('/vcpcloud/api/padApi/stsTokenByPadCode', {padCode:D2});
  save('sdk_token_d2.json', tokenD2);
  R.sdk_token_d2 = tokenD2;
  P(`  D2 token: code=${tokenD2.code}`);
}

// ══════════════════════════════════════════════════════════════════
// PHASE 2: FULL API ENDPOINT SWEEP
// ══════════════════════════════════════════════════════════════════
async function phase2() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 2: FULL API ENDPOINT SWEEP (60+ endpoints)');
  console.log('█'.repeat(75));

  const results = {};

  // Helper
  async function test(name, fn) {
    try {
      const r = await fn();
      results[name] = {code:r.code,hasData:!!r.data,dataLen:JSON.stringify(r.data||'').length,msg:r.msg};
      const status = r.code===200 ? '✓' : `✗(${r.code})`;
      P(`  ${status} ${name}: ${JSON.stringify(r.data||r.msg||'').slice(0,120)}`);
      if (r.code===200 && r.data) save(`api_${name}.json`, r);
      return r;
    } catch(e) {
      results[name] = {error:e.message};
      P(`  ✗ ${name}: ${e.message.slice(0,80)}`);
      return {code:-1};
    }
  }

  // ── INSTANCE MANAGEMENT ──
  P('\n── Instance Management ──');
  await test('padProperties_d1', ()=> post('/vcpcloud/api/padApi/padProperties',{padCode:D1}));
  await test('batchPadProperties', ()=> post('/vcpcloud/api/padApi/batchPadProperties',{padCodes:[D1,D2]}));
  await test('padInfo_d1', ()=> post('/vcpcloud/api/padApi/padInfo',{padCode:D1}));
  await test('detail_d1', ()=> post('/vcpcloud/api/padApi/detail',{padCode:D1},15));
  await test('padDetails', ()=> post('/vcpcloud/api/padApi/padDetails',{padCodes:[D1]}));
  await test('screenshot', ()=> post('/vcpcloud/api/padApi/screenshot',{padCodes:[D1]}));
  await test('getLongGenerateUrl', ()=> post('/vcpcloud/api/padApi/getLongGenerateUrl',{padCodes:[D1]}));
  await test('getListInstalledApp', ()=> post('/vcpcloud/api/padApi/getListInstalledApp',{padCodes:[D1]}));
  await test('listInstalledApp', ()=> post('/vcpcloud/api/padApi/listInstalledApp',{padCode:D1}));
  await test('proxyInfo', ()=> post('/vcpcloud/api/padApi/proxyInfo',{padCodes:[D1]}));
  await test('checkIP', ()=> post('/vcpcloud/api/padApi/checkIP',{ip:'8.8.8.8'}));

  // ── RESOURCE MANAGEMENT ──
  P('\n── Resource Management ──');
  await test('infos', ()=> post('/vcpcloud/api/padApi/infos',{page:1,rows:50}));
  await test('list', ()=> post('/vcpcloud/api/padApi/list',{pageNo:1,pageSize:50}));

  // ── CLOUD PHONE MANAGEMENT ──
  P('\n── Cloud Phone Management ──');
  await test('userPadList', ()=> post('/vcpcloud/api/padApi/userPadList',{page:1,rows:50}));
  const imgResult = await test('imageVersionList', ()=> post('/vcpcloud/api/padApi/imageVersionList',{}));
  await test('getCloudGoodList', ()=> get('/vcpcloud/api/padApi/getCloudGoodList'));
  await test('templateList', ()=> post('/vcpcloud/api/padApi/templateList',{page:1,rows:50}));

  // ── BRAND/MODEL DATABASE ──
  P('\n── Brand/Model Database ──');
  const brandResult = await test('selectBrandList', ()=> post('/vcpcloud/api/vcBrand/selectBrandList',{}));
  await test('modelInfo', ()=> post('/vcpcloud/api/padApi/modelInfo',{modelNames:['SM-S928U','SM-S9280','Pixel 9 Pro']}));

  // ── BACKUP/RESTORE ──
  P('\n── Backup/Restore ──');
  await test('localPodBackupSelectPage', ()=> post('/vcpcloud/api/padApi/localPodBackupSelectPage',{page:1,rows:50}));
  await test('vcTimingBackupList', ()=> get('/vcpcloud/api/padApi/vcTimingBackupList'));

  // ── STORAGE ──
  P('\n── Storage ──');
  await test('getVcStorageGoods', ()=> get('/vcpcloud/api/padApi/getVcStorageGoods'));
  await test('getRenewStorageInfo', ()=> get('/vcpcloud/api/padApi/getRenewStorageInfo'));
  await test('selectAutoRenew', ()=> get('/vcpcloud/api/padApi/selectAutoRenew'));

  // ── EMAIL SERVICE ──
  P('\n── Email Service ──');
  await test('getEmailServiceList', ()=> get('/vcpcloud/api/padApi/getEmailServiceList'));
  await test('getEmailTypeList', ()=> get('/vcpcloud/api/padApi/getEmailTypeList'));

  // ── PROXY SERVICE ──
  P('\n── Proxy Service ──');
  await test('getDynamicGoodService', ()=> get('/vcpcloud/api/padApi/getDynamicGoodService'));
  await test('getDynamicProxyRegion', ()=> get('/vcpcloud/api/padApi/getDynamicProxyRegion'));
  await test('getDynamicProxyHost', ()=> get('/vcpcloud/api/padApi/getDynamicProxyHost'));
  await test('queryCurrentTrafficBalance', ()=> get('/vcpcloud/api/padApi/queryCurrentTrafficBalance'));
  await test('getProxys', ()=> get('/vcpcloud/api/padApi/getProxys',{page:1,rows:50}));
  await test('proxyGoodList', ()=> get('/vcpcloud/api/padApi/proxyGoodList'));
  await test('getProxyRegion', ()=> get('/vcpcloud/api/padApi/getProxyRegion'));
  await test('queryProxyList', ()=> post('/vcpcloud/api/padApi/queryProxyList',{page:1,rows:50}));

  // ── COUNTRIES ──
  P('\n── Countries ──');
  await test('country', ()=> get('/vcpcloud/api/padApi/country'));

  // ── AUTOMATION ──
  P('\n── Automation ──');
  await test('autoTaskList', ()=> post('/vcpcloud/api/padApi/autoTaskList',{page:1,rows:50}));

  // ── CLOUD FILES ──
  P('\n── Cloud Files ──');
  await test('selectFiles', ()=> post('/vcpcloud/api/padApi/selectFiles',{page:1,rows:50}));

  // ── NETWORK PROXY ──
  P('\n── Network Proxy ──');
  await test('networkProxyInfo', ()=> post('/vcpcloud/open/network/proxy/info',{padCodes:[D1]}));

  // ── VIRTUAL/REAL SWITCH ──
  P('\n── Virtual/Real Switch ──');
  // Don't execute this yet, just query current state
  // await test('virtualRealSwitch', ()=> post('/vcpcloud/api/padApi/virtualRealSwitch',{padCodes:[D1],type:'virtual'}));

  // ── ASYNC CMD TEST ──
  P('\n── Async CMD (may bypass 2K limit) ──');
  const asyncResult = await test('asyncCmd', ()=> post('/vcpcloud/api/padApi/asyncCmd',{padCodes:[D1],scriptContent:'id; getprop ro.product.model; echo ASYNC_OK'}));
  if (asyncResult.code === 200 && asyncResult.data) {
    const taskId = (asyncResult.data[0]||{}).taskId;
    if (taskId) {
      P(`  Async task ID: ${taskId} — polling...`);
      await new Promise(r=>setTimeout(r,3000));
      const taskResult = await test('padTaskDetail', ()=> post('/vcpcloud/api/padApi/padTaskDetail',{taskIds:[taskId]}));
      if (taskResult.code === 200) {
        P(`  Async result: ${JSON.stringify(taskResult.data||'').slice(0,200)}`);
      }
    }
  }

  // ── BATCH ADB CMD ──
  P('\n── Batch ADB CMD ──');
  await test('batchAdbCmd', ()=> post('/vcpcloud/api/padApi/batch/adb',{padCodes:[D1],cmd:'id; echo BATCH_ADB_OK'}));

  save('api_sweep_results.json', results);
  R.api_sweep = results;

  // Count successes
  const ok = Object.values(results).filter(r=>r.code===200).length;
  const fail = Object.values(results).filter(r=>r.code!==200).length;
  P(`\n  ★ API SWEEP: ${ok} success, ${fail} failed out of ${Object.keys(results).length} endpoints`);
}

// ══════════════════════════════════════════════════════════════════
// PHASE 2b: DEEP PROPERTY EXTRACTION
// ══════════════════════════════════════════════════════════════════
async function phase2b() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 2b: DEEP PROPERTY & IMAGE EXTRACTION');
  console.log('█'.repeat(75));

  // Extract full properties for both devices
  P('[2b-1] Full D1 properties...');
  const propsD1 = await post('/vcpcloud/api/padApi/padProperties', {padCode:D1});
  save('props_d1_full.json', propsD1);
  R.props_d1 = propsD1;
  if (propsD1.code === 200) {
    P(`  D1 props: ${Object.keys(propsD1.data||{}).length} keys`);
  }

  P('[2b-2] Full D2 properties...');
  const propsD2 = await post('/vcpcloud/api/padApi/padProperties', {padCode:D2});
  save('props_d2_full.json', propsD2);
  R.props_d2 = propsD2;

  // Get detailed instance info
  P('[2b-3] D1 padInfo...');
  const infoD1 = await post('/vcpcloud/api/padApi/padInfo', {padCode:D1});
  save('padinfo_d1.json', infoD1);
  R.padinfo_d1 = infoD1;
  if (infoD1.code === 200) {
    const d = infoD1.data || {};
    P(`  D1 info: model=${d.modelName||''} status=${d.vmStatus||''} image=${d.imageId||d.imageName||''}`);
    P(`  D1 info keys: ${Object.keys(d).join(', ').slice(0,200)}`);
  }

  P('[2b-4] D2 padInfo...');
  const infoD2 = await post('/vcpcloud/api/padApi/padInfo', {padCode:D2});
  save('padinfo_d2.json', infoD2);
  R.padinfo_d2 = infoD2;

  // Full instance list with all metadata
  P('[2b-5] Full instance list...');
  const fullList = await post('/vcpcloud/api/padApi/infos', {page:1,rows:100});
  save('instance_list_full.json', fullList);
  R.instance_list = fullList;
  if (fullList.code === 200) {
    const items = fullList.data?.list || fullList.data || [];
    P(`  Total instances: ${Array.isArray(items) ? items.length : 'N/A'}`);
  }

  // Image versions — crucial for Android 15 image creation
  P('[2b-6] Image version list...');
  const images = await post('/vcpcloud/api/padApi/imageVersionList', {});
  save('image_versions.json', images);
  R.image_versions = images;
  if (images.code === 200) {
    const imgList = images.data || [];
    P(`  Images: ${Array.isArray(imgList) ? imgList.length : typeof imgList}`);
    if (Array.isArray(imgList)) {
      for (const img of imgList.slice(0,10)) {
        P(`    ${img.id||img.imageId||'?'}: ${img.name||img.imageName||img.versionName||JSON.stringify(img).slice(0,80)}`);
      }
    }
  }

  // Brand list (24K entries) — just get count and sample
  P('[2b-7] Brand list (24K+ device templates)...');
  const brands = await post('/vcpcloud/api/vcBrand/selectBrandList', {});
  if (brands.code === 200) {
    const bList = brands.data || [];
    const count = Array.isArray(bList) ? bList.length : 0;
    P(`  Total brands: ${count}`);
    save('brand_list_sample.json', Array.isArray(bList) ? bList.slice(0,50) : bList);
    save('brand_list_count.txt', `Total: ${count}`);
    R.brand_count = count;
    // Find Samsung S24 Ultra entries
    if (Array.isArray(bList)) {
      const s24 = bList.filter(b => (b.model||'').includes('S928') || (b.deviceDisplayName||'').includes('S24'));
      if (s24.length > 0) {
        save('brand_s24_ultra.json', s24);
        P(`  S24 Ultra variants: ${s24.length}`);
        for (const s of s24.slice(0,5)) P(`    ${s.model||''} ${s.brand||''} ${s.fingerprint||''}`);
      }
    }
  }

  // Real device templates
  P('[2b-8] Real device ADI templates...');
  const templates = await post('/vcpcloud/api/padApi/templateList', {page:1,rows:100});
  save('adi_templates.json', templates);
  R.adi_templates = templates;
  if (templates.code === 200) {
    const tList = templates.data?.list || templates.data || [];
    P(`  Templates: ${Array.isArray(tList) ? tList.length : typeof tList}`);
    if (Array.isArray(tList)) {
      for (const t of tList.slice(0,5)) P(`    ${JSON.stringify(t).slice(0,120)}`);
    }
  }

  // User ROM info
  P('[2b-9] User ROM upload info...');
  // Don't actually upload, just check the endpoint response with empty params
  const romInfo = await post('/vcpcloud/api/padApi/addUserRom', {});
  save('user_rom_info.json', romInfo);
  R.user_rom = romInfo;
  P(`  ROM upload: code=${romInfo.code} msg=${romInfo.msg||''}`);
}

// ══════════════════════════════════════════════════════════════════
// PHASE 2c: BACKUP/RESTORE TEST
// ══════════════════════════════════════════════════════════════════
async function phase2c() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 2c: BACKUP/RESTORE CAPABILITIES');
  console.log('█'.repeat(75));

  // Check existing backups
  P('[2c-1] Existing backups...');
  const backups = await post('/vcpcloud/api/padApi/localPodBackupSelectPage', {page:1,rows:50});
  save('existing_backups.json', backups);
  R.existing_backups = backups;
  P(`  Backups: code=${backups.code} data=${JSON.stringify(backups.data||'').slice(0,200)}`);

  // Check timing backup list
  P('[2c-2] Timing backup list...');
  const timingBackups = await get('/vcpcloud/api/padApi/vcTimingBackupList');
  save('timing_backups.json', timingBackups);
  R.timing_backups = timingBackups;
  P(`  Timing: code=${timingBackups.code} data=${JSON.stringify(timingBackups.data||'').slice(0,200)}`);

  // Test backup endpoint (without S3 config to see what params it needs)
  P('[2c-3] Test backup endpoint params...');
  const backupTest = await post('/vcpcloud/api/padApi/localPodBackup', {padCode:D1});
  save('backup_test.json', backupTest);
  R.backup_test = backupTest;
  P(`  Backup test: code=${backupTest.code} msg=${backupTest.msg||''} data=${JSON.stringify(backupTest.data||'').slice(0,200)}`);

  // Test restore endpoint params
  P('[2c-4] Test restore endpoint params...');
  const restoreTest = await post('/vcpcloud/api/padApi/localPodRestore', {padCode:D2});
  save('restore_test.json', restoreTest);
  R.restore_test = restoreTest;
  P(`  Restore test: code=${restoreTest.code} msg=${restoreTest.msg||''}`);

  // Storage info
  P('[2c-5] Storage info...');
  const storage = await get('/vcpcloud/api/padApi/getRenewStorageInfo');
  save('storage_info.json', storage);
  R.storage_info = storage;
  P(`  Storage: code=${storage.code} data=${JSON.stringify(storage.data||'').slice(0,200)}`);
}

// ══════════════════════════════════════════════════════════════════
// PHASE 2d: NEIGHBOR ACCESS VIA API METHODS
// ══════════════════════════════════════════════════════════════════
async function phase2d() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 2d: NEIGHBOR ACCESS VIA ALL API METHODS');
  console.log('█'.repeat(75));

  // Load NATS pad codes from previous scan
  const natsFile = path.join(__dirname, '..', 'output', 'nats_v2_results', 'nats_pad_codes.txt');
  let neighborPads = [];
  if (fs.existsSync(natsFile)) {
    neighborPads = fs.readFileSync(natsFile,'utf8').split('\n').filter(l=>l.match(/^ACP/) && l!==D1 && l!==D2);
    P(`  Loaded ${neighborPads.length} neighbor PAD codes from NATS`);
  }
  
  const testPads = neighborPads.slice(0,5);
  R.neighbor_tests = {};

  for (const pad of testPads) {
    P(`\n  Testing ${pad}...`);
    const t = {};

    // syncCmd
    const sync = await post('/vcpcloud/api/padApi/syncCmd', {padCode:pad,scriptContent:'id'}, 10);
    t.syncCmd = sync.code;

    // asyncCmd
    const async_ = await post('/vcpcloud/api/padApi/asyncCmd', {padCodes:[pad],scriptContent:'id'}, 10);
    t.asyncCmd = async_.code;

    // padInfo
    const info = await post('/vcpcloud/api/padApi/padInfo', {padCode:pad}, 10);
    t.padInfo = info.code;
    if (info.code === 200) {
      t.padInfo_data = info.data;
      P(`  ★ padInfo WORKS on ${pad}!`);
    }

    // padProperties
    const props = await post('/vcpcloud/api/padApi/padProperties', {padCode:pad}, 10);
    t.padProperties = props.code;
    if (props.code === 200) {
      t.padProperties_data = props.data;
      P(`  ★ padProperties WORKS on ${pad}!`);
    }

    // adb info
    const adb = await post('/vcpcloud/api/padApi/adb', {padCode:pad,enable:1}, 10);
    t.adb = adb.code;
    if (adb.code === 200) {
      t.adb_data = adb.data;
      P(`  ★ ADB info WORKS on ${pad}!`);
    }

    // backup
    const bk = await post('/vcpcloud/api/padApi/localPodBackup', {padCode:pad}, 10);
    t.backup = bk.code;

    // SDK token
    const tok = await post('/vcpcloud/api/padApi/stsTokenByPadCode', {padCode:pad}, 10);
    t.sdkToken = tok.code;
    if (tok.code === 200) {
      t.sdkToken_data = tok.data;
      P(`  ★ SDK token WORKS on ${pad}!`);
    }

    // screenshot
    const ss = await post('/vcpcloud/api/padApi/screenshot', {padCodes:[pad]}, 10);
    t.screenshot = ss.code;

    R.neighbor_tests[pad] = t;
    const okCount = Object.values(t).filter(v=>v===200).length;
    P(`  ${pad}: ${okCount} endpoints returned 200`);
  }

  save('neighbor_api_tests.json', R.neighbor_tests);
}

// ══════════════════════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════════════════════
async function main() {
  console.log('█'.repeat(75));
  console.log('  FULL SWEEP — Phase 1 & 2: ADB + API Endpoint Discovery');
  console.log('█'.repeat(75));

  await phase1();
  await phase2();
  await phase2b();
  await phase2c();
  await phase2d();

  save('PHASE_1_2_RESULTS.json', R);

  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 1 & 2 COMPLETE');
  console.log('█'.repeat(75));
  const files = fs.readdirSync(OUT).sort();
  console.log(`  ${files.length} result files`);
  for (const f of files) console.log(`    ${f} (${fs.statSync(`${OUT}/${f}`).size}B)`);
  console.log('█'.repeat(75));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
