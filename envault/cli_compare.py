"""CLI sub-command: envault compare <project_a> <project_b>"""
from __future__ import annotations

import argparse
import sys

from envault.store import LocalStore
from envault.env_compare import compare_projects


def cmd_compare(args: argparse.Namespace) -> None:
    store = LocalStore(args.store_dir)

    password_b = args.password_b if args.password_b else args.password

    try:
        result = compare_projects(
            store,
            project_a=args.project_a,
            project_b=args.project_b,
            password_a=args.password,
            password_b=password_b,
        )
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Decryption failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(result.summary())

    if args.exit_code and result.has_differences():
        sys.exit(2)


def add_compare_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "compare",
        help="Compare the latest env of two projects side-by-side.",
    )
    p.add_argument("project_a", help="First project name.")
    p.add_argument("project_b", help="Second project name.")
    p.add_argument(
        "--password",
        required=True,
        help="Decryption password for project_a (and project_b unless --password-b is set).",
    )
    p.add_argument(
        "--password-b",
        dest="password_b",
        default=None,
        help="Separate decryption password for project_b.",
    )
    p.add_argument(
        "--store-dir",
        default=".envault",
        help="Path to the local store directory (default: .envault).",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 2 when differences are found (useful in CI).",
    )
    p.set_defaults(func=cmd_compare)
