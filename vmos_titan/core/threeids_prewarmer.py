"""
ThreeDSPrewarmer - Issuer Risk Engine Manipulation
Pre-conditions issuers for frictionless transactions via micro-transaction warmth,
cookie seeding, browser history injection, and merchant-specific targeting.

Key Strategy: Establish "Trusted Beneficiary" signal before high-value transaction.
"""

import random
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class ThreeDSPrewarmer:
    """
    Manipulates issuer Risk-Based Authentication (RBA) scoring
    to achieve frictionless transaction processing (5% challenge probability).
    """
    
    # Real merchants with low-value exemption items
    MERCHANT_PREWARM_PROFILES = {
        "amazon": {
            "mcc": 5399,
            "items": ["Kindle eBook", "USB Cable", "AAA Batteries", "Phone Charger"],
            "price_range": (4.99, 7.99),
            "cookie_keys": ["session-id", "session-token", "ubid-main", "csm-hit", "x-main"],
        },
        "walmart": {
            "mcc": 5411,
            "items": ["Hand Soap", "Water Bottle", "Dish Cloths", "Snack Bars"],
            "price_range": (2.97, 4.97),
            "cookie_keys": ["auth", "customer", "CRT", "cart-item-count"],
        },
        "target": {
            "mcc": 5310,
            "items": ["Cotton Balls", "Snack Bars", "Candles", "Notebook"],
            "price_range": (2.49, 5.00),
            "cookie_keys": ["visitorId", "GuestLocation", "sapphire", "TealeafAkaSid"],
        },
        "apple": {
            "mcc": 5961,
            "items": ["App Store Credit", "Apple Music Trial"],
            "price_range": (4.99, 9.99),
            "cookie_keys": ["myacinfo", "X-APPLE-WEB-KB", "dslang"],
        },
    }
    
    # Base challenge probability per BIN/merchant
    BASE_CHALLENGE_RATES = {
        "visa_uk": 0.45,
        "visa_us": 0.35,
        "mastercard_us": 0.50,
        "mastercard_eu": 0.40,
        "amex": 0.25,
    }
    
    def __init__(self, 
                 profile_age_days: int = 90,
                 target_merchant: str = "amazon",
                 target_amount: float = 500.00,
                 timezone: str = "US/Eastern"):
        """
        Args:
            profile_age_days: Age of synthetic profile (90, 180, etc.)
            target_merchant: Primary merchant for main transaction
            target_amount: Value of high-risk transaction to execute
            timezone: For circadian weighting of timestamps
        """
        self.profile_age_days = max(30, profile_age_days)  # minimum 30 days viable
        self.target_merchant = target_merchant
        self.target_amount = target_amount
        self.timezone = timezone
        
    def calculate_challenge_probability(self, 
                                        bin_code: str,
                                        merchant: str = None) -> float:
        """
        Estimate baseline challenge rate for specific BIN/merchant pair.
        
        Args:
            bin_code: First 6 digits of card (FPAN)
            merchant: Target merchant
            
        Returns:
            Challenge probability (0.0 to 1.0)
        """
        merchant = merchant or self.target_merchant
        
        # Simplified lookup
        if bin_code.startswith("4"):  # Visa
            if merchant == "amazon":
                return self.BASE_CHALLENGE_RATES.get("visa_us", 0.35)
        elif bin_code.startswith("5"):  # Mastercard
            return self.BASE_CHALLENGE_RATES.get("mastercard_us", 0.50)
        elif bin_code.startswith("34") or bin_code.startswith("37"):  # Amex
            return self.BASE_CHALLENGE_RATES.get("amex", 0.25)
            
        return 0.40  # Default fallback
        
    def generate_micro_transactions(self, 
                                    count: int = 3) -> List[Dict]:
        """
        Generate warm-up micro-transactions distributed across profile lifetime.
        
        Returns:
            List of micro-transaction records with timestamps.
        """
        merchant_profile = self.MERCHANT_PREWARM_PROFILES.get(
            self.target_merchant,
            self.MERCHANT_PREWARM_PROFILES["amazon"]
        )
        
        transactions = []
        
        # Distribute across profile lifetime (avoid clustering)
        date_offsets = sorted(random.sample(
            range(14, self.profile_age_days - 7),
            min(count, self.profile_age_days // 30)
        ))
        
        for i, days_ago in enumerate(date_offsets):
            # Circadian-weighted hour (business hours: 10 AM - 9 PM)
            hour = random.randint(10, 21)
            minute = random.randint(0, 59)
            
            transaction_date = datetime.now() - timedelta(days=days_ago, hours=hour, minutes=minute)
            
            # Select random item from merchant profile
            item = random.choice(merchant_profile["items"])
            price = round(random.uniform(*merchant_profile["price_range"]), 2)
            
            transactions.append({
                "timestamp": transaction_date,
                "date_iso": transaction_date.isoformat(),
                "merchant": self.target_merchant,
                "item_description": item,
                "amount": price,
                "order_id": f"TTT-{transaction_date.strftime('%Y%m%d%H%M')}-{i:02d}",
                "status": "completed",
                "days_ago": days_ago,
            })
            
        return transactions
        
    def generate_merchant_cookies(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Generate domain-specific cookies for cookie-authenticated transactions.
        
        Returns:
            Dict mapping domain to cookie key-value pairs.
        """
        merchant_profile = self.MERCHANT_PREWARM_PROFILES.get(
            self.target_merchant,
            self.MERCHANT_PREWARM_PROFILES["amazon"]
        )
        
        cookies = {}
        cookie_keys = merchant_profile["cookie_keys"]
        
        for key in cookie_keys:
            # Generate realistic cookie values (random hex)
            value = f"vl_{random.randint(100000, 999999)}_{hex(random.randint(0, 0xFFFFFFFF))[2:]}"
            cookies[key] = value
            
        return {self.target_merchant: cookies}
        
    def generate_browser_history(self, 
                                 transaction_date: datetime = None) -> List[Dict]:
        """
        Generate synthetic Chrome browsing history aligned with micro-transactions.
        
        Returns:
            List of history entries (url, title, timestamp, visit_count)
        """
        transaction_date = transaction_date or (datetime.now() - timedelta(days=30))
        
        merchant_urls = {
            "amazon": [
                ("/", "Amazon.com"),
                ("/s?k=batteries", "Search Results"),
                ("/s?k=cables", "Search Results"),
                ("/dp/B0XXXXXXXXXX", "USB Cable - Amazon"),
                ("/gp/cart/view.html", "Shopping Cart"),
                ("/review/RXXXXXXXXXXX", "Customer Reviews"),
                ("/gp/buy/thankyou", "Order Confirmation"),
            ],
            "walmart": [
                ("/", "Walmart.com"),
                ("/ip/XXXXXXXX", "Product Page"),
                ("/cart/", "Your Cart"),
                ("/checkout/", "Checkout"),
            ],
            "target": [
                ("/", "Target.com"),
                ("/s", "Search/Browse"),
                ("/p/", "Product Detail"),
                ("/checkout", "Checkout"),
            ]
        }
        
        urls = merchant_urls.get(self.target_merchant, merchant_urls["amazon"])
        
        history = []
        for i, (path, title) in enumerate(urls):
            # Spread over 2 hours before transaction
            hour_offset = max(0, 2 - (len(urls) - i) * 0.25)
            visit_time = transaction_date - timedelta(hours=hour_offset)
            
            history.append({
                "url": f"https://{self.target_merchant}.com{path}",
                "title": title,
                "timestamp": visit_time.isoformat(),
                "visit_count": random.randint(1, 3),
            })
            
        return history
        
    def estimate_challenge_reduction(self,
                                     micro_transactions: int = 3,
                                     max_cookie_age_days: int = 30,
                                     history_density: int = 20) -> Dict:
        """
        Calculate estimated RBA score reduction based on warmth parameters.
        
        Returns:
            Projection dict with baseline vs final challenge probability.
        """
        baseline_challenge = self.calculate_challenge_probability("4"  # Visa assumption
        )
        
        # Reduction factors:
        # - 3 micro-transactions reduce risk by ~25%
        # - Ancient cookies (aged) reduce risk by ~10-15%
        # - Dense browsing history reduces risk by ~10-20%
        
        reduction_from_transactions = micro_transactions * 0.08  # 3 * 0.08 = 0.24
        reduction_from_cookies = min(0.15, max_cookie_age_days / 365 * 0.20)  # Age factor
        reduction_from_history = min(0.20, history_density / 100 * 0.25)  # Density factor
        
        total_reduction = reduction_from_transactions + reduction_from_cookies + reduction_from_history
        
        final_challenge = max(0.05, baseline_challenge - total_reduction)  # Floor at 5%
        
        return {
            "baseline_challenge_probability": f"{baseline_challenge:.1%}",
            "reduction_from_micro_transactions": f"{reduction_from_transactions:.1%}",
            "reduction_from_cookies": f"{reduction_from_cookies:.1%}",
            "reduction_from_history": f"{reduction_from_history:.1%}",
            "total_reduction": f"{total_reduction:.1%}",
            "final_challenge_probability": f"{final_challenge:.1%}",
            "frictionless_flow_probability": f"{(1.0 - final_challenge):.1%}",
            "recommendation": "PROCEED_TO_TRANSACTION" if final_challenge < 0.15 else "REQUIRES_OTP",
        }


# Example usage
if __name__ == "__main__":
    prewarmer = ThreeDSPrewarmer(
        profile_age_days=90,
        target_merchant="amazon",
        target_amount=500.00,
        timezone="US/Eastern"
    )
    
    print("=== 3DS Pre-Warming Analysis ===\n")
    
    # Generate warm-up transactions
    micro_txns = prewarmer.generate_micro_transactions(count=3)
    print("Micro-Transactions:")
    for txn in micro_txns:
        print(f"  {txn['date_iso']}: {txn['merchant']} - {txn['item_description']} (${txn['amount']:.2f})")
    
    # Generate cookies
    cookies = prewarmer.generate_merchant_cookies()
    print("\nCookies Generated:")
    for domain, cookie_dict in cookies.items():
        print(f"  {domain}: {len(cookie_dict)} cookies")
    
    # Estimate challenge reduction
    projection = prewarmer.estimate_challenge_reduction()
    print("\nChallenge Probability Projection:")
    for key, val in projection.items():
        print(f"  {key}: {val}")
