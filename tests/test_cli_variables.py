"""Tests for envault.cli_variables CLI commands."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

from envault.cli_variables import cmd_interpolate, cmd_refs
from envault.crypto import encrypt
from envault.env_file import serialize_env
from envault.store import LocalStore, StoreEntry


PASSWORD = "test-secret"


@pytest.fixture()
def store_dir(tmp_path):
    return str(tmp_path)


def _seed(store_dir: str, project: str, env: dict) -> None:
    store = LocalStore(store_dir)
    raw = serialize_env(env)
    ct = encrypt(raw, PASSWORD)
    entry = StoreEntry(project=project, version=1, ciphertext=ct, pushed_by="tester")
    store.save(entry)


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {"store_dir": ".envault", "password": PASSWORD, "format": "env"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_interpolate_env_format(store_dir, capsys):
    _seed(store_dir, "myapp", {"HOST": "db", "URL": "${HOST}:5432"})
    args = make_args(project="myapp", store_dir=store_dir, format="env")
    cmd_interpolate(args)
    out = capsys.readouterr().out
    assert "URL=db:5432" in out


def test_cmd_interpolate_json_format(store_dir, capsys):
    _seed(store_dir, "myapp", {"A": "hello", "B": "${A}_world"})
    args = make_args(project="myapp", store_dir=store_dir, format="json")
    cmd_interpolate(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["B"] == "hello_world"


def test_cmd_interpolate_missing_project_exits(store_dir):
    args = make_args(project="ghost", store_dir=store_dir)
    with pytest.raises(SystemExit):
        cmd_interpolate(args)


def test_cmd_interpolate_warns_on_undefined(store_dir, capsys):
    _seed(store_dir, "myapp", {"URL": "${UNDEFINED}/path"})
    args = make_args(project="myapp", store_dir=store_dir)
    cmd_interpolate(args)
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "UNDEFINED" in err


def test_cmd_refs_lists_references(store_dir, capsys):
    _seed(store_dir, "myapp", {"HOST": "db", "URL": "${HOST}:5432"})
    args = make_args(project="myapp", store_dir=store_dir)
    cmd_refs(args)
    out = capsys.readouterr().out
    assert "URL" in out
    assert "HOST" in out


def test_cmd_refs_no_references(store_dir, capsys):
    _seed(store_dir, "myapp", {"FOO": "bar"})
    args = make_args(project="myapp", store_dir=store_dir)
    cmd_refs(args)
    out = capsys.readouterr().out
    assert "No variable references" in out


def test_cmd_refs_missing_project_exits(store_dir):
    args = make_args(project="nope", store_dir=store_dir)
    with pytest.raises(SystemExit):
        cmd_refs(args)
