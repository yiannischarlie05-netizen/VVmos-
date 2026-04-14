#!/usr/bin/env python3
"""
VMOS Android 15 OS Clone Deployer v1.0

Deploys extracted Android 15 OS images to create a fully cloned
VMOS container device. Works with images extracted by extract_os_image.py.

Three deployment methods:
  1. VPS Docker Registry → VMOS Edge API create_instance
  2. VMOS Cloud local_backup/local_restore with S3 (MinIO)
  3. Direct partition restore via dd (same-host clone)

Usage:
  # Method 1: Upload extracted images to VPS, push to Docker registry,
  #           then create new VMOS Edge instance from that image
  python3 scripts/clone_os_image.py --method registry \
    --vps YOUR_OLLAMA_HOST --source-pad APP6476KYH9KMLU5

  # Method 2: Use VMOS Cloud backup/restore API with S3
  python3 scripts/clone_os_image.py --method s3-restore \
    --s3-endpoint http://YOUR_OLLAMA_HOST:9000 \
    --s3-access-key minioadmin --s3-secret-key minioadmin \
    --source-pad APP6476KYH9KMLU5 --target-pad <target_pad>

  # Method 3: Direct dd restore from staged images (same device or neighbor)
  python3 scripts/clone_os_image.py --method direct \
    --source-pad APP6476KYH9KMLU5 --target-pad <target_pad>

  # Step 0: Download extracted images from device to local machine
  python3 scripts/clone_os_image.py --download-only \
    --source-pad APP6476KYH9KMLU5 --output-dir ./extracted_images
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ═══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
API_BASE = "https://api.vmoscloud.com"

CMD_DELAY = 3.5  # seconds between API calls
STAGING_DIR = "/data/local/tmp/os_extract"

SYSTEM_PARTITIONS = ["system", "system_ext", "product", "vendor", "odm"]


# ═══════════════════════════════════════════════════════════════════════
# BRIDGE (same pattern as extract script)
# ═══════════════════════════════════════════════════════════════════════

class CloneBridge:
    """Thin wrapper around VMOSCloudClient for rate-limited ops."""

    def __init__(self, client: VMOSCloudClient, pad: str):
        self.client = client
        self.pad = pad
        self._last_cmd = 0.0
        self._cmd_count = 0

    async def _throttle(self):
        elapsed = time.time() - self._last_cmd
        if elapsed < CMD_DELAY:
            await asyncio.sleep(CMD_DELAY - elapsed)

    async def cmd(self, command: str, timeout: int = 30) -> str:
        await self._throttle()
        self._last_cmd = time.time()
        self._cmd_count += 1
        try:
            r = await asyncio.wait_for(
                self.client.sync_cmd(self.pad, command, timeout_sec=timeout),
                timeout=timeout + 15,
            )
            data = r.get("data", [])
            if isinstance(data, list) and data:
                return (data[0].get("errorMsg", "") or "").strip()
            elif isinstance(data, dict):
                return (data.get("errorMsg", "") or "").strip()
            return ""
        except asyncio.TimeoutError:
            return "ERR:api_timeout"
        except Exception as e:
            return f"ERR:{e}"

    async def fire(self, command: str):
        await self._throttle()
        self._last_cmd = time.time()
        self._cmd_count += 1
        try:
            await self.client.async_adb_cmd([self.pad], command)
        except Exception:
            pass

    @property
    def api_calls(self) -> int:
        return self._cmd_count


# ═══════════════════════════════════════════════════════════════════════
# METHOD 0: DOWNLOAD IMAGES FROM DEVICE TO LOCAL MACHINE
# ═══════════════════════════════════════════════════════════════════════

async def download_images(pad_code: str, output_dir: str):
    """Download extracted images from device staging dir to local machine.

    Uses the VPS as an intermediate relay: device → curl PUT → VPS → local wget.
    Or if images are already on VPS, downloads directly.
    """
    print(f"\n{'='*60}")
    print(f"  Downloading Extracted Images from {pad_code}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}")

    client = VMOSCloudClient(ak=AK, sk=SK, base_url=API_BASE)
    bridge = CloneBridge(client, pad_code)

    os.makedirs(output_dir, exist_ok=True)

    # Get manifest from device
    print("\n[1] Reading manifest from device...")
    manifest_raw = await bridge.cmd(f"cat {STAGING_DIR}/manifest.json")
    if not manifest_raw or manifest_raw.startswith("ERR:"):
        print(f"  ✗ Cannot read manifest: {manifest_raw}")
        return

    try:
        manifest = json.loads(manifest_raw)
    except json.JSONDecodeError:
        # Manifest might be truncated in single cmd - try reading in parts
        print("  Manifest too large for single read, reading partitions individually...")
        manifest = None

    # Save manifest
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        f.write(manifest_raw)
    print(f"  ✓ Manifest saved to {manifest_path}")

    # List files in staging dir
    files_raw = await bridge.cmd(f"ls -la {STAGING_DIR}/")
    print(f"\n[2] Staged files on device:")
    for line in files_raw.split("\n"):
        if line.strip():
            print(f"    {line.strip()}")

    # Method: Upload from device to VPS via curl, then download from VPS
    print(f"\n[3] Download strategy:")
    print(f"    The images are on the cloud device at {STAGING_DIR}/")
    print(f"    Total ~1.5GB compressed across 5 partitions")
    print(f"")
    print(f"    To retrieve them, use one of these methods:")
    print(f"")
    print(f"    A) Upload to VPS first (from device shell):")
    print(f"       Run: python3 scripts/extract_os_image.py \\")
    print(f"            --pad {pad_code} --vps YOUR_OLLAMA_HOST:18999 \\")
    print(f"            --partitions system,system_ext,product,vendor,odm")
    print(f"       Then: wget http://YOUR_OLLAMA_HOST:18999/os_extract/<file>.img.gz")
    print(f"")
    print(f"    B) Use VMOS Cloud file transfer API:")
    print(f"       await client.pull_file('{pad_code}', '{STAGING_DIR}/system.img.gz')")
    print(f"")
    print(f"    C) ADB pull (if ADB enabled):")
    print(f"       adb -s <device_ip>:5555 pull {STAGING_DIR}/ {output_dir}/")

    # Check if we can use the file transfer API
    print(f"\n[4] Checking VMOS Cloud file transfer capability...")
    try:
        # Try to get file download URL
        r = await client.get_long_generate_url([pad_code])
        print(f"    File transfer response: {json.dumps(r, indent=2)[:200]}")
    except Exception as e:
        print(f"    File transfer API: {e}")

    print(f"\n  ✓ Manifest and file list saved to {output_dir}/")
    print(f"  Total API calls: {bridge.api_calls}")


# ═══════════════════════════════════════════════════════════════════════
# METHOD 1: VPS DOCKER REGISTRY → VMOS EDGE create_instance
# ═══════════════════════════════════════════════════════════════════════

async def clone_via_registry(source_pad: str, vps_host: str,
                             vps_port: int = 18999, registry_port: int = 5000):
    """
    Clone by building a Docker image from extracted partitions and pushing
    to a registry, then creating a new VMOS Edge instance from that image.

    Flow:
    1. Upload partition images from device → VPS via curl PUT
    2. On VPS: build Docker/OCI image from partitions
    3. Push to registry at vps_host:registry_port
    4. Call VMOS Edge API to create instance with that image

    Prerequisites:
    - VPS has Docker installed
    - VPS has a Docker registry running on registry_port
    - Partition images already extracted on device
    """
    print(f"\n{'='*60}")
    print(f"  Clone via Docker Registry")
    print(f"  Source: {source_pad}")
    print(f"  VPS: {vps_host}:{vps_port}")
    print(f"  Registry: {vps_host}:{registry_port}")
    print(f"{'='*60}")

    client = VMOSCloudClient(ak=AK, sk=SK, base_url=API_BASE)
    source_bridge = CloneBridge(client, source_pad)

    # Step 1: Upload images to VPS
    print(f"\n[1/5] Uploading partition images to VPS...")
    vps_url = f"http://{vps_host}:{vps_port}/os_extract"

    for part in SYSTEM_PARTITIONS:
        device_path = f"{STAGING_DIR}/{part}.img.gz"
        filename = f"{part}.img.gz"

        # Check if file exists
        size_str = await source_bridge.cmd(f"wc -c < {device_path} 2>/dev/null")
        try:
            size = int(size_str.strip())
        except (ValueError, AttributeError):
            print(f"  ✗ {part}: not found on device")
            continue

        if size == 0:
            print(f"  ✗ {part}: empty file")
            continue

        print(f"  Uploading {filename} ({size:,} bytes)...")

        # Fire upload in background
        await source_bridge.fire(
            f"nohup curl -s -X PUT -H 'Content-Type: application/octet-stream' "
            f"--data-binary @{device_path} '{vps_url}/{filename}' "
            f"> {device_path}.upload.log 2>&1 &"
        )

        # Poll for upload completion
        uploaded = False
        for _ in range(240):  # up to 20 min for large files
            await asyncio.sleep(5)
            result = await source_bridge.cmd(f"cat {device_path}.upload.log 2>/dev/null")
            if result and ("OK" in result or "200" in result or len(result) > 10):
                print(f"  ✓ {filename} uploaded ({size:,} bytes)")
                await source_bridge.cmd(f"rm -f {device_path}.upload.log")
                uploaded = True
                break
            if result and "ERR" in result:
                print(f"  ✗ {filename} upload failed: {result[:100]}")
                break

        if not uploaded:
            print(f"  ⚠ {filename} upload status unclear, continuing...")

    # Upload manifest
    print(f"  Uploading manifest.json...")
    await source_bridge.fire(
        f"nohup curl -s -X PUT -H 'Content-Type: application/json' "
        f"--data-binary @{STAGING_DIR}/manifest.json '{vps_url}/manifest.json' "
        f"> {STAGING_DIR}/manifest.upload.log 2>&1 &"
    )
    await asyncio.sleep(10)

    # Step 2: Build Docker image on VPS
    print(f"\n[2/5] Building Docker image on VPS...")
    print(f"  This step requires SSH access to the VPS to run:")
    print(f"")
    print(f"  # On VPS ({vps_host}):")
    print(f"  cd /path/to/uploaded/images")
    print(f"  # Decompress all partition images")
    print(f"  for f in *.img.gz; do gunzip \"$f\"; done")
    print(f"")
    print(f"  # Create Dockerfile for VMOS-compatible container")
    print(f"  cat > Dockerfile << 'EOF'")
    print(f"  FROM scratch")
    print(f"  COPY system.img /images/system.img")
    print(f"  COPY system_ext.img /images/system_ext.img")
    print(f"  COPY product.img /images/product.img")
    print(f"  COPY vendor.img /images/vendor.img")
    print(f"  COPY odm.img /images/odm.img")
    print(f"  EOF")
    print(f"")
    print(f"  docker build -t {vps_host}:{registry_port}/armcloud-proxy/armcloud/clone-img:latest .")
    print(f"  docker push {vps_host}:{registry_port}/armcloud-proxy/armcloud/clone-img:latest")

    # Step 3: Generate the VMOS Edge API call
    print(f"\n[3/5] VMOS Edge API create_instance command:")
    print(f"  POST http://<edge_host>:18182/container_api/v1/create")
    print(f"  Body: {{")
    print(f'    "user_name": "android15-clone",')
    print(f'    "bool_start": true,')
    print(f'    "image_repository": "{vps_host}:{registry_port}/armcloud-proxy/armcloud/clone-img:latest"')
    print(f"  }}")

    print(f"\n  Total API calls: {source_bridge.api_calls}")


# ═══════════════════════════════════════════════════════════════════════
# METHOD 2: S3 BACKUP/RESTORE
# ═══════════════════════════════════════════════════════════════════════

async def clone_via_s3(source_pad: str, target_pad: str,
                       s3_endpoint: str, s3_access_key: str,
                       s3_secret_key: str, s3_bucket: str = "vmos-backups"):
    """
    Clone using VMOS Cloud local_backup/local_restore with S3-compatible
    storage (MinIO).

    Flow:
    1. Set up MinIO on VPS with bucket
    2. Call local_backup API on source → streams device to S3
    3. Call local_restore API on target → restores from S3

    This is the most complete method as it captures the full device state
    including /data partition through VMOS's native backup mechanism.
    """
    print(f"\n{'='*60}")
    print(f"  Clone via S3 Backup/Restore")
    print(f"  Source: {source_pad}")
    print(f"  Target: {target_pad}")
    print(f"  S3: {s3_endpoint}")
    print(f"{'='*60}")

    client = VMOSCloudClient(ak=AK, sk=SK, base_url=API_BASE)

    oss_config = {
        "ossEndpoint": s3_endpoint,
        "ossAccessKeyId": s3_access_key,
        "ossAccessKeySecret": s3_secret_key,
        "ossBucketName": s3_bucket,
    }

    # Step 1: Set up MinIO (instructions)
    print(f"\n[1/4] MinIO Setup (run on VPS if not already done):")
    print(f"  docker run -d --name minio \\")
    print(f"    -p 9000:9000 -p 9001:9001 \\")
    print(f"    -e MINIO_ROOT_USER={s3_access_key} \\")
    print(f"    -e MINIO_ROOT_PASSWORD={s3_secret_key} \\")
    print(f"    minio/minio server /data --console-address :9001")
    print(f"")
    print(f"  # Create bucket:")
    print(f"  mc alias set vmos {s3_endpoint} {s3_access_key} {s3_secret_key}")
    print(f"  mc mb vmos/{s3_bucket}")

    # Step 2: Trigger backup
    print(f"\n[2/4] Triggering local backup of {source_pad}...")
    try:
        backup_result = await client.local_backup(source_pad, oss_config)
        print(f"  Backup response: {json.dumps(backup_result, indent=2)[:300]}")

        if backup_result.get("code") == 200:
            print(f"  ✓ Backup initiated successfully")
        else:
            print(f"  ✗ Backup failed: {backup_result.get('msg', 'unknown error')}")
            print(f"  Full response: {json.dumps(backup_result, indent=2)}")
            return
    except Exception as e:
        print(f"  ✗ Backup API error: {e}")
        return

    # Step 3: Wait for backup completion
    print(f"\n[3/4] Waiting for backup to complete...")
    print(f"  (Polling backup list for completion status...)")

    for i in range(120):  # up to 20 minutes
        await asyncio.sleep(10)
        try:
            backups = await client.local_backup_list(page=1, rows=10)
            backup_data = backups.get("data", {})
            if isinstance(backup_data, dict):
                rows = backup_data.get("rows", [])
                if rows:
                    latest = rows[0]
                    status = latest.get("status", "")
                    print(f"  [{i*10}s] Backup status: {status}")
                    if status in ("completed", "success", "done", "3"):
                        print(f"  ✓ Backup completed")
                        break
                    if status in ("failed", "error"):
                        print(f"  ✗ Backup failed")
                        return
        except Exception as e:
            print(f"  [{i*10}s] Poll error: {e}")
    else:
        print(f"  ⚠ Backup poll timeout — check manually")
        return

    # Step 4: Restore to target
    print(f"\n[4/4] Restoring backup to {target_pad}...")
    try:
        restore_result = await client.local_restore(target_pad, oss_config)
        print(f"  Restore response: {json.dumps(restore_result, indent=2)[:300]}")

        if restore_result.get("code") == 200:
            print(f"  ✓ Restore initiated — target device will reboot with cloned image")
        else:
            print(f"  ✗ Restore failed: {restore_result.get('msg', 'unknown error')}")
    except Exception as e:
        print(f"  ✗ Restore API error: {e}")


# ═══════════════════════════════════════════════════════════════════════
# METHOD 3: DIRECT PARTITION RESTORE (dd)
# ═══════════════════════════════════════════════════════════════════════

async def clone_via_direct(source_pad: str, target_pad: str):
    """
    Clone by transferring partition images from source device to target
    device via VPS relay and restoring via dd.

    Flow:
    1. Source device stages compressed partition images
    2. Upload images to VPS via curl PUT
    3. Target device downloads from VPS via curl GET
    4. Decompress and dd images to matching partitions
    5. Sync and reboot target

    ⚠ WARNING: This writes raw partition images to the target device.
    The target must have matching partition layout (same VMOS image version).
    System partitions are read-only, so this method only works for data cloning
    unless the device is freshly provisioned with the same base image.
    """
    print(f"\n{'='*60}")
    print(f"  Clone via Direct Partition Restore")
    print(f"  Source: {source_pad}")
    print(f"  Target: {target_pad}")
    print(f"{'='*60}")

    client = VMOSCloudClient(ak=AK, sk=SK, base_url=API_BASE)
    source = CloneBridge(client, source_pad)
    target = CloneBridge(client, target_pad)

    # Step 1: Get partition maps from both devices
    print(f"\n[1/5] Discovering partition layouts...")

    # Source partition map
    source_mountinfo = await source.cmd("cat /proc/self/mountinfo")
    source_map = _parse_mountinfo(source_mountinfo)
    print(f"  Source: {len(source_map)} partitions discovered")

    # Target partition map
    target_mountinfo = await target.cmd("cat /proc/self/mountinfo")
    target_map = _parse_mountinfo(target_mountinfo)
    print(f"  Target: {len(target_map)} partitions discovered")

    # Check compatibility
    source_image = await source.cmd("getprop ro.boot.container.image")
    target_image = await target.cmd("getprop ro.boot.container.image")

    print(f"\n[2/5] Compatibility check:")
    print(f"  Source image: {source_image}")
    print(f"  Target image: {target_image}")

    if source_image and target_image and source_image == target_image:
        print(f"  ✓ Same base image — partition layout compatible")
    else:
        print(f"  ⚠ Different base images — proceeding with data-only clone")
        print(f"    (System partitions are read-only and identical if same image version)")

    # Step 3: Transfer data partition
    print(f"\n[3/5] Extracting source /data partition state...")
    print(f"  Note: Full /data clone on VMOS would be 57GB.")
    print(f"  Using selective clone (accounts, apps, settings)...")

    # Create selective data tar on source
    data_paths = [
        "system/users",
        "system_ce/0",
        "system_de/0",
        "misc/wifi",
        "misc/bluedroid",
        "data/com.google.android.gms",
        "data/com.google.android.gsf",
        "data/com.android.vending",
        "data/com.android.providers.contacts",
        "data/com.android.providers.telephony",
        "data/com.android.chrome",
    ]

    tar_paths = " ".join(data_paths)
    data_tar = f"{STAGING_DIR}/data_selective.tar.gz"

    print(f"  Creating selective data archive...")
    await source.fire(
        f"nohup sh -c 'cd /data && tar czf {data_tar} "
        f"{tar_paths} 2>/dev/null && echo DONE > {data_tar}.status' "
        f"> /dev/null 2>&1 &"
    )

    # Wait for tar
    for _ in range(60):
        await asyncio.sleep(10)
        status = await source.cmd(f"cat {data_tar}.status 2>/dev/null")
        if status and "DONE" in status:
            break

    size_str = await source.cmd(f"wc -c < {data_tar} 2>/dev/null")
    try:
        tar_size = int(size_str.strip())
    except (ValueError, AttributeError):
        tar_size = 0

    print(f"  ✓ Data archive: {tar_size:,} bytes")

    # Step 4: Transfer via VPS
    print(f"\n[4/5] Transferring data archive to target...")
    vps_url = "http://YOUR_OLLAMA_HOST:18999/clone_transfer"

    # Upload from source
    await source.fire(
        f"nohup curl -s -X PUT -H 'Content-Type: application/octet-stream' "
        f"--data-binary @{data_tar} '{vps_url}/data_selective.tar.gz' "
        f"> {data_tar}.upload.log 2>&1 &"
    )

    for _ in range(120):
        await asyncio.sleep(5)
        result = await source.cmd(f"cat {data_tar}.upload.log 2>/dev/null")
        if result and len(result) > 5:
            print(f"  ✓ Source → VPS upload complete")
            break

    # Download to target
    target_staging = "/data/local/tmp/clone_restore"
    await target.cmd(f"mkdir -p {target_staging}")

    await target.fire(
        f"nohup curl -s -o {target_staging}/data_selective.tar.gz "
        f"'{vps_url}/data_selective.tar.gz' "
        f"> {target_staging}/download.log 2>&1 &"
    )

    for _ in range(120):
        await asyncio.sleep(5)
        target_size = await target.cmd(
            f"wc -c < {target_staging}/data_selective.tar.gz 2>/dev/null"
        )
        try:
            t_size = int(target_size.strip())
        except (ValueError, AttributeError):
            t_size = 0
        if t_size >= tar_size * 0.95:  # Allow small variance
            print(f"  ✓ VPS → Target download complete ({t_size:,} bytes)")
            break

    # Step 5: Restore on target
    print(f"\n[5/5] Restoring data on target device...")
    await target.fire(
        f"nohup sh -c 'cd /data && tar xzf {target_staging}/data_selective.tar.gz "
        f"2>/dev/null && echo RESTORED > {target_staging}/restore.status' "
        f"> /dev/null 2>&1 &"
    )

    for _ in range(60):
        await asyncio.sleep(10)
        status = await target.cmd(f"cat {target_staging}/restore.status 2>/dev/null")
        if status and "RESTORED" in status:
            print(f"  ✓ Data restored successfully")
            break

    # Fix permissions
    print(f"  Fixing permissions...")
    await target.cmd("restorecon -RF /data/system /data/system_ce /data/system_de")
    await target.cmd(f"rm -rf {target_staging}")

    print(f"\n{'='*60}")
    print(f"  CLONE COMPLETE")
    print(f"{'='*60}")
    print(f"  Source: {source_pad}")
    print(f"  Target: {target_pad}")
    print(f"  Data transferred: {tar_size:,} bytes")
    print(f"  API calls: {source.api_calls + target.api_calls}")
    print(f"\n  Note: Reboot target device for changes to take effect.")
    print(f"  If accounts need re-registration, run Genesis pipeline.")


# ═══════════════════════════════════════════════════════════════════════
# METHOD 4: GENERATE DOCKER BUILD SCRIPTS (Local Reconstruction)
# ═══════════════════════════════════════════════════════════════════════

async def generate_docker_build(source_pad: str, output_dir: str):
    """
    Generate all scripts needed to reconstruct a Docker/OCI container
    image from the extracted partition images.

    Output:
    - Dockerfile
    - docker-compose.yml
    - build.sh (build + push script)
    - deploy.sh (VMOS Edge create_instance)
    - README.md (instructions)
    """
    print(f"\n{'='*60}")
    print(f"  Generating Docker Build Scripts")
    print(f"  Source: {source_pad}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}")

    client = VMOSCloudClient(ak=AK, sk=SK, base_url=API_BASE)
    bridge = CloneBridge(client, source_pad)

    os.makedirs(output_dir, exist_ok=True)

    # Get manifest — read individual fields to avoid API truncation
    print("\n[1/3] Reading extraction manifest...")
    model = (await bridge.cmd("getprop ro.product.model")).strip() or "unknown"
    android = (await bridge.cmd("getprop ro.build.version.release")).strip() or "15"
    container_ver = (await bridge.cmd("getprop ro.boot.container.software")).strip() or "unknown"
    image_id = (await bridge.cmd(
        f"grep -o '\"image_id\":[[:space:]]*\"[^\"]*\"' {STAGING_DIR}/manifest.json 2>/dev/null"
    )).strip()
    if '"image_id"' in image_id:
        image_id = image_id.split('"')[-2]
    else:
        image_id = (await bridge.cmd("getprop ro.boot.container.image")).strip() or "unknown"

    # Also try to read the full manifest for partition info
    manifest_raw = await bridge.cmd(f"cat {STAGING_DIR}/manifest.json", timeout=60)
    manifest = {}
    if manifest_raw and not manifest_raw.startswith("ERR:"):
        try:
            manifest = json.loads(manifest_raw)
        except json.JSONDecodeError:
            pass

    source_info = manifest.get("source_device", {})

    # Get partition sizes for Dockerfile
    partitions = manifest.get("partitions", {})

    print(f"  Source: {model} | Android {android}")
    print(f"  Image: {image_id}")
    print(f"  Container: {container_ver}")

    # Generate Dockerfile
    print("\n[2/3] Generating build scripts...")

    dockerfile = f"""# VMOS Android 15 Clone Container Image
