#!/usr/bin/env python3
"""
Clone Injection v4.0 — API-First + GMS Gate Strategy
=====================================================
Uses discoveries from VMOSPro Cloud Device Controller repo analysis:

1. updatePadAndroidProp API for ro.* identity (proper deep write, triggers restart)
2. updatePadProperties API for persist.* identity (no restart)  
3. uploadFileV3 API to push DB files from VPS URL directly to device paths
4. Disable GMS authenticator BEFORE injection to prevent account removal
5. Re-inject android_id + GSF ID AFTER restart for session continuity

Key insight: Previous attempts failed because:
- modify_instance_properties (updatePadProperties) only handles persist.* runtime props
- ro.* props need updatePadAndroidProp which TRIGGERS A RESTART
- GMS authenticator runs after restart and removes injected accounts
- Solution: disable GMS → restart with new identity → inject accounts → enable GMS

Usage:
  python3 tools/clone_inject_v4.py                    # Full injection from cached data
  python3 tools/clone_inject_v4.py --identity-only     # Identity props only
  python3 tools/clone_inject_v4.py --accounts-only     # Account DBs only
  python3 tools/clone_inject_v4.py --verify            # Verify current state
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
PAD = os.environ.get("VMOS_PAD", "APP6476KYH9KMLU5")
BASE_URL = "https://api.vmoscloud.com"
VPS_IP = "YOUR_OLLAMA_HOST"
VPS_PORT = 19001  # nginx/python HTTP server serving extracted files
CMD_DELAY = 3.5

# Source identity (extracted from Xiaomi Mi 10 at 10.12.11.21)
IDENTITY_FILE = Path("/tmp/adv_clone/10_12_11_21/identity.json")
EXTRACTED_DIR = Path("/tmp/adv_clone/extracted")

# File download base URL on VPS
VPS_FILE_BASE = f"http://{VPS_IP}:{VPS_PORT}"


def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


class CloneInjectorV4:
    """API-first clone injector using discovered VMOS Cloud capabilities."""

    def __init__(self, client: VMOSCloudClient, pad: str):
        self.c = client
        self.pad = pad
        self.identity = {}

    async def cmd(self, command: str, timeout: int = 30) -> str:
        """Execute shell command with rate limiting."""
        await asyncio.sleep(CMD_DELAY)
        r = await self.c.sync_cmd(self.pad, command, timeout_sec=timeout)
        data = r.get("data", r)
        if isinstance(data, list):
            data = data[0] if data else {}
        if isinstance(data, dict):
            return data.get("errorMsg", "").strip()
        return str(data).strip()

    async def fire(self, command: str) -> str:
        """Fire async command (no wait for result)."""
        await asyncio.sleep(CMD_DELAY)
        r = await self.c.async_adb_cmd([self.pad], command)
        return str(r.get("data", {}).get("taskId", ""))

    async def load_identity(self):
        """Load extracted identity from VPS cache."""
        if not IDENTITY_FILE.exists():
            log(f"ERROR: Identity file not found: {IDENTITY_FILE}")
            sys.exit(1)
        self.identity = json.loads(IDENTITY_FILE.read_text())
        log(f"Loaded identity: {self.identity.get('ro.product.model', '?')} / "
            f"{self.identity.get('ro.product.brand', '?')}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: DISABLE GMS AUTHENTICATOR
    # ═══════════════════════════════════════════════════════════════════
    async def phase1_disable_gms(self):
        """Disable GMS account authenticator to prevent account removal on restart."""
        log("═══ PHASE 1: DISABLE GMS AUTHENTICATOR ═══")

        # Method: pm disable specific GMS account components
        # This prevents GoogleAccountAuthenticatorService from validating
        # injected accounts against Google servers
        gms_components = [
            "com.google.android.gms/com.google.android.gms.auth.account.authenticator.GoogleAccountAuthenticatorService",
            "com.google.android.gms/com.google.android.gms.auth.be.accountmigration.AccountMigrationService",
            "com.google.android.gms/.auth.GetToken",
        ]

        for comp in gms_components:
            r = await self.cmd(f"pm disable {comp}")
            log(f"  disable {comp.split('/')[-1]}: {r}")

        # Also freeze GMS entirely during injection window
        r = await self.cmd("pm disable-user --user 0 com.google.android.gms")
        log(f"  GMS disabled for user 0: {r}")

        # Verify
        r = await self.cmd("pm list packages -d | grep gms")
        log(f"  Disabled GMS packages: {r}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: INJECT IDENTITY VIA API (updatePadAndroidProp)
    # ═══════════════════════════════════════════════════════════════════
    async def phase2_inject_identity_api(self):
        """Use updatePadAndroidProp API for deep ro.* identity injection."""
        log("═══ PHASE 2: INJECT IDENTITY VIA API ═══")

        # Split identity into ro.* (need updatePadAndroidProp + restart)
        # and persist.* (need updatePadProperties, no restart)
        ro_props = {}
        persist_props = {}

        for key, value in self.identity.items():
            if not value or key in ("android_id", "gsf_id"):
                continue
            if key.startswith("ro."):
                ro_props[key] = str(value)
            elif key.startswith("persist."):
                persist_props[key] = str(value)

        # Also map standard identity fields to their cloud property names
        field_map = {
            "android_id": "ro.sys.cloud.android_id",
        }
        for field, prop in field_map.items():
            if field in self.identity and self.identity[field]:
                ro_props[prop] = str(self.identity[field])

        log(f"  ro.* properties to set: {len(ro_props)}")
        for k, v in ro_props.items():
            log(f"    {k} = {v}")

        # Use updatePadAndroidProp API — this is the DEEP write that
        # actually persists ro.* values (requires restart to apply)
        if ro_props:
            await asyncio.sleep(CMD_DELAY)
            r = await self.c.update_android_prop(self.pad, ro_props)
            log(f"  updatePadAndroidProp result: {r}")

        # Use updatePadProperties for persist.* (no restart needed)
        if persist_props:
            log(f"  persist.* properties to set: {len(persist_props)}")
            await asyncio.sleep(CMD_DELAY)
            r = await self.c.modify_instance_properties([self.pad], persist_props)
            log(f"  updatePadProperties result: {r}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: STAGE ACCOUNT DATABASE FILES
    # ═══════════════════════════════════════════════════════════════════
    async def phase3_stage_account_files(self):
        """Push account DB files to staging area on device via VPS download."""
        log("═══ PHASE 3: STAGE ACCOUNT FILES ON DEVICE ═══")

        # Files to inject and their target staging paths
        files = {
            "accounts_ce.db": "/data/local/tmp/adv_clone/inject/accounts_ce.db",
            "accounts_de.db": "/data/local/tmp/adv_clone/inject/accounts_de.db",
            "gservices.db": "/data/local/tmp/adv_clone/inject/gservices.db",
            "locksettings.db": "/data/local/tmp/adv_clone/inject/locksettings.db",
        }

        # Create staging directory
        await self.cmd("mkdir -p /data/local/tmp/adv_clone/inject")

        # Download each file from VPS to device staging
        for filename, target in files.items():
            source_url = f"{VPS_FILE_BASE}/{filename}"
            log(f"  Downloading {filename} from VPS...")
            # Use curl on device to download
            r = await self.cmd(
                f"curl -s -o {target} '{source_url}' && ls -la {target}",
                timeout=60
            )
            log(f"    Result: {r}")

        log("  All files staged.")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: ATOMIC ACCOUNT DB INJECTION (while GMS disabled)
    # ═══════════════════════════════════════════════════════════════════
    async def phase4_inject_accounts(self):
        """Inject account databases while GMS is disabled."""
        log("═══ PHASE 4: ATOMIC ACCOUNT INJECTION ═══")

        # Kill account-related services first
        log("  Killing system_server and GMS...")
        injection_script = """
