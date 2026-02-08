from __future__ import annotations

import argparse
import importlib.util
import sys
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

ALLOWED_COMMANDS = [
    ["pytest", "-q"],
    ["python", "-m", "evals.run_evals"],
]


def _load_tasks(tasks_path: Path) -> list[dict[str, Any]]:
    tasks = []
    for line in tasks_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            tasks.append(json.loads(line))
    return tasks


def _is_allowed_command(cmd: list[str]) -> bool:
    return any(cmd == allowed for allowed in ALLOWED_COMMANDS)


def _run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    if not _is_allowed_command(cmd):
        raise ValueError(f"Command not allowlisted: {cmd}")
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)


def _apply_unified_patch(diff_text: str, workspace: Path) -> int:
    patched_files = 0
    lines = diff_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]
        if not line.startswith("--- a/"):
            i += 1
            continue
        i += 1
        if i >= len(lines) or not lines[i].startswith("+++ b/"):
            raise ValueError("Malformed unified diff: missing +++ line")

        rel = lines[i].removeprefix("+++ b/").strip()
        target = (workspace / rel).resolve()
        workspace_resolved = workspace.resolve()
        if workspace_resolved not in target.parents and target != workspace_resolved:
            raise ValueError("Patch writes outside workspace")

        original = target.read_text(encoding="utf-8").splitlines() if target.exists() else []
        output: list[str] = []
        src_idx = 0
        i += 1

        while i < len(lines) and not lines[i].startswith("--- a/"):
            if not lines[i].startswith("@@"):
                i += 1
                continue
            header = lines[i]
            match = __import__('re').match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", header)
            if not match:
                raise ValueError(f"Malformed hunk header: {header}")
            old_start = int(match.group(1))

            while src_idx < old_start - 1 and src_idx < len(original):
                output.append(original[src_idx])
                src_idx += 1

            i += 1
            while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("--- a/"):
                hline = lines[i]
                if hline.startswith("+"):
                    output.append(hline[1:])
                elif hline.startswith("-"):
                    src_idx += 1
                elif hline.startswith(" "):
                    if src_idx < len(original):
                        output.append(original[src_idx])
                        src_idx += 1
                i += 1

        while src_idx < len(original):
            output.append(original[src_idx])
            src_idx += 1

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(output) + "\n", encoding="utf-8")
        patched_files += 1

    return patched_files


def _load_agent_module(agent_dir: Path):
    agent_file = agent_dir / "agent.py"
    sys.path.insert(0, str(agent_dir.resolve()))
    spec = importlib.util.spec_from_file_location("candidate_agent", agent_file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load agent module from {agent_file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_evals(tasks_path: Path, agent_dir: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fixtures_root = Path(__file__).resolve().parent / "fixtures"
    tasks = _load_tasks(tasks_path)
    agent_module = _load_agent_module(agent_dir)

    task_results: list[dict[str, Any]] = []
    trace_path = output_dir / "trace.jsonl"
    with trace_path.open("w", encoding="utf-8") as trace_file:
        for task in tasks:
            start = time.time()
            fixture_name = task["fixture"]
            fixture_source = fixtures_root / fixture_name
            with tempfile.TemporaryDirectory(prefix=f"agent_lab_{task['id']}_") as tmp:
                workspace = Path(tmp) / fixture_name
                shutil.copytree(fixture_source, workspace)

                patch = agent_module.generate_task_patch(task, workspace)
                num_patches = _apply_unified_patch(patch, workspace)

                check = task.get("check", {})
                if check.get("type") != "pytest":
                    raise ValueError("Only pytest checks are supported")
                cmd = ["pytest", *check.get("args", ["-q"])]
                proc = _run_command(cmd, cwd=workspace)
                passed = proc.returncode == 0

                elapsed = time.time() - start
                task_result = {
                    "id": task["id"],
                    "passed": passed,
                    "returncode": proc.returncode,
                    "elapsed_seconds": elapsed,
                    "num_patches": num_patches,
                    "num_test_runs": 1,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                }
                task_results.append(task_result)
                trace_file.write(json.dumps({"task": task, "result": task_result}) + "\n")

    results = {
        "tasks": task_results,
        "score": sum(1 for t in task_results if t["passed"]),
        "total": len(task_results),
    }
    (output_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local JSONL eval tasks")
    parser.add_argument("--tasks", default=str(Path(__file__).resolve().parent / "tasks.jsonl"))
    parser.add_argument("--agent-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    results = run_evals(
        tasks_path=Path(args.tasks),
        agent_dir=Path(args.agent_dir),
        output_dir=Path(args.output_dir),
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
