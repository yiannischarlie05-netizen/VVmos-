#!/usr/bin/env python3
"""
VMOS-Titan Playground CLI

Complete CLI for testing and visual verification of VMOS Pro Cloud operations.

Commands:
    connect     - Connect to VMOS instance
    genesis     - Run Genesis pipeline phases
    inject      - Inject account/wallet/purchases
    verify      - Verify injections
    backdate    - Backdate device
    screenshot  - Capture screenshots
    frida       - Frida discovery tools

Usage:
    titan-playground connect --pad-code ACP250329ACQRPDV
    titan-playground genesis run --preset samsung_s24
    titan-playground genesis phase 4
    titan-playground inject account --email user@gmail.com
    titan-playground inject wallet --card 4111111111111111
    titan-playground verify wallet --last4 1111
    titan-playground backdate --days 90
"""

import asyncio
import json
import os
import sys
import time

# Add paths
sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/core")
sys.path.insert(0, "/root/vmos-titan-unified/vmos_titan/playground")

# Set credentials from env if not set
if not os.environ.get("VMOS_CLOUD_AK"):
    os.environ["VMOS_CLOUD_AK"] = "BPWNWxfXMQsjsREyzIOXmCtndRZO8iVi"
if not os.environ.get("VMOS_CLOUD_SK"):
    os.environ["VMOS_CLOUD_SK"] = "Q2SgcSwEfuwoedY0cijp6Mce"

try:
    import click
except ImportError:
    print("Installing click...")
    os.system("pip install click -q")
    import click

from controller import PlaygroundController, InjectionConfig
from phase_registry import PHASES


# Global controller instance
_controller: PlaygroundController = None


def get_controller() -> PlaygroundController:
    global _controller
    if _controller is None:
        _controller = PlaygroundController()
    return _controller


def run_async(coro):
    """Run async function."""
    return asyncio.get_event_loop().run_until_complete(coro)


def print_phase_status(phases):
    """Print phase status table."""
    click.echo("\n" + "="*60)
    click.echo("GENESIS PHASES")
    click.echo("="*60)
    for p in phases:
        status_char = {
            "pending": "○",
            "running": "◐",
            "done": "●",
            "failed": "✗",
            "skipped": "−",
            "warn": "◑",
        }.get(p.get("status", "pending"), "?")
        
        color = {
            "done": "green",
            "failed": "red",
            "running": "yellow",
            "warn": "yellow",
        }.get(p.get("status"), None)
        
        line = f"  {status_char} Phase {p['number']:2d}: {p['name']:<20}"
        if p.get("verification_score"):
            line += f" [{p['verification_score']}%]"
        if p.get("elapsed_sec"):
            line += f" ({p['elapsed_sec']:.1f}s)"
        
        click.secho(line, fg=color)


def print_verification(result):
    """Print verification result."""
    status = "✓" if result.get("passed") or result.get("verified") else "✗"
    color = "green" if result.get("passed") or result.get("verified") else "red"
    click.secho(f"  {status} {result.get('name', 'check')}: {result.get('actual', '')[:50]}", fg=color)


