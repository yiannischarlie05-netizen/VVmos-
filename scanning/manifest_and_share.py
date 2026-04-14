#!/usr/bin/env python3
"""
BACKUP DATA MANIFEST & PUBLIC SHARE GENERATOR v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Creates a comprehensive manifest of all backup data.
Generates a downloadable archive for device injection testing.
Includes integrity checks and metadata for validation.
"""

import os
import sys
import json
import hashlib
import tarfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import subprocess

class BackupManifest:
    def __init__(self, clone_dir: str):
        self.clone_dir = Path(clone_dir)
        self.manifest = {
            "timestamp": datetime.now().isoformat(),
            "source": str(self.clone_dir),
            "files": {},
            "statistics": {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
            },
            "categories": {},
            "integrity": {}
        }
    
    def scan_and_catalog(self) -> Dict:
        """Scan all backup files and create detailed manifest"""
        print("\n[MANIFEST GENERATOR] Cataloging all backup data...\n")
        
        categories = {
            "gms_accounts": "System Account Databases (CE/DE)",
            "gms_shared_prefs": "GMS Authentication & Configuration (146 XML files)",
            "gms_databases": "GMS Service Metadata Databases",
            "chrome_data": "Chrome Browser Login, Cookies, History",
            "gsf_data": "Google Services Framework (Device Identity)",
            "telegram_session": "Telegram Session & Account Data",
            "apps": "Application APK + Data Tars",
            "other": "Device Properties & Metadata"
        }
        
        # Scan each category
        for cat_dir, description in categories.items():
            cat_path = self.clone_dir / cat_dir
            if cat_path.exists():
                self._catalog_category(cat_dir, cat_path, description)
        
        # Add master manifest statistics
        self.manifest["statistics"]["total_size_mb"] = self.manifest["statistics"]["total_size_bytes"] / 1024 / 1024
        
        print(f"\n✓ Manifest complete:")
        print(f"  Total files: {self.manifest['statistics']['total_files']}")
        print(f"  Total size: {self.manifest['statistics']['total_size_mb']:.1f} MB")
        print(f"  Categories: {len(self.manifest['categories'])}")
        
        return self.manifest
    
    def _catalog_category(self, category: str, path: Path, description: str):
        """Catalog a single category"""
        self.manifest["categories"][category] = {
            "description": description,
            "files": []
        }
        
        file_list = []
        for f in path.rglob("*"):
            if f.is_file():
                size = os.path.getsize(f)
                rel_path = f.relative_to(self.clone_dir)
                
                file_entry = {
                    "path": str(rel_path),
                    "size_bytes": size,
                    "size_mb": size / 1024 / 1024,
                    "hash_md5": self._md5_file(f)
                }
                
                file_list.append(file_entry)
                self.manifest["statistics"]["total_files"] += 1
                self.manifest["statistics"]["total_size_bytes"] += size
        
        self.manifest["categories"][category]["files"] = file_list
        self.manifest["categories"][category]["file_count"] = len(file_list)
        self.manifest["categories"][category]["total_size_bytes"] = sum(f["size_bytes"] for f in file_list)
        
        print(f"  [{category}]: {len(file_list)} files, " +
              f"{self.manifest['categories'][category]['total_size_bytes'] / 1024 / 1024:.1f} MB")
    
    def _md5_file(self, file_path: Path) -> str:
        """Compute MD5 of file"""
        md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except:
            return "error"
    
    def save_manifest(self, output_path: str):
        """Save manifest to JSON"""
        with open(output_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)
        print(f"\n✓ Manifest saved to {output_path}")
        return output_path
    
    def create_downloadable_archive(self, output_tar: str, include_apps: bool = True) -> str:
        """Create a compressed archive suitable for device download"""
        print(f"\n[ARCHIVE GENERATOR] Creating downloadable archive...")
        
        # Create tar.gz of all backup data
        with tarfile.open(output_tar, "w:gz") as tar:
            # Add all directories except large APKs if requested
            for item in self.clone_dir.iterdir():
                if item.is_dir():
                    if not include_apps and item.name == "apps":
                        print(f"  Skipping apps (too large): {item.name}")
                        continue
                    
                    print(f"  Adding: {item.name}/")
                    tar.add(str(item), arcname=item.name)
        
        size_mb = os.path.getsize(output_tar) / 1024 / 1024
        print(f"✓ Archive created: {output_tar} ({size_mb:.1f} MB)")
        return output_tar

