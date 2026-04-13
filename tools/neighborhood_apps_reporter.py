#!/usr/bin/env python3
"""
Neighborhood All-Apps Reporter v1.0
====================================
Pre-extraction scanner: scans ALL neighbor devices on the VMOS 10.0.0.0/16
network and reports EVERY installed app — system AND third-party — with
classification, package counts, and comprehensive per-device breakdowns.

Uses the same ADB relay + chunked response reading as neighborhood_extractor.py
(proven to work around sync_cmd 2000-byte output limit).

Usage:
  python3 tools/neighborhood_apps_reporter.py                    # Full scan + report
  python3 tools/neighborhood_apps_reporter.py quick [N]          # Quick scan of N devices (default 20)
  python3 tools/neighborhood_apps_reporter.py report             # Generate report from cached data
  python3 tools/neighborhood_apps_reporter.py single <IP>        # Scan single device
"""

import asyncio
import json
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Reuse the bridge infrastructure from the extractor
from tools.neighborhood_extractor import (
    CloudBridge, HIGH_VALUE_PKGS, SYSTEM_PREFIXES, FINTECH_KEYWORDS,
    HOSTS_FILE, HARVEST_SCAN, BASE_DIR,
    phase1_scan,
)

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

REPORT_DIR = BASE_DIR / "reports" / "apps_reports"
PROGRESS_FILE = REPORT_DIR / "scan_progress.json"
OUR_IP = "10.0.21.62"


# ═══════════════════════════════════════════════════════════════════════
# APP CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════

# Well-known system packages (always present on Android/VMOS)
KNOWN_SYSTEM = {
    "android", "com.android.systemui", "com.android.settings",
    "com.android.launcher3", "com.android.providers.settings",
    "com.android.providers.media", "com.android.providers.contacts",
    "com.android.providers.telephony", "com.android.phone",
    "com.android.server.telecom", "com.android.bluetooth",
    "com.android.nfc", "com.android.shell", "com.android.inputmethod.latin",
    "com.android.camera2", "com.android.documentsui",
    "com.android.certinstaller", "com.android.packageinstaller",
    "com.android.permissioncontroller", "com.android.webview",
    "com.google.android.gms", "com.google.android.gsf",
    "com.google.android.ext.services",
}

# App category classification
APP_CATEGORIES = {
    "finance": ["pay", "wallet", "bank", "cash", "money", "transfer", "remit",
                "credit", "loan", "finance", "invest", "trading"],
    "crypto": ["crypto", "coin", "btc", "eth", "nft", "defi", "token",
              "blockchain", "metamask", "phantom", "binance", "coinbase"],
    "social": ["whatsapp", "telegram", "messenger", "instagram", "facebook",
              "twitter", "tiktok", "snapchat", "discord", "signal", "viber",
              "wechat", "line.", "kakaotalk"],
    "shopping": ["amazon", "ebay", "aliexpress", "shopify", "shopee", "lazada",
                "wish", "etsy", "mercari", "depop", "poshmark"],
    "transport": ["uber", "lyft", "bolt", "grab", "didi", "blablacar",
                  "citymapper", "moovit", "transit"],
    "food": ["doordash", "ubereats", "grubhub", "deliveroo", "justeat",
            "foodpanda", "swiggy", "zomato"],
    "streaming": ["netflix", "spotify", "youtube", "disney", "hbo", "hulu",
                  "prime.video", "twitch", "deezer", "tidal"],
    "vpn": ["vpn", "nordvpn", "expressvpn", "surfshark", "protonvpn",
           "mullvad", "windscribe"],
    "email": ["gmail", "outlook", "yahoo.mail", "protonmail", "tutanota"],
    "cloud": ["dropbox", "onedrive", "gdrive", "icloud", "mega", "box."],
    "security": ["authenticator", "authy", "1password", "bitwarden",
                "lastpass", "keepass", "dashlane"],
    "gaming": ["game", "pubg", "fortnite", "roblox", "minecraft", "genshin",
              "supercell", "gameloft", "rovio", "king.com"],
}


