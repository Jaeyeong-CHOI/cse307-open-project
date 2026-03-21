#!/usr/bin/env python3
"""Shared error output helpers for CLI scripts."""

from __future__ import annotations

import os
import sys


def _escape_github_annotation(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def emit_error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
        print(f"::error::{_escape_github_annotation(message)}", file=sys.stderr)
