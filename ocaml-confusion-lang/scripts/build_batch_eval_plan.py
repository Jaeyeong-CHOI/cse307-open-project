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


DEFAULT_PRESET_FILE = Path(__file__).resolve().parent.parent / "examples" / "batch-plan-presets.v1.json"
PRESET_SUMMARY_TSV_COLUMNS = [
    "preset",
    "models",
    "prompt_conditions",
    "repeats",
    "cheap_first",
    "fair_model_allocation",
    "max_total_runs",
    "max_total_runs_mode",
    "max_runs_per_model",
    "max_runs_per_prompt_condition",
    "max_runs_per_task",
    "max_runs_per_task_model",
    "max_runs_per_task_prompt_condition",
    "tags",
    "description_preview",
]
PRESET_SUMMARY_TSV_SCHEMA = "planner_preset_summary_tsv.v1"


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


def _validate_preset(name: str, preset: Any, preset_file: Path) -> dict[str, Any]:
    if not isinstance(preset, dict):
        raise ValueError(f"{preset_file}: presets.{name} must be an object")

    allowed_keys = {
        "models",
        "prompt_conditions",
        "repeats",
        "cheap_first",
        "fair_model_allocation",
        "max_total_runs",
        "max_total_runs_mode",
        "max_runs_per_model",
        "max_runs_per_prompt_condition",
        "max_runs_per_task",
        "max_runs_per_task_model",
        "max_runs_per_task_prompt_condition",
        "description",
        "tags",
    }
    unknown_keys = sorted(k for k in preset if k not in allowed_keys)
    if unknown_keys:
        raise ValueError(
            f"{preset_file}: presets.{name} contains unknown key(s): {', '.join(unknown_keys)}"
        )

    if "models" in preset and (not isinstance(preset["models"], str) or not preset["models"].strip()):
        raise ValueError(f"{preset_file}: presets.{name}.models must be a non-empty string")
    if "prompt_conditions" in preset and (
        not isinstance(preset["prompt_conditions"], str) or not preset["prompt_conditions"].strip()
    ):
        raise ValueError(f"{preset_file}: presets.{name}.prompt_conditions must be a non-empty string")

    int_keys = [
        "repeats",
        "max_total_runs",
        "max_runs_per_model",
        "max_runs_per_prompt_condition",
        "max_runs_per_task",
        "max_runs_per_task_model",
        "max_runs_per_task_prompt_condition",
    ]
    for key in int_keys:
        if key not in preset:
            continue
        value = preset[key]
        if not isinstance(value, int):
            raise ValueError(f"{preset_file}: presets.{name}.{key} must be an integer")
        if key == "repeats" and value < 1:
            raise ValueError(f"{preset_file}: presets.{name}.repeats must be >= 1")
        if key != "repeats" and value < 0:
            raise ValueError(f"{preset_file}: presets.{name}.{key} must be >= 0")

    bool_keys = ["cheap_first", "fair_model_allocation"]
    for key in bool_keys:
        if key in preset and not isinstance(preset[key], bool):
            raise ValueError(f"{preset_file}: presets.{name}.{key} must be a boolean")

    if "description" in preset and (
        not isinstance(preset["description"], str) or not preset["description"].strip()
    ):
        raise ValueError(f"{preset_file}: presets.{name}.description must be a non-empty string")

    if "tags" in preset:
        tags = preset["tags"]
        if not isinstance(tags, list) or not tags:
            raise ValueError(f"{preset_file}: presets.{name}.tags must be a non-empty array")
        for idx, tag in enumerate(tags):
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError(
                    f"{preset_file}: presets.{name}.tags[{idx}] must be a non-empty string"
                )

    if "max_total_runs_mode" in preset:
        mode = preset["max_total_runs_mode"]
        if mode not in {"fail", "cap"}:
            raise ValueError(
                f"{preset_file}: presets.{name}.max_total_runs_mode must be one of: fail, cap"
            )

    return preset


