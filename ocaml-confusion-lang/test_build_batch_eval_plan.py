#!/usr/bin/env python3
import json
import pathlib
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
        "max_total_runs=6",
        "max_runs_per_model=0",
        "max_runs_per_prompt_condition=0",
        "cheap_first=true",
        "fair_model_allocation=false",
    ]
    for snippet in expected_snippets:
        if snippet not in quick_smoke_line:
            raise AssertionError(f"missing '{snippet}' in summary line: {quick_smoke_line}")

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

    print("OK: build_batch_eval_plan regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
