#!/usr/bin/env node

/**
 * FULL SWEEP: ADB-BASED EXTRACTION (No 2000-char limit)
 * Red Team Offensive - Direct device interrogation
 * Autonomous execution mode (Tier 29-30)
 */

const fs = require('fs');
const { execSync, exec } = require('child_process');
const path = require('path');

const results = {
  timestamp: new Date().toISOString(),
  devices: {},
  extracted_data: {},
  cloning_vectors: [],
  neighbors: [],
  errors: []
};

function runAdbCommand(device, command, returnError = false) {
  try {
    const cmd = `adb -s ${device} shell "${command}" 2>&1`;
    const output = execSync(cmd, { encoding: 'utf8', timeout: 10000, maxBuffer: 10 * 1024 * 1024 });
    return output;
  } catch (e) {
    if (returnError) return `ERROR: ${e.message}`;
    return '';
  }
}

async function main() {
  console.log('╔════════════════════════════════════════════════════════════════════╗');
  console.log('║              FULL SWEEP: ADB-BASED EXTRACTION                      ║');
  console.log('║           Direct Device Interrogation (No Char Limit)              ║');
  console.log('║                    60+ Data Vectors                                ║');
  console.log('╚════════════════════════════════════════════════════════════════════╝');
  
  // Get device list
  let devices = [];
  try {
    const devList = execSync('adb devices | grep -v "^List" | grep "device$" | awk "{print $1}"', 
      { encoding: 'utf8' });
    devices = devList.trim().split('\n').filter(d => d);
    console.log(`\n[*] Found ${devices.length} connected devices:`);
    devices.forEach(d => console.log(`  - ${d}`));
  } catch (e) {
    console.log('✗ Failed to get device list');
    process.exit(1);
  }
  
  // ===== PHASE 1: System Properties & Identity =====
  console.log('\n[PHASE 1] System Properties & Identity ('.repeat(0) + 'Device Fingerprinting)');
  console.log('─'.repeat(70));
  
  for (const device of devices) {
    console.log(`\n◆ Device: ${device}`);
    results.devices[device] = {
      properties: {},
      extracted_data: {},
      escape_capability: {},
      cloning_vectors: []
    };
    
    // Get comprehensive system properties
    const props = runAdbCommand(device, 'getprop 2>/dev/null || setprop');
    const propLines = props.split('\n');
    const keyProps = {};
    
    propLines.forEach(line => {
      const match = line.match(/\[(.*?)\]\s*:\s*\[(.*?)\]/);
      if (match) {
        keyProps[match[1]] = match[2];
      }
    });
    
    // Extract key identity properties
    const identityKeys = [
      'ro.product.brand', 'ro.product.model', 'ro.build.fingerprint',
      'ro.serialno', 'ro.boot.serialno', 'persist.sys.usb.config',
      'ro.hardware', 'ro.boot.hardware', 'ro.baseband', 'ro.bootloader',
      'gsm.device.name', 'gsm.nitz.time', 'gsm.operator.alpha', 'gsm.sim.operator.alpha',
      'gsm.network.type', 'gsm.sim.state', 'persist.sys.cloud.imeinum',
      'persist.sys.cloud.wifi.mac', 'ro.boot.pad_code', 'ro.boot.cluster_code',
      'ro.boot.armcloud_server_addr', 'ro.build.date', 'ro.build.version.release',
      'ro.debuggable', 'persist.sys.timezone', 'persist.sys.profiler_ms',
      'sys.usb.state', 'net.hostname'
    ];
    
    identityKeys.forEach(key => {
      if (keyProps[key]) {
        results.devices[device].properties[key] = keyProps[key];
        console.log(`  ${key}: ${keyProps[key]}`);
      }
    });
    
    results.devices[device].all_properties = keyProps;
  }
  
  // ===== PHASE 2: Container Escape Vectors =====
  console.log('\n[PHASE 2] Container Escape Capability Assessment');
  console.log('─'.repeat(70));
  
  for (const device of devices) {
    console.log(`\n◆ Device: ${device}`);
    
    const escapeChecks = [
      { name: 'Check /proc/cmdline', cmd: 'cat /proc/cmdline' },
      { name: 'Check /proc/self/cgroup', cmd: 'cat /proc/self/cgroup' },
      { name: 'Check /proc/mounts', cmd: 'cat /proc/mounts | head -10' },
      { name: 'SELinux Status', cmd: 'getenforce 2>/dev/null || echo SELINUX_DISABLED' },
      { name: 'Capabilities', cmd: 'grep Cap /proc/self/status 2>/dev/null || cat /proc/self/status | grep -i cap' },
      { name: 'eBPF Programs', cmd: 'bpftool prog list 2>/dev/null | head -5 || echo NO_BPFTOOL' },
      { name: 'Mount Namespaces', cmd: 'ls -la /proc/self/ns/ | head -10' },
      { name: 'Container Detection', cmd: 'ls -la /.dockerenv /proc/1/cgroup 2>&1 | grep -c "cannot access" || echo CONTAINER' }
    ];
    
    for (const check of escapeChecks) {
      const output = runAdbCommand(device, check.cmd, true);
      const preview = output.substring(0, 100).replace(/\n/g, ' | ');
      console.log(`  ✓ ${check.name}: ${preview}...`);
      results.devices[device].escape_capability[check.name] = output.substring(0, 500);
    }
  }
  
  // ===== PHASE 3: File System & Database Extraction =====
  console.log('\n[PHASE 3] File System & Database Extraction');
  console.log('─'.repeat(70));
  
  for (const device of devices) {
    console.log(`\n◆ Device: ${device}`);
    
    const dbPaths = [
      '/data/system/packages.xml',
      '/data/system/locksettings.db',
      '/data/system/accounts_ce.db/accounts_ce.db',
      '/data/system/accounts_de.db/accounts_de.db',
      '/data/data/com.android.chrome/app_chrome/Default/Cookies',
      '/data/data/com.android.chrome/app_chrome/Default/Web Data',
      '/data/data/com.google.android.gms',
      '/data/misc/user/0/gatekeeper.password.key',
      '/data/misc_ce/0/fingerprint',
      '/data/misc_ce/0/keystore:',
      '/data/misc_de/0/apnet'
    ];
    
    for (const dbPath of dbPaths) {
      const exists = runAdbCommand(device, `test -f "${dbPath}" && echo "EXISTS" || echo "NOT_FOUND"`);
      if (exists.includes('EXISTS')) {
        console.log(`  ✓ Found: ${dbPath}`);
        results.devices[device].extracted_data[dbPath] = 'EXISTS';
        results.devices[device].cloning_vectors.push(`Extract: ${dbPath}`);
      }
    }
  }
  
  // ===== PHASE 4: Network Configuration =====
  console.log('\n[PHASE 4] Network Configuration & Proxy Settings');
  console.log('─'.repeat(70));
  
  for (const device of devices) {
    console.log(`\n◆ Device: ${device}`);
    
    const netCmds = [
      { name: 'IP Configuration', cmd: 'ip addr show 2>/dev/null || ifconfig 2>/dev/null | head -20' },
      { name: 'Routing Table', cmd: 'ip route show 2>/dev/null || route -n 2>/dev/null | head -10' },
      { name: 'DNS Settings', cmd: 'getprop init.svc.adbd; getprop persist.sys.dns1; getprop persist.sys.dns2' },
      { name: 'WiFi Networks', cmd: 'cat /data/misc_ce/0/wifi/WifiConfigStore.xml 2>/dev/null | grep -i ssid || echo NO_WIFI' },
      { name: 'Proxy Config', cmd: 'getprop net.proxy 2>/dev/null; getprop net.http.proxy 2>/dev/null; getprop net.gprs.http 2>/dev/null' },
      { name: 'ARP Table', cmd: 'arp -a 2>/dev/null || ip neigh show 2>/dev/null' }
    ];
    
    for (const cmd of netCmds) {
      const output = runAdbCommand(device, cmd.cmd);
      const preview = output.substring(0, 150).replace(/\n/g, ' | ');
      console.log(`  ${cmd.name}: ${preview}`);
      results.devices[device].extracted_data[`net_${cmd.name}`] = output.substring(0, 1000);
    }
  }
  
  // ===== PHASE 5: App Inventory & Package Analysis =====
  console.log('\n[PHASE 5] App Inventory & Package Analysis');
  console.log('─'.repeat(70));
  
  for (const device of devices) {
    console.log(`\n◆ Device: ${device}`);
    
    const pkgOutput = runAdbCommand(device, 'pm list packages | wc -l');
    console.log(`  Total packages: ${pkgOutput.trim()}`);
    
    const sysApps = runAdbCommand(device, 'pm list packages -s | head -20');
    const systemCount = runAdbCommand(device, 'pm list packages -s | wc -l').trim();
    const userApps = runAdbCommand(device, 'pm list packages -3 | head -20');
    const userCount = runAdbCommand(device, 'pm list packages -3 | wc -l').trim();
    
    console.log(`  System apps: ${systemCount}`);
    console.log(`  User apps: ${userCount}`);
    
    results.devices[device].app_inventory = {
      system_count: systemCount,
      user_count: userCount,
      system_apps_sample: sysApps.substring(0, 500),
      user_apps_sample: userApps.substring(0, 500)
    };
    
    results.devices[device].cloning_vectors.push('Extract: Full APK list');
    results.devices[device].cloning_vectors.push('Extract: Package timestamps');
  }
  
  // ===== PHASE 6: Data & Media Extraction =====
  console.log('\n[PHASE 6] Data & Media Inventory');
  console.log('─'.repeat(70));
  
  for (const device of devices) {
    console.log(`\n◆ Device: ${device}`);
    
    const dataCmds = [
      { path: '/data/data', desc: 'App data' },
      { path: '/sdcard/DCIM', desc: 'Camera photos' },
      { path: '/sdcard/Pictures', desc: 'Pictures' },
      { path: '/sdcard/Documents', desc: 'Documents' },
      { path: '/sdcard/Download', desc: 'Downloads' }
    ];
    
    for (const item of dataCmds) {
      const fileCount = runAdbCommand(device, `find "${item.path}" -type f 2>/dev/null | wc -l || echo 0`);
      if (fileCount && fileCount !== '0') {
        console.log(`  ✓ ${item.desc}: ${fileCount.trim()} files`);
        results.devices[device].cloning_vectors.push(`Extract: ${item.desc}`);
      }
    }
  }
  
  // ===== PHASE 7: Neighbor Discovery via Network =====
  console.log('\n[PHASE 7] Neighbor Discovery');
  console.log('─'.repeat(70));
  
  for (const device of devices) {
    console.log(`\n◆ Device: ${device}`);
    
    // Try ARP scan
    const arpOutput = runAdbCommand(device, 'arp -a 2>/dev/null || ip neigh show 2>/dev/null | head -20');
    const neighbors = arpOutput.split('\n').filter(l => l && l.length > 10);
    
    if (neighbors.length > 0) {
      console.log(`  Found ${neighbors.length} ARP neighbors`);
      results.neighbors.push(...neighbors.map(n => ({ device, neighbor: n })));
    } else {
      console.log(`  No ARP neighbors found`);
    }
  }
  
  // ===== PHASE 8: Complete Cloning Vector Summary =====
  console.log('\n[PHASE 8] Complete Cloning Vector Summary');
  console.log('─'.repeat(70));
  
  for (const device of devices) {
    const vectorCount = results.devices[device].cloning_vectors.length;
    console.log(`\n◆ Device: ${device}`);
    console.log(`  Available cloning vectors: ${vectorCount}`);
    results.devices[device].cloning_vectors.forEach((v, i) => {
      if (i < 10) console.log(`    ${i+1}. ${v}`);
    });
    if (vectorCount > 10) {
      console.log(`    ... and ${vectorCount - 10} more`);
    }
  }
  
  // ===== Summary & Output =====
  results.summary = {
    devices_tested: devices.length,
    total_cloning_vectors: devices.reduce((sum, d) => sum + results.devices[d].cloning_vectors.length, 0),
    neighbors_discovered: results.neighbors.length,
    status: 'COMPLETE',
    execution_time: new Date().toISOString()
  };
  
  console.log('\n' + '═'.repeat(70));
  console.log('║' + ' '.repeat(68) + '║');
  console.log(`║ FULL SWEEP (ADB-BASED) COMPLETE                                  ║`);
  console.log(`║ Devices: ${devices.length} | Cloning Vectors: ${results.summary.total_cloning_vectors} | Neighbors: ${results.neighbors.length}                   ║`);
  console.log('║' + ' '.repeat(68) + '║');
  console.log('═'.repeat(70));
  
  // Save results
  fs.writeFileSync('full_sweep_results/FULL_SWEEP_ADB_EXTRACT.json', 
    JSON.stringify(results, null, 2));
  
  console.log('\n✓ Results saved to: full_sweep_results/FULL_SWEEP_ADB_EXTRACT.json');
  
  // Generate cloning report
  const cloningReport = {
    timestamp: results.timestamp,
    devices: {}
  };
  
  for (const device of devices) {
    cloningReport.devices[device] = {
      identity_properties: results.devices[device].properties,
      escape_status: Object.keys(results.devices[device].escape_capability).length,
      available_cloning_vectors: results.devices[device].cloning_vectors.length,
      vectors: results.devices[device].cloning_vectors
    };
  }
  
  fs.writeFileSync('full_sweep_results/CLONING_VECTORS_REPORT.json', 
    JSON.stringify(cloningReport, null, 2));
  
  console.log('✓ Cloning vectors report saved to: full_sweep_results/CLONING_VECTORS_REPORT.json');
}

main().then(() => {
  console.log('\n[✓] ADB extraction completed successfully');
  process.exit(0);
}).catch(err => {
  console.error('ERROR:', err);
  process.exit(1);
});
