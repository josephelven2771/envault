"""Access control: manage per-project allowed users and their permissions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

PERMISSION_READ = "read"
PERMISSION_WRITE = "write"
PERMISSION_ADMIN = "admin"

ALL_PERMISSIONS = {PERMISSION_READ, PERMISSION_WRITE, PERMISSION_ADMIN}


@dataclass
class AccessEntry:
    user: str
    permission: str

    def to_dict(self) -> dict:
        return {"user": self.user, "permission": self.permission}

    @classmethod
    def from_dict(cls, data: dict) -> "AccessEntry":
        return cls(user=data["user"], permission=data["permission"])


@dataclass
class AccessControl:
    _path: Path
    _entries: Dict[str, AccessEntry] = field(default_factory=dict)

    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: Dict[str, AccessEntry] = {}
        if path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self._path.read_text())
        self._entries = {
            e["user"]: AccessEntry.from_dict(e) for e in data.get("entries", [])
        }

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {"entries": [e.to_dict() for e in self._entries.values()]}
        self._path.write_text(json.dumps(data, indent=2))

    def grant(self, user: str, permission: str) -> None:
        if permission not in ALL_PERMISSIONS:
            raise ValueError(f"Unknown permission '{permission}'. Choose from {ALL_PERMISSIONS}")
        self._entries[user] = AccessEntry(user=user, permission=permission)
        self._save()

    def revoke(self, user: str) -> bool:
        if user not in self._entries:
            return False
        del self._entries[user]
        self._save()
        return True

    def get_permission(self, user: str) -> Optional[str]:
        entry = self._entries.get(user)
        return entry.permission if entry else None

    def can(self, user: str, permission: str) -> bool:
        perm = self.get_permission(user)
        if perm is None:
            return False
        order = [PERMISSION_READ, PERMISSION_WRITE, PERMISSION_ADMIN]
        return order.index(perm) >= order.index(permission)

    def list_users(self) -> List[AccessEntry]:
        return list(self._entries.values())
