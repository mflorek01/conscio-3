SYSTEM_PROMPT = """You are a careful coding agent. Return only a unified diff patch.
Do not include markdown fences. Keep edits minimal and deterministic.
"""

TASK_PROMPT_TEMPLATE = """Task instruction:\n{instruction}\n\nGoal:\n{goal}\n\nRepository snapshot root path:\n{workspace_path}\n\nReturn a unified diff patch against files under this workspace.
"""

SELF_IMPROVE_PROMPT_TEMPLATE = """You are improving your own child-agent implementation.
Objective: {objective}
Constraints:
- Edit only files under: {candidate_workspace}
- Prefer small safe improvements.
Return a unified diff patch.
"""
