"""Tests for envault.env_lint."""

from __future__ import annotations

import pytest

from envault.env_lint import LintIssue, format_lint_results, lint_env


# ---------------------------------------------------------------------------
# LintIssue helpers
# ---------------------------------------------------------------------------

def test_lint_issue_to_dict():
    issue = LintIssue("error", "MY_KEY", "something bad")
    d = issue.to_dict()
    assert d == {"level": "error", "key": "MY_KEY", "message": "something bad"}


def test_lint_issue_str():
    issue = LintIssue("warning", "FOO", "watch out")
    assert str(issue) == "[WARNING] FOO: watch out"


# ---------------------------------------------------------------------------
# lint_env checks
# ---------------------------------------------------------------------------

def test_clean_env_no_issues():
    env = {"DATABASE_URL": "postgres://localhost/db", "PORT": "5432"}
    assert lint_env(env) == []


def test_empty_value_warning():
    issues = lint_env({"SECRET_KEY": ""})
    assert any(i.key == "SECRET_KEY" and i.level == "warning" for i in issues)


def test_lowercase_key_warning():
    issues = lint_env({"my_key": "value"})
    assert any(i.key == "my_key" and i.level == "warning" for i in issues)


def test_mixed_case_key_warning():
    issues = lint_env({"MyKey": "value"})
    assert any(i.level == "warning" and "UPPER_SNAKE_CASE" in i.message for i in issues)


def test_leading_whitespace_info():
    issues = lint_env({"API_KEY": "  secret"})
    assert any(i.key == "API_KEY" and i.level == "info" for i in issues)


def test_trailing_whitespace_info():
    issues = lint_env({"API_KEY": "secret  "})
    assert any(i.level == "info" for i in issues)


def test_placeholder_angle_brackets_warning():
    issues = lint_env({"TOKEN": "<your-token-here>"})
    assert any(i.key == "TOKEN" and i.level == "warning" for i in issues)


def test_placeholder_changeme_warning():
    issues = lint_env({"DB_PASS": "CHANGEME"})
    assert any(i.level == "warning" and "placeholder" in i.message.lower() for i in issues)


def test_placeholder_shell_var_warning():
    issues = lint_env({"SECRET": "${SECRET_VALUE}"})
    assert any(i.level == "warning" for i in issues)


def test_multiple_issues_same_key():
    # lowercase key AND empty value → two issues
    issues = lint_env({"bad_key": ""})
    keys_with_issues = [i.key for i in issues]
    assert keys_with_issues.count("bad_key") >= 2


# ---------------------------------------------------------------------------
# format_lint_results
# ---------------------------------------------------------------------------

def test_format_no_issues():
    assert format_lint_results([]) == "No issues found."


def test_format_with_issues():
    issues = [LintIssue("error", "KEY", "bad"), LintIssue("warning", "OTHER", "meh")]
    result = format_lint_results(issues)
    assert "[ERROR]" in result
    assert "[WARNING]" in result
