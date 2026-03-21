#!/usr/bin/env python3
"""Validate machine-readable summary JSON emitted by batch_report_summary.py."""

from __future__ import annotations

import argparse
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from error_utils import emit_error


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


def validate_payload(payload: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{path}: root must be a JSON object"]

    metadata = _expect_type(payload, "metadata", dict, errors, path)
    if isinstance(metadata, dict):
        for key in ["schema_version", "generated_at_utc", "input_report"]:
            if key not in metadata:
                errors.append(f"{path}: metadata missing '{key}'")

        task_set_lineage = metadata.get("task_set_lineage")
        if task_set_lineage is not None:
            if not isinstance(task_set_lineage, dict):
                errors.append(f"{path}: metadata.task_set_lineage must be an object when present")
            else:
                for key in ["task_set_id", "alias_set_id", "manifest_path"]:
                    if key in task_set_lineage:
                        value = task_set_lineage.get(key)
                        if not isinstance(value, str) or not value.strip():
                            errors.append(
                                f"{path}: metadata.task_set_lineage.{key} must be a non-empty string"
                            )

    _expect_type(payload, "title", str, errors, path)

    overview = _expect_type(payload, "overview", dict, errors, path)
    if isinstance(overview, dict):
        for key in [
            "total_cases",
            "ok_cases",
            "ok_cases_pct",
            "mismatch_cases",
            "mismatch_cases_pct",
            "include_diff",
            "taxonomy_weight_source",
            "cases_scope",
        ]:
            if key not in overview:
                errors.append(f"{path}: overview missing '{key}'")

        cases_scope = overview.get("cases_scope")
        if cases_scope is not None and cases_scope not in {"all", "mismatches-only"}:
            errors.append(
                f"{path}: overview.cases_scope must be one of ['all', 'mismatches-only']"
            )

    quality = _expect_type(payload, "quality_signals", dict, errors, path)
    if isinstance(quality, dict):
        for key in [
            "token_equivalent_true",
            "token_equivalent_pct",
            "ast_equivalent_true",
            "ast_equivalent_pct",
            "mismatch_severity_total",
            "mismatch_severity_avg",
        ]:
            if key not in quality:
                errors.append(f"{path}: quality_signals missing '{key}'")

    taxonomy = _expect_type(payload, "failure_taxonomy", dict, errors, path)
    if isinstance(taxonomy, dict):
        frequency = taxonomy.get("frequency")
        if not isinstance(frequency, dict):
            errors.append(f"{path}: failure_taxonomy.frequency must be an object")
        weighted = taxonomy.get("severity_weighted")
        if not isinstance(weighted, list):
            errors.append(f"{path}: failure_taxonomy.severity_weighted must be an array")
        else:
            for idx, row in enumerate(weighted):
                if not isinstance(row, dict):
                    errors.append(f"{path}: severity_weighted[{idx}] must be an object")
                    continue
                for key in ["tag", "count", "weight", "weighted_score"]:
                    if key not in row:
                        errors.append(f"{path}: severity_weighted[{idx}] missing '{key}'")

    top_mismatches = _expect_type(payload, "top_mismatches", list, errors, path)
    if isinstance(top_mismatches, list):
        for idx, row in enumerate(top_mismatches):
            if not isinstance(row, dict):
                errors.append(f"{path}: top_mismatches[{idx}] must be an object")
                continue
            for key in ["source", "failure_taxonomy", "severity"]:
                if key not in row:
                    errors.append(f"{path}: top_mismatches[{idx}] missing '{key}'")

    _expect_type(payload, "mismatch_sort", str, errors, path)

    gates = _expect_type(payload, "gates", dict, errors, path)
    if isinstance(gates, dict):
        for gate_key in ["mismatch", "severity_total", "severity_avg"]:
            gate_value = gates.get(gate_key)
            if not isinstance(gate_value, dict):
                errors.append(f"{path}: gates.{gate_key} must be an object")
                continue
            for key in ["enabled", "tripped"]:
                if key not in gate_value:
                    errors.append(f"{path}: gates.{gate_key} missing '{key}'")

    cases = _expect_type(payload, "cases", list, errors, path)
    if isinstance(cases, list):
        for idx, row in enumerate(cases):
            if not isinstance(row, dict):
                errors.append(f"{path}: cases[{idx}] must be an object")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate summary payload JSON schema")
    parser.add_argument("summary_json", type=Path, help="Path to summary JSON output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = load_json(args.summary_json)
    errors = validate_payload(payload, args.summary_json)
    if errors:
        emit_error(
            "Summary payload schema validation failed:\n" + "\n".join(f"- {err}" for err in errors),
            hints=[f"input={args.summary_json}", "expected_keys=metadata,title,overview,quality_signals,failure_taxonomy,top_mismatches,mismatch_sort,gates,cases"],
        )
        return 1
    print(f"OK: summary payload schema valid ({args.summary_json})")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, JSONDecodeError) as exc:
        emit_error(str(exc))
        raise SystemExit(1)
