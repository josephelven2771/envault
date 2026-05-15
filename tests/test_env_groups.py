"""Tests for envault.env_groups."""

import pytest

from envault.env_groups import GroupRecord, GroupStore


@pytest.fixture()
def group_store(tmp_path):
    return GroupStore(str(tmp_path))


def make_record(name="backend", keys=None, description=""):
    return GroupRecord(
        name=name,
        keys=keys or ["DB_HOST", "DB_PORT", "DB_NAME"],
        description=description,
    )


def test_record_roundtrip_dict():
    rec = make_record(description="Database vars")
    restored = GroupRecord.from_dict(rec.to_dict())
    assert restored.name == rec.name
    assert restored.keys == rec.keys
    assert restored.description == rec.description


def test_record_default_description_empty():
    rec = GroupRecord(name="g", keys=["A"])
    assert rec.description == ""


def test_set_and_get(group_store):
    rec = make_record()
    group_store.set(rec)
    fetched = group_store.get("backend")
    assert fetched is not None
    assert fetched.name == "backend"
    assert "DB_HOST" in fetched.keys


def test_get_nonexistent_returns_none(group_store):
    assert group_store.get("missing") is None


def test_delete_existing(group_store):
    group_store.set(make_record())
    result = group_store.delete("backend")
    assert result is True
    assert group_store.get("backend") is None


def test_delete_nonexistent_returns_false(group_store):
    assert group_store.delete("ghost") is False


def test_list_groups_empty(group_store):
    assert group_store.list_groups() == []


def test_list_groups_multiple(group_store):
    group_store.set(make_record("backend", ["DB_HOST"]))
    group_store.set(make_record("frontend", ["API_URL", "APP_ENV"]))
    names = {r.name for r in group_store.list_groups()}
    assert names == {"backend", "frontend"}


def test_keys_for_group(group_store):
    group_store.set(make_record("backend", ["DB_HOST", "DB_PORT"]))
    keys = group_store.keys_for_group("backend")
    assert set(keys) == {"DB_HOST", "DB_PORT"}


def test_keys_for_missing_group_returns_empty(group_store):
    assert group_store.keys_for_group("nope") == []


def test_groups_for_key(group_store):
    group_store.set(make_record("backend", ["DB_HOST", "SECRET"]))
    group_store.set(make_record("secrets", ["SECRET", "API_KEY"]))
    groups = group_store.groups_for_key("SECRET")
    assert set(groups) == {"backend", "secrets"}


def test_groups_for_key_not_in_any(group_store):
    group_store.set(make_record("backend", ["DB_HOST"]))
    assert group_store.groups_for_key("UNRELATED") == []


def test_filter_env(group_store):
    group_store.set(make_record("backend", ["DB_HOST", "DB_PORT"]))
    env = {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "prod"}
    filtered = group_store.filter_env(env, "backend")
    assert filtered == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_filter_env_missing_group_returns_empty(group_store):
    env = {"DB_HOST": "localhost"}
    assert group_store.filter_env(env, "nope") == {}
