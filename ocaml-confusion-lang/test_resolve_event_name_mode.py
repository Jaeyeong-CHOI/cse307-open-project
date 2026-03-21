#!/usr/bin/env python3
"""Regression tests for resolve_event_name_mode.py."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "resolve_event_name_mode.py"


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_strict_mode_maps_to_true() -> None:
    result = run_cmd("--mode", "strict", "--field-name", "summary_event_name_mode")
    assert result.returncode == 0
    assert "mode=strict" in result.stdout
    assert "require_explicit_event_name=true" in result.stdout


def test_permissive_mode_maps_to_false() -> None:
    result = run_cmd("--mode", "permissive", "--field-name", "snapshot_event_name_mode")
    assert result.returncode == 0
    assert "mode=permissive" in result.stdout
    assert "require_explicit_event_name=false" in result.stdout


def test_invalid_mode_falls_back_with_warning() -> None:
    result = run_cmd("--mode", "maybe", "--field-name", "metric_event_name_mode")
    assert result.returncode == 0
    assert "Invalid metric_event_name_mode='maybe', fallback to permissive" in result.stdout
    assert "mode=permissive" in result.stdout
    assert "require_explicit_event_name=false" in result.stdout


if __name__ == "__main__":
    test_strict_mode_maps_to_true()
    test_permissive_mode_maps_to_false()
    test_invalid_mode_falls_back_with_warning()
    print("ok")
