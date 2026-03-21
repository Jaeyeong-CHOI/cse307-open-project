#!/usr/bin/env python3
"""Regression tests for resolve_event_name_modes.py."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "resolve_event_name_modes.py"


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_all_strict_maps_to_true() -> None:
    result = run_cmd(
        "--summary-mode",
        "strict",
        "--snapshot-mode",
        "strict",
        "--metric-mode",
        "strict",
    )
    assert result.returncode == 0
    assert "summary_mode=strict" in result.stdout
    assert "snapshot_mode=strict" in result.stdout
    assert "metric_mode=strict" in result.stdout
    assert "summary_require_explicit_event_name=true" in result.stdout
    assert "snapshot_require_explicit_event_name=true" in result.stdout
    assert "metric_require_explicit_event_name=true" in result.stdout


def test_mixed_modes_map_independently() -> None:
    result = run_cmd(
        "--summary-mode",
        "permissive",
        "--snapshot-mode",
        "strict",
        "--metric-mode",
        "permissive",
    )
    assert result.returncode == 0
    assert "summary_mode=permissive" in result.stdout
    assert "snapshot_mode=strict" in result.stdout
    assert "metric_mode=permissive" in result.stdout
    assert "summary_require_explicit_event_name=false" in result.stdout
    assert "snapshot_require_explicit_event_name=true" in result.stdout
    assert "metric_require_explicit_event_name=false" in result.stdout


def test_invalid_mode_falls_back_with_warning() -> None:
    result = run_cmd(
        "--summary-mode",
        "oops",
        "--snapshot-mode",
        "permissive",
        "--metric-mode",
        "strict",
    )
    assert result.returncode == 0
    assert "Invalid summary_event_name_mode='oops', fallback to permissive" in result.stdout
    assert "summary_mode=permissive" in result.stdout
    assert "summary_require_explicit_event_name=false" in result.stdout


if __name__ == "__main__":
    test_all_strict_maps_to_true()
    test_mixed_modes_map_independently()
    test_invalid_mode_falls_back_with_warning()
    print("ok")
