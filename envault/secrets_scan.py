"""Scan env variable values for potential secret leaks or weak patterns."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Patterns that suggest a value might be a plaintext secret that looks suspicious
_WEAK_PATTERNS = [
    (re.compile(r'^(password|pass|secret|key|token)$', re.IGNORECASE), "key name suggests sensitive data"),
    (re.compile(r'^.{0,7}$'), "value is very short (possible weak secret)"),
]

_PLACEHOLDER_PATTERNS = [
    re.compile(r'^(changeme|todo|fixme|replace_me|your_.*_here|example|test|dummy|placeholder)$', re.IGNORECASE),
    re.compile(r'^<.*>$'),
    re.compile(r'^\$\{.*\}$'),
]

_SENSITIVE_KEY_PATTERN = re.compile(
    r'(password|passwd|secret|token|api_?key|auth|credential|private_?key|access_?key|signing)',
    re.IGNORECASE
)


@dataclass
class ScanFinding:
    key: str
    value_preview: str
    severity: str  # 'warning' | 'error'
    message: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value_preview": self.value_preview,
            "severity": self.severity,
            "message": self.message,
        }


def _mask(value: str, show: int = 4) -> str:
    if len(value) <= show:
        return "*" * len(value)
    return value[:show] + "*" * (len(value) - show)


def scan_env(env: Dict[str, str]) -> List[ScanFinding]:
    """Scan an env dict and return a list of findings."""
    findings: List[ScanFinding] = []

    for key, value in env.items():
        is_sensitive_key = bool(_SENSITIVE_KEY_PATTERN.search(key))
        preview = _mask(value)

        # Check for placeholder values in sensitive keys
        if is_sensitive_key:
            for pat in _PLACEHOLDER_PATTERNS:
                if pat.match(value):
                    findings.append(ScanFinding(
                        key=key,
                        value_preview=preview,
                        severity="error",
                        message=f"Sensitive key '{key}' has a placeholder value.",
                    ))
                    break

        # Check for empty values in sensitive keys
        if is_sensitive_key and value.strip() == "":
            findings.append(ScanFinding(
                key=key,
                value_preview="(empty)",
                severity="error",
                message=f"Sensitive key '{key}' is empty.",
            ))

        # Check for very short values in sensitive keys
        if is_sensitive_key and 0 < len(value) < 8:
            findings.append(ScanFinding(
                key=key,
                value_preview=preview,
                severity="warning",
                message=f"Sensitive key '{key}' has a very short value (< 8 chars).",
            ))

    return findings


def format_scan_results(findings: List[ScanFinding]) -> str:
    if not findings:
        return "No issues found."
    lines = []
    for f in findings:
        lines.append(f"[{f.severity.upper()}] {f.key}: {f.message}")
    return "\n".join(lines)
