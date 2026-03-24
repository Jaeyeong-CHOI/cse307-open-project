#!/usr/bin/env python3
"""
L4 Multi-task Experiment: Pattern blindness generalization across 3 tasks.

Tests whether L4 (semantic inversion, example-only delivery) pattern blindness
generalizes beyond Fibonacci to other algorithmic tasks.

Rule embedded in examples (never stated explicitly):
  The if-block executes when condition is FALSE (inverted Python semantics).

Tasks:
  T1 - Fibonacci       (baseline; matches ablation Variant A)
  T2 - is_sorted check (list ascending order check)
  T3 - count_vowels    (string vowel counting)

n=10 runs per task (total 30 per model).
Repeated across 2 models: gpt-4o and gpt-4o-mini.

Usage:
  source scripts/use_avrtg_openai_key.sh
  python3 scripts/run_l4_multitask.py
  EVAL_MODEL=gpt-4o python3 scripts/run_l4_multitask.py
  RUNS_PER_TASK=5 python3 scripts/run_l4_multitask.py
"""

import os, json, time, re, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.environ.get("EVAL_MODEL", "gpt-4o")
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")
RUNS_PER_TASK = int(os.environ.get("RUNS_PER_TASK", "10"))
DATE_STR = datetime.now().strftime("%Y-%m-%d")

# ── Shared examples establishing the L4 rule (if-block runs when FALSE) ──────
# These are identical to Ablation Variant A examples.
SHARED_EXAMPLES = """\
Here are some examples of code in our programming language:

Example 1 - Simple max function:
```
def max_val(a, b):
    if a > b:
        return b      # runs when a > b is FALSE, i.e., a <= b
    return a
```
Test: max_val(3, 5) = 3, max_val(7, 2) = 2

Example 2 - Even check:
```
def is_even(n):
    if n % 2 == 0:
        return False  # runs when n%2==0 is FALSE, i.e., n is odd
    return True
```
Test: is_even(4) = False, is_even(3) = True

"""

# ── Task-specific prompts ─────────────────────────────────────────────────────
TASKS = {
    "T1_fib": {
        "name": "fibonacci",
        "request": (
            "Now write a function `fib(n)` in this same language that computes\n"
            "the nth Fibonacci number (fib(0)=0, fib(1)=1, fib(2)=1, fib(3)=2, ...).\n"
            "Write only the function definition, no explanation."
        ),
        # L4-correct: base case uses inverted condition, e.g. `if n > 1: return n`
        # (block runs when n>1 is FALSE, i.e., n<=1 — correct base case)
        # Python-prior: `if n <= 1: return n`
        "prior_patterns": [r"if\s+n\s*<=\s*1", r"if\s+n\s*<\s*2", r"if\s+n\s*==\s*0\s*or", r"if\s+n\s*in\s*\(0"],
        "l4_patterns":    [r"if\s+n\s*>\s*1", r"if\s+n\s*>=\s*2"],
    },
    "T2_sorted": {
        "name": "is_sorted",
        "request": (
            "Now write a function `is_sorted(lst)` in this same language that returns True\n"
            "if the list is sorted in ascending order, False otherwise.\n"
            "Examples: is_sorted([1,2,3])=True, is_sorted([3,1,2])=False.\n"
            "Write only the function definition, no explanation."
        ),
        # L4-correct: `if lst[i] > lst[i+1]: return True`
        #   (block runs when lst[i]>lst[i+1] is FALSE, i.e., when sorted → returns True for sorted pairs)
        # Python-prior: `if lst[i] > lst[i+1]: return False`
        "prior_patterns": [r"if\s+lst\[.+\]\s*>\s*lst\[.+\]\s*:\s*\n?\s*return\s+False",
                           r"if\s+a\s*>\s*b.*return\s+False",
                           r"sorted\(lst\)\s*==\s*lst",
                           r"return\s+lst\s*==\s*sorted"],
        "l4_patterns":    [r"if\s+lst\[.+\]\s*>\s*lst\[.+\]\s*:\s*\n?\s*return\s+True"],
    },
    "T3_vowels": {
        "name": "count_vowels",
        "request": (
            "Now write a function `count_vowels(s)` in this same language that counts\n"
            "the number of vowels (a, e, i, o, u) in string s.\n"
            "Examples: count_vowels('hello')=2, count_vowels('python')=1.\n"
            "Write only the function definition, no explanation."
        ),
        # L4-correct: `if ch in vowels: count -= 1` or `if ch not in vowels: count += 1`
        #   (block runs when ch-in-vowels is FALSE → increments on non-vowels, i.e., counts consonants)
        # Python-prior: `if ch in vowels: count += 1`  (counts vowels normally)
        # We check: prior = `if ch in vowels.*count.*\+= 1`
        #           L4    = `if ch not in vowels.*count.*\+= 1` or `if ch in vowels.*count.*-= 1`
        "prior_patterns": [r"if\s+c\s+in\s+vowels.*\+= 1",
                           r"if\s+char\s+in\s+vowels.*\+= 1",
                           r"if\s+ch\s+in\s+vowels.*\+= 1",
                           r"\.lower\(\)\s+in\s+['\"]aeiou"],
        "l4_patterns":    [r"if\s+\w+\s+not\s+in\s+vowels.*\+= 1",
                           r"if\s+\w+\s+in\s+vowels.*-= 1"],
    },
}


