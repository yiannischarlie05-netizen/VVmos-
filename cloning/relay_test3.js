const { spawn, execSync } = require('child_process');
const fs = require('fs');

const D1 = 'localhost:8479';
const D1_IP = '10.0.96.174';
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

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function test() {
  // Ensure cnxn.bin
  fs.writeFileSync('/tmp/adb_cnxn.bin',
    Buffer.from('434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex'));
  execSync(`adb -s ${D1} push /tmp/adb_cnxn.bin /sdcard/cnxn.bin 2>/dev/null`);

  // Push a combined trigger script to D1 that does BOTH listener + sender
  // This avoids the two-session issue — everything runs in ONE adb shell
  const PORT = 34000;
  
  // Command .220 will run: echo test data → nc to D1
  const cmd220 = `echo RELAY_WORKS_$(date +%s) | nc -w 10 ${D1_IP} ${PORT}`;
  const open = buildOpen(cmd220);
  fs.writeFileSync('/tmp/open_test.bin', open);
  execSync(`adb -s ${D1} push /tmp/open_test.bin /sdcard/open_relay.bin 2>/dev/null`);

  // Script runs on D1 in a SINGLE session using nohup for background processes
  const d1Script = `#!/system/bin/sh
# Clean up
rm -f /sdcard/recv_relay.bin

# Start listener with nohup so it survives
nohup sh -c 'nc -l -p ${PORT} > /sdcard/recv_relay.bin' &
LPID=$!
sleep 2

# Trigger .220 — also nohup'd
nohup sh -c '(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_relay.bin; sleep 10) | nc -w 13 ${SRC} 5555 > /dev/null 2>&1' &
TPID=$!

# Wait for listener to finish (it exits when sender disconnects)
wait $LPID 2>/dev/null
sleep 1

# Report
echo SIZE=$(wc -c < /sdcard/recv_relay.bin 2>/dev/null || echo 0)
echo CONTENT=$(cat /sdcard/recv_relay.bin 2>/dev/null)
`;
  fs.writeFileSync('/tmp/d1_relay_test.sh', d1Script);
  execSync(`adb -s ${D1} push /tmp/d1_relay_test.sh /sdcard/relay_test.sh 2>/dev/null`);

  console.log('Running combined relay test...');
  
  // Run via spawn (not execSync) so we can set timeout
  const proc = spawn('adb', ['-s', D1, 'shell', 'sh /sdcard/relay_test.sh']);
  let out = '';
  proc.stdout.on('data', d => { out += d.toString(); process.stdout.write(d); });
  proc.stderr.on('data', d => { process.stderr.write(d); });
  
  await new Promise((resolve) => {
    const timer = setTimeout(() => { proc.kill(); resolve(); }, 30000);
    proc.on('close', () => { clearTimeout(timer); resolve(); });
  });
  
  console.log('\nFinal output:', out.trim());
}

test().catch(e => console.error(e));
