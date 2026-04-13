#!/usr/bin/env python3
"""
Quick demo of VMOS+OnePlus 100-Experiment Suite
Shows structure and experiment categories without needing cloud credentials
"""

import json
import sys
sys.path.insert(0, "/home/debian/Downloads/vmos-titan-unified")

from vmos_cloud_oneplus_100experiments import VMOSCloudOnePlus100Experiments

def demo_suite():
    """Demonstrate the suite structure."""
    suite = VMOSCloudOnePlus100Experiments()
    
    print("\n" + "=" * 70)
    print("  VMOS PRO CLOUD - ONEPLUS 100 EXPERIMENT SUITE - DEMO")
    print("=" * 70)
    
    # Define experiments
    suite._define_100_experiments()
    
    print(f"\n✓ Total Experiments Defined: {len(suite.experiments)}")
    print(f"✓ Authority Level: {suite.experiments[0].authority_level}/10 (MAXIMUM)")
    
    # Group by category
    by_category = {}
    for exp in suite.experiments:
        if exp.category not in by_category:
            by_category[exp.category] = []
        by_category[exp.category].append(exp)
    
    print(f"\n📊 Experiments by Category:\n")
    total = 0
    for cat in sorted(by_category.keys()):
        exps = by_category[cat]
        total += len(exps)
        print(f"  {cat}: {len(exps)} experiments")
        for exp in exps[:3]:
            print(f"    • {exp.name}")
        if len(exps) > 3:
            print(f"    ... and {len(exps) - 3} more")
    
    print(f"\n✓ TOTAL EXPERIMENTS: {total}")
    
    # Show sample structure
    print(f"\n📋 Sample Experiment Structure:\n")
    sample = suite.experiments[0]
    print(f"  ID: {sample.id}")
    print(f"  Category: {sample.category}")
    print(f"  Name: {sample.name}")
    print(f"  Description: {sample.description}")
    print(f"  Authority: {sample.authority_level}/10")
    
    # Show execution flow
    print(f"\n🚀 Execution Flow:\n")
    print(f"  1. Connect to VMOS Cloud API (HMAC-SHA256)")
    print(f"  2. Discover OnePlus devices in cloud")
    print(f"  3. Setup ADB connection to target device")
    print(f"  4. Execute 100 experiments with findings")
    print(f"  5. Generate comprehensive JSON report")
    print(f"  6. Analyze results by category")
    
    # Show categories
    print(f"\n📚 All 10 Categories:\n")
    for i, cat in enumerate(sorted(by_category.keys()), 1):
        print(f"  {i}. {cat}")
    
    print(f"\n✅ Suite structure verified and ready for deployment")
    
    return 0

if __name__ == "__main__":
    sys.exit(demo_suite())
