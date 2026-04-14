"""
Transaction Simulator — Purchase Flow Automation
=================================================
Simulates and automates purchase transactions for testing wallet injection
and zero-auth configuration without requiring actual payments.

This module provides:
- In-app purchase flow simulation
- Receipt generation for coherence
- Transaction velocity management
- Anti-fraud compliance patterns

Usage::

    from transaction_simulator import TransactionSimulator, PurchaseRequest
    
    simulator = TransactionSimulator(device_executor)
    
    result = await simulator.simulate_purchase(PurchaseRequest(
        app_package="com.spotify.music",
        product_id="premium_monthly",
        price_micros=999_0000,
        currency="USD",
    ))
    
    if result.success:
        print(f"Purchase simulated: {result.order_id}")
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import secrets
import string
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("titan.transaction-simulator")


class PurchaseType(str, Enum):
    """Types of purchase transactions."""
    IN_APP = "in_app"           # In-app purchase (IAP)
    SUBSCRIPTION = "subscription"  # Recurring subscription
    ONE_TIME = "one_time"       # One-time app purchase
    CONSUMABLE = "consumable"   # Consumable IAP
    NFC_TAP = "nfc_tap"         # NFC contactless payment


class PurchaseStatus(str, Enum):
    """Purchase transaction status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class PurchaseRequest:
    """Request for a simulated purchase."""
    app_package: str
    product_id: str = ""
    price_micros: int = 0       # Price in micros (e.g., $9.99 = 9990000)
    currency: str = "USD"
    purchase_type: PurchaseType = PurchaseType.IN_APP
    
    # Optional details
    product_title: str = ""
    merchant_name: str = ""
    billing_period: str = ""    # For subscriptions: "P1M", "P1Y", etc.
    
    # Simulation options
    simulate_3ds: bool = False  # Simulate 3DS challenge
    simulate_failure: bool = False
    delay_seconds: float = 0.0


@dataclass
class PurchaseResult:
    """Result of a simulated purchase."""
    success: bool = False
    status: PurchaseStatus = PurchaseStatus.PENDING
    
    order_id: str = ""          # GPA.XXXX-XXXX-XXXX-XXXXX format
    transaction_id: str = ""
    purchase_token: str = ""
    
    # Timestamps
    purchase_time_ms: int = 0
    acknowledged_time_ms: int = 0
    
    # Receipt data
    receipt_data: Dict[str, Any] = field(default_factory=dict)
    signature: str = ""
    
    # Error info
    error_code: str = ""
    error_message: str = ""
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "status": self.status.value,
            "order_id": self.order_id,
            "transaction_id": self.transaction_id,
            "purchase_time_ms": self.purchase_time_ms,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


@dataclass
class TransactionHistoryEntry:
    """Entry for transaction history injection."""
    order_id: str
    merchant_name: str
    amount_cents: int
    currency: str
    timestamp_ms: int
    status: str = "APPROVED"
    card_last_four: str = ""
    network: str = "visa"
    arqc: str = ""
    atc: int = 0


def generate_order_id() -> str:
    """Generate a realistic Google Play order ID."""
    chars = string.digits + string.ascii_uppercase
    parts = [
        "".join(random.choices(chars, k=4)),
        "".join(random.choices(chars, k=4)),
        "".join(random.choices(chars, k=4)),
        "".join(random.choices(chars, k=5)),
    ]
    return f"GPA.{'-'.join(parts)}"


def generate_purchase_token() -> str:
    """Generate a purchase token for IAP verification."""
    return secrets.token_urlsafe(64)


def generate_transaction_id() -> str:
    """Generate a transaction ID."""
    return f"TXN{secrets.token_hex(12).upper()}"


