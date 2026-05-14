"""Tests for envault.env_pin — PinRecord and PinStore."""

from __future__ import annotations

import pytest

from envault.env_pin import PinRecord, PinStore


@pytest.fixture()
def pin_store(tmp_path):
    return PinStore(str(tmp_path))


def make_record(project="myapp", version=3, pinned_by="alice@example.com", note=""):
    return PinRecord(project=project, version=version, pinned_by=pinned_by, note=note)


def test_record_roundtrip_dict():
    rec = make_record(note="stable release")
    restored = PinRecord.from_dict(rec.to_dict())
    assert restored.project == rec.project
    assert restored.version == rec.version
    assert restored.pinned_by == rec.pinned_by
    assert restored.note == rec.note
    assert restored.pinned_at == rec.pinned_at


def test_record_default_note_empty():
    rec = make_record()
    assert rec.note == ""


def test_set_and_get_pin(pin_store):
    rec = make_record()
    pin_store.set_pin(rec)
    fetched = pin_store.get_pin("myapp")
    assert fetched is not None
    assert fetched.version == 3
    assert fetched.pinned_by == "alice@example.com"


def test_get_nonexistent_returns_none(pin_store):
    assert pin_store.get_pin("nonexistent") is None


def test_is_pinned_true(pin_store):
    pin_store.set_pin(make_record())
    assert pin_store.is_pinned("myapp") is True


def test_is_pinned_false(pin_store):
    assert pin_store.is_pinned("myapp") is False


def test_remove_existing_pin(pin_store):
    pin_store.set_pin(make_record())
    result = pin_store.remove_pin("myapp")
    assert result is True
    assert pin_store.get_pin("myapp") is None


def test_remove_nonexistent_returns_false(pin_store):
    assert pin_store.remove_pin("ghost") is False


def test_list_pins_empty(pin_store):
    assert pin_store.list_pins() == []


def test_list_pins_multiple(pin_store):
    pin_store.set_pin(make_record(project="app1", version=1))
    pin_store.set_pin(make_record(project="app2", version=5))
    pins = pin_store.list_pins()
    projects = {p.project for p in pins}
    assert projects == {"app1", "app2"}


def test_overwrite_pin_updates_version(pin_store):
    pin_store.set_pin(make_record(version=2))
    pin_store.set_pin(make_record(version=7))
    fetched = pin_store.get_pin("myapp")
    assert fetched.version == 7


def test_pin_note_preserved(pin_store):
    pin_store.set_pin(make_record(note="do not upgrade"))
    fetched = pin_store.get_pin("myapp")
    assert fetched.note == "do not upgrade"
