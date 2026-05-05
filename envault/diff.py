"""Utilities for computing and displaying diffs between .env file versions."""

from typing import Dict, List, Tuple


DiffLine = Tuple[str, str, str]  # (status, key, value)
# status: 'added', 'removed', 'changed', 'unchanged'


def diff_envs(
    old: Dict[str, str],
    new: Dict[str, str],
) -> List[DiffLine]:
    """Compare two env dicts and return a list of diff lines."""
    result: List[DiffLine] = []
    all_keys = sorted(set(old) | set(new))

    for key in all_keys:
        if key not in old:
            result.append(("added", key, new[key]))
        elif key not in new:
            result.append(("removed", key, old[key]))
        elif old[key] != new[key]:
            result.append(("changed", key, new[key]))
        else:
            result.append(("unchanged", key, old[key]))

    return result


def format_diff(diff_lines: List[DiffLine], show_unchanged: bool = False) -> str:
    """Format diff lines into a human-readable string."""
    _SYMBOLS = {
        "added": "+",
        "removed": "-",
        "changed": "~",
        "unchanged": " ",
    }
    lines = []
    for status, key, value in diff_lines:
        if status == "unchanged" and not show_unchanged:
            continue
        symbol = _SYMBOLS[status]
        masked = _mask_value(value)
        lines.append(f"{symbol} {key}={masked}")
    return "\n".join(lines)


def has_changes(diff_lines: List[DiffLine]) -> bool:
    """Return True if any diff line is not 'unchanged'."""
    return any(status != "unchanged" for status, _, _ in diff_lines)


def _mask_value(value: str) -> str:
    """Mask a secret value, showing only the first 2 chars."""
    if len(value) <= 4:
        return "***"
    return value[:2] + "*" * (len(value) - 2)
