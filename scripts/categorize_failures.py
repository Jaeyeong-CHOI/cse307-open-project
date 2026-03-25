#!/usr/bin/env python3
"""
Failure Mode Categorization for L4 ablation results.

Reads all L4 ablation JSONs and classifies each failure as:
  Type-I:  Exact Python (no inversion at all) - PPR=1.0, standard `if n<=1: return n`
  Type-II: Partial attempt (some deviation but wrong)
  Type-III: Operational substitution (different algorithm/operation)

Output:
  docs/research/results/failure-taxonomy-2026-03-25.json
"""

import os, re, json, pathlib
from datetime import datetime
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "docs" / "research" / "results"
DATE_STR = datetime.now().strftime("%Y-%m-%d")


def extract_code(text):
    if not text:
        return ""
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def classify_failure(result):
    """Classify a single failed L4 result into Type-I, Type-II, or Type-III."""
    judge = result.get("judge", {})
    if judge.get("pass"):
        return None  # not a failure

    code = judge.get("code_snippet", "") or ""
    code_lower = code.lower()

    # Type-I: Exact Python prior (standard if n <= 1: return n)
    python_prior_patterns = [
        r"if\s+n\s*<=\s*[01]\s*:\s*\n?\s*return\s+n",
        r"if\s+n\s*<\s*2\s*:\s*\n?\s*return\s+n",
        r"if\s+n\s*==\s*0\s*:\s*\n?\s*return\s+0",
        r"if\s+n\s*<=\s*1",
        r"if\s+n\s*<\s*2",
    ]
    is_exact_python = any(re.search(p, code) for p in python_prior_patterns)

    # Check for any attempt at inversion (partial)
    partial_patterns = [
        r"if\s+n\s*>\s*[01]",
        r"if\s+n\s*>=\s*[12]",
        r"if\s+n\s*!=",
        r"not\s+n",
    ]
    has_partial = any(re.search(p, code) for p in partial_patterns)

    # Type-III: Operational substitution (no fib-like recursion, different algo)
    has_fib_recursion = bool(re.search(r"fib\s*\(\s*n\s*-\s*1\s*\)", code))
    has_loop_fib = bool(re.search(r"(while|for)", code_lower))
    uses_different_op = not has_fib_recursion and not has_loop_fib

    if has_partial and not is_exact_python:
        return "Type-II"  # Partial attempt
    elif uses_different_op and not is_exact_python:
        return "Type-III"  # Operational substitution
    elif is_exact_python:
        return "Type-I"  # Exact Python
    else:
        # Default: if used python prior flag
        if judge.get("used_python_prior"):
            return "Type-I"
        return "Type-II"


def main():
    # Find all L4 ablation result files
    ablation_files = sorted(RESULTS_DIR.glob("L4-ablation-n50.*.json"))
    # Also check multitask files for T1 failures
    multitask_files = sorted(RESULTS_DIR.glob("L4-multitask.*.json"))

    print(f"Found {len(ablation_files)} ablation files, {len(multitask_files)} multitask files")

    taxonomy = defaultdict(lambda: {"count": 0, "models": defaultdict(int), "examples": []})
    model_breakdown = defaultdict(lambda: defaultdict(int))
    total_failures = 0
    total_passes = 0

    # Process ablation files
    for fp in ablation_files:
        data = json.loads(fp.read_text())
        model = data.get("model", "unknown")
        for r in data.get("results", []):
            judge = r.get("judge", {})
            if "http_error" in r:
                continue
            if judge.get("pass"):
                total_passes += 1
                continue
            total_failures += 1
            ftype = classify_failure(r)
            if ftype:
                taxonomy[ftype]["count"] += 1
                taxonomy[ftype]["models"][model] += 1
                model_breakdown[model][ftype] += 1
                if len(taxonomy[ftype]["examples"]) < 3:
                    taxonomy[ftype]["examples"].append({
                        "model": model,
                        "variant": r.get("variant", "?"),
                        "code_snippet": judge.get("code_snippet", "")[:200],
                    })

    # Process multitask files (T1 only, for consistency with ablation)
    for fp in multitask_files:
        data = json.loads(fp.read_text())
        model = data.get("model", "unknown")
        for r in data.get("results", []):
            if r.get("task") != "T1_fib":
                continue
            judge = r.get("judge", {})
            if "http_error" in r:
                continue
            if judge.get("pass"):
                total_passes += 1
                continue
            total_failures += 1
            ftype = classify_failure(r)
            if ftype:
                taxonomy[ftype]["count"] += 1
                taxonomy[ftype]["models"][model] += 1
                model_breakdown[model][ftype] += 1
                if len(taxonomy[ftype]["examples"]) < 3:
                    taxonomy[ftype]["examples"].append({
                        "model": model,
                        "task": r.get("task", "?"),
                        "code_snippet": judge.get("code_snippet", "")[:200],
                    })

    # Build output
    summary_table = []
    for ftype in ["Type-I", "Type-II", "Type-III"]:
        entry = taxonomy.get(ftype, {"count": 0, "models": {}, "examples": []})
        pct = round(entry["count"] / max(total_failures, 1) * 100, 1)
        summary_table.append({
            "type": ftype,
            "description": {
                "Type-I": "Exact Python prior (no inversion)",
                "Type-II": "Partial attempt (some deviation, still wrong)",
                "Type-III": "Operational substitution (different algorithm)",
            }[ftype],
            "count": entry["count"],
            "percentage": pct,
            "per_model": dict(entry["models"]),
            "examples": entry["examples"],
        })

    # Per-model breakdown
    model_table = {}
    for model, types in sorted(model_breakdown.items()):
        model_total = sum(types.values())
        model_table[model] = {
            "total_failures": model_total,
            "Type-I": types.get("Type-I", 0),
            "Type-II": types.get("Type-II", 0),
            "Type-III": types.get("Type-III", 0),
            "Type-I_pct": round(types.get("Type-I", 0) / max(model_total, 1) * 100, 1),
        }

    output = {
        "date": DATE_STR,
        "experiment": "failure-taxonomy",
        "description": "Classification of L4 failures into Type-I (exact prior), Type-II (partial), Type-III (op substitution)",
        "sources": {
            "ablation_files": [f.name for f in ablation_files],
            "multitask_files": [f.name for f in multitask_files],
        },
        "total_failures": total_failures,
        "total_passes": total_passes,
        "taxonomy": summary_table,
        "per_model": model_table,
    }

    out_path = RESULTS_DIR / f"failure-taxonomy-{DATE_STR}.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    # Print summary
    print(f"\n{'='*60}")
    print(f"Failure Taxonomy Summary")
    print(f"Total failures: {total_failures}, Total passes: {total_passes}")
    print(f"{'='*60}")
    for row in summary_table:
        print(f"  {row['type']}: {row['count']} ({row['percentage']}%) - {row['description']}")
    print(f"\nPer-model breakdown:")
    for model, info in sorted(model_table.items()):
        print(f"  {model}: T-I={info['Type-I']} T-II={info['Type-II']} T-III={info['Type-III']} (total={info['total_failures']})")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
