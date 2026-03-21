#!/usr/bin/env python3
"""Emit compact markdown snapshot lines for GitHub Actions step summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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
    return " | ".join(chunks)


def _format_tripped_list(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "[]"
    return str(value)


def build_snapshot_markdown(
    payload: dict[str, Any],
    *,
    label: str,
    summary_path: Path,
    metric_path: Path,
    top_k_mismatches: int = 1,
) -> str:
    overview = payload.get("overview", {}) if isinstance(payload.get("overview"), dict) else {}
    gates = payload.get("gates", {}) if isinstance(payload.get("gates"), dict) else {}
    top1 = _top1_fields(payload)

    lines = [
        f"## {label}",
        (
            "- cases: "
            f"{overview.get('total_cases')} total / "
            f"{overview.get('ok_cases')} ok / "
            f"{overview.get('mismatch_cases')} mismatch"
        ),
        (
            "- severity_total: "
            f"{overview.get('mismatch_severity_total')} "
            f"(avg={overview.get('mismatch_severity_avg')})"
        ),
        f"- any_tripped: {gates.get('any_tripped')}",
        f"- tripped_list: {_format_tripped_list(gates.get('tripped_list'))}",
        (
            "- top1_mismatch: "
            f"severity={top1['severity']}; "
            f"taxonomy={top1['taxonomy']}; "
            f"source={top1['source']}; "
            f"first_diff_line={top1['first_diff_line']}; "
            f"first_token_diff_index={top1['first_token_diff_index']}"
        ),
        f"- top{top_k_mismatches}_mismatches_compact: {_topk_compact(payload, top_k=top_k_mismatches)}",
        f"- summary_json: `{summary_path}`",
        f"- metric_json: `{metric_path}`",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit compact CI snapshot markdown from summary JSON payload"
    )
    parser.add_argument("summary_json", type=Path, help="summary JSON payload path")
    parser.add_argument("--metric-json", required=True, type=Path, help="metric JSON path")
    parser.add_argument(
        "--label",
        default="CI result snapshot",
        help="section header label (default: CI result snapshot)",
    )
    parser.add_argument(
        "--top-k-mismatches",
        type=int,
        default=1,
        help="number of mismatch hints to compact into one line (default: 1)",
    )
    args = parser.parse_args()

    if args.top_k_mismatches < 1:
        raise SystemExit("--top-k-mismatches must be >= 1")

    payload = json.loads(args.summary_json.read_text(encoding="utf-8"))
    print(
        build_snapshot_markdown(
            payload,
            label=args.label,
            summary_path=args.summary_json,
            metric_path=args.metric_json,
            top_k_mismatches=args.top_k_mismatches,
        )
    )


if __name__ == "__main__":
    main()
