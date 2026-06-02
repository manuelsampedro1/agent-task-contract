.PHONY: test lint build check

PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests

lint:
	$(PYTHON) -m compileall -q src tests

build: lint

check: test lint
