#!/usr/bin/env python3
"""Build a deterministic batch-evaluation run plan from a task set.

This is an offline planning utility (no model/API calls).
It exists to keep evaluation batches cheap-first and avoid redundant calls.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from error_utils import emit_error


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return payload


def parse_csv_list(raw: str, field_name: str) -> list[str]:
    values = [v.strip() for v in raw.split(",") if v.strip()]
    if not values:
        raise ValueError(f"{field_name} must include at least one non-empty value")
    return values


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _cheap_first_rank(model: str) -> tuple[int, str]:
    name = model.lower()
    cheap_hints = ("nano", "mini", "flash", "haiku", "small", "lite")
    expensive_hints = ("pro", "opus", "sonnet", "large", "ultra")
    if any(h in name for h in cheap_hints):
        return (0, name)
    if any(h in name for h in expensive_hints):
        return (2, name)
    return (1, name)


def validate_task_set(payload: dict[str, Any], path: Path) -> tuple[str, list[dict[str, str]]]:
    schema_version = payload.get("schema_version")
    if schema_version != "v1":
        raise ValueError(f"{path}: schema_version must be 'v1' (got '{schema_version}')")

    task_set_id = payload.get("task_set_id")
    if not isinstance(task_set_id, str) or not task_set_id.strip():
        raise ValueError(f"{path}: task_set_id must be a non-empty string")

    tasks_raw = payload.get("tasks")
    if not isinstance(tasks_raw, list) or not tasks_raw:
        raise ValueError(f"{path}: tasks must be a non-empty array")

    tasks: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(tasks_raw):
        where = f"{path}: tasks[{idx}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where} must be an object")

        task_id = item.get("task_id")
        source = item.get("source")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError(f"{where}: task_id must be a non-empty string")
        if task_id in seen_ids:
            raise ValueError(f"{where}: duplicate task_id '{task_id}'")
        seen_ids.add(task_id)

        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"{where}: source must be a non-empty string")

        tasks.append({"task_id": task_id, "source": source})

    return task_set_id, tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a batch evaluation plan JSON")
    parser.add_argument("task_set_json", type=Path, help="Path to task-set v1 JSON")
    parser.add_argument("--models", required=True, help="Comma-separated model ids")
    parser.add_argument(
        "--prompt-conditions",
        required=True,
        help="Comma-separated prompt condition labels (e.g. base,strict,few-shot)",
    )
    parser.add_argument("--repeats", type=int, default=1, help="Repeat count per task/condition/model (default: 1)")
    parser.add_argument(
        "--max-total-runs",
        type=int,
        default=0,
        help="Optional hard cap for total planned runs (0 disables cap)",
    )
    parser.add_argument(
        "--cheap-first",
        action="store_true",
        help="Order model runs using a cheap-first heuristic before expanding matrix",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path (default: <task_set>.batch-plan.json)",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()

        if args.repeats < 1:
            raise ValueError("--repeats must be >= 1")
        if args.max_total_runs < 0:
            raise ValueError("--max-total-runs must be >= 0")

        task_set = load_json(args.task_set_json)
        task_set_id, tasks = validate_task_set(task_set, args.task_set_json)

        models = _dedupe_keep_order(parse_csv_list(args.models, "--models"))
        conditions = _dedupe_keep_order(parse_csv_list(args.prompt_conditions, "--prompt-conditions"))

        if args.cheap_first:
            models = sorted(models, key=_cheap_first_rank)

        plan: list[dict[str, Any]] = []
        run_index = 0
        for model in models:
            for condition in conditions:
                for task in tasks:
                    for rep in range(1, args.repeats + 1):
                        run_index += 1
                        plan.append(
                            {
                                "run_id": f"run-{run_index:04d}",
                                "task_id": task["task_id"],
                                "source": task["source"],
                                "model": model,
                                "prompt_condition": condition,
                                "repeat_index": rep,
                            }
                        )

        if args.max_total_runs and len(plan) > args.max_total_runs:
            raise ValueError(
                f"planned runs ({len(plan)}) exceed --max-total-runs ({args.max_total_runs}); "
                "reduce models/conditions/repeats or increase cap"
            )

        payload: dict[str, Any] = {
            "schema_version": "v1",
            "task_set_id": task_set_id,
            "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "config": {
                "models": models,
                "prompt_conditions": conditions,
                "repeats": args.repeats,
                "cheap_first": bool(args.cheap_first),
                "max_total_runs": args.max_total_runs,
            },
            "summary": {
                "task_count": len(tasks),
                "model_count": len(models),
                "prompt_condition_count": len(conditions),
                "unique_call_units": len(tasks) * len(models) * len(conditions),
                "planned_runs_total": len(plan),
            },
            "plan": plan,
        }

        out = args.output or args.task_set_json.with_suffix("").with_suffix(".batch-plan.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(out)
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        emit_error(str(exc), hints=[f"task_set_json={args.task_set_json}" if "args" in locals() else "task_set_json=<unknown>"])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