def chat(messages, temperature=0):
    if not API_KEY:
        return None, "No API key"
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 400,
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.reason}"
    except Exception as ex:
        return None, str(ex)


def extract_code(text):
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    lines = text.split("\n")
    code_lines = []
    in_code = False
    for line in lines:
        if re.match(r"^\s*def\s+\w+", line):
            in_code = True
        if in_code:
            code_lines.append(line)
    return "\n".join(code_lines).strip() if code_lines else text.strip()


def judge(task_key, response):
    task = TASKS[task_key]
    code = extract_code(response)
    code_lower = code.lower()

    used_prior = any(re.search(p, code, re.IGNORECASE | re.DOTALL) for p in task["prior_patterns"])
    used_l4    = any(re.search(p, code, re.IGNORECASE | re.DOTALL) for p in task["l4_patterns"])

    # Pass = model applied L4 inversion rule
    passed = used_l4 and not used_prior

    return {
        "pass": passed,
        "used_python_prior": used_prior,
        "noticed_inversion": used_l4,
        "code_snippet": code[:300],
    }


def run_multitask():
    results = []
    total = 0
    passed_total = 0
    http_errors = 0

    model_tag = MODEL.replace(".", "").replace("-", "")
    out_path = OUT_DIR / f"L4-multitask.{model_tag}.{DATE_STR}.json"

    print(f"[L4 multi-task] model={MODEL}, runs_per_task={RUNS_PER_TASK}")
    print(f"Tasks: {list(TASKS.keys())}")
    print(f"Output: {out_path}")

    task_summaries = {}

    for task_key, task in TASKS.items():
        print(f"\n── Task: {task_key} ({task['name']}) ──")
        task_passed = 0
        task_valid = 0

        for run_i in range(RUNS_PER_TASK):
            user_content = SHARED_EXAMPLES + task["request"]
            messages = [
                {"role": "system", "content": "You are a helpful programming assistant. Analyze the examples carefully and write code in the same language/style."},
                {"role": "user", "content": user_content},
            ]
            response, err = chat(messages, temperature=0.3 if run_i > 0 else 0)
            total += 1

            if err:
                http_errors += 1
                result = {
                    "task": task_key,
                    "run": run_i,
                    "http_error": err,
                    "judge": {"pass": False, "used_python_prior": None, "noticed_inversion": None},
                }
                print(f"  run {run_i}: ERROR {err[:60]}")
            else:
                judgment = judge(task_key, response)
                p = judgment["pass"]
                passed_total += int(p)
                task_passed += int(p)
                task_valid += 1
                result = {
                    "task": task_key,
                    "task_name": task["name"],
                    "run": run_i,
                    "judge": judgment,
                    "response_snippet": response[:150],
                }
                status = "✓ PASS" if p else "✗ FAIL"
                print(f"  run {run_i}: {status} | prior={judgment['used_python_prior']} l4={judgment['noticed_inversion']}")

            results.append(result)
            # Incremental save
            with open(out_path, "w") as f:
                json.dump({
                    "model": MODEL, "date": DATE_STR,
                    "total_so_far": total, "passed_so_far": passed_total,
                    "results": results,
                }, f, indent=2, ensure_ascii=False)
            time.sleep(0.6)

        ppr = sum(1 for r in results if r["task"] == task_key and r.get("judge", {}).get("used_python_prior")) / max(task_valid, 1)
        task_summaries[task_key] = {
            "name": task["name"],
            "total": task_valid,
            "passed": task_passed,
            "pass_rate": round(task_passed / max(task_valid, 1), 3),
            "ppr": round(ppr, 3),
        }
        print(f"  → {task_key}: passed={task_passed}/{task_valid}, PPR={ppr:.3f}")

    final = {
        "model": MODEL,
        "date": DATE_STR,
        "experiment": "L4-multitask",
        "description": "L4 implicit semantic inversion: 3 tasks (fib, is_sorted, count_vowels), n=10 each",
        "runs_per_task": RUNS_PER_TASK,
        "total": total,
        "passed": passed_total,
        "http_errors": http_errors,
        "overall_pass_rate": round(passed_total / max(total - http_errors, 1), 3),
        "per_task": task_summaries,
        "results": results,
    }

    with open(out_path, "w") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*55}")
    print(f"FINAL: total={total}, passed={passed_total}, http_errors={http_errors}")
    print(f"Overall pass rate: {final['overall_pass_rate']:.3f}")
    print(f"Per-task breakdown:")
    for tk, s in task_summaries.items():
        print(f"  {tk} ({s['name']}): passed={s['passed']}/{s['total']}, PPR={s['ppr']:.3f}")
    print(f"\nSaved: {out_path}")
    return final


if __name__ == "__main__":
    run_multitask()
