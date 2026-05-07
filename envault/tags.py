"""Tag management for envault projects.

Allows users to attach named tags (e.g. 'production', 'v1.2.0') to specific
versions of a project's env store, making it easy to reference or roll back
to a named snapshot.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Tag:
    name: str
    project: str
    version: int
    created_by: str
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "project": self.project,
            "version": self.version,
            "created_by": self.created_by,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tag":
        return cls(
            name=data["name"],
            project=data["project"],
            version=data["version"],
            created_by=data["created_by"],
            note=data.get("note", ""),
        )


class TagStore:
    """Persists tags as a JSON file inside the store directory."""

    def __init__(self, store_dir: str) -> None:
        self._path = os.path.join(store_dir, "_tags.json")
        self._tags: Dict[str, Dict[str, Tag]] = {}  # project -> name -> Tag
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path, "r") as fh:
            raw = json.load(fh)
        for project, entries in raw.items():
            self._tags[project] = {
                name: Tag.from_dict(data) for name, data in entries.items()
            }

    def _save(self) -> None:
        raw = {
            project: {name: tag.to_dict() for name, tag in entries.items()}
            for project, entries in self._tags.items()
        }
        with open(self._path, "w") as fh:
            json.dump(raw, fh, indent=2)

    def set_tag(self, tag: Tag) -> None:
        """Create or overwrite a tag for a project."""
        self._tags.setdefault(tag.project, {})[tag.name] = tag
        self._save()

    def get_tag(self, project: str, name: str) -> Optional[Tag]:
        return self._tags.get(project, {}).get(name)

    def list_tags(self, project: str) -> List[Tag]:
        return sorted(
            self._tags.get(project, {}).values(), key=lambda t: t.name
        )

    def delete_tag(self, project: str, name: str) -> bool:
        """Remove a tag; returns True if it existed."""
        if name in self._tags.get(project, {}):
            del self._tags[project][name]
            self._save()
            return True
        return False
