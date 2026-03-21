#!/usr/bin/env python3
"""Format compact event-name policy mode lines for GitHub Step Summary."""

from __future__ import annotations

import argparse
from typing import Iterable


def _str_to_bool(raw: str) -> bool:
    value = raw.strip().lower()
    if value == "true":
        return True
    if value == "false":
        return False
    raise argparse.ArgumentTypeError(
        f"expected boolean string 'true' or 'false', got '{raw}'"
    )


def _mode_token(require_explicit: bool) -> str:
    return "1" if require_explicit else "0"


def build_summary_lines(
    summary_require_explicit: bool,
    snapshot_require_explicit: bool,
    metric_require_explicit: bool,
) -> list[str]:
    token = "".join(
        [
            _mode_token(summary_require_explicit),
            _mode_token(snapshot_require_explicit),
            _mode_token(metric_require_explicit),
        ]
    )
    lines = [
        f"- event_name_policy_modes: SPM={token} (1=strict,0=permissive; order=S/P/M)"
    ]
    if "1" in token:
        lines.append(
            "- event_name_policy_note: strict mode disables fallback event_name=unknown"
        )
    return lines


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit compact Step Summary lines for summary/snapshot/metric event-name policy modes."
    )
    parser.add_argument("--summary", required=True, type=_str_to_bool)
    parser.add_argument("--snapshot", required=True, type=_str_to_bool)
    parser.add_argument("--metric", required=True, type=_str_to_bool)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    lines = build_summary_lines(args.summary, args.snapshot, args.metric)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