class PublicShareGenerator:
    """Generate a public share for device download testing"""
    
    @staticmethod
    def create_http_server_manifest(archive_path: str, port: int = 8888) -> Dict:
        """Create manifest for HTTP server"""
        archive_name = Path(archive_path).name
        file_size = os.path.getsize(archive_path)
        
        manifest = {
            "file": archive_name,
            "size_bytes": file_size,
            "size_mb": file_size / 1024 / 1024,
            "download_url": f"http://localhost:{port}/{archive_name}",
            "md5": PublicShareGenerator._md5_file(archive_path),
            "timestamp": datetime.now().isoformat(),
            "instructions": [
                f"1. Start HTTP server: python3 -m http.server {port} --directory $(dirname {archive_path})",
                f"2. On device, download: wget http://<host>:{port}/{archive_name}",
                f"3. Verify: md5sum {archive_name}",
                "4. Extract on device: tar xzf <archive>"
            ]
        }
        
        return manifest
    
    @staticmethod
    def _md5_file(file_path: str) -> str:
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()
    
    @staticmethod
    def generate_device_download_script(archive_url: str, expected_md5: str = None) -> str:
        """Generate bash script for device to download and verify"""
        script = f"""#!/bin/bash
# Download backup archive on device

ARCHIVE_URL="{archive_url}"
ARCHIVE_NAME="$(basename $ARCHIVE_URL)"
EXPECTED_MD5="{expected_md5 or ''}"

echo "[*] Downloading backup from $ARCHIVE_URL"
wget -q "$ARCHIVE_URL" -O "/data/local/tmp/$ARCHIVE_NAME" || exit 1

if [ ! -z "$EXPECTED_MD5" ]; then
    echo "[*] Verifying checksum..."
    ACTUAL_MD5=$(md5sum "/data/local/tmp/$ARCHIVE_NAME" | cut -d' ' -f1)
    if [ "$ACTUAL_MD5" != "$EXPECTED_MD5" ]; then
        echo "[!] Checksum mismatch! Expected: $EXPECTED_MD5, Got: $ACTUAL_MD5"
        exit 1
    fi
    echo "[✓] Checksum OK"
fi

echo "[✓] Download complete: /data/local/tmp/$ARCHIVE_NAME"
echo "[*] Extract with: tar xzf /data/local/tmp/$ARCHIVE_NAME"
"""
        return script

class DataQualityValidator:
    """Validate extracted data for injection readiness"""
    
    @staticmethod
    def assess(manifest: Dict) -> Dict:
        """Assess data quality and readiness"""
        print("\n[DATA QUALITY ASSESSMENT]\n")
        
        assessment = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_readiness": "GOOD",
            "warnings": [],
            "recommendations": []
        }
        
        # Check 1: GMS data presence
        gms_cat = manifest["categories"].get("gms_shared_prefs", {})
        gms_file_count = gms_cat.get("file_count", 0)
        
        if gms_file_count >= 100:
            assessment["checks"]["gms_prefs"] = "✓ EXCELLENT (146+ files)"
        elif gms_file_count >= 50:
            assessment["checks"]["gms_prefs"] = "✓ GOOD (50+ files)"
        else:
            assessment["checks"]["gms_prefs"] = "✗ POOR (< 50 files)"
            assessment["warnings"].append("Low GMS prefs count - accounts may not transfer")
        
        # Check 2: Database presence
        gms_db_cat = manifest["categories"].get("gms_databases", {})
        gms_db_count = gms_db_cat.get("file_count", 0)
        
        if gms_db_count >= 20:
            assessment["checks"]["gms_databases"] = f"✓ GOOD ({gms_db_count} files)"
        else:
            assessment["checks"]["gms_databases"] = f"⚠ MARGINAL ({gms_db_count} files)"
            assessment["recommendations"].append("Consider backing up more GMS data stores")
        
        # Check 3: Account DBs
        acct_cat = manifest["categories"].get("gms_accounts", {})
        acct_count = acct_cat.get("file_count", 0)
        
        if acct_count >= 2:
            assessment["checks"]["account_dbs"] = f"✓ OK ({acct_count} DBs)"
        else:
            assessment["checks"]["account_dbs"] = "⚠ MISSING"
            assessment["warnings"].append("No account databases found")
        
        # Check 4: Chrome data
        chrome_cat = manifest["categories"].get("chrome_data", {})
        chrome_files = chrome_cat.get("file_count", 0)
        
        if chrome_files >= 3:
            assessment["checks"]["chrome_data"] = f"✓ COMPLETE ({chrome_files} files)"
        else:
            assessment["checks"]["chrome_data"] = "⚠ INCOMPLETE"
        
        # Check 5: Apps
        apps_cat = manifest["categories"].get("apps", {})
        apps_count = apps_cat.get("file_count", 0)
        
        if apps_count >= 7:
            assessment["checks"]["apps"] = f"✓ COMPLETE ({apps_count} packages)"
        elif apps_count >= 3:
            assessment["checks"]["apps"] = f"⚠ PARTIAL ({apps_count} packages)"
            assessment["warnings"].append("Missing some critical apps")
        else:
            assessment["checks"]["apps"] = "✗ MISSING"
        
        # Overall assessment
        warning_count = len(assessment["warnings"])
        if warning_count > 2:
            assessment["overall_readiness"] = "FAIR"
        elif warning_count > 0:
            assessment["overall_readiness"] = "GOOD"
        else:
            assessment["overall_readiness"] = "EXCELLENT"
        
        # Print results
        print("Quality Checks:")
        for check, result in assessment["checks"].items():
            print(f"  {check:20s}: {result}")
        
        if assessment["warnings"]:
            print(f"\nWarnings ({len(assessment['warnings'])}):")
            for w in assessment["warnings"]:
                print(f"  ⚠ {w}")
        
        if assessment["recommendations"]:
            print(f"\nRecommendations:")
            for r in assessment["recommendations"]:
                print(f"  → {r}")
        
        print(f"\n✓ Overall: {assessment['overall_readiness']}")
        
        return assessment

# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 manifest_and_share.py <clone_dir>")
        sys.exit(1)
    
    clone_dir = sys.argv[1]
    
    if not Path(clone_dir).exists():
        print(f"ERROR: {clone_dir} not found")
        sys.exit(1)
    
    # Generate manifest
    print("=" * 80)
    print("BACKUP DATA MANIFEST & PUBLIC SHARE GENERATOR")
    print("=" * 80)
    
    manifest_gen = BackupManifest(clone_dir)
    manifest = manifest_gen.scan_and_catalog()
    manifest_gen.save_manifest(f"{clone_dir}/MANIFEST.json")
    
    # Create archive (without large APKs to keep size < 1GB for download)
    archive_path = f"{clone_dir}/backup_data_no_apks.tar.gz"
    manifest_gen.create_downloadable_archive(archive_path, include_apps=False)
    
    # Generate share manifest
    print("\n" + "=" * 80)
    print("PUBLIC SHARE CONFIGURATION")
    print("=" * 80)
    
    share_info = PublicShareGenerator.create_http_server_manifest(archive_path)
    with open(f"{clone_dir}/SHARE_MANIFEST.json", 'w') as f:
        json.dump(share_info, f, indent=2)
    
    print(f"\nShare Details:")
    for key, value in share_info.items():
        if key != "instructions":
            print(f"  {key}: {value}")
    
    # Generate device download script
    script_path = f"{clone_dir}/download_on_device.sh"
    script = PublicShareGenerator.generate_device_download_script(
        share_info["download_url"],
        share_info["md5"]
    )
    with open(script_path, 'w') as f:
        f.write(script)
    os.chmod(script_path, 0o755)
    print(f"\n✓ Device download script: {script_path}")
    
    # Quality assessment
    print("\n" + "=" * 80)
    print("DATA QUALITY ASSESSMENT")
    print("=" * 80)
    
    assessor = DataQualityValidator()
    assessment = assessor.assess(manifest)
    
    with open(f"{clone_dir}/QUALITY_ASSESSMENT.json", 'w') as f:
        json.dump(assessment, f, indent=2)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✓ Manifest: {clone_dir}/MANIFEST.json")
    print(f"✓ Archive: {archive_path} ({share_info['size_mb']:.1f} MB)")
    print(f"✓ MD5: {share_info['md5']}")
    print(f"✓ Assessment: {assessment['overall_readiness']}")
    print(f"\nTo share publicly:")
    print(f"  1. cd {clone_dir}")
    print(f"  2. python3 -m http.server 8000")
    print(f"  3. On device: wget http://<your-ip>:8000/backup_data_no_apks.tar.gz")
