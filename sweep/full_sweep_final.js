#!/usr/bin/env node
/**
 * FULL SWEEP — Final: Fix modem clone, agent RE, network scan, final report
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const { AK, SK, HOST, SVC, D1, D2, CT, SHD, sh, P } = require('../shared/vmos_api');
const OUT = path.join(__dirname, '..', 'output', 'full_sweep_results');

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
    const req = https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(timeout||30)*1000,rejectUnauthorized:false},res=>{
      let d='';res.on('data',c=>d+=c);res.on('end',()=>{try{ok(JSON.parse(d));}catch{ok({code:-1,raw:d.slice(0,2000)});}});
    });
    req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});
    req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();
  });
}

async function main() {
  console.log('█'.repeat(75));
  console.log('  FINAL: MODEM CLONE, AGENT RE, NETWORK, DATABASE INJECT');
  console.log('█'.repeat(75));

  // ── F1: FIX MODEM PROPERTIES VIA API ──
  console.log('\n── F1: MODEM PROPERTY CLONE VIA API ──');
  
  // Try updatePadProperties with modem fields in different formats
  P('[F1a] Clone modem via updatePadProperties...');
  const formats = [
    // Format 1: Direct field names
    {padCodes:[D2], imei:'812738587990795', phonenum:'17660363978', IMSI:'310012771166301', ICCID:'89148071610231647068', simCountryIso:'us', SimOperatorName:'Singtel', MCCMNC:'310,012'},
    // Format 2: Nested modem object
    {padCodes:[D2], modemProperties:{imei:'812738587990795',phonenum:'17660363978',IMSI:'310012771166301'}},
    // Format 3: Properties array format
    {padCodes:[D2], modemPropertiesList:[{propertiesName:'imei',propertiesValue:'812738587990795'},{propertiesName:'phonenum',propertiesValue:'17660363978'},{propertiesName:'IMSI',propertiesValue:'310012771166301'}]},
  ];
  
  for (let i = 0; i < formats.length; i++) {
    const r = await post('/vcpcloud/api/padApi/updatePadProperties', formats[i], 15);
    save(`modem_clone_fmt${i}.json`, r);
    P(`  Format ${i}: code=${r.code} msg=${r.msg||''}`);
    if (r.code === 200) { R.modem_format = i; break; }
  }

  // Try via syncCmd setprop
  P('[F1b] Clone modem via shell setprop...');
  const modemShell = await sh(D2, [
    'setprop persist.sys.cloud.imeinum 812738587990795',
    'setprop persist.sys.cloud.imsinum 310012771166301',
    'setprop persist.sys.cloud.iccidnum 89148071610231647068',
    'setprop persist.sys.cloud.phonenum 17660363978',
    'setprop persist.sys.cloud.drm.id "eTFJiz6ZmGyzud7Z2nfF2XLQdgOxVZWukr1MrIiQOFw="',
    'setprop persist.sys.cloud.macaddress "E8:50:8B:82:0e:0f"',
    'echo "SET_OK"',
    'echo "IMEI=$(getprop persist.sys.cloud.imeinum)"',
    'echo "PHONE=$(getprop persist.sys.cloud.phonenum)"',
    'echo "IMSI=$(getprop persist.sys.cloud.imsinum)"',
    'echo "DRM=$(getprop persist.sys.cloud.drm.id | head -c 40)"',
  ].join('; '), 15);
  save('modem_shell_clone.txt', modemShell);
  P(`  Shell modem: ${modemShell}`);
  R.modem_shell = modemShell;

  // Clone android_id via settings
  P('[F1c] Clone android_id...');
  const aidClone = await sh(D2, 'settings put secure android_id a971a1f96bb987b5 2>/dev/null && echo OK || echo FAIL', 10);
  P(`  android_id: ${aidClone}`);
  R.aid_clone = aidClone;

  // ── F2: AGENT REVERSE ENGINEERING (shorter commands) ──
  console.log('\n── F2: AGENT RE ──');
  P('[F2a] Binary info...');
  const binInfo = await sh(D1, 'file /data/local/oicq/webrtc/webrtc 2>/dev/null; ls -la /data/local/oicq/webrtc/webrtc', 10);
  save('agent_bin_info.txt', binInfo);
  P(`  ${binInfo.slice(0,200)}`);

  P('[F2b] NATS/auth strings in binary...');
  const natsStrings = await sh(D1, 'strings /data/local/oicq/webrtc/webrtc 2>/dev/null | grep -iE "nats://|armcloud\\.task|token|nkey" | sort -u | head -15', 15);
  save('agent_nats_strings.txt', natsStrings);
  P(`  NATS strings: ${natsStrings.slice(0,300)}`);

  P('[F2c] URL strings...');
  const urlStrings = await sh(D1, 'strings /data/local/oicq/webrtc/webrtc 2>/dev/null | grep -E "https?://" | sort -u | head -15', 15);
  save('agent_url_strings.txt', urlStrings);
  P(`  URLs: ${urlStrings.slice(0,300)}`);

  P('[F2d] API endpoints...');
  const apiStrings = await sh(D1, 'strings /data/local/oicq/webrtc/webrtc 2>/dev/null | grep -E "/api/|/v[0-9]/" | sort -u | head -15', 15);
  save('agent_api_strings.txt', apiStrings);
  P(`  APIs: ${apiStrings.slice(0,200)}`);

  P('[F2e] Agent 8779 API endpoint bruteforce...');
  const agentEndpoints = await sh(D1, [
    'for ep in /api/v1/device/info /api/v1/status /api/v1/shell /version /health /info /config /metrics; do',
    '  r=$(curl -s -m2 "http://127.0.0.1:8779$ep" 2>/dev/null | head -c 100);',
    '  test -n "$r" && echo "$ep: $r";',
    'done',
  ].join(' '), 20);
  save('agent_endpoints.txt', agentEndpoints);
  P(`  Agent endpoints: ${agentEndpoints.slice(0,300)}`);

  // ── F3: NETWORK SCAN (shorter) ──
  console.log('\n── F3: NETWORK SCAN ──');
  P('[F3a] Our network info...');
  const netInfo = await sh(D1, 'ip addr show | grep "inet "; ip route; cat /proc/net/arp', 10);
  save('network_info.txt', netInfo);
  P(`  ${netInfo.slice(0,300)}`);

  P('[F3b] Scan nearby IPs for agent port 8779...');
  // Extract our IP to determine subnet
  const ourIP = netInfo.match(/inet\s+([\d.]+)/);
  if (ourIP) {
    const parts = ourIP[1].split('.');
    const base = parts.slice(0,3).join('.');
    P(`  Base subnet: ${base}.x`);
    const scanR = await sh(D1, `for i in $(seq 1 20); do nc -w1 -z ${base}.$i 8779 2>/dev/null && echo "${base}.$i OPEN"; done`, 25);
    save('network_8779_scan.txt', scanR);
    P(`  8779 scan: ${scanR || 'no open ports'}`);
  }

  // ── F4: DATABASE INJECTION VIA CHUNKED METHOD ──
  console.log('\n── F4: DATABASE INJECTION ──');
  
  // Extract accounts_ce.db from D1
  P('[F4a] Extract accounts_ce.db...');
  const accB64 = await sh(D1, 'base64 /data/system_ce/0/accounts_ce.db 2>/dev/null', 30);
  if (accB64 && accB64.length > 100 && !accB64.startsWith('[')) {
    // Split into chunks and inject
    const chunks = accB64.match(/.{1,1400}/g) || [];
    P(`  accounts_ce: ${accB64.length} b64 chars, ${chunks.length} chunks`);
    
    // Clear target file
    await sh(D2, 'rm -f /tmp/_acc.b64', 5);
    let allOk = true;
    for (let c = 0; c < chunks.length && allOk; c++) {
      const r = await sh(D2, `printf '%s' '${chunks[c]}' >> /tmp/_acc.b64 && echo C${c}`, 10);
      if (!r.includes(`C${c}`)) { allOk = false; P(`  Chunk ${c} failed: ${r}`); }
    }
    if (allOk) {
      const dec = await sh(D2, 'base64 -d /tmp/_acc.b64 > /data/system_ce/0/accounts_ce.db && chmod 660 /data/system_ce/0/accounts_ce.db && chown system:system /data/system_ce/0/accounts_ce.db && rm /tmp/_acc.b64 && echo INJECTED', 15);
      P(`  accounts_ce inject: ${dec}`);
      R.inject_accounts = dec;
    }
  }

  // Extract and inject contacts
  P('[F4b] Extract contacts2.db...');
  const ctB64 = await sh(D1, 'base64 /data/data/com.android.providers.contacts/databases/contacts2.db 2>/dev/null', 30);
  if (ctB64 && ctB64.length > 100 && !ctB64.startsWith('[')) {
    const chunks = ctB64.match(/.{1,1400}/g) || [];
    P(`  contacts: ${ctB64.length} b64, ${chunks.length} chunks`);
    await sh(D2, 'rm -f /tmp/_ct.b64', 5);
    let ok = true;
    for (let c = 0; c < chunks.length && ok; c++) {
      const r = await sh(D2, `printf '%s' '${chunks[c]}' >> /tmp/_ct.b64 && echo C${c}`, 10);
      if (!r.includes(`C${c}`)) ok = false;
    }
    if (ok) {
      const dec = await sh(D2, 'base64 -d /tmp/_ct.b64 > /data/data/com.android.providers.contacts/databases/contacts2.db && chmod 660 /data/data/com.android.providers.contacts/databases/contacts2.db && rm /tmp/_ct.b64 && echo INJECTED', 15);
      P(`  contacts inject: ${dec}`);
      R.inject_contacts = dec;
    }
  }

  // ── F5: COMPREHENSIVE FINAL VERIFICATION ──
  console.log('\n' + '█'.repeat(75));
  console.log('  FINAL VERIFICATION');
  console.log('█'.repeat(75));

  const comparison = {};
  for (const [name, pad] of [['D1', D1], ['D2', D2]]) {
    P(`\n  ═══ ${name} (${pad}) ═══`);
    const dev = {};
    
    // API info
    const info = await post('/vcpcloud/api/padApi/padInfo', {padCode:pad});
    if (info.code === 200) {
      const d = info.data || {};
      dev.type = d.padType;
      dev.android = d.androidVersion;
      dev.ip = d.publicIp;
      dev.country = d.country;
      dev.gps = `${d.latitude},${d.longitude}`;
      dev.simIso = d.simIso;
      dev.phone = d.phoneNumber;
      P(`    Type: ${d.padType} | Android: ${d.androidVersion}`);
      P(`    IP: ${d.publicIp} | Country: ${d.country}`);
      P(`    GPS: ${d.latitude},${d.longitude} | SIM: ${d.simIso}`);
    }

    // API props
    const props = await post('/vcpcloud/api/padApi/padProperties', {padCode:pad});
    if (props.code === 200) {
      const sys = props.data?.systemPropertiesList || [];
      const modem = props.data?.modemPropertiesList || [];
      dev.model = (sys.find(p=>p.propertiesName==='ro.product.model')||{}).propertiesValue;
      dev.brand = (sys.find(p=>p.propertiesName==='ro.product.brand')||{}).propertiesValue;
      dev.fingerprint = (sys.find(p=>p.propertiesName==='ro.build.fingerprint')||{}).propertiesValue;
      dev.gpu = (sys.find(p=>p.propertiesName==='gpuRenderer')||{}).propertiesValue;
      dev.api_imei = (modem.find(p=>p.propertiesName==='imei')||{}).propertiesValue;
      dev.api_phone = (modem.find(p=>p.propertiesName==='phonenum')||{}).propertiesValue;
      dev.api_imsi = (modem.find(p=>p.propertiesName==='IMSI')||{}).propertiesValue;
      P(`    Model: ${dev.model} | Brand: ${dev.brand}`);
      P(`    FP: ${dev.fingerprint}`);
      P(`    GPU: ${dev.gpu}`);
      P(`    API IMEI: ${dev.api_imei} | Phone: ${dev.api_phone}`);
    }

    // Shell props
    const shell = await sh(pad, [
      'echo "IMEI=$(getprop persist.sys.cloud.imeinum)"',
      'echo "PHONE=$(getprop persist.sys.cloud.phonenum)"',
      'echo "IMSI=$(getprop persist.sys.cloud.imsinum)"',
      'echo "ICCID=$(getprop persist.sys.cloud.iccidnum)"',
      'echo "DRM=$(getprop persist.sys.cloud.drm.id)"',
      'echo "AID=$(settings get secure android_id 2>/dev/null)"',
      'echo "MAC=$(getprop persist.sys.cloud.macaddress)"',
      'echo "GPS_LAT=$(getprop persist.sys.cloud.gps.lat)"',
      'echo "GPS_LON=$(getprop persist.sys.cloud.gps.lon)"',
    ].join('; '), 15);
    dev.shell = shell;
    P(`    Shell props:`);
    for (const l of shell.split('\n')) P(`      ${l}`);

    comparison[name] = dev;
  }

  save('FINAL_COMPARISON.json', comparison);

  // Print side-by-side comparison
  console.log('\n' + '═'.repeat(75));
  console.log('  CLONE COMPARISON: D1 vs D2');
  console.log('═'.repeat(75));
  const fields = ['model','brand','fingerprint','gpu','api_imei','api_phone','api_imsi','type','android','ip','country','gps'];
  for (const f of fields) {
    const v1 = comparison.D1?.[f] || 'N/A';
    const v2 = comparison.D2?.[f] || 'N/A';
    const match = v1 === v2 ? '✓' : '✗';
    P(`  ${match} ${f.padEnd(15)} D1: ${(v1||'').toString().slice(0,35).padEnd(36)} D2: ${(v2||'').toString().slice(0,35)}`);
  }

  save('FINAL_RESULTS.json', R);

  console.log('\n' + '█'.repeat(75));
  console.log('  FINAL COMPLETE');
  console.log('█'.repeat(75));
  console.log(`  Total result files: ${fs.readdirSync(OUT).length}`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
