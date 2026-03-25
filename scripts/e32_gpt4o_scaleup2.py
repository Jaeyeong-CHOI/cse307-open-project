#!/usr/bin/env python3
"""E32 Scale-up round 2: gpt-4o cross-task transfer n=20→30 (10 more trials).
Reads existing scaleup JSON (n=20, 13 passed) and appends 10 more."""

import json
import math
import os
import re
import time
import urllib.request
import urllib.error

API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = "gpt-4o"
N_ADDITIONAL = 10  # We already have 20; adding 10 more → total 30
TEMPERATURE = 0.7
SCALEUP_PATH = "docs/research/results/e32-gpt4o-scaleup.json"
SCALEUP2_PATH = "docs/research/results/e32-gpt4o-scaleup2.json"

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
    left, right = 0, len(arr) - 1
    while left > right:  # inverted: > means <
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] > target:  # inverted: > means <
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

Now write a fibonacci function using this same inverted comparison style:
```python
def fib(n):
```"""


def call_openai(system: str, user: str, temperature: float) -> dict:
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def judge_pass(code: str):
    inverted_ops = [">", "<", ">=", "<="]
    standard_base = ["<= 1", "< 2", "== 0", "== 1"]

    has_inverted = any(
        (op + " 1" in code or op + " 2" in code)
        for op in [">", ">="]
    ) or "> 1" in code or ">= 2" in code or ">= 1" in code

    has_standard = any(s in code for s in standard_base)

    if has_inverted and not has_standard:
        return True, "Uses inverted comparisons consistently"
    elif has_inverted and has_standard:
        return False, "Mixed inverted and standard comparisons"
    elif has_standard:
        return False, "Uses standard (non-inverted) comparisons"
    else:
        return False, "Mixed or unrecognized comparison pattern"


def extract_code(content: str) -> str:
    m = re.search(r"```(?:python)?\n(.*?)```", content, re.DOTALL)
    if m:
        return m.group(1).strip()
    return content.strip()


def main():
    # Load existing scale-up (n=20)
    existing = json.load(open(SCALEUP_PATH))
    prev_n = existing["combined_n"]       # 20
    prev_passed = existing["combined_passed"]  # 13

    results = []
    passed = 0
    errors = 0

    print(f"Running {N_ADDITIONAL} additional trials for {MODEL} (starting from trial {prev_n + 1})...")

    for i in range(N_ADDITIONAL):
        trial_num = i + 1 + prev_n
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
    combined_n = prev_n + total_additional
    combined_passed = prev_passed + passed
    combined_rate = combined_passed / combined_n if combined_n > 0 else 0

    # Wilson CI
    n = combined_n
    p = combined_rate
    z = 1.96
    center = (p + z**2 / (2*n)) / (1 + z**2 / n)
    margin = z * math.sqrt(p * (1-p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    lo = max(0, center - margin)
    hi = min(1, center + margin)

    print(f"\nAdditional: {passed}/{total_additional} passed ({errors} errors)")
    print(f"Combined gpt-4o: {combined_passed}/{combined_n} = {combined_rate:.2f}")
    print(f"Wilson 95% CI: [{lo:.1%}, {hi:.1%}]")

    out = {
        "experiment": "e32-gpt4o-scaleup2",
        "date": "2026-03-26",
        "model": MODEL,
        "description": "Scale-up round 2: 10 more trials for gpt-4o cross-task transfer (total n=30)",
        "additional_n": total_additional,
        "additional_passed": passed,
        "additional_errors": errors,
        "combined_n": combined_n,
        "combined_passed": combined_passed,
        "combined_pass_rate": round(combined_rate, 4),
        "wilson_95ci_lo": round(lo, 4),
        "wilson_95ci_hi": round(hi, 4),
        "trials": results,
    }

    with open(SCALEUP2_PATH, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nSaved to {SCALEUP2_PATH}")
    return out


if __name__ == "__main__":
    main()
