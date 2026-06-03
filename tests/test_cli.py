import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_task_contract.cli import TEMPLATE, acceptance_ids, check_contract, main, parse_sections


VALID_CONTRACT = """# Agent Task Contract

## Objective
Build a tiny CLI that validates task contracts before agent work starts.

## Acceptance Criteria
- AC-1: `agent-task-contract check AGENT_TASK.md` exits zero for a complete contract.
- AC-2: Missing verification details produce a non-zero exit and actionable error.

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
        self.assertEqual(result.acceptance_id_count, 2)
        self.assertFalse(result.acceptance_ids_required)

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

    def test_require_acceptance_ids_passes_when_all_bullets_are_identified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENT_TASK.md"
            path.write_text(VALID_CONTRACT, encoding="utf-8")
            result = check_contract(path, require_acceptance_ids=True)

        self.assertEqual(result.status, "pass")
        self.assertEqual(result.acceptance_criteria_count, 2)
        self.assertEqual(result.acceptance_id_count, 2)
        self.assertEqual(result.acceptance_ids, ["AC-1", "AC-2"])
        self.assertTrue(result.acceptance_ids_required)

    def test_require_acceptance_ids_fails_anonymous_bullets(self) -> None:
        contract = VALID_CONTRACT.replace("AC-1: ", "").replace("AC-2: ", "")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENT_TASK.md"
            path.write_text(contract, encoding="utf-8")
            result = check_contract(path, require_acceptance_ids=True)

        self.assertEqual(result.status, "fail")
        self.assertIn(
            "Acceptance Criteria should give every bullet a stable id like AC-1.",
            [issue.message for issue in result.issues],
        )

    def test_require_acceptance_ids_fails_duplicates(self) -> None:
        contract = VALID_CONTRACT.replace("AC-2:", "AC-1:")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENT_TASK.md"
            path.write_text(contract, encoding="utf-8")
            result = check_contract(path, require_acceptance_ids=True)

        self.assertEqual(result.status, "fail")
        self.assertIn("Acceptance Criteria ids must be unique: AC-1.", [issue.message for issue in result.issues])

    def test_cli_json_reports_acceptance_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENT_TASK.md"
            path.write_text(VALID_CONTRACT, encoding="utf-8")

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["check", str(path), "--require-acceptance-ids", "--format", "json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["acceptance_id_count"], 2)
        self.assertEqual(payload["acceptance_ids"], ["AC-1", "AC-2"])
        self.assertTrue(payload["acceptance_ids_required"])

    def test_acceptance_id_parser_accepts_bracketed_ids(self) -> None:
        self.assertEqual(acceptance_ids("- [AC-7] Bracketed criterion."), ["AC-7"])


if __name__ == "__main__":
    unittest.main()
