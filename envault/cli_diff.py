"""CLI helpers for the 'envault diff' subcommand."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.crypto import decrypt
from envault.diff import diff_envs, format_diff, has_changes
from envault.env_file import parse_env, read_env_file
from envault.store import LocalStore


def cmd_diff(args: argparse.Namespace) -> int:
    """Show diff between the local .env file and the latest stored version."""
    store = LocalStore(args.store_dir)
    entry = store.load(args.project)

    if entry is None:
        print(f"No stored version found for project '{args.project}'.")
        return 1

    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"Local env file not found: {env_path}")
        return 1

    try:
        local_raw = read_env_file(env_path)
        local_env = parse_env(local_raw)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to read local env file: {exc}")
        return 1

    try:
        stored_raw = decrypt(entry.ciphertext, args.password)
        stored_env = parse_env(stored_raw)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to decrypt stored version: {exc}")
        return 1

    diff = diff_envs(stored_env, local_env)

    if not has_changes(diff):
        print("No changes between local and stored version.")
        return 0

    print(f"Diff for '{args.project}' (stored v{entry.version} → local):")
    print(format_diff(diff, show_unchanged=args.show_unchanged))
    return 0


def add_diff_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'diff' subcommand on an existing subparsers group."""
    parser = subparsers.add_parser(
        "diff",
        help="Show diff between local .env and the stored version",
    )
    parser.add_argument("project", help="Project name")
    parser.add_argument(
        "--env-file", default=".env", help="Path to local .env file (default: .env)"
    )
    parser.add_argument(
        "--store-dir",
        default=".envault",
        help="Path to the local store directory (default: .envault)",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Encryption password",
    )
    parser.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Also show unchanged keys in the diff output",
    )
    parser.set_defaults(func=cmd_diff)
