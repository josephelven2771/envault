"""CLI subcommand for promoting env vars between projects."""

from __future__ import annotations

import argparse
import sys

from envault.store import LocalStore
from envault.env_promote import promote
from envault.whoami import get_current_user


def _print_promote_result(result) -> None:
    """Print a human-readable summary of a promote operation result."""
    print(result.summary())
    if result.promoted_keys:
        print("  New keys    :", ", ".join(result.promoted_keys))
    if result.overwritten_keys:
        print("  Overwritten :", ", ".join(result.overwritten_keys))
    if result.skipped_keys:
        print("  Skipped     :", ", ".join(result.skipped_keys))


def cmd_promote(args: argparse.Namespace) -> None:
    store = LocalStore(args.store_dir)

    source_password = args.source_password
    target_password = args.target_password or args.source_password

    keys = args.keys if args.keys else None
    author = get_current_user(override=getattr(args, "author", None))

    try:
        result = promote(
            store=store,
            source_project=args.source,
            target_project=args.target,
            source_password=source_password,
            target_password=target_password,
            keys=keys,
            overwrite=args.overwrite,
            author=author,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    _print_promote_result(result)


def add_promote_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "promote",
        help="Promote env vars from one project to another.",
    )
    parser.add_argument("source", help="Source project name.")
    parser.add_argument("target", help="Target project name.")
    parser.add_argument("--source-password", required=True, help="Password for the source project.")
    parser.add_argument(
        "--target-password",
        default=None,
        help="Password for the target project (defaults to source password).",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific keys to promote. Promotes all keys if omitted.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite keys that already exist in the target project.",
    )
    parser.add_argument("--store-dir", default=".envault", help="Path to the local store directory.")
    parser.add_argument("--author", default=None, help="Author name for the audit log.")
    parser.set_defaults(func=cmd_promote)
