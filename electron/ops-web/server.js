/**
 * VMOS Titan Ops-Web — Localhost Operations Server
 *
 * Standalone Node.js HTTP server (zero external deps) that proxies to VMOS Cloud API
 * and serves a full operations dashboard at http://localhost:3000
 *
 * Features:
 *   - VMOS Cloud API proxy with HMAC-SHA256 signing
 *   - Instance management (list, restart, reset, screenshot, shell)
 *   - Genesis pipeline trigger + status polling
 *   - Device property inspection & modification
 *   - Real-time log streaming
 *   - Proxy configuration
 *   - Full dashboard UI
 */

'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

// ─── Config ────────────────────────────────────────────────────────
const PORT = parseInt(process.env.OPS_PORT || '3000', 10);
const VERBOSE = process.argv.includes('--verbose');

// Load credentials from parent .env or env vars
function loadEnv() {
  const envPaths = [
    path.join(__dirname, '..', '..', '.env'),           // /opt/titan-v13-device/.env
    path.join(__dirname, '..', '.env'),                  // vmos-titan/.env
    '/opt/titan-v13-device/.env',
  ];
  const vars = {};
  for (const p of envPaths) {
    try {
      if (!fs.existsSync(p)) continue;
      for (const line of fs.readFileSync(p, 'utf-8').split('\n')) {
        const l = line.trim();
        if (!l || l.startsWith('#')) continue;
        const eq = l.indexOf('=');
        if (eq < 1) continue;
        const k = l.slice(0, eq).trim();
        let v = l.slice(eq + 1).trim();
        if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'")))
          v = v.slice(1, -1);
        vars[k] = v;
      }
      if (VERBOSE) console.log(`[env] Loaded ${p}`);
      break;
    } catch (_) {}
  }
  return vars;
}

const BACKEND_PORT = parseInt(process.env.TITAN_BACKEND_PORT || '8080', 10);
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

// Sync credentials from .env to FastAPI backend on startup
function syncCredentials() {
  const envVars = loadEnv();
  const ak = process.env.VMOS_CLOUD_AK || envVars.VMOS_CLOUD_AK || '';
  const sk = process.env.VMOS_CLOUD_SK || envVars.VMOS_CLOUD_SK || '';
  if (!ak || !sk) { console.log('[ops-web] No VMOS credentials found — skipping sync'); return; }
  const payload = JSON.stringify({ ak, sk });
  const req = http.request({
    hostname: '127.0.0.1', port: BACKEND_PORT,
    path: '/api/vmos/credentials', method: 'POST',
    headers: { 'Content-Type': 'application/json', 'content-length': Buffer.byteLength(payload) },
    timeout: 10000,
  }, res => {
    let raw = '';
    res.on('data', c => raw += c);
    res.on('end', () => console.log('[ops-web] Credentials synced to backend'));
  });
  req.on('error', () => console.log('[ops-web] Backend not ready — credentials will sync when available'));
  req.write(payload);
  req.end();
}

// Map ops-web API paths to FastAPI backend paths
function mapApiPath(pathname) {
  // Ops-web uses /api/instances, FastAPI uses /api/vmos/instances
  if (pathname.startsWith('/api/instances')) return '/api/vmos' + pathname.slice(4);
  if (pathname.startsWith('/api/apps/')) return '/api/vmos/apps' + pathname.slice(9);
  if (pathname.startsWith('/api/batch/')) return '/api/vmos/' + pathname.slice(11);
  if (pathname === '/api/models') return '/api/vmos/extended/batch-model-info';
  if (pathname === '/api/adi-templates') return '/api/vmos/extended/adi-templates';
  if (pathname === '/api/smart-ip') return '/api/vmos/extended/smart-ip';
  if (pathname === '/api/check-ip') return '/api/vmos/extended/check-ip';
  if (pathname === '/api/android-props') return '/api/vmos/extended/update-android-prop';
  if (pathname.startsWith('/api/genesis/')) return '/api/unified-genesis' + pathname.slice(12);
  if (pathname.startsWith('/api/task/')) return '/api/vmos/extended/task-detail';
  // Default: pass through as-is
  return pathname;
}

// Proxy API request to FastAPI backend
function handleAPI(pathname, method, body, res) {
  // Local health check
  if (pathname === '/api/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', version: '3.0.0', mode: 'ops-web-proxy', backend: BACKEND_URL, uptime: process.uptime() | 0 }));
    return;
  }

  const backendPath = mapApiPath(pathname);
  const bodyBuf = Buffer.from(body || '', 'utf8');

  const proxyReq = http.request({
    hostname: '127.0.0.1',
    port: BACKEND_PORT,
    path: backendPath,
    method: method,
    headers: {
      'Content-Type': 'application/json',
      'content-length': bodyBuf.length,
    },
    timeout: 120000,
  }, proxyRes => {
    const h = { ...proxyRes.headers };
    h['access-control-allow-origin'] = '*';
    res.writeHead(proxyRes.statusCode, h);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', err => {
    if (err.code === 'ECONNREFUSED') {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'FastAPI backend not running', detail: `Connection to ${BACKEND_URL} refused` }));
    } else {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
  });

  proxyReq.on('timeout', () => {
    proxyReq.destroy();
    res.writeHead(504, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Backend request timeout' }));
  });

  if (bodyBuf.length > 0) proxyReq.write(bodyBuf);
  proxyReq.end();
}
// ─── Static File Server ────────────────────────────────────────────
const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon', '.woff2': 'font/woff2',
};

function serveStatic(pathname, res) {
  let filePath = pathname === '/' ? '/index.html' : pathname;
  filePath = path.join(__dirname, filePath);

  // Security: prevent path traversal
  if (!filePath.startsWith(__dirname)) {
    res.writeHead(403); res.end('Forbidden'); return;
  }

  const ext = path.extname(filePath);
  const mime = MIME[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not Found'); return; }
    res.writeHead(200, { 'Content-Type': mime, 'Cache-Control': 'no-cache' });
    res.end(data);
  });
}

// ─── HTTP Server ──────────────────────────────────────────────────
const server = http.createServer(async (req, res) => {
  const urlObj = new URL(req.url, `http://localhost:${PORT}`);
  const pathname = urlObj.pathname;
  const method = req.method;

  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');
  if (method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  // API routes
  if (pathname.startsWith('/api/')) {
    let body = '';
    await new Promise((resolve, reject) => {
      let size = 0;
      req.on('data', c => { size += c.length; if (size > 65536) { req.destroy(); return reject(); } body += c; });
      req.on('end', resolve);
      req.on('error', reject);
    }).catch(() => {});
    if (res.writableEnded) return;
    return handleAPI(pathname, method, body, res);
  }

  // Static files
  serveStatic(pathname, res);
});

server.listen(PORT, '127.0.0.1', () => {
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  VMOS Titan Ops-Web v3.0 (FastAPI proxy mode)');
  console.log(`  Running at http://localhost:${PORT}`);
  console.log(`  Backend:    ${BACKEND_URL}`);
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  // Sync credentials to backend after brief delay
  setTimeout(syncCredentials, 2000);
});


