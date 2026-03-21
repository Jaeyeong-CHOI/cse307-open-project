#!/usr/bin/env python3
from __future__ import annotations

import argparse

from error_utils import emit_error
from run_context_schema import ALLOWED_EVENT_NAMES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a GitHub event_name against shared run_context schema"
    )
    parser.add_argument("event_name", help="GitHub event_name to validate")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    event_name = args.event_name.strip()
    if event_name not in ALLOWED_EVENT_NAMES:
        emit_error(
            f"event_name must be one of {sorted(ALLOWED_EVENT_NAMES)}",
            hints=[f"event_name={args.event_name}"],
        )
        return 1
    print(f"OK: run_context event_name valid ({event_name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
