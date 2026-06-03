# Agent Task Contract

Validate whether an agent task brief is specific enough before handing it to Codex, Claude Code, or another coding agent.

Most agent failures start before the first edit: vague objective, missing acceptance criteria, unclear constraints, no verification plan, or no explicit non-goals. `agent-task-contract` gives those handoffs a small executable gate.

## What It Checks

- A clear objective.
- Acceptance criteria with concrete bullets and optional stable IDs.
- Context that explains why the work matters.
- Constraints that limit unsafe or distracting changes.
- Expected change areas.
- Verification commands or checks.
- Risks and out-of-scope items.

The tool is intentionally local-first and dependency-free. It reads Markdown, reports actionable issues, and exits non-zero when the contract is not ready.

## Install

Run from a local checkout:

```sh
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

Or run without installing:

```sh
PYTHONPATH=src python3 -m agent_task_contract check AGENT_TASK.md
```

## Usage

Create a template:

```sh
agent-task-contract init AGENT_TASK.md
```

Check the contract:

```sh
agent-task-contract check AGENT_TASK.md
```

JSON output for automation:

```sh
agent-task-contract check AGENT_TASK.md --format json
```

Strict acceptance traceability:

```sh
agent-task-contract check AGENT_TASK.md --require-acceptance-ids
```

Use this when the contract will feed acceptance traces, proof packets, PR
briefs, closeouts, or profile proof. Every acceptance-criteria bullet must
start with a stable ID such as `AC-1`, and duplicate IDs fail the contract.

## Example

```text
Agent Task Contract: AGENT_TASK.md
Status: pass
Score: 100/100
Acceptance ids: 3/3

No blocking issues found.
```

If a task is too vague:

```text
Agent Task Contract: AGENT_TASK.md
Status: fail
Score: 43/100

Errors:
- Missing required section: Verification
- Acceptance Criteria should include at least two concrete bullets.
- Objective still looks like placeholder text.
```

## Contract Format

Use these headings:

```md
# Agent Task Contract

## Objective
State the single outcome the agent should produce.

## Acceptance Criteria
- AC-1: The observable condition that proves the main task is done.
- AC-2: Include at least one verification check tied to the change.

## Context
Explain the repo, product, user, or workflow context the agent needs.

## Constraints
- Boundaries the agent must respect.
- Include files, APIs, style rules, or behaviors that should not change.

## Expected Changes
- Name the likely files, modules, commands, or artifacts.

## Verification
- `command to run`
- Manual checks or review gates are acceptable when code execution is not enough.

## Risks
- What could go wrong if the agent overreaches or misunderstands the task?

## Out of Scope
- Name tempting work that should not be included in this run.
```

## Why This Exists

This project complements:

- `repo-flightcheck`: is the repo ready for agent work?
- `codex-review-packet`: is the review context sharp?
- `verify-by-change`: did the closeout verification match the actual diff?
- `agent-run-ledger`: can the run be audited after the fact?

`agent-task-contract` sits before the agent starts: is the task itself good enough to run?

## Development

```sh
make test
make lint
make build
PYTHONPATH=src python3 -m agent_task_contract check examples/AGENT_TASK.md
PYTHONPATH=src python3 -m agent_task_contract check examples/AGENT_TASK.md --format json
```
