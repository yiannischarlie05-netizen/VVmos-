#!/usr/bin/env python3
"""Quick test of VMOS API device list."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
DEVICE_ID = "APP61F5ERZYHYJH9"

async def test():
    client = VMOSCloudClient(ak=AK, sk=SK)
    
    print("[TEST] Querying device list...")
    try:
        response = await client.instance_list()
        print(f"Response type: {type(response)}")
        print(f"Response:\n{response}\n")
        
        # Try to find our device
        if isinstance(response, dict):
            print("✓ Response is dict")
            print(f"Keys: {response.keys() if hasattr(response, 'keys') else 'N/A'}\n")
            
            # Check for common response formats
            for key in ["data", "devices", "instances", "pads", "padInfos", "result"]:
                if key in response:
                    items = response[key]
                    print(f"Found '{key}': {len(items) if isinstance(items, (list, dict)) else type(items)}")
                    if isinstance(items, list) and len(items) > 0:
                        print(f"First item: {items[0]}\n")
                        
                        # Look for our device
                        for item in items:
                            if isinstance(item, dict):
                                device_id_value = item.get("deviceId") or item.get("device_id") or item.get("padCode") or item.get("id")
                                if device_id_value == DEVICE_ID:
                                    print(f"✓ FOUND DEVICE {DEVICE_ID}!")
                                    print(f"Details: {item}\n")
                                    break
                                    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
