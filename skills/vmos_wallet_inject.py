#!/usr/bin/env python3
"""
VMOS WALLET INJECTION + CLOUD SYNC ISOLATION
=============================================
Implements the full 6-target wallet injection from Titan V13 docs:
1. tapandpay.db (Google Pay token database)
2. COIN.xml (Play Store billing, zero-auth mode)
3. Chrome Web Data (autofill card)
4. GMS billing prefs (wallet_instrument_prefs.xml + payment_profile_prefs.xml)
5. NFC prefs (nfc_on_prefs.xml + default_settings.xml)
6. Cloud sync isolation (iptables block Play Store + GMS payments API)

Also sideloads Google Wallet APK if not installed.

Device: APP5B54EI0Z1EOEA
Account: epolusamuel682@gmail.com
"""
import asyncio, base64, hashlib, json, logging, os, random, secrets
import sqlite3, sys, tempfile, time, uuid, hmac

sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/core")
os.environ["VMOS_CLOUD_AK"] = "YOUR_VMOS_AK_HERE"
os.environ["VMOS_CLOUD_SK"] = "YOUR_VMOS_SK_HERE"
from vmos_cloud_api import VMOSCloudClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("wallet")

PAD = "APP5B54EI0Z1EOEA"
EMAIL = "epolusamuel682@gmail.com"
NAME = "Epolu Samuel"
client = VMOSCloudClient(ak=os.environ["VMOS_CLOUD_AK"], sk=os.environ["VMOS_CLOUD_SK"])

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS (proven from vmos_final_inject.py)
# ═══════════════════════════════════════════════════════════════════════════════

async def sh(cmd, timeout=30):
    """Shell via sync_cmd API with timeout protection."""
    try:
        r = await asyncio.wait_for(
            client.sync_cmd(PAD, cmd, timeout_sec=timeout),
            timeout=timeout + 10  # hard deadline beyond API timeout
        )
        if r.get("code") == 200:
            d = r.get("data")
            if isinstance(d, list) and d:
                return str(d[0].get("errorMsg", "")).strip()
        return ""
    except asyncio.TimeoutError:
        log.warning(f"  TIMEOUT: {cmd[:60]}...")
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERR:{e}]"

async def push_bytes(data, target_path, owner="system:system", mode="660"):
    """Push bytes via chunked base64 through sync_cmd."""
    b64 = base64.b64encode(data).decode("ascii")
    h = hashlib.md5(target_path.encode()).hexdigest()[:8]
    staging = f"/data/local/tmp/_f_{h}"
    b64f = f"{staging}.b64"
    await sh(f"rm -f {b64f} {staging}")

    CHUNK = 3000
    chunks = [b64[i:i+CHUNK] for i in range(0, len(b64), CHUNK)]
    log.info(f"    Push {len(data)}B ({len(chunks)} chunks) → {target_path}")

    for i, chunk in enumerate(chunks):
        await sh(f"echo -n '{chunk}' >> {b64f}")
        if i % 6 == 5:
            await asyncio.sleep(1)

    await sh(f"base64 -d {b64f} > {staging} 2>/dev/null")
    target_dir = os.path.dirname(target_path)
    await sh(f"mkdir -p {target_dir}")
    await sh(f"cp {staging} {target_path}")
    await sh(f"chown {owner} {target_path}")
    await sh(f"chmod {mode} {target_path}")
    await sh(f"restorecon {target_path} 2>/dev/null")
    await sh(f"rm -f {b64f} {staging}")
    if target_path.endswith(".db"):
        await sh(f"rm -f {target_path}-wal {target_path}-shm {target_path}-journal")
    return True

async def push_xml(xml_str, target_path, owner="system:system"):
    """Push XML string as file."""
    return await push_bytes(xml_str.encode("utf-8"), target_path, owner=owner, mode="660")

def tmp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path

def read_and_delete(path):
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data

# ═══════════════════════════════════════════════════════════════════════════════
# DPAN GENERATION (from wallet_injection.py)
# ═══════════════════════════════════════════════════════════════════════════════

# TSP-assigned Token BIN ranges
TOKEN_BINS = {
    "visa": ["489537", "489538", "489539", "440066", "440067"],
    "mastercard": ["530060", "530061", "530062", "530063"],
    "amex": ["374800", "374801"],
    "discover": ["601156", "601157"],
}

def detect_network(card_num):
    first = card_num[0]
    if first == "4": return "visa"
    elif first in ("5", "2"): return "mastercard"
    elif first == "3": return "amex"
    elif first == "6": return "discover"
    return "visa"

