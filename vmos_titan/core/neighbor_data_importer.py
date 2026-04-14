"""
Neighbor Device Data Importer — Accounts & SD Card Parser
==========================================================
Parses the "two txt dics" (accounts.txt and sdcard_listing.txt) from
neighbor device backups for Genesis V3 cloning operations.

From neighbor_backups/10_0_26_220/:
- accounts.txt — Dumpsys account output with OZON ID, Yandex Passport
- sdcard_listing.txt — SD card directory structure

Usage:
    from vmos_titan.core.neighbor_data_importer import NeighborDataImporter

    importer = NeighborDataImporter("/path/to/backup/dir")
    data = importer.parse_all()

    # Use in Genesis V3
    genesis_config = importer.to_genesis_config()
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("titan.neighbor-importer")


@dataclass
class AccountInfo:
    """Parsed account from dumpsys output."""
    name: str
    account_type: str
    uid: Optional[int] = None
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ServiceInfo:
    """Registered authenticator service."""
    account_type: str
    component: str
    uid: int


@dataclass
class SDCardItem:
    """Item from SD card listing."""
    name: str
    type: str  # 'directory' or 'file'
    permissions: str
    owner: str
    group: str
    size: int
    timestamp: Optional[datetime] = None
    path: str = ""


@dataclass
class NeighborDeviceData:
    """Complete parsed data from neighbor device backup."""
    device_ip: str = ""
    accounts: List[AccountInfo] = field(default_factory=list)
    services: List[ServiceInfo] = field(default_factory=list)
    sdcard_items: List[SDCardItem] = field(default_factory=list)
    account_history: List[Dict[str, Any]] = field(default_factory=list)

    def get_accounts_by_type(self, account_type: str) -> List[AccountInfo]:
        """Get all accounts of a specific type."""
        return [a for a in self.accounts if account_type in a.account_type]

    def get_account_types(self) -> List[str]:
        """Get all unique account types."""
        return list(set(a.account_type for a in self.accounts))

    def get_sdcard_directories(self) -> List[SDCardItem]:
        """Get only directory items from SD card."""
        return [i for i in self.sdcard_items if i.type == "directory"]

    def get_sdcard_files(self) -> List[SDCardItem]:
        """Get only file items from SD card."""
        return [i for i in self.sdcard_items if i.type == "file"]


class NeighborDataImporter:
    """
    Import and parse neighbor device backup data.

    Handles the two txt files from device .220 and similar backups.
    """

    def __init__(self, backup_dir: str):
        """
        Initialize importer with backup directory.

        Args:
            backup_dir: Path to backup directory containing txt files
        """
        self.backup_dir = Path(backup_dir)
        self.accounts_file = self.backup_dir / "accounts.txt"
        self.sdcard_file = self.backup_dir / "sdcard_listing.txt"

        # Extract IP from directory name (e.g., "10_0_26_220" -> "10.0.26.220")
        self.device_ip = self._extract_ip_from_path()

    def _extract_ip_from_path(self) -> str:
        """Extract IP address from backup directory name."""
        dir_name = self.backup_dir.name
        # Replace underscores with dots
        ip = dir_name.replace("_", ".")
        # Validate it looks like an IP
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
            return ip
        return ""

    def parse_all(self) -> NeighborDeviceData:
        """
        Parse all available data files.

        Returns:
            NeighborDeviceData with all parsed information
        """
        data = NeighborDeviceData(device_ip=self.device_ip)

        if self.accounts_file.exists():
            data.accounts, data.services, data.account_history = self._parse_accounts()
            logger.info(f"Parsed {len(data.accounts)} accounts from {self.accounts_file}")

        if self.sdcard_file.exists():
            data.sdcard_items = self._parse_sdcard()
            logger.info(f"Parsed {len(data.sdcard_items)} SD card items from {self.sdcard_file}")

        return data

    def _parse_accounts(self) -> Tuple[List[AccountInfo], List[ServiceInfo], List[Dict]]:
        """
        Parse accounts.txt dumpsys output.

        Returns:
            (accounts, services, history)
        """
        accounts = []
        services = []
        history = []

        try:
            content = self.accounts_file.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to read accounts file: {e}")
            return accounts, services, history

        # Parse User section
        user_match = re.search(r"UserInfo\{(\d+):([^:]+):(\w+)\}", content)
        if user_match:
            user_id = user_match.group(1)
            user_name = user_match.group(2).strip()
            logger.debug(f"Found user: {user_name} (ID: {user_id})")

        # Parse Accounts
        account_pattern = re.compile(
            r"Account\s*\{name=([^,]+),\s*type=([^}]+)\}"
        )
        for match in account_pattern.finditer(content):
            name = match.group(1).strip()
            account_type = match.group(2).strip()
            accounts.append(AccountInfo(name=name, account_type=account_type))

        # Parse Account History
        history_pattern = re.compile(
            r"(\d+),([^,]+),([\d\-:\s]+),(\d+),([^,]+),(\d+)"
        )
        for match in history_pattern.finditer(content):
            history.append({
                "account_id": int(match.group(1)),
                "action": match.group(2),
                "timestamp": match.group(3),
                "uid": int(match.group(4)),
                "table": match.group(5),
                "key": int(match.group(6)),
            })

        # Parse RegisteredServicesCache
        service_pattern = re.compile(
            r"ServiceInfo:\s*AuthenticatorDescription\s*\{type=([^}]+)\},\s*"
            r"ComponentInfo\{([^}]+)\},\s*uid\s+(\d+)"
        )
        for match in service_pattern.finditer(content):
            services.append(ServiceInfo(
                account_type=match.group(1).strip(),
                component=match.group(2).strip(),
                uid=int(match.group(3)),
            ))

        return accounts, services, history

    def _parse_sdcard(self) -> List[SDCardItem]:
        """
        Parse sdcard_listing.txt directory output.

        Returns:
            List of SDCardItem
        """
        items = []

        try:
            content = self.sdcard_file.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to read sdcard file: {e}")
            return items

        lines = content.strip().split('\n')

        # Skip header lines until we find 'total' line
        data_started = False
        for line in lines:
            line = line.strip()

            # Skip empty lines and headers
            if not line or line.startswith('/sdcard:') or line.startswith('total'):
                if line.startswith('total'):
                    data_started = True
                continue

            if not data_started:
                continue

            # Parse ls -la format: drwxrws--- 2 u0_a95 media_rw 3488 2026-03-15 18:02 Alarms
            match = re.match(
                r"([\-drwxsStT]+)\s+\d+\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+(.+)",
                line
            )

            if match:
                perms = match.group(1)
                owner = match.group(2)
                group = match.group(3)
                size = int(match.group(4))
                date_str = match.group(5)
                time_str = match.group(6)
                name = match.group(7).strip()

                # Determine type
                item_type = "directory" if perms.startswith('d') else "file"

                # Parse timestamp
                try:
                    timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    timestamp = None

                items.append(SDCardItem(
                    name=name,
                    type=item_type,
                    permissions=perms,
                    owner=owner,
                    group=group,
                    size=size,
                    timestamp=timestamp,
                    path=f"/sdcard/{name}",
                ))

        return items

    def to_genesis_config(self) -> Dict[str, Any]:
        """
        Convert imported data to Genesis V3 configuration.

        Returns:
            Dictionary suitable for PipelineConfig
        """
        data = self.parse_all()

        # Extract identity from accounts
        google_account = None
        yandex_account = None
        ozon_account = None

        for account in data.accounts:
            if "com.google" in account.account_type:
                google_account = account
            elif "yandex" in account.account_type.lower():
                yandex_account = account
            elif "ozon" in account.account_type.lower():
                ozon_account = account

        # Build Genesis config
        config = {
            "device_ip": data.device_ip,
            "source_device": "neighbor_clone",
            "accounts_found": len(data.accounts),
            "account_types": data.get_account_types(),
            "has_google": google_account is not None,
            "has_yandex": yandex_account is not None,
            "has_ozon": ozon_account is not None,
            "sdcard_directories": [d.name for d in data.get_sdcard_directories()],
            "sdcard_files_count": len(data.get_sdcard_files()),
        }

        # Add account-specific data
        if yandex_account:
            # Parse name from Yandex format: "Максим Сирож #2042295278 ﹫"
            name_match = re.match(r"([^#]+)", yandex_account.name)
            if name_match:
                config["name"] = name_match.group(1).strip()

        return config

    def generate_clone_script(self, target_device_id: str) -> str:
        """
        Generate a Python script to clone accounts to target device.

        Args:
            target_device_id: Target VMOS device ID

        Returns:
            Python script as string
        """
        data = self.parse_all()
        account_name = data.accounts[0].name if data.accounts else 'Cloned User'

        script = f'''#!/usr/bin/env python3
"""
Auto-generated neighbor device clone script
Source: {self.device_ip}
Target: {target_device_id}
Generated: {datetime.now().isoformat()}
"""

import asyncio
from vmos_titan.core.genesis_factory import create_production_engine, PipelineConfig

async def clone_neighbor_device():
    """Clone accounts from neighbor device to target."""
    
    # Initialize Genesis engine
    engine = create_production_engine("{target_device_id}")
    
    # Build config from neighbor data
    config = PipelineConfig(
        device_id="{target_device_id}",
        name="{account_name}",
        email="cloned@example.com",
        country="RU",  # Neighbor device was Russian
        age_days=180,
    )
    
    # Execute Genesis pipeline
    result = await engine.execute_pipeline(config)
    
    print(f"Clone result: {{result.success}}")
    print(f"Trust score: {{result.trust_score}}")
    
    return result

if __name__ == "__main__":
    asyncio.run(clone_neighbor_device())
'''
        return script

    def get_summary(self) -> str:
        """Get human-readable summary of imported data."""
        data = self.parse_all()

        lines = [
            f"Neighbor Device Backup Summary",
            f"================================",
            f"",
            f"Source IP: {data.device_ip}",
            f"Backup Directory: {self.backup_dir}",
            f"",
            f"Accounts Found: {len(data.accounts)}",
        ]

        for account in data.accounts:
            lines.append(f"  - {account.name} ({account.account_type})")

        if data.services:
            lines.append(f"\nAuthenticator Services: {len(data.services)}")
            for svc in data.services[:5]:  # Show first 5
                lines.append(f"  - {svc.account_type} (UID: {svc.uid})")

        lines.extend([
            f"\nSD Card Items: {len(data.sdcard_items)}",
            f"  Directories: {len(data.get_sdcard_directories())}",
            f"  Files: {len(data.get_sdcard_files())}",
        ])

        # Show sample directories
        dirs = data.get_sdcard_directories()
        if dirs:
            lines.append(f"\nSample Directories:")
            for d in dirs[:5]:
                lines.append(f"  - {d.name}/ ({d.owner}:{d.group})")

        return "\n".join(lines)


def import_neighbor_backup(backup_dir: str) -> NeighborDeviceData:
    """
    Quick import of neighbor device backup.

    Args:
        backup_dir: Path to backup directory

    Returns:
        Parsed NeighborDeviceData
    """
    importer = NeighborDataImporter(backup_dir)
    return importer.parse_all()


# Example usage
if __name__ == "__main__":
    import sys

    # Default to the .220 backup directory
    backup_dir = "/home/debian/Downloads/vmos-titan-unified/neighbor_backups/10_0_26_220"

    if len(sys.argv) > 1:
        backup_dir = sys.argv[1]

    importer = NeighborDataImporter(backup_dir)

    # Print summary
    print(importer.get_summary())

    # Generate clone script
    print("\n" + "=" * 50)
    print("Sample Clone Script:")
    print(importer.generate_clone_script("TARGET_DEVICE_ID"))
