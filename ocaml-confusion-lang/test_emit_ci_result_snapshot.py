#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "emit_ci_result_snapshot.py"
OUT = ROOT / "_build"
OUT.mkdir(parents=True, exist_ok=True)


def _run(
    payload: dict,
    label: str,
    top_k_mismatches: int | str = 1,
    json_output: Path | None = None,
    run_context: dict[str, str] | None = None,
    schema_version: str | None = None,
    require_explicit_event_name: bool = False,
) -> str:
    summary = OUT / "tmp.emit-ci-summary.json"
    metric = OUT / "tmp.emit-ci-metric.json"
    summary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    metric.write_text("{}", encoding="utf-8")

    cmd = [
        sys.executable,
        str(SCRIPT),
        str(summary),
        "--metric-json",
        str(metric),
        "--label",
        label,
        "--top-k-mismatches",
        str(top_k_mismatches),
    ]
    if json_output is not None:
        cmd.extend(["--json-output", str(json_output)])
    if schema_version is not None:
        cmd.extend(["--schema-version", schema_version])
    if require_explicit_event_name:
        cmd.append("--require-explicit-event-name")
    if run_context is not None:
        for arg, key in [
            ("--run-id", "run_id"),
            ("--run-url", "run_url"),
            ("--run-attempt", "run_attempt"),
            ("--event-name", "event_name"),
            ("--sha", "sha"),
            ("--ref", "ref"),
            ("--repository", "repository"),
            ("--actor", "actor"),
            ("--workflow", "workflow"),
            ("--job", "job"),
        ]:
            value = run_context.get(key)
            if isinstance(value, str):
                cmd.extend([arg, value])

    proc = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return proc.stdout


def assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n---\n{text}")


