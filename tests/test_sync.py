"""Tests for envault.sync — push and pull workflows."""

import pytest
from pathlib import Path

from envault.store import LocalStore
from envault.sync import push, pull


PASSWORD = "supersecret"
PROJECT = "myapp"
ENV = "production"


@pytest.fixture
def store(tmp_path):
    return LocalStore(store_dir=tmp_path / "store")


@pytest.fixture
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("DB_URL=postgres://localhost/mydb\nSECRET_KEY=abc123\nDEBUG=false\n")
    return path


def test_push_creates_store_entry(store, env_file):
    entry = push(PROJECT, ENV, env_file, PASSWORD, "alice@example.com", store=store)
    assert entry.project == PROJECT
    assert entry.environment == ENV
    assert entry.version == 1
    assert entry.updated_by == "alice@example.com"
    assert entry.ciphertext  # non-empty


def test_push_increments_version_on_second_push(store, env_file):
    push(PROJECT, ENV, env_file, PASSWORD, "alice@example.com", store=store)
    entry2 = push(PROJECT, ENV, env_file, PASSWORD, "bob@example.com", store=store)
    assert entry2.version == 2


def test_pull_restores_env_file(store, env_file, tmp_path):
    push(PROJECT, ENV, env_file, PASSWORD, "alice@example.com", store=store)
    dest = tmp_path / ".env.pulled"
    env_vars = pull(PROJECT, ENV, dest, PASSWORD, store=store)
    assert dest.exists()
    assert env_vars["DB_URL"] == "postgres://localhost/mydb"
    assert env_vars["SECRET_KEY"] == "abc123"
    assert env_vars["DEBUG"] == "false"


def test_pull_written_file_is_parseable(store, env_file, tmp_path):
    from envault.env_file import read_env_file
    push(PROJECT, ENV, env_file, PASSWORD, "alice@example.com", store=store)
    dest = tmp_path / ".env.out"
    pull(PROJECT, ENV, dest, PASSWORD, store=store)
    result = read_env_file(dest)
    assert result["DB_URL"] == "postgres://localhost/mydb"


def test_pull_wrong_password_raises(store, env_file, tmp_path):
    push(PROJECT, ENV, env_file, PASSWORD, "alice@example.com", store=store)
    dest = tmp_path / ".env.bad"
    with pytest.raises(Exception):
        pull(PROJECT, ENV, dest, "wrongpassword", store=store)


def test_pull_missing_entry_raises(store, tmp_path):
    dest = tmp_path / ".env.missing"
    with pytest.raises(FileNotFoundError, match="No stored env"):
        pull("nonexistent", "dev", dest, PASSWORD, store=store)


def test_push_pull_roundtrip_preserves_all_vars(store, tmp_path):
    src = tmp_path / ".env.src"
    src.write_text("FOO=bar\nBAZ=qux\nEMPTY=\n")
    push(PROJECT, ENV, src, PASSWORD, "tester", store=store)
    dest = tmp_path / ".env.dest"
    result = pull(PROJECT, ENV, dest, PASSWORD, store=store)
    assert result["FOO"] == "bar"
    assert result["BAZ"] == "qux"
    assert result["EMPTY"] == ""
