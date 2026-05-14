"""Tests for envault.env_archive."""
from __future__ import annotations

import pytest

from envault.env_archive import ArchiveStore, ArchiveRecord


@pytest.fixture
def archive_store(tmp_path):
    return ArchiveStore(store_dir=str(tmp_path))


def make_record(store: ArchiveStore, project: str = "myproject", **kwargs) -> ArchiveRecord:
    return store.archive(project, **kwargs)


def test_archive_record_roundtrip_dict():
    r = ArchiveRecord(project="alpha", archived_by="alice", note="cleanup")
    assert ArchiveRecord.from_dict(r.to_dict()) == r


def test_archive_record_default_note_empty():
    r = ArchiveRecord(project="beta")
    assert r.note == ""
    assert r.archived_by == ""


def test_archive_creates_record(archive_store):
    record = make_record(archive_store, "proj-a", archived_by="bob")
    assert record.project == "proj-a"
    assert record.archived_by == "bob"


def test_is_archived_true_after_archive(archive_store):
    make_record(archive_store, "proj-b")
    assert archive_store.is_archived("proj-b")


def test_is_archived_false_for_unknown(archive_store):
    assert not archive_store.is_archived("no-such-project")


def test_restore_removes_record(archive_store):
    make_record(archive_store, "proj-c")
    result = archive_store.restore("proj-c")
    assert result is True
    assert not archive_store.is_archived("proj-c")


def test_restore_nonexistent_returns_false(archive_store):
    assert archive_store.restore("ghost") is False


def test_get_returns_record(archive_store):
    make_record(archive_store, "proj-d", note="old")
    record = archive_store.get("proj-d")
    assert record is not None
    assert record.note == "old"


def test_get_nonexistent_returns_none(archive_store):
    assert archive_store.get("missing") is None


def test_list_archived_returns_all(archive_store):
    make_record(archive_store, "x")
    make_record(archive_store, "y")
    records = archive_store.list_archived()
    assert len(records) == 2
    projects = {r.project for r in records}
    assert projects == {"x", "y"}


def test_list_archived_empty(archive_store):
    assert archive_store.list_archived() == []


def test_persistence_across_instances(tmp_path):
    s1 = ArchiveStore(store_dir=str(tmp_path))
    s1.archive("persistent-proj", archived_by="carol")
    s2 = ArchiveStore(store_dir=str(tmp_path))
    assert s2.is_archived("persistent-proj")
    assert s2.get("persistent-proj").archived_by == "carol"
