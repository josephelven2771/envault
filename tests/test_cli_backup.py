"""Tests for envault.cli_backup CLI command handlers."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.cli_backup import cmd_backup, cmd_restore, cmd_backup_info
from envault.store import LocalStore, StoreEntry


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "store_dir": None,
        "output": None,
        "input": None,
        "notes": "",
        "overwrite": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _seed(store: LocalStore, project: str) -> None:
    entry = StoreEntry(
        project=project,
        version=1,
        ciphertext="ct",
        pushed_by="u@x.com",
        pushed_at="2024-01-01T00:00:00+00:00",
    )
    store.save(project, entry)


def _create_backup(store: LocalStore, path: Path, notes: str = "") -> Path:
    """Helper to create a backup archive for use in tests."""
    from envault.env_backup import create_backup
    create_backup(store, path, notes=notes)
    return path


@pytest.fixture()
def store_dir(tmp_path: Path) -> str:
    d = tmp_path / "store"
    d.mkdir()
    return str(d)


def test_cmd_backup_creates_file(store_dir, tmp_path, capsys):
    store = LocalStore(store_dir)
    _seed(store, "myproject")
    out = str(tmp_path / "out.zip")
    args = make_args(store_dir=store_dir, output=out)
    cmd_backup(args)
    assert Path(out).exists()
    captured = capsys.readouterr()
    assert "Backup created" in captured.out
    assert "myproject" in captured.out


def test_cmd_backup_notes_shown(store_dir, tmp_path, capsys):
    store = LocalStore(store_dir)
    _seed(store, "p")
    out = str(tmp_path / "out.zip")
    args = make_args(store_dir=store_dir, output=out, notes="sprint 42")
    cmd_backup(args)
    captured = capsys.readouterr()
    assert "sprint 42" in captured.out


def test_cmd_restore_prints_summary(store_dir, tmp_path, capsys):
    store = LocalStore(store_dir)
    _seed(store, "alpha")
    backup = _create_backup(store, tmp_path / "bk.zip")

    new_dir = str(tmp_path / "new_store")
    args = make_args(store_dir=new_dir, input=str(backup))
    cmd_restore(args)
    captured = capsys.readouterr()
    assert "Restore complete" in captured.out


def test_cmd_restore_missing_file_exits(store_dir, tmp_path):
    args = make_args(store_dir=store_dir, input=str(tmp_path / "nope.zip"))
    with pytest.raises(SystemExit):
        cmd_restore(args)


def test_cmd_backup_info_prints_metadata(store_dir, tmp_path, capsys):
    store = LocalStore(store_dir)
    _seed(store, "beta")
    backup = _create_backup(store, tmp_path / "info.zip", notes="info test")

    args = make_args(input=str(backup))
    cmd_backup_info(args)
    captured = capsys.readouterr()
    assert "beta" in captured.out
    assert "info test" in captured.out


def test_cmd_backup_info_bad_file_exits(tmp_path):
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"garbage")
    args = make_args(input=str(bad))
    with pytest.raises(SystemExit):
        cmd_backup_info(args)
