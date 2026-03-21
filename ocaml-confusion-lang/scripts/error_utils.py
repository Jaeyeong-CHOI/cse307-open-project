#!/usr/bin/env python3
"""Shared error output helpers for CLI scripts."""

from __future__ import annotations

import os
import sys


def _escape_github_annotation(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def emit_error(message: str, hints: list[str] | None = None) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    for hint in hints or []:
        print(f"HINT: {hint}", file=sys.stderr)

    if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
        annotation = message
        if hints:
            annotation += "\n" + "\n".join(f"HINT: {hint}" for hint in hints)
        print(f"::error::{_escape_github_annotation(annotation)}", file=sys.stderr)
