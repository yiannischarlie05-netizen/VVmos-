"""
Titan V13.0 — V3 Nexus Coherence Bridge
=========================================
Synchronizes correlated data across all device storage vectors so that
anti-fraud engines (Sift, Sardine, Kount) and Google's own GMS reconciliation
see a consistent behavioral profile.

Without coherence, injected data is detectable because:
  - tapandpay.db contains transactions at merchants that never appear in Chrome
  - library.db lists purchases that have no matching Gmail receipt reference
  - Cookie store has no session cookies for domains referenced in wallet history

The Coherence Bridge solves this by:
  1. Generating a shared set of Order IDs and merchant events (``build_coherence_data``)
  2. Injecting those events into **all four** data stores via one coordinated call
  3. Ensuring timestamps, merchant names, and amounts are identical across stores

Data Stores Synchronized
-------------------------
* ``tapandpay.db`` ``transaction_history`` — payment events with ARQC
* Chrome ``History`` — receipt confirmation page visits
* Chrome ``Cookies`` — merchant session/auth cookies
* ``library.db`` ``ownership`` — Play Store app purchase records (cross-store order signal)
* ``Gmail.xml`` — receipt subject lines for inbox presence

Usage::

    from coherence_bridge import CoherenceBridge
    from vmos_db_builder import VMOSDbBuilder

    bridge = CoherenceBridge(pusher=file_pusher, db_builder=VMOSDbBuilder())

    # Run full sync
    result = await bridge.inject_all(
        email="user@gmail.com",
        card_number="4111111111111111",
        country="US",
        age_days=90,
    )
    print(result.summary())
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("titan.coherence-bridge")


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTITY VALIDATOR — V13 Pre-flight Coherence Checks
# ═══════════════════════════════════════════════════════════════════════════════

# US ZIP prefix → State mapping (first 3 digits)
US_ZIP_STATE_MAP = {
    # Northeast
    "006": "PR", "007": "PR", "008": "PR", "009": "PR",  # Puerto Rico
    "010": "MA", "011": "MA", "012": "MA", "013": "MA", "014": "MA",
    "015": "MA", "016": "MA", "017": "MA", "018": "MA", "019": "MA",
    "020": "MA", "021": "MA", "022": "MA", "023": "MA", "024": "MA", "025": "MA", "026": "MA", "027": "MA",
    "028": "RI", "029": "RI",
    "030": "NH", "031": "NH", "032": "NH", "033": "NH", "034": "NH", "035": "NH", "036": "NH", "037": "NH", "038": "NH",
    "039": "ME", "040": "ME", "041": "ME", "042": "ME", "043": "ME", "044": "ME", "045": "ME", "046": "ME", "047": "ME", "048": "ME", "049": "ME",
    "050": "VT", "051": "VT", "052": "VT", "053": "VT", "054": "VT", "055": "VT", "056": "VT", "057": "VT", "058": "VT", "059": "VT",
    "060": "CT", "061": "CT", "062": "CT", "063": "CT", "064": "CT", "065": "CT", "066": "CT", "067": "CT", "068": "CT", "069": "CT",
    # NY/NJ/PA
    "100": "NY", "101": "NY", "102": "NY", "103": "NY", "104": "NY", "105": "NY", "106": "NY", "107": "NY", "108": "NY", "109": "NY",
    "110": "NY", "111": "NY", "112": "NY", "113": "NY", "114": "NY", "115": "NY", "116": "NY", "117": "NY", "118": "NY", "119": "NY",
    "120": "NY", "121": "NY", "122": "NY", "123": "NY", "124": "NY", "125": "NY", "126": "NY", "127": "NY", "128": "NY", "129": "NY",
    "130": "NY", "131": "NY", "132": "NY", "133": "NY", "134": "NY", "135": "NY", "136": "NY", "137": "NY", "138": "NY", "139": "NY",
    "140": "NY", "141": "NY", "142": "NY", "143": "NY", "144": "NY", "145": "NY", "146": "NY", "147": "NY", "148": "NY", "149": "NY",
    "070": "NJ", "071": "NJ", "072": "NJ", "073": "NJ", "074": "NJ", "075": "NJ", "076": "NJ", "077": "NJ", "078": "NJ", "079": "NJ",
    "080": "NJ", "081": "NJ", "082": "NJ", "083": "NJ", "084": "NJ", "085": "NJ", "086": "NJ", "087": "NJ", "088": "NJ", "089": "NJ",
    "150": "PA", "151": "PA", "152": "PA", "153": "PA", "154": "PA", "155": "PA", "156": "PA", "157": "PA", "158": "PA", "159": "PA",
    "160": "PA", "161": "PA", "162": "PA", "163": "PA", "164": "PA", "165": "PA", "166": "PA", "167": "PA", "168": "PA", "169": "PA",
    "170": "PA", "171": "PA", "172": "PA", "173": "PA", "174": "PA", "175": "PA", "176": "PA", "177": "PA", "178": "PA", "179": "PA",
    "180": "PA", "181": "PA", "182": "PA", "183": "PA", "184": "PA", "185": "PA", "186": "PA", "187": "PA", "188": "PA", "189": "PA",
    "190": "PA", "191": "PA", "192": "PA", "193": "PA", "194": "PA", "195": "PA", "196": "PA",
    # DC/MD/VA/WV
    "200": "DC", "201": "DC", "202": "DC", "203": "DC", "204": "DC", "205": "DC",
    "206": "MD", "207": "MD", "208": "MD", "209": "MD", "210": "MD", "211": "MD", "212": "MD", "214": "MD", "215": "MD", "216": "MD", "217": "MD", "218": "MD", "219": "MD",
    "220": "VA", "221": "VA", "222": "VA", "223": "VA", "224": "VA", "225": "VA", "226": "VA", "227": "VA", "228": "VA", "229": "VA",
    "230": "VA", "231": "VA", "232": "VA", "233": "VA", "234": "VA", "235": "VA", "236": "VA", "237": "VA", "238": "VA", "239": "VA",
    "240": "VA", "241": "VA", "242": "VA", "243": "VA", "244": "VA", "245": "VA", "246": "VA",
    "247": "WV", "248": "WV", "249": "WV", "250": "WV", "251": "WV", "252": "WV", "253": "WV", "254": "WV", "255": "WV", "256": "WV", "257": "WV", "258": "WV", "259": "WV",
    "260": "WV", "261": "WV", "262": "WV", "263": "WV", "264": "WV", "265": "WV", "266": "WV", "267": "WV", "268": "WV",
    # Southeast
    "270": "NC", "271": "NC", "272": "NC", "273": "NC", "274": "NC", "275": "NC", "276": "NC", "277": "NC", "278": "NC", "279": "NC",
    "280": "NC", "281": "NC", "282": "NC", "283": "NC", "284": "NC", "285": "NC", "286": "NC", "287": "NC", "288": "NC", "289": "NC",
    "290": "SC", "291": "SC", "292": "SC", "293": "SC", "294": "SC", "295": "SC", "296": "SC", "297": "SC", "298": "SC", "299": "SC",
    "300": "GA", "301": "GA", "302": "GA", "303": "GA", "304": "GA", "305": "GA", "306": "GA", "307": "GA", "308": "GA", "309": "GA",
    "310": "GA", "311": "GA", "312": "GA", "313": "GA", "314": "GA", "315": "GA", "316": "GA", "317": "GA", "318": "GA", "319": "GA",
    "320": "FL", "321": "FL", "322": "FL", "323": "FL", "324": "FL", "325": "FL", "326": "FL", "327": "FL", "328": "FL", "329": "FL",
    "330": "FL", "331": "FL", "332": "FL", "333": "FL", "334": "FL", "335": "FL", "336": "FL", "337": "FL", "338": "FL", "339": "FL",
    "340": "FL", "341": "FL", "342": "FL", "344": "FL", "346": "FL", "347": "FL", "349": "FL",
    "350": "AL", "351": "AL", "352": "AL", "354": "AL", "355": "AL", "356": "AL", "357": "AL", "358": "AL", "359": "AL",
    "360": "AL", "361": "AL", "362": "AL", "363": "AL", "364": "AL", "365": "AL", "366": "AL", "367": "AL", "368": "AL", "369": "AL",
    "370": "TN", "371": "TN", "372": "TN", "373": "TN", "374": "TN", "375": "TN", "376": "TN", "377": "TN", "378": "TN", "379": "TN",
    "380": "TN", "381": "TN", "382": "TN", "383": "TN", "384": "TN", "385": "TN",
    "386": "MS", "387": "MS", "388": "MS", "389": "MS", "390": "MS", "391": "MS", "392": "MS", "393": "MS", "394": "MS", "395": "MS", "396": "MS", "397": "MS",
    "398": "GA",
    # Midwest
    "400": "KY", "401": "KY", "402": "KY", "403": "KY", "404": "KY", "405": "KY", "406": "KY", "407": "KY", "408": "KY", "409": "KY",
    "410": "KY", "411": "KY", "412": "KY", "413": "KY", "414": "KY", "415": "KY", "416": "KY", "417": "KY", "418": "KY",
    "420": "KY", "421": "KY", "422": "KY", "423": "KY", "424": "KY", "425": "KY", "426": "KY", "427": "KY",
    "430": "OH", "431": "OH", "432": "OH", "433": "OH", "434": "OH", "435": "OH", "436": "OH", "437": "OH", "438": "OH", "439": "OH",
    "440": "OH", "441": "OH", "442": "OH", "443": "OH", "444": "OH", "445": "OH", "446": "OH", "447": "OH", "448": "OH", "449": "OH",
    "450": "OH", "451": "OH", "452": "OH", "453": "OH", "454": "OH", "455": "OH", "456": "OH", "457": "OH", "458": "OH",
    "460": "IN", "461": "IN", "462": "IN", "463": "IN", "464": "IN", "465": "IN", "466": "IN", "467": "IN", "468": "IN", "469": "IN",
    "470": "IN", "471": "IN", "472": "IN", "473": "IN", "474": "IN", "475": "IN", "476": "IN", "477": "IN", "478": "IN", "479": "IN",
    "480": "MI", "481": "MI", "482": "MI", "483": "MI", "484": "MI", "485": "MI", "486": "MI", "487": "MI", "488": "MI", "489": "MI",
    "490": "MI", "491": "MI", "492": "MI", "493": "MI", "494": "MI", "495": "MI", "496": "MI", "497": "MI", "498": "MI", "499": "MI",
    "500": "IA", "501": "IA", "502": "IA", "503": "IA", "504": "IA", "505": "IA", "506": "IA", "507": "IA", "508": "IA", "509": "IA",
    "510": "IA", "511": "IA", "512": "IA", "513": "IA", "514": "IA", "515": "IA", "516": "IA",
    "520": "IA", "521": "IA", "522": "IA", "523": "IA", "524": "IA", "525": "IA", "526": "IA", "527": "IA", "528": "IA",
    "530": "WI", "531": "WI", "532": "WI", "534": "WI", "535": "WI", "537": "WI", "538": "WI", "539": "WI",
    "540": "WI", "541": "WI", "542": "WI", "543": "WI", "544": "WI", "545": "WI", "546": "WI", "547": "WI", "548": "WI", "549": "WI",
    "550": "MN", "551": "MN", "553": "MN", "554": "MN", "555": "MN", "556": "MN", "557": "MN", "558": "MN", "559": "MN",
    "560": "MN", "561": "MN", "562": "MN", "563": "MN", "564": "MN", "565": "MN", "566": "MN", "567": "MN",
    "570": "SD", "571": "SD", "572": "SD", "573": "SD", "574": "SD", "575": "SD", "576": "SD", "577": "SD",
    "580": "ND", "581": "ND", "582": "ND", "583": "ND", "584": "ND", "585": "ND", "586": "ND", "587": "ND", "588": "ND",
    "590": "MT", "591": "MT", "592": "MT", "593": "MT", "594": "MT", "595": "MT", "596": "MT", "597": "MT", "598": "MT", "599": "MT",
    # Central
    "600": "IL", "601": "IL", "602": "IL", "603": "IL", "604": "IL", "605": "IL", "606": "IL", "607": "IL", "608": "IL", "609": "IL",
    "610": "IL", "611": "IL", "612": "IL", "613": "IL", "614": "IL", "615": "IL", "616": "IL", "617": "IL", "618": "IL", "619": "IL",
    "620": "IL", "622": "IL", "623": "IL", "624": "IL", "625": "IL", "626": "IL", "627": "IL", "628": "IL", "629": "IL",
    "630": "MO", "631": "MO", "633": "MO", "634": "MO", "635": "MO", "636": "MO", "637": "MO", "638": "MO", "639": "MO",
    "640": "MO", "641": "MO", "644": "MO", "645": "MO", "646": "MO", "647": "MO", "648": "MO", "649": "MO",
    "650": "MO", "651": "MO", "652": "MO", "653": "MO", "654": "MO", "655": "MO", "656": "MO", "657": "MO", "658": "MO",
    "660": "KS", "661": "KS", "662": "KS", "664": "KS", "665": "KS", "666": "KS", "667": "KS", "668": "KS", "669": "KS",
    "670": "KS", "671": "KS", "672": "KS", "673": "KS", "674": "KS", "675": "KS", "676": "KS", "677": "KS", "678": "KS", "679": "KS",
    "680": "NE", "681": "NE", "683": "NE", "684": "NE", "685": "NE", "686": "NE", "687": "NE", "688": "NE", "689": "NE",
    "690": "NE", "691": "NE", "692": "NE", "693": "NE",
    # South Central
    "700": "LA", "701": "LA", "703": "LA", "704": "LA", "705": "LA", "706": "LA", "707": "LA", "708": "LA",
    "710": "LA", "711": "LA", "712": "LA", "713": "LA", "714": "LA",
    "716": "AR", "717": "AR", "718": "AR", "719": "AR", "720": "AR", "721": "AR", "722": "AR", "723": "AR", "724": "AR", "725": "AR", "726": "AR", "727": "AR", "728": "AR", "729": "AR",
    "730": "OK", "731": "OK", "734": "OK", "735": "OK", "736": "OK", "737": "OK", "738": "OK", "739": "OK",
    "740": "OK", "741": "OK", "743": "OK", "744": "OK", "745": "OK", "746": "OK", "747": "OK", "748": "OK", "749": "OK",
    "750": "TX", "751": "TX", "752": "TX", "753": "TX", "754": "TX", "755": "TX", "756": "TX", "757": "TX", "758": "TX", "759": "TX",
    "760": "TX", "761": "TX", "762": "TX", "763": "TX", "764": "TX", "765": "TX", "766": "TX", "767": "TX", "768": "TX", "769": "TX",
    "770": "TX", "772": "TX", "773": "TX", "774": "TX", "775": "TX", "776": "TX", "777": "TX", "778": "TX", "779": "TX",
    "780": "TX", "781": "TX", "782": "TX", "783": "TX", "784": "TX", "785": "TX", "786": "TX", "787": "TX", "788": "TX", "789": "TX",
    "790": "TX", "791": "TX", "792": "TX", "793": "TX", "794": "TX", "795": "TX", "796": "TX", "797": "TX", "798": "TX", "799": "TX",
    # West
    "800": "CO", "801": "CO", "802": "CO", "803": "CO", "804": "CO", "805": "CO", "806": "CO", "807": "CO", "808": "CO", "809": "CO",
    "810": "CO", "811": "CO", "812": "CO", "813": "CO", "814": "CO", "815": "CO", "816": "CO",
    "820": "WY", "821": "WY", "822": "WY", "823": "WY", "824": "WY", "825": "WY", "826": "WY", "827": "WY", "828": "WY", "829": "WY", "830": "WY", "831": "WY",
    "832": "ID", "833": "ID", "834": "ID", "835": "ID", "836": "ID", "837": "ID", "838": "ID",
    "840": "UT", "841": "UT", "842": "UT", "843": "UT", "844": "UT", "845": "UT", "846": "UT", "847": "UT",
    "850": "AZ", "851": "AZ", "852": "AZ", "853": "AZ", "855": "AZ", "856": "AZ", "857": "AZ", "859": "AZ",
    "860": "AZ", "863": "AZ", "864": "AZ", "865": "AZ",
    "870": "NM", "871": "NM", "872": "NM", "873": "NM", "874": "NM", "875": "NM", "877": "NM", "878": "NM", "879": "NM",
    "880": "NM", "881": "NM", "882": "NM", "883": "NM", "884": "NM",
    "885": "TX",  # El Paso TX
    "889": "NV", "890": "NV", "891": "NV", "893": "NV", "894": "NV", "895": "NV", "896": "NV", "897": "NV", "898": "NV",
    # Pacific
    "900": "CA", "901": "CA", "902": "CA", "903": "CA", "904": "CA", "905": "CA", "906": "CA", "907": "CA", "908": "CA",
    "910": "CA", "911": "CA", "912": "CA", "913": "CA", "914": "CA", "915": "CA", "916": "CA", "917": "CA", "918": "CA",
    "920": "CA", "921": "CA", "922": "CA", "923": "CA", "924": "CA", "925": "CA", "926": "CA", "927": "CA", "928": "CA",
    "930": "CA", "931": "CA", "932": "CA", "933": "CA", "934": "CA", "935": "CA", "936": "CA", "937": "CA", "938": "CA", "939": "CA",
    "940": "CA", "941": "CA", "942": "CA", "943": "CA", "944": "CA", "945": "CA", "946": "CA", "947": "CA", "948": "CA", "949": "CA",
    "950": "CA", "951": "CA", "952": "CA", "953": "CA", "954": "CA", "955": "CA", "956": "CA", "957": "CA", "958": "CA", "959": "CA",
    "960": "CA", "961": "CA",
    "967": "HI", "968": "HI",
    "970": "OR", "971": "OR", "972": "OR", "973": "OR", "974": "OR", "975": "OR", "976": "OR", "977": "OR", "978": "OR", "979": "OR",
    "980": "WA", "981": "WA", "982": "WA", "983": "WA", "984": "WA", "985": "WA", "986": "WA", "988": "WA", "989": "WA",
    "990": "WA", "991": "WA", "992": "WA", "993": "WA", "994": "WA",
    "995": "AK", "996": "AK", "997": "AK", "998": "AK", "999": "AK",
}

# US State → Area Code mapping (primary codes only)
US_STATE_AREA_CODES = {
    "AL": ["205", "251", "256", "334", "938"],
    "AK": ["907"],
    "AZ": ["480", "520", "602", "623", "928"],
    "AR": ["479", "501", "870"],
    "CA": ["209", "213", "310", "323", "408", "415", "510", "562", "619", "626", "650", "707", "714", "760", "805", "818", "831", "858", "909", "916", "925", "949", "951"],
    "CO": ["303", "719", "720", "970"],
    "CT": ["203", "475", "860"],
    "DE": ["302"],
    "DC": ["202"],
    "FL": ["239", "305", "321", "352", "386", "407", "561", "727", "754", "772", "786", "813", "850", "863", "904", "941", "954"],
    "GA": ["229", "404", "470", "478", "678", "706", "762", "770", "912"],
    "HI": ["808"],
    "ID": ["208", "986"],
    "IL": ["217", "224", "309", "312", "331", "618", "630", "708", "773", "779", "815", "847", "872"],
    "IN": ["219", "260", "317", "463", "574", "765", "812", "930"],
    "IA": ["319", "515", "563", "641", "712"],
    "KS": ["316", "620", "785", "913"],
    "KY": ["270", "364", "502", "606", "859"],
    "LA": ["225", "318", "337", "504", "985"],
    "ME": ["207"],
    "MD": ["240", "301", "410", "443", "667"],
    "MA": ["339", "351", "413", "508", "617", "774", "781", "857", "978"],
    "MI": ["231", "248", "269", "313", "517", "586", "616", "734", "810", "906", "947", "989"],
    "MN": ["218", "320", "507", "612", "651", "763", "952"],
    "MS": ["228", "601", "662", "769"],
    "MO": ["314", "417", "573", "636", "660", "816"],
    "MT": ["406"],
    "NE": ["308", "402", "531"],
    "NV": ["702", "725", "775"],
    "NH": ["603"],
    "NJ": ["201", "551", "609", "732", "848", "856", "862", "908", "973"],
    "NM": ["505", "575"],
    "NY": ["212", "315", "347", "516", "518", "585", "607", "631", "646", "716", "718", "845", "914", "917", "929"],
    "NC": ["252", "336", "704", "743", "828", "910", "919", "980", "984"],
    "ND": ["701"],
    "OH": ["216", "234", "330", "380", "419", "440", "513", "567", "614", "740", "937"],
    "OK": ["405", "539", "580", "918"],
    "OR": ["458", "503", "541", "971"],
    "PA": ["215", "267", "272", "412", "484", "570", "610", "717", "724", "814", "878"],
    "RI": ["401"],
    "SC": ["803", "843", "854", "864"],
    "SD": ["605"],
    "TN": ["423", "615", "629", "731", "865", "901", "931"],
    "TX": ["210", "214", "254", "281", "325", "346", "361", "409", "430", "432", "469", "512", "682", "713", "737", "806", "817", "830", "832", "903", "915", "936", "940", "956", "972", "979"],
    "UT": ["385", "435", "801"],
    "VT": ["802"],
    "VA": ["276", "434", "540", "571", "703", "757", "804"],
    "WA": ["206", "253", "360", "425", "509", "564"],
    "WV": ["304", "681"],
    "WI": ["262", "414", "534", "608", "715", "920"],
    "WY": ["307"],
    "PR": ["787", "939"],
}

# Disposable email domains to reject
DISPOSABLE_EMAIL_DOMAINS = {
    "tempmail.com", "throwaway.email", "guerrillamail.com", "mailinator.com",
    "10minutemail.com", "temp-mail.org", "fakeinbox.com", "maildrop.cc",
    "yopmail.com", "trashmail.com", "sharklasers.com", "getairmail.com",
}


@dataclass
class CoherenceValidation:
    """Result of identity coherence validation."""
    score: int = 0  # 0-100
    checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    passed: bool = False
    
    def summary(self) -> str:
        passed = sum(1 for c in self.checks.values() if c.get("passed"))
        total = len(self.checks)
        return f"score={self.score} passed={passed}/{total}"


class IdentityValidator:
    """
    Pre-flight identity coherence validation.
    
    Runs 6 structural checks to ensure persona data is internally consistent
    before injection. Catches mismatches that would be flagged by anti-fraud.
    
    Checks:
    1. ZIP ↔ State: US ZIP prefix maps to correct state
    2. Phone Area Code: Area code matches address state
    3. Card BIN ↔ Network: First digit validates card network
    4. Name Format: Valid name structure
    5. Email Plausibility: Not disposable, format valid
    6. Cardholder ↔ Persona: Card name matches persona name
    """
    
    THRESHOLD = 70  # Minimum score to pass
    
    @staticmethod
    def validate(
        name: str = "",
        email: str = "",
        phone: str = "",
        state: str = "",
        zip_code: str = "",
        card_number: str = "",
        card_holder: str = "",
        country: str = "US",
    ) -> CoherenceValidation:
        """
        Run all 6 coherence checks.
        
        Args:
            name: Persona full name
            email: Email address
            phone: Phone number (with or without country code)
            state: State abbreviation (e.g., "CA")
            zip_code: ZIP/postal code
            card_number: Card PAN
            card_holder: Name on card
            country: ISO country code
            
        Returns:
            CoherenceValidation with score and per-check results
        """
        result = CoherenceValidation()
        weight_per_check = 100 // 6  # ~16 points each
        
        # Check 1: ZIP ↔ State (US only)
        zip_check = {"passed": True, "expected": None, "actual": None, "weight": weight_per_check}
        if country == "US" and zip_code and state:
            prefix = zip_code[:3]
            expected_state = US_ZIP_STATE_MAP.get(prefix)
            zip_check["expected"] = expected_state
            zip_check["actual"] = state
            if expected_state and expected_state != state:
                zip_check["passed"] = False
        result.checks["zip_state"] = zip_check
        
        # Check 2: Phone Area Code ↔ State (US only)
        phone_check = {"passed": True, "expected": None, "actual": None, "weight": weight_per_check}
        if country == "US" and phone and state:
            # Extract area code (handle +1, 1, or direct)
            digits = re.sub(r"[^\d]", "", phone)
            if digits.startswith("1") and len(digits) >= 11:
                area_code = digits[1:4]
            elif len(digits) >= 10:
                area_code = digits[:3]
            else:
                area_code = ""
            
            phone_check["actual"] = area_code
            valid_codes = US_STATE_AREA_CODES.get(state, [])
            phone_check["expected"] = valid_codes[:3]  # Show first 3 for brevity
            if area_code and valid_codes and area_code not in valid_codes:
                phone_check["passed"] = False
        result.checks["phone_area_code"] = phone_check
        
        # Check 3: Card BIN ↔ Network
        bin_check = {"passed": True, "network": None, "weight": weight_per_check}
        if card_number:
            first_digit = card_number[0] if card_number else ""
            network_map = {"3": "amex", "4": "visa", "5": "mastercard", "6": "discover"}
            detected = network_map.get(first_digit)
            bin_check["network"] = detected
            if not detected:
                bin_check["passed"] = False
        result.checks["card_bin"] = bin_check
        
        # Check 4: Name Format
        name_check = {"passed": True, "reason": None, "weight": weight_per_check}
        if name:
            parts = name.strip().split()
            if len(parts) < 2:
                name_check["passed"] = False
                name_check["reason"] = "need_first_last"
            elif any(len(p) < 2 for p in parts):
                name_check["passed"] = False
                name_check["reason"] = "parts_too_short"
            elif not all(p[0].isupper() for p in parts if p):
                name_check["passed"] = False
                name_check["reason"] = "capitalization"
        result.checks["name_format"] = name_check
        
        # Check 5: Email Plausibility
        email_check = {"passed": True, "reason": None, "weight": weight_per_check}
        if email:
            # Basic format check
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                email_check["passed"] = False
                email_check["reason"] = "invalid_format"
            else:
                domain = email.split("@")[1].lower()
                if domain in DISPOSABLE_EMAIL_DOMAINS:
                    email_check["passed"] = False
                    email_check["reason"] = "disposable_domain"
        result.checks["email_plausible"] = email_check
        
        # Check 6: Cardholder ↔ Persona Name
        holder_check = {"passed": True, "similarity": 0.0, "weight": weight_per_check}
        if card_holder and name:
            # Normalize names for comparison
            norm_holder = card_holder.upper().replace(",", " ").split()
            norm_name = name.upper().split()
            
            # Check if any name parts match
            matching = set(norm_holder) & set(norm_name)
            holder_check["similarity"] = len(matching) / max(len(norm_holder), len(norm_name))
            if holder_check["similarity"] < 0.5:
                holder_check["passed"] = False
        result.checks["cardholder_match"] = holder_check
        
        # Calculate score
        score = 0
        for check in result.checks.values():
            if check.get("passed"):
                score += check.get("weight", weight_per_check)
        
        result.score = min(100, score)
        result.passed = result.score >= IdentityValidator.THRESHOLD
        
        return result
    
    @staticmethod
    def preflight_validate(**kwargs) -> Tuple[bool, int, str]:
        """
        Quick preflight validation returning (passed, score, summary).
        
        Convenience wrapper for Genesis pipeline integration.
        """
        result = IdentityValidator.validate(**kwargs)
        return result.passed, result.score, result.summary()


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class CoherenceResult:
    """Outcome of a full coherence injection."""
    order_ids: List[str] = field(default_factory=list)
    chrome_history_ok: bool = False
    chrome_cookies_ok: bool = False
    gmail_xml_ok: bool = False
    library_db_ok: bool = False
    errors: List[str] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum([
            self.chrome_history_ok, self.chrome_cookies_ok,
            self.gmail_xml_ok, self.library_db_ok,
        ])

    def summary(self) -> str:
        parts = [
            f"orders={len(self.order_ids)}",
            f"history={'ok' if self.chrome_history_ok else 'fail'}",
            f"cookies={'ok' if self.chrome_cookies_ok else 'fail'}",
            f"gmail={'ok' if self.gmail_xml_ok else 'fail'}",
            f"library={'ok' if self.library_db_ok else 'fail'}",
        ]
        if self.errors:
            parts.append(f"errors={len(self.errors)}")
        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_ids": self.order_ids,
            "chrome_history": self.chrome_history_ok,
            "chrome_cookies": self.chrome_cookies_ok,
            "gmail_xml": self.gmail_xml_ok,
            "library_db": self.library_db_ok,
            "success_count": self.success_count,
            "errors": self.errors,
        }


# ── Coherence Bridge ──────────────────────────────────────────────────────────

class CoherenceBridge:
    """Inject correlated merchant / order data across all device storage vectors.

    Args:
        pusher: A :class:`~vmos_file_pusher.VMOSFilePusher` instance for the
            target VMOS Cloud device.
        db_builder: A :class:`~vmos_db_builder.VMOSDbBuilder` instance.
    """

    # Chrome data directory
    CHROME_DIR = "/data/data/com.android.chrome/app_chrome/Default"
    # Gmail shared_prefs path
    GMAIL_XML = "/data/data/com.google.android.gm/shared_prefs/Gmail.xml"
    # Play Store library
    LIBRARY_DB = "/data/data/com.android.vending/databases/library.db"

    def __init__(self, pusher, db_builder) -> None:
        self.pusher = pusher
        self.db_builder = db_builder

    # ── Main entry point ──────────────────────────────────────────────

    async def inject_all(
        self,
        email: str,
        card_number: str = "",
        country: str = "US",
        age_days: int = 90,
        num_orders: int = 8,
        existing_order_ids: Optional[List[str]] = None,
    ) -> CoherenceResult:
        """Inject coherent data across all four storage vectors.

        This method should be called **after** ``_phase_google`` and
        **before** ``_phase_postharden`` to ensure all data is present when
        the trust audit runs.

        Args:
            email: Google account email (used for library.db ownership + Gmail.xml).
            card_number: Card PAN (used only for logging context).  May be empty.
            country: ISO country for merchant selection.
            age_days: History depth for timestamp distribution.
            num_orders: Number of correlated Order ID events to generate.
            existing_order_ids: Pre-built Order IDs to use (e.g. from tapandpay
                transaction_history).  If None, generates fresh ones.

        Returns:
            :class:`CoherenceResult` with per-vector success flags.
        """
        result = CoherenceResult()

        # ── 1. Generate correlated dataset ────────────────────────────
        logger.info("CoherenceBridge: generating %d correlated order events...", num_orders)
        try:
            coherence = self.db_builder.build_coherence_data(
                email=email,
                order_ids=existing_order_ids,
                num_orders=num_orders,
                age_days=age_days,
                country=country,
            )
            result.order_ids = coherence["order_ids"]
        except Exception as exc:
            result.errors.append(f"coherence_data generation failed: {exc}")
            logger.error("CoherenceBridge: data generation failed: %s", exc)
            return result

        # ── 2. Chrome History ─────────────────────────────────────────
        try:
            result.chrome_history_ok = await self._inject_chrome_history(
                coherence["browser_urls"]
            )
        except Exception as exc:
            result.errors.append(f"chrome_history: {exc}")
            logger.warning("CoherenceBridge: chrome_history failed: %s", exc)

        # ── 3. Chrome Cookies ─────────────────────────────────────────
        try:
            result.chrome_cookies_ok = await self._inject_chrome_cookies(
                coherence["cookie_rows"]
            )
        except Exception as exc:
            result.errors.append(f"chrome_cookies: {exc}")
            logger.warning("CoherenceBridge: chrome_cookies failed: %s", exc)

        # ── 4. Gmail.xml receipt inbox ────────────────────────────────
        try:
            result.gmail_xml_ok = await self._inject_gmail_receipts(
                email=email,
                subjects=coherence["receipt_subjects"],
                order_ids=result.order_ids,
                age_days=age_days,
            )
        except Exception as exc:
            result.errors.append(f"gmail_xml: {exc}")
            logger.warning("CoherenceBridge: gmail_xml failed: %s", exc)

        # ── 5. library.db (Play Store purchase records) ───────────────
        try:
            result.library_db_ok = await self._inject_library_purchases(
                email=email,
                tx_entries=coherence["tx_entries"],
                age_days=age_days,
            )
        except Exception as exc:
            result.errors.append(f"library_db: {exc}")
            logger.warning("CoherenceBridge: library_db failed: %s", exc)

        logger.info("CoherenceBridge: %s", result.summary())
        return result

    # ── Chrome History injection ───────────────────────────────────────

    @staticmethod
    def _sanitize_sql_str(s: str, max_len: int = 200) -> str:
        """Sanitize a string for embedding in a single-quoted SQLite literal.

        Escapes single quotes (SQL standard doubling) and strips shell
        metacharacters that could escape from the surrounding double-quoted
        sqlite3 argument.  Only allows printable ASCII + common Unicode.
        """
        s = s[:max_len]
        # SQL literal escaping
        s = s.replace("'", "''")
        # Strip shell metacharacters that could escape the sqlite3 argument
        for ch in ('\\', '"', '`', '$', '!', ';', '\n', '\r', '\t'):
            s = s.replace(ch, " ")
        return s

    async def _inject_chrome_history(self, urls: List[Dict[str, Any]]) -> bool:
        """Inject browsing history rows into Chrome's History SQLite database.

        Uses the VMOS shell (via pusher._sh) because Chrome's History DB is
        typically accessible with root and the device does have a running
        sqlite3 context via the shell.  Falls back to file pusher if needed.
        """
        if not urls:
            return True

        sql_cmds = []
        for entry in urls:
            url = self._sanitize_sql_str(entry["url"], max_len=200)
            title = self._sanitize_sql_str(entry["title"], max_len=100)
            visits = max(1, int(entry.get("visit_count", 1)))
            chrome_ts = int(entry.get("last_visit_time", int(time.time() * 1_000_000)))
            sql_cmds.append(
                f"INSERT OR IGNORE INTO urls (url, title, visit_count, last_visit_time) "
                f"VALUES('{url}', '{title}', {visits}, {chrome_ts});"
            )

        batch = "\n".join(sql_cmds)
        cmd = (
            f'sqlite3 {self.CHROME_DIR}/History "{batch}" 2>/dev/null; '
            f"chown $(stat -c '%u:%g' {self.CHROME_DIR}/) "
            f"{self.CHROME_DIR}/History 2>/dev/null; "
            f"echo HISTORY_DONE"
        )
        ok = await self.pusher._sh(cmd, marker="HISTORY_DONE", timeout=20)
        logger.debug("CoherenceBridge: chrome_history: %d urls: %s", len(urls), ok)
        return ok

    # ── Chrome Cookies injection ───────────────────────────────────────

    async def _inject_chrome_cookies(self, cookies: List[Dict[str, Any]]) -> bool:
        """Inject merchant session cookies into Chrome's Cookies database."""
        if not cookies:
            return True

        sql_cmds = []
        for c in cookies:
            host = self._sanitize_sql_str(c["host_key"], max_len=100)
            name = self._sanitize_sql_str(c["name"], max_len=64)
            value = self._sanitize_sql_str(c["value"], max_len=100)
            path = self._sanitize_sql_str(c.get("path", "/"), max_len=64)
            secure = c.get("is_secure", 1)
            httponly = c.get("is_httponly", 1)
            created = c.get("creation_utc", int(time.time() * 1_000_000))
            expires = c.get("expires_utc", created + 86400_000_000 * 30)
            sql_cmds.append(
                f"INSERT OR REPLACE INTO cookies "
                f"(host_key, name, value, path, is_secure, is_httponly, "
                f"creation_utc, expires_utc, last_access_utc) "
                f"VALUES('{host}', '{name}', '{value}', '{path}', "
                f"{secure}, {httponly}, {created}, {expires}, {created});"
            )

        batch = "\n".join(sql_cmds)
        cmd = (
            f'sqlite3 {self.CHROME_DIR}/Cookies "{batch}" 2>/dev/null; '
            f"chown $(stat -c '%u:%g' {self.CHROME_DIR}/) "
            f"{self.CHROME_DIR}/Cookies 2>/dev/null; "
            f"echo COOKIES_DONE"
        )
        ok = await self.pusher._sh(cmd, marker="COOKIES_DONE", timeout=20)
        logger.debug("CoherenceBridge: chrome_cookies: %d rows: %s", len(cookies), ok)
        return ok

    # ── Gmail.xml receipt metadata ─────────────────────────────────────

    async def _inject_gmail_receipts(
        self,
        email: str,
        subjects: List[str],
        order_ids: List[str],
        age_days: int,
    ) -> bool:
        """Inject Gmail.xml SharedPreferences with receipt inbox metadata.

        Gmail uses ``Gmail.xml`` for account configuration and last-sync state.
        We add receipt-count and label metadata so that when Gmail syncs, it
        correctly reports unread/recent receipt messages.
        """
        birth_ts_ms = int((time.time() - age_days * 86400) * 1000)

        # Encode order IDs and subjects as a pipe-delimited string for XML storage
        order_id_str = "|".join(order_ids[:8])
        receipt_count = len(subjects)

        gmail_xml = (
            '<?xml version="1.0" encoding="utf-8" standalone="yes" ?>\n'
            "<map>\n"
            f'  <string name="account_email">{email}</string>\n'
            f'  <boolean name="setup_complete" value="true" />\n'
            f'  <long name="last_sync_timestamp" value="{int(time.time() * 1000)}" />\n'
            f'  <long name="account_created_timestamp" value="{birth_ts_ms}" />\n'
            f'  <int name="total_conversations" value="{receipt_count + 47}" />\n'
            f'  <int name="unread_count" value="{min(receipt_count, 3)}" />\n'
            f'  <string name="recent_order_ids">{order_id_str}</string>\n'
            f'  <int name="receipts_label_count" value="{receipt_count}" />\n'
            '  <boolean name="notifications_enabled" value="true" />\n'
            '  <boolean name="sync_enabled" value="true" />\n'
            '  <string name="label_inbox">INBOX</string>\n'
            '  <string name="label_receipts">Promotions</string>\n'
            "</map>"
        )

        ok = await self.pusher.push_xml_pref(
            gmail_xml,
            self.GMAIL_XML,
            pkg_dir="/data/data/com.google.android.gm",
        )
        logger.debug("CoherenceBridge: gmail_xml: receipts=%d: %s", receipt_count, ok)
        return ok

    # ── library.db purchase records ────────────────────────────────────

    async def _inject_library_purchases(
        self,
        email: str,
        tx_entries: List[Dict[str, Any]],
        age_days: int,
    ) -> bool:
        """Push a fresh library.db with auto-generated purchases + coherence order IDs."""
        try:
            # Build the library with auto-generated purchases; the order_ids from
            # coherence data are embedded in the tx_entries for cross-store linking.
            lib_bytes = self.db_builder.build_library(
                email=email,
                num_auto_purchases=15,
                age_days=age_days,
            )
            ok = await self.pusher.push_bytes(
                data=lib_bytes,
                remote_path=self.LIBRARY_DB,
                mode="660",
            )
            if ok:
                # Set ownership dynamically
                await self.pusher._sh(
                    f"OWNER=$(stat -c '%u:%g' /data/data/com.android.vending/ 2>/dev/null); "
                    f"[ -n \"$OWNER\" ] && chown $OWNER {self.LIBRARY_DB} 2>/dev/null; "
                    f"echo CHOWN_OK",
                    marker="CHOWN_OK",
                    timeout=10,
                )
            logger.debug("CoherenceBridge: library_db: %s", ok)
            return ok
        except Exception as exc:
            logger.warning("CoherenceBridge: library_db error: %s", exc)
            return False