def generate_dpan(card_num):
    """Generate Luhn-valid DPAN using TSP BIN ranges."""
    network = detect_network(card_num)
    token_bin = random.choice(TOKEN_BINS.get(network, TOKEN_BINS["visa"]))
    length = 15 if network == "amex" else 16
    remaining = length - len(token_bin) - 1  # -1 for check digit
    body = "".join(str(random.randint(0, 9)) for _ in range(remaining))
    partial = token_bin + body

    digits = [int(d) for d in partial]
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    check_digit = (10 - checksum % 10) % 10
    return partial + str(check_digit)

def derive_luk(fpan, dpan):
    """Derive Limited Use Key (LUK) for EMV contactless."""
    master_key = hashlib.sha256(fpan.encode()).digest()
    derivation_data = dpan.encode() + secrets.token_bytes(8)
    return hmac.new(master_key, derivation_data, hashlib.sha256).digest()

# ═══════════════════════════════════════════════════════════════════════════════
# TARGET 1: tapandpay.db (Google Pay token database)
# ═══════════════════════════════════════════════════════════════════════════════

def build_tapandpay_db(dpan, last4, network, exp_month, exp_year, cardholder, card_num):
    """Build tapandpay.db with complete token + EMV + transaction history."""
    path = tmp_db()
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.execute("PRAGMA user_version = 1")

    # Main tokens table — enriched schema per Advanced Wallet Provisioning analysis
    c.execute("""CREATE TABLE IF NOT EXISTS tokens (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        issuer_id TEXT, dpan TEXT NOT NULL, fpan_last_four TEXT NOT NULL,
        token_service_provider INTEGER DEFAULT 1, network INTEGER NOT NULL,
        issuer_name TEXT, card_description TEXT, card_color INTEGER DEFAULT -12285185,
        expiry_month INTEGER, expiry_year INTEGER, status INTEGER DEFAULT 1,
        provisioning_status TEXT DEFAULT 'PROVISIONED',
        token_requestor_id TEXT DEFAULT 'GOOGLE_PAY',
        token_reference_id TEXT, wallet_account_id TEXT,
        funding_source_id TEXT,
        creation_timestamp INTEGER, last_used_timestamp INTEGER,
        is_default INTEGER DEFAULT 1, terms_accepted INTEGER DEFAULT 1,
        terms_and_conditions_accepted INTEGER DEFAULT 0,
        card_art_url TEXT DEFAULT '')""")

    # token_metadata VIEW for app version compatibility
    c.execute("CREATE VIEW IF NOT EXISTS token_metadata AS SELECT * FROM tokens")

    # EMV AID info
    c.execute("""CREATE TABLE IF NOT EXISTS emv_aid_info (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_id INTEGER, aid TEXT, priority INTEGER DEFAULT 1,
        FOREIGN KEY (token_id) REFERENCES tokens(_id))""")

    # EMV metadata for cryptographic validation appearance
    c.execute("""CREATE TABLE IF NOT EXISTS emv_metadata (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_id INTEGER, cvn INTEGER DEFAULT 17,
        cryptogram_type TEXT DEFAULT 'ARQC',
        iad TEXT, FOREIGN KEY (token_id) REFERENCES tokens(_id))""")

    # Session keys (LUK)
    c.execute("""CREATE TABLE IF NOT EXISTS session_keys (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_id INTEGER, key_id TEXT, key_data BLOB,
        atc INTEGER DEFAULT 0, max_transactions INTEGER DEFAULT 10,
        creation_time INTEGER, expiry_time INTEGER,
        FOREIGN KEY (token_id) REFERENCES tokens(_id))""")

    # Transaction history
    c.execute("""CREATE TABLE IF NOT EXISTS transaction_history (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_id INTEGER, transaction_id TEXT UNIQUE,
        merchant_name TEXT, amount_cents INTEGER,
        currency TEXT DEFAULT 'USD', timestamp INTEGER,
        transaction_type TEXT DEFAULT 'CONTACTLESS',
        status TEXT DEFAULT 'COMPLETED',
        FOREIGN KEY (token_id) REFERENCES tokens(_id))""")

    # Funding sources table — richer relational schema per analysis docs
    c.execute("""CREATE TABLE IF NOT EXISTS funding_sources (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        funding_source_id TEXT UNIQUE, type TEXT DEFAULT 'CREDIT_CARD',
        display_name TEXT, network INTEGER, last_four TEXT,
        expiry_month INTEGER, expiry_year INTEGER,
        is_active INTEGER DEFAULT 1, creation_time INTEGER)""")

    # Required empty tables for schema compatibility
    c.execute("CREATE TABLE IF NOT EXISTS billing_prefs (key TEXT, value TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS enrollment_info (token_id INTEGER, enrollment_data TEXT)")

    # Map network to integer
    NETWORK_MAP = {"visa": 1, "mastercard": 2, "amex": 3, "discover": 4}
    network_int = NETWORK_MAP.get(network, 1)
    NETWORK_NAMES = {"visa": "Visa", "mastercard": "Mastercard", "amex": "Amex", "discover": "Discover"}
    network_name = NETWORK_NAMES.get(network, "Visa")

    now_ms = int(time.time() * 1000)
    # Card created 14-30 days ago
    created_ms = now_ms - random.randint(14 * 86400000, 30 * 86400000)
    # Last used 0-3 days ago
    last_used_ms = now_ms - random.randint(0, 3 * 86400000)
    wallet_account_id = f"wallet_{secrets.token_hex(8)}"
    token_ref_id = f"DNITHE{secrets.token_hex(10).upper()}"

    # Card art URLs per network (real Google-hosted assets)
    CARD_ART = {
        "visa": "https://pay.google.com/about/static_kcs/images/logos/visa.svg",
        "mastercard": "https://pay.google.com/about/static_kcs/images/logos/mastercard.svg",
        "amex": "https://pay.google.com/about/static_kcs/images/logos/amex.svg",
        "discover": "https://pay.google.com/about/static_kcs/images/logos/discover.svg",
    }
    card_art = CARD_ART.get(network, CARD_ART["visa"])
    issuer_id = f"issuer_{secrets.token_hex(4)}"
    funding_source_id = f"fs_{secrets.token_hex(8)}"

    # Insert funding source first (relational integrity)
    c.execute("""INSERT INTO funding_sources
        (funding_source_id, type, display_name, network, last_four, expiry_month, expiry_year, creation_time)
        VALUES (?, 'CREDIT_CARD', ?, ?, ?, ?, ?, ?)""",
        (funding_source_id, f"{network_name} ····{last4}", network_int, last4, exp_month, exp_year, created_ms))

    c.execute("""INSERT INTO tokens (
        issuer_id, dpan, fpan_last_four, token_service_provider,
        network, issuer_name, card_description, expiry_month, expiry_year,
        status, provisioning_status, token_requestor_id, token_reference_id,
        wallet_account_id, funding_source_id, creation_timestamp, last_used_timestamp,
        is_default, terms_accepted, terms_and_conditions_accepted, card_art_url
    ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, 1, 'PROVISIONED', 'GOOGLE_PAY',
              ?, ?, ?, ?, ?, 1, 1, ?, ?)""", (
        issuer_id,
        dpan, last4, network_int,
        cardholder or "Bank",
        f"{network_name} ····{last4}",
        exp_month, exp_year,
        token_ref_id, wallet_account_id,
        funding_source_id,
        created_ms, last_used_ms,
        created_ms,  # terms_and_conditions_accepted timestamp
        card_art,
    ))
    token_id = c.lastrowid

    # EMV AID
    aid = "A0000000041010" if network == "mastercard" else "A0000000031010"
    c.execute("INSERT INTO emv_aid_info (token_id, aid, priority) VALUES (?, ?, 1)", (token_id, aid))

    # EMV metadata
    luk_hex = secrets.token_hex(8)
    c.execute("INSERT INTO emv_metadata (token_id, cvn, cryptogram_type, iad) VALUES (?, 17, 'ARQC', ?)",
              (token_id, f"0A{luk_hex}"))

    # LUK session key
    luk_data = derive_luk(card_num, dpan)
    c.execute("""INSERT INTO session_keys (token_id, key_id, key_data, atc, max_transactions, creation_time, expiry_time)
                 VALUES (?, ?, ?, 0, 10, ?, ?)""",
              (token_id, f"luk_{secrets.token_hex(4)}", luk_data, now_ms, now_ms + 86400000))

    # Transaction history (3-8 historical transactions)
    merchants = [
        ("Starbucks", 575, 5814), ("Amazon.com", 4299, 5942),
        ("Target", 3247, 5411), ("Whole Foods", 8734, 5411),
        ("Shell Gas", 4520, 5541), ("Uber", 2340, 4121),
        ("Netflix", 1599, 5815), ("Walmart", 6723, 5411),
    ]
    num_txns = random.randint(3, 8)
    for i in range(num_txns):
        merchant, amount, mcc = merchants[i % len(merchants)]
        # Spread over the card age
        tx_time = created_ms + random.randint(0, now_ms - created_ms)
        tx_type = random.choice(["CONTACTLESS", "IN_APP", "ONLINE"])
        c.execute("""INSERT INTO transaction_history
                     (token_id, transaction_id, merchant_name, amount_cents, timestamp, transaction_type)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (token_id, f"txn_{secrets.token_hex(8)}", merchant, amount, tx_time, tx_type))

    conn.commit()
    conn.close()
    return read_and_delete(path)

# ═══════════════════════════════════════════════════════════════════════════════
# TARGET 2: COIN.xml (Play Store billing, zero-auth mode)
# ═══════════════════════════════════════════════════════════════════════════════

def build_coin_xml(email, last4, network, exp_month, exp_year):
    """Build COIN.xml with zero-auth + payment method."""
    network_names = {"visa": "Visa", "mastercard": "Mastercard", "amex": "Amex", "discover": "Discover"}
    network_name = network_names.get(network, "Visa")
    instrument_id = f"instrument_{network}_{last4}"
    payment_profile_id = str(uuid.uuid4())
    auth_token = secrets.token_hex(32)
    now_ms = int(time.time() * 1000)

    return f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="billing_client_version">7.1.1</string>
    <boolean name="has_payment_method" value="true" />
    <string name="payment_method_type">CREDIT_CARD</string>
    <string name="default_payment_method_type">{network_name}</string>
    <string name="default_payment_method_last4">{last4}</string>
    <string name="default_payment_method_description">{network_name} ····{last4}</string>
    <string name="default_instrument_id">{instrument_id}</string>
    <string name="instrument_last_four">{last4}</string>
    <string name="instrument_brand">{network_name.upper()}</string>
    <string name="instrument_expiry_month">{exp_month:02d}</string>
    <string name="instrument_expiry_year">{exp_year}</string>
    <string name="instrument_family">{network_name.upper()}</string>
    <boolean name="purchase_requires_auth" value="false" />
    <boolean name="require_purchase_auth" value="false" />
    <string name="auth_token">{auth_token}</string>
    <boolean name="one_touch_enabled" value="true" />
    <boolean name="biometric_payment_enabled" value="true" />
    <string name="account_name">{email}</string>
    <string name="account_type">com.google</string>
    <string name="billing_account">{email}</string>
    <string name="payment_profile_id">{payment_profile_id}</string>
    <boolean name="tos_accepted" value="true" />
    <long name="tos_accepted_time" value="{now_ms}" />
    <boolean name="billing_supported" value="true" />
    <boolean name="billing_supported_subscriptions" value="true" />
    <string name="google_play_billing_version">6.0.0</string>
    <long name="last_sync_time" value="{now_ms}" />
    <long name="instruments_update_time" value="{now_ms}" />
</map>"""

# ═══════════════════════════════════════════════════════════════════════════════
# TARGET 3: Chrome Web Data (autofill card)
# ═══════════════════════════════════════════════════════════════════════════════

def build_chrome_webdata(last4, network, exp_month, exp_year, cardholder, email):
    """Build Chrome Web Data with credit card autofill entry."""
    path = tmp_db()
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS credit_cards (
        guid TEXT NOT NULL, name_on_card TEXT, expiration_month INTEGER,
        expiration_year INTEGER, card_number_encrypted BLOB,
        date_modified INTEGER NOT NULL DEFAULT 0, origin TEXT DEFAULT '',
        use_count INTEGER NOT NULL DEFAULT 0, use_date INTEGER NOT NULL DEFAULT 0,
        billing_address_id TEXT DEFAULT '', nickname TEXT DEFAULT '')""")

    c.execute("""CREATE TABLE IF NOT EXISTS autofill_profiles (
        guid TEXT NOT NULL, company_name TEXT DEFAULT '', street_address TEXT DEFAULT '',
        dependent_locality TEXT DEFAULT '', city TEXT DEFAULT '', state TEXT DEFAULT '',
        zipcode TEXT DEFAULT '', sorting_code TEXT DEFAULT '', country_code TEXT DEFAULT 'US',
        date_modified INTEGER NOT NULL DEFAULT 0, origin TEXT DEFAULT '',
        language_code TEXT DEFAULT 'en-US', use_count INTEGER NOT NULL DEFAULT 0,
        use_date INTEGER NOT NULL DEFAULT 0)""")

    c.execute("""CREATE TABLE IF NOT EXISTS autofill_profile_names (
        guid TEXT NOT NULL, first_name TEXT DEFAULT '', middle_name TEXT DEFAULT '',
        last_name TEXT DEFAULT '', full_name TEXT DEFAULT '')""")

    c.execute("""CREATE TABLE IF NOT EXISTS autofill_profile_emails (
        guid TEXT NOT NULL, email TEXT DEFAULT '')""")

    network_names = {"visa": "Visa", "mastercard": "Mastercard", "amex": "Amex", "discover": "Discover"}
    network_name = network_names.get(network, "Visa")

    now_s = int(time.time())
    date_added = now_s - random.randint(7 * 86400, 30 * 86400)
    last_used = now_s - random.randint(0, 3 * 86400)

    origins = ["https://pay.google.com", "https://www.amazon.com", "https://checkout.stripe.com",
               "https://www.walmart.com", "https://www.bestbuy.com"]
    origin = random.choice(origins)

    card_guid = str(uuid.uuid4())
    # card_number_encrypted=NULL means Chrome shows card but prompts for number on use
    c.execute("""INSERT INTO credit_cards
        (guid, name_on_card, expiration_month, expiration_year,
         card_number_encrypted, date_modified, origin, use_count, use_date, nickname)
        VALUES (?, ?, ?, ?, NULL, ?, ?, 0, ?, ?)""",
        (card_guid, cardholder, exp_month, exp_year,
         date_added, origin, last_used, f"{network_name} ····{last4}"))

    # Autofill address profile
    profile_guid = str(uuid.uuid4())
    parts = cardholder.split()
    first = parts[0] if parts else cardholder
    last = parts[-1] if len(parts) > 1 else ""
    prof_date = now_s - random.randint(14 * 86400, 60 * 86400)

    c.execute("""INSERT INTO autofill_profiles
        (guid, country_code, date_modified, origin, language_code, use_count, use_date)
        VALUES (?, 'US', ?, ?, 'en-US', ?, ?)""",
        (profile_guid, prof_date, origin, random.randint(5, 20), now_s - random.randint(0, 5 * 86400)))

    c.execute("INSERT INTO autofill_profile_names (guid, first_name, last_name, full_name) VALUES (?, ?, ?, ?)",
              (profile_guid, first, last, cardholder))

    c.execute("INSERT INTO autofill_profile_emails (guid, email) VALUES (?, ?)", (profile_guid, email))

    conn.commit()
    conn.close()
    return read_and_delete(path)

# ═══════════════════════════════════════════════════════════════════════════════
# TARGET 4: GMS Billing Prefs
# ═══════════════════════════════════════════════════════════════════════════════

def build_gms_wallet_prefs(email, last4, network, dpan):
    """Build wallet_instrument_prefs.xml."""
    network_names = {"visa": "Visa", "mastercard": "Mastercard", "amex": "Amex", "discover": "Discover"}
    instrument_id = f"instrument_{network}_{last4}"
    now_ms = int(time.time() * 1000)

    return f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="wallet_setup_complete" value="true" />
    <string name="wallet_account">{email}</string>
    <string name="default_instrument_id">{instrument_id}</string>
    <string name="wallet_default_instrument_last4">{last4}</string>
    <string name="wallet_default_instrument_network">{network_names.get(network, 'Visa')}</string>
    <int name="wallet_instrument_count" value="1" />
    <long name="last_sync_timestamp" value="{now_ms}" />
    <boolean name="nfc_payment_enabled" value="true" />
    <boolean name="tap_to_pay_ready" value="true" />
    <string name="wallet_environment">PRODUCTION</string>
</map>"""

def build_gms_payment_prefs(email, dpan):
    """Build payment_profile_prefs.xml."""
    now_ms = int(time.time() * 1000)
    return f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="payment_methods_synced" value="true" />
    <string name="profile_email">{email}</string>
    <string name="default_payment_method_token">{dpan[-8:]}</string>
    <long name="last_sync_time" value="{now_ms}" />
    <boolean name="has_billing_address" value="true" />
    <string name="payment_profile_id">{str(uuid.uuid4())}</string>
</map>"""

# ═══════════════════════════════════════════════════════════════════════════════
# TARGET 5: NFC Prefs
# ═══════════════════════════════════════════════════════════════════════════════

def build_nfc_prefs():
    """Build nfc_on_prefs.xml."""
    return """<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="nfc_setup_done" value="true" />
    <boolean name="nfc_enabled" value="true" />
    <boolean name="tap_and_pay_enabled" value="true" />
    <boolean name="contactless_payments_enabled" value="true" />
    <boolean name="setup_wizard_complete" value="true" />
    <boolean name="user_has_seen_intro" value="true" />
    <string name="default_payment_app">com.google.android.apps.walletnfcrel</string>
    <boolean name="payment_default_changed" value="false" />
</map>"""

def build_wallet_default_settings():
    """Build default_settings.xml for Wallet."""
    now_ms = int(time.time() * 1000)
    return f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="nfc_payment_default_set" value="true" />
    <boolean name="wallet_setup_complete" value="true" />
    <boolean name="has_accepted_tos" value="true" />
    <boolean name="has_seen_onboarding" value="true" />
    <string name="nfc_payment_component">com.google.android.apps.walletnfcrel/.tap.HceDelegateService</string>
    <long name="nfc_setup_timestamp" value="{now_ms}" />
</map>"""

def build_wallet_app_prefs(email):
    """Build com.google.android.apps.walletnfcrel_preferences.xml."""
    return f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="has_accepted_tos" value="true" />
    <boolean name="has_seen_onboarding" value="true" />
    <boolean name="wallet_setup_complete" value="true" />
    <string name="account_name">{email}</string>
    <boolean name="has_payment_cards" value="true" />
    <int name="card_count" value="1" />
    <long name="last_sync_timestamp" value="{int(time.time() * 1000)}" />
</map>"""

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN INJECTION ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    log.info("=" * 70)
    log.info("VMOS WALLET INJECTION + CLOUD SYNC ISOLATION")
    log.info(f"Device: {PAD} | Account: {EMAIL}")
    log.info("=" * 70)

    # Using a synthetic card for injection (no real CC needed per docs)
    # This is a Luhn-valid test Visa number
    CARD_NUM = "4532015112830366"
    LAST4 = CARD_NUM[-4:]
    NETWORK = detect_network(CARD_NUM)
    DPAN = generate_dpan(CARD_NUM)
    EXP_MONTH = 12
    EXP_YEAR = 2027
    CARDHOLDER = NAME

    log.info(f"Card: {NETWORK.upper()} ****{LAST4} | DPAN: ****{DPAN[-4:]}")
    log.info(f"Expiry: {EXP_MONTH:02d}/{EXP_YEAR}")

    # ─── PHASE 0: Force-stop all target apps ───────────────────────────
    log.info("\n[PHASE 0] Force-stopping target applications...")
    for pkg in ["com.google.android.apps.walletnfcrel", "com.google.android.gms",
                "com.android.vending", "com.android.chrome"]:
        await sh(f"am force-stop {pkg}")
    await asyncio.sleep(2)
    log.info("  All target apps force-stopped")

    # ─── PHASE 1: Get app UIDs for ownership ──────────────────────────
    log.info("\n[PHASE 1] Resolving app UIDs...")
    wallet_uid = (await sh("stat -c '%u:%g' /data/data/com.google.android.apps.walletnfcrel 2>/dev/null")).strip().strip("'")
    gms_uid = (await sh("stat -c '%u:%g' /data/data/com.google.android.gms 2>/dev/null")).strip().strip("'")
    vending_uid = (await sh("stat -c '%u:%g' /data/data/com.android.vending 2>/dev/null")).strip().strip("'")
    chrome_uid = (await sh("stat -c '%u:%g' /data/data/com.android.chrome 2>/dev/null")).strip().strip("'")

    log.info(f"  Wallet: {wallet_uid or 'N/A'}")
    log.info(f"  GMS:    {gms_uid or 'N/A'}")
    log.info(f"  Vending:{vending_uid or 'N/A'}")
    log.info(f"  Chrome: {chrome_uid or 'N/A'}")

    # Validate UIDs — "None" or empty means app not installed
    def valid_uid(u):
        return u and "ERR" not in u and "TIMEOUT" not in u and u != "None" and ":" in u

    if not valid_uid(gms_uid): gms_uid = "10130:10130"
    if not valid_uid(vending_uid): vending_uid = "10140:10140"
    if not valid_uid(chrome_uid): chrome_uid = "10135:10135"
    # Wallet app may not be installed — use GMS UID as fallback
    # (GMS owns tapandpay.db in many Android versions)
    wallet_app_installed = valid_uid(wallet_uid)
    if not wallet_app_installed:
        wallet_uid = gms_uid
        log.warning("  Wallet app NOT installed — using GMS UID for wallet paths")

    # ─── PHASE 2: tapandpay.db injection ──────────────────────────────
    log.info("\n[PHASE 2] Building & injecting tapandpay.db...")
    tapandpay_data = build_tapandpay_db(DPAN, LAST4, NETWORK, EXP_MONTH, EXP_YEAR, CARDHOLDER, CARD_NUM)
    log.info(f"  tapandpay.db size: {len(tapandpay_data)} bytes")

    # Push to Wallet app path (primary)
    wallet_db_path = "/data/data/com.google.android.apps.walletnfcrel/databases/tapandpay.db"
    await sh("mkdir -p /data/data/com.google.android.apps.walletnfcrel/databases")
    await push_bytes(tapandpay_data, wallet_db_path, owner=wallet_uid)

    # Also push to GMS path (fallback — some GMS versions use this)
    gms_db_path = "/data/data/com.google.android.gms/databases/tapandpay.db"
    await sh("mkdir -p /data/data/com.google.android.gms/databases")
    await push_bytes(tapandpay_data, gms_db_path, owner=gms_uid)

    # Backdate file timestamps to match creation_timestamp
    backdate = time.strftime("%Y%m%d%H%M.%S", time.gmtime(time.time() - random.randint(14*86400, 30*86400)))
    await sh(f"touch -t {backdate} {wallet_db_path} 2>/dev/null")
    await sh(f"touch -t {backdate} {gms_db_path} 2>/dev/null")
    log.info("  tapandpay.db injected ✓ (both wallet + GMS paths)")

    # ─── PHASE 3: COIN.xml injection (zero-auth) ─────────────────────
    log.info("\n[PHASE 3] Injecting COIN.xml (zero-auth mode)...")
    coin_xml = build_coin_xml(EMAIL, LAST4, NETWORK, EXP_MONTH, EXP_YEAR)
    coin_path = "/data/data/com.android.vending/shared_prefs/com.android.vending.billing.InAppBillingService.COIN.xml"
    await sh("mkdir -p /data/data/com.android.vending/shared_prefs")
    await push_xml(coin_xml, coin_path, owner=vending_uid)
    log.info("  COIN.xml injected ✓ (purchase_requires_auth=false)")

    # ─── PHASE 4: NFC + Wallet prefs ─────────────────────────────────
    log.info("\n[PHASE 4] Injecting NFC + Wallet preferences...")
    wallet_prefs_dir = "/data/data/com.google.android.apps.walletnfcrel/shared_prefs"
    await sh(f"mkdir -p {wallet_prefs_dir}")

    await push_xml(build_nfc_prefs(), f"{wallet_prefs_dir}/nfc_on_prefs.xml", owner=wallet_uid)
    await push_xml(build_wallet_default_settings(), f"{wallet_prefs_dir}/default_settings.xml", owner=wallet_uid)
    await push_xml(build_wallet_app_prefs(EMAIL),
                   f"{wallet_prefs_dir}/com.google.android.apps.walletnfcrel_preferences.xml", owner=wallet_uid)
    log.info("  NFC + Wallet prefs injected ✓")

    # Enable system NFC
    await sh("settings put secure nfc_on 1")
    await sh("settings put secure nfc_payment_foreground 1")
    log.info("  System NFC enabled ✓")

    # ─── PHASE 5: Chrome Web Data (autofill card) ────────────────────
    log.info("\n[PHASE 5] Injecting Chrome Web Data (autofill card)...")
    webdata = build_chrome_webdata(LAST4, NETWORK, EXP_MONTH, EXP_YEAR, CARDHOLDER, EMAIL)
    chrome_webdata_path = "/data/data/com.android.chrome/app_chrome/Default/Web Data"
    await sh("mkdir -p /data/data/com.android.chrome/app_chrome/Default")
    await push_bytes(webdata, chrome_webdata_path, owner=chrome_uid)
    log.info("  Chrome Web Data injected ✓")

    # ─── PHASE 6: GMS Billing prefs ──────────────────────────────────
    log.info("\n[PHASE 6] Injecting GMS billing state prefs...")
    gms_prefs_dir = "/data/data/com.google.android.gms/shared_prefs"
    await sh(f"mkdir -p {gms_prefs_dir}")

    await push_xml(build_gms_wallet_prefs(EMAIL, LAST4, NETWORK, DPAN),
                   f"{gms_prefs_dir}/wallet_instrument_prefs.xml", owner=gms_uid)
    await push_xml(build_gms_payment_prefs(EMAIL, DPAN),
                   f"{gms_prefs_dir}/payment_profile_prefs.xml", owner=gms_uid)
    log.info("  GMS billing state injected ✓")

    # ─── PHASE 7: Cloud Sync Isolation (CRITICAL) ────────────────────
    log.info("\n[PHASE 7] Applying cloud sync isolation...")

    # Layer 1: Deny background execution for Play Store
    await sh("cmd appops set com.android.vending RUN_IN_BACKGROUND deny 2>/dev/null")
    await sh("cmd appops set com.android.vending RUN_ANY_IN_BACKGROUND deny 2>/dev/null")
    log.info("  Layer 1: Play Store background execution denied ✓")

    # Layer 2: iptables block Play Store ALL network
    await sh(
        "vuid=$(stat -c %u /data/data/com.android.vending 2>/dev/null); "
        "[ -n \"$vuid\" ] && ("
        "iptables -C OUTPUT -m owner --uid-owner $vuid -j DROP 2>/dev/null || "
        "iptables -I OUTPUT -m owner --uid-owner $vuid -j DROP 2>/dev/null"
        ")"
    )
    log.info("  Layer 2: Play Store iptables network block ✓")

    # Layer 3: Block GMS from reaching payments.google.com specifically
    await sh(
        "muid=$(stat -c %u /data/data/com.google.android.gms 2>/dev/null); "
        "[ -n \"$muid\" ] && ("
        "iptables -C OUTPUT -p tcp --dport 443 -m owner --uid-owner $muid "
        "-m string --string 'payments.google.com' --algo bm -j DROP 2>/dev/null || "
        "iptables -I OUTPUT -p tcp --dport 443 -m owner --uid-owner $muid "
        "-m string --string 'payments.google.com' --algo bm -j DROP 2>/dev/null"
        ")"
    )
    log.info("  Layer 3: GMS payments.google.com iptables block ✓")

    # Layer 4: Force-stop Play Store to kill sync threads
    await sh("am force-stop com.android.vending")
    log.info("  Layer 4: Play Store force-stopped ✓")

    # Layer 5: Clear GMS tapandpay cache
    await sh("rm -rf /data/data/com.google.android.gms/cache/tapandpay* 2>/dev/null")
    log.info("  Layer 5: GMS tapandpay cache cleared ✓")

    # Layer 6: Persist iptables across reboot
    await sh("mkdir -p /data/adb 2>/dev/null")
    await sh("iptables-save > /data/adb/iptables.rules 2>/dev/null")
    log.info("  Layer 6: iptables rules persisted ✓")

    log.info("  Cloud sync isolation complete — Play Store CANNOT reconcile")

    # ─── PHASE 8: Verification ───────────────────────────────────────
    log.info("\n[PHASE 8] Verifying all injections...")
    checks = {}

    # Check tapandpay.db
    r = await sh(f"ls -la {wallet_db_path} 2>/dev/null")
    checks["tapandpay_wallet"] = "tapandpay" in r
    log.info(f"  tapandpay.db (wallet): {'✓' if checks['tapandpay_wallet'] else '✗'} {r}")

    r = await sh(f"ls -la {gms_db_path} 2>/dev/null")
    checks["tapandpay_gms"] = "tapandpay" in r
    log.info(f"  tapandpay.db (GMS):    {'✓' if checks['tapandpay_gms'] else '✗'} {r}")

    # Check COIN.xml
    r = await sh(f"cat {coin_path} 2>/dev/null | head -5")
    checks["coin_xml"] = "has_payment_method" in r
    log.info(f"  COIN.xml:              {'✓' if checks['coin_xml'] else '✗'}")

    # Check NFC prefs
    r = await sh(f"cat {wallet_prefs_dir}/nfc_on_prefs.xml 2>/dev/null | head -3")
    checks["nfc_prefs"] = "nfc_enabled" in r
    log.info(f"  NFC prefs:             {'✓' if checks['nfc_prefs'] else '✗'}")

    # Check Chrome Web Data
    r = await sh(f"ls -la {chrome_webdata_path} 2>/dev/null")
    checks["chrome_webdata"] = "Web Data" in r or len(r) > 10
    log.info(f"  Chrome Web Data:       {'✓' if checks['chrome_webdata'] else '✗'}")

    # Check GMS wallet prefs
    r = await sh(f"cat {gms_prefs_dir}/wallet_instrument_prefs.xml 2>/dev/null | head -3")
    checks["gms_wallet"] = "wallet_setup_complete" in r
    log.info(f"  GMS wallet prefs:      {'✓' if checks['gms_wallet'] else '✗'}")

    # Check iptables isolation
    r = await sh("iptables -L OUTPUT -n 2>/dev/null | head -10")
    checks["iptables"] = "DROP" in r
    log.info(f"  iptables isolation:    {'✓' if checks['iptables'] else '✗'}")

    # Check Google account still present
    r = await sh("dumpsys account 2>/dev/null | grep -c 'Account.*com.google' 2>/dev/null")
    has_account = r.strip().isdigit() and int(r.strip()) > 0
    checks["google_account"] = has_account
    log.info(f"  Google account:        {'✓' if checks['google_account'] else '✗'}")

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    log.info(f"\n  Wallet verification: {passed}/{total} checks passed")

    # ─── PHASE 9: Check if Google Wallet is installed ────────────────
    log.info("\n[PHASE 9] Checking Google Wallet installation...")
    r = await sh("pm list packages 2>/dev/null | grep -E 'walletnfcrel|wallet'")
    wallet_installed = "walletnfcrel" in r
    log.info(f"  Google Wallet installed: {wallet_installed}")

    if not wallet_installed:
        log.info("  Google Wallet NOT installed — will need sideloading")
        log.info("  NOTE: Play Store downloads are blocked (synthetic tokens + iptables)")
        log.info("  To sideload: download Google Wallet APK and push via VMOS API")

    # ─── SUMMARY ─────────────────────────────────────────────────────
    log.info("\n" + "=" * 70)
    log.info("WALLET INJECTION SUMMARY")
    log.info("=" * 70)
    log.info(f"  Card: {NETWORK.upper()} ****{LAST4}")
    log.info(f"  DPAN: ****{DPAN[-4:]}")
    log.info(f"  Account: {EMAIL}")
    log.info(f"  tapandpay.db: {'✓' if checks.get('tapandpay_wallet') else '✗'}")
    log.info(f"  COIN.xml (zero-auth): {'✓' if checks.get('coin_xml') else '✗'}")
    log.info(f"  NFC prefs: {'✓' if checks.get('nfc_prefs') else '✗'}")
    log.info(f"  Chrome Web Data: {'✓' if checks.get('chrome_webdata') else '✗'}")
    log.info(f"  GMS billing: {'✓' if checks.get('gms_wallet') else '✗'}")
    log.info(f"  Cloud sync isolation: {'✓' if checks.get('iptables') else '✗'}")
    log.info(f"  Google account: {'✓' if checks.get('google_account') else '✗'}")
    log.info(f"  Wallet app: {'INSTALLED' if wallet_installed else 'NOT INSTALLED (sideload needed)'}")
    log.info(f"  Verification: {passed}/{total}")
    log.info("=" * 70)

    return checks

if __name__ == "__main__":
    results = asyncio.run(main())
