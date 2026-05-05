"""Push and pull encrypted .env files to/from the store, with audit logging."""

from __future__ import annotations

import os
from typing import Optional

from envault.crypto import encrypt, decrypt
from envault.env_file import read_env_file, write_env_file
from envault.store import LocalStore, StoreEntry
from envault.audit import AuditEvent, AuditLog
from envault.whoami import get_current_user

_DEFAULT_AUDIT_PATH = os.path.join(".envault", "audit.json")


def _get_audit_log() -> AuditLog:
    path = os.environ.get("ENVAULT_AUDIT_LOG", _DEFAULT_AUDIT_PATH)
    return AuditLog(path)


def push(
    store: LocalStore,
    project: str,
    env_path: str,
    password: str,
    user: Optional[str] = None,
    note: Optional[str] = None,
) -> StoreEntry:
    """Encrypt the local .env file and push it to the store."""
    plaintext = read_env_file(env_path)
    ciphertext = encrypt(plaintext, password)

    existing = store.load(project)
    version = (existing.version + 1) if existing else 1

    entry = StoreEntry(project=project, version=version, ciphertext=ciphertext)
    store.save(entry)

    event = AuditEvent(
        action="push",
        project=project,
        version=version,
        user=get_current_user(user),
        note=note,
    )
    _get_audit_log().record(event)

    return entry


def pull(
    store: LocalStore,
    project: str,
    env_path: str,
    password: str,
    user: Optional[str] = None,
    note: Optional[str] = None,
) -> StoreEntry:
    """Pull the latest encrypted .env from the store and decrypt it locally."""
    entry = store.load(project)
    if entry is None:
        raise KeyError(f"No entry found for project: {project!r}")

    plaintext = decrypt(entry.ciphertext, password)
    write_env_file(env_path, plaintext)

    event = AuditEvent(
        action="pull",
        project=project,
        version=entry.version,
        user=get_current_user(user),
        note=note,
    )
    _get_audit_log().record(event)

    return entry
