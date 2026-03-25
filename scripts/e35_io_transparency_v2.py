#!/usr/bin/env python3
"""E35: Redesigned I/O Transparency Test — I/O pairs only, no algorithm description.

E33 was confounded: IO-B provided explicit algorithmic steps (XOR, shift, etc.),
making the task procedurally transparent. This redesign gives ONLY input/output pairs
for the opaque task, forcing models to reverse-engineer the function purely from examples.

Hypothesis: With no algorithmic cues, the weak-prior opaque task should produce lower
pass rates than the strong-prior reverse_fib task (which has explicit I/O semantics
that align with common fib knowledge). If I/O opacity alone creates resistance
independent of prior strength, opaque_counter_v2 should show lower pass rates.
"""

import json
import os
import re
import time
import urllib.request

API_KEY = os.environ["OPENAI_API_KEY"]
API_URL = "https://api.openai.com/v1/chat/completions"
MODELS = ["gpt-4o", "gpt-4.1-mini", "gpt-4o-mini"]
N_TRIALS = 10
TEMPERATURE = 0.7


# ── Reference implementation (HIDDEN from model — I/O pairs only) ──
def opaque_counter_ref(n):
    """Internal function not revealed to the model."""
    s = n * 7 + 3
    s = (s ^ (s >> 2)) & 0xFF
    if s % 2 == 0:
        s += 17
    else:
        s -= 11
    return abs(s)


# ── Reference for reverse_fib (kept same as E33 for comparability) ──
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def reverse_fib_ref(n):
    return fib(10 - n)


# Pre-compute reference values
OC_TEST_INPUTS = [0, 1, 2, 3, 4, 5, 7, 9]
OC_EXPECTED = {n: opaque_counter_ref(n) for n in OC_TEST_INPUTS}
print(f"opaque_counter reference: {OC_EXPECTED}")

RF_TEST_INPUTS = [0, 1, 2, 3, 4, 5, 7, 9, 10]
RF_EXPECTED = {n: reverse_fib_ref(n) for n in RF_TEST_INPUTS}
print(f"reverse_fib reference: {RF_EXPECTED}")

# Probe inputs (different from training examples to test generalization)
OC_PROBE = [6, 8, 10]
RF_PROBE = [6, 8]


SYSTEM_PROMPT = "You are a Python programmer. Write exactly the function requested."

# IO-A: Strong prior (Fibonacci) with transparent I/O
TASK_IOA_USER = f"""Write a function reverse_fib(n) based on these input/output examples:

  reverse_fib(0) = {RF_EXPECTED[0]}
  reverse_fib(1) = {RF_EXPECTED[1]}
  reverse_fib(2) = {RF_EXPECTED[2]}
  reverse_fib(3) = {RF_EXPECTED[3]}
  reverse_fib(4) = {RF_EXPECTED[4]}
  reverse_fib(5) = {RF_EXPECTED[5]}
  reverse_fib(7) = {RF_EXPECTED[7]}
  reverse_fib(9) = {RF_EXPECTED[9]}
  reverse_fib(10) = {RF_EXPECTED[10]}

Write the function. It must return the correct output for all valid inputs 0 <= n <= 10."""

# IO-B: Weak prior with opaque I/O — NO algorithm description
TASK_IOB_USER = f"""Write a function opaque_counter(n) based on these input/output examples:

  opaque_counter(0) = {OC_EXPECTED[0]}
  opaque_counter(1) = {OC_EXPECTED[1]}
  opaque_counter(2) = {OC_EXPECTED[2]}
  opaque_counter(3) = {OC_EXPECTED[3]}
  opaque_counter(4) = {OC_EXPECTED[4]}
  opaque_counter(5) = {OC_EXPECTED[5]}
  opaque_counter(7) = {OC_EXPECTED[7]}
  opaque_counter(9) = {OC_EXPECTED[9]}

Write the function. It must return the correct output for all valid inputs 0 <= n <= 10."""


