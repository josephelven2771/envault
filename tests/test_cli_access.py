"""Tests for CLI access subcommands."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path

from envault.access import AccessControl, PERMISSION_READ, PERMISSION_WRITE, PERMISSION_ADMIN
from envault.cli_access import cmd_grant, cmd_revoke, cmd_list_access, cmd_check


def make_args(store: str, project: str, **kwargs) -> argparse.Namespace:
    ns = argparse.Namespace(store=store, project=project, **kwargs)
    return ns


@pytest.fixture
def store_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def test_cmd_grant_creates_entry(store_dir: str, capsys) -> None:
    args = make_args(store_dir, "myproject", user="alice@x.com", permission=PERMISSION_WRITE)
    cmd_grant(args)
    out = capsys.readouterr().out
    assert "Granted" in out
    assert "alice@x.com" in out


def test_cmd_grant_invalid_permission(store_dir: str, capsys) -> None:
    args = make_args(store_dir, "myproject", user="alice@x.com", permission="god")
    cmd_grant(args)
    out = capsys.readouterr().out
    assert "Error" in out


def test_cmd_revoke_existing(store_dir: str, capsys) -> None:
    path = Path(store_dir) / "myproject" / "access.json"
    ac = AccessControl(path)
    ac.grant("bob@x.com", PERMISSION_READ)

    args = make_args(store_dir, "myproject", user="bob@x.com")
    cmd_revoke(args)
    out = capsys.readouterr().out
    assert "Revoked" in out


def test_cmd_revoke_nonexistent(store_dir: str, capsys) -> None:
    args = make_args(store_dir, "myproject", user="ghost@x.com")
    cmd_revoke(args)
    out = capsys.readouterr().out
    assert "no access entry" in out


def test_cmd_list_access_empty(store_dir: str, capsys) -> None:
    args = make_args(store_dir, "emptyproject")
    cmd_list_access(args)
    out = capsys.readouterr().out
    assert "No access entries" in out


def test_cmd_list_access_with_users(store_dir: str, capsys) -> None:
    path = Path(store_dir) / "proj" / "access.json"
    ac = AccessControl(path)
    ac.grant("alice@x.com", PERMISSION_ADMIN)

    args = make_args(store_dir, "proj")
    cmd_list_access(args)
    out = capsys.readouterr().out
    assert "alice@x.com" in out
    assert PERMISSION_ADMIN in out


def test_cmd_check_allowed(store_dir: str, capsys) -> None:
    path = Path(store_dir) / "proj" / "access.json"
    ac = AccessControl(path)
    ac.grant("alice@x.com", PERMISSION_WRITE)

    args = make_args(store_dir, "proj", user="alice@x.com", permission=PERMISSION_READ)
    cmd_check(args)
    out = capsys.readouterr().out
    assert "ALLOWED" in out


def test_cmd_check_denied(store_dir: str, capsys) -> None:
    path = Path(store_dir) / "proj" / "access.json"
    ac = AccessControl(path)
    ac.grant("alice@x.com", PERMISSION_READ)

    args = make_args(store_dir, "proj", user="alice@x.com", permission=PERMISSION_ADMIN)
    cmd_check(args)
    out = capsys.readouterr().out
    assert "DENIED" in out
