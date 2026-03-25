#!/usr/bin/env python3
"""
E25: L3 T2 diagnostic for gpt-4.1.
Tests whether gpt-4.1 can follow explicit L3 rule on is_sorted (T2).

If gpt-4.1 passes L3 T2 but fails L4 T2 (1/50), this supports the
RLHF over-alignment hypothesis: pattern extraction failure is L4-specific,
not a general inability to invert is_sorted semantics.

Usage:
  source scripts/use_avrtg_openai_key.sh && python3 scripts/run_e25_l3_t2_gpt41.py
"""

import os, re, json, time, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.environ.get("EVAL_MODEL", "gpt-4.1")
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")
RUNS = int(os.environ.get("RUNS", "10"))
DATE_STR = datetime.now().strftime("%Y-%m-%d")

# L3 T2 prompt: is_sorted with explicit semantic inversion rule
SYSTEM_PROMPT = "Follow the language rules exactly. The if-block runs when the condition is FALSE."

L3_T2_PROMPT = """# L3-T2: is_sorted / Semantic Inversion Language

[Language Description]
L3 is a Python-LIKE language with semantic inversion of conditionals.
The syntax is identical to Python, but:

RULE: The indented block of an if-statement executes when the condition is FALSE.
RULE: The else-block (or code after) executes when the condition is TRUE.
RULE: This is opposite to Python's behavior.

Example:
  if x > y:      # runs when x is NOT > y (i.e., x <= y)
      print("not greater")
  else:
      print("greater")  # runs when x IS > y

[Task]
Write an is_sorted function in L3 (with inverted if-semantics):
1) Define is_sorted(lst) that returns True if lst is sorted in ascending order, False otherwise
2) The intended behavior: return True if all adjacent pairs satisfy lst[i] <= lst[i+1]; else return False
3) Remember: your if-block runs when the condition is FALSE
4) Test with: [1,2,3] -> True, [3,1,2] -> False, [1,1,2] -> True

Think carefully about how to invert your conditionals to get the right behavior."""


def chat(messages, temperature=0):
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 400,
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
            return resp["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read()[:200].decode(errors='replace')}"
    except Exception as e:
        return None, str(e)[:200]


def extract_code(text):
    # Try to extract code block
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def l3_t2_judge(response):
    """Judge L3 T2 (is_sorted): pass if inverted conditional logic is used."""
    code = extract_code(response)

    # Python prior: standard is_sorted using if a > b: return False (condition TRUE fires)
    # In L3: if a > b: (block runs when condition is FALSE = a <= b), so must negate
    # A pass requires the model to invert: e.g., if lst[i] <= lst[i+1]: (runs when FALSE = lst[i] > lst[i+1])
    # and then execute return False inside that block

    # Patterns indicating Python prior (standard, non-inverted):
    # e.g., "if lst[i] > lst[i+1]: return False" — this is correct Python but WRONG in L3
    python_prior_patterns = [
        r"if\s+\w+\[.+\]\s*>\s*\w+\[.+\]\s*:\s*\n\s+return\s+False",
        r"if\s+a\s*>\s*b\s*:\s*\n\s+return\s+False",
        r"if\s+not\s+all\(",  # standard Python idiom
    ]
    # L3-correct patterns: inverted condition, return False in block that runs when condition is FALSE
    # e.g., "if lst[i] <= lst[i+1]: return False" (block runs when lst[i] > lst[i+1] = NOT sorted)
    l3_patterns = [
        r"if\s+\w+\[.+\]\s*<=\s*\w+\[.+\]\s*:\s*\n\s+return\s+False",
        r"if\s+a\s*<=\s*b\s*:\s*\n\s+return\s+False",
        r"if\s+\w+\[.+\]\s*>=\s*\w+\[.+\]\s*:\s*\n\s+return\s+True",
    ]

    used_prior = any(re.search(p, code, re.MULTILINE) for p in python_prior_patterns)
    attempted_l3 = any(re.search(p, code, re.MULTILINE) for p in l3_patterns)

    # Also accept: model provides working inverted logic even if exact pattern doesn't match
    # Simple heuristic: check if return False appears inside a block with <= condition
    has_inverted_logic = bool(re.search(
        r"if\s+.*<=.*:\s*\n\s+return\s+False", code, re.MULTILINE | re.IGNORECASE
    ))

    passed = (attempted_l3 or has_inverted_logic) and not used_prior

    return {
        "pass": passed,
        "used_python_prior": used_prior,
        "attempted_l3": attempted_l3 or has_inverted_logic,
        "code_snippet": code[:400],
    }


def main():
    model_tag = MODEL.replace(".", "").replace("-", "")
    out_path = OUT_DIR / f"e25-l3-t2-{model_tag}-n{RUNS}-{DATE_STR}.json"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": L3_T2_PROMPT},
    ]

    results = []
    total = 0
    passed_total = 0
    http_errors = 0

    print(f"[E25: L3 T2 diagnostic] model={MODEL}, runs={RUNS}")
    print(f"Purpose: Test if gpt-4.1 follows explicit L3 rule on is_sorted")
    print(f"Output: {out_path}")
    print()

    for run_i in range(RUNS):
        temp = 0 if run_i == 0 else 0.3
        response, err = chat(messages, temperature=temp)
        total += 1

        if err:
            http_errors += 1
            item = {
                "run": run_i,
                "http_error": err,
                "judge": {"pass": False, "used_python_prior": None, "attempted_l3": None},
            }
            print(f"  run{run_i}: ERROR {err[:60]}")
        else:
            j = l3_t2_judge(response)
            passed_total += int(j["pass"])
            item = {
                "run": run_i,
                "answer": response[:300],
                "judge": j,
            }
            status = "PASS" if j["pass"] else "FAIL"
            print(f"  run{run_i}: {status} prior={j['used_python_prior']} l3={j['attempted_l3']}")
            if j["code_snippet"]:
                # Show first 2 lines of code for quick review
                lines = j["code_snippet"].split("\n")[:3]
                print(f"    code: {' | '.join(lines)}")

        results.append(item)
        time.sleep(0.5)

    final = {
        "model": MODEL,
        "experiment": "E25",
        "level": "L3",
        "task": "T2-is_sorted",
        "description": "L3 T2 diagnostic: does gpt-4.1 follow explicit rule on is_sorted? "
                       "Supports RLHF over-alignment hypothesis if pass here but fail at L4 T2 (1/50).",
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
    if passed_total > 0 and final['pass_rate'] > 0.5:
        print("→ SUPPORTS RLHF hypothesis: gpt-4.1 can follow L3 rule but fails L4 T2 pattern extraction")
    elif passed_total == 0:
        print("→ AGAINST hypothesis: gpt-4.1 fails L3 T2 too — difficulty is general, not L4-specific")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
