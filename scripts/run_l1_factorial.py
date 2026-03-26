#!/usr/bin/env python3
"""
L1 Factorial Design Experiment (Type A/B/C, n=30 per type)
=============================================================
Type A (cross-keyword): Python keyword → different Python keyword
  e.g., if→for, def→return, etc.
Type B (long phrase): Python keyword → 3+ word natural language phrase
  e.g., def→"begin function block", if→"check condition whether"
Type C (short non-kw): Python keyword → short non-keyword
  e.g., def→fn, if→go, for→loop

Model: gpt-4o (context-pack), n=10 per prompt
Output: docs/research/results/l1-factorial-typeABC-2026-03-27.json
"""

import os, re, json, time, ast, pathlib, random, sys, urllib.request, urllib.error
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / os.environ.get("L1_OUT_FILE", "l1-factorial-typeABC-n5-2026-03-27.json")

sys.path.insert(0, str(ROOT / "scripts"))
from partial_judge import evaluate as partial_evaluate, parse_mapping, compute_klr_acr

API_KEY = os.environ.get("OPENAI_API_KEY")
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
MODEL = "gpt-4o"
N_PER_PROMPT = int(os.environ.get("L1_N_PER_PROMPT", "5"))
DATE_STR = datetime.now().strftime("%Y-%m-%d")

# ─── Alias pool definitions ────────────────────────────────────────────────

# All Python keywords that can serve as alias targets
PYTHON_KEYWORDS = ["for", "if", "def", "return", "in", "else", "while", "class",
                   "import", "from", "pass", "break", "continue", "lambda",
                   "yield", "with", "as", "try", "except", "finally", "raise",
                   "assert", "del", "global", "nonlocal", "not", "and", "or",
                   "True", "False", "None"]

# Source tokens we always need to alias (required for judge)
REQUIRED_SOURCES = ["def", "if", "return", "for", "in"]

# ─── Type A: cross-keyword aliases (Python kw → different Python kw) ───────
# Each alias replaces one required source with a *different* Python keyword
# We ensure no self-mapping.
TYPE_A_ALIAS_CANDIDATES = {
    "def":    [kw for kw in PYTHON_KEYWORDS if kw not in ("def",)],
    "if":     [kw for kw in PYTHON_KEYWORDS if kw not in ("if",)],
    "return": [kw for kw in PYTHON_KEYWORDS if kw not in ("return",)],
    "for":    [kw for kw in PYTHON_KEYWORDS if kw not in ("for",)],
    "in":     [kw for kw in PYTHON_KEYWORDS if kw not in ("in",)],
}

# ─── Type B: long phrases (3+ words, natural language) ─────────────────────
TYPE_B_LONG_PHRASES = [
    # def replacements
    ("def", "begin function block"),
    ("def", "declare subroutine here"),
    ("def", "create new function with"),
    ("def", "introduce a method called"),
    ("def", "start function definition at"),
    ("def", "open function scope now"),
    # if replacements
    ("if", "check condition whether or"),
    ("if", "evaluate this branch when"),
    ("if", "conditional execution starts here"),
    ("if", "run the following if"),
    ("if", "test guard clause for"),
    ("if", "branch on condition that"),
    # return replacements
    ("return", "emit result value now"),
    ("return", "produce output from function"),
    ("return", "send back this value"),
    ("return", "yield final result here"),
    ("return", "output the computed answer"),
    ("return", "give back the value"),
    # for replacements
    ("for", "iterate over each element"),
    ("for", "loop through all items"),
    ("for", "repeat for each item"),
    ("for", "traverse the sequence from"),
    ("for", "enumerate all elements of"),
    ("for", "cycle through every entry"),
    # in replacements
    ("in", "drawn from the collection"),
    ("in", "taken from the given"),
    ("in", "belonging to the range"),
    ("in", "selected from the set"),
    ("in", "pulled from the sequence"),
    ("in", "sourced from the iterable"),
]

