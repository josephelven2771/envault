"""Pre/post hook support for push and pull operations."""

import os
import subprocess
from pathlib import Path
from typing import Optional

HOOK_NAMES = {
    "pre-push",
    "post-push",
    "pre-pull",
    "post-pull",
}


def _hooks_dir(store_dir: str) -> Path:
    return Path(store_dir) / "hooks"


def hook_path(store_dir: str, hook_name: str) -> Path:
    """Return the path for a named hook script."""
    if hook_name not in HOOK_NAMES:
        raise ValueError(f"Unknown hook: {hook_name!r}. Valid hooks: {sorted(HOOK_NAMES)}")
    return _hooks_dir(store_dir) / hook_name


def install_hook(store_dir: str, hook_name: str, script: str) -> Path:
    """Write a hook script to the hooks directory and make it executable."""
    path = hook_path(store_dir, hook_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script)
    path.chmod(0o755)
    return path


def remove_hook(store_dir: str, hook_name: str) -> bool:
    """Remove a hook script. Returns True if it existed, False otherwise."""
    path = hook_path(store_dir, hook_name)
    if path.exists():
        path.unlink()
        return True
    return False


def run_hook(
    store_dir: str,
    hook_name: str,
    project: str,
    env: Optional[dict] = None,
    timeout: int = 30,
) -> Optional[int]:
    """Run a hook script if it exists.

    Passes ENVAULT_PROJECT as an environment variable to the script.
    Returns the exit code, or None if the hook does not exist.
    Raises subprocess.CalledProcessError if the hook exits non-zero.
    """
    path = hook_path(store_dir, hook_name)
    if not path.exists():
        return None

    run_env = os.environ.copy()
    run_env["ENVAULT_PROJECT"] = project
    if env:
        run_env.update(env)

    result = subprocess.run(
        [str(path)],
        env=run_env,
        timeout=timeout,
        check=True,
    )
    return result.returncode


def list_hooks(store_dir: str) -> list:
    """Return a list of installed hook names."""
    hooks_dir = _hooks_dir(store_dir)
    if not hooks_dir.exists():
        return []
    return sorted(
        p.name for p in hooks_dir.iterdir()
        if p.is_file() and p.name in HOOK_NAMES
    )
