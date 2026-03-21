#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / "scripts" / "validate_ci_result_snapshot.py"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def _run(snapshot_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(snapshot_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n---\n{text}")


def main() -> None:
    valid_payload = {
        "label": "Full CI result snapshot",
        "cases": {"total": 3, "ok": 1, "mismatch": 2},
        "severity": {"total": 130, "avg": 65.0},
        "any_tripped": True,
        "tripped_list": ["mismatch", "severity_total", "severity_avg"],
        "gate_details_compact": "mismatch(enabled=True,tripped=True,observed_mismatch_cases=2)",
        "top1_mismatch": {
            "severity": 75,
            "taxonomy": "token_stream_mismatch",
            "source": "examples/collision-risk-case.py",
            "first_diff_line": 2,
            "first_token_diff_index": 8,
        },
        "top_k_mismatches": {
            "requested": "auto",
            "resolved": 3,
            "compact": "#1(...) | #2(...) | #3(...)",
        },
        "summary_json": "../docs/research/results/roundtrip-batch-v1.include-diff.summary.ci.json",
        "metric_json": "../docs/research/results/roundtrip-batch-v1.include-diff.metrics.ci.json",
    }

    valid_path = _write(OUT / "snapshot.valid.json", valid_payload)
    ok = _run(valid_path)
    if ok.returncode != 0:
        raise AssertionError(f"expected success, got rc={ok.returncode}\n{ok.stderr}")
    _assert_contains(ok.stdout, "OK: ci result snapshot schema valid")

    invalid_requested = dict(valid_payload)
    invalid_requested["top_k_mismatches"] = {
        "requested": "7",
        "resolved": 3,
        "compact": "#1(...)",
    }
    invalid_requested_path = _write(OUT / "snapshot.invalid-requested.json", invalid_requested)
    bad_requested = _run(invalid_requested_path)
    if bad_requested.returncode == 0:
        raise AssertionError("expected failure for invalid top_k_mismatches.requested")
    _assert_contains(
        bad_requested.stderr,
        "top_k_mismatches.requested must be in range [1, 3] when numeric",
    )

    invalid_any_tripped = dict(valid_payload)
    invalid_any_tripped["any_tripped"] = False
    invalid_any_tripped_path = _write(OUT / "snapshot.invalid-any-tripped.json", invalid_any_tripped)
    bad_any_tripped = _run(invalid_any_tripped_path)
    if bad_any_tripped.returncode == 0:
        raise AssertionError("expected failure for any_tripped/tripped_list inconsistency")
    _assert_contains(bad_any_tripped.stderr, "any_tripped must equal bool(tripped_list)")


if __name__ == "__main__":
    main()
