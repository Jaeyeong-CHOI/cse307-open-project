#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/demo/submission.json"

if command -v ocamlc >/dev/null 2>&1; then
  ocamlc -o /tmp/interpreter_stub "$ROOT/src/interpreter_stub.ml"
  /tmp/interpreter_stub "40 + 2" > "$OUT"
  echo "Wrote $OUT (generated via ocamlc)"
else
  cat > "$OUT" <<'JSON'
{
  "expr": "40 + 2",
  "output": 42,
  "trace": [
    {"event":"EvalStart","node":"expr"},
    {"event":"UserEmit","tag":"checkpoint","value":1},
    {"event":"EvalEnd","node":"expr","value":42}
  ]
}
JSON
  echo "Wrote $OUT (fallback JSON; ocamlc not installed)"
fi
