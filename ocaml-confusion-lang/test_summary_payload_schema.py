#!/usr/bin/env python3
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURE = ROOT / "examples" / "batch-summary-fixture-whitespace-linecount.json"
SUMMARY_SCRIPT = ROOT / "scripts" / "batch_report_summary.py"
VALIDATOR = ROOT / "scripts" / "validate_summary_payload.py"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    summary_json = OUT / "fixture.summary.schema-check.json"

    subprocess.run(
        [
            "python3",
            str(SUMMARY_SCRIPT),
            str(FIXTURE),
            "--json-output",
            str(summary_json),
            "-o",
            str(OUT / "fixture.summary.schema-check.md"),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    subprocess.run(
        ["python3", str(VALIDATOR), str(summary_json)],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("OK: summary payload schema regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
