"""Tests for envault.access access control module."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.access import (
    AccessControl,
    AccessEntry,
    PERMISSION_READ,
    PERMISSION_WRITE,
    PERMISSION_ADMIN,
)


@pytest.fixture
def ac(tmp_path: Path) -> AccessControl:
    return AccessControl(tmp_path / "access.json")


def test_grant_and_get_permission(ac: AccessControl) -> None:
    ac.grant("alice@example.com", PERMISSION_WRITE)
    assert ac.get_permission("alice@example.com") == PERMISSION_WRITE


def test_unknown_permission_raises(ac: AccessControl) -> None:
    with pytest.raises(ValueError, match="Unknown permission"):
        ac.grant("bob@example.com", "superuser")


def test_revoke_existing_user(ac: AccessControl) -> None:
    ac.grant("alice@example.com", PERMISSION_READ)
    result = ac.revoke("alice@example.com")
    assert result is True
    assert ac.get_permission("alice@example.com") is None


def test_revoke_nonexistent_user_returns_false(ac: AccessControl) -> None:
    result = ac.revoke("nobody@example.com")
    assert result is False


def test_can_read_with_read_permission(ac: AccessControl) -> None:
    ac.grant("alice@example.com", PERMISSION_READ)
    assert ac.can("alice@example.com", PERMISSION_READ) is True


def test_cannot_write_with_read_permission(ac: AccessControl) -> None:
    ac.grant("alice@example.com", PERMISSION_READ)
    assert ac.can("alice@example.com", PERMISSION_WRITE) is False


def test_admin_can_do_everything(ac: AccessControl) -> None:
    ac.grant("admin@example.com", PERMISSION_ADMIN)
    assert ac.can("admin@example.com", PERMISSION_READ) is True
    assert ac.can("admin@example.com", PERMISSION_WRITE) is True
    assert ac.can("admin@example.com", PERMISSION_ADMIN) is True


def test_unknown_user_cannot(ac: AccessControl) -> None:
    assert ac.can("ghost@example.com", PERMISSION_READ) is False


def test_list_users(ac: AccessControl) -> None:
    ac.grant("alice@example.com", PERMISSION_READ)
    ac.grant("bob@example.com", PERMISSION_ADMIN)
    users = ac.list_users()
    assert len(users) == 2
    names = {e.user for e in users}
    assert "alice@example.com" in names
    assert "bob@example.com" in names


def test_persistence_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "access.json"
    ac1 = AccessControl(path)
    ac1.grant("alice@example.com", PERMISSION_WRITE)

    ac2 = AccessControl(path)
    assert ac2.get_permission("alice@example.com") == PERMISSION_WRITE


def test_grant_overwrites_existing_permission(ac: AccessControl) -> None:
    ac.grant("alice@example.com", PERMISSION_READ)
    ac.grant("alice@example.com", PERMISSION_ADMIN)
    assert ac.get_permission("alice@example.com") == PERMISSION_ADMIN


def test_access_entry_to_and_from_dict() -> None:
    entry = AccessEntry(user="test@example.com", permission=PERMISSION_WRITE)
    d = entry.to_dict()
    restored = AccessEntry.from_dict(d)
    assert restored.user == entry.user
    assert restored.permission == entry.permission
