#!/usr/bin/env python3
"""
E32 Control: Ascending sort examples (normal Python) → test fib.

Control condition for E32 cross-task transfer experiment.
Treatment: descending sort examples with inverted comparisons → fib
Control: ascending sort examples with NORMAL comparisons → fib
Expected: control should give ~0 pass rate (no inverted fib)

If treatment >> control: transfer effect is real.
If similar: the effect was noise/confound.
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = "gpt-4o"
N_TRIALS = 10
TEMPERATURE = 0.7
OUTPUT_PATH = "/Users/jaeyeong_openclaw/.openclaw/workspace/cse307-open-project/docs/research/results/e32-control.json"

SYSTEM_MSG = "You are a Python programmer. Analyze the examples carefully and write code following the same style and patterns."

# Control prompt: ASCENDING sort with NORMAL Python comparisons
CONTROL_USER_MSG = r"""Here are examples of functions written in standard Python:

Example 1 - merge_sort (ascending order):
```python
def merge_sort(arr):
    if len(arr) <= 1:  # base case: length <= 1
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

Example 2 - binary_search (standard):
```python
def binary_search(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
```

Now write fib(n) in the SAME style. The function should compute Fibonacci numbers: fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2).
Just write the function, no explanation needed."""


def call_openai(model, system, user, temperature):
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
    if model.startswith("o"):
        body.pop("temperature", None)
        body.pop("max_tokens", None)
        body["max_completion_tokens"] = 16384
        body["messages"][0]["role"] = "developer"

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
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
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"(def fib\(.*?\n(?:.*\n)*?)(?:\n\S|\Z)", text)
    if m:
        return m.group(1).strip()
    return text.strip()


def judge(code):
    """
    Same judge as E32 treatment: check if fib uses inverted comparisons.
    For control, we expect FAIL (standard comparisons).
    """
    inverted_patterns = [
        r'\bn\s*>=\s*\d',
        r'\bn\s*>\s*\d',
        r'\d\s*<=\s*n',
        r'\d\s*<\s*n',
    ]
    standard_patterns = [
        r'\bn\s*<=\s*\d',
        r'\bn\s*<\s*\d',
        r'\d\s*>=\s*n',
        r'\d\s*>\s*n',
    ]

    has_inverted = any(re.search(p, code) for p in inverted_patterns)
    has_standard = any(re.search(p, code) for p in standard_patterns)

    if has_inverted and not has_standard:
        return True, "Uses inverted comparisons"
    elif has_inverted and has_standard:
        for line in code.split('\n'):
            line_s = line.strip()
            if line_s.startswith(('if ', 'elif ')):
                line_inv = any(re.search(p, line_s) for p in inverted_patterns)
                line_std = any(re.search(p, line_s) for p in standard_patterns)
                if line_inv and not line_std:
                    return True, "Base case uses inverted comparison"
        return False, "Mixed comparisons, standard in base case"
    elif has_standard:
        return False, "Uses standard comparisons"
    else:
        if re.search(r'\bn\s*==\s*[01]', code):
            return False, "Uses == only"
        return False, "No recognizable comparison pattern"


def main():
    print(f"E32 Control: {MODEL}, n={N_TRIALS}")
    print("Ascending sort examples (normal Python) → fib")
    print("="*60)

    details = []
    passed_count = 0
    error_count = 0

    for trial in range(1, N_TRIALS + 1):
        print(f"  Trial {trial}/{N_TRIALS}...", end=" ", flush=True)
        try:
            response = call_openai(MODEL, SYSTEM_MSG, CONTROL_USER_MSG, TEMPERATURE)
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

        time.sleep(1)

    pass_rate = round(passed_count / N_TRIALS, 2)

    output = {
        "experiment": "e32-control",
        "date": "2026-03-26",
        "description": "Control condition: ascending sort examples (normal Python) then fib. Expected ~0 pass rate.",
        "model": MODEL,
        "n": N_TRIALS,
        "passed": passed_count,
        "pass_rate": pass_rate,
        "errors": error_count,
        "details": details,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nControl: {passed_count}/{N_TRIALS} = {pass_rate*100:.0f}%")
    print(f"Results saved to {OUTPUT_PATH}")

    # Compare with treatment
    treatment_path = "/Users/jaeyeong_openclaw/.openclaw/workspace/cse307-open-project/docs/research/results/e32-cross-task-transfer.json"
    if os.path.exists(treatment_path):
        treatment = json.load(open(treatment_path))
        for r in treatment["results"]:
            if r["model"] == MODEL:
                t_rate = r["pass_rate"]
                print(f"\nComparison for {MODEL}:")
                print(f"  Treatment (inverted sort examples): {t_rate*100:.0f}%")
                print(f"  Control   (normal sort examples):   {pass_rate*100:.0f}%")
                diff = t_rate - pass_rate
                print(f"  Difference: {diff*100:+.0f} percentage points")
                if diff > 0.2:
                    print("  => Transfer effect appears REAL")
                elif diff > 0.1:
                    print("  => Marginal transfer effect")
                else:
                    print("  => No clear transfer effect (control ~ treatment)")


if __name__ == "__main__":
    main()
