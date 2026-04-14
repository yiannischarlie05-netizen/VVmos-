#!/usr/bin/env python3
"""
Titan V13 — VMOS Account Fixer
================================
Fixes Play Store 'AuthFailureError: User needs to (re)enter credentials'
on VMOS Cloud devices by rebuilding accounts_ce.db host-side and pushing
via base64 chunking.

Root Cause:
    Account was injected with SYNTHETIC ya29.* tokens that fail server-side
    validation → Play Store can't download anything.

Fix Strategy (3-tier):
    1. Method A (gpsoauth): Get real OAuth tokens → inject into DB
    2. Method C (Hybrid): Store password in DB → GMS authenticates natively
       using device's DroidGuard context (higher trust than raw API calls)
    3. AccountManager force-refresh: Invalidate tokens + broadcast to trigger
       GMS re-authentication cycle

Usage:
    export PYTHONPATH=core:server:vmos_titan/core
    python3 vmos_account_fixer.py
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import random
import secrets
import sqlite3
import struct
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Setup ─────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("account-fixer")

# Load .env
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "vmos_titan" / "core"))
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "server"))


# ══════════════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════════════

PAD_CODE = "APP5B54EI0Z1EOEA"

GMAIL_EMAIL = "epolusamuel682@gmail.com"
GMAIL_PASSWORD = "gA3EFqhAQJOBZ"

# Device identifiers (from earlier scan)
ANDROID_ID_HEX = "c8a554af4d6387"
CHECKIN_ANDROID_ID = "4092477265957745660"
CHECKIN_DEVICE_ID = "1580771363884134"
GMS_VERSION = "24.26.32"

# UIDs on this device
SYSTEM_UID = 1000
GMS_UID = 10036
VENDING_UID = 10042

# Paths
ACCOUNTS_CE_PATH = "/data/system_ce/0/accounts_ce.db"
ACCOUNTS_DE_PATH = "/data/system_de/0/accounts_de.db"
GMS_PREFS = "/data/data/com.google.android.gms/shared_prefs"
GSF_PREFS = "/data/data/com.google.android.gsf/shared_prefs"
VENDING_PREFS = "/data/data/com.android.vending/shared_prefs"

# Base64 chunk size (VMOS syncCmd has ~4KB limit)
B64_CHUNK_SIZE = 2048  # Conservative — 2KB chunks for reliability
CMD_DELAY = 3.5        # Seconds between VMOS API calls

# Core Google OAuth scopes
CORE_SCOPES = [
    "oauth2:https://www.googleapis.com/auth/plus.me",
    "oauth2:https://www.googleapis.com/auth/userinfo.email",
    "oauth2:https://www.googleapis.com/auth/userinfo.profile",
    "oauth2:https://www.googleapis.com/auth/gmail.readonly",
    "oauth2:https://www.googleapis.com/auth/youtube",
    "oauth2:https://www.googleapis.com/auth/drive",
    "oauth2:https://www.googleapis.com/auth/contacts",
    "oauth2:https://www.googleapis.com/auth/calendar",
    "oauth2:https://www.googleapis.com/auth/android",
]

GMS_CLIENT_SIG = "38918a453d07199354f8b19af05ec6562ced5788"


# ══════════════════════════════════════════════════════════════════════════════
# VMOS Cloud API Helper
# ══════════════════════════════════════════════════════════════════════════════

class VMOSHelper:
    """Thin wrapper around VMOSCloudClient with retry + rate limiting."""

    def __init__(self):
        from vmos_cloud_api import VMOSCloudClient
        self.client = VMOSCloudClient()
        self._last_cmd_time = 0.0

    async def cmd(self, command: str, label: str = "", timeout: int = 30) -> str:
        """Execute a shell command on the VMOS device with rate limiting."""
        # Enforce minimum delay between commands
        elapsed = time.time() - self._last_cmd_time
        if elapsed < CMD_DELAY:
            await asyncio.sleep(CMD_DELAY - elapsed)

        self._last_cmd_time = time.time()

        for attempt in range(3):
            try:
                r = await self.client.sync_cmd(PAD_CODE, command, timeout_sec=timeout)
                if not isinstance(r, dict):
                    log.warning("[%s] Unexpected response type: %s", label, type(r))
                    await asyncio.sleep(5)
                    continue

                code = r.get("code")

                if code == 200:
                    data = r.get("data")
                    # data can be None (no output), empty list, or list with results
                    if data is None:
                        # Command executed successfully but produced no output
                        if label and "CHUNK" not in label:
                            log.debug("[%s] OK (no output)", label)
                        return ""
                    if isinstance(data, list) and data:
                        raw = data[0].get("errorMsg") if isinstance(data[0], dict) else None
                        out = raw if raw is not None else ""
                        if label and "CHUNK" not in label and out:
                            log.info("[%s] %s", label, out[:200])
                        return out
                    return ""

                if code == 110012:
                    # Timeout — retry with longer spacing
                    log.warning("[%s] Command timeout (attempt %d/3)", label, attempt + 1)
                    await asyncio.sleep(5)
                    continue

                msg = r.get("msg", "")
                log.warning("[%s] API error %s: %s", label, code, msg)
                return ""
            except Exception as e:
                log.warning("[%s] Exception (attempt %d/3): %s", label, attempt + 1, e)
                await asyncio.sleep(5)
        return ""

    async def push_bytes(self, data: bytes, target_path: str,
                         owner: str = "system:system", mode: str = "660") -> bool:
        """Push file to device via base64 chunking."""
        b64_data = base64.b64encode(data).decode("ascii")
        staging = f"/sdcard/.titan_fix_{hashlib.md5(target_path.encode()).hexdigest()[:8]}"
        b64_file = f"{staging}.b64"

        log.info("Pushing %d bytes → %s (%d b64 chunks)", len(data), target_path,
                 len(b64_data) // B64_CHUNK_SIZE + 1)

        # Clean staging
        await self.cmd(f"rm -f {b64_file} {staging}", "CLEAN")

        # Transfer chunks
        chunks = [b64_data[i:i + B64_CHUNK_SIZE]
                  for i in range(0, len(b64_data), B64_CHUNK_SIZE)]

        for i, chunk in enumerate(chunks):
            # Escape single quotes in b64 data (shouldn't happen but safety)
            safe_chunk = chunk.replace("'", "'\\''")
            await self.cmd(f"echo -n '{safe_chunk}' >> {b64_file}", f"CHUNK {i+1}/{len(chunks)}")
            if (i + 1) % 10 == 0:
                log.info("  Transferred %d/%d chunks...", i + 1, len(chunks))

        # Decode
        await self.cmd(f"base64 -d {b64_file} > {staging}", "B64_DECODE")

        # Verify size
        size_out = await self.cmd(f"wc -c < {staging}", "SIZE_CHECK")
        try:
            actual_size = int(size_out.strip())
            if actual_size != len(data):
                log.warning("Size mismatch: expected %d, got %d", len(data), actual_size)
        except (ValueError, AttributeError):
            log.warning("Could not verify transferred file size")

        # Create target directory
        target_dir = os.path.dirname(target_path)
        await self.cmd(f"mkdir -p {target_dir}", "MKDIR")

        # Copy to target
        await self.cmd(f"cp {staging} {target_path}", "COPY")

        # Set ownership and permissions
        await self.cmd(f"chown {owner} {target_path}", "CHOWN")
        await self.cmd(f"chmod {mode} {target_path}", "CHMOD")

        # Restore SELinux context
        await self.cmd(f"restorecon {target_path}", "RESTORECON")

        # Clean up staging
        await self.cmd(f"rm -f {b64_file} {staging}", "CLEANUP")

        # Verify file exists
        verify = await self.cmd(f"ls -la {target_path}", "VERIFY")
        if target_path in verify:
            log.info("Successfully pushed %s", target_path)
            return True
        else:
            log.error("File verification failed for %s", target_path)
            return False

    async def push_xml(self, xml_content: str, target_path: str,
                       app_package: str) -> bool:
        """Push a SharedPreferences XML file with correct ownership."""
        # Get the app's UID
        uid_str = await self.cmd(
            f"stat -c '%u' /data/data/{app_package} 2>/dev/null",
            f"UID({app_package})"
        )
        try:
            uid = int(uid_str.strip())
        except (ValueError, AttributeError):
            log.warning("Could not get UID for %s, using default", app_package)
            uid = GMS_UID  # fallback

        data = xml_content.encode("utf-8")
        owner = f"{uid}:{uid}"
        return await self.push_bytes(data, target_path, owner=owner, mode="660")


# ══════════════════════════════════════════════════════════════════════════════
# Database Builders (host-side SQLite construction)
# ══════════════════════════════════════════════════════════════════════════════

def build_accounts_ce_db(
    email: str,
    password: str = "",
    tokens: Optional[Dict[str, str]] = None,
    gaia_id: str = "",
    age_days: int = 90,
) -> bytes:
    """Build accounts_ce.db with proper schema, password, and tokens.

    When `password` is set and `tokens` is empty, GMS will attempt to
    authenticate using the stored password + device DroidGuard context.
    This has higher trust than raw gpsoauth API calls.
    """
    if not gaia_id:
        gaia_id = str(random.randint(100_000_000_000_000_000, 999_999_999_999_999_999_999))

    display_name = email.split("@")[0].replace(".", " ").title()
    parts = display_name.split()
    given_name = parts[0] if parts else ""
    family_name = parts[-1] if len(parts) > 1 else ""
    birth_ts_ms = int((time.time() - age_days * 86400) * 1000)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        conn = sqlite3.connect(tmp_path)
        c = conn.cursor()

        # Android 14/15 accounts_ce schema (PRAGMA user_version = 10)
        c.executescript("""
            CREATE TABLE IF NOT EXISTS android_metadata (locale TEXT);
            CREATE TABLE IF NOT EXISTS accounts (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                password TEXT,
                UNIQUE(name, type)
            );
            CREATE TABLE IF NOT EXISTS authtokens (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                accounts_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                authtoken TEXT,
                UNIQUE(accounts_id, type)
            );
            CREATE TABLE IF NOT EXISTS extras (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                accounts_id INTEGER,
                key TEXT NOT NULL,
                value TEXT,
                UNIQUE(accounts_id, key)
            );
            CREATE TABLE IF NOT EXISTS grants (
                accounts_id INTEGER NOT NULL,
                auth_token_type TEXT NOT NULL DEFAULT '',
                uid INTEGER NOT NULL,
                UNIQUE(accounts_id, auth_token_type, uid)
            );
            CREATE TABLE IF NOT EXISTS shared_accounts (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                UNIQUE(name, type)
            );
            PRAGMA user_version = 10;
        """)

        # Insert locale
        c.execute("INSERT OR REPLACE INTO android_metadata (locale) VALUES ('en_US')")

        # Insert account WITH password
        # When GMS finds a password here, it uses it for server-side auth
        c.execute(
            "INSERT OR REPLACE INTO accounts (name, type, password) VALUES (?, 'com.google', ?)",
            (email, password),
        )
        account_id = c.lastrowid or 1

        # Insert auth tokens (real if available, otherwise EMPTY — forces re-auth)
        if tokens:
            for scope, token in tokens.items():
                c.execute(
                    "INSERT OR REPLACE INTO authtokens (accounts_id, type, authtoken) VALUES (?, ?, ?)",
                    (account_id, scope, token),
                )
            log.info("Inserted %d REAL auth tokens", len(tokens))
        else:
            # NO tokens → forces GMS to authenticate with stored password
            log.info("No tokens inserted — GMS will authenticate with stored password")

        # Account extras (metadata)
        extras = [
            ("google.services.gaia", gaia_id),
            ("GoogleUserId", gaia_id),
            ("is_child_account", "false"),
            ("given_name", given_name),
            ("family_name", family_name),
            ("display_name", display_name),
            ("account_creation_time", str(birth_ts_ms)),
            ("last_known_device_id_key", secrets.token_hex(8)),
        ]
        for key, value in extras:
            c.execute(
                "INSERT OR REPLACE INTO extras (accounts_id, key, value) VALUES (?, ?, ?)",
                (account_id, key, value),
            )

        # Shared accounts mirror
        c.execute(
            "INSERT OR IGNORE INTO shared_accounts (name, type) VALUES (?, 'com.google')",
            (email,),
        )

        # Visibility grants — critical system apps must see the account
        for uid in (SYSTEM_UID, GMS_UID, VENDING_UID, 10000, 10001):
            c.execute(
                "INSERT OR IGNORE INTO grants (accounts_id, auth_token_type, uid) VALUES (?, '', ?)",
                (account_id, uid),
            )
            # Also grant specific token types
            for token_type in ("com.google", "SID", "LSID"):
                c.execute(
                    "INSERT OR IGNORE INTO grants (accounts_id, auth_token_type, uid) VALUES (?, ?, ?)",
                    (account_id, token_type, uid),
                )

        conn.commit()
        conn.close()

        data = Path(tmp_path).read_bytes()
        log.info("Built accounts_ce.db: %d bytes, password=%s, tokens=%d",
                 len(data), "YES" if password else "NO",
                 len(tokens) if tokens else 0)
        return data
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def build_accounts_de_db(
    email: str,
    gaia_id: str = "",
) -> bytes:
    """Build accounts_de.db (device-encrypted, no tokens)."""
    if not gaia_id:
        gaia_id = str(random.randint(100_000_000_000_000_000, 999_999_999_999_999_999_999))

    display_name = email.split("@")[0].replace(".", " ").title()
    parts = display_name.split()
    given_name = parts[0] if parts else ""
    family_name = parts[-1] if len(parts) > 1 else ""

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        conn = sqlite3.connect(tmp_path)
        c = conn.cursor()

        c.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                _id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                previous_name TEXT,
                last_password_entry_time_millis_epoch INTEGER DEFAULT 0,
                UNIQUE(name, type)
            );
            CREATE TABLE IF NOT EXISTS grants (
                accounts_id INTEGER NOT NULL,
                auth_token_type TEXT NOT NULL DEFAULT '',
                uid INTEGER NOT NULL,
                UNIQUE(accounts_id, auth_token_type, uid)
            );
            CREATE TABLE IF NOT EXISTS visibility (
                accounts_id INTEGER NOT NULL,
                _package TEXT NOT NULL,
                value INTEGER,
                UNIQUE(accounts_id, _package)
            );
            CREATE TABLE IF NOT EXISTS authtokens (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                accounts_id INTEGER NOT NULL,
                type TEXT NOT NULL DEFAULT '',
                authtoken TEXT,
                UNIQUE(accounts_id, type)
            );
            CREATE TABLE IF NOT EXISTS extras (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                accounts_id INTEGER NOT NULL,
                key TEXT NOT NULL DEFAULT '',
                value TEXT,
                UNIQUE(accounts_id, key)
            );
            PRAGMA user_version = 3;
        """)

        last_entry_ms = int(time.time() * 1000)
        c.execute(
            "INSERT OR REPLACE INTO accounts (name, type, previous_name, "
            "last_password_entry_time_millis_epoch) VALUES (?, 'com.google', NULL, ?)",
            (email, last_entry_ms),
        )
        account_id = c.lastrowid or 1

        for key, value in [
            ("given_name", given_name),
            ("family_name", family_name),
            ("display_name", display_name),
            ("GoogleUserId", gaia_id),
        ]:
            c.execute(
                "INSERT OR IGNORE INTO extras (accounts_id, key, value) VALUES (?, ?, ?)",
                (account_id, key, value),
            )

        # Visibility grants
        for pkg in ("com.google.android.gms", "com.android.vending",
                     "com.google.android.youtube", "com.google.android.gm",
                     "com.google.android.gsf", "com.android.chrome"):
            c.execute(
                "INSERT OR IGNORE INTO visibility (accounts_id, _package, value) VALUES (?, ?, 1)",
                (account_id, pkg),
            )

        conn.commit()
        conn.close()

        data = Path(tmp_path).read_bytes()
        log.info("Built accounts_de.db: %d bytes", len(data))
        return data
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# SharedPreferences XML Builders
# ══════════════════════════════════════════════════════════════════════════════

