#!/usr/bin/env python3
import json
import os
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
        capture_output=True,
        text=True,
    )
    assert mismatch.returncode != 0, "expected mismatched task-set consistency check to fail"

    mismatch_only_summary = OUT / "fixture.summary.mismatch-only.json"
    subprocess.run(
        [
            "python3",
            str(SUMMARY_SCRIPT),
            str(FIXTURE),
            "--json-output",
            str(mismatch_only_summary),
            "--only-mismatches",
            "--top-k-mismatches",
            "0",
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    mismatch_only_metric = subprocess.run(
        [
            "python3",
            str(METRIC_SCRIPT),
            str(mismatch_only_summary),
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
        check=False,
        capture_output=True,
        text=True,
    )
    mismatch_only_output = mismatch_only_metric.stderr + mismatch_only_metric.stdout
    assert mismatch_only_metric.returncode != 0, "expected mismatch-only summary to be rejected with --task-set-json"
    assert "without --only-mismatches" in mismatch_only_output
    assert "Traceback" not in mismatch_only_output

    lineage_mismatch_summary = OUT / "fixture.summary.lineage-mismatch.json"
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    payload.setdefault("metadata", {}).setdefault("task_set_lineage", {})["alias_set_id"] = "tampered-alias"
    lineage_mismatch_summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lineage_fail = subprocess.run(
        [
            "python3",
            str(METRIC_SCRIPT),
            str(lineage_mismatch_summary),
            "--task-set-id",
            "fixture-task-set-v1",
            "--prompt-condition",
            "strict",
            "--model",
            "gpt-5.3-codex",
            "--task-set-json",
            str(TASK_SET_FIXTURE),
            "--lineage-consistency",
            "fail",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    lineage_fail_output = lineage_fail.stderr + lineage_fail.stdout
    assert lineage_fail.returncode != 0, "expected lineage consistency fail mode to fail"
    assert "alias_set_id" in lineage_fail_output
    assert "Traceback" not in lineage_fail_output

    gh_annotated = subprocess.run(
        [
            "python3",
            str(METRIC_SCRIPT),
            str(lineage_mismatch_summary),
            "--task-set-id",
            "fixture-task-set-v1",
            "--prompt-condition",
            "strict",
            "--model",
            "gpt-5.3-codex",
            "--task-set-json",
            str(TASK_SET_FIXTURE),
            "--lineage-consistency",
            "fail",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GITHUB_ACTIONS": "true"},
    )
    gh_output = gh_annotated.stderr + gh_annotated.stdout
    assert gh_annotated.returncode != 0
    assert "::error::" in gh_output

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

    assert lineage.get("task_set_id") == "fixture-task-set-v1", lineage
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
