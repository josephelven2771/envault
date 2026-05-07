"""Project-level locking to prevent concurrent push/pull conflicts."""

import json
import os
import time
from pathlib import Path
from typing import Optional

LOCK_FILENAME = ".envault.lock"
DEFAULT_TIMEOUT = 30  # seconds
STALE_AFTER = 120  # seconds before a lock is considered stale


class LockAcquisitionError(Exception):
    """Raised when a lock cannot be acquired."""


class ProjectLock:
    def __init__(self, store_dir: str, project: str, owner: str):
        self.lock_path = Path(store_dir) / project / LOCK_FILENAME
        self.owner = owner
        self.project = project

    def _read(self) -> Optional[dict]:
        try:
            with open(self.lock_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _write(self, acquired_at: float) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lock_path, "w") as f:
            json.dump({"owner": self.owner, "acquired_at": acquired_at}, f)

    def _is_stale(self, data: dict) -> bool:
        return (time.time() - data.get("acquired_at", 0)) > STALE_AFTER

    def acquire(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            data = self._read()
            if data is None or self._is_stale(data):
                self._write(time.time())
                # Verify we actually own it (last-write-wins on local FS)
                verify = self._read()
                if verify and verify.get("owner") == self.owner:
                    return
            elif data.get("owner") == self.owner:
                return  # Re-entrant: we already hold it
            time.sleep(0.5)
        data = self._read()
        holder = data.get("owner", "unknown") if data else "unknown"
        raise LockAcquisitionError(
            f"Could not acquire lock for project '{self.project}' "
            f"(held by '{holder}'). Try again shortly."
        )

    def release(self) -> None:
        data = self._read()
        if data and data.get("owner") == self.owner:
            try:
                os.remove(self.lock_path)
            except FileNotFoundError:
                pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False
