"""High-level sync operations for envault.

Coordinates encryption/decryption with the backend store,
providing push and pull workflows.
"""

import getpass
import os
from pathlib import Path
from typing import Optional

from envault.crypto import encrypt, decrypt
from envault.env_file import read_env_file, write_env_file, serialize_env, parse_env
from envault.store import LocalStore, StoreEntry, now_utc


def push(
    project: str,
    environment: str,
    env_path: Path,
    password: str,
    updated_by: str,
    store: Optional[LocalStore] = None,
) -> StoreEntry:
    """Encrypt a local .env file and push it to the store.

    Args:
        project: Project name/identifier.
        environment: Environment name (e.g. 'production', 'staging').
        env_path: Path to the local .env file.
        password: Encryption password.
        updated_by: Identifier of the user pushing (e.g. email).
        store: Optional LocalStore instance (defaults to a new one).

    Returns:
        The StoreEntry that was saved.
    """
    if store is None:
        store = LocalStore()

    env_vars = read_env_file(env_path)
    plaintext = serialize_env(env_vars)
    ciphertext = encrypt(plaintext, password)

    existing = store.load(project, environment)
    version = (existing.version + 1) if existing else 1

    entry = StoreEntry(
        project=project,
        environment=environment,
        ciphertext=ciphertext,
        updated_by=updated_by,
        updated_at=now_utc(),
        version=version,
    )
    store.save(entry)
    return entry


def pull(
    project: str,
    environment: str,
    env_path: Path,
    password: str,
    store: Optional[LocalStore] = None,
) -> dict:
    """Pull an encrypted env from the store and write it to a local .env file.

    Args:
        project: Project name/identifier.
        environment: Environment name.
        env_path: Destination path for the .env file.
        password: Decryption password.
        store: Optional LocalStore instance.

    Returns:
        The decrypted env vars as a dict.

    Raises:
        FileNotFoundError: If no entry exists for the given project/environment.
        ValueError: If decryption fails (wrong password).
    """
    if store is None:
        store = LocalStore()

    entry = store.load(project, environment)
    if entry is None:
        raise FileNotFoundError(
            f"No stored env for project='{project}', environment='{environment}'"
        )

    plaintext = decrypt(entry.ciphertext, password)
    env_vars = parse_env(plaintext)
    write_env_file(env_path, env_vars)
    return env_vars
