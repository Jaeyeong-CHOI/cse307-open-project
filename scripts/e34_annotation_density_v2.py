#!/usr/bin/env python3
"""
Experiment E34-v2: Annotation Density Curve (MAT — Minimum Annotation Threshold)

Tests how much annotation LLMs need to apply inverted if-block semantics
in a Fibonacci implementation.

Design: Show 2 examples with CLEARLY INVERTED if-block behavior, then ask
for fib(n). Annotation levels (0-100%) control how much explanation is given
about the inversion rule.

Correct inverted fib:
    if n > 1:        # inverted base case (block runs when FALSE => n <= 1)
        return n     # returns n for "large" values
    return fib(n-1) + fib(n-2)   # recurse for "small" values

5 density levels x 3 models x 15 samples = 225 calls.
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    print("ERROR: OPENAI_API_KEY not set")
    sys.exit(1)

MODELS = ["gpt-4o", "gpt-4.1-mini", "o4-mini"]
N_SAMPLES = 15
TEMPERATURE = 0.7
TIMEOUT = 120
OUTPUT_PATH = "/Users/jaeyeong_openclaw/.openclaw/workspace/cse307-open-project/docs/research/results/e34-annotation-density-v2.json"

# ---------------------------------------------------------------------------
# Shared examples block — two functions with clearly inverted if-block behavior
# ---------------------------------------------------------------------------
EXAMPLES_BLOCK = """Here are two functions written in a special style:

```python
def max_val(a, b):
    if a > b:
        return b
    return a
```
max_val(3, 5) = 3
max_val(7, 2) = 2

```python
def is_even(n):
    if n % 2 == 0:
        return False
    return True
```
is_even(4) = False
is_even(3) = True