def load_preset_file(preset_file: Path) -> dict[str, Any]:
    payload = load_json(preset_file)
    schema_version = payload.get("schema_version")
    if schema_version != "v1":
        raise ValueError(f"{preset_file}: schema_version must be 'v1' (got '{schema_version}')")
    presets_raw = payload.get("presets")
    if not isinstance(presets_raw, dict):
        raise ValueError(f"{preset_file}: presets must be an object")

    return {name: _validate_preset(name, preset, preset_file) for name, preset in presets_raw.items()}


def load_preset_config(preset_file: Path, preset_name: str) -> dict[str, Any]:
    presets_raw = load_preset_file(preset_file)
    preset = presets_raw.get(preset_name)
    if not isinstance(preset, dict):
        available = ", ".join(sorted(presets_raw.keys())) or "<none>"
        raise ValueError(
            f"{preset_file}: unknown preset '{preset_name}' (available: {available})"
        )
    return preset


def resolve_preset_with_defaults(preset: dict[str, Any]) -> dict[str, Any]:
    raw_tags = preset.get("tags", [])
    tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()] if isinstance(raw_tags, list) else []
    return {
        "models": str(preset.get("models", "")),
        "prompt_conditions": str(preset.get("prompt_conditions", "")),
        "repeats": int(preset.get("repeats", 1)),
        "cheap_first": bool(preset.get("cheap_first", False)),
        "fair_model_allocation": bool(preset.get("fair_model_allocation", False)),
        "max_total_runs": int(preset.get("max_total_runs", 0)),
        "max_total_runs_mode": str(preset.get("max_total_runs_mode", "fail")),
        "max_runs_per_model": int(preset.get("max_runs_per_model", 0)),
        "max_runs_per_prompt_condition": int(preset.get("max_runs_per_prompt_condition", 0)),
        "max_runs_per_task": int(preset.get("max_runs_per_task", 0)),
        "max_runs_per_task_model": int(preset.get("max_runs_per_task_model", 0)),
        "max_runs_per_task_prompt_condition": int(preset.get("max_runs_per_task_prompt_condition", 0)),
        "description": str(preset.get("description", "")),
        "tags": tags,
    }


def _matches_preset_tags(
    preset: dict[str, Any], required_tags: set[str], match_mode: str = "all"
) -> bool:
    if not required_tags:
        return True
    raw_tags = preset.get("tags", [])
    if not isinstance(raw_tags, list):
        return False
    preset_tags = {str(tag).strip().lower() for tag in raw_tags if str(tag).strip()}
    if match_mode == "any":
        return any(tag in preset_tags for tag in required_tags)
    return required_tags.issubset(preset_tags)


def _preset_description_preview(raw_description: str, max_len: int = 60) -> str:
    normalized = " ".join(str(raw_description).replace("\t", " ").split())
    if not normalized:
        return "-"
    if len(normalized) <= max_len:
        return normalized
    return f"{normalized[: max_len - 3].rstrip()}..."


def _format_preset_summary_line(name: str, resolved: dict[str, Any]) -> str:
    tags = resolved.get("tags", [])
    tag_value = ",".join(tags) if isinstance(tags, list) and tags else "-"
    description_preview = _preset_description_preview(resolved.get("description", ""))
    return (
        f"{name}\tmodels={resolved['models']}\tprompt_conditions={resolved['prompt_conditions']}\t"
        f"repeats={resolved['repeats']}\tcheap_first={str(resolved['cheap_first']).lower()}\t"
        f"fair_model_allocation={str(resolved['fair_model_allocation']).lower()}\t"
        f"max_total_runs={resolved['max_total_runs']}\tmax_total_runs_mode={resolved['max_total_runs_mode']}\t"
        f"max_runs_per_model={resolved['max_runs_per_model']}\t"
        f"max_runs_per_prompt_condition={resolved['max_runs_per_prompt_condition']}\t"
        f"max_runs_per_task={resolved['max_runs_per_task']}\t"
        f"max_runs_per_task_model={resolved['max_runs_per_task_model']}\t"
        f"max_runs_per_task_prompt_condition={resolved['max_runs_per_task_prompt_condition']}\t"
        f"tags={tag_value}\tdescription={description_preview}"
    )


