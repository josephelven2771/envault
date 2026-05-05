"""Resolve the current user identity for audit logging."""

from __future__ import annotations

import os
import socket
from typing import Optional

_CONFIG_KEY = "ENVAULT_USER"


def get_current_user(override: Optional[str] = None) -> str:
    """Return a user identifier, preferring explicit override, then env var,
    then OS username@hostname."""
    if override:
        return override
    env_user = os.environ.get(_CONFIG_KEY)
    if env_user:
        return env_user
    try:
        username = os.getlogin()
    except OSError:
        username = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "localhost"
    return f"{username}@{hostname}"
