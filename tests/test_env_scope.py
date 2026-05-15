"""Tests for envault.env_scope."""
from __future__ import annotations

import pytest

from envault.env_scope import ScopeRecord, ScopeStore, VALID_SCOPES


@pytest.fixture
def scope_store(tmp_path):
    return ScopeStore(str(tmp_path))


def make_record(project="myapp", scope="dev", version=3, note="") -> ScopeRecord:
    return ScopeRecord(project=project, scope=scope, version=version, note=note)


def test_record_roundtrip_dict():
    r = make_record(note="initial")
    assert ScopeRecord.from_dict(r.to_dict()) == r


def test_record_default_note_empty():
    r = ScopeRecord(project="p", scope="prod", version=1)
    assert r.note == ""


def test_set_and_get_scope(scope_store):
    r = make_record(scope="staging", version=5)
    scope_store.set_scope(r)
    fetched = scope_store.get_scope("myapp", "staging")
    assert fetched is not None
    assert fetched.version == 5


def test_get_nonexistent_returns_none(scope_store):
    assert scope_store.get_scope("ghost", "prod") is None


def test_invalid_scope_raises(scope_store):
    r = ScopeRecord(project="p", scope="banana", version=1)
    with pytest.raises(ValueError, match="Unknown scope"):
        scope_store.set_scope(r)


def test_list_scopes_returns_all_for_project(scope_store):
    scope_store.set_scope(make_record(scope="dev", version=1))
    scope_store.set_scope(make_record(scope="prod", version=7))
    scope_store.set_scope(ScopeRecord(project="other", scope="ci", version=2))
    records = scope_store.list_scopes("myapp")
    assert len(records) == 2
    scopes = {r.scope for r in records}
    assert scopes == {"dev", "prod"}


def test_list_scopes_empty_project(scope_store):
    assert scope_store.list_scopes("nobody") == []


def test_delete_existing_scope(scope_store):
    scope_store.set_scope(make_record(scope="test", version=2))
    removed = scope_store.delete_scope("myapp", "test")
    assert removed is True
    assert scope_store.get_scope("myapp", "test") is None


def test_delete_nonexistent_scope_returns_false(scope_store):
    assert scope_store.delete_scope("myapp", "staging") is False


def test_persistence_across_instances(tmp_path):
    s1 = ScopeStore(str(tmp_path))
    s1.set_scope(make_record(scope="prod", version=10, note="stable"))
    s2 = ScopeStore(str(tmp_path))
    r = s2.get_scope("myapp", "prod")
    assert r is not None
    assert r.version == 10
    assert r.note == "stable"


def test_overwrite_scope_updates_version(scope_store):
    scope_store.set_scope(make_record(scope="dev", version=1))
    scope_store.set_scope(make_record(scope="dev", version=9))
    assert scope_store.get_scope("myapp", "dev").version == 9


def test_valid_scopes_set_contains_expected():
    assert "prod" in VALID_SCOPES
    assert "dev" in VALID_SCOPES
    assert "staging" in VALID_SCOPES
