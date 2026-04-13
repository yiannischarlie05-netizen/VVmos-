"""
Device Backdater — Make device appear old with aged data.

Backdates:
- UsageStats XMLs
- App install timestamps
- Chrome history
- Package manager timestamps
- Photo EXIF data
- SMS/call log timestamps
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class BackdateResult:
    """Result of backdating operation."""
    target: str
    success: bool
    items_modified: int = 0
    error: str = ""
    
    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "success": self.success,
            "items_modified": self.items_modified,
            "error": self.error,
        }


@dataclass
class FullBackdateReport:
    """Complete backdating report."""
    days_backdated: int
    results: List[BackdateResult] = field(default_factory=list)
    
    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)
    
    @property
    def total_items(self) -> int:
        return sum(r.items_modified for r in self.results)
    
    def to_dict(self) -> dict:
        return {
            "days_backdated": self.days_backdated,
            "success_count": self.success_count,
            "total_targets": len(self.results),
            "total_items_modified": self.total_items,
            "results": [r.to_dict() for r in self.results],
        }


class DeviceBackdater:
    """Make device appear old with aged data."""
    
    def __init__(self, client, pad_code: str):
        """
        Initialize backdater.
        
        Args:
            client: VMOS client instance
            pad_code: Device pad code
        """
        self.client = client
        self.pad_code = pad_code
    
    async def _shell(self, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute shell command."""
        try:
            if hasattr(self.client, 'shell'):
                return await self.client.shell(self.pad_code, cmd, timeout=timeout)
            elif hasattr(self.client, 'sync_cmd'):
                result = await self.client.sync_cmd(self.pad_code, cmd, timeout_sec=timeout)
                if result.get("code") == 200:
                    data = result.get("data")
                    if isinstance(data, list) and data:
                        output = data[0].get("errorMsg", "")
                        return True, str(output).strip() if output else ""
                    elif isinstance(data, dict):
                        output = data.get("errorMsg", "")
                        return True, str(output).strip() if output else ""
                return False, result.get("msg", "")
            else:
                result = await self.client.async_adb_cmd([self.pad_code], cmd)
                return result.get("code") == 200, ""
        except Exception as e:
            return False, str(e)
    
    async def backdate_usage_stats(self, days: int) -> BackdateResult:
        """
        Backdate UsageStats XMLs.
        
        Android stores app usage data in /data/system/usagestats/0/
        Files are named by timestamp (daily, weekly, monthly, yearly).
        """
        result = BackdateResult(target="usage_stats", success=False)
        offset_ms = days * 24 * 60 * 60 * 1000
        now_ms = int(time.time() * 1000)
        past_ms = now_ms - offset_ms
        
        try:
            # Get list of usagestats files
            cmd = "ls /data/system/usagestats/0/*.xml 2>/dev/null | head -20"
            success, output = await self._shell(cmd)
            
            if not success or not output:
                result.error = "No usagestats files found"
                return result
            
            files = [f.strip() for f in output.split('\n') if f.strip()]
            modified = 0
            
            for f in files:
                # Modify timestamps in XML
                # UsageStats uses firstTimeStamp and lastTimeStamp attributes
                sed_cmd = (
                    f"sed -i "
                    f"-e 's/firstTimeStamp=\"[0-9]*\"/firstTimeStamp=\"{past_ms}\"/g' "
                    f"-e 's/lastTimeStamp=\"[0-9]*\"/lastTimeStamp=\"{now_ms}\"/g' "
                    f"{f} 2>/dev/null && echo 'OK'"
                )
                ok, _ = await self._shell(sed_cmd)
                if ok:
                    modified += 1
            
            # Touch files with past timestamp
            touch_time = time.strftime("%Y%m%d%H%M.%S", time.gmtime(past_ms / 1000))
            for f in files[:5]:  # First few files
                await self._shell(f"touch -t {touch_time} {f} 2>/dev/null")
            
            result.success = modified > 0
            result.items_modified = modified
            logger.info(f"Backdated {modified} usagestats files")
            
        except Exception as e:
            result.error = str(e)
        
        return result
    
    async def backdate_app_installs(self, days: int) -> BackdateResult:
        """
        Backdate app installation timestamps.
        
        Modifies /data/system/packages.xml firstInstallTime and lastUpdateTime.
        """
        result = BackdateResult(target="app_installs", success=False)
        offset_ms = days * 24 * 60 * 60 * 1000
        now_ms = int(time.time() * 1000)
        base_past_ms = now_ms - offset_ms
        
        try:
            # Create sed script to modify install times
            # Add some randomness so not all apps installed at same time
            sed_cmd = (
                f"cp /data/system/packages.xml /data/system/packages.xml.bak 2>/dev/null; "
                f"sed -i "
                f"-e 's/ft=\"[0-9a-f]*\"/ft=\"{hex(base_past_ms)[2:]}\"/g' "
                f"-e 's/it=\"[0-9a-f]*\"/it=\"{hex(base_past_ms)[2:]}\"/g' "
                f"-e 's/ut=\"[0-9a-f]*\"/ut=\"{hex(now_ms - random.randint(0, offset_ms // 2))[2:]}\"/g' "
                f"/data/system/packages.xml 2>/dev/null && echo 'OK'"
            )
            
            success, output = await self._shell(sed_cmd, timeout=60)
            
            if success and "OK" in output:
                result.success = True
                result.items_modified = 1
                logger.info(f"Backdated packages.xml by {days} days")
            else:
                result.error = output or "Failed to modify packages.xml"
                
        except Exception as e:
            result.error = str(e)
        
        return result
    
    async def backdate_chrome_history(self, days: int) -> BackdateResult:
        """
        Backdate Chrome browsing history.
        
        Modifies timestamps in /data/data/com.android.chrome/app_chrome/Default/History
        """
        result = BackdateResult(target="chrome_history", success=False)
        offset_us = days * 24 * 60 * 60 * 1000000  # Chrome uses microseconds
        
        try:
            db_path = "/data/data/com.android.chrome/app_chrome/Default/History"
            
            # Check if History exists
            check_cmd = f"ls {db_path} 2>/dev/null"
            success, _ = await self._shell(check_cmd)
            
            if not success:
                result.error = "Chrome History not found"
                return result
            
            # Update visit times
            sql = f"UPDATE visits SET visit_time = visit_time - {offset_us}; UPDATE urls SET last_visit_time = last_visit_time - {offset_us};"
            cmd = f'sqlite3 {db_path} "{sql}" 2>/dev/null && echo "OK"'
            
            success, output = await self._shell(cmd)
            
            if success and "OK" in output:
                result.success = True
                # Count modified rows
                count_cmd = f'sqlite3 {db_path} "SELECT COUNT(*) FROM visits" 2>/dev/null'
                _, count = await self._shell(count_cmd)
                try:
                    result.items_modified = int(count.strip())
                except:
                    result.items_modified = 1
                logger.info(f"Backdated Chrome history by {days} days")
            else:
                result.error = output or "Failed to modify History"
                
        except Exception as e:
            result.error = str(e)
        
        return result
    
    async def backdate_contacts(self, days: int) -> BackdateResult:
        """Backdate contact creation timestamps."""
        result = BackdateResult(target="contacts", success=False)
        offset_ms = days * 24 * 60 * 60 * 1000
        
        try:
            db_path = "/data/data/com.android.providers.contacts/databases/contacts2.db"
            
            sql = f"UPDATE raw_contacts SET times_contacted = times_contacted + 5, last_time_contacted = last_time_contacted - {offset_ms} WHERE last_time_contacted > 0;"
            cmd = f'sqlite3 {db_path} "{sql}" 2>/dev/null && echo "OK"'
            
            success, output = await self._shell(cmd)
            
            if success and "OK" in output:
                result.success = True
                result.items_modified = 1
                logger.info(f"Backdated contacts by {days} days")
            else:
                result.error = output or "Failed or no contacts"
                
        except Exception as e:
            result.error = str(e)
        
        return result
    
    async def backdate_sms(self, days: int) -> BackdateResult:
        """Backdate SMS timestamps."""
        result = BackdateResult(target="sms", success=False)
        offset_ms = days * 24 * 60 * 60 * 1000
        
        try:
            db_path = "/data/data/com.android.providers.telephony/databases/mmssms.db"
            
            sql = f"UPDATE sms SET date = date - {offset_ms}, date_sent = date_sent - {offset_ms} WHERE date > 0;"
            cmd = f'sqlite3 {db_path} "{sql}" 2>/dev/null && echo "OK"'
            
            success, output = await self._shell(cmd)
            
            if success:
                result.success = True
                result.items_modified = 1
            else:
                result.error = "No SMS database or empty"
                
        except Exception as e:
            result.error = str(e)
        
        return result
    
    async def backdate_call_log(self, days: int) -> BackdateResult:
        """Backdate call log timestamps."""
        result = BackdateResult(target="call_log", success=False)
        offset_ms = days * 24 * 60 * 60 * 1000
        
        try:
            db_path = "/data/data/com.android.providers.contacts/databases/calllog.db"
            
            sql = f"UPDATE calls SET date = date - {offset_ms} WHERE date > 0;"
            cmd = f'sqlite3 {db_path} "{sql}" 2>/dev/null && echo "OK"'
            
            success, output = await self._shell(cmd)
            
            if success:
                result.success = True
                result.items_modified = 1
            else:
                result.error = "No call log or empty"
                
        except Exception as e:
            result.error = str(e)
        
        return result
    
    async def backdate_wallet_transactions(self, days: int) -> BackdateResult:
        """Backdate Google Wallet transaction timestamps."""
        result = BackdateResult(target="wallet_transactions", success=False)
        offset_ms = days * 24 * 60 * 60 * 1000
        
        try:
            db_path = "/data/data/com.google.android.gms/databases/tapandpay.db"
            
            sql = f"UPDATE transactions SET timestamp = timestamp - {offset_ms} WHERE timestamp > 0;"
            cmd = f'sqlite3 {db_path} "{sql}" 2>/dev/null && echo "OK"'
            
            success, output = await self._shell(cmd)
            
            if success and "OK" in output:
                result.success = True
                # Count
                count_cmd = f'sqlite3 {db_path} "SELECT COUNT(*) FROM transactions" 2>/dev/null'
                _, count = await self._shell(count_cmd)
                try:
                    result.items_modified = int(count.strip())
                except:
                    result.items_modified = 1
                logger.info(f"Backdated wallet transactions by {days} days")
            else:
                result.error = "No wallet transactions"
                
        except Exception as e:
            result.error = str(e)
        
        return result
    
    async def backdate_system_files(self, days: int) -> BackdateResult:
        """Backdate system file timestamps."""
        result = BackdateResult(target="system_files", success=False)
        past_time = int(time.time()) - (days * 86400)
        touch_time = time.strftime("%Y%m%d%H%M.%S", time.gmtime(past_time))
        
        try:
            files = [
                "/data/system/packages.xml",
                "/data/system/users/0/settings_system.xml",
                "/data/system/users/0/settings_secure.xml",
                "/data/system/users/0/settings_global.xml",
            ]
            
            modified = 0
            for f in files:
                cmd = f"touch -t {touch_time} {f} 2>/dev/null && echo 'OK'"
                success, output = await self._shell(cmd)
                if success and "OK" in output:
                    modified += 1
            
            result.success = modified > 0
            result.items_modified = modified
            logger.info(f"Backdated {modified} system files")
            
        except Exception as e:
            result.error = str(e)
        
        return result
    
    async def full_backdate(self, days: int) -> FullBackdateReport:
        """
        Run complete device backdating.
        
        Args:
            days: Number of days to backdate
            
        Returns:
            FullBackdateReport with all results
        """
        report = FullBackdateReport(days_backdated=days)
        
        logger.info(f"Starting full backdate: {days} days")
        
        # Run all backdating operations
        operations = [
            self.backdate_usage_stats(days),
            self.backdate_app_installs(days),
            self.backdate_chrome_history(days),
            self.backdate_contacts(days),
            self.backdate_sms(days),
            self.backdate_call_log(days),
            self.backdate_wallet_transactions(days),
            self.backdate_system_files(days),
        ]
        
        results = await asyncio.gather(*operations, return_exceptions=True)
        
        for r in results:
            if isinstance(r, BackdateResult):
                report.results.append(r)
            elif isinstance(r, Exception):
                report.results.append(BackdateResult(
                    target="unknown",
                    success=False,
                    error=str(r),
                ))
        
        logger.info(f"Backdate complete: {report.success_count}/{len(report.results)} targets, {report.total_items} items modified")
        
        return report
