"""Tests for envault.alerts."""
import pytest
from envault.alerts import (
    AlertRule,
    AlertMatch,
    check_alerts,
    format_alerts,
    _matches_any_rule,
    ALERT_RULES,
)


def make_diff_entry(key: str, status: str) -> dict:
    return {"key": key, "status": status}


def test_matches_rule_case_insensitive():
    rules = [AlertRule("PASSWORD")]
    assert _matches_any_rule("DB_PASSWORD", rules) is not None
    assert _matches_any_rule("db_password", rules) is not None


def test_no_match_for_safe_key():
    rules = [AlertRule("PASSWORD")]
    assert _matches_any_rule("APP_NAME", rules) is None


def test_check_alerts_detects_added_secret():
    diff = [make_diff_entry("API_KEY", "added")]
    matches = check_alerts(diff)
    assert len(matches) == 1
    assert matches[0].key == "API_KEY"
    assert matches[0].action == "added"
    assert matches[0].rule_keyword == "API_KEY"


def test_check_alerts_detects_changed_token():
    diff = [make_diff_entry("AUTH_TOKEN", "changed")]
    matches = check_alerts(diff)
    assert any(m.key == "AUTH_TOKEN" for m in matches)


def test_check_alerts_ignores_unchanged():
    diff = [make_diff_entry("DB_PASSWORD", "unchanged")]
    matches = check_alerts(diff)
    assert matches == []


def test_check_alerts_ignores_safe_keys():
    diff = [
        make_diff_entry("APP_NAME", "added"),
        make_diff_entry("PORT", "changed"),
    ]
    matches = check_alerts(diff)
    assert matches == []


def test_check_alerts_custom_rules():
    rules = [AlertRule("CUSTOM", "custom rule")]
    diff = [make_diff_entry("MY_CUSTOM_VAR", "removed")]
    matches = check_alerts(diff, rules=rules)
    assert len(matches) == 1
    assert matches[0].rule_keyword == "CUSTOM"


def test_format_alerts_no_matches():
    result = format_alerts([])
    assert "No sensitive" in result


def test_format_alerts_with_matches():
    matches = [AlertMatch(key="DB_PASSWORD", rule_keyword="PASSWORD", action="changed")]
    result = format_alerts(matches)
    assert "ALERT" in result
    assert "DB_PASSWORD" in result
    assert "CHANGED" in result


def test_alert_rule_roundtrip():
    rule = AlertRule(keyword="SECRET", description="secret values")
    d = rule.to_dict()
    restored = AlertRule.from_dict(d)
    assert restored.keyword == rule.keyword
    assert restored.description == rule.description


def test_default_rules_cover_common_keywords():
    for kw in ["PASSWORD", "TOKEN", "SECRET"]:
        assert kw in ALERT_RULES
