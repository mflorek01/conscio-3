# tasks.jsonl schema

Each line is a JSON object with this shape:

```json
{
  "id": "unique_task_id",
  "instruction": "Natural language coding request",
  "fixture": "toy_project",
  "check": {"type": "pytest", "args": ["-q"]},
  "goal": {"type": "tests_pass", "target": "specific behavior"}
}
```

Fields:
- `id` (string): unique task key.
- `instruction` (string): prompt given to the child agent.
- `fixture` (string): fixture folder name under `evals/fixtures/`.
- `check` (object): currently supports `{"type": "pytest", "args": ["-q"]}`.
- `goal` (object): descriptive metadata about expected outcome.
