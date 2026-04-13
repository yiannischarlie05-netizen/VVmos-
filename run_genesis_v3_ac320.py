#!/usr/bin/env python3
"""Execute Genesis V3 pipeline on AC32010810392."""
import asyncio
import json
import time
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from dataclasses import asdict
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient
from vmos_titan.core.vmos_genesis_v3 import VMOSGenesisV3, PipelineConfigV3

PAD = "AC32010810392"
AK = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
SK = "Q2SgcSwEfuwoedY0cijp6Mce"

cfg = PipelineConfigV3(
    # Identity — coherent US persona
    name="Samuel Epolu",
    email="epolusamuel682@gmail.com",
    phone="+12134567890",
    dob="1992-03-15",
    street="2847 Westwood Blvd",
    city="Los Angeles",
    state="CA",
    zip="90064",
    country="US",
    gender="M",
    occupation="auto",
    # Card
    cc_number="4938755444709420",
    cc_exp="10/2028",
    cc_cvv="007",
    cc_holder="Samuel Epolu",
    # Google real auth
    google_email="epolusamuel682@gmail.com",
    google_password="cldisiingwnxwhnq",
    use_real_auth=False, # Use HYBRID_INJECT instead
    # Device
    device_model="samsung_s24",
    carrier="tmobile_us",
    location="la",
    age_days=120,
    # Options
    inject_purchase_history=True,
    purchase_count=15,
)


def on_update(result):
    """Live progress callback — only print changed phases."""
    if not hasattr(on_update, '_seen'):
        on_update._seen = {}
    for ph in result.phases:
        key = (ph.phase, ph.status, ph.notes)
        if key not in on_update._seen and ph.status not in ("pending",):
            on_update._seen[key] = True
            icon = "✓" if ph.status == "done" else "⚠" if ph.status in ("warn", "skipped") else "✗" if ph.status == "failed" else "…"
            print(f"  {icon} Phase {ph.phase}: {ph.name:<30} [{ph.status}] {ph.notes}")


async def main():
    logging.info("Creating VMOSCloudClient")
    client = VMOSCloudClient(ak=AK, sk=SK, base_url="https://api.vmoscloud.com")
    engine = VMOSGenesisV3(pad_code=PAD, client=client)

    logging.info("Starting Genesis V3 pipeline")
    result = await engine.run_pipeline(cfg, on_update=on_update)
    logging.info("Genesis V3 pipeline finished")

    print("\n" + "="*60)
    print(f"STATUS: {result.status}")
    print(f"TRUST SCORE: {result.trust_score}/100  GRADE: {result.grade}")
    print(f"REAL TOKENS: {result.real_tokens_obtained}")
    print(f"TIME: {result.elapsed:.0f}s")
    print("="*60)

    # Phase summary
    for ph in result.phases:
        icon = "✓" if ph.status == "done" else "⚠" if ph.status == "warn" else "✗" if ph.status == "failed" else "−"
        print(f"  {icon} Phase {ph.phase}: {ph.name:<30} [{ph.status}] {ph.notes}")

    # Save full log
    log_path = f"/tmp/genesis_v3_{PAD}_{int(time.time())}.json"
    with open(log_path, "w") as f:
        json.dump({
            "result": asdict(result),
            "config": asdict(cfg),
        }, f, indent=2, default=str)
    print(f"\nFull log: {log_path}")

    # Print last 30 log lines
    print(f"\n--- Last 30 log lines ---")
    for line in result.log[-30:]:
        print(f"  {line}")


if __name__ == "__main__":
    asyncio.run(main())
