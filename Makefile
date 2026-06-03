.PHONY: test lint build smoke check

PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests

lint:
	$(PYTHON) -m compileall -q src tests

build: lint

smoke:
	PYTHONPATH=src python3 -m agent_task_contract check examples/AGENT_TASK.md --require-acceptance-ids
	PYTHONPATH=src python3 -m agent_task_contract check examples/AGENT_TASK.md --require-acceptance-ids --format json > /tmp/agent-task-contract.json

check: test lint smoke
