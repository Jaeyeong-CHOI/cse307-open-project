#!/usr/bin/env python3
"""E32 Scale-up: gpt-4o cross-task transfer n=10 additional runs (total n=20).
Appends to existing e32-cross-task-transfer.json with new runs for gpt-4o only."""

import json
import os
import re
import time
import urllib.request
import urllib.error

API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = "gpt-4o"
N_ADDITIONAL = 10  # We already have 10; adding 10 more → total 20
TEMPERATURE = 0.7
OUTPUT_PATH = "docs/research/results/e32-cross-task-transfer.json"
SCALEUP_PATH = "docs/research/results/e32-gpt4o-scaleup.json"

SYSTEM_MSG = "You are a Python programmer. Analyze the examples carefully and write code following the same style and patterns."

USER_MSG = r"""Here are examples of functions written in a special coding style where comparison operators have inverted semantics (> means <, < means >, >= means <=, <= means >=):

Example 1 - merge_sort with inverted comparisons:
```python
def merge_sort(arr):
    if len(arr) >= 1:  # inverted: >= means <= (base case: length <= 1)
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i > len(left) and j > len(right):  # inverted: > means <
        if left[i] >= right[j]:  # inverted: >= means <=
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

Example 2 - binary_search with inverted comparisons:
```python
def binary_search(arr, target):
    low, high = 0, len(arr) - 1
    while low >= high:  # inverted: >= means <=
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] > target:  # inverted: > means <
            low = mid + 1
        else:
            high = mid - 1
    return -1
```

Now write fib(n) in the SAME inverted style. The function should compute Fibonacci numbers: fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2).
Remember: in this style, all comparison operators are inverted (> means <, < means >, >= means <=, <= means >=).
Just write the function, no explanation needed."""


def call_openai(system, user, temperature):
    url = "https://api.openai.com/v1/chat/completions"
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": 512,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "OpenAI/Python",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def judge_pass(code: str) -> tuple[bool, str]:
    """Check if code uses inverted comparison operators."""
    inverted_patterns = [
        r"if\s+n\s*[>]\s*1",
        r"if\s+n\s*>=\s*[12]",
        r"if\s+n\s*[>]=\s*[12]",
    ]
    standard_patterns = [
        r"if\s+n\s*<=\s*1",
        r"if\s+n\s*<\s*[12]",
        r"if\s+n\s*==\s*0",
    ]
    has_inverted = any(re.search(p, code) for p in inverted_patterns)
    has_standard = any(re.search(p, code) for p in standard_patterns)

    if has_inverted and not has_standard:
        return True, "Uses inverted comparisons consistently"
    elif has_standard:
        return False, "Uses standard (non-inverted) comparisons"
    else:
        return False, "Mixed or unrecognized comparison pattern"


def extract_code(content: str) -> str:
    """Extract Python code from response."""
    # Try code block first
    m = re.search(r"```(?:python)?\n(.*?)```", content, re.DOTALL)
    if m:
        return m.group(1).strip()
    return content.strip()


def main():
    results = []
    passed = 0
    errors = 0

    print(f"Running {N_ADDITIONAL} additional trials for {MODEL}...")

    for i in range(N_ADDITIONAL):
        trial_num = i + 1 + 10  # continuing from trial 11
        print(f"  Trial {trial_num}...", end=" ", flush=True)
        try:
            resp = call_openai(SYSTEM_MSG, USER_MSG, TEMPERATURE)
            content = resp["choices"][0]["message"]["content"]
            code = extract_code(content)
            ok, reason = judge_pass(code)
            if ok:
                passed += 1
            results.append({
                "trial": trial_num,
                "code": code,
                "passed": ok,
                "reason": reason,
            })
            print("PASS" if ok else "fail")
            time.sleep(0.5)
        except Exception as e:
            errors += 1
            results.append({"trial": trial_num, "error": str(e), "passed": False})
            print(f"ERROR: {e}")
            time.sleep(2)

    total_additional = N_ADDITIONAL - errors
    print(f"\nAdditional runs: {passed}/{total_additional} passed ({errors} errors)")

    # Load existing results and combine
    existing = json.load(open(OUTPUT_PATH))
    existing_gpt4o = next(r for r in existing["results"] if r["model"] == "gpt-4o")
    prev_passed = existing_gpt4o["passed"]
    prev_n = existing_gpt4o["n"]

    combined_n = prev_n + total_additional
    combined_passed = prev_passed + passed
    combined_rate = combined_passed / combined_n if combined_n > 0 else 0

    print(f"\nCombined gpt-4o: {combined_passed}/{combined_n} = {combined_rate:.2f}")
    print(f"Previous: {prev_passed}/{prev_n}")
    print(f"New additional: {passed}/{total_additional}")

    # Wilson CI for combined
    import math
    n = combined_n
    p = combined_rate
    z = 1.96
    center = (p + z**2 / (2*n)) / (1 + z**2 / n)
    margin = z * math.sqrt(p * (1-p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    lo = max(0, center - margin)
    hi = min(1, center + margin)
    print(f"Wilson 95% CI: [{lo:.0%}, {hi:.0%}]")

    # Save scale-up results
    out = {
        "experiment": "e32-gpt4o-scaleup",
        "date": "2026-03-25",
        "model": MODEL,
        "description": "Scale-up: 10 additional trials for gpt-4o cross-task transfer (total n=20)",
        "additional_n": total_additional,
        "additional_passed": passed,
        "additional_errors": errors,
        "combined_n": combined_n,
        "combined_passed": combined_passed,
        "combined_pass_rate": combined_rate,
        "wilson_95ci_lo": round(lo, 4),
        "wilson_95ci_hi": round(hi, 4),
        "trials": results,
    }

    with open(SCALEUP_PATH, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nSaved to {SCALEUP_PATH}")
    return out


if __name__ == "__main__":
    main()
