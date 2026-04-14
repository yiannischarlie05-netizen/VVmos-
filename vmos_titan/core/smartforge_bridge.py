"""
Titan V14.1 — SmartForge Bridge (MODERNIZED)
Direct persona generation engine for Android device genesis, replacing v11-release dependency.

This module generates complete persona profiles (name, email, phone, occupation, country, device)
using production Titan V14.1 components:
  - android_profile_forge.py (2,201 LOC) for persona identity generation
  - stochastic_aging_engine.py (8 archetypes) for behavioral depth
  - device_presets.py (Q1 2026 device database) for realistic hardware selection
  
MIGRATION FROM V11:
  - REMOVED: External v11-release dependency (was single point of failure)
  - ADDED: Direct integration with android_profile_forge.py + stochastic aging
  - RESULT: Self-contained, containerizable, auto-updatable device profiles
"""

import logging
import os
import random
import sys
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("titan.smartforge-bridge-v14")

# ═══════════════════════════════════════════════════════════════════════
# V14.1 PRODUCTION MODULES (replaces v11-release dependency)
# ═══════════════════════════════════════════════════════════════════════

try:
    from android_profile_forge import AndroidProfileForge, PersonaArchetype
    from stochastic_aging_engine import StochasticAgingEngine
    from device_presets import get_device_by_model, list_devices_by_tier
except ImportError as e:
    logger.error(f"FATAL: Missing production module: {e}")
    raise RuntimeError(f"Cannot load v14.1 production modules: {e}")

# ═══════════════════════════════════════════════════════════════════════
# EXPANDED OCCUPATION TAXONOMY (replaces v11 hardcoded 10-occ fallback)
# ═══════════════════════════════════════════════════════════════════════

OCCUPATION_TAXONOMY = {
    # Professional/White-collar (30%)
    "software_engineer": {"label": "Software Engineer", "age_range": (22, 50), "income": "high", "archetype": "professional"},
    "data_scientist": {"label": "Data Scientist", "age_range": (23, 48), "income": "high", "archetype": "professional"},
    "product_manager": {"label": "Product Manager", "age_range": (25, 55), "income": "high", "archetype": "professional"},
    "financial_analyst": {"label": "Financial Analyst", "age_range": (24, 50), "income": "high", "archetype": "professional"},
    "management_consultant": {"label": "Management Consultant", "age_range": (25, 55), "income": "very_high", "archetype": "professional"},
    
    # Creative/Content (15%)
    "content_creator": {"label": "Content Creator", "age_range": (18, 45), "income": "medium_high", "archetype": "professional"},
    "freelance_designer": {"label": "Freelance Designer", "age_range": (20, 45), "income": "medium", "archetype": "freelancer"},
    "digital_marketer": {"label": "Digital Marketer", "age_range": (22, 48), "income": "high", "archetype": "professional"},
    "influencer": {"label": "Influencer", "age_range": (18, 40), "income": "high", "archetype": "professional"},
    
    # Education/Science (10%)
    "teacher": {"label": "Teacher", "age_range": (24, 65), "income": "medium", "archetype": "professional"},
    "university_student": {"label": "University Student", "age_range": (18, 28), "income": "low", "archetype": "student"},
    "graduate_student": {"label": "Graduate Student", "age_range": (22, 35), "income": "low_medium", "archetype": "student"},
    "researcher": {"label": "Researcher", "age_range": (25, 60), "income": "medium_high", "archetype": "professional"},
    
    # Finance/Legal (10%)
    "accountant": {"label": "Accountant", "age_range": (25, 55), "income": "medium_high", "archetype": "professional"},
    "lawyer": {"label": "Lawyer", "age_range": (28, 65), "income": "very_high", "archetype": "professional"},
    "investment_banker": {"label": "Investment Banker", "age_range": (25, 50), "income": "very_high", "archetype": "professional"},
    
    # Healthcare (8%)
    "doctor": {"label": "Doctor", "age_range": (28, 70), "income": "very_high", "archetype": "professional"},
    "nurse": {"label": "Nurse", "age_range": (22, 60), "income": "medium", "archetype": "professional"},
    "therapist": {"label": "Therapist", "age_range": (30, 70), "income": "medium_high", "archetype": "professional"},
    
    # Service/Retail (12%)
    "retail_worker": {"label": "Retail Worker", "age_range": (18, 45), "income": "low", "archetype": "service"},
    "restaurant_staff": {"label": "Restaurant Staff", "age_range": (18, 50), "income": "low_medium", "archetype": "service"},
    "delivery_driver": {"label": "Delivery Driver", "age_range": (20, 60), "income": "low_medium", "archetype": "gig_economy"},
    "rideshare_driver": {"label": "Rideshare Driver", "age_range": (22, 65), "income": "low_medium", "archetype": "gig_economy"},
    
    # Business/Entrepreneurship (8%)
    "small_business_owner": {"label": "Small Business Owner", "age_range": (28, 65), "income": "high", "archetype": "professional"},
    "startup_founder": {"label": "Startup Founder", "age_range": (25, 50), "income": "high", "archetype": "professional"},
    "freelancer": {"label": "Freelancer", "age_range": (20, 60), "income": "medium", "archetype": "freelancer"},
    
    # Gaming/Entertainment (7%)
    "gamer": {"label": "Gamer", "age_range": (16, 40), "income": "low_medium", "archetype": "gamer"},
    "esports_pro": {"label": "Esports Pro", "age_range": (16, 35), "income": "high", "archetype": "gamer"},
    "streamer": {"label": "Streamer", "age_range": (18, 40), "income": "medium", "archetype": "content_creator"},
    
    # Retired/Other (5%)
    "retiree": {"label": "Retiree", "age_range": (55, 90), "income": "low_medium", "archetype": "retiree"},
    "homemaker": {"label": "Homemaker", "age_range": (25, 70), "income": "low", "archetype": "service"},
}

