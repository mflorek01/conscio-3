from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScoreSummary:
    total: int
    by_task: dict[str, int]
    metrics: dict[str, float]


@dataclass
class Comparison:
    improved: bool
    no_regressions: bool
    baseline: ScoreSummary
    candidate: ScoreSummary


def summarize_results(results: dict[str, Any]) -> ScoreSummary:
    by_task: dict[str, int] = {}
    total = 0
    total_seconds = 0.0
    total_test_runs = 0
    total_patches = 0

    for task in results.get("tasks", []):
        passed = 1 if task.get("passed", False) else 0
        task_id = str(task.get("id", "unknown"))
        by_task[task_id] = passed
        total += passed
        total_seconds += float(task.get("elapsed_seconds", 0.0))
        total_test_runs += int(task.get("num_test_runs", 0))
        total_patches += int(task.get("num_patches", 0))

    return ScoreSummary(
        total=total,
        by_task=by_task,
        metrics={
            "elapsed_seconds": total_seconds,
            "num_test_runs": float(total_test_runs),
            "num_patches": float(total_patches),
        },
    )


def compare(baseline_results: dict[str, Any], candidate_results: dict[str, Any]) -> Comparison:
    base = summarize_results(baseline_results)
    cand = summarize_results(candidate_results)

    no_regressions = True
    for task_id, base_score in base.by_task.items():
        cand_score = cand.by_task.get(task_id, 0)
        if cand_score < base_score:
            no_regressions = False
            break

    improved = cand.total > base.total
    return Comparison(
        improved=improved,
        no_regressions=no_regressions,
        baseline=base,
        candidate=cand,
    )
