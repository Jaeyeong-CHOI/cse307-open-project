#!/usr/bin/env bash
set -euo pipefail

AVRTG_ENV="/Users/jaeyeong_openclaw/.openclaw/workspace/AVRTG_QUERY_GEN/.env"
if [ ! -f "$AVRTG_ENV" ]; then
  echo "AVRTG env file not found: $AVRTG_ENV" >&2
  exit 1
fi

KEY="$(python3 - <<PY
import pathlib, re
p = pathlib.Path('$AVRTG_ENV')
text = p.read_text()
m = re.search(r'^OPENAI_API_KEY\s*=\s*(.+)$', text, flags=re.M)
print(m.group(1).strip() if m else '')
PY
)"

if [ -z "$KEY" ]; then
  echo "OPENAI_API_KEY not found in $AVRTG_ENV" >&2
  exit 1
fi

export OPENAI_API_KEY="$KEY"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://api.openai.com/v1}"

if [ "$#" -eq 0 ]; then
  python3 - <<'PY'
import os, urllib.request, json
url = os.environ['OPENAI_BASE_URL'].rstrip('/') + '/models'
req = urllib.request.Request(url, headers={'Authorization': f"Bearer {os.environ['OPENAI_API_KEY']}"})
with urllib.request.urlopen(req, timeout=20) as r:
    print('models check: OK', r.status)
print('ready: OPENAI_API_KEY loaded from AVRTG env')
PY
else
  "$@"
fi
