"""Tests for envault.env_format."""
import pytest
from envault.env_format import format_env, FormatIssue, FormatResult


# ---------------------------------------------------------------------------
# FormatIssue helpers
# ---------------------------------------------------------------------------

def test_format_issue_to_dict():
    issue = FormatIssue(key="FOO", message="some problem", auto_fixed=True)
    d = issue.to_dict()
    assert d["key"] == "FOO"
    assert d["message"] == "some problem"
    assert d["auto_fixed"] is True


def test_format_issue_str_fixed():
    issue = FormatIssue(key="BAR", message="trailing space", auto_fixed=True)
    assert "[fixed]" in str(issue)
    assert "BAR" in str(issue)


def test_format_issue_str_warn():
    issue = FormatIssue(key="BAZ", message="something", auto_fixed=False)
    assert "[warn]" in str(issue)


# ---------------------------------------------------------------------------
# sort_keys
# ---------------------------------------------------------------------------

def test_sort_keys_default():
    env = {"ZEBRA": "1", "ALPHA": "2", "MANGO": "3"}
    result = format_env(env)
    assert list(result.formatted.keys()) == sorted(env.keys())


def test_sort_keys_disabled():
    env = {"ZEBRA": "1", "ALPHA": "2"}
    result = format_env(env, sort_keys=False)
    assert list(result.formatted.keys()) == ["ZEBRA", "ALPHA"]


# ---------------------------------------------------------------------------
# strip_values
# ---------------------------------------------------------------------------

def test_strip_values_removes_whitespace():
    env = {"KEY": "  hello  "}
    result = format_env(env)
    assert result.formatted["KEY"] == "hello"
    assert any(i.key == "KEY" and i.auto_fixed for i in result.issues)


def test_strip_values_disabled_preserves_whitespace():
    env = {"KEY": "  hello  "}
    result = format_env(env, strip_values=False)
    assert result.formatted["KEY"] == "  hello  "
    assert not result.issues


# ---------------------------------------------------------------------------
# uppercase_keys
# ---------------------------------------------------------------------------

def test_uppercase_keys_normalises():
    env = {"my_key": "val"}
    result = format_env(env, uppercase_keys=True)
    assert "MY_KEY" in result.formatted
    assert "my_key" not in result.formatted
    assert any(i.auto_fixed for i in result.issues)


def test_uppercase_keys_disabled_preserves_case():
    env = {"my_key": "val"}
    result = format_env(env, uppercase_keys=False)
    assert "my_key" in result.formatted


# ---------------------------------------------------------------------------
# remove_empty
# ---------------------------------------------------------------------------

def test_remove_empty_drops_blank_values():
    env = {"KEEP": "yes", "DROP": ""}
    result = format_env(env, remove_empty=True)
    assert "DROP" not in result.formatted
    assert "KEEP" in result.formatted


def test_remove_empty_disabled_keeps_blank_values():
    env = {"KEEP": "yes", "EMPTY": ""}
    result = format_env(env, remove_empty=False)
    assert "EMPTY" in result.formatted


# ---------------------------------------------------------------------------
# changed / summary
# ---------------------------------------------------------------------------

def test_changed_flag_true_when_modified():
    env = {"B": "1", "A": "2"}
    result = format_env(env, sort_keys=True)
    assert result.changed is True


def test_changed_flag_false_when_identical():
    env = {"A": "1", "B": "2"}
    result = format_env(env, sort_keys=True)
    assert result.changed is False


def test_summary_no_issues():
    env = {"A": "1"}
    result = format_env(env)
    assert "No formatting issues" in result.summary()


def test_summary_with_issues():
    env = {"key": "  val  "}
    result = format_env(env, uppercase_keys=True)
    summary = result.summary()
    assert "KEY" in summary or "key" in summary
