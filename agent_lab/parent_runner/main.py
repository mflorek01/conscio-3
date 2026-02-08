from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from datetime import datetime, UTC
from pathlib import Path

from agent_lab.parent_runner.config import load_settings
from agent_lab.parent_runner.promote import promote_candidate
from agent_lab.parent_runner.scoring import compare
from agent_lab.evals.run_evals import run_evals


def _bootstrap_baseline(settings_root: Path, baseline_dir: Path) -> None:
    if baseline_dir.exists():
        return
    baseline_dir.parent.mkdir(parents=True, exist_ok=True)
    source = settings_root / "child_agent"
    shutil.copytree(source, baseline_dir)


def _copy_candidate(baseline_dir: Path, candidates_dir: Path) -> Path:
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = candidates_dir / ts
    candidates_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(baseline_dir, target)
    return target


def _run_self_improve(agent_dir: Path, objective: str) -> None:
    agent_file = agent_dir / "agent.py"
    sys.path.insert(0, str(agent_dir.resolve()))
    spec = importlib.util.spec_from_file_location("candidate_agent_self", agent_file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load agent module from {agent_file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.self_improve(candidate_workspace=agent_dir, objective=objective)


def run_iteration(iteration: int) -> dict:
    settings = load_settings()
    _bootstrap_baseline(settings.root, settings.baseline_dir)
    candidate_dir = _copy_candidate(settings.baseline_dir, settings.candidates_dir)

    run_id = datetime.now(UTC).strftime("run_%Y%m%dT%H%M%SZ") + f"_i{iteration}"
    run_log_dir = settings.logs_dir / run_id
    run_log_dir.mkdir(parents=True, exist_ok=True)

    _run_self_improve(candidate_dir, objective="Improve eval task pass rate safely.")

    baseline_results = run_evals(
        tasks_path=settings.tasks_path,
        agent_dir=settings.baseline_dir,
        output_dir=run_log_dir / "baseline",
    )
    candidate_results = run_evals(
        tasks_path=settings.tasks_path,
        agent_dir=candidate_dir,
        output_dir=run_log_dir / "candidate",
    )

    cmp = compare(baseline_results, candidate_results)
    promoted = cmp.improved and cmp.no_regressions
    if promoted:
        promote_candidate(candidate_dir, settings.baseline_dir)

    summary = {
        "iteration": iteration,
        "promoted": promoted,
        "comparison": {
            "improved": cmp.improved,
            "no_regressions": cmp.no_regressions,
            "baseline_total": cmp.baseline.total,
            "candidate_total": cmp.candidate.total,
            "baseline_metrics": cmp.baseline.metrics,
            "candidate_metrics": cmp.candidate.metrics,
        },
    }
    (run_log_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run parent self-improvement loop.")
    parser.add_argument("--iterations", type=int, default=1)
    args = parser.parse_args()

    for i in range(1, args.iterations + 1):
        summary = run_iteration(i)
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
