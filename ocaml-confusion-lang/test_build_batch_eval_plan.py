#!/usr/bin/env python3
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "build_batch_eval_plan.py"
TASK_SET = ROOT / "examples" / "task-set-v1.json"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    output = OUT / "batch-plan.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro,gpt-5-mini",
            "--prompt-conditions",
            "base,strict,base",
            "--repeats",
            "2",
            "--cheap-first",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    config = payload["config"]
    summary = payload["summary"]

    if config["models"] != ["gpt-5-mini", "gpt-5-pro"]:
        raise AssertionError(f"unexpected model order/dedup: {config['models']}")
    if config["prompt_conditions"] != ["base", "strict"]:
        raise AssertionError(f"unexpected prompt_condition dedup: {config['prompt_conditions']}")

    expected_total = 3 * 2 * 2 * 2  # tasks * models * conditions * repeats
    if summary["planned_runs_total"] != expected_total:
        raise AssertionError(
            f"expected planned_runs_total={expected_total}, got {summary['planned_runs_total']}"
        )

    capped = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--prompt-conditions",
            "base,strict",
            "--repeats",
            "2",
            "--max-total-runs",
            "10",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if capped.returncode == 0:
        raise AssertionError("expected max-total-runs cap violation to fail")

    print("OK: build_batch_eval_plan regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
