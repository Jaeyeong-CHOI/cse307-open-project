#!/usr/bin/env python3
"""Regression tests for format_event_name_policy_modes.py."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "format_event_name_policy_modes.py"


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_all_permissive_outputs_compact_token_without_note() -> None:
    result = run_cmd("--summary", "false", "--snapshot", "false", "--metric", "false")
    assert result.returncode == 0
    assert "SPM=000" in result.stdout
    assert "event_name_policy_note" not in result.stdout


def test_mixed_modes_outputs_expected_token_with_note() -> None:
    result = run_cmd("--summary", "true", "--snapshot", "false", "--metric", "true")
    assert result.returncode == 0
    assert "SPM=101" in result.stdout
    assert "event_name_policy_note" in result.stdout


def test_invalid_bool_fails_fast() -> None:
    result = run_cmd("--summary", "yes", "--snapshot", "false", "--metric", "false")
    assert result.returncode != 0
    assert "expected boolean string 'true' or 'false'" in result.stderr


if __name__ == "__main__":
    test_all_permissive_outputs_compact_token_without_note()
    test_mixed_modes_outputs_expected_token_with_note()
    test_invalid_bool_fails_fast()
    print("ok")
