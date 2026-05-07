"""CLI sub-command: envault rotate — rotate the encryption key for a project."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.rotate import rotate_key
from envault.store import LocalStore


def cmd_rotate(args: argparse.Namespace) -> None:
    """Handle the `rotate` sub-command."""
    store = LocalStore(args.store_dir)

    old_password = args.old_password or getpass.getpass("Current password: ")
    new_password = args.new_password or getpass.getpass("New password: ")
    confirm = args.new_password or getpass.getpass("Confirm new password: ")

    if new_password != confirm:
        print("Error: new passwords do not match.", file=sys.stderr)
        sys.exit(1)

    if old_password == new_password:
        print("Error: new password must differ from the old password.", file=sys.stderr)
        sys.exit(1)

    try:
        count = rotate_key(
            store=store,
            project=args.project,
            old_password=old_password,
            new_password=new_password,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if count == 0:
        print(f"No versions found for project '{args.project}'.")
    else:
        print(
            f"Rotated encryption key for project '{args.project}' "
            f"across {count} version(s)."
        )


def add_rotate_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the `rotate` sub-command on *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "rotate",
        help="Re-encrypt all versions of a project under a new password.",
    )
    parser.add_argument("project", help="Project name whose key should be rotated.")
    parser.add_argument(
        "--store-dir",
        default=".envault",
        help="Path to the local store directory (default: .envault).",
    )
    parser.add_argument(
        "--old-password",
        default=None,
        help="Current encryption password (prompted if omitted).",
    )
    parser.add_argument(
        "--new-password",
        default=None,
        help="New encryption password (prompted if omitted).",
    )
    parser.set_defaults(func=cmd_rotate)
