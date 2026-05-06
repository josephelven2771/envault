"""Rollback support: restore a previous version of an env file from the store."""

from __future__ import annotations

from typing import Optional

from envault.store import LocalStore
from envault.crypto import decrypt
from envault.env_file import write_env_file
from envault.audit import AuditLog, AuditEvent
from envault.whoami import get_current_user


def list_versions(store: LocalStore, project: str) -> list[dict]:
    """Return a list of available versions for *project* (oldest first)."""
    versions = []
    version = 1
    while True:
        entry = store.load(project, version)
        if entry is None:
            break
        versions.append({
            "version": entry.version,
            "pushed_by": entry.pushed_by,
            "pushed_at": entry.pushed_at,
        })
        version += 1
    return versions


def rollback(
    store: LocalStore,
    project: str,
    target_version: int,
    password: str,
    output_path: str,
    audit_log: Optional[AuditLog] = None,
) -> dict:
    """Decrypt and write *target_version* of *project* to *output_path*.

    Returns the metadata dict for the restored entry.
    Raises ValueError if the requested version does not exist.
    """
    entry = store.load(project, target_version)
    if entry is None:
        raise ValueError(
            f"Version {target_version} of project '{project}' not found in store."
        )

    plaintext = decrypt(entry.ciphertext, password)
    write_env_file(output_path, plaintext)

    if audit_log is not None:
        event = AuditEvent(
            project=project,
            action="rollback",
            user=get_current_user(),
            metadata={
                "target_version": target_version,
                "output_path": output_path,
            },
        )
        audit_log.record(event)

    return {
        "version": entry.version,
        "pushed_by": entry.pushed_by,
        "pushed_at": entry.pushed_at,
        "output_path": output_path,
    }