class TransactionSimulator:
    """
    Simulates purchase transactions for testing wallet and billing integration.
    
    This simulator:
    1. Generates realistic purchase records
    2. Creates proper receipt data for validation
    3. Manages transaction velocity to avoid anti-fraud triggers
    4. Injects transaction history for behavioral legitimacy
    """
    
    # Popular apps with known product IDs for simulation
    KNOWN_PRODUCTS = {
        "com.spotify.music": [
            ("premium_monthly", "Spotify Premium", 999_0000, "P1M"),
            ("premium_annual", "Spotify Premium Annual", 9999_0000, "P1Y"),
        ],
        "com.netflix.mediaclient": [
            ("basic_monthly", "Basic Plan", 699_0000, "P1M"),
            ("standard_monthly", "Standard Plan", 1549_0000, "P1M"),
            ("premium_monthly", "Premium Plan", 2299_0000, "P1M"),
        ],
        "com.google.android.apps.youtube.music": [
            ("music_premium", "YouTube Music Premium", 1099_0000, "P1M"),
        ],
        "com.discord": [
            ("nitro_monthly", "Discord Nitro", 999_0000, "P1M"),
            ("nitro_classic", "Nitro Classic", 499_0000, "P1M"),
        ],
    }
    
    # Velocity limits (anti-fraud compliance)
    MAX_PURCHASES_PER_HOUR = 5
    MAX_PURCHASES_PER_DAY = 20
    MIN_DELAY_BETWEEN_PURCHASES = 30  # seconds
    
    def __init__(self, 
                 device_executor: Optional[Callable] = None,
                 email: str = "",
                 card_last_four: str = ""):
        """
        Initialize transaction simulator.
        
        Args:
            device_executor: Async function to execute commands on device
            email: Google account email for receipts
            card_last_four: Last 4 digits of card for transaction records
        """
        self.executor = device_executor
        self.email = email
        self.card_last_four = card_last_four
        self._recent_purchases: List[Tuple[float, str]] = []  # (timestamp, order_id)
        self._transaction_history: List[TransactionHistoryEntry] = []
    
    async def simulate_purchase(self, request: PurchaseRequest) -> PurchaseResult:
        """
        Simulate a purchase transaction.
        
        This generates all the data that would be created by a real purchase
        without actually charging the card.
        
        Args:
            request: Purchase request details
            
        Returns:
            PurchaseResult with generated transaction data
        """
        result = PurchaseResult()
        
        # Check velocity limits
        if not self._check_velocity():
            result.error_code = "VELOCITY_LIMIT"
            result.error_message = "Too many recent purchases, please wait"
            result.status = PurchaseStatus.FAILED
            return result
        
        # Simulate processing delay
        if request.delay_seconds > 0:
            await asyncio.sleep(request.delay_seconds)
        else:
            await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Check for forced failure
        if request.simulate_failure:
            result.error_code = "DECLINED"
            result.error_message = "Card declined by issuer"
            result.status = PurchaseStatus.FAILED
            return result
        
        # Simulate 3DS challenge if requested
        if request.simulate_3ds:
            logger.info("Simulating 3DS challenge (auto-pass in test mode)")
            await asyncio.sleep(1.0)
        
        # Generate purchase data
        now_ms = int(time.time() * 1000)
        
        result.order_id = generate_order_id()
        result.transaction_id = generate_transaction_id()
        result.purchase_token = generate_purchase_token()
        result.purchase_time_ms = now_ms
        result.acknowledged_time_ms = now_ms + random.randint(100, 500)
        
        # Generate receipt data
        result.receipt_data = self._generate_receipt(request, result)
        result.signature = self._sign_receipt(result.receipt_data)
        
        result.success = True
        result.status = PurchaseStatus.COMPLETED
        
        # Record for velocity tracking
        self._recent_purchases.append((time.time(), result.order_id))
        
        # Add to transaction history
        merchant = request.merchant_name or request.app_package.split(".")[-1].title()
        self._transaction_history.append(TransactionHistoryEntry(
            order_id=result.order_id,
            merchant_name=merchant,
            amount_cents=request.price_micros // 10000,
            currency=request.currency,
            timestamp_ms=now_ms,
            card_last_four=self.card_last_four,
        ))
        
        logger.info(
            "Purchase simulated: %s %s %s/%d",
            result.order_id, request.app_package,
            request.currency, request.price_micros
        )
        
        return result
    
    async def simulate_subscription(self, 
                                    app_package: str,
                                    product_id: str = "",
                                    months: int = 1) -> List[PurchaseResult]:
        """
        Simulate a subscription with billing history.
        
        Generates multiple monthly billing records to simulate an active
        subscription with payment history.
        
        Args:
            app_package: App package name
            product_id: Subscription product ID
            months: Number of months of history to generate
            
        Returns:
            List of PurchaseResult for each billing cycle
        """
        results = []
        
        # Get product info
        products = self.KNOWN_PRODUCTS.get(app_package, [])
        product = None
        for p in products:
            if p[0] == product_id or not product_id:
                product = p
                break
        
        if not product:
            product = (product_id or "subscription", "Subscription", 999_0000, "P1M")
        
        product_id, title, price, period = product
        
        # Generate billing history
        now = time.time()
        for i in range(months):
            billing_time = now - (i * 30 * 24 * 60 * 60)  # ~30 days per month
            
            request = PurchaseRequest(
                app_package=app_package,
                product_id=product_id,
                product_title=title,
                price_micros=price,
                purchase_type=PurchaseType.SUBSCRIPTION,
                billing_period=period,
            )
            
            result = await self.simulate_purchase(request)
            result.purchase_time_ms = int(billing_time * 1000)
            results.append(result)
        
        logger.info("Subscription history generated: %s x%d months", app_package, months)
        return results
    
    async def simulate_nfc_tap(self,
                               merchant_name: str,
                               amount_cents: int,
                               currency: str = "USD") -> PurchaseResult:
        """
        Simulate an NFC contactless payment.
        
        Args:
            merchant_name: Merchant name
            amount_cents: Amount in cents
            currency: Currency code
            
        Returns:
            PurchaseResult for the NFC transaction
        """
        request = PurchaseRequest(
            app_package="com.google.android.apps.walletnfcrel",
            product_id="nfc_payment",
            product_title=f"Payment at {merchant_name}",
            merchant_name=merchant_name,
            price_micros=amount_cents * 10000,
            currency=currency,
            purchase_type=PurchaseType.NFC_TAP,
        )
        
        result = await self.simulate_purchase(request)
        
        # Add EMV-specific data for NFC
        if result.success:
            result.receipt_data["payment_type"] = "NFC_CONTACTLESS"
            result.receipt_data["terminal_id"] = f"TRM{secrets.token_hex(4).upper()}"
            result.receipt_data["auth_code"] = f"{random.randint(100000, 999999)}"
        
        return result
    
    def get_transaction_history(self) -> List[TransactionHistoryEntry]:
        """Get all simulated transaction history entries."""
        return list(self._transaction_history)
    
    def get_transaction_history_for_injection(self) -> List[Dict[str, Any]]:
        """Get transaction history formatted for database injection."""
        return [
            {
                "order_id": tx.order_id,
                "merchant_name": tx.merchant_name,
                "amount_cents": tx.amount_cents,
                "currency": tx.currency,
                "timestamp_ms": tx.timestamp_ms,
                "status": tx.status,
                "arqc": tx.arqc,
                "atc": tx.atc,
            }
            for tx in self._transaction_history
        ]
    
    def _check_velocity(self) -> bool:
        """Check if we're within velocity limits."""
        now = time.time()
        
        # Clean old entries
        self._recent_purchases = [
            (ts, oid) for ts, oid in self._recent_purchases
            if now - ts < 86400  # Keep 24 hours
        ]
        
        # Check hourly limit
        hour_ago = now - 3600
        hourly_count = sum(1 for ts, _ in self._recent_purchases if ts > hour_ago)
        if hourly_count >= self.MAX_PURCHASES_PER_HOUR:
            return False
        
        # Check daily limit
        daily_count = len(self._recent_purchases)
        if daily_count >= self.MAX_PURCHASES_PER_DAY:
            return False
        
        # Check minimum delay
        if self._recent_purchases:
            last_ts = max(ts for ts, _ in self._recent_purchases)
            if now - last_ts < self.MIN_DELAY_BETWEEN_PURCHASES:
                return False
        
        return True
    
    def _generate_receipt(self, request: PurchaseRequest, result: PurchaseResult) -> Dict[str, Any]:
        """Generate receipt data for a purchase."""
        return {
            "orderId": result.order_id,
            "packageName": request.app_package,
            "productId": request.product_id,
            "purchaseTime": result.purchase_time_ms,
            "purchaseState": 0,  # 0 = purchased
            "purchaseToken": result.purchase_token,
            "quantity": 1,
            "acknowledged": True,
            "developerPayload": "",
            "obfuscatedAccountId": hashlib.sha256(self.email.encode()).hexdigest()[:16],
            "obfuscatedProfileId": secrets.token_hex(8),
        }
    
    def _sign_receipt(self, receipt: Dict[str, Any]) -> str:
        """Generate a mock signature for the receipt."""
        # In real IAP, this would be RSA-signed by Google
        # We generate a realistic-looking but fake signature
        data = str(sorted(receipt.items())).encode()
        return hashlib.sha256(data).hexdigest()


