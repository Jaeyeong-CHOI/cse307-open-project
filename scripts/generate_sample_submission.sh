#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/demo/submission.json"
cat > "$OUT" <<'JSON'
{
  "note": "리셋 상태: 새 평가 프로토타입 확정 전 임시 파일"
}
JSON
echo "Wrote $OUT"
