#!/usr/bin/env python3
"""
L4 Hard-Task Experiment: Pattern blindness with complex algorithms.

Tests whether harder tasks (longer code, deeper Python priors) show
stronger or weaker pattern blindness compared to simple tasks.

Hard Tasks (L4 implicit semantic inversion, example-only delivery):
  H1 - merge_sort:     returns DESCENDING (prior: ascending)
  H2 - binary_search:  returns -1 if FOUND, index if NOT found
  H3 - bfs_graph:      returns REVERSE BFS order (last-level-first)

Each prompt provides 2 worked examples showing inverted behavior.
No explicit rule about the inversion.

Usage:
  python3 scripts/run_l4_hard_tasks.py
  EVAL_MODEL=o3 python3 scripts/run_l4_hard_tasks.py
  RUNS_PER_TASK=5 python3 scripts/run_l4_hard_tasks.py
"""

import os, json, time, re, pathlib, urllib.request, urllib.error, textwrap
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.environ.get("EVAL_MODEL", "gpt-4o")
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")
RUNS_PER_TASK = int(os.environ.get("RUNS_PER_TASK", "10"))
DATE_STR = datetime.now().strftime("%Y-%m-%d")

REASONING_MODELS = {"o4-mini", "o3-mini", "o3", "o1", "o1-mini"}
COMPLETION_TOKEN_MODELS = {"gpt-5.4-mini", "gpt-5.4"}

SYSTEM_MSG = "You are a helpful programming assistant. Analyze the examples carefully and write code that produces the same behavior as shown in the examples."

# ── H1: merge_sort — descending instead of ascending ─────────────────────────
H1_PROMPT = textwrap.dedent("""\
Here are examples of our merge_sort function:

Example 1:
```
Input:  [5, 2, 8, 1]
Output: [8, 5, 2, 1]
```

Example 2:
```
Input:  [10, 3, 7, 4, 6]
Output: [10, 7, 6, 4, 3]
```

Now implement `merge_sort(arr)` in Python that produces the same behavior as shown above.
Write only the function definition, no explanation.
""")

# ── H2: binary_search — presence/absence inverted ────────────────────────────
H2_PROMPT = textwrap.dedent("""\
Here are examples of our binary_search function on a sorted array:

Example 1:
```
arr = [1, 3, 5, 7, 9]
binary_search(arr, 5) = -1
binary_search(arr, 4) = 2
```
(5 is at index 2 in the array, function returns -1; 4 is not in the array, function returns 2)

Example 2:
```
arr = [2, 4, 6, 8, 10, 12]
binary_search(arr, 8) = -1
binary_search(arr, 7) = 3
```
(8 is at index 3, function returns -1; 7 is not in the array, function returns 3)

Now implement `binary_search(arr, target)` in Python that produces the same behavior as shown above.
The array is always sorted in ascending order.
Write only the function definition, no explanation.
""")

# ── H3: bfs_graph — reversed BFS order ───────────────────────────────────────
H3_PROMPT = textwrap.dedent("""\
Here are examples of our bfs function on a graph (adjacency list):

Example 1:
```
graph = {0: [1, 2], 1: [3], 2: [4], 3: [], 4: []}
bfs(graph, 0) = [4, 3, 2, 1, 0]
```
(Standard BFS from 0 would visit: 0, 1, 2, 3, 4 — our function returns this reversed)

Example 2:
```
graph = {'A': ['B', 'C'], 'B': ['D'], 'C': ['E', 'F'], 'D': [], 'E': [], 'F': []}
bfs(graph, 'A') = ['F', 'E', 'D', 'C', 'B', 'A']
```
(Standard BFS: A, B, C, D, E, F — our function returns this reversed)

Now implement `bfs(graph, start)` in Python that produces the same behavior as shown above.
Write only the function definition, no explanation.
""")


TASKS = {
    "H1_mergesort": {
        "name": "merge_sort (descending)",
        "prompt": H1_PROMPT,
    },
    "H2_binsearch": {
        "name": "binary_search (inverted presence)",
        "prompt": H2_PROMPT,
    },
    "H3_bfs": {
        "name": "bfs (reversed order)",
        "prompt": H3_PROMPT,
    },
}


def chat(messages, temperature=0):
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    if MODEL in REASONING_MODELS:
        # Merge system into user; no temperature param
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
    token_limit = 8000 if MODEL in REASONING_MODELS else 800

    payload = {"model": MODEL, "messages": messages, token_key: token_limit}
    if MODEL not in REASONING_MODELS:
        payload["temperature"] = temperature

    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        return None, f"HTTP {e.code}: {body}"
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


def judge_h1(response):
    """H1 merge_sort: PASS if code produces descending order."""
    code = extract_code(response)
    try:
        ns = {}
        exec(code, ns)
        fn = ns.get("merge_sort")
        if fn is None:
            return {"pass": False, "reason": "no merge_sort function found", "code_snippet": code[:400]}
        result = fn([3, 1, 4, 1, 5, 9, 2, 6])
        expected_desc = [9, 6, 5, 4, 3, 2, 1, 1]
        expected_asc = [1, 1, 2, 3, 4, 5, 6, 9]
        passed = (result == expected_desc)
        used_prior = (result == expected_asc)
        return {
            "pass": passed,
            "used_python_prior": used_prior,
            "output": str(result),
            "code_snippet": code[:400],
        }
    except Exception as e:
        return {"pass": False, "reason": f"exec error: {e}", "code_snippet": code[:400]}


