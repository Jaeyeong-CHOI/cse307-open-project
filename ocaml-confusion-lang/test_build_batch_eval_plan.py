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

    preset_list_sorted_by_name_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "name-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_name_desc = [
        line.strip() for line in preset_list_sorted_by_name_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_name_desc != ["quick-smoke", "full-analysis", "balanced-ci"]:
        raise AssertionError(
            "unexpected --list-presets-sort=name-desc output: "
            f"{preset_names_sorted_by_name_desc}"
        )

    preset_list_sorted_by_max_total_runs = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "max-total-runs",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cap = [line.strip() for line in preset_list_sorted_by_max_total_runs.stdout.splitlines() if line.strip()]
    if preset_names_sorted_by_cap != ["quick-smoke", "balanced-ci", "full-analysis"]:
        raise AssertionError(
            f"unexpected --list-presets-sort=max-total-runs output: {preset_names_sorted_by_cap}"
        )

    preset_list_sorted_by_max_total_runs_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "max-total-runs-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cap_desc = [
        line.strip() for line in preset_list_sorted_by_max_total_runs_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_cap_desc != ["full-analysis", "balanced-ci", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=max-total-runs-desc output: "
            f"{preset_names_sorted_by_cap_desc}"
        )

    preset_list_sorted_by_total_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "total-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_total_cap = [
        line.strip() for line in preset_list_sorted_by_total_cap.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_total_cap != ["quick-smoke", "balanced-ci", "full-analysis"]:
        raise AssertionError(
            "unexpected --list-presets-sort=total-cap output: "
            f"{preset_names_sorted_by_total_cap}"
        )

    preset_list_sorted_by_total_cap_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "total-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_total_cap_desc = [
        line.strip() for line in preset_list_sorted_by_total_cap_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_total_cap_desc != ["full-analysis", "balanced-ci", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=total-cap-desc output: "
            f"{preset_names_sorted_by_total_cap_desc}"
        )

    preset_list_sorted_by_repeats = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "repeats",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_repeats = [
        line.strip() for line in preset_list_sorted_by_repeats.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_repeats != ["quick-smoke", "balanced-ci", "full-analysis"]:
        raise AssertionError(
            f"unexpected --list-presets-sort=repeats output: {preset_names_sorted_by_repeats}"
        )

    preset_list_sorted_by_repeats_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "repeats-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_repeats_desc = [
        line.strip() for line in preset_list_sorted_by_repeats_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_repeats_desc != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=repeats-desc output: "
            f"{preset_names_sorted_by_repeats_desc}"
        )

    preset_list_sorted_by_model_count = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "model-count",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_model_count = [
        line.strip() for line in preset_list_sorted_by_model_count.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_model_count != ["quick-smoke", "balanced-ci", "full-analysis"]:
        raise AssertionError(
            "unexpected --list-presets-sort=model-count output: "
            f"{preset_names_sorted_by_model_count}"
        )

    preset_list_sorted_by_model_count_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "model-count-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_model_count_desc = [
        line.strip() for line in preset_list_sorted_by_model_count_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_model_count_desc != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=model-count-desc output: "
            f"{preset_names_sorted_by_model_count_desc}"
        )

    preset_list_sorted_by_prompt_condition_count = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "prompt-condition-count",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_prompt_condition_count = [
        line.strip() for line in preset_list_sorted_by_prompt_condition_count.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_prompt_condition_count != ["quick-smoke", "balanced-ci", "full-analysis"]:
        raise AssertionError(
            "unexpected --list-presets-sort=prompt-condition-count output: "
            f"{preset_names_sorted_by_prompt_condition_count}"
        )

    preset_list_sorted_by_prompt_condition_count_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "prompt-condition-count-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_prompt_condition_count_desc = [
        line.strip()
        for line in preset_list_sorted_by_prompt_condition_count_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_prompt_condition_count_desc != ["full-analysis", "balanced-ci", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=prompt-condition-count-desc output: "
            f"{preset_names_sorted_by_prompt_condition_count_desc}"
        )

    preset_list_sorted_by_max_runs_per_model = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "max-runs-per-model",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_max_runs_per_model = [
        line.strip() for line in preset_list_sorted_by_max_runs_per_model.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_max_runs_per_model != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=max-runs-per-model output: "
            f"{preset_names_sorted_by_max_runs_per_model}"
        )

    preset_list_sorted_by_max_runs_per_model_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "max-runs-per-model-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_max_runs_per_model_desc = [
        line.strip() for line in preset_list_sorted_by_max_runs_per_model_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_max_runs_per_model_desc != ["full-analysis", "quick-smoke", "balanced-ci"]:
        raise AssertionError(
            "unexpected --list-presets-sort=max-runs-per-model-desc output: "
            f"{preset_names_sorted_by_max_runs_per_model_desc}"
        )

    preset_list_sorted_by_per_model_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "per-model-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_per_model_cap = [
        line.strip() for line in preset_list_sorted_by_per_model_cap.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_per_model_cap != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=per-model-cap output: "
            f"{preset_names_sorted_by_per_model_cap}"
        )

    preset_list_sorted_by_per_model_cap_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "per-model-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_per_model_cap_desc = [
        line.strip() for line in preset_list_sorted_by_per_model_cap_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_per_model_cap_desc != ["full-analysis", "quick-smoke", "balanced-ci"]:
        raise AssertionError(
            "unexpected --list-presets-sort=per-model-cap-desc output: "
            f"{preset_names_sorted_by_per_model_cap_desc}"
        )

    preset_list_sorted_by_max_runs_per_prompt_condition = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "max-runs-per-prompt-condition",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_max_runs_per_prompt_condition = [
        line.strip()
        for line in preset_list_sorted_by_max_runs_per_prompt_condition.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_max_runs_per_prompt_condition != [
        "balanced-ci",
        "full-analysis",
        "quick-smoke",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=max-runs-per-prompt-condition output: "
            f"{preset_names_sorted_by_max_runs_per_prompt_condition}"
        )

    preset_list_sorted_by_max_runs_per_prompt_condition_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "max-runs-per-prompt-condition-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_max_runs_per_prompt_condition_desc = [
        line.strip()
        for line in preset_list_sorted_by_max_runs_per_prompt_condition_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_max_runs_per_prompt_condition_desc != [
        "full-analysis",
        "quick-smoke",
        "balanced-ci",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=max-runs-per-prompt-condition-desc output: "
            f"{preset_names_sorted_by_max_runs_per_prompt_condition_desc}"
        )

    preset_list_sorted_by_per_prompt_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "per-prompt-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_per_prompt_cap = [
        line.strip() for line in preset_list_sorted_by_per_prompt_cap.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_per_prompt_cap != [
        "balanced-ci",
        "full-analysis",
        "quick-smoke",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=per-prompt-cap output: "
            f"{preset_names_sorted_by_per_prompt_cap}"
        )

    preset_list_sorted_by_per_prompt_cap_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "per-prompt-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_per_prompt_cap_desc = [
        line.strip()
        for line in preset_list_sorted_by_per_prompt_cap_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_per_prompt_cap_desc != [
        "full-analysis",
        "quick-smoke",
        "balanced-ci",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=per-prompt-cap-desc output: "
            f"{preset_names_sorted_by_per_prompt_cap_desc}"
        )

    preset_list_sorted_by_per_condition_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "per-condition-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_per_condition_cap = [
        line.strip() for line in preset_list_sorted_by_per_condition_cap.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_per_condition_cap != [
        "balanced-ci",
        "full-analysis",
        "quick-smoke",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=per-condition-cap output: "
            f"{preset_names_sorted_by_per_condition_cap}"
        )

    preset_list_sorted_by_per_condition_cap_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "per-condition-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_per_condition_cap_desc = [
        line.strip()
        for line in preset_list_sorted_by_per_condition_cap_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_per_condition_cap_desc != [
        "full-analysis",
        "quick-smoke",
        "balanced-ci",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=per-condition-cap-desc output: "
            f"{preset_names_sorted_by_per_condition_cap_desc}"
        )

    task_cap_presets_file = OUT / "batch-plan-presets.task-cap-sort.v1.json"
    task_cap_presets_file.write_text(
        json.dumps(
            {
                "schema_version": "v1",
                "presets": {
                    "task-cap-small": {"models": "gpt-5-mini", "prompt_conditions": "base", "max_runs_per_task": 2, "max_runs_per_task_model": 1, "max_runs_per_task_prompt_condition": 2},
                    "task-cap-large": {"models": "gpt-5-mini", "prompt_conditions": "base", "max_runs_per_task": 7, "max_runs_per_task_model": 4, "max_runs_per_task_prompt_condition": 6},
                    "task-cap-uncapped": {"models": "gpt-5-mini", "prompt_conditions": "base"},
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    preset_list_sorted_by_per_task_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(task_cap_presets_file),
            "--list-presets-sort",
            "per-task-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_per_task_cap = [
        line.strip() for line in preset_list_sorted_by_per_task_cap.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_per_task_cap != ["task-cap-small", "task-cap-large", "task-cap-uncapped"]:
        raise AssertionError(
            "unexpected --list-presets-sort=per-task-cap output: "
            f"{preset_names_sorted_by_per_task_cap}"
        )

    preset_list_sorted_by_task_cap_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(task_cap_presets_file),
            "--list-presets-sort",
            "task-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_task_cap_desc = [
        line.strip() for line in preset_list_sorted_by_task_cap_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_task_cap_desc != ["task-cap-uncapped", "task-cap-large", "task-cap-small"]:
        raise AssertionError(
            "unexpected --list-presets-sort=task-cap-desc output: "
            f"{preset_names_sorted_by_task_cap_desc}"
        )

    preset_list_sorted_by_per_task_model_cap_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(task_cap_presets_file),
            "--list-presets-sort",
            "per-task-model-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_per_task_model_cap_desc = [
        line.strip()
        for line in preset_list_sorted_by_per_task_model_cap_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_per_task_model_cap_desc != [
        "task-cap-uncapped",
        "task-cap-large",
        "task-cap-small",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=per-task-model-cap-desc output: "
            f"{preset_names_sorted_by_per_task_model_cap_desc}"
        )

    preset_list_sorted_by_task_model_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(task_cap_presets_file),
            "--list-presets-sort",
            "task-model-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_task_model_cap = [
        line.strip() for line in preset_list_sorted_by_task_model_cap.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_task_model_cap != ["task-cap-small", "task-cap-large", "task-cap-uncapped"]:
        raise AssertionError(
            "unexpected --list-presets-sort=task-model-cap output: "
            f"{preset_names_sorted_by_task_model_cap}"
        )

    preset_list_sorted_by_per_task_prompt_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(task_cap_presets_file),
            "--list-presets-sort",
            "per-task-prompt-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_per_task_prompt_cap = [
        line.strip() for line in preset_list_sorted_by_per_task_prompt_cap.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_per_task_prompt_cap != ["task-cap-small", "task-cap-large", "task-cap-uncapped"]:
        raise AssertionError(
            "unexpected --list-presets-sort=per-task-prompt-cap output: "
            f"{preset_names_sorted_by_per_task_prompt_cap}"
        )

    preset_list_sorted_by_task_prompt_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(task_cap_presets_file),
            "--list-presets-sort",
            "task-prompt-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_task_prompt_cap = [
        line.strip() for line in preset_list_sorted_by_task_prompt_cap.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_task_prompt_cap != ["task-cap-small", "task-cap-large", "task-cap-uncapped"]:
        raise AssertionError(
            "unexpected --list-presets-sort=task-prompt-cap output: "
            f"{preset_names_sorted_by_task_prompt_cap}"
        )

    preset_list_sorted_by_per_task_condition_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(task_cap_presets_file),
            "--list-presets-sort",
            "per-task-condition-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_per_task_condition_cap = [
        line.strip()
        for line in preset_list_sorted_by_per_task_condition_cap.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_per_task_condition_cap != [
        "task-cap-small",
        "task-cap-large",
        "task-cap-uncapped",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=per-task-condition-cap output: "
            f"{preset_names_sorted_by_per_task_condition_cap}"
        )

    preset_list_sorted_by_task_condition_cap_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(task_cap_presets_file),
            "--list-presets-sort",
            "task-condition-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_task_condition_cap_desc = [
        line.strip()
        for line in preset_list_sorted_by_task_condition_cap_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_task_condition_cap_desc != [
        "task-cap-uncapped",
        "task-cap-large",
        "task-cap-small",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=task-condition-cap-desc output: "
            f"{preset_names_sorted_by_task_condition_cap_desc}"
        )

    preset_list_sorted_by_description_length = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "description-length",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_description_length = [
        line.strip() for line in preset_list_sorted_by_description_length.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_description_length != ["quick-smoke", "balanced-ci", "full-analysis"]:
        raise AssertionError(
            "unexpected --list-presets-sort=description-length output: "
            f"{preset_names_sorted_by_description_length}"
        )

    preset_list_sorted_by_description_length_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "description-length-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_description_length_desc = [
        line.strip() for line in preset_list_sorted_by_description_length_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_description_length_desc != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=description-length-desc output: "
            f"{preset_names_sorted_by_description_length_desc}"
        )

    preset_list_sorted_by_tag_count = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "tag-count",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_tag_count = [
        line.strip() for line in preset_list_sorted_by_tag_count.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_tag_count != ["full-analysis", "quick-smoke", "balanced-ci"]:
        raise AssertionError(
            "unexpected --list-presets-sort=tag-count output: "
            f"{preset_names_sorted_by_tag_count}"
        )

    preset_list_sorted_by_tag_count_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "tag-count-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_tag_count_desc = [
        line.strip() for line in preset_list_sorted_by_tag_count_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_tag_count_desc != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=tag-count-desc output: "
            f"{preset_names_sorted_by_tag_count_desc}"
        )

    preset_list_sorted_by_cheap_first_tag = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "cheap-first-tag",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cheap_first_tag = [
        line.strip() for line in preset_list_sorted_by_cheap_first_tag.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_cheap_first_tag != ["balanced-ci", "quick-smoke", "full-analysis"]:
        raise AssertionError(
            "unexpected --list-presets-sort=cheap-first-tag output: "
            f"{preset_names_sorted_by_cheap_first_tag}"
        )

    preset_list_sorted_by_cheap_first_tag_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "cheap-first-tag-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cheap_first_tag_desc = [
        line.strip() for line in preset_list_sorted_by_cheap_first_tag_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_cheap_first_tag_desc != ["full-analysis", "balanced-ci", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=cheap-first-tag-desc output: "
            f"{preset_names_sorted_by_cheap_first_tag_desc}"
        )

    preset_list_sorted_by_cheap_first_alias = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "cheap-first",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cheap_first_alias = [
        line.strip() for line in preset_list_sorted_by_cheap_first_alias.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_cheap_first_alias != ["balanced-ci", "quick-smoke", "full-analysis"]:
        raise AssertionError(
            "unexpected --list-presets-sort=cheap-first output: "
            f"{preset_names_sorted_by_cheap_first_alias}"
        )

    preset_list_sorted_by_cheap_first_desc_alias = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "cheap-first-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cheap_first_desc_alias = [
        line.strip()
        for line in preset_list_sorted_by_cheap_first_desc_alias.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_cheap_first_desc_alias != ["full-analysis", "balanced-ci", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=cheap-first-desc output: "
            f"{preset_names_sorted_by_cheap_first_desc_alias}"
        )

    preset_list_sorted_by_cheap_first_total_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "cheap-first-total-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cheap_first_total_cap = [
        line.strip()
        for line in preset_list_sorted_by_cheap_first_total_cap.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_cheap_first_total_cap != ["quick-smoke", "balanced-ci", "full-analysis"]:
        raise AssertionError(
            "unexpected --list-presets-sort=cheap-first-total-cap output: "
            f"{preset_names_sorted_by_cheap_first_total_cap}"
        )

    preset_list_sorted_by_cheap_total_cap_alias = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "cheap-total-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cheap_total_cap_alias = [
        line.strip()
        for line in preset_list_sorted_by_cheap_total_cap_alias.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_cheap_total_cap_alias != ["quick-smoke", "balanced-ci", "full-analysis"]:
        raise AssertionError(
            "unexpected --list-presets-sort=cheap-total-cap output: "
            f"{preset_names_sorted_by_cheap_total_cap_alias}"
        )

    preset_list_sorted_by_fair_allocation_total_cap = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "fair-allocation-total-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_fair_allocation_total_cap = [
        line.strip()
        for line in preset_list_sorted_by_fair_allocation_total_cap.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_fair_allocation_total_cap != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=fair-allocation-total-cap output: "
            f"{preset_names_sorted_by_fair_allocation_total_cap}"
        )

    preset_list_sorted_by_fair_total_cap_alias = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "fair-total-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_fair_total_cap_alias = [
        line.strip()
        for line in preset_list_sorted_by_fair_total_cap_alias.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_fair_total_cap_alias != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=fair-total-cap output: "
            f"{preset_names_sorted_by_fair_total_cap_alias}"
        )

    preset_list_sorted_by_fair_cap_alias = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "fair-cap",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_fair_cap_alias = [
        line.strip()
        for line in preset_list_sorted_by_fair_cap_alias.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_fair_cap_alias != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=fair-cap output: "
            f"{preset_names_sorted_by_fair_cap_alias}"
        )

    cost_priority_presets_file = OUT / "cost-priority-presets.json"
    cost_priority_presets_file.write_text(
        json.dumps(
            {
                "schema_version": "v1",
                "presets": {
                    "cheap-model-tight": {
                        "models": "gpt-5-mini",
                        "prompt_conditions": "base",
                        "repeats": 1,
                        "cheap_first": True,
                        "max_total_runs": 20,
                        "max_runs_per_model": 4,
                        "max_runs_per_prompt_condition": 3,
                        "tags": ["cheap-first", "ci"],
                    },
                    "cheap-model-loose": {
                        "models": "gpt-5-mini",
                        "prompt_conditions": "base",
                        "repeats": 1,
                        "cheap_first": True,
                        "max_total_runs": 20,
                        "max_runs_per_model": 12,
                        "max_runs_per_prompt_condition": 9,
                        "tags": ["cheap-first", "ci"],
                    },
                    "expensive-analysis": {
                        "models": "gpt-5-pro,gpt-5.3-codex",
                        "prompt_conditions": "base,strict",
                        "repeats": 2,
                        "cheap_first": False,
                        "max_total_runs": 40,
                        "max_runs_per_model": 0,
                        "tags": ["analysis"],
                    },
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    preset_list_sorted_by_cost_priority = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(cost_priority_presets_file),
            "--list-presets-sort",
            "cost-priority",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cost_priority = [
        line.strip()
        for line in preset_list_sorted_by_cost_priority.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_cost_priority != [
        "cheap-model-tight",
        "cheap-model-loose",
        "expensive-analysis",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=cost-priority output: "
            f"{preset_names_sorted_by_cost_priority}"
        )

    preset_list_sorted_by_cost_priority_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(cost_priority_presets_file),
            "--list-presets-sort",
            "cost-priority-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cost_priority_desc = [
        line.strip()
        for line in preset_list_sorted_by_cost_priority_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_cost_priority_desc != [
        "expensive-analysis",
        "cheap-model-loose",
        "cheap-model-tight",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=cost-priority-desc output: "
            f"{preset_names_sorted_by_cost_priority_desc}"
        )

    preset_list_sorted_by_cost_priority_prompt = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(cost_priority_presets_file),
            "--list-presets-sort",
            "cost-priority-prompt",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cost_priority_prompt = [
        line.strip()
        for line in preset_list_sorted_by_cost_priority_prompt.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_cost_priority_prompt != [
        "cheap-model-tight",
        "cheap-model-loose",
        "expensive-analysis",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=cost-priority-prompt output: "
            f"{preset_names_sorted_by_cost_priority_prompt}"
        )

    preset_list_sorted_by_cost_priority_prompt_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--preset-file",
            str(cost_priority_presets_file),
            "--list-presets-sort",
            "cost-priority-prompt-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cost_priority_prompt_desc = [
        line.strip()
        for line in preset_list_sorted_by_cost_priority_prompt_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_cost_priority_prompt_desc != [
        "expensive-analysis",
        "cheap-model-loose",
        "cheap-model-tight",
    ]:
        raise AssertionError(
            "unexpected --list-presets-sort=cost-priority-prompt-desc output: "
            f"{preset_names_sorted_by_cost_priority_prompt_desc}"
        )

    preset_list_sorted_by_cheap_first_total_cap_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "cheap-first-total-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cheap_first_total_cap_desc = [
        line.strip()
        for line in preset_list_sorted_by_cheap_first_total_cap_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_cheap_first_total_cap_desc != ["full-analysis", "balanced-ci", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=cheap-first-total-cap-desc output: "
            f"{preset_names_sorted_by_cheap_first_total_cap_desc}"
        )

    preset_list_sorted_by_cheap_total_cap_desc_alias = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "cheap-total-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_cheap_total_cap_desc_alias = [
        line.strip()
        for line in preset_list_sorted_by_cheap_total_cap_desc_alias.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_cheap_total_cap_desc_alias != ["full-analysis", "balanced-ci", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=cheap-total-cap-desc output: "
            f"{preset_names_sorted_by_cheap_total_cap_desc_alias}"
        )

    preset_list_sorted_by_fair_allocation_total_cap_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "fair-allocation-total-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_fair_allocation_total_cap_desc = [
        line.strip()
        for line in preset_list_sorted_by_fair_allocation_total_cap_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_fair_allocation_total_cap_desc != ["quick-smoke", "full-analysis", "balanced-ci"]:
        raise AssertionError(
            "unexpected --list-presets-sort=fair-allocation-total-cap-desc output: "
            f"{preset_names_sorted_by_fair_allocation_total_cap_desc}"
        )

    preset_list_sorted_by_fair_total_cap_desc_alias = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "fair-total-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_fair_total_cap_desc_alias = [
        line.strip()
        for line in preset_list_sorted_by_fair_total_cap_desc_alias.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_fair_total_cap_desc_alias != ["quick-smoke", "full-analysis", "balanced-ci"]:
        raise AssertionError(
            "unexpected --list-presets-sort=fair-total-cap-desc output: "
            f"{preset_names_sorted_by_fair_total_cap_desc_alias}"
        )

    preset_list_sorted_by_fair_cap_desc_alias = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "fair-cap-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_fair_cap_desc_alias = [
        line.strip()
        for line in preset_list_sorted_by_fair_cap_desc_alias.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_fair_cap_desc_alias != ["quick-smoke", "full-analysis", "balanced-ci"]:
        raise AssertionError(
            "unexpected --list-presets-sort=fair-cap-desc output: "
            f"{preset_names_sorted_by_fair_cap_desc_alias}"
        )

    preset_list_sorted_by_fair_model_allocation = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "fair-model-allocation",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_fair_model_allocation = [
        line.strip()
        for line in preset_list_sorted_by_fair_model_allocation.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_fair_model_allocation != ["balanced-ci", "full-analysis", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=fair-model-allocation output: "
            f"{preset_names_sorted_by_fair_model_allocation}"
        )

    preset_list_sorted_by_fair_allocation_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "fair-allocation-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_fair_allocation_desc = [
        line.strip()
        for line in preset_list_sorted_by_fair_allocation_desc.stdout.splitlines()
        if line.strip()
    ]
    if preset_names_sorted_by_fair_allocation_desc != ["quick-smoke", "balanced-ci", "full-analysis"]:
        raise AssertionError(
            "unexpected --list-presets-sort=fair-allocation-desc output: "
            f"{preset_names_sorted_by_fair_allocation_desc}"
        )

    preset_list_sorted_by_custom_tag = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "tag:analysis",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_custom_tag = [
        line.strip() for line in preset_list_sorted_by_custom_tag.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_custom_tag != ["full-analysis", "balanced-ci", "quick-smoke"]:
        raise AssertionError(
            "unexpected --list-presets-sort=tag:analysis output: "
            f"{preset_names_sorted_by_custom_tag}"
        )

    preset_list_sorted_by_custom_tag_desc = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-sort",
            "tag:analysis-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_names_sorted_by_custom_tag_desc = [
        line.strip() for line in preset_list_sorted_by_custom_tag_desc.stdout.splitlines() if line.strip()
    ]
    if preset_names_sorted_by_custom_tag_desc != ["balanced-ci", "quick-smoke", "full-analysis"]:
        raise AssertionError(
            "unexpected --list-presets-sort=tag:analysis-desc output: "
            f"{preset_names_sorted_by_custom_tag_desc}"
        )

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

    preset_list_resolved_json_with_meta = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-format",
            "resolved-json",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-profile",
            "privacy-safe",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    preset_list_resolved_json_with_meta_payload = json.loads(preset_list_resolved_json_with_meta.stdout)
    list_meta_payload = preset_list_resolved_json_with_meta_payload.get("meta")
    if not isinstance(list_meta_payload, dict):
        raise AssertionError(
            "expected top-level meta object in resolved-json list payload: "
            f"{preset_list_resolved_json_with_meta_payload}"
        )
    if list_meta_payload.get("schema") != "planner_preset_list_meta.v2":
        raise AssertionError(
            "unexpected schema in resolved-json list meta payload: "
            f"{list_meta_payload}"
        )
    if list_meta_payload.get("filtered_count") != 3 or list_meta_payload.get("emitted_count") != 2:
        raise AssertionError(
            "unexpected counts in resolved-json list meta payload: "
            f"{list_meta_payload}"
        )
    if list_meta_payload.get("truncated") is not True:
        raise AssertionError(
            "unexpected truncated flag in resolved-json list meta payload: "
            f"{list_meta_payload}"
        )
    for required_key in (
        "tag_match",
        "python_version",
        "git_head",
        "git_branch",
        "git_dirty",
        "git_toplevel",
        "git_repo_name",
        "git_worktree_name",
        "argv_sha256",
        "argv_count",
        "preset_file_sha256",
    ):
        if required_key not in list_meta_payload:
            raise AssertionError(
                f"missing {required_key} in resolved-json list meta payload: {list_meta_payload}"
            )
    for forbidden_key in ("cwd", "generated_at_utc", "pid", "hostname", "git_remote", "argv", "argv_tokens"):
        if forbidden_key in list_meta_payload:
            raise AssertionError(
                f"unexpected {forbidden_key} in resolved-json list meta payload: {list_meta_payload}"
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

    preset_list_names_with_meta_json_argv_tokens = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-format",
            "json",
            "--list-presets-meta-include-argv-tokens",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_meta_payload_with_tokens = json.loads(
        [line.strip() for line in preset_list_names_with_meta_json_argv_tokens.stdout.splitlines() if line.strip()][-1]
    )
    if not isinstance(names_meta_payload_with_tokens.get("argv_tokens"), list):
        raise AssertionError(f"argv_tokens should be a list in list-presets json meta payload: {names_meta_payload_with_tokens}")
    if "--list-presets-meta-include-argv-tokens" not in names_meta_payload_with_tokens["argv_tokens"]:
        raise AssertionError(f"argv_tokens missing include flag in list-presets json meta payload: {names_meta_payload_with_tokens}")

    preset_list_names_with_meta_json_argv_sha256 = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-format",
            "json",
            "--list-presets-meta-include-argv-sha256",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_meta_payload_with_argv_sha256 = json.loads(
        [line.strip() for line in preset_list_names_with_meta_json_argv_sha256.stdout.splitlines() if line.strip()][-1]
    )
    list_argv_sha256 = names_meta_payload_with_argv_sha256.get("argv_sha256")
    if not isinstance(list_argv_sha256, str) or len(list_argv_sha256) != 64:
        raise AssertionError(f"invalid argv_sha256 in list-presets json meta payload: {names_meta_payload_with_argv_sha256}")

    preset_list_names_with_meta_json_argv_count = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-format",
            "json",
            "--list-presets-meta-include-argv-count",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_meta_payload_with_argv_count = json.loads(
        [line.strip() for line in preset_list_names_with_meta_json_argv_count.stdout.splitlines() if line.strip()][-1]
    )
    list_argv_count = names_meta_payload_with_argv_count.get("argv_count")
    if not isinstance(list_argv_count, int) or list_argv_count < 1:
        raise AssertionError(f"invalid argv_count in list-presets json meta payload: {names_meta_payload_with_argv_count}")

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

    preset_list_names_with_meta_profile_debug = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "1",
            "--list-presets-with-meta",
            "--list-presets-meta-format",
            "json",
            "--list-presets-meta-profile",
            "debug",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    list_debug_meta_payload = json.loads(
        [line.strip() for line in preset_list_names_with_meta_profile_debug.stdout.splitlines() if line.strip()][-1]
    )
    for required_key in (
        "tag_filter",
        "generated_at_utc",
        "cwd",
        "python_version",
        "pid",
        "hostname",
        "git_head",
        "git_head_date_utc",
        "git_head_subject",
        "git_branch",
        "git_remote",
        "git_dirty",
        "git_toplevel",
        "git_repo_name",
        "git_worktree_name",
        "argv",
        "argv_tokens",
        "argv_sha256",
        "argv_count",
    ):
        if required_key not in list_debug_meta_payload:
            raise AssertionError(f"missing {required_key} in list-presets meta debug profile payload: {list_debug_meta_payload}")

    preset_list_names_with_meta_profile_safe_debug = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "1",
            "--list-presets-with-meta",
            "--list-presets-meta-format",
            "json",
            "--list-presets-meta-profile",
            "safe-debug",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    list_safe_debug_meta_payload = json.loads(
        [line.strip() for line in preset_list_names_with_meta_profile_safe_debug.stdout.splitlines() if line.strip()][-1]
    )
    for required_key in (
        "tag_filter",
        "generated_at_utc",
        "cwd",
        "python_version",
        "pid",
        "hostname",
        "git_head",
        "git_head_date_utc",
        "git_head_subject",
        "git_branch",
        "git_remote",
        "git_dirty",
        "git_toplevel",
        "git_repo_name",
        "git_worktree_name",
        "argv_sha256",
        "argv_count",
        "preset_file_sha256",
    ):
        if required_key not in list_safe_debug_meta_payload:
            raise AssertionError(f"missing {required_key} in list-presets meta safe-debug profile payload: {list_safe_debug_meta_payload}")
    for forbidden_key in ("argv", "argv_tokens"):
        if forbidden_key in list_safe_debug_meta_payload:
            raise AssertionError(f"unexpected {forbidden_key} in list-presets meta safe-debug profile payload: {list_safe_debug_meta_payload}")

    preset_list_names_with_meta_profile_ci_safe = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "1",
            "--list-presets-with-meta",
            "--list-presets-meta-format",
            "json",
            "--list-presets-meta-profile",
            "ci-safe",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    list_ci_safe_meta_payload = json.loads(
        [line.strip() for line in preset_list_names_with_meta_profile_ci_safe.stdout.splitlines() if line.strip()][-1]
    )
    for required_key in (
        "tag_filter",
        "cwd",
        "python_version",
        "git_head",
        "git_branch",
        "git_dirty",
        "git_toplevel",
        "git_repo_name",
        "git_worktree_name",
        "argv_sha256",
        "argv_count",
        "preset_file_sha256",
    ):
        if required_key not in list_ci_safe_meta_payload:
            raise AssertionError(f"missing {required_key} in list-presets meta ci-safe profile payload: {list_ci_safe_meta_payload}")
    for forbidden_key in (
        "generated_at_utc",
        "pid",
        "hostname",
        "git_head_date_utc",
        "git_head_subject",
        "git_remote",
        "argv",
        "argv_tokens",
    ):
        if forbidden_key in list_ci_safe_meta_payload:
            raise AssertionError(f"unexpected {forbidden_key} in list-presets meta ci-safe profile payload: {list_ci_safe_meta_payload}")
    list_preset_file_sha256 = list_ci_safe_meta_payload.get("preset_file_sha256")
    if not isinstance(list_preset_file_sha256, str) or len(list_preset_file_sha256) != 64:
        raise AssertionError(
            "invalid preset_file_sha256 in list-presets meta ci-safe profile payload: "
            f"{list_ci_safe_meta_payload}"
        )

    preset_list_names_with_meta_profile_privacy_safe = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "1",
            "--list-presets-with-meta",
            "--list-presets-meta-format",
            "json",
            "--list-presets-meta-profile",
            "privacy-safe",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    list_privacy_safe_meta_payload = json.loads(
        [line.strip() for line in preset_list_names_with_meta_profile_privacy_safe.stdout.splitlines() if line.strip()][-1]
    )
    for required_key in (
        "tag_filter",
        "python_version",
        "git_head",
        "git_branch",
        "git_dirty",
        "git_toplevel",
        "git_repo_name",
        "git_worktree_name",
        "argv_sha256",
        "argv_count",
        "preset_file_sha256",
    ):
        if required_key not in list_privacy_safe_meta_payload:
            raise AssertionError(
                f"missing {required_key} in list-presets meta privacy-safe profile payload: {list_privacy_safe_meta_payload}"
            )
    for forbidden_key in (
        "cwd",
        "generated_at_utc",
        "pid",
        "hostname",
        "git_head_date_utc",
        "git_head_subject",
        "git_remote",
        "argv",
        "argv_tokens",
    ):
        if forbidden_key in list_privacy_safe_meta_payload:
            raise AssertionError(
                f"unexpected {forbidden_key} in list-presets meta privacy-safe profile payload: {list_privacy_safe_meta_payload}"
            )

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

    preset_list_names_with_meta_git_head_subject = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-git-head-subject",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_git_head_subject_lines = [
        line.strip() for line in preset_list_names_with_meta_git_head_subject.stdout.splitlines() if line.strip()
    ]
    git_head_subject_value = names_with_meta_git_head_subject_lines[-1].rsplit("git_head_subject=", 1)[-1]
    if not git_head_subject_value:
        raise AssertionError(
            "missing git_head_subject in list-presets meta footer: "
            f"{names_with_meta_git_head_subject_lines}"
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

    preset_list_names_with_meta_argv = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-argv",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_argv_lines = [
        line.strip() for line in preset_list_names_with_meta_argv.stdout.splitlines() if line.strip()
    ]
    argv_value = names_with_meta_argv_lines[-1].rsplit("argv=", 1)[-1]
    if "--list-presets-meta-include-argv" not in argv_value:
        raise AssertionError(
            "missing argv in list-presets meta footer: "
            f"{names_with_meta_argv_lines}"
        )

    preset_list_names_with_meta_argv_tokens = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-argv-tokens",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_argv_tokens_lines = [
        line.strip() for line in preset_list_names_with_meta_argv_tokens.stdout.splitlines() if line.strip()
    ]
    argv_tokens_value = names_with_meta_argv_tokens_lines[-1].rsplit("argv_tokens=", 1)[-1]
    argv_tokens = json.loads(argv_tokens_value)
    if "--list-presets-meta-include-argv-tokens" not in argv_tokens:
        raise AssertionError(
            "missing argv_tokens in list-presets meta footer: "
            f"{names_with_meta_argv_tokens_lines}"
        )

    preset_list_names_with_meta_argv_sha256 = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-presets",
            "--list-presets-limit",
            "2",
            "--list-presets-with-meta",
            "--list-presets-meta-include-argv-sha256",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    names_with_meta_argv_sha256_lines = [
        line.strip() for line in preset_list_names_with_meta_argv_sha256.stdout.splitlines() if line.strip()
    ]
    argv_sha256_value = names_with_meta_argv_sha256_lines[-1].rsplit("argv_sha256=", 1)[-1]
    if len(argv_sha256_value) != 64 or any(ch not in "0123456789abcdef" for ch in argv_sha256_value):
        raise AssertionError(
            "invalid argv_sha256 in list-presets meta footer: "
            f"{names_with_meta_argv_sha256_lines}"
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
        "\ttag_filter=cheap-first,smoke\ttag_match=all\tname_contains=quick\tlimit=1\tsort=name"
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

    show_preset_json_with_meta = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-with-meta",
            "--show-preset-meta-profile",
            "privacy-safe",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_json_with_meta_payload = json.loads(show_preset_json_with_meta.stdout)
    show_meta_payload = show_preset_json_with_meta_payload.get("meta")
    if not isinstance(show_meta_payload, dict):
        raise AssertionError(
            "expected top-level meta object in show-preset json payload: "
            f"{show_preset_json_with_meta_payload}"
        )
    if show_meta_payload.get("schema") != "planner_preset_show_meta.v2":
        raise AssertionError(f"unexpected show-preset json meta schema: {show_meta_payload}")
    if show_meta_payload.get("preset") != "quick-smoke" or show_meta_payload.get("format") != "json":
        raise AssertionError(f"unexpected show-preset json meta identity fields: {show_meta_payload}")
    if show_meta_payload.get("filtered_count") != 1 or show_meta_payload.get("emitted_count") != 1:
        raise AssertionError(f"unexpected show-preset json meta counters: {show_meta_payload}")
    if show_meta_payload.get("truncated") is not False:
        raise AssertionError(f"unexpected show-preset json meta truncated flag: {show_meta_payload}")
    for required_key in (
        "override_count",
        "python_version",
        "git_head",
        "git_branch",
        "git_dirty",
        "git_toplevel",
        "git_repo_name",
        "git_worktree_name",
        "argv_sha256",
        "argv_count",
        "preset_file_sha256",
    ):
        if required_key not in show_meta_payload:
            raise AssertionError(f"missing {required_key} in show-preset json meta payload: {show_meta_payload}")
    for forbidden_key in ("cwd", "generated_at_utc", "pid", "hostname", "git_remote", "argv", "argv_tokens"):
        if forbidden_key in show_meta_payload:
            raise AssertionError(
                f"unexpected {forbidden_key} in show-preset json meta payload: {show_meta_payload}"
            )

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

    show_preset_summary_with_meta_json_argv_tokens = subprocess.run(
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
            "--show-preset-meta-include-argv-tokens",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_meta_payload_with_tokens = json.loads(
        [line.rstrip("\n") for line in show_preset_summary_with_meta_json_argv_tokens.stdout.splitlines() if line.strip()][-1]
    )
    if not isinstance(show_meta_payload_with_tokens.get("argv_tokens"), list):
        raise AssertionError(f"argv_tokens should be a list in show-preset json meta payload: {show_meta_payload_with_tokens}")
    if "--show-preset-meta-include-argv-tokens" not in show_meta_payload_with_tokens["argv_tokens"]:
        raise AssertionError(f"argv_tokens missing include flag in show-preset json meta payload: {show_meta_payload_with_tokens}")

    show_preset_summary_with_meta_json_argv_sha256 = subprocess.run(
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
            "--show-preset-meta-include-argv-sha256",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_meta_payload_with_argv_sha256 = json.loads(
        [line.rstrip("\n") for line in show_preset_summary_with_meta_json_argv_sha256.stdout.splitlines() if line.strip()][-1]
    )
    show_argv_sha256 = show_meta_payload_with_argv_sha256.get("argv_sha256")
    if not isinstance(show_argv_sha256, str) or len(show_argv_sha256) != 64:
        raise AssertionError(f"invalid argv_sha256 in show-preset json meta payload: {show_meta_payload_with_argv_sha256}")

    show_preset_summary_with_meta_json_argv_count = subprocess.run(
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
            "--show-preset-meta-include-argv-count",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_meta_payload_with_argv_count = json.loads(
        [line.rstrip("\n") for line in show_preset_summary_with_meta_json_argv_count.stdout.splitlines() if line.strip()][-1]
    )
    show_argv_count = show_meta_payload_with_argv_count.get("argv_count")
    if not isinstance(show_argv_count, int) or show_argv_count < 1:
        raise AssertionError(f"invalid argv_count in show-preset json meta payload: {show_meta_payload_with_argv_count}")

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

    show_preset_summary_with_meta_profile_debug = subprocess.run(
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
            "--show-preset-meta-profile",
            "debug",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_debug_meta_payload = json.loads(
        [line.rstrip("\n") for line in show_preset_summary_with_meta_profile_debug.stdout.splitlines() if line.strip()][-1]
    )
    for required_key in (
        "override_count",
        "generated_at_utc",
        "cwd",
        "python_version",
        "pid",
        "hostname",
        "git_head",
        "git_head_date_utc",
        "git_head_subject",
        "git_branch",
        "git_remote",
        "git_dirty",
        "git_toplevel",
        "git_repo_name",
        "git_worktree_name",
        "argv",
        "argv_tokens",
        "argv_sha256",
        "argv_count",
    ):
        if required_key not in show_debug_meta_payload:
            raise AssertionError(f"missing {required_key} in show-preset meta debug profile payload: {show_debug_meta_payload}")

    show_preset_summary_with_meta_profile_safe_debug = subprocess.run(
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
            "--show-preset-meta-profile",
            "safe-debug",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_safe_debug_meta_payload = json.loads(
        [line.rstrip("\n") for line in show_preset_summary_with_meta_profile_safe_debug.stdout.splitlines() if line.strip()][-1]
    )
    for required_key in (
        "override_count",
        "generated_at_utc",
        "cwd",
        "python_version",
        "pid",
        "hostname",
        "git_head",
        "git_head_date_utc",
        "git_head_subject",
        "git_branch",
        "git_remote",
        "git_dirty",
        "git_toplevel",
        "git_repo_name",
        "git_worktree_name",
        "argv_sha256",
        "argv_count",
        "preset_file_sha256",
    ):
        if required_key not in show_safe_debug_meta_payload:
            raise AssertionError(f"missing {required_key} in show-preset meta safe-debug profile payload: {show_safe_debug_meta_payload}")
    for forbidden_key in ("argv", "argv_tokens"):
        if forbidden_key in show_safe_debug_meta_payload:
            raise AssertionError(f"unexpected {forbidden_key} in show-preset meta safe-debug profile payload: {show_safe_debug_meta_payload}")

    show_preset_summary_with_meta_profile_ci_safe = subprocess.run(
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
            "--show-preset-meta-profile",
            "ci-safe",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_ci_safe_meta_payload = json.loads(
        [line.rstrip("\n") for line in show_preset_summary_with_meta_profile_ci_safe.stdout.splitlines() if line.strip()][-1]
    )
    for required_key in (
        "override_count",
        "cwd",
        "python_version",
        "git_head",
        "git_branch",
        "git_dirty",
        "git_toplevel",
        "git_repo_name",
        "git_worktree_name",
        "argv_sha256",
        "argv_count",
        "preset_file_sha256",
    ):
        if required_key not in show_ci_safe_meta_payload:
            raise AssertionError(f"missing {required_key} in show-preset meta ci-safe profile payload: {show_ci_safe_meta_payload}")
    for forbidden_key in (
        "generated_at_utc",
        "pid",
        "hostname",
        "git_head_date_utc",
        "git_head_subject",
        "git_remote",
        "argv",
        "argv_tokens",
    ):
        if forbidden_key in show_ci_safe_meta_payload:
            raise AssertionError(f"unexpected {forbidden_key} in show-preset meta ci-safe profile payload: {show_ci_safe_meta_payload}")
    show_preset_file_sha256 = show_ci_safe_meta_payload.get("preset_file_sha256")
    if not isinstance(show_preset_file_sha256, str) or len(show_preset_file_sha256) != 64:
        raise AssertionError(
            "invalid preset_file_sha256 in show-preset meta ci-safe profile payload: "
            f"{show_ci_safe_meta_payload}"
        )

    show_preset_summary_with_meta_profile_privacy_safe = subprocess.run(
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
            "--show-preset-meta-profile",
            "privacy-safe",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_privacy_safe_meta_payload = json.loads(
        [line.rstrip("\n") for line in show_preset_summary_with_meta_profile_privacy_safe.stdout.splitlines() if line.strip()][-1]
    )
    for required_key in (
        "override_count",
        "python_version",
        "git_head",
        "git_branch",
        "git_dirty",
        "git_toplevel",
        "git_repo_name",
        "git_worktree_name",
        "argv_sha256",
        "argv_count",
        "preset_file_sha256",
    ):
        if required_key not in show_privacy_safe_meta_payload:
            raise AssertionError(
                f"missing {required_key} in show-preset meta privacy-safe profile payload: {show_privacy_safe_meta_payload}"
            )
    for forbidden_key in (
        "cwd",
        "generated_at_utc",
        "pid",
        "hostname",
        "git_head_date_utc",
        "git_head_subject",
        "git_remote",
        "argv",
        "argv_tokens",
    ):
        if forbidden_key in show_privacy_safe_meta_payload:
            raise AssertionError(
                f"unexpected {forbidden_key} in show-preset meta privacy-safe profile payload: {show_privacy_safe_meta_payload}"
            )

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

    show_preset_summary_with_meta_git_head_subject = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-git-head-subject",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_git_head_subject_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_git_head_subject.stdout.splitlines()
        if line.strip()
    ]
    show_git_head_subject_value = show_preset_with_meta_git_head_subject_lines[-1].rsplit("git_head_subject=", 1)[-1]
    if not show_git_head_subject_value:
        raise AssertionError(
            "missing git_head_subject in show-preset meta footer: "
            f"{show_preset_with_meta_git_head_subject_lines}"
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

    show_preset_summary_with_meta_argv = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-argv",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_argv_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_argv.stdout.splitlines()
        if line.strip()
    ]
    show_argv_value = show_preset_with_meta_argv_lines[-1].rsplit("argv=", 1)[-1]
    if "--show-preset-meta-include-argv" not in show_argv_value:
        raise AssertionError(
            "missing argv in show-preset meta footer: "
            f"{show_preset_with_meta_argv_lines}"
        )

    show_preset_summary_with_meta_argv_tokens = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-argv-tokens",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_argv_tokens_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_argv_tokens.stdout.splitlines()
        if line.strip()
    ]
    show_argv_tokens_value = show_preset_with_meta_argv_tokens_lines[-1].rsplit("argv_tokens=", 1)[-1]
    show_argv_tokens = json.loads(show_argv_tokens_value)
    if "--show-preset-meta-include-argv-tokens" not in show_argv_tokens:
        raise AssertionError(
            "missing argv_tokens in show-preset meta footer: "
            f"{show_preset_with_meta_argv_tokens_lines}"
        )

    show_preset_summary_with_meta_argv_sha256 = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--show-preset",
            "quick-smoke",
            "--show-preset-format",
            "summary",
            "--show-preset-with-meta",
            "--show-preset-meta-include-argv-sha256",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    show_preset_with_meta_argv_sha256_lines = [
        line.rstrip("\n")
        for line in show_preset_summary_with_meta_argv_sha256.stdout.splitlines()
        if line.strip()
    ]
    show_argv_sha256_value = show_preset_with_meta_argv_sha256_lines[-1].rsplit("argv_sha256=", 1)[-1]
    if len(show_argv_sha256_value) != 64 or any(ch not in "0123456789abcdef" for ch in show_argv_sha256_value):
        raise AssertionError(
            "invalid argv_sha256 in show-preset meta footer: "
            f"{show_preset_with_meta_argv_sha256_lines}"
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

    list_sort_aliases_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    sort_aliases_payload = json.loads(list_sort_aliases_run.stdout)
    if sort_aliases_payload.get("schema_version") != "v2":
        raise AssertionError(
            "unexpected list-sort-aliases schema_version: "
            f"{sort_aliases_payload.get('schema_version')}"
        )
    if sort_aliases_payload.get("filtered_count") != len(sort_aliases_payload.get("aliases", {})):
        raise AssertionError(
            "expected filtered_count to match emitted aliases without limit, got: "
            f"{sort_aliases_payload.get('filtered_count')} vs {len(sort_aliases_payload.get('aliases', {}))}"
        )
    if sort_aliases_payload.get("sort") != "alias":
        raise AssertionError(
            "expected default list-sort-aliases sort=alias, got: "
            f"{sort_aliases_payload.get('sort')}"
        )
    if sort_aliases_payload.get("filter_mode") != "contains":
        raise AssertionError(
            "expected default list-sort-aliases filter_mode=contains, got: "
            f"{sort_aliases_payload.get('filter_mode')}"
        )
    if sort_aliases_payload.get("match_field") != "both":
        raise AssertionError(
            "expected default list-sort-aliases match_field=both, got: "
            f"{sort_aliases_payload.get('match_field')}"
        )
    if sort_aliases_payload.get("name_not_filter_mode") != "contains":
        raise AssertionError(
            "expected default list-sort-aliases name_not_filter_mode=contains, got: "
            f"{sort_aliases_payload.get('name_not_filter_mode')}"
        )
    if sort_aliases_payload.get("min_group_size") != 1:
        raise AssertionError(
            "expected default list-sort-aliases min_group_size=1, got: "
            f"{sort_aliases_payload.get('min_group_size')}"
        )
    if sort_aliases_payload.get("max_group_size") is not None:
        raise AssertionError(
            "expected default list-sort-aliases max_group_size=None, got: "
            f"{sort_aliases_payload.get('max_group_size')}"
        )
    aliases = sort_aliases_payload.get("aliases", {})
    alias_group_count = len({canonical for canonical in aliases.values()})
    if sort_aliases_payload.get("group_count") != alias_group_count:
        raise AssertionError(
            "expected list-sort-aliases group_count to equal unique canonical count, got: "
            f"{sort_aliases_payload.get('group_count')} vs {alias_group_count}"
        )
    if aliases.get("fair-cap") != "fair-allocation-total-cap":
        raise AssertionError(f"unexpected alias mapping for fair-cap: {aliases.get('fair-cap')}")
    if aliases.get("total-cap-desc") != "max-total-runs-desc":
        raise AssertionError(
            f"unexpected alias mapping for total-cap-desc: {aliases.get('total-cap-desc')}"
        )

    grouped_sort_aliases_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-format",
            "grouped-json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    grouped_sort_aliases_payload = json.loads(grouped_sort_aliases_run.stdout)
    if grouped_sort_aliases_payload.get("schema_version") != "v2":
        raise AssertionError(
            "unexpected grouped list-sort-aliases schema_version: "
            f"{grouped_sort_aliases_payload.get('schema_version')}"
        )
    if grouped_sort_aliases_payload.get("group_schema_version") != "v2":
        raise AssertionError(
            "unexpected grouped list-sort-aliases group_schema_version: "
            f"{grouped_sort_aliases_payload.get('group_schema_version')}"
        )
    if grouped_sort_aliases_payload.get("sort") != "alias":
        raise AssertionError(
            "expected grouped list-sort-aliases sort=alias by default, got: "
            f"{grouped_sort_aliases_payload.get('sort')}"
        )
    if grouped_sort_aliases_payload.get("filter_mode") != "contains":
        raise AssertionError(
            "expected grouped list-sort-aliases filter_mode=contains by default, got: "
            f"{grouped_sort_aliases_payload.get('filter_mode')}"
        )
    if grouped_sort_aliases_payload.get("match_field") != "both":
        raise AssertionError(
            "expected grouped list-sort-aliases match_field=both by default, got: "
            f"{grouped_sort_aliases_payload.get('match_field')}"
        )
    if grouped_sort_aliases_payload.get("name_not_filter_mode") != "contains":
        raise AssertionError(
            "expected grouped list-sort-aliases name_not_filter_mode=contains by default, got: "
            f"{grouped_sort_aliases_payload.get('name_not_filter_mode')}"
        )
    groups = grouped_sort_aliases_payload.get("groups", {})
    if grouped_sort_aliases_payload.get("group_count") != len(groups):
        raise AssertionError(
            "expected grouped list-sort-aliases group_count to match groups size, got: "
            f"{grouped_sort_aliases_payload.get('group_count')} vs {len(groups)}"
        )
    group_sizes = grouped_sort_aliases_payload.get("group_sizes", {})
    if set(group_sizes.keys()) != set(groups.keys()):
        raise AssertionError(
            "expected grouped list-sort-aliases group_sizes keys to match groups keys, got: "
            f"{sorted(group_sizes.keys())} vs {sorted(groups.keys())}"
        )
    for canonical, aliases_in_group in groups.items():
        if group_sizes.get(canonical) != len(aliases_in_group):
            raise AssertionError(
                "expected grouped list-sort-aliases group_sizes to equal per-group alias counts, got: "
                f"{canonical} -> {group_sizes.get(canonical)} vs {len(aliases_in_group)}"
            )
    total_cap_aliases = groups.get("max-total-runs", [])
    if "total-cap" not in total_cap_aliases:
        raise AssertionError(f"expected total-cap alias in max-total-runs group, got: {total_cap_aliases}")
    fair_total_cap_aliases = groups.get("fair-allocation-total-cap", [])
    if "fair-cap" not in fair_total_cap_aliases:
        raise AssertionError(
            "expected fair-cap alias in fair-allocation-total-cap group, "
            f"got: {fair_total_cap_aliases}"
        )

    filtered_sort_aliases_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "fair",
            "--list-sort-aliases-limit",
            "2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    filtered_sort_aliases_payload = json.loads(filtered_sort_aliases_run.stdout)
    if filtered_sort_aliases_payload.get("schema_version") != "v2":
        raise AssertionError(
            "unexpected filtered list-sort-aliases schema_version: "
            f"{filtered_sort_aliases_payload.get('schema_version')}"
        )
    if filtered_sort_aliases_payload.get("name_contains") != "fair":
        raise AssertionError(
            "expected name_contains in filtered alias payload, got: "
            f"{filtered_sort_aliases_payload.get('name_contains')}"
        )
    if filtered_sort_aliases_payload.get("emitted_count") != 2:
        raise AssertionError(
            "expected filtered alias emitted_count=2, got: "
            f"{filtered_sort_aliases_payload.get('emitted_count')}"
        )
    if filtered_sort_aliases_payload.get("truncated") is not True:
        raise AssertionError(
            "expected filtered alias payload to be truncated with limit=2"
        )
    filtered_aliases = filtered_sort_aliases_payload.get("aliases", {})
    filtered_group_count = len({canonical for canonical in filtered_aliases.values()})
    if filtered_sort_aliases_payload.get("group_count") != filtered_group_count:
        raise AssertionError(
            "expected filtered alias payload group_count to equal unique canonical count, got: "
            f"{filtered_sort_aliases_payload.get('group_count')} vs {filtered_group_count}"
        )

    canonical_sort_aliases_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-sort",
            "canonical",
            "--list-sort-aliases-limit",
            "3",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    canonical_sort_aliases_payload = json.loads(canonical_sort_aliases_run.stdout)
    if canonical_sort_aliases_payload.get("sort") != "canonical":
        raise AssertionError(
            "expected canonical list-sort-aliases sort mode in payload, got: "
            f"{canonical_sort_aliases_payload.get('sort')}"
        )
    canonical_aliases = list(canonical_sort_aliases_payload.get("aliases", {}).items())
    expected_prefix = [
        ("cheap-first", "cheap-first-tag"),
        ("cheap-first-desc", "cheap-first-tag-desc"),
        ("cheap-total-cap", "cheap-first-total-cap"),
    ]
    if canonical_aliases != expected_prefix:
        raise AssertionError(
            "expected canonical sort prefix to follow canonical key ordering, got: "
            f"{canonical_aliases}"
        )

    group_size_sort_aliases_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "fair",
            "--list-sort-aliases-sort",
            "group-size-desc",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    group_size_sort_aliases_payload = json.loads(group_size_sort_aliases_run.stdout)
    if group_size_sort_aliases_payload.get("sort") != "group-size-desc":
        raise AssertionError(
            "expected group-size-desc sort mode in payload, got: "
            f"{group_size_sort_aliases_payload.get('sort')}"
        )
    group_size_aliases = list(group_size_sort_aliases_payload.get("aliases", {}).items())
    expected_group_size_aliases = [
        ("fair-cap", "fair-allocation-total-cap"),
        ("fair-total-cap", "fair-allocation-total-cap"),
        ("fair-cap-desc", "fair-allocation-total-cap-desc"),
        ("fair-total-cap-desc", "fair-allocation-total-cap-desc"),
        ("fair-allocation", "fair-model-allocation"),
        ("fair-allocation-desc", "fair-model-allocation-desc"),
    ]
    if group_size_aliases != expected_group_size_aliases:
        raise AssertionError(
            "expected group-size-desc sort to prioritize larger canonical families first, got: "
            f"{group_size_aliases}"
        )

    min_group_size_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "fair",
            "--list-sort-aliases-min-group-size",
            "2",
            "--list-sort-aliases-sort",
            "canonical",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    min_group_size_payload = json.loads(min_group_size_run.stdout)
    if min_group_size_payload.get("min_group_size") != 2:
        raise AssertionError(
            "expected min_group_size to be reflected in payload, got: "
            f"{min_group_size_payload.get('min_group_size')}"
        )
    min_group_size_aliases = min_group_size_payload.get("aliases", {})
    expected_min_group_size_aliases = {
        "fair-cap": "fair-allocation-total-cap",
        "fair-total-cap": "fair-allocation-total-cap",
        "fair-cap-desc": "fair-allocation-total-cap-desc",
        "fair-total-cap-desc": "fair-allocation-total-cap-desc",
    }
    if min_group_size_aliases != expected_min_group_size_aliases:
        raise AssertionError(
            "expected min_group_size filter to keep only canonical families with >=2 aliases, got: "
            f"{min_group_size_aliases}"
        )

    max_group_size_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "fair",
            "--list-sort-aliases-max-group-size",
            "1",
            "--list-sort-aliases-sort",
            "canonical",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    max_group_size_payload = json.loads(max_group_size_run.stdout)
    if max_group_size_payload.get("max_group_size") != 1:
        raise AssertionError(
            "expected max_group_size to be reflected in payload, got: "
            f"{max_group_size_payload.get('max_group_size')}"
        )
    max_group_size_aliases = max_group_size_payload.get("aliases", {})
    expected_max_group_size_aliases = {
        "fair-allocation": "fair-model-allocation",
        "fair-allocation-desc": "fair-model-allocation-desc",
    }
    if max_group_size_aliases != expected_max_group_size_aliases:
        raise AssertionError(
            "expected max_group_size filter to keep only canonical families with <=1 alias, got: "
            f"{max_group_size_aliases}"
        )

    aliases_tsv_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-format",
            "aliases-tsv",
            "--list-sort-aliases-name-contains",
            "fair",
            "--list-sort-aliases-sort",
            "canonical",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    aliases_tsv_lines = aliases_tsv_run.stdout.strip().splitlines()
    if aliases_tsv_lines[0] != "alias\tcanonical\tcanonical_group_count":
        raise AssertionError(f"unexpected aliases-tsv header: {aliases_tsv_lines[0]}")
    if "fair-allocation\tfair-model-allocation\t1" not in aliases_tsv_lines[1:]:
        raise AssertionError(
            "expected aliases-tsv output to include fair-allocation mapping with canonical_group_count, got: "
            f"{aliases_tsv_lines}"
        )

    aliases_tsv_with_meta_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-format",
            "aliases-tsv",
            "--list-sort-aliases-name-contains",
            "fair",
            "--list-sort-aliases-limit",
            "2",
            "--list-sort-aliases-tsv-with-meta",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    aliases_tsv_with_meta_lines = aliases_tsv_with_meta_run.stdout.strip().splitlines()
    if not aliases_tsv_with_meta_lines[-1].startswith("# meta\tschema=planner_sort_aliases_tsv_meta.v1\t"):
        raise AssertionError(
            "expected aliases-tsv meta footer with schema id, got: "
            f"{aliases_tsv_with_meta_lines[-1]}"
        )
    if "\tfiltered_count=" not in aliases_tsv_with_meta_lines[-1] or "\temitted_count=" not in aliases_tsv_with_meta_lines[-1]:
        raise AssertionError(
            "expected aliases-tsv meta footer to include filtered/emitted counters, got: "
            f"{aliases_tsv_with_meta_lines[-1]}"
        )
    if "\tmin_group_size=1" not in aliases_tsv_with_meta_lines[-1]:
        raise AssertionError(
            "expected aliases-tsv meta footer to include min_group_size context, got: "
            f"{aliases_tsv_with_meta_lines[-1]}"
        )

    grouped_tsv_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-format",
            "grouped-tsv",
            "--list-sort-aliases-name-contains",
            "fair-cap",
            "--list-sort-aliases-filter-mode",
            "exact",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    grouped_tsv_lines = grouped_tsv_run.stdout.strip().splitlines()
    if grouped_tsv_lines[0] != "canonical\talias_count\talias_share_pct\taliases":
        raise AssertionError(f"unexpected grouped-tsv header: {grouped_tsv_lines[0]}")
    if grouped_tsv_lines[1:] != ["fair-allocation-total-cap\t1\t100.00\tfair-cap"]:
        raise AssertionError(
            "expected grouped-tsv exact filter output to collapse to a single canonical family with 100% share, got: "
            f"{grouped_tsv_lines}"
        )

    grouped_tsv_with_meta_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-format",
            "grouped-tsv",
            "--list-sort-aliases-name-contains",
            "fair-cap",
            "--list-sort-aliases-filter-mode",
            "exact",
            "--list-sort-aliases-tsv-with-meta",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    grouped_tsv_with_meta_lines = grouped_tsv_with_meta_run.stdout.strip().splitlines()
    if not grouped_tsv_with_meta_lines[-1].startswith("# meta\tschema=planner_sort_aliases_tsv_meta.v1\t"):
        raise AssertionError(
            "expected grouped-tsv meta footer with schema id, got: "
            f"{grouped_tsv_with_meta_lines[-1]}"
        )
    if "\tfilter_mode=exact\t" not in grouped_tsv_with_meta_lines[-1]:
        raise AssertionError(
            "expected grouped-tsv meta footer to include filter_mode context, got: "
            f"{grouped_tsv_with_meta_lines[-1]}"
        )
    if "\tname_not_filter_mode=contains\t" not in grouped_tsv_with_meta_lines[-1]:
        raise AssertionError(
            "expected grouped-tsv meta footer to include name_not_filter_mode context, got: "
            f"{grouped_tsv_with_meta_lines[-1]}"
        )

    aliases_tsv_with_meta_json_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-format",
            "aliases-tsv",
            "--list-sort-aliases-name-contains",
            "fair",
            "--list-sort-aliases-limit",
            "2",
            "--list-sort-aliases-tsv-with-meta",
            "--list-sort-aliases-tsv-meta-format",
            "json",
            "--list-sort-aliases-tsv-meta-json-schema-version",
            "v2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    aliases_tsv_with_meta_json_lines = aliases_tsv_with_meta_json_run.stdout.strip().splitlines()
    aliases_tsv_meta_json_payload = json.loads(aliases_tsv_with_meta_json_lines[-1])
    if aliases_tsv_meta_json_payload.get("meta") is not True:
        raise AssertionError(
            "expected aliases-tsv JSON meta footer to include meta=true, got: "
            f"{aliases_tsv_meta_json_payload}"
        )
    if aliases_tsv_meta_json_payload.get("schema") != "planner_sort_aliases_tsv_meta.v1":
        raise AssertionError(
            "unexpected aliases-tsv JSON meta schema id, got: "
            f"{aliases_tsv_meta_json_payload}"
        )
    if aliases_tsv_meta_json_payload.get("schema_version") != "v2":
        raise AssertionError(
            "unexpected aliases-tsv JSON meta schema_version, got: "
            f"{aliases_tsv_meta_json_payload}"
        )
    if not isinstance(aliases_tsv_meta_json_payload.get("group_count"), int):
        raise AssertionError(
            "expected aliases-tsv JSON meta footer to include integer group_count, got: "
            f"{aliases_tsv_meta_json_payload}"
        )
    if aliases_tsv_meta_json_payload.get("max_group_size") is not None:
        raise AssertionError(
            "expected aliases-tsv JSON meta footer max_group_size=None by default, got: "
            f"{aliases_tsv_meta_json_payload}"
        )

    invalid_aliases_meta_schema_version_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-format",
            "aliases-tsv",
            "--list-sort-aliases-tsv-with-meta",
            "--list-sort-aliases-tsv-meta-format",
            "json",
            "--list-sort-aliases-tsv-meta-json-schema-version",
            "oops",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_aliases_meta_schema_version_run.returncode == 0:
        raise AssertionError("expected invalid list-sort-aliases meta JSON schema version to fail-fast")
    if "--list-sort-aliases-tsv-meta-json-schema-version must match vN (N>=1)" not in (
        invalid_aliases_meta_schema_version_run.stderr or ""
    ):
        raise AssertionError(
            "expected list-sort-aliases meta schema-version validation error, got: "
            f"{invalid_aliases_meta_schema_version_run.stderr}"
        )

    prefix_filter_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "per-task",
            "--list-sort-aliases-filter-mode",
            "prefix",
            "--list-sort-aliases-sort",
            "alias",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    prefix_filter_payload = json.loads(prefix_filter_run.stdout)
    if prefix_filter_payload.get("filter_mode") != "prefix":
        raise AssertionError(
            "expected prefix filter mode in payload, got: "
            f"{prefix_filter_payload.get('filter_mode')}"
        )
    prefix_aliases = list(prefix_filter_payload.get("aliases", {}).keys())
    if not prefix_aliases or any(not alias.startswith("per-task") for alias in prefix_aliases):
        raise AssertionError(
            "expected prefix filter to keep only aliases starting with per-task, got: "
            f"{prefix_aliases}"
        )

    exact_filter_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "FAIR-CAP",
            "--list-sort-aliases-filter-mode",
            "exact",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    exact_filter_payload = json.loads(exact_filter_run.stdout)
    exact_aliases = exact_filter_payload.get("aliases", {})
    if list(exact_aliases.items()) != [("fair-cap", "fair-allocation-total-cap")]:
        raise AssertionError(
            "expected exact filter to match a single case-insensitive alias, got: "
            f"{exact_aliases}"
        )

    case_sensitive_filter_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "FAIR-CAP",
            "--list-sort-aliases-filter-mode",
            "exact",
            "--list-sort-aliases-case-sensitive",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    case_sensitive_filter_payload = json.loads(case_sensitive_filter_run.stdout)
    if case_sensitive_filter_payload.get("case_sensitive") is not True:
        raise AssertionError(
            "expected case_sensitive=true in payload when --list-sort-aliases-case-sensitive is set, got: "
            f"{case_sensitive_filter_payload.get('case_sensitive')}"
        )
    if case_sensitive_filter_payload.get("aliases") != {}:
        raise AssertionError(
            "expected case-sensitive exact filter to reject uppercase FAIR-CAP for lowercase alias keys, got: "
            f"{case_sensitive_filter_payload.get('aliases')}"
        )

    canonical_match_field_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "max-total-runs",
            "--list-sort-aliases-match-field",
            "canonical",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    canonical_match_field_payload = json.loads(canonical_match_field_run.stdout)
    canonical_field_aliases = canonical_match_field_payload.get("aliases", {})
    if not canonical_field_aliases:
        raise AssertionError("expected canonical match_field filter to emit aliases")
    if canonical_match_field_payload.get("match_field") != "canonical":
        raise AssertionError(
            "expected canonical match_field in payload, got: "
            f"{canonical_match_field_payload.get('match_field')}"
        )
    if any("max-total-runs" not in canonical for canonical in canonical_field_aliases.values()):
        raise AssertionError(
            "expected canonical match_field filter to keep only matching canonical values, got: "
            f"{canonical_field_aliases}"
        )

    alias_only_no_hit_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "max-total-runs",
            "--list-sort-aliases-match-field",
            "alias",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    alias_only_no_hit_payload = json.loads(alias_only_no_hit_run.stdout)
    if alias_only_no_hit_payload.get("aliases") != {}:
        raise AssertionError(
            "expected alias-only match_field to exclude canonical-only matches, got: "
            f"{alias_only_no_hit_payload.get('aliases')}"
        )

    invalid_max_group_size_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-max-group-size",
            "0",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_max_group_size_run.returncode == 0:
        raise AssertionError("expected non-positive --list-sort-aliases-max-group-size to fail-fast")
    if "--list-sort-aliases-max-group-size must be >= 1" not in (invalid_max_group_size_run.stderr or ""):
        raise AssertionError(
            "expected list-sort-aliases-max-group-size validation error, got: "
            f"{invalid_max_group_size_run.stderr}"
        )

    invalid_group_size_range_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-min-group-size",
            "2",
            "--list-sort-aliases-max-group-size",
            "1",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_group_size_range_run.returncode == 0:
        raise AssertionError("expected max<min list-sort-aliases group-size bounds to fail-fast")
    if "--list-sort-aliases-max-group-size must be >= --list-sort-aliases-min-group-size" not in (invalid_group_size_range_run.stderr or ""):
        raise AssertionError(
            "expected list-sort-aliases group-size bounds validation error, got: "
            f"{invalid_group_size_range_run.stderr}"
        )

    invalid_min_group_size_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-min-group-size",
            "0",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_min_group_size_run.returncode == 0:
        raise AssertionError("expected non-positive --list-sort-aliases-min-group-size to fail-fast")
    if "--list-sort-aliases-min-group-size must be >= 1" not in (invalid_min_group_size_run.stderr or ""):
        raise AssertionError(
            "expected list-sort-aliases-min-group-size validation error, got: "
            f"{invalid_min_group_size_run.stderr}"
        )

    include_exclude_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "cap",
            "--list-sort-aliases-name-not-contains",
            "total",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    include_exclude_payload = json.loads(include_exclude_run.stdout)
    include_exclude_aliases = include_exclude_payload.get("aliases", {})
    if not include_exclude_aliases:
        raise AssertionError("expected include+exclude alias filter to emit at least one alias")
    if any("total" in alias.lower() or "total" in canonical.lower() for alias, canonical in include_exclude_aliases.items()):
        raise AssertionError(
            "expected --list-sort-aliases-name-not-contains to drop aliases/canonical keys containing exclusion substring"
        )

    include_exclude_exact_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "fair",
            "--list-sort-aliases-name-not-contains",
            "fair-cap",
            "--list-sort-aliases-name-not-filter-mode",
            "exact",
            "--list-sort-aliases-sort",
            "alias",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    include_exclude_exact_payload = json.loads(include_exclude_exact_run.stdout)
    if include_exclude_exact_payload.get("name_not_filter_mode") != "exact":
        raise AssertionError(
            "expected name_not_filter_mode=exact in payload, got: "
            f"{include_exclude_exact_payload.get('name_not_filter_mode')}"
        )
    include_exclude_exact_aliases = include_exclude_exact_payload.get("aliases", {})
    if "fair-cap" in include_exclude_exact_aliases:
        raise AssertionError(
            "expected exact exclusion to remove fair-cap alias key"
        )
    if "fair-cap-desc" not in include_exclude_exact_aliases:
        raise AssertionError(
            "expected exact exclusion not to remove fair-cap-desc alias key"
        )

    invalid_sort_alias_not_contains_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-not-contains",
            "   ",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_sort_alias_not_contains_run.returncode == 0:
        raise AssertionError("expected empty --list-sort-aliases-name-not-contains to fail-fast")
    if "--list-sort-aliases-name-not-contains must include at least one non-empty character" not in (
        invalid_sort_alias_not_contains_run.stderr or ""
    ):
        raise AssertionError(
            "expected list-sort-aliases-name-not-contains validation error, got: "
            f"{invalid_sort_alias_not_contains_run.stderr}"
        )

    invalid_sort_alias_contains_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-contains",
            "   ",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_sort_alias_contains_run.returncode == 0:
        raise AssertionError("expected empty --list-sort-aliases-name-contains to fail-fast")
    if "--list-sort-aliases-name-contains must include at least one non-empty character" not in (
        invalid_sort_alias_contains_run.stderr or ""
    ):
        raise AssertionError(
            "expected list-sort-aliases-name-contains validation error, got: "
            f"{invalid_sort_alias_contains_run.stderr}"
        )

    invalid_sort_alias_not_filter_mode_run = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--list-sort-aliases",
            "--list-sort-aliases-name-not-filter-mode",
            "suffix",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if invalid_sort_alias_not_filter_mode_run.returncode == 0:
        raise AssertionError("expected unsupported --list-sort-aliases-name-not-filter-mode to fail-fast")
    if "invalid choice" not in (invalid_sort_alias_not_filter_mode_run.stderr or ""):
        raise AssertionError(
            "expected argparse invalid choice error for name-not-filter-mode, got: "
            f"{invalid_sort_alias_not_filter_mode_run.stderr}"
        )

    print("OK: build_batch_eval_plan regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
