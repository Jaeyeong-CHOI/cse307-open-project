#!/usr/bin/env python3
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURE = ROOT / "examples" / "batch-summary-fixture-whitespace-linecount.json"
TASK_SET_FIXTURE = ROOT / "examples" / "task-set-v1.json"
SUMMARY_SCRIPT = ROOT / "scripts" / "batch_report_summary.py"
VALIDATOR = ROOT / "scripts" / "validate_summary_payload.py"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def _run_validator(path: pathlib.Path, expect_ok: bool) -> None:
    result = subprocess.run(
        ["python3", str(VALIDATOR), str(path)],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if expect_ok and result.returncode != 0:
        raise RuntimeError(f"expected validator to pass: {path}")
    if (not expect_ok) and result.returncode == 0:
        raise RuntimeError(f"expected validator to fail: {path}")


def main() -> int:
    summary_json = OUT / "fixture.summary.schema-check.json"

    subprocess.run(
        [
            "python3",
            str(SUMMARY_SCRIPT),
            str(FIXTURE),
            "--json-output",
            str(summary_json),
            "--task-set-json",
            str(TASK_SET_FIXTURE),
            "-o",
            str(OUT / "fixture.summary.schema-check.md"),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    _run_validator(summary_json, expect_ok=True)

    invalid_summary = OUT / "fixture.summary.schema-check.invalid-lineage.json"
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    payload["metadata"]["task_set_lineage"]["manifest_path"] = ""
    invalid_summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    _run_validator(invalid_summary, expect_ok=False)

    print("OK: summary payload schema regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
