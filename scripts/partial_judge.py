#!/usr/bin/env python3
"""
partial_judge.py — Continuous metrics for confusion-language experiments.

Returns:
  KLR  (Keyword Leakage Rate): fraction of required-alias slots where original keyword was used
  ACR  (Alias Compliance Rate): fraction of alias slots correctly absent of original keyword
  PSS  (Partial Structural Score): weighted sub-component score 0.0–1.0
  PIR  (Prior Influence Rate): KLR / (KLR + ACR), represents how much prior dominates
"""
import re, ast


REQUIRED_TOKENS = ["def", "if", "return", "for", "in"]

WEIGHTS = {
    "alias_compliance": 0.40,
    "normalize_parse": 0.25,
    "skeleton": 0.25,
    "format_fidelity": 0.10,
}


def parse_mapping(prompt_text: str) -> dict:
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
    return bool(re.search(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])", text))


def compute_klr_acr(prompt_text: str, answer_text: str) -> tuple[float, float, dict[str, bool]]:
    """Returns (KLR, ACR, per-token-leakage dict)."""
    mapping = parse_mapping(prompt_text)
    active_tokens = [t for t in REQUIRED_TOKENS if t in mapping and mapping[t] != t]

    if not active_tokens:
        return 0.0, 1.0, {}

    leakage = {}
    for tok in active_tokens:
        leakage[tok] = has_word(answer_text, tok)  # True = leaked (bad)

    leaked_count = sum(leakage.values())
    klr = leaked_count / len(active_tokens)
    acr = 1.0 - klr
    return klr, acr, leakage


def normalize_and_parse(prompt_text: str, answer_text: str) -> tuple[bool, str]:
    mapping = parse_mapping(prompt_text)
    norm = answer_text
    for k, alias in mapping.items():
        if alias and alias != k:
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", alias):
                norm = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(alias) + r"(?![A-Za-z0-9_])", k, norm)
            else:
                norm = norm.replace(alias, k)
    try:
        ast.parse(norm)
        return True, norm
    except Exception:
        return False, norm


def check_skeleton(norm: str) -> dict[str, bool]:
    """Returns presence of required structural elements."""
    results = {"has_fib_function": False, "has_base_case": False,
               "has_recursion": False, "has_loop": False}
    try:
        tree = ast.parse(norm)
    except Exception:
        return results

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "fib":
            results["has_fib_function"] = True
            for n in ast.walk(node):
                if isinstance(n, ast.If):
                    if (isinstance(n.test, ast.Compare)
                            and isinstance(n.test.left, ast.Name)
                            and n.test.left.id == "n"
                            and n.test.ops
                            and isinstance(n.test.ops[0], ast.LtE)
                            and n.test.comparators
                            and isinstance(n.test.comparators[0], ast.Constant)
                            and n.test.comparators[0].value == 1):
                        for b in n.body:
                            if isinstance(b, ast.Return) and isinstance(b.value, ast.Name) and b.value.id == "n":
                                results["has_base_case"] = True
                if isinstance(n, ast.Return):
                    if isinstance(n.value, ast.BinOp) and isinstance(n.value.op, ast.Add):
                        results["has_recursion"] = True

    for node in tree.body:
        if isinstance(node, ast.For):
            if isinstance(node.target, ast.Name) and node.target.id == "i":
                if (isinstance(node.iter, ast.Call)
                        and isinstance(node.iter.func, ast.Name)
                        and node.iter.func.id == "range"):
                    results["has_loop"] = True

    return results


def pss(acr: float, parse_ok: bool, skeleton: dict) -> float:
    skel_score = sum([
        skeleton.get("has_fib_function", False),
        skeleton.get("has_base_case", False),
        skeleton.get("has_recursion", False),
        skeleton.get("has_loop", False),
    ]) / 4.0

    return (
        WEIGHTS["alias_compliance"] * acr
        + WEIGHTS["normalize_parse"] * (1.0 if parse_ok else 0.0)
        + WEIGHTS["skeleton"] * skel_score
        + WEIGHTS["format_fidelity"] * (1.0 if skeleton.get("has_loop") else 0.0)
    )


def evaluate(prompt_text: str, answer_text: str) -> dict:
    klr, acr, leakage = compute_klr_acr(prompt_text, answer_text)
    parse_ok, norm = normalize_and_parse(prompt_text, answer_text)
    skeleton = check_skeleton(norm)
    score = pss(acr, parse_ok, skeleton)
    pir = klr / (klr + acr + 1e-9)

    return {
        "klr": round(klr, 4),
        "acr": round(acr, 4),
        "pss": round(score, 4),
        "pir": round(pir, 4),
        "parse_ok": parse_ok,
        "skeleton": skeleton,
        "per_token_leakage": leakage,
    }


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) > 1:
        # Re-evaluate an existing batch JSON file
        import glob, pathlib
        path = sys.argv[1]
        d = json.loads(pathlib.Path(path).read_text())
        results = d.get("results", [])
        import os; base = pathlib.Path(path).stem
        out = []
        for r in results:
            prompt_path = r.get("file", "")
            answer = r.get("answer", "")
            try:
                pt = pathlib.Path(prompt_path).read_text()
            except Exception:
                pt = ""
            ev = evaluate(pt, answer)
            ev["file"] = r.get("file")
            out.append(ev)

        # Aggregate
        if out:
            avg_klr = sum(x["klr"] for x in out) / len(out)
            avg_acr = sum(x["acr"] for x in out) / len(out)
            avg_pss = sum(x["pss"] for x in out) / len(out)
            avg_pir = sum(x["pir"] for x in out) / len(out)
            print(f"n={len(out)} | avg_KLR={avg_klr:.4f} | avg_ACR={avg_acr:.4f} | avg_PSS={avg_pss:.4f} | avg_PIR={avg_pir:.4f}")

        out_path = pathlib.Path(path).with_suffix(".partial_scores.json")
        out_path.write_text(json.dumps({"source": str(path), "n": len(out), "samples": out}, indent=2, ensure_ascii=False))
        print(f"Saved: {out_path}")
