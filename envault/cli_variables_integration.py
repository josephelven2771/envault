"""Standalone entry point for the variable interpolation subcommands."""
from __future__ import annotations

import argparse
import sys

from envault.cli_variables import add_variables_subcommand


def build_variables_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-vars",
        description="Inspect and resolve variable references in stored env files.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True
    add_variables_subcommand(subparsers)
    return parser


def dispatch_variables(argv: list[str] | None = None) -> None:
    parser = build_variables_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    dispatch_variables()
