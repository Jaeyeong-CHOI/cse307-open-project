#!/usr/bin/env python3
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURE = ROOT / "examples" / "metric-schema-v1.json"
VALIDATOR = ROOT / "scripts" / "validate_metric_schema.py"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    subprocess.run(
        ["python3", str(VALIDATOR), str(FIXTURE)],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "python3",
            str(VALIDATOR),
            str(FIXTURE),
            "--schema-version-min",
            "1",
            "--schema-version-max",
            "2",
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    failed_range = subprocess.run(
        [
            "python3",
            str(VALIDATOR),
            str(FIXTURE),
            "--schema-version-min",
            "2",
            "--schema-version-max",
            "2",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if failed_range.returncode == 0:
        raise AssertionError("expected schema version range mismatch to fail validation")

    failed_invalid_range = subprocess.run(
        [
            "python3",
            str(VALIDATOR),
            str(FIXTURE),
            "--schema-version-min",
            "3",
            "--schema-version-max",
            "2",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if failed_invalid_range.returncode == 0:
        raise AssertionError("expected invalid schema version range arguments to fail")

    invalid = OUT / "metric.invalid.json"
    invalid.write_text(
        """{
  \"schema_version\": \"v1\",
  \"task_set_id\": \"task-set-v1-sample\",
  \"prompt_condition\": \"strict\",
  \"model\": \"gpt-5.3-codex\",
  \"metrics\": {
    \"acr\": 1.2,
    \"prr\": 0.2,
    \"esr\": 0.7,
    \"mfb\": -1
  }
}
""",
        encoding="utf-8",
    )

    failed = subprocess.run(
        ["python3", str(VALIDATOR), str(invalid)],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if failed.returncode == 0:
        raise AssertionError("expected invalid metric payload to fail validation")

    invalid_run_context = OUT / "metric.invalid.run-context.json"
    invalid_run_context.write_text(
        """{
  \"schema_version\": \"v1\",
  \"task_set_id\": \"task-set-v1-sample\",
  \"prompt_condition\": \"strict\",
  \"model\": \"gpt-5.3-codex\",
  \"metrics\": {
    \"acr\": 0.8,
    \"prr\": 0.2,
    \"esr\": 0.7,
    \"mfb\": 1.0
  },
  \"source_summary\": {
    \"run_context\": {
      \"run_id\": \"123\",
      \"event_name\": \"workflow_dispatch\"
    }
  }
}
""",
        encoding="utf-8",
    )

    failed_run_context = subprocess.run(
        ["python3", str(VALIDATOR), str(invalid_run_context)],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if failed_run_context.returncode == 0:
        raise AssertionError("expected invalid run_context pair to fail validation")

    print("OK: metric schema regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
