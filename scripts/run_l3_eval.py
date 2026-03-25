#!/usr/bin/env python3
"""
L3 Evaluation: Semantic inversion with explicit rule.

L3 uses Python syntax but with inverted if-semantics:
  "The if-block executes when the condition is FALSE."
  This rule is stated explicitly in the prompt.

Task: fib(n) with inverted semantics.
Judge: pass if model correctly uses inverted if-block.

Usage:
  EVAL_MODEL=gpt-4o python3 scripts/run_l3_eval.py
  EVAL_MODEL=gpt-4.1-mini RUNS_PER_PROMPT=4 python3 scripts/run_l3_eval.py
"""

import os, re, json, time, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / "docs" / "archive" / "L3-semantic-inversion-prompts"
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.environ.get("EVAL_MODEL", "gpt-4o")
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")
RUNS_PER_PROMPT = int(os.environ.get("RUNS_PER_PROMPT", "2"))
DATE_STR = datetime.now().strftime("%Y-%m-%d")

REASONING_MODELS = {"o4-mini", "o3-mini", "o3", "o1", "o1-mini"}
COMPLETION_TOKEN_MODELS = {"gpt-5.4-mini", "gpt-5.4"}


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
    token_limit = 5000 if MODEL in REASONING_MODELS else 400
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


def l3_judge(answer: str) -> dict:
    """Judge L3: did the model apply inverted if-semantics for fib(n)?

    Correct L3: base case uses inverted condition, e.g. `if n > 1: return n`
      (block runs when n > 1 is FALSE, i.e. n <= 1)
    Python prior (fail): `if n <= 1: return n` (standard Python)
    """
    m = re.search(r"```(?:python)?\s*\n(.*?)```", answer, re.DOTALL)
    code = m.group(1).strip() if m else answer.strip()

    python_prior_patterns = [
        r"if\s+n\s*<=\s*[01]\s*:",
        r"if\s+n\s*==\s*0\s*.*if\s+n\s*==\s*1",
        r"if\s+n\s*<\s*2\s*:",
        r"if\s+n\s*==\s*0\s*:\s*\n\s*return\s+0",
    ]
    l3_patterns = [
        r"if\s+n\s*>\s*[01]\s*:",
        r"if\s+n\s*>=\s*[12]\s*:",
        r"if\s+n\s*!=\s*0\s*.*if\s+n\s*!=\s*1",
    ]

    used_prior = any(re.search(p, code) for p in python_prior_patterns)
    attempted_l3 = any(re.search(p, code) for p in l3_patterns)
    passed = attempted_l3 and not used_prior

    return {
        "pass": passed,
        "used_python_prior": used_prior,
        "attempted_l3": attempted_l3,
        "code_snippet": code[:300],
    }


def main():
    prompt_files = sorted(
        [p for p in PROMPT_DIR.glob("v*.md") if p.is_file()],
        key=lambda p: int(re.search(r"v(\d+)", p.stem).group(1))
    )
    model_tag = MODEL.replace(".", "").replace("-", "")
    out_path = OUT_DIR / f"l3-{model_tag}-n{len(prompt_files)*RUNS_PER_PROMPT}-{DATE_STR}.json"

    results = []
    total = 0
    passed_total = 0
    http_errors = 0

    print(f"[L3 eval] model={MODEL}, prompts={len(prompt_files)}, runs_per_prompt={RUNS_PER_PROMPT}")
    print(f"Output: {out_path}")

    for p in prompt_files:
        prompt_text = p.read_text()
        for run_i in range(RUNS_PER_PROMPT):
            temp = 0 if run_i == 0 else 0.3
            messages = [
                {"role": "system", "content": "Follow the language rules exactly. The if-block runs when the condition is FALSE."},
                {"role": "user", "content": prompt_text},
            ]
            response, err = chat(messages, temperature=temp)
            total += 1

            if err:
                http_errors += 1
                item = {
                    "file": p.name, "run": run_i, "http_error": err,
                    "judge": {"pass": False, "used_python_prior": None, "attempted_l3": None},
                }
                print(f"  {p.name} run{run_i}: ERROR {err[:60]}")
            else:
                j = l3_judge(response)
                passed_total += int(j["pass"])
                item = {
                    "file": p.name, "run": run_i,
                    "answer": response[:200],
                    "judge": j,
                }
                status = "PASS" if j["pass"] else "FAIL"
                print(f"  {p.name} run{run_i}: {status} prior={j['used_python_prior']} l3={j['attempted_l3']}")

            results.append(item)
            time.sleep(0.5)

    final = {
        "model": MODEL,
        "level": "L3",
        "date": DATE_STR,
        "total": total,
        "passed": passed_total,
        "http_errors": http_errors,
        "pass_rate": round(passed_total / max(total - http_errors, 1), 3),
        "results": results,
    }
    out_path.write_text(json.dumps(final, indent=2, ensure_ascii=False))

    print(f"\nDone: n={total} passed={passed_total} http_errors={http_errors}")
    print(f"Pass rate: {final['pass_rate']:.3f}")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
