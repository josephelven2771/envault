"""Backend store abstraction for envault.

Provides a simple file-based store for encrypted .env bundles.
Each project/environment is stored as a JSON file containing
the encrypted payload and metadata.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


DEFAULT_STORE_DIR = Path.home() / ".envault" / "store"


class StoreEntry:
    """Represents a stored encrypted env bundle."""

    def __init__(self, project: str, environment: str, ciphertext: str,
                 updated_by: str, updated_at: str, version: int = 1):
        self.project = project
        self.environment = environment
        self.ciphertext = ciphertext
        self.updated_by = updated_by
        self.updated_at = updated_at
        self.version = version

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "ciphertext": self.ciphertext,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StoreEntry":
        return cls(
            project=data["project"],
            environment=data["environment"],
            ciphertext=data["ciphertext"],
            updated_by=data["updated_by"],
            updated_at=data["updated_at"],
            version=data.get("version", 1),
        )


class LocalStore:
    """File-based local store for encrypted env bundles."""

    def __init__(self, store_dir: Optional[Path] = None):
        self.store_dir = Path(store_dir) if store_dir else DEFAULT_STORE_DIR
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _entry_path(self, project: str, environment: str) -> Path:
        safe_project = project.replace("/", "_").replace("\\", "_")
        safe_env = environment.replace("/", "_").replace("\\", "_")
        return self.store_dir / f"{safe_project}__{safe_env}.json"

    def save(self, entry: StoreEntry) -> None:
        """Persist a StoreEntry to disk."""
        path = self._entry_path(entry.project, entry.environment)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry.to_dict(), f, indent=2)

    def load(self, project: str, environment: str) -> Optional[StoreEntry]:
        """Load a StoreEntry from disk, or None if not found."""
        path = self._entry_path(project, environment)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return StoreEntry.from_dict(data)

    def delete(self, project: str, environment: str) -> bool:
        """Delete a stored entry. Returns True if it existed."""
        path = self._entry_path(project, environment)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_entries(self) -> list[dict]:
        """Return a list of {project, environment} dicts for all stored entries."""
        results = []
        for f in sorted(self.store_dir.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                results.append({"project": data["project"], "environment": data["environment"]})
            except (json.JSONDecodeError, KeyError):
                continue
        return results


def now_utc() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()
