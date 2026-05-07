"""Import .env variables from external sources (dotenv files, shell environment, JSON)."""

import json
import os
from typing import Dict, Optional

from envault.env_file import parse_env


def import_from_file(path: str) -> Dict[str, str]:
    """Read and parse a .env file from the given path."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    return parse_env(content)


def import_from_shell(keys: Optional[list] = None) -> Dict[str, str]:
    """Import variables from the current shell environment.

    If *keys* is provided, only those keys are imported.
    Otherwise all environment variables are returned.
    """
    env = dict(os.environ)
    if keys:
        env = {k: env[k] for k in keys if k in env}
    return env


def import_from_json(path: str) -> Dict[str, str]:
    """Import variables from a JSON file (flat key/value object)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("JSON file must contain a top-level object")
    return {str(k): str(v) for k, v in data.items()}


def merge_envs(
    base: Dict[str, str],
    override: Dict[str, str],
    conflict: str = "override",
) -> Dict[str, str]:
    """Merge two env dicts.

    conflict:
        'override'  – values in *override* win (default)
        'keep'      – values in *base* win
        'error'     – raise ValueError on any conflicting key
    """
    if conflict not in ("override", "keep", "error"):
        raise ValueError(f"Unknown conflict strategy: {conflict!r}")

    result = dict(base)
    for key, value in override.items():
        if key in result:
            if conflict == "error":
                raise ValueError(f"Conflicting key: {key!r}")
            if conflict == "keep":
                continue
        result[key] = value
    return result
