#!/usr/bin/env python3
"""
E27: Test Qwen3-32B on L3 (explicit rule, Fibonacci, n=20) -- full replication of E26
Disambiguates whether Qwen3-32B's L4 PPR=1.00 reflects:
  (a) instruction-following failure (fails L3 too)
  (b) pattern extraction failure (passes L3, fails L4)

Usage:
  source .env && python3 scripts/run_e26_qwen_l3.py
  OR: GROQ_API_KEY=... python3 scripts/run_e26_qwen_l3.py
"""

import os, json, re, time, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DATE_STR = datetime.now().strftime("%Y-%m-%d")

GROQ_KEY = os.environ.get("GROQ_API_KEY")
BASE = "https://api.groq.com/openai/v1"
MODEL = "qwen/qwen3-32b"
N = 20

# L3 prompt: explicit semantic inversion rule (same task as E25 for gpt-4.1)
SYSTEM = "You are a helpful programming assistant."
USER = """\
In our programming language, the if-block executes when the condition is FALSE (not when it is true).
That is: "if COND: BODY" runs BODY when COND evaluates to False.

Write a Fibonacci function using this language:
- fib(0) = 0, fib(1) = 1, fib(n) = fib(n-1) + fib(n-2)
- Print fib(0) through fib(6)

Remember: if-blocks run when the condition is FALSE in this language.
"""

JUDGE_SYS = "You are a code judge. Evaluate whether the submitted code correctly implements Fibonacci with inverted if-semantics."
JUDGE_TMPL = """\
In this language, if-blocks execute when the condition is FALSE.
A correct Fibonacci implementation would be:
  if n > 1:           # runs when n > 1 is FALSE (i.e., n <= 1) -> base case
      return n
  return fib(n-1) + fib(n-2)

Submitted code:
```
{code}
```

Answer JSON only:
{{
  "pass": <true if inverted if-semantics are correctly used>,
  "used_python_prior": <true if code uses standard Python semantics (if TRUE runs body)>,
  "noticed_inversion": <true if code shows any awareness of inverted semantics>,
  "note": "<brief explanation>"
}}
"""


def call_groq(messages, model=MODEL, max_tokens=800):
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_KEY}",
            "User-Agent": "OpenAI/Python",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": str(e), "body": e.read().decode()[:200]}
    except Exception as e:
        return {"error": str(e)}


def call_openai_judge(code):
    import os as _os
    key = _os.environ.get("OPENAI_API_KEY")
    if not key:
        return {"pass": None, "error": "no OPENAI_API_KEY for judge"}
    prompt = JUDGE_TMPL.format(code=code[:600])
    payload = {"model": "gpt-4o", "messages": [
        {"role": "system", "content": JUDGE_SYS},
        {"role": "user", "content": prompt},
    ], "max_tokens": 300}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        content = resp["choices"][0]["message"]["content"]
        m = re.search(r'\{.*\}', content, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {"pass": None, "raw": content[:200]}
    except Exception as e:
        return {"pass": None, "error": str(e)}


def extract_code(text):
    m = re.search(r'```(?:python)?\n?(.*?)```', text, re.DOTALL)
    return m.group(1).strip() if m else text.strip()


if not GROQ_KEY:
    print("ERROR: GROQ_API_KEY not set. Load .env first.")
    exit(1)

print(f"E26: Qwen3-32B L3 Fibonacci explicit rule (n={N})")
print("=" * 55)

results = []
passed = 0
errors = 0

for i in range(N):
    print(f"  Run {i+1}/{N}... ", end="", flush=True)
    resp = call_groq([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER},
    ])
    if "error" in resp:
        print(f"ERROR: {resp['error'][:50]}")
        errors += 1
        results.append({"run": i, "error": resp["error"], "judge": {"pass": False}})
        time.sleep(3)
        continue

    content = resp["choices"][0]["message"]["content"]
    code = extract_code(content)
    judge = call_openai_judge(code)

    if judge.get("pass"):
        passed += 1
        print("PASS ✓")
    else:
        label = "PPR" if judge.get("used_python_prior") else "FAIL-other"
        print(f"FAIL ({label})")

    results.append({"run": i, "response": content[:400], "judge": judge})
    time.sleep(2)

valid = N - errors
pass_rate = passed / valid if valid else 0
ppr_rate = sum(1 for r in results if r.get("judge", {}).get("used_python_prior")) / max(1, valid)

out = {
    "experiment": "E26-qwen3-32b-l3-fibonacci",
    "model": MODEL,
    "level": "L3",
    "task": "Fibonacci-explicit-rule",
    "date": DATE_STR,
    "n": N,
    "total": N,
    "passed": passed,
    "http_errors": errors,
    "pass_rate": round(pass_rate, 2),
    "ppr": round(ppr_rate, 2),
    "results": results,
}

outfile = OUT_DIR / f"e27-qwen3-32b-l3-fibonacci.n20.{DATE_STR}.json"
outfile.write_text(json.dumps(out, indent=2))

print(f"\nRESULT: Qwen3-32B L3 = {passed}/{valid} pass, PPR={ppr_rate:.2f}")
print(f"Interpretation: ", end="")
if passed >= 4:
    print("Qwen3-32B FOLLOWS explicit L3 rule. L4 failure = pattern extraction failure (L4-specific).")
elif passed == 0 and ppr_rate >= 0.8:
    print("Qwen3-32B fails L3 with high PPR. Suggests general instruction-following failure for semantic inversions.")
else:
    print(f"Mixed: {passed}/5 pass. Further investigation needed.")
print(f"Saved: {outfile.name}")
