"""Tests for envault/export.py."""

import json
import pytest

from envault.export import export_shell, export_json, export_docker, export_env


SAMPLE_ENV = {
    "DATABASE_URL": "postgres://user:pass@localhost/db",
    "DEBUG": "true",
    'SECRET': 'has"quote',
}


def test_export_shell_contains_export():
    result = export_shell(SAMPLE_ENV)
    assert 'export DATABASE_URL="postgres://user:pass@localhost/db"' in result
    assert 'export DEBUG="true"' in result


def test_export_shell_escapes_double_quotes():
    result = export_shell({"KEY": 'say "hello"'})
    assert r'\"hello\"' in result


def test_export_shell_sorted_keys():
    result = export_shell({"ZEBRA": "1", "ALPHA": "2"})
    lines = result.splitlines()
    assert lines[0].startswith("export ALPHA")
    assert lines[1].startswith("export ZEBRA")


def test_export_json_valid_json():
    result = export_json(SAMPLE_ENV)
    parsed = json.loads(result)
    assert parsed["DEBUG"] == "true"
    assert parsed["DATABASE_URL"] == "postgres://user:pass@localhost/db"


def test_export_json_sorted_keys():
    result = export_json({"ZEBRA": "1", "ALPHA": "2"})
    parsed = json.loads(result)
    assert list(parsed.keys()) == ["ALPHA", "ZEBRA"]


def test_export_docker_no_quotes():
    result = export_docker({"PORT": "8080", "HOST": "localhost"})
    assert "PORT=8080" in result
    assert "HOST=localhost" in result
    assert '"' not in result


def test_export_docker_sorted_keys():
    result = export_docker({"ZEBRA": "1", "ALPHA": "2"})
    lines = result.splitlines()
    assert lines[0] == "ALPHA=2"
    assert lines[1] == "ZEBRA=1"


def test_export_env_dispatches_shell():
    result = export_env({"FOO": "bar"}, "shell")
    assert "export FOO" in result


def test_export_env_dispatches_json():
    result = export_env({"FOO": "bar"}, "json")
    assert json.loads(result) == {"FOO": "bar"}


def test_export_env_dispatches_docker():
    result = export_env({"FOO": "bar"}, "docker")
    assert result == "FOO=bar"


def test_export_env_invalid_format_raises():
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_env({"FOO": "bar"}, "xml")


def test_export_empty_env():
    assert export_shell({}) == ""
    assert export_json({}) == "{}"
    assert export_docker({}) == ""
