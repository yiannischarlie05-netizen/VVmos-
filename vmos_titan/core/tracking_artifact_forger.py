"""
TrackingArtifactForger — SDK Tracking Artifact Generation for Anti-Fraud Evasion

Generates SDK-specific SharedPreferences and installation artifacts that
make apps appear organically installed via legitimate attribution channels.

Modern anti-fraud systems (Sift, Sardine, Kount, ThreatMetrix) cross-validate
SDK fingerprints. A device with apps but no tracking SDK data is instantly
flagged as synthetic/cloned.

Supported SDKs:
- AppsFlyer: af_user_id, install_time, af_referrer, first_launch
- Adjust: adid, app_token, installed_at, attribution_deeplink  
- Branch: branch_key, identity_id, session_id, link_click_id
- Firebase: firebase_installations_id, app_instance_id, fid_token

16 app→SDK mappings covering major consumer apps.

Usage:
    forger = TrackingArtifactForger(adb_target="127.0.0.1:6520")
    result = forger.forge_all_artifacts(
        android_id="abc123def456",
        install_base_ts=1709251200,  # Base install timestamp
        country="US"
    )
"""

import hashlib
import logging
import random
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# APP → SDK MAPPINGS (from V13 Technical Documentation)
# ═══════════════════════════════════════════════════════════════════════════

APP_SDK_MAP: Dict[str, List[str]] = {
    # Social
    "com.instagram.android": ["appsflyer", "firebase"],
    "com.zhiliaoapp.musically": ["adjust", "firebase"],  # TikTok
    "com.twitter.android": ["appsflyer", "firebase"],
    "com.facebook.katana": ["firebase"],
    "com.snapchat.android": ["adjust", "firebase"],
    
    # Finance
    "com.squareup.cash": ["appsflyer", "firebase"],
    "com.venmo": ["appsflyer", "firebase"],
    "com.paypal.android.p2pmobile": ["appsflyer", "firebase"],
    "com.revolut.revolut": ["adjust", "appsflyer"],
    "com.robinhood.android": ["branch", "firebase"],
    
    # Rideshare/Delivery
    "com.ubercab": ["branch", "firebase"],
    "com.lyft.android": ["branch", "firebase"],
    "com.doordash.driverapp": ["appsflyer", "firebase"],
    
    # Shopping
    "com.amazon.mShop.android.shopping": ["firebase"],
    "com.walmart.android": ["appsflyer", "firebase"],
    "com.target.ui": ["appsflyer", "firebase"],
}

# SDK-specific app tokens/keys (fake but structurally valid)
SDK_APP_TOKENS = {
    "appsflyer": {
        "com.instagram.android": "AfZ8kJ9mN2pQ4rT6",
        "com.squareup.cash": "CaK7mL3nP5qR8sU2",
        "com.venmo": "VeM4nO6pQ8rS1tW3",
        "com.twitter.android": "TwX9yZ2aB4cD6eF8",
        "com.doordash.driverapp": "DdG1hI3jK5lM7nO9",
        "com.walmart.android": "WmP2qR4sT6uV8wX0",
        "com.target.ui": "TgY1zA3bC5dE7fG9",
        "com.paypal.android.p2pmobile": "PpH2iJ4kL6mN8oP0",
    },
    "adjust": {
        "com.zhiliaoapp.musically": "adj_tk_1a2b3c4d5e",
        "com.snapchat.android": "adj_sc_6f7g8h9i0j",
        "com.revolut.revolut": "adj_rv_k1l2m3n4o5",
    },
    "branch": {
        "com.ubercab": "key_live_abc123xyz789",
        "com.lyft.android": "key_live_def456uvw012",
        "com.robinhood.android": "key_live_ghi789rst345",
    },
}


@dataclass
class ArtifactResult:
    """Result of artifact generation for one app."""
    package: str
    sdks: List[str]
    files_created: List[str]
    success: bool
    error: Optional[str] = None