def classify_package(pkg: str, is_third_party: bool) -> dict:
    """Classify a package into type and category."""
    pkg_lower = pkg.lower()

    # Determine type
    if not is_third_party:
        pkg_type = "system"
    else:
        pkg_type = "third_party"

    # Determine category
    category = "other"
    if pkg in HIGH_VALUE_PKGS:
        name, score = HIGH_VALUE_PKGS[pkg]
        category = "high_value"
    else:
        for cat_name, keywords in APP_CATEGORIES.items():
            if any(kw in pkg_lower for kw in keywords):
                category = cat_name
                break

    # Check if it's a known system package
    is_system_prefix = any(pkg_lower.startswith(prefix) for prefix in SYSTEM_PREFIXES)

    return {
        "package": pkg,
        "type": pkg_type,
        "category": category,
        "is_system_prefix": is_system_prefix,
        "known_name": HIGH_VALUE_PKGS.get(pkg, (None, 0))[0],
    }


# ═══════════════════════════════════════════════════════════════════════
# DEVICE SCANNING
# ═══════════════════════════════════════════════════════════════════════

async def scan_device_apps(bridge: CloudBridge, ip: str) -> dict:
    """Scan a single neighbor device for ALL installed apps."""
    compound = (
        "echo '===IDENTITY==='; "
        "echo MODEL:$(getprop ro.product.model); "
        "echo BRAND:$(getprop ro.product.brand); "
        "echo MANUF:$(getprop ro.product.manufacturer); "
        "echo SERIAL:$(getprop ro.serialno); "
        "echo ANDROID:$(getprop ro.build.version.release); "
        "echo FP:$(getprop ro.build.fingerprint); "
        "echo '===SHELL==='; "
        "id | head -1; "
        "echo '===ALL_PKGS==='; "
        "pm list packages 2>/dev/null; "
        "echo '===THIRD_PARTY==='; "
        "pm list packages -3 2>/dev/null; "
        "echo '===END===';"
    )
    out = await bridge.neighbor_cmd(ip, compound, timeout=10)

    if not out or "===IDENTITY===" not in out:
        return {"ip": ip, "status": "unreachable", "error": (out or "no response")[:200]}

    sections = _parse_sections(out)

    # Parse identity using key=value format (robust against empty getprop values)
    props_raw = sections.get("IDENTITY", [])
    props_dict = {}
    for line in props_raw:
        if ":" in line:
            key, _, val = line.partition(":")
            props_dict[key.strip()] = val.strip()
    identity = {
        "model": props_dict.get("MODEL", ""),
        "brand": props_dict.get("BRAND", ""),
        "manufacturer": props_dict.get("MANUF", ""),
        "serial": props_dict.get("SERIAL", ""),
        "android": props_dict.get("ANDROID", ""),
        "fingerprint": props_dict.get("FP", ""),
    }

    shell_lines = sections.get("SHELL", [])
    shell_access = "root" if any("uid=0" in l for l in shell_lines) else "shell"

    # Parse packages
    all_pkgs = sorted(set(
        p.replace("package:", "").strip()
        for p in sections.get("ALL_PKGS", [])
        if p.startswith("package:")
    ))
    third_party = sorted(set(
        p.replace("package:", "").strip()
        for p in sections.get("THIRD_PARTY", [])
        if p.startswith("package:")
    ))
    third_party_set = set(third_party)

    # Classify every package
    system_apps = []
    third_party_apps = []
    high_value_apps = []
    fintech_apps = []
    categorized = defaultdict(list)
    score = 0

    for pkg in all_pkgs:
        is_tp = pkg in third_party_set
        classification = classify_package(pkg, is_tp)

        if is_tp:
            third_party_apps.append(classification)
        else:
            system_apps.append(classification)

        categorized[classification["category"]].append(pkg)

        if pkg in HIGH_VALUE_PKGS:
            name, pts = HIGH_VALUE_PKGS[pkg]
            score += pts
            high_value_apps.append({"package": pkg, "name": name, "score": pts})
        elif is_tp and any(kw in pkg.lower() for kw in FINTECH_KEYWORDS):
            score += 3
            fintech_apps.append(pkg)

    return {
        "ip": ip,
        "status": "alive",
        "identity": identity,
        "shell": shell_access,
        "all_packages": all_pkgs,
        "system_apps": [a["package"] for a in system_apps],
        "third_party_apps": [a["package"] for a in third_party_apps],
        "all_count": len(all_pkgs),
        "system_count": len(system_apps),
        "third_party_count": len(third_party_apps),
        "categories": {k: sorted(v) for k, v in categorized.items()},
        "high_value_apps": high_value_apps,
        "fintech_apps": fintech_apps,
        "score": score,
        "scanned_at": datetime.now().isoformat(),
    }