# ─── Type C: short non-keyword aliases ─────────────────────────────────────
TYPE_C_SHORT = [
    # def
    ("def", "fn"),
    ("def", "fc"),
    ("def", "proc"),
    ("def", "sub"),
    ("def", "mk"),
    ("def", "blk"),
    # if
    ("if", "go"),
    ("if", "cmp"),
    ("if", "chk"),
    ("if", "whn"),
    ("if", "bif"),
    ("if", "qry"),
    # return
    ("return", "ret"),
    ("return", "out"),
    ("return", "emit"),
    ("return", "yld"),
    ("return", "res"),
    ("return", "ans"),
    # for
    ("for", "loop"),
    ("for", "each"),
    ("for", "iter"),
    ("for", "rpt"),
    ("for", "cyc"),
    ("for", "trv"),
    # in
    ("in", "of"),
    ("in", "frm"),
    ("in", "src"),
    ("in", "via"),
    ("in", "thru"),
    ("in", "within"),
]


# ─── Prompt builder ──────────────────────────────────────────────────────────

PROBLEM_TEXT = """[문제] 아래 동작을 만족하는 코드를 작성하시오.
1) fib(n) 함수를 정의하라.
2) n <= 1 이면 n을 반환하라.
3) 그 외에는 fib(n-1) + fib(n-2)를 반환하라.
4) for 반복문으로 i = 0..6까지 순회하며 print(i, fib(i))를 출력하라."""

LANG_DESC = """[언어 설명]
Python 문법은 그대로 유지합니다.
키워드 별칭은 사용자가 원하는 문자열(공백 포함)로 설정할 수 있습니다.
실행 시에는 입력 코드에서 별칭을 감지하고, 변경된 키워드는 원본 Python 키워드와 같은 글자수의 난수 토큰을 거친 뒤 Python 원본 키워드로 변환해 실행합니다."""


def build_prompt(alias_map: dict) -> str:
    """Build a v-style prompt string from alias_map {source: alias}."""
    lines = []
    for src, alias in alias_map.items():
        lines.append(f"- {src} --> {alias}")
    mapping_block = "\n".join(lines)
    return f"{LANG_DESC}\n\n현재 설정 요약:\n{mapping_block}\n\n[문제 설명]\n{PROBLEM_TEXT}"


def build_system_message(alias_map: dict) -> str:
    base = (
        "Solve the given prompt exactly. Return ONLY code (no explanation, no markdown). "
        "Follow alias mapping strictly."
    )
    alias_rules = [f"{src}->{alias}" for src, alias in alias_map.items() if alias != src]
    banned = [src for src, alias in alias_map.items() if alias != src]
    rules_block = "\n".join(f"- {x}" for x in alias_rules) or "- (no transformed aliases)"
    banned_block = ", ".join(banned) or "(none)"
    return (
        base
        + "\n\n[Transformed language contract]"
        + "\nUse transformed aliases exactly as follows:"
        + f"\n{rules_block}"
        + "\nDo NOT output original Python keywords for transformed entries."
        + f"\nBanned originals for this task: {banned_block}"
        + "\nOutput only executable code in the transformed language."
    )


# ─── Sampling helpers ────────────────────────────────────────────────────────

def generate_type_a_configs(n: int, seed: int) -> list[dict]:
    """Generate n Type-A alias configs using given seed."""
    rng = random.Random(seed)
    configs = []
    for _ in range(n):
        alias_map = {}
        for src in REQUIRED_SOURCES:
            candidates = TYPE_A_ALIAS_CANDIDATES[src]
            # pick a different kw; avoid collisions with already-chosen aliases
            chosen = rng.choice(candidates)
            alias_map[src] = chosen
        configs.append(alias_map)
    return configs


def generate_type_b_configs(n: int, seed: int) -> list[dict]:
    """Select n Type-B alias configs (one mapping per config, cycling through sources)."""
    rng = random.Random(seed)
    # group by source
    by_source = {}
    for src, phrase in TYPE_B_LONG_PHRASES:
        by_source.setdefault(src, []).append(phrase)

    configs = []
    for _ in range(n):
        # pick aliases for all required sources
        alias_map = {}
        for src in REQUIRED_SOURCES:
            phrases = by_source.get(src, [src])
            alias_map[src] = rng.choice(phrases)
        configs.append(alias_map)
    return configs


def generate_type_c_configs(n: int, seed: int) -> list[dict]:
    """Select n Type-C alias configs."""
    rng = random.Random(seed)
    by_source = {}
    for src, short in TYPE_C_SHORT:
        by_source.setdefault(src, []).append(short)

    configs = []
    for _ in range(n):
        alias_map = {}
        for src in REQUIRED_SOURCES:
            shorts = by_source.get(src, [src])
            alias_map[src] = rng.choice(shorts)
        configs.append(alias_map)
    return configs


