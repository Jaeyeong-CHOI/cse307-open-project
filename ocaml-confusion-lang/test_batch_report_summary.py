#!/usr/bin/env python3
import csv
import json
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURE = ROOT / "examples" / "batch-summary-fixture-whitespace-linecount.json"
SCRIPT = ROOT / "scripts" / "batch_report_summary.py"
ALT_WEIGHTS = ROOT / "examples" / "taxonomy-weights-severity-alt.json"
PROFILE_V2 = "v2-education-risk"
TASK_SET = ROOT / "examples" / "task-set-v1.json"
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
    only_mismatches: bool = False,
    task_set_json: pathlib.Path | None = None,
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
    if only_mismatches:
        cmd.append("--only-mismatches")
    if task_set_json is not None:
        cmd.extend(["--task-set-json", str(task_set_json)])
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
        task_set_json=TASK_SET,
    )

    content = summary_md.read_text(encoding="utf-8")
    assert_contains(content, "- total_cases: 3")
    assert_contains(content, "- ok_cases: 1 (33.3%)")
    assert_contains(content, "- mismatch_cases: 2 (66.7%)")
    assert_contains(content, "- include_diff: true")
    assert_contains(content, "- taxonomy_weight_source: default:built-in")
    assert_contains(content, "- cases_scope: all")
    assert_contains(content, "- task_set_id: cse307-task-set-v1")
    assert_contains(content, "- alias_set_id: case-c2")
    assert_contains(content, "- manifest_path: examples/manifest-v1.txt")
    assert_contains(content, "- mismatch_severity_total: 130")
    assert_contains(content, "- mismatch_severity_avg: 65.0")

    if summary_json is None:
        raise AssertionError("expected JSON summary output path")
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise AssertionError("expected metadata object in JSON summary")
    for key in ["schema_version", "generated_at_utc", "input_report"]:
        if key not in metadata:
            raise AssertionError(f"expected metadata.{key} in JSON summary")
    lineage = metadata.get("task_set_lineage")
    if not isinstance(lineage, dict):
        raise AssertionError("expected metadata.task_set_lineage in JSON summary")
    if lineage.get("task_set_id") != "cse307-task-set-v1":
        raise AssertionError("unexpected task_set_id in summary metadata lineage")

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

    # --only-mismatches should reduce cases in markdown/json/csv to mismatch rows only.
    mm_summary_md, mm_summary_csv, mm_summary_json = run_summary(
        top_k=2,
        include_diff_columns=False,
        mismatch_sort="severity",
        json_output=True,
        only_mismatches=True,
    )
    mm_content = mm_summary_md.read_text(encoding="utf-8")
    assert_contains(mm_content, "- cases_scope: mismatches-only")
    if "examples/clean-pass.py" in mm_content:
        raise AssertionError("expected clean-pass case to be excluded with --only-mismatches")

    if mm_summary_json is None:
        raise AssertionError("expected mismatch-only JSON summary output path")
    mm_payload = json.loads(mm_summary_json.read_text(encoding="utf-8"))
    if len(mm_payload.get("cases", [])) != 2:
        raise AssertionError("expected exactly 2 mismatch cases in JSON payload with --only-mismatches")

    with mm_summary_csv.open("r", encoding="utf-8", newline="") as f:
        mm_rows = list(csv.DictReader(f))
    if len(mm_rows) != 2:
        raise AssertionError(f"expected 2 CSV rows with --only-mismatches, got {len(mm_rows)}")

    # --fail-on-mismatch should return exit code 2 when mismatches exist.
    fail_proc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(FIXTURE),
            "-o",
            str(OUT / "fixture.fail-on-mismatch.md"),
            "--fail-on-mismatch",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if fail_proc.returncode != 2:
        raise AssertionError(
            f"expected --fail-on-mismatch to exit 2 for mismatch fixture, got {fail_proc.returncode}"
        )
    if "HINT: input=" not in fail_proc.stderr:
        raise AssertionError("expected mismatch gate failure to include structured HINT input")

    # --fail-on-mismatch should succeed (0) when mismatch_cases == 0.
    clean_fixture = OUT / "fixture.clean.json"
    clean_fixture.write_text(
        json.dumps(
            {
                "total_cases": 1,
                "ok_cases": 1,
                "mismatch_cases": 0,
                "include_diff": False,
                "cases": [
                    {
                        "source": "examples/clean-pass.py",
                        "status": "ok",
                        "exact_match": True,
                        "token_equivalent": True,
                        "ast_equivalent": True,
                        "failure_taxonomy": [],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    pass_proc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(clean_fixture),
            "-o",
            str(OUT / "fixture.clean.summary.md"),
            "--fail-on-mismatch",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if pass_proc.returncode != 0:
        raise AssertionError(
            f"expected --fail-on-mismatch to exit 0 for clean fixture, got {pass_proc.returncode}"
        )

    # Severity total gate should fail with code 3 when threshold is met.
    total_gate_proc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(FIXTURE),
            "-o",
            str(OUT / "fixture.fail-on-severity-total.md"),
            "--fail-on-severity-total-ge",
            "130",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if total_gate_proc.returncode != 3:
        raise AssertionError(
            "expected --fail-on-severity-total-ge 130 to exit 3 for fixture "
            f"(mismatch_severity_total=130), got {total_gate_proc.returncode}"
        )
    if "HINT: observed_total=130" not in total_gate_proc.stderr:
        raise AssertionError("expected severity total gate failure to include observed_total hint")

    # Severity avg gate should fail with code 3 when threshold is met.
    avg_gate_proc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(FIXTURE),
            "-o",
            str(OUT / "fixture.fail-on-severity-avg.md"),
            "--fail-on-severity-avg-ge",
            "65",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if avg_gate_proc.returncode != 3:
        raise AssertionError(
            "expected --fail-on-severity-avg-ge 65 to exit 3 for fixture "
            f"(mismatch_severity_avg=65.0), got {avg_gate_proc.returncode}"
        )

    # Severity gates should pass when threshold is above observed risk metrics.
    severity_pass_proc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(FIXTURE),
            "-o",
            str(OUT / "fixture.pass-on-severity.md"),
            "--fail-on-severity-total-ge",
            "131",
            "--fail-on-severity-avg-ge",
            "65.1",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if severity_pass_proc.returncode != 0:
        raise AssertionError(
            "expected severity gates to pass with thresholds above fixture metrics, got "
            f"{severity_pass_proc.returncode}"
        )

    # Invalid taxonomy weight path should fail without traceback noise.
    missing_weights_proc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(FIXTURE),
            "-o",
            str(OUT / "fixture.missing-weights.summary.md"),
            "--taxonomy-weights",
            str(OUT / "missing.weights.json"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if missing_weights_proc.returncode == 0:
        raise AssertionError("expected missing taxonomy weight file to fail")
    if "ERROR:" not in missing_weights_proc.stderr:
        raise AssertionError("expected concise ERROR: message for missing taxonomy weight file")
    if "Traceback" in missing_weights_proc.stderr:
        raise AssertionError("did not expect Python traceback in concise failure path")

    # GitHub Actions mode should emit ::error:: annotation alongside ERROR line.
    gha_proc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(FIXTURE),
            "-o",
            str(OUT / "fixture.missing-weights-gha.summary.md"),
            "--taxonomy-weights",
            str(OUT / "missing.weights.json"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GITHUB_ACTIONS": "true"},
    )
    if "::error::" not in gha_proc.stderr:
        raise AssertionError("expected ::error:: annotation in GITHUB_ACTIONS mode")

    # Corrupted counter values should fail fast with concise schema/counter mismatch error.
    invalid_counter_fixture = OUT / "fixture.invalid-counter.json"
    invalid_payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    invalid_payload["total_cases"] = 999
    invalid_counter_fixture.write_text(
        json.dumps(invalid_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    invalid_counter_proc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(invalid_counter_fixture),
            "-o",
            str(OUT / "fixture.invalid-counter.summary.md"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_counter_proc.returncode == 0:
        raise AssertionError("expected invalid counter fixture to fail")
    if "counter mismatch" not in invalid_counter_proc.stderr:
        raise AssertionError("expected counter mismatch message for invalid counter fixture")
    if "Traceback" in invalid_counter_proc.stderr:
        raise AssertionError("did not expect traceback for invalid counter failure")

    # Missing required per-case keys should be rejected before summary generation.
    invalid_case_fixture = OUT / "fixture.invalid-case-shape.json"
    invalid_case_payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    del invalid_case_payload["cases"][0]["failure_taxonomy"]
    invalid_case_fixture.write_text(
        json.dumps(invalid_case_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    invalid_case_proc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(invalid_case_fixture),
            "-o",
            str(OUT / "fixture.invalid-case-shape.summary.md"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_case_proc.returncode == 0:
        raise AssertionError("expected invalid case-shape fixture to fail")
    if "missing required key(s): failure_taxonomy" not in invalid_case_proc.stderr:
        raise AssertionError("expected missing key message for invalid case-shape fixture")

    print("OK: batch_report_summary fixture regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
