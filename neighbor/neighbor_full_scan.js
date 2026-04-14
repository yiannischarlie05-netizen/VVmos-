#!/usr/bin/env node
/**
 * NEIGHBOR FULL SCAN — Phase 3: Extract device model + running apps from all 445 neighbors
 * Uses raw ADB protocol via nc from D1 (via ADB tunnel) and syncCmd as fallback.
 */

const path = require('path');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const { execSync, exec } = require('child_process');

const { AK, SK, HOST, D1, D2, CT, SHD, P } = require('../shared/vmos_api');
const D1_ADB = 'localhost:8479';
const OUT = path.join(__dirname, '..', 'output', 'neighbor_full_scan_results');

if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });
const save = (f, d) => fs.writeFileSync(`${OUT}/${f}`, typeof d === 'string' ? d : JSON.stringify(d, null, 2));

// HMAC signing
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

// Run command via local ADB tunnel (unlimited output)
function adbShell(cmd, timeoutMs) {
  try {
    return execSync(`adb -s ${D1_ADB} shell "${cmd.replace(/"/g, '\\"')}"`, {
      timeout: timeoutMs || 15000,
      encoding: 'utf8',
      maxBuffer: 10 * 1024 * 1024
    }).trim();
  } catch(e) {
    return `[ADB_ERR: ${(e.message||'').slice(0,100)}]`;
  }
}