def build_xml(entries: Dict[str, str | bool | int]) -> str:
    """Build a SharedPreferences XML file from key-value pairs."""
    lines = ['<?xml version=\'1.0\' encoding=\'utf-8\' standalone=\'yes\' ?>', '<map>']
    for key, value in entries.items():
        if isinstance(value, bool):
            lines.append(f'    <boolean name="{key}" value="{str(value).lower()}" />')
        elif isinstance(value, int):
            lines.append(f'    <long name="{key}" value="{value}" />')
        elif isinstance(value, float):
            lines.append(f'    <float name="{key}" value="{value}" />')
        else:
            # Escape XML special characters
            val = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            lines.append(f'    <string name="{key}">{val}</string>')
    lines.append('</map>')
    return "\n".join(lines) + "\n"


def build_checkin_service_xml(email: str) -> str:
    """GMS CheckinService.xml — device registration state."""
    now_ms = int(time.time() * 1000)
    return f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="CheckinService_lastSim">[no-sim:310012732480500]</string>
    <long name="CheckinService_lastCheckinServerTime" value="{now_ms}" />
    <string name="lastRadio">S9280ZCS4BYDF,S9280ZCS4BYDF</string>
    <long name="CheckinInterval_IntervalSeconds" value="43163" />
    <long name="CheckinInterval_FlexSec" value="10800" />
    <long name="CheckinService_lastCheckinSuccessTime" value="{now_ms}" />
    <long name="CheckinService_last_checkin_ms_unspecified" value="{now_ms}" />
    <long name="CheckinService_checkinCompleteBroadcastTime" value="{now_ms}" />
    <string name="android_id">{CHECKIN_ANDROID_ID}</string>
    <string name="CheckinService_versionInfo">c8_dsQvF0IQXIJ42qPW9kfDTTyIQ1Bk</string>
    <long name="CheckinTask_bookmark" value="0" />
    <set name="CheckinService_accountsReceivedByServer">
        <string>{{"authAccount":"{email}","accountType":"com.google"}}</string>
    </set>
