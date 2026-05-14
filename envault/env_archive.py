"""Archive (soft-delete) and restore projects in the store."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

ARCHIVE_FILENAME = "_archive.json"


@dataclass
class ArchiveRecord:
    project: str
    archived_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    archived_by: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "archived_at": self.archived_at,
            "archived_by": self.archived_by,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArchiveRecord":
        return cls(
            project=data["project"],
            archived_at=data.get("archived_at", ""),
            archived_by=data.get("archived_by", ""),
            note=data.get("note", ""),
        )


class ArchiveStore:
    def __init__(self, store_dir: str) -> None:
        self._path = Path(store_dir) / ARCHIVE_FILENAME
        self._records: dict[str, ArchiveRecord] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._records = {k: ArchiveRecord.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._records.items()}, indent=2))

    def archive(self, project: str, archived_by: str = "", note: str = "") -> ArchiveRecord:
        record = ArchiveRecord(project=project, archived_by=archived_by, note=note)
        self._records[project] = record
        self._save()
        return record

    def restore(self, project: str) -> bool:
        if project in self._records:
            del self._records[project]
            self._save()
            return True
        return False

    def is_archived(self, project: str) -> bool:
        return project in self._records

    def get(self, project: str) -> Optional[ArchiveRecord]:
        return self._records.get(project)

    def list_archived(self) -> List[ArchiveRecord]:
        return sorted(self._records.values(), key=lambda r: r.archived_at)
