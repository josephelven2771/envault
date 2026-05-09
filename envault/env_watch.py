"""Watch a local .env file for changes and auto-push to the store."""

import hashlib
import time
from pathlib import Path
from typing import Callable, Optional

from envault.sync import push
from envault.store import LocalStore


def _file_hash(path: Path) -> str:
    """Return the MD5 hex digest of a file's contents."""
    data = path.read_bytes()
    return hashlib.md5(data).hexdigest()


def watch(
    env_path: Path,
    store: LocalStore,
    project: str,
    password: str,
    poll_interval: float = 2.0,
    max_iterations: Optional[int] = None,
    on_push: Optional[Callable[[str, int], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
) -> None:
    """Poll *env_path* and push to *store* whenever the file changes.

    Args:
        env_path:       Path to the .env file to watch.
        store:          LocalStore instance to push changes into.
        project:        Project name used as the store key.
        password:       Encryption password.
        poll_interval:  Seconds between file-hash checks.
        max_iterations: Stop after this many iterations (None = run forever).
        on_push:        Optional callback invoked with (project, new_version).
        on_error:       Optional callback invoked when an exception occurs.
    """
    if not env_path.exists():
        raise FileNotFoundError(f"env file not found: {env_path}")

    last_hash = _file_hash(env_path)
    iteration = 0

    while max_iterations is None or iteration < max_iterations:
        time.sleep(poll_interval)
        iteration += 1

        try:
            current_hash = _file_hash(env_path)
            if current_hash != last_hash:
                last_hash = current_hash
                entry = push(str(env_path), project, password, store)
                if on_push is not None:
                    on_push(project, entry.version)
        except Exception as exc:  # noqa: BLE001
            if on_error is not None:
                on_error(exc)
            else:
                raise
