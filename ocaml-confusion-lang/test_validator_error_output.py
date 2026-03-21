#!/usr/bin/env python3
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "validate_metric_schema.py"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    invalid = OUT / "metric.invalid.for-error-output.json"
    invalid.write_text(
        """{
  \"schema_version\": \"v1\",
  \"task_set_id\": \"task-set-v1-sample\",
  \"prompt_condition\": \"strict\",
  \"model\": \"gpt-5.3-codex\",
  \"metrics\": {
    \"acr\": 9,
    \"prr\": 0.2,
    \"esr\": 0.7,
    \"mfb\": -1
  }
}
""",
        encoding="utf-8",
    )

    proc = subprocess.run(
        ["python3", str(SCRIPT), str(invalid)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GITHUB_ACTIONS": "true"},
    )

    if proc.returncode == 0:
        raise AssertionError("expected validator failure for invalid metric payload")

    stderr = proc.stderr
    if "ERROR: Metric schema validation failed:" not in stderr:
        raise AssertionError(f"missing concise ERROR prefix: {stderr!r}")
    if "::error::Metric schema validation failed:" not in stderr:
        raise AssertionError(f"missing GitHub annotation: {stderr!r}")
    if "Traceback" in stderr:
        raise AssertionError(f"unexpected traceback noise: {stderr!r}")

    print("OK: validator error output format regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