@dataclass
class ForgeResult:
    """Overall result of artifact forging."""
    total_apps: int = 0
    successful_apps: int = 0
    total_files: int = 0
    results: List[ArtifactResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def summary(self) -> str:
        return f"apps={self.successful_apps}/{self.total_apps} files={self.total_files}"


class TrackingArtifactForger:
    """
    Generate and inject SDK tracking artifacts for anti-fraud evasion.
    
    Creates SharedPreferences XML files that match real SDK initialization
    patterns, making apps appear organically installed.
    """
    
    def __init__(self, adb_target: str = "127.0.0.1:6520",
                 vmos_client: Optional[Any] = None):
        """
        Initialize forger.
        
        Args:
            adb_target: ADB target for direct injection
            vmos_client: Optional VMOSCloudClient for VMOS Cloud mode
        """
        self.target = adb_target
        self.vmos_client = vmos_client
        self._use_vmos = vmos_client is not None
    
    # ═══════════════════════════════════════════════════════════════════════
    # ARTIFACT GENERATORS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _gen_appsflyer_artifacts(self, package: str, android_id: str,
                                  install_ts: int) -> Dict[str, str]:
        """Generate AppsFlyer SDK SharedPreferences."""
        app_token = SDK_APP_TOKENS.get("appsflyer", {}).get(package, secrets.token_hex(8))
        
        # AppsFlyer user ID: SHA1(android_id + app_token)[:24]
        af_user_id = hashlib.sha1(
            f"{android_id}{app_token}".encode()
        ).hexdigest()[:24]
        
        # First launch jitter: 0-60 seconds after install
        first_launch_ts = install_ts + random.randint(0, 60)
        
        # Session count: proportional to age
        age_days = (int(time.time()) - install_ts) // 86400
        session_count = max(1, age_days * random.randint(1, 3))
        
        prefs_content = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="AF_USER_ID">{af_user_id}</string>
    <string name="AF_DEVICE_ID">{android_id}</string>
    <long name="AF_INSTALL_TIME" value="{install_ts * 1000}" />
    <long name="AF_FIRST_LAUNCH" value="{first_launch_ts * 1000}" />
    <string name="AF_REFERRER">utm_source=google-play&amp;utm_medium=organic</string>
    <boolean name="AF_IS_FIRST_LAUNCH" value="false" />
    <int name="AF_LAUNCH_COUNT" value="{session_count}" />
    <long name="AF_LAST_LAUNCH" value="{int(time.time() - random.randint(0, 86400)) * 1000}" />
    <string name="AF_APP_VERSION">1.0.0</string>
    <boolean name="AF_GDPR_CONSENT" value="true" />
    <string name="AF_INSTALL_STORE">com.android.vending</string>
</map>'''
        
        return {
            f"/data/data/{package}/shared_prefs/appsflyer-data.xml": prefs_content
        }
    
    def _gen_adjust_artifacts(self, package: str, android_id: str,
                               install_ts: int) -> Dict[str, str]:
        """Generate Adjust SDK SharedPreferences."""
        app_token = SDK_APP_TOKENS.get("adjust", {}).get(package, f"adj_{secrets.token_hex(6)}")
        
        # Adjust device ID (adid): UUID v4 format
        adid = str(uuid.uuid4())
        
        # Activity state
        age_days = (int(time.time()) - install_ts) // 86400
        session_count = max(1, age_days * random.randint(2, 4))
        subsession_count = session_count * random.randint(3, 8)
        
        prefs_content = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="adid">{adid}</string>
    <string name="app_token">{app_token}</string>
    <long name="installed_at" value="{install_ts * 1000}" />
    <long name="created_at" value="{install_ts * 1000}" />
    <int name="session_count" value="{session_count}" />
    <int name="subsession_count" value="{subsession_count}" />
    <long name="last_activity" value="{int(time.time() - random.randint(0, 3600)) * 1000}" />
    <boolean name="enabled" value="true" />
    <boolean name="is_gdpr_forgotten" value="false" />
    <string name="push_token"></string>
    <string name="attribution_deeplink"></string>
    <boolean name="ask_in" value="false" />
</map>'''
        
        activity_state = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="uuid">{adid}</string>
    <boolean name="enabled" value="true" />
    <long name="last_interval" value="{random.randint(60, 3600) * 1000}" />
    <int name="event_count" value="{random.randint(5, 50)}" />
    <long name="time_spent" value="{random.randint(300, 7200) * 1000}" />