# Source: {model} ({source_pad})
# Original Image: {image_id}
# Container Version: {container_ver}
# Generated by: clone_os_image.py

FROM scratch

# Partition images (gunzipped ext4/f2fs raw images)
COPY images/system.img /images/system.img
COPY images/system_ext.img /images/system_ext.img
COPY images/product.img /images/product.img
COPY images/vendor.img /images/vendor.img
COPY images/odm.img /images/odm.img

# Optional: data overlay
# COPY images/data_selective.tar.gz /images/data_selective.tar.gz

# Metadata
LABEL source.model="{model}"
LABEL source.android="{android}"
LABEL source.container="{container_ver}"
LABEL source.pad="{source_pad}"
LABEL type="vmos_android15_clone"
"""

    build_sh = f"""#!/bin/bash
# Build and push VMOS Android 15 clone container image
# Usage: ./build.sh [registry_host:port]

set -e

REGISTRY="${{1:-localhost:5000}}"
IMAGE_NAME="armcloud-proxy/armcloud/clone-{source_pad.lower()}"
IMAGE_TAG="latest"
FULL_TAG="${{REGISTRY}}/${{IMAGE_NAME}}:${{IMAGE_TAG}}"

echo "=== VMOS Android 15 Clone Image Builder ==="
echo "Registry: $REGISTRY"
echo "Image: $FULL_TAG"
echo ""

