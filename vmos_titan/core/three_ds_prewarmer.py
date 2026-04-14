"""
ThreeDSPrewarmer — 3DS Frictionless Flow Pre-Warming Engine
============================================================
Coordinates purchase_history_bridge.py and three_ds_strategy.py to
pre-seed Chrome cookies, browsing history, and transaction patterns
that lower 3DS challenge rates for target merchants.

Gap #4 from research report cross-reference:
- three_ds_strategy.py predicts challenge rates but doesn't ACT
- purchase_history_bridge.py generates purchase artifacts but isn't
  targeted toward 3DS frictionless flow optimization
- Missing: coordination layer that takes a target merchant + card BIN
  and pre-seeds the exact artifacts needed to achieve frictionless auth

3DS Frictionless Flow Conditions (from reports):
    1. TRA exemption: transaction < €500 AND issuer fraud rate < 0.13%
    2. Low Value Exemption: < €30 EU / < $30 US
    3. Trusted beneficiary: merchant whitelisted by cardholder
    4. Recurring MIT: merchant-initiated transaction pattern
    5. Delegated auth: wallet biometric verified (COIN.xml)
    6. RBA score < 30: coherent identity + purchase history

This module targets conditions 3, 4, and 6 by:
    - Pre-seeding Chrome cookies from target merchant domain
    - Injecting 3-5 smaller "warm-up" transactions at the same merchant
    - Building browsing history showing repeated visits over weeks
    - Creating "returning customer" signal via cookie age + visit count
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PrewarmPlan:
    """Plan for pre-warming a specific merchant for frictionless 3DS."""
    merchant_domain: str
    merchant_name: str
    bin_prefix: str
    target_amount: float
    warmup_transactions: List[Dict[str, Any]]
    browsing_sessions: List[Dict[str, Any]]
    cookies_to_inject: List[Dict[str, Any]]
    expected_challenge_rate_before: float
    expected_challenge_rate_after: float
    risk_reduction: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "merchant_domain": self.merchant_domain,
            "merchant_name": self.merchant_name,
            "bin_prefix": self.bin_prefix,
            "target_amount": self.target_amount,
            "warmup_tx_count": len(self.warmup_transactions),
            "browsing_sessions": len(self.browsing_sessions),
            "cookies_count": len(self.cookies_to_inject),
            "challenge_rate_before": round(self.expected_challenge_rate_before, 3),
            "challenge_rate_after": round(self.expected_challenge_rate_after, 3),
            "risk_reduction_pct": round(self.risk_reduction * 100, 1),
        }


@dataclass
class PrewarmResult:
    """Result of executing a pre-warm plan."""
    merchant_domain: str
    success: bool
    cookies_injected: int
    history_entries_added: int
    warmup_txs_added: int
    chrome_updated: bool
    duration_s: float
    errors: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
# Merchant intelligence for 3DS pre-warming
# ═══════════════════════════════════════════════════════════════════════

MERCHANT_PREWARM_PROFILES = {
    "amazon.com": {
        "name": "Amazon.com",
        "mcc": "5942",
        "low_value_items": [
            ("AmazonBasics USB Cable", 7.99),
            ("AmazonBasics Lightning Cable", 8.99),
            ("Kindle eBook", 4.99),
            ("AmazonBasics AAA Batteries (8pk)", 6.49),
        ],
        "pages": [
            "/", "/gp/yourstore", "/gp/css/homepage.html",
            "/dp/B0XXXXXXXXXX", "/gp/cart/view.html",
            "/gp/buy/spc/handlers/display.html",
        ],
        "cookies": ["session-id", "ubid-main", "session-token", "csm-hit", "x-main"],
        "3ds_exempt_below": 30.0,
    },
    "walmart.com": {
        "name": "Walmart",
        "mcc": "5411",
        "low_value_items": [
            ("Great Value Water (24pk)", 3.48),
            ("Equate Hand Soap", 2.97),
            ("Mainstays Dish Cloths", 4.97),
        ],
        "pages": [
            "/", "/account", "/cart",
            "/ip/XXXXXXXXX", "/checkout",
        ],
        "cookies": ["auth", "cart-item-count", "CRT", "customer"],
        "3ds_exempt_below": 30.0,
    },
    "bestbuy.com": {
        "name": "Best Buy",
        "mcc": "5732",
        "low_value_items": [
            ("Insignia USB-C Cable", 9.99),
            ("Rocketfish HDMI Cable", 12.99),
            ("Screen Cleaning Kit", 7.99),
        ],
        "pages": [
            "/", "/site/electronics/pcmcat702200702102.c",
            "/cart", "/checkout/r/fulfillment",
        ],
        "cookies": ["UID", "SID", "CTX", "ltc"],
        "3ds_exempt_below": 25.0,
    },
    "target.com": {
        "name": "Target",
        "mcc": "5331",
        "low_value_items": [
            ("Up&Up Cotton Balls", 2.49),
            ("Threshold Candle", 5.00),
            ("Market Pantry Snack Bars", 3.99),
        ],
        "pages": [
            "/", "/account", "/cart",
            "/p/XXXXXXX", "/co-review",
        ],
        "cookies": ["visitorId", "TealeafAkaSid", "sapphire", "GuestLocation"],
        "3ds_exempt_below": 25.0,
    },
    "ebay.com": {
        "name": "eBay",
        "mcc": "5999",
        "low_value_items": [
            ("USB Type-C Adapter", 5.99),
            ("Phone Case (generic)", 4.99),
            ("LED Flashlight", 7.49),
        ],
        "pages": [
            "/", "/myebay/summary", "/itm/XXXXXXXXX",
            "/cart", "/pay/checkout",
        ],
        "cookies": ["ebay", "dp1", "nonsession", "ds2", "s"],
        "3ds_exempt_below": 30.0,
    },
    "paypal.com": {
        "name": "PayPal",
        "mcc": "6012",
        "low_value_items": [],
        "pages": [
            "/", "/myaccount/summary", "/myaccount/transactions",
            "/webapps/mpp/send-money-online",
        ],
        "cookies": ["cookie_check", "ts", "X-PP-SILOVER", "LANG"],
        "3ds_exempt_below": 0,  # PayPal handles auth internally
    },
    "shopify.com": {
        "name": "Shopify Store",
        "mcc": "5999",
        "low_value_items": [
            ("Sticker Pack", 4.99),
            ("Phone Grip", 8.99),
        ],
        "pages": [
            "/", "/collections/all", "/products/XXXXXXXXX",
            "/cart", "/checkouts/XXXXXXXXX",
        ],
        "cookies": ["_shopify_y", "_shopify_s", "cart", "_orig_referrer"],
        "3ds_exempt_below": 25.0,
    },
    # ── Expanded merchant profiles (Phase 5 production hardening) ──
    "apple.com": {
        "name": "Apple",
        "mcc": "5732",
        "low_value_items": [
            ("Apple Polishing Cloth", 19.00),
            ("Lightning to USB Cable", 19.00),
            ("AirTag", 29.00),
        ],
        "pages": [
            "/", "/shop", "/shop/buy-iphone",
            "/shop/bag", "/shop/checkout",
        ],
        "cookies": ["as_dc", "dssid2", "s_vi", "pxro"],
        "3ds_exempt_below": 25.0,
    },
    "nike.com": {
        "name": "Nike",
        "mcc": "5699",
        "low_value_items": [
            ("Nike Everyday Socks (3pk)", 16.00),
            ("Nike Dry-FIT Headband", 12.00),
            ("Nike Essential Water Bottle", 15.00),
        ],
        "pages": [
            "/", "/w/mens-shoes", "/t/XXXXXXXXX",
            "/cart", "/checkout",
        ],
        "cookies": ["NIKE_COMMERCE_GUID", "anonymousId", "AnalysisUserId"],
        "3ds_exempt_below": 30.0,
    },
    "homedepot.com": {
        "name": "The Home Depot",
        "mcc": "5200",
        "low_value_items": [
            ("3M Electrical Tape", 2.98),
            ("HDX Work Gloves", 5.97),
            ("GE LED Bulb 4-Pack", 8.97),
        ],
        "pages": [
            "/", "/c/tools", "/p/XXXXXXXXX",
            "/mycart/home", "/mycheckout",
        ],
        "cookies": ["THD_PERSIST", "THD_SESSION", "akacd_thd_cart"],
        "3ds_exempt_below": 30.0,
    },
    "costco.com": {
        "name": "Costco",
        "mcc": "5300",
        "low_value_items": [
            ("Kirkland Water (40pk)", 4.49),
            ("Kirkland Batteries AA (48pk)", 15.99),
            ("Kirkland Paper Towels (12pk)", 18.99),
        ],
        "pages": [
            "/", "/CatalogSearch", "/product.XXXXXXXXX.html",
            "/CartHandler", "/CheckoutCartHandler",
        ],
        "cookies": ["C_LOC", "COSTCO_CSRF_TOKEN", "cos_cart"],
        "3ds_exempt_below": 30.0,
    },
    "sephora.com": {
        "name": "Sephora",
        "mcc": "5977",
        "low_value_items": [
            ("Sephora Collection Blotting Papers", 8.00),
            ("Sephora Collection Mini Lip Stain", 7.00),
            ("Clean Skin Gel Cleanser", 10.00),
        ],
        "pages": [
            "/", "/shop/skincare", "/product/XXXXXXXXX",
            "/basket", "/checkout",
        ],
        "cookies": ["SEPH_UID", "AKA_A2", "DYN_USER_ID"],
        "3ds_exempt_below": 25.0,
    },
    "starbucks.com": {
        "name": "Starbucks",
        "mcc": "5812",
        "low_value_items": [
            ("Pike Place Roast K-Cups (10ct)", 8.99),
            ("Starbucks Reusable Cup", 3.00),
            ("Starbucks Via Instant (8ct)", 7.95),
        ],
        "pages": [
            "/", "/menu", "/store-locator",
            "/account/card", "/account/rewards",
        ],
        "cookies": ["AWSALB", "x-]]csrf-token", "starbucks_session"],
        "3ds_exempt_below": 25.0,
    },
    "uber.com": {
        "name": "Uber / Uber Eats",
        "mcc": "4121",
        "low_value_items": [],
        "pages": [
            "/", "/ride", "/orders",
            "/payment", "/checkout",
        ],
        "cookies": ["jwt-session", "marketing_vistor_id", "uber_sites_optout"],
        "3ds_exempt_below": 0,  # Uber handles auth via in-app flow
    },
    "doordash.com": {
        "name": "DoorDash",
        "mcc": "5812",
        "low_value_items": [],
        "pages": [
            "/", "/orders", "/store/XXXXXXXXX",
            "/cart", "/checkout",
        ],
        "cookies": ["dd_device_id", "_dd_l", "dd_session"],
        "3ds_exempt_below": 0,  # DoorDash handles auth via in-app
    },
}


class ThreeDSPrewarmer:
    """
    Coordinate purchase artifacts to reduce 3DS challenge rates.

    Analyzes the target merchant + card BIN combination, then generates
    and injects the exact browsing/transaction artifacts needed to
    push the issuer's RBA (Risk-Based Authentication) score below
    the challenge threshold.

    Usage:
        prewarmer = ThreeDSPrewarmer()
        plan = prewarmer.create_plan(
            merchant_domain="amazon.com",
            bin_prefix="4024",
            target_amount=149.99,
            profile_age_days=90,
        )
        print(f"Challenge rate reduction: {plan.risk_reduction:.0%}")

        # Execute plan (requires device access)
        result = prewarmer.execute_plan(
            plan, adb_target="127.0.0.1:6520",
        )
    """

    def __init__(self):
        self._strategy = None
        self._bridge = None

    def _get_strategy(self):
        """Lazy-load ThreeDSStrategy."""
        if self._strategy is None:
            try:
                from three_ds_strategy import ThreeDSStrategy
                self._strategy = ThreeDSStrategy()
            except ImportError:
                logger.warning("three_ds_strategy not available")
        return self._strategy

    def _get_bridge(self):
        """Lazy-load PurchaseHistoryBridge."""
        if self._bridge is None:
            try:
                from purchase_history_bridge import PurchaseHistoryBridge
                self._bridge = PurchaseHistoryBridge()
            except ImportError:
                logger.warning("purchase_history_bridge not available")
        return self._bridge

    # ──────────────────────────────────────────────────────────────
    # Plan generation
    # ──────────────────────────────────────────────────────────────

    def create_plan(self, merchant_domain: str, bin_prefix: str,
                    target_amount: float,
                    profile_age_days: int = 90) -> PrewarmPlan:
        """
        Create a pre-warming plan for frictionless 3DS.

        Args:
            merchant_domain: Target merchant domain (e.g., "amazon.com").
            bin_prefix: Card BIN (first 4-6 digits).
            target_amount: Transaction amount to optimize for.
            profile_age_days: Age of the device profile in days.

        Returns:
            PrewarmPlan with all artifacts to inject.
        """
        profile = MERCHANT_PREWARM_PROFILES.get(merchant_domain)
        if not profile:
            # Generate generic profile
            profile = self._generate_generic_profile(merchant_domain)

        # Get challenge rate prediction from 3DS strategy engine
        strategy = self._get_strategy()
        challenge_rate_before = 0.5  # default
        if strategy:
            try:
                rec = strategy.get_recommendations(
                    bin_prefix=bin_prefix,
                    merchant=merchant_domain,
                    amount=target_amount,
                )
                if rec and hasattr(rec, "risk_score"):
                    challenge_rate_before = rec.risk_score / 100.0
            except Exception:
                pass

        # Generate warm-up transactions (smaller amounts at same merchant)
        warmup_txs = self._generate_warmup_transactions(
            profile, target_amount, profile_age_days,
        )

        # Generate browsing sessions showing repeated visits
        browsing = self._generate_browsing_sessions(
            merchant_domain, profile, profile_age_days,
        )

        # Generate aged cookies
        cookies = self._generate_aged_cookies(
            merchant_domain, profile, profile_age_days,
        )

        # Estimate challenge rate reduction
        # Factors: warm-up tx count, cookie age, visit frequency
        reduction = self._estimate_challenge_reduction(
            warmup_tx_count=len(warmup_txs),
            cookie_age_days=profile_age_days,
            visit_count=len(browsing),
            target_amount=target_amount,
            exempt_below=profile.get("3ds_exempt_below", 25.0),
        )

        challenge_rate_after = max(0.05, challenge_rate_before - reduction)

        return PrewarmPlan(
            merchant_domain=merchant_domain,
            merchant_name=profile["name"],
            bin_prefix=bin_prefix,
            target_amount=target_amount,
            warmup_transactions=warmup_txs,
            browsing_sessions=browsing,
            cookies_to_inject=cookies,
            expected_challenge_rate_before=challenge_rate_before,
            expected_challenge_rate_after=challenge_rate_after,
            risk_reduction=challenge_rate_before - challenge_rate_after,
        )

    def _generate_warmup_transactions(self, profile: dict,
                                       target_amount: float,
                                       age_days: int) -> List[Dict[str, Any]]:
        """
        Generate 3-5 smaller transactions at the same merchant,
        backdated across the profile age.

        Smaller prior transactions build "trusted beneficiary" signal:
        the issuer sees the cardholder has used this merchant before
        without chargebacks.
        """
        low_items = profile.get("low_value_items", [])
        if not low_items:
            # Generic low-value items
            low_items = [
                ("Shipping upgrade", 5.99),
                ("Gift card $10", 10.00),
                ("Accessories", 8.99),
            ]

        tx_count = random.randint(3, 5)
        txs = []
        now = datetime.now()

        for i in range(tx_count):
            item_name, item_price = random.choice(low_items)
            # Space transactions across profile age
            days_ago = random.randint(
                max(7, age_days // (tx_count + 1) * i),
                max(14, age_days // (tx_count + 1) * (i + 1)),
            )
            tx_time = now - timedelta(days=days_ago)
            # Add realistic hour variance (10am-9pm)
            tx_time = tx_time.replace(
                hour=random.randint(10, 21),
                minute=random.randint(0, 59),
            )

            txs.append({
                "merchant": profile["name"],
                "merchant_domain": profile.get("domain", ""),
                "mcc": profile.get("mcc", "5999"),
                "item": item_name,
                "amount": item_price,
                "timestamp": int(tx_time.timestamp()),
                "timestamp_iso": tx_time.isoformat(),
                "status": "completed",
                "order_id": self._generate_order_id(profile["name"]),
            })

        # Sort by timestamp (oldest first)
        txs.sort(key=lambda t: t["timestamp"])
        return txs

    def _generate_browsing_sessions(self, domain: str, profile: dict,
                                     age_days: int) -> List[Dict[str, Any]]:
        """
        Generate 8-15 browsing sessions at the merchant over time.

        Returning-customer cookies + browsing frequency = lower RBA score.
        """
        pages = profile.get("pages", ["/", "/cart", "/checkout"])
        session_count = random.randint(8, 15)
        sessions = []
        now = datetime.now()

        for i in range(session_count):
            days_ago = random.randint(1, age_days)
            session_start = now - timedelta(days=days_ago)
            session_start = session_start.replace(
                hour=random.randint(8, 22),
                minute=random.randint(0, 59),
            )

            # 2-6 page views per session
            page_count = random.randint(2, min(6, len(pages)))
            visited_pages = random.sample(pages, page_count)

            page_visits = []
            current_time = session_start
            for page in visited_pages:
                url = f"https://www.{domain}{page}"
                page_visits.append({
                    "url": url,
                    "title": f"{profile['name']} - {page.strip('/') or 'Home'}",
                    "timestamp": int(current_time.timestamp()),
                    "visit_duration_s": random.randint(15, 120),
                })
                current_time += timedelta(seconds=random.randint(20, 180))

            sessions.append({
                "session_start": int(session_start.timestamp()),
                "page_views": page_visits,
                "duration_s": int((current_time - session_start).total_seconds()),
            })

        sessions.sort(key=lambda s: s["session_start"])
        return sessions

    def _generate_aged_cookies(self, domain: str, profile: dict,
                                age_days: int) -> List[Dict[str, Any]]:
        """
        Generate merchant-specific cookies with realistic aging.

        Cookie ages must match browsing history timestamps for coherence.
        Chrome SQLite uses Windows FILETIME epoch: (unix * 1000000) + 11644473600000000.
        """
        cookie_names = profile.get("cookies", ["session", "user", "cart"])
        cookies = []
        now = datetime.now()

        for name in cookie_names:
            # Cookie created on first visit, updated on latest
            created_days_ago = random.randint(
                max(age_days // 2, 14), age_days,
            )
            last_accessed_days_ago = random.randint(1, 7)

            created_epoch = int(
                (now - timedelta(days=created_days_ago)).timestamp()
            )
            last_accessed_epoch = int(
                (now - timedelta(days=last_accessed_days_ago)).timestamp()
            )

            # Chrome FILETIME format
            chrome_created = (created_epoch * 1_000_000) + 11_644_473_600_000_000
            chrome_last = (last_accessed_epoch * 1_000_000) + 11_644_473_600_000_000

            # Generate realistic cookie value
            if "session" in name.lower():
                value = f"{random.randint(100, 999)}-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}"
            elif "id" in name.lower() or "uid" in name.lower():
                import secrets
                value = secrets.token_hex(16)
            else:
                import secrets
                value = secrets.token_urlsafe(24)

            cookies.append({
                "host": f".{domain}",
                "name": name,
                "value": value,
                "path": "/",
                "creation_utc": chrome_created,
                "last_access_utc": chrome_last,
                "expires_utc": chrome_last + (365 * 24 * 3600 * 1_000_000),
                "is_secure": 1,
                "is_httponly": 0 if "session" in name.lower() else 1,
                "samesite": 0,
                "priority": 1,
            })

        return cookies

    # ──────────────────────────────────────────────────────────────
    # Risk estimation
    # ──────────────────────────────────────────────────────────────

    def _estimate_challenge_reduction(self, warmup_tx_count: int,
                                       cookie_age_days: int,
                                       visit_count: int,
                                       target_amount: float,
                                       exempt_below: float) -> float:
        """
        Estimate how much pre-warming reduces 3DS challenge probability.

        Based on research data:
        - Prior merchant transactions: -8% per successful tx (max -30%)
        - Cookie age > 30 days: -10%
        - Visit count > 5: -8%
        - Amount below LVE threshold: -15%
        - Returning customer cookie: -12%
        """
        reduction = 0.0

        # Prior transactions at same merchant
        tx_reduction = min(0.30, warmup_tx_count * 0.08)
        reduction += tx_reduction

        # Cookie age signal
        if cookie_age_days > 90:
            reduction += 0.12
        elif cookie_age_days > 30:
            reduction += 0.10
        elif cookie_age_days > 7:
            reduction += 0.05

        # Visit frequency
        if visit_count > 10:
            reduction += 0.10
        elif visit_count > 5:
            reduction += 0.08
        elif visit_count > 2:
            reduction += 0.04

        # Low Value Exemption
        if target_amount < exempt_below:
            reduction += 0.15

        # Cap reduction at 55% (can't eliminate challenge entirely)
        return min(0.55, reduction)

    # ──────────────────────────────────────────────────────────────
    # Plan execution
    # ──────────────────────────────────────────────────────────────

    def execute_plan(self, plan: PrewarmPlan,
                     adb_target: str = "127.0.0.1:6520") -> PrewarmResult:
        """
        Execute a pre-warm plan by injecting artifacts into Chrome.

        Injects browsing history, cookies, and transaction references
        into Chrome's SQLite databases on the target device.

        Args:
            plan: PrewarmPlan from create_plan().
            adb_target: ADB target device.

        Returns:
            PrewarmResult with injection outcomes.
        """
        import subprocess
        start = time.time()
        errors = []
        cookies_ok = 0
        history_ok = 0
        warmup_ok = 0

        def sh(cmd: str) -> str:
            try:
                r = subprocess.run(
                    f"adb -s {adb_target} shell {cmd}",
                    shell=True, capture_output=True, text=True, timeout=30,
                )
                return r.stdout.strip()
            except Exception as e:
                errors.append(str(e))
                return ""

        # Chrome DB paths
        chrome_cookies = "/data/data/com.android.chrome/app_chrome/Default/Cookies"
        chrome_history = "/data/data/com.android.chrome/app_chrome/Default/History"

        # Force-stop Chrome before injection
        sh("am force-stop com.android.chrome")

        # 1. Inject cookies
        for cookie in plan.cookies_to_inject:
            sql = (
                f"INSERT OR REPLACE INTO cookies "
                f"(host_key, name, value, path, creation_utc, "
                f"last_access_utc, expires_utc, is_secure, is_httponly, "
                f"samesite, priority) VALUES ("
                f"'{cookie['host']}', '{cookie['name']}', "
                f"'{cookie['value']}', '{cookie['path']}', "
                f"{cookie['creation_utc']}, {cookie['last_access_utc']}, "
                f"{cookie['expires_utc']}, {cookie['is_secure']}, "
                f"{cookie['is_httponly']}, {cookie['samesite']}, "
                f"{cookie['priority']}"
                f");"
            )
            result = sh(f"sqlite3 {chrome_cookies} \"{sql}\" 2>/dev/null")
            if "error" not in result.lower():
                cookies_ok += 1

        # 2. Inject browsing history
        for session in plan.browsing_sessions:
            for page in session["page_views"]:
                # Chrome History uses microsecond timestamps
                chrome_ts = (page["timestamp"] * 1_000_000) + 11_644_473_600_000_000
                sql = (
                    f"INSERT INTO urls (url, title, visit_count, "
                    f"typed_count, last_visit_time) VALUES ("
                    f"'{page['url']}', '{page['title']}', "
                    f"1, 0, {chrome_ts});"
                )
                result = sh(f"sqlite3 {chrome_history} \"{sql}\" 2>/dev/null")
                if "error" not in result.lower():
                    history_ok += 1

        # 3. Record warm-up transactions (as browsing history entries)
        for tx in plan.warmup_transactions:
            # Create order confirmation page visit
            order_url = f"https://www.{plan.merchant_domain}/order/{tx['order_id']}"
            chrome_ts = (tx["timestamp"] * 1_000_000) + 11_644_473_600_000_000
            sql = (
                f"INSERT INTO urls (url, title, visit_count, "
                f"typed_count, last_visit_time) VALUES ("
                f"'{order_url}', "
                f"'Order Confirmation - {tx['item']}', "
                f"1, 0, {chrome_ts});"
            )
            result = sh(f"sqlite3 {chrome_history} \"{sql}\" 2>/dev/null")
            if "error" not in result.lower():
                warmup_ok += 1

        # Fix Chrome DB ownership
        chrome_uid = sh("stat -c %u /data/data/com.android.chrome 2>/dev/null")
        if chrome_uid:
            sh(f"chown {chrome_uid}:{chrome_uid} {chrome_cookies}")
            sh(f"chown {chrome_uid}:{chrome_uid} {chrome_history}")
        sh(f"chmod 660 {chrome_cookies} {chrome_history}")
        sh(f"restorecon -R /data/data/com.android.chrome/app_chrome/ 2>/dev/null")

        duration = time.time() - start
        return PrewarmResult(
            merchant_domain=plan.merchant_domain,
            success=cookies_ok > 0 or history_ok > 0,
            cookies_injected=cookies_ok,
            history_entries_added=history_ok,
            warmup_txs_added=warmup_ok,
            chrome_updated=True,
            duration_s=duration,
            errors=errors,
        )

    # ──────────────────────────────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────────────────────────────

    def _generate_generic_profile(self, domain: str) -> dict:
        """Generate a generic merchant profile for unknown domains."""
        return {
            "name": domain.split(".")[0].title(),
            "mcc": "5999",
            "low_value_items": [
                ("Digital gift card", 10.00),
                ("Basic item", 7.99),
                ("Accessory", 5.49),
            ],
            "pages": ["/", "/account", "/products", "/cart", "/checkout"],
            "cookies": ["session", "user_id", "cart", "pref"],
            "3ds_exempt_below": 25.0,
        }

    @staticmethod
    def _generate_order_id(merchant_name: str) -> str:
        """Generate merchant-specific order ID format."""
        import secrets
        name = merchant_name.lower()
        if "amazon" in name:
            return f"114-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}"
        elif "ebay" in name:
            return f"{random.randint(10, 99)}-{random.randint(10000, 99999)}-{random.randint(10000, 99999)}"
        elif "walmart" in name:
            return f"{random.randint(100000000, 999999999)}"
        elif "best buy" in name:
            return f"BBY01-{random.randint(800000000, 899999999)}"
        elif "target" in name:
            return f"{random.randint(100000000, 999999999)}"
        else:
            return f"ORD-{secrets.token_hex(6).upper()}"

    def get_optimal_merchants(self, bin_prefix: str,
                               amount: float) -> List[Dict[str, Any]]:
        """
        Rank merchants by 3DS frictionless likelihood for this BIN+amount.

        Returns list of merchants sorted by expected frictionless rate.
        """
        results = []
        strategy = self._get_strategy()

        for domain, profile in MERCHANT_PREWARM_PROFILES.items():
            challenge_rate = 0.5
            if strategy:
                try:
                    rec = strategy.get_recommendations(
                        bin_prefix=bin_prefix,
                        merchant=domain,
                        amount=amount,
                    )
                    if rec and hasattr(rec, "risk_score"):
                        challenge_rate = rec.risk_score / 100.0
                except Exception:
                    pass

            results.append({
                "domain": domain,
                "name": profile["name"],
                "challenge_rate": round(challenge_rate, 3),
                "frictionless_rate": round(1.0 - challenge_rate, 3),
                "lve_eligible": amount < profile.get("3ds_exempt_below", 0),
            })

        results.sort(key=lambda r: r["challenge_rate"])
        return results
