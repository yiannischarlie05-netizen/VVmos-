#!/usr/bin/env node
/**
 * FULL CLONE - FIXED VERSION
 * ==========================
 * 
 * Fixes:
 * 1. Property parsing regex
 * 2. Direct property extraction via getprop commands
 * 3. Better handling of large files
 * 4. Complete identity cloning
 */

const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { AK, SK, HOST, SVC, CT, SHD } = require('../shared/vmos_api');
const SOURCE = 'ACP250923JS861KJ';
const TARGET = 'ACP251008GUOEEHB';

const SAVE_DIR = path.join(__dirname, '..', 'output', 'full_clone_data');
const R = { ts: new Date().toISOString(), source: SOURCE, target: TARGET, props: {}, files: {}, injection: {} };

function sign(bj){const xd=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z');const sd=xd.slice(0,8);const xs=crypto.createHash('sha256').update(bj,'utf8').digest('hex');const can=[`host:${VMOS_HOST}`,`x-date:${xd}`,`content-type:${VMOS_CT}`,`signedHeaders:${VMOS_SH}`,`x-content-sha256:${xs}`].join('\n');const hc=crypto.createHash('sha256').update(can,'utf8').digest('hex');const sts=['HMAC-SHA256',xd,`${sd}/${VMOS_SERVICE}/request`,hc].join('\n');const kd=crypto.createHmac('sha256',Buffer.from(SK,'utf8')).update(sd).digest();const ks=crypto.createHmac('sha256',kd).update(VMOS_SERVICE).digest();const sk2=crypto.createHmac('sha256',ks).update('request').digest();const sig=crypto.createHmac('sha256',sk2).update(sts).digest('hex');return{'content-type':VMOS_CT,'x-date':xd,'x-host':VMOS_HOST,'authorization':`HMAC-SHA256 Credential=${AK}, SignedHeaders=${VMOS_SH}, Signature=${sig}`};}
function post(p,d,s){return new Promise((ok)=>{const b=JSON.stringify(d||{});const h=sign(b);const buf=Buffer.from(b,'utf8');const req=https.request({hostname:VMOS_HOST,path:p,method:'POST',headers:{...h,'content-length':buf.length},timeout:(s||30)*1000},res=>{let r='';res.on('data',c=>r+=c);res.on('end',()=>{try{ok(JSON.parse(r));}catch{ok({code:-1,raw:r.slice(0,300)});}});});req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();});}
async function cmd(pad,script,sec){try{const r=await post('/vcpcloud/api/padApi/syncCmd',{padCode:pad,scriptContent:script},sec||30);if(r.code!==200)return{ok:false,out:`[API ${r.code}]`};const it=(Array.isArray(r.data)?r.data:[r.data])[0]||{};return{ok:it.taskStatus===3,out:(it.errorMsg||it.taskResult||'').trim()};}catch(e){return{ok:false,out:`[ERR]`};}}

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d){if(!fs.existsSync(d))fs.mkdirSync(d,{recursive:true});return d;}
function save(f,d){fs.writeFileSync(path.join(SAVE_DIR,f),typeof d==='string'?d:JSON.stringify(d,null,2));}

// Key properties to clone for device identity
const IDENTITY_PROPS = [
  'ro.product.model',
  'ro.product.brand', 
  'ro.product.manufacturer',
  'ro.product.device',
  'ro.product.name',
  'ro.product.board',
  'ro.hardware',
  'ro.serialno',
  'ro.boot.serialno',
  'ro.build.fingerprint',
  'ro.build.display.id',
  'ro.build.id',
  'ro.build.version.release',
  'ro.build.version.sdk',
  'ro.build.description',
  'persist.sys.cloud.imeinum',
  'persist.sys.cloud.imsinum',
  'persist.sys.cloud.iccidnum',
  'persist.sys.cloud.phonenum',
  'persist.sys.cloud.macaddress',
  'persist.sys.cloud.gps.lat',
  'persist.sys.cloud.gps.lon',
  'persist.sys.cloud.drm.id',
];