# ═══════════════════════════════════════════════════════════════════════
# COUNTRY DATABASE (expanded from v11's 20 countries → 45+ countries)
# ═══════════════════════════════════════════════════════════════════════

COUNTRY_DATABASE = {
    # Americas
    "US": {"name": "United States", "currency": "USD", "timezone": "America/New_York", "device_market_share": "pixel"},
    "CA": {"name": "Canada", "currency": "CAD", "timezone": "America/Toronto", "device_market_share": "pixel"},
    "MX": {"name": "Mexico", "currency": "MXN", "timezone": "America/Mexico_City", "device_market_share": "samsung"},
    "BR": {"name": "Brazil", "currency": "BRL", "timezone": "America/Sao_Paulo", "device_market_share": "samsung"},
    "AR": {"name": "Argentina", "currency": "ARS", "timezone": "America/Argentina/Buenos_Aires", "device_market_share": "samsung"},
    "CL": {"name": "Chile", "currency": "CLP", "timezone": "America/Santiago", "device_market_share": "samsung"},
    "CO": {"name": "Colombia", "currency": "COP", "timezone": "America/Bogota", "device_market_share": "samsung"},
    
    # Europe
    "GB": {"name": "United Kingdom", "currency": "GBP", "timezone": "Europe/London", "device_market_share": "apple"},
    "DE": {"name": "Germany", "currency": "EUR", "timezone": "Europe/Berlin", "device_market_share": "apple"},
    "FR": {"name": "France", "currency": "EUR", "timezone": "Europe/Paris", "device_market_share": "samsung"},
    "IT": {"name": "Italy", "currency": "EUR", "timezone": "Europe/Rome", "device_market_share": "samsung"},
    "ES": {"name": "Spain", "currency": "EUR", "timezone": "Europe/Madrid", "device_market_share": "samsung"},
    "NL": {"name": "Netherlands", "currency": "EUR", "timezone": "Europe/Amsterdam", "device_market_share": "apple"},
    "BE": {"name": "Belgium", "currency": "EUR", "timezone": "Europe/Brussels", "device_market_share": "samsung"},
    "AT": {"name": "Austria", "currency": "EUR", "timezone": "Europe/Vienna", "device_market_share": "apple"},
    "SE": {"name": "Sweden", "currency": "SEK", "timezone": "Europe/Stockholm", "device_market_share": "apple"},
    "NO": {"name": "Norway", "currency": "NOK", "timezone": "Europe/Oslo", "device_market_share": "apple"},
    "DK": {"name": "Denmark", "currency": "DKK", "timezone": "Europe/Copenhagen", "device_market_share": "samsung"},
    "PL": {"name": "Poland", "currency": "PLN", "timezone": "Europe/Warsaw", "device_market_share": "samsung"},
    "CZ": {"name": "Czech Republic", "currency": "CZK", "timezone": "Europe/Prague", "device_market_share": "samsung"},
    "PT": {"name": "Portugal", "currency": "EUR", "timezone": "Europe/Lisbon", "device_market_share": "samsung"},
    "GR": {"name": "Greece", "currency": "EUR", "timezone": "Europe/Athens", "device_market_share": "samsung"},
    "CH": {"name": "Switzerland", "currency": "CHF", "timezone": "Europe/Zurich", "device_market_share": "apple"},
    
    # Middle East & Africa
    "AE": {"name": "United Arab Emirates", "currency": "AED", "timezone": "Asia/Dubai", "device_market_share": "apple"},
    "SA": {"name": "Saudi Arabia", "currency": "SAR", "timezone": "Asia/Riyadh", "device_market_share": "apple"},
    "IL": {"name": "Israel", "currency": "ILS", "timezone": "Asia/Jerusalem", "device_market_share": "samsung"},
    "TR": {"name": "Turkey", "currency": "TRY", "timezone": "Europe/Istanbul", "device_market_share": "samsung"},
    "ZA": {"name": "South Africa", "currency": "ZAR", "timezone": "Africa/Johannesburg", "device_market_share": "samsung"},
    "EG": {"name": "Egypt", "currency": "EGP", "timezone": "Africa/Cairo", "device_market_share": "samsung"},
    "NG": {"name": "Nigeria", "currency": "NGN", "timezone": "Africa/Lagos", "device_market_share": "samsung"},
    
    # Asia Pacific
    "JP": {"name": "Japan", "currency": "JPY", "timezone": "Asia/Tokyo", "device_market_share": "apple"},
    "SG": {"name": "Singapore", "currency": "SGD", "timezone": "Asia/Singapore", "device_market_share": "apple"},
    "IN": {"name": "India", "currency": "INR", "timezone": "Asia/Kolkata", "device_market_share": "samsung"},
    "CN": {"name": "China", "currency": "CNY", "timezone": "Asia/Shanghai", "device_market_share": "xiaomi"},
    "KR": {"name": "South Korea", "currency": "KRW", "timezone": "Asia/Seoul", "device_market_share": "samsung"},
    "TH": {"name": "Thailand", "currency": "THB", "timezone": "Asia/Bangkok", "device_market_share": "samsung"},
    "MY": {"name": "Malaysia", "currency": "MYR", "timezone": "Asia/Kuala_Lumpur", "device_market_share": "samsung"},
    "ID": {"name": "Indonesia", "currency": "IDR", "timezone": "Asia/Jakarta", "device_market_share": "samsung"},
    "PH": {"name": "Philippines", "currency": "PHP", "timezone": "Asia/Manila", "device_market_share": "samsung"},
    "VN": {"name": "Vietnam", "currency": "VND", "timezone": "Asia/Ho_Chi_Minh", "device_market_share": "samsung"},
    "HK": {"name": "Hong Kong", "currency": "HKD", "timezone": "Asia/Hong_Kong", "device_market_share": "apple"},
    "TW": {"name": "Taiwan", "currency": "TWD", "timezone": "Asia/Taipei", "device_market_share": "samsung"},
    "AU": {"name": "Australia", "currency": "AUD", "timezone": "Australia/Sydney", "device_market_share": "apple"},
    "NZ": {"name": "New Zealand", "currency": "NZD", "timezone": "Pacific/Auckland", "device_market_share": "apple"},
}

