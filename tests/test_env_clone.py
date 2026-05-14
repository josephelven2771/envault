"""Tests for envault.env_clone."""
from __future__ import annotations

import pytest

from envault.crypto import decrypt, encrypt
from envault.env_clone import CloneResult, clone_project
from envault.store import LocalStore, StoreEntry


@pytest.fixture()
def tmp_store(tmp_path):
    return LocalStore(str(tmp_path / "store"))


RAW_ENV = "DB_HOST=localhost\nDB_PASS=secret\nAPP_KEY=abc123\n"
PASSWORD = "hunter2"


def _seed(store: LocalStore, project: str, content: str = RAW_ENV) -> StoreEntry:
    entry = StoreEntry(
        project=project,
        version=1,
        ciphertext=encrypt(content, PASSWORD),
        pushed_by="tester",
    )
    store.save(entry)
    return entry


def test_clone_creates_target_entry(tmp_store):
    _seed(tmp_store, "prod")
    result = clone_project(tmp_store, "prod", "staging", PASSWORD)
    assert isinstance(result, CloneResult)
    assert result.target_project == "staging"
    assert result.skipped_existing is False
    assert tmp_store.load("staging") is not None


def test_clone_preserves_content(tmp_store):
    _seed(tmp_store, "prod")
    clone_project(tmp_store, "prod", "staging", PASSWORD)
    staging_entry = tmp_store.load("staging")
    plaintext = decrypt(staging_entry.ciphertext, PASSWORD)
    assert "DB_HOST=localhost" in plaintext
    assert "DB_PASS=secret" in plaintext


def test_clone_counts_keys(tmp_store):
    _seed(tmp_store, "prod")
    result = clone_project(tmp_store, "prod", "staging", PASSWORD)
    assert result.keys_copied == 3


def test_clone_target_is_independent(tmp_store):
    """Re-encrypting means source and target ciphertexts differ."""
    _seed(tmp_store, "prod")
    clone_project(tmp_store, "prod", "staging", PASSWORD)
    prod_entry = tmp_store.load("prod")
    staging_entry = tmp_store.load("staging")
    assert prod_entry.ciphertext != staging_entry.ciphertext


def test_clone_missing_source_raises(tmp_store):
    with pytest.raises(ValueError, match="not found"):
        clone_project(tmp_store, "nonexistent", "staging", PASSWORD)


def test_clone_skips_existing_target_by_default(tmp_store):
    _seed(tmp_store, "prod")
    _seed(tmp_store, "staging", "ONLY=one\n")
    result = clone_project(tmp_store, "prod", "staging", PASSWORD)
    assert result.skipped_existing is True
    assert result.keys_copied == 0
    # staging should be unchanged
    staging_entry = tmp_store.load("staging")
    assert decrypt(staging_entry.ciphertext, PASSWORD) == "ONLY=one\n"


def test_clone_overwrite_replaces_target(tmp_store):
    _seed(tmp_store, "prod")
    _seed(tmp_store, "staging", "ONLY=one\n")
    result = clone_project(tmp_store, "prod", "staging", PASSWORD, overwrite=True)
    assert result.skipped_existing is False
    staging_entry = tmp_store.load("staging")
    plaintext = decrypt(staging_entry.ciphertext, PASSWORD)
    assert "DB_HOST=localhost" in plaintext


def test_clone_result_summary_contains_projects(tmp_store):
    _seed(tmp_store, "prod")
    result = clone_project(tmp_store, "prod", "staging", PASSWORD)
    summary = result.summary()
    assert "prod" in summary
    assert "staging" in summary
    assert "ok" in summary


def test_clone_version_starts_at_one_for_new_target(tmp_store):
    _seed(tmp_store, "prod")
    result = clone_project(tmp_store, "prod", "staging", PASSWORD)
    assert result.version == 1