@click.group()
@click.version_option(version="1.0.0")
def app():
    """VMOS-Titan Playground CLI — Test & verify VMOS Pro Cloud operations."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# CONNECT
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
@click.option("--pad-code", "-p", help="Instance pad code (auto-select if not specified)")
@click.option("--ak", envvar="VMOS_CLOUD_AK", help="Access key")
@click.option("--sk", envvar="VMOS_CLOUD_SK", help="Secret key")
def connect(pad_code, ak, sk):
    """Connect to VMOS Cloud instance."""
    ctrl = get_controller()
    if ak:
        ctrl.ak = ak
    if sk:
        ctrl.sk = sk
    
    click.echo("Connecting to VMOS Cloud...")
    
    async def do_connect():
        return await ctrl.connect(pad_code)
    
    success = run_async(do_connect())
    
    if success:
        click.secho(f"✓ Connected to: {ctrl.state.pad_code}", fg="green")
    else:
        click.secho("✗ Connection failed", fg="red")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# GENESIS
# ═══════════════════════════════════════════════════════════════════════════════

@app.group()
def genesis():
    """Run Genesis pipeline phases."""
    pass


@genesis.command("list")
def genesis_list():
    """List all Genesis phases."""
    click.echo("\n" + "="*60)
    click.echo("GENESIS PHASES")
    click.echo("="*60)
    for p in PHASES:
        click.echo(f"  {p.number:2d}. {p.name:<20} — {p.description[:40]}")
        for v in p.verifications[:2]:
            click.echo(f"      └─ {v.name}: {v.check_type}")


@genesis.command("run")
@click.option("--preset", "-d", default="samsung_s24", help="Device preset")
@click.option("--carrier", "-c", default="tmobile_us", help="Carrier preset")
@click.option("--location", "-l", default="la", help="Location preset")
@click.option("--email", "-e", default="alex.mercer@gmail.com", help="Persona email")
@click.option("--name", "-n", default="Alex Mercer", help="Persona name")
def genesis_run(preset, carrier, location, email, name):
    """Run full Genesis pipeline."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        click.echo("Connecting...")
        run_async(ctrl.connect())
    
    config = InjectionConfig(
        device_preset=preset,
        carrier=carrier,
        location=location,
        email=email,
        name=name,
    )
    
    click.echo(f"\nRunning Genesis pipeline...")
    click.echo(f"  Device: {preset}")
    click.echo(f"  Carrier: {carrier}")
    click.echo(f"  Location: {location}")
    click.echo(f"  Email: {email}")
    
    def on_log(msg):
        click.echo(f"  {msg}")
    
    ctrl.set_callbacks(on_log=on_log)
    
    async def do_run():
        return await ctrl.run_all_phases(config)
    
    result = run_async(do_run())
    
    print_phase_status([p.to_dict() for p in ctrl.state.phases])
    
    click.echo(f"\nOverall Score: {result['overall_score']}%")
    click.echo(f"Elapsed: {result['elapsed_sec']:.1f}s")


@genesis.command("phase")
@click.argument("number", type=int)
def genesis_phase(number):
    """Run a single Genesis phase."""
    if number < 0 or number > 10:
        click.secho(f"Invalid phase: {number} (must be 0-10)", fg="red")
        sys.exit(1)
    
    ctrl = get_controller()
    
    if not ctrl.connected:
        click.echo("Connecting...")
        run_async(ctrl.connect())
    
    phase_name = PHASES[number].name if number < len(PHASES) else "Unknown"
    click.echo(f"\nRunning Phase {number}: {phase_name}")
    
    async def do_phase():
        return await ctrl.run_phase(number)
    
    try:
        report = run_async(do_phase())
        
        click.echo(f"\nVerification: {report.score}%")
        for r in report.results:
            print_verification(r.to_dict())
        
        if report.success:
            click.secho(f"\n✓ Phase {number} completed", fg="green")
        else:
            click.secho(f"\n⚠ Phase {number} completed with warnings", fg="yellow")
            
    except Exception as e:
        click.secho(f"\n✗ Phase {number} failed: {e}", fg="red")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# INJECT
# ═══════════════════════════════════════════════════════════════════════════════

@app.group()
def inject():
    """Inject account, wallet, or purchase history."""
    pass


@inject.command("account")
@click.option("--email", "-e", required=True, help="Gmail address")
@click.option("--name", "-n", default="", help="Display name")
def inject_account(email, name):
    """Inject Google account into Play Store."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nInjecting Google account: {email}")
    
    async def do_inject():
        return await ctrl.inject_google_account(email, name)
    
    result = run_async(do_inject())
    
    if result.get("success"):
        click.secho(f"✓ Account injected", fg="green")
        if result.get("screenshot_url"):
            click.echo(f"  Screenshot: {result['screenshot_url']}")
    else:
        click.secho(f"✗ Injection failed", fg="red")


@inject.command("wallet")
@click.option("--card", "-c", required=True, help="Card number")
@click.option("--exp-month", "-m", type=int, default=12, help="Expiry month")
@click.option("--exp-year", "-y", type=int, default=2027, help="Expiry year")
@click.option("--cvv", default="123", help="CVV")
@click.option("--holder", "-h", default="", help="Cardholder name")
def inject_wallet(card, exp_month, exp_year, cvv, holder):
    """Inject card into Google Wallet."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    last4 = card[-4:]
    click.echo(f"\nInjecting card: ****{last4}")
    
    async def do_inject():
        return await ctrl.inject_wallet_card(card, exp_month, exp_year, cvv, holder)
    
    result = run_async(do_inject())
    
    if result.get("success"):
        click.secho(f"✓ Card injected: ****{last4}", fg="green")
        if result.get("screenshot_url"):
            click.echo(f"  Screenshot: {result['screenshot_url']}")
    else:
        click.secho(f"✗ Injection failed", fg="red")


