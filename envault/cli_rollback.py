"""CLI sub-commands for rollback: ``envault rollback`` and ``envault versions``."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.store import LocalStore
from envault.audit import AuditLog
from envault.rollback import list_versions, rollback


def cmd_versions(args: argparse.Namespace) -> None:
    """List all stored versions for a project."""
    store = LocalStore(args.store_path)
    versions = list_versions(store, args.project)

    if not versions:
        print(f"No versions found for project '{args.project}'.")
        return

    print(f"{'Version':<10} {'Pushed by':<30} {'Pushed at'}")
    print("-" * 60)
    for v in versions:
        print(f"{v['version']:<10} {v['pushed_by']:<30} {v['pushed_at']}")


def cmd_rollback(args: argparse.Namespace) -> None:
    """Roll back to a specific version of an env file."""
    password = getpass.getpass("Encryption password: ")

    store = LocalStore(args.store_path)
    audit_log = AuditLog(args.audit_log) if args.audit_log else None

    try:
        result = rollback(
            store=store,
            project=args.project,
            target_version=args.version,
            password=password,
            output_path=args.env_file,
            audit_log=audit_log,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Rolled back '{args.project}' to version {result['version']} "
        f"(originally pushed by {result['pushed_by']} at {result['pushed_at']})."
    )
    print(f"Written to: {result['output_path']}")


def add_rollback_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register 'versions' and 'rollback' sub-commands onto *subparsers*."""
    # --- versions ---
    p_versions = subparsers.add_parser(
        "versions", help="List stored versions for a project"
    )
    p_versions.add_argument("project", help="Project name")
    p_versions.add_argument(
        "--store-path", default=".envault_store", help="Path to local store directory"
    )
    p_versions.set_defaults(func=cmd_versions)

    # --- rollback ---
    p_rollback = subparsers.add_parser(
        "rollback", help="Restore a previous version of an env file"
    )
    p_rollback.add_argument("project", help="Project name")
    p_rollback.add_argument("version", type=int, help="Version number to restore")
    p_rollback.add_argument(
        "--env-file", default=".env", help="Path to write the restored env file"
    )
    p_rollback.add_argument(
        "--store-path", default=".envault_store", help="Path to local store directory"
    )
    p_rollback.add_argument(
        "--audit-log", default=None, help="Path to audit log file"
    )
    p_rollback.set_defaults(func=cmd_rollback)
