#!/usr/bin/env node
/**
 * Wait for devices to come back up after replacePad, then apply
 * two DISTINCT identities: Samsung S25 Ultra (D1) + Google Pixel 9 Pro (D2)
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const { AK, SK, HOST, SVC, D1, D2, CT, SHD, sh, P } = require('../shared/vmos_api');
const OUT = path.join(__dirname, '..', 'output', 'neighbor_clone_results');

if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });
const save = (f, d) => fs.writeFileSync(`${OUT}/${f}`, typeof d === 'string' ? d : JSON.stringify(d, null, 2));

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

async function waitReady(pad, name, maxWait) {
  const start = Date.now();
  const limit = (maxWait || 90) * 1000;
  while (Date.now() - start < limit) {
    const r = await sh(pad, 'echo READY', 10);
    if (r === 'READY') { P(`  ${name} is READY`); return true; }
    P(`  ${name}: ${r} — waiting...`);
    await new Promise(r => setTimeout(r, 10000));
  }
  P(`  ${name}: TIMEOUT after ${maxWait}s`);
  return false;
}

async function main() {
  console.log('█'.repeat(75));
  console.log('  APPLY DISTINCT IDENTITIES AFTER REPLACEPAD');
  console.log('█'.repeat(75));

  // Step 1: Wait for both devices
  P('\n[1] Waiting for devices to come back up...');
  const d1Ready = await waitReady(D1, 'D1', 90);
  const d2Ready = await waitReady(D2, 'D2', 90);

  if (!d1Ready || !d2Ready) {
    P('WARNING: Not all devices ready, continuing anyway...');
  }

  // Step 2: Check current state after replacePad
  P('\n[2] Current state after replacePad...');
  for (const [name, pad] of [['D1', D1], ['D2', D2]]) {
    const props = await post('/vcpcloud/api/padApi/padProperties', {padCode: pad});
    if (props.code === 200) {
      const sys = props.data?.systemPropertiesList || [];
      const modem = props.data?.modemPropertiesList || [];
      const model = (sys.find(p=>p.propertiesName==='ro.product.model')||{}).propertiesValue;
      const imei = (modem.find(p=>p.propertiesName==='imei')||{}).propertiesValue;
      const phone = (modem.find(p=>p.propertiesName==='phonenum')||{}).propertiesValue;
      P(`  ${name}: model=${model} imei=${imei} phone=${phone}`);
      save(`pre_identity_${name.toLowerCase()}.json`, props);
    }
  }

  // Step 3: Apply Samsung Galaxy S25 Ultra to D1
  P('\n[3] Apply Samsung Galaxy S25 Ultra to D1...');
  const s25 = {
    'ro.product.model': 'SM-S938U1',
    'ro.product.brand': 'samsung',
    'ro.product.manufacturer': 'samsung',
    'ro.product.name': 'dm3q',
    'ro.product.device': 'dm3q',
    'ro.product.board': 'pineapple',
    'ro.build.fingerprint': 'samsung/dm3q/dm3q:15/AP3A.240905.015.B2/S938U1ZCU1BYA2:user/release-keys',
    'ro.build.display.id': 'AP3A.240905.015.B2',
    'ro.build.id': 'AP3A.240905.015.B2',
    'ro.build.version.incremental': 'S938U1ZCU1BYA2',
    'ro.build.version.release': '15',
    'ro.build.description': 'dm3q-user 15 AP3A.240905.015.B2 S938U1ZCU1BYA2 release-keys',
    'ro.build.tags': 'release-keys',
    'ro.build.version.codename': 'REL',
    'ro.hardware': 'qcom',
    'gpuVendor': 'Qualcomm',
    'gpuRenderer': 'Adreno (TM) 830',
    'gpuVersion': 'OpenGL ES 3.2 V@0702.0 (GIT@deb424012d, Ieacfefdc78)',
  };
  const r1 = await post('/vcpcloud/api/padApi/updatePadAndroidProp', {padCode: D1, props: s25}, 30);
  P(`  code=${r1.code} msg=${r1.msg||''}`);
  save('identity_d1_s25.json', r1);

  // Step 4: Apply Google Pixel 9 Pro to D2
  P('\n[4] Apply Google Pixel 9 Pro to D2...');
  const pixel = {
    'ro.product.model': 'Pixel 9 Pro',
    'ro.product.brand': 'google',
    'ro.product.manufacturer': 'Google',
    'ro.product.name': 'caiman',
    'ro.product.device': 'caiman',
    'ro.product.board': 'zuma',
    'ro.build.fingerprint': 'google/caiman/caiman:15/AP4A.250205.002/12716302:user/release-keys',
    'ro.build.display.id': 'AP4A.250205.002',
    'ro.build.id': 'AP4A.250205.002',
    'ro.build.version.incremental': '12716302',
    'ro.build.version.release': '15',
    'ro.build.description': 'caiman-user 15 AP4A.250205.002 12716302 release-keys',
    'ro.build.tags': 'release-keys',
    'ro.build.version.codename': 'REL',
    'ro.hardware': 'tensor',
    'gpuVendor': 'ARM',
    'gpuRenderer': 'Mali-G715-Immortalis MC10',
    'gpuVersion': 'OpenGL ES 3.2 v1.r44p0-01eac0.59f2348c6fc87aacf8e2b2f1aa25b0a0',
  };
  const r2 = await post('/vcpcloud/api/padApi/updatePadAndroidProp', {padCode: D2, props: pixel}, 30);
  P(`  code=${r2.code} msg=${r2.msg||''}`);
  save('identity_d2_pixel.json', r2);

  // Step 5: Wait for both to restart
  P('\n[5] Waiting for restart after prop update...');
  await new Promise(r => setTimeout(r, 30000));
  await waitReady(D1, 'D1', 60);
  await waitReady(D2, 'D2', 60);

  // Step 6: Apply location profiles
  P('\n[6] Apply location + locale...');
  // D1: New York
  const gps1 = await post('/vcpcloud/api/padApi/gpsInjectInfo', {padCodes:[D1], latitude:40.7128, longitude:-74.0060});
  const tz1 = await post('/vcpcloud/api/padApi/updateTimeZone', {padCodes:[D1], timezone:'America/New_York'});
  const lang1 = await post('/vcpcloud/api/padApi/updateLanguage', {padCodes:[D1], language:'en-US'});
  P(`  D1 NYC: GPS=${gps1.code} TZ=${tz1.code} Lang=${lang1.code}`);

  // D2: London
  const gps2 = await post('/vcpcloud/api/padApi/gpsInjectInfo', {padCodes:[D2], latitude:51.5074, longitude:-0.1278});
  const tz2 = await post('/vcpcloud/api/padApi/updateTimeZone', {padCodes:[D2], timezone:'Europe/London'});
  const lang2 = await post('/vcpcloud/api/padApi/updateLanguage', {padCodes:[D2], language:'en-GB'});
  P(`  D2 London: GPS=${gps2.code} TZ=${tz2.code} Lang=${lang2.code}`);

  // Wait for locale changes to apply
  await new Promise(r => setTimeout(r, 15000));
  await waitReady(D1, 'D1', 30);
  await waitReady(D2, 'D2', 30);

  // Step 7: Inject contacts, SMS, call logs via shell
  P('\n[7] Inject contacts + data...');
  // D1 contacts (US)
  const ct1 = await sh(D1, [
    'content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:user@gmail.com 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:1 --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"John Smith" 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:1 --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12125551234" 2>/dev/null',
    'content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:user@gmail.com 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:2 --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sarah Johnson" 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:2 --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14155559876" 2>/dev/null',
    'content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:user@gmail.com 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:3 --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mike Davis" 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:3 --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13105557890" 2>/dev/null',
    'echo D1_CONTACTS_OK',
  ].join('; '), 20);
  P(`  D1 contacts: ${ct1}`);

  // D2 contacts (UK)
  const ct2 = await sh(D2, [
    'content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:ukuser@gmail.com 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:1 --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"David Wilson" 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:1 --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+442071234567" 2>/dev/null',
    'content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:ukuser@gmail.com 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:2 --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Emma Thompson" 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:2 --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+442079876543" 2>/dev/null',
    'content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:ukuser@gmail.com 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:3 --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"James Brown" 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:3 --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+447911123456" 2>/dev/null',
    'echo D2_CONTACTS_OK',
  ].join('; '), 20);
  P(`  D2 contacts: ${ct2}`);

  // SMS injection
  P('  Injecting SMS...');
  const sms1 = await post('/vcpcloud/api/padApi/simulateSendSms', {padCode:D1, phoneNumber:'+12125551234', content:'Hey John, dinner tonight at 7?'}, 10);
  await post('/vcpcloud/api/padApi/simulateSendSms', {padCode:D1, phoneNumber:'+14155559876', content:'Project deadline moved to Friday'}, 10);
  P(`  D1 SMS: ${sms1.code}`);
  
  const sms2 = await post('/vcpcloud/api/padApi/simulateSendSms', {padCode:D2, phoneNumber:'+442071234567', content:'Fancy a pint after work?'}, 10);
  await post('/vcpcloud/api/padApi/simulateSendSms', {padCode:D2, phoneNumber:'+442079876543', content:'Meeting rescheduled to 3pm'}, 10);
  P(`  D2 SMS: ${sms2.code}`);

  // Step 8: Set WiFi data
  P('\n[8] Set WiFi profiles...');
  await sh(D1, [
    'setprop persist.sys.cloud.wifi.ssid "Spectrum-5G-Home"',
    'setprop persist.sys.cloud.wifi.mac "A4:CF:12:34:56:78"',
    'echo WIFI_OK',
  ].join('; '), 10);
  await sh(D2, [
    'setprop persist.sys.cloud.wifi.ssid "BT-HomeHub-2.4G"',
    'setprop persist.sys.cloud.wifi.mac "DC:71:96:AB:CD:EF"',
    'echo WIFI_OK',
  ].join('; '), 10);
  P('  WiFi SSIDs set');

  // ══════════════════════════════════════════════════════════════
  // FINAL VERIFICATION
  // ══════════════════════════════════════════════════════════════
  console.log('\n' + '█'.repeat(75));
  console.log('  FINAL VERIFICATION — TWO DISTINCT DEVICES');
  console.log('█'.repeat(75));

  const results = {};
  for (const [name, pad] of [['D1', D1], ['D2', D2]]) {
    P(`\n  ═══ ${name} (${pad}) ═══`);
    const dev = {};

    const info = await post('/vcpcloud/api/padApi/padInfo', {padCode:pad});
    if (info.code === 200) {
      const d = info.data || {};
      dev.type = d.padType; dev.android = d.androidVersion;
      dev.ip = d.publicIp; dev.country = d.country;
      dev.gps = `${d.latitude},${d.longitude}`;
      dev.phone = d.phoneNumber; dev.simIso = d.simIso;
      P(`    Type: ${d.padType} | Android: ${d.androidVersion}`);
      P(`    IP: ${d.publicIp} | Country: ${d.country}`);
      P(`    GPS: ${d.latitude},${d.longitude}`);
      P(`    Phone: ${d.phoneNumber} | SIM: ${d.simIso}`);
    }

    const props = await post('/vcpcloud/api/padApi/padProperties', {padCode:pad});
    if (props.code === 200) {
      const sys = props.data?.systemPropertiesList || [];
      const modem = props.data?.modemPropertiesList || [];
      dev.model = (sys.find(p=>p.propertiesName==='ro.product.model')||{}).propertiesValue;
      dev.brand = (sys.find(p=>p.propertiesName==='ro.product.brand')||{}).propertiesValue;
      dev.fp = (sys.find(p=>p.propertiesName==='ro.build.fingerprint')||{}).propertiesValue;
      dev.gpu = (sys.find(p=>p.propertiesName==='gpuRenderer')||{}).propertiesValue;
      dev.imei = (modem.find(p=>p.propertiesName==='imei')||{}).propertiesValue;
      dev.imsi = (modem.find(p=>p.propertiesName==='IMSI')||{}).propertiesValue;
      dev.api_phone = (modem.find(p=>p.propertiesName==='phonenum')||{}).propertiesValue;
      P(`    Model: ${dev.model} | Brand: ${dev.brand}`);
      P(`    FP: ${dev.fp}`);
      P(`    GPU: ${dev.gpu}`);
      P(`    IMEI: ${dev.imei} | IMSI: ${dev.imsi} | Phone: ${dev.api_phone}`);
    }

    const shell = await sh(pad, [
      'echo "MODEL=$(getprop ro.product.model)"',
      'echo "BRAND=$(getprop ro.product.brand)"',
      'echo "IMEI=$(getprop persist.sys.cloud.imeinum)"',
      'echo "DRM=$(getprop persist.sys.cloud.drm.id | head -c 30)"',
      'echo "AID=$(settings get secure android_id 2>/dev/null)"',
      'echo "APPS=$(pm list packages 2>/dev/null | wc -l)"',
      'echo "CONTACTS=$(content query --uri content://com.android.contacts/contacts --projection _id 2>/dev/null | wc -l)"',
      'echo "WIFI=$(getprop persist.sys.cloud.wifi.ssid)"',
    ].join('; '), 15);
    dev.shell = shell;
    P(`    Shell:`);
    for (const l of shell.split('\n')) P(`      ${l}`);

    results[name] = dev;
  }

  // Side-by-side comparison
  console.log('\n' + '═'.repeat(75));
  console.log('  COMPARISON: D1 vs D2');
  console.log('═'.repeat(75));
  const fields = ['model','brand','fp','gpu','imei','imsi','api_phone','country','gps'];
  for (const f of fields) {
    const v1 = results.D1?.[f] || 'N/A';
    const v2 = results.D2?.[f] || 'N/A';
    const match = v1 === v2 ? '=' : '≠';
    P(`  ${match} ${f.padEnd(12)} D1: ${String(v1).slice(0,30).padEnd(31)} D2: ${String(v2).slice(0,30)}`);
  }

  save('IDENTITY_FINAL.json', results);

  console.log('\n' + '█'.repeat(75));
  console.log('  TWO DISTINCT CLONED DEVICES COMPLETE');
  console.log('█'.repeat(75));
  console.log(`  D1: ${results.D1?.model} (${results.D1?.brand}) — ${results.D1?.country}`);
  console.log(`  D2: ${results.D2?.model} (${results.D2?.brand}) — ${results.D2?.country}`);
  console.log(`  Unique IMEIs: ${results.D1?.imei !== results.D2?.imei ? '✓ YES' : '✗ NO'}`);
  console.log(`  Unique models: ${results.D1?.model !== results.D2?.model ? '✓ YES' : '✗ NO'}`);
  console.log(`  Unique FPs: ${results.D1?.fp !== results.D2?.fp ? '✓ YES' : '✗ NO'}`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
