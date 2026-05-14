"""Pin a specific version of a project's env so it won't be overwritten by pulls."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class PinRecord:
    project: str
    version: int
    pinned_by: str
    pinned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "version": self.version,
            "pinned_by": self.pinned_by,
            "pinned_at": self.pinned_at,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PinRecord":
        return cls(
            project=data["project"],
            version=data["version"],
            pinned_by=data["pinned_by"],
            pinned_at=data["pinned_at"],
            note=data.get("note", ""),
        )


class PinStore:
    _FILENAME = "pins.json"

    def __init__(self, store_dir: str) -> None:
        self._path = Path(store_dir) / self._FILENAME

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        with open(self._path) as fh:
            return json.load(fh)

    def _save(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as fh:
            json.dump(data, fh, indent=2)

    def set_pin(self, record: PinRecord) -> None:
        data = self._load()
        data[record.project] = record.to_dict()
        self._save(data)

    def get_pin(self, project: str) -> Optional[PinRecord]:
        data = self._load()
        if project not in data:
            return None
        return PinRecord.from_dict(data[project])

    def remove_pin(self, project: str) -> bool:
        data = self._load()
        if project not in data:
            return False
        del data[project]
        self._save(data)
        return True

    def list_pins(self) -> list[PinRecord]:
        data = self._load()
        return [PinRecord.from_dict(v) for v in data.values()]

    def is_pinned(self, project: str) -> bool:
        return self.get_pin(project) is not None