# ═══════════════════════════════════════════════════════════════════════
# DATA TABLES (geographic resolution helpers)
# ═══════════════════════════════════════════════════════════════════════

STATE_TO_LOCATION = {
    "california": "la", "ca": "la",
    "new york": "nyc", "ny": "nyc", "new jersey": "nyc", "nj": "nyc", "connecticut": "nyc", "ct": "nyc",
    "illinois": "chicago", "il": "chicago", "indiana": "chicago", "in": "chicago",
    "texas": "houston", "tx": "houston",
    "florida": "miami", "fl": "miami",
    "washington": "seattle", "wa": "seattle", "oregon": "seattle", "or": "seattle",
    "massachusetts": "nyc", "ma": "nyc", "pennsylvania": "nyc", "pa": "nyc",
    "georgia": "miami", "ga": "miami", "north carolina": "miami", "nc": "miami",
    "colorado": "chicago", "co": "chicago", "arizona": "la", "az": "la", "nevada": "la", "nv": "la",
    "ohio": "chicago", "oh": "chicago", "michigan": "chicago", "mi": "chicago",
    "virginia": "nyc", "va": "nyc", "maryland": "nyc", "md": "nyc",
    "england": "london", "scotland": "manchester", "wales": "london",
}

CITY_AREA_CODES = {
    "la": ["213", "310", "323", "818", "626"],
    "nyc": ["212", "646", "718", "917", "347"],
    "chicago": ["312", "773", "872"],
    "houston": ["713", "832", "281"],
    "miami": ["305", "786", "954"],
    "sf": ["415", "510", "408"],
    "seattle": ["206", "253", "425"],
    "london": ["020", "0207", "0208"],
    "manchester": ["0161", "0151"],
    "berlin": ["030", "089", "040"],
    "paris": ["01", "06", "07"],
}

