# AGENTS.md

## Goal

Maintain `agent-task-contract` as a small, dependency-free Python CLI that validates Markdown task briefs before coding-agent work starts.

## Constraints

- Keep the package local-first and standard-library only.
- Preserve the Markdown contract format documented in `README.md`.
- Do not add telemetry, network calls, hosted services, or heavyweight prompt generation.
- Keep CLI output readable for humans and JSON output stable for automation.

## Verification

Run these before closing meaningful changes:

```sh
python3 -m unittest discover -s tests
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m agent_task_contract check examples/AGENT_TASK.md
PYTHONPATH=src python3 -m agent_task_contract check examples/AGENT_TASK.md --format json
```

If package metadata or install behavior changes, also run:

```sh
python3 -m pip install -e .
agent-task-contract check examples/AGENT_TASK.md
```

## Commit Expectations

- Commit only real behavior, verification, documentation, or packaging improvements.
- Keep the working tree clean after generated caches are removed.
- Do not commit secrets, local virtualenvs, build artifacts, or generated egg-info metadata.
