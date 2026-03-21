#!/usr/bin/env python3
"""Generate metric-schema payload from summary JSON output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: summary root must be a JSON object")
    return payload


def _safe_ratio(numer: float, denom: float) -> float:
    if denom <= 0:
        return 0.0
    return numer / denom


def _round3(value: float) -> float:
    return round(float(value), 3)


def build_metric_payload(
    summary: dict[str, Any],
    task_set_id: str,
    prompt_condition: str,
    model: str,
) -> dict[str, Any]:
    overview = summary.get("overview") or {}
    quality = summary.get("quality_signals") or {}
    taxonomy = (summary.get("failure_taxonomy") or {}).get("frequency") or {}

    total = float(overview.get("total_cases", 0) or 0)
    ok_cases = float(overview.get("ok_cases", 0) or 0)
    mismatch_cases = float(overview.get("mismatch_cases", 0) or 0)
    ast_true = float(quality.get("ast_equivalent_true", 0) or 0)
    mismatch_severity_avg = float(quality.get("mismatch_severity_avg", 0.0) or 0.0)

    line_gap_count = float(
        (taxonomy.get("line_count_mismatch", 0) or 0)
        + (taxonomy.get("whitespace_or_blankline_drift", 0) or 0)
    )

    metrics = {
        "acr": _round3(_safe_ratio(ok_cases, total)),
        "prr": _round3(_safe_ratio(mismatch_cases, total)),
        "esr": _round3(_safe_ratio(ast_true, total)),
        "mfb": _round3(max(0.0, mismatch_severity_avg)),
        "lgp": _round3(_safe_ratio(line_gap_count, total)),
    }

    metadata = summary.get("metadata") or {}
    return {
        "schema_version": "v1",
        "task_set_id": task_set_id,
        "prompt_condition": prompt_condition,
        "model": model,
        "metrics": metrics,
        "source_summary": {
            "input_report": metadata.get("input_report"),
            "generated_at_utc": metadata.get("generated_at_utc"),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate metric-schema JSON payload from batch summary JSON"
    )
    parser.add_argument("summary_json", type=Path, help="Path to summary JSON payload")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output metric JSON path (default: <summary>.metrics.json)",
    )
    parser.add_argument("--task-set-id", required=True, help="Experiment task set id")
    parser.add_argument("--prompt-condition", required=True, help="Prompt condition label")
    parser.add_argument("--model", required=True, help="Model identifier")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = load_json(args.summary_json)
    payload = build_metric_payload(
        summary,
        task_set_id=args.task_set_id,
        prompt_condition=args.prompt_condition,
        model=args.model,
    )

    output = args.output or args.summary_json.with_suffix("").with_suffix(".metrics.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
