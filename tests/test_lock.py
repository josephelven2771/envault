"""Tests for envault.lock — project-level locking."""

import json
import time
import pytest
from pathlib import Path

from envault.lock import ProjectLock, LockAcquisitionError, LOCK_FILENAME, STALE_AFTER


@pytest.fixture
def lock_dir(tmp_path):
    return str(tmp_path)


def make_lock(store_dir, project="myproject", owner="alice@example.com"):
    return ProjectLock(store_dir, project, owner)


def test_acquire_creates_lock_file(lock_dir):
    lock = make_lock(lock_dir)
    lock.acquire()
    lock_path = Path(lock_dir) / "myproject" / LOCK_FILENAME
    assert lock_path.exists()
    lock.release()


def test_release_removes_lock_file(lock_dir):
    lock = make_lock(lock_dir)
    lock.acquire()
    lock.release()
    lock_path = Path(lock_dir) / "myproject" / LOCK_FILENAME
    assert not lock_path.exists()


def test_context_manager_acquires_and_releases(lock_dir):
    lock_path = Path(lock_dir) / "myproject" / LOCK_FILENAME
    with make_lock(lock_dir) as lock:
        assert lock_path.exists()
    assert not lock_path.exists()


def test_same_owner_can_reacquire(lock_dir):
    lock = make_lock(lock_dir)
    lock.acquire()
    # Should not raise — re-entrant for same owner
    lock.acquire()
    lock.release()


def test_different_owner_raises_on_timeout(lock_dir):
    lock_a = make_lock(lock_dir, owner="alice@example.com")
    lock_b = make_lock(lock_dir, owner="bob@example.com")
    lock_a.acquire()
    with pytest.raises(LockAcquisitionError, match="bob"):
        lock_b.acquire(timeout=1)
    lock_a.release()


def test_stale_lock_is_overridden(lock_dir):
    lock_path = Path(lock_dir) / "myproject" / LOCK_FILENAME
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # Write a lock that is already stale
    stale_time = time.time() - (STALE_AFTER + 10)
    with open(lock_path, "w") as f:
        json.dump({"owner": "ghost@example.com", "acquired_at": stale_time}, f)

    lock = make_lock(lock_dir, owner="alice@example.com")
    lock.acquire(timeout=5)
    data = json.loads(lock_path.read_text())
    assert data["owner"] == "alice@example.com"
    lock.release()


def test_release_by_non_owner_does_nothing(lock_dir):
    lock_a = make_lock(lock_dir, owner="alice@example.com")
    lock_b = make_lock(lock_dir, owner="bob@example.com")
    lock_a.acquire()
    lock_b.release()  # should not remove alice's lock
    lock_path = Path(lock_dir) / "myproject" / LOCK_FILENAME
    assert lock_path.exists()
    lock_a.release()


def test_lock_error_message_includes_holder(lock_dir):
    lock_a = make_lock(lock_dir, owner="alice@example.com")
    lock_b = make_lock(lock_dir, owner="bob@example.com")
    lock_a.acquire()
    with pytest.raises(LockAcquisitionError) as exc_info:
        lock_b.acquire(timeout=1)
    assert "alice@example.com" in str(exc_info.value)
    lock_a.release()