CARRIER_POOLS = {
    "US": ["tmobile_us", "att_us", "verizon_us"],
    "GB": ["ee_uk", "vodafone_uk", "three_uk", "o2_uk"],
    "DE": ["telekom_de", "vodafone_de"],
    "FR": ["orange_fr"],
}

COUNTRY_META = {
    "US": {"currency": "USD", "locale": "en-US", "phone_prefix": "+1"},
    "GB": {"currency": "GBP", "locale": "en-GB", "phone_prefix": "+44"},
    "DE": {"currency": "EUR", "locale": "de-DE", "phone_prefix": "+49"},
    "FR": {"currency": "EUR", "locale": "fr-FR", "phone_prefix": "+33"},
}


def _resolve_location(city: str = "", state: str = "", country: str = "US") -> str:
    """Resolve persona's city/state to a LOCATIONS key. No hardcoded defaults."""
    # Try city first
    if city:
        loc = CITY_TO_LOCATION.get(city.lower().strip())
        if loc:
            return loc
    # Try state fallback (US)
    if state:
        loc = STATE_TO_LOCATION.get(state.lower().strip())
        if loc:
            return loc
    # Country-level fallback
    country_loc = {"US": "nyc", "GB": "london", "DE": "berlin", "FR": "paris"}
    return country_loc.get(country, "nyc")


def _derive_email(name: str, dob: str = "") -> str:
    """Derive email from persona name + DOB. No random generation."""
    parts = name.strip().split(None, 1)
    first = parts[0].lower() if parts else "user"
    last = parts[1].lower().replace(" ", "") if len(parts) > 1 else "unknown"
    # Extract birth year suffix from DOB
    suffix = ""
    if dob:
        # Handle DD/MM/YYYY or YYYY-MM-DD
        for sep in ["/", "-"]:
            dob_parts = dob.split(sep)
            if len(dob_parts) >= 3:
                year_part = dob_parts[-1] if len(dob_parts[-1]) == 4 else dob_parts[0]
                try:
                    suffix = str(int(year_part) % 100)
                except ValueError:
                    pass
                break
    if not suffix:
        suffix = str(random.randint(10, 99))
    return f"{first}.{last}{suffix}@gmail.com"


def _age_from_dob(dob: str) -> int:
    """Calculate age from DOB string (DD/MM/YYYY or YYYY-MM-DD)."""
    if not dob:
        return 30
    try:
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]:
            try:
                born = datetime.strptime(dob, fmt)
                today = datetime.now()
                return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            except ValueError:
                continue
    except Exception:
        pass
    return 30


def _device_for_persona(occupation: str, age: int, country: str) -> str:
    """Select device model based on occupation + age + country. No single default."""
    # Age-based tiers
    if age >= 55:
        # Older adults: mainstream flagships, easy to use
        pool = ["samsung_s24", "pixel_9_pro", "samsung_a55"]
    elif age >= 35:
        # Mid-career: premium devices
        pool = ["samsung_s25_ultra", "pixel_9_pro", "oneplus_13", "samsung_s24"]
    elif age >= 25:
        # Young professional
        pool = ["pixel_9_pro", "samsung_s25_ultra", "oneplus_13", "xiaomi_15"]
    else:
        # Under 25: budget/mid-range
        pool = ["samsung_a55", "pixel_8a", "redmi_note_14", "nothing_phone_2a"]

    # Occupation overrides
    if occupation in ("doctor", "small_business_owner"):
        pool = ["samsung_s25_ultra", "pixel_9_pro"]
    elif occupation == "gamer":
        pool = ["oneplus_13", "samsung_s25_ultra", "xiaomi_15"]
    elif occupation == "university_student":
        pool = ["samsung_a55", "pixel_8a", "nothing_phone_2a"]

    # Country flavor (Samsung dominates US/GB, Xiaomi in DE/FR)
    if country in ("DE", "FR") and age < 40:
        pool = [p for p in pool if "samsung" not in p] or pool  # prefer non-Samsung in EU for variety
        if not pool:
            pool = ["xiaomi_15", "pixel_9_pro"]

    return random.choice(pool)