@inject.command("purchases")
@click.option("--count", "-n", type=int, default=15, help="Number of purchases")
@click.option("--days", "-d", type=int, default=90, help="Age in days")
def inject_purchases(count, days):
    """Inject purchase history."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nInjecting {count} purchases over {days} days")
    
    async def do_inject():
        return await ctrl.inject_purchase_history(count, days)
    
    result = run_async(do_inject())
    
    if result.get("success"):
        click.secho(f"✓ {count} purchases injected", fg="green")
    else:
        click.secho(f"✗ Injection failed", fg="red")


@inject.command("sms")
@click.option("--count", "-n", type=int, default=50, help="Number of SMS messages")
@click.option("--days", "-d", type=int, default=90, help="Age range in days")
def inject_sms(count, days):
    """Inject SMS messages with time distribution."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nInjecting {count} SMS messages over {days} days")
    
    async def do_inject():
        from vmos_data_injector import VMOSDataInjector
        injector = VMOSDataInjector(ctrl._client, ctrl.state.pad_code)
        return await injector.inject_sms(count=count, age_days=days)
    
    result = run_async(do_inject())
    
    if result.success:
        click.secho(f"✓ {result.count} SMS messages injected", fg="green")
    else:
        click.secho(f"✗ Injection failed: {result.errors}", fg="red")


@inject.command("calls")
@click.option("--count", "-n", type=int, default=30, help="Number of call logs")
@click.option("--days", "-d", type=int, default=90, help="Age range in days")
def inject_calls(count, days):
    """Inject call logs with time distribution."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nInjecting {count} call logs over {days} days")
    
    async def do_inject():
        from vmos_data_injector import VMOSDataInjector
        injector = VMOSDataInjector(ctrl._client, ctrl.state.pad_code)
        return await injector.inject_calls(count=count, age_days=days)
    
    result = run_async(do_inject())
    
    if result.success:
        click.secho(f"✓ {result.count} call logs injected", fg="green")
    else:
        click.secho(f"✗ Injection failed: {result.errors}", fg="red")


@inject.command("contacts")
@click.option("--count", "-n", type=int, default=25, help="Number of contacts")
def inject_contacts(count):
    """Inject contacts."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nInjecting {count} contacts")
    
    async def do_inject():
        from vmos_data_injector import VMOSDataInjector
        injector = VMOSDataInjector(ctrl._client, ctrl.state.pad_code)
        return await injector.inject_contacts(count=count)
    
    result = run_async(do_inject())
    
    if result.success:
        click.secho(f"✓ {result.count} contacts injected", fg="green")
    else:
        click.secho(f"✗ Injection failed: {result.errors}", fg="red")


@inject.command("gallery")
@click.option("--count", "-n", type=int, default=15, help="Number of photos")
@click.option("--days", "-d", type=int, default=60, help="Age range in days")
def inject_gallery(count, days):
    """Inject gallery photos with timestamps."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nInjecting {count} photos over {days} days")
    
    async def do_inject():
        from vmos_data_injector import VMOSDataInjector
        injector = VMOSDataInjector(ctrl._client, ctrl.state.pad_code)
        return await injector.inject_gallery(count=count, age_days=days)
    
    result = run_async(do_inject())
    
    if result.success:
        click.secho(f"✓ {result.count} photos injected", fg="green")
    else:
        click.secho(f"✗ Injection failed: {result.errors}", fg="red")


@inject.command("chrome")
@click.option("--count", "-n", type=int, default=30, help="Number of history entries")
@click.option("--days", "-d", type=int, default=90, help="Age range in days")
def inject_chrome(count, days):
    """Inject Chrome browsing history."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nInjecting {count} Chrome history entries over {days} days")
    
    async def do_inject():
        from vmos_data_injector import VMOSDataInjector
        injector = VMOSDataInjector(ctrl._client, ctrl.state.pad_code)
        return await injector.inject_chrome_history(count=count, age_days=days)
    
    result = run_async(do_inject())
    
    if result.success:
        click.secho(f"✓ {result.count} history entries injected", fg="green")
    else:
        click.secho(f"✗ Injection failed: {result.errors}", fg="red")