async function main() {
  console.log('═'.repeat(70));
  console.log('  FULL CLONE - FIXED VERSION');
  console.log('═'.repeat(70));
  console.log(`  Source: ${SOURCE} → Target: ${TARGET}`);
  console.log('═'.repeat(70));

  ensureDir(SAVE_DIR);

  // Enable root
  log('Enabling root...');
  await post('/vcpcloud/api/padApi/switchRoot', { padCodes: [SOURCE, TARGET], rootStatus: 1, rootType: 0 });
  await post('/vcpcloud/api/padApi/switchRoot', { padCodes: [SOURCE, TARGET], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });

  // ═══════════════════════════════════════════════════════════════════════
  // PHASE 1: EXTRACT PROPERTIES ONE BY ONE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('\n▶ PHASE 1: EXTRACT DEVICE IDENTITY PROPERTIES');
  
  const extractedProps = {};
  
  for (const prop of IDENTITY_PROPS) {
    const r = await cmd(SOURCE, `getprop "${prop}"`, 10);
    if (r.ok && r.out && r.out.length > 0 && !r.out.startsWith('[')) {
      extractedProps[prop] = r.out;
      log(`  ${prop} = ${r.out.slice(0, 50)}`);
    }
    await sleep(100);
  }
  
  // Get android_id
  const androidId = await cmd(SOURCE, 'settings get secure android_id 2>/dev/null', 10);
  if (androidId.ok && androidId.out.match(/^[0-9a-f]{16}$/)) {
    extractedProps['android_id'] = androidId.out;
    log(`  android_id = ${androidId.out}`);
  }
  
  R.props = extractedProps;
  save('extracted_props.json', extractedProps);
  log(`\n  Extracted ${Object.keys(extractedProps).length} properties`);

  // ═══════════════════════════════════════════════════════════════════════
  // PHASE 2: INJECT PROPERTIES INTO TARGET
  // ═══════════════════════════════════════════════════════════════════════
  console.log('\n▶ PHASE 2: INJECT PROPERTIES INTO TARGET');
  
  const injected = { props: [], failed: [] };
  
  for (const [prop, value] of Object.entries(extractedProps)) {
    if (prop === 'android_id') {
      // Use settings command for android_id
      const r = await cmd(TARGET, `settings put secure android_id "${value}"`, 10);
      if (r.ok) {
        injected.props.push(prop);
        log(`  ✓ ${prop} = ${value}`);
      } else {
        injected.failed.push(prop);
      }
    } else {
      // Use setprop for other properties
      const escapedValue = value.replace(/"/g, '\\"').replace(/\$/g, '\\$');
      const r = await cmd(TARGET, `setprop "${prop}" "${escapedValue}"`, 10);
      if (r.ok) {
        injected.props.push(prop);
        log(`  ✓ ${prop}`);
      } else {
        injected.failed.push(prop);
      }
    }
    await sleep(100);
  }
  
  log(`\n  Injected: ${injected.props.length}, Failed: ${injected.failed.length}`);

  // ═══════════════════════════════════════════════════════════════════════
  // PHASE 3: CLONE FILES
  // ═══════════════════════════════════════════════════════════════════════
  console.log('\n▶ PHASE 3: CLONE DATABASE FILES');
  
  const filesToClone = [
    { name: 'accounts_ce.db', src: '/data/system_ce/0/accounts_ce.db', perm: '600', owner: 'system:system' },
    { name: 'contacts2.db', src: '/data/data/com.android.providers.contacts/databases/contacts2.db' },
    { name: 'calllog.db', src: '/data/data/com.android.providers.contacts/databases/calllog.db' },
    { name: 'mmssms.db', src: '/data/data/com.android.providers.telephony/databases/mmssms.db' },
  ];
  
  for (const file of filesToClone) {
    log(`  Cloning ${file.name}...`);
    
    // Extract via base64
    const extract = await cmd(SOURCE, `base64 "${file.src}" 2>/dev/null | head -c 100000`, 60);
    
    if (extract.ok && extract.out.length > 100 && !extract.out.startsWith('[')) {
      R.files[file.name] = { size: extract.out.length };
      save(`${file.name}.b64`, extract.out);
      
      // Inject via base64 decode
      const inject = await cmd(TARGET, `echo '${extract.out}' | base64 -d > "${file.src}" 2>/dev/null && echo OK`, 60);
      
      if (inject.ok && inject.out.includes('OK')) {
        // Set permissions if specified
        if (file.perm) {
          await cmd(TARGET, `chmod ${file.perm} "${file.src}"`, 5);
        }
        if (file.owner) {
          await cmd(TARGET, `chown ${file.owner} "${file.src}"`, 5);
        }
        
        injected.props.push(file.name);
        log(`    ✓ ${file.name} cloned (${extract.out.length} b64 chars)`);
      } else {
        injected.failed.push(file.name);
        log(`    ✗ ${file.name} injection failed`);
      }
    } else {
      log(`    - ${file.name} not found or empty`);
    }
    
    await sleep(200);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // PHASE 4: VERIFICATION
  // ═══════════════════════════════════════════════════════════════════════
  console.log('\n▶ PHASE 4: VERIFICATION');
  
  log('Source device:');
  const srcCheck = await cmd(SOURCE, [
    'echo "MODEL: $(getprop ro.product.model)"',
    'echo "BRAND: $(getprop ro.product.brand)"',
    'echo "FINGERPRINT: $(getprop ro.build.fingerprint | head -c 60)"',
    'echo "IMEI: $(getprop persist.sys.cloud.imeinum)"',
    'echo "ANDROID_ID: $(settings get secure android_id 2>/dev/null)"',
  ].join('; '), 20);
  for (const line of srcCheck.out.split('\n')) log(`  ${line}`);
  
  log('\nTarget device:');
  const tgtCheck = await cmd(TARGET, [
    'echo "MODEL: $(getprop ro.product.model)"',
    'echo "BRAND: $(getprop ro.product.brand)"',
    'echo "FINGERPRINT: $(getprop ro.build.fingerprint | head -c 60)"',
    'echo "IMEI: $(getprop persist.sys.cloud.imeinum)"',
    'echo "ANDROID_ID: $(settings get secure android_id 2>/dev/null)"',
  ].join('; '), 20);
  for (const line of tgtCheck.out.split('\n')) log(`  ${line}`);
  
  R.verification = { source: srcCheck.out, target: tgtCheck.out };
  R.injection = injected;

  // Save report
  const reportFile = path.join(SAVE_DIR, `CLONE_REPORT_${Date.now()}.json`);
  fs.writeFileSync(reportFile, JSON.stringify(R, null, 2));

  // ═══════════════════════════════════════════════════════════════════════
  // SUMMARY
  // ═══════════════════════════════════════════════════════════════════════
  console.log('\n' + '═'.repeat(70));
  console.log('  CLONE COMPLETE');
  console.log('═'.repeat(70));
  console.log(`  Properties cloned: ${injected.props.filter(p => !p.includes('.db')).length}`);
  console.log(`  Files cloned: ${injected.props.filter(p => p.includes('.db')).length}`);
  console.log(`  Failed: ${injected.failed.length}`);
  console.log(`  Report: ${reportFile}`);
  console.log('═'.repeat(70));

  // Compare key identity values
  console.log('\n  IDENTITY COMPARISON:');
  const srcModel = extractedProps['ro.product.model'] || 'N/A';
  const srcBrand = extractedProps['ro.product.brand'] || 'N/A';
  const srcImei = extractedProps['persist.sys.cloud.imeinum'] || 'N/A';
  const srcAndroid = extractedProps['android_id'] || 'N/A';
  
  // Get target values
  const tgtModel = await cmd(TARGET, 'getprop ro.product.model', 10);
  const tgtBrand = await cmd(TARGET, 'getprop ro.product.brand', 10);
  const tgtImei = await cmd(TARGET, 'getprop persist.sys.cloud.imeinum', 10);
  const tgtAndroid = await cmd(TARGET, 'settings get secure android_id 2>/dev/null', 10);
  
  console.log(`  Model:      ${srcModel} → ${tgtModel.out} ${srcModel === tgtModel.out ? '✓' : '✗'}`);
  console.log(`  Brand:      ${srcBrand} → ${tgtBrand.out} ${srcBrand === tgtBrand.out ? '✓' : '✗'}`);
  console.log(`  IMEI:       ${srcImei} → ${tgtImei.out} ${srcImei === tgtImei.out ? '✓' : '✗'}`);
  console.log(`  Android ID: ${srcAndroid} → ${tgtAndroid.out} ${srcAndroid === tgtAndroid.out ? '✓' : '✗'}`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