def _emit_preset_summary_tsv_header(with_schema_header: bool) -> None:
    if with_schema_header:
        print(f"# schema={PRESET_SUMMARY_TSV_SCHEMA}")
    print("\t".join(PRESET_SUMMARY_TSV_COLUMNS))


def _format_preset_summary_tsv_row(name: str, resolved: dict[str, Any]) -> str:
    tags = resolved.get("tags", [])
    tag_value = ",".join(tags) if isinstance(tags, list) and tags else "-"
    row = [
        name,
        str(resolved["models"]),
        str(resolved["prompt_conditions"]),
        str(resolved["repeats"]),
        str(resolved["cheap_first"]).lower(),
        str(resolved["fair_model_allocation"]).lower(),
        str(resolved["max_total_runs"]),
        str(resolved["max_total_runs_mode"]),
        str(resolved["max_runs_per_model"]),
        str(resolved["max_runs_per_prompt_condition"]),
        str(resolved["max_runs_per_task"]),
        str(resolved["max_runs_per_task_model"]),
        str(resolved["max_runs_per_task_prompt_condition"]),
        tag_value,
        _preset_description_preview(resolved.get("description", "")),
    ]
    return "\t".join(item.replace("\t", " ") for item in row)


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


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _ratio_map_1d(planned: dict[str, int], potential: dict[str, int]) -> dict[str, float]:
    return {key: _safe_ratio(planned[key], potential[key]) for key in planned}


