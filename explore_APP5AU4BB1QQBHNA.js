#!/usr/bin/env node
/**
 * Direct shell exploration of device APP5AU4BB1QQBHNA
 * Expert-level device analysis and container escape testing
 */

const { AK, SK, HOST, SVC, CT, SHD, hmacSign, api, sh, P } = require('./shared/vmos_api');

const PAD = 'APP5AU4BB1QQBHNA';

async function run(cmd, timeout = 30) {
  const result = await sh(PAD, cmd, timeout);
  return result;
}

async function main() {
  console.log('═'.repeat(70));
  console.log(`  DEVICE EXPLORATION: ${PAD}`);
  console.log('═'.repeat(70));

  // ─── 1. Basic device info ─────────────────────────────────────────────
  console.log('\n▶ 1. BASIC DEVICE INFO');
  const basic = await run('uname -a && getprop ro.build.version.release');
  console.log(basic);

  // ─── 2. User and process context ───────────────────────────────────────
  console.log('\n▶ 2. USER & PROCESS CONTEXT');
  const context = await run('id && ps -o user,pid,comm --no-headers | head -20');
  console.log(context);

  // ─── 3. Container boundaries ───────────────────────────────────────────
  console.log('\n▶ 3. CONTAINER BOUNDARIES');
  const cgroups = await run('cat /proc/1/cgroup | head -10');
  console.log(cgroups);

  // ─── 4. Host access vectors ───────────────────────────────────────────
  console.log('\n▶ 4. HOST ACCESS VECTORS');
  const nsenter = await run('which nsenter && nsenter --version 2>&1 || echo "no nsenter"');
  console.log(nsenter);

  // ─── 5. Filesystem structure ─────────────────────────────────────────
  console.log('\n▶ 5. FILESYSTEM STRUCTURE');
  const fsinfo = await run('df -h && mount | grep -E "(overlay|dm-|/proc)" | head -15');
  console.log(fsinfo);

  // ─── 6. Android 15 system image location ───────────────────────────────
  console.log('\n▶ 6. ANDROID SYSTEM IMAGE');
  const systemImg = await run('ls -la /system/ 2>/dev/null | head -20 || ls -la / 2>/dev/null | head -20');
  console.log(systemImg);

  // ─── 7. Device identity ──────────────────────────────────────────────
  console.log('\n▶ 7. DEVICE IDENTITY');
  const identity = await run('getprop ro.product.model && getprop ro.serialno && getprop ro.build.id');
  console.log(identity);

  // ─── 8. Network info ────────────────────────────────────────────────────
  console.log('\n▶ 8. NETWORK INFO');
  const network = await run('ip addr show && ip route show 2>/dev/null || ifconfig 2>/dev/null');
  console.log(network);

  console.log('\n' + '═'.repeat(70));
  console.log('  INITIAL SCAN COMPLETE');
  console.log('═'.repeat(70));
}

main().catch(console.error);
