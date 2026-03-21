#!/usr/bin/env python3
import csv
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURE = ROOT / "examples" / "batch-summary-fixture-whitespace-linecount.json"
SCRIPT = ROOT / "scripts" / "batch_report_summary.py"
ALT_WEIGHTS = ROOT / "examples" / "taxonomy-weights-severity-alt.json"
PROFILE_V2 = "v2-education-risk"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def run_summary(
    *,
    top_k: int,
    include_diff_columns: bool,
    mismatch_sort: str,
    taxonomy_weights: pathlib.Path | None = None,
    taxonomy_weight_profile: str | None = None,
    json_output: bool = False,
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path | None]:
    summary_md = OUT / "fixture.summary.md"
    summary_csv = OUT / "fixture.csv"
    summary_json = OUT / "fixture.summary.json" if json_output else None
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
        "--mismatch-sort",
        mismatch_sort,
    ]
    if include_diff_columns:
        cmd.append("--include-diff-columns")
    if taxonomy_weights is not None:
        cmd.extend(["--taxonomy-weights", str(taxonomy_weights)])
    if taxonomy_weight_profile is not None:
        cmd.extend(["--taxonomy-weight-profile", taxonomy_weight_profile])
    if summary_json is not None:
        cmd.extend(["--json-output", str(summary_json)])
    subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return summary_md, summary_csv, summary_json


def assert_contains(content: str, needle: str) -> None:
    if needle not in content:
        raise AssertionError(f"expected to find '{needle}' in summary output")


def main() -> int:
    summary_md, summary_csv, summary_json = run_summary(
        top_k=2,
        include_diff_columns=True,
        mismatch_sort="severity",
        json_output=True,
    )

    content = summary_md.read_text(encoding="utf-8")
    assert_contains(content, "- total_cases: 3")
    assert_contains(content, "- ok_cases: 1 (33.3%)")
    assert_contains(content, "- mismatch_cases: 2 (66.7%)")
    assert_contains(content, "- include_diff: true")
    assert_contains(content, "- taxonomy_weight_source: default:built-in")
    assert_contains(content, "- mismatch_severity_total: 130")
    assert_contains(content, "- mismatch_severity_avg: 65.0")

    if summary_json is None:
        raise AssertionError("expected JSON summary output path")
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    if payload["overview"]["total_cases"] != 3:
        raise AssertionError("expected total_cases=3 in JSON summary")
    if payload["quality_signals"]["mismatch_severity_total"] != 130:
        raise AssertionError("expected mismatch_severity_total=130 in JSON summary")
    if payload["top_mismatches"][0]["source"] != "examples/collision-risk-case.py":
        raise AssertionError("expected collision-risk case to be first top mismatch in JSON summary")

    # taxonomy frequency block should include whitespace/line-count drift tags.
    assert_contains(content, "- line_count_mismatch: 1")
    assert_contains(content, "- whitespace_or_blankline_drift: 1")
    assert_contains(content, "- token_stream_mismatch: 1")

    # severity-weighted taxonomy view should rank token-level failures above drift tags.
    assert_contains(content, "### Failure Taxonomy (severity-weighted)")
    assert_contains(content, "- token_stream_mismatch: weighted_score=40 (count=1, weight=40)")
    assert_contains(content, "- token_substitution_mismatch: weighted_score=35 (count=1, weight=35)")
    token_weighted_idx = content.find("- token_stream_mismatch: weighted_score=40 (count=1, weight=40)")
    linecount_weighted_idx = content.find("- line_count_mismatch: weighted_score=10 (count=1, weight=10)")
    if token_weighted_idx == -1 or linecount_weighted_idx == -1 or token_weighted_idx > linecount_weighted_idx:
        raise AssertionError("expected token_stream_mismatch to rank above line_count_mismatch in severity-weighted taxonomy")

    # mismatch highlight block should list top-k mismatches and include the drift case.
    assert_contains(content, "## Top 2 Mismatch Cases (sort=severity)")
    assert_contains(content, "examples/blankline-drift.py (failure_taxonomy=line_count_mismatch, whitespace_or_blankline_drift)")
    # severity sort should rank token-stream collision case ahead of whitespace drift case.
    collision_idx = content.find("examples/collision-risk-case.py (failure_taxonomy=token_stream_mismatch, token_substitution_mismatch)")
    drift_idx = content.find("examples/blankline-drift.py (failure_taxonomy=line_count_mismatch, whitespace_or_blankline_drift)")
    if collision_idx == -1 or drift_idx == -1 or collision_idx > drift_idx:
        raise AssertionError("expected collision-risk mismatch to be listed before blankline drift under severity sort")

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

    # Custom taxonomy weight config should affect severity-weighted section and ordering.
    alt_summary_md, _, _ = run_summary(
        top_k=2,
        include_diff_columns=False,
        mismatch_sort="severity",
        taxonomy_weights=ALT_WEIGHTS,
    )
    alt_content = alt_summary_md.read_text(encoding="utf-8")
    assert_contains(alt_content, f"- taxonomy_weight_source: file:{ALT_WEIGHTS}")
    assert_contains(alt_content, "- token_substitution_mismatch: weighted_score=60 (count=1, weight=60)")
    alt_collision_idx = alt_content.find(
        "examples/collision-risk-case.py (failure_taxonomy=token_stream_mismatch, token_substitution_mismatch)"
    )
    alt_drift_idx = alt_content.find(
        "examples/blankline-drift.py (failure_taxonomy=line_count_mismatch, whitespace_or_blankline_drift)"
    )
    if alt_collision_idx == -1 or alt_drift_idx == -1 or alt_collision_idx > alt_drift_idx:
        raise AssertionError("expected collision-risk mismatch to remain above blankline drift with custom weights")

    # Named taxonomy profile list should include versioned profile files.
    list_profiles = subprocess.run(
        ["python3", str(SCRIPT), "--list-taxonomy-profiles"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    profiles = set(list_profiles.stdout.split())
    if "v1-default" not in profiles or PROFILE_V2 not in profiles:
        raise AssertionError(f"expected v1-default and {PROFILE_V2} in profile list, got {sorted(profiles)}")

    # Named profile execution should match explicit custom-weight behavior.
    prof_summary_md, _, _ = run_summary(
        top_k=2,
        include_diff_columns=False,
        mismatch_sort="severity",
        taxonomy_weight_profile=PROFILE_V2,
    )
    prof_content = prof_summary_md.read_text(encoding="utf-8")
    assert_contains(prof_content, f"- taxonomy_weight_source: profile:{PROFILE_V2} ({ROOT / 'examples' / 'weights' / f'{PROFILE_V2}.json'})")
    assert_contains(prof_content, "- token_substitution_mismatch: weighted_score=60 (count=1, weight=60)")

    print("OK: batch_report_summary fixture regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
