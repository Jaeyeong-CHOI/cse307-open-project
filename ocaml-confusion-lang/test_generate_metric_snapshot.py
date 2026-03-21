#!/usr/bin/env python3
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURE = ROOT / "examples" / "batch-summary-fixture-whitespace-linecount.json"
TASK_SET_FIXTURE = ROOT / "examples" / "task-set-fixture-whitespace-linecount-v1.json"
MISMATCH_TASK_SET = ROOT / "examples" / "task-set-v1.json"
SUMMARY_SCRIPT = ROOT / "scripts" / "batch_report_summary.py"
METRIC_SCRIPT = ROOT / "scripts" / "generate_metric_snapshot.py"
METRIC_VALIDATOR = ROOT / "scripts" / "validate_metric_schema.py"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    summary_json = OUT / "fixture.summary.json"
    metric_json = OUT / "fixture.metrics.json"

    subprocess.run(
        [
            "python3",
            str(SUMMARY_SCRIPT),
            str(FIXTURE),
            "--json-output",
            str(summary_json),
            "--top-k-mismatches",
            "0",
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    subprocess.run(
        [
            "python3",
            str(METRIC_SCRIPT),
            str(summary_json),
            "-o",
            str(metric_json),
            "--task-set-id",
            "fixture-task-set-v1",
            "--prompt-condition",
            "strict",
            "--model",
            "gpt-5.3-codex",
            "--task-set-json",
            str(TASK_SET_FIXTURE),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Intentional mismatch fixture should fail consistency checks.
    mismatch = subprocess.run(
        [
            "python3",
            str(METRIC_SCRIPT),
            str(summary_json),
            "--task-set-id",
            "cse307-task-set-v1",
            "--prompt-condition",
            "strict",
            "--model",
            "gpt-5.3-codex",
            "--task-set-json",
            str(MISMATCH_TASK_SET),
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert mismatch.returncode != 0, "expected mismatched task-set consistency check to fail"

    subprocess.run(
        ["python3", str(METRIC_VALIDATOR), str(metric_json)],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    payload = json.loads(metric_json.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    source_summary = payload.get("source_summary") or {}
    lineage = source_summary.get("task_set_lineage") or {}

    assert lineage.get("alias_set_id") == "fixture-alias-v1", lineage
    assert lineage.get("manifest_path") == "examples/manifest-v1.txt", lineage

    # fixture totals: total=3, ok=1, mismatch=2, ast_true=2,
    # line-gap proxy tags(line_count + whitespace)=2
    assert metrics["acr"] == 0.333, metrics
    assert metrics["prr"] == 0.667, metrics
    assert metrics["esr"] == 0.667, metrics
    assert metrics["mfb"] >= 0, metrics
    assert metrics["lgp"] == 0.667, metrics

    print("OK: metric snapshot generation regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
