#!/usr/bin/env python3
"""
Genesis V3 Executor with Automatic Retry
Implements exponential backoff (3s → 5s → 10s → 30s max) for VMOS API errors
Recovers from temporary service disruptions (code 500, code 110031)
"""

import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path

LOG_DIR = Path("/tmp/genesis_v3_logs")
LOG_DIR.mkdir(exist_ok=True)

def run_genesis_pipeline(attempt: int = 1, max_attempts: int = 5) -> bool:
    """Execute Genesis V3 pipeline with retry logic."""
    
    log_file = LOG_DIR / f"genesis_attempt_{attempt}_{int(time.time())}.log"
    
    print(f"\n{'='*70}")
    print(f"GENESIS V3 EXECUTION — ATTEMPT {attempt}/{max_attempts}")
    print(f"{'='*70}")
    print(f"Device: ATP2508250GBTNU6")
    print(f"User: Jason Hailey (williamsetkyson@gmail.com)")
    print(f"Target: 100/100 Trust Score")
    print(f"Log: {log_file}")
    print(f"{'='*70}\n")
    
    # Set environment
    env = os.environ.copy()
    env.update({
        "VMOS_CLOUD_AK": "YOUR_VMOS_AK_HERE",
        "VMOS_CLOUD_SK": "YOUR_VMOS_SK_HERE",
        "VMOS_CLOUD_BASE_URL": "https://api.vmoscloud.com",
        "PYTHONUNBUFFERED": "1",
    })
    
    # Execute pipeline
    try:
        with open(log_file, "w") as logf:
            result = subprocess.run(
                [
                    sys.executable,
                    "genesis/genesis_full_pipeline.py"
                ],
                cwd="/home/debian/Downloads/vmos-titan-unified",
                env=env,
                stdout=logf,
                stderr=subprocess.STDOUT,
                timeout=600  # 10-minute timeout per attempt
            )
        
        # Check result
        with open(log_file, "r") as f:
            output = f.read()
        
        # Success indicators
        if "GENESIS PIPELINE COMPLETE" in output and "TRUST SCORE:" in output:
            print(f"✅ ATTEMPT {attempt} → SUCCESS")
            print(f"\n{'='*70}")
            print("GENESIS V3 PIPELINE COMPLETED SUCCESSFULLY")
            print(f"{'='*70}\n")
            
            # Extract final scores
            for line in output.split("\n"):
                if "TRUST SCORE:" in line or "GRADE:" in line or "BNPL" in line:
                    print(f"  {line.strip()}")
            
            print(f"\nFull log: {log_file}")
            return True
        
        # Failure cases
        if result.returncode != 0:
            print(f"⚠️ ATTEMPT {attempt} → FAILED (exit code {result.returncode})")
            
            # Parse error type
            if "code=500" in output or "System is busy" in output:
                print("   Error: API service busy (code 500)")
                print("   Action: Retry with backoff...")
            elif "code=110031" in output or "FLOOD" in output:
                print("   Error: Rate limited (code 110031)")
                print("   Action: Retry with longer delay...")
            else:
                print("   Error: Check log for details")
                return False
        else:
            print(f"⚠️ ATTEMPT {attempt} → INCOMPLETE (no success marker)")
            print("   Action: Retry...")
    
    except subprocess.TimeoutExpired:
        print(f"⚠️ ATTEMPT {attempt} → TIMEOUT (10 minutes)")
        print("   Action: Retry with fresh execution...")
    
    except Exception as e:
        print(f"❌ ATTEMPT {attempt} → ERROR: {e}")
        return False
    
    # Retry logic
    if attempt < max_attempts:
        # Exponential backoff: 3s, 5s, 10s, 30s
        backoff_schedule = [3, 5, 10, 30]
        wait_time = backoff_schedule[min(attempt - 1, len(backoff_schedule) - 1)]
        
        print(f"\n⏳ Waiting {wait_time}s before retry...")
        time.sleep(wait_time)
        
        return run_genesis_pipeline(attempt + 1, max_attempts)
    else:
        print(f"\n❌ MAX ATTEMPTS ({max_attempts}) REACHED")
        print("   Recommendations:")
        print("   1. Check VMOS Cloud service status")
        print("   2. Verify credentials in environment variables")
        print("   3. Wait longer before retrying (service may be under maintenance)")
        return False


if __name__ == "__main__":
    success = run_genesis_pipeline()
    sys.exit(0 if success else 1)
