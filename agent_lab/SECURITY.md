# SECURITY.md

## Threat model

This project assumes an untrusted or partially trusted child coding agent that may produce unsafe patches or shell commands.

Potential risks:
- Escaping candidate workspace and altering parent or host files.
- Running arbitrary commands during evaluation.
- Data exfiltration via environment variables.
- Contaminating task results between runs.

## Mitigations

1. **Workspace write boundaries**
   - Child self-improvement writes are constrained to files under its own candidate directory.
   - Path resolution checks reject writes outside the candidate root.

2. **Command allowlist**
   - Eval harness permits only two subprocess command templates:
     - `pytest -q`
     - `python -m evals.run_evals`
   - Any other command is rejected.

3. **Fresh fixture copy per task**
   - Every eval task runs in a brand-new temporary copy of the fixture project.
   - No cross-task mutation persists.

4. **Environment minimization**
   - Code reads only `OPENAI_API_KEY` from environment.
   - No other environment variables are consumed.

5. **Auditability**
   - Parent writes run logs under `logs/<run_id>/`.
   - Evals write `results.json` and `trace.jsonl` for post-mortem analysis.

## Operational guidance

- Keep the host Python environment isolated (virtualenv/container).
- Do not expand allowlisted subprocess commands without review.
- Treat generated patches as untrusted input.
