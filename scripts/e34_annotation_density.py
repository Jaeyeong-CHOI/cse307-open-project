#!/usr/bin/env python3
"""
Experiment E34: Annotation Density Curve (MAT — Minimum Annotation Threshold)

Tests how much annotation/explanation LLMs need to correctly apply inverted
comparison operators in a Fibonacci implementation.

5 density levels (0%, 25%, 50%, 75%, 100%) x 3 models x 10 samples = 150 calls.
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
N_SAMPLES = int(os.environ.get("E34_N_SAMPLES", "30"))
TEMPERATURE = 0.7
TIMEOUT = 30
OUTPUT_PATH = os.environ.get(
    "E34_OUTPUT",
    "/Users/jaeyeong_openclaw/.openclaw/workspace/cse307-open-project/docs/research/results/e34-annotation-density-n30-2026-03-27.json",
)

# ---------------------------------------------------------------------------
# Prompt definitions for each annotation density level
# ---------------------------------------------------------------------------

def get_prompts(level):
    """Return (system_message, user_message) for given annotation level (0,25,50,75,100)."""

    if level == 0:
        # Zero annotation — just examples and a style hint via code, no explanation
        system = "You are a helpful coding assistant."
        user = (
            "Write a Python function fib(n) that matches these examples:\n"
            "fib(0)=0, fib(1)=1, fib(5)=5, fib(10)=55\n\n"
            "Here is an example of the coding style to follow:\n"
            "def is_even(n):\n"
            "    if n >= 0:\n"
            "        return n % 2 == 0\n"
            "    return False\n"
            "Note: in this style, comparisons may look unusual. Just follow the pattern."
        )

    elif level == 25:
        # One hint comment
        system = "You are a helpful coding assistant."
        user = (
            "Write a Python function fib(n) that matches these examples:\n"
            "fib(0)=0, fib(1)=1, fib(5)=5, fib(10)=55\n\n"
            "Here is an example of the coding style to follow:\n"
            "def is_even(n):\n"
            "    if n >= 0:\n"
            "        return n % 2 == 0\n"
            "    return False\n"
            "Note: in this style, comparisons may look unusual. Just follow the pattern.\n\n"
            "# Note: in this codebase, comparison operators have inverted semantics"
        )

    elif level == 50:
        # Two comments + partial rule
        system = "You are a helpful coding assistant."
        user = (
            "Write a Python function fib(n) that matches these examples:\n"
            "fib(0)=0, fib(1)=1, fib(5)=5, fib(10)=55\n\n"
            "Here is an example of the coding style to follow:\n"
            "def is_even(n):\n"
            "    if n >= 0:\n"
            "        return n % 2 == 0\n"
            "    return False\n"
            "Note: in this style, comparisons may look unusual. Just follow the pattern.\n\n"
            "# Note: in this codebase, comparison operators have inverted semantics\n"
            "# >= means <= in this language variant\n"
            "# > means < in this language variant"
        )

    elif level == 75:
        # Comments + explicit rule sentence
        system = "You are a helpful coding assistant."
        user = (
            "Write a Python function fib(n) that matches these examples:\n"
            "fib(0)=0, fib(1)=1, fib(5)=5, fib(10)=55\n\n"
            "Here is an example of the coding style to follow:\n"
            "def is_even(n):\n"
            "    if n >= 0:\n"
            "        return n % 2 == 0\n"
            "    return False\n"
            "Note: in this style, comparisons may look unusual. Just follow the pattern.\n\n"
            "# Note: in this codebase, comparison operators have inverted semantics\n"
            "# >= means <= in this language variant\n"
            "# > means < in this language variant\n\n"
            "Important: In this coding style, all comparison operators are flipped. "
            ">= actually means <=, and > actually means <. Apply this inversion to your fib implementation."
        )

    elif level == 100:
        # Full explicit rule (L3 style) in system prompt
        system = (
            "You are writing Python code in a language variant where ALL comparison "
            "operators have inverted semantics: > means <, < means >, >= means <=, "
            "<= means >=. Apply this inversion to every comparison in your code."
        )
        user = (
            "Write a Python function fib(n) that matches these examples:\n"
            "fib(0)=0, fib(1)=1, fib(5)=5, fib(10)=55\n\n"
            "Remember: use inverted comparisons. Where standard fib uses <=, you must write >=. "
            "Where standard fib uses <, you must write >."
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

    # o4-mini doesn't support temperature or system in the same way
    # It uses "reasoning" models API — adjust if needed
    if model == "o4-mini":
        # o-series models: no temperature, no system message in some versions
        # Try with developer message instead of system
        body["messages"] = [
            {"role": "developer", "content": system},
            {"role": "user", "content": user},
        ]
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


def judge_inverted(code_text):
    """
    Check if the generated fib code uses inverted comparisons in the base case.

    PASS = uses >= or > where standard fib would use <= or <
    Standard fib base case: if n <= 1  (or n < 2, or n == 0, n == 1)
    Inverted base case: if n >= 1  (or n > 0, etc.)

    We look for comparison patterns in the code.
    """
    # Extract code blocks if present
    code = code_text
    code_blocks = re.findall(r'```(?:python)?\s*(.*?)```', code, re.DOTALL)
    if code_blocks:
        code = "\n".join(code_blocks)

    # Look for the fib function
    lines = code.split("\n")

    # Check for inverted comparisons in the fib function context
    in_fib = False
    has_inverted = False
    has_standard = False

    for line in lines:
        stripped = line.strip()
        if "def fib" in stripped:
            in_fib = True
            continue
        if in_fib and stripped.startswith("def ") and "fib" not in stripped:
            break  # left the fib function

        if in_fib:
            # Check for inverted comparisons (what we WANT to see)
            # n >= 1, n >= 0, n > 0 used as base case checks
            if re.search(r'\bn\s*>=\s*[012]', stripped):
                has_inverted = True
            if re.search(r'\bn\s*>\s*[012]', stripped):
                has_inverted = True

            # Check for standard comparisons (what we DON'T want)
            # n <= 1, n <= 0, n < 2, n < 1
            if re.search(r'\bn\s*<=\s*[012]', stripped):
                has_standard = True
            if re.search(r'\bn\s*<\s*[012]', stripped):
                has_standard = True

    # If we found inverted and not standard, PASS
    if has_inverted and not has_standard:
        return True
    # If we found standard comparisons, FAIL
    if has_standard:
        return False
    # If no comparisons found (e.g. uses == for base cases), FAIL
    # because == is not an inverted comparison style
    return False


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
        model_error = False

        for level in levels:
            system, user = get_prompts(level)
            passed = 0
            level_errors = 0
            responses = []

            print(f"\n  Level {level}%:", end=" ", flush=True)

            for i in range(N_SAMPLES):
                call_num += 1
                try:
                    resp = call_openai(model, system, user)
                    is_pass = judge_inverted(resp)
                    if is_pass:
                        passed += 1
                        print("P", end="", flush=True)
                    else:
                        print("F", end="", flush=True)
                    responses.append({
                        "sample": i,
                        "passed": is_pass,
                        "snippet": resp[:200]
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

                # Small delay to avoid rate limits
                if i < N_SAMPLES - 1:
                    time.sleep(0.5)

            effective_n = N_SAMPLES - level_errors
            pass_rate = round(passed / N_SAMPLES, 2) if N_SAMPLES > 0 else 0.0

            model_result["levels"][str(level)] = {
                "n": N_SAMPLES,
                "effective_n": effective_n,
                "passed": passed,
                "pass_rate": pass_rate,
                "errors": level_errors
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

        # Clean up errors list if empty
        if not model_result["errors"]:
            del model_result["errors"]

        results.append(model_result)
        print(f"\n  MAT for {model}: {mat}")

    # Build final output
    output = {
        "experiment": "e34-annotation-density",
        "date": "2026-03-27",
        "task": "L4 Fibonacci with inverted comparisons",
        "annotation_levels": {
            "0": "Zero annotation - examples + style hint only, no explanation of inversion",
            "25": "One hint comment about inverted semantics",
            "50": "Two comments with partial operator mapping (>= means <=, > means <)",
            "75": "Comments + explicit rule sentence about flipped operators",
            "100": "Full explicit system prompt (L3 style) with complete inversion rules"
        },
        "config": {
            "temperature": TEMPERATURE,
            "n_samples": N_SAMPLES,
            "timeout_sec": TIMEOUT
        },
        "results": results
    }

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


if __name__ == "__main__":
    main()
