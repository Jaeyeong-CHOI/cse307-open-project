#!/usr/bin/env python3
"""Generate human-friendly summaries from batch-roundtrip-report JSON."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

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


def build_summary(
    report: dict[str, Any],
    source_path: Path,
    top_k_mismatches: int,
    mismatch_sort: str,
    taxonomy_weights: Mapping[str, int],
    default_weight: int,
) -> str:
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

    lines: list[str] = []
    lines.append(f"# Batch Roundtrip Summary ({source_path.name})")
    lines.append("")
    lines.append("## Overview")
    lines.append(f"- total_cases: {total}")
    lines.append(f"- ok_cases: {ok_cases} ({pct(ok_cases, total)})")
    lines.append(f"- mismatch_cases: {mismatch_cases} ({pct(mismatch_cases, total)})")
    lines.append(f"- include_diff: {str(include_diff).lower()}")
    lines.append("")
    mismatch_list = [c for c in cases if c.get("status") != "ok"]
    mismatch_severity_total = sum(
        _mismatch_severity_score(case, taxonomy_weights, default_weight)[0]
        for case in mismatch_list
    )
    mismatch_severity_avg = (
        mismatch_severity_total / len(mismatch_list) if mismatch_list else 0.0
    )

    lines.append("## Quality Signals")
    lines.append(f"- token_equivalent=true: {token_equiv_true}/{total} ({pct(token_equiv_true, total)})")
    lines.append(f"- ast_equivalent=true: {ast_equiv_true}/{total} ({pct(ast_equiv_true, total)})")
    lines.append(f"- mismatch_severity_total: {mismatch_severity_total}")
    lines.append(f"- mismatch_severity_avg: {mismatch_severity_avg:.1f}")
    lines.append("")

    lines.append("## Failure Taxonomy (frequency)")
    if taxonomy_counts:
        for tag, count in taxonomy_counts.most_common():
            lines.append(f"- {tag}: {count}")

        lines.append("")
        lines.append("### Failure Taxonomy (severity-weighted)")
        weighted_rows = sorted(
            (
                (
                    tag,
                    count,
                    _tag_weight(tag, taxonomy_weights, default_weight),
                    count * _tag_weight(tag, taxonomy_weights, default_weight),
                )
                for tag, count in taxonomy_counts.items()
            ),
            key=lambda item: (item[3], item[1], item[0]),
            reverse=True,
        )
        for tag, count, weight, weighted_score in weighted_rows:
            lines.append(
                f"- {tag}: weighted_score={weighted_score} (count={count}, weight={weight})"
            )
    else:
        lines.append("- none")

    if mismatch_sort == "severity":
        mismatch_list = sorted(
            mismatch_list,
            key=lambda c: _mismatch_severity_score(c, taxonomy_weights, default_weight),
            reverse=True,
        )
    if top_k_mismatches > 0:
        lines.append("")
        lines.append(
            f"## Top {min(top_k_mismatches, len(mismatch_list))} Mismatch Cases (sort={mismatch_sort})"
        )
        if mismatch_list:
            for case in mismatch_list[:top_k_mismatches]:
                path = case.get("source", "<unknown>")
                tags = case.get("failure_taxonomy") or []
                tags_str = ", ".join(str(t) for t in tags) if tags else "none"
                lines.append(f"- {path} (failure_taxonomy={tags_str})")
        else:
            lines.append("- none")

    lines.append("")
    lines.append("## Cases")
    for case in cases:
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


def write_csv(report: dict[str, Any], output_csv: Path, include_diff_columns: bool) -> None:
    cases = report.get("cases", []) or []
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
    output = args.output or args.input_json.with_suffix("").with_suffix(".summary.md")
    top_k = max(0, int(args.top_k_mismatches))

    taxonomy_weight_path = args.taxonomy_weights
    if taxonomy_weight_path is None and args.taxonomy_weight_profile is not None:
        taxonomy_weight_path = resolve_taxonomy_profile(args.taxonomy_weight_profile, PROFILE_DIR)

    taxonomy_weights, default_weight = load_taxonomy_weights(taxonomy_weight_path)
    summary = build_summary(
        report,
        args.input_json,
        top_k,
        args.mismatch_sort,
        taxonomy_weights,
        default_weight,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(summary, encoding="utf-8")

    if args.csv_output is not None:
        write_csv(report, args.csv_output, include_diff_columns=args.include_diff_columns)
        print(f"{output}\n{args.csv_output}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
