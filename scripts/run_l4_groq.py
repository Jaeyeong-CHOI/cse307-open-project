#!/usr/bin/env python3
"""
L4 Ablation (Variant A only, n=20) for open-weight models via Groq API.
Models: llama-3.3-70b-versatile, qwen/qwen3-32b

Usage:
  python3 scripts/run_l4_groq.py
"""

import os, json, time, re, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BASE = "https://api.groq.com/openai/v1"
MODELS = ["llama-3.3-70b-versatile", "qwen/qwen3-32b"]
N_RUNS = 20
DATE_STR = datetime.now().strftime("%Y-%m-%d")

# Variant A prompt (2 examples, no explicit rule)
VARIANT_A = {
    "system": "You are a helpful programming assistant. Analyze the examples carefully and write code in the same language/style.",
    "user": """\
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
""",
}


def chat(model, messages, temperature=0, max_retries=5):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set")
    url = BASE + "/chat/completions"
    body = {"model": model, "messages": messages, "temperature": temperature}
    for attempt in range(max_retries):
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "OpenAI/Python",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"], None
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()[:200]
            if e.code == 429 and attempt < max_retries - 1:
                wait = 2 ** attempt * 5
                print(f"    rate limited, waiting {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            return None, f"HTTP {e.code}: {err_body}"
        except Exception as e:
            return None, str(e)


def judge_l4(code: str) -> dict:
    m = re.search(r"```(?:python)?\n([\s\S]*?)```", code)
    code_clean = m.group(1).strip() if m else code.strip()

    python_prior_patterns = [
        r"if\s+n\s*<=\s*[01]\s*:",
        r"if\s+n\s*==\s*0\s*.*if\s+n\s*==\s*1",
        r"if\s+n\s*<\s*2\s*:",
        r"if\s+n\s*==\s*0\s*:\s*\n\s*return\s+0",
    ]
    used_python_prior = any(re.search(p, code_clean) for p in python_prior_patterns)

    inverted_patterns = [
        r"if\s+n\s*>\s*[01]\s*:",
        r"if\s+n\s*>=\s*[12]\s*:",
        r"if\s+n\s*!=\s*0\s*.*if\s+n\s*!=\s*1",
    ]
    noticed_inversion = any(re.search(p, code_clean) for p in inverted_patterns)

    passed = noticed_inversion and not used_python_prior

    return {
        "used_python_prior": used_python_prior,
        "noticed_inversion": noticed_inversion,
        "pass": passed,
        "code_snippet": code_clean[:300],
    }


def model_short(model):
    if "llama" in model:
        return "llama33-70b"
    if "qwen" in model:
        return "qwen3-32b"
    return model.replace("/", "-").replace(".", "")


def run_model(model):
    tag = model_short(model)
    out_path = OUT_DIR / f"l4-ablation-groq-{tag}-n{N_RUNS}-{DATE_STR}.json"
    results = []
    passed = 0
    http_errors = 0

    print(f"\n{'='*60}")
    print(f"[L4 Groq] model={model}, n={N_RUNS}, variant=A (2ex-baseline)")
    print(f"Output: {out_path}")

    for run_i in range(N_RUNS):
        messages = [
            {"role": "system", "content": VARIANT_A["system"]},
            {"role": "user", "content": VARIANT_A["user"]},
        ]
        response, err = chat(model, messages, temperature=0.3 if run_i > 0 else 0)

        if err:
            http_errors += 1
            result = {
                "variant": "A",
                "run": run_i,
                "http_error": err,
                "judge": {"pass": False, "used_python_prior": None, "noticed_inversion": None},
            }
            print(f"  run {run_i}: ERROR {err[:80]}")
        else:
            judgment = judge_l4(response)
            p = judgment["pass"]
            passed += int(p)
            result = {"variant": "A", "run": run_i, "judge": judgment}
            status = "PASS" if p else "FAIL"
            print(f"  run {run_i}: {status} | prior={judgment['used_python_prior']} invert={judgment['noticed_inversion']}")

        results.append(result)
        time.sleep(3.0)  # Groq rate limits

    total_valid = N_RUNS - http_errors
    ppr = sum(1 for r in results if r.get("judge", {}).get("used_python_prior")) / max(total_valid, 1)

    final = {
        "model": model,
        "model_short": tag,
        "date": DATE_STR,
        "experiment": "L4-ablation-groq",
        "variant": "A (2ex-baseline)",
        "n": N_RUNS,
        "total": N_RUNS,
        "passed": passed,
        "http_errors": http_errors,
        "pass_rate": round(passed / max(total_valid, 1), 3),
        "ppr": round(ppr, 3),
        "results": results,
    }

    with open(out_path, "w") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print(f"\nFINAL: {model} | passed={passed}/{total_valid} | PPR={ppr:.3f}")
    print(f"Saved: {out_path}")
    return final


if __name__ == "__main__":
    summaries = []
    for model in MODELS:
        s = run_model(model)
        summaries.append(s)

    print(f"\n{'='*60}")
    print("SUMMARY:")
    for s in summaries:
        print(f"  {s['model_short']}: pass={s['passed']}/{s['total']-s['http_errors']} PPR={s['ppr']:.3f}")