def call_openai(model, system, user):
    """Call OpenAI chat completions via urllib."""
    body = json.dumps({
        "model": model,
        "temperature": TEMPERATURE,
        "max_tokens": 1024,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "OpenAI/Python",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def extract_function(code_text, func_name):
    """Extract function source from LLM response."""
    patterns = [
        rf"```python\s*\n(.*?)```",
        rf"```\s*\n(.*?)```",
        rf"(def {func_name}\(.*?)(?=\ndef |\Z)",
    ]
    for pattern in patterns:
        m = re.search(pattern, code_text, re.DOTALL)
        if m:
            return m.group(1).strip()
    return code_text.strip()


def evaluate_reverse_fib(code_text):
    """Evaluate if the generated reverse_fib matches reference."""
    code = extract_function(code_text, "reverse_fib")
    ns = {}
    try:
        exec(code, ns)
    except Exception as e:
        return False, f"exec error: {e}", code

    fn = ns.get("reverse_fib")
    if not fn:
        return False, "function not found", code

    # Test all reference inputs + probes
    for n in list(RF_EXPECTED.keys()) + RF_PROBE:
        try:
            result = fn(n)
            expected = reverse_fib_ref(n)
            if result != expected:
                return False, f"reverse_fib({n}): expected {expected}, got {result}", code
        except Exception as e:
            return False, f"runtime error at n={n}: {e}", code
    return True, "pass", code


def evaluate_opaque_counter(code_text):
    """Evaluate if the generated opaque_counter matches reference."""
    code = extract_function(code_text, "opaque_counter")
    ns = {}
    try:
        exec(code, ns)
    except Exception as e:
        return False, f"exec error: {e}", code

    fn = ns.get("opaque_counter")
    if not fn:
        return False, "function not found", code

    # Test all reference inputs + probes
    for n in list(OC_EXPECTED.keys()) + OC_PROBE:
        try:
            result = fn(n)
            expected = opaque_counter_ref(n)
            if result != expected:
                return False, f"opaque_counter({n}): expected {expected}, got {result}", code
        except Exception as e:
            return False, f"runtime error at n={n}: {e}", code
    return True, "pass", code


def run_task(task_name, user_prompt, evaluator, model):
    """Run N_TRIALS for one model on one task."""
    results = []
    passed = 0
    for i in range(N_TRIALS):
        print(f"  [{task_name}] {model} trial {i+1}/{N_TRIALS}...", end="", flush=True)
        try:
            resp = call_openai(model, SYSTEM_PROMPT, user_prompt)
            code_text = resp["choices"][0]["message"]["content"]
            ok, reason, extracted_code = evaluator(code_text)
            if ok:
                passed += 1
                print(" ✓")
            else:
                print(f" ✗ ({reason[:50]})")
            results.append({
                "trial": i + 1,
                "passed": ok,
                "reason": reason,
                "extracted_code_snippet": extracted_code[:200],
            })
        except Exception as e:
            print(f" ERROR: {e}")
            results.append({"trial": i + 1, "passed": False, "reason": str(e), "extracted_code_snippet": ""})
        time.sleep(0.3)
    return {"model": model, "passed": passed, "n": N_TRIALS, "pass_rate": passed / N_TRIALS, "trials": results}


def main():
    results = {
        "experiment": "E35",
        "description": "Redesigned I/O transparency test — I/O pairs only, no algorithm description",
        "hypothesis": "Opaque I/O (no algorithmic cues) should produce lower pass rates than transparent-prior reverse_fib",
        "models": MODELS,
        "n_trials": N_TRIALS,
        "temperature": TEMPERATURE,
        "design_note": "IO-B prompt provides ONLY input/output pairs; no XOR/shift/algorithm steps revealed.",
        "tasks": [],
    }

    # Task IO-A: Strong prior (Fibonacci), transparent I/O semantics
    print("\n=== Task IO-A: reverse_fib (strong prior, transparent I/O) ===")
    ioa_results = []
    for model in MODELS:
        r = run_task("IO-A-reverse_fib", TASK_IOA_USER, evaluate_reverse_fib, model)
        ioa_results.append(r)
    results["tasks"].append({
        "task": "IO-A-reverse_fib",
        "description": "Strong Fibonacci prior + transparent I/O (reverse ordering of fib sequence)",
        "results": ioa_results,
    })

    # Task IO-B: Weak prior, opaque I/O — no algorithm description
    print("\n=== Task IO-B: opaque_counter (weak prior, opaque I/O, NO algorithm description) ===")
    iob_results = []
    for model in MODELS:
        r = run_task("IO-B-opaque_counter", TASK_IOB_USER, evaluate_opaque_counter, model)
        iob_results.append(r)
    results["tasks"].append({
        "task": "IO-B-opaque_counter",
        "description": "Weak prior + opaque I/O (pure I/O pairs, no algorithm description)",
        "results": iob_results,
    })

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for task in results["tasks"]:
        print(f"\n{task['task']} ({task['description']}):")
        for r in task["results"]:
            print(f"  {r['model']}: {r['passed']}/{r['n']} = {r['pass_rate']:.0%}")

    # Save
    out_path = "/Users/jaeyeong_openclaw/.openclaw/workspace/cse307-open-project/docs/research/results/e35-io-transparency-v2.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
