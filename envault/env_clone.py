"""Clone an existing project's latest env to a new project name."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envault.crypto import decrypt, encrypt
from envault.store import LocalStore, StoreEntry
from envault.whoami import get_current_user


@dataclass
class CloneResult:
    source_project: str
    target_project: str
    version: int
    keys_copied: int
    skipped_existing: bool

    def summary(self) -> str:
        status = "skipped (target already had data)" if self.skipped_existing else "ok"
        return (
            f"Clone {self.source_project!r} → {self.target_project!r}: "
            f"{self.keys_copied} keys at version {self.version} [{status}]"
        )


def clone_project(
    store: LocalStore,
    source_project: str,
    target_project: str,
    password: str,
    *,
    overwrite: bool = False,
    user: Optional[str] = None,
) -> CloneResult:
    """Copy the latest encrypted env from *source_project* into *target_project*.

    The ciphertext is decrypted with *password* and re-encrypted under the same
    password so each project's store entry is independent.

    Raises:
        ValueError: if the source project does not exist.
        ValueError: if the target already has entries and *overwrite* is False.
    """
    source_entry = store.load(source_project)
    if source_entry is None:
        raise ValueError(f"Source project {source_project!r} not found in store.")

    target_entry = store.load(target_project)
    if target_entry is not None and not overwrite:
        return CloneResult(
            source_project=source_project,
            target_project=target_project,
            version=target_entry.version,
            keys_copied=0,
            skipped_existing=True,
        )

    plaintext = decrypt(source_entry.ciphertext, password)

    # Count keys in the plaintext env
    keys_copied = sum(
        1
        for line in plaintext.splitlines()
        if line.strip() and not line.strip().startswith("#") and "=" in line
    )

    new_ciphertext = encrypt(plaintext, password)
    actor = user or get_current_user()
    new_version = 1 if target_entry is None else target_entry.version + 1

    new_entry = StoreEntry(
        project=target_project,
        version=new_version,
        ciphertext=new_ciphertext,
        pushed_by=actor,
    )
    store.save(new_entry)

    return CloneResult(
        source_project=source_project,
        target_project=target_project,
        version=new_version,
        keys_copied=keys_copied,
        skipped_existing=False,
    )
