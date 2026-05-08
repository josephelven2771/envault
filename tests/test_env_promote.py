"""Tests for envault.env_promote."""

from __future__ import annotations

import pytest

from envault.store import LocalStore
from envault.sync import push, pull
from envault.env_promote import promote, PromoteResult


@pytest.fixture()
def tmp_store(tmp_path):
    return LocalStore(str(tmp_path / "store"))


def _seed(store, project, env, password="pass"):
    push(store, project, env, password)


# ---------------------------------------------------------------------------
# PromoteResult.summary
# ---------------------------------------------------------------------------

def test_promote_result_summary_contains_project_names():
    r = PromoteResult(source_project="staging", target_project="prod")
    summary = r.summary()
    assert "staging" in summary
    assert "prod" in summary


# ---------------------------------------------------------------------------
# promote() happy-path
# ---------------------------------------------------------------------------

def test_promote_all_keys_to_empty_target(tmp_store):
    _seed(tmp_store, "staging", {"DB_URL": "postgres://staging", "SECRET": "abc"})
    result = promote(tmp_store, "staging", "prod", "pass", "pass")
    assert set(result.promoted_keys) == {"DB_URL", "SECRET"}
    assert result.skipped_keys == []
    assert result.overwritten_keys == []

    target_env = pull(tmp_store, "prod", "pass")
    assert target_env["DB_URL"] == "postgres://staging"
    assert target_env["SECRET"] == "abc"


def test_promote_specific_keys_only(tmp_store):
    _seed(tmp_store, "staging", {"A": "1", "B": "2", "C": "3"})
    result = promote(tmp_store, "staging", "prod", "pass", "pass", keys=["A", "C"])
    assert set(result.promoted_keys) == {"A", "C"}
    target_env = pull(tmp_store, "prod", "pass")
    assert "A" in target_env
    assert "C" in target_env
    assert "B" not in target_env


def test_promote_skips_missing_source_key(tmp_store):
    _seed(tmp_store, "staging", {"A": "1"})
    result = promote(tmp_store, "staging", "prod", "pass", "pass", keys=["A", "MISSING"])
    assert "MISSING" in result.skipped_keys
    assert "A" in result.promoted_keys


def test_promote_no_overwrite_skips_existing_target_keys(tmp_store):
    _seed(tmp_store, "staging", {"KEY": "new_value"})
    _seed(tmp_store, "prod", {"KEY": "old_value"}, password="prodpass")
    result = promote(tmp_store, "staging", "prod", "pass", "prodpass", overwrite=False)
    assert "KEY" in result.skipped_keys
    # original value preserved
    target_env = pull(tmp_store, "prod", "prodpass")
    assert target_env["KEY"] == "old_value"


def test_promote_overwrite_replaces_existing_target_keys(tmp_store):
    _seed(tmp_store, "staging", {"KEY": "new_value"})
    _seed(tmp_store, "prod", {"KEY": "old_value"}, password="prodpass")
    result = promote(tmp_store, "staging", "prod", "pass", "prodpass", overwrite=True)
    assert "KEY" in result.overwritten_keys
    target_env = pull(tmp_store, "prod", "prodpass")
    assert target_env["KEY"] == "new_value"


def test_promote_nonexistent_source_raises(tmp_store):
    with pytest.raises(ValueError, match="no stored environment"):
        promote(tmp_store, "ghost", "prod", "pass", "pass")


def test_promote_uses_different_passwords_for_source_and_target(tmp_store):
    _seed(tmp_store, "staging", {"X": "hello"}, password="src_pass")
    result = promote(tmp_store, "staging", "prod", "src_pass", "tgt_pass")
    assert "X" in result.promoted_keys
    target_env = pull(tmp_store, "prod", "tgt_pass")
    assert target_env["X"] == "hello"
