#!/usr/bin/env python3
"""Validate task-set schema JSON for confusion-lang experiment inputs."""

from __future__ import annotations

import argparse
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from error_utils import emit_error

REQUIRED_ROOT_KEYS = ["schema_version", "task_set_id", "tasks"]
REQUIRED_TASK_KEYS = ["task_id", "source"]
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}
OPTIONAL_ROOT_PATH_KEYS = ["manifest_path"]
OPTIONAL_ROOT_TEXT_KEYS = ["alias_set_id"]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_payload(payload: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{path}: root must be a JSON object"]

    for key in REQUIRED_ROOT_KEYS:
        if key not in payload:
            errors.append(f"{path}: missing required key '{key}'")

    for key in OPTIONAL_ROOT_TEXT_KEYS:
        if key in payload:
            value = payload[key]
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{path}: key '{key}' must be a non-empty string when present")

    for key in OPTIONAL_ROOT_PATH_KEYS:
        if key in payload:
            value = payload[key]
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{path}: key '{key}' must be a non-empty string when present")
            elif not value.endswith(".txt"):
                errors.append(f"{path}: key '{key}' must point to a .txt manifest when present")

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

        for key in REQUIRED_TASK_KEYS:
            if key not in task:
                errors.append(f"{where}: missing required key '{key}'")

        task_id = task.get("task_id")
        if isinstance(task_id, str):
            if not task_id.strip():
                errors.append(f"{where}: task_id must not be empty")
            elif task_id in seen_task_ids:
                errors.append(f"{where}: duplicate task_id '{task_id}'")
            else:
                seen_task_ids.add(task_id)
        elif "task_id" in task:
            errors.append(f"{where}: task_id must be a string")

        source = task.get("source")
        if isinstance(source, str):
            if not source.strip():
                errors.append(f"{where}: source must not be empty")
            elif not source.endswith(".py"):
                errors.append(f"{where}: source must point to a .py file")
        elif "source" in task:
            errors.append(f"{where}: source must be a string")

        if "difficulty" in task and task["difficulty"] not in ALLOWED_DIFFICULTIES:
            errors.append(
                f"{where}: difficulty must be one of {sorted(ALLOWED_DIFFICULTIES)} when present"
            )

        if "tags" in task:
            tags = task["tags"]
            if not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() for t in tags):
                errors.append(f"{where}: tags must be an array of non-empty strings when present")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate task-set schema JSON")
    parser.add_argument("task_set_json", type=Path, help="Path to task-set JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = load_json(args.task_set_json)
    errors = validate_payload(payload, args.task_set_json)
    if errors:
        emit_error("Task-set schema validation failed:\n" + "\n".join(f"- {err}" for err in errors))
        return 1
    print(f"OK: task-set schema valid ({args.task_set_json})")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, JSONDecodeError) as exc:
        emit_error(str(exc))
        raise SystemExit(1)
