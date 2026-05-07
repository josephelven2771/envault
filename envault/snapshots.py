"""Snapshot support: label a specific version of a project for easy recall."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Snapshot:
    project: str
    label: str
    version: int
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    note: str = ""

    def to_dict(self) -> Dict:
        return {
            "project": self.project,
            "label": self.label,
            "version": self.version,
            "created_at": self.created_at,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Snapshot":
        return cls(
            project=data["project"],
            label=data["label"],
            version=data["version"],
            created_at=data.get("created_at", ""),
            note=data.get("note", ""),
        )


class SnapshotStore:
    def __init__(self, store_dir: str) -> None:
        self._path = os.path.join(store_dir, "snapshots.json")
        self._data: Dict[str, Dict[str, Dict]] = {}  # project -> label -> snapshot
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path, "r", encoding="utf-8") as fh:
                self._data = json.load(fh)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    def set_snapshot(self, snapshot: Snapshot) -> None:
        self._data.setdefault(snapshot.project, {})[snapshot.label] = snapshot.to_dict()
        self._save()

    def get_snapshot(self, project: str, label: str) -> Optional[Snapshot]:
        raw = self._data.get(project, {}).get(label)
        return Snapshot.from_dict(raw) if raw else None

    def list_snapshots(self, project: str) -> List[Snapshot]:
        return [
            Snapshot.from_dict(v)
            for v in self._data.get(project, {}).values()
        ]

    def delete_snapshot(self, project: str, label: str) -> bool:
        if label in self._data.get(project, {}):
            del self._data[project][label]
            self._save()
            return True
        return False
