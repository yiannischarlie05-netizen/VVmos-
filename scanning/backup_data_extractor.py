#!/usr/bin/env python3
"""
BACKUP DATA EXTRACTOR & REPLACER v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Extracts critical authentication & account data from device backups.
Provides granular replacement logic for device coherence (Android ID, accounts, etc).
Validates data integrity before injection.
"""

import os
import sys
import json
import sqlite3
import xml.etree.ElementTree as ET
import hashlib
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────

@dataclass
class AccountInfo:
    account_name: str
    account_type: str
    auth_token: Optional[str] = None
    device_id: Optional[str] = None
    timestamp: Optional[int] = None

@dataclass
class GMSToken:
    token_key: str
    token_value: str
    source_file: str
    token_type: str  # "access", "refresh", "device", "client"

@dataclass
class ChromeLogin:
    url: str
    username: str
    password_encrypted: bytes
    form_data: Optional[dict] = None

@dataclass
class DeviceIdentity:
    android_id: str
    build_fingerprint: str
    device_name: str
    brand: str
    model: str
    serial: str
    imei: str

@dataclass
class ExtractedData:
    """Complete backup data freeze"""
    timestamp: str
    source_device: str
    
    # Account Data
    accounts: List[AccountInfo]
    system_accounts_dbs: Dict[str, bytes]  # filename -> DB binary
    
    # GMS Authentication
    gms_tokens: List[GMSToken]
    gms_shared_prefs: Dict[str, str]  # filename -> XML content
    gms_databases: Dict[str, bytes]  # filename -> DB binary
    
    # Chrome
    chrome_logins: List[ChromeLogin]
    chrome_cookies: Dict[str, str]  # cookie_name -> value
    chrome_history: int  # count of history entries
    
    # Identity
    device_identity: Optional[DeviceIdentity] = None
    gsf_data: Optional[Dict[str, bytes]] = None  # GSF databases
    
    # Telegram
    telegram_session: Optional[bytes] = None  # tgnet.dat
    
    # Metadata
    integrity_hash: Optional[str] = None
    data_size_bytes: int = 0

# ─────────────────────────────────────────────────────────────────────
# EXTRACTOR
# ─────────────────────────────────────────────────────────────────────

