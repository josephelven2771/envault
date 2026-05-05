"""Audit log for tracking push/pull operations on env files."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class AuditEvent:
    action: str  # 'push' or 'pull'
    project: str
    version: int
    user: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "project": self.project,
            "version": self.version,
            "user": self.user,
            "timestamp": self.timestamp,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEvent":
        return cls(
            action=data["action"],
            project=data["project"],
            version=data["version"],
            user=data["user"],
            timestamp=data["timestamp"],
            note=data.get("note"),
        )


class AuditLog:
    def __init__(self, log_path: str):
        self.log_path = log_path

    def _load(self) -> List[dict]:
        if not os.path.exists(self.log_path):
            return []
        with open(self.log_path, "r") as f:
            return json.load(f)

    def _save(self, entries: List[dict]) -> None:
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        with open(self.log_path, "w") as f:
            json.dump(entries, f, indent=2)

    def record(self, event: AuditEvent) -> None:
        entries = self._load()
        entries.append(event.to_dict())
        self._save(entries)

    def get_events(self, project: Optional[str] = None) -> List[AuditEvent]:
        entries = self._load()
        events = [AuditEvent.from_dict(e) for e in entries]
        if project:
            events = [e for e in events if e.project == project]
        return events

    def clear(self) -> None:
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
