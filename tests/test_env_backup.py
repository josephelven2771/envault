"""Tests for envault.env_backup: create_backup, restore_backup, read_backup_manifest."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from envault.env_backup import create_backup, restore_backup, read_backup_manifest, BackupManifest
from envault.store import LocalStore, StoreEntry


@pytest.fixture()
def tmp_store(tmp_path: Path) -> LocalStore:
    return LocalStore(str(tmp_path / "store"))


def _push(store: LocalStore, project: str, ciphertext: str = "data") -> None:
    versions = store.list_versions(project)
    version = (max(versions) + 1) if versions else 1
    entry = StoreEntry(
        project=project,
        version=version,
        ciphertext=ciphertext,
        pushed_by="test@example.com",
        pushed_at="2024-01-01T00:00:00+00:00",
    )
    store.save(project, entry)


def test_create_backup_produces_zip(tmp_store, tmp_path):
    _push(tmp_store, "alpha")
    dest = tmp_path / "backup.zip"
    manifest = create_backup(tmp_store, dest)
    assert dest.exists()
    assert manifest.entry_count == 1
    assert "alpha" in manifest.projects


def test_backup_manifest_notes_stored(tmp_store, tmp_path):
    _push(tmp_store, "beta")
    dest = tmp_path / "backup.zip"
    manifest = create_backup(tmp_store, dest, notes="release backup")
    assert manifest.notes == "release backup"


def test_backup_contains_manifest_json(tmp_store, tmp_path):
    _push(tmp_store, "gamma")
    dest = tmp_path / "backup.zip"
    create_backup(tmp_store, dest)
    with zipfile.ZipFile(dest, "r") as zf:
        assert "manifest.json" in zf.namelist()


def test_restore_recreates_entries(tmp_store, tmp_path):
    _push(tmp_store, "proj", ciphertext="secret_blob")
    dest = tmp_path / "backup.zip"
    create_backup(tmp_store, dest)

    new_store = LocalStore(str(tmp_path / "new_store"))
    restore_backup(new_store, dest)

    entry = new_store.load("proj", 1)
    assert entry is not None
    assert entry.ciphertext == "secret_blob"


def test_restore_skips_existing_without_overwrite(tmp_store, tmp_path):
    _push(tmp_store, "proj", ciphertext="original")
    dest = tmp_path / "backup.zip"
    create_backup(tmp_store, dest)

    _push(tmp_store, "proj")  # version 2
    restore_store = LocalStore(str(tmp_path / "rs"))
    _push(restore_store, "proj", ciphertext="already_there")

    restore_backup(restore_store, dest, overwrite=False)
    entry = restore_store.load("proj", 1)
    assert entry.ciphertext == "already_there"


def test_restore_overwrites_when_flag_set(tmp_store, tmp_path):
    _push(tmp_store, "proj", ciphertext="from_backup")
    dest = tmp_path / "backup.zip"
    create_backup(tmp_store, dest)

    other_store = LocalStore(str(tmp_path / "os"))
    _push(other_store, "proj", ciphertext="old_value")

    restore_backup(other_store, dest, overwrite=True)
    entry = other_store.load("proj", 1)
    assert entry.ciphertext == "from_backup"


def test_read_backup_manifest_returns_manifest(tmp_store, tmp_path):
    _push(tmp_store, "x")
    dest = tmp_path / "backup.zip"
    create_backup(tmp_store, dest, notes="peek test")

    manifest = read_backup_manifest(dest)
    assert isinstance(manifest, BackupManifest)
    assert "x" in manifest.projects
    assert manifest.notes == "peek test"


def test_read_backup_manifest_bad_file_returns_none(tmp_path):
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a zip")
    result = read_backup_manifest(bad)
    assert result is None


def test_manifest_roundtrip_dict():
    m = BackupManifest(
        created_at="2024-06-01T12:00:00+00:00",
        projects=["a", "b"],
        entry_count=4,
        notes="test",
    )
    restored = BackupManifest.from_dict(m.to_dict())
    assert restored.projects == ["a", "b"]
    assert restored.entry_count == 4
    assert restored.notes == "test"


def test_empty_store_backup_has_zero_entries(tmp_store, tmp_path):
    dest = tmp_path / "empty_backup.zip"
    manifest = create_backup(tmp_store, dest)
    assert manifest.entry_count == 0
    assert manifest.projects == []
