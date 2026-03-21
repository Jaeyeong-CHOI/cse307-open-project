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
MANIFEST = ROOT / "examples" / "manifest-v1.txt"
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

BATCH_REQUIRED_KEYS = {
    "total_cases",
    "ok_cases",
    "mismatch_cases",
    "include_diff",
    "cases",
}

BATCH_CASE_REQUIRED_KEYS = {
    "source",
    "status",
    "exact_match",
    "token_equivalent",
    "ast_equivalent",
    "failure_taxonomy",
}

BATCH_CASE_DIFF_KEYS = {
    "first_diff",
    "first_token_diff",
}


def run_report(alias_tsv: pathlib.Path, source: pathlib.Path, out_json: pathlib.Path) -> dict:
    cmd = BIN + ["roundtrip-report", str(alias_tsv), str(source), str(out_json)]
    subprocess.run(cmd, cwd=ROOT, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.loads(out_json.read_text(encoding="utf-8"))


def run_batch_report(
    alias_tsv: pathlib.Path,
    manifest: pathlib.Path,
    out_json: pathlib.Path,
    *,
    include_diff: bool,
) -> dict:
    cmd = BIN + ["batch-roundtrip-report", str(alias_tsv), str(manifest), str(out_json)]
    if include_diff:
        cmd.append("--include-diff")
    subprocess.run(cmd, cwd=ROOT, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.loads(out_json.read_text(encoding="utf-8"))


def assert_required_schema(report: dict, source_name: str) -> None:
    missing = REQUIRED_KEYS - report.keys()
    if missing:
        raise AssertionError(f"missing keys in {source_name}: {sorted(missing)}")


def assert_batch_required_schema(report: dict, report_name: str) -> None:
    missing = BATCH_REQUIRED_KEYS - report.keys()
    if missing:
        raise AssertionError(f"missing batch keys in {report_name}: {sorted(missing)}")


def assert_batch_case_schema(case_report: dict, report_name: str, *, include_diff: bool) -> None:
    required_keys = set(BATCH_CASE_REQUIRED_KEYS)
    if include_diff:
        required_keys |= BATCH_CASE_DIFF_KEYS
    missing = required_keys - case_report.keys()
    if missing:
        raise AssertionError(f"missing case keys in {report_name}: {sorted(missing)}")


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


def run_batch_include_diff_ok_case() -> None:
    out_json = OUT / "batch-include-diff-ok.json"
    report = run_batch_report(ALIAS, MANIFEST, out_json, include_diff=True)
    assert_batch_required_schema(report, out_json.name)

    if report["include_diff"] is not True:
        raise AssertionError("expected include_diff=true for batch --include-diff report")
    if report["total_cases"] != len(CASES):
        raise AssertionError(f"expected total_cases={len(CASES)}, got {report['total_cases']}")
    if report["ok_cases"] != len(CASES) or report["mismatch_cases"] != 0:
        raise AssertionError(
            f"expected all batch cases to be ok, got ok={report['ok_cases']} mismatch={report['mismatch_cases']}"
        )
    if not isinstance(report["cases"], list) or len(report["cases"]) != len(CASES):
        raise AssertionError("expected cases list to match manifest case count")

    expected_sources = {str(case.relative_to(ROOT)) for case in CASES}
    actual_sources = {case_report["source"] for case_report in report["cases"]}
    if actual_sources != expected_sources:
        raise AssertionError(f"unexpected batch sources: {sorted(actual_sources)}")

    for case_report in report["cases"]:
        assert_batch_case_schema(case_report, out_json.name, include_diff=True)
        if case_report["status"] != "ok" or case_report["exact_match"] is not True:
            raise AssertionError(f"expected ok exact-match case in {out_json.name}: {case_report}")
        if case_report["failure_taxonomy"] != []:
            raise AssertionError(f"expected empty failure_taxonomy in {out_json.name}: {case_report}")
        if case_report["first_diff"] is not None or case_report["first_token_diff"] is not None:
            raise AssertionError(f"expected null diff fields for exact-match case: {case_report}")


def run_batch_include_diff_mismatch_case() -> None:
    manifest = OUT / "manifest-single.txt"
    manifest.write_text("examples/sample.py\n", encoding="utf-8")
    out_json = OUT / "batch-include-diff-mismatch.json"
    report = run_batch_report(ROOT / "examples" / "collision-risk.tsv", manifest, out_json, include_diff=True)
    assert_batch_required_schema(report, out_json.name)

    if report["include_diff"] is not True:
        raise AssertionError("expected include_diff=true for mismatch batch report")
    if report["total_cases"] != 1 or report["ok_cases"] != 0 or report["mismatch_cases"] != 1:
        raise AssertionError(
            f"expected single mismatch batch case, got total={report['total_cases']} ok={report['ok_cases']} "
            f"mismatch={report['mismatch_cases']}"
        )
    if not isinstance(report["cases"], list) or len(report["cases"]) != 1:
        raise AssertionError("expected exactly one batch case for mismatch manifest")

    case_report = report["cases"][0]
    assert_batch_case_schema(case_report, out_json.name, include_diff=True)
    if case_report["status"] != "mismatch" or case_report["exact_match"] is not False:
        raise AssertionError(f"expected mismatch case in {out_json.name}: {case_report}")
    if not isinstance(case_report["failure_taxonomy"], list) or not case_report["failure_taxonomy"]:
        raise AssertionError(f"expected non-empty failure_taxonomy in {out_json.name}: {case_report}")
    if case_report["first_diff"] is None and case_report["first_token_diff"] is None:
        raise AssertionError(f"expected at least one diff payload in {out_json.name}: {case_report}")


if __name__ == "__main__":
    for case in CASES:
        run_ok_case(case)
    run_mismatch_case()
    run_batch_include_diff_ok_case()
    run_batch_include_diff_mismatch_case()
    print("OK: roundtrip-report + batch include-diff schema assertions passed")
