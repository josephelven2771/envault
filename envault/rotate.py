"""Key rotation: re-encrypt stored env data under a new password."""

from __future__ import annotations

from typing import Optional

from envault.crypto import decrypt, encrypt
from envault.store import LocalStore, StoreEntry
from envault.whoami import get_current_user


def rotate_key(
    store: LocalStore,
    project: str,
    old_password: str,
    new_password: str,
    actor: Optional[str] = None,
) -> int:
    """Re-encrypt every version of *project* from old_password to new_password.

    Returns the number of versions rotated.
    Raises ValueError if any version cannot be decrypted with old_password.
    """
    versions = store.list_versions(project)
    if not versions:
        return 0

    if old_password == new_password:
        raise ValueError("new_password must differ from old_password")

    rotated = 0
    for version in versions:
        entry = store.load(project, version)
        if entry is None:
            continue

        # Decrypt with the old password
        try:
            plaintext = decrypt(entry.ciphertext, old_password)
        except Exception as exc:
            raise ValueError(
                f"Failed to decrypt version {version} of '{project}' "
                f"with the old password: {exc}"
            ) from exc

        # Re-encrypt with the new password
        new_ciphertext = encrypt(plaintext, new_password)

        new_entry = StoreEntry(
            project=entry.project,
            version=entry.version,
            ciphertext=new_ciphertext,
            created_by=entry.created_by,
            created_at=entry.created_at,
            note=entry.note,
        )
        store.save(new_entry)
        rotated += 1

    return rotated
