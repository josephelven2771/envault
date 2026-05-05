"""Tests for envault.store — LocalStore and StoreEntry."""

import json
import pytest
from pathlib import Path

from envault.store import LocalStore, StoreEntry, now_utc


@pytest.fixture
def tmp_store(tmp_path):
    return LocalStore(store_dir=tmp_path / "store")


def make_entry(project="myapp", environment="staging", version=1):
    return StoreEntry(
        project=project,
        environment=environment,
        ciphertext="abc123encryptedpayload==",
        updated_by="alice@example.com",
        updated_at=now_utc(),
        version=version,
    )


def test_save_and_load(tmp_store):
    entry = make_entry()
    tmp_store.save(entry)
    loaded = tmp_store.load("myapp", "staging")
    assert loaded is not None
    assert loaded.project == "myapp"
    assert loaded.environment == "staging"
    assert loaded.ciphertext == entry.ciphertext
    assert loaded.updated_by == entry.updated_by
    assert loaded.version == 1


def test_load_nonexistent_returns_none(tmp_store):
    result = tmp_store.load("ghost", "production")
    assert result is None


def test_delete_existing(tmp_store):
    entry = make_entry()
    tmp_store.save(entry)
    deleted = tmp_store.delete("myapp", "staging")
    assert deleted is True
    assert tmp_store.load("myapp", "staging") is None


def test_delete_nonexistent(tmp_store):
    deleted = tmp_store.delete("ghost", "production")
    assert deleted is False


def test_list_entries_empty(tmp_store):
    assert tmp_store.list_entries() == []


def test_list_entries_multiple(tmp_store):
    tmp_store.save(make_entry("app1", "dev"))
    tmp_store.save(make_entry("app1", "prod"))
    tmp_store.save(make_entry("app2", "staging"))
    entries = tmp_store.list_entries()
    assert len(entries) == 3
    projects = {e["project"] for e in entries}
    assert projects == {"app1", "app2"}


def test_entry_roundtrip_dict():
    entry = make_entry(version=3)
    restored = StoreEntry.from_dict(entry.to_dict())
    assert restored.project == entry.project
    assert restored.version == 3
    assert restored.ciphertext == entry.ciphertext


def test_store_creates_dir(tmp_path):
    deep_path = tmp_path / "a" / "b" / "c"
    store = LocalStore(store_dir=deep_path)
    assert deep_path.exists()


def test_overwrite_increments_not_automatic(tmp_store):
    """Store.save does not auto-increment; caller controls version."""
    entry_v1 = make_entry(version=1)
    tmp_store.save(entry_v1)
    entry_v2 = make_entry(version=2)
    tmp_store.save(entry_v2)
    loaded = tmp_store.load("myapp", "staging")
    assert loaded.version == 2
