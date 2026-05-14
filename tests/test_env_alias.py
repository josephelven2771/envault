"""Tests for envault.env_alias and envault.cli_alias."""
from __future__ import annotations

import argparse
import pytest

from envault.env_alias import AliasRecord, AliasStore
from envault.cli_alias import (
    cmd_alias_set,
    cmd_alias_get,
    cmd_alias_resolve,
    cmd_alias_delete,
    cmd_alias_list,
)


@pytest.fixture
def alias_store(tmp_path):
    return AliasStore(str(tmp_path))


def make_record(alias="prod", project="myapp-production", note=""):
    return AliasRecord(alias=alias, project=project, note=note)


# --- Unit tests for AliasRecord ---

def test_record_roundtrip_dict():
    r = make_record(note="live env")
    assert AliasRecord.from_dict(r.to_dict()) == r


def test_record_default_note_empty():
    r = AliasRecord(alias="a", project="b")
    assert r.note == ""


# --- Unit tests for AliasStore ---

def test_set_and_get(alias_store):
    r = make_record()
    alias_store.set(r)
    fetched = alias_store.get("prod")
    assert fetched == r


def test_get_nonexistent_returns_none(alias_store):
    assert alias_store.get("ghost") is None


def test_resolve_known_alias(alias_store):
    alias_store.set(make_record(alias="staging", project="myapp-staging"))
    assert alias_store.resolve("staging") == "myapp-staging"


def test_resolve_unknown_returns_input(alias_store):
    assert alias_store.resolve("myapp-production") == "myapp-production"


def test_delete_existing(alias_store):
    alias_store.set(make_record())
    assert alias_store.delete("prod") is True
    assert alias_store.get("prod") is None


def test_delete_nonexistent_returns_false(alias_store):
    assert alias_store.delete("nope") is False


def test_list_all_returns_all(alias_store):
    alias_store.set(make_record("prod", "app-prod"))
    alias_store.set(make_record("dev", "app-dev"))
    names = {r.alias for r in alias_store.list_all()}
    assert names == {"prod", "dev"}


def test_list_all_empty(alias_store):
    assert alias_store.list_all() == []


# --- CLI command tests ---

def make_args(store_dir, **kwargs):
    ns = argparse.Namespace(store_dir=str(store_dir), **kwargs)
    return ns


def test_cmd_alias_set_creates_entry(tmp_path, capsys):
    args = make_args(tmp_path, alias="prod", project="myapp-prod", note="")
    cmd_alias_set(args)
    out = capsys.readouterr().out
    assert "prod" in out
    assert AliasStore(str(tmp_path)).get("prod") is not None


def test_cmd_alias_get_prints_mapping(tmp_path, capsys):
    store = AliasStore(str(tmp_path))
    store.set(make_record("dev", "app-dev", note="local"))
    args = make_args(tmp_path, alias="dev")
    cmd_alias_get(args)
    out = capsys.readouterr().out
    assert "app-dev" in out
    assert "local" in out


def test_cmd_alias_get_missing_exits(tmp_path):
    args = make_args(tmp_path, alias="missing")
    with pytest.raises(SystemExit):
        cmd_alias_get(args)


def test_cmd_alias_resolve_prints_project(tmp_path, capsys):
    AliasStore(str(tmp_path)).set(make_record("prod", "myapp-prod"))
    args = make_args(tmp_path, alias_or_project="prod")
    cmd_alias_resolve(args)
    assert "myapp-prod" in capsys.readouterr().out


def test_cmd_alias_delete_removes(tmp_path, capsys):
    AliasStore(str(tmp_path)).set(make_record())
    args = make_args(tmp_path, alias="prod")
    cmd_alias_delete(args)
    assert AliasStore(str(tmp_path)).get("prod") is None


def test_cmd_alias_list_shows_all(tmp_path, capsys):
    store = AliasStore(str(tmp_path))
    store.set(make_record("prod", "app-prod"))
    store.set(make_record("dev", "app-dev"))
    args = make_args(tmp_path)
    cmd_alias_list(args)
    out = capsys.readouterr().out
    assert "prod" in out
    assert "dev" in out
