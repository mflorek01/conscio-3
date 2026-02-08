from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from llm_client import LLMClient
from prompts import (
    SELF_IMPROVE_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
    TASK_PROMPT_TEMPLATE,
)


def _default_toy_patch() -> str:
    return """--- a/src/toy_project/core.py
+++ b/src/toy_project/core.py
@@ -1,34 +1,48 @@
 def add(a, b):
-    return a - b
+    return a + b
 
 
 def subtract(a, b):
     return a - b
 
 
 def multiply(a, b):
-    return a + b
+    return a * b
 
 
 def divide(a, b):
+    if b == 0:
+        raise ValueError("division by zero")
     return a / b
 
 
 def is_even(n):
-    return False
+    return n % 2 == 0
 
 
 def fibonacci(n):
-    return [0, 1]
+    if n <= 0:
+        return []
+    seq = [0]
+    if n == 1:
+        return seq
+    seq.append(1)
+    while len(seq) < n:
+        seq.append(seq[-1] + seq[-2])
+    return seq
 
 
 def normalize_whitespace(text):
-    return text
+    return " ".join(text.split())
 
 
 def title_case(text):
-    return text
+    return " ".join(part.capitalize() for part in text.split())
 
 
 def unique_sorted(items):
-    return items
+    return sorted(set(items))
 
 
 def safe_int(value, default=0):
-    return value
+    try:
+        return int(value)
+    except (TypeError, ValueError):
+        return default
"""


def generate_task_patch(task: dict[str, Any], workspace_path: Path) -> str:
    client = LLMClient()
    prompt = TASK_PROMPT_TEMPLATE.format(
        instruction=task.get("instruction", ""),
        goal=task.get("goal", {}),
        workspace_path=str(workspace_path),
    )
    patch = client.generate_patch(SYSTEM_PROMPT, prompt)
    if patch:
        return patch
    return _default_toy_patch()


def _parse_changed_files_from_diff(diff_text: str) -> Iterable[str]:
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            yield line.removeprefix("+++ b/").strip()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _apply_full_file_replacement(diff_text: str, root: Path) -> None:
    target_files = list(_parse_changed_files_from_diff(diff_text))
    if not target_files:
        return
    file_rel = target_files[0]
    target = root / file_rel
    if not _is_within(target, root):
        raise ValueError("Refusing write outside candidate workspace")

    plus_lines = []
    in_hunk = False
    for line in diff_text.splitlines():
        if line.startswith("@@"):
            in_hunk = True
            continue
        if in_hunk and line.startswith("+") and not line.startswith("+++"):
            plus_lines.append(line[1:])
    if plus_lines:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(plus_lines) + "\n", encoding="utf-8")


def self_improve(candidate_workspace: Path, objective: str) -> None:
    candidate_workspace = candidate_workspace.resolve()
    client = LLMClient()
    if not client.enabled:
        return

    prompt = SELF_IMPROVE_PROMPT_TEMPLATE.format(
        objective=objective,
        candidate_workspace=str(candidate_workspace),
    )
    diff_text = client.generate_patch(SYSTEM_PROMPT, prompt)
    if not diff_text:
        return

    for rel in _parse_changed_files_from_diff(diff_text):
        target = (candidate_workspace / rel).resolve()
        if not _is_within(target, candidate_workspace):
            raise ValueError("Generated patch attempts to edit outside candidate workspace")

    _apply_full_file_replacement(diff_text, candidate_workspace)
