"""Tests for envault.import_env module."""

import json
import os
import textwrap

import pytest

from envault.import_env import import_from_file, import_from_json, import_from_shell, merge_envs


# ---------------------------------------------------------------------------
# import_from_file
# ---------------------------------------------------------------------------

def test_import_from_file_parses_correctly(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    result = import_from_file(str(env_file))
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_import_from_file_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        import_from_file(str(tmp_path / "nonexistent.env"))


# ---------------------------------------------------------------------------
# import_from_json
# ---------------------------------------------------------------------------

def test_import_from_json_flat_object(tmp_path):
    data = {"API_KEY": "abc123", "DEBUG": "true"}
    json_file = tmp_path / "vars.json"
    json_file.write_text(json.dumps(data))
    result = import_from_json(str(json_file))
    assert result == {"API_KEY": "abc123", "DEBUG": "true"}


def test_import_from_json_non_dict_raises(tmp_path):
    json_file = tmp_path / "bad.json"
    json_file.write_text(json.dumps(["a", "b"]))
    with pytest.raises(ValueError, match="top-level object"):
        import_from_json(str(json_file))


def test_import_from_json_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        import_from_json(str(tmp_path / "missing.json"))


# ---------------------------------------------------------------------------
# import_from_shell
# ---------------------------------------------------------------------------

def test_import_from_shell_specific_keys(monkeypatch):
    monkeypatch.setenv("MY_VAR", "hello")
    monkeypatch.setenv("OTHER", "world")
    result = import_from_shell(keys=["MY_VAR"])
    assert result == {"MY_VAR": "hello"}
    assert "OTHER" not in result


def test_import_from_shell_missing_keys_ignored(monkeypatch):
    result = import_from_shell(keys=["DEFINITELY_NOT_SET_XYZ"])
    assert result == {}


def test_import_from_shell_no_filter_returns_all(monkeypatch):
    monkeypatch.setenv("ENVAULT_TEST_VAR", "1")
    result = import_from_shell()
    assert "ENVAULT_TEST_VAR" in result


# ---------------------------------------------------------------------------
# merge_envs
# ---------------------------------------------------------------------------

def test_merge_override_strategy():
    base = {"A": "1", "B": "2"}
    override = {"B": "99", "C": "3"}
    result = merge_envs(base, override, conflict="override")
    assert result == {"A": "1", "B": "99", "C": "3"}


def test_merge_keep_strategy():
    base = {"A": "1", "B": "2"}
    override = {"B": "99", "C": "3"}
    result = merge_envs(base, override, conflict="keep")
    assert result == {"A": "1", "B": "2", "C": "3"}


def test_merge_error_strategy_raises_on_conflict():
    base = {"A": "1"}
    override = {"A": "2"}
    with pytest.raises(ValueError, match="Conflicting key"):
        merge_envs(base, override, conflict="error")


def test_merge_error_strategy_no_conflict():
    base = {"A": "1"}
    override = {"B": "2"}
    result = merge_envs(base, override, conflict="error")
    assert result == {"A": "1", "B": "2"}


def test_merge_invalid_strategy_raises():
    with pytest.raises(ValueError, match="Unknown conflict strategy"):
        merge_envs({}, {}, conflict="invalid")
