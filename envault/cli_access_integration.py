"""Integration helper: wire access subcommands into the main envault CLI."""

from __future__ import annotations

import argparse
from typing import Optional

from envault.cli_access import add_access_subcommands
from envault.access import AccessControl, PERMISSION_READ, PERMISSION_WRITE
from envault.whoami import get_current_user
from pathlib import Path


def check_access_or_exit(
    project: str,
    store_dir: str,
    required_permission: str,
    override_user: Optional[str] = None,
) -> None:
    """Guard helper: raise SystemExit if current user lacks required permission.

    If no access.json exists yet (project not yet protected), access is granted
    to allow initial push/pull bootstrapping.
    """
    path = Path(store_dir) / project / "access.json"
    if not path.exists():
        return  # No ACL configured — open access

    user = override_user or get_current_user()
    ac = AccessControl(path)
    if not ac.can(user, required_permission):
        perm = ac.get_permission(user)
        if perm is None:
            msg = f"Access denied: '{user}' has no access to project '{project}'."
        else:
            msg = (
                f"Access denied: '{user}' has '{perm}' on '{project}' "
                f"but '{required_permission}' is required."
            )
        raise SystemExit(msg)


def build_access_parser() -> argparse.ArgumentParser:
    """Build a standalone argument parser with access subcommands (for testing)."""
    parser = argparse.ArgumentParser(prog="envault")
    subparsers = parser.add_subparsers(dest="command")
    add_access_subcommands(subparsers)
    return parser


def dispatch_access(args: argparse.Namespace) -> None:
    """Dispatch to the correct access subcommand handler."""
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("No access subcommand specified. Use: grant, revoke, list, check")


if __name__ == "__main__":
    import sys

    parser = build_access_parser()
    args = parser.parse_args(sys.argv[1:])
    dispatch_access(args)
