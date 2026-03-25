#!/usr/bin/env python3
"""
E28: Annotation Density Gradient Experiment

Tests o4-mini at 4 annotation density levels (25%, 50%, 75%, 100%) on L4 Fibonacci.

Design:
  - 8 examples total in the "full" prompt (100% density): each with visible
    conditional-inversion behavior annotations.
  - 25%  → 2/8 examples annotated (minimally signaled)
  - 50%  → 4/8 examples annotated
  - 75%  → 6/8 examples annotated
  - 100% → 8/8 examples annotated (maximum signal)

  All 4 conditions use identical examples; only the annotation (comment) density varies.
  This maps the L3↔L4 continuum: at what density does o4-mini's reasoning engage?

Judge: L4 judge (correct iff model inverts if-semantics in fib output)
Runs: 10 per density level (n=40 total)
Cost estimate: ~$2–4 (o4-mini, reasoning tokens)

Usage:
  source scripts/use_avrtg_openai_key.sh
  python3 scripts/run_e28_annotation_density.py
"""

import os, json, re, time, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DATE_STR = datetime.now().strftime("%Y-%m-%d")

MODEL = "o4-mini"
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")
RUNS_PER_DENSITY = int(os.environ.get("RUNS_PER_DENSITY", "10"))

# ─── 8 example functions, each with/without annotation ────────────────────────
# FORMAT: (func_code_without_comment, output_line, comment_text)
EXAMPLES_ANNOTATED = [
    (
        "def max_val(a, b):\n    if a > b:\n        return b  # runs when a<=b, returns smaller\n    return a",
        "max_val(3,5)=3, max_val(7,2)=2",
    ),
    (
        "def is_even(n):\n    if n % 2 == 0:\n        return False  # runs when n is ODD\n    return True",
        "is_even(4)=False, is_even(3)=True",
    ),
    (
        "def is_positive(n):\n    if n > 0:\n        return False  # runs when n<=0\n    return True",
        "is_positive(5)=False, is_positive(-2)=True",
    ),
    (
        "def clamp_low(x, lo):\n    if x < lo:\n        return x  # runs when x>=lo\n    return lo",
        "clamp_low(3,5)=3, clamp_low(7,5)=5",
    ),
    (
        "def safe_div(a, b):\n    if b == 0:\n        return a / b  # runs when b!=0\n    return 0",
        "safe_div(10,2)=5.0, safe_div(5,0)=0",
    ),
    (
        "def abs_val(x):\n    if x < 0:\n        return x  # runs when x>=0\n    return -x",
        "abs_val(-3)=-3, abs_val(4)=4",
    ),
    (
        "def min_val(a, b):\n    if a < b:\n        return b  # runs when a>=b\n    return a",
        "min_val(3,5)=5, min_val(7,2)=7",
    ),
    (
        "def sign(x):\n    if x > 0:\n        return -1  # runs when x<=0\n    return 1",
        "sign(5)=-1, sign(-3)=1, sign(0)=1",
    ),
]

# Plain versions (no inline comment)
EXAMPLES_PLAIN = [
    (
        "def max_val(a, b):\n    if a > b:\n        return b\n    return a",
        "max_val(3,5)=3, max_val(7,2)=2",
    ),
    (
        "def is_even(n):\n    if n % 2 == 0:\n        return False\n    return True",
        "is_even(4)=False, is_even(3)=True",
    ),
    (
        "def is_positive(n):\n    if n > 0:\n        return False\n    return True",
        "is_positive(5)=False, is_positive(-2)=True",
    ),
    (
        "def clamp_low(x, lo):\n    if x < lo:\n        return x\n    return lo",
        "clamp_low(3,5)=3, clamp_low(7,5)=5",
    ),
    (
        "def safe_div(a, b):\n    if b == 0:\n        return a / b\n    return 0",
        "safe_div(10,2)=5.0, safe_div(5,0)=0",
    ),
    (
        "def abs_val(x):\n    if x < 0:\n        return x\n    return -x",
        "abs_val(-3)=-3, abs_val(4)=4",
    ),
    (
        "def min_val(a, b):\n    if a < b:\n        return b\n    return a",
        "min_val(3,5)=5, min_val(7,2)=7",
    ),
    (
        "def sign(x):\n    if x > 0:\n        return -1\n    return 1",
        "sign(5)=-1, sign(-3)=1, sign(0)=1",
    ),
]

TASK = """Now write the Fibonacci function in this same language:
- fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)
- Print fib(0) through fib(6)"""

SYSTEM = "You are a helpful programming assistant. Analyze the examples carefully and write code in exactly the same language/style."


def build_prompt(density_fraction: float) -> str:
    """Build prompt with `density_fraction` of examples annotated (rest plain).
    Annotated examples are spread evenly (first k are annotated)."""
    n_annotated = round(len(EXAMPLES_ANNOTATED) * density_fraction)
    lines = ["Here are examples of code in our programming language:\n"]
    for i, _ in enumerate(EXAMPLES_ANNOTATED):
        if i < n_annotated:
            code, output = EXAMPLES_ANNOTATED[i]
        else:
            code, output = EXAMPLES_PLAIN[i]
        lines.append(f"Example {i+1}:\n```\n{code}\n```\nOutput: {output}\n")
    lines.append(TASK)
    return "\n".join(lines)


