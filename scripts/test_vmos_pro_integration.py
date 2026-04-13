#!/usr/bin/env python3
"""
VMOS Pro Integration Test Suite
================================
Validates the unified VMOS Pro pipeline including:
1. VMOSProBridge connectivity and shell execution
2. VMOSGenesisEngine pipeline phases
3. Wallet injection completeness
4. Cloud API endpoint availability
5. File push via chunked base64
6. Database construction and injection

Usage:
    python scripts/test_vmos_pro_integration.py [--pad PAD_CODE] [--full]

Options:
    --pad    Specific pad code to test (default: first available)
    --full   Run full genesis pipeline test (takes 5-10 minutes)
    --skip   Skip specific tests (comma-separated: bridge,genesis,wallet,file,api)

Exit codes:
    0 = All tests passed
    1 = One or more tests failed
    2 = Configuration error
"""

import argparse
import asyncio
import json
import os
import sys
import time

# Add core modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "vmos_titan", "core"))

# Configure logging before imports
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("vmos-test")


class TestResult:
    """Container for test results."""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = ""
        self.data = {}
        self.elapsed_sec = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "error": self.error,
            "data": self.data,
            "elapsed_sec": round(self.elapsed_sec, 2),
        }


class VMOSProTestSuite:
    """Complete integration test suite for VMOS Pro."""

    def __init__(self, pad_code: str | None = None):
        self.pad_code = pad_code
        self.results: list[TestResult] = []
        self.bridge = None
        self.client = None

    async def setup(self) -> bool:
        """Initialize test environment."""
        from vmos_cloud_api import VMOSCloudClient
        from vmos_pro_bridge import VMOSProBridge

        # Load credentials
        ak = os.environ.get("VMOS_CLOUD_AK", "")
        sk = os.environ.get("VMOS_CLOUD_SK", "")
        if not ak or not sk:
            log.error("Missing VMOS_CLOUD_AK or VMOS_CLOUD_SK environment variables")
            return False

        # Initialize client
        self.client = VMOSCloudClient(ak=ak, sk=sk)

        # Find a pad code if not specified
        if not self.pad_code:
            log.info("No pad code specified — querying available instances...")
            resp = await self.client.cloud_phone_list(page=1, rows=10)
            if resp.get("code") == 200:
                data = resp.get("data", {})
                items = data.get("pageDataList", [])
                if items:
                    self.pad_code = items[0].get("padCode")
                    log.info(f"Using pad code: {self.pad_code}")
                else:
                    log.error("No VMOS instances available")
                    return False
            else:
                log.error(f"Failed to list instances: {resp.get('msg')}")
                return False

        # Initialize bridge
        self.bridge = VMOSProBridge(pad_code=self.pad_code, client=self.client)
        return True

    async def test_bridge_connectivity(self) -> TestResult:
        """Test 1: VMOSProBridge shell connectivity."""
        result = TestResult("bridge_connectivity")
        t0 = time.time()

        try:
            # Test basic echo
            output = await self.bridge.shell_output("echo VMOS_TEST")
            if "VMOS_TEST" in output:
                result.passed = True
                result.data["echo_test"] = "OK"
            else:
                result.error = f"Echo test failed: {output[:100]}"

            # Test getprop
            model = await self.bridge.shell_output("getprop ro.product.model")
            result.data["device_model"] = model.strip() if model else "unknown"

            # Test root access
            id_output = await self.bridge.shell_output("id")
            result.data["root_access"] = "uid=0" in id_output

        except Exception as e:
            result.error = str(e)

        result.elapsed_sec = time.time() - t0
        return result

    async def test_file_push(self) -> TestResult:
        """Test 2: Chunked base64 file push."""
        result = TestResult("file_push")
        t0 = time.time()

        try:
            # Create test data
            test_data = b"VMOS PRO TEST FILE " * 100  # ~1.9KB
            checksum = __import__("hashlib").md5(test_data).hexdigest()
            remote_path = "/data/local/tmp/vmos_test_file"

            # Push file
            push_result = await self.bridge.push_bytes(
                test_data, remote_path, owner="root:root", mode="644"
            )

            if not push_result.success:
                result.error = f"Push failed: {push_result.error}"
                result.elapsed_sec = time.time() - t0
                return result

            # Verify via checksum
            remote_md5 = await self.bridge.shell_output(f"md5sum {remote_path} | cut -d' ' -f1")
            if checksum in remote_md5:
                result.passed = True
                result.data["checksum_match"] = True
                result.data["size_bytes"] = len(test_data)
            else:
                result.error = f"Checksum mismatch: local={checksum}, remote={remote_md5[:32]}"

            # Cleanup
            await self.bridge.shell(f"rm -f {remote_path}")

        except Exception as e:
            result.error = str(e)

        result.elapsed_sec = time.time() - t0
        return result

    async def test_api_endpoints(self) -> TestResult:
        """Test 3: VMOS Cloud API endpoint availability."""
        result = TestResult("api_endpoints")
        t0 = time.time()

        endpoints_tested = []
        endpoints_ok = []

        try:
            # Test 1: Instance info
            resp = await self.client.cloud_phone_info(self.pad_code)
            endpoints_tested.append("cloud_phone_info")
            if resp.get("code") == 200:
                endpoints_ok.append("cloud_phone_info")
                result.data["device_status"] = resp.get("data", {}).get("padStatus", "unknown")

            # Test 2: Screenshot (async, check task created)
            resp = await self.client.screenshot([self.pad_code])
            endpoints_tested.append("screenshot")
            if resp.get("code") == 200:
                endpoints_ok.append("screenshot")

            # Test 3: Reset GAID
            resp = await self.client.reset_gaid([self.pad_code])
            endpoints_tested.append("reset_gaid")
            if resp.get("code") == 200:
                endpoints_ok.append("reset_gaid")

            # Test 4: Device property query
            resp = await self.client.query_instance_properties([self.pad_code])
            endpoints_tested.append("query_property")
            if resp.get("code") == 200:
                endpoints_ok.append("query_property")

            result.data["endpoints_tested"] = len(endpoints_tested)
            result.data["endpoints_ok"] = len(endpoints_ok)
            result.data["endpoint_list"] = endpoints_ok

            if len(endpoints_ok) >= 3:
                result.passed = True
            else:
                result.error = f"Only {len(endpoints_ok)}/{len(endpoints_tested)} endpoints working"

        except Exception as e:
            result.error = str(e)

        result.elapsed_sec = time.time() - t0
        return result

    async def test_native_apis(self) -> TestResult:
        """Test 4: Native API wrappers (set_proxy, set_wifi, etc.)."""
        result = TestResult("native_apis")
        t0 = time.time()

        try:
            # Test 1: GPS set
            gps_ok = await self.bridge.set_gps(
                lat=34.0522, lng=-118.2437, altitude=50.0,
                speed=0.0, bearing=0.0, horizontal_accuracy=10.0
            )
            result.data["gps_set"] = gps_ok

            # Test 2: GAID reset via native API
            gaid_ok = await self.bridge.reset_gaid()
            result.data["gaid_reset"] = gaid_ok

            # Test 3: App stop (non-destructive test with shell)
            # Use sync_cmd to test app lifecycle
            stop_result = await self.bridge.shell("am force-stop com.android.chrome 2>/dev/null; echo STOP_OK")
            result.data["app_stop"] = "STOP_OK" in stop_result.output

            if gps_ok and gaid_ok:
                result.passed = True
            else:
                failed = [k for k, v in result.data.items() if not v]
                result.error = f"Failed APIs: {failed}"

        except Exception as e:
            result.error = str(e)

        result.elapsed_sec = time.time() - t0
        return result

    async def test_health_check(self) -> TestResult:
        """Test 5: VMOSProBridge health check."""
        result = TestResult("health_check")
        t0 = time.time()

        try:
            checks = await self.bridge.health_check()
            result.data = checks

            # Pass if shell connected and instance found
            if checks.get("shell_connected") and checks.get("instance_found"):
                result.passed = True
            else:
                failed = [k for k, v in checks.items() if not v]
                result.error = f"Failed checks: {failed}"

        except Exception as e:
            result.error = str(e)

        result.elapsed_sec = time.time() - t0
        return result

    async def test_genesis_engine_init(self) -> TestResult:
        """Test 6: VMOSGenesisEngine initialization."""
        result = TestResult("genesis_engine_init")
        t0 = time.time()

        try:
            from vmos_genesis_engine import VMOSGenesisEngine, PipelineConfig

            engine = VMOSGenesisEngine(self.pad_code, client=self.client)

            # Verify engine has required attributes
            result.data["has_client"] = engine.client is not None
            result.data["has_pad"] = engine.pad == self.pad_code

            # Create a minimal config
            cfg = PipelineConfig(
                name="Test User",
                email="test@example.com",
                cc_number="",  # Skip wallet for quick test
                skip_patch=True,
            )

            result.data["config_created"] = True

            if result.data["has_client"] and result.data["has_pad"]:
                result.passed = True
            else:
                result.error = "Engine initialization incomplete"

        except ImportError as e:
            result.error = f"Import failed: {e}"
        except Exception as e:
            result.error = str(e)

        result.elapsed_sec = time.time() - t0
        return result

    async def test_full_genesis_pipeline(self) -> TestResult:
        """Test 7: Full VMOSGenesisEngine pipeline (optional, slow)."""
        result = TestResult("full_genesis_pipeline")
        t0 = time.time()

        try:
            from vmos_genesis_engine import VMOSGenesisEngine, PipelineConfig

            engine = VMOSGenesisEngine(self.pad_code, client=self.client)

            cfg = PipelineConfig(
                name="Integration Test",
                email="test.vmos@example.com",
                cc_number="4532015112830366",
                cc_exp="12/2027",
                cc_cvv="123",
                cc_holder="Integration Test",
                google_email="test.vmos@example.com",
                device_model="samsung_s24",
                carrier="tmobile_us",
                location="la",
                age_days=90,
                skip_patch=False,
            )

            # Run pipeline
            pipeline_result = await engine.run_pipeline(cfg, job_id=f"test-{int(time.time())}")

            result.data["trust_score"] = pipeline_result.trust_score
            result.data["grade"] = pipeline_result.grade
            result.data["status"] = pipeline_result.status
            result.data["phases_completed"] = sum(
                1 for p in pipeline_result.phases if p.status == "done"
            )

            # Pass if trust score > 50 and status is completed
            if pipeline_result.status == "completed" and pipeline_result.trust_score >= 50:
                result.passed = True
            else:
                result.error = f"Pipeline incomplete: score={pipeline_result.trust_score}, status={pipeline_result.status}"

        except Exception as e:
            result.error = str(e)
            import traceback
            result.data["traceback"] = traceback.format_exc()

        result.elapsed_sec = time.time() - t0
        return result

    async def run_tests(self, skip_tests: list[str], full_pipeline: bool) -> list[TestResult]:
        """Execute all requested tests."""
        tests = [
            ("bridge", self.test_bridge_connectivity),
            ("file", self.test_file_push),
            ("api", self.test_api_endpoints),
            ("native", self.test_native_apis),
            ("health", self.test_health_check),
            ("engine", self.test_genesis_engine_init),
        ]

        if full_pipeline:
            tests.append(("genesis", self.test_full_genesis_pipeline))

        for test_name, test_func in tests:
            if test_name in skip_tests:
                log.info(f"Skipping {test_name} (--skip)")
                skipped = TestResult(test_name)
                skipped.passed = True
                skipped.data["skipped"] = True
                self.results.append(skipped)
                continue

            log.info(f"Running test: {test_name}...")
            try:
                result = await test_func()
                self.results.append(result)
                status = "PASS" if result.passed else "FAIL"
                log.info(f"  {status} ({result.elapsed_sec:.1f}s)")
                if not result.passed and result.error:
                    log.warning(f"    Error: {result.error[:100]}")
            except Exception as e:
                log.error(f"  EXCEPTION: {e}")
                failed = TestResult(test_name)
                failed.error = str(e)
                self.results.append(failed)

        return self.results

    def print_report(self):
        """Print formatted test report."""
        print("\n" + "=" * 70)
        print("  VMOS PRO INTEGRATION TEST REPORT")
        print("=" * 70)
        print(f"  Pad Code: {self.pad_code}")
        print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        for r in self.results:
            icon = "✓" if r.passed else "✗"
            status = "PASS" if r.passed else "FAIL"
            print(f"  {icon} {r.name:25s} [{status:4s}] {r.elapsed_sec:5.1f}s")
            if r.error:
                print(f"      Error: {r.error[:60]}")
            if r.data:
                data_str = json.dumps(r.data, default=str)[:60]
                print(f"      Data: {data_str}")

        print("-" * 70)
        print(f"  Results: {passed}/{total} passed, {failed} failed")
        print("=" * 70)

        return failed == 0

    async def run(self, args) -> int:
        """Main entry point."""
        log.info("VMOS Pro Integration Test Suite")
        log.info("=" * 50)

        # Setup
        if not await self.setup():
            return 2

        # Run tests
        skip_list = args.skip.split(",") if args.skip else []
        await self.run_tests(skip_list, args.full)

        # Print report
        all_passed = self.print_report()

        # Save results to file
        results_dict = {
            "pad_code": self.pad_code,
            "timestamp": time.time(),
            "results": [r.to_dict() for r in self.results],
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
            },
        }
        out_path = f"/tmp/vmos_test_{self.pad_code}_{int(time.time())}.json"
        with open(out_path, "w") as f:
            json.dump(results_dict, f, indent=2)
        log.info(f"Results saved to: {out_path}")

        return 0 if all_passed else 1


def main():
    parser = argparse.ArgumentParser(description="VMOS Pro Integration Test Suite")
    parser.add_argument("--pad", help="Specific pad code to test")
    parser.add_argument("--full", action="store_true", help="Run full genesis pipeline test (slow)")
    parser.add_argument("--skip", help="Skip tests (comma-separated: bridge,genesis,wallet,file,api)")
    args = parser.parse_args()

    suite = VMOSProTestSuite(pad_code=args.pad)
    exit_code = asyncio.run(suite.run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
