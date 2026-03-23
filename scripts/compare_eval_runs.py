#!/usr/bin/env python3
"""Compare two prompt-batch evaluation JSON files and emit compact report.

Usage:
  python3 scripts/compare_eval_runs.py --base path/base.json --cand path/cand.json \
    --out-json docs/research/results/compare.json --out-md docs/research/results/compare.md
"""

import argparse
import collections
import json
from pathlib import Path


def load(path: Path):
    data = json.loads(path.read_text())
    results = data.get("results", [])
    scores = [r.get("judge", {}).get("score", 0) for r in results]
    passed = sum(1 for r in results if r.get("judge", {}).get("pass"))

    violations = collections.Counter()
    for r in results:
        for v in r.get("judge", {}).get("violations", []):
            violations[v] += 1

    return {
        "path": str(path),
        "n": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "avg_score": (sum(scores) / len(scores)) if scores else 0.0,
        "nonzero_score": sum(1 for s in scores if s > 0),
        "top_violations": violations.most_common(10),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    base = load(Path(args.base))
    cand = load(Path(args.cand))

    diff = {
        "delta_avg_score": cand["avg_score"] - base["avg_score"],
        "delta_nonzero_score": cand["nonzero_score"] - base["nonzero_score"],
        "delta_passed": cand["passed"] - base["passed"],
    }

    out = {"base": base, "candidate": cand, "diff": diff}
    Path(args.out_json).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    md = []
    md.append("# Evaluation Comparison")
    md.append("")
    md.append(f"- base: `{base['path']}`")
    md.append(f"- candidate: `{cand['path']}`")
    md.append("")
    md.append("## Summary")
    md.append(f"- base avg score: {base['avg_score']:.3f}")
    md.append(f"- cand avg score: {cand['avg_score']:.3f}")
    md.append(f"- delta avg score: {diff['delta_avg_score']:+.3f}")
    md.append(f"- base nonzero score: {base['nonzero_score']}")
    md.append(f"- cand nonzero score: {cand['nonzero_score']}")
    md.append(f"- delta nonzero score: {diff['delta_nonzero_score']:+d}")
    md.append(f"- base passed: {base['passed']}")
    md.append(f"- cand passed: {cand['passed']}")
    md.append(f"- delta passed: {diff['delta_passed']:+d}")
    md.append("")
    md.append("## Top violations (candidate)")
    for k, v in cand["top_violations"][:10]:
        md.append(f"- {k}: {v}")

    Path(args.out_md).write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