</map>'''
        
        return {
            f"/data/data/{package}/shared_prefs/adjust_preferences.xml": prefs_content,
            f"/data/data/{package}/shared_prefs/adjust_activity_state.xml": activity_state,
        }
    
    def _gen_branch_artifacts(self, package: str, android_id: str,
                               install_ts: int) -> Dict[str, str]:
        """Generate Branch SDK SharedPreferences."""
        branch_key = SDK_APP_TOKENS.get("branch", {}).get(package, f"key_live_{secrets.token_hex(12)}")
        
        # Branch identity ID: random 18-digit number
        identity_id = str(random.randint(100000000000000000, 999999999999999999))
        
        # Session ID: random 18-digit number
        session_id = str(random.randint(100000000000000000, 999999999999999999))
        
        # Browser fingerprint ID
        browser_fp = secrets.token_hex(16)
        
        prefs_content = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="bnc_branch_key">{branch_key}</string>
    <string name="bnc_identity_id">{identity_id}</string>
    <string name="bnc_session_id">{session_id}</string>
    <string name="bnc_device_fingerprint_id">{browser_fp}</string>
    <string name="bnc_link_click_id"></string>
    <long name="bnc_install_time" value="{install_ts * 1000}" />
    <boolean name="bnc_is_first_session" value="false" />
    <int name="bnc_total_added_to_session" value="{random.randint(5, 30)}" />
    <string name="bnc_referral_link"></string>
    <boolean name="bnc_tracking_disabled" value="false" />
</map>'''
        
        return {
            f"/data/data/{package}/shared_prefs/branch_referral_shared_pref.xml": prefs_content
        }
    
    def _gen_firebase_artifacts(self, package: str, android_id: str,
                                 install_ts: int) -> Dict[str, str]:
        """Generate Firebase SDK SharedPreferences."""
        # Firebase Installation ID (FID): 22-char base64url
        fid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        fid = "".join(random.choices(fid_chars, k=22))
        
        # App instance ID: 32-char hex
        app_instance_id = secrets.token_hex(16)
        
        # FID token: JWT-like structure (fake but structurally valid)
        fid_token = f"eyJ{secrets.token_urlsafe(60)}"
        
        # Token expiry: 7 days from now
        token_expiry = int(time.time()) + (7 * 86400)
        
        installations_content = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="firebase_installations_id">{fid}</string>
    <string name="firebase_installations_auth_token">{fid_token}</string>
    <long name="firebase_installations_auth_token_expiration_time" value="{token_expiry * 1000}" />
    <long name="firebase_installations_creation_time" value="{install_ts * 1000}" />
    <int name="firebase_installations_status" value="2" />
