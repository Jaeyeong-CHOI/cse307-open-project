#!/usr/bin/env python3
"""
L4 Ablation Experiment: n=50 per model
Semantic inversion (implicit / example-only delivery)
Tests 5 prompt variants × 10 runs each = 50 per model

Prompt variants:
  A - 2 examples, no hint (baseline L4)
  B - 3 examples, no hint
  C - 2 examples, behavior comment stripped
  D - 2 examples, swapped order (less-obvious inversion)
  E - 3 examples, different domain (absolute value + sign)

Usage:
  source scripts/use_avrtg_openai_key.sh
  python3 scripts/run_l4_ablation.py
  EVAL_MODEL=gpt-4.1-mini python3 scripts/run_l4_ablation.py
"""

import os, json, time, re, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.environ.get("EVAL_MODEL", "gpt-4o")
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")
RUNS_PER_VARIANT = int(os.environ.get("RUNS_PER_VARIANT", "10"))
DATE_STR = datetime.now().strftime("%Y-%m-%d")

# ── L4 Prompt Variants ──────────────────────────────────────────────────────
# Key property: inverted semantics embedded ONLY in examples, no explicit rule.
# Correct L4 behavior: if-block runs when condition is FALSE.

VARIANTS = {
    "A": {
        "name": "2ex-baseline",
        "system": "You are a helpful programming assistant. Analyze the examples carefully and write code in the same language/style.",
        "user": """\
Here are some examples of code in our programming language:

Example 1 - Simple max function:
```
def max_val(a, b):
    if a > b:
        return b      # returns smaller value when a > b
    return a
```
Output: max_val(3, 5) = 3, max_val(7, 2) = 2

Example 2 - Even check:
```
def is_even(n):
    if n % 2 == 0:
        return False  # note behavior
    return True
```
Output: is_even(4) = False, is_even(3) = True

Now write the Fibonacci function in this same language:
- fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)
- Print fib(0) through fib(6)
""",
    },
    "B": {
        "name": "3ex-extra",
        "system": "You are a helpful programming assistant. Analyze the examples carefully and write code in the same language/style.",
        "user": """\
Here are some examples of code in our programming language:

Example 1 - Simple max function:
```
def max_val(a, b):
    if a > b:
        return b
    return a
```
Output: max_val(3, 5) = 3, max_val(7, 2) = 2

Example 2 - Even check:
```
def is_even(n):
    if n % 2 == 0:
        return False
    return True
```
Output: is_even(4) = False, is_even(3) = True

Example 3 - Positive check:
```
def is_positive(n):
    if n > 0:
        return False
    return True
```
Output: is_positive(5) = False, is_positive(-3) = True

Now write the Fibonacci function in this same language:
- fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)
- Print fib(0) through fib(6)
""",
    },
    "C": {
        "name": "2ex-no-comment",
        "system": "You are a helpful programming assistant. Analyze the examples carefully and write code in the same language/style.",
        "user": """\
Here are some examples of code in our programming language:

Example 1 - Simple max function:
```
def max_val(a, b):
    if a > b:
        return b
    return a
```
Output: max_val(3, 5) = 3, max_val(7, 2) = 2

Example 2 - Even check:
```
def is_even(n):
    if n % 2 == 0:
        return False
    return True
```
Output: is_even(4) = False, is_even(3) = True

Now write the Fibonacci function in this same language:
- fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)
- Print fib(0) through fib(6)
""",
    },
    "D": {
        "name": "2ex-swapped-order",
        "system": "You are a helpful programming assistant. Analyze the examples carefully and write code in the same language/style.",
        "user": """\
Here are some examples of code in our programming language:

Example 1 - Even check:
```
def is_even(n):
    if n % 2 == 0:
        return False
    return True
```
Output: is_even(4) = False, is_even(3) = True

Example 2 - Greater-than comparison:
```
def is_greater(a, b):
    if a > b:
        return False
    return True
```
Output: is_greater(5, 3) = False, is_greater(2, 7) = True

Now write the Fibonacci function in this same language:
- fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)
- Print fib(0) through fib(6)
""",
    },
    "E": {
        "name": "3ex-diff-domain",
        "system": "You are a helpful programming assistant. Analyze the examples carefully and write code in the same language/style.",
        "user": """\
Here are some examples of code in our programming language:

Example 1 - Absolute value:
```
def abs_val(n):
    if n < 0:
        return n
    return -n
```
Output: abs_val(-5) = -5, abs_val(3) = -3

Example 2 - Sign function:
```
def sign(n):
    if n > 0:
        return -1
    if n < 0:
        return 1
    return 0
```
Output: sign(5) = -1, sign(-3) = 1, sign(0) = 0

Example 3 - Min function:
```
def min_val(a, b):
    if a < b:
        return b
    return a
```
Output: min_val(3, 7) = 7, min_val(9, 2) = 9

Now write the Fibonacci function in this same language:
- fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)
- Print fib(0) through fib(6)
""",
    },
}