class PurchaseHistoryGenerator:
    """
    Generates realistic purchase history for behavioral aging.
    
    Creates a diverse set of purchase records that:
    - Span the account lifetime
    - Follow circadian patterns
    - Include a mix of free and paid apps
    - Have realistic merchant diversity
    """
    
    # Popular apps by category
    APPS_BY_CATEGORY = {
        "social": [
            ("com.instagram.android", "Instagram", 0),
            ("com.facebook.katana", "Facebook", 0),
            ("com.twitter.android", "Twitter", 0),
            ("com.snapchat.android", "Snapchat", 0),
            ("com.zhiliaoapp.musically", "TikTok", 0),
        ],
        "entertainment": [
            ("com.spotify.music", "Spotify", 0),
            ("com.netflix.mediaclient", "Netflix", 0),
            ("com.google.android.youtube", "YouTube", 0),
            ("com.disney.disneyplus", "Disney+", 0),
            ("com.hbo.hbonow", "HBO Max", 0),
        ],
        "productivity": [
            ("com.google.android.apps.docs", "Google Docs", 0),
            ("com.microsoft.office.word", "Microsoft Word", 0),
            ("com.notion.id", "Notion", 0),
            ("com.slack", "Slack", 0),
            ("com.dropbox.android", "Dropbox", 0),
        ],
        "shopping": [
            ("com.amazon.mShop.android.shopping", "Amazon", 0),
            ("com.ebay.mobile", "eBay", 0),
            ("com.target.ui", "Target", 0),
            ("com.walmart.android", "Walmart", 0),
        ],
        "finance": [
            ("com.paypal.android.p2pmobile", "PayPal", 0),
            ("com.venmo", "Venmo", 0),
            ("com.squareup.cash", "Cash App", 0),
        ],
        "games_free": [
            ("com.supercell.clashofclans", "Clash of Clans", 0),
            ("com.king.candycrushsaga", "Candy Crush", 0),
            ("com.rovio.angrybirds", "Angry Birds", 0),
        ],
        "games_paid": [
            ("com.mojang.minecraftpe", "Minecraft", 749_0000),
            ("com.rockstargames.gtasa", "GTA: San Andreas", 699_0000),
            ("com.innersloth.spacemafia", "Among Us", 399_0000),
        ],
        "utilities": [
            ("com.google.android.apps.photos", "Google Photos", 0),
            ("com.google.android.gm", "Gmail", 0),
            ("com.google.android.apps.maps", "Google Maps", 0),
        ],
    }
    
    # Circadian weights (index = hour 0-23)
    CIRCADIAN_WEIGHTS = [
        1, 1, 1, 1, 1, 2,      # 00-05: night
        3, 5, 7, 9, 10, 10,    # 06-11: morning
        9, 10, 10, 9, 8, 8,    # 12-17: afternoon
        7, 6, 5, 4, 2, 1,      # 18-23: evening
    ]
    
    def __init__(self, email: str, age_days: int = 90):
        self.email = email
        self.age_days = age_days
    
    def generate(self, 
                 num_free: int = 15,
                 num_paid: int = 3,
                 num_iap: int = 5) -> List[Dict[str, Any]]:
        """
        Generate diverse purchase history.
        
        Args:
            num_free: Number of free app installs
            num_paid: Number of paid app purchases
            num_iap: Number of in-app purchases
            
        Returns:
            List of purchase records for library.db injection
        """
        purchases = []
        now_ms = int(time.time() * 1000)
        birth_ms = now_ms - self.age_days * 86400 * 1000
        
        # Select free apps from multiple categories
        free_apps = []
        for category in ["social", "entertainment", "productivity", "shopping", 
                        "finance", "games_free", "utilities"]:
            apps = self.APPS_BY_CATEGORY.get(category, [])
            if apps:
                free_apps.extend(random.sample(apps, min(3, len(apps))))
        
        random.shuffle(free_apps)
        for pkg, name, _ in free_apps[:num_free]:
            purchase_ts = self._generate_timestamp(birth_ms, now_ms)
            purchases.append({
                "app_id": pkg,
                "doc_type": 1,
                "purchase_time_ms": purchase_ts,
                "price_micros": 0,
                "currency": "USD",
                "order_id": generate_order_id(),
            })
        
        # Add paid apps
        paid_apps = self.APPS_BY_CATEGORY.get("games_paid", [])
        for pkg, name, price in random.sample(paid_apps, min(num_paid, len(paid_apps))):
            purchase_ts = self._generate_timestamp(birth_ms, now_ms)
            purchases.append({
                "app_id": pkg,
                "doc_type": 1,
                "purchase_time_ms": purchase_ts,
                "price_micros": price,
                "currency": "USD",
                "order_id": generate_order_id(),
            })
        
        # Add in-app purchases
        iap_apps = ["com.supercell.clashofclans", "com.king.candycrushsaga",
                    "com.spotify.music", "com.discord"]
        for _ in range(num_iap):
            app = random.choice(iap_apps)
            purchase_ts = self._generate_timestamp(birth_ms, now_ms)
            purchases.append({
                "app_id": app,
                "doc_type": 1,  # IAP also uses doc_type 1
                "purchase_time_ms": purchase_ts,
                "price_micros": random.choice([99_0000, 199_0000, 499_0000, 999_0000]),
                "currency": "USD",
                "order_id": generate_order_id(),
            })
        
        # Sort by timestamp
        purchases.sort(key=lambda x: x["purchase_time_ms"])
        
        logger.info(
            "Generated purchase history: %d free, %d paid, %d IAP over %d days",
            num_free, num_paid, num_iap, self.age_days
        )
        
        return purchases
    
    def _generate_timestamp(self, birth_ms: int, now_ms: int) -> int:
        """Generate a circadian-weighted timestamp."""
        # Random day within range
        day_offset_ms = random.randint(0, now_ms - birth_ms)
        base_ts = birth_ms + day_offset_ms
        
        # Apply circadian weighting to hour
        hour = random.choices(range(24), weights=self.CIRCADIAN_WEIGHTS)[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        # Adjust to selected hour
        day_start = (base_ts // 86400000) * 86400000
        return day_start + hour * 3600000 + minute * 60000 + second * 1000


# ── Convenience functions ─────────────────────────────────────────────────────

async def simulate_purchase_flow(
    app_package: str,
    product_id: str,
    price_micros: int,
    email: str = "",
    card_last_four: str = "",
) -> PurchaseResult:
    """
    Convenience function to simulate a single purchase.
    
    Args:
        app_package: App package name
        product_id: Product ID
        price_micros: Price in micros
        email: Account email
        card_last_four: Card last 4 digits
        
    Returns:
        PurchaseResult
    """
    simulator = TransactionSimulator(email=email, card_last_four=card_last_four)
    request = PurchaseRequest(
        app_package=app_package,
        product_id=product_id,
        price_micros=price_micros,
    )
    return await simulator.simulate_purchase(request)


def generate_purchase_history(
    email: str,
    age_days: int = 90,
    num_entries: int = 20,
) -> List[Dict[str, Any]]:
    """
    Convenience function to generate purchase history.
    
    Args:
        email: Account email
        age_days: Account age in days
        num_entries: Approximate number of entries
        
    Returns:
        List of purchase records
    """
    generator = PurchaseHistoryGenerator(email, age_days)
    num_free = int(num_entries * 0.6)
    num_paid = int(num_entries * 0.15)
    num_iap = num_entries - num_free - num_paid
    return generator.generate(num_free, num_paid, num_iap)
