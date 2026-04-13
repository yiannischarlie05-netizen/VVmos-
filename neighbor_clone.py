#!/usr/bin/env python3
"""
Neighbor Device Clone v1.0
===========================
Clones a neighbor device's identity into a VMOS Cloud instance.

Flow:
  1. Load v2 extraction report → select source neighbor
  2. Map extracted properties → VMOS Cloud API parameters
  3. Apply ro.* properties via update_android_prop (triggers restart)
  4. Apply persist.* via modify_instance_properties (no restart)
  5. Set proxy, timezone, language, GPS
  6. Verify clone by comparing properties

Property injection strategy:
  - update_android_prop(pad_code, props)  → deep ro.* props, triggers ~20s restart
  - modify_instance_properties(pad_codes, props) → persist.sys.* props, instant
  - set_proxy(pad_codes, proxy_info) → proxy config
  - modify_timezone(pad_codes, tz) → timezone
  - modify_language(pad_codes, lang) → language/locale
  - set_gps(pad_codes, lat, lng) → GPS coordinates

Usage:
  # Clone best neighbor into our S25
  python neighbor_clone.py --report mass_extract_v2_report.json

  # Clone specific neighbor IP into specific target device
  python neighbor_clone.py --report mass_extract_v2_report.json --source 10.10.53.43 --target APP5BJ4LRVRJFJQR

  # Clone with proxy transfer
  python neighbor_clone.py --report mass_extract_v2_report.json --with-proxy

  # Dry run (show what would be set)
  python neighbor_clone.py --report mass_extract_v2_report.json --dry-run
"""

import asyncio
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

# ─── Config ───────────────────────────────────────────────────────────
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"
BASE_URL = "https://api.vmoscloud.com"
DEFAULT_TARGET = "APP5BJ4LRVRJFJQR"  # Virtual Android 16
RATE_SPACING = 3.5

# ─── Property mapping: extraction field → API property key ────────────
# These ro.* props go through update_android_prop (restart required)
ANDROID_PROP_MAP = {
    # From labeled extraction fields
    "ro.product.model": "model",
    "ro.product.brand": "brand",
    "ro.product.manufacturer": "manufacturer",
    "ro.product.device": "device",
    "ro.product.name": "product_name",
    "ro.product.board": "board",
    "ro.hardware": "hardware",
    "ro.build.fingerprint": "fingerprint",
    "ro.build.display.id": "display_id",
    "ro.build.version.release": "android_version",
    "ro.build.version.sdk": "sdk",
    "ro.build.version.security_patch": "security_patch",
    "ro.build.type": "build_type",
    "ro.build.tags": "build_tags",
    "ro.product.first_api_level": "first_api_level",
    "ro.board.platform": "platform",
    "ro.serialno": "serial",
}

# These go through clone_properties (from ==PROPS== section getprop dump)
ANDROID_PROP_KEYS_FROM_DUMP = [
    "ro.product.brand", "ro.product.model", "ro.product.device",
    "ro.product.name", "ro.product.manufacturer", "ro.product.board",
    "ro.hardware", "ro.build.display.id", "ro.build.fingerprint",
    "ro.build.version.release", "ro.build.version.sdk",
    "ro.build.version.incremental", "ro.build.version.security_patch",
    "ro.build.flavor", "ro.build.type", "ro.build.tags",
    "ro.serialno", "ro.boot.serialno", "ro.boot.hardware",
    "ro.boot.verifiedbootstate", "ro.boot.flash.locked",
    "ro.boot.vbmeta.device_state",
    "ro.soc.manufacturer", "ro.soc.model",
    "ro.hardware.chipname", "ro.board.platform",
    "ro.product.first_api_level",
    # Variants
    "ro.product.odm.brand", "ro.product.odm.model",
    "ro.product.odm.device", "ro.product.odm.name",
    "ro.product.system.brand", "ro.product.system.model",
    "ro.product.system.device", "ro.product.system.name",
    "ro.product.vendor.brand", "ro.product.vendor.model",
    "ro.product.vendor.device", "ro.product.vendor.name",
    # Build fingerprint variants
    "ro.odm.build.fingerprint", "ro.vendor.build.fingerprint",
    "ro.system.build.fingerprint", "ro.system_ext.build.fingerprint",
    "ro.product.build.fingerprint",
]

# Persist props → modify_instance_properties (no restart)
PERSIST_PROP_KEYS = [
    "persist.sys.timezone", "persist.sys.locale",
    "persist.sys.cloud.imeinum", "persist.sys.cloud.iccidnum",
    "persist.sys.cloud.imsinum", "persist.sys.cloud.phonenum",
    "persist.sys.cloud.wifi.ssid", "persist.sys.cloud.wifi.mac",
    "persist.sys.cloud.drm.id", "persist.sys.cloud.drm.puid",
    "persist.sys.cloud.gpu.gl_vendor", "persist.sys.cloud.gpu.gl_renderer",
    "persist.sys.cloud.gpu.gl_version",
    "persist.sys.cloud.battery.capacity", "persist.sys.cloud.battery.level",
    "persist.sys.cloud.pm.install_source",
]


