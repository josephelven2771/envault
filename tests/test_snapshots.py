"""Tests for envault.snapshots module."""

import pytest

from envault.snapshots import Snapshot, SnapshotStore


@pytest.fixture
def snap_store(tmp_path):
    return SnapshotStore(str(tmp_path))


def make_snap(label: str = "v1", version: int = 1, project: str = "myapp") -> Snapshot:
    return Snapshot(project=project, label=label, version=version, note="test snap")


def test_snapshot_roundtrip_dict():
    snap = make_snap("release-1", 3)
    restored = Snapshot.from_dict(snap.to_dict())
    assert restored.label == "release-1"
    assert restored.version == 3
    assert restored.note == "test snap"
    assert restored.project == "myapp"


def test_set_and_get_snapshot(snap_store):
    snap = make_snap("staging", 5)
    snap_store.set_snapshot(snap)
    result = snap_store.get_snapshot("myapp", "staging")
    assert result is not None
    assert result.version == 5
    assert result.label == "staging"


def test_get_nonexistent_returns_none(snap_store):
    assert snap_store.get_snapshot("myapp", "ghost") is None


def test_list_snapshots_empty(snap_store):
    assert snap_store.list_snapshots("noproject") == []


def test_list_snapshots_multiple(snap_store):
    snap_store.set_snapshot(make_snap("alpha", 1))
    snap_store.set_snapshot(make_snap("beta", 2))
    snaps = snap_store.list_snapshots("myapp")
    labels = {s.label for s in snaps}
    assert labels == {"alpha", "beta"}


def test_overwrite_snapshot(snap_store):
    snap_store.set_snapshot(make_snap("prod", 1))
    snap_store.set_snapshot(make_snap("prod", 7))
    result = snap_store.get_snapshot("myapp", "prod")
    assert result.version == 7


def test_delete_existing_snapshot(snap_store):
    snap_store.set_snapshot(make_snap("old", 2))
    deleted = snap_store.delete_snapshot("myapp", "old")
    assert deleted is True
    assert snap_store.get_snapshot("myapp", "old") is None


def test_delete_nonexistent_returns_false(snap_store):
    assert snap_store.delete_snapshot("myapp", "nope") is False


def test_snapshots_persisted_across_instances(tmp_path):
    store1 = SnapshotStore(str(tmp_path))
    store1.set_snapshot(make_snap("persist", 9))
    store2 = SnapshotStore(str(tmp_path))
    result = store2.get_snapshot("myapp", "persist")
    assert result is not None
    assert result.version == 9


def test_snapshot_default_note_empty():
    snap = Snapshot(project="p", label="l", version=1)
    assert snap.note == ""


def test_snapshot_created_at_set_automatically():
    snap = Snapshot(project="p", label="l", version=1)
    assert snap.created_at != ""
