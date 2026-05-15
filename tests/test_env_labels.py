"""Tests for envault.env_labels."""
import pytest
from pathlib import Path

from envault.env_labels import LabelRecord, LabelStore


@pytest.fixture
def label_store(tmp_path):
    return LabelStore(str(tmp_path))


def make_record(project="proj", key="DB_URL", labels=None, note=""):
    return LabelRecord(
        project=project,
        key=key,
        labels=labels or ["sensitive", "required"],
        note=note,
    )


def test_record_roundtrip_dict():
    r = make_record(note="important")
    assert LabelRecord.from_dict(r.to_dict()).labels == r.labels
    assert LabelRecord.from_dict(r.to_dict()).note == "important"


def test_record_default_note_empty():
    r = make_record()
    assert r.note == ""


def test_set_and_get(label_store):
    label_store.set_labels("proj", "API_KEY", ["secret", "required"])
    record = label_store.get_labels("proj", "API_KEY")
    assert record is not None
    assert "secret" in record.labels
    assert "required" in record.labels


def test_get_nonexistent_returns_none(label_store):
    assert label_store.get_labels("proj", "MISSING_KEY") is None


def test_delete_existing(label_store):
    label_store.set_labels("proj", "X", ["foo"])
    assert label_store.delete_labels("proj", "X") is True
    assert label_store.get_labels("proj", "X") is None


def test_delete_nonexistent_returns_false(label_store):
    assert label_store.delete_labels("proj", "GHOST") is False


def test_list_by_project(label_store):
    label_store.set_labels("proj", "A", ["a"])
    label_store.set_labels("proj", "B", ["b"])
    label_store.set_labels("other", "C", ["c"])
    results = label_store.list_by_project("proj")
    keys = {r.key for r in results}
    assert keys == {"A", "B"}


def test_list_by_project_empty(label_store):
    assert label_store.list_by_project("empty") == []


def test_find_by_label_matches(label_store):
    label_store.set_labels("proj", "SECRET_KEY", ["sensitive", "required"])
    label_store.set_labels("proj", "APP_NAME", ["optional"])
    found = label_store.find_by_label("proj", "sensitive")
    assert len(found) == 1
    assert found[0].key == "SECRET_KEY"


def test_find_by_label_no_match(label_store):
    label_store.set_labels("proj", "X", ["foo"])
    assert label_store.find_by_label("proj", "bar") == []


def test_overwrite_labels(label_store):
    label_store.set_labels("proj", "KEY", ["old"])
    label_store.set_labels("proj", "KEY", ["new"])
    record = label_store.get_labels("proj", "KEY")
    assert record.labels == ["new"]


def test_labels_persisted_across_instances(tmp_path):
    s1 = LabelStore(str(tmp_path))
    s1.set_labels("proj", "K", ["persistent"])
    s2 = LabelStore(str(tmp_path))
    record = s2.get_labels("proj", "K")
    assert record is not None
    assert "persistent" in record.labels
