#!/usr/bin/env python3
"""
NL-DSL v0.1 toy parser
- Extracts section/mode/inline token definitions
- Tokenizes known ambiguous connectors
- Resolves token senses via precedence rules
- Emits JSON interpretation log
"""
from __future__ import annotations
import argparse
import json
import re
from dataclasses import dataclass

DEFAULT_DICT = {
    "그리고": "CONSTRAINT_MERGE",
    "또는": "ALT_BRANCH",
    "먼저": "PRIORITY_UP",
    "가능하면": "SOFT_REQUIRE",
    "단": "OVERRIDE_PREV",
    "적어도": "LOWER_BOUND",
    "제외하고": "EXCEPT_FILTER",
    "그대로": "IDENTITY_OP",
    "다만": "CONTEXT_SWITCH",
    "즉": "REWRITE_RULE",
}

SECTION_OVERRIDES = {
    "[계산]": {"그리고": "SEQ_EVAL"},
    "[검증]": {"그리고": "CONSTRAINT_MERGE"},
    "[제약]": {"그리고": "CONSTRAINT_MERGE"},
}

MODE_OVERRIDES = {
    "@mode:eval": {"먼저": "PRE_STEP"},
    "@mode:type": {"먼저": "PRIORITY_UP"},
}

TOKENS = sorted(DEFAULT_DICT.keys(), key=len, reverse=True)
DEF_RE = re.compile(r"define\s+token\s+(\S+)\s+as\s+(\S+)")

@dataclass
class Context:
    section: str | None = None
    mode: str | None = None
    user_defs: dict[str, str] = None

    def __post_init__(self):
        if self.user_defs is None:
            self.user_defs = {}


def parse(text: str, seed_overrides: dict[str, str] | None = None):
    ctx = Context()
    logs = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    for ln in lines:
        if ln in ("[계산]", "[검증]", "[제약]"):
            ctx.section = ln
            continue
        if ln in ("@mode:eval", "@mode:type"):
            ctx.mode = ln
            continue
        m = DEF_RE.match(ln)
        if m:
            tok, sense = m.group(1), m.group(2)
            ctx.user_defs[tok] = sense
            continue

        for tok in TOKENS:
            start = 0
            while True:
                idx = ln.find(tok, start)
                if idx == -1:
                    break
                sense, rule = resolve(tok, ctx, seed_overrides or {})
                logs.append({
                    "line": ln,
                    "token": tok,
                    "sense": sense,
                    "rule": rule,
                    "section": ctx.section,
                    "mode": ctx.mode,
                    "span": [idx, idx + len(tok)],
                })
                start = idx + len(tok)

    return {
        "section": ctx.section,
        "mode": ctx.mode,
        "user_defs": ctx.user_defs,
        "interpretation_log": logs,
    }


def resolve(tok: str, ctx: Context, seed_overrides: dict[str, str]):
    # 1) section
    if ctx.section and tok in SECTION_OVERRIDES.get(ctx.section, {}):
        return SECTION_OVERRIDES[ctx.section][tok], f"Section>{ctx.section}"
    # 2) mode
    if ctx.mode and tok in MODE_OVERRIDES.get(ctx.mode, {}):
        return MODE_OVERRIDES[ctx.mode][tok], f"Mode>{ctx.mode}"
    # 3) user define
    if tok in ctx.user_defs:
        return ctx.user_defs[tok], "UserDefine"
    # 4) seed dict
    if tok in seed_overrides:
        return seed_overrides[tok], "SeedOverride"
    # 5) default
    return DEFAULT_DICT.get(tok, "UNKNOWN"), "Default"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Path to NL-DSL text")
    ap.add_argument("--seed-dict", help="Optional JSON file {token: sense}")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    seed = {}
    if args.seed_dict:
        with open(args.seed_dict, "r", encoding="utf-8") as f:
            seed = json.load(f)

    out = parse(text, seed)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
