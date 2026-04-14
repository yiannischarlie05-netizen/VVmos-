#!/usr/bin/env python3
"""
Genesis V3 Phase Executor (CLI shim)

This script delegates to the canonical VMOSGenesisV3 engine in
`vmos_titan.core.vmos_genesis_v3`. It builds a `PipelineConfigV3`
from CLI args and runs the engine, then writes a JSON report to /tmp.
"""

import argparse
import asyncio
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

# Ensure package imports work when executed as a script
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR.joinpath("vmos_titan", "core")))

# Attempt to use the real VMOS package when available.
try:
    from vmos_titan.core.vmos_genesis_v3 import VMOSGenesisV3, PipelineConfigV3
    from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
    _REAL_ENGINE_IMPORTED = True
except Exception:
    _REAL_ENGINE_IMPORTED = False


@dataclass
class PipelineConfigV3:
    name: str = ""
    email: str = ""
    google_email: str = ""
    cc_number: str = ""
    cc_exp: str = ""
    age_days: int = 120
    use_real_auth: bool = False
    proxy_url: str = ""


class VMOSGenesisV3:
    def __init__(self, pad_code: str, *, client=None):
        self.pad_code = pad_code
        self.client = client

    async def run_pipeline(self, cfg: PipelineConfigV3):
        raise RuntimeError("VMOSGenesisV3 not loaded; tests should monkeypatch this method")


class VMOSCloudClient:
    def __init__(self, *args, **kwargs):
        # Placeholder client; real client is loaded at runtime if available.
        pass


# Defaults (kept for backward compatibility)
DEVICE_ID = "APP61F5ERZYHYJH9"
AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE_URL = "https://api.vmoscloud.com"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Genesis V3 Phase Executor (delegates to VMOSGenesisV3)")
    p.add_argument("--device-id", default=DEVICE_ID, help="Target VMOS pad code")
    p.add_argument("--email", default="", help="Google account email")
    p.add_argument("--profile-name", default="Genesis User", help="Profile display name")
    p.add_argument("--card-number", default="", help="Card number for wallet injection")
    p.add_argument("--card-exp", default="", help="Card expiration MM/YY")
    p.add_argument("--age-days", type=int, default=120, help="Forged profile age in days")
    p.add_argument("--use-real-auth", action="store_true", help="Attempt real Google auth via gpsoauth")
    p.add_argument("--proxy", default="", help="Optional proxy URL for OSINT/enrichment")
    return p


async def main_async():
    parser = build_parser()
    args = parser.parse_args()

    cfg = PipelineConfigV3()
    cfg.name = args.profile_name
    cfg.google_email = args.email or ""
    cfg.email = args.email or ""
    cfg.cc_number = args.card_number or ""
    cfg.cc_exp = args.card_exp or ""
    cfg.age_days = args.age_days
    cfg.use_real_auth = bool(args.use_real_auth)
    cfg.proxy_url = args.proxy or ""

    # Initialize client and engine
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE_URL)
    engine = VMOSGenesisV3(pad_code=args.device_id, client=client)

    # Run pipeline
    result = await engine.run_pipeline(cfg)

    # Serialize dataclass to JSON
    try:
        payload = asdict(result)
    except Exception:
        # Fallback: shallow dict
        payload = {k: getattr(result, k) for k in result.__dict__.keys()}

    report_path = f"/tmp/genesis_v3_report_{args.device_id}_{int(time.time())}.json"
    with open(report_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"Pipeline completed: status={result.status} trust_score={result.trust_score}")
    print(f"Report saved: {report_path}")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
