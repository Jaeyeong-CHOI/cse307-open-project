#!/usr/bin/env python3
"""Resolve event-name policy mode to normalized mode + strict boolean."""

from __future__ import annotations

import argparse
from typing import Iterable


VALID_MODES = {"permissive", "strict"}


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize workflow event-name policy mode and emit shell-friendly key=value lines."
        )
    )
    parser.add_argument("--mode", required=True)
    parser.add_argument("--field-name", required=True)
    return parser.parse_args(argv)


def _normalize_mode(raw: str, field_name: str) -> tuple[str, bool, str | None]:
    mode = raw.strip().lower()
    if mode in VALID_MODES:
        return mode, mode == "strict", None

    warning = (
        f"Invalid {field_name}='{raw}', fallback to permissive"
    )
    return "permissive", False, warning


def main() -> int:
    args = parse_args()
    mode, require_explicit, warning = _normalize_mode(args.mode, args.field_name)
    if warning:
        print(warning)

    print(f"mode={mode}")
    print(f"require_explicit_event_name={'true' if require_explicit else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
