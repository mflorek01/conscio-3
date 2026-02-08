# agent_lab

`agent_lab` is a safe prototype for a **parent/child self-improving coding agent loop**.

- The **parent runner** creates candidate copies from a baseline child agent.
- The parent runs a local JSONL evaluation harness for both baseline and candidate.
- If candidate score improves with no regressions, the candidate is promoted.

## Quickstart

1. Create and activate a virtual environment:

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r agent_lab/requirements.txt
   ```

3. Set API key (only env var read by code):

   ```bash
   export OPENAI_API_KEY="your_key_here"
   ```

4. Run one parent-loop iteration:

   ```bash
   python -m agent_lab.parent_runner.main --iterations 1
   ```

## Layout

- `agent_lab/parent_runner/`: parent orchestration, scoring, promotion.
- `agent_lab/child_agent/`: child logic, memory, prompts, LLM wrapper.
- `agent_lab/evals/`: tasks, fixture project, and evaluation harness.
- `agent_lab/sandbox/`: baseline + candidates.
- `agent_lab/logs/`: timestamped run artifacts.

## Notes

- Python 3.11 target.
- No network dependency except OpenAI API calls through `llm_client.py`.
- If `OPENAI_API_KEY` is missing, child operations gracefully degrade to deterministic fallback behavior.
