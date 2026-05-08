"""Tests for envault.secrets_scan module."""

import pytest
from envault.secrets_scan import scan_env, format_scan_results, ScanFinding, _mask


def test_mask_short_value():
    assert _mask("abc") == "***"


def test_mask_long_value():
    result = _mask("supersecret", show=4)
    assert result.startswith("supe")
    assert "*" in result


def test_no_findings_for_clean_env():
    env = {
        "APP_NAME": "myapp",
        "PORT": "8080",
        "DEBUG": "false",
    }
    findings = scan_env(env)
    assert findings == []


def test_placeholder_password_raises_error():
    env = {"DB_PASSWORD": "changeme"}
    findings = scan_env(env)
    assert any(f.severity == "error" and "placeholder" in f.message.lower() for f in findings)


def test_placeholder_token_angle_brackets():
    env = {"API_TOKEN": "<your_token_here>"}
    findings = scan_env(env)
    assert any(f.severity == "error" for f in findings)


def test_placeholder_env_variable_syntax():
    env = {"SECRET_KEY": "${SECRET_KEY}"}
    findings = scan_env(env)
    assert any(f.severity == "error" for f in findings)


def test_empty_sensitive_key_raises_error():
    env = {"AUTH_TOKEN": ""}
    findings = scan_env(env)
    assert any(f.severity == "error" and "empty" in f.message.lower() for f in findings)


def test_short_sensitive_value_raises_warning():
    env = {"API_KEY": "abc"}
    findings = scan_env(env)
    assert any(f.severity == "warning" and "short" in f.message.lower() for f in findings)


def test_non_sensitive_key_with_placeholder_ignored():
    env = {"GREETING": "changeme"}
    findings = scan_env(env)
    assert findings == []


def test_multiple_issues_detected():
    env = {
        "DB_PASSWORD": "changeme",
        "API_KEY": "",
        "APP_PORT": "3000",
    }
    findings = scan_env(env)
    assert len(findings) >= 2


def test_finding_to_dict():
    f = ScanFinding(key="SECRET", value_preview="****", severity="error", message="test msg")
    d = f.to_dict()
    assert d["key"] == "SECRET"
    assert d["severity"] == "error"
    assert d["message"] == "test msg"


def test_format_scan_results_no_findings():
    assert format_scan_results([]) == "No issues found."


def test_format_scan_results_with_findings():
    findings = [ScanFinding("DB_PASSWORD", "****", "error", "placeholder value")]
    output = format_scan_results(findings)
    assert "[ERROR]" in output
    assert "DB_PASSWORD" in output
