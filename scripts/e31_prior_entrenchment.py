#!/usr/bin/env python3
"""
Experiment E31: Prior Entrenchment Score (PES) using logprobs API.

Tests how strongly each model's prior favors canonical completions
for common coding patterns.
"""

import json
import math
import os
import sys
import urllib.request
import urllib.error

API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    print("ERROR: OPENAI_API_KEY not set")
    sys.exit(1)

MODELS = ["gpt-4o", "gpt-4.1-mini", "gpt-4o-mini"]

TASKS = [
    {
        "task": "fib_base_case",
        "prompt_suffix": 'def fib(n):\n    if n <= 1:\n        return ',
        "canonical_token": "n",
    },
    {
        "task": "merge_sort_base_case",
        "prompt_suffix": 'def merge_sort(arr):\n    if len(arr) <= 1:\n        return ',
        "canonical_token": "arr",
    },
    {
        "task": "is_sorted_base_case",
        "prompt_suffix": 'def is_sorted(lst):\n    if len(lst) <= 1:\n        return ',
        "canonical_token": "True",
    },
    {
        "task": "count_vowels_loop",
        "prompt_suffix": 'def count_vowels(s):\n    count = 0\n    for char in ',
        "canonical_token": "s",
    },
]

ENDPOINT = "https://api.openai.com/v1/chat/completions"


def call_openai(model, prompt):
    """Call OpenAI chat completions with logprobs enabled."""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1,
        "logprobs": True,
        "top_logprobs": 5,
        "temperature": 0,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode("utf-8"))


def run_experiment():
    results = []

    for model in MODELS:
        print(f"\n{'='*60}")
        print(f"Model: {model}")
        print(f"{'='*60}")

        for task_info in TASKS:
            task = task_info["task"]
            suffix = task_info["prompt_suffix"]
            canonical = task_info["canonical_token"]
            prompt = f"Complete this Python code (just the next token):\n{suffix}"

            print(f"\n  Task: {task} | canonical: '{canonical}'")

            try:
                resp = call_openai(model, prompt)
                choice = resp["choices"][0]
                logprobs_data = choice.get("logprobs", {})
                content_logprobs = logprobs_data.get("content", [])

                if not content_logprobs:
                    print("    WARNING: no logprobs returned")
                    results.append({
                        "model": model,
                        "task": task,
                        "prompt_suffix": suffix,
                        "top5_logprobs": [],
                        "canonical_token": canonical,
                        "canonical_prob": None,
                        "canonical_rank": None,
                        "error": "no logprobs returned",
                    })
                    continue

                token_data = content_logprobs[0]
                top_logprobs = token_data.get("top_logprobs", [])

                top5 = []
                for entry in top_logprobs:
                    lp = entry["logprob"]
                    prob = math.exp(lp)
                    top5.append({
                        "token": entry["token"],
                        "logprob": round(lp, 4),
                        "prob": round(prob, 4),
                    })

                # Find canonical token rank and prob
                canonical_prob = None
                canonical_rank = None
                for i, entry in enumerate(top5):
                    tok = entry["token"].strip()
                    if tok == canonical:
                        canonical_prob = entry["prob"]
                        canonical_rank = i + 1
                        break

                # Also check the generated token itself
                generated_token = token_data.get("token", "").strip()

                result = {
                    "model": model,
                    "task": task,
                    "prompt_suffix": suffix,
                    "top5_logprobs": top5,
                    "canonical_token": canonical,
                    "canonical_prob": canonical_prob,
                    "canonical_rank": canonical_rank,
                    "generated_token": generated_token,
                }
                results.append(result)

                # Print summary
                print(f"    Generated: '{generated_token}'")
                for i, t in enumerate(top5):
                    marker = " <-- canonical" if t["token"].strip() == canonical else ""
                    print(f"    #{i+1}: '{t['token']}' logprob={t['logprob']} prob={t['prob']}{marker}")
                if canonical_rank:
                    print(f"    Canonical rank: {canonical_rank}, prob: {canonical_prob}")
                else:
                    print(f"    Canonical token '{canonical}' NOT in top 5")

            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                print(f"    ERROR {e.code}: {err_body[:200]}")
                results.append({
                    "model": model,
                    "task": task,
                    "prompt_suffix": suffix,
                    "top5_logprobs": [],
                    "canonical_token": canonical,
                    "canonical_prob": None,
                    "canonical_rank": None,
                    "error": f"HTTP {e.code}: {err_body[:200]}",
                })
            except Exception as e:
                print(f"    ERROR: {e}")
                results.append({
                    "model": model,
                    "task": task,
                    "prompt_suffix": suffix,
                    "top5_logprobs": [],
                    "canonical_token": canonical,
                    "canonical_prob": None,
                    "canonical_rank": None,
                    "error": str(e),
                })

    return results


def main():
    print("Experiment E31: Prior Entrenchment Score (PES)")
    print("=" * 60)

    results = run_experiment()

    out_path = "/Users/jaeyeong_openclaw/.openclaw/workspace/cse307-open-project/docs/research/results/e31-prior-entrenchment-score.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n\nResults saved to: {out_path}")
    print(f"Total results: {len(results)}")

    # Summary table
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Model':<20} {'Task':<25} {'Canon.':<8} {'Rank':<6} {'Prob':<8} {'Top Token'}")
    print("-" * 85)
    for r in results:
        if "error" in r:
            print(f"{r['model']:<20} {r['task']:<25} {r['canonical_token']:<8} {'ERR':<6} {'ERR':<8} ERROR")
        else:
            rank = r.get("canonical_rank") or "N/A"
            prob = f"{r['canonical_prob']:.4f}" if r.get("canonical_prob") is not None else "N/A"
            top_tok = r["top5_logprobs"][0]["token"] if r["top5_logprobs"] else "?"
            print(f"{r['model']:<20} {r['task']:<25} {r['canonical_token']:<8} {str(rank):<6} {prob:<8} '{top_tok}'")


if __name__ == "__main__":
    main()