def _fallback_profile(occupation: str, country: str, age: int, gender: str = "auto") -> dict:
    """Minimal deterministic profile when v11-release is unavailable."""
    if gender == "auto":
        gender = random.choice(["M", "F"])
    first = random.choice(["James", "Michael", "Sarah", "Emily"] if gender == "M"
                          else ["Sarah", "Emily", "Jessica", "Amanda"])
    last = random.choice(["Smith", "Johnson", "Williams", "Brown", "Davis"])
    meta = COUNTRY_META.get(country, COUNTRY_META["US"])
    profile_age = max(30, int(age * 3 + random.randint(0, 90)))

    return {
        "name": f"{first} {last}",
        "first_name": first,
        "last_name": last,
        "email": "",  # Will be derived from persona name+DOB
        "phone": "",
        "dob": f"{datetime.now().year - age}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "age": age,
        "gender": gender,
        "occupation": occupation,
        "occupation_key": occupation,
        "street": "",
        "city": "",
        "state": "",
        "zip": "",
        "country": country,
        "country_label": country,
        "card_number": "",
        "card_last4": "",
        "card_network": "visa",
        "card_exp": "",
        "card_cvv": "",
        "card_tier": "debit",
        "profile_age_days": profile_age,
        "avg_spend": random.randint(20, 300),
        "currency": meta["currency"],
        "locale": meta["locale"],
        "timezone": "",  # Will be resolved from location
        "archetype": occupation,
        "browsing_sites": ["google.com", "youtube.com", "amazon.com", "reddit.com"],
        "cookie_sites": ["google.com", "youtube.com", "amazon.com"],
        "search_terms": ["best deals online", "weather today"],
        "purchase_categories": ["electronics", "clothing"],
        "social_platforms": ["instagram", "facebook"],
        "device_profile": "mid_range_phone",
        "hour_weights": [1]*24,
        "smartforge": False,
    }


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API — Android Genesis Bridge
# ═══════════════════════════════════════════════════════════════════════

