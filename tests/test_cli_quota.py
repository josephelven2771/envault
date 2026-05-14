"""Tests for envault.cli_quota CLI commands."""
from __future__ import annotations

import argparse
import pytest

from envault.store import LocalStore, StoreEntry
from envault.cli_quota import cmd_quota_status, cmd_quota_list


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "store_dir": None,
        "max_versions": 50,
        "max_projects": 20,
        "project": "testproject",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def store_dir(tmp_path):
    return str(tmp_path / "store")


def _seed(store_dir: str, project: str, n: int = 1) -> None:
    store = LocalStore(store_dir)
    for i in range(n):
        store.save(StoreEntry(
            project=project,
            version=i + 1,
            ciphertext=b"x",
            salt=b"s",
            pushed_by="u",
        ))


def test_cmd_quota_status_prints_project(store_dir, capsys):
    _seed(store_dir, "myapp", n=2)
    args = make_args(store_dir=store_dir, project="myapp")
    cmd_quota_status(args)
    out = capsys.readouterr().out
    assert "myapp" in out
    assert "2/" in out


def test_cmd_quota_status_warns_when_exceeded(store_dir, capsys):
    _seed(store_dir, "myapp", n=5)
    args = make_args(store_dir=store_dir, project="myapp", max_versions=5)
    cmd_quota_status(args)
    out = capsys.readouterr().out
    assert "WARNING" in out


def test_cmd_quota_list_empty_store(store_dir, capsys):
    args = make_args(store_dir=store_dir)
    cmd_quota_list(args)
    out = capsys.readouterr().out
    assert "No projects found" in out


def test_cmd_quota_list_shows_all_projects(store_dir, capsys):
    _seed(store_dir, "alpha", n=1)
    _seed(store_dir, "beta", n=3)
    args = make_args(store_dir=store_dir)
    cmd_quota_list(args)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_cmd_quota_list_shows_over_status(store_dir, capsys):
    _seed(store_dir, "overloaded", n=4)
    args = make_args(store_dir=store_dir, max_versions=4)
    cmd_quota_list(args)
    out = capsys.readouterr().out
    assert "OVER" in out
