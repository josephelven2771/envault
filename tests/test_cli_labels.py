"""Tests for envault.cli_labels CLI commands."""
import argparse
import pytest
from envault.cli_labels import cmd_label_set, cmd_label_get, cmd_label_delete, cmd_label_list, cmd_label_find
from envault.env_labels import LabelStore


def make_args(**kwargs):
    defaults = dict(store_dir=None, project="proj", key="API_KEY", labels="", note="", label="")
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def store_dir(tmp_path):
    return str(tmp_path)


def test_cmd_label_set_creates_entry(store_dir, capsys):
    args = make_args(store_dir=store_dir, key="DB_URL", labels="sensitive,required")
    cmd_label_set(args)
    record = LabelStore(store_dir).get_labels("proj", "DB_URL")
    assert record is not None
    assert "sensitive" in record.labels
    captured = capsys.readouterr()
    assert "DB_URL" in captured.out


def test_cmd_label_set_with_note(store_dir):
    args = make_args(store_dir=store_dir, key="TOKEN", labels="secret", note="rotate monthly")
    cmd_label_set(args)
    record = LabelStore(store_dir).get_labels("proj", "TOKEN")
    assert record.note == "rotate monthly"


def test_cmd_label_get_existing(store_dir, capsys):
    LabelStore(store_dir).set_labels("proj", "API_KEY", ["critical"])
    args = make_args(store_dir=store_dir, key="API_KEY")
    cmd_label_get(args)
    out = capsys.readouterr().out
    assert "critical" in out


def test_cmd_label_get_missing(store_dir, capsys):
    args = make_args(store_dir=store_dir, key="GHOST")
    cmd_label_get(args)
    out = capsys.readouterr().out
    assert "No labels" in out


def test_cmd_label_delete_existing(store_dir, capsys):
    LabelStore(store_dir).set_labels("proj", "API_KEY", ["x"])
    args = make_args(store_dir=store_dir, key="API_KEY")
    cmd_label_delete(args)
    assert LabelStore(store_dir).get_labels("proj", "API_KEY") is None
    assert "removed" in capsys.readouterr().out


def test_cmd_label_delete_missing(store_dir, capsys):
    args = make_args(store_dir=store_dir, key="MISSING")
    cmd_label_delete(args)
    assert "No labels" in capsys.readouterr().out


def test_cmd_label_list_shows_keys(store_dir, capsys):
    s = LabelStore(store_dir)
    s.set_labels("proj", "A", ["x"])
    s.set_labels("proj", "B", ["y"])
    args = make_args(store_dir=store_dir)
    cmd_label_list(args)
    out = capsys.readouterr().out
    assert "A" in out and "B" in out


def test_cmd_label_list_empty(store_dir, capsys):
    args = make_args(store_dir=store_dir)
    cmd_label_list(args)
    assert "No labels" in capsys.readouterr().out


def test_cmd_label_find_match(store_dir, capsys):
    LabelStore(store_dir).set_labels("proj", "SECRET", ["sensitive"])
    args = make_args(store_dir=store_dir, label="sensitive")
    cmd_label_find(args)
    assert "SECRET" in capsys.readouterr().out


def test_cmd_label_find_no_match(store_dir, capsys):
    args = make_args(store_dir=store_dir, label="nonexistent")
    cmd_label_find(args)
    assert "No keys" in capsys.readouterr().out