# Stop account manager and system_server
am force-stop com.google.android.gms
am force-stop com.google.android.gsf

# Kill system_server — it will restart automatically
# But GMS authenticator is DISABLED so it won't validate accounts
kill $(pidof system_server)

# Wait for system_server to restart
sleep 3

# Copy staged files to system locations
# accounts_ce.db → /data/system_ce/0/
cp /data/local/tmp/adv_clone/inject/accounts_ce.db /data/system_ce/0/accounts_ce.db
chmod 600 /data/system_ce/0/accounts_ce.db
chown system:system /data/system_ce/0/accounts_ce.db

# accounts_de.db → /data/system_de/0/
cp /data/local/tmp/adv_clone/inject/accounts_de.db /data/system_de/0/accounts_de.db
chmod 600 /data/system_de/0/accounts_de.db
chown system:system /data/system_de/0/accounts_de.db

# gservices.db → GSF databases
cp /data/local/tmp/adv_clone/inject/gservices.db /data/data/com.google.android.gsf/databases/gservices.db
chown $(stat -c '%U:%G' /data/data/com.google.android.gsf/databases/) /data/data/com.google.android.gsf/databases/gservices.db
chmod 660 /data/data/com.google.android.gsf/databases/gservices.db

# Remove WAL/journal files that would overwrite our changes
rm -f /data/system_ce/0/accounts_ce.db-wal /data/system_ce/0/accounts_ce.db-journal
rm -f /data/system_de/0/accounts_de.db-wal /data/system_de/0/accounts_de.db-journal
rm -f /data/data/com.google.android.gsf/databases/gservices.db-wal
rm -f /data/data/com.google.android.gsf/databases/gservices.db-journal

