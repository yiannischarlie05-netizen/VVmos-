#!/usr/bin/env node
/**
 * Shared VMOS Cloud API Helper
 * 
 * Provides HMAC-SHA256 signed API calls to VMOS Cloud.
 * Reads credentials from ../.env file.
 * 
 * Usage:
 *   const { AK, SK, HOST, D1, D2, api, sh, syncCmd, hmacSign } = require('../shared/vmos_api');
 */

const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// ─── Load .env ───────────────────────────────────────────────────────────────
function loadEnv() {
  const envPath = path.join(__dirname, '..', '.env');
  const vars = {};
  if (fs.existsSync(envPath)) {
    for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eq = trimmed.indexOf('=');
      if (eq > 0) {
        vars[trimmed.slice(0, eq).trim()] = trimmed.slice(eq + 1).trim();
      }
    }
  }
  return vars;
}

const ENV = loadEnv();

const AK  = process.env.VMOS_AK  || ENV.VMOS_AK  || '';
const SK  = process.env.VMOS_SK  || ENV.VMOS_SK  || '';
const HOST = process.env.VMOS_HOST || ENV.VMOS_HOST || 'api.vmoscloud.com';
const SVC  = process.env.VMOS_SVC  || ENV.VMOS_SVC  || 'armcloud-paas';
const D1  = process.env.VMOS_D1  || ENV.VMOS_D1  || '';
const D2  = process.env.VMOS_D2  || ENV.VMOS_D2  || '';

const CT  = 'application/json;charset=UTF-8';
const SHD = 'content-type;host;x-content-sha256;x-date';

// ─── HMAC Signing ────────────────────────────────────────────────────────────
function hmacSign(body, opts) {
  const ak = (opts && opts.ak) || AK;
  const sk = (opts && opts.sk) || SK;
  const host = (opts && opts.host) || HOST;
  const svc = (opts && opts.svc) || SVC;

  const xd = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  const sd = xd.slice(0, 8);
  const bh = crypto.createHash('sha256').update(body, 'utf8').digest('hex');
  const canonical = [
    `host:${host}`,
    `x-date:${xd}`,
    `content-type:${CT}`,
    `signedHeaders:${SHD}`,
    `x-content-sha256:${bh}`
  ].join('\n');
  const ch = crypto.createHash('sha256').update(canonical, 'utf8').digest('hex');
  const sts = ['HMAC-SHA256', xd, `${sd}/${svc}/request`, ch].join('\n');
  let k = crypto.createHmac('sha256', sk).update(sd).digest();
  k = crypto.createHmac('sha256', k).update(svc).digest();
  k = crypto.createHmac('sha256', k).update('request').digest();
  const sig = crypto.createHmac('sha256', k).update(sts).digest('hex');
  return {
    'content-type': CT,
    'x-date': xd,
    'x-host': host,
    'authorization': `HMAC-SHA256 Credential=${ak}, SignedHeaders=${SHD}, Signature=${sig}`
  };
}

// ─── API POST ────────────────────────────────────────────────────────────────
function api(ep, data, timeout, opts) {
  return new Promise(ok => {
    const host = (opts && opts.host) || HOST;
    const b = JSON.stringify(data || {});
    const h = hmacSign(b, opts);
    const buf = Buffer.from(b);
    const req = https.request({
      hostname: host,
      path: ep,
      method: 'POST',
      headers: { ...h, 'content-length': buf.length },
      timeout: (timeout || 30) * 1000
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        try { ok(JSON.parse(d)); } catch { ok({ code: -1, raw: d.slice(0, 500) }); }
      });
    });
    req.on('timeout', () => { req.destroy(); ok({ code: -99, msg: 'timeout' }); });
    req.on('error', e => ok({ code: -99, msg: e.message }));
    req.write(buf);
    req.end();
  });
}

// ─── Shell command via syncCmd ───────────────────────────────────────────────
async function sh(pad, script, sec, opts) {
  const r = await api('/vcpcloud/api/padApi/syncCmd', { padCode: pad, scriptContent: script }, sec || 30, opts);
  if (r.code !== 200) return `[API_ERR:${r.code}]`;
  const it = (Array.isArray(r.data) ? r.data : [r.data])[0] || {};
  if (it.taskStatus === 3) return (it.errorMsg || it.taskResult || '').trim();
  return `[STATUS:${it.taskStatus}]`;
}

// Alias
const syncCmd = sh;

// ─── Logging helper ──────────────────────────────────────────────────────────
const P = m => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);

// ─── Exports ─────────────────────────────────────────────────────────────────
module.exports = {
  AK, SK, HOST, SVC, D1, D2,
  CT, SHD,
  hmacSign, api, sh, syncCmd, P,
  loadEnv, ENV,
};
