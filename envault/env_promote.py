"""Promote environment variables from one project to another (e.g., staging -> production)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.store import LocalStore
from envault.crypto import decrypt, encrypt
from envault.sync import push, pull


@dataclass
class PromoteResult:
    source_project: str
    target_project: str
    promoted_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)
    overwritten_keys: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Promote: {self.source_project} -> {self.target_project}",
            f"  Promoted : {len(self.promoted_keys)} key(s)",
            f"  Skipped  : {len(self.skipped_keys)} key(s)",
            f"  Overwritten: {len(self.overwritten_keys)} key(s)",
        ]
        return "\n".join(lines)


def promote(
    store: LocalStore,
    source_project: str,
    target_project: str,
    source_password: str,
    target_password: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    author: str = "envault",
) -> PromoteResult:
    """Copy env vars from source_project into target_project.

    Args:
        store: LocalStore instance.
        source_project: Project to read from.
        target_project: Project to write into.
        source_password: Decryption password for source.
        target_password: Encryption password for target.
        keys: If given, only promote these keys. Otherwise promote all.
        overwrite: If False, skip keys already present in target.
        author: Author string recorded in the audit log.

    Returns:
        PromoteResult describing what happened.
    """
    result = PromoteResult(source_project=source_project, target_project=target_project)

    source_env = pull(store, source_project, source_password)
    if source_env is None:
        raise ValueError(f"Source project '{source_project}' has no stored environment.")

    try:
        target_env: Dict[str, str] = pull(store, target_project, target_password) or {}
    except Exception:
        target_env = {}

    candidate_keys = list(keys) if keys else list(source_env.keys())

    merged: Dict[str, str] = dict(target_env)

    for key in candidate_keys:
        if key not in source_env:
            result.skipped_keys.append(key)
            continue
        if key in target_env and not overwrite:
            result.skipped_keys.append(key)
            continue
        if key in target_env and overwrite:
            result.overwritten_keys.append(key)
        else:
            result.promoted_keys.append(key)
        merged[key] = source_env[key]

    push(store, target_project, merged, target_password, author=author)
    return result
