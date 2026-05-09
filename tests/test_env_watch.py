"""Tests for envault.env_watch."""

import pytest
from pathlib import Path
from unittest.mock import patch, call

from envault.store import LocalStore
from envault.env_watch import watch, _file_hash


@pytest.fixture()
def tmp_store(tmp_path):
    return LocalStore(str(tmp_path / "store"))


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("KEY=value\n")
    return p


def test_file_hash_is_stable(env_file):
    h1 = _file_hash(env_file)
    h2 = _file_hash(env_file)
    assert h1 == h2


def test_file_hash_changes_after_write(env_file):
    h1 = _file_hash(env_file)
    env_file.write_text("KEY=changed\n")
    h2 = _file_hash(env_file)
    assert h1 != h2


def test_watch_raises_if_file_missing(tmp_store, tmp_path):
    missing = tmp_path / "nonexistent.env"
    with pytest.raises(FileNotFoundError):
        watch(missing, tmp_store, "proj", "pass", max_iterations=1)


def test_watch_no_change_does_not_push(env_file, tmp_store):
    pushed = []
    with patch("envault.env_watch.time.sleep"):
        watch(
            env_path=env_file,
            store=tmp_store,
            project="proj",
            password="secret",
            poll_interval=0.0,
            max_iterations=3,
            on_push=lambda p, v: pushed.append(v),
        )
    assert pushed == [], "no push expected when file is unchanged"


def test_watch_detects_change_and_pushes(env_file, tmp_store):
    pushed = []
    call_count = 0

    def fake_sleep(_):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            env_file.write_text("KEY=changed\n")

    with patch("envault.env_watch.time.sleep", side_effect=fake_sleep):
        watch(
            env_path=env_file,
            store=tmp_store,
            project="proj",
            password="secret",
            poll_interval=0.0,
            max_iterations=2,
            on_push=lambda p, v: pushed.append((p, v)),
        )

    assert len(pushed) == 1
    project, version = pushed[0]
    assert project == "proj"
    assert version == 1


def test_watch_on_error_callback_called(env_file, tmp_store):
    errors = []

    def boom(_):
        raise RuntimeError("disk full")

    with patch("envault.env_watch.time.sleep"):
        with patch("envault.env_watch._file_hash", side_effect=["aaa", "bbb"]):
            with patch("envault.env_watch.push", side_effect=RuntimeError("disk full")):
                watch(
                    env_path=env_file,
                    store=tmp_store,
                    project="proj",
                    password="secret",
                    poll_interval=0.0,
                    max_iterations=1,
                    on_error=lambda e: errors.append(str(e)),
                )

    assert any("disk full" in e for e in errors)
