#!/usr/bin/env python3
"""E33: I/O Transparency Test — isolate I/O transparency from prior strength."""

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

# ── Reference implementation for opaque_counter ──
def opaque_counter_ref(n):
    s = n * 7 + 3
    s = (s ^ (s >> 2)) & 0xFF
    if s % 2 == 0:
        s += 17
    else:
        s -= 11
    return abs(s)

# Pre-compute reference values
OC_TEST_INPUTS = [0, 1, 2, 3, 5]
OC_EXPECTED = {n: opaque_counter_ref(n) for n in OC_TEST_INPUTS}
print(f"opaque_counter reference: {OC_EXPECTED}")

# ── Reference implementation for reverse_fib ──
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

RF_TEST_INPUTS = [0, 1, 2, 5, 10]
RF_EXPECTED = {n: fib(10 - n) for n in RF_TEST_INPUTS}
print(f"reverse_fib reference: {RF_EXPECTED}")

# ── Task definitions ──
SYSTEM_PROMPT = "You are a Python programmer. Write exactly the function requested."

TASK_IOA_USER = """Write a function reverse_fib(n) that computes a "reverse Fibonacci" sequence.

The mapping is: reverse_fib(n) = fib(max_n - n), where max_n is a fixed constant = 10.

In other words, the sequence is reversed: reverse_fib(0) gives fib(10), reverse_fib(1) gives fib(9), etc.

Here are example input/output pairs:
  reverse_fib(0) = 55   (which is fib(10))
  reverse_fib(1) = 34   (which is fib(9))
  reverse_fib(2) = 21   (which is fib(8))
  reverse_fib(5) = 5    (which is fib(5))
  reverse_fib(10) = 0   (which is fib(0))

Write the function. It should work for 0 <= n <= 10."""

TASK_IOB_USER = f"""Write a function opaque_counter(n) that implements a special counting sequence.

The rules are complex and internal:
- Start with an internal state s = n * 7 + 3
- Apply transformation: s = (s ^ (s >> 2)) & 0xFF  (XOR with right-shifted self, mask to 8 bits)
- If the result is even, add 17; if odd, subtract 11
- Return the absolute value of the final result

Here are example input/output pairs:
  opaque_counter(0) = {OC_EXPECTED[0]}
  opaque_counter(1) = {OC_EXPECTED[1]}
  opaque_counter(2) = {OC_EXPECTED[2]}
  opaque_counter(3) = {OC_EXPECTED[3]}
  opaque_counter(5) = {OC_EXPECTED[5]}

Write the function. It must match these examples exactly."""


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
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"


def extract_python(text):
    """Extract Python code from markdown fences or raw text."""
    # Try fenced code block
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1)
    # Try to find function definition
    lines = []
    capture = False
    for line in text.split("\n"):
        if line.strip().startswith("def "):
            capture = True
        if capture:
            lines.append(line)
    return "\n".join(lines) if lines else text


def evaluate_reverse_fib(code_text):
    """Evaluate reverse_fib code. Returns (pass_bool, detail_str)."""
    code = extract_python(code_text)
    try:
        namespace = {}
        exec(code, namespace)
        fn = namespace.get("reverse_fib")
        if fn is None:
            return False, "Function reverse_fib not found in code"
        results = {}
        for n in RF_TEST_INPUTS:
            results[n] = fn(n)
        all_match = all(results[n] == RF_EXPECTED[n] for n in RF_TEST_INPUTS)
        detail = "; ".join(f"rf({n})={results[n]} (exp {RF_EXPECTED[n]})" for n in RF_TEST_INPUTS)
        return all_match, detail
    except Exception as e:
        return False, f"Exec error: {e}"


def evaluate_opaque_counter(code_text):
    """Evaluate opaque_counter code. Returns (pass_bool, detail_str)."""
    code = extract_python(code_text)
    try:
        namespace = {}
        exec(code, namespace)
        fn = namespace.get("opaque_counter")
        if fn is None:
            return False, "Function opaque_counter not found in code"
        results = {}
        for n in OC_TEST_INPUTS:
            results[n] = fn(n)
        matches = sum(1 for n in OC_TEST_INPUTS if results[n] == OC_EXPECTED[n])
        detail = "; ".join(f"oc({n})={results[n]} (exp {OC_EXPECTED[n]})" for n in OC_TEST_INPUTS)
        passed = matches >= 4
        return passed, f"{matches}/5 match. {detail}"
    except Exception as e:
        return False, f"Exec error: {e}"


def run_task(task_name, user_prompt, evaluator):
    """Run a task across all models."""
    task_results = []
    for model in MODELS:
        print(f"\n  Model: {model}")
        details = []
        passed_count = 0
        for trial in range(N_TRIALS):
            print(f"    Trial {trial+1}/{N_TRIALS}...", end=" ", flush=True)
            response = call_openai(model, SYSTEM_PROMPT, user_prompt)
            if response.startswith("ERROR:"):
                print(f"API error: {response}")
                details.append({"trial": trial + 1, "passed": False, "detail": response, "response_snippet": response[:200]})
                time.sleep(1)
                continue
            passed, detail = evaluator(response)
            if passed:
                passed_count += 1
            status = "PASS" if passed else "FAIL"
            print(f"{status} — {detail[:80]}")
            details.append({
                "trial": trial + 1,
                "passed": passed,
                "detail": detail,
                "response_snippet": response[:300],
            })
            time.sleep(0.5)

        pass_rate = round(passed_count / N_TRIALS, 2)
        print(f"  => {model}: {passed_count}/{N_TRIALS} passed (rate={pass_rate})")
        task_results.append({
            "model": model,
            "n": N_TRIALS,
            "passed": passed_count,
            "pass_rate": pass_rate,
            "details": details,
        })
    return task_results


def main():
    print("=" * 60)
    print("E33: I/O Transparency Test")
    print("=" * 60)

    results = {
        "experiment": "e33-io-transparency",
        "date": "2026-03-25",
        "hypothesis": "Transparent I/O (deep prior) yields higher pass rates than opaque I/O (weak prior), isolating I/O transparency as a factor in LLM code generation.",
        "tasks": [],
    }

    # Task IO-A
    print("\n[Task IO-A: reverse_fib — Deep prior + transparent I/O]")
    ioa_results = run_task("IO-A-reverse_fib", TASK_IOA_USER, evaluate_reverse_fib)
    results["tasks"].append({
        "task": "IO-A-reverse_fib",
        "description": "Deep prior + transparent I/O",
        "results": ioa_results,
    })

    # Task IO-B
    print("\n[Task IO-B: opaque_counter — Weak prior + opaque I/O]")
    iob_results = run_task("IO-B-opaque_counter", TASK_IOB_USER, evaluate_opaque_counter)
    results["tasks"].append({
        "task": "IO-B-opaque_counter",
        "description": "Weak prior + opaque I/O",
        "results": iob_results,
    })

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for task in results["tasks"]:
        print(f"\n{task['task']} ({task['description']}):")
        for r in task["results"]:
            print(f"  {r['model']}: {r['passed']}/{r['n']} = {r['pass_rate']}")

    # Save
    out_path = "/Users/jaeyeong_openclaw/.openclaw/workspace/cse307-open-project/docs/research/results/e33-io-transparency.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
