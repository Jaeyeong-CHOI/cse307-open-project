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


def _run_validator(path: pathlib.Path, expect_ok: bool) -> None:
    result = subprocess.run(
        ["python3", str(VALIDATOR), str(path)],
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

    print("OK: summary payload schema regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
