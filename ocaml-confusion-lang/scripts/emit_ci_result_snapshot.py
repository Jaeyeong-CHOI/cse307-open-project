#!/usr/bin/env python3
"""Emit compact markdown snapshot lines for GitHub Actions step summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TOP_K_AUTO = "auto"
TOP_K_MIN = 1
TOP_K_MAX = 3


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


def build_snapshot_markdown(
    payload: dict[str, Any],
    *,
    label: str,
    summary_path: Path,
    metric_path: Path,
    top_k_mismatches: str = "1",
) -> str:
    overview = payload.get("overview", {}) if isinstance(payload.get("overview"), dict) else {}
    gates = payload.get("gates", {}) if isinstance(payload.get("gates"), dict) else {}
    top1 = _top1_fields(payload)
    resolved_top_k = _resolve_top_k(payload, top_k_mismatches)

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
        (
            "- top_k_mismatches: "
            f"requested={top_k_mismatches}; "
            f"resolved={resolved_top_k}"
        ),
        f"- top{resolved_top_k}_mismatches_compact: {_topk_compact(payload, top_k=resolved_top_k)}",
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
        default="1",
        help="number of mismatch hints to compact into one line (1-3) or 'auto' (default: 1)",
    )
    args = parser.parse_args()

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
