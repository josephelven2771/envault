"""CLI subcommand: envault lint — check a .env file for common issues."""

from __future__ import annotations

import argparse
import sys

from envault.env_file import read_env_file
from envault.env_lint import format_lint_results, lint_env


def cmd_lint(args: argparse.Namespace) -> None:
    """Run the linter against a local .env file."""
    try:
        env = read_env_file(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    issues = lint_env(env)

    if args.format == "json":
        import json
        print(json.dumps([i.to_dict() for i in issues], indent=2))
    else:
        print(format_lint_results(issues))

    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]

    if not args.quiet:
        total = len(issues)
        print(f"\n{total} issue(s) found: {len(errors)} error(s), {len(warnings)} warning(s).")

    if errors and args.strict:
        sys.exit(2)
    elif issues and not errors and args.strict:
        sys.exit(1)


def add_lint_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("lint", help="Lint a .env file for common issues.")
    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any issues are found.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the summary line.",
    )
    parser.set_defaults(func=cmd_lint)