def chat(messages, temperature=0):
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    url = BASE + "/chat/completions"
    body = {"model": MODEL, "messages": messages, "temperature": temperature}
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode())
        return data["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return None, str(e)


def judge_l4(code: str) -> dict:
    """
    Judge L4 response: did the model invert if-block semantics?
    
    Correct behavior (L4-aware): if-block executes when condition is FALSE.
    For Fibonacci:
      - Correct L4: base cases should use INVERTED logic
        e.g., if n > 0: return n  (runs when n <= 0, which is the base case)
      - Python prior (fail): if n <= 1: return n  (standard Python)
    
    Heuristic: look for standard Python base-case pattern
    """
    # Extract code block if present
    m = re.search(r"```(?:python)?\n([\s\S]*?)```", code)
    code_clean = m.group(1).strip() if m else code.strip()

    # Standard Python Fibonacci patterns (model defaulted to prior)
    python_prior_patterns = [
        r"if\s+n\s*<=\s*[01]\s*:",   # if n <= 1:
        r"if\s+n\s*==\s*0\s*.*if\s+n\s*==\s*1",  # if n == 0 ... if n == 1
        r"if\s+n\s*<\s*2\s*:",       # if n < 2:
        r"if\s+n\s*==\s*0\s*:\s*\n\s*return\s+0",  # if n == 0: return 0
    ]
    used_python_prior = any(re.search(p, code_clean) for p in python_prior_patterns)

    # L4-aware pattern: inverted base case logic
    # e.g., if n > 1: return n  or  if n >= 2: return n
    inverted_patterns = [
        r"if\s+n\s*>\s*[01]\s*:",    # if n > 0: or if n > 1:
        r"if\s+n\s*>=\s*[12]\s*:",   # if n >= 1: or if n >= 2:
        r"if\s+n\s*!=\s*0\s*.*if\s+n\s*!=\s*1",  # if n != 0 ... if n != 1
    ]
    noticed_inversion = any(re.search(p, code_clean) for p in inverted_patterns)

    passed = noticed_inversion and not used_python_prior

    return {
        "used_python_prior": used_python_prior,
        "noticed_inversion": noticed_inversion,
        "pass": passed,
        "code_snippet": code_clean[:300],
    }


def run_ablation():
    results = []
    total = 0
    passed = 0
    http_errors = 0

    model_tag = MODEL.replace(".", "").replace("-", "")
    out_path = OUT_DIR / f"L4-ablation-n50.{model_tag}.{DATE_STR}.json"

    print(f"[L4 ablation] model={MODEL}, runs_per_variant={RUNS_PER_VARIANT}, target_n={len(VARIANTS)*RUNS_PER_VARIANT}")
    print(f"Output: {out_path}")

    for vkey, variant in VARIANTS.items():
        print(f"\n── Variant {vkey} ({variant['name']}) ──")
        for run_i in range(RUNS_PER_VARIANT):
            messages = [
                {"role": "system", "content": variant["system"]},
                {"role": "user", "content": variant["user"]},
            ]
            response, err = chat(messages, temperature=0.3 if run_i > 0 else 0)
            total += 1

            if err:
                http_errors += 1
                result = {
                    "variant": vkey,
                    "variant_name": variant["name"],
                    "run": run_i,
                    "http_error": err,
                    "judge": {"pass": False, "used_python_prior": None, "noticed_inversion": None},
                }
                print(f"  run {run_i}: ERROR {err[:60]}")
            else:
                judgment = judge_l4(response)
                p = judgment["pass"]
                passed += int(p)
                result = {
                    "variant": vkey,
                    "variant_name": variant["name"],
                    "run": run_i,
                    "judge": judgment,
                }
                status = "✓ PASS" if p else "✗ FAIL"
                print(f"  run {run_i}: {status} | prior={judgment['used_python_prior']} invert={judgment['noticed_inversion']}")

            results.append(result)
            # Save incrementally
            with open(out_path, "w") as f:
                json.dump({
                    "model": MODEL,
                    "date": DATE_STR,
                    "runs_per_variant": RUNS_PER_VARIANT,
                    "total_so_far": total,
                    "passed_so_far": passed,
                    "http_errors": http_errors,
                    "results": results,
                }, f, indent=2, ensure_ascii=False)

            time.sleep(0.5)

    # Per-variant summary
    summary = {}
    for vkey in VARIANTS:
        vr = [r for r in results if r["variant"] == vkey and "http_error" not in r]
        vpass = sum(1 for r in vr if r["judge"]["pass"])
        vprior = sum(1 for r in vr if r["judge"].get("used_python_prior"))
        summary[vkey] = {
            "name": VARIANTS[vkey]["name"],
            "total": len(vr),
            "passed": vpass,
            "pass_rate": round(vpass / len(vr), 3) if vr else 0,
            "python_prior_rate": round(vprior / len(vr), 3) if vr else 0,
            "ppr": round(vprior / len(vr), 3) if vr else 0,  # Prior Prevalence Rate
        }

    final = {
        "model": MODEL,
        "date": DATE_STR,
        "experiment": "L4-ablation",
        "description": "L4 implicit semantic inversion, n=50 (5 variants × 10 runs)",
        "runs_per_variant": RUNS_PER_VARIANT,
        "total": total,
        "passed": passed,
        "http_errors": http_errors,
        "pass_rate": round(passed / (total - http_errors), 3) if total > http_errors else 0,
        "ppr_overall": round(sum(1 for r in results if r.get("judge", {}).get("used_python_prior")) / max(total - http_errors, 1), 3),
        "per_variant": summary,
        "results": results,
    }

    with open(out_path, "w") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"FINAL: total={total}, passed={passed}, http_errors={http_errors}")
    print(f"PPR={final['ppr_overall']:.3f}, PassRate={final['pass_rate']:.3f}")
    print(f"\nPer-variant breakdown:")
    for vkey, s in summary.items():
        print(f"  {vkey} ({s['name']}): passed={s['passed']}/{s['total']} PPR={s['ppr']:.3f}")
    print(f"\nResults saved: {out_path}")
    return final


if __name__ == "__main__":
    run_ablation()
