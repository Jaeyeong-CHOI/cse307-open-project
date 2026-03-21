from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPORTER = ROOT / "scripts" / "export_run_context_event_names.py"


def test_export_outputs_match_shared_schema() -> None:
    out_dir = ROOT / "_build" / "tmp" / "run-context-export-test"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "event-names.json"
    md_path = out_dir / "event-names.md"

    run = subprocess.run(
        [
            "python3",
            str(EXPORTER),
            "--json-output",
            str(json_path),
            "--markdown-output",
            str(md_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stderr
    assert "OK: exported" in run.stdout

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    names = payload["allowed_event_names"]
    assert payload["schema_version"] == "run_context_event_names.v1"
    assert payload["count"] == len(names)
    assert names == sorted(names)
    assert "pull_request_target" in names
    assert "merge_group" in names

    md = md_path.read_text(encoding="utf-8")
    assert "# run_context.event_name allowed values" in md
    for name in names:
        assert f"- `{name}`" in md


if __name__ == "__main__":
    test_export_outputs_match_shared_schema()
    print("OK: run_context schema export regression passed")
