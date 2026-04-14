#!/usr/bin/env node
/**
 * ADB protocol stream client: connect to .220 via D1's ADB tunnel
 * with full WRTE/OKAY flow control for large file transfers.
 * 
 * Chain: local TCP → D1 ADB (localhost:8479) → exec:nc .220 5555 → .220 ADB
 */
const net = require('net');
const fs = require('fs');
const path = require('path');

const D1_ADB_PORT = 8479;
const SRC_IP = '10.0.26.220';

// ADB protocol constants
const A_CNXN = 0x4e584e43;
const A_OPEN = 0x4e45504f;
const A_OKAY = 0x59414b4f;
const A_WRTE = 0x45545257;
const A_CLSE = 0x45534c43;
const MAX_PAYLOAD = 4096;

function makeHeader(cmd, arg0, arg1, dataLen, dataCrc) {
  const h = Buffer.alloc(24);
  h.writeUInt32LE(cmd, 0);
  h.writeUInt32LE(arg0, 4);
  h.writeUInt32LE(arg1, 8);
  h.writeUInt32LE(dataLen, 12);
  h.writeUInt32LE(dataCrc, 16);
  h.writeUInt32LE((cmd ^ 0xFFFFFFFF) >>> 0, 20);
  return h;
}

function crc(data) {
  let s = 0;
  for (let i = 0; i < data.length; i++) s += data[i];
  return s >>> 0;
}

function makeCnxn() {
  const payload = Buffer.from('host::\x00');
  return Buffer.concat([
    makeHeader(A_CNXN, 0x01000000, MAX_PAYLOAD, payload.length, crc(payload)),
    payload
  ]);
}

function makeOpen(localId, service) {
  const payload = Buffer.from(service + '\x00');
  return Buffer.concat([
    makeHeader(A_OPEN, localId, 0, payload.length, crc(payload)),
    payload
  ]);
}

function makeOkay(localId, remoteId) {
  return makeHeader(A_OKAY, localId, remoteId, 0, 0);
}

function makeWrte(localId, remoteId, data) {
  return Buffer.concat([
    makeHeader(A_WRTE, localId, remoteId, data.length, crc(data)),
    data
  ]);
}

// Parse ADB packets from a buffer
function parsePackets(buf) {
  const packets = [];
  let offset = 0;
  while (offset + 24 <= buf.length) {
    const cmd = buf.readUInt32LE(offset);
    const arg0 = buf.readUInt32LE(offset + 4);
    const arg1 = buf.readUInt32LE(offset + 8);
    const dataLen = buf.readUInt32LE(offset + 12);
    // const dataCrc = buf.readUInt32LE(offset + 16);
    // const magic = buf.readUInt32LE(offset + 20);

    if (offset + 24 + dataLen > buf.length) break; // incomplete packet

    const data = buf.slice(offset + 24, offset + 24 + dataLen);
    packets.push({ cmd, arg0, arg1, data });
    offset += 24 + dataLen;
  }
  return { packets, remaining: buf.slice(offset) };
}

const cmdName = c => ({
  [A_CNXN]: 'CNXN', [A_OPEN]: 'OPEN', [A_OKAY]: 'OKAY',
  [A_WRTE]: 'WRTE', [A_CLSE]: 'CLSE'
}[c] || `0x${c.toString(16)}`);

