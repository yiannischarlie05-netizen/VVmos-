#!/usr/bin/env python3
"""
HLR Lookup Engine — Home Location Register Query via Commercial APIs
====================================================================
Queries real HLR/SS7 data through legitimate commercial API gateways.
Returns: carrier, roaming status, ported status, MCC/MNC, IMSI prefix,
original network, current MSC/VLR hints.

Providers (in priority order):
  1. hlrlookup.com    — Free tier: 50 lookups (HLR_LOOKUP_API_KEY + HLR_LOOKUP_PASSWORD)
  2. Infobip          — Freemium: number validation + porting (INFOBIP_API_KEY)
  3. MessageBird      — Freemium: HLR lookup (MESSAGEBIRD_API_KEY)
  4. D7Networks       — AE-based provider with SL coverage (D7_API_TOKEN)

Usage:
    python3 hlr_lookup.py <msisdn>
    python3 hlr_lookup.py 94740873924

As library:
    from hlr_lookup import hlr_query
    result = hlr_query("94740873924")
"""

import os
import sys
import json
import base64
import requests
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, List


@dataclass
class HLRResult:
    msisdn: str
    valid: bool = False
    carrier: str = ""
    original_carrier: str = ""
    mcc: str = ""
    mnc: str = ""
    country: str = ""
    ported: bool = False
    roaming: bool = False
    roaming_country: str = ""
    roaming_carrier: str = ""
    status: str = ""        # active, absent, busy, no_teleservice, not_reachable
    imsi_prefix: str = ""
    msc: str = ""           # Mobile Switching Center address (location hint)
    hlr: str = ""           # Home Location Register address
    sources: List[str] = field(default_factory=list)
    raw: Dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d.pop("raw", None)
        return d

    def summary(self) -> str:
        parts = [self.msisdn]
        if self.valid:
            parts.append("ACTIVE" if self.status in ("active", "") else self.status.upper())
        else:
            parts.append("INVALID/INACTIVE")
        if self.carrier:
            parts.append(f"Carrier: {self.carrier}")
        if self.ported:
            parts.append(f"PORTED from {self.original_carrier}")
        if self.roaming:
            rc = f" ({self.roaming_country})" if self.roaming_country else ""
            parts.append(f"ROAMING{rc}")
        if self.mcc and self.mnc:
            parts.append(f"MCC/MNC: {self.mcc}/{self.mnc}")
        if self.msc:
            parts.append(f"MSC: {self.msc}")
        return " | ".join(parts)


