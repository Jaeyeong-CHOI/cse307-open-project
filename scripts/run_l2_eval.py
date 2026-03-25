#!/usr/bin/env python3
"""Evaluate L2 syntax-inversion language prompts against models.
L2 uses inverted Python-like syntax: :define, <=, ?cond:, loop ... over
Judge checks structural compliance: did model use L2 syntax or fall back to Python?
"""
import os, re, json, time, pathlib, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / "docs" / "archive" / "L2-prompt-versions"

MODEL = os.environ.get("EVAL_MODEL", "gpt-4o-mini")
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")
RUNS_PER_PROMPT = int(os.environ.get("RUNS_PER_PROMPT", "1"))
DATE_STR = datetime.now().strftime("%Y-%m-%d")
model_tag = MODEL.replace(".", "").replace("-", "")
default_out = str(ROOT / "docs" / "research" / "results" / f"l2-{model_tag}-n{5*RUNS_PER_PROMPT}-{DATE_STR}.json")
RESULT_JSON = os.environ.get("RESULT_JSON", default_out)

PYTHON_KEYWORDS = ["def ", "return ", " if ", " for ", " in "]
L2_MARKERS = [":define", "<=", "?cond:", "loop ", " over ", ";;"]


def chat(messages):
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    url = BASE + "/chat/completions"
    body = {"model": MODEL, "messages": messages, "temperature": 0}
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())["choices"][0]["message"]["content"]


def l2_judge(answer: str) -> dict:
    """Judge L2 compliance. Returns SIR, L2 adoption, violations."""
    # Count Python keyword leakage
    python_hits = {kw: answer.count(kw) for kw in PYTHON_KEYWORDS if kw in answer}
    l2_hits = {m: answer.count(m) for m in L2_MARKERS if m in answer}

    total_structural = sum(python_hits.values()) + sum(l2_hits.values())
    python_count = sum(python_hits.values())
    l2_count = sum(l2_hits.values())

    sir = python_count / max(total_structural, 1)  # Structural Inversion Rate (lower = better L2 compliance)
    l2_adoption = l2_count / max(total_structural, 1)  # higher = more L2 tokens used

    violations = [f"Python keyword used: '{k.strip()}'" for k in python_hits if python_hits[k] > 0]
    pass_ = len(violations) == 0 and l2_count > 0

    return {
        "pass": pass_,
        "sir": round(sir, 4),
        "l2_adoption": round(l2_adoption, 4),
        "python_hits": python_hits,
        "l2_hits": l2_hits,
        "violations": violations,
    }


def main():
    prompt_files = sorted(
        [p for p in PROMPT_DIR.glob("v*.md") if p.is_file()],
        key=lambda p: int(re.search(r"v(\d+)", p.stem).group(1))
    )
    results = []
    print(f"[L2 eval] model={MODEL}, prompts={len(prompt_files)}, runs_per_prompt={RUNS_PER_PROMPT}")
    for p in prompt_files:
        prompt_text = p.read_text()
        for run_i in range(RUNS_PER_PROMPT):
            try:
                answer = chat([
                    {"role": "system", "content": "Follow the L2 language specification exactly. Use ONLY L2 syntax. Do NOT use Python keywords."},
                    {"role": "user", "content": prompt_text},
                ])
                j = l2_judge(answer)
                item = {"file": str(p.name), "run": run_i, "answer": answer, "judge": j}
                print(f"{p.name} run{run_i}: pass={j['pass']} SIR={j['sir']} L2adopt={j['l2_adoption']}")
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="ignore")[:200]
                item = {"file": str(p.name), "run": run_i, "answer": "", "judge": {"pass": False, "sir": 1.0, "l2_adoption": 0.0, "violations": [f"HTTP {e.code}: {detail}"]}}
                print(f"{p.name} run{run_i}: HTTP {e.code}")
            except Exception as e:
                item = {"file": str(p.name), "run": run_i, "answer": "", "judge": {"pass": False, "sir": 1.0, "l2_adoption": 0.0, "violations": [str(e)]}}
                print(f"{p.name} run{run_i}: error {e}")
            results.append(item)
            time.sleep(0.4)

    out = pathlib.Path(RESULT_JSON)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"model": MODEL, "level": "L2", "date": DATE_STR, "total": len(results), "results": results}, indent=2, ensure_ascii=False))

    avg_sir = sum(r["judge"].get("sir", 1.0) for r in results) / max(len(results), 1)
    avg_l2 = sum(r["judge"].get("l2_adoption", 0.0) for r in results) / max(len(results), 1)
    print(f"\nDone: n={len(results)} | avg_SIR={avg_sir:.3f} | avg_L2adopt={avg_l2:.3f} | output={out}")


if __name__ == "__main__":
    main()
