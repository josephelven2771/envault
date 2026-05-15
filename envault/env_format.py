"""Formatting and normalization utilities for .env file contents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FormatIssue:
    key: str
    message: str
    auto_fixed: bool = False

    def to_dict(self) -> dict:
        return {"key": self.key, "message": self.message, "auto_fixed": self.auto_fixed}

    def __str__(self) -> str:
        tag = "[fixed]" if self.auto_fixed else "[warn]"
        return f"{tag} {self.key}: {self.message}"


@dataclass
class FormatResult:
    original: Dict[str, str]
    formatted: Dict[str, str]
    issues: List[FormatIssue] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.original != self.formatted

    def summary(self) -> str:
        if not self.issues:
            return "No formatting issues found."
        lines = [str(i) for i in self.issues]
        return "\n".join(lines)


def format_env(
    env: Dict[str, str],
    *,
    sort_keys: bool = True,
    strip_values: bool = True,
    uppercase_keys: bool = False,
    remove_empty: bool = False,
) -> FormatResult:
    """Apply formatting rules to an env dict and return a FormatResult."""
    issues: List[FormatIssue] = []
    result: Dict[str, str] = {}

    for key, value in env.items():
        new_key = key
        new_value = value

        if strip_values and value != value.strip():
            issues.append(FormatIssue(key, "value has leading/trailing whitespace", auto_fixed=True))
            new_value = value.strip()

        if uppercase_keys and key != key.upper():
            issues.append(FormatIssue(key, f"key should be uppercase (expected {key.upper()})", auto_fixed=True))
            new_key = key.upper()

        if remove_empty and new_value == "":
            issues.append(FormatIssue(new_key, "empty value removed", auto_fixed=True))
            continue

        if new_key in result:
            issues.append(FormatIssue(new_key, "duplicate key after normalisation", auto_fixed=False))
            continue

        result[new_key] = new_value

    if sort_keys:
        result = dict(sorted(result.items()))

    return FormatResult(original=dict(env), formatted=result, issues=issues)