def _parse_sections(text: str) -> dict:
    """Parse ===SECTION=== delimited output into dict."""
    sections = {}
    current = None
    lines_buf = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("===") and line.endswith("==="):
            if current:
                sections[current] = lines_buf
            current = line.strip("=")
            lines_buf = []
        elif current and line:
            lines_buf.append(line)
    if current:
        sections[current] = lines_buf
    return sections


# ═══════════════════════════════════════════════════════════════════════
# SCANNING PIPELINE
# ═══════════════════════════════════════════════════════════════════════

async def scan_neighborhood(hosts: list[str], limit: int = 0) -> list[dict]:
    """Scan all neighborhood devices for apps."""
    bridge = CloudBridge()
    target_hosts = hosts[:limit] if limit > 0 else hosts
    target_hosts = [h for h in target_hosts if h != OUR_IP]

    print(f"\n{'='*70}")
    print(f"SCANNING {len(target_hosts)} DEVICES FOR ALL APPS")
    print(f"{'='*70}")

    # Resume from progress if exists
    scanned = {}
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            saved = json.load(f)
        scanned = {d["ip"]: d for d in saved.get("devices", []) if d.get("ip")}
        print(f"  Resuming: {len(scanned)} already done")

    remaining = [h for h in target_hosts if h not in scanned]
    if not remaining:
        print("  All hosts already scanned")
        return list(scanned.values())

    print(f"  Remaining: {len(remaining)} devices")
    start = time.time()
    errors = 0

    DEVICE_TIMEOUT = 90  # max seconds per device before skipping

    for i, ip in enumerate(remaining):
        try:
            device = await asyncio.wait_for(scan_device_apps(bridge, ip), timeout=DEVICE_TIMEOUT)
            scanned[ip] = device
            if device["status"] == "alive":
                ident = device.get("identity", {})
                m = ident.get("model", "?")
                b = ident.get("brand", "?")
                n_all = device.get("all_count", 0)
                n_sys = device.get("system_count", 0)
                n_tp = device.get("third_party_count", 0)
                hv = len(device.get("high_value_apps", []))
                hv_str = f" ★{device['score']}" if hv > 0 else ""
                print(f"  [{len(scanned)}/{len(target_hosts)}] {ip} → {b} {m} ({n_sys}sys/{n_tp}tp = {n_all} total){hv_str}")
            else:
                errors += 1
                if errors <= 5 or errors % 20 == 0:
                    print(f"  [{len(scanned)}/{len(target_hosts)}] {ip} → unreachable")
        except asyncio.TimeoutError:
            errors += 1
            scanned[ip] = {"ip": ip, "status": "timeout", "error": f"scan exceeded {DEVICE_TIMEOUT}s"}
            print(f"  [{len(scanned)}/{len(target_hosts)}] {ip} → TIMEOUT ({DEVICE_TIMEOUT}s)")
        except Exception as e:
            errors += 1
            scanned[ip] = {"ip": ip, "status": "error", "error": str(e)[:200]}

        # Save progress every 5 devices
        if len(scanned) % 5 == 0:
            _save_progress(scanned)

    _save_progress(scanned)
    elapsed = time.time() - start
    alive = [d for d in scanned.values() if d.get("status") == "alive"]
    scored = [d for d in alive if d.get("score", 0) > 0]
    print(f"\n  ✓ Scan: {len(alive)} alive, {len(scored)} high-value, {errors} errors, {elapsed/60:.1f}min")
    print(f"  API calls: {bridge.api_calls}")
    return list(scanned.values())