class BackupDataExtractor:
    def __init__(self, clone_dir: str):
        self.clone_dir = Path(clone_dir)
        self.data = ExtractedData(
            timestamp=datetime.now().isoformat(),
            source_device="",
            accounts=[],
            system_accounts_dbs={},
            gms_tokens=[],
            gms_shared_prefs={},
            gms_databases={},
            chrome_logins=[],
            chrome_cookies={},
            chrome_history=0,
            gsf_data={},
        )
        
    def extract_all(self) -> ExtractedData:
        """Complete extraction pipeline"""
        print("[\n  BACKUP DATA EXTRACTOR v1.0\n  Extracting all critical data...\n]")
        
        self._extract_accounts()
        self._extract_gms_tokens_and_prefs()
        self._extract_gms_databases()
        self._extract_chrome_data()
        self._extract_device_identity()
        self._extract_gsf_data()
        self._extract_telegram()
        self._compute_integrity()
        
        print(f"\n✓ Extraction complete: {self.data.data_size_bytes / 1024 / 1024:.1f} MB")
        return self.data
    
    def _extract_accounts(self):
        """Extract system accounts from accounts_ce.db and accounts_de.db"""
        print("  [1/8] Extracting accounts...")
        accounts_dir = self.clone_dir / "gms_accounts"
        
        for db_file in accounts_dir.glob("*.db"):
            try:
                with open(db_file, 'rb') as f:
                    db_bytes = f.read()
                    self.data.system_accounts_dbs[db_file.name] = db_bytes
                    self.data.data_size_bytes += len(db_bytes)
                
                # Parse accounts (if accessible)
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT account_name, account_type FROM accounts")
                    for name, acct_type in cursor.fetchall():
                        self.data.accounts.append(AccountInfo(
                            account_name=name,
                            account_type=acct_type,
                            timestamp=int(datetime.now().timestamp())
                        ))
                    conn.close()
                    print(f"    - {db_file.name}: {len(self.data.accounts)} accounts")
                except:
                    print(f"    - {db_file.name}: (DB parse failed, saved binary)")
            except Exception as e:
                print(f"    - {db_file.name}: ERROR {e}")
    
    def _extract_gms_tokens_and_prefs(self):
        """Extract GMS tokens from shared_prefs XML files"""
        print("  [2/8] Extracting GMS tokens & shared prefs...")
        prefs_dir = self.clone_dir / "gms_shared_prefs"
        
        token_count = 0
        for xml_file in prefs_dir.glob("*.xml"):
            try:
                with open(xml_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    self.data.gms_shared_prefs[xml_file.name] = content
                    self.data.data_size_bytes += len(content.encode())
                
                # Extract tokens from common keys
                if 'Checkin' in xml_file.name or 'Gservices' in xml_file.name:
                    root = ET.fromstring(content) if content.strip() else None
                    if root is not None:
                        for elem in root.findall('.//string'):
                            key = elem.get('name', '')
                            val = elem.text or ''
                            if any(x in key.lower() for x in ['token', 'auth', 'client', 'device']):
                                if len(val) > 20:
                                    self.data.gms_tokens.append(GMSToken(
                                        token_key=key,
                                        token_value=val[:80],  # truncate for safety
                                        source_file=xml_file.name,
                                        token_type=self._classify_token(key)
                                    ))
                                    token_count += 1
            except Exception as e:
                print(f"    - {xml_file.name}: ERROR {e}")
        
        print(f"    - {len(self.data.gms_shared_prefs)} prefs, {token_count} tokens found")
    
    def _extract_gms_databases(self):
        """Extract GMS database files"""
        print("  [3/8] Extracting GMS databases...")
        db_dir = self.clone_dir / "gms_databases"
        
        if db_dir.exists():
            for db_file in db_dir.glob("*.db"):
                try:
                    with open(db_file, 'rb') as f:
                        db_bytes = f.read()
                        self.data.gms_databases[db_file.name] = db_bytes
                        self.data.data_size_bytes += len(db_bytes)
                except Exception as e:
                    print(f"    - {db_file.name}: ERROR {e}")
            
            print(f"    - {len(self.data.gms_databases)} database files")
    
    def _extract_chrome_data(self):
        """Extract Chrome login & cookie data"""
        print("  [4/8] Extracting Chrome data...")
        chrome_dir = self.clone_dir / "chrome_data"
        
        if chrome_dir.exists():
            for db_file in chrome_dir.glob("*.db"):
                size = os.path.getsize(db_file)
                self.data.data_size_bytes += size
                
                if db_file.name == "Login_Data.db":
                    self._extract_chrome_logins(db_file)
                elif db_file.name == "Cookies.db":
                    self._extract_chrome_cookies(db_file)
                elif db_file.name == "History.db":
                    self._extract_chrome_history(db_file)
    
    def _extract_chrome_logins(self, db_path):
        """Extract saved passwords from Chrome Login_Data.db"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins WHERE blacklisted_by_user=0")
            for url, user, pwd_enc in cursor.fetchall():
                self.data.chrome_logins.append(ChromeLogin(
                    url=url,
                    username=user,
                    password_encrypted=pwd_enc
                ))
            conn.close()
            print(f"    - Chrome logins: {len(self.data.chrome_logins)} saved")
        except Exception as e:
            print(f"    - Chrome logins: ERROR {e}")
    
    def _extract_chrome_cookies(self, db_path):
        """Extract authentication cookies"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, value FROM cookies WHERE secure=1")
            for name, value in cursor.fetchall():
                if any(x in name.lower() for x in ['auth', 'sid', 'token', 'session']):
                    self.data.chrome_cookies[name] = value
            conn.close()
            print(f"    - Chrome cookies: {len(self.data.chrome_cookies)} auth tokens")
        except Exception as e:
            print(f"    - Chrome cookies: ERROR {e}")
    
    def _extract_chrome_history(self, db_path):
        """Count Chrome history entries"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM urls")
            self.data.chrome_history = cursor.fetchone()[0]
            conn.close()
            print(f"    - Chrome history: {self.data.chrome_history} entries")
        except Exception as e:
            print(f"    - Chrome history: ERROR {e}")
    
    def _extract_device_identity(self):
        """Extract device identity from fingerprint.json"""
        print("  [5/8] Extracting device identity...")
        fp_file = self.clone_dir / "fingerprint.json"
        
        if fp_file.exists():
            try:
                with open(fp_file) as f:
                    fp = json.load(f)
                    self.data.device_identity = DeviceIdentity(
                        android_id=fp.get("ro.android_id", "unknown"),
                        build_fingerprint=fp.get("ro.build.fingerprint", ""),
                        device_name=fp.get("ro.product.device", ""),
                        brand=fp.get("ro.product.brand", ""),
                        model=fp.get("ro.product.model", ""),
                        serial=fp.get("ro.serialno", ""),
                        imei=fp.get("ro.gsm.imei", "")
                    )
                    print(f"    - Device: {self.data.device_identity.brand} {self.data.device_identity.model}")
                    print(f"    - Android ID: {self.data.device_identity.android_id[:8]}...")
            except Exception as e:
                print(f"    - ERROR {e}")
    
    def _extract_gsf_data(self):
        """Extract Google Services Framework databases"""
        print("  [6/8] Extracting GSF data...")
        gsf_dir = self.clone_dir / "gsf_data"
        
        if gsf_dir.exists():
            for db_file in gsf_dir.glob("*.db*"):
                try:
                    with open(db_file, 'rb') as f:
                        db_bytes = f.read()
                        self.data.gsf_data[db_file.name] = db_bytes
                        self.data.data_size_bytes += len(db_bytes)
                except Exception as e:
                    print(f"    - {db_file.name}: ERROR {e}")
            
            print(f"    - {len(self.data.gsf_data)} GSF files extracted")
    
    def _extract_telegram(self):
        """Extract Telegram session"""
        print("  [7/8] Extracting Telegram session...")
        tg_dir = self.clone_dir / "telegram_session"
        
        if tg_dir.exists():
            tgnet = tg_dir / "tgnet.dat"
            if tgnet.exists():
                try:
                    with open(tgnet, 'rb') as f:
                        self.data.telegram_session = f.read()
                        self.data.data_size_bytes += len(self.data.telegram_session)
                        print(f"    - Telegram session: {len(self.data.telegram_session)} bytes")
                except Exception as e:
                    print(f"    - ERROR {e}")
    
    def _compute_integrity(self):
        """Compute integrity hash of extracted data"""
        print("  [8/8] Computing integrity hash...")
        hasher = hashlib.sha256()
        
        # Hash key data in deterministic order
        for token in self.data.gms_tokens[:10]:
            hasher.update(token.token_value.encode())
        for db_name in sorted(self.data.gms_databases.keys())[:5]:
            hasher.update(self.data.gms_databases[db_name][:100])
        if self.data.device_identity:
            hasher.update(self.data.device_identity.android_id.encode())
        
        self.data.integrity_hash = hasher.hexdigest()[:16]
        print(f"    - Hash: {self.data.integrity_hash}")
    
    def _classify_token(self, key: str) -> str:
        """Classify token type"""
        key_lower = key.lower()
        if 'access' in key_lower:
            return "access"
        elif 'refresh' in key_lower:
            return "refresh"
        elif 'device' in key_lower:
            return "device"
        elif 'client' in key_lower:
            return "client"
        else:
            return "unknown"
    
    def save_json(self, output_path: str):
        """Save extracted data as JSON (tokens truncated for safety)"""
        export_data = {
            "metadata": {
                "timestamp": self.data.timestamp,
                "source_device": self.data.source_device,
                "data_size_mb": self.data.data_size_bytes / 1024 / 1024,
                "integrity_hash": self.data.integrity_hash,
            },
            "accounts": [asdict(a) for a in self.data.accounts],
            "gms_tokens_count": len(self.data.gms_tokens),
            "gms_databases_count": len(self.data.gms_databases),
            "chrome_logins_count": len(self.data.chrome_logins),
            "chrome_cookies_count": len(self.data.chrome_cookies),
            "chrome_history_count": self.data.chrome_history,
            "device_identity": asdict(self.data.device_identity) if self.data.device_identity else None,
            "gsf_files_count": len(self.data.gsf_data) if self.data.gsf_data else 0,
            "telegram_session_size": len(self.data.telegram_session) if self.data.telegram_session else 0,
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        print(f"✓ Saved extraction summary to {output_path}")

# ─────────────────────────────────────────────────────────────────────
# REPLACER
# ─────────────────────────────────────────────────────────────────────

class DataReplacer:
    """Replace device-specific identifiers for injection into different device"""
    
    def __init__(self, extracted_data: ExtractedData):
        self.data = extracted_data
        self.replacements = {}
    
    def plan_replacements(self, target_android_id: str, target_imei: str) -> Dict:
        """Plan all replacements needed"""
        print(f"\n[DATA REPLACER] Planning replacements...")
        print(f"  Source Android ID: {self.data.device_identity.android_id if self.data.device_identity else 'unknown'}")
        print(f"  Target Android ID: {target_android_id}")
        
        old_id = (self.data.device_identity.android_id 
                  if self.data.device_identity else "00000000000000")
        
        self.replacements = {
            "android_id_old": old_id,
            "android_id_new": target_android_id,
            "imei_old": self.data.device_identity.imei if self.data.device_identity else "",
            "imei_new": target_imei,
            "token_mapping": {},  # tokens that need refresh
            "account_mapping": {},  # account name changes
        }
        
        # Flag tokens for refresh
        for token in self.data.gms_tokens:
            if token.token_type in ["access", "device"]:
                self.replacements["token_mapping"][token.token_key] = "⚠ NEEDS REFRESH"
        
        print(f"  Replacements planned:")
        print(f"    - Android ID: {old_id} → {target_android_id}")
        print(f"    - Tokens needing refresh: {len(self.replacements['token_mapping'])}")
        
        return self.replacements
    
    def can_transfer(self) -> Tuple[bool, str]:
        """Check if data can be transferred safely"""
        checks = []
        
        if not self.data.accounts:
            checks.append("⚠ No accounts found in backup")
        
        if not self.data.gms_tokens:
            checks.append("⚠ No GMS tokens found")
        
        if not self.data.device_identity:
            checks.append("⚠ No device identity found")
        
        if len(self.data.gms_databases) < 10:
            checks.append("⚠ Very few GMS databases (expected 20+)")
        
        # OK if we have key data
        is_ok = bool(self.data.accounts and self.data.gms_tokens)
        msg = "\n".join(checks) if checks else "✓ Data looks good for transfer"
        
        return is_ok, msg

# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 backup_data_extractor.py <clone_dir> [--json output.json]")
        sys.exit(1)
    
    clone_dir = sys.argv[1]
    
    if not Path(clone_dir).exists():
        print(f"ERROR: {clone_dir} not found")
        sys.exit(1)
    
    # Extract
    extractor = BackupDataExtractor(clone_dir)
    extracted = extractor.extract_all()
    
    # Save JSON summary
    output_file = "tmp/backup_extraction_summary.json"
    if "--json" in sys.argv:
        idx = sys.argv.index("--json")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    extractor.save_json(output_file)
    
    # Test replacer
    replacer = DataReplacer(extracted)
    replacer.plan_replacements(
        target_android_id="deadbeefcafebabe",
        target_imei="358381000000001"
    )
    
    can_xfer, msg = replacer.can_transfer()
    print(f"\nTransfer Assessment: {msg}")
    print(f"Overall: {'✓ READY' if can_xfer else '✗ NOT READY'}")
