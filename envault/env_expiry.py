"""Track and check expiry dates for project secrets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional


@dataclass
class ExpiryRecord:
    project: str
    expires_on: date
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "expires_on": self.expires_on.isoformat(),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExpiryRecord":
        return cls(
            project=data["project"],
            expires_on=date.fromisoformat(data["expires_on"]),
            note=data.get("note", ""),
        )

    def is_expired(self, as_of: Optional[date] = None) -> bool:
        today = as_of or date.today()
        return self.expires_on < today

    def days_until_expiry(self, as_of: Optional[date] = None) -> int:
        today = as_of or date.today()
        return (self.expires_on - today).days


class ExpiryStore:
    def __init__(self, store_dir: str) -> None:
        self._path = Path(store_dir) / "expiry.json"

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        with self._path.open() as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as f:
            json.dump(data, f, indent=2)

    def set_expiry(self, record: ExpiryRecord) -> None:
        data = self._load()
        data[record.project] = record.to_dict()
        self._save(data)

    def get_expiry(self, project: str) -> Optional[ExpiryRecord]:
        data = self._load()
        if project not in data:
            return None
        return ExpiryRecord.from_dict(data[project])

    def remove_expiry(self, project: str) -> bool:
        data = self._load()
        if project not in data:
            return False
        del data[project]
        self._save(data)
        return True

    def list_all(self) -> list[ExpiryRecord]:
        data = self._load()
        return [ExpiryRecord.from_dict(v) for v in data.values()]

    def list_expiring_within(self, days: int, as_of: Optional[date] = None) -> list[ExpiryRecord]:
        return [
            r for r in self.list_all()
            if 0 <= r.days_until_expiry(as_of) <= days
        ]

    def list_expired(self, as_of: Optional[date] = None) -> list[ExpiryRecord]:
        return [r for r in self.list_all() if r.is_expired(as_of)]
