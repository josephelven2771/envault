"""Lint .env files for common issues: duplicate keys, empty values, bad naming."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

_VALID_KEY_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')


@dataclass
class LintIssue:
    level: str  # 'error' | 'warning' | 'info'
    key: str
    message: str

    def to_dict(self) -> dict:
        return {"level": self.level, "key": self.key, "message": self.message}

    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.key}: {self.message}"


def lint_env(env: Dict[str, str]) -> List[LintIssue]:
    """Run all lint checks on a parsed env dict and return a list of issues."""
    issues: List[LintIssue] = []
    seen_keys: List[str] = []

    for key, value in env.items():
        # Duplicate key check (only meaningful if caller passes ordered dict with dupes,
        # but we track here for completeness)
        if key in seen_keys:
            issues.append(LintIssue("error", key, "Duplicate key detected."))
        seen_keys.append(key)

        # Naming convention
        if not _VALID_KEY_RE.match(key):
            issues.append(
                LintIssue("warning", key, "Key should be UPPER_SNAKE_CASE (A-Z, 0-9, _).")
            )

        # Empty value
        if value == "":
            issues.append(LintIssue("warning", key, "Value is empty."))

        # Unquoted whitespace
        if value != value.strip():
            issues.append(LintIssue("info", key, "Value has leading or trailing whitespace."))

        # Placeholder detection
        if re.search(r'<[^>]+>|\$\{[^}]+\}|CHANGEME|TODO|FIXME', value, re.IGNORECASE):
            issues.append(LintIssue("warning", key, "Value looks like an unfilled placeholder."))

    return issues


def format_lint_results(issues: List[LintIssue]) -> str:
    """Format lint issues as a human-readable string."""
    if not issues:
        return "No issues found."
    return "\n".join(str(i) for i in issues)
