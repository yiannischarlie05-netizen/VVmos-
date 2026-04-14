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

async function test() {
  console.log('Testing basic relay...');
  const r1 = await relay('echo "TEST"');
  console.log('Basic relay ok:', r1.ok, 'out:', r1.out);
  
  console.log('\nTesting NATS monitor...');
  const r2 = await relay('curl -s "http://192.168.200.51:8222/connz?limit=10" 2>/dev/null');
  console.log('NATS monitor ok:', r2.ok, 'len:', r2.out.length);
  console.log('First 200 chars:', r2.out.slice(0, 200));
  
  if (!r2.ok) {
    console.log('\nTrying alternative...');
    const r3 = await relay('wget -qO- "http://192.168.200.51:8222/connz?limit=10" 2>/dev/null');
    console.log('WGET ok:', r3.ok, 'len:', r3.out.length);
  }
}

test().catch(console.error);
