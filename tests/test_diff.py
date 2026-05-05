"""Tests for envault.diff module."""

import pytest
from envault.diff import diff_envs, format_diff, has_changes, _mask_value


OLD = {"DB_HOST": "localhost", "DB_PASS": "secret", "PORT": "5432"}
NEW = {"DB_HOST": "prod.db", "DB_PASS": "secret", "API_KEY": "abc123"}


def test_added_key_detected():
    diff = diff_envs({}, {"FOO": "bar"})
    assert any(s == "added" and k == "FOO" for s, k, _ in diff)


def test_removed_key_detected():
    diff = diff_envs({"FOO": "bar"}, {})
    assert any(s == "removed" and k == "FOO" for s, k, _ in diff)


def test_changed_key_detected():
    diff = diff_envs({"FOO": "old"}, {"FOO": "new"})
    assert any(s == "changed" and k == "FOO" for s, k, _ in diff)


def test_unchanged_key_detected():
    diff = diff_envs({"FOO": "same"}, {"FOO": "same"})
    assert any(s == "unchanged" and k == "FOO" for s, k, _ in diff)


def test_full_diff_keys():
    diff = diff_envs(OLD, NEW)
    statuses = {k: s for s, k, _ in diff}
    assert statuses["DB_HOST"] == "changed"
    assert statuses["DB_PASS"] == "unchanged"
    assert statuses["PORT"] == "removed"
    assert statuses["API_KEY"] == "added"


def test_has_changes_true():
    diff = diff_envs(OLD, NEW)
    assert has_changes(diff) is True


def test_has_changes_false():
    diff = diff_envs({"A": "1"}, {"A": "1"})
    assert has_changes(diff) is False


def test_format_diff_excludes_unchanged_by_default():
    diff = diff_envs({"A": "1", "B": "2"}, {"A": "1", "B": "3"})
    output = format_diff(diff)
    assert "~ B=" in output
    assert "A" not in output


def test_format_diff_includes_unchanged_when_requested():
    diff = diff_envs({"A": "1"}, {"A": "1"})
    output = format_diff(diff, show_unchanged=True)
    assert "  A=" in output or " A=" in output


def test_format_diff_symbols():
    diff = diff_envs({"OLD": "x"}, {"NEW": "y"})
    output = format_diff(diff)
    assert output.startswith("-") or "+" in output


def test_mask_value_short():
    assert _mask_value("abc") == "***"


def test_mask_value_long():
    masked = _mask_value("mysecretpassword")
    assert masked.startswith("my")
    assert "*" in masked
    assert "secret" not in masked
