"""Time-to-live (TTL) enforcement for environment variable keys."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

_TTL_FILENAME = "ttl.json"


@dataclass
class TTLRecord:
    project: str
    key: str
    expires_at: datetime
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "key": self.key,
            "expires_at": self.expires_at.isoformat(),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TTLRecord":
        return cls(
            project=data["project"],
            key=data["key"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            note=data.get("note", ""),
        )

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now >= exp

    def days_remaining(self, now: Optional[datetime] = None) -> float:
        now = now or datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return (exp - now).total_seconds() / 86400


class TTLStore:
    def __init__(self, store_dir: str) -> None:
        self._path = Path(store_dir) / _TTL_FILENAME
        self._records: Dict[str, Dict[str, TTLRecord]] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        raw = json.loads(self._path.read_text())
        for project, keys in raw.items():
            self._records[project] = {
                k: TTLRecord.from_dict(v) for k, v in keys.items()
            }

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            project: {k: rec.to_dict() for k, rec in keys.items()}
            for project, keys in self._records.items()
        }
        self._path.write_text(json.dumps(data, indent=2))

    def set_ttl(self, project: str, key: str, days: float, note: str = "") -> TTLRecord:
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)
        rec = TTLRecord(project=project, key=key, expires_at=expires_at, note=note)
        self._records.setdefault(project, {})[key] = rec
        self._save()
        return rec

    def get_ttl(self, project: str, key: str) -> Optional[TTLRecord]:
        return self._records.get(project, {}).get(key)

    def remove_ttl(self, project: str, key: str) -> bool:
        if key in self._records.get(project, {}):
            del self._records[project][key]
            self._save()
            return True
        return False

    def expired_keys(self, project: str, now: Optional[datetime] = None) -> List[TTLRecord]:
        return [
            rec for rec in self._records.get(project, {}).values()
            if rec.is_expired(now)
        ]

    def all_for_project(self, project: str) -> List[TTLRecord]:
        return list(self._records.get(project, {}).values())
