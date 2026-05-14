"""Tests for envault.cli_pin subcommands."""

from __future__ import annotations

import argparse
import pytest

from envault.cli_pin import cmd_pin, cmd_unpin, cmd_pin_status, cmd_pin_list
from envault.env_pin import PinStore, PinRecord


def make_args(store_dir, **kwargs):
    ns = argparse.Namespace(store_dir=str(store_dir))
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


@pytest.fixture()
def store_dir(tmp_path):
    return tmp_path


def _seed(store_dir, project="myapp", version=2):
    ps = PinStore(str(store_dir))
    ps.set_pin(PinRecord(project=project, version=version, pinned_by="ci@bot"))
    return ps


def test_cmd_pin_creates_entry(store_dir, capsys):
    args = make_args(store_dir, project="myapp", version=4, note="")
    cmd_pin(args)
    ps = PinStore(str(store_dir))
    rec = ps.get_pin("myapp")
    assert rec is not None
    assert rec.version == 4


def test_cmd_pin_prints_confirmation(store_dir, capsys):
    args = make_args(store_dir, project="myapp", version=4, note="")
    cmd_pin(args)
    out = capsys.readouterr().out
    assert "myapp" in out
    assert "4" in out


def test_cmd_unpin_existing(store_dir, capsys):
    _seed(store_dir)
    args = make_args(store_dir, project="myapp")
    cmd_unpin(args)
    ps = PinStore(str(store_dir))
    assert ps.get_pin("myapp") is None
    out = capsys.readouterr().out
    assert "Unpinned" in out


def test_cmd_unpin_nonexistent_exits(store_dir):
    args = make_args(store_dir, project="ghost")
    with pytest.raises(SystemExit):
        cmd_unpin(args)


def test_cmd_pin_status_pinned(store_dir, capsys):
    _seed(store_dir, version=2)
    args = make_args(store_dir, project="myapp")
    cmd_pin_status(args)
    out = capsys.readouterr().out
    assert "pinned" in out.lower()
    assert "2" in out


def test_cmd_pin_status_not_pinned(store_dir, capsys):
    args = make_args(store_dir, project="myapp")
    cmd_pin_status(args)
    out = capsys.readouterr().out
    assert "not pinned" in out.lower()


def test_cmd_pin_list_empty(store_dir, capsys):
    args = make_args(store_dir)
    cmd_pin_list(args)
    out = capsys.readouterr().out
    assert "No pins" in out


def test_cmd_pin_list_shows_entries(store_dir, capsys):
    _seed(store_dir, project="app1", version=1)
    _seed(store_dir, project="app2", version=9)
    args = make_args(store_dir)
    cmd_pin_list(args)
    out = capsys.readouterr().out
    assert "app1" in out
    assert "app2" in out
