#!/usr/bin/env python3
import json
import pathlib
import re
import socket
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "build_batch_eval_plan.py"
TASK_SET = ROOT / "examples" / "task-set-v1.json"
OUT = ROOT / "_build" / "batch-summary-test"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    output = OUT / "batch-plan.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro,gpt-5-mini",
            "--prompt-conditions",
            "base,strict,base",
            "--repeats",
            "2",
            "--cheap-first",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    config = payload["config"]
    summary = payload["summary"]

    if config["models"] != ["gpt-5-mini", "gpt-5-pro"]:
        raise AssertionError(f"unexpected model order/dedup: {config['models']}")
    if config["prompt_conditions"] != ["base", "strict"]:
        raise AssertionError(f"unexpected prompt_condition dedup: {config['prompt_conditions']}")

    expected_total = 3 * 2 * 2 * 2  # tasks * models * conditions * repeats
    if summary["planned_runs_total"] != expected_total:
        raise AssertionError(
            f"expected planned_runs_total={expected_total}, got {summary['planned_runs_total']}"
        )
    if summary["planned_runs_by_model"] != {"gpt-5-mini": 12, "gpt-5-pro": 12}:
        raise AssertionError(
            f"unexpected planned_runs_by_model: {summary['planned_runs_by_model']}"
        )
    if summary["planned_runs_by_prompt_condition"] != {"base": 12, "strict": 12}:
        raise AssertionError(
            "unexpected planned_runs_by_prompt_condition: "
            f"{summary['planned_runs_by_prompt_condition']}"
        )
    if summary["planned_runs_by_task"] != {
        "sample-basic-loop": 8,
        "protected-literals": 8,
        "triple-quote-stress": 8,
    }:
        raise AssertionError(
            f"unexpected planned_runs_by_task: {summary['planned_runs_by_task']}"
        )
    if summary["planned_runs_by_model_prompt_condition"] != {
        "gpt-5-mini": {"base": 6, "strict": 6},
        "gpt-5-pro": {"base": 6, "strict": 6},
    }:
        raise AssertionError(
            "unexpected planned_runs_by_model_prompt_condition: "
            f"{summary['planned_runs_by_model_prompt_condition']}"
        )
    if summary["planned_runs_by_task_model"] != {
        "sample-basic-loop": {"gpt-5-mini": 4, "gpt-5-pro": 4},
        "protected-literals": {"gpt-5-mini": 4, "gpt-5-pro": 4},
        "triple-quote-stress": {"gpt-5-mini": 4, "gpt-5-pro": 4},
    }:
        raise AssertionError(
            f"unexpected planned_runs_by_task_model: {summary['planned_runs_by_task_model']}"
        )
    if summary["planned_runs_by_task_prompt_condition"] != {
        "sample-basic-loop": {"base": 4, "strict": 4},
        "protected-literals": {"base": 4, "strict": 4},
        "triple-quote-stress": {"base": 4, "strict": 4},
    }:
        raise AssertionError(
            "unexpected planned_runs_by_task_prompt_condition: "
            f"{summary['planned_runs_by_task_prompt_condition']}"
        )
    if summary["potential_runs_total"] != expected_total or summary["skipped_runs_total"] != 0:
        raise AssertionError(
            "expected uncapped run counters to match planned total: "
            f"{summary['potential_runs_total']=}, {summary['skipped_runs_total']=}"
        )
    if summary.get("planned_run_ratio_total") != 1.0:
        raise AssertionError(
            f"expected planned_run_ratio_total=1.0, got {summary.get('planned_run_ratio_total')}"
        )
    if summary.get("planned_run_ratio_by_model") != {"gpt-5-mini": 1.0, "gpt-5-pro": 1.0}:
        raise AssertionError(
            f"unexpected planned_run_ratio_by_model: {summary.get('planned_run_ratio_by_model')}"
        )
    if summary.get("planned_run_ratio_by_prompt_condition") != {"base": 1.0, "strict": 1.0}:
        raise AssertionError(
            "unexpected planned_run_ratio_by_prompt_condition: "
            f"{summary.get('planned_run_ratio_by_prompt_condition')}"
        )
    if summary["potential_runs_by_model"] != {"gpt-5-mini": 12, "gpt-5-pro": 12}:
        raise AssertionError(
            f"unexpected potential_runs_by_model: {summary['potential_runs_by_model']}"
        )
    if summary["potential_runs_by_prompt_condition"] != {"base": 12, "strict": 12}:
        raise AssertionError(
            "unexpected potential_runs_by_prompt_condition: "
            f"{summary['potential_runs_by_prompt_condition']}"
        )
    if summary["potential_runs_by_task"] != {
        "sample-basic-loop": 8,
        "protected-literals": 8,
        "triple-quote-stress": 8,
    }:
        raise AssertionError(
            f"unexpected potential_runs_by_task: {summary['potential_runs_by_task']}"
        )
    if summary["potential_runs_by_model_prompt_condition"] != {
        "gpt-5-mini": {"base": 6, "strict": 6},
        "gpt-5-pro": {"base": 6, "strict": 6},
    }:
        raise AssertionError(
            "unexpected potential_runs_by_model_prompt_condition: "
            f"{summary['potential_runs_by_model_prompt_condition']}"
        )
    if summary["potential_runs_by_task_model"] != {
        "sample-basic-loop": {"gpt-5-mini": 4, "gpt-5-pro": 4},
        "protected-literals": {"gpt-5-mini": 4, "gpt-5-pro": 4},
        "triple-quote-stress": {"gpt-5-mini": 4, "gpt-5-pro": 4},
    }:
        raise AssertionError(
            "unexpected potential_runs_by_task_model: "
            f"{summary['potential_runs_by_task_model']}"
        )
    if summary["potential_runs_by_task_prompt_condition"] != {
        "sample-basic-loop": {"base": 4, "strict": 4},
        "protected-literals": {"base": 4, "strict": 4},
        "triple-quote-stress": {"base": 4, "strict": 4},
    }:
        raise AssertionError(
            "unexpected potential_runs_by_task_prompt_condition: "
            f"{summary['potential_runs_by_task_prompt_condition']}"
        )
    if summary["skipped_runs_by_model"] != {"gpt-5-mini": 0, "gpt-5-pro": 0}:
        raise AssertionError(
            f"unexpected skipped_runs_by_model: {summary['skipped_runs_by_model']}"
        )
    if summary["skipped_runs_by_prompt_condition"] != {"base": 0, "strict": 0}:
        raise AssertionError(
            "unexpected skipped_runs_by_prompt_condition: "
            f"{summary['skipped_runs_by_prompt_condition']}"
        )
    if summary["skipped_runs_by_task"] != {
        "sample-basic-loop": 0,
        "protected-literals": 0,
        "triple-quote-stress": 0,
    }:
        raise AssertionError(
            f"unexpected skipped_runs_by_task: {summary['skipped_runs_by_task']}"
        )
    if summary["skipped_runs_by_model_prompt_condition"] != {
        "gpt-5-mini": {"base": 0, "strict": 0},
        "gpt-5-pro": {"base": 0, "strict": 0},
    }:
        raise AssertionError(
            "unexpected skipped_runs_by_model_prompt_condition: "
            f"{summary['skipped_runs_by_model_prompt_condition']}"
        )
    if summary["skipped_runs_by_task_model"] != {
        "sample-basic-loop": {"gpt-5-mini": 0, "gpt-5-pro": 0},
        "protected-literals": {"gpt-5-mini": 0, "gpt-5-pro": 0},
        "triple-quote-stress": {"gpt-5-mini": 0, "gpt-5-pro": 0},
    }:
        raise AssertionError(
            "unexpected skipped_runs_by_task_model: "
            f"{summary['skipped_runs_by_task_model']}"
        )
    if summary["skipped_runs_by_task_prompt_condition"] != {
        "sample-basic-loop": {"base": 0, "strict": 0},
        "protected-literals": {"base": 0, "strict": 0},
        "triple-quote-stress": {"base": 0, "strict": 0},
    }:
        raise AssertionError(
            "unexpected skipped_runs_by_task_prompt_condition: "
            f"{summary['skipped_runs_by_task_prompt_condition']}"
        )
    if summary["planned_runs_by_repeat_index"] != {"1": 12, "2": 12}:
        raise AssertionError(
            f"unexpected planned_runs_by_repeat_index: {summary['planned_runs_by_repeat_index']}"
        )
    if summary["potential_runs_by_repeat_index"] != {"1": 12, "2": 12}:
        raise AssertionError(
            f"unexpected potential_runs_by_repeat_index: {summary['potential_runs_by_repeat_index']}"
        )
    if summary["skipped_runs_by_repeat_index"] != {"1": 0, "2": 0}:
        raise AssertionError(
            f"unexpected skipped_runs_by_repeat_index: {summary['skipped_runs_by_repeat_index']}"
        )
    if summary.get("planned_run_ratio_by_repeat_index") != {"1": 1.0, "2": 1.0}:
        raise AssertionError(
            "unexpected planned_run_ratio_by_repeat_index: "
            f"{summary.get('planned_run_ratio_by_repeat_index')}"
        )

    capped = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--prompt-conditions",
            "base,strict",
            "--repeats",
            "2",
            "--max-total-runs",
            "10",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if capped.returncode == 0:
        raise AssertionError("expected max-total-runs cap violation to fail")

    capped_mode_output = OUT / "batch-plan.max-total-cap-mode.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--prompt-conditions",
            "base,strict",
            "--repeats",
            "2",
            "--cheap-first",
            "--max-total-runs",
            "10",
            "--max-total-runs-mode",
            "cap",
            "--output",
            str(capped_mode_output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    capped_mode_payload = json.loads(capped_mode_output.read_text(encoding="utf-8"))
    capped_mode_summary = capped_mode_payload["summary"]
    if capped_mode_payload["config"].get("max_total_runs_mode") != "cap":
        raise AssertionError("expected max_total_runs_mode=cap in config")
    if capped_mode_summary["planned_runs_total"] != 10:
        raise AssertionError(
            f"expected max-total-runs cap mode planned total=10, got {capped_mode_summary['planned_runs_total']}"
        )
    if abs(capped_mode_summary.get("planned_run_ratio_total", 0.0) - round(10 / 24, 6)) > 1e-9:
        raise AssertionError(
            "unexpected capped planned_run_ratio_total: "
            f"{capped_mode_summary.get('planned_run_ratio_total')}"
        )
    if capped_mode_summary["planned_runs_by_repeat_index"] != {"1": 6, "2": 4}:
        raise AssertionError(
            "unexpected capped planned_runs_by_repeat_index: "
            f"{capped_mode_summary['planned_runs_by_repeat_index']}"
        )
    if capped_mode_summary["skipped_runs_by_repeat_index"] != {"1": 6, "2": 8}:
        raise AssertionError(
            "unexpected capped skipped_runs_by_repeat_index: "
            f"{capped_mode_summary['skipped_runs_by_repeat_index']}"
        )

    per_model_capped_output = OUT / "batch-plan.per-model-capped.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--prompt-conditions",
            "base,strict",
            "--repeats",
            "3",
            "--max-runs-per-model",
            "5",
            "--cheap-first",
            "--output",
            str(per_model_capped_output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    per_model_capped_payload = json.loads(per_model_capped_output.read_text(encoding="utf-8"))
    per_model_summary = per_model_capped_payload["summary"]
    if per_model_summary["planned_runs_total"] != 10:
        raise AssertionError(
            f"expected per-model capped total=10, got {per_model_summary['planned_runs_total']}"
        )
    if per_model_summary["planned_runs_by_model"] != {"gpt-5-mini": 5, "gpt-5-pro": 5}:
        raise AssertionError(
            "unexpected per-model capped runs_by_model: "
            f"{per_model_summary['planned_runs_by_model']}"
        )
    if per_model_summary["planned_runs_by_prompt_condition"] != {"base": 10, "strict": 0}:
        raise AssertionError(
            "unexpected per-model capped runs_by_prompt_condition: "
            f"{per_model_summary['planned_runs_by_prompt_condition']}"
        )
    if per_model_summary["planned_runs_by_model_prompt_condition"] != {
        "gpt-5-mini": {"base": 5, "strict": 0},
        "gpt-5-pro": {"base": 5, "strict": 0},
    }:
        raise AssertionError(
            "unexpected per-model capped planned_runs_by_model_prompt_condition: "
            f"{per_model_summary['planned_runs_by_model_prompt_condition']}"
        )
    if per_model_summary["potential_runs_total"] != 36:
        raise AssertionError(
            f"expected per-model potential total=36, got {per_model_summary['potential_runs_total']}"
        )
    if per_model_summary["skipped_runs_total"] != 26:
        raise AssertionError(
            f"expected per-model skipped total=26, got {per_model_summary['skipped_runs_total']}"
        )
    if abs(per_model_summary.get("planned_run_ratio_total", 0.0) - round(10 / 36, 6)) > 1e-9:
        raise AssertionError(
            "unexpected per-model planned_run_ratio_total: "
            f"{per_model_summary.get('planned_run_ratio_total')}"
        )
    expected_per_model_ratio = round(5 / 18, 6)
    if per_model_summary.get("planned_run_ratio_by_model") != {
        "gpt-5-mini": expected_per_model_ratio,
        "gpt-5-pro": expected_per_model_ratio,
    }:
        raise AssertionError(
            "unexpected per-model planned_run_ratio_by_model: "
            f"{per_model_summary.get('planned_run_ratio_by_model')}"
        )
    if per_model_summary["skipped_runs_by_model"] != {"gpt-5-mini": 13, "gpt-5-pro": 13}:
        raise AssertionError(
            "unexpected per-model capped skipped_runs_by_model: "
            f"{per_model_summary['skipped_runs_by_model']}"
        )
    if per_model_summary["potential_runs_by_prompt_condition"] != {"base": 18, "strict": 18}:
        raise AssertionError(
            "unexpected per-model capped potential_runs_by_prompt_condition: "
            f"{per_model_summary['potential_runs_by_prompt_condition']}"
        )
    if per_model_summary["potential_runs_by_model_prompt_condition"] != {
        "gpt-5-mini": {"base": 9, "strict": 9},
        "gpt-5-pro": {"base": 9, "strict": 9},
    }:
        raise AssertionError(
            "unexpected per-model capped potential_runs_by_model_prompt_condition: "
            f"{per_model_summary['potential_runs_by_model_prompt_condition']}"
        )
    if per_model_summary["skipped_runs_by_prompt_condition"] != {"base": 8, "strict": 18}:
        raise AssertionError(
            "unexpected per-model capped skipped_runs_by_prompt_condition: "
            f"{per_model_summary['skipped_runs_by_prompt_condition']}"
        )
    if per_model_summary["skipped_runs_by_model_prompt_condition"] != {
        "gpt-5-mini": {"base": 4, "strict": 9},
        "gpt-5-pro": {"base": 4, "strict": 9},
    }:
        raise AssertionError(
            "unexpected per-model capped skipped_runs_by_model_prompt_condition: "
            f"{per_model_summary['skipped_runs_by_model_prompt_condition']}"
        )


    per_prompt_capped_output = OUT / "batch-plan.per-prompt-capped.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--prompt-conditions",
            "base,strict",
            "--repeats",
            "3",
            "--max-runs-per-prompt-condition",
            "5",
            "--cheap-first",
            "--output",
            str(per_prompt_capped_output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    per_prompt_capped_payload = json.loads(per_prompt_capped_output.read_text(encoding="utf-8"))
    per_prompt_summary = per_prompt_capped_payload["summary"]
    if per_prompt_summary["planned_runs_total"] != 10:
        raise AssertionError(
            f"expected per-prompt capped total=10, got {per_prompt_summary['planned_runs_total']}"
        )
    if per_prompt_summary["planned_runs_by_prompt_condition"] != {"base": 5, "strict": 5}:
        raise AssertionError(
            "unexpected per-prompt capped runs_by_prompt_condition: "
            f"{per_prompt_summary['planned_runs_by_prompt_condition']}"
        )
    if per_prompt_summary["planned_runs_by_model"] != {"gpt-5-mini": 6, "gpt-5-pro": 4}:
        raise AssertionError(
            "unexpected per-prompt capped runs_by_model: "
            f"{per_prompt_summary['planned_runs_by_model']}"
        )
    if per_prompt_summary["planned_runs_by_model_prompt_condition"] != {
        "gpt-5-mini": {"base": 3, "strict": 3},
        "gpt-5-pro": {"base": 2, "strict": 2},
    }:
        raise AssertionError(
            "unexpected per-prompt capped planned_runs_by_model_prompt_condition: "
            f"{per_prompt_summary['planned_runs_by_model_prompt_condition']}"
        )
    if per_prompt_summary["skipped_runs_by_prompt_condition"] != {"base": 13, "strict": 13}:
        raise AssertionError(
            "unexpected per-prompt capped skipped_runs_by_prompt_condition: "
            f"{per_prompt_summary['skipped_runs_by_prompt_condition']}"
        )

    fair_per_prompt_output = OUT / "batch-plan.per-prompt-capped.fair.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--prompt-conditions",
            "base,strict",
            "--repeats",
            "3",
            "--max-runs-per-prompt-condition",
            "5",
            "--cheap-first",
            "--fair-model-allocation",
            "--output",
            str(fair_per_prompt_output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    fair_per_prompt_payload = json.loads(fair_per_prompt_output.read_text(encoding="utf-8"))
    fair_per_prompt_summary = fair_per_prompt_payload["summary"]
    if fair_per_prompt_payload["config"].get("fair_model_allocation") is not True:
        raise AssertionError("expected fair_model_allocation=true in config")
    if fair_per_prompt_summary["planned_runs_by_model"] != {"gpt-5-mini": 5, "gpt-5-pro": 5}:
        raise AssertionError(
            "unexpected fair per-prompt runs_by_model: "
            f"{fair_per_prompt_summary['planned_runs_by_model']}"
        )
    if fair_per_prompt_summary["planned_runs_by_model_prompt_condition"] != {
        "gpt-5-mini": {"base": 3, "strict": 2},
        "gpt-5-pro": {"base": 2, "strict": 3},
    }:
        raise AssertionError(
            "unexpected fair per-prompt planned_runs_by_model_prompt_condition: "
            f"{fair_per_prompt_summary['planned_runs_by_model_prompt_condition']}"
        )

    per_task_capped_output = OUT / "batch-plan.per-task-capped.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--prompt-conditions",
            "base,strict",
            "--repeats",
            "3",
            "--max-runs-per-task",
            "4",
            "--cheap-first",
            "--output",
            str(per_task_capped_output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    per_task_capped_payload = json.loads(per_task_capped_output.read_text(encoding="utf-8"))
    per_task_summary = per_task_capped_payload["summary"]
    if per_task_summary["planned_runs_total"] != 12:
        raise AssertionError(
            f"expected per-task capped total=12, got {per_task_summary['planned_runs_total']}"
        )
    if per_task_summary["planned_runs_by_task"] != {
        "sample-basic-loop": 4,
        "protected-literals": 4,
        "triple-quote-stress": 4,
    }:
        raise AssertionError(
            "unexpected per-task capped planned_runs_by_task: "
            f"{per_task_summary['planned_runs_by_task']}"
        )
    if per_task_summary["skipped_runs_by_task"] != {
        "sample-basic-loop": 8,
        "protected-literals": 8,
        "triple-quote-stress": 8,
    }:
        raise AssertionError(
            "unexpected per-task capped skipped_runs_by_task: "
            f"{per_task_summary['skipped_runs_by_task']}"
        )

    per_task_model_capped_output = OUT / "batch-plan.per-task-model-capped.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--prompt-conditions",
            "base,strict",
            "--repeats",
            "3",
            "--max-runs-per-task-model",
            "2",
            "--cheap-first",
            "--output",
            str(per_task_model_capped_output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    per_task_model_capped_payload = json.loads(per_task_model_capped_output.read_text(encoding="utf-8"))
    per_task_model_summary = per_task_model_capped_payload["summary"]
    if per_task_model_summary["planned_runs_total"] != 12:
        raise AssertionError(
            "unexpected per-task-model capped total: "
            f"{per_task_model_summary['planned_runs_total']}"
        )
    if per_task_model_summary["planned_runs_by_task_model"] != {
        "sample-basic-loop": {"gpt-5-mini": 2, "gpt-5-pro": 2},
        "protected-literals": {"gpt-5-mini": 2, "gpt-5-pro": 2},
        "triple-quote-stress": {"gpt-5-mini": 2, "gpt-5-pro": 2},
    }:
        raise AssertionError(
            "unexpected per-task-model capped planned_runs_by_task_model: "
            f"{per_task_model_summary['planned_runs_by_task_model']}"
        )
    if per_task_model_summary["skipped_runs_by_task_model"] != {
        "sample-basic-loop": {"gpt-5-mini": 4, "gpt-5-pro": 4},
        "protected-literals": {"gpt-5-mini": 4, "gpt-5-pro": 4},
        "triple-quote-stress": {"gpt-5-mini": 4, "gpt-5-pro": 4},
    }:
        raise AssertionError(
            "unexpected per-task-model capped skipped_runs_by_task_model: "
            f"{per_task_model_summary['skipped_runs_by_task_model']}"
        )

    per_task_prompt_capped_output = OUT / "batch-plan.per-task-prompt-capped.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--prompt-conditions",
            "base,strict",
            "--repeats",
            "2",
            "--max-runs-per-task-prompt-condition",
            "3",
            "--cheap-first",
            "--output",
            str(per_task_prompt_capped_output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    per_task_prompt_payload = json.loads(per_task_prompt_capped_output.read_text(encoding="utf-8"))
    per_task_prompt_summary = per_task_prompt_payload["summary"]
    if per_task_prompt_payload["config"].get("max_runs_per_task_prompt_condition") != 3:
        raise AssertionError("expected max_runs_per_task_prompt_condition=3 in config")
    if per_task_prompt_summary["planned_runs_total"] != 18:
        raise AssertionError(
            "unexpected per-task-prompt capped total: "
            f"{per_task_prompt_summary['planned_runs_total']}"
        )
    if per_task_prompt_summary["planned_runs_by_task_prompt_condition"] != {
        "sample-basic-loop": {"base": 3, "strict": 3},
        "protected-literals": {"base": 3, "strict": 3},
        "triple-quote-stress": {"base": 3, "strict": 3},
    }:
        raise AssertionError(
            "unexpected per-task-prompt capped planned_runs_by_task_prompt_condition: "
            f"{per_task_prompt_summary['planned_runs_by_task_prompt_condition']}"
        )
    if per_task_prompt_summary["planned_runs_by_model"] != {"gpt-5-mini": 12, "gpt-5-pro": 6}:
        raise AssertionError(
            "unexpected per-task-prompt capped planned_runs_by_model: "
            f"{per_task_prompt_summary['planned_runs_by_model']}"
        )
    if per_task_prompt_summary["skipped_runs_by_task_prompt_condition"] != {
        "sample-basic-loop": {"base": 1, "strict": 1},
        "protected-literals": {"base": 1, "strict": 1},
        "triple-quote-stress": {"base": 1, "strict": 1},
    }:
        raise AssertionError(
            "unexpected per-task-prompt capped skipped_runs_by_task_prompt_condition: "
            f"{per_task_prompt_summary['skipped_runs_by_task_prompt_condition']}"
        )

    fair_per_task_prompt_capped_output = OUT / "batch-plan.per-task-prompt-capped.fair.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--prompt-conditions",
            "base,strict",
            "--repeats",
            "2",
            "--max-runs-per-task-prompt-condition",
            "3",
            "--cheap-first",
            "--fair-model-allocation",
            "--output",
            str(fair_per_task_prompt_capped_output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    fair_per_task_prompt_payload = json.loads(fair_per_task_prompt_capped_output.read_text(encoding="utf-8"))
    fair_per_task_prompt_summary = fair_per_task_prompt_payload["summary"]
    if fair_per_task_prompt_summary["planned_runs_by_model"] != {"gpt-5-mini": 9, "gpt-5-pro": 9}:
        raise AssertionError(
            "unexpected fair per-task-prompt planned_runs_by_model: "
            f"{fair_per_task_prompt_summary['planned_runs_by_model']}"
        )

    preset_list = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names = [line.strip() for line in preset_list.stdout.splitlines() if line.strip()]
    if preset_names != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(f"unexpected preset list output: {preset_names}")

    preset_list_limited = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_limited = [line.strip() for line in preset_list_limited.stdout.splitlines() if line.strip()]
    if preset_names_limited != ["balanced-ci", "full-analysis"]:
        raise AssertionError(f"unexpected limited preset list output: {preset_names_limited}")

    preset_list_tag_filtered = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-tag",
            "smoke,cheap-first",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_tag_filtered = [
        line.strip() for line in preset_list_tag_filtered.stdout.splitlines() if line.strip()
    ]
    if preset_names_tag_filtered != ["quick-smoke"]:
        raise AssertionError(
            f"unexpected tag-filtered preset names: {preset_names_tag_filtered}"
        )

    preset_list_json = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_list_payload = json.loads(preset_list_json.stdout)
    if preset_list_payload.get("schema_version") != "v1":
        raise AssertionError(f"unexpected preset list schema_version: {preset_list_payload.get('schema_version')}")
    listed_presets = preset_list_payload.get("presets")
    if not isinstance(listed_presets, dict) or "quick-smoke" not in listed_presets:
        raise AssertionError(f"unexpected preset list json payload: {preset_list_payload}")
    if preset_list_payload.get("filtered_count") != 3:
        raise AssertionError(f"unexpected filtered_count in preset json payload: {preset_list_payload}")
    if preset_list_payload.get("emitted_count") != 3:
        raise AssertionError(f"unexpected emitted_count in preset json payload: {preset_list_payload}")
    if preset_list_payload.get("truncated") is not False:
        raise AssertionError(f"unexpected truncated flag in preset json payload: {preset_list_payload}")

    preset_list_json_tag_filtered = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "json",
            "--list-presets-tag",
            "SMOKE",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_list_json_tag_filtered_payload = json.loads(preset_list_json_tag_filtered.stdout)
    if sorted(preset_list_json_tag_filtered_payload.get("presets", {}).keys()) != ["quick-smoke"]:
        raise AssertionError(
            "unexpected tag-filtered preset json payload: "
            f"{preset_list_json_tag_filtered_payload}"
        )

    preset_list_json_limited = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "json",
            "--list-presets-limit",
            "2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_list_json_limited_payload = json.loads(preset_list_json_limited.stdout)
    if sorted(preset_list_json_limited_payload.get("presets", {}).keys()) != [
        "balanced-ci",
        "full-analysis",
    ]:
        raise AssertionError(
            "unexpected limited preset json payload: "
            f"{preset_list_json_limited_payload}"
        )
    if preset_list_json_limited_payload.get("filtered_count") != 3:
        raise AssertionError(
            "unexpected filtered_count for limited preset json payload: "
            f"{preset_list_json_limited_payload}"
        )
    if preset_list_json_limited_payload.get("emitted_count") != 2:
        raise AssertionError(
            "unexpected emitted_count for limited preset json payload: "
            f"{preset_list_json_limited_payload}"
        )
    if preset_list_json_limited_payload.get("truncated") is not True:
        raise AssertionError(
            "unexpected truncated flag for limited preset json payload: "
            f"{preset_list_json_limited_payload}"
        )

    preset_list_json_tag_filtered_any = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "json",
            "--list-presets-tag",
            "cheap-first,analysis",
            "--list-presets-tag-match",
            "any",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_list_json_tag_filtered_any_payload = json.loads(preset_list_json_tag_filtered_any.stdout)
    if sorted(preset_list_json_tag_filtered_any_payload.get("presets", {}).keys()) != [
        "balanced-ci",
        "full-analysis",
        "quick-smoke",
    ]:
        raise AssertionError(
            "unexpected tag-filtered(any) preset json payload: "
            f"{preset_list_json_tag_filtered_any_payload}"
        )

    preset_list_resolved_json = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "resolved-json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_list_resolved_payload = json.loads(preset_list_resolved_json.stdout)
    resolved_presets = preset_list_resolved_payload.get("presets")
    if not isinstance(resolved_presets, dict) or "quick-smoke" not in resolved_presets:
        raise AssertionError(f"unexpected resolved-json payload: {preset_list_resolved_payload}")
    if preset_list_resolved_payload.get("filtered_count") != 3:
        raise AssertionError(
            f"unexpected filtered_count in resolved-json payload: {preset_list_resolved_payload}"
        )
    if preset_list_resolved_payload.get("emitted_count") != 3:
        raise AssertionError(
            f"unexpected emitted_count in resolved-json payload: {preset_list_resolved_payload}"
        )
    if preset_list_resolved_payload.get("truncated") is not False:
        raise AssertionError(f"unexpected truncated flag in resolved-json payload: {preset_list_resolved_payload}")
    quick_smoke_resolved = resolved_presets["quick-smoke"]
    if quick_smoke_resolved.get("max_runs_per_task_prompt_condition") != 0:
        raise AssertionError(
            "expected default max_runs_per_task_prompt_condition=0 in resolved-json output, "
            f"got {quick_smoke_resolved}"
        )
    if quick_smoke_resolved.get("description") != "Fast sanity check with minimal cost.":
        raise AssertionError(f"expected resolved description in preset payload, got: {quick_smoke_resolved}")
    if quick_smoke_resolved.get("tags") != ["cheap-first", "smoke"]:
        raise AssertionError(f"expected resolved tags in preset payload, got: {quick_smoke_resolved}")

    preset_list_resolved_json_limited = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "resolved-json",
            "--list-presets-limit",
            "2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_list_resolved_json_limited_payload = json.loads(preset_list_resolved_json_limited.stdout)
    resolved_presets_limited = preset_list_resolved_json_limited_payload.get("presets")
    if not isinstance(resolved_presets_limited, dict) or sorted(resolved_presets_limited.keys()) != [
        "balanced-ci",
        "full-analysis",
    ]:
        raise AssertionError(
            "unexpected limited resolved-json payload: "
            f"{preset_list_resolved_json_limited_payload}"
        )
    if preset_list_resolved_json_limited_payload.get("filtered_count") != 3:
        raise AssertionError(
            "unexpected filtered_count for limited resolved-json payload: "
            f"{preset_list_resolved_json_limited_payload}"
        )
    if preset_list_resolved_json_limited_payload.get("emitted_count") != 2:
        raise AssertionError(
            "unexpected emitted_count for limited resolved-json payload: "
            f"{preset_list_resolved_json_limited_payload}"
        )
    if preset_list_resolved_json_limited_payload.get("truncated") is not True:
        raise AssertionError(
            "unexpected truncated flag for limited resolved-json payload: "
            f"{preset_list_resolved_json_limited_payload}"
        )

    preset_list_names_with_meta = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_lines = [line.strip() for line in preset_list_names_with_meta.stdout.splitlines() if line.strip()]
    if names_with_meta_lines[-1] != "# meta\tschema=planner_preset_list_meta.v1\tfiltered_count=3\temitted_count=2\ttruncated=true":
        raise AssertionError(f"unexpected names-with-meta footer: {names_with_meta_lines}")

    preset_list_names_with_meta_custom_schema = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-schema-id",
            "planner_preset_list_meta.v2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_custom_schema_lines = [
        line.strip() for line in preset_list_names_with_meta_custom_schema.stdout.splitlines() if line.strip()
    ]
    if names_with_meta_custom_schema_lines[-1] != (
        "# meta\tschema=planner_preset_list_meta.v2\tfiltered_count=3\temitted_count=2\ttruncated=true"
    ):
        raise AssertionError(
            f"unexpected names-with-meta custom schema footer: {names_with_meta_custom_schema_lines}"
        )

    preset_list_names_with_meta_json = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_json_lines = [
        line.strip() for line in preset_list_names_with_meta_json.stdout.splitlines() if line.strip()
    ]
    names_meta_payload = json.loads(names_with_meta_json_lines[-1])
    if names_meta_payload != {
        "meta": True,
        "schema_version": "v1",
        "schema": "planner_preset_list_meta.v1",
        "filtered_count": "3",
        "emitted_count": "2",
        "truncated": "true",
    }:
        raise AssertionError(f"unexpected names-with-meta json payload: {names_meta_payload}")

    preset_list_names_with_meta_json_schema_v2 = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-format",
            "json",
            "--list-presets-meta-json-schema-version",
            "v2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_meta_payload_v2 = json.loads(
        [line.strip() for line in preset_list_names_with_meta_json_schema_v2.stdout.splitlines() if line.strip()][-1]
    )
    if names_meta_payload_v2.get("schema_version") != "v2":
        raise AssertionError(f"expected schema_version=v2 in list-presets json meta payload: {names_meta_payload_v2}")

    preset_list_names_with_meta_generated_at = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-generated-at",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_generated_at_lines = [
        line.strip() for line in preset_list_names_with_meta_generated_at.stdout.splitlines() if line.strip()
    ]
    names_with_meta_generated_at_footer = names_with_meta_generated_at_lines[-1]
    if not names_with_meta_generated_at_footer.startswith(
        "# meta\tschema=planner_preset_list_meta.v1\tfiltered_count=3\temitted_count=2\ttruncated=true\tgenerated_at_utc="
    ):
        raise AssertionError(
            f"unexpected names-with-meta generated_at footer: {names_with_meta_generated_at_lines}"
        )
    generated_at_value = names_with_meta_generated_at_footer.rsplit("generated_at_utc=", 1)[-1]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", generated_at_value) is None:
        raise AssertionError(
            "unexpected generated_at_utc timestamp format in list-presets meta footer: "
            f"{generated_at_value}"
        )

    preset_list_names_with_meta_cwd = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-cwd",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_cwd_lines = [
        line.strip() for line in preset_list_names_with_meta_cwd.stdout.splitlines() if line.strip()
    ]
    if f"\tcwd={ROOT}" not in names_with_meta_cwd_lines[-1]:
        raise AssertionError(f"missing cwd in list-presets meta footer: {names_with_meta_cwd_lines}")

    preset_list_names_with_meta_python_version = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-python-version",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_python_version_lines = [
        line.strip() for line in preset_list_names_with_meta_python_version.stdout.splitlines() if line.strip()
    ]
    python_version_value = names_with_meta_python_version_lines[-1].rsplit("python_version=", 1)[-1]
    if re.fullmatch(r"\d+\.\d+\.\d+", python_version_value) is None:
        raise AssertionError(
            "unexpected python_version format in list-presets meta footer: "
            f"{names_with_meta_python_version_lines}"
        )

    preset_list_names_with_meta_pid = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-pid",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_pid_lines = [
        line.strip() for line in preset_list_names_with_meta_pid.stdout.splitlines() if line.strip()
    ]
    pid_value = names_with_meta_pid_lines[-1].rsplit("pid=", 1)[-1]
    if re.fullmatch(r"\d+", pid_value) is None:
        raise AssertionError(
            "unexpected pid format in list-presets meta footer: "
            f"{names_with_meta_pid_lines}"
        )

    preset_list_names_with_meta_hostname = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-hostname",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_hostname_lines = [
        line.strip() for line in preset_list_names_with_meta_hostname.stdout.splitlines() if line.strip()
    ]
    if f"\thostname={socket.gethostname()}" not in names_with_meta_hostname_lines[-1]:
        raise AssertionError(
            "missing hostname in list-presets meta footer: "
            f"{names_with_meta_hostname_lines}"
        )

    preset_list_names_with_meta_git_head = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-git-head",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_git_head_lines = [
        line.strip() for line in preset_list_names_with_meta_git_head.stdout.splitlines() if line.strip()
    ]
    git_head_value = names_with_meta_git_head_lines[-1].rsplit("git_head=", 1)[-1]
    if re.fullmatch(r"[0-9a-f]{4,40}|unknown", git_head_value) is None:
        raise AssertionError(
            "unexpected git_head format in list-presets meta footer: "
            f"{names_with_meta_git_head_lines}"
        )

    preset_list_names_with_meta_git_branch = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-git-branch",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_git_branch_lines = [
        line.strip() for line in preset_list_names_with_meta_git_branch.stdout.splitlines() if line.strip()
    ]
    git_branch_value = names_with_meta_git_branch_lines[-1].rsplit("git_branch=", 1)[-1]
    if re.fullmatch(r"[A-Za-z0-9._/\-]+|unknown", git_branch_value) is None:
        raise AssertionError(
            "unexpected git_branch format in list-presets meta footer: "
            f"{names_with_meta_git_branch_lines}"
        )

    preset_list_names_with_meta_git_remote = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-git-remote",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_git_remote_lines = [
        line.strip() for line in preset_list_names_with_meta_git_remote.stdout.splitlines() if line.strip()
    ]
    git_remote_value = names_with_meta_git_remote_lines[-1].rsplit("git_remote=", 1)[-1]
    if re.fullmatch(r"\S+|unknown", git_remote_value) is None:
        raise AssertionError(
            "unexpected git_remote format in list-presets meta footer: "
            f"{names_with_meta_git_remote_lines}"
        )

    preset_list_names_with_meta_git_dirty = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-git-dirty",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_git_dirty_lines = [
        line.strip() for line in preset_list_names_with_meta_git_dirty.stdout.splitlines() if line.strip()
    ]
    git_dirty_value = names_with_meta_git_dirty_lines[-1].rsplit("git_dirty=", 1)[-1]
    if git_dirty_value not in {"clean", "dirty", "unknown"}:
        raise AssertionError(
            "unexpected git_dirty value in list-presets meta footer: "
            f"{names_with_meta_git_dirty_lines}"
        )

    preset_list_names_with_filter_meta = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "1",
            "--list-presets-tag",
            "cheap-first,smoke",
            "--list-presets-tag-match",
            "all",
            "--list-presets-name-contains",
            "quick",
            "--list-presets-with-meta",
            "--list-presets-meta-include-filters",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_filter_meta_lines = [
        line.strip() for line in preset_list_names_with_filter_meta.stdout.splitlines() if line.strip()
    ]
    expected_filter_meta_footer = (
        "# meta\tschema=planner_preset_list_meta.v1\tfiltered_count=1\temitted_count=1\ttruncated=false"
        "\ttag_filter=cheap-first,smoke\ttag_match=all\tname_contains=quick\tlimit=1"
    )
    if names_with_filter_meta_lines[-1] != expected_filter_meta_footer:
        raise AssertionError(
            f"unexpected names-with-filter-meta footer: {names_with_filter_meta_lines}"
        )

    preset_list_summary = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "summary",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary_lines = [line.strip() for line in preset_list_summary.stdout.splitlines() if line.strip()]
    if len(summary_lines) != 3:
        raise AssertionError(f"unexpected preset summary line count: {summary_lines}")
    quick_smoke_line = next((line for line in summary_lines if line.startswith("quick-smoke\t")), None)
    if quick_smoke_line is None:
        raise AssertionError(f"missing quick-smoke summary line: {summary_lines}")
    expected_snippets = [
        "models=gpt-5-mini",
        "prompt_conditions=base",
        "repeats=1",
        "max_total_runs=6",
        "max_total_runs_mode=cap",
        "max_runs_per_model=0",
        "max_runs_per_prompt_condition=0",
        "max_runs_per_task=0",
        "max_runs_per_task_model=0",
        "max_runs_per_task_prompt_condition=0",
        "cheap_first=true",
        "fair_model_allocation=false",
        "tags=cheap-first,smoke",
        "description=Fast sanity check with minimal cost.",
    ]
    for snippet in expected_snippets:
        if snippet not in quick_smoke_line:
            raise AssertionError(f"missing '{snippet}' in summary line: {quick_smoke_line}")

    preset_list_summary_tsv = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "summary-tsv",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary_tsv_lines = [line.rstrip("\n") for line in preset_list_summary_tsv.stdout.splitlines() if line.strip()]
    expected_tsv_header_preview = (
        "preset\tmodels\tprompt_conditions\trepeats\tcheap_first\tfair_model_allocation\t"
        "max_total_runs\tmax_total_runs_mode\tmax_runs_per_model\tmax_runs_per_prompt_condition\t"
        "max_runs_per_task\tmax_runs_per_task_model\tmax_runs_per_task_prompt_condition\t"
        "tags\tdescription_length\tdescription_mode\tdescription_truncated\tdescription_preview"
    )
    if not summary_tsv_lines or summary_tsv_lines[0] != expected_tsv_header_preview:
        raise AssertionError(f"unexpected summary-tsv header: {summary_tsv_lines}")
    quick_smoke_tsv_row = next((line for line in summary_tsv_lines[1:] if line.startswith("quick-smoke\t")), None)
    if quick_smoke_tsv_row is None:
        raise AssertionError(f"missing quick-smoke summary-tsv row: {summary_tsv_lines}")
    if "\ttags=cheap-first,smoke\t" in quick_smoke_tsv_row:
        raise AssertionError(
            f"summary-tsv row should be raw TSV values (not key=value pairs): {quick_smoke_tsv_row}"
        )
    quick_smoke_tsv_cells = quick_smoke_tsv_row.split("\t")
    if len(quick_smoke_tsv_cells) != 18:
        raise AssertionError(f"unexpected summary-tsv column count: {quick_smoke_tsv_cells}")
    if quick_smoke_tsv_cells[13] != "cheap-first,smoke":
        raise AssertionError(f"unexpected summary-tsv tags cell: {quick_smoke_tsv_cells}")
    if quick_smoke_tsv_cells[14] != "36":
        raise AssertionError(f"unexpected summary-tsv description_length cell: {quick_smoke_tsv_cells}")
    if quick_smoke_tsv_cells[15] != "preview":
        raise AssertionError(f"unexpected summary-tsv description_mode cell: {quick_smoke_tsv_cells}")
    if quick_smoke_tsv_cells[16] != "false":
        raise AssertionError(f"unexpected summary-tsv description_truncated cell: {quick_smoke_tsv_cells}")

    preset_list_summary_tsv_with_meta = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "summary-tsv",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary_tsv_meta_lines = [line.rstrip("\n") for line in preset_list_summary_tsv_with_meta.stdout.splitlines() if line.strip()]
    if summary_tsv_meta_lines[-1] != "# meta\tschema=planner_preset_list_meta.v1\tfiltered_count=3\temitted_count=2\ttruncated=true":
        raise AssertionError(f"unexpected summary-tsv meta footer: {summary_tsv_meta_lines}")

    preset_list_summary_tsv_with_schema = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "summary-tsv",
            "--summary-tsv-with-schema-header",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary_tsv_schema_lines = [
        line.rstrip("\n") for line in preset_list_summary_tsv_with_schema.stdout.splitlines() if line.strip()
    ]
    if len(summary_tsv_schema_lines) < 3:
        raise AssertionError(f"summary-tsv with schema header should include comment+header+rows: {summary_tsv_schema_lines}")
    if summary_tsv_schema_lines[0] != "# schema=planner_preset_summary_tsv.v2":
        raise AssertionError(f"unexpected schema header line: {summary_tsv_schema_lines}")
    if summary_tsv_schema_lines[1] != expected_tsv_header_preview:
        raise AssertionError(f"unexpected summary-tsv header with schema preface: {summary_tsv_schema_lines}")

    preset_list_summary_tsv_schema_column = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "summary-tsv",
            "--summary-tsv-with-schema-column",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary_tsv_schema_column_lines = [
        line.rstrip("\n") for line in preset_list_summary_tsv_schema_column.stdout.splitlines() if line.strip()
    ]
    expected_tsv_header_preview_with_schema_column = f"{expected_tsv_header_preview}\tschema"
    if not summary_tsv_schema_column_lines or summary_tsv_schema_column_lines[0] != expected_tsv_header_preview_with_schema_column:
        raise AssertionError(f"unexpected summary-tsv schema-column header: {summary_tsv_schema_column_lines}")
    quick_smoke_tsv_schema_row = next(
        (line for line in summary_tsv_schema_column_lines[1:] if line.startswith("quick-smoke\t")),
        None,
    )
    if quick_smoke_tsv_schema_row is None:
        raise AssertionError(
            f"missing quick-smoke summary-tsv schema-column row: {summary_tsv_schema_column_lines}"
        )
    if not quick_smoke_tsv_schema_row.endswith("\tplanner_preset_summary_tsv.v2"):
        raise AssertionError(
            f"summary-tsv schema-column row should end with schema id: {quick_smoke_tsv_schema_row}"
        )

    preset_list_summary_tsv_custom_schema = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "summary-tsv",
            "--summary-tsv-with-schema-header",
            "--summary-tsv-with-schema-column",
            "--summary-tsv-schema-id",
            "planner_preset_summary_tsv.v3",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary_tsv_custom_schema_lines = [
        line.rstrip("\n") for line in preset_list_summary_tsv_custom_schema.stdout.splitlines() if line.strip()
    ]
    if summary_tsv_custom_schema_lines[0] != "# schema=planner_preset_summary_tsv.v3":
        raise AssertionError(f"unexpected custom schema header line: {summary_tsv_custom_schema_lines}")
    if not summary_tsv_custom_schema_lines[1].endswith("\tschema"):
        raise AssertionError(f"expected schema column in custom schema header: {summary_tsv_custom_schema_lines}")
    quick_smoke_custom_schema_row = next(
        (line for line in summary_tsv_custom_schema_lines[2:] if line.startswith("quick-smoke\t")),
        None,
    )
    if quick_smoke_custom_schema_row is None or not quick_smoke_custom_schema_row.endswith("\tplanner_preset_summary_tsv.v3"):
        raise AssertionError(
            "expected custom schema id in summary-tsv row, got: "
            f"{summary_tsv_custom_schema_lines}"
        )

    invalid_summary_tsv_schema_id_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "summary-tsv",
            "--summary-tsv-schema-id",
            "planner_preset_summary_tsv.v0",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_summary_tsv_schema_id_run.returncode == 0:
        raise AssertionError("expected invalid --summary-tsv-schema-id to fail-fast")
    if "--summary-tsv-schema-id must match planner_preset_summary_tsv.vN (N>=1)" not in (
        invalid_summary_tsv_schema_id_run.stderr or ""
    ):
        raise AssertionError(
            "expected summary-tsv schema id validation error, got: "
            f"{invalid_summary_tsv_schema_id_run.stderr}"
        )

    preset_list_summary_tsv_full = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "summary-tsv",
            "--summary-tsv-description",
            "full",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary_tsv_full_lines = [line.rstrip("\n") for line in preset_list_summary_tsv_full.stdout.splitlines() if line.strip()]
    expected_tsv_header_full = expected_tsv_header_preview.replace("description_preview", "description_full")
    if not summary_tsv_full_lines or summary_tsv_full_lines[0] != expected_tsv_header_full:
        raise AssertionError(f"unexpected summary-tsv(full) header: {summary_tsv_full_lines}")

    preset_list_summary_tsv_full_soft_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "summary-tsv",
            "--summary-tsv-description",
            "full",
            "--summary-tsv-description-max-len",
            "24",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary_tsv_full_soft_cap_lines = [
        line.rstrip("\n") for line in preset_list_summary_tsv_full_soft_cap.stdout.splitlines() if line.strip()
    ]
    full_analysis_soft_cap_row = next(
        (line for line in summary_tsv_full_soft_cap_lines[1:] if line.startswith("full-analysis\t")),
        None,
    )
    if full_analysis_soft_cap_row is None:
        raise AssertionError(f"missing full-analysis row in summary-tsv(full+cap): {summary_tsv_full_soft_cap_lines}")
    if "\tfull\t" not in full_analysis_soft_cap_row:
        raise AssertionError(
            f"expected description_mode=full in summary-tsv(full+cap) row, got: {full_analysis_soft_cap_row}"
        )
    if "\ttrue\t" not in full_analysis_soft_cap_row:
        raise AssertionError(
            f"expected description_truncated=true in summary-tsv(full+cap) row, got: {full_analysis_soft_cap_row}"
        )
    if not full_analysis_soft_cap_row.endswith("..."):
        raise AssertionError(
            f"expected truncated full description with ellipsis in summary-tsv(full+cap), got: {full_analysis_soft_cap_row}"
        )

    invalid_summary_tsv_description_max_len_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "summary-tsv",
            "--summary-tsv-description",
            "full",
            "--summary-tsv-description-max-len",
            "3",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_summary_tsv_description_max_len_run.returncode == 0:
        raise AssertionError("expected summary-tsv description max len validation failure")
    if "--summary-tsv-description-max-len must be >= 4" not in (
        invalid_summary_tsv_description_max_len_run.stderr or ""
    ):
        raise AssertionError(
            "expected summary-tsv description max len validation error, got: "
            f"{invalid_summary_tsv_description_max_len_run.stderr}"
        )

    show_preset_json = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_payload = json.loads(show_preset_json.stdout)
    if show_preset_payload.get("preset") != "quick-smoke":
        raise AssertionError(f"unexpected show-preset name: {show_preset_payload}")
    resolved = show_preset_payload.get("resolved")
    if not isinstance(resolved, dict):
        raise AssertionError(f"missing resolved preset payload: {show_preset_payload}")
    if resolved.get("max_runs_per_task") != 0:
        raise AssertionError(f"expected default max_runs_per_task=0 in resolved preset, got {resolved}")
    if resolved.get("description") != "Fast sanity check with minimal cost.":
        raise AssertionError(f"expected show-preset description, got {resolved}")

    show_preset_summary = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_line = show_preset_summary.stdout.strip()
    if not show_preset_line.startswith("quick-smoke\t"):
        raise AssertionError(f"unexpected show-preset summary output: {show_preset_line}")
    for snippet in [
        "repeats=1",
        "max_total_runs_mode=cap",
        "max_runs_per_task=0",
        "tags=cheap-first,smoke",
        "description=Fast sanity check with minimal cost.",
    ]:
        if snippet not in show_preset_line:
            raise AssertionError(f"missing '{snippet}' in show-preset summary output: {show_preset_line}")

    show_preset_summary_with_meta = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_summary_with_meta_lines = [
        line.rstrip("\n") for line in show_preset_summary_with_meta.stdout.splitlines() if line.strip()
    ]
    if len(show_preset_summary_with_meta_lines) != 2:
        raise AssertionError(
            f"unexpected show-preset summary with meta output: {show_preset_summary_with_meta_lines}"
        )
    if not show_preset_summary_with_meta_lines[1].startswith(
        "# meta\tschema=planner_preset_show_meta.v1\tfiltered_count=1\temitted_count=1\ttruncated=false\tpreset=quick-smoke\tformat=summary\tpreset_file="
    ):
        raise AssertionError(
            f"unexpected show-preset summary meta footer: {show_preset_summary_with_meta_lines}"
        )

    show_preset_summary_with_meta_overrides = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-overrides",
            "--repeats",
            "2",
            "--max-total-runs",
            "12",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_summary_with_meta_overrides_lines = [
        line.rstrip("\n") for line in show_preset_summary_with_meta_overrides.stdout.splitlines() if line.strip()
    ]
    if "\toverride_count=2\toverrides=repeats,max_total_runs" not in show_preset_summary_with_meta_overrides_lines[-1]:
        raise AssertionError(
            "unexpected show-preset override context in meta footer: "
            f"{show_preset_summary_with_meta_overrides_lines}"
        )

    show_preset_summary_with_meta_custom_schema = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-schema-id",
            "planner_preset_show_meta.v2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_summary_with_meta_custom_schema_lines = [
        line.rstrip("\n") for line in show_preset_summary_with_meta_custom_schema.stdout.splitlines() if line.strip()
    ]
    if not show_preset_summary_with_meta_custom_schema_lines[-1].startswith(
        "# meta\tschema=planner_preset_show_meta.v2\tfiltered_count=1\temitted_count=1\ttruncated=false\tpreset=quick-smoke\tformat=summary\tpreset_file="
    ):
        raise AssertionError(
            "unexpected show-preset summary custom schema meta footer: "
            f"{show_preset_summary_with_meta_custom_schema_lines}"
        )

    show_preset_summary_with_meta_json = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_json_lines = [
        line.rstrip("\n") for line in show_preset_summary_with_meta_json.stdout.splitlines() if line.strip()
    ]
    show_meta_payload = json.loads(show_preset_with_meta_json_lines[-1])
    if (
        show_meta_payload.get("meta") is not True
        or show_meta_payload.get("schema_version") != "v1"
        or show_meta_payload.get("schema") != "planner_preset_show_meta.v1"
    ):
        raise AssertionError(f"unexpected show-preset json meta payload: {show_meta_payload}")
    if show_meta_payload.get("preset") != "quick-smoke" or show_meta_payload.get("format") != "summary":
        raise AssertionError(f"unexpected show-preset json meta payload core fields: {show_meta_payload}")

    show_preset_summary_with_meta_json_schema_v2 = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-format",
            "json",
            "--show-preset-meta-json-schema-version",
            "v2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_meta_payload_v2 = json.loads(
        [line.rstrip("\n") for line in show_preset_summary_with_meta_json_schema_v2.stdout.splitlines() if line.strip()][-1]
    )
    if show_meta_payload_v2.get("schema_version") != "v2":
        raise AssertionError(f"expected schema_version=v2 in show-preset json meta payload: {show_meta_payload_v2}")

    show_preset_summary_with_meta_generated_at = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-generated-at",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_generated_at_lines = [
        line.rstrip("\n") for line in show_preset_summary_with_meta_generated_at.stdout.splitlines() if line.strip()
    ]
    show_generated_at_footer = show_preset_with_meta_generated_at_lines[-1]
    if "\tgenerated_at_utc=" not in show_generated_at_footer:
        raise AssertionError(
            "missing generated_at_utc in show-preset meta footer: "
            f"{show_preset_with_meta_generated_at_lines}"
        )
    show_generated_at_value = show_generated_at_footer.rsplit("generated_at_utc=", 1)[-1]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", show_generated_at_value) is None:
        raise AssertionError(
            "unexpected generated_at_utc timestamp format in show-preset meta footer: "
            f"{show_generated_at_value}"
        )

    show_preset_summary_with_meta_cwd = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-cwd",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_cwd_lines = [
        line.rstrip("\n") for line in show_preset_summary_with_meta_cwd.stdout.splitlines() if line.strip()
    ]
    if f"\tcwd={ROOT}" not in show_preset_with_meta_cwd_lines[-1]:
        raise AssertionError(
            f"missing cwd in show-preset meta footer: {show_preset_with_meta_cwd_lines}"
        )

    show_preset_summary_with_meta_python_version = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-python-version",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_python_version_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_python_version.stdout.splitlines()
        if line.strip()
    ]
    show_python_version_value = show_preset_with_meta_python_version_lines[-1].rsplit(
        "python_version=", 1
    )[-1]
    if re.fullmatch(r"\d+\.\d+\.\d+", show_python_version_value) is None:
        raise AssertionError(
            "unexpected python_version format in show-preset meta footer: "
            f"{show_preset_with_meta_python_version_lines}"
        )

    show_preset_summary_with_meta_pid = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-pid",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_pid_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_pid.stdout.splitlines()
        if line.strip()
    ]
    show_pid_value = show_preset_with_meta_pid_lines[-1].rsplit("pid=", 1)[-1]
    if re.fullmatch(r"\d+", show_pid_value) is None:
        raise AssertionError(
            "unexpected pid format in show-preset meta footer: "
            f"{show_preset_with_meta_pid_lines}"
        )

    show_preset_summary_with_meta_hostname = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-hostname",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_hostname_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_hostname.stdout.splitlines()
        if line.strip()
    ]
    if f"\thostname={socket.gethostname()}" not in show_preset_with_meta_hostname_lines[-1]:
        raise AssertionError(
            "missing hostname in show-preset meta footer: "
            f"{show_preset_with_meta_hostname_lines}"
        )

    show_preset_summary_with_meta_git_head = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-git-head",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_git_head_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_git_head.stdout.splitlines()
        if line.strip()
    ]
    show_git_head_value = show_preset_with_meta_git_head_lines[-1].rsplit("git_head=", 1)[-1]
    if re.fullmatch(r"[0-9a-f]{4,40}|unknown", show_git_head_value) is None:
        raise AssertionError(
            "unexpected git_head format in show-preset meta footer: "
            f"{show_preset_with_meta_git_head_lines}"
        )

    show_preset_summary_with_meta_git_branch = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-git-branch",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_git_branch_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_git_branch.stdout.splitlines()
        if line.strip()
    ]
    show_git_branch_value = show_preset_with_meta_git_branch_lines[-1].rsplit("git_branch=", 1)[-1]
    if re.fullmatch(r"[A-Za-z0-9._/\-]+|unknown", show_git_branch_value) is None:
        raise AssertionError(
            "unexpected git_branch format in show-preset meta footer: "
            f"{show_preset_with_meta_git_branch_lines}"
        )

    show_preset_summary_with_meta_git_remote = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-git-remote",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_git_remote_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_git_remote.stdout.splitlines()
        if line.strip()
    ]
    show_git_remote_value = show_preset_with_meta_git_remote_lines[-1].rsplit("git_remote=", 1)[-1]
    if re.fullmatch(r"\S+|unknown", show_git_remote_value) is None:
        raise AssertionError(
            "unexpected git_remote format in show-preset meta footer: "
            f"{show_preset_with_meta_git_remote_lines}"
        )

    show_preset_summary_with_meta_git_dirty = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-git-dirty",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_git_dirty_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_git_dirty.stdout.splitlines()
        if line.strip()
    ]
    show_git_dirty_value = show_preset_with_meta_git_dirty_lines[-1].rsplit("git_dirty=", 1)[-1]
    if show_git_dirty_value not in {"clean", "dirty", "unknown"}:
        raise AssertionError(
            "unexpected git_dirty value in show-preset meta footer: "
            f"{show_preset_with_meta_git_dirty_lines}"
        )

    invalid_show_preset_meta_schema = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-schema-id",
            "bad_schema",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_show_preset_meta_schema.returncode == 0:
        raise AssertionError("expected show-preset meta schema id validation failure")
    if "--show-preset-meta-schema-id must match planner_preset_show_meta.vN (N>=1)" not in (
        invalid_show_preset_meta_schema.stderr or ""
    ):
        raise AssertionError(
            "expected show-preset meta schema validation error, got: "
            f"{invalid_show_preset_meta_schema.stderr}"
        )

    show_preset_summary_tsv = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary-tsv",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_summary_tsv_lines = [line.rstrip("\n") for line in show_preset_summary_tsv.stdout.splitlines() if line.strip()]
    if len(show_summary_tsv_lines) != 2:
        raise AssertionError(f"unexpected show-preset summary-tsv output lines: {show_summary_tsv_lines}")
    if show_summary_tsv_lines[0] != expected_tsv_header_preview:
        raise AssertionError(f"unexpected show-preset summary-tsv header: {show_summary_tsv_lines}")
    if not show_summary_tsv_lines[1].startswith("quick-smoke\tgpt-5-mini\tbase\t1\ttrue\t"):
        raise AssertionError(f"unexpected show-preset summary-tsv row: {show_summary_tsv_lines}")

    show_preset_summary_tsv_with_meta = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary-tsv",
            "--show-preset-with-meta",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_summary_tsv_with_meta_lines = [
        line.rstrip("\n") for line in show_preset_summary_tsv_with_meta.stdout.splitlines() if line.strip()
    ]
    if len(show_summary_tsv_with_meta_lines) != 3:
        raise AssertionError(
            f"unexpected show-preset summary-tsv with meta output: {show_summary_tsv_with_meta_lines}"
        )
    if not show_summary_tsv_with_meta_lines[2].startswith(
        "# meta\tschema=planner_preset_show_meta.v1\tfiltered_count=1\temitted_count=1\ttruncated=false\tpreset=quick-smoke\tformat=summary-tsv\tpreset_file="
    ):
        raise AssertionError(
            f"unexpected show-preset summary-tsv meta footer: {show_summary_tsv_with_meta_lines}"
        )

    show_preset_summary_tsv_full = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary-tsv",
            "--summary-tsv-description",
            "full",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_summary_tsv_full_lines = [line.rstrip("\n") for line in show_preset_summary_tsv_full.stdout.splitlines() if line.strip()]
    if len(show_summary_tsv_full_lines) != 2:
        raise AssertionError(f"unexpected show-preset summary-tsv(full) output lines: {show_summary_tsv_full_lines}")
    if show_summary_tsv_full_lines[0] != expected_tsv_header_preview.replace("description_preview", "description_full"):
        raise AssertionError(f"unexpected show-preset summary-tsv(full) header: {show_summary_tsv_full_lines}")

    show_preset_summary_tsv_with_schema = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary-tsv",
            "--summary-tsv-with-schema-header",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_summary_tsv_schema_lines = [
        line.rstrip("\n") for line in show_preset_summary_tsv_with_schema.stdout.splitlines() if line.strip()
    ]
    if len(show_summary_tsv_schema_lines) != 3:
        raise AssertionError(
            f"unexpected show-preset summary-tsv with schema output lines: {show_summary_tsv_schema_lines}"
        )
    if show_summary_tsv_schema_lines[0] != "# schema=planner_preset_summary_tsv.v2":
        raise AssertionError(f"unexpected show-preset schema header: {show_summary_tsv_schema_lines}")
    if show_summary_tsv_schema_lines[1] != expected_tsv_header_preview:
        raise AssertionError(f"unexpected show-preset summary-tsv header with schema preface: {show_summary_tsv_schema_lines}")

    show_preset_summary_tsv_schema_column = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary-tsv",
            "--summary-tsv-with-schema-column",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_summary_tsv_schema_column_lines = [
        line.rstrip("\n") for line in show_preset_summary_tsv_schema_column.stdout.splitlines() if line.strip()
    ]
    if len(show_summary_tsv_schema_column_lines) != 2:
        raise AssertionError(
            f"unexpected show-preset summary-tsv schema-column lines: {show_summary_tsv_schema_column_lines}"
        )
    if show_summary_tsv_schema_column_lines[0] != f"{expected_tsv_header_preview}\tschema":
        raise AssertionError(
            f"unexpected show-preset summary-tsv schema-column header: {show_summary_tsv_schema_column_lines}"
        )
    if not show_summary_tsv_schema_column_lines[1].endswith("\tplanner_preset_summary_tsv.v2"):
        raise AssertionError(
            f"show-preset summary-tsv schema-column row should end with schema id: {show_summary_tsv_schema_column_lines}"
        )

    show_preset_overridden = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--models",
            "gpt-5-mini,gpt-5-pro",
            "--repeats",
            "2",
            "--max-total-runs",
            "8",
            "--fair-model-allocation",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_overridden_payload = json.loads(show_preset_overridden.stdout)
    overridden = show_preset_overridden_payload.get("resolved", {})
    if overridden.get("models") != "gpt-5-mini,gpt-5-pro":
        raise AssertionError(f"show-preset override for models not applied: {overridden}")
    if overridden.get("repeats") != 2:
        raise AssertionError(f"show-preset override for repeats not applied: {overridden}")
    if overridden.get("max_total_runs") != 8:
        raise AssertionError(f"show-preset override for max_total_runs not applied: {overridden}")
    if overridden.get("fair_model_allocation") is not True:
        raise AssertionError(
            f"show-preset override for fair_model_allocation not applied: {overridden}"
        )

    preset_output = OUT / "batch-plan.preset.quick-smoke.json"
    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(TASK_SET),
            "--preset",
            "quick-smoke",
            "--output",
            str(preset_output),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    preset_payload = json.loads(preset_output.read_text(encoding="utf-8"))
    preset_config = preset_payload["config"]
    if preset_config.get("preset") != "quick-smoke":
        raise AssertionError(f"unexpected preset name in config: {preset_config.get('preset')}")
    if preset_config["models"] != ["gpt-5-mini"]:
        raise AssertionError(f"unexpected preset models: {preset_config['models']}")
    if preset_payload["summary"]["planned_runs_total"] != 3:
        raise AssertionError(
            "expected quick-smoke preset to plan 3 runs (3 tasks x 1 model x 1 condition x 1 repeat), "
            f"got {preset_payload['summary']['planned_runs_total']}"
        )

    invalid_empty_tag_filter_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-tag",
            ",,,",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_empty_tag_filter_run.returncode == 0:
        raise AssertionError("expected empty --list-presets-tag to fail-fast")
    if "--list-presets-tag must include at least one non-empty tag" not in (
        invalid_empty_tag_filter_run.stderr or ""
    ):
        raise AssertionError(
            "expected empty tag filter validation error, got: "
            f"{invalid_empty_tag_filter_run.stderr}"
        )

    invalid_preset_limit_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "0",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_preset_limit_run.returncode == 0:
        raise AssertionError("expected invalid --list-presets-limit to fail-fast")
    if "--list-presets-limit must be >= 1" not in (invalid_preset_limit_run.stderr or ""):
        raise AssertionError(
            "expected list-presets-limit validation error, got: "
            f"{invalid_preset_limit_run.stderr}"
        )

    name_filtered_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-name-contains",
            "ci",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if name_filtered_run.stdout.strip().splitlines() != ["balanced-ci"]:
        raise AssertionError(
            f"unexpected preset name substring filter output: {name_filtered_run.stdout!r}"
        )

    name_and_tag_filtered_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-name-contains",
            "analysis",
            "--list-presets-tag",
            "high-coverage",
            "--list-presets-format",
            "summary-tsv",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    name_and_tag_filtered_lines = name_and_tag_filtered_run.stdout.strip().splitlines()
    if len(name_and_tag_filtered_lines) != 2:
        raise AssertionError(
            "expected summary-tsv output to contain header and one filtered row, got: "
            f"{name_and_tag_filtered_lines}"
        )
    if not name_and_tag_filtered_lines[1].startswith("full-analysis\t"):
        raise AssertionError(
            "unexpected combined name/tag filtered summary-tsv row: "
            f"{name_and_tag_filtered_lines}"
        )

    invalid_empty_name_filter_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-name-contains",
            "   ",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_empty_name_filter_run.returncode == 0:
        raise AssertionError("expected empty --list-presets-name-contains to fail-fast")
    if "--list-presets-name-contains must include at least one non-empty character" not in (
        invalid_empty_name_filter_run.stderr or ""
    ):
        raise AssertionError(
            "expected empty name filter validation error, got: "
            f"{invalid_empty_name_filter_run.stderr}"
        )

    invalid_list_meta_json_schema_version_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-meta-json-schema-version",
            "1",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_list_meta_json_schema_version_run.returncode == 0:
        raise AssertionError("expected invalid --list-presets-meta-json-schema-version to fail-fast")
    if "--list-presets-meta-json-schema-version must match vN (N>=1)" not in (
        invalid_list_meta_json_schema_version_run.stderr or ""
    ):
        raise AssertionError(
            "expected list meta json schema version validation error, got: "
            f"{invalid_list_meta_json_schema_version_run.stderr}"
        )

    invalid_preset_file = OUT / "invalid-batch-plan-presets.v1.json"
    invalid_preset_file.write_text(
        json.dumps(
            {
                "schema_version": "v1",
                "presets": {
                    "bad": {
                        "models": "gpt-5-mini",
                        "prompt_conditions": "base",
                        "repeats": 1,
                        "unexpected_field": "oops",
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    invalid_preset_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--preset-file",
            str(invalid_preset_file),
            "--list-presets",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_preset_run.returncode == 0:
        raise AssertionError("expected invalid preset file to fail-fast")
    if "unknown key(s): unexpected_field" not in (invalid_preset_run.stderr or ""):
        raise AssertionError(
            "expected unknown-key preset validation error message, got: "
            f"{invalid_preset_run.stderr}"
        )

    invalid_preset_tags_file = OUT / "invalid-batch-plan-presets.tags.v1.json"
    invalid_preset_tags_file.write_text(
        json.dumps(
            {
                "schema_version": "v1",
                "presets": {
                    "bad-tags": {
                        "models": "gpt-5-mini",
                        "prompt_conditions": "base",
                        "repeats": 1,
                        "tags": "not-an-array",
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    invalid_preset_tags_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--preset-file",
            str(invalid_preset_tags_file),
            "--list-presets",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_preset_tags_run.returncode == 0:
        raise AssertionError("expected invalid preset tags to fail-fast")
    if "presets.bad-tags.tags must be a non-empty array" not in (invalid_preset_tags_run.stderr or ""):
        raise AssertionError(
            "expected tags type preset validation error message, got: "
            f"{invalid_preset_tags_run.stderr}"
        )

    print("OK: build_batch_eval_plan regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
