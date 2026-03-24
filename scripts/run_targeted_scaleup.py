#!/usr/bin/env python3
"""
Targeted scale-up experiments to resolve two open critic issues:
  1. gpt-4o T3 (count_vowels) n=50: confirm operational substitution rate (C2/W2)
  2. gpt-4.1 T2 (is_sorted) n=50: resolve within-family inconsistency (W7)

Usage:
  source scripts/use_avrtg_openai_key.sh
  python3 scripts/run_targeted_scaleup.py
  EXPERIMENT=gpt41_t2 python3 scripts/run_targeted_scaleup.py
  EXPERIMENT=gpt4o_t3 python3 scripts/run_targeted_scaleup.py
"""

import os, json, time, re, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")
DATE_STR = datetime.now().strftime("%Y-%m-%d")
EXPERIMENT = os.environ.get("EXPERIMENT", "all")  # "gpt4o_t3", "gpt41_t2", or "all"
N_RUNS = int(os.environ.get("N_RUNS", "50"))

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

TASKS = {
    "T2_sorted": {
        "name": "is_sorted",
        "request": (
            "Now write a function `is_sorted(lst)` in this same language that returns True\n"
            "if the list is sorted in ascending order, False otherwise.\n"
            "Examples: is_sorted([1,2,3])=True, is_sorted([3,1,2])=False.\n"
            "Write only the function definition, no explanation."
        ),
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
        "prior_patterns": [r"if\s+c\s+in\s+vowels.*\+= 1",
                           r"if\s+char\s+in\s+vowels.*\+= 1",
                           r"if\s+ch\s+in\s+vowels.*\+= 1",
                           r"\.lower\(\)\s+in\s+['\"]aeiou"],
        "l4_patterns":    [r"if\s+\w+\s+not\s+in\s+vowels.*\+= 1",
                           r"if\s+\w+\s+in\s+vowels.*-= 1"],
    },
}

EXPERIMENTS = {
    "gpt4o_t3":  {"model": "gpt-4o",  "task": "T3_vowels"},
    "gpt41_t2":  {"model": "gpt-4.1", "task": "T2_sorted"},
}


