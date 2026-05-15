"""Key-level label/tag metadata for .env entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class LabelRecord:
    project: str
    key: str
    labels: List[str]
    note: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "key": self.key,
            "labels": list(self.labels),
            "note": self.note,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LabelRecord":
        return cls(
            project=data["project"],
            key=data["key"],
            labels=list(data.get("labels", [])),
            note=data.get("note", ""),
            updated_at=data.get("updated_at", ""),
        )


class LabelStore:
    def __init__(self, store_dir: str) -> None:
        self._path = Path(store_dir) / "labels.json"

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text())

    def _save(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2))

    def _record_id(self, project: str, key: str) -> str:
        return f"{project}::{key}"

    def set_labels(self, project: str, key: str, labels: List[str], note: str = "") -> LabelRecord:
        record = LabelRecord(project=project, key=key, labels=labels, note=note)
        data = self._load()
        data[self._record_id(project, key)] = record.to_dict()
        self._save(data)
        return record

    def get_labels(self, project: str, key: str) -> Optional[LabelRecord]:
        data = self._load()
        raw = data.get(self._record_id(project, key))
        return LabelRecord.from_dict(raw) if raw else None

    def delete_labels(self, project: str, key: str) -> bool:
        data = self._load()
        rid = self._record_id(project, key)
        if rid not in data:
            return False
        del data[rid]
        self._save(data)
        return True

    def list_by_project(self, project: str) -> List[LabelRecord]:
        data = self._load()
        prefix = f"{project}::"
        return [LabelRecord.from_dict(v) for k, v in data.items() if k.startswith(prefix)]

    def find_by_label(self, project: str, label: str) -> List[LabelRecord]:
        return [r for r in self.list_by_project(project) if label in r.labels]
