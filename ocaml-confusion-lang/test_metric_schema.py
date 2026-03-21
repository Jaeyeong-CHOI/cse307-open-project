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

    print("OK: metric schema regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
