"""Rename a key across all versions of a project's encrypted .env store."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from envault.crypto import decrypt, encrypt
from envault.env_file import parse_env, serialize_env
from envault.store import LocalStore


@dataclass
class RenameResult:
    project: str
    old_key: str
    new_key: str
    versions_updated: int
    versions_skipped: int

    def summary(self) -> str:
        lines = [
            f"Project  : {self.project}",
            f"Renamed  : {self.old_key!r} -> {self.new_key!r}",
            f"Updated  : {self.versions_updated} version(s)",
        ]
        if self.versions_skipped:
            lines.append(f"Skipped  : {self.versions_skipped} version(s) (key absent)")
        return "\n".join(lines)


def rename_key(
    store: LocalStore,
    project: str,
    old_key: str,
    new_key: str,
    password: str,
) -> RenameResult:
    """Rename *old_key* to *new_key* in every stored version of *project*.

    Raises ValueError if old_key == new_key or new_key is empty.
    Raises KeyError if the project has no versions.
    """
    if not new_key:
        raise ValueError("new_key must not be empty")
    if old_key == new_key:
        raise ValueError("old_key and new_key must differ")

    versions: List[int] = store.list_versions(project)
    if not versions:
        raise KeyError(f"No versions found for project {project!r}")

    updated = 0
    skipped = 0

    for version in versions:
        entry = store.load(project, version)
        if entry is None:
            skipped += 1
            continue

        env = parse_env(decrypt(entry.ciphertext, password))

        if old_key not in env:
            skipped += 1
            continue

        env[new_key] = env.pop(old_key)

        new_ciphertext = encrypt(serialize_env(env), password)
        entry.ciphertext = new_ciphertext
        store.save(project, entry)
        updated += 1

    return RenameResult(
        project=project,
        old_key=old_key,
        new_key=new_key,
        versions_updated=updated,
        versions_skipped=skipped,
    )
