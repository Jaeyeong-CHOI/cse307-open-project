#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / "scripts" / "validate_ci_result_snapshot.py"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def _run(snapshot_path: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(snapshot_path), *extra_args],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n---\n{text}")


def main() -> None:
    valid_payload = {
        "schema_version": "ci_result_snapshot.v1",
        "label": "Full CI result snapshot",
        "cases": {"total": 3, "ok": 1, "mismatch": 2},
        "severity": {"total": 130, "avg": 65.0},
        "any_tripped": True,
        "tripped_list": ["mismatch", "severity_total", "severity_avg"],
        "gate_details_compact": "mismatch(enabled=True,tripped=True,observed_mismatch_cases=2)",
        "top1_mismatch": {
            "severity": 75,
            "taxonomy": "token_stream_mismatch",
            "source": "examples/collision-risk-case.py",
            "first_diff_line": 2,
            "first_token_diff_index": 8,
        },
        "top_k_mismatches": {
            "requested": "auto",
            "resolved": 3,
            "compact": "#1(...) | #2(...) | #3(...)",
        },
        "summary_json": "../docs/research/results/roundtrip-batch-v1.include-diff.summary.ci.json",
        "metric_json": "../docs/research/results/roundtrip-batch-v1.include-diff.metrics.ci.json",
        "run_context": {
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
    }

    valid_path = _write(OUT / "snapshot.valid.json", valid_payload)
    ok = _run(valid_path)
    if ok.returncode != 0:
        raise AssertionError(f"expected success, got rc={ok.returncode}\n{ok.stderr}")
    _assert_contains(ok.stdout, "OK: ci result snapshot schema valid")

    invalid_requested = dict(valid_payload)
    invalid_requested["top_k_mismatches"] = {
        "requested": "7",
        "resolved": 3,
        "compact": "#1(...)",
    }
    invalid_requested_path = _write(OUT / "snapshot.invalid-requested.json", invalid_requested)
    bad_requested = _run(invalid_requested_path)
    if bad_requested.returncode == 0:
        raise AssertionError("expected failure for invalid top_k_mismatches.requested")
    _assert_contains(
        bad_requested.stderr,
        "top_k_mismatches.requested must be in range [1, 3] when numeric",
    )

    invalid_any_tripped = dict(valid_payload)
    invalid_any_tripped["any_tripped"] = False
    invalid_any_tripped_path = _write(OUT / "snapshot.invalid-any-tripped.json", invalid_any_tripped)
    bad_any_tripped = _run(invalid_any_tripped_path)
    if bad_any_tripped.returncode == 0:
        raise AssertionError("expected failure for any_tripped/tripped_list inconsistency")
    _assert_contains(bad_any_tripped.stderr, "any_tripped must equal bool(tripped_list)")

    invalid_schema_version = dict(valid_payload)
    invalid_schema_version["schema_version"] = "ci_result_snapshot.v0"
    invalid_schema_version_path = _write(
        OUT / "snapshot.invalid-schema-version.json", invalid_schema_version
    )
    bad_schema_version = _run(invalid_schema_version_path)
    if bad_schema_version.returncode == 0:
        raise AssertionError("expected failure for invalid schema_version")
    _assert_contains(
        bad_schema_version.stderr,
        "schema_version v0 is outside allowed range [v1, v1]",
    )

    valid_v2 = dict(valid_payload)
    valid_v2["schema_version"] = "ci_result_snapshot.v2"
    valid_v2_path = _write(OUT / "snapshot.valid-v2.json", valid_v2)
    ok_v2 = _run(valid_v2_path, "--schema-version-max", "2")
    if ok_v2.returncode != 0:
        raise AssertionError(f"expected v2 success with max=2, got rc={ok_v2.returncode}\n{ok_v2.stderr}")
    _assert_contains(ok_v2.stdout, "OK: ci result snapshot schema valid")

    invalid_schema_format = dict(valid_payload)
    invalid_schema_format["schema_version"] = "ci_result_snapshot.vX"
    invalid_schema_format_path = _write(
        OUT / "snapshot.invalid-schema-format.json", invalid_schema_format
    )
    bad_schema_format = _run(invalid_schema_format_path)
    if bad_schema_format.returncode == 0:
        raise AssertionError("expected failure for invalid schema_version format")
    _assert_contains(
        bad_schema_format.stderr,
        "schema_version must match 'ci_result_snapshot.vN'",
    )

    invalid_run_context = dict(valid_payload)
    invalid_run_context["run_context"] = {"repository": ""}
    invalid_run_context_path = _write(OUT / "snapshot.invalid-run-context.json", invalid_run_context)
    bad_run_context = _run(invalid_run_context_path)
    if bad_run_context.returncode == 0:
        raise AssertionError("expected failure for invalid run_context.repository")
    _assert_contains(
        bad_run_context.stderr,
        "run_context.repository must be a non-empty string when present",
    )

    invalid_run_context_workflow = dict(valid_payload)
    invalid_run_context_workflow["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "workflow": "",
    }
    invalid_run_context_workflow_path = _write(
        OUT / "snapshot.invalid-run-context-workflow.json", invalid_run_context_workflow
    )
    bad_run_context_workflow = _run(invalid_run_context_workflow_path)
    if bad_run_context_workflow.returncode == 0:
        raise AssertionError("expected failure for invalid run_context.workflow")
    _assert_contains(
        bad_run_context_workflow.stderr,
        "run_context.workflow must be a non-empty string when present",
    )

    invalid_run_context_pair = dict(valid_payload)
    invalid_run_context_pair["run_context"] = {
        "run_id": "123456789",
        "event_name": "push",
    }
    invalid_run_context_pair_path = _write(
        OUT / "snapshot.invalid-run-context-pair.json", invalid_run_context_pair
    )
    bad_run_context_pair = _run(invalid_run_context_pair_path)
    if bad_run_context_pair.returncode == 0:
        raise AssertionError("expected failure when run_id/run_url are not provided together")
    _assert_contains(
        bad_run_context_pair.stderr,
        "run_context.run_id and run_context.run_url must be provided together",
    )

    invalid_run_context_traceability = dict(valid_payload)
    invalid_run_context_traceability["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/999999999",
    }
    invalid_run_context_traceability_path = _write(
        OUT / "snapshot.invalid-run-context-traceability.json",
        invalid_run_context_traceability,
    )
    bad_run_context_traceability = _run(invalid_run_context_traceability_path)
    if bad_run_context_traceability.returncode == 0:
        raise AssertionError("expected failure when run_url does not contain run_id")
    _assert_contains(
        bad_run_context_traceability.stderr,
        "run_context.run_url must include run_context.run_id for traceability",
    )

    invalid_run_attempt = dict(valid_payload)
    invalid_run_attempt["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "run_attempt": "two",
    }
    invalid_run_attempt_path = _write(OUT / "snapshot.invalid-run-attempt.json", invalid_run_attempt)
    bad_run_attempt = _run(invalid_run_attempt_path)
    if bad_run_attempt.returncode == 0:
        raise AssertionError("expected failure for non-numeric run_attempt")
    _assert_contains(
        bad_run_attempt.stderr,
        "run_context.run_attempt must be a numeric string when present",
    )

    invalid_sha = dict(valid_payload)
    invalid_sha["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "sha": "zz12",
    }
    invalid_sha_path = _write(OUT / "snapshot.invalid-run-sha.json", invalid_sha)
    bad_sha = _run(invalid_sha_path)
    if bad_sha.returncode == 0:
        raise AssertionError("expected failure for invalid run_context.sha")
    _assert_contains(
        bad_sha.stderr,
        "run_context.sha must be a 7~40 hex string when present",
    )

    invalid_ref = dict(valid_payload)
    invalid_ref["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "ref": "main",
    }
    invalid_ref_path = _write(OUT / "snapshot.invalid-run-ref.json", invalid_ref)
    bad_ref = _run(invalid_ref_path)
    if bad_ref.returncode == 0:
        raise AssertionError("expected failure for invalid run_context.ref")
    _assert_contains(
        bad_ref.stderr,
        "run_context.ref must start with 'refs/' when present",
    )


if __name__ == "__main__":
    main()
