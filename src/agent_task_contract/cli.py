from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_SECTIONS = [
    "Objective",
    "Acceptance Criteria",
    "Context",
    "Constraints",
    "Expected Changes",
    "Verification",
    "Risks",
    "Out of Scope",
]

PLACEHOLDER_PATTERNS = [
    r"\btbd\b",
    r"\btodo\b",
    r"\bplaceholder\b",
    r"\bfill this\b",
    r"\bto be defined\b",
    r"\bstate the\b",
    r"\bexplain the\b",
    r"\bname the\b",
]

TEMPLATE = """# Agent Task Contract

## Objective
State the single outcome the agent should produce.

## Acceptance Criteria
- The observable conditions that prove the task is done.
- Include at least two concrete checks.

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
"""


@dataclass(frozen=True)
class Issue:
    severity: str
    message: str


@dataclass(frozen=True)
class CheckResult:
    path: str
    status: str
    score: int
    issues: list[Issue]


def parse_sections(markdown: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in markdown.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def has_placeholder_text(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in PLACEHOLDER_PATTERNS)


def bullet_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if re.match(r"^\s*[-*]\s+\S+", line))


def has_verification_signal(text: str) -> bool:
    if "`" in text:
        return True
    lowered = text.lower()
    return any(word in lowered for word in ["test", "build", "lint", "review", "manual check", "verify"])


def score_from_issues(issues: Iterable[Issue]) -> int:
    score = 100
    for issue in issues:
        score -= 18 if issue.severity == "error" else 7
    return max(score, 0)


def check_contract(path: Path) -> CheckResult:
    markdown = path.read_text(encoding="utf-8")
    sections = parse_sections(markdown)
    issues: list[Issue] = []

    for section in REQUIRED_SECTIONS:
        content = sections.get(section, "")
        if not content:
            issues.append(Issue("error", f"Missing required section: {section}"))
            continue
        if len(content) < 24:
            issues.append(Issue("warn", f"{section} is very short. Add enough detail for an agent handoff."))
        if has_placeholder_text(content):
            issues.append(Issue("error", f"{section} still looks like placeholder text."))

    acceptance = sections.get("Acceptance Criteria", "")
    if acceptance and bullet_count(acceptance) < 2:
        issues.append(Issue("error", "Acceptance Criteria should include at least two concrete bullets."))

    constraints = sections.get("Constraints", "")
    if constraints and bullet_count(constraints) < 1:
        issues.append(Issue("warn", "Constraints should include at least one explicit boundary."))

    expected_changes = sections.get("Expected Changes", "")
    if expected_changes and bullet_count(expected_changes) < 1:
        issues.append(Issue("warn", "Expected Changes should name likely files, modules, or artifacts."))

    verification = sections.get("Verification", "")
    if verification and not has_verification_signal(verification):
        issues.append(Issue("error", "Verification should include a command or concrete manual check."))

    risks = sections.get("Risks", "")
    if risks and bullet_count(risks) < 1:
        issues.append(Issue("warn", "Risks should list at least one way the task can go wrong."))

    out_of_scope = sections.get("Out of Scope", "")
    if out_of_scope and bullet_count(out_of_scope) < 1:
        issues.append(Issue("warn", "Out of Scope should list tempting work to exclude."))

    score = score_from_issues(issues)
    status = "fail" if any(issue.severity == "error" for issue in issues) or score < 80 else "pass"
    return CheckResult(str(path), status, score, issues)


def render_text(result: CheckResult) -> str:
    lines = [
        f"Agent Task Contract: {result.path}",
        f"Status: {result.status}",
        f"Score: {result.score}/100",
        "",
    ]

    errors = [issue for issue in result.issues if issue.severity == "error"]
    warnings = [issue for issue in result.issues if issue.severity == "warn"]

    if not result.issues:
        lines.append("No blocking issues found.")
        return "\n".join(lines)

    if errors:
        lines.append("Errors:")
        lines.extend(f"- {issue.message}" for issue in errors)
        lines.append("")

    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {issue.message}" for issue in warnings)

    return "\n".join(lines).rstrip()


def init_contract(path: Path, force: bool) -> int:
    if path.exists() and not force:
        print(f"{path} already exists. Use --force to overwrite.")
        return 1
    path.write_text(TEMPLATE, encoding="utf-8")
    print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-task-contract")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create an AGENT_TASK.md template.")
    init_parser.add_argument("path", nargs="?", default="AGENT_TASK.md")
    init_parser.add_argument("--force", action="store_true", help="Overwrite an existing file.")

    check_parser = subparsers.add_parser("check", help="Validate an agent task contract.")
    check_parser.add_argument("path", nargs="?", default="AGENT_TASK.md")
    check_parser.add_argument("--format", choices=["text", "json"], default="text")
    check_parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings are present.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return init_contract(Path(args.path), args.force)

    path = Path(args.path)
    if not path.exists():
        print(f"{path} does not exist.")
        return 2

    result = check_contract(path)
    if args.format == "json":
        print(json.dumps(asdict(result), indent=2))
    else:
        print(render_text(result))

    if result.status == "fail":
        return 1
    if args.strict and result.issues:
        return 1
    return 0

