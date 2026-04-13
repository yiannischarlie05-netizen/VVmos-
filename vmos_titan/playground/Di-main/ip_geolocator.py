#!/usr/bin/env python3
"""
IP Geolocation Engine — Multi-Provider City/Region Resolver
============================================================
Queries 4 free IP geolocation APIs (no keys required) and returns
best-confidence result with ISP, carrier, and VPN/proxy detection.

Usage:
    python3 ip_geolocator.py <ip_address>
    python3 ip_geolocator.py 1.2.3.4
    
As library:
    from ip_geolocator import geolocate_ip
    result = geolocate_ip("1.2.3.4")
"""

import sys
import json
import time
import requests
from dataclasses import dataclass, asdict
from typing import Optional, List

# --- Free IP Geolocation Providers (no API key) ---

PROVIDERS = [
    {
        "name": "ip-api.com",
        "url": "http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,mobile,proxy,hosting,query",
        "rate_limit": 45,  # per minute
    },
    {
        "name": "ipwho.is",
        "url": "https://ipwho.is/{ip}",
        "rate_limit": 10000,
    },
    {
        "name": "ipapi.co",
        "url": "https://ipapi.co/{ip}/json/",
        "rate_limit": 30,
    },
    {
        "name": "freeipapi.com",
        "url": "https://freeipapi.com/api/json/{ip}",
        "rate_limit": 60,
    },
]


@dataclass
class GeoResult:
    ip: str
    country: str = ""
    region: str = ""
    city: str = ""
    lat: float = 0.0
    lon: float = 0.0
    zip_code: str = ""
    timezone: str = ""
    isp: str = ""
    org: str = ""
    asn: str = ""
    is_mobile: bool = False
    is_proxy: bool = False
    is_vpn: bool = False
    is_hosting: bool = False
    confidence: int = 0  # 0-100
    provider: str = ""
    raw: dict = None

    def to_dict(self):
        d = asdict(self)
        d.pop("raw", None)
        return d

    def summary(self) -> str:
        parts = []
        if self.city:
            parts.append(self.city)
        if self.region and self.region != self.city:
            parts.append(self.region)
        if self.country:
            parts.append(self.country)
        loc = ", ".join(parts) or "Unknown"
        flags = []
        if self.is_mobile:
            flags.append("MOBILE")
        if self.is_proxy or self.is_vpn:
            flags.append("VPN/PROXY")
        if self.is_hosting:
            flags.append("DATACENTER")
        flag_str = f" [{'/'.join(flags)}]" if flags else ""
        return f"{loc} ({self.lat:.4f}, {self.lon:.4f}) — {self.isp}{flag_str} [conf:{self.confidence}%]"


def _parse_ip_api(data: dict, ip: str) -> Optional[GeoResult]:
    if data.get("status") != "success":
        return None
    return GeoResult(
        ip=ip,
        country=data.get("country", ""),
        region=data.get("regionName", ""),
        city=data.get("city", ""),
        lat=float(data.get("lat", 0)),
        lon=float(data.get("lon", 0)),
        zip_code=data.get("zip", ""),
        timezone=data.get("timezone", ""),
        isp=data.get("isp", ""),
        org=data.get("org", ""),
        asn=data.get("as", ""),
        is_mobile=bool(data.get("mobile")),
        is_proxy=bool(data.get("proxy")),
        is_hosting=bool(data.get("hosting")),
        confidence=85,
        provider="ip-api.com",
        raw=data,
    )


def _parse_ipwho(data: dict, ip: str) -> Optional[GeoResult]:
    if not data.get("success"):
        return None
    conn = data.get("connection", {})
    return GeoResult(
        ip=ip,
        country=data.get("country", ""),
        region=data.get("region", ""),
        city=data.get("city", ""),
        lat=float(data.get("latitude", 0)),
        lon=float(data.get("longitude", 0)),
        zip_code=data.get("postal", ""),
        timezone=data.get("timezone", {}).get("id", ""),
        isp=conn.get("isp", ""),
        org=conn.get("org", ""),
        asn=str(conn.get("asn", "")),
        confidence=80,
        provider="ipwho.is",
        raw=data,
    )


