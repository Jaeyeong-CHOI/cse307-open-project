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
            "run_url": "https://github.com/org/repo/actions/runs/123456789/attempts/2",
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

    invalid_cases_sum = dict(valid_payload)
    invalid_cases_sum["cases"] = {"total": 3, "ok": 2, "mismatch": 2}
    invalid_cases_sum_path = _write(OUT / "snapshot.invalid-cases-sum.json", invalid_cases_sum)
    bad_cases_sum = _run(invalid_cases_sum_path)
    if bad_cases_sum.returncode == 0:
        raise AssertionError("expected failure for cases total/ok/mismatch inconsistency")
    _assert_contains(
        bad_cases_sum.stderr,
        "cases.total must equal cases.ok + cases.mismatch",
    )

    invalid_cases_negative = dict(valid_payload)
    invalid_cases_negative["cases"] = {"total": -1, "ok": 0, "mismatch": 0}
    invalid_cases_negative_path = _write(OUT / "snapshot.invalid-cases-negative.json", invalid_cases_negative)
    bad_cases_negative = _run(invalid_cases_negative_path)
    if bad_cases_negative.returncode == 0:
        raise AssertionError("expected failure for negative case counters")
    _assert_contains(
        bad_cases_negative.stderr,
        "cases.total must be >= 0",
    )

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
        "run_context.run_url run_id segment must equal run_context.run_id",
    )

    invalid_run_url_shape = dict(valid_payload)
    invalid_run_url_shape["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://example.com/org/repo/actions/runs/123456789",
    }
    invalid_run_url_shape_path = _write(OUT / "snapshot.invalid-run-url-shape.json", invalid_run_url_shape)
    bad_run_url_shape = _run(invalid_run_url_shape_path)
    if bad_run_url_shape.returncode == 0:
        raise AssertionError("expected failure for invalid run_context.run_url shape")
    _assert_contains(
        bad_run_url_shape.stderr,
        "run_context.run_url must match 'https://github.com/<owner>/<repo>/actions/runs/<run_id>[/attempts/<n>]'",
    )

    invalid_run_id = dict(valid_payload)
    invalid_run_id["run_context"] = {
        "run_id": "run-123",
        "run_url": "https://github.com/org/repo/actions/runs/run-123",
    }
    invalid_run_id_path = _write(OUT / "snapshot.invalid-run-id.json", invalid_run_id)
    bad_run_id = _run(invalid_run_id_path)
    if bad_run_id.returncode == 0:
        raise AssertionError("expected failure for non-numeric run_id")
    _assert_contains(
        bad_run_id.stderr,
        "run_context.run_id must be a numeric string when present",
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

    invalid_run_attempt_missing_url_segment = dict(valid_payload)
    invalid_run_attempt_missing_url_segment["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789/attempts/2",
    }
    invalid_run_attempt_missing_url_segment_path = _write(
        OUT / "snapshot.invalid-run-attempt-missing-url-segment.json",
        invalid_run_attempt_missing_url_segment,
    )
    bad_run_attempt_missing_url_segment = _run(invalid_run_attempt_missing_url_segment_path)
    if bad_run_attempt_missing_url_segment.returncode == 0:
        raise AssertionError("expected failure when run_url has attempt segment but run_attempt is missing")
    _assert_contains(
        bad_run_attempt_missing_url_segment.stderr,
        "run_context.run_attempt must be provided when run_context.run_url contains '/attempts/<n>'",
    )

    invalid_run_attempt_missing_in_url = dict(valid_payload)
    invalid_run_attempt_missing_in_url["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "run_attempt": "2",
    }
    invalid_run_attempt_missing_in_url_path = _write(
        OUT / "snapshot.invalid-run-attempt-missing-in-url.json",
        invalid_run_attempt_missing_in_url,
    )
    bad_run_attempt_missing_in_url = _run(invalid_run_attempt_missing_in_url_path)
    if bad_run_attempt_missing_in_url.returncode == 0:
        raise AssertionError("expected failure when run_attempt is set but run_url lacks attempt segment")
    _assert_contains(
        bad_run_attempt_missing_in_url.stderr,
        "run_context.run_url must include '/attempts/<n>' when run_context.run_attempt is provided",
    )

    invalid_run_attempt_mismatch = dict(valid_payload)
    invalid_run_attempt_mismatch["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789/attempts/3",
        "run_attempt": "2",
    }
    invalid_run_attempt_mismatch_path = _write(
        OUT / "snapshot.invalid-run-attempt-mismatch.json",
        invalid_run_attempt_mismatch,
    )
    bad_run_attempt_mismatch = _run(invalid_run_attempt_mismatch_path)
    if bad_run_attempt_mismatch.returncode == 0:
        raise AssertionError("expected failure for run_attempt/run_url attempt mismatch")
    _assert_contains(
        bad_run_attempt_mismatch.stderr,
        "run_context.run_url attempt segment must equal run_context.run_attempt",
    )

    invalid_repository_format = dict(valid_payload)
    invalid_repository_format["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "repository": "org repo",
    }
    invalid_repository_format_path = _write(
        OUT / "snapshot.invalid-repository-format.json", invalid_repository_format
    )
    bad_repository_format = _run(invalid_repository_format_path)
    if bad_repository_format.returncode == 0:
        raise AssertionError("expected failure for invalid repository format")
    _assert_contains(
        bad_repository_format.stderr,
        "run_context.repository must match '<owner>/<repo>' when present",
    )

    invalid_repository_mismatch = dict(valid_payload)
    invalid_repository_mismatch["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "repository": "org/another-repo",
    }
    invalid_repository_mismatch_path = _write(
        OUT / "snapshot.invalid-repository-mismatch.json", invalid_repository_mismatch
    )
    bad_repository_mismatch = _run(invalid_repository_mismatch_path)
    if bad_repository_mismatch.returncode == 0:
        raise AssertionError("expected failure for run_context repository/run_url mismatch")
    _assert_contains(
        bad_repository_mismatch.stderr,
        "run_context.repository must match run_context.run_url repository segment",
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
        "run_context.ref must match 'refs/heads/*', 'refs/tags/*', or 'refs/pull/*' when present",
    )

    invalid_ref_namespace = dict(valid_payload)
    invalid_ref_namespace["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "ref": "refs/notes/main",
    }
    invalid_ref_namespace_path = _write(OUT / "snapshot.invalid-run-ref-namespace.json", invalid_ref_namespace)
    bad_ref_namespace = _run(invalid_ref_namespace_path)
    if bad_ref_namespace.returncode == 0:
        raise AssertionError("expected failure for unsupported run_context.ref namespace")
    _assert_contains(
        bad_ref_namespace.stderr,
        "run_context.ref must match 'refs/heads/*', 'refs/tags/*', or 'refs/pull/*' when present",
    )

    valid_pull_ref = dict(valid_payload)
    valid_pull_ref["run_context"] = dict(valid_payload["run_context"])
    valid_pull_ref["run_context"]["ref"] = "refs/pull/42/merge"
    valid_pull_ref_path = _write(OUT / "snapshot.valid-run-ref-pull.json", valid_pull_ref)
    ok_pull_ref = _run(valid_pull_ref_path)
    if ok_pull_ref.returncode != 0:
        raise AssertionError(f"expected success for refs/pull/* ref, got rc={ok_pull_ref.returncode}\n{ok_pull_ref.stderr}")

    valid_pull_request_target_event = dict(valid_payload)
    valid_pull_request_target_event["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "event_name": "pull_request_target",
    }
    valid_pull_request_target_event_path = _write(
        OUT / "snapshot.valid-event-name-pull-request-target.json", valid_pull_request_target_event
    )
    ok_pull_request_target_event = _run(valid_pull_request_target_event_path)
    if ok_pull_request_target_event.returncode != 0:
        raise AssertionError(
            f"expected success for run_context.event_name=pull_request_target, got rc={ok_pull_request_target_event.returncode}\n{ok_pull_request_target_event.stderr}"
        )

    invalid_event_name = dict(valid_payload)
    invalid_event_name["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "event_name": "manual",
    }
    invalid_event_name_path = _write(OUT / "snapshot.invalid-event-name.json", invalid_event_name)
    bad_event_name = _run(invalid_event_name_path)
    if bad_event_name.returncode == 0:
        raise AssertionError("expected failure for invalid run_context.event_name")
    _assert_contains(
        bad_event_name.stderr,
        "run_context.event_name must be one of",
    )

    invalid_actor = dict(valid_payload)
    invalid_actor["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/org/repo/actions/runs/123456789",
        "actor": "octo_cat",
    }
    invalid_actor_path = _write(OUT / "snapshot.invalid-actor.json", invalid_actor)
    bad_actor = _run(invalid_actor_path)
    if bad_actor.returncode == 0:
        raise AssertionError("expected failure for invalid run_context.actor")
    _assert_contains(
        bad_actor.stderr,
        "run_context.actor must match '[A-Za-z0-9-]+' when present",
    )

    invalid_workflow_too_long = dict(valid_payload)
    invalid_workflow_too_long["run_context"] = dict(valid_payload["run_context"])
    invalid_workflow_too_long["run_context"]["workflow"] = "w" * 129
    invalid_workflow_too_long_path = _write(
        OUT / "snapshot.invalid-workflow-too-long.json", invalid_workflow_too_long
    )
    bad_workflow_too_long = _run(invalid_workflow_too_long_path)
    if bad_workflow_too_long.returncode == 0:
        raise AssertionError("expected failure for too-long run_context.workflow")
    _assert_contains(
        bad_workflow_too_long.stderr,
        "run_context.workflow length must be <= 128 when present",
    )

    invalid_job_too_long = dict(valid_payload)
    invalid_job_too_long["run_context"] = dict(valid_payload["run_context"])
    invalid_job_too_long["run_context"]["job"] = "j" * 129
    invalid_job_too_long_path = _write(
        OUT / "snapshot.invalid-job-too-long.json", invalid_job_too_long
    )
    bad_job_too_long = _run(invalid_job_too_long_path)
    if bad_job_too_long.returncode == 0:
        raise AssertionError("expected failure for too-long run_context.job")
    _assert_contains(
        bad_job_too_long.stderr,
        "run_context.job length must be <= 128 when present",
    )


if __name__ == "__main__":
    main()
