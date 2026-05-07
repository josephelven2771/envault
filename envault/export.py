"""Export decrypted .env contents to various formats (shell, JSON, Docker)."""

import json
from typing import Dict


SUPPORTED_FORMATS = ("shell", "json", "docker")


def export_shell(env: Dict[str, str]) -> str:
    """Export env vars as shell export statements."""
    lines = []
    for key, value in sorted(env.items()):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines)


def export_json(env: Dict[str, str]) -> str:
    """Export env vars as a JSON object."""
    return json.dumps(dict(sorted(env.items())), indent=2)


def export_docker(env: Dict[str, str]) -> str:
    """Export env vars as Docker --env-file compatible format (KEY=VALUE, no quotes)."""
    lines = []
    for key, value in sorted(env.items()):
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def export_env(env: Dict[str, str], fmt: str) -> str:
    """Dispatch export to the requested format.

    Args:
        env: Dictionary of environment variables.
        fmt: One of 'shell', 'json', 'docker'.

    Returns:
        Formatted string representation.

    Raises:
        ValueError: If fmt is not a supported format.
    """
    if fmt == "shell":
        return export_shell(env)
    elif fmt == "json":
        return export_json(env)
    elif fmt == "docker":
        return export_docker(env)
    else:
        raise ValueError(
            f"Unsupported export format: '{fmt}'. "
            f"Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