def _save_progress(scanned: dict):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "device_count": len(scanned),
            "devices": list(scanned.values()),
        }, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════
# REPORTING
# ═══════════════════════════════════════════════════════════════════════

def generate_report(devices: list[dict]) -> dict:
    """Generate comprehensive all-apps report."""
    print(f"\n{'='*70}")
    print("GENERATING ALL-APPS REPORT")
    print(f"{'='*70}")

    alive = [d for d in devices if d.get("status") == "alive"]
    dead = [d for d in devices if d.get("status") != "alive"]

    # Aggregate data
    brands = defaultdict(int)
    models = defaultdict(int)
    android_versions = defaultdict(int)
    all_packages_freq = defaultdict(int)
    system_packages_freq = defaultdict(int)
    third_party_freq = defaultdict(int)
    category_totals = defaultdict(lambda: defaultdict(int))
    high_value_presence = defaultdict(int)

    per_device_reports = []

    for d in alive:
        ident = d.get("identity", {})
        brands[ident.get("brand", "?")] += 1
        models[ident.get("model", "?")] += 1
        android_versions[ident.get("android", "?")] += 1

        for pkg in d.get("all_packages", []):
            all_packages_freq[pkg] += 1
        for pkg in d.get("system_apps", []):
            system_packages_freq[pkg] += 1
        for pkg in d.get("third_party_apps", []):
            third_party_freq[pkg] += 1

        categories = d.get("categories", {})
        for cat, pkgs in categories.items():
            for pkg in pkgs:
                category_totals[cat][pkg] += 1

        for app in d.get("high_value_apps", []):
            high_value_presence[app["package"]] += 1

        per_device_reports.append({
            "ip": d["ip"],
            "brand": ident.get("brand", "?"),
            "model": ident.get("model", "?"),
            "android": ident.get("android", "?"),
            "serial": ident.get("serial", "?"),
            "shell": d.get("shell", "?"),
            "total_apps": d.get("all_count", 0),
            "system_apps": d.get("system_count", 0),
            "third_party_apps": d.get("third_party_count", 0),
            "score": d.get("score", 0),
            "high_value": [a["name"] for a in d.get("high_value_apps", [])],
            "all_system_list": d.get("system_apps", []),
            "all_third_party_list": d.get("third_party_apps", []),
        })

    # Sort everything
    per_device_reports.sort(key=lambda x: x["score"], reverse=True)

    # High-value app presence with names
    hv_report = {}
    for pkg, count in sorted(high_value_presence.items(), key=lambda x: x[1], reverse=True):
        name = HIGH_VALUE_PKGS.get(pkg, ("Unknown", 0))[0]
        hv_report[name] = {"package": pkg, "devices": count}

    # Category summaries
    cat_summary = {}
    for cat, pkgs in sorted(category_totals.items()):
        cat_summary[cat] = {
            "unique_apps": len(pkgs),
            "total_installs": sum(pkgs.values()),
            "top_apps": dict(sorted(pkgs.items(), key=lambda x: x[1], reverse=True)[:10]),
        }

    report = {
        "report_info": {
            "generated": datetime.now().isoformat(),
            "tool": "neighborhood_apps_reporter v1.0",
            "total_scanned": len(devices),
            "alive": len(alive),
            "unreachable": len(dead),
        },
        "summary": {
            "unique_packages_total": len(all_packages_freq),
            "unique_system_packages": len(system_packages_freq),
            "unique_third_party_packages": len(third_party_freq),
            "avg_total_apps": round(sum(d.get("all_count", 0) for d in alive) / max(len(alive), 1), 1),
            "avg_system_apps": round(sum(d.get("system_count", 0) for d in alive) / max(len(alive), 1), 1),
            "avg_third_party_apps": round(sum(d.get("third_party_count", 0) for d in alive) / max(len(alive), 1), 1),
            "max_total_apps": max((d.get("all_count", 0) for d in alive), default=0),
            "max_third_party": max((d.get("third_party_count", 0) for d in alive), default=0),
            "high_value_device_count": sum(1 for d in alive if d.get("score", 0) > 0),
        },
        "brands": dict(sorted(brands.items(), key=lambda x: x[1], reverse=True)),
        "android_versions": dict(sorted(android_versions.items(), key=lambda x: x[1], reverse=True)),
        "most_common_system_apps_top50": dict(
            sorted(system_packages_freq.items(), key=lambda x: x[1], reverse=True)[:50]
        ),
        "most_common_third_party_top50": dict(
            sorted(third_party_freq.items(), key=lambda x: x[1], reverse=True)[:50]
        ),
        "all_packages_by_frequency_top100": dict(
            sorted(all_packages_freq.items(), key=lambda x: x[1], reverse=True)[:100]
        ),
        "high_value_app_presence": hv_report,
        "app_categories": cat_summary,
        "per_device_details": per_device_reports,
    }

    # Save reports
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = REPORT_DIR / f"all_apps_report_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    txt_path = REPORT_DIR / f"all_apps_report_{timestamp}.txt"
    _write_text_report(report, txt_path)

    # Also save latest symlink-style copy
    with open(REPORT_DIR / "latest_report.json", "w") as f:
        json.dump(report, f, indent=2)
    _write_text_report(report, REPORT_DIR / "latest_report.txt")

    # Print summary
    s = report["summary"]
    print(f"\n  Devices scanned:       {len(alive)} alive / {len(devices)} total")
    print(f"  Unique packages total: {s['unique_packages_total']}")
    print(f"  Unique system pkgs:    {s['unique_system_packages']}")
    print(f"  Unique 3rd-party pkgs: {s['unique_third_party_packages']}")
    print(f"  Avg apps per device:   {s['avg_total_apps']} ({s['avg_system_apps']} sys / {s['avg_third_party_apps']} tp)")
    print(f"  High-value devices:    {s['high_value_device_count']}")
    if hv_report:
        print(f"\n  HIGH-VALUE APPS FOUND:")
        for name, info in hv_report.items():
            print(f"    {name} ({info['package']}): {info['devices']} device(s)")
    if third_party_freq:
        print(f"\n  TOP 15 THIRD-PARTY APPS:")
        for pkg, count in sorted(third_party_freq.items(), key=lambda x: x[1], reverse=True)[:15]:
            name = HIGH_VALUE_PKGS.get(pkg, (pkg, 0))[0]
            if name == pkg:
                name = pkg.split(".")[-1] if "." in pkg else pkg
            print(f"    {name}: {count} device(s)")

    print(f"\n  Reports saved:")
    print(f"    {json_path}")
    print(f"    {txt_path}")

    return report