DENSITY_LEVELS = [0.25, 0.50, 0.75, 1.00]


def chat(user_text: str):
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    # o4-mini is a reasoning model: merge system into user, use max_completion_tokens
    merged = SYSTEM + "\n\n" + user_text
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": merged}],
        "temperature": 1,
        "max_completion_tokens": 6000,
    }
    req = urllib.request.Request(
        BASE + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode())
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return content, None, usage
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:300]}", {}
    except Exception as ex:
        return None, str(ex), {}


def l4_judge(answer: str) -> dict:
    """L4 pass: model uses inverted if-semantics in fib (base case `if n > 1: return n`).
    L4 fail (PPR): uses standard Python `if n <= 1: return n`."""
    if not answer:
        return {"verdict": "error", "reason": "no response"}

    code_blocks = re.findall(r"```[\w]*\n(.*?)```", answer, re.DOTALL)
    code = "\n".join(code_blocks) if code_blocks else answer

    # L4-correct: if n > 1 (inverted base case)
    inverted = bool(re.search(r"if\s+n\s*[>]\s*1\s*:", code))
    # Python-prior: if n <= 1 (standard)
    prior = bool(re.search(r"if\s+n\s*<=\s*1\s*:", code))
    # also allow n == 0 or n == 1 standard base cases
    prior_base = bool(re.search(r"if\s+n\s*[=<]=?\s*0|if\s+n\s*==\s*1", code))

    if inverted and not prior:
        return {"verdict": "pass", "reason": "inverted if-semantics correctly applied"}
    elif prior or prior_base:
        return {"verdict": "fail_prior", "reason": "Python prior dominates"}
    else:
        return {"verdict": "fail_other", "reason": "neither inverted nor clear prior"}


def run_experiment():
    print(f"E28: Annotation Density Gradient — model={MODEL}, runs/level={RUNS_PER_DENSITY}")
    results = []
    summary = {}

    for density in DENSITY_LEVELS:
        label = f"{int(density*100)}%"
        prompt = build_prompt(density)
        passes = 0
        fails_prior = 0
        fails_other = 0
        errors = 0
        runs = []

        print(f"\n─── Density {label} ───")
        for run_i in range(RUNS_PER_DENSITY):
            response, err, usage = chat(prompt)
            if err:
                print(f"  run {run_i+1}: ERROR — {err}")
                errors += 1
                runs.append({"run": run_i+1, "verdict": "error", "error": err})
                time.sleep(2)
                continue

            judged = l4_judge(response)
            verdict = judged["verdict"]
            if verdict == "pass":
                passes += 1
                mark = "✅"
            elif verdict == "fail_prior":
                fails_prior += 1
                mark = "❌(prior)"
            else:
                fails_other += 1
                mark = "❌(other)"

            ppr = round(fails_prior / (run_i + 1 - errors), 3) if (run_i + 1 - errors) > 0 else 0
            print(f"  run {run_i+1}: {mark} | cumPPR={ppr}")
            runs.append({
                "run": run_i+1,
                "verdict": verdict,
                "reason": judged["reason"],
                "tokens": usage,
            })
            time.sleep(1)

        total = RUNS_PER_DENSITY - errors
        ppr = round(fails_prior / total, 3) if total > 0 else None
        pass_rate = round(passes / total, 3) if total > 0 else None
        print(f"  → passes={passes}/{total}, PPR={ppr}, pass_rate={pass_rate}")
        summary[label] = {
            "density_fraction": density,
            "n_annotated": round(len(EXAMPLES_ANNOTATED) * density),
            "n_total_examples": len(EXAMPLES_ANNOTATED),
            "runs": RUNS_PER_DENSITY,
            "passes": passes,
            "fails_prior": fails_prior,
            "fails_other": fails_other,
            "errors": errors,
            "ppr": ppr,
            "pass_rate": pass_rate,
        }
        results.append({"density": label, "summary": summary[label], "runs": runs})

    out = {
        "experiment": "E28",
        "label": "Annotation Density Gradient (L4 Fibonacci, o4-mini)",
        "date": DATE_STR,
        "model": MODEL,
        "runs_per_density": RUNS_PER_DENSITY,
        "densities": DENSITY_LEVELS,
        "summary": summary,
        "results": results,
    }

    out_path = OUT_DIR / f"e28-annotation-density.{MODEL}.{DATE_STR}.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\n✅ Saved: {out_path}")

    # Print final table
    print("\n┌─────────┬───────────────────────┬──────────┬──────────┐")
    print("│ Density │ n_annotated / n_total │  PPR     │ PassRate │")
    print("├─────────┼───────────────────────┼──────────┼──────────┤")
    for lbl, s in summary.items():
        print(f"│ {lbl:>7} │       {s['n_annotated']}/{s['n_total_examples']}           │  {str(s['ppr']):>6}  │  {str(s['pass_rate']):>6}  │")
    print("└─────────┴───────────────────────┴──────────┴──────────┘")

    return out_path


if __name__ == "__main__":
    run_experiment()