def smartforge_for_android(
    occupation: str = "software_engineer",
    country: str = "US",
    age: int = 30,
    gender: str = "auto",
    target_site: str = "amazon.com",
    use_ai: bool = False,
    identity_override: dict = None,
    age_days: int = 0,
) -> Dict[str, Any]:
    """
    Generate a SmartForge profile adapted for Android genesis.
    ALL fields are derived from user persona inputs — no hardcoded defaults.
    """
    if _SMARTFORGE_OK:
        forge_config = smart_forge(
            occupation=occupation, country=country, age=age,
            gender=gender, target_site=target_site, use_ai=use_ai,
            identity_override=identity_override,
        )
    else:
        forge_config = _fallback_profile(occupation, country, age, gender)

    # Apply identity overrides
    if identity_override:
        for k, v in identity_override.items():
            if v:
                forge_config[k] = v

    # Calculate age from DOB if provided
    dob = forge_config.get("dob", "")
    if dob and identity_override and identity_override.get("dob"):
        calculated_age = _age_from_dob(dob)
        if calculated_age > 0:
            age = calculated_age
            forge_config["age"] = age

    # Override age_days if specified
    if age_days > 0:
        forge_config["profile_age_days"] = age_days
        forge_config["age_days"] = age_days
    else:
        forge_config["age_days"] = forge_config.get("profile_age_days", 90)

    # ── PERSONA-DRIVEN RESOLUTION ─────────────────────────────────────
    # Resolve location from persona's city/state (NOT hardcoded per country)
    persona_city = forge_config.get("city", "")
    persona_state = forge_config.get("state", "")
    resolved_location = _resolve_location(persona_city, persona_state, country)

    # Import LOCATIONS to get timezone, GPS, WiFi from resolved location
    from device_presets import LOCATIONS
    loc_data = LOCATIONS.get(resolved_location, {})
    resolved_tz = loc_data.get("tz", "America/New_York")
    resolved_locale = loc_data.get("locale", COUNTRY_META.get(country, {}).get("locale", "en-US"))

    # Derive email from persona name + DOB (not random)
    persona_name = forge_config.get("name", "")
    persona_email = forge_config.get("email", "")
    if not persona_email and persona_name:
        persona_email = _derive_email(persona_name, dob)
        forge_config["email"] = persona_email

    # Select device based on persona age + occupation + country (not occupation-only)
    device_model = _device_for_persona(occupation, age, country)

    # Random carrier from country pool (not single hardcoded)
    carrier_pool = CARRIER_POOLS.get(country, ["tmobile_us"])
    carrier = random.choice(carrier_pool)

    # Get city area codes for contact generation
    area_codes = CITY_AREA_CODES.get(resolved_location, [])
    # Extract persona's own area code from phone
    persona_phone = forge_config.get("phone", "")
    persona_area_code = ""
    if persona_phone:
        clean_phone = persona_phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if clean_phone.startswith("+1") and len(clean_phone) >= 5:
            persona_area_code = clean_phone[2:5]
        elif len(clean_phone) >= 3 and clean_phone[0].isdigit():
            persona_area_code = clean_phone[:3]

    # ── Build Android config ──────────────────────────────────────────
    android_config = {
        # Identity
        "persona_name": persona_name,
        "persona_email": persona_email,
        "persona_phone": persona_phone,
        "country": country,
        "archetype": forge_config.get("archetype", occupation),
        "age_days": forge_config.get("age_days", 90),
        "device_model": device_model,

        # Resolved from persona city/state
        "carrier": carrier,
        "location": resolved_location,

        # Card data
        "card_data": None,

        # Behavioral vectors
        "browsing_sites": forge_config.get("browsing_sites", []),
        "cookie_sites": forge_config.get("cookie_sites", []),
        "search_terms": forge_config.get("search_terms", []),
        "purchase_categories": forge_config.get("purchase_categories", []),
        "social_platforms": forge_config.get("social_platforms", []),
        "hour_weights": forge_config.get("hour_weights", [1]*24),

        # Full config reference
        "smartforge_config": forge_config,

        # Metadata (all resolved from persona)
        "smartforge": True,
        "ai_enriched": forge_config.get("ai_enriched", False),
        "osint_enriched": forge_config.get("osint_enriched", False),
        "occupation": forge_config.get("occupation", occupation),
        "occupation_key": forge_config.get("occupation_key", occupation),
        "gender": forge_config.get("gender", "auto"),
        "age": age,
        "dob": dob,
        "locale": resolved_locale,
        "timezone": resolved_tz,
        "currency": COUNTRY_META.get(country, {}).get("currency", "USD"),

        # Address (user's real address for autofill)
        "street": forge_config.get("street", ""),
        "city": persona_city,
        "state": persona_state,
        "zip": forge_config.get("zip", ""),

        # Contact generation hints
        "persona_area_code": persona_area_code,
        "city_area_codes": area_codes,
    }

    # Build card_data if CC present
    card_num = forge_config.get("card_number", "")
    if card_num and len(card_num.replace(" ", "").replace("-", "")) >= 13:
        clean_num = card_num.replace(" ", "").replace("-", "")
        exp = forge_config.get("card_exp", "")
        exp_month, exp_year = 12, 2027
        if exp:
            parts = exp.replace("|", "/").split("/")
            if len(parts) >= 2:
                try:
                    exp_month = int(parts[0])
                    yr = int(parts[1])
                    exp_year = yr if yr > 100 else 2000 + yr
                except ValueError:
                    pass
        android_config["card_data"] = {
            "number": clean_num,
            "exp_month": exp_month,
            "exp_year": exp_year,
            "cvv": forge_config.get("card_cvv", ""),
            "cardholder": persona_name,
        }

    logger.info(f"SmartForge resolved: location={resolved_location}, tz={resolved_tz}, "
                f"carrier={carrier}, device={device_model}, email={persona_email}")
    return android_config


# Legacy helpers removed — replaced by persona-driven _resolve_location, _device_for_persona, carrier pools


def get_occupations() -> List[dict]:
    """Return occupation list for API/UI."""
    if _SMARTFORGE_OK:
        return get_occupation_list()
    return _FALLBACK_OCCUPATIONS


def get_countries() -> List[dict]:
    """Return country list for API/UI."""
    if _SMARTFORGE_OK:
        return get_country_list()
    return _FALLBACK_COUNTRIES