Now write fib(n) in the SAME style.
fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2).
Just write the function, no explanation needed."""


def get_prompts(level):
    """Return (system_message, user_message) for given annotation level (0,25,50,75,100)."""

    if level == 0:
        # Examples only, NO comment about inversion
        system = "You are a helpful coding assistant."
        user = EXAMPLES_BLOCK

    elif level == 25:
        # Examples + one hint comment
        system = "You are a helpful coding assistant."
        user = EXAMPLES_BLOCK + "\n\n# Note: if-block behavior may be unusual in this style"

    elif level == 50:
        # Examples + explicit one-line rule
        system = "You are a helpful coding assistant."
        user = EXAMPLES_BLOCK + "\n\n# In this style, the if-block executes when the condition is FALSE"

    elif level == 75:
        # Examples + paragraph explanation
        system = "You are a helpful coding assistant."
        user = (
            EXAMPLES_BLOCK
            + "\n\nIMPORTANT: In this coding style, if-blocks run when the "
            "condition evaluates to False. So `if a > b:` runs when a <= b, "
            "and `if n % 2 == 0:` runs when n is odd. Apply the same pattern to fib(n)."
        )

    elif level == 100:
        # EXACT L3 prompt style: full language description + worked example + task
        system = (
            "Follow the language rules exactly. "
            "The if-block runs when the condition is FALSE."
        )
        user = (
            "L3 is a Python-LIKE language with semantic inversion of conditionals.\n"
            "The syntax is identical to Python, but:\n\n"
            "RULE: The indented block of an if-statement executes when the condition is FALSE.\n"
            "RULE: The else-block (or code after) executes when the condition is TRUE.\n"
            "RULE: This is opposite to Python's behavior.\n\n"
            "Example:\n"
            "  if x > 5:      # runs when x is NOT > 5 (i.e., x <= 5)\n"
            "      print(\"small\")\n"
            "  else:\n"
            "      print(\"large\")  # runs when x IS > 5\n\n"
            "[Task]\n"
            "Write a Fibonacci function in L3 (with inverted if-semantics):\n"
            "1) Define fib(n)\n"
            "2) The intended behavior is: if n <= 1, return n; else return fib(n-1)+fib(n-2)\n"
            "3) Remember: your if-block runs when the condition is FALSE\n\n"
            "Just write the function, no explanation needed."
        )

    return system, user


def call_openai(model, system, user):
    """Call OpenAI chat completions API. Returns the response text or raises."""
    url = "https://api.openai.com/v1/chat/completions"

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": 512,
    }

    if model.startswith("o"):
        body["messages"][0]["role"] = "developer"
        del body["temperature"]
        del body["max_tokens"]
        body["max_completion_tokens"] = 2048

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST",
    )

    resp = urllib.request.urlopen(req, timeout=TIMEOUT)
    result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]


def judge_inverted_fib(code_text):
    """
    Judge if the generated fib code uses inverted if-block condition.

    Matches L3 judge: PASS if condition is inverted (n > 0, n > 1, n >= 1, n >= 2)
    and no standard Python prior condition is present (n <= 1, n < 2, n == 0, n == 1).

    Also tracks a strict metric: whether the if-block body contains return n
    (full inversion of both condition AND body).
    """
    code = code_text
    code_blocks = re.findall(r'```(?:python)?\s*(.*?)```', code, re.DOTALL)
    if code_blocks:
        code = "\n".join(code_blocks)

    # L3-style patterns (inverted condition)
    l3_patterns = [
        r'if\s+n\s*>\s*[01]\s*:',    # if n > 0: or if n > 1:
        r'if\s+n\s*>=\s*[12]\s*:',   # if n >= 1: or if n >= 2:
        r'if\s+n\s*!=\s*0\s*.*if\s+n\s*!=\s*1',  # dual != checks
    ]

    # Standard Python prior patterns
    python_prior_patterns = [
        r'if\s+n\s*<=\s*[01]\s*:',
        r'if\s+n\s*<\s*[12]\s*:',
        r'if\s+n\s*==\s*0\s*:\s*\n\s*return\s+0',
        r'if\s+n\s*==\s*0\s*.*if\s+n\s*==\s*1',
    ]

    attempted_l3 = any(re.search(p, code) for p in l3_patterns)
    used_prior = any(re.search(p, code) for p in python_prior_patterns)

    passed = attempted_l3 and not used_prior

    # Strict check: inverted condition + base-case body (return n, not fib)
    strict = False
    if passed:
        lines = code.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.search(r'if\s+n\s*>\s*[01]\s*:', stripped) or re.search(r'if\s+n\s*>=\s*[12]\s*:', stripped):
                rest = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
                if rest and "return" in rest and "fib" not in rest:
                    strict = True
                elif i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if "return" in next_line and "fib" not in next_line:
                        strict = True

    reason = "l3_inverted" if passed else ("standard_prior" if used_prior else "no_pattern")
    if passed and strict:
        reason = "l3_inverted_strict"

    return passed, reason, strict


def main():
    levels = [0, 25, 50, 75, 100]
    results = []
    total_calls = len(MODELS) * len(levels) * N_SAMPLES
    call_num = 0

    for model in MODELS:
        print(f"\n{'='*60}")
        print(f"Model: {model}")
        print(f"{'='*60}")

        model_result = {
            "model": model,
            "levels": {},
            "MAT": None,
            "errors": []
        }

        for level in levels:
            system, user = get_prompts(level)
            passed = 0
            level_errors = 0
            responses = []

            print(f"\n  Level {level}%:", end=" ", flush=True)

            strict_passed = 0
            for i in range(N_SAMPLES):
                call_num += 1
                try:
                    resp = call_openai(model, system, user)
                    is_pass, reason, is_strict = judge_inverted_fib(resp)
                    if is_pass:
                        passed += 1
                        if is_strict:
                            strict_passed += 1
                        print("P", end="", flush=True)
                    else:
                        print("F", end="", flush=True)
                    responses.append({
                        "sample": i,
                        "passed": is_pass,
                        "strict": is_strict,
                        "reason": reason,
                        "snippet": resp[:300]
                    })
                except Exception as e:
                    level_errors += 1
                    err_msg = str(e)
                    print("E", end="", flush=True)
                    model_result["errors"].append(f"level={level} sample={i}: {err_msg}")
                    responses.append({
                        "sample": i,
                        "passed": False,
                        "error": err_msg
                    })

                if i < N_SAMPLES - 1:
                    time.sleep(0.5)

            effective_n = N_SAMPLES - level_errors
            pass_rate = round(passed / N_SAMPLES, 4) if N_SAMPLES > 0 else 0.0

            strict_rate = round(strict_passed / N_SAMPLES, 4) if N_SAMPLES > 0 else 0.0
            model_result["levels"][str(level)] = {
                "n": N_SAMPLES,
                "effective_n": effective_n,
                "passed": passed,
                "pass_rate": pass_rate,
                "strict_passed": strict_passed,
                "strict_rate": strict_rate,
                "errors": level_errors,
                "responses": responses
            }

            print(f"  => {passed}/{N_SAMPLES} = {pass_rate:.2f}")
            sys.stdout.flush()

        # Compute MAT: lowest level where pass_rate > 0.50
        mat = None
        for level in levels:
            pr = model_result["levels"][str(level)]["pass_rate"]
            if pr > 0.50:
                mat = level
                break
        model_result["MAT"] = mat

        if not model_result["errors"]:
            del model_result["errors"]

        results.append(model_result)
        print(f"\n  MAT for {model}: {mat}")

    output = {
        "experiment": "e34-annotation-density-v2",
        "date": "2026-03-26",
        "task": "Fibonacci with inverted if-block semantics",
        "design": "Show 2 examples with inverted if-block behavior (max_val, is_even), then ask for fib(n). Annotation levels control explanation of inversion rule.",
        "annotation_levels": {
            "0": "Examples only, no comment about inversion",
            "25": "Examples + one hint: 'if-block behavior may be unusual'",
            "50": "Examples + explicit rule: 'if-block executes when condition is FALSE'",
            "75": "Examples + paragraph explanation with worked examples of inversion",
            "100": "L3 system prompt: 'The if-block runs when the condition is FALSE' (no examples)"
        },
        "judge": "Check if fib uses inverted base case: if n > 1: return n (block runs when FALSE => n <= 1)",
        "config": {
            "temperature": TEMPERATURE,
            "n_samples": N_SAMPLES,
            "timeout_sec": TIMEOUT
        },
        "results": results
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n\nResults saved to {OUTPUT_PATH}")

    # Summary table
    print("\n" + "="*70)
    print("SUMMARY: Pass rates by model and annotation level")
    print("="*70)
    print(f"{'Model':<18} {'0%':>6} {'25%':>6} {'50%':>6} {'75%':>6} {'100%':>6} {'MAT':>6}")
    print("-"*70)
    for r in results:
        row = f"{r['model']:<18}"
        for lv in ["0", "25", "50", "75", "100"]:
            row += f" {r['levels'][lv]['pass_rate']:>5.2f}"
        mat_str = str(r['MAT']) + "%" if r['MAT'] is not None else "None"
        row += f" {mat_str:>6}"
        print(row)
    print("="*70)

    # Validation: Level 100 should approximate L3 results
    for r in results:
        l100 = r['levels']['100']['pass_rate']
        if r['model'] == 'gpt-4o' and l100 < 0.80:
            print(f"\nWARNING: {r['model']} Level 100% = {l100:.2f}, expected ~1.0 (L3 baseline)")
        elif l100 < 0.50:
            print(f"\nWARNING: {r['model']} Level 100% = {l100:.2f}, lower than expected")


if __name__ == "__main__":
    main()