# Step 1: Decompress partition images
echo "[1/4] Decompressing partition images..."
mkdir -p images
for gz in *.img.gz; do
    name=$(basename "$gz" .img.gz)
    if [ ! -f "images/$name.img" ]; then
        echo "  Decompressing $gz..."
        gunzip -c "$gz" > "images/$name.img"
    else
        echo "  images/$name.img already exists"
    fi
done

# Step 2: Build Docker image
echo ""
echo "[2/4] Building Docker image..."
docker build -t "$FULL_TAG" .

# Step 3: Push to registry
echo ""
echo "[3/4] Pushing to registry..."
docker push "$FULL_TAG"

# Step 4: Verify
echo ""
echo "[4/4] Verifying..."
docker manifest inspect "$FULL_TAG" 2>/dev/null || echo "Image pushed (manifest inspect may not be available)"

echo ""
echo "=== BUILD COMPLETE ==="
echo "Image: $FULL_TAG"
echo ""
echo "To deploy via VMOS Edge API:"
echo "  curl -X POST http://<edge_host>:18182/container_api/v1/create \\\\"
echo "    -H 'Content-Type: application/json' \\\\"
echo "    -d '{{\\"user_name\\": \\"clone\\", \\"bool_start\\": true, \\"image_repository\\": \\"'$FULL_TAG'\\"}}'"
"""

    deploy_sh = f"""#!/bin/bash
