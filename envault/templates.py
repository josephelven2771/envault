"""Template support for envault: save and apply named env variable templates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Template:
    name: str
    keys: List[str]
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "keys": self.keys,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Template":
        return cls(
            name=data["name"],
            keys=data["keys"],
            description=data.get("description", ""),
        )


class TemplateStore:
    def __init__(self, store_dir: str) -> None:
        self._path = Path(store_dir) / "templates.json"

    def _load(self) -> Dict[str, dict]:
        if not self._path.exists():
            return {}
        with self._path.open("r") as fh:
            return json.load(fh)

    def _save(self, data: Dict[str, dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as fh:
            json.dump(data, fh, indent=2)

    def set(self, template: Template) -> None:
        data = self._load()
        data[template.name] = template.to_dict()
        self._save(data)

    def get(self, name: str) -> Optional[Template]:
        data = self._load()
        if name not in data:
            return None
        return Template.from_dict(data[name])

    def list(self) -> List[Template]:
        data = self._load()
        return [Template.from_dict(v) for v in data.values()]

    def delete(self, name: str) -> bool:
        data = self._load()
        if name not in data:
            return False
        del data[name]
        self._save(data)
        return True

    def apply(self, name: str, env: Dict[str, str]) -> Dict[str, str]:
        """Return a filtered env dict containing only keys defined in the template."""
        tmpl = self.get(name)
        if tmpl is None:
            raise KeyError(f"Template '{name}' not found.")
        return {k: env[k] for k in tmpl.keys if k in env}
