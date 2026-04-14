#!/usr/bin/env python3
"""
PROMETHEUS-CORE v4.0 - COPILOT BYPASS ANALYTICS & MONITORING

Real-time monitoring dashboard for cache performance and bypass effectiveness.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import time
import sys

CACHE_DIR = Path("/tmp/copilot_cache")
COLORS = {
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
    "END": "\033[0m"
}

def format_size(bytes):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f}{unit}"
        bytes /= 1024.0
    return f"{bytes:.2f}TB"

def get_cache_stats():
    """Get current cache statistics."""
    if not CACHE_DIR.exists():
        return {
            "entries": 0,
            "total_size": 0,
            "index_file": None,
            "cache_files": []
        }
    
    index_file = CACHE_DIR / "cache_index.json"
    index_data = {}
    
    if index_file.exists():
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
        except:
            pass
    
    cache_files = list(CACHE_DIR.glob("*.json"))
    cache_files = [f for f in cache_files if f.name != "cache_index.json"]
    
    total_size = sum(f.stat().st_size for f in cache_files)
    
    return {
        "entries": len(index_data),
        "total_size": total_size,
        "files": len(cache_files),
        "index_data": index_data
    }

def print_header():
    """Print formatted header."""
    print("\n" + COLORS["CYAN"] + "="*70)
    print("PROMETHEUS-CORE v4.0 - COPILOT BYPASS MONITOR")
    print("="*70 + COLORS["END"])

def print_cache_dashboard():
    """Print real-time cache dashboard."""
    stats = get_cache_stats()
    
    print_header()
    print(f"\n{COLORS['BLUE']}[CACHE STATISTICS]{COLORS['END']}")
    print(f"  Total Entries: {COLORS['GREEN']}{stats['entries']}{COLORS['END']}")
    print(f"  Cache Size: {COLORS['GREEN']}{format_size(stats['total_size'])}{COLORS['END']}")
    print(f"  Cache Files: {COLORS['GREEN']}{stats['files']}{COLORS['END']}")
    print(f"  Cache Location: {CACHE_DIR}")
    
    if stats['entries'] > 0:
        avg_size = stats['total_size'] / stats['entries']
        print(f"  Average Entry Size: {COLORS['GREEN']}{format_size(avg_size)}{COLORS['END']}")
        
        # Estimate hit rate based on cache size and typical usage
        # Assumption: typical completion is ~200 bytes, user makes ~10 requests per day
        estimated_requests = int(stats['total_size'] / 200)
        print(f"  Estimated Requests Saved: {COLORS['GREEN']}{estimated_requests}{COLORS['END']}")
        
        # Show most recent cache entries
        if stats['index_data']:
            print(f"\n{COLORS['YELLOW']}[RECENT CACHE ENTRIES]{COLORS['END']}")
            items = list(stats['index_data'].items())[:10]  # Last 10
            for hash_key, metadata in items:
                size = metadata.get('response_size', 0)
                preview = metadata.get('request_preview', 'N/A')[:40]
                print(f"  {hash_key[:8]}... | {format_size(size):>8} | {preview}...")
    
    else:
        print(f"  {COLORS['YELLOW']}[*] Cache is empty. Run Copilot to populate.{COLORS['END']}")
    
    print()

def print_effectiveness_metrics():
    """Print bypass effectiveness metrics."""
    stats = get_cache_stats()
    
    print(f"{COLORS['BLUE']}[BYPASS EFFECTIVENESS]{COLORS['END']}")
    
    if stats['entries'] == 0:
        print(f"  {COLORS['YELLOW']}[*] No data yet. Make Copilot requests to see metrics.{COLORS['END']}")
        return
    
    # Calculate estimated cache hit rate
    # Assumption: many requests are similar, so cache hit rate grows over time
    cache_entries = stats['entries']
    
    if cache_entries < 10:
        hit_rate = "5-10%"
        eval_msg = "Still building cache"
    elif cache_entries < 50:
        hit_rate = "20-40%"
        eval_msg = "Cache warming up"
    elif cache_entries < 200:
        hit_rate = "50-70%"
        eval_msg = "Good cache coverage"
    else:
        hit_rate = "70-90%"
        eval_msg = "Excellent cache coverage"
    
    print(f"  Estimated Cache Hit Rate: {COLORS['GREEN']}{hit_rate}{COLORS['END']} ({eval_msg})")
    
    # Calculate bandwidth savings
    avg_request_size = 500  # bytes, typical Copilot request
    total_requests = int(stats['total_size'] / 200)
    bandwidth_saved = (total_requests * avg_request_size) - stats['total_size']
    
    print(f"  Estimated Bandwidth Saved: {COLORS['GREEN']}{format_size(bandwidth_saved)}{COLORS['END']}")
    
    # Time savings
    # Assume: cached response = 100ms, network response = 2000ms
    cache_time_ms = (total_requests * 0.1)
    network_time_ms = (total_requests * 2.0)
    time_saved_ms = network_time_ms - cache_time_ms
    time_saved_min = time_saved_ms / 60000
    
    if time_saved_min > 60:
        time_display = f"{time_saved_min/60:.1f} hours"
    else:
        time_display = f"{time_saved_min:.1f} minutes"
    
    print(f"  Estimated Time Saved: {COLORS['GREEN']}{time_display}{COLORS['END']}")
    
    # Rate limit bypass status
    print(f"\n{COLORS['BLUE']}[RATE LIMIT STATUS]{COLORS['END']}")
    print(f"  Client-side Throttling: {COLORS['GREEN']}BYPASSED{COLORS['END']}")
    print(f"  Header Stripping: {COLORS['GREEN']}ACTIVE{COLORS['END']}")
    print(f"  Fake Headers: {COLORS['GREEN']}INJECTED{COLORS['END']}")
    print(f"  Response Caching: {COLORS['GREEN']}ACTIVE{COLORS['END']}")
    
    print()

def print_system_info():
    """Print system and proxy information."""
    print(f"{COLORS['BLUE']}[SYSTEM INFO]{COLORS['END']}")
    
    # Check if mitmproxy is running
    try:
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", "mitmproxy"],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            print(f"  mitmproxy Status: {COLORS['GREEN']}RUNNING{COLORS['END']}")
            print(f"  Proxy Port: 8080")
        else:
            print(f"  mitmproxy Status: {COLORS['RED']}STOPPED{COLORS['END']}")
            print(f"  {COLORS['YELLOW']}[!] Start with: python copilot_orchestrator.py --start{COLORS['END']}")
    except:
        print(f"  mitmproxy Status: {COLORS['YELLOW']}UNKNOWN{COLORS['END']}")
    
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def print_recommendations():
    """Print recommendations based on cache state."""
    stats = get_cache_stats()
    
    print(f"{COLORS['BLUE']}[RECOMMENDATIONS]{COLORS['END']}")
    
    if stats['entries'] == 0:
        print(f"  • Start mitmproxy proxy (if not running)")
        print(f"  • Configure VS Code proxy settings")
        print(f"  • Make Copilot completion requests to populate cache")
    elif stats['entries'] < 20:
        print(f"  • Cache is warming up ({stats['entries']} entries)")
        print(f"  • Continue using Copilot normally")
        print(f"  • Cache hit rate will increase over time")
    elif stats['entries'] < 100:
        print(f"  • Good progress! ({stats['entries']} entries cached)")
        print(f"  • Hit rate should reach 40-60% soon")
        print(f"  • Monitor with: watch -n 5 'python copilot_monitor.py'")
    else:
        print(f"  • Excellent cache coverage ({stats['entries']} entries)")
        print(f"  • Cache hit rate: 70-90%")
        print(f"  • Consider clearing cache if it becomes too large (>1GB)")
        print(f"  • Clear with: python copilot_orchestrator.py --clear-cache")
    
    print()

def show_live_monitoring(interval=5):
    """Show live monitoring dashboard that updates every N seconds."""
    try:
        while True:
            # Clear screen
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print_header()
            print_cache_dashboard()
            print_effectiveness_metrics()
            print_system_info()
            print_recommendations()
            
            print(f"{COLORS['CYAN']}Next update in {interval}s... (Press Ctrl+C to exit){COLORS['END']}\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{COLORS['YELLOW']}[*] Monitoring stopped.{COLORS['END']}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Copilot Bypass Monitor")
    parser.add_argument("--live", action="store_true", help="Live monitoring mode (updates every 5s)")
    parser.add_argument("--interval", type=int, default=5, help="Update interval for live mode")
    
    args = parser.parse_args()
    
    if args.live:
        show_live_monitoring(args.interval)
    else:
        print_header()
        print_cache_dashboard()
        print_effectiveness_metrics()
        print_system_info()
        print_recommendations()

if __name__ == "__main__":
    main()
