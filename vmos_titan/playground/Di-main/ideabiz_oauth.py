#!/usr/bin/env python3
"""
IdeaBiz OAuth2 Token Manager — Production-Ready

Handles the full IdeaBiz (Dialog Axiata) OAuth2 lifecycle:
- Token generation via consumer_key + consumer_secret
- Automatic token refresh when expired
- Token persistence to avoid unnecessary regeneration
- Multi-credential support (try all configured creds)

Configuration via environment variables or config.json:
  IDEABIZ_CONSUMER_KEY / IDEABIZ_CONSUMER_SECRET
  IDEABIZ_USERNAME / IDEABIZ_PASSWORD  (for password grant)
  IDEABIZ_REFRESH_TOKEN (for refresh flow)

Based on official IdeaBiz API docs:
  https://docs.ideabiz.lk/Getting_Started/Token_Manegment/

Token endpoint: https://ideabiz.lk/apicall/token
  - grant_type=client_credentials (consumer key/secret only)
  - grant_type=password (consumer key/secret + username/password)
  - grant_type=refresh_token (refresh existing token)
"""

import os
import sys
import json
import time
import base64
import requests
from datetime import datetime, timedelta
from pathlib import Path

TOKEN_URL = "https://ideabiz.lk/apicall/token"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".token_cache.json")

