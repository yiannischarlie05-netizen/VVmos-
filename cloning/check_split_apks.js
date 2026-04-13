const fs = require('fs');
const { execSync } = require('child_process');

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

function run220(cmd) {
  const open = buildOpen(cmd);
  fs.writeFileSync('/tmp/adb_open_tmp.bin', open);
  execSync('adb -s localhost:8479 push /tmp/adb_open_tmp.bin /sdcard/open_tmp.bin 2>/dev/null');
  
  // Write the shell command to a script file on D1
  const shellScript = '(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_tmp.bin; sleep 4) | nc -w 6 10.0.26.220 5555 2>/dev/null | strings';
  fs.writeFileSync('/tmp/d1_run.sh', shellScript);
  execSync('adb -s localhost:8479 push /tmp/d1_run.sh /sdcard/run.sh 2>/dev/null');
  
  try {
    const raw = execSync('adb -s localhost:8479 shell sh /sdcard/run.sh', {
      timeout: 15000, encoding: 'utf8', maxBuffer: 5 * 1024 * 1024
    });
    return raw.split('\n').filter(l => !l.match(/^(CNXN|OKAY|WRTE|CLSE|device::)/)).join('\n').trim();
  } catch (e) { return 'ERR: ' + e.message.slice(0, 100); }
}

// Check split APKs for yandex bank
const dir = '/data/app/~~0hnfvBzhxnhpDuHI9cY30Q==/com.yandex.bank-r0hzstC_hD8aKHipTzfq_g==/';
console.log('=== Yandex Bank APK dir ===');
console.log(run220('ls -la ' + dir));
console.log('\n=== Total size ===');
console.log(run220('du -sh ' + dir));
console.log('\n=== pm dump short ===');
console.log(run220('pm dump com.yandex.bank 2>/dev/null | grep -E "codePath|split|apk" | head -20'));
