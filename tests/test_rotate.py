"""Tests for envault.rotate — key rotation logic."""

from __future__ import annotations

import pytest

from envault.crypto import decrypt, encrypt
from envault.rotate import rotate_key
from envault.store import LocalStore, StoreEntry


OLD_PASSWORD = "old-secret"
NEW_PASSWORD = "new-secret"
PROJECT = "myapp"


@pytest.fixture()
def tmp_store(tmp_path):
    return LocalStore(str(tmp_path / "store"))


def _make_entry(project: str, version: int, password: str, content: str) -> StoreEntry:
    ciphertext = encrypt(content.encode(), password)
    return StoreEntry(
        project=project,
        version=version,
        ciphertext=ciphertext,
        created_by="tester",
        note="",
    )


def test_rotate_re_encrypts_all_versions(tmp_store):
    for v in (1, 2, 3):
        tmp_store.save(_make_entry(PROJECT, v, OLD_PASSWORD, f"KEY=v{v}"))

    count = rotate_key(tmp_store, PROJECT, OLD_PASSWORD, NEW_PASSWORD)

    assert count == 3
    for v in (1, 2, 3):
        entry = tmp_store.load(PROJECT, v)
        assert entry is not None
        plaintext = decrypt(entry.ciphertext, NEW_PASSWORD)
        assert plaintext == f"KEY=v{v}".encode()


def test_rotate_old_password_no_longer_works(tmp_store):
    tmp_store.save(_make_entry(PROJECT, 1, OLD_PASSWORD, "KEY=value"))
    rotate_key(tmp_store, PROJECT, OLD_PASSWORD, NEW_PASSWORD)

    entry = tmp_store.load(PROJECT, 1)
    assert entry is not None
    with pytest.raises(Exception):
        decrypt(entry.ciphertext, OLD_PASSWORD)


def test_rotate_empty_project_returns_zero(tmp_store):
    count = rotate_key(tmp_store, "nonexistent", OLD_PASSWORD, NEW_PASSWORD)
    assert count == 0


def test_rotate_wrong_old_password_raises(tmp_store):
    tmp_store.save(_make_entry(PROJECT, 1, OLD_PASSWORD, "KEY=value"))

    with pytest.raises(ValueError, match="old password"):
        rotate_key(tmp_store, PROJECT, "wrong-password", NEW_PASSWORD)


def test_rotate_preserves_metadata(tmp_store):
    entry = _make_entry(PROJECT, 1, OLD_PASSWORD, "KEY=value")
    entry.note = "initial push"
    tmp_store.save(entry)

    rotate_key(tmp_store, PROJECT, OLD_PASSWORD, NEW_PASSWORD)

    rotated = tmp_store.load(PROJECT, 1)
    assert rotated is not None
    assert rotated.note == "initial push"
    assert rotated.created_by == "tester"
    assert rotated.version == 1