def _write_text_report(report: dict, path: Path):
    """Write human-readable text report."""
    info = report.get("report_info", {})
    s = report.get("summary", {})

    lines = [
        "=" * 80,
        "  NEIGHBORHOOD ALL-APPS REPORT",
        f"  Generated: {info.get('generated', '')}",
        f"  Tool: {info.get('tool', '')}",
        "=" * 80,
        "",
        "┌─────────────────────────────────────────────────┐",
        "│  SCAN SUMMARY                                   │",
        "├─────────────────────────────────────────────────┤",
        f"│  Devices scanned:       {info.get('total_scanned', 0):<23} │",
        f"│  Alive:                 {info.get('alive', 0):<23} │",
        f"│  Unreachable:           {info.get('unreachable', 0):<23} │",
        f"│  Unique pkgs (all):     {s.get('unique_packages_total', 0):<23} │",
        f"│  Unique system pkgs:    {s.get('unique_system_packages', 0):<23} │",
        f"│  Unique 3rd-party pkgs: {s.get('unique_third_party_packages', 0):<23} │",
        f"│  Avg total per device:  {s.get('avg_total_apps', 0):<23} │",
        f"│  Avg system per device: {s.get('avg_system_apps', 0):<23} │",
        f"│  Avg 3p per device:     {s.get('avg_third_party_apps', 0):<23} │",
        f"│  High-value devices:    {s.get('high_value_device_count', 0):<23} │",
        "└─────────────────────────────────────────────────┘",
        "",
    ]

    # Brands
    lines += ["DEVICE BRANDS", "-" * 50]
    for brand, count in report.get("brands", {}).items():
        bar = "█" * min(count, 30)
        lines.append(f"  {brand:<25} {count:>3} {bar}")
    lines.append("")

    # Android versions
    lines += ["ANDROID VERSIONS", "-" * 50]
    for ver, count in report.get("android_versions", {}).items():
        lines.append(f"  {ver:<40} {count:>3}")
    lines.append("")

    # High-value apps
    hv = report.get("high_value_app_presence", {})
    if hv:
        lines += ["HIGH-VALUE APP PRESENCE", "-" * 50]
        for name, info in hv.items():
            bar = "★" * min(info["devices"], 20)
            lines.append(f"  {name:<30} {info['devices']:>3} device(s) {bar}")
        lines.append("")

    # Top system apps
    lines += ["TOP 50 SYSTEM APPS (by install count)", "-" * 50]
    for pkg, count in list(report.get("most_common_system_apps_top50", {}).items())[:50]:
        lines.append(f"  {count:>3}x  {pkg}")
    lines.append("")

    # Top 3rd-party apps
    lines += ["TOP 50 THIRD-PARTY APPS (by install count)", "-" * 50]
    for pkg, count in list(report.get("most_common_third_party_top50", {}).items())[:50]:
        name = HIGH_VALUE_PKGS.get(pkg, (None, 0))[0]
        suffix = f" [{name}]" if name else ""
        lines.append(f"  {count:>3}x  {pkg}{suffix}")
    lines.append("")

    # App categories
    lines += ["APP CATEGORIES", "-" * 50]
    for cat, info in report.get("app_categories", {}).items():
        lines.append(f"  {cat.upper()}: {info.get('unique_apps', 0)} unique apps, "
                      f"{info.get('total_installs', 0)} total installs")
        for pkg, cnt in list(info.get("top_apps", {}).items())[:5]:
            lines.append(f"    {cnt:>3}x  {pkg}")
    lines.append("")

    # Per-device details
    lines += ["PER-DEVICE BREAKDOWN", "=" * 80]
    for d in report.get("per_device_details", []):
        score_str = f" ★{d['score']}" if d.get("score", 0) > 0 else ""
        lines.append(f"\n  {d['ip']} — {d['brand']} {d['model']}{score_str}")
        lines.append(f"  Android {d['android']} | Serial: {d['serial']} | Shell: {d['shell']}")
        lines.append(f"  Total: {d['total_apps']} | System: {d['system_apps']} | 3rd-party: {d['third_party_apps']}")
        if d.get("high_value"):
            lines.append(f"  High-value: {', '.join(d['high_value'])}")
        if d.get("all_third_party_list"):
            lines.append(f"  3rd-party packages:")
            for pkg in d["all_third_party_list"]:
                name = HIGH_VALUE_PKGS.get(pkg, (None, 0))[0]
                suffix = f" [{name}]" if name else ""
                lines.append(f"    • {pkg}{suffix}")
        lines.append(f"  System packages ({d['system_apps']}):")
        for pkg in d.get("all_system_list", []):
            lines.append(f"    · {pkg}")

    with open(path, "w") as f:
        f.write("\n".join(lines))


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]

    if not args or args[0] == "full":
        # Full scan: discover hosts + scan all + report
        bridge = CloudBridge()
        hosts = await phase1_scan(bridge)
        devices = await scan_neighborhood(hosts)
        generate_report(devices)

    elif args[0] == "quick":
        # Quick scan on N devices
        n = int(args[1]) if len(args) > 1 else 20
        hosts = _load_hosts()
        if not hosts:
            print("No hosts available. Run full scan first.")
            return
        print(f"\nQuick scan: {n} devices from {len(hosts)} known hosts")
        devices = await scan_neighborhood(hosts, limit=n)
        generate_report(devices)

    elif args[0] == "report":
        # Generate report from cached progress
        if not PROGRESS_FILE.exists():
            print("No scan data. Run scan first.")
            return
        with open(PROGRESS_FILE) as f:
            data = json.load(f)
        devices = data.get("devices", [])
        print(f"Loaded {len(devices)} devices from cache")
        generate_report(devices)

    elif args[0] == "single":
        # Scan single device
        if len(args) < 2:
            print("Usage: single <IP>")
            return
        ip = args[1]
        bridge = CloudBridge()
        print(f"\nScanning {ip}...")
        device = await scan_device_apps(bridge, ip)
        if device["status"] == "alive":
            ident = device.get("identity", {})
            print(f"  Model:      {ident.get('model', '?')}")
            print(f"  Brand:      {ident.get('brand', '?')}")
            print(f"  Android:    {ident.get('android', '?')}")
            print(f"  Shell:      {device.get('shell', '?')}")
            print(f"  Total apps: {device.get('all_count', 0)}")
            print(f"  System:     {device.get('system_count', 0)}")
            print(f"  3rd-party:  {device.get('third_party_count', 0)}")
            if device.get("high_value_apps"):
                print(f"  High-value:")
                for a in device["high_value_apps"]:
                    print(f"    ★ {a['name']} ({a['package']}) +{a['score']}")
            print(f"\n  SYSTEM APPS ({device.get('system_count', 0)}):")
            for pkg in device.get("system_apps", []):
                print(f"    · {pkg}")
            print(f"\n  THIRD-PARTY APPS ({device.get('third_party_count', 0)}):")
            for pkg in device.get("third_party_apps", []):
                name = HIGH_VALUE_PKGS.get(pkg, (None, 0))[0]
                suffix = f" [{name}]" if name else ""
                print(f"    • {pkg}{suffix}")
        else:
            print(f"  Status: {device.get('status')} — {device.get('error', '')[:200]}")
        # Save single result
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_ip = ip.replace(".", "_")
        with open(REPORT_DIR / f"device_{safe_ip}.json", "w") as f:
            json.dump(device, f, indent=2)
    else:
        print(__doc__)


def _load_hosts() -> list[str]:
    """Load hosts from available sources."""
    if HARVEST_SCAN.exists():
        with open(HARVEST_SCAN) as f:
            data = json.load(f)
        hosts = [d["ip"] for d in data if isinstance(d, dict) and d.get("status") == "scanned"]
        if hosts:
            return hosts
    if HOSTS_FILE.exists():
        with open(HOSTS_FILE) as f:
            return [l.strip() for l in f if l.strip() and re.match(r'^\d+\.\d+\.\d+\.\d+$', l.strip())]
    return []


if __name__ == "__main__":
    asyncio.run(main())
