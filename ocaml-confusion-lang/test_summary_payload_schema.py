#!/usr/bin/env python3
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURE = ROOT / "examples" / "batch-summary-fixture-whitespace-linecount.json"
TASK_SET_FIXTURE = ROOT / "examples" / "task-set-v1.json"
SUMMARY_SCRIPT = ROOT / "scripts" / "batch_report_summary.py"
VALIDATOR = ROOT / "scripts" / "validate_summary_payload.py"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def _run_validator(path: pathlib.Path, expect_ok: bool, extra_args: list[str] | None = None) -> None:
    command = ["python3", str(VALIDATOR), str(path)]
    if extra_args:
        command.extend(extra_args)
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if expect_ok and result.returncode != 0:
        raise RuntimeError(f"expected validator to pass: {path}")
    if (not expect_ok) and result.returncode == 0:
        raise RuntimeError(f"expected validator to fail: {path}")


def main() -> int:
    summary_json = OUT / "fixture.summary.schema-check.json"

    subprocess.run(
        [
            "python3",
            str(SUMMARY_SCRIPT),
            str(FIXTURE),
            "--json-output",
            str(summary_json),
            "--task-set-json",
            str(TASK_SET_FIXTURE),
            "-o",
            str(OUT / "fixture.summary.schema-check.md"),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    _run_validator(summary_json, expect_ok=True)
    _run_validator(summary_json, expect_ok=True, extra_args=["--schema-version-min", "1", "--schema-version-max", "2"])

    payload_ok = json.loads(summary_json.read_text(encoding="utf-8"))
    gates = payload_ok.get("gates")
    if not isinstance(gates, dict):
        raise RuntimeError("expected 'gates' object in summary payload")
    if "mismatch" not in gates or "severity_total" not in gates or "severity_avg" not in gates:
        raise RuntimeError("expected mismatch/severity gate entries in summary payload")
    if "any_tripped" not in gates or "tripped_list" not in gates:
        raise RuntimeError("expected aggregate gate fields (any_tripped/tripped_list) in summary payload")
    aggregate_gate = gates.get("aggregate")
    if not isinstance(aggregate_gate, dict):
        raise RuntimeError("expected gates.aggregate object in summary payload")
    if (
        aggregate_gate.get("enabled") is not False
        or aggregate_gate.get("tripped") is not False
        or aggregate_gate.get("exit_code") != 4
    ):
        raise RuntimeError("expected gates.aggregate defaults to enabled=False tripped=False exit_code=4")

    invalid_summary = OUT / "fixture.summary.schema-check.invalid-lineage.json"
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    payload["metadata"]["task_set_lineage"]["manifest_path"] = ""
    invalid_summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    _run_validator(invalid_summary, expect_ok=False)

    invalid_scope_summary = OUT / "fixture.summary.schema-check.invalid-cases-scope.json"
    payload_scope = json.loads(summary_json.read_text(encoding="utf-8"))
    payload_scope["overview"]["cases_scope"] = "subset"
    invalid_scope_summary.write_text(json.dumps(payload_scope, ensure_ascii=False, indent=2), encoding="utf-8")

    _run_validator(invalid_scope_summary, expect_ok=False)

    invalid_schema_version_summary = OUT / "fixture.summary.schema-check.invalid-schema-version.json"
    payload_schema_version = json.loads(summary_json.read_text(encoding="utf-8"))
    payload_schema_version["metadata"]["schema_version"] = "v2"
    invalid_schema_version_summary.write_text(
        json.dumps(payload_schema_version, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _run_validator(invalid_schema_version_summary, expect_ok=False)
    _run_validator(
        invalid_schema_version_summary,
        expect_ok=True,
        extra_args=["--schema-version-min", "1", "--schema-version-max", "2"],
    )

    invalid_gate_summary = OUT / "fixture.summary.schema-check.invalid-gate-shape.json"
    payload_gate = json.loads(summary_json.read_text(encoding="utf-8"))
    payload_gate["gates"]["mismatch"] = True
    invalid_gate_summary.write_text(json.dumps(payload_gate, ensure_ascii=False, indent=2), encoding="utf-8")

    _run_validator(invalid_gate_summary, expect_ok=False)

    invalid_gate_list_summary = OUT / "fixture.summary.schema-check.invalid-gate-list.json"
    payload_gate_list = json.loads(summary_json.read_text(encoding="utf-8"))
    payload_gate_list["gates"]["tripped_list"] = ["unknown_gate"]
    invalid_gate_list_summary.write_text(
        json.dumps(payload_gate_list, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _run_validator(invalid_gate_list_summary, expect_ok=False)

    invalid_aggregate_summary = OUT / "fixture.summary.schema-check.invalid-aggregate.json"
    payload_aggregate = json.loads(summary_json.read_text(encoding="utf-8"))
    payload_aggregate["gates"]["aggregate"] = {"enabled": "nope", "tripped": "nope", "exit_code": "4"}
    invalid_aggregate_summary.write_text(
        json.dumps(payload_aggregate, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _run_validator(invalid_aggregate_summary, expect_ok=False)

    invalid_gate_consistency_summary = OUT / "fixture.summary.schema-check.invalid-gate-consistency.json"
    payload_gate_consistency = json.loads(summary_json.read_text(encoding="utf-8"))
    payload_gate_consistency["gates"]["mismatch"]["tripped"] = True
    payload_gate_consistency["gates"]["any_tripped"] = False
    payload_gate_consistency["gates"]["tripped_list"] = []
    invalid_gate_consistency_summary.write_text(
        json.dumps(payload_gate_consistency, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _run_validator(invalid_gate_consistency_summary, expect_ok=False)

    invalid_aggregate_consistency = OUT / "fixture.summary.schema-check.invalid-aggregate-consistency.json"
    payload_aggregate_consistency = json.loads(summary_json.read_text(encoding="utf-8"))
    payload_aggregate_consistency["gates"]["any_tripped"] = True
    payload_aggregate_consistency["gates"]["tripped_list"] = ["mismatch"]
    payload_aggregate_consistency["gates"]["mismatch"]["tripped"] = True
    payload_aggregate_consistency["gates"]["aggregate"]["enabled"] = True
    payload_aggregate_consistency["gates"]["aggregate"]["tripped"] = False
    invalid_aggregate_consistency.write_text(
        json.dumps(payload_aggregate_consistency, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _run_validator(invalid_aggregate_consistency, expect_ok=False)

    valid_run_context_summary = OUT / "fixture.summary.schema-check.valid-run-ref-pull.json"
    payload_valid_run_context = json.loads(summary_json.read_text(encoding="utf-8"))
    payload_valid_run_context["run_context"] = {
        "run_id": "123456789",
        "run_url": "https://github.com/Jaeyeong-CHOI/cse307-open-project/actions/runs/123456789",
        "run_attempt": "2",
        "event_name": "pull_request",
        "repository": "Jaeyeong-CHOI/cse307-open-project",
        "sha": "abcdef1",
        "ref": "refs/pull/42/merge",
        "workflow": "ocaml-confusion-lang-ci",
        "job": "summary-regression",
        "actor": "github-actions",
    }
    payload_valid_run_context["run_context"]["run_url"] = (
        "https://github.com/Jaeyeong-CHOI/cse307-open-project/actions/runs/123456789/attempts/2"
    )
    valid_run_context_summary.write_text(
        json.dumps(payload_valid_run_context, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _run_validator(valid_run_context_summary, expect_ok=True)

    invalid_run_context_summary = OUT / "fixture.summary.schema-check.invalid-run-context-workflow.json"
    payload_invalid_run_context = json.loads(valid_run_context_summary.read_text(encoding="utf-8"))
    payload_invalid_run_context["run_context"]["workflow"] = "x" * 129
    invalid_run_context_summary.write_text(
        json.dumps(payload_invalid_run_context, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _run_validator(invalid_run_context_summary, expect_ok=False)

    invalid_run_context_actor = OUT / "fixture.summary.schema-check.invalid-run-context-actor.json"
    payload_invalid_run_context_actor = json.loads(valid_run_context_summary.read_text(encoding="utf-8"))
    payload_invalid_run_context_actor["run_context"]["actor"] = "bad actor"
    invalid_run_context_actor.write_text(
        json.dumps(payload_invalid_run_context_actor, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _run_validator(invalid_run_context_actor, expect_ok=False)

    invalid_run_context_unknown = OUT / "fixture.summary.schema-check.invalid-run-context-unknown-key.json"
    payload_invalid_run_context_unknown = json.loads(valid_run_context_summary.read_text(encoding="utf-8"))
    payload_invalid_run_context_unknown["run_context"]["branch"] = "main"
    invalid_run_context_unknown.write_text(
        json.dumps(payload_invalid_run_context_unknown, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _run_validator(invalid_run_context_unknown, expect_ok=False)

    print("OK: summary payload schema regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
