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
        "--max-total-runs-mode",
        choices=("fail", "cap"),
        default="fail",
        help="Behavior when --max-total-runs is set: fail (default) or cap plan length",
    )
    parser.add_argument(
        "--max-runs-per-model",
        type=int,
        default=0,
        help="Optional per-model cap for planned runs (0 disables cap)",
    )
    parser.add_argument(
        "--max-runs-per-prompt-condition",
        type=int,
        default=0,
        help="Optional per-prompt-condition cap for planned runs (0 disables cap)",
    )
    parser.add_argument(
        "--max-runs-per-task",
        type=int,
        default=0,
        help="Optional per-task cap for planned runs (0 disables cap)",
    )
    parser.add_argument(
        "--max-runs-per-task-model",
        type=int,
        default=0,
        help="Optional per-task×model cap for planned runs (0 disables cap)",
    )
    parser.add_argument(
        "--max-runs-per-task-prompt-condition",
        type=int,
        default=0,
        help="Optional per-task×prompt-condition cap for planned runs (0 disables cap)",
    )
    parser.add_argument(
        "--cheap-first",
        action="store_true",
        help="Order model runs using a cheap-first heuristic before expanding matrix",
    )
    parser.add_argument(
        "--fair-model-allocation",
        action="store_true",
        help="Rotate model iteration order per expansion step to reduce cap-induced model skew",
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
        if args.max_runs_per_model < 0:
            raise ValueError("--max-runs-per-model must be >= 0")
        if args.max_runs_per_prompt_condition < 0:
            raise ValueError("--max-runs-per-prompt-condition must be >= 0")
        if args.max_runs_per_task < 0:
            raise ValueError("--max-runs-per-task must be >= 0")
        if args.max_runs_per_task_model < 0:
            raise ValueError("--max-runs-per-task-model must be >= 0")
        if args.max_runs_per_task_prompt_condition < 0:
            raise ValueError("--max-runs-per-task-prompt-condition must be >= 0")

        task_set = load_json(args.task_set_json)
        task_set_id, tasks = validate_task_set(task_set, args.task_set_json)

        models = _dedupe_keep_order(parse_csv_list(args.models, "--models"))
        conditions = _dedupe_keep_order(parse_csv_list(args.prompt_conditions, "--prompt-conditions"))

        if args.cheap_first:
            models = sorted(models, key=_cheap_first_rank)

        plan: list[dict[str, Any]] = []
        run_index = 0
        model_cursor = 0
        stop_planning = False

        runs_per_model: dict[str, int] = {model: 0 for model in models}

        def total_cap_reached() -> bool:
            return bool(args.max_total_runs and len(plan) >= args.max_total_runs)

        def iter_models() -> list[str]:
            nonlocal model_cursor
            if not args.fair_model_allocation or len(models) <= 1:
                return models
            min_runs = min(runs_per_model.values())
            # Prioritize currently under-allocated models first, then retain cheap-first/base order.
            under_allocated = [m for m in models if runs_per_model[m] == min_runs]
            if len(under_allocated) == len(models):
                # All tied: rotate to avoid deterministic first-model stickiness.
                ordered = models[model_cursor:] + models[:model_cursor]
                model_cursor = (model_cursor + 1) % len(models)
                return ordered
            ordered = sorted(models, key=lambda m: (runs_per_model[m], models.index(m)))
            return ordered
        runs_per_prompt_condition: dict[str, int] = {condition: 0 for condition in conditions}
        runs_per_task: dict[str, int] = {task["task_id"]: 0 for task in tasks}
        runs_by_task_model: dict[str, dict[str, int]] = {
            task["task_id"]: {model: 0 for model in models} for task in tasks
        }
        runs_by_model_prompt_condition: dict[str, dict[str, int]] = {
            model: {condition: 0 for condition in conditions} for model in models
        }
        runs_by_task_prompt_condition: dict[str, dict[str, int]] = {
            task["task_id"]: {condition: 0 for condition in conditions} for task in tasks
        }
        if args.max_runs_per_prompt_condition:
            # Condition-first expansion keeps per-condition caps from starving later models.
            for condition in conditions:
                if stop_planning:
                    break
                for task in tasks:
                    if stop_planning:
                        break
                    for rep in range(1, args.repeats + 1):
                        if stop_planning:
                            break
                        for model in iter_models():
                            if total_cap_reached() and args.max_total_runs_mode == "cap":
                                stop_planning = True
                                break
                            if args.max_runs_per_model and runs_per_model[model] >= args.max_runs_per_model:
                                continue
                            if runs_per_prompt_condition[condition] >= args.max_runs_per_prompt_condition:
                                continue
                            if args.max_runs_per_task and runs_per_task[task["task_id"]] >= args.max_runs_per_task:
                                continue
                            if (
                                args.max_runs_per_task_model
                                and runs_by_task_model[task["task_id"]][model] >= args.max_runs_per_task_model
                            ):
                                continue
                            if (
                                args.max_runs_per_task_prompt_condition
                                and runs_by_task_prompt_condition[task["task_id"]][condition]
                                >= args.max_runs_per_task_prompt_condition
                            ):
                                continue
                            run_index += 1
                            runs_per_model[model] += 1
                            runs_per_prompt_condition[condition] += 1
                            runs_per_task[task["task_id"]] += 1
                            runs_by_task_model[task["task_id"]][model] += 1
                            runs_by_model_prompt_condition[model][condition] += 1
                            runs_by_task_prompt_condition[task["task_id"]][condition] += 1
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
        else:
            # Default expansion order (no per-prompt cap): condition -> task -> repeat -> model.
            # Keeping model iteration innermost lets fair_model_allocation rotate continuously,
            # reducing model skew when other caps (e.g., task×prompt) truncate candidate runs.
            for condition in conditions:
                if stop_planning:
                    break
                for task in tasks:
                    if stop_planning:
                        break
                    for rep in range(1, args.repeats + 1):
                        if stop_planning:
                            break
                        for model in iter_models():
                            if total_cap_reached() and args.max_total_runs_mode == "cap":
                                stop_planning = True
                                break
                            if args.max_runs_per_model and runs_per_model[model] >= args.max_runs_per_model:
                                continue
                            if args.max_runs_per_task and runs_per_task[task["task_id"]] >= args.max_runs_per_task:
                                continue
                            if (
                                args.max_runs_per_task_model
                                and runs_by_task_model[task["task_id"]][model] >= args.max_runs_per_task_model
                            ):
                                continue
                            if (
                                args.max_runs_per_task_prompt_condition
                                and runs_by_task_prompt_condition[task["task_id"]][condition]
                                >= args.max_runs_per_task_prompt_condition
                            ):
                                continue
                            run_index += 1
                            runs_per_model[model] += 1
                            runs_per_prompt_condition[condition] += 1
                            runs_per_task[task["task_id"]] += 1
                            runs_by_task_model[task["task_id"]][model] += 1
                            runs_by_model_prompt_condition[model][condition] += 1
                            runs_by_task_prompt_condition[task["task_id"]][condition] += 1
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

        if args.max_total_runs_mode == "fail" and args.max_total_runs and len(plan) > args.max_total_runs:
            raise ValueError(
                f"planned runs ({len(plan)}) exceed --max-total-runs ({args.max_total_runs}); "
                "reduce models/conditions/repeats or increase cap, or use --max-total-runs-mode cap"
            )

        potential_runs_per_model = len(tasks) * len(conditions) * args.repeats
        potential_runs_total = potential_runs_per_model * len(models)
        potential_runs_per_condition = len(tasks) * len(models) * args.repeats
        potential_runs_per_task = len(models) * len(conditions) * args.repeats
        skipped_runs_by_model = {
            model: max(0, potential_runs_per_model - runs_per_model[model]) for model in models
        }
        skipped_runs_by_prompt_condition = {
            condition: max(0, potential_runs_per_condition - runs_per_prompt_condition[condition])
            for condition in conditions
        }
        skipped_runs_by_task = {
            task_id: max(0, potential_runs_per_task - runs_per_task[task_id])
            for task_id in runs_per_task
        }
        potential_runs_per_model_prompt_condition = len(tasks) * args.repeats
        potential_runs_by_model_prompt_condition = {
            model: {condition: potential_runs_per_model_prompt_condition for condition in conditions}
            for model in models
        }
        skipped_runs_by_model_prompt_condition = {
            model: {
                condition: max(
                    0,
                    potential_runs_by_model_prompt_condition[model][condition]
                    - runs_by_model_prompt_condition[model][condition],
                )
                for condition in conditions
            }
            for model in models
        }
        potential_runs_per_task_model = len(conditions) * args.repeats
        potential_runs_by_task_model = {
            task["task_id"]: {model: potential_runs_per_task_model for model in models}
            for task in tasks
        }
        skipped_runs_by_task_model = {
            task_id: {
                model: max(0, potential_runs_by_task_model[task_id][model] - runs_by_task_model[task_id][model])
                for model in models
            }
            for task_id in runs_by_task_model
        }
        potential_runs_per_task_prompt_condition = len(models) * args.repeats
        potential_runs_by_task_prompt_condition = {
            task["task_id"]: {condition: potential_runs_per_task_prompt_condition for condition in conditions}
            for task in tasks
        }
        skipped_runs_by_task_prompt_condition = {
            task_id: {
                condition: max(
                    0,
                    potential_runs_by_task_prompt_condition[task_id][condition]
                    - runs_by_task_prompt_condition[task_id][condition],
                )
                for condition in conditions
            }
            for task_id in runs_by_task_prompt_condition
        }

        payload: dict[str, Any] = {
            "schema_version": "v1",
            "task_set_id": task_set_id,
            "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "config": {
                "models": models,
                "prompt_conditions": conditions,
                "repeats": args.repeats,
                "cheap_first": bool(args.cheap_first),
                "fair_model_allocation": bool(args.fair_model_allocation),
                "max_total_runs": args.max_total_runs,
                "max_total_runs_mode": args.max_total_runs_mode,
                "max_runs_per_model": args.max_runs_per_model,
                "max_runs_per_prompt_condition": args.max_runs_per_prompt_condition,
                "max_runs_per_task": args.max_runs_per_task,
                "max_runs_per_task_model": args.max_runs_per_task_model,
                "max_runs_per_task_prompt_condition": args.max_runs_per_task_prompt_condition,
            },
            "summary": {
                "task_count": len(tasks),
                "model_count": len(models),
                "prompt_condition_count": len(conditions),
                "unique_call_units": len(tasks) * len(models) * len(conditions),
                "planned_runs_total": len(plan),
                "potential_runs_total": potential_runs_total,
                "skipped_runs_total": max(0, potential_runs_total - len(plan)),
                "planned_runs_by_model": runs_per_model,
                "planned_runs_by_prompt_condition": runs_per_prompt_condition,
                "planned_runs_by_task": runs_per_task,
                "planned_runs_by_model_prompt_condition": runs_by_model_prompt_condition,
                "planned_runs_by_task_model": runs_by_task_model,
                "planned_runs_by_task_prompt_condition": runs_by_task_prompt_condition,
                "potential_runs_by_model": {model: potential_runs_per_model for model in models},
                "potential_runs_by_prompt_condition": {
                    condition: potential_runs_per_condition for condition in conditions
                },
                "potential_runs_by_task": {task_id: potential_runs_per_task for task_id in runs_per_task},
                "potential_runs_by_model_prompt_condition": potential_runs_by_model_prompt_condition,
                "potential_runs_by_task_model": potential_runs_by_task_model,
                "potential_runs_by_task_prompt_condition": potential_runs_by_task_prompt_condition,
                "skipped_runs_by_model": skipped_runs_by_model,
                "skipped_runs_by_prompt_condition": skipped_runs_by_prompt_condition,
                "skipped_runs_by_task": skipped_runs_by_task,
                "skipped_runs_by_model_prompt_condition": skipped_runs_by_model_prompt_condition,
                "skipped_runs_by_task_model": skipped_runs_by_task_model,
                "skipped_runs_by_task_prompt_condition": skipped_runs_by_task_prompt_condition,
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
