#!/usr/bin/env python3
"""
VMOS Pro Quickstart — Run the full Genesis pipeline against a VMOS Cloud instance.

This script demonstrates the unified VMOS Pro pipeline using either:
  1. VMOSGenesisEngine (full 11-phase pipeline)
  2. VMOSProBridge (individual operations)

Usage:
    # Full pipeline
    python scripts/vmos_pro_quickstart.py --pad APP5B54EI0Z1EOEA \
        --name "Alex Mercer" --email alex@gmail.com \
        --cc 4532015112830366 --cc-exp 12/2027 --cc-cvv 123

    # Health check only
    python scripts/vmos_pro_quickstart.py --pad APP5B54EI0Z1EOEA --health-check

    # Bridge mode (individual operations)
    python scripts/vmos_pro_quickstart.py --pad APP5B54EI0Z1EOEA --bridge \
        --shell "getprop ro.product.model"

Environment:
    VMOS_CLOUD_AK  — API access key
    VMOS_CLOUD_SK  — API secret key
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time

# Add core modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "vmos_titan", "core"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("vmos-quickstart")


async def run_health_check(pad_code: str):
    """Run health check on VMOS instance."""
    from vmos_pro_bridge import VMOSProBridge

    bridge = VMOSProBridge(pad_code=pad_code)
    log.info(f"Running health check on {pad_code}...")

    checks = await bridge.health_check()
    print("\n╔═══════════════════════════════════════════╗")
    print("║         VMOS Pro Health Check              ║")
    print("╠═══════════════════════════════════════════╣")
    for k, v in checks.items():
        status = "OK" if v and v not in ("unknown", False) else "FAIL"
        icon = "✓" if status == "OK" else "✗"
        print(f"║  {icon} {k:25s} {str(v):12s} ║")
    print("╚═══════════════════════════════════════════╝")
    return checks


async def run_bridge_shell(pad_code: str, command: str):
    """Execute a shell command via the bridge."""
    from vmos_pro_bridge import VMOSProBridge

    bridge = VMOSProBridge(pad_code=pad_code)
    result = await bridge.shell(command, timeout=30)

    if result.success:
        print(result.output)
    else:
        print(f"ERROR: {result.error}", file=sys.stderr)
        sys.exit(1)

    stats = bridge.get_stats()
    log.info(f"Bridge stats: {json.dumps(stats, indent=2)}")


async def run_full_pipeline(args):
    """Run the full VMOS Genesis pipeline."""
    from vmos_genesis_engine import VMOSGenesisEngine, PipelineConfig

    pad_code = args.pad
    log.info(f"Starting full Genesis pipeline for {pad_code}")
    log.info(f"Persona: {args.name} <{args.email}>")

    # Build pipeline config
    cc_exp = args.cc_exp or ""
    cfg = PipelineConfig(
        name=args.name or "Auto User",
        email=args.email or "",
        phone=args.phone or "",
        dob=args.dob or "",
        ssn="",
        street=args.street or "",
        city=args.city or "",
        state=args.state or "",
        zip=args.zip_code or "",
        country=args.country or "US",
        gender=args.gender or "M",
        occupation=args.occupation or "professional",
        cc_number=args.cc or "",
        cc_exp=cc_exp,
        cc_cvv=args.cc_cvv or "",
        cc_holder=args.cc_holder or args.name or "",
        google_email=args.google_email or args.email or "",
        google_password=args.google_password or "",
        real_phone=args.real_phone or "",
        otp_code="",
        proxy_url=args.proxy or "",
        device_model=args.device_model or "samsung_s24",
        carrier=args.carrier or "tmobile_us",
        location=args.location or "la",
        age_days=args.age_days or 120,
        skip_patch=args.skip_patch,
    )

    engine = VMOSGenesisEngine(pad_code)
    t0 = time.time()

    def on_update(result):
        """Live progress callback."""
        for ph in result.phases:
            if ph.status == "running":
                log.info(f"  Phase {ph.phase}: {ph.name} — running...")

    result = await engine.run_pipeline(cfg, on_update=on_update)
    elapsed = time.time() - t0

    # Print results
    print("\n" + "=" * 60)
    print("  VMOS PRO GENESIS PIPELINE — RESULTS")
    print("=" * 60)
    print(f"  PAD Code:    {result.pad_code}")
    print(f"  Profile ID:  {result.profile_id}")
    print(f"  Status:      {result.status}")
    print(f"  Trust Score: {result.trust_score}/100 ({result.grade})")
    print(f"  Duration:    {elapsed:.0f}s")
    print("-" * 60)

    for ph in result.phases:
        icon = {"done": "✓", "failed": "✗", "skipped": "⊘", "warn": "⚠"}.get(ph.status, "?")
        print(f"  {icon} Phase {ph.phase:2d}: {ph.name:20s} [{ph.status:8s}] {ph.notes[:40]}")

    print("-" * 60)

    # Print last 10 log entries
    if result.log:
        print("\n  Recent Log:")
        for entry in result.log[-10:]:
            print(f"    {entry}")

    print("=" * 60)

    # Return result dict for programmatic use
    return engine.result_dict()


def main():
    parser = argparse.ArgumentParser(
        description="VMOS Pro Quickstart — Genesis Pipeline for VMOS Cloud Instances",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required
    parser.add_argument("--pad", required=True, help="VMOS Cloud PAD code (e.g. APP5B54EI0Z1EOEA)")

    # Mode selection
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--health-check", action="store_true", help="Run health check only")
    mode.add_argument("--bridge", action="store_true", help="Bridge mode (use --shell)")
    mode.add_argument("--pipeline", action="store_true", default=True, help="Full pipeline (default)")

    # Bridge mode
    parser.add_argument("--shell", help="Shell command to execute (bridge mode)")

    # Persona
    parser.add_argument("--name", help="Full name")
    parser.add_argument("--email", help="Email address")
    parser.add_argument("--phone", help="Phone number")
    parser.add_argument("--dob", help="Date of birth (MM/DD/YYYY)")
    parser.add_argument("--gender", default="M", help="Gender (M/F)")
    parser.add_argument("--occupation", default="professional", help="Occupation archetype")

    # Address
    parser.add_argument("--street", help="Street address")
    parser.add_argument("--city", help="City")
    parser.add_argument("--state", help="State")
    parser.add_argument("--zip-code", help="ZIP code")
    parser.add_argument("--country", default="US", help="Country code")

    # Payment
    parser.add_argument("--cc", help="Credit card number")
    parser.add_argument("--cc-exp", help="Card expiry (MM/YYYY)")
    parser.add_argument("--cc-cvv", help="Card CVV")
    parser.add_argument("--cc-holder", help="Cardholder name (defaults to --name)")

    # Google
    parser.add_argument("--google-email", help="Google email (defaults to --email)")
    parser.add_argument("--google-password", help="Google password (for UI sign-in)")
    parser.add_argument("--real-phone", help="Real phone for 2FA")

    # Device
    parser.add_argument("--device-model", default="samsung_s24", help="Device preset")
    parser.add_argument("--carrier", default="tmobile_us", help="Carrier preset")
    parser.add_argument("--location", default="la", help="Location preset")
    parser.add_argument("--proxy", help="Proxy URL (socks5://user:pass@host:port)")

    # Aging
    parser.add_argument("--age-days", type=int, default=120, help="Device age in days")

    # Options
    parser.add_argument("--skip-patch", action="store_true", help="Skip stealth patch phase")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate environment
    ak = os.environ.get("VMOS_CLOUD_AK", "")
    sk = os.environ.get("VMOS_CLOUD_SK", "")
    if not ak or not sk:
        print("ERROR: Set VMOS_CLOUD_AK and VMOS_CLOUD_SK environment variables", file=sys.stderr)
        sys.exit(1)

    # Dispatch
    if args.health_check:
        asyncio.run(run_health_check(args.pad))
    elif args.bridge and args.shell:
        asyncio.run(run_bridge_shell(args.pad, args.shell))
    elif args.bridge:
        parser.error("--bridge requires --shell <command>")
    else:
        result = asyncio.run(run_full_pipeline(args))
        # Write result to file
        out_path = f"/tmp/vmos_genesis_{args.pad}_{int(time.time())}.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        log.info(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