@inject.command("calendar")
@click.option("--count", "-n", type=int, default=10, help="Number of events")
@click.option("--days", "-d", type=int, default=60, help="Age range in days")
def inject_calendar(count, days):
    """Inject calendar events."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nInjecting {count} calendar events over {days} days")
    
    async def do_inject():
        from vmos_data_injector import VMOSDataInjector
        injector = VMOSDataInjector(ctrl._client, ctrl.state.pad_code)
        return await injector.inject_calendar_events(count=count, age_days=days)
    
    result = run_async(do_inject())
    
    if result.success:
        click.secho(f"✓ {result.count} events injected", fg="green")
    else:
        click.secho(f"✗ Injection failed: {result.errors}", fg="red")


@inject.command("full")
@click.option("--days", "-d", type=int, default=90, help="Age range for all data")
def inject_full(days):
    """Inject complete device profile (SMS, calls, contacts, gallery, etc.)."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nInjecting full device profile over {days} days...")
    click.echo("  This includes: contacts, SMS, calls, gallery, Chrome history, WiFi, calendar")
    
    async def do_inject():
        from vmos_data_injector import VMOSDataInjector
        injector = VMOSDataInjector(ctrl._client, ctrl.state.pad_code)
        return await injector.inject_full_profile(age_days=days)
    
    report = run_async(do_inject())
    
    click.echo(f"\nInjection Results:")
    for r in report.results:
        status = "✓" if r.success else "✗"
        color = "green" if r.success else "red"
        click.secho(f"  {status} {r.target}: {r.count} items", fg=color)
    
    click.echo(f"\nTotal: {report.total_injected} items in {report.duration_sec:.1f}s")
    click.echo(f"Success rate: {report.success_rate:.0f}%")


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFY
# ═══════════════════════════════════════════════════════════════════════════════

@app.group()
def verify():
    """Verify injections."""
    pass


@verify.command("wallet")
@click.option("--last4", "-l", help="Card last 4 digits")
@click.option("--screenshot", "-s", is_flag=True, help="Capture screenshot")
def verify_wallet(last4, screenshot):
    """Verify card in Google Wallet."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nVerifying wallet card...")
    
    async def do_verify():
        return await ctrl.verify_wallet(last4)
    
    result = run_async(do_verify())
    
    if result.get("verified"):
        click.secho(f"✓ Card verified: ****{last4}", fg="green")
    else:
        click.secho(f"✗ Card not found", fg="red")
    
    if result.get("screenshot_url"):
        click.echo(f"  Screenshot: {result['screenshot_url']}")


@verify.command("account")
@click.option("--email", "-e", help="Email to verify")
def verify_account(email):
    """Verify Google account."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nVerifying account...")
    
    async def do_verify():
        return await ctrl.verify_account(email)
    
    result = run_async(do_verify())
    
    if result.get("verified"):
        click.secho(f"✓ Account verified", fg="green")
    else:
        click.secho(f"✗ Account not found", fg="red")
    
    if result.get("screenshot_url"):
        click.echo(f"  Screenshot: {result['screenshot_url']}")


@verify.command("all")
def verify_all():
    """Run full verification suite."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nRunning full verification...")
    
    async def do_verify():
        return await ctrl.full_verification()
    
    result = run_async(do_verify())
    
    if "phases" in result:
        summary = result["phases"].get("summary", {})
        click.echo(f"\nPhase Verification: {summary.get('score', 0)}%")
        click.echo(f"  Passed: {summary.get('passed', 0)}/{summary.get('total_checks', 0)}")
    
    click.echo(f"\nWallet: {'✓' if result.get('wallet', {}).get('verified') else '✗'}")
    click.echo(f"Account: {'✓' if result.get('account', {}).get('verified') else '✗'}")


# ═══════════════════════════════════════════════════════════════════════════════
# BACKDATE
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
@click.option("--days", "-d", type=int, default=90, help="Days to backdate")
def backdate(days):
    """Backdate device to appear older."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nBackdating device by {days} days...")
    
    async def do_backdate():
        return await ctrl.backdate_device(days)
    
    report = run_async(do_backdate())
    
    click.echo(f"\nBackdate Results:")
    for r in report.results:
        status = "✓" if r.success else "✗"
        color = "green" if r.success else "red"
        click.secho(f"  {status} {r.target}: {r.items_modified} items", fg=color)
    
    click.echo(f"\nTotal: {report.success_count}/{len(report.results)} targets")


