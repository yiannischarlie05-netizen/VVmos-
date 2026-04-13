const https = require('https');
const crypto = require('crypto');

// Config
const { AK, SK, HOST, SVC, CT } = require('../shared/vmos_api');
const SH = 'content-type;host;x-content-sha256;x-date';

function sign(b) {
  const xd = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  const sd = xd.slice(0, 8);
  const xs = crypto.createHash('sha256').update(b, 'utf8').digest('hex');
  const can = [`host:${HOST}`, `x-date:${xd}`, `content-type:${CT}`, `signedHeaders:${SH}`, `x-content-sha256:${xs}`].join('\n');
  const hc = crypto.createHash('sha256').update(can, 'utf8').digest('hex');
  const sts = ['HMAC-SHA256', xd, `${sd}/${SVC}/request`, hc].join('\n');
  const kd = crypto.createHmac('sha256', Buffer.from(SK, 'utf8')).update(sd).digest();
  const ks = crypto.createHmac('sha256', kd).update(SVC).digest();
  const sk2 = crypto.createHmac('sha256', ks).update('request').digest();
  const sig = crypto.createHmac('sha256', sk2).update(sts).digest('hex');
  return { 'content-type': CT, 'x-date': xd, 'x-host': HOST, 'authorization': `HMAC-SHA256 Credential=${AK}, SignedHeaders=${SH}, Signature=${sig}` };
}

function apiPost(p, d, t) {
  return new Promise(ok => {
    const b = JSON.stringify(d || {});
    const h = sign(b);
    const buf = Buffer.from(b, 'utf8');
    const req = https.request({ hostname: HOST, path: p, method: 'POST', headers: { ...h, 'content-length': buf.length }, timeout: (t || 30) * 1000 }, res => {
      let r = ''; res.on('data', c => r += c);
      res.on('end', () => { try { ok(JSON.parse(r)); } catch { ok({ code: -1, raw: r.slice(0, 500) }); } });
    });
    req.on('timeout', () => { req.destroy(); ok({ code: -99 }); });
    req.on('error', () => ok({ code: -99 }));
    req.write(buf); req.end();
  });
}

async function relay(cmd) {
  const r = await apiPost('/vcpcloud/api/padApi/syncCmd', { padCode: 'ACP250923JS861KJ', scriptContent: cmd });
  if (r.code !== 200) return { ok: false, out: `[API ${r.code}: ${r.msg || ''}]` };
  const it = (Array.isArray(r.data) ? r.data : [r.data])[0] || {};
  return { ok: it.taskStatus === 3, out: (it.errorMsg || it.taskResult || '').trim() };
}

async function analyzeAgent() {
  console.log('=== ANALYZING LOCAL AGENT ===');
  
  // Check agent binary for protocol hints
  const strings = await relay('strings /data/local/oicq/webrtc/webrtc | grep -iE "http|port|8779|protocol|api|endpoint" | head -20');
  console.log('Agent strings:');
  console.log(strings.out);
  
  // Check what's actually listening on 8779
  const netstat = await relay('netstat -tlnp 2>/dev/null | grep 8779');
  console.log('\nNetstat 8779:');
  console.log(netstat.out);
  
  // Try to connect with telnet/netcat
  console.log('\n=== RAW TCP TEST ===');
  const raw = await relay('echo -e "GET / HTTP/1.0\\r\\n\\r\\n" | nc -w3 127.0.0.1 8779 2>&1 | head -10');
  console.log('Raw TCP response:');
  console.log(raw.out);
  
  // Check if it's a WebSocket server
  const ws = await relay('echo -e "GET / HTTP/1.1\\r\\nUpgrade: websocket\\r\\nConnection: Upgrade\\r\\n\\r\\n" | nc -w3 127.0.0.1 8779 2>&1 | head -10');
  console.log('\nWebSocket test:');
  console.log(ws.out);
  
  // Check the agent config
  console.log('\n=== AGENT CONFIG ===');
  const config = await relay('cat /data/local/oicq/webrtc/conf/conf.json');
  console.log(config.out);
  
  // Try to find how the VMOS Cloud communicates with the agent
  console.log('\n=== FIND VMOS-AGENT COMMUNICATION ===');
  const comm = await relay('ps aux | grep -i "webrtc\\|armcloud\\|agent" | head -10');
  console.log(comm.out);
}

analyzeAgent().catch(console.error);
