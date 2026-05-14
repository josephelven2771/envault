"""Tests for envault.env_redact."""
import pytest
from envault.env_redact import (
    RedactConfig,
    redact_env,
    redact_value,
    format_redacted,
    REDACT_PLACEHOLDER,
    DEFAULT_REDACT_PATTERNS,
)


# ---------------------------------------------------------------------------
# RedactConfig
# ---------------------------------------------------------------------------

def test_redact_config_defaults():
    cfg = RedactConfig()
    assert cfg.patterns == DEFAULT_REDACT_PATTERNS
    assert cfg.show_length is False


def test_redact_config_roundtrip():
    cfg = RedactConfig(patterns=["secret", "token"], show_length=True)
    restored = RedactConfig.from_dict(cfg.to_dict())
    assert restored.patterns == ["secret", "token"]
    assert restored.show_length is True


def test_redact_config_from_dict_defaults():
    cfg = RedactConfig.from_dict({})
    assert cfg.patterns == DEFAULT_REDACT_PATTERNS
    assert cfg.show_length is False


# ---------------------------------------------------------------------------
# redact_env
# ---------------------------------------------------------------------------

def test_safe_keys_are_not_redacted():
    env = {"APP_NAME": "myapp", "PORT": "8080", "DEBUG": "true"}
    result = redact_env(env)
    assert result == env


def test_password_key_is_redacted():
    env = {"DB_PASSWORD": "super_secret_123"}
    result = redact_env(env)
    assert result["DB_PASSWORD"] == REDACT_PLACEHOLDER


def test_token_key_is_redacted():
    env = {"GITHUB_TOKEN": "ghp_abc123"}
    result = redact_env(env)
    assert result["GITHUB_TOKEN"] == REDACT_PLACEHOLDER


def test_api_key_is_redacted():
    env = {"STRIPE_API_KEY": "sk_live_xyz"}
    result = redact_env(env)
    assert result["STRIPE_API_KEY"] == REDACT_PLACEHOLDER


def test_show_length_includes_value_length():
    cfg = RedactConfig(show_length=True)
    env = {"DB_PASSWORD": "abc123"}
    result = redact_env(env, cfg)
    assert "6" in result["DB_PASSWORD"]
    assert "REDACTED" in result["DB_PASSWORD"]


def test_original_env_not_mutated():
    env = {"DB_PASSWORD": "secret"}
    original = dict(env)
    redact_env(env)
    assert env == original


def test_mixed_env_only_sensitive_redacted():
    env = {"APP_NAME": "envault", "SECRET_KEY": "abc", "PORT": "3000"}
    result = redact_env(env)
    assert result["APP_NAME"] == "envault"
    assert result["PORT"] == "3000"
    assert result["SECRET_KEY"] == REDACT_PLACEHOLDER


def test_custom_patterns():
    cfg = RedactConfig(patterns=["internal"])
    env = {"INTERNAL_URL": "http://internal", "DB_PASSWORD": "secret"}
    result = redact_env(env, cfg)
    # Only INTERNAL_URL matches the custom pattern
    assert result["INTERNAL_URL"] == REDACT_PLACEHOLDER
    assert result["DB_PASSWORD"] == "secret"  # not in custom patterns


# ---------------------------------------------------------------------------
# redact_value
# ---------------------------------------------------------------------------

def test_redact_value_sensitive():
    assert redact_value("API_KEY", "my_key") == REDACT_PLACEHOLDER


def test_redact_value_safe():
    assert redact_value("HOST", "localhost") == "localhost"


# ---------------------------------------------------------------------------
# format_redacted
# ---------------------------------------------------------------------------

def test_format_redacted_sorted_output():
    env = {"Z_KEY": "z", "A_KEY": "a"}
    output = format_redacted(env)
    lines = output.splitlines()
    assert lines[0].startswith("A_KEY")
    assert lines[1].startswith("Z_KEY")


def test_format_redacted_masks_secrets():
    env = {"DB_PASSWORD": "hunter2", "APP": "myapp"}
    output = format_redacted(env)
    assert "hunter2" not in output
    assert REDACT_PLACEHOLDER in output
    assert "APP=myapp" in output