# Deploy cloned VMOS container to Edge instance
# Usage: ./deploy.sh <edge_host_ip> [registry_host:port]

set -e

EDGE_HOST="${{1:?Usage: ./deploy.sh <edge_host_ip> [registry:port]}}"
REGISTRY="${{2:-localhost:5000}}"
IMAGE_NAME="armcloud-proxy/armcloud/clone-{source_pad.lower()}"
IMAGE_TAG="latest"
FULL_TAG="${{REGISTRY}}/${{IMAGE_NAME}}:${{IMAGE_TAG}}"

echo "=== VMOS Edge Clone Deployer ==="
echo "Edge Host: $EDGE_HOST"
echo "Image: $FULL_TAG"
echo ""

# Create instance
echo "[1/2] Creating VMOS Edge instance..."
RESPONSE=$(curl -s -X POST "http://${{EDGE_HOST}}:18182/container_api/v1/create" \\
    -H "Content-Type: application/json" \\
    -d '{{
        "user_name": "android15-clone-{model.lower().replace(' ','-')}",
        "bool_start": true,
        "image_repository": "'$FULL_TAG'",
        "resolution": "1440x3120",
        "count": 1
    }}')

echo "  Response: $RESPONSE"

# Extract db_id
DB_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{{}}).get('db_id',''))" 2>/dev/null || echo "")

