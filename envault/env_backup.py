"""Backup and restore snapshots of encrypted env entries to/from a local archive."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from envault.store import LocalStore


@dataclass
class BackupManifest:
    created_at: str
    projects: List[str]
    entry_count: int
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "created_at": self.created_at,
            "projects": self.projects,
            "entry_count": self.entry_count,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackupManifest":
        return cls(
            created_at=data["created_at"],
            projects=data["projects"],
            entry_count=data["entry_count"],
            notes=data.get("notes", ""),
        )


def create_backup(store: LocalStore, dest: Path, notes: str = "") -> BackupManifest:
    """Write all store entries into a zip archive and return a manifest."""
    projects = store.list_projects()
    entries_written = 0
    now = datetime.now(timezone.utc).isoformat()

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for project in projects:
            versions = store.list_versions(project)
            for version in versions:
                entry = store.load(project, version)
                if entry is None:
                    continue
                arcname = f"{project}/{version}.json"
                zf.writestr(arcname, json.dumps(entry.to_dict(), indent=2))
                entries_written += 1

        manifest = BackupManifest(
            created_at=now,
            projects=projects,
            entry_count=entries_written,
            notes=notes,
        )
        zf.writestr("manifest.json", json.dumps(manifest.to_dict(), indent=2))

    return manifest


def restore_backup(store: LocalStore, src: Path, overwrite: bool = False) -> BackupManifest:
    """Read a zip archive and restore entries into the store."""
    from envault.store import StoreEntry

    with zipfile.ZipFile(src, "r") as zf:
        manifest_data = json.loads(zf.read("manifest.json"))
        manifest = BackupManifest.from_dict(manifest_data)

        for name in zf.namelist():
            if name == "manifest.json":
                continue
            parts = name.replace("\\", "/").split("/")
            if len(parts) != 2:
                continue
            project, filename = parts
            version = int(filename.replace(".json", ""))

            existing = store.load(project, version)
            if existing is not None and not overwrite:
                continue

            raw = json.loads(zf.read(name))
            entry = StoreEntry.from_dict(raw)
            store.save(project, entry)

    return manifest


def read_backup_manifest(src: Path) -> Optional[BackupManifest]:
    """Peek at the manifest inside a backup archive without restoring."""
    try:
        with zipfile.ZipFile(src, "r") as zf:
            data = json.loads(zf.read("manifest.json"))
            return BackupManifest.from_dict(data)
    except (KeyError, zipfile.BadZipFile, json.JSONDecodeError):
        return None
