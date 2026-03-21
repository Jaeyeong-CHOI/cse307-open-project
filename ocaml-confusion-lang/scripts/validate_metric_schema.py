#!/usr/bin/env python3
"""Validate metric schema JSON for confusion-lang experiment batches."""

from __future__ import annotations

import argparse
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from error_utils import emit_error
from run_context_validation import validate_run_context

REQUIRED_ROOT_KEYS = [
    "schema_version",
    "task_set_id",
    "prompt_condition",
    "model",
    "metrics",
]

REQUIRED_METRICS_KEYS = ["acr", "prr", "esr", "mfb"]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _in_range_0_1(value: Any) -> bool:
    return isinstance(value, (int, float)) and 0.0 <= float(value) <= 1.0


def validate_payload(payload: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{path}: root must be a JSON object"]

    for key in REQUIRED_ROOT_KEYS:
        if key not in payload:
            errors.append(f"{path}: missing required key '{key}'")

    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        errors.append(f"{path}: key 'metrics' must be an object")
        return errors

    for key in REQUIRED_METRICS_KEYS:
        if key not in metrics:
            errors.append(f"{path}: metrics missing '{key}'")

    if "acr" in metrics and not _in_range_0_1(metrics["acr"]):
        errors.append(f"{path}: metrics.acr must be a number in [0, 1]")
    if "prr" in metrics and not _in_range_0_1(metrics["prr"]):
        errors.append(f"{path}: metrics.prr must be a number in [0, 1]")
    if "esr" in metrics and not _in_range_0_1(metrics["esr"]):
        errors.append(f"{path}: metrics.esr must be a number in [0, 1]")
    if "mfb" in metrics and not (isinstance(metrics["mfb"], (int, float)) and float(metrics["mfb"]) >= 0):
        errors.append(f"{path}: metrics.mfb must be a non-negative number")

    if "lgp" in metrics and not isinstance(metrics["lgp"], (int, float)):
        errors.append(f"{path}: metrics.lgp must be numeric when present")

    source_summary = payload.get("source_summary")
    if source_summary is not None:
        if not isinstance(source_summary, dict):
            errors.append(f"{path}: source_summary must be an object when present")
        else:
            for key in ["input_report", "generated_at_utc"]:
                if key in source_summary and (
                    not isinstance(source_summary[key], str) or not source_summary[key].strip()
                ):
                    errors.append(f"{path}: source_summary.{key} must be a non-empty string when present")

            task_set_lineage = source_summary.get("task_set_lineage")
            if task_set_lineage is not None:
                if not isinstance(task_set_lineage, dict):
                    errors.append(f"{path}: source_summary.task_set_lineage must be an object when present")
                else:
                    for key in ["task_set_id", "alias_set_id", "manifest_path"]:
                        if key in task_set_lineage and (
                            not isinstance(task_set_lineage[key], str)
                            or not task_set_lineage[key].strip()
                        ):
                            errors.append(
                                f"{path}: source_summary.task_set_lineage.{key} must be a non-empty string when present"
                            )

            run_context = source_summary.get("run_context")
            if run_context is not None:
                validate_run_context(
                    {"run_context": run_context},
                    path,
                    errors,
                    run_url_label="source_summary.run_context.run_url",
                    run_url_suffix="",
                )

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate metric schema JSON")
    parser.add_argument("metric_json", type=Path, help="Path to metric schema JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = load_json(args.metric_json)
    errors = validate_payload(payload, args.metric_json)
    if errors:
        emit_error(
            "Metric schema validation failed:\n" + "\n".join(f"- {err}" for err in errors),
            hints=[f"input={args.metric_json}", "schema=examples/metric-schema-v1.json"],
        )
        return 1
    print(f"OK: metric schema valid ({args.metric_json})")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, JSONDecodeError) as exc:
        emit_error(str(exc))
        raise SystemExit(1)
