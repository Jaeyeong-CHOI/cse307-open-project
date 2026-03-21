#!/usr/bin/env python3
"""Generate human-friendly summaries from batch-roundtrip-report JSON."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from error_utils import emit_error

SCRIPT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = SCRIPT_DIR.parent / "examples" / "weights"

TAXONOMY_WEIGHTS: dict[str, int] = {
    "token_stream_mismatch": 40,
    "token_substitution_mismatch": 35,
    "ast_parse_error": 30,
    "line_count_mismatch": 10,
    "whitespace_or_blankline_drift": 5,
}
DEFAULT_TAXONOMY_WEIGHT = 15


def pct(n: int, d: int) -> str:
    if d == 0:
        return "0.0%"
    return f"{(n / d) * 100:.1f}%"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_non_negative_int_field(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"batch report key '{key}' must be an integer")
    if value < 0:
        raise ValueError(f"batch report key '{key}' must be >= 0")
    return value


def validate_batch_report_shape(report: dict[str, Any], input_path: Path) -> None:
    required_root_keys = {"total_cases", "ok_cases", "mismatch_cases", "cases"}
    missing = sorted(required_root_keys.difference(report.keys()))
    if missing:
        raise ValueError(
            f"batch report missing required key(s): {', '.join(missing)}"
        )

    cases = report.get("cases")
    if not isinstance(cases, list):
        raise ValueError("batch report key 'cases' must be an array")

    required_case_keys = {
        "source",
        "status",
        "exact_match",
        "token_equivalent",
        "ast_equivalent",
        "failure_taxonomy",
    }
    allowed_case_statuses = {"ok", "mismatch"}
    for idx, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{idx}] must be an object")
        missing_case = sorted(required_case_keys.difference(case.keys()))
        if missing_case:
            raise ValueError(
                f"cases[{idx}] missing required key(s): {', '.join(missing_case)}"
            )
        source = case.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"cases[{idx}].source must be a non-empty string")

        status = case.get("status")
        if status not in allowed_case_statuses:
            raise ValueError(
                f"cases[{idx}].status must be one of: {', '.join(sorted(allowed_case_statuses))}"
            )

        for bool_key in ("exact_match", "token_equivalent", "ast_equivalent"):
            if not isinstance(case.get(bool_key), bool):
                raise ValueError(f"cases[{idx}].{bool_key} must be a boolean")

        if not isinstance(case.get("failure_taxonomy"), list):
            raise ValueError(f"cases[{idx}].failure_taxonomy must be an array")

    total_cases = _read_non_negative_int_field(report, "total_cases")
    ok_cases = _read_non_negative_int_field(report, "ok_cases")
    mismatch_cases = _read_non_negative_int_field(report, "mismatch_cases")
    observed_total = len(cases)
    observed_mismatch = sum(1 for c in cases if c.get("status") != "ok")
    observed_ok = observed_total - observed_mismatch

    if total_cases != observed_total:
        raise ValueError(
            "batch report counter mismatch: total_cases does not match len(cases) "
            f"(declared={total_cases}, observed={observed_total}, input={input_path})"
        )
    if mismatch_cases != observed_mismatch:
        raise ValueError(
            "batch report counter mismatch: mismatch_cases does not match case statuses "
            f"(declared={mismatch_cases}, observed={observed_mismatch}, input={input_path})"
        )
    if ok_cases != observed_ok:
        raise ValueError(
            "batch report counter mismatch: ok_cases does not match case statuses "
            f"(declared={ok_cases}, observed={observed_ok}, input={input_path})"
        )


def load_task_set_lineage(path: Path | None) -> dict[str, str] | None:
    if path is None:
        return None
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("task set JSON root must be an object")

    lineage: dict[str, str] = {}
    task_set_id = payload.get("task_set_id")
    if isinstance(task_set_id, str) and task_set_id.strip():
        lineage["task_set_id"] = task_set_id
    alias_set_id = payload.get("alias_set_id")
    if isinstance(alias_set_id, str) and alias_set_id.strip():
        lineage["alias_set_id"] = alias_set_id
    manifest_path = payload.get("manifest_path")
    if isinstance(manifest_path, str) and manifest_path.strip():
        lineage["manifest_path"] = manifest_path

    return lineage or None


def load_taxonomy_weights(path: Path | None) -> tuple[dict[str, int], int]:
    if path is None:
        return dict(TAXONOMY_WEIGHTS), DEFAULT_TAXONOMY_WEIGHT

    payload = load_json(path)
    default_weight = int(payload.get("default_weight", DEFAULT_TAXONOMY_WEIGHT))

    raw_weights = payload.get("weights", {})
    if not isinstance(raw_weights, Mapping):
        raise ValueError("taxonomy weights JSON must contain an object at key 'weights'")

    weights: dict[str, int] = {}
    for k, v in raw_weights.items():
        weights[str(k)] = int(v)

    return weights, default_weight


def list_taxonomy_profiles(profile_dir: Path) -> list[str]:
    if not profile_dir.exists():
        return []
    return sorted(p.stem for p in profile_dir.glob("*.json") if p.is_file())


def resolve_taxonomy_profile(profile_name: str, profile_dir: Path) -> Path:
    profile_path = profile_dir / f"{profile_name}.json"
    if not profile_path.exists():
        raise FileNotFoundError(
            f"taxonomy profile '{profile_name}' not found in {profile_dir}"
        )
    return profile_path


def _tag_weight(tag: str, taxonomy_weights: Mapping[str, int], default_weight: int) -> int:
    return int(taxonomy_weights.get(tag, default_weight))


def _mismatch_severity_score(
    case: dict[str, Any], taxonomy_weights: Mapping[str, int], default_weight: int
) -> tuple[int, int, int, str]:
    """Higher tuple value means more severe mismatch.

    Priority (desc):
    1) taxonomy weight
    2) ast/token equivalence broken
    3) taxonomy tag count
    4) source path (stable tie-break)
    """
    tags = [str(t) for t in (case.get("failure_taxonomy") or [])]
    tag_weight = sum(_tag_weight(tag, taxonomy_weights, default_weight) for tag in tags)

    ast_penalty = 0 if case.get("ast_equivalent") is True else 20
    token_penalty = 0 if case.get("token_equivalent") is True else 20
    severity = tag_weight + ast_penalty + token_penalty

    return (severity, len(tags), 1 if case.get("status") != "ok" else 0, str(case.get("source", "")))


def build_summary_payload(
    report: dict[str, Any],
    source_path: Path,
    top_k_mismatches: int,
    mismatch_sort: str,
    taxonomy_weights: Mapping[str, int],
    default_weight: int,
    taxonomy_weight_source: str,
    only_mismatches: bool,
    task_set_lineage: dict[str, str] | None = None,
) -> dict[str, Any]:
    total = int(report.get("total_cases", 0))
    ok_cases = int(report.get("ok_cases", 0))
    mismatch_cases = int(report.get("mismatch_cases", 0))
    include_diff = bool(report.get("include_diff", False))
    cases = report.get("cases", []) or []

    token_equiv_true = 0
    ast_equiv_true = 0
    taxonomy_counts: Counter[str] = Counter()

    for case in cases:
        if case.get("token_equivalent") is True:
            token_equiv_true += 1
        if case.get("ast_equivalent") is True:
            ast_equiv_true += 1
        for tag in case.get("failure_taxonomy") or []:
            taxonomy_counts[str(tag)] += 1

    mismatch_list = [c for c in cases if c.get("status") != "ok"]
    visible_cases = mismatch_list if only_mismatches else cases
    mismatch_severity_total = sum(
        _mismatch_severity_score(case, taxonomy_weights, default_weight)[0]
        for case in mismatch_list
    )
    mismatch_severity_avg = (
        mismatch_severity_total / len(mismatch_list) if mismatch_list else 0.0
    )

    weighted_rows = sorted(
        (
            {
                "tag": tag,
                "count": count,
                "weight": _tag_weight(tag, taxonomy_weights, default_weight),
                "weighted_score": count * _tag_weight(tag, taxonomy_weights, default_weight),
            }
            for tag, count in taxonomy_counts.items()
        ),
        key=lambda item: (item["weighted_score"], item["count"], item["tag"]),
        reverse=True,
    )

    if mismatch_sort == "severity":
        mismatch_list = sorted(
            mismatch_list,
            key=lambda c: _mismatch_severity_score(c, taxonomy_weights, default_weight),
            reverse=True,
        )

    top_mismatches: list[dict[str, Any]] = []
    if top_k_mismatches > 0:
        for case in mismatch_list[:top_k_mismatches]:
            tags = [str(t) for t in (case.get("failure_taxonomy") or [])]
            first_diff = case.get("first_diff") if isinstance(case.get("first_diff"), dict) else {}
            first_token_diff = (
                case.get("first_token_diff") if isinstance(case.get("first_token_diff"), dict) else {}
            )
            top_mismatch: dict[str, Any] = {
                "source": case.get("source", "<unknown>"),
                "failure_taxonomy": tags,
                "severity": _mismatch_severity_score(case, taxonomy_weights, default_weight)[0],
            }
            if "line" in first_diff:
                top_mismatch["first_diff_line"] = first_diff.get("line")
            if "index" in first_token_diff:
                top_mismatch["first_token_diff_index"] = first_token_diff.get("index")
            top_mismatches.append(top_mismatch)

    generated_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    metadata: dict[str, Any] = {
        "schema_version": "v1",
        "generated_at_utc": generated_at_utc,
        "input_report": str(source_path),
    }
    if task_set_lineage:
        metadata["task_set_lineage"] = task_set_lineage

    return {
        "metadata": metadata,
        "title": f"Batch Roundtrip Summary ({source_path.name})",
        "overview": {
            "total_cases": total,
            "ok_cases": ok_cases,
            "ok_cases_pct": pct(ok_cases, total),
            "mismatch_cases": mismatch_cases,
            "mismatch_cases_pct": pct(mismatch_cases, total),
            "include_diff": include_diff,
            "taxonomy_weight_source": taxonomy_weight_source,
            "cases_scope": "mismatches-only" if only_mismatches else "all",
        },
        "quality_signals": {
            "token_equivalent_true": token_equiv_true,
            "token_equivalent_pct": pct(token_equiv_true, total),
            "ast_equivalent_true": ast_equiv_true,
            "ast_equivalent_pct": pct(ast_equiv_true, total),
            "mismatch_severity_total": mismatch_severity_total,
            "mismatch_severity_avg": round(mismatch_severity_avg, 1),
        },
        "failure_taxonomy": {
            "frequency": dict(taxonomy_counts),
            "severity_weighted": weighted_rows,
        },
        "top_mismatches": top_mismatches,
        "mismatch_sort": mismatch_sort,
        "cases": visible_cases,
    }


def build_summary(payload: dict[str, Any], top_k_mismatches: int) -> str:
    overview = payload["overview"]
    quality = payload["quality_signals"]
    metadata = payload.get("metadata") or {}
    gates = payload.get("gates") if isinstance(payload.get("gates"), dict) else {}
    task_set_lineage = metadata.get("task_set_lineage") if isinstance(metadata, dict) else None
    lines: list[str] = []
    lines.append(f"# {payload['title']}")
    lines.append("")
    lines.append("## Overview")
    lines.append(f"- total_cases: {overview['total_cases']}")
    lines.append(f"- ok_cases: {overview['ok_cases']} ({overview['ok_cases_pct']})")
    lines.append(
        f"- mismatch_cases: {overview['mismatch_cases']} ({overview['mismatch_cases_pct']})"
    )
    lines.append(f"- include_diff: {str(overview['include_diff']).lower()}")
    lines.append(f"- taxonomy_weight_source: {overview['taxonomy_weight_source']}")
    lines.append(f"- cases_scope: {overview['cases_scope']}")
    if isinstance(task_set_lineage, dict):
        if "task_set_id" in task_set_lineage:
            lines.append(f"- task_set_id: {task_set_lineage['task_set_id']}")
        if "alias_set_id" in task_set_lineage:
            lines.append(f"- alias_set_id: {task_set_lineage['alias_set_id']}")
        if "manifest_path" in task_set_lineage:
            lines.append(f"- manifest_path: {task_set_lineage['manifest_path']}")
    lines.append("")

    lines.append("## Quality Signals")
    lines.append(
        f"- token_equivalent=true: {quality['token_equivalent_true']}/{overview['total_cases']} ({quality['token_equivalent_pct']})"
    )
    lines.append(
        f"- ast_equivalent=true: {quality['ast_equivalent_true']}/{overview['total_cases']} ({quality['ast_equivalent_pct']})"
    )
    lines.append(f"- mismatch_severity_total: {quality['mismatch_severity_total']}")
    lines.append(f"- mismatch_severity_avg: {quality['mismatch_severity_avg']:.1f}")
    lines.append("")

    if gates:
        lines.append("## Gate Signals")
        lines.append(
            f"- any_tripped: {gates.get('any_tripped')}"
        )
        tripped_list = gates.get("tripped_list")
        if isinstance(tripped_list, list):
            rendered = ", ".join(str(item) for item in tripped_list) if tripped_list else "none"
            lines.append(f"- tripped_list: {rendered}")
        aggregate_gate = gates.get("aggregate") if isinstance(gates.get("aggregate"), dict) else None
        if isinstance(aggregate_gate, dict):
            lines.append(
                "- aggregate gate: "
                f"enabled={aggregate_gate.get('enabled')}, "
                f"tripped={aggregate_gate.get('tripped')}, "
                f"exit_code={aggregate_gate.get('exit_code')}"
            )
        mismatch_gate = gates.get("mismatch") if isinstance(gates.get("mismatch"), dict) else None
        if isinstance(mismatch_gate, dict):
            lines.append(
                "- mismatch gate: "
                f"enabled={mismatch_gate.get('enabled')}, "
                f"tripped={mismatch_gate.get('tripped')}, "
                f"observed_mismatch_cases={mismatch_gate.get('observed_mismatch_cases')}"
            )
        severity_total_gate = (
            gates.get("severity_total") if isinstance(gates.get("severity_total"), dict) else None
        )
        if isinstance(severity_total_gate, dict):
            lines.append(
                "- severity_total gate: "
                f"enabled={severity_total_gate.get('enabled')}, "
                f"tripped={severity_total_gate.get('tripped')}, "
                f"threshold={severity_total_gate.get('threshold')}, "
                f"observed={severity_total_gate.get('observed')}"
            )
        severity_avg_gate = (
            gates.get("severity_avg") if isinstance(gates.get("severity_avg"), dict) else None
        )
        if isinstance(severity_avg_gate, dict):
            lines.append(
                "- severity_avg gate: "
                f"enabled={severity_avg_gate.get('enabled')}, "
                f"tripped={severity_avg_gate.get('tripped')}, "
                f"threshold={severity_avg_gate.get('threshold')}, "
                f"observed={severity_avg_gate.get('observed')}"
            )
        lines.append("")

    lines.append("## Failure Taxonomy (frequency)")
    freq = payload["failure_taxonomy"]["frequency"]
    if freq:
        for tag, count in sorted(freq.items(), key=lambda kv: kv[1], reverse=True):
            lines.append(f"- {tag}: {count}")

        lines.append("")
        lines.append("### Failure Taxonomy (severity-weighted)")
        for row in payload["failure_taxonomy"]["severity_weighted"]:
            lines.append(
                f"- {row['tag']}: weighted_score={row['weighted_score']} (count={row['count']}, weight={row['weight']})"
            )
    else:
        lines.append("- none")

    if top_k_mismatches > 0:
        lines.append("")
        lines.append(
            f"## Top {min(top_k_mismatches, len(payload['top_mismatches']))} Mismatch Cases (sort={payload['mismatch_sort']})"
        )
        if payload["top_mismatches"]:
            for case in payload["top_mismatches"]:
                tags = case.get("failure_taxonomy") or []
                tags_str = ", ".join(str(t) for t in tags) if tags else "none"
                lines.append(f"- {case['source']} (failure_taxonomy={tags_str})")
        else:
            lines.append("- none")

    lines.append("")
    lines.append("## Cases")
    for case in payload["cases"]:
        path = case.get("source", "<unknown>")
        status = case.get("status", "<unknown>")
        exact = case.get("exact_match")
        token_eq = case.get("token_equivalent")
        ast_eq = case.get("ast_equivalent")
        tags = case.get("failure_taxonomy") or []
        tags_str = ", ".join(str(t) for t in tags) if tags else "none"
        lines.append(
            f"- {path}: status={status}, exact_match={exact}, token_equivalent={token_eq}, ast_equivalent={ast_eq}, failure_taxonomy={tags_str}"
        )

    lines.append("")
    return "\n".join(lines)


def write_csv(
    report: dict[str, Any], output_csv: Path, include_diff_columns: bool, only_mismatches: bool
) -> None:
    cases = report.get("cases", []) or []
    if only_mismatches:
        cases = [c for c in cases if c.get("status") != "ok"]
    fieldnames = [
        "source",
        "status",
        "exact_match",
        "token_equivalent",
        "ast_equivalent",
        "failure_taxonomy",
    ]
    if include_diff_columns:
        fieldnames.extend(
            [
                "first_diff_line",
                "first_diff_src",
                "first_diff_restored",
                "first_token_diff_index",
                "first_token_diff_src",
                "first_token_diff_restored",
            ]
        )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for case in cases:
            tags = case.get("failure_taxonomy") or []
            row = {
                "source": case.get("source", ""),
                "status": case.get("status", ""),
                "exact_match": case.get("exact_match", ""),
                "token_equivalent": case.get("token_equivalent", ""),
                "ast_equivalent": case.get("ast_equivalent", ""),
                "failure_taxonomy": "|".join(str(t) for t in tags),
            }
            if include_diff_columns:
                first_diff = case.get("first_diff") or {}
                first_token_diff = case.get("first_token_diff") or {}
                row.update(
                    {
                        "first_diff_line": first_diff.get("line", ""),
                        "first_diff_src": first_diff.get("src", ""),
                        "first_diff_restored": first_diff.get("restored", ""),
                        "first_token_diff_index": first_token_diff.get("index", ""),
                        "first_token_diff_src": first_token_diff.get("src", ""),
                        "first_token_diff_restored": first_token_diff.get("restored", ""),
                    }
                )
            writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize batch-roundtrip-report JSON into markdown."
    )
    parser.add_argument("input_json", type=Path, nargs="?", help="Path to batch report JSON")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output markdown path (default: <input>.summary.md)",
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=None,
        help="Optional CSV export for case-level rows",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional machine-readable JSON summary output",
    )
    parser.add_argument(
        "--top-k-mismatches",
        type=int,
        default=5,
        help="How many mismatch cases to show in the summary highlight section (default: 5)",
    )
    parser.add_argument(
        "--include-diff-columns",
        action="store_true",
        help="Include first_diff/first_token_diff detail columns in CSV export",
    )
    parser.add_argument(
        "--mismatch-sort",
        choices=["input", "severity"],
        default="input",
        help="Sort mode for mismatch highlight section (default: input)",
    )
    parser.add_argument(
        "--taxonomy-weights",
        type=Path,
        default=None,
        help=(
            "Optional JSON file with taxonomy severity weights. "
            "Schema: {\"default_weight\": 15, \"weights\": {\"tag\": 40, ...}}"
        ),
    )
    parser.add_argument(
        "--taxonomy-weight-profile",
        type=str,
        default=None,
        help=(
            "Named taxonomy weight profile from examples/weights/<name>.json. "
            "Ignored when --taxonomy-weights is explicitly provided."
        ),
    )
    parser.add_argument(
        "--list-taxonomy-profiles",
        action="store_true",
        help="List available named taxonomy weight profiles and exit",
    )
    parser.add_argument(
        "--only-mismatches",
        action="store_true",
        help="Limit Cases section and CSV/JSON case rows to mismatches only",
    )
    parser.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="Exit with code 2 when mismatch_cases > 0 (useful for CI gating)",
    )
    parser.add_argument(
        "--fail-on-severity-total-ge",
        type=int,
        default=None,
        help=(
            "Exit with code 3 when quality_signals.mismatch_severity_total is >= this threshold "
            "(risk-budget gate for CI/automation)"
        ),
    )
    parser.add_argument(
        "--fail-on-severity-avg-ge",
        type=float,
        default=None,
        help=(
            "Exit with code 3 when quality_signals.mismatch_severity_avg is >= this threshold "
            "(risk-budget gate for CI/automation)"
        ),
    )
    parser.add_argument(
        "--task-set-json",
        type=Path,
        default=None,
        help="Optional task-set JSON; embed task-set lineage metadata into summary outputs",
    )
    parser.add_argument(
        "--fail-on-any-tripped",
        action="store_true",
        help=(
            "Exit with code 4 when any enabled gate is tripped (aggregate gate for automation). "
            "Works with --fail-on-mismatch / --fail-on-severity-* flags."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_taxonomy_profiles:
        profiles = list_taxonomy_profiles(PROFILE_DIR)
        for name in profiles:
            print(name)
        return 0

    if args.input_json is None:
        raise ValueError("input_json is required unless --list-taxonomy-profiles is used")

    report = load_json(args.input_json)
    validate_batch_report_shape(report, args.input_json)
    output = args.output or args.input_json.with_suffix("").with_suffix(".summary.md")
    top_k = max(0, int(args.top_k_mismatches))

    taxonomy_weight_path = args.taxonomy_weights
    if taxonomy_weight_path is None and args.taxonomy_weight_profile is not None:
        taxonomy_weight_path = resolve_taxonomy_profile(args.taxonomy_weight_profile, PROFILE_DIR)

    taxonomy_weight_source = "default:built-in"
    if args.taxonomy_weights is not None:
        taxonomy_weight_source = f"file:{args.taxonomy_weights}"
    elif args.taxonomy_weight_profile is not None and taxonomy_weight_path is not None:
        taxonomy_weight_source = f"profile:{args.taxonomy_weight_profile} ({taxonomy_weight_path})"

    taxonomy_weights, default_weight = load_taxonomy_weights(taxonomy_weight_path)
    task_set_lineage = load_task_set_lineage(args.task_set_json)
    payload = build_summary_payload(
        report,
        args.input_json,
        top_k,
        args.mismatch_sort,
        taxonomy_weights,
        default_weight,
        taxonomy_weight_source,
        args.only_mismatches,
        task_set_lineage=task_set_lineage,
    )

    observed_mismatch = int(payload["overview"]["mismatch_cases"])
    severity_total = int(payload["quality_signals"]["mismatch_severity_total"])
    severity_avg = float(payload["quality_signals"]["mismatch_severity_avg"])

    mismatch_gate_tripped = bool(args.fail_on_mismatch and observed_mismatch > 0)
    severity_total_gate_enabled = args.fail_on_severity_total_ge is not None
    severity_total_threshold = (
        int(args.fail_on_severity_total_ge) if severity_total_gate_enabled else None
    )
    severity_total_gate_tripped = bool(
        severity_total_gate_enabled and severity_total >= int(args.fail_on_severity_total_ge)
    )

    severity_avg_gate_enabled = args.fail_on_severity_avg_ge is not None
    severity_avg_threshold = (
        float(args.fail_on_severity_avg_ge) if severity_avg_gate_enabled else None
    )
    severity_avg_gate_tripped = bool(
        severity_avg_gate_enabled and severity_avg >= float(args.fail_on_severity_avg_ge)
    )

    tripped_gate_names: list[str] = []
    if mismatch_gate_tripped:
        tripped_gate_names.append("mismatch")
    if severity_total_gate_tripped:
        tripped_gate_names.append("severity_total")
    if severity_avg_gate_tripped:
        tripped_gate_names.append("severity_avg")

    payload["gates"] = {
        "mismatch": {
            "enabled": bool(args.fail_on_mismatch),
            "tripped": mismatch_gate_tripped,
            "observed_mismatch_cases": observed_mismatch,
        },
        "severity_total": {
            "enabled": severity_total_gate_enabled,
            "threshold": severity_total_threshold,
            "observed": severity_total,
            "tripped": severity_total_gate_tripped,
        },
        "severity_avg": {
            "enabled": severity_avg_gate_enabled,
            "threshold": severity_avg_threshold,
            "observed": severity_avg,
            "tripped": severity_avg_gate_tripped,
        },
        "any_tripped": bool(tripped_gate_names),
        "tripped_list": tripped_gate_names,
        "aggregate": {
            "enabled": bool(args.fail_on_any_tripped),
            "tripped": bool(args.fail_on_any_tripped and tripped_gate_names),
            "exit_code": 4,
        },
    }

    summary = build_summary(payload, top_k)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(summary, encoding="utf-8")

    outputs: list[Path] = [output]
    if args.csv_output is not None:
        write_csv(
            report,
            args.csv_output,
            include_diff_columns=args.include_diff_columns,
            only_mismatches=args.only_mismatches,
        )
        outputs.append(args.csv_output)
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs.append(args.json_output)

    print("\n".join(str(p) for p in outputs))

    if args.fail_on_any_tripped and tripped_gate_names:
        emit_error(
            "aggregate gate tripped",
            hints=[
                f"input={args.input_json}",
                f"tripped={','.join(tripped_gate_names)}",
                "gate=--fail-on-any-tripped",
            ],
        )
        return 4

    if mismatch_gate_tripped:
        emit_error(
            "mismatch gate tripped: mismatch_cases > 0",
            hints=[f"input={args.input_json}", "gate=--fail-on-mismatch"],
        )
        return 2

    if severity_total_gate_tripped:
        emit_error(
            "severity total gate tripped",
            hints=[
                f"input={args.input_json}",
                f"observed_total={severity_total}",
                f"threshold_total={int(args.fail_on_severity_total_ge)}",
            ],
        )
        return 3
    if severity_avg_gate_tripped:
        emit_error(
            "severity average gate tripped",
            hints=[
                f"input={args.input_json}",
                f"observed_avg={severity_avg}",
                f"threshold_avg={float(args.fail_on_severity_avg_ge)}",
            ],
        )
        return 3

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        input_hint = f"input={sys.argv[1]}" if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "input=<unspecified>"
        emit_error(str(exc), hints=[input_hint])
        raise SystemExit(1)
