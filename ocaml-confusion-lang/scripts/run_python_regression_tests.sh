#!/usr/bin/env bash
set -euo pipefail

if command -v dune >/dev/null 2>&1; then
  python3 test_roundtrip_report_schema.py
else
  echo "SKIP: test_roundtrip_report_schema.py (dune not found)"
fi

python3 test_batch_report_summary.py
python3 test_taxonomy_profile_schema.py
python3 test_summary_payload_schema.py
python3 test_metric_schema.py
python3 test_generate_metric_snapshot.py
python3 test_emit_ci_result_snapshot.py
python3 test_ci_result_snapshot_schema.py
python3 test_run_context_event_name_schema.py
python3 test_run_context_schema_export.py
python3 test_format_event_name_policy_modes.py
python3 test_resolve_event_name_mode.py
python3 test_resolve_event_name_modes.py
python3 test_task_set_schema.py
python3 test_validator_error_output.py
