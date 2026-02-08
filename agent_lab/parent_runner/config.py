from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root: Path
    sandbox_dir: Path
    baseline_dir: Path
    candidates_dir: Path
    logs_dir: Path
    tasks_path: Path


def load_settings() -> Settings:
    root = Path(__file__).resolve().parents[1]
    sandbox_dir = root / "sandbox"
    baseline_dir = sandbox_dir / "baseline"
    candidates_dir = sandbox_dir / "candidates"
    logs_dir = root / "logs"
    tasks_path = root / "evals" / "tasks.jsonl"
    return Settings(
        root=root,
        sandbox_dir=sandbox_dir,
        baseline_dir=baseline_dir,
        candidates_dir=candidates_dir,
        logs_dir=logs_dir,
        tasks_path=tasks_path,
    )
