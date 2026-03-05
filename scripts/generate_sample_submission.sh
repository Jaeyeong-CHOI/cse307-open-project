#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/demo/submission.json"

# Compile stub and emit JSON
ocamlc -o /tmp/interpreter_stub "$ROOT/src/interpreter_stub.ml"
/tmp/interpreter_stub "40 + 2" > "$OUT"

echo "Wrote $OUT"
