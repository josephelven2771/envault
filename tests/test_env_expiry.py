"""Tests for envault.env_expiry."""

import pytest
from datetime import date
from pathlib import Path

from envault.env_expiry import ExpiryRecord, ExpiryStore


@pytest.fixture
def expiry_store(tmp_path):
    return ExpiryStore(str(tmp_path))


def make_record(project="myapp", expires_on: date = date(2030, 1, 1), note=""):
    return ExpiryRecord(project=project, expires_on=expires_on, note=note)


# --- ExpiryRecord unit tests ---

def test_record_roundtrip_dict():
    rec = make_record(note="rotate soon")
    restored = ExpiryRecord.from_dict(rec.to_dict())
    assert restored.project == rec.project
    assert restored.expires_on == rec.expires_on
    assert restored.note == rec.note


def test_record_default_note_empty():
    rec = ExpiryRecord(project="p", expires_on=date(2025, 6, 1))
    assert rec.note == ""


def test_is_expired_past_date():
    rec = make_record(expires_on=date(2000, 1, 1))
    assert rec.is_expired(as_of=date(2024, 1, 1)) is True


def test_is_expired_future_date():
    rec = make_record(expires_on=date(2099, 12, 31))
    assert rec.is_expired(as_of=date(2024, 1, 1)) is False


def test_is_expired_same_day_not_expired():
    today = date(2025, 6, 15)
    rec = make_record(expires_on=today)
    assert rec.is_expired(as_of=today) is False


def test_days_until_expiry_positive():
    rec = make_record(expires_on=date(2025, 6, 20))
    assert rec.days_until_expiry(as_of=date(2025, 6, 10)) == 10


def test_days_until_expiry_negative_when_expired():
    rec = make_record(expires_on=date(2025, 1, 1))
    assert rec.days_until_expiry(as_of=date(2025, 6, 1)) < 0


# --- ExpiryStore tests ---

def test_set_and_get_expiry(expiry_store):
    rec = make_record(project="alpha", expires_on=date(2026, 3, 15))
    expiry_store.set_expiry(rec)
    fetched = expiry_store.get_expiry("alpha")
    assert fetched is not None
    assert fetched.expires_on == date(2026, 3, 15)


def test_get_nonexistent_returns_none(expiry_store):
    assert expiry_store.get_expiry("ghost") is None


def test_remove_existing(expiry_store):
    expiry_store.set_expiry(make_record(project="beta"))
    assert expiry_store.remove_expiry("beta") is True
    assert expiry_store.get_expiry("beta") is None


def test_remove_nonexistent_returns_false(expiry_store):
    assert expiry_store.remove_expiry("nope") is False


def test_list_all_returns_all(expiry_store):
    expiry_store.set_expiry(make_record(project="a"))
    expiry_store.set_expiry(make_record(project="b"))
    records = expiry_store.list_all()
    projects = {r.project for r in records}
    assert projects == {"a", "b"}


def test_list_expiring_within(expiry_store):
    today = date(2025, 6, 1)
    expiry_store.set_expiry(make_record(project="soon", expires_on=date(2025, 6, 10)))
    expiry_store.set_expiry(make_record(project="later", expires_on=date(2025, 12, 31)))
    results = expiry_store.list_expiring_within(30, as_of=today)
    assert len(results) == 1
    assert results[0].project == "soon"


def test_list_expired(expiry_store):
    today = date(2025, 6, 1)
    expiry_store.set_expiry(make_record(project="old", expires_on=date(2024, 1, 1)))
    expiry_store.set_expiry(make_record(project="fresh", expires_on=date(2026, 1, 1)))
    expired = expiry_store.list_expired(as_of=today)
    assert len(expired) == 1
    assert expired[0].project == "old"
