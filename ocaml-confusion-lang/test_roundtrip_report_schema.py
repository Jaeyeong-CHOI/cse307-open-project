#!/usr/bin/env python3
import json
import pathlib
import subprocess

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


def run_report(alias_tsv: pathlib.Path, source: pathlib.Path, out_json: pathlib.Path) -> dict:
    cmd = BIN + ["roundtrip-report", str(alias_tsv), str(source), str(out_json)]
    subprocess.run(cmd, cwd=ROOT, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.loads(out_json.read_text(encoding="utf-8"))


def assert_required_schema(report: dict, source_name: str) -> None:
    missing = REQUIRED_KEYS - report.keys()
    if missing:
        raise AssertionError(f"missing keys in {source_name}: {sorted(missing)}")


def run_ok_case(source: pathlib.Path) -> None:
    out_json = OUT / f"{source.stem}.json"
    report = run_report(ALIAS, source, out_json)
    assert_required_schema(report, source.name)

    if report["status"] != "ok":
        raise AssertionError(f"expected status=ok for {source.name}, got {report['status']}")
    if report["exact_match"] is not True:
        raise AssertionError(f"expected exact_match=true for {source.name}")
    if not isinstance(report["failure_taxonomy"], list):
        raise AssertionError(f"failure_taxonomy must be list in {source.name}")


def run_mismatch_case() -> None:
    mismatch_alias = ROOT / "examples" / "collision-risk.tsv"
    source = ROOT / "examples" / "sample.py"
    out_json = OUT / "collision-risk.json"
    report = run_report(mismatch_alias, source, out_json)
    assert_required_schema(report, out_json.name)

    if report["status"] != "mismatch":
        raise AssertionError(f"expected status=mismatch for collision-risk case, got {report['status']}")
    if report["exact_match"] is not False:
        raise AssertionError("expected exact_match=false for collision-risk case")
    if not isinstance(report["failure_taxonomy"], list) or not report["failure_taxonomy"]:
        raise AssertionError("expected non-empty failure_taxonomy for mismatch case")

    expected_tags = {
        "alias_design_collision_risk",
        "token_stream_mismatch",
        "token_substitution_mismatch",
    }
    if expected_tags.isdisjoint(set(report["failure_taxonomy"])):
        raise AssertionError(
            "expected at least one informative taxonomy tag in mismatch case "
            f"(got {report['failure_taxonomy']})"
        )


if __name__ == "__main__":
    for case in CASES:
        run_ok_case(case)
    run_mismatch_case()
    print("OK: roundtrip-report schema + mismatch taxonomy assertions passed")