if [ -n "$DB_ID" ]; then
    echo ""
    echo "[2/2] Instance created!"
    echo "  DB ID: $DB_ID"
    echo ""
    echo "  Check status: curl -s http://${{EDGE_HOST}}:18182/container_api/v1/list"
    echo "  ADB connect:  adb connect ${{EDGE_HOST}}:<adb_port>"
else
    echo ""
    echo "  ⚠ Could not extract db_id from response"
    echo "  Check Edge API logs for details"
fi
"""

    readme = f"""# VMOS Android 15 Clone — {model}

## Source Device
- **PAD Code**: {source_pad}
- **Model**: {model}
- **Android**: {android}
- **Container**: {container_ver}
- **Original Image**: {image_id}

## Files
| File | Description | Size (compressed) |
|---|---|---|
| system.img.gz | Main Android system partition | ~1.15 GB |
| system_ext.img.gz | System extensions | ~102 MB |
| product.img.gz | Product overlay | ~210 MB |
| vendor.img.gz | Vendor HAL | ~73 MB |
| odm.img.gz | ODM customization | ~250 KB |
| manifest.json | Extraction metadata | ~2 KB |
| Dockerfile | Docker build template | Generated |
| build.sh | Build + push script | Generated |
| deploy.sh | VMOS Edge deploy script | Generated |

