#!/usr/bin/env python3
"""Validate machine-readable summary JSON emitted by batch_report_summary.py."""

from __future__ import annotations

import argparse
import json
import re
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from error_utils import emit_error
from run_context_schema import ALLOWED_EVENT_NAMES


SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{7,40}$")
RUN_ID_PATTERN = re.compile(r"^\d+$")
REPOSITORY_PATTERN = re.compile(r"^[^/\s]+/[^/\s]+$")
REF_PATTERN = re.compile(r"^refs/(heads|tags|pull)/.+$")
RUN_CONTEXT_TEXT_MAX_LEN = 128
GITHUB_RUN_URL_PATTERN = re.compile(
    r"^https://github\.com/(?P<repository>[^/\s]+/[^/\s]+)/actions/runs/(?P<run_id>\d+)(?:/attempts/(?P<attempt>\d+))?/?$"
)


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
        any_tripped = gates.get("any_tripped")
        if not isinstance(any_tripped, bool):
            errors.append(f"{path}: gates.any_tripped must be a boolean")

        tripped_list = gates.get("tripped_list")
        if not isinstance(tripped_list, list):
            errors.append(f"{path}: gates.tripped_list must be an array")
        else:
            for idx, gate_name in enumerate(tripped_list):
                if gate_name not in {"mismatch", "severity_total", "severity_avg"}:
                    errors.append(
                        f"{path}: gates.tripped_list[{idx}] must be one of ['mismatch', 'severity_total', 'severity_avg']"
                    )

        gate_tripped_map: dict[str, bool] = {}
        for gate_key in ["mismatch", "severity_total", "severity_avg"]:
            gate_value = gates.get(gate_key)
            if not isinstance(gate_value, dict):
                errors.append(f"{path}: gates.{gate_key} must be an object")
                continue
            for key in ["enabled", "tripped"]:
                if key not in gate_value:
                    errors.append(f"{path}: gates.{gate_key} missing '{key}'")
            tripped_value = gate_value.get("tripped")
            if isinstance(tripped_value, bool):
                gate_tripped_map[gate_key] = tripped_value

        if isinstance(any_tripped, bool) and isinstance(tripped_list, list):
            expected_any_tripped = bool(tripped_list)
            if any_tripped != expected_any_tripped:
                errors.append(f"{path}: gates.any_tripped must equal bool(gates.tripped_list)")

        if isinstance(tripped_list, list) and gate_tripped_map:
            expected_tripped_list = [
                gate_key for gate_key in ["mismatch", "severity_total", "severity_avg"] if gate_tripped_map.get(gate_key)
            ]
            if tripped_list != expected_tripped_list:
                errors.append(
                    f"{path}: gates.tripped_list must match tripped gate entries {expected_tripped_list}"
                )

        aggregate = gates.get("aggregate")
        if aggregate is not None:
            if not isinstance(aggregate, dict):
                errors.append(f"{path}: gates.aggregate must be an object")
            else:
                enabled = aggregate.get("enabled")
                if not isinstance(enabled, bool):
                    errors.append(f"{path}: gates.aggregate.enabled must be a boolean")
                tripped = aggregate.get("tripped")
                if not isinstance(tripped, bool):
                    errors.append(f"{path}: gates.aggregate.tripped must be a boolean")
                elif isinstance(enabled, bool) and isinstance(any_tripped, bool):
                    expected_aggregate_tripped = bool(enabled and any_tripped)
                    if tripped != expected_aggregate_tripped:
                        errors.append(
                            f"{path}: gates.aggregate.tripped must equal bool(gates.aggregate.enabled and gates.any_tripped)"
                        )
                exit_code = aggregate.get("exit_code")
                if not isinstance(exit_code, int):
                    errors.append(f"{path}: gates.aggregate.exit_code must be an integer")

    cases = _expect_type(payload, "cases", list, errors, path)
    if isinstance(cases, list):
        for idx, row in enumerate(cases):
            if not isinstance(row, dict):
                errors.append(f"{path}: cases[{idx}] must be an object")

    run_context = payload.get("run_context")
    if run_context is not None:
        if not isinstance(run_context, dict):
            errors.append(f"{path}: run_context must be an object when present")
        else:
            for key in ["run_id", "run_url", "run_attempt", "event_name", "repository", "sha", "ref", "workflow", "job"]:
                if key in run_context and (
                    not isinstance(run_context.get(key), str) or not run_context.get(key).strip()
                ):
                    errors.append(f"{path}: run_context.{key} must be a non-empty string when present")

            run_id = run_context.get("run_id")
            run_url = run_context.get("run_url")
            has_run_id = isinstance(run_id, str) and bool(run_id.strip())
            has_run_url = isinstance(run_url, str) and bool(run_url.strip())

            if has_run_id != has_run_url:
                errors.append(f"{path}: run_context.run_id and run_context.run_url must be provided together")

            parsed_run_url = None
            if has_run_url:
                parsed_run_url = GITHUB_RUN_URL_PATTERN.match(str(run_url).strip())
                if not parsed_run_url:
                    errors.append(
                        f"{path}: run_context.run_url must match 'https://github.com/<owner>/<repo>/actions/runs/<run_id>[/attempts/<n>] when present'"
                    )

            if has_run_id and not RUN_ID_PATTERN.match(str(run_id).strip()):
                errors.append(f"{path}: run_context.run_id must be a numeric string when present")

            if has_run_id and parsed_run_url:
                parsed_run_id = parsed_run_url.group("run_id")
                if str(run_id).strip() != parsed_run_id:
                    errors.append(f"{path}: run_context.run_url run_id segment must equal run_context.run_id")

            run_attempt = run_context.get("run_attempt")
            has_run_attempt = isinstance(run_attempt, str) and bool(run_attempt.strip())
            if has_run_attempt and not str(run_attempt).strip().isdigit():
                errors.append(f"{path}: run_context.run_attempt must be a numeric string when present")

            if parsed_run_url:
                parsed_attempt = parsed_run_url.group("attempt")
                if parsed_attempt and not has_run_attempt:
                    errors.append(
                        f"{path}: run_context.run_attempt must be provided when run_context.run_url contains '/attempts/<n>'"
                    )
                if has_run_attempt and not parsed_attempt:
                    errors.append(
                        f"{path}: run_context.run_url must include '/attempts/<n>' when run_context.run_attempt is provided"
                    )
                if parsed_attempt and has_run_attempt and str(run_attempt).strip() != parsed_attempt:
                    errors.append(
                        f"{path}: run_context.run_url attempt segment must equal run_context.run_attempt"
                    )

            repository = run_context.get("repository")
            if isinstance(repository, str) and repository.strip() and not REPOSITORY_PATTERN.match(repository.strip()):
                errors.append(f"{path}: run_context.repository must match '<owner>/<repo>' when present")
            if parsed_run_url and isinstance(repository, str) and repository.strip():
                parsed_repository = parsed_run_url.group("repository")
                if repository.strip() != parsed_repository:
                    errors.append(
                        f"{path}: run_context.repository must match run_context.run_url repository segment"
                    )

            sha = run_context.get("sha")
            if isinstance(sha, str) and sha.strip() and not SHA_PATTERN.match(sha.strip()):
                errors.append(f"{path}: run_context.sha must be a 7~40 hex string when present")

            ref = run_context.get("ref")
            if isinstance(ref, str) and ref.strip() and not REF_PATTERN.match(ref.strip()):
                errors.append(
                    f"{path}: run_context.ref must match 'refs/heads/*', 'refs/tags/*', or 'refs/pull/*' when present"
                )

            event_name = run_context.get("event_name")
            if isinstance(event_name, str) and event_name.strip() and event_name.strip() not in ALLOWED_EVENT_NAMES:
                errors.append(
                    f"{path}: run_context.event_name must be one of {sorted(ALLOWED_EVENT_NAMES)} when present"
                )

            for key in ["workflow", "job"]:
                value = run_context.get(key)
                if isinstance(value, str) and value.strip() and len(value.strip()) > RUN_CONTEXT_TEXT_MAX_LEN:
                    errors.append(
                        f"{path}: run_context.{key} length must be <= {RUN_CONTEXT_TEXT_MAX_LEN} when present"
                    )

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
