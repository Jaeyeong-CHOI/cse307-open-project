#!/usr/bin/env python3
"""
L1 context-pack eval (v1-v20) for open-weight models via Groq API.
Models: llama-3.3-70b-versatile, qwen/qwen3-32b

Reuses the same judge logic as run_gpt54_eval.py + partial_judge.py.

Usage:
  python3 scripts/run_l1_groq.py
"""

import os, re, json, time, ast, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / "docs" / "archive" / "prompt-versions"
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BASE = "https://api.groq.com/openai/v1"
MODELS = ["llama-3.3-70b-versatile", "qwen/qwen3-32b"]
DATE_STR = datetime.now().strftime("%Y-%m-%d")

# Import partial_judge for KLR/PSS metrics
import sys
sys.path.insert(0, str(ROOT / "scripts"))
from partial_judge import evaluate as partial_evaluate, parse_mapping


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


def extract_code(raw: str) -> str:
    m = re.search(r"```(?:python)?\n([\s\S]*?)```", raw)
    if m:
        return m.group(1).strip()
    return raw.strip()


def build_system_message(prompt_text: str) -> str:
    base = (
        "Solve the given prompt exactly. Return ONLY code (no explanation, no markdown). "
        "Follow alias mapping strictly."
    )
    mapping = parse_mapping(prompt_text)
    required = ["def", "if", "return", "for", "in"]

    alias_rules = []
    banned_original = []
    for k in required:
        if k in mapping and mapping[k] != k:
            alias_rules.append(f"{k}->{mapping[k]}")
            banned_original.append(k)

    rules_block = "\n".join(f"- {x}" for x in alias_rules) if alias_rules else "- (no transformed aliases)"
    banned_block = ", ".join(banned_original) if banned_original else "(none)"

    return (
        base
        + "\n\n[Transformed language contract]"
        + "\nUse transformed aliases exactly as follows:"
        + f"\n{rules_block}"
        + "\nDo NOT output original Python keywords for transformed entries."
        + f"\nBanned originals for this task: {banned_block}"
        + "\nOutput only executable code in the transformed language."
    )


def deterministic_judge(prompt_text: str, answer_text: str):
    """Same judge as run_gpt54_eval.py."""
    mapping = parse_mapping(prompt_text)
    required = ["def", "if", "return", "for", "in"]
    violations = []

    def has_word(text, token):
        return re.search(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])", text) is not None

    for k in required:
        if k in mapping and mapping[k] != k:
            alias = mapping[k]
            if alias and alias not in answer_text:
                violations.append(f"missing alias for {k}: {alias}")
            if has_word(answer_text, k):
                violations.append(f"original keyword used: {k}")

    norm = answer_text
    for k, alias in mapping.items():
        if alias and alias != k:
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", alias):
                norm = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(alias) + r"(?![A-Za-z0-9_])", k, norm)
            else:
                norm = norm.replace(alias, k)

    try:
        ast.parse(norm)
    except Exception as e:
        violations.append(f"python parse failed after normalization: {e}")
        return {"pass": False, "score": 0, "violations": violations, "normalized_code": norm}

    score = 100 if not violations else max(0, 100 - 10 * len(violations))
    return {"pass": len(violations) == 0, "score": score, "violations": violations, "normalized_code": norm}


def model_short(model):
    if "llama" in model:
        return "llama33-70b"
    if "qwen" in model:
        return "qwen3-32b"
    return model.replace("/", "-").replace(".", "")


def run_model(model):
    tag = model_short(model)

    prompt_files = sorted(
        [p for p in PROMPT_DIR.glob("v*.md") if p.is_file() and p.stem[1:].isdigit()],
        key=lambda p: int(re.search(r"v(\d+)", p.stem).group(1)),
    )
    # Use v1-v20 for context-pack eval
    prompt_files = [p for p in prompt_files if int(re.search(r"v(\d+)", p.stem).group(1)) <= 20]

    out_path = OUT_DIR / f"l1-{tag}-contextpack-groq-{DATE_STR}.json"
    partial_out_path = OUT_DIR / f"l1-{tag}-contextpack-groq-{DATE_STR}.partial_scores.json"

    results = []
    partial_scores = []

    print(f"\n{'='*60}")
    print(f"[L1 Groq] model={model}, prompts={len(prompt_files)}, ctx-pack=True")
    print(f"Output: {out_path}")

    for p in prompt_files:
        prompt_text = p.read_text()
        sys_msg = build_system_message(prompt_text)

        response, err = chat(model, [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt_text},
        ])

        if err:
            item = {
                "file": str(p.relative_to(ROOT)),
                "answer": "",
                "judge": {"pass": False, "score": 0, "violations": [err]},
            }
            ev = {"klr": 1.0, "acr": 0.0, "pss": 0.0, "pir": 1.0, "parse_ok": False,
                  "skeleton": {}, "per_token_leakage": {}, "file": str(p.relative_to(ROOT))}
            print(f"  {p.name}: ERROR {err[:60]}")
        else:
            answer = extract_code(response)
            j = deterministic_judge(prompt_text, answer)
            item = {"file": str(p.relative_to(ROOT)), "answer": answer, "judge": j}
            ev = partial_evaluate(prompt_text, answer)
            ev["file"] = str(p.relative_to(ROOT))
            print(f"  {p.name}: pass={j['pass']} score={j['score']} KLR={ev['klr']:.2f} PSS={ev['pss']:.2f}")

        results.append(item)
        partial_scores.append(ev)
        time.sleep(3.0)

    # Save results
    with open(out_path, "w") as f:
        json.dump({"model": model, "results": results}, f, indent=2, ensure_ascii=False)

    with open(partial_out_path, "w") as f:
        json.dump({"source": str(out_path), "n": len(partial_scores), "samples": partial_scores},
                  f, indent=2, ensure_ascii=False)

    avg_klr = sum(x["klr"] for x in partial_scores) / max(len(partial_scores), 1)
    avg_pss = sum(x["pss"] for x in partial_scores) / max(len(partial_scores), 1)
    passes = sum(1 for r in results if r["judge"]["pass"])

    print(f"\nFINAL: {model} | passes={passes}/{len(results)} | avg_KLR={avg_klr:.3f} | avg_PSS={avg_pss:.3f}")
    print(f"Saved: {out_path}")
    return {"model": model, "tag": tag, "n": len(results), "passes": passes,
            "avg_klr": round(avg_klr, 3), "avg_pss": round(avg_pss, 3)}


if __name__ == "__main__":
    summaries = []
    for model in MODELS:
        s = run_model(model)
        summaries.append(s)

    print(f"\n{'='*60}")
    print("SUMMARY:")
    for s in summaries:
        print(f"  {s['tag']}: passes={s['passes']}/{s['n']} KLR={s['avg_klr']:.3f} PSS={s['avg_pss']:.3f}")
