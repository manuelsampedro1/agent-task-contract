import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_task_contract.cli import TEMPLATE, check_contract, main, parse_sections


VALID_CONTRACT = """# Agent Task Contract

## Objective
Build a tiny CLI that validates task contracts before agent work starts.

## Acceptance Criteria
- `agent-task-contract check AGENT_TASK.md` exits zero for a complete contract.
- Missing verification details produce a non-zero exit and actionable error.

## Context
The repo is a small local-first developer tool for coding-agent workflows.

## Constraints
- Use only the Python standard library.
- Do not add network calls or external services.

## Expected Changes
- Add a CLI package under `src/agent_task_contract`.
- Add unit tests under `tests/`.

## Verification
- `make test`
- `make lint`
- `PYTHONPATH=src python3 -m agent_task_contract check examples/AGENT_TASK.md`

## Risks
- The validator could become too vague if it only checks headings.

## Out of Scope
- Do not build a hosted dashboard or SaaS workflow.
"""


class ContractTests(unittest.TestCase):
    def test_parse_sections(self) -> None:
        sections = parse_sections(VALID_CONTRACT)
        self.assertIn("Objective", sections)
        self.assertIn("Verification", sections)

    def test_valid_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENT_TASK.md"
            path.write_text(VALID_CONTRACT, encoding="utf-8")

            result = check_contract(path)

        self.assertEqual(result.status, "pass")
        self.assertEqual(result.score, 100)

    def test_template_fails_because_it_is_placeholder_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENT_TASK.md"
            path.write_text(TEMPLATE, encoding="utf-8")

            result = check_contract(path)

        self.assertEqual(result.status, "fail")
        self.assertTrue(any("placeholder" in issue.message for issue in result.issues))

    def test_json_output_returns_nonzero_for_incomplete_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENT_TASK.md"
            path.write_text("# Agent Task Contract\n\n## Objective\nDo a thing.\n", encoding="utf-8")

            with redirect_stdout(StringIO()):
                exit_code = main(["check", str(path), "--format", "json"])

        self.assertEqual(exit_code, 1)

    def test_json_shape_is_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENT_TASK.md"
            path.write_text(VALID_CONTRACT, encoding="utf-8")
            result = check_contract(path)

        payload = json.loads(json.dumps({"status": result.status, "score": result.score}))
        self.assertEqual(payload["status"], "pass")


if __name__ == "__main__":
    unittest.main()
