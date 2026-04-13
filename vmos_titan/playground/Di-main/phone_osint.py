#!/usr/bin/env python3
"""
Phone OSINT Engine — Multi-Source Number Intelligence
=====================================================
Aggregates data from free + freemium APIs to build target profile
from a phone number alone.  No carrier API access required.

Sources (in priority order):
  1. NumVerify       — carrier, line type, country (free: 100/mo)
  2. AbstractAPI     — carrier, line type, valid (free: 250/mo on signup)
  3. Veriphone       — validation + carrier (free: 1000/mo)
  4. Google libphonenumber — offline region/type analysis (no API)
  5. ipqualityscore  — fraud score, carrier, line (free: 5000/mo)

Usage:
    python3 phone_osint.py <msisdn>
    python3 phone_osint.py 94740873924

As library:
    from phone_osint import phone_lookup
    result = phone_lookup("94740873924")
"""

import os
import sys
import re
import json
import requests
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict


@dataclass
class PhoneIntel:
    msisdn: str
    valid: bool = False
    country: str = ""
    country_code: str = ""
    carrier: str = ""
    line_type: str = ""  # mobile, landline, voip, toll_free
    location: str = ""   # city/region hint
    fraud_score: int = -1
    is_voip: bool = False
    is_prepaid: bool = False
    name: str = ""       # from caller ID lookups
    sources: List[str] = field(default_factory=list)
    raw: Dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d.pop("raw", None)
        return d

    def summary(self) -> str:
        parts = [f"Number: {self.msisdn}"]
        if self.valid:
            parts.append("VALID")
        else:
            parts.append("UNVERIFIED")
        if self.carrier:
            parts.append(f"Carrier: {self.carrier}")
        if self.line_type:
            parts.append(f"Type: {self.line_type}")
        if self.location:
            parts.append(f"Region: {self.location}")
        if self.is_voip:
            parts.append("[VOIP]")
        if self.fraud_score >= 0:
            parts.append(f"FraudScore: {self.fraud_score}")
        if self.name:
            parts.append(f"Name: {self.name}")
        return " | ".join(parts)


def _normalize_msisdn(number: str) -> str:
    """Strip spaces, dashes, + prefix."""
    n = re.sub(r"[\s\-\(\)\.]", "", number)
    if n.startswith("+"):
        n = n[1:]
    # SL local → intl
    if n.startswith("0") and len(n) == 10:
        n = "94" + n[1:]
    return n


# ---- SRI LANKA OFFLINE CARRIER MAP ----

SL_CARRIERS = {
    "070": "Mobitel (SLT-Mobitel)",
    "071": "Mobitel (SLT-Mobitel)",
    "072": "Dialog Axiata",
    "074": "Dialog Axiata (ex-Hutch)",
    "075": "Dialog Axiata",
    "076": "Dialog Axiata",
    "077": "Dialog Axiata",
    "078": "Hutch (CK Hutchison)",
    "011": "SLT Landline",
    "021": "SLT Landline",
    "031": "SLT Landline",
    "033": "SLT Landline",
    "034": "SLT Landline",
    "035": "SLT Landline",
    "036": "SLT Landline",
    "037": "SLT Landline",
    "038": "SLT Landline",
    "041": "SLT Landline",
    "045": "SLT Landline",
    "047": "SLT Landline",
    "051": "SLT Landline",
    "054": "SLT Landline",
    "055": "SLT Landline",
    "057": "SLT Landline",
    "063": "SLT Landline",
    "065": "SLT Landline",
    "066": "SLT Landline",
    "067": "SLT Landline",
    "081": "SLT Landline",
    "091": "SLT Landline",
}

SL_REGIONS = {
    "011": "Colombo", "021": "Jaffna", "031": "Negombo", "033": "Kegalle",
    "034": "Kalutara", "035": "Kottawa", "036": "Avissawella", "037": "Kurunegala",
    "038": "Panadura", "041": "Matara", "045": "Ratnapura", "047": "Hambantota",
    "051": "Hatton", "054": "Nawalapitiya", "055": "Badulla", "057": "Bandarawela",
    "063": "Ampara", "065": "Batticaloa", "066": "Matale", "067": "Polonnaruwa",
    "081": "Kandy", "091": "Galle",
}


def _offline_lookup(msisdn: str) -> PhoneIntel:
    """Offline Sri Lanka carrier + region detection from number prefix."""
    result = PhoneIntel(msisdn=msisdn)

    if msisdn.startswith("94"):
        local = "0" + msisdn[2:]
    else:
        local = msisdn

    result.country = "Sri Lanka"
    result.country_code = "LK"

    prefix3 = local[:3]
    carrier = SL_CARRIERS.get(prefix3, "")
    if carrier:
        result.carrier = carrier
        result.valid = True
        if prefix3 in ("070", "071", "072", "074", "075", "076", "077", "078"):
            result.line_type = "mobile"
        else:
            result.line_type = "landline"
            region = SL_REGIONS.get(prefix3, "")
            if region:
                result.location = region
    else:
        # Generic SL mobile check
        if len(msisdn) == 11 and msisdn.startswith("94"):
            result.line_type = "mobile"
            result.valid = True

    result.sources.append("offline_sl_db")
    return result


# ---- API PROVIDERS ----