# ─── API call ───────────────────────────────────────────────────────────────

def has_word(text: str, token: str) -> bool:
    return bool(re.search(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])", text))


def extract_code(raw: str) -> str:
    m = re.search(r"```(?:python)?\n([\s\S]*?)```", raw)
    if m:
        return m.group(1).strip()
    return raw.strip()


def deterministic_judge(alias_map: dict, answer_text: str):
    """Judge based on alias_map directly (no prompt-file parsing needed)."""
    violations = []
    for src in REQUIRED_SOURCES:
        alias = alias_map.get(src, src)
        if alias == src:
            continue
        # Check alias is present
        if not has_word(answer_text, alias):
            violations.append(f"missing alias for {src}: {alias}")
        # Check original not leaked
        if has_word(answer_text, src):
            violations.append(f"original keyword used: {src}")

    # Normalize and parse
    norm = answer_text
    for src in REQUIRED_SOURCES:
        alias = alias_map.get(src, src)
        if alias == src:
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", alias):
            norm = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(alias) + r"(?![A-Za-z0-9_])", src, norm)
        else:
            norm = norm.replace(alias, src)

    parse_ok = False
    try:
        ast.parse(norm)
        parse_ok = True
    except SyntaxError as e:
        violations.append(f"python parse failed after normalization: {e}")

    passed = len(violations) == 0
    return {
        "pass": passed,
        "violations": violations,
        "normalized_code": norm,
        "parse_ok": parse_ok,
    }


def compute_klr_from_alias(alias_map: dict, answer_text: str):
    active = [(src, alias_map[src]) for src in REQUIRED_SOURCES if alias_map.get(src, src) != src]
    if not active:
        return 0.0, 1.0
    leaked = sum(1 for src, alias in active if has_word(answer_text, src))
    klr = leaked / len(active)
    return klr, 1.0 - klr


def chat(messages, temperature=0, max_retries=5):
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    url = BASE + "/chat/completions"
    body = {"model": MODEL, "messages": messages, "temperature": temperature}
    for attempt in range(max_retries):
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
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


# ─── Main evaluation loop ────────────────────────────────────────────────────

def run_type(type_label: str, configs: list[dict]) -> list[dict]:
    results = []
    for idx, alias_map in enumerate(configs):
        prompt_text = build_prompt(alias_map)
        sys_msg = build_system_message(alias_map)
        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt_text},
        ]

        print(f"  [{type_label}] config {idx+1}/{len(configs)} | aliases: {alias_map}")

        trial_results = []
        for trial in range(N_PER_PROMPT):
            raw, err = chat(messages, temperature=0.7)
            if err:
                print(f"    trial {trial+1}: ERROR {err}")
                trial_results.append({"error": err, "pass": False})
                continue
            answer = extract_code(raw)
            judge = deterministic_judge(alias_map, answer)
            klr, acr = compute_klr_from_alias(alias_map, answer)
            trial_results.append({
                "trial": trial + 1,
                "pass": judge["pass"],
                "klr": round(klr, 4),
                "acr": round(acr, 4),
                "violations": judge["violations"],
                "parse_ok": judge["parse_ok"],
                "answer_snippet": answer[:200],
            })
            time.sleep(0.3)

        n_pass = sum(1 for t in trial_results if t.get("pass"))
        avg_klr = sum(t.get("klr", 0) for t in trial_results if "klr" in t) / max(1, len([t for t in trial_results if "klr" in t]))

        results.append({
            "type": type_label,
            "config_idx": idx + 1,
            "alias_map": alias_map,
            "n_trials": N_PER_PROMPT,
            "n_pass": n_pass,
            "pass_rate": round(n_pass / N_PER_PROMPT, 3),
            "avg_klr": round(avg_klr, 4),
            "trials": trial_results,
        })

        print(f"    → pass {n_pass}/{N_PER_PROMPT} | avg_KLR={avg_klr:.3f}")
        time.sleep(0.5)

    return results


