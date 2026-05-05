"""Utilities for reading and writing .env files."""

from pathlib import Path
from typing import Dict


def parse_env(content: str) -> Dict[str, str]:
    """Parse .env file content into a dictionary."""
    result: Dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes if present
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def serialize_env(data: Dict[str, str]) -> str:
    """Serialize a dictionary back into .env file content."""
    lines = []
    for key, value in sorted(data.items()):
        # Quote values that contain spaces or special characters
        if any(c in value for c in (" ", "#", "'", '"')):
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def read_env_file(path: str) -> str:
    """Read raw content from a .env file."""
    return Path(path).read_text(encoding="utf-8")


def write_env_file(path: str, content: str) -> None:
    """Write content to a .env file."""
    Path(path).write_text(content, encoding="utf-8")
