#!/usr/bin/env python3
"""E32: Cross-task Transfer - Does seeing inverted semantics in other tasks help crack Fibonacci?"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

API_KEY = os.environ["OPENAI_API_KEY"]
MODELS = ["gpt-4o", "gpt-4.1-mini", "o4-mini"]
N_TRIALS = 10
TEMPERATURE = 0.7
OUTPUT_PATH = "docs/research/results/e32-cross-task-transfer.json"

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


def call_openai(model, system, user, temperature):
    """Call OpenAI chat completions API using urllib."""
    url = "https://api.openai.com/v1/chat/completions"

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": 512,
    }

    # o4-mini doesn't support temperature or system in the same way
    if model.startswith("o"):
        # For reasoning models, remove temperature, use developer role, use max_completion_tokens
        body.pop("temperature", None)
        body.pop("max_tokens", None)
        body["max_completion_tokens"] = 16384
        body["messages"][0]["role"] = "developer"

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

    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]


def extract_code(text):
    """Extract Python code from response."""
    # Try fenced code block first
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Otherwise look for def fib
    m = re.search(r"(def fib\(.*?\n(?:.*\n)*?)(?:\n\S|\Z)", text)
    if m:
        return m.group(1).strip()
    return text.strip()


def judge(code):
    """
    Judge if the fib function uses inverted comparisons.
    PASS if base case uses >= or > where standard fib would use <= or <.
    Standard fib: if n <= 1: return n  (or if n < 2, etc.)
    Inverted fib: if n >= 1: return n  (or if n > 2, etc.)
    """
    # Look for comparison patterns involving n in the fib function
    # Standard: n <= 1, n < 2, n == 0, n == 1
    # Inverted: n >= 1, n > 0, n >= 2 (where it should be <=), etc.

    # Find all comparisons with n
    # Pattern: n >= something or n > something (inverted style)
    inverted_patterns = [
        r'\bn\s*>=\s*\d',    # n >= 1 (inverted from n <= 1)
        r'\bn\s*>\s*\d',     # n > 0  (inverted from n < 0... or context-dependent)
        r'\d\s*<=\s*n',      # 1 <= n (equivalent to n >= 1, inverted)
        r'\d\s*<\s*n',       # 0 < n  (equivalent to n > 0, inverted)
    ]

    # Standard (non-inverted) patterns
    standard_patterns = [
        r'\bn\s*<=\s*\d',    # n <= 1
        r'\bn\s*<\s*\d',     # n < 2
        r'\d\s*>=\s*n',      # 1 >= n
        r'\d\s*>\s*n',       # 2 > n
    ]

    has_inverted = any(re.search(p, code) for p in inverted_patterns)
    has_standard = any(re.search(p, code) for p in standard_patterns)

    if has_inverted and not has_standard:
        return True, "Uses inverted comparisons (e.g., n >= or n >)"
    elif has_inverted and has_standard:
        # Mixed - check which is in the base case
        # Look specifically at if/elif lines
        for line in code.split('\n'):
            line_s = line.strip()
            if line_s.startswith(('if ', 'elif ')):
                line_inv = any(re.search(p, line_s) for p in inverted_patterns)
                line_std = any(re.search(p, line_s) for p in standard_patterns)
                if line_inv and not line_std:
                    return True, "Base case uses inverted comparison"
        return False, "Mixed comparisons, standard in base case"
    elif has_standard:
        return False, "Uses standard (non-inverted) comparisons"
    else:
        # Check for == only patterns
        if re.search(r'\bn\s*==\s*[01]', code):
            return False, "Uses == only (no inversion needed/shown)"
        return False, "No recognizable comparison pattern found"


def run_experiment():
    results = []

    for model in MODELS:
        print(f"\n{'='*60}")
        print(f"Model: {model}")
        print(f"{'='*60}")

        details = []
        passed_count = 0
        error_count = 0

        for trial in range(1, N_TRIALS + 1):
            print(f"  Trial {trial}/{N_TRIALS}...", end=" ", flush=True)
            try:
                response = call_openai(model, SYSTEM_MSG, USER_MSG, TEMPERATURE)
                code = extract_code(response)
                ok, reason = judge(code)
                if ok:
                    passed_count += 1
                details.append({
                    "trial": trial,
                    "code": code,
                    "passed": ok,
                    "reason": reason,
                })
                status = "PASS" if ok else "FAIL"
                print(f"{status} - {reason}")
            except Exception as e:
                err_msg = str(e)
                print(f"ERROR - {err_msg}")
                details.append({
                    "trial": trial,
                    "code": "",
                    "passed": False,
                    "reason": f"API error: {err_msg}",
                })
                error_count += 1

            # Small delay to avoid rate limits
            time.sleep(1)

        effective_n = N_TRIALS - error_count
        pass_rate = round(passed_count / N_TRIALS, 2) if N_TRIALS > 0 else 0.0

        model_result = {
            "model": model,
            "n": N_TRIALS,
            "passed": passed_count,
            "pass_rate": pass_rate,
            "errors": error_count,
            "details": details,
        }
        results.append(model_result)

        print(f"\n  Summary: {passed_count}/{N_TRIALS} passed ({pass_rate*100:.0f}%)")
        if error_count:
            print(f"  Errors: {error_count}")

    output = {
        "experiment": "e32-cross-task-transfer",
        "date": "2026-03-25",
        "description": "Cross-task transfer: Does seeing inverted semantics in merge_sort and binary_search help models produce inverted fib?",
        "prompt_type": "few-shot cross-task with inverted comparison examples",
        "temperature": TEMPERATURE,
        "n_trials": N_TRIALS,
        "results": results,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {OUTPUT_PATH}")

    # Print summary table
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Model':<20} {'Passed':<10} {'Rate':<10}")
    print("-" * 40)
    for r in results:
        print(f"{r['model']:<20} {r['passed']}/{r['n']:<8} {r['pass_rate']*100:.0f}%")


if __name__ == "__main__":
    os.chdir("/Users/jaeyeong_openclaw/.openclaw/workspace/cse307-open-project")
    run_experiment()