async function main() {
  console.log('█'.repeat(75));
  console.log('  NEIGHBOR FULL SCAN — 445 devices: Model + Apps Extraction');
  console.log('█'.repeat(75));

  // Load all neighbor IPs
  const allIPs = fs.readFileSync('/tmp/all_open_neighbors.txt', 'utf8')
    .split('\n')
    .map(l => l.split(':')[0].trim())
    .filter(ip => ip && ip.startsWith('10.'));

  P(`Total neighbor IPs to scan: ${allIPs.length}`);

  // ═══════════════════════════════════════════════════════════
  // PHASE 3a: Get device model from ADB CNXN banner (batch via ADB shell)
  // ═══════════════════════════════════════════════════════════
  P('\n── PHASE 3a: Extract device models via raw ADB CNXN ──');

  const devices = [];
  const BATCH = 20;

  for (let i = 0; i < allIPs.length; i += BATCH) {
    const batch = allIPs.slice(i, i + BATCH);
    const batchNum = Math.floor(i / BATCH) + 1;
    const totalBatches = Math.ceil(allIPs.length / BATCH);
    P(`Batch ${batchNum}/${totalBatches} (${batch.length} IPs)...`);

    // Build a script that queries each IP's ADB CNXN banner
    const script = batch.map(ip =>
      `(printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00\\x07\\x00\\x00\\x00\\x32\\x02\\x00\\x00\\xbc\\xb1\\xa7\\xb1host::\\x00' | nc -w2 ${ip} 5555 2>/dev/null | strings | grep -oP 'ro\\.product\\.(model|brand|name)=[^;]+' | head -3 | tr '\\n' '|'; echo "IP=${ip}")`
    ).join('\n');

    const result = adbShell(script, 30000);

    // Parse results
    for (const line of result.split('\n')) {
      if (!line.includes('IP=')) continue;
      const ipMatch = line.match(/IP=([\d.]+)/);
      if (!ipMatch) continue;
      const ip = ipMatch[1];
      const model = (line.match(/ro\.product\.model=([^|]+)/) || [])[1] || '';
      const brand = (line.match(/ro\.product\.brand=([^|]+)/) || [])[1] || '';
      const name = (line.match(/ro\.product\.name=([^|]+)/) || [])[1] || '';
      devices.push({ ip, model, brand, name, userApps: [], allApps: [] });
    }

    // Also add IPs that didn't respond to CNXN
    for (const ip of batch) {
      if (!devices.find(d => d.ip === ip)) {
        devices.push({ ip, model: '', brand: '', name: '', userApps: [], allApps: [] });
      }
    }
  }

  P(`Device info collected: ${devices.length} (${devices.filter(d=>d.model).length} with model)`);
  save('device_models.json', devices);

  // ═══════════════════════════════════════════════════════════
  // PHASE 3b: Get running user apps from each device
  // Use syncCmd to send raw ADB shell commands via nc
  // Sample 50 diverse devices across subnets for app queries
  // ═══════════════════════════════════════════════════════════
  P('\n── PHASE 3b: Extract running apps (sampling 80 devices) ──');

  // Sample: pick devices spread across subnets
  const subnets = {};
  for (const d of devices) {
    const sub = d.ip.split('.').slice(0,3).join('.');
    if (!subnets[sub]) subnets[sub] = [];
    subnets[sub].push(d);
  }

  const sampled = [];
  for (const [sub, devs] of Object.entries(subnets)) {
    // Take up to 15 per subnet, spread evenly
    const step = Math.max(1, Math.floor(devs.length / 15));
    for (let i = 0; i < devs.length && sampled.length < 80; i += step) {
      sampled.push(devs[i]);
    }
  }

  P(`Sampling ${sampled.length} devices across ${Object.keys(subnets).length} subnets`);

  // Query each sampled device for user apps via raw ADB shell through nc
  for (let i = 0; i < sampled.length; i++) {
    const d = sampled[i];
    if (i % 10 === 0) P(`  Progress: ${i}/${sampled.length}`);

    // Use syncCmd to query neighbor via raw ADB protocol
    const cmd = `(
      printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00\\x07\\x00\\x00\\x00\\x32\\x02\\x00\\x00\\xbc\\xb1\\xa7\\xb1host::\\x00'
      sleep 0.3
      printf 'OPEN\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x25\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00shell:pm list packages -3\\x00'
      sleep 2
    ) | nc -w4 ${d.ip} 5555 2>/dev/null | strings | grep '^package:' | head -30`;

    const result = await syncCmd(D1, cmd, 15);
    
    if (result && result.includes('package:')) {
      d.userApps = result.split('\n')
        .filter(l => l.startsWith('package:'))
        .map(l => l.replace('package:', '').trim());
    }

    // Also get all running processes
    const psCmd = `(
      printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00\\x07\\x00\\x00\\x00\\x32\\x02\\x00\\x00\\xbc\\xb1\\xa7\\xb1host::\\x00'
      sleep 0.3
      printf 'OPEN\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x1b\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00shell:ps -A | wc -l\\x00'
      sleep 1
    ) | nc -w3 ${d.ip} 5555 2>/dev/null | strings | grep -E '^[0-9]+$' | tail -1`;

    const psResult = await syncCmd(D1, psCmd, 8);
    d.processCount = parseInt(psResult) || 0;
  }

  // Update main devices array with sampled data
  for (const s of sampled) {
    const d = devices.find(x => x.ip === s.ip);
    if (d) {
      d.userApps = s.userApps;
      d.processCount = s.processCount;
    }
  }

  save('device_apps.json', devices);

  // ═══════════════════════════════════════════════════════════
  // PHASE 4: GENERATE REPORT
  // ═══════════════════════════════════════════════════════════
  P('\n── PHASE 4: Generating Report ──');

  const withApps = devices.filter(d => d.userApps.length > 0);
  const withModel = devices.filter(d => d.model);
  const sterile = sampled.filter(d => d.userApps.length === 0);

  // Collect all unique apps
  const allApps = {};
  for (const d of devices) {
    for (const app of d.userApps) {
      if (!allApps[app]) allApps[app] = [];
      allApps[app].push(d.ip);
    }
  }

  let report = `# NEIGHBOR FULL SCAN REPORT\n\n`;
  report += `Generated: ${new Date().toISOString()}\n\n`;
  report += `## Summary\n\n`;
  report += `| Metric | Count |\n|--------|-------|\n`;
  report += `| **Total Neighbors Found** | ${devices.length} |\n`;
  report += `| **With Device Model** | ${withModel.length} |\n`;
  report += `| **Sampled for Apps** | ${sampled.length} |\n`;
  report += `| **With User Apps** | ${withApps.length} |\n`;
  report += `| **Sterile (system only)** | ${sterile.length} |\n`;
  report += `| **Unique User Apps Found** | ${Object.keys(allApps).length} |\n\n`;

  report += `## Subnet Distribution\n\n`;
  report += `| Subnet | Devices |\n|--------|--------|\n`;
  for (const [sub, devs] of Object.entries(subnets).sort((a,b) => b[1].length - a[1].length)) {
    report += `| ${sub}.x | ${devs.length} |\n`;
  }

  if (withApps.length > 0) {
    report += `\n## Devices WITH User Apps (Clone Candidates!)\n\n`;
    report += `| IP | Model | Brand | User Apps |\n|-----|-------|-------|----------|\n`;
    for (const d of withApps) {
      report += `| ${d.ip} | ${d.model || '?'} | ${d.brand || '?'} | ${d.userApps.join(', ')} |\n`;
    }
  }

  if (Object.keys(allApps).length > 0) {
    report += `\n## All Unique User Apps Found\n\n`;
    report += `| App Package | Found On # Devices |\n|-------------|-------------------|\n`;
    for (const [app, ips] of Object.entries(allApps).sort((a,b) => b[1].length - a[1].length)) {
      report += `| ${app} | ${ips.length} |\n`;
    }
  }

  report += `\n## Devices with Model Info\n\n`;
  report += `| IP | Model | Brand | Name |\n|-----|-------|-------|------|\n`;
  for (const d of withModel.slice(0, 100)) {
    report += `| ${d.ip} | ${d.model} | ${d.brand} | ${d.name} |\n`;
  }

  if (sterile.length > 0 && withApps.length === 0) {
    report += `\n## Note: All Sampled Devices Are Sterile\n\n`;
    report += `None of the ${sampled.length} sampled devices had user apps installed.\n`;
    report += `These are fresh VMOS cloud containers with only system services running.\n`;
  }

  report += `\n## Recommendation\n\n`;
  if (withApps.length > 0) {
    report += `**${withApps.length} devices have user apps!** These are prime clone candidates.\n`;
    report += `Proceed with full data extraction from the best candidates.\n`;
  } else {
    report += `All neighbors are sterile. Consider:\n`;
    report += `1. Cross-clone D1 ↔ D2\n`;
    report += `2. Install apps on neighbors first\n`;
    report += `3. Synthetic data injection\n`;
  }

  save('NEIGHBOR_FULL_SCAN_REPORT.md', report);
  // Also save to project root
  fs.writeFileSync(path.join(__dirname, '..', 'reports', 'NEIGHBOR_FULL_SCAN_REPORT.md'), report);

  P(`\nReport saved to ${OUT}/NEIGHBOR_FULL_SCAN_REPORT.md`);
  P(`Total: ${devices.length} neighbors, ${withApps.length} with user apps, ${Object.keys(allApps).length} unique apps`);

  console.log('\n' + '█'.repeat(75));
  console.log('  SCAN COMPLETE');
  console.log('█'.repeat(75));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
