"""Tests for envault.env_rename."""

from __future__ import annotations

import pytest

from envault.crypto import encrypt
from envault.env_file import serialize_env
from envault.env_rename import rename_key
from envault.store import LocalStore, StoreEntry


PASSWORD = "rename-test-secret"


@pytest.fixture()
def tmp_store(tmp_path):
    return LocalStore(str(tmp_path))


def _push(store: LocalStore, project: str, env: dict, version: int = 1) -> None:
    ciphertext = encrypt(serialize_env(env), PASSWORD)
    entry = StoreEntry(
        project=project,
        version=version,
        ciphertext=ciphertext,
        pushed_by="tester",
    )
    store.save(project, entry)


def test_rename_updates_key(tmp_store):
    _push(tmp_store, "proj", {"OLD_KEY": "value", "OTHER": "x"})
    result = rename_key(tmp_store, "proj", "OLD_KEY", "NEW_KEY", PASSWORD)
    assert result.versions_updated == 1
    assert result.versions_skipped == 0


def test_rename_new_key_present_old_absent(tmp_store):
    _push(tmp_store, "proj", {"OLD_KEY": "value"})
    rename_key(tmp_store, "proj", "OLD_KEY", "NEW_KEY", PASSWORD)

    from envault.crypto import decrypt
    from envault.env_file import parse_env

    entry = tmp_store.load("proj", 1)
    env = parse_env(decrypt(entry.ciphertext, PASSWORD))
    assert "NEW_KEY" in env
    assert "OLD_KEY" not in env
    assert env["NEW_KEY"] == "value"


def test_rename_preserves_other_keys(tmp_store):
    _push(tmp_store, "proj", {"OLD_KEY": "v1", "KEEP": "v2"})
    rename_key(tmp_store, "proj", "OLD_KEY", "NEW_KEY", PASSWORD)

    from envault.crypto import decrypt
    from envault.env_file import parse_env

    entry = tmp_store.load("proj", 1)
    env = parse_env(decrypt(entry.ciphertext, PASSWORD))
    assert env["KEEP"] == "v2"


def test_rename_key_absent_skips_version(tmp_store):
    _push(tmp_store, "proj", {"UNRELATED": "val"})
    result = rename_key(tmp_store, "proj", "MISSING_KEY", "NEW_KEY", PASSWORD)
    assert result.versions_updated == 0
    assert result.versions_skipped == 1


def test_rename_multiple_versions(tmp_store):
    _push(tmp_store, "proj", {"A": "1"}, version=1)
    _push(tmp_store, "proj", {"A": "2"}, version=2)
    _push(tmp_store, "proj", {"B": "3"}, version=3)  # key absent
    result = rename_key(tmp_store, "proj", "A", "Z", PASSWORD)
    assert result.versions_updated == 2
    assert result.versions_skipped == 1


def test_rename_same_key_raises(tmp_store):
    _push(tmp_store, "proj", {"KEY": "v"})
    with pytest.raises(ValueError, match="must differ"):
        rename_key(tmp_store, "proj", "KEY", "KEY", PASSWORD)


def test_rename_empty_new_key_raises(tmp_store):
    _push(tmp_store, "proj", {"KEY": "v"})
    with pytest.raises(ValueError, match="must not be empty"):
        rename_key(tmp_store, "proj", "KEY", "", PASSWORD)


def test_rename_no_versions_raises(tmp_store):
    with pytest.raises(KeyError, match="no versions"):
        rename_key(tmp_store, "empty-proj", "A", "B", PASSWORD)


def test_summary_contains_key_names(tmp_store):
    _push(tmp_store, "proj", {"OLD": "1"})
    result = rename_key(tmp_store, "proj", "OLD", "NEW", PASSWORD)
    summary = result.summary()
    assert "OLD" in summary
    assert "NEW" in summary
    assert "proj" in summary