def _query_numverify(msisdn: str) -> Optional[dict]:
    """NumVerify API — free 100 req/mo."""
    key = os.getenv("NUMVERIFY_API_KEY", "")
    if not key:
        return None
    try:
        r = requests.get(
            "http://apilayer.net/api/validate",
            params={"access_key": key, "number": msisdn, "format": 1},
            timeout=8,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _query_abstractapi(msisdn: str) -> Optional[dict]:
    """AbstractAPI — free 250 req/mo on signup."""
    key = os.getenv("ABSTRACTAPI_KEY", "")
    if not key:
        return None
    try:
        r = requests.get(
            f"https://phonevalidation.abstractapi.com/v1/",
            params={"api_key": key, "phone": msisdn},
            timeout=8,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _query_veriphone(msisdn: str) -> Optional[dict]:
    """Veriphone — free 1000 req/mo."""
    key = os.getenv("VERIPHONE_API_KEY", "")
    if not key:
        return None
    try:
        r = requests.get(
            f"https://api.veriphone.io/v2/verify",
            params={"phone": msisdn, "key": key},
            timeout=8,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _query_ipqs(msisdn: str) -> Optional[dict]:
    """IPQualityScore — free 5000 req/mo on signup. Returns fraud score."""
    key = os.getenv("IPQS_API_KEY", "")
    if not key:
        return None
    try:
        r = requests.get(
            f"https://ipqualityscore.com/api/json/phone/{key}/{msisdn}",
            timeout=8,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def phone_lookup(number: str) -> PhoneIntel:
    """
    Multi-source phone intelligence lookup.
    Works with zero API keys (offline SL DB) and improves with each key configured.
    """
    msisdn = _normalize_msisdn(number)

    # Start with offline SL database
    result = _offline_lookup(msisdn)

    # Layer 1: NumVerify
    nv = _query_numverify(msisdn)
    if nv and nv.get("valid"):
        result.valid = True
        result.carrier = nv.get("carrier", result.carrier) or result.carrier
        result.location = nv.get("location", result.location) or result.location
        result.line_type = nv.get("line_type", result.line_type) or result.line_type
        result.country = nv.get("country_name", result.country) or result.country
        result.sources.append("numverify")
        result.raw["numverify"] = nv

    # Layer 2: AbstractAPI
    ab = _query_abstractapi(msisdn)
    if ab and ab.get("valid"):
        result.valid = True
        c = ab.get("carrier", {})
        result.carrier = c.get("name", result.carrier) or result.carrier
        result.line_type = ab.get("type", result.line_type) or result.line_type
        result.location = ab.get("location", result.location) or result.location
        result.country = ab.get("country", {}).get("name", result.country) or result.country
        result.sources.append("abstractapi")
        result.raw["abstractapi"] = ab

    # Layer 3: Veriphone
    vp = _query_veriphone(msisdn)
    if vp and vp.get("phone_valid"):
        result.valid = True
        result.carrier = vp.get("carrier", result.carrier) or result.carrier
        result.line_type = vp.get("phone_type", result.line_type) or result.line_type
        result.country = vp.get("country", result.country) or result.country
        result.sources.append("veriphone")
        result.raw["veriphone"] = vp

    # Layer 4: IPQS (fraud scoring)
    ipqs = _query_ipqs(msisdn)
    if ipqs and ipqs.get("success"):
        result.fraud_score = int(ipqs.get("fraud_score", -1))
        result.is_voip = bool(ipqs.get("VOIP"))
        result.is_prepaid = bool(ipqs.get("prepaid"))
        result.carrier = ipqs.get("carrier", result.carrier) or result.carrier
        result.name = ipqs.get("name", "") or result.name
        result.location = ipqs.get("city", result.location) or result.location
        if ipqs.get("region"):
            result.location = f"{result.location}, {ipqs['region']}".strip(", ")
        result.sources.append("ipqualityscore")
        result.raw["ipqualityscore"] = ipqs

    return result


# ---- CLI ----
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 phone_osint.py <msisdn>")
        print("\nFree API keys (set in env for richer results):")
        print("  NUMVERIFY_API_KEY    — apilayer.com (100/mo free)")
        print("  ABSTRACTAPI_KEY      — abstractapi.com (250/mo free)")
        print("  VERIPHONE_API_KEY    — veriphone.io (1000/mo free)")
        print("  IPQS_API_KEY         — ipqualityscore.com (5000/mo free)")
        sys.exit(1)

    target = sys.argv[1]
    print(f"\n[*] Phone OSINT lookup: {target}\n")

    intel = phone_lookup(target)
    print(f"  {intel.summary()}")
    print(f"\n  Sources used: {', '.join(intel.sources)}")

    # Show which API keys are configured
    keys = {
        "NUMVERIFY_API_KEY": bool(os.getenv("NUMVERIFY_API_KEY")),
        "ABSTRACTAPI_KEY": bool(os.getenv("ABSTRACTAPI_KEY")),
        "VERIPHONE_API_KEY": bool(os.getenv("VERIPHONE_API_KEY")),
        "IPQS_API_KEY": bool(os.getenv("IPQS_API_KEY")),
    }
    configured = sum(1 for v in keys.values() if v)
    print(f"\n  API keys configured: {configured}/4")
    for k, v in keys.items():
        status = "✓ SET" if v else "✗ NOT SET"
        print(f"    {k}: {status}")
    print()