// ═══════════════════════════════════════════════════════════════
// ADB Client for D1
// ═══════════════════════════════════════════════════════════════
class AdbClient {
  constructor(port) {
    this.port = port;
    this.sock = null;
    this.buf = Buffer.alloc(0);
    this.localIdCounter = 1;
    this.streams = {}; // localId -> { remoteId, data, resolve, reject }
    this.connected = false;
    this.connResolve = null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.connResolve = resolve;
      this.sock = net.createConnection(this.port, '127.0.0.1', () => {
        this.sock.write(makeCnxn());
      });
      this.sock.on('data', d => this.onData(d));
      this.sock.on('error', e => {
        if (this.connResolve) { this.connResolve = null; reject(e); }
      });
      this.sock.on('close', () => {
        for (const s of Object.values(this.streams)) {
          if (s.resolve) s.resolve(s.data);
        }
      });
      setTimeout(() => {
        if (!this.connected) reject(new Error('connect timeout'));
      }, 10000);
    });
  }

  onData(chunk) {
    this.buf = Buffer.concat([this.buf, chunk]);
    const { packets, remaining } = parsePackets(this.buf);
    this.buf = remaining;

    for (const pkt of packets) {
      if (pkt.cmd === A_CNXN) {
        this.connected = true;
        if (this.connResolve) { this.connResolve(); this.connResolve = null; }
      } else if (pkt.cmd === A_OKAY) {
        const stream = this.findStreamByLocal(pkt.arg1);
        if (stream && !stream.remoteId) {
          stream.remoteId = pkt.arg0;
        }
      } else if (pkt.cmd === A_WRTE) {
        const stream = this.findStreamByLocal(pkt.arg1);
        if (stream) {
          stream.data = Buffer.concat([stream.data, pkt.data]);
          // Send OKAY to keep data flowing
          this.sock.write(makeOkay(pkt.arg1, pkt.arg0));
          if (stream.onData) stream.onData(pkt.data);
        }
      } else if (pkt.cmd === A_CLSE) {
        const stream = this.findStreamByLocal(pkt.arg1);
        if (stream) {
          stream.closed = true;
          if (stream.resolve) { stream.resolve(stream.data); stream.resolve = null; }
        }
      }
    }
  }

  findStreamByLocal(localId) {
    return this.streams[localId];
  }

  // Open a stream and collect all data until CLSE
  openAndCollect(service, timeout) {
    const localId = this.localIdCounter++;
    return new Promise((resolve, reject) => {
      const stream = {
        localId, remoteId: null, data: Buffer.alloc(0),
        resolve, reject, closed: false, onData: null,
      };
      this.streams[localId] = stream;
      this.sock.write(makeOpen(localId, service));
      if (timeout) {
        setTimeout(() => {
          if (!stream.closed) {
            stream.closed = true;
            resolve(stream.data);
          }
        }, timeout);
      }
    });
  }

  // Open a stream with a data callback for streaming
  openStream(service) {
    const localId = this.localIdCounter++;
    const stream = {
      localId, remoteId: null, data: Buffer.alloc(0),
      resolve: null, reject: null, closed: false, onData: null,
    };
    this.streams[localId] = stream;
    this.sock.write(makeOpen(localId, service));
    return {
      localId,
      onData: (cb) => { stream.onData = cb; },
      write: (data) => {
        if (stream.remoteId) {
          this.sock.write(makeWrte(localId, stream.remoteId, data));
        }
      },
      waitClose: (timeout) => new Promise(resolve => {
        stream.resolve = () => resolve(stream.data);
        if (timeout) setTimeout(() => {
          if (!stream.closed) { stream.closed = true; resolve(stream.data); }
        }, timeout);
      }),
      getData: () => stream.data,
    };
  }

  close() {
    if (this.sock) this.sock.destroy();
  }
}