def judge_h2(response):
    """H2 binary_search: PASS if returns -1 for found, index for not-found."""
    code = extract_code(response)
    try:
        ns = {}
        exec(code, ns)
        fn = ns.get("binary_search")
        if fn is None:
            return {"pass": False, "reason": "no binary_search function found", "code_snippet": code[:400]}

        arr = [1, 3, 5, 7, 9]
        # Inverted: found->-1, not-found->index
        tests = [
            (arr, 5, -1),   # 5 is found at idx 2 -> should return -1
            (arr, 4, 2),    # 4 not found, would-be index is 2 -> return 2
            (arr, 7, -1),   # 7 is found at idx 3 -> return -1
            (arr, 6, 3),    # 6 not found, would-be index is 3 -> return 3
        ]
        results = []
        all_pass = True
        used_prior = True
        for a, target, expected in tests:
            actual = fn(a, target)
            ok = (actual == expected)
            results.append({"target": target, "expected": expected, "actual": actual, "ok": ok})
            if not ok:
                all_pass = False
            # Check if model used standard prior (found->index, not-found->-1)
            if target in a:
                if actual != a.index(target):
                    used_prior = False
            else:
                if actual != -1:
                    used_prior = False

        return {
            "pass": all_pass,
            "used_python_prior": used_prior,
            "test_results": results,
            "code_snippet": code[:400],
        }
    except Exception as e:
        return {"pass": False, "reason": f"exec error: {e}", "code_snippet": code[:400]}


def judge_h3(response):
    """H3 bfs: PASS if BFS order is reversed."""
    code = extract_code(response)
    try:
        ns = {}
        exec(code, ns)
        fn = ns.get("bfs")
        if fn is None:
            return {"pass": False, "reason": "no bfs function found", "code_snippet": code[:400]}

        graph = {0: [1, 2], 1: [3], 2: [4], 3: [], 4: []}
        result = fn(graph, 0)
        standard_bfs = [0, 1, 2, 3, 4]
        expected_reversed = [4, 3, 2, 1, 0]  # reversed standard BFS

        passed = (list(result) == expected_reversed)
        used_prior = (list(result) == standard_bfs)

        return {
            "pass": passed,
            "used_python_prior": used_prior,
            "output": str(result),
            "expected": str(expected_reversed),
            "code_snippet": code[:400],
        }
    except Exception as e:
        return {"pass": False, "reason": f"exec error: {e}", "code_snippet": code[:400]}


JUDGES = {
    "H1_mergesort": judge_h1,
    "H2_binsearch": judge_h2,
    "H3_bfs": judge_h3,
}


def run_hard_tasks():
    results = []
    total = 0
    passed_total = 0
    http_errors = 0

    model_tag = MODEL.replace(".", "").replace("-", "")
    out_path = OUT_DIR / f"l4-hard-tasks-{model_tag}-{DATE_STR}.json"

    print(f"[L4 hard-task] model={MODEL}, runs_per_task={RUNS_PER_TASK}")
    print(f"Tasks: {list(TASKS.keys())}")
    print(f"Output: {out_path}")

    task_summaries = {}

    for task_key, task in TASKS.items():
        print(f"\n== Task: {task_key} ({task['name']}) ==")
        task_passed = 0
        task_valid = 0
        task_prior = 0

        for run_i in range(RUNS_PER_TASK):
            messages = [
                {"role": "system", "content": SYSTEM_MSG},
                {"role": "user", "content": task["prompt"]},
            ]
            temp = 0 if run_i == 0 else 0.3
            response, err = chat(messages, temperature=temp)
            total += 1

            if err:
                http_errors += 1
                result = {
                    "task": task_key,
                    "run": run_i,
                    "http_error": err,
                    "judge": {"pass": False, "used_python_prior": None},
                }
                print(f"  run {run_i}: ERROR {err[:60]}")
            else:
                judgment = JUDGES[task_key](response)
                p = judgment["pass"]
                passed_total += int(p)
                task_passed += int(p)
                task_valid += 1
                if judgment.get("used_python_prior"):
                    task_prior += 1
                result = {
                    "task": task_key,
                    "task_name": task["name"],
                    "run": run_i,
                    "judge": judgment,
                    "response_snippet": response[:200],
                }
                status = "PASS" if p else "FAIL"
                print(f"  run {run_i}: {status} | prior={judgment.get('used_python_prior')}")

            results.append(result)
            with open(out_path, "w") as f:
                json.dump({
                    "model": MODEL, "date": DATE_STR,
                    "total_so_far": total, "passed_so_far": passed_total,
                    "results": results,
                }, f, indent=2, ensure_ascii=False)
            time.sleep(0.8)

        ppr = task_prior / max(task_valid, 1)
        task_summaries[task_key] = {
            "name": task["name"],
            "total": task_valid,
            "passed": task_passed,
            "pass_rate": round(task_passed / max(task_valid, 1), 3),
            "ppr": round(ppr, 3),
        }
        print(f"  -> {task_key}: passed={task_passed}/{task_valid}, PPR={ppr:.3f}")

    final = {
        "model": MODEL,
        "date": DATE_STR,
        "experiment": "L4-hard-tasks",
        "description": "L4 implicit inversion: 3 hard tasks (merge_sort/binary_search/bfs), example-only delivery",
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
    for tk, s in task_summaries.items():
        print(f"  {tk} ({s['name']}): passed={s['passed']}/{s['total']}, PPR={s['ppr']:.3f}")
    print(f"\nSaved: {out_path}")
    return final


if __name__ == "__main__":
    run_hard_tasks()