## Deployment Methods

### Method 1: VMOS Edge API (Docker Registry)
```bash
# 1. Start a Docker registry on your server
docker run -d -p 5000:5000 --name registry registry:2

# 2. Build and push the clone image
./build.sh localhost:5000

# 3. Deploy to VMOS Edge
./deploy.sh <edge_host_ip> localhost:5000
```

### Method 2: VMOS Cloud Backup/Restore (S3)
```bash
# 1. Set up MinIO
docker run -d -p 9000:9000 -p 9001:9001 \\
  -e MINIO_ROOT_USER=minioadmin \\
  -e MINIO_ROOT_PASSWORD=minioadmin \\
  minio/minio server /data --console-address :9001

# 2. Run backup/restore
python3 scripts/clone_os_image.py --method s3-restore \\
  --s3-endpoint http://your-server:9000 \\
  --s3-access-key minioadmin --s3-secret-key minioadmin \\
  --source-pad {source_pad} --target-pad <target_pad>
```

### Method 3: Manual Partition Restore
```bash
# 1. Decompress images
for f in *.img.gz; do gunzip "$f"; done

# 2. Mount read-only to inspect
sudo mkdir -p /mnt/android_clone/system
sudo mount -o ro,loop system.img /mnt/android_clone/system

# 3. Or write to loop device on target
dd if=system.img of=/dev/block/loop3840 bs=1M
```

