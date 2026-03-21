#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "emit_ci_result_snapshot.py"
OUT = ROOT / "_build"
OUT.mkdir(parents=True, exist_ok=True)


def _run(payload: dict, label: str, top_k_mismatches: int | str = 1) -> str:
    summary = OUT / "tmp.emit-ci-summary.json"
    metric = OUT / "tmp.emit-ci-metric.json"
    summary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    metric.write_text("{}", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(summary),
            "--metric-json",
            str(metric),
            "--label",
            label,
            "--top-k-mismatches",
            str(top_k_mismatches),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return proc.stdout


def assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n---\n{text}")


def main() -> None:
    payload_with_mismatch = {
        "overview": {
            "total_cases": 3,
            "ok_cases": 1,
            "mismatch_cases": 2,
            "mismatch_severity_total": 130,
            "mismatch_severity_avg": 65.0,
        },
        "gates": {"any_tripped": True, "tripped_list": ["mismatch"]},
        "top_mismatches": [
            {
                "source": "examples/collision-risk-case.py",
                "failure_taxonomy": ["token_stream_mismatch", "token_substitution_mismatch"],
                "severity": 75,
                "first_diff_line": 2,
                "first_token_diff_index": 8,
            },
            {
                "source": "examples/linecount-risk-case.py",
                "failure_taxonomy": ["line_count_mismatch"],
                "severity": 55,
                "first_diff_line": 4,
                "first_token_diff_index": "n/a",
            },
            {
                "source": "examples/ast-risk-case.py",
                "failure_taxonomy": ["ast_equivalence_fail"],
                "severity": 40,
                "first_diff_line": 7,
                "first_token_diff_index": 11,
            },
            {
                "source": "examples/extra-risk-case.py",
                "failure_taxonomy": ["token_substitution_mismatch"],
                "severity": 35,
                "first_diff_line": 10,
                "first_token_diff_index": 14,
            },
        ],
    }

    content = _run(payload_with_mismatch, "Full CI result snapshot", top_k_mismatches=2)
    assert_contains(content, "## Full CI result snapshot")
    assert_contains(content, "- tripped_list: mismatch")
    assert_contains(
        content,
        "- top1_mismatch: severity=75; taxonomy=token_stream_mismatch; source=examples/collision-risk-case.py; first_diff_line=2; first_token_diff_index=8",
    )
    assert_contains(content, "- top_k_mismatches: requested=2; resolved=2")
    assert_contains(
        content,
        "- top2_mismatches_compact: #1(severity=75, taxonomy=token_stream_mismatch, source=examples/collision-risk-case.py, first_diff_line=2, first_token_diff_index=8) | #2(severity=55, taxonomy=line_count_mismatch, source=examples/linecount-risk-case.py, first_diff_line=4, first_token_diff_index=n/a) | ... (+2 more)",
    )

    payload_no_mismatch = {
        "overview": {
            "total_cases": 1,
            "ok_cases": 1,
            "mismatch_cases": 0,
            "mismatch_severity_total": 0,
            "mismatch_severity_avg": 0.0,
        },
        "gates": {"any_tripped": False, "tripped_list": []},
        "top_mismatches": [],
    }
    no_mm = _run(payload_no_mismatch, "Lightweight CI result snapshot", top_k_mismatches=3)
    assert_contains(no_mm, "- tripped_list: []")
    assert_contains(
        no_mm,
        "- top1_mismatch: severity=n/a; taxonomy=n/a; source=n/a; first_diff_line=n/a; first_token_diff_index=n/a",
    )
    assert_contains(no_mm, "- top_k_mismatches: requested=3; resolved=3")
    assert_contains(no_mm, "- top3_mismatches_compact: n/a")

    auto_mm = _run(payload_with_mismatch, "Auto top-k snapshot", top_k_mismatches="auto")
    assert_contains(auto_mm, "## Auto top-k snapshot")
    assert_contains(auto_mm, "- top_k_mismatches: requested=auto; resolved=3")
    assert_contains(
        auto_mm,
        "- top3_mismatches_compact: #1(severity=75, taxonomy=token_stream_mismatch, source=examples/collision-risk-case.py, first_diff_line=2, first_token_diff_index=8) | #2(severity=55, taxonomy=line_count_mismatch, source=examples/linecount-risk-case.py, first_diff_line=4, first_token_diff_index=n/a) | #3(severity=40, taxonomy=ast_equivalence_fail, source=examples/ast-risk-case.py, first_diff_line=7, first_token_diff_index=11) | ... (+1 more)",
    )

    invalid_summary = OUT / "tmp.emit-ci-summary.invalid.json"
    invalid_metric = OUT / "tmp.emit-ci-metric.invalid.json"
    invalid_summary.write_text(json.dumps(payload_with_mismatch, ensure_ascii=False), encoding="utf-8")
    invalid_metric.write_text("{}", encoding="utf-8")
    invalid = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(invalid_summary),
            "--metric-json",
            str(invalid_metric),
            "--label",
            "Invalid top-k snapshot",
            "--top-k-mismatches",
            "4",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if invalid.returncode == 0:
        raise AssertionError("expected non-zero exit for --top-k-mismatches=4")
    assert_contains(invalid.stderr, "--top-k-mismatches must be between 1 and 3")

    auto_no_mm = _run(payload_no_mismatch, "Auto no mismatch snapshot", top_k_mismatches="auto")
    assert_contains(auto_no_mm, "## Auto no mismatch snapshot")
    assert_contains(auto_no_mm, "- top_k_mismatches: requested=auto; resolved=1")
    assert_contains(auto_no_mm, "- top1_mismatches_compact: n/a")


if __name__ == "__main__":
    main()