def _ratio_map_2d(
    planned: dict[str, dict[str, int]], potential: dict[str, dict[str, int]]
) -> dict[str, dict[str, float]]:
    return {
        outer_key: {
            inner_key: _safe_ratio(planned[outer_key][inner_key], potential[outer_key][inner_key])
            for inner_key in planned[outer_key]
        }
        for outer_key in planned
    }


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
    parser.add_argument("task_set_json", nargs="?", type=Path, help="Path to task-set v1 JSON")
    parser.add_argument("--preset", default=None, help="Preset name from --preset-file")
    parser.add_argument(
        "--show-preset",
        default=None,
        help="Show one preset resolved with planner defaults and exit",
    )
    parser.add_argument(
        "--show-preset-format",
        choices=("json", "summary", "summary-tsv"),
        default="json",
        help="Output format for --show-preset (default: json)",
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List available presets from --preset-file and exit",
    )
    parser.add_argument(
        "--list-presets-format",
        choices=("names", "json", "resolved-json", "summary", "summary-tsv"),
        default="names",
        help="Output format for --list-presets (default: names)",
    )
    parser.add_argument(
        "--list-presets-tag",
        default=None,
        help="Optional tag filter for --list-presets (comma-separated, case-insensitive)",
    )
    parser.add_argument(
        "--list-presets-tag-match",
        choices=("all", "any"),
        default="all",
        help="Tag match mode for --list-presets-tag: all (default, AND) or any (OR)",
    )
    parser.add_argument(
        "--summary-tsv-with-schema-header",
        action="store_true",
        help=(
            "Prefix summary-tsv output with '# schema=<id>' comment for parser-friendly format versioning"
        ),
    )
    parser.add_argument(
        "--preset-file",
        type=Path,
        default=DEFAULT_PRESET_FILE,
        help=f"Preset file path (default: {DEFAULT_PRESET_FILE})",
    )
    parser.add_argument("--models", default=None, help="Comma-separated model ids")
    parser.add_argument(
        "--prompt-conditions",
        default=None,
        help="Comma-separated prompt condition labels (e.g. base,strict,few-shot)",
    )
    parser.add_argument("--repeats", type=int, default=None, help="Repeat count per task/condition/model")
    parser.add_argument("--max-total-runs", type=int, default=None, help="Optional hard cap for total planned runs (0 disables cap)")
    parser.add_argument(
        "--max-total-runs-mode",
        choices=("fail", "cap"),
        default=None,
        help="Behavior when --max-total-runs is set: fail (default) or cap plan length",
    )
    parser.add_argument("--max-runs-per-model", type=int, default=None, help="Optional per-model cap for planned runs (0 disables cap)")
    parser.add_argument("--max-runs-per-prompt-condition", type=int, default=None, help="Optional per-prompt-condition cap for planned runs (0 disables cap)")
    parser.add_argument("--max-runs-per-task", type=int, default=None, help="Optional per-task cap for planned runs (0 disables cap)")
    parser.add_argument("--max-runs-per-task-model", type=int, default=None, help="Optional per-task×model cap for planned runs (0 disables cap)")
    parser.add_argument("--max-runs-per-task-prompt-condition", type=int, default=None, help="Optional per-task×prompt-condition cap for planned runs (0 disables cap)")
    parser.add_argument(
        "--cheap-first",
        action="store_true",
        default=None,
        help="Order model runs using a cheap-first heuristic before expanding matrix",
    )
    parser.add_argument(
        "--fair-model-allocation",
        action="store_true",
        default=None,
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

        if args.show_preset:
            preset = load_preset_config(args.preset_file, args.show_preset)
            resolved = resolve_preset_with_defaults(preset)
            # Preview final values after optional CLI overrides, mirroring plan-generation precedence.
            if args.models is not None:
                resolved["models"] = args.models
            if args.prompt_conditions is not None:
                resolved["prompt_conditions"] = args.prompt_conditions
            if args.repeats is not None:
                resolved["repeats"] = args.repeats
            if args.cheap_first is not None:
                resolved["cheap_first"] = bool(args.cheap_first)
            if args.fair_model_allocation is not None:
                resolved["fair_model_allocation"] = bool(args.fair_model_allocation)
            if args.max_total_runs is not None:
                resolved["max_total_runs"] = args.max_total_runs
            if args.max_total_runs_mode is not None:
                resolved["max_total_runs_mode"] = args.max_total_runs_mode
            if args.max_runs_per_model is not None:
                resolved["max_runs_per_model"] = args.max_runs_per_model
            if args.max_runs_per_prompt_condition is not None:
                resolved["max_runs_per_prompt_condition"] = args.max_runs_per_prompt_condition
            if args.max_runs_per_task is not None:
                resolved["max_runs_per_task"] = args.max_runs_per_task
            if args.max_runs_per_task_model is not None:
                resolved["max_runs_per_task_model"] = args.max_runs_per_task_model
            if args.max_runs_per_task_prompt_condition is not None:
                resolved["max_runs_per_task_prompt_condition"] = args.max_runs_per_task_prompt_condition

            if resolved["repeats"] < 1:
                raise ValueError("--repeats must be >= 1")
            if resolved["max_total_runs"] < 0:
                raise ValueError("--max-total-runs must be >= 0")
            if resolved["max_total_runs_mode"] not in {"fail", "cap"}:
                raise ValueError("--max-total-runs-mode must be one of: fail, cap")
            if resolved["max_runs_per_model"] < 0:
                raise ValueError("--max-runs-per-model must be >= 0")
            if resolved["max_runs_per_prompt_condition"] < 0:
                raise ValueError("--max-runs-per-prompt-condition must be >= 0")
            if resolved["max_runs_per_task"] < 0:
                raise ValueError("--max-runs-per-task must be >= 0")
            if resolved["max_runs_per_task_model"] < 0:
                raise ValueError("--max-runs-per-task-model must be >= 0")
            if resolved["max_runs_per_task_prompt_condition"] < 0:
                raise ValueError("--max-runs-per-task-prompt-condition must be >= 0")

            payload = {
                "schema_version": "v1",
                "preset_file": str(args.preset_file),
                "preset": args.show_preset,
                "resolved": resolved,
            }
            if args.show_preset_format == "summary":
                print(_format_preset_summary_line(args.show_preset, resolved))
                return 0
            if args.show_preset_format == "summary-tsv":
                _emit_preset_summary_tsv_header(args.summary_tsv_with_schema_header)
                print(_format_preset_summary_tsv_row(args.show_preset, resolved))
                return 0
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.list_presets:
            presets = load_preset_file(args.preset_file)
            required_tags: set[str] = set()
            if args.list_presets_tag:
                required_tags = {tag.strip().lower() for tag in args.list_presets_tag.split(",") if tag.strip()}
                if not required_tags:
                    raise ValueError("--list-presets-tag must include at least one non-empty tag")
            filtered_presets = {
                name: preset
                for name, preset in presets.items()
                if isinstance(preset, dict)
                and _matches_preset_tags(
                    preset,
                    required_tags,
                    match_mode=args.list_presets_tag_match,
                )
            }
            if args.list_presets_format == "json":
                print(json.dumps({"schema_version": "v1", "presets": filtered_presets}, ensure_ascii=False, indent=2))
                return 0
            preset_names = sorted(filtered_presets.keys())
            if args.list_presets_format == "resolved-json":
                resolved_presets: dict[str, dict[str, Any]] = {}
                for name in preset_names:
                    preset = filtered_presets[name]
                    if not isinstance(preset, dict):
                        raise ValueError(f"{args.preset_file}: presets.{name} must be an object")
                    resolved_presets[name] = resolve_preset_with_defaults(preset)
                print(
                    json.dumps(
                        {
                            "schema_version": "v1",
                            "preset_file": str(args.preset_file),
                            "presets": resolved_presets,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            if args.list_presets_format == "summary":
                for name in preset_names:
                    preset = filtered_presets[name]
                    if not isinstance(preset, dict):
                        raise ValueError(f"{args.preset_file}: presets.{name} must be an object")
                    resolved = resolve_preset_with_defaults(preset)
                    print(_format_preset_summary_line(name, resolved))
                return 0
            if args.list_presets_format == "summary-tsv":
                _emit_preset_summary_tsv_header(args.summary_tsv_with_schema_header)
                for name in preset_names:
                    preset = filtered_presets[name]
                    if not isinstance(preset, dict):
                        raise ValueError(f"{args.preset_file}: presets.{name} must be an object")
                    resolved = resolve_preset_with_defaults(preset)
                    print(_format_preset_summary_tsv_row(name, resolved))
                return 0
            for name in preset_names:
                print(name)
            return 0

        if args.task_set_json is None:
            raise ValueError("task_set_json is required (or use --list-presets)")

        preset: dict[str, Any] = {}
        if args.preset:
            preset = load_preset_config(args.preset_file, args.preset)

        models_raw = args.models if args.models is not None else preset.get("models")
        conditions_raw = (
            args.prompt_conditions
            if args.prompt_conditions is not None
            else preset.get("prompt_conditions")
        )
        if not isinstance(models_raw, str) or not models_raw.strip():
            raise ValueError("--models is required (or provide preset.models)")
        if not isinstance(conditions_raw, str) or not conditions_raw.strip():
            raise ValueError("--prompt-conditions is required (or provide preset.prompt_conditions)")

        repeats = args.repeats if args.repeats is not None else int(preset.get("repeats", 1))
        max_total_runs = (
            args.max_total_runs if args.max_total_runs is not None else int(preset.get("max_total_runs", 0))
        )
        max_total_runs_mode = (
            args.max_total_runs_mode
            if args.max_total_runs_mode is not None
            else str(preset.get("max_total_runs_mode", "fail"))
        )
        max_runs_per_model = (
            args.max_runs_per_model if args.max_runs_per_model is not None else int(preset.get("max_runs_per_model", 0))
        )
        max_runs_per_prompt_condition = (
            args.max_runs_per_prompt_condition
            if args.max_runs_per_prompt_condition is not None
            else int(preset.get("max_runs_per_prompt_condition", 0))
        )
        max_runs_per_task = (
            args.max_runs_per_task if args.max_runs_per_task is not None else int(preset.get("max_runs_per_task", 0))
        )
        max_runs_per_task_model = (
            args.max_runs_per_task_model
            if args.max_runs_per_task_model is not None
            else int(preset.get("max_runs_per_task_model", 0))
        )
        max_runs_per_task_prompt_condition = (
            args.max_runs_per_task_prompt_condition
            if args.max_runs_per_task_prompt_condition is not None
            else int(preset.get("max_runs_per_task_prompt_condition", 0))
        )
        cheap_first = args.cheap_first if args.cheap_first is not None else bool(preset.get("cheap_first", False))
        fair_model_allocation = (
            args.fair_model_allocation
            if args.fair_model_allocation is not None
            else bool(preset.get("fair_model_allocation", False))
        )

        if repeats < 1:
            raise ValueError("--repeats must be >= 1")
        if max_total_runs < 0:
            raise ValueError("--max-total-runs must be >= 0")
        if max_total_runs_mode not in {"fail", "cap"}:
            raise ValueError("--max-total-runs-mode must be one of: fail, cap")
        if max_runs_per_model < 0:
            raise ValueError("--max-runs-per-model must be >= 0")
        if max_runs_per_prompt_condition < 0:
            raise ValueError("--max-runs-per-prompt-condition must be >= 0")
        if max_runs_per_task < 0:
            raise ValueError("--max-runs-per-task must be >= 0")
        if max_runs_per_task_model < 0:
            raise ValueError("--max-runs-per-task-model must be >= 0")
        if max_runs_per_task_prompt_condition < 0:
            raise ValueError("--max-runs-per-task-prompt-condition must be >= 0")

        task_set = load_json(args.task_set_json)
        task_set_id, tasks = validate_task_set(task_set, args.task_set_json)

        models = _dedupe_keep_order(parse_csv_list(models_raw, "--models"))
        conditions = _dedupe_keep_order(parse_csv_list(conditions_raw, "--prompt-conditions"))

        if cheap_first:
            models = sorted(models, key=_cheap_first_rank)

        plan: list[dict[str, Any]] = []
        run_index = 0
        model_cursor = 0
        stop_planning = False

        runs_per_model: dict[str, int] = {model: 0 for model in models}

        def total_cap_reached() -> bool:
            return bool(max_total_runs and len(plan) >= max_total_runs)

        def iter_models() -> list[str]:
            nonlocal model_cursor
            if not fair_model_allocation or len(models) <= 1:
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
        runs_by_repeat_index: dict[str, int] = {str(rep): 0 for rep in range(1, repeats + 1)}
        if max_runs_per_prompt_condition:
            # Condition-first expansion keeps per-condition caps from starving later models.
            for condition in conditions:
                if stop_planning:
                    break
                for task in tasks:
                    if stop_planning:
                        break
                    for rep in range(1, repeats + 1):
                        if stop_planning:
                            break
                        for model in iter_models():
                            if total_cap_reached() and max_total_runs_mode == "cap":
                                stop_planning = True
                                break
                            if max_runs_per_model and runs_per_model[model] >= max_runs_per_model:
                                continue
                            if runs_per_prompt_condition[condition] >= max_runs_per_prompt_condition:
                                continue
                            if max_runs_per_task and runs_per_task[task["task_id"]] >= max_runs_per_task:
                                continue
                            if (
                                max_runs_per_task_model
                                and runs_by_task_model[task["task_id"]][model] >= max_runs_per_task_model
                            ):
                                continue
                            if (
                                max_runs_per_task_prompt_condition
                                and runs_by_task_prompt_condition[task["task_id"]][condition]
                                >= max_runs_per_task_prompt_condition
                            ):
                                continue
                            run_index += 1
                            runs_per_model[model] += 1
                            runs_per_prompt_condition[condition] += 1
                            runs_per_task[task["task_id"]] += 1
                            runs_by_task_model[task["task_id"]][model] += 1
                            runs_by_model_prompt_condition[model][condition] += 1
                            runs_by_task_prompt_condition[task["task_id"]][condition] += 1
                            runs_by_repeat_index[str(rep)] += 1
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
                    for rep in range(1, repeats + 1):
                        if stop_planning:
                            break
                        for model in iter_models():
                            if total_cap_reached() and max_total_runs_mode == "cap":
                                stop_planning = True
                                break
                            if max_runs_per_model and runs_per_model[model] >= max_runs_per_model:
                                continue
                            if max_runs_per_task and runs_per_task[task["task_id"]] >= max_runs_per_task:
                                continue
                            if (
                                max_runs_per_task_model
                                and runs_by_task_model[task["task_id"]][model] >= max_runs_per_task_model
                            ):
                                continue
                            if (
                                max_runs_per_task_prompt_condition
                                and runs_by_task_prompt_condition[task["task_id"]][condition]
                                >= max_runs_per_task_prompt_condition
                            ):
                                continue
                            run_index += 1
                            runs_per_model[model] += 1
                            runs_per_prompt_condition[condition] += 1
                            runs_per_task[task["task_id"]] += 1
                            runs_by_task_model[task["task_id"]][model] += 1
                            runs_by_model_prompt_condition[model][condition] += 1
                            runs_by_task_prompt_condition[task["task_id"]][condition] += 1
                            runs_by_repeat_index[str(rep)] += 1
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

        if max_total_runs_mode == "fail" and max_total_runs and len(plan) > max_total_runs:
            raise ValueError(
                f"planned runs ({len(plan)}) exceed --max-total-runs ({max_total_runs}); "
                "reduce models/conditions/repeats or increase cap, or use --max-total-runs-mode cap"
            )

        potential_runs_per_model = len(tasks) * len(conditions) * repeats
        potential_runs_total = potential_runs_per_model * len(models)
        potential_runs_per_condition = len(tasks) * len(models) * repeats
        potential_runs_per_task = len(models) * len(conditions) * repeats
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
        potential_runs_per_model_prompt_condition = len(tasks) * repeats
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
        potential_runs_per_task_model = len(conditions) * repeats
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
        potential_runs_per_task_prompt_condition = len(models) * repeats
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
        potential_runs_per_repeat_index = len(tasks) * len(models) * len(conditions)
        potential_runs_by_repeat_index = {
            str(rep): potential_runs_per_repeat_index for rep in range(1, repeats + 1)
        }
        skipped_runs_by_repeat_index = {
            repeat_key: max(0, potential_runs_by_repeat_index[repeat_key] - runs_by_repeat_index[repeat_key])
            for repeat_key in runs_by_repeat_index
        }

        planned_run_ratio_total = _safe_ratio(len(plan), potential_runs_total)
        planned_run_ratio_by_model = _ratio_map_1d(runs_per_model, {model: potential_runs_per_model for model in models})
        planned_run_ratio_by_prompt_condition = _ratio_map_1d(
            runs_per_prompt_condition,
            {condition: potential_runs_per_condition for condition in conditions},
        )
        planned_run_ratio_by_task = _ratio_map_1d(runs_per_task, {task_id: potential_runs_per_task for task_id in runs_per_task})
        planned_run_ratio_by_model_prompt_condition = _ratio_map_2d(
            runs_by_model_prompt_condition,
            potential_runs_by_model_prompt_condition,
        )
        planned_run_ratio_by_task_model = _ratio_map_2d(runs_by_task_model, potential_runs_by_task_model)
        planned_run_ratio_by_task_prompt_condition = _ratio_map_2d(
            runs_by_task_prompt_condition,
            potential_runs_by_task_prompt_condition,
        )
        planned_run_ratio_by_repeat_index = _ratio_map_1d(
            runs_by_repeat_index,
            potential_runs_by_repeat_index,
        )

        payload: dict[str, Any] = {
            "schema_version": "v1",
            "task_set_id": task_set_id,
            "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "config": {
                "preset": args.preset,
                "preset_file": str(args.preset_file) if args.preset else None,
                "models": models,
                "prompt_conditions": conditions,
                "repeats": repeats,
                "cheap_first": bool(cheap_first),
                "fair_model_allocation": bool(fair_model_allocation),
                "max_total_runs": max_total_runs,
                "max_total_runs_mode": max_total_runs_mode,
                "max_runs_per_model": max_runs_per_model,
                "max_runs_per_prompt_condition": max_runs_per_prompt_condition,
                "max_runs_per_task": max_runs_per_task,
                "max_runs_per_task_model": max_runs_per_task_model,
                "max_runs_per_task_prompt_condition": max_runs_per_task_prompt_condition,
            },
            "summary": {
                "task_count": len(tasks),
                "model_count": len(models),
                "prompt_condition_count": len(conditions),
                "unique_call_units": len(tasks) * len(models) * len(conditions),
                "planned_runs_total": len(plan),
                "potential_runs_total": potential_runs_total,
                "skipped_runs_total": max(0, potential_runs_total - len(plan)),
                "planned_run_ratio_total": planned_run_ratio_total,
                "planned_run_ratio_by_model": planned_run_ratio_by_model,
                "planned_run_ratio_by_prompt_condition": planned_run_ratio_by_prompt_condition,
                "planned_run_ratio_by_task": planned_run_ratio_by_task,
                "planned_run_ratio_by_model_prompt_condition": planned_run_ratio_by_model_prompt_condition,
                "planned_run_ratio_by_task_model": planned_run_ratio_by_task_model,
                "planned_run_ratio_by_task_prompt_condition": planned_run_ratio_by_task_prompt_condition,
                "planned_run_ratio_by_repeat_index": planned_run_ratio_by_repeat_index,
                "planned_runs_by_model": runs_per_model,
                "planned_runs_by_prompt_condition": runs_per_prompt_condition,
                "planned_runs_by_task": runs_per_task,
                "planned_runs_by_model_prompt_condition": runs_by_model_prompt_condition,
                "planned_runs_by_task_model": runs_by_task_model,
                "planned_runs_by_task_prompt_condition": runs_by_task_prompt_condition,
                "planned_runs_by_repeat_index": runs_by_repeat_index,
                "potential_runs_by_model": {model: potential_runs_per_model for model in models},
                "potential_runs_by_prompt_condition": {
                    condition: potential_runs_per_condition for condition in conditions
                },
                "potential_runs_by_task": {task_id: potential_runs_per_task for task_id in runs_per_task},
                "potential_runs_by_model_prompt_condition": potential_runs_by_model_prompt_condition,
                "potential_runs_by_task_model": potential_runs_by_task_model,
                "potential_runs_by_task_prompt_condition": potential_runs_by_task_prompt_condition,
                "potential_runs_by_repeat_index": potential_runs_by_repeat_index,
                "skipped_runs_by_model": skipped_runs_by_model,
                "skipped_runs_by_prompt_condition": skipped_runs_by_prompt_condition,
                "skipped_runs_by_task": skipped_runs_by_task,
                "skipped_runs_by_model_prompt_condition": skipped_runs_by_model_prompt_condition,
                "skipped_runs_by_task_model": skipped_runs_by_task_model,
                "skipped_runs_by_task_prompt_condition": skipped_runs_by_task_prompt_condition,
                "skipped_runs_by_repeat_index": skipped_runs_by_repeat_index,
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