def _query_hlrlookup(msisdn: str) -> Optional[dict]:
    """hlrlookup.com — free 50 requests. Returns full HLR record."""
    api_key = os.getenv("HLR_LOOKUP_API_KEY", "")
    password = os.getenv("HLR_LOOKUP_PASSWORD", "")
    if not api_key or not password:
        return None
    try:
        r = requests.get(
            f"https://www.hlrlookup.com/api/hlr/",
            params={"apikey": api_key, "password": password, "msisdn": msisdn},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "ok":
                return data
    except Exception:
        pass
    return None


def _query_infobip(msisdn: str) -> Optional[dict]:
    """Infobip Number Context API — freemium."""
    api_key = os.getenv("INFOBIP_API_KEY", "")
    base_url = os.getenv("INFOBIP_BASE_URL", "https://api.infobip.com")
    if not api_key:
        return None
    try:
        r = requests.post(
            f"{base_url}/number/1/query",
            headers={
                "Authorization": f"App {api_key}",
                "Content-Type": "application/json",
            },
            json={"to": [msisdn]},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                return results[0]
    except Exception:
        pass
    return None


def _query_messagebird(msisdn: str) -> Optional[dict]:
    """MessageBird HLR Lookup — freemium."""
    api_key = os.getenv("MESSAGEBIRD_API_KEY", "")
    if not api_key:
        return None
    try:
        # Create HLR request
        r = requests.post(
            "https://rest.messagebird.com/hlr",
            headers={"Authorization": f"AccessKey {api_key}"},
            json={"msisdn": int(msisdn)},
            timeout=15,
        )
        if r.status_code in (200, 201):
            data = r.json()
            # Poll for result (HLR is async)
            hlr_id = data.get("id")
            if hlr_id:
                import time
                for _ in range(5):
                    time.sleep(2)
                    poll = requests.get(
                        f"https://rest.messagebird.com/hlr/{hlr_id}",
                        headers={"Authorization": f"AccessKey {api_key}"},
                        timeout=10,
                    )
                    if poll.status_code == 200:
                        result = poll.json()
                        if result.get("status") == "active":
                            return result
                return data
    except Exception:
        pass
    return None


def _query_d7(msisdn: str) -> Optional[dict]:
    """D7 Networks — AE-based provider. Number Lookup API."""
    token = os.getenv("D7_API_TOKEN", "")
    if not token:
        return None
    try:
        r = requests.post(
            "https://api.d7networks.com/hlr/v1/lookup",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"recipients": [msisdn]},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def hlr_query(number: str) -> HLRResult:
    """Multi-provider HLR lookup. Returns best available data."""
    msisdn = number.replace("+", "").replace(" ", "").replace("-", "")
    if msisdn.startswith("0") and len(msisdn) == 10:
        msisdn = "94" + msisdn[1:]

    result = HLRResult(msisdn=msisdn)

    # Provider 1: hlrlookup.com (richest data)
    hlr = _query_hlrlookup(msisdn)
    if hlr:
        r = hlr.get("result", hlr)
        result.valid = True
        result.carrier = r.get("original_network_name", "")
        result.original_carrier = r.get("original_network_name", "")
        result.mcc = str(r.get("mcc", ""))
        result.mnc = str(r.get("mnc", ""))
        result.country = r.get("country_name", "")
        result.ported = bool(r.get("is_ported"))
        result.roaming = bool(r.get("is_roaming"))
        result.roaming_country = r.get("roaming_country_name", "")
        result.status = r.get("status_desc", "active")
        result.imsi_prefix = str(r.get("imsi", ""))[:6]
        result.msc = str(r.get("msc", ""))
        result.hlr = str(r.get("servingHlr", ""))
        if r.get("current_network_name"):
            result.carrier = r["current_network_name"]
        result.sources.append("hlrlookup.com")
        result.raw["hlrlookup"] = hlr

    # Provider 2: Infobip
    info = _query_infobip(msisdn)
    if info:
        nc = info.get("numberContext", info)
        result.valid = True
        mno = nc.get("originalNetwork", nc.get("currentNetwork", {}))
        if isinstance(mno, dict):
            result.carrier = mno.get("networkName", result.carrier) or result.carrier
            result.mcc = str(mno.get("countryCode", result.mcc)) or result.mcc
            result.mnc = str(mno.get("networkCode", result.mnc)) or result.mnc
        result.ported = bool(nc.get("portedNetwork") or nc.get("isPorted"))
        result.status = nc.get("status", result.status) or result.status
        result.sources.append("infobip")
        result.raw["infobip"] = info

    # Provider 3: MessageBird
    mb = _query_messagebird(msisdn)
    if mb:
        result.valid = True
        nw = mb.get("network", {})
        if isinstance(nw, dict):
            result.carrier = nw.get("name", result.carrier) or result.carrier
            result.mcc = str(nw.get("mcc", result.mcc)) or result.mcc
            result.mnc = str(nw.get("mnc", result.mnc)) or result.mnc
        result.status = mb.get("statusDescription", result.status) or result.status
        result.sources.append("messagebird")
        result.raw["messagebird"] = mb

    # Provider 4: D7
    d7 = _query_d7(msisdn)
    if d7:
        entries = d7.get("data", [d7])
        if entries and isinstance(entries, list):
            e = entries[0] if entries else d7
            result.valid = True
            result.carrier = e.get("operator", result.carrier) or result.carrier
            result.country = e.get("country", result.country) or result.country
            result.status = e.get("status", result.status) or result.status
            result.sources.append("d7networks")
            result.raw["d7"] = d7

    # Fallback: offline SL carrier map
    if not result.carrier and msisdn.startswith("94"):
        local_prefix = "0" + msisdn[2:5]
        prefix3 = local_prefix[:3]
        from phone_osint import SL_CARRIERS
        carrier = SL_CARRIERS.get(prefix3, "")
        if carrier:
            result.carrier = carrier
            result.valid = True
            result.country = "Sri Lanka"
            result.mcc = "413"
            result.sources.append("offline_sl_db")

    return result


# ---- CLI ----
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 hlr_lookup.py <msisdn>")
        print("\nAPI keys (set in env):")
        print("  HLR_LOOKUP_API_KEY + HLR_LOOKUP_PASSWORD  — hlrlookup.com (50 free)")
        print("  INFOBIP_API_KEY                           — infobip.com (freemium)")
        print("  MESSAGEBIRD_API_KEY                       — messagebird.com (freemium)")
        print("  D7_API_TOKEN                              — d7networks.com (freemium)")
        sys.exit(1)

    target = sys.argv[1]
    print(f"\n[*] HLR Lookup: {target}\n")

    r = hlr_query(target)
    print(f"  {r.summary()}")
    print(f"\n  Sources: {', '.join(r.sources) or 'none'}")

    keys = {
        "HLR_LOOKUP_API_KEY": bool(os.getenv("HLR_LOOKUP_API_KEY")),
        "INFOBIP_API_KEY": bool(os.getenv("INFOBIP_API_KEY")),
        "MESSAGEBIRD_API_KEY": bool(os.getenv("MESSAGEBIRD_API_KEY")),
        "D7_API_TOKEN": bool(os.getenv("D7_API_TOKEN")),
    }
    configured = sum(1 for v in keys.values() if v)
    print(f"\n  HLR API keys configured: {configured}/4")
    for k, v in keys.items():
        print(f"    {k}: {'✓ SET' if v else '✗ NOT SET'}")
    print()
