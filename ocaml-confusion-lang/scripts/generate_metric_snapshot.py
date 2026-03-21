#!/usr/bin/env python3
"""Generate metric-schema payload from summary JSON output."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

LINEAGE_KEYS = ("task_set_id", "alias_set_id", "manifest_path")

ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}


def emit_error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
        safe = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error::{safe}", file=sys.stderr)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return payload


def _safe_ratio(numer: float, denom: float) -> float:
    if denom <= 0:
        return 0.0
    return numer / denom


def _round3(value: float) -> float:
    return round(float(value), 3)


def validate_task_set_payload(payload: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{path}: root must be a JSON object"]

    for key in ["schema_version", "task_set_id", "tasks"]:
        if key not in payload:
            errors.append(f"{path}: missing required key '{key}'")

    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append(f"{path}: key 'tasks' must be a non-empty array")
        return errors

    seen_task_ids: set[str] = set()
    for idx, task in enumerate(tasks):
        where = f"{path}: tasks[{idx}]"
        if not isinstance(task, dict):
            errors.append(f"{where} must be an object")
            continue

        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            errors.append(f"{where}: task_id must be a non-empty string")
        elif task_id in seen_task_ids:
            errors.append(f"{where}: duplicate task_id '{task_id}'")
        else:
            seen_task_ids.add(task_id)

        source = task.get("source")
        if not isinstance(source, str) or not source.strip():
            errors.append(f"{where}: source must be a non-empty string")
        elif not source.endswith(".py"):
            errors.append(f"{where}: source must point to a .py file")

        if "difficulty" in task and task["difficulty"] not in ALLOWED_DIFFICULTIES:
            errors.append(
                f"{where}: difficulty must be one of {sorted(ALLOWED_DIFFICULTIES)} when present"
            )

        if "tags" in task:
            tags = task["tags"]
            if not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() for t in tags):
                errors.append(f"{where}: tags must be an array of non-empty strings when present")

    return errors


def assert_task_set_consistency(
    summary: dict[str, Any],
    task_set: dict[str, Any],
    task_set_path: Path,
    task_set_id: str,
) -> None:
    expected_id = task_set.get("task_set_id")
    if expected_id != task_set_id:
        raise ValueError(
            f"task-set id mismatch: --task-set-id='{task_set_id}' but {task_set_path} has '{expected_id}'"
        )

    overview = summary.get("overview") or {}
    scope = overview.get("cases_scope")
    if scope != "all":
        raise ValueError(
            "summary overview.cases_scope must be 'all' when using --task-set-json "
            f"(got '{scope}'). Re-generate summary without --only-mismatches to keep all task-set cases."
        )

    tasks = task_set.get("tasks") or []
    cases = summary.get("cases") or []

    total_cases = int(overview.get("total_cases", 0) or 0)
    if total_cases != len(tasks):
        raise ValueError(
            f"task count mismatch: summary total_cases={total_cases}, task_set tasks={len(tasks)}"
        )

    case_sources = {c.get("source") for c in cases if isinstance(c, dict) and isinstance(c.get("source"), str)}
    task_sources = {t.get("source") for t in tasks if isinstance(t, dict) and isinstance(t.get("source"), str)}

    if case_sources != task_sources:
        missing_in_summary = sorted(task_sources - case_sources)
        extra_in_summary = sorted(case_sources - task_sources)
        raise ValueError(
            "task source mismatch between summary and task set: "
            f"missing_in_summary={missing_in_summary}, extra_in_summary={extra_in_summary}"
        )


def check_summary_lineage_consistency(
    summary: dict[str, Any],
    task_set: dict[str, Any],
    mode: str,
) -> None:
    metadata = summary.get("metadata") or {}
    summary_lineage = metadata.get("task_set_lineage")
    if summary_lineage is None:
        return
    if not isinstance(summary_lineage, dict):
        message = "summary metadata.task_set_lineage must be an object when present"
        if mode == "fail":
            raise ValueError(message)
        if mode == "warn":
            print(f"WARN: {message}")
        return

    mismatches: list[str] = []
    for key in LINEAGE_KEYS:
        summary_value = summary_lineage.get(key)
        task_set_value = task_set.get(key)
        if summary_value is None or task_set_value is None:
            continue
        if summary_value != task_set_value:
            mismatches.append(
                f"{key}: summary='{summary_value}' task_set='{task_set_value}'"
            )

    if mismatches:
        message = (
            "summary/task-set lineage mismatch. "
            "Check task_set_lineage in summary metadata vs task-set JSON fields "
            "(task_set_id, alias_set_id, manifest_path): "
            + "; ".join(mismatches)
        )
        if mode == "fail":
            raise ValueError(message)
        if mode == "warn":
            print(f"WARN: {message}")


def build_metric_payload(
    summary: dict[str, Any],
    task_set_id: str,
    prompt_condition: str,
    model: str,
    task_set_lineage: dict[str, str] | None = None,
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
    source_summary: dict[str, Any] = {
        "input_report": metadata.get("input_report"),
        "generated_at_utc": metadata.get("generated_at_utc"),
    }
    if task_set_lineage:
        source_summary["task_set_lineage"] = task_set_lineage

    return {
        "schema_version": "v1",
        "task_set_id": task_set_id,
        "prompt_condition": prompt_condition,
        "model": model,
        "metrics": metrics,
        "source_summary": source_summary,
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
    parser.add_argument(
        "--task-set-json",
        type=Path,
        default=None,
        help="Optional task-set JSON to validate id/source consistency against summary",
    )
    parser.add_argument(
        "--lineage-consistency",
        choices=["off", "warn", "fail"],
        default="warn",
        help="How to handle summary/task-set lineage mismatches when --task-set-json is used",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        summary = load_json(args.summary_json)

        task_set_lineage: dict[str, str] | None = None
        if args.task_set_json is not None:
            task_set = load_json(args.task_set_json)
            errors = validate_task_set_payload(task_set, args.task_set_json)
            if errors:
                for err in errors:
                    emit_error(err)
                return 1
            assert_task_set_consistency(
                summary,
                task_set,
                task_set_path=args.task_set_json,
                task_set_id=args.task_set_id,
            )

            lineage: dict[str, str] = {"task_set_id": args.task_set_id}
            alias_set_id = task_set.get("alias_set_id")
            manifest_path = task_set.get("manifest_path")
            if isinstance(alias_set_id, str) and alias_set_id.strip():
                lineage["alias_set_id"] = alias_set_id
            if isinstance(manifest_path, str) and manifest_path.strip():
                lineage["manifest_path"] = manifest_path
            check_summary_lineage_consistency(summary, task_set, args.lineage_consistency)
            task_set_lineage = lineage or None

        payload = build_metric_payload(
            summary,
            task_set_id=args.task_set_id,
            prompt_condition=args.prompt_condition,
            model=args.model,
            task_set_lineage=task_set_lineage,
        )

        output = args.output or args.summary_json.with_suffix("").with_suffix(".metrics.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(output)
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        emit_error(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