// ═══════════════════════════════════════════════════════════════
// Main: Test the chain
// ═══════════════════════════════════════════════════════════════
async function main() {
  const log = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);

  // Step 1: Connect to D1's ADB
  log('Connecting to D1 ADB...');
  const d1 = new AdbClient(D1_ADB_PORT);
  await d1.connect();
  log('D1 connected');

  // Step 2: Test basic exec on D1
  log('Test: exec on D1...');
  const testData = await d1.openAndCollect('exec:echo D1_EXEC_OK', 5000);
  log(`D1 exec result: "${testData.toString().trim()}"`);

  // Step 3: Open nc tunnel to .220 via D1
  log('Opening nc tunnel to .220 via D1...');
  const tunnel = d1.openStream(`exec:nc ${SRC_IP} 5555`);

  // Wait for OKAY (tunnel opened)
  await new Promise(r => setTimeout(r, 1000));

  // Step 4: Send CNXN to .220 through the tunnel
  log('Sending CNXN to .220...');
  tunnel.write(makeCnxn());

  // Step 5: Collect .220's response through the tunnel
  // The tunnel's onData will receive raw bytes from .220's ADB
  let tunnelBuf = Buffer.alloc(0);
  let src220Connected = false;

  tunnel.onData((chunk) => {
    tunnelBuf = Buffer.concat([tunnelBuf, chunk]);
    // Try to parse .220's ADB packets
    const { packets, remaining } = parsePackets(tunnelBuf);
    tunnelBuf = remaining;

    for (const pkt of packets) {
      if (pkt.cmd === A_CNXN) {
        log(`.220 CNXN: ${pkt.data.toString().slice(0, 60)}`);
        src220Connected = true;
      }
    }
  });

  // Wait for .220's CNXN
  await new Promise(r => setTimeout(r, 3000));

  if (!src220Connected) {
    log('.220 did not respond to CNXN');
    d1.close();
    return;
  }

  // Step 6: Test echo first
  log('Test: echo on .220...');
  const shellCmd = 'shell:echo HELLO_FROM_220_STREAM\x00';
  const shellPayload = Buffer.from(shellCmd);
  const openPkt = Buffer.concat([
    makeHeader(A_OPEN, 100, 0, shellPayload.length, crc(shellPayload)),
    shellPayload
  ]);
  tunnel.write(openPkt);

  // Collect .220's response (OKAY + WRTE data + CLSE)
  let fileData = Buffer.alloc(0);
  let src220RemoteId = null;
  let fileDone = false;

  // Replace the onData handler
  tunnel.onData((chunk) => {
    tunnelBuf = Buffer.concat([tunnelBuf, chunk]);
    const { packets, remaining } = parsePackets(tunnelBuf);
    tunnelBuf = remaining;

    for (const pkt of packets) {
      const name = cmdName(pkt.cmd);
      if (pkt.cmd === A_OKAY) {
        src220RemoteId = pkt.arg0;
        log(`.220 OKAY: remoteId=${src220RemoteId}`);
      } else if (pkt.cmd === A_WRTE && pkt.arg1 === 100) {
        fileData = Buffer.concat([fileData, pkt.data]);
        // Send OKAY to .220 through the tunnel to keep data flowing
        const okayPkt = makeOkay(100, src220RemoteId);
        tunnel.write(okayPkt);
      } else if (pkt.cmd === A_CLSE) {
        fileDone = true;
        log(`.220 CLSE: file transfer done, ${fileData.length} bytes`);
      } else {
        log(`.220 ${name}: arg0=${pkt.arg0} arg1=${pkt.arg1} len=${pkt.data.length}`);
      }
    }
  });

  // Wait for file transfer to complete
  for (let i = 0; i < 30 && !fileDone; i++) {
    await new Promise(r => setTimeout(r, 1000));
    if (i % 5 === 4) log(`  ... ${fileData.length} bytes so far`);
  }

  log(`\nFile data: ${fileData.length} bytes`);
  if (fileData.length > 0) {
    log(`Preview: ${fileData.toString('utf8').slice(0, 200)}`);
  }

  // Step 7: If build.prop works, try an APK
  if (fileData.length > 100) {
    log('\n═══ Small file worked! Now trying APK... ═══');

    const apkPath = '/data/app/~~Wxk7-55Bxuh7YZnn2ZFEiA==/com.app.trademo-5zyYOz2-ozsLRT0GbiAuSQ==/base.apk';
    const apkCmd = `shell:cat "${apkPath}" 2>/dev/null\x00`;
    const apkPayload = Buffer.from(apkCmd);
    const apkOpenPkt = Buffer.concat([
      makeHeader(A_OPEN, 200, 0, apkPayload.length, crc(apkPayload)),
      apkPayload
    ]);

    let apkData = Buffer.alloc(0);
    let apkRemoteId = null;
    let apkDone = false;

    tunnel.onData((chunk) => {
      tunnelBuf = Buffer.concat([tunnelBuf, chunk]);
      const { packets, remaining } = parsePackets(tunnelBuf);
      tunnelBuf = remaining;

      for (const pkt of packets) {
        if (pkt.cmd === A_OKAY && pkt.arg1 === 200) {
          apkRemoteId = pkt.arg0;
        } else if (pkt.cmd === A_WRTE && pkt.arg1 === 200) {
          apkData = Buffer.concat([apkData, pkt.data]);
          tunnel.write(makeOkay(200, apkRemoteId));
        } else if (pkt.cmd === A_CLSE && pkt.arg1 === 200) {
          apkDone = true;
        }
      }
    });

    tunnel.write(apkOpenPkt);

    // Wait up to 120 seconds for APK transfer
    for (let i = 0; i < 120 && !apkDone; i++) {
      await new Promise(r => setTimeout(r, 1000));
      if (i % 10 === 9) log(`  APK: ${(apkData.length / 1024 / 1024).toFixed(1)} MB...`);
    }

    log(`APK data: ${(apkData.length / 1024 / 1024).toFixed(1)} MB`);

    if (apkData.length > 100000) {
      const outFile = '/tmp/trademo_test.apk';
      fs.writeFileSync(outFile, apkData);
      log(`Saved to ${outFile}`);
      // Quick install test
      try {
        const r = require('child_process').execSync(
          `adb -s localhost:7391 install -r -g "${outFile}" 2>&1`, {
          timeout: 60000, encoding: 'utf8'
        });
        log(`Install: ${r.trim()}`);
      } catch (e) { log(`Install err: ${(e.stdout || e.message).slice(0, 80)}`); }
    }
  }

  d1.close();
  log('Done');
}

main().catch(e => console.error('FATAL:', e.message));
