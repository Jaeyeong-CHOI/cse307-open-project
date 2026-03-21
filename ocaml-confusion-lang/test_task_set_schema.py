#!/usr/bin/env python3
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURE = ROOT / "examples" / "task-set-v1.json"
VALIDATOR = ROOT / "scripts" / "validate_task_set.py"
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

    invalid = OUT / "task-set.invalid.json"
    invalid.write_text(
        """{
  \"schema_version\": \"v1\",
  \"task_set_id\": \"broken\",
  \"tasks\": [
    {
      \"task_id\": \"dup\",
      \"source\": \"examples/sample.py\",
      \"difficulty\": \"easy\",
      \"tags\": [\"ok\"]
    },
    {
      \"task_id\": \"dup\",
      \"source\": \"examples/protected_literals.txt\",
      \"difficulty\": \"expert\",
      \"tags\": [\"\"]
    }
  ]
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
        raise AssertionError("expected invalid task-set payload to fail validation")

    print("OK: task-set schema regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
