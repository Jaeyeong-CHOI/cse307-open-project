#!/usr/bin/env python3
"""Validate machine-readable CI result snapshot JSON emitted by emit_ci_result_snapshot.py."""

from __future__ import annotations

import argparse
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from error_utils import emit_error


EXPECTED_GATES = {"mismatch", "severity_total", "severity_avg"}
EXPECTED_SCHEMA_VERSION = "ci_result_snapshot.v1"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _expect_type(payload: dict[str, Any], key: str, expected: type, errors: list[str], path: Path) -> Any:
    value = payload.get(key)
    if value is None:
        errors.append(f"{path}: missing required key '{key}'")
        return None
    if not isinstance(value, expected):
        errors.append(f"{path}: key '{key}' must be {expected.__name__}")
        return None
    return value


def validate_snapshot(payload: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{path}: root must be a JSON object"]

    schema_version = _expect_type(payload, "schema_version", str, errors, path)
    if isinstance(schema_version, str) and schema_version != EXPECTED_SCHEMA_VERSION:
        errors.append(
            f"{path}: schema_version must be '{EXPECTED_SCHEMA_VERSION}'"
        )

    _expect_type(payload, "label", str, errors, path)

    cases = _expect_type(payload, "cases", dict, errors, path)
    if isinstance(cases, dict):
        for key in ["total", "ok", "mismatch"]:
            value = cases.get(key)
            if not isinstance(value, int):
                errors.append(f"{path}: cases.{key} must be an integer")

    severity = _expect_type(payload, "severity", dict, errors, path)
    if isinstance(severity, dict):
        total = severity.get("total")
        avg = severity.get("avg")
        if not isinstance(total, int):
            errors.append(f"{path}: severity.total must be an integer")
        if not isinstance(avg, (int, float)):
            errors.append(f"{path}: severity.avg must be a number")

    any_tripped = payload.get("any_tripped")
    if not isinstance(any_tripped, bool):
        errors.append(f"{path}: any_tripped must be a boolean")

    tripped_list = payload.get("tripped_list")
    if not isinstance(tripped_list, list):
        errors.append(f"{path}: tripped_list must be an array")
    else:
        for idx, gate_name in enumerate(tripped_list):
            if gate_name not in EXPECTED_GATES:
                errors.append(
                    f"{path}: tripped_list[{idx}] must be one of ['mismatch', 'severity_total', 'severity_avg']"
                )

    gate_details = payload.get("gate_details_compact")
    if not isinstance(gate_details, str) or not gate_details.strip():
        errors.append(f"{path}: gate_details_compact must be a non-empty string")

    top1 = _expect_type(payload, "top1_mismatch", dict, errors, path)
    if isinstance(top1, dict):
        for key in ["severity", "taxonomy", "source", "first_diff_line", "first_token_diff_index"]:
            if key not in top1:
                errors.append(f"{path}: top1_mismatch missing '{key}'")

    top_k = _expect_type(payload, "top_k_mismatches", dict, errors, path)
    if isinstance(top_k, dict):
        requested = top_k.get("requested")
        resolved = top_k.get("resolved")
        compact = top_k.get("compact")

        if not isinstance(requested, str):
            errors.append(f"{path}: top_k_mismatches.requested must be a string")
        elif requested != "auto":
            try:
                requested_int = int(requested)
            except ValueError:
                errors.append(f"{path}: top_k_mismatches.requested must be 'auto' or integer string in range [1, 3]")
            else:
                if requested_int < 1 or requested_int > 3:
                    errors.append(f"{path}: top_k_mismatches.requested must be in range [1, 3] when numeric")

        if not isinstance(resolved, int) or resolved < 1 or resolved > 3:
            errors.append(f"{path}: top_k_mismatches.resolved must be an integer in range [1, 3]")

        if not isinstance(compact, str):
            errors.append(f"{path}: top_k_mismatches.compact must be a string")

    summary_json = payload.get("summary_json")
    metric_json = payload.get("metric_json")
    if not isinstance(summary_json, str) or not summary_json.strip():
        errors.append(f"{path}: summary_json must be a non-empty string")
    if not isinstance(metric_json, str) or not metric_json.strip():
        errors.append(f"{path}: metric_json must be a non-empty string")

    if isinstance(any_tripped, bool) and isinstance(tripped_list, list):
        if any_tripped != bool(tripped_list):
            errors.append(f"{path}: any_tripped must equal bool(tripped_list)")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate CI result snapshot JSON schema")
    parser.add_argument("snapshot_json", type=Path, help="Path to CI snapshot JSON output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = load_json(args.snapshot_json)
    errors = validate_snapshot(payload, args.snapshot_json)
    if errors:
        emit_error(
            "CI result snapshot schema validation failed:\n" + "\n".join(f"- {err}" for err in errors),
            hints=[
                f"input={args.snapshot_json}",
                "expected_keys=schema_version,label,cases,severity,any_tripped,tripped_list,gate_details_compact,top1_mismatch,top_k_mismatches,summary_json,metric_json",
            ],
        )
        return 1

    print(f"OK: ci result snapshot schema valid ({args.snapshot_json})")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, JSONDecodeError) as exc:
        emit_error(str(exc))
        raise SystemExit(1)
