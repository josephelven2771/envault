"""Standalone entry point for the envault backup/restore CLI."""

from __future__ import annotations

import argparse
import sys

from envault.cli_backup import add_backup_subcommand


def build_backup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-backup",
        description="Backup and restore envault store data.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True
    add_backup_subcommand(subparsers)
    return parser


def dispatch_backup(argv: list[str] | None = None) -> None:
    parser = build_backup_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    dispatch_backup()