### Method 4: Direct Device-to-Device Clone
```bash
python3 scripts/clone_os_image.py --method direct \\
  --source-pad {source_pad} --target-pad <target_pad>
```

## Notes
- System partitions (system, system_ext, product, vendor, odm) are read-only
- All devices using the same VMOS image version share identical system partitions
- The unique state is in the /data partition (accounts, apps, settings)
- For full cloning, use S3 backup/restore (Method 2) or direct clone (Method 4)
"""

    # Write files
    with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile)

    with open(os.path.join(output_dir, "build.sh"), "w") as f:
        f.write(build_sh)
    os.chmod(os.path.join(output_dir, "build.sh"), 0o755)

    with open(os.path.join(output_dir, "deploy.sh"), "w") as f:
        f.write(deploy_sh)
    os.chmod(os.path.join(output_dir, "deploy.sh"), 0o755)

    with open(os.path.join(output_dir, "README.md"), "w") as f:
        f.write(readme)

    print(f"\n[3/3] Files generated:")
    for name in ["Dockerfile", "build.sh", "deploy.sh", "README.md"]:
        print(f"    ✓ {output_dir}/{name}")

    print(f"\n{'='*60}")
    print(f"  BUILD SCRIPTS GENERATED")
    print(f"{'='*60}")
    print(f"  Output: {output_dir}/")
    print(f"")
    print(f"  Next steps:")
    print(f"  1. Download partition images from device to {output_dir}/")
    print(f"  2. Run: cd {output_dir} && ./build.sh <registry:port>")
    print(f"  3. Run: ./deploy.sh <edge_host> <registry:port>")


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _parse_mountinfo(raw: str) -> dict:
    """Parse /proc/self/mountinfo into partition map."""
    import re
    partitions = {}
    MOUNT_NAMES = {
        "/": "system", "/system_ext": "system_ext", "/product": "product",
        "/vendor": "vendor", "/odm": "odm", "/data": "data", "/cache": "cache",
    }
    for line in (raw or "").split("\n"):
        parts = line.split()
        if len(parts) < 10:
            continue
        mount_point = parts[4]
        if mount_point not in MOUNT_NAMES:
            continue
        name = MOUNT_NAMES[mount_point]
        device = parts[9] if len(parts) > 9 else ""

        import re
        dm_match = re.match(r"/dev/block/dm-(\d+)", device)
        loop_match = re.match(r"/dev/block/loop(\d+)", device)

        if dm_match:
            major, minor = parts[2].split(":")
            loop_dev = f"loop{minor}" if major == "7" else f"dm-{dm_match.group(1)}"
        elif loop_match:
            loop_dev = f"loop{loop_match.group(1)}"
        else:
            continue

        partitions[name] = {
            "mount_point": mount_point,
            "actual_device": f"/dev/block/{loop_dev}",
            "raw_device": device,
        }
    return partitions


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(
        description="VMOS Android 15 OS Clone Deployer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--method", choices=["registry", "s3-restore", "direct",
                                              "docker-build", "download"],
                        default="docker-build",
                        help="Clone deployment method")
    parser.add_argument("--source-pad", required=True,
                        help="Source device PAD code")
    parser.add_argument("--target-pad",
                        help="Target device PAD code (for s3-restore/direct)")
    parser.add_argument("--vps", default="YOUR_OLLAMA_HOST",
                        help="VPS host for image transfer")
    parser.add_argument("--vps-port", type=int, default=18999,
                        help="VPS HTTP port")
    parser.add_argument("--registry-port", type=int, default=5000,
                        help="Docker registry port on VPS")
    parser.add_argument("--s3-endpoint",
                        help="S3-compatible endpoint (MinIO)")
    parser.add_argument("--s3-access-key", default="minioadmin",
                        help="S3 access key")
    parser.add_argument("--s3-secret-key", default="minioadmin",
                        help="S3 secret key")
    parser.add_argument("--s3-bucket", default="vmos-backups",
                        help="S3 bucket name")
    parser.add_argument("--output-dir", default="./clone_build",
                        help="Output directory for generated scripts")

    args = parser.parse_args()

    if args.method == "download":
        await download_images(args.source_pad, args.output_dir)

    elif args.method == "registry":
        await clone_via_registry(args.source_pad, args.vps,
                                 args.vps_port, args.registry_port)

    elif args.method == "s3-restore":
        if not args.target_pad:
            parser.error("--target-pad required for s3-restore method")
        if not args.s3_endpoint:
            parser.error("--s3-endpoint required for s3-restore method")
        await clone_via_s3(args.source_pad, args.target_pad,
                           args.s3_endpoint, args.s3_access_key,
                           args.s3_secret_key, args.s3_bucket)

    elif args.method == "direct":
        if not args.target_pad:
            parser.error("--target-pad required for direct method")
        await clone_via_direct(args.source_pad, args.target_pad)

    elif args.method == "docker-build":
        await generate_docker_build(args.source_pad, args.output_dir)


if __name__ == "__main__":
    asyncio.run(main())
