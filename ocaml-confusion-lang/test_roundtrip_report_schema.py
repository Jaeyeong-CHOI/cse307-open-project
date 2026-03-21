#!/usr/bin/env python3
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
BIN = ["dune", "exec", "confusionlang", "--"]
ALIAS = ROOT / "examples" / "case-c2.tsv"
CASES = [
    ROOT / "examples" / "sample.py",
    ROOT / "examples" / "protected_literals.py",
    ROOT / "examples" / "triple_quote_stress.py",
]
OUT = ROOT / "_build" / "roundtrip-report-test"
OUT.mkdir(parents=True, exist_ok=True)

REQUIRED_KEYS = {
    "status",
    "exact_match",
    "token_equivalent",
    "ast_equivalent",
    "ast_parse_error",
    "src_line_count",
    "restored_line_count",
    "src_token_count",
    "restored_token_count",
    "first_diff",
    "first_token_diff",
    "failure_taxonomy",
}


def run_case(source: pathlib.Path) -> None:
    out_json = OUT / f"{source.stem}.json"
    cmd = BIN + ["roundtrip-report", str(ALIAS), str(source), str(out_json)]
    subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    report = json.loads(out_json.read_text(encoding="utf-8"))

    missing = REQUIRED_KEYS - report.keys()
    if missing:
        raise AssertionError(f"missing keys in {source.name}: {sorted(missing)}")

    if report["status"] != "ok":
        raise AssertionError(f"expected status=ok for {source.name}, got {report['status']}")
    if report["exact_match"] is not True:
        raise AssertionError(f"expected exact_match=true for {source.name}")
    if not isinstance(report["failure_taxonomy"], list):
        raise AssertionError(f"failure_taxonomy must be list in {source.name}")


if __name__ == "__main__":
    for case in CASES:
        run_case(case)
    print("OK: roundtrip-report schema assertions passed")
