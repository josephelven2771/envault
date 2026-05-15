"""Variable interpolation: resolve ${VAR} and $VAR references within an env dict."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_BRACE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_BARE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationWarning:
    key: str
    ref: str
    message: str

    def __str__(self) -> str:
        return f"[{self.key}] reference '${self.ref}' — {self.message}"


@dataclass
class InterpolationResult:
    resolved: Dict[str, str]
    warnings: List[InterpolationWarning] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return len(self.warnings) == 0


def _resolve_value(
    key: str,
    value: str,
    env: Dict[str, str],
    warnings: List[InterpolationWarning],
    depth: int = 0,
) -> str:
    if depth > 10:
        warnings.append(InterpolationWarning(key, key, "circular reference depth exceeded"))
        return value

    def _replace(m: re.Match) -> str:
        ref = m.group(1)
        if ref == key:
            warnings.append(InterpolationWarning(key, ref, "self-reference ignored"))
            return m.group(0)
        if ref not in env:
            warnings.append(InterpolationWarning(key, ref, "undefined variable"))
            return m.group(0)
        return _resolve_value(ref, env[ref], env, warnings, depth + 1)

    result = _BRACE_RE.sub(_replace, value)
    result = _BARE_RE.sub(_replace, result)
    return result


def interpolate(env: Dict[str, str]) -> InterpolationResult:
    """Return a new env dict with variable references expanded."""
    warnings: List[InterpolationWarning] = []
    resolved = {
        k: _resolve_value(k, v, env, warnings)
        for k, v in env.items()
    }
    return InterpolationResult(resolved=resolved, warnings=warnings)


def list_references(env: Dict[str, str]) -> Dict[str, List[str]]:
    """Return a mapping of key -> list of variable names it references."""
    result: Dict[str, List[str]] = {}
    for key, value in env.items():
        refs = _BRACE_RE.findall(value) + _BARE_RE.findall(value)
        unique = list(dict.fromkeys(r for r in refs if r != key))
        if unique:
            result[key] = unique
    return result
