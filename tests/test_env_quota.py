"""Tests for envault.env_quota."""
from __future__ import annotations

import pytest

from envault.store import LocalStore, StoreEntry
from envault.env_quota import (
    QuotaConfig,
    QuotaStatus,
    QuotaExceededError,
    check_quota,
    enforce_quota,
)


@pytest.fixture()
def tmp_store(tmp_path):
    return LocalStore(str(tmp_path / "store"))


def _push(store: LocalStore, project: str, n: int = 1) -> None:
    for i in range(n):
        entry = StoreEntry(
            project=project,
            version=i + 1,
            ciphertext=b"data",
            salt=b"salt",
            pushed_by="user@test",
        )
        store.save(entry)


def test_check_quota_empty_project(tmp_store):
    status = check_quota(tmp_store, "myapp", QuotaConfig(max_versions_per_project=10, max_projects=5))
    assert status.version_count == 0
    assert status.project_count == 0
    assert not status.versions_exceeded
    assert not status.projects_exceeded


def test_check_quota_counts_versions(tmp_store):
    _push(tmp_store, "myapp", n=3)
    status = check_quota(tmp_store, "myapp", QuotaConfig(max_versions_per_project=10))
    assert status.version_count == 3


def test_versions_exceeded_flag(tmp_store):
    _push(tmp_store, "myapp", n=5)
    status = check_quota(tmp_store, "myapp", QuotaConfig(max_versions_per_project=5))
    assert status.versions_exceeded


def test_projects_exceeded_flag(tmp_store):
    for proj in ["a", "b", "c"]:
        _push(tmp_store, proj, n=1)
    status = check_quota(tmp_store, "a", QuotaConfig(max_projects=3))
    assert status.projects_exceeded


def test_enforce_quota_raises_on_version_overflow(tmp_store):
    _push(tmp_store, "myapp", n=5)
    with pytest.raises(QuotaExceededError, match="Version quota exceeded"):
        enforce_quota(tmp_store, "myapp", QuotaConfig(max_versions_per_project=5))


def test_enforce_quota_passes_when_under_limit(tmp_store):
    _push(tmp_store, "myapp", n=3)
    status = enforce_quota(tmp_store, "myapp", QuotaConfig(max_versions_per_project=10))
    assert status.version_count == 3


def test_quota_status_summary_contains_project_name(tmp_store):
    _push(tmp_store, "proj-x", n=2)
    status = check_quota(tmp_store, "proj-x", QuotaConfig())
    summary = status.summary()
    assert "proj-x" in summary
    assert "2/" in summary


def test_quota_config_roundtrip():
    cfg = QuotaConfig(max_versions_per_project=30, max_projects=15)
    restored = QuotaConfig.from_dict(cfg.to_dict())
    assert restored.max_versions_per_project == 30
    assert restored.max_projects == 15


def test_default_quota_config_values():
    cfg = QuotaConfig()
    assert cfg.max_versions_per_project == 50
    assert cfg.max_projects == 20
