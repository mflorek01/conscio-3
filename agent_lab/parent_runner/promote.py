from __future__ import annotations

import shutil
from pathlib import Path


def promote_candidate(candidate_dir: Path, baseline_dir: Path) -> None:
    if baseline_dir.exists():
        shutil.rmtree(baseline_dir)
    shutil.copytree(candidate_dir, baseline_dir)