class IdeaBizAuth:
    """IdeaBiz OAuth2 Token Manager"""
    
    def __init__(self, consumer_key=None, consumer_secret=None, 
                 username=None, password=None, refresh_token=None):
        self.consumer_key = consumer_key or os.environ.get("IDEABIZ_CONSUMER_KEY", "")
        self.consumer_secret = consumer_secret or os.environ.get("IDEABIZ_CONSUMER_SECRET", "")
        self.username = username or os.environ.get("IDEABIZ_USERNAME", "")
        self.password = password or os.environ.get("IDEABIZ_PASSWORD", "")
        self.refresh_token = refresh_token or os.environ.get("IDEABIZ_REFRESH_TOKEN", "")
        self.access_token = ""
        self.token_expiry = 0  # Unix timestamp
        
        # Try loading from config.json if env vars not set
        if not self.consumer_key:
            self._load_config()
        
        # Try loading cached token
        self._load_token_cache()
    
    def _load_config(self):
        """Load credentials from config.json"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                self.consumer_key = config.get("auth_consumerKey", config.get("consumer_key", ""))
                self.consumer_secret = config.get("auth_consumerSecret", config.get("consumer_secret", ""))
                self.username = config.get("username", "")
                self.password = config.get("password", "")
                self.refresh_token = config.get("refresh_token", "")
                if config.get("access_token"):
                    self.access_token = config["access_token"]
            except Exception:
                pass
    
    def _load_token_cache(self):
        """Load cached token to avoid regeneration"""
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, "r") as f:
                    cache = json.load(f)
                cached_token = cache.get("access_token", "")
                cached_expiry = cache.get("expiry", 0)
                cached_refresh = cache.get("refresh_token", "")
                
                if cached_token and cached_expiry > time.time() + 60:  # 60s buffer
                    self.access_token = cached_token
                    self.token_expiry = cached_expiry
                    if cached_refresh:
                        self.refresh_token = cached_refresh
            except Exception:
                pass
    
    def _save_token_cache(self):
        """Persist token to disk"""
        try:
            cache = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expiry": self.token_expiry,
                "generated_at": datetime.now().isoformat(),
            }
            with open(TOKEN_CACHE_FILE, "w") as f:
                json.dump(cache, f, indent=2)
        except Exception:
            pass
    
    def _basic_auth(self):
        """Generate Basic auth header from consumer key/secret"""
        if not self.consumer_key or not self.consumer_secret:
            return None
        return base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()
    
    def _request_token(self, grant_params):
        """Make OAuth2 token request"""
        basic = self._basic_auth()
        if not basic:
            return None
        
        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        try:
            resp = requests.post(TOKEN_URL, headers=headers, data=grant_params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("access_token", "")
                if data.get("refresh_token"):
                    self.refresh_token = data["refresh_token"]
                
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = time.time() + expires_in
                self._save_token_cache()
                
                return {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "expires_in": expires_in,
                    "token_type": data.get("token_type", "bearer"),
                    "scope": data.get("scope", ""),
                }
            else:
                error = resp.text[:300]
                return {"error": True, "status": resp.status_code, "detail": error}
        except Exception as e:
            return {"error": True, "detail": str(e)}
    
    def generate_token_client_credentials(self):
        """Generate token using client_credentials grant (simplest)"""
        return self._request_token("grant_type=client_credentials&scope=PRODUCTION")
    
    def generate_token_password(self):
        """Generate token using password grant (requires username/password)"""
        if not self.username or not self.password:
            return {"error": True, "detail": "Username/password not configured"}
        params = (
            f"grant_type=password"
            f"&username={requests.utils.quote(self.username)}"
            f"&password={requests.utils.quote(self.password)}"
            f"&scope=PRODUCTION"
        )
        return self._request_token(params)
    
    def refresh_access_token(self):
        """Refresh an expired token using refresh_token"""
        if not self.refresh_token:
            return {"error": True, "detail": "No refresh token available"}
        params = (
            f"grant_type=refresh_token"
            f"&refresh_token={requests.utils.quote(self.refresh_token)}"
            f"&scope=PRODUCTION"
        )
        return self._request_token(params)
    
    def get_valid_token(self):
        """Get a valid access token, refreshing/regenerating as needed"""
        # Check if current token is still valid
        if self.access_token and self.token_expiry > time.time() + 60:
            return self.access_token
        
        # Try refresh first (least privilege)
        if self.refresh_token:
            result = self.refresh_access_token()
            if result and not result.get("error"):
                return self.access_token
        
        # Try password grant
        if self.username and self.password:
            result = self.generate_token_password()
            if result and not result.get("error"):
                return self.access_token
        
        # Try client_credentials
        if self.consumer_key and self.consumer_secret:
            result = self.generate_token_client_credentials()
            if result and not result.get("error"):
                return self.access_token
        
        return None
    
    def get_bearer_header(self):
        """Get Authorization header dict with valid Bearer token"""
        token = self.get_valid_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return None
    
    @property
    def is_configured(self):
        """Check if credentials are configured"""
        return bool(self.consumer_key and self.consumer_secret)
    
    @property
    def token_status(self):
        """Get human-readable token status"""
        if not self.is_configured:
            return "NOT_CONFIGURED"
        if not self.access_token:
            return "NO_TOKEN"
        if self.token_expiry <= time.time():
            return "EXPIRED"
        remaining = int(self.token_expiry - time.time())
        return f"VALID ({remaining}s remaining)"


def create_default_config():
    """Create a template config.json for the user to fill in"""
    template = {
        "auth_url": "https://ideabiz.lk/apicall/",
        "auth_consumerKey": "",
        "auth_consumerSecret": "",
        "username": "",
        "password": "",
        "access_token": "",
        "refresh_token": "",
        "_instructions": (
            "Fill in consumer_key and consumer_secret from your IdeaBiz MySubscriptions page. "
            "See: https://docs.ideabiz.lk/Getting_Started/Generate_Token/"
        ),
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(template, f, indent=2)
    print(f"Config template created: {CONFIG_FILE}")
    print("Fill in your IdeaBiz consumer_key and consumer_secret.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="IdeaBiz OAuth2 Token Manager")
    parser.add_argument("--generate", action="store_true", help="Generate a new access token")
    parser.add_argument("--refresh", action="store_true", help="Refresh existing token")
    parser.add_argument("--status", action="store_true", help="Check token status")
    parser.add_argument("--init", action="store_true", help="Create template config.json")
    parser.add_argument("--consumer-key", help="Override consumer key")
    parser.add_argument("--consumer-secret", help="Override consumer secret")
    parser.add_argument("--username", help="IdeaBiz username")
    parser.add_argument("--password", help="IdeaBiz password")
    args = parser.parse_args()
    
    if args.init:
        create_default_config()
        sys.exit(0)
    
    auth = IdeaBizAuth(
        consumer_key=args.consumer_key,
        consumer_secret=args.consumer_secret,
        username=args.username,
        password=args.password,
    )
    
    if args.status:
        print(f"Consumer Key: {'SET' if auth.consumer_key else 'NOT SET'}")
        print(f"Consumer Secret: {'SET' if auth.consumer_secret else 'NOT SET'}")
        print(f"Username: {'SET' if auth.username else 'NOT SET'}")
        print(f"Refresh Token: {'SET' if auth.refresh_token else 'NOT SET'}")
        print(f"Token Status: {auth.token_status}")
        if auth.access_token:
            print(f"Access Token: {auth.access_token[:30]}...")
        sys.exit(0)
    
    if args.refresh:
        result = auth.refresh_access_token()
    elif args.generate:
        # Try password grant first, then client_credentials
        if auth.username and auth.password:
            result = auth.generate_token_password()
        else:
            result = auth.generate_token_client_credentials()
    else:
        # Auto-detect best method
        token = auth.get_valid_token()
        if token:
            result = {"access_token": token, "status": auth.token_status}
        else:
            result = {"error": True, "detail": "No credentials configured. Run with --init to create config.json"}
    
    print(json.dumps(result, indent=2))
