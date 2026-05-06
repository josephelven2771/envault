"""Tests for envault.rollback."""

import os
import pytest

from envault.store import LocalStore, StoreEntry
from envault.crypto import encrypt
from envault.rollback import list_versions, rollback
from envault.audit import AuditLog


PASSWORD = "test-secret"
PROJECT = "myapp"


@pytest.fixture()
def tmp_store(tmp_path):
    return LocalStore(str(tmp_path / "store"))


@pytest.fixture()
def populated_store(tmp_store):
    """Store with two versions of MYAPP."""
    for version, content in enumerate(["KEY=v1\n", "KEY=v2\n"], start=1):
        ciphertext = encrypt(content, PASSWORD)
        entry = StoreEntry(
            project=PROJECT,
            version=version,
            ciphertext=ciphertext,
            pushed_by="alice@example.com",
            pushed_at="2024-01-01T00:00:00",
        )
        tmp_store.save(entry)
    return tmp_store


def test_list_versions_returns_all(populated_store):
    versions = list_versions(populated_store, PROJECT)
    assert len(versions) == 2
    assert versions[0]["version"] == 1
    assert versions[1]["version"] == 2


def test_list_versions_empty_project(tmp_store):
    assert list_versions(tmp_store, "unknown") == []


def test_rollback_restores_correct_content(populated_store, tmp_path):
    out = str(tmp_path / ".env")
    result = rollback(populated_store, PROJECT, 1, PASSWORD, out)

    assert result["version"] == 1
    assert result["output_path"] == out
    assert os.path.exists(out)
    assert open(out).read() == "KEY=v1\n"


def test_rollback_latest_version(populated_store, tmp_path):
    out = str(tmp_path / ".env")
    rollback(populated_store, PROJECT, 2, PASSWORD, out)
    assert open(out).read() == "KEY=v2\n"


def test_rollback_missing_version_raises(populated_store, tmp_path):
    out = str(tmp_path / ".env")
    with pytest.raises(ValueError, match="Version 99"):
        rollback(populated_store, PROJECT, 99, PASSWORD, out)


def test_rollback_wrong_password_raises(populated_store, tmp_path):
    out = str(tmp_path / ".env")
    with pytest.raises(Exception):
        rollback(populated_store, PROJECT, 1, "wrong-password", out)


def test_rollback_records_audit_event(populated_store, tmp_path):
    audit_path = str(tmp_path / "audit.json")
    log = AuditLog(audit_path)
    out = str(tmp_path / ".env")

    rollback(populated_store, PROJECT, 1, PASSWORD, out, audit_log=log)

    events = log.get_events(project=PROJECT)
    assert len(events) == 1
    assert events[0].action == "rollback"
    assert events[0].metadata["target_version"] == 1
