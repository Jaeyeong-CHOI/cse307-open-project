#!/usr/bin/env python3
import os, re, json, time, ast, pathlib, urllib.request, urllib.error

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
    body = {"model": MODEL, "messages": messages, "temperature": temperature}
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


def extract_code(raw: str) -> str:
    m = re.search(r"```(?:python)?\n([\s\S]*?)```", raw)
    if m:
        return m.group(1).strip()
    return raw.strip()


def parse_mapping(prompt_text: str):
    m = re.search(r"현재 설정 요약:\n([\s\S]*?)\n\n\[문제 설명\]", prompt_text)
    if not m:
        return {}
    mp = {}
    for ln in m.group(1).splitlines():
        ln = ln.strip().lstrip("-").strip()
        if "-->" in ln:
            a, b = [x.strip() for x in ln.split("-->", 1)]
            mp[a] = b
    return mp


def has_word(text: str, token: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])", text) is not None


def deterministic_judge(prompt_text: str, answer_text: str):
    """
    Rule:
    1) Core mapping compliance for fib task keywords: def/if/return/for/in
    2) After alias->python normalization, code must parse and match task skeleton
    """
    mapping = parse_mapping(prompt_text)
    required = ["def", "if", "return", "for", "in"]
    violations = []

    # 1) mapping compliance in raw answer
    for k in required:
        if k in mapping and mapping[k] != k:
            alias = mapping[k]
            if alias and alias not in answer_text:
                violations.append(f"missing alias for {k}: {alias}")
            if has_word(answer_text, k):
                violations.append(f"original keyword used: {k}")

    # 2) normalize aliases -> python
    norm = answer_text
    for k, alias in mapping.items():
        if alias and alias != k:
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", alias):
                norm = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(alias) + r"(?![A-Za-z0-9_])", k, norm)
            else:
                norm = norm.replace(alias, k)

    # parse
    try:
        tree = ast.parse(norm)
    except Exception as e:
        violations.append(f"python parse failed after normalization: {e}")
        return {
            "pass": False,
            "score": 0,
            "violations": violations,
            "normalized_code": norm,
        }

    # skeleton checks
    fn = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "fib":
            fn = node
            break
    if not fn:
        violations.append("missing function fib")
    else:
        # if n <= 1: return n
        found_base = False
        found_recur = False
        for n in ast.walk(fn):
            if isinstance(n, ast.If):
                # n <= 1
                if isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name) and n.test.left.id == "n":
                    if n.test.ops and isinstance(n.test.ops[0], ast.LtE):
                        # comparator 1
                        if n.test.comparators and isinstance(n.test.comparators[0], ast.Constant) and n.test.comparators[0].value == 1:
                            # return n in body
                            for b in n.body:
                                if isinstance(b, ast.Return) and isinstance(b.value, ast.Name) and b.value.id == "n":
                                    found_base = True
            if isinstance(n, ast.Return):
                # return fib(n-1) + fib(n-2)
                if isinstance(n.value, ast.BinOp) and isinstance(n.value.op, ast.Add):
                    l, r = n.value.left, n.value.right
                    def is_fib_call(x, delta):
                        return (
                            isinstance(x, ast.Call)
                            and isinstance(x.func, ast.Name)
                            and x.func.id == "fib"
                            and len(x.args) == 1
                            and isinstance(x.args[0], ast.BinOp)
                            and isinstance(x.args[0].left, ast.Name)
                            and x.args[0].left.id == "n"
                            and isinstance(x.args[0].op, ast.Sub)
                            and isinstance(x.args[0].right, ast.Constant)
                            and x.args[0].right.value == delta
                        )
                    if is_fib_call(l, 1) and is_fib_call(r, 2):
                        found_recur = True
        if not found_base:
            violations.append("missing base case: if n <= 1 return n")
        if not found_recur:
            violations.append("missing recursive return fib(n-1)+fib(n-2)")

    # top-level for i in range(7): print(i, fib(i))
    found_loop = False
    for n in tree.body:
        if isinstance(n, ast.For):
            if isinstance(n.target, ast.Name) and n.target.id == "i":
                if isinstance(n.iter, ast.Call) and isinstance(n.iter.func, ast.Name) and n.iter.func.id == "range":
                    if len(n.iter.args) == 1 and isinstance(n.iter.args[0], ast.Constant) and n.iter.args[0].value == 7:
                        for b in n.body:
                            if isinstance(b, ast.Expr) and isinstance(b.value, ast.Call):
                                c = b.value
                                if isinstance(c.func, ast.Name) and c.func.id == "print" and len(c.args) == 2:
                                    if isinstance(c.args[0], ast.Name) and c.args[0].id == "i":
                                        if isinstance(c.args[1], ast.Call) and isinstance(c.args[1].func, ast.Name) and c.args[1].func.id == "fib":
                                            if len(c.args[1].args) == 1 and isinstance(c.args[1].args[0], ast.Name) and c.args[1].args[0].id == "i":
                                                found_loop = True
    if not found_loop:
        violations.append("missing loop: for i in range(7): print(i, fib(i))")

    score = 100 if not violations else max(0, 100 - 10 * len(violations))
    return {
        "pass": len(violations) == 0,
        "score": score,
        "violations": violations,
        "normalized_code": norm,
    }


def main():
    target_failures = int(os.environ.get("TARGET_FAILURES", "50"))
    prompt_files = sorted(
        [p for p in PROMPT_DIR.glob("v*.md") if p.is_file()],
        key=lambda p: int(re.search(r"v(\d+)", p.stem).group(1)),
    )

    results = []
    for p in prompt_files:
        prompt_text = p.read_text()
        try:
            answer_raw = chat([
                {
                    "role": "system",
                    "content": (
                        "Solve the given prompt exactly. "
                        "Return ONLY code (no explanation, no markdown). "
                        "Follow alias mapping strictly."
                    ),
                },
                {"role": "user", "content": prompt_text},
            ])
            answer = extract_code(answer_raw)
            j = deterministic_judge(prompt_text, answer)
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
                "judge": {
                    "pass": False,
                    "score": 0,
                    "violations": [f"HTTP {e.code}", detail[:1000]],
                },
            }
            print(f"{p.name}: HTTP {e.code}")
            results.append(item)
            break
        except Exception as e:
            item = {
                "file": str(p.relative_to(ROOT)),
                "answer": "",
                "judge": {"pass": False, "score": 0, "violations": [str(e)]},
            }
            print(f"{p.name}: error {e}")

        results.append(item)
        fails = len([r for r in results if not r.get("judge", {}).get("pass")])
        if fails >= target_failures:
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
