"""Group related environment variables under named groups for easier management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class GroupRecord:
    name: str
    keys: List[str]
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "keys": list(self.keys),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupRecord":
        return cls(
            name=data["name"],
            keys=list(data.get("keys", [])),
            description=data.get("description", ""),
        )


class GroupStore:
    def __init__(self, store_dir: str) -> None:
        self._path = Path(store_dir) / "groups.json"

    def _load(self) -> Dict[str, dict]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text())

    def _save(self, data: Dict[str, dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2))

    def set(self, record: GroupRecord) -> None:
        data = self._load()
        data[record.name] = record.to_dict()
        self._save(data)

    def get(self, name: str) -> Optional[GroupRecord]:
        data = self._load()
        if name not in data:
            return None
        return GroupRecord.from_dict(data[name])

    def delete(self, name: str) -> bool:
        data = self._load()
        if name not in data:
            return False
        del data[name]
        self._save(data)
        return True

    def list_groups(self) -> List[GroupRecord]:
        data = self._load()
        return [GroupRecord.from_dict(v) for v in data.values()]

    def keys_for_group(self, name: str) -> List[str]:
        record = self.get(name)
        return record.keys if record else []

    def groups_for_key(self, key: str) -> List[str]:
        return [r.name for r in self.list_groups() if key in r.keys]

    def filter_env(self, env: Dict[str, str], group_name: str) -> Dict[str, str]:
        keys = self.keys_for_group(group_name)
        return {k: v for k, v in env.items() if k in keys}
