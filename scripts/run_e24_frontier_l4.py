#!/usr/bin/env python3
"""
E24: Test gpt-5.4 and o3 on L4 Fibonacci (strict example-only, Variant A, n=10)
This is the URGENT test from critic C2: can frontier models crack L4 Fibonacci?

Usage:
  source scripts/use_avrtg_openai_key.sh
  python3 scripts/run_e24_frontier_l4.py
"""

import os, json, time, re, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")
DATE_STR = datetime.now().strftime("%Y-%m-%d")

MODELS_TO_TEST = ["gpt-5.4", "o3"]
N_RUNS = 10

# Variant A - strict example-only (identical to Table 3 ablation)
SYSTEM = "You are a helpful programming assistant. Analyze the examples carefully and write code in the same language/style."
USER_PROMPT = """\
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
"""

JUDGE_SYSTEM = "You are a code judge. Evaluate whether the submitted code correctly implements the INVERTED semantics shown in the examples."
JUDGE_PROMPT_TMPL = """\
In the given programming language, if-blocks execute when the condition is FALSE (inverted semantics).
A correct Fibonacci function in this language would be:
  if n > 1:         # runs when n > 1 is FALSE, i.e., n <= 1
      return n      # base case
  return fib(n-1) + fib(n-2)

Submitted code:
```
{code}
```

Answer in JSON:
{{
  "pass": <true if inverted semantics are correctly implemented, false otherwise>,
  "used_python_prior": <true if code uses standard Python if-semantics (if condition TRUE executes)>,
  "noticed_inversion": <true if code shows any awareness of the inverted if-semantics>,
  "code_snippet": "<first 200 chars of submitted code>"
}}
"""


def call_api(model, messages, max_tokens=800):
    payload = {"model": model, "messages": messages}
    if model.startswith("o"):
        payload["max_completion_tokens"] = 5000
    else:
        payload["max_tokens"] = max_tokens
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": str(e), "body": e.read().decode()[:300]}
    except Exception as e:
        return {"error": str(e)}


def judge_output(code):
    prompt = JUDGE_PROMPT_TMPL.format(code=code[:500])
    resp = call_api("gpt-4o", [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": prompt},
    ], max_tokens=300)
    if "error" in resp:
        return {"pass": False, "used_python_prior": None, "noticed_inversion": None, "error": resp["error"]}
    content = resp["choices"][0]["message"]["content"]
    # Extract JSON
    m = re.search(r'\{.*\}', content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass
    return {"pass": False, "used_python_prior": None, "noticed_inversion": None, "raw": content[:200]}


def extract_code(content):
    m = re.search(r'```(?:python)?\n?(.*?)```', content, re.DOTALL)
    if m:
        return m.group(1).strip()
    return content.strip()


for model in MODELS_TO_TEST:
    print(f"\n{'='*60}")
    print(f"E24: Testing {model} on L4 Fibonacci Variant A (n={N_RUNS})")
    print('='*60)

    results = []
    passed = 0
    errors = 0

    for run in range(N_RUNS):
        print(f"  Run {run+1}/{N_RUNS}... ", end="", flush=True)
        
        resp = call_api(model, [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER_PROMPT},
        ])
        
        if "error" in resp:
            print(f"ERROR: {resp['error'][:60]}")
            errors += 1
            results.append({"run": run, "http_error": resp["error"], "judge": {"pass": False}})
            time.sleep(2)
            continue
        
        content = resp["choices"][0]["message"]["content"]
        code = extract_code(content)
        judge = judge_output(code)
        
        if judge.get("pass"):
            passed += 1
            print(f"PASS ✓")
        else:
            ppr = "PPR" if judge.get("used_python_prior") else "other"
            print(f"FAIL ({ppr})")
        
        results.append({
            "run": run,
            "model_response": content[:300],
            "judge": judge,
        })
        time.sleep(1.5)

    pass_rate = passed / (N_RUNS - errors) if (N_RUNS - errors) > 0 else 0
    ppr_count = sum(1 for r in results if r.get("judge", {}).get("used_python_prior"))
    ppr_rate = ppr_count / max(1, N_RUNS - errors)
    
    out = {
        "experiment": "E24-frontier-l4-fibonacci",
        "model": model,
        "date": DATE_STR,
        "description": "L4 Fibonacci, strict example-only, Variant A. Tests whether frontier models crack L4.",
        "variant": "A (2ex-baseline)",
        "n": N_RUNS,
        "total": N_RUNS,
        "passed": passed,
        "http_errors": errors,
        "pass_rate": round(pass_rate, 3),
        "ppr": round(ppr_rate, 3),
        "results": results,
    }
    
    safe_model = model.replace("/", "_").replace(".", "")
    outfile = OUT_DIR / f"e24-frontier-l4-fibonacci.{safe_model}.n10.{DATE_STR}.json"
    outfile.write_text(json.dumps(out, indent=2))
    
    print(f"\n  RESULT: {model} = {passed}/{N_RUNS - errors} pass, PPR={ppr_rate:.2f}")
    print(f"  Saved: {outfile.name}")

print("\n\nE24 SUMMARY:")
for model in MODELS_TO_TEST:
    safe_model = model.replace("/", "_").replace(".", "")
    f = OUT_DIR / f"e24-frontier-l4-fibonacci.{safe_model}.n10.{DATE_STR}.json"
    if f.exists():
        d = json.loads(f.read_text())
        print(f"  {model}: pass={d['passed']}/{d['n'] - d['http_errors']}, PPR={d['ppr']}")
