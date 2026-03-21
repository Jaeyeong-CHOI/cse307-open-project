#!/usr/bin/env python3
"""Validate taxonomy weight profile JSON schemas."""

from __future__ import annotations

import argparse
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from error_utils import emit_error


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_profile(payload: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{path}: root must be a JSON object"]

    default_weight = payload.get("default_weight")
    if default_weight is None:
        errors.append(f"{path}: missing required key 'default_weight'")
    elif not isinstance(default_weight, int):
        errors.append(f"{path}: 'default_weight' must be an integer")

    weights = payload.get("weights")
    if weights is None:
        errors.append(f"{path}: missing required key 'weights'")
    elif not isinstance(weights, dict):
        errors.append(f"{path}: 'weights' must be an object mapping taxonomy tag -> integer weight")
    else:
        for tag, weight in weights.items():
            if not isinstance(tag, str) or tag.strip() == "":
                errors.append(f"{path}: weight key must be a non-empty string (got {tag!r})")
            if not isinstance(weight, int):
                errors.append(f"{path}: weight for tag '{tag}' must be an integer")

    return errors


def iter_profile_paths(profile_dir: Path) -> list[Path]:
    if not profile_dir.exists():
        return []
    return sorted(p for p in profile_dir.glob("*.json") if p.is_file())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate taxonomy weight profile JSON schemas")
    parser.add_argument(
        "--profile-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "examples" / "weights",
        help="Directory containing taxonomy profile JSON files (default: ocaml-confusion-lang/examples/weights)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile_paths = iter_profile_paths(args.profile_dir)
    if not profile_paths:
        print(f"No taxonomy profile files found under: {args.profile_dir}")
        return 0

    all_errors: list[str] = []
    for profile_path in profile_paths:
        try:
            payload = load_json(profile_path)
        except Exception as exc:  # pragma: no cover - defensive
            all_errors.append(f"{profile_path}: failed to parse JSON ({exc})")
            continue
        all_errors.extend(validate_profile(payload, profile_path))

    if all_errors:
        emit_error(
            "Taxonomy profile schema validation failed:\n" + "\n".join(f"- {err}" for err in all_errors),
            hints=[f"profile_dir={args.profile_dir}", "required_keys=default_weight,weights"],
        )
        return 1

    print(f"OK: validated {len(profile_paths)} taxonomy profile file(s)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, JSONDecodeError) as exc:
        emit_error(str(exc))
        raise SystemExit(1)
