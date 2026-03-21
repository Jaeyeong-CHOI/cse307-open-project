#!/usr/bin/env python3
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent


def main() -> int:
    runner = (
        "from scripts.error_utils import emit_error;"
        "emit_error('percent % and newline\\nsecond line')"
    )

    proc = subprocess.run(
        ["python3", "-c", runner],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GITHUB_ACTIONS": "true"},
    )

    stderr = proc.stderr
    assert proc.returncode == 0
    assert "ERROR: percent % and newline" in stderr
    assert "::error::percent %25 and newline%0Asecond line" in stderr

    print("OK: error_utils annotation escaping regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