def load_report(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def select_source(report: dict, source_ip: str = None, prefer_proxy: bool = False) -> dict:
    """Select best neighbor to clone from extraction report."""
    all_results = report.get("all_results", [])
    ok_results = [r for r in all_results if r.get("status") == "OK"]

    if not ok_results:
        print("[ERROR] No successful extractions in report")
        sys.exit(1)

    if source_ip:
        matches = [r for r in ok_results if r["ip"] == source_ip]
        if not matches:
            print(f"[ERROR] IP {source_ip} not found in report")
            available = [r["ip"] for r in ok_results[:10]]
            print(f"  Available: {', '.join(available)}")
            sys.exit(1)
        return matches[0]

    # Auto-select best: proxy > clone_props > apps > processes
    ranked = sorted(ok_results, key=lambda r: (
        (100 if prefer_proxy and r.get("proxy", {}).get("has_active_proxy") else 0)
        + (50 if r.get("proxy", {}).get("has_active_proxy") else 0)
        + len(r.get("clone_properties", {})) * 2
        + len(r.get("apps", []))
        + len(r.get("running_processes", []))
        + (10 if r.get("sim", {}).get("operator_alpha") else 0)
        + (10 if r.get("imei") else 0)
    ), reverse=True)

    return ranked[0]


def build_android_props(source: dict) -> dict:
    """Build ro.* property dict from extraction data."""
    props = {}

    # First: use clone_properties (from ==PROPS== section, most accurate)
    clone_props = source.get("clone_properties", {})
    for key in ANDROID_PROP_KEYS_FROM_DUMP:
        if key in clone_props and clone_props[key]:
            props[key] = clone_props[key]

    # Second: fill gaps from labeled extraction fields
    for prop_key, field_name in ANDROID_PROP_MAP.items():
        if prop_key not in props or not props[prop_key]:
            val = source.get(field_name, "")
            if val:
                props[prop_key] = val

    # Ensure fingerprint variants are consistent
    fp = props.get("ro.build.fingerprint", "")
    if fp:
        for variant in ["ro.odm.build.fingerprint", "ro.vendor.build.fingerprint",
                        "ro.system.build.fingerprint", "ro.system_ext.build.fingerprint",
                        "ro.product.build.fingerprint"]:
            if variant not in props:
                props[variant] = fp

    # Ensure product variants match base
    for base, variants in [
        ("ro.product.brand", ["ro.product.odm.brand", "ro.product.system.brand", "ro.product.vendor.brand"]),
        ("ro.product.model", ["ro.product.odm.model", "ro.product.system.model", "ro.product.vendor.model"]),
        ("ro.product.device", ["ro.product.odm.device", "ro.product.system.device", "ro.product.vendor.device"]),
        ("ro.product.name", ["ro.product.odm.name", "ro.product.system.name", "ro.product.vendor.name"]),
    ]:
        if base in props:
            for v in variants:
                if v not in props:
                    props[v] = props[base]

    return props


def build_persist_props(source: dict) -> dict:
    """Build persist.sys.* property dict from extraction data."""
    props = {}

    # From clone_properties dump
    clone_props = source.get("clone_properties", {})
    for key in PERSIST_PROP_KEYS:
        if key in clone_props and clone_props[key]:
            props[key] = clone_props[key]

    # Fill from labeled extraction fields
    if "persist.sys.timezone" not in props and source.get("timezone"):
        props["persist.sys.timezone"] = source["timezone"]
    if "persist.sys.locale" not in props and source.get("locale"):
        props["persist.sys.locale"] = source["locale"]
    if "persist.sys.cloud.imeinum" not in props and source.get("imei"):
        props["persist.sys.cloud.imeinum"] = source["imei"]
    if "persist.sys.cloud.iccidnum" not in props and source.get("iccid"):
        props["persist.sys.cloud.iccidnum"] = source["iccid"]
    if "persist.sys.cloud.imsinum" not in props and source.get("imsi"):
        props["persist.sys.cloud.imsinum"] = source["imsi"]
    if "persist.sys.cloud.wifi.mac" not in props and source.get("mac"):
        props["persist.sys.cloud.wifi.mac"] = source["mac"]

    return props


def build_proxy_info(source: dict) -> dict | None:
    """Build proxy API payload from extraction data."""
    proxy = source.get("proxy", {})
    parsed = proxy.get("parsed")
    if not parsed:
        return None
    if not parsed.get("ip") or parsed.get("enabled", "").lower() != "true":
        return None

    return {
        "proxyType": "proxy",
        "proxyName": "socks5",
        "proxyIp": parsed["ip"],
        "proxyPort": int(parsed.get("port", 0)),
        "proxyUser": parsed.get("user", ""),
        "proxyPassword": parsed.get("pass", ""),
        "enable": True,
    }


class NeighborCloner:
    def __init__(self, target_pad: str):
        self.client = VMOSCloudClient(AK, SK, BASE_URL)
        self.target_pad = target_pad
        self.log_entries = []

    def log(self, msg: str):
        print(msg)
        self.log_entries.append(msg)

    async def rate_sleep(self):
        await asyncio.sleep(RATE_SPACING)

    async def wait_for_device(self, timeout_sec: int = 60):
        """Wait for device to come back online (status 10) after restart."""
        self.log(f"  Waiting for device restart (up to {timeout_sec}s)...")
        start = time.time()
        while time.time() - start < timeout_sec:
            await asyncio.sleep(5)
            try:
                r = await self.client.instance_list(pad_codes=[self.target_pad])
                instances = r.get("data", {}).get("pageData", r.get("data", {}).get("records", []))
                if instances:
                    status = instances[0].get("padStatus", instances[0].get("status", 0))
                    if status == 10:  # running
                        self.log(f"  Device online (took {time.time()-start:.0f}s)")
                        return True
                    self.log(f"  Status: {status}, waiting...")
            except Exception:
                pass
        self.log(f"  WARNING: Device did not come back within {timeout_sec}s")
        return False

    async def clone(self, source: dict, with_proxy: bool = False, dry_run: bool = False):
        """Execute full device clone."""
        self.log(f"\n{'='*70}")
        self.log(f"  NEIGHBOR CLONE v1.0")
        self.log(f"{'='*70}")
        self.log(f"  Source: {source['ip']} ({source.get('model','?')} / {source.get('brand','?')})")
        self.log(f"  Target: {self.target_pad}")
        self.log(f"  Android: {source.get('android_version','?')} SDK:{source.get('sdk','?')}")
        self.log(f"  Timezone: {source.get('timezone','?')}")
        self.log(f"  Carrier: {source.get('sim',{}).get('operator_alpha','?')}")
        self.log(f"  Proxy: {'YES' if source.get('proxy',{}).get('has_active_proxy') else 'NO'}")
        self.log(f"  Clone props: {len(source.get('clone_properties',{}))}")
        self.log(f"  Dry run: {dry_run}")
        self.log("")

        # ── Phase 1: Build property sets ──
        self.log("[PHASE 1] Building property maps...")
        android_props = build_android_props(source)
        persist_props = build_persist_props(source)
        proxy_info = build_proxy_info(source) if with_proxy else None

        self.log(f"  Android (ro.*) properties: {len(android_props)}")
        for k, v in list(android_props.items())[:8]:
            self.log(f"    {k} = {v}")
        if len(android_props) > 8:
            self.log(f"    ... and {len(android_props)-8} more")

        self.log(f"\n  Persist (persist.sys.*) properties: {len(persist_props)}")
        for k, v in persist_props.items():
            self.log(f"    {k} = {v}")

        if proxy_info:
            self.log(f"\n  Proxy: {proxy_info['proxyIp']}:{proxy_info['proxyPort']}")
            self.log(f"    User: {proxy_info['proxyUser']}")
        else:
            self.log(f"\n  Proxy: NONE (not cloning proxy)")

        if dry_run:
            self.log(f"\n[DRY RUN] Would apply {len(android_props)} ro.* props + {len(persist_props)} persist props")
            return self._build_result(source, android_props, persist_props, proxy_info, dry_run=True)

        # ── Phase 2: Apply Android properties (triggers restart) ──
        if android_props:
            self.log(f"\n[PHASE 2] Applying {len(android_props)} Android properties (ro.*)...")
            self.log(f"  WARNING: This triggers device restart (~20-30s)")
            await self.rate_sleep()
            try:
                r = await self.client.update_android_prop(self.target_pad, android_props)
                code = r.get("code", "?")
                self.log(f"  update_android_prop response: code={code}")
                if code in [0, 200]:
                    self.log(f"  Properties queued, waiting for restart...")
                    await self.wait_for_device(timeout_sec=60)
                else:
                    self.log(f"  WARNING: Unexpected response code {code}: {r.get('msg','')}")
            except Exception as e:
                self.log(f"  ERROR: {e}")

        # ── Phase 3: Apply persist properties (no restart) ──
        if persist_props:
            self.log(f"\n[PHASE 3] Applying {len(persist_props)} persist properties...")
            await self.rate_sleep()
            try:
                r = await self.client.modify_instance_properties(
                    [self.target_pad], persist_props
                )
                code = r.get("code", "?")
                self.log(f"  modify_instance_properties response: code={code}")
            except Exception as e:
                self.log(f"  ERROR: {e}")

        # ── Phase 4: Set timezone ──
        tz = source.get("timezone", "")
        if tz:
            self.log(f"\n[PHASE 4] Setting timezone: {tz}")
            await self.rate_sleep()
            try:
                r = await self.client.modify_timezone([self.target_pad], tz)
                self.log(f"  modify_timezone response: code={r.get('code','?')}")
            except Exception as e:
                self.log(f"  ERROR: {e}")

        # ── Phase 5: Set language/locale ──
        locale = source.get("locale", "")
        if locale:
            self.log(f"\n[PHASE 5] Setting locale: {locale}")
            await self.rate_sleep()
            try:
                r = await self.client.modify_language([self.target_pad], locale)
                self.log(f"  modify_language response: code={r.get('code','?')}")
            except Exception as e:
                self.log(f"  ERROR: {e}")

        # ── Phase 6: Set proxy ──
        if proxy_info and with_proxy:
            self.log(f"\n[PHASE 6] Setting proxy: {proxy_info['proxyIp']}:{proxy_info['proxyPort']}")
            await self.rate_sleep()
            try:
                r = await self.client.set_proxy([self.target_pad], proxy_info)
                self.log(f"  set_proxy response: code={r.get('code','?')}")
            except Exception as e:
                self.log(f"  ERROR: {e}")

        # ── Phase 7: Verify ──
        self.log(f"\n[PHASE 7] Verifying clone...")
        await self.rate_sleep()
        await asyncio.sleep(3)  # Brief settle time
        try:
            r = await self.client.query_instance_properties(self.target_pad)
            if r.get("code") in [0, 200]:
                data = r.get("data", {})
                self.log(f"  Post-clone properties:")
                # Check key identity fields
                checks = [
                    ("Model", data.get("model", ""), android_props.get("ro.product.model", "")),
                    ("Brand", data.get("brand", ""), android_props.get("ro.product.brand", "")),
                    ("Fingerprint", data.get("fingerprint", "")[:50], android_props.get("ro.build.fingerprint", "")[:50]),
                ]
                all_match = True
                for label, actual, expected in checks:
                    match = "✓" if actual == expected else "✗"
                    if actual != expected:
                        all_match = False
                    self.log(f"    {match} {label}: {actual}")
                    if actual != expected and expected:
                        self.log(f"      Expected: {expected}")

                if all_match:
                    self.log(f"\n  CLONE VERIFIED — all identity fields match")
                else:
                    self.log(f"\n  CLONE PARTIAL — some fields may need restart to take effect")
            else:
                self.log(f"  Could not verify: {r}")
        except Exception as e:
            self.log(f"  Verify error: {e}")

        result = self._build_result(source, android_props, persist_props, proxy_info)
        self.log(f"\n{'='*70}")
        self.log(f"  CLONE COMPLETE")
        self.log(f"{'='*70}")
        return result

    def _build_result(self, source, android_props, persist_props, proxy_info, dry_run=False):
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "source_ip": source["ip"],
            "source_model": source.get("model", ""),
            "source_brand": source.get("brand", ""),
            "target_pad": self.target_pad,
            "dry_run": dry_run,
            "android_props_count": len(android_props),
            "persist_props_count": len(persist_props),
            "proxy_applied": proxy_info is not None,
            "android_props": android_props,
            "persist_props": persist_props,
            "proxy_info": proxy_info,
            "log": self.log_entries,
        }


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Clone neighbor device identity into VMOS Cloud instance")
    parser.add_argument("--report", required=True, help="Path to v2 extraction report JSON")
    parser.add_argument("--source", default=None, help="Source neighbor IP to clone (default: auto-select best)")
    parser.add_argument("--target", default=DEFAULT_TARGET, help=f"Target VMOS pad code (default: {DEFAULT_TARGET})")
    parser.add_argument("--with-proxy", action="store_true", help="Also clone proxy configuration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be set without applying")
    parser.add_argument("--output", default="clone_result.json", help="Output results file")
    args = parser.parse_args()

    report = load_report(args.report)
    source = select_source(report, args.source, prefer_proxy=args.with_proxy)

    print(f"Selected source: {source['ip']} ({source.get('model','?')})")
    print(f"Clone properties available: {len(source.get('clone_properties',{}))}")

    cloner = NeighborCloner(args.target)
    result = await cloner.clone(source, with_proxy=args.with_proxy, dry_run=args.dry_run)

    # Save result
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
    with open(filepath, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nResult saved to {filepath}")


if __name__ == "__main__":
    asyncio.run(main())
