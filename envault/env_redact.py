"""Redaction utilities for masking sensitive env values in output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Keys whose values should always be fully redacted
DEFAULT_REDACT_PATTERNS: List[str] = [
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "private_key", "auth", "credential", "access_key", "signing_key",
]

REDACT_PLACEHOLDER = "***REDACTED***"


@dataclass
class RedactConfig:
    """Configuration controlling which keys are redacted and how."""
    patterns: List[str] = field(default_factory=lambda: list(DEFAULT_REDACT_PATTERNS))
    show_length: bool = False  # if True, append value length hint e.g. ***REDACTED(12)***

    def to_dict(self) -> dict:
        return {"patterns": self.patterns, "show_length": self.show_length}

    @classmethod
    def from_dict(cls, data: dict) -> "RedactConfig":
        return cls(
            patterns=data.get("patterns", list(DEFAULT_REDACT_PATTERNS)),
            show_length=data.get("show_length", False),
        )


def _key_is_sensitive(key: str, patterns: List[str]) -> bool:
    """Return True if the key matches any redaction pattern (case-insensitive)."""
    lower = key.lower()
    return any(pat in lower for pat in patterns)


def redact_env(
    env: Dict[str, str],
    config: Optional[RedactConfig] = None,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values replaced by a placeholder."""
    if config is None:
        config = RedactConfig()
    result: Dict[str, str] = {}
    for key, value in env.items():
        if _key_is_sensitive(key, config.patterns):
            if config.show_length:
                result[key] = f"***REDACTED({len(value)})***"
            else:
                result[key] = REDACT_PLACEHOLDER
        else:
            result[key] = value
    return result


def redact_value(key: str, value: str, config: Optional[RedactConfig] = None) -> str:
    """Redact a single value if its key is sensitive."""
    if config is None:
        config = RedactConfig()
    if _key_is_sensitive(key, config.patterns):
        if config.show_length:
            return f"***REDACTED({len(value)})***"
        return REDACT_PLACEHOLDER
    return value


def format_redacted(env: Dict[str, str], config: Optional[RedactConfig] = None) -> str:
    """Return a human-readable string of the redacted env dict."""
    redacted = redact_env(env, config)
    lines = [f"{k}={v}" for k, v in sorted(redacted.items())]
    return "\n".join(lines)
