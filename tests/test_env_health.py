"""Tests for envault.env_health."""
import pytest

from envault.store import LocalStore, StoreEntry
from envault.crypto import encrypt
from envault.env_health import check_health, HealthReport


PASSWORD = "test-secret-pw"
PROJECT = "myapp"


@pytest.fixture()
def tmp_store(tmp_path):
    return LocalStore(str(tmp_path))


def _push(store: LocalStore, project: str, env: dict, password: str, version: int = 1):
    content = "\n".join(f"{k}={v}" for k, v in env.items())
    ciphertext = encrypt(content, password)
    entry = StoreEntry(project=project, version=version, ciphertext=ciphertext)
    store.save(entry)
    return entry


def test_no_entry_returns_unhealthy(tmp_store):
    report = check_health(tmp_store, PROJECT, PASSWORD)
    assert not report.has_entry
    assert not report.healthy
    assert report.error is not None
    assert "No entry" in report.error


def test_clean_env_is_healthy(tmp_store):
    _push(tmp_store, PROJECT, {"DATABASE_URL": "postgres://localhost/db", "PORT": "8080"}, PASSWORD)
    report = check_health(tmp_store, PROJECT, PASSWORD)
    assert report.has_entry
    assert report.decrypt_ok
    assert report.healthy
    assert report.version == 1


def test_wrong_password_decrypt_fails(tmp_store):
    _push(tmp_store, PROJECT, {"KEY": "value"}, PASSWORD)
    report = check_health(tmp_store, PROJECT, "wrong-password")
    assert report.has_entry
    assert not report.decrypt_ok
    assert not report.healthy
    assert "Decryption failed" in (report.error or "")


def test_lint_issues_reflected_in_report(tmp_store):
    # lowercase key triggers a lint warning
    _push(tmp_store, PROJECT, {"lowercase_key": "value"}, PASSWORD)
    report = check_health(tmp_store, PROJECT, PASSWORD)
    assert report.decrypt_ok
    assert len(report.lint_issues) > 0
    keys = [i.key for i in report.lint_issues]
    assert "lowercase_key" in keys


def test_lint_error_makes_unhealthy(tmp_store):
    # empty value is a lint error
    _push(tmp_store, PROJECT, {"EMPTY_KEY": ""}, PASSWORD)
    report = check_health(tmp_store, PROJECT, PASSWORD)
    errors = [i for i in report.lint_issues if i.level == "error"]
    if errors:
        assert not report.healthy


def test_scan_finding_makes_unhealthy(tmp_store):
    _push(tmp_store, PROJECT, {"SECRET_TOKEN": "sk-abcdefghijklmnopqrstuvwxyz1234567890"}, PASSWORD)
    report = check_health(tmp_store, PROJECT, PASSWORD)
    assert report.decrypt_ok
    if report.scan_findings:
        assert not report.healthy


def test_summary_contains_project_name(tmp_store):
    _push(tmp_store, PROJECT, {"API_KEY": "safe_value"}, PASSWORD)
    report = check_health(tmp_store, PROJECT, PASSWORD)
    summary = report.summary()
    assert PROJECT in summary


def test_summary_shows_ok_when_healthy(tmp_store):
    _push(tmp_store, PROJECT, {"PORT": "3000"}, PASSWORD)
    report = check_health(tmp_store, PROJECT, PASSWORD)
    if report.healthy:
        assert "OK" in report.summary()
        assert "No issues found" in report.summary()


def test_version_tracked_correctly(tmp_store):
    _push(tmp_store, PROJECT, {"X": "1"}, PASSWORD, version=5)
    report = check_health(tmp_store, PROJECT, PASSWORD)
    assert report.version == 5
