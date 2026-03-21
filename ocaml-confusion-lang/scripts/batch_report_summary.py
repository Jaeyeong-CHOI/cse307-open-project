#!/usr/bin/env python3
"""Generate a concise markdown summary from batch-roundtrip-report JSON."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def pct(n: int, d: int) -> str:
    if d == 0:
        return "0.0%"
    return f"{(n / d) * 100:.1f}%"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_summary(report: dict[str, Any], source_path: Path) -> str:
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
    lines.append("## Quality Signals")
    lines.append(f"- token_equivalent=true: {token_equiv_true}/{total} ({pct(token_equiv_true, total)})")
    lines.append(f"- ast_equivalent=true: {ast_equiv_true}/{total} ({pct(ast_equiv_true, total)})")
    lines.append("")

    lines.append("## Failure Taxonomy (frequency)")
    if taxonomy_counts:
        for tag, count in taxonomy_counts.most_common():
            lines.append(f"- {tag}: {count}")
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize batch-roundtrip-report JSON into markdown."
    )
    parser.add_argument("input_json", type=Path, help="Path to batch report JSON")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output markdown path (default: <input>.summary.md)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = load_json(args.input_json)
    output = args.output or args.input_json.with_suffix("").with_suffix(".summary.md")
    summary = build_summary(report, args.input_json)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(summary, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
