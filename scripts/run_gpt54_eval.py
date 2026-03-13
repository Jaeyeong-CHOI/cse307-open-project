#!/usr/bin/env python3
import os, re, json, time, pathlib, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / "docs" / "prompt-versions"
OUT_DIR = ROOT / "docs" / "prompt-failures"
RESULT_JSON = ROOT / "docs" / "prompt-eval-results.json"

MODEL = os.environ.get("EVAL_MODEL", "gpt-5.4")
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY")


def chat(messages, temperature=0):
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    url = BASE + "/chat/completions"
    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode())
    return data["choices"][0]["message"]["content"]


def judge(prompt_text, answer_text):
    sys = (
        "You are a strict evaluator. Return JSON only. "
        "Assess whether the answer follows ALL mapping rules in the prompt with 100% compliance."
    )
    usr = f"""
Evaluate this model answer against the prompt.

PROMPT:
{prompt_text}

ANSWER:
{answer_text}

Return strict JSON object:
{{
  "pass": true|false,
  "score": 0-100,
  "reasons": ["..."],
  "violations": ["..."]
}}

Pass only if rule-following is 100% exact.
"""
    raw = chat([
        {"role": "system", "content": sys},
        {"role": "user", "content": usr},
    ])
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return {"pass": False, "score": 0, "reasons": ["judge parse failed"], "violations": [raw[:500]]}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {"pass": False, "score": 0, "reasons": ["judge json decode failed"], "violations": [raw[:500]]}


def main():
    target_failures = int(os.environ.get("TARGET_FAILURES", "50"))
    prompt_files = sorted(
        [p for p in PROMPT_DIR.glob("v*.md") if p.is_file()],
        key=lambda p: int(re.search(r"v(\d+)", p.stem).group(1))
    )

    results = []
    for p in prompt_files:
        prompt_text = p.read_text()
        try:
            answer = chat([
                {"role": "system", "content": "Solve the prompt exactly. Output only code."},
                {"role": "user", "content": prompt_text},
            ])
            j = judge(prompt_text, answer)
            item = {
                "file": str(p.relative_to(ROOT)),
                "answer": answer,
                "judge": j,
            }
            print(f"{p.name}: pass={j.get('pass')} score={j.get('score')}")
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="ignore")
            item = {
                "file": str(p.relative_to(ROOT)),
                "answer": "",
                "judge": {"pass": False, "score": 0, "reasons": [f"HTTP {e.code}"], "violations": [detail[:1000]]},
            }
            print(f"{p.name}: HTTP {e.code}")
            results.append(item)
            break
        except Exception as e:
            item = {
                "file": str(p.relative_to(ROOT)),
                "answer": "",
                "judge": {"pass": False, "score": 0, "reasons": [str(e)], "violations": []},
            }
            print(f"{p.name}: error {e}")
        results.append(item)
        if len([r for r in results if not r.get("judge", {}).get("pass")]) >= target_failures:
            print(f"target failures reached: {target_failures}")
            break
        time.sleep(0.4)

    RESULT_JSON.write_text(json.dumps({"model": MODEL, "results": results}, ensure_ascii=False, indent=2))

    failed = [r for r in results if not r.get("judge", {}).get("pass")]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for f in OUT_DIR.glob("v*.md"):
        f.unlink()

    for i, r in enumerate(failed, 1):
        src = ROOT / r["file"]
        content = [
            f"# v{i} - failed case",
            "",
            "## Source Prompt",
            src.read_text(),
            "",
            "## Model Answer",
            "```",
            r.get("answer", ""),
            "```",
            "",
            "## Judge",
            "```json",
            json.dumps(r.get("judge", {}), ensure_ascii=False, indent=2),
            "```",
            "",
        ]
        (OUT_DIR / f"v{i}.md").write_text("\n".join(content))

    (OUT_DIR / "README.md").write_text(
        "# Failed Cases\n\n"
        f"Model: {MODEL}\n\n"
        f"Total: {len(results)}, Failed: {len(failed)}\n"
    )

    print(f"done: total={len(results)} failed={len(failed)}")


if __name__ == "__main__":
    main()