# Verify
ls -la /data/system_ce/0/accounts_ce.db
ls -la /data/system_de/0/accounts_de.db
"""
        # Fire the injection script
        r = await self.fire(injection_script.strip())
        log(f"  Injection task fired: {r}")

        # Wait for system_server to come back
        log("  Waiting 15s for system_server restart...")
        await asyncio.sleep(15)

        # Verify files are in place
        r = await self.cmd("ls -la /data/system_ce/0/accounts_ce.db")
        log(f"  accounts_ce.db: {r}")

        r = await self.cmd("wc -c /data/system_ce/0/accounts_ce.db")
        log(f"  accounts_ce.db size: {r}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 5: SET ANDROID_ID AND GSF_ID AFTER RESTART
    # ═══════════════════════════════════════════════════════════════════
    async def phase5_post_restart_ids(self):
        """Set android_id and GSF settings_id via settings command after restart."""
        log("═══ PHASE 5: POST-RESTART ID INJECTION ═══")

        android_id = self.identity.get("android_id", "")
        gsf_id = self.identity.get("gsf_id", "")

        if android_id:
            r = await self.cmd(
                f"settings put secure android_id {android_id}"
            )
            log(f"  android_id set: {r}")

            # Also via content provider for persistence
            r = await self.cmd(
                f"content update --uri content://settings/secure "
                f"--where \"name='android_id'\" --bind value:s:{android_id}"
            )
            log(f"  android_id via content: {r}")

        # Verify android_id
        r = await self.cmd("settings get secure android_id")
        log(f"  Current android_id: {r}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 6: SELECTIVE GMS RE-ENABLE
    # ═══════════════════════════════════════════════════════════════════
    async def phase6_reenable_gms(self):
        """Re-enable GMS but keep authenticator components disabled longer."""
        log("═══ PHASE 6: SELECTIVE GMS RE-ENABLE ═══")

        # Re-enable GMS package but keep authenticator services disabled
        r = await self.cmd("pm enable com.google.android.gms")
        log(f"  GMS package re-enabled: {r}")

        # Keep the authenticator DISABLED - it's the one removing our accounts
        log("  NOTE: GoogleAccountAuthenticatorService remains DISABLED")
        log("  This prevents GMS from validating/removing the injected accounts")

        # Verify account state
        await asyncio.sleep(5)
        r = await self.cmd(
            "sqlite3 /data/system_ce/0/accounts_ce.db "
            "'SELECT _id, name, type FROM accounts'"
        )
        # sqlite3 might not be available, try alternative
        if not r or "not found" in r.lower():
            r = await self.cmd(
                "content query --uri content://com.android.contacts/raw_contacts --projection display_name"
            )
        log(f"  Account query result: {r}")

        # Check account via settings
        r = await self.cmd("dumpsys account 2>/dev/null | head -20")
        log(f"  Account dump: {r}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 7: VERIFICATION
    # ═══════════════════════════════════════════════════════════════════
    async def phase7_verify(self):
        """Comprehensive verification of cloned state."""
        log("═══ PHASE 7: VERIFICATION ═══")

        checks = [
            ("Identity Model", "getprop ro.product.model"),
            ("Identity Brand", "getprop ro.product.brand"),
            ("Identity Fingerprint", "getprop ro.build.fingerprint"),
            ("Android ID", "settings get secure android_id"),
            ("accounts_ce.db size", "wc -c /data/system_ce/0/accounts_ce.db"),
            ("accounts_de.db size", "wc -c /data/system_de/0/accounts_de.db"),
            ("GMS state", "pm list packages -d | grep gms"),
            ("Account authenticator state",
             "pm dump com.google.android.gms | grep -A2 GoogleAccountAuthenticator | head -5"),
        ]

        results = {}
        for label, cmd_str in checks:
            r = await self.cmd(cmd_str)
            results[label] = r
            log(f"  {label}: {r}")

        return results

    # ═══════════════════════════════════════════════════════════════════
    # ALTERNATIVE: uploadFileV3 API for direct file push
    # ═══════════════════════════════════════════════════════════════════
    async def upload_file_via_api(self, file_url: str, target_path: str):
        """Use VMOS uploadFileV3 API to push file from URL to device path."""
        log(f"  uploadFileV3: {file_url} → {target_path}")
        await asyncio.sleep(CMD_DELAY)
        r = await self.c.upload_file_via_url(
            [self.pad], file_url,
            filePath=target_path,
        )
        task_id = r.get("data", {}).get("taskId")
        log(f"    Task: {task_id}")
        return task_id

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3-ALT: Use uploadFileV3 API instead of curl
    # ═══════════════════════════════════════════════════════════════════
    async def phase3_stage_via_api(self):
        """Push account files using VMOS uploadFileV3 API (URL → device path)."""
        log("═══ PHASE 3-ALT: STAGE FILES VIA uploadFileV3 API ═══")

        files = {
            "accounts_ce.db": "/data/local/tmp/adv_clone/inject/accounts_ce.db",
            "accounts_de.db": "/data/local/tmp/adv_clone/inject/accounts_de.db",
            "gservices.db": "/data/local/tmp/adv_clone/inject/gservices.db",
            "locksettings.db": "/data/local/tmp/adv_clone/inject/locksettings.db",
        }

        # Create staging dir
        await self.cmd("mkdir -p /data/local/tmp/adv_clone/inject")

        tasks = []
        for filename, target in files.items():
            file_url = f"{VPS_FILE_BASE}/{filename}"
            task_id = await self.upload_file_via_api(file_url, target)
            if task_id:
                tasks.append((filename, task_id))

        # Poll task completion
        for filename, task_id in tasks:
            log(f"  Polling {filename} upload task {task_id}...")
            for _ in range(10):
                await asyncio.sleep(5)
                try:
                    r = await self.c.file_task_detail([int(task_id)])
                    status = r.get("data", [{}])[0].get("taskStatus", "")
                    if status in ("3", "completed", "Completed"):
                        log(f"    {filename}: COMPLETED")
                        break
                    log(f"    {filename}: {status}")
                except Exception as e:
                    log(f"    Poll error: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # MAIN EXECUTOR
    # ═══════════════════════════════════════════════════════════════════
    async def run_full_injection(self):
        """Execute complete clone injection pipeline."""
        log("╔══════════════════════════════════════════════════╗")
        log("║  CLONE INJECTION v4.0 — API-FIRST + GMS GATE   ║")
        log("╚══════════════════════════════════════════════════╝")

        await self.load_identity()

        # Phase 1: Disable GMS authenticator (prevents account removal)
        await self.phase1_disable_gms()

        # Phase 2: Inject identity via API (ro.* via updatePadAndroidProp)
        # This TRIGGERS A RESTART — but GMS is disabled so accounts safe
        await self.phase2_inject_identity_api()

        # Wait for device restart from updatePadAndroidProp
        log("  Waiting 45s for device restart after identity injection...")
        await asyncio.sleep(45)

        # Phase 3: Stage account files on device
        await self.phase3_stage_account_files()

        # Phase 4: Inject account databases (while GMS still disabled)
        await self.phase4_inject_accounts()

        # Phase 5: Set android_id after restart
        await self.phase5_post_restart_ids()

        # Phase 6: Selectively re-enable GMS
        await self.phase6_reenable_gms()

        # Phase 7: Verify
        results = await self.phase7_verify()

        log("\n═══ INJECTION COMPLETE ═══")
        return results

    async def run_identity_only(self):
        """Identity injection only (no account DBs)."""
        await self.load_identity()
        await self.phase2_inject_identity_api()
        log("  Identity injected. Device will restart for ro.* changes.")

    async def run_accounts_only(self):
        """Account injection only (assumes identity already set)."""
        await self.load_identity()
        await self.phase1_disable_gms()
        await self.phase3_stage_account_files()
        await self.phase4_inject_accounts()
        await self.phase5_post_restart_ids()
        await self.phase6_reenable_gms()
        await self.phase7_verify()

    async def run_verify(self):
        """Verify current clone state."""
        await self.load_identity()
        await self.phase7_verify()


async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
    injector = CloneInjectorV4(client, PAD)

    try:
        if mode == "--identity-only":
            await injector.run_identity_only()
        elif mode == "--accounts-only":
            await injector.run_accounts_only()
        elif mode == "--verify":
            await injector.run_verify()
        else:
            await injector.run_full_injection()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
