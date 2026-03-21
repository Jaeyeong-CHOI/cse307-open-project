#!/usr/bin/env python3
"""Resolve summary/snapshot/metric event-name policy modes in one pass."""

from __future__ import annotations

import argparse
from typing import Iterable


VALID_MODES = {"permissive", "strict"}


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize summary/snapshot/metric event-name policy modes and emit shell-friendly key=value lines."
        )
    )
    parser.add_argument("--summary-mode", required=True)
    parser.add_argument("--snapshot-mode", required=True)
    parser.add_argument("--metric-mode", required=True)
    return parser.parse_args(argv)


def _normalize_mode(raw: str, field_name: str) -> tuple[str, bool, str | None]:
    mode = raw.strip().lower()
    if mode in VALID_MODES:
        return mode, mode == "strict", None

    warning = f"Invalid {field_name}='{raw}', fallback to permissive"
    return "permissive", False, warning


def _emit_mode(prefix: str, raw: str, field_name: str) -> None:
    mode, require_explicit, warning = _normalize_mode(raw, field_name)
    if warning:
        print(warning)

    print(f"{prefix}_mode={mode}")
    print(f"{prefix}_require_explicit_event_name={'true' if require_explicit else 'false'}")


def main() -> int:
    args = parse_args()
    _emit_mode("summary", args.summary_mode, "summary_event_name_mode")
    _emit_mode("snapshot", args.snapshot_mode, "snapshot_event_name_mode")
    _emit_mode("metric", args.metric_mode, "metric_event_name_mode")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