</map>'''
        
        analytics_content = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="app_instance_id">{app_instance_id}</string>
    <long name="first_open_time" value="{install_ts * 1000}" />
    <long name="last_pause_time" value="{int(time.time() - random.randint(60, 3600)) * 1000}" />
    <boolean name="measurement_enabled" value="true" />
    <boolean name="analytics_collection_enabled" value="true" />
    <int name="session_number" value="{random.randint(5, 50)}" />
</map>'''
        
        return {
            f"/data/data/{package}/shared_prefs/com.google.firebase.installations.xml": installations_content,
            f"/data/data/{package}/shared_prefs/com.google.android.gms.measurement.prefs.xml": analytics_content,
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # INJECTION METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _inject_file_adb(self, path: str, content: str, package: str) -> bool:
        """Inject file via ADB."""
        import subprocess
        import base64
        
        try:
            # Base64 encode to avoid shell escaping issues
            b64 = base64.b64encode(content.encode()).decode()
            
            # Create directory if needed
            dir_path = "/".join(path.split("/")[:-1])
            subprocess.run(
                ["adb", "-s", self.target, "shell", f"mkdir -p {dir_path}"],
                capture_output=True, timeout=10
            )
            
            # Write file
            cmd = f"echo '{b64}' | base64 -d > {path}"
            result = subprocess.run(
                ["adb", "-s", self.target, "shell", cmd],
                capture_output=True, timeout=10
            )
            
            if result.returncode != 0:
                return False
            
            # Fix ownership (get app UID)
            uid_result = subprocess.run(
                ["adb", "-s", self.target, "shell", 
                 f"stat -c %u /data/data/{package} 2>/dev/null || echo 10000"],
                capture_output=True, text=True, timeout=10
            )
            uid = uid_result.stdout.strip() or "10000"
            
            subprocess.run(
                ["adb", "-s", self.target, "shell", f"chown {uid}:{uid} {path}"],
                capture_output=True, timeout=10
            )
            
            # Restore SELinux context
            subprocess.run(
                ["adb", "-s", self.target, "shell", f"restorecon {path}"],
                capture_output=True, timeout=10
            )
            
            return True
        except Exception as e:
            logger.error(f"ADB injection failed: {e}")
            return False
    
    async def _inject_file_vmos(self, path: str, content: str, package: str) -> bool:
        """Inject file via VMOS Cloud API."""
        if not self.vmos_client:
            return False
        
        import base64
        
        try:
            b64 = base64.b64encode(content.encode()).decode()
            
            # Create directory
            dir_path = "/".join(path.split("/")[:-1])
            await self.vmos_client.async_adb_cmd(
                [self.target], f"mkdir -p {dir_path}"
            )
            
            # Write file via base64
            cmd = f"echo '{b64}' | base64 -d > {path}"
            result = await self.vmos_client.async_adb_cmd([self.target], cmd)
            
            # Fix ownership
            await self.vmos_client.async_adb_cmd(
                [self.target],
                f"chown $(stat -c %u /data/data/{package} 2>/dev/null || echo 10000):$(stat -c %g /data/data/{package} 2>/dev/null || echo 10000) {path}"
            )
            
            return result.get("code") == 200
        except Exception as e:
            logger.error(f"VMOS injection failed: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════
    
    def forge_app_artifacts(self, package: str, android_id: str,
                            install_ts: int) -> ArtifactResult:
        """
        Generate and inject artifacts for a single app.
        
        Args:
            package: App package name
            android_id: Device Android ID
            install_ts: App install timestamp (Unix seconds)
            
        Returns:
            ArtifactResult with injection status
        """
        sdks = APP_SDK_MAP.get(package, [])
        if not sdks:
            return ArtifactResult(
                package=package, sdks=[], files_created=[],
                success=False, error="Unknown package"
            )
        
        all_files: Dict[str, str] = {}
        
        for sdk in sdks:
            if sdk == "appsflyer":
                all_files.update(self._gen_appsflyer_artifacts(package, android_id, install_ts))
            elif sdk == "adjust":
                all_files.update(self._gen_adjust_artifacts(package, android_id, install_ts))
            elif sdk == "branch":
                all_files.update(self._gen_branch_artifacts(package, android_id, install_ts))
            elif sdk == "firebase":
                all_files.update(self._gen_firebase_artifacts(package, android_id, install_ts))
        
        files_created = []
        errors = []
        
        for path, content in all_files.items():
            if self._inject_file_adb(path, content, package):
                files_created.append(path)
            else:
                errors.append(f"Failed: {path}")
        
        return ArtifactResult(
            package=package,
            sdks=sdks,
            files_created=files_created,
            success=len(errors) == 0,
            error="; ".join(errors) if errors else None
        )
    
    def forge_all_artifacts(self, android_id: str,
                            install_base_ts: Optional[int] = None,
                            packages: Optional[List[str]] = None) -> ForgeResult:
        """
        Generate artifacts for all mapped apps or specified packages.
        
        Args:
            android_id: Device Android ID
            install_base_ts: Base install timestamp (default: 30-90 days ago)
            packages: Optional list of packages to process (default: all mapped)
            
        Returns:
            ForgeResult with overall status
        """
        if install_base_ts is None:
            # Random install time 30-90 days ago
            install_base_ts = int(time.time()) - random.randint(30 * 86400, 90 * 86400)
        
        target_packages = packages or list(APP_SDK_MAP.keys())
        
        result = ForgeResult(total_apps=len(target_packages))
        
        for i, package in enumerate(target_packages):
            # Stagger install times: each app installed 0-7 days after previous
            app_install_ts = install_base_ts + (i * random.randint(0, 7 * 86400))
            
            app_result = self.forge_app_artifacts(package, android_id, app_install_ts)
            result.results.append(app_result)
            
            if app_result.success:
                result.successful_apps += 1
                result.total_files += len(app_result.files_created)
            else:
                if app_result.error:
                    result.errors.append(f"{package}: {app_result.error}")
        
        logger.info(f"Tracking artifacts forged: {result.summary()}")
        return result
    
    async def forge_all_artifacts_async(self, android_id: str,
                                        install_base_ts: Optional[int] = None,
                                        packages: Optional[List[str]] = None) -> ForgeResult:
        """Async version for VMOS Cloud mode."""
        if install_base_ts is None:
            install_base_ts = int(time.time()) - random.randint(30 * 86400, 90 * 86400)
        
        target_packages = packages or list(APP_SDK_MAP.keys())
        
        result = ForgeResult(total_apps=len(target_packages))
        
        for i, package in enumerate(target_packages):
            app_install_ts = install_base_ts + (i * random.randint(0, 7 * 86400))
            
            sdks = APP_SDK_MAP.get(package, [])
            if not sdks:
                continue
            
            all_files: Dict[str, str] = {}
            
            for sdk in sdks:
                if sdk == "appsflyer":
                    all_files.update(self._gen_appsflyer_artifacts(package, android_id, app_install_ts))
                elif sdk == "adjust":
                    all_files.update(self._gen_adjust_artifacts(package, android_id, app_install_ts))
                elif sdk == "branch":
                    all_files.update(self._gen_branch_artifacts(package, android_id, app_install_ts))
                elif sdk == "firebase":
                    all_files.update(self._gen_firebase_artifacts(package, android_id, app_install_ts))
            
            files_created = []
            errors = []
            
            for path, content in all_files.items():
                if await self._inject_file_vmos(path, content, package):
                    files_created.append(path)
                else:
                    errors.append(f"Failed: {path}")
            
            app_result = ArtifactResult(
                package=package,
                sdks=sdks,
                files_created=files_created,
                success=len(errors) == 0,
                error="; ".join(errors) if errors else None
            )
            result.results.append(app_result)
            
            if app_result.success:
                result.successful_apps += 1
                result.total_files += len(files_created)
            else:
                result.errors.extend(errors)
        
        return result


# Convenience function
def forge_tracking_artifacts(adb_target: str, android_id: str,
                             install_base_ts: Optional[int] = None) -> ForgeResult:
    """Quick helper to forge all tracking artifacts."""
    forger = TrackingArtifactForger(adb_target=adb_target)
    return forger.forge_all_artifacts(android_id, install_base_ts)
