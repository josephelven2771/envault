"""Tests for envault.env_compare."""
from __future__ import annotations

import pytest

from envault.store import LocalStore, StoreEntry
from envault.crypto import encrypt
from envault.env_compare import compare_projects, CompareResult


PASSWORD = "s3cret"


@pytest.fixture()
def tmp_store(tmp_path):
    return LocalStore(str(tmp_path))


def _push(store: LocalStore, project: str, env_text: str, password: str = PASSWORD) -> None:
    ciphertext = encrypt(env_text, password)
    existing = store.load(project)
    version = (existing.version + 1) if existing else 1
    entry = StoreEntry(
        project=project,
        version=version,
        ciphertext=ciphertext,
        pushed_by="tester",
    )
    store.save(entry)


def test_matching_keys_detected(tmp_store):
    _push(tmp_store, "alpha", "KEY=hello\nSHARED=same\n")
    _push(tmp_store, "beta", "KEY=hello\nSHARED=same\n")
    result = compare_projects(tmp_store, "alpha", "beta", PASSWORD)
    assert result.matching_keys == ["KEY", "SHARED"]
    assert not result.has_differences()


def test_only_in_a_detected(tmp_store):
    _push(tmp_store, "alpha", "ONLY_A=1\nCOMMON=x\n")
    _push(tmp_store, "beta", "COMMON=x\n")
    result = compare_projects(tmp_store, "alpha", "beta", PASSWORD)
    assert "ONLY_A" in result.only_in_a
    assert result.has_differences()


def test_only_in_b_detected(tmp_store):
    _push(tmp_store, "alpha", "COMMON=x\n")
    _push(tmp_store, "beta", "ONLY_B=2\nCOMMON=x\n")
    result = compare_projects(tmp_store, "alpha", "beta", PASSWORD)
    assert "ONLY_B" in result.only_in_b
    assert result.has_differences()


def test_differing_values_detected(tmp_store):
    _push(tmp_store, "alpha", "DB_URL=postgres://a\n")
    _push(tmp_store, "beta", "DB_URL=postgres://b\n")
    result = compare_projects(tmp_store, "alpha", "beta", PASSWORD)
    assert "DB_URL" in result.differing_keys
    assert result.has_differences()


def test_separate_passwords(tmp_store):
    pw_b = "other_pass"
    _push(tmp_store, "alpha", "KEY=val\n", password=PASSWORD)
    _push(tmp_store, "beta", "KEY=val\n", password=pw_b)
    result = compare_projects(tmp_store, "alpha", "beta", PASSWORD, password_b=pw_b)
    assert "KEY" in result.matching_keys


def test_missing_project_raises(tmp_store):
    _push(tmp_store, "alpha", "KEY=val\n")
    with pytest.raises(KeyError, match="ghost"):
        compare_projects(tmp_store, "alpha", "ghost", PASSWORD)


def test_summary_contains_project_names(tmp_store):
    _push(tmp_store, "proj1", "A=1\n")
    _push(tmp_store, "proj2", "B=2\n")
    result = compare_projects(tmp_store, "proj1", "proj2", PASSWORD)
    summary = result.summary()
    assert "proj1" in summary
    assert "proj2" in summary


def test_compare_result_no_differences():
    r = CompareResult(project_a="x", project_b="y")
    assert not r.has_differences()
