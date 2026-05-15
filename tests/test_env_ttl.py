"""Tests for envault.env_ttl — TTL enforcement for env keys."""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from envault.env_ttl import TTLRecord, TTLStore


@pytest.fixture()
def ttl_store(tmp_path: Path) -> TTLStore:
    return TTLStore(str(tmp_path))


def make_record(
    project: str = "myapp",
    key: str = "API_KEY",
    days: float = 30.0,
    note: str = "",
) -> TTLRecord:
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    return TTLRecord(project=project, key=key, expires_at=expires_at, note=note)


# --- TTLRecord unit tests ---

def test_record_roundtrip_dict():
    rec = make_record(note="rotate soon")
    restored = TTLRecord.from_dict(rec.to_dict())
    assert restored.project == rec.project
    assert restored.key == rec.key
    assert restored.note == rec.note
    assert abs((restored.expires_at.replace(tzinfo=timezone.utc) - rec.expires_at).total_seconds()) < 1


def test_record_default_note_empty():
    rec = make_record()
    assert rec.note == ""


def test_is_expired_future():
    rec = make_record(days=10)
    assert not rec.is_expired()


def test_is_expired_past():
    rec = make_record(days=-1)
    assert rec.is_expired()


def test_days_remaining_positive():
    rec = make_record(days=5)
    assert rec.days_remaining() > 4.9


def test_days_remaining_negative_when_expired():
    rec = make_record(days=-2)
    assert rec.days_remaining() < 0


# --- TTLStore tests ---

def test_set_and_get_ttl(ttl_store: TTLStore):
    ttl_store.set_ttl("proj", "DB_PASS", days=14, note="bi-weekly")
    rec = ttl_store.get_ttl("proj", "DB_PASS")
    assert rec is not None
    assert rec.key == "DB_PASS"
    assert rec.note == "bi-weekly"
    assert not rec.is_expired()


def test_get_nonexistent_returns_none(ttl_store: TTLStore):
    assert ttl_store.get_ttl("proj", "MISSING") is None


def test_remove_ttl_existing(ttl_store: TTLStore):
    ttl_store.set_ttl("proj", "TOKEN", days=7)
    removed = ttl_store.remove_ttl("proj", "TOKEN")
    assert removed is True
    assert ttl_store.get_ttl("proj", "TOKEN") is None


def test_remove_ttl_nonexistent(ttl_store: TTLStore):
    assert ttl_store.remove_ttl("proj", "GHOST") is False


def test_expired_keys_returns_only_expired(ttl_store: TTLStore):
    ttl_store.set_ttl("proj", "FRESH", days=10)
    # Manually insert an expired record
    past = datetime.now(timezone.utc) - timedelta(days=1)
    from envault.env_ttl import TTLRecord
    ttl_store._records.setdefault("proj", {})["STALE"] = TTLRecord(
        project="proj", key="STALE", expires_at=past
    )
    ttl_store._save()
    expired = ttl_store.expired_keys("proj")
    assert len(expired) == 1
    assert expired[0].key == "STALE"


def test_all_for_project(ttl_store: TTLStore):
    ttl_store.set_ttl("proj", "A", days=1)
    ttl_store.set_ttl("proj", "B", days=2)
    all_recs = ttl_store.all_for_project("proj")
    keys = {r.key for r in all_recs}
    assert keys == {"A", "B"}


def test_persistence_across_instances(tmp_path: Path):
    s1 = TTLStore(str(tmp_path))
    s1.set_ttl("env", "SECRET", days=60, note="persisted")
    s2 = TTLStore(str(tmp_path))
    rec = s2.get_ttl("env", "SECRET")
    assert rec is not None
    assert rec.note == "persisted"