def main():
    print(f"=== L1 Factorial Design Experiment ===")
    print(f"Model: {MODEL} | N per prompt: {N_PER_PROMPT}")
    print(f"Generating configs...")

    n_configs = int(os.environ.get("L1_N_CONFIGS", "10"))
    type_a_configs = generate_type_a_configs(n_configs, seed=42)
    type_b_configs = generate_type_b_configs(n_configs, seed=43)
    type_c_configs = generate_type_c_configs(n_configs, seed=44)

    print(f"Type A (cross-keyword): {len(type_a_configs)} configs")
    print(f"Type B (long phrase): {len(type_b_configs)} configs")
    print(f"Type C (short non-kw): {len(type_c_configs)} configs")

    all_results = {}

    print("\n--- Running Type A (cross-keyword) ---")
    all_results["type_A"] = run_type("A_cross_keyword", type_a_configs)

    print("\n--- Running Type B (long phrase) ---")
    all_results["type_B"] = run_type("B_long_phrase", type_b_configs)

    print("\n--- Running Type C (short non-kw) ---")
    all_results["type_C"] = run_type("C_short_nonkw", type_c_configs)

    # ─── Compute summary stats per type ─────────────────────────────────────
    summary = {}
    for t_key, t_results in all_results.items():
        pass_rates = [r["pass_rate"] for r in t_results]
        klrs = [r["avg_klr"] for r in t_results]
        n = len(t_results)
        avg_pr = sum(pass_rates) / n
        avg_klr = sum(klrs) / n
        # Wilson CI for pass rate (aggregate over all trials)
        total_trials = sum(r["n_trials"] for r in t_results)
        total_pass = sum(r["n_pass"] for r in t_results)
        from math import sqrt
        p_hat = total_pass / total_trials if total_trials > 0 else 0
        z = 1.96
        denom = 1 + z**2 / total_trials
        center = (p_hat + z**2 / (2 * total_trials)) / denom
        margin = (z * sqrt(p_hat * (1 - p_hat) / total_trials + z**2 / (4 * total_trials**2))) / denom
        wilson_lo = max(0, center - margin)
        wilson_hi = min(1, center + margin)

        summary[t_key] = {
            "n_configs": n,
            "total_trials": total_trials,
            "total_pass": total_pass,
            "avg_pass_rate": round(avg_pr, 4),
            "avg_klr": round(avg_klr, 4),
            "wilson_ci_95": {
                "lower": round(wilson_lo, 4),
                "upper": round(wilson_hi, 4),
                "p_hat": round(p_hat, 4),
            },
        }

    output = {
        "experiment": "L1 Factorial Design (Type A/B/C)",
        "date": DATE_STR,
        "model": MODEL,
        "n_per_prompt": N_PER_PROMPT,
        "seeds": {"type_A": 42, "type_B": 43, "type_C": 44},
        "design": {
            "type_A": "cross-keyword: Python keyword → different Python keyword",
            "type_B": "long-phrase: Python keyword → 3+ word natural language phrase",
            "type_C": "short-nonkw: Python keyword → short non-keyword token",
        },
        "rigor_notes": {
            "alias_generation": "random (seeded; seed=42,43,44); no researcher selection bias",
            "judge": "deterministic rule-based (alias presence + keyword leakage + AST parse)",
            "judge_validation": "automated judge, unvalidated (manual spot-check recommended)",
            "n_per_cell": f"{N_PER_PROMPT} trials per config; n=30 configs per type",
            "statistical_test": "Wilson CI (95%) per type reported in summary",
            "type_A_collision_warning": (
                "Type A cross-kw aliases may produce src-alias collisions "
                "(e.g., alias(return)=for while for is also a source token). "
                "Judge conservatively flags such outputs as violations; "
                "true compliance may be slightly higher than reported KLR."
            ),
        },
        "summary": summary,
        "results": all_results,
    }

    OUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n=== Done. Results saved to {OUT_FILE} ===")
    print("\nSummary:")
    for t_key, s in summary.items():
        ci = s["wilson_ci_95"]
        print(f"  {t_key}: pass={ci['p_hat']:.3f} [95% CI {ci['lower']:.3f}–{ci['upper']:.3f}]"
              f"  avg_KLR={s['avg_klr']:.3f}  (n={s['total_trials']} trials)")

    return output


if __name__ == "__main__":
    main()