def _parse_ipapi_co(data: dict, ip: str) -> Optional[GeoResult]:
    if data.get("error"):
        return None
    return GeoResult(
        ip=ip,
        country=data.get("country_name", ""),
        region=data.get("region", ""),
        city=data.get("city", ""),
        lat=float(data.get("latitude", 0)),
        lon=float(data.get("longitude", 0)),
        zip_code=data.get("postal", ""),
        timezone=data.get("timezone", ""),
        isp=data.get("org", ""),
        org=data.get("org", ""),
        asn=data.get("asn", ""),
        confidence=75,
        provider="ipapi.co",
        raw=data,
    )


def _parse_freeipapi(data: dict, ip: str) -> Optional[GeoResult]:
    if not data.get("countryName"):
        return None
    return GeoResult(
        ip=ip,
        country=data.get("countryName", ""),
        region=data.get("regionName", ""),
        city=data.get("cityName", ""),
        lat=float(data.get("latitude", 0)),
        lon=float(data.get("longitude", 0)),
        zip_code=data.get("zipCode", ""),
        timezone=data.get("timeZone", ""),
        confidence=70,
        provider="freeipapi.com",
        raw=data,
    )


PARSERS = {
    "ip-api.com": _parse_ip_api,
    "ipwho.is": _parse_ipwho,
    "ipapi.co": _parse_ipapi_co,
    "freeipapi.com": _parse_freeipapi,
}


def geolocate_ip(ip: str) -> GeoResult:
    """Query multiple free providers, return best-confidence result."""
    results: List[GeoResult] = []

    for prov in PROVIDERS:
        url = prov["url"].format(ip=ip)
        try:
            r = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                data = r.json()
                parser = PARSERS.get(prov["name"])
                if parser:
                    geo = parser(data, ip)
                    if geo and (geo.lat != 0 or geo.lon != 0):
                        results.append(geo)
        except Exception:
            continue

    if not results:
        return GeoResult(ip=ip, confidence=0, provider="none")

    # Cross-validate: boost confidence if multiple providers agree on city
    if len(results) >= 2:
        cities = [r.city.lower() for r in results if r.city]
        for r in results:
            matching = sum(1 for c in cities if c == r.city.lower())
            if matching >= 2:
                r.confidence = min(r.confidence + 10, 98)

    # Return highest confidence
    results.sort(key=lambda r: r.confidence, reverse=True)
    best = results[0]

    # Merge mobile/proxy flags from providers that detect them  
    for r in results:
        if r.is_mobile:
            best.is_mobile = True
        if r.is_proxy or r.is_vpn:
            best.is_proxy = True
        if r.is_hosting:
            best.is_hosting = True

    return best


def geolocate_ip_all(ip: str) -> List[GeoResult]:
    """Return results from ALL providers for comparison."""
    results = []
    for prov in PROVIDERS:
        url = prov["url"].format(ip=ip)
        try:
            r = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                parser = PARSERS.get(prov["name"])
                if parser:
                    geo = parser(r.json(), ip)
                    if geo:
                        results.append(geo)
        except Exception:
            continue
    return results


# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ip_geolocator.py <ip_address>")
        sys.exit(1)

    ip = sys.argv[1].strip()
    print(f"\n[*] Geolocating {ip} via 4 providers...\n")

    all_results = geolocate_ip_all(ip)
    for r in all_results:
        print(f"  [{r.provider}] {r.summary()}")

    print()
    best = geolocate_ip(ip)
    print(f"[+] BEST RESULT: {best.summary()}")
    print(f"    Coords : {best.lat}, {best.lon}")
    print(f"    ISP    : {best.isp}")
    print(f"    Mobile : {best.is_mobile}")
    print(f"    Proxy  : {best.is_proxy}")
    print()
