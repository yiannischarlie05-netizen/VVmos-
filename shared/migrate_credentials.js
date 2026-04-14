#!/usr/bin/env node
/**
 * Migration script: Replace hardcoded AK/SK/HOST credentials and 
 * duplicated hmacSign/api/sh functions with shared/vmos_api.js imports.
 * 
 * Run: node shared/migrate_credentials.js
 * 
 * What it does per file:
 * 1. Adds `const { AK, SK, HOST, SVC, D1, D2, CT, SHD, hmacSign, api, sh, P } = require('<relative>/shared/vmos_api');`
 * 2. Removes hardcoded credential lines (const AK=..., const SK=..., etc.)
 * 3. Removes duplicated function definitions (hmacSign, vmosSign, api, vmosPost, sh, syncCmd, run)
 * 4. Removes now-unused `require('https')` and `require('crypto')` if they were only used by the removed functions
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');

// Directories to process (only our reorganized ones + electron)
const DIRS = [
  'cloning', 'escape', 'neighbor', 'nats', 'sweep',
  'injection', 'scanning', 'adb', 'genesis', 'autonomous',
  'cctv', 'vmos_ops', 'tmp', 'electron'
];

// Patterns to remove (credential declarations)
const CRED_PATTERNS = [
  /^const AK\s*=\s*['"][^'"]+['"];?\s*$/,
  /^const SK\s*=\s*['"][^'"]+['"];?\s*$/,
  /^const HOST\s*=\s*['"][^'"]+['"];?\s*$/,
  /^const VMOS_HOST\s*=\s*['"][^'"]+['"];?\s*$/,
  /^const SVC\s*=\s*['"][^'"]+['"];?\s*$/,
  /^const VMOS_SERVICE\s*=\s*['"][^'"]+['"];?\s*$/,
  /^const CT\s*=\s*['"][^'"]+['"];?\s*$/,
  /^const VMOS_CT\s*=\s*['"][^'"]+['"];?\s*$/,
  /^const SHD\s*=\s*['"][^'"]+['"];?\s*$/,
  /^const VMOS_SH\s*=\s*['"][^'"]+['"];?\s*$/,
];

// Function definition patterns to remove (multi-line aware)
const FUNC_START_PATTERNS = [
  /^function hmacSign\s*\(/,
  /^function vmosSign\s*\(/,
  /^function api\s*\(/,
  /^function vmosPost\s*\(/,
  /^async function sh\s*\(/,
  /^async function syncCmd\s*\(/,
  /^async function run\s*\(/,
  /^const P\s*=\s*m\s*=>\s*console\.log/,
];

// One-liner function patterns (minified inline)
const ONELINER_PATTERNS = [
  /^function vmosSign\(.*\}$/,
  /^function vmosPost\(.*\}$/,
  /^async function run\(cmd.*\}$/,
];

let totalFiles = 0;
let modifiedFiles = 0;

function getRelativePath(fileDir) {
  const rel = path.relative(fileDir, path.join(ROOT, 'shared', 'vmos_api'));
  return rel.startsWith('.') ? rel : './' + rel;
}

function processFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  
  // Skip if no hardcoded AK
  if (!content.includes("const AK") && !content.includes("const AK ")) return false;
  
  const lines = content.split('\n');
  const newLines = [];
  let modified = false;
  let importAdded = false;
  let skipUntilCloseBrace = false;
  let braceDepth = 0;
  let removedHttps = false;
  let removedCrypto = false;
  let needsHttps = false;
  let needsCrypto = false;
  
  // First pass: check if https/crypto are used beyond the sign/api functions
  const withoutFunctions = content
    .replace(/function (hmacSign|vmosSign|api|vmosPost)\s*\([^]*?\n\}/g, '')
    .replace(/async function (sh|syncCmd|run)\s*\([^]*?\n\}/g, '');
  
  if (/https\.(request|get)/.test(withoutFunctions)) needsHttps = true;
  if (/crypto\.(createHash|createHmac|randomBytes)/.test(withoutFunctions)) needsCrypto = true;
  
  const fileDir = path.dirname(filePath);
  const relImport = getRelativePath(fileDir);
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    
    // Skip lines inside multi-line function removal
    if (skipUntilCloseBrace) {
      // Count braces
      for (const ch of line) {
        if (ch === '{') braceDepth++;
        if (ch === '}') braceDepth--;
      }
      if (braceDepth <= 0) {
        skipUntilCloseBrace = false;
        braceDepth = 0;
      }
      modified = true;
      continue;
    }
    
    // Check for credential lines to remove
    if (CRED_PATTERNS.some(p => p.test(trimmed))) {
      modified = true;
      
      // Add import line right before first credential removal
      if (!importAdded) {
        // Determine what to import based on what the file uses
        const uses = [];
        if (content.includes('AK')) uses.push('AK');
        if (content.includes('SK')) uses.push('SK');
        if (content.match(/\bHOST\b/) || content.match(/\bVMOS_HOST\b/)) uses.push('HOST');
        if (content.match(/\bSVC\b/) || content.match(/\bVMOS_SERVICE\b/)) uses.push('SVC');
        if (content.match(/\bD1\b/)) uses.push('D1');
        if (content.match(/\bD2\b/)) uses.push('D2');
        if (content.match(/\bCT\b/) || content.match(/\bVMOS_CT\b/)) uses.push('CT');
        if (content.match(/\bSHD\b/) || content.match(/\bVMOS_SH\b/)) uses.push('SHD');
        if (content.match(/\bhmacSign\b/) || content.match(/\bvmosSign\b/)) uses.push('hmacSign');
        if (content.match(/\bapi\b/) && content.match(/function api\b|vmosPost/)) uses.push('api');
        if (content.match(/\bsh\b/) && content.match(/async function sh\b|function run\b/)) uses.push('sh');
        if (content.match(/\bP\b/) && content.match(/const P\s*=/)) uses.push('P');
        
        // Deduplicate
        const uniqueUses = [...new Set(uses)];
        newLines.push(`const { ${uniqueUses.join(', ')} } = require('${relImport}');`);
        importAdded = true;
      }
      continue;
    }
    
    // Check for one-liner functions to remove
    if (ONELINER_PATTERNS.some(p => p.test(trimmed))) {
      modified = true;
      continue;
    }
    
    // Check for multi-line function definitions to remove
    if (FUNC_START_PATTERNS.some(p => p.test(trimmed))) {
      // Count braces on this line
      braceDepth = 0;
      for (const ch of line) {
        if (ch === '{') braceDepth++;
        if (ch === '}') braceDepth--;
      }
      if (braceDepth > 0) {
        skipUntilCloseBrace = true;
      }
      modified = true;
      continue;
    }
    
    // Remove unused requires
    if (trimmed === "const https = require('https');" && !needsHttps) {
      modified = true;
      continue;
    }
    if (trimmed === "const crypto = require('crypto');" && !needsCrypto) {
      modified = true;
      continue;
    }
    
    newLines.push(line);
  }
  
  if (modified) {
    // Clean up multiple consecutive blank lines
    let cleaned = newLines.join('\n').replace(/\n{3,}/g, '\n\n');
    fs.writeFileSync(filePath, cleaned);
    return true;
  }
  return false;
}

console.log('Migrating JS files to use shared/vmos_api.js...\n');

for (const dir of DIRS) {
  const dirPath = path.join(ROOT, dir);
  if (!fs.existsSync(dirPath)) continue;
  
  const files = fs.readdirSync(dirPath).filter(f => f.endsWith('.js'));
  for (const file of files) {
    const filePath = path.join(dirPath, file);
    totalFiles++;
    if (processFile(filePath)) {
      modifiedFiles++;
      console.log(`  ✓ ${dir}/${file}`);
    }
  }
}

console.log(`\nDone: ${modifiedFiles}/${totalFiles} JS files updated.`);
