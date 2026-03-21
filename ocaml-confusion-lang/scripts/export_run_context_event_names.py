#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_context_schema import ALLOWED_EVENT_NAMES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export shared run_context event_name enum as JSON/Markdown"
    )
    parser.add_argument(
        "--json-output",
        required=True,
        help="Path to write machine-readable event enum JSON",
    )
    parser.add_argument(
        "--markdown-output",
        required=True,
        help="Path to write human-readable markdown event enum",
    )
    return parser.parse_args()


def build_markdown(events: list[str]) -> str:
    lines = [
        "# run_context.event_name allowed values",
        "",
        "Shared single source from `scripts/run_context_schema.py`.",
        "",
    ]
    lines.extend([f"- `{event}`" for event in events])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    events = sorted(ALLOWED_EVENT_NAMES)

    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": "run_context_event_names.v1",
        "count": len(events),
        "allowed_event_names": events,
    }
    json_output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_output.write_text(build_markdown(events), encoding="utf-8")

    print(f"OK: exported {len(events)} event names")
    print(f"- json: {json_output}")
    print(f"- markdown: {markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
