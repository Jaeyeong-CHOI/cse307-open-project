#!/usr/bin/env python3
"""Emit compact markdown snapshot lines for GitHub Actions step summary."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from error_utils import emit_error


TOP_K_AUTO = "auto"
TOP_K_MIN = 1
TOP_K_MAX = 3
SNAPSHOT_SCHEMA_VERSION = "ci_result_snapshot.v1"
SCHEMA_VERSION_PATTERN = r"^ci_result_snapshot\.v[1-9][0-9]*$"


def _mismatch_fields(item: Any) -> dict[str, Any]:
    top = item if isinstance(item, dict) else {}
    taxonomy = top.get("failure_taxonomy")
    taxonomy_value = "n/a"
    if isinstance(taxonomy, list) and taxonomy:
        taxonomy_value = taxonomy[0]

    return {
        "severity": top.get("severity", "n/a"),
        "taxonomy": taxonomy_value,
        "source": top.get("source", "n/a"),
        "first_diff_line": top.get("first_diff_line", "n/a"),
        "first_token_diff_index": top.get("first_token_diff_index", "n/a"),
    }


def _top1_fields(payload: dict[str, Any]) -> dict[str, Any]:
    mismatches = payload.get("top_mismatches")
    if not isinstance(mismatches, list) or not mismatches:
        return _mismatch_fields({})
    return _mismatch_fields(mismatches[0])


def _resolve_top_k(payload: dict[str, Any], requested: str) -> int:
    mismatches = payload.get("top_mismatches")
    mismatch_count = len(mismatches) if isinstance(mismatches, list) else 0

    if requested == TOP_K_AUTO:
        if mismatch_count <= 1:
            return 1
        if mismatch_count <= 3:
            return 2
        return 3

    top_k = int(requested)
    if top_k < TOP_K_MIN or top_k > TOP_K_MAX:
        raise ValueError(f"--top-k-mismatches must be between {TOP_K_MIN} and {TOP_K_MAX}")
    return top_k


def _topk_compact(payload: dict[str, Any], *, top_k: int) -> str:
    mismatches = payload.get("top_mismatches")
    if not isinstance(mismatches, list) or not mismatches:
        return "n/a"

    chunks: list[str] = []
    for idx, item in enumerate(mismatches[:top_k], start=1):
        top = _mismatch_fields(item)
        chunks.append(
            (
                f"#{idx}(severity={top['severity']}, "
                f"taxonomy={top['taxonomy']}, "
                f"source={top['source']}, "
                f"first_diff_line={top['first_diff_line']}, "
                f"first_token_diff_index={top['first_token_diff_index']})"
            )
        )

    remaining = len(mismatches) - min(top_k, len(mismatches))
    if remaining > 0:
        chunks.append(f"... (+{remaining} more)")

    return " | ".join(chunks)


def _format_tripped_list(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "[]"
    return str(value)


def _gate_details_compact(gates: dict[str, Any]) -> str:
    gate_names = ["mismatch", "severity_total", "severity_avg", "aggregate"]
    chunks: list[str] = []

    for name in gate_names:
        gate = gates.get(name)
        if not isinstance(gate, dict):
            continue

        enabled = gate.get("enabled", "n/a")
        tripped = gate.get("tripped", "n/a")
        chunk = f"{name}(enabled={enabled},tripped={tripped}"

        if "threshold" in gate:
            chunk += f",threshold={gate.get('threshold')}"
        if "observed" in gate:
            chunk += f",observed={gate.get('observed')}"
        if "observed_mismatch_cases" in gate:
            chunk += f",observed_mismatch_cases={gate.get('observed_mismatch_cases')}"
        if "exit_code" in gate:
            chunk += f",exit_code={gate.get('exit_code')}"

        chunk += ")"
        chunks.append(chunk)

    if not chunks:
        return "n/a"
    return " | ".join(chunks)


def _validate_summary_payload(payload: dict[str, Any], *, input_path: Path) -> None:
    errors: list[str] = []

    overview = payload.get("overview")
    if not isinstance(overview, dict):
        errors.append("overview must be an object")
    else:
        for key in ["total_cases", "ok_cases", "mismatch_cases", "mismatch_severity_total"]:
            if not isinstance(overview.get(key), int):
                errors.append(f"overview.{key} must be an integer")
        if not isinstance(overview.get("mismatch_severity_avg"), (int, float)):
            errors.append("overview.mismatch_severity_avg must be a number")

    gates = payload.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
    else:
        if not isinstance(gates.get("any_tripped"), bool):
            errors.append("gates.any_tripped must be a boolean")
        if not isinstance(gates.get("tripped_list"), list):
            errors.append("gates.tripped_list must be an array")

    top_mismatches = payload.get("top_mismatches")
    if top_mismatches is not None and not isinstance(top_mismatches, list):
        errors.append("top_mismatches must be an array when present")

    if errors:
        emit_error(
            "CI snapshot emit input validation failed:\n" + "\n".join(f"- {err}" for err in errors),
            hints=[
                f"input={input_path}",
                "required=overview(total/ok/mismatch/severity), gates(any_tripped,tripped_list)",
            ],
        )
        raise SystemExit(1)


def build_snapshot_payload(
    payload: dict[str, Any],
    *,
    label: str,
    summary_path: Path,
    metric_path: Path,
    schema_version: str = SNAPSHOT_SCHEMA_VERSION,
    top_k_mismatches: str = "1",
    run_context: dict[str, str] | None = None,
) -> dict[str, Any]:
    overview = payload.get("overview", {}) if isinstance(payload.get("overview"), dict) else {}
    gates = payload.get("gates", {}) if isinstance(payload.get("gates"), dict) else {}
    top1 = _top1_fields(payload)
    resolved_top_k = _resolve_top_k(payload, top_k_mismatches)

    snapshot = {
        "schema_version": schema_version,
        "label": label,
        "cases": {
            "total": overview.get("total_cases"),
            "ok": overview.get("ok_cases"),
            "mismatch": overview.get("mismatch_cases"),
        },
        "severity": {
            "total": overview.get("mismatch_severity_total"),
            "avg": overview.get("mismatch_severity_avg"),
        },
        "any_tripped": gates.get("any_tripped"),
        "tripped_list": gates.get("tripped_list"),
        "gate_details_compact": _gate_details_compact(gates),
        "top1_mismatch": top1,
        "top_k_mismatches": {
            "requested": top_k_mismatches,
            "resolved": resolved_top_k,
            "compact": _topk_compact(payload, top_k=resolved_top_k),
        },
        "summary_json": str(summary_path),
        "metric_json": str(metric_path),
    }
    if run_context:
        snapshot["run_context"] = run_context
    return snapshot


def build_snapshot_markdown(snapshot: dict[str, Any]) -> str:
    top1 = snapshot.get("top1_mismatch", {}) if isinstance(snapshot.get("top1_mismatch"), dict) else {}
    cases = snapshot.get("cases", {}) if isinstance(snapshot.get("cases"), dict) else {}
    severity = snapshot.get("severity", {}) if isinstance(snapshot.get("severity"), dict) else {}
    top_k = (
        snapshot.get("top_k_mismatches", {})
        if isinstance(snapshot.get("top_k_mismatches"), dict)
        else {}
    )

    resolved_top_k = top_k.get("resolved")
    run_context = snapshot.get("run_context") if isinstance(snapshot.get("run_context"), dict) else {}

    lines = [
        f"## {snapshot.get('label')}",
        (
            "- cases: "
            f"{cases.get('total')} total / "
            f"{cases.get('ok')} ok / "
            f"{cases.get('mismatch')} mismatch"
        ),
        f"- severity_total: {severity.get('total')} (avg={severity.get('avg')})",
        f"- any_tripped: {snapshot.get('any_tripped')}",
        f"- tripped_list: {_format_tripped_list(snapshot.get('tripped_list'))}",
        f"- gate_details: {snapshot.get('gate_details_compact')}",
        (
            "- top1_mismatch: "
            f"severity={top1.get('severity')}; "
            f"taxonomy={top1.get('taxonomy')}; "
            f"source={top1.get('source')}; "
            f"first_diff_line={top1.get('first_diff_line')}; "
            f"first_token_diff_index={top1.get('first_token_diff_index')}"
        ),
        (
            "- top_k_mismatches: "
            f"requested={top_k.get('requested')}; "
            f"resolved={resolved_top_k}"
        ),
        f"- top{resolved_top_k}_mismatches_compact: {top_k.get('compact')}",
        (
            "- run_context: "
            f"run_id={run_context.get('run_id', 'n/a')}; "
            f"run_url={run_context.get('run_url', 'n/a')}; "
            f"run_attempt={run_context.get('run_attempt', 'n/a')}; "
            f"event_name={run_context.get('event_name', 'n/a')}; "
            f"sha={run_context.get('sha', 'n/a')}; "
            f"ref={run_context.get('ref', 'n/a')}; "
            f"repository={run_context.get('repository', 'n/a')}; "
            f"actor={run_context.get('actor', 'n/a')}"
        ),
        f"- summary_json: `{snapshot.get('summary_json')}`",
        f"- metric_json: `{snapshot.get('metric_json')}`",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit compact CI snapshot markdown from summary JSON payload"
    )
    parser.add_argument("summary_json", type=Path, help="summary JSON payload path")
    parser.add_argument("--metric-json", required=True, type=Path, help="metric JSON path")
    parser.add_argument(
        "--json-output",
        type=Path,
        help="optional output path for machine-readable snapshot JSON",
    )
    parser.add_argument(
        "--label",
        default="CI result snapshot",
        help="section header label (default: CI result snapshot)",
    )
    parser.add_argument(
        "--schema-version",
        default=SNAPSHOT_SCHEMA_VERSION,
        help=(
            "snapshot schema version tag (default: ci_result_snapshot.v1, "
            "format: ci_result_snapshot.vN)"
        ),
    )
    parser.add_argument(
        "--top-k-mismatches",
        default="1",
        help="number of mismatch hints to compact into one line (1-3) or 'auto' (default: 1)",
    )
    parser.add_argument("--run-id", help="optional CI run id metadata")
    parser.add_argument("--run-url", help="optional CI run URL metadata")
    parser.add_argument("--run-attempt", help="optional CI run attempt metadata")
    parser.add_argument("--event-name", help="optional GitHub event name metadata")
    parser.add_argument("--sha", help="optional git SHA metadata")
    parser.add_argument("--ref", help="optional git ref metadata")
    parser.add_argument("--repository", help="optional repository metadata (owner/repo)")
    parser.add_argument("--actor", help="optional trigger actor metadata")
    args = parser.parse_args()

    if not re.match(SCHEMA_VERSION_PATTERN, args.schema_version):
        raise SystemExit(
            "--schema-version must match 'ci_result_snapshot.vN' where N is a positive integer"
        )

    if args.top_k_mismatches != TOP_K_AUTO:
        try:
            parsed_top_k = int(args.top_k_mismatches)
        except ValueError as exc:
            raise SystemExit(
                f"--top-k-mismatches must be an integer between {TOP_K_MIN} and {TOP_K_MAX} or '{TOP_K_AUTO}'"
            ) from exc
        if parsed_top_k < TOP_K_MIN or parsed_top_k > TOP_K_MAX:
            raise SystemExit(
                f"--top-k-mismatches must be between {TOP_K_MIN} and {TOP_K_MAX}"
            )

    payload = json.loads(args.summary_json.read_text(encoding="utf-8"))
    _validate_summary_payload(payload, input_path=args.summary_json)
    run_context = {
        key: value
        for key, value in {
            "run_id": args.run_id,
            "run_url": args.run_url,
            "run_attempt": args.run_attempt,
            "event_name": args.event_name,
            "sha": args.sha,
            "ref": args.ref,
            "repository": args.repository,
            "actor": args.actor,
        }.items()
        if isinstance(value, str) and value.strip()
    }
    snapshot = build_snapshot_payload(
        payload,
        label=args.label,
        summary_path=args.summary_json,
        metric_path=args.metric_json,
        schema_version=args.schema_version,
        top_k_mismatches=args.top_k_mismatches,
        run_context=run_context or None,
    )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(build_snapshot_markdown(snapshot))


if __name__ == "__main__":
    main()
