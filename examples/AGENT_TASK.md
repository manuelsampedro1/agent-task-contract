# Agent Task Contract

## Objective
Add a dependency-free CLI that validates Markdown task contracts before a coding agent starts work.

## Acceptance Criteria
- `PYTHONPATH=src python3 -m agent_task_contract check examples/AGENT_TASK.md` exits with status 0.
- Incomplete contracts return a non-zero exit code with actionable messages.
- JSON output includes `path`, `status`, `score`, and `issues`.

## Context
The project is for builders using Codex, Claude Code, or similar coding agents in local repositories. It should reduce vague handoffs before edits begin.

## Constraints
- Use the Python standard library only.
- Keep the contract format readable as plain Markdown.
- Do not add a server, hosted dashboard, telemetry, or network dependency.

## Expected Changes
- Python package under `src/agent_task_contract`.
- Unit tests under `tests/`.
- README usage examples and a sample task contract.

## Verification
- `make test`
- `make lint`
- `PYTHONPATH=src python3 -m agent_task_contract check examples/AGENT_TASK.md`
- `PYTHONPATH=src python3 -m agent_task_contract check examples/AGENT_TASK.md --format json`

## Risks
- The checker could reward headings without useful content.
- The rules could become too rigid for small tasks if warnings are treated as hard errors by default.

## Out of Scope
- Do not build a prompt-generation system.
- Do not inspect private repo content beyond the contract file supplied by the user.
- Do not claim that a passing contract guarantees good agent output.
