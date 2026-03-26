#!/usr/bin/env python3
"""Wrapper: injects API key then runs run_l1_factorial.py main()"""
import pathlib, re, os, sys

p = pathlib.Path('/Users/jaeyeong_openclaw/.openclaw/workspace/AVRTG_QUERY_GEN/.env')
text = p.read_text()
m = re.search(r'^OPENAI_API_KEY\s*=\s*(.+)$', text, flags=re.M)
key = m.group(1).strip() if m else ''
if not key:
    print("ERROR: OPENAI_API_KEY not found in AVRTG env", file=sys.stderr)
    sys.exit(1)
os.environ['OPENAI_API_KEY'] = key
print(f"API key loaded (len={len(key)})")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import run_l1_factorial
run_l1_factorial.main()
