"""CLI sub-commands for importing env variables into envault."""

import argparse
import sys

from envault.import_env import import_from_file, import_from_json, import_from_shell, merge_envs
from envault.store import LocalStore
from envault.sync import push
from envault.whoami import get_current_user


def cmd_import(args: argparse.Namespace) -> None:
    """Handle the `envault import` command."""
    store = LocalStore(args.store)
    password = args.password
    project = args.project

    # --- collect variables from the chosen source ---
    try:
        if args.source == "file":
            imported = import_from_file(args.path)
        elif args.source == "json":
            imported = import_from_json(args.path)
        elif args.source == "shell":
            keys = args.keys.split(",") if args.keys else None
            imported = import_from_shell(keys)
        else:
            print(f"Unknown source: {args.source}", file=sys.stderr)
            sys.exit(1)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not imported:
        print("No variables found to import.")
        return

    # --- optionally merge with existing store entry ---
    if args.merge:
        entry = store.load(project)
        if entry is not None:
            from envault.crypto import decrypt
            from envault.env_file import parse_env

            existing_raw = decrypt(entry.encrypted_data, password)
            existing = parse_env(existing_raw)
            try:
                imported = merge_envs(existing, imported, conflict=args.conflict)
            except ValueError as exc:
                print(f"Merge conflict: {exc}", file=sys.stderr)
                sys.exit(1)

    # --- push merged/imported variables ---
    from envault.env_file import serialize_env

    env_text = serialize_env(imported)
    user = get_current_user()
    push(store, project, env_text, password, pushed_by=user)
    print(f"Imported {len(imported)} variable(s) into project '{project}'.")


def add_import_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("import", help="Import env variables from an external source")
    parser.add_argument("project", help="Project name")
    parser.add_argument("--password", required=True, help="Encryption password")
    parser.add_argument("--store", default=".envault_store", help="Path to local store directory")
    parser.add_argument(
        "--source",
        choices=["file", "json", "shell"],
        default="file",
        help="Source type (default: file)",
    )
    parser.add_argument("--path", help="Path to source file (required for file/json sources)")
    parser.add_argument("--keys", help="Comma-separated list of shell keys to import (shell source only)")
    parser.add_argument("--merge", action="store_true", help="Merge with existing store entry")
    parser.add_argument(
        "--conflict",
        choices=["override", "keep", "error"],
        default="override",
        help="Conflict resolution strategy when merging (default: override)",
    )
    parser.set_defaults(func=cmd_import)
