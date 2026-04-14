#!/usr/bin/env python3
"""
VMOS Pro Cloud — Host-Level Billing & Expiration Reconnaissance
Connects to VMOS Cloud API, enumerates all devices with their billing
status, expiration dates, and tests expiration extension capabilities.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient


AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE = "https://api.vmoscloud.com"


def ts_to_str(ts):
    """Convert millisecond or second timestamp to readable datetime."""
    if ts is None:
        return "N/A"
    try:
        ts = int(ts)
        if ts > 1e12:
            ts = ts / 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return str(ts)


def days_remaining(ts):
    """Calculate days remaining from a timestamp."""
    if ts is None:
        return None
    try:
        ts = int(ts)
        if ts > 1e12:
            ts = ts / 1000
        exp = datetime.fromtimestamp(ts, tz=timezone.utc)
        delta = exp - datetime.now(timezone.utc)
        return round(delta.total_seconds() / 86400, 1)
    except Exception:
        return None


async def main():
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE)

    print("=" * 80)
    print("  VMOS PRO CLOUD — BILLING & EXPIRATION RECONNAISSANCE")
    print("=" * 80)

    # ─── PHASE 1: Device Inventory with Full Metadata ───────────────────
    print("\n[PHASE 1] Enumerating all cloud devices via instance_list (padApi/infos)...")
    all_devices = []
    page = 1
    while True:
        await asyncio.sleep(3)
        resp = await client.instance_list(page=page, rows=50)
        data = resp.get("data", {})
        if isinstance(data, dict):
            records = data.get("pageData", data.get("records", data.get("list", [])))
            total = data.get("total", 0)
        elif isinstance(data, list):
            records = data
            total = len(data)
        else:
            break
        if not records:
            break
        all_devices.extend(records)
        if len(all_devices) >= total:
            break
        page += 1

    print(f"  instance_list: {len(all_devices)} devices found")

    # ─── PHASE 1b: Cloud Phone List (has billing fields) ─────────────────
    print("\n[PHASE 1b] Enumerating via cloud_phone_list (padApi/userPadList)...")
    all_phones = []
    await asyncio.sleep(3)
    cp_resp = await client.cloud_phone_list(page=1, rows=200)
    cp_data = cp_resp.get("data", {})
    if isinstance(cp_data, list):
        all_phones = cp_data
    elif isinstance(cp_data, dict):
        all_phones = cp_data.get("records", cp_data.get("pageData", cp_data.get("list", [])))
    
    print(f"  userPadList: {len(all_phones)} devices found")

    # Merge into unified view — userPadList has the billing fields
    phone_by_code = {p.get("padCode", ""): p for p in all_phones}
    
    print(f"\n{'PAD CODE':<28} {'ST':>3} {'CREATED':>20} {'EXPIRES':>20} {'DAYS LEFT':>10} {'AUTO-RENEW':>10} {'GOOD':>6}")
    print("-" * 105)

    billing_fields_seen = set()
    expiration_devices = []

    # Use userPadList as primary — it has billing info
    for d in all_phones:
        pad_code = d.get("padCode", "?")
        status = d.get("cvmStatus", d.get("podStatus", d.get("padStatus", "?")))
        
        # Collect time-related keys
        time_keys = {}
        for k, v in d.items():
            kl = k.lower()
            if any(t in kl for t in ["time", "date", "expir", "renew", "creat", "end", "start", "due", "period", "order", "sign", "boot"]):
                time_keys[k] = v
                billing_fields_seen.add(k)

        created = d.get("createTime", None)
        expires = d.get("signExpirationTime", d.get("signExpirationTimeTamp", d.get("dueTime", None)))
        auto_renew_gid = d.get("autoRenewGoodId", d.get("autoRenew", "?"))
        good_id = d.get("goodId", "?")

        remaining = days_remaining(expires)
        remaining_str = f"{remaining}d" if remaining is not None else "?"

        print(f"{pad_code:<28} {str(status):>3} {ts_to_str(created):>20} {ts_to_str(expires):>20} {remaining_str:>10} {str(auto_renew_gid):>10} {str(good_id):>6}")

        expiration_devices.append({
            "padCode": pad_code,
            "status": status,
            "created": created,
            "expires": expires,
            "daysRemaining": remaining,
            "autoRenewGoodId": auto_renew_gid,
            "goodId": good_id,
            "displayName": d.get("displayName", d.get("padName", "?")),
            "allTimeFields": time_keys,
        })

    # ─── PHASE 2: Field Discovery ──────────────────────────────────────
    print(f"\n\n[PHASE 2] Billing/Time field discovery across all devices")
    print(f"  Unique time/billing fields found: {sorted(billing_fields_seen)}")
    
    # Show raw data for first phone entry
    if all_phones:
        print(f"\n  [RAW] First userPadList entry — ALL fields:")
        for k, v in sorted(all_phones[0].items()):
            val_str = str(v)[:120]
            print(f"    {k}: {val_str}")

    # Show raw data for first instance_list entry
    if all_devices:
        print(f"\n  [RAW] First instance_list entry — ALL fields:")
        for k, v in sorted(all_devices[0].items()):
            val_str = str(v)[:120]
            print(f"    {k}: {val_str}")

    # ─── PHASE 3: (Data already gathered in Phase 1b — cross-reference) ─
    print(f"\n\n[PHASE 3] Cross-referencing instance_list vs userPadList...")
    inst_codes = {d.get("padCode") for d in all_devices if d.get("padCode")}
    phone_codes = {p.get("padCode") for p in all_phones if p.get("padCode")}
    only_inst = inst_codes - phone_codes
    only_phone = phone_codes - inst_codes
    both = inst_codes & phone_codes
    print(f"  In both endpoints: {len(both)}")
    print(f"  Only in instance_list: {len(only_inst)} — {only_inst or 'none'}")
    print(f"  Only in userPadList: {len(only_phone)} — {only_phone or 'none'}")

    # ─── PHASE 4: SKU Package List ─────────────────────────────────────
    print(f"\n\n[PHASE 4] SKU package/product catalog...")
    await asyncio.sleep(3)
    sku_resp = await client.sku_package_list()
    sku_data = sku_resp.get("data", [])
    if isinstance(sku_data, list):
        print(f"  Found {len(sku_data)} SKU packages:")
        for sku in sku_data[:10]:
            if isinstance(sku, dict):
                name = sku.get("goodName", sku.get("name", "?"))
                price = sku.get("goodPrice", sku.get("price", "?"))
                good_id = sku.get("goodId", sku.get("id", "?"))
                duration = sku.get("duration", sku.get("period", sku.get("days", "?")))
                print(f"    ID={good_id}  {name}  price={price}  duration={duration}")
                print(f"      Full fields: {list(sku.keys())}")
    else:
        print(f"  SKU response: {json.dumps(sku_data, indent=2)[:500]}")

    # ─── PHASE 5: Storage/Renewal Status ────────────────────────────────
    print(f"\n\n[PHASE 5] Storage & renewal status...")
    await asyncio.sleep(3)
    
    try:
        renewal_resp = await client.query_storage_renewal()
        print(f"  Storage renewal status: {json.dumps(renewal_resp.get('data', renewal_resp), indent=2)[:500]}")
    except Exception as e:
        print(f"  query_storage_renewal error: {e}")

    await asyncio.sleep(3)
    try:
        storage_info = await client.get_storage_info()
        print(f"  Storage info: {json.dumps(storage_info.get('data', storage_info), indent=2)[:500]}")
    except Exception as e:
        print(f"  get_storage_info error: {e}")

    await asyncio.sleep(3)
    try:
        storage_goods = await client.get_storage_goods()
        sg_data = storage_goods.get("data", storage_goods)
        print(f"  Storage goods catalog: {json.dumps(sg_data, indent=2)[:500]}")
    except Exception as e:
        print(f"  get_storage_goods error: {e}")

    # ─── PHASE 6: Cloud Phone Info (per-device billing detail) ──────────
    print(f"\n\n[PHASE 6] Per-device billing detail (padInfo endpoint)...")
    # Check 3 devices for detailed info
    for dev in all_devices[:3]:
        pad_code = dev.get("padCode", dev.get("code", ""))
        if not pad_code:
            continue
        await asyncio.sleep(3)
        try:
            info_resp = await client.cloud_phone_info(pad_code)
            info_data = info_resp.get("data", info_resp)
            print(f"\n  [{pad_code}] padInfo response:")
            if isinstance(info_data, dict):
                for k, v in sorted(info_data.items()):
                    print(f"    {k}: {v}")
            else:
                print(f"    {json.dumps(info_data, indent=2)[:400]}")
        except Exception as e:
            print(f"  [{pad_code}] padInfo error: {e}")

    # ─── PHASE 7: Image Version List ────────────────────────────────────
    print(f"\n\n[PHASE 7] Available image versions...")
    await asyncio.sleep(3)
    try:
        img_resp = await client.image_version_list()
        img_data = img_resp.get("data", [])
        if isinstance(img_data, list):
            print(f"  {len(img_data)} image versions available")
            for img in img_data[:5]:
                if isinstance(img, dict):
                    print(f"    {img.get('androidVersionName', img.get('name', '?'))} — {list(img.keys())}")
        else:
            print(f"  {json.dumps(img_data, indent=2)[:300]}")
    except Exception as e:
        print(f"  image_version_list error: {e}")

    # ─── PHASE 8: createMoneyOrder Dry-Run Recon ────────────────────────
    print(f"\n\n[PHASE 8] Probing createMoneyOrder endpoint (billing extension test)...")
    # We'll attempt to probe what parameters it expects by sending minimal payload
    await asyncio.sleep(3)
    try:
        probe_resp = await client.create_cloud_phone()
        print(f"  createMoneyOrder (empty): code={probe_resp.get('code')} msg={probe_resp.get('msg', '')[:200]}")
        if probe_resp.get("data"):
            print(f"    data: {json.dumps(probe_resp['data'], indent=2)[:300]}")
    except Exception as e:
        print(f"  createMoneyOrder probe error: {e}")

    # Probe createByTimingOrder  
    await asyncio.sleep(3)
    try:
        timing_probe = await client.create_timing_order()
        print(f"  createByTimingOrder (empty): code={timing_probe.get('code')} msg={timing_probe.get('msg', '')[:200]}")
    except Exception as e:
        print(f"  createByTimingOrder probe error: {e}")

    # ─── PHASE 9: Expiration Extension Test ─────────────────────────────
    print(f"\n\n[PHASE 9] Expiration extension feasibility analysis...")
    
    # Search for renewal/extension endpoints not yet in the client
    # Common VMOS Cloud renewal patterns from API docs
    extension_endpoints = [
        ("/vcpcloud/api/padApi/renewOrder", "POST", "Standard renewal"),
        ("/vcpcloud/api/padApi/renewPad", "POST", "Direct pad renewal"),
        ("/vcpcloud/api/padApi/extendOrder", "POST", "Order extension"),
        ("/vcpcloud/api/padApi/renewMoneyOrder", "POST", "Paid renewal order"),
        ("/vcpcloud/api/padApi/createRenewOrder", "POST", "Create renewal order"),
        ("/vcpcloud/api/padApi/queryRenewGoods", "GET", "Query renewal products"),
        ("/vcpcloud/api/padApi/getRenewGoodList", "GET", "Get renewal product list"),
        ("/vcpcloud/api/padApi/autoRenewOrder", "POST", "Auto-renew order"),
        ("/vcpcloud/api/padApi/selectRenewGoods", "GET", "Select renewal goods"),
    ]
    
    print(f"  Probing {len(extension_endpoints)} potential renewal/extension endpoints...\n")

    for endpoint, method, desc in extension_endpoints:
        await asyncio.sleep(3)
        try:
            if method == "POST":
                resp = await client._post(endpoint, {})
            else:
                resp = await client._get(endpoint, {})
            code = resp.get("code", "?")
            msg = resp.get("msg", "")[:120]
            data = resp.get("data")
            status = "FOUND" if code in (200, "200", 0, "0") else f"code={code}"
            print(f"  [{status:>12}] {endpoint}")
            print(f"               {desc} — msg: {msg}")
            if data and code in (200, "200", 0, "0"):
                print(f"               data: {json.dumps(data, indent=2)[:300]}")
        except Exception as e:
            print(f"  [{'ERROR':>12}] {endpoint} — {e}")

    # ─── PHASE 10: Summary ──────────────────────────────────────────────
    print(f"\n\n{'=' * 80}")
    print(f"  BILLING & EXPIRATION RECON SUMMARY")
    print(f"{'=' * 80}")
    print(f"  Total devices: {len(all_devices)}")
    
    # Categorize by expiration
    expiring_soon = [d for d in expiration_devices if d["daysRemaining"] is not None and d["daysRemaining"] <= 7]
    expired = [d for d in expiration_devices if d["daysRemaining"] is not None and d["daysRemaining"] <= 0]
    healthy = [d for d in expiration_devices if d["daysRemaining"] is not None and d["daysRemaining"] > 7]
    unknown = [d for d in expiration_devices if d["daysRemaining"] is None]
    
    print(f"  Expired: {len(expired)}")
    print(f"  Expiring within 7 days: {len(expiring_soon)}")
    print(f"  Healthy (>7 days): {len(healthy)}")
    print(f"  Unknown expiration: {len(unknown)}")
    print(f"\n  Billing fields discovered: {sorted(billing_fields_seen)}")

    if expiring_soon:
        print(f"\n  [!] DEVICES EXPIRING SOON:")
        for d in expiring_soon:
            print(f"      {d['padCode']} — {d['daysRemaining']}d remaining — expires {ts_to_str(d['expires'])}")

    print(f"\n{'=' * 80}")
    print(f"  RECON COMPLETE")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(main())