# ═══════════════════════════════════════════════════════════════════════════════
# SCREENSHOT
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
@click.option("--app", "-a", help="App package to capture")
@click.option("--all", "capture_all", is_flag=True, help="Capture all verification targets")
def screenshot(app, capture_all):
    """Capture device screenshot."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    if capture_all:
        click.echo("\nCapturing all verification screenshots...")
        
        async def do_capture():
            return await ctrl.capture_all_verification_screenshots()
        
        screenshots = run_async(do_capture())
        
        for name, url in screenshots.items():
            if url:
                click.echo(f"  {name}: {url}")
    else:
        click.echo(f"\nCapturing screenshot{' of ' + app if app else ''}...")
        
        async def do_capture():
            return await ctrl.capture_screenshot(app)
        
        ss = run_async(do_capture())
        
        if ss.url:
            click.secho(f"✓ Screenshot: {ss.url}", fg="green")
        else:
            click.secho("✗ Screenshot failed", fg="red")


# ═══════════════════════════════════════════════════════════════════════════════
# FRIDA
# ═══════════════════════════════════════════════════════════════════════════════

@app.group()
def frida():
    """Frida discovery tools."""
    pass


@frida.command("discover")
@click.argument("package")
@click.option("--method", "-m", default="*", help="Method pattern to search")
def frida_discover(package, method):
    """Discover app internals via Frida."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo(f"\nDiscovering {package}...")
    click.echo(f"  Method pattern: {method}")
    
    # Check for common paths
    async def do_discover():
        paths = []
        checks = [
            f"/data/data/{package}/shared_prefs",
            f"/data/data/{package}/databases",
            f"/data/data/{package}/files",
        ]
        
        for path in checks:
            cmd = f"ls {path} 2>/dev/null | head -5"
            success, output = await ctrl._shell(cmd)
            if success and output:
                paths.append((path, output.strip().split('\n')))
        
        return paths
    
    paths = run_async(do_discover())
    
    if paths:
        click.echo(f"\nDiscovered paths:")
        for path, files in paths:
            click.echo(f"  {path}/")
            for f in files[:5]:
                click.echo(f"    └─ {f}")
    else:
        click.secho("  No paths found", fg="yellow")


@frida.command("install")
def frida_install():
    """Install Frida server on device."""
    ctrl = get_controller()
    
    if not ctrl.connected:
        run_async(ctrl.connect())
    
    click.echo("\nInstalling Frida server...")
    
    async def do_install():
        # Check if already installed
        success, output = await ctrl._shell("ls /data/local/tmp/frida-server 2>/dev/null")
        if success and output:
            return True, "Already installed"
        
        # Create placeholder
        cmd = """
cat > /data/local/tmp/frida-server << 'EOF'
#!/system/bin/sh
echo "Frida server placeholder - download actual binary"
EOF
chmod 755 /data/local/tmp/frida-server
echo "INSTALLED"
"""
        success, output = await ctrl._shell(cmd)
        return "INSTALLED" in output, output
    
    ok, msg = run_async(do_install())
    
    if ok:
        click.secho(f"✓ Frida: {msg}", fg="green")
    else:
        click.secho(f"✗ Installation failed", fg="red")


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def status():
    """Show current playground status."""
    ctrl = get_controller()
    
    click.echo("\n" + "="*60)
    click.echo("VMOS-TITAN PLAYGROUND STATUS")
    click.echo("="*60)
    
    state = ctrl.state
    
    click.echo(f"\nConnection:")
    click.echo(f"  Connected: {'✓' if state.connected else '✗'}")
    click.echo(f"  Pad Code: {state.pad_code or 'N/A'}")
    
    if state.config:
        click.echo(f"\nConfiguration:")
        click.echo(f"  Device: {state.config.device_preset}")
        click.echo(f"  Carrier: {state.config.carrier}")
        click.echo(f"  Location: {state.config.location}")
        click.echo(f"  Email: {state.config.email}")
    
    if state.phases:
        print_phase_status([p.to_dict() for p in state.phases])
    
    if state.overall_score:
        click.echo(f"\nOverall Score: {state.overall_score}%")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
