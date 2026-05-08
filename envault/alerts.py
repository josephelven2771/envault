"""Alert rules for detecting sensitive changes in .env files."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

ALERT_RULES = [
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "API_KEY",
    "PRIVATE_KEY",
    "CREDENTIALS",
    "AUTH",
]


@dataclass
class AlertRule:
    keyword: str
    description: str = ""

    def to_dict(self) -> dict:
        return {"keyword": self.keyword, "description": self.description}

    @classmethod
    def from_dict(cls, data: dict) -> "AlertRule":
        return cls(keyword=data["keyword"], description=data.get("description", ""))


@dataclass
class AlertMatch:
    key: str
    rule_keyword: str
    action: str  # 'added', 'removed', 'changed'

    def to_dict(self) -> dict:
        return {"key": self.key, "rule_keyword": self.rule_keyword, "action": self.action}


def _matches_any_rule(key: str, rules: List[AlertRule]) -> Optional[AlertRule]:
    upper = key.upper()
    for rule in rules:
        if rule.keyword.upper() in upper:
            return rule
    return None


def check_alerts(
    diff_results: List[dict],
    rules: Optional[List[AlertRule]] = None,
) -> List[AlertMatch]:
    """Check diff results against alert rules, returning matches."""
    if rules is None:
        rules = [AlertRule(k) for k in ALERT_RULES]

    matches: List[AlertMatch] = []
    for entry in diff_results:
        key = entry.get("key", "")
        action = entry.get("status", "")
        if action == "unchanged":
            continue
        rule = _matches_any_rule(key, rules)
        if rule:
            matches.append(AlertMatch(key=key, rule_keyword=rule.keyword, action=action))
    return matches


def format_alerts(matches: List[AlertMatch]) -> str:
    """Return a human-readable summary of alert matches."""
    if not matches:
        return "No sensitive-key alerts."
    lines = ["[ALERT] Sensitive key changes detected:"]
    for m in matches:
        lines.append(f"  [{m.action.upper()}] {m.key!r} matches rule '{m.rule_keyword}'")
    return "\n".join(lines)
