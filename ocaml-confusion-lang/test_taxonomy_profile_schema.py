#!/usr/bin/env python3
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "validate_taxonomy_profiles.py"


def write(path: pathlib.Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        profile_dir = pathlib.Path(td)

        # valid profile
        write(
            profile_dir / "valid.json",
            '{"default_weight": 15, "weights": {"token_stream_mismatch": 40}}\n',
        )
        ok_run = subprocess.run(
            ["python3", str(SCRIPT), "--profile-dir", str(profile_dir)],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        if "OK: validated 1 taxonomy profile file(s)" not in ok_run.stdout:
            raise AssertionError(f"unexpected success output: {ok_run.stdout!r}")

        # invalid profile: non-int default_weight
        write(
            profile_dir / "invalid.json",
            '{"default_weight": "high", "weights": {"line_count_mismatch": 10}}\n',
        )
        bad_run = subprocess.run(
            ["python3", str(SCRIPT), "--profile-dir", str(profile_dir)],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        if bad_run.returncode == 0:
            raise AssertionError("expected non-zero exit for invalid profile schema")
        if "default_weight' must be an integer" not in bad_run.stdout:
            raise AssertionError(f"missing schema error details in output: {bad_run.stdout!r}")

    print("OK: taxonomy profile schema validation regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
