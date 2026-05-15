"""Scope management: tag env entries with named scopes (e.g. dev, staging, prod)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

VALID_SCOPES = {"dev", "staging", "prod", "test", "ci"}


@dataclass
class ScopeRecord:
    project: str
    scope: str
    version: int
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "scope": self.scope,
            "version": self.version,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScopeRecord":
        return cls(
            project=data["project"],
            scope=data["scope"],
            version=data["version"],
            note=data.get("note", ""),
        )


class ScopeStore:
    def __init__(self, store_dir: str) -> None:
        self._path = Path(store_dir) / "scopes.json"
        self._data: Dict[str, ScopeRecord] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = {k: ScopeRecord.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2))

    @staticmethod
    def _key(project: str, scope: str) -> str:
        return f"{project}::{scope}"

    def set_scope(self, record: ScopeRecord) -> None:
        if record.scope not in VALID_SCOPES:
            raise ValueError(f"Unknown scope '{record.scope}'. Valid: {sorted(VALID_SCOPES)}")
        self._data[self._key(record.project, record.scope)] = record
        self._save()

    def get_scope(self, project: str, scope: str) -> Optional[ScopeRecord]:
        return self._data.get(self._key(project, scope))

    def list_scopes(self, project: str) -> List[ScopeRecord]:
        return [r for r in self._data.values() if r.project == project]

    def delete_scope(self, project: str, scope: str) -> bool:
        key = self._key(project, scope)
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False
