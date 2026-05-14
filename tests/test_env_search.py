"""Tests for envault.env_search."""
from __future__ import annotations

import pytest

from envault.store import LocalStore
from envault.sync import push
from envault.env_search import search_envs, SearchMatch, SearchResult


@pytest.fixture
def tmp_store(tmp_path):
    return LocalStore(str(tmp_path))


def _seed(store, project, password, env_text):
    """Push a raw env string into the store."""
    env_file = store.path / f"_{project}.env"
    env_file.write_text(env_text)
    push(store, str(env_file), project, password)
    env_file.unlink()


def test_search_by_key_finds_match(tmp_store, tmp_path):
    _seed(tmp_store, "proj", "secret", "DATABASE_URL=postgres://localhost/db\nAPP_PORT=8080\n")
    result = search_envs(tmp_store, "secret", "DATABASE", search_keys=True)
    assert result.found
    assert any(m.key == "DATABASE_URL" for m in result.matches)


def test_search_by_key_no_match(tmp_store, tmp_path):
    _seed(tmp_store, "proj", "secret", "APP_PORT=8080\n")
    result = search_envs(tmp_store, "secret", "MISSING_KEY", search_keys=True)
    assert not result.found
    assert result.matches == []


def test_search_by_value_finds_match(tmp_store, tmp_path):
    _seed(tmp_store, "proj", "secret", "API_KEY=supersecrettoken\nFOO=bar\n")
    result = search_envs(
        tmp_store, "secret", "supersecret", search_keys=False, search_values=True
    )
    assert result.found
    assert result.matches[0].match_on == "value"


def test_search_is_case_insensitive(tmp_store, tmp_path):
    _seed(tmp_store, "proj", "secret", "DATABASE_URL=postgres://localhost\n")
    result = search_envs(tmp_store, "secret", "database_url", search_keys=True)
    assert result.found


def test_search_across_multiple_projects(tmp_store, tmp_path):
    _seed(tmp_store, "alpha", "secret", "TOKEN=abc\n")
    _seed(tmp_store, "beta", "secret", "TOKEN=xyz\n")
    result = search_envs(tmp_store, "secret", "TOKEN", search_keys=True)
    projects_found = {m.project for m in result.matches}
    assert "alpha" in projects_found
    assert "beta" in projects_found


def test_search_limited_to_specified_projects(tmp_store, tmp_path):
    _seed(tmp_store, "alpha", "secret", "TOKEN=abc\n")
    _seed(tmp_store, "beta", "secret", "TOKEN=xyz\n")
    result = search_envs(
        tmp_store, "secret", "TOKEN", projects=["alpha"], search_keys=True
    )
    assert all(m.project == "alpha" for m in result.matches)


def test_search_wrong_password_skips_entry(tmp_store, tmp_path):
    _seed(tmp_store, "proj", "correct", "SECRET_KEY=value\n")
    result = search_envs(tmp_store, "wrong", "SECRET_KEY", search_keys=True)
    assert not result.found


def test_search_result_summary_no_matches():
    r = SearchResult(pattern="FOO")
    assert "No matches" in r.summary()
    assert "FOO" in r.summary()


def test_search_result_summary_with_matches():
    r = SearchResult(
        pattern="DB",
        matches=[
            SearchMatch(project="p", version=1, key="DB_URL", value="pg://", match_on="key")
        ],
    )
    summary = r.summary()
    assert "1 match" in summary
    assert "DB_URL" in summary
    assert "key" in summary


def test_search_match_to_dict():
    m = SearchMatch(project="p", version=2, key="K", value="V", match_on="value")
    d = m.to_dict()
    assert d["project"] == "p"
    assert d["version"] == 2
    assert d["key"] == "K"
    assert d["value"] == "V"
    assert d["match_on"] == "value"
