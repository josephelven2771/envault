"""Tests for envault.env_schema validation module."""

import pytest
from envault.env_schema import SchemaRule, ValidationError, validate_env


# ---------------------------------------------------------------------------
# SchemaRule serialisation
# ---------------------------------------------------------------------------

def test_schema_rule_roundtrip_dict():
    rule = SchemaRule(key="DATABASE_URL", required=True, value_type="str",
                      pattern=r"postgres://.+", description="Postgres DSN")
    assert SchemaRule.from_dict(rule.to_dict()) == rule


def test_schema_rule_defaults():
    rule = SchemaRule(key="FOO")
    assert rule.required is True
    assert rule.value_type == "str"
    assert rule.pattern is None
    assert rule.description == ""


# ---------------------------------------------------------------------------
# Required key checks
# ---------------------------------------------------------------------------

def test_missing_required_key_raises_error():
    rules = [SchemaRule(key="SECRET_KEY", required=True)]
    errors = validate_env({}, rules)
    assert len(errors) == 1
    assert errors[0].key == "SECRET_KEY"
    assert "missing" in errors[0].message


def test_missing_optional_key_no_error():
    rules = [SchemaRule(key="OPTIONAL_VAR", required=False)]
    errors = validate_env({}, rules)
    assert errors == []


def test_present_required_key_no_error():
    rules = [SchemaRule(key="API_KEY", required=True)]
    errors = validate_env({"API_KEY": "abc123"}, rules)
    assert errors == []


# ---------------------------------------------------------------------------
# Type checks
# ---------------------------------------------------------------------------

def test_valid_int_passes():
    rules = [SchemaRule(key="PORT", value_type="int")]
    assert validate_env({"PORT": "8080"}, rules) == []


def test_invalid_int_fails():
    rules = [SchemaRule(key="PORT", value_type="int")]
    errors = validate_env({"PORT": "not_a_number"}, rules)
    assert any("int" in e.message for e in errors)


def test_valid_float_passes():
    rules = [SchemaRule(key="RATIO", value_type="float")]
    assert validate_env({"RATIO": "0.75"}, rules) == []


def test_invalid_float_fails():
    rules = [SchemaRule(key="RATIO", value_type="float")]
    errors = validate_env({"RATIO": "abc"}, rules)
    assert any("float" in e.message for e in errors)


def test_valid_bool_passes():
    for val in ("true", "false", "1", "0", "yes", "no", "True", "FALSE"):
        rules = [SchemaRule(key="FLAG", value_type="bool")]
        assert validate_env({"FLAG": val}, rules) == [], f"Expected valid bool for '{val}'"


def test_invalid_bool_fails():
    rules = [SchemaRule(key="FLAG", value_type="bool")]
    errors = validate_env({"FLAG": "maybe"}, rules)
    assert any("bool" in e.message for e in errors)


# ---------------------------------------------------------------------------
# Pattern checks
# ---------------------------------------------------------------------------

def test_pattern_match_passes():
    rules = [SchemaRule(key="DB_URL", pattern=r"postgres://.+")]
    assert validate_env({"DB_URL": "postgres://localhost/mydb"}, rules) == []


def test_pattern_mismatch_fails():
    rules = [SchemaRule(key="DB_URL", pattern=r"postgres://.+")]
    errors = validate_env({"DB_URL": "mysql://localhost/mydb"}, rules)
    assert any("pattern" in e.message for e in errors)


# ---------------------------------------------------------------------------
# Unknown type in schema
# ---------------------------------------------------------------------------

def test_unknown_type_in_schema_reports_error():
    rules = [SchemaRule(key="X", value_type="uuid")]
    errors = validate_env({"X": "some-value"}, rules)
    assert any("unknown type" in e.message for e in errors)


# ---------------------------------------------------------------------------
# ValidationError __str__
# ---------------------------------------------------------------------------

def test_validation_error_str():
    e = ValidationError(key="FOO", message="required key is missing")
    assert str(e) == "FOO: required key is missing"
