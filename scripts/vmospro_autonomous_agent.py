#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vmos_titan.core.vmos_cloud_api import VMOSCloudClient


def get_env_var(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is not None and value.strip() == "":
        return default
    return value if value is not None else default


def build_client(args: argparse.Namespace) -> VMOSCloudClient:
    ak = args.ak or get_env_var("VMOS_CLOUD_AK")
    sk = args.sk or get_env_var("VMOS_CLOUD_SK")
    base_url = args.base_url or get_env_var("VMOS_CLOUD_BASE_URL", "https://api.vmoscloud.com")
    if not ak or not sk:
        raise RuntimeError("VMOS Cloud credentials not found. Set VMOS_CLOUD_AK and VMOS_CLOUD_SK.")
    return VMOSCloudClient(ak=ak, sk=sk, base_url=base_url)


def audit_dir(args: argparse.Namespace) -> Path:
    audit_dir = args.audit_dir or get_env_var("VMOS_AGENT_AUDIT_DIR", "~/.vmos_titan/agent_logs")
    path = Path(audit_dir).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def operator_identity(args: argparse.Namespace) -> str:
    operator = args.operator or get_env_var("VMOS_AGENT_OPERATOR")
    if not operator:
        raise RuntimeError("VMOS_AGENT_OPERATOR is required for audit logging and operator assertion.")
    return operator


def is_confirm_destructive() -> bool:
    raw = get_env_var("VMOS_AGENT_CONFIRM_DESTRUCTIVE", "false").lower()
    return raw in {"1", "true", "yes", "on"}


def audit_entry(log_path: Path, entry: dict) -> None:
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def serialize_response(value: object) -> object:
    try:
        json.dumps(value)
        return value
    except Exception:
        return repr(value)


def build_result(command: str, request: dict, response: object, error: str | None = None) -> dict:
    return {
        "timestamp": datetime.now().astimezone().isoformat(),
        "command": command,
        "request": request,
        "response": serialize_response(response),
        "error": error,
    }


async def run_command(args: argparse.Namespace) -> dict:
    client = build_client(args)
    command = args.command
    request = {}
    response = None
    error = None

    try:
        if command == "instance-list":
            request = {"page": args.page, "rows": args.rows}
            response = await client.instance_list(page=args.page, rows=args.rows)
        elif command == "switch-root":
            request = {
                "pad_codes": args.pad_codes,
                "enable": args.enable,
                "root_type": args.root_type,
                "package_name": args.package_name,
            }
            if args.enable and is_confirm_destructive() and not args.confirm:
                raise RuntimeError("Destructive root operation requires --confirm when VMOS_AGENT_CONFIRM_DESTRUCTIVE=true.")
            response = await client.switch_root(
                pad_codes=args.pad_codes,
                enable=args.enable,
                root_type=args.root_type,
                package_name=args.package_name,
            )
        elif command == "enable-adb":
            request = {"pad_codes": args.pad_codes, "enable": True}
            response = await client.enable_adb(pad_codes=args.pad_codes, enable=True)
        elif command == "get-adb-info":
            request = {"pad_code": args.pad_code, "enable": args.enable}
            response = await client.get_adb_info(pad_code=args.pad_code, enable=args.enable)
        elif command == "sync-cmd":
            request = {"pad_code": args.pad_code, "command": args.command_text, "timeout_sec": args.timeout}
            response = await client.sync_cmd(pad_code=args.pad_code, command=args.command_text, timeout_sec=args.timeout)
        elif command == "async-adb-cmd":
            request = {"pad_codes": args.pad_codes, "command": args.command_text}
            response = await client.async_adb_cmd(pad_codes=args.pad_codes, command=args.command_text)
        elif command == "screenshot":
            request = {"pad_codes": args.pad_codes}
            response = await client.screenshot(pad_codes=args.pad_codes)
        elif command == "get-preview-image":
            request = {"pad_codes": args.pad_codes}
            response = await client.get_preview_image(pad_codes=args.pad_codes)
        elif command == "modify-instance-properties":
            request = {"pad_codes": args.pad_codes, "properties": args.properties}
            response = await client.modify_instance_properties(pad_codes=args.pad_codes, properties=args.properties)
        elif command == "update-android-prop":
            request = {"pad_code": args.pad_code, "props": args.properties}
            if is_confirm_destructive() and not args.confirm:
                raise RuntimeError("Destructive property update requires --confirm when VMOS_AGENT_CONFIRM_DESTRUCTIVE=true.")
            response = await client.update_android_prop(pad_code=args.pad_code, props=args.properties)
        elif command == "restart":
            request = {"pad_codes": args.pad_codes}
            response = await client.instance_restart(pad_codes=args.pad_codes)
        elif command == "reset":
            request = {"pad_codes": args.pad_codes}
            if is_confirm_destructive() and not args.confirm:
                raise RuntimeError("Destructive reset requires --confirm when VMOS_AGENT_CONFIRM_DESTRUCTIVE=true.")
            response = await client.instance_reset(pad_codes=args.pad_codes)
        elif command == "smart-ip":
            request = {"pad_codes": args.pad_codes, "params": args.params}
            response = await client.set_smart_ip(pad_codes=args.pad_codes, **args.params)
        elif command == "set-gps":
            request = {
                "pad_codes": args.pad_codes,
                "lat": args.latitude,
                "lng": args.longitude,
                "altitude": args.altitude,
                "speed": args.speed,
                "bearing": args.bearing,
                "horizontal_accuracy": args.horizontal_accuracy,
            }
            response = await client.set_gps(
                pad_codes=args.pad_codes,
                lat=args.latitude,
                lng=args.longitude,
                altitude=args.altitude,
                speed=args.speed,
                bearing=args.bearing,
                horizontal_accuracy=args.horizontal_accuracy,
            )
        else:
            raise RuntimeError(f"Unknown command: {command}")
    except Exception as exc:
        error = str(exc)
        response = {"error": error}

    return build_result(command, request, response, error)


def parse_json_dict(value: str) -> dict:
    try:
        data = json.loads(value)
        if not isinstance(data, dict):
            raise ValueError("JSON value must be an object/dict.")
        return data
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"Invalid JSON: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VMOSPro Autonomous Agent CLI")
    parser.add_argument("command", choices=[
        "instance-list", "switch-root", "enable-adb", "get-adb-info",
        "sync-cmd", "async-adb-cmd", "screenshot", "get-preview-image",
        "modify-instance-properties", "update-android-prop", "restart",
        "reset", "smart-ip", "set-gps"
    ])
    parser.add_argument("--ak", help="VMOS Cloud access key")
    parser.add_argument("--sk", help="VMOS Cloud secret key")
    parser.add_argument("--base-url", help="VMOS Cloud base URL")
    parser.add_argument("--operator", help="Operator identity for audit logging")
    parser.add_argument("--audit-dir", help="Audit log directory")
    parser.add_argument("--confirm", action="store_true", help="Confirm destructive operation")

    parser.add_argument("--pad-code", help="Single pad code")
    parser.add_argument("--pad-codes", nargs="+", help="Multiple pad codes")
    parser.add_argument("--enable", type=lambda s: s.lower() in {"1","true","yes","on"}, default=True,
                        help="Enable/disable flag for switch-root or ADB operations")
    parser.add_argument("--root-type", type=int, default=1, help="Root type for switch-root (1=per-app, 0=global)")
    parser.add_argument("--package-name", default="com.android.shell", help="Package name for per-app root")
    parser.add_argument("--command-text", help="Shell command to run")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout seconds for sync command")
    parser.add_argument("--page", type=int, default=1, help="Page number for instance-list")
    parser.add_argument("--rows", type=int, default=10, help="Rows per page for instance-list")
    parser.add_argument("--properties", type=parse_json_dict, default={},
                        help='JSON object for properties, e.g. "{\"ro.product.model\": \"SM-G\"}"')
    parser.add_argument("--params", type=parse_json_dict, default={},
                        help='JSON object for smart-ip parameters')
    parser.add_argument("--latitude", type=float, help="GPS latitude")
    parser.add_argument("--longitude", type=float, help="GPS longitude")
    parser.add_argument("--altitude", type=float, help="GPS altitude")
    parser.add_argument("--speed", type=float, help="GPS speed")
    parser.add_argument("--bearing", type=float, help="GPS bearing")
    parser.add_argument("--horizontal-accuracy", type=float, help="GPS horizontal accuracy meters")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        operator_identity(args)
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1

    try:
        result = asyncio.run(run_command(args))
        audit_path = audit_dir(args) / f"{datetime.now().strftime('%Y%m%d')}.log"
        audit_entry(audit_path, {
            "timestamp": result["timestamp"],
            "operator": operator_identity(args),
            "command": args.command,
            "request": result["request"],
            "response": result["response"],
            "error": result["error"],
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["error"] is None else 2
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
