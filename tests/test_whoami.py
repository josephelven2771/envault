"""Tests for the whoami user-identity helper."""

import os
import pytest
from envault.whoami import get_current_user, _CONFIG_KEY


def test_override_takes_priority(monkeypatch):
    monkeypatch.setenv(_CONFIG_KEY, "env-user")
    result = get_current_user(override="explicit-user")
    assert result == "explicit-user"


def test_env_var_used_when_no_override(monkeypatch):
    monkeypatch.setenv(_CONFIG_KEY, "team-bot")
    result = get_current_user()
    assert result == "team-bot"


def test_fallback_contains_at_symbol(monkeypatch):
    monkeypatch.delenv(_CONFIG_KEY, raising=False)
    result = get_current_user()
    assert "@" in result


def test_no_override_no_env_returns_string(monkeypatch):
    monkeypatch.delenv(_CONFIG_KEY, raising=False)
    result = get_current_user()
    assert isinstance(result, str)
    assert len(result) > 0