def main() -> None:
    payload_with_mismatch = {
        "overview": {
            "total_cases": 3,
            "ok_cases": 1,
            "mismatch_cases": 2,
            "mismatch_severity_total": 130,
            "mismatch_severity_avg": 65.0,
        },
        "gates": {
            "mismatch": {"enabled": True, "tripped": True, "observed_mismatch_cases": 2},
            "severity_total": {"enabled": True, "threshold": 120, "observed": 130, "tripped": True},
            "severity_avg": {"enabled": True, "threshold": 60.0, "observed": 65.0, "tripped": True},
            "aggregate": {"enabled": True, "tripped": True, "exit_code": 4},
            "any_tripped": True,
            "tripped_list": ["mismatch", "severity_total", "severity_avg"],
        },
        "top_mismatches": [
            {
                "source": "examples/collision-risk-case.py",
                "failure_taxonomy": ["token_stream_mismatch", "token_substitution_mismatch"],
                "severity": 75,
                "first_diff_line": 2,
                "first_token_diff_index": 8,
            },
            {
                "source": "examples/linecount-risk-case.py",
                "failure_taxonomy": ["line_count_mismatch"],
                "severity": 55,
                "first_diff_line": 4,
                "first_token_diff_index": "n/a",
            },
            {
                "source": "examples/ast-risk-case.py",
                "failure_taxonomy": ["ast_equivalence_fail"],
                "severity": 40,
                "first_diff_line": 7,
                "first_token_diff_index": 11,
            },
            {
                "source": "examples/extra-risk-case.py",
                "failure_taxonomy": ["token_substitution_mismatch"],
                "severity": 35,
                "first_diff_line": 10,
                "first_token_diff_index": 14,
            },
        ],
    }

    snapshot_json = OUT / "tmp.emit-ci-snapshot.json"
    content = _run(
        payload_with_mismatch,
        "Full CI result snapshot",
        top_k_mismatches=2,
        json_output=snapshot_json,
        run_context={
            "run_id": "123456789",
            "run_url": "https://github.com/org/repo/actions/runs/123456789",
            "run_attempt": "2",
            "event_name": "workflow_dispatch",
            "sha": "abc123def456",
            "ref": "refs/heads/main",
            "repository": "org/repo",
            "actor": "octocat",
            "workflow": "ocaml-confusion-lang-ci",
            "job": "build-and-test",
        },
    )
    assert_contains(content, "## Full CI result snapshot")
    assert_contains(content, "- tripped_list: mismatch, severity_total, severity_avg")
    assert_contains(
        content,
        "- gate_details: mismatch(enabled=True,tripped=True,observed_mismatch_cases=2) | severity_total(enabled=True,tripped=True,threshold=120,observed=130) | severity_avg(enabled=True,tripped=True,threshold=60.0,observed=65.0) | aggregate(enabled=True,tripped=True,exit_code=4)",
    )
    assert_contains(
        content,
        "- top1_mismatch: severity=75; taxonomy=token_stream_mismatch; source=examples/collision-risk-case.py; first_diff_line=2; first_token_diff_index=8",
    )
    assert_contains(content, "- top_k_mismatches: requested=2; resolved=2")
    assert_contains(
        content,
        "- top2_mismatches_compact: #1(severity=75, taxonomy=token_stream_mismatch, source=examples/collision-risk-case.py, first_diff_line=2, first_token_diff_index=8) | #2(severity=55, taxonomy=line_count_mismatch, source=examples/linecount-risk-case.py, first_diff_line=4, first_token_diff_index=n/a) | ... (+2 more)",
    )
    assert_contains(
        content,
        "- run_context: run_id=123456789; run_url=https://github.com/org/repo/actions/runs/123456789; run_attempt=2; event_name=workflow_dispatch; event_name_source=provided; sha=abc123def456; ref=refs/heads/main; repository=org/repo; actor=octocat; workflow=ocaml-confusion-lang-ci; job=build-and-test",
    )

    snapshot_payload = json.loads(snapshot_json.read_text(encoding="utf-8"))
    if snapshot_payload.get("schema_version") != "ci_result_snapshot.v1":
        raise AssertionError("json snapshot schema_version mismatch")
    if snapshot_payload.get("label") != "Full CI result snapshot":
        raise AssertionError("json snapshot label mismatch")
    top_k_meta = snapshot_payload.get("top_k_mismatches", {})
    if top_k_meta.get("requested") != "2" or top_k_meta.get("resolved") != 2:
        raise AssertionError("json snapshot top-k metadata mismatch")
    if "#1(severity=75" not in str(top_k_meta.get("compact")):
        raise AssertionError("json snapshot compact mismatch summary missing")
    run_context_meta = snapshot_payload.get("run_context", {})
    if run_context_meta.get("run_id") != "123456789":
        raise AssertionError("json snapshot run_context.run_id mismatch")
    if run_context_meta.get("event_name") != "workflow_dispatch":
        raise AssertionError("json snapshot run_context.event_name mismatch")
    if run_context_meta.get("event_name_source") != "provided":
        raise AssertionError("json snapshot run_context.event_name_source mismatch")
    if run_context_meta.get("repository") != "org/repo":
        raise AssertionError("json snapshot run_context.repository mismatch")
    if run_context_meta.get("actor") != "octocat":
        raise AssertionError("json snapshot run_context.actor mismatch")
    if run_context_meta.get("workflow") != "ocaml-confusion-lang-ci":
        raise AssertionError("json snapshot run_context.workflow mismatch")
    if run_context_meta.get("job") != "build-and-test":
        raise AssertionError("json snapshot run_context.job mismatch")

    payload_no_mismatch = {
        "overview": {
            "total_cases": 1,
            "ok_cases": 1,
            "mismatch_cases": 0,
            "mismatch_severity_total": 0,
            "mismatch_severity_avg": 0.0,
        },
        "gates": {"any_tripped": False, "tripped_list": []},
        "top_mismatches": [],
    }
    no_mm = _run(payload_no_mismatch, "Lightweight CI result snapshot", top_k_mismatches=3)
    assert_contains(no_mm, "- tripped_list: []")
    assert_contains(no_mm, "- gate_details: n/a")
    assert_contains(
        no_mm,
        "- top1_mismatch: severity=n/a; taxonomy=n/a; source=n/a; first_diff_line=n/a; first_token_diff_index=n/a",
    )
    assert_contains(no_mm, "- top_k_mismatches: requested=3; resolved=3")
    assert_contains(no_mm, "- top3_mismatches_compact: n/a")

    auto_mm = _run(payload_with_mismatch, "Auto top-k snapshot", top_k_mismatches="auto")
    assert_contains(auto_mm, "## Auto top-k snapshot")
    assert_contains(auto_mm, "- top_k_mismatches: requested=auto; resolved=3")
    assert_contains(
        auto_mm,
        "- top3_mismatches_compact: #1(severity=75, taxonomy=token_stream_mismatch, source=examples/collision-risk-case.py, first_diff_line=2, first_token_diff_index=8) | #2(severity=55, taxonomy=line_count_mismatch, source=examples/linecount-risk-case.py, first_diff_line=4, first_token_diff_index=n/a) | #3(severity=40, taxonomy=ast_equivalence_fail, source=examples/ast-risk-case.py, first_diff_line=7, first_token_diff_index=11) | ... (+1 more)",
    )

    invalid_summary = OUT / "tmp.emit-ci-summary.invalid.json"
    invalid_metric = OUT / "tmp.emit-ci-metric.invalid.json"
    invalid_summary.write_text(json.dumps(payload_with_mismatch, ensure_ascii=False), encoding="utf-8")
    invalid_metric.write_text("{}", encoding="utf-8")
    invalid = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(invalid_summary),
            "--metric-json",
            str(invalid_metric),
            "--label",
            "Invalid top-k snapshot",
            "--top-k-mismatches",
            "4",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if invalid.returncode == 0:
        raise AssertionError("expected non-zero exit for --top-k-mismatches=4")
    assert_contains(invalid.stderr, "--top-k-mismatches must be between 1 and 3")

    auto_no_mm = _run(payload_no_mismatch, "Auto no mismatch snapshot", top_k_mismatches="auto")
    assert_contains(auto_no_mm, "## Auto no mismatch snapshot")
    assert_contains(auto_no_mm, "- top_k_mismatches: requested=auto; resolved=1")
    assert_contains(auto_no_mm, "- top1_mismatches_compact: n/a")

    snapshot_v2_json = OUT / "tmp.emit-ci-snapshot.v2.json"
    _run(
        payload_with_mismatch,
        "Schema v2 snapshot",
        json_output=snapshot_v2_json,
        schema_version="ci_result_snapshot.v2",
    )
    snapshot_v2_payload = json.loads(snapshot_v2_json.read_text(encoding="utf-8"))
    if snapshot_v2_payload.get("schema_version") != "ci_result_snapshot.v2":
        raise AssertionError("json snapshot schema_version override mismatch")

    invalid_schema_summary = OUT / "tmp.emit-ci-summary.invalid-schema.json"
    invalid_schema_metric = OUT / "tmp.emit-ci-metric.invalid-schema.json"
    invalid_schema_summary.write_text(json.dumps(payload_with_mismatch, ensure_ascii=False), encoding="utf-8")
    invalid_schema_metric.write_text("{}", encoding="utf-8")
    invalid_schema = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(invalid_schema_summary),
            "--metric-json",
            str(invalid_schema_metric),
            "--label",
            "Invalid schema snapshot",
            "--schema-version",
            "ci_result_snapshot.vX",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if invalid_schema.returncode == 0:
        raise AssertionError("expected non-zero exit for invalid --schema-version")
    assert_contains(
        invalid_schema.stderr,
        "--schema-version must match 'ci_result_snapshot.vN' where N is a positive integer",
    )

    invalid_shape_summary = OUT / "tmp.emit-ci-summary.invalid-shape.json"
    invalid_shape_metric = OUT / "tmp.emit-ci-metric.invalid-shape.json"
    invalid_shape_payload = dict(payload_with_mismatch)
    invalid_shape_payload["overview"] = {
        "total_cases": 3,
        "ok_cases": 1,
        # mismatch_cases intentionally missing for fail-fast validation
        "mismatch_severity_total": 130,
        "mismatch_severity_avg": 65.0,
    }
    invalid_shape_summary.write_text(
        json.dumps(invalid_shape_payload, ensure_ascii=False),
        encoding="utf-8",
    )
    invalid_shape_metric.write_text("{}", encoding="utf-8")
    invalid_shape = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(invalid_shape_summary),
            "--metric-json",
            str(invalid_shape_metric),
            "--label",
            "Invalid shape snapshot",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if invalid_shape.returncode == 0:
        raise AssertionError("expected non-zero exit for invalid summary payload shape")
    assert_contains(invalid_shape.stderr, "CI snapshot emit input validation failed")
    assert_contains(invalid_shape.stderr, "overview.mismatch_cases must be an integer")

    unknown_default_content = _run(
        payload_with_mismatch,
        "Unknown default event snapshot",
        run_context={
            "run_id": "987654321",
            "run_url": "https://github.com/org/repo/actions/runs/987654321",
            "run_attempt": "1",
            "repository": "org/repo",
            "actor": "octocat",
            "workflow": "ocaml-confusion-lang-ci",
            "job": "build-and-test",
        },
    )
    assert_contains(unknown_default_content, "event_name=unknown")
    assert_contains(unknown_default_content, "event_name_source=derived")

    strict_missing_event = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(invalid_summary),
            "--metric-json",
            str(invalid_metric),
            "--label",
            "Strict missing event snapshot",
            "--require-explicit-event-name",
            "--run-id",
            "987654321",
            "--run-url",
            "https://github.com/org/repo/actions/runs/987654321",
            "--run-attempt",
            "1",
            "--repository",
            "org/repo",
            "--actor",
            "octocat",
            "--workflow",
            "ocaml-confusion-lang-ci",
            "--job",
            "build-and-test",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if strict_missing_event.returncode == 0:
        raise AssertionError("expected non-zero exit for strict mode without --event-name")
    assert_contains(
        strict_missing_event.stderr,
        "--require-explicit-event-name requires --event-name when run_context metadata is provided",
    )

    invalid_event = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(invalid_summary),
            "--metric-json",
            str(invalid_metric),
            "--label",
            "Invalid event snapshot",
            "--event-name",
            "manual",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if invalid_event.returncode == 0:
        raise AssertionError("expected non-zero exit for invalid --event-name")
    assert_contains(invalid_event.stderr, "--event-name must be one of")


if __name__ == "__main__":
    main()
