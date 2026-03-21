#!/usr/bin/env python3
"""Validate machine-readable CI result snapshot JSON emitted by emit_ci_result_snapshot.py."""

from __future__ import annotations

import argparse
import json
import re
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from error_utils import emit_error


EXPECTED_GATES = {"mismatch", "severity_total", "severity_avg"}
ALLOWED_EVENT_NAMES = {
    "push",
    "pull_request",
    "workflow_dispatch",
    "schedule",
    "workflow_run",
    "repository_dispatch",
}
SCHEMA_VERSION_PATTERN = re.compile(r"^ci_result_snapshot\.v(\d+)$")
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{7,40}$")
RUN_ID_PATTERN = re.compile(r"^\d+$")
REPOSITORY_PATTERN = re.compile(r"^[^/\s]+/[^/\s]+$")
ACTOR_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
REF_PATTERN = re.compile(r"^refs/(heads|tags|pull)/.+$")
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


def validate_snapshot(payload: Any, path: Path, schema_version_min: int, schema_version_max: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{path}: root must be a JSON object"]

    schema_version = _expect_type(payload, "schema_version", str, errors, path)
    if isinstance(schema_version, str):
        m = SCHEMA_VERSION_PATTERN.match(schema_version)
        if not m:
            errors.append(
                f"{path}: schema_version must match 'ci_result_snapshot.vN' (got '{schema_version}')"
            )
        else:
            version_num = int(m.group(1))
            if version_num < schema_version_min or version_num > schema_version_max:
                errors.append(
                    f"{path}: schema_version v{version_num} is outside allowed range [v{schema_version_min}, v{schema_version_max}]"
                )

    _expect_type(payload, "label", str, errors, path)

    cases = _expect_type(payload, "cases", dict, errors, path)
    if isinstance(cases, dict):
        for key in ["total", "ok", "mismatch"]:
            value = cases.get(key)
            if not isinstance(value, int):
                errors.append(f"{path}: cases.{key} must be an integer")
            elif value < 0:
                errors.append(f"{path}: cases.{key} must be >= 0")

        total = cases.get("total")
        ok = cases.get("ok")
        mismatch = cases.get("mismatch")
        if all(isinstance(v, int) for v in (total, ok, mismatch)) and total != ok + mismatch:
            errors.append(f"{path}: cases.total must equal cases.ok + cases.mismatch")

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

    run_context = payload.get("run_context")
    if run_context is not None:
        if not isinstance(run_context, dict):
            errors.append(f"{path}: run_context must be an object when present")
        else:
            for key in [
                "run_id",
                "run_url",
                "run_attempt",
                "event_name",
                "sha",
                "ref",
                "repository",
                "actor",
                "workflow",
                "job",
            ]:
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

            if has_run_url and not str(run_url).startswith(("http://", "https://")):
                errors.append(f"{path}: run_context.run_url must start with http:// or https://")

            parsed_run_url = None
            if has_run_url:
                parsed_run_url = GITHUB_RUN_URL_PATTERN.match(str(run_url).strip())
                if not parsed_run_url:
                    errors.append(
                        f"{path}: run_context.run_url must match 'https://github.com/<owner>/<repo>/actions/runs/<run_id>[/attempts/<n>]'"
                    )

            run_id = run_context.get("run_id")
            if isinstance(run_id, str) and run_id.strip() and not RUN_ID_PATTERN.match(run_id.strip()):
                errors.append(f"{path}: run_context.run_id must be a numeric string when present")

            if has_run_id and has_run_url and parsed_run_url:
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
                errors.append(
                    f"{path}: run_context.repository must match '<owner>/<repo>' when present"
                )
            if parsed_run_url and isinstance(repository, str) and repository.strip():
                parsed_repository = parsed_run_url.group("repository")
                if repository.strip() != parsed_repository:
                    errors.append(
                        f"{path}: run_context.repository must match run_context.run_url repository segment"
                    )

            sha = run_context.get("sha")
            if isinstance(sha, str) and sha.strip() and not SHA_PATTERN.match(sha.strip()):
                errors.append(
                    f"{path}: run_context.sha must be a 7~40 hex string when present"
                )

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

            actor = run_context.get("actor")
            if isinstance(actor, str) and actor.strip() and not ACTOR_PATTERN.match(actor.strip()):
                errors.append(
                    f"{path}: run_context.actor must match '[A-Za-z0-9-]+' when present"
                )

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate CI result snapshot JSON schema")
    parser.add_argument("snapshot_json", type=Path, help="Path to CI snapshot JSON output")
    parser.add_argument(
        "--schema-version-min",
        type=int,
        default=1,
        help="Minimum supported schema version number (default: 1 for ci_result_snapshot.v1)",
    )
    parser.add_argument(
        "--schema-version-max",
        type=int,
        default=1,
        help="Maximum supported schema version number (default: 1 for ci_result_snapshot.v1)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.schema_version_min < 1 or args.schema_version_max < 1:
        emit_error("schema-version bounds must be >= 1")
        return 1
    if args.schema_version_min > args.schema_version_max:
        emit_error("schema-version bounds invalid: min must be <= max")
        return 1

    payload = load_json(args.snapshot_json)
    errors = validate_snapshot(
        payload,
        args.snapshot_json,
        schema_version_min=args.schema_version_min,
        schema_version_max=args.schema_version_max,
    )
    if errors:
        emit_error(
            "CI result snapshot schema validation failed:\n" + "\n".join(f"- {err}" for err in errors),
            hints=[
                f"input={args.snapshot_json}",
                f"supported_schema_versions=ci_result_snapshot.v{args.schema_version_min}..ci_result_snapshot.v{args.schema_version_max}",
                "expected_keys=schema_version,label,cases,severity,any_tripped,tripped_list,gate_details_compact,top1_mismatch,top_k_mismatches,summary_json,metric_json[,run_context(run_id,run_url,run_attempt,event_name,sha,ref,repository,actor,workflow,job)]",
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