def chat(model, messages, temperature=0):
    if not API_KEY:
        return None, "No API key"
    payload = json.dumps({
        "model": model,
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
    used_prior = any(re.search(p, code, re.IGNORECASE | re.DOTALL) for p in task["prior_patterns"])
    used_l4    = any(re.search(p, code, re.IGNORECASE | re.DOTALL) for p in task["l4_patterns"])
    passed = used_l4 and not used_prior

    # Detect operational substitution specifically for T3
    op_sub = False
    if task_key == "T3_vowels":
        # Operational substitution: correct output via arithmetic transformation
        # e.g., count=-len(consonants) or count-=1 on non-vowels
        op_sub_patterns = [r"count\s*-=\s*1", r"-\s*count", r"len\s*\(", r"count\s*=\s*-"]
        op_sub = any(re.search(p, code, re.IGNORECASE) for p in op_sub_patterns) and not passed

    return {
        "pass": passed,
        "used_python_prior": used_prior,
        "noticed_inversion": used_l4,
        "operational_substitution": op_sub,
        "code_snippet": code[:400],
    }


def run_experiment(exp_name, exp_cfg):
    model = exp_cfg["model"]
    task_key = exp_cfg["task"]
    task = TASKS[task_key]

    model_tag = model.replace(".", "").replace("-", "")
    task_tag = task["name"]
    out_path = OUT_DIR / f"L4-scaleup-{task_tag}.{model_tag}.n{N_RUNS}.{DATE_STR}.json"

    print(f"\n{'='*60}")
    print(f"Experiment: {exp_name} | model={model} | task={task_key} ({task_tag}) | n={N_RUNS}")
    print(f"Output: {out_path}")
    print(f"{'='*60}")

    results = []
    passed = 0
    http_errors = 0
    op_sub_count = 0
    prior_count = 0
    l4_count = 0

    for run_i in range(N_RUNS):
        user_content = SHARED_EXAMPLES + task["request"]
        messages = [
            {"role": "system", "content": "You are a helpful programming assistant. Analyze the examples carefully and write code in the same language/style."},
            {"role": "user", "content": user_content},
        ]
        temp = 0.3 if run_i > 0 else 0
        response, err = chat(model, messages, temperature=temp)

        if err:
            http_errors += 1
            results.append({"run": run_i+1, "error": err, "pass": False})
            print(f"  [{run_i+1:02d}/{N_RUNS}] HTTP error: {err}")
            time.sleep(2)
            continue

        verdict = judge(task_key, response)
        verdict["run"] = run_i + 1
        verdict["temperature"] = temp
        results.append(verdict)

        if verdict["pass"]:
            passed += 1
        if verdict.get("operational_substitution"):
            op_sub_count += 1
        if verdict["used_python_prior"]:
            prior_count += 1
        if verdict["noticed_inversion"]:
            l4_count += 1

        status = "PASS" if verdict["pass"] else ("OPSUB" if verdict.get("operational_substitution") else ("PRIOR" if verdict["used_python_prior"] else "FAIL"))
        print(f"  [{run_i+1:02d}/{N_RUNS}] {status} | prior={verdict['used_python_prior']} l4={verdict['noticed_inversion']} | {verdict['code_snippet'][:60]!r}")

        # Small delay to avoid rate limits
        time.sleep(0.5)

    valid_n = N_RUNS - http_errors
    pass_rate = passed / valid_n if valid_n > 0 else 0
    ppr = prior_count / valid_n if valid_n > 0 else 0
    op_sub_rate = op_sub_count / valid_n if valid_n > 0 else 0

    summary = {
        "experiment": exp_name,
        "model": model,
        "task": task_key,
        "task_name": task_tag,
        "n_runs": N_RUNS,
        "n_valid": valid_n,
        "n_http_errors": http_errors,
        "passed": passed,
        "pass_rate": round(pass_rate, 4),
        "ppr": round(ppr, 4),
        "op_sub_count": op_sub_count,
        "op_sub_rate": round(op_sub_rate, 4),
        "prior_count": prior_count,
        "l4_detected": l4_count,
        "date": DATE_STR,
        "results": results,
    }

    # Wilson 95% CI for pass rate
    if valid_n > 0:
        z = 1.96
        p_hat = pass_rate
        n = valid_n
        center = (p_hat + z**2/(2*n)) / (1 + z**2/n)
        margin = z * ((p_hat*(1-p_hat)/n + z**2/(4*n**2))**0.5) / (1 + z**2/n)
        summary["wilson_ci_pass"] = [round(max(0, center - margin), 4), round(min(1, center + margin), 4)]
        # Wilson CI for PPR
        p_hat2 = ppr
        center2 = (p_hat2 + z**2/(2*n)) / (1 + z**2/n)
        margin2 = z * ((p_hat2*(1-p_hat2)/n + z**2/(4*n**2))**0.5) / (1 + z**2/n)
        summary["wilson_ci_ppr"] = [round(max(0, center2 - margin2), 4), round(min(1, center2 + margin2), 4)]

    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\n{'─'*60}")
    print(f"RESULT: {passed}/{valid_n} pass ({pass_rate:.1%}), PPR={ppr:.2f}, OpSub={op_sub_count}/{valid_n} ({op_sub_rate:.1%})")
    if "wilson_ci_pass" in summary:
        print(f"  Wilson 95% CI (pass): {summary['wilson_ci_pass']}")
        print(f"  Wilson 95% CI (PPR):  {summary['wilson_ci_ppr']}")
    print(f"Saved: {out_path}")
    return summary


def main():
    if EXPERIMENT == "all":
        exps = list(EXPERIMENTS.items())
    elif EXPERIMENT in EXPERIMENTS:
        exps = [(EXPERIMENT, EXPERIMENTS[EXPERIMENT])]
    else:
        print(f"Unknown experiment: {EXPERIMENT}. Use: {list(EXPERIMENTS.keys())} or 'all'")
        return

    all_summaries = []
    for exp_name, exp_cfg in exps:
        s = run_experiment(exp_name, exp_cfg)
        all_summaries.append(s)

    print("\n" + "="*60)
    print("ALL DONE")
    for s in all_summaries:
        print(f"  {s['experiment']} ({s['model']} {s['task_name']}): {s['passed']}/{s['n_valid']} pass, PPR={s['ppr']:.2f}, OpSub={s['op_sub_count']}/{s['n_valid']}")
    print("="*60)


if __name__ == "__main__":
    main()
