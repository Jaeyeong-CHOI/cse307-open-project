#!/usr/bin/env python3
import csv
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURE = ROOT / "examples" / "batch-summary-fixture-whitespace-linecount.json"
SCRIPT = ROOT / "scripts" / "batch_report_summary.py"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def run_summary(*, top_k: int, include_diff_columns: bool) -> tuple[pathlib.Path, pathlib.Path]:
    summary_md = OUT / "fixture.summary.md"
    summary_csv = OUT / "fixture.csv"
    cmd = [
        "python3",
        str(SCRIPT),
        str(FIXTURE),
        "-o",
        str(summary_md),
        "--csv-output",
        str(summary_csv),
        "--top-k-mismatches",
        str(top_k),
    ]
    if include_diff_columns:
        cmd.append("--include-diff-columns")
    subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return summary_md, summary_csv


def assert_contains(content: str, needle: str) -> None:
    if needle not in content:
        raise AssertionError(f"expected to find '{needle}' in summary output")


def main() -> int:
    summary_md, summary_csv = run_summary(top_k=2, include_diff_columns=True)

    content = summary_md.read_text(encoding="utf-8")
    assert_contains(content, "- total_cases: 3")
    assert_contains(content, "- ok_cases: 1 (33.3%)")
    assert_contains(content, "- mismatch_cases: 2 (66.7%)")
    assert_contains(content, "- include_diff: true")

    # taxonomy frequency block should include whitespace/line-count drift tags.
    assert_contains(content, "- line_count_mismatch: 1")
    assert_contains(content, "- whitespace_or_blankline_drift: 1")
    assert_contains(content, "- token_stream_mismatch: 1")

    # mismatch highlight block should list top-k mismatches and include the drift case.
    assert_contains(content, "## Top 2 Mismatch Cases")
    assert_contains(content, "examples/blankline-drift.py (failure_taxonomy=line_count_mismatch, whitespace_or_blankline_drift)")

    # CSV export should include the fixture rows and taxonomy serialization.
    with summary_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 3:
        raise AssertionError(f"expected 3 CSV rows, got {len(rows)}")

    row_by_source = {row["source"]: row for row in rows}
    drift_row = row_by_source.get("examples/blankline-drift.py")
    if drift_row is None:
        raise AssertionError("missing blankline-drift row in CSV output")
    if drift_row["failure_taxonomy"] != "line_count_mismatch|whitespace_or_blankline_drift":
        raise AssertionError(
            "unexpected failure_taxonomy CSV encoding for blankline drift row: "
            f"{drift_row['failure_taxonomy']}"
        )

    # Optional diff columns should be present and populated for mismatch rows.
    expected_extra_cols = {
        "first_diff_line",
        "first_diff_src",
        "first_diff_restored",
        "first_token_diff_index",
        "first_token_diff_src",
        "first_token_diff_restored",
    }
    missing_cols = expected_extra_cols.difference(rows[0].keys())
    if missing_cols:
        raise AssertionError(f"missing CSV diff columns: {sorted(missing_cols)}")

    collision_row = row_by_source.get("examples/collision-risk-case.py")
    if collision_row is None:
        raise AssertionError("missing collision-risk row in CSV output")
    if collision_row["first_token_diff_index"] != "8":
        raise AssertionError(
            "expected first_token_diff_index=8 for collision-risk row, got "
            f"{collision_row['first_token_diff_index']}"
        )

    print("OK: batch_report_summary fixture regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
