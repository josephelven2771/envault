"""Tests for envault/hooks.py"""

import stat
import subprocess
import pytest
from pathlib import Path

from envault.hooks import (
    install_hook,
    remove_hook,
    list_hooks,
    run_hook,
    hook_path,
    HOOK_NAMES,
)


@pytest.fixture
def store_dir(tmp_path):
    return str(tmp_path)


def test_hook_path_valid(store_dir):
    p = hook_path(store_dir, "pre-push")
    assert p.name == "pre-push"


def test_hook_path_invalid_raises(store_dir):
    with pytest.raises(ValueError, match="Unknown hook"):
        hook_path(store_dir, "not-a-hook")


def test_install_creates_executable_script(store_dir):
    script = "#!/bin/sh\necho hello\n"
    path = install_hook(store_dir, "pre-push", script)
    assert path.exists()
    assert path.read_text() == script
    assert path.stat().st_mode & stat.S_IXUSR


def test_install_overwrites_existing(store_dir):
    install_hook(store_dir, "post-push", "#!/bin/sh\necho v1\n")
    install_hook(store_dir, "post-push", "#!/bin/sh\necho v2\n")
    path = hook_path(store_dir, "post-push")
    assert "v2" in path.read_text()


def test_remove_existing_hook(store_dir):
    install_hook(store_dir, "pre-pull", "#!/bin/sh\ntrue\n")
    result = remove_hook(store_dir, "pre-pull")
    assert result is True
    assert not hook_path(store_dir, "pre-pull").exists()


def test_remove_nonexistent_hook_returns_false(store_dir):
    result = remove_hook(store_dir, "post-pull")
    assert result is False


def test_list_hooks_empty(store_dir):
    assert list_hooks(store_dir) == []


def test_list_hooks_returns_installed(store_dir):
    install_hook(store_dir, "pre-push", "#!/bin/sh\ntrue\n")
    install_hook(store_dir, "post-pull", "#!/bin/sh\ntrue\n")
    hooks = list_hooks(store_dir)
    assert "pre-push" in hooks
    assert "post-pull" in hooks
    assert hooks == sorted(hooks)


def test_run_hook_nonexistent_returns_none(store_dir):
    result = run_hook(store_dir, "pre-push", project="myproject")
    assert result is None


def test_run_hook_success_returns_exit_code(store_dir):
    install_hook(store_dir, "pre-push", "#!/bin/sh\nexit 0\n")
    result = run_hook(store_dir, "pre-push", project="myproject")
    assert result == 0


def test_run_hook_passes_project_env(store_dir, tmp_path):
    output_file = tmp_path / "project.txt"
    script = f"#!/bin/sh\necho $ENVAULT_PROJECT > {output_file}\n"
    install_hook(store_dir, "post-push", script)
    run_hook(store_dir, "post-push", project="alpha")
    assert output_file.read_text().strip() == "alpha"


def test_run_hook_failure_raises(store_dir):
    install_hook(store_dir, "pre-pull", "#!/bin/sh\nexit 1\n")
    with pytest.raises(subprocess.CalledProcessError):
        run_hook(store_dir, "pre-pull", project="myproject")
