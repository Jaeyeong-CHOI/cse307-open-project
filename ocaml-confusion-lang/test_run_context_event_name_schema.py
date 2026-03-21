from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / "scripts" / "validate_run_context_event_name.py"


def run_validator(event_name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(VALIDATOR), event_name],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_known_event_name_passes() -> None:
    ok = run_validator("pull_request_target")
    assert ok.returncode == 0, ok.stderr
    assert "OK: run_context event_name valid" in ok.stdout


def test_unknown_fallback_event_name_passes() -> None:
    ok = run_validator("unknown")
    assert ok.returncode == 0, ok.stderr
    assert "OK: run_context event_name valid" in ok.stdout


def test_unknown_event_name_fails() -> None:
    bad = run_validator("manual")
    assert bad.returncode != 0, "expected invalid event_name to fail"
    assert "ERROR:" in bad.stderr
    assert "event_name=manual" in bad.stderr


if __name__ == "__main__":
    test_known_event_name_passes()
    test_unknown_fallback_event_name_passes()
    test_unknown_event_name_fails()
    print("OK: run_context event_name schema regression passed")
