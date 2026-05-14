"""Alias management: map friendly names to project identifiers."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AliasRecord:
    alias: str
    project: str
    note: str = ""

    def to_dict(self) -> dict:
        return {"alias": self.alias, "project": self.project, "note": self.note}

    @classmethod
    def from_dict(cls, data: dict) -> "AliasRecord":
        return cls(
            alias=data["alias"],
            project=data["project"],
            note=data.get("note", ""),
        )


class AliasStore:
    _FILENAME = "aliases.json"

    def __init__(self, store_dir: str) -> None:
        self._path = Path(store_dir) / self._FILENAME
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, dict]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text())

    def _save(self, data: Dict[str, dict]) -> None:
        self._path.write_text(json.dumps(data, indent=2))

    def set(self, record: AliasRecord) -> None:
        data = self._load()
        data[record.alias] = record.to_dict()
        self._save(data)

    def get(self, alias: str) -> Optional[AliasRecord]:
        data = self._load()
        if alias not in data:
            return None
        return AliasRecord.from_dict(data[alias])

    def resolve(self, alias_or_project: str) -> str:
        """Return the project name for an alias, or the input unchanged."""
        record = self.get(alias_or_project)
        return record.project if record else alias_or_project

    def delete(self, alias: str) -> bool:
        data = self._load()
        if alias not in data:
            return False
        del data[alias]
        self._save(data)
        return True

    def list_all(self) -> List[AliasRecord]:
        return [AliasRecord.from_dict(v) for v in self._load().values()]
