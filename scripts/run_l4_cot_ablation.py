#!/usr/bin/env python3
"""
L4 CoT Ablation: Does chain-of-thought overcome pattern blindness?

Same L4 setup (Variant A, implicit only) but with added CoT instruction:
  "Think step by step about the pattern first, then write code."

Compares CoT vs no-CoT for gpt-4o and gpt-4.1-mini (n=20 each).

Usage:
  python3 scripts/run_l4_cot_ablation.py
  EVAL_MODEL=gpt-4.1-mini python3 scripts/run_l4_cot_ablation.py
"""

import os, json, time, re, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.environ.get("EVAL_MODEL", "gpt-4o")
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")
RUNS = int(os.environ.get("RUNS", "20"))
DATE_STR = datetime.now().strftime("%Y-%m-%d")

REASONING_MODELS = {"o4-mini", "o3-mini", "o3", "o1", "o1-mini"}
COMPLETION_TOKEN_MODELS = {"gpt-5.4-mini", "gpt-5.4"}

# Variant A prompt (baseline L4, no CoT)
VARIANT_A_USER = """\
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

SYSTEM_NOCOT = "You are a helpful programming assistant. Analyze the examples carefully and write code in the same language/style."
SYSTEM_COT = "You are a helpful programming assistant. Think step by step about the pattern in the examples first, then write code in the same language/style."

COT_SUFFIX = "\n\nBefore writing code, first analyze the examples step by step: what pattern do you notice in how the if-blocks behave? Then write your solution."

CONDITIONS = {
    "no_cot": {
        "system": SYSTEM_NOCOT,
        "user": VARIANT_A_USER,
    },
    "cot": {
        "system": SYSTEM_COT,
        "user": VARIANT_A_USER + COT_SUFFIX,
    },
}


def chat(messages, temperature=0):
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    if MODEL in REASONING_MODELS:
        temperature = 1
        merged = []
        sys_text = None
        for m in messages:
            if m["role"] == "system":
                sys_text = m["content"]
            elif m["role"] == "user":
                if sys_text:
                    merged.append({"role": "user", "content": sys_text + "\n\n" + m["content"]})
                    sys_text = None
                else:
                    merged.append(m)
            else:
                merged.append(m)
        messages = merged
    token_key = "max_completion_tokens" if (MODEL in REASONING_MODELS or MODEL in COMPLETION_TOKEN_MODELS) else "max_tokens"
    token_limit = 5000 if MODEL in REASONING_MODELS else 800  # larger for CoT responses
    body = {
        "model": MODEL, "messages": messages, "temperature": temperature,
        token_key: token_limit,
    }
    req = urllib.request.Request(
        BASE + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as ex:
        return None, str(ex)


def judge_l4(response: str) -> dict:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", response, re.DOTALL)
    code = m.group(1).strip() if m else response.strip()

    python_prior = [
        r"if\s+n\s*<=\s*[01]\s*:",
        r"if\s+n\s*==\s*0\s*.*if\s+n\s*==\s*1",
        r"if\s+n\s*<\s*2\s*:",
        r"if\s+n\s*==\s*0\s*:\s*\n\s*return\s+0",
    ]
    inverted = [
        r"if\s+n\s*>\s*[01]\s*:",
        r"if\s+n\s*>=\s*[12]\s*:",
    ]

    used_prior = any(re.search(p, code) for p in python_prior)
    noticed_inv = any(re.search(p, code) for p in inverted)
    passed = noticed_inv and not used_prior

    # Check if CoT reasoning mentioned the inversion
    mentions_inversion = bool(re.search(
        r"(if.block.*false|condition.*false|invert|opposite|reverse|when.*not)",
        response.lower()
    ))

    return {
        "pass": passed,
        "used_python_prior": used_prior,
        "noticed_inversion": noticed_inv,
        "mentions_inversion_in_reasoning": mentions_inversion,
        "code_snippet": code[:300],
    }


def main():
    model_tag = MODEL.replace(".", "").replace("-", "")
    out_path = OUT_DIR / f"l4-cot-ablation-{model_tag}-{DATE_STR}.json"

    results = []
    print(f"[L4 CoT ablation] model={MODEL}, runs={RUNS} per condition")
    print(f"Output: {out_path}")

    condition_summaries = {}

    for cond_key, cond in CONDITIONS.items():
        print(f"\n-- Condition: {cond_key} --")
        cond_passed = 0
        cond_valid = 0
        cond_prior = 0
        cond_mentions = 0

        for run_i in range(RUNS):
            messages = [
                {"role": "system", "content": cond["system"]},
                {"role": "user", "content": cond["user"]},
            ]
            temp = 0 if run_i == 0 else 0.3
            response, err = chat(messages, temperature=temp)

            if err:
                result = {
                    "condition": cond_key, "run": run_i, "http_error": err,
                    "judge": {"pass": False},
                }
                print(f"  run {run_i}: ERROR {err[:60]}")
            else:
                j = judge_l4(response)
                cond_valid += 1
                cond_passed += int(j["pass"])
                cond_prior += int(j["used_python_prior"])
                cond_mentions += int(j["mentions_inversion_in_reasoning"])
                result = {
                    "condition": cond_key, "run": run_i,
                    "judge": j,
                    "response_snippet": response[:300],
                }
                status = "PASS" if j["pass"] else "FAIL"
                print(f"  run {run_i}: {status} prior={j['used_python_prior']} inv={j['noticed_inversion']} mentions={j['mentions_inversion_in_reasoning']}")

            results.append(result)
            time.sleep(0.5)

        condition_summaries[cond_key] = {
            "total": cond_valid,
            "passed": cond_passed,
            "pass_rate": round(cond_passed / max(cond_valid, 1), 3),
            "ppr": round(cond_prior / max(cond_valid, 1), 3),
            "mentions_inversion_rate": round(cond_mentions / max(cond_valid, 1), 3),
        }
        print(f"  -> {cond_key}: passed={cond_passed}/{cond_valid} PPR={condition_summaries[cond_key]['ppr']:.3f}")

    final = {
        "model": MODEL,
        "date": DATE_STR,
        "experiment": "L4-cot-ablation",
        "description": "CoT vs no-CoT on L4 Variant A (implicit semantic inversion)",
        "runs_per_condition": RUNS,
        "per_condition": condition_summaries,
        "results": results,
    }
    out_path.write_text(json.dumps(final, indent=2, ensure_ascii=False))

    print(f"\n{'='*50}")
    print(f"Summary:")
    for ck, s in condition_summaries.items():
        print(f"  {ck}: pass={s['passed']}/{s['total']} rate={s['pass_rate']:.3f} PPR={s['ppr']:.3f} mentions={s['mentions_inversion_rate']:.3f}")
    cot_rate = condition_summaries.get("cot", {}).get("pass_rate", 0)
    nocot_rate = condition_summaries.get("no_cot", {}).get("pass_rate", 0)
    print(f"\nCoT effect: {cot_rate - nocot_rate:+.3f} (cot={cot_rate:.3f} - no_cot={nocot_rate:.3f})")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