</map>
"""


def build_checkin_account_xml(email: str) -> str:
    """GMS CheckinAccount.xml — account binding for checkin."""
    return build_xml({
        "account_name": email,
        "account_type": "com.google",
        "registered": True,
    })


def build_gservices_xml() -> str:
    """GMS GservicesSettings.xml — device IDs."""
    return build_xml({
        "android_id": ANDROID_ID_HEX,
        "checkin_device_id": CHECKIN_DEVICE_ID,
        "gms:version": GMS_VERSION,
    })


def build_finsky_xml(email: str) -> str:
    """Play Store finsky.xml — account binding and setup state."""
    now_ms = int(time.time() * 1000)
    return build_xml({
        "signed_in_account": email,
        "first_account_name": email,
        "logged_in": True,
        "setup_done": True,
        "setup_wizard_has_run": True,
        "tos_accepted": True,
        "content_filters": "0",
        "auto_update_enabled": True,
        "download_manager_max_bytes_over_mobile": "0",
        "notify_updates": True,
        "last_notified_time": now_ms,
    })


def build_gsf_google_settings_xml() -> str:
    """GSF googlesettings.xml — GSF device registration."""
    return build_xml({
        "android_id": ANDROID_ID_HEX,
        "checkin_device_id": CHECKIN_DEVICE_ID,
        "digest": secrets.token_hex(20),
    })


# ══════════════════════════════════════════════════════════════════════════════
# Token Acquisition (Method A — gpsoauth)
# ══════════════════════════════════════════════════════════════════════════════

def try_gpsoauth(email: str, password: str, android_id: str) -> Optional[Dict[str, str]]:
    """Attempt to get real OAuth tokens via gpsoauth.

    Returns dict of {scope: token} or None if authentication fails.
    """
    try:
        import gpsoauth
    except ImportError:
        log.warning("gpsoauth not installed — skipping Method A")
        return None

    log.info("Method A: Attempting gpsoauth master token login...")

    try:
        master_resp = gpsoauth.perform_master_login(
            email=email,
            password=password,
            android_id=android_id,
            service="ac2dm",
            device_country="us",
            operator_country="us",
            lang="en_US",
            sdk_version=34,
            client_sig=GMS_CLIENT_SIG,
        )
    except Exception as e:
        log.warning("Method A network error: %s", e)
        return None

    if "Token" not in master_resp:
        error = master_resp.get("Error", "Unknown")
        log.warning("Method A failed: %s", error)
        if error == "BadAuthentication":
            log.info("  → Password rejected. If 2FA is enabled, use a Google App Password.")
            log.info("  → Create one at: https://myaccount.google.com/apppasswords")
        elif error == "NeedsBrowser":
            log.info("  → Google requires browser sign-in. Use App Password instead.")
        return None

    master_token = master_resp["Token"]
    log.info("Method A: Master token acquired! Exchanging for OAuth tokens...")

    tokens: Dict[str, str] = {}
    tokens["com.google"] = master_token

    for scope in CORE_SCOPES:
        try:
            oauth_resp = gpsoauth.perform_oauth(
                email=email,
                master_token=master_token,
                android_id=android_id,
                service=scope,
                app="com.google.android.gms",
                client_sig=GMS_CLIENT_SIG,
                sdk_version=34,
            )
            if "Auth" in oauth_resp:
                tokens[scope] = oauth_resp["Auth"]
        except Exception as e:
            log.debug("OAuth exchange failed for %s: %s", scope, e)

    if len(tokens) > 1:
        log.info("Method A: Got %d real tokens!", len(tokens))
        return tokens
    else:
        log.warning("Method A: Master token acquired but no OAuth tokens exchanged")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Main Fix Pipeline
# ══════════════════════════════════════════════════════════════════════════════

async def run_fix():
    """Execute the complete account fix pipeline."""
    vmos = VMOSHelper()

    log.info("=" * 70)
    log.info("TITAN ACCOUNT FIXER — Fixing Play Store auth for %s", GMAIL_EMAIL)
    log.info("=" * 70)

    # ── Step 0: Verify device is alive ────────────────────────────────
    log.info("\n[STEP 0] Verifying device connectivity...")
    whoami = await vmos.cmd("id -u 2>/dev/null", "VERIFY")
    if "0" not in whoami:
        log.error("Device not responding or not root. Aborting.")
        return False
    log.info("Device alive and root confirmed.")

    # ── Step 1: Try Method A (gpsoauth) ───────────────────────────────
    log.info("\n[STEP 1] Attempting Method A: gpsoauth real tokens...")
    real_tokens = try_gpsoauth(GMAIL_EMAIL, GMAIL_PASSWORD, ANDROID_ID_HEX)

    if real_tokens:
        log.info("Method A SUCCEEDED — will inject real tokens")
        use_password = ""  # Don't need password when we have real tokens
        tokens_to_inject = real_tokens
    else:
        log.info("Method A failed — using Method C: password stored for GMS native auth")
        use_password = GMAIL_PASSWORD
        tokens_to_inject = None

    # ── Step 2: Generate GAIA ID ──────────────────────────────────────
    gaia_id = str(random.randint(100_000_000_000_000_000, 999_999_999_999_999_999_999))
    log.info("Generated GAIA ID: %s", gaia_id)

    # ── Step 3: Stop all Google apps ──────────────────────────────────
    log.info("\n[STEP 3] Stopping Google apps...")
    await vmos.cmd("am force-stop com.android.vending", "STOP_VENDING")
    await vmos.cmd("am force-stop com.google.android.gms", "STOP_GMS")
    await vmos.cmd("am force-stop com.google.android.gsf", "STOP_GSF")
    log.info("All Google apps stopped.")

    # ── Step 4: Remove existing broken DB files ───────────────────────
    log.info("\n[STEP 4] Removing old account databases...")
    await vmos.cmd(f"rm -f {ACCOUNTS_CE_PATH} {ACCOUNTS_CE_PATH}-journal {ACCOUNTS_CE_PATH}-wal {ACCOUNTS_CE_PATH}-shm", "RM_CE")
    await vmos.cmd(f"rm -f {ACCOUNTS_DE_PATH} {ACCOUNTS_DE_PATH}-journal {ACCOUNTS_DE_PATH}-wal {ACCOUNTS_DE_PATH}-shm", "RM_DE")
    log.info("Old databases removed.")

    # ── Step 5: Build fresh databases host-side ───────────────────────
    log.info("\n[STEP 5] Building fresh databases on host...")
    ce_db = build_accounts_ce_db(
        email=GMAIL_EMAIL,
        password=use_password,
        tokens=tokens_to_inject,
        gaia_id=gaia_id,
        age_days=90,
    )
    de_db = build_accounts_de_db(
        email=GMAIL_EMAIL,
        gaia_id=gaia_id,
    )

    # ── Step 6: Push databases to device ──────────────────────────────
    log.info("\n[STEP 6] Pushing databases to device via base64...")

    ce_ok = await vmos.push_bytes(
        ce_db, ACCOUNTS_CE_PATH,
        owner=f"{SYSTEM_UID}:{SYSTEM_UID}", mode="600"
    )
    if not ce_ok:
        log.error("Failed to push accounts_ce.db!")
        return False

    de_ok = await vmos.push_bytes(
        de_db, ACCOUNTS_DE_PATH,
        owner=f"{SYSTEM_UID}:{SYSTEM_UID}", mode="600"
    )
    if not de_ok:
        log.error("Failed to push accounts_de.db!")
        return False

    log.info("Both databases pushed successfully.")

    # ── Step 7: Push SharedPreferences ────────────────────────────────
    log.info("\n[STEP 7] Pushing SharedPreferences...")

    prefs_to_push = [
        (build_checkin_service_xml(GMAIL_EMAIL),
         f"{GMS_PREFS}/CheckinService.xml", "com.google.android.gms"),
        (build_checkin_account_xml(GMAIL_EMAIL),
         f"{GMS_PREFS}/CheckinAccount.xml", "com.google.android.gms"),
        (build_gservices_xml(),
         f"{GMS_PREFS}/GservicesSettings.xml", "com.google.android.gms"),
        (build_finsky_xml(GMAIL_EMAIL),
         f"{VENDING_PREFS}/finsky.xml", "com.android.vending"),
        (build_gsf_google_settings_xml(),
         f"{GSF_PREFS}/googlesettings.xml", "com.google.android.gsf"),
    ]

    for xml_content, path, pkg in prefs_to_push:
        ok = await vmos.push_xml(xml_content, path, pkg)
        if ok:
            log.info("  ✓ %s", path.split("/")[-1])
        else:
            log.warning("  ✗ %s (non-fatal, continuing)", path.split("/")[-1])

    # ── Step 8: Force GMS to re-authenticate ──────────────────────────
    log.info("\n[STEP 8] Forcing GMS re-authentication cycle...")

    # Kill AccountManagerService's host process (system_server restart is too heavy)
    # Instead, broadcast account changes + force GMS to re-sync
    await vmos.cmd(
        "am broadcast -a android.accounts.LOGIN_ACCOUNTS_CHANGED 2>/dev/null",
        "BROADCAST_LOGIN_CHANGED"
    )
    await vmos.cmd(
        "am broadcast -a com.google.android.gms.auth.LOGIN_ACCOUNTS_CHANGED 2>/dev/null",
        "BROADCAST_GMS_LOGIN_CHANGED"
    )
    await vmos.cmd(
        "am broadcast -a android.accounts.action.ACCOUNT_REMOVED 2>/dev/null",
        "BROADCAST_ACCOUNT_REMOVED"
    )

    # Force ContentResolver sync for Google account
    await vmos.cmd(
        f"content call --uri content://com.google.android.gms.auth.accounts --method clearToken 2>/dev/null || echo skip",
        "CLEAR_TOKEN_CACHE"
    )

    # Restart GMS to pick up new DB
    await vmos.cmd("am force-stop com.google.android.gms", "RESTART_GMS_1")
    await asyncio.sleep(2)

    # Start GMS explicitly
    await vmos.cmd(
        "am startservice -n com.google.android.gms/.checkin.CheckinService 2>/dev/null || echo skip",
        "START_CHECKIN"
    )
    await vmos.cmd(
        "am broadcast -a com.google.android.gms.INITIALIZE 2>/dev/null",
        "GMS_INITIALIZE"
    )

    log.info("GMS re-authentication cycle triggered.")

    # ── Step 9: Wait for GMS to process ───────────────────────────────
    log.info("\n[STEP 9] Waiting 15s for GMS to process account...")
    await asyncio.sleep(15)

    # ── Step 10: Verify ───────────────────────────────────────────────
    log.info("\n[STEP 10] Verifying account state...")

    # Check account is visible
    acct_dump = await vmos.cmd(
        "dumpsys account 2>/dev/null | head -10",
        "VERIFY_ACCOUNT"
    )
    if GMAIL_EMAIL in acct_dump:
        log.info("  ✓ Account visible in AccountManager")
    else:
        log.warning("  ✗ Account NOT visible — system_server may need restart")

    # Check for auth errors in logcat
    auth_log = await vmos.cmd(
        "logcat -d -s Finsky AccountManagerService GmsAccountChange 2>/dev/null | grep -iE 'auth|token|credential|error' | tail -10",
        "CHECK_AUTH_LOG"
    )
    if "AuthFailureError" in auth_log:
        log.warning("  ✗ AuthFailureError still present in logs")
    else:
        log.info("  ✓ No AuthFailureError in recent logs")

    # Try opening Play Store
    await vmos.cmd(
        "am start -n com.android.vending/com.android.vending.AssetBrowserActivity 2>/dev/null",
        "LAUNCH_PLAY_STORE"
    )

    log.info("\n" + "=" * 70)
    if real_tokens:
        log.info("FIX COMPLETE — Real tokens injected (Method A)")
        log.info("Play Store should work immediately.")
    else:
        log.info("FIX APPLIED — Method C (password stored for GMS native auth)")
        log.info("")
        log.info("WHAT HAPPENS NEXT:")
        log.info("  1. GMS will attempt to authenticate with the stored password")
        log.info("  2. If successful → real tokens appear → Play Store works")
        log.info("  3. If Google rejects the password (2FA, security block):")
        log.info("     → A 'Sign in to your Google Account' notification appears")
        log.info("     → Tapping it opens the proper Google sign-in flow")
        log.info("     → This flow uses WebView (not old GSF login)")
        log.info("")
        log.info("IF PASSWORD IS REJECTED, you need one of these:")
        log.info("  a) Create a Google App Password:")
        log.info("     https://myaccount.google.com/apppasswords")
        log.info("     Then re-run with the App Password")
        log.info("  b) Tap the notification on the device screen")
        log.info("     (screen share: check VMOS Cloud console)")
    log.info("=" * 70)

    return True


# ══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    success = asyncio.run(run_fix())
    sys.exit(0 if success else 1)
