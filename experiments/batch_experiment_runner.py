#!/usr/bin/env python3
"""
Batch Experiment Runner — Executes commands on VMOS Cloud device with rate limiting.
Outputs JSON results for each experiment.
Usage: python3 batch_experiment_runner.py <experiment_file.json> <output_file.json>
"""
import json, os, sys, time, subprocess

AK = os.environ.get("VMOS_CLOUD_AK", "YOUR_VMOS_AK_HERE")
SK = os.environ.get("VMOS_CLOUD_SK", "YOUR_VMOS_SK_HERE")
PAD_CODE = os.environ.get("VMOS_PAD_CODE", "AC32010810392")
AGENT_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "scripts", "vmospro_autonomous_agent.py")
RATE_LIMIT_DELAY = 3.5  # seconds between commands


def run_cmd(command_text: str) -> str:
    """Execute a single command on the VMOS device and return output."""
    env = os.environ.copy()
    env["VMOS_CLOUD_AK"] = AK
    env["VMOS_CLOUD_SK"] = SK
    env["VMOS_AGENT_OPERATOR"] = "copilot"

    try:
        result = subprocess.run(
            ["python3", AGENT_SCRIPT, "sync-cmd",
             "--pad-code", PAD_CODE,
             "--command-text", command_text],
            capture_output=True, text=True, timeout=60, env=env,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        data = json.loads(result.stdout)
        output = data.get("response", {}).get("data", [{}])[0].get("errorMsg", "NO OUTPUT")
        return output.strip()
    except json.JSONDecodeError:
        return f"PARSE_ERROR: {result.stdout[:500]}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {str(e)}"


def run_batch(experiments: list) -> list:
    """Run a batch of experiments with rate limiting."""
    results = []
    total = len(experiments)
    for i, exp in enumerate(experiments):
        exp_id = exp.get("id", i + 1)
        cmd = exp.get("command", "")
        category = exp.get("category", "unknown")
        description = exp.get("description", "")

        print(f"[{i+1}/{total}] Exp #{exp_id}: {description[:60]}...", flush=True)
        output = run_cmd(cmd)

        results.append({
            "id": exp_id,
            "category": category,
            "description": description,
            "command": cmd,
            "output": output,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        })

        if i < total - 1:
            time.sleep(RATE_LIMIT_DELAY)

    return results


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 batch_experiment_runner.py <experiments.json> <output.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        experiments = json.load(f)

    print(f"Running {len(experiments)} experiments on device {PAD_CODE}...")
    results = run_batch(experiments)

    with open(sys.argv[2], "w") as f:
        json.dump(results, f, indent=2)

    success = sum(1 for r in results if "ERROR" not in r["output"] and "PARSE_ERROR" not in r["output"])
    print(f"\nComplete: {success}/{len(results)} successful. Output: {sys.argv[2]}")


if __name__ == "__main__":
    main()
